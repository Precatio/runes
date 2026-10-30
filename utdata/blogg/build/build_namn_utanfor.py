"""Artikeln "Ingen på runstenarna hette Freja" (sv + en): de fornnordiska namn som lever i Sverige i dag, var de kommer
ifrån och varför just namnen lever, enligt den låsta planen analysplaner/2026-10-30-namnen-utanfor-runstenarna.md.
Fortsättning på "Tor föll, hjälten blev dräng". Siffrorna låses mot utdata/namn_utanfor/resultat.json och grupper.csv.
    ../../../.venv/bin/python build_namn_utanfor.py [--write | --update DOC]"""
import csv
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import commons  # noqa: E402

U = os.path.join(ROOT, "utdata", "namn_utanfor")
R = json.load(open(os.path.join(U, "resultat.json"), encoding="utf-8"))
ROWS = {r["namn"]: r for r in csv.DictReader(open(os.path.join(U, "grupper.csv"), encoding="utf-8"))}
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
nz = lambda s: recs[s]["normalization"].replace('"', "").strip()  # noqa: E731
pc = lambda x: round(100 * x)  # noqa: E731
sp = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en = lambda n: f"{n:,}"  # noqa: E731
N = lambda name, y: int(ROWS[name][f"n{y}"])  # noqa: E731

# ---- the locked numbers -----------------------------------------------------------------------------------------------
ETY = {r["namn"]: r["etymologi"] for r in csv.DictReader(open(os.path.join(U, "ursprung.csv"), encoding="utf-8"))}
GR = R["groups"]
assert R["n"] == 193 and {g: GR[g]["n"] for g in GR} == {"runsten": 107, "annan runtext": 15, "övrigt": 45, "myt": 26}
B20 = {g: GR[g]["bearers_2020"] for g in GR}
B99 = {g: GR[g]["bearers_1999"] for g in GR}
TOTAL = sum(B20.values())
assert TOTAL == 1063838 and (B20["runsten"], B99["runsten"]) == (710112, 1126231) and (B20["myt"], B99["myt"]) == (93494, 76822)
assert R["P2"]["holds"] and R["P3"]["holds"] and not R["P4"]["holds"]
assert R["P2"]["holm"] < 0.02 and R["P3"]["holm"] < 0.01
DROP = round(100 * (1 - B20["runsten"] / B99["runsten"]))
RISE = round(100 * (B20["myt"] / B99["myt"] - 1))
assert (DROP, RISE) == (37, 22)
for g, name in (("myt", "Idun"), ("myt", "Freja"), ("myt", "Embla"), ("myt", "Saga"), ("myt", "Liv"), ("myt", "Balder"),
                ("myt", "Frej"), ("runsten", "Tuva"), ("runsten", "Love"), ("runsten", "Sixten"), ("runsten", "Sigge"),
                ("runsten", "Bror"), ("runsten", "Gunhild"), ("runsten", "Ingeborg"), ("runsten", "Helge"),
                ("annan runtext", "Vidar"), ("annan runtext", "Tor"), ("övrigt", "Loke"), ("övrigt", "Tyr"),
                ("övrigt", "Leif"), ("övrigt", "Hjalmar"), ("övrigt", "Arvid")):
    assert ROWS[name]["grupp"] == g, (name, ROWS[name]["grupp"])
