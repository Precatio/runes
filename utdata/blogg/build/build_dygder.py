"""Artikeln "Mild i ord och god på mat": vad runstenarna och Hávamál håller för en god människa. Ett porträtt drag för
drag, med en sten och en strof bredvid varandra. Siffrorna låses mot utdata/dygder (dygder_runstenar.py,
dygder_edda.py, havamal_teman.csv, dygder_test.json); varje citerad sten står ordagrant som i Rundatas normalisering
och varje strof som i havamal_strofer.csv.
    ../../../.venv/bin/python build_dygder.py [--write | --update DOC]"""
import csv
import datetime as dt
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src import commons  # noqa: E402

D = os.path.join(ROOT, "utdata", "dygder")
R = json.load(open(os.path.join(D, "dygder_runstenar.json"), encoding="utf-8"))
E = json.load(open(os.path.join(D, "dygder_edda.json"), encoding="utf-8"))
T = json.load(open(os.path.join(D, "dygder_test.json"), encoding="utf-8"))
STROF = {int(r["nr"]): r for r in csv.DictReader(open(os.path.join(ROOT, "utdata", "Edda", "havamal_strofer.csv"), encoding="utf-8"))}
TEMAN = {int(r["nr"]): r["teman"].split(";") for r in csv.DictReader(open(os.path.join(D, "havamal_teman.csv"), encoding="utf-8"))}

svn = lambda x, d=1: f"{x:.{d}f}".replace(".", ",")  # noqa: E731
pct = lambda k, n: round(100 * k / n)  # noqa: E731
tus = lambda x: f"{int(x):,}".replace(",", " ")  # noqa: E731

# ---- the runestones ------------------------------------------------------------------------------------------------
N = R["n_runstenar"]
EG, GA = R["egenskaper"], R["garningar"]
N_EG = R["n_med_egenskap"]
assert N == 2633 and N_EG == 293 and EG["god"] == 213 and EG["drengr"] == 74 and EG["þegn"] == 47
assert EG["modig"] == 9 and EG["givmild"] == 7 and EG["ord_och_rad"] == 6 and EG["heder"] == 17 and EG["framst"] == 18
assert GA["strid"] == 51 and GA["bro_och_vag"] == 117 and GA["kristen_bon"] == 315 and GA["gard_och_arv"] == 65
RESOR = GA["resa_osterut"] + GA["resa_vasterut"]
assert T["drengr"]["n"] == 74 and T["drengr"]["k"] == 11 and T["drengr"]["p"] < 1e-4
assert T["þegn"]["n"] == 47 and T["þegn"]["k"] == 3 and T["þegn"]["p"] > 0.2
assert T["alla"]["k"] == 99 and T["egenskap_men_inte_krig"] == 273
MOD_PLUS_STRID = EG["modig"]  # the brave as a quality; the fallen are deeds, counted apart

# the quoted stones, verbatim from Rundata's Old West Norse normalisation
S = store()


def sten(sig, *bitar):
    t = S.get(sig)["normalization_ows"]
    for b in bitar:
        assert b in t, (sig, b)
    return t


sten("Sö 130", "mildan orða ok matar góðan")
sten("Sm 44", "mil[dan við] sinna [ok]", "matar góðan, í orðlofi allra m[ikl]u")
sten("DR 291", "beztr búmanna ok mildastr matar")
sten("U 739", "mildr matar ok málsrisinn")
sten("U 1146", "hinn málspaka")
sten("Sö 338", "heldu sína húskarla ve[l]", "beztra manna, á landi ok í liði úti")
sten("DR 68", "Sá dó manna mest óníðingr")
sten("N 68", "Sú var mær hônnurst á")
sten("U 654", "Er kunni vel knerri stýra")
sten("Vs 24", "Kemr hýfreyja til", "eigi betri, en býi ráðr")
sten("DR 212", "Æ mun standa, með steinn lifir")
sten("Sö 140", "Engi fœðir son snjallara")
sten("DR 295", "Sá fló eigi at")
sten("Sm 35", "þann frænda ok þegna beztan")
sten("U 1011", "slœgjastr manna")

# ---- Hávamál ---------------------------------------------------------------------------------------------------------
def strof(nr, *bitar):
    t = STROF[nr]["text"]
    for b in bitar:
        assert b in t, (nr, b)
    return t


strof(39, "mildan mann eða svá matar góðan")
strof(72, "bautarsteinar standa brautu nær, nema reisi niðr at nið")
strof(76, "orðstírr deyr aldregi")
strof(52, "með halfum hleif ok með höllu keri fekk ek mér félaga")
strof(48, "Mildir, fræknir menn bazt lifa")
strof(135, "get þú váluðum vel")
strof(134, "at hárum þul hlæ þú aldregi")
strof(16, "Ósnjallr maðr hyggsk munu ey lifa")
strof(4, "orðs ok endrþögu")
strof(133, "er-at maðr svá góðr at galli né fylgi")
strof(126, "skósmiðr þú verir né skeftismiðr")

RAD = [nr for nr in STROF if STROF[nr]["del"] in ("I", "IV")]
assert len(RAD) == 110 and len(STROF) == 164 and len(TEMAN) == 164
tc = Counter(t for nr in RAD for t in TEMAN[nr])
andel = {k: pct(v, len(RAD)) for k, v in tc.items()}
assert andel["VÄN"] == 20 and andel["ORD"] == 19 and andel["VETT"] == 18 and andel["GÄST"] == 14 and andel["MÅTTA"] == 14
assert andel["MOD"] == 6 and andel["GÅVA"] == 7 and andel["RYKTE"] == 7 and andel["OMSORG"] == 5
assert "MOD" in TEMAN[16] and "GÅVA" in TEMAN[39] and "RYKTE" in TEMAN[76] and "OMSORG" in TEMAN[135]

