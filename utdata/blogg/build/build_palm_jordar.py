"""Artikeln om runstenarna och jorden (sv + en): Rune Palms förklaring från 1992 prövad med SGU:s jordartskarta.
Varje tal läses ur utdata/palm_jordarna/resultat.json och diagram.json (låst plan analysplaner/2026-11-08-palm-jordarna.md,
sha 85a70fa3), varje citat kontrolleras mot källans text (utdata/norge/citat.py). Kartan: utdata/palm_jordarna/karta.R.
    ../../../.venv/bin/python build_palm_jordar.py [--write | --update DOC]"""
import datetime as dt
import io
import json
import math
import os
import re
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels  # noqa: E402
from utdata.norge.citat import check  # noqa: E402

PJ = os.path.join(ROOT, "utdata", "palm_jordarna")
R = json.load(open(os.path.join(PJ, "resultat.json"), encoding="utf-8"))
D = json.load(open(os.path.join(PJ, "diagram.json"), encoding="utf-8"))
NO = json.load(open(os.path.join(ROOT, "utdata", "norge", "resultat.json"), encoding="utf-8"))["stones"]
assert R["plan_sha"] == "85a70fa3"

# ---- the numbers ------------------------------------------------------------------------------------------------------
assert (NO["norge"], NO["sverige"]) == (66, 2321)
assert (R["cells"], R["stones"], R["gravefields"], R["lands"]) == (6190, 707, 17781, 36)
P1, P2, P3, P0 = R["P1"], R["P2"], R["P3"], R["P0"]
assert P1["holds"] and P2["holds"] and P3["holds"]
q25, q75 = R["clay_quartiles"]
assert (round(100 * q25), round(100 * q75)) == (2, 38) and round(R["ratio_q75_vs_q25"], 2) == 1.45
assert round(P1["rate_ratio"], 1) == 2.8 and round(P0["rate_ratio"], 1) == 4.0
assert 4000 < 1 / P1["p_one_sided"] < 5000  # "ungefär en gång på 4 700"
ONE_IN_P1 = round(1 / P1["p_one_sided"], -2)
assert ONE_IN_P1 == 4700
assert round(P2["unadjusted"]["ratio"], 1) == 6.5 and round(P2["adjusted"]["ratio"], 1) == 2.4
assert round(100 * P2["explained_share"]) == 52 and P2["adjusted"]["p_one_sided"] < 1e-5
DOUBLE = P3["rate_ratio"] ** math.log(2)
assert round(100 * (1 - DOUBLE)) == 20 and 400 < 1 / P3["p_one_sided"] < 500  # "ungefär en gång på 450"
ONE_IN_P3 = round(1 / P3["p_one_sided"], -1)
assert ONE_IN_P3 == 440
ROB = R["robustness"]
assert all(v["p_one_sided"] < 0.05 and v["rate_ratio"] > 1 for v in ROB.values())
pc = lambda d: round(100 * d["k"] / d["n"])  # noqa: E731
LBL = ["under 10 %", "10–25 %", "25–50 %", "över 50 %"]
assert [pc(D["malar"][k]) for k in LBL] == [7, 13, 16, 19] and [pc(D["gota"][k]) for k in LBL] == [3, 3, 3, 9]
assert D["gota"]["över 50 %"]["n"] == 98
N_KVAR = 834  # runestones not moved or lost in the Viking-age Swedish area (rutor.R prints it)
TOT = NO["sverige"]

# after the test, descriptive (bidrag.R, platsen.py): settlement, clay or water – and on the clay or at its edge?
B = json.load(open(os.path.join(PJ, "bidrag.json"), encoding="utf-8"))
PL = json.load(open(os.path.join(PJ, "platsen.json"), encoding="utf-8"))
ST, OV, GAP = B["steps"], B["overlap"], B["gap"]
assert (round(ST["gravefields"]["ratio"], 1), round(ST["clay"]["ratio"], 2), round(ST["water_near"]["ratio"], 2)) == (2.4, 1.45, 1.42)
assert (ST["gravefields"]["from"], ST["gravefields"]["to"], ST["water_near"]["from_km"], ST["water_near"]["to_km"]) == (1, 4, 1, 0)
plus = lambda x: round(100 * (x - 1))  # noqa: E731
assert [plus(ST[k][f]) for k in ("gravefields", "clay", "water_near") for f in ("ratio", "lo95", "hi95")] == \
    [139, 103, 182, 45, 18, 78, 42, 11, 80]
assert round(OV["cor_clay_logdist"], 2) == -0.10
assert (round(OV["clay_all_or_nothing_with_water"], 2), round(OV["clay_all_or_nothing_without_water"], 2)) == (2.83, 2.71)
assert (round(100 * (1 - OV["water_per_doubling_with_clay"])), round(100 * (1 - OV["water_per_doubling_without_clay"]))) == (20, 19)
SH = GAP["shapley_share"]
assert (round(100 * SH["lgrave"]), round(100 * SH["clay"]), round(100 * SH["ldist"])) == (33, 15, 5)
assert round(100 * GAP["explained_share_total"]) == 52 and round(GAP["unadjusted_ratio"], 1) == 6.5
pct = lambda x: round(100 * x)  # noqa: E731
SO, SR = PL["runstenar"]["observed"], PL["runstenar"]["random_same_cells"]
GO, GR = PL["gravfält"]["observed"], PL["gravfält"]["random_same_cells"]
assert (SO["n"], GO["n"]) == (707, 17781)
assert (pct(SO["on_clay"]), pct(SR["on_clay"]), pct(SO["edge_within_200m"]), pct(SR["edge_within_200m"])) == (28, 37, 52, 40)
assert (pct(GO["on_clay"]), pct(GR["on_clay"]), pct(GO["edge_within_200m"]), pct(GR["edge_within_200m"])) == (16, 29, 50, 36)
dry = lambda d: pct(d["soil"]["morän"] + d["soil"]["berg"] + d["soil"]["sand och grus"])  # noqa: E731
assert (dry(SO), dry(SR), dry(GO), dry(GR)) == (68, 60, 82, 66)
SD, GD = PL["runstenar"]["difference"], PL["gravfält"]["difference"]
assert sorted(pct(-x) for x in SD["on_clay_95"]) == [4, 13] and [pct(x) for x in SD["edge_95"]] == [8, 16]
assert sorted(pct(-x) for x in GD["on_clay_95"]) == [11, 15] and [pct(x) for x in GD["edge_95"]] == [13, 16]
SRG, GRG = PL["runstenar"]["by_region"], PL["gravfält"]["by_region"]
RM, RO, RG = SRG["Mälardalen"], SRG["övriga landskap"], SRG["Götalands inland"]
assert (RM["n"], RO["n"], RG["n"]) == (569, 69, 69)
assert (pct(RO["on_clay"]), pct(RO["on_clay_random"]), pct(RO["edge"]), pct(RO["edge_random"])) == (28, 37, 52, 38)
assert RO["on_clay_diff_95"][1] < 0 < RO["edge_diff_95"][0] and RM["on_clay_diff_95"][1] < 0 < RM["edge_diff_95"][0]
assert RG["on_clay_diff_95"][0] < 0 < RG["on_clay_diff_95"][1] and RG["edge_diff_95"][0] < 0 < RG["edge_diff_95"][1]
assert all(v["on_clay_diff_95"][1] < 0 < v["edge_diff_95"][0] for v in GRG.values()) and len(GRG) == 3

