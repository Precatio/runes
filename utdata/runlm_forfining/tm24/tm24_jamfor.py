"""Jämförelserna i analysplaner/2026-11-27-bojningsmodellen-tm24.md (sha 1656a0bf): parvis per lucka mot appens inställning
(app_f0–4), bara runstenar.
  --val:  rutnätet på veck 0 (val_<λ>_<tröskel>_<μ>_f0.json) mot app_f0. Valet: flest vunna minus förlorade
          böjningsluckor, utan nya säkra fel (svar ≥ 95 % som är fel här men inte i app_f0); lika → minsta λ_böj (sedan
          högsta tröskel och minsta μ, de enklaste). Ger ingen kombination fler vunna än förlorade stoppas arbetet.
          Skriver val_val.json, som committas innan veck 1–4 körs.
  --prov: prov_f1–4 (den valda inställningen) mot app_f1–4 och planens fyra villkor; skriver tm24_sammanfattning.json.
Böjningslucka (fältet infl_gap): det rätta ordet finns inte i veckets träningsordförråd, men dess lemma eller stam gör
det (src/runlm.py, inflection_gap). Fältet beror bara på veckets träningsdata och det dolda ordet, inte på lagret, så när
app-raden saknar det (äldre körningar) tas det från den parade tm24-raden; finns det på båda måste de vara lika.
    PYTHONPATH=. .venv/bin/python utdata/runlm_forfining/tm24/tm24_jamfor.py --val|--prov"""
import argparse
import json
import os
import sys

sys.path.insert(0, ".")
from src import runlm as rl  # noqa: E402
from src import textmodel as tm  # noqa: E402

F = "utdata/runlm_forfining/"
T = F + "tm24/"
GRID = [(lam, t, mu) for lam in ("0.003", "0.01", "0.03") for t in ("0.02", "0.05") for mu in ("0", "0.5")]
_d = None


def records():
    global _d
    if _d is None:
        _d = tm._records()
    return _d


def load(path):
    by = records()["by"]
    return [x for x in json.load(open(path))["rows"] if rl.object_kind(by[x["sig"]]) == "runsten"]


def is_sure(x):
    G = records()["G"]
    return bool(x["word"] and x["word"] != "<unk>" and
                tm.calibrate_gap(x["p_word"], x["word"], x["n"], G, x["kind"] == "helt ord") >= 0.95)


def compare(A, B):
    """A: app (utan lagret), B: med lagret; samma luckor i samma ordning."""
    assert len(A) == len(B), (len(A), len(B))
    r = {"infl": {"won": 0, "lost": 0, "n": 0, "ok_base": 0, "ok_new": 0, "reached_new": 0, "gold_is_layer_form": 0,
                  "won_with_layer_form": 0},
         "alla": {"won": 0, "lost": 0, "n": 0, "ok_base": 0, "ok_new": 0},
         "short": {"new_right": 0, "new_errors": 0},
         "sure": {"base": [0, 0], "new": [0, 0], "new_sure_errors": 0},
         "layer_words_read": 0}
    for x, y in zip(A, B):
        assert (x["sig"], x["kind"], x["truth"]) == (y["sig"], y["kind"], y["truth"])
        if "infl_gap" in x and "infl_gap" in y:
            assert x["infl_gap"] == y["infl_gap"], (x["sig"], x["kind"])
        ig = y["infl_gap"] if "infl_gap" in y else x["infl_gap"]
        won, lost = bool(y["word_ok"] and not x["word_ok"]), bool(x["word_ok"] and not y["word_ok"])
        a = r["alla"]
        a["n"] += 1; a["won"] += won; a["lost"] += lost; a["ok_base"] += bool(x["word_ok"]); a["ok_new"] += bool(y["word_ok"])
        if ig:
            b = r["infl"]
            b["n"] += 1; b["won"] += won; b["lost"] += lost; b["ok_base"] += bool(x["word_ok"]); b["ok_new"] += bool(y["word_ok"])
            b["reached_new"] += bool(y.get("reached")); b["gold_is_layer_form"] += bool(y.get("gold_infl_form"))
            b["won_with_layer_form"] += won and bool(y.get("word_infl"))
        r["layer_words_read"] += bool(y.get("word_infl"))
        if x["n"] <= 2:
            r["short"]["new_right"] += won
            r["short"]["new_errors"] += (x["word_ok"] or not x["word"]) and bool(y["word"] and y["word"] != "<unk>" and not y["word_ok"])
        sx, sy = is_sure(x), is_sure(y)
        r["sure"]["base"][0] += sx; r["sure"]["base"][1] += sx and not x["word_ok"]
        r["sure"]["new"][0] += sy; r["sure"]["new"][1] += sy and not y["word_ok"]
        r["sure"]["new_sure_errors"] += (sy and not y["word_ok"]) and not (sx and not x["word_ok"])
    return r


