"""Artikeln "Var tog alverna vägen?" – del 2 i serien Nordiska väsen under vikingatiden.

Bygger på den låsta studien analysplaner/2026-11-21-alverna.md (5d305b6) + tillägg 1 (1b50c3d); siffrorna läses ur
utdata/alverna/matt.json och varje citat kontrolleras mot texten i korpusen.
    ../../../.venv/bin/python build_alverna.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

SLUG = "var-tog-alverna-vagen"
PLAN = "https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-21-alverna.md"
RES = "https://github.com/Precatio/runes/blob/main/utdata/alverna/resultat.md"
M = json.load(open(os.path.join(ROOT, "utdata", "alverna", "matt.json"), encoding="utf-8"))

# ======================================================================================================================
# 1. Siffrorna
# ======================================================================================================================
EL = {c: v["väsen"] + v["Völundr"] for c, v in M["A1"].items()}
N_EL = sum(EL.values())
assert N_EL == 64
GROUPS = {"eddadikter": ("Eddadikterna", "The Eddic poems", ["eddadikter"]),
          "snorre": ("Snorres Edda", "Snorri's Edda", ["snorra_edda_gylfaginning", "snorra_edda_skáldskaparmál"]),
          "fornaldar": ("Fornaldarsagorna", "The legendary sagas", ["fornaldarsagor", "fornaldarsagor_vers"]),
          "islanninga": ("Islänningasagorna", "The sagas of Icelanders", ["islanningasagor", "islanningasagor_vers"]),
          "hk": ("Heimskringla", "Heimskringla", ["heimskringla", "heimskringla_vers"]),
          "samtid": ("Samtidssagorna", "The contemporary sagas", ["samtidssagor", "samtidssagor_vers"])}
GN = {k: sum(EL[c] for c in cs) for k, (_, _, cs) in GROUPS.items()}
assert GN == {"eddadikter": 31, "snorre": 13, "fornaldar": 15, "islanninga": 3, "hk": 2, "samtid": 0}
IS_PROSE = EL["islanningasagor"]
assert IS_PROSE == 2
WORDS_IS = round(1e4 * IS_PROSE / M["A2_per_10000"]["islanningasagor"]) if M["A2_per_10000"]["islanningasagor"] else None

T1 = M["T1"]["huvud"]
assert T1["T1a_gudar"]["håller"] and not T1["T1b_vidunder"]["håller"]
assert T1["T1a_gudar"]["sagorna_%"] == 0.0 and T1["T1a_gudar"]["Eddan_%"] == 68.2
assert M["T1"]["utan_Alvíssmál"]["T1a_gudar"]["håller"] and M["T1"]["fönster_10"]["T1a_gudar"]["håller"]
U = T1["underlag"]
assert (U["Eddan_träffar"], U["sagorna_träffar"], U["sagorna_texter"]) == (44, 20, 12)
R5 = M["A5_runstenar"]
assert (R5["alf_stenar"], R5["tor_stenar"], R5["as_stenar"], R5["stenar"]) == (7, 335, 168, 2321)
assert "Hs 10" in R5["alf_signa"]
A6 = M["A6"]["läsning"]
assert A6["alvnamn_enligt_SOL"] == 0 and A6["träffar"] == 6
assert len(M["A3_kult"]) == 3 and len(M["A4_ljus_dokk"]) == 8
NAMES_SAGAS = M["A5_sagor_namn_antal"]
assert M["träffar"] == 443
assert NAMES_SAGAS == 314
CTRL = json.load(open(os.path.join(ROOT, "utdata", "alverna", "kontroll_resultat.json"), encoding="utf-8"))
assert CTRL["lika"] == 40


def pc(a, b):
    return round(100 * a / b)


# ======================================================================================================================
# 2. Citaten (kontrolleras mot korpusen)
# ======================================================================================================================
K = os.path.join(ROOT, "utdata", "varlden", "korpus")
EDDA = json.load(open(os.path.join(ROOT, "utdata", "Malt", "kallor", "edda.json"), encoding="utf-8"))


def flat(t):
    return " ".join(t.split())


def src(path):
    return flat(open(os.path.join(K, path), encoding="utf-8").read())


Q = {
    "sigvat": ("heimskringla/Saga_Ólafs_hins_helga.txt", "stóð þar húsfreyja í durum, ok bað hann eigi þar inn koma, segir, at þau œtti álfa blót"),
    "sigvat_vers": ("heimskringla/Saga_Ólafs_hins_helga.txt", "Gakkat þú inu, kvað ekkja, armi drengr! en lengra; hræðumk ek við Óðins, erum heiðnir vér, reiði."),
    "kormak_hol": ("islendingasogur/kormaks_saga.is.txt", "Hóll einn er héðan skammt í brott er álfar búa í"),
    "kormak": ("islendingasogur/kormaks_saga.is.txt", "gera álfum veislu af slátrinu og mun þér batna"),
    "alfkona": ("fornaldarsogur/Hrólfs_saga_kraka_ok_kappa_hans.txt", "Þetta hafði verit ein álfkona"),
    "sogubrot": ("fornaldarsogur/Sögubrot_af_nokkurum_fornkonungum_í_Dana-_ok_Svíaveldi.txt",
                 "um þat fólk, er Álfar hétu, at þat var miklu fríðara en engi önnur mannkind á Norðrlöndum"),
}
EQ = {
    "thrym": ("Þrymskviða", "Hvat er með ásum? Hvat er með alfum?"),
    "loki": ("Þrymskviða", "Illt er með ásum, illt er með alfum"),
    "lokasenna": ("Lokasenna", "ása ok alfa, er hér inni eru"),
    "ljos": ("Gylfaginning", "Ljósálfar eru fegri en sól sýnum, en Dökkálfar eru svartari en bik"),
    "ljodi": ("Völundarkviða", "alfa ljóði"),
    "visi": ("Völundarkviða", "vísi alfa"),
}
for k, (p, q) in Q.items():
    assert q in src(p), k
for k, (poem, q) in EQ.items():
    assert q in flat(EDDA[poem]), k


def q(k):
    return Q[k][1] if k in Q else EQ[k][1]


# Alvíssmál: vad alverna kallar saker (orden kontrolleras: "alfar <ord>" i dikten)
ALVISS = [("jorden", "the earth", "gróandi", "den grönskande", "the greening one"),
          ("himlen", "the sky", "fagraræfr", "det vackra taket", "the fair roof"),
          ("månen", "the moon", "ártala", "årsräknaren", "the year-counter"),
          ("solen", "the sun", "fagrahvél", "det vackra hjulet", "the fair wheel"),
          ("molnen", "the clouds", "veðrmegin", "vädermakten", "the weather-might"),
          ("vinden", "the wind", "dynfara", "dånfararen", "the din-farer"),
          ("vindstillan", "the calm", "dagsefa", "dagsvilan", "the day's rest"),
          ("havet", "the sea", "lagastaf", "vattenstaven", "the water-stave"),
          ("skogen", "the forest", "fagrlima", "den vackergrenade", "the fair-limbed"),
          ("natten", "the night", "svefngaman", "sömnglädjen", "the joy of sleep")]
AV = flat(EDDA["Alvíssmál"])
for _, _, w, _, _ in ALVISS:
    assert re.search(r"\balfar " + w + r"\b", AV), w

# ======================================================================================================================
# 3. Bilderna (Wikimedia Commons; licenser kontrollerade 2026-11-21)
# ======================================================================================================================
ALVOR = ("https://upload.wikimedia.org/wikipedia/commons/9/97/%C3%84ngs%C3%A4lvor_-_Nils_Blomm%C3%A9r_1850.jpg",
         "https://commons.wikimedia.org/wiki/File:%C3%84ngs%C3%A4lvor_-_Nils_Blomm%C3%A9r_1850.jpg", "Nils Blommér", "public domain")
ARDRE = ("https://upload.wikimedia.org/wikipedia/commons/5/5e/V%C3%B6lund_on_ardre_01.png",
         "https://commons.wikimedia.org/wiki/File:V%C3%B6lund_on_ardre_01.png", "public domain")
U573 = ("https://upload.wikimedia.org/wikipedia/commons/f/f3/Upplands_runinskrifter_573.png",
        "https://commons.wikimedia.org/wiki/File:Upplands_runinskrifter_573.png", "Upplands runinskrifter (1943)", "CC0")


# ======================================================================================================================
# 4. Diagrammen (procent)
# ======================================================================================================================
def chart_where(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Var alverna står: andel av alla alver i texterna' if sv else 'Where the elves stand: share of all elves in the texts'}"]
    for k, (lsv, len_, _) in GROUPS.items():
        hl = "+" if k in ("eddadikter", "snorre") else ""
        rows.append(f"{hl}{lsv if sv else len_} | {pc(GN[k], N_EL)} | {GN[k]} {'av' if sv else 'of'} {N_EL}")
    rows.append("Alven som väsen (också i sammansättningar som alvkvinna och alvablot), inte personnamn eller ortnamn. Diagram: Vitki, efter Vitkis handklassning av alla träffar."
                if sv else "The elf as a being (also in compounds such as elf-woman and elf-sacrifice), not personal or place names. Chart: Vitki, from Vitki's hand classification of all hits.")
    return "\n".join(rows) + "\n:::"


def chart_company(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Alvernas sällskap: andel av alverna med ett ord av slaget inom 25 ord' if sv else 'The company of the elves: share of the elves with a word of the kind within 25 words'}"]
    for key, lsv, len_ in (("T1a_gudar", "gudarna (asar, vaner, gudar)", "the gods (æsir, vanir, gods)"),
                           ("T1b_vidunder", "jättar, troll och onda väsen", "giants, trolls and evil beings"),
                           ("dvärgar", "dvärgarna", "the dwarves")):
        rows.append(f"# {lsv if sv else len_}")
        rows.append(f"{'+' if key == 'T1a_gudar' else ''}{'Eddan' if sv else 'The Edda'} | {round(T1[key]['Eddan_%'])} | ")
        rows.append(f"{'Sagorna' if sv else 'The sagas'} | {round(T1[key]['sagorna_%'])} | ")
    rows.append(f"Eddan = eddadikterna och Snorres Edda ({U['Eddan_träffar']} alver), sagorna = alla sagor ({U['sagorna_träffar']} alver). Diagram: Vitki."
                if sv else f"The Edda = the Eddic poems and Snorri's Edda ({U['Eddan_träffar']} elves), the sagas = all sagas ({U['sagorna_träffar']} elves). Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


def chart_names(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Andel svenska runstenar med ett namn som börjar på …' if sv else 'Share of Swedish runestones with a name beginning in …'}"]
    rows.append(f"Tor- (Þór-, Þur-) | {R5['tor_andel']} | {R5['tor_stenar']} {'stenar' if sv else 'stones'}")
    rows.append(f"As- (Ás-) | {R5['as_andel']} | {R5['as_stenar']} {'stenar' if sv else 'stones'}")
    rows.append(f"+Alf- (Alf-, Álf-) | {R5['alf_andel']} | {R5['alf_stenar']} {'stenar' if sv else 'stones'}")
    rows.append(f"Källa: {R5['stenar']:,} svenska runstenar från vikingatiden, Samnordisk runtextdatabas. Diagram: Vitki.".replace(",", " ")
                if sv else f"Source: {R5['stenar']:,} Swedish Viking-age runestones, Scandinavian Runic-text Database. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


def alviss_box(lang):
    sv = lang == "sv"
    rows = [":::box " + ("Alvernas ord, enligt Alvíssmál" if sv else "The elves' words, according to Alvíssmál")]
    for s, e, w, gs, ge in ALVISS:
        rows.append(f"- {s.capitalize() if sv else e.capitalize()}: *{w}* – {gs if sv else ge}")
    rows.append("" if sv else "")
    rows.append("Översättningarna är våra och så ordagranna vi kan göra dem." if sv else "The translations are ours, as literal as we can make them.")
    return "\n".join(r for r in rows if r != "") + "\n:::"


# ======================================================================================================================
# 5. Texten
# ======================================================================================================================
title = "Var tog alverna vägen? Gudarnas grannar i Eddan, nästan borta i sagorna"
summary = (f"Vi läste varje alv i den fornnordiska litteraturen, {N_EL} stycken. I Eddan står alverna nästan alltid bredvid gudarna. "
           "I sagorna står de aldrig där – och i Sverige finns de varken i ortnamnen eller på runstenarna, utom i sju namn.")

body = f"""En kväll för nästan tusen år sedan vandrar en isländsk skald genom Götaland. Han heter Sigvat, han är ute i kung Olav Haraldssons ärenden, och han behöver tak över huvudet. På den första gården är dörren stängd. På nästa står husfrun i dörröppningen:

