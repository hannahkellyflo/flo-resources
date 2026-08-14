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
  -- ATS + MANUAL_ENTRY (both are real Forward postings; ATS-only was an over-filter
  -- inherited from the attorney base — it dropped MANUAL_ENTRY 3L roles like Latham).
  -- lateral/pc are tag-gated so unaffected; entry3l gains its MANUAL_ENTRY roles.
  AND (j.JOB_TYPE IN ('ATS','MANUAL_ENTRY') OR j.JOB_TYPE IS NULL) AND j.JOB_CLASSIFICATION = 'LAW_FIRM'
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
# paralegal/staff/3L guard). Level split by GRAD-TARGET YEAR (Hannah 2026-08-12):
# Summer 2027 is two different classes — 1L table = Class of 2029 (grad-target 2029),
# 2L table = Class of 2028 (grad-target 2028). This is the reliable structured signal
# (every open summer role carries a grad-target rule); title-token split was wrong
# (dumped generic "Summer Associate" roles into both, inflating the 1L table). The 1L
# table is small until 1L recruiting opens (~Dec); the 2L table is the large one.
# open = open now & deadline not passed; upcoming = open date in the future.
# Firm Profile -> '—' (no slug in Metabase, Hannah).
SUMMER_SQL = """
SELECT j.ID AS job_id, o.NAME AS firm, j.TITLE AS position,
  j.OPEN_DATE AS open_date, j.CLOSE_DATE AS close_date,
  EXISTS (SELECT 1 FROM FORWARD_JOB_GRAD_DATE_TARGET_RULE r WHERE r.JOB_ID=j.ID
          AND r.IS_NOT_DELETED=1 AND r.RULE_TYPE='INDIVIDUAL_YEARS' AND YEAR(r.MIN_GRAD_DATE)=2029) AS g1L,
  EXISTS (SELECT 1 FROM FORWARD_JOB_GRAD_DATE_TARGET_RULE r WHERE r.JOB_ID=j.ID
          AND r.IS_NOT_DELETED=1 AND r.RULE_TYPE='INDIVIDUAL_YEARS' AND YEAR(r.MIN_GRAD_DATE)=2028) AS g2L,
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
    season_start = datetime.date(now.year if now.month >= 6 else now.year - 1, 6, 1)
    mcur, scur = set(), set()  # distinct job ids opened this month / this season (as shown in the tables)
    for r in rows:
        levels = []
        if int(r.get("g1L") or 0):
            levels.append("1L")           # Class of 2029
        if int(r.get("g2L") or 0):
            levels.append("2L")           # Class of 2028
        if not levels:
            continue                       # targets neither 2028 nor 2029 -> not a 1L/2L Summer 2027 role
        od = r.get("open_date")
        upcoming = bool(od) and str(od)[:10] > now.date().isoformat()
        if not upcoming and _close_passed(r.get("close_date")):
            continue                       # deadline passed -> not open
        # count opened-in-window straight off the same rows that build the tables,
        # so the momentum tiles can't diverge from what's countable in the table
        try:
            od_d = datetime.date.fromisoformat(str(od)[:10]) if od else None
        except ValueError:
            od_d = None
        if od_d:
            jid = r.get("job_id")
            if (od_d.year, od_d.month) == (now.year, now.month):
                mcur.add(jid)
            if od_d >= season_start:
                scur.add(jid)
        for lv in levels:
            out[lv]["upcoming" if upcoming else "open"].append(_summer_record(r, lv, upcoming))
    for lv, key in (("1L", "summer1L"), ("2L", "summer2L")):
        # open newest-first (already sorted desc), upcoming soonest-first
        out[lv]["upcoming"].reverse()
        data["tables"][key] = out[lv]
    data["overview"]["_lawfirmFlow"] = {"m_cur": len(mcur), "s_cur": len(scur)}
    print(f"  summer split: 1L {len(out['1L']['open'])} open/{len(out['1L']['upcoming'])} upcoming, "
          f"2L {len(out['2L']['open'])} open/{len(out['2L']['upcoming'])} upcoming; "
          f"opened this month {len(mcur)}, this season {len(scur)}")


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


# Breakdown windows (open ⊆ 3mo ⊆ 12mo): open=published now; 3mo/12mo = published OR
# OPEN_DATE within the window. Reusable across lateral/partner/3L market + grad panels.
_WIN_CASE = ("""COUNT(DISTINCT CASE WHEN j.FORWARD_PUBLISHING_STATUS='PUBLISHED' THEN j.ID END) AS o,
  COUNT(DISTINCT CASE WHEN j.FORWARD_PUBLISHING_STATUS='PUBLISHED' OR j.OPEN_DATE>=DATE_SUB(NOW(),INTERVAL 3 MONTH) THEN j.ID END) AS w3,
  COUNT(DISTINCT CASE WHEN j.FORWARD_PUBLISHING_STATUS='PUBLISHED' OR j.OPEN_DATE>=DATE_SUB(NOW(),INTERVAL 12 MONTH) THEN j.ID END) AS w12""")
LAT_COND = f"""j.DELETED_AT IS NULL AND j.JOB_CLASSIFICATION='LAW_FIRM'
  AND LOWER(o.NAME) NOT REGEXP '{DEMO_REGEXP}'
  AND EXISTS (SELECT 1 FROM JOB_HIRING_TYPE j2 JOIN HIRING_TYPE h2 ON h2.ID=j2.HIRING_TYPE_ID WHERE j2.JOB_ID=j.ID AND h2.NAME IN ('Lateral Associate','Lateral Counsel','Staff Attorney'))
  AND NOT EXISTS (SELECT 1 FROM JOB_HIRING_TYPE j3 JOIN HIRING_TYPE h3 ON h3.ID=j3.HIRING_TYPE_ID WHERE j3.JOB_ID=j.ID AND h3.NAME='Lateral Partner')"""


def _market_sql(cond):
    return f"""SELECT loc.OPTION AS city, {_WIN_CASE}
