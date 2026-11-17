"""Skärmbild av texten på stensidan (Inskrifter: translitterering, normalisering och översättning) i den lokala appen
(:3000), på svenska och engelska. Bilderna sparas i utdata/blogg/bilder/sten_<signum>_<sv|en>.png (inte i git).
    .venv/bin/python utdata/blogg/build/skarmbild_sten.py "U 1104"
"""
import os
import re
import sys
import urllib.parse

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "bilder")


def main(signa):
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", args=["--in-process-gpu"])
        for lang in ("sv", "en"):
            ctx = b.new_context(viewport={"width": 1280, "height": 1600}, device_scale_factor=2)
            ctx.add_init_script(f"try {{ localStorage.setItem('vitki_lang', '{lang}') }} catch (e) {{}}")
            pg = ctx.new_page()
            for s in signa:
                pg.goto("http://127.0.0.1:3000/inskrifter?signum=" + urllib.parse.quote(s), wait_until="networkidle", timeout=120000)
                lab = pg.get_by_text(re.compile(r"^(Translitterering|Transliteration)$")).first
                lab.wait_for(timeout=60000)
                pg.wait_for_timeout(1500)
                col = lab.locator("xpath=ancestor::div[contains(@class,'space-y-4')][1]")
                col.scroll_into_view_if_needed()
                # Down to the translation: the column's top to the bottom of the translation field
                top = col.bounding_box()
                tr = pg.get_by_text(re.compile(r"^(Översättning \(engelska\)|Translation \(English\))$")).first
                tb = tr.locator("xpath=..").bounding_box()
                clip = {"x": top["x"] - 16, "y": top["y"] - 16, "width": top["width"] + 32,
                        "height": tb["y"] + tb["height"] - top["y"] + 32}
                path = os.path.join(OUT, f"sten_{s.replace(' ', '_')}_{lang}.png")
                pg.screenshot(path=path, clip=clip)
                print(lang, s, path)
            ctx.close()
        b.close()


if __name__ == "__main__":
    main(sys.argv[1:] or ["U 1104"])
