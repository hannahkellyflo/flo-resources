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
import json, os, re, urllib.request, urllib.parse, pathlib, datetime

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


# ── TODO: other live sections (wire incrementally) ───────────────────────────
# entry3l       -> Metabase #5413 grad-target 2027 + Airtable page pagf1mxzXOqa5fjDz
# lateral / pc  -> Metabase #5413 hiring-type filters
# charts.*      -> Metabase aggregations (see specs 01-08 / memory); judgment-heavy
#                  ones (practice-from-title, funnel, headcount) stay on snapshot until validated
WIRED = [wire_public_interest, wire_campus_exams]


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
