"""Artikeln "Jättekvinnans ugn" – del 3 i serien Nordiska väsen under vikingatiden: jättarna.

Bygger på den låsta studien analysplaner/2026-11-21-jattarna.md (d57af06); siffrorna läses ur utdata/jattarna/matt.json,
efterkontroll.json och j5_lasning.json, och varje citat kontrolleras mot texten i korpusen.
    ../../../.venv/bin/python build_jattarna.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

SLUG = "jattekvinnans-ugn"
PLAN = "https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-21-jattarna.md"
RES = "https://github.com/Precatio/runes/blob/main/utdata/jattarna/resultat.md"
D = os.path.join(ROOT, "utdata", "jattarna")
M = json.load(open(os.path.join(D, "matt.json"), encoding="utf-8"))
EK = json.load(open(os.path.join(D, "efterkontroll.json"), encoding="utf-8"))
J5 = json.load(open(os.path.join(D, "j5_lasning.json"), encoding="utf-8"))

# ======================================================================================================================
# 1. Siffrorna
# ======================================================================================================================
EDDA_C = ["eddadikter", "snorra_edda_gylfaginning", "snorra_edda_skáldskaparmál"]
SAGA_C = [c for c in M["J1"] if c not in EDDA_C and not c.startswith("runstenar")]
n_edda = sum(sum(M["J1"][c].values()) for c in EDDA_C)
n_saga = sum(sum(M["J1"][c].values()) for c in SAGA_C)
DENS = M["J1_per_10000"]
assert round(DENS["snorra_edda_gylfaginning"]) == 91 and round(DENS["eddadikter"]) == 54
assert round(DENS["islanningasagor"], 1) == 1.7 and round(DENS["heimskringla"], 1) == 0.5
R = M["J2_risi_andel"]
assert R["eddadikter"]["risi"] == 0 and R["eddadikter"]["av"] == 110
RISI = {"eddadikter": R["eddadikter"], "gylf": R["snorra_edda_gylfaginning"], "isl": R["islanningasagor"], "forn": R["fornaldarsagor"]}
PCT = {k: round(100 * x["risi"] / x["av"]) for k, x in RISI.items()}
assert list(PCT.values()) == [0, 13, 21, 29]
T = M["tester"]["huvud"]
T2, T3 = T["T2_kvinnor"], T["T3_norr"]
assert not T2["håller"] and T3.get("obestämt")
T2_TROLL = M["tester"]["utan_tröll"]["T2_kvinnor"]
assert (round(T2["Eddan_%"]), round(T2["sagorna_%"]), round(T2_TROLL["sagorna_%"])) == (12, 23, 36)
assert round(EK["utan_namn_i_sagorna_och_tröll"]["sagorna_%"]) == 35
NAMES = J5["jatte_eller_trollnamn"]
assert len(NAMES) == 8 and len(J5["samiska_jattenamn"]) == 2
ISL = M["J1"]["islanningasagor"]
FORN = M["J1"]["fornaldarsagor"]
assert ISL["tröll"] == 75 and FORN["tröll"] == 101 and FORN["namngiven jättinna"] == 20
assert [v["sten"] if isinstance(v, dict) else v[0] for v in M["J4_runstenar"]] == ["Ög 64", "U 703"]
GATE = M["grind"]["viktat_procent"]
assert GATE == 97.8
NAMN71 = EK["namn_utanfor_eddan_handlast"]
assert (NAMN71["träffar"], NAMN71["verkliga_jättar"]) == (71, 29)

# ======================================================================================================================
# 2. Citaten
# ======================================================================================================================
K = os.path.join(ROOT, "utdata", "varlden", "korpus")
EDDA = json.load(open(os.path.join(ROOT, "utdata", "Malt", "kallor", "edda.json"), encoding="utf-8"))


def flat(t):
    return " ".join(t.split())


Q = {
    "grid": ("fornaldarsogur/Illuga_saga_Gríðarfóstra.txt", "Hellir nokkurr stóð öðrum megin fjarðar þessa, er réð fyrir tröllkona sú, er Gríðr hét. Hún var in mesta tröllkona."),
    "bergrisi": ("heimskringla/Saga_Ólafs_Tryggvasonar.txt", "Þar kom í móti honum bergrisi, ok hafði járnstaf í hendi, ok bar höfuð hans hæra en fjöllin"),
    "bard": ("islendingasogur/bardar_saga_snaefellsass.is.txt", "móðir hans var komin af tröllaættum"),
}
EQ = {
    "hanzki": ("Gylfaginning", "En hvárt hefir þú dregit á braut hanzka minn?"),
    "thumall": ("Gylfaginning", "Sér Þórr þá, at þat hafði hann haft of nóttina fyrir skála, en afhúsit, þat var þumlungrinn hanzkans."),
    "voluspa": ("Völuspá", "Ek man jötna ár of borna, þá er forðum mik fædda höfðu"),
}
for k, (p, s) in Q.items():
    assert s in flat(open(os.path.join(K, p), encoding="utf-8").read()), k
for k, (poem, s) in EQ.items():
    assert s in flat(EDDA[poem]), k


def q(k):
    return Q[k][1] if k in Q else EQ[k][1]


# ======================================================================================================================
# 3. Bilderna (Wikimedia Commons; licenser kontrollerade 2026-11-21)
# ======================================================================================================================
GIROM = ("https://upload.wikimedia.org/wikipedia/commons/9/98/Ekornavallen_-_KMB_-_16000300031992.jpg",
         "https://commons.wikimedia.org/wiki/File:Ekornavallen_-_KMB_-_16000300031992.jpg", "Bengt A. Lundberg, Riksantikvarieämbetet", "CC BY 2.5")
TRULL = ("https://thumb.wikimedia.org/wikipedia/commons/thumb/6/62/Trullhalsar.JPG/1280px-Trullhalsar.JPG",
         "https://commons.wikimedia.org/wiki/File:Trullhalsar.JPG", "Tokfursten", "public domain")
HUARD = ("https://thumb.wikimedia.org/wikipedia/commons/thumb/3/30/Louis_Huard_-_Giant_Skrymir_and_Thor.jpg/1280px-Louis_Huard_-_Giant_Skrymir_and_Thor.jpg",
         "https://commons.wikimedia.org/wiki/File:Louis_Huard_-_Giant_Skrymir_and_Thor.jpg", "Louis Huard", "public domain")


# ======================================================================================================================
# 4. Diagrammen (procent)
# ======================================================================================================================
def chart_risi(lang):
    sv = lang == "sv"
    labs = {"eddadikter": ("Eddadikterna", "The Eddic poems"), "gylf": ("Snorres Gylfaginning", "Snorri's Gylfaginning"),
            "isl": ("Islänningasagorna", "The sagas of Icelanders"), "forn": ("Fornaldarsagorna", "The legendary sagas")}
    rows = [f":::chart {'Hur ofta jätten kallas risi: andel av orden jötunn, þurs och risi' if sv else 'How often the giant is called risi: share of the words jötunn, þurs and risi'}"]
    for k, x in RISI.items():
        rows.append(f"{'+' if k == 'eddadikter' else ''}{labs[k][0 if sv else 1]} | {PCT[k]} | {x['risi']} {'av' if sv else 'of'} {x['av']}")
    rows.append("Prosan i sagorna. Diagram: Vitki, efter Vitkis räkning i texterna från heimskringla.no och sagadb.org."
                if sv else "The prose of the sagas. Chart: Vitki, from Vitki's count in the texts from heimskringla.no and sagadb.org.")
    return "\n".join(rows) + "\n:::"


def chart_women(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Hur stor andel av jätteorden som betecknar en kvinna' if sv else 'How large a share of the giant words denote a woman'}"]
    rows.append("# " + ("Alla jätteord" if sv else "All giant words"))
    rows.append(f"{'Eddan' if sv else 'The Edda'} | {round(T2['Eddan_%'])} | ")
    rows.append(f"{'Sagorna' if sv else 'The sagas'} | {round(T2['sagorna_%'])} | ")
    rows.append("# " + ("Utan det allmänna ordet tröll" if sv else "Without the general word tröll"))
    rows.append(f"{'Eddan' if sv else 'The Edda'} | {round(T2_TROLL['Eddan_%'])} | ")
    rows.append(f"+{'Sagorna' if sv else 'The sagas'} | {round(T2_TROLL['sagorna_%'])} | ")
    rows.append("Den övre jämförelsen var vårt låsta test, och det höll inte. Den undre var en kontroll som pekar mot en ny fråga, men den är inte prövad. Diagram: Vitki."
                if sv else "The upper comparison was our locked test, and it did not hold. The lower one was a check that points to a new question, but it is not tested. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


def names_list(lang):
    sv = lang == "sv"
    gloss = {"Edenryd": ("”jättarnas röjning” – och en tradition om jättar i ett stenröse", "“the giants' clearing” – and a tradition of giants in a cairn"),
             "Gigerugnen (Ekornavallen)": ("”jättekvinnans ugn” – en gånggrift", "“the giantess's oven” – a passage grave"),
             "Trollhättan": ("fallet som ett vattentrolls hätta", "the falls as a water-troll's hood"),
             "Trullhalsar": ("”trollhalsar” – ett gravfält", "“troll necks” – a grave field"),
             "Bobergs härad": ("kanske jättarnas eller trollens boning i berget", "perhaps the giants' or trolls' dwelling in the hill"),
             "Tossebergsklätten": ("kanske *tusse*, jätte", "perhaps *tusse*, giant"),
             "Locknevi": ("en av tolkningarna är ”trollkäring”", "one of the readings is “troll-hag”"),
             "Trollaborg": ("sägner om troll – eller släkten Trolle", "legends of trolls – or the Trolle family")}
    out = []
    for n in NAMES:
        g = gloss[n["namn"]]
        out.append(f"- **{n['namn'].replace(' (Ekornavallen)', '')}** ({n['landskap']}): {g[0] if sv else g[1]}")
    return "\n".join(out)


# ======================================================================================================================
# 5. Texten
# ======================================================================================================================
title = "Jättekvinnans ugn – var jättarna bodde, i sagorna och i Sverige"
summary = ("Vi räknade jättarna i den fornnordiska litteraturen och letade efter dem i de svenska ortnamnen. I Eddan heter de jötnar och har namn. "
           "I sagorna blir de troll. Och i Sverige har de, där de finns, lämnat sina namn på de äldsta gravarna.")

body = f"""En natt söker Tor och hans följe skydd i en stor stuga med en bred öppning åt ena hållet. Det mullrar och skakar hela natten. På morgonen ligger en jätte och sover bredvid dem, och han frågar Tor:

