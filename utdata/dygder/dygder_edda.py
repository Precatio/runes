"""Värdeorden i Eddadikterna: hur ofta ord för vänskap, gåvor, förstånd, ord och tystnad, måtta, gästfrihet, rykte,
mod och strid samt hämnd står i dikterna, per 1 000 ord, i fyra grupper: Hávamál, de övriga gudadikterna,
hjältedikterna och de kristna dikterna (Hugsvinnsmál, Sólarljóð). Snorres prosa (Gylfaginning, Skáldskaparmál) är
inte med. Texterna är de normaliserade fornisländska texterna från Hávamálartikeln (utdata/Edda/edda_karta_texter.csv).

Ordlistorna matchar hela ord (ordets början där det står \\w*) och är satta före räkningen. Mod och strid räknas både
som egenskap (frœkn, djarfr, hugaðr) och som strid (víg, vápn, sverð, orrosta, hildr).
    .venv/bin/python utdata/dygder/dygder_edda.py
"""
import csv
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(__file__)
csv.field_size_limit(10 ** 9)
TEXTER = {r["namn"]: r["text"] for r in csv.DictReader(open(os.path.join(HERE, "..", "Edda", "edda_karta_texter.csv")))}

GRUPP = {
    "Hávamál": ["Hávamál_gnomisk", "Hávamál_kvinnoråd_Gunnlöd", "Hávamál_Loddfáfnismál", "Hávamál_Runatal_Ljóðatal"],
    "gudadikter": ["Völuspá", "Grímnismál", "Vafþrúðnismál", "Alvíssmál", "Fjölsvinnsmál", "Skírnismál", "Lokasenna",
                   "Hárbarðsljóð", "Hymiskviða", "Þrymskviða", "Hyndluljóð", "Rígsþula", "Sigrdrífumál"],
    "hjältedikter": ["Atlakviða", "Atlamál_in_grænlenzku", "Guðrúnarkviða_in_forna", "Guðrúnarkviða_in_fyrsta",
                     "Hamðismál", "Helgakviða_Hjörvarðssonar", "Helgakviða_Hundingsbana_I", "Völsungakviða_in_forna",
                     "Sigurðarkviða_in_meiri", "Sigurðarkviða_in_skamma", "Grípisspá", "Oddrúnarkviða", "Reginsmál",
                     "Fáfnismál", "Völundarkviða", "Hlöðskviða", "Hervararkviða", "Hálfsrekkaljóð", "Eddubrot"],
    "kristna": ["Hugsvinnsmál", "Sólarljóð"],
}

ORD = {
    "vänskap": r"vin(r|ar|i|a|um|ir)?|vinátt\w*|vinskap\w*|trygg\w*|félag\w*",
    # (inte gjaforð 'giftermål' eller namn som Gjaflaug)
    "gåvor_givmildhet": r"gjöf|gjöfum|gjafa|gjafar|gjafir|gjöfull|gefa|gefr|gaf|gefit|gefendr|\w+gefendr"
                        r"|mild(r|ir|an|astr|ari)?|örlát\w*",
    # (inte bara 'vit': det kan vara pronomenet 'vi två')
    "förstånd": r"vits|mannvit\w*|snot(r|rir|rum|rs|ran|ra)|ósnot\w*|horsk\w*|fróð\w*|spak\w*|svinn\w*|ósvinn\w*"
                r"|ósvið\w*|heimsk\w*|vitr\w*",
    "ord_och_tystnad": r"orð|orða|orðum|orðs|mæla|mælir|mælti|mæltu|þegja|þegir|þagði|þagðak|þögull|tunga|tungu",
    # (inte hóf/hófu 'lyfte', hófgullinna/hófvarpnir 'hov')
    "måtta": r"hófi|hófs|ofdrykkj\w*|ofrölvi|meðalsnot\w*|ofvar\w*",
    "gästfrihet": r"gest(r|s|i|a|ir|um)?|gesti|verðar|kynnis",
    "rykte": r"orðstír\w*|lof|lofs|frægð\w*|frama|dómr",
    "mod": r"frœkn\w*|frækn\w*|djarf\w*|vígdjarf\w*|hugað\w*|hvat(r|an|ir|astr)|ósnjall\w*",
    "strid": r"víg|vígs|vígi|vápn\w*|sverð\w*|mæki\w*|orrost\w*|hild(i|ar)?|folkvíg\w*|bardag\w*",  # (inte gunnar: namnet Gunnarr)
    "hämnd": r"hefn\w*|hefnd\w*|bróðurbani\w*",
}
RX = {k: re.compile(rf"^(?:{v})$") for k, v in ORD.items()}


def tokens(t):
    return re.findall(r"[a-záéíóúýþðæöœøǫ]+", t.lower())


ut = {"grupper": {}, "dikter": {}}
for g, namn in GRUPP.items():
    toks = [w for n in namn for w in tokens(TEXTER[n])]
    c = Counter()
    for w in toks:
        for k, rx in RX.items():
            if rx.match(w):
                c[k] += 1
    ut["grupper"][g] = {"n_ord": len(toks), **{k: round(1000 * c[k] / len(toks), 2) for k in ORD},
                        "antal": dict(c)}
    for n in namn:
        tk = tokens(TEXTER[n])
        cc = Counter(k for w in tk for k, rx in RX.items() if rx.match(w))
        ut["dikter"][n] = {"n_ord": len(tk), **{k: round(1000 * cc[k] / len(tk), 2) for k in ORD}}

json.dump(ut, open(os.path.join(HERE, "dygder_edda.json"), "w"), ensure_ascii=False, indent=1)
print(f"{'per 1000 ord':18}" + "".join(f"{g[:12]:>14}" for g in GRUPP))
print(f"{'antal ord':18}" + "".join(f"{ut['grupper'][g]['n_ord']:>14}" for g in GRUPP))
for k in ORD:
    print(f"{k:18}" + "".join(f"{ut['grupper'][g][k]:>14}" for g in GRUPP))
