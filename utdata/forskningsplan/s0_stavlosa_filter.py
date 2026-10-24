"""Steg 0b: känner runfiltret igen stavlösa runor? Igenkända runor per sten mot antalet runor i Rundatas text."""
import glob, json, re, sys
sys.path.insert(0, ".")
from api.rundata import store
s = store()
rows = []
for p in glob.glob("utdata/automatisk_korning/*/*.json"):
    d = json.load(open(p, encoding="utf-8"))
    if "error" in d or not d.get("signum"):
        continue
    r = s.get(d["signum"]) or {}
    n_text = len(re.findall(r"[a-zæøåþðîï§RAEIOUY]", re.sub(r"\[[^\]]*\]|\([^)]*\)", "", r.get("transliteration") or ""), re.I))
    rows.append((d["signum"], "stavlösa" in (r.get("rune_types") or ""), (d.get("rune_summary") or {}).get("n_runes") or 0,
                 n_text, d["counts"]["accepted"], d["counts"]["rejection_reasons"].get("inte runa: ensamt rakt spår utan andra runor intill", 0)))
rows.sort(key=lambda x: (not x[1], x[0]))
print("signum stavlösa igenkända text_runor kvot godkända_snitt ensamma_raka")
for sg, st, n, t, a, iso in rows:
    print(f"{sg:14} {'J' if st else ' '} {n:4} {t:4} {n / t if t else 0:5.2f} {a:5} {iso:5}")
import statistics as S
for flag in (True, False):
    q = [n / t for _, st, n, t, _, _ in rows if st == flag and t >= 10]
    print("stavlösa" if flag else "övriga", len(q), "median kvot", round(S.median(q), 2) if q else None)