> {q('hanzki')}

”Har du tagit bort min handske?”

> {q('thumall')}

”Då ser Tor att det var den han hade sovit i under natten, och sidorummet var handskens tumme.”

Jätten heter Skrymer, och berättelsen kommer från Snorre Sturlassons Gylfaginning. Det är en av de berättelser där jättarna är som störst. Den här artikeln är den tredje i serien om de nordiska väsendena. Efter [trollen](/artiklar/var-bodde-trollen) och [alverna](/artiklar/var-tog-alverna-vagen) kommer nu jättarna: vad de heter, vilka av dem som är kvinnor, och var de finns kvar i Sverige.

![Skrymer och Tor av Louis Huard]({HUARD[0]})
Tor möter jätten Skrymer, som 1800-talets illustratörer föreställde sig honom. Teckning: {HUARD[2]}, {HUARD[3]}, via [Wikimedia Commons]({HUARD[1]}).

## Jättarnas ord

Jättar finns överallt i litteraturen, men tätast i myten. Snorres Gylfaginning nämner dem {round(DENS['snorra_edda_gylfaginning'])} gånger per tiotusen ord, och eddadikterna {round(DENS['eddadikter'])} gånger. I islänningasagornas prosa sjunker det till {str(round(DENS['islanningasagor'], 1)).replace('.', ',')} och i Heimskringla till {str(round(DENS['heimskringla'], 1)).replace('.', ',')}. Völvan i Völuspá börjar sitt minne hos dem: *{q('voluspa')}* – ”jag minns jättar, födda i tidernas början, som en gång fostrade mig”.