# ---- the quotes, checked against Palm's text (printed page = pdf page − 5) -----------------------------------------
PALM = "text/palm_1992_runor_och_regionalitet.txt"
Q = {
    "s107": ("Den faktor som kanske inverkar mest är att ingen hänsyn tagits till olikheterna i områdenas marktyper, "
             "t ex odlingsbar jord och skog", 112),
    "s255a": ("Runstenarna är ett fenomen knutet till en jordägande klass och de har sina främsta utbredningsområden i "
              "anslutning till de bästa jordarna", 260),
    "s255b": ("En eventuellt lägre jordbrukspotential i runstensområdena i Danmark och Götaland än i runstensområdena i "
              "Svealand kan emellertid inte vara hela förklaringen till de stora skillnaderna i antal och täthet", 260),
    "s255c": ("eliten har så att säga varit bredare", 260),
    "s107b": ("På grund av sin kommunikativa karaktär placerades minnesinskrifter normalt ej i områden utanför den vanliga "
              "samhällssfären", 112),
    "s255d": ("runstensbönder", 260),
    "s259": ("i öster ett expansivt område med utvecklad råvaruhantering och sjöfart", 264),
}
for q, pdf in Q.values():
    check(PALM, q, pdf)
# Ekholm 1950 (Fornvännen 45, s. 137–147), fetched 2026-11-09 to downloads/palm_lit/ekholm1950; printed page = pdf page + 136
EKHOLM = "../palm_lit/ekholm1950/ekholm_1950.txt"
EK = {
    "s140a": ("ligga gravfälten vanligen i omedelbar anslutning till de gamla gårdarna och byarna. Men dessa äro aldrig "
              "uppförda på lermarkerna utan på de moräner, som omge dessa eller ligga som öar på slätten", 4),
    "s140b": ("forntidens samfärdsled", 4),
}
for q, pdf in EK.values():
    check(EKHOLM, q, pdf)


def bild(path: str, alt: str, text: str, max_w: int = 1600) -> str:
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return f"![{alt}]({blog_figures.freeze(out.getvalue())})\n{text}"


KARTA = os.path.join(PJ, "karta_malardalen.png")
IMG = {
    True: bild(KARTA, "Mälardalen: lera och silt, vattnet omkring år 1050 och runstenarna",
               "Mälardalen från Västerås till Östersjön. Gult är lera och silt, ljust är annan jord eller berg, blått är "
               "vatten omkring år 1050 (landhöjningen har sedan dess gjort mycket av Mälarens vikar till land), och de "
               "röda prickarna är runstenar som står kvar på sin ursprungliga plats. Ramen visar inzoomningen längre ned. Karta: Vitki, efter SGU:s "
               "jordartskarta 1:25 000–1:100 000 och strandförskjutningsmodell (båda CC BY 4.0) och Samnordisk "
               "runtextdatabas (ODbL)."),
    False: bild(KARTA, "The Mälaren valley: clay and silt, the water around 1050 and the runestones",
                "The Mälaren valley from Västerås to the Baltic. Yellow is clay and silt, light is other soils or rock, blue "
                "is water around 1050 (land uplift has since turned many of Lake Mälaren's bays into land), and the red "
                "dots are runestones still standing where they were raised. The frame shows the zoomed-in map further down. Map: Vitki, after SGU's soil map 1:25,000–"
                "1:100,000 and shore displacement model (both CC BY 4.0) and the Scandinavian Runic-text Database (ODbL)."),
}


KARTA_Z = os.path.join(PJ, "karta_zoom.png")
IMGZ = {
    True: bild(KARTA_Z, "Täby och Vallentuna: lera, torr mark, vattnet omkring år 1050, gravfält och runstenar",
               "Inzoomning på Täby och Vallentuna i Attundaland, 20 × 20 kilometer – Jarlabankes bygd (ramen på kartan "
               "ovan). Gult är lera och silt, ljust är morän, berg, sand och annan torr mark, blått är vatten omkring år "
               "1050. Rostfärgade prickar är runstenar som står kvar på sin plats, små mörka trianglar är gravfält. Strecket "
               "nere till vänster är två kilometer. Karta: Vitki, efter SGU:s jordartskarta 1:25 000–1:100 000 och "
               "strandförskjutningsmodell (båda CC BY 4.0), Riksantikvarieämbetets kulturmiljöregister och Samnordisk "
               "runtextdatabas (ODbL)."),
    False: bild(KARTA_Z, "Täby and Vallentuna: clay, dry ground, the water around 1050, grave fields and runestones",
                "Zoomed in on Täby and Vallentuna in Attundaland, 20 × 20 kilometres – Jarlabanke's district (the frame on "
                "the map above). Yellow is clay and silt, light is moraine, rock, sand and other dry ground, blue is water "
                "around 1050. Rust-coloured dots are runestones still standing where they were raised, small dark triangles "
                "are grave fields. The bar at the bottom left is two kilometres. Map: Vitki, after SGU's soil map "
                "1:25,000–1:100,000 and shore displacement model (both CC BY 4.0), the Swedish National Heritage Board's "
                "cultural heritage register and the Scandinavian Runic-text Database (ODbL)."),
}


