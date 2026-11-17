"""Skärmbild av "Pröva en egen fråga" (Statistik, components/OwnQuestion.tsx) med en körd fråga, i den lokala appen
(:3000), på svenska och engelska. Bilderna sparas i utdata/blogg/bilder/egen_fraga_<a>_<key>_<sv|en>.png (inte i git).
    .venv/bin/python utdata/blogg/build/skarmbild_egen_fraga.py stungna tid 1050
"""
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "bilder")


def main(a: str, kind: str, key: str):
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", args=["--in-process-gpu"])
        for lang in ("sv", "en"):
            ctx = b.new_context(viewport={"width": 1280, "height": 1800}, device_scale_factor=2)
            ctx.add_init_script(f"try {{ localStorage.setItem('vitki_lang', '{lang}'); sessionStorage.clear() }} catch (e) {{}}")
            pg = ctx.new_page()
            pg.goto("http://127.0.0.1:3000/statistik#egen-fraga", wait_until="networkidle", timeout=120000)
            box = pg.locator("#egen-fraga")
            if not box.count():
                pg.get_by_text("Pröva en egen fråga").first.click()
            box.wait_for(timeout=60000)
            sel = box.locator("select")
            sel.nth(0).select_option(a)
            sel.nth(1).select_option(kind)
            sel.nth(2).select_option(key)
            box.locator("button").first.click()
            pg.wait_for_timeout(1000)
            box.locator("button", has_text="Pröva" if lang == "sv" else "").first.wait_for(timeout=120000)
            pg.wait_for_function("() => !document.querySelector('#egen-fraga button[disabled]')", timeout=180000)
            pg.wait_for_timeout(2500)
            box.scroll_into_view_if_needed()
            path = os.path.join(OUT, f"egen_fraga_{a}_{key}_{lang}.png")
            # Only the question, the answer and the two cards (not the note field and the list of the visit's questions)
            top = box.bounding_box()
            stop = box.locator("input, textarea").first.bounding_box()
            clip = {"x": top["x"], "y": top["y"], "width": top["width"], "height": stop["y"] - top["y"] - 40}
            pg.screenshot(path=path, clip=clip, full_page=True)
            print(lang, path)
            ctx.close()
        b.close()


if __name__ == "__main__":
    main(*(sys.argv[1:4] if len(sys.argv) >= 4 else ("stungna", "tid", "1050")))