Orden för dem skiftar med texterna.

- **Jötunn** och **þurs** är mytens ord. *Þurs* är också namnet på en runa, och i Snorres skapelseberättelse kommer *hrímþursar*, rimtursarna, från urjätten Ymer.
- **Risi** saknas helt i eddadikterna: inte en gång bland {RISI['eddadikter']['av']} jätteord. I fornaldarsagorna är vart tredje av dem *risi*.
- **Tröll** är sagornas ord. Det är det vanligaste i både fornaldarsagorna ({FORN['tröll']} gånger) och islänningasagorna ({ISL['tröll']}), men det förekommer bara en gång i eddadikterna.
- **Gýgr, flagð, skessa, tröllkona** – orden för jättinnan.
- **Bergbúi**, ”den som bor i berget”.

{chart_risi('sv')}

Det ser ut som en förskjutning i språket: från mytens *jötunn* till sagornas *risi* och *tröll*. Vi prövade inte den saken, eftersom vi redan hade sett den i stora drag innan vi låste planen. Mönstret redovisas, men det är inte bevisat.

Ibland står jättarna mitt i landskapet också i kungasagorna. När en trollkunnig man i valskepnad simmar mot Island för att speja åt den danske kungen, möter han landvättarna. En av dem är en bergjätte: *{q('bergrisi')}* – ”där kom en bergjätte emot honom, med en järnstav i handen, och hans huvud räckte högre än fjällen.”

