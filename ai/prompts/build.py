#!/usr/bin/env python3
"""Build site/ai/prompts/index.html from the sources in this directory.

    cd ai/prompts && python3 build.py

Like pipeline/, this directory is the source and site/ is the output: never
hand-edit site/ai/prompts/index.html. The page ships as one self-contained file
with CSS, JS, prompt data, the hero mark and both fonts inlined; the only thing
it fetches is the shared joinflo.com footer in an iframe — same contract as site/tracker/index.html.

Fonts are inlined as base64 rather than loaded from Google Fonts: the page is
served from resources.joinflo.com, and Season Mix is a licensed brand font that
should not come from a CDN in any case.
"""
import base64, pathlib, re, shutil, struct, sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent                       # ai/prompts/ -> repo root
SLUG = "ai/prompts"                             # URL path, and the path under site/
OUT = REPO / "site" / SLUG / "index.html"

TITLE = "The Flo AI Prompt Library"
DESCRIPTION = ("Prompts you can copy into Flo AI to get answers from your "
               "recruiting and performance data.")
SITE = "https://resources.joinflo.com"
CANONICAL = f"{SITE}/{SLUG}"

# The social card. Master lives beside the other sources; the build copies it to the site
# root next to the tracker's og-image.png, since nothing under site/ is hand-edited.
OG_SRC = HERE / "img" / "og-image.png"
OG_FILE = "og-prompts.png"


def png_size(path):
    """(width, height) of a PNG, or None if it is not one. Same reader as pipeline/build.py."""
    try:
        head = path.open("rb").read(24)
    except OSError:
        return None
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", head[16:24])


def og_image_tags():
    """The large-card tags, with the master's real pixel dimensions.

    twitter:card carries the weight here, not the file: Slack and X read it to choose
    between the full-width banner and the compact layout with a small square thumbnail.
    With "summary" they keep the compact card and ignore a 1200x630 image entirely.
    """
    size = png_size(OG_SRC)
    if size is None:
        sys.exit(f"build: {OG_SRC} is missing or not a PNG")
    width, height = size
    return (
        f'<meta property="og:image" content="{SITE}/{OG_FILE}">\n'
        f'<meta property="og:image:type" content="image/png">\n'
        f'<meta property="og:image:width" content="{width}">\n'
        f'<meta property="og:image:height" content="{height}">\n'
        f'<meta property="og:image:alt" content="{TITLE}">\n'
        f'<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:image" content="{SITE}/{OG_FILE}">\n'
        f'<meta name="twitter:title" content="{TITLE}">\n'
        f'<meta name="twitter:description" content="{DESCRIPTION}">\n'
    )


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
<meta property="og:site_name" content="Flo Resource Center">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESCRIPTION}">
<meta property="og:url" content="{CANONICAL}">
{og_image_tags()}
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

    # --- images: inline the hero mark so the page still makes no requests -----
    icon = data_uri(HERE / "img" / "flo-ai-icon.png", "image/png")
    template, n = re.subn(r'src="\./img/flo-ai-icon\.png"', f'src="{icon}"', template)
    if n != 1:
        sys.exit("build: could not inline the hero mark image")

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

    # The social card is referenced by absolute URL, so unlike the fonts and the hero mark
    # it cannot be inlined -- it has to exist as a file Slack and X can fetch.
    shutil.copyfile(OG_SRC, REPO / "site" / OG_FILE)
    kb = len(html.encode("utf-8")) / 1024
    print(f"wrote {OUT.relative_to(REPO)}  ({kb:,.0f} KB)")


if __name__ == "__main__":
    build()
