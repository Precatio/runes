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
assert (N["n_names"], N["alive"]) == (391, 85) and pc(N["share"]) == 22 and pc(N["bearer_weighted"]) == 37
TH, TO = N["N2"]["a"], N["N2"]["b"]
assert (TH, TO) == ([22, 34], [63, 272]) and N["N2"]["holm"] < 0.003
HELGI = next(int(r["stones"]) for r in __import__("csv").DictReader(open(os.path.join(O, "namn.csv"), encoding="utf-8")) if r["name"] == "Helgi")
assert HELGI == 14
ONE_IN = int(1 / N["N2"]["p"]) // 100 * 100  # "i ungefär ett fall av sjuhundra"
assert ONE_IN == 700
WO, MA = N["N1"]["a"], N["N1"]["b"]
assert (WO, MA) == ([20, 41], [65, 265])
CH = N["chain"]
assert (CH["in_letters"], CH["in_letters_alive"], CH["not_in_letters"], CH["not_in_letters_alive"]) == (60, 44, 331, 41)
assert (NX["n_names"], NX["alive"]) == (385, 88)
N_FALSE = len(NX["false_hits"])
assert N_FALSE == 15
assert W["W1"]["table"] == [[9, 8], [23, 4]] and W["W1"]["p"] < 0.025
assert W["description_rank_only"]["table"][0] == [2, 7]
BY = W["by_domain"]
assert BY["makt"]["lever"] == ["konungr", "styrimaðr"] and BY["makt"]["ändrad"] == ["drengr"]
assert set(BY["makt"]["borta"]) == {"þegn", "húskarl", "lið", "dróttinn", "félagi", "sveinn (följesman)"}
K = {k: SCB[k] for k in ("Helge", "Rune", "Kåre", "Torsten", "Torbjörn", "Tore", "Tord", "Ingrid", "Ingvar", "Åsa", "Erik", "Björn", "Sven",
                         "Håkan", "Knut", "Harald", "Ulf", "Gunnar")}
assert (K["Torsten"], K["Ulf"], K["Erik"], K["Ingrid"]) == (3540, 31585, 55968, 40300)
pn = lambda a: pc(a[0] / sum(a))  # noqa: E731
DEAD = {x["name"] for x in N["top_dead"]}
assert {"Ônundr", "Ingifastr", "Freysteinn", "Holmsteinn", "Holmfastr", "Guðfastr", "Vébjôrn"} <= DEAD

# ---- the titles and the areas (descriptive, after the locked plan: utdata/overlevde/politik_analys.py) -----------------
P = json.load(open(os.path.join(O, "politik.json"), encoding="utf-8"))
PT, PA = P["titles"], P["areas"]
assert P["n_titles"] == 16 and {c: PT[c]["n"] for c in PT} == {"lever": 4, "sjönk": 1, "historisk": 6, "borta": 5}
assert PT["lever"]["words"] == ["konungr", "styrimaðr", "skipari", "þingstaðr"]
assert set(PT["borta"]["words"]) == {"þegn", "landmaðr", "hersir", "þingalið", "liðs forungi"}
assert set(PT["historisk"]["words"]) == {"jarl", "stallari", "bryti", "húskarl", "hundari", "dróttinn"}
TS = P["title_stones"]
assert (TS["þegn"], TS["jarl"], TS["húskarl"]) == (21, 2, 3)
THEGN_VG = 18  # þegn stones in Västergötland (politik_kodning.csv: 18 Vg, 2 Sm, 1 Ög)
assert sum(1 for x in next(r for r in json.load(open(os.path.join(O, "politik_underlag.json"), encoding="utf-8"))["titles"]
                           if r["lemma"] == "þegn")["stones"] if x.startswith("Vg ")) == THEGN_VG
LOANS = P["new"]["lån"]
assert LOANS == ["hertig", "greve", "marsk", "fogde", "riddare", "kansler", "riksdag", "biskop", "präst"]
assert P["new"]["nordiskt"] == ["frälse", "härad", "lagman", "socken", "ledung", "adel"]
assert P["n_areas"] == 22 and P["area_any_stones"] == 91
assert {c: (PA[c]["n"], PA[c]["stones"]) for c in PA} == {"samma": (11, 44), "historisk": (2, 4), "bytt": (9, 45)}
AS = P["area_stones"]
assert (AS["Grikkland / Grikkir"], AS["Svíþjóð"], AS["Garðar"], AS["Serkland"]) == (24, 2, 6, 6)
nz = lambda s: recs[s]["normalization"].replace('"', "")  # noqa: E731
for s in ("Sö 140", "Sö Fv1948;289"):
    assert "Sveþiuðu" in nz(s) and "Ludgo" in recs[s]["parish"]
assert "æinn atti allt hu[n]dari þetta" in nz("U 212")
assert "stallara HakonaR iarls" in nz("Sm 76") and "HakonaR iarls" in nz("U 617")
assert "skipari Haralds kunungs" in nz("Sm 42") and "huskarl SigrøðaR" in nz("U 335")
assert "liðs forungi, landmanna bæztr" in nz("Sö 338") and "i þingaliði" in nz("U 668")
assert "sotti IorsaliR" in nz("U 136")
pt = lambda c: pc(PT[c]["n"] / P["n_titles"])  # noqa: E731
# numbers that open a sentence are written out
W_SV = {2: "Två", 4: "Fyra", 5: "Fem", 6: "Sex", 9: "Nio", 11: "Elva"}
W_EN = {2: "Two", 4: "Four", 5: "Five", 6: "Six", 9: "Nine", 11: "Eleven"}

