"""Artikeln "Vad den Höge säger tusen år senare": en humanistisk läsning av Hávamál – vilka beröringspunkter dikten har
med en läsare tusen år efter att den diktades – inramad av mätningen av rösten (havamal_rosten.py). Varje siffra hämtas
ur analysfilerna i utdata/Edda och låses med asserts; varje citerad strof står ordagrant i Codex Regius-textens
normaliserade utgåva (havamal_strofer.csv). Bilderna är public domain, kontrollerade mot Commons API 2026-10-19.
    ../../../.venv/bin/python build_havamal.py [--write | --update DOC]"""
import csv
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
E = os.path.join(ROOT, "utdata", "Edda")
STROF = list(csv.DictReader(open(os.path.join(E, "havamal_strofer.csv"))))

svn = lambda x, d=1: f"{x:.{d}f}".replace(".", ",")  # noqa: E731

# ---- låsningarna ---------------------------------------------------------------------------------
d76 = {int(r["nr"]): r for r in STROF}
assert len(STROF) == 164 and "deyr fé" in d76[76]["text"].lower() and "orðstírr" in d76[76]["text"]
full = " ".join(r["text"].lower() for r in STROF)
assert all(full.count(w) == 0 for w in ("krist", "kirkj", "messa", "synd"))

# ---- rösten mot kristen och hednisk dikt (havamal_rosten.py) --------------------------------------
RO = json.load(open(os.path.join(E, "havamal_rosten.json")))
rk, G, VN, BT, EKr, EFr, SK = RO["kristet"], RO["gava"], RO["van"], RO["betra"]["del_I"], RO["ek"], RO["ef"], RO["skall"]["hela"]
assert rk["Hávamál"]["traffar"] == 0 and rk["hedniska_dialoger"]["traffar"] == 0
assert rk["Hugsvinnsmál"]["per100"] == 0.42 and rk["Sólarljóð"]["per100"] == 1.55
# gåvans och vänskapens etik delas av Hávamál och Hugsvinnsmål, men inte av de hedniska dialogerna
assert G["mot_hugsvinnsmal"]["p"] > 0.5 and VN["mot_hugsvinnsmal"]["p"] > 0.5
assert G["mot_hedniska"]["p"] < 0.001 and VN["mot_hedniska"]["p"] < 0.001
assert 4 <= G["mot_hedniska"]["per100_a"] / G["mot_hedniska"]["per100_b"] <= 6
assert 10 <= VN["mot_hedniska"]["per100_a"] / VN["mot_hedniska"]["per100_b"] <= 14
# 'bättre': gästvisdomen mot Hugsvinnsmål och dialogerna
assert BT["mot_hugsvinnsmal"]["p"] < 0.01 and BT["mot_hedniska"]["p"] < 0.001
assert BT["mot_hugsvinnsmal"]["a"] == 13 and BT["mot_hugsvinnsmal"]["b"] == 4
# jaget: Hugsvinnsmål bedömer (5) eller undervisar (3); Hávamáls kann ek
assert EKr["hugsvinnsmal_bedomer"] == 5 and EKr["hugsvinnsmal_undervisar"] == 3 and EKr["kann_ek"] == 18
assert EKr["hela"]["mot_hedniska"]["p"] > 0.1, "jag-formen är inte unik mot dialogerna"
# kasserade mått: 'ef' faller utan refrängen, 'skal' skiljer inte
assert EFr["utan_refrang"]["mot_hugsvinnsmal"]["p"] > 0.5 and EFr["refranger"][0] == 20
assert EFr["hela"]["mot_hugsvinnsmal"]["a"] - EFr["utan_refrang"]["mot_hugsvinnsmal"]["a"] == 2 * EFr["refranger"][0]
assert SK["mot_hugsvinnsmal"]["p"] > 0.1
# de citerade stroferna står ordagrant i texten
for nr, ord_ in ((1, "Gáttir allar"), (1, "hvar óvinir sitja á fleti fyrir"), (2, "Gefendr heilir"), (3, "Elds er þörf"), (3, "á kné kalinn"),
                 (4, "orðs ok endrþögu"), (8, "lof ok líknstafi"), (12, "Er-a svá gótt sem gótt kveða"), (16, "elli gefr hánum engi frið"),
                 (23, "Ósviðr maðr vakir um allar nætr"), (23, "allt er víl sem var"), (36, "þat er þó betra en bæn"), (38, "Vápnum sínum"),
                 (41, "endrgefendr"), (42, "gjalda gjöf við gjöf"), (46, "glík skulu gjöld gjöfum"), (47, "Ungr var ek forðum"),
                 (47, "maðr er manns gaman"), (48, "Mildir, fræknir menn bazt lifa"), (50, "Hrörnar þöll"), (52, "með halfum hleif"),
                 (54, "Meðalsnotr"), (56, "örlög sín viti engi fyrir"), (57, "maðr af manni verðr at máli kuðr"),
                 (66, "Mikilsti snemma kom ek í marga staði"), (69, "Er-at maðr alls vesall"), (69, "sumr af verkum vel"),
                 (70, "Betra er lifðum en sé ólifðum"), (71, "nýtr manngi nás"), (72, "bautarsteinar"), (76, "orðstírr deyr aldregi"),
                 (77, "dómr um dauðan hvern"), (78, "Fullar grindr sá ek"), (78, "nú bera þeir vánar völ"), (84, "Meyjar orðum"),
                 (91, "brigðr er karla hugr konum"), (105, "ill iðgjöld lét ek hana"), (111, "sá ek ok þagðak"),
                 (119, "far þú at finna oft"), (121, "sorg etr hjarta"), (131, "varan bið ek þik vera ok eigi ofvaran"),
                 (138, "gefinn Óðni, sjalfr sjalfum mér"), (139, "Við hleifi mik"), (144, "Veistu, hvé blóta skal"),
                 (145, "ey sér til gildis gjöf"), (164, "njóti sá, er nam")):
    assert ord_ in d76[nr]["text"], (nr, ord_)
_hug = open(os.path.join(E, "kallor", "hugsvinnsmal_norront.txt"), encoding="utf-8").read()
for ord_ in ("gjǫld af guði hygg ek gumnar taki", "ef veizt þik syndgan sjálfr"):
    assert ord_ in _hug, ord_