G = E["grupper"]
H, GU, HJ, KR = G["Hávamál"], G["gudadikter"], G["hjältedikter"], G["kristna"]
assert H["hämnd"] == 0 and HJ["strid"] > H["strid"] > KR["strid"] and H["vänskap"] > 6 and HJ["vänskap"] < 1
assert H["förstånd"] > 10 and HJ["hämnd"] > 0.8 and H["gästfrihet"] > 3.5 and HJ["gästfrihet"] < 0.3
assert KR["hämnd"] > 0 and GU["hämnd"] > 0
NIO_AV_TIO = T["egenskap_men_inte_krig"] / N_EG
assert 0.9 <= NIO_AV_TIO < 0.95 and 0.83 <= (T["drengr"]["n"] - T["drengr"]["k"]) / T["drengr"]["n"] <= 0.87
assert 3.5 <= (T["drengr"]["k"] / T["drengr"]["n"]) / (T["alla"]["k"] / T["alla"]["n"]) <= 4.5 and 1 / T["drengr"]["p"] > 10000

# ---- photographs from Wikimedia Commons (via Wikidata), credits pinned ----------------------------------------------
FILES = {**commons.wikidata_files(["Sö 130"]), "Codex Regius": "GKS 2365 4to, 0017r - 42.jpg"}
INFO = commons.commons_info([FILES[s] for s in FILES])
CREDIT = {"Sö 130": ("Berig", "CC BY-SA 3.0"), "Codex Regius": ("Thorsteinn1996", "CC BY-SA 4.0")}


def photo(signum: str, text: str, lang: str = "sv") -> str:
    img = {**INFO[FILES[signum]], "signum": signum}
    assert (img["author"], img["licence"]) == CREDIT[signum], (signum, img["author"], img["licence"])
    cap = commons.caption(img, lang)
    lead = f"{signum}. Foto: " if lang == "sv" else f"{signum}. Photo: "
    assert cap.startswith(lead)
    alt = (f"Runstenen {signum}" if lang == "sv" else f"The runestone {signum}") if signum != "Codex Regius" else (
        "Ett blad ur Codex Regius" if lang == "sv" else "A leaf of Codex Regius")
    rest = cap[len(lead):]
    for raw, shown in SHOWN.items():  # the file pages name the photographers; the author field has uploader or museum text
        rest = rest.replace(raw, shown)
    return f"![{alt}]({img['thumb']})\n{text} {'Foto' if lang == 'sv' else 'Photo'}: {rest}"


SHOWN: dict[str, str] = {}  # photographer names to show instead of the author field, when they differ
PH_130 = photo("Sö 130", "Hagstugan (Sö 130) i Sparsta, Södermanland: fyra söner åt sin far, ”mild i ord och god på mat”. Stenen är en av sju med formeln.")
PH_130_EN = photo("Sö 130", "Hagstugan (Sö 130) at Sparsta, Södermanland: four sons for their father, “gentle in speech and free with food”. One of seven stones with the formula.", "en")
CR = photo("Codex Regius", "Ett blad ur Codex Regius (GKS 2365 4to, fol. 17r), handskriften från omkring 1270 som är Hávamáls enda medeltida källa. På det här bladet börjar Þrymskviða.")
CR_EN = photo("Codex Regius", "A leaf of Codex Regius (GKS 2365 4to, fol. 17r), the manuscript of about 1270 that is Hávamál's only medieval source. On this leaf Þrymskviða begins.", "en")

# ---- figures -----------------------------------------------------------------------------------------------------------
CHART = f""":::chart Vad runstenarna säger om den döde, antal stenar av {tus(N)} vikingatida runstenar
# Egenskaper
+god (góðr) | {EG['god']} | {EG['god']} stenar
drengr, pålitlig man | {EG['drengr']} | {EG['drengr']}
þegn, fri man av stånd | {EG['þegn']} | {EG['þegn']}
den bäste, den främste | {EG['framst']} | {EG['framst']}
utan skam, duglig | {EG['heder']} | {EG['heder']}
duktig (snjallr) | {EG['duktig']} | {EG['duktig']}
+givmild, god på mat | {EG['givmild']} | {EG['givmild']}
+mild i ord, vältalig, vis | {EG['ord_och_rad']} | {EG['ord_och_rad']}
modig, flydde inte | {EG['modig']} | {EG['modig']}
# Gärningar
kristen bön för själen | {GA['kristen_bon']} | {GA['kristen_bon']}
+byggde bro eller väg | {GA['bro_och_vag']} | {GA['bro_och_vag']}
gård, arv, ägande | {GA['gard_och_arv']} | {GA['gard_och_arv']}
resa österut eller västerut | {RESOR} | {RESOR}
stupade eller dräptes | {GA['strid']} | {GA['strid']}
handel, skepp, styrman | {GA['handel_och_skepp']} | {GA['handel_och_skepp']}
Källa: Samnordisk runtextdatabas 3.1, vikingatida runstenar och fragment i hela Norden, räknade i den fornvästnordiska normaliseringen. Vitkis beräkning; en sten räknas en gång per kategori.
:::"""

