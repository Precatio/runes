"""Studie 3, fallstudier (beskrivande): standardiserat avstånd mellan stenmedianer på de fyra huvudmåtten (P-data,
runstenar, z-värden över alla runstenar). Åsmund: U 1144 mot Gs 11/Gs 13 och mot övriga granitstenar. Medelpad:
närmast Fartägns M 1 (förslag; attribueringen är bara kalibrerad i Mälardalen)."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import s_analys as sa  # noqa: E402
st = {}
for key, ds in sa.objects(sa.load("automatisk_korning")).items():
    if sa.object_type(ds[0]) != "runsten":
        continue
    sl = [s for d in ds for s in d["slices"]]
    if len(sl) < 10:
        continue
    st[key] = {"v": [sa.med(sl, m)[0] for m in sa.MAIN], "rock": sa.rock(ds[0]), "series": ds[0]["series"], "n": len(sl)}
X = np.array([v["v"] for v in st.values()]); mu, sd = X.mean(0), X.std(0, ddof=1)
z = {k: (np.array(v["v"]) - mu) / sd for k, v in st.items()}
dist = lambda a, b: float(np.linalg.norm(z[a] - z[b]))
print(f"{len(st)} runstenar med minst 10 snitt")
if "U 1144" in z:
    print("\nÅsmund: U 1144 (granit) till")
    for k in ("Gs 11", "Gs 13"):
        if k in z: print(f"  {k} (sandsten, Åsmund): {dist('U 1144', k):.2f}")
    g = sorted((dist("U 1144", k), k) for k in z if k != "U 1144" and st[k]["rock"] == "kristallin")
    print(f"  övriga kristallina stenar: median {np.median([d for d, _ in g]):.2f}; närmast {', '.join(f'{k} {d:.2f}' for d, k in g[:3])}")
    rk = sorted((dist("U 1144", k), k) for k in z if k != "U 1144")
    print("  rang bland alla:", {k: 1 + [x for _, x in rk].index(k) for k in ("Gs 11", "Gs 13") if k in z}, "av", len(rk))
if "M 1" in z:
    m = sorted((dist("M 1", k), k) for k in z if k != "M 1" and st[k]["series"] == "medelpad")
    print("\nMedelpad närmast Fartägns M 1:", ", ".join(f"{k} {d:.2f}" for d, k in m))
