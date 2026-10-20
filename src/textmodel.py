"""Sannolikhetsmodellen i appen (inskriftssidans panel "Läsning och luckor"): för en vikingatida inskrift modellens
läsning ord för ord, ifyllning av förlorade runor – med det som syns av dem, om användaren anger det –, datering ur
språket och översättningsutkast på svenska och engelska. Bygger på src/runlm.py och src/rungloss.py; proven och
siffrorna finns i METHODS.md, avsnitt 8.1.

En inskrift läses alltid av en modell som inte är tränad på den. Inskrifterna delas i fem delar efter signum, och en
inskrift i del k läses av modellen som tränats på de fyra andra – annars skulle en lucka som Rundata har återställt
fyllas av en modell som redan läst återställningen. Modellerna byggs först när de behövs (omkring en halv minut
vardera) och resultaten sparas per inskrift i data/cache/textmodel/."""
import json
import math
import os
import re
import threading
import zlib
from collections import Counter
from datetime import datetime, timezone

from src import runlm as rl
from src import rungloss as rg

VERSION = "textmodel-19"
K = 5
CACHE = os.path.join(rl.ROOT, "data", "cache", "textmodel", VERSION)
CACHE_LOO = CACHE + "-loo"  # readings with the leave-one-out model
MAX_GAP = 4  # longer runs of lost runes are left open: the masking test covers 1–4 runes
# Soft traces (trace_eps): a misread trace costs a factor 0.05 per rune instead of ruling out the right answer. With one
# trace in five misread, whole words were 73 % right against 44 % with hard traces (scripts/runlm_restore_test.py).
# each stone read with its carver's own divider rate (rl.stone_divider_rate) instead of the corpus rate: word boundaries
# +0.31 percentage points on the runestones of the reading test (95 %: +0.12 to +0.49), the words unchanged (textmodel-15)
OWN_D = True
# name_cands=40 (textmodel-18): namnmatcharens kandidater med egen kvot, så att sällsynta namn når poängsättningen i
# stället för att drunkna bland ordförrådets kandidater. A/B på samma maskeringsprov: 8 luckor vunna (guðfastr,
# þormóð, huskarl …), ingen förlorad; dokumenterade luckor 248 → 249 rätt av 361, ≥95-felantalet oförändrat.
FILL = dict(window=None, char_fills=15, context_cands=True, n_cands=100, by_word=True, near_km=10.0, lam_near=0.1,
            trace_eps=0.05, name_cands=40)
# tolerance=0.02 (textmodel-19): toleranslagret – varje belagd stavning utökas med regelgenererade varianter (slut-R,
# h-, obetonad vokal, i/e/a, nasal före k/t/b, svarabhakti; högst två regler) till straffet λ per regel, så att ord
# vars huggna stavning saknas i träningsmaterialet kan nås. Plan låst innan resultat (utdata/runlm_forfining/
# analysplan_tm19.md); λ valt på veck 0, veck 1–4: inne i ord +8/−2, hela ord +5/−3, säkra fel 16 → 15; dok5 252 av 361
# (249) med 2 fel bland 158 svar ≥ 95 % (4). Liten effekt, inga fler säkra fel.
MODEL = dict(aligned=True, lam_name=0.05, contexts=True, alpha=100.0, kappa_e=50.0, lm_beta=200.0, lam_class=0.2,
             tolerance=0.02, tol_max_rules=2)
EPOCH_LABEL = {"800": "800-talet", "900": "900-talet", "1000": "1000–1070", "1100": "1070–1150"}
# What the tests showed (METHODS.md 8.1), shown with the results so that a reader can judge them. Runestones, with the
# calibrated choice of textmodel-19 (scripts/runlm_list_calibrate.py, cross-validated with whole stones held out;
# numbers from utdata/runlm_forfining/validering_tm19.py on the tm19 generation): the masking test (inside a word 698
# gaps, whole words 698; at least 95 %: 409 gaps), the editors' restored gaps (256 at ≥ 95 %), the documented gaps end
# to end (361; 155 at ≥ 95 % cross-validated; scripts/runlm_documented_test.py, dok5), the dating test (1 670
# runestones) and the masking test with simulated traces, half of each hidden rune visible (whole words; one trace in
# five misread for with_misread_traces). The masking figures are measured on the mask4 generation of the test
# (textmodel-18: inside 0.755, whole 0.587, sure 0.951, documented 0.69); textmodel-17 published the older mask3
# generation's, so those are not comparable one to one.
VALIDATION = {"inside_word": 0.764, "whole_word": 0.592, "sure_right": 0.954, "rundata_sure": 0.996,
              "with_traces": 0.842, "with_misread_traces": 0.769, "dating_epoch": 0.585, "dating_near": 0.948,
              "documented_right": 0.698, "documented_sure": 0.987}

