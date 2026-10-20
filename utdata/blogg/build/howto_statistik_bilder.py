"""Skärmbilder till "Så gör du"-artikeln om Statistik i R: översikten, en modul (Vem ristade?), Okända ristare med
täckningsvarningen, och Ordförrådet. Kräver att korpusanalyserna är beräknade för det aktuella fingeravtrycket.
    PLAYWRIGHT_BROWSERS_PATH=/Volumes/2TB/cache/ms-playwright .venv/bin/python utdata/blogg/build/howto_statistik_bilder.py
"""
import os

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "utdata", "blogg", "howto_statistik")
os.makedirs(OUT, exist_ok=True)


def shot(loc, name):
    loc.scroll_into_view_if_needed()
    loc.page.wait_for_timeout(600)
    loc.screenshot(path=os.path.join(OUT, name))
    print("sparade", name)


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=2)
    pg.goto("http://localhost:3000/statistik", wait_until="networkidle", timeout=180000)
    pg.get_by_text("Vem ristade?").first.wait_for(timeout=300000)
    pg.wait_for_timeout(3000)
    pg.screenshot(path=os.path.join(OUT, "01_oversikt.png"))

    def tab(label, name, extra=None):
        pg.get_by_text(label, exact=True).first.click()
        pg.wait_for_timeout(3000)
        pg.screenshot(path=os.path.join(OUT, name))
        print("sparade", name)
        if extra:
            extra()

    tab("Vem ristade?", "02_vem_ristade.png")
    det = pg.get_by_text("Kommer träffen från bergarten?")
    if det.count():
        det.first.click(); pg.wait_for_timeout(800)
        shot(det.first.locator("..").locator(".."), "03_bergart.png")
    tab("Okända ristare", "04_okanda.png")
    warn = pg.get_by_text("Prövat bara där ristare är kända.")
    if warn.count():
        shot(warn.first.locator(".."), "05_tackningsvarning.png")
    tbl = pg.locator("table").first
    if tbl.count():
        shot(tbl, "06_grupper_tabell.png")
    tab("Ordförrådet", "07_ordforradet.png")
    b.close()
print("klart")