FROM JOB j JOIN ORG o ON o.ID=j.ORG_ID
JOIN JOB_OFFICE jo ON jo.JOB_ID=j.ID JOIN ORG_OFFICE ofc ON ofc.ID=jo.OFFICE_ID
JOIN STATIC_LIST_OPTION loc ON loc.ID=ofc.OFFICE_LOCATION_ID
WHERE {cond} GROUP BY loc.OPTION HAVING w12 > 0"""


def _grad_sql(cond):
    return f"""SELECT YEAR(r.MIN_GRAD_DATE) AS gy, {_WIN_CASE}
FROM JOB j JOIN ORG o ON o.ID=j.ORG_ID
JOIN FORWARD_JOB_GRAD_DATE_TARGET_RULE r ON r.JOB_ID=j.ID AND r.IS_NOT_DELETED=1 AND r.RULE_TYPE='INDIVIDUAL_YEARS'
WHERE {cond} AND YEAR(r.MIN_GRAD_DATE) BETWEEN 2011 AND 2026 GROUP BY gy"""


def _windows(rows, labelkey, as_int=False, by_label=False):
    def lab(r):
        return int(r[labelkey]) if as_int else str(r[labelkey])

    def ok(r):
        return as_int or str(r[labelkey]).strip() not in ("--", "")

    def arr(k):
        a = [[lab(r), int(r[k])] for r in rows if int(r[k]) > 0 and ok(r)]
        a.sort(key=(lambda x: x[0]) if by_label else (lambda x: -x[1]))
        return a
    return {"open": arr("o"), "3mo": arr("w3"), "12mo": arr("w12")}


# Practice-area classifier (title -> master-taxonomy group). Fresh keyword heuristic
# (practice is NOT a stored field). Ordered: substantive area first, general litigation
# last (so "Patent Litigation"->IP, "Real Estate Litigation"->Real Estate, but bare
# "Commercial Litigation"->Dispute Resolution). Unmatched -> 'Other / General' (excluded).
_PRACTICE_RULES = [
    ("Bankruptcy/Restructuring", r"bankruptc|restructur|insolvenc|workout|chapter 11|distressed"),
    ("Antitrust", r"antitrust|\bcompetition\b|cartel"),
    ("Tax", r"\btax\b|taxation"),
    ("Capital Markets", r"capital markets|securit(ies|ization)|high.?yield|\becm\b|\bdcm\b|public offering|\bipo\b"),
    ("Private Equity", r"private equity|\bpe\b|buyout"),
    ("Banking & Finance", r"banking|leveraged finance|acquisition finance|project finance|structured finance|\bfinance\b|lending|\bcredit\b"),
    ("Funds", r"fund formation|investment management|hedge fund|asset management|\bfunds\b"),
    ("Real Estate", r"real estate|\breit\b|land use|leasing|zoning"),
    ("Labor & Employment", r"\blabor\b|employment|\berisa\b|employee benefit|executive compensation|\bwage\b|labour"),
    ("Intellectual Property", r"intellectual property|\bip\b|patent|trademark|copyright|trade secret"),
    ("Privacy & Data Security", r"privacy|data security|data protection|\bcyber|information security"),
    ("Technology", r"technolog|software|\bsaas\b|artificial intelligence|\bai\b|blockchain|\bcrypto"),
    ("Healthcare", r"health\s?care|life science|pharmaceutic|\bfda\b|\bmedical\b|biotech"),
    ("Energy & Projects", r"\benergy\b|oil\s?(&|and)?\s?gas|\bpower\b|renewable|utilit|infrastructure|\blng\b"),
    ("Environment", r"environment|climate|\besg\b|natural resource"),
    ("Insurance", r"insurance|reinsurance"),
    ("Media & Entertainment", r"\bmedia\b|entertainment|\bfilm\b|\bmusic\b|advertising|\bsports\b"),
    ("White Collar", r"white collar|\bfcpa\b|enforcement|government investigation|internal investigation"),
    ("Trusts & Estates", r"\btrust|estate planning|private client|private wealth|fiduciary|\bwealth\b"),
    ("Financial Services", r"fintech|financial services|\bpayments\b|consumer financial|broker.?dealer"),
    ("Government, Administrative & Public Law", r"\bgovernment\b|regulatory|public law|administrative law|political law|lobbying"),
    ("Construction", r"construction"),
    ("Transportation", r"transportation|aviation|maritime|shipping|\brail\b"),
    ("Family Law", r"family law|matrimonial|divorce"),
    ("Trade & Commodities", r"international trade|commodit|customs|\bexport\b|sanctions|\bcfius\b"),
    ("Corporate/M&A", r"corporate|\bm&a\b|m\s?&\s?a\b|\bmerger|acquisition|transactional|emerging compan|startup|venture capital"),
    ("Dispute Resolution", r"litigation|\btrial\b|\bdispute|appellate|arbitration|\blitigator\b|class action|controvers"),
]
_PR = [(lbl, re.compile(pat)) for lbl, pat in _PRACTICE_RULES]


def _practice(title):
    t = (title or "").lower()
    for lbl, rx in _PR:
        if rx.search(t):
            return lbl
    return "Other / General"


def _practice_windows(cond):
    rows = metabase_sql(MB_DB, f"""
SELECT j.TITLE AS title,
  (j.FORWARD_PUBLISHING_STATUS='PUBLISHED') AS o,
  (j.FORWARD_PUBLISHING_STATUS='PUBLISHED' OR j.OPEN_DATE>=DATE_SUB(NOW(),INTERVAL 3 MONTH)) AS w3,
  (j.FORWARD_PUBLISHING_STATUS='PUBLISHED' OR j.OPEN_DATE>=DATE_SUB(NOW(),INTERVAL 12 MONTH)) AS w12