_lock = threading.Lock()
_compute = threading.Lock()  # one reading at a time: the models' caches are shared
_bundles: dict = {}
_loo: dict = {}
_data: dict = {}


def fold_of(signum: str) -> int:
    return zlib.crc32(signum.encode("utf-8")) % K


def _records() -> dict:
    if "by" not in _data:
        recs = rl.load_rundata()
        cal = os.environ.get("RUNLM_CALIBRATION") or os.path.join(rl.ROOT, "data", "runlm_calibration.json")
        _data.update(recs=recs, by={r["signum"]: r for r in recs},
                     V=[r for r in recs if rl.viking(r) and r.get("transliteration") and r.get("normalization")],
                     da=rg.load_danish(recs), edda=rl.edda_tokens(),
                     T=json.load(open(cal))["dating_temperature"] if os.path.exists(cal) else None,
                     B=(json.load(open(cal)).get("word_recal") or {}).get("B") if os.path.exists(cal) else None,
                     G=(json.load(open(cal)).get("gap_recal") or None) if os.path.exists(cal) else None,
                     GL=(json.load(open(cal)).get("gap_list") or None) if os.path.exists(cal) else None)
        if _data["G"]:
            _data["G"] = (_data["G"]["B"], set(_data["G"]["top50"]), name_keys(recs))
        if _data["GL"]:
            _data["GL"] = (_data["GL"]["theta"], _data["GL"]["classes"], _data["GL"]["kmax"], set(_data["GL"]["top50"]),
                           name_keys(recs))
        # names on nearby stones come from the whole corpus (the stone itself left out), not only from the stones the
        # stone's model learned from: a companion stone in the same held-out part is no leak about this one
        _data["sites"] = rl.name_sites(_data["V"])
    return _data


def bundle(k: int) -> dict:
    """The model, glossaries and Old Norse forms learned from every inscription outside part k."""
    with _lock:
        if k not in _bundles:
            _bundles[k] = _build(lambda r: fold_of(r["signum"]) != k)
        return _bundles[k]


def bundle_loo(signum: str) -> dict:
    """The same, learned from every inscription but this one (leave one out): for reading a single stone, the model also
    sees the stones in its own part, such as a sister stone (Sö 208 for Sö 206). About 20 s to build; the latest is kept."""
    with _lock:
        if signum not in _loo:
            _loo.clear()
            _loo[signum] = _build(lambda r: r["signum"] != signum)
        return _loo[signum]


def _build(keep) -> dict:
    if True:
        d = _records()
        m = rl.Model([r for r in d["V"] if keep(r)], edda_tokens=d["edda"], **MODEL)
        rest = [r for r in d["recs"] if keep(r)]
        da_recs = [dict(r, translation_da=d["da"][r["signum"]]) for r in rest if r["signum"] in d["da"]]
        # how common each word is in the texts the model learned from, over all its normalized forms (for recal)
        freq = Counter(rl.normtok(b_) for r in d["V"] if keep(r) for _, p in rl.sections(r["normalization"])
                       for b_ in rl.norm_words(p))
        fk = Counter()
        for w_, c_ in freq.items():
            fk[rl.key(w_)] += c_
        return {
            "model": m, "fk": fk, "en": rg.Glossary([r for r in rest if r.get("translation_en")]),
            "da": rg.Glossary(da_recs, field="translation_da", words=rg._danish, src="normalization_ows") if da_recs else None,
            "ows": rg.ows_map(rest)}


def recal(b: dict, p: float, w: str, runes: str, B) -> float:
    """The calibrated probability that a word in the reading is right (data/runlm_calibration.json, word_recal): the
    model's own probability is too sure – said 70 %, right 40 % – and less so for common words with a usual spelling."""
    if not B or w == "<unk>":
        return p
    fk, m = b["fk"], b["model"]
    p = min(max(p, 1e-4), 1 - 1e-4)
    lch = max(math.log(max(m.index.get(runes, {}).get(w, 0.0), 1e-12)), -12.0)
    x = [1.0, math.log(p / (1 - p)), math.log1p(fk[rl.key(w)]), float(fk[rl.key(w)] == 0), math.log(len(runes)), lch]
    return 1 / (1 + math.exp(-sum(a * c for a, c in zip(x, B))))


