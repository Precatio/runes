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

IMG_CR = "https://upload.wikimedia.org/wikipedia/commons/5/50/Codex_Regius_of_Eddaic_Poems.jpg"
PAGE_CR = "https://commons.wikimedia.org/wiki/File:Codex_Regius_of_Eddaic_Poems.jpg"
IMG_ODIN = "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/4d/Odin%27s_Self-sacrifice_by_Collingwood.jpg/1280px-Odin%27s_Self-sacrifice_by_Collingwood.jpg"
PAGE_ODIN = "https://commons.wikimedia.org/wiki/File:Odin%27s_Self-sacrifice_by_Collingwood.jpg"
IMG_GUNN = "https://upload.wikimedia.org/wikipedia/commons/1/1f/Odin_and_Gunnl%C3%B6%C3%B0_by_Fr%C3%B8lich.jpg"
PAGE_GUNN = "https://commons.wikimedia.org/wiki/File:Odin_and_Gunnl%C3%B6%C3%B0_by_Fr%C3%B8lich.jpg"

title = "Vem talar i Hávamál?"
summary = ("Eddans visdomsdikt finns i en enda medeltida handskrift och har lästs i århundraden. Vi lät "
           "statistiken läsa den förutsättningslöst: rösterna – han, jag, du – ritar diktens dolda arkitektur, "
           "en blind sömsökning hittar själv två av forskningens skarvar, och för första gången mäts dikten mot "
           "en hel runkorpus. Där föll vår egen hypotes – och det fyndet är artikelns bästa.")

