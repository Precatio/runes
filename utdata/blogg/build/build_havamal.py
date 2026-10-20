"""Artikeln "Vem talar i Hávamál?": vad den Höge säger och hur: jämförelsen mot kristen och hednisk dikt, korsningen mot
runkorpusen (först i sitt slag) och en läsning. Varje siffra hämtas ur
analysfilerna i utdata/Edda (havamal_prep.py + havamal.R + djupmönsterkörningen) och låses med asserts.
Bilderna är public domain, kontrollerade mot Commons API 2026-10-19.
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
R = json.load(open(os.path.join(E, "havamal_resultat.json")))
D = json.load(open(os.path.join(E, "havamal_djupmonster.json")))
STROF = list(csv.DictReader(open(os.path.join(E, "havamal_strofer.csv"))))

svn = lambda x, d=1: f"{x:.{d}f}".replace(".", ",")  # noqa: E731

# ---- låsningarna ---------------------------------------------------------------------------------
MB = D["memorial_bydel"]
assert 0.16 <= min(MB.values()) and max(MB.values()) <= 0.21
d76 = {int(r["nr"]): r for r in STROF}
assert "deyr fé" in d76[76]["text"].lower() and "orðstírr" in d76[76]["text"]
full = " ".join(r["text"].lower() for r in STROF)
assert all(full.count(w) == 0 for w in ("krist", "kirkj", "messa", "synd"))
matt = {x["del"]: x for x in R["versmatt"]}
assert matt["IV"]["segment_median"] == 9
ttr = R["ttr"]
assert ttr["IV"] == 0.463
runb = {x["del"]: x["andel"] for x in R["runbelagg"]}
assert runb["VI"] == 0.605 and runb["V"] == 0.5
assert R["ljodatal_kann_ek"] == 17
L = json.load(open(os.path.join(E, "havamal_runkorpus_per_land.json")))
LR, LK = L["rå"], L["kontroll"]
assert LR["Sverige"]["stenar"] == 2321 and LR["Danmark"]["stenar"] == 239 and LR["Norge"]["stenar"] == 66
assert LK["Norge"]["median_medel"] == 0.19 and LK["Danmark"]["median_medel"] == 0.161 and LK["Sverige"]["median_medel"] == 0.142
assert LK["Sverige"]["andel_minst_norge"] == 0.003  # en dragning av trehundra når Norges nivå
assert L["kontroll_dansk_budget"]["andel_sverige_minst_danmark"] == 0.0
assert all(w in L["ord_diff"]["norsk_ej_svensk"] for w in ("sa", "mer", "konu", "up", "stendr"))
assert all(w in L["ord_diff"]["dansk_ej_svensk"] for w in ("munu", "vel", "lifa", "nu", "lengi"))
pN, pD, pS = (svn(100 * LK[k]["median_medel"], 0) for k in ("Norge", "Danmark", "Sverige"))

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
for nr, ord_ in ((36, "þat er þó betra en bæn"), (38, "Vápnum sínum"), (41, "endrgefendr"), (42, "gjalda gjöf við gjöf"),
                 (46, "glík skulu gjöld gjöfum"), (47, "Ungr var ek forðum"), (48, "Mildir, fræknir menn bazt lifa"),
                 (50, "Hrörnar þöll"), (54, "Meðalsnotr"), (56, "örlög sín viti engi fyrir"), (66, "Mikilsti snemma kom ek í marga staði"),
                 (70, "Betra er lifðum en sé ólifðum"), (77, "dómr um dauðan hvern"), (78, "Fullar grindr sá ek"), (78, "nú bera þeir vánar völ"),
                 (84, "Meyjar orðum"), (91, "brigðr er karla hugr konum"), (105, "ill iðgjöld lét ek hana"),
                 (111, "sá ek ok þagðak"), (119, "far þú at finna oft"), (131, "varan bið ek þik vera ok eigi ofvaran"),
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

title = "Vem talar i Hávamál?"
summary = ("Eddans visdomsdikt är genomtröskad av tvåhundra års forskning – så den här artikeln håller sig "
           "till det ingen visat förut. Dikten mäts mot kristna dikter i samma versmått och mot Nordens runstenar, "
           "och sist kommer en läsning av vad den Höge säger om ensamhet, gåva och blot – och vad vi offrar i dag.")

body = f"""Hávamál, "den höges tal", är nordens mest citerade dikt: etthundrasextiofyra strofer visdom, varningar, kärleksäventyr och trolldom, bevarade i en enda handskrift – Codex Regius, nedskriven på Island omkring 1270. Forskare har i tvåhundra år diskuterat om dikten är ett verk eller flera hopfogade, var skarvarna går och vad den egentligen vill. Det mesta om dikten är redan utrett, och det tänker vi inte upprepa. Den här artikeln håller sig till det forskningen inte redan visste: tre mätningar som är nya – varav en gick emot oss själva – och sist en läsning av vad den Höge säger till en människa.

![Uppslag ur Codex Regius]({IMG_CR})
Codex Regius (GKS 2365 4to), nedskriven omkring 1270 – Hávamáls enda medeltida källa. Allt i den här artikeln är mätt på den textens normaliserade utgåva (Guðni Jónsson). Bild: public domain, via [Wikimedia Commons]({PAGE_CR}).

## Hur den Höge talar – och vad han aldrig lovar

Vilken sorts röst är det som ger råden? Vi ställde Hávamál mot tre grupper av dikter i samma versmått, ljóðaháttr. Den första är de hedniska dialogdikterna (Vafþrúðnismál, Grímnismál, Skírnismál, Lokasenna, Alvíssmál, Sigrdrífumál och Fjölsvinnsmál). De två andra är kristna: *Sólarljóð*, en visionsdikt om en död man som ser straff och nåd, och *Hugsvinnsmál*, en kristen bearbetning av den latinska visdomsboken Disticha Catonis. Hugsvinnsmál är den intressantaste jämförelsen, eftersom den liksom stora delar av Hávamál är ett råd från en far till hans son.

