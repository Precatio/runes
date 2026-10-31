"""Maltstenen läst med sannolikhetsmodellen (src/runlm.py), utan någon tolkning: modellen har aldrig sett Rundatas
normalisering av Maltstenen. Texten är stenens huggna grupper i ordningen A1, B1–B6 (runraden A2 och specialtecknet
är gränser, inte runor); de sex omstridda punkterna prövas i alla 64
kombinationer, och sannolikheten för varje läsning av en omstridd runa är den andel av textens totala sannolikhet
som den står för (lika förhand). För varje ord ges modellens sannolikhet och den kalibrerade sannolikheten
(malt_avkod_kalibrering.json). Modellen byggs med samma inställningar som i provet; om epoken gissas ur texten
(steg 3) dateras Maltstenen också: hur sannolik är texten på 800-talet, 900-talet, 1000–1070 och 1070–1150?
Skriver malt_avkodning.json (eller MALT_OUT; med RUNLM_LIT/RUNLM_LEX/RUNLM_NAMES_LIT läses stenen med litteraturlexikonet).
    .venv/bin/python -m scripts.malt_decode [--dating-only]"""
import itertools
import json
import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.runlm import (EPOCHS, Model, context, decode, decode_epochs, edda_tokens, epoch_posterior, fit_temperature,  # noqa: E402
                       key, load_rundata, norm_words, normtok, pairs, runekey, sections, viking)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utdata", "Malt")
MALT = "DR NOR1988;5"
CAL = json.load(open(os.path.join(OUT, "malt_avkod_kalibrering.json")))


def calibrated_dating(ll_malt, prior):
    """The Malt stone's dating with a temperature fitted on the dating test (utdata/Malt/runlm_datering.json)."""
    drows = json.load(open(os.path.join(OUT, "runlm_datering.json")))["rows"]
    out = {}
    for mode, use_prior in (("prior", True), ("uniform", False)):
        T = fit_temperature(drows, use_prior)
        rel = []
        for lo, hi in ((0, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.01)):
            sub = [(x, epoch_posterior(x["ll"], x["prior"] if use_prior else None, T)) for x in drows]
            sub = [(x, p) for x, p in sub if lo <= max(p.values()) < hi]
            rel.append((lo, len(sub), sum(max(p.values()) for _, p in sub) / max(1, len(sub)),
                        sum(max(p, key=p.get) == x["true"] for x, p in sub) / max(1, len(sub))))
        post = epoch_posterior(ll_malt, prior if use_prior else None, T)
        out[mode] = {"temperature": T, "posterior": post, "reliability": rel}
        print(f"kalibrerad datering ({mode}, temperatur {T:.2f}):", {e: f"{p:.0%}" for e, p in post.items()},
              "| säkerhet → träff:", [(f"{p:.2f}", f"{a:.2f}", n) for _, n, p, a in rel])
    return out


if "--dating-only" in sys.argv:  # recompute the calibrated dating from a finished reading
    path = os.path.join(OUT, "malt_avkodning.json")
    res_ = json.load(open(path))
    res_["epoch_cal"] = calibrated_dating(res_["epoch_ll"], res_["epoch_prior"])
    json.dump(res_, open(path, "w"), ensure_ascii=False, indent=1, default=str)
    sys.exit()
RECS = load_rundata()
V = [r for r in RECS if viking(r) and r.get("transliteration") and r.get("normalization") and r["signum"] != MALT]
CFG = CAL.get("config", {})
MED = ([r for r in RECS if (r.get("period") or "").startswith("M") and r.get("transliteration") and r.get("normalization")]
       if CFG.get("medieval") else [])
EPOCH_MODE = CFG.get("epoch", "none") if CFG.get("contexts") else "none"
MALT_PATH = context(next(r for r in RECS if r["signum"] == MALT))[:CFG.get("levels", 5)]


def _lexicon():
    """The literature lexicon (textmodel-22 candidate) through the same environment variables as src/textmodel
    (RUNLM_LIT, RUNLM_LEX, RUNLM_NAMES_LIT); unset = off, as in the published reading."""
    if not any(os.environ.get(k) for k in ("RUNLM_LIT", "RUNLM_LEX", "RUNLM_NAMES_LIT")):
        return {}
    from src import textmodel as tm
    return tm._lexicon_kwargs(lambda r: r["signum"] != MALT)


