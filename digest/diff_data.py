#!/usr/bin/env python3
"""Detect newsletter-worthy changes to the Legal Recruiting Tracker.

Diffs pipeline/data.json across git commits and emits a typed changeset:
  { audience: student|attorney, section, kind: add|open_date|program_date|close_date,
    entity, detail, link, ... }

Design notes (Hannah 2026-08-21):
  * data.json is the single source of truth; the daily refresh bot commits it as
    "chore: refresh legal recruiting tracker data [skip ci]". Only those bot commits
    are genuine data changes. Human commits (template/generate.py edits) can shift the
    data.json output too (e.g. the 6-month takedown rule dropped 131 lateral rows) — so
    diffs whose target is a human commit are flagged for review, never auto-reported.
  * Rows are keyed on the Flo job ID from the listing URL (/jobs/<id>) when present, with
    a normalized employer|position composite fallback for the link-less tables (upcoming,
    campus, exams). This kills the punctuation-churn false positives (en-dash vs hyphen).
  * Reported in the EMAIL: new items, open-date changes, campus program-date changes,
    exam/grade-date changes. NOT close-date changes (those go to the Slack digest only)
    and NOT removals.

Usage:
  diff_data.py <from_ref> <to_ref>      # diff two data.json versions
  diff_data.py --since YYYY-MM-DD        # aggregate all bot-commit changes since a date
  diff_data.py --since YYYY-MM-DD --json # emit the raw changeset as JSON
"""
import json, subprocess, re, sys, datetime

DATA_PATH = "pipeline/data.json"
BOT_SUBJECT = "chore: refresh legal recruiting tracker data"
JOB_ID_RE = re.compile(r"/jobs/(\d+)")

# ── per-table config ────────────────────────────────────────────────────────
# rows: "split" -> {open:[],upcoming:[]}, else flat list.
# name/pos: identity columns; link: column holding the {text,href} listing link (job-id key).
# open_date/close_date: date columns; date_cols: extra date fields to watch (campus/exams).
TABLES = [
    {"key": "summer1L", "rows": "split", "audience": "student",
     "section": "New Law Firm 1L Summer Open Dates",
     "name": "Employer", "pos": "1L Position", "link": "1L Job Listing",
     "open_date": "1L Application Open Date", "close_date": "Application Close Date",
     "profile": "Firm Profile"},
    {"key": "summer2L", "rows": "split", "audience": "student",
     "section": "New Law Firm 2L Summer Open Dates",
     "name": "Employer", "pos": "2L Position", "link": "2L Job Listing",
     "open_date": "2L Application Open Date", "close_date": "Application Close Date",
     "profile": "Firm Profile"},
    {"key": "entry3l", "rows": "flat", "audience": "student",
     "section": "New 3L Openings",
     "name": "Employer", "pos": "3L Position", "link": "3L Job Listing", "profile": "Firm Profile"},
    {"key": "piSummerOpen", "rows": "flat", "audience": "student",
     "section": "New Public Interest Openings", "open_as_link": True,
     "name": "Organization", "pos": "Job Title", "link": "Apply Here",
     "open_date": "Application Open Date", "close_date": "Application Close Date"},
    {"key": "piExternOpen", "rows": "flat", "audience": "student",
     "section": "New Public Interest Openings", "open_as_link": True,
     "name": "Organization", "pos": "Job Title", "link": "Apply Here",
     "open_date": "Application Open Date", "close_date": "Application Close Date"},
    {"key": "campus", "rows": "flat", "audience": "student",
     "section": "New Campus Programs",
     "name": "Law School", "pos": "Program",
     "date_cols": ["Program Dates", "Employer Registration Dates",
                   "Student Bidding / Application Dates",
                   "Initial Employer Schedule Release Date", "Final Schedule Release Date"]},
    {"key": "exams", "rows": "flat", "audience": "student",
     "section": "Exam & Grade Dates",  # new schools AND date changes (Hannah 2026-08-21)
     "name": "Law School", "pos": None,
     "date_cols": ["First Semester Grades Available", "Second Semester Grades Available",
                   "First Semester Exam Dates", "Second Semester Exam Dates"]},
    {"key": "lateral", "rows": "flat", "audience": "attorney",
     "section": "New Lateral Non-Partner Openings",
     "name": "Law Firm", "pos": "Position", "link": "Job Listing", "open_date": "Open Date"},
    {"key": "pc", "rows": "flat", "audience": "attorney",
     "section": "New Post-Clerkship Openings",
     "name": "Law Firm", "pos": "Position", "link": "Job Listing", "open_date": "Open Date"},
    {"key": "piAttorneyOpen", "rows": "flat", "audience": "attorney",
     "section": "New Public Interest Openings",
     "name": "Organization", "pos": "Job Title", "link": "Apply Here",
     "open_date": "Application Open Date", "close_date": "Application Close Date"},
]

