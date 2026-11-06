"""Artikeln "De gamla landen: Värend – sjöbygden mitt i skogen" (sv + en), en del i serien De gamla landen i seriens
atmosfäriska form (Viktor 2026-11-04). Värend omkring år 1000: sjöbygden, byarna, gravarna, hövdingen och tinget (Hanssons
hypotetiska modell), lagsagan, järnet och vägarna, tron. Varje uppgift är ett ordagrant citat ur källorna i
/Volumes/2TB/Antigrvity/Runes/downloads/smaland_lit (NOTES.md, insamlat 2026-11-04) och kontrolleras nedan som en delsträng
av källans text med blanktecknen sammanslagna. Kartan: utdata/gamla_landen/karta_land.R med varend.json.
    ../../../.venv/bin/python build_varend.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, commons  # noqa: E402

LIT = "/Volumes/2TB/Antigrvity/Runes/downloads/smaland_lit/"
_txt = {}


def said(fil, quote):
    if fil not in _txt:
        _txt[fil] = " ".join(open(LIT + fil, encoding="utf-8").read().split())
    assert " ".join(quote.split()) in _txt[fil], (fil, quote)


H, ING, BERG, BOL, LYA = ("Hansson1999_renjagare_col.txt", "LstG_Ingelstad_col.txt", "LstG_Bergkvara_col.txt",
                          "LstG_Bolmso_col.txt", "LstG_Lyasa-Stromhult_col.txt")
HAR, FV25, VXO, ALM, BEN = ("KLM_Harensas_col.txt", "Fv2025_Hennius_blastugn_col.txt", "LstG_Vaxjo_col.txt",
                            "Almquist1954_Lagsagor_del1.txt", "LstG_Benestad_col.txt")
FACTS = [
    (H, "Bebyggelsen låg under hela järnåldern i de centrala delarna, mellan och runt sjöarna Salen, Åsnen, Helgasjön, Örken och Rottnen"),
    (H, "Hela östra och södra delarna av Värend verkar i princip sakna fast bebyggelse"),
    (H, "Bebyggelseutvecklingen i Värend framstår som oerhört kontinuerlig."),
    (ING, "Området domineras visserligen av barr- och blandskogar men i relation till länets randbygder har miljön mellanbygdens karaktär med öppna jordbruksarealer"),
    (BERG, "Bergkvara och Växjö ingår i den centralbygd som sträcker sig från Helgasjön till sjön Åsnen, och som under medeltiden utgjorde huvudbygd i folklandet Värend."),
    (BOL, "Geografiskt är centralbygderna i Värend knutna till låga moränhöjder i anslutning till de stora sjöarna medan Finnvedens i högre grad varit mer knutna till ådalarna och isälvssedimenten."),
    (H, "Namnet Värend kan också mycket väl vara så gammalt."),
    (ING, "Ingelstad hade på medeltiden inte mindre än 10 gårdar."), (ING, "Byarna ha varit stora med minst 5-6 gårdar, ofta fler."),
    (H, "Utifrån 14C-analyser att döma, verkar bandparcellerna byggas ut från 500-talet och framåt."),
    (H, "De många tegarna i Sävsjö gör att här bör ha funnits flera gårdar, troligen en by."),
    (LYA, "boskapsskötseln hade en något starkare ställning i de perifera områdena medan åkerbruket i gengäld hade en starkare profil i centralbygden"),
    (H, "Det som egentligen karaktäriserar gravskicket i Värend är variationen på gravformer."),
    (H, "I Värend förekommer de så typiska ovala stensättningarna främst i östra Värend, inte minst i Uppvidinge härad."),
    (H, "Gravfälten i västra Värend består däremot av runda stensättningar och resta stenar."),
    (H, "Det varierade gravskicket i Värend har däremot klara paralleller i Blekinge, norra Skåne och Halland."),
    (HAR, "Få gravfält från denna tid har undersökts med moderna arkeologiska metoder."),
    (H, "Inglinge hög, 35 meter i diameter och sex meter hög"), (H, "När det gäller Inglinge hög är en datering till yngre järnålder mest sannolik."),
    (ING, "Gravfältet har en rik flora av gravformer så som högar, ovala stensättningar, treuddar och resta stenar."),
    (H, "En sådan ryttargrav undersöktes 1940 vid Benestad herrgård söder om Alvesta."),
    (ING, "På en udde i Helgasjön låg Thiudby"), (ING, "på den plats där Biskopsgården Kronoberg uppfördes på 1300talet"),
    (H, "Den döde hade bland annat fått med sig sin sköld, betsel och en ryktskrapa i graven."),
    (H, "Bland de brända benen i brandlagret fanns sammanlagt 31 pärlor, de flesta av glas och glasfluss, men här fanns också pärlor av agat och bergkristall samt två silverpärlor."),
    (H, "Den aktuella graven visar att hedniska brandbegravningar fortfarande skedde under 1000talet, kanske även mot dess slut."),
    (H, "Exemplen från Kånna och Benestad visar hur ett ”kristet” och hedniskt gravskick levde sida vid sida under en tid."),
    (H, "Värend hyser sannolikt landets största koncentration av gravrösen från denna period."),
    (H, "järnframställningsplatser, men från och med vikingatid börjar järnframställningen att tillta."),
    (H, "Den huvudsakliga mängden av de järnframställningsplatser som hittats i de småländska skogarna är dock lämningar efter en medeltida produktion."),
    (H, "I Kronobergs län hittas järnframställningsplatser framför allt i Älghult, Åseda och Lessebo socknar i öster"),
    (FV25, "Från och med tidig medeltid ökade produktionen markant"),
    (H, "en tolkning varit att fyndet varit ett varulager som tappats av en kringresande gotländsk handelsman på sin färd över sjön Furen."),
    (VXO, "Det var en naturlig plats där den låg vid sjön i gränsen mellan Kinnevalds, Konga och Norrvidinge härad."),
    (H, "i Värends hjärta Växjö – sjön vid vägamotet"),
    (H, "De småländska runstenarna, i Tiohärad ca 90 kända, är direkt knutna till den vikingatida bebyggelsen och resta i anslutning till gravfält och vägar."),
    (H, "Hövdingasätet låg i Ingelstad, medan några av följeslagarna var bosatta i Rinkaby och Tegnaby ett par kilometer norrut."),
    (H, "Värend framstår som ett typexempel på hur ett landskap hypotetiskt kunde vara organiserat."),
    (H, "norrut låg kultplatsen, Hov, och Thiudby, där tinget var beläget."),
    (ING, "anses ha haft en funktion som tingsplats för ”kungadömet” Värend."),
    (H, "Växjö, som under medeltiden växte fram som Värends centrum, blev ingen centralort förrän kyrkan och biskopsdömet etablerades här under 1100-talet"),
    (VXO, "Växjö var tidigt redan under förhistorisk tid en samlings- och marknadsplats för människorna från Värend."),
    (H, "I det centrala Värend har man Hov, Växjö, Helgö, Helgasjön och ett nu försvunnet Tuna som kan rekonstrueras ur namnet Tunatorp i Öjaby."),
    (H, "medan Huseby i Skatelöv socken är den enda husabybyn i Värend."),
    (H, "var ett faktum redan under yngre järnålder. Snarare utgjorde Värend och Finnveden vid denna tid en form av egna"),
    (ALM, "omfattande de tre landen Finnveden, Värend och Njudung"), (ALM, "Dessförinnan torde namnet hava varit Värends lagsaga"),
    (ALM, "har påpekats, att Värend ursprungligen måste hava bestått av fyra härad"), (ALM, "Detta måste dock hava skett före 1266"),
    (ALM, "som förmodligen nedskrivits under 1200-talets senare hälft, men av vilken numera endast kyrkobalken finnes bevarad."),
    (H, "Namnen är viktiga källor till vår kunskap om den förkristna kulten, eftersom de visar vilka gudar som dyrkats (Frö, Oden och Tor)"),
    (ING, "de hedniskt-sakrala ortnamnen Torsås och Torsjö"), (H, "Kulten verkar ha varit knuten direkt till enskilda hövdingamiljöer"),
    (H, "medan bönen dominerar klart i Värend"),
    (BEN, "Fascinerad av sägnerna om sköldmön Blända och hennes bragder i forna strider mot danskarna"),
]
for fil, q in FACTS:
    said(fil, q)

# ---- picture and map --------------------------------------------------------------------------------------------------
FI = "Inglinge Hog a burial mound (150424061).jpg"
INFO = commons.commons_info([FI])
assert INFO[FI]["licence"] == "CC BY-SA 2.0" and INFO[FI]["author"].startswith("Jerzy Kociatkiewicz")
LIC = f"[{INFO[FI]['licence']}]({INFO[FI]['licence_url']})" if INFO[FI].get("licence_url") else INFO[FI]["licence"]
PAGE = "https://commons.wikimedia.org/wiki/File:" + FI.replace(" ", "_")
MAP = {lang: blog_figures.freeze(open(os.path.join(ROOT, "utdata", "gamla_landen", f"karta_varend_{lang}.png"), "rb").read())
       for lang in ("sv", "en")}

title = "De gamla landen: Värend – sjöbygden mitt i skogen"
summary = ("Värend var det största av Smålands små land: en bygd kring sjöarna Helgasjön, Salen och Åsnen, omgiven av skog åt "
           "alla håll. Där låg stora byar, en storhög vid Ingelstad och kanske ett ting vid Helgasjön. Följ med dit omkring år "
           "1000. En del i serien De gamla landen.")

body = f"""Till Värend kommer man för tusen år sedan genom skogen, för det finns ingen annan väg. Skogen står tät, marken är stenig, och det är långt mellan människorna. Men så öppnar sig landskapet. Mellan låga moränhöjder blänker sjöarna – Helgasjön, Salen, Åsnen, Örken, Rottnen – och på höjderna kring dem ligger åkrar, ängar och gårdar. Det är här folk har bott, i de mittersta delarna av landet, under hela järnåldern, och så länge att forskarna kallar bygden ovanligt kontinuerlig. Den östra och södra delen av Värend ligger nästan tom. Där tar skogen över.