assert (N("Idun", 1999), N("Idun", 2020), N("Freja", 1999), N("Freja", 2020)) == (43, 1313, 562, 7085)
assert (N("Embla", 1999), N("Embla", 2020), N("Saga", 1999), N("Saga", 2020)) == (130, 1112, 2353, 11851)
assert (N("Tuva", 1999), N("Tuva", 2020), N("Bror", 1999), N("Bror", 2020)) == (255, 6443, 14189, 4319)
assert (N("Arvid", 1999), N("Arvid", 2020), N("Hjalmar", 1999), N("Hjalmar", 2020)) == (4195, 12186, 1122, 3331)
assert (N("Olle", 1999), N("Olle", 2020), N("Leif", 1999), N("Leif", 2020)) == (7360, 14105, 44888, 33083)
assert (N("Meja", 1999), N("Meja", 2020), N("Gösta", 1999), N("Gösta", 2020)) == (27, 3711, 14052, 4499)
assert all(ROWS[n]["grupp"] == "övrigt" for n in ("Arvid", "Hjalmar", "Olle", "Kalle", "Leif", "Gösta", "Börje", "Sture", "Meja"))
assert "Arnviðr" in ETY["Arvid"] and "Hjalmarr" in ETY["Hjalmar"] and "smeknamn för Olof" in ETY["Olle"]
assert "Víðarr" in ROWS["Vidar"]["runform"] and "Þór" in ROWS["Tor"]["runform"]
assert ", Þórr, Sigurðr" in nz("N B599") and "Víðarr" in nz("N 121")  # Tor in the Bryggen name list, Vidar on a church
GROW = {g: sum(1 for r in ROWS.values() if r["grupp"] == g and float(r["tillväxt"]) > 0) for g in GR}
assert GROW == {g: GROW[g] for g in GR}  # computed from grupper.csv
SM16 = nz("Sm 16")
assert "Þy mun go[ðs manns u]m gætit verða, meðan stæinn lifiR ok stafiR runa." in SM16
assert "Þorðr/Þorr/Þorn" in nz("U 440")
# Dates from Wiktionary (ursprung.csv): first use as a given name in Sweden
assert "revived since 1811" in ETY["Ragnar"] and "1827" in ETY["Vidar"] and "1829" in ETY["Viking"]
assert "1873" in ETY["Saga"] and "2000s" in ETY["Loke"] and "2017" in ETY["Idun"]
TOR_ART = "/artiklar/tor-foll-hjalten-blev-drang"
CHAIN = json.load(open(os.path.join(ROOT, "utdata", "overlevde", "namn.json"), encoding="utf-8"))["chain"]
assert (CHAIN["in_letters"], CHAIN["in_letters_alive"]) == (60, 44)  # "tre av fyra"
assert any(r["normalform"] == "Torsten" for r in csv.DictReader(open(os.path.join(ROOT, "utdata", "namnarv", "lexikon.csv"),
                                                                       encoding="utf-8")))  # Torsten in the charters

# ---- pictures ---------------------------------------------------------------------------------------------------------
ASK = "Odin, Lodur, Hoenir skabe Ask og Embla by Frølich.jpg"
IDUN = "Idun by Doepler.jpg"
INFO = commons.commons_info([ASK, IDUN])
assert INFO[ASK]["licence"] == INFO[IDUN]["licence"] == "Public domain"


def pic(f, alt, text, lang):
    page = "https://commons.wikimedia.org/wiki/File:" + f.replace(" ", "_")
    cr = ("Fri från upphovsrätt" if lang == "sv" else "Public domain") + f", via [Wikimedia Commons]({page})."
    return f"![{alt}]({INFO[f]['thumb']})\n{text} {cr}"


LAB = {"sv": {"runsten": "På svenska runstenar", "annan runtext": "I andra runinskrifter", "övrigt": "Sagor och senare",
              "myt": "Ur myterna"},
       "en": {"runsten": "On Swedish runestones", "annan runtext": "In other runic inscriptions",
              "övrigt": "Sagas and later", "myt": "From the myths"}}


def chart_bearers(lang):
    sv = lang == "sv"
    rows = [":::chart Svenskar med ett fornnordiskt förnamn 2020, efter var namnet kommer ifrån" if sv else
            ":::chart Swedes with an Old Norse first name in 2020, by where the name comes from"]
    for g in ("runsten", "övrigt", "myt", "annan runtext"):
        rows.append(f"{'+' if g == 'runsten' else ''}{LAB[lang][g]} | {pc(B20[g] / TOTAL)} | "
                    f"{(sp if sv else en)(B20[g])} {'bärare' if sv else 'bearers'}, {GR[g]['n']} {'namn' if sv else 'names'}")
    rows.append("Källa: SCB:s tilltalsnamn 2020; ursprung enligt svenska och engelska Wiktionary och Wikipedia; runformer ur "
                "Samnordisk runtextdatabas. Vitkis räkning." if sv else
                "Source: Statistics Sweden's first names 2020; origin according to the Swedish and English Wiktionary and "
                "Wikipedia; runic forms from the Scandinavian Runic-text Data Base. Vitki's count.")
    return "\n".join(rows) + "\n:::"


