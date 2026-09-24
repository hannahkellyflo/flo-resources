#!/usr/bin/env python3
"""Validate prompt-data-v4.js. Exits non-zero on any error.

Run:  python3 tools/validate-data.py
"""
import sys
from collections import Counter
from lib_data import load, slugify, bracket_vars

def main():
    v, _ = load()
    P, CATS, THEMES = v["PROMPTS"], v["CATEGORIES"], v["THEMES"]
    JOBS, CNOTES, JNOTES = v["JOBS"], v["CATEGORY_NOTES"], v["JOB_NOTES"]

    errors, warnings = [], []
    e, w = errors.append, warnings.append

    # --- taxonomies -------------------------------------------------------
    for c in CATS:
        if c not in THEMES:      e(f"CATEGORIES has '{c}' but THEMES does not")
        if c not in CNOTES:      e(f"CATEGORY_NOTES missing '{c}'")
    for c in THEMES:
        if c not in CATS:        e(f"THEMES has '{c}' which is not in CATEGORIES")
    for j in JOBS:
        if j not in JNOTES:      w(f"JOB_NOTES missing '{j}'")

    pairs = [(c, t) for c, ts in THEMES.items() for t in ts]
    names = [t for _, t in pairs]
    for name, n in Counter(names).items():
        if n > 1:
            owners = sorted(c for c, t in pairs if t == name)
            e(f"subheading '{name}' is used by {n} categories ({', '.join(owners)}) — "
              f"names must be unique so each maps to one CMS item")
    for c, ts in THEMES.items():
        for t, n in Counter(ts).items():
            if n > 1:            e(f"category '{c}' lists subheading '{t}' {n} times")

    # --- prompts ----------------------------------------------------------
    for key, label in (("n", "n"), ("slug", "slug")):
        for val, n in Counter(p[key] for p in P).items():
            if n > 1:            e(f"duplicate {label}: {val!r} appears {n} times")

    for p in P:
        ref = f"n={p.get('n', '?')} {p.get('title', '<untitled>')!r}"
        for f in ("n", "slug", "title", "prompt", "category", "theme", "jobs"):
            if f not in p:       e(f"{ref}: missing required field '{f}'"); continue
        if not p.get("title", "").strip():  e(f"{ref}: empty title")
        if not p.get("prompt", "").strip(): e(f"{ref}: empty prompt")

        cat = p.get("category")
        if cat not in CATS:
            e(f"{ref}: unknown category {cat!r}")
        else:
            declared = THEMES.get(cat, [])
            th = p.get("theme", "")
            if th and th not in declared:
                e(f"{ref}: theme {th!r} is not declared under category {cat!r}")
            if not th and declared:
                e(f"{ref}: category {cat!r} has subheadings but this prompt has none")

        for j in p.get("jobs", []):
            if j not in JOBS:    e(f"{ref}: unknown job {j!r}")
        if not p.get("jobs"):    e(f"{ref}: must have at least one job")

        want = slugify(p.get("title", ""))
        if p.get("slug") != want:
            e(f"{ref}: slug {p.get('slug')!r} does not match title (expected {want!r})")

        want_vars = bracket_vars(p.get("prompt", ""))
        if p.get("vars", []) != want_vars:
            e(f"{ref}: vars {p.get('vars')!r} do not match brackets in prompt "
              f"(expected {want_vars!r})")

        if "[" in p.get("prompt", "") and "]" not in p.get("prompt", ""):
            e(f"{ref}: unclosed '[' in prompt text")
        if p.get("req") is not None and not str(p["req"]).strip():
            w(f"{ref}: empty requirements string — omit the field instead")

    # --- ordering ---------------------------------------------------------
    ns = [p["n"] for p in P]
    if ns != sorted(ns):
        e("PROMPTS is not sorted by ascending n — render order depends on array order")

    # --- empty buckets ----------------------------------------------------
    for c in CATS:
        if not any(p["category"] == c for p in P):
            w(f"category '{c}' has no prompts")
        for t in THEMES.get(c, []):
            if not any(p["category"] == c and p["theme"] == t for p in P):
                w(f"subheading '{c} / {t}' has no prompts")

    # --- report -----------------------------------------------------------
    counts = Counter(p["category"] for p in P)
    print(f"{len(P)} prompts · {len(CATS)} categories · {len(pairs)} subheadings · {len(JOBS)} jobs")
    for c in CATS:
        print(f"  {counts.get(c, 0):>4}  {c}")

    for m in warnings: print(f"warning: {m}")
    for m in errors:   print(f"ERROR:   {m}")

    if errors:
        print(f"\n{len(errors)} error(s).")
        return 1
    print(f"\nOK{f' — {len(warnings)} warning(s)' if warnings else ''}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
