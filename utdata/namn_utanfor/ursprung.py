"""Steg 2 i analysplaner/2026-10-30-namnen-utanfor-runstenarna.md: vilka av Wiktionarys svenska förnamn som är
fornnordiska, ur etymologierna i wiktionary_namn.json (sv) och wiktionary_en_namn.json (en). Regel: fornnordiskt när
etymologin bara härleder genom nordiska och fornnordiska led (non, gmq-*, is, nordiska nutidsspråk, urgermanska) och
inget annat språk; blandat när båda finns (granskas för hand i GRANSKNING); främmande när bara annat språk finns.
Skriver ursprung.csv.
    .venv/bin/python utdata/namn_utanfor/ursprung.py"""
import csv
import json
import os
import re

OUT = os.path.dirname(os.path.abspath(__file__))
SV = json.load(open(os.path.join(OUT, "wiktionary_namn.json"), encoding="utf-8"))
EN = json.load(open(os.path.join(OUT, "wiktionary_en_namn.json"), encoding="utf-8"))
# Third source (deviation before results): Swedish Wikipedia's name article, for names without etymology in Wiktionary
WP = json.load(open(os.path.join(OUT, "wikipedia_namn.json"), encoding="utf-8")) if os.path.exists(
    os.path.join(OUT, "wikipedia_namn.json")) else {}
WPN = json.load(open(os.path.join(OUT, "wikipedia_myt.json"), encoding="utf-8")) if os.path.exists(
    os.path.join(OUT, "wikipedia_myt.json")) else {}
NORDIC = {"non", "gmq-osw", "gmq-fsv", "gmq-oda", "gmq-ogu", "gmq-osw-run", "gmq-pro", "is", "no", "nb", "nn", "da", "fo",
          "sv", "gem-pro", "gem-ugm", "gem-uno", "gmq-oda-run", "gmq-bot"}
DERIV = re.compile(r"\{\{(?:inh|der|bor|lbor|uder|härledning|ubor|slbor|translit)\|sv\|([a-zA-Z\-]+)\|")
WORD_N = re.compile(r"Old Norse|Old Swedish|Old Danish|Old Icelandic|Icelandic|Norse|runsvensk|fornnordisk|fornvästnordisk|"
                    r"fornsvensk|forndansk|fornisländsk|isländsk|nordiskt namn|nordisk|norrön|fornskandinavisk", re.I)
WORD_F = re.compile(r"Latin|Greek|Hebrew|Aramaic|German(?!ic)|French|English|Irish|Gaelic|Celtic|Russian|Finnish|Slavic|"
                    r"Arabic|Italian|Spanish|latin|grekisk|hebreisk|tysk|fransk|engelsk|irländsk|gaelisk|keltisk|ryska|"
                    r"rysk|finsk|slavisk|arabisk|italiensk|spansk|bibl")
MYTH = re.compile(r"gud|gudinna|Eddan|edda|mytolog|valkyr|jätte|asagud|\bgod\b|goddess|mytholog|Edda|valkyrie|giant|"
                  r"\bÆsir\b|\basar\b", re.I)