def chart_steps(sv: bool) -> str:
    rows = (("gravefields", "fler gravfält i rutan (från 1 till 4)", "more grave fields in the square (from 1 to 4)"),
            ("clay", "mer lera och silt (från 2 till 38 procent av marken)", "more clay and silt (from 2 to 38 percent of the land)"),
            ("water_near", "närmare vattnet (från en kilometer bort till vid stranden)",
             "closer to the water (from a kilometre away to by the shore)"))
    out = [":::chart " + ("Så många procent fler runstenar, när en sak i taget går från en vanlig låg till en vanlig hög nivå"
                          if sv else "How many percent more runestones, when one thing at a time goes from a common low to a common high level")]
    for k, lsv, len_ in rows:
        d = ST[k]
        out.append(f"{lsv if sv else len_} | {plus(d['ratio'])} | "
                   + (f"95 %-intervall {plus(d['lo95'])}–{plus(d['hi95'])} %" if sv else f"95 % interval {plus(d['lo95'])}–{plus(d['hi95'])} %"))
    out.append(("Källa: Vitkis prov av Palms förklaring, beskrivande jämförelse efter provet. Samma land och allt annat lika; "
                "”vanlig låg” och ”vanlig hög” är gränserna för den fjärdedel av bygderutorna som har minst respektive mest. "
                "Procent. Diagram: Vitki, efter SGU (CC BY 4.0), Kulturmiljöregistret och Rundata (ODbL).") if sv else
               ("Source: Vitki's test of Palm's explanation, descriptive comparison after the test. Same land and everything "
                "else equal; \"common low\" and \"common high\" are the limits of the quarter of settled squares with the least "
                "and the most. Percent. Chart: Vitki, after SGU (CC BY 4.0), the Swedish cultural heritage register and "
                "Rundata (ODbL)."))
    return "\n".join(out) + "\n:::"


def chart_edge(sv: bool) -> str:
    out = [":::chart " + ("Var runstenarna och gravfälten står, jämfört med slumpvisa platser på land i samma rutor"
                          if sv else "Where the runestones and grave fields stand, compared with random places on land in the same squares")]
    for o, r, gsv, gen in ((SO, SR, "Runstenarna", "The runestones"), (GO, GR, "Gravfälten", "The grave fields")):
        out.append("# " + (gsv if sv else gen))
        for val, rnd, lsv, len_ in ((o["on_clay"], r["on_clay"], "på leran", "on the clay"),
                                    (o["edge_within_200m"], r["edge_within_200m"], "vid lerans kant (inom 200 meter)",
                                     "at the edge of the clay (within 200 metres)"),
                                    (None, None, "på torr mark (morän, berg, sand)", "on dry ground (moraine, rock, sand)")):
            v, rv = (pct(val), pct(rnd)) if val is not None else (dry(o), dry(r))
            out.append(f"{lsv if sv else len_} | {v} | " + (f"slumpvisa platser: {rv} %" if sv else f"random places: {rv} %"))
    out.append(("Källa: Vitki, beskrivande mätning efter provet: jorden under 707 runstenar som står kvar och 17 781 gravfält, "
                "mot 50 slumpvisa platser per sten och 5 per gravfält i samma två kilometers ruta; jordartskartan i 100 meters "
                "rutnät. Procent. Diagram: Vitki, efter SGU (CC BY 4.0), Kulturmiljöregistret och Rundata (ODbL).") if sv else
               ("Source: Vitki, descriptive measurement after the test: the soil under 707 runestones still in place and "
                "17,781 grave fields, against 50 random places per stone and 5 per grave field in the same two-kilometre "
                "square; the soil map on a 100-metre grid. Percent. Chart: Vitki, after SGU (CC BY 4.0), the Swedish cultural "
                "heritage register and Rundata (ODbL)."))
    return "\n".join(out) + "\n:::"


def chart(sv: bool) -> str:
    out = [":::chart " + ("Andel bygderutor med minst en runsten, efter hur mycket av marken som är lera och silt" if sv else
                          "Share of settled squares with at least one runestone, by how much of the land is clay and silt")]
    en = {"under 10 %": "under 10 %", "10–25 %": "10–25 %", "25–50 %": "25–50 %", "över 50 %": "over 50 %"}
    for grp, name_sv, name_en in (("malar", "Mälardalen (Uppland, Södermanland, Västmanland)",
                                   "The Mälaren valley (Uppland, Södermanland, Västmanland)"),
                                  ("gota", "Götalands inland (Västergötland, Smålands små land)",
                                   "Inland Götaland (Västergötland, Småland's small lands)")):
        out.append("# " + (name_sv if sv else name_en))
        for k in LBL:
            d = D[grp][k]
            lab = ("lera och silt " + k) if sv else ("clay and silt " + en[k])
            note = f"{d['k']} av {d['n']} rutor" if sv else f"{d['k']} of {d['n']:,} squares"
            out.append(f"{lab} | {pc(d)} | {note}")
    out.append(("Källa: Vitkis prov av Palms förklaring (låst plan 2026-11-08). Bygderutor om 2 × 2 km med minst ett gravfält "
                "och minst en fjärdedel land år 1050; runstenar som står kvar på sin plats. Procent. Diagram: Vitki, efter "
                "SGU (CC BY 4.0), Kulturmiljöregistret och Rundata (ODbL).") if sv else
               ("Source: Vitki's test of Palm's explanation (locked plan 8 November 2026). Settled squares of 2 × 2 km with at "
                "least one grave field and at least a quarter land in 1050; runestones still in place. Percent. Chart: "
                "Vitki, after SGU (CC BY 4.0), the Swedish cultural heritage register and Rundata (ODbL)."))
    return "\n".join(out) + "\n:::"


f1 = lambda x, n=1: f"{x:.{n}f}".replace(".", ",")  # noqa: E731
GH = "https://github.com/Precatio/runes/blob/main"
SLUG = "runstenarna-foljde-leran"
title = "Varför står runstenarna vid lerans kant – och sex gånger tätare i Mälardalen?"
title_en = "Why do the runestones stand at the edge of the clay – and six times as densely around Lake Mälaren?"
summary = ("Rune Palm skrev 1992 att runstenarna står vid de bästa jordarna, men att jorden inte kan förklara hela "
           "skillnaden mellan Mälardalen och resten av Norden. Vi lade SGU:s jordartskarta över varje runsten som står kvar på "
           "sin plats. Stenarna följer bygden, leran och vattnet, var för sig. Men de står inte på leran utan vid dess kant, "
           "på den torra marken där gårdarna och gravarna låg. Och hälften av Mälardalens försprång förklarar ingen av dem.")
summary_en = ("Rune Palm wrote in 1992 that the runestones stand by the best soils, but that the soil cannot explain the whole "
              "difference between the Mälaren valley and the rest of the North. We laid the Swedish soil map over every "
              "runestone still in its place. The stones follow the settlement, the clay and the water, each on its own. But "
              "they do not stand on the clay; they stand at its edge, on the dry ground where the farms and the graves lay. "
              "And half of the Mälaren valley's lead is explained by none of them.")