FROM JOB j JOIN ORG o ON o.ID=j.ORG_ID WHERE {cond}""")
    agg = {"o": {}, "w3": {}, "w12": {}}
    for r in rows:
        cat = _practice(r.get("title"))
        if cat == "Other / General":
            continue
        for k in ("o", "w3", "w12"):
            if int(r[k] or 0):
                agg[k][cat] = agg[k].get(cat, 0) + 1

    def arr(k):
        a = [[c, n] for c, n in agg[k].items()]
        a.sort(key=lambda x: -x[1])
        return a
    return {"open": arr("o"), "3mo": arr("w3"), "12mo": arr("w12")}


# Candidate-source funnel (Q10231 base + our funnel/fold/demo layer). Warehouse db 67.
# Smart status classification: "reached offer" excludes "no offer"/"before offer";
# "reached interview" excludes "no interview"/"not interviewed"/"before interview"/
# "no screen/interview" (so "Rejected AFTER Interview" counts, "No Interview" doesn't).
_OFFER_COND = ("((LOWER(job_app_status) LIKE '%offer%' AND LOWER(job_app_status) NOT LIKE '%no offer%' "
               "AND LOWER(job_app_status) NOT LIKE '%before offer%') OR LOWER(job_app_status) LIKE '%hired%')")
_INTERVIEW_COND = (f"({_OFFER_COND} "
                   "OR (LOWER(job_app_status) LIKE '%interview%' AND LOWER(job_app_status) NOT LIKE '%no interview%' "
                   "AND LOWER(job_app_status) NOT LIKE '%not interview%' AND LOWER(job_app_status) NOT LIKE '%before interview%' "
                   "AND LOWER(job_app_status) NOT LIKE '%no screen/interview%') "
                   "OR LOWER(job_app_status) LIKE '%callback%' "
                   "OR (LOWER(job_app_status) LIKE '%screening%' AND LOWER(job_app_status) NOT LIKE '%no screening%') "
                   "OR LOWER(job_app_status) LIKE '%full round%' OR LOWER(job_app_status) LIKE '%round interview%')")
_SRC_FOLD = ("""CASE WHEN source='Write-in' THEN 'Write-in' WHEN source='Agency' THEN 'Agency'
  WHEN source IN ('Referral','Employee Referral') THEN 'Referral'
  WHEN source='Direct Outreach' THEN 'Direct Outreach'
  WHEN source='Advertisement/Job Board' THEN 'Advertisement/Job Board'
  WHEN source='None' THEN 'None' ELSE 'Other' END""")
SRC_DEMO = ("4,48,55,84,93,189,190,238,251,323,324,346,357,409,451,452,464,477,482,484,486,520,522,523,"
            "525,526,538,543,549,550,569,585,586,594,669,673,675,679,682,684,685,699,764,767,790,798,828,"
            "834,840,891,982,1003,1104,1268,1270,1276,1280,1338,1381,1387,1388,1391,1396,1411,1443,1464,"
            "1476,1503,1506,1512,1517,1541,1607,1649,1659,1699,1734,1825,1885,1948,1949,1967,1970,1979,"
            "1991,2074,2098,2106,2188,2196,2224,2247,2256,2259,2319,2330,2353,2370,2405,2406,2561,2580,"
            "2582,2586,2590,2593,2597,2630,2643,2664,2665,2673,2678,2679,2686,2694,2700,2717,2727,2737,2738")


def _source_funnel(jobtypes):
    jt = ",".join(f"'{t}'" for t in jobtypes)
    rows = metabase_sql(67, f"""
SELECT {_SRC_FOLD} AS cat, COUNT(DISTINCT candidate_id) AS applied,
  COUNT(DISTINCT CASE WHEN {_INTERVIEW_COND} THEN candidate_id END) AS interview,
  COUNT(DISTINCT CASE WHEN {_OFFER_COND} THEN candidate_id END) AS offer
FROM flocustomer.job_applications
WHERE is_deleted IS FALSE AND job_type IN ({jt}) AND date_applied >= '2025-01-01'
  AND org_id NOT IN ({SRC_DEMO}) GROUP BY cat""")
    return {r["cat"]: {"applied": int(r["applied"]), "interview": int(r["interview"]), "offer": int(r["offer"])} for r in rows}


def _apply_source(existing, funnel):
    for e in existing:
        if e.get("label") in funnel:
            e["v"] = funnel[e["label"]]
    return existing


def wire_lateral_charts(data: dict) -> None:
    tl = metabase_sql(MB_DB, f"""
