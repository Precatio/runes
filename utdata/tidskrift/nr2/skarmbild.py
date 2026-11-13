"""Skärmbilder till Korpus nr 2, sidan "I appen: Luckor i texten" (sv + en), ur den lokala appen på :3000.

Språket sätts med localStorage-nyckeln vitki_lang före laddningen (som för nr 1). Hela bilden sparas som
bilder/app_luckor_<sv|en>_hel.png (inte i git) och ett beskuret utsnitt som bilder/app_luckor_<sv|en>.jpg.
    .venv/bin/python utdata/tidskrift/nr2/skarmbild.py
"""
import os
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
BILDER = os.path.join(HERE, "..", "bilder")
URL = "http://127.0.0.1:3000/luckor"
FLIK = {"sv": "Luckor i texten", "en": "Gaps in the text"}


def main():
    os.makedirs(BILDER, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", args=["--in-process-gpu"])
        for sprak in ("sv", "en"):
            ctx = b.new_context(viewport={"width": 1440, "height": 1100}, device_scale_factor=2)
            ctx.add_init_script(f"try {{ localStorage.setItem('vitki_lang', '{sprak}') }} catch (e) {{}}")
            pg = ctx.new_page()
            pg.goto(URL, wait_until="networkidle", timeout=120000)
            flik = pg.get_by_role("button", name=FLIK[sprak]).or_(pg.get_by_role("tab", name=FLIK[sprak])).first
            flik.click()
            pg.wait_for_timeout(4000)
            # listan med luckor: scrolla så att förklaringen står överst, och beskär bort sidomenyn
            pg.locator("select").last.evaluate("e => e.scrollIntoView({block: 'start'})")  # sidan scrollar i en inre ruta
            pg.wait_for_timeout(1500)
            hel = os.path.join(BILDER, f"app_luckor_{sprak}_hel.png")
            pg.screenshot(path=hel, full_page=False)
            im = Image.open(hel).convert("RGB")
            w, h = im.size
            # utan sidomenyn, sökfältet upptill och den avklippta kolumnen längst till höger; de tio första raderna
            im.crop((int(w * 0.2), int(h * 0.075), int(w * 0.905), int(h * 0.68))).save(os.path.join(BILDER, f"app_luckor_{sprak}.jpg"), quality=88)
            print(sprak, hel, im.size)
            ctx.close()
        b.close()


if __name__ == "__main__":
    sys.exit(main())
