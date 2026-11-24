"""Ornamentik steg 1, utvidgning: SRI-planschsidor för Gotland (G) och Öland (Öl).

Samma mål som planscher.py – {signum: [[pdf, sida], ...]} – men de två landskapen kräver egen logik:

Gotland (SRI XI–XII, planschband downloads/sri_plansch/sri_gotland_*):
  * Bildtexterna har oftast signum ("G 151. Norrlanda kyrka"), ibland bara ortnamn ("Drakarve, Näs sn").
  * Varje band börjar med en förteckning (i nummerföljd och alfabetisk) med kolumnerna Nr / Sid. / Pl.
    Den läses med ordkoordinater (pdftotext -bbox) så att Pl.-kolumnen skiljs från sidkolumnen.
  * Planschsidorna bär "Pl. N"; sidnummer = planschnummer + konstant förskjutning per PDF (skattas ur de läsbara
    "Pl. N"-raderna och kontrolleras).
  * En sida tas med om bildtexten nämner stenen, eller om förteckningen pekar på planschen och sidans text
    innehåller förteckningens ortnamn (fångar bildtexter där OCR tappat signum). Oenigheter skrivs ut.
  * Bara de 42 stenar som arbetet gäller (GOTLAND nedan). G 223 och högre ingår inte i SRI XI–XII.

Öland (SRI I, Ölands runinskrifter 1900–1906, downloads/sri/sri_oland_b01_h01/h02.pdf – inget separat planschband):
  * Inskrifterna är numrerade 1–60 och "citeras Öl. 1–60" (innehållsförteckningen), alltså SRI nr N = Öl N.
  * Artikelrubriken följs av en rad "Pl. VI. Fig. 5." Figurnumret är detsamma som artikelnumret.
  * Planscherna är etsningar/teckningar inbundna mellan textsidorna: bildsidor med nästan inget textlager.
    De numreras i ordning I, II, … över båda häftena (h01 = I–XVII, h02 = XVIII–XXXVIII). Planscherna XXXIII–XXXVIII
    är avbildningar ur Bautil (figur 58–70) vars figurnummer INTE är stennummer; de används inte.
  * Öl 58–60 och alla senare fynd (Köping-fragmenten, ATA-nummer m.fl.) har ingen plansch i SRI.
  * Många figurer är kopior av 1600–1700-talsteckningar av förlorade stenar (Rhezelius, Bautil), inte avbildningar
    av bevarade stenar; se rapporten och verifieringen.

Planscherna (RAÄ, Digitala Sveriges runinskrifter) är upphovsrättsligt skyddade: de läses och räknas bara, och både PDF:erna
och de renderade sidorna ligger utanför git (downloads/ och data/cache/hander/plansch).

    .venv/bin/python utdata/nya_ristare/ornamentik/planscher_utvidgning.py [--render]
Skriver data/cache/hander/plansch/sidor_utvidgning.json  {signum: [[pdf, sida], ...]} (sidor.json lämnas orörd);
med --render även img300/<pdf>_p<sida>.jpg (300 dpi, en pdftoppm i taget).
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.belagg import load  # noqa: E402

DL = "/Volumes/2TB/Antigrvity/Runes/downloads"
G_PDF = [os.path.join(DL, "sri_plansch", f"sri_gotland_{s}.pdf")
         for s in ("b11_d01_plansch", "b12_d02_plansch_1", "b12_d02_plansch_2")]
OL_PDF = [os.path.join(DL, "sri", f"sri_oland_b01_{h}.pdf") for h in ("h01", "h02")]
OUT = os.path.join(ROOT, "data", "cache", "hander", "plansch")

GOTLAND = [37, 41, 72, 80, 94, 96, 111, 112, 113, 116, 117, 134, 135, 136, 138, 141, 186, 187, 188, 189, 193, 200,
           203, 207, 208, 218, 219, 220, 227, 228, 266, 270, 272, 276, 280, 300, 309, 325, 342, 368, 370, 373]
FIX = str.maketrans({"l": "1", "I": "1", "i": "1", "O": "0", "o": "0", "S": "5", "B": "8"})
ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50}


def npages(pdf):
    return int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))


def page_text(pdf, p):
    return subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), pdf, "-"], capture_output=True,
                          text=True).stdout


def page_words(pdf, p):
    """Ord med koordinater: [(x, y, ord)]."""
    xml = subprocess.run(["pdftotext", "-bbox", "-f", str(p), "-l", str(p), pdf, "-"], capture_output=True,
                         text=True).stdout
    return [(float(x), float(y), w) for x, y, w in
            re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="[\d.]+" yMax="[\d.]+">(.*?)</word>', xml)]


def squash(s):
    return re.sub(r"\s+", "", s).lower()


def num(s):
    s = s.replace(" ", "").translate(FIX)
    return int(s) if s.isdigit() else None


# ---------------------------------------------------------------- Gotland

CAPTION = re.compile(r"(?<![A-Za-zÅÄÖåäö])G\s?([0-9lIOi][0-9lIOi ]{0,4}?)(?:\s?:\s?[a-zA-Z][a-z0-9 ,\-]{0,8})?"
                     r"(?:\s?(?:och|[—–-])\s?G?\s?([0-9lIOi]{1,4}))?\s*(?=[.,:]|\soch\b|\ssamt\b)")
PLATE_MARK = re.compile(r"P\s?l\s?\.\s?:?\s?(\d[\d ]{0,3})")


def captions(txt):
    """Signum som nämns i bildtexterna på en planschsida ("G 144 och 145", "G 195-196", "G i l l" = 111)."""
    out = set()
    for m in CAPTION.finditer(txt):
        a = num(m.group(1))
        if a is None:
            continue
        out.add(a)
        b = num(m.group(2)) if m.group(2) else None
        if b and 0 < b - a <= 5:
            out.update(range(a + 1, b + 1))
    return out


def parse_index(pdf, p):
    """Förteckningssida -> {nr: (planscher, ortnamn)}; tvåspaltig, kolumnerna avgränsas med rubrikordens x-läge."""
    words = page_words(pdf, p)
    sid = [(x, y) for x, y, w in words if w.startswith("Sid") and y < 160]
    if len(sid) != 2:
        return {}
    y_head = min(y for x, y in sid)
    on_head = [(x, w) for x, y, w in words if abs(y - y_head) < 5]   # rubrikraden Nr / Sid. / Pl. (två spalter)
    sid_x = sorted(x for x, y in sid)
    pl_x = sorted(x for x, w in on_head if w.startswith("Pl"))
    nr_x = sorted(x for x, w in on_head if w == "Nr")
    if len(pl_x) != 2:
        return {}
    split = nr_x[1] - 5 if len(nr_x) == 2 else pl_x[0] + 30
    res = {}
    for col, (lo, hi) in enumerate(((0, split), (split, 1e9))):
        cw = [w for w in words if lo <= w[0] < hi and w[1] > y_head + 5]
        lines = []
        for x, y, w in sorted(cw, key=lambda t: (t[1], t[0])):
            if lines and abs(lines[-1][0] - y) < 4:
                lines[-1][1].append((x, w))
            else:
                lines.append([y, [(x, w)]])
        cur = None
        for y, ws in lines:
            ws.sort()
            sid_lo, pl_lo = sid_x[col] - 22, pl_x[col] - 8
            name = " ".join(w for x, w in ws if x < sid_lo)
            pl = " ".join(w for x, w in ws if x >= pl_lo)
            # nummer (OCR: "2 1", "I l l" = 111) följt av ortnamn med versal + gemen ("I I I ) ." är ingen ny post)
            m = re.match(r"^((?:[0-9IlO]\s?){1,3})\s+(?=[A-ZÅÄÖÜ]\s?[a-zåäöü])", name + " ")
            if m and num(m.group(1)) and num(m.group(1)) <= 400 and len(name) > len(m.group(0)) + 1:
                cur = num(m.group(1))
                res.setdefault(cur, [set(), name[m.end():]])
            elif name.lstrip().startswith(("—", "-", "–")):
                cur = None
            if cur is not None and pl:
                s = re.sub(r"(?<=\d) (?=\d)", "", pl.replace("—", "-").replace("–", "-"))
                s = re.sub(r"\s*-\s*", "-", s)
                for a, b in re.findall(r"(\d{1,3})(?:-(\d{1,3}))?", s):
                    a = int(a)
                    b = int(b) if b else a
                    if 0 < b - a <= 10:
                        res[cur][0].update(range(a, b + 1))
                    else:
                        res[cur][0].add(a)
    return res


def gotland():
    targets = set(GOTLAND)
    pages = defaultdict(list)
    index = defaultdict(lambda: defaultdict(lambda: [set(), ""]))    # band -> nr -> (planscher, ortnamn)
    files = []
    for pdf in G_PDF:
        stem = os.path.basename(pdf)[:-4]
        band = stem.split("_")[2]                                       # b11 / b12 (b12 delad på två PDF:er)
        n = npages(pdf)
        txt = {p: page_text(pdf, p) for p in range(1, n + 1)}
        # förteckningssidor (nummerföljd och alfabetisk): rubrikrad med Sid. och Pl.
        idx_pages = [p for p in txt if re.search(r"Sid\..*Pl", txt[p]) and "FÖRTECKNING" in txt[p].upper().replace(" ", "")]
        for p in idx_pages:
            for k, (pls, name) in parse_index(pdf, p).items():
                index[band][k][0].update(pls)
                index[band][k][1] = index[band][k][1] or name
        # förskjutning sida - plansch ur läsbara "Pl. N"
        offs = Counter()
        for p, t in txt.items():
            for m in PLATE_MARK.finditer(t[:400]):
                k = num(m.group(1))
                if k:
                    offs[p - k] += 1
        off, hits = offs.most_common(1)[0]
        first = max(idx_pages) + 1 if idx_pages else 1
        plate_of = {p: p - off for p in range(first, n + 1) if p - off >= 1}
        print(f"{stem}: {n} sidor, förteckning s. {idx_pages}, sida = plansch + {off} ({hits} av {sum(offs.values())} "
              f"läsbara Pl.-märken stämmer), planscher {min(plate_of.values())}–{max(plate_of.values())}")
        files.append((stem, band, txt, plate_of, {p: captions(txt[p]) for p in plate_of}))
    for g in sorted(targets):
        band = "b11" if g <= 137 else "b12"
        pls, name = index[band].get(g, [set(), ""])
        place = squash(re.split(r"[,.]", name)[0])[:8] if name else ""
        found, how = set(), {}
        for stem, b, txt, plate_of, cap in files:
            if b != band:
                continue
            for p, cs in cap.items():
                if g in cs:
                    found.add((stem, p))
                    how[(stem, p)] = "bildtext" + ("+förteckning" if plate_of[p] in pls else " (ej i förteckningen)")
            for p, pl in plate_of.items():
                if pl not in pls or (stem, p) in found:
                    continue
                if place and place in squash(txt[p]):
                    found.add((stem, p))
                    how[(stem, p)] = "förteckning+ortnamn"
                else:
                    print(f"  G {g}: förteckningen anger pl. {pl} ({stem} s. {p}) men varken signum eller '{place}' "
                          f"på sidan – utelämnas")
        if g > 222:
            continue
        got = ", ".join(f"{st[-9:]} s. {p} [{how[(st, p)]}]" for st, p in sorted(found)) or "–"
        print(f"  G {g} ({name.strip()[:30]}): pl. {sorted(pls) or '– (ingen plansch)'} -> {got}")
        for stem, p in sorted(found):
            pages[f"G {g}"].append([stem, p])
    return pages


# ---------------------------------------------------------------- Öland

def roman(s):
    s = s.upper().translate(str.maketrans({"Y": "V", "1": "I", "L": "I"}))  # OCR: "Yll" = VII; L förekommer inte < 50
    if not s or any(c not in ROMAN for c in s):
        return None
    v = 0
    for a, b in zip(s, s[1:] + " "):
        v += -ROMAN[a] if b != " " and ROMAN[b] > ROMAN[a] else ROMAN[a]
    return v


def oland(known):
    plates, articles = [], {}
    for pdf in OL_PDF:
        stem = os.path.basename(pdf)[:-4]
        n = npages(pdf)
        txt = {p: page_text(pdf, p) for p in range(1, n + 1)}
        words = {p: len(t.split()) for p, t in txt.items()}
        body = min(p for p in txt if words[p] >= 300)            # första egentliga textsida
        end = min(p for p in txt if p > body and "INNEHÅLL" in txt[p])
        # planschsidor: bildsidor utan löptext före innehållsförteckningen; före första textsidan bara sidor med
        # någon bildtext som inte är titelblad (h02 s. 4 = pl. XVIII; tomma blad och titelblad hoppas över)
        own = [p for p in range(1, body) if 0 < words[p] < 80 and "RUNINSKRIFT" not in txt[p].upper().replace(" ", "")
               and "UTGIFNA" not in txt[p]]
        own += [p for p in range(body, end) if words[p] < 80]
        for p in own:
            plates.append((stem, p, txt[p]))
        # artikelrubriker "N. Ort." (ev. "N och M. Ort.") följda av "Pl. …"-rad
        for p in range(body, end):
            lines = [l for l in txt[p].splitlines() if l.strip()]
            for i, l in enumerate(lines):
                m = re.match(r"^\s{8,}([\dIl]\s?\d?)\s*(?:o\s?c\s?h\s*(\d\s?\d?))?\s?\.\s+[A-ZÅÄÖ]\s?[a-zåäö]", l)
                if not m:
                    continue
                # "Pl."-raden följer direkt, ibland efter en rad OCR-skräp ("I. Karlevi" = 1, "P l . XII.")
                pl = next((x for x in lines[i + 1:i + 3] if re.search(r"P\s?[lI1]\s?\.", x)), None)
                if pl is None:
                    continue
                nums = [num(m.group(1))] + ([num(m.group(2))] if m.group(2) else [])
                romans = []
                for a, b in re.findall(r"P\s?[lI1]\s?\.\s?([IVXYl1]+)\.?(?:\s?[—–-]\s?([IVXYl1]+))?", pl):
                    a, b = roman(a), roman(b) if b else None
                    if a:
                        romans += list(range(a, b + 1)) if b and b > a else [a]
                if len(nums) == 2 and len(romans) == 2:   # "3 och 4 … Pl. IV. Nr 3. — Pl. V." / "26 och 27 … Pl. XVI och Pl. XVII"
                    pairs = list(zip(nums, [[r] for r in romans]))
                else:
                    pairs = [(k, romans) for k in nums]
                for k, rs in pairs:
                    if k and rs and k not in articles:
                        articles[k] = rs
        print(f"{stem}: {n} sidor, text från s. {body}, innehåll s. {end}, {len(own)} planschsidor: {own}")
    plate_page = {}
    agree = disagree = 0
    for i, (stem, p, t) in enumerate(plates, start=1):
        plate_page[i] = (stem, p)
        seen = [roman(w.strip(".,")) for w in t.split() if re.fullmatch(r"[IVXY1l]{2,6}\.?", w.strip())]
        seen = [r for r in seen if r]
        if i in seen:
            agree += 1
        elif seen:
            disagree += 1
            print(f"  plansch {i} = {stem} s. {p}: OCR visar {seen} (inte {i})")
    print(f"Öland: {len(plates)} planscher; tryckt romersk siffra läsbar och lika på {agree}, olika på {disagree}")
    if len(plates) < 32 or plate_page[18][0] != "sri_oland_b01_h02":
        raise SystemExit("planschräkningen stämmer inte (väntat I–XVII i h01, XVIII– i h02) – kontrollera")
    pages = defaultdict(list)
    for k in sorted(articles):
        s = f"Öl {k}"
        if k > 57 or any(r > 32 for r in articles[k]):     # XXXIII– = Bautilkopior, fig. 58–70 ≠ Öl 58–70
            continue
        print(f"  {s}: pl. {articles[k]} -> {[plate_page[r] for r in articles[k]]}{'' if s in known else ' (ej i korpus)'}")
        if s in known:
            pages[s] = [list(plate_page[r]) for r in articles[k]]
    return pages


def main(render):
    known = set(load().sig)
    pages = gotland()
    pages.update(oland(known))
    os.makedirs(os.path.join(OUT, "img300"), exist_ok=True)
    json.dump(dict(sorted(pages.items())), open(os.path.join(OUT, "sidor_utvidgning.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
    ol = [s for s in known if s.startswith("Öl ")]
    print(f"G: {sum(s.startswith('G ') for s in pages)} av {len(GOTLAND)}; Öl: {sum(s.startswith('Öl ') for s in pages)} "
          f"av {len(ol)} med minst en planschsida")
    if render:
        src = {os.path.basename(p)[:-4]: p for p in G_PDF + OL_PDF}
        need = sorted({tuple(x) for v in pages.values() for x in v})
        for stem, p in need:
            f = os.path.join(OUT, "img300", f"{stem}_p{p:04d}")
            if not os.path.exists(f + ".jpg"):
                subprocess.run(["pdftoppm", "-r", "300", "-jpeg", "-jpegopt", "quality=85", "-singlefile", "-f", str(p),
                                "-l", str(p), src[stem], f], check=True, stderr=subprocess.DEVNULL)
        print(len(need), "sidor renderade")


if __name__ == "__main__":
    main("--render" in sys.argv)
