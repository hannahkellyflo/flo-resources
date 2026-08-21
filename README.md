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

## URLs inside the tracker

The tracker is one page, but its views are addressable:

| URL | View |
| --- | --- |
| `/tracker` | Landing page, both columns |
| `/tracker/student` | Law Student Recruiting card grid |
| `/tracker/attorney` | Attorney Recruiting card grid |
| `/tracker/student/lawfirm/2lsummer` | A section, on a specific tab |

The path is `/tracker/{world}/{section}/{tab}`, where `world` is `student` (internally
`entry`) or `attorney` (internally `lateral`), and `section`/`tab` are the `SUBS` and `tabs`
ids from `pipeline/template.dc.html`. Add a section or tab there and its URL works with no
further wiring — nothing maps ids to slugs.

Two pieces make this work, and both matter:

- The app pushes the URL from each nav handler (`enterSub`, `selectSub`, `selectTab`,
  `goOverview`, `openWorld`, `backToLanding`) and reads it back on load and on `popstate`.
  This runtime doesn't invoke `componentDidUpdate`, so the sync is inline per handler — the
  same reason `scrollTop()` is called that way.
- `site/vercel.json` rewrites `/tracker/*` to `tracker/index.html`, so refreshing or sharing
  a deep link serves the page instead of a 404.

An unknown path (`/tracker/student/bogus`) falls back to the landing page and normalizes the
URL. Served from anywhere other than `/tracker` — a local `file://`, a bare static server —
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