## Jättinnorna

I Eddan är ungefär en av åtta jättar en kvinna. Bland dem finns Gjalp och Greip, Geirröds döttrar som Tor bryter ryggen på, och Hyndla, som räknar upp ätterna. I fornaldarsagorna får jättinnorna större roller. I Illuga saga Gríðarfóstra kommer hjälten till en grotta på andra sidan fjorden:

> {q('grid')}

”Där fanns en grotta på andra sidan fjorden, och där rådde en trollkvinna som hette Gríðr. Hon var en mycket stor trollkvinna.” Gríðr är också den jättinna som nämns flest gånger i hela materialet.

Vi ville veta om jättarna blir mer kvinnliga i sagorna. Svaret är att vi inte vet. Räknat på alla jätteord är andelen kvinnor {round(T2['Eddan_%'])} procent i Eddan och {round(T2['sagorna_%'])} procent i sagorna, men skillnaden är inte säker. Den kan ha uppstått av en slump. Det var vårt låsta test, och det höll inte.

{chart_women('sv')}

En kontroll pekar ändå mot något. Tar man bort det allmänna ordet *tröll*, som inte säger om väsendet är man eller kvinna, är vart tredje av sagornas jätteord en kvinna: tröllkonor, flögð och skessor. I Eddan är det ungefär vart åttonde. Men den jämförelsen prövade vi inte i förväg, och därför är den en fråga för nästa plan och inte ett resultat.

## Jättarna i Sverige

![Gånggriften Girommen vid Ekornavallen]({GIROM[0]})
Gånggriften vid Ekornavallen i Västergötland som heter Gigerugnen eller Girommen, ”jättekvinnans ugn”. Graven byggdes på stenåldern, flera tusen år före vikingarna. Foto: {GIROM[2]}, {GIROM[3]}, via [Wikimedia Commons]({GIROM[1]}).

Runstenarnas texter nämner inga jättar. Listan gav två träffar, och båda var falska: Greip på Ög 64 är en man, och *risinn* på U 703 betyder ”rest”. Men i ortnamnen finns jättarna. Vi läste allt i Svenskt ortnamnslexikon där förklaringen nämner jätte, troll, turs eller rese. Åtta namn tolkas av lexikonet som jätte- eller trollnamn, säkert eller möjligt:

{names_list('sv')}

Tre av dem sitter på förhistoriska gravar: gånggriften vid Ekornavallen, gravfältet Trullhalsar på Gotland och stenröset vid Edenryd i Skåne. Vi vet inte när namnen gavs eller vad de som gav dem tänkte. Men när jättarna och trollen finns i det svenska landskapet, är det ofta vid de gamla gravarna.

![Trullhalsar på Gotland]({TRULL[0]})
Trullhalsar, gravfältet i Anga socken på Gotland. Namnet betyder ”trollhalsar”, antagligen efter stensättningarna med sina murade sidor. Foto: {TRULL[2]}, {TRULL[3]}, via [Wikimedia Commons]({TRULL[1]}).

