"""Torshammare i svensk jord – enligt analysplaner/2026-11-20-torshammare.md (låst 14a659e).

Läser SHM-exporterna i downloads/torshammare/ (shm/*.csv: hammarposterna; exponering/Kam.csv, Spänne.csv: T1:s exponering;
metadata CC0, samlingar.shm.se), Rundata (runstenarna) och data/geo/socknar_harader.json (Wikidata, CC0).
Rådata är inte vår och ligger utanför git; här skrivs bara summor.

    .venv/bin/python utdata/torshammare/analys.py --grind     # stickproven till kvalitetsgrinden
    .venv/bin/python utdata/torshammare/analys.py             # måtten D1–D7 + data till T1 (analys_t1.R)
"""
import csv
import glob
import json
import os
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src.research_gaps import PROVINCE_NAMES, is_runestone  # noqa: E402

SRC = os.environ.get("TORSHAMMARE", "/Volumes/2TB/Antigrvity/Runes/downloads/torshammare")
CACHE = os.path.join(ROOT, "data", "cache", "torshammare")
HERE = os.path.dirname(__file__)
MALAREN = {"Uppland", "Södermanland", "Västmanland", "Närke"}

# --- regeln (planen: Underlaget) ---
RULE1 = re.compile(r"th?orshammar", re.I)
RULE2_NAMES = {"amulett", "amulettring", "amuletthänge", "hammare", "gjutform"}
RULE2_TEXT = re.compile(r"th?orshammar|hammarformad|hammarformat|hammarhänge|miniatyrhammare|med hammare|hammarhängen", re.I)
OLD_ONLY = re.compile(r"^(stenålder|bronsålder|neolitikum|mesolitikum|paleolitikum|tidigneolitikum|mellanneolitikum|"
                      r"senneolitikum|äldre bronsålder|yngre bronsålder|äldre stenålder|yngre stenålder)$", re.I)
STONE_TEXT = re.compile(r"brynsten|stenyxa|yxa av sten", re.I)
CONTEXT = [("skatt", re.compile(r"skatt|depå", re.I)),
           ("grav", re.compile(r"grav|stensättning|\bhög\b|röse|skelett|kremering|urna|brandlager|kammargrav|båtgrav", re.I)),
           ("boplats", re.compile(r"hus|grop|kulturlager|boplats|stolphål|härd|svarta jorden|r-enhet|ruta|lager", re.I)),
           ("lösfynd", re.compile(r"lösfynd|detektor|påträffad i åker|plöj", re.I))]


