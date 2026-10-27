"""Samma familjer, platser och händelser på flera runstenar: länkar mellan stenar som delar namn, prövade mot slumpen.

Två runstenar länkas när de delar minst två personnamn eller ett gårdsnamn (src/entities.extract; ristarna räknas inte,
de prövas för sig i ristarmodellerna), och minst ett av de delade namnen står på högst COMMON runstenar: ett par som
bara delar mycket vanliga namn (Sveinn, Bjôrn, Þorsteinn, Ulfr) prövas inte, varken i data eller i nollmodellen. Varje
delat namn vägs efter hur ovanligt det är, som i informationssökning: vikten är log(N / n), där n är antalet runstenar
med namnet och N alla runstenar med namn. Länkens styrka är summan av vikterna.

Slumpen prövas med en nollmodell: personnamnen blandas mellan stenarna inom samma landskap, N_NULL gånger. Varje sten
behåller sitt antal namn och varje namn sitt antal stenar i landskapet; en sten får aldrig samma namn två gånger (en
dubblett byts mot ett namn på en annan sten i landskapet, så att båda marginalerna står kvar). För en länk med styrka s
är den uppskattade andelen falska länkar (q, FDR) antalet länkar med styrka ≥ s i nollmodellen, i genomsnitt, delat
med antalet i data. Slumpfelet i q skattas genom att dra om nollkörningarna (bootstrap, q_lo–q_hi): en länk vars
intervall går över FDR_CUT är osäker, och det redovisas. Länkar med q under FDR_CUT bildar släktgrupper: stenar som
hänger ihop genom länkarna.

Prövning: Jarlabankes stenar, där han säger att han ensam ägde Täby (U 127, U 164, U 165, U 212, U 261), och Rundatas
parstenar (anteckningen "Parsten till …", "parstenen till …", "Parsten med …"), som modellen inte ser. En länk är
rundata_linked när någon av stenarnas anmärkning i Rundata nämner den andra stenen ("Utgör ett monument tillsammans
med …", "Samma brödrakrets som nämns på …", också i en följd: "U 457-U 459 härrör från samma ätt").

Motsägelser: olika fäder eller olika mödrar för samma namn. Förälderns kön tas ur släktorden, ur pronomenet ("in memory
of Ôzurr, his son": resaren är en man) och, när materialet inget säger, ur namnets ändelse (name_sex, ending_sex).

Bara runstenar ingår (appens grundregel). Namnen läses med regler ur Rundatas engelska översättning; ett namn som
regeln missar ger ingen länk, och samma namn kan vara olika personer – därför nollmodellen.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np

from src.entities import FEMALE, extract
from src.r_bridge import _style_dates
from src import research_gaps as gaps

FDR_CUT = 0.1
N_NULL = 2000  # 200 left q at the cut to Monte Carlo noise (the Jarlabanke block flipped with the seed)
COMMON = 60  # a name on more runestones than this links nothing by itself
N_BOOT = 500  # bootstrap draws over the null replicates for the Monte Carlo interval of q
# Style-group dates are rough (a group spans 30-40 years, and the order of two groups can be wrong for a given pair of
# stones): the time rule needs a gap of at least this many years between the intervals, and never applies to stones at
# the same site or stones that Rundata's notes tie together
TIME_GAP = 30
SAME_SITE_KM = 1.0
RANGE = 10  # 'U 457-U 459' in a note ties the stones in the range together, when it spans at most this many numbers
MALE = {"father", "son", "sons", "brother", "brothers", "husband", "husbandman", "grandfather", "grandson", "uncle",
        "nephew", "stepson", "stepfather", "foster-son", "foster-father", "foster-brother", "father-in-law",
        "son-in-law", "brother-in-law"}


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
                            "pron": _pronoun_sex(r.get("translation_en") or "", e["persons"], e["facts"]),
                            "other": r.get("other") or ""}
    return out


def _pronoun_sex(text: str, persons: list[dict], facts: list) -> list[tuple[str, str]]:
    """Resarens kön ur pronomenet vid den dödes släktord: 'Gási raised the stone in memory of Ôzurr, his son' gör Gási
    till man, 'her son' resaren till kvinna. Bara när släktfaktumet gäller en enda resare ('their' säger inget)."""
    t = re.sub(r"§[A-Z]+\s*", " ", text.replace("(?)", ""))
    name = {p["key"]: p["name"] for p in persons}
    raisers = {p["key"] for p in persons if p["role"] == "resare"}
    by = defaultdict(set)
    for a, rel, b in facts:
        if b in raisers and rel != "förälder till":
            by[(a, rel)].add(b)
    out = []
    for (a, rel), bs in by.items():
        if len(bs) != 1 or a not in name:
            continue
        n, r_ = re.escape(name[a]), re.escape(rel)
        m = (re.search(rf"(?<!\w){n},?\s+(his|her|their)\s+(?:\w+\s+){{0,2}}?{r_}\b", t)
             or re.search(rf"\b(his|her|their)\s+(?:\w+\s+)?{r_}\s+{n}(?!\w)", t))
        if m and m.group(1) != "their":
            out.append((next(iter(bs)), "m" if m.group(1) == "his" else "f"))
    return out


def _tokens(s: dict) -> set[str]:
    return set(s["names"]) | {"plats:" + p for p in s["places"]}


def weights(st: dict[str, dict]) -> dict[str, float]:
    """log(N / n) per namn och gårdsnamn (gårdsnamnen med prefixet 'plats:')."""
    n = Counter(k for s in st.values() for k in _tokens(s))
    N = sum(1 for s in st.values() if _tokens(s))
    return {k: math.log(N / v) for k, v in n.items()}


def links(st: dict[str, dict], w: dict[str, float], token_sets: dict[str, set] | None = None) -> list[dict]:
    """Par av stenar som delar minst två namn eller ett gårdsnamn, med styrkan (summan av vikterna). Paret prövas bara
    när minst ett delat namn står på högst COMMON runstenar (se all_pairs för hur många par regeln lämnar utanför)."""
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


def all_pairs(st: dict[str, dict]) -> int:
    """Antalet par som delar minst två namn eller ett gårdsnamn, också de som bara delar namn på fler än COMMON stenar."""
    ts = {sg: _tokens(s) for sg, s in st.items()}
    index = defaultdict(list)
    for sg, t in ts.items():
        for k in t:
            index[k].append(sg)
    cand = {p for sgs in index.values() for p in combinations(sorted(sgs), 2)}
    return sum(1 for a, b in cand if len(ts[a] & ts[b]) >= 2 or any(k.startswith("plats:") for k in ts[a] & ts[b]))


def _draw(sizes: list[int], pool: list[str], rng: np.random.Generator, tries: int = 200) -> tuple[list[list[str]], int]:
    """Blandar namnen över stenarna (storlekarna i sizes) utan att en sten får samma namn två gånger: en dubblett byts mot
    ett namn på en slumpvis vald annan sten så länge bytet inte ger en ny dubblett. Båda marginalerna (namn per sten,
    stenar per namn) står kvar. Ger listorna och antalet dubbletter som inte gick att byta bort (väntat 0)."""
    rng.shuffle(pool)
    lists, slot, i = [], [], 0  # slot: (stone, position) of every place in the pool
    for si, k in enumerate(sizes):
        lists.append(pool[i:i + k])
        slot.extend((si, j) for j in range(k))
        i += k
    left = 0
    for si, li in enumerate(lists):
        for j in range(len(li)):
            a = li[j]
            if a not in li[:j]:
                continue
            for _ in range(tries):
                o, m = slot[int(rng.integers(len(slot)))]
                b = lists[o][m]
                if o != si and b not in li and a not in lists[o]:
                    li[j], lists[o][m] = b, a
                    break
            else:
                left += 1
    return lists, left


def null_scores(st: dict[str, dict], w: dict[str, float], n: int = N_NULL, seed: int = 2026,
                level: str = "province", stats: dict | None = None) -> list[np.ndarray]:
    """Länkstyrkorna när personnamnen blandats mellan stenarna inom landskapet (level="province") eller, strängare,
    inom häradet (level="district": lokala namnseder), medan gårdsnamnen följer sin sten. Ingen sten får samma namn två
    gånger (_draw). stats får antalet dubbletter som inte gick att byta bort."""
    rng = np.random.default_rng(seed)
    by_prov = defaultdict(list)
    for sg, s in st.items():
        by_prov[s["province"] if level == "province" else (s["province"], s.get("district") or s["parish"])].append(sg)
    groups_ = [(sgs, [len(st[sg]["names"]) for sg in sgs], [k for sg in sgs for k in sorted(st[sg]["names"])])
               for sgs in by_prov.values()]
    out, left = [], 0
    for _ in range(n):
        ts = {}
        for sgs, sizes, names in groups_:
            lists, lo = _draw(sizes, list(names), rng)
            left += lo
            for sg, li in zip(sgs, lists):
                ts[sg] = set(li) | {"plats:" + p for p in st[sg]["places"]}
        out.append(np.array([x["score"] for x in links(st, w, ts)]))
    if stats is not None:
        stats["unrepaired"] = left
    return out


def _q(exp: np.ndarray, order: np.ndarray) -> np.ndarray:
    """q ur det väntade antalet nollänkar per länk (exp, sista axeln), monoton i styrkan (order: starkast först)."""
    ranks = np.arange(1, exp.shape[-1] + 1)
    qs = np.minimum(1.0, exp[..., order] / ranks)
    qs = np.minimum.accumulate(qs[..., ::-1], axis=-1)[..., ::-1]
    q = np.empty_like(qs)
    q[..., order] = qs
    return q


def fdr(obs: list[dict], null: list[np.ndarray], n_boot: int = N_BOOT, seed: int = 2026) -> np.ndarray:
    """Lägger på den uppskattade andelen falska länkar (q) per länk, monoton i styrkan, och slumpfelets 95-procentiga
    intervall (q_lo, q_hi) när nollkörningarna dras om med återläggning. Ger q för varje omdragning (n_boot × länkar)."""
    sc = np.array([x["score"] for x in obs], dtype=float)
    order = np.argsort(-sc, kind="stable")
    if not null or not len(sc):
        for x in obs:
            x["q"] = x["q_lo"] = x["q_hi"] = 1.0
        return np.ones((0, len(sc)))
    # counts[r, i]: links in null replicate r at least as strong as link i
    counts = np.array([len(z) - np.searchsorted(np.sort(z), sc, side="left") for z in null], dtype=float)
    q = _q(counts.mean(axis=0), order)
    rng = np.random.default_rng(seed)
    wts = rng.multinomial(len(null), np.full(len(null), 1 / len(null)), size=n_boot) / len(null)
    qb = _q(wts @ counts, order)
    lo, hi = np.percentile(qb, [2.5, 97.5], axis=0)
    for x, v, a, b in zip(obs, q, lo, hi):
        x["q"], x["q_lo"], x["q_hi"] = round(float(v), 4), round(float(a), 4), round(float(b), 4)
    return qb


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
    """Rundatas parstenar ('Parsten till U 343.', 'eventuellt parstenen till U 358', 'Parsten med U Fv1979;245')."""
    out = set()
    for sg, s in st.items():
        for m in re.finditer(r"[Pp]arsten(?:en)? (?:till|med) ([A-ZÅÄÖ][a-zåäö]* [\w;:/-]+)", s["other"]):
            other = m.group(1).rstrip(".,")
            if other in st:
                out.add(tuple(sorted((sg, other))))
    return out


def _mentions(text: str, sg: str) -> bool:
    """Nämner anmärkningen stenen sg? 'U 724', också i en uppräkning ('U 240, 241', 'U 723 och 725')."""
    pre, _, num = sg.partition(" ")
    if not num or not text:
        return False
    if re.search(rf"(?<![\w]){re.escape(pre)}\s+(?:\d+[a-zA-Z]?\s*(?:,|och|&|samt)\s*)*{re.escape(num)}(?![\w;:])",
                 text):
        return True
    # a range of numbers: 'G 134-G 136 har utgjort ett monument', 'U 457-U 459 härrör från samma ätt' (at most RANGE apart)
    if num.isdigit():
        for m in re.finditer(rf"(?<![\w]){re.escape(pre)}\s+(\d+)\s*[-–]\s*(?:{re.escape(pre)}\s+)?(\d+)(?![\w;:])", text):
            lo, hi = int(m.group(1)), int(m.group(2))
            if lo < hi <= lo + RANGE and lo <= int(num) <= hi:
                return True
    return False


def rundata_linked(a: dict, b: dict) -> bool:
    """Knyter Rundata ihop stenarna? Sant när någon av stenarnas anmärkning ('other') nämner den andra stenen: parsten,
    'Utgör ett monument tillsammans med', 'Samma brödrakrets som nämns på' och liknande."""
    return _mentions(a.get("other") or "", b["signum"]) or _mentions(b.get("other") or "", a["signum"])


def rundata_noted_pairs(st: dict[str, dict]) -> set[tuple[str, str]]:
    """Alla par av runstenar som Rundatas anmärkningar knyter ihop, med samma prov som rundata_linked (_mentions), för
    prövningen."""
    by_pre = defaultdict(list)
    for sg in st:
        by_pre[sg.partition(" ")[0]].append(sg)
    out = set()
    for sg, s in st.items():
        text = s["other"]
        if not text:
            continue
        for pre, sgs in by_pre.items():
            if not re.search(rf"(?<![\w]){re.escape(pre)}\s", text):
                continue
            ranged = bool(re.search(r"\d\s*[-–]", text))
            for other in sgs:
                if other != sg and (ranged or other.partition(" ")[2] in text) and _mentions(text, other):
                    out.add(tuple(sorted((sg, other))))
    return out


PARENT = {"father": "m", "mother": "f"}
CHILD = {"son", "sons", "daughter", "daughters"}


# Old Norse female name endings (Rundata's normalised forms, folded as in src/entities.fold): Alfhildr, Ingiríðr,
# Ingigerðr, Ragnheiðr, Ásdís, Gillaug, Rannveig, Ásborg, Sigbjôrg, Ásný, Þyrvé, Hróðelfr, Gunnvôr, Sigþrúðr, Ásgunnr,
# Ingileif, Jôfurfast, Ásmóð, Hróðþjóð. Checked against the names whose sex the corpus gives: -a (26 women, 21 men),
# -rún, -unn and -unnr are mixed and give no sex
FEMALE_END = ("hildr", "ridr", "gerdr", "heidr", "dis", "laug", "veig", "borg", "bjorg", "ny", "ve", "elfr", "vor",
              "thrudr", "gunnr", "leif", "fast", "mod", "thjod")
UNSURE_END = ("a", "run", "unn", "unnr")


def ending_sex(key: str) -> str | None:
    """Namnets kön ur ändelsen när materialet inte säger något: 'f' för de kvinnliga ändelserna (FEMALE_END), 'm' för
    -r, -i och andra konsonanter (Hrútr, Harðr, Víði, Gási, Freybjôrn), inget för -a och de andra blandade ändelserna
    (UNSURE_END)."""
    if len(key) < 3 or key.endswith(UNSURE_END):
        return None
    if key.endswith(FEMALE_END):
        return "f"
    if key[-1] in "irnlstkgdfmpb":
        return "m"
    return None


def name_sex(st: dict[str, dict], endings: bool = True) -> dict[str, str]:
    """Namnets kön: ur släktorden i hela materialet ('m' när namnet minst 90 % av gångerna står som far, son, bror, make …,
    'f' som mor, dotter, syster, hustru …) och ur pronomenet vid den dödes släktord ('in memory of Ôzurr, his son': resaren
    är en man). Ett namn som materialet inte säger något om får könet ur ändelsen (ending_sex, endings=False hoppar över
    det). Ett namn med blandade belägg får inget kön."""
    c = defaultdict(Counter)
    seen = set()
    for s in st.values():
        for p in s["persons"]:
            seen.add(p["key"])
            if p.get("rel") in FEMALE:
                c[p["key"]]["f"] += 1
            elif p.get("rel") in MALE:
                c[p["key"]]["m"] += 1
        for a, rel, b in s["facts"]:  # a is b's <rel>
            seen.update((a, b))
            if rel in FEMALE:
                c[a]["f"] += 1
            elif rel in MALE:
                c[a]["m"] += 1
        for k, sx in s.get("pron", []):
            c[k][sx] += 1
    out = {}
    for k, v in c.items():
        n = v["f"] + v["m"]
        if v["f"] >= 0.9 * n:
            out[k] = "f"
        elif v["m"] >= 0.9 * n:
            out[k] = "m"
    if endings:
        for k in seen - set(c):
            sx = ending_sex(k)
            if sx:
                out[k] = sx
    return out


def parents(s: dict, sex: dict[str, str] | None = None) -> dict[str, dict[str, str | None]]:
    """Vem som är förälder till vem på en sten, ur släktfakta: {barn: {förälder: 'm' (far), 'f' (mor) eller None}}.
    Far och mor står i släktordet; i 'hans son', 'hennes son' och 'Alfhildrs son' ger namnets kön (name_sex) vilken
    förälder det är."""
    sex = sex or {}
    out = defaultdict(dict)

    def add(child, parent, sx):
        if out[child].get(parent) is None:
            out[child][parent] = sx

    for a, rel, b in s["facts"]:
        if rel in PARENT:            # a is b's father/mother
            add(b, a, PARENT[rel])
        elif rel in CHILD:           # a is b's son/daughter
            add(a, b, sex.get(b))
        elif rel == "förälder till":  # a is b's parent (patronymic or metronymic)
            add(b, a, sex.get(a))
    return out


def _parent_conflict(pa: dict[str, str | None], pb: dict[str, str | None]) -> str | None:
    """Kan två stenars föräldrar till samma namn gälla samma person? Nej när de anger olika fäder eller olika mödrar,
    eller när den ena stenen anger båda föräldrarna och den andra en förälder som inte är någon av dem. En mor på den
    ena stenen och en far på den andra är ingen motsägelse. När könet på en av två olika föräldrar är okänt (name_sex
    vet inget) räknas det som en möjlig motsägelse: 'föräldrar, kön okänt'."""
    if not pa or not pb or set(pa) & set(pb):
        return None
    for sx, word in (("m", "fäder"), ("f", "mödrar")):
        if any(v == sx for v in pa.values()) and any(v == sx for v in pb.values()):
            return word
    if len(pa) >= 2 or len(pb) >= 2:
        return "föräldrar"
    if None in pa.values() or None in pb.values():
        return "föräldrar, kön okänt"
    return None


def contradictions(x: dict, st: dict[str, dict], sex: dict[str, str] | None = None) -> list[str]:
    """Varför två stenar inte kan gälla samma personer: olika fäder eller mödrar för samma namn (_parent_conflict), eller
    en person som är död på en äldre sten och reser en sten på en yngre. Tidsregeln kräver minst TIME_GAP år mellan
    stilgruppernas intervall och gäller inte stenar på samma plats eller stenar som Rundata knyter ihop: där säger
    texterna mer om ordningen än stilgrupperna (U 844 och U 845 vid Viggby bro). sex: name_sex(st), räknas annars här."""
    A, B = st[x["a"]], st[x["b"]]
    sex = name_sex(st) if sex is None else sex
    pa, pb = parents(A, sex), parents(B, sex)
    d = km(A, B)
    # the same site: within SAME_SITE_KM, or (without coordinates) the same place in the same parish
    same_site = d <= SAME_SITE_KM if d is not None else bool(A["place"] and A["place"] == B["place"]
                                                              and A["parish"] == B["parish"])
    timed = not same_site and not rundata_linked(A, B)
    out = []
    for k in x["shared"]:
        if k.startswith("plats:"):
            continue
        why = _parent_conflict(pa.get(k) or {}, pb.get(k) or {})
        if why:
            out.append(f"{k}: olika {why} ({', '.join(sorted(pa[k]))} / {', '.join(sorted(pb[k]))})")
        if not timed:
            continue
        role = lambda s, k: {p["role"] for p in s["persons"] if p["key"] == k}  # noqa: E731
        for old, new in ((A, B), (B, A)):
            if old["to"] is not None and new["from"] is not None and new["from"] - old["to"] >= TIME_GAP \
                    and "minnes" in role(old, k) and "resare" in role(new, k):
                out.append(f"{k}: död på {old['signum']} men resare på den yngre {new['signum']}")
    return out


def patterns(path: str) -> list[dict]:
    """Mönstren ur länkmodellen för Statistik (R) (märks Nytt via src/pattern_registry.py). Texten är hela meningar utan
    semikolon, resultatet först: översättningen (web/src/i18n) delar vid semikolon och slår upp varje mening för sig."""
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

    def listed(xs):  # "U 1041–Vs 22 (78 km) och U 1003–Vs 22 (84 km)": signa and kilometres only, so it needs no translation
        items = [f"{x['a']}–{x['b']}" + (f" ({x['km']:.0f} km)" if x.get("km") is not None else "") for x in xs]
        return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " och " + items[-1]

    strict = [x for x in cross if x.get("q_district", 1) < cut]
    loose = [x for x in cross if x.get("q_district", 1) >= cut]
    sents = [f"{d['n_sure']} länkar mellan runstenar håller (andel falska under {round(cut * 100)} %), och de står i "
             f"median {_d(d['km_median_sure'], 1)} km isär, {round(d['share_sure_within_10km'] * 100)} % inom 10 km."]
    iv = d.get("n_sure_interval")
    if iv and iv[0] != iv[1]:
        sents.append(f"Med slumpfelet i nollmodellen håller {iv[0]:.0f}–{iv[1]:.0f}, och {d['n_sure_robust']} av dem "
                     "ligger säkert under gränsen.")
    seeds = d.get("seeds") or []
    if seeds:
        ns = sorted({z["n_sure"] for z in seeds})
        sents.append(f"Med {len(seeds)} andra slumpfrön blir antalet detsamma." if ns == [d["n_sure"]]
                     else f"Med {len(seeds)} andra slumpfrön blir antalet mellan {min(ns + [d['n_sure']])} och "
                          f"{max(ns + [d['n_sure']])}.")
    sents.append("Familjerna som går att följa över flera stenar var lokala.")
    sents.append("Ingen länk över landskapsgränserna håller." if not cross
                 else "Över landskapsgränserna håller bara en länk." if len(cross) == 1
                 else f"Över landskapsgränserna håller bara {len(cross)} länkar.")
    if strict:
        sents.append(f"Den strängare prövningen inom häradet klarar: {listed(strict)}.")
    if loose:
        sents.append(f"Den strängare prövningen inom häradet klarar inte: {listed(loose)}.")
    if killed:
        kinds = [" ".join(x["contradictions"]) for x in killed]
        n_kin = sum(1 for c in kinds if "olika " in c)
        n_time = sum(1 for c in kinds if "död på" in c)
        sents.append((f"{len(killed)} länkar mellan landskap som först såg starka ut" if len(killed) > 1
                      else "En länk mellan landskap som först såg stark ut")
                     + f" avfärdas av motsägelser ({n_kin} i släktskapen, {n_time} i tiden).")
        sents.append("Släktskapen läses med regler och dateringen efter stilgrupper, så en motsägelse är ett skäl till "
                     "tvivel snarare än ett motbevis.")

    pairs_all = d.get("n_pairs_all")
    common = d.get("common_max", COMMON)
    left_out = (f" ({pairs_all - d['n_links']} par som bara delar namn på fler än {common} runstenar prövas inte)"
                if pairs_all and pairs_all > d["n_links"] else "")
    note = [f"Av {d['n_links']} par av runstenar som delar minst två namn eller ett gårdsnamn{left_out} ger slumpen "
            f"omkring {round(d['null_mean'])}.",
            "Namnen läses med regler ur Rundatas engelska översättning (src/entities.py) och vägs efter hur ovanliga de är.",
            f"Nollmodellen blandar namnen inom landskapet {d['n_null']} gånger, och ingen sten får samma namn två gånger.",
            f"I den strängare nollmodellen, där namnen blandas inom häradet, håller {d['n_sure_district']} länkar."]
    par = d["validation"]["parsten"]
    missed = par["n"] - par["found"]
    sh = [par.get(k) for k in ("missed_shared_none", "missed_shared_one", "missed_shared_two_plus")]
    note.append(f"Av Rundatas parstenar hittas {par['found']} av {par['n']}.")
    if missed and None not in sh:
        note.append(f"Av de {missed} som missas delar {sh[0]} inget läst namn alls, {sh[1]} bara ett namn och {sh[2]} två "
                    "eller fler utan att länken skiljer sig från slumpen.")
    noted = d["validation"].get("rundata_noted") or {}
    if noted.get("n"):
        note.append(f"Av de {noted['n']} par som Rundatas anmärkningar knyter ihop hittas {noted['found']}.")
    jar = d["validation"].get("jarlabanke") or {}
    if jar.get("q_max") is not None:
        jv = jar.get("q_max_interval")
        q = _d(jar["q_max"], 3)
        if jar["q_max"] < cut:
            jt = f"Jarlabankes fem stenar om Täby hittas (q högst {q}" + (
                f", {_d(jv[0], 3)}–{_d(jv[1], 3)} med slumpfelet)" if jv else ")")
            if not jar.get("stable", True):
                jt += ", men de ligger vid gränsen och beror på slumpen i nollmodellen"
        else:
            jt = (f"Jarlabankes fem stenar om Täby hittas inte: q högst {q}"
                  + (f", {_d(jv[0], 3)}–{_d(jv[1], 3)} med slumpfelet" if jv else "") + f", över gränsen {_d(cut, 2)}")
        note.append(jt + ".")
    note.append(f"Olika fäder eller olika mödrar för samma namn, eller en person som är död på en sten och reser en sten "
                f"som är minst {d.get('time_gap', TIME_GAP)} år yngre efter stilgrupperna (inte på samma plats och inte "
                "när Rundata knyter ihop stenarna), avfärdar en länk.")
    note.append("Förälderns kön tas ur släktorden, ur pronomenet (hans eller hennes son) och annars ur namnets ändelse, "
                "och två olika föräldrar där könet är okänt räknas som en möjlig motsägelse.")
    return [{"key": "links_local", "topic": "Släkter över stenar", "status": "mönster att pröva",
             # the result first: the panel of new patterns shows the first sentence
             "text": " ".join(sents), "note": " ".join(note),
             "significance": significance(None, test="nollmodell med blandade namn (andel falska länkar per länk)")}]
