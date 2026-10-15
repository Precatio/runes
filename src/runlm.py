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


class Model:
    def __init__(self, recs, edda_tokens=(), lam_edda=0.03, lam_unk=0.01, D=0.75, d=None, kappa=2.0, exclude=(),
                 aligned=False, contexts=False, alpha=20.0, kappa_e=5.0, lm_beta=0.0, spelling_recs=(), lam_name=0.0):
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
            for ep, big in self.big_e.items():
                fol = Counter(a for a, _ in big)
                self.gamma_e[ep] = {a: D * fol[a] / self.hist_e[ep][a] for a in self.hist_e[ep]}
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
        # names the vocabulary has never seen (lam_name > 0): composed of name elements; how likely a name is after a
        # given word is learned from where names stand in the training texts
        self.lam_name, self.names = lam_name, None
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

    def p_word(self, w, prev, ep=None):
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
        return lr * pk + self.lam_edda * self.pe.get(w, 0.0)

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


def posteriors(model, groups, signs=(), lexicon=True, ctx=None):
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
            p = model.lam_unk if w == "<unk>" else model.p_name(prev) if w[0] == "§" else model.p_word(w, prev, ep)
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


def best_path(post, L):
    """The path with the highest expected number of correctly read runes (posterior × length); the same word in
    several normalizations counts as one reading of the span."""
    grp = defaultdict(float)
    top = {}
    for (i, j, w), p in post.items():
        k = (i, j, key(w))
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
    return logZ, best_path(post, len(text)), post, text


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
