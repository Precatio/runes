"""Artikeln "De gamla landen: Skåne – slätten där kungen byggde nytt" (sv + en), en del i serien De gamla landen i seriens
atmosfäriska form (Viktor 2026-11-04: "ta hela Skåne"). Skåne omkring år 1000, ett danskt land: kusten och strandbosättningarna,
slätten och skogen, Uppåkra, Järrestad, ringborgarna, Lund, köpingeorterna, Skånelagen och landstinget, tron.
Varje uppgift är ett ordagrant citat ur källorna i /Volumes/2TB/Antigrvity/Runes/downloads/skane_lit (NOTES.md, insamlat
2026-11-04) och kontrolleras nedan som en delsträng av en rad i källans text; inskrifterna mot Rundata. Kartan:
utdata/skane_land/karta_skane.R.
    ../../../.venv/bin/python build_skane_land.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, commons  # noqa: E402

recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
nz = lambda s: re.sub(r"§[A-Z] ", "", recs[s]["normalization"].replace('"', "")).strip()  # noqa: E731
SK = json.load(open(os.path.join(ROOT, "utdata", "skane", "skane.json"), encoding="utf-8"))
assert SK["n"]["Skåne"] == 59

# ---- every fact against its source line --------------------------------------------------------------------------------
LIT = "/Volumes/2TB/Antigrvity/Runes/downloads/skane_lit/"
_lines = {}


def said(fil, quote):
    if fil not in _lines:
        _lines[fil] = [" ".join(line.split()) for line in open(LIT + fil, encoding="utf-8")]
    assert any(quote in line for line in _lines[fil]), (fil, quote)


U7, U8, U10, U12, U13 = ("uppakrastudier07_centrality_regionality_2003.txt", "uppakrastudier08_landskapsarkeologi_tidig_medeltid.txt",
                         "uppakrastudier10_continuity_for_centuries_2004.txt", "uppakrastudier12_folk_fae_och_fynd.txt",
                         "uppakrastudier13_bygd_by_och_bostad.txt")
HIK, KUL, BORG, LAW, RAA = ("hikuin_jacobsson_trelleborg.txt", "kulturen_2015-5_kv_bavern_trelleborg.txt",
                            "raa_rapport_2016-73_borgeby_vallgravar.txt", "dgl1_skaanske_lov_tekstnet.txt",
                            "raa_skane_M_riksintressen_2026-06.txt")
FACTS = [
    # the coast
    ("lst_kmp_kusten-under-forhistorien.txt", "Skånes kust saknar naturliga hamnar, här kan åmynningarna ha utgjort skyddade lägen."),
    ("lst_kmp_kusten-under-forhistorien.txt", "Inom ett kustbälte på upp till 3 mil från kust och inåt land påträffas de flesta av förhistoriens lämningar i Skåne."),
    (HIK, "where there were wetlands at this time which were"),
    (U13, "Bland fynden från boplatsen och grophusen framstår glas, pärlor, bärnsten och"),
    (U13, "Några av de begravda hade filade tänder,"),
    (HIK, "1000 the fort seems to have been abandoned, and at"),
    (KUL, "Den uppfördes i två faser under 900-talet men övergavs redan omkring år"),
    (HIK, "was not quite circular, but had a diameter of"), (HIK, "earth rampart, about 12-13 meters wide, with four"),
    (HIK, "Age. The fort was built on a flat hill, overlooking the"),
    (U7, "was built in the 10th century, the road ran"), (U7, "through its north gate."),
    ("lst_kmp_forhistoriska-forsvarsanlaggningar.txt", "Trelleborgen i Trelleborg upptäcktes 1988 i samband med att ett nytt bostadsområde skulle byggas på platsen."),
    # plain, forest, villages, houses
    ("lst_kmp_odlingslandskapets-geografiska-forutsattningar.txt", "skogsbygden främst i norr och nordost och slättbygden i söder och sydväst"),
    ("lst_kmp_gard-och-by.txt", "Perioden mellan år 900 och 1200 karakteriseras av en stor befolkningsökning"),
    ("lst_kmp_gard-och-by.txt", "Många av dagens skånska byar har sitt ursprung i 1000-talets Skåne."),
    ("lst_kmp_gard-och-by.txt", "Under senare delen av järnåldern (500–1000 e.Kr.) tillkom grophusen som var avsedda för bland annat textilt hantverk."),
    ("lst_kmp_gard-och-by.txt", "I långhusets ladugårdsdel kunde det finnas utrymme för mellan 16 till 26 djur."),
    ("lst_kmp_gard-och-by.txt", "Livslängden för ett järnåldershus brukar beräknas till cirka 75 år."),
    (U13, "och flätverksgärden (Kriig & Pettersson 1997; Pettersson & Brorsson 2002;"),
    (U13, "bestått av ett tiotal gårdar med tofter tydligt avgränsade genom diken, rännor"),
    # Uppåkra
    ("lst_omr_bomhog-hjarup-uppakra.txt", "från cirka 100 f.Kr. till cirka 1000 e.Kr."),
    (U12, "spridda över en yta omkring 40 hektar med upp"), (U12, "snarast kan beskrivas som en järnåldersstad."),
    (U10, "of 13.5 metres with convex long sides and"), (U10, "houses in altogether seven stages."),
    (U10, "including more than hundred gold-foil"), (U10, "ker of bronze and silver with gold foil decoration and a glass bowl was found."),
    (U12, "high frequency of piglets and fowl from the postholes of the ceremonial house represent feasting by the aristocracy"),
    (U10, "occurred during the early Viking Age."), (U13, "under den tidiga vikingatiden. Samtidigt upphörde även offrandet av vapen"),
    (U13, "beläggas under denna period, åtminstone fram till mitten av 1000-talet, utifrån"),
    (U13, "ett stort antal vågar och framför allt vikter, men även mynt och bitsilver"),
    (U13, "Det vikingatida Uppåkra framstår som en dåligt känd period i platsens"),
    (U13, "i eller i närheten till Uppåkra är anmärkningsvärd."),
    (U8, "kristen påverkan i form av skelettgravar med öst-västlig orientering, och som"),
    # Järrestad
    (U7, "In phase 4 a fifty-metre-long and up to"), (U7, "fourteen-metre-wide hall was built slightly to"),
    (U7, "during the period c. AD 950–1050, through-"), (U7, "Preliminary chronology"), (U7, "“the settlement of the jarl/earl” or possibly"),
    (U7, "härad or hundred, recorded in 1182 as"), (U7, "the magnate’s farm disappears in the course of"),
    (U7, "is recorded as a kongelev in King Valdemar’s"), (U7, "a focal point of the pagan cosmos"),
    # the king: realm, ring forts, Lund
    ("lst_kmp_administration-och-forvaltning.txt", "Från 900-talet var Skåne en del av det danska riket som Harald Blåtand förklarade sig själv som härskare över."),
    ("lst_kmp_forhistoriska-forsvarsanlaggningar.txt", "Detta var de första skånska offensiva borgarna som byggdes för att hysa en beväpnad styrka."),
    ("lst_kmp_forhistoriska-forsvarsanlaggningar.txt", "I Skåne har man endast påträffat två borgar av denna typ, i Trelleborg på Skånes sydkust och i Borgeby på västkusten."),
    (U8, "kring år 980, uppfördes en vikingatida ringborg i Borgeby."), (U8, "varken ha reparerats eller underhållits (Lund 1997b, s. 163)."),
    (BORG, "Sådana spännen har tillskrivits Harald Blåtands hov, och har bland"),
    (U8, "Roskildekrönikan från kring 1140 berättar att Sven Tveskägg uppförde en"),
    (U8, "kyrka i Skåne. Denna är sannolikt den kyrka från ca 990 som hittats vid"),
    (U8, "mellan 1310 och 1746 personer begravts i storkyrkogårdens äldsta skede"),
    (U8, "Den äldsta kyrkliga sfären i Lund uppvisar många drag från England"),
    ("lst_omr_lund.txt", "som var centralt belägen vid den punkt där flera större vägar möttes"),
    (U13, "i Lund, från omkring 1000 e.Kr., har etablerats i de centrala delarna av den"),
    (U13, "omgivande samtida bebyggelsen, dvs. den har bestått av stora gårdsenheter"),
    (U8, "Jag vill i stället föra fram tanken att Lund inte har någon föregångare,"),
    (U13, "Förhållandet mellan det sena Uppåkra och det tidiga Lund framstår som"),
    ("lst_omr_lund.txt", "Själva grundläggningstiden anges till 1020 då Knut den Store lät anlägga ett myntverk på platsen"),
    # trade by the rivers
    ("lst_kmp_loddekopinge-och-andra-kopingeorter.txt", "Med strategiska lägen en bit från kusten, i anslutning till åar, grundades så kallade köpingeorter."),
    ("lst_kmp_loddekopinge-och-andra-kopingeorter.txt", "Löddeköpinge varit en plats för handel med framför allt jord- och skogsprodukter och bruksföremål"),
    ("lst_kmp_loddekopinge-och-andra-kopingeorter.txt", "Det stora antalet grophus kan tyda på att här skett en omfattande tillverkning av bruksföremål."),
    ("lst_kmp_loddekopinge-och-andra-kopingeorter.txt", "en sten- och timmerkonstruktion på 160 gånger 8 meter"),
    ("lst_kmp_loddekopinge-och-andra-kopingeorter.txt", "Lödde kar har daterats till senare delen av vikingatiden, cirka år 950 -1100."),
    (U7, "Kar, dated to the 11th and twelfth centuries."), (U8, "nes enda egentligt segelbara å"),
    ("lst_kmp_sjofart-och-handel.txt", "Köpingeorterna utvecklades aldrig till städer utan deras funktion som handelsplats upphörde vid 1000-talet."),
    (U13, "bestod av arabiskt mynt, pärlor, spännen, verktyg, nyckel och Feldberg-keramik."),
    (U8, "Löddeköpinge har som tidigare nämnts över 2300 gravar hittats"),
    # roads
    ("lst_kmp_det-aldsta-vagnatet.txt", "För tunga transporter var oftast vägar på vatten att föredra, eller om möjligt vintervägar med släde."),
    (LAW, "vil ødelægge en Hovedvej med Grøft eller med Pløjning"), (LAW, "eller spærrer den med Gærde, skal bøde tre Mark til Kongen*"),
    # law and assembly
    (LAW, "Skikkelse, hvori vi nu kender den, er blevet til mellem 1202"), (LAW, "Skaanske Lov havde Gyldighed inden for det skaanske"),
    ("lst_kmp_administration-och-forvaltning.txt", "Skånelagen var den äldsta landskapslagen i Danmark och gällde Skåneland, vilket omfattade Skåne, Blekinge, Halland och Bornholm."),
    (LAW, "optegnelser, som ikke har faaet officiel Stadfæstelse"),
    ("lst_kmp_ordning-ratt-och-sakerhet.txt", "Vid sidan om häradstingen fanns även Skåne landsting, som hölls vid Arendala öster om Lund."),
    ("lst_kmp_ordning-ratt-och-sakerhet.txt", "I landstinget hyllade skåningarna också nytillträdda kungar med ceremoni på Lerbäckshögen norr om Lund."),
    (LAW, "værelse ved Vaabentag paa Landstinget, og før kan Bonden"), (LAW, "sig paa Jernet, da brænder han til Bonden Værdien af det"),
    (LAW, "ikke vil opdyrke den, til Herredstinget eller til Landstinget"),
    ("lst_kmp_administration-och-forvaltning.txt", "nämns Ljunits härad i skrift första gången 1145"), ("lst_kmp_administration-och-forvaltning.txt", "I Skåne finns 23 härader."),
    (LAW, "og Spade til Landstinget og paabyde Udgærdsleding"), (LAW, "bet* Og Styrismanden skal forestaa Leding i seksten Uger,"),
    (LAW, "en anden Mand, da kan Styrismanden sagesløst skære Ørerne"), (LAW, "Halvdel af 13* Aarh*, men maa bygge paa en ældre Kilde"),
    # belief
    ("lar_stromberg_ales_stones.txt", "ship is extremely large, 67 metres long, 19"),
    ("lst_omr_kaseberga-ales-stenar.txt", "Den omfattar 59 resta stenar och uppfördes antagligen för omkring 1000 - 1500 år sedan."),
    (RAA, "Skeppsättningen Ales stenar från yngre järnåldern med 58 resta stenar och dominerande läge på"),
    ("lst_kmp_trosforestallningar-under-forhistorien.txt", "Ales stenar härrör troligen från vikingatid, men en tidigare datering är också möjlig."),
    ("lst_kmp_trosforestallningar-under-forhistorien.txt", "Exempelvis kan Onslunda härledas till gudanamnet Oden, Torsjö till Tor och Fröslöv till Frö."),
    ("lst_kmp_trosforestallningar-under-forhistorien.txt", "Det kristna inflytandet kan ses i upphörandet av att bränna den döde"),
    ("lst_kmp_kristnandet.txt", "Missionen i Skåne skedde främst från tyskt och anglosaxiskt håll."),
    ("lst_kmp_kristnandet.txt", "Monumentet uppfördes i början av 1000-talet och vittnade om att den skånska kristnandeprocessen hade inletts."),
    ("lst_omr_hardeberga-arendala-dalby-skrylle-hallestad.txt", "I dess östra yttermur är inmurat tre runstenar från vikingatid."),
    # sea level
    ("sgu_strandforskjutningsmodell_beskrivning.txt", "visar en övergripande bild av den forntida fördelningen mellan hav"),
]
for fil, q in FACTS:
    said(fil, q)
assert "SaR flo ægi at Upsalum" in nz("DR 295") and "Toka Gorms sun, seR hullan drottin" in nz("DR 295")
assert recs["DR 295"]["parish"].startswith("Hällestad") and "§" not in nz("DR 295")
for q in ("Og af hver Havne skal en der hjemmehørende Mand drage", "Stedet for sig sende en anden end sin egen Søn* Sender han", "af ham og sende ham hjem* Har Styrismanden selv et Skib,"):
    said(LAW, q)

# ---- pictures and map -------------------------------------------------------------------------------------------------
FT, FU = "Trelleborg, trelleborgen (2008-07-27).JPG", "Uppakra ceremonial house 01.jpg"
INFO = commons.commons_info([FT, FU])
assert (INFO[FT]["licence"], INFO[FT]["author"]) == ("CC BY-SA 3.0", "Klugschnacker")
assert (INFO[FU]["licence"], INFO[FU]["author"]) == ("CC BY-SA 4.0", "Sinikka Halme")
LIC = {f: f"[{INFO[f]['licence']}]({INFO[f]['licence_url']})" if INFO[f].get("licence_url") else INFO[f]["licence"] for f in (FT, FU)}
PAGE = {f: "https://commons.wikimedia.org/wiki/File:" + f.replace(" ", "_") for f in (FT, FU)}
MAP = {lang: blog_figures.freeze(open(os.path.join(ROOT, "utdata", "skane_land", f"karta_skane_{lang}.png"), "rb").read())
       for lang in ("sv", "en")}
HEMMA = "/artiklar/hemma-mellan-rikena-skanes-runstenar"
SOTHOLM = "/artiklar/de-gamla-landen-sotholm"

title = "De gamla landen: Skåne – slätten där kungen byggde nytt"
summary = ("Omkring år 1000 var Skåne ett danskt land i förvandling: den gamla centralplatsen Uppåkra bleknade, kungen byggde "
           "ringborgar och en kyrka i Lund, och på slätten växte nya byar fram. Följ med från stranden vid Trelleborg till "
           "landstinget öster om Lund. En del i serien De gamla landen.")

body = f"""Föreställ dig att du kommer till Skåne från havet, för tusen år sedan, och går i land vid Trelleborg. Det finns ingen hamn. Skånes kust saknar naturliga hamnar, och båtarna dras upp på sanden eller söker skydd i åmynningarna. På strandvallen ligger en lång rad små hus, nedgrävda i marken, och bakom dem breder våtmarker ut sig. Här har folk bott i generationer, och i jorden ligger det de lämnat efter sig: glas, pärlor, bärnsten och mycket krukgods från slaviska länder på andra sidan Östersjön. På gravfältet vid Vannhög ligger döda med filade tänder.