SELECT YEAR(j.OPEN_DATE) AS yr, MONTH(j.OPEN_DATE) AS mo, COUNT(DISTINCT j.ID) AS n
{LATERAL_BASE} AND YEAR(j.OPEN_DATE) IN (2025, 2026)
GROUP BY yr, mo""")
    ch = data["charts"]["lateral"]
    ch["timeline"] = {"2025": monthly12(tl, 2025), "2026": monthly12(tl, 2026)}
    ch["totalByWindow"] = _job_window_totals(LATERAL_BASE)
    ch["marketByWindow"] = _windows(metabase_sql(MB_DB, _market_sql(LAT_COND)), "city")
    ch["gradByWindow"] = _windows(metabase_sql(MB_DB, _grad_sql(LAT_COND)), "gy", as_int=True, by_label=True)
    ch["practiceByWindow"] = _practice_windows(LAT_COND)
    ch["source"] = _apply_source(ch["source"], _source_funnel(("Lateral Associate", "Lateral Counsel", "Staff Attorney")))
    print(f"  lateral charts: timeline + totals + market + grad + practice + source")


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

# Breakdown conditions for 3L (grad-target 2027 + noise) and partner (tag-only, trailing
# 12mo per memory). PARTNER breakdowns are single arrays (not windowed).
THREEL_COND = f"""j.DELETED_AT IS NULL AND (j.JOB_TYPE IN ('ATS','MANUAL_ENTRY') OR j.JOB_TYPE IS NULL)
  AND j.JOB_CLASSIFICATION='LAW_FIRM' AND LOWER(o.NAME) NOT REGEXP '{DEMO_REGEXP}'
  AND EXISTS (SELECT 1 FROM FORWARD_JOB_GRAD_DATE_TARGET_RULE r2 WHERE r2.JOB_ID=j.ID
              AND r2.IS_NOT_DELETED=1 AND r2.RULE_TYPE='INDIVIDUAL_YEARS' AND YEAR(r2.MIN_GRAD_DATE)=2027)
  AND LOWER(j.TITLE) NOT REGEXP '{THREEL_NOISE}'"""
PARTNER_TAG_COND = f"""j.DELETED_AT IS NULL AND j.JOB_CLASSIFICATION='LAW_FIRM'
  AND LOWER(o.NAME) NOT REGEXP '{DEMO_REGEXP}'
  AND EXISTS (SELECT 1 FROM JOB_HIRING_TYPE j2 JOIN HIRING_TYPE h2 ON h2.ID=j2.HIRING_TYPE_ID
              WHERE j2.JOB_ID=j.ID AND h2.NAME='Lateral Partner')"""


def _market_single(cond):
    """Single [[city,count]] array (trailing 12mo), for partner (non-windowed breakdowns)."""
    rows = metabase_sql(MB_DB, f"""
SELECT loc.OPTION AS city, COUNT(DISTINCT j.ID) AS n
FROM JOB j JOIN ORG o ON o.ID=j.ORG_ID
JOIN JOB_OFFICE jo ON jo.JOB_ID=j.ID JOIN ORG_OFFICE ofc ON ofc.ID=jo.OFFICE_ID
JOIN STATIC_LIST_OPTION loc ON loc.ID=ofc.OFFICE_LOCATION_ID
WHERE {cond} AND (j.FORWARD_PUBLISHING_STATUS='PUBLISHED' OR j.OPEN_DATE>=DATE_SUB(NOW(),INTERVAL 12 MONTH))
GROUP BY loc.OPTION HAVING n>0 ORDER BY n DESC""")
    return [[str(r["city"]), int(r["n"])] for r in rows if str(r["city"]).strip() not in ("--", "")]


def wire_partner_charts(data: dict) -> None:
    tl = metabase_sql(MB_DB, f"""
SELECT YEAR(j.OPEN_DATE) AS yr, MONTH(j.OPEN_DATE) AS mo, COUNT(DISTINCT j.ID) AS n
{PARTNER_WHERE} AND YEAR(j.OPEN_DATE) IN (2025, 2026)
GROUP BY yr, mo""")
    data["charts"]["partner"]["timeline"] = {"2025": monthly12(tl, 2025), "2026": monthly12(tl, 2026)}
    data["charts"]["partner"]["market"] = _market_single(PARTNER_TAG_COND)
    data["charts"]["partner"]["practice"] = _practice_windows(PARTNER_TAG_COND)["12mo"]
    data["charts"]["partner"]["source"] = _apply_source(data["charts"]["partner"]["source"], _source_funnel(("Lateral Partner",)))
    print(f"  partner charts: timeline + market + practice + source")


def wire_threeL_charts(data: dict) -> None:
    rows = metabase_sql(MB_DB, """
SELECT r.gy AS gyear, YEAR(j.OPEN_DATE) AS yr, MONTH(j.OPEN_DATE) AS mo, COUNT(DISTINCT j.ID) AS n
FROM JOB j JOIN ORG o ON o.ID = j.ORG_ID
JOIN (SELECT DISTINCT JOB_ID, YEAR(MIN_GRAD_DATE) AS gy FROM FORWARD_JOB_GRAD_DATE_TARGET_RULE
      WHERE IS_NOT_DELETED = 1 AND RULE_TYPE = 'INDIVIDUAL_YEARS') r ON r.JOB_ID = j.ID AND r.gy IN (2026, 2027)
WHERE j.DELETED_AT IS NULL
  AND (j.JOB_TYPE IN ('ATS','MANUAL_ENTRY') OR j.JOB_TYPE IS NULL) AND j.JOB_CLASSIFICATION = 'LAW_FIRM'
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
    data["charts"]["threeL"]["marketByWindow"] = _windows(metabase_sql(MB_DB, _market_sql(THREEL_COND)), "city")
    data["charts"]["threeL"]["practiceByWindow"] = _practice_windows(THREEL_COND)
    print(f"  3L charts: timeline + market + practice")


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


# lawStudent.postings: law-student job postings by OPEN_DATE month, school-year (Jul-Jun)
# cycles. Law-student = Law Student tag OR IS_1L/IS_2L flag OR summer-ish title, minus the
# lateral/partner/paralegal/staff/3L guard; ATS+MANUAL_ENTRY; all non-deleted (volume).
LAWSTUDENT_JOB_WHERE = """
FROM JOB j JOIN ORG o ON o.ID = j.ORG_ID
WHERE j.DELETED_AT IS NULL
  AND (j.JOB_TYPE IN ('ATS','MANUAL_ENTRY') OR j.JOB_TYPE IS NULL) AND j.JOB_CLASSIFICATION = 'LAW_FIRM'
  AND LOWER(o.NAME) NOT REGEXP '%s'
  AND (EXISTS (SELECT 1 FROM JOB_HIRING_TYPE jh JOIN HIRING_TYPE h ON h.ID=jh.HIRING_TYPE_ID WHERE jh.JOB_ID=j.ID AND h.NAME='Law Student')
       OR j.IS_1L=1 OR j.IS_2L=1
       OR LOWER(j.TITLE) REGEXP 'summer associate|summer program|\\\\b1l\\\\b|\\\\b2l\\\\b|summer law|summer clerk|summer intern|summer fellow')
  AND LOWER(j.TITLE) NOT REGEXP 'lateral|partner|paralegal|staff attorney|\\\\b3l\\\\b'""" % DEMO_REGEXP


