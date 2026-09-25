#!/usr/bin/env python3
"""Pull the Airtable base and regenerate prompt-data-v4.js.

    export AIRTABLE_TOKEN=pat...
    export AIRTABLE_BASE_ID=app...
    python3 tools/sync-airtable.py [--dry-run]

Nothing is written unless the pulled data passes validation, so a bad edit in
Airtable fails here rather than on the live site. Review the git diff, then
commit and push — Vercel deploys from the committed file.

Derived fields (slug, vars) are computed here. Do not add them to Airtable.
"""
import argparse, json, os, sys, urllib.parse, urllib.request
from lib_data import load, write, slugify, bracket_vars, HERE

API = "https://api.airtable.com/v0"

def fetch(base, table, token):
    """Return all records from a table, following pagination."""
    rows, offset = [], None
    while True:
        q = {"pageSize": "100"}
        if offset:
            q["offset"] = offset
        url = f"{API}/{base}/{urllib.parse.quote(table)}?{urllib.parse.urlencode(q)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                payload = json.load(r)
        except urllib.error.HTTPError as ex:
            body = ex.read().decode("utf-8", "replace")[:400]
            sys.exit(f"Airtable {ex.code} on table {table!r}: {body}")
        rows.extend(payload.get("records", []))
        offset = payload.get("offset")
        if not offset:
            return rows

def by_order(records, label):
    """Sort records by their Order field, complaining if any lack one."""
    missing = [r for r in records if r["fields"].get("Order") is None]
    if missing:
        names = ", ".join(repr(r["fields"].get("Name", r["id"])) for r in missing[:5])
        sys.exit(f"{label}: {len(missing)} record(s) have no Order value ({names})")
    return sorted(records, key=lambda r: r["fields"]["Order"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change without writing")
    args = ap.parse_args()

    token = os.environ.get("AIRTABLE_TOKEN")
    base = os.environ.get("AIRTABLE_BASE_ID")
    if not token or not base:
        sys.exit("Set AIRTABLE_TOKEN and AIRTABLE_BASE_ID in the environment.")

    cats_raw = by_order(fetch(base, "Categories", token), "Categories")
    subs_raw = by_order(fetch(base, "Subheadings", token), "Subheadings")
    jobs_raw = by_order(fetch(base, "Jobs", token), "Jobs")
    prompts_raw = fetch(base, "Prompts", token)

    cat_name = {r["id"]: r["fields"]["Name"] for r in cats_raw}
    sub_name = {r["id"]: r["fields"]["Name"] for r in subs_raw}
    job_name = {r["id"]: r["fields"]["Name"] for r in jobs_raw}

    def one_link(fields, key, table):
        v = fields.get(key) or []
        if not v:
            return None
        if len(v) > 1:
            sys.exit(f"{fields.get('Title', '?')!r}: {key} links to {len(v)} records; expected one")
        return table.get(v[0])

    CATEGORIES = [cat_name[r["id"]] for r in cats_raw]
    JOBS = [job_name[r["id"]] for r in jobs_raw]

    THEMES = {c: [] for c in CATEGORIES}
    for r in subs_raw:
        parent = one_link(r["fields"], "Category", cat_name)
        if parent is None:
            sys.exit(f"Subheading {r['fields'].get('Name')!r} has no parent Category")
        THEMES[parent].append(r["fields"]["Name"])

    CATEGORY_NOTES = {cat_name[r["id"]]: r["fields"].get("Description", "") for r in cats_raw}
    JOB_NOTES = {job_name[r["id"]]: r["fields"].get("Description", "") for r in jobs_raw}

    prompts_raw = by_order(prompts_raw, "Prompts")
    PROMPTS = []
    for r in prompts_raw:
        f = r["fields"]
        title = (f.get("Title") or "").strip()
        text = (f.get("Prompt") or "").strip()
        if f.get("n") is None:
            sys.exit(f"Prompt {title!r} has no n value")
        item = {
            "n": int(f["n"]),
            "slug": slugify(title),
            "title": title,
            "prompt": text,
            "category": one_link(f, "Category", cat_name) or "",
            "theme": one_link(f, "Subheading", sub_name) or "",
            "jobs": [job_name[i] for i in (f.get("Jobs") or []) if i in job_name],
            "vars": bracket_vars(text),
        }
        req = (f.get("Requirements") or "").strip()
        if req:
            item["req"] = req
        PROMPTS.append(item)

    # Render order is array order, and the page relies on ascending n.
    PROMPTS.sort(key=lambda p: p["n"])

    values, src = load()
    before = json.dumps(values, sort_keys=True)
    values.update(PROMPTS=PROMPTS, CATEGORIES=CATEGORIES, THEMES=THEMES, JOBS=JOBS,
                  CATEGORY_NOTES=CATEGORY_NOTES, JOB_NOTES=JOB_NOTES)
    after = json.dumps(values, sort_keys=True)

    print(f"pulled {len(PROMPTS)} prompts · {len(CATEGORIES)} categories · "
          f"{sum(len(v) for v in THEMES.values())} subheadings · {len(JOBS)} jobs")

    if before == after:
        print("no changes.")
        return 0

    if args.dry_run:
        print("changes detected (dry run — nothing written).")
        return 0

    write(values, src)
    print(f"wrote {(HERE / 'prompt-data-v4.js').name}\n")

    # Validate what we just wrote; on failure restore the original file text
    # verbatim, so a bad pull can never land.
    sys.path.insert(0, str(HERE))
    import validate_data
    if validate_data.main() != 0:
        (HERE / "prompt-data-v4.js").write_text(src, encoding="utf-8")
        sys.exit("\nvalidation failed — data file restored, nothing changed")
    print("\nReview `git diff prompt-data-v4.js`, then commit and push to deploy.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
