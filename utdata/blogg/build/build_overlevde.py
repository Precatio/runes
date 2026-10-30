"""Artikeln "Tor föll, hjälten blev dräng – vilka vikinganamn lever kvar?" (sv + en): runstenarnas personnamn mot SCB
2020 och maktens ord mot dagens svenska, enligt den låsta planen analysplaner/2026-10-30-namnen-och-orden-som-overlevde.md.
Siffrorna låses mot utdata/overlevde/namn.json, ord.json och SCB:s tilltalsnamn (data/namn/scb_tilltalsnamn.json).
    ../../../.venv/bin/python build_overlevde.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import commons  # noqa: E402

O = os.path.join(ROOT, "utdata", "overlevde")
N = json.load(open(os.path.join(O, "namn.json"), encoding="utf-8"))
NX = json.load(open(os.path.join(O, "namn_extra.json"), encoding="utf-8"))
W = json.load(open(os.path.join(O, "ord.json"), encoding="utf-8"))
SCB = {}
for x in json.load(open(os.path.join(ROOT, "data", "namn", "scb_tilltalsnamn.json"), encoding="utf-8"))["names"]:
    SCB[x["name"]] = SCB.get(x["name"], 0) + (x["n2020"] or 0)
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
pc = lambda x: round(100 * x)  # noqa: E731
sp = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731  (Swedish thousands separator)
en = lambda n: f"{n:,}"  # noqa: E731

# ---- the locked numbers -----------------------------------------------------------------------------------------------
assert (N["n_names"], N["alive"]) == (391, 82) and pc(N["share"]) == 21 and pc(N["bearer_weighted"]) == 37
TH, TO = N["N2"]["a"], N["N2"]["b"]
assert (TH, TO) == ([22, 34], [60, 275]) and N["N2"]["holm"] < 0.002
WO, MA = N["N1"]["a"], N["N1"]["b"]
assert (WO, MA) == ([20, 41], [62, 268])
CH = N["chain"]
assert (CH["in_letters"], CH["in_letters_alive"], CH["not_in_letters"], CH["not_in_letters_alive"]) == (60, 44, 331, 38)
assert (NX["n_names"], NX["alive"]) == (385, 85)
assert W["W1"]["table"] == [[9, 8], [23, 4]] and W["W1"]["p"] < 0.025
assert W["description_rank_only"]["table"][0] == [2, 7]
BY = W["by_domain"]
assert BY["makt"]["lever"] == ["konungr", "styrimaðr"] and BY["makt"]["ändrad"] == ["drengr"]
assert set(BY["makt"]["borta"]) == {"þegn", "húskarl", "lið", "dróttinn", "félagi", "sveinn (följesman)"}
K = {k: SCB[k] for k in ("Torsten", "Torbjörn", "Tore", "Tord", "Ingrid", "Ingvar", "Åsa", "Erik", "Björn", "Sven",
                         "Håkan", "Knut", "Harald", "Ulf", "Gunnar")}
assert (K["Torsten"], K["Ulf"], K["Erik"], K["Ingrid"]) == (3540, 31585, 55968, 40300)
pn = lambda a: pc(a[0] / sum(a))  # noqa: E731
DEAD = {x["name"] for x in N["top_dead"]}
assert {"Ônundr", "Ingifastr", "Freysteinn", "Holmsteinn", "Holmfastr", "Guðfastr", "Vébjôrn"} <= DEAD

Q = {s: recs[s]["normalization"].strip().replace('"', "") for s in ("Sö 179", "U 344")}
assert "foru drængila" in Q["Sö 179"]
assert Q["U 344"].startswith("En UlfR hafiR a Ænglandi þry giald takit.")
Q["U 344"] = Q["U 344"].split(". ")[0] + "."  # the first sentence: Ulfr's three payments

# ---- photographs ------------------------------------------------------------------------------------------------------
FILES = commons.wikidata_files(["Sö 179", "U 344"])
THOR = "Lorenz Frølich - Æsir-Thor - NMH 425-1925 - Nationalmuseum.jpg"
INFO = commons.commons_info(list(FILES.values()) + [THOR])
assert INFO[THOR]["licence"] == "Public domain" and "Frølich" in INFO[THOR]["author"]


def thor(lang):
    page = "https://commons.wikimedia.org/wiki/File:" + THOR.replace(" ", "_")
    if lang == "sv":
        return (f"![Tor, tecknad av Lorenz Frølich]({INFO[THOR]['thumb']})\nTor med hammaren, omgiven av slingrande "
                f"ormdjur som på en runsten. Akvarell av Lorenz Frølich (1820–1908), Nationalmuseum (NMH 425/1925). "
                f"Fri från upphovsrätt, via [Wikimedia Commons]({page}).")
    return (f"![Thor, drawn by Lorenz Frølich]({INFO[THOR]['thumb']})\nThor with his hammer, framed by intertwined serpents "
            f"as on a runestone. Watercolour by Lorenz Frølich (1820–1908), Nationalmuseum, Stockholm (NMH 425/1925). "
            f"Public domain, via [Wikimedia Commons]({page}).")
LIC = {"CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/", "CC BY 2.5": "https://creativecommons.org/licenses/by/2.5/"}
CRED = {"Sö 179": ("Tåggas", "CC BY-SA 3.0"), "U 344": ("Berig", "CC BY 2.5")}
for s, (who, lic) in CRED.items():
    assert lic in INFO[FILES[s]]["licence"], (s, INFO[FILES[s]])


def photo(s, text, lang):
    who, lic = CRED[s]
    page = "https://commons.wikimedia.org/wiki/File:" + FILES[s].replace(" ", "_")
    alt = f"Runstenen {s}" if lang == "sv" else f"The runestone {s}"
    return (f"![{alt}]({INFO[FILES[s]]['thumb']})\n{text} {'Foto' if lang == 'sv' else 'Photo'}: {who}, [{lic}]({LIC[lic]}), "
            f"via [Wikimedia Commons]({page}).")


def chart(lang):
    sv = lang == "sv"
    st = "namn" if sv else "names"
    of = "av" if sv else "of"
    rows = [":::chart Hur stor del av runstenarnas namn som bärs av minst tio svenskar i dag" if sv else
            ":::chart Share of the runestones' names borne by at least ten Swedes today",
            f"+{'Namn med en gud i' if sv else 'Names with a god in them'} | {pn(TH)} | {TH[0]} {of} {sum(TH)} {st}",
            f"{'Övriga namn' if sv else 'Other names'} | {pn(TO)} | {TO[0]} {of} {sum(TO)} {st}",
            f"{'Kvinnonamn' if sv else 'Women’s names'} | {pn(WO)} | {WO[0]} {of} {sum(WO)} {st}",
            f"{'Mansnamn' if sv else 'Men’s names'} | {pn(MA)} | {MA[0]} {of} {sum(MA)} {st}",
            ("Källa: personnamn på minst tre svenska vikingatida runstenar (Samnordisk runtextdatabas) mot SCB:s tilltalsnamn "
             "31 december 2020; Vitkis räkning." if sv else
             "Source: personal names on at least three Swedish Viking-age runestones (Scandinavian Runic-text Data Base) "
             "against Statistics Sweden's first names, 31 December 2020; Vitki's count.")]
    return "\n".join(rows) + "\n:::"


def chart_words(lang):
    sv = lang == "sv"
    t = W["W1"]["table"]
    r = W["description_rank_only"]["table"][0]
    rows = [":::chart Runstenarnas ord som lever kvar med samma betydelse" if sv else
            ":::chart The runestones' words that live on with the same meaning",
            f"+{'Rang och följe' if sv else 'Rank and following'} | {pc(r[0] / sum(r))} | {r[0]} {'av' if sv else 'of'} {sum(r)} {'ord' if sv else 'words'}",
            f"{'Makt, lag och tro' if sv else 'Power, law and faith'} | {pc(t[0][0] / sum(t[0]))} | {t[0][0]} {'av' if sv else 'of'} {sum(t[0])}",
            f"{'Släkt och vardag' if sv else 'Kin and everyday life'} | {pc(t[1][0] / sum(t[1]))} | {t[1][0]} {'av' if sv else 'of'} {sum(t[1])}",
            ("Källa: ord på minst tre runstenar, kodade efter dagens betydelse i svenska Wiktionary; Vitkis räkning." if sv else
             "Source: words on at least three runestones, coded by their present meaning in the Swedish Wiktionary; Vitki's count.")]
    return "\n".join(rows) + "\n:::"


title = "Tor föll, hjälten blev dräng – vilka vikinganamn lever kvar?"
summary = (f"Var femte namn på runstenarna bärs fortfarande av svenskar – och namnen med en gud i har klarat sig bäst. "
           f"Men orden för vikingatidens makt försvann eller sjönk: av nio ord för rang och följe lever två.")

body = f"""Nästan tusen år efter att de sista runstenarna restes heter {sp(K['Torsten'])} svenskar Torsten, {sp(K['Torbjörn'])} Torbjörn och {sp(K['Ingrid'])} Ingrid. Tor föll när kristendomen kom. Hans namn gjorde det inte.