> {q('sigvat')}

”… där stod husfrun i dörren och bad honom inte komma in, och sade att de höll alvablot.”

Sigvat gjorde en dikt av det, och den finns kvar:

> {q('sigvat_vers')}

”Gå inte längre in, sade kvinnan, du stackars karl; jag fruktar Odens vrede, vi är hedningar.”

Det är en av mycket få gånger som en alv – eller ett offer till alverna – syns i en text om verkliga människor i Sverige. Den här artikeln är den andra i serien om de nordiska väsendena. [Den första]({'/artiklar/var-bodde-trollen'}) räknade alla väsen på en gång. Nu tar vi ett i taget, och börjar med alverna: var de står i texterna, vem de står bredvid, och var de saknas.

## Ett folk vid gudarnas sida

I Eddan är alverna inte småfolk i ängen. De är ett av världens folk, och de nämns nästan alltid i samma andetag som gudarna. När jätten Trym vill veta hur det står till i världen frågar han Loke:

> {q('thrym')}

”Hur är det hos asarna? Hur är det hos alverna?” Och Loke svarar: *{q('loki')}* – ”illa är det hos asarna, illa hos alverna.” I Lokasenna smädar Loke de församlade gudarna, och han gör det inför *{q('lokasenna')}* – ”asar och alver som är här inne”.