Ovanför stranden, på en flack höjd med utsikt över havet, ligger en ringborg: en nästan rund vall, omkring hundrafyrtio meter tvärs över, tolv–tretton meter bred, med fyra portar. Vägen från kusten in mot Uppåkra går genom dess norra port. Men om du kommer omkring år 1000 är borgen redan övergiven. Den byggdes i två omgångar under 900-talet och lämnades, och samtidigt försvinner bosättningen på stranden. Något har förändrats i Skåne.

![Den rekonstruerade delen av Trelleborgen]({INFO[FT]['thumb']})
Trelleborgen i Trelleborg, där en fjärdedel av vallen och en port har byggts upp igen. Foto: Klugschnacker, {LIC[FT]}, via [Wikimedia Commons]({PAGE[FT]}).

## Slätten och skogen

Gå inåt land, och landskapet öppnar sig. Skåne är delat på snedden: slätten i söder och sydväst, skogen i norr och nordost, och mellan dem en bygd av både och. De flesta av förhistoriens lämningar ligger inom tre mil från kusten. Det är där folk bor.

Föreställ dig en by på slätten: långhus där människor och djur bor under samma tak, med plats för sexton till tjugosex djur i ladugårdsänden, och runt dem små nedgrävda grophus där man väver. Ett hus står i ungefär sjuttiofem år innan det måste byggas nytt. Vid Bjärred, norr om Lund, har man hittat en sådan bosättning: ett tiotal gårdar, var och en på sin tomt, avgränsad med diken och flätade gärdesgårdar.

