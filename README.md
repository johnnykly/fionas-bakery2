# Fiona's Bakery: webbplats (riktning A, "Romantisk & elegant")

A static website for Fiona's Bakery, a one-person custom-cake studio in Arlöv/Malmö. Plain HTML, CSS and JS with a small Python build script. It has no framework runtime and makes no third-party requests.

## Pages

| URL | Source |
| --- | --- |
| `/` | `src/pages/index.html` |
| `/brollopstartor/` | `src/pages/brollopstartor.html` |
| `/tartor-till-fest/` | `src/pages/tartor-till-fest.html` |
| `/foretag-och-catering/` | `src/pages/foretag-och-catering.html` |
| `/priser/` (with FAQPage JSON-LD) | `src/pages/priser.html` |
| `/om-fiona/` | `src/pages/om-fiona.html` |
| `/bestall/` (order form) | `src/pages/bestall.html` |
| `/integritet/` | `src/pages/integritet.html` |
| `404.html` | `src/pages/404.html` |

Shared header and footer live in `src/partials/layout.html`.

## Build and preview

```sh
python3 tools/build.py            # writes _site/
python3 tools/check.py            # dashes, h1 count, alt text, broken links
python3 -m http.server -d _site 8000
```

`--base /repo-name/` builds for a GitHub Pages project URL. The workflow in `.github/workflows/pages.yml` does this automatically: it uses `/` on a custom domain and `/<repo>/` otherwise. To deploy, set **Settings → Pages → Source** to "GitHub Actions" and push to `main`.

When moving to fionasbakery.se, add the custom domain under Settings → Pages. Canonical URLs, the sitemap and Open Graph tags already point to `https://fionasbakery.se/`.

## Order form

The form at `/bestall/` has these defaults:

- **No endpoint (current setting):** submitting opens the visitor's mail app with a pre-filled email to kontakt@fionasbakery.se. The success screen also shows the text so it can be copied.
- **Formspree:** set `data-endpoint="https://formspree.io/f/XXXX"` on `<form id="order-form">` in `src/pages/bestall.html`.
- **Web3Forms:** set `data-endpoint="https://api.web3forms.com/submit"` and `data-access-key="YOUR_KEY"`.

A link like `/bestall/?tillfalle=brollop` pre-selects the occasion. The values are `brollop`, `fodelsedag`, `dop`, `mohippa`, `foretag` and `annat`.

## Assets

- **Photos:** Fiona's own photos from fionasbakery.se. `tools/images.py <originals-dir>` converts them to WebP at 640 px and 1200 px wide (or at the original width when the original is narrower), writes the 1200×630 OG images, and writes `src/images.json`, which holds each photo's size and Swedish alt text. Cakes showing other brands' logos or licensed characters are left out.
- **Fonts:** Cormorant Garamond and Hanken Grotesk, both variable fonts from Fontsource and both SIL OFL. They are self-hosted in `assets/fonts/`.
- **Icons:** Phosphor Icons, light weight (MIT). The SVGs are copied into `assets/icons/` and inlined at build time.
- **Logo:** `assets/logo/` holds the logo files. The mark is an original drawing of a sugar-flower petal around a didone "F". The wordmark is Cormorant Garamond converted to outlines with `tools/logo.py`. Both are one colour and use `currentColor` inline.

## Still to do before launch

- Add a portrait of Fiona to `/om-fiona/` (there is none yet).
- Choose a form endpoint, or keep the mailto fallback.
- Review the privacy text in `/integritet/` once the form service has been chosen.
- Add more photos from Instagram if wanted. Instagram blocks automated downloads, so only photos from the current site are included.