Det första resultatet är det väntade. Hávamál har inte ett enda ord ur det kristna ordförrådet – *guð*, *synd*, *sál*, *drottinn*, *náð* och deras släkt – medan Hugsvinnsmál har dem {svn(rk['Hugsvinnsmál']['per100'], 1)} gånger per hundra ord och Sólarljóð {svn(rk['Sólarljóð']['per100'], 1)}. De hedniska dialogerna har dem inte heller. Det är David Evans gamla belägg (1986) uttryckt i siffror, inte något nytt. (Ordet *bæn* står en gång i Hávamál, men i strof 36 betyder det ’tiggeri’ och inte ’bön’: *þat er þó betra en bæn*, ’det är ändå bättre än att tigga’.)

Det andra är mer överraskande: vänskapens och gåvans etik skiljer inte hednisk från kristen. Ord för gåva och gäld står {f2(G['mot_hugsvinnsmal']['per100_a'])} gånger per hundra ord i Hávamál och {f2(G['mot_hugsvinnsmal']['per100_b'])} i Hugsvinnsmál, och ord för vän {f2(VN['mot_hugsvinnsmal']['per100_a'])} mot {f2(VN['mot_hugsvinnsmal']['per100_b'])} – men bara {f2(G['mot_hedniska']['per100_b'])} respektive {f2(VN['mot_hedniska']['per100_b'])} i de hedniska dialogerna, alltså ungefär fem till tretton gånger mer i de två visdomsdikterna. Att gälda gåva med gåva och vårda sina vänner hör till visdomslitteraturen, inte till tron. Det är känt sedan Marcel Mauss använde Hávamáls gåvostrofer i sin klassiska studie av gåvan; det som tillkommer här är att det går att mäta.

Skillnaden ligger i två andra saker. Den första är att Hávamál jämför. Ordet *betra*, ’bättre’, står {f2(BT['mot_hugsvinnsmal']['per100_a'])} gånger per hundra ord i gästvisdomen mot {f2(BT['mot_hugsvinnsmal']['per100_b'])} i Hugsvinnsmál och {f2(BT['mot_hedniska']['per100_b'])} i dialogerna. En slump skulle ge en så stor skillnad mot Hugsvinnsmál ungefär en gång på {ett_pa(BT['mot_hugsvinnsmal']['p'])}. Talen är små ({BT['mot_hugsvinnsmal']['a']} träffar mot {BT['mot_hugsvinnsmal']['b']}), så det är en antydan och inte ett bevis, men den pekar åt samma håll som texten: *Bú er betra, þótt lítit sé* – ett hem är bättre, om än litet. *Betra er lifðum en sé ólifðum* – bättre att leva än att vara död. Råden är sällan bud utan avvägningar mellan det sämre och det bättre, en fattigmansfilosofi där inget val är gratis.

Den andra är vad jaget gör. I Hugsvinnsmál *bedömer* det: *hygg ek*, ’jag tror’, och *tel ek*, ’jag räknar’, utgör fem av dess åtta *ek*, och de övriga tre rammar in undervisningen. I Hávamáls gästvisdom *minns* jaget: *Ungr var ek forðum, fór ek einn saman* (47), ’ung var jag förr, jag for ensam’; *Mikilsti snemma kom ek í marga staði* (66), ’alltför tidigt kom jag till många platser’; *Fullar grindr sá ek fyr Fitjungs sonum* (78), ’fulla fållor såg jag hos Fitjungs söner – nu bär de tiggarstav’. Rådet vilar på en människas erfarenhet. I trollsångerna blir jaget kunnigt: *þat kann ek*, ’det kan jag’, {EKr['kann_ek']} gånger. Jag-formen i sig är inte unik för Hávamál, för dialogdikterna har lika mycket, men det är den som skiljer dikten från den kristna visdomsdikten.

Två saker vi trodde oss se höll inte. Vi trodde först att Hávamál argumenterar med villkor, eftersom ordet *ef*, ’om’, är dubbelt så vanligt som i Hugsvinnsmál. Men {2 * EFr['refranger'][0]} av de {EFr['hela']['mot_hugsvinnsmal']['a']} *ef* står i Loddfáfnismáls refräng (*njóta mundu, ef þú nemr … ef þú getr*), och utan den är skillnaden borta ({svn(EFr['utan_refrang']['mot_hugsvinnsmal']['per100_a'], 1)} mot {svn(EFr['utan_refrang']['mot_hugsvinnsmal']['per100_b'], 1)} per hundra ord). Och Hávamál är inte mer befallande: *skal*-formerna står {svn(SK['mot_hugsvinnsmal']['per100_a'], 1)} gånger per hundra ord mot {svn(SK['mot_hugsvinnsmal']['per100_b'], 1)} i Hugsvinnsmál, en skillnad som lätt kan vara slump. Den Höge befaller lika mycket som den kristne läraren. Han motiverar annorlunda, och han har ingen domare.

Den sista skillnaden fångar ingen räkning. I Hugsvinnsmál går gälden via Gud: *gjǫld af guði hygg ek gumnar taki*, ’gäld från Gud, tror jag, får människorna’ (135), och självprövningen gäller synd: *ef veizt þik syndgan sjálfr* (45), ’om du vet att du själv syndat’. I Hávamál står gälden mellan människor: *glík skulu gjöld gjöfum* (46), ’lika ska gälden vara gåvorna’.

## Hypotesen som föll: Hávamál låter inte som runstenarna

Här kommer artikelns ärligaste fynd. Hávamáls mest berömda strofer säger samma sak som varje runsten: *Deyr fé, deyja frændr … en orðstírr deyr aldregi* – boskap dör, fränder dör, men eftermälet dör aldrig. Runstenarna är ju exakt det: eftermälen i sten. Så vi antog att förgänglighetsstroferna också skulle *låta* som runstenarna, och mätte varje strofs ordförråd mot de tvåhundra vanligaste orden på Nordens vikingatida runstenar – samma korpus som driver resten av Vitki.