Namnet Värend kan vara mycket gammalt, kanske lika gammalt som bronsåldern. Det är ett land som har haft tid att bli sig självt.

## Byarna vid sjöarna

I centralbygden kring sjöarna är byarna stora, med minst fem eller sex gårdar, ofta fler. Ingelstad har på medeltiden tio gårdar. Kring Bergkvara, längre söderut, är byarna mindre, fyra eller fem gårdar. Vid Sävsjö i norra Värend har man hittat långa, smala tegar som började anläggas på 500-talet – spåren av flera gårdar som delade på marken, troligen en by som höll på att formas.

Föreställ dig en sådan by en höstdag: röken från husen, säden som bärgas på åkrarna kring sjön, korna som drivs hem från skogen. Det är åkern som betyder mest här i mitten av landet. Ute i randbygderna, där skogen är närmare, är det boskapen.

## De döda

Gravarna i Värend är inte lika varandra. Det som utmärker bygden är just variationen. I östra Värend, inte minst i Uppvidinge, lägger man de döda under ovala stensättningar, i västra under runda stensättningar och resta stenar. Gravskicket liknar det i Blekinge, norra Skåne och Halland, inte det i Mälardalen. Värend vände sig söderut och västerut. Få av gravfälten från den här tiden har undersökts med moderna metoder, så mycket är fortfarande okänt.

