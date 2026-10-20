"""Skärmbilder till "Så gör du"-artikeln om Inskrifter: sökningen, en stens sida, Runor 2020-rutan, ortografin och
sannolikhetsmodellens läsning med "Vad skannern ser" (Sö 206, som har förlorade runor och en inmätt skanning).
Dev-servrarna måste köras. Bilder till utdata/blogg/howto_inskrifter/.
    PLAYWRIGHT_BROWSERS_PATH=/Volumes/2TB/cache/ms-playwright .venv/bin/python utdata/blogg/build/howto_inskrifter_bilder.py
"""
import os

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "utdata", "blogg", "howto_inskrifter")
os.makedirs(OUT, exist_ok=True)
STONE = "Sö 206"


def shot(loc, name):
    loc.scroll_into_view_if_needed()
    loc.page.wait_for_timeout(500)
    loc.screenshot(path=os.path.join(OUT, name))
    print("sparade", name)


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=2)
    pg.goto("http://localhost:3000/inskrifter", wait_until="networkidle", timeout=90000)
    pg.wait_for_timeout(1500)
    pg.screenshot(path=os.path.join(OUT, "01_sokning.png"))
    box = pg.get_by_placeholder("Signum, plats, runtext, normalisering eller översättning")
    box.fill("Lid")
    pg.wait_for_timeout(2500)
    shot(box.locator("..").locator(".."), "02_sok_lid.png")
    pg.screenshot(path=os.path.join(OUT, "03_traffar.png"))

    pg.goto(f"http://localhost:3000/inskrifter?signum={STONE.replace(' ', '%20')}", wait_until="networkidle", timeout=90000)
    pg.wait_for_timeout(2500)
    pg.screenshot(path=os.path.join(OUT, "04_stensida.png"))
    head = pg.locator("h2", has_text=STONE).first.locator("..").locator("..").locator("..")
    shot(head, "05_uppgifter.png")
    runor = pg.get_by_text("Runor 2020 (Riksantikvarieämbetet)")
    if runor.count():
        shot(runor.first.locator(".."), "06_runor.png")
    orto = pg.get_by_role("heading", name="Ortografisk profil")
    if orto.count():
        shot(orto.first.locator("..").locator(".."), "07_ortografi.png")

    pg.get_by_role("button", name="Läs med sannolikhetsmodellen").click()
    pg.get_by_text("förlorad", exact=False).first.wait_for(timeout=180000)
    pg.wait_for_timeout(2000)
    panel = pg.get_by_role("heading", name="Läsning och luckor").first.locator("..").locator("..")
    shot(panel, "08_lasning.png")
    btn = pg.get_by_role("button", name="Ange vad som syns · skannern har ett förslag")
    if not btn.count():
        btn = pg.get_by_role("button", name="Ange vad som syns")
    btn.first.click()
    pg.wait_for_timeout(1500)
    shot(panel, "09_lucka_oppen.png")
    scan = pg.get_by_text("Vad skannern ser i luckan")
    if scan.count():
        shot(scan.first.locator("..").locator(".."), "10_skannern.png")
    b.close()
print("klart")