Och bygden växer. Mellan år 900 och 1200 ökar befolkningen kraftigt, och nya byar grundas. Många av de skånska byar som finns kvar än i dag har sitt ursprung i 1000-talets Skåne. Den som går över slätten omkring år 1000 går genom ett land som håller på att fyllas.

## Uppåkra

Mitt på slätten, söder om där Lund snart ska ligga, finns en plats som har varit centrum i över tusen år. Uppåkra har funnits sedan omkring hundra år före Kristus. Lämningarna sprider sig över fyrtio hektar, och kulturlagren är upp till två meter djupa – forskarna kallar platsen snarast en järnåldersstad. Här har det funnits ett litet men mycket högt hus, tretton och en halv meter långt med svängda långsidor, som byggts upp igen sju gånger på samma plats. I det har man hittat en bägare av brons och silver med guldfolie, en glasskål och mer än hundra guldgubbar, små bilder i tunt guld. I stolphålen ligger ben av spädgrisar och fåglar: rester av fester för de mäktiga.

![Modell av kulthuset i Uppåkra]({INFO[FU]['thumb']})
Kulthuset i Uppåkra som modell, på Uppåkra arkeologiska center. Foto: Sinikka Halme, {LIC[FU]}, via [Wikimedia Commons]({PAGE[FU]}).