Q = {s: recs[s]["normalization"].strip().replace('"', "") for s in ("Sö 179", "U 344")}
assert "foru drængila" in Q["Sö 179"]
assert Q["U 344"].startswith("En UlfR hafiR a Ænglandi þry giald takit.")
Q["U 344"] = Q["U 344"].split(". ")[0] + "."  # the first sentence: Ulfr's three payments

# ---- photographs ------------------------------------------------------------------------------------------------------
FILES = commons.wikidata_files(["Sö 179", "U 344"])
THOR = "Lorenz Frølich - Æsir-Thor - NMH 425-1925 - Nationalmuseum.jpg"
CARTA = "Carta Marina.jpeg"
INFO = commons.commons_info(list(FILES.values()) + [THOR, CARTA])
assert INFO[THOR]["licence"] == "Public domain" and "Frølich" in INFO[THOR]["author"]
assert INFO[CARTA]["licence"] == "Public domain" and INFO[CARTA]["author"] == "Olaus Magnus"


def carta(lang):
    page = "https://commons.wikimedia.org/wiki/File:" + CARTA.replace(" ", "_")
    if lang == "sv":
        return (f"![Olaus Magnus Carta marina]({INFO[CARTA]['thumb']})\nNorden när de medeltida rikena var färdiga: Olaus "
                f"Magnus Carta marina, tryckt i Venedig 1539. Fri från upphovsrätt, via [Wikimedia Commons]({page}).")
    return (f"![Olaus Magnus' Carta marina]({INFO[CARTA]['thumb']})\nThe North once the medieval realms were complete: "
            f"Olaus Magnus' Carta marina, printed in Venice in 1539. Public domain, via [Wikimedia Commons]({page}).")


def chart_titles(lang):
    sv = lang == "sv"
    n = P["n_titles"]
    of = "av" if sv else "of"
    rows = [":::chart Vad hände med runstenarnas titlar och ämbetsord" if sv else
            ":::chart What became of the runestones' titles and offices",
            f"+{'Lever med samma innebörd' if sv else 'Live on with the same meaning'} | {pt('lever')} | {PT['lever']['n']} {of} {n}: "
            + ("kung, styrman, skeppare, ting" if sv else "king, helmsman, skipper, thing"),
            f"{'Sjönk' if sv else 'Sank'} | {pt('sjönk')} | {PT['sjönk']['n']} {of} {n}: " + ("dräng" if sv else "drengr → dräng, farmhand"),
            f"{'Bara som historisk term' if sv else 'Only as a historical term'} | {pt('historisk')} | {PT['historisk']['n']} {of} {n}: "
            "jarl, stallare, bryte, huskarl, hundare, drott",
            f"{'Borta' if sv else 'Gone'} | {pt('borta')} | {PT['borta']['n']} {of} {n}: þegn, landmaðr, hersir, þingalið, forungi",
            ("Källa: titlar och ämbetsord på svenska vikingatida runstenar (Samnordisk runtextdatabas), följda till dagens "
             "svenska med Wiktionary och Wikipedia som belägg; Vitkis genomgång." if sv else
             "Source: titles and words for office on Swedish Viking-age runestones (Scandinavian Runic-text Data Base), "
             "followed into today's Swedish with Wiktionary and Wikipedia as evidence; Vitki's review.")]
    return "\n".join(rows) + "\n:::"


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
           f"Men vikingatidens makt bytte ord: jarlen blev hertig, hundaret härad och Svitjod Sverige, medan tinget och "
           f"lagmannen fick behålla sina nordiska namn.")

