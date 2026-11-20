"""Petersons Nordiskt runnamnslexikon (2007, 5 uppl.) som tabell, kontrollerad mot Rundata.

Läser sidtexten från scripts/peterson_ocr.py (/Volumes/2TB/cache/peterson_ocr/<inställning>/pNNN.tsv), delar den i
uppslag med hjälp av indraget (uppslagsorden står mot vänstermarginalen, artikeltexten är indragen), tolkar
uppslagsord, kön, fornvästnordisk form och beläggen (runform + signum per kasus) och prövar varje belägg mot Rundata
(data/rundata.json): finns signumet, och står formen i stenens translitterering? Signum som tesseract läst nästan
rätt (gammaldags siffror: Ögl83 = Ög 183; flaggan $ läst som siffra: U5854 = U 585$) rättas bara om formen står
på den rättade stenen och rättelsen är entydig; rättelsen markeras i kolumnen `rattat`.

Lexikonet är upphovsrättsskyddat: tabellen skrivs bara till data/cache/literature/ (git-ignorerad), aldrig in i git.

    .venv/bin/python scripts/peterson_lexikon.py --ocr /Volumes/2TB/cache/peterson_ocr/full          # skriv tabellen
    .venv/bin/python scripts/peterson_lexikon.py --prov DIR1 DIR2 ... --pages 20,45                  # jämför stickprov
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import unicodedata
from collections import Counter, defaultdict
from functools import lru_cache

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RUNDATA = os.path.join(ROOT, "data", "rundata.json")
OUT = os.path.join(ROOT, "data", "cache", "literature", "peterson2007_namn.csv")
OLD = os.path.join(ROOT, "data", "cache", "literature", "peterson2007_namn_fore_2026-11-20.csv")
PDF = "/Volumes/2TB/litteratur/peterson2007_runnamnslexikon.pdf"
CACHE = "/Volumes/2TB/cache/peterson_ocr"
FIRST_PAGE, LAST_PAGE = 17, 272  # personal-name lexicon (PDF pages); then frequency tables, uninterpreted, places

CASES = r"(?:[Nn]om|[Gg]en|[Dd]at|[Aa]ck|Vok|Instr|Obl)"
CASE_RE = re.compile(r"(?<![A-Za-zåäö])(" + CASES + r"[.,]|Kasus ovisst:)\s*")
STOP_RE = re.compile(r"\b(?:L[iíì]tt|Anm|Sms|Lit)[.,]?\s*:|\bSe även\b|\bSe äv\b|\bBel[äaáàåã]gg(?:en|et)\b|\bSamma person\b"
                     r"|\bJfr\b|\bNamnet\b|\bOm namnet\b|\b(?:Fsv|Fda|Fvn|Fgutn|Fl|F\.l|E\.l|Trol|Möjl)\.\s"
                     r"|\s(?:mn|kvn)\.(?:\s|$)")
# OCR variants of province prefixes (old-style figures and the small ö confuse tesseract)
PREFIX_FIX = {"S6": "Sö", "$6": "Sö", "So": "Sö", "Sé": "Sö", "S0": "Sö", "Só": "Sö", "Sô": "Sö", "Sò": "Sö", "Së": "Sö",
              "$ö": "Sö", "Sø": "Sö", "Og": "Ög", "Óg": "Ög", "Ôg": "Ög", "0g": "Ög", "Õg": "Ög", "Øg": "Ög", "Òg": "Ög",
              "Ol": "Öl", "OI": "Öl", "0l": "Öl", "ÖI": "Öl", "Ól": "Öl", "O1": "Öl", "Öi": "Öl", "Øl": "Öl", "Na": "Nä", "Ná": "Nä", "SM": "Sm", "Sin": "Sm",
              "VG": "Vg", "Ve": "Vg", "Vy": "Vg", "Vz": "Vg", "Ög": "Ög", "Öl": "Öl", "Sö": "Sö", "Nä": "Nä", "Gs": "Gs",
              "Hs": "Hs", "DK": "DR", "Dr": "DR"}
RUNIC_LETTERS = "abcdefghijklmnopqrstuvwxyzþðæøåäöąǫ"


# ---------------------------------------------------------------------------------------------------------------------
# keys (unchanged from utdata/litteraturdata/peterson_namn.py so old and new tables compare)
def key(n: str) -> str:
    """Samma nyckel för Petersons och Rundatas former: þ/ð, ô/ǫ/ø/œ, æi/ei, j/i, R/r och dubbeltecken förs samman."""
    s = (n.replace("Þ", "th").replace("þ", "th").replace("ð", "d").replace("ô", "o").replace("ǫ", "o").replace("ø", "o")
         .replace("œ", "o").replace("Œ", "o").replace("Ø", "O").replace("æi", "ei").replace("Æi", "ei").replace("æ", "e").replace("Æ", "e")
         .replace("ey", "øy").replace("Ey", "øy").replace("ø", "o"))
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower().replace("j", "i").replace("R", "r")
    return re.sub(r"[^a-z]", "", re.sub(r"(.)\1+", r"\1", s))


ENDINGS = ("iar", "ar", "ur", "ir", "r", "s", "a", "i", "u", "e", "o")


def stem(n: str) -> str:
    """key() without the case ending, so Rundata's inflected names (Friðlæifs, Friðmund, Hrifla) meet Peterson's
    nominative headwords (Friðlæifr, Friðmundr, Hrifli)."""
    k = key(n)
    for e in ENDINGS:
        if k.endswith(e) and len(k) - len(e) >= 3:
            return k[:-len(e)]
    return k


def compact(s: str) -> str:
    """Runic transliteration -> letters only (separators, brackets, uncertainty marks and bind-rune ^ removed)."""
    s = s.replace("ʀ", "R").lower()
    return "".join(c for c in s if c in RUNIC_LETTERS)


def sigkey(s: str) -> str:
    return re.sub(r"\s+", "", s).lower()


# ---------------------------------------------------------------------------------------------------------------------
# Rundata
class Rundata:
    def __init__(self, path: str = RUNDATA):
        d = json.load(open(path, encoding="utf-8"))
        self.text: dict[str, str] = {}
        self.canon: dict[str, str] = {}
        names = set()
        for i in d["inscriptions"]:
            sig = i["signum"]
            self.canon[sigkey(sig)] = sig
            self.text[sig] = self.text.get(sig, "") + " " + compact(i.get("transliteration") or "")
            for m in re.finditer(r'"\[?([A-ZÆØÞÅÄÖÉÁÍÓÚ][^\s,.;:!?"/()<>{}]*)', i.get("normalization") or ""):
                names.add(m.group(1).replace("[", "").replace("]", ""))
        for a, b in d["aliases"].items():
            if sigkey(b) in self.canon and sigkey(a) not in self.canon:
                self.canon[sigkey(a)] = self.canon[sigkey(b)]
        self.names = names
        self.name_keys = {key(n) for n in names}
        self.name_stems = {stem(n) for n in names} - {""}
        self.prefixes = sorted({s.split()[0] for s in self.canon.values()} | {a.split()[0] for a in d["aliases"]},
                               key=len, reverse=True)

    def lookup(self, sig: str) -> str | None:
        """Peterson's signum (no space: U585, DRAUD1999;288, Sö238) -> Rundata signum, also via aliases and with a
        side letter (DR143A) mapped to the whole stone (DR 143)."""
        k = sigkey(sig)
        if k in self.canon:
            return self.canon[k]
        m = re.fullmatch(r"(.*\d)[a-f]", k)
        if m and m.group(1) in self.canon:
            return self.canon[m.group(1)]
        return None

    def has_form(self, sig: str, form: str) -> bool:
        """The form (or one of its slash alternatives, triun/(t)riun) stands in the stone's transliteration."""
        t = self.text.get(sig, "")
        return any(len(f) >= 1 and f in t for f in (compact(x) for x in form.split("/")))


