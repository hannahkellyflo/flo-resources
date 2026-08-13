#!/usr/bin/env python3
"""Regenerate data.json from live sources (Metabase + Airtable), then the workflow
runs build.py to embed it and commit index.html.

Design: load the committed data.json as a BASE (today's snapshot), then OVERRIDE
sections that are wired to live queries. Un-wired sections keep their snapshot values;
wire them one at a time. If a live source returns nothing, the section renders BLANK
(intentional — show what's actually there, not stale samples).

Secrets (GitHub Actions env):
  METABASE_API_KEY   - scoped service-account key; header x-api-key on POST /api/dataset
  AIRTABLE_TOKEN     - Bearer read token

Run:  METABASE_API_KEY=… AIRTABLE_TOKEN=… python3 generate.py
"""
import json, os, re, html, urllib.request, urllib.parse, pathlib, datetime

PIPE = pathlib.Path(__file__).parent
DATA_JSON = PIPE / "data.json"

METABASE_URL = "https://flo-recruit.metabaseapp.com"
AIRTABLE_BASE = "appi5xzw51C2e58PR"
TODAY = datetime.date.today()

MB_KEY = os.environ.get("METABASE_API_KEY", "").strip()
AT_TOKEN = os.environ.get("AIRTABLE_TOKEN", "").strip()