CHART_HAV = f""":::chart Vad Hávamáls råd handlar om, andel av de {len(RAD)} rådstroferna (del I och Loddfáfnismál)
+vänskap | {andel['VÄN']} | {tc['VÄN']} strofer
+ord och tystnad | {andel['ORD']} | {tc['ORD']}
+förstånd | {andel['VETT']} | {tc['VETT']}
gästfrihet | {andel['GÄST']} | {tc['GÄST']}
måtta | {andel['MÅTTA']} | {tc['MÅTTA']}
försiktighet | {andel['VAR']} | {tc['VAR']}
livets värde | {andel['LIV']} | {tc['LIV']}
eget hem och flit | {andel['HEM']} | {tc['HEM']}
rykte och eftermäle | {andel['RYKTE']} | {tc['RYKTE']}
gåvor | {andel['GÅVA']} | {tc['GÅVA']}
mod och strid | {andel['MOD']} | {tc['MOD']}
omsorg om andra | {andel['OMSORG']} | {tc['OMSORG']}
Källa: vår läsning av Codex Regius-texten (Guðni Jónssons normalisering), en eller flera teman per strof; listan ligger öppen i kodförrådet (utdata/dygder/havamal_teman.csv).
:::"""

CHART_EDDA = f""":::chart Värdeord per tusen ord i fyra grupper av eddadikter
# vänskap (vinr, tryggð, félagi)
+Hávamál | {svn(H['vänskap'])} | {H['antal'].get('vänskap', 0)} ord av {tus(H['n_ord'])}
gudadikterna | {svn(GU['vänskap'])} | {GU['antal'].get('vänskap', 0)} av {tus(GU['n_ord'])}
hjältedikterna | {svn(HJ['vänskap'])} | {HJ['antal'].get('vänskap', 0)} av {tus(HJ['n_ord'])}
de kristna dikterna | {svn(KR['vänskap'])} | {KR['antal'].get('vänskap', 0)} av {tus(KR['n_ord'])}
# förstånd (mannvit, horskr, fróðr, snotr …)
+Hávamál | {svn(H['förstånd'])} | {H['antal'].get('förstånd', 0)}
gudadikterna | {svn(GU['förstånd'])} | {GU['antal'].get('förstånd', 0)}
hjältedikterna | {svn(HJ['förstånd'])} | {HJ['antal'].get('förstånd', 0)}
de kristna dikterna | {svn(KR['förstånd'])} | {KR['antal'].get('förstånd', 0)}
# strid (víg, vápn, sverð, orrosta, hildr)
Hávamál | {svn(H['strid'])} | {H['antal'].get('strid', 0)}
gudadikterna | {svn(GU['strid'])} | {GU['antal'].get('strid', 0)}
+hjältedikterna | {svn(HJ['strid'])} | {HJ['antal'].get('strid', 0)}
de kristna dikterna | {svn(KR['strid'])} | {KR['antal'].get('strid', 0)}
# hämnd (hefna, hefnd, bróðurbani)
Hávamál | {svn(H['hämnd'])} | {H['antal'].get('hämnd', 0)}
gudadikterna | {svn(GU['hämnd'])} | {GU['antal'].get('hämnd', 0)}
+hjältedikterna | {svn(HJ['hämnd'])} | {HJ['antal'].get('hämnd', 0)}
de kristna dikterna | {svn(KR['hämnd'])} | {KR['antal'].get('hämnd', 0)}
Källa: de normaliserade texterna från vår Hávamálartikel; Snorres prosa inte medräknad. Ordlistorna står i kodförrådet (utdata/dygder/dygder_edda.py).
:::"""


title = "Mild i ord och god på mat"
summary = ("Vad ville vikingatidens människor bli ihågkomna för? Vi läste alla vikingatida runstenar och hela Hávamál "
           "och räknade vad som prisas. Krigaren finns där, men han är en bifigur. Det som räknas är hur man är mot "
           "andra.")