ett_pa = lambda p: f"{round((1 / p) / 10 ** (len(str(int(1 / p))) - 2)) * 10 ** (len(str(int(1 / p))) - 2):,}".replace(",", " ")  # noqa: E731
f2 = lambda x: svn(x, 2)  # noqa: E731
ORD = {k: f"{v:,}".replace(",", " ") for k, v in RO["ord"].items()}
e2 = lambda x, dd=2: f"{x:.{dd}f}"  # noqa: E731  (engelska: decimalpunkt)

IMG_CR = "https://upload.wikimedia.org/wikipedia/commons/5/50/Codex_Regius_of_Eddaic_Poems.jpg"
PAGE_CR = "https://commons.wikimedia.org/wiki/File:Codex_Regius_of_Eddaic_Poems.jpg"
IMG_ODIN = "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/4d/Odin%27s_Self-sacrifice_by_Collingwood.jpg/1280px-Odin%27s_Self-sacrifice_by_Collingwood.jpg"
PAGE_ODIN = "https://commons.wikimedia.org/wiki/File:Odin%27s_Self-sacrifice_by_Collingwood.jpg"
IMG_GUNN = "https://upload.wikimedia.org/wikipedia/commons/1/1f/Odin_and_Gunnl%C3%B6%C3%B0_by_Fr%C3%B8lich.jpg"
PAGE_GUNN = "https://commons.wikimedia.org/wiki/File:Odin_and_Gunnl%C3%B6%C3%B0_by_Fr%C3%B8lich.jpg"

title = "Vad den Höge säger tusen år senare"
summary = ("Hávamál diktades för omkring tusen år sedan och nådde oss i en enda handskrift. Vi mätte först hur rösten låter "
           "– utan Gud, med ett jag som minns – och läste sedan dikten som den själv ber om att bli läst: som råd till en "
           "människa. Om att komma som gäst, om ensamhet och vänskap, om gåvor och blot, om sömnlösa nätter, om ålderdom "
           "och om eftermälet – och vad som står kvar för den som läser i dag.")