body = f"""Hávamál, "den höges tal", är nordens mest citerade dikt: etthundrasextiofyra strofer visdom, varningar, kärleksäventyr och trolldom, bevarade i en enda handskrift – Codex Regius, nedskriven på Island omkring 1270. Forskare har i tvåhundra år diskuterat om dikten är ett verk eller flera hopfogade, var skarvarna går och vad den egentligen vill. Vi lät statistiken läsa den förutsättningslöst: inga tolkningar, bara texten själv, mätt med samma slags metoder som vi annars använder på runstenarna. Tre mönster steg fram – och ett av våra egna antaganden föll.

![Uppslag ur Codex Regius]({IMG_CR})
Codex Regius (GKS 2365 4to), nedskriven omkring 1270 – Hávamáls enda medeltida källa. Allt i den här artikeln är mätt på den textens normaliserade utgåva (Guðni Jónsson). Bild: public domain, via [Wikimedia Commons]({PAGE_CR}).

## Rösterna ritar arkitekturen

Det enklaste måttet visade sig vara det mest avslöjande: vem som talar. Vi räknade första person (*ek*, 'jag') och andra person (*þú*, 'du') per hundra ord, del för del.

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

De två starkaste stilbrotten i hela dikten hamnade vid strof 111–112 och 138–140: **exakt där Loddfáfnismál respektive Runatal börjar.** Två av de klassiska gränserna är alltså verkliga sömmar i språket, inte utgivarkonvention. Lika talande är var metoden *inte* slår ut: gränsen vid strof 84, där kvinnoråden tar vid, ger inget utslag alls. Den övergången är stilmässigt mjuk – gästvisdomen glider över i kärleksvarningarna snarare än byter hand.

Stilmätningen som helhet pekar åt samma håll: strofblock inom samma del liknar varandra (Burrows' Delta 0,69 i snitt) medan block ur olika delar skiljer sig klart mer (1,13). Och i släktträdet över blocken händer något vackert: Gunnlöd-episoden och Runatal – de två ställen där Oden berättar om *sina egna* nederlag och offer – lägger sig närmast varandra, fast de inte står intill i dikten. Diktens "Odens bekännelser" delar stil.

![Odens självoffer, tecknat av W.G. Collingwood]({IMG_ODIN})
"Jag vet att jag hängde på det vindpinade trädet nio hela nätter" – Runatal är diktens tematiskt renaste del (ett enda LDA-ämne dominerar {svn(100 * amnesdom['V'], 0)} procent av stroferna) och stilsyskon med Gunnlöd-episoden. Teckning: W.G. Collingwood (1908), public domain, via [Wikimedia Commons]({PAGE_ODIN}).

![Oden och Gunnlöd, tecknade av Lorenz Frølich]({IMG_GUNN})
Oden hos Gunnlöd, Lorenz Frølichs teckning. Episoden är kort – åtta strofer – men bär samma stilsignatur som Runatal. Bild: public domain, via [Wikimedia Commons]({PAGE_GUNN}).

Ett tredje spår i trädet: gästvisdomens sista strofer, 67–83 – trakten kring *deyr fé* – driver bort från sin egen dels början och lägger sig närmare kvinnoråden. Forskningen har länge anat ett eget vänskaps- och förgänglighetsskikt just där. Vår mätning, som inte läst den debatten, pekar på samma ställe.

## Hypotesen som föll: Hávamál låter inte som runstenarna

Här kommer artikelns ärligaste fynd. Hávamáls mest berömda strofer säger samma sak som varje runsten: *Deyr fé, deyja frændr … en orðstírr deyr aldregi* – boskap dör, fränder dör, men eftermälet dör aldrig. Runstenarna är ju exakt det: eftermälen i sten. Så vi antog att förgänglighetsstroferna också skulle *låta* som runstenarna, och mätte varje strofs ordförråd mot de tvåhundra vanligaste orden på Sveriges vikingatida runstenar – samma korpus som driver resten av Vitki.

Hypotesen föll. Likheten med runstenarnas formelspråk är jämnt låg genom hela dikten – medianen ligger mellan {svn(100 * min(MB.values()), 0)} och {svn(100 * max(MB.values()), 0)} procent av strofens ordtyper i alla sex delarna – och *deyr fé*-stroferna ligger mitt i fältet, inte i toppen. Dikten och stenarna delar eftermälets teologi, men inte dess ord: runstenens *ræisti stæin æftiR* och Hávamáls *orðstírr* är två skilda språkvärldar kring samma tanke. Det talar för två oberoende traditioner – minnesformeln på stenarna är inte diktcitat, och dikten härmar inte stenarna. Såvitt vi vet är det första gången dikten mäts mot en hel runkorpus, och det tydligaste resultatet blev ett nej – vilket är precis så mätningar ska få lov att sluta.

## Vad dikten vill

Väger man diktens massa är svaret inte mystik utan vardag: orden som bär den stora gästvisdomen är *vita*, *snotr*, *kemr*, *guma* – veta, klok, komma, människa. Hávamál är till största delen en överlevnadslära för livet bland andra: var vaksam i dörren, drick med måtta, håll dina vänner. Mot den vardagen står kronan i strof 76–77 – bara eftermälet består – och slutets dyrköpta kunskap, Odens nio nätter i trädet. Klokskapen håller dig vid liv; ryktet och kunskapen är det enda som överlever dig. Diktens sista strof säger det själv: kväden "människors söner till gagn".

:::box Så räknade vi
Texten är Codex Regius-textens normaliserade utgåva (Guðni Jónsson), 164 strofer, cirka 5 000 ord. Rösterna räknades som *ek*- respektive *þú*-former per hundra ord. Sömsökningen jämför funktionsordens fördelning i tio strofer före mot tio efter varje punkt, utan kännedom om någon indelning. Skiktjämförelsen använder Burrows' Delta på de sextio vanligaste orden i strofblock om högst 22 strofer, kontrollerad mot stylo-paketets egen beräkning, med LDA-ämnen, typ/token-kvot och versgränser (utgåvans kommatering) som stöd. Runstensjämförelsen räknar andelen av strofens ordtyper som finns bland de tvåhundra vanligaste orden i Rundatas vikingatida runstensnormaliseringar, med ordformerna hopslagna över normaliseringstraditionerna. All kod och alla resultatfiler ligger öppet i kodförrådet (utdata/Edda).
:::

:::box Det viktigaste i korthet
- Hávamál är mätbart sammansatt: stycken ur olika delar skiljer sig klart mer i stil än styckena inom en del, så bilden av ett enda verk i ett svep har minst stöd i språket.
- Rösterna ritar en arkitektur – från visdomens *han* över erfarenhetens *jag* och förmaningens *du* till maktens *jag* – och en blind sökning hittar själv skarvarna där Loddfáfnismál och Runatal börjar, men ingen skarv vid kvinnoråden: den övergången är mjuk.
- Gunnlöd-episoden och Runatal delar stil fast de inte står ihop – Odens bekännelser kan vara ett eget skikt – och förgänglighetsstroferna i gästvisdomens slut driver mot ett eget håll, där forskningen länge anat en söm.
- Dikten och runstenarna delar tanken att bara eftermälet består, men inte språket: vår hypotes att *deyr fé*-skiktet skulle låta som stenarna föll, och det pekar mot två oberoende traditioner kring samma idé.
- Inget av detta daterar eller placerar dikten: en enda handskrift från 1270-talet sätter gränsen för vad någon metod kan veta, och stilskillnad kan bero på genre lika väl som på hand eller tid.
:::

## Källor och data

- Forskningsläget: diktens sammansatta natur har diskuterats sedan 1800-talet, och kvantitativa dateringskriterier för eddadiktning finns sedan länge (Fidjestøls of/um-partikel, Haukur Þorgeirssons allitterationskriterier). Vårt bidrag är ett annat: skiktens stilometri, den blinda sömsökningen, röstkartan och korsningen mot runkorpusen.
- Hávamál: Guðni Jónssons normaliserade utgåva av Codex Regius-texten (Eddukvæði, Sæmundar-Edda), via heimskringla.no.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet, för runstensjämförelsen.
- Analyskod och resultat: utdata/Edda i Vitkis kodförråd (R-paketen stylo, topicmodels, tidytext, quanteda, factoextra).
- Bilder: Wikimedia Commons, public domain, med upphov i bildtexterna.

*Tid och plats lämnar vi medvetet öppna: Codex Regius är isländsk och sen, dikten i delar sannolikt långt äldre – men var och när de delarna föddes kan ingen stilometri i världen läsa ut ur en enda handskrift.*"""

