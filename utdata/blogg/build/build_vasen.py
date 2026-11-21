"""Artikeln "Var bodde trollen?" – väsen som inte är gudar i den fornnordiska litteraturen.

Bygger på den låsta fokusstudien analysplaner/2026-11-21-vasen.md (2076615) + tillägg 1 (c56f36f); siffrorna läses ur
utdata/vasen/matt.json och data/cache/vasen/traffar.csv (utdata/vasen/analys.py), och varje citat kontrolleras mot
texten i korpusen. Svensk och engelsk text. Viktor 2026-11-21: "artikel ja, försök få med lite intressanta
illustrationer … varva dem något så om man läser flera på raken så känns det inte som en alltför mallad form."
    ../../../.venv/bin/python build_vasen.py [--write | --update DOC]"""
import csv
import datetime as dt
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "utdata", "vasen"))
from src import blog_labels  # noqa: E402
import analys as vasen  # noqa: E402

SLUG = "var-bodde-trollen"
PLAN = "https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-21-vasen.md"
RES = "https://github.com/Precatio/runes/blob/main/utdata/vasen/resultat.md"
M = json.load(open(os.path.join(ROOT, "utdata", "vasen", "matt.json"), encoding="utf-8"))
ROWS = [r for r in csv.DictReader(open(os.path.join(ROOT, "data", "cache", "vasen", "traffar.csv"), encoding="utf-8"))]
OK = [r for r in ROWS if r["klass"] != "vättar"]  # vättarna klarade inte grinden och räknas inte i jämförelserna

# ======================================================================================================================
# 1. Siffrorna
# ======================================================================================================================
TEXTS = {(c, n): t for c, n, t in vasen.texts()}
WORDS = {k: len(t.split()) for k, t in TEXTS.items()}
TOTAL_WORDS = sum(n for (c, _), n in WORDS.items() if not c.startswith("runstenar"))
assert TOTAL_WORDS == sum(v for k, v in M["ord_per_korpus"].items() if not k.startswith("runstenar"))
N_TEXTS = sum(1 for (c, _) in WORDS if not c.startswith("runstenar") and not c.endswith("_vers"))

T1 = M["tester"]["huvud"]["T1"]
assert T1["håller"] and T1["kvot"] == 5.88 and T1["intervall"] == [3.437, 10.21]
T1_TROLL = M["tester"]["utan_tröll"]["T1"]
T1_BIG = M["tester"]["utan_största_sagan"]["T1"]
assert T1_TROLL["håller"] and T1_BIG["håller"]
T2 = M["tester"]["huvud"]["T2"]
T3 = M["tester"]["huvud"]["T3"]
assert not T2["håller"] and T3.get("obestämt")
V2 = {c: M["V2"][c]["per_10000_ord"] for c in M["V2"]}

per_text = Counter((r["korpus"], r["text"]) for r in OK)
by_corpus = defaultdict(Counter)
for r in OK:
    by_corpus[r["korpus"]][r["klass"]] += 1


def with_hit(c):
    n = M["texter_per_korpus"][c]
    k = sum(1 for (cc, _) in per_text if cc == c)
    return k, n


def share(c, klass):
    tot = sum(by_corpus[c].values())
    return round(100 * by_corpus[c][klass] / tot)


def terms(c):
    return Counter(r["term"] for r in OK if r["korpus"] == c)


# Islänningasagorna
IS_HITS = sum(by_corpus["islanningasagor"].values())
BARD = per_text[("islanningasagor", "bardar saga snaefellsass")]
BARD_PC = round(100 * BARD / IS_HITS)
IS_NONE = M["texter_per_korpus"]["islanningasagor"] - with_hit("islanningasagor")[0]
IS_TERMS = terms("islanningasagor")
FA_TERMS = terms("fornaldarsagor")
assert IS_TERMS.most_common(1)[0][0] == "tröll" and FA_TERMS.most_common(1)[0][0] == "tröll"
assert by_corpus["islanningasagor"]["dvärgar"] == 0
# utan Bárðar saga (beskrivande, inte låst): täthet i islänningasagorna
is_keys = [k for k in WORDS if k[0] == "islanningasagor"]
rate_is_nobard = 1e4 * (IS_HITS - BARD) / (sum(WORDS[k] for k in is_keys) - WORDS[("islanningasagor", "bardar saga snaefellsass")])
FA_RATE = 1e4 * sum(by_corpus["fornaldarsagor"].values()) / sum(WORDS[k] for k in WORDS if k[0] == "fornaldarsagor")
assert round(FA_RATE, 2) == T1["fornaldar"]
RATIO_NOBARD = FA_RATE / rate_is_nobard
assert RATIO_NOBARD > T1["kvot"]

# Heimskringla
HK = Counter(t for (c, t) in per_text.elements() if c == "heimskringla") if False else Counter(
    {t: n for (c, t), n in per_text.items() if c == "heimskringla"})