def name_keys(recs) -> set[str]:
    """The keys of every word Rundata writes as a name ("Ragnvi) somewhere in its normalizations."""
    return {rl.key(rl.normtok(re.sub(r"[\[\](){}<>?]", "", w.lstrip('"')))) for r in recs if r.get("normalization")
            for w in re.findall(r'"[^\s,.;:!]+', r["normalization"])}  # "Alfdi[s]: restored runes count too


def gap_class(word: str, top: set[str], names: set[str], composed: bool = False) -> int:
    """0 a formula word (the 50 most common), 1 another word, 2 a name (marked § by the model, or written as a name in
    Rundata). A formula word that is also a name ("Guð") counts as a formula word. composed: a name the model has put
    together of name elements (§) is a class of its own, 3."""
    k = rl.key(rl.normtok(word.lstrip("§")))
    if k in top:
        return 0
    if composed and word.startswith("§"):
        return 3
    return 2 if (word.startswith("§") or k in names) else 1


def calibrate_gap(p: float, word: str, n_lost: int, G, whole: bool = False) -> float:
    """The calibrated probability for a word in a gap (data/runlm_calibration.json, gap_recal): P(right) =
    sigmoid(a_class + b_class·logit(p) + c·log(lost runes) [+ d·whole word lost]), the class from gap_class. Fitted on
    gaps the editors have filled and, since textmodel-15, on documented gaps (runes known from older drawings, lost for
    physical reasons like the gaps in the app) and masked words, at the level of the documented gaps
    (scripts/runlm_gap_calibrate.py). whole: the gap covers a whole word (no preserved rune of it)."""
    if not G or word == "<unk>" or p <= 0:
        return p
    B, top, names = G
    # 2K + 1 coefficients (K classes: three, or four with the composed names on their own), + 1 with the whole-word term
    K, has_whole = (len(B) - 1) // 2, (len(B) - 1) % 2 == 1
    cls = gap_class(word, top, names, composed=K > 3)
    q = min(max(p, 1e-4), 1 - 1e-4)
    oh = [1.0 if cls == k else 0.0 for k in range(K)]
    x = oh + [o * math.log(q / (1 - q)) for o in oh] + [math.log(max(1, n_lost))] + ([1.0 if whole else 0.0] if has_whole else [])
    return 1 / (1 + math.exp(-sum(c * v for c, v in zip(B, x))))


def calibrate_words(dist: dict, n_lost: int, GL, whole: bool = False) -> dict:
    """All the words of a gap calibrated together (data/runlm_calibration.json, gap_list; scripts/runlm_list_calibrate.py):
    each of the gap's kmax most probable words gets u = a_class + b_class · log p (+ r_class for the first choice, whose
    probability is too high because it was chosen for being the highest), "none of them" gets
    u0 = c + d · log(lost runes) + e · whole word + f · log(1 − largest p) + the documented gaps' constant, and the
    probabilities are a softmax over the words and "none". What "none" gets is left unassigned; words beyond the kmax
    get 0."""
    if not GL or not dist:
        return dist
    theta, K, kmax, top, names = GL
    items = [(w, p) for w, p in sorted(dist.items(), key=lambda kv: -kv[1]) if w != "<unk>" and p > 0][:kmax]
    if not items:
        return dist
    a, b, c, r = theta[:K], theta[K:2 * K], theta[2 * K:2 * K + 6], theta[2 * K + 6:]
    cl = [gap_class(w, top, names, composed=True) for w, _ in items]
    us = [a[k] + b[k] * math.log(p) + (r[k] if i == 0 else 0.0) for i, ((w, p), k) in enumerate(zip(items, cl))]
    z = [1.0, math.log(max(1, n_lost)), 1.0 if whole else 0.0, math.log(max(1 - items[0][1], 1e-6)), 0.0, 1.0]
    u0 = sum(ci * zi for ci, zi in zip(c, z))
    mx = max(us + [u0])
    ex = [math.exp(u - mx) for u in us]
    tot = sum(ex) + math.exp(u0 - mx)
    out = {w: 0.0 for w in dist}
    out.update({w: e / tot for (w, _), e in zip(items, ex)})
    return out


