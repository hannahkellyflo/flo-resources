#!/usr/bin/env python3
"""Compose + post the daily Slack digest for the Legal Recruiting Tracker.

Reads the changeset from diff_data (a single day's bot-refresh diff by default, or an
aggregate window via --since) and posts a grouped summary to Elizabeth, noting which
upcoming email (Tue/Fri) the changes will land in.

  * Email-worthy (counted at top): new items + open-date / campus-program-date / exam-grade-date changes.
  * Slack-only end sections (context, never in the email): close-date FYI, removals ("Removed from the
    tracker"), and general edits ("Edited listings" — non-date fields like title/office/comp).
  * Human-commit deltas (rule changes) are noted as "needs review", never counted as news.

Prod:   SLACK_BOT_TOKEN + SLACK_TARGET (a user id for a DM, or a channel id) → chat.postMessage.
Dry-run: prints the composed markdown (default when no token/target, or with --dry-run).

Usage:
  slack_notify.py                       # today's diff (last two bot refreshes), dry-run/post
  slack_notify.py --since 2026-08-19    # aggregate window (for testing with real content)
  slack_notify.py --dry-run             # force print, never post
"""
import os, sys, json, datetime, urllib.request
import diff_data  # same directory

TUE, FRI = 1, 4  # Monday = 0


def next_send_date(today):
    """The next Tuesday or Friday on/after `today`."""
    for i in range(8):
        d = today + datetime.timedelta(days=i)
        if d.weekday() in (TUE, FRI):
            return d
    return today


def _fmt_day(d):
    return d.strftime("%A, %B ") + str(d.day)


def _slk(url, text):
    """Slack hyperlink: <url|text>, or plain text when there's no url."""
    return f"<{url}|{text}>" if url else text


def _bullets(items):
    out = []
    for c in items:
        name = _slk(c.get("profile"), c["entity"])   # firm name links to its Flo profile when it has one
        pos = f" · {c['pos']}" if c.get("pos") else ""
        if c["kind"] == "add":
            if c.get("open_date"):
                tail = f" — {c['open_date']}"
            elif c.get("link"):
                tail = f" — {_slk(c['link'], 'Open')}"   # 'Open' links to the Flo Forward application
            else:
                tail = ""
            out.append(f"  • {name}{pos}{tail}")
        elif c["kind"] == "open_date":
            out.append(f"  • {name}{pos} — open date {c['old']} → {c['new']}")
        elif c["kind"] == "program_date":
            out.append(f"  • {name} — {c['field']}: {c['old'] or '—'} → {c['new'] or '—'}")
        elif c["kind"] == "remove":
            out.append(f"  • {name}{pos}")
        elif c["kind"] == "edit":
            es = c.get("edits", [])
            shown = "; ".join(f"{e['field']}: {e['old']} → {e['new']}" for e in es[:3])
            more = len(es) - 3
            if more > 0:
                shown += f" (+{more} more)"
            out.append(f"  • {name}{pos} — {shown}")
    return out


def _section_group(items):
    secs, order = {}, []
    for c in items:
        if c["section"] not in secs:
            secs[c["section"]] = []
            order.append(c["section"])
        secs[c["section"]].append(c)
    return [(s, secs[s]) for s in order]


# Kinds that feed the marketing email; everything else (close-date, removals, general edits)
# is Slack-only context for Elizabeth.
EMAIL_KINDS = ("add", "open_date", "program_date")


def compose(changes, flagged, today):
    student = [c for c in changes if c["audience"] == "student" and c["kind"] in EMAIL_KINDS]
    attorney = [c for c in changes if c["audience"] == "attorney" and c["kind"] in EMAIL_KINDS]
    close = [c for c in changes if c["kind"] == "close_date"]
    removed = [c for c in changes if c["kind"] == "remove"]
    edited = [c for c in changes if c["kind"] == "edit"]
    nxt = next_send_date(today)
    total = len(student) + len(attorney)
    when = (f"*today's* email update ({_fmt_day(today)})" if nxt == today
            else f"the next email update on *{_fmt_day(nxt)}*")

    L = [f"*Legal Recruiting Tracker — daily update · {_fmt_day(today)}*", ""]
    if not (total or close or removed or edited):
        L.append("No tracker changes today. :white_check_mark:")
    elif total:
        L.append(f"*{total}* new/date change{'s' if total != 1 else ''} today — "
                 f"{len(student)} student, {len(attorney)} attorney. "
                 f"These will be included in {when}.")
    else:
        L.append(f"No email-worthy changes today (see the sections below). "
                 f"Next email: {when}.")

    for label, items in (("STUDENT", student), ("ATTORNEY", attorney)):
        if not items:
            continue
        L += ["", f"*{label} ({len(items)})*"]
        for sec, cs in _section_group(items):
            L.append(f"_{sec}:_")
            L += _bullets(cs)

    if close:
        agg = {}  # collapse the same firm's close-date shift across multiple listings
        for c in close:
            agg.setdefault((c["entity"], c["old"], c["new"]), 0)
            agg[(c["entity"], c["old"], c["new"])] += 1
        L += ["", f"*FYI — close-date changes ({len(agg)})* _(not in the email)_"]
        for (ent, old, new), n in agg.items():
            mult = f" (×{n} listings)" if n > 1 else ""
            L.append(f"  • {ent} — close date {old} → {new}{mult}")

    # Separate end sections (Slack only): rows that came off the tracker, and rows whose
    # non-date fields changed (title/office/comp/etc.) — context for Elizabeth, not email content.
    _clean = lambda s: s[4:] if s.startswith("New ") else s   # "New Lateral…" reads oddly under Removed/Edited
    if removed:
        L += ["", f"*Removed from the tracker ({len(removed)})* _(not in the email)_"]
        for sec, cs in _section_group(removed):
            L.append(f"_{_clean(sec)}:_")
            L += _bullets(cs)

    if edited:
        L += ["", f"*Edited listings ({len(edited)})* _(not in the email)_"]
        for sec, cs in _section_group(edited):
            L.append(f"_{_clean(sec)}:_")
            L += _bullets(cs)

    if flagged:
        subs = {}
        for c in flagged:
            subs[c["human_commit"]] = subs.get(c["human_commit"], 0) + 1
        L += ["", f"*:warning: {len(subs)} human commit(s) touched the data — review, not auto-reported:*"]
        for subj, n in subs.items():
            L.append(f"  • [{n} changes] {subj}")

    L += ["", "<https://resources.joinflo.com/tracker|View the tracker>"]
    return "\n".join(L)