HK_HITS = sum(HK.values())
assert HK["Ynglinga saga"] == 8 and HK_HITS == 18 and len(HK) == 5
HK_WITH, HK_N = with_hit("heimskringla")
# samtidssagorna
SA = terms("samtidssagor")
assert sum(SA.values()) == T3["träffar_samtid"] == 7 and SA["djöfull"] == 3

# Eddan och Snorre
ED_JATT = share("eddadikter", "jättar")
GY_JATT = share("snorra_edda_gylfaginning", "jättar")
IS_JATT = share("islanningasagor", "jättar")
FA_JATT = share("fornaldarsagor", "jättar")
ED_ODJ = share("eddadikter", "odjur")
FA_ODJ = share("fornaldarsagor", "odjur")
IS_ODJ = share("islanningasagor", "odjur")
assert (ED_JATT, GY_JATT, IS_JATT, FA_JATT, ED_ODJ) == (59, 69, 80, 64, 20)

# runstenarna: båda träffarna falska (grinden: Öl 1 kenning, U 703 "risinn" = rest)
assert [v["sten"] for v in M["V4"]] == ["Öl 1", "U 703"]
N_STONES = M["texter_per_korpus"]["runstenar_SE"]
assert not [r for r in ROWS if r["korpus"] == "runstenar_SE" and r["text"] == "Sö 101"]

GATE = M["grind"]["omgang_1"]["viktat_procent"]
assert GATE == 94


def sv_n(x):
    return f"{x:,}".replace(",", " ")


def en_n(x):
    return f"{x:,}"


def sv_d(x, n=1):
    return f"{x:.{n}f}".replace(".", ",")


MILJ_SV = sv_d(TOTAL_WORDS / 1e6, 2)
MILJ_EN = f"{TOTAL_WORDS / 1e6:.2f}"
assert MILJ_SV == "1,65"

# ======================================================================================================================
# 2. Citaten (kontrolleras mot korpusen)
# ======================================================================================================================
K = os.path.join(ROOT, "utdata", "varlden", "korpus")
EDDA = json.load(open(os.path.join(ROOT, "utdata", "Malt", "kallor", "edda.json"), encoding="utf-8"))


def src(path):
    return open(os.path.join(K, path), encoding="utf-8").read()


Q = {
    "snorre": ("heimskringla/Saga_Ólafs_Tryggvasonar.txt",
               "Ok varð í þeirri ferð mart, þat er í frásögn er fœrt, er tröll ok illar vættir glettust við menn hans ok "
               "stundum við sjálfan hann; en vér viljum heldr rita um þá atburði, er Ólafr konungr kristnaði Noreg"),
    "vanlande": ("heimskringla/Ynglinga_saga.txt", "kallaði hann ok sagði, at mara trað hann"),
    "njal": ("islendingasogur/brennu-njals_saga.is.txt", "og munt þú séð hafa fylgju þína"),
    "bard": ("islendingasogur/bardar_saga_snaefellsass.is.txt", "móðir hans var komin af tröllaættum"),
    "bard2": ("islendingasogur/bardar_saga_snaefellsass.is.txt", "risum og tröllum og óvættum"),
    "dverga": ("fornaldarsogur/Sörla_þáttr_eða_Heðins_saga_ok_Högna.txt", "Þess háttar menn, sem þeir váru, kölluðu menn dverga"),
    "alfkona": ("fornaldarsogur/Hrólfs_saga_kraka_ok_kappa_hans.txt", "Þetta hafði verit ein álfkona"),
    "kormak": ("islendingasogur/kormaks_saga.is.txt", "gera álfum veislu af slátrinu og mun þér batna"),
    "kormak_hol": ("islendingasogur/kormaks_saga.is.txt", "Hóll einn er héðan skammt í brott er álfar búa í"),
    "sigvat": ("heimskringla/Saga_Ólafs_hins_helga.txt", "stóð þar húsfreyja í durum, ok bað hann eigi þar inn koma, segir, at þau œtti álfa blót"),
    "grettir": ("islendingasogur/grettis_saga.is.txt", "hjó á hálsinn haugbúanum"),
}
for k, (p, q) in Q.items():
    assert q in src(p), k
EQ = {"tunridur": ("Hávamál", "ef ek sé túnriður leika lofti á"),
      "audhumla": ("Gylfaginning", "kýr sú, er Auðhumla hét, en fjórar mjólkár runnu ór spenum hennar, ok fæddi hon Ymi")}
for k, (poem, q) in EQ.items():
    assert q in EDDA[poem], k


def q(k):
    return Q[k][1] if k in Q else EQ[k][1]


# ======================================================================================================================
# 3. Bilderna (Wikimedia Commons; fria licenser kontrollerade 2026-11-21)
# ======================================================================================================================
RAMSUND = ("https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b6/S%C3%B6_101%2C_Ramsund.jpg/1280px-S%C3%B6_101%2C_Ramsund.jpg",
           "https://commons.wikimedia.org/wiki/File:S%C3%B6_101,_Ramsund.jpg", "Berig", "CC BY 2.5")
