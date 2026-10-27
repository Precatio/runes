"""Samma familjer, platser och händelser på flera runstenar: länkar mellan stenar som delar namn, prövade mot slumpen.

Två runstenar länkas när de delar personnamn eller gårdsnamn (src/entities.extract; ristarna räknas inte, de prövas för
sig i ristarmodellerna). Varje delat namn vägs efter hur ovanligt det är, som i informationssökning: vikten är
log(N / n), där n är antalet runstenar med namnet och N alla runstenar med namn. Länkens styrka är summan av vikterna.

Slumpen prövas med en nollmodell: personnamnen blandas mellan stenarna inom samma landskap (varje sten behåller sitt
antal namn och varje namn sitt antal stenar i landskapet), N_NULL gånger. För en länk med styrka s är den uppskattade
andelen falska länkar (q, FDR) antalet länkar med styrka ≥ s i nollmodellen, i genomsnitt, delat med antalet i data.
Länkar med q under FDR_CUT bildar släktgrupper: stenar som hänger ihop genom länkarna.

Prövning: Jarlabankes stenar, där han säger att han ensam ägde Täby (U 127, U 164, U 165, U 212, U 261), och Rundatas
parstenar (anteckningen "Parsten till …"), som modellen inte ser.

Bara runstenar ingår (appens grundregel). Namnen läses med regler ur Rundatas engelska översättning; ett namn som
regeln missar ger ingen länk, och samma namn kan vara olika personer – därför nollmodellen.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np

from src.entities import extract
from src.r_bridge import _style_dates
from src import research_gaps as gaps

FDR_CUT = 0.1
N_NULL = 200
COMMON = 60  # a name on more runestones than this links nothing by itself


def runestones(inscriptions: list[dict]) -> list[dict]:
    return [r for r in inscriptions if (r.get("period") or "").startswith("V") and "runsten" in (r.get("object") or "").lower()
            and r.get("translation_en")]


def km(a: dict, b: dict) -> float | None:
    if a.get("lat") is None or b.get("lat") is None:
        return None
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def stones(inscriptions: list[dict]) -> dict[str, dict]:
    """Per runsten: platsen, dateringen, enheterna och de namn som kan länka (personer utom ristare, gårdsnamn)."""
    out = {}
    for r in runestones(inscriptions):
        e = extract(r)
        d = _style_dates(r)
        out[r["signum"]] = {"signum": r["signum"], "lat": r.get("lat"), "lon": r.get("lon"),
                            "province": gaps.province(r), "place": r.get("place") or "", "parish": r.get("parish") or "",
                            "district": r.get("district") or "",
                            "from": d["style_from"], "to": d["style_to"], "carvers": sorted(gaps.certain_carvers(r)),
                            "persons": e["persons"], "places": [p["key"] for p in e["places"]], "events": e["events"],
                            "facts": [list(f) for f in e["facts"]],
                            "names": {p["key"] for p in e["persons"] if p["role"] != "ristare"},
                            "other": r.get("other") or ""}
    return out


def _tokens(s: dict) -> set[str]:
    return set(s["names"]) | {"plats:" + p for p in s["places"]}


def weights(st: dict[str, dict]) -> dict[str, float]:
    """log(N / n) per namn och gårdsnamn (gårdsnamnen med prefixet 'plats:')."""
    n = Counter(k for s in st.values() for k in _tokens(s))
    N = sum(1 for s in st.values() if _tokens(s))
    return {k: math.log(N / v) for k, v in n.items()}


def links(st: dict[str, dict], w: dict[str, float], token_sets: dict[str, set] | None = None) -> list[dict]:
    """Par av stenar som delar minst två namn eller ett gårdsnamn, med styrkan (summan av vikterna)."""
    ts = token_sets if token_sets is not None else {sg: _tokens(s) for sg, s in st.items()}
    index = defaultdict(list)
    for sg, t in ts.items():
        for k in t:
            index[k].append(sg)
    cand = set()
    for k, sgs in index.items():
        if len(sgs) > COMMON:
            continue
        for a, b in combinations(sorted(sgs), 2):
            cand.add((a, b))
    out = []
    for a, b in cand:
        ks = ts[a] & ts[b]
        place = any(k.startswith("plats:") for k in ks)
        if len(ks) < 2 and not place:
            continue
        out.append({"a": a, "b": b, "shared": sorted(ks), "score": round(sum(w.get(k, 0.0) for k in ks), 3)})
    return out


def null_scores(st: dict[str, dict], w: dict[str, float], n: int = N_NULL, seed: int = 2026,
                level: str = "province") -> list[np.ndarray]:
    """Länkstyrkorna när personnamnen blandats mellan stenarna inom landskapet (level="province") eller, strängare,
    inom häradet (level="district": lokala namnseder), medan gårdsnamnen följer sin sten."""
    rng = np.random.default_rng(seed)
    by_prov = defaultdict(list)
    for sg, s in st.items():
        by_prov[s["province"] if level == "province" else (s["province"], s.get("district") or s["parish"])].append(sg)
    out = []
    for _ in range(n):
        ts = {}
        for sgs in by_prov.values():
            pool = [k for sg in sgs for k in sorted(st[sg]["names"])]
            rng.shuffle(pool)
            i = 0
            for sg in sgs:
                k = len(st[sg]["names"])
                ts[sg] = set(pool[i:i + k]) | {"plats:" + p for p in st[sg]["places"]}
                i += k
        out.append(np.array([x["score"] for x in links(st, w, ts)]))
    return out


def fdr(obs: list[dict], null: list[np.ndarray]) -> None:
    """Lägger på den uppskattade andelen falska länkar (q) per länk, monoton i styrkan."""
    sc = np.array([x["score"] for x in obs])
    order = np.argsort(-sc)
    allnull = np.sort(np.concatenate(null)) if null else np.array([])
    k = max(1, len(null))
    q = np.empty(len(sc))
    for rank, i in enumerate(order, 1):
        exp = (len(allnull) - np.searchsorted(allnull, sc[i], side="left")) / k
        q[i] = min(1.0, exp / rank)
    best = 1.0
    for i in order[::-1]:
        best = min(best, q[i])
        q[i] = best
    for x, v in zip(obs, q):
        x["q"] = round(float(v), 4)


def groups(obs: list[dict], st: dict[str, dict], cut: float = FDR_CUT) -> list[dict]:
    """Släktgrupper: stenar som hänger ihop genom länkar med q under cut."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for x in obs:
        if x["q"] < cut:
            parent[find(x["a"])] = find(x["b"])
    g = defaultdict(set)
    for x in list(parent):
        g[find(x)].add(x)
    out = []
    for members in g.values():
        if len(members) < 2:
            continue
        ms = sorted(members)
        names = Counter(k for sg in ms for k in _tokens(st[sg]))
        dists = [d for d in (km(st[a], st[b]) for a, b in combinations(ms, 2)) if d is not None]
        out.append({"stones": ms, "n": len(ms), "names": [k for k, c in names.most_common() if c >= 2][:8],
                    "max_km": round(max(dists), 1) if dists else None,
                    "provinces": sorted({st[sg]["province"] for sg in ms})})
    return sorted(out, key=lambda x: -x["n"])


