"""Skärmbilder till artikeln om sidan Ristarna (build_ristarna.py): Balles fingeravtryck, heatmapen sten för sten
(de signerade och de första attribuerade raderna), kärna/spann/ytterkant och kartan. Tas ur den körande appen
(localhost:3000/ristare#balle).
    PLAYWRIGHT_BROWSERS_PATH=/Volumes/2TB/cache/ms-playwright .venv/bin/python utdata/blogg/build/ristarna_bilder.py
"""
import os

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "utdata", "blogg", "ristarna")
os.makedirs(OUT, exist_ok=True)


def panel_of(pg, heading):
    return pg.get_by_role("heading", name=heading, exact=True).locator("xpath=ancestor::section[1]")


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1400, "height": 4000}, device_scale_factor=2)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://localhost:3000/ristare#balle", wait_until="networkidle", timeout=300000)
    pg.get_by_role("heading", name="Balle – vilka stenar följer hans drag?").wait_for(timeout=120000)
    pg.wait_for_timeout(2500)
    pg.add_style_tag(content=".rp-root .sticky { position: static !important; }")  # the picker bar must not cover the panels
    pg.wait_for_timeout(300)
    for heading, name in (("Fingeravtrycket", "01_fingeravtryck.png"), ("Kärna, spann och ytterkant", "03_karna_ytterkant.png"),
                          ("Var stenarna står", "04_karta.png")):
        loc = panel_of(pg, heading)
        loc.scroll_into_view_if_needed()
        pg.wait_for_timeout(600)
        loc.screenshot(path=os.path.join(OUT, name))
        print("sparade", name)
    # The heatmap: the panel down to the 20 signed stones and the first ten attributed ones
    hm = panel_of(pg, "Sten för sten")
    hm.scroll_into_view_if_needed()
    pg.wait_for_timeout(600)
    path = os.path.join(OUT, "02_heatmap.png")
    hm.screenshot(path=path)
    box = hm.bounding_box()
    svg = pg.locator("#rp-hm").bounding_box()
    # 210 px of trait labels, 18 px group heading, 20 signed rows of 16 px, gap 20 + heading 18, ten attributed rows
    cut = svg["y"] - box["y"] + 210 + 18 + 20 * 16 + 20 + 18 + 10 * 16 + 14
    im = Image.open(path)
    im.crop((0, 0, im.width, min(im.height, round(2 * cut)))).save(path)
    print("sparade 02_heatmap.png")
    print("fel:", errs)
    b.close()
