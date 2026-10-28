"""Upptäcktsmotorn, version 1: stenarnas drag som en matris för parskanningen i r/discovery.R, enligt den låsta planen
analysplaner/2026-10-28-upptacktsmotorn.md. En rad per svensk vikingatida runsten med minst fyra läsbara ord; varje drag
är 1, 0 eller tomt (går inte att avgöra). Dragen läses ur korpusberäkningens filer (corpus.csv, messages.csv,
people.csv, remains_stones.csv, geography_stones.csv) och stenarnas mått (data/stone_dimensions.json).

FAMILY anger vilka drag som hänger ihop genom hur de är definierade: par inom samma familj prövas inte."""
from __future__ import annotations

import csv
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_WORDS = 4
TALL_M = 1.6  # medianhöjden bland mätta hela stenar (planen)
NEAR_KM = 0.5
WATER_KM = 1.0
DIVIDERS = ("punkt", "kryss", "kolon", "apostrof", "plus", "blandat")

FAMILY = {
    "cat_kristen": "kristen", "pm_kors": "kristen", "pm_bon": "kristen", "pm_sjal": "kristen",
    "pm_stungna": "stungna", "stungen_e": "stungna", "stungen_y": "stungna", "stungen_g": "stungna",
    "cat_sjalvminne": "egen",
    "cat_fard": "resa", "msg_resa": "resa", "msg_dod_borta": "resa", "msg_dod_uppgift": "resa", "msg_gald": "resa",
    "cat_arv": "arv", "msg_gard": "arv",
    "pm_signatur": "ristare", "has_carver": "ristare",
    "msg_berom": "berom", "drengr": "berom", "thegn": "berom", "god": "berom",
    "kvinna_resare": "resare", "kvinna_ensam": "resare", "flera_resare": "resare",
    "pm_hednisk": "hednisk", "cat_magisk": "hednisk",
    "cat_bro_vag": "bro", "cat_ting": "ting",
    "monoftong": "monoftong", "au_monoftong": "au", "o_runa": "o_runa", "r_for_R": "r", "nasal_utelamnad": "nasal",
    "h_saknas": "h", "prep_at": "prep", "bindrunor": "bindrunor", "short_twig": "kortkvist",
    "kvinna_dod": "dod_kvinna", "hog_sten": "monument",
}
for _k in DIVIDERS:
    FAMILY[f"skilj_{_k}"] = "skiljetecken"
for _k in ("barn", "foralder", "syskon", "make", "slakt", "ej_slakt"):
    FAMILY[f"rel_{_k}"] = "relation"
for _k in ("gravfalt", "hog", "vag", "bro", "fornborg", "church"):
    FAMILY[f"nara_{_k}"] = "landskap"
FAMILY["nara_vatten"] = "landskap"


def _read(path: str) -> dict[str, dict]:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return {r["signum"]: r for r in csv.DictReader(fh)}


def _num(v):
    try:
        x = float(v)
        return None if math.isnan(x) else x
    except (TypeError, ValueError):
        return None


def _bin(v):
    x = _num(v)
    return None if x is None else int(x > 0)


def _cat(v, yes: str, no: tuple[str, ...]):
    """En kategorisk trait som 1/0: 'båda' räknas som ja (draget förekommer)."""
    if v in (None, ""):
        return None
    return 1 if v in (yes, "båda") else 0 if v in no else None


