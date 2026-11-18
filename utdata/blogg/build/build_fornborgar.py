"""Artikeln om fornborgarna (sv + en). Låst plan analysplaner/2026-11-17-fornborgarna.md (e0bd5ea5), resultat
utdata/fornborgar/resultat.json (analys.R), karta utdata/fornborgar/karta.R. Registrets text (Kulturmiljöregistret,
uttag 2026-11-02) i /Volumes/2TB/Antigrvity/Runes/downloads/fornborgar/fornborgar.csv; litteraturen ur sok.sqlite.
    ../../../.venv/bin/python build_fornborgar.py [--write | --update DOC]"""
import csv
import datetime as dt
import io
import json
import os
import re
import sqlite3
import statistics as st
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels  # noqa: E402
from utdata.norge.citat import letters  # noqa: E402

F = os.path.join(ROOT, "utdata", "fornborgar")
R = json.load(open(os.path.join(F, "resultat.json"), encoding="utf-8"))
assert R["sha"] == "e0bd5ea5"
W, G, B = R["water"], R["graves"], R["border"]
assert W["haller"] and not G["haller"] and not B["haller"]
assert W["huvud"]["n"] == 1236 and round(W["huvud"]["u"], 3) == 0.376 and W["p_holm"] < 0.001
assert all(W["halvor"][h]["p"] < 0.001 for h in "AB") and round(W["all_mark"]["u"], 2) == 0.39
IN500 = (100 * W["inom_500m"]["borgar"], 100 * W["inom_500m"]["jamforelse"])
assert [round(v) for v in IN500] == [64, 48]
CLOSER = 100 * (1 - W["huvud"]["u"])
assert round(CLOSER) == 62
assert G["p_holm"] < 0.05 and G["halvor"]["A"]["p"] > 0.05 and G["all_mark"]["p"] > 0.05
assert B["huvud"]["n"] == 322 and B["huvud"]["p"] > 0.3
# the shoreline curve (plan 2026-11-18-fornborgarnas-strandkurva, ba363a4b): AD 450 does NOT fit better than later shores
SK = json.load(open(os.path.join(F, "resultat_strandkurva.json"), encoding="utf-8"))
assert SK["sha"] == "ba363a4b" and not SK["prov"]["K1_idag"]["haller"] and not SK["prov"]["K2_vikingatid"]["haller"]
assert SK["prov"]["K1_idag"]["medel_d"] > 0 and SK["botten"] == 2000

# ---- the register (counted, not tested)
K = list(csv.DictReader(open("/Volumes/2TB/Antigrvity/Runes/downloads/fornborgar/fornborgar.csv", encoding="utf-8")))
assert len(K) == 1304
desc = lambda r: re.sub(r"\s+", " ", r["beskrivning"] or "")  # noqa: E731
area = sorted(float(r["area_m2"]) for r in K if r["area_m2"] not in ("", "NA"))
MED_HA = st.median(area) / 1e4
assert round(MED_HA, 1) == 1.1
N_STUP = sum(1 for r in K if re.search("stup", desc(r), re.I))
N_ING = sum(1 for r in K if re.search("ingång", desc(r), re.I))
N_HUS = sum(1 for r in K if re.search("husgrund", desc(r), re.I))
N_UND = sum(1 for r in K if r["undersokningsstatus"] in ("Delundersökt", "Helt undersökt"))
N_NAMN = sum(1 for r in K if r["lamningsnamn"] not in ("", "NA"))
N_TRAD = sum(1 for r in K if r["tradition"] not in ("", "NA"))
assert (N_STUP, N_ING, N_HUS, N_UND, N_NAMN, N_TRAD) == (703, 563, 46, 73, 292, 79)
BY = {r["lamningsnamn"]: r for r in K if r["lamningsnamn"] not in ("", "NA")}
assert "Ringmuren har ni" in desc(BY["Ismantorps fornborg"]) or "ringmur kring ett närmast runt område" in desc(BY["Ismantorps fornborg"])
assert "Murens omkrets är 411 m" in desc(BY["Ismantorps fornborg"]) and "bevarad höjd vanligen ca 2,5 m" in desc(BY["Ismantorps fornborg"])
assert BY["Eketorps borg"]["undersokningsstatus"] == "Ej undersökt"
HALLE = [r for r in K if "platåberget Halleberg" in desc(r)]
assert len(HALLE) == 1 and round(float(HALLE[0]["area_m2"]) / 1e4) == 1745
TORS = [r for r in K if r["socken"] == "Ardre,Kräklingbo" and "På 12 platser har branten förtäckts med stenmurar" in desc(r)]
assert len(TORS) == 1 and round(float(TORS[0]["area_m2"]) / 1e4) == 124
trad = {r["lamningsnamn"]: re.sub(r"\s+", " ", r["tradition"]) for r in K if r["tradition"] not in ("", "NA")}
assert "kallat Jättetummen. För var gång kyrkklockorna ringde, skulle stenen ha vridit sig" in trad["Stenbyborg"]
assert "skall det har bott en jätte i Bogstensberget" in trad["Bogsten"] and "kastat en sten mot Tumbo kyrka" in trad["Bogsten"]
assert any(r["lamningsnamn"] == "Skansberget" and r["socken"] == "Horn" and "Borgen nyttjades under Dackefejden" in (r["tradition"] or "") for r in K)