Hypotesen föll. Likheten med runstenarnas formelspråk är jämnt låg genom hela dikten – medianen ligger mellan {svn(100 * min(MB.values()), 0)} och {svn(100 * max(MB.values()), 0)} procent av strofens ordtyper i alla sex delarna – och *deyr fé*-stroferna ligger mitt i fältet, inte i toppen. Dikten och stenarna delar eftermälets teologi, men inte dess ord: runstenens *ræisti stæin æftiR* och Hávamáls *orðstírr* är två skilda språkvärldar kring samma tanke. Det talar för två oberoende traditioner – minnesformeln på stenarna är inte diktcitat, och dikten härmar inte stenarna. Såvitt vi vet är det första gången dikten mäts mot en hel runkorpus, och det tydligaste resultatet blev ett nej – vilket är precis så mätningar ska få lov att sluta.

Så delade vi korpusen per land – dikten är ju västnordisk, stenarna till största delen östnordiska. Då träder ett andra mönster fram. Jämfört på lika stora textmängder ligger de norska stenarnas vanligaste ord närmast dikten ({pN} procent av strofens ordtyper), de danska därnäst ({pD} procent) och de svenska längst bort ({pS} procent); av trehundra slumpdragningar ur den svenska korpusen når en enda upp till den norska nivån. Ordningen följer alltså geografin, väst mot öst.

Och orden som gör skillnaden är inte minnesformelns utan vardagens: på de norska stenarna *sá*, *mér*, *konu*, *upp*, *stendr*, på de danska *munu*, *vel*, *lifa*, *nú*, *lengi* – ord som också bär dikten – medan de svenska stenarnas topplista trängs med namn och res-formeln. Norges runstenskorpus är liten, bara 66 stenar, så detta är en antydan och inget bevis, och mer mångordiga inskrifter väster ut kan förklara en del av skillnaden. Men pilen pekar åt samma håll som diktens egen hemtrakt: där stenarna får tala vardagsspråk kommer de Hávamál närmare, och ju längre väster ut de står, desto närmare kommer de.

## Där dikten och stenarna ändå möts

Ett möte finns till slut ändå, och det står i dikten själv: strof 72 säger att *bautastenar sällan står vid vägen om inte frände reser dem efter frände*. Seden strofen beskriver är exakt den vår runkorpus består av – tusentals stenar, resta vid vägar och broar, av fränder efter fränder. Det belägget är David Evans (1986), inte vårt. Men vår mätning lägger en egen liten vikt i samma vågskål: stenarnas språk ligger närmast diktens just i väster, där strofens bautastenar hör hemma.

## Vad den Höge säger till en människa

Det som följer är en läsning och inte ett mätresultat. Siffrorna ovan visar hur dikten talar; här frågar vi vad den säger. Vi håller oss till stroferna själva, översatta så ordagrant vi kan, och till det mätningarna pekade mot: ett jag som minns och en moral som ligger mellan människor.

### Människan är människans glädje

> *Ungr var ek forðum, fór ek einn saman, þá varð ek villr vega; auðigr þóttumk, er ek annan fann, maðr er manns gaman.*

Ung var jag förr, jag for ensam; då gick jag vilse på vägen. Rik tyckte jag mig, när jag fann en annan: människan är människans glädje.

Strof 47 hör till diktens mest mänskliga. En av de största farorna i Hávamál är inte döden utan ensamheten, och det säger strof 50 med en bild ur skogen:

> *Hrörnar þöll, sú er stendr þorpi á, hlýr-at henni börkr né barr; svá er maðr, sá er manngi ann. Hvat skal hann lengi lifa?*

Förtorkas gör tallen som står vid byn; varken bark eller barr skyddar henne. Så är den människa som ingen älskar. Varför ska en sådan leva länge?

Rådet som följer är nästan tekniskt. Strof 119: *far þú at finna oft, því at hrísi vex ok hávu grasi vegr, er vættki treðr* – gå ofta och hälsa på din vän, för på en väg som ingen trampar växer buskar och högt gräs. Vänskap är ingen känsla utan ett underhåll.

### Gåva mot gåva – och blotet

> *Vin sínum skal maðr vinr vera ok gjalda gjöf við gjöf.*

Mot sin vän ska man vara en vän och gälda gåva med gåva (42). De som ger och de som ger igen, säger strof 41, förblir längst vänner. Det är diktens ekonomi: ingen är skyldig någon något för alltid, och därför kan vänskapen leva.

Samma tanke återkommer i ett av diktens mest främmande ord, blot. I strof 144 ställer den Höge åtta frågor – *veistu, hvé rísta skal*, ’vet du hur man ska rista’ – och en av dem är *veistu, hvé blóta skal*, ’vet du hur man ska blota’. Ett svar står i strof 145, och det är samma ömsesidighet:

> *Betra er óbeðit en sé ofblótit, ey sér til gildis gjöf.*

Bättre ej bedd än för mycket offrat; en gåva ser alltid efter sin gengåva (*gildi*). Blotet är alltså inte något främmande och högtidligt utan vänskapens bokföring riktad uppåt: man ger för att få, och man ska ge lagom. Dikten varnar för överdriften, men lika tydligt för snålheten: *mildir, fræknir menn bazt lifa*, ’frikostiga, tappra män lever bäst’ (48).

Den dyraste gåvan i dikten är den Höges egen. I strof 138 hänger han nio nätter i trädet, *gefinn Óðni, sjalfr sjalfum mér*, ’given åt Oden, själv åt mig själv’, och i strof 139 får han varken bröd eller dryckeshorn. Det han köper är runorna, och han tar dem *æpandi*, ’skrikande’. Det som gör offret stort är inte att det är högt utan att det kostar.

![Odens självoffer i trädet, tecknat av W.G. Collingwood]({IMG_ODIN})
Odens självoffer (strof 138): nio nätter i trädet, ”gåva åt Oden, han själv åt sig själv”. Teckning: W.G. Collingwood (1908), public domain, via [Wikimedia Commons]({PAGE_ODIN}).