def rows(corpus_dir: str) -> list[dict]:
    corpus = _read(os.path.join(corpus_dir, "corpus.csv"))
    msg = _read(os.path.join(corpus_dir, "messages.csv"))
    ppl = _read(os.path.join(corpus_dir, "people.csv"))
    rem = _read(os.path.join(corpus_dir, "remains_stones.csv"))
    geo = _read(os.path.join(corpus_dir, "geography_stones.csv"))
    dims = json.load(open(os.path.join(ROOT, "data", "stone_dimensions.json"), encoding="utf-8"))["stones"]
    out = []
    for s, c in corpus.items():
        words = _num(c.get("n_words_core"))
        if words is None or words < MIN_WORDS:
            continue
        m, p, r, g, dm = msg.get(s, {}), ppl.get(s, {}), rem.get(s, {}), geo.get(s, {}), dims.get(s, {})
        row = {"signum": s, "province": c["province"], "parish": c.get("parish") or "", "carver": c.get("carver") or "",
               "style_from": c.get("style_from") or "", "style_to": c.get("style_to") or "", "n_words": words}
        for k in ("cat_sjalvminne", "cat_bro_vag", "cat_kristen", "cat_fard", "cat_arv", "cat_ting", "cat_magisk",
                  "pm_hednisk", "pm_kors", "pm_bon", "pm_sjal", "pm_stungna", "pm_signatur", "has_carver"):
            row[k] = _bin(c.get(k))
        row["stungen_e"] = _cat(c.get("trait_stungen_e"), "ja", ("nej",))
        row["stungen_y"] = _cat(c.get("trait_stungen_y"), "ja", ("nej",))
        row["stungen_g"] = _cat(c.get("trait_stungen_g"), "ja", ("nej",))
        row["monoftong"] = _bin(c.get("pm_monoftong"))
        row["au_monoftong"] = _cat(c.get("trait_au_och"), "monoftong", ("auk",))
        row["o_runa"] = _bin(c.get("pm_o_runa"))
        row["r_for_R"] = _bin(c.get("pm_r_for_R"))
        row["nasal_utelamnad"] = _cat(c.get("trait_nasal"), "utelämnad", ("skriven",))
        row["h_saknas"] = _cat(c.get("trait_h_bortfall"), "h saknas", ("h skrivet",))
        row["prep_at"] = _cat(c.get("trait_preposition"), "at", ("æftiR",))
        row["bindrunor"] = _cat(c.get("trait_bindrunor"), "ja", ("nej",))
        row["short_twig"] = _bin(c.get("short_twig"))
        sk = c.get("trait_skiljetecken") or ""
        for k in DIVIDERS:
            row[f"skilj_{k}"] = int(sk == k) if sk else None
        for k in ("msg_dod_uppgift", "msg_dod_borta", "msg_resa", "msg_gald", "msg_gard", "msg_berom"):
            row[k] = _bin(m.get(k))
        if p and p.get("legible") == "1":
            nk, nm, nr = int(p["resare_k"]), int(p["resare_m"]), int(p["n_resare"])
            row["kvinna_resare"] = int(nk > 0) if nr else None
            row["kvinna_ensam"] = int(nk > 0 and nm == 0 and int(p["resare_okand"]) == 0) if nr else None
            row["flera_resare"] = int(nr >= 2) if nr else None
            row["kvinna_dod"] = int(int(p["doda_k"]) > 0) if int(p["n_doda"]) else None
            for k in ("barn", "foralder", "syskon", "make", "slakt", "ej_slakt"):
                row[f"rel_{k}"] = int(p[f"rel_{k}"]) if int(p["n_doda"]) else None
            for k in ("drengr", "thegn", "god"):
                row[k] = int(p[k])
        else:
            for k in ("kvinna_resare", "kvinna_ensam", "flera_resare", "kvinna_dod", "drengr", "thegn", "god") + tuple(
                    f"rel_{x}" for x in ("barn", "foralder", "syskon", "make", "slakt", "ej_slakt")):
                row[k] = None
        for k in ("gravfalt", "hog", "vag", "bro", "fornborg", "church"):
            km = _num(r.get(f"km_{k}"))
            row[f"nara_{k}"] = None if km is None else int(km < NEAR_KM)
        wk = _num(g.get("water_km"))
        row["nara_vatten"] = None if wk is None or c.get("moved") == "1" else int(wk < WATER_KM)
        h = dm.get("height_m") if dm.get("status") == "ok" and not dm.get("fragment") else None
        row["hog_sten"] = None if h is None else int(h >= TALL_M)
        out.append(row)
    return out


def write(corpus_dir: str, path: str) -> int:
    rs = rows(corpus_dir)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rs[0]))
        w.writeheader()
        for r in rs:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    json.dump(FAMILY, open(os.path.splitext(path)[0] + "_familjer.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return len(rs)


if __name__ == "__main__":
    import sys
    print(write(sys.argv[1], sys.argv[2]))