# ---------------------------------------------------------------------------------------------------------------------
# signa
SIG_RE = None


def sig_regex(prefixes) -> re.Pattern:
    pre = sorted(set(prefixes) | set(PREFIX_FIX), key=len, reverse=True)
    body = (r"(?:[0-9IlO|!GSB]{1,5}[A-Za-z]?|[A-ZÅÄÖ][A-Za-zÅÄÖåäö]{0,9}[;:]?[0-9IlO]{1,5}(?:[;:/\-][0-9IlO]{1,6}){0,3}"
            r"[A-Za-z]?)")
    # flags may stand before a side letter (N413†A, Og8$A); a stray Q after the flag is OCR noise
    return re.compile(r"^(" + "|".join(re.escape(p) for p in pre) + r")" + r"(" + body + r")" + r"([$†+*tf#§]*)"
                      r"([A-F]?)Q?(?:\(\?\))?$")


def fix_digits(body: str) -> str:
    """Old-style figures: l/I/|/! read for 1, O for 0, G for 6, S for 5, B for 8 inside the number part."""
    tr = str.maketrans({"l": "1", "I": "1", "|": "1", "!": "1", "O": "0", "G": "6", "S": "5", "B": "8"})
    m = re.fullmatch(r"([0-9IlO|!GSB]+?)([A-F]?)", body)
    if m and (re.search(r"[0-9]", m.group(1)) or len(m.group(1)) >= 2):
        return m.group(1).translate(tr) + m.group(2)
    m = re.fullmatch(r"([A-ZÅÄÖ][A-Za-zÅÄÖåäö]*?[;:]?)([0-9IlO|]+(?:[;:/\-][0-9IlO|]+)*)([A-Za-z]?)", body)
    if m:
        return m.group(1) + m.group(2).translate(tr) + m.group(3)
    return body


