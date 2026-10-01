#!/usr/bin/env python3
"""Morning heads-up for Juli: which tracked jobs are opening TODAY that she needs to add to
Flo Forward.

Point-in-time read of pipeline/data.json (no git diff): the summer 1L/2L *upcoming* tables are
jobs the Tracker knows about but that are NOT yet live on Flo Forward ("Opens M/D/YYYY", no
listing link). When one's open date arrives, Juli posts it. Jobs already live on Flo Forward
(real /jobs/ link, in the "open" bucket) are intentionally excluded — those are done.

Posts to #forward-job-postings tagging Juli. On Monday it also sweeps Saturday/Sunday open
dates (the refresh doesn't run weekends) so nothing is missed. Zero openings → a clear
"no intel for today" note.

Delivery timing: GitHub's scheduled cron fires 4-7 hours late and unpredictably, so we do NOT
rely on the run landing at 8 AM. Instead the workflow runs the EVENING BEFORE, and we hand the
message to Slack's chat.scheduleMessage pinned to 8:00 AM CT on the next weekday (next_delivery()).
Because the run fires the night before, that 8 AM target is always comfortably in the future even
when GitHub is hours late, so delivery actually lands at 8 AM. `--now` sends immediately instead
(manual catch-up); `--date YYYY-MM-DD` overrides the delivery date for testing.

Prod: SLACK_BOT_TOKEN → chat.scheduleMessage (or chat.postMessage with --now). Dry-run: prints.
"""
import os, sys, json, re, datetime, urllib.request
from zoneinfo import ZoneInfo

DATA_PATH = "pipeline/data.json"
CHANNEL = os.environ.get("SLACK_CHANNEL", "C073ZL436BB")   # #forward-job-postings
JULI = os.environ.get("JULI_USER_ID", "U09HWPD25JS")       # Juli Davis
JOB_ID_RE = re.compile(r"/jobs/\d+")
CT = ZoneInfo("America/Chicago")

# Paused through this date (exclusive): before it, scheduled runs skip silently and auto-resume on it.
# Set to None to remove the pause. (Hannah 2026-09-02: hold Juli's heads-ups until 2026-09-29.)
RESUME_ON = datetime.date(2026, 9, 29)

# (table, open-date col, position col, listing col)
SUMMER = [("summer1L", "1L Application Open Date", "1L Position", "1L Job Listing", "1L Summer"),
          ("summer2L", "2L Application Open Date", "2L Position", "2L Job Listing", "2L Summer")]


def _parse_open(v):
    if not v:
        return None
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", str(v))
    if not m:
        return None
    try:
        return datetime.date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
    except ValueError:
        return None


def _is_live(listing):
    return isinstance(listing, dict) and bool(JOB_ID_RE.search(str(listing.get("href", ""))))


def target_dates(today):
    """Today — but on Monday also Saturday+Sunday, since the data refresh skips weekends."""
    prev = today - datetime.timedelta(days=1)
    while prev.weekday() >= 5:            # back up over Sun/Sat to the previous weekday
        prev -= datetime.timedelta(days=1)
    out, d = [], prev + datetime.timedelta(days=1)
    while d <= today:
        out.append(d)
        d += datetime.timedelta(days=1)
    return out


def find_openings(tables, dates):
    dset = set(dates)
    hits = {"1L Summer": [], "2L Summer": []}
    for key, odc, posc, lkc, label in SUMMER:
        # only the "upcoming" bucket = not-yet-live tracked jobs (add-these). Guard live just in case.
        for row in (tables.get(key, {}).get("upcoming") or []):
            if _is_live(row.get(lkc)):
                continue
            od = _parse_open(row.get(odc))
            if od and od in dset:
                fp = row.get("Firm Profile")
                hits[label].append({
                    "firm": row.get("Employer"),
                    "pos": row.get(posc),
                    "date": od,
                    "profile": fp.get("href") if isinstance(fp, dict) else None,
                })
    return hits


