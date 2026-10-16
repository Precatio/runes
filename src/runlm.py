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
import difflib
import itertools
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


def pairs(r, aligned=False):
    """(rune word, normalized word) for every section whose word counts agree. With aligned=True, sections whose
    counts differ are lined up by `align` (step 2: damaged and restored words no longer cost the whole section)."""
    T = dict((lab, p) for lab, p in sections(r.get("transliteration")))
    N = dict((lab, p) for lab, p in sections(r.get("normalization")))
    out = []
    for lab, t in T.items():
        if lab not in N:
            continue
        a, b = translit_words(t), norm_words(N[lab])
        if len(a) == len(b) and a:
            out.extend(zip(a, b))
        elif aligned and a and b:
            out.extend(align(a, b))
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


# ---- context: era, epoch, area, region and carver of an inscription -------------------------------------------------
EPOCHS = ("800", "900", "1000", "1100")  # 800-talet, 900-talet, 1000–1070, 1070–1150
PHASE = {"800": "tidig", "900": "tidig", "1000": "sen", "1100": "sen", "M": "M"}  # early and late Viking Age
STYLE_YEARS = {"RAK": (980, 1015), "Fp": (1010, 1040), "KB": (1010, 1050), "Pr1": (1010, 1050), "Pr2": (1020, 1050),
               "Pr3": (1045, 1075), "Pr4": (1070, 1100), "Pr5": (1100, 1130)}
AREAS = {"Danmark": "DR DE", "Norge": "N", "Svealand": "U Sö Vs Nä Gs D Vr", "Götaland": "Ög Vg Sm Öl Bo Ds", "Gotland": "G",
         "Norrland": "Hs M J Ån Lp Hr", "Västerled": "IM IR E Or Sc Sh FR IS GR NL F IT", "Österled": "RU PL By UA LV FI"}
AREA_OF = {pre: area for area, pres in AREAS.items() for pre in pres.split()}


def years(dating):
    """An approximate (first, last) year from Rundata's dating, or None: 'V 1065-1075', 'V s 1000-t', 'V ca 1100' …"""
    d = (dating or "")
    if "Helnæs" in d:
        return (750, 900)
    if "för-Jelling" in d:
        return (900, 950)
    if "efter-Jelling" in d:
        return (1000, 1050) if "Jelling el." not in d else (950, 1050)
    if "Jelling" in d:
        return (950, 1000)
    spans = []
    for m in re.finditer(r"(?:(b|m|s|första hälften av|andra hälften av)\s+)?(?<![/\d])(\d{3,4})(?:-(\d{3,4}))?(-t)?", d):
        part, y1, y2, cent = m.group(1), int(m.group(2)), m.group(3) and int(m.group(3)), m.group(4)
        if cent:  # a century, possibly 'NNN-NNN-t'
            lo, hi = y1, (y2 or y1) + 99
            sub = {"b": (0, 33), "m": (33, 66), "s": (66, 99), "första hälften av": (0, 50), "andra hälften av": (50, 99)}.get(part)
            if sub and not y2:
                lo, hi = y1 + sub[0], y1 + sub[1]
        elif y2:
            lo, hi = y1, y2
        else:
            lo, hi = ((y1 - 10, y1 + 10) if "ca" in d else (y1, y1 + 50) if ("efter" in d or "inte före" in d) else
                      (y1 - 50, y1) if "före" in d else (y1, y1))
        spans.append((lo, hi))
    if not spans:
        return None
    return (min(x for x, _ in spans), max(y for _, y in spans))


def epoch(r):
    """The inscription's epoch from Rundata's dating or, for Swedish stones, its ornamental style; None if unknown
    or too wide (more than 120 years). Medieval inscriptions are 'M'."""
    if (r.get("period") or "").startswith("M"):
        return "M"
    y = years(r.get("dating")) if not (r.get("dating") or "").startswith("V/M") else None
    if y is None and "Helnæs" in (r.get("rune_types") or ""):
        y = (750, 900)
    if y is None:
        st = re.findall(r"RAK|Fp|KB|Pr\d", r.get("style") or "")
        if st:
            y = (min(STYLE_YEARS[x][0] for x in st), max(STYLE_YEARS[x][1] for x in st))
    if y is None or y[1] - y[0] > 120:
        return None
    mid = (y[0] + y[1]) / 2
    return "800" if mid < 900 else "900" if mid < 1000 else "1000" if mid < 1070 else "1100" if mid <= 1150 else None


def context(r, epoch_=None):
    """The inscription's place in the spelling tree: (era, phase, epoch, area, region, carver), where the phase is the
    early (800- and 900-talet) or late (1000–1150) Viking Age, so that an epoch with few stones leans on its phase.
    An unknown epoch is '?'."""
    pre = re.match(r"\S+", r["signum"]).group(0)
    era = "M" if (r.get("period") or "").startswith("M") else "V"
    ep = epoch_ or epoch(r) or "?"
    cv = [c["name"] for c in (r.get("carvers") or []) if isinstance(c, dict) and not c.get("uncertain")]
    return (era, PHASE.get(ep, "?"), ep, AREA_OF.get(pre, "Övrigt"), pre, cv[0] if len(cv) == 1 else None)


def _cls(w):
    """A word in coarse sound classes, for lining up carved and normalized words: vowels V, stops by place."""
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(ch for ch in w if unicodedata.category(ch) != "Mn")
    out = []
    for ch in w:
        c = ("V" if ch in "aæeiouyøǫąåöäœ" else "U" if ch in "vw" else "T" if ch in "þðdt" else "K" if ch in "gkcq" else
             "B" if ch in "bp" else "S" if ch in "sz" else "I" if ch == "j" else "" if ch == "h" else ch.upper() if ch.isalpha() else "")
        out.append(c)
    s = re.sub(r"(.)\1+", r"\1", "".join(out).replace("U", "V").replace("I", "V"))
    return re.sub(r"N(?=[TK])|M(?=B)", "", s)


def _lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def similarity(rune, norm):
    a, b = _cls(rune), _cls(norm)
    return 1 - _lev(a, b) / max(len(a), len(b), 1)