body = f"""Hávamál, ”den Höges tal”, är Nordens mest citerade dikt: etthundrasextiofyra strofer råd, varningar, kärleksäventyr och trolldom. Forskningen daterar det mesta av dikten till 900-talet, men den nådde oss i en enda handskrift, Codex Regius, nedskriven på Island omkring 1270. Den som läser dikten i dag läser alltså något som tänktes ut för omkring tusen år sedan, av människor som inte visste att vi skulle finnas, och som ändå talar till oss i du-form. Det är den situationen den här artikeln handlar om: vad en så gammal text kan ha för beröringspunkter med en läsare tusen år senare.

Vi gjorde en sak innan vi läste. Vi mätte rösten – mot kristna dikter i samma versmått och mot hedniska – för att veta vem det är som talar och vad slags råd det är. Det tar ett kort avsnitt. Resten är en läsning, strof för strof, översatta så ordagrant vi kan.

![Uppslag ur Codex Regius]({IMG_CR})
Codex Regius (GKS 2365 4to), nedskriven omkring 1270 – Hávamáls enda medeltida källa. Allt här är läst och mätt på den textens normaliserade utgåva (Guðni Jónsson). Bild: public domain, via [Wikimedia Commons]({PAGE_CR}).

## Vilken röst är det som talar?

Vi ställde Hávamál mot tre grupper av dikter i samma versmått, ljóðaháttr: de hedniska dialogdikterna (Vafþrúðnismál, Grímnismál, Skírnismál, Lokasenna, Alvíssmál, Sigrdrífumál och Fjölsvinnsmál) och två kristna, *Sólarljóð*, en visionsdikt om en död man som ser straff och nåd, och *Hugsvinnsmál*, en kristen bearbetning av den latinska visdomsboken Disticha Catonis – liksom Hávamál ett råd från en far till en son.

Tre saker visade sig. Hávamál har inte ett enda ord ur det kristna ordförrådet – *guð*, *synd*, *sál*, *drottinn*, *náð* – medan Hugsvinnsmál har dem {svn(rk['Hugsvinnsmál']['per100'], 1)} gånger per hundra ord och Sólarljóð {svn(rk['Sólarljóð']['per100'], 1)}. Det är David Evans gamla iakttagelse (1986) uttryckt i siffror. (Ordet *bæn* står en gång, men i strof 36 betyder det ’tiggeri’: *þat er þó betra en bæn*, ’det är ändå bättre än att tigga’.) Men vänskapens och gåvans etik skiljer inte hedniskt från kristet: ord för gåva och gäld står {f2(G['mot_hugsvinnsmal']['per100_a'])} gånger per hundra ord i Hávamál och {f2(G['mot_hugsvinnsmal']['per100_b'])} i Hugsvinnsmál, ord för vän {f2(VN['mot_hugsvinnsmal']['per100_a'])} mot {f2(VN['mot_hugsvinnsmal']['per100_b'])}, men bara {f2(G['mot_hedniska']['per100_b'])} respektive {f2(VN['mot_hedniska']['per100_b'])} i de hedniska dialogerna. Att gälda gåva med gåva och vårda sina vänner hör till visdomslitteraturen, inte till tron; det är den tanke Marcel Mauss byggde sin studie av gåvan på, här mätt.

Det tredje är hur råden ges. Hávamál jämför: ordet *betra*, ’bättre’, står {f2(BT['mot_hugsvinnsmal']['per100_a'])} gånger per hundra ord i gästvisdomen mot {f2(BT['mot_hugsvinnsmal']['per100_b'])} i Hugsvinnsmál ({BT['mot_hugsvinnsmal']['a']} träffar mot {BT['mot_hugsvinnsmal']['b']}, en skillnad slumpen ger ungefär en gång på {ett_pa(BT['mot_hugsvinnsmal']['p'])} – en antydan, inte ett bevis). Råden är sällan bud utan avvägningar mellan det sämre och det bättre. Och jaget minns i stället för att döma: i Hugsvinnsmál är jaget *hygg ek* och *tel ek*, ’jag tror’, ’jag räknar’, fem av dess åtta *ek*; i Hávamál är det *Ungr var ek forðum* (47), ’ung var jag förr’, och *Fullar grindr sá ek* (78), ’fulla fållor såg jag’. Gälden står mellan människor, *glík skulu gjöld gjöfum* (46), inte som i Hugsvinnsmál inför Gud: *gjǫld af guði hygg ek gumnar taki*.

Det är alltså den rösten som möter läsaren: ingen domare, inga löften om något efter döden, en människa som har varit med om saker och väger det ena mot det andra. Det är också därför dikten fortfarande går att läsa som råd. Den kräver ingen tro av den som lyssnar.

## Att komma in genom dörren

Dikten börjar inte med visdom utan med en dörr. Strof 1:

> *Gáttir allar, áðr gangi fram, um skoðask skyli, um skyggnast skyli, því at óvíst er at vita, hvar óvinir sitja á fleti fyrir.*

Alla dörrar bör man se sig om i, speja i, innan man går fram; för ovisst är att veta var ovänner sitter på bänken därinne.

Sedan vänder dikten sig om och talar för värden. *Gefendr heilir!* (2), ’hell er, givare!’ – en gäst har kommit in, var ska han sitta? Den som kommit in är frusen om knäna och behöver eld (3), mat och kläder efter färden över fjället, och vatten, handduk och ett vänligt välkomnande (4). Det sista på listan över vad gästen behöver är det märkligaste: *orðs ok endrþögu*, ’ett ord – och tystnad i gengäld’. Att få säga något och bli lyssnad på.

Det är en lista som inte har åldrats. Byt fjället mot ett flyg eller en flytt, och den som kommer in genom dörren behöver fortfarande precis det här: värme, mat, ett ställe att sitta, och någon som tiger medan man berättar. Hávamáls första råd till den som tar emot en främling är att lyssna.

## Människan är människans glädje

Det mesta den Höge säger handlar om andra människor, och den mest citerade raden står i strof 47:

> *Ungr var ek forðum, fór ek einn saman, þá varð ek villr vega; auðigr þóttumk, er ek annan fann, maðr er manns gaman.*

Ung var jag förr, jag for ensam; då gick jag vilse på vägen. Rik tyckte jag mig, när jag fann en annan: människan är människans glädje.

En av de största farorna i Hávamál är inte döden utan ensamheten, och det säger strof 50 med en bild ur skogen:

> *Hrörnar þöll, sú er stendr þorpi á, hlýr-at henni börkr né barr; svá er maðr, sá er manngi ann. Hvat skal hann lengi lifa?*

Förtorkas gör tallen som står vid byn; varken bark eller barr skyddar henne. Så är den människa som ingen älskar. Varför ska en sådan leva länge?

Botemedlet är samtalet. *Maðr af manni verðr at máli kuðr* (57), ’människa blir känd av människa genom talet’, som brand tänds av brand; den som inte talar med någon blir *dælskr af dul*, dum av sin avskildhet. Och det är ett underhållsarbete. Strof 119: *far þú at finna oft*, gå ofta och hälsa på din vän, för på en väg som ingen trampar växer buskar och högt gräs. Loddfáfnismál lägger till det som kanske är diktens ömmaste rad, strof 121: *sorg etr hjarta, ef þú segja né náir einhverjum allan hug* – sorg äter hjärtat, om du inte får säga någon hela ditt sinne.

En läsare i dag känner igen alltihop, och kanske mer än någon generation före oss. Vi har fler sätt att nå varandra än någon annan tid och fler som ändå inte har någon att säga allt till. Hávamál har inget svar på det, men den har diagnosen: vägen växer igen om ingen går på den, och den som inte får tala blir sjuk av det.

## Gåva mot gåva – och blotet

Vänskapens underhåll har sin bokföring, och den står i strof 42:

> *Vin sínum skal maðr vinr vera ok gjalda gjöf við gjöf.*

Mot sin vän ska man vara en vän och gälda gåva med gåva. De som ger och ger igen, säger strof 41, förblir längst vänner. Det är diktens ekonomi: ingen är skyldig någon något för alltid, och därför kan vänskapen leva. Och gåvan behöver inte vara stor. Strof 52: *með halfum hleif ok með höllu keri fekk ek mér félaga* – med ett halvt bröd och en lutad bägare fick jag mig en följeslagare.

Samma tanke återkommer i ett av diktens mest främmande ord, blot. I strof 144 ställer den Höge åtta frågor – *veistu, hvé rísta skal*, ’vet du hur man ska rista’ – och en av dem är *veistu, hvé blóta skal*, ’vet du hur man ska blota’. Ett svar står i strof 145, och det är samma ömsesidighet:

> *Betra er óbeðit en sé ofblótit, ey sér til gildis gjöf.*

Bättre ej bedd än för mycket offrat; en gåva ser alltid efter sin gengåva. Blotet är alltså inte något främmande och högtidligt utan vänskapens bokföring riktad uppåt: man ger för att få, och man ska ge lagom. Dikten varnar för överdriften, men lika tydligt för snålheten: *mildir, fræknir menn bazt lifa*, ’frikostiga, tappra män lever bäst’ (48).

Den dyraste gåvan i dikten är den Höges egen. I strof 138 hänger han nio nätter i trädet, *gefinn Óðni, sjalfr sjalfum mér*, ’given åt Oden, själv åt mig själv’, och i strof 139 får han varken bröd eller dryckeshorn. Det han köper är runorna, och han tar dem *æpandi*, ’skrikande’. Det som gör offret stort är inte att det är högt utan att det kostar.

![Odens självoffer i trädet, tecknat av W.G. Collingwood]({IMG_ODIN})
Odens självoffer (strof 138): nio nätter i trädet, ”gåva åt Oden, han själv åt sig själv”. Teckning: W.G. Collingwood (1908), public domain, via [Wikimedia Commons]({PAGE_ODIN}).

Vad blotar vi i dag? Det är en fråga dikten inte ställer, men som dess ord gör rimlig, och här tillåter vi oss en tolkning som inte är diktens egen. Vi offrar något varje dag. Det som kostar har bara blivit något annat än boskap och mjöd: för oss har det dyrbara blivit vår tid och vår uppmärksamhet, och vi ger bort dem hela dagarna, ofta utan att fråga vad vi får tillbaka. Då är den Höges fråga inte ett arkaiskt krav utan en vass fråga om det egna livet: vet du hur du ska ge bort dina dagar, och vad väntar gåvan sig av dig? *Ey sér til gildis gjöf.* Och varningen gäller också här: *betra er óbeðit en sé ofblótit*. Man kan offra för mycket av sin uppmärksamhet åt sådant som aldrig ger något tillbaka.

## Natten då allt är som det var

Det finns en strof i Hávamál som kunde vara skriven i går natt. Strof 23:

> *Ósviðr maðr vakir um allar nætr ok hyggr at hvívetna; þá er móðr, er at morgni kemr, allt er víl sem var.*

Den ovise ligger vaken alla nätter och grubblar över allting; så är han trött när morgonen kommer, och allt elände är som det var.

Tusen år före ordet ångest står här dess hela kliniska bild: vakan, grubblet som griper allt, tröttheten och det bittra i att ingenting blev bättre av det. Den Höge ger inget botemedel, men han sätter grubblet i den ovises kolumn, och det är i sig ett slags råd: det hjälper inte att veta mer om natten. Samma röst säger i strof 12 att ölet inte är så gott som det sägs vara, *því at færa veit, er fleira drekkr síns til geðs gumi* – för den som dricker mer vet mindre om sitt eget sinne.

Det hänger ihop med diktens mest oväntade råd, att inte veta för mycket:

> *Meðalsnotr skyli manna hverr, æva til snotr sé … örlög sín viti engi fyrir, þeim er sorgalausastr sefi.*

Måttligt vis ska var människa vara, aldrig alltför vis … ingen ska i förväg veta sitt öde; då är sinnet friast från sorg (54, 56). Strof 55 säger att den alltför visas hjärta sällan blir glatt, och strof 131 har samma balans: *varan bið ek þik vera ok eigi ofvaran*, ’vaksam ber jag dig vara, men inte alltför vaksam’. Dikten som prisar kunskapen varnar för för mycket av den. För en läsare som kan veta nästan allt om nästan alla, hela tiden, och ligga vaken över det, är det kanske diktens mest tidsenliga rad.

Uppmärksamheten är ändå diktens första lärdom: *sá ek ok þagðak, sá ek ok hugðak, hlýdda ek á manna mál* (111), ’jag såg och teg, jag såg och tänkte, jag lyssnade till människornas tal’. Ordningen är att se, tiga, tänka och lyssna innan man talar. Samma strof är utgångspunkten för essän [Korpen som heter Minne](/artiklar/korpen-som-heter-minne).

## Ålderdomen, kroppen och det som duger

Dikten är också rak om det vi helst inte talar om. Strof 16 säger att den fege tror sig leva för evigt om han aktar sig för strid – *en elli gefr hánum engi frið, þótt hánum geirar gefi*, ’men ålderdomen ger honom ingen fred, om än spjuten gör det’. Det går inte att smita.

Men strof 69 och 71 vänder på det:

> *Er-at maðr alls vesall, þótt hann sé illa heill; sumr er af sonum sæll, sumr af frændum, sumr af fé ærnu, sumr af verkum vel.*

Ingen är helt eländig, även om hälsan är dålig: en är lycklig av söner, en av fränder, en av rikligt gods, en av goda gärningar. Och strof 71: den halte rider häst, den handlöse vallar hjorden, den döve strider och duger; blind är bättre än bränd – *nýtr manngi nás*, ’ingen har nytta av ett lik’.

Det är en hård röst, men inte en kall. Den mäter inte människan efter hennes skada utan efter vad hon ändå kan, och den räknar upp fyra olika sätt att ha ett gott liv utan att rangordna dem. För en tid som gärna mäter människor efter en enda skala är det en ovanligt rymlig syn på vad som duger.

## Domen över de döda – och stenarna vid vägen

Måttet på ett liv är till sist vad som blir kvar av det. Strof 76 och 77 är diktens mest berömda:

> *Deyr fé, deyja frændr, deyr sjalfr it sama, en orðstírr deyr aldregi, hveim er sér góðan getr.*

Boskap dör, fränder dör, själv dör man likaså; men eftermälet dör aldrig för den som får sig ett gott. Och strof 77 säger vad det är som består: *ek veit einn, at aldrei deyr: dómr um dauðan hvern* – jag vet ett som aldrig dör: domen över varje död.

Det är exakt den tanke som reste varje runsten, och dikten vet det. Strof 72 säger att *bautastenar sällan står vid vägen om inte frände reser dem efter frände* – seden som de tusentals stenarna i Vitkis korpus består av, resta vid vägar och broar av fränder efter fränder. Läsaren som står framför en runsten i dag står alltså framför Hávamáls strof 77 i sten: någons dom över någon död, huggen för att överleva dem båda. Det har den gjort. Vi läser den.

Men det är en röst som inte gör sig själv felfri. I strof 105 säger den Höge om Gunnlöd, som gav honom mjödet:

> *Gunnlöð mér of gaf gullnum stóli á drykk ins dýra mjaðar; ill iðgjöld lét ek hana eftir hafa síns ins heila hugar, síns ins svára sefa.*

Gunnlöd gav mig, på gyllene stol, en dryck av den dyra mjöden; ond lön lät jag henne få för sitt hela hjärta, sitt tunga sinne.

![Oden och Gunnlöd, tecknade av Lorenz Frølich]({IMG_GUNN})
Oden hos Gunnlöd, tecknad av Lorenz Frølich. Bild: public domain, via [Wikimedia Commons]({PAGE_GUNN}).

Den som har lärt ut att gälda gåva med gåva erkänner här att han själv gäldade en gåva illa. Det är samma jag som hängde nio nätter i trädet, och han räknar sina egna fel lika öppet som sina offer. En visdom som kan säga *ill iðgjöld lét ek* är svårare att avfärda än en som aldrig misstar sig – och lättare att ta till sig tusen år senare, för den talar inte uppifrån.

## Att ta den till sig – eller låta den stå stilla

Efter allt detta återstår en fråga: ska vi ta Hávamál till oss i dag, eller låta den vara en bild av våra förfäder, fryst i tiden? Dikten är ärlig om att mycket i den hör till sin tid. Rådet att inte gå ett steg från sina vapen på fältet (38) hör hemma i en värld utan polis, och rådet att aldrig lita på en kvinnas ord (84) är en misstro vi inte vill ta med oss – även om samma röst i strof 91 öppet säger att det är männens hjärta som är opålitligt mot kvinnorna. Den som tar hela dikten bokstavligt får både vishet och förhinder.

Men det som hör till sin tid är svaren, inte frågorna: hur tar jag emot den som kommer in genom dörren, hur undviker jag ensamheten, vad ger jag för det jag får, hur mycket ska jag veta, vad gör jag med en natt som inte vill ta slut, vad duger jag till när kroppen sviker, och hur blir jag ihågkommen? Och dikten ber själv om att användas, inte bevaras. Loddfáfnismáls refräng lovar nytta åt den som tar emot: *njóta mundu, ef þú nemr*, ’du får nytta, om du tar det till dig’. Den sista strofen kallar orden *allþörf ýta sonum*, ’till stor nytta för människors söner’, och avslutas med välsignelser åt den som kvad, den som kan, den som lärt och dem som lyssnat: *njóti sá, er nam* (164), ’må den njuta som har lärt’. En bild fryst i tiden ger ingen någon nytta.

Visdom är alltså tidsbunden i sina svar men inte i sina frågor, och den överlever bara så länge någon prövar den mot sitt eget liv. Strof 119 kan vem som helst pröva i kväll, genom att höra av sig till en vän man inte hört av på ett år. Strof 4 kan prövas nästa gång någon kommer in genom dörren: ett ord, och tystnad i gengäld. Det är vår läsning av vad det betyder att ta Hávamál till sig.

:::box Det viktigaste i korthet
- Rösten i Hávamál är en människas, inte en domares: den saknar Gud, synd och själ, väger det sämre mot det bättre och minns i stället för att döma. Det är därför dikten går att läsa som råd av en läsare som inte delar dess tro.
- Dess beröringspunkter med oss ligger i frågorna, inte svaren: gästen vid dörren, ensamheten, gåvan och gengåvan, den sömnlösa natten, kroppen som sviker och eftermälet. Varje runsten är strof 77 i sten.
- Vänskapens och gåvans etik är visdomens, inte hedendomens – den kristna Hugsvinnsmál delar den – och blotet är samma ömsesidighet riktad uppåt. Det dyra är det som kostar; för oss är det tid och uppmärksamhet.
- Dikten ber själv om att användas, inte bevaras, och den är ärlig om att en del av dess svar hör till sin tid. Att ta den till sig är att pröva dess frågor mot sitt eget liv.
:::

:::box Så räknade vi
Texten är Codex Regius-textens normaliserade utgåva (Guðni Jónsson), 164 strofer, {ORD['Hávamál']} ord; alla citat står ordagrant där, och översättningarna är våra. Jämförelsen mot kristen och hednisk dikt gjordes med fasta ordlistor och Fishers exakta test, som frågar hur ofta en slump skulle ge en lika stor skillnad; vi anger det som ”en gång på …”. Jämförelsetexterna är Hugsvinnsmál (Finnur Jónssons utgåva), Sólarljóð och de sju hedniska dialogdikterna (Guðni Jónssons utgåvor) med {ORD['Hugsvinnsmál']}, {ORD['Sólarljóð']} och {ORD['hedniska_dialoger']} ord. Eftersom utgåvorna stavar olika använde vi bara ord vars stavning är lika. Hugsvinnsmál är en bearbetning av en latinsk förebild, så resultaten gäller just de här jämförelserna. Två mått kasserades när vi prövade dem mot sina egna artefakter: ordet *ef* (som mest speglar Loddfáfnismáls refräng) och *skal* (som inte skiljer dikterna åt). Mätningarna av diktens skikt, sömmar och ordförråd mot runstenarna ligger öppet i kodförrådet (utdata/Edda) men ingår inte i den här artikeln, som är en läsning.
:::

## Källor och data

- Hávamál: Guðni Jónssons normaliserade utgåva av Codex Regius-texten (Eddukvæði, Sæmundar-Edda), via heimskringla.no.
- Hugsvinnsmál: Finnur Jónsson (utg.), Den norsk-islandske skjaldedigtning, 1912–15, via heimskringla.no. Sólarljóð och de hedniska dialogdikterna: Guðni Jónssons utgåvor, via heimskringla.no.
- Utgåva och kommentar: David A. H. Evans, Hávamál (Viking Society, 1986). Datering: Mikael Males, Maal og Minne 2024:1, s. 81–117.
- Gåvans etik: Marcel Mauss, ”Essai sur le don”, L’Année sociologique 1923–24.
- Analyskod och resultat: utdata/Edda i Vitkis kodförråd.
- Bilder: Wikimedia Commons, public domain, med upphov i bildtexterna."""