def compose(hits, today):
    n = sum(len(v) for v in hits.values())
    day = today.strftime("%A, %B ") + str(today.day)
    if n == 0:
        return (f"<@{JULI}> :calendar: *Opening today — {day}*\n"
                "The Tracker doesn't have any intel on new openings for today's date.")
    L = [f"<@{JULI}> :calendar: *Opening today per the Tracker — {day}*",
         f"_{n} job{'s' if n != 1 else ''} to add to Flo Forward:_"]
    for label in ("1L Summer", "2L Summer"):
        items = hits[label]
        if not items:
            continue
        L += ["", f"*{label}:*"]
        for it in items:
            firm = f"<{it['profile']}|{it['firm']}>" if it.get("profile") else it["firm"]
            d = it["date"].strftime("%-m/%-d")
            L.append(f"  • {firm} — {it['pos']}  _(opens {d})_")
    return "\n".join(L)


def next_delivery(now):
    """The soonest weekday whose 8 AM CT is still ahead — the morning this run targets. Run the
    evening before and this returns the next day; run before 8 AM and it returns today; Sat/Sun
    roll to Monday. This is what lets an evening (or hours-late) run still land at 8 AM."""
    eight_today = now.replace(hour=8, minute=0, second=0, microsecond=0)
    d = now.date()
    if now + datetime.timedelta(seconds=60) >= eight_today:   # today's 8 AM window is gone
        d += datetime.timedelta(days=1)
    while d.weekday() >= 5:                                    # roll Sat/Sun -> Mon
        d += datetime.timedelta(days=1)
    return d


def _post_at_8am_ct(delivery):
    """Unix ts for 8:00 AM America/Chicago on the delivery date (DST-correct via zoneinfo)."""
    dt = datetime.datetime(delivery.year, delivery.month, delivery.day, 8, 0, 0, tzinfo=CT)
    return int(dt.timestamp())


def post(message, post_at):
    """Schedule for post_at (Unix ts) via chat.scheduleMessage, or send now when post_at is None."""
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        raise RuntimeError("SLACK_BOT_TOKEN required to post")
    payload = {"channel": CHANNEL, "text": message, "unfurl_links": False, "mrkdwn": True}
    if post_at:
        payload["post_at"] = post_at
        url = "https://slack.com/api/chat.scheduleMessage"   # delivered at 8 AM CT regardless of run time
    else:
        url = "https://slack.com/api/chat.postMessage"       # --now: immediate
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"})
    res = json.load(urllib.request.urlopen(req))
    if not res.get("ok"):
        raise RuntimeError(f"slack error: {res.get('error')}")
    return res


def main(argv):
    if "--date" in argv:  # testing override of the delivery date, e.g. --date 2026-11-01
        delivery = datetime.date.fromisoformat(argv[argv.index("--date") + 1])
    else:
        delivery = next_delivery(datetime.datetime.now(CT))
    # Paused window: real runs skip until RESUME_ON, then resume on their own. --dry-run/--force test through it.
    if RESUME_ON and delivery < RESUME_ON and "--dry-run" not in argv and "--force" not in argv:
        print(f"opening-today paused until {RESUME_ON.isoformat()} — skipping (delivery {delivery.isoformat()})")
        return
    tables = json.load(open(DATA_PATH)).get("tables", {})
    hits = find_openings(tables, target_dates(delivery))
    message = compose(hits, delivery)
    send_now = "--now" in argv
    if "--dry-run" in argv or not os.environ.get("SLACK_BOT_TOKEN"):
        print(f"[would {'send immediately' if send_now else 'schedule for 8 AM CT ' + delivery.isoformat()}]")
        print(message)
    else:
        post(message, None if send_now else _post_at_8am_ct(delivery))
        print("posted (immediately)" if send_now else f"scheduled for 8 AM CT {delivery.isoformat()}")


if __name__ == "__main__":
    main(sys.argv[1:])