Vi mätte detta. För varje alv räknade vi om det fanns ett ord för gudarna – asar, vaner, gudar – inom 25 ord åt något håll. I Eddan gällde det **{round(T1['T1a_gudar']['Eddan_%'])} procent** av alverna. I sagorna gällde det **ingen enda** av de {U['sagorna_träffar']}. Skillnaden är så stor att den skulle uppstå av en slump i färre än ett fall på tiotusen, och den finns kvar när vi tar bort dikten som har flest alver, och när vi gör fönstret smalare.

{chart_company('sv')}

Vi hade också en gissning åt andra hållet: att alverna i sagorna skulle ha flyttat över till trollens sida. Den höll inte. Jättar och onda väsen står inte säkert oftare nära alverna i sagorna än i Eddan. Alverna i sagorna har tappat sina gudar, men de har inte fått några monster i stället.

{alviss_box('sv')}

Dikten Alvíssmál är en ordlista över världens folk. Dvärgen Alvis svarar Tor på vad allting heter hos människor, gudar, jättar, dvärgar – och alver. Alvernas ord är ofta ljusa: det vackra taket, det vackra hjulet, sömnglädjen. Det är också dikten med flest alver, och det är därför vi prövade resultatet utan den.

## Ljusa och mörka – bara hos Snorre

