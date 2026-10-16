"""Från fornspråkliga ord till översättning: en ordlista som lärs ur Rundatas texter och deras engelska översättningar,
utan någon tryckt ordbok.

Varje vikingatida inskrift finns i Rundata både som normaliserad fornspråklig text och som engelsk översättning.
En översättningsmodell av det enklaste slaget (IBM-modell 1, Brown m.fl. 1993) lär sig, genom att räkna vilka ord
som återkommer tillsammans i samma inskrift och dess översättning, sannolikheten P(engelskt ord | fornspråkligt ord).
Den kräver ingen ordlista och ingen ordföljd, och den räknar med att varje engelskt ord kan sakna motsvarighet (ett
tomt ord). Namn som modellen inte har sett översätts med sig själva.

Används av scripts/runlm_gloss_test.py (prov på inskrifter som inte fanns i träningen) och för att ge en läsning från
src/runlm.py ett översättningsutkast."""
import math
import re
from collections import Counter, defaultdict

from src.runlm import normtok, norm_words, sections

NULL = "<null>"
# English words that carry grammar rather than meaning; left out when the glossary is compared with a translation
STOP = set("""a an the of in to and or for on at by with from as is was were be been his her its their them they he she it
him who which that this these those there here into upon after memory himself herself had has have did do not no""".split())
# Articles and prepositions a translation adds around a word; not used as the gloss of a word
FUNC = set("a an the of in to at on for by may".split())
# Swedish for the commonest English glosses, so that a reading can be given in Swedish (checked by hand)
SV = {"stone": "sten", "stones": "stenar", "raised": "reste", "raise": "resa", "had": "lät", "memory": "minne",
      "father": "fader", "mother": "moder", "brother": "broder", "brothers": "bröder", "son": "son", "sons": "söner",
      "daughter": "dotter", "wife": "hustru", "husband": "make", "husbandman": "husbonde", "god": "Gud", "help": "hjälpe",
      "soul": "själ", "spirit": "ande", "good": "god", "carved": "ristade", "cut": "högg", "runes": "runor",
      "bridge": "bro", "made": "gjorde", "monument": "minnesmärke", "died": "dog", "east": "österut", "west": "västerut",
      "england": "England", "greece": "Grekland", "killed": "dräpt", "fell": "föll", "this": "denna", "these": "dessa",
      "his": "sin", "her": "sin", "their": "sin", "and": "och", "in": "i", "of": "av", "who": "som", "was": "var",
      "were": "var", "ship": "skepp", "farm": "gård", "lived": "bodde", "owned": "ägde", "mary": "Maria",
      "christ": "Kristus", "dear": "kär", "valiant": "tapper", "partner": "kompanjon", "slab": "häll", "rock": "häll",
      "coloured": "färgade", "painted": "målade", "let": "lät", "stand": "stå", "stands": "står", "here": "här",
      "foster": "foster", "uncle": "farbror", "nephew": "brorson", "kinsman": "frände", "friend": "vän", "land": "land",
      "home": "hem", "journey": "resa", "travelled": "färdades", "abroad": "utomlands", "gold": "guld", "men": "män",
      "man": "man", "woman": "kvinna", "the": "", "a": "", "may": "", "lord": "herre", "memory": "minne",
      "in memory of": "efter", "sister": "syster", "grandfather": "farfar", "stepfather": "styvfar", "estate": "gods",
      "inheritance": "arv", "voyage": "färd", "sweden": "Sverige", "denmark": "Danmark", "norway": "Norge",
      "baptised": "döpt", "baptism": "dopkläder", "white": "vita", "clothes": "kläder", "path": "väg", "road": "väg",
      "steersman": "styrman", "chieftain": "hövding", "warrior": "krigare", "young": "ung", "best": "bäst",
      "sacred": "helig", "holy": "helig", "eternal": "evig", "light": "ljus", "paradise": "paradis",
      "he": "han", "she": "hon", "they": "de", "erected": "reste", "landmark": "minnesmärke", "placed": "satte",
      "owns": "äger", "himself": "själv", "very": "mycket", "stamp": "stav", "þegn": "tägn", "all": "alla",
      "mound": "hög", "it": "det", "deserved": "förtjänade", "into": "in i", "well": "väl", "from": "från",
      "both": "båda", "smith": "smed", "then": "då", "live": "leva", "sea": "hav", "marked": "märkte",
      "kinsman-by-marriage": "svåger", "jarl": "jarl", "drowned": "drunknade", "gave": "gav", "own": "egen",
      "sister's": "systers", "bridges": "broar", "lies": "ligger", "buried": "begravd", "church": "kyrka",
      "everlasting": "evig", "mercy": "nåd", "living": "levande", "stood": "stod", "sat": "satt", "travelled": "färdades",
      "interpret": "tyda", "secure": "säkra", "rich": "rik", "fine": "fin", "brave": "modig", "generous": "givmild"}