def chart_growth(lang):
    sv = lang == "sv"
    rows = [":::chart Andel av namnen som fick fler bärare från 1999 till 2020" if sv else
            ":::chart Share of the names that gained bearers from 1999 to 2020"]
    for g in ("myt", "annan runtext", "övrigt", "runsten"):
        rows.append(f"{'+' if g == 'myt' else ''}{LAB[lang][g]} | {pc(GROW[g] / GR[g]['n'])} | {GROW[g]} "
                    f"{'av' if sv else 'of'} {GR[g]['n']}")
    rows.append("Källa: SCB:s tilltalsnamn 1999 och 2020; Vitkis räkning." if sv else
                "Source: Statistics Sweden's first names 1999 and 2020; Vitki's count.")
    return "\n".join(rows) + "\n:::"


title = "Ingen på runstenarna hette Freja – i dag heter 7 000 svenskar det"
summary = ("Vi räknade alla fornnordiska förnamn som svenskar bär i dag och letade upp dem på runstenarna. Stenarnas namn "
           "åldras med sina bärare. Det som växer är gudarnas egna namn – Freja, Idun, Embla, Loke – som ingen människa på "
           "runstenarna bar. Och varför är det just namnen som har levt vidare i tusen år?")

body = f"""År 1999 hette {N('Idun', 1999)} svenskar Idun. År 2020 hette {sp(N('Idun', 2020))} det. Freja gick från {N('Freja', 1999)} till {sp(N('Freja', 2020))}, Embla från {N('Embla', 1999)} till {sp(N('Embla', 2020))}. Det är gudinnor och den första kvinnan i den nordiska skapelsemyten – och inte en enda människa på de svenska runstenarna bar de namnen.

I [förra artikeln]({TOR_ART}) räknade vi hur många av runstenarnas namn som lever i dag: vart femte. Sedan kom frågan om alla fornnordiska namn som inte stod på stenarna. Helge, till exempel. Det visade sig att Helgi står på fjorton runstenar och att vår regel hade missat honom; vi rättade artikeln. Men frågan var bättre än felet. Vilka fornnordiska namn bär vi i dag, varifrån kommer de – och varför är det just namnen som har överlevt, när nästan allt annat från vikingatiden har bytts ut?

{pic(IDUN, 'Idun med äpplena', 'Idun med äpplena som håller gudarna unga. Teckning av Carl Emil Doepler (1824–1905).', 'sv')}

:::box Kort sagt
- {R['n']} fornnordiska förnamn bärs av minst tio svenskar. {GR['runsten']['n']} av dem står på svenska runstenar, och de bärs av två tredjedelar av alla som har ett fornnordiskt namn.
- Men stenarnas namn åldras. Från 1999 till 2020 minskade deras bärare med {DROP} procent – Bror, Gunhild och Ingeborg dör ut med en generation.
- Namnen ur myterna växer: tillsammans med {RISE} procent, och Idun trettio gånger om. Skillnaden håller i en låst prövning.
- Ingen människa på runstenarna hette som en gud. Vikingarna bar gudarna i namnen – Torsten, Ingrid – men gav inte barnen gudens eget namn. Det gör vi.
- Namnen överlever för att de inte påstår något, för att de ärvs, och för att de till slut kan väljas.
:::

## {R['n']} namn från vikingatiden

Vi började med en fråga som låter enkel: vilka förnamn i Sverige i dag är fornnordiska? För att inte lita på våra egna regler tog vi svaret från andra. Svenska och engelska Wiktionary har uppslag för drygt tusen svenska förnamn, med varifrån namnet kommer, och för de namn som saknar uppgift där läste vi namnartikeln i svenska Wikipedia. Ett namn räknas som fornnordiskt när det går att följa tillbaka till fornnordiskan eller runsvenskan, och inte vidare till latin, grekiska, hebreiska eller tyska. Johan står till exempel som fornsvenska *Iohan* i Wiktionary, men namnet kommer från hebreiskan, så det räknas inte.

Kvar blev {R['n']} namn som bärs av minst tio svenskar. Sedan letade vi efter vart och ett i runinskrifterna.

{chart_bearers('sv')}

{GR['runsten']['n']} namn står på svenska runstenar, ibland i en form som har slipats av tusen år av uttal: Kjell var *Ketill*, Sixten var *Sigsteinn*, Love var *Lófi*. De bärs av {sp(B20['runsten'])} svenskar. {GR['annan runtext']['n']} namn finns i andra runinskrifter, oftast norska och medeltida – Vidar står på en kyrka i Norge, och Tor i en namnlista från Bryggen i Bergen. {GR['övrigt']['n']} kommer ur sagorna eller är senare bildningar: Leif, Arvid, Hjalmar, Gustav. Och {GR['myt']['n']} kommer ur myterna.

## Stenarnas namn åldras

Runstenarnas namn är fortfarande de stora. Men de krymper. År 1999 bar {sp(B99['runsten'])} svenskar ett namn som står på en runsten. År 2020 var de {sp(B20['runsten'])}, en tredjedel färre. Det är inte så att namnen har blivit omoderna på en gång. Det är bärarna som blir gamla. Bror hade {sp(N('Bror', 1999))} bärare 1999 och {sp(N('Bror', 2020))} år 2020. Gunhild gick från {sp(N('Gunhild', 1999))} till {sp(N('Gunhild', 2020))}, Ingeborg från {sp(N('Ingeborg', 1999))} till {sp(N('Ingeborg', 2020))}. Det är 1900-talets namn, som gick i arv från far- och morföräldrar, och som nu följer med dem.

Några runstensnamn kommer tillbaka, och de liknar varandra: korta, mjuka och gamla. Tuva gick från {N('Tuva', 1999)} till {sp(N('Tuva', 2020))} bärare – det är *Tófa*, som står på flera svenska runstenar. Love, som Lófi skrev på en sten i Bjälbo, gick från {sp(N('Love', 1999))} till {sp(N('Love', 2020))}. Sixten och Sigge växer också.

## Gudarna fick egna namn

{chart_growth('sv')}

Namnen ur myterna går åt andra hållet. Tillsammans växte de med {RISE} procent, och {GROW['myt']} av {GR['myt']['n']} fick fler bärare. Saga gick från {sp(N('Saga', 1999))} till {sp(N('Saga', 2020))}, Liv från {sp(N('Liv', 1999))} till {sp(N('Liv', 2020))}. Idun var 2017 ett av de hundra vanligaste namnen på nyfödda flickor. Vi prövade det i förväg: mytnamnen har vuxit mer än de övriga fornnordiska namnen, och skillnaden är för stor för att vara slump.

{pic(ASK, 'Oden, Lodur och Höne skapar Ask och Embla', 'Oden, Lodur och Höne skapar de första människorna, Ask och Embla, ur två trästycken på stranden. Teckning av Lorenz Frølich (1820–1908).', 'sv')}

Det märkliga är att de här namnen nästan inte fanns som människonamn förut. På de svenska runstenarna heter ingen person Freyja, Óðinn eller Þórr. Gudarna finns där ändå, i namnen: Þorsteinn, Ásbjôrn, Ingiríðr. Vikingarna bar en gud i namnet men gav inte barnet gudens eget namn. Det närmaste vi kommer är en sten vid U 440 i Uppland, där namnet kan läsas Þórðr, Þórr eller Þórn – ingen vet säkert.

I dag är det tvärtom. Svenskar heter Tor ({sp(N('Tor', 2020))}), Freja ({sp(N('Freja', 2020))}), Loke ({sp(N('Loke', 2020))}), Frej ({N('Frej', 2020)}), Tyr ({N('Tyr', 2020)}) och Balder ({N('Balder', 2020)}). Varför vikingarna inte gjorde så vet vi inte. Kanske var gudens namn för heligt för en människa, kanske var det bara inte sed. Men skillnaden är tydlig: förr bar man guden som en del av sitt namn. Nu bär man guden hela.

## Ur böckerna, inte ur stenarna

Vi prövade också den större frågan: växer de fornnordiska namn som inte står på runstenarna mer än de som gör det? Svaret är ja, och det håller i den låsta prövningen. Det nya fornnordiska namnmodet hämtar inte från runstenarna. Det hämtar från sagorna och myterna – från böckerna.

Det har hänt förr. Enligt Wiktionary försvann Ragnar ur bruk i Sverige på 1500-talet och togs upp igen 1811. Vidar fick sin första svenska bärare 1827, Viking 1829 och Saga 1873 – det var götiska förbundets och Tegnérs tid, när det fornnordiska blev romantik. Loke blev ett vanligt namn först på 2000-talet. Varje gång ett namn kommer tillbaka på det sättet är det ett val, inte ett arv.

## Mellangenerationen och smeknamnen

Mellan stenarnas namn och myternas finns en tredje grupp, och den visar samma sak från ett annat håll. Det är namnen som inte står på någon svensk runsten i den form vi bär dem, men som är lika fornnordiska: Leif, Gösta, Börje, Sture. Det var 1900-talets namn, och de krymper fortare än nästan några andra. Leif gick från {sp(N('Leif', 1999))} till {sp(N('Leif', 2020))} bärare, Gösta från {sp(N('Gösta', 1999))} till {sp(N('Gösta', 2020))}.

Samtidigt växer andra namn ur samma förråd. Arvid – fornnordiska *Arnviðr* – gick från {sp(N('Arvid', 1999))} till {sp(N('Arvid', 2020))}. Hjalmar, *Hjalmarr*, från {sp(N('Hjalmar', 1999))} till {sp(N('Hjalmar', 2020))}. Meja, bildat av fornsvenskans ord för kraft, från {N('Meja', 1999)} till {sp(N('Meja', 2020))}. Det är inte ursprunget som avgör vilka namn som växer. Det är om namnet hör till farföräldrarnas generation eller till generationen före den.

Och så smeknamnen. Olle växte fram under medeltiden som smeknamn för Olof – runstenarnas *Ólafr* – och har blivit ett eget namn: {sp(N('Olle', 1999))} bärare 1999, {sp(N('Olle', 2020))} år 2020. Kalle, av Karl, går samma väg. Runstenarnas namn lever alltså inte bara i sin egen form. De lever också i de korta, vardagliga formerna, som en gång var det man ropade över gårdsplanen.

## Varför just namnen?

Här tänker vi högt. Det här avsnittet är vår tolkning och inte en prövning – men det bygger på det vi har visat i den här och den förra artikeln.

Nästan allt från vikingatiden har bytts ut. Maktens titlar försvann – jarlen blev hertig, tegnen och huskarlen finns inte längre. Kulten byttes mot kyrkan. Lagen skrevs om. Men vart femte namn på runstenarna lever, och gudanamnen klarade sig dubbelt så bra som de andra. Varför?

**Ett namn påstår ingenting.** En titel säger vem som har makt. Ett ord för kult säger vad man tror på. När makten och tron byttes, måste de orden bort. Ett namn säger bara vem någon är. Det hotar ingen, och därför fanns det ingen anledning att ta bort det. Kyrkan döpte barnen – och i de medeltida breven heter de fortfarande Torsten.

**Ett namn tappar sin betydelse.** Ingen som heter Torsten hör längre att det betyder Tors sten. Ingrid är inte längre Ing den vackra. Ett namn blir ett ljud som pekar på en människa, och det är just därför det kan överleva en ny tro. Betydelsen nöts bort, men ljudet går vidare.

**Ett namn är ett arv.** Runstenarna själva är byggda för att hålla namn vid liv. Vid Nöbbele i Småland står det: *Þy mun goðs manns um gætit verða, meðan stæinn lifiR ok stafiR runa.* – därför ska den gode mannen minnas, så länge stenen lever och runornas stavar. Stenen skulle bära namnet. Men det som bar namnen längst var familjerna, som gav barnen namn efter de döda. Av de runstensnamn som också finns i de medeltida breven lever tre av fyra i dag. Namnet gick från generation till generation, långt efter att stenen slutat läsas.

**Och till slut kan ett namn väljas.** Det är det nya. Runstenarnas namn ärvdes, och de åldras nu med sina bärare. Gudarnas namn väljs – av föräldrar som inte tror på Freja, men som vill att barnet ska höra till något äldre än sig själv. Gudarna kom tillbaka som namn just när ingen längre trodde på dem. Det är kanske därför de kunde komma tillbaka.

Två sätt att leva vidare, alltså. Stenarnas namn levde av arv. Myternas namn lever av val.

## Så säkra är vi

:::box Så säkra är vi
- **Det vi visar:** att {GR['runsten']['n']} av dagens {R['n']} fornnordiska förnamn står på svenska runstenar, att deras bärare minskade med en tredjedel på tjugo år, och att namnen ur myterna och sagorna har vuxit mer – två prövningar som låstes innan vi räknade, och som båda håller.
- **Det vi tror:** att namn överlever för att de inte påstår något, för att de tappar sin betydelse och för att de ärvs – och att de i dag lever vidare för att de väljs.
- **Det vi inte kan visa:** varför vikingarna inte gav barnen gudarnas egna namn. Och kvinnonamnen växte inte annorlunda än mansnamnen, trots att vi trodde det.
- **Svagheterna:** vad som är fornnordiskt bygger på Wiktionary och Wikipedia, inte på vår egen forskning, och 291 namn saknar uppgift om ursprung. Vi granskade alla gränsfall för hand – sju namn som Johan och Kristina räknas inte, trots fornsvenska former, och 28 namn som Kjell och Sixten räknas som samma namn som på stenarna. Smeknamn som Olle och Kalle räknas inte som runstensnamn. Siffrorna gäller tilltalsnamn med minst tio bärare.
:::

:::box Det viktigaste i korthet
- Två av tre svenskar med ett fornnordiskt namn bär ett namn som stod på en runsten – men de namnen blir färre för varje år.
- De som växer är gudarnas namn, Freja, Idun, Embla och Loke, som ingen människa på runstenarna bar.
- Vikingarna bar guden som en del av namnet. Vi bär guden hela.
- Namnen överlevde tusen år för att de inte påstod något. Nu lever de för att vi väljer dem.
:::

## Källor

- Statistiska centralbyrån, Tilltalsnamn med minst 10 bärare bland folkbokförda 31 december (BE0001TNamn10), 1999 och 2020.
- Wiktionary (svenska och engelska), uppslagen för svenska förnamn med etymologi; Wikipedia (svenska), namnartiklarna.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Den låsta analysplanen, alla 1 166 namn med etymologi och grupp, och Vitkis räkning ligger öppet på [GitHub](https://github.com/Precatio/runes).
- Bilder: Wikimedia Commons, med upphovsperson i bildtexterna."""