Vid Ingelstad, söder om Växjö, reser sig Inglinge hög, trettiofem meter bred och sex meter hög, troligen från yngre järnålder. Runt den ligger ett gravfält med högar, ovala stensättningar, treuddar och resta stenar. Vid Benestad söder om Alvesta har man grävt ut en ryttargrav: en man som bränts och fått med sig sin sköld, sitt betsel och en ryktskrapa för hästen. Där har man också hittat en kvinnas grav, med trettioen pärlor bland de brända benen, de flesta av glas men några av agat och bergkristall och två av silver. Den graven visar att man fortfarande brände sina döda på det gamla sättet under 1000-talet, kanske ända mot dess slut, samtidigt som andra döda lades i jorden på det kristna sättet. En tid levde de två sederna sida vid sida.

![Inglinge hög vid Ingelstad]({INFO[FI]['thumb']})
Inglinge hög vid Ingelstad. Foto: Jerzy Kociatkiewicz, {LIC}, via [Wikimedia Commons]({PAGE}).

De stora stenrösena som Värend är känt för är mycket äldre. Värend har troligen landets största samling av gravrösen från bronsåldern. Den som levde här omkring år 1000 gick bland dem som bland något redan uråldrigt.

## Hövdingen och tinget

Hur var landet styrt? Arkeologen Martin Hansson har föreslagit en bild, och han kallar den själv hypotetisk. Hövdingen satt i Ingelstad, vid den stora högen. Några av hans följeslagare bodde i Rinkaby och Tegnaby, ett par kilometer norrut. Ännu längre norrut låg kultplatsen Hov och Thiudby, där tinget hölls – på udden i Helgasjön där biskoparna långt senare byggde borgen Kronoberg. Ortnamnen i centrala Värend pekar mot samma trakt: Hov, Växjö, Helgö, Helgasjön och ett försvunnet Tuna. Länsstyrelsen skriver att Thiudby anses ha varit tingsplats för ”kungadömet” Värend.

