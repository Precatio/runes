"""Sannolikhetsmodell för vikingatida runtext: läser en inskrifts huggna grupper utan att låna någon tolkning.

Modellen är en brusig kanal i två steg:
  1. Språket: vilka ord följer på vilka. Ett bigram med absolut rabatt (Kneser–Ney) över Rundatas normaliserade
     vikingatida inskrifter, blandat med ordförrådet i Eddan och Snorres Edda (ett yngre, isländskt men besläktat
     språk, med liten vikt) och med ett "okänt ord" vars runor kommer från en teckenmodell.
  2. Stavningen: hur ett ord skrivs med 16 runor. Varje ord har en regelbaserad mängd möjliga stavningar
     (a → a/ą, æ → a/i/e, nasal före klusil kan falla bort …) vars sannolikheter skattas (EM) från runristarnas
     faktiska stavningar i Rundata. Ord med egna belägg får dessutom sina faktiska stavningar.
Avkodningen räknar framåt och bakåt över alla sätt att dela de huggna grupperna i ord. Skiljetecken är alltid
ordgränser; en ordgräns utan skiljetecken kostar (1 − d), en med kostar d. Resultatet är, för varje del av texten,
sannolikheten för varje ord givet runorna och språket, och den totala sannolikheten för texten, som gör att
omstridda runor kan jämföras.

Data: Rundata (data/rundata.json) och, om den är nedladdad, Eddan och Snorres Edda från heimskringla.no som
{verk: text} (EDDA). Används av scripts/runlm_calibrate.py (provet på inskrifter med känd läsning) och
scripts/malt_decode.py (Maltstenen). Metod: METHODS.md, avsnitt 8.
"""
import json
import math
import os
import re
import unicodedata
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDDA = os.path.join(ROOT, "utdata/Malt/kallor/edda.json")


def load_rundata(path=os.path.join(ROOT, "data/rundata.json")):
    """All inscriptions in Rundata (data/rundata.json) as a list of records."""
    data = json.load(open(path))
    return [r for r in (data["inscriptions"] if "inscriptions" in data else data.values()) if isinstance(r, dict)]


viking = lambda r: (r.get("period") or "").startswith("V") and not (r.get("flags") or {}).get("medieval")
DIV = r"[:÷'·×+]"
RUNES = set("fuþorkhniastbmlRyeæøcdgpvqxzåäö")


def sections(t):
    """Rundata's sections; alternative readings (labels ending in Q) are dropped, so each text is counted once."""
    parts = re.split(r"(§[A-Z]+)", t or "")
    out, lab = [], ""
    for p in parts:
        if re.fullmatch(r"§[A-Z]+", p):
            lab = p[1:]
            continue
        if lab.endswith("Q") and lab != "Q" or lab == "Q":
            continue
        if p.strip():
            out.append((lab.rstrip("P") or "-", p))
    return out


def clean_translit(s):
    s = re.sub(r"<([^>]*)>", r"\1", s)            # cipher runes: their transliteration
    s = s.replace("¶", "").replace("| |", " ").replace("|", "")
    s = re.sub(r"[()\[\]{}^]", "", s)
    return s


def translit_words(s):
    """Rundata's words in the transliteration (its spaces are an interpretation – used only for training)."""
    s = clean_translit(s)
    return [w for w in re.split(rf"\s+|{DIV}", s) if w]


def norm_words(s):
    s = re.sub(r"<([^>]*)>", r"\1", s)
    s = re.sub(r"(\S+)/\S+", r"\1", s)            # alternatives: the first
    s = s.replace("[", "").replace("]", "").replace('"', "").replace("(?)", "")
    return [w for w in re.split(r"[\s,.;:!?]+", s) if re.search(r"\w", w)]


def is_runes(w):
    return bool(w) and all(ch in RUNES for ch in w)


