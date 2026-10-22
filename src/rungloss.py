"""Från fornspråkliga ord till översättning: en ordlista som lärs ur Rundatas texter och deras engelska översättningar,
utan någon tryckt ordbok.

Varje vikingatida inskrift finns i Rundata både som normaliserad fornspråklig text och som engelsk översättning.
En översättningsmodell av det enklaste slaget (IBM-modell 1, Brown m.fl. 1993) lär sig, genom att räkna vilka ord
som återkommer tillsammans i samma inskrift och dess översättning, sannolikheten P(engelskt ord | fornspråkligt ord).
Den kräver ingen ordlista och ingen ordföljd, och den räknar med att varje engelskt ord kan sakna motsvarighet (ett
tomt ord). Namn som modellen inte har sett översätts med sig själva.

Den svenska versionen kan också gå via danska: Danske Runeindskrifter (runer.ku.dk) översätter de danska inskrifterna
till danska, och en andra ordlista lärs mellan Rundatas fornvästnordiska standardformer och de danska översättningarna.
Danskan ligger närmare svenskan än engelskan: den skiljer infinitiv från preteritum (lod rejse → lät resa), har numerus
på possessivet (sine brødre → sina bröder) och ger namnen i nordisk form (Thorbjørn → Torbjörn). Ett ord tar den danska
vägen bara när den danska ordlistan känner det och det danska ordet finns i den handgranskade listan DA_SV; annars går
det som förut via engelskan.

Används av scripts/runlm_gloss_test.py och scripts/runlm_gloss_da_test.py (prov på inskrifter som inte fanns i
träningen) och för att ge en läsning från src/runlm.py ett översättningsutkast."""
import difflib
import os
import re
from collections import Counter, defaultdict

from src.runlm import ROOT, normtok, norm_words, sections

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
      "christ": "Kristus", "dear": "kär", "valiant": "tapper", "partner": "bolagsman", "slab": "häll", "rock": "häll",
      "coloured": "färgade", "painted": "målade", "let": "lät", "stand": "stå", "stands": "står", "here": "här",
      "foster": "foster", "uncle": "farbror", "nephew": "brorson", "kinsman": "frände", "friend": "vän", "land": "land",
      "home": "hem", "journey": "resa", "travelled": "färdades", "abroad": "utomlands", "gold": "guld", "men": "män",
      "man": "man", "woman": "kvinna", "the": "", "a": "", "may": "", "lord": "herre",
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
      "everlasting": "evig", "mercy": "nåd", "living": "levande", "stood": "stod", "sat": "satt",
      "interpret": "tyda", "secure": "säkra", "rich": "rik", "fine": "fin", "brave": "modig", "generous": "givmild"}
# a verb in the infinitive (ræisa, haggva, gæra …) after 'lät' is glossed by the translations' past participle
INF = {"raised": "resa", "erected": "resa", "cut": "hugga", "made": "göra", "carved": "rista", "placed": "sätta",
       "coloured": "färga", "painted": "måla"}

