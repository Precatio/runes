"""Skärmbilder och mätfiler till "Så gör du"-artikeln om att mäta bara runorna (groove-7: runslingorna, runorna
indelade längs slingan, Markera runorna och bilden Runor och ornamentik): appen körs i en huvudlös Chrome mot de lokala
servrarna (web :3000, api :8000), skanningen laddas upp och den automatiska analysen körs enligt Vitki-protokollet,
precis som en användare gör det.

Fyra omgångar:
  0. --startvy: analysen körs från sidans startvy, utan att stenen vrids (analys_startvy.json).
  1. svenska: analysen efter knappen Vänd ristade sidan mot mig (analys.json); slutar efter granskningsbilden
     eftersom klick.json saknas. Sedan räknar howto_runor_klick.py klicken ur de granskade runslingorna (klick.json).
  2. svenska: samma analys, runorna som resultat med appens egen indelning (resultat_auto.json), klicken
     (resultat.json) och bilden Runor och ornamentik (band_bild.json).
  3. --lang en: samma sak på engelska; filerna får ändelsen _en.
Språket sätts med localStorage-nyckeln vitki_lang före laddningen.
    PLAYWRIGHT_BROWSERS_PATH=/Volumes/2TB/cache/ms-playwright .venv/bin/python utdata/blogg/build/howto_runor_bilder.py \
        SKANNING.stl [--lang sv|en] [--startvy]
"""
import base64
import json
import os
import re
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "utdata", "blogg", "howto_runor")
os.makedirs(OUT, exist_ok=True)
SCAN = sys.argv[1]
LANG = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "sv"
STARTVY = "--startvy" in sys.argv
SFX = "" if LANG == "sv" else "_" + LANG
ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
CATALOG = json.load(open(os.path.join(ROOT, "web", "src", "i18n", "en.json"), encoding="utf-8"))


def T(sv: str, exact: bool = True) -> re.Pattern:
    """The Swedish text or, on the English page, its translation in the app's catalog (the page leaves texts the
    catalog lacks in Swedish, so both are accepted)."""
    alts = {sv, CATALOG.get(sv, sv)} if LANG == "en" else {sv}
    body = "|".join(re.escape(a) for a in alts)
    return re.compile(rf"^\s*(?:{body})\s*$" if exact else f"(?:{body})")


def fil(name: str) -> str:
    stem, ext = os.path.splitext(name)
    return os.path.join(OUT, stem + SFX + ext)


def shot(loc, name):
    loc.scroll_into_view_if_needed()
    loc.page.wait_for_timeout(800)
    try:
        loc.screenshot(path=fil(name), timeout=120000)
    except Exception:  # an element that never settles: the window cut to its box (the window is tall enough, below)
        loc.page.screenshot(path=fil(name), clip=loc.bounding_box())
    print("sparade", os.path.basename(fil(name)), flush=True)


def keep(data: dict) -> dict:
    """What the article needs from the analysis's answer (not the image or the profiles)."""
    return {**{k: data.get(k) for k in ("counts", "parameters", "bands", "provenance", "groove_map_scale",
                                        "image_width", "image_height", "runes")},
            "slices": [{k: s.get(k) for k in ("accepted", "feature", "band", "img_x", "img_y", "rune_id")}
                       for s in data["slices"]]}


def run_analysis(pg):
    knapp = pg.get_by_role("button", name=T("Kör automatisk analys"))
    for _ in range(60):
        if knapp.is_enabled():
            break
        pg.wait_for_timeout(5000)
    t0 = time.time()
    with pg.expect_response(lambda r: "auto_analyze" in r.url, timeout=20 * 60 * 1000) as resp:
        knapp.click(timeout=120000)
    data = resp.value.json()
    print("analys klar efter", round(time.time() - t0), "s:", data["counts"]["accepted"], "godkända snitt", flush=True)
    return data