Vad blotar vi i dag? Det är en fråga som dikten inte ställer, men som dess ord gör rimlig, och här tillåter vi oss en tolkning som inte är diktens egen. Vi offrar något varje dag. Det som kostar har bara blivit något annat än boskap och mjöd: för oss har det dyrbara blivit vår tid och vår uppmärksamhet, och vi ger bort dem hela dagarna, ofta utan att fråga vad vi får tillbaka. Då är den Höges fråga inte ett arkaiskt krav utan en vass fråga om det egna livet: vet du hur du ska ge bort dina dagar, och vad väntar gåvan sig av dig? *Ey sér til gildis gjöf.* Och varningen gäller också här: *betra er óbeðit en sé ofblótit*. Man kan offra för mycket av sin uppmärksamhet åt sådant som aldrig ger något tillbaka.

### Måttlig vishet

> *Meðalsnotr skyli manna hverr, æva til snotr sé … örlög sín viti engi fyrir, þeim er sorgalausastr sefi.*

Måttligt vis ska var människa vara, aldrig alltför vis … ingen ska i förväg veta sitt öde; då är sinnet friast från sorg (54, 56). Strof 55 går längre och säger att den alltför visas hjärta sällan blir glatt. Samma balans finns i strof 131: *varan bið ek þik vera ok eigi ofvaran*, ’vaksam ber du vara, men inte alltför vaksam’. Dikten som prisar kunskapen varnar alltså för för mycket av den, och det är ett märkligt råd i en tid då vi kan veta nästan allt om nästan alla, hela tiden.

Uppmärksamheten är diktens första lärdom: *sá ek ok þagðak, sá ek ok hugðak, hlýdda ek á manna mál* (111), ’jag såg och teg, jag såg och tänkte, jag lyssnade till människornas tal’. Ordningen är att se, tiga, tänka och lyssna innan man talar. Samma strof är utgångspunkten för essän [Korpen som heter Minne](/artiklar/korpen-som-heter-minne).

### Domen över de döda – och den Höges erkännande

Strof 77 säger vad som består: *ek veit einn, at aldrei deyr: dómr um dauðan hvern* – jag vet ett som aldrig dör: domen över varje död. Domen som avses är eftermälets: det de levande säger om den döde, och därför är det enda som består ett gott namn (76). Det är samma tanke som reste varje runsten.

Men det är en röst som inte gör sig själv felfri. I strof 105 säger den Höge om Gunnlöd, som gav honom mjödet:

> *Gunnlöð mér of gaf gullnum stóli á drykk ins dýra mjaðar; ill iðgjöld lét ek hana eftir hafa síns ins heila hugar, síns ins svára sefa.*

Gunnlöd gav mig, på gyllene stol, en dryck av den dyra mjöden; ond lön lät jag henne få för sitt hela hjärta, sitt tunga sinne.

![Oden och Gunnlöd, tecknade av Lorenz Frølich]({IMG_GUNN})
Oden hos Gunnlöd, tecknad av Lorenz Frølich. Bild: public domain, via [Wikimedia Commons]({PAGE_GUNN}).

Den som har lärt ut att gälda gåva med gåva erkänner här att han själv gäldade en gåva illa. Det är samma jag som hänger i trädet i Runatal: Odens bekännelser. En visdom som kan säga *ill iðgjöld lét ek* är svårare att avfärda än en som aldrig misstar sig.

### Att ta den till sig – eller låta den stå stilla

Ska vi ta Hávamál till oss i dag, eller låta den vara en bild av våra förfäder, fryst i tiden? Dikten är ärlig om att mycket i den hör till sin tid. Rådet att inte gå ett steg från sina vapen på fältet (38) hör hemma i en värld utan polis, och rådet att aldrig lita på en kvinnas ord (84) är en misstro vi inte vill ta med oss – även om samma röst i strof 91 öppet säger att det är männens hjärta som är opålitligt mot kvinnorna. Den som tar hela dikten bokstavligt får både vishet och förhinder.

Men det som hör till sin tid är svaren, inte frågorna: hur undviker jag ensamheten, hur håller jag vänner, vad ger jag för det jag får, hur mycket ska jag veta, och hur blir jag ihågkommen? Och dikten ber själv om att användas, inte bevaras. Loddfáfnismáls refräng lovar nytta åt den som tar emot: *njóta mundu, ef þú nemr*, ’du får nytta, om du tar det till dig’. Den sista strofen kallar orden *allþörf ýta sonum*, ’till stor nytta för människors söner’, och avslutas med välsignelser åt den som kvad, den som kan, den som lärt och dem som lyssnat: *njóti sá, er nam* (164), ’må den njuta som har lärt’. En bild fryst i tiden ger ingen någon nytta.

Visdom är alltså tidsbunden i sina svar men inte i sina frågor, och den överlever bara så länge någon prövar den mot sitt eget liv. Strof 119 kan vem som helst pröva i kväll, genom att höra av sig till en vän man inte hört av på ett år. Det är vår läsning av vad det betyder att ta Hávamál till sig.