def text_groups(translit: str, words: bool = False) -> tuple[list[str], list[int]]:
    """The carved groups with every lost rune ('-') written '?', and the groups followed by a break: text lost to an
    unknown extent ('...') or a sign that is not read, where the reading starts afresh. words=True: the editors' word
    boundaries too (the spaces of the transliteration), which the model otherwise chooses for itself."""
    groups, breaks = [], []
    for _, t in rl.sections(translit):
        for g in re.split(rl.DIV, rl.clean_translit(t)):
            for c in (g.split() if words else [re.sub(r"\s+", "", g)]):
                c = rl.runekey(c).replace("-", "?")
                pieces = re.split(r"([^a-zþðæøåöäąR?]+)", c)
                for q, p in enumerate(pieces):
                    if q % 2 == 1:  # a separator: a break after the group before it
                        if groups and p.strip():
                            breaks.append(len(groups) - 1)
                    elif p:
                        groups.append(p)
        if groups:
            breaks.append(len(groups) - 1)  # a new section starts afresh
    return groups, sorted(set(breaks))


def alternative_reading(translit: str) -> str | None:
    """The transliteration with Rundata's alternative readings (sections labelled Q) in place of the main ones, or None
    when there are none. On U Fv1971;212B the main reading divides s--ii ok, the alternative s--i iok."""
    secs, lab = [], ""
    for p in re.split(r"(§[A-Z]+)", translit or ""):
        if re.fullmatch(r"§[A-Z]+", p):
            lab = p[1:]
        elif p.strip():
            secs.append((lab, p))
    alt = {lab[:-1]: p for lab, p in secs if lab.endswith("Q")}
    if not alt:
        return None
    main = [(lab[:-1] if lab.endswith("P") else lab, p) for lab, p in secs if not lab.endswith("Q")]
    return " ".join(f"§{base or 'A'}X {alt.get(base, p)}" for base, p in main)


def _parts(groups, breaks):
    """The text without its open gaps: pieces of the groups and where the reading may break at no cost."""
    parts, sg, at = [], [], []
    for idx, grp in enumerate(groups):
        pieces = [p for p in grp.split("?") if p]
        for q, p in enumerate(pieces):
            parts.append(p)
            if q < len(pieces) - 1 or idx in breaks or (q == len(pieces) - 1 and grp.endswith("?")):
                sg.append(len(parts) - 1)
    return parts, sg


def _safe(signum: str) -> str:
    return re.sub(r"[^A-Za-z0-9ÅÄÖåäöÆØæø;_-]+", "_", signum)


def analyze(signum: str, allowed: dict | None = None, loo: bool = False) -> dict:
    """The model's reading of an inscription. allowed: {gap number: for each lost rune of the gap the runes its
    visible remains allow ('' or None: nothing visible)}; without it the result is cached. loo: read with the model
    learned from every other inscription (bundle_loo) instead of the one that has not seen the stone's whole part; the
    tests (VALIDATION) are made with the parts, so for a single stone the figures are if anything cautious."""
    d = _records()
    r = d["by"].get(signum)
    if r is None:
        raise KeyError(signum)
    base = {"signum": signum, "version": VERSION, "validation": VALIDATION, "model": "loo" if loo else "fold"}
    if not (rl.viking(r) and r.get("transliteration")):
        return {**base, "available": False,
                "reason": "Modellen är byggd för vikingatida inskrifter med en translitterering i Rundata."}
    path = os.path.join(CACHE_LOO if loo else CACHE, _safe(signum) + ".json")
    if not allowed and os.path.exists(path):
        try:
            # the test figures describe the model, not the stone: always today's (a batch may have saved older ones)
            return {**json.load(open(path, encoding="utf-8")), "validation": VALIDATION}
        except ValueError:
            pass
    groups, breaks = text_groups(r["transliteration"])
    if sum(len(g.replace("?", "")) for g in groups) < 4:
        return {**base, "available": False, "reason": "För få läsbara runor för att läsa texten."}
    b = bundle_loo(signum) if loo else bundle(fold_of(signum))
    with _compute:
        out = _read(r, groups, breaks, b, allowed, base, d)
    if not allowed:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False)
        os.replace(tmp, path)
    return out


