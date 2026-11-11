"""Artikeln om de norska runstenarna (sv + en): varför Norge har så få, Palms förklaring prövad, kvinnorna som mindes,
Ringerikestilen. Varje tal läses ur utdata/norge/resultat.json (låst plan analysplaner/2026-11-07-norska-runstenar.md, sha
e275168c), varje runtext ur Rundata och varje citat ur litteraturen kontrolleras mot källans text
(utdata/norge/citat.py; källorna i /Volumes/2TB/Antigrvity/Runes/downloads/norge_lit/).
    ../../../.venv/bin/python build_norge.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels, commons  # noqa: E402
from utdata.norge.citat import check, letters  # noqa: E402

R = json.load(open(os.path.join(ROOT, "utdata", "norge", "resultat.json"), encoding="utf-8"))
assert R["plan_sha"].startswith("e275168c")
RD = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
IMG = {i["signum"]: i for i in json.load(open(os.path.join(ROOT, "utdata", "blogg", "build", "norge_imgs_kandidater.json"), encoding="utf-8"))}

# ---- the numbers ------------------------------------------------------------------------------------------------------
H1, H2, H3, H4 = R["H1_H3"]["H1"], R["H1_H3"]["H2"], R["H1_H3"]["H3"], R["H4"]
N_NO, N_SE, N_DK = R["stones"]["norge"], R["stones"]["sverige"], R["stones"]["danmark"]
assert (N_NO, N_SE, N_DK) == (66, 2321, 239)
N_U = sum(1 for r in RD.values() if r["signum"].split()[0] == "U" and r.get("period") == "V" and "runsten" in (r.get("object") or "").lower())
assert N_U == 1178
pc = lambda d: round(100 * d["k"] / d["n"])  # noqa: E731
# H1: "had raised"
assert (H1["norge"]["k"], H1["norge"]["n"]) == (1, 66) and H1["norway_hits"] == ["N 233"]
assert pc(H1["sverige"]) == 29 and pc(H1["sverige_tidig"]) == 24 and H1["holds"] and H1["robust"]
assert 1e8 < 1 / H1["test"]["p"] < 2e8  # "färre än ett fall på hundra miljoner"
LOTTO = 6_724_520  # Swedish Lotto, 7 of 35: one row's chance of the top prize
assert round((1 / H1["test"]["p"]) / LOTTO) == 20  # "ungefär tjugo gånger osannolikare"
assert 1e6 < 1 / H1["early"]["p"]  # "färre än ett fall på en miljon"
D1 = H1["descriptive"]
assert (D1["Vg"]["k"], D1["Vg"]["n"]) == (3, 131) and D1["Vg"]["p"] > 0.99
assert "[lé]t gera" in RD["N 233"]["normalization"]  # the only "had" in Norway, and its runes are reconstructed
CH1 = [("Norge", "Norway", H1["norge"]), ("Västergötland", "Västergötland", D1["Vg"]), ("Östergötland", "Östergötland", D1["Ög"]),
       ("Danmark", "Denmark", H1["danmark"]), ("Småland", "Småland", D1["Sm"]), ("Gotland", "Gotland", D1["G"]),
       ("Öland", "Öland", D1["Öl"]), ("Södermanland", "Södermanland", D1["Sö"]), ("Uppland", "Uppland", D1["U"])]
assert [pc(d) for *_, d in CH1] == [2, 2, 9, 10, 15, 17, 19, 23, 41]
assert pc(D1["U"]) == 41  # "fyra stenar av tio"
# H4: the workshops
assert H4["pro_carvers"] == 22 and round(100 * H4["pro_share_sweden"]["share"], 1) == 26.5 and H4["holds"]
assert round(100 * H4["pro_share_had"]["share"]) == 46 and round(100 * H4["pro_share_not_had"]["share"]) == 18
assert round(H4["or_mh"], 1) == 1.6 and H4["strata_used"] == 62 and 2000 < 1 / H4["p"] < 3000
TOP = dict(H4["top_swedish_carvers"])
assert (TOP["Öpir 1"], TOP["Balle"], TOP["Åsmund"], TOP["Fot 2"]) == (112, 76, 74, 68)
assert H4["norway_carvers"] == {}  # Rundata names no carver for any Norwegian runestone
# H2: women remembered
assert (H2["norge"]["k"], H2["norge"]["n"]) == (4, 20) and H2["holds"] and H2["robust"]
assert sorted(H2["norway_hits"]) == ["N 225", "N 251", "N 68", "N A53"]
assert (H2["sverige"]["k"], H2["sverige"]["n"]) == (33, 1067) and pc(H2["sverige"]) == 3 and pc(H2["sverige_tidig"]) == 2
assert 0.003 < H2["test"]["p"] < 0.005 and H2["early"]["p"] < 0.002  # "ungefär fyra fall av tusen", "färre än två"
D2 = H2["descriptive"]
assert (D2["Öl"]["k"], D2["Öl"]["n"]) == (5, 30)
CH2 = [("Norge", "Norway", H2["norge"]), ("Öland", "Öland", D2["Öl"]), ("Danmark", "Denmark", H2["danmark"]),
       ("Västergötland", "Västergötland", D2["Vg"]), ("Östergötland", "Östergötland", D2["Ög"]),
       ("Uppland", "Uppland", D2["U"]), ("Södermanland", "Södermanland", D2["Sö"]), ("Småland", "Småland", D2["Sm"])]
assert [pc(d) for *_, d in CH2] == [20, 17, 5, 5, 3, 2, 2, 2]
# H3: land, which does not hold
assert (H3["norge"]["k"], H3["norge"]["n"]) == (3, 66) and (H3["sverige"]["k"], H3["sverige"]["n"]) == (30, 2321)
assert not H3["holds"] and 0.055 < H3["test"]["p"] < 0.065 and sorted(H3["norway_hits"]) == ["N 210", "N 236", "N 29"]
# Rundata's style groups on the Norwegian stones
STY = {}
for r in RD.values():
    if r["signum"].split()[0] == "N" and r.get("period") == "V" and "runsten" in (r.get("object") or "").lower():
        STY[r.get("style") or "ingen"] = STY.get(r.get("style") or "ingen", 0) + 1
assert (STY["RAK"], STY["ingen"]) == (33, 29)

# ---- the runic texts, as Rundata has them ----------------------------------------------------------------------------
NORM = lambda s: RD[s]["normalization"]  # noqa: E731
for s, frag in (("N 68", "Gunnvôr gerði brú, \"Þrýðríks dóttir, eptir \"Ástríði, dóttur sína. Sú var mær hônnurst á \"Haðalandi."),
                ("N 225", "reisti stein þenna ept \"Ásgerði, kván sína"), ("N 251", "eptir \"Jórunni, konu sína"),
                ("N A53", "fyrir sálu móður sinnar"), ("N 61", "ok fœrði af \"Hringaríki útan ór \"Ulfeyj[u]"),
                ("N 184", "Sá varð dauðr í liði, þá's \"Knútr sótti \"England"), ("N 449", "Tolf vetr hafði kristindómr verit í \"Nóregi"),
                ("N 29", "Þeir \"Finnr ok \"Skopti reistu stein þenna, þá er þeir skiptu lôndum sínum"),
                ("N 210", "á óðali sínu"), ("N 236", "at eign ok at óðli"), ("N 236", "Máli er á steini þessum"), ("N 271", "\"Erlendr reist rúnar þessar §B eptir \"Ôlvi fôður")):
    assert frag in NORM(s), (s, frag)
assert "litu ÷ risa ÷ stin ÷ at ' tuba" in RD["U 1177"]["transliteration"] and RD["U 1177"]["carvers"][0]["name"] == "Öpir 1"
assert RD["N 61"]["parish"] == "Hof sn" and RD["N 84"]["place"] == "Vang" and RD["N A53"]["parish"] == "Sokndal sn"

# ---- the literature, against the sources (pdf page; printed page in the text) ----------------------------------------
PALM, SAW = "text/palm_1992_runor_och_regionalitet.txt", "text/sawyer_1989_tesseract.txt"  # Palm: printed = pdf − 5; Sawyer: pdf + 184
Q_PALM = {
    "s217": "Som framgår av tabell 37a är denna företeelse inte alls belagd i Norge",
    "s221a": ("Det är dock frestande att sätta hjälpverbskonstruktionen i samband med det faktum att det är i de uppländska "
              "runstensområdena som de professionella ristarna tycks ha en alldeles speciell status"),
    "s221b": "Man kunde där på ett annat sätt anförtro utförandet av minnesmärket åt de yrkesverksamma",
    "s227": "I Danmark och Norge samt i de sydligare landskapen i Sverige lyser ristare med sin frånvaro i inskrifterna",
    "s255a": ("Runstenarna är ett fenomen knutet till en jordägande klass och de har sina främsta utbredningsområden i "
              "anslutning till de bästa jordarna"),
    "s255b": "i samband med de topografiska förhållandena och den jämförelsevis lilla jordbruksarealen",
    "s256": ("Behovet av minnesinskrifter i Mälarområdet har varit så stort att en grupp människor har kunnat specialisera "
             "sig på att framställa runstenar"),
    "s257": "Både Danmark och Norge kom tidigare än Sverige under kontroll av monarker",
}
for key, pdf in (("s217", 222), ("s221a", 226), ("s221b", 226), ("s227", 232), ("s255a", 260), ("s255b", 260), ("s256", 261), ("s257", 262)):
    check(PALM, Q_PALM[key], pdf, fuzzy=0.9 if key == "s221a" else None)  # OCR: "ristama" for "ristarna"
assert re.search(r"N\s*orge\s+0\s*/\s*2\s*9", open("/Volumes/2TB/Antigrvity/Runes/downloads/norge_lit/" + PALM, encoding="utf-8").read().split("\f")[222])  # tab. 37a, s. 218
Q_SAW = {"s185": "Från norskt område är endast ca 50 kända",
         "s189a": "På norskt område slog detta mode inte igenom så som på danskt och svenskt",
         "s189b": "vilka i runstensfattiga områden varit onödiga eller fyllts på andra sätt",
         "s190": "i Danmark och Norge något lägre",
         "s191": "Att män och kvinnor reser sten gemensamt är ett bruk, som huvudsakligen är koncentrerat till Uppland, Öland och Södermanland",
         "s192": "i Norge aldrig"}
for key, pdf in (("s185", 1), ("s189a", 5), ("s189b", 5), ("s190", 6), ("s191", 7), ("s192", 8)):
    check(SAW, Q_SAW[key], pdf)
check(SAW, "Andelarna ensamma kvinnliga stenresare är anmärkningsvärt lika i olika delar av Skandinavien", 6)
ALM, KLE, SHE, KNI = ("text/viking_08_1944_almgren_vangstenen.txt", "text/viking_29_1965_kleiber_alstadsteinen.txt",
                      "text/viking_14_1950_shetelig_stilhistorie.txt", "text/knirk_2017_kuli_namn_og_nemne34.txt")
check(ALM, "vilka alla huggits i röd sandsten, hämtad från Ringerike", 86)      # s. 84
check(ALM, "Materialet är en tät, grå glimmerskiffer", 86, fuzzy=0.85)          # s. 84
check(ALM, "i främsta ledet bland Ringerikestilens många högtstående alster", 90, fuzzy=0.85)  # s. 88
check(KLE, "beviste at steinens bergart forefinnes nettopp på Ulvøya", 63)       # s. 63
check(SHE, "Ringerikstilen, best representert ved steinmonumenter", 64)          # s. 60
check(SHE, "en framstilling av Jesusbarnet og de hellige tre konger", 64)
check(KNI, "vart ein av trestokkane i fundamentet årringsdatert til 1034", 2)    # s. 94
check(KNI, "ved å gå ut frå, klokt nok, at brulegginga og reising av runesteinen skjedde samtidig", 2)
check(KNI, "vart vedteke kristne lover på moster-tinget tidleg på 1020-talet", 2)
# Palm s. 223: his own impression of the link, and the bedrock carvings
Q_PALM["s223a"], Q_PALM["s223b"] = "många gånger tycks osäkra", "ett samband mellan kända ristare och förekomsten av hjälpverb"
check(PALM, "Även om attribueringarna många gånger tycks osäkra, kan man ändå se ett samband mellan kända ristare och förekomsten av hjälpverb", 228)
check(PALM, "Hjälpverb är dessutom synnerligen vanligt i ristningar på fast berg", 228)

# ---- the literature review 2026-11 (Fornvännen 1906–2023, Futhark 1–15): text layers in sok.sqlite, page = pdf page ----
# The Fornvännen OCR runs two columns together, so long sentences are checked line by line.
SOK = sqlite3.connect("/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite")


def jcheck(key, page, *frags):
    text = letters(SOK.execute("select text from pages where key=? and page=?", (key, page)).fetchone()[0])
    for f in frags:
        assert letters(f) in text, (key, page, f)


Q_GRA = "de är ju något typiskt för Norge som varken finns i Sverige eller i Danmark vid denna tid"
jcheck("futhark_7_181_1087624", 6, Q_GRA,  # Gräslund 2016, s. 182 (review of Imer & Fortuna)
       "Imer uppger att det finns ca 2300 vikingatida runstenar i Sverige", "ca 260 i Danmark och ca 50 i Norge",
       "politiska, geografiska och demografiska förhållanden tillsammans med tradition och mode",
       "Norge var glest befolkat och att storbönderna uppenbarligen fann andra sätt att uttrycka makt och status")
Q_BAR = "surprise and even astonishment"
jcheck("futhark_3_59_616873", 4, "Over thirty stone inscriptions from that period, complete or fragmentary",  # Barnes 2013, s. 60
       "approximately fifty rune-stones known from Viking Age Norway has over the years caused surprise and even "
       "astonishment in runological circles", "only some 570 km2 in area")
jcheck("2003_litt_d", 3, "runinskrifterna, som uppgår till mer än 1 400", "vilket är ungefär dubbelt så",  # Källström 2003, s. 318
       "från svenskt område under samma pe", "Mellan 800 och 900 av dessa utgörs dess", "som Bergen, Oslo, Trondheim")
jcheck("2014_243", 8, "skilt på Södertörn (fig. 2), hör let hagg(v)a kon",  # Kitzler Åhfeldt 2014, s. 249
       "sekvent samman med ristning i fast block medan", "hio/hiogg hör ihop med resta stenar")
jcheck("2014_243", 9, "Palm (1992, s. 223)")
Q_HAU = "den norske Urnesstilen"
jcheck("1975_245", 4, "med den norske Urnesstilen eller de tusen")  # Hauglid 1975, s. 247
jcheck("futhark_9-10_159_1385974", 2, "Most of these runestones are from the end of the period, dating to the 1000s")  # s. 160

# ---- pictures --------------------------------------------------------------------------------------------------------
for s in ("N 68", "N 251", "N 84", "N 61"):
    assert s in IMG and IMG[s]["licence"].startswith("CC"), s
assert "John Erling Blad" in IMG["N 84"]["author"]
IMG["N 84"] = {**IMG["N 84"], "author": "John Erling Blad"}  # Commons' author field: "Photo and processing © John Erling Blad (jeb) <date>"
PIC = lambda s, lang: commons.markdown(IMG[s], lang)  # noqa: E731

CHART_SV, CHART_EN = "Diagram: Vitki, efter Rundata (ODbL).", "Chart: Vitki, after Rundata (ODbL)."
f_sv = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731


def chart(rows, title, lang, src):
    sv = lang == "sv"
    out = [f":::chart {title}"]
    for i, (a, b, d) in enumerate(rows):
        lab = a if sv else b
        out.append(f"{'+' if i == 0 else ''}{lab} | {pc(d)} | {d['k']} {'av' if sv else 'of'} {f_sv(d['n']) if sv else f'{d[chr(110)]:,}'}")
    out.append(src)
    return "\n".join(out) + "\n:::"


C1_SV = chart(CH1, "Andel runstenar där någon lät resa stenen", "sv",
              "Källa: Samnordisk runtextdatabas (Rundata), vikingatida runstenar; ”lät resa” efter Rundatas översättning "
              f"(”had … raised/made”). Landskap med minst 30 stenar. Procent. {CHART_SV}")
C1_EN = chart(CH1, "Share of runestones where someone had the stone raised", "en",
              "Source: Scandinavian Runic-text Database (Rundata), Viking-age runestones; “had raised” after Rundata's translation "
              f"(“had … raised/made”). Provinces with at least 30 stones. Percent. {CHART_EN}")
C2_SV = chart(CH2, "Andel stenar som minns en kvinna, bland stenar som anger den dödes släktskap", "sv",
              "Källa: Samnordisk runtextdatabas (Rundata), vikingatida runstenar där översättningen anger hur den döde var släkt "
              f"med resaren. Procent. {CHART_SV}")
C2_EN = chart(CH2, "Share of stones remembering a woman, among stones that state the kinship of the dead", "en",
              "Source: Scandinavian Runic-text Database (Rundata), Viking-age runestones whose translation states how the dead "
              f"was related to the raiser. Percent. {CHART_EN}")

SLUG = "varfor-har-norge-bara-66-runstenar"
title = "Varför har Norge bara 66 runstenar – och Sverige 2 300?"
title_en = "Why does Norway have only 66 runestones – and Sweden 2,300?"
summary = ("Rundata har 66 runstenar från vikingatidens Norge och drygt 2 300 från Sverige. Norrmännen skrev nästan aldrig att "
           "de lät resa en sten, och där stenarna blev många, i Mälardalen, gjordes de ofta av yrkesristare åt beställare. Vi "
           "prövar Rune Palms gamla förklaring – och hittar något han inte sökte: de norska stenarna minns kvinnor oftare.")
summary_en = ("Rundata has 66 runestones from Viking-age Norway and more than 2,300 from Sweden. Norwegians almost never wrote "
              "that they had a stone raised, and where the stones became many, in the Mälaren valley, they were often made by "
              "professional carvers for patrons. We test Rune Palm's old explanation – and find something he did not look for: "
              "the Norwegian stones remember women more often.")

body = f"""*Gunnvôr gerði brú, Þrýðríks dóttir, eptir Ástríði, dóttur sína. Sú var mær hônnurst á Haðalandi.*