:::box Så räknade vi
Texten är Codex Regius-textens normaliserade utgåva (Guðni Jónsson), 164 strofer, cirka 5 000 ord. Runstensjämförelsen räknar andelen av strofens ordtyper som finns bland de tvåhundra vanligaste orden i Rundatas vikingatida runstensnormaliseringar, med ordformerna hopslagna över normaliseringstraditionerna. Landjämförelsen delar korpusen i svenska, danska (DR) och norska (N) stenar; eftersom en topplista ur en liten korpus når djupare ner i vardagsorden jämförs länderna efter slumpprov med lika många löpord, trehundra dragningar per land. Jämförelsen mot kristen och hednisk dikt gjordes med fasta ordlistor och Fishers exakta test, som frågar hur ofta en slump skulle ge en lika stor skillnad; vi anger det som ”en gång på …”. Jämförelsetexterna är Hugsvinnsmál (Finnur Jónssons utgåva), Sólarljóð och de sju hedniska dialogdikterna (Guðni Jónssons utgåvor) med {ORD['Hugsvinnsmál']}, {ORD['Sólarljóð']} och {ORD['hedniska_dialoger']} ord, mot Hávamáls {ORD['Hávamál']}. Eftersom utgåvorna stavar olika använde vi bara ord vars stavning är lika; ett första försök med nyckelord lades ned, eftersom det mest fångade stavningsskillnader. Hugsvinnsmál är dessutom en bearbetning av en latinsk förebild, så resultaten gäller just de här jämförelserna. Två mått kasserades när vi prövade dem mot sina egna artefakter: ordet *ef* (som mest speglar en refräng) och *skal* (som inte skiljer). All kod och alla resultatfiler ligger öppet i kodförrådet (utdata/Edda).
:::

:::box Det viktigaste i korthet
- Dikten och runstenarna delar tanken att bara eftermälet består, men inte orden: den första mätningen någonsin mot en hel runkorpus slutade i ett nej, och det pekar på två oberoende traditioner. Delas korpusen per land ligger stenarnas vardagsspråk närmast dikten i väster – ett svagt men riktningsrätt eko av diktens västnordiska hemtrakt.
- Mätt mot kristna dikter i samma versmått saknar Hávamál Gud, synd och själ helt, men delar vänskapens och gåvans etik med den kristna Hugsvinnsmál: den etiken är visdomens, inte hedendomens. Skillnaden är att råden vilar på avvägningar (”bättre … än”) och på ett jag som minns, och att gälden står mellan människor och inte inför en domare.
- Blotet är i dikten samma ömsesidighet som vänskapen, riktad uppåt: man ger för att få, och man ska ge lagom. Det dyra är det som kostar – för oss har det blivit tid och uppmärksamhet.
- Dikten är bunden till sin tid i sina svar men inte i sina frågor, och den ber själv om att användas, inte bevaras.
- Inget av detta daterar eller placerar dikten: en enda handskrift från 1270-talet sätter gränsen för vad någon metod kan veta, och en jämförelse mellan två dikter kan spegla genre lika väl som tradition.
:::

## Källor och data

- Hávamál: Guðni Jónssons normaliserade utgåva av Codex Regius-texten (Eddukvæði, Sæmundar-Edda), via heimskringla.no.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet, för runstensjämförelsen.
- Analyskod och resultat: utdata/Edda i Vitkis kodförråd.
- Hugsvinnsmál: Finnur Jónsson (utg.), Den norsk-islandske skjaldedigtning, 1912–15, via heimskringla.no. Sólarljóð och de hedniska dialogdikterna: Guðni Jónssons utgåvor, via heimskringla.no.
- Gåvans etik: Marcel Mauss, ”Essai sur le don”, L’Année sociologique 1923–24. Utgåva och kommentar: David A. H. Evans, Hávamál (Viking Society, 1986).
- Bilder: Wikimedia Commons, public domain, med upphov i bildtexterna.

*Mätningen själv daterar och placerar ingenting – en enda handskrift från 1270-talet sätter den gränsen. Men den kan jämföra ordvärldar och lämna siffrorna öppna för runologer och filologer att pröva.*"""

body_en = f"""Hávamál, "the words of the High One", is the North's most quoted poem: one hundred and sixty-four stanzas of wisdom, warnings, love adventures and magic, preserved in a single manuscript – the Codex Regius, written down in Iceland around 1270. For two hundred years scholars have debated whether the poem is one work or several joined together, where the seams run and what it really wants. Most of that debate is already settled ground, and we are not going to repeat it. This article keeps to what scholarship did not already know: three measurements that are new – one of which went against ourselves – and, last, a reading of what the High One says to a person.

![Opening of the Codex Regius]({IMG_CR})
The Codex Regius (GKS 2365 4to), written down around 1270 – Hávamál's only medieval source. Everything in this article is measured on that text's normalised edition (Guðni Jónsson). Image: public domain, via [Wikimedia Commons]({PAGE_CR}).

## How the High One speaks – and what he never promises

What kind of voice gives the advice? We set Hávamál against three groups of poems in the same metre, ljóðaháttr. The first is the pagan dialogue poems (Vafþrúðnismál, Grímnismál, Skírnismál, Lokasenna, Alvíssmál, Sigrdrífumál and Fjölsvinnsmál). The other two are Christian: *Sólarljóð*, a vision poem about a dead man who sees punishment and grace, and *Hugsvinnsmál*, a Christian adaptation of the Latin wisdom book Disticha Catonis. Hugsvinnsmál is the most interesting comparison, because like large parts of Hávamál it is advice from a father to his son.

The first result is the expected one. Hávamál has not a single word from the Christian vocabulary – *guð*, *synd*, *sál*, *drottinn*, *náð* and their kin – while Hugsvinnsmál has them {e2(rk['Hugsvinnsmál']['per100'], 1)} times per hundred words and Sólarljóð {e2(rk['Sólarljóð']['per100'], 1)}. The pagan dialogues have none either. That is David Evans's old evidence (1986) in numbers, not something new. (The word *bæn* occurs once in Hávamál, but in stanza 36 it means 'begging', not 'prayer': *þat er þó betra en bæn*, 'that is still better than begging'.)

The second is more surprising: the ethics of friendship and gifts does not separate pagan from Christian. Words for gift and repayment stand {e2(G['mot_hugsvinnsmal']['per100_a'])} times per hundred words in Hávamál and {e2(G['mot_hugsvinnsmal']['per100_b'])} in Hugsvinnsmál, and words for friend {e2(VN['mot_hugsvinnsmal']['per100_a'])} against {e2(VN['mot_hugsvinnsmal']['per100_b'])} – but only {e2(G['mot_hedniska']['per100_b'])} and {e2(VN['mot_hedniska']['per100_b'])} in the pagan dialogues, roughly five to thirteen times more in the two wisdom poems. Repaying gift with gift and tending one's friends belong to wisdom literature, not to belief. That has been known since Marcel Mauss used Hávamál's gift stanzas in his classic study of the gift; what is added here is that it can be measured.