Men den som kommer till Uppåkra omkring år 1000 ser inte kulthuset. Det revs troligen redan under tidig vikingatid, och då upphörde också offren av vapen. Ändå levde platsen vidare. Fynden av vågar, vikter, mynt och bitsilver visar att man handlade här åtminstone fram till mitten av 1000-talet. Det vikingatida Uppåkra är dåligt känt, eftersom plogen har förstört de övre lagren, och märkligt nog har inga gravfält hittats i eller nära platsen. Men på gravfälten runt omkring syns något nytt: döda som läggs i jorden med huvudet i väster, utan gravgåvor. Det kristna har börjat sätta sina spår.

## Jarlens gård

Långt österut, på Österlen, ligger Järrestad, vars namn tolkas som jarlens boplats. Här står en stormannagård med en hall som omkring år 1000 är femtio meter lång och upp till fjorton meter bred, omgiven av en palissad, med brunnar i våtmarken intill. Hallen har tolkats som ett hov, en medelpunkt i den förkristna världen. Häradet bär gårdens namn när det första gången nämns, 1182. Men gården försvinner under 1000-talet, och på samma trakter blir mark så småningom kungens.

## Kungens nya Skåne

Sedan 900-talet hör Skåne till det danska riket, och det är kungarna som förändrar landet. Under Harald Blåtand byggs ringborgarna, de första skånska borgar som byggts för att hysa en beväpnad styrka. Två är kända: Trelleborgen och Borgeby, vid övergången över Kävlingeån, byggd kring år 980. I Borgeby har man hittat en gjutform för stora spännen av ett slag som har knutits till Harald Blåtands hov. Ingen av borgarna verkar ha lagats eller underhållits. De var kungens verk, och de var kortlivade.

Det som blev kvar var Lund. Roskildekrönikan, skriven kring 1140, berättar att Sven Tveskägg byggde en kyrka i Skåne, och den är sannolikt den kyrka från omkring 990 som har hittats i Lund. Runt den växte en kyrkogård där mellan 1 300 och 1 700 människor begravdes under det första skedet. Den äldsta kyrkliga miljön i Lund har många drag från England, där Knut den store också blev kung. Lund låg där flera stora vägar möttes, och de äldsta gårdarna där liknade landsbygdens: stora gårdar med långhus.

Var Lund Uppåkras arvtagare? Det är omstritt. Arkeologen Anna Lihammer menar att Lund inte har någon föregångare utan anlades som något nytt. Mats Anglert kallar förhållandet mellan det sena Uppåkra och det tidiga Lund oklart. Men den som står på slätten omkring år 1000 ser två platser några kilometer från varandra: en gammal, där handeln fortfarande pågår, och en ny, där kungens kyrka står.

