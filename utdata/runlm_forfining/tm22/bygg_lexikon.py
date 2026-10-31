"""textmodel-22-kandidat (analysplaner/2026-10-30-litteraturlexikon.md, punkt 2): ordlistorna ur litteraturen.
N1 fornvästnordisk prosa (Heimskringla, fornaldarsagor, samtidssagor; utdata/varlden/korpus), N2 islänningasagorna
(sagadb, nutida stavning) om återföringsprovet når 95 %, N3 fornsvenska lagar (Språkbanken fsv-aldrelagar +
fsv-yngrelagar, inkl. Skånelagen), N4 Zoëgas uppslagsord och Petersons runnamn (namnmodellen).
Inga ord läggs till för hand; Rundata används inte som källa. Skriver data/cache/literature/lexikon/*.json och
utdata/runlm_forfining/tm22/lexikon_rapport.md.
    .venv/bin/python utdata/runlm_forfining/tm22/bygg_lexikon.py"""
import bz2
import csv
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src.runlm import normtok  # noqa: E402

KORPUS = os.path.join(ROOT, "utdata/varlden/korpus")
LEX = "/Volumes/2TB/litteratur/lexikon"
OUT = os.path.join(ROOT, "data/cache/literature/lexikon")
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)
WORD = re.compile(r"[A-Za-zÀ-ÿĀ-žǫǪęĘ]+")
# the letters the model's vocabulary accepts (runlm.Model: the index is built for words of these letters only)
PLAIN = re.compile(r"[a-zþðæøåöäąǫœáéíóúýęR]+")
V = "aeiouyáéíóúýöøæœǫę"


def tokens(path):
    """Word tokens of one text file, lower case, after the edition's front matter (the first chapter heading)."""
    text = open(path, encoding="utf-8").read()
    m = re.search(r"\n\s*(1\.|I\.|1\. kafli|I\. KAPÍTULI)\s", text)
    if m:
        text = text[m.start():]
    return [w.lower() for w in WORD.findall(text)]


def corpus(name):
    out = []
    for f in sorted(os.listdir(os.path.join(KORPUS, name))):
        out.extend(tokens(os.path.join(KORPUS, name, f)))
    return out


# ---- N2: modern Icelandic spelling → classical normalisation -----------------------------------------------------
# A small, regular rule set (the sagadb texts → the Linder & Haggson / Guðni Jónsson normalisation of N1), plus one
# exception: a form attested in N1 is kept as it stands (konur, grið, yður are old forms too). The rules are tested
# by moving N1 the other way (old_to_modern) and back; the exception list then comes from the OTHER half of N1
# (texts split in two), so that the test is not trivially passed. The plan's limit: 95 % of the word forms.
KIN = {"föður", "bróður", "móður", "dóttur", "systur", "fjögur", "sumur", "augu"}  # -ur that is old, not svarabhakti
FIXED = {"og": "ok", "að": "at", "það": "þat", "eg": "ek", "ég": "ek", "mig": "mik", "þig": "þik", "sig": "sik",
         "svo": "svá", "voru": "váru", "vorum": "várum", "hið": "hit", "þið": "þit", "nokkuð": "nökkut",
         "best": "bezt", "von": "ván", "vopn": "vápn", "vopnum": "vápnum", "tvo": "tvá", "vor": "vár", "vorið": "várit",
         "þykir": "þykkir", "þykist": "þykkist", "lítið": "lítit", "mikið": "mikit"}
INV = {v: k for k, v in FIXED.items()}
END = r"(?=(s|inn|inum|ins|na|nir|num|nar)?$)"


def modern_to_old(w, attested=frozenset()):
    if w in FIXED:
        return FIXED[w]
    if w in KIN or w in attested:
        return w
    o = w
    # the svarabhakti vowel: maður → maðr, hestur → hestr, also before an ending: hendur → hendr, veturinn → vetrinn
    o = re.sub(r"(?<=[^" + V + r"])ur" + END, "r", o)
    # the neuter -ið (participle, definite article) → -it after a consonant: tekið → tekit, sverðið → sverðit
    if o.endswith("ið") and len(o) >= 4 and o[-3] not in V and o not in ("grið", "frið", "hlið", "smið", "skið", "við"):
        o = o[:-2] + "it"
    return o


