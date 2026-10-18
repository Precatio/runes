"""Artikeln om Ordförrådet (r/words.R, METHODS.md 1m): vilka ord på runstenarna som bär regional och tidslig
signal. Varje siffra i texten hämtas ur den senaste färdiga korpuskörningens words.json och låses med asserts, så
att artikeln inte kan glida ifrån analysen. Formen: beställarhistorien först (lät resa mot reste själv), sedan en
läsning ord för ord. Bilderna är hämtade från Wikimedia Commons med licens och fotograf kontrollerade mot
API:t 2026-10-18 (U 164 Einarspetz CC BY-SA 3.0; Vg 181 Bengt A. Lundberg/RAÄ CC BY 2.5; Sö 14 Berig CC BY-SA 3.0).
    ../../../.venv/bin/python build_ordartikel.py [--write | --update DOC]
Skriver utdata/blogg/ordartikel.json; --write sparar ett nytt opublicerat utkast i Firestore."""
import datetime as dt
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

# ---- den senaste färdiga korpuskörningen med Ordförrådet ----------------------------------------
runs = []
for done_p in glob.glob(os.path.join(ROOT, "data", "cache", "r", "corpus", "*", "done.json")):
    d = os.path.dirname(done_p)
    if os.path.exists(os.path.join(d, "words.json")):
        done = json.load(open(done_p, encoding="utf-8"))
        if "words" not in (done.get("errors") or {}):
            runs.append((os.path.getmtime(done_p), d))
assert runs, "Ingen färdig korpuskörning med words.json hittades"
RUN = max(runs)[1]
W = json.load(open(os.path.join(RUN, "words.json"), encoding="utf-8"))

svn = lambda x, d=0: (f"{x:,.{d}f}".replace(",", " ").replace(".", ","))  # noqa: E731
enn = lambda x, d=0: f"{x:,.{d}f}"  # noqa: E731
pr = lambda x: round(100 * x)  # noqa: E731

reg = {(r["word"], r["province"]): r for r in W["region"]}
tid = {t["word"]: t for t in W["time"]}
holds = [r for r in W["region"] if r["holds"]]
ep = lambda w, i: pr(tid[w]["shares"][i]["k"] / tid[w]["shares"][i]["n"])  # noqa: E731

# ---- låsningarna: texten nedan får bara påstå det som står här ----------------------------------
assert W["n_words_tested"] == 75 and W["n_dated"] == 972 and W["n_stones"] == 1848
assert len(holds) == 14 and len({r["word"] for r in holds}) == 11 and len(W["time"]) == 30
AT = reg[("at", "Sö")]; assert AT["holds"] and pr(AT["rate_in"]) == 55 and pr(AT["rate_out"]) == 19
EFT = reg[("æftiR", "Sö")]; assert EFT["holds"] and pr(EFT["rate_in"]) == 32 and pr(EFT["rate_out"]) == 68
RVG = reg[("ræisti", "Vg")]; assert RVG["holds"] and pr(RVG["rate_in"]) == 52 and pr(RVG["rate_out"]) == 10
RU = reg[("ræisti", "U")]; assert RU["holds"] and pr(RU["rate_in"]) == 3 and pr(RU["rate_out"]) == 22
RSA = reg[("ræisa", "U")]; assert RSA["holds"] and pr(RSA["rate_in"]) == 43 and pr(RSA["rate_out"]) == 17
DR = reg[("dræng", "Vg")]; assert DR["holds"] and pr(DR["rate_in"]) == 12 and pr(DR["rate_out"]) == 1
GOD = reg[("goðan", "Vg")]; assert GOD["holds"] and pr(GOD["rate_in"]) == 30 and pr(GOD["rate_out"]) == 6
AND = reg[("and", "U")]; assert AND["holds"] and pr(AND["rate_in"]) == 13 and pr(AND["rate_out"]) == 5
assert tid["gærði"]["slope"] < 0 and ep("gærði", 0) == 10 and ep("gærði", 3) == 0
assert tid["letu"]["slope"] > 0 and ep("letu", 0) == 5 and ep("letu", 2) == 44
assert tid["risti"]["slope"] > 0 and ep("risti", 0) == 0 and ep("risti", 3) == 19
assert tid["þenna"]["slope"] < 0 and ep("þenna", 0) == 29 and ep("þenna", 3) == 10
NB = [(n["a"], n["b"]) for n in W["neighbors"]]
assert NB[0] == ("Sö", "U")
assert all(x["q"] < 0.05 for x in holds) and AT["q"] < 1e-15
EPOCH_LABELS = [s["epoch"] for s in W["time"][0]["shares"]]
assert EPOCH_LABELS == ["980–1015", "1015–1050", "1050–1080", "1080–1130"]

