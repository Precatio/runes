"""Vitkis tidskrift Korpus – digital runforskning från Vitki (Viktor 2026-11-11: underrubriken Ristat & räknat struken; tidigare Viktor 2026-11-10: en egen tidskrift likt Futhark och Fornvännen, men för
digital forskning som Vitkis, för den som inte kan lägga all sin tid på att läsa; ljus, fräsch, professionell, PDF; "tänk
Populär Historia fast lite mer återhållsam"; namnet mellan Korpus och Ristat & räknat; en engelsk utgåva).
Bygger provnumret på svenska och engelska av tre publicerade artiklar (utdata/blogg/*.json, body och body_en) som HTML
och skriver ut dem till PDF med Chrome, i två varv så att innehållsförteckningen får rätt sidnummer. Skriver också en
omslagsjämförelse: Korpus mot Ristat & räknat som titel.
    python3 utdata/tidskrift/bygg_tidskrift.py"""
import html
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BLOGG = os.path.join(HERE, "..", "blogg")
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WM = "https://upload.wikimedia.org/wikipedia/commons/"
OMSLAG = WM + "9/9d/U_489%2C_Morby.jpg"
LOGO = "../../branding/vitki_logo.svg"  # Vitkis bindruna (Viktor 2026-11-10: på omslaget i stället för runraden)

ARTIKLAR = [  # per artikel: fil, öppningsbild i Commons, antal bilder i brödtexten, och per språk tema/siffran/lyftcitat
    dict(fil="dottrar.json", bild="5/5f/U29%2C_Hillersjoh%C3%A4llen.jpg", bilder=1,
         sv=dict(tema="Människorna", siffra="1 på 19", betyder="Så många stenar är resta efter en dotter för varje sten efter en son.",
                 citat="Ändå är det nitton gånger så många stenar efter söner som efter döttrar."),
         en=dict(bilder=0, tema="People", siffra="1 in 19", betyder="That many stones were raised for a daughter for every stone raised for a son.",
                 citat="Yet there are nineteen times as many stones for sons as for daughters.")),
    dict(fil="unga.json", bild="e/ec/Vg_61%2C_H%C3%A4rlingstorp.JPG", bilder=2,
         sv=dict(tema="Resorna", siffra="3–4 ×", betyder="Så mycket oftare dog söner och bröder utanför Norden än fäder och makar.",
                 citat="Den unge mannen var drengr, en i följet; den äldre var þegn, en man med gård och ansvar."),
         en=dict(bilder=0, tema="Journeys", siffra="3–4 ×", betyder="That much more often sons and brothers died outside the Nordic lands than fathers and husbands.",
                 citat="The young man was a drengr, one of the following; the older man was a þegn, a man with a farm and responsibilities.")),
    dict(fil="overlevde.json", bild="c/c3/Lorenz_Fr%C3%B8lich_-_%C3%86sir-Thor_-_NMH_425-1925_-_Nationalmuseum.jpg", bilder=2, staende=True,
         sv=dict(tema="Språket", siffra="1 av 5", betyder="Så stor del av namnen på runstenarna bärs fortfarande av svenskar i dag.",
                 citat="Drengr, hjälten, blev dräng."),
         en=dict(tema="Language", siffra="1 in 5", betyder="The share of the names on the runestones still borne by Swedes today.",
                 citat="Drengr, the hero, became dräng, the farmhand.")),
]

T = {
    "sv": dict(
        lang="sv", nr="Nr 1 · November 2026", fran="Tidskrift", undertitel="Digital runforskning från Vitki",
        fot="nr 1 · 2026", lastid="Text: Viktor Kvant · Lästid {m} minuter", siffran="Siffran", trettio="På 30 sekunder",
        webb="Hela artikeln med alla bilder, interaktiva diagram och data:",
        omtema="Människorna", omnum="14 <i>mot</i> 268",
        puffar=[("Resorna", None, "Söner och bröder dog borta tre till fyra gånger så ofta som fäder."),
                ("Språket", "Tor föll, hjälten blev dräng", "Vilka vikinganamn lever kvar – och vilka maktord bytte språk?"),
                ("Verkstaden", "Hundra års runforskning – lästa på en gång", "1 081 texter i Fornvännen och Futhark.")],
        provnummer="Provnummer<br>vitkirunor.se",
        omkredit="Omslag: U 489 vid Morby, Uppland – Gullaugs bro för dottern Gillaugs själ. Foto: Christine Jewell, CC BY-SA 2.0, via Wikimedia Commons.",
        innehall="I detta nummer",
        extra=[("Verkstaden", "Hundra års runforskning – lästa på en gång"), ("Metodhörnan", "Vad betyder p = 0,003?")],
        lasband=[("30 sek", "Rubriken, <i>Siffran</i> och <i>På 30 sekunder</i> ger fyndet och hur säkert det är."),
                 ("5 min", "Artikeln: hur vi kom fram till det, med diagram i procent och stenarna som exempel."),
                 ("På djupet", "<i>Så säkra är vi</i>, källorna och öppna data på vitkirunor.se.")],
        vflik="04 · Verkstaden", vrubrik="Hundra års runforskning – lästa på en gång",
        vdeck="Vi har läst varje text om runor och vikingatid i Fornvännen sedan 1906 och i Futhark sedan starten, och ställt samma fråga till alla: vad har den svenska runforskningen missat?",
        tal=[("1 081", "texter lästa, 1906–2023"), ("3 794", "påståenden som går att mäta mot data"), ("1", "fråga ställd till alla: vad har fältet missat?")],
        v1=("Det som återkommer", "Samma blinda fläckar dyker upp i text efter text, oberoende av varandra. Stilgrupperna och språket daterar varandra, med få fasta punkter utanför. Placeringar som ”vid vägen” eller ”vid gravfältet” prövas sällan mot slumpvis valda platser i samma bygd. Och de stenar vi känner är de som överlevde plogen, kyrkbyggena och 1600-talets inventerare."),
        v2=("Det vi gör nu", "Varje återkommande fråga blir en låst analysplan som prövas på hela korpusen. Resultaten kommer här i {namn} – också de som inte håller. Läsningen själv, med citat och källa för varje påstående, publiceras öppet så att andra kan granska den."),
        mflik="05 · Metodhörnan", mrubrik="Vad betyder p = 0,003?",
        mtext="Det betyder: om det inte fanns något verkligt mönster alls, skulle en lika stor skillnad som den vi ser dyka upp av ren slump ungefär tre gånger på tusen försök. Det är ungefär lika sällsynt som att få krona åtta gånger i rad med ett mynt. Det bevisar inget ensamt – men det säger att slumpen är en dålig förklaring, och att mönstret är värt att ta på allvar.",
        bak=[("Om {namn}", "{namn} är en öppen tidskrift för digital och kvantitativ runforskning, utgiven av Vitki. Den samlar Vitkis artiklar, rapporter och metodnotiser i en form som går att läsa på en kaffepaus. Den kommer ut på svenska och engelska."),
             ("Om Vitki", "Vitki är en öppen forskningsplattform för Nordens runinskrifter. Analyserna förregistreras, och kod, data och rapporter publiceras öppet på Zenodo."),
             ("Redaktion", "Viktor Kvant, redaktör<br>vitkirunor.se/kontakt"),
             ("Licens", "Texterna får spridas fritt under CC BY 4.0. Bilder från Wikimedia Commons har egna licenser, angivna vid varje bild."),
             ("Data", "Samnordisk runtextdatabas, Riksantikvarieämbetets Runor, SGU, ISOF och Kulturmiljöregistret. Bearbetning: Vitki.")],
        bakrad="Nr 1 · 2026 · Provnummer",
    ),
    "en": dict(
        lang="en", nr="No. 1 · November 2026", fran="Journal", undertitel="Digital runic research from Vitki",
        fot="No. 1 · 2026", lastid="Text: Viktor Kvant · Reading time {m} minutes", siffran="The number", trettio="In 30 seconds",
        webb="The full article with all images, interactive charts and data:",
        omtema="People", omnum="14 <i>to</i> 268",
        puffar=[("Journeys", None, "Sons and brothers died abroad three to four times as often as fathers."),
                ("Language", "Thor fell, the hero became a farmhand", "Which Viking names live on – and which words of power changed language?"),
                ("Workshop", "A century of runic research – read at once", "1,081 texts in Fornvännen and Futhark.")],
        provnummer="Sample issue<br>vitkirunor.se",
        omkredit="Cover: U 489 at Morby, Uppland – Gullaug's bridge for the soul of her daughter Gillaug. Photo: Christine Jewell, CC BY-SA 2.0, via Wikimedia Commons.",
        innehall="In this issue",
        extra=[("Workshop", "A century of runic research – read at once"), ("Method corner", "What does p = 0.003 mean?")],
        lasband=[("30 sec", "The headline, <i>The number</i> and <i>In 30 seconds</i> give you the finding and how certain it is."),
                 ("5 min", "The article: how we got there, with charts in percent and the stones as examples."),
                 ("In depth", "<i>How sure we are</i>, the sources and open data at vitkirunor.se.")],
        vflik="04 · Workshop", vrubrik="A century of runic research – read at once",
        vdeck="We have read every text on runes and the Viking Age in Fornvännen since 1906 and in Futhark since its start, and put the same question to all of them: what has Swedish runic research missed?",
        tal=[("1,081", "texts read, 1906–2023"), ("3,794", "claims that can be measured against data"), ("1", "question put to all of them: what has the field missed?")],
        v1=("What keeps coming back", "The same blind spots appear in text after text, independently of each other. Style groups and language date each other, with few fixed points outside. Placements such as “by the road” or “at the grave field” are rarely tested against randomly chosen places in the same district. And the stones we know are the ones that survived the plough, the church builders and the antiquarians of the 1600s."),
        v2=("What we do now", "Every recurring question becomes a locked analysis plan, tested on the whole corpus. The results will appear here in {namn} – including those that do not hold. The reading itself, with quotation and source for every claim, is published openly so that others can check it."),
        mflik="05 · Method corner", mrubrik="What does p = 0.003 mean?",
        mtext="It means: if there were no real pattern at all, a difference as large as the one we see would turn up by pure chance about three times in a thousand tries. That is about as rare as getting heads eight times in a row with a coin. It proves nothing on its own – but it tells us that chance is a poor explanation, and that the pattern is worth taking seriously.",
        bak=[("About {namn}", "{namn} is an open journal for digital and quantitative runic research, published by Vitki. It gathers Vitki's articles, reports and method notes in a form that can be read over a coffee break. It appears in Swedish and English."),
             ("About Vitki", "Vitki is an open research platform for the runic inscriptions of the Nordic countries. Analyses are pre-registered, and code, data and reports are published openly on Zenodo."),
             ("Editors", "Viktor Kvant, editor<br>vitkirunor.se/kontakt"),
             ("Licence", "Texts may be shared freely under CC BY 4.0. Images from Wikimedia Commons carry their own licences, given with each image."),
             ("Data", "Scandinavian Runic-text Database, the Swedish National Heritage Board's Runor, SGU, ISOF and the Swedish register of ancient monuments. Processing: Vitki.")],
        bakrad="No. 1 · 2026 · Sample issue",
    ),
}