Lika talande är namnen som *inte* handlar om jättar. **Jättendal** i Hälsingland kommer enligt lexikonet av ett fornsvenskt ord för betesmark. **Jättene** i Västergötland kommer av *gátt*, öppning. Längst i norr finns ett annat jättefolk: de samiska namnen Staloluokta och Stalon bär den människoätande jätten *stállo*.

## Det som inte gick

- **Väderstrecken.** Vi ville veta om jättarna bor i öster i myten och i norr i sagorna. Men för få jätteord står nära ett väderstreck: 18 i Eddan och 21 i sagorna, och vi hade bestämt att det skulle vara minst 20 i vardera. Frågan är obesvarad.
- **Namnen utanför Eddan.** När vi räknat klart såg vi att jättenamnen ofta är något annat i sagorna. *Greip* är där verbet ”grep”, Surtr och Baugi är vanliga män, och Skrýmir är ett svärd. Av {NAMN71['träffar']} sådana träffar var bara omkring {NAMN71['verkliga_jättar']} riktiga jättar. Vårt stickprov hade inte fångat det. Vi räknade om utan dem, och slutsatserna ovan står sig.
- **Om metoden.** Ett stickprov av träffarna lästes för hand, och {str(GATE).replace('.', ',')} procent var riktiga jättar. Stickprovet bedömdes med Anthropics språkmodell Claude (Claude Opus), och varje citat i artikeln är kontrollerat mot texten. Reglerna låstes i [en analysplan]({PLAN}) innan vi räknade, och allt finns i [resultatet]({RES}).

## Gå dit

Gigerugnen ligger vid Ekornavallen mellan Falköping och Hornborgasjön, och Trullhalsar ligger i Anga på Gotland. Båda går att besöka. Den som står vid gånggriften kan fråga sig vad människorna som gav den namnet trodde om dem som byggt den.

:::box Det viktigaste i korthet
- Jättarna hör till myten. Gylfaginning och eddadikterna nämner dem tiotals gånger oftare än islänningasagorna och kungasagorna.
- Orden skiftar: myten säger *jötunn* och *þurs*, sagorna *tröll* och *risi*. *Risi* finns inte en enda gång i eddadikterna.
- Om jättarna blir mer kvinnliga i sagorna kunde vi inte avgöra. Det är en öppen fråga för en ny prövning.
- I Sverige finns jättarna i ortnamnen, inte på runstenarna. Tre av de åtta jätte- och trollnamnen sitter på förhistoriska gravar.
:::

## Källor

Eddadikterna och Snorres Edda: heimskringla.no, Guðni Jónssons utgåvor; texterna används här bara för räkning och korta citat. Heimskringla: heimskringla.no, utgåvan av N. Linder och H. A. Haggson (1869–72), public domain. Islänningasagorna: sagadb.org (Sveinbjörn Þórðarson), public domain. Fornaldarsagorna och samtidssagorna: heimskringla.no, Guðni Jónssons m.fl. utgåvor, bara räkning och korta citat. Tack till heimskringla.no för texterna. Ortnamnen: Svenskt ortnamnslexikon (Institutet för språk och folkminnen, 2016), bara läsning och korta citat. Runstenarna: Samnordisk runtextdatabas, version 3.1 (2018), Uppsala universitet. Översättningarna är våra egna. Reglerna och skripten: [analysplanen]({PLAN})."""

title_en = "The giantess's oven – where the giants lived, in the sagas and in Sweden"
summary_en = ("We counted the giants of Old Norse literature and looked for them in Swedish place names. In the Edda they are jötnar and have names. "
              "In the sagas they become trolls. And in Sweden, where they appear at all, they have left their names on the oldest graves.")

body_en = f"""One night Thor and his companions take shelter in a large hall with a wide opening at one end. It rumbles and shakes all night. In the morning a giant is lying asleep beside them, and he asks Thor:

> {q('hanzki')}

“Have you taken away my glove?”

> {q('thumall')}

“Then Thor sees that this was what he had slept in during the night, and the side room was the thumb of the glove.”

The giant is Skrýmir, and the story comes from Snorri Sturluson's Gylfaginning. It is one of the stories in which the giants are at their largest. This article is the third in the series on the Norse beings. After [the trolls](/en/artiklar/var-bodde-trollen) and [the elves](/en/artiklar/var-tog-alverna-vagen) come the giants: what they are called, which of them are women, and where they survive in Sweden.