Det är en tolkning, men den bygger på något som Hansson menar är säkert: att Värend och Finnveden redan under yngre järnålder var egna riken, med en gräns mellan sig. På medeltiden var Värend en del av en lagsaga som omfattade tre land, Finnveden, Värend och Njudung. Lagsagan hade tidigare hetat Värends lagsaga. Landet hade då fyra härader, och när ett av dem delades fick lagsagan namnet Tiohärad, före 1266. Lagen skrevs ner under 1200-talets senare hälft, men bara kyrkobalken finns kvar.

![Karta över Värend omkring år 1000 med runstenarna och platserna i texten]({MAP['sv']})
**Karta.** Värend omkring år 1000. Rostfärgat är Värend, ljust grannlanden; gränserna är ungefärliga. Grå punkter är runstenar, ringar platser i texten. Karta: Vitki, efter SGU:s modell för strandförskjutningen år 1000, Institutet för språk och folkminnens ortnamnsregister och Rundata.

## Vägarna, järnet och sjöarna

Växjö ligger där tre härader möts, och namnet betyder ungefär sjön vid vägamötet. Men om Växjö var en samlingsplats redan före kristendomen är omstritt. Länsstyrelsen skriver att det var en marknadsplats redan i förhistorisk tid. Hansson menar att Växjö blev en centralort först när kyrkan och biskopen kom på 1100-talet. Kungamakten har lämnat få spår: Huseby i Skatelöv är den enda husaby-byn i Värend.

Runstenarna står vid gravfälten och vägarna. I hela Tiohärad finns omkring nittio, och på Värends stenar är det bönen som dominerar, inte korset. Och i skogarna öster om sjöarna, i Älghult, Åseda och Lessebo, ligger platser där man framställde järn. Från vikingatiden börjar den tillverkningen att öka, men det mesta som hittats är medeltida; produktionen tog fart på allvar först i början av medeltiden.

Sjöarna var vägar. I sjön Furen har man hittat ett fynd som har tolkats som varulagret efter en gotländsk handelsman som reste genom Värend, från 1000- eller 1100-talet. Föreställ dig båten som välte, lasten som sjönk, och mannen som kanske tog sig i land.

## Tron

Ortnamnen minns gudarna: Frö, Oden och Tor. Nära Inglinge hög ligger Torsås och Torsjö. Kulten verkar ha varit knuten till hövdingarnas gårdar. Namnen Helgasjön och Helgö betyder kanske inte ”helig” utan ”fredad”, enligt ortnamnsforskaren Staffan Fridell. Och sägnen om sköldmön Blända, som slog danskarna, är en lärd berättelse från 1600-talet, inte historia.

## Ett land kring sjöarna

Värend omkring år 1000 är ett land mitt i skogen. Det har sina byar kring sjöarna, sina storhögar och sitt ting, och det vänder sig söderut, mot Blekinge och Skåne, mer än mot Mälardalen. Det ska ännu dröja innan kyrkan och biskopen gör Växjö till landets centrum. Den som står vid Inglinge hög och ser ut över sjöbygden ser ett land som redan är gammalt.

## Så vet vi det

Landskapet, byarna, gravarna och centralplatserna bygger på Martin Hanssons arkeologiska historia om södra Småland (1999) och på länsstyrelsen i Kronobergs läns beskrivningar av Ingelstad, Växjö, Bergkvara och andra miljöer; lagsagan på Jan Eric Almquists *Lagsagor och domsagor*. Värend saknar en volym i *Det medeltida Sverige*. Bilden av en hövding i Ingelstad och ett ting vid Thiudby är en tolkning, som författaren själv kallar hypotetisk, och om Växjö var en förhistorisk marknadsplats är omstritt. Lagen och lagsagan är kända från medeltiden. Länkarna till källorna finns nedan.

## Källor