# "I appen" (Viktor 2026-11-10): varje nummer förklarar en funktion i Vitki på en sida. Texten bygger på
# metoddokumentationen (METHODS.md) för funktionen; siffrorna är de publicerade.
APP = {
    "sv": dict(
        flik="06 · I appen", rubrik="Människorna: vem reste stenen, och efter vem?",
        deck="Människomodulen läser varje runsten som en liten släktberättelse: vilka som reste stenen, vem den döde var för dem och vad de sa om honom eller henne. Den ligger bakom två av artiklarna i det här numret.",
        gor=["För varje vikingatida runsten tar modulen fram hur många som reste stenen och deras kön, hur många döda och deras kön, och den dödes relation till resaren: barn, förälder, syskon, make eller maka, annan släkt. Den läser också berömmet – drengr, þegn, god och bäst – och om den döde dog utanför Norden.",
             "Könet bestäms i en fast ordning: först relationsordet (mor, dotter, hustru, son), sedan formeln (hennes son, hans son), sedan ett namnlexikon och sist namnets ändelse. Därefter prövar R sex frågor enligt en låst plan, med landsdel, tid och ristaren i modellen, och varje mönster prövas i två halvor av landet var för sig."],
        steg=["Öppna Statistik (R) i appen och välj Människorna.",
              "Läs frågan, nyckeltalet och svaret överst. Under dem står hur säkert mönstret är: bekräftar, mönster att pröva eller indikation.",
              "Pröva samma sak på din egen avgränsning under Egen fråga – till exempel bara Uppland eller bara 1000-talet."],
        kan_inte="Modulen ser bara de personer som texten nämner, och den kan missa namn där stenen är skadad. I en kontroll mot handkodning av 40 stenar som reglerna aldrig sett hade den rätt om kvinnor bland resarna på 39 och om relationen på 38. Den säger hur ofta något står på stenarna – inte hur ofta det hände.",
        panel="Två fynd ur modulen",
        rader=[("Kvinna bland resarna", [("Svealand", 31, True), ("Götaland", 17, False)]),
               ("Den döde dog utanför Norden", [("Söner och bröder", 10, True), ("Fäder och makar", 3, False)])],
        kalla="Källa: Vitkis analys av Samnordisk runtextdatabas, vikingatida svenska runstenar; låst plan 2026-10-28.",
        fot="Vitki är fri programvara och körs på din egen dator: github.com/Precatio/runes. Metoden: METHODS.md, avsnitt 1u.",
        kan_inte_rubrik="Vad den inte kan", steg_rubrik="Så gör du", gor_rubrik="Vad den gör", innehall=("I appen", "Människorna: vem reste stenen, och efter vem?"),
        bild="bilder/app_manniskorna_sv.jpg",
        bildtext="<b>Så ser det ut i appen:</b> Statistik (R) med de nya mönstren filtrerade på Människorna. De två första korten är fynden i diagrammet ovan. Skärmbild: Vitki."),
    "en": dict(
        flik="06 · In the app", rubrik="People: who raised the stone, and for whom?",
        deck="The people module reads every runestone as a small family story: who raised the stone, who the dead person was to them and what they said about him or her. It lies behind two of the articles in this issue.",
        gor=["For every Viking-age runestone the module finds how many raised the stone and their sex, how many dead and their sex, and the dead person's relation to the raiser: child, parent, sibling, spouse, other kin. It also reads the praise – drengr, þegn, good and best – and whether the dead person died outside the Nordic lands.",
             "Sex is decided in a fixed order: first the kin word (mother, daughter, wife, son), then the formula (her son, his son), then a name lexicon and last the name's ending. R then tests six questions under a locked plan, with region, period and the carver in the model, and every pattern is tested in two halves of the country separately."],
        steg=["Open Statistics (R) in the app and choose People.",
              "Read the question, the key number and the answer at the top. Below them it says how sure the pattern is: confirmed, pattern to test or indication.",
              "Try the same thing on your own selection under Your own question – only Uppland, for example, or only the 11th century."],
        kan_inte="The module sees only the people the text names, and it can miss names where the stone is damaged. Checked against hand-coding of 40 stones the rules had never seen, it was right about women among the raisers on 39 and about the relation on 38. It tells how often something is said on the stones – not how often it happened.",
        panel="Two findings from the module",
        rader=[("A woman among the raisers", [("Svealand", 31, True), ("Götaland", 17, False)]),
               ("The dead man died outside the Nordic lands", [("Sons and brothers", 10, True), ("Fathers and husbands", 3, False)])],
        kalla="Source: Vitki's analysis of the Scandinavian Runic-text Database, Swedish Viking-age runestones; locked plan 2026-10-28.",
        fot="Vitki is free software and runs on your own computer: github.com/Precatio/runes. The method: METHODS.md, section 1u.",
        kan_inte_rubrik="What it cannot do", steg_rubrik="How to use it", gor_rubrik="What it does", innehall=("In the app", "People: who raised the stone, and for whom?"),
        bild="bilder/app_manniskorna_en.jpg",
        bildtext="<b>What it looks like in the app:</b> Statistics (R) with the new patterns filtered on People. The first two cards are the findings in the chart above. Screenshot: Vitki."),
}


# "Från redaktören" (Viktor 2026-11-11): en stående spalt på s. 2 i varje nummer, bredvid innehållet, 250–400 ord,
# signerad av Viktor. Texten skriver VIKTOR SJÄLV (nr 1: redaktor_nr1.json, godkänd 2026-11-11, ordagrant). Sidan
# är provad med 400 ords text och håller sig på en sida; under 250 ord blir det luft ovanför läsbandet. Ett porträtt
# läggs in med "portratt": "bilder/<fil>.jpg" (tomt = inget porträtt).
REDAKTOR_SV = dict(
    rubrik="Alla stenar på en gång",
    text=["Mitt intresse för historia började med vår egen. Som ung läste jag Eddan och fängslades av Tor i striden mot jättarna och av Oden, som offrade sig själv för att vinna visdom. I yrkeslivet blev dataanalys mitt fält: att söka mönster i stora mängder data. Korpus är platsen där de två intressena möts.",
          "Runforskningen har länge utgått från den enskilda stenen – en läsning, en ristare, ett ord. Det arbetet har gett oss ett rikt och väldokumenterat material, insamlat och digitaliserat av generationer av forskare. Utan deras idoga insatser hade inget av det som följer varit möjligt. Men vissa frågor har sällan kunnat prövas: de som bara går att besvara när man räknar alla stenar på en gång.",
          "Det är de frågorna Korpus är till för. Vi ställer hela korpusen – drygt 2 300 svenska runstenar – mot jordarter, strandlinjer, ortnamn, gravfält och vägar, och vi prövar varje mönster mot slumpen innan vi kallar det ett fynd. Analysplanen låses innan vi räknar, och när ett resultat inte håller redovisar vi det lika öppet som när det gör det.",
          "Det som berör mig mest är ofta det som stenarna förtiger. Döttrarna, som så sällan fick samma röst som sönerna. Den gamla tron, som rymde många gudar och till och med gav plats åt den vite Krist, men som till sist fick ge vika för en lära med en enda gud. Jag vill veta vilka spår som ändå finns kvar och förstå mer av vårt arv: hur människorna tänkte, och vilken visdom de ville föra vidare.",
          "I det här numret möter du döttrarna som nästan aldrig fick en sten, de unga männen som inte kom hem från färderna och namnen som svenskar fortfarande bär i dag. Varje artikel kan läsas på trettio sekunder, på fem minuter eller på djupet, och alla data finns öppet tillgängliga på vitkirunor.se. Min förhoppning är att Korpus ska nå fram genom bruset av allt som tävlar om vår uppmärksamhet – och att vi på vårt sätt kan bidra till runforskningen."],
    portratt="",
)
REDAKTOR_EN = dict(
    rubrik="Every stone at once",
    text=["My interest in history began with our own. As a young man I read the Edda and was captivated by Thor in his battles with the giants, and by Odin, who sacrificed himself to win wisdom. In my working life, data analysis became my field: searching for patterns in large amounts of data. Korpus is where those two interests meet.",
          "Runic research has long started from the single stone – one reading, one carver, one word. That work has given us a rich and well-documented body of material, gathered and digitised by generations of scholars. Without their patient efforts, none of what follows would be possible. Yet some questions have seldom been tested: those that can only be answered by counting every stone at once.",
          "Those are the questions Korpus exists for. We set the whole corpus – more than 2,300 Swedish runestones – against soils, shorelines, place names, grave fields and roads, and we test every pattern against chance before we call it a finding. The analysis plan is locked before we count, and when a result does not hold, we report it as openly as when it does.",
          "What moves me most is often what the stones leave unsaid. The daughters, who so seldom got the same voice as the sons. The old faith, which held many gods and even made room for the White Christ, but in the end had to give way to a teaching with a single god. I want to know what traces remain, and to understand more of our heritage: how people thought, and what wisdom they wished to pass on.",
          "In this issue you will meet the daughters who almost never got a stone, the young men who did not come home from their journeys, and the names that Swedes still carry today. Every article can be read in thirty seconds, in five minutes or in depth, and all data are openly available at vitkirunor.se. My hope is that Korpus will reach you through the noise of everything competing for our attention – and that we, in our way, can contribute to runic research."],
    portratt="",
)
REDAKTOR = {"sv": REDAKTOR_SV, "en": REDAKTOR_EN}