def build(lam_unk, lam_edda):
    return Model(V, edda_tokens=edda_tokens(), lam_unk=lam_unk, lam_edda=lam_edda, aligned=CFG.get("aligned", False), **_lexicon(),
                 contexts=CFG.get("contexts", False), alpha=CFG.get("alpha", 20.0), kappa_e=CFG.get("kappa_e", 5.0),
                 lm_beta=CFG.get("lm_beta", 0.0), spelling_recs=MED, lam_name=CFG.get("lam_name", 0.0))


def read(model, groups, signs):
    """(log P(text), best path, posteriors, text, P(epoch | text), log P(text | epoch)) with the provet's settings."""
    if EPOCH_MODE == "inferred":
        return decode_epochs(model, groups, signs, path=MALT_PATH, adapt=CFG.get("adapt", 0.0))
    ctx = model.ctx(MALT_PATH[:1]) if CFG.get("contexts") else None  # the Malt stone's epoch is not known
    logZ, path, post, t = decode(model, groups, signs=signs, ctx=ctx)
    return logZ, path, post, t, None, None


m = build(CAL["lam_unk"], CAL["lam_edda"])
freq = Counter(normtok(b) for r in V for _, p in sections(r["normalization"]) for b in norm_words(p))
fk = Counter()
for w_, c_ in freq.items():
    fk[key(w_)] += c_  # how common the word is, over all its normalized forms
print("ordpar", sum(sum(c.values()) for c in m.emp.values()), "| ordförråd", len(m.uni), "runiska +", len(m.pe), "ur Eddan | d", round(m.d, 3))

# The disputed points (Rundata/Stoklund, Grønvik 1992, Heltoft 2017): (name, readings)
POINTS = [("B1:23", ["i", ":"]), ("B4 efter 14", [":", ""]), ("B4:1", ["a", "k"]), ("B3:11", ["s", "i"]), ("B5:14", ["i", "a"]), ("B5:22–23", ["ki", "il"])]


def text(v):
    """The carved groups in the order A1, B1–B6 (the futhark row and the special sign are boundaries, not runes)."""
    b1, b4d, b41, b311, b514, b522 = v
    s = ("suaai:titultitul|huaRisi:alistiosa:huaRis" + b1 + "uifrþuR:karþi:afraftasinifauþrkul:finR:fal" + b311 +
         ":taitirunoR:u" + b41 + "iuinrunoR:suli" + b4d + "alta:huaR|utu:tuuutbilik" + b514 + "kR:tuRra" + b522 + "tuli")
    groups, signs, cur = [], [], ""
    for ch in s:
        if ch in (":", "|"):
            groups.append(cur); cur = ""
            if ch == "|":
                signs.append(len(groups) - 1)
        else:
            cur += ch
    groups.append(cur)
    return groups, signs


def _lse_list(xs):
    mx_ = max(xs)
    return mx_ + math.log(sum(math.exp(x - mx_) for x in xs))


def recal(p, w, length, runes):
    """The calibrated probability (scripts/runlm_calibrate.py) that the word is right; None for an unknown word."""
    if w == "<unk>":
        return None
    B = CAL["recal"]
    p = min(max(p, 1e-4), 1 - 1e-4)
    lch = max(math.log(max(m.index.get(runes, {}).get(w, 0.0), 1e-12)), -12.0)
    x = [1.0, math.log(p / (1 - p)), math.log1p(fk[key(w)]), float(fk[key(w)] == 0), math.log(length), lch]
    return 1 / (1 + math.exp(-sum(a * b for a, b in zip(x, B, strict=False))))


res = {}
for v in itertools.product(*[r for _, r in POINTS]):
    groups, signs = text(v)
    logZ, path, post, t, ep_post, ep_ll = read(m, groups, signs)
    res[v] = (logZ, path, post, t, groups, ep_post, ep_ll)
