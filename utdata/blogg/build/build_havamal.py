"""Artikeln "Vem talar i Hávamál?": diktens dolda arkitektur mätt – röstkartan (han/jag/du), den blinda
sömsökningen, skiktstilometrin och korsningen mot runkorpusen (först i sitt slag). Varje siffra hämtas ur
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
V = D["voice"]
assert V["I"]["ek_per100"] == 1.0 and V["I"]["thu_per100"] == 0.8
assert V["IV"]["thu_per100"] == 16.4 and V["VI"]["ek_per100"] == 10.6
assert V["II"]["ek_per100"] == 4.6 and V["III"]["ek_per100"] == 7.8 and V["V"]["ek_per100"] == 6.5
topseam = [s for s, _ in D["seams"][:8]]
assert 112 in topseam[:2] and 138 in topseam[:2]
assert not any(83 <= s <= 85 for s in topseam), "gränsen vid 84 ska INTE vara en topp-söm"
S = R["stilometri"]
assert S["inom_medel"] == 0.689 and S["mellan_medel"] == 1.131 and S["stylo_kontroll"] is True
MB = D["memorial_bydel"]
assert 0.16 <= min(MB.values()) and max(MB.values()) <= 0.21
d76 = {int(r["nr"]): r for r in STROF}
assert "deyr fé" in d76[76]["text"].lower() and "orðstírr" in d76[76]["text"]
full = " ".join(r["text"].lower() for r in STROF)
assert all(full.count(w) == 0 for w in ("krist", "kirkj", "messa", "synd"))
amnesdom = {x["del"]: x["dominans"] for x in R["amnesdominans_per_del"]}
assert amnesdom["V"] == 0.75
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

IMG_CR = "https://upload.wikimedia.org/wikipedia/commons/5/50/Codex_Regius_of_Eddaic_Poems.jpg"
PAGE_CR = "https://commons.wikimedia.org/wiki/File:Codex_Regius_of_Eddaic_Poems.jpg"
IMG_ODIN = "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/4d/Odin%27s_Self-sacrifice_by_Collingwood.jpg/1280px-Odin%27s_Self-sacrifice_by_Collingwood.jpg"
PAGE_ODIN = "https://commons.wikimedia.org/wiki/File:Odin%27s_Self-sacrifice_by_Collingwood.jpg"
IMG_GUNN = "https://upload.wikimedia.org/wikipedia/commons/1/1f/Odin_and_Gunnl%C3%B6%C3%B0_by_Fr%C3%B8lich.jpg"
PAGE_GUNN = "https://commons.wikimedia.org/wiki/File:Odin_and_Gunnl%C3%B6%C3%B0_by_Fr%C3%B8lich.jpg"

title = "Vem talar i Hávamál?"
summary = ("Eddans visdomsdikt är genomtröskad av tvåhundra års forskning – så den här artikeln håller sig "
           "till det ingen visat förut. En blind sömsökning hittar själv två av diktens skarvar men förklarar "
           "en tredje mjuk, två av Odens bekännelser visar sig dela stil fast de inte står ihop, och för "
           "första gången mäts dikten mot Nordens samlade runstenar. Där föll vår egen hypotes – och "
           "ersattes av ett spår som pekar västerut, mot diktens hemtrakt.")

body = f"""Hávamál, "den höges tal", är nordens mest citerade dikt: etthundrasextiofyra strofer visdom, varningar, kärleksäventyr och trolldom, bevarade i en enda handskrift – Codex Regius, nedskriven på Island omkring 1270. Forskare har i tvåhundra år diskuterat om dikten är ett verk eller flera hopfogade, var skarvarna går och vad den egentligen vill. Det mesta om dikten är redan utrett, och det tänker vi inte upprepa. Den här artikeln håller sig till det forskningen inte redan visste: fyra mätningar som är nya – varav en gick emot oss själva.

![Uppslag ur Codex Regius]({IMG_CR})
Codex Regius (GKS 2365 4to), nedskriven omkring 1270 – Hávamáls enda medeltida källa. Allt i den här artikeln är mätt på den textens normaliserade utgåva (Guðni Jónsson). Bild: public domain, via [Wikimedia Commons]({PAGE_CR}).