# The table of Danske Runeindskrifter (runer.ku.dk), copied by hand (utdata/ is not published; see its README.md)
DA_PATH = os.path.join(ROOT, "utdata", "Malt", "kallor", "runer_ku", "indskrifter.txt")
# Danish words that carry grammar rather than meaning (left out when a Danish draft is compared with a translation)
DA_STOP = set("""en et den det de at af i til på for med ved og som er var han hun hans hendes sin sine sit deres dette
denne disse der her ham hende dem sig om""".split())
# articles and prepositions a Danish translation adds around a word; not the gloss of a word unless nothing else is
DA_FUNC = set("en et den det de at af til for med ved".split())
# Swedish for the words of the Danish translations (checked by hand); a Danish word not listed is not used
DA_SV = {"efter": "efter", "sten": "sten", "stenen": "stenen", "stene": "stenar", "og": "och", "denne": "denna",
         "dette": "detta", "disse": "dessa", "sin": "sin", "sine": "sina", "sit": "sitt", "rejste": "reste",
         "rejse": "resa", "søn": "son", "sønner": "söner", "sønnerne": "sönerna", "satte": "satte", "sætte": "sätta",
         "broder": "broder", "bror": "bror", "brødre": "bröder", "god": "god", "gode": "gode", "fader": "fader",
         "far": "far", "deres": "deras", "som": "som", "lod": "lät", "hans": "hans", "hendes": "hennes",
         "gjorde": "gjorde", "gøre": "göra", "hjælpe": "hjälpe", "kumler": "kummel", "kuml": "kummel",
         "kumlet": "kumlet", "meget": "mycket", "såre": "mycket", "i": "i", "er": "är", "mand": "man",
         "sjæl": "själ", "sjæle": "själar", "til": "till", "dreng": "dräng", "drenge": "drängar", "var": "var",
         "for": "för", "thegn": "tägn", "þegn": "tägn", "af": "av", "runer": "runor", "runerne": "runorna",
         "ristede": "ristade", "riste": "rista", "de": "de", "han": "han", "hun": "hon", "med": "med",
         "fælle": "bolagsman", "fæller": "bolagsmän", "på": "på", "men": "men", "eller": "eller", "moder": "moder",
         "mor": "mor", "skal": "ska", "døde": "dog", "fandt": "fann", "døden": "döden", "hugge": "hugga",
         "huggede": "högg", "ånd": "ande", "datter": "dotter", "hirdmand": "hirdman", "kone": "hustru",
         "hustru": "hustru", "ægtefælle": "make", "ægtemand": "make", "stå": "stå", "står": "står", "ved": "vid",
         "vil": "vill", "ligger": "ligger", "om": "om", "længe": "länge", "måg": "måg", "da": "då",
         "sammen": "tillsammans", "ejede": "ägde", "ejer": "äger", "skib": "skepp", "høj": "hög", "højen": "högen",
         "begge": "båda", "blev": "blev", "dræbt": "dräpt", "bonde": "bonde", "kan": "kan", "bro": "bro",
         "broen": "bron", "malede": "målade", "vie": "vige", "frænde": "frände", "vel": "väl", "end": "än",
         "bedste": "bäste", "hos": "hos", "gav": "gav", "ham": "honom", "hende": "henne", "sig": "sig", "har": "har",
         "tre": "tre", "to": "två", "nu": "nu", "jeg": "jag", "lys": "ljus", "paradis": "paradis", "evigt": "evigt",
         "rigtigt": "rätt", "ret": "rätt", "søster": "syster", "druknede": "drunknade", "hele": "hela",
         "uden": "utan", "lever": "lever", "leve": "leva", "skipper": "skeppare", "skippere": "skeppare",
         "drot": "drott", "vorde": "varde", "ræte": "rete", "over": "över", "tog": "tog", "smed": "smed",
         "bryder": "bryter", "mindesmærke": "minnesmärke", "minde": "minne", "landbestyrer": "förvaltare",
         "gods": "gods", "dig": "dig", "giver": "ger", "kvinde": "kvinna", "blive": "bli", "selv": "själv",
         "min": "min", "flygtede": "flydde", "viking": "viking", "alle": "alla", "sværd": "svärd",
         "hellige": "helige", "sønnesøn": "sonson", "brodersøn": "brorson", "fostersøn": "fosterson",
         "stedfader": "styvfar", "østpå": "österut", "vesterpå": "västerut", "nordpå": "norrut", "sydpå": "söderut",
         "død": "död", "sted": "plats", "her": "här", "herfra": "härifrån", "fra": "från", "under": "under",
         "konge": "kung", "kong": "kung", "konger": "kungar", "dronning": "drottning", "kæmpede": "stred",
         "guld": "guld", "klog": "klok", "første": "förste", "bedst": "bäst", "altid": "alltid", "hvem": "vem",
         "skjulte": "dolde", "kristne": "kristna", "vandt": "vann", "bød": "bjöd", "lagde": "lade",
         "byggede": "byggde", "elskede": "älskade", "kær": "kär", "største": "störste", "blandt": "bland",
         "mænd": "män", "gift": "gift", "sagde": "sade", "lad": "låt", "navn": "namn", "liv": "liv",
         "levende": "levande", "evige": "eviga", "gud": "Gud", "guds": "Guds", "krist": "Kristus",
         "kristus": "Kristus", "sankt": "sankt", "mikael": "Mikael", "maria": "Maria", "thor": "Tor",
         "landmand": "landman", "landmænd": "landmän", "bomænd": "bomän", "hirden": "hirden", "søstersøn": "systerson",
         "sejdkarl": "sejdkarl", "kampen": "striden", "kamp": "strid", "danmark": "Danmark", "england": "England",
         "norge": "Norge", "svitjod": "Svitjod", "gotland": "Gotland", "hedeby": "Hedeby", "uppsala": "Uppsala",
         "london": "London", "øresund": "Öresund"}