# Nr 1 i 20 sidor (Viktor 2026-11-11: tryckeriet häftar i ark om fyra sidor; "om du saknar innehåll så fyll ut med något
# av vårt material från appen"). Nya sidor: Till läsaren med innehåll och kolofon (s. 2), kartan över alla stenar (s. 3),
# Runstenarna i siffror (s. 4) och Nästa nummer (s. 19). Alla tal på kartan och siffersidan räknas i korpusfakta().
NY = {
    "sv": dict(
        tillrubrik="Från redaktören",
        kolofon=[("{namn}", "Digital runforskning från Vitki<br>Nr 1 · November 2026"), ("Redaktion", "Viktor Kvant"),
                 ("Utgivare", "Vitki · vitkirunor.se"), ("Licens", "Texterna: CC BY 4.0. Bilderna har egna licenser, angivna vid varje bild.")],
        kflik="Kartan", krubrik="Var stenarna står",
        ktext="Varje prick är en vikingatida runsten eller ett fragment av en, där Samnordisk runtextdatabas placerar den. Tätast står de runt Mälaren; Uppland ensamt har hälften av alla.",
        kleg=[("finns kvar", "{bev}"), ("försvunna enligt databasen, kända från äldre avbildningar", "{lostk}"),
              ("i Skåne och Blekinge, som då hörde till Danmark", "{dk}")],
        knot="{Nk} av korpusens {N} stenar har en plats i databasen. Ringarna är vikingatida runstenar i dagens Sverige som har danska signum; de räknas inte i korpusens siffror på nästa sida.",
        kkredit="Karta: Vitki, efter Samnordisk runtextdatabas (ODbL). Kustlinjer och sjöar: Natural Earth.",
        sflik="I siffror", srubrik="Runstenarna i siffror",
        sdeck="Det här är korpusen som {namn} räknar på: alla vikingatida runstenar och fragment av runstenar från Sverige i Samnordisk runtextdatabas. Varje tal är räknat ur databasen för det här numret.",
        rutor=[("{N}", "runstenar och fragment från vikingatiden. Det är underlaget för varje artikel i numret."),
               ("{up_p} %", "kommer från Uppland, {up} stenar. Varannan svensk runsten är uppländsk."),
               ("{frag_p} %", "är fragment: {frag} stenar är bara delar av en sten. Nästan var tredje."),
               ("{lost_p} %", "är försvunna enligt databasen, {lost} stenar. De är kända från äldre avbildningar men finns inte kvar. Nästan var femte."),
               ("{sign_p} %", "är signerade: på {sign} stenar har ristaren skrivit in sitt namn. Ungefär en av tio."),
               ("{opir}", "stenar knyts säkert till Öpir, den ristare som har flest stenar i databasen. Alla utom {opir_ut} står i Uppland."),
               ("{kors_p} %", "har ett kors i ristningen, {kors} stenar. Fyra av tio."),
               ("{stil_p} %", "har en säker stilgrupp, {stil} stenar. Stilgruppen bygger på ornamentiken och är det vanligaste sättet att datera en runsten.")],
        sdiagram="Var stenarna kommer ifrån", sgrupp="Andel av alla {N} stenar", sovriga="Övriga landskap", senhet="stenar",
        skalla="Diagram: Vitki, efter Samnordisk runtextdatabas (ODbL).",
        rdiagram="Ristarna med flest stenar", rgrupp="Stenar som databasen säkert knyter till ristaren",
        rkalla="Diagram: Vitki, efter Samnordisk runtextdatabas (ODbL). Signerade och attribuerade stenar.",
        sboxh="Så räknade vi",
        sbox="Med runsten menar vi det som Samnordisk runtextdatabas (2014 års version, uppdaterad 2018) kallar runsten eller fragment av runsten, daterat till vikingatiden och med svenskt signum. Stenarna i Skåne, Blekinge och Halland har danska signum och är inte med. Försvunnen, signatur, ristare, kors och stilgrupp är databasens egna uppgifter; vi har inte prövat dem sten för sten. En ristare räknas när databasen anger honom utan frågetecken.",
        nflik="Nästa nummer · Nr 2 · Mars 2027", nrubrik="Det vi inte ser",
        ndeck="Runstenarna vi räknar är de som blev kvar, och de som blev kvar står inte alltid där de restes. Nästa nummer handlar om allt vi inte ser i korpusen – och om hur mycket det kan påverka det vi tror oss veta.",
        nblock=[("Stenarna som flyttades", "Många runstenar står inte där de en gång restes. De har murats in i kyrkor, flyttats till gårdar och parker eller ställts upp vid en väg i modern tid. Varje karta över var stenarna stod bygger på att vi vet vilka som har flyttats. Vi går igenom hur det går att veta."),
                ("Stenarna som försvann", "Nästan var femte sten i databasen är försvunnen och känd bara från äldre avbildningar och beskrivningar. Vilka stenar försvann, och var? Är de försvunna en slumpmässig del av korpusen, eller saknas vissa slags stenar oftare än andra?"),
                ("När restes stenen?", "De flesta runstenar dateras efter ornamentiken eller språket, och de två har till stor del daterat varandra. Vi beskriver vilka stenar som har en datering som inte vilar på stilen, och vad som händer med ett mönster när dateringen är osäker."),
                ("Ingvarsstenarna", "Stenarna efter männen som följde Ingvar österut är en av runforskningens mest kända grupper. De hör till samma färd och därmed till ungefär samma tid. Vi frågar vad en sådan grupp kan lära oss om resten av korpusen.")],
        nplan="Studierna är inte gjorda än. Planerna låses innan vi räknar, och resultaten – också de som inte håller – kommer i nästa nummer. I appen: Luckor i texten.",
        nlas="Läs {namn} fritt", nlastext="Alla nummer finns som PDF på svenska och engelska på <b>vitkirunor.se/tidskrift</b>, tillsammans med artiklarna i sin helhet, interaktiva diagram och öppna data. Appen Vitki, som analyserna görs i, är fri programvara: <b>github.com/Precatio/runes</b>. Skriv till oss: <b>vitkirunor.se/kontakt</b>.",
        innehall_extra=dict(karta=("Kartan", "Var stenarna står"), siffror=("I siffror", "Runstenarna i siffror"), nasta=("Nästa nummer", "Det vi inte ser")),
    ),
    "en": dict(
        tillrubrik="From the editor",
        kolofon=[("{namn}", "Digital runic research from Vitki<br>No. 1 · November 2026"), ("Editor", "Viktor Kvant"),
                 ("Publisher", "Vitki · vitkirunor.se"), ("Licence", "Texts: CC BY 4.0. Images carry their own licences, given with each image.")],
        kflik="The map", krubrik="Where the stones stand",
        ktext="Every dot is a Viking-age runestone or a fragment of one, where the Scandinavian Runic-text Database places it. They stand densest around Lake Mälaren; Uppland alone has half of them.",
        kleg=[("still exists", "{bev}"), ("lost according to the database, known from older drawings", "{lostk}"),
              ("in Skåne and Blekinge, which then belonged to Denmark", "{dk}")],
        knot="{Nk} of the corpus's {N} stones have a location in the database. The rings are Viking-age runestones in present-day Sweden with Danish signa; they are not counted in the corpus figures on the next page.",
        kkredit="Map: Vitki, after the Scandinavian Runic-text Database (ODbL). Coastlines and lakes: Natural Earth.",
        sflik="In numbers", srubrik="The runestones in numbers",
        sdeck="This is the corpus {namn} counts: every Viking-age runestone and fragment of a runestone from Sweden in the Scandinavian Runic-text Database. Every number is counted from the database for this issue.",
        rutor=[("{N}", "runestones and fragments from the Viking Age. This is the basis for every article in the issue."),
               ("{up_p} %", "come from Uppland, {up} stones. Every second Swedish runestone is from Uppland."),
               ("{frag_p} %", "are fragments: {frag} stones are only parts of a stone. Almost one in three."),
               ("{lost_p} %", "are lost according to the database, {lost} stones. They are known from older drawings but no longer exist. Almost one in five."),
               ("{sign_p} %", "are signed: on {sign} stones the carver wrote his name into the text. About one in ten."),
               ("{opir}", "stones are firmly tied to Öpir, the carver with the most stones in the database. All but {opir_ut} stand in Uppland."),
               ("{kors_p} %", "have a cross in the carving, {kors} stones. Four in ten."),
               ("{stil_p} %", "have a certain style group, {stil} stones. The style group rests on the ornament and is the most common way to date a runestone.")],
        sdiagram="Where the stones come from", sgrupp="Share of all {N} stones", sovriga="Other provinces", senhet="stones",
        skalla="Chart: Vitki, after the Scandinavian Runic-text Database (ODbL).",
        rdiagram="The carvers with the most stones", rgrupp="Stones the database firmly ties to the carver",
        rkalla="Chart: Vitki, after the Scandinavian Runic-text Database (ODbL). Signed and attributed stones.",
        sboxh="How we counted",
        sbox="By runestone we mean what the Scandinavian Runic-text Database (the 2014 version, updated 2018) calls a runestone or a fragment of a runestone, dated to the Viking Age and with a Swedish signum. The stones of Skåne, Blekinge and Halland have Danish signa and are not included. Lost, signature, carver, cross and style group are the database's own entries; we have not checked them stone by stone. A carver counts when the database gives him without a question mark.",
        nflik="Next issue · No. 2 · March 2027", nrubrik="What we cannot see",
        ndeck="The runestones we count are the ones that survived, and the ones that survived do not always stand where they were raised. The next issue is about everything we cannot see in the corpus – and how much it may change what we think we know.",
        nblock=[("The stones that were moved", "Many runestones no longer stand where they were once raised. They have been built into churches, moved to farms and parks or set up by a road in modern times. Every map of where the stones stood depends on knowing which ones have been moved. We look at how that can be known."),
                ("The stones that were lost", "Almost one stone in five in the database is lost and known only from older drawings and descriptions. Which stones were lost, and where? Are the lost stones a random part of the corpus, or are some kinds of stone missing more often than others?"),
                ("When was the stone raised?", "Most runestones are dated by their ornament or their language, and the two have largely dated each other. We describe which stones have a date that does not rest on the style, and what happens to a pattern when the date is uncertain."),
                ("The Ingvarr stones", "The stones for the men who followed Ingvarr to the east are among the best-known groups in runic research. They belong to the same expedition and so to roughly the same time. We ask what such a group can teach us about the rest of the corpus.")],
        nplan="The studies have not been run yet. The plans are locked before we count, and the results – including those that do not hold – will appear in the next issue. In the app: Gaps in the text.",
        nlas="Read {namn} for free", nlastext="Every issue is available as a PDF in Swedish and English at <b>vitkirunor.se/en/tidskrift</b>, together with the full articles, interactive charts and open data. The Vitki app, in which the analyses are made, is free software: <b>github.com/Precatio/runes</b>. Write to us: <b>vitkirunor.se/kontakt</b>.",
        innehall_extra=dict(karta=("The map", "Where the stones stand"), siffror=("In numbers", "The runestones in numbers"), nasta=("Next issue", "What we cannot see")),
    ),
}