{thor('sv')}

Det är en av få saker som har överlevt från vikingatiden i vardagen: namnen. Vi ville veta hur många – och om det är slump vilka. Vår hypotes var att det som hörde makten till inte överlevde. Den gamla eliten, dess titlar, dess lag och dess gudar borde ha ersatts av kyrkans och kungamaktens ord, medan familjens vardag levde vidare. Halva hypotesen höll. Den andra halvan föll – åt ett håll vi inte väntade oss.

:::box Kort sagt
- Vi jämförde de {N['n_names']} personnamn som står på minst tre svenska runstenar med vilka förnamn svenskar bär i dag. {N['alive']} av dem – vart femte – bärs av minst tio personer.
- Namnen med en gud i, som Torsten, Torbjörn, Åsa och Ingrid, lever dubbelt så ofta som andra. De hedniska namnen trängdes inte undan.
- Orden för vikingatidens makt gick sämre. Av nio ord för rang och följe lever två: *kung* och *styrman*. *Drengr*, hjälten, blev *dräng*.
- Kristnandet bytte ut maktens språk men lät familjernas namn vara.
:::

## Vart femte namn lever

Runstenarna är fulla av namn: de som reste stenen, de döda, ibland ristaren. Vi tog alla personnamn som står på minst tre svenska runstenar – {N['n_names']} namn – och översatte dem till nutida form: Þorsteinn blir Torsten, Ásbjôrn Esbjörn, Sveinn Sven. Sedan jämförde vi med Statistiska centralbyråns lista över förnamn som minst tio svenskar bär.