’Gunnvor, Trydriks dotter, gjorde bron efter Astrid, sin dotter. Hon var den händigaste mön på Hadeland.’

Så står det på Dynnastenen från Hadeland, ristad på 1000-talet. En mor byggde en bro efter sin dotter och ville att alla som gick över den skulle veta vad flickan hade kunnat. Den som läser henne i dag har något ovanligt framför sig, och inte bara för att stenen minns en dotter. En runsten från vikingatidens Norge är i sig sällsynt. I Samnordisk runtextdatabas, Rundata, finns {N_NO} norska runstenar från vikingatiden. Från Sverige finns drygt 2 300, och bara Uppland har {f_sv(N_U)}. Birgit Sawyer skrev redan 1989 att ”Från norskt område är endast ca 50 kända”.

{PIC("N 68", "sv")} Bilden på framsidan visar Jesusbarnet och de tre vise männen.

Den här artikeln frågar varför. Vi har gjort tre saker: läst vad forskningen redan har sagt, prövat en gammal förklaring på hela det svenska materialet och letat efter det som skiljer de norska stenarna från de svenska. Planen låstes innan vi räknade.

## Ingen norrman lät resa sin sten

I Uppland står det oftast att någon *lät* resa stenen. *litu risa stin at tuba*, ’lät resa stenen efter Tobbe’, står det på U 1177 i Harbo, och under texten har ristaren skrivit sitt namn: Öpir. Ordet *lät* rymmer en arbetsdelning, en som beställde och en som högg. Vi har skrivit om hur det skiljer Uppland från Västergötland i [Västgöten reste själv – upplänningen lät resa](/artiklar/reste-sjalv-eller-lat-resa).