def parsten_pairs(st: dict[str, dict]) -> set[tuple[str, str]]:
    """Rundatas parstenar ('Parsten till U 343.') bland stenarna."""
    out = set()
    for sg, s in st.items():
        for m in re.finditer(r"[Pp]arsten till ([A-ZÅÄÖ][a-zåäö]* [\w;:/-]+)", s["other"]):
            other = m.group(1).rstrip(".,")
            if other in st:
                out.add(tuple(sorted((sg, other))))
    return out


PARENT = {"father", "mother"}
CHILD = {"son", "sons", "daughter", "daughters"}


def parents(s: dict) -> dict[str, set[str]]:
    """Vem som är förälder till vem på en sten, ur släktfakta: {barn: {föräldrar}}."""
    out = defaultdict(set)
    for a, rel, b in s["facts"]:
        if rel in PARENT:            # a is b's father/mother
            out[b].add(a)
        elif rel in CHILD:           # a is b's son/daughter
            out[a].add(b)
        elif rel == "förälder till":  # a is b's parent (patronymic)
            out[b].add(a)
    return out


def contradictions(x: dict, st: dict[str, dict]) -> list[str]:
    """Varför två stenar inte kan gälla samma personer: olika föräldrar för samma namn, eller en person som är död på en
    äldre sten och reser en sten på en yngre (efter stilgruppernas datering)."""
    A, B = st[x["a"]], st[x["b"]]
    pa, pb = parents(A), parents(B)
    out = []
    for k in x["shared"]:
        if k.startswith("plats:"):
            continue
        if pa.get(k) and pb.get(k) and not (pa[k] & pb[k]):
            out.append(f"{k}: olika föräldrar ({', '.join(sorted(pa[k]))} / {', '.join(sorted(pb[k]))})")
        role = lambda s, k: {p["role"] for p in s["persons"] if p["key"] == k}  # noqa: E731
        for old, new in ((A, B), (B, A)):
            if old["to"] is not None and new["from"] is not None and old["to"] < new["from"] \
                    and "minnes" in role(old, k) and "resare" in role(new, k):
                out.append(f"{k}: död på {old['signum']} men resare på den yngre {new['signum']}")
    return out