# ---- bilderna (Wikimedia Commons, licens och fotograf kontrollerade mot API:t) ------------------
IMG_U164 = "https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b0/Jarlabanke1.JPG/1280px-Jarlabanke1.JPG"
PAGE_U164 = "https://commons.wikimedia.org/wiki/File:Jarlabanke1.JPG"
IMG_VG181 = "https://upload.wikimedia.org/wikipedia/commons/6/67/Vg181_Frug%C3%A5rden%2C_Olsbro_-_KMB_-_16000300013812.jpg"
PAGE_VG181 = "https://commons.wikimedia.org/wiki/File:Vg181_Frug%C3%A5rden,_Olsbro_-_KMB_-_16000300013812.jpg"
IMG_SO14 = "https://thumb.wikimedia.org/wikipedia/commons/thumb/1/12/S%C3%B6_14%2C_G%C3%A5singe.JPG/1280px-S%C3%B6_14%2C_G%C3%A5singe.JPG"
PAGE_SO14 = "https://commons.wikimedia.org/wiki/File:S%C3%B6_14,_G%C3%A5singe.JPG"
CCBYSA3 = "https://creativecommons.org/licenses/by-sa/3.0"
CCBY25 = "https://creativecommons.org/licenses/by/2.5"
# Rikskartan ur appens Jämför länder-vy (mönstret þegn och drængr, rikena omkring 1025), fryst i bloggens arkiv
IMG_KARTA = "/api/blog/figures/35aea84e1d1f3006.png"
assert os.path.exists(os.path.join(ROOT, "data", "blog", "figures", os.path.basename(IMG_KARTA)))

title = "Västgöten reste själv – upplänningen lät resa"
summary = ("Vi räknade de vanligaste orden på Sveriges vikingatida runstenar, landskap för landskap och årtionde "
           "för årtionde. Orden håller sig hemma: Västergötland reste sina stenar med egna händer, Uppland lät "
           "andra göra jobbet, Södermanland satte sina märken at – inte æftiR – de döda. Elva ord vägrar vara "
           "rikssvenska, och trettio byter skepnad mitt under 1000-talet.")

