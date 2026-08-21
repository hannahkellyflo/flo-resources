# flo-resources

Static resources hosted for Flo at **resources.joinflo.com**.

## Layout

Everything Vercel serves lives under `site/`, and the directory structure *is* the URL
structure. Add a new page as `site/<slug>/index.html` and it's live at
`resources.joinflo.com/<slug>`.

```
site/
  vercel.json          # / -> /tracker redirect; /tracker/* rewrite (see below)
  tracker/index.html   # -> resources.joinflo.com/tracker
```

Deploy on Vercel with **Root Directory = `site`** (Framework preset: *Other*).

## Page metadata and icons

`build.py` prepends a document head (`HEAD` in that file) to the page it writes: title,
description, canonical URL, link-preview tags, and icon links. The shell starts straight at
`<script>`, so without this the page ships no title, no icon and no charset.

It lives in `build.py` rather than in `artifact-shell.html` (regenerated wholesale) or the
template's `<helmet>` block — helmet is appended by JS after boot, which browsers honour but
crawlers and link unfurlers never see, so OG tags there would not unfurl.

Two deliberate choices worth keeping:

- **No `<!doctype html>`.** Adding one flips the page from quirks mode to standards mode and
  shifts the existing layout (page height +10px, some elements ~4px). Metadata parsing doesn't
  need a doctype. Adding it is a separate change that wants a visual review of its own.
- **A fixed canonical to `/tracker`.** Every `/tracker/*` path is served this same document by
  the `vercel.json` rewrite, so they are one page; without the canonical, crawlers would treat
  each deep link as a duplicate.

Icons are generated from the Flo mark that is already inline in the template and live at the
site root (`site/favicon.ico`, `favicon-{16,32,48,192,512}.png`, `apple-touch-icon.png`). The
16–48px sizes use a tighter crop so the wordmark stays legible at tab size.

There is no `og:image` yet, so link previews unfurl as text (title + description) rather than a
card with a picture. That needs a designed 1200×630 asset.

## URLs inside the tracker

The tracker is one page, but its views are addressable. The shape is
`/tracker/{world}/{group}/{section}/{tab}`, with the tab left off when it's the section's
default:

| URL | View |
| --- | --- |
| `/tracker` | Landing page, both columns |
| `/tracker/student` | Law Student Recruiting card grid |
| `/tracker/attorney` | Attorney Recruiting card grid |
| `/tracker/student/lawfirm/summer` | 1L–2L Summer Associates (1L Summer) |
| `/tracker/student/lawfirm/summer/2l` | ” (2L Summer) |
| `/tracker/student/lawfirm/summer/campus` | ” (Campus Programs) |
| `/tracker/student/lawfirm/summer/examsgrades` | ” (Exams & Grades) |
| `/tracker/student/lawfirm/summer/market` | ” (Market Data) |
| `/tracker/student/lawfirm/3l` | 3L Entry-Level Associates (Job Details) |
| `/tracker/student/lawfirm/3l/market` | ” (Market Data) |
| `/tracker/student/lawfirm/fall3l` | 3L Fall Associates (Law Firm Direct Apply) |
| `/tracker/student/lawfirm/fall3l/market` | ” (Market Data) |
| `/tracker/student/publicinterest/intern` | Law Student Internships |
| `/tracker/student/publicinterest/entrylevel` | Entry-Level Positions |
| `/tracker/attorney/lawfirm/postclerk` | Post-Judicial Clerkship (Job Details) |
| `/tracker/attorney/lawfirm/postclerk/market` | ” (Market Data) |
| `/tracker/attorney/lawfirm/nonpartner` | Lateral Non-Partners (Search Details) |
| `/tracker/attorney/lawfirm/nonpartner/market` | ” (Market Data) |
| `/tracker/attorney/lawfirm/partner` | Lateral Partners (Market Data) |
| `/tracker/attorney/publicinterest/positions` | Attorney Positions |

`group` is the section's own `group` field (`Law Firm` / `Public Interest`), and it is
verified on the way in — a section can't be reached under the wrong group. `3L Fall Associates`
sits under `lawfirm` because that is its group: it is law-firm direct-apply content, despite
the `pi*` naming of the genuinely public-interest sections around it. It has a URL but no
section tab and no overview card yet, so it isn't reachable by clicking.

Slugs live in `SECTION_SLUG` / `TAB_SLUG` in `pipeline/template.dc.html`. Anything without
an entry falls back to its raw id, so a new section or tab still gets a working URL with
nothing to add — the maps only exist to make the URLs readable.

Two pieces make this work, and both matter:

- The app pushes the URL from each nav handler (`enterSub`, `selectSub`, `selectTab`,
  `goOverview`, `openWorld`, `backToLanding`) and reads it back on load and on `popstate`.
  This runtime doesn't invoke `componentDidUpdate`, so the sync is inline per handler — the
  same reason `scrollTop()` is called that way.
- `site/vercel.json` rewrites `/tracker/*` to `tracker/index.html`, so refreshing or sharing
  a deep link serves the page instead of a 404.

An unknown path, or a real section under the wrong group, falls back to the landing page and
normalizes the URL; so does a group with no section (`/tracker/student/lawfirm`), since the
focused grid shows both groups. An explicitly named default tab canonicalizes to the short
form. Served from anywhere other than `/tracker` — a local `file://`, a bare static server —
routing switches off and the dashboard behaves as it did before it existed.

## /tracker — Legal Recruiting Tracker

Flo's public Legal Recruiting Tracker dashboard: a single self-contained `index.html`
(React, runtime, fonts, and data all inlined; no build step, no external requests).

It's generated, so don't hand-edit `site/tracker/index.html`. Change the inputs in
`pipeline/` and rebuild:

```sh
cd pipeline
python3 generate.py   # refresh data.json from Metabase/Airtable (needs API keys)
python3 build.py      # write ../site/tracker/index.html
```

`.github/workflows/refresh-tracker.yml` runs both on weekday mornings and commits any
change, so pushing to `main` is all that's needed to publish.

> Note: data is a work-in-progress snapshot, not yet wired to live Metabase/Airtable.