Den mest berömda beskrivningen av alverna kommer från Snorre Sturlasson:

> {q('ljos')}

”Ljusalverna är fagrare än solen att se, men dökkalverna är svartare än beck.”

Den uppdelningen finns **bara hos Snorre**. Inte en enda annan text i vårt material talar om ljusalver eller dökkalver. När Snorre själv återkommer till de mörka alverna, *svartálfar*, är det de som smider Sifs hår av guld, och i deras land, Svartalfheim, bor dvärgen Andvari. Hos Snorre glider de mörka alverna och dvärgarna ihop.

## Völund, alvernas furste

Den ende i Eddan som kallas alvernas furste är smeden Völund, och han har en egen dikt. Han kallas *{q('ljodi')}* och *{q('visi')}* – ungefär ”alvernas furste” och ”alvernas ledare”. Kung Nidud tar honom till fånga, lamslår honom och sätter honom att smida. Völund hämnas genom att döda kungens söner, och sedan lyfter han i luften och är borta.

![Völund på Ardrestenen VIII, Gotland]({ARDRE[0]})
Völunds smedja på bildstenen Ardre VIII från Gotland: kungadottern till vänster, smedjan i mitten och Völund som flyger bort i fågelskepnad. Bild: {ARDRE[2]}, via [Wikimedia Commons]({ARDRE[1]}).

Völund syns också på en gotländsk bildsten. Ingen runsten i Sverige skriver ut ordet *alv*, men berättelsen om alvernas furste fanns i Sverige i bild.

## Kullen, blotet och alvkvinnan

Utanför Eddan finns alverna nästan bara i fornaldarsagorna, sagorna om tiden före Islands bosättning: {GN['fornaldar']} av de {N_EL} alverna. Där har de flyttat ned till människorna. Kung Helge i Hrólfs saga kraka får en dotter med en kvinna som kommer en natt och försvinner, och berättaren konstaterar: *{q('alfkona')}* – ”det hade varit en alvkvinna.” I en annan berättelse har alverna blivit ett mänskligt folk i landet Alfheim, och de sägs vara *{q('sogubrot')}* – ”ett folk som hette alver, som var mycket vackrare än något annat folk i Norden”.