The difference lies in two other things. The first is that Hávamál compares. The word *betra*, 'better', stands {e2(BT['mot_hugsvinnsmal']['per100_a'])} times per hundred words in the guest wisdom against {e2(BT['mot_hugsvinnsmal']['per100_b'])} in Hugsvinnsmál and {e2(BT['mot_hedniska']['per100_b'])} in the dialogues. Chance would produce a difference that large against Hugsvinnsmál about once in {ett_pa(BT['mot_hugsvinnsmal']['p'])}. The numbers are small ({BT['mot_hugsvinnsmal']['a']} hits against {BT['mot_hugsvinnsmal']['b']}), so it is a hint and not proof, but it points the same way as the text: *Bú er betra, þótt lítit sé* – a home is better, though small. *Betra er lifðum en sé ólifðum* – better to live than to be dead. The advice is seldom commands and mostly trade-offs between the worse and the better, a poor man's philosophy where no choice is free.

The second is what the I does. In Hugsvinnsmál it *judges*: *hygg ek*, 'I think', and *tel ek*, 'I count', make up five of its eight *ek*, and the other three frame the teaching. In Hávamál's guest wisdom the I *remembers*: *Ungr var ek forðum, fór ek einn saman* (47), 'young I was once, I travelled alone'; *Mikilsti snemma kom ek í marga staði* (66), 'far too early I came to many places'; *Fullar grindr sá ek fyr Fitjungs sonum* (78), 'full folds I saw among Fitjung's sons – now they carry the beggar's staff'. The advice rests on a person's experience. In the charms the I becomes knowing: *þat kann ek*, 'that I know', {EKr['kann_ek']} times. The first person in itself is not unique to Hávamál, since the dialogue poems have as much, but it is what separates the poem from the Christian wisdom poem.

Two things we thought we saw did not hold. We first thought Hávamál argues with conditions, because the word *ef*, 'if', is twice as common as in Hugsvinnsmál. But {2 * EFr['refranger'][0]} of the {EFr['hela']['mot_hugsvinnsmal']['a']} *ef* stand in the refrain of Loddfáfnismál (*njóta mundu, ef þú nemr … ef þú getr*), and without it the difference is gone ({e2(EFr['utan_refrang']['mot_hugsvinnsmal']['per100_a'], 1)} against {e2(EFr['utan_refrang']['mot_hugsvinnsmal']['per100_b'], 1)} per hundred words). Nor is Hávamál more commanding: the *skal* forms stand {e2(SK['mot_hugsvinnsmal']['per100_a'], 1)} times per hundred words against {e2(SK['mot_hugsvinnsmal']['per100_b'], 1)} in Hugsvinnsmál, a difference that could easily be chance. The High One commands as much as the Christian teacher. He gives reasons differently, and he has no judge.

The last difference no count captures. In Hugsvinnsmál repayment runs through God: *gjǫld af guði hygg ek gumnar taki*, 'requital from God, I think, men receive' (135), and self-examination concerns sin: *ef veizt þik syndgan sjálfr* (45), 'if you know yourself sinful'. In Hávamál repayment stands between people: *glík skulu gjöld gjöfum* (46), 'let the repayment match the gifts'.

## The hypothesis that fell: Hávamál does not sound like the runestones

Here is the article's most honest find. Hávamál's most famous stanzas say the same thing as every runestone: *Deyr fé, deyja frændr … en orðstírr deyr aldregi* – cattle die, kinsmen die, but the word-fame never dies. The runestones are precisely that: memorials in stone. So we assumed the impermanence stanzas would also *sound* like the runestones, and measured each stanza's vocabulary against the two hundred most common words on the North's Viking-age runestones – the same corpus that drives the rest of Vitki.

The hypothesis fell. The similarity to the runestones' formula language is uniformly low throughout the poem – the median lies between {svn(100 * min(MB.values()), 0)} and {svn(100 * max(MB.values()), 0)} per cent of a stanza's word types in all six parts – and the *deyr fé* stanzas sit in the middle of the field, not at the top. The poem and the stones share the theology of being remembered, but not its words: the runestone's *ræisti stæin æftiR* and Hávamál's *orðstírr* are two separate language worlds around the same thought. That speaks for two independent traditions – the memorial formula on the stones is not poem quotation, and the poem does not imitate the stones. As far as we know this is the first time the poem has been measured against a whole runic corpus, and the clearest result was a no – which is exactly how measurements should be allowed to end.