På de norska stenarna står det nästan aldrig. Av de {N_NO} stenarna har en enda något som Rundata översätter med ’lät göra’, och just där, på ett fragment från Bore i Rogaland, är de avgörande runorna rekonstruerade. Rune Palm såg det redan 1992 i avhandlingen *Runor och regionalitet*: av 29 norska inskrifter hade ingen hjälpverbet. ”Som framgår av tabell 37a är denna företeelse inte alls belagd i Norge” (s. 217).

{C1_SV}

Av de svenska stenarna har {pc(H1['sverige'])} procent *lät*, och bland dem som Rundata daterar till 1050 eller tidigare, de som ungefär är samtida med de norska, {pc(H1['sverige_tidig'])} procent. En så stor skillnad skulle slumpen ge i färre än ett fall på hundra miljoner – ungefär tjugo gånger osannolikare än högsta vinsten på Lotto med en enda rad. Men diagrammet visar också att Norge inte är ensamt. Västergötland ligger lika lågt, {D1['Vg']['k']} stenar av {D1['Vg']['n']}. Skillnaden går inte mellan rikena utan mellan väst och öst, från Norge och Västergötland till Uppland, där fyra stenar av tio har *lät*.

## Palms förklaring, prövad

Palm hade en förklaring. ”{Q_PALM['s221a']}”, skrev han. ”{Q_PALM['s221b']}.” (s. 221) I väster, menade han, hade beställaren själv ansvaret för stenen: ”{Q_PALM['s227']}” (s. 227).

