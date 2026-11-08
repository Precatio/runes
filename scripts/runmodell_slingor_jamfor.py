"""Slingmodell v2 mot v1 på de frysta prövstenarna (analysplaner/2026-11-08-slingmodell-v2.md): överlappet (IoU vid
0,5) per prövsten för v1 (den driftsatta filen), kontrollen v1' (omtränad på bara v1:s stenar) och v2 (v1:s stenar och
de nya granskade). P1: v2 > v1, Wilcoxon ensidigt p < 0,05 och positiv medianskillnad. P2: medianen av v2 − v1' > 0.
    .venv/bin/python -m scripts.runmodell_slingor_jamfor V1.pt KONTROLL.pt V2.pt > utdata/slingmodell_v2/resultat.json"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

import torch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from scripts.runmodell_slingor_train import UNet, iou, load, predict  # noqa: E402

FROZEN = os.path.join(ROOT, "data", "runmodell", "slingmodell_provstenar.json")


def main(v1: str, control: str, v2: str):
    from scipy.stats import wilcoxon
    frozen = json.load(open(FROZEN, encoding="utf-8"))
    test = [d for d in load() if d["name"] in set(frozen["test_stones"])]
    assert len(test) == len(frozen["test_stones"])
    scores = {}
    for name, path in (("v1", v1), ("kontroll", control), ("v2", v2)):
        m = UNet()
        m.load_state_dict(torch.load(path, map_location="cpu")["state"])
        m.eval()
        scores[name] = {d["name"]: iou(predict(m, d, "cpu"), d["mask"]) for d in test}
    names = [d["name"] for d in test]
    d21 = [scores["v2"][n] - scores["v1"][n] for n in names]
    d2c = [scores["v2"][n] - scores["kontroll"][n] for n in names]
    p1 = float(wilcoxon(d21, alternative="greater").pvalue)
    out = {"plan": "analysplaner/2026-11-08-slingmodell-v2.md", "test_stones": len(names),
           "new_stones": None, "median_iou": {k: st.median(v.values()) for k, v in scores.items()},
           "P1": {"median_diff": st.median(d21), "p": p1, "better": sum(x > 0 for x in d21),
                  "holds": p1 < 0.05 and st.median(d21) > 0},
           "P2": {"median_diff": st.median(d2c), "holds": st.median(d2c) > 0},
           "per_stone": {n: {k: round(scores[k][n], 3) for k in scores} for n in names}}
    out["replace"] = out["P1"]["holds"] and out["P2"]["holds"]
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