FENRIR = ("https://thumb.wikimedia.org/wikipedia/commons/thumb/0/06/AM_738_4to%2C_43v%2C_BW_Fenrir.jpeg/1280px-AM_738_4to%2C_43v%2C_BW_Fenrir.jpeg",
          "https://commons.wikimedia.org/wiki/File:AM_738_4to,_43v,_BW_Fenrir.jpeg", "okänd tecknare", "public domain")
AUDHUMLA = ("https://upload.wikimedia.org/wikipedia/commons/4/47/Manuscript_Audhumla.jpg",
            "https://commons.wikimedia.org/wiki/File:Manuscript_Audhumla.jpg", "okänd tecknare", "public domain")
BAUER = ("https://upload.wikimedia.org/wikipedia/commons/2/2f/John_Bauer_-_Troll_-_NMH_496-1953_recto_-_Nationalmuseum.jpg",
         "https://commons.wikimedia.org/wiki/File:John_Bauer_-_Troll_-_NMH_496-1953_recto_-_Nationalmuseum.jpg", "John Bauer", "public domain")


# ======================================================================================================================
# 4. Diagrammen (procent)
# ======================================================================================================================
LAB = {"eddadikter": ("Eddadikterna", "The Eddic poems"), "fornaldarsagor": ("Fornaldarsagorna", "The legendary sagas"),
       "islanningasagor": ("Islänningasagorna", "The sagas of Icelanders"), "samtidssagor": ("Samtidssagorna", "The contemporary sagas"),
       "heimskringla": ("Heimskringla", "Heimskringla")}