def pairs(r):
    """(rune word, normalized word) for every section whose word counts agree; None if nothing aligns."""
    T = dict((lab, p) for lab, p in sections(r.get("transliteration")))
    N = dict((lab, p) for lab, p in sections(r.get("normalization")))
    out = []
    for lab, t in T.items():
        if lab not in N:
            continue
        a, b = translit_words(t), norm_words(N[lab])
        if len(a) == len(b) and a:
            out.extend(zip(a, b))
    return out


def carved_groups(t):
    """The inscription as the carver divided it: groups between dividers (line breaks are not dividers)."""
    out = []
    for lab, p in sections(t):
        p = clean_translit(p)
        for g in re.split(DIV, p):
            g = re.sub(r"\s+", "", g)
            if g:
                out.append(g)
    return out


def edda_tokens(path=EDDA):
    """Word tokens of the Eddic poems and Snorri's Edda (heimskringla.no, {work: text}), without the site's
    boilerplate. Empty if the file has not been downloaded."""
    out = []
    if not os.path.exists(path):
        return out
    for work, text in json.load(open(path)).items():
        i = text.find("prentunar")
        text = text[i + 9:] if i >= 0 else " ".join(text.split()[60:])
        out.extend(w.lower() for w in re.findall(r"[A-Za-zÀ-ÿĀ-žǫę]+", text))
    return out


# ---- spelling: normalized form → rune strings ----------------------------------------------------------------------
UNITS = ["æi", "ei", "ey", "øy", "au", "ng", "nk", "nd", "nt", "mb", "mp", "kk", "gg", "tt", "dd", "ll", "nn", "ss", "rr", "pp", "ff", "mm"]
CHOICES = {
    "a": ["a", "o"], "á": ["a", "o"], "ą": ["o", "a"],
    "æ": ["a", "i", "e"], "e": ["i", "a", "e"], "é": ["i", "a", "e"], "ę": ["i", "a", "e"],
    "i": ["i"], "í": ["i"], "j": ["i", ""], "y": ["u", "y", "i"], "ý": ["u", "y"],
    "o": ["u", "o"], "ó": ["u", "o"], "ǫ": ["u", "o", "a"], "ö": ["u", "o", "a"], "ø": ["u", "o", "au", "y"], "œ": ["u", "o", "y"],
    "u": ["u", "o"], "ú": ["u", "o"], "v": ["u", ""], "w": ["u", ""],
    "æi": ["ai", "i", "a", "e"], "ei": ["ai", "i", "a", "e"], "ey": ["au", "u", "y", "ou"], "øy": ["au", "u", "y", "ou"],
    "au": ["au", "u", "o", "ou"],
    "þ": ["þ", "t"], "ð": ["þ", "t"], "t": ["t", "þ"], "d": ["t", "þ"], "b": ["b"], "p": ["b", "p"],
    "g": ["k", "g"], "k": ["k"], "c": ["k"], "q": ["k"], "x": ["ks", "s"], "z": ["s", "ts"],
    "f": ["f"], "h": ["h", ""], "l": ["l"], "m": ["m"], "n": ["n"], "s": ["s"], "r": ["r", "R"], "R": ["R", "r"],
    "ng": ["nk", "k", "ng"], "nk": ["nk", "k"], "nd": ["nt", "t"], "nt": ["nt", "t"], "mb": ["mb", "b", "m"], "mp": ["mb", "b"],
}
for dbl in ("kk", "gg", "tt", "dd", "ll", "nn", "ss", "rr", "pp", "ff", "mm"):
    CHOICES[dbl] = list(CHOICES[dbl[0]])  # runes do not write double letters


def units(w):
    out, i = [], 0
    while i < len(w):
        if w[i:i + 2] in UNITS:
            out.append(w[i:i + 2]); i += 2
        else:
            out.append(w[i]); i += 1
    return [u for u in out if u in CHOICES]


def runekey(s):
    """A rune string as the carver wrote it: lower case except ʀ, older-futhark capitals lowered."""
    return "".join(ch if ch == "R" else ch.lower() for ch in s)


def normtok(w):
    return (w[:1].lower() + "".join(ch if ch == "R" else ch.lower() for ch in w[1:])) if w else w


