"""Skärmbilder till "Så gör du"-artikeln om Forskningsluckor: frågekorten, Våra resultat, Luckor (täckning), Nya ristare,
3D-mätning och Luckor i texten. Dev-servrarna måste köras. Bilder till utdata/blogg/howto_luckor/.
    PLAYWRIGHT_BROWSERS_PATH=/Volumes/2TB/cache/ms-playwright .venv/bin/python utdata/blogg/build/howto_luckor_bilder.py
"""
import os

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "utdata", "blogg", "howto_luckor")
os.makedirs(OUT, exist_ok=True)


def shot(loc, name):
    loc.scroll_into_view_if_needed()
    loc.page.wait_for_timeout(600)
    loc.screenshot(path=os.path.join(OUT, name))
    print("sparade", name)


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=2)
    pg.goto("http://localhost:3000/luckor", wait_until="networkidle", timeout=180000)
    pg.get_by_text("Vad säger appens analyser jämfört med forskningen?").first.wait_for(timeout=300000)
    pg.wait_for_timeout(2500)
    pg.screenshot(path=os.path.join(OUT, "01_sidan.png"))
    cards = pg.get_by_role("button", name="Vad säger appens analyser jämfört med forskningen?").first.locator("..")
    shot(cards, "02_fragekort.png")
    main = pg.locator("main").first if pg.locator("main").count() else pg.locator("body")

    def tab(question, name):
        pg.get_by_role("button", name=question).first.click()
        pg.wait_for_timeout(2500)
        pg.screenshot(path=os.path.join(OUT, name), full_page=False)
        print("sparade", name)

    tab("Vad säger appens analyser jämfört med forskningen?", "03_vara_resultat.png")
    tab("Var saknas uppgifter om runstenarna?", "04_tackning.png")
    tab("Vilka stenar utan ristare liknar en känd ristare i stavningen?", "05_nya_ristare.png")
    tab("Vilka stenar vore mest värda att mäta i 3D?", "06_3d_matning.png")
    tab("Vilka förlorade runor kan sannolikhetsmodellen fylla i?", "07_luckor_i_texten.png")
    tbl = pg.locator("table").last
    if tbl.count():
        shot(tbl, "08_luckor_tabell.png")
    b.close()
print("klart")