def patterns(path: str) -> list[dict]:
    """Mönstren ur länkmodellen för Statistik (R) (märks Nytt via src/pattern_registry.py)."""
    import json
    try:
        d = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not d.get("n_links"):
        return []
    from src.r_findings import _d, significance
    cut = d["fdr_cut"]
    prov = lambda sg: sg.split()[0]  # noqa: E731
    sure = [x for x in d["links"] if x["q"] < cut and not x["contradictions"]]
    cross = [x for x in sure if prov(x["a"]) != prov(x["b"])]
    killed = [x for x in d["links"] if x["q"] < cut and x["contradictions"] and prov(x["a"]) != prov(x["b"])]
    cross_txt = ("; över landskapsgränserna håller bara " + ", ".join(f"{x['a']}–{x['b']} ({', '.join(x['names'])}, "
                 f"{x['km']:.0f} km)".replace(".", ",") for x in cross) + ", och inte i den strängare prövningen"
                 if cross else "; ingen länk över landskapsgränserna håller")
    return [{"key": "links_local", "topic": "Släkter över stenar", "status": "mönster att pröva",
             "text": f"Av {d['n_links']} par av runstenar som delar minst två namn eller ett gårdsnamn ger slumpen omkring "
                     f"{round(d['null_mean'])}. {d['n_sure']} länkar håller (andel falska under {round(cut * 100)} %), och de "
                     f"står i median {_d(d['km_median_sure'], 1)} km isär, {round(d['share_sure_within_10km'] * 100)} % inom "
                     f"10 km. Familjerna som går att följa över flera stenar var lokala: {len(killed)} länkar mellan "
                     f"landskap som först såg starka ut faller på motsägelser i släktskap eller tid{cross_txt}.",
             "note": "Namnen läses med regler ur Rundatas engelska översättning (src/entities.py) och vägs efter hur ovanliga "
                     "de är; nollmodellen blandar namnen inom landskapet (200 gånger), den strängare inom häradet "
                     f"({d['n_sure_district']} länkar håller där). Parstenar delar ofta bara ett namn och fångas därför sällan "
                     f"({d['validation']['parsten']['found']} av {d['validation']['parsten']['n']}). Samma namn med olika "
                     "föräldrar, eller en person som är död på en äldre sten och reser en sten på en yngre, avfärdar en länk.",
             "significance": significance(None, test="nollmodell med blandade namn (andel falska länkar per länk)")}]
