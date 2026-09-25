# /ai/prompts — Flo AI Prompt Library

`resources.joinflo.com/ai/prompts`. A searchable, filterable library of 129 prompts
customers copy into Flo AI. Like the tracker, the page is generated: this
directory is the source, `site/ai/prompts/index.html` is the output.

**Don't hand-edit `site/ai/prompts/index.html`.** Change the inputs here and rebuild:

```sh
cd ai/prompts
python3 build.py      # write ../../site/ai/prompts/index.html
```

`.github/workflows/verify-build.yml` rebuilds on every PR and fails if the
committed output is stale, so the two can't drift.

## Layout

| File | |
| --- | --- |
| `template.html` | Page markup. Only its `<body>` is used; `build.py` writes the head |
| `styles.css` | All styling. Design tokens are custom properties on `:root` |
| `app.js` | Filtering, counts, search, bracket highlighting, copy |
| `prompt-data-v4.js` | The prompts and taxonomies. Generated from Airtable — see below |
| `fonts/` | Season Mix SemiBold and Zalando Sans Variable, inlined at build time |
| `build.py` | Writes the single self-contained output file |
| `sync-airtable.py` | Pulls Airtable and rewrites `prompt-data-v4.js` |
| `validate_data.py` | Checks the data file. Runs in CI on every PR |
| `lib_data.py` | Shared read/write helpers |

## One self-contained file

The output inlines CSS, JS, prompt data and both fonts as base64, so the page
makes **no external requests** — the same contract as `site/tracker/index.html`,
and the reason there is no `vercel.json` change: `site/<slug>/index.html` is
already served at `/<slug>`, and this page has no client-side routing needing a
rewrite.

Fonts are inlined rather than loaded from Google Fonts because Season Mix is a
licensed brand font that shouldn't be served from a CDN, and because one request
beats four. It costs ~560KB of the 633KB output.

Unlike the tracker, this page **does** ship `<!doctype html>`. It was designed
and verified in standards mode; the tracker's quirks-mode choice is specific to
that page's layout and isn't a repo-wide convention.

## Editing prompts

Prompts are edited in **Airtable**, not here. Base `app0rvRiD5FKs7ucR` — four
tables: Categories (4), Subheadings (21), Jobs (5), Prompts (129).

```sh
export AIRTABLE_TOKEN=pat...          # data.records:read, scoped to that base
export AIRTABLE_BASE_ID=app0rvRiD5FKs7ucR

cd ai/prompts
python3 sync-airtable.py --dry-run    # report changes, write nothing
python3 sync-airtable.py              # rewrite prompt-data-v4.js
python3 build.py                      # rebuild the page
```

The sync validates before it keeps anything; on failure it restores the file
verbatim, so a bad Airtable edit fails at your desk rather than on the live page.

### Field rules

| Field | Who owns it |
| --- | --- |
| `Title`, `Prompt`, `Category`, `Subheading`, `Jobs`, `Requirements` | Editors, in Airtable |
| `n` | Stable internal id. Assign once, never reuse, never renumber |
| `Order` | Sort position. Decimals are fine — `53.5` slots between 53 and 54 |
| `slug`, `vars` | **Derived by the sync.** Never add these to Airtable |

`slug` comes from the title, `vars` from the `[brackets]` in the prompt text.
Storing them in Airtable would be two more things to keep in step.

Every subheading belongs to exactly one category, and subheading names must be
unique across the base — the validator fails if two categories share one. This
matters: the design's original data had *"Screening and criteria"* under two
categories, which made the rail show 5 prompts under each when the real split
was 2 and 3. They were renamed to `Screening criteria` and `Student screening`.

## Counts

Nothing in the UI hard-codes a total. Category blocks, rail rows, subheading
rows, section headers and the footer all derive from the data, and each count is
computed *after* the other active filters, so a dimension never counts itself.