body = f"""Den som kör genom Uppland ser det utan karta. Runstenarna står där landskapet öppnar sig: vid åkrarna på lerslätten, vid vägen över ån, där gårdarna har legat i tusen år. I skogen mellan bygderna står de nästan aldrig. Det ser självklart ut. Men det betyder inte att det är förklaringen till varför Mälardalen har så många runstenar och resten av Norden så få – Sverige har {TOT:,} vikingatida runstenar i Samnordisk runtextdatabas, Norge {NO['norge']}.

Runologen Rune Palm gav ett svar i sin avhandling *Runor och regionalitet* 1992. Det är två påståenden i samma resonemang, och de drar åt olika håll:

> {Q['s255a'][0]}.

> {Q['s255b'][0]} […]

Jorden förklarar en del, alltså, men inte allt. Resten söker Palm i ekonomin: Mälardalen var enligt arkeologen Åke Hyenstrand, som han citerar, ”{Q['s259'][0]}”. Där hade fler råd att resa sten – ”{Q['s255c'][0]}”, skriver Palm.

Det fanns en sak han inte kunde göra 1992. Han räknade runstenar per tusen hektar och landskap, och skrev själv om svagheten: ”{Q['s107'][0]}”. I dag finns Sveriges geologiska undersöknings jordartskarta öppen, ytbit för ytbit. Så vi gjorde det han inte kunde: lade kartan över varje runsten och frågade om stenarna verkligen följer jorden, hur mycket av Mälardalen jorden förklarar – och om det i så fall är leran som gör det, eller vattnet, eller bygden själv.

## Så mätte vi

Vi delade det vikingatida Sverige i rutor om två gånger två kilometer och behöll de rutor där människor bevisligen bodde under järnåldern: rutor med minst ett registrerat gravfält i Riksantikvarieämbetets kulturmiljöregister, och minst en fjärdedel land på den tiden. Landhöjningen är viktig här – mycket av det som i dag är åker kring Mälaren låg under vatten år 1050, och den marken räknas inte. Det gav {R['cells']:,} bygderutor med {R['gravefields']:,} gravfält och {R['stones']} runstenar.

I varje ruta mätte vi hur stor del av marken som är lera och silt – de fina sedimenten som Mälardalens lerslätter består av – enligt SGU:s karta. Och vi räknade bara runstenar som står kvar där de restes: en sten som flyttats till en kyrka eller ett museum säger inget om jorden den en gång stod på. Det är {N_KVAR} av de {TOT:,}, och det är provets största svaghet; vi återkommer till den.

Sedan jämförde vi rutor inom samma vikingatida land – Attundaland med Attundaland, Västergötland med Västergötland – och med lika många gravfält. Gravfälten är vårt mått på var folk bodde. Frågan blir då inte om runstenarna står där människor fanns, utan om de står på den bästa jorden *bland* de platser där människor fanns. Allt detta bestämde vi och låste i en analysplan innan något räknades.

{IMG[True]}

## Stenarna följer leran

De gör det. Inom samma land och vid lika många gravfält står det fler runstenar där marken är lera och silt. Går man från en ruta där {round(100*q25)} procent av marken är lera till en där {round(100*q75)} procent är det – från en vanlig skogsbygd till en vanlig slättbygd – blir det {f1(R['ratio_q75_vs_q25'], 2)} gånger så många runstenar. Ett så tydligt samband skulle slumpen ge ungefär en gång på {ONE_IN_P1:,.0f}.

Det håller hur vi än vänder på det: med rutor om en och fem kilometer i stället för två, i Mälardalen för sig och i Götalands inland för sig, och med eller utan vattnet i räkningen. Diagrammet visar det enklaste måttet – hur stor andel av bygderutorna som har minst en runsten:

{chart(True)}

## Lera, vatten eller bygd?

Leran är inte det enda som skiljer en ruta från en annan. Vattnet är en annan sak, och bygden själv en tredje. Är det egentligen leran som gör det, eller bara att lerslätterna ligger vid vattnet och att folk bodde där?

Vi kan ställa dem bredvid varandra med samma sorts steg: från en vanlig låg till en vanlig hög nivå – gränsen för den fjärdedel av rutorna som har minst och den fjärdedel som har mest – i samma land och med allt annat lika.

{chart_steps(True)}

Bygden väger tyngst. Där det finns fyra gravfält i rutan i stället för ett står det {f1(ST['gravefields']['ratio'])} gånger så många runstenar. Stenarna står där folk bodde, och där många bodde. Leran och vattnet väger ungefär lika, var för sig: {f1(ST['clay']['ratio'], 2)} gånger för mer lera, {f1(ST['water_near']['ratio'], 1)} gånger för en ruta vid stranden mot en kilometer bort. Intervallen i diagrammet anger var det sanna värdet troligen ligger, och inget av dem når ner till noll procent – ingen skillnad.

Och leran och vattnet är två saker, inte en. I bygderutorna hänger de nästan inte ihop: där det finns mycket lera är det inte närmare till vattnet än där det finns lite (korrelationen är {f1(OV['cor_clay_logdist'], 2).replace('-', '−')}, nästan noll). Lerans samband med stenarna är lika starkt med vattnet i räkningen som utan det – {f1(OV['clay_all_or_nothing_with_water'], 2)} mot {f1(OV['clay_all_or_nothing_without_water'], 2)} gånger från ingen lera till bara lera. Och vattnets är lika starkt med leran som utan den: dubbelt så långt till stranden som den låg år 1050 ger ungefär {round(100*(1-DOUBLE))} procent färre stenar. Ett sådant samband skulle slumpen ge ungefär en gång på {ONE_IN_P3:,.0f}.

## Inte på leran – vid kanten

Rutorna är två kilometer breda. Inuti en ruta kan man fråga något mer precist: står stenen på leran, eller bredvid den? Vi tittade på jorden under varje runsten och varje gravfält och jämförde med slumpvisa platser på land i samma ruta – femtio per sten, fem per gravfält.

De står vid kanten. {pct(SO['on_clay'])} procent av runstenarna står på lera, mot {pct(SR['on_clay'])} procent av de slumpvisa platserna i samma rutor. Men {pct(SO['edge_within_200m'])} procent står inom 200 meter från leran utan att stå på den, mot {pct(SR['edge_within_200m'])}. Gravfälten visar samma sak ännu tydligare: {pct(GO['on_clay'])} procent på leran mot {pct(GR['on_clay'])}, och {pct(GO['edge_within_200m'])} procent vid kanten mot {pct(GR['edge_within_200m'])}. De ligger på morän, berg och sand – den torra marken som höjer sig ur lerslätten. Skillnaderna är inga slumpeffekter: också när vi tar hänsyn till att stenar och gravfält ligger i grupper, genom att dra hela områden om 20 kilometer på nytt, står runstenarna med 95 procents säkerhet mellan {sorted(pct(-x) for x in SD['on_clay_95'])[0]} och {sorted(pct(-x) for x in SD['on_clay_95'])[1]} procentenheter mer sällan på leran än slumpen ger, och mellan {pct(SD['edge_95'][0])} och {pct(SD['edge_95'][1])} oftare vid dess kant.

{chart_edge(True)}

Det gäller inte bara Mälardalen. Gravfälten står vid lerans kant i hela landet: i Mälardalen, i Götalands inland och i de övriga landskapen från Östergötland till Medelpad. Runstenarna gör det i Mälardalen, och i de övriga landskapen – där de flesta står i Östergötland – står {pct(RO['on_clay'])} procent på leran mot {pct(RO['on_clay_random'])} och {pct(RO['edge'])} procent vid kanten mot {pct(RO['edge_random'])}. I Västergötland och Smålands små land pekar de åt samma håll, men där står bara {RG['n']} runstenar kvar på sin plats, för få för att säga något säkert.

Det är ingen ny iakttagelse, och just därför är den värd att mäta. Arkeologen Gunnar Ekholm skrev 1950, med runologen Otto von Friesen som stöd, att det i Uppland är så att det

> […] {EK['s140a'][0]}.

De runstenar som står ute på leran hade enligt Ekholm oftare hört till vägar än till gravfält. Erik Nygren Wåhlin har i en uppsats 2018 ställt Upplands runstenar mot gravfält, vatten och odlingsjord med GIS. Det vi lägger till är mätningen i hela landet, mot slumpvisa platser i samma rutor och med ett mått på hur säker den är. Svaret blir detsamma som Ekholms.

Kartan nedan zoomar in på Täby och Vallentuna, där Jarlabanke och hans släkt reste sina stenar. Det syns utan siffror. Gravfälten ligger som pärlband längs lerdalarnas kanter, och runstenarna står bland dem, nära vattnet som då gick långt in i landet.

{IMGZ[True]}

Det svarar på en fråga som är lätt att missa. Leran var inte där man bodde. Gravarna – och gårdarna, som brukar ligga nära sina gravfält – låg på den torra marken intill, som Ekholm skrev; den som har grävt i Mälardalens lera vet varför. Leran var det man levde av, nedanför gården.

## Varför just leran?

Vad var det då med leran? Här lämnar vi mätningarna och går till tolkningen, och vi gör den med källorna.

Det första är vad leran gav. Lerslätterna kring Mälaren är gammal havsbotten som landhöjningen har lyft upp. Det är jord som håller vatten och näring, och på vikingatiden var mycket av den troligen äng och bete snarare än åker; åkrarna låg ofta på de lättare jordarna närmast gården. ”Äng är åkers moder”, säger ett gammalt svenskt ordspråk. Ängen gav höet, höet förde djuren genom vintern, och djuren gav gödseln till åkern. Djuren var rikedom. Det fornnordiska ordet *fé* betyder både boskap och förmögenhet – samma ord som gav runan ᚠ sitt namn.

Det andra är vem som reste stenarna. Palm skrev att runstenarna är ”ett fenomen knutet till en jordägande klass”. Historikern Birgit Sawyer har läst runstenarna som arvshandlingar: vem som reste stenen efter vem säger något om vem som tog över gården. Arkeologen Torun Zachrisson har i Uppland knutit runstenar och gravfält till gårdarnas gränser och till odalen, släktens rätt till sin jord. Det stämmer med vad vi själva har funnit: runstenar som står kvar ligger i grupper vid gravfälten och nämner samma personer, som en släkts monument ([Runstenarna samlas i familjegrupper vid gravfälten](https://vitkirunor.se/forskningsrapporter/familjegrupper-vid-gravfalten)). Den som hade mer av den goda jorden hade mer att ärva – och mer att markera.

Det tredje är vem stenen talade till. ”{Q['s107b'][0]}”, skriver Palm. En runsten restes för att läsas. Våra egna mätningar visar att hälften av stenarna som står kvar vänder texten mot vägen ([Runstenarna vände texten mot vägen](https://vitkirunor.se/forskningsrapporter/ristningen-vand-mot-vagen)). Vid lerslättens kant möttes gården, vägen och ängen; där gick folk förbi. Och vattnet var tidens stora väg, vilket kan förklara varför närheten till stranden betyder något för sig, oavsett jorden. Ekholm menade att en runsten vid Knivsta restes för att synas från ån, ”{EK['s140b'][0]}”.

Det här är tolkningar. Mätningarna säger var stenarna står. Att det var rikedom, arv och synlighet som styrde är vår läsning tillsammans med Palm, Sawyer och Zachrisson – inte något kartan kan visa.

## Men jorden räcker inte

Det första diagrammet visade också en annan sak. Mälardalens rutor ligger högre än Götalands på varje nivå: också där marken är lika lerig står det fler stenar i Uppland och Södermanland än i Västergötland och Småland.

Räknat i hela modellen har Mälardalens bygder {f1(P2['unadjusted']['ratio'])} gånger så många runstenar per kvadratkilometer som Götalands inland. Tar vi hänsyn till jorden, gravfälten och vattnet återstår {f1(P2['adjusted']['ratio'])} gånger. De tre förklarar alltså ungefär hälften av skillnaden. Hur delar de på den? De hänger ihop – det finns fler gravfält där det finns lera – så vilken man räknar först spelar roll. Vi tog därför medelvärdet över alla ordningar man kan ta in dem i. Bygden står för ungefär en tredjedel av skillnaden ({pct(SH['lgrave'])} procent), leran för {pct(SH['clay'])} procent och vattnet för {pct(SH['ldist'])}. Den andra hälften förklarar ingen av dem. Det är precis vad Palm skrev: jorden kan inte vara hela förklaringen.

## Vad det betyder

Vi visar var stenarna står: i bygden, vid lerans kant, nära vattnet. Den bästa jorden hade de som hade råd att låta resa sten. Men i Mälardalen var de fler än jorden ensam räcker till för att förklara. Där fanns också vattenvägarna, handeln och de yrkesristare som levde av att hugga stenar åt dem som beställde. Eliten var, med Palms ord, bredare: det fanns fler av dem som litteraturforskaren Lars Lönnroth har kallat ”{Q['s255d'][0]}”.

Det gör också Norges få runstenar lättare att förstå. Där är den bästa jorden smala dalgångar och kustremsor. Men jorden förklarar bara en del också där, och resten är samma fråga som i Götaland: vilka fler var det som hade både råd och anledning att resa sten i Mälardalen?

Nästa gång du står vid en runsten i Uppland, se dig om. Ofta står den på en höjning vid kanten av den låga, flacka marken – med gravarna i backen bakom och åkern nedanför, där det för tusen år sedan var äng eller vatten.

## Det som är osäkert

- **Bara stenar som står kvar.** {N_KVAR} av {TOT:,} runstenar står där de restes. Gotland och stora delar av Småland, där nästan alla stenar flyttats till kyrkor, faller i praktiken bort. Om de flyttade stenarna ursprungligen stod på annan jord än de som står kvar kan det ändra bilden.
- **Gravfälten är från hela järnåldern**, inte bara vikingatiden, och inventeringen är ojämn mellan landskapen.
- **Lera i rutan är inte gårdens jord.** Måttet i rutan säger att det finns lera i närheten, inte vilken jord gården brukade. Mätningen vid kanten säger var stenen står, men den är gjord i ett rutnät om 100 meter, så ”inom 200 meter” är ungefärligt.
- **Två jämförelser gjordes efter provet.** Hur bygd, lera och vatten väger mot varandra, och om stenarna står på leran eller vid dess kant, bestämde vi inte i analysplanen. De beskriver; de är inte prövade på samma sätt som huvudresultaten.
- **Jordartskartan är dagens**, och dess kvalitet varierar mellan områden enligt SGU själv.

:::box Det viktigaste i korthet
- Runstenarna står i bygden, vid den bästa jorden och nära vattnet – tre saker som var för sig betyder något. Bygden väger tyngst; leran och vattnet ungefär lika.
- De står inte på leran utan vid dess kant, på den torra marken där gårdarna och gravfälten låg. Det gäller gravfälten i hela landet, och runstenarna överallt där tillräckligt många står kvar för att säga det.
- Bygd, jord och vatten förklarar ungefär hälften av varför Mälardalen har sex gånger tätare med runstenar än Götalands inland. Den andra hälften står kvar, som Rune Palm skrev 1992.
- Varför leran? Ängen och djuren gav rikedom, jorden gick i arv, och stenen restes där folk gick förbi. Det är tolkningar, som vi gör med Palm, Sawyer och Zachrisson.
:::

## Källor

- Palm, R. 1992. *Runor och regionalitet. Studier av variation i de nordiska minnesinskrifterna*. Uppsala: Institutionen för nordiska språk (Runrön 7). Citaten från s. 107 och 255; Hyenstrand 1989 (s. 19) citerad på s. 259 och Lönnroths ”runstensbönder” (1982) på s. 255.
- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, s. 137–147. Citaten från s. 140; där också von Friesen, O. 1913, *Upplands runstenar*.
- Nygren Wåhlin, E. 2018. *Vid gravfält och åkermark. En landskapsanalys av Upplands runstenar*. Kandidatuppsats i arkeologi, Uppsala universitet. [uppsatser.se](https://www.uppsatser.se/uppsats/c198e2d7c4/)
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford: Oxford University Press.
- Zachrisson, T. 1998. *Gård, gräns, gravfält. Sammanhang kring ädelmetalldepåer och runstenar från vikingatid och tidig medeltid i Uppland och Gästrikland*. Stockholm: Arkeologiska institutionen, Stockholms universitet (Stockholm Studies in Archaeology 15).
- Sveriges geologiska undersökning. *Jordarter 1:25 000–1:100 000* (INSPIRE-version) och *Strandförskjutningsmodell*. CC BY 4.0.
- Riksantikvarieämbetet. *Kulturmiljöregistret* (gravfält). Institutet för språk och folkminnen, ortnamnsregistret (socknar och landskap), CC BY.
- Samnordisk runtextdatabas (Rundata), Uppsala universitet, ODbL.
- Vitki 2026. Analysplan: följer runstenarna de bästa jordarna? Låst 2026-11-08. [analysplaner/2026-11-08-palm-jordarna.md]({GH}/analysplaner/2026-11-08-palm-jordarna.md)
- Vitki 2026. Resultat, med jämförelserna efter provet. [utdata/palm_jordarna/resultat.md]({GH}/utdata/palm_jordarna/resultat.md)
- Vitki 2026. *Runstenarna samlas i familjegrupper vid gravfälten* och *Runstenarna vände texten mot vägen*. Forskningsrapporter, [vitkirunor.se/forskningsrapporter](https://vitkirunor.se/forskningsrapporter)."""

