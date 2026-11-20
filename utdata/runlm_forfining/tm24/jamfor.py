"""Jämförelserna i analysplaner/2026-11-20-grannstenarnas-namn-narhet.md (sha fe998288), parvis per lucka mot app_f*,
bara runstenar. --kontroll, --steg1 (val på veck 0; exit 1 om ingen har positivt netto), --steg2 (veck 1–4, fyra villkor).
    PYTHONPATH=. .venv/bin/python utdata/runlm_forfining/tm24/jamfor.py --kontroll|--steg1|--steg2"""
import argparse
import importlib.util
import json
import os
import sys

sys.path.insert(0, ".")
F = "utdata/runlm_forfining/"
T = F + "tm24/"
_spec = importlib.util.spec_from_file_location("tm24lib", F + "tm24/lib.py")
J = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(J)  # noqa: E702
COMBOS = {"s5_l02": (5, 0.2), "s1_l01": (1, 0.1), "s1_l02": (1, 0.2), "s025_l01": (0.25, 0.1), "s025_l02": (0.25, 0.2)}
ORDER = sorted(COMBOS, key=lambda k: (-COMBOS[k][0], COMBOS[k][1]))  # nearest today first: larger s, then smaller lambda

ap = argparse.ArgumentParser()
ap.add_argument("--kontroll", action="store_true")
ap.add_argument("--steg1", action="store_true")
ap.add_argument("--steg2", action="store_true")
args = ap.parse_args()
P = T + "sammanfattning.json"
S = json.load(open(P)) if os.path.exists(P) else {}

if args.kontroll:
    ok = J.same_choices(F + "app_f0.json", T + "kontroll_f0.json")
    S["kontroll"] = {"samma_val_som_app_f0": ok}
    json.dump(S, open(P, "w"), ensure_ascii=False, indent=1)
    print("kontroll", ok); sys.exit(0 if ok else 1)  # noqa: E702

if args.steg1:
    A = J.load(F + "app_f0.json")
    S["steg1"] = {}
    for k in ORDER:
        r = J.compare(A, J.load(T + f"{k}_f0.json"))
        r["netto_namn"] = r["namn"]["won"] - r["namn"]["lost"]
        r["tillaten"] = r["sure"]["new"][1] <= r["sure"]["base"][1]
        S["steg1"][k] = r
        print(k, "namn netto", r["netto_namn"], "säkra fel", r["sure"], "tillåten", r["tillaten"])
    ok = [k for k in ORDER if S["steg1"][k]["tillaten"] and S["steg1"][k]["netto_namn"] > 0]
    best = max(ok, key=lambda k: (S["steg1"][k]["netto_namn"], -ORDER.index(k))) if ok else None
    S["val"] = {"namn": best, "s": COMBOS[best][0], "lam": COMBOS[best][1]} if best else None
    json.dump(S, open(P, "w"), ensure_ascii=False, indent=1)
    print("val", S["val"]); sys.exit(0 if best else 1)  # noqa: E702

if args.steg2:
    per = {k: J.compare(J.load(F + f"app_f{k}.json"), J.load(T + f"vald_f{k}.json")) for k in range(1, 5)}
    tot = per[1]
    for k in range(2, 5):
        tot = J.add(tot, per[k])
    S["steg2"] = {"per_veck": per, "totalt": tot, **J.verdict(tot)}
    json.dump(S, open(P, "w"), ensure_ascii=False, indent=1)
    print(J.line(tot), "HÅLLER:", S["steg2"]["haller"])