body = f"""Den som vill veta vad en tid höll för gott har två slags källor att gå till. Det ena är vad människorna skrev om sina egna döda, det andra är vad de lärde sina barn. Från vikingatiden finns båda: {tus(N)} runstenar med ett par ord om den som gått bort, och Hávamál, en dikt med etthundrasextiofyra strofer råd till den som ska leva. Vi läste allt och räknade.

Frågan var enkel. Om man lägger ihop allt beröm, alla råd och alla varningar – vad för slags människa träder fram? Vi väntade oss krigaren, för det är den bild som vikingatiden för med sig. Han finns där. Men han står långt bak i rummet.

## Vad stenarna säger

De flesta runstenar prisar ingen. Av {tus(N)} vikingatida runstenar säger bara {N_EG}, en av nio, något om hur den döde var. Resten anger vem som reste stenen och åt vem: *son sin*, *fôður sinn*, *bróður sinn*. Släktskapet är stenens egentliga budskap, och att någon brydde sig om att hugga det i sten.

Men när stenarna säger något, säger de ganska samstämmigt vad. Det vanligaste ordet är *góðr*, god – {EG['god']} stenar. Sedan kommer två ord för vad en man ska vara: *drengr*, {EG['drengr']} stenar, och *þegn*, {EG['þegn']}. Forskningen har tvistat i hundra år om vad orden betyder på stenarna, om det är en rang i kungens följe eller ett ideal; vi återkommer till det. Mod, uttryckligen – *djarfr*, *frœkn*, *þróttar þegn*, ”flydde inte” – står på {EG['modig']} stenar.

{CHART}

Det som förvånade oss är de små kategorierna, för de är så bestämda. Sju stenar prisar någon för att ha varit *mildr matar*, ”god på mat”, generös med maten. Sex prisar någon för orden: *mildan orða*, mild i tal; *málsrisinn*, ”rask i tal”, vältalig; *málspakr*, vis i tal. Tre för en färdighet: en man som *kunni vel knerri stýra*, kunde styra ett skepp väl, en som var *slœgjastr manna*, den skickligaste av män, och en flicka i Hadeland som var *mær hônnurst*, den händigaste. Sjutton för hedern, ofta i negation: *óníðingr*, ingen niding, *óneiss*, utan skam.

Och gärningarna pekar åt samma håll. {GA['bro_och_vag']} stenar berättar att någon byggde en bro eller röjde en väg – mer än dubbelt så många som berättar att någon stupade eller dräptes ({GA['strid']}). Resor österut och västerut nämns på {RESOR} stenar. Bönen för själen, *Guð hjalpi ônd hans*, står på {GA['kristen_bon']}.

## Ett porträtt i sex drag

Så här ser han ut, den människa som stenarna och dikten håller för god. Vi låter en sten och en strof stå bredvid varandra i varje drag.

**Generös.** På Hagstugan i Södermanland (Sö 130) reste fyra söner en sten åt sin far, *mildan orða ok matar góðan* – mild i ord och god på mat. I Sövestad i Skåne (DR 291) var Bram *beztr búmanna ok mildastr matar*, den bäste av bönder och den generösaste med mat. Hávamál säger samma sak i strof 39, med nästan samma ord:

> *Fannk-a ek mildan mann eða svá matar góðan, at væri-t þiggja þegit.*

Jag fann aldrig en så givmild man, eller så god på mat, att det inte var välkommet att ta emot. Den parallellen är gammal; David Evans noterade den i sin utgåva 1986, efter Sven B. F. Jansson. Det vi lägger till är att formeln inte är ett undantag: sju stenar har den, från Småland till Uppland och Skåne, och Hávamáls ekonomi – *gjalda gjöf við gjöf*, gälda gåva med gåva – är dess förklaring. Att bjuda var att binda människor till sig. *Með halfum hleif ok með höllu keri fekk ek mér félaga* (52): med ett halvt bröd och en lutad bägare fick jag mig en följeslagare.

{PH_130}

**Mild i ord.** Kari i Gillberga (U 1146) hette *hinn málspaki*, den talvise. Holmbjörn i Gådi (U 739) reste själv sin sten och lät skriva att han var *mildr matar ok málsrisinn*, generös med mat och rask i tal. Sveinn i Ivla (Sm 44) var mild mot de sina och god på mat, *í orðlofi allra miklu* – mycket prisad av alla. Hávamál ägnar var femte rådstrof åt ordet: att tala lagom, att tiga, att lyssna. Gästen behöver *orðs ok endrþögu* (4), ett ord och tystnad i gengäld.

**Den som sköter sitt.** Þorsteinn i Turinge (Sö 338) var en av *beztra manna, á landi ok í liði úti*, de bästa män i land och i följe ute, och bröderna *heldu sína húskarla vel*: de höll sina huskarlar väl. Det är den enda sten som berömmer någon för hur han höll sitt husfolk, och den gör det på samma sten som berättar att han stupade i Gårdarike. Odindisa i Hassmyra (Vs 24) får stenens enda husfruberöm: *kemr hýfreyja til Hôsumýra eigi betri, en býi ráðr* – det kommer ingen bättre husfru till Hassmyra, som råder över gården. Hávamál: *bú er betra, þótt lítit sé* (36), eget hem är bättre, om än litet.

**Utan skam.** Özurr i Århus (DR 68) *dó manna mest óníðingr*, dog som den minst nidingaktiga av män. Toke Gormsson i Hällestad (DR 295) *fló eigi at Uppsôlum*, flydde inte vid Uppsala. Det är här modet står, och det är värt att se hur det står: inte som anfall utan som att inte svika. Hávamál 16 säger varför den fege ändå inte vinner något: *ósnjallr maðr hyggsk munu ey lifa, ef hann við víg varask; en elli gefr hánum engi frið* – den fege tror att han ska leva för evigt om han undviker strid, men ålderdomen ger honom ingen frid. Och i strof 48 står mod och generositet i samma rad: *mildir, fræknir menn bazt lifa*, frikostiga, tappra män lever bäst.

**Skicklig.** Gunnleifr (U 654) dräptes i österled med Ingvar, men det ristaren ville ha sagt om honom var att han *kunni vel knerri stýra*, kunde styra en knarr väl. Astrid i Dynna (N 68) var *mær hônnurst á Haðalandi*, den händigaste mön i Hadeland; hennes mor byggde en bro åt henne. Hávamál saknar ordet för hantverk men inte tanken: var inte skomakare eller skaftmakare åt andra, säger strof 126, om du inte kan det – ett dåligt skaft blir din olycka.

**Ihågkommen.** Þóra i Saleby (Vg 67) var *bezt með ôldum*, den bästa i sin generation. Etill i Fågelö (Sö 64) *var manna beztr*. Joarr vid Korpbron (Sö 140): *engi fœðir son snjallara*, ingen föder en duktigare son. Det är stenens hela ärende – att låta ett omdöme stå kvar – och Hávamál säger i sin mest kända strof (76) vad som står på spel:

> *Deyr fé, deyja frændr, deyr sjalfr it sama, en orðstírr deyr aldregi, hveim er sér góðan getr.*

Fä dör, fränder dör, själv dör man likaså; men ryktet dör aldrig för den som vinner sig ett gott. Áskell på Lolland (DR 212) formulerade det i sten: *æ mun standa, með steinn lifir*, alltid skall det stå, så länge stenen lever. Och strof 72 vet vem som reser stenarna: *sjaldan bautarsteinar standa brautu nær, nema reisi niðr at nið* – sällan står bautastenar vid vägen, om inte ättling reser dem åt ättling.

## Vad dikten lär ut

{CR}

Vi läste alla strofer och antecknade vad var och en handlar om. I de {len(RAD)} rådstroferna – gästvisdomen och Loddfáfnismál – är vänskapen det största ämnet, var femte strof. Sedan ordet, förståndet, gästfriheten och måttan. Mod och strid: {tc['MOD']} strofer av {len(RAD)}.

{CHART_HAV}

Det finns också något i dikten som inte har något ord på stenarna: omsorgen om den svage. *Get þú váluðum vel* (135), behandla den fattige väl. *At hárum þul hlæ þú aldregi* (134), skratta aldrig åt en gråhårig talare. Och strof 133: *er-at maðr svá góðr at galli né fylgi, né svá illr, at einugi dugi* – ingen är så god att han saknar fel, eller så dålig att han inte duger till något.

## Var krigaren står

Krigaren finns, men han bor i ett annat hus. Vi räknade värdeorden i fyra grupper av eddadikter. Ord för vänskap står {svn(H['vänskap'])} gånger per tusen ord i Hávamál och mindre än en gång i hjältedikterna; ord för strid {svn(HJ['strid'])} gånger per tusen i hjältedikterna. Hämnd – *hefna*, *bróðurbani* – finns i hjältedikterna och gudadikterna och till och med i de kristna. I Hávamál står ordet inte en enda gång.

{CHART_EDDA}

På stenarna är det *drengr* som drar åt striden. Drengr-stenarna nämner strid eller färder utomlands fyra gånger så ofta som stenar i allmänhet: {T['drengr']['k']} av {T['drengr']['n']} mot {T['alla']['k']} av {tus(T['alla']['n'])}, en skillnad slumpen skulle ge färre än en gång på tiotusen. *Þegn* har inget sådant samband. Men också bland drengerna nämner fem av sex varken strid eller resa. Ordet ligger mellan ”krigare” och ”en man man kan lita på”, och stenarna lutar åt det senare.

## Var det så här de var?

Det vet vi inte. En runsten är ett eftermäle, och eftermälen är artiga; Hávamál är ett ideal, och ideal beskriver vad folk brister i. Det som går att säga är vad de valde att hugga i sten, och vad de valde att lära ut. Där står inte erövring och inte hämnd. Där står: var generös, tala väl, sköt ditt, svik inte, kunna något – och se till att någon minns det.

Det är en lista som inte har åldrats, och det är kanske det mest oväntade. Byt stenen mot vad som helst som ska överleva en människa, så står kraven kvar.

:::box Det viktigaste i korthet
- När en vikingatida runsten säger något om den döde är det nästan alltid ett ord för godhet, pålitlighet eller generositet. Uttryckligt mod står på {EG['modig']} stenar av {tus(N)}.
- Runstenarna och Hávamál pekar åt samma håll: generositet med mat, mildhet i ord, omsorg om de sina och ett gott eftermäle. Formeln *mildr … matar góðr* står på sju stenar och i strof 39.
- Krig och hämnd hör hemma i hjältedikterna. Hávamál saknar hämndordet helt, och nio runstenar av tio med en egenskap nämner varken strid eller resa.
- *Drengr* lutar åt striden, *þegn* gör det inte. Men ordens tyngdpunkt på stenarna är pålitligheten, inte vapnen.
:::

:::box Så räknade vi
- **Runstenarna:** alla {tus(N)} inskrifter i Samnordisk runtextdatabas 3.1 som är daterade till vikingatiden och är runstenar eller fragment av runstenar, i hela Norden. Vi sökte i den fornvästnordiska normaliseringen efter ord för egenskaper och gärningar, med ordlistor satta före räkningen; varje träff granskades i sitt sammanhang, och ristarformeln *ráði sá kunni*, ”tyde den som kan”, räknas inte som beröm för råd. En sten räknas en gång per kategori.
- **Hávamál:** vi läste alla 164 strofer och satte ett eller flera ämnen på var och en. Listan ligger öppen. Andelarna gäller de {len(RAD)} rådstroferna, del I och Loddfáfnismál.
- **Eddan:** värdeord per tusen ord i Hávamál, de övriga gudadikterna, hjältedikterna och de kristna dikterna Hugsvinnsmál och Sólarljóð, i de normaliserade texterna från vår Hávamálartikel.
- **Gränser:** ordlistor fångar ord, inte betydelse; vår strofläsning är en läsning; och ett eftermäle är inte ett vittnesmål. Parallellen mellan strof 39 och stenarna är känd sedan Evans 1986; antalen är våra.
:::

## Källor

- Samnordisk runtextdatabas 3.1 (Rundata). Uppsala universitet.
- Evans, David A. H. (utg.) 1986. *Hávamál*. Viking Society for Northern Research, London. Kommentaren till strof 39, s. 91.
- Jansson, Sven B. F. 1985. *Runinskrifter i Sverige*. 3 uppl. Värnamo. (Den utgåva Evans hänvisar till.)
- Goetting, Lauren 2006. ”Þegn and drengr in the Viking Age”. *Scandinavian Studies* 78 (4).
- Sukhino-Khomenko, Denis 2024. *Thegns Around the North Sea*. Göteborgs universitet.
- Vitkis artikel [Vad den Höge säger tusen år senare](/artiklar/vem-talar-i-havamal/), med texterna och metoden."""