![Karta över Skåne omkring år 1000 med häraderna, runstenarna och platserna i texten]({MAP['sv']})
**Karta.** Skåne omkring år 1000. Kusten såg ut ungefär som senare, eftersom landet här knappt har höjt sig. Den rostfärgade ytan är Skåne, de streckade linjerna häradsgränserna, ungefärliga. Grå punkter är Skånes vikingatida runstenar, ringar platser i texten. Karta: Vitki, efter SGU:s modell för strandförskjutningen år 1000, Institutet för språk och folkminnens ortnamnsregister och Rundata.

## Handel vid åarna

Handeln sökte sig till åarna. En bit från kusten, vid vattendrag som då gick att segla på, låg köpingeorterna. Vid Löddeköpinge, vid Kävlingeån, västra Skånes enda egentligt segelbara å, handlade man framför allt med det jorden och skogen gav och med vardagsföremål, och de många grophusen tyder på att mycket tillverkades på platsen. Utanför åmynningen ligger Lödde kar, en konstruktion av sten och timmer, hundrasextio gånger åtta meter, troligen en plats där last flyttades från stora skepp till mindre. Söder om Löddeköpinge, vid kusten, har en hantverksplats lämnat efter sig pärlor, spännen, verktyg och ett arabiskt mynt.

Föreställ dig marknadsdagen vid ån: säd och hudar, trä och järn, folk från byarna runt omkring som byter med varandra. Köpingeorterna blev aldrig städer. Deras tid som handelsplatser tog slut under 1000-talet, samtidigt som Lund växte fram.

## Lagen och tinget

Skåne hade sin egen lag, Skånelagen. Den skrevs ner mellan 1202 och omkring 1216 och gällde Skåne, Halland, Blekinge och Bornholm. Den stadfästes aldrig formellt utan är en uppteckning av hur man brukade döma, och den bygger på äldre sedvänjor. Därför går det att se det äldre samhället i den, med försiktighet.

Landet var indelat i härader, tjugotre stycken, och de är gamla: Ljunits härad nämns redan 1145. Över häradstingen fanns landstinget, som på medeltiden hölls vid Arendala öster om Lund. Där hyllade skåningarna sina nya kungar, med en ceremoni på Lerbäckshögen norr om Lund. Där dömdes den fredlös som inte svarade för sig, genom vapentak, när männen slog sina vapen samman. Och dit gick tvisterna när några i byn ville odla upp den gemensamma allmänningen och andra inte.

Lagen känner också järnbörden, där den anklagade bar glödande järn för att visa sin oskuld. Den skyddade vägarna: den som förstörde en huvudväg med dike eller plog, eller stängde den med gärdesgård, fick böta tre mark till kungen. Och lagen visar hur landet gick i krig. När fienden var i landet bars skovel och spade till landstinget som tecken på uppbåd. Från varje hamna skulle en man som bodde där följa styresmannen. Fick han förhinder fick han inte skicka någon annan än sin egen son, och kom det en annan man i hans ställe fick styresmannen skära öronen av honom och skicka hem honom.

## Tron

På en höjd vid Kåseberga, med havet nedanför, står Ales stenar, Sveriges största skeppssättning, sextiosju meter lång och nitton meter bred, av femtioåtta eller femtionio stenar. Den är troligen från vikingatiden, men den kan vara äldre. Ortnamnen minns de gamla gudarna: Onslunda efter Oden, Torsjö efter Tor, Fröslöv efter Frö.

Men omkring år 1000 är det nya redan på väg. Missionen kom till Skåne från tyskt och engelskt håll. I början av 1000-talet restes Hunnestadsmonumentet, med bilder både från den gamla tron och den nya. Man slutade bränna de döda. Och i Hällestad, öster om Lund, sitter tre vikingatida runstenar inmurade i kyrkans vägg. En av dem minns en man som inte flydde vid Uppsala:

> *{nz("DR 295")}*

Eskil satte denna sten efter Toke, Gorms son, en trogen herre för honom. Han flydde inte vid Uppsala. Kämpar satte efter sin broder stenen på berget, stödd med runor. De gick närmast Gorms Toke.

Vad Skånes runstenar säger om att höra hemma har vi skrivit om i [Hemma mellan rikena]({HEMMA}).

## Ett land som byggdes om

Skåne omkring år 1000 är ett gammalt land som byggs om. Slätten fylls av nya byar. Det gamla kulthuset i Uppåkra är borta, men handeln där pågår ännu. Kungens ringborgar står övergivna, och i Lund har kungen byggt en kyrka. Den som går längs vägen från stranden vid Trelleborg mot Lund går genom alla dessa tider på en gång: förbi den tomma borgen, över slätten med sina byar, förbi Uppåkra, mot det nya.

Det här är en del i serien De gamla landen. Den första tog oss till [Sotholm på ön Tören]({SOTHOLM}), i det svenska riket. Skåne hörde till Danmark, och det märks.

## Så vet vi det

Landskapet, byarna, Uppåkra, Järrestad, ringborgarna och Lund bygger på Lunds universitets Uppåkrastudier, på Trelleborgs och Borgebys utgrävningsrapporter och på länsstyrelsens och Riksantikvarieämbetets beskrivningar av Skånes kulturmiljöer. Lagen och tinget är kända först från medeltiden: Skånelagen från början av 1200-talet och landstinget vid Arendala från ännu senare källor, så de visar Skåne efter år 1000, inte säkert före. Flera dateringar är osäkra. Kronologin för Järrestad är preliminär, Ales stenar kan vara äldre än vikingatiden, och om Lund ska räknas från kyrkan omkring 990 eller från Knut den stores myntverk 1020 är en tolkningsfråga. Kusten på kartan bygger på SGU:s modell för strandförskjutningen, som bara ger en översiktlig bild. I Skåne har landet knappt höjt sig sedan vikingatiden, och kusten var i stort sett densamma som senare, utom på Kristianstadsslätten.