{N['alive']} av namnen lever i dag – {pc(N['share'])} procent. Räknar man efter hur vanliga de var på stenarna blir det {pc(N['bearer_weighted'])} procent, eftersom de vanligaste namnen oftare har överlevt. Ulf, som tog tre gälder i England, har {sp(K['Ulf'])} namnar i dag.


Kunganamnen klarade sig nästan alla: Erik ({sp(K['Erik'])} bärare), Björn ({sp(K['Björn'])}), Sven ({sp(K['Sven'])}), Håkan ({sp(K['Håkan'])}), Knut ({sp(K['Knut'])}) och Harald ({sp(K['Harald'])}). Men de flesta namnen dog. Önund, Ingefast, Freysten, Holmsten, Holmfast, Gudfast och Vebjörn stod på många runstenar och bärs av färre än tio svenskar i dag.

## Gudarna fick behålla namnen

Om makthypotesen stämde borde namnen med en hednisk gud i ha försvunnit först. Det är tvärtom. Namn som börjar på Tor-, Ås-, Frey-, Ingi- eller Gud- lever i {pn(TH)} procent av fallen, övriga namn i {pn(TO)} procent. Skillnaden är så stor att den skulle uppstå av en slump i färre än ett fall av tusen.

{chart('sv')}

Torsten, Torbjörn ({sp(K['Torbjörn'])} bärare), Tore ({sp(K['Tore'])}), Tord ({sp(K['Tord'])}), Ingvar ({sp(K['Ingvar'])}), Ingrid och Åsa ({sp(K['Åsa'])}) – alla bär de en gud eller ordet för gud. Kyrkan tog bort Tor ur kulten men inte ur namnen.

