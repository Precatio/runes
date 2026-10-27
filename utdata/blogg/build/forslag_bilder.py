"""Skärmbilder till artikeln om Vitkis ristarförslag för stenar utan ristare (build_forslag.py): Stenöversiktens diagram
över stenarna utan ristare, U 843:s panel med metodernas besked, topplistan och Statistiks ruta om "kanske någon annan". Tas ur den körande appen (localhost:3000 och :8000).
    PLAYWRIGHT_BROWSERS_PATH=/Volumes/2TB/cache/ms-playwright .venv/bin/python utdata/blogg/build/forslag_bilder.py
"""
import os

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "utdata", "blogg", "forslag")
os.makedirs(OUT, exist_ok=True)


def shot(loc, name):
    loc.scroll_into_view_if_needed()
    loc.page.wait_for_timeout(800)
    loc.screenshot(path=os.path.join(OUT, name))
    print("sparade", name)


with sync_playwright() as p:
    b = p.chromium.launch()
    # The app scrolls inside its own frame and its header floats over the page: a window tall enough for the whole
    # panel, and a clip from the panel's top down to the comparison section, keep the header out of the picture
    pg = b.new_page(viewport={"width": 1440, "height": 3200}, device_scale_factor=2)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))

    pg.goto("http://localhost:3000/oversikt?signum=U%20843", wait_until="networkidle", timeout=300000)
    pg.get_by_role("heading", name="Stenar utan ristare i Rundata").wait_for(timeout=300000)
    pg.wait_for_timeout(4000)
    shot(pg.get_by_role("heading", name="Stenar utan ristare i Rundata").locator(".."), "01_stenar_utan_ristare.png")

    panel = pg.get_by_role("heading", name="U 843", exact=True).locator("xpath=ancestor::div[contains(@class,'liquid-glass-island')][1]")
    panel.get_by_text("Tänkbara ristare").wait_for(timeout=120000)
    pg.wait_for_timeout(2500)
    box, cut = panel.bounding_box(), panel.get_by_text("Stenen jämförd med").bounding_box()
    pg.screenshot(path=os.path.join(OUT, "02_u843_panel.png"),
                  clip={"x": box["x"], "y": box["y"], "width": box["width"], "height": cut["y"] - box["y"] - 8})
    print("sparade 02_u843_panel.png")

    # The top of the list: only "nytt förslag" picked, the table sorted by strength, ten rows. A wide
    # window keeps each row on one line; the column "Metoder" (Rundata's carver's sources, 0 here) is left out
    wide = b.new_page(viewport={"width": 1920, "height": 1600}, device_scale_factor=2)
    wide.goto("http://localhost:3000/oversikt", wait_until="networkidle", timeout=300000)
    wide.get_by_role("heading", name="Stenar utan ristare i Rundata").wait_for(timeout=300000)
    wide.locator("button", has_text="nytt förslag").first.click()  # a click shows only that status
    wide.get_by_role("button", name="Visa som tabell").click()
    table = wide.locator("table").first
    table.wait_for(timeout=60000)
    wide.wait_for_timeout(1500)
    # The table lies below the app's own scrolling frame: an element screenshot, cut afterwards at the tenth row and at
    # the column "Metoder" (offsets from the table's corner do not change when it is scrolled into view)
    tb, last = table.bounding_box(), table.locator("tbody tr").nth(9).bounding_box()
    methods = table.locator("thead th").nth(5).bounding_box()
    w, h = methods["x"] - tb["x"], last["y"] + last["height"] - tb["y"] + 4
    path = os.path.join(OUT, "05_topplista.png")
    table.screenshot(path=path)
    Image.open(path).crop((0, 0, round(2 * w), round(2 * h))).save(path)
    print("sparade 05_topplista.png")

    pg.goto("http://localhost:3000/statistik", wait_until="networkidle", timeout=300000)
    pg.get_by_text("Kan statistiken föreslå vem som ristade en sten?").first.click()
    pg.wait_for_timeout(3000)
    shot(pg.get_by_role("heading", name="Kan modellen säga").first.locator(".."), "04_kanske_nagon_annan.png")

    print("fel:", errs)
    b.close()
