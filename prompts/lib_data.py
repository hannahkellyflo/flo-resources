"""Shared helpers for reading and writing prompt-data-v4.js.

The data file is JS, but PROMPTS/CATEGORIES/THEMES/JOBS and the two NOTES maps
are all JSON-compatible literals, so we slice them out by brace matching rather
than parsing JavaScript.
"""
import json, pathlib, re

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "prompt-data-v4.js"

EXPORTS = ["PROMPTS", "CATEGORIES", "THEMES", "JOBS", "CATEGORY_NOTES", "JOB_NOTES"]


def _span(src, name):
    marker = f"export const {name} = "
    i = src.index(marker) + len(marker)
    depth = 0
    for j in range(i, len(src)):
        if src[j] in "[{":
            depth += 1
        elif src[j] in "]}":
            depth -= 1
            if depth == 0:
                return i, j + 1
    raise ValueError(f"unterminated literal for {name}")


def load(path=DATA):
    src = pathlib.Path(path).read_text(encoding="utf-8")
    out = {}
    for name in EXPORTS:
        a, b = _span(src, name)
        out[name] = json.loads(src[a:b])
    return out, src


def write(values, src, path=DATA):
    """Splice new values back in, preserving everything else byte-for-byte."""
    spans = sorted(((_span(src, n), n) for n in EXPORTS), reverse=True)
    for (a, b), name in spans:
        src = src[:a] + json.dumps(values[name], indent=1, ensure_ascii=False) + src[b:]
    pathlib.Path(path).write_text(src, encoding="utf-8")


def slugify(s):
    s = str(s).lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def bracket_vars(prompt):
    return re.findall(r"\[[^\]]+\]", prompt)
