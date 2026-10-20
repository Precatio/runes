"""Hemsidans fem appbilder (web/public/bilder/app-*.webp), tagna ur den körande appen på localhost:3000 med samma
utsnitt som 2026-10-18: 1600 × 965, utloggad, menyn synlig. Kräver att statistiken i R är beräknad.
    PLAYWRIGHT_BROWSERS_PATH=/Volumes/2TB/cache/ms-playwright .venv/bin/python utdata/landning/skarmbilder.py"""
import io
import os

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "web", "public", "bilder")
VIEWS = [
    ("karta", "/karta", "Kristna markörer"),
    ("inskrifter", "/inskrifter", "Exportera alla träffar"),
    ("statistik", "/statistik", "Vad statistiken säger sammantaget"),
    ("luckor", "/luckor", "Luckor i texten"),
    ("stenoversikt", "/oversikt", "Hur väl stöder metoderna Rundatas ristare"),
]

with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
    pg = b.new_page(viewport={"width": 1600, "height": 965}, device_scale_factor=1)
    only = os.environ.get("VYER", "").split(",")  # VYER=inskrifter,luckor tar om bara dessa
    for name, path, wait_text in VIEWS:
        if only != [""] and name not in only:
            continue
        pg.goto(f"http://localhost:3000{path}", wait_until="networkidle", timeout=180000)
        pg.get_by_text(wait_text).first.wait_for(timeout=300000)
        if name == "karta":
            pg.get_by_text("Kristna markörer", exact=True).first.click()
        pg.wait_for_timeout(4000)
        png = pg.screenshot()
        im = Image.open(io.BytesIO(png)).convert("RGB")
        im.save(os.path.join(OUT, f"app-{name}.webp"), "WEBP", quality=82, method=6)
        print("sparade", f"app-{name}.webp", im.size)
    b.close()
print("klart")