# Danish words of the same meaning counted as one, so that the glossary does not split them (mor/moder, stenen/sten)
DA_SAME = {"mor": "moder", "far": "fader", "bror": "broder", "stenen": "sten", "kuml": "kumler", "kumlet": "kumler"}
# Danish name forms whose Swedish form is not just a matter of spelling
NAME_SV = {"svend": "Sven", "svenne": "Svenne", "troels": "Torgils", "keld": "Ketil", "esbern": "Åsbjörn"}
# possessives and demonstratives that Old Norse puts after the noun (faður sinn, stæin þennsi), and words that are not
# such a noun
POST = {"sin", "sina", "sitt", "denna", "dessa", "detta"}
# nouns in the singular, after which 'dessa' (Old Norse þessa, also singular) is 'denna' (brú þessa → denna bro)
SG = {"bro", "sten", "hög", "häll", "väg", "själ", "ande", "son", "broder", "fader", "moder", "hustru", "dotter"}
# and plural nouns, after which 'denna' is 'dessa' (stæina þessa → dessa stenar)
PL = {"stenar", "runor", "söner", "bröder", "bolagsmän", "drängar", "broar", "själar"}
# adjectives that Old Norse may put after the noun (drængR goðr → god dräng), with 'mycket' before them
ADJ = {"god", "gode", "goda", "tapper", "bäste", "bäst", "ung", "rik", "givmild", "modig", "kär", "klok"}
NOUN_HANS = {"själ", "ande", "son", "broder", "bror", "fader", "far", "moder", "mor", "hustru", "make", "dotter",
             "själar", "söner", "bröder"}
NOT_NOUN = {"efter", "och", "lät", "reste", "satte", "gjorde", "i", "…", "av", "till", "på", "med", "vid", "som",
            "var", "är", "hjälpe", "resa", "göra", "hugga", "högg", "ristade", "ägde"}


def _english(s):
    s = re.sub(r"\(\?\)|\[|\]|\(|\)|<[^>]*>", " ", s or "")
    return [w for w in re.findall(r"[A-Za-zÀ-ÿĀ-žǫðþÞÐ'-]+", s.lower()) if w.strip("'-")]


def _danish(s):
    """The words of a Danish translation: editorial marks (?), [], (), *, N.N. and alternatives after '/' left out."""
    s = re.sub(r"\(\?\)|N\.N\.?|\b(el|ell|dvs|jf)\.", " ", s or "")
    s = re.sub(r"(\S+)/\S+", r"\1", s)
    s = re.sub(r"[\[\]()*{}'\"‘’]", "", s)
    return [DA_SAME.get(w, w) for w in re.findall(r"[A-Za-zÆØÅæøåÀ-ÿǫðþ-]+", s.lower())
            if w.strip("-") and len(w.strip("-")) > 1 or w == "i"]


