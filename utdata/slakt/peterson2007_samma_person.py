"""Peterson 2007 (Nordiskt runnamnslexikon, 5 uppl.): alla anmärkningar om att belägg avser samma person, ur två
OCR-versioner av lexikonet (/Volumes/2TB/litteratur/peterson2007_isof_ocr.pdf och peterson2007_runnamnslexikon.pdf,
text i /Volumes/2TB/tmp/peterson/). Varje anmärkning knyts till sitt uppslagsord; "Beläggen avser samma person" gäller alla
belägg under ordet. Ord som "sannolikt", "troligen", "trol.", "möjligen" gör resten av satsen osäker. Signum som de två
versionerna läser olika skrivs ut för kontroll mot sidbilden. Skriver peterson2007_samma_person.json.
Peterson anger själv (inledningen, s. 15) att anmärkningarna utan litteraturhänvisning bygger på Williams 1990, Axelson
1993 och Lerche Nielsen 1997.
    .venv/bin/python utdata/slakt/peterson2007_samma_person.py"""
import json
import os
import re

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
TXT = {"isof": "/Volumes/2TB/tmp/peterson/peterson2007_isof_ocr.txt", "lex": "/Volumes/2TB/tmp/peterson/peterson2007_runnamnslexikon.txt"}
PREF = {"U": "U", "1J": "U", "Sö": "Sö", "S6": "Sö", "$6": "Sö", "Sé": "Sö", "Ög": "Ög", "Og": "Ög", "Vg": "Vg", "Ve": "Vg",
        "Sm": "Sm", "Öl": "Öl", "Ol": "Öl", "G": "G", "Gs": "Gs", "Hs": "Hs", "Nä": "Nä", "Na": "Nä", "Vs": "Vs", "M": "M", "J": "J",
        "D": "D", "Bo": "Bo", "Vr": "Vr", "DR": "DR", "N": "N"}
SIG = re.compile(r"(?<![A-Za-zÅÄÖåäö])(1J|S6|\$6|Sé|Sö|Ög|Og|Vg|Ve|Sm|Öl|Ol|Gs|Hs|Nä|Na|Vs|Bo|Vr|DR|U|G|M|J|D|N)\s?"
                 r"(Fv\s?\d{4}\s?[;,:]\s?\d+[A-Za-z]?|[0-9lIO]{1,4}[A-Za-z]?)(?![0-9])")
HEAD = re.compile(r"^\s{0,3}\S.*\s(mn|kvn|bn|kvn\.|mn\.)\.?(\s|$)")
UNSURE = re.compile(r"\b(sannolikt|troligen|trol\.|möjligen|möjl\.|ev\.|kanske)(?=\W)", re.I)


def norm(pref, num):
    p = PREF[pref]
    if num.startswith("Fv"):
        y, n = re.split(r"\s?[;,:]\s?", num[2:].strip(), maxsplit=1)
        return f"{p} Fv{y};{n}"
    num = num.replace("l", "1").replace("I", "1").replace("O", "0")
    return f"{p} {num}"


def sigs(text):
    return [norm(a, b) for a, b in SIG.findall(text)]


SEG = re.compile(r";\s+(?=(?:1J|S6|\$6|Sö|Ög|Og|Vg|Ve|Sm|Öl|Ol|Gs|Hs|Nä|Vs|Bo|Vr|DR|U|G|M|J|D|N)\s?[0-9F]|trol|troligen|möjl|möjligen|sannolikt)")
MAX_ALL = 4   # "Beläggen avser samma person" utan lista: bara uppslagsord med högst så många belägg (annars kan belägg ha läckt in)


