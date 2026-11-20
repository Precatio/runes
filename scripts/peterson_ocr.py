"""Ny teckenigenkänning av Petersons Nordiskt runnamnslexikon (2007) sida för sida med tesseract.

Lexikonet är upphovsrättsskyddat: bilder och text skrivs bara till /Volumes/2TB/cache/peterson_ocr/ (utanför repot).
Sidans egen skanning (300 ppi, pdfimages) skalas till --dpi i gråskala (eller renderas med pdftoppm), kan rensas från
genomslag från baksidan (--prep) och läses med tesseract; för varje sida skrivs pNNN.tsv (ord med position, för indraget som skiljer uppslagsord från artikeltext)
och pNNN.txt. Redan lästa sidor hoppas över, så körningen kan avbrytas och tas upp igen. En sida i taget
(tesseract får högst 4 trådar): datorn har 16 GB.

    .venv/bin/python scripts/peterson_ocr.py --pages 17-272 --out /Volumes/2TB/cache/peterson_ocr/full
    .venv/bin/python scripts/peterson_ocr.py --pages 20,45 --dpi 300 --lang swe+isl --psm 4 --out …/prov/x
"""
import argparse
import os
import subprocess
import sys
import tempfile
import time

PDF = os.environ.get("PETERSON_PDF", "/Volumes/2TB/litteratur/peterson2007_runnamnslexikon.pdf")
CACHE = "/Volumes/2TB/cache/peterson_ocr"
TESSDATA = {"best": os.path.join(CACHE, "tessdata_best"), "fast": "/opt/homebrew/share/tessdata"}


def parse_pages(spec: str) -> list[int]:
    """'17-20,45' -> [17, 18, 19, 20, 45]."""
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return out


def prep_image(src: str, dst: str, mode: str) -> None:
    """none: as rendered. levels: background normalised (page / blurred page) and light grey (show-through) set to
    white, ink kept as grey levels. otsu: levels + global binarisation."""
    if mode == "none":
        os.replace(src, dst)
        return
    import numpy as np
    from PIL import Image, ImageFilter
    im = Image.open(src).convert("L")
    a = np.asarray(im, dtype=np.float32)
    bg = np.asarray(im.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(25)), dtype=np.float32)
    n = np.clip(a / np.maximum(bg, 1) * 255.0, 0, 255)
    lo, hi = 60.0, 200.0  # ink below lo stays black, show-through above hi becomes paper
    n = np.clip((n - lo) / (hi - lo), 0, 1) * 255.0
    if mode == "otsu":
        hist = np.histogram(n, bins=256, range=(0, 256))[0].astype(np.float64)
        p = hist / hist.sum()
        w = np.cumsum(p)
        mu = np.cumsum(p * np.arange(256))
        sb = (mu[-1] * w - mu) ** 2 / np.maximum(w * (1 - w), 1e-12)
        t = int(np.argmax(sb))
        n = np.where(n > t, 255.0, 0.0)
    Image.fromarray(n.astype(np.uint8)).save(dst)
    os.remove(src)


def ocr_page(page: int, out: str, dpi: int, lang: str, psm: int, model: str, prep: str,
             render: str = "pdfimages") -> float:
    base = os.path.join(out, f"p{page:03d}")
    if os.path.exists(base + ".tsv") and os.path.exists(base + ".txt"):
        return 0.0
    t0 = time.time()
    with tempfile.TemporaryDirectory(dir=CACHE) as tmp:
        if render == "pdftoppm":
            subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", str(dpi), "-gray", "-png", PDF,
                            os.path.join(tmp, "r")], check=True)
        else:  # the page's own 300 ppi scan, scaled with Lanczos (pdftoppm spends ~13 s per page on this 177 MB PDF)
            from PIL import Image
            subprocess.run(["pdfimages", "-f", str(page), "-l", str(page), "-j", PDF, os.path.join(tmp, "s")], check=True)
            src = sorted(f for f in os.listdir(tmp) if f.startswith("s"))[0]
            im = Image.open(os.path.join(tmp, src)).convert("L")
            f = dpi / 300.0
            if f != 1.0:
                im = im.resize((round(im.width * f), round(im.height * f)), Image.LANCZOS)
            im.save(os.path.join(tmp, "r.png"))
            os.remove(os.path.join(tmp, src))
        raw = [f for f in os.listdir(tmp) if f.startswith("r")][0]
        img = os.path.join(tmp, "page.png")
        prep_image(os.path.join(tmp, raw), img, prep)
        env = dict(os.environ, OMP_THREAD_LIMIT="4")
        subprocess.run(["tesseract", img, base, "--tessdata-dir", TESSDATA[model], "-l", lang, "--psm", str(psm),
                        "--dpi", str(dpi), "-c", "preserve_interword_spaces=1", "txt", "tsv"],
                       check=True, capture_output=True, env=env)
    return time.time() - t0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pages", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dpi", type=int, default=400)
    ap.add_argument("--lang", default="swe+isl+dan")
    ap.add_argument("--psm", type=int, default=4)
    ap.add_argument("--model", choices=sorted(TESSDATA), default="best")
    ap.add_argument("--prep", choices=["none", "levels", "otsu"], default="none")
    ap.add_argument("--render", choices=["pdfimages", "pdftoppm"], default="pdfimages")
    a = ap.parse_args(argv)
    if not os.path.abspath(a.out).startswith("/Volumes/2TB/cache/"):
        sys.exit("utdata för lexikonet hör hemma under /Volumes/2TB/cache/ (upphovsrätt, inte i repot)")
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "settings.txt"), "w") as fh:
        fh.write(f"dpi={a.dpi} lang={a.lang} psm={a.psm} model={a.model} prep={a.prep} render={a.render}\n")
    pages = parse_pages(a.pages)
    for i, p in enumerate(pages, 1):
        dt = ocr_page(p, a.out, a.dpi, a.lang, a.psm, a.model, a.prep, a.render)
        print(f"{i}/{len(pages)} s. {p} {dt:.1f} s", flush=True)


if __name__ == "__main__":
    main()