# ---- the literature
SOK = sqlite3.connect("/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite")


def jcheck(key, page, *frags):
    text = letters(SOK.execute("select text from pages where key=? and page=?", (key, page)).fetchone()[0])
    for f in frags:
        assert letters(f) in text, (key, page, f)


jcheck("1924_129", 5, "132", "Götalands borgar väsentligen höra till början av folkvandringstiden, omkring 400 e. Kr.",
       "de strider, som utkämpades mellan götar och svear")
jcheck("1932_095", 9, "102", "en del äro tillflyktsorter, andra däremot mera strategiska borgar i mitten av bygden")
jcheck("2011_290", 11, "299", "Fornborgar förekommer ofta nära brobyar eller vid farlederna")
jcheck("2016_184", 4, "186", "muren avgränsade och kontrollerade ett", "område likt gården och inägorna", "frångick Birgitta", "Johansen en traditionell",
       "miniatyrisering av den vardagliga", "Åsa Wall (2002; 2003)", "Södermanlands romartida fornborgar", "hägnade berg",
       "mellersta järnålderns")
jcheck("1965_154", 2, "Den 1964 påbörjade undersökningen av den s. k. Eketorps borg")

# ---- pictures
from PIL import Image  # noqa: E402


def frozen(path):
    buf = io.BytesIO()
    Image.open(path).convert("RGB").save(buf, "PNG", optimize=True)
    return blog_figures.freeze(buf.getvalue())


MAP = {l: frozen(os.path.join(F, f"karta_malardalen_{l}.png")) for l in ("sv", "en")}
IMG = {"sv": f"![Karta: fornborgarna i Mälardalen och vattnet omkring år 450]({MAP['sv']})\nBild: Vitki. Fornborgarna i Mälardalen (röda prickar) och vattnet omkring år 450 enligt SGU:s strandförskjutningsmodell. Mälaren var då en havsvik; skillnaden mot i dag (mörkblått) är här bara några meter i höjd, så den syns mest i vikarnas ändar.",
       "en": f"![Map: the hillforts of the Mälar valley and the water around AD 450]({MAP['en']})\nImage: Vitki. The hillforts of the Mälar valley (red dots) and the water around AD 450 according to SGU's shoreline displacement model. Lake Mälaren was then a bay of the sea; the difference from today (dark blue) is only a few metres of height here, so it shows mostly at the ends of the bays."}


