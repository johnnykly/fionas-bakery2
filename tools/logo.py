"""Generate the Fiona's Bakery logo SVGs.

The wordmark is set in Cormorant Garamond (SIL OFL) and converted to outlines so
the SVG renders identically everywhere without a font dependency. The monogram
is an original drawing: a single sugar-flower petal framing a didone-style "F".

Usage:
  pip install fonttools brotli
  python3 tools/logo.py <path-to>/@fontsource/cormorant-garamond/files

Writes assets/logo/*.svg and assets/favicon.svg and prints the inline symbol
markup used in src/partials/logo-symbols.html.
"""
import re
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else None

# Single petal, notched at the top like a cherry blossom petal. 100 x 120 box.
PETAL = (
    "M50 116C26 100 9 74 11 48C13 24 29 8 44 8C47 8 49 10 50 13"
    "C51 10 53 8 56 8C71 8 87 24 89 48C91 74 74 100 50 116Z"
)
# Didone "F": thick stem, hairline arms with bracket serifs.
F_MARK = (
    "M36 34H66V47H64.4C63.6 41 61.6 37.6 55 37.6H47.6V61.6H54.6"
    "C58.4 61.6 59.4 60 59.8 56.4H61.4V70.6H59.8C59.4 67 58.4 65.4 54.6 65.4"
    "H47.6V87.4C47.6 89.6 48.6 90.4 52 90.6V92H34V90.6C37.4 90.4 39.4 89.6 39.4 87.4"
    "V38.6C39.4 36.4 37.4 35.6 36 35.4Z"
)


def mark_svg(stroke=2.2):
    return (
        f'<path d="{PETAL}" fill="none" stroke="currentColor" stroke-width="{stroke}" '
        f'stroke-linejoin="round"/>'
        f'<path d="{F_MARK}" fill="currentColor"/>'
    )


def set_text(font_path, text, size, x0, baseline, tracking=0.0):
    font = TTFont(font_path)
    cmap = font.getBestCmap()
    gs = font.getGlyphSet()
    upm = font["head"].unitsPerEm
    scale = size / upm
    paths = []
    x = x0
    for ch in text:
        gname = cmap[ord(ch)]
        pen = SVGPathPen(gs)
        tpen = TransformPen(pen, (scale, 0, 0, -scale, x, baseline))
        gs[gname].draw(tpen)
        d = pen.getCommands()
        if d:
            paths.append(d)
        x += gs[gname].width * scale + tracking
    return " ".join(paths), x


def round_path(d, nd=1):
    def fmt(m):
        v = f"{float(m.group()):.{nd}f}".rstrip("0").rstrip(".")
        return "0" if v in ("-0", "") else v
    return re.sub(r"-?\d+(?:\.\d+)?", fmt, d)


def main():
    if not FONT_DIR:
        sys.exit("pass the @fontsource/cormorant-garamond/files directory")
    upright = FONT_DIR / "cormorant-garamond-latin-500-normal.woff2"
    italic = FONT_DIR / "cormorant-garamond-latin-500-italic.woff2"

    # Wordmark: "Fiona’s" upright, "Bakery" italic, on one baseline.
    size, base = 64, 56
    d1, x = set_text(upright, "Fiona’s", size, 0, base, tracking=0.6)
    d2, x2 = set_text(italic, "Bakery", size, x + 15, base, tracking=0.2)
    width = round(x2 + 2)
    word = round_path(d1 + " " + d2)

    out = ROOT / "assets" / "logo"
    out.mkdir(parents=True, exist_ok=True)
    (out / "wordmark.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 72" '
        f'role="img" aria-labelledby="t"><title id="t">Fiona’s Bakery</title>'
        f'<path fill="#2E2430" d="{word}"/></svg>\n'
    )
    (out / "mark.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 120" '
        'role="img" aria-labelledby="t"><title id="t">Fiona’s Bakery</title>'
        f'<g color="#2E2430">{mark_svg()}</g></svg>\n'
    )
    # Lockup: mark + wordmark side by side.
    lock_w = 100 + 22 + width
    (out / "logo.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {lock_w} 120" '
        f'role="img" aria-labelledby="t"><title id="t">Fiona’s Bakery</title>'
        f'<g color="#2E2430">{mark_svg()}</g>'
        f'<path fill="#2E2430" transform="translate(122 26)" d="{word}"/></svg>\n'
    )
    # Favicon: plum petal on warm white, adapts to dark mode.
    (ROOT / "assets" / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 120">'
        "<style>g{color:#2E2430}@media (prefers-color-scheme:dark){g{color:#F3E9EB}}</style>"
        f"<g>{mark_svg(stroke=4)}</g></svg>\n"
    )
    # Inline <symbol>s for the header/footer.
    (ROOT / "src" / "partials" / "logo-symbols.html").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false" style="position:absolute;width:0;height:0;overflow:hidden">'
        f'<symbol id="logo-mark" viewBox="0 0 100 120">{mark_svg()}</symbol>'
        f'<symbol id="petal" viewBox="0 0 100 120"><path d="{PETAL}" fill="none" stroke="currentColor" stroke-width="1.2"/></symbol>'
        f'<symbol id="logo-word" viewBox="0 0 {width} 72"><path fill="currentColor" d="{word}"/></symbol>'
        "</svg>\n"
    )
    print("wordmark width", width)


if __name__ == "__main__":
    main()