class Spelling:
    def __init__(self, train_pairs):
        self.p = {u: {c: 1.0 / len(cs) for c in cs} for u, cs in CHOICES.items()}
        for _ in range(3):  # EM: fractional counts over the expansions that reproduce the carver's spelling
            cnt = defaultdict(Counter)
            for rune, norm in train_pairs:
                exp = self._derivations(norm, rune)
                tot = sum(p for p, _ in exp)
                if tot <= 0:
                    continue
                for p, path in exp:
                    for u, c in path:
                        cnt[u][c] += p / tot
            for u, cs in CHOICES.items():
                n = sum(cnt[u].values())
                self.p[u] = {c: (cnt[u][c] + 0.5) / (n + 0.5 * len(cs)) for c in cs}
        self.cover = sum(1 for r, n in train_pairs if self._derivations(n, r)) / max(1, len(train_pairs))

    def _derivations(self, norm, rune):
        """All ways the rules turn the normalized word into exactly this rune string, with probabilities."""
        us = units(norm)
        out = []

        def go(i, pos, prob, path):
            if len(out) > 50:
                return
            if i == len(us):
                if pos == len(rune):
                    out.append((prob, path))
                return
            for c, pc in self.p[us[i]].items():
                if rune.startswith(c, pos):
                    go(i + 1, pos + len(c), prob * pc, path + [(us[i], c)])
        go(0, 0, 1.0, [])
        return out

    def expand(self, norm, beam=400, edda=False):
        """The most probable rune spellings of a normalized word (sum over derivations), renormalized. For words
        known only from the Icelandic texts, æ may also continue the older diphthong æi (written ai in runes)."""
        states = {"": 1.0}
        us = units(norm)
        for k, u in enumerate(us):
            choice = self.p[u]
            if edda and u in ("æ", "ǽ"):
                choice = {**{c: q * 0.7 for c, q in choice.items()}, "ai": 0.3}
            if edda and u == "r" and k == len(us) - 1 and len(us) > 1:
                choice = {"R": 0.5, "r": 0.5}  # Icelandic final -r continues older ʀ in endings (-aʀ, -iʀ, -ʀ)
            nxt = defaultdict(float)
            for s, p in states.items():
                for c, pc in choice.items():
                    nxt[s + c] += p * pc
            top = max(nxt.values())
            states = dict(sorted(((k, v) for k, v in nxt.items() if v > top * 1e-5), key=lambda kv: -kv[1])[:beam])
        out = defaultdict(float)
        for s, p in states.items():
            if s:
                out[re.sub(r"(.)\1+", r"\1", s)] += p
        z = sum(out.values()) or 1
        return {s: p / z for s, p in out.items()}


# ---- language: Kneser–Ney bigram over normalized runic text + Edda unigram + unknown word -------------------------
class CharModel:
    """Trigram over runes inside words (with an end mark), for words the lexicon does not know."""
    def __init__(self, words):
        self.c3, self.c2 = Counter(), Counter()
        self.alpha = sorted({ch for w in words for ch in w} | {"$"})
        for w in words:
            s = "^^" + w + "$"
            for i in range(2, len(s)):
                self.c3[s[i - 2:i + 1]] += 1
                self.c2[s[i - 2:i]] += 1

    def logp(self, w):
        s = "^^" + w + "$"
        V = len(self.alpha)
        return sum(math.log((self.c3[s[i - 2:i + 1]] + 0.1) / (self.c2[s[i - 2:i]] + 0.1 * V)) for i in range(2, len(s)))