Han hade också sett ett spår av det i Södermanland. Fast attribueringarna där ”{Q_PALM['s223a']}”, tyckte han sig se ”{Q_PALM['s223b']}”, och han noterade att hjälpverbet är särskilt vanligt i ristningar på fast berg (s. 223). Laila Kitzler Åhfeldt har senare visat att *lét haggva*, ’lät hugga’, i Södermanland hör ihop med ristningar i fast block, medan *hjó*, ’högg’, hör ihop med resta stenar (Fornvännen 2014, s. 249). Vi räknade bara det som Rundata kallar runstenar, inte ristningar i berg och jordfasta block.

Det är en hypotes som går att pröva på hela materialet, och så vitt vi vet har ingen gjort det. Vi räknade de ristare som Rundata knyter till minst tio svenska runstenar. De är {H4['pro_carvers']}, med Öpir ({TOP['Öpir 1']} stenar), Balle ({TOP['Balle']}), Åsmund ({TOP['Åsmund']}) och Fot ({TOP['Fot 2']}) främst, och tillsammans gjorde de ungefär var fjärde svensk runsten. Bland stenar där någon *lät* resa stenen är {round(100 * H4['pro_share_had']['share'])} procent gjorda av en av dem, bland de andra {round(100 * H4['pro_share_not_had']['share'])} procent.

Uppland har både många *lät* och många yrkesristare, och de yngre stenarna har mer av båda. Därför jämförde vi bara stenar i samma landskap och samma stilgrupp, alltså ungefär samma trakt och samma tid, och vägde ihop jämförelserna ({H4['strata_used']} sådana grupper). Sambandet står kvar. När texten säger *lät* är oddsen att stenen gjordes av en yrkesristare 1,6 gånger så höga. Slumpen skulle ge ett så tydligt samband ungefär en gång på 2 600. Palms gissning håller.

I Norge fanns inget sådant yrke att se. Rundata anger ingen ristare för någon av de norska runstenarna, och när en norsk sten själv nämner den som ristade är det ett nytt namn varje gång. På Gjerde i Hordaland gjorde sonen jobbet själv: *Erlendr reist rúnar þessar eptir Ôlvi fôður*, ’Erlend ristade dessa runor efter Ölver, sin far’.

## Varför så få?

Att verkstäderna fanns i Mälardalen förklarar inte ensamt varför Norge har så få stenar, men det passar in i det forskningen redan har föreslagit. Palm igen: ”{Q_PALM['s255a']}”, och det norska materialets litenhet måste sättas ”{Q_PALM['s255b']}” (s. 255). Där efterfrågan var stor kunde ett yrke uppstå: ”{Q_PALM['s256']}” (s. 256). Och han pekar på makten: ”{Q_PALM['s257']}” (s. 257).

Sawyer sa samma sak från andra hållet: ”{Q_SAW['s189a']}”, vilket tyder på att stenresandet fyllt funktioner ”{Q_SAW['s189b']}” (1989, s. 189).

Senare forskare har lagt till fler skäl. Lisbeth Imer räknar i *Danmarks runesten* (2016) med omkring 2 300 vikingatida runstenar i Sverige, 260 i Danmark och 50 i Norge, och förklarar skillnaden med politik, geografi, folkmängd, tradition och mode: Norge var glest befolkat, och storbönderna fann andra sätt att visa makt och status. Det skriver Anne-Sofie Gräslund i sin recension av boken, och hon saknar en sak, stenkorsen: ”{Q_GRA}” (Futhark 7, 2016, s. 182).

Folkmängden förklarar ändå inte allt. Isle of Man är en ö på 570 kvadratkilometer, och där finns över trettio runristade stenar från vikingatiden, hela eller i fragment. Jämförelsen med Norges femtio har enligt Michael Barnes väckt ”{Q_BAR}”, förvåning och till och med häpnad, bland runologerna (Futhark 3, 2013, s. 60).

Norrmännen saknade inte heller runor. Terje Spurkland räknar med mer än 1 400 medeltida runinskrifter i Norge, ungefär dubbelt så många som från Sverige under samma tid, och 800–900 av dem kommer från utgrävningar i städer som Bergen, Oslo och Trondheim (enligt Magnus Källströms recension i Fornvännen 2003, s. 318). Att stenarna är få betyder alltså inte att runorna var det.

De norska stenarna bär kungarnas och missionens tid på ytan. Kulistenen på Nordmøre säger *Tolf vetr hafði kristindómr verit í Nóregi*, ’tolv vintrar hade kristendomen varit i Norge’, och en av stockarna i grunden till bron vid stenen har årringsdaterats till 1034, skriver James Knirk (2017, s. 94). Bron och stenen antas vara samtida, och tolv vintrar före 1034 hamnar man vid tinget på Moster, där kristna lagar enligt Snorre antogs i början av 1020-talet. Galtelandstenen i Agder minns en son som dog i kungens här: *Sá varð dauðr í liði, þá's Knútr sótti England*, ’han dog i hären när Knut anföll England’, alltså 1015–16.

Vårt eget bidrag till frågan är ett samband, inte ett bevis. Där stenarna var många, i Mälardalen, gjordes de ofta av yrkesristare åt beställare som *lät* resa dem. I Norge fanns varken beställarformeln eller yrket. Om det berodde på att efterfrågan saknades, eller på att jorden, kungamakten och kyrkan fyllde samma behov på andra sätt, kan siffrorna inte avgöra.

## Kvinnorna som mindes