# appsubs = Metabase Q2509 "Forward Application Submissions" (native SQL extracted from
# the saved question): JOB_APP (ATS, APP_SOURCE='FORWARD') + EXTERNAL_JOB_APP, by created
# month. Reconstruction reproduced the snapshot EXACTLY.
APPSUBS_SQL = """
WITH subs AS (
  SELECT DATE_FORMAT(ja.created_at,'%Y-%m') m, COUNT(*) n
  FROM JOB_APP ja JOIN JOB j ON ja.job_id=j.id
  WHERE j.job_type='ATS' AND ja.APP_SOURCE='FORWARD' GROUP BY m
  UNION ALL
  SELECT DATE_FORMAT(ja.created_at,'%Y-%m') m, COUNT(*) n
  FROM EXTERNAL_JOB_APP ja JOIN JOB j ON ja.job_id=j.id GROUP BY m
)
SELECT m, SUM(n) n FROM subs WHERE m >= '2022-07' GROUP BY m ORDER BY m"""


# net_all = Metabase Q2445 "Law School Networking Events": EVENTS VIRTUAL IN (3,7,10)
# ("University Events" types), demo org-id blocklist from the question. Reproduces snapshot
# exactly. (The big candidate-law-school CTE in Q2445 is only for the unused T15 toggle.)
NET_DEMO_ORGS = ("4,32,189,190,982,525,569,346,357,84,61,69,78,94,251,451,452,463,464,471,"
                 "477,483,484,486,538,543,549,551,585,586,589,673,675,682,683,684,699,727,"
                 "767,790,828,1003,1007,1135,1270,1280,1381,1396,1476,1503")
NET_SQL = f"""
SELECT YEAR(e.DATE) AS yr, MONTH(e.DATE) AS mo, COUNT(*) AS n
FROM EVENTS e JOIN ORG o ON o.ID = e.OID
WHERE e.VIRTUAL IN (3,7,10) AND o.ID NOT IN ({NET_DEMO_ORGS}) AND e.DATE >= '2022-07-01'
GROUP BY yr, mo"""


# ls_all = Metabase Q1123 "Law School Interview Volume": EVENTUSERTIMESLOTS (VIRTUAL IN
# (5,9,11,13), org UNIVERSITY=1, demo org-id list). NOTE: NO event-name keyword filter
# (that's the firm-side Q7459 only). Reproduces snapshot exactly.
LS_SQL = f"""
SELECT YEAR(ts.DATE) AS yr, MONTH(ts.DATE) AS mo, COUNT(*) AS n
FROM EVENTUSERTIMESLOTS ts
JOIN EVENTUSERSCHEDULE eus ON eus.ID = ts.EUSID
JOIN EVENTS e ON e.ID = eus.EID
JOIN ORG o ON o.ID = e.OID
WHERE ts.DELETEDAT IS NULL AND e.VIRTUAL IN (5,9,11,13) AND o.UNIVERSITY = 1
  AND o.ID NOT IN ({NET_DEMO_ORGS}) AND ts.DATE >= '2022-07-01'
GROUP BY yr, mo"""

# accounts = Metabase Q6436 "Account Creation - Cumulated": cumulative distinct active
# candidates by grad class (grad year from QQ 'Graduation date' or education END_DATE),
# REQUIRING a resolvable law school (QQ 'Law school' or education law school), by
# ACTIVE_SINCE month. Each class over its Jul(Y-3)-Jun(Y-2) recruiting year. Validated.
ACCOUNTS_SQL = """
WITH cand AS (
  SELECT DISTINCT RECRUITS.CANID cid,
    CASE WHEN QQANSWERS.ANSWER LIKE '%2026%' THEN 2026 WHEN QQANSWERS.ANSWER LIKE '%2027%' THEN 2027
         WHEN QQANSWERS.ANSWER LIKE '%2028%' THEN 2028 WHEN QQANSWERS.ANSWER LIKE '%2029%' THEN 2029 END gy
  FROM QQANSWERS JOIN QQS ON QQS.ID=QQANSWERS.QID AND QQS.`LOCKED`=2 AND QQS.QUESTION='Graduation date'
  JOIN RECRUITS ON QQANSWERS.RID=RECRUITS.ID
  JOIN CANDIDATE_ACCOUNT ca ON ca.CANDIDATE_ID=RECRUITS.CANID AND ca.IS_ACTIVE=1 AND ca.DELETED_AT IS NULL
  WHERE QQANSWERS.ANSWER LIKE '%2026%' OR QQANSWERS.ANSWER LIKE '%2027%'
     OR QQANSWERS.ANSWER LIKE '%2028%' OR QQANSWERS.ANSWER LIKE '%2029%'
  UNION
  SELECT DISTINCT eh.candidate_id, YEAR(eh.END_DATE)
  FROM CANDIDATE_EDUCATION_HISTORY_ENTRY eh
  WHERE eh.DELETED_AT IS NULL AND YEAR(eh.END_DATE) IN (2026,2027,2028,2029)
),
has_ls AS (
  SELECT DISTINCT RECRUITS.CANID cid FROM QQANSWERS JOIN QQS ON QQS.ID=QQANSWERS.QID
    AND QQS.`LOCKED`=2 AND QQS.QUESTION='Law school' JOIN RECRUITS ON QQANSWERS.RID=RECRUITS.ID
  UNION
  SELECT DISTINCT eh.candidate_id FROM CANDIDATE_EDUCATION_HISTORY_ENTRY eh
    JOIN LAW_SCHOOL ls ON ls.ID=eh.SCHOOL_ID AND ls.SCHOOL_TYPE='LAW_SCHOOL' WHERE eh.DELETED_AT IS NULL
),
monthly AS (
  SELECT c.gy gy, DATE_FORMAT(ca.ACTIVE_SINCE,'%Y-%m') period, COUNT(DISTINCT c.cid) cnt
  FROM cand c JOIN has_ls h ON h.cid=c.cid
  JOIN CANDIDATE_ACCOUNT ca ON ca.CANDIDATE_ID=c.cid AND ca.IS_ACTIVE=1 AND ca.DELETED_AT IS NULL
  WHERE c.gy IS NOT NULL GROUP BY c.gy, period
),
cum AS (SELECT gy, period, SUM(cnt) OVER (PARTITION BY gy ORDER BY period) cumc FROM monthly)
SELECT gy, period, cumc FROM cum
WHERE (gy=2026 AND period>='2023-07' AND period<'2024-07')
   OR (gy=2027 AND period>='2024-07' AND period<'2025-07')
   OR (gy=2028 AND period>='2025-07' AND period<'2026-07')
   OR (gy=2029 AND period>='2026-07' AND period<'2027-07')
ORDER BY gy, period"""