def chart(sv):
    a, b = IN500
    f = (lambda v: f"{v:.0f}")
    return "\n".join([":::chart " + ("Inom 500 meter från vattnet omkring år 450" if sv else "Within 500 metres of the water around AD 450"),
                      f"+{'Fornborgarna' if sv else 'The hillforts'} | {f(a)} | {'1 236 borgar' if sv else '1,236 forts'}",
                      f"{'Berg i dagen runt dem, 0,2–5 km bort' if sv else 'Bare rock around them, 0.2–5 km away'} | {f(b)} | {'tio per borg' if sv else 'ten per fort'}",
                      ("Källa: Riksantikvarieämbetet, Kulturmiljöregistret; SGU, strandförskjutningsmodellen och jordartskartan. Procent. "
                       "Bild: Vitki.") if sv else
                      ("Source: Swedish National Heritage Board, Kulturmiljöregistret; SGU, shoreline displacement model and soil map. "
                       "Per cent. Image: Vitki."), ":::"])


SLUG = "borgarna-som-vaktade-vattnet"
title = "Borgarna som vaktade vattnet – vad var fornborgarna?"
title_en = "The forts that watched the water – what were the hillforts?"
seo_title = "Fornborgar i Sverige: vad var de och vad finns kvar?"
seo_title_en = "Swedish hillforts: what were they, what remains?"
summary = ("Det finns över 1 300 fornborgar i Sverige: stenvallar på bergen från järnålderns mitt. Bara var "
           "tjugonde är utgrävd, och ingen vet säkert vad de var till för. Vi har mätt var de ligger, och svaret är tydligt: "
           "de låg vid vattnet.")
summary_en = ("There are more than 1,300 hillforts in Sweden: stone ramparts on the hills from the middle of the Iron Age. "
              "Only one in twenty has been excavated, and no one knows for certain what they were for. We measured where they "
              "lie, and the answer is clear: they lay by the water.")