body = f"""Den som läser många runstenar märker det till slut: stenarna säger nästan samma sak, men inte med samma ord. Någon *reste stenen efter* sin far. Någon annan *lät resa* – och det lilla ordet *lät* rymmer en hel arbetsdelning: en som beställde och betalade, en annan som högg. Vi har nu räknat ordvalen över hela det svenska materialet, och de visar sig varken vara slump eller smak. Ordvalet följer landskapen, och det följer tiden.

Underlaget är de {svn(W['n_stones'])} vikingatida runstenarna i Samnordisk runtextdatabas som har minst tre läsbara ord, och de {svn(W['n_words_tested'])} vanligaste orden på dem – namnen borträknade, för namn följer familjer och inte trakter. Varje ord räknas en gång per sten: antingen står det där eller inte. Av de orden har elva en regional signal som överlever alla kontroller vi kan utsätta den för, och trettio ändras tydligt över tid.

## Två sätt att resa en sten

Uppland och Västergötland gjorde samma sak med olika grammatik. På Västergötlands stenar dominerar det enkla verbet: *N ræisti stæin* – 'N reste stenen' – står på {pr(RVG['rate_in'])} procent av stenarna, mot {pr(RVG['rate_out'])} procent i resten av landet. I Uppland är samma ordform nästan utdöd, {pr(RU['rate_in'])} procent mot {pr(RU['rate_out'])} utanför. Upplänningarna sade i stället *let ræisa* – 'lät resa' – och mycket riktigt står *ræisa* på {pr(RSA['rate_in'])} procent av Upplands stenar mot {pr(RSA['rate_out'])} procent i övriga landet.

:::chart Att resa en sten: enkelt verb eller lät-konstruktion
# ræisti ('reste')
+Västergötland | {pr(RVG['rate_in'])} | {RVG['k_in']} av {RVG['n_in']} stenar
Uppland | {pr(RU['rate_in'])}
Resten av landet | {pr(RVG['rate_out'])}
# ræisa ('resa', efter lät)
+Uppland | {pr(RSA['rate_in'])} | {RSA['k_in']} av {RSA['n_in']} stenar
Resten av landet | {pr(RSA['rate_out'])}
Källa: Samnordisk runtextdatabas, {svn(W['n_stones'])} vikingatida runstenar med minst tre läsbara ord; Vitkis R-modul Ordförrådet. Andelarna är observerade, proven justerade för tid och textlängd.
:::

Skillnaden är inte bara stilistik. Den som *lät resa* betalade någon annan för arbetet – konstruktionen bär en antydan om beställare och utförare, om en arbetsdelning som tycks ha varit självklar i Mälardalen och ovanlig i väster. Ingen har drivit den tanken längre än Jarlabanke i Täby, som inte ens väntade på att dö: *"Jarlabanke lät resa dessa stenar åt sig själv, medan han ännu levde ... och ensam ägde han hela Täby."* Vi mäter orden, inte samhället bakom dem, men orden pekar.

![Jarlabankes sten vid bron i Täby]({IMG_U164})
En av Jarlabankes stenar vid broänden i Täby (U 164). Texten har beställarformeln i dess mest självmedvetna form: han *lät resa* stenarna åt sig själv i livstiden, *gærði* – gjorde – bron för sin själ, *and* sina, och ägde ensam hela Täby. Tre av orden i den här artikeln på en och samma sten. Foto: Einarspetz, [CC BY-SA 3.0]({CCBYSA3}), via [Wikimedia Commons]({PAGE_U164}).

Att något är vanligare i ett landskap kan bero på annat än landskapet. Upplandsstenarna är i genomsnitt yngre än Götalands, och korta texter rymmer färre ord än långa. Därför räknas varje ord i en modell som håller tiden (stilgruppens datering) och textens längd konstanta, och som dessutom behandlar ristaren som en egen källa till likhet – annars skulle en enda flitig ristares vana kunna se ut som ett helt landskaps. Till sist delas varje landskaps socknar i två halvor, och signalen måste peka åt samma håll i båda.

## Ordet som ritar en gräns kring Södermanland

Minnesformelns lilla preposition – *æftiR* eller *at* – är den skarpaste gränsen i hela materialet. På Södermanlands runstenar står *at* på {pr(AT['rate_in'])} procent av stenarna; i resten av landet på {pr(AT['rate_out'])}. Spegelbilden: *æftiR* står på {pr(EFT['rate_in'])} procent av sörmlandsstenarna mot {pr(EFT['rate_out'])} procent utanför. Samma formel, samma betydelse – men sörmlänningarna valde det korta ordet, och grannlandskapen det långa. Ordet *at* klarar alla kontrollerna med bred marginal: sannolikheten att se en så stor skillnad av en slump, om ordvalet egentligen vore lika i hela landet, är mindre än en på tusen biljoner.

:::chart Prepositionen i minnesformeln, andel av stenarna
# at
+Södermanland | {pr(AT['rate_in'])} | {AT['k_in']} av {AT['n_in']} stenar
Resten av landet | {pr(AT['rate_out'])}
# æftiR
Södermanland | {pr(EFT['rate_in'])}
+Resten av landet | {pr(EFT['rate_out'])}
Källa: samma underlag och modell som ovan.
:::

![Runstenen Sö 14 vid Gåsinge kyrka]({IMG_SO14})
Sö 14 vid Gåsinge kyrka: Ragna reste stenen *at* Sven, sin make – med prepositionen som ritar Södermanlands gräns. Foto: Berig, [CC BY-SA 3.0]({CCBYSA3}), via [Wikimedia Commons]({PAGE_SO14}).

## Västgötarnas dräng och Upplands själar

Två ord till som vägrar flytta hemifrån. På Västergötlands stenar hyllas de döda som *goðan dræng* – 'en god ung man': *dræng* står på {pr(DR['rate_in'])} procent av stenarna där mot {pr(DR['rate_out'])} procent i resten av landet, och *goðan* på {pr(GOD['rate_in'])} mot {pr(GOD['rate_out'])}. Det rimmar med vad vi sett förr: Västgötarnas formelspråk pekar söderut, mot det danska området, där drängarna också bor i stenarna.

![Runstenen Vg 181 vid Frugården]({IMG_VG181})
Vg 181 vid Frugården: Gufi *reste* stenen – det enkla västgötska verbet – efter sonen Olav, *dræng harða goðan*, 'en mycket god dräng', som dräptes i Estland. Foto: Bengt A. Lundberg, Riksantikvarieämbetet, [CC BY 2.5]({CCBY25}), via [Wikimedia Commons]({PAGE_VG181}).

![Titelorden þegn och drængr på kartan, med rikena omkring 1025]({IMG_KARTA})
Titelorden *þegn* och *drængr* på Vitkis karta, med rikenas ungefärliga gränser omkring 1025: Danmark i rött, götarnas landskap i grönt, Svitjod i brunt, Norge i lila. Blå rutor är andelen runstenar i rutan som bär mönstret – mörkare är större andel. Titlarna samlas i det danska området och i Västergötland, och tunnas ut norrut mot Mälardalen. Kartan går att utforska själv under Karta → Jämför länder i appen.

:::box Två mätningar, samma gräns
Den här artikeln hör ihop med [Västgötarna skrev som danskarna](/artiklar/vastgotarna-skrev-som-danskarna). Där mätte vi *hur* orden stavades – ljud för ljud, över riksgränsen – och Västergötland lutade söderut medan gränsbygden teg. Här mäter vi i stället *vilka* ord som alls står på stenarna, inom Sverige. Det är två oberoende mätningar: stavningen vet ingenting om ordvalet, och ordvalet ingenting om stavningen. Att båda pekar åt samma håll – Västergötland delade tradition med det danska området, och Mälardalen gick sin egen väg – gör slutsatsen mycket starkare än någon av mätningarna ensam.
:::

I Uppland är det i stället själen som sticker ut. Bönens *and* – 'ande, själ' – står på {pr(AND['rate_in'])} procent av Upplands stenar mot {pr(AND['rate_out'])} procent i övriga landet. Upplands många sena, kristna stenar ber oftare för själen – och eftersom modellen håller tiden konstant är det inte bara en effekt av att Uppland ristade längst. Jarlabanke igen: bron gjorde han *fyr and sina*, för sin själ.

## Orden som gick ur tiden

Trettio av de {svn(W['n_words_tested'])} orden ökar eller minskar tydligt över 1000-talet. Tillsammans ser man formelboken byta skepnad. Verbet *gærði* – 'gjorde' – står på {ep('gærði', 0)} procent av de äldsta stenarna och faller till noll på de yngsta. *Letu* – 'läto', flera beställare som lät resa – går åt andra hållet, från {ep('letu', 0)} procent till {ep('letu', 2)} som mest, och *risti* – 'ristade', ristarens eget verb i signaturen – växer från ingenting till {ep('risti', 3)} procent när ristarna mot slutet allt oftare skriver sitt namn. Utpekandets *þenna* – 'denna sten' – halveras, från {ep('þenna', 0)} procent till {ep('þenna', 3)}.

:::chart Fyra ord över tid, andel av de daterade stenarna
# gærði ('gjorde')
{EPOCH_LABELS[0]} | {ep('gærði', 0)}
{EPOCH_LABELS[1]} | {ep('gærði', 1)}
{EPOCH_LABELS[2]} | {ep('gærði', 2)}
+{EPOCH_LABELS[3]} | {ep('gærði', 3)}
# letu ('läto')
{EPOCH_LABELS[0]} | {ep('letu', 0)}
{EPOCH_LABELS[1]} | {ep('letu', 1)}
+{EPOCH_LABELS[2]} | {ep('letu', 2)}
{EPOCH_LABELS[3]} | {ep('letu', 3)}
# risti ('ristade')
{EPOCH_LABELS[0]} | {ep('risti', 0)}
{EPOCH_LABELS[1]} | {ep('risti', 1)}
{EPOCH_LABELS[2]} | {ep('risti', 2)}
+{EPOCH_LABELS[3]} | {ep('risti', 3)}
# þenna ('denna')
+{EPOCH_LABELS[0]} | {ep('þenna', 0)}
{EPOCH_LABELS[1]} | {ep('þenna', 1)}
{EPOCH_LABELS[2]} | {ep('þenna', 2)}
{EPOCH_LABELS[3]} | {ep('þenna', 3)}
Källa: de {svn(W['n_dated'])} daterade stenarna; tiden kommer ur stilgrupperna (Gräslund), därför ungefär 980–1130.
:::

Dateringen förtjänar sin egen brasklapp: årtalen kommer ur ornamentikens stilgrupper, inte ur årtal på stenarna, så kurvorna beskriver stilgruppernas tid. Men riktningarna håller när vi justerar för landskap och textlängd, och de berättar en begriplig historia – beställarformeln tar över, ristarna signerar, och det gamla *gærði* dör med sin generation.

## Vilka landskap skriver mest lika?

Lägger man landskapens hela ordprofiler bredvid varandra – med korrespondensanalys, samma metod som arkeologer använder för att ordna gravfynd – hamnar Södermanland och Uppland närmast varandra, med Östergötland strax intill. Västergötland står för sig självt, draget åt sitt *ræisti*, sin *dræng* och sin *goðan*. Det är samma bild som språkdragen gav i våra tidigare analyser, men nu framräknad ur något så enkelt som vilka ord som alls står på stenarna.

:::box Så räknade vi
Orden är Rundatas normaliserade former på de {svn(W['n_stones'])} vikingatida runstenarna med minst tre läsbara ord; skadade och osäkra ord räknas inte, och namn ingår inte. Ett ord räknas en gång per sten. För varje ord med belägg på minst tjugo stenar skattas en logistisk modell på de {svn(W['n_dated'])} daterade stenarna: landskap mot riksgenomsnittet, stilgruppens mittår och textens längd som kontroller, och ristaren som slumpeffekt (stenar utan känd ristare grupperas per socken). Alla p-värden justeras för de många proven (Benjamini–Hochberg, q under 0,05), och varje regional signal prövas dessutom i två sockenhalvor med krav på samma riktning i båda. Bara Östergötland, Södermanland, Uppland och Västergötland har nog med daterade stenar för egna prov. Metoden i sin helhet: METHODS.md, avsnitt 1m, i Vitkis källkod; hela analysen går att köra om på statistiksidan i appen.
:::

Vad betyder det att orden höll sig hemma? Försiktigt uttryckt: att minnesformlerna inte var en rikslikare utan lokala traditioner, stabila nog att överleva justering för tid, textlängd och enskilda ristare. Vad vi *inte* kan säga är varför – om det är dialekt i talet, formelvanor i verkstäderna eller beställarnas smak. Orden skiljer inte på de tre. Men gränserna de ritar är verkliga, och de går att pröva vidare: varje tabell i analysen går att ladda ner, och den som vill kan börja med att läsa en sörmländsk sten och en västgötsk bredvid varandra. Lyssna efter *at* – och efter drängen.

*Data: Samnordisk runtextdatabas (Uppsala universitet). Analysen är fri programvara i Vitki; alla siffror i artikeln är framräknade ur modulen Ordförrådet och låsta mot dess resultat i artikelbygget.*"""