title_en = "No one on the runestones was called Freja – today 7,000 Swedes are"
summary_en = ("We counted every Old Norse first name Swedes bear today and looked for them on the runestones. The stones' "
              "names are ageing with their bearers. What grows are the gods' own names – Freja, Idun, Embla, Loke – which no "
              "person on the runestones bore. And why is it the names that have lived on for a thousand years?")

body_en = f"""In 1999, {N('Idun', 1999)} Swedes were called Idun. In 2020, {en(N('Idun', 2020))} were. Freja went from {N('Freja', 1999)} to {en(N('Freja', 2020))}, Embla from {N('Embla', 1999)} to {en(N('Embla', 2020))}. They are goddesses and the first woman of the Norse creation myth – and not a single person on the Swedish runestones bore those names.

In [the previous article](/en{TOR_ART}) we counted how many of the runestones' names live on today: one in five. Then came the question about all the Old Norse names that did not stand on the stones. Helge, for example. It turned out that Helgi stands on fourteen runestones and that our rule had missed him; we corrected the article. But the question was better than the mistake. Which Old Norse names do we bear today, where do they come from – and why is it the names that have survived, when nearly everything else from the Viking Age has been replaced?

{pic(IDUN, 'Idun with the apples', 'Idun with the apples that keep the gods young. Drawing by Carl Emil Doepler (1824–1905).', 'en')}

:::box In short
- {R['n']} Old Norse first names are borne by at least ten Swedes. {GR['runsten']['n']} of them stand on Swedish runestones, and they are borne by two-thirds of everyone with an Old Norse name.
- But the stones' names are ageing. From 1999 to 2020 their bearers fell by {DROP} per cent – Bror, Gunhild and Ingeborg are dying out with a generation.
- The names from the myths are growing: by {RISE} per cent together, and Idun thirtyfold. The difference holds in a locked test.
- No person on the runestones was named after a god. The Vikings carried the gods inside their names – Torsten, Ingrid – but did not give a child the god's own name. We do.
- Names survive because they claim nothing, because they are inherited, and because in the end they can be chosen.
:::

## {R['n']} names from the Viking Age

We started with a question that sounds simple: which first names in Sweden today are Old Norse? So as not to rely on our own rules, we took the answer from others. The Swedish and English Wiktionary have entries for more than a thousand Swedish first names, with where each name comes from, and for the names without that information there we read the name article in the Swedish Wikipedia. A name counts as Old Norse when it can be traced back to Old Norse or Runic Swedish, and not further to Latin, Greek, Hebrew or German. Johan, for instance, appears as Old Swedish *Iohan* in Wiktionary, but the name comes from Hebrew, so it does not count.

That left {R['n']} names borne by at least ten Swedes. Then we looked for each of them in the runic inscriptions.

{chart_bearers('en')}

{GR['runsten']['n']} names stand on Swedish runestones, sometimes in a form worn down by a thousand years of speech: Kjell was *Ketill*, Sixten was *Sigsteinn*, Love was *Lófi*. They are borne by {en(B20['runsten'])} Swedes. {GR['annan runtext']['n']} names appear in other runic inscriptions, mostly Norwegian and medieval – Vidar stands on a church in Norway, and Tor in a list of names from Bryggen in Bergen. {GR['övrigt']['n']} come from the sagas or are later formations: Leif, Arvid, Hjalmar, Gustav. And {GR['myt']['n']} come from the myths.

## The stones' names are ageing

The runestones' names are still the big ones. But they are shrinking. In 1999, {en(B99['runsten'])} Swedes bore a name that stands on a runestone. In 2020 they were {en(B20['runsten'])}, a third fewer. It is not that the names went out of fashion all at once. It is the bearers who are growing old. Bror had {en(N('Bror', 1999))} bearers in 1999 and {en(N('Bror', 2020))} in 2020. Gunhild went from {en(N('Gunhild', 1999))} to {en(N('Gunhild', 2020))}, Ingeborg from {en(N('Ingeborg', 1999))} to {en(N('Ingeborg', 2020))}. These are the names of the twentieth century, handed down from grandparents, and now leaving with them.

Some runestone names are coming back, and they resemble each other: short, soft and old. Tuva went from {N('Tuva', 1999)} to {en(N('Tuva', 2020))} bearers – it is *Tófa*, who stands on several Swedish runestones. Love, as Lófi wrote on a stone at Bjälbo, went from {en(N('Love', 1999))} to {en(N('Love', 2020))}. Sixten and Sigge are growing too.

## The gods got names of their own

{chart_growth('en')}

The names from the myths go the other way. Together they grew by {RISE} per cent, and {GROW['myt']} of {GR['myt']['n']} gained bearers. Saga went from {en(N('Saga', 1999))} to {en(N('Saga', 2020))}, Liv from {en(N('Liv', 1999))} to {en(N('Liv', 2020))}. In 2017 Idun was one of the hundred most common names for newborn girls. We tested it in advance: the myth names have grown more than the other Old Norse names, and the difference is too large to be chance.

{pic(ASK, 'Odin, Lodur and Hœnir create Ask and Embla', 'Odin, Lóðurr and Hœnir create the first humans, Askr and Embla, from two pieces of wood on the shore. Drawing by Lorenz Frølich (1820–1908).', 'en')}

What is striking is that these names hardly existed as human names before. On the Swedish runestones no person is called Freyja, Óðinn or Þórr. The gods are there all the same, inside the names: Þorsteinn, Ásbjôrn, Ingiríðr. The Vikings carried a god in their name but did not give a child the god's own name. The closest we come is the stone U 440 in Uppland, where the name can be read Þórðr, Þórr or Þórn – no one knows for certain.

Today it is the other way round. Swedes are called Tor ({en(N('Tor', 2020))}), Freja ({en(N('Freja', 2020))}), Loke ({en(N('Loke', 2020))}), Frej ({N('Frej', 2020)}), Tyr ({N('Tyr', 2020)}) and Balder ({N('Balder', 2020)}). Why the Vikings did not do so, we do not know. Perhaps the god's name was too holy for a person, perhaps it simply was not the custom. But the difference is clear: then one carried the god as part of one's name. Now one carries the whole god.

## From the books, not the stones

We also tested the larger question: do the Old Norse names that do not stand on the runestones grow more than those that do? The answer is yes, and it holds in the locked test. The new fashion for Old Norse names does not draw on the runestones. It draws on the sagas and the myths – on books.

It has happened before. According to Wiktionary, Ragnar went out of use in Sweden in the sixteenth century and was taken up again in 1811. Vidar got his first Swedish bearer in 1827, Viking in 1829 and Saga in 1873 – the age of the Gothic Society and of Tegnér, when the Old Norse became romance. Loke became a common name only in the 2000s. Each time a name comes back in that way, it is a choice, not an inheritance.

## The middle generation and the pet names

Between the stones' names and the myths' there is a third group, and it shows the same thing from another side. These are names that do not stand on any Swedish runestone in the form we bear them, but are just as Old Norse: Leif, Gösta, Börje, Sture. They were the names of the twentieth century, and they are shrinking faster than almost any others. Leif went from {en(N('Leif', 1999))} to {en(N('Leif', 2020))} bearers, Gösta from {en(N('Gösta', 1999))} to {en(N('Gösta', 2020))}.

At the same time other names from the same store are growing. Arvid – Old Norse *Arnviðr* – went from {en(N('Arvid', 1999))} to {en(N('Arvid', 2020))}. Hjalmar, *Hjalmarr*, from {en(N('Hjalmar', 1999))} to {en(N('Hjalmar', 2020))}. Meja, formed from the Old Swedish word for strength, from {N('Meja', 1999)} to {en(N('Meja', 2020))}. It is not the origin that decides which names grow. It is whether the name belongs to the grandparents' generation or to the generation before that.

And then the pet names. Olle grew up in the Middle Ages as a pet name for Olof – the runestones' *Ólafr* – and has become a name of its own: {en(N('Olle', 1999))} bearers in 1999, {en(N('Olle', 2020))} in 2020. Kalle, from Karl, is going the same way. So the runestones' names live on not only in their own form. They also live in the short, everyday forms that were once what you called across the farmyard.

## Why the names?

Here we are thinking aloud. This section is our interpretation, not a test – but it rests on what we have shown in this and the previous article.

Nearly everything from the Viking Age has been replaced. The titles of power vanished – the jarl became a duke, the thegn and the housecarl are gone. The cult was exchanged for the church. The law was rewritten. Yet one name in five on the runestones lives on, and the names with a god in them fared twice as well as the others. Why?

**A name claims nothing.** A title says who holds power. A word for cult says what one believes. When power and faith changed, those words had to go. A name only says who someone is. It threatens no one, and so there was no reason to remove it. The church baptised the children – and in the medieval charters they are still called Torsten.

**A name loses its meaning.** No one called Torsten still hears that it means Thor's stone. Ingrid is no longer Ing the beautiful. A name becomes a sound pointing at a person, and that is exactly why it can survive a new faith. The meaning wears away, but the sound goes on.

**A name is an inheritance.** The runestones themselves were built to keep names alive. At Nöbbele in Småland it says: *Þy mun goðs manns um gætit verða, meðan stæinn lifiR ok stafiR runa* – so the good man shall be remembered while the stone lives and the staves of the runes. The stone was to carry the name. But what carried the names longest were the families, who named their children after the dead. Of the runestone names that also appear in the medieval charters, three in four live today. The name passed from generation to generation, long after the stone was no longer read.

**And in the end a name can be chosen.** That is what is new. The runestones' names were inherited, and they are now ageing with their bearers. The gods' names are chosen – by parents who do not believe in Freja, but who want the child to belong to something older than themselves. The gods came back as names just when no one believed in them any more. Perhaps that is why they could come back.

Two ways of living on, then. The stones' names lived by inheritance. The myths' names live by choice.

## How sure we are

:::box How sure we are
- **What we show:** that {GR['runsten']['n']} of today's {R['n']} Old Norse first names stand on Swedish runestones, that their bearers fell by a third in twenty years, and that the names from the myths and sagas have grown more – two tests locked before we counted, both of which hold.
- **What we believe:** that names survive because they claim nothing, because they lose their meaning and because they are inherited – and that today they live on because they are chosen.
- **What we cannot show:** why the Vikings did not give their children the gods' own names. And women's names did not grow differently from men's, though we thought they would.
- **The weaknesses:** what is Old Norse rests on Wiktionary and Wikipedia, not on our own research, and 291 names lack any information on origin. We reviewed every borderline case by hand – seven names such as Johan and Kristina do not count, despite Old Swedish forms, and 28 names such as Kjell and Sixten count as the same name as on the stones. Pet forms such as Olle and Kalle do not count as runestone names. The figures concern first names with at least ten bearers.
:::

:::box The essentials in brief
- Two in three Swedes with an Old Norse name bear a name that stood on a runestone – but those names grow fewer every year.
- What grows are the gods' names, Freja, Idun, Embla and Loke, which no person on the runestones bore.
- The Vikings carried the god as part of their name. We carry the whole god.
- The names survived a thousand years because they claimed nothing. Now they live because we choose them.
:::

## Sources

- Statistics Sweden, First names with at least 10 bearers among the registered population on 31 December (BE0001TNamn10), 1999 and 2020.
- Wiktionary (Swedish and English), the entries for Swedish first names with etymology; Wikipedia (Swedish), the name articles.
- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- The locked analysis plan, all 1,166 names with etymology and group, and Vitki's count are open on [GitHub](https://github.com/Precatio/runes).
- Images: Wikimedia Commons, with the artist in the captions."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"

out = {"slug": "ingen-pa-runstenarna-hette-freja", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Språk och stavning", "Tro och magi", "Eddan"]}
path = os.path.join(ROOT, "utdata", "blogg", "namn_utanfor.json")
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