def _offsets(groups):
    """Where each group starts in the text with every rune and lost rune counted."""
    out, at = [], 0
    for g in groups:
        out.append(at)
        at += len(g)
    return out


def _covering(intervals, a, e):
    """The (start, end) intervals that overlap [a, e)."""
    return {(s, t) for s, t in intervals if s < e and a < t}


def _read(r, groups, breaks, b, allowed, base, d, trace_at=None, alt=True):
    """trace_at: the traces by a lost rune's place in the text (every rune counted), instead of allowed – to carry them
    over to another division into words. alt: also read with the editors' word boundaries where they differ from the
    model's around a gap."""
    m = b["model"]
    site = (float(r["lat"]), float(r["lon"])) if r.get("lat") is not None and r.get("lon") is not None else None
    every = [(gi, x.start(), x.end()) for gi, g in enumerate(groups) for x in re.finditer(r"\?+", g)]
    # runs of lost runes close together in one group (?a??bi?rn) are filled as one (rl.merge_runs)
    _, runs, _, _ = rl.merge_runs(groups, every)
    lost = {sp: [i for i in range(sp[1], sp[2]) if groups[sp[0]][i] == "?"] for sp in runs}
    fillable = [sp for sp in runs if len(lost[sp]) <= MAX_GAP]
    work = list(groups)
    for gi, a, e in fillable:
        work[gi] = work[gi][:a] + "?" * (e - a) + work[gi][e:]
    off = _offsets(groups)
    if trace_at is not None:
        user = {}
        for sp in fillable:
            vals = [trace_at.get(off[sp[0]] + i) for i in lost[sp]]
            if any(vals):
                user[sp] = vals
    else:
        user = {fillable[int(n)]: v for n, v in (allowed or {}).items()
                if str(n).isdigit() and int(n) < len(fillable) and len(v) == len(lost[fillable[int(n)]])}
    trace_at = {off[sp[0]] + i: v for sp, vals in user.items() for i, v in zip(lost[sp], vals) if v}
    traces, hard = {}, {}
    for sp in fillable:
        gi, a, e = sp
        seen = dict(zip(lost[sp], user.get(sp, [None] * len(lost[sp]))))
        cons = [seen[i] or None if i in seen else groups[gi][i] for i in range(a, e)]
        if any(c is not None for c in cons):
            traces[sp] = cons
            hard[sp] = [i - a for i in range(a, e) if i not in seen]  # the preserved runes inside the gap
    details, positions = {}, {}
    near = [(la, lo, nm, ck) for sg, la, lo, nm, ck in d["sites"] if sg != r["signum"]]
    # the carver's own share of marked word boundaries (rl.stone_divider_rate), for the filling and the reading
    dr = rl.stone_divider_rate(m, work, breaks) if OWN_D else None
    combos, gaps, words = (rl.restore_all(m, work, signs=breaks, only=fillable, site=site, allowed=traces, details=details,
                                          positions=positions, hard=hard, near_sites=near, div_rate=dr, **FILL) if fillable else ([], [], {}))
    best = list(combos[0][0]) if combos else []
    if d.get("GL"):
        # the word with the highest calibrated probability is the gap's choice (textmodel-17): on the documented gaps the
        # model's own first choice was often a name it had composed where a formula word was right; the filling follows
        # the chosen word. Gaps whose filling covers two words (merge_runs) keep the model's choice.
        for n, (gi, a, e) in enumerate(gaps):
            wd = words.get(n) or {}
            if not wd or (positions.get(n) and len({max(p_, key=p_.get) for p_ in positions[n] if p_}) > 1):
                continue
            whole_pre = a == 0 and e == len(work[gi])
            cd = calibrate_words(wd, len(lost[(gi, a, e)]), d["GL"], whole_pre)
            w_star = max(cd, key=cd.get)
            if w_star == max(wd, key=wd.get) or cd[w_star] <= 0:
                continue
            lm = m.lemma(w_star)
            fits = [(p_, f_) for f_, p_, w_ in details.get(n, []) if w_ and w_ != "<unk>" and m.lemma(w_) == lm]
            if fits:
                best[n] = max(fits)[1]
    filled = list(groups)
    for (gi, a, e), f in sorted(zip(gaps, best), key=lambda x: (-x[0][0], -x[0][1])):
        filled[gi] = filled[gi][:a] + f + filled[gi][e:]
    parts, sg = _parts(filled, breaks)
    # read in the stone's branch of the spelling tree (era to landscape), as in the calibration
    _, read, _, text, _, ll = rl.decode_epochs(m, parts, sg, path=rl.context(r)[:5], d=dr)
    # each letter of the read text at its place among all runes, lost ones counted (open gaps are not in the text)
    at_rune = [off[gi] + k for gi, g in enumerate(filled) for k, c in enumerate(g) if c != "?"]
    # where the filled runes stand in the read text, and where the text breaks
    spans = []
    for (gi, a, e), f in zip(gaps, best):
        at = sum(len(x.replace("?", "")) for x in filled[:gi]) + len(filled[gi][:a].replace("?", ""))
        spans.append((at, at + len(f)))
    ends, pos = set(), 0
    for i, p in enumerate(parts):
        pos += len(p)
        if i in sg:
            ends.add(pos)
    n_lost = [len(lost[sp]) for sp in gaps]
    # a gap that covers a whole word of the reading (none of its runes preserved) is calibrated as such
    whole = [any(a_ <= i and j <= e_ for i, j, _, _ in read if i < e_ and a_ < j) for a_, e_ in spans]

    def cal_dist(dist, k, whole=False):
        if d.get("GL"):
            return calibrate_words(dist, k, d["GL"], whole)
        return cal_dist16(dist, k, whole)

    def cal_dist16(dist, k, whole=False):
        """The words of a gap with the model's first choice calibrated by its class (scripts/runlm_gap_calibrate.py) and
        the others at most at their own probability: scaled down when the first choice gains, never up when it loses;
        what is not given to any word is left unassigned. On the documented gaps (utdata/runlm_forfining/alt_kalib.py)
        the alternatives then got 44 right where 41 were, while sharing out what the first choice lost (textmodel-15)
        gave them 57 and made a strong alternative equal to the first choice. An alternative can thus end above the
        first choice, when the first is a word of a class the model is often wrong about (textmodel-16)."""
        if not d.get("G") or not dist:
            return dist
        w0, p0 = max(dist.items(), key=lambda kv: kv[1])
        if w0 == "<unk>" or p0 >= 1:
            return dist
        c0 = calibrate_gap(p0, w0, k, d["G"], whole)
        scale = min(1.0, (1 - c0) / (1 - p0))
        return {w: (c0 if w == w0 else p * scale) for w, p in dist.items()}

    def p_filled(i, j, w):
        """A word with filled runes is as probable as that word in its gaps (the reading itself takes the filling as
        given): the smallest probability of the word over the gap positions it covers. A gap of two runs filled as
        one can cover the end of one word and the start of the next; each word is judged where it stands."""
        def q(dist):
            return (sum(q_ for w_, q_ in dist.items() if w_ != "<unk>" and rl.same_word(w_, w)) if w != "<unk>"
                    else dist.get("<unk>", 0.0))
        qs = [q(cal_dist(positions[n][o] if positions.get(n) else words.get(n, {}), n_lost[n], whole[n]))
              for n, (a_, e_) in enumerate(spans) if i < e_ and a_ < j
              for o in range(max(i, a_) - a_, min(j, e_) - a_)]
        return min(qs) if qs else None

    reading = []
    for i, j, w, p in read:
        filled = any(i < e_ and a_ < j for a_, e_ in spans)
        pf = p_filled(i, j, w) if filled else None
        reading.append({"runes": text[i:j], "word": w.lstrip("§"), "name": w.startswith("§"), "unknown": w == "<unk>",
                        "p": round(pf if pf is not None else recal(b, p, w, text[i:j], d["B"]), 4), "filled": filled,
                        "break_after": j in ends})
    prior = {e: (m.epoch_prior[e] or 1) for e in rl.EPOCHS}
    dating = rl.epoch_posterior(ll, prior, d["T"] or 1.0)
    vocab = [w for _, _, w, _ in read]
    out = {
        **base, "available": True, "computed_at": datetime.now(timezone.utc).isoformat(), "calibrated": bool(d["B"]), "gap_calibrated": bool(d.get("G")),
        "groups": groups, "reading": reading,
        "gaps": [{"number": n, "group": gi, "start": a, "end": e, "carved": groups[gi], "n": len(lost[(gi, a, e)]),
                  "lost": [i - a for i in lost[(gi, a, e)]],
                  "best": best[n] if n < len(best) else None,
                  "fills": [{"fill": f, "p": round(p, 4), "word": (w or "").lstrip("§") or None}
                            for f, p, w in details.get(n, [])[:8]],
                  # the model's six best words, shown most probable first by their calibrated percentage
                  "words": sorted(({"word": w.lstrip("§"), "p": round(cd[w], 4), "p_model": round(p, 4)}
                                   for cd in [cal_dist(words.get(n, {}), len(lost[(gi, a, e)]), whole[n])]
                                   for w, p in list(words.get(n, {}).items())[:6]), key=lambda x: -x["p"]),
                  "traces": user.get((gi, a, e))}
                 for n, (gi, a, e) in enumerate(gaps)],
        "open_gaps": [{"group": gi, "start": a, "end": e, "n": len(lost[(gi, a, e)])} for gi, a, e in runs
                      if (gi, a, e) not in fillable],
        "dating": {"epochs": [{"epoch": e, "label": EPOCH_LABEL[e], "p": round(dating[e], 4)} for e in rl.EPOCHS],
                   "calibrated": bool(d["T"]), "rundata": r.get("dating") or ""},
        "translation": {"sv": rg.swedish(vocab, b["en"], b["da"], b["ows"]), "en": b["en"].translate(vocab)},
    }
    if alt and len(at_rune) == len(text):
        out["boundaries"] = _boundaries(r, groups, gaps, best, words, read, spans, at_rune, trace_at, b, base, d)
    return out