body_en = f"""Anyone driving through Uppland sees it without a map. The runestones stand where the landscape opens up: by the fields on the clay plain, by the road across the river, where the farms have lain for a thousand years. In the forest between the settled districts they almost never stand. It looks obvious. But that does not make it the reason why the Mälaren valley has so many runestones and the rest of the North so few – Sweden has {TOT:,} Viking-age runestones in the Scandinavian Runic-text Database, Norway {NO['norge']}.

The runologist Rune Palm gave an answer in his dissertation *Runor och regionalitet* in 1992. It is two claims in the same argument, and they pull in different directions (our translation):

> The runestones are a phenomenon tied to a land-owning class, and their main areas of distribution are close to the best soils.

> A possibly lower agricultural potential in the runestone areas of Denmark and Götaland than in those of Svealand cannot, however, be the whole explanation of the great differences in number and density […]

The soil explains part, then, but not all. Palm looks for the rest in the economy: the Mälaren region was, according to the archaeologist Åke Hyenstrand, whom he quotes, "an expansive area in the east with developed handling of raw materials and seafaring". There, more people could afford to raise a stone – “the elite has, so to speak, been broader”, Palm writes.

There was one thing he could not do in 1992. He counted runestones per thousand hectares and province, and himself named the weakness: "The factor that perhaps matters most is that no account has been taken of the differences in the areas' types of land, e.g. arable land and forest." Today the Geological Survey of Sweden's soil map is open, patch by patch. So we did what he could not: laid the map over every runestone and asked whether the stones really follow the soil, how much of the Mälaren valley the soil explains – and whether it is then the clay that does it, or the water, or the settlement itself.

## How we measured

We divided Viking-age Sweden into squares of two by two kilometres and kept the squares where people demonstrably lived in the Iron Age: squares with at least one registered grave field in the Swedish National Heritage Board's register, and at least a quarter land at the time. Land uplift matters here – much of what is field around Lake Mälaren today lay under water in 1050, and that land is not counted. This gave {R['cells']:,} settled squares with {R['gravefields']:,} grave fields and {R['stones']} runestones.

In each square we measured how much of the land is clay and silt – the fine sediments the clay plains of the Mälaren valley are made of – according to the SGU map. And we counted only runestones still standing where they were raised: a stone moved to a church or a museum says nothing about the soil it once stood on. That is {N_KVAR} of the {TOT:,}, and it is the test's greatest weakness; we return to it.

Then we compared squares within the same Viking-age land – Attundaland with Attundaland, Västergötland with Västergötland – and with as many grave fields. The grave fields are our measure of where people lived. The question is then not whether the runestones stand where people were, but whether they stand on the best soil *among* the places where people were. We decided all of this and locked it in an analysis plan before anything was counted.

{IMG[False]}

## The stones follow the clay

They do. Within the same land and with as many grave fields, more runestones stand where the land is clay and silt. Going from a square where {round(100*q25)} percent of the land is clay to one where {round(100*q75)} percent is – from an ordinary forest district to an ordinary plain – gives {R['ratio_q75_vs_q25']:.2f} times as many runestones. A connection this clear would arise by chance about once in {ONE_IN_P1:,.0f}.

It holds whichever way we turn it: with squares of one and five kilometres instead of two, in the Mälaren valley on its own and in inland Götaland on its own, and with or without the water in the count. The chart shows the simplest measure – how many of the settled squares have at least one runestone:

{chart(False)}

## Clay, water or settlement?

Clay is not the only thing that sets one square apart from another. The water is another, and the settlement itself a third. Is it really the clay that does it, or merely that the clay plains lie by the water and that people lived there?

We can set them side by side with the same kind of step: from a common low to a common high level – the limit of the quarter of squares with the least and the quarter with the most – in the same land and with everything else equal.

{chart_steps(False)}

The settlement weighs most. Where there are four grave fields in the square instead of one, {ST['gravefields']['ratio']:.1f} times as many runestones stand. The stones stand where people lived, and where many lived. The clay and the water weigh about the same, each on its own: {ST['clay']['ratio']:.2f} times for more clay, {ST['water_near']['ratio']:.1f} times for a square by the shore against one a kilometre away. The intervals in the chart give where the true value probably lies, and none of them reaches down to zero percent – no difference.

And the clay and the water are two things, not one. In the settled squares they hardly go together: where there is much clay, the water is no closer than where there is little (the correlation is {f'{OV["cor_clay_logdist"]:.2f}'.replace('-', '−')}, almost zero). The clay's connection with the stones is as strong with the water in the count as without it – {OV['clay_all_or_nothing_with_water']:.2f} against {OV['clay_all_or_nothing_without_water']:.2f} times from no clay to only clay. And the water's is as strong with the clay as without it: twice as far to the shore as it lay in 1050 gives about {round(100*(1-DOUBLE))} percent fewer stones. A connection like that would arise by chance about once in {ONE_IN_P3:,.0f}.

## Not on the clay – at its edge

The squares are two kilometres wide. Inside a square one can ask something more precise: does the stone stand on the clay, or beside it? We looked at the soil under every runestone and every grave field and compared it with random places on land in the same square – fifty per stone, five per grave field.

They stand at the edge. {pct(SO['on_clay'])} percent of the runestones stand on clay, against {pct(SR['on_clay'])} percent of the random places in the same squares. But {pct(SO['edge_within_200m'])} percent stand within 200 metres of the clay without standing on it, against {pct(SR['edge_within_200m'])}. The grave fields show the same thing even more clearly: {pct(GO['on_clay'])} percent on the clay against {pct(GR['on_clay'])}, and {pct(GO['edge_within_200m'])} percent at the edge against {pct(GR['edge_within_200m'])}. They lie on moraine, rock and sand – the dry ground that rises out of the clay plain. The differences are not chance: even when we allow for stones and grave fields lying in groups, by drawing whole areas of 20 kilometres anew, the runestones stand, with 95 percent certainty, between {sorted(pct(-x) for x in SD['on_clay_95'])[0]} and {sorted(pct(-x) for x in SD['on_clay_95'])[1]} percentage points less often on the clay than chance gives, and between {pct(SD['edge_95'][0])} and {pct(SD['edge_95'][1])} more often at its edge.

{chart_edge(False)}

It is not only the Mälaren valley. The grave fields stand at the edge of the clay across the country: in the Mälaren valley, in inland Götaland and in the other provinces from Östergötland to Medelpad. The runestones do so in the Mälaren valley, and in the other provinces – where most of them stand in Östergötland – {pct(RO['on_clay'])} percent stand on the clay against {pct(RO['on_clay_random'])}, and {pct(RO['edge'])} percent at the edge against {pct(RO['edge_random'])}. In Västergötland and Småland's small lands they point the same way, but only {RG['n']} runestones still stand in place there, too few to say anything for certain.

It is not a new observation, and that is exactly why it is worth measuring. The archaeologist Gunnar Ekholm wrote in 1950, with the runologist Otto von Friesen as support, that in Uppland

> […] the grave fields usually lie immediately next to the old farms and villages. But these are never built on the clay lands, but on the moraines that surround them or lie as islands on the plain.

The runestones that stand out on the clay had, according to Ekholm, more often belonged to roads than to grave fields. Erik Nygren Wåhlin set Uppland's runestones against grave fields, water and arable land with GIS in an essay in 2018. What we add is the measurement across the whole country, against random places in the same squares and with a measure of how certain it is. The answer is the same as Ekholm's.

The map below zooms in on Täby and Vallentuna, where Jarlabanke and his kin raised their stones. It shows without numbers. The grave fields lie like strings of beads along the edges of the clay valleys, and the runestones stand among them, near the water that then reached far inland.

{IMGZ[False]}

That answers a question that is easy to miss. The clay was not where people lived. The graves – and the farms, which usually lie close to their grave fields – lay on the dry ground beside it, as Ekholm wrote; anyone who has dug in the clay of the Mälaren valley knows why. The clay was what people lived from, below the farm.

## Why the clay?

What was it, then, about the clay? Here we leave the measurements and turn to interpretation, and we make it with the sources.

The first thing is what the clay gave. The clay plains around Lake Mälaren are old sea floor that the land uplift has raised. It is soil that holds water and nutrients, and in the Viking Age much of it was probably meadow and pasture rather than field; the fields often lay on the lighter soils nearest the farm. "Meadow is the mother of the field", says an old Swedish proverb. The meadow gave the hay, the hay carried the animals through the winter, and the animals gave the dung for the field. The animals were wealth. The Old Norse word *fé* means both livestock and property – the same word that gave the rune ᚠ its name.

The second thing is who raised the stones. Palm wrote that the runestones are "a phenomenon tied to a land-owning class". The historian Birgit Sawyer has read the runestones as records of inheritance: who raised the stone after whom says something about who took over the farm. The archaeologist Torun Zachrisson has, in Uppland, tied runestones and grave fields to the boundaries of farms and to the *odal*, the kin's right to its land. That agrees with what we have found ourselves: runestones still in place lie in groups by the grave fields and name the same people, like a family's monuments ([Runestones gather in family groups by the grave fields](https://vitkirunor.se/en/forskningsrapporter/familjegrupper-vid-gravfalten)). Whoever had more of the good land had more to inherit – and more to mark.

The third thing is whom the stone spoke to. "Because of their communicative character, memorial inscriptions were normally not placed in areas outside the ordinary sphere of society", Palm writes (our translation). A runestone was raised to be read. Our own measurements show that half of the stones still in place turn their text towards the road ([The runestones turned their text towards the road](https://vitkirunor.se/en/forskningsrapporter/ristningen-vand-mot-vagen)). At the edge of the clay plain the farm, the road and the meadow met; that is where people passed. And the water was the great road of the time, which may explain why closeness to the shore matters on its own, whatever the soil. Ekholm thought a runestone at Knivsta was raised to be seen from the river, "the waterway of ancient times".

These are interpretations. The measurements say where the stones stand. That wealth, inheritance and visibility were what steered it is our reading together with Palm, Sawyer and Zachrisson – not something the map can show.

## But the soil is not enough

The first chart also showed something else. The Mälaren valley's squares lie higher than Götaland's at every level: even where the land is just as clayey, more stones stand in Uppland and Södermanland than in Västergötland and Småland.

Counted in the full model, the Mälaren valley's settled districts have {P2['unadjusted']['ratio']:.1f} times as many runestones per square kilometre as inland Götaland. Taking the soil, the grave fields and the water into account, {P2['adjusted']['ratio']:.1f} times remain. The three thus explain roughly half of the difference. How do they share it? They go together – there are more grave fields where there is clay – so which one is counted first matters. We therefore took the average over every order in which they can be brought in. The settlement accounts for about a third of the difference ({pct(SH['lgrave'])} percent), the clay for {pct(SH['clay'])} percent and the water for {pct(SH['ldist'])}. The other half is explained by none of them. That is exactly what Palm wrote: the soil cannot be the whole explanation.

## What it means

We show where the stones stand: in the settled districts, at the edge of the clay, near the water. The best soil belonged to those who could afford to have a stone raised. But in the Mälaren valley they were more than the soil alone can explain. There were also the waterways, the trade and the professional carvers who lived by carving stones for those who commissioned them. The elite was, in Palm's words, broader: there were more of those whom the literary scholar Lars Lönnroth has called *runstensbönder*, "runestone farmers".

It also makes Norway's few runestones easier to understand. There the best soil is narrow valleys and coastal strips. But the soil explains only part there too, and the rest is the same question as in Götaland: who were the many more who had both the means and a reason to raise a stone in the Mälaren valley?

Next time you stand by a runestone in Uppland, look around. Often it stands on a rise at the edge of the low, flat land – with the graves on the slope behind and the field below, where a thousand years ago there was meadow or water.

## What is uncertain

- **Only stones still in place.** {N_KVAR} of {TOT:,} runestones stand where they were raised. Gotland and much of Småland, where almost all stones were moved to churches, practically drop out. If the moved stones originally stood on different soil from those still standing, the picture could change.
- **The grave fields are from the whole Iron Age**, not only the Viking Age, and the survey is uneven between provinces.
- **Clay in the square is not the farm's soil.** The measure in the square says that there is clay nearby, not which soil the farm worked. The measurement at the edge says where the stone stands, but it is made on a 100-metre grid, so "within 200 metres" is approximate.
- **Two comparisons were made after the test.** How settlement, clay and water weigh against each other, and whether the stones stand on the clay or at its edge, we did not set out in the analysis plan. They describe; they are not tested in the same way as the main results.
- **The soil map is today's**, and its quality varies between areas, according to SGU itself.

:::box The essentials in brief
- The runestones stand in the settled districts, by the best soil and near the water – three things that each matter on their own. The settlement weighs most; the clay and the water about the same.
- They do not stand on the clay but at its edge, on the dry ground where the farms and grave fields lay. That holds for the grave fields across the country, and for the runestones wherever enough of them still stand to tell.
- Settlement, soil and water explain roughly half of why the Mälaren valley has runestones six times as densely as inland Götaland. The other half remains, as Rune Palm wrote in 1992.
- Why the clay? The meadows and the animals gave wealth, the land was inherited, and the stone was raised where people passed. These are interpretations, which we make with Palm, Sawyer and Zachrisson.
:::

## Sources

- Palm, R. 1992. *Runor och regionalitet. Studier av variation i de nordiska minnesinskrifterna*. Uppsala: Department of Scandinavian Languages (Runrön 7). Quotations from pp. 107 and 255 (our translations); Hyenstrand 1989 (p. 19) quoted on p. 259 and Lönnroth's *runstensbönder* (1982) on p. 255.
- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, pp. 137–147. Quotations from p. 140 (our translations); there also von Friesen, O. 1913, *Upplands runstenar*.
- Nygren Wåhlin, E. 2018. *Vid gravfält och åkermark. En landskapsanalys av Upplands runstenar*. Bachelor's essay in archaeology, Uppsala University. [uppsatser.se](https://www.uppsatser.se/uppsats/c198e2d7c4/)
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford: Oxford University Press.
- Zachrisson, T. 1998. *Gård, gräns, gravfält. Sammanhang kring ädelmetalldepåer och runstenar från vikingatid och tidig medeltid i Uppland och Gästrikland*. Stockholm: Department of Archaeology, Stockholm University (Stockholm Studies in Archaeology 15).
- Geological Survey of Sweden (SGU). *Jordarter 1:25 000–1:100 000* (INSPIRE version) and *Strandförskjutningsmodell*. CC BY 4.0.
- Swedish National Heritage Board. *Kulturmiljöregistret* (grave fields). Institute for Language and Folklore, place-name register (parishes and provinces), CC BY.
- Scandinavian Runic-text Database (Rundata), Uppsala University, ODbL.
- Vitki 2026. Analysis plan: do the runestones follow the best soils? Locked 8 November 2026 (in Swedish). [analysplaner/2026-11-08-palm-jordarna.md]({GH}/analysplaner/2026-11-08-palm-jordarna.md)
- Vitki 2026. Results, with the comparisons after the test (in Swedish). [utdata/palm_jordarna/resultat.md]({GH}/utdata/palm_jordarna/resultat.md)
- Vitki 2026. *Runestones gather in family groups by the grave fields* and *The runestones turned their text towards the road*. Research reports, [vitkirunor.se/en/forskningsrapporter](https://vitkirunor.se/en/forskningsrapporter)."""

body = re.sub(r"(\d),(\d{3})\b", r"\1 \2", body)  # Swedish thousands: 6 190, not 6,190 (decimals keep their comma)
assert "6 190" in body and "4 700" in body and "2 321" in body and "1,45" in body
for lang, b in (("sv", body), ("en", body_en)):
    assert not re.search(r"^\|", b, re.M), "BlogBody visar inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M))
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index(":::box") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 2 and all(re.match(r"/api/blog/figures/[0-9a-f]{16}\.png$", x) for x in imgs)
    assert "Karta: Vitki" in b or "Map: Vitki" in b
labels = ["Forskning", "Geografi"]
assert blog_labels.check(labels) is None
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
path = os.path.join(ROOT, "utdata", "blogg", "palm_jordar.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", len(body_en.split()), "words")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    else:
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Forskning|palm-jordar", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