class Model:
    def __init__(self, recs, edda_tokens=(), lam_edda=0.03, lam_unk=0.01, D=0.75, d=None, kappa=2.0, exclude=()):
        recs = [r for r in recs if r["signum"] not in set(exclude)]
        tp = [(runekey(a), normtok(b)) for r in recs for a, b in pairs(r) if is_runes(runekey(a).lower())]
        self.spell = Spelling(tp)
        self.emp = defaultdict(Counter)
        for a, b in tp:
            self.emp[b][re.sub(r"(.)\1+", r"\1", a)] += 1
        # bigram counts within sections
        self.big, self.uni, self.hist = Counter(), Counter(), Counter()
        for r in recs:
            for _, p in sections(r.get("normalization")):
                ws = ["<s>"] + [normtok(w) for w in norm_words(p)]
                for a, b in zip(ws, ws[1:]):
                    self.big[(a, b)] += 1
                    self.hist[a] += 1
                self.uni.update(ws[1:])
        self.follow = defaultdict(set)
        cont = Counter()
        for (a, b) in self.big:
            self.follow[a].add(b)
            cont[b] += 1
        nb = len(self.big)
        self.pc = {w: c / nb for w, c in cont.items()}
        self.D = D
        self.gamma = {a: D * len(self.follow[a]) / self.hist[a] for a in self.hist}
        ec = Counter(normtok(w) for w in edda_tokens)
        ne = sum(ec.values()) or 1
        self.pe = {w: c / ne for w, c in ec.items()}
        self.lam_edda, self.lam_unk = lam_edda, lam_unk
        self.char = CharModel([a for a, _ in tp])
        # divider rate: share of word boundaries marked by a divider in the carved texts
        nd = nb_ = 0
        for r in recs:
            for _, p in sections(r.get("transliteration")):
                ws = translit_words(p)
                gs = carved_groups("§A " + p) if p else []
                if len(ws) > 1 and gs:
                    nb_ += len(ws) - 1
                    nd += min(len(gs), len(ws)) - 1
        self.d = min(max(d if d is not None else (nd / nb_ if nb_ else 0.5), 0.01), 0.99)
        # index: rune string → {word: P(runes | word)}
        self.index = defaultdict(dict)
        vocab = sorted(set(self.uni) | set(self.pe))  # a fixed order, so that runs are reproducible
        for w in vocab:
            if not re.fullmatch(r"[a-zþðæøåöäąǫœáéíóúýęR]+", w):
                continue
            n = sum(self.emp[w].values())
            rule = self.spell.expand(w, edda=(w not in self.uni))
            ps = {s: (kappa / (n + kappa)) * p for s, p in rule.items()}
            for s, c in self.emp[w].items():
                ps[s] = ps.get(s, 0) + c / (n + kappa)
            for s, p in ps.items():
                if p > 1e-4:
                    self.index[s][w] = p
        self.maxlen = max(len(s) for s in self.index)

    def p_word(self, w, prev):
        """P(w | prev) for a lexicon word (the unknown word is handled separately)."""
        lr = 1 - self.lam_edda - self.lam_unk
        pc = self.pc.get(w, 0.0)
        if prev in self.hist:
            pk = max(self.big.get((prev, w), 0) - self.D, 0) / self.hist[prev] + self.gamma[prev] * pc
        else:
            pk = pc
        return lr * pk + self.lam_edda * self.pe.get(w, 0.0)

    def candidates(self, s):
        out = dict(self.index.get(s, {}))
        out["<unk>"] = math.exp(self.char.logp(s))
        return out


def key(w):
    """The same word in another normalization: Old Danish, Old Swedish and Icelandic spellings brought together
    (stæinn = sten = steinn, sin = sinn, þøsi = þausi, faður = faþur), but different words kept apart."""
    if w == "<unk>":
        return w
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(ch for ch in w if unicodedata.category(ch) != "Mn")
    for a, b in (("ð", "þ"), ("w", "v"), ("ǫ", "o"), ("ø", "o"), ("œ", "o"), ("æi", "e"), ("ei", "e"), ("ai", "e"),
                 ("au", "o"), ("ey", "o"), ("oy", "o"), ("æ", "e"), ("y", "u"), ("pt", "ft")):
        w = w.replace(a, b)
    return re.sub(r"(.)\1+", r"\1", w)


def _lse(xs):
    m = max(xs)
    return m + math.log(sum(math.exp(x - m) for x in xs)) if m > float("-inf") else m