def parse_signum(tok: str, rd: Rundata) -> dict | None:
    """One OCR token -> {'raw', 'pre', 'body', 'flags'} with the prefix and the number cleaned, or None."""
    global SIG_RE
    if SIG_RE is None:
        SIG_RE = sig_regex(rd.prefixes)
    t = tok.strip(".,;)/")
    m = SIG_RE.match(t)
    if not m:
        return None
    pre, body, flags, side = m.groups()
    if side and flags:
        body += side
    elif side:
        if body[-1] in "tfc" and body[-2:-1].isdigit():  # N413tA, ...168cA: the flag read as a small letter
            flags, body = ("$" if body[-1] == "c" else "†"), body[:-1] + side
        else:
            return None
    if not (re.search(r"[0-9]", body) or (len(body) >= 2 and re.search(r"[Il|!]", body))):
        return None  # Fl. (förled): a signum has a figure (an old-style 1 read l/I counts only in longer numbers)
    pre = PREFIX_FIX.get(pre, pre)
    if re.fullmatch(r"[0-9IlO|!]+[tfT]", body):  # † read as a letter after a plain number (Vgl26t = Vg126†)
        body, flags = body[:-1], "†" + flags
    flags = flags.replace("t", "†").replace("+", "†").replace("f", "†").replace("#", "$").replace("§", "$")
    return {"raw": tok, "pre": pre, "body": fix_digits(body), "flags": flags}


def signum_candidates(pre: str, body: str):
    """Near misses for an unknown signum, most plausible first: a flag read as a trailing figure (U5854 = U585$,
    2883 = 288$), one figure misread, one figure too many or too few."""
    m = re.fullmatch(r"(.*?)(\d+)([A-Za-z]?)", body)
    if not m:
        return
    stem, num, side = m.groups()
    seen = set()

    def out(n, why):
        s = pre + stem + n + side
        if n and not n.startswith("0") and s not in seen:
            seen.add(s)
            return s, why
        return None
    if len(num) >= 2:
        r = out(num[:-1], "sista siffran = flagga")
        if r:
            yield r
    if side:
        r = out(num, "sidbokstav")
        if r:
            yield (pre + stem + num, "sidbokstav")
    for i, c in enumerate(num):
        for d in "0123456789":
            if d != c:
                r = out(num[:i] + d + num[i + 1:], "en siffra")
                if r:
                    yield r
    for i in range(len(num)):
        r = out(num[:i] + num[i + 1:], "en siffra för mycket")
        if r:
            yield r


# ---------------------------------------------------------------------------------------------------------------------
# forms
FORM_CONF = [("p", "þ"), ("b", "þ"), ("P", "þ"), ("k", "R"), ("r", "R"), ("n", "R"), ("u", "R"), ("o", "ą"), ("a", "ą"),
             ("h", "þ"), ("þ", "p"), ("e", "æ"), ("ç", "þ"), ("I", "l"), ("í", "i"), ("|", "l"), ("i", "l"), ("l", "i")]


def form_variants(form: str):
    """OCR confusions in the bold sans-serif runic forms, fewest changes first: (l) read (D, þ read p (often in every þ
    of the form), ] read j or |, then one more single-letter confusion (ʀ read k/r, l read I ...)."""
    bases = [form]
    for a, b in (("(D", "(l)"), ("p", "þ"), ("j", ""), ("J", ""), ("b", "þ")):
        bases += [x.replace(a, b) for x in bases if a in x]
    seen = set()
    for base in bases:
        if base not in seen:
            seen.add(base)
            yield base
    for base in bases:
        for a, b in FORM_CONF:
            for i, c in enumerate(base):
                if c == a:
                    v = base[:i] + b + base[i + 1:]
                    if v not in seen:
                        seen.add(v)
                        yield v


def clean_form(f: str) -> str:
    f = f.strip(" .;:/")
    f = re.sub(r"^\(?(?:se|jfr)\b.*", "", f)
    return f.strip()


# ---------------------------------------------------------------------------------------------------------------------
# attestations
def strip_notes(s: str) -> str:
    """Remove parenthesised notes with a space or '?' in them ((se Sigriðr), (?), (läses ...)); keep (u) in forms."""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"/?\((?:[^()]*[\s?][^()]*)\)", " ", s)
    return s


def join_signa(s: str, rd: Rundata) -> str:
    s = re.sub(r"([;:/])\s+(?=\d)", r"\1", s)                 # DRAUD1999; 288$
    pre = "|".join(re.escape(p) for p in sorted(set(rd.prefixes) | set(PREFIX_FIX), key=len, reverse=True))
    s = re.sub(r"(?<![\w\]\)])(" + pre + r")([A-Z]{0,4})\s+(?=\d)", r"\1\2", s)  # DR 288, DRMNOR 2002;11b
    s = re.sub(r"([\])|])(?=(?:" + pre + r")[0-9lI])", r"\1 ", s)
    s = re.sub(r"(?<![\w\]\)])(DR|U|Sö|Ög|Vg|Sm|Öl|N|G)\s+(?=(?:EM85|NOR|AUD|Fv|FV|ATA|M\d|IK|KJ)[\w;:/]*\d)", r"\1", s)  # khu[nal-](r)Vs19: signum glued to the form
    return s


