"""Build the static site into _site/.

Usage:
  python3 tools/build.py [--base /sub/path/] [--out _site]

Pages live in src/pages/*.html. Each starts with a JSON block in an HTML
comment (<!--meta {...} -->) followed by the page body. The build wraps every
page in src/partials/layout.html, expands the small macros below, writes
sitemap.xml and robots.txt, and copies assets/.

Macros:
  <x-img slug="..." sizes="..." class="..." alt="..." eager>  responsive <img>
  <x-icon name="...">                                        inline Phosphor icon
  Root-relative href="/..." and src="/..." get the --base prefix, so the same
  source works on fionasbakery.se and on a GitHub Pages project URL.
"""
import argparse
import datetime as dt
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
SITE_URL = "https://fionasbakery.se"

NAV = [
    ("brollop", "/brollopstartor/", "Bröllop"),
    ("fest", "/tartor-till-fest/", "Fest & kalas"),
    ("foretag", "/foretag-och-catering/", "Företag"),
    ("priser", "/priser/", "Priser & smaker"),
    ("om", "/om-fiona/", "Om Fiona"),
]

BUSINESS = {
    "@context": "https://schema.org",
    "@type": "Bakery",
    "@id": SITE_URL + "/#bakery",
    "name": "Fiona's Bakery",
    "description": "Skräddarsydda tårtor, sockerblommor och bakverk till bröllop, kalas, dop, babyshower, möhippor och företag i Malmö med omnejd.",
    "url": SITE_URL + "/",
    "image": [
        SITE_URL + "/assets/og/og-hem.jpg",
        SITE_URL + "/assets/og/og-brollop.jpg",
        SITE_URL + "/assets/og/og-fest.jpg",
    ],
    "logo": SITE_URL + "/assets/logo/logo.svg",
    "telephone": "+46738740378",
    "email": "kontakt@fionasbakery.se",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "Trossgatan 25",
        "postalCode": "232 36",
        "addressLocality": "Arlöv",
        "addressCountry": "SE",
    },
    "priceRange": "$$",
    "currenciesAccepted": "SEK",
    "paymentAccepted": "Swish",
    "areaServed": [
        {"@type": "City", "name": n}
        for n in ["Malmö", "Arlöv", "Burlöv", "Lund", "Lomma", "Staffanstorp", "Vellinge"]
    ],
    "sameAs": ["https://www.instagram.com/fionasbakery/"],
}


def read(p):
    return Path(p).read_text(encoding="utf-8")


def parse_page(path):
    raw = read(path)
    m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*", raw, re.S)
    if not m:
        raise SystemExit(f"{path}: missing <!--meta {{...}} --> header")
    return json.loads(m.group(1)), raw[m.end():]


def attrs(s):
    out = {}
    for m in re.finditer(r'([\w-]+)(?:="([^"]*)")?', s):
        out[m.group(1)] = m.group(2) if m.group(2) is not None else True
    return out


class Renderer:
    def __init__(self, base):
        self.base = base
        self.images = json.loads(read(SRC / "images.json"))
        self.icons = {}

    def icon(self, m):
        a = attrs(m.group(1))
        name = a["name"]
        if name not in self.icons:
            svg = read(ROOT / "assets" / "icons" / f"{name}.svg")
            self.icons[name] = re.sub(r"<svg ", "<svg ", svg.strip(), count=1)
        svg = self.icons[name]
        cls = "icon" + (" " + a["class"] if "class" in a else "")
        return svg.replace("<svg ", f'<svg class="{cls}" aria-hidden="true" focusable="false" width="1em" height="1em" ', 1)

    def img(self, m):
        a = attrs(m.group(1))
        slug = a["slug"]
        meta = self.images[slug]
        src = lambda w: f"{self.base}assets/img/{slug}-{w}.webp"
        srcset = ", ".join(f"{src(w)} {w}w" for w in meta["widths"])
        alt = a.get("alt", meta["alt"])
        sizes = a.get("sizes", "(min-width: 64em) 50vw, 100vw")
        parts = [
            f'<img src="{src(meta["widths"][0])}"',
            f'srcset="{srcset}"',
            f'sizes="{sizes}"',
            f'width="{meta["w"]}" height="{meta["h"]}"',
            f'alt="{html.escape(alt, quote=True)}"',
        ]
        if "class" in a:
            parts.append(f'class="{a["class"]}"')
        if "eager" in a:
            parts.append('fetchpriority="high" decoding="async"')
        else:
            parts.append('loading="lazy" decoding="async"')
        return " ".join(parts) + ">"

    def expand(self, s):
        s = re.sub(r"<x-icon\s+([^>]*?)/?>", self.icon, s)
        s = re.sub(r"<x-img\s+([^>]*?)/?>", self.img, s)
        s = re.sub(r'(\s(?:href|src|action)=")/(?!/)', lambda m: m.group(1) + self.base, s)
        return s