lz = {v: r[0] for v, r in res.items()}
mx = max(lz.values())
Zs = sum(math.exp(x - mx) for x in lz.values())
point_post = {}
for k, (name, reads) in enumerate(POINTS):
    point_post[name] = {rd: sum(math.exp(x - mx) for v, x in lz.items() if v[k] == rd) / Zs for rd in reads}
    print(f"{name}: " + ", ".join(f"{rd or 'inget'} {p:.0%}" for rd, p in point_post[name].items()))
best_v = max(lz, key=lz.get)
print("mest sannolik kombination:", best_v, f"{math.exp(lz[best_v] - mx) / Zs:.0%}")


def reading(v):
    """The best path for one combination of the disputed points, with alternatives for each stretch."""
    logZ, path, post, t, groups = res[v][:5]
    out = []
    for i, j, w, p in path:
        alts = sorted(((ww, pp) for (ii, jj, ww), pp in post.items() if ii == i and jj == j and key(ww) != key(w) and pp > 0.03), key=lambda x: -x[1])[:4]
        over = sorted(((t[ii:jj], ww, pp) for (ii, jj, ww), pp in post.items() if (ii, jj) != (i, j) and ii < j and jj > i and pp > 0.10 and ww != '<unk>'),
                      key=lambda x: -x[2])[:4]
        out.append({"runes": t[i:j], "start": i, "end": j, "word": w, "p": p, "pc": recal(p, w, j - i, t[i:j]), "freq": fk[key(w)] if w != "<unk>" else 0,
                    "edda_only": w != "<unk>" and fk[key(w)] == 0, "alts": alts, "overlap": over})
    return out


R = reading(best_v)
for x in R:
    pc = f"{x['pc']:.2f}" if x["pc"] is not None else "  – "
    print(f"  {x['runes']:<14} {x['word']:<14} p={x['p']:.2f} kal={pc} belägg={x['freq']:<4} {'Edda ' if x['edda_only'] else ''}"
          f"alt={[(w, round(p, 2)) for w, p in x['alts']]} {[(r, w, round(p, 2)) for r, w, p in x['overlap']]}")

# Forced: if every stretch must be a known word, which words would it be? (the unknown word almost switched off;
# the calibration is applied with the ordinary model's spelling probabilities)
lam_unk = m.lam_unk
m.lam_unk = 1e-12
try:
    g, sg = text(best_v)
    _, path, _, t, _, _ = read(m, g, sg)
    F = [{"runes": t[i:j], "word": w, "p": p, "pc": recal(p, w, j - i, t[i:j]), "freq": fk[key(w)], "edda_only": fk[key(w)] == 0} for i, j, w, p in path]
finally:
    m.lam_unk = lam_unk
print("tvingad läsning (bara kända ord):")
print("  " + " ".join(f"{x['word']}({x['pc']:.2f})" if x["pc"] is not None else x["word"] for x in F))

# Readings under each alternative of each disputed point (the rest at their most probable values)
alt_read = {}
for k, (name, reads) in enumerate(POINTS):
    for rd in reads:
        v = list(best_v); v[k] = rd; v = tuple(v)
        alt_read[f"{name}={rd or 'inget'}"] = [(x["runes"], x["word"], round(x["p"], 3)) for x in reading(v)]

# How probable is a complete reading? Expected number of right words and the chance that all are right
pcs = [x["pc"] for x in R if x["pc"] is not None]
n_unk = sum(1 for x in R if x["word"] == "<unk>")
exp_right = sum(pcs)
all_right = math.prod(pcs) * (CAL["unk_span"] ** n_unk)
pf = [x["pc"] for x in F if x["pc"] is not None]
forced_all = math.prod(pf)
print(f"ord i läsningen {len(R)}, varav okända {n_unk}; väntat antal rätt bland de kända {exp_right:.1f} av {len(pcs)}")
print(f"sannolikhet att alla kända ord är rätt (och de okändas gränser): {all_right:.1e}; tvingad helt fullständig läsning: {forced_all:.1e}")
strong = [(x["runes"], x["word"], round(x["pc"], 2)) for x in R if x["pc"] is not None and x["pc"] >= 0.7]
print("ord med kalibrerad sannolikhet ≥ 0,7:", strong)