pf = lambda v: f"{v:.0f}"  # noqa: E731
body = f"""Den som går i skogen på ett berg i Mälardalen kan plötsligt kliva över en låg vall av sten, tvärs över krönet. Den är för lång för att vara ett röjningsröse och för rak för att vara naturens. Det är en fornborg. Det finns {len(K):,} av dem i Riksantikvarieämbetets register, de flesta i Södermanland, Uppland, Östergötland och Västergötland.

Vad var de? Borgar, säger namnet. Men den som letar efter en borg med torn och portar blir besviken. Det mesta är stenvallar, raserade sedan länge, runt ett bergskrön.

## Vad som finns kvar

Registrets beskrivningar ger en ganska enhetlig bild. Medianborgen innesluter ungefär {MED_HA:.0f} hektar, ett par fotbollsplaner. {N_STUP} av beskrivningarna nämner stup: man byggde där berget redan skyddade, och murade bara där det gick att ta sig upp. {N_ING} beskrivningar nämner en ingång, {N_HUS} spår av husgrunder innanför murarna.

Några är väldiga. Halleberg i Västergötland är ett helt platåberg på över 1 700 hektar, där murarna bara stänger klyftorna. Torsburgen på Gotland omsluter 124 hektar; på tolv ställen har den tio meter höga branten förstärkts med stenmurar. Och på Öland står Ismantorp kvar som det kanske ser ut i fantasin: en ringmur som är 411 meter runt och fortfarande omkring två och en halv meter hög.

## Var de borgar?

Det vet vi mindre om än man skulle tro. Av de {len(K):,} borgarna i registret är bara {N_UND} del- eller helt undersökta enligt registret, och inte ens den siffran går att lita på: Eketorp på Öland står som ”ej undersökt”, fast den grävdes ut från 1964 och framåt (Fornvännen 1965).

Redan 1924 sammanfattade arkeologen Ture J. Arne Bror Schnittgers utgrävningar: ”Götalands borgar väsentligen höra till början av folkvandringstiden, omkring 400 e. Kr.” Han knöt dem till ”de strider, som utkämpades mellan götar och svear” (Fornvännen 1924, s. 132). Sedan dess har tolkningarna gått isär. Somliga var tillflyktsorter dit bygden flydde när fienden kom, andra ”mera strategiska borgar i mitten av bygden”, skrev A. M. Tallgren 1932 (Fornvännen 1932, s. 102). Senare har arkeologerna sökt andra svar än försvaret. Birgitta Johansen såg 1997 borgen som en miniatyr av vardagen: ”muren avgränsade och kontrollerade ett område likt gården och inägorna”. Åsa Wall har kallat Södermanlands borgar, som hon för till romersk järnålder, för ”hägnade berg” (båda återgivna av Anders Bornfalk Back, Fornvännen 2016, s. 186). Borgarna hör alltså till järnålderns mitt, men alla är inte lika gamla.

Ingen av tolkningarna går att avgöra utan att gräva. Men en sak går att mäta: var borgarna ligger.

## De låg vid vattnet

För 1 500 år sedan låg havet flera meter högre än i dag. Mälaren var en havsvik, och många av dagens dalar var sund och vikar. Sveriges geologiska undersökning har räknat ut var stranden gick, århundrade för århundrade. Vi lade borgarna på den strand som gällde omkring år 450, borgarnas egen tid.

{IMG['sv']}

Ett berg ligger ofta nära vatten, så vi jämförde varje borg med tio andra berg i samma trakt, mellan 200 meter och fem kilometer bort. Om borgarna bara låg på berg, utan tanke på vattnet, borde de ligga lika nära vattnet som bergen runt dem.

{chart(True)}

Så var det inte. {pf(IN500[0])} procent av borgarna låg inom 500 meter från dåtidens vatten, mot {pf(IN500[1])} procent av bergen runt dem. I genomsnitt låg en borg närmare vattnet än {pf(CLOSER)} procent av de berg den hade kunnat byggas på. Mönstret är lika tydligt i båda halvorna när vi delar borgarna socken för socken, och det håller också när borgen jämförs med all mark runt den och inte bara med berg. Ett så tydligt mönster skulle uppstå av en slump i färre än ett fall på tusen.

Det stämmer med vad Michael Schneider skrev 2011: ”Fornborgar förekommer ofta nära brobyar eller vid farlederna” (Fornvännen 2011, s. 299). Nu är det mätt för hela landet, mot vattnet som det låg då.

Vad det betyder kan kartan inte säga. Borgarna kan ha vaktat farlederna, som många har tänkt. Men vattnet var också vägen dit: en borg vid stranden var lätt att nå för den som kom med båt, och lätt att fly till.

## Det som inte höll

Vi prövade två saker till. Låg borgarna i den täta bygden, med många gravfält runt sig, eller i utkanten? Det fanns något fler gravfält runt borgarna än runt bergen, men bara i den ena halvan, och inte när vi jämförde med all mark. Det räcker inte. Och låg de vid gränserna mellan de gamla landen, som vakter mellan bygderna? Det gick inte att se: borgarna låg inte närmare gränserna än bergen runt dem. Gränserna på vår karta gäller visserligen vikingatiden, flera hundra år efter borgarna.

## Jättarna och kyrkklockorna

{N_NAMN} av borgarna har ett namn i registret – Gullborg, Rövarborgen, Skansen, Kungsbjär – och {N_TRAD} har en sägen. Där lever en annan historia. I Bogstensberget i Tumbo i Södermanland ska en jätte ha bott, och när kyrkan nyss stod färdig ”kastat en sten mot Tumbo kyrka”. I Stenbyborg på Fogdö finns en sten med ett hål, ”kallat Jättetummen. För var gång kyrkklockorna ringde, skulle stenen ha vridit sig.” Och om Skansberget i Horn i Östergötland sägs bara: ”Borgen nyttjades under Dackefejden.”

Borgarna var redan gamla när kyrkorna byggdes. I sägnerna blev de jättarnas hem, och jättarna tålde inte klockorna. Det är kanske det närmaste vi kommer vad borgarna betydde för dem som levde bredvid dem senare: platser från en tid före den egna, som hörde till någon annan.

:::box Det viktigaste i korthet
- Sverige har över 1 300 fornborgar, de flesta stenvallar på bergskrön från järnålderns mitt. Bara ett par procent är ordentligt utgrävda.
- Borgarna låg vid vattnet. Mätt mot stranden omkring år 450 låg nästan två av tre inom 500 meter från vattnet, mot hälften av bergen runt dem.
- Vi kunde inte se att borgarna låg i den tätaste bygden eller vid gränserna mellan de gamla landen.
- Vad de var till för – tillflykt, makt eller gräns – avgörs inte av läget. Men vattnet hörde till svaret.
:::

## Så säkra är vi

SGU:s strandmodell har en osäkerhet på några meter i höjd och några hundra år i tid, och borgarna är inte alla från samma århundrade; år 450 är ett mittvärde. Vi prövade också, i en egen låst plan, om borgarna passar bättre till stranden omkring år 450 än till senare stränder. Det gör de inte: jämfört med bergen runt omkring ligger de lika nära, ja något närmare, dagens vatten. Närheten till vattnet säger alltså inget om när borgarna byggdes – bara att vattnet var viktigt för dem som byggde. Varje borg är mätt från mitten av sin yta, och de stora borgarna sträcker sig långt ut över berget. Jämförelsebergen är tagna ur SGU:s jordartskarta, som inte täcker Skåne, Halland, Blekinge och Norrland; där räknades borgarna bara med all mark som jämförelse. Registrets uppgift om vilka borgar som är utgrävda är ofullständig. Planen låstes innan något räknades, och den ligger öppet på GitHub tillsammans med koden.

## Se själv

- Vitkis mönsterkarta under Statistik kan visa fornborgarna som ett eget lager, bredvid runstenarna.
- [Runstenarna restes vid sin tids vatten](/forskningsrapporter/runstenarna-vid-sin-tids-vatten/) – samma metod, femhundra år senare.

## Källor

- Riksantikvarieämbetet, Kulturmiljöregistret: alla lämningar av typen fornborg, uttag 2 november 2026. Beskrivningarna och sägnerna citeras kort.
- Sveriges geologiska undersökning, Strandförskjutningsmodell (öppna data), lagret år 1500 före 1950. CC BY 4.0. SGU, Jordarter 1:25 000–1:100 000. CC BY 4.0.
- Arne, Ture J. 1924. Bror Schnittger. *Fornvännen*, s. 129 ff.
- Tallgren, A. M. 1932. Finland vid slutet av hednatiden. *Fornvännen*, s. 95 ff.
- Schneider, Michael 2011. Broby – där hav mötte land. *Fornvännen*, s. 290–305.
- Bornfalk Back, Anders 2016. Konflikt i den arkeologiska rekonstruktionen. *Fornvännen*, s. 184–191. Om Johansen 1997 och Wall 2002–2003.
- Stenberger, Mårten 1965. Nytt från Eketorp. *Fornvännen*.
- Analysplanen och koden: [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-17-fornborgarna.md)."""