I islänningasagornas prosa finns alverna två gånger på närmare en miljon ord, båda i Kormáks saga. En sårad man får höra att det finns *{q('kormak_hol')}* – ”en kulle här nära där alver bor” – och att han ska *{q('kormak')}*: ”hålla gästabud för alverna med köttet, så blir du bättre.” Det och Sigvats stängda dörr i Götaland är **de enda gångerna i hela materialet som människor ger alverna något**.

{chart_where('sv')}

## Där alverna saknas

![Ängsälvor av Nils Blommér, 1850]({ALVOR[0]})
Älvorna på ängen, som 1800-talet såg dem: Nils Blommérs målning från 1850. Det är folksagans älvor, inte Eddans. Målning: {ALVOR[2]}, {ALVOR[3]}, via [Wikimedia Commons]({ALVOR[1]}).

I Sverige är det svårt att hitta alverna alls. Vi letade på tre ställen.

**I ortnamnen.** Svenskt ortnamnslexikon nämner ordet *alv* i {A6['träffar']} förklaringar, men **inte en enda gång tolkas ett ortnamn som ett alvnamn**. Alva på Gotland och Alvaret på Öland har fått sina namn av *alv*, jordlagret närmast under matjorden. Till och med Alvhem i Västergötland innehåller enligt lexikonet ”möjligen” samma jordlager.

**I namnen.** I sagorna är namn som Álfr, Álfhildr och Álfgeirr vanliga, {NAMES_SAGAS} gånger. På de svenska runstenarna finns sådana namn på bara **{R5['alf_stenar']} av {R5['stenar']:,} stenar**, och en av dem är osäkert läst. Tor-namnen finns på {R5['tor_stenar']} stenar.

{chart_names('sv')}

![U 573 vid Kragsta]({U573[0]})
U 573 vid Kragsta i Lohärads socken, Uppland: ”Alfgautr och Vígdjarfr lät resa stenen efter sin fader Vígi.” En av sju svenska runstenar med ett alvnamn. Bild: {U573[2]}, {U573[3]}, via [Wikimedia Commons]({U573[1]}). Översättning: Samnordisk runtextdatabas.

**På runstenarna.** I texterna finns inga alver alls, bara namnen.

Den som reste U 573 hette Alfgautr. Namnet är ett av mycket få spår av alverna i det vikingatida Sverige, tillsammans med husfrun i Götaland som stängde dörren för Sigvat.

## Det vi inte vet

- **Ett namn är inte en tro.** Att en förälder kallade sitt barn Alfgautr eller Alfhildr säger inget säkert om vad familjen trodde. Namnled ärvdes.
- **Ett sällskap i texten är inte en tro.** Att alverna står bredvid gudarna i Eddan visar hur diktarna ordnade sin värld. Dikterna skrevs ned på Island på 1200-talet.
- **Den första delen räknade fel på alverna.** Utgåvan stavar *alfar* utan accent, och ordlistan i första delen sökte bara *álf-*. Därför fattades eddadikternas alver där. Här är de med, och felet påverkar inte första delens jämförelse mellan sagorna.
- **Om metoden.** Alla {M['träffar']} ord som börjar på *alf* eller *álf* lästes och klassades för hand: alv, personnamn, ortnamn, kenning för en man, världsdel eller något annat (som *Alföðr*, Oden ”allfadern”). Klassningen gjordes med Anthropics språkmodell Claude (Claude Opus). En annan instans av samma modell klassade om 40 slumpade ord utan att se den första klassningen och kom fram till samma sak i alla 40. Varje citat i artikeln är kontrollerat mot texten. Reglerna låstes i [en analysplan]({PLAN}) innan vi räknade, och alla siffror finns i [resultatet]({RES}).

## Läs själv

Läs Alvíssmál, gärna högt. Lyssna efter vad alverna kallar saker, och jämför med jättarnas ord. Läs sedan Sigvats strof om den stängda dörren. Den är skriven av en man som stod där.