def en_chart(sv: str) -> str:
    """The same chart with English labels (the numbers are the same strings)."""
    for a, b in EN_LABELS:
        sv = sv.replace(a, b)
    return sv


EN_LABELS = [
    (f"Vad runstenarna säger om den döde, antal stenar av {tus(N)} vikingatida runstenar", f"What the runestones say about the dead, number of stones out of {tus(N)} Viking-age runestones"),
    ("# Egenskaper", "# Qualities"), ("# Gärningar", "# Deeds"), ("god (góðr)", "good (góðr)"), ("stenar\n", "stones\n"),
    ("drengr, pålitlig man", "drengr, reliable man"), ("þegn, fri man av stånd", "þegn, free man of standing"),
    ("den bäste, den främste", "the best, the foremost"), ("utan skam, duglig", "without shame, capable"),
    ("duktig (snjallr)", "able (snjallr)"), ("givmild, god på mat", "generous, free with food"),
    ("mild i ord, vältalig, vis", "gentle in speech, eloquent, wise"), ("modig, flydde inte", "brave, did not flee"),
    ("kristen bön för själen", "Christian prayer for the soul"), ("byggde bro eller väg", "built a bridge or road"),
    ("gård, arv, ägande", "farm, inheritance, ownership"), ("resa österut eller västerut", "journey east or west"),
    ("stupade eller dräptes", "fell or was killed"), ("handel, skepp, styrman", "trade, ship, captain"),
    ("Källa: Samnordisk runtextdatabas 3.1, vikingatida runstenar och fragment i hela Norden, räknade i den fornvästnordiska normaliseringen. Vitkis beräkning; en sten räknas en gång per kategori.",
     "Source: Scandinavian Runic-text Database 3.1, Viking-age runestones and fragments across the Nordic countries, counted in the Old West Norse normalisation. Vitki's computation; a stone counts once per category."),
    (f"Vad Hávamáls råd handlar om, andel av de {len(RAD)} rådstroferna (del I och Loddfáfnismál)", f"What Hávamál's advice is about, share of the {len(RAD)} advice stanzas (part I and Loddfáfnismál)"),
    ("vänskap |", "friendship |"), ("ord och tystnad", "speech and silence"), ("förstånd |", "understanding |"),
    ("gästfrihet |", "hospitality |"), ("måtta |", "moderation |"), ("försiktighet", "caution"), ("livets värde", "the value of life"),
    ("eget hem och flit", "one's own home and diligence"), ("rykte och eftermäle", "reputation and memory"), ("gåvor |", "gifts |"),
    ("mod och strid", "courage and fighting"), ("omsorg om andra", "care for others"), ("strofer\n", "stanzas\n"),
    ("Källa: vår läsning av Codex Regius-texten (Guðni Jónssons normalisering), en eller flera teman per strof; listan ligger öppen i kodförrådet (utdata/dygder/havamal_teman.csv).",
     "Source: our reading of the Codex Regius text (Guðni Jónsson's normalisation), one or more themes per stanza; the list is open in the code repository (utdata/dygder/havamal_teman.csv)."),
    ("Värdeord per tusen ord i fyra grupper av eddadikter", "Value words per thousand words in four groups of Eddic poems"),
    ("# vänskap (vinr, tryggð, félagi)", "# friendship (vinr, tryggð, félagi)"), ("# förstånd (mannvit, horskr, fróðr, snotr …)", "# understanding (mannvit, horskr, fróðr, snotr …)"),
    ("# strid (víg, vápn, sverð, orrosta, hildr)", "# fighting (víg, vápn, sverð, orrosta, hildr)"), ("# hämnd (hefna, hefnd, bróðurbani)", "# revenge (hefna, hefnd, bróðurbani)"),
    ("gudadikterna", "the mythological poems"), ("hjältedikterna", "the heroic poems"), ("de kristna dikterna", "the Christian poems"),
    (" ord av ", " words of "),
    ("Källa: de normaliserade texterna från vår Hávamálartikel; Snorres prosa inte medräknad. Ordlistorna står i kodförrådet (utdata/dygder/dygder_edda.py).",
     "Source: the normalised texts from our Hávamál article; Snorri's prose not included. The word lists are in the code repository (utdata/dygder/dygder_edda.py)."),
]
for ch in (CHART, CHART_HAV, CHART_EDDA):
    assert not re.search(r"[åäö]", en_chart(ch).split("Source")[0].replace("Hávamál", "").replace("þegn", "").replace("snjallr", "").replace("góðr", "").replace("tryggð", "").replace("fróðr", "").replace("bróðurbani", "").replace("Loddfáfnismál", "").replace("Jónsson", "")), en_chart(ch)

