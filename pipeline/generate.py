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
    years = [int(c["name"]) for c in (grad_cells or []) if c.get("name", "").isdigit()]
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
        f = r["cellValuesByFieldId"]
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


# ── TODO: other live sections (wire incrementally) ───────────────────────────
# campus/exams  -> Airtable tbl3TysOhuqGmnTp6 (currently empty -> render blank, correct)
# entry3l       -> Metabase #5413 grad-target 2027 + Airtable page pagf1mxzXOqa5fjDz
# lateral / pc  -> Metabase #5413 hiring-type filters
# charts.*      -> Metabase aggregations (see specs 01-08 / memory); judgment-heavy
#                  ones (practice-from-title, funnel, headcount) stay on snapshot until validated
WIRED = [wire_public_interest]


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