# Robustness: the disputed points under other weights for the unknown word and the Icelandic vocabulary
sens = {}
for lu, le in ((0.003, 0.03), (0.03, 0.03), (0.01, 0.0), (0.01, 0.1)):
    m2 = build(lu, le)
    lz2 = {}
    for v in itertools.product(*[r for _, r in POINTS]):
        g, sg = text(v)
        lz2[v] = read(m2, g, sg)[0]
    mx2 = max(lz2.values()); Z2 = sum(math.exp(x - mx2) for x in lz2.values())
    sens[f"{lu}/{le}"] = {name: {rd: sum(math.exp(x - mx2) for v, x in lz2.items() if v[k] == rd) / Z2 for rd in reads} for k, (name, reads) in enumerate(POINTS)}
    print(f"känslighet lam_unk {lu} lam_edda {le}: " + "; ".join(f"{n} {max(d_, key=d_.get) or 'inget'} {max(d_.values()):.0%}" for n, d_ in sens[f"{lu}/{le}"].items()))

# Dating: P(epoch | text), summed over the combinations of the disputed runes; with the epochs' share in training as
# prior, and with equal priors (only the text speaks)
epoch_post = epoch_uniform = epoch_cal = lu_ = None
if EPOCH_MODE == "inferred":
    epoch_post = {e: sum(math.exp(lz[v] - mx) / Zs * res[v][5][e] for v in res) for e in EPOCHS}
    lu_ = {e: _lse_list([res[v][6][e] for v in res]) for e in EPOCHS}
    mu_ = max(lu_.values())
    zu = sum(math.exp(x - mu_) for x in lu_.values())
    epoch_uniform = {e: math.exp(lu_[e] - mu_) / zu for e in EPOCHS}
    print("datering av Maltstenen (med förhand):", {e: f"{p:.0%}" for e, p in epoch_post.items()})
    print("datering av Maltstenen (lika förhand):", {e: f"{p:.0%}" for e, p in epoch_uniform.items()})
    print("förhand (andel i träningen):", dict(m.epoch_prior))
    if os.path.exists(os.path.join(OUT, "runlm_datering.json")):
        epoch_cal = calibrated_dating(lu_, dict(m.epoch_prior))

# How is 'ok' spelled? (B4:1 = k gives uk; with a, the lone u would have to be ok)
okc = Counter(runekey(a_) for r in V for a_, b_ in pairs(r, CFG.get("aligned", False)) if normtok(b_) == "ok")
print("ok stavas:", okc.most_common(6), "| ensamt u:", okc["u"] + okc["o"])

# Spelling examples for the article: how the model expects 'stone' and 'monument' to be carved
spell_ex = {}
for w in ("stæin", "kumbl"):
    ps = {s_: d_[w] for s_, d_ in m.index.items() if w in d_}
    spell_ex[w] = sorted(ps.items(), key=lambda kv: -kv[1])[:5]
print("stavningsexempel:", {w: [(s_, round(p_, 2)) for s_, p_ in v] for w, v in spell_ex.items()})
n_pair_inscr = m.n_pair_inscriptions

json.dump({"config": CFG, "epoch_post": epoch_post, "epoch_uniform": epoch_uniform, "epoch_cal": epoch_cal, "epoch_ll": lu_,
           "epoch_prior": dict(m.epoch_prior),
           "spell_examples": spell_ex, "n_train": len(V), "n_pair_inscriptions": n_pair_inscr, "ok_spellings": dict(okc),
           "exp_right": exp_right, "n_known": len(pcs), "n_unk": n_unk, "all_right": all_right, "forced_all": forced_all, "strong": strong,
           "sensitivity": sens, "points": point_post, "best": list(best_v), "best_share": math.exp(lz[best_v] - mx) / Zs, "reading": R, "forced": F,
           "alt_readings": alt_read, "d": m.d, "n_pairs": m.n_pairs, "n_vocab": len(m.uni), "n_edda": len(m.pe)},
          open(os.environ.get("MALT_OUT") or os.path.join(OUT, "malt_avkodning.json"), "w"), ensure_ascii=False, indent=1, default=str)