def notes(path):
    """Every note with its persons: a list of segments [(signa, unsure)], one per person (semicolons separate persons)."""
    lines = open(path, encoding="utf-8").read().split("\n")
    out, head, att = [], None, []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if HEAD.match(ln) and not re.search(r"samma\s+person", ln, re.I):
            head, att = ln.strip(), []
        elif re.match(r"^\s*(Nom|Gen|Dat|Ack|Obl|Pl|Sg)\.", ln):
            att += sigs(ln)
        if re.search(r"samma\s+person", ln, re.I) or (re.search(r"samma$", ln.strip(), re.I) and i + 1 < len(lines) and lines[i + 1].strip().startswith("person")):
            t = ln.strip()
            if not re.match(r"^(Belägg|Samma|Båda|De |Det |Ev\.|Åtm)", t, re.I) and i > 0:  # avstavat: början på raden före
                t = lines[i - 1].strip().rstrip("-") + ("" if lines[i - 1].strip().endswith("-") else " ") + t
            j = i + 1
            while not t.rstrip().endswith(".") and j < len(lines) and lines[j].strip() and not HEAD.match(lines[j]):
                t += " " + lines[j].strip(); j += 1
            m = re.search(r"(Belägg\w*|Samma person|Beliggen|Belaggen|Belággen|Båda|Bada)", t)
            t = t[m.start():] if m else t
            tt = re.sub(r"Bel[aáiä]ggen", "Beläggen", t)
            prot = re.sub(r"\b(trol|möjl|ev|äv|jfr|bl\.a|s|ms|resp|dvs|ff|f|sk|ca)\.", lambda m_: m_.group(1) + "§", tt)
            first = re.split(r"\.\s+(?=[A-ZÅÄÖ])", prot)[0].replace("§", ".")   # bara första meningen
            segs = []
            for part in SEG.split(first):
                u = UNSURE.search(part)
                if segs and segs[-1]["open_unsure"] and not sigs(part[:u.start()] if u else part) and not u:
                    pass
                sure_s, unsure_s = (sigs(part[:u.start()]), sigs(part[u.start():])) if u else (sigs(part), [])
                if segs and segs[-1]["open_unsure"]:      # efter "trol."/"möjl." förblir följande personer osäkra
                    sure_s, unsure_s = [], sure_s + unsure_s
                if sure_s or unsure_s:
                    segs.append({"sure": sure_s, "unsure": unsure_s, "open_unsure": bool(u) or (bool(segs) and segs[-1]["open_unsure"])})
            every = not segs and re.match(r"^(Beläggen|Båda beläggen|Bada beläggen|Beläggen i båda inskrifterna) (avser|avses)", tt) is not None
            if every and 2 <= len(set(att)) <= MAX_ALL:
                u = bool(UNSURE.search(first))
                segs = [{"sure": [] if u else sorted(set(att)), "unsure": sorted(set(att)) if u else [], "open_unsure": u}]
            out.append({"head": head, "text": t, "all": every, "segments": segs, "attestations": sorted(set(att))})
            i = j
            continue
        i += 1
    return out

A, B = notes(TXT["isof"]), notes(TXT["lex"])
intro = lambda n: n["text"].startswith("Belägg avseende samma person")  # noqa: E731  innehållsförteckning och inledning
A, B = [n for n in A if not intro(n)], [n for n in B if not intro(n)]
import sys  # noqa: E402
import unicodedata  # noqa: E402
sys.path.insert(0, ROOT)
from src import linking as L  # noqa: E402
from src.entities import extract  # noqa: E402

RD = json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]
BY = {r["signum"]: r for r in RD}
FOLD = {re.sub(r"\s+", "", s).lower(): s for s in BY}
SE = ("U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Nä", "Vs", "Gs", "Hs", "M", "J", "D", "Bo", "Vr")
STONES = {k for k in L.stones(RD) if k.split(" ")[0] in SE}
assert len(STONES) == 2320
fold = lambda x: "".join(c for c in unicodedata.normalize("NFKD", x.lower()) if c.isalpha() and not unicodedata.combining(c))  # noqa: E731


def rd(s):
    return FOLD.get(re.sub(r"\s+", "", re.sub(r"[t†$]$", "", s)).lower())


def nfold(x):
    x = x.lower()
    for a, b in (("þ", "th"), ("ð", "d"), ("æ", "ae"), ("ø", "o"), ("ö", "o"), ("ǫ", "o"), ("ä", "a"), ("å", "a"), ("j", "i")):
        x = x.replace(a, b)
    return "".join(c for c in unicodedata.normalize("NFKD", x) if c.isalpha() and not unicodedata.combining(c))


def head_variants(head):
    """'Ar(i)n-/Ær(i)nbiorn mn.' -> the spellings of the headword, folded."""
    h = re.split(r"\s(mn|kvn|bn)\.", head or "")[0]
    h = re.sub(r"\((\?|se [^)]*|jfr [^)]*|el\.[^)]*)\)", "", h)
    return {nfold(v) for v in h.split("/") if len(nfold(v)) >= 3}