def old_to_modern(w):
    """The inverse, for the round-trip test (N1 forwards and back)."""
    if w in INV:
        return INV[w]
    if w in KIN:
        return w
    o = re.sub(r"(?<=[^" + V + r"])r" + END, "ur", w)
    if o.endswith("it") and len(o) >= 4 and o[-3] not in V:
        o = o[:-2] + "ið"
    return o


# ---- N3: Old Swedish orthography → the letters the model knows -------------------------------------------------
def fsv_letters(w):
    """th → þ, dh → ð, gh → g, w → v, c/q → k, x → ks, z → s, ä/å kept (the model spells them), i/j as written."""
    o = w.lower()
    o = o.replace("th", "þ").replace("dh", "ð").replace("gh", "g").replace("ch", "k")
    o = o.replace("w", "v").replace("qu", "kv").replace("q", "k").replace("x", "ks").replace("z", "s")
    o = re.sub(r"c(?=[eiyæ])", "s", o)
    o = o.replace("c", "k").replace("ff", "f").replace("ph", "f")
    return o


def main():
    rep = ["# Ordlistorna till textmodel-22 (bygg_lexikon.py)", ""]
    # N1
    n1 = Counter()
    for name in ("heimskringla", "fornaldarsogur", "samtidssagor"):
        c = Counter(corpus(name))
        rep.append(f"- N1 {name}: {sum(c.values())} ord, {len(c)} former")
        n1 += c
    # N2 round trip on N1: pure rules on all of N1, and with the attested exception taken from the other half
    halves = [Counter(), Counter()]
    i = 0
    for name in ("heimskringla", "fornaldarsogur", "samtidssagor"):
        for f in sorted(os.listdir(os.path.join(KORPUS, name))):
            halves[i % 2].update(tokens(os.path.join(KORPUS, name, f)))
            i += 1
    forms = [w for w in n1 if PLAIN.fullmatch(w)]
    pure_ok = sum(1 for w in forms if modern_to_old(old_to_modern(w)) == w)
    pure_share = pure_ok / len(forms)
    ok = tot = tok_ok = tok = 0
    wrong = Counter()
    for h in (0, 1):
        att = frozenset(w for w in halves[1 - h] if PLAIN.fullmatch(w))
        for w, c in halves[h].items():
            if not PLAIN.fullmatch(w):
                continue
            back = modern_to_old(old_to_modern(w), att)
            tot += 1; tok += c
            if back == w:
                ok += 1; tok_ok += c
            else:
                wrong[f"{w}→{back}"] += c
    share_forms, share_tok = ok / tot, tok_ok / tok
    rep += ["", f"## N2 återföringsprov på N1 (former fram och tillbaka)",
            f"- rena regler, hela N1: {pure_ok} av {len(forms)} former ({pure_share:.1%})",
            f"- regler + undantaget 'formen finns i N1:s andra hälft': {ok} av {tot} former ({share_forms:.1%}), ordförekomster {share_tok:.1%}; gräns 95 % av ordformerna",
            "Vanligaste som inte kommer tillbaka: " + ", ".join(f"{k} ({c})" for k, c in wrong.most_common(40))]
    n2_in = share_forms >= 0.95
    n2 = Counter()
    if n2_in:
        raw = Counter(corpus("islendingasogur"))
        att = frozenset(w for w in n1 if PLAIN.fullmatch(w))
        for w, c in raw.items():
            n2[modern_to_old(w, att)] += c
        before = sum(c for w, c in raw.items() if w in n1) / sum(raw.values())
        after = sum(c for w, c in n2.items() if w in n1) / sum(n2.values())
        new_forms = [w for w in n2 if w not in n1]
        rep += [f"- N2 islänningasagorna TAS MED: {sum(n2.values())} ord, {len(n2)} former efter återföring; andel ordförekomster "
                f"vars form finns i N1: {before:.1%} före, {after:.1%} efter; {len(new_forms)} former nya mot N1"]
    else:
        rep += ["- N2 islänningasagorna UTESLUTS (återföringsprovet under 95 %)"]
    # N3
    n3 = Counter()
    texts = Counter()
    for f in ("fsv-aldrelagar.xml.bz2", "fsv-yngrelagar.xml.bz2"):
        title = None
        with bz2.open(os.path.join(LEX, "fsv", f), "rt", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("<text "):
                    m = re.search(r'title="([^"]*)"', line)
                    title = m.group(1) if m else "?"
                elif line.startswith("<w "):
                    m = re.search(r">([^<]*)</w>", line)
                    if not m:
                        continue
                    w = m.group(1)
                    if not WORD.fullmatch(w) or re.fullmatch(r"[ivxlcdm]+", w.lower()):
                        continue  # numerals and punctuation
                    n3[fsv_letters(w)] += 1
                    texts[title] += 1
    rep += ["", f"## N3 fornsvenska lagar: {sum(n3.values())} ord, {len(n3)} former, {len(texts)} texter (Språkbanken "
            "fsv-aldrelagar + fsv-yngrelagar, CC BY 4.0)", "Texter: " + "; ".join(f"{t} ({c})" for t, c in sorted(texts.items()))]
    # N4 Zoëga
    z = json.load(open(os.path.join(LEX, "zoega", "zoega_no_markup.json"), encoding="utf-8"))
    heads = [x["word"].lower() for x in z]
    zoega = sorted({w for w in heads if PLAIN.fullmatch(w)})
    rep += ["", f"## N4 Zoëga: {len(heads)} uppslagsord, {len(zoega)} enkla ordformer tas med (sammansättningsled med bindestreck, "
            "flerordiga uppslag och ord med andra tecken utesluts); böjningsformer bildas inte"]
    # N4 Peterson names: headword keys + the signa each entry cites (for leak-free folds)
    pet = list(csv.DictReader(open(os.path.join(ROOT, "data/cache/literature/peterson2007_namn.csv"), encoding="utf-8")))
    sig = re.compile(r"\b(U|Sö|Ög|Vg|Sm|Öl|G|Vs|Nä|Hs|Gs|M|Ds|DR|N|Bo|J|Vr|Lp|Sl)\s?([0-9]+[A-Za-z]?|[A-Z][A-Za-z]*[0-9]+[;:][0-9]+[A-Z]?)\b")
    names = []
    for r in pet:
        for k in r["keys"].split("|"):
            k = k.strip()
            if PLAIN.fullmatch(k) and len(k) >= 3:
                names.append({"name": k, "gender": r["gender"], "signa": sorted({a + " " + b for a, b in sig.findall(r["block"])})})
    rep += ["", f"## N4 Peterson (2007): {len(pet)} uppslag → {len(names)} namnformer till namnmodellen; "
            f"{sum(1 for n in names if n['signa'])} med citerade signa (utesluts för provstenarnas veck)"]
    # the lists (words through normtok, as the Edda tokens are)
    lit = Counter()
    for c in (n1, n2, n3):
        for w, k in c.items():
            if PLAIN.fullmatch(w):
                lit[normtok(w)] += k
    lex = {normtok(w): 1 for w in zoega}
    json.dump(lit, open(os.path.join(OUT, "litteratur.json"), "w"), ensure_ascii=False)
    json.dump(lex, open(os.path.join(OUT, "lexikon.json"), "w"), ensure_ascii=False)
    json.dump(names, open(os.path.join(OUT, "namn.json"), "w"), ensure_ascii=False)
    json.dump({"N1": {k: v for k, v in n1.items() if PLAIN.fullmatch(k)}, "N2": dict(n2), "N3": dict(n3), "N2_in": n2_in,
               "roundtrip_forms": share_forms, "roundtrip_tokens": share_tok}, open(os.path.join(OUT, "nivaer.json"), "w"), ensure_ascii=False)
    rep += ["", f"## Listorna: litteratur.json {len(lit)} former ({sum(lit.values())} ord), lexikon.json {len(lex)} uppslagsord, "
            f"namn.json {len(names)} namn", f"Former i litteraturen som också är Zoëga-uppslag: {sum(1 for w in lit if w in lex)}"]
    open(os.path.join(HERE, "lexikon_rapport.md"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