Det vi inte letade efter, men hittade, gäller vem stenarna minns. Bland de {H2['norge']['n']} norska stenar där det går att se hur den döde var släkt med resaren minns {H2['norge']['k']} en kvinna. Dynna minns en dotter. På två stenar minns en man sin hustru: Klepp i Rogaland, *reisti stein þenna ept Ásgerði, kván sína*, och Mariakirken i Stavanger, *eptir Jórunni, konu sína*. På Eik i Sokndal byggde Saxe en bro *fyrir sálu móður sinnar*, ’för sin mors själ’. I Sverige gäller det {H2['sverige']['k']} stenar av {f_sv(H2['sverige']['n'])}, {pc(H2['sverige'])} procent, och bland de tidiga svenska stenarna {pc(H2['sverige_tidig'])} procent.

{C2_SV}

Slumpen skulle ge en så stor skillnad i ungefär fyra fall av tusen, och mot de tidiga svenska stenarna i färre än två fall av tusen. Men det är fyra stenar. En sten mer eller mindre flyttar andelen fem procentenheter, och Öland ligger nästan lika högt, {D2['Öl']['k']} av {D2['Öl']['n']}. Mönstret är tydligt nog att se, men inte nog att förklara.

Det står dessutom i en egendomlig kontrast till vilka som reste stenarna. Sawyer visade 1989 att ensamma kvinnliga resare är ”{Q_SAW['s190']}” än genomsnittet (s. 190), och att män och kvinnor som reser sten tillsammans hör hemma i Uppland, Öland och Södermanland men förekommer ”{Q_SAW['s192']}” (s. 191 f.). De norska kvinnorna reste alltså sällan stenar, men de blev ihågkomna oftare. Vi har inte hittat det beskrivet förut. Sawyers bok från 2000, med fler tabeller, har vi dock inte kunnat läsa.

{PIC("N 251", "sv")} Ketill reste stenen efter Jórunn, sin hustru.

## Den röda stenen från Ringerike

Så till stilarna. Rundata använder Anne-Sofie Gräslunds stilgrupper, som är gjorda för Mälardalens djurornamentik, och de passar dåligt på Norge: {STY['RAK']} av de norska stenarna har bara en enkel runslinga utan djurhuvud, och {STY['ingen']} har ingen stil alls. De få ornerade stenarna hör i stället till en stil med namn efter en norsk bygd, Ringerike. Haakon Shetelig kallade den ”Ringerikstilen, best representert ved steinmonumenter” (1950, s. 60), och han nämner just Dynnastenen och dess bild. Bertil Almgren satte Vangstenen i Valdres ”i främsta ledet bland Ringerikestilens många högtstående alster” (1944, s. 88).

{PIC("N 84", "sv")}

Stilen har bokstavligen fått namn efter en sten. De norska ornerade stenarna från 1000-talet är enligt Almgren huggna i ”röd sandsten, hämtad från Ringerike” – utom Vangstenen själv, som är ”en tät, grå glimmerskiffer” (s. 84). Alstadstenen från Toten säger det med egna ord. Jorunn reste den efter sin man *ok fœrði af Hringaríki útan ór Ulfeyju*, ’och förde den ut ur Ringerike, från Ulvøya’, och geologen V. Goldschmidt visade senare att stenens bergart finns just på Ulvøya (Kleiber 1965, s. 63). En änka på 1000-talet fraktade alltså sin sten från Ringerike till Toten för att den skulle vara av rätt sort.

{PIC("N 61", "sv")}

Någon norsk runsten i den senare Urnesstilen, som är så vanlig på upplandsstenarna, har vi inte hittat – fast stilen har fått sitt namn efter stavkyrkan i Urnes i Sogn. Roar Hauglid skiljer just mellan ”{Q_HAU}” och de tusentals svenska runstenarna i samma stil (Fornvännen 1975, s. 247).

## Det som inte höll

Vi trodde också att de norska stenarna oftare skulle tala om jord. Tre gör det. På Nørstebø i Lesja *reistu stein þenna, þá er þeir skiptu lôndum sínum*, ’reste de denna sten när de delade sina jordar’. På Oddernes byggde Eyvind kyrkan *á óðali sínu*, ’på sin odalsjord’. Och på Sele i Rogaland står en överenskommelse, *Máli er á steini þessum*, ’överenskommelsen står på denna sten’, om något som ska höra till någon *at eign ok at óðli*, ’som egendom och som odal’. Men tre av {N_NO} mot {H3['sverige']['k']} av {f_sv(H3['sverige']['n'])} i Sverige räcker inte. En sådan skillnad ger slumpen i ungefär sex fall av hundra, för ofta för att vi ska kalla det ett fynd.

## Svagheterna

De norska stenarna är få, och många är fragment; när mönstret om kvinnorna vilar på fyra stenar kan några nyfynd ändra det. De flesta norska runstenar är från 1000-talet (Haukur Þorgeirsson, Futhark 9–10, 2020, s. 160), men de saknar de svenska stilgrupperna, så vi har inte kunnat hålla tiden konstant som vi brukar; i stället jämförde vi med de svenska stenar som Rundata daterar till 1050 eller tidigare, och båda fynden höll där. Dragen är räknade ur Rundatas engelska översättningar, som är gjorda på samma sätt i alla länder; de norska träffarna har vi läst en och en, de svenska inte. Det var Palm som först såg att norrmännen inte lät resa sina stenar – vårt bidrag är att pröva hans förklaring och fyndet om kvinnorna. Och sambandet mellan *lät* och yrkesristarna visar att de följs åt, inte att det ena orsakade det andra.

Nästa gång du står vid en runsten i Uppland, läs verbet. Står det *litu risa*, ’lät resa’, har någon betalat en ristare. Står det bara att någon reste stenen, gjorde man som man nästan alltid gjorde i Norge – där en änka på Toten fraktade sin sten hela vägen från Ringerike.