def carver_note(head, signa):
    """The headword names a carver (signed or attributed) on at least one of the stones: the note is about a carver, not
    a family (our linking leaves carvers out). Spellings compared with difflib (ratio at least 0.75), since the lexicon
    writes Viseti, Þorbiorn and Lik(n)biorn where Rundata has Veseti, Þorbjôrn and Likbjôrn."""
    import difflib
    hv = head_variants(head)
    if not hv:
        return False
    for s in signa:
        r = BY.get(s)
        if not r:
            continue
        names = {nfold(c.get("name") or "") for c in r.get("carvers") or []} | {nfold(p["key"]) for p in extract(r)["persons"] if p["role"] == "ristare"}
        if any(difflib.SequenceMatcher(a=h, b=re.sub(r"\d+$", "", x)).ratio() >= 0.75 for h in hv for x in names if x):
            return True
    return False


# Som Williams (1990 s. 186): Ingvars-, Knuts- och Frögersstenarna nämner samma kända man, inte en släkt, och räknas inte
FAMOUS = ("ingvar", "knut", "frog", "frøg")


def pairs(notes):
    out = {}
    for n in notes:
        if any(v.startswith(f) for v in head_variants(n["head"]) for f in FAMOUS):
            continue
        for seg in n["segments"]:
            su = sorted({x for x in map(rd, seg["sure"]) if x})
            un = sorted({x for x in map(rd, seg["unsure"]) if x and x not in su})
            carv = carver_note(n["head"], su + un)
            for i, a in enumerate(su):
                for b in su[i + 1:]:
                    out.setdefault((a, b), {"sure": True, "head": n["head"], "carver": carv})
            for a in un:
                for b in su + [x for x in un if x != a]:
                    k = tuple(sorted((a, b)))
                    out.setdefault(k, {"sure": False, "head": n["head"], "carver": carv})
    return out


PA, PB = pairs(A), pairs(B)
both = sorted(set(PA) & set(PB))
disagree = sorted(set(PA) ^ set(PB))
W = json.load(open(os.path.join(OUT, "williams1990_bilaga.json"), encoding="utf-8"))
gid = {}
for gi, g in enumerate(W["groups"]):
    for m in g["members"]:
        gid.setdefault(m["rundata"], set()).add(gi)
rows = []
for k in both:
    a, b = k
    x = PA[k]
    rows.append({"a": a, "b": b, "sure": x["sure"] and PB[k]["sure"], "head_isof": x["head"], "head_lex": PB[k]["head"],
                 "carver": x["carver"] or PB[k]["carver"], "stones": a in STONES and b in STONES,
                 "in_williams": bool(gid.get(a, set()) & gid.get(b, set()))})
use = [r for r in rows if r["stones"] and not r["carver"]]
out = {"source": "Peterson, L. 2007. Nordiskt runnamnslexikon. 5 uppl. Uppsala: Institutet för språk och folkminnen.",
       "note": "Peterson (s. 15): anmärkningar utan litteraturhänvisning bygger på Williams 1990, Axelson 1993, Lerche Nielsen 1997.",
       "n_notes": [len(A), len(B)], "n_pairs_both_versions": len(both), "n_pairs_disagree": len(disagree),
       "disagree": [list(k) for k in disagree], "pairs": rows,
       "validation": {"n_pairs": len(use), "n_sure": sum(r["sure"] for r in use),
                      "n_in_williams": sum(r["in_williams"] for r in use),
                      "n_not_in_williams": sum(not r["in_williams"] for r in use),
                      "n_sure_not_in_williams": sum(r["sure"] and not r["in_williams"] for r in use),
                      "n_carver_pairs_excluded": sum(1 for r in rows if r["carver"] and r["stones"])}}
json.dump(out, open(os.path.join(OUT, "peterson2007_samma_person.json"), "w"), ensure_ascii=False, indent=1)
print({k: v for k, v in out.items() if k in ("n_notes", "n_pairs_both_versions", "n_pairs_disagree")}, out["validation"])
print("olika i versionerna:", out["disagree"][:30])