# Hand review of the mixed and code-less entries (2026-10-30): name -> (kod, skäl)
G_F, G_N, G_X = "främmande", "fornnordiskt", "blandat"
GRANSKNING = {
    # Wiktionary stops at Old Swedish, which borrowed many names
    "Johan": (G_F, "hebreiska Johannes via fornsvenska"), "Kristina": (G_F, "latin Christina via fornsvenska"),
    "Fredrik": (G_F, "tyska Friedrich via fornsvenska"), "Albrekt": (G_F, "tyska Albrecht via fornsvenska"),
    "Märta": (G_F, "Margareta via forndanska"), "Elin": (G_F, "grekiska Helena"), "Majvor": (G_F, "Maj (latin) + -vor, 1900-tal"),
    "Olga": (G_F, "Helga via ryska"), "Dan": (G_X, "Danr eller Daniel – tvetydigt"),
    "Alrik": (G_N, "fornnordiska Alfrekr (runsten Vg 119)"), "Erika": (G_N, "femininum av Erik"), "Frej": (G_N, "fornnordiska Freyr"),
    # Wikipedia hits that are not Old Norse names
    "Hedda": (G_F, "smekform av tyska Hedvig"), "Margit": (G_F, "kortform av Margareta"), "Moa": (G_F, "smekform av ordet mor, sent"),
    "Lillemor": (G_F, "nybildning 1900-tal"), "Nisse": (G_F, "smeknamn för Nils (Nikolaus)"), "Smilla": (G_F, "ur roman 1992"),
    "Maivor": (G_F, "Maj + -vor, 1910"), "Signhild": (G_F, "medeltida balladnamn Signil, annan historia"),
    "Birk": (G_F, "ortnamnsord, inte ett fornnordiskt personnamn"),
    # mixed in the Wikipedia text but Old Norse names
    "Alfrida": (G_N, "fornnordiska Alfridh"), "Alpha": (G_N, "femininum av Alf"), "Alva": (G_N, "fornnordiska alv"),
    "Frida": (G_N, "fornnordiska fridh"), "Hilda": (G_N, "fornnordiska hildr"), "Holger": (G_N, "Holmgeirr"),
    "Hulda": (G_N, "nordiska huld"), "Inge": (G_N, "fornnordiska Ingi"), "Love": (G_N, "runsvenska Lófi"),
    "Orvar": (G_N, "fornnordiska ǫrvar"), "Ove": (G_N, "fornnordiska Áfi, via danskan"), "Sven": (G_N, "fornnordiska Sveinn"),
    "Thore": (G_N, "fornnordiska Þórir"), "Calle": (G_N, "Karl"), "Kalle": (G_N, "Karl"),
}


def classify(etys):
    codes = [c for e in etys for c in DERIV.findall(e)]
    nordic = [c for c in codes if c in NORDIC]
    foreign = [c for c in codes if c not in NORDIC]
    text = " ".join(etys)
    if not codes:
        n, f = bool(WORD_N.search(text)), bool(WORD_F.search(text))
        return ("blandat" if n and f else "fornnordiskt" if n else "främmande" if f else "okänt"), "ord"
    if nordic and not foreign and any(c not in {"sv", "da", "no", "nb", "nn", "gem-pro", "gem-ugm", "gem-uno"} for c in nordic):
        return "fornnordiskt", "koder"
    if nordic and foreign:
        return "blandat", "koder"
    if foreign:
        return "främmande", "koder"
    return "okänt", "koder"


rows = []
for n in sorted(set(SV) | set(EN)):
    etys = (SV.get(n, {}).get("etymology") or []) + (EN.get(n, {}).get("etymology") or [])
    sex = sorted(set(SV.get(n, {}).get("sex", [])) | set(EN.get(n, {}).get("sex", [])))
    code, how = classify(etys)
    if code == "okänt" and n in WP:
        etys = ["[Wikipedia] " + WP[n]]
        code, how = classify(etys)
        how = "wikipedia"
    if n in GRANSKNING:
        code, how = GRANSKNING[n][0], "granskning: " + GRANSKNING[n][1]
    # myth: Wiktionary's etymology or the name article in Wikipedia (deviation before results: Embla, Vidar, Loke)
    myth_text = " ".join(etys) + " " + WP.get(n, "") + " " + WPN.get(n, "")
    rows.append({"namn": n, "kön": "/".join(sex), "ursprung": code, "grund": how, "myt": int(bool(MYTH.search(myth_text))),
                 "etymologi": " || ".join(re.sub(r"\s+", " ", e)[:400] for e in etys)})
with open(os.path.join(OUT, "ursprung.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
from collections import Counter  # noqa: E402
print(len(rows), Counter(r["ursprung"] for r in rows))