:::box Det viktigaste i korthet
- Norrmännen skrev nästan aldrig att de lät resa en runsten; i Uppland gjorde fyra av tio det. Rune Palm såg det 1992, och Västergötland gjorde som Norge.
- Där någon lät resa stenen gjorde en yrkesristare den oftare, också inom samma landskap och tid. Det stöder Palms tanke att verkstäderna hörde Mälardalen till, och kan vara en del av svaret på varför Norge fick så få stenar.
- De norska stenarna minns en kvinna oftare än de svenska: fyra av tjugo. Mönstret är tydligt men vilar på fyra stenar.
- Den röda sandstenen från Ringerike gav en hel stil sitt namn, och en av stenarna säger själv att den kom därifrån.
:::

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Palm, Rune 1992. *Runor och regionalitet. Studier av variation i de nordiska minnesinskrifterna*. Runrön 7. Uppsala. [Fritt på DiVA](https://www.diva-portal.org/smash/record.jsf?pid=diva2:740596).
- Sawyer, Birgit 1989. Det vikingatida runstensresandet i Skandinavien. *Scandia* 55:2, s. 185–202. [Fritt hos Scandia](https://journals.lub.lu.se/scandia/article/view/440).
- Almgren, Bertil 1944. Vangstenen. *Viking* 8.
- Shetelig, Haakon 1950. Religionshistoriske drag fra vikingetidens stilhistorie. *Viking* 14.
- Kleiber, Boris 1965. Alstadsteinen i lyset av nye utgravninger ved Kiev. *Viking* 29.
- Knirk, James E. 2017. Kuli-steinen og landsnamnet Noreg. *Namn og nemne* 34, s. 93 ff.
- Barnes, Michael P. 2013. The Manx Runes and the Supposed Jæren Connection. *Futhark* 3, s. 59–80. [Fri fulltext](https://uu.diva-portal.org/smash/get/diva2:616873/FULLTEXT01.pdf).
- Gräslund, Anne-Sofie 2016. Recension av Lisbeth M. Imer och Roberto Fortuna, *Danmarks runesten: En fortælling* (2016). *Futhark* 7, s. 181–185. [Fri fulltext](https://uu.diva-portal.org/smash/get/diva2:1087624/FULLTEXT01.pdf).
- Hauglid, Roar 1975. Kritikk av Kritikken. *Fornvännen* 70, s. 245–247. [Fri fulltext](https://pub.raa.se/dokumentation/2244ae3f-48da-4cfb-9adb-d4d8080e0a77).
- Kitzler Åhfeldt, Laila 2014. Setu stain, kiarþu merki, risti runaR: tekniska termer i runstensinskrifter från vikingatiden. *Fornvännen* 109, s. 243–258. [Fri fulltext](https://pub.raa.se/dokumentation/2712b668-38f1-4e7c-b57c-2f231df0ac18).
- Källström, Magnus 2003. Recension av Terje Spurkland, *I begynnelsen var fuþark: Norske runer og runeinnskrifter* (2001). *Fornvännen* 98, s. 317–319. [Fri fulltext](https://pub.raa.se/dokumentation/3f802992-ace6-48b9-81fe-e98cc7646a01).
- Þorgeirsson, Haukur 2020. Runic and Skaldic Evidence of Palatal r in West Norse. *Futhark* 9–10, s. 159–177. [doi:10.33063/diva-401047](https://doi.org/10.33063/diva-401047).
- Analysplanen (låst före körningen) och koden finns öppet på [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-07-norska-runstenar.md). Om formlerna inom Sverige: [Västgöten reste själv – upplänningen lät resa](/artiklar/reste-sjalv-eller-lat-resa). Om kvinnorna som resare: [Hon ärvde efter sitt barn](/artiklar/hon-arvde-efter-sitt-barn-kvinnorna-pa-runstenarna).
- Foton: Wikimedia Commons, med fotograf och licens i bildtexterna."""

body_en = f"""*Gunnvôr gerði brú, Þrýðríks dóttir, eptir Ástríði, dóttur sína. Sú var mær hônnurst á Haðalandi.*

‘Gunnvor, Trydrik's daughter, made the bridge in memory of Astrid, her daughter. She was the handiest maiden in Hadeland.’

So reads the Dynna stone from Hadeland, carved in the eleventh century. A mother built a bridge for her daughter and wanted everyone who crossed it to know what the girl could do. Whoever reads it today has something unusual in front of them, and not only because the stone remembers a daughter. A runestone from Viking-age Norway is itself a rarity. The Scandinavian Runic-text Database, Rundata, has {N_NO} Norwegian runestones from the Viking Age. From Sweden it has more than 2,300, and Uppland alone has {N_U:,}. As early as 1989 Birgit Sawyer wrote that only about fifty were known from Norway (“Från norskt område är endast ca 50 kända”).

{PIC("N 68", "en")} The picture on the front shows the Christ Child and the three wise men.

This article asks why. We did three things: read what research has already said, tested an old explanation on the whole Swedish material, and looked for what sets the Norwegian stones apart from the Swedish ones. The plan was locked before we counted.

## No Norwegian had his stone raised

In Uppland the stones most often say that someone *had* the stone raised. *litu risa stin at tuba*, ‘had the stone raised in memory of Tobbi’, reads U 1177 at Harbo, and below the text the carver signed his name: Öpir. The little word *lét*, ‘had’, holds a division of labour: one who ordered and one who carved. We have written about how it sets Uppland apart from Västergötland in [The man from Västergötland raised it himself – the man from Uppland had it raised](/en/artiklar/reste-sjalv-eller-lat-resa).

On the Norwegian stones it is almost never there. Of the {N_NO} stones, a single one has something Rundata translates as ‘had made’, and there, on a fragment from Bore in Rogaland, the decisive runes are reconstructed. Rune Palm saw this in 1992 in his thesis *Runor och regionalitet*: of 29 Norwegian inscriptions, none had the auxiliary verb – “this feature is not attested at all in Norway” (“Som framgår av tabell 37a är denna företeelse inte alls belagd i Norge”, p. 217).

{C1_EN}

Of the Swedish stones {pc(H1['sverige'])} per cent have *lét*, and among those Rundata dates to 1050 or earlier, the ones roughly contemporary with the Norwegian stones, {pc(H1['sverige_tidig'])} per cent. A difference this large would arise by chance in fewer than one case in a hundred million – about twenty times less likely than the top prize on the Swedish Lotto with a single row. But the chart also shows that Norway is not alone. Västergötland is just as low, {D1['Vg']['k']} stones of {D1['Vg']['n']}. The difference does not run between the realms but between west and east, from Norway and Västergötland to Uppland, where four stones in ten have *lét*.

## Palm's explanation, tested

Palm had an explanation. It is “tempting”, he wrote, to link the auxiliary verb to the fact that it is in Uppland's runestone districts that the professional carvers seem to have had a quite special status; there one could entrust the making of the memorial to the professionals (p. 221, our translation). In the west, he thought, the patron himself was responsible for the stone: “In Denmark and Norway and in the more southerly provinces of Sweden, carvers are conspicuously absent from the inscriptions” (p. 227, our translation).

He had also seen a trace of it in Södermanland. Although the attributions there “often seem uncertain”, he thought he could see “a link between known carvers and the occurrence of the auxiliary verb”, and he noted that the auxiliary verb is especially common in carvings on bedrock (p. 223, our translation). Laila Kitzler Åhfeldt later showed that in Södermanland *lét haggva*, ‘had cut’, goes with carvings on fixed blocks, while *hjó*, ‘cut’, goes with raised stones (Fornvännen 2014, p. 249). We counted only what Rundata calls runestones, not carvings on bedrock and earth-fast boulders.

That is a hypothesis that can be tested on the whole material, and as far as we know nobody has. We counted the carvers whom Rundata links to at least ten Swedish runestones. There are {H4['pro_carvers']}, with Öpir ({TOP['Öpir 1']} stones), Balle ({TOP['Balle']}), Åsmund ({TOP['Åsmund']}) and Fot ({TOP['Fot 2']}) at the top, and together they made about one Swedish runestone in four. Among stones where someone *had* the stone raised, {round(100 * H4['pro_share_had']['share'])} per cent were made by one of them; among the others, {round(100 * H4['pro_share_not_had']['share'])} per cent.

Uppland has both many *lét* and many professional carvers, and the younger stones have more of both. So we compared only stones in the same province and the same style group – roughly the same district and the same time – and pooled the comparisons ({H4['strata_used']} such groups). The link remains. When the text says *lét*, the odds that a professional carver made the stone are 1.6 times as high. Chance would give a link this clear about once in 2,600. Palm's guess holds.

In Norway there was no such trade to be seen. Rundata names no carver for any of the Norwegian runestones, and when a Norwegian stone itself names the one who carved it, it is a new name every time. At Gjerde in Hordaland the son did the work himself: *Erlendr reist rúnar þessar eptir Ôlvi fôður*, ‘Erlend carved these runes in memory of Ölver, his father’.

## Why so few?

That the workshops were in the Mälaren valley does not on its own explain why Norway has so few stones, but it fits what research has already proposed. Palm again: runestones are a phenomenon tied to a landowning class, with their main areas next to the best soils, and the smallness of the Norwegian material must be linked to the topography and the comparatively small area of farmland (p. 255). Where demand was great a trade could arise: the need for memorial inscriptions around Lake Mälaren was so great that a group of people could specialise in making runestones (p. 256). And he points to power: Denmark and Norway came under the control of monarchs earlier than Sweden (p. 257).

Sawyer put the same thing from the other side: in Norway “this fashion never caught on as it did in Denmark and Sweden”, which suggests that raising stones filled functions that “in areas poor in runestones were unnecessary or were met in other ways” (1989, p. 189, our translation).

Later scholars have added more reasons. In *Danmarks runesten* (2016) Lisbeth Imer counts about 2,300 Viking-age runestones in Sweden, 260 in Denmark and 50 in Norway, and explains the difference by politics, geography, population, tradition and fashion: Norway was thinly populated, and its big farmers found other ways to show power and status. So writes Anne-Sofie Gräslund in her review of the book, and she misses one thing, the stone crosses, “which are something typical of Norway, found neither in Sweden nor in Denmark at this time” (Futhark 7, 2016, p. 182, our translation).

Population does not explain everything, though. The Isle of Man is an island of 570 square kilometres, and it has over thirty rune-inscribed stones from the Viking Age, complete or fragmentary. The comparison with Norway's fifty has, in Michael Barnes's words, caused “{Q_BAR}” in runological circles (Futhark 3, 2013, p. 60).

Nor did the Norwegians lack runes. Terje Spurkland counts more than 1,400 medieval runic inscriptions in Norway, about twice as many as are known from Sweden in the same period, and 800–900 of them come from excavations in towns such as Bergen, Oslo and Trondheim (according to Magnus Källström's review in Fornvännen 2003, p. 318). That the stones are few does not mean that the runes were.

The Norwegian stones wear the time of kings and mission on their surface. The Kuli stone in Nordmøre says *Tolf vetr hafði kristindómr verit í Nóregi*, ‘Christianity had been twelve winters in Norway’, and one of the logs in the foundation of the bridge by the stone has been tree-ring dated to 1034, writes James Knirk (2017, p. 94). Bridge and stone are assumed to be contemporary, and twelve winters before 1034 brings us to the assembly at Moster, where according to Snorri Christian laws were adopted early in the 1020s. The Galteland stone in Agder remembers a son who died in the king's host: *Sá varð dauðr í liði, þá's Knútr sótti England*, ‘he died in the host when Knut attacked England’ – that is, in 1015–16.

Our own contribution to the question is a link, not a proof. Where the stones were many, in the Mälaren valley, they were often made by professional carvers for patrons who *had* them raised. In Norway there was neither the patron's formula nor the trade. Whether that was because there was no demand, or because land, kingship and church met the same needs in other ways, the numbers cannot tell.

## The women who were remembered

What we did not look for, but found, concerns whom the stones remember. Among the {H2['norge']['n']} Norwegian stones where we can see how the dead was related to the raiser, {H2['norge']['k']} remember a woman. Dynna remembers a daughter. On two stones a man remembers his wife: Klepp in Rogaland, *reisti stein þenna ept Ásgerði, kván sína*, and Mariakirken in Stavanger, *eptir Jórunni, konu sína*. At Eik in Sokndal, Saxi built a bridge *fyrir sálu móður sinnar*, ‘for the soul of his mother’. In Sweden this is true of {H2['sverige']['k']} stones of {H2['sverige']['n']:,}, {pc(H2['sverige'])} per cent, and among the early Swedish stones {pc(H2['sverige_tidig'])} per cent.

{C2_EN}

Chance would give a difference this large in about four cases in a thousand, and against the early Swedish stones in fewer than two in a thousand. But it is four stones. One stone more or less moves the share by five percentage points, and Öland is almost as high, {D2['Öl']['k']} of {D2['Öl']['n']}. The pattern is clear enough to see, but not enough to explain.

It also stands in a strange contrast to who raised the stones. Sawyer showed in 1989 that women as sole raisers are somewhat rarer than average in Denmark and Norway (p. 190), and that men and women raising a stone together belong to Uppland, Öland and Södermanland but occur “in Norway never” (“i Norge aldrig”, pp. 191 f.). Norwegian women thus seldom raised stones, but they were remembered more often. We have not found this described before. Sawyer's book of 2000, with more tables, we have not been able to read, however.

{PIC("N 251", "en")} Ketill raised the stone in memory of Jórunn, his wife.

## The red stone from Ringerike

Now to the styles. Rundata uses Anne-Sofie Gräslund's style groups, made for the animal ornament of the Mälaren valley, and they fit Norway poorly: {STY['RAK']} of the Norwegian stones have only a plain rune band without an animal head, and {STY['ingen']} have no style at all. The few ornamented stones belong instead to a style named after a Norwegian district, Ringerike. Haakon Shetelig called it the Ringerike style, “best represented by stone monuments” (“best representert ved steinmonumenter”, 1950, p. 60), and he names the Dynna stone and its picture. Bertil Almgren placed the Vang stone in Valdres “in the front rank of the Ringerike style's many accomplished works” (1944, p. 88, our translation).

{PIC("N 84", "en")}

The style is quite literally named after a stone. According to Almgren, the ornamented Norwegian stones of the eleventh century are cut from “red sandstone, brought from Ringerike” – except the Vang stone itself, which is “a dense, grey mica schist” (p. 84, our translation). The Alstad stone from Toten says it in its own words. Jorunn raised it in memory of her husband *ok fœrði af Hringaríki útan ór Ulfeyju*, ‘and brought it out of Ringerike, from Ulvøya’, and the geologist V. Goldschmidt later showed that the stone's rock is found precisely on Ulvøya (Kleiber 1965, p. 63). A widow in the eleventh century thus carried her stone from Ringerike to Toten so that it would be of the right kind.

{PIC("N 61", "en")}

A Norwegian runestone in the later Urnes style, so common on the Uppland stones, we have not found – although the style is named after the stave church at Urnes in Sogn. Roar Hauglid distinguishes precisely between “the Norwegian Urnes style” (“{Q_HAU}”) and the thousands of Swedish runestones in the same style (Fornvännen 1975, p. 247).

## What did not hold

We also expected the Norwegian stones to speak of land more often. Three do. At Nørstebø in Lesja, *reistu stein þenna, þá er þeir skiptu lôndum sínum*, ‘they raised this stone when they divided their lands’. At Oddernes, Eyvind built the church *á óðali sínu*, ‘on his allodial land’. And at Sele in Rogaland there is an agreement, *Máli er á steini þessum*, ‘the agreement is on this stone’, about something that is to belong to someone *at eign ok at óðli*, ‘as property and as allodial land’. But three of {N_NO} against {H3['sverige']['k']} of {H3['sverige']['n']:,} in Sweden is not enough. Chance gives a difference like that in about six cases in a hundred, too often for us to call it a finding.

## The weaknesses

The Norwegian stones are few, and many are fragments; when the pattern about women rests on four stones, a few new finds could change it. Most Norwegian runestones date from the eleventh century (Haukur Þorgeirsson, Futhark 9–10, 2020, p. 160), but they lack the Swedish style groups, so we could not hold time constant as we usually do; instead we compared with the Swedish stones Rundata dates to 1050 or earlier, and both findings held there. The features are counted from Rundata's English translations, which are made the same way in every country; the Norwegian hits we read one by one, the Swedish ones not. It was Palm who first saw that Norwegians did not have their stones raised – our contribution is to test his explanation and the finding about women. And the link between *lét* and the professional carvers shows that they go together, not that one caused the other.

Next time you stand by a runestone in Uppland, read the verb. If it says *litu risa*, ‘had raised’, someone paid a carver. If it simply says that someone raised the stone, they did as people nearly always did in Norway – where a widow at Toten carried her stone all the way from Ringerike.

:::box The essentials in brief
- Norwegians almost never wrote that they had a runestone raised; in Uppland four in ten did. Rune Palm saw this in 1992, and Västergötland did as Norway did.
- Where someone had the stone raised, a professional carver made it more often, also within the same province and time. That supports Palm's idea that the workshops belonged to the Mälaren valley, and may be part of the answer to why Norway got so few stones.
- The Norwegian stones remember a woman more often than the Swedish ones: four in twenty. The pattern is clear but rests on four stones.
- The red sandstone from Ringerike gave a whole style its name, and one of the stones says itself that it came from there.
:::

## Sources

- Scandinavian Runic-text Database (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Palm, Rune 1992. *Runor och regionalitet. Studier av variation i de nordiska minnesinskrifterna*. Runrön 7. Uppsala. [Open on DiVA](https://www.diva-portal.org/smash/record.jsf?pid=diva2:740596).
- Sawyer, Birgit 1989. Det vikingatida runstensresandet i Skandinavien. *Scandia* 55:2, pp. 185–202. [Open at Scandia](https://journals.lub.lu.se/scandia/article/view/440).
- Almgren, Bertil 1944. Vangstenen. *Viking* 8.
- Shetelig, Haakon 1950. Religionshistoriske drag fra vikingetidens stilhistorie. *Viking* 14.
- Kleiber, Boris 1965. Alstadsteinen i lyset av nye utgravninger ved Kiev. *Viking* 29.
- Knirk, James E. 2017. Kuli-steinen og landsnamnet Noreg. *Namn og nemne* 34, pp. 93 ff.
- Barnes, Michael P. 2013. The Manx Runes and the Supposed Jæren Connection. *Futhark* 3, pp. 59–80. [Free full text](https://uu.diva-portal.org/smash/get/diva2:616873/FULLTEXT01.pdf).
- Gräslund, Anne-Sofie 2016. Review of Lisbeth M. Imer and Roberto Fortuna, *Danmarks runesten: En fortælling* (2016). *Futhark* 7, pp. 181–185. [Free full text](https://uu.diva-portal.org/smash/get/diva2:1087624/FULLTEXT01.pdf).
- Hauglid, Roar 1975. Kritikk av Kritikken. *Fornvännen* 70, pp. 245–247. [Free full text](https://pub.raa.se/dokumentation/2244ae3f-48da-4cfb-9adb-d4d8080e0a77).
- Kitzler Åhfeldt, Laila 2014. Setu stain, kiarþu merki, risti runaR: tekniska termer i runstensinskrifter från vikingatiden. *Fornvännen* 109, pp. 243–258. [Free full text](https://pub.raa.se/dokumentation/2712b668-38f1-4e7c-b57c-2f231df0ac18).
- Källström, Magnus 2003. Review of Terje Spurkland, *I begynnelsen var fuþark: Norske runer og runeinnskrifter* (2001). *Fornvännen* 98, pp. 317–319. [Free full text](https://pub.raa.se/dokumentation/3f802992-ace6-48b9-81fe-e98cc7646a01).
- Þorgeirsson, Haukur 2020. Runic and Skaldic Evidence of Palatal r in West Norse. *Futhark* 9–10, pp. 159–177. [doi:10.33063/diva-401047](https://doi.org/10.33063/diva-401047).
- The analysis plan (locked before the run) and the code are open on [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-07-norska-runstenar.md). On the formulas within Sweden: [The man from Västergötland raised it himself](/en/artiklar/reste-sjalv-eller-lat-resa). On women as raisers: [She inherited from her child](/en/artiklar/hon-arvde-efter-sitt-barn-kvinnorna-pa-runstenarna).
- Photos: Wikimedia Commons, with photographer and licence in the captions."""

# ---- checks ----------------------------------------------------------------------------------------------------------
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index(":::box") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 4 and all(re.match(r"https://(upload|thumb)\.wikimedia\.org/", u) for u in imgs), imgs  # what BlogBody shows
for s in ("Dynna", "Gjerde", "Kuli", "Galteland", "Nørstebø", "Oddernes", "Sele", "Alstad", "Vang"):
    assert s in body and s in body_en, s
labels = ["Forskning", "Norden", "Ristare", "Kvinnor och barn", "Datering och stil"]
assert blog_labels.check(labels) is None
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
path = os.path.join(ROOT, "utdata", "blogg", "norge.json")
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
                 "topic": "Forskning|norge", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
