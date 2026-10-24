"""Studie 1, efterhandskontroll 2 (inte i den låsta planen): ser mätningen alls skillnader mellan spårsorter på samma
sten? Runor mot oregelbundna spår (sprickor, vittring) inom varje objekt, Wilcoxons teckenrangtest över objekten.
    PYTHONPATH=. .venv/bin/python utdata/forskningsplan/s1_kanslighet.py > utdata/forskningsplan/s1_kanslighet.txt"""
import json, os, sys
import numpy as np
from scipy.stats import wilcoxon
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import s_analys as sa  # noqa: E402
A = sa.load("automatisk_korning_alla")
out = {}
for m in sa.MAIN:
    d_irr, d_orn = [], []
    for key, ds in sa.objects(A).items():
        if not sa.object_type(ds[0]):
            continue
        sl = [s for d in ds for s in d["slices"]]
        r, nr = sa.med(sl, m, {"rune"}); i, ni = sa.med(sl, m, {"irregular"}); o, no = sa.med(sl, m, {"ornament"})
        if nr >= 10 and ni >= 10: d_irr.append(r - i)
        if nr >= 10 and no >= 10: d_orn.append(r - o)
    out[m] = {"runa_minus_oregelbundet": float(np.median(d_irr)), "p_irr": float(wilcoxon(d_irr).pvalue), "n_irr": len(d_irr),
              "runa_minus_linje": float(np.median(d_orn)), "iqr_irr": [float(x) for x in np.percentile(d_irr, [25, 75])]}
    print(f"{m:16} runa − oregelbundet: median {out[m]['runa_minus_oregelbundet']:+.2f} (IQR {out[m]['iqr_irr'][0]:+.2f}.."
          f"{out[m]['iqr_irr'][1]:+.2f}), Wilcoxon p {out[m]['p_irr']:.1e}, {len(d_irr)} objekt | runa − linje: "
          f"{out[m]['runa_minus_linje']:+.2f}")
json.dump(out, open(os.path.join(HERE, "s1_kanslighet.json"), "w"), indent=1)