:::box Det viktigaste i korthet
- Alverna är mytens folk. Två tredjedelar av alla alver i den fornnordiska litteraturen står i Eddan och hos Snorre.
- I Eddan står alverna nästan alltid bredvid gudarna. I sagorna har de förlorat det sällskapet helt, men de har inte blivit monster.
- Ljusalver och dökkalver finns bara hos Snorre. Ingen annan text i materialet delar upp alverna så.
- I Sverige syns alverna nästan inte: inga ortnamn enligt Svenskt ortnamnslexikon, inga alver i runstenarnas texter och alvnamn på bara sju stenar. Det tydligaste spåret är ett offer, en kväll i Götaland.
:::

## Källor

Eddadikterna och Snorres Edda: heimskringla.no, Guðni Jónssons utgåvor; texterna används här bara för räkning och korta citat. Heimskringla: heimskringla.no, utgåvan av N. Linder och H. A. Haggson (1869–72), public domain. Islänningasagorna: sagadb.org (Sveinbjörn Þórðarson), nutida isländsk stavning, public domain. Fornaldarsagorna och samtidssagorna: heimskringla.no, Guðni Jónssons m.fl. utgåvor, bara räkning och korta citat. Tack till heimskringla.no för texterna. Ortnamnen: Svenskt ortnamnslexikon (Institutet för språk och folkminnen, 2016), bara läsning och korta citat. Runstenarna: Samnordisk runtextdatabas, version 3.1 (2018), Uppsala universitet. Översättningarna är våra egna utom runstenens. Reglerna och skripten: [analysplanen]({PLAN}) med ett tillägg."""

title_en = "Where did the elves go? The gods' neighbours in the Edda, almost gone from the sagas"
summary_en = (f"We read every elf in Old Norse literature, {N_EL} of them. In the Edda the elves nearly always stand beside the gods. "
              "In the sagas they never do – and in Sweden they appear neither in the place names nor on the runestones, except in seven names.")

body_en = f"""One evening almost a thousand years ago an Icelandic poet is walking through Götaland in today's Sweden. His name is Sigvatr, he is travelling on King Óláfr Haraldsson's business, and he needs a roof over his head. At the first farm the door is shut. At the next, the housewife stands in the doorway:

> {q('sigvat')}

“… the housewife stood in the door and told him not to come in, saying that they were holding a sacrifice to the elves.”

Sigvatr made a poem of it, and it survives:

> {q('sigvat_vers')}

“Come no further in, said the woman, you wretched man; I fear Odin's wrath, we are heathens.”

It is one of very few times an elf – or an offering to the elves – appears in a text about real people in Sweden. This article is the second in the series on the Norse beings. [The first]({'/en/artiklar/var-bodde-trollen'}) counted all the beings at once. Now we take one at a time, beginning with the elves: where they stand in the texts, whom they stand beside, and where they are missing.

## A people at the gods' side

In the Edda the elves are not little folk in the meadow. They are one of the peoples of the world, and they are nearly always named in the same breath as the gods. When the giant Þrymr wants to know how things stand in the world, he asks Loki:

> {q('thrym')}

“How is it with the æsir? How is it with the elves?” And Loki answers: *{q('loki')}* – “ill it is with the æsir, ill with the elves.” In Lokasenna Loki insults the assembled gods, and he does it before *{q('lokasenna')}* – “æsir and elves who are in here”.

We measured this. For every elf we checked whether a word for the gods – æsir, vanir, gods – stood within 25 words on either side. In the Edda that was true of **{round(T1['T1a_gudar']['Eddan_%'])} per cent** of the elves. In the sagas it was true of **not a single one** of the {U['sagorna_träffar']}. The difference is so large that it would arise by chance in fewer than one case in ten thousand, and it remains when we remove the poem with the most elves, and when we narrow the window.

{chart_company('en')}

We also had a guess in the other direction: that the elves of the sagas would have moved over to the trolls' side. It did not hold. Giants and evil beings are not reliably more often near the elves in the sagas than in the Edda. The elves of the sagas have lost their gods, but they have not gained monsters instead.

{alviss_box('en')}

The poem Alvíssmál is a word list of the peoples of the world. The dwarf Alvíss answers Thor on what everything is called among humans, gods, giants, dwarves – and elves. The elves' words are often bright: the fair roof, the fair wheel, the joy of sleep. It is also the poem with the most elves, which is why we tested the result without it.

## Light and dark – only in Snorri

The most famous description of the elves comes from Snorri Sturluson:

> {q('ljos')}