# Committed watermark: the last bot-refresh SHA already reported to Elizabeth. The daily job
# diffs from here to the newest refresh, so a Monday run spans the whole weekend and it's robust
# to failed runs / multiple refreshes in a day. The workflow commits the advanced watermark.
WATERMARK = ".recruiting-digest/last_reported.txt"


# Twice-weekly "email-ready" aggregate: the copy/paste content for the Tue/Fri sends, used
# until (or instead of) direct HubSpot drafting. Its own watermark advances only on send days,
# so it spans the whole gap since the last email regardless of the daily digest.
WATERMARK_EMAIL = ".recruiting-digest/last_email.txt"


def prev_send_date(today):
    """The most recent Tuesday or Friday strictly before today (the last email send)."""
    for i in range(1, 8):
        d = today - datetime.timedelta(days=i)
        if d.weekday() in (TUE, FRI):
            return d
    return today


def compose_email(changes, today):
    """Email-ready aggregate: Student and Attorney blocks Elizabeth can copy/paste per version."""
    student = [c for c in changes if c["audience"] == "student" and c["kind"] in EMAIL_KINDS]
    attorney = [c for c in changes if c["audience"] == "attorney" and c["kind"] in EMAIL_KINDS]
    total = len(student) + len(attorney)
    since = prev_send_date(today)
    L = [f":clipboard: *Email-ready update — {_fmt_day(today)}* _(copy/paste for today's send)_",
         "_Three versions: *Student* = the Student block · *Attorney* = the Attorney block · "
         "*Both* = both blocks._", ""]
    L.append(f"_Suggested intro:_ We've added *{total}* update{'s' if total != 1 else ''} to the "
             f"Recruiting Tracker since {_fmt_day(since)}.")
    for label, items in (("STUDENT", student), ("ATTORNEY", attorney)):
        L += ["", f"*━━ {label} EMAIL — {len(items)} item{'s' if len(items) != 1 else ''} ━━*"]
        if not items:
            L.append(f"_No {label.lower()} updates since the last send — skip the {label.lower()} email._")
            continue
        for sec, cs in _section_group(items):
            L.append(f"*{sec}:*")
            L += _bullets(cs)
    L += ["", "<https://resources.joinflo.com/tracker|View the tracker>"]
    return "\n".join(L)


def build(argv):
    """Return (message, meta). --email = twice-weekly aggregate; --since = ad-hoc window;
    otherwise the daily digest. Each mode diffs from its own committed watermark."""
    today = datetime.date.today()
    email_mode = "--email" in argv
    wm_path = WATERMARK_EMAIL if email_mode else WATERMARK
    if "--since" in argv:
        changes, flagged = diff_data.aggregate_since(argv[argv.index("--since") + 1])
    else:
        wm = (open(wm_path).read().strip() or None) if os.path.exists(wm_path) else None
        if wm:
            changes, flagged = diff_data.aggregate_since_ref(wm)
        else:  # first run — latest single step, then set the watermark
            bots = [c for c in diff_data.commits_touching_data() if c["bot"]]
            if len(bots) < 2:
                return None, None
            changes, flagged = diff_data.diff(bots[-2]["sha"], bots[-1]["sha"]), []
    msg = compose_email(changes, today) if email_mode else compose(changes, flagged, today)
    return msg, {"latest": diff_data.latest_bot_sha(), "wm_path": wm_path}


def post(message):
    token, target = os.environ.get("SLACK_BOT_TOKEN"), os.environ.get("SLACK_TARGET")
    if not token or not target:
        raise RuntimeError("SLACK_BOT_TOKEN and SLACK_TARGET required to post")
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps({"channel": target, "text": message,
                         "unfurl_links": False, "mrkdwn": True}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"})
    res = json.load(urllib.request.urlopen(req))
    if not res.get("ok"):
        raise RuntimeError(f"slack error: {res.get('error')}")
    return res


def main(argv):
    message, meta = build(argv)
    if message is None:
        print("Not enough bot-refresh history to diff.")
        return
    dry = "--dry-run" in argv or not (os.environ.get("SLACK_BOT_TOKEN") and os.environ.get("SLACK_TARGET"))
    if dry:
        print(message)
        return
    post(message)
    # advance this mode's watermark so the next run starts where this one ended
    meta = meta or {}
    if meta.get("latest") and meta.get("wm_path") and "--since" not in argv:
        os.makedirs(os.path.dirname(meta["wm_path"]), exist_ok=True)
        with open(meta["wm_path"], "w") as f:
            f.write(meta["latest"] + "\n")
    print("posted")


if __name__ == "__main__":
    main(sys.argv[1:])