body = f"""Nästan tusen år efter att de sista runstenarna restes heter {sp(K['Torsten'])} svenskar Torsten, {sp(K['Torbjörn'])} Torbjörn och {sp(K['Ingrid'])} Ingrid. Tor föll när kristendomen kom. Hans namn gjorde det inte.

{thor('sv')}

Det är en av få saker som har överlevt från vikingatiden i vardagen: namnen. Vi ville veta hur många – och om det är slump vilka. Vår hypotes var att det som hörde makten till inte överlevde. Den gamla eliten, dess titlar, dess lag och dess gudar borde ha ersatts av kyrkans och kungamaktens ord, medan familjens vardag levde vidare. Halva hypotesen höll. Den andra halvan föll – åt ett håll vi inte väntade oss.

:::box Kort sagt
- Vi jämförde de {N['n_names']} personnamn som står på minst tre svenska runstenar med vilka förnamn svenskar bär i dag. {N['alive']} av dem – vart femte – bärs av minst tio personer.
- Namnen med en gud i, som Torsten, Torbjörn, Åsa och Ingrid, lever dubbelt så ofta som andra. De hedniska namnen trängdes inte undan.
- Orden för vikingatidens makt gick sämre. Av nio ord för rang och följe lever två: *kung* och *styrman*. *Drengr*, hjälten, blev *dräng*.
- Av runstenarnas {P['n_titles']} titlar och ämbetsord lever {PT['lever']['n']} med samma innebörd. Kronans nya män under medeltiden fick lånade titlar – hertig, greve, marsk, fogde – medan bygdens ting, härad och lagman behöll nordiska namn.
- Kartan bytte också namn. {W_SV[PA['bytt']['n']]} av de {P['n_areas']} länder och platser som runstenarna nämner heter något annat i dag eller finns inte längre: Gårdarike, Grikkland, Serkland – och Svitjod, som blev Sverige.
- Kristnandet och kungamakten bytte ut maktens språk men lät familjernas namn vara.
:::

## Vart femte namn lever

Runstenarna är fulla av namn: de som reste stenen, de döda, ibland ristaren. Vi tog alla personnamn som står på minst tre svenska runstenar – {N['n_names']} namn – och översatte dem till nutida form: Þorsteinn blir Torsten, Ásbjôrn Esbjörn, Sveinn Sven. Sedan jämförde vi med Statistiska centralbyråns lista över förnamn som minst tio svenskar bär.

{N['alive']} av namnen lever i dag – {pc(N['share'])} procent. Räknar man efter hur vanliga de var på stenarna blir det {pc(N['bearer_weighted'])} procent, eftersom de vanligaste namnen oftare har överlevt. Ulf, som tog tre gälder i England, har {sp(K['Ulf'])} namnar i dag. Helgi står på {HELGI} runstenar och heter i dag Helge ({sp(K['Helge'])} bärare); Rúni är Rune ({sp(K['Rune'])}) och Kári är Kåre ({sp(K['Kåre'])}).


Kunganamnen klarade sig nästan alla: Erik ({sp(K['Erik'])} bärare), Björn ({sp(K['Björn'])}), Sven ({sp(K['Sven'])}), Håkan ({sp(K['Håkan'])}), Knut ({sp(K['Knut'])}) och Harald ({sp(K['Harald'])}). Men de flesta namnen dog. Önund, Ingefast, Freysten, Holmsten, Holmfast, Gudfast och Vebjörn stod på många runstenar och bärs av färre än tio svenskar i dag.

## Gudarna fick behålla namnen

Om makthypotesen stämde borde namnen med en hednisk gud i ha försvunnit först. Det är tvärtom. Namn som börjar på Tor-, Ås-, Frey-, Ingi- eller Gud- lever i {pn(TH)} procent av fallen, övriga namn i {pn(TO)} procent. Skillnaden är så stor att den skulle uppstå av en slump i ungefär ett fall av sjuhundra.

{chart('sv')}

Torsten, Torbjörn ({sp(K['Torbjörn'])} bärare), Tore ({sp(K['Tore'])}), Tord ({sp(K['Tord'])}), Ingvar ({sp(K['Ingvar'])}), Ingrid och Åsa ({sp(K['Åsa'])}) – alla bär de en gud eller ordet för gud. Kyrkan tog bort Tor ur kulten men inte ur namnen.

Och kvinnorna? Vi väntade oss att kvinnonamnen skulle ha klarat sig sämre, eftersom kvinnorna i de medeltida breven oftare bar kristna namn än männen. Det är tvärtom här också: {pn(WO)} procent av kvinnonamnen lever, mot {pn(MA)} procent av männens. Det har vi inte prövat i förväg, så det är en iakttagelse att pröva vidare, inte ett resultat.

En del av förklaringen är att många namn har återupplivats. Av de {CH['in_letters']} runstensnamn som också finns i de medeltida breven 1350–1450 lever {CH['in_letters_alive']} – tre av fyra. Av de {CH['not_in_letters']} som inte finns där lever bara {CH['not_in_letters_alive']}. Namn som Åsa, Tora och Runa verkar alltså ha varit borta i medeltiden och kommit tillbaka med 1800- och 1900-talens intresse för fornnordiskt.

## Hjälten blev dräng

Med orden för makt är det annorlunda. Vi tog orden som står på minst tre runstenar och kontrollerade om de finns i dagens svenska med samma betydelse. Av orden för släkt och vardag – sten, bro, väg, far, mor, bror, son – lever {W['W1']['table'][1][0]} av {sum(W['W1']['table'][1])}. Av orden för makt, lag och tro lever {W['W1']['table'][0][0]} av {sum(W['W1']['table'][0])}.

{chart_words('sv')}

Och bland orden för rang och följe lever bara två av nio: *kung* och *styrman*. *Þegn*, mannen med ställning och gård, finns inte i svenskan. Inte heller *húskarl*, hövdingens livvakt, *lið*, följet, eller *félagi*, kamraten som delade skepp och byte. *Dróttinn*, herren, lever bara i *drottning* – och på runstenarna används det redan bara om Gud.

{photo('Sö 179', '*' + Q['Sö 179'] + '* Tola reste stenen efter sin son Harald, Ingvars bror. De for som drängar, långt efter guld (Sö 179, Gripsholm). *Drængila* betydde tappert, som en hjälte.', 'sv')}

Det tydligaste exemplet är *drengr*. På runstenarna är det en hedersbeteckning: Ingvars män for *drængila*, som riktiga drängar – modigt, som hjältar. I dag är en dräng en anställd på bondgården, och i överförd mening en medlöpare. Ordet för hjälten blev ordet för tjänaren.

Kyrkans ord gick det däremot bra för. Gud, själ, ande och helig står redan på runstenarna och lever alla. Det var inte tron som saknade ord, det var den gamla eliten.

## Kungens män fick nya titlar

Runstenarna handlar inte bara om familjer. De handlar också om makt: vem som var någons man, vem som styrde skeppet, var tinget hölls. Vi gick därför igenom alla titlar och ämbetsord som står på svenska runstenar – {P['n_titles']} stycken – och följde dem fram till dagens svenska. Den genomgången gjorde vi efter den låsta planen, så den beskriver men prövar inget.

{chart_titles('sv')}

{W_SV[PT['lever']['n']]} lever med samma innebörd: kung, styrman, skeppare och ting. *Drengr* sjönk till dräng. {W_SV[PT['historisk']['n']]} finns bara kvar som historiska termer: jarl, stallare, bryte, huskarl, hundare och drott. {W_SV[PT['borta']['n']]} är helt borta: *þegn*, *landmaðr*, *hersir*, *þingalið* och *liðs forungi*.

Det som klarade sig är kungen och skeppet. Det som försvann är följet – orden för männen i en hövdings tjänst. Och titlarna står nästan alltid med en herre. Assur var *skipari Haralds kunungs*, kung Haralds skeppare (Sm 42, Tuna i Småland). Vrái var *stallari Hákonar jarls*, Håkon jarls stallare (Sm 76, Komstad). Hæra var Sigröds huskarl (U 335, Orkesta). Makten på runstenarna är personlig: man var någons man.

*Þegn* står på {TS['þegn']} stenar, {THEGN_VG} av dem i Västergötland, där "en mycket god tegn" är ett av de vanligaste sätten att hedra en död. Ordet lever i engelskans *thane* men inte i svenskan. På stenen vid Turinge kyrka i Södermanland (Sö 338) får Torsten nästan hela ordförrådet på en gång. Han föll i Gårdarike som *liðs forungi*, följets anförare, och *landmanna bæztr*, den bäste av landets män, och bröderna höll sina huskarlar väl. Inget av de orden finns kvar i svenskan. Och Geir från Kålsta i Uppland satt "i väster i tingalidet" (U 668) – troligen den danske kungen Knuts garde i England. Ordet dog med gardet.

Jarlen står bara på {TS['jarl']} svenska runstenar, och båda gäller samme man: Håkon jarl, vars stallare Vrái fick en sten i Komstad (Sm 76) och vars son Assur fick en vid Bro kyrka i Uppland (U 617). I Sverige levde jarlämbetet vidare in i medeltiden. Den siste store jarlen var Birger jarl, som dog 1266, och ämbetet avskaffades 1308. Riksjarlen kallades på latin *dux regni*, rikets hertig – och det var just ordet *hertig* som tog över. Det är belagt i svenskan sedan 1285, lånat från lågtyskans *hertoch*. Samma sak hände med Vráis titel. Stallaren, som ledde kungens följe, ersattes under 1200-talet av marsken, ett ord från tyskans *marschalk*.

## Toppen bytte språk, bygden behöll sitt

Titta på orden som makten fick under medeltiden, och på varifrån de kom. Kronans och adelns män fick ord utifrån: hertig, greve, marsk och riddare från lågtyskan, fogde från latinet genom tyskan, kansler från franskan och latinet. Riksdag är en översättning av tyskans *Reichstag*. Biskop och präst kom med kyrkan. Alla {len(LOANS)} är lån.

Bygdens ord är nordiska. Tinget, häradet, lagmannen, socknen och ledungen – den gemensamma plikten att ställa skepp och män – bär alla namn som fanns före kristnandet. Till och med frälset, adelns skattefrihet från Alsnö stadga 1280, har ett nordiskt namn. Och *adel* är ett gammalt nordiskt ord, *aðal*, som fick sin nya mening från tyskan.

Här tolkar vi, och tolkningen är inte prövad: makten byttes uppifrån. Den nya kungamakten och kyrkan tog sina ord från Europa, där de hade lärt sig att styra. Bönderna fortsatte att samlas till ting i sina härad, och de orden behövde ingen byta ut.

Vikingatidens egna indelningar gick sämre. Jarlabanke lät hugga på sin sten vid Vallentuna kyrka (U 212) att han gjorde tingsplatsen och *æinn atti allt hundari þetta* – ensam ägde hela detta hundare. Hundaret var Svealands gamla indelning, knuten till ledungen. Under unionstiden trängdes ordet undan av *härad*, som redan användes i Götaland och Danmark. Upplands tre folkland – Tiundaland, Attundaland och Fjädrundaland – blev ett landskap, Uppland, med Upplandslagen 1296.

Ibland gick staten tillbaka till de gamla orden. När häradsrätterna och rådhusrätterna ersattes 1971 fick de nya domstolarna heta tingsrätter, och deras ordförande fick den fornnordiska titeln lagman. Dittills hade de hetat häradshövdingar. Vikingarnas ting dömer alltså fortfarande.

## Gårdarike blev Ryssland – och Svitjod blev Sverige

Samma mönster syns på kartan. Runstenarna nämner {P['n_areas']} länder, folk och platser utanför den egna bygden, på sammanlagt {P['area_any_stones']} stenar. {W_SV[PA['samma']['n']]} har samma namn i dag: England, Danmark, Gotland, Skåne, Estland, Finland, Tavastland och några till. {W_SV[PA['historisk']['n']]} finns bara som historiska landskap, Wierland och Livland i Baltikum. Men {PA['bytt']['n']} har bytt namn eller finns inte längre – och de står på {PA['bytt']['stones']} stenar, ungefär hälften.

{carta('sv')}

Det är de stora rikena långt österut och söderut. *Garðar*, Gårdarike, var Kievriket, som blev grunden till Ryssland, Belarus och Ukraina; *Holmgarðr* är Novgorod. *Grikkland*, som står på {AS['Grikkland / Grikkir']} stenar, är inte dagens Grekland utan det bysantinska kejsardömet. *Langbarðaland* är Italien – namnet lever bara i Lombardiet. *Serkland*, landen kring Kaspiska havet och kalifatet, har inget nutida namn alls. Rikena föll eller byggdes om, och deras nordiska namn föll med dem.

Ett namn bytte kyrkan ut. Östen, som Astrid reste stenen efter i Broby i Täby (U 136), *sotti IorsaliR* – sökte sig till Jórsalir – och dog i Grikkland. Vikingarna hade ett eget namn på Jerusalem. Det försvann när Bibelns namn tog över.

Och Sverige självt. *Sveþiuð*, Svitjod, står på två runstenar, båda i Ludgo socken i Södermanland. På den ena står att ingen ska föda en dugligare son i Svitjod (Sö 140), och på samma sten anropas kanske Tor. På den andra var Astrids söner de duktigaste i Svitjod (Sö Fv1948;289, Aspa bro). Svitjod betyder svearnas folk. Sverige betyder svearnas rike – *Swerike* på 1200-talet, *Svearike* på 1300-talet. På isländska heter landet fortfarande Svíþjóð. Landet bytte namn från ett folk till ett rike, och i det bytet ryms hela den politiska förändringen.

## Så säkra är vi

:::box Så säkra är vi
- **Det vi visar:** att vart femte namn på runstenarna lever i dag, att namnen med en gud i har klarat sig dubbelt så bra som andra, och att orden för makt har överlevt sämre än orden för vardag. Planen låstes innan vi räknade.
- **Det vi tror:** att kristnandet och den nya kungamakten bytte ut maktens språk uppifrån – kronans och kyrkans titlar kom utifrån – men lät familjernas namnskick och bygdens institutioner vara.
- **Det vi inte kan visa:** att kvinnonamnen klarade sig bättre – det gick åt andra hållet mot vad vi väntade, så det är en iakttagelse. Vi kan inte heller säga hur många namn som levt hela vägen och hur många som återupplivats.
- **Svagheterna:** namnen är översatta till nutida form med regler, och {N_FALSE} träffar där ett modernt namn bara råkar se likadant ut eller har ett annat ursprung – som Elif, Hera och Vide – är borttagna för hand. Ordens betydelse är vår bedömning, med Wiktionary som belägg. Maktens ord är få, och kungar och jarlar nämns nästan aldrig på runstenarna.
- **Titlarna och kartan:** genomgången gjordes efter den låsta planen och prövar inget. Många titlar står på en enda sten, och vad varje ord har blivit bygger på Wiktionary och Wikipedia – kodningen ligger öppet med belägg för varje ord. Att lånorden gällde kronan och de nordiska orden bygden är vår läsning av den listan, inte en räkning.
- **Rättat den 30 oktober 2026:** vår regel för att översätta namnen missade att fornnordiska mansnamn på *-i* slutar på *-e* i dag – Helgi är Helge, Rúni är Rune. Med den rättelsen lever {N['alive']} namn i stället för 82, {pc(N['share'])} i stället för 21 procent. Slutsatserna står sig.
- **En rättelse under arbetet:** vår första sökning missade *jarl*, eftersom Rundata stavar ordet *iarl*. Det står på två stenar och når inte gränsen på tre, så ordtestet påverkas inte.
:::

:::box Det viktigaste i korthet
- Namnen är en av få saker som har levt vidare från vikingatiden – vart femte runstensnamn bärs fortfarande.
- Gudarna fick behålla namnen: Tor försvann ur kulten men lever i Torsten, Torbjörn och Tore.
- Makten bytte ord uppifrån. Vikingatidens följe – tegnar, huskarlar, drängar – försvann eller sjönk, kronans nya män fick tyska titlar, men bygdens ting, härad och lagman behöll sina nordiska namn.
- Även kartan och landet bytte namn: Gårdarike blev Ryssland, och Svitjod, svearnas folk, blev Sverige, svearnas rike.
- Heter du Torsten, Åsa eller Ulf? Då bär du ett namn som stod på en runsten för tusen år sedan.
:::

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Statistiska centralbyrån, Tilltalsnamn med minst 10 bärare bland folkbokförda 31 december (BE0001TNamn10), 2020.
- Svenskt diplomatariums huvudkartotek (SDHK), Riksarkivet: personnamn i breven 1350–1450.
- Wiktionary (svenska och engelska), uppslagen för ordens nutida betydelse och ursprung.
- Wikipedia (svenska): artiklarna Jarl, Stallare, Bryte, Hundare, Härad, Häradshövding, Tingsrätt, Frälse, Svitjod, Gårdarike, Langbardaland, Särkland och Uppland.
- Vitkis räkning, den låsta analysplanen, genomgången av titlarna och områdena och alla matchningar ligger öppet på [GitHub](https://github.com/Precatio/runes).
- Bilder: Wikimedia Commons, med upphovsperson och licens i bildtexterna."""