def rows(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def shm_union():
    seen = {}
    for p in sorted(glob.glob(os.path.join(SRC, "shm", "*.csv"))):
        for r in rows(p):
            seen.setdefault(r["Föremålsnummer"], r)
    return list(seen.values())


def names(r):
    return [n.strip() for n in r["Föremålsbenämning"].split("|") if n.strip()]


def text(r):
    return " ".join([r["Föremålsbenämning"], r["Titel"], r["Beskrivning"]])


def rule(r):
    """1 or 2 when the record is a genuine Thor's hammer, else None (planen: regel 1–3)."""
    nm = names(r)
    which = None
    if any(RULE1.search(n) for n in nm) or any(n.lower() == "miniatyr hammare" for n in nm):
        which = 1
    elif any(n.lower() in RULE2_NAMES for n in nm) and RULE2_TEXT.search(text(r)):
        which = 2
    if which is None:
        return None
    periods = [p.strip() for p in r["Tidsperiod"].split("|") if p.strip()]
    if periods and all(OLD_ONLY.match(p) for p in periods):
        return None
    if STONE_TEXT.search(text(r)):
        return None
    mats = {m.strip().lower() for m in r["Material"].split("|") if m.strip()}
    if mats == {"sten"} and not any(n.lower() == "gjutform" for n in nm):
        return None
    return which


def kind(r):
    if re.search("ring", r["Föremålsbenämning"] + " " + r["Titel"], re.I):
        return "ring"
    if any(n.lower() == "gjutform" for n in names(r)):
        return "gjutform"
    return "hänge"


def context(r):
    t = r["Arkeologisk kontext"].strip() or " ".join([r["Titel"], r["Beskrivning"], r["Fyndplats, Plats"]])
    for k, rx in CONTEXT:
        if rx.search(t):
            return k
    return "okänt"


def material(r):
    m = (r["Material"].split("|")[0] if r["Material"] else "").strip().lower()
    if "silver" in m:
        return "silver"
    if any(w in m for w in ("brons", "koppar", "mässing")):
        return "brons/kopparlegering"
    if "järn" in m:
        return "järn"
    return "annat/tomt"


def period(r):
    return r["Tidsperiod"].strip() or "tom"


def objects(r):
    try:
        return max(1, int(r["Antal"]))
    except ValueError:
        return 1


# --- socken → härad (Wikidata), på namn + landskap ---
def fold(s):
    s = unicodedata.normalize("NFC", s or "").strip()
    s = s.split("|")[0].strip()
    s = re.sub(r"\s+(sn|socken|landsförsamling|stadsförsamling)\.?$", "", s, flags=re.I)
    return s.lower()


class Harad:
    def __init__(self):
        d = json.load(open(os.path.join(ROOT, "data", "geo", "socknar_harader.json"), encoding="utf-8"))
        land = {r["id"]: r["land"] for r in csv.DictReader(open(os.path.join(ROOT, "data", "geo", "socknar_land.csv"),
                                                                      encoding="utf-8"))}
        self.by_name = defaultdict(list)
        for s in d["socknar"]:
            if s.get("harad"):
                f = fold(s["namn"])
                cand = (s["harad"][0]["namn"], land.get(s["id"]) or "")
                # Wikidata writes the parish in the genitive ("Vendels socken"); the museums often not ("Vendel socken")
                for key in {f, f[:-1] if f.endswith("s") and len(f) > 3 else f}:
                    if cand not in self.by_name[key]:
                        self.by_name[key].append(cand)
        # Where Wikidata gives the parish no härad (327 parishes, e.g. Järfälla), Rundata's district for the parish's
        # runestones, written the same way ("Färentuna hd" → "Färentuna härad")
        self.rundata = defaultdict(Counter)
        for r in store().inscriptions:
            dist, par = (r.get("district") or "").strip(), (r.get("parish") or "").strip()
            if dist and par and r["signum"].split()[0] in PROVINCE_NAMES:
                dist = re.sub(r"\bhd$", "härad", dist)
                f = fold(par)
                for key in {f, f[:-1] if f.endswith("s") and len(f) > 3 else f}:
                    self.rundata[(key, PROVINCE_NAMES[r["signum"].split()[0]])][dist] += 1
        self.harad_land = defaultdict(Counter)  # filled by learn()

    def learn(self, pairs):
        """Härad → landskap from unambiguous matches (socken name with one candidate) of the records' own landskap."""
        for soc, ls in pairs:
            c = self.by_name.get(fold(soc), [])
            if len(c) == 1 and ls:
                self.harad_land[c[0][0]][ls] += 1
        for cands in self.by_name.values():
            for h, ls in cands:
                if ls:
                    self.harad_land[h][ls] += 1

    def of(self, soc, ls):
        c = self.by_name.get(fold(soc), [])
        if len(c) == 1:
            return c[0][0]
        fit = [h for h, l in c if l == ls] or [h for h, _ in c if self.harad_land[h] and self.harad_land[h].most_common(1)[0][0] == ls]
        if len(set(fit)) == 1:
            return fit[0]
        rd = self.rundata.get((fold(soc), ls))
        return rd.most_common(1)[0][0] if rd else None


def hammers():
    out = []
    for r in shm_union():
        w = rule(r)
        if w:
            out.append(dict(r, _rule=w))
    return out


def grind():
    os.makedirs(CACHE, exist_ok=True)
    hs = hammers()
    r2 = [h for h in hs if h["_rule"] == 2]
    r1 = [h for h in hs if h["_rule"] == 1]
    s1 = random.Random(20261120).sample(r1, min(50, len(r1)))
    s3 = random.Random(20261121).sample(hs, min(60, len(hs)))
    cols = ["Föremålsnummer", "Föremålsbenämning", "Material", "Tidsperiod", "Fyndplats, Landskap", "Fyndplats, Socken",
            "Titel", "Beskrivning"]
    for name, sample in (("grind_regel2.csv", r2), ("grind_regel1_prov50.csv", s1)):
        with open(os.path.join(CACHE, name), "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            for h in sample:
                w.writerow([h[c][:300] for c in cols])
    with open(os.path.join(CACHE, "grind_kontext_prov60_blind.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Föremålsnummer", "Arkeologisk kontext", "Fyndplats, Plats", "Titel", "Beskrivning"])
        for h in s3:
            w.writerow([h["Föremålsnummer"], h["Arkeologisk kontext"], h["Fyndplats, Plats"], h["Titel"][:200], h["Beskrivning"][:300]])
    with open(os.path.join(CACHE, "grind_kontext_regel.json"), "w", encoding="utf-8") as f:
        json.dump({h["Föremålsnummer"]: context(h) for h in s3}, f, ensure_ascii=False, indent=0)
    print(f"äkta enligt regeln: {len(hs)} (regel 1: {len(r1)}, regel 2: {len(r2)}); stickprov i {CACHE}")


def pct(a, b):
    return round(100 * a / b, 1) if b else None


def main():
    excluded = set()
    p = os.path.join(HERE, "grind_bort.txt")  # records judged wrong at the gate (rule 2), one Föremålsnummer per line
    if os.path.exists(p):
        excluded = {ln.strip() for ln in open(p, encoding="utf-8") if ln.strip() and not ln.startswith("#")}
    hs = [h for h in hammers() if h["Föremålsnummer"] not in excluded]
    for h in hs:
        h["_kind"], h["_ctx"], h["_mat"], h["_per"] = kind(h), context(h), material(h), period(h)
        h["_land"] = h["Fyndplats, Landskap"].strip() or "okänt"
    res = {"poster": len(hs), "föremål": sum(objects(h) for h in hs), "bort_vid_grinden": sorted(excluded)}

    # D1–D4
    res["D1_per_landskap"] = {l: {"poster": n, "föremål": sum(objects(h) for h in hs if h["_land"] == l),
                                  **{k: sum(1 for h in hs if h["_land"] == l and h["_kind"] == k) for k in ("ring", "hänge", "gjutform")}}
                              for l, n in Counter(h["_land"] for h in hs).most_common()}
    res["D1_per_typ"] = dict(Counter(h["_kind"] for h in hs))
    for key, fld in (("D2_sammanhang", "_ctx"), ("D3_period", "_per"), ("D4_material", "_mat")):
        res[key] = {k: {"n": sum(1 for h in hs if h["_kind"] == k),
                        "andelar": {v: pct(c, sum(1 for h in hs if h["_kind"] == k))
                                    for v, c in Counter(h[fld] for h in hs if h["_kind"] == k).most_common()},
                        "antal": dict(Counter(h[fld] for h in hs if h["_kind"] == k).most_common())}
                    for k in ("ring", "hänge", "gjutform")}
    res["D2_sammanhang_per_landskap"] = {l: dict(Counter(h["_ctx"] for h in hs if h["_land"] == l).most_common())
                                         for l, n in Counter(h["_land"] for h in hs).most_common() if n >= 10}
    res["D6_malardalen"] = {k: {"n": sum(1 for h in hs if h["_kind"] == k),
                                "mälardalen": sum(1 for h in hs if h["_kind"] == k and h["_land"] in MALAREN),
                                "andel": pct(sum(1 for h in hs if h["_kind"] == k and h["_land"] in MALAREN),
                                             sum(1 for h in hs if h["_kind"] == k))} for k in ("ring", "hänge")}
    res["D7_socknar"] = [{"socken": s, "landskap": l, "poster": n}
                         for (s, l), n in Counter((h["Fyndplats, Socken"].split("|")[0].strip() or "okänd", h["_land"]) for h in hs).most_common(5)]

    # Gotland för sig
    got = [h for h in hs if h["_land"] == "Gotland"]
    res["gotland"] = {"poster": len(got), "typ": dict(Counter(h["_kind"] for h in got)), "sammanhang": dict(Counter(h["_ctx"] for h in got)),
                      "material": dict(Counter(h["_mat"] for h in got)), "period": dict(Counter(h["_per"] for h in got))}
    res["gotland_ksamsok_andra"] = ksamsok_gotland()

    # T1: per härad
    hr = Harad()
    stones = [r for r in store().inscriptions if is_runestone(r)]
    expo = [r for n in ("Kam", "Spänne") for r in rows(os.path.join(SRC, "exponering", f"{n}.csv"))
            if "Vikingatid" in r["Tidsperiod"]]
    hr.learn([(h["Fyndplats, Socken"], h["Fyndplats, Landskap"]) for h in hs + expo]
             + [((r.get("parish") or ""), PROVINCE_NAMES.get(r["signum"].split()[0], "")) for r in stones])
    unmatched = Counter()
    seen_land = defaultdict(Counter)  # härad → the landskap of the records that landed there (its landskap = majority)

    def tally(items, soc, land, skip_adelso):
        c = Counter()
        for it in items:
            s, l = soc(it), land(it)
            if l == "Gotland" or (skip_adelso and fold(s) == "adelsö"):
                continue
            h = hr.of(s, l)
            if h:
                c[h] += 1
                seen_land[h][l] += 1
            else:
                unmatched[(l, s.split("|")[0].strip())] += 1
        return c

    def table(skip_adelso):
        unmatched.clear()
        sh = lambda h: h["Fyndplats, Socken"]  # noqa: E731
        ln = lambda h: h["Fyndplats, Landskap"].strip()  # noqa: E731
        H = tally(hs, sh, ln, skip_adelso)
        Hr = tally([h for h in hs if h["_kind"] == "ring"], sh, ln, skip_adelso)
        Hh = tally([h for h in hs if h["_kind"] == "hänge"], sh, ln, skip_adelso)
        E = tally(expo, sh, ln, skip_adelso)
        R = tally(stones, lambda r: r.get("parish") or "", lambda r: PROVINCE_NAMES.get(r["signum"].split()[0], ""), skip_adelso)
        um = dict(unmatched)
        out = []
        for h in sorted(set(E) | set(H) | set(R)):
            if E[h] >= 5:
                land = seen_land[h].most_common(1)[0][0] if seen_land[h] else "okänt"
                out.append({"harad": h, "landskap": land, "hammare": H[h], "ringar": Hr[h], "hangen": Hh[h],
                            "exponering": E[h], "runstenar": R[h]})
        return out, um, H, E, R

    os.makedirs(CACHE, exist_ok=True)
    for skip, name in ((False, "harader.csv"), (True, "harader_utan_adelso.csv")):
        tab, um, H, E, R = table(skip)
        with open(os.path.join(CACHE, name), "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(tab[0]))
            w.writeheader()
            w.writerows(tab)
        if not skip:
            res["T1_underlag"] = {"härader_med_exponering_minst_5": len(tab),
                                  "hammare_i_dem": sum(t["hammare"] for t in tab), "hammare_kopplade_totalt": sum(H.values()),
                                  "exponering_poster": len(expo), "runstenar_i_dem": sum(t["runstenar"] for t in tab),
                                  "runstenar_kopplade_totalt": sum(R.values()), "runstenar_totalt_utom_gotland": sum(1 for r in stones if not r["signum"].startswith("G ")),
                                  "okopplade_socknar": len(um), "okopplade_poster": sum(um.values()),
                                  "okopplade_vanligaste": [f"{l}: {s} ({n})" for (l, s), n in Counter(um).most_common(15)]}
            # D5: map per härad (alla härader med hammare), med runstenarna
            res["D5_harad"] = [{"harad": h, "hammare": n, "runstenar": R[h], "exponering": E[h]} for h, n in H.most_common()]
    json.dump(res, open(os.path.join(HERE, "matt.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("poster", "föremål", "D1_per_typ", "T1_underlag")}, ensure_ascii=False, indent=1))


def ksamsok_gotland():
    """K-samsök records from other managers than SHM on Gotland, with the same rule on name/label/description."""
    csv.field_size_limit(10 ** 9)
    p = os.path.join(SRC, "ksamsok", "ksamsok_flat.csv")
    n, hits = 0, []
    for r in rows(p):
        if r["serviceOrganization"] == "shm" or "Gotland" not in r["provinceName"]:
            continue
        n += 1
        t = " ".join([r["itemName"], r["itemLabel"], r["desc"]])
        if RULE1.search(t) or RULE2_TEXT.search(t):
            hits.append(r["itemNumber"])
    return {"poster_gotland_andra": n, "torshammare": len(hits)}


if __name__ == "__main__":
    grind() if "--grind" in sys.argv else main()