:::box Det som redan var känt
Att Hávamál är sammansatt av flera stycken har forskningen vetat sedan 1800-talet (Müllenhoff; den moderna skiktanalysen är John McKinnells). Dateringen är också andras fält: senast Mikael Males (2024), som prövar sex oberoende kriterier och landar i att dikten sannolikt fick sin form omkring 900–950. Att kristet ordförråd saknas helt – vilket vår mätning bekräftar rakt igenom – var ett av David Evans huvudargument redan på 1980-talet, liksom platsbelägget i strof 72: *bautastenar* är okända på Island men hör hemma i det förkristna Skandinavien. Allt detta är utgångspunkt här, inte resultat.
:::

## Rösterna ritar arkitekturen

Att rösterna skiftar genom dikten har varje läsare hört – men ingen har satt siffror på hela kartan. Vi räknade första person (*ek*, 'jag') och andra person (*þú*, 'du') per hundra ord, del för del.

:::chart Rösterna i Hávamál, förekomster per hundra ord
# jag (ek)
Gästvisdomen 1–83 | {svn(V['I']['ek_per100'])}
Kvinnoråden 84–102 | {svn(V['II']['ek_per100'])}
Gunnlöd-episoden 103–110 | {svn(V['III']['ek_per100'])}
Loddfáfnismál 111–137 | {svn(V['IV']['ek_per100'])}
Runatal 138–145 | {svn(V['V']['ek_per100'])}
+Trollsångerna 146–164 | {svn(V['VI']['ek_per100'])}
# du (þú)
Gästvisdomen 1–83 | {svn(V['I']['thu_per100'])}
Kvinnoråden 84–102 | {svn(V['II']['thu_per100'])}
Gunnlöd-episoden 103–110 | {svn(V['III']['thu_per100'])}
+Loddfáfnismál 111–137 | {svn(V['IV']['thu_per100'])}
Runatal 138–145 | {svn(V['V']['thu_per100'])}
Trollsångerna 146–164 | {svn(V['VI']['thu_per100'])}
Källa: Codex Regius-texten i Guðni Jónssons utgåva; Vitkis analys (utdata/Edda i kodförrådet).
:::

Mönstret är slående. Den stora gästvisdomen i diktens början är nästan röstlös – ett *jag* eller *du* per hundra ord; visdomen talar om människan i tredje person. Sedan kliver jaget in: i kärleksäventyren säger Oden *ek* nästan fem gånger per hundra ord, i Gunnlöd-episoden åtta. Loddfáfnismál vänder allt till ett förmaningens du-regn – sexton *þú* per hundra ord, mer än tjugo gånger tätare än i gästvisdomen. Och i trollsångerna tar jaget över helt: *þat kann ek*, 'det kan jag', sjutton gånger på nitton strofer. Dikten rör sig mätbart från **han** (den allmänna klokskapen) över **jag** (erfarenheten) och **du** (förmaningen) till **jag** igen (makten). Det är en dramaturgi – och den syns i siffror.

## Den blinda sömsökningen

Är delarna verkligen olika stycken, eller är indelningen något utgivare lagt på texten? Vi lät ett fönster om tio strofer glida genom dikten och mätte hur mycket funktionsorden – småorden en författare sällan väljer medvetet – skiljer sig före och efter varje punkt. Metoden vet ingenting om forskningens indelning.

De två starkaste stilbrotten i hela dikten hamnade vid strof 111–112 och 138–140: **exakt där Loddfáfnismál respektive Runatal börjar** – gränser som forskningen dragit sedan Müllenhoffs dagar och som John McKinnell bygger sin moderna skiktanalys på. Att en blind metod återfinner dem betyder att de är verkliga sömmar i språket, inte utgivarkonvention. Lika talande är var metoden *inte* slår ut: vid strof 84, där McKinnell låter sin "intrigdikt" börja, ger funktionsorden inget utslag alls. Den övergången är lexikalt mjuk – gästvisdomen glider över i kärleksvarningarna snarare än byter språkdräkt. Det är ett nytt empiriskt datum i en gammal debatt.