with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS, channel="chrome")
    pg = b.new_page(viewport={"width": 1440, "height": 2600}, device_scale_factor=1.5)  # tall: the side panel fits whole  # 2 starves the software-rendered 3D view
    pg.add_init_script(f"try {{ localStorage.setItem('vitki_lang', '{LANG}'); }} catch (e) {{}}")
    pg.set_default_timeout(180000)  # the 3D view renders in software and keeps the page busy
    pg.on("pageerror", lambda e: print("SIDFEL:", e, flush=True))
    pg.on("console", lambda m: m.type == "error" and print("KONSOL:", m.text[:300], flush=True))
    pg.on("crash", lambda _: print("SIDAN KRASCHADE", flush=True))
    pg.goto("http://localhost:3000/3d", wait_until="networkidle", timeout=90000)
    pg.wait_for_timeout(2000)
    pg.set_input_files("input[type=file]", SCAN)
    auto = pg.get_by_role("button", name=T("Automatiskt"))
    auto.wait_for(timeout=180000)
    for _ in range(90):  # the model is loaded when the run button can be pressed in automatic mode
        pg.wait_for_timeout(5000)
        status = pg.get_by_text(T("Status")).first.locator("..").inner_text()
        if re.search(r"inläst|loaded", status):
            break
    print("status:", status.replace("\n", " ")[:200], flush=True)
    pg.wait_for_timeout(3000)
    auto.click()
    pg.wait_for_timeout(1000)
    panel = pg.get_by_text(T("Vad ska mätas?")).locator("..").locator("..")
    shot(panel, "01_vad_ska_matas.png")

    view3d = pg.get_by_text(re.compile(r"Dra: rotera|Drag: rotate")).first.locator("..").locator("..")
    if STARTVY:  # the page's starting view, as a user who does not turn the stone sees it
        pg.wait_for_timeout(3000)
        shot(view3d, "01a_startvy.png")
        json.dump(keep(run_analysis(pg)), open(os.path.join(OUT, "analys_startvy.json"), "w"), ensure_ascii=False, indent=1)
        # the page now draws every measured point in the software-rendered 3D view and has no frames to spare, so
        # the run with the button starts afresh
        b.close()
        print("startvyn klar; kör skriptet igen utan --startvy")
        sys.exit(0)

    pg.get_by_role("button", name=T("Vänd ristade sidan mot mig")).dispatch_event("click")  # needs no free frames
    pg.wait_for_timeout(4000)
    shot(view3d, "01b_vy.png")
    # the later pictures do not show the 3D view, which renders in software on every frame; it is hidden (the view
    # direction for the analysis is already taken), else the page gets no frames to spare for the review
    pg.add_style_tag(content="canvas { display: none !important; }")
    data = run_analysis(pg)
    # the view direction has been sent: release the 3D view's WebGL context so that the software renderer stops
    pg.evaluate("""() => document.querySelectorAll('canvas').forEach(c => {
        const gl = c.getContext('webgl2') || c.getContext('webgl');
        gl && gl.getExtension('WEBGL_lose_context') && gl.getExtension('WEBGL_lose_context').loseContext(); })""")
    # a window tall enough for the whole review card, so that no picture depends on the app's inner scrolling
    pg.set_viewport_size({"width": 1440, "height": 2600})
    json.dump(keep(data), open(fil("analys.json"), "w"), ensure_ascii=False, indent=1)
    with open(fil("granskningsbild.png"), "wb") as fh:
        fh.write(base64.b64decode(data["image_base64"].split(",", 1)[1]))
    review_head = pg.get_by_text(T("Granska den automatiska analysen"))
    review_head.wait_for(timeout=5 * 60 * 1000)
    pg.wait_for_timeout(3000)
    shot(pg.locator("p[role=status]").first, "02_status_slingor.png")
    review = review_head.locator("..").locator("..").locator("..")
    shot(review, "03_granskning.png")
    print("granskning:", review.locator("p").first.inner_text()[:300], flush=True)

    klick = os.path.join(OUT, "klick.json")
    if not os.path.exists(klick):
        b.close()
        print("omgång 1 klar; kör howto_runor_klick.py och sedan det här skriptet igen")
        sys.exit(0)

    # the runes as the unit with the app's own division along the band (no marks)
    use = pg.get_by_role("button", name=T("Använd runorna som resultat"))
    with pg.expect_response(lambda r: "stats/summarize" in r.url) as summ:
        use.click()
    json.dump(summ.value.json(), open(fil("resultat_auto.json"), "w"), ensure_ascii=False, indent=1)
    unit = pg.get_by_text(T("Med runan som enhet")).first.locator("..")
    unit.wait_for(timeout=120000)
    pg.wait_for_timeout(2500)
    shot(unit, "06_runan_auto.png")

    # one click per rune
    clicks = json.load(open(klick, encoding="utf-8"))
    svg = review.locator("svg").first
    vb = [float(v) for v in svg.get_attribute("viewBox").split()]
    print(len(clicks), "klick", flush=True)
    pg.get_by_role("button", name=T("Markera runorna")).click()
    pg.wait_for_timeout(500)
    for x, y in clicks:  # each point scrolled into the window before the click
        box = svg.bounding_box()
        sy = box["y"] + y / vb[3] * box["height"]
        if not 80 < sy < 2400:
            pg.mouse.wheel(0, sy - 1300)
            pg.wait_for_timeout(400)
            box = svg.bounding_box()
        pg.mouse.click(box["x"] + x / vb[2] * box["width"], box["y"] + y / vb[3] * box["height"])
        pg.wait_for_timeout(150)
    pg.wait_for_timeout(1000)
    shot(review, "04_markerade.png")
    shot(pg.get_by_text(T("Markera runorna.")).first.locator("..").locator(".."), "05_markera_ruta.png")
    pg.get_by_role("button", name=T("Klar med runorna")).click()
    with pg.expect_response(lambda r: "stats/summarize" in r.url) as summ:
        use.click()
    json.dump(summ.value.json(), open(fil("resultat.json"), "w"), ensure_ascii=False, indent=1)
    pg.wait_for_timeout(3000)
    shot(pg.get_by_text(T("Med runan som enhet")).first.locator(".."), "07_runan_som_enhet.png")

    # Runor och ornamentik: the depth image coloured by the text bands, from the same view every time (the default)
    pg.set_viewport_size({"width": 1440, "height": 2600})  # the whole dialog, picture included
    with pg.expect_response(lambda r: "band_image" in r.url, timeout=10 * 60 * 1000) as bi:
        pg.get_by_role("button", name=T("Runor och ornamentik – se textslingorna")).click()
    bd = bi.value.json()
    json.dump({k: v for k, v in bd.items() if k != "image"}, open(fil("band_bild.json"), "w"), ensure_ascii=False, indent=1)
    dialog = pg.get_by_role("dialog")
    dialog.wait_for()
    pg.wait_for_timeout(3000)
    shot(dialog.locator("> div"), "08_runor_ornamentik.png")
    if LANG != "sv":  # texts the page left in Swedish (the catalog lacks them), for web/src/i18n/en.json
        misses = pg.evaluate("() => (window.__vitkiI18n || {}).misses || {}")
        json.dump(misses, open(fil("saknade_oversattningar.json"), "w"), ensure_ascii=False, indent=1)
        print(len(misses), "texter utan översättning", flush=True)
    b.close()
print("klart")