- Hansson, Martin 1999. Från renjägare till viking. En arkeologisk historia om södra Småland. I: Johansson (red.) *Landen kring sjöarna*. Kronobergsboken 1999/2000. Med faktarutor av Christer Knutsson (runinskrifterna) och Staffan Fridell (ortnamnen).
- Almquist, Jan Eric 1954. *Lagsagor och domsagor i Sverige* I. Stockholm.
- Hennius, Andreas m.fl. 2025. Järnframställning i blästugn – en uppdaterad kronologi. *Fornvännen* 120.
- Länsstyrelsen i Kronobergs län: fördjupade beskrivningar av riksintressena Ingelstad (2014), Växjö (2009), Bergkvara (2016), Lyåsa-Strömhult (2016), Benestad-Blädinge-Oby-Näs (2014) och Bolmsö kyrkby (2015).
- Wahlberg Traneskog, Tove 2024. *Invid ett gravfält i Härensås*. Kalmar läns museum, rapport 2024:23.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License. Institutet för språk och folkminnen, ortnamnsregistret, CC BY. Sveriges geologiska undersökning, strandförskjutningsmodell (kartan).
- Bild: Wikimedia Commons, med fotografen och licensen i bildtexten."""

title_en = "The old lands: Värend – the lake country in the middle of the forest"
summary_en = ("Värend was the largest of Småland's small lands: a district round the lakes Helgasjön, Salen and Åsnen, surrounded by "
              "forest on every side. There lay large villages, a great mound at Ingelstad and perhaps an assembly by Helgasjön. "
              "Come along around AD 1000. A part of the series The old lands.")

body_en = f"""A thousand years ago the only way into Värend is through the forest. The forest stands close, the ground is stony, and people are few and far between. But then the landscape opens. Between low moraine heights the lakes gleam – Helgasjön, Salen, Åsnen, Örken, Rottnen – and on the heights around them lie fields, meadows and farms. This is where people have lived, in the middle of the land, throughout the Iron Age, and for so long that researchers call the settlement unusually continuous. The eastern and southern parts of Värend lie almost empty. There the forest takes over.

The name Värend may be very old, perhaps as old as the Bronze Age. It is a land that has had time to become itself.

## The villages by the lakes

In the central district round the lakes the villages are large, with at least five or six farms, often more. Ingelstad has ten farms in the Middle Ages. Around Bergkvara, further south, the villages are smaller, four or five farms. At Sävsjö in northern Värend long, narrow strips of field have been found that began to be laid out in the sixth century – the traces of several farms sharing the land, probably a village taking shape.

Imagine such a village on an autumn day: the smoke from the houses, the grain being brought in from the fields by the lake, the cows driven home from the forest. Here in the middle of the land it is the field that matters most. Out in the fringes, where the forest is nearer, it is the cattle.

## The dead

The graves in Värend are not alike. What marks the district is precisely the variety. In eastern Värend, not least in Uppvidinge, the dead are laid under oval stone settings, in the west under round stone settings and standing stones. The burial custom resembles that of Blekinge, northern Skåne and Halland, not that of the Mälaren valley. Värend faced south and west. Few of the grave fields from this time have been examined with modern methods, so much is still unknown.

At Ingelstad, south of Växjö, rises Inglinge hög, thirty-five metres across and six metres high, probably from the Late Iron Age. Round it lies a grave field with mounds, oval stone settings, three-pointed settings and standing stones. At Benestad south of Alvesta a rider's grave has been excavated: a man who was burnt and given his shield, his bridle bit and a curry comb for the horse. There a woman's grave has also been found, with thirty-one beads among the burnt bones, most of glass but some of agate and rock crystal and two of silver. That grave shows that people still burnt their dead in the old way during the eleventh century, perhaps right to its end, while other dead were laid in the ground in the Christian way. For a while the two customs lived side by side.

![Inglinge hög at Ingelstad]({INFO[FI]['thumb']})
Inglinge hög at Ingelstad. Photo: Jerzy Kociatkiewicz, {LIC}, via [Wikimedia Commons]({PAGE}).

The great stone cairns that Värend is known for are much older. Värend probably has the country's largest concentration of Bronze Age burial cairns. Whoever lived here around AD 1000 walked among them as among something already ancient.

## The chieftain and the assembly

How was the land governed? The archaeologist Martin Hansson has proposed a picture, and he himself calls it hypothetical. The chieftain sat at Ingelstad, by the great mound. Some of his retinue lived at Rinkaby and Tegnaby, a couple of kilometres north. Further north still lay the cult place Hov and Thiudby, where the assembly was held – on the point in Lake Helgasjön where the bishops much later built the castle of Kronoberg. The place-names of central Värend point to the same district: Hov, Växjö, Helgö, Helgasjön and a lost Tuna. The county board writes that Thiudby is thought to have been the assembly place of the "kingdom" of Värend.