def nav_html(active):
    items = []
    for key, href, label in NAV:
        cur = ' aria-current="page"' if key == active else ""
        items.append(f'<li><a href="{href}"{cur}>{label}</a></li>')
    return "\n          ".join(items)


def breadcrumb_ld(meta):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Hem", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": meta["crumb"], "item": SITE_URL + meta["path"]},
        ],
    }


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def faq_ld(body):
    items = []
    for m in re.finditer(
        r'<details class="faq[^"]*"[^>]*>\s*<summary[^>]*>(.*?)</summary>(.*?)</details>', body, re.S
    ):
        items.append({
            "@type": "Question",
            "name": strip_tags(m.group(1)),
            "acceptedAnswer": {"@type": "Answer", "text": strip_tags(m.group(2))},
        })
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": items}


def ld_tag(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"


def minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{}:;,>])\s*", r"\1", css)
    css = css.replace(";}", "}")
    # restore spaces needed inside media queries, e.g. "and (min-width:..."
    css = re.sub(r"\band\(", "and (", css)
    return css.strip()


def build(base, out):
    r = Renderer(base)
    # Inline the stylesheet (one small file) so it never blocks rendering.
    css = minify_css(read(ROOT / "assets" / "css" / "style.css")).replace("../fonts/", base + "assets/fonts/")
    layout = read(SRC / "partials" / "layout.html")
    symbols = read(SRC / "partials" / "logo-symbols.html")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copytree(ROOT / "assets", out / "assets", ignore=shutil.ignore_patterns("icons"))
    shutil.copy(ROOT / "assets" / "favicon.svg", out / "favicon.svg")

    today = dt.date.today().isoformat()
    urls = []
    for path in sorted((SRC / "pages").glob("*.html")):
        meta, body = parse_page(path)
        ld = []
        if meta["path"] == "/":
            ld.append(BUSINESS)
        elif meta.get("crumb"):
            ld.append(breadcrumb_ld(meta))
        if meta.get("faq"):
            ld.append(faq_ld(body))
        canonical = SITE_URL + meta["path"]
        og_img = f"{SITE_URL}/assets/og/{meta.get('og', 'og-hem')}.jpg"
        crumbs = ""
        if meta.get("crumb") and meta["path"] not in ("/", "/404.html"):
            crumbs = (
                '<nav class="breadcrumbs container" aria-label="Brödsmulor"><ol>'
                '<li><a href="/">Hem</a></li>'
                f'<li><a href="{meta["path"]}" aria-current="page">{meta["crumb"]}</a></li>'
                "</ol></nav>"
            )
        page = (
            layout.replace("{{title}}", html.escape(meta["title"]))
            .replace("{{description}}", html.escape(meta["description"], quote=True))
            .replace("{{canonical}}", canonical)
            .replace("{{og_image}}", og_img)
            .replace("{{og_alt}}", html.escape(meta.get("og_alt", "Tårta från Fiona's Bakery"), quote=True))
            .replace("{{robots}}", "noindex" if meta.get("noindex") else "index,follow")
            .replace("{{jsonld}}", "\n  ".join(ld_tag(x) for x in ld))
            .replace("{{body_class}}", meta.get("body_class", ""))
            .replace("{{nav}}", nav_html(meta.get("nav")))
            .replace("{{symbols}}", symbols)
            .replace("{{breadcrumbs}}", crumbs)
            .replace("{{year}}", str(dt.date.today().year))
            .replace("{{base}}", base)
        )
        page = page.replace('<link rel="stylesheet" href="/assets/css/style.css">', f"<style>{css}</style>")
        if meta.get("noindex"):
            page = re.sub(r'\s*<link rel="canonical"[^>]*>', "", page)
            page = re.sub(r'\s*<meta property="og:url"[^>]*>', "", page)
        page = page.replace("{{content}}", body)
        page = r.expand(page)
        if meta["path"] == "/404.html":
            dest = out / "404.html"
        else:
            dest = out / meta["path"].strip("/") / "index.html"
            urls.append((canonical, meta.get("priority", "0.7")))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page, encoding="utf-8")
        print("built", dest.relative_to(out))

    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, prio in urls:
        sm.append(f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod><priority>{prio}</priority></url>")
    sm.append("</urlset>")
    (out / "sitemap.xml").write_text("\n".join(sm) + "\n")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    (out / ".nojekyll").write_text("")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="/", help="URL path the site is served from, e.g. /fionas-bakery2/")
    ap.add_argument("--out", default=str(ROOT / "_site"))
    a = ap.parse_args()
    base = "/" + a.base.strip("/") + "/" if a.base.strip("/") else "/"
    build(base, Path(a.out))


if __name__ == "__main__":
    main()
