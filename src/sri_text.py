"""Sveriges runinskrifter (RAÄ:s digitala utgåva) som text per sten, och ornament- och runformsdragen ur den fasta
ordlistan i den låsta planen analysplaner/2026-11-04-attribuering-v4-ornamentik.md.

Volymerna (textdelarna) laddas ned och görs till text med pdftotext -layout i SRI_DIR. En artikel börjar på en
centrerad rubrikrad "N. Ortnamn …" och räcker till nästa; numren ska stiga (falska träffar i löptexten sållas bort så).
Landskapets förkortning kommer ur filnamnet.

    .venv/bin/python -m src.sri_text KORPUSMAPP UT.csv     (dragen per sten för attribueringsmodellen)
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

SRI_DIR = os.environ.get("SRI_DIR", "/Volumes/2TB/Antigrvity/Runes/downloads/sri")
PROVINCE = {"gastrikland": "Gs", "narke": "Nä", "oland": "Öl", "ostergotland": "Ög", "smaland": "Sm",
            "sodermanland": "Sö", "uppland": "U", "vastergotland": "Vg", "vastmanland": "Vs", "halsingland": "Hs",
            "medelpad": "M", "angermanland": "Ån", "dalarna": "D", "varmland": "Vr", "bohuslan": "Bo", "jamtland": "J"}
HEADING = re.compile(r"^\s{8,}(\d{1,4})\s?\.\s+([A-ZÅÄÖÆØ][^\n]{2,90})$")
MIN_ARTICLES = 15

# The vocabulary of the locked plan: name -> regular expression on the cleaned text (lower case, spaced words joined)
VOCAB = {
    # ornament
    "fagelperspektiv": r"fågelperspektiv", "i_profil": r"\bi profil", "rundjur": r"rundjur", "fyrfota": r"fyrfot",
    "drake": r"\bdrak(e|en|ar|huvud)", "ormhuvud": r"ormhuvud", "ormslinga": r"ormsling", "tva_ormar": r"\btvå ormar",
    "tre_ormar": r"\btre ormar", "svans": r"\bsvans", "flik": r"\bflik", "upprullad": r"upprullad", "spiral": r"spiral",
    "ogla": r"\bögl(a|or|an)", "koppel": r"\bkoppel|sammanbindande band|sammanbinda", "tvarband": r"tvärband|bindband",
    "ringkors": r"ringkors", "korsband": r"korsband", "rak_runslinga": r"rak runsling|raka runsling",
    "ramlinje": r"ramlinje", "dubbelkontur": r"dubbelkontur|dubbel kontur", "skuggning": r"skuggning|streckfyll",
    "fyllnadsornament": r"fyllnadsornament", "mask": r"\bmask\b|masken", "fotter": r"\bfötter|\bben\b|\bbenen",
    "nos": r"\bnos", "lappflik": r"läppflik", "nackflik": r"nackflik|nacktofs", "oga": r"\böga|\bögat",
    "ryttare": r"ryttare", "skepp": r"\bskepp", "fagel": r"\bfågel(?!perspektiv)", "bildfalt": r"bildfält",
    "urnes": r"urnes", "ringerike": r"ringerike", "bandornamentik": r"bandornament",
    # rune forms and writing
    "kortkvist": r"kortkvist", "langkvist": r"långkvist", "stavlosa": r"stavlös", "stungen": r"stungen|stungna",
    "bindruna": r"bindrun", "spegelvand": r"spegelvänd", "vandruna": r"vändrun", "ensidig_bistav": r"ensidig bistav|ensidiga bistav",
    "dubbelsidig_bistav": r"dubbelsidig bistav|dubbelsidiga bistav", "skiljetecken": r"skiljetecken",
    "kryss_skilj": r"kryss", "punkt_skilj": r"\bpunkt", "lonnrunor": r"lönnrun",
}
VOCAB_RE = {k: re.compile(v) for k, v in VOCAB.items()}
RUNE_HEIGHT = re.compile(r"runornas höjd (?:är |varierar mellan |utgör )?(?:omkr\. |ca |c:a )?(\d{1,2}(?:[,.]\d)?)")


def clean(text: str) -> str:
    t = text.replace("­", "").replace("ı", "i")
    t = re.sub(r"-\s*\n\s*", "", t)                      # hyphenation at line ends
    t = re.sub(r"\b(?:[a-zåäöA-ZÅÄÖ] ){2,}[a-zåäöA-ZÅÄÖ]\b", lambda m: m.group(0).replace(" ", ""), t)  # spaced words
    return re.sub(r"\s+", " ", t).lower()


def articles() -> dict[str, str]:
    """Signum -> the article text (cleaned), from all volumes in SRI_DIR."""
    out: dict[str, list[str]] = defaultdict(list)
    for path in sorted(glob.glob(os.path.join(SRI_DIR, "sri_*_text*.txt")) + glob.glob(os.path.join(SRI_DIR, "sri_oland_*.txt"))):
        name = os.path.basename(path)
        prov = next((v for k, v in PROVINCE.items() if f"sri_{k}_" in name), None)
        if not prov:
            continue
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        cur, buf = None, []
        last = 0
        for ln in lines:
            m = HEADING.match(ln)
            if m:
                n = int(m.group(1))
                # A volume part may begin anywhere in the series (Uppland 7 begins at U 295): the first heading of a file
                # is taken when it is well indented (centred), after that the numbers must rise
                indent = len(ln) - len(ln.lstrip())
                if (cur is None and indent >= 15) or (cur is not None and last < n <= last + 40):
                    if cur:
                        out[cur].append("\n".join(buf))
                    cur, buf, last = f"{prov} {n}", [ln], n
                    continue
            if cur:
                buf.append(ln)
        if cur:
            out[cur].append("\n".join(buf))
    return {k: clean("\n".join(v)) for k, v in out.items()}


def features(text: str) -> dict[str, int | float | None]:
    f: dict[str, int | float | None] = {k: int(bool(r.search(text))) for k, r in VOCAB_RE.items()}
    m = RUNE_HEIGHT.search(text)
    f["runhojd_over_10"] = (1 if float(m.group(1).replace(",", ".")) > 10 else 0) if m else None
    return f


def main(corpus_dir: str, out: str) -> None:
    csv.field_size_limit(10 ** 9)
    signa = [r["signum"] for r in csv.DictReader(open(os.path.join(corpus_dir, "corpus.csv"), encoding="utf-8"))]
    arts = articles()
    have = {s: features(arts[s]) for s in signa if s in arts}
    counts = Counter(k for f in have.values() for k, v in f.items() if v == 1)
    keep = [k for k in list(VOCAB) + ["runhojd_over_10"] if counts[k] >= MIN_ARTICLES]
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["signum", "sri_artikel"] + [f"sri_{k}" for k in keep])
        for s in signa:
            f = have.get(s)
            w.writerow([s, "1" if f else "0"] + [("" if f is None or f.get(k) is None else str(f[k])) for k in keep])
    print(out, f"{len(have)} av {len(signa)} stenar har en SRI-artikel; {len(keep)} drag:", ", ".join(keep))
    json.dump({k: counts[k] for k in list(VOCAB) + ["runhojd_over_10"]}, open(out.replace(".csv", "_antal.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