It is an interpretation, but it rests on something Hansson considers certain: that Värend and Finnveden were already in the Late Iron Age realms of their own, with a border between them. In the Middle Ages Värend was part of a law province that covered three lands, Finnveden, Värend and Njudung. It had earlier been called the law province of Värend. The land then had four hundreds, and when one of them was split the law province got the name Tiohärad, the Ten Hundreds, before 1266. The law was written down in the later thirteenth century, but only its church section survives.

![Map of Värend around AD 1000 with the runestones and the places in the text]({MAP['en']})
**Map.** Värend around AD 1000. Rust is Värend, light the neighbouring lands; the borders are approximate. Grey points are runestones, rings places in the text. Map: Vitki, after the Geological Survey of Sweden's shore-displacement model for AD 1000, the place-name register of the Institute for Language and Folklore, and Rundata.

## The roads, the iron and the lakes

Växjö lies where three hundreds meet, and its name means roughly the lake by the meeting of roads. But whether Växjö was a gathering place already before Christianity is disputed. The county board writes that it was a market place already in prehistoric times. Hansson argues that Växjö became a central place only when the church and the bishop came in the twelfth century. Royal power has left few traces: Huseby in Skatelöv is the only husaby village in Värend.

The runestones stand by the grave fields and the roads. In the whole of Tiohärad there are about ninety, and on Värend's stones it is the prayer that dominates, not the cross. And in the forests east of the lakes, in Älghult, Åseda and Lessebo, lie places where iron was made. From the Viking Age that production begins to grow, but most of what has been found is medieval; it took off in earnest only at the start of the Middle Ages.

The lakes were roads. In Lake Furen a find has been made that has been interpreted as the stock of a Gotlandic merchant travelling through Värend, from the eleventh or twelfth century. Imagine the boat that capsized, the cargo that sank, and the man who perhaps made it ashore.

## Belief

The place-names remember the gods: Frey, Odin and Thor. Near Inglinge hög lie Torsås and Torsjö. The cult seems to have been tied to the chieftains' farms. The names Helgasjön and Helgö may mean not "holy" but "protected", according to the place-name scholar Staffan Fridell. And the legend of the shield-maiden Blända, who beat the Danes, is a learned story from the seventeenth century, not history.

## A land round the lakes

Värend around AD 1000 is a land in the middle of the forest. It has its villages round the lakes, its great mounds and its assembly, and it faces south, towards Blekinge and Skåne, more than towards the Mälaren valley. It will be a while yet before the church and the bishop make Växjö the land's centre. Whoever stands by Inglinge hög and looks out over the lake country sees a land that is already old.

## How we know

The landscape, the villages, the graves and the central places rest on Martin Hansson's archaeological history of southern Småland (1999) and on the County Administrative Board of Kronoberg's descriptions of Ingelstad, Växjö, Bergkvara and other places; the law province on Jan Eric Almquist's *Lagsagor och domsagor*. Värend has no volume in *Det medeltida Sverige*. The picture of a chieftain at Ingelstad and an assembly at Thiudby is an interpretation, which its author himself calls hypothetical, and whether Växjö was a prehistoric market place is disputed. The law and the law province are known from the Middle Ages. The sources are listed below.

## Sources

- Hansson, Martin 1999. Från renjägare till viking. En arkeologisk historia om södra Småland. In: Johansson (ed.) *Landen kring sjöarna*. Kronobergsboken 1999/2000. With boxes by Christer Knutsson (the runic inscriptions) and Staffan Fridell (the place-names).
- Almquist, Jan Eric 1954. *Lagsagor och domsagor i Sverige* I. Stockholm.
- Hennius, Andreas et al. 2025. Järnframställning i blästugn – en uppdaterad kronologi. *Fornvännen* 120.
- County Administrative Board of Kronoberg: in-depth descriptions of the areas of national interest Ingelstad (2014), Växjö (2009), Bergkvara (2016), Lyåsa-Strömhult (2016), Benestad-Blädinge-Oby-Näs (2014) and Bolmsö kyrkby (2015).
- Wahlberg Traneskog, Tove 2024. *Invid ett gravfält i Härensås*. Kalmar County Museum, report 2024:23.
- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License. Institute for Language and Folklore, place-name register, CC BY. Geological Survey of Sweden, shore-displacement model (the map).
- Image: Wikimedia Commons, with the photographer and the licence in the caption."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert ":::" not in b and "/karta" not in b and "/statistik" not in b

out = {"slug": "de-gamla-landen-varend", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Geografi", "Tro och magi"]}
from src import blog_labels  # noqa: E402
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
path = os.path.join(ROOT, "utdata", "blogg", "varend.json")
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
                 "topic": "Geografi|varend", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