title_en = "Thor fell, the hero became a farmhand – which Viking names live on?"
summary_en = ("One in five names on the runestones is still borne by Swedes – and the names with a god in them have fared "
              "best. But Viking-age power changed its words: the jarl became a duke, the hundred a härad and Svitjod Sweden, "
              "while the thing and the lawman kept their Norse names.")

body_en = f"""Almost a thousand years after the last runestones were raised, {en(K['Torsten'])} Swedes are called Torsten, {en(K['Torbjörn'])} Torbjörn and {en(K['Ingrid'])} Ingrid. Thor fell when Christianity came. His name did not.

{thor('en')}

It is one of few things from the Viking Age that have survived in everyday life: the names. We wanted to know how many – and whether it is chance which ones. Our hypothesis was that what belonged to power did not survive. The old elite, its titles, its law and its gods ought to have been replaced by the words of the church and the crown, while the everyday life of the family lived on. Half of the hypothesis held. The other half failed – in a direction we did not expect.

:::box In short
- We compared the {N['n_names']} personal names that stand on at least three Swedish runestones with the first names Swedes bear today. {N['alive']} of them – one in five – are borne by at least ten people.
- The names with a god in them, like Torsten, Torbjörn, Åsa and Ingrid, live on twice as often as others. The pagan names were not pushed out.
- The words for Viking-age power fared worse. Of nine words for rank and following, two live on: *kung* (king) and *styrman* (helmsman). *Drengr*, the hero, became *dräng*, the farmhand.
- Of the runestones' {P['n_titles']} titles and words for office, {PT['lever']['n']} live on with the same meaning. The crown's new men in the Middle Ages got borrowed titles – *hertig*, *greve*, *marsk*, *fogde* – while the local thing, härad and lawman kept Norse names.
- The map changed its names too. {W_EN[PA['bytt']['n']]} of the {P['n_areas']} lands and places named on the runestones are called something else today or no longer exist: Garðar, Grikkland, Serkland – and Svitjod, which became Sverige.
- Christianisation and the new royal power replaced the language of power but left the families' names alone.
:::

## One name in five lives on

The runestones are full of names: those who raised the stone, the dead, sometimes the carver. We took every personal name that stands on at least three Swedish runestones – {N['n_names']} names – and translated them into their present form: Þorsteinn becomes Torsten, Ásbjôrn Esbjörn, Sveinn Sven. Then we compared them with Statistics Sweden's list of first names that at least ten Swedes bear.

{N['alive']} of the names live on today – {pc(N['share'])} per cent. Counting by how common they were on the stones, it is {pc(N['bearer_weighted'])} per cent, since the most common names survived more often. Ulfr, who took three payments in England, has {en(K['Ulf'])} namesakes today. Helgi stands on {HELGI} runestones and is Helge today ({en(K['Helge'])} bearers); Rúni is Rune ({en(K['Rune'])}) and Kári is Kåre ({en(K['Kåre'])}).


The kings' names nearly all made it: Erik ({en(K['Erik'])} bearers), Björn ({en(K['Björn'])}), Sven ({en(K['Sven'])}), Håkan ({en(K['Håkan'])}), Knut ({en(K['Knut'])}) and Harald ({en(K['Harald'])}). But most of the names died. Ônundr, Ingifastr, Freysteinn, Holmsteinn, Holmfastr, Guðfastr and Vébjôrn stood on many runestones and are borne by fewer than ten Swedes today.

## The gods kept their names

If the power hypothesis were right, the names with a pagan god in them ought to have vanished first. It is the other way round. Names beginning with Þór-, Ás-, Frey-, Ingi- or Guð- live on in {pn(TH)} per cent of cases, other names in {pn(TO)} per cent. The difference is so large that it would arise by chance in about one case in seven hundred.

{chart('en')}

Torsten, Torbjörn ({en(K['Torbjörn'])} bearers), Tore ({en(K['Tore'])}), Tord ({en(K['Tord'])}), Ingvar ({en(K['Ingvar'])}), Ingrid and Åsa ({en(K['Åsa'])}) – all of them carry a god or the word for god. The church took Thor out of the cult but not out of the names.

And the women? We expected women's names to have fared worse, since women in the medieval charters more often bore Christian names than men did. Here, too, it is the other way round: {pn(WO)} per cent of the women's names live on, against {pn(MA)} per cent of the men's. We did not test that in advance, so it is an observation to test further, not a result.

Part of the explanation is that many names have been revived. Of the {CH['in_letters']} runestone names that also appear in the medieval charters of 1350–1450, {CH['in_letters_alive']} live on – three in four. Of the {CH['not_in_letters']} that do not appear there, only {CH['not_in_letters_alive']} do. Names like Åsa, Tora and Runa thus seem to have been gone in the Middle Ages and to have come back with the interest in all things Old Norse in the 19th and 20th centuries.

## The hero became a farmhand

The words for power are another matter. We took the words that stand on at least three runestones and checked whether they exist in today's Swedish with the same meaning. Of the words for kin and everyday life – stone, bridge, road, father, mother, brother, son – {W['W1']['table'][1][0]} of {sum(W['W1']['table'][1])} live on. Of the words for power, law and faith, {W['W1']['table'][0][0]} of {sum(W['W1']['table'][0])} do.

{chart_words('en')}

And among the words for rank and following only two of nine live on: *kung* and *styrman*. *Þegn*, the man of standing with a farm of his own, does not exist in Swedish. Nor does *húskarl*, the chieftain's bodyguard, *lið*, the following, or *félagi*, the comrade who shared ship and spoils. *Dróttinn*, the lord, lives on only in *drottning*, queen – and on the runestones it is already used only of God.

{photo('Sö 179', '*' + Q['Sö 179'] + '* Tóla raised the stone in memory of her son Haraldr, Ingvarr’s brother. They travelled like heroes, far for gold (Sö 179, Gripsholm). *Drængila* meant valiantly, like a hero.', 'en')}

The clearest example is *drengr*. On the runestones it is a title of honour: Ingvarr's men travelled *drængila*, like true *drengir* – bravely, like heroes. Today a *dräng* is a hired hand on the farm, and figuratively a henchman. The word for the hero became the word for the servant.

The church's words, by contrast, fared well. God, soul, spirit and holy already stand on the runestones and all live on. It was not the faith that lacked words, it was the old elite.

## The king's men got new titles

The runestones are not only about families. They are also about power: who was whose man, who steered the ship, where the thing was held. So we went through every title and word for office that stands on Swedish runestones – {P['n_titles']} of them – and followed them into today's Swedish. We did that review after the locked plan, so it describes but tests nothing.

{chart_titles('en')}

{W_EN[PT['lever']['n']]} live on with the same meaning: *kung*, *styrman*, *skeppare* and *ting* – king, helmsman, skipper and thing. *Drengr* sank to *dräng*. {W_EN[PT['historisk']['n']]} survive only as historical terms: jarl, stallare, bryte, huskarl, hundare and drott. {W_EN[PT['borta']['n']]} are gone altogether: *þegn*, *landmaðr*, *hersir*, *þingalið* and *liðs forungi*.

What survived is the king and the ship. What vanished is the following – the words for the men in a chieftain's service. And the titles nearly always stand with a lord. Ôzurr was *skipari Haralds kunungs*, King Haraldr's seaman (Sm 42, Tuna in Småland). Vrái was *stallari Hákonar jarls*, Earl Hákon's marshal (Sm 76, Komstad). Hæra was Sigrøðr's housecarl (U 335, Orkesta). Power on the runestones is personal: you were someone's man.

*Þegn* stands on {TS['þegn']} stones, {THEGN_VG} of them in Västergötland, where "a very good thegn" is one of the commonest ways of honouring the dead. The word lives on in English *thane* but not in Swedish. On the stone at Turinge church in Södermanland (Sö 338), Þorsteinn gets nearly the whole vocabulary at once. He fell in Garðar as *liðs forungi*, leader of the retinue, and *landmanna bæztr*, the best of the men of the land, and the brothers held their housecarls well. None of those words remain in Swedish. And Geiri from Kålsta in Uppland "sat in the west in the þingalið" (U 668) – probably the Danish king Knútr's guard in England. The word died with the guard.

The jarl stands on only {TS['jarl']} Swedish runestones, and both concern the same man: Earl Hákon, whose marshal Vrái got a stone at Komstad (Sm 76) and whose son Ôzurr got one at Bro church in Uppland (U 617). In Sweden the office of jarl lived on into the Middle Ages. The last great jarl was Birger jarl, who died in 1266, and the office was abolished in 1308. The jarl of the realm was called *dux regni* in Latin, the duke of the realm – and it was precisely the word *hertig*, duke, that took over. It is attested in Swedish from 1285, borrowed from Low German *hertoch*. The same happened to Vrái's title. The *stallare*, who led the king's following, was replaced in the 13th century by the *marsk*, a word from German *Marschall*.

## The top changed language, the countryside kept its own

Look at the words power acquired in the Middle Ages, and at where they came from. The men of the crown and the nobility got words from outside: *hertig*, *greve*, *marsk* and *riddare* (duke, count, marshal, knight) from Low German, *fogde* (bailiff) from Latin by way of German, *kansler* from French and Latin. *Riksdag* is a translation of German *Reichstag*. *Biskop* and *präst* came with the church. All {len(LOANS)} are loans.

The words of the countryside are Norse. The *ting*, the *härad*, the *lagman*, the *socken* and the *ledung* – the shared duty to provide ships and men – all bear names that existed before Christianisation. Even *frälse*, the nobility's freedom from tax under the Statute of Alsnö in 1280, has a Norse name. And *adel*, nobility, is an old Norse word, *aðal*, that got its new meaning from German.

Here we interpret, and the interpretation is untested: power was replaced from the top. The new royal power and the church took their words from Europe, where they had learned to rule. The farmers went on gathering at the thing in their härad, and nobody needed to replace those words.

The Viking Age's own divisions fared worse. Jarlabanki had it carved on his stone at Vallentuna church (U 212) that he made the assembly place and *æinn atti allt hundari þetta* – alone owned all of this hundred. The hundred was Svealand's old division, tied to the levy. In the Union period the word was pushed aside by *härad*, already in use in Götaland and Denmark. Uppland's three *folkland* – Tiundaland, Attundaland and Fjädrundaland – became one province, Uppland, with the Uppland Law of 1296.

Sometimes the state went back to the old words. When the rural and town courts were replaced in 1971, the new courts were named *tingsrätter*, thing courts, and their presidents got the Old Norse title *lagman*, lawman. Until then they had been called *häradshövding*. The Vikings' thing, in other words, still passes judgement.

## Garðar became Russia – and Svitjod became Sweden

The same pattern shows on the map. The runestones name {P['n_areas']} lands, peoples and places beyond the home district, on {P['area_any_stones']} stones in all. {W_EN[PA['samma']['n']]} have the same name today: England, Denmark, Gotland, Skåne, Estonia, Finland, Tavastia and a few more. {W_EN[PA['historisk']['n']]} exist only as historical regions, Wierland and Livonia in the Baltic. But {PA['bytt']['n']} have changed their name or no longer exist – and they stand on {PA['bytt']['stones']} stones, about half.

{carta('en')}

They are the great realms far to the east and south. *Garðar* was the Kievan realm, which became the foundation of Russia, Belarus and Ukraine; *Holmgarðr* is Novgorod. *Grikkland*, on {AS['Grikkland / Grikkir']} stones, is not today's Greece but the Byzantine Empire. *Langbarðaland* is Italy – the name lives on only in Lombardy. *Serkland*, the lands around the Caspian Sea and the caliphate, has no present-day name at all. The realms fell or were rebuilt, and their Norse names fell with them.

One name was replaced by the church. Øystæinn, in whose memory Æstriðr raised the stone at Broby in Täby (U 136), *sotti IorsaliR* – made his way to Jórsalir – and died in Grikkland. The Vikings had a name of their own for Jerusalem. It vanished when the Bible's name took over.

And Sweden itself. *Sveþiuð*, Svitjod, stands on two runestones, both in Ludgo parish in Södermanland. On one, no one will bear a more able son in Svitjod (Sö 140), and the same stone perhaps calls on Thor. On the other, Ástríðr's sons were the ablest in Svitjod (Sö Fv1948;289, Aspa bridge). Svitjod means the people of the Svear. Sverige means the realm of the Svear – *Swerike* in the 13th century, *Svearike* in the 14th. In Icelandic the country is still called Svíþjóð. The country changed its name from a people to a realm, and that change holds the whole political shift.

## How sure we are

:::box How sure we are
- **What we show:** that one name in five on the runestones lives on today, that names with a god in them have fared twice as well as others, and that the words for power have survived less well than the words for everyday life. The plan was locked before we counted.
- **What we believe:** that Christianisation and the new royal power replaced the language of power from the top – the titles of the crown and the church came from outside – but left the families' naming customs and the local institutions alone.
- **What we cannot show:** that women's names fared better – it went the opposite way to what we expected, so it is an observation. Nor can we say how many names lived all the way and how many were revived.
- **The weaknesses:** the names are translated into present form by rules, and {N_FALSE} hits where a modern name merely looks the same or has another origin – like Elif, Hera and Vide – were removed by hand. The words' meaning is our judgement, with Wiktionary as evidence. The words of power are few, and kings and jarls are almost never named on the runestones.
- **The titles and the map:** the review was done after the locked plan and tests nothing. Many titles stand on a single stone, and what each word has become rests on Wiktionary and Wikipedia – the coding is open, with evidence for every word. That the loans concerned the crown and the Norse words the countryside is our reading of that list, not a count.
- **Corrected on 30 October 2026:** our rule for translating the names missed that Old Norse men's names in *-i* end in *-e* today – Helgi is Helge, Rúni is Rune. With that correction {N['alive']} names live on instead of 82, {pc(N['share'])} instead of 21 per cent. The conclusions stand.
- **A correction along the way:** our first search missed *jarl*, since Rundata spells the word *iarl*. It stands on two stones and does not reach the threshold of three, so the word test is unaffected.
:::

:::box The essentials in brief
- Names are one of the few things that have lived on from the Viking Age – one runestone name in five is still borne.
- The gods kept their names: Thor vanished from the cult but lives on in Torsten, Torbjörn and Tore.
- Power changed its words from the top. The Viking-age following – thegns, housecarls, drengir – vanished or sank, the crown's new men got German titles, but the local thing, härad and lawman kept their Norse names.
- The map and the country changed names too: Garðar became Russia, and Svitjod, the people of the Svear, became Sverige, the realm of the Svear.
- Are you called Torsten, Åsa or Ulf? Then you bear a name that stood on a runestone a thousand years ago.
:::

## Sources

- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Statistics Sweden, First names with at least 10 bearers among the registered population on 31 December (BE0001TNamn10), 2020.
- Svenskt diplomatariums huvudkartotek (SDHK), Swedish National Archives: personal names in the charters 1350–1450.
- Wiktionary (Swedish and English), the entries for the words' present meaning and origin.
- Wikipedia (Swedish): the articles Jarl, Stallare, Bryte, Hundare, Härad, Häradshövding, Tingsrätt, Frälse, Svitjod, Gårdarike, Langbardaland, Särkland and Uppland.
- Vitki's count, the locked analysis plan, the review of the titles and areas and all matches are open on [GitHub](https://github.com/Precatio/runes).
- Images: Wikimedia Commons, with creator and licence in the captions."""

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