![Skrýmir and Thor by Louis Huard]({HUARD[0]})
Thor meets the giant Skrýmir, as the illustrators of the 19th century imagined him. Drawing: {HUARD[2]}, {HUARD[3]}, via [Wikimedia Commons]({HUARD[1]}).

## The giants' words

Giants are everywhere in the literature, but densest in myth. Snorri's Gylfaginning mentions them {round(DENS['snorra_edda_gylfaginning'])} times per ten thousand words, and the Eddic poems {round(DENS['eddadikter'])} times. In the prose of the sagas of Icelanders it drops to {round(DENS['islanningasagor'], 1)} and in Heimskringla to {round(DENS['heimskringla'], 1)}. The seeress in Völuspá begins her memory among them: *{q('voluspa')}* – “I remember giants, born at the beginning of time, who once raised me”.

The words for them shift with the texts.

- **Jötunn** and **þurs** are the words of myth. *Þurs* is also the name of a rune, and in Snorri's creation story the *hrímþursar*, the rime-giants, descend from the primeval giant Ymir.
- **Risi** is entirely missing from the Eddic poems: not once among {RISI['eddadikter']['av']} giant words. In the legendary sagas every third one is *risi*.
- **Tröll** is the word of the sagas. It is the commonest in both the legendary sagas ({FORN['tröll']} times) and the sagas of Icelanders ({ISL['tröll']}), but it occurs only once in the Eddic poems.
- **Gýgr, flagð, skessa, tröllkona** – the words for the giantess.
- **Bergbúi**, “the one who lives in the mountain”.

{chart_risi('en')}

It looks like a shift in the language: from the *jötunn* of myth to the *risi* and *tröll* of the sagas. We did not test this, because we had already seen it in broad outline before we locked the plan. The pattern is reported, but it is not proven.

Sometimes the giants stand in the landscape in the kings' sagas too. When a sorcerer in the shape of a whale swims towards Iceland to spy for the Danish king, he meets the land-spirits. One of them is a mountain giant: *{q('bergrisi')}* – “there came a mountain giant towards him, with an iron staff in his hand, and his head reached higher than the mountains.”

## The giantesses

In the Edda about one giant in eight is a woman. Among them are Gjálp and Greip, Geirröðr's daughters whose backs Thor breaks, and Hyndla, who recites the lineages. In the legendary sagas the giantesses get larger parts. In Illuga saga Gríðarfóstra the hero comes to a cave on the other side of the fjord:

> {q('grid')}

“There was a cave on the other side of this fjord, ruled by the troll-woman called Gríðr. She was a very great troll-woman.” Gríðr is also the giantess named most often in the whole material.

We wanted to know whether the giants become more female in the sagas. The answer is that we do not know. Counted over all giant words, the share of women is {round(T2['Eddan_%'])} per cent in the Edda and {round(T2['sagorna_%'])} per cent in the sagas, but the difference is not certain. It could have arisen by chance. That was our locked test, and it did not hold.

{chart_women('en')}

One check does point to something. Leave out the general word *tröll*, which does not say whether the being is male or female, and every third giant word in the sagas is a woman: troll-women, ogresses and skessur. In the Edda it is about one in eight. But we did not test that comparison in advance, so it is a question for the next plan and not a result.

## The giants in Sweden

![The passage grave Girommen at Ekornavallen]({GIROM[0]})
The passage grave at Ekornavallen in Västergötland called Gigerugnen or Girommen, “the giantess's oven”. The grave was built in the Stone Age, thousands of years before the Vikings. Photo: {GIROM[2]}, {GIROM[3]}, via [Wikimedia Commons]({GIROM[1]}).

The runestone texts mention no giants. The list gave two hits, and both were false: Greip on Ög 64 is a man, and *risinn* on U 703 means “raised”. But in the place names the giants are there. We read everything in the Swedish place-name dictionary (Svenskt ortnamnslexikon) where the explanation mentions giant, troll, turs or rese. Eight names are read by the dictionary as giant or troll names, certainly or possibly:

{names_list('en')}

Three of them sit on prehistoric graves: the passage grave at Ekornavallen, the grave field Trullhalsar on Gotland and the cairn at Edenryd in Skåne. We do not know when the names were given or what those who gave them thought. But when the giants and trolls appear in the Swedish landscape, it is often at the old graves.

