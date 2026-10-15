"""Convert Fiona's original photos to responsive WebP files.

Usage:
  python3 tools/images.py <dir-with-originals>

Each original is named <slug>.jpg/.png. For every slug in IMAGES this writes
assets/img/<slug>-640.webp and assets/img/<slug>-<large>.webp (1200 px, or the
original width if smaller), plus 1200x630 Open Graph JPEGs for OG_CROPS, and
src/images.json which the build script reads for widths, heights and alt text.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img"
OG = ROOT / "assets" / "og"

# slug: Swedish alt text (describes what is actually in the photo)
IMAGES = {
    # Bröllop och sockerblommor
    "brollopstarta-tre-vaningar-sockerrosor": "Vit bröllopstårta i tre våningar med handgjorda sockerrosor i persika, vitt och lila och band i ljuslila",
    "tarta-sockerrosor-oblatpapper": "Hög vit tårta med sockerrosor och svepande dekor av oblatpapper i rosa och guld",
    "tarta-sockerrosor-pioner": "Vit tårta på tårtfat med sockerrosor och pioner i aprikos och vitt samt gröna blad",
    "sockerblomma-pion-narbild": "Närbild på en handgjord sockerblomma, en krämvit pion med gul mitt",
    "sockerrosor-korsbarsblommor": "Handgjorda sockerrosor i blekrosa och små körsbärsblommor av socker",
    "korsbarsblommor-i-kanna": "Kvist med körsbärsblommor och en blekrosa ros i en liten vit kanna, allt gjort av socker",
    "tarta-korsbarsblommor": "Vit tårta med en kvist körsbärsblommor och en blekrosa ros i sockermassa",
    "brollopstartor-mr-mrs": "Två vita bröllopstårtor med blommor i vitt, rosa och lila och en Mr & Mrs-dekoration på toppen",
    "smorkramstarta-tva-vaningar-rosor": "Vit smörkrämstårta i två våningar med rosor i persika och brudslöja",
    "pionstarta-fjarilar": "Hög vit tårta med guldflagor, en rosa pion, lila blommor och små fjärilar",
    # Fest och barnkalas
    "bondgardstarta-djur": "Barnkalastårta med röd lada, ett lamm, en ko och en gris i sockermassa och barnets namn",
    "kattarta": "Vit katt med rosa rosett i sockermassa på en krämvit tårta med pärlor",
    "babyshower-tarta-nallar": "Babyshowertårta i vanilj och vitt med två nallar, pärlor i lila och guld och en namnskylt",
    "its-a-girl-tarta-nallar": "Babyshowertårta med vit rosett, texten It's a girl och två nallar i rosa tyll på toppen",
    "its-a-boy-tarta-drake": "Mintgrön tårta med en liten drake i sockermassa, guldpärlor och skylten It's a boy",
    "doptarta-nalle-klossar": "Vit doptårta med en nalle, en ljusgrön filt och bokstavsklossar i ljusblått",
    "biltarta-isak": "Tårta med en leksaksbil på toppen, randig och rutig sida och barnets namn i silver",
    "tarta-genomskuren-lager": "Uppskuren tårta som visar lager i blått, grönt och gult under en vit och pastellfärgad yta",
    "macarons-babyfotter": "Macarons i rosa och mintgrönt med små babyfötter i sockermassa",
    "fodelsedagstarta-gron": "Mörkgrön födelsedagstårta med Happy Birthday i guld, röda blommor, kottar och guldkulor",
    "60-arstarta-marmor-blommor": "Rosa marmorerad tårta med vita rosor, en flaska bubbel och en 60-skylt i guld",
    "studenttarta-rosor": "Studenttårta med quiltat mönster, studentmössa, rosor och gratulationstext i guld",
    "studentmossa-tarta": "Tårta formad som en vit studentmössa med svart band",
    # Bakverk och företag
    "cupcakes-monogram-bla": "Cupcakes med turkos marängsmörkräm, sockerblommor och vita lock med monogram i guld",
    "cupcakes-monogram-grona": "Cupcakes med ljusgrön och lila smörkräm, små blommor och vita lock med monogram i guld",
    "cupcakes-luftballong": "Cupcakes med turkos smörkräm och bilder på en nalle i luftballong",
    "cake-pops-choklad": "Cake pops doppade i mörk choklad med guldstänk",
    "marangklubbor": "Maränglollipops i rosa, lila och mint på pinnar med randigt papper",
}

# slug: (output name, vertical focus 0..1)
OG_CROPS = {
    "tarta-sockerrosor-pioner": ("og-hem", 0.45),
    "sockerrosor-korsbarsblommor": ("og-brollop", 0.5),
    "its-a-girl-tarta-nallar": ("og-fest", 0.45),
    "cupcakes-monogram-bla": ("og-foretag", 0.5),
    "cupcakes-luftballong": ("og-priser", 0.5),
    "sockerblomma-pion-narbild": ("og-om", 0.45),
}


def main():
    src = Path(sys.argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    OG.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for slug, alt in IMAGES.items():
        f = next(src.glob(slug + ".*"))
        im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
        large = min(1200, im.width)
        widths = sorted({640, large})
        for w in widths:
            h = round(im.height * w / im.width)
            im.resize((w, h), Image.LANCZOS).save(OUT / f"{slug}-{w}.webp", "WEBP", quality=78, method=6)
        manifest[slug] = {
            "w": large,
            "h": round(im.height * large / im.width),
            "widths": widths,
            "alt": alt,
        }
        if slug in OG_CROPS:
            name, focus = OG_CROPS[slug]
            target = 1200 / 630
            cw, ch = im.width, round(im.width / target)
            if ch > im.height:
                ch, cw = im.height, round(im.height * target)
            left = (im.width - cw) // 2
            top = round((im.height - ch) * focus)
            im.crop((left, top, left + cw, top + ch)).resize((1200, 630), Image.LANCZOS).save(
                OG / f"{name}.jpg", "JPEG", quality=82, optimize=True, progressive=True
            )
        print(slug, widths)
    (ROOT / "src" / "images.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
