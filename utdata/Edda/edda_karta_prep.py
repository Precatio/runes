"""Textunderlag för Eddans stilometriska karta (edda_karta.R).

Alla texter ur utdata/Malt/kallor/edda.json (Guðni Jónssons utgåvor via heimskringla.no) städas från
sidhuvudsskräp och tokeniseras; Hávamál byts mot sina fyra delar; Völuspá in skamma utgår (ingår i
Hyndluljóð); Hugsvinnsmál (Finnur Jónssons utgåva, heimskringla.no) extraheras ur nedladdad HTML och
sparas i kallor/. Utdata: edda_karta_texter.csv (namn, ljodahattr, n_ord, text).
"""
import csv
import html as H
import json
import re

ROT = "/Volumes/2TB/Antigrvity/Runes/aagaard-research"
HUGSVINN_HTML = "/Volumes/2TB/Antigrvity/Runes/downloads/hugsvinnsmal/hugsvinnsmal.html"
MIN_ORD = 600

def tokenisera(text):
    # ǫ i Finnur Jónssons normalisering motsvarar ö hos Guðni Jónsson
    text = text.lower().replace("ǫ", "ö").replace("ǿ", "æ")
    return re.findall(r"[a-zþðæöøáéíóúýœå]+", text)

def stada(text):
    """Klipp bort heimskringla-sidhuvudet: allt före första strof-/kapitelmarkören ' 1. '."""
    m = re.search(r"\s1\.\s+[A-ZÁÉÍÓÚÝÞÆÖÐ]", text)
    if m:
        return text[m.start():]
    m = re.search(r"bjó til prentunar\s+\S+\s*", text)
    assert m, f"hittar ingen start i: {text[:120]}"
    return text[m.end():]

# --- Hugsvinnsmál ur nedladdningen -----------------------------------------------------------------
raw = open(HUGSVINN_HTML, encoding="utf-8").read()
m = (re.search(r'<div[^>]*mw-parser-output[^>]*>(.*?)<div class="printfooter">', raw, re.S)
     or re.search(r'<div[^>]*mw-parser-output[^>]*>(.*)', raw, re.S))
sida = re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", m.group(1))))
start = re.search(r"\s1\.\s+Heyri", sida).start()
slut_strof = sida.index("Hugsvinnsmál hefi ek fyr h")          # strof 148, diktens sista
slut = sida.index(".", sida.index("hér er nú", slut_strof)) + 1  # t.o.m. slutmeningen
hugsvinn = sida[start:slut].strip()
open(f"{ROT}/utdata/Edda/kallor/hugsvinnsmal_norront.txt", "w").write(
    "Hugsvinnsmál, norrön text ur Den norsk-islandske skjaldedigtning (Finnur Jónsson 1912-1915),\n"
    "hämtad från heimskringla.no 2026-10-19. Variantnummer och nottecken kvarstår men faller bort\n"
    "vid tokenisering.\n\n" + hugsvinn)

# --- enheterna -------------------------------------------------------------------------------------
LJODAHATTR = {"Hávamál_gnomisk", "Hávamál_kvinnoråd_Gunnlöd", "Hávamál_Loddfáfnismál",
              "Hávamál_Runatal_Ljóðatal", "Vafþrúðnismál", "Grímnismál", "Skírnismál", "Lokasenna",
              "Alvíssmál", "Sigrdrífumál", "Fjölsvinnsmál", "Sólarljóð", "Hugsvinnsmál"}

enheter = {}
texter = json.load(open(f"{ROT}/utdata/Malt/kallor/edda.json"))
for namn, text in texter.items():
    if namn in ("Hávamál", "Völuspá_in_skamma"):
        continue
    enheter[namn] = tokenisera(stada(text))

DELGRUPP = {"I": "Hávamál_gnomisk", "II": "Hávamál_kvinnoråd_Gunnlöd", "III": "Hávamál_kvinnoråd_Gunnlöd",
            "IV": "Hávamál_Loddfáfnismál", "V": "Hávamál_Runatal_Ljóðatal", "VI": "Hávamál_Runatal_Ljóðatal"}
for r in csv.DictReader(open(f"{ROT}/utdata/Edda/havamal_strofer.csv")):
    enheter.setdefault(DELGRUPP[r["del"]], []).extend(tokenisera(r["text"]))

enheter["Hugsvinnsmál"] = tokenisera(hugsvinn)

with open(f"{ROT}/utdata/Edda/edda_karta_texter.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["namn", "ljodahattr", "n_ord", "text"])
    for namn in sorted(enheter):
        ordlista = enheter[namn]
        if len(ordlista) < MIN_ORD and not namn.startswith("Hávamál_"):
            continue
        w.writerow([namn, int(namn in LJODAHATTR), len(ordlista), " ".join(ordlista)])
        print(f"{namn}: {len(ordlista)} ord{' (ljóðaháttr)' if namn in LJODAHATTR else ''}")
print("\nHugsvinnsmál-slut:", " ".join(enheter["Hugsvinnsmál"][-12:]))
