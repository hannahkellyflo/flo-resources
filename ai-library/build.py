#!/usr/bin/env python3
"""Build site/ai-library/index.html from the sources in this directory.

    cd ai-library && python3 build.py

Like pipeline/, this directory is the source and site/ is the output: never
hand-edit site/ai-library/index.html. The page ships as one self-contained file
with CSS, JS, prompt data and both fonts inlined, so it makes no external
requests — same contract as site/tracker/index.html.

Fonts are inlined as base64 rather than loaded from Google Fonts: the page is
served from resources.joinflo.com, and Season Mix is a licensed brand font that
should not come from a CDN in any case.
"""
import base64, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "site" / "ai-library" / "index.html"

TITLE = "The Flo AI Prompt Library"
DESCRIPTION = ("Prompts you can copy into Flo AI to get answers out of your "
               "recruiting and performance data.")
CANONICAL = "https://resources.joinflo.com/ai-library"

# Mirrors the icon set pipeline/build.py wires up; the files live at the site root.
HEAD = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{DESCRIPTION}">
<link rel="canonical" href="{CANONICAL}">

<meta property="og:type" content="website">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESCRIPTION}">
<meta property="og:url" content="{CANONICAL}">
<meta name="twitter:card" content="summary">

<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
"""


def data_uri(path, mime="font/ttf"):
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def build():
    css = (HERE / "styles.css").read_text(encoding="utf-8")
    template = (HERE / "template.html").read_text(encoding="utf-8")
    data_js = (HERE / "prompt-data-v4.js").read_text(encoding="utf-8")
    app_js = (HERE / "app.js").read_text(encoding="utf-8")

    # --- fonts: replace the @font-face src and the Google Fonts link ----------
    season = data_uri(HERE / "fonts" / "SeasonMix-SemiBold.ttf")
    zalando = data_uri(HERE / "fonts" / "ZalandoSans-Variable.ttf")

    css, n = re.subn(
        r'src:url\("\./fonts/SeasonMix-SemiBold\.otf"\)[^;]*;',
        f'src:url("{season}") format("truetype");',
        css)
    if n != 1:
        sys.exit("build: could not rewrite the Season Mix @font-face src")

    # Zalando came from Google Fonts in the standalone build; inline it instead.
    css = css.replace(
        '@font-face{',
        '@font-face{\n  font-family:"Zalando Sans";\n'
        f'  src:url("{zalando}") format("truetype");\n'
        '  font-weight:400 700;font-stretch:75% 125%;font-style:normal;font-display:swap;\n'
        '}\n@font-face{', 1)

    # --- js: fold the data module into the app, dropping import/export --------
    data_js = re.sub(r'^export\s+const\s+', 'const ', data_js, flags=re.M)
    app_js = re.sub(r'^import\s+\{[^}]*\}\s+from\s+"\./prompt-data-v4\.js";\s*$',
                    '', app_js, flags=re.M)
    script = f"{data_js}\n\n{app_js}"

    # --- body: strip the document wrapper and the external <link>s ------------
    body = template.split("<body>", 1)[1].rsplit("</body>", 1)[0].strip()
    body = re.sub(r'\s*<script type="module" src="\./app\.js"></script>', '', body)

    html = (HEAD
            + "\n<style>\n" + css.strip() + "\n</style>\n"
            + "</head>\n<body>\n"
            + body
            + '\n\n<script type="module">\n' + script.strip() + "\n</script>\n"
            + "</body>\n</html>\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    kb = len(html.encode("utf-8")) / 1024
    print(f"wrote {OUT.relative_to(HERE.parent)}  ({kb:,.0f} KB)")


if __name__ == "__main__":
    build()