def attestations(text: str, rd: Rundata) -> list[dict]:
    """All (case, form, signum) items in an article text."""
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1-\2", text)
    text = re.sub(r"\s+", " ", text)
    out = []
    pieces = CASE_RE.split(text)
    # pieces: [before, case1, run1, case2, run2, ...]
    for ci in range(1, len(pieces) - 1, 2):
        case, run = pieces[ci].rstrip(".,:").replace("Kasus ovisst", "ovisst").capitalize(), pieces[ci + 1]
        m = STOP_RE.search(run)
        if m:
            run = run[:m.start()]
        run = join_signa(strip_notes(run), rd)
        form = None
        for item in run.split(","):
            toks = item.split()
            if not toks:
                continue
            # the signum is the last token that parses as one
            si = None
            for j in range(len(toks) - 1, -1, -1):
                if parse_signum(toks[j], rd):
                    si = j
                    break
            if si is None:
                continue
            ftoks = toks[:si]
            if ftoks:
                form = clean_form(" ".join(ftoks))
            if not form:
                continue
            ps = parse_signum(toks[si], rd)
            out.append({"case": case, "form": form, **ps, "uncertain": "(?)" in item})
    return out


def check(att: dict, rd: Rundata, correct: bool = True) -> dict:
    """Status of one attestation: ok / form_saknas / signum_saknas, with a correction if one is unique and verified.
    `rattat` = '' (as printed, after reading old-style figures), or a note on what was changed."""
    raw_sig = att["pre"] + att["body"]
    form = att["form"]
    sig = rd.lookup(raw_sig)
    res = {"signum": sig or "", "form_fix": form, "status": "", "rattat": ""}
    glyph = sigkey(raw_sig) != sigkey(re.sub(r"[$†+*(?)]", "", att["raw"]))
    if sig and rd.has_form(sig, form):
        res["status"] = "ok"
        if glyph:
            res["rattat"] = "tecken"
        return res
    if not correct:
        res["status"] = "form_saknas" if sig else "signum_saknas"
        return res
    # 1) the signum is right, the form has one OCR confusion
    if sig:
        fx = [v for v in form_variants(form) if v != form and rd.has_form(sig, v)]
        if fx and len(compact(form)) >= 3:
            res.update(status="ok", form_fix=fx[0], rattat="form")
            return res
    # 2) near-miss signum on which the form stands (unique)
    if len(compact(form)) >= 3:
        hits = []
        for cand, why in signum_candidates(att["pre"], att["body"]):
            s = rd.lookup(cand)
            if s and s != sig and rd.has_form(s, form):
                hits.append((s, why))
        if hits:
            best = [h for h in hits if h[1] in ("sista siffran = flagga", "sidbokstav")] or hits
            if len({h[0] for h in best}) == 1:
                res.update(status="ok", signum=best[0][0], rattat=f"signum {raw_sig} -> {best[0][0]} ({best[0][1]})")
                return res
    res["status"] = "form_saknas" if sig else "signum_saknas"
    return res


def borrow(att: dict, alt: list[dict], rd: Rundata, taken: set) -> dict | None:
    """A failed attestation in the main reading -> the verified attestation in another reading of the same page that
    is the same item (same case, form at least 60 % alike), if exactly one fits; `taken` holds (form, signum) pairs
    already verified in the main reading so an item is never counted twice."""
    from difflib import SequenceMatcher
    best = []
    for b in alt:
        if b["case"].lower() != att["case"].lower():
            continue
        cb = check(b, rd)
        if cb["status"] != "ok" or (compact(cb["form_fix"]), cb["signum"]) in taken:
            continue
        r = SequenceMatcher(None, compact(att["form"]), compact(cb["form_fix"])).ratio()
        same_sig = rd.lookup(att["pre"] + att["body"]) == cb["signum"] or (att["pre"] == b["pre"])
        if r >= 0.6 and same_sig:
            best.append((r, cb, b))
    best.sort(key=lambda x: -x[0])
    if not best or (len(best) > 1 and best[1][0] == best[0][0] and best[1][1]["signum"] != best[0][1]["signum"]):
        return None
    r, cb, b = best[0]
    return {**cb, "rattat": f"annan läsning: {b['form']} {b['raw']}"}