“The light elves are fairer than the sun to look at, but the dark elves are blacker than pitch.”

That division exists **only in Snorri**. Not a single other text in our material speaks of light elves or dark elves. When Snorri himself returns to the dark elves, *svartálfar*, they are the ones who forge Sif's hair of gold, and in their land, Svartálfaheimr, lives the dwarf Andvari. In Snorri the dark elves and the dwarves run together.

## Völundr, prince of the elves

The only one in the Edda called prince of the elves is the smith Völundr, and he has a poem of his own. He is called *{q('ljodi')}* and *{q('visi')}* – roughly “prince of the elves” and “leader of the elves”. King Níðuðr captures him, hamstrings him and sets him to forge. Völundr takes his revenge by killing the king's sons, and then he rises into the air and is gone.

![Völundr on the Ardre VIII stone, Gotland]({ARDRE[0]})
Völundr's smithy on the picture stone Ardre VIII from Gotland: the king's daughter on the left, the smithy in the middle, and Völundr flying away in bird shape. Image: {ARDRE[2]}, via [Wikimedia Commons]({ARDRE[1]}).

Völundr appears on a Gotlandic picture stone too. No runestone in Sweden spells out the word *elf*, but the story of the elves' prince was there in Sweden in pictures.

## The hill, the sacrifice and the elf-woman

Outside the Edda the elves are found almost only in the legendary sagas, the sagas of the time before Iceland was settled: {GN['fornaldar']} of the {N_EL} elves. There they have moved down among humans. King Helgi in Hrólfs saga kraka has a daughter with a woman who comes one night and vanishes, and the storyteller notes: *{q('alfkona')}* – “it had been an elf-woman.” In another story the elves have become a human people in the land of Álfheimar, and they are said to be *{q('sogubrot')}* – “a people called elves, much fairer than any other people in the North”.

In the prose of the sagas of Icelanders the elves appear twice in close to a million words, both times in Kormáks saga. A wounded man is told that there is *{q('kormak_hol')}* – “a hill near here where elves live” – and that he should *{q('kormak')}*: “hold a feast for the elves with the meat, and you will get better.” That and Sigvatr's shut door in Götaland are **the only times in the whole material that people give the elves anything**.

{chart_where('en')}

## Where the elves are missing

![Meadow elves by Nils Blommér, 1850]({ALVOR[0]})
The elves of the meadow as the 19th century saw them: Nils Blommér's painting of 1850. These are the elves of folk tales, not of the Edda. Painting: {ALVOR[2]}, {ALVOR[3]}, via [Wikimedia Commons]({ALVOR[1]}).

In Sweden it is hard to find the elves at all. We looked in three places.

**In the place names.** The Swedish place-name dictionary (Svenskt ortnamnslexikon) mentions the word *alv* in {A6['träffar']} explanations, but **not once is a place name read as an elf name**. Alva on Gotland and Alvaret on Öland are named after *alv*, the soil layer just below the topsoil. Even Alvhem in Västergötland, according to the dictionary, “possibly” contains the same soil layer.

**In the names.** In the sagas names such as Álfr, Álfhildr and Álfgeirr are common, {NAMES_SAGAS} times. On the Swedish runestones such names appear on only **{R5['alf_stenar']} of {R5['stenar']:,} stones**, and one of them is an uncertain reading. Thor names appear on {R5['tor_stenar']} stones.

{chart_names('en')}

![U 573 at Kragsta]({U573[0]})
U 573 at Kragsta in Lohärad parish, Uppland: “Alfgautr and Vígdjarfr had the stone raised in memory of their father Vígi.” One of seven Swedish runestones with an elf name. Image: {U573[2]}, {U573[3]}, via [Wikimedia Commons]({U573[1]}). Translation: Scandinavian Runic-text Database.

**On the runestones.** There are no elves at all in the texts, only the names.

The man who raised U 573 was called Alfgautr. His name is one of very few traces of the elves in Viking-age Sweden, together with the housewife in Götaland who shut the door on Sigvatr.

## What we do not know