def _cumulative_jul(per: dict, start_year: int) -> list:
    """12-elem Jul..Jun cumulative array; forward-fills flat months, nulls strictly-future."""
    out, last = [], None
    for i in range(12):
        mo = (6 + i) % 12 + 1
        yr = start_year + (0 if mo >= 7 else 1)
        key = f"{yr:04d}-{mo:02d}"
        if key in per:
            last = per[key]
        future = yr > TODAY.year or (yr == TODAY.year and mo > TODAY.month)
        out.append(None if future else last)
    return out


def _by_ym(rows, mkey="m", nkey="n"):
    out = {}
    for r in rows:
        y, mo = str(r[mkey]).split("-")[:2]
        out[(int(y), int(mo))] = int(r[nkey])
    return out


# outreach (Q2444) + lf interview (Q7459) with the <500/500+ attorney-headcount split.
# The split is NOT in the questions — layered on via firm headcount. 500+ set = live
# pendo.accounts.attorney_headcount>=500 (71 firms, warehouse db 67) + name-matched BigLaw
# hosts whose pendo headcount is blank (Jones Day/Katten/Ballard/etc.); unknown -> <500.
# STOPGAP: refresh the 500+ list periodically (pendo headcount backfill). outreach =
# EVENTS VIRTUAL IN (0,1,2) (Q2444's real def; the snapshot used a wrong 0,1,2,4,8 guess).
# lf = firm interview timeslots VIRTUAL IN (5,9,11,13) UNIVERSITY=0 WITH the keyword filter.
HC_500PLUS = ("13,17,191,192,195,197,199,201,202,203,207,209,210,211,215,216,22,228,229,230,"
              "232,233,234,237,240,241,258,272,273,277,278,28,280,284,304,310,313,325,33,335,"
              "34,343,35,356,36,375,38,381,447,476,481,489,498,546,548,56,564,57,577,579,58,59,"
              "605,63,632,67,732,736,751,772,92,"
              "127,2579,16,288,276,591,2090,2232,130,279,1974,1983,2046,2647,2726")
OUTREACH_SQL = f"""
SELECT YEAR(e.DATE) AS yr, MONTH(e.DATE) AS mo,
  SUM(CASE WHEN o.ID IN ({HC_500PLUS}) THEN 1 ELSE 0 END) AS p500,
  SUM(CASE WHEN o.ID NOT IN ({HC_500PLUS}) THEN 1 ELSE 0 END) AS u500
FROM EVENTS e JOIN ORG o ON o.ID = e.OID
WHERE e.VIRTUAL IN (0,1,2) AND o.ID NOT IN ({NET_DEMO_ORGS}) AND e.DATE >= '2022-07-01'
GROUP BY yr, mo"""
LF_SQL = f"""
SELECT YEAR(ts.DATE) AS yr, MONTH(ts.DATE) AS mo,
  SUM(CASE WHEN o.ID IN ({HC_500PLUS}) THEN 1 ELSE 0 END) AS p500,
  SUM(CASE WHEN o.ID NOT IN ({HC_500PLUS}) THEN 1 ELSE 0 END) AS u500
FROM EVENTUSERTIMESLOTS ts
JOIN EVENTUSERSCHEDULE eus ON eus.ID = ts.EUSID
JOIN EVENTS e ON e.ID = eus.EID JOIN ORG o ON o.ID = e.OID
WHERE ts.DELETEDAT IS NULL AND e.VIRTUAL IN (5,9,11,13) AND o.UNIVERSITY = 0
  AND o.ID NOT IN ({NET_DEMO_ORGS})
  AND LOWER(e.NAME) REGEXP '1l|2l|summer|student|callback|flyback|scholar|fellow|diversity'
  AND ts.DATE >= '2022-07-01'
GROUP BY yr, mo"""


def _split_cycles(rows, key):
    by = {(int(r["yr"]), int(r["mo"])): int(r[key]) for r in rows}
    return {f"{cy}-{cy+1}": cycle_series(by, cy, 7) for cy in range(2022, 2027)}