def parallel(recs, field="translation_en", words=_english, src="normalization"):
    """(normalized words, translated words) for every section that has both. A translation without sections (the
    Danish ones) is paired with the whole text."""
    out = []
    for r in recs:
        N = dict(sections(r.get(src)))
        E = dict(sections(r.get(field)))
        common = [lab for lab in N if lab in E]
        if not common and list(E) == ["-"] and N:
            f = [normtok(w) for p in N.values() for w in norm_words(p)]
            e = words(E["-"])
            if f and e:
                out.append((f, e))
            continue
        for lab in common:
            f = [normtok(w) for w in norm_words(N[lab])]
            e = words(E[lab])
            if f and e:
                out.append((f, e))
    return out


class Glossary:
    def __init__(self, recs, iters=10, field="translation_en", words=_english, src="normalization"):
        """field: the translation learned from (translation_en, or translation_da from load_danish); src: the
        normalization it is learned against (normalization_ows: the standard Old West Norse forms)."""
        self.src = src
        pairs = parallel(recs, field, words, src)
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
            n_ = r.get(self.src) or ""
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

    def best_da(self, w, min_n=3, min_p=0.4):
        """(Danish word, probability) for a word, when the glossary knows it well enough (seen min_n times, its gloss
        at least min_p probable); articles and prepositions only when nothing else is likely. None otherwise."""
        if self.freq.get(w, 0) < min_n:
            return None
        g = self.gloss(w, top=4)
        if not g:
            return None
        for e, p in g:
            if e not in DA_FUNC and p >= 0.2:
                return (e, p) if p >= min_p or g[0][0] in DA_FUNC else None
        return g[0] if g[0][1] >= min_p else None

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


def load_danish(recs, path=DA_PATH):
    """{Rundata signum: Danish translation} from the table of Danske Runeindskrifter (runer.ku.dk: signum,
    transliteration, Danish and English translation, separated by eight spaces). A row is matched to Rundata by
    Rundata's own reference to the Danish number ('DK nr.: Sl 1') or by a signum 'DR DK…'. Empty without the table."""
    if not os.path.exists(path):
        return {}
    key = lambda s: s.lower().replace(" ", "")
    dk = {}
    for r in recs:
        for m in re.finditer(r"dk nr\.:\s*([^,;]+)", (r.get("references") or "").lower()):
            dk.setdefault(key(m.group(1)), r["signum"])
        m = re.match(r"DR DK(\S+)", r["signum"])
        if m:
            dk.setdefault(key(m.group(1)), r["signum"])
    out = {}
    for line in open(path, encoding="utf-8-sig").read().splitlines():
        parts = [x.strip() for x in line.split(" " * 8)]
        if len(parts) != 4 or not parts[2]:
            continue
        sig = dk.get(key(parts[0]))
        # a translation that only says the text cannot be read ('Utolket', 'Indskriften er for ødelagt …') is no use
        if sig and re.search(r"[a-zæøå]", parts[2]) and not re.match(r"(Utolket|Indskrift|Næppe|Uden|Tolkning)", parts[2]):
            out.setdefault(sig, parts[2])
    return out


def ows_map(recs):
    """Each of Rundata's normalized words (runic Swedish and Danish) → its commonest standard Old West Norse form
    (normalization_ows), from the sections where the two have the same number of words: stæin and sten → stein."""
    pairs = defaultdict(Counter)
    for r in recs:
        O = dict(sections(r.get("normalization_ows")))
        for lab, n in sections(r.get("normalization")):
            if lab in O:
                a, b = norm_words(n), norm_words(O[lab])
                if len(a) == len(b):
                    for x, y in zip(a, b, strict=False):
                        pairs[normtok(x)][normtok(y)] += 1
    return {w: c.most_common(1)[0][0] for w, c in pairs.items()}