Och kvinnorna? Vi väntade oss att kvinnonamnen skulle ha klarat sig sämre, eftersom kvinnorna i de medeltida breven oftare bar kristna namn än männen. Det är tvärtom här också: {pn(WO)} procent av kvinnonamnen lever, mot {pn(MA)} procent av männens. Det har vi inte prövat i förväg, så det är en iakttagelse att pröva vidare, inte ett resultat.

En del av förklaringen är att många namn har återupplivats. Av de {CH['in_letters']} runstensnamn som också finns i de medeltida breven 1350–1450 lever {CH['in_letters_alive']} – tre av fyra. Av de {CH['not_in_letters']} som inte finns där lever bara {CH['not_in_letters_alive']}. Namn som Åsa, Tora och Runa verkar alltså ha varit borta i medeltiden och kommit tillbaka med 1800- och 1900-talens intresse för fornnordiskt.

## Hjälten blev dräng

Med orden för makt är det annorlunda. Vi tog orden som står på minst tre runstenar och kontrollerade om de finns i dagens svenska med samma betydelse. Av orden för släkt och vardag – sten, bro, väg, far, mor, bror, son – lever {W['W1']['table'][1][0]} av {sum(W['W1']['table'][1])}. Av orden för makt, lag och tro lever {W['W1']['table'][0][0]} av {sum(W['W1']['table'][0])}.

{chart_words('sv')}

Och bland orden för rang och följe lever bara två av nio: *kung* och *styrman*. *Þegn*, mannen med ställning och gård, finns inte i svenskan. Inte heller *húskarl*, hövdingens livvakt, *lið*, följet, eller *félagi*, kamraten som delade skepp och byte. *Dróttinn*, herren, lever bara i *drottning*.

{photo('Sö 179', '*' + Q['Sö 179'] + '* Tola reste stenen efter sin son Harald, Ingvars bror. De for som drängar, långt efter guld (Sö 179, Gripsholm). *Drængila* betydde tappert, som en hjälte.', 'sv')}

Det tydligaste exemplet är *drengr*. På runstenarna är det en hedersbeteckning: Ingvars män for *drængila*, som riktiga drängar – modigt, som hjältar. I dag är en dräng en anställd på bondgården, och i överförd mening en medlöpare. Ordet för hjälten blev ordet för tjänaren.

Kyrkans ord gick det däremot bra för. Gud, själ, ande och helig står redan på runstenarna och lever alla. Det var inte tron som saknade ord, det var den gamla eliten. Under medeltiden fick makten nya namn: hertig och greve, riddare och adel, biskop och präst – ord som kom med kyrkan och från Tyskland.

## Så säkra är vi

:::box Så säkra är vi
- **Det vi visar:** att vart femte namn på runstenarna lever i dag, att namnen med en gud i har klarat sig dubbelt så bra som andra, och att orden för makt har överlevt sämre än orden för vardag. Planen låstes innan vi räknade.
- **Det vi tror:** att kristnandet bytte ut maktens språk men lät familjernas namnskick vara.
- **Det vi inte kan visa:** att kvinnonamnen klarade sig bättre – det gick åt andra hållet mot vad vi väntade, så det är en iakttagelse. Vi kan inte heller säga hur många namn som levt hela vägen och hur många som återupplivats.
- **Svagheterna:** namnen är översatta till nutida form med regler, och tio träffar där ett modernt namn bara råkar se likadant ut – som Elif och Hera – är borttagna för hand. Ordens betydelse är vår bedömning, med Wiktionary som belägg. Maktens ord är få, och kungar och jarlar nämns nästan aldrig på runstenarna.
:::