## Källor

- Anglert, Mats 2003. Uppåkra. Bland högar, ortnamn och kyrkor. I: Anglert & Thomasson (red.) *Landskapsarkeologi och tidig medeltid*. Uppåkrastudier 8. Lund.
- Anglert, Mats 2021. Uppåkra, Lund och landskapet. I: Roslund (red.) *Bygd, by och bostad runt Uppåkra*. Uppåkrastudier 13. Lund.
- Jacobsson, Bengt 1998. Trelleborg in Scania. *Hikuin* 25, s. 15–22.
- Jacobsson, Bengt 2003. Trelleborg and the Southern Plain during the Iron Age. I: Larsson & Hårdh (red.) *Centrality – Regionality*. Uppåkrastudier 7. Lund.
- Kroman, Erik (övers.) 1945. *Danmarks gamle Love paa nutidsdansk* I. Skaanske Lov. København.
- Larsson, Lars & Lenntorp, Karl-Magnus 2004. The Enigmatic House. I: Larsson (red.) *Continuity for Centuries*. Uppåkrastudier 10. Lund.
- Lihammer, Anna 2003. Kungen och landskapet. I: Anglert & Thomasson (red.) *Landskapsarkeologi och tidig medeltid*. Uppåkrastudier 8. Lund.
- Magnell, Ola, Boethius, Adam & Thilderqvist, Johan 2013. Fest i Uppåkra. I: Hårdh & Larsson (red.) *Folk, fä och fynd*. Uppåkrastudier 12. Lund.
- Söderberg, Bengt 2003. Integrating Power. Some Aspects of a Magnate's Farm and Presumed Central Place in Järrestad. I: *Centrality – Regionality*. Uppåkrastudier 7. Lund.
- Söderberg, Bengt & Stark, Kennet 2016. *Borgeby. Vikingatida vallgravar*. Rapport 2016:73. Arkeologerna, Statens historiska museer.
- Balic, Ivan 2015. *Kv Bävern 1 … Trelleborg*. Kulturmiljörapport 2015:5. Kulturen, Lund.
- Strömberg, Märta 2001. Ale's Stones. A Monument of Recycled Boulders? *Lund Archaeological Review* 7.
- Länsstyrelsen Skåne. *Kulturmiljöprogram för Skåne* (teman och områden), hämtat 2026-11-04.
- Riksantikvarieämbetet 2026. *Riksintressen för kulturmiljövården – Skåne län*.
- Sveriges geologiska undersökning, strandförskjutningsmodell (öppna data, CC BY 4.0), med produktbeskrivning 2022.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License. Institutet för språk och folkminnen, ortnamnsregistret, CC BY.
- Bilder: Wikimedia Commons, med fotografen och licensen i bildtexten."""

title_en = "The old lands: Skåne – the plain where the king built anew"
summary_en = ("Around AD 1000 Skåne was a Danish land in change: the old central place of Uppåkra was fading, the king built "
              "ring forts and a church in Lund, and new villages grew up on the plain. Come along from the shore at Trelleborg "
              "to the land assembly east of Lund. A part of the series The old lands.")

body_en = f"""Imagine coming to Skåne from the sea a thousand years ago and going ashore at Trelleborg. There is no harbour. The coast of Skåne has no natural harbours, and the boats are hauled up on the sand or seek shelter in the river mouths. On the beach ridge lies a long row of small houses, sunk into the ground, and behind them wetlands spread out. People have lived here for generations, and in the ground lies what they left behind: glass, beads, amber and a great deal of pottery from the Slavic lands across the Baltic. In the grave field at Vannhög lie dead with filed teeth.

Above the shore, on a low hill overlooking the sea, lies a ring fort: an almost round rampart, some hundred and forty metres across, twelve to thirteen metres wide, with four gates. The road from the coast inland towards Uppåkra runs through its north gate. But if you come around AD 1000, the fort is already abandoned. It was built in two phases during the tenth century and left, and at the same time the settlement on the shore disappears. Something has changed in Skåne.

![The reconstructed part of Trelleborgen]({INFO[FT]['thumb']})
Trelleborgen in Trelleborg, where a quarter of the rampart and a gate have been rebuilt. Photo: Klugschnacker, {LIC[FT]}, via [Wikimedia Commons]({PAGE[FT]}).

## The plain and the forest

Go inland, and the landscape opens. Skåne is divided on the diagonal: the plain in the south and south-west, the forest in the north and north-east, and between them a country of both. Most of prehistory's remains lie within thirty kilometres of the coast. That is where people live.

Imagine a village on the plain: longhouses where people and animals live under one roof, with room for sixteen to twenty-six animals in the byre end, and around them small sunken huts where cloth is woven. A house stands for about seventy-five years before it has to be rebuilt. At Bjärred, north of Lund, such a settlement has been found: some ten farms, each on its own plot, bounded by ditches and wattle fences.

And the countryside grows. Between 900 and 1200 the population rises sharply, and new villages are founded. Many of the villages of Skåne that still exist have their origin in eleventh-century Skåne. Whoever crosses the plain around AD 1000 walks through a land that is filling up.

## Uppåkra

