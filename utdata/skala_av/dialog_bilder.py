"""Skärmbilder av dialogen Skala av vittringen till artikeln om funktionen: Sö 128 laddas upp i den lokala appen
(web :3000, api :8000), dialogen öppnas, och den största grå fläcken (ramslingan till vänster) görs till spår med det
nya klickläget. Bilderna sparas i utdata/skala_av/dialog/ (lokalt; artikeln fryser dem i bloggens bildarkiv).
    PLAYWRIGHT_BROWSERS_PATH=/Volumes/2TB/cache/ms-playwright .venv/bin/python utdata/skala_av/dialog_bilder.py [--en]"""
import base64
import io
import os
import re
import sys
import time

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "dialog")
os.makedirs(OUT, exist_ok=True)
SCAN = os.path.join(ROOT, "skanningar", "So 128_1_4 thin closed holes.stl")
ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist",
        "--in-process-gpu"]
EN = "--en" in sys.argv
T = ({"button": "Peel away the weathering – see the deep grooves", "dialog": "Peel away the weathering",
      "radio": "Click makes a groove", "hand": "by hand", "download": "Download the picture", "suffix": "_en"} if EN else
     {"button": "Skala av vittringen – se de djupa spåren", "dialog": "Skala av vittringen",
      "radio": "Klick gör till spår", "hand": "för hand", "download": "Ladda ned bilden", "suffix": ""})


def labels_of(body):
    im = np.array(Image.open(io.BytesIO(base64.b64decode(body["labels"].split(",", 1)[1]))).convert("RGB")).astype(np.int64)
    return im[..., 0] + 256 * im[..., 1] + 65536 * im[..., 2]


with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    pg = b.new_page(viewport={"width": 1500, "height": 1150}, device_scale_factor=1.5)
    pg.add_init_script(f"try {{ localStorage.setItem('vitki_lang', '{'en' if EN else 'sv'}'); }} catch (e) {{}}")
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto("http://localhost:3000/3d", wait_until="networkidle", timeout=120000)
    pg.set_input_files("input[type=file]", SCAN)
    btn = pg.get_by_role("button", name=T["button"])
    for _ in range(300):
        if btn.count() and btn.is_enabled():
            break
        time.sleep(1)
    with pg.expect_response(lambda r: "/api/3d/peel" in r.url, timeout=300000) as resp:
        btn.click()
    body = resp.value.json()
    dlg = pg.get_by_role("dialog", name=T["dialog"])
    canvas = dlg.locator("canvas")
    canvas.wait_for(state="visible", timeout=120000)
    time.sleep(1.5)
    panel = dlg.locator("xpath=./div")
    panel.screenshot(path=os.path.join(OUT, f"so128_fore{T['suffix']}.png"))
    t = dlg.inner_text().replace("\n", " ")
    print("före:", t[t.find(T["download"]):][:120])

    # the largest grey speck, and a pixel of it near its middle
    lab = labels_of(body)
    pits = sorted((c for c in body["components"] if c["kind"] == "grop"), key=lambda c: -c["area_mm2"])
    big = pits[0]
    rr, cc = np.nonzero(lab == big["id"])
    k = len(rr) // 2
    y, x = int(rr[k]), int(cc[k])
    print("största gropen:", big["area_mm2"], "mm², längd", big["length_mm"], "mm, bildpunkt", x, y)
    box = canvas.bounding_box()
    at = {"x": (x + 0.5) * box["width"] / body["width"], "y": (y + 0.5) * box["height"] / body["height"]}
    dlg.get_by_role("radio", name=T["radio"]).click()
    time.sleep(0.3)
    canvas.hover(position=at)
    time.sleep(0.5)
    t = dlg.inner_text().replace("\n", " ")
    print("under pekaren:", t[t.find("bortklickade"):][:120])
    canvas.click(position=at)
    time.sleep(1.0)
    pg.mouse.move(3, 3)
    time.sleep(0.5)
    txt = dlg.inner_text().replace("\n", " ")
    print("efter:", txt[txt.find("spår ("):][:200] if "spår (" in txt else txt[400:800])
    assert T["hand"] in txt, "fläcken blev inte spår"
    panel.screenshot(path=os.path.join(OUT, f"so128_efter{T['suffix']}.png"))
    # and it stays a groove when the slider moves
    slider = dlg.locator('input[type="range"]')
    slider.focus()
    pg.keyboard.press("ArrowRight")
    time.sleep(5)
    t = dlg.inner_text().replace("\n", " ")
    print("reglaget +0,1 mm:", t[t.find(T["download"]):][:120])
    assert T["hand"] in t, "markeringen följde inte med reglaget"
    print("sidfel:", errs)
    b.close()