LANDSKAP = {"sv": {"U": "Uppland", "Sö": "Södermanland", "Ög": "Östergötland", "Öl": "Öland", "Vg": "Västergötland", "Sm": "Småland", "G": "Gotland"},
            "en": {"U": "Uppland", "Sö": "Södermanland", "Ög": "Östergötland", "Öl": "Öland", "Vg": "Västergötland", "Sm": "Småland", "G": "Gotland"}}


def korpusfakta():
    """Talen på kartan och siffersidan, räknade ur data/rundata.json med samma urval som Vitkis analyser
    (src/research_gaps.is_runestone: vikingatid, svenskt signum, runsten eller fragment av runsten). Talen är låsta
    med assert så att en ny version av databasen inte i tysthet ändrar en tryckt siffra."""
    import collections
    import sys
    sys.path.insert(0, ROOT)
    from src.research_gaps import certain_carvers, has_style, is_runestone
    st = [r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"] if is_runestone(r)]
    prov = collections.Counter(r["signum"].split(" ")[0] for r in st)
    ristare = collections.Counter(c for r in st for c in set(certain_carvers(r)))
    topp, opir = ristare.most_common(1)[0]
    opir_up = sum("Öpir 1" in certain_carvers(r) and r["signum"].startswith("U ") for r in st)
    k = dict(N=len(st), up=prov["U"], frag=sum("fragment" in (r["object"] or "") for r in st), lost=sum(r["flags"]["lost"] for r in st),
             sign=sum(any(c["kind"] == "S" for c in r["carvers"]) for r in st), opir=opir, opir_ut=opir - opir_up,
             kors=sum(bool(r["cross_form"]) for r in st), stil=sum(has_style(r) for r in st),
             Nk=sum(r["lat"] is not None for r in st), lostk=sum(r["lat"] is not None and r["flags"]["lost"] for r in st))
    k["bev"] = k["Nk"] - k["lostk"]
    assert topp == "Öpir 1"
    assert (k["N"], k["up"], k["frag"], k["lost"], k["sign"], k["opir"], k["opir_ut"], k["kors"], k["stil"], k["Nk"], k["lostk"]) == \
        (2321, 1178, 725, 415, 248, 111, 3, 959, 1038, 2318, 414), k
    for n in ("up", "frag", "lost", "sign", "kors", "stil"):
        k[n + "_p"] = round(100 * k[n] / k["N"])
    k["prov"] = [(p, prov[p], round(100 * prov[p] / k["N"])) for p in LANDSKAP["sv"]]
    ovr = k["N"] - sum(n for _, n, _ in k["prov"])
    k["prov"].append(("*", ovr, round(100 * ovr / k["N"])))
    k["ristare"] = [(re.sub(r"\s+\d+$", "", r), n) for r, n in ristare.most_common(5)]
    assert k["ristare"] == [("Öpir", 111), ("Balle", 76), ("Fot", 68), ("Åsmund", 67), ("Gunnar", 42)], k["ristare"]
    punkter = [dict(signum=r["signum"], lat=r["lat"], lon=r["lon"], lost=r["flags"]["lost"], dk=False) for r in st if r["lat"] is not None]
    # Viktor 2026-11-11: kartan visar också stenarna i dagens Sverige som då var danska (Skåne, Blekinge, Halland; DR-signum).
    # De ritas som ringar och räknas bara här, aldrig i korpusens tal (Sverige-fokus: separata tal).
    dk = [r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
          if r["signum"].startswith("DR ") and r["period"] == "V" and "runsten" in (r.get("object") or "").lower()
          and (r.get("district") or "").split(", ")[-1] in ("Skåne", "Blekinge", "Halland") and r["lat"] is not None]
    k["dk"] = len(dk)
    assert k["dk"] == 61, k["dk"]
    punkter += [dict(signum=r["signum"], lat=r["lat"], lon=r["lon"], lost=r["flags"]["lost"], dk=True) for r in dk]
    return k, punkter


def tal(n, sprak):
    """Tusental med hårt mellanrum på svenska (2 321), med komma på engelska (2,321)."""
    return f"{n:,}".replace(",", " " if sprak == "sv" else ",") if isinstance(n, int) else n


def karta(punkter, tvinga=False):
    """Helsideskartan ritas av karta_korpus.R ur punkterna (en gång; --karta ritar om)."""
    png = os.path.join(HERE, "bilder", "karta_alla.png")
    pj = os.path.join(HERE, "bilder", "karta_punkter.json")
    ny = json.dumps(punkter, ensure_ascii=False)
    if tvinga or not os.path.exists(png) or not os.path.exists(pj) or open(pj, encoding="utf-8").read() != ny:
        open(pj, "w", encoding="utf-8").write(ny)
        subprocess.run(["Rscript", "--vanilla", os.path.join(HERE, "karta_korpus.R")], check=True)
    return "bilder/karta_alla.png"


def fyll(s, k, sprak, namn="Korpus"):
    return s.format(namn=namn, **{n: tal(v, sprak) for n, v in k.items() if not isinstance(v, list)})


def kartsida(N, k, sprak):
    leg = "".join(f'<li><i class="prick{["", " rost", " ring"][i]}"></i><span><b>{fyll(v, k, sprak)}</b> {t}</span></li>' for i, (t, v) in enumerate(N["kleg"]))
    return f"""
<section class="kartsida">
  <img class="bg" src="bilder/karta_alla.png" alt="">
  <div class="kartpanel">
    <div class="flik">{N["kflik"]}</div>
    <h2>{N["krubrik"]}</h2>
    <p>{fyll(N["ktext"], k, sprak)}</p>
    <ul class="kartleg">{leg}</ul>
  </div>
  <div class="kartkredit">{fyll(N["knot"], k, sprak)}<br>{N["kkredit"]}</div>
</section>"""


def siffersida(N, k, sprak, namn):
    rutor = "".join(f'<div><b>{fyll(b, k, sprak)}</b><span>{fyll(t, k, sprak)}</span></div>' for b, t in N["rutor"])
    rader = "".join(
        f'<div class="crow{" hi" if p == "U" else ""}"><div class="clab">{N["sovriga"] if p == "*" else LANDSKAP[sprak][p]}</div>'
        f'<div class="cbar"><span style="width:{max(pc, 0.8)}%"></span></div><div class="cval">{pc} %</div>'
        f'<div class="cnote">{tal(n, sprak)} {N["senhet"]}</div></div>' for p, n, pc in k["prov"])
    topp = k["ristare"][0][1]
    ristrader = "".join(
        f'<div class="crow{" hi" if i == 0 else ""}"><div class="clab">{r}</div><div class="cbar"><span style="width:{100 * n / topp:.1f}%"></span></div>'
        f'<div class="cval">{n}</div><div class="cnote">{N["senhet"]}</div></div>' for i, (r, n) in enumerate(k["ristare"]))
    return f"""
<section class="vanlig siffersida">
  <div class="flik">{N["sflik"]}</div>
  <h2>{N["srubrik"]}</h2>
  <p class="deck">{fyll(N["sdeck"], k, sprak, namn)}</p>
  <div class="rutor">{rutor}</div>
  <div class="tvaspalt sifferbotten">
    <figure class="chart sifferchart"><figcaption class="ctitle">{N["sdiagram"]}</figcaption>
      <div class="cgroup">{fyll(N["sgrupp"], k, sprak)}</div>{rader}<div class="csrc">{N["skalla"]}</div></figure>
    <figure class="chart sifferchart"><figcaption class="ctitle">{N["rdiagram"]}</figcaption>
      <div class="cgroup">{N["rgrupp"]}</div>{ristrader}<div class="csrc">{N["rkalla"]}</div></figure>
  </div>
  <aside class="box sifferbox"><div class="boxh">{N["sboxh"]}</div><p>{N["sbox"]}</p></aside>
</section>"""


def nastasida(N, namn):
    block = "".join(f'<div><h3>{h}</h3><p>{t}</p></div>' for h, t in N["nblock"])
    return f"""
<section class="vanlig nastasida">
  <div class="flik">{N["nflik"]}</div>
  <h2>{N["nrubrik"]}</h2>
  <p class="deck">{N["ndeck"]}</p>
  <div class="nastagrid">{block}</div>
  <p class="nplan">{N["nplan"]}</p>
  <div class="lasfritt"><div class="slab">{N["nlas"].format(namn=namn)}</div><p>{N["nlastext"]}</p>
    <img class="bindruna" src="{LOGO}" alt="Vitki"></div>
</section>"""


def appsida(A):
    rader = "".join(f'<div class="cgroup">{g}</div>' + "".join(
        f'<div class="crow{" hi" if hi else ""}"><div class="clab">{lab}</div><div class="cbar"><span style="width:{v}%"></span></div>'
        f'<div class="cval">{v} %</div><div class="cnote"></div></div>' for lab, v, hi in rows) for g, rows in A["rader"])
    steg = "".join(f"<li>{x}</li>" for x in A["steg"])
    return f"""
<section class="vanlig appsida">
  <div class="flik">{A["flik"]}</div>
  <h2>{A["rubrik"]}</h2>
  <p class="deck">{A["deck"]}</p>
  <div class="tvaspalt">
    <div>
      <h3>{A["gor_rubrik"]}</h3>{"".join(f"<p>{x}</p>" for x in A["gor"])}
      <h3>{A["steg_rubrik"]}</h3><ol class="appsteg">{steg}</ol>
    </div>
    <div>
      <figure class="chart appchart"><figcaption class="ctitle">{A["panel"]}</figcaption>{rader}<div class="csrc">{A["kalla"]}</div></figure>
      <aside class="box appbox"><div class="boxh">{A["kan_inte_rubrik"]}</div><p>{A["kan_inte"]}</p></aside>
    </div>
  </div>
  {f'<figure class="appbild"><img src="{A["bild"]}" alt=""><figcaption>{A["bildtext"]}</figcaption></figure>' if A.get("bild") else ""}
  <p class="appfot">{A["fot"]}</p>
</section>"""


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    return s


def caption(cap):
    c = inline(cap)
    m = re.match(r"([^:]{3,70}):(.*)", c, re.S)  # bildtextens början i fetstil, som i en tidskrift
    return f"<b>{m.group(1)}:</b>{m.group(2)}" if m else c


def chart(block):
    lines = [l for l in block.split("\n") if l.strip()]
    out = [f'<figure class="chart"><figcaption class="ctitle">{inline(lines[0])}</figcaption>']
    source = ""
    for l in lines[1:]:
        if l.startswith(("Källa", "Source")):
            source = l
            continue
        if l.startswith("#"):
            out.append(f'<div class="cgroup">{inline(l.lstrip("# "))}</div>')
            continue
        parts = [p.strip() for p in l.lstrip("+").split("|")]
        if len(parts) < 2:
            continue
        val = float(parts[1].replace(",", "."))
        note = parts[2] if len(parts) > 2 else ""
        out.append(f'<div class="crow{" hi" if l.startswith("+") else ""}"><div class="clab">{inline(parts[0])}</div>'
                   f'<div class="cbar"><span style="width:{max(val, 0.8):.1f}%"></span></div>'
                   f'<div class="cval">{val:g} %</div><div class="cnote">{inline(note)}</div></div>')
    if source:
        out.append(f'<div class="csrc">{inline(source)}</div>')
    return "\n".join(out + ["</figure>"])


def flyttattr(fid, flytt):
    """data-id för placeringen (se placera()); data-flytt = antal stycken som elementet flyttas framåt i texten."""
    n = (flytt or {}).get(fid, 0)
    return f' data-id="{fid}"' + (f' data-flytt="{n}"' if n else "")


def body_html(body, skip_img, citat, max_images=2, flytt=None):
    """BlogBody-markeringen till tidskriftens HTML. Första rutan ('Kort sagt'/'In short') blir 30-sekundersrutan på
    öppningssidan; den avslutande sammanfattningsrutan tas bort (upprepar början); anfang på första stycket; lyftcitat
    efter tredje stycket; källavsnitten i liten stil."""
    kort, parts, imgs, nparas, tail, nd = None, [], 0, 0, False, 0
    for b in re.split(r"(:::(?:box|chart)[^\n]*\n.*?\n:::)", body, flags=re.S):
        if b.startswith(":::chart"):
            nd += 1
            parts.append(chart(b[len(":::chart"):].rsplit(":::", 1)[0]).replace('<figure class="chart"', f'<figure class="chart"{flyttattr(f"d{nd}", flytt)}', 1))
            continue
        if b.startswith(":::box"):
            head, inner = b[len(":::box"):].split("\n", 1)
            head, inner = head.strip(), inner.rsplit(":::", 1)[0]
            items = [inline(l[2:]) for l in inner.split("\n") if l.startswith("- ")]
            text = [inline(l) for l in inner.split("\n") if l.strip() and not l.startswith("- ")]
            if kort is None and head.lower().startswith(("kort", "in short")):
                kort = items or text
            elif not re.search(r"viktigaste|essentials", head, re.I):
                # rubriken står redan i rutan: en mellanrubrik med samma ord direkt ovanför tas bort (Viktor 2026-11-10)
                if parts and parts[-1] == f"<h3>{inline(head)}</h3>":
                    parts.pop()
                ul = "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>" if items else ""
                parts.append(f'<aside class="box"><div class="boxh">{inline(head)}</div>'
                             + "".join(f"<p>{t}</p>" for t in text) + ul + "</aside>")
            continue
        lines, i = b.split("\n"), 0
        while i < len(lines):
            l = lines[i].rstrip()
            if not l:
                i += 1
                continue
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", l)
            if m:
                nxt = lines[i + 1] if i + 1 < len(lines) else ""
                cap = nxt if nxt.strip() and not nxt.startswith(("!", "#", ":::")) else ""
                if imgs < max_images and not tail and skip_img not in m.group(2):
                    parts.append(f'<figure class="img"{flyttattr(f"b{imgs + 1}", flytt)}><img src="{m.group(2)}" alt="{html.escape(m.group(1))}">'
                                 f'<figcaption>{caption(cap)}</figcaption></figure>')
                    imgs += 1
                i += 2 if cap else 1
                continue
            if l.startswith("## "):
                h = l[3:]
                if re.match(r"(Källor|Se själv|Sources|See for yourself)", h) and not tail:
                    parts.append('<div class="sources">')
                    tail = True
                parts.append(f"<h3>{inline(h)}</h3>")
            elif l.startswith("> "):
                parts.append(f"<blockquote>{inline(l[2:])}</blockquote>")
            elif l.startswith("- "):
                items = []
                while i < len(lines) and lines[i].startswith("- "):
                    items.append(f"<li>{inline(lines[i][2:])}</li>")
                    i += 1
                parts.append("<ul>" + "".join(items) + "</ul>")
                continue
            else:
                runcitat = l.startswith("*") and l.endswith("*")
                if runcitat:
                    parts.append(f'<p class="runcitat">{inline(l)}</p>')
                else:
                    if not tail:
                        nparas += 1
                    parts.append(f'<p{" class=forsta" if nparas == 1 and not tail else ""}>{inline(l)}</p>')
                    if nparas == 3 and not tail and citat:
                        parts.append(f'<blockquote class="pull"{flyttattr("q", flytt)}>{html.escape(citat)}</blockquote>')
                        citat = None
            i += 1
    if tail:
        parts.append("</div>")
    return kort or [], "\n".join(parts)


RUNOR = {"f": "M6 2V58M6 22L22 8M6 36L22 22", "u": "M6 58V2L22 18V58", "þ": "M6 2V58M6 18L20 30L6 42",
         "a": "M14 2V58M4 18L24 34", "r": "M6 58V2L20 14L6 28L22 58", "k": "M6 58V2M6 24L22 8"}


def runrad(scale=1.0):
    g = "".join(f'<path transform="translate({i * 34},0)" d="{RUNOR[k]}"/>' for i, k in enumerate("fuþark"))
    return (f'<svg class="runor" viewBox="0 0 204 60" width="{204 * scale:.0f}" height="{60 * scale:.0f}"><g fill="none" '
            f'stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">{g}</g></svg>')



SNAP_JS = """<script>
// Baslinjeraster: varje element i brödtexten som inte är vanlig text tar, med luften runt sig, ett helt antal rader.
// v4 (Viktor 2026-11-11, "inte all brödtext linjerar i nederkant"): luften kring bilder, citat, rutor och källor ligger
// som utfyllnad i ett omslag (div.snapwrap) i stället för som marginaler. Chrome stryker marginaler i slutet av en spalt,
// och då kom spaltraden före ett diagram över alla spalter – och all text efter det – bredvid rastret; tomma rader som
// egna element kunde i stället hamna överst i nästa spalt. Omslaget hålls ihop (break-inside: avoid) utom kring rutor
// och källor, som får brytas: en ruta har hela rader i sig (radavstånd, luft och rubrik mätta i rader) och får en hel
// rad före och efter. Diagram över alla spalter bryts aldrig och behåller marginaler: en hel rad ovanför (stryks den
// överst på en sida flyttas allt en hel rad, inte en halv) och resten under.
window.addEventListener('load', () => {
  const LH = 18;  // 13,5 pt
  // Placeringen (placera() i bygg_tidskrift.py): ett diagram, en bild eller ett citat flyttas n stycken framåt i texten,
  // så att det inte skjuts till nästa spalt eller sida och lämnar en kort spalt efter sig.
  document.querySelectorAll('.text > [data-flytt]').forEach(el => {
    let n = +el.dataset.flytt, t = el;
    while (n > 0 && t.nextElementSibling && !t.nextElementSibling.matches('.sources, .slut, .webb')) {
      t = t.nextElementSibling;
      if (t.tagName == 'P' && !t.classList.contains('runcitat')) n--;
    }
    if (t !== el) t.after(el);
  });
  const hojd = (el) => [...el.getClientRects()].reduce((s, r) => s + r.height, 0);
  document.querySelectorAll('.text > figure, .text > aside, .text > blockquote, .text > .sources').forEach(el => {
    const forst = !el.previousElementSibling;
    el.classList.add('snap');
    if (el.classList.contains('chart')) {
      const h = el.getBoundingClientRect().height, top = forst ? 0 : LH;
      const total = Math.ceil((h + top) / LH + 0.5) * LH;
      el.style.setProperty('margin-top', top + 'px', 'important');
      el.style.setProperty('margin-bottom', (total - h - top) + 'px', 'important');
      return;
    }
    const delbar = el.tagName == 'ASIDE' || el.classList.contains('sources');
    const w = document.createElement('div');
    w.className = 'snapwrap' + (delbar ? ' delbar' : '');
    el.before(w); w.appendChild(el);
    const h = hojd(el);
    let top, bottom;
    if (el.tagName == 'ASIDE' || (el.tagName == 'BLOCKQUOTE' && !el.classList.contains('pull')) || el.classList.contains('sources')) {
      top = forst ? 0 : LH; bottom = Math.ceil(h / LH - 0.02) * LH - h + LH; }
    else { top = forst ? 0 : LH * 0.5; bottom = Math.ceil((h + top) / LH + 0.5) * LH - h - top; }
    w.style.paddingTop = top + 'px'; w.style.paddingBottom = bottom + 'px';
  });
  document.body.dataset.snapped = '1';
});
</script>"""


# Tryckversionen (Helloprint, häftad A4): grå och svart text blir neutralt grå, så att den efter rensningen i
# gratonade() ligger i DeviceGray och hamnar på bara K-plåten; rosten och bilderna förblir RGB tills tryckeriets
# CMYK-profil (FOGRA39) finns. Varje kall grå ersätts med en neutral grå med samma ljushet.
GRATT = ["#2d3439", "#3a4249", "#5f6a73", "#8a949b", "#9aa2a8", "#a9b0b5", "#d8dcdf", "#e6e8e6", "#f1f2f0"]


def neutral(hexf):
    r, g, b = (int(hexf[i:i + 2], 16) for i in (1, 3, 5))
    v = round(0.2126 * r + 0.7152 * g + 0.0722 * b)
    return f"#{v:02x}{v:02x}{v:02x}"


def css_for(L, namn, arts, tryck=False):
    css = open(os.path.join(HERE, "korpus.css"), encoding="utf-8").read()
    css += f'\n@page {{ @bottom-right {{ content: "{namn} {L["fot"]}"; }} }}'
    for n, a in enumerate(arts, 1):  # löpande sidhuvud med artikelns tema
        css += (f'\n@page b{n} {{ @top-left {{ content: "{namn} · {a["tema"]}"; font: 700 7pt var(--sans); color: #b7410e; '
                f'letter-spacing: .14em; text-transform: uppercase; }} }}')
    if tryck:
        css += "\n" + open(os.path.join(HERE, "korpus_tryck.css"), encoding="utf-8").read()
        css = css.replace("#1d2226", "#000000")  # brödtexten och rubrikerna: 100 % K
        for f in GRATT:
            css = re.sub(re.escape(f), neutral(f), css, flags=re.I)
    return css


def omslag(L, namn, arts):
    lang = "lang" if len(namn) > 9 else ""
    p = L["puffar"]
    puffar = "".join(f'<div><div class="ptema">{t}</div><div class="pt">{html.escape(titel or arts[1]["title"])}</div><p>{txt}</p></div>'
                     for t, titel, txt in p)
    return f"""
<section class="omslag">
  <img class="bg" src="{OMSLAG}" alt="">
  <div class="omtopp">
    <div class="mastrad"><span>{L["nr"]}</span><span>{L["fran"]}</span></div>
    <h1 class="{lang}">{html.escape(namn)}</h1>
    <div class="undertitel">{L["undertitel"]}</div>
  </div>
  <div class="ompuff">
    <div class="ptema">{L["omtema"]}</div>
    <div class="pnum">{L["omnum"]}</div>
    <div class="ptitel">{html.escape(arts[0]["title"])}</div>
  </div>
  <div class="omband">{puffar}<div class="omruna"><img class="bindruna" src="{LOGO}" alt="Vitki"><span>{L["provnummer"]}</span></div></div>
  <div class="omkredit">{L["omkredit"]}</div>
</section>"""


def bygg(L, namn, arts, sidor, k, tryck=False):
    sprak = L["lang"]
    N = NY[sprak]
    nr = ["01", "02", "03"]
    kort_li = lambda t, r, key: (f'<li class="kort"><div><span class="ttema">{t}</span><span class="ttitle">{html.escape(r)}</span></div>'  # noqa: E731
                                 f'<span class="tsida">{sidor.get(key, "")}</span></li>')
    ix = N["innehall_extra"]
    innehall = kort_li(*ix["karta"], "karta") + kort_li(*ix["siffror"], "siffror")
    innehall += "".join(
        f'<li class="kort"><div><span class="ttema">{a["tema"]}</span>'
        f'<span class="ttitle">{html.escape(a["title"])}</span><span class="tdeck">{a["betyder"]}</span></div>'
        f'<span class="tsida">{sidor.get(a["title"], "")}</span></li>' for a in arts)
    innehall += "".join(kort_li(t, r, "verkstad") for t, r in L["extra"])
    A = APP[sprak]
    innehall += kort_li(*A["innehall"], "app") + kort_li(*ix["nasta"], "nasta")
    art_html = []
    for n, a in enumerate(arts, 1):
        kort = "".join(f"<li>{x}</li>" for x in a["kort"])
        art_html.append(f"""
<section class="opener">
  <figure class="hero{" staende" if a.get("staende") else ""}"><img src="{WM}{a["bild"]}" alt=""><figcaption>{a["hero_cap"]}</figcaption></figure>
  <div class="opentext">
    <div class="flik">{nr[n - 1]} · {a["tema"]}</div>
    <h2>{html.escape(a["title"])}</h2>
    <p class="deck">{inline(a["summary"])}</p>
    <p class="byline">{L["lastid"].format(m=a["minuter"])}</p>
    <div class="snabb">
      <div class="siffran"><div class="slab">{L["siffran"]}</div><div class="snum">{a["siffra"]}</div><p>{a["betyder"]}</p></div>
      <div class="trettio"><div class="slab">{L["trettio"]}</div><ul>{kort}</ul></div>
    </div>
  </div>
</section>
<section class="brodtext b{n}">
  <div class="text">{a["body"]}<p class="slut">■</p>
  <p class="webb">{L["webb"]} <b>vitkirunor.se{"/en" if sprak == "en" else ""}/artiklar/{a["slug"]}</b></p></div>
</section>""")
    R = REDAKTOR[sprak]
    # Typografi: hårt mellanrum i tusental (2 300) och ingen avstavning av webbadressen.
    def _typo(t):
        return re.sub(r"(\d) (\d{3})", "\\1\u00a0\\2", t).replace("vitkirunor.se", '<span class="nohy">vitkirunor.se</span>')
    led = "".join(f'<p{" class=forsta" if i == 0 else ""}>{_typo(t)}</p>' for i, t in enumerate(R["text"]))
    portratt = f'<img class="portratt" src="{R["portratt"]}" alt="Viktor Kvant">' if R.get("portratt") else ""
    kolofon = "".join(f'<div><b>{h.format(namn=namn)}</b> {t}</div>' for h, t in N["kolofon"])
    bak = "".join(f'<div class="bakblock"><div class="slab">{h.format(namn=namn)}</div><p>{t.format(namn=namn)}</p></div>' for h, t in L["bak"])
    return f"""<!doctype html><html lang="{sprak}"><head><meta charset="utf-8"><title>{namn} 1/2026</title>
<style>{css_for(L, namn, arts, tryck)}</style>{SNAP_JS}</head><body class="{"tryck" if tryck else "skarm"}">
{omslag(L, namn, arts)}
<section class="vanlig ledsida">
  <div class="ledgrid">
    <div class="ledare">
      <div class="slab">{N["tillrubrik"]}</div>
      <h2>{R["rubrik"]}</h2>
      <div class="redtext">{led}</div>
      <div class="sign">{portratt}<span>Viktor Kvant, {"redaktör" if sprak == "sv" else "editor"}</span></div>
    </div>
    <div class="innehallsspalt"><div class="slab">{L["innehall"]}</div><ol class="innehall">{innehall}</ol>
      <div class="kolofon">{kolofon}</div></div>
  </div>
  <div class="lasband">{"".join(f"<div><b>{b}</b><span>{s}</span></div>" for b, s in L["lasband"])}</div>
</section>
{kartsida(N, k, sprak)}
{siffersida(N, k, sprak, namn)}
{"".join(art_html)}
<section class="vanlig verkstad">
  <div class="flik">{L["vflik"]}</div>
  <h2>{L["vrubrik"]}</h2>
  <p class="deck">{L["vdeck"]}</p>
  <div class="tal">{"".join(f"<div><b>{b}</b><span>{s}</span></div>" for b, s in L["tal"])}</div>
  <div class="tvaspalt">
    <div><h3>{L["v1"][0]}</h3><p class="forsta">{L["v1"][1]}</p></div>
    <div><h3>{L["v2"][0]}</h3><p>{L["v2"][1].format(namn=namn)}</p></div>
  </div>
  <div class="metod"><div class="flik">{L["mflik"]}</div><h3>{L["mrubrik"]}</h3><p>{L["mtext"]}</p></div>
</section>
{appsida(APP[sprak])}
{nastasida(N, namn)}
<section class="vanlig baksida">
  <div class="baktext">{bak}</div>
  <div class="bakmast">{html.escape(namn)} <img class="bindruna" src="{LOGO}" alt="Vitki"><span>{L["bakrad"]}</span></div>
</section>
</body></html>"""


def skriv_pdf(doc, namn):
    h = os.path.join(HERE, namn + ".html")
    open(h, "w", encoding="utf-8").write(doc)
    pdf = os.path.join(HERE, namn + ".pdf")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--hide-scrollbars",
                    "--virtual-time-budget=30000", f"--print-to-pdf={pdf}", "file://" + h], check=True, capture_output=True)
    return pdf