def chart_texts(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Hur stor andel av texterna som nämner minst ett väsen' if sv else 'Share of the texts that mention at least one being'}"]
    for c in ("eddadikter", "fornaldarsagor", "islanningasagor", "samtidssagor", "heimskringla"):
        k, n = with_hit(c)
        hl = "+" if c in ("fornaldarsagor", "islanningasagor") else ""
        rows.append(f"{hl}{LAB[c][0 if sv else 1]} | {round(100 * k / n)} | {k} {'av' if sv else 'of'} {n}")
    rows.append("Sagornas prosa; vättarna är inte medräknade. Diagram: Vitki, efter Vitkis räkning i texterna från sagadb.org och heimskringla.no."
                if sv else "The prose of the sagas; the vættir are not counted. Chart: Vitki, from Vitki's count in the texts from sagadb.org and heimskringla.no.")
    return "\n".join(rows) + "\n:::"


CL = [("jättar", "jättar och troll", "giants and trolls"), ("odjur", "odjur", "monsters"), ("dvärgar", "dvärgar", "dwarves"),
      ("diser och nornor", "diser, nornor, valkyrior, fylgjor", "dísir, norns, valkyries, fylgjur")]


def chart_kinds(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Vilka väsen? Andel av träffarna i varje slags text' if sv else 'Which beings? Share of the hits in each kind of text'}"]
    for c in ("eddadikter", "fornaldarsagor", "islanningasagor"):
        rows.append(f"# {LAB[c][0 if sv else 1]}")
        for kl, lsv, len_ in CL:
            hl = "+" if (c == "islanningasagor" and kl == "jättar") else ""
            rows.append(f"{hl}{lsv if sv else len_} | {share(c, kl)} | ")
    rows.append("Övriga väsen (alver, gengångare, nattväsen, änglar och djävulen) är de procent som fattas. Diagram: Vitki."
                if sv else "Other beings (elves, the walking dead, night-riders, angels and the devil) are the missing per cent. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


# ======================================================================================================================
# 5. Texten
# ======================================================================================================================
title = "Var bodde trollen? Mest i forntiden, sällan på Island"
summary = (f"Vi räknade jättar, dvärgar, alver, nornor, gengångare och odjur i {MILJ_SV} miljoner ord fornnordisk litteratur. "
           "De bor i myten och i sagorna om forntiden – fornaldarsagorna nämner dem nästan sex gånger så ofta som islänningasagorna – "
           "och runstenarnas texter nämner dem inte alls.")

body = f"""Den som öppnar Heimskringla väntar sig kanske troll. Kungasagorna handlar om en tid då folk fortfarande blotade, och Olav Tryggvason seglar längs Norges kust för att kristna landet. Men på ett ställe stannar Snorre Sturlasson upp och säger rakt ut vad han tänker lämna därhän:

> {q('snorre')}

”Och på den färden hände mycket som berättas, att troll och onda väsen retades med hans män och ibland med honom själv; men vi vill hellre skriva om hur kung Olav kristnade Norge.”

Trollen fanns alltså i berättelserna. Snorre valde bort dem. Vi ville veta hur ofta andra skrivare gjorde samma val – och var väsendena hamnade när de fick vara kvar.

## Ett bestiarium i nio fack

Först behövde vi en lista. Den fornnordiska litteraturen har inget register över sina väsen, så vi gjorde ett: 30 ord i nio grupper, skrivna både med fornisländsk och nutida isländsk stavning, och frysta innan vi räknade något. Gudarna är inte med, inte heller människor med särskilda förmågor som berserkar och völvor. Sedan lät vi listan gå igenom {sv_n(N_TEXTS)} sagor, dikter och skrifter, {MILJ_SV} miljoner ord. Det här är vad den fann.

**Jättarna** är flest överallt. I eddadikterna är {ED_JATT} procent av alla väsen jättar, och hos Snorre i Gylfaginning {GY_JATT} procent. Där har de namn: Ymer, Trym, Skrymer, Hrungner, Suttung, Vafþrudner, Hymer, Tjatse, Utgårdaloke. I sagorna heter de oftare bara *jötunn*, *risi*, *þurs*, *flagð* – och framför allt *tröll*.

**Odjuren** är nästan alla namngivna: Fafner, Fenrisulven, Midgårdsormen, Nidhögg, Sleipner, korparna Hugin och Munin, ekorren Ratatosk. Kon Audhumla hör också hit. Hos Snorre är det hon som håller liv i den första jätten:

> {q('audhumla')}

”… en ko som hette Audhumla, och fyra mjölkfloder rann ur hennes spenar, och hon födde Ymer.”

![Audhumla i en isländsk handskrift från 1700-talet]({AUDHUMLA[0]})
Audhumla slickar fram Bure ur rimfrosten medan fyra mjölkfloder rinner ur spenarna. Isländsk handskrift från 1700-talet (SÁM 66, Árni Magnússon-institutet). Teckning: {AUDHUMLA[2]}, {AUDHUMLA[3]}, via [Wikimedia Commons]({AUDHUMLA[1]}).

**Dvärgarna** finns i myten och i fornaldarsagorna. I Sörla þáttr får de en förklaring som nästan låter som en folkbokföring: *{q('dverga')}* – ”sådana män som de var kallade man dvärgar.”

**Alverna** är få, bara ett par dussin träffar, men de förekommer på oväntade ställen. I Kormáks saga får en sårad man rådet att söka sig till en kulle i närheten, *{q('kormak_hol')}* – ”där alver bor” – och *{q('kormak')}*: ”hålla gästabud för alverna med köttet, så blir du bättre.” I Heimskringla vandrar skalden Sigvat genom Götaland, i dagens Sverige, och blir nekad husrum en kväll: *{q('sigvat')}* – ”där stod husfrun i dörren och bad honom inte komma in, och sade att de höll alvablot.” I fornaldarsagorna kan alverna gifta in sig i kungaätter. Kung Helge i Hrólfs saga kraka släpper en natt in en eländig kvinna som visar sig vara mycket vacker. Tre år senare förs ett barn till honom, och berättaren konstaterar efteråt: *{q('alfkona')}* – ”det hade varit en alvkvinna.” Deras dotter Skuld blir sagans stora trollkvinna.

**Diserna, nornorna, valkyriorna och fylgjorna** är de kvinnliga väsen som håller i ödet. I Njals saga ser Tord en blodig bock på gården där ingen bock finns, och Njal säger lugnt: ”du har nog sett din fylgja” – *{q('njal')}*.

**De döda som går igen** – draugar, högbor, gengångare – är färre än man tror. Grettir halshugger en högbo, *{q('grettir')}*, men orden är få.

**Nattväsendena** är maran och gärdsgårdsriderskorna. Hávamál har en galder mot dem: *{q('tunridur')}*, ”om jag ser gärdsgårdsriderskor leka uppe i luften.”

**Vättarna** – landvättar, onda vättar, *meinvættir* – fanns på listan, men vi lyckades inte räkna dem säkert. Mer om det längre ned.

**Änglarna och djävulen** är också väsen, och de dyker upp även i de gamla berättelserna. De är få, men de är där.

## Där väsendena bor

Sedan räknade vi tätheten: hur många väsen texten nämner per tiotusen ord, ungefär en tunn saga.

- **Snorres Gylfaginning**: {sv_n(round(V2['snorra_edda_gylfaginning']))} väsen per tiotusen ord
- **Eddadikterna**: {sv_n(round(V2['eddadikter']))}
- **Fornaldarsagorna**, sagorna om tiden före Islands bosättning: {sv_d(V2['fornaldarsagor'])}
- **Islänningasagorna**, sagorna om de första generationerna på Island: {sv_d(V2['islanningasagor'])}
- **Samtidssagorna** om 1200-talet: {sv_d(V2['samtidssagor'])}
- **Heimskringlas** kungasagor: {sv_d(V2['heimskringla'])}

Det är en trappa nedåt från myten till historien. Det tydligaste steget går mellan fornaldarsagorna och islänningasagorna. Båda skrevs ned på Island under 1200- och 1300-talen. Men fornaldarsagorna nämner väsen **nästan sex gånger så ofta** ({sv_d(T1['kvot'])} gånger; med den osäkerhet som finns i materialet sannolikt någonstans mellan {sv_d(T1['intervall'][0])} och {sv_d(T1['intervall'][1], 0)} gånger). En så tydlig skillnad skulle uppstå av en slump i färre än ett fall på tiotusen.

{chart_texts('sv')}

Vi prövade om skillnaden hänger på enskilda ord eller sagor. Utan ordet *tröll* blir den större, {sv_d(T1_TROLL['kvot'])} gånger. Utan den största sagan är den {sv_d(T1_BIG['kvot'])} gånger. Väsendena hör alltså till forntiden, inte till ett enda ord eller en enda berättare.

Heimskringla bekräftar mönstret inifrån. Av kungasagornas {HK_HITS} väsen står {HK['Ynglinga saga']} i Ynglinga saga, den del som handlar om de mytiska kungarna före den historiska tiden. Där finns maran som trampar ihjäl kung Vanlande i Uppsala: *{q('vanlande')}* – ”han ropade och sade att maran trampade på honom.” När Snorre kommer fram till kungar som folk fortfarande mindes, blir det nästan tyst: de övriga tio fördelar sig på fyra långa sagor.

## Trollet – ett ord, inte en bild

Det vanligaste väsensordet i både fornaldarsagorna och islänningasagorna är *tröll*. Men ordet säger inget om hur trollen ser ut. Det står gärna i sällskap: ”troll och onda väsen” hos Snorre, *{q('bard2')}* – ”risar och troll och onda väsen” – i Bárðar saga. Ordet verkar stå för något farligt utanför människornas värld snarare än för en bestämd varelse.

![Troll av John Bauer]({BAUER[0]})
Så ser trollen ut för oss: John Bauers teckning, i dag på Nationalmuseum. Bilden är 1900-talets, inte sagornas. Teckning: {BAUER[2]} (1882–1918), {BAUER[3]}, via [Wikimedia Commons]({BAUER[1]}).

Islänningasagorna har trollen, men få av dem. {IS_NONE} av de 42 sagorna nämner inget väsen alls, och dvärgarna saknas helt i deras prosa. Den saga som har flest är ett undantag: Bárðar saga, där huvudpersonens *{q('bard')}* – ”mor härstammade från trollsläkter”. Den ensam står för {BARD_PC} procent av alla väsen i islänningasagorna. Utan den blir skillnaden mot fornaldarsagorna ännu större, omkring {sv_d(RATIO_NOBARD, 0)} gånger.

{chart_kinds('sv')}

Jättarna dominerar överallt. Det som skiljer är odjuren: de är en femtedel av väsendena i Eddan och fornaldarsagorna, men bara {IS_ODJ} procent på Island, där dvärgarna saknas helt.

![Fenrisulven i en isländsk handskrift från 1600-talet]({FENRIR[0]})
Fenrisulven i en isländsk handskrift från omkring 1680 (AM 738 4to, blad 43v). Islänningasagorna nämner nästan aldrig sådana odjur. Teckning: {FENRIR[2]}, {FENRIR[3]}, via [Wikimedia Commons]({FENRIR[1]}).

## Stenen som visar men inte säger

![Ramsundsberget, Sö 101]({RAMSUND[0]})
Sigurd stöter svärdet i Fafner på Ramsundsberget i Södermanland (Sö 101). Ristningen är full av sagans väsen, men runorna handlar om en bro. Foto: {RAMSUND[2]}, {RAMSUND[3]}, via [Wikimedia Commons]({RAMSUND[1]}).

Samma lista fick gå igenom texterna på alla {sv_n(N_STONES)} svenska runstenar från vikingatiden. Den hittade två ord. Båda var falska: på Karlevistenen på Öland är *draugr* en skaldisk omskrivning för en krigare, och på U 703 betyder *risinn* ”rest”. **Runstenarnas texter nämner inga väsen.** Väsendena finns på stenarna, men i bilderna: Fafner på Ramsundsberget, Midgårdsormen på Altunastenen. Det runristarna skrev var namn, släkt och böner.

## Det vi inte kunde räkna

- **Gengångarna är underskattade.** De döda som går igen i islänningasagorna beskrivs ofta med ett verb, ”han gick igen”, i stället för ett substantiv. Den frasen kan också betyda att någon gick tillbaka, så vi räknade den inte. Därför kan vi inte säga om de döda är vanligare i islänningasagorna än i fornaldarsagorna, och vårt test av det gav inget svar.
- **Vättarna gick inte att räkna säkert.** *Vætt* är också en viktenhet, och verbet *vætta* betyder att vänta sig. Ett stickprov visade för många fel även efter en rättelse, så vättarna är bara med som exempel här, inte i jämförelserna.
- **Samtidssagorna är för få.** Sex texter med sju väsen, och tre av dem är djävulen. Det räcker inte för en jämförelse.
- **Versen är något annat.** Skaldestroferna nämner väsen tio till tjugofem gånger tätare än prosan runt dem, men ofta som bilder: en jättes namn för guld, en korps namn för en korp.

Ett stickprov av träffarna lästes i sitt sammanhang för att se om ordet verkligen avsåg ett väsen. {GATE} procent gjorde det. Stickprovet bedömdes med Anthropics språkmodell Claude (Claude Opus), och varje citat i artikeln är kontrollerat mot texten. Reglerna låstes innan vi räknade, i [en analysplan]({PLAN}), och alla siffror finns i [resultatet]({RES}).

Antal ord är inte tro. Att en saga nämner troll visar vad en berättare på 1200- eller 1300-talet valde att ta med, inte vad någon på vikingatiden trodde på.

## Läs själv

Nästa gång du läser en islänningasaga, håll räkningen på väsendena. Det går fort. Läs sedan Ynglinga saga, kapitlet om Vanlande, och känn skillnaden. Snorre skrev båda sorternas historia – och han visste precis var trollen hörde hemma.

Samma mönster syntes när vi räknade platser: fornaldarsagorna blickar mot öster och mot en annan värld än islänningasagorna ([Vikingarnas värld](/artiklar/vikingarnas-varld)). Om de magiska formlerna på runstenarna har vi skrivit i [Den som bryter denna sten](/artiklar/den-som-bryter-denna-sten).

:::box Det viktigaste i korthet
- Väsendena bor i myten och i sagorna om forntiden. Fornaldarsagorna nämner dem nästan sex gånger så ofta som islänningasagorna, fast båda skrevs på samma ö under samma århundraden.
- Trollet är sagornas vanligaste väsen, men som ett ord för det farliga och främmande, inte som en bestämd gestalt.
- Även Heimskringla har nästan hälften av sina väsen i den mytiska förhistorien. Snorre skriver själv att han hellre berättar om kristnandet än om trollen.
- Runstenarna visar väsen i bilderna men nämner dem inte i texten.
:::

## Källor

Islänningasagorna: sagadb.org (Sveinbjörn Þórðarson), nutida isländsk stavning, public domain. Heimskringla: heimskringla.no, utgåvan av N. Linder och H. A. Haggson (1869–72), public domain. Fornaldarsagorna, samtidssagorna, eddadikterna och Snorres Edda: heimskringla.no, Guðni Jónssons m.fl. utgåvor; texterna används här bara för räkning och korta citat. Tack till heimskringla.no för texterna. Runstenarna: Samnordisk runtextdatabas, version 3.1 (2018), Uppsala universitet. Översättningarna är våra egna. Ordlistan, reglerna och skripten: [analysplanen]({PLAN}) med ett tillägg."""

title_en = "Where did the trolls live? Mostly in the ancient past, rarely in Iceland"
summary_en = (f"We counted giants, dwarves, elves, norns, the walking dead and monsters in {MILJ_EN} million words of Old Norse literature. "
              "They live in myth and in the sagas of the ancient past – the legendary sagas mention them almost six times as often as the sagas of Icelanders – "
              "and the runestone texts do not mention them at all.")

body_en = f"""Anyone opening Heimskringla might expect trolls. The kings' sagas tell of a time when people still made sacrifices, and Óláfr Tryggvason sails along the coast of Norway to make the land Christian. But at one point Snorri Sturluson stops and says plainly what he intends to leave out:

> {q('snorre')}

“And on that voyage much happened that is told in stories, that trolls and evil beings teased his men and sometimes himself; but we would rather write about how King Óláfr made Norway Christian.”

So the trolls were there in the stories. Snorri left them out. We wanted to know how often other writers made the same choice – and where the beings ended up when they were allowed to stay.

## A bestiary in nine compartments

First we needed a list. Old Norse literature keeps no register of its beings, so we made one: 30 words in nine groups, spelled both in Old Icelandic and in modern Icelandic, and frozen before we counted anything. The gods are not included, nor are people with special powers such as berserks and seeresses. Then we ran the list through {en_n(N_TEXTS)} sagas, poems and treatises, {MILJ_EN} million words. This is what it found.

**The giants** are the most numerous everywhere. In the Eddic poems {ED_JATT} per cent of all beings are giants, and in Snorri's Gylfaginning {GY_JATT} per cent. There they have names: Ymir, Þrymr, Skrýmir, Hrungnir, Suttungr, Vafþrúðnir, Hymir, Þjazi, Útgarða-Loki. In the sagas they are more often just *jötunn*, *risi*, *þurs*, *flagð* – and above all *tröll*.

**The monsters** are almost all named: Fáfnir, the wolf Fenrir, the Midgard Serpent, Níðhöggr, Sleipnir, the ravens Huginn and Muninn, the squirrel Ratatoskr. The cow Auðhumla belongs here too. In Snorri she is the one who keeps the first giant alive:

> {q('audhumla')}

“… a cow called Auðhumla, and four rivers of milk ran from her teats, and she fed Ymir.”

![Auðhumla in an Icelandic manuscript of the 18th century]({AUDHUMLA[0]})
Auðhumla licks Búri out of the rime while four rivers of milk run from her teats. Icelandic manuscript of the 18th century (SÁM 66, the Árni Magnússon Institute). Drawing: unknown artist, public domain, via [Wikimedia Commons]({AUDHUMLA[1]}).

**The dwarves** live in myth and in the legendary sagas. In Sörla þáttr they get an explanation that sounds almost like a census entry: *{q('dverga')}* – “men such as they were, people called dwarves.”

**The elves** are few, only a couple of dozen hits, but they turn up in unexpected places. In Kormáks saga a wounded man is advised to go to a hill nearby, *{q('kormak_hol')}* – “where elves live” – and *{q('kormak')}*: “hold a feast for the elves with the meat, and you will get better.” In Heimskringla the poet Sigvatr travels through Götaland, in today's Sweden, and is turned away one evening: *{q('sigvat')}* – “the housewife stood in the door and told him not to come in, saying that they were holding a sacrifice to the elves.” In the legendary sagas elves can marry into royal lines. King Helgi in Hrólfs saga kraka lets in a wretched woman one night who turns out to be very beautiful. Three years later a child is brought to him, and the storyteller notes: *{q('alfkona')}* – “it had been an elf-woman.” Their daughter Skuld becomes the saga's great sorceress.

**The dísir, norns, valkyries and fylgjur** are the female beings who hold fate. In Njáls saga Þórðr sees a bloody goat on the farm where there is no goat, and Njáll says calmly: “you must have seen your fylgja” – *{q('njal')}*.

**The dead who walk again** – draugar, mound-dwellers, revenants – are fewer than one might think. Grettir beheads a mound-dweller, *{q('grettir')}*, but the words are few.

**The night-riders** are the mara and the fence-riders. Hávamál has a spell against them: *{q('tunridur')}*, “if I see fence-riders playing up in the air.”

**The vættir** – land-spirits, evil wights, *meinvættir* – were on the list, but we could not count them reliably. More on that below.

**The angels and the devil** are beings too, and they appear even in the old stories. They are few, but they are there.

## Where the beings live

Then we counted the density: how many beings a text mentions per ten thousand words, roughly one short saga.

- **Snorri's Gylfaginning**: {round(V2['snorra_edda_gylfaginning'])} beings per ten thousand words
- **The Eddic poems**: {round(V2['eddadikter'])}
- **The legendary sagas**, about the time before Iceland was settled: {V2['fornaldarsagor']:.1f}
- **The sagas of Icelanders**, about the first generations in Iceland: {V2['islanningasagor']:.1f}
- **The contemporary sagas** of the 13th century: {V2['samtidssagor']:.1f}
- **Heimskringla's** kings' sagas: {V2['heimskringla']:.1f}

It is a staircase down from myth to history. The clearest step lies between the legendary sagas and the sagas of Icelanders. Both were written down in Iceland in the 13th and 14th centuries. But the legendary sagas mention beings **almost six times as often** ({T1['kvot']:.2f} times; given the uncertainty in the material, probably somewhere between {T1['intervall'][0]:.1f} and {T1['intervall'][1]:.0f} times). A difference this clear would arise by chance in fewer than one case in ten thousand.

{chart_texts('en')}

We checked whether the difference hangs on single words or sagas. Without the word *tröll* it grows, to {T1_TROLL['kvot']:.1f} times. Without the largest saga it is {T1_BIG['kvot']:.1f} times. The beings belong to the ancient past, not to one word or one storyteller.

Heimskringla confirms the pattern from the inside. Of the kings' sagas' {HK_HITS} beings, {HK['Ynglinga saga']} stand in Ynglinga saga, the part about the mythical kings before historical time. There we meet the mara that tramples King Vanlandi to death at Uppsala: *{q('vanlande')}* – “he called out and said that the mara was trampling him.” When Snorri reaches kings that people still remembered, it falls almost silent: the other ten are spread over four long sagas.

## The troll – a word, not a picture

The commonest word for a being in both the legendary sagas and the sagas of Icelanders is *tröll*. But the word says nothing about what trolls look like. It likes company: “trolls and evil beings” in Snorri, *{q('bard2')}* – “giants and trolls and evil beings” – in Bárðar saga. The word seems to stand for something dangerous outside the human world rather than for a particular creature.

![Troll by John Bauer]({BAUER[0]})
This is how trolls look to us: John Bauer's drawing, now in the Nationalmuseum, Stockholm. The picture belongs to the 20th century, not to the sagas. Drawing: {BAUER[2]} (1882–1918), {BAUER[3]}, via [Wikimedia Commons]({BAUER[1]}).

The sagas of Icelanders have their trolls, but few of them. {IS_NONE} of the 42 sagas mention no being at all, and the dwarves are entirely missing from their prose. The saga with the most is an exception: Bárðar saga, whose hero's *{q('bard')}* – “mother came of troll kin”. It alone accounts for {BARD_PC} per cent of all beings in the sagas of Icelanders. Without it the difference from the legendary sagas grows to about {RATIO_NOBARD:.0f} times.

{chart_kinds('en')}

The giants dominate everywhere. What differs is the monsters: a fifth of the beings in the Edda and the legendary sagas, but only {IS_ODJ} per cent in Iceland, where the dwarves are missing altogether.

![Fenrir in an Icelandic manuscript of the 17th century]({FENRIR[0]})
The wolf Fenrir in an Icelandic manuscript of about 1680 (AM 738 4to, leaf 43v). The sagas of Icelanders almost never mention such monsters. Drawing: unknown artist, public domain, via [Wikimedia Commons]({FENRIR[1]}).

## The stone that shows but does not say

![Ramsundsberget, Sö 101]({RAMSUND[0]})
Sigurðr drives his sword into Fáfnir on the Ramsund rock in Södermanland (Sö 101). The carving is full of the saga's beings, but the runes are about a bridge. Photo: {RAMSUND[2]}, {RAMSUND[3]}, via [Wikimedia Commons]({RAMSUND[1]}).

The same list was run through the texts of all {en_n(N_STONES)} Swedish runestones of the Viking Age. It found two words. Both were false: on the Karlevi stone on Öland *draugr* is a poetic circumlocution for a warrior, and on U 703 *risinn* means “raised”. **The runestone texts mention no beings.** The beings are on the stones, but in the pictures: Fáfnir at Ramsund, the Midgard Serpent on the Altuna stone. What the carvers wrote were names, kin and prayers.

## What we could not count

- **The walking dead are undercounted.** The dead who walk again in the sagas of Icelanders are often described with a verb, “he walked again”, rather than a noun. The phrase can also mean that someone went back, so we did not count it. We therefore cannot say whether the dead are more common in the sagas of Icelanders than in the legendary sagas, and our test of it gave no answer.
- **The vættir could not be counted reliably.** *Vætt* is also a unit of weight, and the verb *vætta* means to expect. A sample showed too many errors even after a correction, so the vættir appear here only as examples, not in the comparisons.
- **The contemporary sagas are too few.** Six texts with seven beings, three of them the devil. That is not enough for a comparison.
- **Verse is something else.** The skaldic stanzas mention beings ten to twenty-five times as densely as the prose around them, but often as images: a giant's name for gold, a raven's name for a raven.

A sample of the hits was read in context to see whether the word really meant a being. {GATE} per cent did. The sample was judged with Anthropic's language model Claude (Claude Opus), and every quotation in the article is checked against the text. The rules were locked before we counted, in [an analysis plan]({PLAN}), and all figures are in [the results]({RES}).

Counting words is not counting belief. That a saga mentions trolls shows what a storyteller of the 13th or 14th century chose to include, not what anyone in the Viking Age believed in.

## Read for yourself

Next time you read a saga of Icelanders, keep count of the beings. It goes quickly. Then read Ynglinga saga, the chapter on Vanlandi, and feel the difference. Snorri wrote both kinds of history – and he knew exactly where the trolls belonged.

The same pattern appeared when we counted places: the legendary sagas look east, to another world than the sagas of Icelanders ([The Vikings' world](/en/artiklar/vikingarnas-varld)). On the magic formulas on the runestones we wrote in [Whoever breaks this stone](/en/artiklar/den-som-bryter-denna-sten).

:::box The essentials in brief
- The beings live in myth and in the sagas of the ancient past. The legendary sagas mention them almost six times as often as the sagas of Icelanders, although both were written on the same island in the same centuries.
- The troll is the sagas' commonest being, but as a word for the dangerous and alien, not as a particular figure.
- Even Heimskringla keeps almost half of its beings in the mythical prehistory. Snorri writes himself that he would rather tell of the conversion than of the trolls.
- The runestones show beings in their pictures but do not name them in their texts.
:::

## Sources

The sagas of Icelanders: sagadb.org (Sveinbjörn Þórðarson), modern Icelandic spelling, public domain. Heimskringla: heimskringla.no, the edition by N. Linder and H. A. Haggson (1869–72), public domain. The legendary sagas, the contemporary sagas, the Eddic poems and Snorri's Edda: heimskringla.no, editions by Guðni Jónsson and others; the texts are used here only for counting and short quotations. Thanks to heimskringla.no for the texts. The runestones: Scandinavian Runic-text Database (Samnordisk runtextdatabas), version 3.1 (2018), Uppsala University. The translations are our own. The word list, the rules and the scripts: [the analysis plan]({PLAN}) with one addendum."""

# ======================================================================================================================
# 6. Kontroller och skrivning
# ======================================================================================================================
HOLDBACK = re.compile(r"\bAI\b|signifikan|p-värde|p-value|bootstrap|\bHolm\b", re.I)
labels = ["Forskning", "Eddan", "Tro och magi"]
assert blog_labels.check(labels) is None, blog_labels.check(labels)
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not HOLDBACK.search(b), (lang, HOLDBACK.search(b).group(0))
    assert not re.search(r"^\|", b, re.M), "inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index(":::box") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 4 and all(re.match(r"https://(upload|thumb)\.wikimedia\.org/", u) for u in imgs), imgs
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
path = os.path.join(ROOT, "utdata", "blogg", "vasen.json")
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
                 "topic": "Eddan och sagorna|väsen", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id, SLUG)
    blog._forget()