body_en = f"""Hávamál, "the words of the High One", is the North's most quoted poem: one hundred and sixty-four stanzas of wisdom, warnings, love adventures and magic, preserved in a single manuscript – the Codex Regius, written down in Iceland around 1270. For two hundred years scholars have debated whether the poem is one work or several joined together, where the seams run and what it really wants. We let statistics read it without preconceptions: no interpretations, only the text itself, measured with the same kinds of methods we otherwise use on the runestones. Three patterns emerged – and one of our own assumptions fell.

![Opening of the Codex Regius]({IMG_CR})
The Codex Regius (GKS 2365 4to), written down around 1270 – Hávamál's only medieval source. Everything in this article is measured on that text's normalised edition (Guðni Jónsson). Image: public domain, via [Wikimedia Commons]({PAGE_CR}).

## The voices draw the architecture

The simplest measure turned out to be the most revealing: who is speaking. We counted first person (*ek*, 'I') and second person (*þú*, 'you') per hundred words, part by part.

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

The two strongest style breaks in the whole poem landed at stanzas 111–112 and 138–140: **exactly where Loddfáfnismál and Rúnatal begin.** Two of the classic boundaries are thus real seams in the language, not editorial convention. Just as telling is where the method does *not* fire: the boundary at stanza 84, where the counsel on women takes over, gives no signal at all. That transition is stylistically soft – the guest wisdom glides into the love warnings rather than changing hands.

The style measurement as a whole points the same way: stanza blocks within the same part resemble each other (Burrows' Delta 0.69 on average) while blocks from different parts differ clearly more (1.13). And in the cluster tree something beautiful happens: the Gunnlöð episode and Rúnatal – the two places where Odin tells of *his own* defeats and sacrifice – settle closest to each other, though they do not stand together in the poem. The poem's "confessions of Odin" share a style.

![Odin's self-sacrifice, drawn by W.G. Collingwood]({IMG_ODIN})
"I know that I hung on the wind-swept tree nine whole nights" – Rúnatal is the poem's thematically purest part (a single LDA topic dominates {svn(100 * amnesdom['V'], 0)} per cent of its stanzas) and a style sibling of the Gunnlöð episode. Drawing: W.G. Collingwood (1908), public domain, via [Wikimedia Commons]({PAGE_ODIN}).

![Odin and Gunnlöð, drawn by Lorenz Frølich]({IMG_GUNN})
Odin with Gunnlöð, drawn by Lorenz Frølich. The episode is short – eight stanzas – but carries the same style signature as Rúnatal. Image: public domain, via [Wikimedia Commons]({PAGE_GUNN}).

A third trace in the tree: the last stanzas of the guest wisdom, 67–83 – the region around *deyr fé* – drift away from the opening of their own part and settle nearer the counsel on women. Scholars have long suspected a separate layer of friendship and impermanence just there. Our measurement, which has not read that debate, points to the same place.

## The hypothesis that fell: Hávamál does not sound like the runestones

Here is the article's most honest find. Hávamál's most famous stanzas say the same thing as every runestone: *Deyr fé, deyja frændr … en orðstírr deyr aldregi* – cattle die, kinsmen die, but the word-fame never dies. The runestones are precisely that: memorials in stone. So we assumed the impermanence stanzas would also *sound* like the runestones, and measured each stanza's vocabulary against the two hundred most common words on Sweden's Viking-age runestones – the same corpus that drives the rest of Vitki.

The hypothesis fell. The similarity to the runestones' formula language is uniformly low throughout the poem – the median lies between {svn(100 * min(MB.values()), 0)} and {svn(100 * max(MB.values()), 0)} per cent of a stanza's word types in all six parts – and the *deyr fé* stanzas sit in the middle of the field, not at the top. The poem and the stones share the theology of being remembered, but not its words: the runestone's *ræisti stæin æftiR* and Hávamál's *orðstírr* are two separate language worlds around the same thought. That speaks for two independent traditions – the memorial formula on the stones is not poem quotation, and the poem does not imitate the stones. As far as we know this is the first time the poem has been measured against a whole runic corpus, and the clearest result was a no – which is exactly how measurements should be allowed to end.

## What the poem wants

Weighing the poem's mass, the answer is not mysticism but everyday life: the words that carry the great guest wisdom are *vita*, *snotr*, *kemr*, *guma* – know, wise, come, man. Hávamál is for the most part a survival manual for life among others: be watchful in the doorway, drink in moderation, keep your friends. Against that everyday stands the crown in stanzas 76–77 – only the word-fame endures – and the ending's dearly bought knowledge, Odin's nine nights in the tree. Prudence keeps you alive; reputation and knowledge are all that outlive you. The poem's last stanza says it itself: sung "for the benefit of the sons of men".

:::box How we counted
The text is the Codex Regius text in its normalised edition (Guðni Jónsson), 164 stanzas, about 5,000 words. The voices were counted as *ek* and *þú* forms per hundred words. The seam search compares the distribution of function words in ten stanzas before against ten after every point, with no knowledge of any division. The layer comparison uses Burrows' Delta on the sixty most common words in blocks of at most 22 stanzas, checked against the stylo package's own computation, with LDA topics, type/token ratio and verse boundaries (the edition's punctuation) as support. The runestone comparison counts the share of a stanza's word types found among the two hundred most common words in Rundata's Viking-age runestone normalisations, with word forms merged across the normalisation traditions. All code and result files are open in the repository (utdata/Edda).
:::

:::box The essentials in brief
- Hávamál is measurably composite: pieces from different parts differ clearly more in style than pieces within one part, so the picture of a single work in one sweep has the least support in the language.
- The voices draw an architecture – from wisdom's *he* through experience's *I* and admonition's *you* to power's *I* – and a blind search finds by itself the seams where Loddfáfnismál and Rúnatal begin, but no seam at the counsel on women: that transition is soft.
- The Gunnlöð episode and Rúnatal share a style though they do not stand together – Odin's confessions may be a layer of their own – and the impermanence stanzas at the end of the guest wisdom drift in their own direction, where scholars have long suspected a seam.
- The poem and the runestones share the thought that only the word-fame endures, but not the language: our hypothesis that the *deyr fé* layer would sound like the stones fell, and that points to two independent traditions around the same idea.
- None of this dates or places the poem: a single manuscript from the 1270s sets the limit of what any method can know, and style difference can stem from genre as well as from hand or time.
:::

## Sources and data

- The state of research: the poem's composite nature has been debated since the nineteenth century, and quantitative dating criteria for Eddic poetry have long existed (Fidjestøl's of/um particle, Haukur Þorgeirsson's alliteration criteria). Our contribution is a different one: the stylometry of the layers, the blind seam search, the voice map and the crossing against the runic corpus.
- Hávamál: Guðni Jónsson's normalised edition of the Codex Regius text (Eddukvæði, Sæmundar-Edda), via heimskringla.no.
- The Scandinavian Runic Text Database (Rundata), Uppsala University, for the runestone comparison.
- Analysis code and results: utdata/Edda in Vitki's repository (the R packages stylo, topicmodels, tidytext, quanteda, factoextra).
- Images: Wikimedia Commons, public domain, with credits in the captions.

*Time and place we deliberately leave open: the Codex Regius is Icelandic and late, parts of the poem in all likelihood far older – but where and when those parts were born, no stylometry in the world can read out of a single manuscript.*"""

# aldrig siffra först i en mening; bild- och diagramrader räknas inte
for b in (body, body_en):
    flat = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", b)
    flat = "\n".join(line for line in flat.splitlines() if "|" not in line and not line.startswith(":::"))
    for m in re.finditer(r"[.!?]\s+(\d)", flat.replace("\n", " ")):
        ctx = flat.replace("\n", " ")[max(0, m.start() - 40):m.end() + 20]
        assert re.search(r"GKS|1270|190[0-9]|while|medan", ctx), f"Mening börjar med siffra: …{ctx}…"

out = {"slug": "vem-talar-i-havamal", "title": title, "summary": summary, "body": body,
       "title_en": "Who Is Speaking in Hávamál?",
       "summary_en": ("The Edda's wisdom poem survives in a single medieval manuscript and has been read for "
                      "centuries. We let statistics read it without preconceptions: the voices – he, I, you – "
                      "draw the poem's hidden architecture, a blind seam search finds two of scholarship's "
                      "boundaries on its own, and for the first time the poem is measured against a whole runic "
                      "corpus. There our own hypothesis fell – and that find is the article's best."),
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