def _boundaries(r, groups, gaps, best, words, read, spans, at_rune, trace_at, b, base, d):
    """Where a gap's word depends on a word boundary. Runic texts are often written without dividers, and the model then
    chooses where the words begin – and may borrow runes from a word it does not know (U Fv1971;212B: Víseti across
    Ragnví). For each of the editors' divisions into words (Rundata's main reading and its alternative, when they have
    the same runes and differ only in the boundaries) whose words around a gap differ from the model's, the text is read
    again with those boundaries – only where the model's word around a gap runs across one of the editors' boundaries,
    since reading the text again doubles the time; the gaps whose best word then changes are returned."""
    flat = "".join(groups)
    out, seen = [], set()
    for variant, tr in (("main", r["transliteration"]), ("alt", alternative_reading(r["transliteration"]))):
        if not tr:
            continue
        eg, eb = text_groups(tr, words=True)
        if "".join(eg) != flat or tuple(eg) in seen:
            continue
        seen.add(tuple(eg))
        eoff = _offsets(eg)
        theirs = [(s, s + len(g)) for s, g in zip(eoff, eg)]
        cuts = set(eoff[1:])
        off = _offsets(groups)
        differ = []
        for n, ((gi, a, e), (ta, te)) in enumerate(zip(gaps, spans)):
            fa, fe = off[gi] + a, off[gi] + e
            model_iv = {(at_rune[i], at_rune[j - 1] + 1) for i, j, _, _ in read if i < te and ta < j and j > i}
            # only where the model's word runs across a boundary the editors draw, borrowing runes from the next word
            if any(s < c < t for s, t in model_iv for c in cuts):
                differ.append((n, fa, fe, model_iv))
        if not differ:
            continue
        other = _read(r, eg, eb, b, None, base, d, trace_at=trace_at, alt=False)
        for n, fa, fe, model_iv in differ:
            og = next((g for g in other.get("gaps", []) if eoff[g["group"]] + g["start"] < fe and fa < eoff[g["group"]] + g["end"]), None)
            if not og or not og["words"] or not words.get(n):
                continue
            top_mine, top_theirs = max(words[n], key=words[n].get).lstrip("§"), og["words"][0]["word"]
            unknown = (top_mine == "<unk>", top_theirs == "<unk>")
            if all(unknown) or (not any(unknown) and rl.same_word(top_mine, top_theirs)):
                continue  # the same answer either way
            s0, s1 = min(s for s, _ in model_iv), max(t for _, t in model_iv)
            ew = sorted(_covering(theirs, fa, fe))
            out.append({"gap": n, "variant": variant, "model_runes": flat[s0:s1],
                        "model_fill": best[n] if n < len(best) else None,
                        "editor_runes": " ".join(flat[s:t] for s, t in ew), "best": og["best"],
                        "words": og["words"][:5]})
    return out