def wire_lawstudent_charts(data: dict) -> None:
    ls = data["charts"]["lawStudent"]
    # postings (rebuilt from Q6271 intent — law-student volume by open month)
    pr = metabase_sql(MB_DB, f"""
SELECT YEAR(j.OPEN_DATE) AS yr, MONTH(j.OPEN_DATE) AS mo, COUNT(DISTINCT j.ID) AS n
{LAWSTUDENT_JOB_WHERE} AND j.OPEN_DATE >= '2022-07-01'
GROUP BY yr, mo""")
    by = {(int(r["yr"]), int(r["mo"])): int(r["n"]) for r in pr}
    ls["postings"] = {f"{cy}-{cy+1}": cycle_series(by, cy, 7) for cy in range(2022, 2027)}
    # appsubs (Q2509, exact SQL) — cohorts 2023-24 .. 2026-27
    aby = _by_ym(metabase_sql(MB_DB, APPSUBS_SQL))
    ls["appsubs"] = {f"{cy}-{cy+1}": cycle_series(aby, cy, 7) for cy in range(2023, 2027)}
    # net_all (Q2445) — university-event networking, Jul-Jun cycles
    nby = {(int(r["yr"]), int(r["mo"])): int(r["n"]) for r in metabase_sql(MB_DB, NET_SQL)}
    ls["net_all"] = {f"{cy}-{cy+1}": cycle_series(nby, cy, 7) for cy in range(2022, 2027)}
    # ls_all (Q1123) — law-school interview volume, Jul-Jun cycles
    lby = {(int(r["yr"]), int(r["mo"])): int(r["n"]) for r in metabase_sql(MB_DB, LS_SQL)}
    ls["ls_all"] = {f"{cy}-{cy+1}": cycle_series(lby, cy, 7) for cy in range(2022, 2027)}
    # accounts (Q6436) — cumulative account activations by grad Class
    acc = {}
    for r in metabase_sql(MB_DB, ACCOUNTS_SQL):
        acc.setdefault(int(r["gy"]), {})[str(r["period"])[:7]] = int(r["cumc"])
    ls["accounts"] = {f"Class of {Y}": _cumulative_jul(acc.get(Y, {}), Y - 3) for Y in (2026, 2027, 2028, 2029)}
    # outreach + lf interview volume, <500/500+ headcount split
    oro = metabase_sql(MB_DB, OUTREACH_SQL)
    ls["outreach_500plus"], ls["outreach_u500"] = _split_cycles(oro, "p500"), _split_cycles(oro, "u500")
    lfo = metabase_sql(MB_DB, LF_SQL)
    ls["lf_500plus"], ls["lf_u500"] = _split_cycles(lfo, "p500"), _split_cycles(lfo, "u500")
    print(f"  lawStudent charts: postings + appsubs + net_all + ls_all + accounts + outreach + lf")


# ── OVERVIEW STAT TILES (runs last — derives from already-wired DATA.tables + a few flow
# queries). 1L-2L card = combined 1L(grad 2029)+2L(grad 2028), "opened" by OPEN_DATE with
# YoY deltas (same-day window). Categorical lateral tiles stay on snapshot (from breakdowns).
# Current-window counts (m_cur/s_cur) mirror the visible table exactly: published and
# not-yet-closed. The prior-year baselines (m_prev/s_prev) are historical flow — those
# jobs are all long closed, so a "still open" filter would zero them out.
LAWFIRM_STATS_SQL = ("""
SELECT
  SUM(j.OPEN_DATE >= DATE_FORMAT(NOW(),'%%Y-%%m-01')
      AND (j.CLOSE_DATE IS NULL OR j.CLOSE_DATE >= CURDATE())) AS m_cur,
  SUM(j.OPEN_DATE >= DATE_FORMAT(DATE_SUB(NOW(),INTERVAL 1 YEAR),'%%Y-%%m-01')
      AND j.OPEN_DATE <= DATE_SUB(NOW(),INTERVAL 1 YEAR)) AS m_prev,
  SUM(j.OPEN_DATE >= '2026-06-01'
      AND (j.CLOSE_DATE IS NULL OR j.CLOSE_DATE >= CURDATE())) AS s_cur,
  SUM(j.OPEN_DATE >= '2025-06-01' AND j.OPEN_DATE <= DATE_SUB(NOW(),INTERVAL 1 YEAR)) AS s_prev
FROM JOB j JOIN ORG o ON o.ID = j.ORG_ID
WHERE j.DELETED_AT IS NULL AND j.FORWARD_PUBLISHING_STATUS = 'PUBLISHED'
  AND (j.JOB_TYPE IN ('ATS','MANUAL_ENTRY') OR j.JOB_TYPE IS NULL)
  AND j.JOB_CLASSIFICATION='LAW_FIRM' AND LOWER(o.NAME) NOT REGEXP '%s'
  AND (EXISTS (SELECT 1 FROM JOB_HIRING_TYPE jh JOIN HIRING_TYPE h ON h.ID=jh.HIRING_TYPE_ID WHERE jh.JOB_ID=j.ID AND h.NAME='Law Student')
       OR LOWER(j.TITLE) REGEXP 'summer associate|summer program|\\\\b1l\\\\b|\\\\b2l\\\\b|summer law|summer clerk|summer intern|summer fellow|summer scholar')
  AND LOWER(j.TITLE) NOT REGEXP 'lateral|partner|paralegal|staff attorney|\\\\b3l\\\\b'
  AND EXISTS (SELECT 1 FROM FORWARD_JOB_GRAD_DATE_TARGET_RULE r WHERE r.JOB_ID=j.ID
              AND r.IS_NOT_DELETED=1 AND r.RULE_TYPE='INDIVIDUAL_YEARS' AND YEAR(r.MIN_GRAD_DATE) IN (2028,2029))
""" % DEMO_REGEXP)

PARTNER_12MO_SQL = f"""
SELECT COUNT(DISTINCT j.ID) AS n
FROM JOB j JOIN ORG o ON o.ID = j.ORG_ID
WHERE j.DELETED_AT IS NULL AND (j.JOB_TYPE IN ('ATS','MANUAL_ENTRY') OR j.JOB_TYPE IS NULL)
  AND j.JOB_CLASSIFICATION='LAW_FIRM' AND LOWER(o.NAME) NOT REGEXP '{DEMO_REGEXP}'
  AND EXISTS (SELECT 1 FROM JOB_HIRING_TYPE j2 JOIN HIRING_TYPE h2 ON h2.ID=j2.HIRING_TYPE_ID
              WHERE j2.JOB_ID=j.ID AND h2.NAME='Lateral Partner')
  AND j.OPEN_DATE >= DATE_SUB(NOW(), INTERVAL 12 MONTH)"""

