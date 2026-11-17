"""De danska runstenarna (låst plan analysplaner/2026-11-17-danska-runstenar.md, sha dd9f1ad3, och tillägg 1 om
budskapet, sha 8f32a977): del A (det kända, beskrivande), del M (M1 följet, M2 striden, M3 ämbetet), del B (B1 kyrkan,
B2 monumentet, B3 kvinnor som reser) och del C (beskrivande). Danmark mot Sverige, Mantel–Haenszel över tidsskikten,
Holm inom M och inom B. Skriver resultat.json och traffar.json (alla danska träffar, för läsning för hand).
    PYTHONPATH=. .venv/bin/python utdata/danmark/analys.py"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import nordic as nd  # noqa: E402
from src import people  # noqa: E402
from src.pattern_map import pagan  # noqa: E402
from src.stats import wilson  # noqa: E402

PLANER = {"analysplaner/2026-11-17-danska-runstenar.md": "dd9f1ad3",
          "analysplaner/2026-11-17-danska-runstenar-tillagg-1-budskapet.md": "8f32a977"}
for p, sha in PLANER.items():
    assert open(os.path.join(ROOT, p.replace(".md", ".sha256"))).read().startswith(sha), p

KYRKA = re.compile(r"kyrk|kirke|kirche|vapenhus|våbenhus|kapell|kapel|kyrkogård|kirkegård|kirchhof|kirkedige", re.I)
MUSEUM = re.compile(r"museum|museet|samling", re.I)
MONUMENT = re.compile(r"\bmounds?\b|\bthese stones\b|\bthose stones\b|\bboth stones\b|\bstone-setting"
                      r"|\bship\b[^.;]{0,20}\b(setting|stones)\b|\bmonuments?\b", re.I)
STRID = re.compile(r"\bfell\b|\bfought\b|\bbattle\b|\bbesieged\b|\bwhen kings\b|\bin the fight|\bdied in (?:the )?(?:battle|fight)"
                   r"|\bwas killed\b|\bslain\b", re.I)
AMBETE_TR = re.compile(r"\bsteward\b|\blanded[- ]man\b|\bretainer\b|\bhousehold\b|\bhelmsman\b|\bcaptain\b|\bchieftain\b"
                       r"|\bpriest\b|\bgoði\b|\bking's\b|\bqueen\b|\bjarl\b|\bearl\b", re.I)
AMBETE_NO = re.compile(r"\bbryti|\bgoði|\bgoþi|\blandmann|\bhirð|\bstýrima|\bstyrima", re.I)
KUNG = re.compile(r"\bking\b", re.I)
KUNG_NO = re.compile(r"konungr|kunungr", re.I)

rd = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
stones = [r for r in rd if nd.is_runestone(r) and nd.land_of(r) in ("danmark", "sverige")]
lex = people.lexicon(rd)
OST = {"dk_oarna", "dk_skane", "dk_bornholm"}


def land(r):
    return "DK" if nd.land_of(r) == "danmark" else "SE"


def norm(r):
    return (r.get("normalization") or "") + " " + (r.get("normalization_ows") or "")


def code(r):
    """Planens koder för en sten: 1, 0 eller None (ej tillämplig)."""
    ft = nd.features(r)
    tr = r.get("translation_en") or ""
    pt = nd.patterns(r, ft)
    ps = people.stone(r, lex)
    platstext = " ".join(r.get(k) or "" for k in ("place", "placement", "other"))
    las = ft is not None
    rel_any = any(ps[f"rel_{g}"] for g, _ in people.GROUPS)
    kon = ps["resare_k"] + ps["resare_m"]
    c = {f"A_{k}": pt.get(k) for k in ("kristen", "bon", "hednisk", "titel", "kumbl", "bro", "fard", "arv")}
    c.update({f"A_{k}": (ft[k] if las else None) for k in ("placed", "raised", "had")})
    c.update({
        "M1_foljet": (ps["rel_ej_slakt"] if rel_any else None) if las else None,
        "M2_striden": int(bool(STRID.search(tr))) if las else None,
        "M3_ambetet": int(bool(AMBETE_TR.search(tr) or AMBETE_NO.search(norm(r)))) if las else None,
        "B1_kyrkan": int(bool(KYRKA.search(platstext))),
        "B2_monumentet": int(bool(nd.NORM_KUMBL.search(norm(r)) or MONUMENT.search(tr))) if las else None,
        "B3_kvinna_reser": (int(ps["resare_k"] > 0) if kon else None) if las else None,
        "C_museum": int(bool(MUSEUM.search(r.get("placement") or ""))),
        "C_kung": int(bool(KUNG.search(tr) or KUNG_NO.search(norm(r)))) if las else None,
    })
    return c


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: (ps[i] is None, ps[i] if ps[i] is not None else 1))
    out, run = [None] * len(ps), 0.0
    m = sum(p is not None for p in ps)
    for rank, i in enumerate(order):
        if ps[i] is None:
            continue
        run = max(run, min(1.0, (m - rank) * ps[i]))
        out[i] = run
    return out


rows = []
for r in stones:
    y = nd.year_of(r)
    rows.append({"signum": r["signum"], "land": land(r), "realm": nd.realm_of(r) if land(r) == "DK" else None,
                 "bin": nd.bin_of(y), "code": code(r), "rec": r})
BINS = [b[0] for b in nd.BINS]


def share(rs, k):
    v = [x["code"][k] for x in rs if x["code"][k] is not None]
    n, a = len(v), sum(v)
    lo, hi = wilson(a, n) if n else (None, None)
    return {"a": a, "n": n, "andel": round(a / n, 4) if n else None, "wilson95": [lo, hi]}


def mh(k, dk_filter=lambda x: True):
    strata, used = [], {}
    for b in BINS:
        d = [x["code"][k] for x in rows if x["land"] == "DK" and x["bin"] == b and dk_filter(x) and x["code"][k] is not None]
        s = [x["code"][k] for x in rows if x["land"] == "SE" and x["bin"] == b and x["code"][k] is not None]
        strata.append((sum(d), len(d) - sum(d), sum(s), len(s) - sum(s)))
        used[b] = {"DK": f"{sum(d)}/{len(d)}", "SE": f"{sum(s)}/{len(s)}"}
    orr, p, n = nd.mantel_haenszel(strata)
    return {"or_mh": round(orr, 3) if orr else orr, "p": p, "skikt": n, "per_skikt": used}


def describe(k):
    return {"DK": share([x for x in rows if x["land"] == "DK"], k), "SE": share([x for x in rows if x["land"] == "SE"], k),
            "utan_ar": {"DK": sum(1 for x in rows if x["land"] == "DK" and x["bin"] is None and x["code"][k] is not None),
                        "SE": sum(1 for x in rows if x["land"] == "SE" and x["bin"] is None and x["code"][k] is not None)},
            "mh": mh(k)}


res = {"plan": PLANER, "n": {"DK": sum(x["land"] == "DK" for x in rows), "SE": sum(x["land"] == "SE" for x in rows)},
       "A": {}, "M": {}, "B": {}, "C": {}}
for k in [k for k in rows[0]["code"] if k.startswith("A_")]:
    res["A"][k] = describe(k)
for fam in ("M", "B"):
    keys = [k for k in rows[0]["code"] if k[0] == fam and k[1].isdigit()]
    for k in keys:
        d = describe(k)
        d["robust"] = {"jylland": mh(k, lambda x: x["realm"] == "dk_jylland"), "ost": mh(k, lambda x: x["realm"] in OST)}
        res[fam][k] = d
    hp = holm([res[fam][k]["mh"]["p"] for k in keys])
    for k, h in zip(keys, hp):
        d = res[fam][k]
        o = d["mh"]["or_mh"]
        same = [d["robust"][g]["or_mh"] for g in ("jylland", "ost")]
        d["holm_p"] = h
        d["haller"] = bool(h is not None and h < 0.05)
        d["robust_riktning"] = bool(o and all(s and ((s > 1) == (o > 1)) for s in same))
# del C och delområden
dk = [x for x in rows if x["land"] == "DK"]
res["C"]["plats_idag"] = {L: {"kyrka": share([x for x in rows if x["land"] == L], "B1_kyrkan"),
                              "museum": share([x for x in rows if x["land"] == L], "C_museum")} for L in ("DK", "SE")}
res["C"]["material"] = {L: dict(collections.Counter(((x["rec"].get("material") or "okänt").split(",")[0].strip().lower())
                                                    for x in rows if x["land"] == L).most_common(6)) for L in ("DK", "SE")}
res["C"]["kung"] = {L: share([x for x in rows if x["land"] == L], "C_kung") for L in ("DK", "SE")}
res["C"]["delomraden"] = {g: {k: share([x for x in dk if x["realm"] == g], k)
                              for k in ("A_hednisk", "M1_foljet", "M2_striden", "M3_ambetet", "B1_kyrkan", "B2_monumentet",
                                        "B3_kvinna_reser")}
                          for g in ("dk_jylland", "dk_oarna", "dk_skane", "dk_bornholm")}
res["C"]["dk_utan_ar"] = sum(1 for x in dk if x["bin"] is None)
res["C"]["dk_per_skikt"] = dict(collections.Counter(x["bin"] or "utan år" for x in dk))

# alla danska träffar (och svenska för M2/M3, som är få) för läsning för hand
traffar = {}
for k in ["A_hednisk", "M1_foljet", "M2_striden", "M3_ambetet", "B2_monumentet", "B3_kvinna_reser", "C_kung", "B1_kyrkan"]:
    traffar[k] = [{"signum": x["signum"], "land": x["land"], "bin": x["bin"], "plats": x["rec"].get("place"),
                   "placering": x["rec"].get("placement"), "text": (x["rec"].get("translation_en") or "")[:400]}
                  for x in rows if x["code"][k] == 1 and (x["land"] == "DK" or k in ("M2_striden", "M3_ambetet", "C_kung"))]
json.dump(res, open(os.path.join(HERE, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
json.dump(traffar, open(os.path.join(HERE, "traffar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for fam in ("M", "B"):
    for k, d in res[fam].items():
        print(k, "DK", d["DK"]["a"], "/", d["DK"]["n"], "SE", d["SE"]["a"], "/", d["SE"]["n"], "OR", d["mh"]["or_mh"],
              "p", d["mh"]["p"] and f"{d['mh']['p']:.2g}", "holm", d["holm_p"] and f"{d['holm_p']:.2g}", "håller", d["haller"],
              "robust", d["robust_riktning"], "| J", d["robust"]["jylland"]["or_mh"], "Ö", d["robust"]["ost"]["or_mh"])
for k, d in res["A"].items():
    print(k, "DK", d["DK"]["a"], "/", d["DK"]["n"], "SE", d["SE"]["a"], "/", d["SE"]["n"], "OR", d["mh"]["or_mh"], "p",
          d["mh"]["p"] and f"{d['mh']['p']:.2g}")
print(json.dumps(res["C"], ensure_ascii=False)[:1500])