# ---------------------------------------------------------------------------------------------------------------------
# page text -> lines with indentation
def tsv_lines(path: str) -> list[dict]:
    """tesseract (or pdftotext -tsv) TSV -> [{'x': left, 'y': top, 'text': line}] in reading order (confident words
    only for x)."""
    rows = list(csv.reader(open(path, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
    lines = defaultdict(list)
    for r in rows[1:]:
        if len(r) < 12 or r[0] != "5" or not r[11].strip() or r[11].startswith("###"):
            continue
        lines[(int(r[2]), int(r[3]), int(r[4]))].append((float(r[6]), float(r[7]), float(r[10]), r[11]))
    out = []
    for k in sorted(lines, key=lambda k: min(w[1] for w in lines[k])):
        ws = sorted(lines[k])
        good = [w for w in ws if w[2] > 20 and re.search(r"\w", w[3])] or ws
        out.append({"x": good[0][0], "y": min(w[1] for w in ws), "text": " ".join(w[3] for w in ws)})
    return out


def textlayer_pages(pdf: str, first: int, last: int, cache: str) -> list[tuple[int, list[dict]]]:
    """The PDF's own text layer (ocrmypdf 2026-10-30) as lines with x in points (dpi 72), one TSV per page in cache."""
    os.makedirs(cache, exist_ok=True)
    out = []
    for p in range(first, last + 1):
        f = os.path.join(cache, f"p{p:03d}.tsv")
        if not os.path.exists(f):
            subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-tsv", pdf, f], check=True)
        out.append((p, tsv_lines(f)))
    return out


def align_entries(main: list[dict], alt: list[dict]) -> dict[int, dict]:
    """Pair the articles of two readings in book order by their headwords (stems); -> {index in main: alt entry}."""
    from difflib import SequenceMatcher
    a = [stem(headword_variants(e["headword"])[0]) if headword_variants(e["headword"]) else "" for e in main]
    b = [stem(headword_variants(e["headword"])[0]) if headword_variants(e["headword"]) else "" for e in alt]
    out = {}
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                if tag == "equal" or SequenceMatcher(None, a[i1 + k], b[j1 + k]).ratio() >= 0.6:
                    out[i1 + k] = alt[j1 + k]
    return out


HEAD_RE = re.compile(r"^(?P<hw>[^\s].{0,70}?)\s+(?P<g>mn|kvn|mansbinamn|kvinnobinamn|binamn)[.,:]?"
                     r"(?:\s+el\.\s+(?P<g2>mn|kvn)[.,]?)?(?P<rest>[?\s].*)?$")
GFIX = [(r"\bm[nm][.,:]?(?=\s|$)", "mn."), (r"\brn[.,]?(?=\s|$)", "mn."), (r"\bk[vy][nm][.,:]?(?=\s|$)", "kvn."),
        (r"\bkvrn[.,]?(?=\s|$)", "kvn."), (r"\bkv\.-binamn", "kvinnobinamn"), (r"\bm\.-binamn", "mansbinamn"),
        (r"(?<=[a-zðþæ])kvn\.$", " kvn."), (r"^[bp](?=[a-zæøðþ]+\s+(?:mn|kvn)\b)", "Þ")]


def head_match(text: str):
    t = text.strip()
    for a, b in GFIX:
        t = re.sub(a, b, t)
    m = HEAD_RE.match(t)
    if not m:
        return None
    hw = m.group("hw").strip()
    if not re.match(r"^[\[(“\"']?[A-ZÆØÞÅÄÖÁÉÍÓÚÝĀĒĪŌŪǪŒP]", hw) or len(hw) > 60 or "," in hw.split(" el. ")[0][-3:]:
        return None
    if re.match(r"^(Nom|Gen|Dat|Ack|Litt|Fda|Fsv|Fvn|Fl|E\.l|Se|Jfr|Sms|Anm)\b", hw):
        return None
    return m


def page_entries(pages: list[tuple[int, list[dict]]], dpi: int) -> list[dict]:
    """Split the running text into articles: a head line sits at the left margin, article lines are indented."""
    entries, cur = [], None
    for pno, lines in pages:
        lines = [ln for ln in lines if ln["text"].strip()]
        if not lines:
            continue
        # page number (running head) wherever tesseract put it
        lines = [ln for ln in lines if not re.fullmatch(r"[\dIlO|]{1,3}", ln["text"].strip())]
        if not lines:
            continue
        xs = sorted(ln["x"] for ln in lines)
        if not xs:
            continue
        x0 = xs[max(0, len(xs) // 20)]
        indent = 0.08 * dpi
        for ln in lines:
            t = ln["text"].strip()
            at_margin = ln["x"] < x0 + indent
            if at_margin and re.fullmatch(r"[A-ZÆØÞÅÄÖ]{1,2}|Lexikon.*", t):
                continue  # letter heading
            m = head_match(t) if at_margin else None
            if at_margin and m is None and (re.match(r"^-?[A-ZÆØÞÅÄÖÁĀ][^\s]*-$", t) or re.match(r"^-\S+", t)
                                            or re.search(r",\s*se\s", t)):
                if cur:
                    entries.append(cur)
                cur = None  # name element (Al-, -aðr m.) or cross-reference: not an entry
                continue
            if m:
                if cur:
                    entries.append(cur)
                cur = {"head": t, "headword": m.group("hw").strip(), "g": m.group("g"), "g2": m.group("g2") or "",
                       "rest": (m.group("rest") or "").strip(), "page": pno, "pages": {pno}, "lines": []}
                continue
            if cur is not None:
                cur["lines"].append(t)
                cur["pages"].add(pno)
    if cur:
        entries.append(cur)
    return entries


def headword_variants(hw: str) -> list[str]:
    hw = re.sub(r"\s*\((?:\?|\d)\)\s*", " ", hw).strip()
    parts = [p.strip() for p in re.split(r"\s*/\s*|\s+el\.\s+", hw)]
    out = []
    for i, p in enumerate(parts):
        lead = p.startswith(("-", "–"))
        p = p.strip("”\"*(-–?! []")
        if not p:
            continue
        if lead and out:  # Þorgisl/-gils: the tail replaces the end of the first form from its last matching letter
            first = out[0]
            j = first.rfind(p[0], 1)
            p = first[:j] + p if j > 0 else first + p
        out.append(p)
    # 'Heðin-/Hiðinfriða': the first part ends with a hyphen -> it takes the second form's tail (same-length first element)
    if len(parts) == 2 and parts[0].endswith("-") and len(out) == 2 and len(out[1]) > len(out[0]):
        out[0] = out[0] + out[1][len(out[0]):]
    # optional letters: Ar(i)nfastr -> Arinfastr and Arnfastr, Mun(d)gæirr -> Mundgæirr and Mungæirr
    full = []
    for v in out:
        if re.search(r"\([a-zæøþðåäö]{1,3}\)", v):
            full += [re.sub(r"\(([a-zæøþðåäö]{1,3})\)", r"\1", v), re.sub(r"\([a-zæøþðåäö]{1,3}\)", "", v)]
        else:
            full.append(v)
    return list(dict.fromkeys(full))


def fvn_form(lines: list[str]) -> str:
    for ln in lines[:4]:
        m = re.search(r"\b[Ff]vn\.\s+(?:binamn(?:et)?\s+|kvinnobinamn\s+|mansbinamn\s+)?([^,;()]+?)\s*(?:[,;(]|$)", ln)
        if m:
            return re.sub(r"^(?:mn|kvn)\.\s*", "", m.group(1).strip()).rstrip(".")
    return ""


GENDER = {"mn": "mn", "kvn": "kvn", "mansbinamn": "mn", "kvinnobinamn": "kvn", "binamn": ""}


def build_rows(entries: list[dict], rd: Rundata, alt: dict | None = None,
               alt_entries: dict | None = None) -> tuple[list[dict], list[dict]]:
    """Entries -> table rows (+ all attestations with their check). `alt_entries` maps an entry's index to the same
    article in another reading (align_entries); `alt` maps page -> attestations of another reading of that page and
    is used when an article has no partner. A failed attestation borrows the matching verified one from the other
    reading (borrow()); verified attestations that only the other reading has are added (rattat 'annan läsning,
    tillagd'), so a signum tesseract lost in one reading is not lost from the table."""
    rows, atts = [], []
    for idx, e in enumerate(entries):
        block = " ".join(e["lines"])
        hw, hw_note = fix_headword(e["headword"], rd)
        variants = headword_variants(hw)
        keys = set()
        for v in variants:
            keys.add(key(v))
            if re.match(r"^[Pp](?=[oöóiuyeæaåǫō])", v):  # Þ read as P
                keys.add(key("Þ" + v[1:]))
        keys.discard("")
        forms, fixed, signa = [], [], []
        if hw_note:
            fixed.append(hw_note)
        att = attestations(block, rd)
        checks = [check(a, rd) for a in att]
        taken = {(compact(c["form_fix"]), c["signum"]) for c in checks if c["status"] == "ok"}
        partner = (alt_entries or {}).get(idx)
        if partner is not None:
            pool = attestations(" ".join(partner["lines"]), rd)
        else:
            pool = [x for p in sorted(e.get("pages", {e["page"]})) for x in (alt or {}).get(p, [])]
        if partner is not None and not any(stem(v) in rd.name_stems for v in variants):
            hw2, note2 = fix_headword(partner["headword"], rd)
            v2 = headword_variants(hw2)
            if any(stem(v) in rd.name_stems for v in v2):  # the text layer read the headword better
                fixed.append(f"uppslagsord {hw} -> {hw2} (textlagret)")
                hw, variants = hw2, v2
                keys |= {key(v) for v in v2} - {""}
        for i, (a, c) in enumerate(zip(att, checks)):
            if c["status"] != "ok" and pool:
                b = borrow(a, pool, rd, taken)
                if b:
                    c = b
                    taken.add((compact(c["form_fix"]), c["signum"]))
            elif c["rattat"] == "form" and partner is not None:
                # the form was repaired by an OCR confusion: show the other reading's spelling if it stood as printed
                same = [b for b in pool if rd.lookup(b["pre"] + b["body"]) == c["signum"]
                        and rd.has_form(c["signum"], b["form"]) and compact(b["form"]) == compact(c["form_fix"])]
                if same:
                    c = {**c, "form_fix": same[0]["form"]}
            checks[i] = c
            a.update(c, headword=hw, page=e["page"])
        if partner is not None:  # verified items only the other reading has
            seen_sig = {c["signum"] or rd.lookup(a["pre"] + a["body"]) for a, c in zip(att, checks)}
            for b in pool:
                cb = check(b, rd)
                if cb["status"] == "ok" and (compact(cb["form_fix"]), cb["signum"]) not in taken \
                        and cb["signum"] not in seen_sig:
                    taken.add((compact(cb["form_fix"]), cb["signum"]))
                    b.update(cb, rattat=f"annan läsning, tillagd: {b['form']} {b['raw']}", headword=hw, page=e["page"])
                    att.append(b)
                    checks.append(b)
                    block += f" [ur textlagret: {b['form']} {b['raw']}]"
        new_block = block
        for a in att:
            c = a
            atts.append(a)
            if c["status"] == "ok":
                forms.append(f"{c['form_fix']}@{c['signum']}")
                signa.append(c["signum"])
                if c["rattat"] and c["rattat"] != "tecken":
                    fixed.append(f"{a['form']} {a['raw']} -> {c['form_fix']} {c['signum']}")
                # the verified signum goes back into the article text (tm22 reads signa from `block`)
                new_block = new_block.replace(a["raw"].rstrip(".,;/"), c["signum"].replace(" ", "") + a["flags"], 1)
        rows.append({"headword": hw, "variants": "|".join(variants), "keys": "|".join(sorted(keys)),
                     "gender": GENDER[e["g"]], "gender2": e["g2"], "fvn": fvn_form(e["lines"]),
                     "block": new_block[:1500], "page": e["page"] - 2, "kind": "binamn" if "binamn" in e["g"] else "namn",
                     "headword_ocr": e["headword"],
                     "n_belagg": len(att), "n_ok": sum(1 for a in att if a["status"] == "ok"),
                     "former": "|".join(forms), "signa": "|".join(sorted(set(signa), key=signa.index)),
                     "rattat": "|".join(fixed)})
    return rows, atts


# ---------------------------------------------------------------------------------------------------------------------
# measures
def measure_atts(atts: list[dict], rd: Rundata, correct: bool) -> dict:
    n = len(atts)
    res = [check(a, rd, correct=correct) for a in atts]
    sig = sum(1 for r in res if r["signum"])
    ok = sum(1 for r in res if r["status"] == "ok")
    return {"belagg": n, "signum_finns": sig, "form_pa_stenen": ok, "andel_ok": ok / n if n else 0.0,
            "rattade": sum(1 for r in res if r["rattat"].startswith(("signum", "form")))}


def name_match(rows: list[dict], rd: Rundata, stems: bool = True) -> tuple[int, int]:
    """Headwords one of whose variants is a Rundata name (same stem, any case form; stems=False: same exact key)."""
    def ok(r):
        vs = [v for v in r["variants"].split("|") if v] or [r["headword"]]
        return any((stem(v) in rd.name_stems) if stems else (key(v) in rd.name_keys) for v in vs)
    return sum(1 for r in rows if ok(r)), len(rows)


HW_CONF = [("k", "R"), ("p", "þ"), ("b", "þ"), ("P", "Þ"), ("T", "Þ"), ("T", "I"), ("B", "Þ"), ("n", "R"), ("g", "ǫ"),
           ("o", "ø"), ("O", "Ø"), ("e", "æ"), ("i", "l"), ("l", "i"), ("ii", "u"), ("z", "i"), ("t", "i")]


def fix_headword(hw: str, rd: Rundata) -> tuple[str, str]:
    """A headword whose stem is not a Rundata name: try one OCR confusion of the italic/small-capital type (ʀ read k,
    þ read p, ð read d, Þ read P); taken only if exactly one variant meets a Rundata name. -> (headword, note)."""
    note = ""
    g = re.sub(r"\((\w{1,3})j", r"(\1)", hw)                    # Full(hjugi: ')' read j in italics
    g = re.sub(r"(?<=[bB]i)g(?=rn)|(?<=Þi)g(?=kk)", "ǫ", g)          # Biǫrn, Þiǫkkr: ǫ read g
    if g != hw:
        note, hw = f"uppslagsord {hw} -> {g} (tecken)", g
    vs = headword_variants(hw)
    if not vs or any(stem(v) in rd.name_stems for v in vs):
        return hw, note
    v = vs[0]
    hits = set()
    for a, b in HW_CONF:
        i = v.find(a)
        while i >= 0:
            w = v[:i] + b + v[i + len(a):]
            if stem(w) in rd.name_stems:
                hits.add(w)
            i = v.find(a, i + 1)
    if len(hits) == 1:
        w = hits.pop()
        return hw.replace(v, w, 1), (note + "|" if note else "") + f"uppslagsord {v} -> {w}"
    return hw, note


def names_study_match(rows: list[dict]) -> tuple[int, int]:
    """The earlier measure (104/391): runestone names on >= 3 stones (utdata/overlevde/namn.csv) found in the lexicon."""
    path = os.path.join(ROOT, "utdata", "overlevde", "namn.csv")
    if not os.path.exists(path):
        return 0, 0
    lex = {k for r in rows for k in r["keys"].split("|")}
    ours = list(csv.DictReader(open(path, encoding="utf-8")))
    return sum(1 for r in ours if key(r["name"]) in lex), len(ours)


def text_of_page(src: str, page: int) -> str:
    if src.endswith(".pdf"):
        return subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), src, "-"], capture_output=True,
                              text=True).stdout
    return open(os.path.join(src, f"p{page:03d}.txt"), encoding="utf-8").read()


def compare_sample(srcs: list[str], pages: list[int], rd: Rundata) -> list[dict]:
    out = []
    for src in srcs:
        atts = []
        for p in pages:
            atts += attestations(text_of_page(src, p), rd)
        raw = measure_atts(atts, rd, correct=False)
        fix = measure_atts(atts, rd, correct=True)
        settings = ""
        sp = os.path.join(src, "settings.txt")
        if os.path.exists(sp):
            settings = open(sp).read().strip()
        out.append({"kalla": src, "inst": settings, "belagg": raw["belagg"], "signum_finns": raw["signum_finns"],
                    "ok_utan_rattning": raw["form_pa_stenen"], "ok_med_rattning": fix["form_pa_stenen"]})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ocr", help="katalog med pNNN.tsv från scripts/peterson_ocr.py")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--alt", nargs="*", default=[PDF],
                    help="andra läsningar (PDF med textlager eller katalog med pNNN.txt) att låna verifierade belägg ur")
    ap.add_argument("--first", type=int, default=FIRST_PAGE)
    ap.add_argument("--last", type=int, default=LAST_PAGE)
    ap.add_argument("--prov", nargs="*", help="jämför stickprov: kataloger med pNNN.txt eller PDF:er")
    ap.add_argument("--pages", default="")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--report", default="/Volumes/2TB/cache/peterson_ocr/kontroll.json")
    a = ap.parse_args(argv)
    rd = Rundata()
    if a.prov:
        import sys
        sys.path.insert(0, ROOT)
        from scripts.peterson_ocr import parse_pages
        for r in compare_sample(a.prov, parse_pages(a.pages), rd):
            n = r["belagg"] or 1
            print(f"{r['kalla'].split('/')[-1]:<40} {r['inst']:<48} belägg {r['belagg']:4d}  signum finns "
                  f"{r['signum_finns'] / n:6.1%}  form på stenen {r['ok_utan_rattning'] / n:6.1%}  med rättning "
                  f"{r['ok_med_rattning'] / n:6.1%}")
        return
    pages = []
    for p in range(a.first, a.last + 1):
        f = os.path.join(a.ocr, f"p{p:03d}.tsv")
        if os.path.exists(f):
            pages.append((p, tsv_lines(f)))
    entries = page_entries(pages, a.dpi)
    alt = defaultdict(list)
    for src in a.alt or []:
        for p, _ in pages:
            alt[p] += attestations(text_of_page(src, p), rd)
    alt_entries = {}
    if PDF in (a.alt or []):
        tl = textlayer_pages(PDF, a.first, a.last, os.path.join(CACHE, "textlager"))
        alt_entries = align_entries(entries, page_entries(tl, 72))
    rows, atts = build_rows(entries, rd, alt, alt_entries)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    fields = ["headword", "variants", "keys", "gender", "gender2", "fvn", "block", "page", "kind", "headword_ocr",
              "n_belagg", "n_ok", "former", "signa", "rattat"]
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    # measures before (old table) and after
    rep = {"sidor": len(pages)}
    for label, rws in (("fore", list(csv.DictReader(open(OLD, encoding="utf-8")))) if os.path.exists(OLD) else (),
                       ("efter", rows)):
        if label == "fore":
            oatts = [x for r in rws for x in attestations(r["block"], rd)]
            m_raw, m_fix = measure_atts(oatts, rd, correct=False), measure_atts(oatts, rd, correct=True)
            raw_rows = rws
        else:
            m_raw = measure_atts(atts, rd, correct=False)
            m_fix = {"form_pa_stenen": sum(1 for x in atts if x["status"] == "ok")}
            raw_rows = [{**r, "variants": "|".join(headword_variants(r["headword_ocr"]))} for r in rws]
        rep[label] = {"uppslag": len(rws), "kon": dict(Counter(r["gender"] for r in rws)),
                      "belagg": m_raw["belagg"], "signum_finns_utan_rattning": m_raw["signum_finns"],
                      "form_pa_stenen_utan_rattning": m_raw["form_pa_stenen"],
                      "form_pa_stenen_med_rattning": m_fix["form_pa_stenen"],
                      "uppslag_rundatanamn_stam": name_match(rws, rd)[0],
                      "uppslag_rundatanamn_stam_utan_uppslagsrattning": name_match(raw_rows, rd)[0],
                      "uppslag_rundatanamn_exakt_nyckel": name_match(rws, rd, stems=False)[0],
                      "runstensnamn_minst_3_stenar": list(names_study_match(rws))}
    rep["efter"]["signum_finns_med_rattning"] = sum(1 for x in atts if x["signum"])
    rep["efter"]["artiklar_parade_med_textlagret"] = len(alt_entries)
    rep["efter"]["rattade"] = dict(Counter(x["rattat"].split(" ")[0] if x["rattat"] else "inget" for x in atts))
    rep["efter"]["status"] = dict(Counter(x["status"] for x in atts))
    rep["signumrattelser"] = [f"{x['headword']}: {x['form']} {x['rattat']}" for x in atts
                              if x["rattat"].startswith("signum")]
    rep["kvarvarande_exempel"] = [{"uppslag": x["headword"], "s": x["page"] - 2, "form": x["form"], "signum": x["raw"],
                                  "status": x["status"], "rundata": x["signum"]}
                                 for x in atts if x["status"] != "ok"][:400]
    json.dump(rep, open(a.report, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k not in ("kvarvarande_exempel", "signumrattelser")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