In the middle of the plain, south of where Lund will soon stand, lies a place that has been a centre for over a thousand years. Uppåkra has existed since about a hundred years before Christ. Its remains spread over forty hectares, and the deposits are up to two metres deep – researchers call the place a kind of Iron Age town. Here there was a small but very tall house, thirteen and a half metres long with curving long sides, rebuilt seven times on the same spot. In it were found a beaker of bronze and silver with gold foil, a glass bowl and more than a hundred gold-foil figures, small pictures in thin gold. In the postholes lie the bones of piglets and fowl: remains of feasts for the powerful.

![Model of the cult house at Uppåkra]({INFO[FU]['thumb']})
The cult house at Uppåkra as a model, at Uppåkra Archaeological Centre. Photo: Sinikka Halme, {LIC[FU]}, via [Wikimedia Commons]({PAGE[FU]}).

But whoever comes to Uppåkra around AD 1000 does not see the cult house. It was probably pulled down already in the early Viking Age, and then the offerings of weapons also ceased. Still, the place lived on. Finds of scales, weights, coins and hack silver show that people traded here at least until the middle of the eleventh century. Viking-age Uppåkra is poorly known, since the plough has destroyed the upper layers, and strangely no grave fields have been found in or near the place. But in the grave fields round about something new shows: dead laid in the ground with the head to the west, without grave goods. Christianity has begun to leave its mark.

## The jarl's farm

Far to the east, in Österlen, lies Järrestad, whose name is interpreted as the settlement of the jarl. Here stands a magnate's farm with a hall that around AD 1000 is fifty metres long and up to fourteen metres wide, enclosed by a palisade, with wells in the wetland beside it. The hall has been interpreted as a hov, a focal point of the pre-Christian world. The hundred bears the farm's name when it is first mentioned, in 1182. But the farm disappears during the eleventh century, and in the same districts land in time becomes the king's.

## The king's new Skåne

Since the tenth century Skåne has belonged to the Danish realm, and it is the kings who change the land. Under Harald Bluetooth the ring forts are built, the first forts in Skåne made to house an armed force. Two are known: Trelleborgen and Borgeby, at the crossing of the Kävlingeån river, built around 980. At Borgeby a mould has been found for large brooches of a kind linked to Harald Bluetooth's court. Neither fort seems to have been repaired or maintained. They were the king's work, and they were short-lived.

What remained was Lund. The Roskilde Chronicle, written around 1140, tells that Sven Forkbeard built a church in Skåne, and it is probably the church from about 990 that has been found in Lund. Around it grew a churchyard where between 1,300 and 1,700 people were buried in the first phase. The oldest church setting in Lund has many features from England, where Cnut the Great also became king. Lund lay where several great roads met, and the oldest farms there resembled those of the countryside: large farms with longhouses.

Was Lund Uppåkra's heir? That is disputed. The archaeologist Anna Lihammer argues that Lund had no forerunner but was founded as something new. Mats Anglert calls the relationship between late Uppåkra and early Lund unclear. But whoever stands on the plain around AD 1000 sees two places a few kilometres apart: an old one, where trade still goes on, and a new one, where the king's church stands.

![Map of Skåne around AD 1000 with the hundreds, the runestones and the places in the text]({MAP['en']})
**Map.** Skåne around AD 1000. The coast looked much as it did later, since the land here has hardly risen. The rust area is Skåne, the dashed lines the borders of the hundreds, approximate. Grey points are Skåne's Viking-age runestones, rings places in the text. Map: Vitki, after the Geological Survey of Sweden's shore-displacement model for AD 1000, the place-name register of the Institute for Language and Folklore, and Rundata.

## Trade by the rivers

Trade sought out the rivers. Some way from the coast, by streams that could then be sailed, lay the köpinge places. At Löddeköpinge, on the Kävlingeån, the only truly navigable river in western Skåne, people traded above all in what the soil and the forest gave and in everyday goods, and the many sunken huts suggest that much was made on the spot. Off the river mouth lies Lödde kar, a construction of stone and timber, a hundred and sixty by eight metres, probably a place where cargo was moved from large ships to smaller ones. South of Löddeköpinge, on the coast, a craft site has left beads, brooches, tools and an Arabic coin.

Imagine market day by the river: grain and hides, wood and iron, people from the villages round about trading with one another. The köpinge places never became towns. Their time as trading places ended during the eleventh century, while Lund grew.

## The law and the assembly

Skåne had its own law, the Law of Scania. It was written down between 1202 and about 1216 and applied to Skåne, Halland, Blekinge and Bornholm. It was never formally ratified but is a record of how judgements were usually made, and it builds on older custom. So the older society can be glimpsed in it, with care.

The land was divided into hundreds, twenty-three of them, and they are old: the hundred of Ljunit is mentioned as early as 1145. Above the hundred assemblies stood the land assembly, which in the Middle Ages met at Arendala east of Lund. There the people of Skåne acclaimed their new kings, with a ceremony on Lerbäckshögen north of Lund. There the man who would not answer for himself was declared an outlaw by vápnatak, when the men struck their weapons together. And there the disputes went when some in a village wanted to clear the common land and others did not.

The law also knows the ordeal of hot iron, where the accused carried red-hot iron to show his innocence. It protected the roads: whoever ruined a main road with a ditch or a plough, or closed it with a fence, was fined three marks to the king. And the law shows how the land went to war. When the enemy was in the land, a shovel and a spade were carried to the land assembly as the call to arms. From each *hamna* a man who lived there was to go with the commander. If he was prevented, he could send no one but his own son, and if another man came in his place, the commander could cut off that man's ears and send him home.

