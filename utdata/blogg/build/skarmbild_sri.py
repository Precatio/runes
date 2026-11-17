"""Skärmbilder av rutan "Fyndhistorik enligt Sveriges runinskrifter" på stensidan i den lokala appen (:3000), på svenska
och engelska, till artiklar och Korpus. Bilderna sparas i utdata/blogg/bilder/sri_<signum>_<sv|en>.png (inte i git).
    .venv/bin/python utdata/blogg/build/skarmbild_sri.py "Vg 130" "Nä 8"
"""
import os
import re
import sys
import urllib.parse

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "bilder")
LABEL = {"sv": "Fyndhistorik enligt", "en": "Find history according to"}


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
                lab = pg.get_by_text(re.compile("Fyndhistorik enligt|Find history according to")).first
                lab.wait_for(timeout=60000)
                pg.wait_for_timeout(1500)
                box = lab.locator("xpath=../..")
                box.scroll_into_view_if_needed()
                path = os.path.join(OUT, f"sri_{s.replace(' ', '_')}_{lang}.png")
                box.screenshot(path=path)
                print(lang, s, path)
            ctx.close()
        b.close()


if __name__ == "__main__":
    main(sys.argv[1:] or ["Vg 130"])