def lokal_tumnagel(url):
    """Wikimedias tumnaglar levereras som WebP till Chrome, som då bäddar in dem okomprimerat (en enda bild blev 6 MB i
    PDF:en). Hämtas i stället en gång som JPEG till bilder/cache/ (samma pixelmått, så sidbrytningarna ändras inte)."""
    import urllib.request
    namn = re.sub(r"[^\w.,-]", "_", url.split("/")[-1])
    ut = os.path.join(HERE, "bilder", "cache", namn)
    if not os.path.exists(ut):
        os.makedirs(os.path.dirname(ut), exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Korpus-tidskrift/1.0 (build script)", "Accept": "image/jpeg"})
        data = urllib.request.urlopen(req, timeout=60).read()
        if data[:3] != b"\xff\xd8\xff":
            return url  # inte JPEG: behåll länken
        open(ut, "wb").write(data)
    return "bilder/cache/" + namn


def artiklar(sprak, placering=None):
    arts = []
    for ai, a in enumerate(ARTIKLAR):
        d = json.load(open(os.path.join(BLOGG, a["fil"]), encoding="utf-8"))
        suf = "_en" if sprak == "en" else ""
        body = d["body" + suf]
        fn = a["bild"].split("/")[-1]
        L = a[sprak]
        kort, html_body = body_html(body, fn, L["citat"], L.get("bilder", a["bilder"]), (placering or {}).get(str(ai)))
        html_body = re.sub(r'src="(https://thumb\.wikimedia\.org/[^"]+)"', lambda m: f'src="{lokal_tumnagel(m.group(1))}"', html_body)
        bl = body.split("\n")  # öppningsbildens bildtext och fotokredit tas ordagrant från artikeln
        cap = next((bl[j + 1] for j, l in enumerate(bl) if l.startswith("![") and fn in l and j + 1 < len(bl)), "")
        arts.append(dict(L, bild=a["bild"], staende=a.get("staende", False), hero_cap=caption(cap), title=d["title" + suf], summary=d["summary" + suf],
                         kort=kort, body=html_body, slug=d["slug"], minuter=max(1, round(len(body.split()) / 220))))
    return arts


SIDOR = 20  # tryckeriet häftar i ark om fyra sidor
TRYCK_SPRAK = ("sv",)  # Viktor 2026-11-11: bara den svenska utgåvan trycks; den engelska finns som PDF på webben
PLACERING = os.path.join(HERE, "placering.json")


def _rena(t):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip()


def flyttbara(doc):
    """(artikel, id) -> de första orden i elementets rubrik eller bildtext, ur den färdiga HTML:en."""
    ut = {}
    for ai, sek in enumerate(re.findall(r'<section class="brodtext b\d">(.*?)</section>', doc, re.S)):
        for fid, inner in re.findall(r'data-id="(\w+)"[^>]*>(.*?)</(?:figure|blockquote)>', sek, re.S):
            cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", inner, re.S)
            ord_ = _rena(cap.group(1) if cap else inner).split()
            ut[(str(ai), fid)] = " ".join(ord_[:3])
    return ut


def granska(pdf, doc, sidor, arts):
    """Spaltbottnar per brödtextsida. Returnerar (brist i mm totalt, korta sidor som [(artikel, sida)], beskrivning,
    var de flyttbara elementen står som {(artikel, id): sida})."""
    import tryckkontroll as tk
    rader = {s["sida"]: s for s in tk.baslinjer(pdf)}
    linjer = {nr: lines for nr, (W, H, lines) in enumerate(tk._sidor(pdf), 1)}
    lagen = {}
    for key, txt in flyttbara(doc).items():
        for nr, lines in linjer.items():
            if any(_rena(ln["text"]).startswith(txt) for ln in lines):
                lagen[key] = nr
                break
    oppnare = [sidor[a["title"]] for a in arts]
    slut = oppnare[1:] + [sidor["verkstad"]]
    brist, korta, besk = 0.0, [], []
    for ai, (o, e) in enumerate(zip(oppnare, slut)):
        for p in range(o + 1, e - 1):  # inte artikelns sista sida
            r = rader.get(p)
            if not r:
                continue
            b = [x if x is not None else 0 for x in r["botten"]]
            if any(x < 277.5 - 2 for x in b):
                brist += sum(max(0, 277.5 - x) for x in b)
                besk.append(f"s. {p}: {r['botten']}")
                korta.append((str(ai), p))
    return brist, korta, besk, lagen


def placera(sprak, namn="Korpus", svep=2, max_steg=4):
    """Flyttar diagram, bilder och lyftcitat stycke för stycke tills inga spalter står korta mitt i en artikel (Viktor
    2026-11-11: spalterna på en sida ska sluta på samma baslinje). Koordinatsökning: i varje artikel med korta sidor
    prövas varje flyttbart element 0–max_steg stycken framåt, ett element i taget, och det läge som ger minst brist
    behålls; två svep. Resultatet sparas i placering.json och används av varje bygge; kör igen (--placera) när en
    artikel eller layouten ändras."""
    L = T[sprak]
    k, _ = korpusfakta()
    alla = json.load(open(PLACERING, encoding="utf-8")) if os.path.exists(PLACERING) else {}
    n = [0]

    def prova(plac):
        n[0] += 1
        arts = artiklar(sprak, plac)
        doc = bygg(L, namn, arts, {}, k)
        pdf = skriv_pdf(doc, f"_placering_{sprak}")
        sidtext = sidkarta(pdf)
        brist, korta, besk, lagen = granska(pdf, doc, hitta_sidor(sidtext, L, arts, sprak), arts)
        return brist + (0 if len(sidtext) == SIDOR else 10000 * abs(len(sidtext) - SIDOR)), korta, besk, lagen

    plac = {a: dict(v) for a, v in alla.get(sprak, {}).items()}
    kost, korta, besk, lagen = prova(plac)
    print(f"  placering {sprak}: start {kost:.0f} mm {plac}; {'; '.join(besk)}", flush=True)
    for sv in range(svep):
        battre = False
        for ai in sorted({a for a, p in korta}):
            for fid in sorted(f for a2, f in lagen if a2 == ai):
                for val in range(max_steg + 1):
                    if val == plac.get(ai, {}).get(fid, 0):
                        continue
                    ny = json.loads(json.dumps(plac))
                    ny.setdefault(ai, {})[fid] = val
                    res = prova(ny)
                    if res[0] < kost - 0.5:
                        plac, (kost, korta, besk, lagen) = ny, res
                        battre = True
                        print(f"  placering {sprak} svep {sv}: {kost:.0f} mm {plac}; {'; '.join(besk)}", flush=True)
                if not korta:
                    break
        if not battre or not korta:
            break
    for f in (f"_placering_{sprak}.pdf", f"_placering_{sprak}.html"):
        if os.path.exists(os.path.join(HERE, f)):
            os.remove(os.path.join(HERE, f))
    alla = json.load(open(PLACERING, encoding="utf-8")) if os.path.exists(PLACERING) else {}
    alla[sprak] = {a: {f: v for f, v in d.items() if v} for a, d in plac.items() if any(d.values())}
    json.dump(alla, open(PLACERING, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  placering {sprak}: klar efter {n[0]} renderingar, brist {kost:.0f} mm, {alla[sprak]}; {'; '.join(besk)}", flush=True)
    return plac


def placering(sprak):
    return json.load(open(PLACERING, encoding="utf-8")).get(sprak, {}) if os.path.exists(PLACERING) else {}


def sidkarta(pdf):
    """Sidornas text, för innehållsförteckningen och sidkartan."""
    return subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True).stdout.split("\f")[:-1]


def hitta_sidor(sidtext, L, arts, sprak):
    N = NY[sprak]
    sidor = {}
    nalar = ([("karta", N["krubrik"]), ("siffror", N["srubrik"])] + [(a["title"], " ".join(a["title"].split()[:2])) for a in arts]
             + [("verkstad", L["vflik"]), ("app", APP[sprak]["flik"]), ("nasta", N["nflik"])])
    for key, needle in nalar:
        for p, t in enumerate(sidtext[2:], 3):
            if re.sub(r"\s", "", needle).upper() in re.sub(r"\s", "", t).upper():  # flikarna spärras och sätts i versaler
                sidor[key] = p
                break
    return sidor


def utgava(sprak, namn="Korpus", tryck=False):
    L, arts = T[sprak], artiklar(sprak, placering(sprak))
    k, punkter = korpusfakta()
    karta(punkter)
    fil = f"Korpus_nr1_{sprak}" + ("_tryck" if tryck else "")
    pdf = skriv_pdf(bygg(L, namn, arts, {}, k, tryck), fil)  # varv 1: utan sidnummer
    sidor = hitta_sidor(sidkarta(pdf), L, arts, sprak)
    pdf = skriv_pdf(bygg(L, namn, arts, sidor, k, tryck), fil)  # varv 2: med sidnummer
    sidtext = sidkarta(pdf)
    assert hitta_sidor(sidtext, L, arts, sprak) == sidor, "sidnumren flyttade sig mellan varven"
    print(sprak, "tryck" if tryck else "skärm", "sidor:", sidor)
    for p, t in enumerate(sidtext, 1):
        rader = [r for r in t.split("\n") if r.strip()]
        print(f"  {p:2d} {len(rader):3d} rader  {' '.join(rader[:2])[:80]}")
    assert len(sidtext) == SIDOR, f"{fil}: {len(sidtext)} sidor, inte {SIDOR}"
    if tryck:
        gratonade(pdf)
    return pdf


def gratonade(pdf):
    """Neutral grå och svart (r = g = b) i sidornas innehåll skrivs om från DeviceRGB till DeviceGray, så att
    svart text blir 100 % K och grå text en K-ton när tryckeriet eller Ghostscript går över till CMYK."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ContentStream, FloatObject, NameObject
    r = PdfReader(pdf)
    w = PdfWriter(clone_from=r)
    n = 0
    for page in w.pages:
        cs = ContentStream(page.get_contents(), w)
        ops = []
        for operands, op in cs.operations:
            if op in (b"rg", b"RG") and len(operands) == 3 and len({round(float(x), 4) for x in operands}) == 1:
                ops.append(([FloatObject(float(operands[0]))], b"g" if op == b"rg" else b"G"))
                n += 1
            else:
                ops.append((operands, op))
        cs.operations = ops
        page[NameObject("/Contents")] = w._add_object(cs)
    w.write(pdf)
    print(f"  gråtoner till DeviceGray: {n} färgval")


def tryckmatt(pdf):
    """Sidstorlek och boxar för tryckfilen: A4 med 3 mm utfall (216 x 303 mm); TrimBox = A4, BleedBox = hela sidan."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import RectangleObject
    mm = 72 / 25.4
    w = PdfWriter(clone_from=PdfReader(pdf))
    for page in w.pages:
        if "/Annots" in page:  # länkar är inte tillåtna i PDF/X och behövs inte i tryck
            del page["/Annots"]
        W, H = float(page.mediabox.width), float(page.mediabox.height)
        assert abs(W - 216 * mm) < 1.5 and abs(H - 303 * mm) < 1.5, (W / mm, H / mm)
        # Chrome avrundar sidbredden till hela pixlar (612 pt i stället för 612,28): boxarna sätts exakt 216 x 303 mm
        # och 210 x 297 mm, centrerade på sidan; skillnaden (0,05 mm per kant) ligger ytterst i utfallet.
        x0, y0 = (W - 216 * mm) / 2, (H - 303 * mm) / 2
        box = [x0, y0, x0 + 216 * mm, y0 + 303 * mm]
        page.mediabox = RectangleObject(box)
        page.cropbox = RectangleObject(box)
        page.bleedbox = RectangleObject(box)
        page.trimbox = RectangleObject([x0 + 3 * mm, y0 + 3 * mm, x0 + 213 * mm, y0 + 300 * mm])
    w.write(pdf)


def cmyk(pdf, icc, ut=None, villkor="FOGRA39"):
    """CMYK med tryckeriets profil via Ghostscript, som PDF/X-3 med profilen som OutputIntent (Helloprint: FOGRA39 /
    ISO Coated v2; för 300 % total färgmängd ISOcoated_v2_300_eci.icc). DeviceGray (svart och grå text efter
    gratonade()) går till bara K-plåten (-dDeviceGrayToK). Bilderna samplas inte ned."""
    ut = ut or pdf.replace(".pdf", "_cmyk.pdf")
    mall = open("/opt/homebrew/share/ghostscript/lib/PDFX_def.ps", encoding="latin-1").read()
    icc_ps = os.path.abspath(icc).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    mall = mall.replace("/ICCProfile (ISO Coated sb.icc) def", f"/ICCProfile ({icc_ps}) def")
    mall = mall.replace("/Title (Title)", "/Title (Korpus nr 1)")
    mall = mall.replace("/OutputConditionIdentifier (CGATS TR001)", f"/OutputConditionIdentifier ({villkor})")
    mall = mall.replace("/OutputCondition (Commercial and specialty printing)", f"/OutputCondition ({villkor})")
    defps = ut.replace(".pdf", "_PDFX_def.ps")
    open(defps, "w", encoding="latin-1").write(mall)
    subprocess.run(["gs", "-q", "-dBATCH", "-dNOPAUSE", "-dSAFER", f"--permit-file-read={os.path.abspath(icc)}", "-sDEVICE=pdfwrite", "-dPDFSETTINGS=/prepress", "-dPDFX=3", "-dCompatibilityLevel=1.4",
                    "-sColorConversionStrategy=CMYK", "-sProcessColorModel=DeviceCMYK", f"-sOutputICCProfile={icc}",
                    "-dDeviceGrayToK=true", "-dAutoRotatePages=/None",
                    "-dDownsampleColorImages=false", "-dDownsampleGrayImages=false", "-dEmbedAllFonts=true",
                    f"-sOutputFile={ut}", defps, pdf], check=True)
    os.remove(defps)
    return ut


def jamforelse():
    """Omslagen sida vid sida: Korpus och Ristat & räknat som titel, och Korpus på engelska."""
    sv, en = artiklar("sv"), artiklar("en")
    css = open(os.path.join(HERE, "korpus.css"), encoding="utf-8").read()
    doc = (f'<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Omslag</title><style>{css}</style></head><body>'
           + omslag(T["sv"], "Korpus", sv) + omslag(T["sv"], "Ristat & räknat", sv) + omslag(T["en"], "Korpus", en)
           + "</body></html>")
    return skriv_pdf(doc, "Omslag_Korpus_eller_Ristat")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tryck", action="store_true", help="skriv också tryckversionerna (A4 + 3 mm utfall) och tryck_kontroll.md")
    ap.add_argument("--bara-tryck", action="store_true", help="skriv bara tryckversionerna")
    ap.add_argument("--icc", help="tryckeriets CMYK-profil (FOGRA39 / ISO Coated v2); utan den förblir tryckfilen RGB")
    ap.add_argument("--karta", action="store_true", help="rita om helsideskartan")
    ap.add_argument("--placera", action="store_true", help="räkna om var diagram, bilder och citat står (placering.json)")
    a = ap.parse_args()
    if a.placera:
        for sprak in ("sv", "en"):
            placera(sprak)
    if a.karta:
        karta(korpusfakta()[1], tvinga=True)
    for sprak in ("sv", "en"):
        if not a.bara_tryck:
            print(utgava(sprak))
        if (a.tryck or a.bara_tryck) and sprak in TRYCK_SPRAK:
            pdf = utgava(sprak, tryck=True)
            tryckmatt(pdf)
            print(pdf)
            if a.icc:
                print(cmyk(pdf, a.icc))
    if a.tryck or a.bara_tryck:
        import tryckkontroll
        tryckkontroll.rapport(HERE, a.icc, TRYCK_SPRAK)
