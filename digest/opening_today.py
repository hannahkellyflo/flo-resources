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

Prod: SLACK_BOT_TOKEN → chat.postMessage to SLACK_CHANNEL. Dry-run: prints (no token).
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


def _post_at_8am_ct():
    """Unix ts for 8:00 AM America/Chicago today if it's still ahead (DST-correct), else None.
    GitHub cron fires late and unpredictably, so we pin *delivery* to 8 AM via Slack rather than
    trust the run time. If the run itself lands after 8 AM CT, return None -> send immediately
    (better a bit late than pushed to tomorrow, since the content is for today)."""
    now = datetime.datetime.now(CT)
    target = now.replace(hour=8, minute=0, second=0, microsecond=0)
    return int(target.timestamp()) if target > now + datetime.timedelta(seconds=60) else None


def post(message):
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        raise RuntimeError("SLACK_BOT_TOKEN required to post")
    post_at = _post_at_8am_ct()
    payload = {"channel": CHANNEL, "text": message, "unfurl_links": False, "mrkdwn": True}
    if post_at:
        payload["post_at"] = post_at
        url = "https://slack.com/api/chat.scheduleMessage"   # delivered at 8 AM CT regardless of run time
    else:
        url = "https://slack.com/api/chat.postMessage"       # already past 8 AM CT -> send now
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"})
    res = json.load(urllib.request.urlopen(req))
    if not res.get("ok"):
        raise RuntimeError(f"slack error: {res.get('error')}")
    return res


def main(argv):
    today = datetime.date.today()
    if "--date" in argv:  # testing override, e.g. --date 2026-11-01
        today = datetime.date.fromisoformat(argv[argv.index("--date") + 1])
    # Paused window: real runs skip until RESUME_ON, then resume on their own. --dry-run/--force test through it.
    if RESUME_ON and today < RESUME_ON and "--dry-run" not in argv and "--force" not in argv:
        print(f"opening-today paused until {RESUME_ON.isoformat()} — skipping (today {today.isoformat()})")
        return
    tables = json.load(open(DATA_PATH)).get("tables", {})
    hits = find_openings(tables, target_dates(today))
    message = compose(hits, today)
    if "--dry-run" in argv or not os.environ.get("SLACK_BOT_TOKEN"):
        print(message)
    else:
        post(message)
        print("posted")


if __name__ == "__main__":
    main(sys.argv[1:])