Stilmätningen som helhet pekar åt samma håll: strofblock inom samma del liknar varandra (Burrows' Delta 0,69 i snitt) medan block ur olika delar skiljer sig klart mer (1,13). Och i släktträdet över blocken händer något vackert: Gunnlöd-episoden och Runatal – de två ställen där Oden berättar om *sina egna* nederlag och offer – lägger sig närmast varandra, fast de inte står intill i dikten. Det är en parning som inte finns i McKinnells indelning, där Runatal i stället hör ihop med trollsångerna och Gunnlöd med intrigdikten; vi redovisar den som ett mätresultat att pröva, inte som ett anspråk om upphov. Men tanken ligger nära: diktens "Odens bekännelser" delar stil.

![Odens självoffer, tecknat av W.G. Collingwood]({IMG_ODIN})
"Jag vet att jag hängde på det vindpinade trädet nio hela nätter" – Runatal är diktens tematiskt renaste del (ett enda LDA-ämne dominerar {svn(100 * amnesdom['V'], 0)} procent av stroferna) och stilsyskon med Gunnlöd-episoden. Teckning: W.G. Collingwood (1908), public domain, via [Wikimedia Commons]({PAGE_ODIN}).

![Oden och Gunnlöd, tecknade av Lorenz Frølich]({IMG_GUNN})
Oden hos Gunnlöd, Lorenz Frølichs teckning. Episoden är kort – åtta strofer – men bär samma stilsignatur som Runatal. Bild: public domain, via [Wikimedia Commons]({PAGE_GUNN}).

Ett tredje spår i trädet: gästvisdomens sista strofer, 67–83 – trakten kring *deyr fé* – driver bort från sin egen dels början och lägger sig närmare kvinnoråden. Många forskare låter den gnomiska dikten sluta redan vid strof 79, och vår mätning, som inte läst den debatten, pekar på samma trakt: slutet av del I hör stilistiskt inte riktigt ihop med sin början.

## Hypotesen som föll: Hávamál låter inte som runstenarna

Här kommer artikelns ärligaste fynd. Hávamáls mest berömda strofer säger samma sak som varje runsten: *Deyr fé, deyja frændr … en orðstírr deyr aldregi* – boskap dör, fränder dör, men eftermälet dör aldrig. Runstenarna är ju exakt det: eftermälen i sten. Så vi antog att förgänglighetsstroferna också skulle *låta* som runstenarna, och mätte varje strofs ordförråd mot de tvåhundra vanligaste orden på Nordens vikingatida runstenar – samma korpus som driver resten av Vitki.

Hypotesen föll. Likheten med runstenarnas formelspråk är jämnt låg genom hela dikten – medianen ligger mellan {svn(100 * min(MB.values()), 0)} och {svn(100 * max(MB.values()), 0)} procent av strofens ordtyper i alla sex delarna – och *deyr fé*-stroferna ligger mitt i fältet, inte i toppen. Dikten och stenarna delar eftermälets teologi, men inte dess ord: runstenens *ræisti stæin æftiR* och Hávamáls *orðstírr* är två skilda språkvärldar kring samma tanke. Det talar för två oberoende traditioner – minnesformeln på stenarna är inte diktcitat, och dikten härmar inte stenarna. Såvitt vi vet är det första gången dikten mäts mot en hel runkorpus, och det tydligaste resultatet blev ett nej – vilket är precis så mätningar ska få lov att sluta.

Så delade vi korpusen per land – dikten är ju västnordisk, stenarna till största delen östnordiska. Då träder ett andra mönster fram. Jämfört på lika stora textmängder ligger de norska stenarnas vanligaste ord närmast dikten ({pN} procent av strofens ordtyper), de danska därnäst ({pD} procent) och de svenska längst bort ({pS} procent); av trehundra slumpdragningar ur den svenska korpusen når en enda upp till den norska nivån. Ordningen följer alltså geografin, väst mot öst. Och orden som gör skillnaden är inte minnesformelns utan vardagens: på de norska stenarna *sá*, *mér*, *konu*, *upp*, *stendr*, på de danska *munu*, *vel*, *lifa*, *nú*, *lengi* – ord som också bär dikten – medan de svenska stenarnas topplista trängs med namn och res-formeln. Norges runstenskorpus är liten, bara 66 stenar, så detta är en antydan och inget bevis, och mer mångordiga inskrifter väster ut kan förklara en del av skillnaden. Men pilen pekar åt samma håll som diktens egen hemtrakt: där stenarna får tala vardagsspråk kommer de Hávamál närmare, och ju längre väster ut de står, desto närmare kommer de.

## Där dikten och stenarna ändå möts

Ett möte finns till slut ändå, och det står i dikten själv: strof 72 säger att *bautastenar sällan står vid vägen om inte frände reser dem efter frände*. Seden strofen beskriver är exakt den vår runkorpus består av – tusentals stenar, resta vid vägar och broar, av fränder efter fränder. Det belägget är Evans, inte vårt. Men vår mätning lägger en egen liten vikt i samma vågskål: stenarnas språk ligger närmast diktens just i väster, där strofens bautastenar hör hemma.

:::box Så räknade vi
Texten är Codex Regius-textens normaliserade utgåva (Guðni Jónsson), 164 strofer, cirka 5 000 ord. Rösterna räknades som *ek*- respektive *þú*-former per hundra ord. Sömsökningen jämför funktionsordens fördelning i tio strofer före mot tio efter varje punkt, utan kännedom om någon indelning. Skiktjämförelsen använder Burrows' Delta på de sextio vanligaste orden i strofblock om högst 22 strofer, kontrollerad mot stylo-paketets egen beräkning, med LDA-ämnen, typ/token-kvot och versgränser (utgåvans kommatering) som stöd. Runstensjämförelsen räknar andelen av strofens ordtyper som finns bland de tvåhundra vanligaste orden i Rundatas vikingatida runstensnormaliseringar, med ordformerna hopslagna över normaliseringstraditionerna. Landjämförelsen delar korpusen i svenska, danska (DR) och norska (N) stenar; eftersom en topplista ur en liten korpus når djupare ner i vardagsorden jämförs länderna efter slumpprov med lika många löpord, trehundra dragningar per land. All kod och alla resultatfiler ligger öppet i kodförrådet (utdata/Edda).
:::

:::box Det viktigaste i korthet
- En blind sökning som inte vet var forskningen drar sina gränser hittar själv språksömmarna där Loddfáfnismál och Runatal börjar – men ingen alls vid strof 84, där en omdebatterad del sägs börja. Den övergången är språkligt mjuk, och det är ett nytt datum i en gammal debatt.
- Gunnlöd-episoden och Runatal delar stil fast de inte står ihop i dikten – Odens bekännelser kan vara ett eget skikt, en parning som inte finns i forskningens scheman.
- Diktens mest berömda tanke, att bara eftermälet består, delas med varje runsten – men språket delas inte: den första mätningen någonsin mot en hel runkorpus slutade i ett nej, och nejet betyder att dikt och minnesformel är två oberoende traditioner kring samma idé.
- Delas runkorpusen per land ligger stenarnas vardagsspråk närmast dikten i väster och längst bort i öster – ett svagt men riktningsrätt eko av diktens västnordiska hemtrakt.
- Inget av detta daterar eller placerar dikten: en enda handskrift från 1270-talet sätter gränsen för vad någon metod kan veta, och stilskillnad kan bero på genre lika väl som på hand eller tid.
:::

## Källor och data

- Forskningsläget: diktens sammansatta natur är dokumenterad sedan Müllenhoff på 1800-talet; den moderna skiktanalysen är John McKinnell, "The Making of Hávamál" (Viking and Medieval Scandinavia 3, 2007). Datering: Bjarne Fidjestøl, The Dating of Eddic Poetry (1999); Haukur Þorgeirsson (2012, 2016, 2017); Christopher Sapp (2022); Mikael Males, "The Dating of Hávamál" (Maal og Minne 1-2024). Utgåva och kommentar: David A. H. Evans, Hávamál (Viking Society, 1986). Gnomisk stil: Carolyne Larrington, A Store of Common Sense (1993). Vårt bidrag är ett annat än deras: skiktens stilometri, den blinda sömsökningen, röstkartan och korsningen mot runkorpusen.
- Hávamál: Guðni Jónssons normaliserade utgåva av Codex Regius-texten (Eddukvæði, Sæmundar-Edda), via heimskringla.no.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet, för runstensjämförelsen.
- Analyskod och resultat: utdata/Edda i Vitkis kodförråd (R-paketen stylo, topicmodels, tidytext, quanteda, factoextra).
- Bilder: Wikimedia Commons, public domain, med upphov i bildtexterna.

*Stilometrin själv daterar och placerar ingenting – en enda handskrift från 1270-talet sätter den gränsen. Men den kan mäta sömmar, röster och ordvärldar, och lämna siffrorna öppna för runologer och filologer att pröva.*"""

body_en = f"""Hávamál, "the words of the High One", is the North's most quoted poem: one hundred and sixty-four stanzas of wisdom, warnings, love adventures and magic, preserved in a single manuscript – the Codex Regius, written down in Iceland around 1270. For two hundred years scholars have debated whether the poem is one work or several joined together, where the seams run and what it really wants. Most of that debate is already settled ground, and we are not going to repeat it. This article keeps to what scholarship did not already know: four measurements that are new – one of which went against ourselves.

![Opening of the Codex Regius]({IMG_CR})
The Codex Regius (GKS 2365 4to), written down around 1270 – Hávamál's only medieval source. Everything in this article is measured on that text's normalised edition (Guðni Jónsson). Image: public domain, via [Wikimedia Commons]({PAGE_CR}).

:::box What was already known
That Hávamál is composed of several pieces has been known since the nineteenth century (Müllenhoff; the modern analysis of the layers is John McKinnell's). Dating is also the field of others: most recently Mikael Males (2024), who tests six independent criteria and concludes that the poem most likely took its shape around 900–950. That Christian vocabulary is entirely absent – which our measurement confirms throughout – was one of David Evans's main arguments already in the 1980s, as was the evidence of place in stanza 72: *memorial stones* are unknown in Iceland but belong to pre-Christian Scandinavia. All of this is the starting point here, not a result.
:::

## The voices draw the architecture

That the voices shift through the poem is something every reader has heard – but no one has put numbers on the whole map. We counted first person (*ek*, 'I') and second person (*þú*, 'you') per hundred words, part by part.

:::chart The voices of Hávamál, occurrences per hundred words
# I (ek)
Guest wisdom 1–83 | {svn(V['I']['ek_per100'])}
Counsel on women 84–102 | {svn(V['II']['ek_per100'])}
The Gunnlöð episode 103–110 | {svn(V['III']['ek_per100'])}
Loddfáfnismál 111–137 | {svn(V['IV']['ek_per100'])}
Rúnatal 138–145 | {svn(V['V']['ek_per100'])}
+The spell songs 146–164 | {svn(V['VI']['ek_per100'])}
# you (þú)
Guest wisdom 1–83 | {svn(V['I']['thu_per100'])}
Counsel on women 84–102 | {svn(V['II']['thu_per100'])}
The Gunnlöð episode 103–110 | {svn(V['III']['thu_per100'])}
+Loddfáfnismál 111–137 | {svn(V['IV']['thu_per100'])}
Rúnatal 138–145 | {svn(V['V']['thu_per100'])}
The spell songs 146–164 | {svn(V['VI']['thu_per100'])}
Source: the Codex Regius text in Guðni Jónsson's edition; Vitki's analysis (utdata/Edda in the repository).
:::

The pattern is striking. The great guest wisdom at the poem's opening is nearly voiceless – one *I* or *you* per hundred words; wisdom speaks of man in the third person. Then the I steps in: in the love adventures Odin says *ek* nearly five times per hundred words, in the Gunnlöð episode eight. Loddfáfnismál turns everything into a rain of admonishing *you* – sixteen per hundred words, more than twenty times denser than in the guest wisdom. And in the spell songs the I takes over entirely: *þat kann ek*, 'that I know', seventeen times in nineteen stanzas. The poem moves measurably from **he** (general prudence) through **I** (experience) and **you** (admonition) to **I** again (power). It is a dramaturgy – and it shows in numbers.

## The blind seam search

Are the parts really separate pieces, or is the division something editors laid upon the text? We let a window of ten stanzas slide through the poem and measured how much the function words – the small words an author rarely chooses deliberately – differ before and after each point. The method knows nothing of the scholarly division.

The two strongest style breaks in the whole poem landed at stanzas 111–112 and 138–140: **exactly where Loddfáfnismál and Rúnatal begin** – boundaries drawn by scholars since Müllenhoff's day and central to John McKinnell's modern analysis of the layers. That a blind method finds them again means they are real seams in the language, not editorial convention. Just as telling is where the method does *not* fire: at stanza 84, where McKinnell lets his "Poem of Sexual Intrigue" begin, the function words give no signal at all. That transition is lexically soft – the guest wisdom glides into the love warnings rather than changing dress. It is a new empirical datum in an old debate.

The style measurement as a whole points the same way: stanza blocks within the same part resemble each other (Burrows' Delta 0.69 on average) while blocks from different parts differ clearly more (1.13). And in the cluster tree something beautiful happens: the Gunnlöð episode and Rúnatal – the two places where Odin tells of *his own* defeats and sacrifice – settle closest to each other, though they do not stand together in the poem. This pairing is not found in McKinnell's scheme, where Rúnatal belongs with the spell songs and Gunnlöð with the intrigue poem; we report it as a measurement to be tested, not as a claim about origins. But the thought lies near: the poem's "confessions of Odin" share a style.

![Odin's self-sacrifice, drawn by W.G. Collingwood]({IMG_ODIN})
"I know that I hung on the wind-swept tree nine whole nights" – Rúnatal is the poem's thematically purest part (a single LDA topic dominates {svn(100 * amnesdom['V'], 0)} per cent of its stanzas) and a style sibling of the Gunnlöð episode. Drawing: W.G. Collingwood (1908), public domain, via [Wikimedia Commons]({PAGE_ODIN}).

![Odin and Gunnlöð, drawn by Lorenz Frølich]({IMG_GUNN})
Odin with Gunnlöð, drawn by Lorenz Frølich. The episode is short – eight stanzas – but carries the same style signature as Rúnatal. Image: public domain, via [Wikimedia Commons]({PAGE_GUNN}).

A third trace in the tree: the last stanzas of the guest wisdom, 67–83 – the region around *deyr fé* – drift away from the opening of their own part and settle nearer the counsel on women. Many scholars end the gnomic poem already at stanza 79, and our measurement, which has not read that debate, points to the same region: the end of part one does not quite belong, stylistically, with its beginning.

## The hypothesis that fell: Hávamál does not sound like the runestones

Here is the article's most honest find. Hávamál's most famous stanzas say the same thing as every runestone: *Deyr fé, deyja frændr … en orðstírr deyr aldregi* – cattle die, kinsmen die, but the word-fame never dies. The runestones are precisely that: memorials in stone. So we assumed the impermanence stanzas would also *sound* like the runestones, and measured each stanza's vocabulary against the two hundred most common words on the North's Viking-age runestones – the same corpus that drives the rest of Vitki.

The hypothesis fell. The similarity to the runestones' formula language is uniformly low throughout the poem – the median lies between {svn(100 * min(MB.values()), 0)} and {svn(100 * max(MB.values()), 0)} per cent of a stanza's word types in all six parts – and the *deyr fé* stanzas sit in the middle of the field, not at the top. The poem and the stones share the theology of being remembered, but not its words: the runestone's *ræisti stæin æftiR* and Hávamál's *orðstírr* are two separate language worlds around the same thought. That speaks for two independent traditions – the memorial formula on the stones is not poem quotation, and the poem does not imitate the stones. As far as we know this is the first time the poem has been measured against a whole runic corpus, and the clearest result was a no – which is exactly how measurements should be allowed to end.

Then we split the corpus by country – the poem is after all West Norse, the stones mostly East Norse. A second pattern emerges. Compared on equal amounts of text, the most common words of the Norwegian stones lie closest to the poem ({pN} per cent of a stanza's word types), the Danish next ({pD} per cent) and the Swedish furthest away ({pS} per cent); of three hundred random draws from the Swedish corpus, a single one reaches the Norwegian level. The order follows the geography, west against east. And the words that make the difference are not the memorial formula's but the everyday's: on the Norwegian stones *sá*, *mér*, *konu*, *upp*, *stendr*, on the Danish *munu*, *vel*, *lifa*, *nú*, *lengi* – words that also carry the poem – while the Swedish stones' top list is crowded with names and the raising formula. Norway's runestone corpus is small, only 66 stones, so this is a hint and no proof, and wordier inscriptions in the west may explain part of the difference. But the arrow points in the same direction as the poem's own homeland: where the stones get to speak everyday language they come closer to Hávamál, and the further west they stand, the closer they come.

## Where the poem and the stones meet after all

One meeting remains in the end, and it stands in the poem itself: stanza 72 says that *memorial stones seldom stand by the road unless kinsman raises them for kinsman*. The custom the stanza describes is exactly what our runic corpus consists of – thousands of stones, raised by roads and bridges, by kinsmen for kinsmen. That piece of evidence is Evans's, not ours. But our measurement adds a small weight of its own to the same scale: the language of the stones lies closest to the poem's precisely in the west, where the stanza's memorial stones belong.

:::box How we counted
The text is the Codex Regius text in its normalised edition (Guðni Jónsson), 164 stanzas, about 5,000 words. The voices were counted as *ek* and *þú* forms per hundred words. The seam search compares the distribution of function words in ten stanzas before against ten after every point, with no knowledge of any division. The layer comparison uses Burrows' Delta on the sixty most common words in blocks of at most 22 stanzas, checked against the stylo package's own computation, with LDA topics, type/token ratio and verse boundaries (the edition's punctuation) as support. The runestone comparison counts the share of a stanza's word types found among the two hundred most common words in Rundata's Viking-age runestone normalisations, with word forms merged across the normalisation traditions. The country comparison splits the corpus into Swedish, Danish (DR) and Norwegian (N) stones; since a top list from a small corpus reaches deeper into everyday words, the countries are compared on random samples with equal numbers of running words, three hundred draws per country. All code and result files are open in the repository (utdata/Edda).
:::

:::box The essentials in brief
- A blind search that does not know where scholarship draws its boundaries finds by itself the language seams where Loddfáfnismál and Rúnatal begin – but none at all at stanza 84, where a much-debated part is said to start. That transition is linguistically soft, and that is a new datum in an old debate.
- The Gunnlöð episode and Rúnatal share a style though they do not stand together in the poem – Odin's confessions may be a layer of their own, a pairing that exists in none of scholarship's schemes.
- The poem's most famous thought, that only the word-fame endures, is shared with every runestone – but the language is not: the first measurement ever against a whole runic corpus ended in a no, and the no means that poem and memorial formula are two independent traditions around the same idea.
- Split the runic corpus by country and the stones' everyday language lies closest to the poem in the west and furthest away in the east – a faint but well-aimed echo of the poem's West Norse homeland.
- None of this dates or places the poem: a single manuscript from the 1270s sets the limit of what any method can know, and style difference can stem from genre as well as from hand or time.
:::

## Sources and data

- The state of research: the poem's composite nature has been documented since Müllenhoff in the nineteenth century; the modern analysis of the layers is John McKinnell, "The Making of Hávamál" (Viking and Medieval Scandinavia 3, 2007). Dating: Bjarne Fidjestøl, The Dating of Eddic Poetry (1999); Haukur Þorgeirsson (2012, 2016, 2017); Christopher Sapp (2022); Mikael Males, "The Dating of Hávamál" (Maal og Minne 1-2024). Edition and commentary: David A. H. Evans, Hávamál (Viking Society, 1986). Gnomic style: Carolyne Larrington, A Store of Common Sense (1993). Our contribution is a different one from theirs: the stylometry of the layers, the blind seam search, the voice map and the crossing against the runic corpus.
- Hávamál: Guðni Jónsson's normalised edition of the Codex Regius text (Eddukvæði, Sæmundar-Edda), via heimskringla.no.
- The Scandinavian Runic Text Database (Rundata), Uppsala University, for the runestone comparison.
- Analysis code and results: utdata/Edda in Vitki's repository (the R packages stylo, topicmodels, tidytext, quanteda, factoextra).
- Images: Wikimedia Commons, public domain, with credits in the captions.

*Stylometry itself dates and places nothing – a single manuscript from the 1270s sets that limit. But it can measure seams, voices and word worlds, and leave the figures open for runologists and philologists to test.*"""

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
                      "article keeps to what no one has shown before. A blind seam search finds two of the poem's "
                      "boundaries on its own but declares a third one soft, two of Odin's confessions turn out to "
                      "share a style though they do not stand together, and for the first time the poem is "
                      "measured against the North's collected runestones. There our own hypothesis fell – and "
                      "was replaced by a trail pointing west, towards the poem's homeland."),
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