# ── HTTP helpers ──────────────────────────────────────────────────────────────
def metabase_sql(database_id: int, sql: str) -> list[dict]:
    """Run native SQL via the Metabase dataset API; return rows as list of dicts."""
    req = urllib.request.Request(
        f"{METABASE_URL}/api/dataset",
        data=json.dumps({"database": database_id, "type": "native",
                         "native": {"query": sql}}).encode(),
        headers={"Content-Type": "application/json", "x-api-key": MB_KEY},
        method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        res = json.load(r)
    cols = [c["name"] for c in res["data"]["cols"]]
    return [dict(zip(cols, row)) for row in res["data"]["rows"]]


def airtable_records(table_id: str, field_ids: list[str]) -> list[dict]:
    """Fetch all records (paginated) from an Airtable table via the REST API."""
    out, offset = [], None
    while True:
        params = [("returnFieldsByFieldId", "true"), ("pageSize", "100")]
        params += [("fields[]", f) for f in field_ids]
        if offset:
            params.append(("offset", offset))
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{table_id}?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {AT_TOKEN}"})
        with urllib.request.urlopen(req, timeout=60) as r:
            res = json.load(r)
        out.extend(res.get("records", []))
        offset = res.get("offset")
        if not offset:
            return out


# ── small utils ───────────────────────────────────────────────────────────────
def fmt_date(iso: str | None) -> str:
    """'2026-07-15' -> 'Jul 15, 2026'; '' / None -> '—'."""
    if not iso:
        return "—"
    try:
        d = datetime.date.fromisoformat(iso[:10])
        return d.strftime("%b %-d, %Y")
    except ValueError:
        return iso


def apply_link(richtext: str | None):
    """The 'Apply on Flo Forward' field is a Flo URL wrapped in <>. -> {text,href} or '—'."""
    if not richtext:
        return "—"
    m = re.search(r"https?://\S+", richtext)
    return {"text": "Apply", "href": m.group(0).rstrip(">")} if m else "—"


# ── PUBLIC INTEREST (Airtable, LIVE) ─────────────────────────────────────────
# Source: tblLw1ZX1As4nTKDl. Bucket by EARLIEST targeted JD grad year:
#   min <= 2025 -> Attorney;  2026/2027 -> Entry-Level;  2028/2029 -> Internships.
# Open vs Past: past = close date has passed; auto-removed 30 days after close.
PI_TABLE = "tblLw1ZX1As4nTKDl"
PI_F = {"org": "fldKjqVMve8XOBQNs", "title": "fldsjcEMbh9O0LAg9", "apply": "fld9FL1tdAoo5xfd2",
        "loc": "fldrMW9cz2ybhiKkW", "comp": "fldWr5bZXbAL3CWvG", "gov": "fldvnrDSFimercAG3",
        "desc": "fldsI4862SJND6miB", "open": "fldRxM0vfBGih8w1l", "close": "fldNqRfq3gXeerGWG",
        "grad": "fldJMdOy91wy7ByAq"}


def pi_bucket(grad_cells) -> str:
    # multipleSelects: REST returns ["2026", ...]; MCP returns [{"name":"2026"}, ...]
    years = []
    for c in (grad_cells or []):
        name = c.get("name", "") if isinstance(c, dict) else str(c)
        if name.isdigit():
            years.append(int(name))
    if not years:
        return "attorney"          # no signal -> treat as experienced/attorney
    lo = min(years)
    return "attorney" if lo <= 2025 else ("extern" if lo <= 2027 else "summer")


def pi_record(f: dict) -> dict:
    g = f.get(PI_F["gov"])
    return {
        "Organization": f.get(PI_F["org"]) or "—",
        "Job Title": f.get(PI_F["title"]) or "—",
        "Apply Here": apply_link(f.get(PI_F["apply"])),
        "Location(s)": f.get(PI_F["loc"]) or "—",
        "Compensation": f.get(PI_F["comp"]) or "—",
        "Government": bool(g),
        "Job Description": (f.get(PI_F["desc"]) or "—"),
        "Application Open Date": fmt_date(f.get(PI_F["open"])),
        "Application Close Date": fmt_date(f.get(PI_F["close"])),
        "Posted Date": "—",   # createdTime handled below (not a fieldId)
    }


def wire_public_interest(data: dict) -> None:
    recs = airtable_records(PI_TABLE, list(PI_F.values()))
    buckets = {b: {"open": [], "past": []} for b in ("summer", "extern", "attorney")}
    for r in recs:
        f = r.get("fields", {})   # REST API keys fields under "fields" (by field id via returnFieldsByFieldId)
        rec = pi_record(f)
        rec["Posted Date"] = fmt_date(r.get("createdTime"))
        # open vs past by close date (past kept only for 30 days after close)
        close = f.get(PI_F["close"])
        state = "open"
        if close:
            try:
                cd = datetime.date.fromisoformat(close[:10])
                if cd < TODAY:
                    state = "past" if (TODAY - cd).days <= 30 else "drop"
            except ValueError:
                pass
        if state == "drop":
            continue
        buckets[pi_bucket(f.get(PI_F["grad"]))][state].append(rec)
    m = {"summer": "piSummer", "extern": "piExtern", "attorney": "piAttorney"}
    for b, key in m.items():
        data["tables"][f"{key}Open"] = buckets[b]["open"]
        data["tables"][f"{key}Past"] = buckets[b]["past"]
    n = sum(len(v["open"]) + len(v["past"]) for v in buckets.values())
    print(f"  public interest: {len(recs)} records -> {n} bucketed")


# ── CAMPUS + EXAMS (Airtable, LIVE) ──────────────────────────────────────────
# Same table tbl3TysOhuqGmnTp6. Public filter (Hannah 2026-08-12):
#   campus: status == Approved AND Recruiting-For in the current cycles
#           {1L Summer 2027, 2L Summer 2028, 2L Summer 2027} (Class of 2028 & 2029);
#           drops old "1L Summer 2026" and "Other".
#   exams:  status == Approved, one row per school (school-level exam/grade facts).
CAMPUS_TABLE = "tbl3TysOhuqGmnTp6"
STATUS_F = "fldxmMbFRt7ZmP1Zn"
CAMPUS_CYCLES = {"1L Summer 2027", "2L Summer 2028", "2L Summer 2027"}

CAMPUS_F = {"school": "fldMX6usDsVcPL5mv", "program": "fldia9d25thQk2XZD",
            "sector": "fldTUQOTFLVQMqvlJ", "recruiting": "fldeM4oZQubYnfDkj",
            "progDates": "fld0ptuFrxywALle1", "regLink": "fldO18qW51Y8Pp7u3",
            "regDates": "fldPvaLGnarml45Ut", "virtual": "fldZO9ShTm1e2gpQT",
            "format": "fld3vosa24Mywu4QK", "contactName": "fldpDGxas6jiDS9A4",
            "contactEmail": "fldigmcw7jmnWVbXD", "bidding": "flddvClqs4cWWO13W",
            "initRelease": "fldGgxzEt1DUDxfO5", "finalRelease": "fldcj7lfD7OQG8WMU",
            "addlInfo": "fldzRMQiWHC8HQCno", "updated": "fldKmUHPxskiftnIh"}
EXAMS_F = {"school": "fldMX6usDsVcPL5mv", "grades1": "fldHVmAIeSG6VonqF",
           "grades2": "fldhnelSoLqhY6qno", "gradesNotes": "fld1VKn9gTsmjionb",
           "exams1": "fldiIpsyrAnauwtzU", "exams2": "fldN0a2xtUQcUxt2L",
           "examsNotes": "fldjtEPxSqwFzkAQa"}


def _sel(v):   # singleSelect: REST -> str, MCP -> {"name":..}
    return v.get("name", "") if isinstance(v, dict) else (v or "")


def _multi(v):  # multipleSelects: REST -> [str], MCP -> [{"name":..}]
    if not isinstance(v, list):
        return _sel(v)
    return ", ".join(x.get("name", "") if isinstance(x, dict) else str(x) for x in v)


def _txt(v):
    return v.strip() if isinstance(v, str) else (v or "")


def fmt_mdy(iso) -> str:
    """date/lastModifiedTime -> 'M/D/YYYY'; empty -> ''."""
    if not iso:
        return ""
    try:
        d = datetime.date.fromisoformat(str(iso)[:10])
        return f"{d.month}/{d.day}/{d.year}"
    except ValueError:
        return str(iso)


def campus_record(f: dict) -> dict:
    reg, email = f.get(CAMPUS_F["regLink"]), f.get(CAMPUS_F["contactEmail"])
    return {
        "Law School": _txt(f.get(CAMPUS_F["school"])),
        "Program": _txt(f.get(CAMPUS_F["program"])),
        "Sector": _multi(f.get(CAMPUS_F["sector"])),
        "Recruiting For": _multi(f.get(CAMPUS_F["recruiting"])),
        "Program Dates": _txt(f.get(CAMPUS_F["progDates"])),
        "Employer Registration Link": {"text": reg, "href": reg} if reg else "",
        "Employer Registration Dates": _txt(f.get(CAMPUS_F["regDates"])),
        "Virtual vs. In-Person": _sel(f.get(CAMPUS_F["virtual"])),
        "Format": _multi(f.get(CAMPUS_F["format"])),
        "Program Contact - Name": _txt(f.get(CAMPUS_F["contactName"])),
        "Program Contact - Email": {"text": email, "href": f"mailto:{email}"} if email else "",
        "Student Bidding / Application Dates": _txt(f.get(CAMPUS_F["bidding"])),
        "Initial Employer Schedule Release Date": fmt_mdy(f.get(CAMPUS_F["initRelease"])),
        "Final Schedule Release Date": fmt_mdy(f.get(CAMPUS_F["finalRelease"])),
        "Additional Info": _txt(f.get(CAMPUS_F["addlInfo"])),
        "Last updated": fmt_mdy(f.get(CAMPUS_F["updated"])),
    }


def exams_record(f: dict) -> dict:
    return {
        "Law School": _txt(f.get(EXAMS_F["school"])),
        "First Semester Grades Available": _txt(f.get(EXAMS_F["grades1"])),
        "Second Semester Grades Available": _txt(f.get(EXAMS_F["grades2"])),
        "Career Services Notes on Grades": _txt(f.get(EXAMS_F["gradesNotes"])),
        "First Semester Exam Dates": _txt(f.get(EXAMS_F["exams1"])),
        "Second Semester Exam Dates": _txt(f.get(EXAMS_F["exams2"])),
        "Career Services Notes on Exams": _txt(f.get(EXAMS_F["examsNotes"])),
    }


def wire_campus_exams(data: dict) -> None:
    recs = airtable_records(CAMPUS_TABLE, sorted({*CAMPUS_F.values(), *EXAMS_F.values(), STATUS_F}))
    campus, exams = [], {}   # exams: school -> (updated, record), latest wins
    for r in recs:
        f = r.get("fields", {})
        if _sel(f.get(STATUS_F)) != "Approved":
            continue
        rvals = f.get(CAMPUS_F["recruiting"]) or []
        rnames = [x.get("name", "") if isinstance(x, dict) else str(x) for x in rvals] \
            if isinstance(rvals, list) else [_sel(rvals)]
        if any(v in CAMPUS_CYCLES for v in rnames) and f.get(CAMPUS_F["school"]) and f.get(CAMPUS_F["program"]):
            campus.append(campus_record(f))
        school = f.get(EXAMS_F["school"])
        has_exam = any(f.get(EXAMS_F[k]) for k in
                       ("grades1", "grades2", "gradesNotes", "exams1", "exams2", "examsNotes"))
        if school and has_exam:
            upd = f.get(CAMPUS_F["updated"]) or ""
            if school not in exams or upd > exams[school][0]:
                exams[school] = (upd, exams_record(f))
    campus.sort(key=lambda r: (r["Law School"], r["Program"]))
    data["tables"]["campus"] = campus
    data["tables"]["exams"] = [rec for _, (_, rec) in sorted(exams.items())]
    print(f"  campus/exams: {len(recs)} records -> {len(campus)} campus (Approved, current cycle), "
          f"{len(data['tables']['exams'])} exams schools")


# ── LATERAL NON-PARTNER + POST-JUDICIAL-CLERKSHIP (Metabase db 2, LIVE) ───────
# Base = #5413 filters: published + not-deleted + ATS/null job type + LAW_FIRM +
# demo orgs excluded. Offices via JOB_OFFICE->ORG_OFFICE->STATIC_LIST_OPTION.
MB_DB = 2
# NOTE: \\b (two backslashes) is REQUIRED — MySQL's string-literal parser consumes one
# backslash, so the SQL text needs \\b for REGEXP to see a \b word boundary. Verified:
# 'example company' REGEXP '\\bexample' = 1, but REGEXP '\bexample' = 0.
DEMO_REGEXP = (r"demo\\b|\\btest|sandbox|\\bexample|\\bacme\\b|\\bsample\\b|playground|"
               r"employer|flo recruit|flo-recruit|flo firm|dupes|hartwell cross")

_JOB_SELECT = """
SELECT j.ID AS job_id, o.NAME AS firm, j.TITLE AS position,
  j.DESCRIPTION AS descr, j.OPEN_DATE AS open_date, j.UPDATED_AT AS updated_at,
  GROUP_CONCAT(DISTINCT ht.NAME) AS hiring_types,
  (SELECT GROUP_CONCAT(DISTINCT loc.OPTION SEPARATOR '; ')
     FROM JOB_OFFICE jo JOIN ORG_OFFICE ofc ON ofc.ID = jo.OFFICE_ID
     JOIN STATIC_LIST_OPTION loc ON loc.ID = ofc.OFFICE_LOCATION_ID
     WHERE jo.JOB_ID = j.ID) AS offices
FROM JOB j
JOIN ORG o ON o.ID = j.ORG_ID
LEFT JOIN JOB_HIRING_TYPE jht ON jht.JOB_ID = j.ID
LEFT JOIN HIRING_TYPE ht ON ht.ID = jht.HIRING_TYPE_ID
WHERE j.FORWARD_PUBLISHING_STATUS = 'PUBLISHED' AND j.DELETED_AT IS NULL
  AND (j.JOB_TYPE = 'ATS' OR j.JOB_TYPE IS NULL) AND j.JOB_CLASSIFICATION = 'LAW_FIRM'
  AND LOWER(o.NAME) NOT REGEXP '%s'
  AND (%s)
GROUP BY j.ID, o.NAME, j.TITLE, j.DESCRIPTION, j.OPEN_DATE, j.UPDATED_AT
ORDER BY j.OPEN_DATE DESC;""" % (DEMO_REGEXP, "%s")

LATERAL_WHERE = """
  EXISTS (SELECT 1 FROM JOB_HIRING_TYPE j2 JOIN HIRING_TYPE h2 ON h2.ID=j2.HIRING_TYPE_ID
          WHERE j2.JOB_ID=j.ID AND h2.NAME IN ('Lateral Associate','Lateral Counsel','Staff Attorney'))
  AND NOT EXISTS (SELECT 1 FROM JOB_HIRING_TYPE j3 JOIN HIRING_TYPE h3 ON h3.ID=j3.HIRING_TYPE_ID
                  WHERE j3.JOB_ID=j.ID AND h3.NAME='Lateral Partner')"""

PC_WHERE = """
  EXISTS (SELECT 1 FROM JOB_HIRING_TYPE j2 JOIN HIRING_TYPE h2 ON h2.ID=j2.HIRING_TYPE_ID
          WHERE j2.JOB_ID=j.ID AND h2.NAME='Judicial Clerk')
  OR LOWER(j.TITLE) REGEXP 'post[- ]clerkship'"""


def strip_html(s) -> str:
    if not s:
        return "—"
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s or "—"


def job_record(row: dict, type_val: str) -> dict:
    jid = row.get("job_id")
    return {
        "Law Firm": row.get("firm") or "—",
        "Job Listing": {"text": "View listing",
                        "href": f"https://florecruit.com/v2/app/forward/jobs/{jid}"},
        "Position": row.get("position") or "—",
        "Offices": row.get("offices") or "—",
        "Job Description": strip_html(row.get("descr")),
        "Open Date": fmt_date(row.get("open_date")),
        "Type": type_val,
        "Last Updated": fmt_date(row.get("updated_at")),
    }


def wire_lateral(data: dict) -> None:
    rows = metabase_sql(MB_DB, _JOB_SELECT % LATERAL_WHERE)

    def typ(hts):
        s = hts or ""
        return ("Associate" if "Lateral Associate" in s else
                "Counsel" if "Lateral Counsel" in s else
                "Staff Attorney" if "Staff Attorney" in s else "Associate")
    data["tables"]["lateral"] = [job_record(r, typ(r.get("hiring_types"))) for r in rows]
    print(f"  lateral: {len(rows)} non-partner listings")


def wire_pc(data: dict) -> None:
    rows = metabase_sql(MB_DB, _JOB_SELECT % PC_WHERE)
    data["tables"]["pc"] = [
        job_record(r, "Judicial Clerk" if "Judicial Clerk" in (r.get("hiring_types") or "")
                   else "Post-Judicial Clerkship")
        for r in rows]
    print(f"  post-judicial-clerkship: {len(rows)} listings")


# ── 3L ENTRY-LEVEL (Metabase db 2, LIVE) ─────────────────────────────────────
# grad-target year 2027 (FORWARD_JOB_GRAD_DATE_TARGET_RULE) is a noisy proxy — it
# also matches summer/intern/vacation-scheme/OCI/lateral roles carrying a stray 2027
# target, so a heavy title-noise exclusion is required (grad-target alone over-counts ~3x).
# Airtable "3L Hiring" page is empty today, so this is Metabase-only.
ENTRY3L_WHERE = r"""
  EXISTS (SELECT 1 FROM FORWARD_JOB_GRAD_DATE_TARGET_RULE r
          WHERE r.JOB_ID = j.ID AND r.IS_NOT_DELETED = 1
            AND r.RULE_TYPE = 'INDIVIDUAL_YEARS' AND YEAR(r.MIN_GRAD_DATE) = 2027)
  AND LOWER(j.TITLE) NOT REGEXP 'summer|intern|extern|clerk|test|vacation|fellowship|networking|\\boci\\b|resume|general submission|general consideration|\\blateral\\b|managing counsel|training contract|sign.?up|\\bselsc\\b|\\b1l\\b|\\b2l\\b'"""


def wire_entry3l(data: dict) -> None:
    rows = metabase_sql(MB_DB, _JOB_SELECT % ENTRY3L_WHERE)
    data["tables"]["entry3l"] = [{
        "Employer": r.get("firm") or "—",
        "3L Position": r.get("position") or "—",
        "3L Job Listing": {"text": "View listing",
                           "href": f"https://florecruit.com/v2/app/forward/jobs/{r.get('job_id')}"},
        "Offices": r.get("offices") or "—",
        "Practices, If Specified": "",       # not reliably derivable -> muted em-dash
        "Bar Admission, If Required": "",
        "Last Updated": fmt_date(r.get("updated_at")),
    } for r in rows]
    print(f"  entry3l: {len(rows)} 3L entry-level listings")


# ── 1L / 2L SUMMER SPLIT (Metabase db 2, LIVE) ───────────────────────────────
# Law-student set (Law Student tag OR summer-ish title, minus lateral/partner/
# paralegal/staff/3L guard). Level split by title token: 1L table = has '1l' OR no
# token; 2L table = has '2l' OR no token; no-token roles appear in BOTH (Hannah).
# No cycle window (Hannah 2026-08-12: show all). open = open now & deadline not passed;
# upcoming = open date in the future. Firm Profile -> '—' (no slug in Metabase, Hannah).
SUMMER_SQL = """
SELECT j.ID AS job_id, o.NAME AS firm, j.TITLE AS position,
  j.OPEN_DATE AS open_date, j.CLOSE_DATE AS close_date,
  (SELECT GROUP_CONCAT(DISTINCT loc.OPTION SEPARATOR '; ')
     FROM JOB_OFFICE jo JOIN ORG_OFFICE ofc ON ofc.ID = jo.OFFICE_ID
     JOIN STATIC_LIST_OPTION loc ON loc.ID = ofc.OFFICE_LOCATION_ID
     WHERE jo.JOB_ID = j.ID) AS offices
FROM JOB j JOIN ORG o ON o.ID = j.ORG_ID
WHERE j.FORWARD_PUBLISHING_STATUS = 'PUBLISHED' AND j.DELETED_AT IS NULL
  -- law-student jobs are mostly MANUAL_ENTRY (not ATS) — must include both
  AND (j.JOB_TYPE IN ('ATS','MANUAL_ENTRY') OR j.JOB_TYPE IS NULL) AND j.JOB_CLASSIFICATION = 'LAW_FIRM'
  AND LOWER(o.NAME) NOT REGEXP '%s'
  AND (EXISTS (SELECT 1 FROM JOB_HIRING_TYPE jh JOIN HIRING_TYPE h ON h.ID=jh.HIRING_TYPE_ID
               WHERE jh.JOB_ID=j.ID AND h.NAME='Law Student')
       OR LOWER(j.TITLE) REGEXP 'summer associate|summer program|\\\\b1l\\\\b|\\\\b2l\\\\b|summer law|summer clerk|summer intern|summer fellow|summer scholar')
  AND LOWER(j.TITLE) NOT REGEXP 'lateral|partner|paralegal|staff attorney|\\\\b3l\\\\b'
ORDER BY j.OPEN_DATE DESC;""" % DEMO_REGEXP


def _close_passed(close) -> bool:
    if not close:
        return False
    try:
        return datetime.date.fromisoformat(str(close)[:10]) < TODAY
    except ValueError:
        return False


def _summer_record(r: dict, lvl: str, upcoming: bool) -> dict:
    jid = r.get("job_id")
    od = fmt_mdy(r.get("open_date"))
    return {
        f"{lvl} Application Open Date": (f"Opens {od}" if upcoming else od) or "—",
        "Employer": r.get("firm") or "—",
        f"{lvl} Job Listing": ("Not yet open" if upcoming else
                               {"text": "Apply", "href": f"https://florecruit.com/v2/app/forward/jobs/{jid}"}),
        "Firm Profile": "—",
        f"{lvl} Position": r.get("position") or "—",
        "Office Location": r.get("offices") or "—",
        "Scholarship": "—",
        "Application Close Date": fmt_mdy(r.get("close_date")) or "—",
    }


def wire_summer_split(data: dict) -> None:
    rows = metabase_sql(MB_DB, SUMMER_SQL)
    out = {"1L": {"open": [], "upcoming": []}, "2L": {"open": [], "upcoming": []}}
    now = datetime.datetime.now(datetime.timezone.utc)
    for r in rows:
        t = (r.get("position") or "").lower()
        has1, has2 = re.search(r"\b1l\b", t) is not None, re.search(r"\b2l\b", t) is not None
        levels = [lv for lv, keep in (("1L", has1 or not has2), ("2L", has2 or not has1)) if keep]
        od = r.get("open_date")
        upcoming = bool(od) and str(od)[:10] > now.date().isoformat()
        if not upcoming and _close_passed(r.get("close_date")):
            continue                       # deadline passed -> not open
        for lv in levels:
            out[lv]["upcoming" if upcoming else "open"].append(_summer_record(r, lv, upcoming))
    for lv, key in (("1L", "summer1L"), ("2L", "summer2L")):
        # open newest-first (already sorted desc), upcoming soonest-first
        out[lv]["upcoming"].reverse()
        data["tables"][key] = out[lv]
    print(f"  summer split: 1L {len(out['1L']['open'])} open/{len(out['1L']['upcoming'])} upcoming, "
          f"2L {len(out['2L']['open'])} open/{len(out['2L']['upcoming'])} upcoming")


# ── MARKET CHARTS (Metabase db 2, LIVE) ──────────────────────────────────────
# Wiring the CLEAN aggregations (timelines + window totals). The judgment-heavy chart
# data stays on snapshot until validated: *.practiceByWindow/practice (title-derived),
# *.marketByWindow/market (office-city), *.gradByWindow, *.source (candidate funnel),
# and lawStudent headcount-split series.
LATERAL_BASE = """
FROM JOB j JOIN ORG o ON o.ID = j.ORG_ID
WHERE j.DELETED_AT IS NULL
  AND (j.JOB_TYPE = 'ATS' OR j.JOB_TYPE IS NULL) AND j.JOB_CLASSIFICATION = 'LAW_FIRM'
  AND LOWER(o.NAME) NOT REGEXP '%s'
  AND EXISTS (SELECT 1 FROM JOB_HIRING_TYPE j2 JOIN HIRING_TYPE h2 ON h2.ID=j2.HIRING_TYPE_ID
              WHERE j2.JOB_ID=j.ID AND h2.NAME IN ('Lateral Associate','Lateral Counsel','Staff Attorney'))
  AND NOT EXISTS (SELECT 1 FROM JOB_HIRING_TYPE j3 JOIN HIRING_TYPE h3 ON h3.ID=j3.HIRING_TYPE_ID
                  WHERE j3.JOB_ID=j.ID AND h3.NAME='Lateral Partner')""" % DEMO_REGEXP


def monthly12(rows, year: int, yr_key="yr", mo_key="mo", n_key="n") -> list:
    """12-element Jan..Dec array of counts for `year`; the current partial month and
    all future months are null (avoids a misleading dip at the in-progress month)."""
    by = {int(r[mo_key]): int(r[n_key]) for r in rows if int(r[yr_key]) == year}
    out = []
    for m in range(1, 13):
        complete = year < TODAY.year or (year == TODAY.year and m < TODAY.month)
        out.append(by.get(m, 0) if complete else None)
    return out


def _job_window_totals(base_where: str) -> dict:
    """open (published now) ⊆ 3mo ⊆ 12mo (published OR OPEN_DATE within the window)."""
    r = metabase_sql(MB_DB, f"""
SELECT SUM(CASE WHEN j.FORWARD_PUBLISHING_STATUS='PUBLISHED' THEN 1 ELSE 0 END) AS open_now,
  SUM(CASE WHEN j.FORWARD_PUBLISHING_STATUS='PUBLISHED' OR j.OPEN_DATE >= DATE_SUB(NOW(), INTERVAL 3 MONTH) THEN 1 ELSE 0 END) AS w3,
  SUM(CASE WHEN j.FORWARD_PUBLISHING_STATUS='PUBLISHED' OR j.OPEN_DATE >= DATE_SUB(NOW(), INTERVAL 12 MONTH) THEN 1 ELSE 0 END) AS w12
{base_where}""")[0]
    return {"open": int(r["open_now"]), "3mo": int(r["w3"]), "12mo": int(r["w12"])}


def wire_lateral_charts(data: dict) -> None:
    tl = metabase_sql(MB_DB, f"""
SELECT YEAR(j.OPEN_DATE) AS yr, MONTH(j.OPEN_DATE) AS mo, COUNT(DISTINCT j.ID) AS n
{LATERAL_BASE} AND YEAR(j.OPEN_DATE) IN (2025, 2026)
GROUP BY yr, mo""")
    ch = data["charts"]["lateral"]
    ch["timeline"] = {"2025": monthly12(tl, 2025), "2026": monthly12(tl, 2026)}
    ch["totalByWindow"] = _job_window_totals(LATERAL_BASE)
    print(f"  lateral charts: timeline + totals {ch['totalByWindow']}")


def cycle_series(by: dict, cycle_start_year: int, axis_start=6) -> list:
    """12-elem array on a cycle axis starting at `axis_start` month (6=Jun..May).
    `by` = {(yr,mo): n}. Current partial month + future are null."""
    out = []
    for i in range(12):
        mo = (axis_start - 1 + i) % 12 + 1
        yr = cycle_start_year + (1 if mo < axis_start else 0)
        complete = (yr, mo) < (TODAY.year, TODAY.month)
        out.append(by.get((yr, mo), 0) if complete else None)
    return out


# Lateral PARTNER timeline uses tag OR title (the 'Lateral Partner' tag was ~absent
# before Jul 2025, so pre-2025-07 points are a title-match FLOOR, not exact).
PARTNER_WHERE = """
FROM JOB j JOIN ORG o ON o.ID = j.ORG_ID
WHERE j.DELETED_AT IS NULL
  AND (j.JOB_TYPE = 'ATS' OR j.JOB_TYPE IS NULL) AND j.JOB_CLASSIFICATION = 'LAW_FIRM'
  AND LOWER(o.NAME) NOT REGEXP '%s'
  AND (EXISTS (SELECT 1 FROM JOB_HIRING_TYPE j2 JOIN HIRING_TYPE h2 ON h2.ID=j2.HIRING_TYPE_ID
               WHERE j2.JOB_ID=j.ID AND h2.NAME='Lateral Partner')
       OR (LOWER(j.TITLE) REGEXP 'partner'
           AND LOWER(j.TITLE) NOT REGEXP 'non-partner|nonpartner|partnership program|partner development|business|assistant|paralegal|counsel to|of counsel'))""" % DEMO_REGEXP

# 3L grad-target-year timeline: same noise exclusion as the entry3l table.
THREEL_NOISE = (r"summer|intern|extern|clerk|test|vacation|fellowship|networking|\\boci\\b|resume|"
                r"general submission|general consideration|\\blateral\\b|managing counsel|"
                r"training contract|sign.?up|\\bselsc\\b|\\b1l\\b|\\b2l\\b")


def wire_partner_charts(data: dict) -> None:
    tl = metabase_sql(MB_DB, f"""
SELECT YEAR(j.OPEN_DATE) AS yr, MONTH(j.OPEN_DATE) AS mo, COUNT(DISTINCT j.ID) AS n
{PARTNER_WHERE} AND YEAR(j.OPEN_DATE) IN (2025, 2026)
GROUP BY yr, mo""")
    data["charts"]["partner"]["timeline"] = {"2025": monthly12(tl, 2025), "2026": monthly12(tl, 2026)}
    print(f"  partner charts: timeline")


def wire_threeL_charts(data: dict) -> None:
    rows = metabase_sql(MB_DB, """
SELECT r.gy AS gyear, YEAR(j.OPEN_DATE) AS yr, MONTH(j.OPEN_DATE) AS mo, COUNT(DISTINCT j.ID) AS n
FROM JOB j JOIN ORG o ON o.ID = j.ORG_ID
JOIN (SELECT DISTINCT JOB_ID, YEAR(MIN_GRAD_DATE) AS gy FROM FORWARD_JOB_GRAD_DATE_TARGET_RULE
      WHERE IS_NOT_DELETED = 1 AND RULE_TYPE = 'INDIVIDUAL_YEARS') r ON r.JOB_ID = j.ID AND r.gy IN (2026, 2027)
WHERE j.DELETED_AT IS NULL
  AND (j.JOB_TYPE = 'ATS' OR j.JOB_TYPE IS NULL) AND j.JOB_CLASSIFICATION = 'LAW_FIRM'
  AND LOWER(o.NAME) NOT REGEXP '%s'
  AND LOWER(j.TITLE) NOT REGEXP '%s'
  AND j.OPEN_DATE >= '2025-06-01' AND j.OPEN_DATE < '2027-06-01'
GROUP BY gyear, yr, mo""" % (DEMO_REGEXP, THREEL_NOISE))
    by = {gy: {(int(r["yr"]), int(r["mo"])): int(r["n"]) for r in rows if int(r["gyear"]) == gy}
          for gy in (2026, 2027)}
    data["charts"]["threeL"]["timeline"] = {
        "2026": cycle_series(by[2026], 2025),   # Class of 2026 cycle: Jun 2025 – May 2026
        "2027": cycle_series(by[2027], 2026),   # Class of 2027 cycle: Jun 2026 – May 2027
    }
    print(f"  3L charts: timeline")


# Post-clerkship market = firm-hosted judicial-clerk RECEPTIONS (EVENTS) + registrations
# (RATTENDEES.EID→EVENTS.ID). Cycle Sep→Aug. Validated cycle totals 11/265, 15/375,
# 24/799, 26/1112 vs snapshot 11/265, 16/378, 24/799, 26/1113.
PC_EVENTS_WHERE = """
FROM EVENTS e JOIN ORG o ON o.ID = e.OID
LEFT JOIN RATTENDEES ra ON ra.EID = e.ID
WHERE LOWER(e.NAME) REGEXP 'clerk' AND LOWER(e.NAME) REGEXP 'reception'
  AND LOWER(e.NAME) NOT REGEXP 'interview|mock|test|1l|diversity|summer'
  AND o.UNIVERSITY = 0
  AND LOWER(o.NAME) NOT REGEXP '%s'
  AND e.DATE >= '2022-09-01'""" % DEMO_REGEXP


def wire_postclerk_charts(data: dict) -> None:
    rows = metabase_sql(MB_DB, f"""
SELECT YEAR(e.DATE) AS yr, MONTH(e.DATE) AS mo,
  COUNT(DISTINCT e.ID) AS events, COUNT(ra.ID) AS regs
{PC_EVENTS_WHERE}
GROUP BY yr, mo""")
    ev = {(int(r["yr"]), int(r["mo"])): int(r["events"]) for r in rows}
    rg = {(int(r["yr"]), int(r["mo"])): int(r["regs"]) for r in rows}
    ch = data["charts"]["postClerk"]
    ch["events"] = {f"{cy}-{cy+1}": cycle_series(ev, cy, 9) for cy in range(2022, 2027)}
    ch["registrations"] = {f"{cy}-{cy+1}": cycle_series(rg, cy, 9) for cy in range(2022, 2027)}
    # registrationsAnnual stays on snapshot (the '2026-27 est.' dashed projection is a
    # product call — replace with a real bar once that cycle has volume).
    print(f"  post-clerkship charts: events + registrations")


# ── TODO: remaining chart segments (wire incrementally) ──────────────────────
# lawStudent.*  -> dashboard-661 aggregations (appsubs/postings/net/accounts clean;
#                  outreach/lf need the <500/500+ pendo headcount split)
# *.practice*/market*/grad*/source + *.totalByWindow bars + postClerk.registrationsAnnual
#   -> judgment-heavy / product calls, stay on snapshot
WIRED = [wire_public_interest, wire_campus_exams, wire_lateral, wire_pc, wire_entry3l,
         wire_summer_split, wire_lateral_charts, wire_partner_charts, wire_threeL_charts,
         wire_postclerk_charts]


def main() -> None:
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))  # snapshot base
    print(f"loaded snapshot; wiring {len(WIRED)} live section(s)")
    for fn in WIRED:
        fn(data)
    data.setdefault("meta", {})["generatedAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    DATA_JSON.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {DATA_JSON}")


if __name__ == "__main__":
    if not AT_TOKEN:
        raise SystemExit("AIRTABLE_TOKEN not set")
    main()