# a verb in the infinitive (ræisa, haggva, gæra …) after 'lät' is glossed by the translations' past participle
INF = {"raised": "resa", "erected": "resa", "cut": "hugga", "made": "göra", "carved": "rista", "placed": "sätta",
       "coloured": "färga", "painted": "måla"}


def _english(s):
    s = re.sub(r"\(\?\)|\[|\]|\(|\)|<[^>]*>", " ", s or "")
    return [w for w in re.findall(r"[A-Za-zÀ-ÿĀ-žǫðþÞÐ'-]+", s.lower()) if w.strip("'-")]


def parallel(recs):
    """(normalized words, English words) for every section that has both."""
    out = []
    for r in recs:
        N = dict(sections(r.get("normalization")))
        E = dict(sections(r.get("translation_en")))
        for lab, n in N.items():
            if lab in E:
                f = [normtok(w) for w in norm_words(n)]
                e = _english(E[lab])
                if f and e:
                    out.append((f, e))
    return out


class Glossary:
    def __init__(self, recs, iters=10):
        pairs = parallel(recs)
        self.n_pairs = len(pairs)
        self.t = defaultdict(dict)  # t[f][e] = P(e | f)
        cooc = defaultdict(set)
        for f, e in pairs:
            for fw in f + [NULL]:
                cooc[fw].update(e)
        for fw, es in cooc.items():
            u = 1.0 / len(es)
            self.t[fw] = {ew: u for ew in es}
        for _ in range(iters):  # EM: each English word is explained by one of the source words (or none)
            cnt = defaultdict(Counter)
            for f, e in pairs:
                src = f + [NULL]
                for ew in e:
                    z = sum(self.t[fw].get(ew, 0.0) for fw in src)
                    if z <= 0:
                        continue
                    for fw in src:
                        c = self.t[fw].get(ew, 0.0) / z
                        if c:
                            cnt[fw][ew] += c
            for fw, c in cnt.items():
                tot = sum(c.values())
                self.t[fw] = {ew: v / tot for ew, v in c.items()}
        self.freq = Counter(fw for f, _ in pairs for fw in f)
        # names (Rundata marks them with a quotation mark), written with a capital in a translation
        quoted, alltok = Counter(), Counter()
        for r in recs:
            n_ = r.get("normalization") or ""
            quoted.update(normtok(w) for w in re.findall(r'"([^\s,.;:!?/()\[\]"]+)', n_))
            alltok.update(normtok(w) for _, p in sections(n_) for w in norm_words(p))
        # a word counts as a name when it usually stands as one (Stæin, Faður and Broður are also names)
        self.names = {w for w, c in quoted.items() if c >= 0.5 * max(1, alltok[w])}

    def gloss(self, w, top=3, min_p=0.05):
        """[(English word, P)] for a normalized word; a name the glossary has not seen is translated by itself."""
        w = w.lstrip("§")
        if w in self.t and w != NULL:
            cand = [(e, p) for e, p in sorted(self.t[w].items(), key=lambda kv: -kv[1]) if p >= min_p]
            return cand[:top]
        return [(w, 1.0)]

    def content(self, w):
        """The meaning-bearing English words a normalized word stands for (most probable first)."""
        return [e for e, p in self.gloss(w, top=4) if e not in STOP]

    def best(self, w):
        """The gloss of a word for a draft translation: its most probable English word, skipping articles and
        prepositions the translation adds around it, and the formula 'in memory of' as one phrase."""
        g = self.gloss(w, top=4)
        es = {e for e, p in g if p >= 0.2}
        if {"in", "memory", "of"} <= es or {"memory", "of"} <= es:
            return "in memory of"
        for e, _ in g:
            if e not in FUNC:
                return e
        return g[0][0] if g else w

    def translate(self, words, lang="en"):
        """A word-by-word draft: for each word its best gloss; unknown words are left as '…'."""
        out = []
        for w in words:
            if w in ("<unk>", None):
                out.append("…")
                continue
            if w.startswith("§") or w in self.names:  # a name: as the glossary knows it, or as read
                e = self.best(w)
                e = SV.get(e, e) if lang == "sv" else e
                out.append(e[:1].upper() + e[1:] if e else w)
                continue
            e = self.best(w)
            if lang == "sv":
                if e in INF and w.endswith("a"):  # the infinitive: lät resa, lät hugga, lät göra
                    out.append(INF[e])
                    continue
                out.append(SV.get(e, " ".join(SV.get(x, x) for x in e.split())))
            else:
                out.append(e)
        return " ".join(x for x in out if x)
