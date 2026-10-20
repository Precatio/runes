"""Skärmbilder till "Så gör du"-artikeln om huggspårsanalys: appen körs i en huvudlös webbläsare mot de lokala
dev-servrarna (web :3000, api :8000), en skanning laddas upp och den automatiska analysen körs enligt Vitki-protokollet.
Bilderna sparas som PNG i utdata/blogg/howto/ och fryses i bloggens bildarkiv av build_howto_huggspar.py.
    PLAYWRIGHT_BROWSERS_PATH=/Volumes/2TB/cache/ms-playwright .venv/bin/python utdata/blogg/build/howto_huggspar_bilder.py SKANNING.stl
"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "utdata", "blogg", "howto")
os.makedirs(OUT, exist_ok=True)
SCAN = sys.argv[1]
ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]


def shot(loc, name, pad=0):
    """Elementet i sin helhet (Playwright rullar fram det och tar med det som ligger utanför fönstret)."""
    loc.scroll_into_view_if_needed()
    loc.page.wait_for_timeout(600)
    loc.screenshot(path=os.path.join(OUT, name))
    print("sparade", name)


with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    pg = b.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=2)
    pg.goto("http://localhost:3000/3d", wait_until="networkidle", timeout=90000)
    pg.wait_for_timeout(1500)
    pg.screenshot(path=os.path.join(OUT, "01_sidan.png"))
    card = pg.locator("form").first.locator("..")
    shot(card, "02_installningar_tom.png")

    pg.set_input_files("input[type=file]", SCAN)
    pg.get_by_text("Automatiskt", exact=True).wait_for(timeout=120000)
    for _ in range(60):
        pg.wait_for_timeout(5000)
        if "inläst" in pg.locator("text=Status").first.locator("..").inner_text():
            break
    pg.wait_for_timeout(3000)
    shot(pg.locator("text=Status").first.locator(".."), "03_status_inlast.png")
    shot(pg.locator("text=Mätsätt").first.locator(".."), "04_matsatt.png")

    pg.get_by_text("Automatiskt", exact=True).click()
    pg.wait_for_timeout(800)
    auto = pg.get_by_text("Vitki-protokollet", exact=False).first.locator("..").locator("..").locator("..")
    shot(auto, "05_automatisk_panel.png")
    pg.screenshot(path=os.path.join(OUT, "06_sidan_fore_analys.png"))

    t0 = time.time()
    pg.get_by_role("button", name="Kör automatisk analys").click()
    pg.get_by_text("Granska den automatiska analysen").wait_for(timeout=20 * 60 * 1000)
    print("analys klar efter", round(time.time() - t0), "s")
    pg.wait_for_timeout(4000)
    pg.screenshot(path=os.path.join(OUT, "07_sidan_efter_analys.png"), full_page=True)
    shot(pg.locator("text=Status").first.locator(".."), "08_status_klar.png")
    review = pg.get_by_text("Granska den automatiska analysen").locator("..").locator("..").locator("..")
    shot(review, "09_granska.png")
    canvas = pg.locator("canvas").first
    if canvas.count():
        shot(canvas, "10_3d_vy.png", pad=0)
    pg.get_by_role("button", name="Använd runorna som resultat").click()
    pg.get_by_text("Huggteknik jämfört med mätkorpusen").wait_for(timeout=120000)
    pg.wait_for_timeout(2500)
    panel = pg.get_by_text("Huggteknik jämfört med mätkorpusen").locator("..").locator("..").locator("..")
    shot(panel, "11_resultat.png")
    # Måtten (rutorna med V-vinkel m.m.) står först i resultatpanelen; ta hela panelens förälder också
    shot(panel.locator(".."), "11b_resultat_allt.png")
    rep = pg.get_by_text("Stenrapport", exact=True)
    if rep.count():
        shot(rep.first.locator("..").locator(".."), "12_stenrapport.png")
    sp = pg.get_by_role("button", name="Spara snitt i Projekt")
    if sp.count():
        shot(sp.first, "12_spara.png")
    pg.screenshot(path=os.path.join(OUT, "13_sidan_slut.png"))
    b.close()
print("klart")