def _plain(s):
    """A name in plain letters, for comparing an Old Norse form with a Danish one (Þorbjǫrn ~ Thorbjørn)."""
    s = s.lower().replace("th", "t").replace("þ", "t").replace("ð", "d").replace("aa", "a")
    s = s.translate(str.maketrans("ǫøöæäåáéíóúýj", "ooo aaaeiouyi".replace(" ", "e")))
    return re.sub(r"[^a-z]", "", s)


def _same_name(on, da):
    a, b = _plain(on), _plain(da)
    return bool(a and b) and a[0] == b[0] and difflib.SequenceMatcher(None, a, b).ratio() >= 0.5


def _sv_name(da):
    """A Danish name form in Swedish spelling: Thorbjørn → Torbjörn, Ødbjørn → Ödbjörn, Svend → Sven."""
    if da.lower() in NAME_SV:
        return NAME_SV[da.lower()]
    s = re.sub(r"^th", "t", da.lower()).replace("aa", "å").replace("ø", "ö").replace("æ", "ä")
    return "-".join(p[:1].upper() + p[1:] for p in s.split("-"))


def swedish(words, en, da=None, ows=None, reorder=True):
    """A Swedish draft of a reading (normalized words, '<unk>' for a word not read). en: the English glossary; da: a
    Danish one (Glossary(..., field='translation_da', words=_danish, src='normalization_ows')), with ows from ows_map.
    A word goes through Danish when the Danish glossary knows it and the Danish word is in DA_SV (a name when the
    Danish form is the same name), unless the English glossary gives another Swedish word with a higher probability;
    otherwise through English. reorder: possessives and demonstratives that Old Norse
    puts after the noun are put before it, as in Swedish (faður sinn → sin fader, stæin þennsi → denna sten), with a
    comma when they follow a name (efter Saxi, sin son)."""
    toks = []  # [Swedish, is a name, through Danish]
    for w in words:
        if w in ("<unk>", None):
            toks.append(["…", False, False])
            continue
        w0 = w.lstrip("§")
        name = w.startswith("§") or w0 in en.names
        sv = None
        if da is not None:
            o = (ows or {}).get(w0, w0)
            dp = da.best_da(o)
            if dp:
                d, p_da = dp
                if name:
                    sv = _sv_name(d) if _same_name(o, d) else None
                else:
                    sv = DA_SV.get(d)
                    e = en.best(w)
                    if sv and SV.get(e) and SV[e] != sv and en.t.get(w, {}).get(e, 0.0) > p_da:
                        sv = None
        toks.append([sv, name, True] if sv else [en.translate([w], "sv"), name, False])
    if reorder:
        i = 0
        while i < len(toks) - 1:
            a, b = toks[i], toks[i + 1]
            if not a[1] and a[0] and (b[0] in POST or (b[0] == "hans" and a[0] in NOUN_HANS)) and a[0] not in NOT_NOUN \
                    and a[0] not in POST:
                b = (["denna"] + b[1:] if b[0] == "dessa" and a[0] in SG else
                     ["dessa"] + b[1:] if b[0] == "denna" and a[0] in PL else b)
                toks[i], toks[i + 1] = b, a
                if i > 0 and toks[i - 1][1]:
                    toks[i - 1] = [toks[i - 1][0] + ",", True, toks[i - 1][2]]
                i += 2
                continue
            i += 1
        i = 1
        while i < len(toks):  # noun (mycket) god → (mycket) god noun
            j = i + 1 if toks[i][0] == "mycket" and i + 1 < len(toks) else i
            a = toks[i - 1]
            if toks[j][0] in ADJ and not a[1] and a[0] and a[0] not in NOT_NOUN | POST | ADJ | {"mycket"}:
                toks[i - 1:j + 1] = toks[i:j + 1] + [a]
                i = j + 1
                continue
            i += 1
    return " ".join(t[0] for t in toks if t[0])