![Trullhalsar on Gotland]({TRULL[0]})
Trullhalsar, the grave field in Anga parish on Gotland. The name means “troll necks”, presumably after the stone settings with their walled sides. Photo: {TRULL[2]}, {TRULL[3]}, via [Wikimedia Commons]({TRULL[1]}).

Just as telling are the names that are *not* about giants. **Jättendal** in Hälsingland, according to the dictionary, comes from an Old Swedish word for pasture. **Jättene** in Västergötland comes from *gátt*, opening. Far in the north there is another giant people: the Sami names Staloluokta and Stalon carry the man-eating giant *stállo*.

## What did not work

- **The points of the compass.** We wanted to know whether the giants live in the east in myth and in the north in the sagas. But too few giant words stand near a point of the compass: 18 in the Edda and 21 in the sagas, and we had decided on at least 20 in each. The question is unanswered.
- **The names outside the Edda.** When we had finished counting, we saw that the giants' names are often something else in the sagas. There *Greip* is the verb “grabbed”, Surtr and Baugi are ordinary men, and Skrýmir is a sword. Of {NAMN71['träffar']} such hits only about {NAMN71['verkliga_jättar']} were real giants. Our sample had not caught it. We counted again without them, and the conclusions above stand.
- **On the method.** A sample of the hits was read by hand, and {GATE} per cent were real giants. The sample was judged with Anthropic's language model Claude (Claude Opus), and every quotation in the article is checked against the text. The rules were locked in [an analysis plan]({PLAN}) before we counted, and everything is in [the results]({RES}).

## Go there

Gigerugnen lies at Ekornavallen between Falköping and Lake Hornborga, and Trullhalsar lies in Anga on Gotland. Both can be visited. Whoever stands by the passage grave can ask what the people who named it believed about those who built it.

:::box The essentials in brief
- The giants belong to myth. Gylfaginning and the Eddic poems mention them tens of times more often than the sagas of Icelanders and the kings' sagas.
- The words shift: myth says *jötunn* and *þurs*, the sagas *tröll* and *risi*. *Risi* does not occur once in the Eddic poems.
- Whether the giants become more female in the sagas we could not decide. It is an open question for a new test.
- In Sweden the giants are found in the place names, not on the runestones. Three of the eight giant and troll names sit on prehistoric graves.
:::

## Sources

The Eddic poems and Snorri's Edda: heimskringla.no, Guðni Jónsson's editions; the texts are used here only for counting and short quotations. Heimskringla: heimskringla.no, the edition by N. Linder and H. A. Haggson (1869–72), public domain. The sagas of Icelanders: sagadb.org (Sveinbjörn Þórðarson), public domain. The legendary and contemporary sagas: heimskringla.no, editions by Guðni Jónsson and others, counting and short quotations only. Thanks to heimskringla.no for the texts. The place names: Svenskt ortnamnslexikon (Institute for Language and Folklore, 2016), reading and short quotations only. The runestones: Scandinavian Runic-text Database (Samnordisk runtextdatabas), version 3.1 (2018), Uppsala University. The translations are our own. The rules and the scripts: [the analysis plan]({PLAN})."""

# ======================================================================================================================
# 6. Kontroller och skrivning
# ======================================================================================================================
HOLDBACK = re.compile(r"\bAI\b|signifikan|p-värde|p-value|bootstrap|\bHolm\b", re.I)
labels = ["Forskning", "Eddan", "Tro och magi", "Geografi"]
assert blog_labels.check(labels) is None, blog_labels.check(labels)
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not HOLDBACK.search(b), (lang, HOLDBACK.search(b).group(0))
    assert not re.search(r"^\|", b, re.M), "inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M))
    assert "{" not in b and "}" not in b
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
        if k != "bard":
            assert q(k) in b, (lang, k)
assert M["J1"]["eddadikter"].get("tröll") == 1

OUT = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
wc = lambda x: len(re.sub(r"\]\([^)]*\)", "]", x).split())  # noqa: E731
path = os.path.join(ROOT, "utdata", "blogg", "jattarna.json")
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
                 "topic": "Eddan och sagorna|väsen|jättarna", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id, SLUG)
    blog._forget()
