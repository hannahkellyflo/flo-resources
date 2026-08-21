# flo-resources

Static resources hosted for Flo at **resources.joinflo.com**.

## Layout

Everything Vercel serves lives under `site/`, and the directory structure *is* the URL
structure. Add a new page as `site/<slug>/index.html` and it's live at
`resources.joinflo.com/<slug>`.

```
site/
  vercel.json          # redirects / -> /tracker until a real homepage exists
  tracker/index.html   # -> resources.joinflo.com/tracker
```

Deploy on Vercel with **Root Directory = `site`** (Framework preset: *Other*).

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