## Belief

On a height at Kåseberga, with the sea below, stand Ale's Stones, Sweden's largest ship setting, sixty-seven metres long and nineteen metres wide, of fifty-eight or fifty-nine stones. It is probably from the Viking Age, but it may be older. The place-names remember the old gods: Onslunda after Odin, Torsjö after Thor, Fröslöv after Frey.

But around AD 1000 the new is already on its way. The mission came to Skåne from the German and the English side. Early in the eleventh century the Hunnestad monument was raised, with pictures from both the old faith and the new. People stopped burning their dead. And at Hällestad, east of Lund, three Viking-age runestones are set into the church wall. One of them remembers a man who did not flee at Uppsala:

> *{nz("DR 295")}*

Áskell placed this stone in memory of Tóki, Gormr's son, to him a faithful lord. He did not flee at Uppsala. Valiant men placed in memory of their brother the stone on the hill, steadied by runes. They went closest to Gormr's Tóki.

What the runestones of Skåne say about belonging we have written about in [Hemma mellan rikena]({HEMMA}).

## A land being rebuilt

Skåne around AD 1000 is an old land being rebuilt. The plain fills with new villages. The old cult house at Uppåkra is gone, but trade there still goes on. The king's ring forts stand abandoned, and in Lund the king has built a church. Whoever walks the road from the shore at Trelleborg towards Lund walks through all these times at once: past the empty fort, over the plain with its villages, past Uppåkra, towards the new.

This is a part of the series The old lands. The first took us to [Sotholm on the island of Tören]({SOTHOLM}), in the Swedish realm. Skåne belonged to Denmark, and it shows.

## How we know

The landscape, the villages, Uppåkra, Järrestad, the ring forts and Lund rest on Lund University's Uppåkra studies, on the excavation reports from Trelleborg and Borgeby and on the county board's and the National Heritage Board's descriptions of Skåne's cultural environments. The law and the assembly are known only from the Middle Ages: the Law of Scania from the early thirteenth century and the land assembly at Arendala from later sources still, so they show Skåne after AD 1000, not certainly before. Several dates are uncertain. The chronology of Järrestad is preliminary, Ale's Stones may be older than the Viking Age, and whether Lund should be counted from the church of about 990 or from Cnut the Great's mint of 1020 is a matter of interpretation. The coast on the map rests on the Geological Survey of Sweden's shore-displacement model, which gives only an overview. In Skåne the land has hardly risen since the Viking Age, and the coast was much the same as later, except on the Kristianstad plain.

## Sources

- Anglert, Mats 2003. Uppåkra. Bland högar, ortnamn och kyrkor. In: Anglert & Thomasson (eds) *Landskapsarkeologi och tidig medeltid*. Uppåkrastudier 8. Lund.
- Anglert, Mats 2021. Uppåkra, Lund och landskapet. In: Roslund (ed.) *Bygd, by och bostad runt Uppåkra*. Uppåkrastudier 13. Lund.
- Jacobsson, Bengt 1998. Trelleborg in Scania. *Hikuin* 25, pp. 15–22.
- Jacobsson, Bengt 2003. Trelleborg and the Southern Plain during the Iron Age. In: Larsson & Hårdh (eds) *Centrality – Regionality*. Uppåkrastudier 7. Lund.
- Kroman, Erik (transl.) 1945. *Danmarks gamle Love paa nutidsdansk* I. Skaanske Lov. Copenhagen.
- Larsson, Lars & Lenntorp, Karl-Magnus 2004. The Enigmatic House. In: Larsson (ed.) *Continuity for Centuries*. Uppåkrastudier 10. Lund.
- Lihammer, Anna 2003. Kungen och landskapet. In: Anglert & Thomasson (eds) *Landskapsarkeologi och tidig medeltid*. Uppåkrastudier 8. Lund.
- Magnell, Ola, Boethius, Adam & Thilderqvist, Johan 2013. Fest i Uppåkra. In: Hårdh & Larsson (eds) *Folk, fä och fynd*. Uppåkrastudier 12. Lund.
- Söderberg, Bengt 2003. Integrating Power. Some Aspects of a Magnate's Farm and Presumed Central Place in Järrestad. In: *Centrality – Regionality*. Uppåkrastudier 7. Lund.
- Söderberg, Bengt & Stark, Kennet 2016. *Borgeby. Vikingatida vallgravar*. Report 2016:73. Arkeologerna, National Historical Museums.
- Balic, Ivan 2015. *Kv Bävern 1 … Trelleborg*. Kulturmiljörapport 2015:5. Kulturen, Lund.
- Strömberg, Märta 2001. Ale's Stones. A Monument of Recycled Boulders? *Lund Archaeological Review* 7.
- County Administrative Board of Skåne. *Kulturmiljöprogram för Skåne* (themes and areas), retrieved 2026-11-04.
- Swedish National Heritage Board 2026. *Riksintressen för kulturmiljövården – Skåne län*.
- Geological Survey of Sweden, shore-displacement model (open data, CC BY 4.0), with product description 2022.
- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License. Institute for Language and Folklore, place-name register, CC BY.
- Images: Wikimedia Commons, with the photographer and the licence in the caption."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert ":::" not in b and "/karta" not in b and "/statistik" not in b

out = {"slug": "de-gamla-landen-skane", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Geografi", "Norden", "Tro och magi"]}
from src import blog_labels  # noqa: E402
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
path = os.path.join(ROOT, "utdata", "blogg", "skane_land.json")
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
                 "topic": "Geografi|skane", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
