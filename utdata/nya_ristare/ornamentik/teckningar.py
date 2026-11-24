"""Ornamentik: äldre teckningar (1600- och 1700-tal) av runstenarna, framför allt de förlorade, så att ornamentiken
(rundjurets huvud, öga, flikar, svans, ögla, kors) kan kodas också där stenen inte finns kvar. Kvarvarande stenar med en
gammal teckning märks också, för källkontrollen teckning mot modernt planschfoto av samma sten.

Tre källor:
  1. SRI-textbanden (RAÄ, Digitala Sveriges runinskrifter): artiklarna återger ofta den gamla teckningen som figur i
     texten ("Fig. 198. U 204. Ångarns kyrka. Efter teckning av Rhezelius."). Bildtexterna läses ur textlagret med
     koordinater (pdftotext -bbox); figuren beskärs ovanför bildtexten. Textbanden är upphovsrättsligt skyddade: de läses
     och räknas bara, och de beskurna bilderna ligger utanför git.
  2. Bautil (Johan Göransson, Stockholm 1750; 1 173 träsnitt efter Hadorphs, Peringskiölds, Leitz', Törnevalls m.fl.
     teckningar). Umeå universitetsbiblioteks exemplar i Digitala samlingar (urn:17a_000068, LIBRIS 10936379), "fritt från
     kända upphovsrättsliga restriktioner"; sidbilderna (ca 300 dpi) ligger i downloads/bautil_umu. Signum -> B-nummer
     tas ur SRI-artiklarna ("Litteratur: B. 1145"), B-nummer -> sida ur sidornas tryckta "N:o"-rubriker (tesseract)
     med stigande nummer som kontroll; varje B-nummer på en sida beskärs ut ur sidan med träsnittens ramar.
  3. Planschsidor som själva är gamla teckningar (Sö 1924 efter Bautil, Ög och Öl efter B.-nummer): listas under
     "_plansch_ar_teckning", inga nya bilder.

    .venv/bin/python utdata/nya_ristare/ornamentik/teckningar.py [--render]
Skriver data/cache/hander/plansch/teckningar.json; med --render även bilderna i data/cache/hander/plansch/teckningar/.
"""
import glob
import html
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.belagg import load  # noqa: E402
from src.sri_text import HEADING, PROVINCE  # noqa: E402

SRI = "/Volumes/2TB/Antigrvity/Runes/downloads/sri"
OUT = os.path.join(ROOT, "data", "cache", "hander", "plansch")
IMG = os.path.join(OUT, "teckningar")
DPI = 300

# Signumprefix i bildtexterna (OCR skriver ibland "Sm." och sätter mellanslag i siffrorna)
SIG = re.compile(r"(?<![a-zåäö])(u|sö|ög|öl|sm|vg|vs|nä|gs|vr|hs|m|g)\.?(\d{1,4})([a-c]?)(?=[.,:;(]|och|$)")
FIGSTART = re.compile(r"^[fe]i[gq]\.?\d")
# Bildtexter som anger en avbildning och inte ett foto, en karta eller en plan
DRAWING = re.compile(r"teckning|träsnitt|kopparstick|uppteckning|ritning|avtecknad|avbildning|lavering|litografi|"
                     r"monumenta|bautil|ransakning|collectanea|efterb\.?\d|\(b\.?\d|efterkopia|gravyr|stick")
NOT_DRAWING = re.compile(r"foto|karta|planskiss|\bplan\b|kartblad|fyndplats")

# Tecknare/källa -> (källa, sekel). Ordningen spelar roll: den första träffen vinner.
UPPHOV = [
    # OCR läser Rhezelius som Ehezelius, Bhezelius, ßhezelius, Kbezelius, Rliezelius ...; hans handskrifter F a 10:1, F l 1–2
    (r"[hb]e[zs]eli|liezeli|iihezel|lihezel|fa10:1|\(fl[12]\)|ifl[12]\b|fm18|ifc6", "Rhezelius", "Rhezelius", 1600),
    (r"hadorph", "Hadorph", "Hadorph", 1600),
    (r"helgon", "annan", "Helgonius", 1600),
    # Peringskiöld (OCR: Feringskiöld, PeriDgskiöld, Beringskiöld); Monumenta Sveo-Gothica är hans; handskriften F l 5
    (r"[pfb]eri[nd]g-?sk|peringskicld|monumentasveo|sveo-?gothica|if15:|ifl5:", "Peringskiöld", "Peringskiöld", 1600),
    (r"bautil|efterb\.?\d|\(b\.?\d|träsnittb\d", "Bautil", None, 1700),
    # Bureus (OCR: Burens, Bureas, Bnreus, Biireus, Kureus); hans kopparstick i F f 6
    (r"b[uün]r[eu][nu]s|bureas|biireus|b[uü]reu|kureus|ff6", "annan", "Bureus", 1600),
    (r"[aâ]s[ce][hb]aneus|aschane", "annan", "Aschaneus", 1600),
    (r"leitz|leits", "annan", "Leitz", 1600),
    (r"christof|christoph", "annan", "Christofersson", 1600),
    (r"brenner", "annan", "Brenner", 1600),
    (r"ransakning|petrusberg", "annan", "Ransakningarna", 1600),
    (r"axehielm", "annan", "Axehielm", 1600),
    (r"verelius", "annan", "Verelius", 1600),
    (r"rudbeck,atlant|atlantica|o\.rudbeck", "annan", "O. Rudbeck (Atlantica)", 1600),
    (r"törnevall|tornevall", "annan", "Törnevall", 1700),
    (r"celsius", "annan", "Celsius", 1700),
    (r"hallman", "annan", "Hallman", 1700),
    (r"tillæus|tillaeus", "annan", "Tillæus", 1700),
    (r"o\.[rk]ehn", "annan", "O. Rehn", 1700),
    (r"grau", "annan", "Grau", 1700),
    (r"brocman|broocman", "annan", "Brocman", 1700),
    (r"fryxell", "annan", "Fryxell", 1700),
    (r"gahm", "annan", "Gahm-Persson", 1700),
    (r"rogberg", "annan", "Rogberg", 1700),
    (r"bjerchen", "annan", "Bjerchenius", 1700),
    (r"tham,|avtham|itham", "annan", "Tham", 1700),
    (r"hilfeling", "annan", "Hilfeling", 1700),
    (r"eliasmartin", "annan", "Elias Martin", 1700),
    (r"næzén|naezen", "annan", "Næzén", 1700),
    (r"h[iü]+lphers", "annan", "Hülphers", 1700),
    (r"gestrin", "annan", "Gestrin", 1700),
    (r"göransson", "Bautil", None, 1700),
    (r"dybeck", "annan", "Dybeck", 1800), (r"hofberg", "annan", "Hofberg", 1800), (r"säve|save\b", "annan", "Säve", 1800),
    (r"djurklou", "annan", "Djurklou", 1800), (r"liljegren", "annan", "Liljegren", 1800),
    (r"rudbeck", "annan", "R. C. G. Rudbeck", 1800), (r"söderberg", "annan", "Söderberg", 1800),
    (r"hagelberg|wieselgren", "annan", "Hagelberg", 1800), (r"mandelgren", "annan", "Mandelgren", 1800),
    (r"stephens", "annan", "Stephens", 1800), (r"ljung", "annan", "Ljung", 1800), (r"unge\.", "annan", "Unge", 1800),
    (r"ekdahl", "annan", "Ekdahl", 1800), (r"söderholm", "annan", "Söderholm", 1800), (r"kempff", "annan", "Kempff", 1800),
    (r"lindberger", "annan", "Lindberger", 1800), (r"wætter|waetter", "annan", "Wætter", 1800),
    (r"c\.m\.bol[mi]|avbolm", "annan", "C. M. Bolm", 1800), (r"öberg", "annan", "Öberg", 1800),
    (r"alström", "annan", "Alström", 1800), (r"brusewitz", "annan", "Brusewitz", 1800), (r"sjöborg", "annan", "Sjöborg", 1800),
    (r"frigell\b|frigell\.", "annan", "Frigell", 1800), (r"carlmark", "annan", "Carlmark", 1800),
    (r"tranander", "annan", "Tranander", 1800), (r"alsterlund", "annan", "Alsterlund", 1800),
    (r"vistrand", "annan", "Vistrand", 1800), (r"ihrfors", "annan", "Ihrfors", 1800),
    (r"inventeringsprotokoll", "annan", "inventeringsprotokoll", 1800),
    (r"brate", "annan", "Brate", 1900), (r"friesen", "annan", "von Friesen", 1900), (r"handel", "annan", "Handel", 1900),
    (r"lindqvist", "annan", "O. Lindqvist", 1900), (r"noreen", "annan", "Noreen", 1900),
]
UPPHOV_RE = [(re.compile(a), b, c, d) for a, b, c, d in UPPHOV]