MONTHS = ["", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def _norm(s) -> str:
    s = "" if s is None else str(s)
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s.rstrip(".,;: ")


def _link_href(cell):
    return cell.get("href") if isinstance(cell, dict) else None


def _row_key(cfg, row):
    """Stable identity: Flo job id from the listing link, else normalized name|pos."""
    href = _link_href(row.get(cfg.get("link"))) if cfg.get("link") else None
    if href:
        m = JOB_ID_RE.search(href)
        if m:
            return f"job:{m.group(1)}"
    parts = [cfg["key"], _norm(row.get(cfg["name"]))]
    if cfg.get("pos"):
        parts.append(_norm(row.get(cfg["pos"])))
    return "cmp:" + "|".join(parts)


def _rows(cfg, tables):
    v = tables.get(cfg["key"])
    if v is None:
        return []
    if cfg["rows"] == "split":
        return (v.get("open") or []) + (v.get("upcoming") or [])
    return v


def _fmt_date(v):
    """'Opens 10/1/2026' / '8/20/2026' -> 'October 1, 2026'; pass through anything else."""
    if not v:
        return v
    s = str(v).replace("Opens ", "").strip()
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if m:
        mo, da, yr = int(m.group(1)), int(m.group(2)), m.group(3)
        if 1 <= mo <= 12:
            return f"{MONTHS[mo]} {da}, {yr}"
    return s


def load_data(ref):
    out = subprocess.run(["git", "show", f"{ref}:{DATA_PATH}"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"cannot read {DATA_PATH} at {ref}: {out.stderr.strip()}")
    return json.loads(out.stdout).get("tables", {})


def diff(from_ref, to_ref):
    """Return a list of change dicts for a single from->to step."""
    a, b = load_data(from_ref), load_data(to_ref)
    changes = []
    for cfg in TABLES:
        ar = {_row_key(cfg, r): r for r in _rows(cfg, a)}
        br = {_row_key(cfg, r): r for r in _rows(cfg, b)}
        for k, row in br.items():
            common = {"audience": cfg["audience"], "section": cfg["section"],
                      "table": cfg["key"], "key": k,
                      "entity": row.get(cfg["name"]),
                      "pos": row.get(cfg["pos"]) if cfg.get("pos") else None,
                      "link": _link_href(row.get(cfg.get("link"))) if cfg.get("link") else None,
                      "profile": _link_href(row.get(cfg.get("profile"))) if cfg.get("profile") else None}
            if k not in ar:  # ── addition ──
                if not cfg.get("adds", True):
                    continue
                item = dict(common, kind="add")
                if cfg.get("open_date") and not cfg.get("open_as_link"):
                    item["open_date"] = _fmt_date(row.get(cfg["open_date"]))
                changes.append(item)
                continue
            old = ar[k]  # ── field changes on an existing row ──
            if cfg.get("open_date"):
                o, n = old.get(cfg["open_date"]), row.get(cfg["open_date"])
                if _norm(o) != _norm(n) and _norm(n) not in ("", "not yet open"):
                    changes.append(dict(common, kind="open_date",
                                        old=_fmt_date(o), new=_fmt_date(n)))
            if cfg.get("close_date"):
                o, n = old.get(cfg["close_date"]), row.get(cfg["close_date"])
                if _norm(o) != _norm(n):  # close-date changes -> Slack only
                    changes.append(dict(common, kind="close_date",
                                        old=_fmt_date(o), new=_fmt_date(n)))
            for col in cfg.get("date_cols", []):
                o, n = old.get(col), row.get(col)
                if _norm(o) != _norm(n):
                    changes.append(dict(common, kind="program_date", field=col,
                                        old=o, new=n))
    return changes


def commits_touching_data(since=None):
    """Commits that touched data.json, oldest->newest, each tagged bot/human."""
    fmt = "%H\x1f%ct\x1f%s"
    args = ["git", "log", f"--pretty={fmt}", "--reverse"]
    if since:
        args.append(f"--since={since} 00:00:00")
    args += ["--", DATA_PATH]
    out = subprocess.run(args, capture_output=True, text=True, check=True)
    rows = []
    for line in out.stdout.splitlines():
        h, ct, subj = line.split("\x1f", 2)
        rows.append({"sha": h, "ts": int(ct), "subject": subj,
                     "bot": subj.startswith(BOT_SUBJECT)})
    return rows


def latest_bot_sha():
    for c in reversed(commits_touching_data()):
        if c["bot"]:
            return c["sha"]
    return None


def _walk(prev, window):
    """Diff each consecutive commit in `window`; union bot-target changes, flag human ones."""
    email, flagged = {}, []
    for c in window:
        try:
            step = diff(prev, c["sha"])
        except RuntimeError:
            prev = c["sha"]
            continue
        for ch in step:
            if c["bot"]:
                email[(ch["table"], ch["key"], ch["kind"], ch.get("field"))] = ch
            else:
                flagged.append(dict(ch, human_commit=c["subject"]))
        prev = c["sha"]
    return list(email.values()), flagged


def aggregate_since_ref(from_sha):
    """Union all changes AFTER a watermark commit through the newest commit. This is what the
    daily job uses: the watermark is the last-reported bot refresh, so a Monday run naturally
    spans the whole weekend, and it's robust to failed runs / multiple refreshes in a day."""
    seq = commits_touching_data()
    idx = next((i for i, c in enumerate(seq)
                if c["sha"].startswith(from_sha) or from_sha.startswith(c["sha"])), None)
    if idx is None:  # watermark not in history (e.g. shallow clone) — fall back to last step
        bots = [c for c in seq if c["bot"]]
        return (diff(bots[-2]["sha"], bots[-1]["sha"]), []) if len(bots) >= 2 else ([], [])
    return _walk(seq[idx]["sha"], seq[idx + 1:])


def aggregate_since(since):
    """Walk consecutive data.json commits since `since`; union changes whose TARGET is a
    bot commit (genuine data). Changes landing on a human commit are flagged separately."""
    # baseline: last data.json commit at/before `since`
    base = subprocess.run(
        ["git", "log", "-1", f"--until={since} 00:00:00", "--pretty=%H", "--", DATA_PATH],
        capture_output=True, text=True).stdout.strip()
    seq = commits_touching_data(since=since)
    if not seq:
        return [], []
    prev = base or (seq[0]["sha"] + "^")
    email, flagged = {}, []
    for c in seq:
        try:
            step = diff(prev, c["sha"])
        except RuntimeError:
            prev = c["sha"]
            continue
        for ch in step:
            if c["bot"]:
                email[(ch["table"], ch["key"], ch["kind"], ch.get("field"))] = ch
            else:
                flagged.append(dict(ch, human_commit=c["subject"]))
        prev = c["sha"]
    return list(email.values()), flagged


# ── CLI ─────────────────────────────────────────────────────────────────────
def _print_summary(changes, flagged):
    by_aud = {"student": [], "attorney": []}
    slack_only = []
    for c in changes:
        if c["kind"] == "close_date":
            slack_only.append(c)
        else:
            by_aud[c["audience"]].append(c)
    for aud in ("student", "attorney"):
        items = by_aud[aud]
        print(f"\n{'='*60}\n{aud.upper()}  ({len(items)} email items)\n{'='*60}")
        secs = {}
        for c in items:
            secs.setdefault(c["section"], []).append(c)
        for sec, cs in secs.items():
            print(f"\n{sec}:")
            for c in cs:
                if c["kind"] == "add":
                    tail = f" — {c.get('open_date')}" if c.get("open_date") else \
                           (" — Open" if c.get("link") else "")
                    print(f"  + {c['entity']}{(' · ' + c['pos']) if c.get('pos') else ''}{tail}")
                elif c["kind"] == "open_date":
                    print(f"  ~ {c['entity']} — open date {c['old']} → {c['new']}")
                elif c["kind"] == "program_date":
                    print(f"  ~ {c['entity']} — {c['field']}: {c['old']!r} → {c['new']!r}")
    if slack_only:
        print(f"\n{'-'*60}\nSLACK-ONLY (close-date changes, {len(slack_only)}):")
        for c in slack_only:
            print(f"  · {c['entity']} — close date {c['old']} → {c['new']}")
    if flagged:
        print(f"\n{'-'*60}\nFLAGGED — landed on human commits, NOT auto-reported ({len(flagged)}):")
        seen = set()
        for c in flagged:
            if c["human_commit"] in seen:
                continue
            seen.add(c["human_commit"])
            n = sum(1 for x in flagged if x["human_commit"] == c["human_commit"])
            print(f"  ! [{n:>3} changes] {c['human_commit']}")


def main(argv):
    if "--since" in argv:
        since = argv[argv.index("--since") + 1]
        changes, flagged = aggregate_since(since)
        if "--json" in argv:
            print(json.dumps({"changes": changes, "flagged": flagged}, ensure_ascii=False, indent=2))
        else:
            print(f"Changes since {since} (bot-commit data only):")
            _print_summary(changes, flagged)
        return
    if len(argv) >= 2:
        changes = diff(argv[0], argv[1])
        if "--json" in argv:
            print(json.dumps(changes, ensure_ascii=False, indent=2))
        else:
            _print_summary(changes, [])
        return
    print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