title_en = "Gentle in speech and free with food"
summary_en = ("What did the people of the Viking Age want to be remembered for? We read every Viking-age runestone and "
              "the whole of Hávamál and counted what is praised. The warrior is there, but as a minor figure. What "
              "counts is how you treat other people.")

body_en = f"""Anyone who wants to know what an age held to be good has two kinds of source. One is what people wrote about their own dead; the other is what they taught their children. From the Viking Age we have both: {tus(N)} runestones with a word or two about the person who has gone, and Hávamál, a poem of one hundred and sixty-four stanzas of advice to those who have still to live. We read all of it and counted.

The question was simple. If you add up all the praise, all the advice and all the warnings, what kind of person emerges? We expected the warrior, because that is the figure the Viking Age brings with it. He is there. But he stands at the back of the room.

## What the stones say

Most runestones praise nobody. Of {tus(N)} Viking-age runestones, only {N_EG}, one in nine, say anything about what the dead person was like. The rest state who raised the stone and for whom: *son sinn*, *fôður sinn*, *bróður sinn*. Kinship is the stone's real message, and the fact that someone cared enough to cut it in stone.

But when the stones do say something, they are fairly unanimous about what. The commonest word is *góðr*, good – {EG['god']} stones. Then come two words for what a man should be: *drengr*, {EG['drengr']} stones, and *þegn*, {EG['þegn']}. Scholars have argued for a century about what the words mean on the stones, whether a rank in the king's retinue or an ideal; we return to that below. Courage, stated outright – *djarfr*, *frœkn*, *þróttar þegn*, "did not flee" – stands on {EG['modig']} stones.

{en_chart(CHART)}

What surprised us were the small categories, because they are so definite. Seven stones praise someone for having been *mildr matar*, "free with food", generous with what was on the table. Six praise someone for their words: *mildan orða*, gentle in speech; *málsrisinn*, "quick of speech", eloquent; *málspakr*, wise in speech. Three for a skill: a man who *kunni vel knerri stýra*, could steer a ship well; one who was *slœgjastr manna*, the most skilful of men; and a girl in Hadeland who was *mær hônnurst*, the handiest maiden. Seventeen for honour, often in the negative: *óníðingr*, no villain; *óneiss*, without shame.

And the deeds point the same way. {GA['bro_och_vag']} stones tell that someone built a bridge or cleared a road – more than twice as many as tell that someone fell or was killed ({GA['strid']}). Journeys east and west are mentioned on {RESOR} stones. The prayer for the soul, *Guð hjalpi ônd hans*, stands on {GA['kristen_bon']}.

## A portrait in six traits

This is what the person the stones and the poem hold to be good looks like. We let a stone and a stanza stand side by side in each trait.

**Generous.** At Hagstugan in Södermanland (Sö 130) four sons raised a stone for their father, *mildan orða ok matar góðan* – gentle in speech and free with food. At Sövestad in Skåne (DR 291) Bramr was *beztr búmanna ok mildastr matar*, the best of farmers and the most generous with food. Hávamál says the same thing in stanza 39, in almost the same words:

> *Fannk-a ek mildan mann eða svá matar góðan, at væri-t þiggja þegit.*

I never found a man so generous, or so free with food, that a gift was not welcome. That parallel is old; David Evans noted it in his edition of 1986, after Sven B. F. Jansson. What we add is that the formula is not an exception: seven stones carry it, from Småland to Uppland and Skåne, and Hávamál's economy – *gjalda gjöf við gjöf*, repay gift with gift – is its explanation. To give was to bind people to you. *Með halfum hleif ok með höllu keri fekk ek mér félaga* (52): with half a loaf and a tilted cup I got myself a companion.

{PH_130_EN}

**Gentle in speech.** Kári of Gillberga (U 1146) was called *hinn málspaki*, the wise in speech. Holmbjôrn of Gådi (U 739) raised his own stone and had it say that he was *mildr matar ok málsrisinn*, generous with food and quick of speech. Sveinn of Ivla (Sm 44) was gentle to his own and free with food, *í orðlofi allra miklu* – greatly praised by all. Hávamál gives one advice stanza in five to the word: speaking in measure, keeping silent, listening. The guest needs *orðs ok endrþögu* (4), a word, and silence in return.

**Minding one's own.** Þorsteinn of Turinge (Sö 338) was one of the *beztra manna, á landi ok í liði úti*, the best of men at home and in the host abroad, and the brothers *heldu sína húskarla vel*: they kept their household men well. It is the only stone that praises someone for how he kept his household, and it does so on the same stone that tells how he fell in Garðaríki. Óðindísa of Hassmyra (Vs 24) gets the stones' one word of praise for a housewife: *kemr hýfreyja til Hôsumýra eigi betri, en býi ráðr* – no better housewife will come to Hassmyra, who rules the farm. Hávamál: *bú er betra, þótt lítit sé* (36), a home of one's own is better, though it be small.

**Without shame.** Ôzurr of Århus (DR 68) *dó manna mest óníðingr*, died the least villainous of men. Tóki Gormsson of Hällestad (DR 295) *fló eigi at Uppsôlum*, did not flee at Uppsala. This is where courage stands, and it is worth seeing how it stands: not as attack but as not failing others. Hávamál 16 says why the coward gains nothing anyway: *ósnjallr maðr hyggsk munu ey lifa, ef hann við víg varask; en elli gefr hánum engi frið* – the coward thinks he will live for ever if he shuns the fight, but old age gives him no peace. And in stanza 48 courage and generosity share a line: *mildir, fræknir menn bazt lifa*, generous, brave men live best.

**Skilled.** Gunnleifr (U 654) was killed in the east with Ingvarr, but what the carver wanted said of him was that he *kunni vel knerri stýra*, could steer a cargo ship well. Ástríðr of Dynna (N 68) was *mær hônnurst á Haðalandi*, the handiest maiden in Hadeland; her mother built a bridge for her. Hávamál has no word for craft but has the thought: be no shoemaker or shaft-maker for others, says stanza 126, unless you can do it – a bad shaft will be your undoing.

**Remembered.** Þóra of Saleby (Vg 67) was *bezt með ôldum*, the best of her generation. Etill of Fågelö (Sö 64) *var manna beztr*. Jóarr at Korpbron (Sö 140): *engi fœðir son snjallara*, no one bears an abler son. That is the stone's whole errand – to let a judgement stand – and Hávamál says in its best-known stanza (76) what is at stake:

> *Deyr fé, deyja frændr, deyr sjalfr it sama, en orðstírr deyr aldregi, hveim er sér góðan getr.*

Cattle die, kinsmen die, you yourself die likewise; but a good name never dies for the one who earns it. Áskell on Lolland (DR 212) put it in stone: *æ mun standa, með steinn lifir*, ever will it stand, while the stone lives. And stanza 72 knows who raises the stones: *sjaldan bautarsteinar standa brautu nær, nema reisi niðr at nið* – seldom do memorial stones stand by the road unless kin raise them for kin.

## What the poem teaches

{CR_EN}

We read every stanza and noted what each is about. In the {len(RAD)} advice stanzas – the guest wisdom and Loddfáfnismál – friendship is the largest subject, one stanza in five. Then speech, understanding, hospitality and moderation. Courage and fighting: {tc['MOD']} stanzas out of {len(RAD)}.

{en_chart(CHART_HAV)}

There is also something in the poem that has no word on the stones: care for the weak. *Get þú váluðum vel* (135), treat the poor well. *At hárum þul hlæ þú aldregi* (134), never laugh at a grey-haired speaker. And stanza 133: *er-at maðr svá góðr at galli né fylgi, né svá illr, at einugi dugi* – no one is so good that no fault goes with him, nor so bad that he is good for nothing.

## Where the warrior stands

The warrior exists, but he lives in another house. We counted value words in four groups of Eddic poems. Words for friendship stand {svn(H['vänskap']).replace(',', '.')} times per thousand words in Hávamál and less than once in the heroic poems; words for fighting {svn(HJ['strid']).replace(',', '.')} times per thousand in the heroic poems. Revenge – *hefna*, *bróðurbani* – occurs in the heroic poems and the mythological ones and even in the Christian ones. In Hávamál the word does not occur once.

{en_chart(CHART_EDDA)}

On the stones it is *drengr* that leans towards fighting. The drengr stones mention battle or journeys abroad four times as often as stones in general: {T['drengr']['k']} of {T['drengr']['n']} against {T['alla']['k']} of {tus(T['alla']['n'])}, a difference chance would produce less than once in ten thousand. *Þegn* has no such link. But even among the drengs, five in six mention neither battle nor journey. The word lies between "warrior" and "a man you can rely on", and the stones lean towards the latter.

## Is this what they were like?

We do not know. A runestone is an epitaph, and epitaphs are polite; Hávamál is an ideal, and ideals describe what people fall short of. What can be said is what they chose to cut in stone, and what they chose to teach. Conquest is not there, and neither is revenge. What is there is: be generous, speak well, mind your own, do not fail others, be able at something – and make sure someone remembers it.

It is a list that has not aged, and that is perhaps the most unexpected thing. Replace the stone with anything meant to outlive a person, and the demands stay the same.

:::box The essentials in brief
- When a Viking-age runestone says anything about the dead, it is nearly always a word for goodness, reliability or generosity. Explicit courage stands on {EG['modig']} stones out of {tus(N)}.
- The runestones and Hávamál point the same way: generosity with food, gentleness in speech, care for one's own and a good name after death. The formula *mildr … matar góðr* stands on seven stones and in stanza 39.
- War and revenge belong to the heroic poems. Hávamál lacks the word for revenge entirely, and nine runestones in ten that name a quality mention neither battle nor travel.
- *Drengr* leans towards fighting; *þegn* does not. But the weight of the words on the stones is reliability, not weapons.
:::

:::box How we counted
- **The runestones:** all {tus(N)} inscriptions in the Scandinavian Runic-text Database 3.1 dated to the Viking Age that are runestones or fragments of runestones, across the Nordic countries. We searched the Old West Norse normalisation for words for qualities and deeds, with word lists fixed before counting; every hit was checked in context, and the carvers' formula *ráði sá kunni*, "interpret, he who can", is not counted as praise for counsel. A stone counts once per category.
- **Hávamál:** we read all 164 stanzas and assigned one or more subjects to each. The list is open. The shares concern the {len(RAD)} advice stanzas, part I and Loddfáfnismál.
- **The Edda:** value words per thousand words in Hávamál, the other mythological poems, the heroic poems and the Christian poems Hugsvinnsmál and Sólarljóð, in the normalised texts from our Hávamál article.
- **Limits:** word lists catch words, not meaning; our reading of the stanzas is a reading; and an epitaph is not testimony. The parallel between stanza 39 and the stones has been known since Evans 1986; the counts are ours.
:::

## Sources

- Scandinavian Runic-text Database 3.1 (Rundata). Uppsala University.
- Evans, David A. H. (ed.) 1986. *Hávamál*. Viking Society for Northern Research, London. Commentary on stanza 39, p. 91.
- Jansson, Sven B. F. 1985. *Runinskrifter i Sverige*. 3rd ed. Värnamo. (The edition Evans refers to.)
- Goetting, Lauren 2006. "Þegn and drengr in the Viking Age". *Scandinavian Studies* 78 (4).
- Sukhino-Khomenko, Denis 2024. *Thegns Around the North Sea*. University of Gothenburg.
- Vitki's article [What the High One says a thousand years later](/en/artiklar/vem-talar-i-havamal/), with the texts and the method."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M)  # BlogBody has no tables
    assert b.count(":::box") == 2 and b.count(":::chart") == 3 and b.count("![") == 2
out = {"slug": "mild-i-ord-och-god-pa-mat", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Eddan", "Formler och syfte", "Tolkning"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "dygder.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "dygder.json"), len(body.split()), "ord,", len(body_en.split()), "words")

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
                 "topic": "Forskning|dygder", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