RECEPTIONS_SQL = f"""
SELECT COUNT(DISTINCT e.ID) AS n
FROM EVENTS e JOIN ORG o ON o.ID = e.OID
WHERE LOWER(e.NAME) REGEXP 'clerk' AND LOWER(e.NAME) REGEXP 'reception'
  AND LOWER(e.NAME) NOT REGEXP 'interview|mock|test|1l|diversity|summer'
  AND o.UNIVERSITY = 0 AND LOWER(o.NAME) NOT REGEXP '{DEMO_REGEXP}' AND e.DATE > CURDATE()"""


def _parse_mdy(s):
    try:
        return datetime.datetime.strptime(str(s).strip(), "%b %d, %Y").date()
    except (ValueError, TypeError):
        return None


def _opened_this_month(recs, key="Application Open Date"):
    return sum(1 for r in recs if (d := _parse_mdy(r.get(key))) and (d.year, d.month) == (TODAY.year, TODAY.month))


def wire_overview_stats(data: dict) -> None:
    t, ov = data["tables"], data["overview"]

    def pi(open_key, third_kind):
        recs = t.get(open_key, [])
        n = len(recs)
        if third_kind == "paid":
            paid = sum(1 for r in recs if str(r.get("Compensation", "")).strip() not in ("", "—"))
            third = {"label": "Paid", "value": f"{round(100 * paid / n)}%" if n else "0%"}
        else:
            third = {"label": "Government", "value": str(sum(1 for r in recs if r.get("Government") is True))}
        return [{"label": "Listed", "value": str(n)},
                {"label": "Opened this month", "value": str(_opened_this_month(recs))}, third]

    ov["piCardStats"] = {"summer": pi("piSummerOpen", "paid"), "extern": pi("piExternOpen", "gov"),
                         "attorney": pi("piAttorneyOpen", "gov")}
    for sub, k in (("pisummer", "summer"), ("piextern", "extern"), ("piattorney", "attorney")):
        ov["headerStats"][sub] = [{**s, "delta": "", "hasDelta": False} for s in ov["piCardStats"][k]]

    ov["headerStats"]["entrylevel3l"] = [{"label": "Currently open", "value": str(len(t.get("entry3l", []))),
                                          "delta": "", "hasDelta": False}]

    npc = len(t.get("pc", []))
    recept = int(metabase_sql(MB_DB, RECEPTIONS_SQL)[0]["n"])
    ov["headerStats"]["judicial"] = [{"label": "Open now", "value": str(npc), "delta": "", "hasDelta": False},
                                     {"label": "Upcoming receptions", "value": str(recept), "delta": "", "hasDelta": False}]
    ov["pcStats"] = [{"label": "Open now", "value": str(npc)}, {"label": "Upcoming opens", "value": "0"},
                     {"label": "Upcoming receptions", "value": str(recept)}]

    p12 = int(metabase_sql(MB_DB, PARTNER_12MO_SQL)[0]["n"])
    ov["headerStats"]["lateralpartner"] = [{"label": "Opened past 12 mo", "value": str(p12), "delta": "", "hasDelta": False}]

    lf = metabase_sql(MB_DB, LAWFIRM_STATS_SQL)[0]
    # current-window counts come from the table-derived flow (exact match to the visible
    # table); the SQL supplies only the prior-year baselines for the YoY comparison.
    flow = ov.pop("_lawfirmFlow", None) or {"m_cur": int(lf["m_cur"]), "s_cur": int(lf["s_cur"])}

    def dlt(cur, prev):
        # suppress the YoY % when the prior-year baseline is too small to be meaningful
        # (early-cycle same-window counts of 1-2 produce absurd percentages)
        return (f"{round((cur - prev) / prev * 100)}%", True) if prev >= 5 else ("", False)
    mc, mp = int(flow["m_cur"]), int(lf["m_prev"])
    sc, sp = int(flow["s_cur"]), int(lf["s_prev"])
    md, mh = dlt(mc, mp)
    sd, sh = dlt(sc, sp)
    ov["headerStats"]["lawfirm"] = [{"label": "Opened this month", "value": str(mc), "delta": md, "hasDelta": mh},
                                    {"label": "Opened this season", "value": str(sc), "delta": sd, "hasDelta": sh}]
    ov["cards"]["lawfirm"]["stats"] = [
        {"value": str(mc), "delta": md, "vs": f"vs. {mp} this time last year"},
        {"value": str(sc), "delta": sd, "vs": f"vs. {sp} by this date last year"}]

    total = (len(t.get("lateral", [])) + npc + len(t.get("entry3l", []))
             + len(t.get("summer1L", {}).get("open", [])) + len(t.get("summer2L", {}).get("open", []))
             + sum(len(t.get(k, [])) for k in ("piSummerOpen", "piExternOpen", "piAttorneyOpen"))
             + len(t.get("campus", [])))
    ov["statStrip"][1]["value"] = f"{total // 10 * 10}+"
    ups = []
    for lv in ("summer1L", "summer2L"):
        for r in t.get(lv, {}).get("upcoming", []):
            v = next((r[c] for c in r if "Application Open Date" in c), "")
            try:
                ups.append(datetime.datetime.strptime(str(v).replace("Opens ", "").strip(), "%m/%d/%Y").date())
            except ValueError:
                pass
    if ups:
        ov["statStrip"][2]["value"] = min(ups).strftime("%b %-d")
    print(f"  overview stats: 1L-2L {mc}/{sc}, 3L {len(t.get('entry3l', []))}, pc {npc}, partner12mo {p12}, openings {total}")


WIRED = [wire_public_interest, wire_campus_exams, wire_lateral, wire_pc, wire_entry3l,
         wire_summer_split, wire_lateral_charts, wire_partner_charts, wire_threeL_charts,
         wire_postclerk_charts, wire_lawstudent_charts, wire_overview_stats]


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
