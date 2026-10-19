"""Blind sömsökning i Völuspá och Hyndluljóð, med facit.

Samma metod som i Hávamál-artikeln: för varje punkt jämförs de vanligaste ordens fördelning i W strofer
före mot W strofer efter (Burrows' Delta på topp-50, z-poäng över alla glidande W-fönster). Metoden
valideras först mot Hávamál (ska återfinna sömmarna 112 och 138, ingen vid 83-85) och sedan mot
Hyndluljóð, där Völuspá in skamma (strof 29-44) är ett känt främmande block - ett inbyggt facit.
Först därefter läses Völuspás karta. Resultat → somsokning_facit.json.
"""
import csv
import json
import re
import statistics
import sys

ROT = "/Volumes/2TB/Antigrvity/Runes/aagaard-research"
sys.path.insert(0, ROT)
MFW_N = 50

tok = lambda t: re.findall(r"[a-zþðæöøáéíóúýœå]+", t.lower())  # noqa: E731

def strofdela(text):
    """Dela utgåvans löptext i numrerade strofer; numren måste stiga med ett."""
    bitar = re.split(r"\s(\d{1,3})\.\s", " " + text)
    strofer, vantat = {}, 1
    for i in range(1, len(bitar) - 1, 2):
        nr = int(bitar[i])
        if nr == vantat:
            strofer[nr] = bitar[i + 1]
            vantat += 1
        elif nr < vantat and vantat > 1:  # siffra inne i strofen - klistra tillbaka
            strofer[vantat - 1] += f" {bitar[i]}. {bitar[i + 1]}"
    return [strofer[n] for n in sorted(strofer)]

def somkarta(strofer, W):
    """Delta mellan fönstren [p-W, p-1] och [p, p+W-1] för varje p; z-poäng över alla glidande fönster."""
    ordlistor = [tok(s) for s in strofer]
    alla = [w for s in ordlistor for w in s]
    mfw = [w for w, _ in sorted(__import__("collections").Counter(alla).items(),
                                key=lambda kv: -kv[1])[:MFW_N]]
    fonster = []
    for i in range(len(ordlistor) - W + 1):
        ws = [w for s in ordlistor[i:i + W] for w in s]
        n = len(ws)
        c = __import__("collections").Counter(ws)
        fonster.append([c[w] / n for w in mfw])
    mu = [statistics.mean(f[j] for f in fonster) for j in range(MFW_N)]
    sd = [statistics.stdev(f[j] for f in fonster) or 1e-9 for j in range(MFW_N)]
    z = [[(f[j] - mu[j]) / sd[j] for j in range(MFW_N)] for f in fonster]
    kartan = []
    for p in range(W + 1, len(ordlistor) - W + 2):   # p = strofnummer (1-baserat) som inleder efter-fönstret
        za, zb = z[p - 1 - W], z[p - 1]
        kartan.append((p, round(statistics.mean(abs(a - b) for a, b in zip(za, zb)), 3)))
    return sorted(kartan, key=lambda x: -x[1]), dict(kartan)

ut = {}

# --- validering mot Hávamál ------------------------------------------------------------------------
hav = [r["text"] for r in csv.DictReader(open(f"{ROT}/utdata/Edda/havamal_strofer.csv"))]
topp, _ = somkarta(hav, 10)
ut["validering_havamal"] = {"topp8": topp[:8],
                            "facit_112_138_i_topp2": sorted(s for s, _ in topp[:2]) == [112, 138] or
                                                     {s for s, _ in topp[:2]} <= {111, 112, 138, 139, 140},
                            "ingen_som_83_85": not any(83 <= s <= 85 for s, _ in topp[:8])}
print("Hávamál topp-8:", topp[:8])

# --- Hyndluljóð: Völuspá in skamma som facit -------------------------------------------------------
# Guðni Jónssons utgåva trycker skamman som egen text (Hyndluljóð har 34 strofer, inte standardens
# ~50). Vi splitsar in skammans 15 strofer på handskriftsplatsen, efter strof 28 (Guðni-29 "Ber þú
# minnisöl" = standard-45). Facit för den blinda metoden: skarvar vid 29 (in) och 44 (ut).
texter = json.load(open(f"{ROT}/utdata/Malt/kallor/edda.json"))
stada = lambda t: t[re.search(r"\s1\.\s+[\"'«„]?[A-ZÁÉÍÓÚÝÞÆÖÐ]", t).start():]  # noqa: E731
hyndla34 = strofdela(stada(texter["Hyndluljóð"]))
skamma = strofdela(stada(texter["Völuspá_in_skamma"]))
assert len(hyndla34) == 34 and len(skamma) == 15
hyndla = hyndla34[:28] + skamma + hyndla34[28:]

topp34, karta34 = somkarta(hyndla34, 6)
ut["hyndluljod_utan_skamma_W6"] = {"strofer": 34, "topp4": topp34[:4], "vid_snittet_29": karta34.get(29)}
print("Hyndluljóð utan skamma (kontroll) topp-4:", topp34[:4])
for W in (5, 6):
    topp, karta = somkarta(hyndla, W)
    ut[f"hyndluljod_facit_W{W}"] = {"strofer": len(hyndla), "topp6": topp[:6],
                                    "facit_in_29": karta.get(29), "facit_ut_44": karta.get(44),
                                    "facit_i_topp3": {s for s, _ in topp[:3]} >= {29} and
                                                     any(43 <= s <= 45 for s, _ in topp[:6])}
    print(f"Hyndluljóð med skamma W={W} topp-6:", topp[:6], "| in 29:", karta.get(29), "ut 44:", karta.get(44))

# --- Völuspá: kartan läses först efter valideringen ------------------------------------------------
vsp = strofdela(stada(texter["Völuspá"]))
print("Völuspá strofer:", len(vsp))
for W in (8, 10):
    topp, karta = somkarta(vsp, W)
    ut[f"voluspa_W{W}"] = {"strofer": len(vsp), "topp8": topp[:8],
                           "dvergatal_in": karta.get(10), "dvergatal_ut": karta.get(17)}
    print(f"Völuspá W={W} topp-8:", topp[:8])

json.dump(ut, open(f"{ROT}/utdata/Edda/somsokning_facit.json", "w"), ensure_ascii=False, indent=1)