Then we split the corpus by country – the poem is after all West Norse, the stones mostly East Norse. A second pattern emerges. Compared on equal amounts of text, the most common words of the Norwegian stones lie closest to the poem ({pN} per cent of a stanza's word types), the Danish next ({pD} per cent) and the Swedish furthest away ({pS} per cent); of three hundred random draws from the Swedish corpus, a single one reaches the Norwegian level. The order follows the geography, west against east.

And the words that make the difference are not the memorial formula's but the everyday's: on the Norwegian stones *sá*, *mér*, *konu*, *upp*, *stendr*, on the Danish *munu*, *vel*, *lifa*, *nú*, *lengi* – words that also carry the poem – while the Swedish stones' top list is crowded with names and the raising formula. Norway's runestone corpus is small, only 66 stones, so this is a hint and no proof, and wordier inscriptions in the west may explain part of the difference. But the arrow points in the same direction as the poem's own homeland: where the stones get to speak everyday language they come closer to Hávamál, and the further west they stand, the closer they come.

## Where the poem and the stones meet after all

One meeting remains in the end, and it stands in the poem itself: stanza 72 says that *memorial stones seldom stand by the road unless kinsman raises them for kinsman*. The custom the stanza describes is exactly what our runic corpus consists of – thousands of stones, raised by roads and bridges, by kinsmen for kinsmen. That piece of evidence is David Evans's (1986), not ours. But our measurement adds a small weight of its own to the same scale: the language of the stones lies closest to the poem's precisely in the west, where the stanza's memorial stones belong.

## What the High One says to a person

What follows is a reading and not a measured result. The figures above show how the poem speaks; here we ask what it says. We keep to the stanzas themselves, translated as literally as we can, and to what the measurements pointed towards: an I that remembers and a morality that lies between people.

### Man is man's joy

> *Ungr var ek forðum, fór ek einn saman, þá varð ek villr vega; auðigr þóttumk, er ek annan fann, maðr er manns gaman.*

Young I was once, I travelled alone; then I lost my way. Rich I felt when I found another: man is man's joy.

Stanza 47 is among the poem's most human. One of the greatest dangers in Hávamál is not death but loneliness, and stanza 50 says so with an image from the forest:

> *Hrörnar þöll, sú er stendr þorpi á, hlýr-at henni börkr né barr; svá er maðr, sá er manngi ann. Hvat skal hann lengi lifa?*

The pine that stands by the village withers; neither bark nor needles shelter it. So is the person whom no one loves. Why should such a one live long?

The advice that follows is almost technical. Stanza 119: *far þú at finna oft, því at hrísi vex ok hávu grasi vegr, er vættki treðr* – go often to see your friend, for on a road no one treads, brush and tall grass grow. Friendship is no feeling but maintenance.

### Gift for gift – and the blót

> *Vin sínum skal maðr vinr vera ok gjalda gjöf við gjöf.*

To his friend a man should be a friend and repay gift with gift (42). Those who give and give back, says stanza 41, remain friends longest. That is the poem's economy: no one owes anyone anything forever, and so friendship can live.

The same thought returns in one of the poem's strangest words, blót. In stanza 144 the High One asks eight questions – *veistu, hvé rísta skal*, 'do you know how to carve' – and one of them is *veistu, hvé blóta skal*, 'do you know how to sacrifice'. One answer stands in stanza 145, and it is the same reciprocity:

> *Betra er óbeðit en sé ofblótit, ey sér til gildis gjöf.*

Better not asked than over-sacrificed; a gift always looks for its return (*gildi*). The blót is thus nothing foreign and solemn but friendship's bookkeeping turned upwards: one gives in order to get, and one should give in measure. The poem warns against excess, but just as plainly against stinginess: *mildir, fræknir menn bazt lifa*, 'generous, brave men live best' (48).

The costliest gift in the poem is the High One's own. In stanza 138 he hangs nine nights in the tree, *gefinn Óðni, sjalfr sjalfum mér*, 'given to Odin, myself to myself', and in stanza 139 he gets neither bread nor drinking horn. What he buys is the runes, and he takes them *æpandi*, 'screaming'. What makes the sacrifice great is not that it is lofty but that it costs.

![Odin's self-sacrifice in the tree, drawn by W.G. Collingwood]({IMG_ODIN})
Odin's self-sacrifice (stanza 138): nine nights in the tree, “a gift to Odin, himself to himself”. Drawing: W.G. Collingwood (1908), public domain, via [Wikimedia Commons]({PAGE_ODIN}).

What do we sacrifice today? That is a question the poem does not ask, but its words make it reasonable, and here we allow ourselves an interpretation that is not the poem's own. We sacrifice something every day. What costs has simply become something other than cattle and mead: for us the precious has become our time and our attention, and we give them away all day long, often without asking what we get back. Then the High One's question is not an archaic demand but a sharp question about one's own life: do you know how to give away your days, and what does the gift expect of you? *Ey sér til gildis gjöf.* And the warning applies here too: *betra er óbeðit en sé ofblótit*. One can sacrifice too much of one's attention to things that never give anything back.

### Moderate wisdom

> *Meðalsnotr skyli manna hverr, æva til snotr sé … örlög sín viti engi fyrir, þeim er sorgalausastr sefi.*

Moderately wise should everyone be, never too wise … let no one know their fate in advance; then the mind is freest from sorrow (54, 56). Stanza 55 goes further and says that the heart of the all-too-wise is seldom glad. The same balance is in stanza 131: *varan bið ek þik vera ok eigi ofvaran*, 'wary I bid you be, but not over-wary'. The poem that praises knowledge thus warns against too much of it, and that is a strange piece of advice in an age when we can know nearly everything about nearly everyone, all the time.

Attention is the poem's first lesson: *sá ek ok þagðak, sá ek ok hugðak, hlýdda ek á manna mál* (111), 'I saw and kept silent, I saw and thought, I listened to the speech of men'. The order is to see, be silent, think and listen before speaking. The same stanza is the starting point of the essay [Korpen som heter Minne](/artiklar/korpen-som-heter-minne) (in Swedish).

### The verdict on the dead – and the High One's confession

Stanza 77 says what endures: *ek veit einn, at aldrei deyr: dómr um dauðan hvern* – I know one thing that never dies: the verdict on each dead person. The verdict meant is the posthumous one: what the living say about the dead, and so the only thing that endures is a good name (76). It is the same thought that raised every runestone.

But this is a voice that does not make itself faultless. In stanza 105 the High One says of Gunnlöð, who gave him the mead:

> *Gunnlöð mér of gaf gullnum stóli á drykk ins dýra mjaðar; ill iðgjöld lét ek hana eftir hafa síns ins heila hugar, síns ins svára sefa.*

Gunnlöð gave me, on a golden stool, a drink of the precious mead; bad repayment I let her have for her whole heart, her heavy mind.

![Odin and Gunnlöð, drawn by Lorenz Frølich]({IMG_GUNN})
Odin with Gunnlöð, drawn by Lorenz Frølich. Image: public domain, via [Wikimedia Commons]({PAGE_GUNN}).

He who has taught repaying gift with gift admits here that he himself repaid a gift badly. It is the same I that hangs in the tree in Rúnatal: Odin's confessions. A wisdom that can say *ill iðgjöld lét ek* is harder to dismiss than one that never errs.

### Taking it to heart – or letting it stand still

Should we take Hávamál to heart today, or let it be a picture of our ancestors, frozen in time? The poem is honest that much in it belongs to its time. The advice never to go a step from one's weapons in the field (38) belongs in a world without police, and the advice never to trust a woman's word (84) is a distrust we do not want to carry with us – even though the same voice in stanza 91 says openly that it is men's hearts that are unreliable towards women. Whoever takes the whole poem literally gets both wisdom and hindrance.

But what belongs to its time is the answers, not the questions: how do I avoid loneliness, how do I keep friends, what do I give for what I get, how much should I know, and how will I be remembered? And the poem itself asks to be used, not preserved. The refrain of Loddfáfnismál promises benefit to the one who receives: *njóta mundu, ef þú nemr*, 'you will benefit, if you take it in'. The last stanza calls the words *allþörf ýta sonum*, 'of great use to the sons of men', and closes with blessings on the one who spoke, the one who knows, the one who has learned and those who listened: *njóti sá, er nam* (164), 'may he enjoy who has learned'. A picture frozen in time is of use to no one.

Wisdom, then, is bound to its time in its answers but not in its questions, and it survives only as long as someone tests it against their own life. Stanza 119 anyone can test tonight, by getting in touch with a friend one has not heard from in a year. That is our reading of what it means to take Hávamál to heart.

:::box How we counted
The text is the Codex Regius text in its normalised edition (Guðni Jónsson), 164 stanzas, about 5,000 words. The runestone comparison counts the share of a stanza's word types found among the two hundred most common words in Rundata's Viking-age runestone normalisations, with word forms merged across the normalisation traditions. The country comparison splits the corpus into Swedish, Danish (DR) and Norwegian (N) stones; since a top list from a small corpus reaches deeper into everyday words, the countries are compared on random samples with equal numbers of running words, three hundred draws per country. The comparison against Christian and pagan poetry used fixed word lists and Fisher's exact test, which asks how often chance would produce a difference that large; we give it as 'once in …'. The comparison texts are Hugsvinnsmál (Finnur Jónsson's edition), Sólarljóð and the seven pagan dialogue poems (Guðni Jónsson's editions) with {ORD['Hugsvinnsmál']}, {ORD['Sólarljóð']} and {ORD['hedniska_dialoger']} words, against Hávamál's {ORD['Hávamál']}. Because the editions spell differently we used only words with equal spelling; a first attempt with keywords was dropped because it mostly caught spelling differences. Hugsvinnsmál is, moreover, an adaptation of a Latin model, so the results hold for these comparisons only. Two measures were discarded when we tested them against their own artefacts: the word *ef* (which mostly reflects a refrain) and *skal* (which does not separate). All code and result files are open in the repository (utdata/Edda).
:::

:::box The essentials in brief
- The poem and the runestones share the thought that only the word-fame endures, but not the words: the first measurement ever against a whole runic corpus ended in a no, which points to two independent traditions. Split by country, the stones' everyday language lies closest to the poem in the west – a faint but well-aimed echo of the poem's West Norse homeland.
- Measured against Christian poems in the same metre, Hávamál lacks God, sin and soul entirely, but shares the ethics of friendship and gifts with the Christian Hugsvinnsmál: that ethics belongs to wisdom, not to paganism. The difference is that the advice rests on trade-offs ('better … than') and on an I that remembers, and that repayment stands between people and not before a judge.
- The blót is in the poem the same reciprocity as friendship, turned upwards: one gives in order to get, and should give in measure. What is precious is what costs – for us it has become time and attention.
- The poem is bound to its time in its answers but not in its questions, and it asks itself to be used, not preserved.
- None of this dates or places the poem: a single manuscript from the 1270s sets the limit of what any method can know, and a comparison between two poems can reflect genre as well as tradition.
:::

## Sources and data

- Hávamál: Guðni Jónsson's normalised edition of the Codex Regius text (Eddukvæði, Sæmundar-Edda), via heimskringla.no.
- The Scandinavian Runic Text Database (Rundata), Uppsala University, for the runestone comparison.
- Analysis code and results: utdata/Edda in Vitki's repository.
- Hugsvinnsmál: Finnur Jónsson (ed.), Den norsk-islandske skjaldedigtning, 1912–15, via heimskringla.no. Sólarljóð and the pagan dialogue poems: Guðni Jónsson's editions, via heimskringla.no.
- The ethics of the gift: Marcel Mauss, 'Essai sur le don', L'Année sociologique 1923–24. Edition and commentary: David A. H. Evans, Hávamál (Viking Society, 1986).
- Images: Wikimedia Commons, public domain, with credits in the captions.

*The measurement itself dates and places nothing – a single manuscript from the 1270s sets that limit. But it can compare word worlds and leave the figures open for runologists and philologists to test.*"""

# aldrig siffra först i en mening; bild- och diagramrader räknas inte
for b in (body, body_en):
    flat = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", b)
    flat = "\n".join(line for line in flat.splitlines() if "|" not in line and not line.startswith(":::"))
    for m in re.finditer(r"[.!?]\s+(\d)", flat.replace("\n", " ")):
        ctx = flat.replace("\n", " ")[max(0, m.start() - 40):m.end() + 20]
        assert re.search(r"GKS|1270|190[0-9]|while|medan", ctx), f"Mening börjar med siffra: …{ctx}…"

out = {"slug": "vem-talar-i-havamal", "title": title, "summary": summary, "body": body,
       "title_en": "Who Is Speaking in Hávamál?",
       "summary_en": ("The Edda's wisdom poem has been worked over by two hundred years of scholarship – so this "
                      "article keeps to what no one has shown before. The poem is measured against Christian "
                      "poems in the same metre and against the North's runestones, and last comes a reading of what the "
                      "High One says about loneliness, gift and blót – and what we sacrifice today."),
       "body_en": body_en}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "havamalartikel.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "havamalartikel.json"), len(body), len(body_en))

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