body_en = f"""Anyone walking in the forest on a hill in the Mälar valley may suddenly step over a low bank of stones running across the crest. It is too long to be a clearance cairn and too straight to be nature's. It is a hillfort. There are {len(K):,} of them in the Swedish National Heritage Board's register, most of them in Södermanland, Uppland, Östergötland and Västergötland.

What were they? Forts, says the name. But whoever looks for a castle with towers and gates will be disappointed. Most are stone ramparts, long since collapsed, around a hilltop.

## What remains

The register's descriptions give a fairly uniform picture. The median fort encloses about {MED_HA:.0f} hectare, a couple of football pitches. {N_STUP} of the descriptions mention cliffs: people built where the rock already protected them, and walled only where it could be climbed. {N_ING} descriptions mention an entrance, {N_HUS} traces of house foundations inside the walls.

Some are enormous. Halleberg in Västergötland is a whole plateau mountain of more than 1,700 hectares, where the walls only close the clefts. Torsburgen on Gotland encloses 124 hectares; in twelve places the ten-metre cliff has been reinforced with stone walls. And on Öland, Ismantorp still stands as one might imagine it: a ring wall 411 metres round and still about two and a half metres high.

## Were they forts?

We know less about that than you might think. Of the {len(K):,} forts in the register only {N_UND} are partly or fully excavated according to the register, and not even that figure can be trusted: Eketorp on Öland is listed as ”not excavated”, although it was dug from 1964 onwards (Fornvännen 1965).

As early as 1924 the archaeologist Ture J. Arne summed up Bror Schnittger's excavations: the forts of Götaland belong ”essentially to the beginning of the Migration Period, around AD 400”. He linked them to the battles ”fought between Geats and Swedes” (Fornvännen 1924, p. 132). Since then the interpretations have diverged. Some were refuges where the district fled when the enemy came, others ”more strategic forts in the middle of the district”, wrote A. M. Tallgren in 1932 (Fornvännen 1932, p. 102). Later archaeologists have looked for answers other than defence. In 1997 Birgitta Johansen saw the fort as a miniature of everyday life: ”the wall delimited and controlled an area like the farm and the infields”. Åsa Wall has called the forts of Södermanland, which she places in the Roman Iron Age, ”fenced hills” (both as rendered by Anders Bornfalk Back, Fornvännen 2016, p. 186). So the forts belong to the middle of the Iron Age, but they are not all the same age.

None of the interpretations can be settled without digging. But one thing can be measured: where the forts lie.

## They lay by the water

1,500 years ago the sea stood several metres higher than today. Lake Mälaren was a bay of the sea, and many of today's valleys were straits and inlets. The Geological Survey of Sweden has calculated where the shore ran, century by century. We laid the forts on the shore of around AD 450, the forts' own time.

{IMG['en']}

A hill is often near water, so we compared each fort with ten other hills in the same area, between 200 metres and five kilometres away. If the forts simply lay on hills, with no thought for the water, they ought to lie as close to the water as the hills around them.

{chart(False)}

That was not the case. {pf(IN500[0])} per cent of the forts lay within 500 metres of the water of their time, against {pf(IN500[1])} per cent of the hills around them. On average a fort lay closer to the water than {pf(CLOSER)} per cent of the hills it could have been built on. The pattern is just as clear in both halves when we split the forts parish by parish, and it holds also when the fort is compared with all the land around it, not only with hills. A pattern this clear would arise by chance in fewer than one case in a thousand.

That agrees with what Michael Schneider wrote in 2011: hillforts ”often occur near brobyar or by the fairways leading to them” (Fornvännen 2011, p. 299). Now it is measured for the whole country, against the water as it lay then.

What it means the map cannot say. The forts may have watched the fairways, as many have thought. But the water was also the road there: a fort by the shore was easy to reach for those who came by boat, and easy to flee to.

## What did not hold

We tested two more things. Did the forts lie in the dense settlement, with many grave fields around them, or at its edges? There were somewhat more grave fields around the forts than around the hills, but only in one half, and not when we compared with all the land. That is not enough. And did they lie at the borders between the old lands, as guards between districts? It could not be seen: the forts did not lie closer to the borders than the hills around them. The borders on our map belong to the Viking Age, several hundred years after the forts.

## The giants and the church bells

{N_NAMN} of the forts have a name in the register – Gullborg, Rövarborgen (the robbers' fort), Skansen, Kungsbjär – and {N_TRAD} have a legend. Another story lives there. In Bogstensberget in Tumbo in Södermanland a giant is said to have lived, and when the church was newly finished to have ”thrown a stone at Tumbo church”. In Stenbyborg on Fogdö there is a stone with a hole, ”called the Giant's Thumb. Every time the church bells rang, the stone was said to have turned.” And of Skansberget in Horn in Östergötland it is said only: ”The fort was used during the Dacke war.”

The forts were already old when the churches were built. In the legends they became the giants' homes, and the giants could not bear the bells. That is perhaps the closest we come to what the forts meant to those who later lived beside them: places from a time before their own, which belonged to someone else.

:::box The essentials in brief
- Sweden has more than 1,300 hillforts, most of them stone ramparts on hilltops from the middle of the Iron Age. Only a few per cent have been properly excavated.
- The forts lay by the water. Measured against the shore around AD 450, almost two in three lay within 500 metres of the water, against half of the hills around them.
- We could not see that the forts lay in the densest settlement or at the borders between the old lands.
- What they were for – refuge, power or boundary – is not settled by their location. But the water was part of the answer.
:::

## How sure we are

SGU's shoreline model has an uncertainty of a few metres in height and a few hundred years in time, and the forts are not all from the same century; AD 450 is a middle value. We also tested, in a separate locked plan, whether the forts fit the shore of around AD 450 better than later shores. They do not: compared with the hills around them they lie as close to, indeed slightly closer to, today's water. So closeness to the water says nothing about when the forts were built – only that the water mattered to those who built them. Each fort is measured from the middle of its area, and the large forts stretch far across the hill. The comparison hills are taken from SGU's soil map, which does not cover Skåne, Halland, Blekinge and Norrland; there the forts were counted only with all land as the comparison. The register's information on which forts have been excavated is incomplete. The plan was locked before anything was counted, and it is open on GitHub with the code.

## See for yourself

- Vitki's pattern map under Statistics can show the hillforts as a layer of their own, beside the runestones.
- [The runestones were raised by the water of their time](/en/forskningsrapporter/runstenarna-vid-sin-tids-vatten/) – the same method, five hundred years later.

## Sources

- Swedish National Heritage Board, Kulturmiljöregistret: all remains of the type hillfort, extract of 2 November 2026. The descriptions and legends are quoted briefly.
- Geological Survey of Sweden, Shoreline displacement model (open data), the layer for 1500 years before 1950. CC BY 4.0. SGU, Soils 1:25,000–1:100,000. CC BY 4.0.
- Arne, Ture J. 1924. Bror Schnittger. *Fornvännen*, pp. 129 ff.
- Tallgren, A. M. 1932. Finland vid slutet av hednatiden. *Fornvännen*, pp. 95 ff.
- Schneider, Michael 2011. Broby – där hav mötte land. *Fornvännen*, pp. 290–305.
- Bornfalk Back, Anders 2016. Konflikt i den arkeologiska rekonstruktionen. *Fornvännen*, pp. 184–191. On Johansen 1997 and Wall 2002–2003.
- Stenberger, Mårten 1965. Nytt från Eketorp. *Fornvännen*.
- The analysis plan and the code: [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-17-fornborgarna.md)."""

body = body.replace(f"{len(K):,}", f"{len(K):,}".replace(",", " "))
body_en = body_en.replace("Fornborgar förekommer", "Fornborgar förekommer")
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not re.search(r"^\|", b, re.M)
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M))
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index(":::box") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 1 and all(re.match(r"/api/blog/figures/[0-9a-f]{16}\.png$", u) for u in imgs), imgs
    assert not re.search(r"\bAI\b", b)
labels = ["Forskning", "Geografi"]
assert blog_labels.check(labels) is None
assert len(seo_title) <= 52 and len(seo_title_en) <= 52
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "seo_title": seo_title, "seo_title_en": seo_title_en, "labels": labels}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "fornborgar.json"), "w"), ensure_ascii=False, indent=1)
print(len(body.split()), "ord,", len(body_en.split()), "words")

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
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Forskning|fornborgar", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
