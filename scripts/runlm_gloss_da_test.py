"""Svenska översättningsutkast via danska eller via engelska: vilken väg kommer närmast? Prov på de vikingatida danska
inskrifterna som har både Rundatas normalisering och en dansk översättning från Danske Runeindskrifter (runer.ku.dk,
tabellen i utdata/Malt/kallor/runer_ku/). Femfaldigt över inskrifterna: den danska ordlistan, den engelska ordlistan
och kopplingen till fornvästnordiska standardformer lärs utan den femte delen, som sedan översätts från Rundatas
normalisering på tre sätt:
  * via engelska, ord för ord (som förut)
  * via engelska, med svensk ordföljd för possessiv, demonstrativ och adjektiv (sin fader, denna sten, god dräng)
  * via danska där den danska ordlistan känner ordet, annars engelska, med svensk ordföljd
Facit är den danska översättningen överförd till svenska ord för ord med samma lista (DA_SV) som den danska vägen
använder. Det gynnar den danska vägen när det gäller ordval; därför mäts också ordföljden för sig (ordpar), och
namnen. Skriver utdata/Malt/runlm_oversattning_da.json.
    .venv/bin/python -m scripts.runlm_gloss_da_test"""
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.runlm import load_rundata, norm_words, normtok, sections, viking  # noqa: E402
from src.rungloss import DA_STOP, DA_SV, Glossary, _danish, _sv_name, load_danish, ows_map, swedish  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = load_rundata()
DA = load_danish(R)
if not DA:
    sys.exit("Tabellen från runer.ku.dk saknas (utdata/Malt/kallor/runer_ku/indskrifter.txt).")
WITH_DA = [dict(r, translation_da=DA[r["signum"]]) for r in R if r["signum"] in DA]
TEST = [r for r in WITH_DA if viking(r) and r.get("normalization") and len(norm_words(r["normalization"])) >= 4]
random.Random(2026).shuffle(TEST)
K = 5
SV_STOP = {DA_SV[w] for w in DA_STOP if w in DA_SV} | {"…", "efter"}


def reference(da):
    """The Danish translation in Swedish words: DA_SV for the words it lists, names in Swedish spelling."""
    s = re.sub(r"\(\?\)|N\.N\.?|\b(el|ell|dvs|jf)\.", " ", da)
    s = re.sub(r"(\S+)/\S+", r"\1", re.sub(r"[\[\]()*{}'\"‘’]", "", s))
    out = []
    for w in re.findall(r"[A-Za-zÆØÅæøåÀ-ÿ-]+", s):
        lw = w.lower()
        out.append(DA_SV.get(lw, _sv_name(w) if w[0].isupper() and lw not in DA_SV else lw).lower())
    return out


def toks(s):
    return [w.strip(",.").lower() for w in s.split() if w.strip(",.")]


def score(hyp, ref):
    """Content words: how many of the draft's are in the reference (precision), how many of the reference's the draft
    has (coverage); word pairs: how many of the draft's neighbouring pairs stand together in the reference."""
    h, r_ = [w for w in hyp if w not in SV_STOP], {w for w in ref if w not in SV_STOP}
    pairs_r = set(zip(ref, ref[1:], strict=False))
    pairs_h = [p for p in zip(hyp, hyp[1:], strict=False) if "…" not in p]
    return {"hit": sum(w in r_ for w in h), "n_h": len(h), "cov": len({w for w in h if w in r_}), "n_r": len(r_),
            "pair_hit": sum(p in pairs_r for p in pairs_h), "n_pair": len(pairs_h)}


rows = []
for k in range(K):
    test = TEST[k::K]
    tset = {r["signum"] for r in test}
    rest = [r for r in R if r["signum"] not in tset]
    en = Glossary([r for r in rest if r.get("translation_en")])
    da = Glossary([r for r in WITH_DA if r["signum"] not in tset], field="translation_da", words=_danish,
                  src="normalization_ows")
    ows = ows_map(rest)
    for r in test:
        ws = [normtok(w) for _, p in sections(r["normalization"]) for w in norm_words(p)]
        ref = reference(r["translation_da"])
        hyp = {"engelska": en.translate(ws, "sv"), "engelska_ordföljd": swedish(ws, en),
               "danska": swedish(ws, en, da, ows)}
        rows.append({"sig": r["signum"], "ref": " ".join(ref), **hyp,
                     **{f"s_{n}": score(toks(h), ref) for n, h in hyp.items()}})
    print(f"del {k + 1} klar; {len(rows)} inskrifter", flush=True)

out = {"n": len(rows)}
for n in ("engelska", "engelska_ordföljd", "danska"):
    S = [x[f"s_{n}"] for x in rows]
    prec = sum(s["hit"] for s in S) / max(1, sum(s["n_h"] for s in S))
    rec = sum(s["cov"] for s in S) / max(1, sum(s["n_r"] for s in S))
    pair = sum(s["pair_hit"] for s in S) / max(1, sum(s["n_pair"] for s in S))
    out[n] = {"precision": prec, "täckning": rec, "ordpar": pair}
    print(f"{n:18}: precision {prec:.1%}, täckning {rec:.1%}, ordpar som står så i facit {pair:.1%}")
# how much of the Swedish Viking-age stones' words would go through Danish (glossaries learned from everything)
en = Glossary([r for r in R if r.get("translation_en")])
da = Glossary(WITH_DA, field="translation_da", words=_danish, src="normalization_ows")
ows = ows_map(R)
SW = set("U Sö Ög Vg Sm Öl G Nä Vs Gs Hs M J Ån Lp D Vr Bo Ds".split())
n_all = n_da = 0
for r in R:
    if viking(r) and r.get("normalization") and r["signum"].split()[0] in SW:
        for _, p in sections(r["normalization"]):
            for w in norm_words(p):
                w = normtok(w)
                n_all += 1
                n_da += bool(da.best_da(ows.get(w, w)))
out["svenska_ord_via_danska"] = n_da / max(1, n_all)
print(f"ord på svenska vikingatida stenar som den danska ordlistan känner: {n_da / max(1, n_all):.1%} av {n_all}")
for x in rows[:10]:
    print(f"  {x['sig']:12} facit:    {x['ref'][:100]}\n  {'':12} engelska: {x['engelska'][:100]}\n  {'':12} danska:   {x['danska'][:100]}")
out["rows"] = rows
json.dump(out, open(os.path.join(ROOT, "utdata", "Malt", "runlm_oversattning_da.json"), "w"), ensure_ascii=False, indent=1)