body_en = f"""Hávamál, "the words of the High One", is the North's most quoted poem: one hundred and sixty-four stanzas of advice, warnings, love adventures and magic. Scholarship dates most of the poem to the tenth century, but it reached us in a single manuscript, the Codex Regius, written down in Iceland around 1270. Whoever reads the poem today is reading something thought out about a thousand years ago, by people who did not know we would exist, and who nevertheless address us as "you". That situation is what this article is about: what points of contact such an old text can have with a reader a thousand years later.

We did one thing before reading. We measured the voice – against Christian poems in the same metre and against pagan ones – to know who is speaking and what kind of advice it is. That takes one short section. The rest is a reading, stanza by stanza, translated as literally as we can.

![Opening of the Codex Regius]({IMG_CR})
The Codex Regius (GKS 2365 4to), written down around 1270 – Hávamál's only medieval source. Everything here is read and measured on that text's normalised edition (Guðni Jónsson). Image: public domain, via [Wikimedia Commons]({PAGE_CR}).

## Whose voice is it?

We set Hávamál against three groups of poems in the same metre, ljóðaháttr: the pagan dialogue poems (Vafþrúðnismál, Grímnismál, Skírnismál, Lokasenna, Alvíssmál, Sigrdrífumál and Fjölsvinnsmál) and two Christian ones, *Sólarljóð*, a vision poem about a dead man who sees punishment and grace, and *Hugsvinnsmál*, a Christian adaptation of the Latin wisdom book Disticha Catonis – like Hávamál, advice from a father to a son.

Three things showed. Hávamál has not a single word from the Christian vocabulary – *guð*, *synd*, *sál*, *drottinn*, *náð* – while Hugsvinnsmál has them {e2(rk['Hugsvinnsmál']['per100'], 1)} times per hundred words and Sólarljóð {e2(rk['Sólarljóð']['per100'], 1)}. That is David Evans's old observation (1986) in numbers. (The word *bæn* occurs once, but in stanza 36 it means 'begging': *þat er þó betra en bæn*, 'that is still better than begging'.) But the ethics of friendship and gifts does not separate pagan from Christian: words for gift and repayment stand {e2(G['mot_hugsvinnsmal']['per100_a'])} times per hundred words in Hávamál and {e2(G['mot_hugsvinnsmal']['per100_b'])} in Hugsvinnsmál, words for friend {e2(VN['mot_hugsvinnsmal']['per100_a'])} against {e2(VN['mot_hugsvinnsmal']['per100_b'])}, but only {e2(G['mot_hedniska']['per100_b'])} and {e2(VN['mot_hedniska']['per100_b'])} in the pagan dialogues. Repaying gift with gift and tending one's friends belong to wisdom literature, not to belief; it is the thought Marcel Mauss built his study of the gift on, here measured.

The third is how the advice is given. Hávamál compares: the word *betra*, 'better', stands {e2(BT['mot_hugsvinnsmal']['per100_a'])} times per hundred words in the guest wisdom against {e2(BT['mot_hugsvinnsmal']['per100_b'])} in Hugsvinnsmál ({BT['mot_hugsvinnsmal']['a']} hits against {BT['mot_hugsvinnsmal']['b']}, a difference chance gives about once in {ett_pa(BT['mot_hugsvinnsmal']['p'])} – a hint, not proof). The advice is seldom commands and mostly trade-offs between the worse and the better. And the I remembers instead of judging: in Hugsvinnsmál the I is *hygg ek* and *tel ek*, 'I think', 'I count', five of its eight *ek*; in Hávamál it is *Ungr var ek forðum* (47), 'young I was once', and *Fullar grindr sá ek* (78), 'full folds I saw'. Repayment stands between people, *glík skulu gjöld gjöfum* (46), not, as in Hugsvinnsmál, before God: *gjǫld af guði hygg ek gumnar taki*.

So this is the voice that meets the reader: no judge, no promises about anything after death, a person who has been through things and weighs one against the other. That is also why the poem can still be read as advice. It asks no belief of the listener.

## Coming in through the door

The poem does not begin with wisdom but with a door. Stanza 1:

> *Gáttir allar, áðr gangi fram, um skoðask skyli, um skyggnast skyli, því at óvíst er at vita, hvar óvinir sitja á fleti fyrir.*

All doorways, before going forward, one should look around in, should peer into; for it is uncertain to know where enemies sit on the bench inside.

Then the poem turns and speaks for the host. *Gefendr heilir!* (2), 'hail, givers!' – a guest has come in, where shall he sit? The one who has come in is cold about the knees and needs fire (3), food and clothes after the journey over the mountain, and water, a towel and a friendly welcome (4). The last item on the list of what the guest needs is the strangest: *orðs ok endrþögu*, 'a word – and silence in return'. To be allowed to say something and be listened to.

It is a list that has not aged. Replace the mountain with a flight or a move, and the one who comes in through the door still needs exactly this: warmth, food, a place to sit, and someone who keeps quiet while they tell. Hávamál's first advice to whoever receives a stranger is to listen.

## Man is man's joy

Most of what the High One says is about other people, and the most quoted line is in stanza 47:

> *Ungr var ek forðum, fór ek einn saman, þá varð ek villr vega; auðigr þóttumk, er ek annan fann, maðr er manns gaman.*

Young I was once, I travelled alone; then I lost my way. Rich I felt when I found another: man is man's joy.

One of the greatest dangers in Hávamál is not death but loneliness, and stanza 50 says so with an image from the forest:

> *Hrörnar þöll, sú er stendr þorpi á, hlýr-at henni börkr né barr; svá er maðr, sá er manngi ann. Hvat skal hann lengi lifa?*

The pine that stands by the village withers; neither bark nor needles shelter it. So is the person whom no one loves. Why should such a one live long?

The remedy is conversation. *Maðr af manni verðr at máli kuðr* (57), 'a person becomes known to a person through speech', as fire is kindled from fire; whoever speaks with no one becomes *dælskr af dul*, dull from seclusion. And it is maintenance work. Stanza 119: *far þú at finna oft*, go often to see your friend, for on a road no one treads, brush and tall grass grow. Loddfáfnismál adds what may be the poem's tenderest line, stanza 121: *sorg etr hjarta, ef þú segja né náir einhverjum allan hug* – sorrow eats the heart if you cannot tell someone your whole mind.

A reader today recognises all of it, perhaps more than any generation before us. We have more ways of reaching each other than any other age, and more people who still have no one to tell everything to. Hávamál has no answer to that, but it has the diagnosis: the road grows over if no one walks it, and the one who cannot speak falls ill of it.

## Gift for gift – and the blót

Friendship's maintenance has its bookkeeping, and it stands in stanza 42:

> *Vin sínum skal maðr vinr vera ok gjalda gjöf við gjöf.*

To his friend a man should be a friend and repay gift with gift. Those who give and give back, says stanza 41, remain friends longest. That is the poem's economy: no one owes anyone anything forever, and so friendship can live. And the gift need not be large. Stanza 52: *með halfum hleif ok með höllu keri fekk ek mér félaga* – with half a loaf and a tilted cup I got myself a companion.

The same thought returns in one of the poem's strangest words, blót. In stanza 144 the High One asks eight questions – *veistu, hvé rísta skal*, 'do you know how to carve' – and one of them is *veistu, hvé blóta skal*, 'do you know how to sacrifice'. One answer stands in stanza 145, and it is the same reciprocity:

> *Betra er óbeðit en sé ofblótit, ey sér til gildis gjöf.*

Better not asked than over-sacrificed; a gift always looks for its return. The blót is thus nothing foreign and solemn but friendship's bookkeeping turned upwards: one gives in order to get, and one should give in measure. The poem warns against excess, but just as plainly against stinginess: *mildir, fræknir menn bazt lifa*, 'generous, brave men live best' (48).

The costliest gift in the poem is the High One's own. In stanza 138 he hangs nine nights in the tree, *gefinn Óðni, sjalfr sjalfum mér*, 'given to Odin, myself to myself', and in stanza 139 he gets neither bread nor drinking horn. What he buys is the runes, and he takes them *æpandi*, 'screaming'. What makes the sacrifice great is not that it is lofty but that it costs.

![Odin's self-sacrifice in the tree, drawn by W.G. Collingwood]({IMG_ODIN})
Odin's self-sacrifice (stanza 138): nine nights in the tree, “a gift to Odin, himself to himself”. Drawing: W.G. Collingwood (1908), public domain, via [Wikimedia Commons]({PAGE_ODIN}).

What do we sacrifice today? That is a question the poem does not ask, but its words make it reasonable, and here we allow ourselves an interpretation that is not the poem's own. We sacrifice something every day. What costs has simply become something other than cattle and mead: for us the precious has become our time and our attention, and we give them away all day long, often without asking what we get back. Then the High One's question is not an archaic demand but a sharp question about one's own life: do you know how to give away your days, and what does the gift expect of you? *Ey sér til gildis gjöf.* And the warning applies here too: *betra er óbeðit en sé ofblótit*. One can sacrifice too much of one's attention to things that never give anything back.

## The night when everything is as it was

There is a stanza in Hávamál that could have been written last night. Stanza 23:

> *Ósviðr maðr vakir um allar nætr ok hyggr at hvívetna; þá er móðr, er at morgni kemr, allt er víl sem var.*

The unwise man lies awake all nights and broods over everything; so he is weary when morning comes, and all the misery is as it was.

A thousand years before the word anxiety, here is its whole clinical picture: the wakefulness, the brooding that seizes everything, the tiredness and the bitterness that nothing got better for it. The High One offers no cure, but he puts the brooding in the unwise man's column, and that is itself a kind of advice: it does not help to know more at night. The same voice says in stanza 12 that ale is not as good as it is said to be, *því at færa veit, er fleira drekkr síns til geðs gumi* – for the one who drinks more knows less of his own mind.

It belongs with the poem's most unexpected advice, not to know too much:

> *Meðalsnotr skyli manna hverr, æva til snotr sé … örlög sín viti engi fyrir, þeim er sorgalausastr sefi.*

Moderately wise should everyone be, never too wise … let no one know their fate in advance; then the mind is freest from sorrow (54, 56). Stanza 55 says that the heart of the all-too-wise is seldom glad, and stanza 131 has the same balance: *varan bið ek þik vera ok eigi ofvaran*, 'wary I bid you be, but not over-wary'. The poem that praises knowledge warns against too much of it. For a reader who can know nearly everything about nearly everyone, all the time, and lie awake over it, that may be the poem's most timely line.

Attention is still the poem's first lesson: *sá ek ok þagðak, sá ek ok hugðak, hlýdda ek á manna mál* (111), 'I saw and kept silent, I saw and thought, I listened to the speech of men'. The order is to see, be silent, think and listen before speaking. The same stanza is the starting point of the essay [Korpen som heter Minne](/artiklar/korpen-som-heter-minne) (in Swedish).

## Old age, the body and what is good enough

The poem is also plain about what we would rather not talk about. Stanza 16 says that the coward thinks he will live forever if he avoids fighting – *en elli gefr hánum engi frið, þótt hánum geirar gefi*, 'but old age gives him no peace, even if the spears do'. There is no slipping away.

But stanzas 69 and 71 turn it around:

> *Er-at maðr alls vesall, þótt hann sé illa heill; sumr er af sonum sæll, sumr af frændum, sumr af fé ærnu, sumr af verkum vel.*

No one is wholly wretched, even if in poor health: one is happy in sons, one in kinsmen, one in ample wealth, one in good deeds. And stanza 71: the lame rides a horse, the handless herds the flock, the deaf fights and is of use; blind is better than burned – *nýtr manngi nás*, 'no one has use of a corpse'.

It is a hard voice, but not a cold one. It does not measure a person by their injury but by what they can still do, and it lists four different ways of having a good life without ranking them. For an age that likes to measure people on a single scale, that is an unusually roomy view of what is good enough.

## The verdict on the dead – and the stones by the road

The measure of a life is in the end what remains of it. Stanzas 76 and 77 are the poem's most famous:

> *Deyr fé, deyja frændr, deyr sjalfr it sama, en orðstírr deyr aldregi, hveim er sér góðan getr.*

Cattle die, kinsmen die, oneself dies the same; but the word-fame never dies for the one who earns a good one. And stanza 77 says what it is that endures: *ek veit einn, at aldrei deyr: dómr um dauðan hvern* – I know one thing that never dies: the verdict on each dead person.

That is exactly the thought that raised every runestone, and the poem knows it. Stanza 72 says that *memorial stones seldom stand by the road unless kinsman raises them for kinsman* – the custom that the thousands of stones in Vitki's corpus consist of, raised by roads and bridges by kinsmen for kinsmen. The reader who stands before a runestone today is standing before Hávamál's stanza 77 in stone: someone's verdict on someone dead, cut to outlive them both. It has. We are reading it.

But this is a voice that does not make itself faultless. In stanza 105 the High One says of Gunnlöð, who gave him the mead:

> *Gunnlöð mér of gaf gullnum stóli á drykk ins dýra mjaðar; ill iðgjöld lét ek hana eftir hafa síns ins heila hugar, síns ins svára sefa.*

Gunnlöð gave me, on a golden stool, a drink of the precious mead; bad repayment I let her have for her whole heart, her heavy mind.

![Odin and Gunnlöð, drawn by Lorenz Frølich]({IMG_GUNN})
Odin with Gunnlöð, drawn by Lorenz Frølich. Image: public domain, via [Wikimedia Commons]({PAGE_GUNN}).

He who has taught repaying gift with gift admits here that he himself repaid a gift badly. It is the same I that hung nine nights in the tree, and he counts his own faults as openly as his sacrifices. A wisdom that can say *ill iðgjöld lét ek* is harder to dismiss than one that never errs – and easier to take to heart a thousand years later, because it does not speak from above.

## Taking it to heart – or letting it stand still

After all this one question remains: should we take Hávamál to heart today, or let it be a picture of our ancestors, frozen in time? The poem is honest that much in it belongs to its time. The advice never to go a step from one's weapons in the field (38) belongs in a world without police, and the advice never to trust a woman's word (84) is a distrust we do not want to carry with us – even though the same voice in stanza 91 says openly that it is men's hearts that are unreliable towards women. Whoever takes the whole poem literally gets both wisdom and hindrance.

But what belongs to its time is the answers, not the questions: how do I receive the one who comes in through the door, how do I avoid loneliness, what do I give for what I get, how much should I know, what do I do with a night that will not end, what am I good for when the body fails, and how will I be remembered? And the poem itself asks to be used, not preserved. The refrain of Loddfáfnismál promises benefit to the one who receives: *njóta mundu, ef þú nemr*, 'you will benefit, if you take it in'. The last stanza calls the words *allþörf ýta sonum*, 'of great use to the sons of men', and closes with blessings on the one who spoke, the one who knows, the one who has learned and those who listened: *njóti sá, er nam* (164), 'may he enjoy who has learned'. A picture frozen in time is of use to no one.

Wisdom, then, is bound to its time in its answers but not in its questions, and it survives only as long as someone tests it against their own life. Stanza 119 anyone can test tonight, by getting in touch with a friend one has not heard from in a year. Stanza 4 can be tested the next time someone comes in through the door: a word, and silence in return. That is our reading of what it means to take Hávamál to heart.

:::box The essentials in brief
- The voice in Hávamál is a person's, not a judge's: it lacks God, sin and soul, weighs the worse against the better and remembers instead of judging. That is why the poem can be read as advice by a reader who does not share its belief.
- Its points of contact with us lie in the questions, not the answers: the guest at the door, loneliness, the gift and its return, the sleepless night, the failing body and the word-fame. Every runestone is stanza 77 in stone.
- The ethics of friendship and gifts belongs to wisdom, not to paganism – the Christian Hugsvinnsmál shares it – and the blót is the same reciprocity turned upwards. What is precious is what costs; for us that is time and attention.
- The poem itself asks to be used, not preserved, and it is honest that some of its answers belong to its time. Taking it to heart means testing its questions against one's own life.
:::

:::box How we counted
The text is the Codex Regius text in its normalised edition (Guðni Jónsson), 164 stanzas, {ORD['Hávamál']} words; every quotation stands there verbatim, and the translations are ours. The comparison against Christian and pagan poetry used fixed word lists and Fisher's exact test, which asks how often chance would produce a difference that large; we give it as 'once in …'. The comparison texts are Hugsvinnsmál (Finnur Jónsson's edition), Sólarljóð and the seven pagan dialogue poems (Guðni Jónsson's editions) with {ORD['Hugsvinnsmál']}, {ORD['Sólarljóð']} and {ORD['hedniska_dialoger']} words. Because the editions spell differently we used only words with equal spelling. Hugsvinnsmál is an adaptation of a Latin model, so the results hold for these comparisons only. Two measures were discarded when we tested them against their own artefacts: the word *ef* (which mostly reflects the refrain of Loddfáfnismál) and *skal* (which does not separate the poems). The measurements of the poem's layers, seams and vocabulary against the runestones are open in the repository (utdata/Edda) but are not part of this article, which is a reading.
:::

## Sources and data

- Hávamál: Guðni Jónsson's normalised edition of the Codex Regius text (Eddukvæði, Sæmundar-Edda), via heimskringla.no.
- Hugsvinnsmál: Finnur Jónsson (ed.), Den norsk-islandske skjaldedigtning, 1912–15, via heimskringla.no. Sólarljóð and the pagan dialogue poems: Guðni Jónsson's editions, via heimskringla.no.
- Edition and commentary: David A. H. Evans, Hávamál (Viking Society, 1986). Dating: Mikael Males, Maal og Minne 2024:1, pp. 81–117.
- The ethics of the gift: Marcel Mauss, 'Essai sur le don', L'Année sociologique 1923–24.
- Analysis code and results: utdata/Edda in Vitki's repository.
- Images: Wikimedia Commons, public domain, with credits in the captions."""