def add(a, b):
    out = {}
    for k, v in a.items():
        out[k] = add(v, b[k]) if isinstance(v, dict) else ([p + q for p, q in zip(v, b[k])] if isinstance(v, list) else v + b[k])
    return out


ap = argparse.ArgumentParser()
ap.add_argument("--val", action="store_true")
ap.add_argument("--prov", action="store_true")
args = ap.parse_args()

if args.val:
    missing = [f"val_{lam}_{t}_{mu}_f0.json" for lam, t, mu in GRID if not os.path.exists(T + f"val_{lam}_{t}_{mu}_f0.json")]
    if missing:
        sys.exit(f"saknas: {', '.join(missing)} – kör klart tm24_kor_val.sh")
    base = load(F + "app_f0.json")
    tab = []
    for lam, t, mu in GRID:
        path = T + f"val_{lam}_{t}_{mu}_f0.json"
        r = compare(base, load(path))
        meta = json.load(open(path)).get("infl", {})
        tab.append({"lam": float(lam), "min": float(t), "mu": float(mu), "fil": os.path.basename(path), "stats": meta.get("stats"),
                    "infl": r["infl"], "netto": r["infl"]["won"] - r["infl"]["lost"], "alla": r["alla"], "sure": r["sure"],
                    "short": r["short"], "godkand": r["sure"]["new_sure_errors"] == 0})
        print(f"λ {lam:>5} t {t} μ {mu:>3}: böjningsluckor {r['infl']['n']} vunna {r['infl']['won']} förlorade {r['infl']['lost']}; "
              f"alla vunna {r['alla']['won']} förlorade {r['alla']['lost']}; nya säkra fel {r['sure']['new_sure_errors']}")
    ok = sorted((x for x in tab if x["godkand"]), key=lambda x: (-x["netto"], x["lam"], -x["min"], x["mu"]))
    best = ok[0] if ok and ok[0]["netto"] > 0 else None
    out = {"plan": "analysplaner/2026-11-27-bojningsmodellen-tm24.md (sha 1656a0bf)", "jamfort_med": "app_f0.json",
           "regel": "flest vunna minus förlorade böjningsluckor utan nya säkra fel (≥ 95 %); lika → minsta λ_böj, sedan högsta tröskel, minsta μ",
           "vald": ({"lam": best["lam"], "min": best["min"], "mu": best["mu"]} if best else None),
           "stopp": best is None, "tabell": tab}
    json.dump(out, open(T + "val_val.json", "w"), ensure_ascii=False, indent=1)
    if best is None:
        print("INGEN kombination ger fler vunna än förlorade böjningsluckor (utan nya säkra fel) på veck 0 – arbetet stoppas, "
              "redovisas som negativt (val_val.json).")
        sys.exit(1)
    print(f"VALD: λ_böj {best['lam']}, tröskel {best['min']}, μ {best['mu']} (netto {best['netto']}). "
          f"Committa {T}val_val.json (git add -f) innan tm24_kor_prov.sh körs.")

if args.prov:
    V = json.load(open(T + "val_val.json"))
    if not V.get("vald"):
        sys.exit("ingen inställning vald på veck 0 – inget prov")
    per = {k: compare(load(F + f"app_f{k}.json"), load(T + f"prov_f{k}.json")) for k in range(1, 5)}
    tot = per[1]
    for k in range(2, 5):
        tot = add(tot, per[k])
    c1 = tot["infl"]["won"] > tot["infl"]["lost"]
    c2 = tot["alla"]["won"] - tot["alla"]["lost"] >= 0
    c3 = tot["sure"]["new"][1] <= tot["sure"]["base"][1]
    c4 = tot["short"]["new_errors"] <= tot["short"]["new_right"]
    S = {"plan": "analysplaner/2026-11-27-bojningsmodellen-tm24.md (sha 1656a0bf)", "vald": V["vald"],
         "per_veck": per, "totalt": tot,
         "villkor": {"1_bojningsluckor": c1, "2_alla": c2, "3_saker": c3, "4_korta": c4}, "haller": c1 and c2 and c3 and c4,
         "lagret_per_veck": {k: json.load(open(T + f"prov_f{k}.json")).get("infl", {}).get("stats") for k in range(1, 5)}}
    json.dump(S, open(T + "tm24_sammanfattning.json", "w"), ensure_ascii=False, indent=1)
    n = tot["infl"]
    print(f"böjningsluckor {n['n']}: rätt {n['ok_base']} → {n['ok_new']} (vunna {n['won']}, förlorade {n['lost']}; "
          f"rätt form bland förslagen {n['reached_new']}, rätt form gjord av lagret {n['gold_is_layer_form']}); "
          f"alla {tot['alla']['n']}: vunna {tot['alla']['won']}, förlorade {tot['alla']['lost']}; "
          f"≥ 95 % (svar, fel): {tot['sure']['base']} → {tot['sure']['new']}; korta: nya rätt {tot['short']['new_right']}, "
          f"nya fel {tot['short']['new_errors']}; HÅLLER: {S['haller']}")
