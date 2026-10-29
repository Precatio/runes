"""Robusthetstrappan (METHODS.md 1v): samma steg för varje mönster i Statistik (R) som kan räknas om sten för sten.

Mönstren kommer ur olika moduler med olika test (r/change.R, r/hotspots.R, r/geography.R, r/messages.R, r/people.R).
Trappan lägger samma kontroller på alla, så att det går att jämföra hur väl de håller (r/robustness.R): rått, justerat
för landskap och tid, ristaren som slumpeffekt, socknen som slumpeffekt, platsen som yta, båda halvorna av korpusen,
utan ett landskap i taget och utan flyttade stenar (enligt Rundata och enligt Runor 2020). Därtill skillnaden i
procentenheter, en modellkontroll (DHARMa) och – där en regel kodar utfallet och det finns ett handkodat facit –
kodningsfelen förda vidare in i resultatet.

Varje mönster blir ett samband y ~ x på stenarna:
  Förändring        draget mot tiden (stilgruppens mittår i 50-årssteg; 1000 mot 1100), justerat för landskapet
  Regional skillnad draget i det visade paret av landskap, justerat för tiden
  Samband           draget mot stentypen (själsbön på brostenar), justerat för landskap och tid
  hot spot          draget inom klustrets radie mot utanför, justerat för tiden
  cult_prayer       bön inom 2 km från ett teoforiskt ortnamn, justerat för landskap och tid
  Budskap           budskapet i Götaland mot Svealand, justerat för tiden
  Människorna       som i r/people.R, justerat för landsdel och tid
Trappan använder samma tidsskikt för alla mönster (src/question.EPOCHS), så de justerade stegen kan skilja sig något
från modulens egen siffra. Mönster som prövas på annat sätt (avstånd mot slumppunkter, attribueringar, seriation,
kluster av ristare) får ingen trappa och behåller sitt eget test.

Två saker läggs på alla mönster (annotate):
  * En gemensam Benjamini–Hochberg över alla visade mönster: trappans justerade p där trappan finns, annars mönstrets
    eget p (eller q, vilket är försiktigt). Där jämförelsen själv valdes ur datan (hot spots, det landskapspar som
    skilde sig mest) det största av trappans p och mönstrets eget. q_global är vad mönstret kostar när man ser alla
    mönster samtidigt.
  * Bekräftat: samma riktning och p < 0,05 i båda halvorna av korpusen och q_global < 0,05. Halvorna är fasta (hela
    socknar växelvis inom landskapet, src/question.halves) och bestäms oberoende av mönstren. Ett nytt mönster märks
    "Nytt" först när det är bekräftat; innan dess "Nytt, obekräftat" (src/pattern_registry.annotate).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import threading

from src import question
from src.stone_size import bh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALPHA = 0.05
CULT_KM = 2.0  # radien i r/geography.R (vald i förväg)
N_SIM = 200
_lock = threading.Lock()

# r/change.R:s drag: kolumn, ja-värden, nej-värden, bara läsbara stenar
FEATURES = {
    "ai_alla": ("trait_ai_alla", {"monoftong", "båda"}, {"diftong"}, False),
    "au_och": ("trait_au_och", {"monoftong"}, {"auk"}, False),
    "r_for_R": ("trait_r_for_R", {"r för ʀ", "båda"}, {"ʀ-runa"}, False),
    "o_runa": ("trait_o_runa", {"o-runa", "båda"}, {"u-runa"}, False),
    "h": ("trait_h_bortfall", {"h saknas"}, {"h skrivet"}, False),
    "nasal": ("trait_nasal", {"skriven"}, {"utelämnad"}, False),
    "preposition": ("trait_preposition", {"at", "båda"}, {"æftiR"}, False),
    "stungna": ("trait_stungna", {"ja"}, {"nej"}, False),
    "stungen_e": ("trait_stungen_e", {"ja"}, {"nej"}, False),
    "stungen_y": ("trait_stungen_y", {"ja"}, {"nej"}, False),
    "stungen_g": ("trait_stungen_g", {"ja"}, {"nej"}, False),
    "bon": ("trait_bon", {"ja"}, {"nej"}, False),
    "sjal": ("trait_sjal", {"ja"}, {"nej"}, False),
    "cross": ("cross", {1}, {0}, True),
    "bro": ("cat_bro_vag", {1}, {0}, True),
    "signatur": ("trait_signatur", {"ja"}, {"nej"}, False),
}
ASSOC = {"bro_bon": ("bon", "bro"), "bro_sjal": ("sjal", "bro"), "bro_cross": ("cross", "bro")}
REGION = None  # src.messages.REGION, laddas vid behov

RUNG_LABELS = {
    "raw": "Rått, ingenting justerat",
    "adjusted": "Justerat för landskap och tid",
    "carver": "Ristaren som slumpeffekt",
    "parish": "Socknen som slumpeffekt",
    "place": "Platsen som yta (utan flyttade stenar)",
    "half_A": "Korpusens halva A",
    "half_B": "Korpusens halva B",
    "lopo": "Utan ett landskap i taget",
    "moved_rundata": "Utan flyttade stenar (Rundata)",
    "moved_runor": "Utan flyttade stenar (Rundata och Runor 2020)",
}


def _coerce(v: str):
    if v == "":
        return None
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v


def read_corpus(path: str) -> list[dict]:
    """Korpusraderna ur jobbets corpus.csv (samma rader som fingeravtrycket), med tal som tal."""
    with open(path, encoding="utf-8", newline="") as fh:
        return [{k: _coerce(v) for k, v in r.items()} for r in csv.DictReader(fh)]


def _feature(key: str):
    col, yes, no, legible = FEATURES[key]

    def get(r):
        if legible and r.get("trait_bon") in (None, ""):
            return None
        v = r.get(col)
        return 1 if v in yes else (0 if v in no else None)
    return get


def _runor_moved() -> set[str]:
    """Stenar som Riksantikvarieämbetets Runor 2020 anger som inte på ursprunglig plats (original = nej)."""
    path = os.path.join(ROOT, "data", "raa", "runor_2020.json")
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return set()
    recs = d.get("inscriptions", []) if isinstance(d, dict) else d
    return {x["signum"] for x in recs if isinstance(x, dict) and x.get("original") is False and x.get("signum")}


def _haversine(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(min(1.0, a)))


# --- facit för regelkodningen (punkt 4) ---

def _confusion(pairs: list[tuple[int, int]]) -> dict:
    """(regel, hand) -> rätt och fel bland regelns ja (ppv) och bland dess nej (npv)."""
    tp = sum(1 for r, h in pairs if r == 1 and h == 1)
    fp = sum(1 for r, h in pairs if r == 1 and h == 0)
    tn = sum(1 for r, h in pairs if r == 0 and h == 0)
    fn = sum(1 for r, h in pairs if r == 0 and h == 1)
    return {"ppv": [tp, fp], "npv": [tn, fn], "n": len(pairs)}


def message_facit(msg: dict[str, dict]) -> dict[str, dict]:
    """Regelns budskap mot handkodningarna (data/messages_facit_ost.csv, utdata/brittiska/hemma_kodning.csv), per
    budskap; samma underlag som scripts/check_messages.py."""
    hand: dict[str, dict[str, int]] = {}
    east = os.path.join(ROOT, "data", "messages_facit_ost.csv")
    west = os.path.join(ROOT, "utdata", "brittiska", "hemma_kodning.csv")
    if os.path.exists(east):
        for r in csv.DictReader(open(east, encoding="utf-8")):
            hand.setdefault(r["signum"], {}).update(
                {k: int(r[k]) for k in ("resa", "dod_borta", "dod_uppgift") if r.get(k) in ("0", "1")})
    if os.path.exists(west):
        for r in csv.DictReader(open(west, encoding="utf-8")):
            if r.get("utfall") == "utesluten":
                continue
            hand.setdefault(r["signum"], {}).setdefault("resa", 1)
            hand[r["signum"]].setdefault("dod_borta", int(r["utfall"] == "dog"))
    out = {}
    for k in ("resa", "dod_borta", "dod_uppgift"):
        pairs = [(msg[s][f"msg_{k}"], h[k]) for s, h in hand.items()
                 if k in h and s in msg and msg[s].get(f"msg_{k}") is not None]
        if pairs:
            out[k] = _confusion(pairs)
    return out


def people_facit(people_rows: dict[str, dict]) -> dict[str, dict]:
    """En kvinna bland resarna: regeln (src/people.py) mot handkodningen av 100 slumpvisa stenar i två urval
    (data/people_check.json; urval 2 kodades blint, före jämförelsen)."""
    path = os.path.join(ROOT, "data", "people_check.json")
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return {}
    k = {**(d.get("kodning") or {}), **(d.get("kodning2") or {})}
    pairs = [(int((people_rows[s].get("resare_k") or 0) > 0), int((h.get("resare_k") or 0) > 0))
             for s, h in k.items() if s in people_rows and (people_rows[s].get("n_resare") or 0) >= 1]
    return {"kvinna": _confusion(pairs)} if pairs else {}


# --- underlaget ---

def _base(rows: list[dict], runor: set[str]) -> dict[str, dict]:
    prep = question.prepare(rows)
    by = {r["signum"]: r for r in rows}
    out = {}
    for s in prep["stones"]:
        r = by[s["signum"]]
        out[s["signum"]] = {**s, "row": r, "parish": f"{s['province']}:{r.get('parish') or s['signum']}",
                            "moved_runor": int(s["signum"] in runor)}
    return out


def _line(b: dict, y, x) -> dict:
    return {"signum": b["signum"], "y": y, "x": x, "province": b["province"], "epoch": b["epoch"], "half": b["half"],
            "hand": b["hand"], "parish": b["parish"], "xk": b["xk"], "yk": b["yk"], "moved": b["moved"],
            "moved_runor": b["moved_runor"]}


def _region(province: str) -> str:
    global REGION
    if REGION is None:
        from src.messages import REGION as R
        REGION = R
    return REGION.get(province, "")


def build(rows: list[dict], patterns: list[dict], hotspots: dict | None, msg_rows: list[dict],
          people_rows: list[dict], runor: set[str] | None = None) -> tuple[list[dict], list[dict], dict]:
    """Raderna (en per mönster och sten), specifikationerna för r/robustness.R och facit för kodningen."""
    base = _base(rows, runor if runor is not None else _runor_moved())
    msg = {m["signum"]: m for m in msg_rows}
    ppl = {p["signum"]: p for p in people_rows}
    mfac, pfac = message_facit(msg), people_facit(ppl)
    clusters = {}
    for hp in (hotspots or {}).get("patterns") or []:
        for c in hp.get("clusters") or []:
            clusters[f"hotspot_{hp['key']}_{c['center']}"] = (hp["key"], c)
    lines: list[dict] = []
    specs: list[dict] = []

    def add(pid: str, pairs, adjust, *, x_lo=0, x_hi=1, lopo=True, place=True, moved=False, coding=None, note=None,
            selected=False):
        pairs = [(b, y, x) for b, y, x in pairs if y is not None and x is not None]
        if not pairs:
            return
        lines.extend({"pattern": pid, **_line(b, y, x)} for b, y, x in pairs)
        sp = {"id": pid, "adjust": adjust, "x_lo": x_lo, "x_hi": x_hi, "lopo": lopo, "place": place, "moved": moved,
              "selected": selected}
        if coding:
            sp["coding"] = {**coding, "n_sim": N_SIM}
        if note:
            sp["note"] = note
        specs.append(sp)

    t50 = lambda b: None if b["year"] is None else round((b["year"] - 1050) / 50, 4)  # noqa: E731
    cult = None
    for p in patterns:
        topic, key = p.get("topic"), p.get("key") or ""
        pid = f"{topic}|{key}"
        if topic == "Förändring" and key in FEATURES:
            f = _feature(key)
            add(pid, [(b, f(b["row"]), t50(b)) for b in base.values()], ["province"], x_lo=-1, x_hi=1)
        elif topic == "Regional skillnad" and key in FEATURES and len(p.get("pair") or []) == 2:
            hi, lo = p["pair"]
            f = _feature(key)
            add(pid, [(b, f(b["row"]), int(b["province"] == hi)) for b in base.values() if b["province"] in (hi, lo)],
                ["epoch"], lopo=False, place=False, moved=True, selected=True,
                note=f"{hi} mot {lo}, det par som skilde sig mest (paret är utvalt)")
        elif topic == "Samband" and key in ASSOC:
            fy, fx = (_feature(k) for k in ASSOC[key])
            add(pid, [(b, fy(b["row"]), fx(b["row"])) for b in base.values()], ["province", "epoch"])
        elif key in clusters:
            vkey, c = clusters[key]
            if vkey not in question.VAR:
                continue
            fn = question.VAR[vkey][3]
            inside = lambda b: None if b["row"].get("lat") is None else int(  # noqa: E731
                _haversine(c["lat"], c["lon"], b["row"]["lat"], b["row"]["lon"]) <= c["radius_km"])
            add(pid, [(b, fn(b["row"]), inside(b)) for b in base.values() if not b["moved"]], ["epoch"],
                lopo=False, place=False, moved=True, selected=True,
                note="klustret valdes på hela korpusen; trappan prövar inte valet av kluster")
        elif key == "cult_prayer":
            if cult is None:
                from src import places
                stones = [b for b in base.values() if b["row"].get("lat") is not None]
                dist, _ = places.nearest("cult_a", [b["row"]["lat"] for b in stones], [b["row"]["lon"] for b in stones])
                cult = {b["signum"]: d for b, d in zip(stones, dist)}
            f = _feature("bon")
            add(pid, [(b, f(b["row"]), None if cult.get(b["signum"]) is None else int(cult[b["signum"]] <= CULT_KM))
                      for b in base.values() if not b["moved"]], ["province", "epoch"], place=False, moved=True)
        elif topic == "Budskap" and key in ("messages_praise", "messages_travel_less", "messages_travel_death"):
            def got(b):
                return int(_region(b["province"]) == "Götaland") if _region(b["province"]) in ("Götaland", "Svealand") else None
            m = lambda b, k: (msg.get(b["signum"]) or {}).get(f"msg_{k}")  # noqa: E731
            if key == "messages_praise":
                add(pid, [(b, m(b, "berom"), got(b)) for b in base.values()], ["epoch"], place=False, moved=False,
                    note="beröm är inte kontrollerat mot en handkodning")
            elif key == "messages_travel_less":
                add(pid, [(b, m(b, "resa"), got(b)) for b in base.values()], ["epoch"], place=False,
                    coding={"var": "y", **mfac["resa"]} if "resa" in mfac else None)
            else:
                add(pid, [(b, m(b, "dod_borta"), got(b)) for b in base.values() if m(b, "resa") == 1], ["epoch"],
                    place=False, coding={"var": "y", **mfac["dod_borta"]} if "dod_borta" in mfac else None)
        elif topic == "Människorna" and key.startswith("people_"):
            def pr(b):
                q = ppl.get(b["signum"])
                return q if q and q.get("legible") == 1 and q.get("region") in ("Svealand", "Götaland", "Gotland", "Norrland") else None

            def ung(q):
                young = (q["rel_barn"] or q["rel_syskon"]) and not (q["rel_foralder"] or q["rel_make"])
                older = (q["rel_foralder"] or q["rel_make"]) and not (q["rel_barn"] or q["rel_syskon"])
                return 1 if young else (0 if older else None)

            def men(q):
                return q["doda_k"] == 0 and q["doda_m"] >= 1
            st = [(b, pr(b)) for b in base.values() if pr(b)]
            kv = lambda q: int(q["resare_k"] > 0)  # noqa: E731
            kfac = {"var": "y", **pfac["kvinna"]} if "kvinna" in pfac else None
            if key == "people_kvinna_landsdel":
                add(pid, [(b, kv(q), int(q["region"] == "Götaland")) for b, q in st
                          if q["n_resare"] >= 1 and q["region"] in ("Svealand", "Götaland")], ["epoch"],
                    place=False, coding=kfac)
            elif key == "people_kvinna_tid":
                add(pid, [(b, kv(q), t50(b)) for b, q in st if q["n_resare"] >= 1], ["province"], x_lo=-1, x_hi=1,
                    coding=kfac)
            elif key in ("people_drengr_ung", "people_thegn_ung", "people_dod_borta_ung"):
                col = {"people_drengr_ung": "drengr", "people_thegn_ung": "thegn", "people_dod_borta_ung": "dod_borta"}[key]
                add(pid, [(b, q.get(col), ung(q)) for b, q in st if men(q)], ["province", "epoch"],
                    coding=({"var": "y", **mfac["dod_borta"]} if col == "dod_borta" and "dod_borta" in mfac else None))
            elif key == "people_bro_kvinna":
                fb = _feature("bro")
                add(pid, [(b, fb(b["row"]), kv(q)) for b, q in st if q["n_resare"] >= 1], ["province", "epoch"],
                    coding={"var": "x", **pfac["kvinna"]} if "kvinna" in pfac else None)
    return lines, specs, {"messages": mfac, "people": pfac}


def _csv(lines: list[dict]) -> bytes:
    cols = ["pattern", "signum", "y", "x", "province", "epoch", "half", "hand", "parish", "xk", "yk", "moved",
            "moved_runor"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in lines:
        w.writerow({k: ("" if r.get(k) is None else r[k]) for k in cols})
    return buf.getvalue().encode("utf-8")


def path(fp: str) -> str:
    from src import r_bridge as rb
    return os.path.join(rb.JOB.directory(fp), "robustness.json")


def run(fp: str, patterns: list[dict]) -> dict:
    """Bygger underlaget ur korpusjobbets filer och kör r/robustness.R; resultatet sparas i jobbets mapp
    (robustness.json) med en nyckel över underlag och skript, så att samma trappa räknas en gång."""
    from api.rundata import store
    from src import messages, people, r_bridge as rb
    d = rb.JOB.directory(fp)
    rows = read_corpus(os.path.join(d, "corpus.csv"))
    try:
        with open(os.path.join(d, "hotspots.json"), encoding="utf-8") as fh:
            hotspots = json.load(fh)
    except (OSError, ValueError):
        hotspots = None
    ins = store().inscriptions
    lines, specs, facit = build(rows, patterns, hotspots, messages.rows(ins), people.rows(ins))
    data = _csv(lines)
    key = hashlib.sha256(data + json.dumps(specs, sort_keys=True).encode()
                         + rb._scripts_hash(["robustness.R"]).encode()).hexdigest()[:16]
    out = path(fp)
    with _lock:
        old = load(fp)
        if old and old.get("key") == key:
            return old
        work = os.path.join(d, "robustness")
        os.makedirs(work, exist_ok=True)
        with open(os.path.join(work, "data.csv"), "wb") as fh:
            fh.write(data)
        res = rb.run_module("robustness", {"data": os.path.join(work, "data.csv"), "specs": specs, "seed": 2026},
                            work, timeout=3600)
        res = {**res, "key": key, "facit": facit, "specs": {s["id"]: s for s in specs}}
        tmp = out + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False)
        os.replace(tmp, out)
        return res


_started: set[str] = set()


def start(fp: str, patterns: list[dict]) -> bool:
    """Räknar trappan i en bakgrundstråd, en gång per version av data och serverprocess."""
    with _lock:
        if fp in _started:
            return False
        _started.add(fp)

    def work():
        try:
            run(fp, patterns)
        except Exception as e:  # noqa: BLE001 – the patterns are shown without the ladder
            import logging
            logging.getLogger(__name__).warning("Robusthetstrappan misslyckades: %s", e)
    threading.Thread(target=work, daemon=True, name=f"robustness-{fp}").start()
    return True


def load(fp: str) -> dict | None:
    try:
        with open(path(fp), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


# --- på mönstren ---

def summarize(r: dict, spec: dict | None) -> dict | None:
    """Trappan för ett mönster i den form sidan visar: stegen i ordning, hur många som håller, effekten i
    procentenheter, modellkontrollen och kodningsfelen."""
    if not r or r.get("error") or not (r.get("rungs") or {}).get("adjusted"):
        return None
    adj = r["rungs"]["adjusted"]
    if adj.get("error") or adj.get("skipped") or adj.get("p") is None:
        return None
    rungs = []
    for k, label in RUNG_LABELS.items():
        x = (r.get("rungs") or {}).get(k)
        if not x:
            continue
        item = {"key": k, "label": label, "holds": x.get("holds"), "or": x.get("or"), "ci": x.get("ci"),
                "p": x.get("p"), "n": x.get("n")}
        if x.get("error"):
            item["error"] = x["error"]
        if x.get("skipped"):
            item["skipped"] = x["skipped"]
        if k == "lopo":
            item["without"] = x.get("without")
            item["n_provinces"] = x.get("n_provinces")
            item["flips"] = x.get("flips") or []
        if k in ("carver", "parish"):
            item["singular"] = x.get("singular")
        rungs.append(item)
    tested = [x for x in rungs if x["holds"] is not None]
    halves = [x for x in rungs if x["key"] in ("half_A", "half_B")]
    out = {"n": r.get("n"), "k": r.get("k"), "direction": r.get("direction"), "p": adj["p"], "rungs": rungs,
           "passed": sum(1 for x in tested if x["holds"]), "tested": len(tested),
           "halves": len(halves) == 2 and all(x["holds"] for x in halves),
           "effect": r.get("effect"), "check": r.get("check"), "coding": r.get("coding"),
           "time": (spec or {}).get("x_lo") == -1, "note": (spec or {}).get("note"),
           "selected": bool((spec or {}).get("selected"))}
    first = next((x for x in rungs if x["holds"] is False), None)
    out["first_fail"] = first["key"] if first else None
    return out


def _own_p(p: dict) -> float | None:
    s = p.get("significance") or {}
    v = s.get("value")
    return v if isinstance(v, (int, float)) and s.get("kind") in ("p", "q") and 0 <= v <= 1 else None


def annotate(patterns: list[dict], rob: dict | None) -> list[dict]:
    """Mönstren med trappan (ladder), en gemensam BH över alla visade mönster (q_global) och om mönstret är bekräftat
    (confirmed: båda halvorna och q_global < 0,05; utan trappa mönstrets egen halvprovning)."""
    res = (rob or {}).get("patterns") or {}
    specs = (rob or {}).get("specs") or {}
    out = []
    for p in patterns:
        pid = f"{p.get('topic')}|{p.get('key')}"
        lad = summarize(res.get(pid), specs.get(pid)) if pid in res else None
        out.append({**p, "ladder": lad} if lad else dict(p))
    # Where the comparison itself was chosen on the data (a hot spot, the regional pair that differed most) the
    # ladder's p does not know about the choice: the pattern's own p (the scan statistic, the pair) is used when larger
    ps = [(max(q["ladder"]["p"], _own_p(q) or 0) if q.get("ladder") and q["ladder"]["selected"] else
           q["ladder"]["p"] if q.get("ladder") else _own_p(q)) for q in out]
    qs = bh(ps)
    for q, pv, qv in zip(out, ps, qs):
        q["q_global"] = qv
        if q.get("ladder"):
            q["confirmed"] = bool(q["ladder"]["halves"] and qv is not None and qv < ALPHA)
        elif q.get("replicated") is not None and qv is not None:
            q["confirmed"] = bool(q["replicated"] and qv < ALPHA)
        else:
            q["confirmed"] = None  # no split-half test for this kind of pattern
    return out


def summary(patterns: list[dict]) -> dict:
    """Hur många mönster som har en trappa, hur många som håller hela vägen, och den gemensamma justeringen."""
    lad = [p for p in patterns if p.get("ladder")]
    return {"n_patterns": len(patterns), "n_ladder": len(lad),
            "all_rungs": sum(1 for p in lad if p["ladder"]["passed"] == p["ladder"]["tested"]),
            "confirmed": sum(1 for p in patterns if p.get("confirmed")),
            "n_fdr": sum(1 for p in patterns if p.get("q_global") is not None),
            "fdr_ok": sum(1 for p in patterns if (p.get("q_global") or 1) < ALPHA)}