- **A name is not a belief.** That parents called their child Alfgautr or Alfhildr says nothing certain about what the family believed. Name elements were inherited.
- **Company in a text is not a belief.** That the elves stand beside the gods in the Edda shows how the poets ordered their world. The poems were written down in Iceland in the 13th century.
- **The first part miscounted the elves.** The edition spells *alfar* without an accent, and the word list in the first part only looked for *álf-*. The elves of the Eddic poems were therefore missing there. Here they are included, and the error does not affect the first part's comparison between the sagas.
- **On the method.** All {M['träffar']} words beginning with *alf* or *álf* were read and classified by hand: elf, personal name, place name, kenning for a man, part of the world or something else (such as *Alföðr*, Odin “the All-father”). The classification was done with Anthropic's language model Claude (Claude Opus). Another instance of the same model reclassified 40 random words without seeing the first classification and reached the same result in all 40. Every quotation in the article is checked against the text. The rules were locked in [an analysis plan]({PLAN}) before we counted, and all figures are in [the results]({RES}).

## Read for yourself

Read Alvíssmál, preferably aloud. Listen for what the elves call things, and compare with the giants' words. Then read Sigvatr's stanza about the shut door. It was written by a man who stood there.

:::box The essentials in brief
- The elves are a people of myth. Two thirds of all the elves in Old Norse literature stand in the Edda and in Snorri.
- In the Edda the elves nearly always stand beside the gods. In the sagas they have lost that company entirely, but they have not become monsters.
- Light elves and dark elves exist only in Snorri. No other text in the material divides the elves that way.
- In Sweden the elves hardly appear: no place names according to the Swedish place-name dictionary, no elves in the runestone texts and elf names on only seven stones. The clearest trace is an offering, one evening in Götaland.
:::

## Sources

The Eddic poems and Snorri's Edda: heimskringla.no, Guðni Jónsson's editions; the texts are used here only for counting and short quotations. Heimskringla: heimskringla.no, the edition by N. Linder and H. A. Haggson (1869–72), public domain. The sagas of Icelanders: sagadb.org (Sveinbjörn Þórðarson), modern Icelandic spelling, public domain. The legendary and contemporary sagas: heimskringla.no, editions by Guðni Jónsson and others, counting and short quotations only. Thanks to heimskringla.no for the texts. The place names: Svenskt ortnamnslexikon (Institute for Language and Folklore, 2016), reading and short quotations only. The runestones: Scandinavian Runic-text Database (Samnordisk runtextdatabas), version 3.1 (2018), Uppsala University. The translations are our own except the runestone's. The rules and the scripts: [the analysis plan]({PLAN}) with one addendum."""

# ======================================================================================================================
# 6. Kontroller och skrivning
# ======================================================================================================================
HOLDBACK = re.compile(r"\bAI\b|signifikan|p-värde|p-value|bootstrap|\bHolm\b", re.I)
labels = ["Forskning", "Eddan", "Tro och magi"]
assert blog_labels.check(labels) is None, blog_labels.check(labels)
assert pc(GN["eddadikter"] + GN["snorre"], N_EL) == 69  # "två tredjedelar"
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not HOLDBACK.search(b), (lang, HOLDBACK.search(b).group(0))
    assert not re.search(r"^\|", b, re.M), "inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 3 and all(re.match(r"https://(upload|thumb)\.wikimedia\.org/", u) for u in imgs), imgs
    caps = [b.splitlines()[i + 1] for i, ln in enumerate(b.splitlines()) if ln.startswith("![")]
    assert all("Wikimedia Commons" in c and re.search(r"CC BY|CC0|public domain", c) for c in caps), caps
    for m in re.finditer(r":::chart[^\n]*\n(.*?)\n:::", b, re.S):
        assert "Diagram: Vitki" in m.group(1) or "Chart: Vitki" in m.group(1)
        for row in m.group(1).splitlines():
            if "|" in row:
                assert 0 <= float(row.split("|")[1].strip()) <= 100, row
    for k in list(Q) + list(EQ):
        assert q(k) in b, (lang, k)

OUT = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
wc = lambda x: len(re.sub(r"\]\([^)]*\)", "]", x).split())  # noqa: E731
path = os.path.join(ROOT, "utdata", "blogg", "alverna.json")
json.dump(OUT, open(path, "w"), ensure_ascii=False, indent=1)
print(path, wc(body), "ord sv,", wc(body_en), "words en")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published") and old.get("slug") == SLUG, "Bara det opublicerade utkastet skrivs över härifrån"
        ref.set({**OUT, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc, SLUG)
    else:
        assert not [p for p in blog._all() if p.get("slug") == SLUG], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**OUT, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Eddan och sagorna|väsen|alverna", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id, SLUG)
    blog._forget()