body_en = f"""Anyone who reads many runestones notices it eventually: the stones say nearly the same thing, but not with the same words. One man *raised the stone after* his father. Another *had it raised* – and that little *had* holds a whole division of labour: one who commissioned and paid, another who carved. We have now counted the choices of words across the whole Swedish corpus, and they turn out to be neither chance nor taste. The choice of words follows the provinces, and it follows time.

The material is the {enn(W['n_stones'])} Viking-age runestones in the Scandinavian Runic Text Database with at least three legible words, and the {enn(W['n_words_tested'])} most common words on them – names excluded, since names follow families rather than regions. Each word is counted once per stone: either it is there or it is not. Of those words, eleven carry a regional signal that survives every control we can subject it to, and thirty change clearly over time.

## Two ways to raise a stone

Uppland and Västergötland did the same thing with different grammar. On the stones of Västergötland the simple verb dominates: *N ræisti stæin* – 'N raised the stone' – stands on {pr(RVG['rate_in'])} per cent of the stones, against {pr(RVG['rate_out'])} per cent in the rest of the country. In Uppland the same word form is nearly extinct, {pr(RU['rate_in'])} per cent against {pr(RU['rate_out'])} outside. The Upplanders said *let ræisa* – 'had raised' – instead, and accordingly *ræisa* stands on {pr(RSA['rate_in'])} per cent of Uppland's stones against {pr(RSA['rate_out'])} per cent elsewhere.

:::chart Raising a stone: simple verb or had-it-raised
# ræisti ('raised')
+Västergötland | {pr(RVG['rate_in'])} | {RVG['k_in']} of {RVG['n_in']} stones
Uppland | {pr(RU['rate_in'])}
Rest of the country | {pr(RVG['rate_out'])}
# ræisa ('raise', after let)
+Uppland | {pr(RSA['rate_in'])} | {RSA['k_in']} of {RSA['n_in']} stones
Rest of the country | {pr(RSA['rate_out'])}
Source: Scandinavian Runic Text Database, {enn(W['n_stones'])} Viking-age runestones with at least three legible words; Vitki's R module Ordförrådet. The shares are observed, the tests adjusted for time and text length.
:::

The difference is not merely stylistic. Whoever *had a stone raised* paid someone else for the work – the construction carries a hint of commissioner and craftsman, of a division of labour that seems to have been self-evident around Lake Mälaren and uncommon in the west. No one took that idea further than Jarlabanke of Täby, who did not even wait to die: *"Jarlabanki had these stones raised for himself while he was still alive ... and alone he owned all of Täby."* We measure the words, not the society behind them, but the words point.

![Jarlabanke's stone at the bridge in Täby]({IMG_U164})
One of Jarlabanke's stones at the bridge end in Täby (U 164). The text has the commissioner formula in its most self-assured form: he *had the stones raised* for himself while alive, *gærði* – made – the bridge for his soul, *and* sina, and alone owned all of Täby. Three of the words of this article on one and the same stone. Photo: Einarspetz, [CC BY-SA 3.0]({CCBYSA3}), via [Wikimedia Commons]({PAGE_U164}).

Something being more common in one province can have other causes than the province. The Uppland stones are on average younger than Götaland's, and short texts hold fewer words than long ones. Every word is therefore counted in a model that holds time (the style-group dating) and text length constant, and that moreover treats the carver as a source of similarity of its own – otherwise a single prolific carver's habit could look like a whole province's. Finally, each province's parishes are split into two halves, and the signal must point the same way in both.

## The word that draws a line around Södermanland

The memorial formula's little preposition – *æftiR* or *at* – is the sharpest boundary in the whole material. On the runestones of Södermanland, *at* stands on {pr(AT['rate_in'])} per cent of the stones; in the rest of the country on {pr(AT['rate_out'])}. The mirror image: *æftiR* stands on {pr(EFT['rate_in'])} per cent of the Södermanland stones against {pr(EFT['rate_out'])} per cent outside. The same formula, the same meaning – but the people of Södermanland chose the short word, and the neighbouring provinces the long one. The word *at* passes all the controls with a wide margin: the probability of seeing so large a difference by chance, if the choice of words were really the same across the country, is less than one in a thousand trillion.

:::chart The preposition of the memorial formula, share of stones
# at
+Södermanland | {pr(AT['rate_in'])} | {AT['k_in']} of {AT['n_in']} stones
Rest of the country | {pr(AT['rate_out'])}
# æftiR
Södermanland | {pr(EFT['rate_in'])}
+Rest of the country | {pr(EFT['rate_out'])}
Source: the same material and model as above.
:::

![The runestone Sö 14 at Gåsinge church]({IMG_SO14})
Sö 14 at Gåsinge church: Ragna raised the stone *at* Sveinn, her husband – with the preposition that draws Södermanland's boundary. Photo: Berig, [CC BY-SA 3.0]({CCBYSA3}), via [Wikimedia Commons]({PAGE_SO14}).

## Västergötland's dræng and Uppland's souls

Two more words that refuse to leave home. On the stones of Västergötland the dead are praised as *goðan dræng* – 'a good young man': *dræng* stands on {pr(DR['rate_in'])} per cent of the stones there against {pr(DR['rate_out'])} per cent in the rest of the country, and *goðan* on {pr(GOD['rate_in'])} against {pr(GOD['rate_out'])}. That fits what we have seen before: the formula language of Västergötland points south, towards the Danish area, where the drengs live in the stones too.

![The runestone Vg 181 at Frugården]({IMG_VG181})
Vg 181 at Frugården: Gufi *raised* the stone – the simple western verb – after his son Olav, *dræng harða goðan*, 'a very good dreng', who was killed in Estonia. Photo: Bengt A. Lundberg, Swedish National Heritage Board, [CC BY 2.5]({CCBY25}), via [Wikimedia Commons]({PAGE_VG181}).

![The title words þegn and drængr on the map, with the realms about 1025]({IMG_KARTA})
The title words *þegn* and *drængr* on Vitki's map, with the approximate borders of the realms about 1025: Denmark in red, the Geatish provinces in green, Svitjod in brown, Norway in purple. Blue cells are the share of runestones in the cell carrying the pattern – darker is a larger share. The titles gather in the Danish area and in Västergötland, and thin out northwards towards Lake Mälaren. The map can be explored under Karta → Jämför länder in the app.

:::box Two measurements, the same boundary
This article belongs together with [The Westrogothians wrote like the Danes](/artiklar/vastgotarna-skrev-som-danskarna). There we measured *how* the words were spelled – sound by sound, across the national border – and Västergötland leaned south while the border country kept silent. Here we instead measure *which* words stand on the stones at all, within Sweden. The two measurements are independent: the spelling knows nothing of the choice of words, and the choice of words nothing of the spelling. That both point the same way – Västergötland shared its tradition with the Danish area, and the Mälaren valley went its own way – makes the conclusion far stronger than either measurement alone.
:::

In Uppland it is instead the soul that stands out. The prayer's *and* – 'spirit, soul' – stands on {pr(AND['rate_in'])} per cent of Uppland's stones against {pr(AND['rate_out'])} per cent elsewhere. Uppland's many late, Christian stones pray for the soul more often – and since the model holds time constant, this is not merely an effect of Uppland carving longest. Jarlabanke again: the bridge he made *fyr and sina*, for his soul.

## The words that went out of time

Thirty of the {enn(W['n_words_tested'])} words rise or fall clearly across the eleventh century. Together they show the book of formulas changing shape. The verb *gærði* – 'made' – stands on {ep('gærði', 0)} per cent of the oldest stones and falls to zero on the youngest. *Letu* – 'had raised', several commissioners – goes the other way, from {ep('letu', 0)} per cent to {ep('letu', 2)} at its peak, and *risti* – 'carved', the carver's own verb in the signature – grows from nothing to {ep('risti', 3)} per cent as carvers towards the end sign their names ever more often. The deictic *þenna* – 'this stone' – is halved, from {ep('þenna', 0)} per cent to {ep('þenna', 3)}.

:::chart Four words over time, share of the dated stones
# gærði ('made')
{EPOCH_LABELS[0]} | {ep('gærði', 0)}
{EPOCH_LABELS[1]} | {ep('gærði', 1)}
{EPOCH_LABELS[2]} | {ep('gærði', 2)}
+{EPOCH_LABELS[3]} | {ep('gærði', 3)}
# letu ('had raised')
{EPOCH_LABELS[0]} | {ep('letu', 0)}
{EPOCH_LABELS[1]} | {ep('letu', 1)}
+{EPOCH_LABELS[2]} | {ep('letu', 2)}
{EPOCH_LABELS[3]} | {ep('letu', 3)}
# risti ('carved')
{EPOCH_LABELS[0]} | {ep('risti', 0)}
{EPOCH_LABELS[1]} | {ep('risti', 1)}
{EPOCH_LABELS[2]} | {ep('risti', 2)}
+{EPOCH_LABELS[3]} | {ep('risti', 3)}
# þenna ('this')
+{EPOCH_LABELS[0]} | {ep('þenna', 0)}
{EPOCH_LABELS[1]} | {ep('þenna', 1)}
{EPOCH_LABELS[2]} | {ep('þenna', 2)}
{EPOCH_LABELS[3]} | {ep('þenna', 3)}
Source: the {enn(W['n_dated'])} dated stones; the dating comes from the ornamental style groups (Gräslund), hence roughly 980–1130.
:::

The dating deserves its own caveat: the years come from the ornamental style groups, not from dates on the stones, so the curves describe the style groups' time. But the directions hold when we adjust for province and text length, and they tell an intelligible story – the commissioner formula takes over, the carvers sign, and the old *gærði* dies with its generation.

## Which provinces write most alike?

Laying the provinces' whole word profiles side by side – with correspondence analysis, the same method archaeologists use to order grave finds – Södermanland and Uppland end up closest to each other, with Östergötland just beside them. Västergötland stands on its own, pulled towards its *ræisti*, its *dræng* and its *goðan*. It is the same picture that the language traits gave in our earlier analyses, but now computed from something as simple as which words stand on the stones at all.

:::box How we counted
The words are the normalised forms of the Runic Text Database on the {enn(W['n_stones'])} Viking-age runestones with at least three legible words; damaged and uncertain words are not counted, and names are excluded. A word is counted once per stone. For every word attested on at least twenty stones, a logistic model is fitted on the {enn(W['n_dated'])} dated stones: province against the national mean, the style group's mid-year and the length of the text as controls, and the carver as a random effect (stones without a known carver are grouped by parish). All p-values are adjusted for the many tests (Benjamini–Hochberg, q below 0.05), and every regional signal is additionally tested in two parish halves, required to point the same way in both. Only Östergötland, Södermanland, Uppland and Västergötland have enough dated stones for tests of their own. The full method: METHODS.md, section 1m, in Vitki's source code; the whole analysis can be re-run from the statistics page in the app.
:::

What does it mean that the words stayed home? Put cautiously: that the memorial formulas were not a national standard but local traditions, stable enough to survive adjustment for time, text length and individual carvers. What we *cannot* say is why – whether it is dialect in speech, formula habits in the workshops, or the taste of the commissioners. The words do not distinguish the three. But the boundaries they draw are real, and they can be tested further: every table in the analysis can be downloaded, and anyone who likes can begin by reading one stone from Södermanland and one from Västergötland side by side. Listen for the *at* – and for the dreng.

*Data: Scandinavian Runic Text Database (Uppsala University). The analysis is free software in Vitki; every figure in this article is computed from the Ordförrådet module and locked against its results in the article build.*"""

# aldrig siffra först i en mening (husregeln); bildrader och diagramrader räknas inte som meningar
for b in (body, body_en):
    flat = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", b).replace("\n", " ")
    for m in re.finditer(r"[.!?]\s+(\d)", flat):
        ctx = flat[max(0, m.start() - 40):m.end() + 20]
        assert re.search(r"U 164|Vg 181|Sö 14|980|1015|1050|1080", ctx), f"Mening börjar med siffra: …{ctx}…"

out = {"slug": "reste-sjalv-eller-lat-resa", "title": title, "summary": summary, "body": body,
       "title_en": "Raise It Yourself – or Have It Raised",
       "summary_en": ("We counted the most common words on Sweden's Viking-age runestones, province by province "
                      "and decade by decade. The words stayed home: Västergötland raised its stones with its own "
                      "hands, Uppland had others do the work, Södermanland set its marks at – not æftiR – the "
                      "dead. Eleven words refuse to be national, and thirty change shape in the middle of the "
                      "eleventh century."),
       "body_en": body_en}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "ordartikel.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "ordartikel.json"), len(body), len(body_en))

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
                 "topic": "Språk och formler|statistik i R", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
