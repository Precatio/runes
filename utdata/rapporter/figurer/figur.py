"""Gemensamt för rapportbyggarna: en figur ur rapportfigurer.py som bild i rapporten (blog_figures.freeze) och
ändringsloggen för en ny rapportversion (mallen: en ny version får en ändringslogg sist i rapporten)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures  # noqa: E402

FIG = json.load(open(os.path.join(HERE, "figurer.json"), encoding="utf-8"))


def bild(name: str, lang: str, caption: str) -> str:
    """Bilden och bildtexten; bildtexten slutar alltid med vem som gjort bilden (Viktor 2026-11-01)."""
    assert "Vitki" in caption[-260:], "bildtexten ska säga att Vitki har gjort bilden"
    with open(os.path.join(HERE, f"{name}_{lang}.png"), "rb") as fh:
        url = blog_figures.freeze(fh.read())
    return f"![{caption.split('.')[0]}]({url})\n{caption}"


def andringslogg(lang: str, version: int, date: str, what_sv: str, what_en: str) -> str:
    if lang == "sv":
        return (f"## Ändringslogg\n\n- **Version {version}, {date}.** {what_sv} Inga siffror, tolkningar eller slutsatser är "
                "ändrade.")
    return (f"## Change log\n\n- **Version {version}, {date}.** {what_en} No numbers, interpretations or conclusions have "
            "changed.")
