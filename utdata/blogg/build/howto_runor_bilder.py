"""Skärmbilder till "Så gör du"-artikeln om att mäta bara runorna (groove-6, runslingorna och Markera runorna): appen
körs i en huvudlös webbläsare mot de lokala servrarna (web :3000, api :8000), skanningen laddas upp, den automatiska
analysen körs enligt Vitki-protokollet och runorna markeras med ett klick var.

Två omgångar: den första sparar analysen (analys.json) och slutar efter granskningsbilden; howto_runor_klick.py räknar
klicken ur de granskade runslingorna (klick.json); den andra omgången gör samma analys och klickar dem.
    PLAYWRIGHT_BROWSERS_PATH=/Volumes/2TB/cache/ms-playwright .venv/bin/python utdata/blogg/build/howto_runor_bilder.py SKANNING.stl
"""
import base64
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "utdata", "blogg", "howto_runor")
os.makedirs(OUT, exist_ok=True)
SCAN = sys.argv[1]
ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]


def shot(loc, name):
    loc.scroll_into_view_if_needed()
    loc.page.wait_for_timeout(600)
    try:
        loc.screenshot(path=os.path.join(OUT, name), timeout=120000)
    except Exception:  # an element that never settles: the window cut to its box (the window is tall enough, below)
        loc.page.screenshot(path=os.path.join(OUT, name), clip=loc.bounding_box())
    print("sparade", name, flush=True)


with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    pg = b.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1.5)  # 2 starves the software-rendered 3D view
    pg.set_default_timeout(180000)  # the 3D view renders in software and keeps the page busy
    pg.on("pageerror", lambda e: print("SIDFEL:", e, flush=True))
    pg.on("console", lambda m: m.type == "error" and print("KONSOL:", m.text[:300], flush=True))
    pg.on("crash", lambda _: print("SIDAN KRASCHADE", flush=True))
    pg.goto("http://localhost:3000/3d", wait_until="networkidle", timeout=90000)
    pg.wait_for_timeout(1500)
    pg.set_input_files("input[type=file]", SCAN)
    pg.get_by_text("Automatiskt", exact=True).wait_for(timeout=120000)
    for _ in range(60):
        pg.wait_for_timeout(5000)
        if "inläst" in pg.locator("text=Status").first.locator("..").inner_text():
            break
    pg.wait_for_timeout(3000)
    pg.get_by_text("Automatiskt", exact=True).click()
    pg.wait_for_timeout(800)
    panel = pg.get_by_text("Vad ska mätas?", exact=True).locator("..").locator("..")
    shot(panel, "01_vad_ska_matas.png")
    pg.get_by_role("button", name="Vänd ristade sidan mot mig").dispatch_event("click")  # needs no free frames
    pg.wait_for_timeout(2500)
    shot(pg.get_by_text("Dra: rotera").locator("..").locator(".."), "01b_vy.png")
    # the 3D view renders in software on every frame; the later pictures do not show it, so it is hidden (the view
    # direction for the analysis is already taken), else the page gets no frames to spare for the review
    pg.add_style_tag(content="canvas { display: none !important; }")

    t0 = time.time()
    knapp = pg.get_by_role("button", name="Kör automatisk analys")
    for _ in range(60):
        if knapp.is_enabled():
            break
        pg.wait_for_timeout(5000)
    with pg.expect_response(lambda r: "auto_analyze" in r.url, timeout=20 * 60 * 1000) as resp:
        knapp.click(timeout=120000)
    data = resp.value.json()
    # the view direction has been sent: release the 3D view's WebGL context so that the software renderer stops
    pg.evaluate("""() => document.querySelectorAll('canvas').forEach(c => {
        const gl = c.getContext('webgl2') || c.getContext('webgl');
        gl && gl.getExtension('WEBGL_lose_context') && gl.getExtension('WEBGL_lose_context').loseContext(); })""")
    # a window tall enough for the whole review card, so that no picture depends on the app's inner scrolling
    pg.set_viewport_size({"width": 1440, "height": 2600})
    json.dump({**{k: data.get(k) for k in ("counts", "parameters", "bands", "provenance", "groove_map_scale",
                                           "image_width", "image_height")},
               "slices": [{k: s.get(k) for k in ("accepted", "feature", "band", "img_x", "img_y", "rune_id")} for s in data["slices"]]},
              open(os.path.join(OUT, "analys.json"), "w"), ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "granskningsbild.png"), "wb") as fh:
        fh.write(base64.b64decode(data["image_base64"].split(",", 1)[1]))
    try:
        pg.get_by_text("Granska den automatiska analysen").wait_for(timeout=5 * 60 * 1000)
    except Exception:
        pg.screenshot(path=os.path.join(OUT, "fel_sidan.png"), full_page=True, timeout=300000)
        print("ingen granskning; status:", pg.locator("text=Status").first.locator("..").inner_text()[:500], flush=True)
        raise
    print("analys klar efter", round(time.time() - t0), "s", flush=True)
    pg.wait_for_timeout(3000)
    shot(pg.locator("p[role=status]").first, "02_status_slingor.png")
    shot(panel, "02b_panel_efter.png")
    review = pg.get_by_text("Granska den automatiska analysen").locator("..").locator("..").locator("..")
    shot(review, "03_granskning.png")
    head = review.locator("p").first.inner_text()
    print("granskning:", head[:300], flush=True)

    # phase 1 ends here: the clicks are computed from the saved analysis (howto_runor_klick.py)
    klick = os.path.join(OUT, "klick.json")
    if not os.path.exists(klick):
        b.close()
        print("fas 1 klar; kör howto_runor_klick.py och sedan det här skriptet igen")
        sys.exit(0)
    clicks = json.load(open(klick, encoding="utf-8"))
    svg = review.locator("svg").first
    vb = [float(v) for v in svg.get_attribute("viewBox").split()]
    print(len(clicks), "klick", flush=True)

    pg.get_by_role("button", name="Markera runorna").click()
    pg.wait_for_timeout(500)
    for x, y in clicks:  # each point scrolled into the window before the click
        box = svg.bounding_box()
        sy = box["y"] + y / vb[3] * box["height"]
        if not 80 < sy < 1000:
            pg.mouse.wheel(0, sy - 550)
            pg.wait_for_timeout(400)
            box = svg.bounding_box()
        pg.mouse.click(box["x"] + x / vb[2] * box["width"], box["y"] + y / vb[3] * box["height"])
        pg.wait_for_timeout(150)
    pg.wait_for_timeout(1000)
    shot(review, "04_markerade.png")
    shot(pg.get_by_text("Markera runorna.", exact=True).locator("..").locator(".."), "05_markera_ruta.png")
    print("status:", pg.get_by_text("runor markerade").first.inner_text(), flush=True)
    pg.get_by_role("button", name="Klar med runorna").click()

    with pg.expect_response(lambda r: "stats/summarize" in r.url) as summ:
        pg.get_by_role("button", name="Använd runorna som resultat").click()
    json.dump(summ.value.json(), open(os.path.join(OUT, "resultat.json"), "w"), ensure_ascii=False, indent=1)
    pg.get_by_text("Huggteknik jämfört med mätkorpusen").wait_for(timeout=120000)
    pg.wait_for_timeout(2500)
    res = pg.get_by_text("Huggteknik jämfört med mätkorpusen").locator("..").locator("..").locator("..")
    shot(res.locator(".."), "06_resultat.png")
    shot(pg.get_by_text("Med runan som enhet", exact=True).locator(".."), "07_runan_som_enhet.png")
    b.close()
print("klart")
