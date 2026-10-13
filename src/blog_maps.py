"""Bilder i stället för länkar in i appen. Den publika webbplatsen har bara startsidan och artiklarna – appen körs lokalt
och laddas ner från GitHub – så en artikel visar kartverktygets bild i stället för att länka till kartan (r/blogfig.R):

- tidskartan: kartverktygets vy "före och efter omkring 1050", andelen stenar med mönstret per sexkant
- punktkartan: de få stenarna med ett sällsynt mönster, var för sig
- kurvorna: förändringsmodellens kurvor för de drag artikeln handlar om

Varje bild ritas på svenska och engelska och fryses under sin innehållshash (src/blog_figures.py), så att artikeln
behåller den när analysen räknas om.
"""
from __future__ import annotations

import os
import re
import tempfile

from src import blog_figures
from src import r_bridge as rb

GITHUB = "https://github.com/Precatio/runes"
METHODS = f"{GITHUB}/blob/main/METHODS.md"


def _render(kind: str, params: dict) -> dict[str, str] | None:
    """Ritar en figur på båda språken och fryser den: {"sv": url, "en": url}, eller None om R saknas eller misslyckas."""
    if not rb.enabled():
        return None
    with tempfile.TemporaryDirectory(prefix="blogfig-") as out:
        try:
            files = rb.run_module("blogfig", {"kind": kind, "langs": ["sv", "en"], "water_dir": rb.ensure_water(),
                                              **params}, out, timeout=600)
        except (rb.RError, OSError, TimeoutError):
            return None
        urls = {}
        for lang in ("sv", "en"):
            name = files.get(lang)
            if not name:
                return None
            with open(os.path.join(out, name), "rb") as fh:
                urls[lang] = blog_figures.freeze(fh.read())
        return urls


def time_map(corpus_csv: str, key: str, label: str, label_en: str, split: int = 1050) -> dict | None:
    urls = _render("timemap", {"corpus": corpus_csv, "key": key, "label": label, "label_en": label_en, "split": split,
                               "hex_km": 20, "min_stones": 5, "name": f"tidskarta_{key}"})
    if not urls:
        return None
    return {"url": urls["sv"], "url_en": urls["en"],
            "label": f"{label} på Vitkis mönsterkarta, före och efter omkring {split}",
            "label_en": f"{label_en} on Vitki's pattern map, before and after about {split}",
            "source": "Vitkis mönsterkarta (r/blogfig.R); Samnordisk runtextdatabas (ODbL)",
            "source_en": "Vitki's pattern map (r/blogfig.R); Scandinavian Runic-text Data Base (ODbL)"}


def points_map(corpus_csv: str, key: str, label: str, label_en: str, exclude: list[str] | None = None) -> dict | None:
    urls = _render("points", {"corpus": corpus_csv, "key": key, "label": label, "label_en": label_en,
                              "exclude": exclude or [], "name": f"punkter_{key}"})
    if not urls:
        return None
    return {"url": urls["sv"], "url_en": urls["en"], "label": f"{label} på Vitkis mönsterkarta",
            "label_en": f"{label_en} on Vitki's pattern map",
            "source": "Vitkis mönsterkarta (r/blogfig.R); Samnordisk runtextdatabas (ODbL)",
            "source_en": "Vitki's pattern map (r/blogfig.R); Scandinavian Runic-text Data Base (ODbL)"}


def curves(change_json: str, keys: list[str], labels: list[str], labels_en: list[str]) -> dict | None:
    urls = _render("curves", {"change": change_json, "keys": keys, "labels": labels, "labels_en": labels_en,
                              "name": "kurvor_" + "_".join(keys)})
    if not urls:
        return None
    join = lambda xs, och: ", ".join(xs[:-1]) + f" {och} " + xs[-1] if len(xs) > 1 else xs[0]  # noqa: E731
    return {"url": urls["sv"], "url_en": urls["en"],
            "label": f"Förändringsmodellens kurvor: {join([x.lower() for x in labels], 'och')}",
            "label_en": f"The change model's curves: {join([_lower_en(x) for x in labels_en], 'and')}",
            "source": "Vitkis korpusanalys i R (change.R); Samnordisk runtextdatabas (ODbL)",
            "source_en": "Vitki's corpus analysis in R (change.R); Scandinavian Runic-text Data Base (ODbL)"}


def _lower_en(label: str) -> str:
    """"Cross" → "cross", but "Christian prayer" keeps its capital."""
    return label if re.match(r"^(Christian|Thor|Odin)\b", label) else label[:1].lower() + label[1:]


def markdown(fig: dict, lang: str = "sv") -> str:
    """Figuren som block i en artikel (components/BlogBody.tsx): bilden och bildtexten med källan."""
    if lang == "en":
        return f"![{fig['label_en']}]({fig['url_en']})\n{fig['label_en']}. Source: {fig['source_en']}."
    return f"![{fig['label']}]({fig['url']})\n{fig['label']}. Källa: {fig['source']}."


def github_note(lang: str = "sv") -> str:
    """Var läsaren kan göra om analysen: appen finns på GitHub, inte på webbplatsen."""
    if lang == "en":
        return (f"The maps, curves and models come from Vitki, an open tool for runestone research that you can download "
                f"and run on your own computer from [GitHub]({GITHUB}). The method is described in [METHODS.md]({METHODS}).")
    return (f"Kartorna, kurvorna och modellerna kommer från Vitki, ett öppet verktyg för runstensforskning som du kan "
            f"ladda ner och köra på din egen dator från [GitHub]({GITHUB}). Metoden beskrivs i [METHODS.md]({METHODS}).")