:::box Det viktigaste i korthet
- Namnen är en av få saker som har levt vidare från vikingatiden – vart femte runstensnamn bärs fortfarande.
- Gudarna fick behålla namnen: Tor försvann ur kulten men lever i Torsten, Torbjörn och Tore.
- Maktens ord gick sämre. Vikingatidens titlar försvann eller sjönk, och den nya tidens makt fick nya ord.
- Heter du Torsten, Åsa eller Ulf? Då bär du ett namn som stod på en runsten för tusen år sedan.
:::

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Statistiska centralbyrån, Tilltalsnamn med minst 10 bärare bland folkbokförda 31 december (BE0001TNamn10), 2020.
- Svenskt diplomatariums huvudkartotek (SDHK), Riksarkivet: personnamn i breven 1350–1450.
- Wiktionary (svenska), uppslagen för ordens nutida betydelse.
- Vitkis räkning, den låsta analysplanen och alla matchningar ligger öppet på [GitHub](https://github.com/Precatio/runes).
- Foton: Wikimedia Commons, med fotograf och licens i bildtexterna."""

title_en = "Thor fell, the hero became a farmhand – which Viking names live on?"
summary_en = ("One in five names on the runestones is still borne by Swedes – and the names with a god in them have fared "
              "best. But the words for Viking-age power vanished or sank: of nine words for rank and following, two live on.")

body_en = f"""Almost a thousand years after the last runestones were raised, {en(K['Torsten'])} Swedes are called Torsten, {en(K['Torbjörn'])} Torbjörn and {en(K['Ingrid'])} Ingrid. Thor fell when Christianity came. His name did not.

{thor('en')}

It is one of few things from the Viking Age that have survived in everyday life: the names. We wanted to know how many – and whether it is chance which ones. Our hypothesis was that what belonged to power did not survive. The old elite, its titles, its law and its gods ought to have been replaced by the words of the church and the crown, while the everyday life of the family lived on. Half of the hypothesis held. The other half failed – in a direction we did not expect.

:::box In short
- We compared the {N['n_names']} personal names that stand on at least three Swedish runestones with the first names Swedes bear today. {N['alive']} of them – one in five – are borne by at least ten people.
- The names with a god in them, like Torsten, Torbjörn, Åsa and Ingrid, live on twice as often as others. The pagan names were not pushed out.
- The words for Viking-age power fared worse. Of nine words for rank and following, two live on: *kung* (king) and *styrman* (helmsman). *Drengr*, the hero, became *dräng*, the farmhand.
- Christianisation replaced the language of power but left the families' names alone.
:::

## One name in five lives on

The runestones are full of names: those who raised the stone, the dead, sometimes the carver. We took every personal name that stands on at least three Swedish runestones – {N['n_names']} names – and translated them into their present form: Þorsteinn becomes Torsten, Ásbjôrn Esbjörn, Sveinn Sven. Then we compared them with Statistics Sweden's list of first names that at least ten Swedes bear.

{N['alive']} of the names live on today – {pc(N['share'])} per cent. Counting by how common they were on the stones, it is {pc(N['bearer_weighted'])} per cent, since the most common names survived more often. Ulfr, who took three payments in England, has {en(K['Ulf'])} namesakes today.


The kings' names nearly all made it: Erik ({en(K['Erik'])} bearers), Björn ({en(K['Björn'])}), Sven ({en(K['Sven'])}), Håkan ({en(K['Håkan'])}), Knut ({en(K['Knut'])}) and Harald ({en(K['Harald'])}). But most of the names died. Ônundr, Ingifastr, Freysteinn, Holmsteinn, Holmfastr, Guðfastr and Vébjôrn stood on many runestones and are borne by fewer than ten Swedes today.

## The gods kept their names

If the power hypothesis were right, the names with a pagan god in them ought to have vanished first. It is the other way round. Names beginning with Þór-, Ás-, Frey-, Ingi- or Guð- live on in {pn(TH)} per cent of cases, other names in {pn(TO)} per cent. The difference is so large that it would arise by chance in fewer than one case in a thousand.

{chart('en')}

Torsten, Torbjörn ({en(K['Torbjörn'])} bearers), Tore ({en(K['Tore'])}), Tord ({en(K['Tord'])}), Ingvar ({en(K['Ingvar'])}), Ingrid and Åsa ({en(K['Åsa'])}) – all of them carry a god or the word for god. The church took Thor out of the cult but not out of the names.

And the women? We expected women's names to have fared worse, since women in the medieval charters more often bore Christian names than men did. Here, too, it is the other way round: {pn(WO)} per cent of the women's names live on, against {pn(MA)} per cent of the men's. We did not test that in advance, so it is an observation to test further, not a result.

Part of the explanation is that many names have been revived. Of the {CH['in_letters']} runestone names that also appear in the medieval charters of 1350–1450, {CH['in_letters_alive']} live on – three in four. Of the {CH['not_in_letters']} that do not appear there, only {CH['not_in_letters_alive']} do. Names like Åsa, Tora and Runa thus seem to have been gone in the Middle Ages and to have come back with the interest in all things Old Norse in the 19th and 20th centuries.

## The hero became a farmhand

The words for power are another matter. We took the words that stand on at least three runestones and checked whether they exist in today's Swedish with the same meaning. Of the words for kin and everyday life – stone, bridge, road, father, mother, brother, son – {W['W1']['table'][1][0]} of {sum(W['W1']['table'][1])} live on. Of the words for power, law and faith, {W['W1']['table'][0][0]} of {sum(W['W1']['table'][0])} do.

{chart_words('en')}

And among the words for rank and following only two of nine live on: *kung* and *styrman*. *Þegn*, the man of standing with a farm of his own, does not exist in Swedish. Nor does *húskarl*, the chieftain's bodyguard, *lið*, the following, or *félagi*, the comrade who shared ship and spoils. *Dróttinn*, the lord, lives on only in *drottning*, queen.

{photo('Sö 179', '*' + Q['Sö 179'] + '* Tóla raised the stone in memory of her son Haraldr, Ingvarr’s brother. They travelled like heroes, far for gold (Sö 179, Gripsholm). *Drængila* meant valiantly, like a hero.', 'en')}

The clearest example is *drengr*. On the runestones it is a title of honour: Ingvarr's men travelled *drængila*, like true *drengir* – bravely, like heroes. Today a *dräng* is a hired hand on the farm, and figuratively a henchman. The word for the hero became the word for the servant.

The church's words, by contrast, fared well. God, soul, spirit and holy already stand on the runestones and all live on. It was not the faith that lacked words, it was the old elite. In the Middle Ages power got new names: *hertig* and *greve* (duke and count), *riddare* and *adel* (knight and nobility), *biskop* and *präst* (bishop and priest) – words that came with the church and from Germany.

## How sure we are

:::box How sure we are
- **What we show:** that one name in five on the runestones lives on today, that names with a god in them have fared twice as well as others, and that the words for power have survived less well than the words for everyday life. The plan was locked before we counted.
- **What we believe:** that Christianisation replaced the language of power but left the families' naming customs alone.
- **What we cannot show:** that women's names fared better – it went the opposite way to what we expected, so it is an observation. Nor can we say how many names lived all the way and how many were revived.
- **The weaknesses:** the names are translated into present form by rules, and ten hits where a modern name merely looks the same – like Elif and Hera – were removed by hand. The words' meaning is our judgement, with Wiktionary as evidence. The words of power are few, and kings and jarls are almost never named on the runestones.
:::

:::box The essentials in brief
- Names are one of the few things that have lived on from the Viking Age – one runestone name in five is still borne.
- The gods kept their names: Thor vanished from the cult but lives on in Torsten, Torbjörn and Tore.
- The words of power fared worse. The Viking-age titles vanished or sank, and the power of the new age got new words.
- Are you called Torsten, Åsa or Ulf? Then you bear a name that stood on a runestone a thousand years ago.
:::

## Sources

- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Statistics Sweden, First names with at least 10 bearers among the registered population on 31 December (BE0001TNamn10), 2020.
- Svenskt diplomatariums huvudkartotek (SDHK), Swedish National Archives: personal names in the charters 1350–1450.
- Wiktionary (Swedish), the entries for the words' present meaning.
- Vitki's count, the locked analysis plan and all matches are open on [GitHub](https://github.com/Precatio/runes).
- Photos: Wikimedia Commons, with photographer and licence in the captions."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"

out = {"slug": "tor-foll-hjalten-blev-drang", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Språk och stavning", "Tro och magi"]}
path = os.path.join(ROOT, "utdata", "blogg", "overlevde.json")
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
                 "topic": "Forskning|namn", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