def align(a, b):
    """Line up carved words a with normalized words b when their counts differ (damaged words, restored words,
    compounds). Dynamic programming over 1:1, skips and 2:1/1:2 merges; returns the 1:1 pairs that are clearly
    the same word (runic, similarity ≥ 0.6, and exact in sound classes for words of one or two classes)."""
    n, m = len(a), len(b)
    NEG = float("-inf")
    best = [[NEG] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    best[0][0] = 0.0
    run = [is_runes(runekey(w).lower()) for w in a]
    for i in range(n + 1):
        for j in range(m + 1):
            v = best[i][j]
            if v == NEG:
                continue
            moves = []
            if i < n and j < m:
                moves.append((i + 1, j + 1, (similarity(a[i], b[j]) - 0.5) if run[i] else -0.1, "1:1"))
            if i < n:
                moves.append((i + 1, j, -0.3, "a"))
            if j < m:
                moves.append((i, j + 1, -0.3, "b"))
            if i + 1 < n and j < m and run[i] and run[i + 1]:
                moves.append((i + 2, j + 1, similarity(a[i] + a[i + 1], b[j]) - 0.6, "2:1"))
            if i < n and j + 1 < m and run[i]:
                moves.append((i + 1, j + 2, similarity(a[i], b[j] + b[j + 1]) - 0.6, "1:2"))
            for ii, jj, sc, kind in moves:
                if v + sc > best[ii][jj]:
                    best[ii][jj] = v + sc
                    back[ii][jj] = (i, j, kind)
    out, i, j = [], n, m
    while (i, j) != (0, 0) and back[i][j]:
        pi, pj, kind = back[i][j]
        if kind == "1:1" and run[pi]:
            sim = similarity(a[pi], b[pj])
            if sim >= 0.6 and (len(_cls(a[pi])) > 2 or sim == 1.0):
                out.append((a[pi], b[pj]))
        i, j = pi, pj
    return out[::-1]


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


def choice_table(table, us, k, edda):
    """The rule choices for unit us[k]. For words known only from the Icelandic texts, æ may continue the older
    diphthong æi (written ai in runes), and a final -r the older ʀ of endings (-aʀ, -iʀ, -ʀ)."""
    u = us[k]
    choice = table[u]
    if edda and u in ("æ", "ǽ"):
        choice = {**{c: q * 0.7 for c, q in choice.items()}, "ai": 0.3}
    if edda and u == "r" and k == len(us) - 1 and len(us) > 1:
        choice = {"R": 0.5, "r": 0.5}
    return choice


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
                    for u, c, _ in path:
                        cnt[u][c] += p / tot
            for u, cs in CHOICES.items():
                n = sum(cnt[u].values())
                self.p[u] = {c: (cnt[u][c] + 0.5) / (n + 0.5 * len(cs)) for c in cs}
        self.cover = sum(1 for r, n in train_pairs if self._derivations(n, r)) / max(1, len(train_pairs))

    def _derivations(self, norm, rune, table=None, edda=False):
        """All ways the rules turn the normalized word into exactly this rune string, with their probabilities under
        `table` (the global choice probabilities if None). Paths are lists of (unit, choice, position)."""
        us = units(norm)
        out = []

        def go(i, pos, prob, path):
            if len(out) > 50:
                return
            if i == len(us):
                if pos == len(rune):
                    out.append((prob, path))
                return
            for c, pc in choice_table(table or self.p, us, i, edda).items():
                if rune.startswith(c, pos):
                    go(i + 1, pos + len(c), prob * pc, path + [(us[i], c, i)])
        go(0, 0, 1.0, [])
        return out

    def expected_counts(self, norm, rune, table=None, edda=False):
        """How often each rule choice was used in writing this word with these runes (expected over derivations)."""
        exp = self._derivations(norm, rune, table, edda)
        tot = sum(p for p, _ in exp)
        out = Counter()
        if tot > 0:
            for p, path in exp:
                for u, c, _ in path:
                    out[(u, c)] += p / tot
        return out

    def expand(self, norm, beam=400, edda=False, mass=False):
        """The most probable rune spellings of a normalized word (sum over derivations), renormalized. For words
        known only from the Icelandic texts, æ may also continue the older diphthong æi (written ai in runes)."""
        states = {"": 1.0}
        us = units(norm)
        for k, u in enumerate(us):
            choice = choice_table(self.p, us, k, edda)
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
        res = {s: p / z for s, p in out.items()}
        return (res, z) if mass else res


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


# ---- names: two elements and an ending (Ás-bjǫrn-aʀ), for names the vocabulary has never seen -----------------------
NAME_ENDINGS = ["aR", "iR", "uR", "ar", "ir", "ur", "R", "r", "s", "a", "i", "u", ""]


class NameModel:
    """Names as first element + second element + ending, or as a simple stem + ending, learned from the names in the
    training texts (Rundata marks names with a quotation mark). Each part is spelled with the spelling model; a name
    the vocabulary does not know can then still be read, e.g. osbiarnaR as as + biarn + aR."""
    def __init__(self, names, spell, min_share=3):
        def stem(n):
            for e in NAME_ENDINGS:
                if e and n.endswith(e) and len(n) - len(e) >= 3:
                    return n[:-len(e)], e
            return n, ""
        stems, ends = Counter(), Counter()
        for n, c in names.items():
            st, e = stem(n)
            stems[st] += c
            ends[e] += c
        pre, suf = Counter(), Counter()
        for st in stems:
            for i in range(2, len(st) - 2):
                pre[st[:i]] += 1
                suf[st[i:]] += 1
        first, second, simple = Counter(), Counter(), Counter()
        for st, c in stems.items():
            best = None
            for i in range(2, len(st) - 2):
                a, b = st[:i], st[i:]
                if pre[a] >= min_share and suf[b] >= min_share:
                    sc = min(pre[a], suf[b])
                    if not best or sc > best[0]:
                        best = (sc, a, b)
            if best:
                first[best[1]] += c
                second[best[2]] += c
            else:
                simple[st] += c
        tot = sum(stems.values()) or 1
        self.p_compound = sum(first.values()) / tot
        norm = lambda cnt: {k: (v + 0.5) / (sum(cnt.values()) + 0.5 * len(cnt)) for k, v in cnt.items()}
        self.first, self.second, self.simple, self.ends = norm(first), norm(second), norm(simple), norm(ends)
        self.idx = {}
        for part, table in (("F", self.first), ("S", self.second), ("X", self.simple), ("E", self.ends)):
            ix = defaultdict(dict)
            for w in table:
                for sp, p in (spell.expand(w).items() if w else [("", 1.0)]):
                    if p > 0.01:
                        ix[sp][w] = p
            self.idx[part] = ix
        self._cache = {}

    def match(self, pattern, top=20):
        """Names whose spelling fits a run of runes with lost runes ('.'): {spelled runes: P(name) · P(runes | name)}."""
        n = len(pattern)
        rx = lambda pat: re.compile(pat + "$")
        if not hasattr(self, "_by_len"):
            self._by_len = {part: defaultdict(list) for part in "FSXE"}
            for part in "FSXE":
                for sp in self.idx[part]:
                    self._by_len[part][len(sp)].append(sp)
        out = defaultdict(float)
        for j in range(2, n + 1):
            r_e = rx(pattern[j:])
            ends = [sp for sp in self._by_len["E"].get(n - j, []) if r_e.match(sp)]
            if not ends:
                continue
            qe = sum(self.ends[e] * pe for sp in ends for e, pe in self.idx["E"][sp].items())
            r_x = rx(pattern[:j])
            for sp in self._by_len["X"].get(j, []):
                if r_x.match(sp):
                    for x, px in self.idx["X"][sp].items():
                        for es in ends:
                            for e, pe in self.idx["E"][es].items():
                                out[sp + es] += (1 - self.p_compound) * self.simple[x] * px * self.ends[e] * pe
            for i in range(2, j - 1):
                r_f, r_s = rx(pattern[:i]), rx(pattern[i:j])
                fs = [sp for sp in self._by_len["F"].get(i, []) if r_f.match(sp)]
                if not fs:
                    continue
                ss = [sp for sp in self._by_len["S"].get(j - i, []) if r_s.match(sp)]
                for f_ in fs:
                    pf = sum(self.first[f] * p_ for f, p_ in self.idx["F"][f_].items())
                    for s_ in ss:
                        ps_ = sum(self.second[g] * p_ for g, p_ in self.idx["S"][s_].items())
                        for es in ends:
                            pe = sum(self.ends[e] * p_ for e, p_ in self.idx["E"][es].items())
                            out[f_ + s_ + es] += self.p_compound * pf * ps_ * pe
        return dict(sorted(out.items(), key=lambda kv: -kv[1])[:top])

    def candidates(self, s, top=5):
        """{normalized name: P(name) · P(runes | name)} for names composed of known parts that spell s."""
        if s in self._cache:
            return self._cache[s]
        out = defaultdict(float)
        F, S, X, E = self.idx["F"], self.idx["S"], self.idx["X"], self.idx["E"]
        n = len(s)
        for j in range(2, n + 1):  # the stem ends at j, the ending is s[j:]
            ends = E.get(s[j:])
            if not ends:
                continue
            for e, pe in ends.items():
                q = self.ends[e] * pe
                for x, px in X.get(s[:j], {}).items():
                    out[x + e] += (1 - self.p_compound) * self.simple[x] * px * q
                for i in range(2, j - 1):
                    fs, ss = F.get(s[:i]), S.get(s[i:j])
                    if fs and ss:
                        for f, pf in fs.items():
                            for g, pg in ss.items():
                                out[f + g + e] += self.p_compound * self.first[f] * pf * self.second[g] * pg * q
        res = dict(sorted(out.items(), key=lambda kv: -kv[1])[:top])
        self._cache[s] = res
        return res


class Ctx:
    """Where an inscription is read from: its path in the spelling tree (era, phase, epoch, area, region, carver),
    the choice table for that path and, after adaptation, the stone's own table."""
    def __init__(self, path, table, key):
        self.path, self.table, self.key = path, table, key
        self.epoch = path[2] if len(path) > 2 and path[2] in EPOCHS else None
        self.phase = path[1] if len(path) > 1 and path[1] in ("tidig", "sen") else None


VOWELS = set("aeiouyæøąåöä")


def rune_type(ch):
    """V for a vowel rune, C for a consonant, $ for the end of the word."""
    return "$" if ch == "$" else "V" if ch in VOWELS else "C"


class CVCharModel:
    """Runes inside words in two steps: first whether the next rune is a vowel, a consonant or the end of the word
    (from the pattern of vowels and consonants before it), then which rune of that kind (from the runes before it).
    The 16-rune alphabet has five vowel runes and about a dozen consonants, so knowing that a vowel comes narrows the
    choice to a few signs; the pattern of vowels and consonants is learned from far more words than any single run of
    runes."""
    def __init__(self, words, order=4):
        self.order = order
        self.tc, self.th = Counter(), Counter()   # type n-grams over the vowel/consonant pattern
        self.cc, self.ch = Counter(), Counter()   # rune n-grams within each type
        self.alpha = sorted({ch for w in words for ch in w} | {"$"})
        self.by_type = defaultdict(set)
        for ch in self.alpha:
            self.by_type[rune_type(ch)].add(ch)
        for w in words:
            s = "^" * order + w + "$"
            ts = "".join("^" if ch == "^" else rune_type(ch) for ch in s)
            for i in range(order, len(s)):
                for n in range(0, order + 1):  # type given the last n types
                    self.tc[(ts[i - n:i], ts[i])] += 1
                    self.th[ts[i - n:i]] += 1
                for n in range(0, 3):  # rune given its type and the last n runes
                    self.cc[(s[i - n:i], ts[i], s[i])] += 1
                    self.ch[(s[i - n:i], ts[i])] += 1

    def _p_type(self, ts, t):
        p = 1.0 / 3
        for n in range(0, self.order + 1):  # interpolated, longer patterns where they have been seen
            h = ts[len(ts) - n:] if n else ""
            c = self.th[h]
            if c:
                lam = c / (c + 3.0)
                p = lam * self.tc[(h, t)] / c + (1 - lam) * p
        return p

    def _p_in(self, s, t, ch):
        p = 1.0 / max(1, len(self.by_type[t]))
        for n in range(0, 3):
            h = s[len(s) - n:] if n else ""
            c = self.ch[(h, t)]
            if c:
                lam = c / (c + 2.0)
                p = lam * self.cc[(h, t, ch)] / c + (1 - lam) * p
        return p

    def step(self, prefix, ch):
        """log P(next rune | the runes so far)."""
        s = "^" * self.order + prefix
        ts = "".join("^" if c == "^" else rune_type(c) for c in s)
        t = rune_type(ch)
        return math.log(max(self._p_type(ts, t) * self._p_in(s, t, ch), 1e-12))

    def logp(self, w):
        return sum(self.step(w[:i], ch) for i, ch in enumerate(w + "$"))

    def fills(self, left, k, right="", beam=30):
        """The most probable runs of k runes between `left` and `right` within a word (a beam over the runes)."""
        states = [("", 0.0)]
        for _ in range(k):
            nxt = []
            for f, lp in states:
                for ch in self.alpha:
                    if ch != "$":
                        nxt.append((f + ch, lp + self.step(left + f, ch)))
            states = sorted(nxt, key=lambda x: -x[1])[:beam]
        out = []
        for f, lp in states:  # the runes after the gap must also fit
            w = left + f
            for i, ch in enumerate(right):
                lp += self.step(w + right[:i], ch)
            out.append((f, lp))
        return sorted(out, key=lambda x: -x[1])



def name_pairs(r):
    """The names of an inscription with their carved spellings: [(normalized name, runes without doubled letters)],
    from sections where the carved and the normalized words can be paired one to one."""
    out = []
    T = dict(sections(r.get("transliteration")))
    for lab, n_ in sections(r.get("normalization")):
        if lab not in T:
            continue
        raw = [w for w in re.split(r"[\s,.;:!?]+", re.sub(r"(\S+)/\S+", r"\1", n_)) if re.search(r"\w", w)]
        carved = translit_words(T[lab])
        if len(raw) == len(carved):
            pairs = list(zip(raw, carved))
        else:  # a damaged text: the words that clearly line up (align), so that one lost word does not lose the rest
            plain = [w.strip('"[]').replace("[", "").replace("]", "") for w in raw]
            pairs, at = [], 0
            for cw, nw in align(carved, plain):
                j = next((k for k in range(at, len(plain)) if plain[k] == nw), None)
                if j is not None:
                    pairs.append((raw[j], cw)); at = j + 1
        for nw, cw in pairs:
            ck = runekey(cw)
            if nw.startswith('"') and is_runes(ck.lower()):
                nm = normtok(nw.strip('"[]').replace("[", "").replace("]", "").replace("(?)", ""))
                out.append((nm, re.sub(r"(.)\1+", r"\1", ck)))
    return out


def name_sites(recs):
    """Where each name stands: [(signum, lat, lon, normalized name, carved spelling)] for located inscriptions."""
    return [(r["signum"], float(r["lat"]), float(r["lon"]), nm, ck) for r in recs
            if r.get("lat") is not None and r.get("lon") is not None for nm, ck in name_pairs(r)]

class Model:
    def __init__(self, recs, edda_tokens=(), lam_edda=0.03, lam_unk=0.01, D=0.75, d=None, kappa=2.0, exclude=(),
                 aligned=False, contexts=False, alpha=20.0, kappa_e=5.0, lm_beta=0.0, spelling_recs=(), lam_name=0.0,
                 cv_chars=False, lam_doc=0.0, area_lm=False, area_beta=200.0):
        """recs: Viking-Age inscriptions for the language and spelling. aligned: also use sections whose word counts
        differ (step 2). contexts: spelling by era, epoch, area, region and carver, and word sequences by epoch (step 3);
        alpha is how many observations a level needs to outweigh the level above it. spelling_recs: further inscriptions
        (e.g. medieval) used only for the spelling."""
        recs = [r for r in recs if r["signum"] not in set(exclude)]
        self.aligned, self.contexts, self.alpha, self.kappa, self.kappa_e = aligned, contexts, alpha, kappa, kappa_e
        self.lm_beta = lm_beta  # how many occurrences of a word an epoch needs before its own word sequences get half the weight
        tpr = [(runekey(a), normtok(b), r) for r in list(recs) + list(spelling_recs) for a, b in pairs(r, aligned)
               if is_runes(runekey(a).lower())]
        tp = [(a, b) for a, b, _ in tpr]
        self.spell = Spelling(tp)
        self.emp = defaultdict(Counter)
        viking_set = {id(r) for r in recs}
        for a, b, r in tpr:
            if id(r) in viking_set:
                self.emp[b][re.sub(r"(.)\1+", r"\1", a)] += 1
        self.n_pairs, self.n_pair_inscriptions = len(tp), len({id(r) for _, _, r in tpr})
        # the same word in different normalizations, learned from the data: forms that carvers spelled alike (each
        # at least twice) and that differ by at most two sounds are one word (ræisti = ræisþi, þennsi = þannsi)
        by_spell = defaultdict(Counter)
        for a, b, r in tpr:
            if id(r) in viking_set:
                by_spell[re.sub(r"(.)\1+", r"\1", a)][b] += 1
        parent = {}

        def root(x):
            while parent.get(x, x) != x:
                parent[x] = parent.get(parent[x], parent[x])
                x = parent[x]
            return x
        for sp, ws in by_spell.items():
            common = [w for w, c in ws.items() if c >= 2 and len(w) >= 3]
            for i_, w1 in enumerate(common):
                for w2 in common[i_ + 1:]:
                    k1, k2 = key(w1), key(w2)
                    if k1 != k2 and _lev(k1, k2) <= 2 and k1[:1] == k2[:1]:
                        r1, r2 = root(w1), root(w2)
                        if r1 != r2:
                            parent[max(r1, r2)] = min(r1, r2)
        self.lemma_of = {w: root(w) for w in parent}
        self.node, self.emp_ep = defaultdict(lambda: defaultdict(Counter)), defaultdict(lambda: defaultdict(Counter))
        self._tables, self._deriv, self._cand = {}, {}, {}
        if contexts:
            ctxs = {id(r): context(r) for r in list(recs) + list(spelling_recs)}
            for a, b, r in tpr:
                path = ctxs[id(r)]
                cnt = self.spell.expected_counts(b, a)
                for k in range(1, len(path) + 1):
                    if path[k - 1] is None:
                        break
                    node = self.node[path[:k]]
                    for (u, c), x in cnt.items():
                        node[u][c] += x
                self.emp_ep[path[:3]][b][re.sub(r"(.)\1+", r"\1", a)] += 1
        # bigram counts within sections
        self.big, self.uni, self.hist = Counter(), Counter(), Counter()
        self.big3, self.hist2, self.fol3 = Counter(), Counter(), Counter()  # three-word sequences (formulas)
        for r in recs:
            for _, p in sections(r.get("normalization")):
                ws = ["<s>"] + [normtok(w) for w in norm_words(p)]
                for a, b in zip(ws, ws[1:]):
                    self.big[(a, b)] += 1
                    self.hist[a] += 1
                self.uni.update(ws[1:])
                ws3 = ["<s>"] + ws
                for a, b, c in zip(ws3, ws3[1:], ws3[2:]):
                    if not self.big3[(a, b, c)]:
                        self.fol3[(a, b)] += 1
                    self.big3[(a, b, c)] += 1
                    self.hist2[(a, b)] += 1
        self.follow = defaultdict(set)
        cont = Counter()
        for (a, b) in self.big:
            self.follow[a].add(b)
            cont[b] += 1
        nb = len(self.big)
        self.pc = {w: c / nb for w, c in cont.items()}
        self.D = D
        self.gamma = {a: D * len(self.follow[a]) / self.hist[a] for a in self.hist}
        # word sequences by epoch, backing off to the whole Viking Age (step 3)
        self.big_e, self.hist_e, self.gamma_e = defaultdict(Counter), defaultdict(Counter), {}
        self.epoch_prior = Counter()
        if contexts:
            for r in recs:
                ep = epoch(r)
                if ep not in EPOCHS:
                    continue
                self.epoch_prior[ep] += 1
                for _, p in sections(r.get("normalization")):
                    ws = ["<s>"] + [normtok(w) for w in norm_words(p)]
                    for a, b in zip(ws, ws[1:]):
                        for lev in (ep, PHASE[ep]):  # the epoch and its phase
                            self.big_e[lev][(a, b)] += 1
                            self.hist_e[lev][a] += 1
        if area_lm:  # word sequences by area (formula habits differ between landscapes), backing off to the whole
            for r in recs:
                ar = "A:" + context(r)[3]
                for _, p in sections(r.get("normalization")):
                    ws = ["<s>"] + [normtok(w) for w in norm_words(p)]
                    for a, b in zip(ws, ws[1:]):
                        self.big_e[ar][(a, b)] += 1
                        self.hist_e[ar][a] += 1
        self.area_beta = area_beta
        if contexts or area_lm:
            for ep, big in self.big_e.items():
                fol = Counter(a for a, _ in big)
                self.gamma_e[ep] = {a: D * fol[a] / self.hist_e[ep][a] for a in self.hist_e[ep]}
        ec = Counter(normtok(w) for w in edda_tokens)
        ne = sum(ec.values()) or 1
        self.pe = {w: c / ne for w, c in ec.items()}
        self.lam_edda, self.lam_unk = lam_edda, lam_unk
        self.char = (CVCharModel if cv_chars else CharModel)([a for a, _ in tp])
        self.cvchar = None  # built on demand, to propose fillings rune by rune
        self._train_words = [a for a, _ in tp]
        # the text as a whole: which words stand in the same inscription (a word's company), lam_doc > 0
        self.lam_doc, self.cooc, self.cooc_tot, self._doc_cache = lam_doc, defaultdict(Counter), Counter(), {}
        if lam_doc:
            for r in recs:
                ws = {normtok(w) for _, p in sections(r.get("normalization")) for w in norm_words(p)}
                for v in ws:
                    for w in ws:
                        if v != w:
                            self.cooc[v][w] += 1
                            self.cooc_tot[v] += 1
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
        self.rule_z = {}  # the share of a word's spellings the beam keeps; context spellings are scaled the same way
        vocab = sorted(set(self.uni) | set(self.pe))  # a fixed order, so that runs are reproducible
        for w in vocab:
            if not re.fullmatch(r"[a-zþðæøåöäąǫœáéíóúýęR]+", w):
                continue
            n = sum(self.emp[w].values())
            rule, self.rule_z[w] = self.spell.expand(w, edda=(w not in self.uni), mass=True)
            ps = {s: (kappa / (n + kappa)) * p for s, p in rule.items()}
            for s, c in self.emp[w].items():
                ps[s] = ps.get(s, 0) + c / (n + kappa)
            for s, p in ps.items():
                if p > 1e-4:
                    self.index[s][w] = p
        self.maxlen = max(len(s) for s in self.index)
        self.keys_by_len = defaultdict(list)
        for k_ in self.index:
            self.keys_by_len[len(k_)].append(k_)
        # names the vocabulary has never seen (lam_name > 0): composed of name elements; how likely a name is after a
        # given word is learned from where names stand in the training texts
        self.lam_name, self.names = lam_name, None
        # where each name stands: (lat, lon, normalized name, carved spelling), for names on nearby stones
        self.name_sites = []
        # names on each carver's stones: (carver, normalized name, carved spelling), for the carver's circle
        self.name_carver = []
        for r in recs:
            located = r.get("lat") is not None and r.get("lon") is not None
            carvers = [c["name"] for c in (r.get("carvers") or []) if isinstance(c, dict) and not c.get("uncertain")]
            if not located and not carvers:
                continue
            for nm, ck in name_pairs(r):
                if located:
                    self.name_sites.append((float(r["lat"]), float(r["lon"]), nm, ck))
                self.name_carver.extend((cv, nm, ck) for cv in carvers)
        if lam_name:
            nm, after, after_all = Counter(), Counter(), Counter()
            for r in recs:
                for _, p in sections(r.get("normalization")):
                    toks = re.findall(r'("?)([^\s,.;:!?/()\[\]"]+)', re.sub(r"<([^>]*)>", r"\1", p))
                    prev = "<s>"
                    for q, w in toks:
                        if not re.search(r"\w", w):
                            continue
                        w = normtok(w)
                        after_all[prev] += 1
                        if q:
                            nm[w] += 1
                            after[prev] += 1
                        prev = w
            self.names = NameModel(nm, self.spell)
            self.name_f0 = sum(after.values()) / max(1, sum(after_all.values()))
            self.name_after = {w: (after[w] + 5 * self.name_f0) / (after_all[w] + 5) for w in after_all}

    def p_doc(self, doc):
        """P(w | the other words of the inscription): how often w stands in the same inscription as those words."""
        key_ = frozenset(doc)
        if key_ not in self._doc_cache:
            tot = sum(self.cooc_tot[v] for v in key_)
            out = Counter()
            for v in key_:
                for w, c in self.cooc[v].items():
                    out[w] += c
            self._doc_cache[key_] = {w: c / tot for w, c in out.items()} if tot else {}
        return self._doc_cache[key_]

    def names_near(self, lat, lon, km=20.0, sites=None):
        """Names on stones within km of a place: {normalized name: weight}, {carved spelling}; nearer weighs more.
        sites: other (lat, lon, name, spelling) to look among instead of the stones the model learned from."""
        out, spell = defaultdict(float), set()
        for la, lo, nm, ck in (self.name_sites if sites is None else sites):
            d = 6371.0 * math.acos(max(-1.0, min(1.0, math.sin(math.radians(lat)) * math.sin(math.radians(la)) +
                                   math.cos(math.radians(lat)) * math.cos(math.radians(la)) * math.cos(math.radians(lo - lon)))))
            if d <= km:
                out[nm] += 1.0 / (1.0 + d / 5.0)
                spell.add(ck)
        tot = sum(out.values())
        return ({k: v / tot for k, v in out.items()} if tot else {}), spell

    def names_by_carver(self, carver):
        """Names on the stones of a carver (signed or attributed in Rundata), the carver's own signature included:
        {normalized name: share}, {carved spelling}. The same families often turned to the same carver."""
        out, spell = Counter(), set()
        for cv, nm, ck in self.name_carver:
            if cv == carver:
                out[nm] += 1
                spell.add(ck)
        tot = sum(out.values())
        return ({k: v / tot for k, v in out.items()} if tot else {}), spell

    def lemma(self, w):
        """The word behind a normalized form (forms the data shows to be the same word share one key)."""
        return key(self.lemma_of.get(w.lstrip("§"), w.lstrip("§"))) if w != "<unk>" else w

    def p_word3(self, w, u, v):
        """P(w | u v) for three-word sequences, backing off to P(w | v)."""
        p2 = self.p_word(w, v)
        h = self.hist2.get((u, v), 0)
        if not h:
            return p2
        lr = 1 - self.lam_edda - self.lam_unk
        gam = self.D * self.fol3[(u, v)] / h
        return lr * max(self.big3.get((u, v, w), 0) - self.D, 0) / h + gam * p2

    def p_word(self, w, prev, ep=None, doc=None, cache=None, area=None):
        """P(w | prev) for a lexicon word (the unknown word is handled separately); with an epoch, the epoch's own
        word sequences back off to those of its phase, and those to the whole Viking Age."""
        lr = 1 - self.lam_edda - self.lam_unk
        pc = self.pc.get(w, 0.0)
        if prev in self.hist:
            pk = max(self.big.get((prev, w), 0) - self.D, 0) / self.hist[prev] + self.gamma[prev] * pc
        else:
            pk = pc
        if getattr(self, "use_epoch_lm", True) and ep:
            for lev in (PHASE.get(ep), ep):
                if lev in self.hist_e and prev in self.hist_e[lev]:
                    h = self.hist_e[lev][prev]
                    pe = max(self.big_e[lev].get((prev, w), 0) - self.D, 0) / h + self.gamma_e[lev][prev] * pk
                    lam = h / (h + self.lm_beta) if self.lm_beta else 1.0
                    pk = lam * pe + (1 - lam) * pk
        lev = "A:" + area if area else None
        if lev and lev in self.hist_e and prev in self.hist_e[lev]:  # the area's own formulas
            h = self.hist_e[lev][prev]
            pa = max(self.big_e[lev].get((prev, w), 0) - self.D, 0) / h + self.gamma_e[lev][prev] * pk
            lam = h / (h + self.area_beta)
            pk = lam * pa + (1 - lam) * pk
        p = lr * pk + self.lam_edda * self.pe.get(w, 0.0)
        if doc and self.lam_doc:
            p = (1 - self.lam_doc) * p + self.lam_doc * lr * self.p_doc(doc).get(w, 0.0)
        if cache:  # (weight, {word: share}) – words read elsewhere in the same inscription
            lam_c, shares = cache
            p = (1 - lam_c) * p + lam_c * lr * shares.get(w, 0.0)
        return p

    # ---- step 3: spelling by context ----
    def table(self, path):
        """Choice probabilities for a path in the spelling tree: each level is pulled towards the level above it
        (Dirichlet shrinkage with strength alpha), so a level with little data stays close to its parent."""
        path = tuple(path)
        if path in self._tables:
            return self._tables[path]
        t = self.spell.p if not path else self.table(path[:-1])
        cnt = self.node.get(path) if path else None
        if cnt and path[-1] is not None:
            t = {u: {c: (cnt[u][c] + self.alpha * q) / (sum(cnt[u].values()) + self.alpha) for c, q in cs.items()}
                 if u in cnt else cs for u, cs in t.items()}
        self._tables[path] = t
        return t

    def ctx(self, path):
        path = tuple(path)
        while path and path[-1] is None:
            path = path[:-1]
        return Ctx(path, self.table(path), path)

    def adapt(self, ctx, counts, beta=10.0):
        """The stone's own spelling: expected rule choices from a first reading, pulled towards the context table."""
        t = {u: {c: (counts.get((u, c), 0.0) + beta * q) / (sum(x for (uu, _), x in counts.items() if uu == u) + beta)
                 for c, q in cs.items()} for u, cs in ctx.table.items()}
        return Ctx(ctx.path, t, ctx.key + (("stone", id(t)),))

    def derivations(self, w, s):
        k = (w, s)
        if k not in self._deriv:
            self._deriv[k] = [path for _, path in self.spell._derivations(w, s, edda=(w not in self.uni))]
        return self._deriv[k]

    def rule_prob(self, w, s, table):
        edda = w not in self.uni
        us = units(w)
        tot = 0.0
        for path in self.derivations(w, s):
            p = 1.0
            for u, c, k in path:
                p *= choice_table(table, us, k, edda).get(c, 0.0)
            tot += p
        return tot

    def candidates(self, s, ctx=None):
        if ctx is None:
            out = dict(self.index.get(s, {}))
        else:
            ck = (s, ctx.key)
            if ck in self._cand:
                out = dict(self._cand[ck])
                out["<unk>"] = math.exp(self.char.logp(s))
                return self._with_names(s, out)
            if len(self._cand) > 400000:  # keep the cache bounded
                self._cand.clear()
            out = {}
            emp_ep = self.emp_ep.get(ctx.path[:3], {})
            for w in self.index.get(s, {}):
                n = sum(self.emp[w].values())
                rule = self.rule_prob(w, s, ctx.table) / self.rule_z.get(w, 1.0)
                pg = (self.emp[w].get(s, 0) + self.kappa * rule) / (n + self.kappa)
                m = emp_ep.get(w)
                p = (m.get(s, 0) + self.kappa_e * pg) / (sum(m.values()) + self.kappa_e) if m else pg
                if p > 1e-6:
                    out[w] = p
            self._cand[ck] = dict(out)
        out["<unk>"] = math.exp(self.char.logp(s))
        return self._with_names(s, out)

    def _with_names(self, s, out):
        """Add names composed of name elements (marked §) that the vocabulary does not have."""
        if self.names is not None and len(s) >= 3:
            for w, p in self.names.candidates(s).items():
                if w not in out:
                    out["§" + w] = p
        return out

    def p_name(self, prev):
        """P(a name the vocabulary does not know | previous word)."""
        return self.lam_name * self.name_after.get(prev, self.name_f0) / self.name_f0


def key(w):
    """The same word in another normalization: Old Danish, Old Swedish and Icelandic spellings brought together
    (stæinn = sten = steinn, sin = sinn, þøsi = þausi, faður = faþur), but different words kept apart."""
    if w == "<unk>":
        return w
    w = unicodedata.normalize("NFD", w.lstrip("§").lower())
    w = "".join(ch for ch in w if unicodedata.category(ch) != "Mn")
    for a, b in (("ð", "þ"), ("w", "v"), ("ǫ", "o"), ("ø", "o"), ("œ", "o"), ("æi", "e"), ("ei", "e"), ("ai", "e"),
                 ("au", "o"), ("ey", "o"), ("oy", "o"), ("æ", "e"), ("y", "u"), ("pt", "ft")):
        w = w.replace(a, b)
    return re.sub(r"(.)\1+", r"\1", w)


def _lse(xs):
    m = max(xs)
    return m + math.log(sum(math.exp(x - m) for x in xs)) if m > float("-inf") else m


def posteriors(model, groups, signs=(), lexicon=True, ctx=None, doc=None, cache=None, area=None):
    """Forward–backward over the carved text. `groups` are the carver's groups (a divider between each);
    `signs` are indices of groups followed by a non-runic sign or the futhark row (a boundary at no cost).
    Returns (log P(text), span posteriors {(i, j, w): p}, text)."""
    text = "".join(groups)
    L = len(text)
    div, free, pos = set(), set(), 0
    for gi, g in enumerate(groups[:-1]):
        pos += len(g)
        (free if gi in signs else div).add(pos)
    d = model.d
    lbf = lambda i: 0.0 if (i == 0 or i in free) else math.log(d if i in div else 1 - d)
    ep = ctx.epoch if ctx is not None else None

    starts = defaultdict(list)  # start → [(end, word, log P(runes | word))]
    for i in range(L):
        for j in range(i + 1, min(L, i + model.maxlen) + 1):
            if any(b in div or b in free for b in range(i + 1, j)):
                break
            for w, ps in model.candidates(text[i:j], ctx).items():
                if ps > 0 and (lexicon or w == "<unk>"):
                    starts[i].append((j, w, math.log(ps)))
    ltrans = {}

    def lt(w, prev):
        k = (w, prev)
        if k not in ltrans:
            p = model.lam_unk if w == "<unk>" else model.p_name(prev) if w[0] == "§" else model.p_word(w, prev, ep, doc, cache, area)
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
    return logZ, post, text


def best_path(post, L, keyfn=None):
    """The path with the highest expected number of correctly read runes (posterior × length); the same word in
    several normalizations counts as one reading of the span (keyfn: e.g. Model.lemma; default key)."""
    keyfn = keyfn or key
    grp = defaultdict(float)
    top = {}
    for (i, j, w), p in post.items():
        k = (i, j, keyfn(w))
        grp[k] += p
        if k not in top or p > post[(i, j, top[k])]:
            top[k] = w
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
    return path[::-1]


def decode(model, groups, signs=(), lexicon=True, ctx=None):
    """Returns (log P(text), best path [(start, end, word, posterior)], span posteriors {(i, j, w): p}, text)."""
    logZ, post, text = posteriors(model, groups, signs, lexicon, ctx)
    return logZ, best_path(post, len(text), getattr(model, "lemma", None)), post, text


def adapt_counts(model, post, text, ctx, floor=0.05):
    """Expected rule choices in a reading: each word's derivations weighted by its posterior."""
    out = Counter()
    for (i, j, w), p in post.items():
        if w == "<unk>" or p < floor:
            continue
        exp = [(math.prod(choice_table(ctx.table, units(w), k, w not in model.uni).get(c, 0.0) for u, c, k in path), path)
               for path in model.derivations(w, text[i:j])]
        tot = sum(x for x, _ in exp)
        if tot <= 0:
            continue
        for x, path in exp:
            for u, c, _ in path:
                out[(u, c)] += p * x / tot
    return out


def decode_epochs(model, groups, signs=(), path=None, adapt=0.0, prior=None):
    """Read with each epoch in turn and weigh the readings by how probable the text is in each epoch: the model
    dates the text from its spelling and language. path is (era, phase, epoch, area, region, carver); its phase and
    epoch are ignored.
    Returns (log P(text), best path, mixed posteriors, text, {epoch: P(epoch | text)}, {epoch: log P(text | epoch)})."""
    path = tuple(path or ("V",))
    prior = prior or {e: (model.epoch_prior[e] or 1) for e in EPOCHS}
    zp = sum(prior.values())
    runs, ll = {}, {}
    for e in EPOCHS:
        c = model.ctx((path[0], PHASE[e], e) + path[3:])
        logZ, post, text = posteriors(model, groups, signs, ctx=c)
        if adapt:
            c = model.adapt(c, adapt_counts(model, post, text, c), adapt)
            logZ, post, text = posteriors(model, groups, signs, ctx=c)
        ll[e] = logZ
        runs[e] = (logZ + math.log(prior[e] / zp), post)
    m = max(v for v, _ in runs.values())
    tot = sum(math.exp(v - m) for v, _ in runs.values())
    ep_post = {e: math.exp(v - m) / tot for e, (v, _) in runs.items()}
    mix = defaultdict(float)
    for e, (_, post) in runs.items():
        for k, p in post.items():
            mix[k] += ep_post[e] * p
    return m + math.log(tot), best_path(mix, len(text)), dict(mix), text, ep_post, ll


def epoch_posterior(ll, prior=None, temperature=1.0):
    """P(epoch | text) from log P(text | epoch), with the epochs' prior (None: equal priors), softened by a temperature
    fitted on the dating test (scripts/runlm_dating.py), so that a stated certainty matches how often it is right."""
    v = {e: (ll[e] + (math.log(prior[e] / sum(prior.values())) if prior else 0.0)) / temperature for e in EPOCHS}
    mx = max(v.values())
    z = sum(math.exp(x - mx) for x in v.values())
    return {e: math.exp(x - mx) / z for e, x in v.items()}


def fit_temperature(rows, use_prior=True):
    """The temperature that minimises the log loss of the dating on held-out inscriptions (rows from
    scripts/runlm_dating.py: {'true', 'll', 'prior'})."""
    def loss(t):
        return -sum(math.log(max(epoch_posterior(x["ll"], x["prior"] if use_prior else None, t)[x["true"]], 1e-12))
                    for x in rows) / len(rows)
    grid = [1.0 * 1.15 ** k for k in range(0, 40)]
    return min(grid, key=loss)


# ---- filling lost runes ---------------------------------------------------------------------------------------------
FILL_ALPHABET = "fuþorkhniastbmlRe"


def trigram_delta(model, path):
    """How much more (log) probable the words of a reading are when each is judged by the two words before it."""
    ws = ["<s>", "<s>"] + [w for _, _, w, _ in path]
    out = 0.0
    for u, v, w in zip(ws, ws[1:], ws[2:]):
        if w == "<unk>" or w[0] == "§" or v == "<unk>" or v[0] == "§":
            continue
        p2, p3 = model.p_word(w, v), model.p_word3(w, u, v)
        if p2 > 0 and p3 > 0:
            out += math.log(p3 / p2)
    return out


def restore(model, groups, gap, signs=(), ctx=None, window=2, n_cands=60, use_doc=False, char_fills=0,
            context_cands=False, name_cands=0, adapt=0.0, trigram=False, cache=0.0, area=None, by_word=False,
            words=None, site=None, near_km=20.0, lam_near=0.0, near_sites=None, allowed=None, carver=None, lam_carver=0.0,
            trace_eps=0.0, segments=None, hard=None):
    """Fill a run of lost runes. groups are the carved groups (dividers between them) with every lost rune written '?';
    gap is (group index, first position, last position + 1) of the run to fill. Candidate fillings come from the words
    whose spelling fits the preserved runes around the gap (and, for gaps of one or two runes, every combination of
    runes); each candidate is scored by how probable the whole text then is (within `window` groups on each side, or
    the whole text if window is None). use_doc: the words read in the rest of the inscription also count (which words
    stand together). char_fills: that many fillings proposed rune by rune by the vowel/consonant model, for words the
    vocabulary does not have. context_cands: candidate words are weighed by how well they fit the words read before and
    after the gap. name_cands: that many names composed of name elements that fit the preserved runes. adapt: the
    stone's own spelling, learned from the rest of its text, is used (strength of the general spelling). trigram:
    each candidate is also judged by three-word sequences (formulas) along its reading. cache: words already read
    elsewhere in the inscription become candidates and more probable (weight). by_word: the fillings are ranked
    by the word they give (its probability summed over its spellings), then by spelling – when a whole word is lost
    its spelling cannot be known, but the word can. words: a dict that receives the word each filling gives.
    site, near_km, lam_near: (lat, lon) of the stone; names on stones within near_km become candidates (in the
    spellings their carvers used) and more probable (weight lam_near) – families raised stones near each other.
    near_sites: the stones to take those names from (name_sites), instead of the stones the model learned from – a
    stone's companion may by chance be in the same held-out part, and its carved names are no leak about this stone.
    carver, lam_carver: the carver of the stone; names on the carver's other stones (and the carver's own name)
    become candidates and more probable (weight lam_carver). The carver's spelling comes with ctx (Model(contexts=True),
    a path ending in the carver).
    allowed: for each lost rune the runes its visible remains allow (a set, or None when nothing is visible), e.g.
    from a 3D scan or a photograph (data/rune_traces.json for what part of a rune leaves which runes possible); only
    fillings that agree are considered, and when few combinations agree all of them are tried. trace_eps > 0 makes the
    traces soft: a filling that disagrees with a trace is still tried, but each rune that disagrees multiplies its
    probability by trace_eps – a misread trace then costs less. hard: the positions in the gap whose rune is known
    for certain (a preserved rune inside two runs filled as one); they hold even when the traces are soft. segments: a dict that receives, for each filling, the
    words over the gap [(from, to, word)] with positions counted from the gap's start – a gap that spans two words (two
    runs filled as one, merge_runs) has a word for each part; `words` has only the word where the gap starts.
    Returns [(filling, probability)], best first, over the candidates considered."""
    gi, g0, g1 = gap
    k = g1 - g0
    g = groups[gi]
    sets = [set(allowed[i]) if (allowed and allowed[i]) else None for i in range(k)]
    ok = lambda f: all(s_ is None or ch in s_ for s_, ch in zip(sets, f))
    soft = bool(allowed) and trace_eps > 0
    fixed = set(hard or ())
    ok_hard = lambda f: all(sets[i] is None or f[i] in sets[i] for i in fixed if i < len(f))  # noqa: E731
    misfit = lambda f: sum(1 for i, (s_, ch) in enumerate(zip(sets, f)) if s_ is not None and ch not in s_ and i not in fixed)
    # a first reading of the rest of the text (the gap left open): its words give the context
    parts0, sg0 = [], []
    for idx, grp in enumerate(groups):
        pieces = [p_ for p_ in grp.split("?") if p_]
        for q, p_ in enumerate(pieces):
            parts0.append(p_)
            if q < len(pieces) - 1 or idx in signs or (idx == gi and q == len(pieces) - 1 and "?" in grp):
                sg0.append(len(parts0) - 1)
    reading0 = decode(model, parts0, sg0, ctx=ctx) if (parts0 and (use_doc or context_cands or adapt or cache)) else None
    cache_arg, cached_runes = None, set()
    if cache and reading0:
        seen = Counter(w for _, _, w, p_ in reading0[1] if p_ >= 0.3 and w != "<unk>")
        if seen:
            tot = sum(seen.values())
            cache_arg = (cache, {w.lstrip("§"): c / tot for w, c in seen.items()})
            cached_runes = {reading0[3][i_:j_] for i_, j_, w, p_ in reading0[1] if p_ >= 0.3 and w != "<unk>"}
    prev_w = next_w = None
    if reading0 and context_cands:
        # the gap's position in the text without lost runes: everything before it in the groups, minus earlier gaps
        before = sum(len(x.replace("?", "")) for x in groups[:gi]) + len(g[:g0].replace("?", ""))
        for i_, j_, w_, p_ in reading0[1]:
            if j_ <= before and p_ >= 0.3:
                prev_w = w_
            if i_ >= before and next_w is None and p_ >= 0.3:
                next_w = w_
    near_shares, near_spell = ({}, set())
    if site and lam_near:
        near_shares, near_spell = model.names_near(site[0], site[1], near_km, sites=near_sites)
    car_shares, car_spell = model.names_by_carver(carver) if (carver and lam_carver) else ({}, set())
    near_spell = near_spell | car_spell
    if (near_shares or car_shares) and not cache_arg:  # names of the stone's neighbours and of its carver's circle
        lam = (lam_near if near_shares else 0.0) + (lam_carver if car_shares else 0.0)
        mixed = defaultdict(float)
        for shares, w_ in ((near_shares, lam_near), (car_shares, lam_carver)):
            for k_, v_ in shares.items():
                mixed[k_] += w_ * v_ / lam
        cache_arg = (lam, dict(mixed))
    pre = defaultdict(float)
    ntok = sum(model.uni.values()) or 1
    # windows inside the group that cover the gap; a candidate word is weighed by how common it is (or how well it
    # fits between the words before and after) and how well its spelling fits (other lost runes are wildcards)
    for a in range(max(0, g1 - model.maxlen), g0 + 1):
        for b in range(g1, min(len(g), a + model.maxlen) + 1):
            pat_s = "".join("." if ch == "?" else re.escape(ch) for ch in g[a:b])
            pat = re.compile(pat_s + "$")
            for key_ in model.keys_by_len.get(b - a, ()):
                if pat.match(key_):
                    f = key_[g0 - a:g1 - a]
                    if context_cands:
                        sc = max(p_ * model.p_word(w, prev_w if a == 0 else "<s>") *
                                 (model.p_word(next_w, w) if (next_w and b == len(g)) else 1.0)
                                 for w, p_ in model.index[key_].items())
                    else:
                        sc = max(p_ * (model.uni.get(w, 0) + 0.5) / ntok for w, p_ in model.index[key_].items())
                    pre[f] = max(pre[f], sc)
            for cr in near_spell:  # a name as it was carved on a nearby stone
                if len(cr) == b - a and pat.match(cr):
                    pre[cr[g0 - a:g1 - a]] = max(pre[cr[g0 - a:g1 - a]], 0.5)
            for cr in cached_runes:  # the same word written elsewhere on the stone
                if len(cr) == b - a and pat.match(cr):
                    pre[cr[g0 - a:g1 - a]] = max(pre[cr[g0 - a:g1 - a]], 1.0)
            if name_cands and model.names is not None and b - a >= 4:
                for sp, pn in model.names.match(pat_s.replace("\\", ""), top=name_cands).items():
                    f = sp[g0 - a:g1 - a]
                    pre[f] = max(pre[f], pn * model.lam_name)
    ranked = [f for f, _ in sorted(pre.items(), key=lambda kv: -kv[1])]
    cands = [f for f in ranked if ok(f)][:n_cands]
    if soft:  # the best candidates whatever the traces say, in case a trace is misread
        cands += [f for f in ranked[:n_cands] if f not in cands and ok_hard(f)]
    alpha = [sorted(s_) if s_ is not None else FILL_ALPHABET for s_ in sets]
    if k <= 2 or (allowed and math.prod(len(a_) for a_ in alpha) <= 400):
        # short gaps, or few combinations left by what is visible: every combination is tried as well
        cands += ["".join(f) for f in itertools.product(*alpha) if "".join(f) not in cands]
        if soft and k <= 2:
            cands += ["".join(f) for f in itertools.product(FILL_ALPHABET, repeat=k)
                      if "".join(f) not in cands and ok_hard("".join(f))]
        if soft and fixed:
            # runs filled as one (preserved runes fixed): every rune the traces leave out is also tried at the lost
            # positions, since the vocabulary does not propose fillings that span two words
            wide = [sorted(s_) if (s_ is not None and i in fixed) else FILL_ALPHABET for i, s_ in enumerate(sets)]
            if math.prod(len(a_) for a_ in wide) <= 400:
                cands += ["".join(f) for f in itertools.product(*wide) if "".join(f) not in cands]
    elif char_fills:  # longer gaps: runs of runes that fit the vowel/consonant pattern and the runes around the gap
        if model.cvchar is None:
            model.cvchar = CVCharModel(model._train_words)
        left, right = g[max(0, g0 - 4):g0].split("?")[-1], g[g1:g1 + 3].split("?")[0]
        fills = model.cvchar.fills(left, k, right)[:char_fills * (5 if allowed else 1)]
        cands += [f for f, _ in fills if f not in cands and (ok(f) or (soft and ok_hard(f)))][:char_fills * (2 if soft else 1)]
    if adapt and reading0:  # the stone's own spelling habits, from the rest of its text
        base = ctx or Ctx((), model.spell.p, ("glob",))
        ctx = model.adapt(base, adapt_counts(model, reading0[2], reading0[3], base), adapt)
    lo, hi = (0, len(groups)) if window is None else (max(0, gi - window), min(len(groups), gi + window + 1))
    doc = None
    if use_doc and reading0:  # the words of the rest of the text
        doc = {w for _, _, w, p_ in reading0[1] if p_ >= 0.5 and w != "<unk>" and w[0] != "§"}
    out, word_of, seg_of = {}, {}, {}
    gap_at = sum(len(x.replace("?", "")) for x in groups[lo:gi]) + len(g[:g0].replace("?", ""))
    for f in cands:
        filled = g[:g0] + f + g[g1:]
        win = groups[lo:gi] + [filled] + groups[gi + 1:hi]
        # other lost runes split their group (a boundary at no cost), so that only this gap is filled
        parts, sg = [], []
        for idx, grp in enumerate(win):
            pieces = [p_ for p_ in grp.split("?") if p_]
            for q, p_ in enumerate(pieces):
                parts.append(p_)
                if q < len(pieces) - 1 or (lo + idx) in signs:
                    sg.append(len(parts) - 1)
        if not parts:
            continue
        lz, post_, text_ = posteriors(model, parts, sg, ctx=ctx, doc=doc, cache=cache_arg, area=area)
        path_ = (best_path(post_, len(text_), model.lemma)
                 if (trigram or by_word or words is not None or segments is not None) else None)
        out[f] = lz + (trigram_delta(model, path_) if trigram else 0.0) + (misfit(f) * math.log(trace_eps) if soft else 0.0)
        if path_ is not None:
            word_of[f] = next((w for i_, j_, w, _ in path_ if i_ <= gap_at < j_), None)
            seg_of[f] = [(max(i_, gap_at) - gap_at, min(j_, gap_at + k) - gap_at, w)
                         for i_, j_, w, _ in path_ if i_ < gap_at + k and j_ > gap_at]
    if not out:
        return []
    mx = max(out.values())
    z = sum(math.exp(v - mx) for v in out.values())
    probs = {f: math.exp(v - mx) / z for f, v in out.items()}
    if words is not None:
        words.update(word_of)
    if segments is not None:
        segments.update(seg_of)
    if by_word:
        wl = lambda f: model.lemma(word_of[f]) if word_of.get(f) and word_of[f] != "<unk>" else ("<unk>", f)
        tot = defaultdict(float)
        for f, p_ in probs.items():
            tot[wl(f)] += p_
        return sorted(probs.items(), key=lambda kv: (-tot[wl(kv[0])], -kv[1]))
    return sorted(probs.items(), key=lambda kv: -kv[1])


def merge_runs(groups, runs, max_between=3):
    """Runs of lost runes ('?') close together in one group are filled as one: the preserved runes between them (at
    most max_between) are kept by constraining those places to themselves, so that the word is weighed as a whole.
    Filled one run at a time, each run takes the others' best filling as given and the word looks more certain than
    it is. Returns (the groups with each span all '?', the spans, {span: the constraint of each place, None where a
    rune is lost}, {run: its span})."""
    spans, member = [], {}
    for gp in sorted(runs):
        if spans and spans[-1][0] == gp[0] and gp[1] - spans[-1][2] <= max_between:
            spans[-1] = (gp[0], spans[-1][1], gp[2])
        else:
            spans.append(gp)
        member[gp] = len(spans) - 1
    work, cons = list(groups), {}
    for gi, a, e in spans:
        c = [None if groups[gi][i] == "?" else groups[gi][i] for i in range(a, e)]
        work[gi] = work[gi][:a] + "?" * (e - a) + work[gi][e:]
        if any(x is not None for x in c):
            cons[(gi, a, e)] = c
    return work, spans, cons, {gp: spans[i] for gp, i in member.items()}


def _fold(w):
    """A normalized word in plain letters, for comparing two normalizations of the same word."""
    w = unicodedata.normalize("NFD", (w or "").lower().lstrip("§").replace("[", "").replace("]", "").replace('"', ""))
    w = "".join(ch for ch in w if unicodedata.category(ch) != "Mn")
    w = w.translate(str.maketrans("ðdæøy", "þþaou")).replace("e", "i").replace("ia", "io")
    return re.sub(r"(.)\1+", r"\1", re.sub(r"[^a-zþ]", "", w))


def same_word(a, b):
    """Are two normalized forms the same word, allowing for another case form or another normalization of it
    (Guðmundr ~ GuðmundaR, Vigbiorn ~ Vigbiarn, stæinn ~ stæin)? For comparing a reading with Rundata's."""
    a, b = _fold(a), _fold(b)
    if not a or not b:
        return False
    n = min(len(a), len(b))
    if a == b or (n >= 4 and (a.startswith(b[:n - 1]) or b.startswith(a[:n - 1]))):
        return True
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.8


def _by_lemma(model, pairs):
    """{word: probability} from [(word, probability)], the forms of one word counted together (the most probable form
    – the first seen – stands for them), most probable first."""
    d, rep = defaultdict(float), {}
    for w_, p_ in pairs:
        lk = model.lemma(w_) if w_ != "<unk>" else ("<unk>", w_)
        d[lk] += p_
        rep.setdefault(lk, w_)
    out = defaultdict(float)
    for lk, p_ in d.items():
        out[rep[lk]] += p_
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def restore_all(model, groups, signs=(), ctx=None, top=5, rounds=2, only=None, area=None, allowed=None, details=None,
                positions=None, hard=None, **kw):
    """Fill several runs of lost runes in a text together. Each gap is first filled on its own, then again with the
    other gaps filled by their best candidates, for a couple of rounds; finally every combination of the best
    candidates of each gap is weighed by how probable the whole text is. only: the gaps to fill (others stay open).
    allowed: {gap: what is visible of each of its lost runes} (see restore). details: a dict that receives, for each
    gap index, its fillings [(filling, probability, word)] from the last round. positions: a dict that receives, for
    each gap index, the word at each of its positions [{word: probability}] – when two runs are filled as one
    (merge_runs) the gap can cover the end of one word and the start of the next, and each run has its own word.
    hard: {gap: positions whose rune is certain} (see restore), for soft traces.
    Returns ([(fillings per gap, probability among the combinations, reading)], best first, gaps,
    {gap index: {word: probability over all its candidates, the other gaps filled}})."""
    gaps = [(gi, m_.start(), m_.end()) for gi, g in enumerate(groups) for m_ in re.finditer(r"\?+", g)]
    if only is not None:
        gaps = [gp for gp in gaps if gp in set(only)]
    if not gaps:
        return [], gaps, {}
    top = top if len(gaps) <= 3 else 3 if len(gaps) <= 5 else 2

    def fill(gs, choice):
        gs = list(gs)
        for (gi, a, b), f in sorted(zip(gaps, choice), key=lambda x: (-x[0][0], -x[0][1])):
            gs[gi] = gs[gi][:a] + f + gs[gi][b:]
        return gs

    best = [None] * len(gaps)
    options = [[] for _ in gaps]
    wdist = {}
    for r_ in range(rounds if len(gaps) > 1 else 1):
        for n, gp in enumerate(gaps):
            choice = [best[i] if (best[i] is not None and i != n) else "?" * (gaps[i][2] - gaps[i][1]) for i in range(len(gaps))]
            wd, seg = {}, {}
            res = restore(model, fill(groups, choice), gp, signs=signs, ctx=ctx, area=area, words=wd, segments=seg,
                          allowed=(allowed or {}).get(gp), hard=(hard or {}).get(gp), **kw)
            if details is not None:
                details[n] = [(f, p_, wd.get(f)) for f, p_ in res[:12]]
            if res:
                options[n] = [f for f, _ in res[:top]]
                best[n] = res[0][0]
                # the word in this gap, over all its candidates (the other gaps filled by their best candidates)
                wdist[n] = _by_lemma(model, [(wd.get(f) or "<unk>", p_) for f, p_ in res])
                if positions is not None:
                    at = lambda f, o: next((w_ for a_, b_, w_ in seg.get(f, ()) if a_ <= o < b_), None) or "<unk>"  # noqa: E731
                    positions[n] = [_by_lemma(model, [(at(f, o), p_) for f, p_ in res]) for o in range(gp[2] - gp[1])]
    combos = list(itertools.product(*[o or ["?" * (b - a)] for o, (_, a, b) in zip(options, gaps)]))
    scored = []
    for choice in combos:
        gs = fill(groups, choice)
        parts, sg, offs = [], [], []
        for idx, grp in enumerate(gs):
            pieces = [p_ for p_ in grp.split("?") if p_]
            for q, p_ in enumerate(pieces):
                parts.append(p_)
                if q < len(pieces) - 1 or idx in signs:
                    sg.append(len(parts) - 1)
        lz, post_, text_ = posteriors(model, parts, sg, ctx=ctx, area=area)
        path_ = best_path(post_, len(text_), model.lemma)
        if kw.get("trigram"):
            lz += trigram_delta(model, path_)
        at = [sum(len(x.replace("?", "")) for x in gs[:gi]) + len(gs[gi][:a].replace("?", "")) for gi, a, _ in gaps]
        words = [next((w for i_, j_, w, _ in path_ if i_ <= t < j_), None) for t in at]
        scored.append((lz, choice, " ".join(w for _, _, w, _ in path_), words))
    mx = max(x[0] for x in scored)
    z = sum(math.exp(x[0] - mx) for x in scored)
    out = sorted(((c, math.exp(v - mx) / z, rd) for v, c, rd, _ in scored), key=lambda x: -x[1])
    return out, gaps, wdist
