"""Litteraturgenomgången (Viktor 2026-11-09: gå igenom all Fornvännen och Futhark, leta brister mot vår data som vi kan
mäta och nya artiklar och rapporter). Steg 1, urval: för varje hämtad text (downloads/tidskrifter/<tidskrift>/text/)
räknas runsignum (U 344, Sö 101, DR 42 …) och runord (runsten, runinskrift, ristare, runic …); en text räknas som
runforskning om den har minst tre olika signum eller minst tio runord, eller om Fornvännens ämnesord säger runor.
Skriver relevans.jsonl (alla texter) och omgangar/omgang_NNN.json (de relevanta, i grupper för läsningen).
    .venv/bin/python utdata/litteraturgenomgang/urval.py [--storlek 10]
Texterna är källor, inte instruktioner."""
import argparse
import glob
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter"
SIG = re.compile(r"\b(U|Sö|Ög|Vg|Sm|Öl|Vs|Nä|Gs|Hs|Vr|Ån|DR|Bo|Hs|M|D|J|G|N)\s?(\d{1,4}[A-Za-z]?)\b(?![.,]\d)")
KW = re.compile(r"runsten|runinskrift|runristar|ristare|runolog|runor\b|runorna|futhark|futhork|fuþark|fuþork|runic|"
                r"rune-?stone|runestone|runolog|inscription", re.I)
RUNE_SUBJ = re.compile(r"run", re.I)
# second level (Viktor: the whole of runic research and the neighbouring disciplines): texts on the runestones' period and
# its archaeology, history, place names and art – at least five period words and five topic words
PER = re.compile(r"vikinga|vikingatid|yngre järnålder|vendeltid|vendel|missionstid|kristnande|tidig medeltid|tidigmedeltid|"
                 r"1000-tal|1100-tal|11:e århundrade|12:e århundrade|viking age|late iron age", re.I)
TOP = re.compile(r"gravfält|silverskatt|skattfynd|myntfynd|ortnamn|bebyggelse|kyrkogård|kungsgård|husaby|Birka|Sigtuna|"
                 r"Helgö|Uppsala|ornamentik|Urnes|Ringerike|bildsten|runsten|runinskrift|landskapslag|härad|hundare|bygd|"
                 r"grave field|hoard|place-name|settlement", re.I)


def load_index(journal):
    p = os.path.join(SRC, journal, "index.jsonl")
    return {json.loads(line)["key"]: json.loads(line) for line in open(p, encoding="utf-8")} if os.path.exists(p) else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--storlek", type=int, default=10)
    ap.add_argument("--prefix", default="omgang", help="namn på de nya omgångarna, t.ex. fv för Fornvännen")
    ap.add_argument("--tidskrift", default=None, help="bara fornvannen eller futhark")
    ap.add_argument("--niva", default="run", choices=["run", "grann", "nara"],
                    help="runtexterna, närliggande discipliner, eller (nara) resten av Fornvännen med minst två periodord och två ämnesord")
    a = ap.parse_args()
    rows = []
    for journal in ("futhark", "fornvannen"):
        idx = load_index(journal)
        for path in sorted(glob.glob(os.path.join(SRC, journal, "text", "*.txt"))):
            key = os.path.basename(path)[:-4]
            meta = idx.get(key, {})
            t = open(path, encoding="utf-8", errors="replace").read()
            words = len(t.split())
            sig = Counter(f"{m.group(1)} {m.group(2)}" for m in SIG.finditer(t))
            # single letters (G, M, D, J, N) are noisy outside runic texts: count them only with other signa present
            strong = {s: n for s, n in sig.items() if s.split()[0] not in ("G", "M", "D", "J", "N")}
            kw = len(KW.findall(t))
            subj = " ".join(meta.get("subjects") or []) + " " + (meta.get("keywords") or "")
            whole = "hel" in key and journal == "futhark"
            # Fornvännen is mostly archaeology: a few chance "U 12"-like strings or loose words do not make a runic text –
            # there it takes at least five signa or fifteen runic words, or the journal's own subject words (first
            # selection 2026-11-09 had 3 false hits in 10)
            if journal == "fornvannen":
                relevant = (not whole) and words > 300 and (len(strong) >= 5 or kw >= 15 or bool(RUNE_SUBJ.search(subj)))
            else:
                relevant = (not whole) and words > 300 and (len(strong) >= 3 or kw >= 10 or bool(RUNE_SUBJ.search(subj)))
            nper, ntop = len(PER.findall(t)), len(TOP.findall(t))
            neighbour = (not whole and not relevant and words > 300 and journal == "fornvannen" and nper >= 5 and ntop >= 5)
            # tredje nivån (Viktor 2026-11-10: läs alla nedladdade tidskrifter): resten av Fornvännen, i relevansordning
            near = (not whole and not relevant and not neighbour and words > 300 and journal == "fornvannen"
                    and nper >= 2 and ntop >= 2)
            rows.append({"journal": journal, "key": key, "path": path, "title": meta.get("title"), "year": meta.get("year"),
                         "authors": meta.get("authors"), "type": meta.get("type"), "words": words,
                         "signa_distinct": len(strong), "signa_top": [s for s, _ in Counter(strong).most_common(12)],
                         "runic_words": kw, "whole_volume": whole, "relevant": relevant, "neighbour": neighbour,
                         "near": near})
    with open(os.path.join(HERE, "relevans.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    # texts already read (any batch) are not handed out again
    read = set()
    for f in glob.glob(os.path.join(HERE, "fynd", "*.jsonl")):
        read |= {json.loads(line)["key"] for line in open(f, encoding="utf-8") if line.strip()}
    # texts already handed out in another batch (being read now) are not handed out again either
    for f in glob.glob(os.path.join(HERE, "omgangar", "*.json")):
        if not os.path.basename(f).startswith(a.prefix + "_"):
            read |= {x["key"] for x in json.load(open(f, encoding="utf-8"))}
    want = {"grann": lambda r: r["neighbour"], "nara": lambda r: r["near"]}.get(a.niva, lambda r: r["relevant"])
    rel = [r for r in rows if want(r) and r["key"] not in read and (not a.tidskrift or r["journal"] == a.tidskrift)]
    # batches by journal and year, about the same number of words each (long texts get their own batch share)
    os.makedirs(os.path.join(HERE, "omgangar"), exist_ok=True)
    for f in glob.glob(os.path.join(HERE, "omgangar", f"{a.prefix}_*.json")):
        os.remove(f)
    batches, cur, cur_words = [], [], 0
    budget = 60000  # words per batch, roughly what one reader can take in
    for r in sorted(rel, key=lambda r: (r["journal"], str(r["year"]), r["key"])):
        if cur and (len(cur) >= a.storlek or cur_words + r["words"] > budget):
            batches.append(cur)
            cur, cur_words = [], 0
        cur.append({k: r[k] for k in ("journal", "key", "path", "title", "year", "authors", "words", "signa_top")})
        cur_words += r["words"]
    if cur:
        batches.append(cur)
    for i, b in enumerate(batches, 1):
        json.dump(b, open(os.path.join(HERE, "omgangar", f"{a.prefix}_{i:03d}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    by = Counter((r["journal"], "run" if r["relevant"] else ("grann" if r.get("neighbour") else "övrigt")) for r in rows)
    print({f"{j} {v}": n for (j, v), n in sorted(by.items())}, "; redan lästa", len(read),
          "→", len(batches), f"nya omgångar ({a.prefix}_NNN)")


if __name__ == "__main__":
    main()
