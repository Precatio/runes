"""Ristarattribueringar i litteraturen som Rundatas ristarfält saknar (data/carver_literature.json), för de möjliga
okända ristarnas grupper (r/anonymous.R). En grupp där litteraturen redan knyter minst hälften av stenarna till en
ristare är "beskriven", en där den knyter några är "delvis beskriven", och en vars stenar är genomlästa utan träff har
"inget i litteraturen". Grupper som inte är genomlästa får "inte kontrollerad". Gruppen matchas på stenarna, inte på
numret, eftersom numren kan ändras när korpusen räknas om."""
import json
import os

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "carver_literature.json")
CHECKED_SHARE = 0.6  # a group counts as read when this share of its stones has been looked up (n_read says how many)
_cache: tuple[float, dict] | None = None


def load() -> dict:
    global _cache
    try:
        mtime = os.path.getmtime(PATH)
    except OSError:
        return {}
    if _cache is None or _cache[0] != mtime:
        with open(PATH, encoding="utf-8") as fh:
            _cache = (mtime, json.load(fh))
    return _cache[1]


def attributions(lit: dict | None = None) -> list[dict]:
    """SRI:s och Källströms attribueringar, och Källströms namngivna signaturer som Rundata saknar (signatures) som
    attribueringar av slaget "signerad", utom där en attribuering redan gäller stenen."""
    lit = load() if lit is None else lit
    out = list(lit.get("attributions") or [])
    have = {s for a in out for s in a["stones"]}
    for x in lit.get("signatures") or []:
        if x["signum"] not in have:
            out.append({"stones": [x["signum"]], "carver": x["carver"], "kind": "signerad", "source": x["source"],
                        "page": x["page"], "text": f"Signerad: {x['text']} ({x['type']} i Källströms katalog)."})
    return out


def carver_for(signum: str, lit: dict | None = None) -> dict | None:
    """Ristaren enligt litteraturen för en sten som Rundata saknar ristare för, eller None."""
    lit = load() if lit is None else lit
    sources = lit.get("sources") or {}
    for a in attributions(lit):
        if signum in a["stones"]:
            others = [x for x in a["stones"] + a.get("outside", []) if x != signum]
            return {"carver": a.get("carver"), "kind": a.get("kind"), "same_as": others,
                    "reference": f"{a['source']} {a['page']}", "source_full": sources.get(a["source"]), "text": a.get("text")}
    return None


def for_group(stones: list[str], lit: dict | None = None) -> dict:
    """Vad litteraturen säger om gruppens stenar: status, attribueringarna som rör dem och hur många stenar de täcker."""
    lit = load() if lit is None else lit
    group = set(stones)
    hits = [a for a in attributions(lit) if group & set(a["stones"])]
    covered = sorted(group & {s for a in hits for s in a["stones"]})
    checked = set((lit.get("checked") or {}).get("stones") or [])
    read = len(group & checked) / len(group) if group else 0
    if covered and len(covered) >= len(group) / 2:
        status = "beskriven"
    elif covered:
        status = "delvis beskriven"
    elif read >= CHECKED_SHARE:
        status = "inget i litteraturen"
    else:
        status = "inte kontrollerad"
    sources = lit.get("sources") or {}
    return {"status": status, "covered": covered, "n_covered": len(covered), "n_read": len(group & checked),
            "attributions": [{**a, "stones": [s for s in a["stones"] if s in group],
                              "reference": f"{a['source']} {a['page']}", "source_full": sources.get(a["source"])}
                             for a in hits],
            "nearby_signed": [x for x in lit.get("nearby_signed") or [] if x.get("anchor") in group],
            "not_read": (lit.get("checked") or {}).get("not_read")}


def by_stone(lit: dict | None = None) -> dict[str, dict]:
    """Signum -> attribueringen som gäller stenen."""
    lit = load() if lit is None else lit
    return {s: a for a in attributions(lit) for s in a["stones"]}


def annotate(anon: dict) -> dict:
    """De okända ristarnas resultat med litteraturen på varje grupp (en kopia)."""
    if not anon or not anon.get("groups"):
        return anon
    lit = load()
    return {**anon, "groups": [{**g, "literature": for_group(list(g.get("stones") or []), lit)} for g in anon["groups"]]}


def pair_test(anon: dict, corpus_dir: str) -> dict | None:
    """Hamnar två stenar som litteraturen knyter till samme ristare i samma grupp oftare än grannar på samma avstånd?
    Paren är alla par inom en attribuering (stenar i och utanför gruppen) där båda stenarna ingår i metodens underlag
    (ingen ristare i Rundata, minst fem ord, koordinater). Väntat antal: för varje par andelen av den första stenens
    grannar i samma landskap, inom parets avstånd (minst 2 km), som ligger i samma grupp som den. Därtill grupper som
    rymmer två olika signerade ristare enligt litteraturen. Beskrivande, inget test (utdata/okanda_ristare/sri_par.py)."""
    import csv
    import math

    import numpy as np
    from pyproj import Transformer
    path = os.path.join(corpus_dir, "corpus.csv")
    if not anon or not anon.get("groups") or not os.path.exists(path):
        return None
    grp = {s: g["id"] for g in anon["groups"] for s in g["stones"]}
    rows = {r["signum"]: r for r in csv.DictReader(open(path, encoding="utf-8"))}
    pool = [s for s, r in rows.items() if r["lat"] and not r["carver"] and r["has_carver"] == "0"
            and int(r["n_words"] or 0) >= 5]
    if not pool:
        return None
    tf = Transformer.from_crs(4326, 3006, always_xy=True)
    xs, ys = tf.transform([float(rows[s]["lon"]) for s in pool], [float(rows[s]["lat"]) for s in pool])
    P = np.c_[xs, ys] / 1000
    idx = {s: i for i, s in enumerate(pool)}
    prov = np.array([rows[s]["province"] for s in pool])
    g = np.array([grp.get(s, -1) for s in pool])
    lit = load()
    n = same = 0
    expected = 0.0
    for a in attributions(lit):
        st = [s for s in a["stones"] + a.get("outside", []) if s in idx]
        for i in range(len(st)):
            for j in range(i + 1, len(st)):
                x, y = idx[st[i]], idx[st[j]]
                d = math.dist(P[x], P[y])
                dist = np.hypot(*(P - P[x]).T)
                m = (dist <= max(d, 2)) & (dist > 0) & (prov == prov[x])
                n += 1
                same += int(g[x] != -1 and g[x] == g[y])
                expected += float((g[m] == g[x]).mean()) if m.sum() and g[x] != -1 else 0.0
    signed = [a for a in attributions(lit) if a.get("kind", "").startswith("signerad") and a.get("carver")]
    merged = []
    for gid in {grp.get(s) for a in signed for s in a["stones"] if s in grp}:
        names = sorted({a["carver"] for a in signed for s in a["stones"] if grp.get(s) == gid})
        if len(names) > 1:
            merged.append({"group": gid, "carvers": names})
    return {"n_pairs": n, "same_group": same, "expected_from_neighbours": round(expected, 1), "merged": merged}


def annotate_with_pairs(anon: dict, fp: str | None) -> dict:
    """annotate() och, när korpusens mapp är känd, parprovet (literature_pairs)."""
    out = annotate(anon)
    if out and out.get("groups") and load().get("signature_coverage"):
        out = {**out, "signature_coverage": load()["signature_coverage"]}
    if fp and out and out.get("groups"):
        from src import r_bridge as rb
        pt = pair_test(out, rb.JOB.directory(fp))
        if pt:
            out = {**out, "literature_pairs": pt}
    return out