# aldrig siffra först i en mening; bild- och diagramrader räknas inte
for b in (body, body_en):
    flat = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", b)
    flat = "\n".join(line for line in flat.splitlines() if "|" not in line and not line.startswith(":::"))
    for m in re.finditer(r"[.!?]\s+(\d)", flat.replace("\n", " ")):
        ctx = flat.replace("\n", " ")[max(0, m.start() - 40):m.end() + 20]
        assert re.search(r"GKS|1270|190[0-9]|while|medan|\bs\. \d|\bpp\. \d", ctx), f"Mening börjar med siffra: …{ctx}…"
# vi-form: the narrator says "vi"; the first person inside the quotations is the High One's
assert "Vi gjorde en sak innan vi läste" in body and "Det är vår läsning av vad det betyder" in body
assert not re.search(r"^\|", body, re.M)

out = {"slug": "vem-talar-i-havamal", "title": title, "summary": summary, "body": body,
       "title_en": "What the High One Says a Thousand Years Later",
       "summary_en": ("Hávamál was composed about a thousand years ago and reached us in a single manuscript. We first "
                      "measured how the voice sounds – without God, with an I that remembers – and then read the poem as it "
                      "asks to be read: as advice to a person. On arriving as a guest, on loneliness and friendship, on gifts "
                      "and sacrifice, on sleepless nights, on old age and on being remembered – and what remains for whoever "
                      "reads it today."),
       "body_en": body_en, "labels": ["Personligt", "Eddan", "Tolkning"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "havamalartikel.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "havamalartikel.json"), len(body.split()), "ord sv,", len(body_en.split()), "ord en")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        json.dump({k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in old.items()},
                  open(os.path.join(ROOT, f"utdata/blogg/{old['slug']}.FORE.json"), "w"), ensure_ascii=False, indent=1, default=str)
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    else:
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Eddan|statistik i R", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