def decode(model, groups, signs=(), lexicon=True):
    """Forward–backward over the carved text. `groups` are the carver's groups (a divider between each);
    `signs` are indices of groups followed by a non-runic sign or the futhark row (a boundary at no cost).
    Returns (log P(text), best path [(start, end, word, posterior)], span posteriors {(i, j, w): p}, text)."""
    text = "".join(groups)
    L = len(text)
    div, free, pos = set(), set(), 0
    for gi, g in enumerate(groups[:-1]):
        pos += len(g)
        (free if gi in signs else div).add(pos)
    d = model.d
    lbf = lambda i: 0.0 if (i == 0 or i in free) else math.log(d if i in div else 1 - d)

    starts = defaultdict(list)  # start → [(end, word, log P(runes | word))]
    for i in range(L):
        for j in range(i + 1, min(L, i + model.maxlen) + 1):
            if any(b in div or b in free for b in range(i + 1, j)):
                break
            for w, ps in model.candidates(text[i:j]).items():
                if ps > 0 and (lexicon or w == "<unk>"):
                    starts[i].append((j, w, math.log(ps)))
    ltrans = {}

    def lt(w, prev):
        k = (w, prev)
        if k not in ltrans:
            p = model.lam_unk if w == "<unk>" else model.p_word(w, prev)
            ltrans[k] = math.log(p) if p > 0 else float("-inf")
        return ltrans[k]

    # forward: la[j][w] = log P(runes before j, last word w ends at j)
    la = [dict() for _ in range(L + 1)]
    la[0]["<s>"] = 0.0
    incoming = [defaultdict(list) for _ in range(L + 1)]
    for i in range(L + 1):
        if i > 0:
            la[i] = {w: _lse(v) for w, v in incoming[i].items()}
            incoming[i] = None
        if not la[i] or i == L:
            continue
        for j, w, lps in starts[i]:
            s_ = _lse([a + lt(w, prev) for prev, a in la[i].items()])
            incoming[j][w].append(s_ + lbf(i) + lps)
    logZ = _lse(list(la[L].values())) if la[L] else float("-inf")

    # backward: lb[i][prev] = log P(runes from i on | previous word prev ended at i)
    lb = [dict() for _ in range(L + 1)]
    lb[L] = {w: 0.0 for w in la[L]}
    for i in range(L - 1, -1, -1):
        if not la[i]:
            continue
        acc = defaultdict(list)
        for j, w, lps in starts[i]:
            if w not in lb[j]:
                continue
            base = lbf(i) + lps + lb[j][w]
            for prev in la[i]:
                acc[prev].append(lt(w, prev) + base)
        lb[i] = {prev: _lse(v) for prev, v in acc.items()}

    post = {}
    for i in range(L):
        if not la[i]:
            continue
        for j, w, lps in starts[i]:
            if w not in lb[j]:
                continue
            v = _lse([a + lt(w, prev) for prev, a in la[i].items()]) + lbf(i) + lps + lb[j][w] - logZ
            if v > -30:
                post[(i, j, w)] = post.get((i, j, w), 0.0) + math.exp(v)

    # the same word in several normalizations counts as one reading of the span
    grp = defaultdict(float)
    top = {}
    for (i, j, w), p in post.items():
        k = (i, j, key(w))
        grp[k] += p
        if k not in top or p > post[(i, j, top[k])]:
            top[k] = w
    # the path with the highest expected number of correctly read runes (posterior × length)
    byend = defaultdict(list)
    for (i, j, k), p in grp.items():
        byend[j].append((i, top[(i, j, k)], p))
    best = [(-1.0, None)] * (L + 1)
    best[0] = (0.0, None)
    for j in range(1, L + 1):
        for i, w, p in byend[j]:
            if best[i][0] >= 0 and best[i][0] + p * (j - i) > best[j][0]:
                best[j] = (best[i][0] + p * (j - i), (i, w, p))
    path, j = [], L
    while j > 0 and best[j][1]:
        i, w, p = best[j][1]
        path.append((i, j, w, p))
        j = i
    return logZ, path[::-1], post, text