def key(s):
    """Jämförelsetext: gemener utan blanksteg (OCR sprider bokstäverna: 'E f t e r t r ä s n i t t')."""
    return re.sub(r"\s+", "", s.replace("­", "").replace("ı", "i")).lower()


# ---------------------------------------------------------------- 1. SRI-textbandens figurer

def bbox_pages(pdf):
    """Ord med koordinater (punkter) per sida ur pdftotext -bbox: [(bredd, höjd, [(x0, y0, x1, y1, ord)])]."""
    out = subprocess.run(["pdftotext", "-bbox", pdf, "-"], capture_output=True, text=True).stdout
    pages = []
    for m in re.finditer(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', out, re.S):
        words = [(float(a), float(b), float(c), float(d), html.unescape(t)) for a, b, c, d, t in
                 re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', m.group(3))]
        pages.append((float(m.group(1)), float(m.group(2)), words))
    return pages


def segments(words):
    """Ord -> rader -> segment (spalter skilda av breda luckor). Segment: dict x0, y0, x1, y1, text, n."""
    rows = []
    for w in sorted(words, key=lambda w: (w[1] + w[3]) / 2):
        yc, h = (w[1] + w[3]) / 2, w[3] - w[1]
        if rows and abs(yc - rows[-1]["yc"]) < max(3.0, 0.45 * min(h, rows[-1]["h"])):
            rows[-1]["w"].append(w)
        else:
            rows.append({"yc": yc, "h": h, "w": [w]})
    segs = []
    for r in rows:
        ws = sorted(r["w"])
        cur = [ws[0]]
        for w in ws[1:]:
            if w[0] - cur[-1][2] > 22:      # spaltlucka
                segs.append(cur)
                cur = [w]
            else:
                cur.append(w)
        segs.append(cur)
    out = []
    for s in segs:
        out.append({"x0": min(w[0] for w in s), "y0": min(w[1] for w in s), "x1": max(w[2] for w in s),
                    "y1": max(w[3] for w in s), "text": " ".join(w[4] for w in s), "n": len(s)})
    return sorted(out, key=lambda s: (s["y0"], s["x0"]))


def is_body(seg):
    """Brödtext: en bred rad med många bokstäver och få andra tecken (OCR-skräp ur en teckning blir sällan så).
    Räknar tecken och inte ord, eftersom OCR ofta sprider bokstäverna ('m a n')."""
    t = seg["text"].replace(" ", "")
    letters = sum(c.isalpha() for c in t)
    return seg["x1"] - seg["x0"] > 120 and letters >= 25 and letters / max(1, len(t)) >= 0.8


def caption_start(seg, prov):
    k = key(seg["text"])
    if FIGSTART.match(k):
        return True
    # Södermanland 1936– har bildtexter utan figurnummer: "Sö 286.    Botkyrka."
    return prov in ("Sö",) and bool(re.match(r"^sö\.?\d{1,3}[a-c]?\.", k)) and len(k) < 60


def article_pages(txt, prov):
    """Sida (1-baserad) -> artiklar (signum) som pågår på sidan, ur de centrerade rubrikerna i -layout-texten."""
    pages = open(txt, encoding="utf-8", errors="replace").read().split("\f")
    cur, last, on = None, 0, defaultdict(set)
    for i, p in enumerate(pages, 1):
        if cur:
            on[i].add(cur)
        for ln in p.splitlines():
            m = HEADING.match(ln)
            if m:
                n = int(m.group(1))
                indent = len(ln) - len(ln.lstrip())
                if (cur is None and indent >= 15) or (cur is not None and last < n <= last + 40):
                    cur, last = f"{prov} {n}", n
                    on[i].add(cur)
    return on


def header_nums(txt):
    """Sida -> nummer i sidhuvudet ('203—204. ÅNGARNS KYRKA.', '30. JÄRPÅS SN, KYRKAN.') och i artikelrubrikerna."""
    out = {}
    for i, p in enumerate(open(txt, encoding="utf-8", errors="replace").read().split("\f"), 1):
        lines = [ln for ln in p.splitlines() if ln.strip()]
        nums = set()
        for ln in lines[:4]:
            ln = re.sub(r"(?<=\d) (?=\d)", "", ln)          # "7 3 . TERLE"
            ln = re.sub(r"(?<=\d) \.", ".", ln)
            for m in re.finditer(r"(?<![\d,])(\d{1,4})\s?(?:[—–-]\s?(\d{1,4}))?\s?\.\s+[A-ZÅÄÖ]", ln):
                a, b = int(m.group(1)), int(m.group(2) or m.group(1))
                if 0 <= b - a <= 12:
                    nums.update(range(a, b + 1))
        for ln in lines:
            m = HEADING.match(ln)
            if m:
                nums.add(int(m.group(1)))
        out[i] = nums
    return out


def upphov_of(k):
    for r, kalla, who, sek in UPPHOV_RE:
        if r.search(k):
            return kalla, who, sek
    return "annan", None, None


def sri_figures(known):
    figs = []
    for pdf in sorted(glob.glob(os.path.join(SRI, "sri_*.pdf"))):
        name = os.path.basename(pdf)[:-4]
        if "karta" in name or "plansch" in name:
            continue
        prov = next((v for k, v in PROVINCE.items() if f"sri_{k}_" in name), None)
        if not prov or prov in ("Öl", "Ög"):        # Öl och Ög har bilderna på planscherna, inte i texten
            continue
        on = article_pages(pdf[:-4] + ".txt", prov)
        hdr = header_nums(pdf[:-4] + ".txt")
        for pno, (W, H, words) in enumerate(bbox_pages(pdf), 1):
            segs = segments(words)
            starts = [s for s in segs if caption_start(s, prov)]
            for s in starts:
                # bildtexten = startsegmentet + upp till två rader under i samma spalt
                block, bottom = [s], s
                for t in segs:
                    if len(block) >= 3:
                        break
                    if t is s or t["y0"] <= bottom["y0"] or t["y0"] - bottom["y1"] > 9:
                        continue
                    if t["x0"] < s["x0"] - 25 or t["x0"] > s["x1"] or caption_start(t, prov):
                        continue
                    if re.search(r"efter|teckning|träsnitt|\(b\.?\d", key(" ".join(b["text"] for b in block)) + "") and \
                            key(block[-1]["text"]).endswith((".", ")")):
                        break
                    block.append(t)
                    bottom = t
                text = " ".join(b["text"] for b in block)
                k = key(text)
                if not DRAWING.search(k) or NOT_DRAWING.search(k):
                    continue
                head = re.sub(r"^[fe]i[gq]\.?\d+[a-c]?[.,]?", "", k)
                sigs = []
                for m in SIG.finditer(head[:40]):
                    sigs.append(f"{m.group(1).capitalize() if m.group(1) != 'u' else 'U'} {int(m.group(2))}{m.group(3).upper() if m.group(3) else ''}")
                # "Vg 66 och 65", "Vs 9 och 10"
                m1 = SIG.search(head[:40])
                if m1:
                    for m2 in re.finditer(r"(?:och|samt|,)(?:\([^)]{0,12}\))?(\d{1,4})(?=[.,(]|och)", head[m1.end():m1.end() + 30]):
                        sigs.append(sigs[0].split()[0] + " " + m2.group(1))
                sigs = [x if x in known else x.rstrip("ABC") if x.rstrip("ABC") in known else x for x in sigs]
                sigs = [x for x in dict.fromkeys(sigs) if x in known]
                if not sigs:
                    continue
                kalla, who, sek = upphov_of(k)
                yr = re.search(r"(1[5-9]\d\d)(?!\s*[:—-]\s*\d)", text.replace(" ", ""))
                if yr and kalla != "Bautil":
                    sek = int(yr.group(1)) // 100 * 100
                bnr = re.search(r"(?:efterb|\(b|träsnittb)\.?(\d{1,4})", k)
                ctx = set().union(*(on.get(pno + d, set()) for d in (-2, -1, 0, 1, 2)))
                near = {int(re.sub(r"\D", "", c.split()[1]) or 0) for c in ctx}
                near |= set().union(*(hdr.get(pno + d, set()) for d in (-2, -1, 0, 1, 2)))
                rattat = []
                for j, x in enumerate(sigs):
                    n = int(re.sub(r"\D", "", x.split()[1]))
                    if any(abs(n - c) <= 3 for c in near):
                        continue
                    # OCR-fel i en siffra (U 614 för U 514): rätta bara när precis ett rubriknummer ligger en siffra ifrån
                    cand = {c for c in near if len(str(c)) == len(str(n)) and
                            sum(a != b for a, b in zip(str(c), str(n))) == 1}
                    if len(cand) == 1:
                        y = f"{x.split()[0]} {cand.pop()}"
                        if y in known:
                            rattat.append(f"{x}->{y}")
                            sigs[j] = y
                            continue
                    sigs[j] = None
                sigs = [x for x in dict.fromkeys(sigs) if x]
                if not sigs:
                    print("  utan artikel i närheten:", name, pno, text[:90], flush=True)
                    continue
                # spaltens bredd: andra bildtexter på samma rad delar sidan; brödtext bredvid begränsar
                same = sorted([t for t in starts if abs(t["y0"] - s["y0"]) < 6], key=lambda t: t["x0"])
                i = same.index(s)
                left = 0.0 if i == 0 else (same[i - 1]["x1"] + s["x0"]) / 2
                right = W if i == len(same) - 1 else (s["x1"] + same[i + 1]["x0"]) / 2
                for t in segs:
                    if abs(t["y0"] - s["y0"]) < 6 and t is not s and t not in same and is_body(t):
                        if t["x0"] >= s["x1"]:
                            right = min(right, t["x0"] - 4)
                        elif t["x1"] <= s["x0"]:
                            left = max(left, t["x1"] + 4)
                cx0, cx1 = min(t["x0"] for t in block), max(t["x1"] for t in block)

                def top_of(lo, hi):
                    """Överkant: närmaste brödtextrad ovanför som täcker spalten (eller sidhuvudet)."""
                    top = 0.0
                    for t in segs:
                        if t["y1"] >= s["y0"] - 2:
                            continue
                        if is_body(t) and min(t["x1"], hi) - max(t["x0"], lo) > 0.5 * (hi - lo):
                            top = max(top, t["y1"] + 2)
                        elif t["y0"] < 0.1 * H and re.search(r"\d", t["text"]):
                            top = max(top, t["y1"] + 2)      # sidhuvud med sidnummer
                    return top
                top = top_of(left, right)
                # brödtext bredvid figuren (ovanför bildtexten, helt till vänster eller höger om den) smalnar av spalten
                for _ in range(2):
                    for t in segs:
                        if top <= t["y0"] and t["y1"] < s["y0"] - 2 and is_body(t):
                            if t["x0"] >= cx1 - 5:
                                right = min(right, t["x0"] - 4)
                            elif t["x1"] <= cx0 + 5:
                                left = max(left, t["x1"] + 4)
                    top = top_of(left, right)
                figs.append({"pdf": name, "sida": pno, "signa": sigs, "bildtext": re.sub(r"\s+", " ", text).strip(),
                             "källa": kalla, "upphov": who, "sekel": sek, "år": int(yr.group(1)) if yr else None,
                             "bautil_nr": int(bnr.group(1)) if bnr else None,
                             "ocr_rättat": rattat,
                             "ruta": [left, top, right, max(t["y1"] for t in block) + 2],
                             "bildtext_ruta": [cx0, s["y0"], cx1], "sidmått": [W, H]})
        print(name, sum(1 for f in figs if f["pdf"] == name), "teckningsfigurer", flush=True)
    return figs


def crop_sri(f, out):
    """Rendera rutan (300 dpi, gråskala) och behåll bara de bläckspalter som står över bildtexten: står två figurer
    bredvid varandra med var sin bildtext på olika höjd, eller en spalt brödtext i marginalen, skärs de bort."""
    import numpy as np
    from PIL import Image
    x0, y0, x1, y1 = f["ruta"]
    s = DPI / 72
    subprocess.run(["pdftoppm", "-r", str(DPI), "-jpeg", "-jpegopt", "quality=88", "-singlefile", "-gray",
                    "-f", str(f["sida"]), "-l", str(f["sida"]), "-x", str(int(x0 * s)), "-y", str(int(y0 * s)),
                    "-W", str(int((x1 - x0) * s)), "-H", str(int((y1 - y0) * s)),
                    os.path.join(SRI, f["pdf"] + ".pdf"), out[:-4]], check=True, stderr=subprocess.DEVNULL)
    im = Image.open(out).convert("L")
    a = np.asarray(im)
    cx0, cy0, cx1 = f["bildtext_ruta"]
    fig = a[: max(1, int((cy0 - y0) * s) - 4)]
    cols = np.flatnonzero((fig < 150).sum(axis=0) > 3)
    if len(cols):
        runs, start, prev = [], cols[0], cols[0]
        for c in cols[1:]:
            if c - prev > 30:                       # en vit ränna på minst 30 px (2,5 mm) skiljer två figurer
                runs.append((start, prev))
                start = c
            prev = c
        runs.append((start, prev))
        lo, hi = (cx0 - x0) * s, (cx1 - x0) * s
        keep = [r for r in runs if min(r[1], hi) - max(r[0], lo) > 0] or runs
        a0, a1 = min(min(r[0] for r in keep), int(lo)), max(max(r[1] for r in keep), int(hi))
        im = im.crop((max(0, a0 - 10), 0, min(im.width, a1 + 10), im.height))
    im.save(out, quality=88)
    trim(out)


def trim(path, thr=170, pad=12):
    """Skär bort vit marginal kring det som är tryckt (behåller bildtexten längst ned)."""
    from PIL import Image
    im = Image.open(path).convert("L")
    bw = im.point(lambda v: 255 if v < thr else 0)
    bb = bw.getbbox()
    if bb:
        a, b, c, d = bb
        im.crop((max(0, a - pad), max(0, b - pad), min(im.width, c + pad), min(im.height, d + pad))).save(path, quality=88)


# ---------------------------------------------------------------- 2. Bautil: signum -> B-nummer -> sida

BFIX = str.maketrans({"l": "1", "I": "1", "O": "0", "o": "0", "U": "1", "i": "1", "Ó": "0", "ó": "0"})
BDIG = r"(?:[\dlIOUiÓó]\s?){1,4}"


def raw_articles():
    """Signum -> artikeltexten oförändrad (versaler behålls, så att 'B 95' skiljs från runan b), samma
    rubrikregel som src.sri_text.articles()."""
    out = defaultdict(list)
    for path in sorted(glob.glob(os.path.join(SRI, "sri_*_text*.txt")) + glob.glob(os.path.join(SRI, "sri_oland_*.txt"))):
        name = os.path.basename(path)
        prov = next((v for k, v in PROVINCE.items() if f"sri_{k}_" in name), None)
        if not prov:
            continue
        cur, buf, last = None, [], 0
        for ln in open(path, encoding="utf-8", errors="replace").read().splitlines():
            m = HEADING.match(ln)
            if m:
                n = int(m.group(1))
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
    return {k: "\n".join(v) for k, v in out.items()}


def bnums(s):
    """'B 832, 833' / 'B. 7ii' / 'B 9 3 2' -> [832, 833] / [711] / [932]. Ett nummer måste följas av skiljetecken,
    blanksteg eller 'och' ('B. 886, l l ö l' ger bara 886)."""
    out = []
    m = re.match(r"[Bß]\.?\s?", s)
    if not m:
        return out
    rest = s[m.end():]
    while True:
        n = re.match(rf"({BDIG})(?=\s*(?:[,;.:)—–]|och\b|$))", rest)
        if not n:
            break
        raw = n.group(1).replace(" ", "")
        if not re.search(r"\d", raw):          # 'I, 472' = 'L 472' (Liljegren), inte ett B-nummer
            break
        v = raw.translate(BFIX)
        if v.isdigit() and 1 <= int(v) <= 1173:
            out.append(int(v))
        rest = rest[n.end():]
        c = re.match(r"\s?(?:,|och)\s?(?=[\dlIOU])", rest)
        if not c:
            break
        rest = rest[c.end():]
    return out


def bautil_numbers(known):
    """Signum -> B-nummer ur artikelns 'Litteratur:'-rad (första B-gruppen) och planschhänvisningen 'Pl. 14: B. 1145'."""
    res = {}
    for sig, txt in raw_articles().items():
        if sig not in known:
            continue
        found, pl = [], []
        for m in re.finditer(r"L\s?i\s?t\s?t?\s?e\s?r\s?a\s?t\s?u\s?r\s?:(.{0,200})", txt, re.S):
            seg = m.group(1).replace("\n", " ")
            # B-gruppen står först eller efter L-numret (Öland: 'Literatur: L. 1324, B. 1076')
            b = re.search(r"(?<![A-Za-zÅÄÖåäö])[Bß]\s?\.?\s?[\dlIOU]", seg)
            # B-gruppen först eller efter L-numret; inte 'L. f. B. 1090' (en annan samling)
            if b and b.start() < 40 and re.fullmatch(r"\s*|.*[,;:—–]\s*", seg[:b.start()]):
                found += bnums(seg[b.start():].replace("B .", "B."))
            break
        for m in re.finditer(r"P\s?[lLI1]\s?\.?\s?\d{1,3}\s?:\s?(B\.?\s?[\dlIOU ]{1,6})", txt[:1500]):
            pl += bnums(m.group(1))
        found = pl or found               # planschhänvisningen är tydligare tryckt än litteraturraden
        if found:
            res[sig] = sorted(set(found))
    return res


BAUTIL = "/Volumes/2TB/Antigrvity/Runes/downloads/bautil_umu"
# Sidorna 0000–0029 är titelblad, företal och 'Runa-svenskans innehåll' (texten per N:o); träsnitten börjar med No 1 på 0030
FIRST_WOODCUT_PAGE = 30


def bautil_ocr():
    """Tesseract (swe, gles text, svartvit bild skalad till 70 %: snabbt och träffar 'N:o'-raderna lika bra som full
    upplösning) på varje Bautil-sida en i taget; TSV sparas i BAUTIL/ocr/NNNN_70.tsv. (Sidorna 0000–0044 lästes
    först i full upplösning, NNNN.tsv; båda läses.)"""
    from PIL import Image
    os.makedirs(os.path.join(BAUTIL, "ocr"), exist_ok=True)
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    for jpg in sorted(glob.glob(os.path.join(BAUTIL, "[0-9][0-9][0-9][0-9].jpg"))):
        stem = os.path.basename(jpg)[:-4]
        if int(stem) < FIRST_WOODCUT_PAGE:
            continue
        tsv = os.path.join(BAUTIL, "ocr", stem + "_70")
        if os.path.exists(tsv + ".tsv"):
            continue
        tmp = tsv + "_bw.png"
        im = Image.open(jpg).convert("L")
        im.resize((im.width * 7 // 10, im.height * 7 // 10)).point(lambda v: 0 if v < 110 else 255).save(tmp)
        subprocess.run(["tesseract", tmp, tsv + ".part", "-l", "swe", "--psm", "11", "tsv"], env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.replace(tsv + ".part.tsv", tsv + ".tsv")
        os.remove(tmp)


def bautil_strips(stem, boxes):
    """Snabbare och säkrare än hela sidan: tesseract på smala band strax ovanför och under varje träsnitt, där
    Bautils bildtexter ('N:o 1145. J Biörnlunda Sockn.') står. Ger [(nr, x, y, h, med_No, bildtext)] i sidans
    koordinater; sparas i BAUTIL/ocr/NNNN_band.json."""
    from PIL import Image
    cache = os.path.join(BAUTIL, "ocr", stem + "_band.json")
    if os.path.exists(cache):
        return [tuple(r) for r in json.load(open(cache))]
    im = Image.open(os.path.join(BAUTIL, stem + ".jpg")).convert("L")
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    tmp = os.path.join(BAUTIL, "ocr", stem + "_band.png")
    # alla band staplas i en bild (60 px vitt emellan) så att tesseract startas en gång per sida
    strips, offs, yy = [], [], 0
    for x0, y0, x1, y1 in boxes:
        for a, b in ((y0 - 170, y0 + 10), (y1 - 10, y1 + 170)):
            ox, oy = max(0, x0 - 250), max(0, a)
            c = im.crop((ox, oy, min(im.width, x1 + 250), min(im.height, b))).point(lambda v: 0 if v < 110 else 255)
            strips.append(c)
            offs.append((yy, yy + c.height, ox, oy))
            yy += c.height + 60
    out = []
    if strips:
        comp = Image.new("L", (max(c.width for c in strips), yy), 255)
        for c, (ya, yb, ox, oy) in zip(strips, offs):
            comp.paste(c, (0, ya))
        comp.save(tmp)
        tsv = subprocess.run(["tesseract", tmp, "-", "-l", "swe", "--psm", "4", "tsv"], capture_output=True,
                             text=True, env=env).stdout.splitlines()[1:]
        words = []
        for ln in tsv:
            f = ln.split("\t")
            if len(f) == 12 and f[11].strip():
                x, y, w, h = (int(v) for v in f[6:10])
                band = next((o for o in offs if o[0] <= y < o[1]), None)
                if band:
                    words.append((x + band[2], y - band[0] + band[3], w, h, f[11].strip(), (int(f[2]), int(f[3]), int(f[4]))))
        for i, (x, y, w, h, t, line) in enumerate(words):
            m = re.fullmatch(r"[.,:]?(\d{1,4})[.,:;]?", t)
            if not m or h < 25:
                continue
            no = i > 0 and bool(re.fullmatch(r"\W*[NJAK][:;.,']?[oOd0e°]?[.,:]?|N[:;.]?o|No|Neo|N:o", words[i - 1][4]))
            cap = " ".join(w2[4] for w2 in words[i + 1:] if w2[5] == line)[:80]
            out.append((int(m.group(1)), x, y, h, no, cap))
    if os.path.exists(tmp):
        os.remove(tmp)
    json.dump(out, open(cache, "w"), ensure_ascii=False)
    return out


def bautil_caption(stem, n, near=None):
    """Bautils ortsangivelse efter 'N:o n' på sidan, som OCR läst den (frakturen ger ofta förvanskade ord); finns numret
    flera gånger tas läsningen närmast den valda etiketten."""
    path = os.path.join(BAUTIL, "ocr", stem + "_band.json")
    rows = [r for r in json.load(open(path)) if r[0] == n and r[5]] if os.path.exists(path) else []
    if not rows:
        return ""
    if near:
        return min(rows, key=lambda r: abs(r[1] - near[0]) + abs(r[2] - near[1]))[5]
    return max(rows, key=lambda r: len(r[5]))[5]


def bautil_labels(stem):
    """Träsnittsnumren på en Bautil-sida ur tesseract-TSV: [(nr, x, y, h, med_No)] där med_No = 'N:o' står före."""
    out = []
    band = os.path.join(BAUTIL, "ocr", stem + "_band.json")
    if os.path.exists(band):
        out += [tuple(r[:5]) for r in json.load(open(band))]
    for suf, sc in (("", 1.0), ("_70", 0.7)):
        path = os.path.join(BAUTIL, "ocr", stem + suf + ".tsv")
        if os.path.exists(path):
            out += _labels(path, sc)
    return out


def _labels(path, sc):
    rows = []
    for ln in open(path, encoding="utf-8", errors="replace").read().splitlines()[1:]:
        f = ln.split("\t")
        if len(f) == 12 and f[11].strip():
            rows.append(tuple(int(int(v) / sc) for v in f[6:10]) + (float(f[10]), f[11].strip()))
    out = []
    for x, y, w, h, conf, t in rows:
        m = re.fullmatch(r"[.,:]?(\d{1,4})[.,:;]?", t)
        if not m or h < 25:
            continue
        no = any(re.fullmatch(r"[NJ][:;.,']?[o0e°]?[.,:]?|N[:;.]?o|No|Neo|N:o|N.o|A:o|K:o", t2) and
                 0 < x - (x2 + w2) < 260 and abs(y - y2) < 60 for x2, y2, w2, h2, c2, t2 in rows)
        out.append((int(m.group(1)), x, y, h, no))
    return out


def bautil_boxes(stem):
    """Träsnitten på en Bautil-sida som rutor (x0, y0, x1, y1) i full upplösning: sammanhängande svarta ytor
    (träsnittens ramlinjer håller ihop dem) på en nedskalad svartvit bild; ytor som rör bildkanten är bokens kant."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage as nd
    im = Image.open(os.path.join(BAUTIL, stem + ".jpg")).convert("L")
    q = 4
    g = np.asarray(im.resize((im.width // q, im.height // q))).astype(float)
    a = g < 120
    # bokens kant och skannerns bakgrund: rader/kolumner som till största delen är mörka, plus 15 px, räknas bort
    dark_c = np.flatnonzero((g < 110).mean(axis=0) > 0.5)
    dark_r = np.flatnonzero((g < 110).mean(axis=1) > 0.5)
    W0 = g.shape[1]
    left = max([c for c in dark_c if c < W0 // 3] or [0])
    right = min([c for c in dark_c if c > 2 * W0 // 3] or [W0])
    a[:, : left + 15] = False
    a[:, max(0, right - 15):] = False
    H0 = g.shape[0]
    a[: max([r for r in dark_r if r < H0 // 3] or [0]) + 15] = False
    a[min([r for r in dark_r if r > 2 * H0 // 3] or [H0]) - 15:] = False
    a = nd.binary_dilation(a, iterations=2)
    lab, n = nd.label(a)
    H, W = a.shape
    boxes = []
    for sl in nd.find_objects(lab):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        if (y1 - y0) * (x1 - x0) < 2500 or min(y1 - y0, x1 - x0) < 30:
            continue
        if x0 <= 8 or y0 <= 8 or x1 >= W - 8 or y1 >= H - 8:
            continue
        boxes.append((x0 * q, y0 * q, x1 * q, y1 * q))
    # bort med textrader och bitar: ett träsnitt är minst 300 x 200 px, och en ruta inuti en annan är en del av den
    boxes = [b for b in boxes if b[3] - b[1] >= 300 and b[2] - b[0] >= 200]

    def inside(b, o):                                   # andel av b som ligger inom o
        w = max(0, min(b[2], o[2]) - max(b[0], o[0]))
        h = max(0, min(b[3], o[3]) - max(b[1], o[1]))
        return w * h / ((b[2] - b[0]) * (b[3] - b[1]))
    boxes = [b for b in boxes if not any(o != b and inside(b, o) > 0.6 and
                                         (o[2] - o[0]) * (o[3] - o[1]) > (b[2] - b[0]) * (b[3] - b[1]) for o in boxes)]
    return boxes, im.size


def label_box(lbl, boxes):
    """Rutan som hör till ett 'N:o'-nummer: närmast under numret (Bautils bildtext står ovanför träsnittet), annars
    närmast ovanför."""
    n, x, y, h, _ = lbl
    below = [b for b in boxes if b[1] > y - 40 and b[1] - y < 450 and b[0] < x + 500 and b[2] > x - 200]
    if below:
        return min(below, key=lambda b: b[1] - y), "under"
    above = [b for b in boxes if b[3] < y + 40 and y - b[3] < 300 and b[0] < x + 500 and b[2] > x - 200]
    if above:
        return max(above, key=lambda b: b[3]), "över"
    return None, None


def bautil_map():
    """B-nummer -> {sida, ruta, säker, etikett}: 'N:o'-numren ur OCR (band ovanför/under varje träsnitt, och för de första
    sidorna hela sidan), rensade med en längsta stigande följd över sidorna; svaga och avhuggna nummer tas med bara när
    de passar mellan två säkra grannar. Rutan = träsnittet under (annars över) numret."""
    cache = os.path.join(BAUTIL, "ocr", "rutor.json")
    boxes = json.load(open(cache)) if os.path.exists(cache) else {}
    stems = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(BAUTIL, "[0-9]*.jpg"))
                   if int(os.path.basename(f)[:4]) >= FIRST_WOODCUT_PAGE)
    for st in stems:
        if st not in boxes:
            boxes[st] = bautil_boxes(st)[0]
            json.dump(boxes, open(cache, "w"))
        bautil_strips(st, boxes[st])
    labs = defaultdict(list)                             # (sidindex, nr) -> [(etikett, ruta, över/under)]
    under = defaultdict(set)                             # (sidindex, ruta) -> nummer som står ovanför rutan
    for i, st in enumerate(stems):
        ls = [lb for lb in bautil_labels(st) if 1 <= lb[0] <= 1173]
        if not boxes[st] or sum(lb[4] for lb in ls) > 30:      # textsidor
            continue
        for lb in ls:
            bx, how = label_box(lb, boxes[st])
            labs[(i, lb[0])].append((lb, tuple(bx) if bx else None, how))
            if how == "under" and lb[4]:
                under[(i, tuple(bx))].add(lb[0])

    def best_box(i, n):
        v = defaultdict(float)
        for lb, bx, how in labs[(i, n)]:
            # ett nummer under en ruta får inte ta en ruta som ett annat 'N:o' står ovanför (grannens träsnitt)
            if bx and not (how == "över" and under[(i, bx)] - {n}):
                v[bx] += 2 if lb[4] else 1
        if not v:
            return None, None
        bx = max(v, key=v.get)
        lb = max((lb for lb, b, _ in labs[(i, n)] if b == bx), key=lambda lb: lb[4])
        return bx, lb

    # 1) starka etiketter ('N:o' före numret): längsta strängt stigande följd över (sida, nummer), viktad med antal läsningar
    strong = sorted(k for k, v in labs.items() if any(lb[4] for lb, _, _ in v))
    wt = [min(3, sum(lb[4] for lb, _, _ in labs[k])) for k in strong]
    best, prev = list(wt), [-1] * len(strong)
    for j, (i, n) in enumerate(strong):
        for k in range(j):
            if strong[k][1] < n and strong[k][0] <= i and best[k] + wt[j] > best[j]:
                best[j], prev[j] = best[k] + wt[j], k
    j = max(range(len(strong)), key=lambda k: best[k]) if strong else -1
    found = {}
    while j >= 0:
        i, n = strong[j]
        bx, lb = best_box(i, n)
        found[n] = {"sida": stems[i], "ruta": list(bx) if bx else None, "säker": True,
                    "etikett": list(lb[1:4]) if lb else None}
        j = prev[j]

    def bounds(n, i=None):
        nums = sorted(found)
        lo = max([m for m in nums if m < n] or [0])
        hi = min([m for m in nums if m > n] or [1174])
        return lo, hi

    # 2) svaga etiketter (utan 'N:o', minst två siffror) och avhuggna nummer ('146' för 1146) som passar mellan grannarna
    for (i, n), v in sorted(labs.items()):
        # svaga etiketter: minst tre siffror; avhuggna: bara med 'N:o' före och minst två siffror kvar
        has_no = any(lb[4] for lb, _, _ in v)
        cands = [n] if n >= 100 or (has_no and n >= 10) else []
        for m in [found_n for found_n in sorted(found) if stems.index(found[found_n]["sida"]) <= i][-1:]:
            if has_no and n >= 10 and len(str(m)) > len(str(n)):
                cands.append(int(str(m)[: len(str(m)) - len(str(n))] + str(n)))
        for c in cands:
            if c in found:
                continue
            lo, hi = bounds(c)
            if lo and hi < 1174 and stems.index(found[lo]["sida"]) <= i <= stems.index(found[hi]["sida"]):
                bx, lb = best_box(i, n)
                found[c] = {"sida": stems[i], "ruta": list(bx) if bx else None, "säker": True,
                            "etikett": list(lb[1:4]) if lb else None}
                break
    used = {(f["sida"], tuple(f["ruta"])) for f in found.values() if f["ruta"]}
    # Nummer som OCR inte läst lämnas utan sida: att räkna sig fram via antalet rutor visade sig opålitligt
    # (träsnitt som rör varandra blir en ruta, roterade bildtexter läses inte) – hellre omappat än tvivelaktigt.
    return found


def crop_bautil(info, out):
    from PIL import Image
    im = Image.open(os.path.join(BAUTIL, info["sida"] + ".jpg"))
    if info.get("ruta"):
        x0, y0, x1, y1 = info["ruta"]
        if info.get("etikett"):
            lx, ly, lh = info["etikett"]
            y0, y1 = min(y0, ly - 20), max(y1, ly + lh + 20)
            x0 = min(x0, lx - 20)
        im = im.crop((max(0, x0 - 30), max(0, y0 - 30), min(im.width, x1 + 30), min(im.height, y1 + 30)))
    im.convert("RGB").save(out, quality=88)


# ---------------------------------------------------------------- 3. planschsidor som själva är gamla teckningar

PLANSCH = "/Volumes/2TB/Antigrvity/Runes/downloads/sri_plansch"


def plansch_ar_teckning(known, bnr):
    """Signum -> [{pdf, sida, källa, bautil_nr, not_}] för planschfigurer som är återgivna gamla teckningar:
    Östergötland (bildtexten 'Ög. 16. Kuddby (B. 835)'), Södermanland 1924 ('Pl. 14: B. 1145' i artikeln; planscherna
    1–14 i h01 är faksimil av Bautils sidor), Öland (artikeln: 'Vår fig. 10, pl. VII är en kopia af Rhezelii teckning')."""
    out = defaultdict(list)
    # Östergötland: bildtexterna på planscherna
    for pdf in sorted(glob.glob(os.path.join(PLANSCH, "sri_ostergotland_*_plansch.pdf"))):
        stem = os.path.basename(pdf)[:-4]
        for p, txt in enumerate(subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True,
                                               text=True).stdout.split("\f"), 1):
            flat = re.sub(r"\s+", " ", txt)
            for m in re.finditer(r"[ÖO]g\.?\s?(\d{1,3})(?:\s?[—–-]\s?(\d{1,3}))?\.\s+([^()\d]{2,40}?)\s*\(([^)]{2,60})\)", flat):
                inner = m.group(4)
                a, b = int(m.group(1)), int(m.group(2) or m.group(1))
                bn = re.match(r"\s*[Bß]\.\s?(\d{3,4})", inner)
                if bn:
                    entry = {"källa": "Bautil", "bautil_nr": int(bn.group(1)), "upphov": None}
                elif re.search(r"teckning", inner):
                    kalla, who, sek = upphov_of(key(inner))
                    entry = {"källa": kalla, "bautil_nr": None, "upphov": who or inner.strip()}
                else:
                    continue                      # 'L. f. B. 1090' m.m.: annan samling
                for n in range(a, b + 1):
                    sig = f"Ög {n}"
                    if sig in known:
                        out[sig].append(dict(entry, pdf=stem, sida=p, not_=f"planschtext: {m.group(0).strip()}"))
    # Södermanland: 'Pl. N: B NNN' i artikeln -> h01-planschen N (sida N + 2), ett faksimil av Bautils sida
    arts = raw_articles()
    so = "sri_sodermanland_b03_h01_plansch"
    for sig, txt in arts.items():
        if not sig.startswith("Sö ") or sig not in known:
            continue
        for m in re.finditer(r"P\s?[lLI1]\s?\.?\s?(\d{1,2})\s?:\s?(B\.?\s?[\dlIOUG ]{1,6})", txt[:1500]):
            pl = int(m.group(1))
            if 1 <= pl <= 14:
                for n in bnums(m.group(2).replace("G", "6")) or bnr.get(sig, [None])[:1]:
                    out[sig].append({"källa": "Bautil", "bautil_nr": n, "upphov": None, "pdf": so, "sida": pl + 2,
                                     "not_": f"Sö-planschen Pl. {pl} är ett faksimil av Bautils sida; sök N:o {n}"})
    # Öland (Söderberg & Brate 1900–06): artikeln säger ofta vems teckning planschfiguren återger
    for sig, txt in arts.items():
        if not (sig.startswith("Öl ") and sig in known):
            continue
        flat = re.sub(r"\s+", " ", txt)
        for m in re.finditer(r"reproduktion|reproducera\w*|kopia af|återgifva\w*", flat):
            win = flat[m.start():m.start() + 160]
            before = flat[max(0, m.start() - 160):m.start()]
            if not re.search(r"\b(fig|pl)\.", before[-80:] + win[:80], re.I):
                continue
            names = [(n.start(), n.group(0)) for n in re.finditer(r"Rhezeli\w*|Bautil\w*|B\.\s?1\d{3}|n:r 1\d{3} i Bautil", win)]
            if not names and re.search(r"\bhans teckning", win):
                names = [(0, n.group(0)) for n in re.finditer(r"Rhezeli\w*|Bautil\w*", before)][-1:]
            if not names:
                continue
            nm = names[0][1]
            bn = re.search(r"1\d{3}", nm)
            if nm.startswith("Rhezeli"):
                e = {"källa": "Rhezelius", "bautil_nr": None, "upphov": "Rhezelius"}
            else:
                e = {"källa": "Bautil", "bautil_nr": int(bn.group(0)) if bn else (bnr.get(sig) or [None])[0], "upphov": None}
            out[sig].append(dict(e, pdf=None, sida=None, not_="artikeln: " + flat[max(0, m.start() - 60):m.start() + 120]))
            break
    return out


# ---------------------------------------------------------------- samman

def main(render):
    import csv
    csv.field_size_limit(10 ** 9)
    known = set(load().sig)
    corp = {r["signum"]: r for r in csv.DictReader(open(os.path.join(
        ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "corpus.csv"), encoding="utf-8")) if r["signum"] in known}
    lost = {s for s, r in corp.items() if r["lost"] == "1"}
    sidor = {}
    for f in ("sidor.json", "sidor_utvidgning.json"):
        sidor.update(json.load(open(os.path.join(OUT, f), encoding="utf-8")))
    os.makedirs(IMG, exist_ok=True)
    res = defaultdict(list)

    def fname(*parts):
        return os.path.join(IMG, re.sub(r"[^\w.-]+", "_", "_".join(str(p) for p in parts)) + ".jpg")

    # 1. SRI-textbanden
    figs = sri_figures(known)
    for f in figs:
        for sig in f["signa"]:
            fil = fname(sig, f["pdf"], f"p{f['sida']:04d}", int(f["ruta"][0]), int(f["ruta"][1]))
            if any(e["fil"] == os.path.relpath(fil, ROOT) for e in res[sig]):
                continue                                   # samma bildtext läst två gånger
            whole = False
            if render and not os.path.exists(fil):
                crop_sri(f, fil)
            if os.path.exists(fil):
                from PIL import Image
                if Image.open(fil).height < 400:   # figuren står inte ovanför bildtexten (bredvid, på annan sida)
                    subprocess.run(["pdftoppm", "-r", str(DPI), "-jpeg", "-jpegopt", "quality=88", "-singlefile", "-gray",
                                    "-f", str(f["sida"]), "-l", str(f["sida"]), os.path.join(SRI, f["pdf"] + ".pdf"),
                                    fil[:-4]], check=True, stderr=subprocess.DEVNULL)
                    whole = True
                elif Image.open(fil).height > 4500:          # tidigare körning: redan hela sidan
                    whole = True
            res[sig].append({"fil": os.path.relpath(fil, ROOT), "källa": "SRI-text" if f["källa"] == "annan" else f["källa"],
                             "återgiven_i": "SRI-text", "upphov": f["upphov"], "år": f["år"], "sekel": f["sekel"],
                             "bautil_nr": f["bautil_nr"], "förlorad": sig in lost, "pdf": f["pdf"], "sida": f["sida"],
                             "not": f"bildtext: {f['bildtext'][:200]}" + (f"; signum rättat {f['ocr_rättat']}" if f["ocr_rättat"] else "")
                             + ("; flera stenar i samma figur" if len(f["signa"]) > 1 else "")
                             + ("; hela sidan (figuren kunde inte skäras ut ovanför bildtexten)" if whole else "")})
    # 2. Bautil (Umeå UB:s exemplar)
    bnr = bautil_numbers(known)
    for f in figs:                                   # 'Efter B 95' i bildtexten ger också numret
        if f["bautil_nr"]:
            for sig in f["signa"]:
                bnr.setdefault(sig, [])
                if f["bautil_nr"] not in bnr[sig]:
                    bnr[sig].append(f["bautil_nr"])
    pat = plansch_ar_teckning(known, bnr)
    for sig, v in pat.items():
        for e in v:
            if e["källa"] == "Bautil" and e["bautil_nr"] and e["bautil_nr"] not in bnr.setdefault(sig, []):
                bnr[sig].append(e["bautil_nr"])
    bmap = bautil_map() if glob.glob(os.path.join(BAUTIL, "ocr", "*.tsv")) else {}
    olost = []
    for sig, ns in sorted(bnr.items()):
        for n in sorted(set(ns)):
            info = bmap.get(n)
            if not info:
                olost.append((sig, n))
                continue
            r = info["ruta"]
            if r and (r[2] - r[0] < 450 or r[3] - r[1] < 450):
                info = dict(info, ruta=None)          # för liten ruta = bara en bit av träsnittet: ta hela sidan
            fil = fname(sig, "bautil", n)
            if render and not os.path.exists(fil):
                crop_bautil(info, fil)
            cap = bautil_caption(info["sida"], n, info.get("etikett"))
            not_ = ("träsnittet utskuret (rutan kan rymma ett grannträsnitt; numret står vid bilden)" if info["ruta"]
                    else "hela sidan (träsnittet ej utskuret automatiskt); sök N:o " + str(n)) \
                + (f"; Bautils bildtext (OCR): {cap}" if cap else "")
            res[sig].append({"fil": os.path.relpath(fil, ROOT), "källa": "Bautil", "återgiven_i": "Bautil (Umeå UB)",
                             "upphov": None, "år": 1750, "sekel": 1700, "bautil_nr": n, "förlorad": sig in lost,
                             "bautil_sida": int(info["sida"]), "sidbild": os.path.join(BAUTIL, info["sida"] + ".jpg"),
                             "not": not_})
    # 3. planscher som är teckningar. Öland 1900–06 har bara teckningar på planscherna; för förlorade öländska stenar
    #    utan uttalad källa listas planschen ändå, med källan okänd (Rhezelius 1634, Bautil eller Söderbergs egen)
    for sig in sorted(lost):
        if sig.startswith("Öl ") and sig in sidor and sig not in pat:
            pat[sig].append({"källa": "okänd", "bautil_nr": None, "upphov": None, "pdf": None, "sida": None,
                             "not_": "förlorad sten; Ölandsbandets planschfigurer är teckningar, källan ej utläst ur artikeln"})
    pl = {}
    for sig, v in sorted(pat.items()):
        rows = []
        for e in v:
            pdf, sida = e["pdf"], e["sida"]
            if pdf is None and sig in sidor:
                pdf, sida = sidor[sig][0]
            rows.append({"pdf": pdf, "sida": sida, "källa": e["källa"], "upphov": e["upphov"], "bautil_nr": e["bautil_nr"],
                         "förlorad": sig in lost, "ny_sida": not (sig in sidor and [pdf, sida] in sidor[sig]),
                         "not": e["not_"][:220]})
        pl[sig] = rows
    out = {k: res[k] for k in sorted(res)}
    out["_plansch_ar_teckning"] = pl
    out["_bautil_saknar_sida"] = [f"{s}: B {n}" for s, n in olost]
    out["_källor"] = {
        "SRI-text": "Sveriges runinskrifter, textbanden (RAÄ, Digitala SRI); figurer efter äldre teckningar, beskurna. Skyddade: bara för forskning, ej i git.",
        "Bautil": "J. Göransson, Bautil (Stockholm 1750), Umeå universitetsbiblioteks exemplar, Digitala samlingar urn:17a_000068 "
                  "(LIBRIS 10936379): 'fritt från kända upphovsrättsliga restriktioner'. Sidbilder ca 300 dpi.",
        "fält": "källa = tecknare/verk som teckningen går tillbaka på; återgiven_i = var bilden hämtats; sekel = tecknarens sekel "
                "(1600/1700 = äldre teckning; 1800/1900 = senare, med för fullständighetens skull)."}
    json.dump(out, open(os.path.join(OUT, "teckningar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    have = {s for s, v in res.items() if any((e["sekel"] or 0) <= 1700 or e["källa"] in ("Bautil", "Rhezelius", "Hadorph", "Peringskiöld") for e in v)}
    print(len(res), "stenar med teckning;", len(have), "med 1600/1700-talsteckning;",
          len(have & lost), "av", len(lost), "förlorade;", len(pl), "planscher som är teckningar")


if __name__ == "__main__":
    main("--render" in sys.argv)
