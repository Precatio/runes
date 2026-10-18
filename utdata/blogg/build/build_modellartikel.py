"""Artikeln om arbetet med sannolikhetsmodellen för runtext (sv + en), skriven som ett pågående arbete: modellen är
inte släppt i appen. Omskriven 2026-10-17 på Viktors begäran, så att allt arbete med modellen kommer med och forskningen
kan se hur den är prövad: sex prov, kalibreringen mot dokumenterade luckor, kontrollerna av koden och körningen över alla
runstenar. Det korta utkastet "Ett arbete som pågår" (kZlNLqkwSexyDFWAX1es) är inarbetat här.
Siffrorna kommer ur build_modellartikel_data.py (proven och körningen), panelens cache för Sö 45, Sö 137, Sö 206 och
Sö 211, Södermanlands runinskrifter för skadorna, och Laila Kitzler Åhfeldts skanningar för bilderna
(utdata/modellartikel/render.py och figurer.py). Den tidigare versionen: build_modellartikel_tm14.py.
    ../../../.venv/bin/python build_modellartikel.py [--write | --update DOC]
Skriver utdata/blogg/modellartikel.json; --write sparar ett nytt opublicerat utkast i Firestore."""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_modellartikel_data import D, pr  # noqa: E402
from scripts.runlm_gap_calibrate import top_words  # noqa: E402
from src import blog_figures  # noqa: E402
from src import runlm as rl  # noqa: E402
from src import textmodel as tm  # noqa: E402

M = os.path.join(ROOT, "utdata", "modellartikel")
recs = rl.load_rundata()
TOP, NAMES = top_words(recs), tm.name_keys(recs)
BL, SCN = D["blind"], D["scantraces"]
R, MK, HD, RG, DOC, DT, BT, CK = (D["reading"], D["masking"], D["hard"], D["restored"], D["documented"], D["dating"],
                                  D["batch"], D["checks"])
RK = R["by_kind"]
VAL = D["validation"]
CAL = D["calibration"]
DB0, DB1 = DOC["before"], DOC["after"]
ECE = lambda bins: sum(abs(b["said"] - b["right"]) * b["n"] for b in bins) / sum(b["n"] for b in bins)  # noqa: E731
ECE0, ECE1 = ECE(DB0), ECE(DB1)
assert ECE0 > 0.1 and ECE1 < 0.04
PCT_CLS = {int(k): 100 * v["right"] for k, v in RG["by_class"].items()}  # 0 formula words, 1 other words, 2 names
ALL = BT["bands"]
N_GAPS, N_STONES, N_FEW = BT["gaps"], BT["inscriptions"], BT["too_few"]
N_WITH = N_STONES + N_FEW
REST_N, REST_SURE = sum(BT["status"]["återställt"].values()), BT["status"]["återställt"].get("≥95", 0)
OPEN_N, OPEN_SURE = sum(BT["status"]["ej återställt"].values()), BT["status"]["ej återställt"].get("≥95", 0)
HOURS = BT["hours_longest_part"]
assert 0.1 < ALL["≥95"] / N_GAPS < 0.3 and OPEN_SURE / OPEN_N < 0.1


def share(k):
    return 100 * ALL.get(k, 0) / N_GAPS


def cached(sig):
    return json.load(open(os.path.join(tm.CACHE, tm._safe(sig) + ".json"), encoding="utf-8"))


def top(sig, n, k=3):
    return [(w["word"], 100 * w["p"]) for w in cached(sig)["gaps"][n]["words"][:k]]


S45 = top("Sö 45", 0, 2)
S137 = top("Sö 137", 0, 1)[0]
S211 = top("Sö 211", 1, 1)[0]
S211_NAME = top("Sö 211", 0, 1)[0]
S206A, S206B = top("Sö 206", 0, 2), top("Sö 206", 1, 3)
assert [w for w, _ in S45] == ["gæiRfastr", "gæiRfriðr"] and S137[0] == "þannsi" and S211[0] == "stæin"
assert [w for w, _ in S206A] == ["hrungnir", "roðnir"]  # the giant first: within a word class the calibration never reverses the model's order
RAW206 = {w["word"]: w["p_model"] for w in cached("Sö 206")["gaps"][0]["words"]}
assert RAW206["hrungnir"] > RAW206["roðnir"] and S206A[0][1] < 50
assert tm.fold_of("Sö 206") == tm.fold_of("Sö 208")
# Sö 206 with an imagined trace in ru?niR (only þ, or only k, allowed for the lost rune; soft traces), and with the
# model that leaves out only Sö 206 itself, so that it has seen the sister stone Sö 208
SP = os.path.join(M, "spar_so206.json")
SPAR = json.load(open(SP)) if os.path.exists(SP) else {}
if SPAR.get("version") != tm.VERSION:
    SPAR = {"version": tm.VERSION, **{tr: {w["word"]: w["p"] for w in tm.analyze("Sö 206", allowed={0: [tr]})["gaps"][0]["words"][:4]}
                                     for tr in ("þ", "k")}}
    LOO = tm.analyze("Sö 206", loo=True)
    SPAR["loo"] = {w["word"]: w["p"] for w in LOO["gaps"][1]["words"][:4]}
    json.dump(SPAR, open(SP, "w"), ensure_ascii=False, indent=1)
assert SPAR["þ"]["roðnir"] > SPAR["þ"].get("hrungnir", 0) and SPAR["k"]["hrungnir"] > SPAR["k"].get("roðnir", 0)
# a word as the text writes it: names with a capital (Guðlaug), other words not (karl, kross)
SHOW = {"gislaug": "Gíslaug", "karl": "karl"}  # karl here is the word 'man', as the edition reads the alternatives
NM = lambda w: SHOW.get(w) or (w.capitalize() if tm.gap_class(w, TOP, NAMES) == 2 else w)  # noqa: E731
OPEN_SV = (f"gör den det inte i någon av de {OPEN_N}" if OPEN_SURE == 0 else f"gör den det bara i {OPEN_SURE} av {OPEN_N}")
OPEN_EN = (f"it does so in none of the {OPEN_N}" if OPEN_SURE == 0 else f"it does so in only {OPEN_SURE} of {OPEN_N}")
assert max(w for _, w in S206B) < 40  # 'inget förslag mer än …': the model does not know


def svn(x, d=0):
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def enn(x, d=0):
    return f"{x:,.{d}f}"


def hours(x, lang):
    """The run's duration (its longest part, in hours) in words: minutes to the nearest five under an hour."""
    if x < 1:
        m = max(5, int(round(60 * x / 5)) * 5)
        return f"ungefär {m} minuter" if lang == "sv" else f"about {m} minutes"
    h = round(x)
    return (f"ungefär {h} timme" if h == 1 else f"ungefär {h} timmar") if lang == "sv" else (f"about {h} hour" if h == 1 else f"about {h} hours")


FIG = {name: {lang: blog_figures.freeze(open(os.path.join(M, f"fig_{name}_{lang}.png"), "rb").read()) for lang in ("sv", "en")}
       for name in ("so45", "runljud", "flode", "so206", "spar")}
KA = "https://doi.org/10.5281/zenodo.11951255"
CC_BY = "https://creativecommons.org/licenses/by/4.0"
SRI_URL = "https://www.raa.se/kulturarv/runor-och-runstenar/digitala-sveriges-runinskrifter/"
METHODS = "https://github.com/Precatio/runes/blob/main/METHODS.md"
GITHUB = "https://github.com/Precatio/runes"
SPRAK = "/artiklar/hur-spraklik-ar-en-runfoljd"
CREDIT_SV = f"Laila Kitzler Åhfeldts skanning (Riksantikvarieämbetet, [CC BY 4.0]({CC_BY}), doi:[10.5281/zenodo.11951255]({KA}))"
CREDIT_EN = f"Laila Kitzler Åhfeldt's scan (Swedish National Heritage Board, [CC BY 4.0]({CC_BY}), doi:[10.5281/zenodo.11951255]({KA}))"
BIN_SV = lambda b: "under 50 %" if b["lo"] == 0 else "minst 95 %" if b["lo"] == 0.95 else f"{round(100 * b['lo'])}–{round(100 * b['hi'])} %"  # noqa: E731
BIN_EN = lambda b: "under 50 %" if b["lo"] == 0 else "at least 95 %" if b["lo"] == 0.95 else f"{round(100 * b['lo'])}–{round(100 * b['hi'])} %"  # noqa: E731
SURE_DOC = DB1[3]
RS_SURE = RG["bins"][-1]
DNY = CAL["documented | runstenar | ny (KV)"]
RNY = CAL["restored | runstenar | ny (KV)"]
HNY = CAL["svår maskering | runstenar (ingick inte) | ny"]

title = "Runorna som fattas – ett pågående arbete med Vitkis sannolikhetsmodell"
summary = ("Många runstenar har ställen där runor har fallit bort. Vi bygger en modell som föreslår vad som stod där och "
           "säger hur säker den är. Här redovisar vi hur långt vi har kommit och hur modellen är prövad: sex prov med känt "
           "svar, kalibrerade procent och kontroller av koden. Modellen är ännu inte släppt i appen.")

body = f"""![Sö 45 i strykljus, med närbild av de skadade runorna]({FIG['so45']['sv']})
Sö 45 vid Stora Släbro i Södermanland, i strykljus ur en 3D-skanning. Till höger det vänstra runbandet i närbild. Inom den streckade ringen är två runor skadade i stenens första ord, mansnamnet GæiRf[as]tr: den ena av flinta, den andra av en djup grop. Bilden är beräknad i Vitki ur {CREDIT_SV}.

Nästan ingen runsten har klarat tusen år utan skador. Stenar har spruckit, flisor har lossnat och vittringen har ätit sig in i ristningen. Av de {svn(D['viking_runestones'])} vikingatida runstenarna i Samnordisk runtextdatabas har {svn(N_WITH)} minst ett ställe där en till fyra runor har gått förlorade.

När runologerna ger ut en sten fyller de ofta sådana luckor. De ifyllda runorna sätts inom hakparentes, som i GæiRf[as]tr. Hakparentesen säger att runorna inte syns på stenen. Den säger inte hur säker utgivaren var, eller vilka andra möjligheter som vägdes.

I Vitki bygger vi en modell som gör samma arbete på ett annat sätt. Den föreslår vad som stod i luckan, rangordnar förslagen och anger hur säker den är. Procenten är prövad mot luckor där svaret är känt, så att 90 procent ska betyda att förslaget stämmer ungefär nio gånger av tio. Här berättar vi hur långt vi har kommit, och vi redovisar varje prov, så att den som vill kan granska hur modellen är byggd och prövad innan den släpps.

:::box Pågående arbete
- Modellen finns i Vitkis öppna källkod men är **ännu inte släppt i appen**. Vi prövar och förbättrar den fortfarande.
- Siffrorna gäller den version vi har i dag ({D['version']}, oktober 2026) och kan ändras.
- Siffrorna gäller runstenar, också fragment och försvunna stenar. Modellen läser också inskrifter på andra stenar och lösa föremål som amuletter och runben, och där säger vi det.
- Förslagen är förslag, inte tolkningar. Modellen räknar med runor, ord och ordföljd, inte med vad en text betyder.
:::

## Ett pussel med för få bitar

Den yngre runraden har bara 16 runor, men språket hade många fler ljud. Samma runa fick därför stå för flera ljud: ᚴ kunde vara k, g eller ng, och ᛁ kunde vara i, e, æ eller j. Ristarna satte inte heller alltid skiljetecken mellan orden. En runföljd kan alltså läsas på flera sätt redan när alla runor finns kvar. När några saknas blir möjligheterna ännu fler.

![En runa – flera ljud]({FIG['runljud']['sv']})
Ett urval ur modellens stavningstabell, förenklat. Modellen har lärt sig hur ofta varje ljud skrevs med varje runa, i olika tider och trakter.

## Så resonerar modellen

Ta Sö 45 som exempel. Enligt *Södermanlands runinskrifter* är stenen sprucken i tre delar. Det första namnet börjar med runorna kai på den nedersta delen och fortsätter med Rfastr på den övre vänstra. Där är staven i a "otydlig genom flinta", och av s finns bara "övre staven och mellanstreckets utgångspunkt, det övriga av runan är förstört genom en djup grop". Utgivarna läser GæiRf[as]tr. Modellen får se runorna kaiRf??tr, där de två frågetecknen är de förlorade runorna.

![Så resonerar modellen]({FIG['flode']['sv']})
Modellens steg, med luckan på Sö 45 som exempel.

Först prövar modellen vilka ord som kan stavas med de bevarade runorna och två runor till. Sedan vägs varje förslag efter hur väl det passar där det står. Det är samma princip som när telefonen föreslår nästa ord: vissa ord brukar följa på vissa andra. Här står ordet först i texten, följt av ännu ett namn, Æistfari, och verbet *ræisþu*, 'reste'. Namnet GæiRfastr finns på flera andra stenar, till exempel Sö 227, Sm 111 och U 1144, så modellen känner det. Några spår av runorna har vi inte lagt in här.

Svaret blir GæiRfastr med {svn(S45[0][1])} procent och GæiRfriðr med {svn(S45[1][1])}. Det första förslaget är samma namn som utgivarna skrev in. Modellen har inte sett Sö 45:s egen text, för en sten läses alltid av en version av modellen som har tränats utan den.

## Byggstenarna

Modellen är inte en enda stor maskin utan flera delar, och varje del går att pröva för sig. Flera av dem är beprövade metoder från språkteknologin. Språket lär sig modellen ur alla slags vikingatida inskrifter, inte bara runstenarna, eftersom det är detsamma på en amulett som på en sten.

- **Stavningen.** Modellen har lärt sig hur ljud skrevs med runor ur 27 218 par av huggna ord och deras normaliserade form, från 2 877 inskrifter. Stavningen skattas för varje tid och trakt, så att en sten från 900-talet inte läses som en från 1000-talet.
- **Ordföljden.** Hur ofta ett ord följer på ett annat räknas med en metod från taligenkänningen, Kneser–Ney-utjämning (Kneser & Ney 1995). Den ger också sällsynta ordpar en rimlig chans.
- **Ordklasserna.** Ord som står i liknande sammanhang grupperas automatiskt. Genitiverna *hans*, *hennaR*, *sina* och *þæiRa* hamnar i samma klass, utan att någon har talat om för modellen vad en genitiv är. Det hjälper den med ovanliga ord. Klasserna räknas fram med scikit-learn.
- **Namnen.** Många namn finns bara på en enda sten. Modellen bygger därför okända namn av förled, efterled och ändelse, stavade som ristarna stavade dem. Förledet Ragn- är till exempel huggit som *rahn* 17 gånger i Rundata.
- **Grannstenarna.** Namn som står på stenar inom en mil väger lite tyngre, eftersom samma familjer ofta reste flera stenar i samma bygd.
- **Skiljetecknen.** Ristarna skilde sig åt. De flesta satte skiljetecken mellan nästan alla ord, några mellan inga alls. Modellen skattar därför för varje sten hur ofta just den ristaren markerade en ordgräns, och låter det avgöra hur gärna den själv sätter en gräns där ristaren inte satte något tecken.
- **Spåren.** Syns en rest av en runa i skanningen eller i utgåvans beskrivning kan den läggas in. Spåret räknas som troligt men inte säkert, så att en felläst rest inte stänger ute rätt svar.
- **Kalibreringen.** Modellens egna procent var för höga, särskilt för namn. De justeras därför med en logistisk modell, samma princip som hos Platt (1999), olika för formelord, kända namn, namn som modellen själv har satt ihop och andra ord. Alla förslag i en lucka kalibreras tillsammans, och även "inget av förslagen" får en sannolikhet; förstavalet får ett eget avdrag, eftersom det valdes just för att dess sannolikhet var högst. Kalibreringen är skattad på tre slags luckor med känt svar, som vi beskriver nedan.
- **Inget fusk.** Materialet är delat i fem delar efter signum. En sten läses alltid av en modell som har tränats på de fyra andra, så att utgivarnas ifyllning aldrig läcker in. När en enda sten ska analyseras kan modellen också tränas på allt utom just den stenen.

## Sex prov med känt svar

Ett förslag är bara värt något om man vet hur ofta det stämmer. Vi prövar därför modellen på sex sätt, alltid på stenar som den inte har tränats på. Varje prov svarar på en egen fråga:

- **Läsprovet:** läser modellen hela texter rätt, när den själv måste avgöra var orden börjar?
- **Maskeringsprovet:** kan den fylla runor som vi döljer i texter med känt svar?
- **Det svåra maskeringsprovet:** klarar den detsamma när svaret aldrig är ett formelord?
- **Utgivarnas luckor:** kommer den fram till samma ord som utgivarna där de har fyllt en lucka?
- **De dokumenterade luckorna:** träffar den rätt där runorna verkligen har fallit bort, men är kända från äldre avbildningar?
- **Dateringsprovet:** kan den säga när en text skrevs, bara ur språket?

:::chart Rätt ord i proven, runstenar
+Läsprovet | {100 * RK['runsten']['same']:.1f} | {svn(RK['runsten']['words'])} ord på {RK['runsten']['inscriptions']} runstenar
Maskering, inne i ord | {100 * MK['inne i ord']['right']:.1f} | {MK['inne i ord']['n']} luckor
Maskering, helt ord | {100 * MK['helt ord']['right']:.1f} | {MK['helt ord']['n']} luckor
Maskering, helt ord med halva runan synlig | {100 * VAL['with_traces']:.1f} | simulerade spår
Svår maskering, inne i ord | {100 * HD['inne i ord']['right']:.1f} | {HD['inne i ord']['n']} luckor utan formelord
Utgivarnas luckor | {100 * RG['right']:.1f} | {RG['known']} luckor
Dokumenterade luckor | {100 * DOC['right']:.1f} | {DOC['gaps']} luckor
Källa: Vitkis prov med {D['version']}, i fem delar. Proven mäter olika saker och är svåra på olika sätt, så staplarna ska inte jämföras som en tävling.
:::

**Läsprovet.** Modellen läser {R['inscriptions']} inskrifter där svaret är känt, sammanlagt {svn(R['words'])} ord, utan utgivarnas ordgränser. Den väljer samma ord som utgivarna i {svn(100 * R['same'], 1)} procent av fallen och delar orden rätt i {svn(100 * R['span'], 1)} procent. När den första versionen var klar i oktober låg siffrorna på {R['first_same']} och {R['first_span']} procent. Tre procentenheter kan låta lite, men det är ungefär {svn(R['gain_words'])} fler rätt lästa ord, och ungefär hälften av vinsten kom när modellen lärde sig bygga namn. De {R['inscriptions']} inskrifterna är {RK['runsten']['inscriptions']} runstenar, {RK['annan sten']['inscriptions']} andra stenar och {RK['lösa föremål']['inscriptions']} lösa föremål. På runstenarna väljer modellen samma ord som utgivarna i {svn(100 * RK['runsten']['same'], 1)} procent av fallen och delar orden rätt i {svn(100 * RK['runsten']['span'], 1)} procent. De lösa föremålen är svårast, med {svn(100 * RK['lösa föremål']['same'])} och {svn(100 * RK['lösa föremål']['span'])} procent.

:::chart Läsprovet, från första versionen till i dag
# Samma ord som utgivarna
Första versionen | {R['first_same']}
+I dag | {100 * R['same']:.1f}
# Rätt delade ord
Första versionen | {R['first_span']}
+I dag | {100 * R['span']:.1f}
Källa: Vitkis läsprov på {R['inscriptions']} inskrifter ({RK['runsten']['inscriptions']} runstenar, {RK['annan sten']['inscriptions']} andra stenar och {RK['lösa föremål']['inscriptions']} lösa föremål) med {svn(R['words'])} ord, i fem delar.
:::

**Maskeringsprovet.** Här döljer vi runor i texter där svaret är känt och låter modellen fylla i dem. Saknas några runor inne i ett ord på en runsten ger den rätt ord i {pr(MK['inne i ord']['right'])} procent av fallen. Saknas ett helt ord blir det {pr(MK['helt ord']['right'])} procent, för då finns inga runor kvar att gå på, bara orden runt omkring. I ett simulerat prov på runstenar, där hälften av varje förlorad runa syns, stiger andelen rätta hela ord till {pr(VAL['with_traces'])} procent, och den är fortfarande {pr(VAL['with_misread_traces'])} procent när vart femte spår är felläst. Det provet är simulerat med rena runformer och visar vad spåren är värda i bästa fall.

**Det svåra maskeringsprovet.** Formelorden, som *sten*, *reste* och *efter*, är lätta att gissa. I det här provet döljer vi därför bara ord som inte hör till de 50 vanligaste. Då ger modellen rätt ord i {pr(HD['inne i ord']['right'])} procent av fallen när några runor saknas inne i ordet, och i {pr(HD['helt ord']['right'])} procent när hela ordet saknas. Provet visar hur mycket formlerna hjälper, och hur svårt det är att gissa ett ovanligt ord utan spår. Det viktiga är att modellen vet om det, och det gör den nästan hela vägen: när den säger minst 95 procent har den rätt i {pr(HD['pooled']['sure_right_sw'])} av hundra också här, mätt med samma regel som i utgivarnas luckor – räknar man i stället varje normaliseringsvariant som fel, som hakun mot hakon, blir det {pr(HD['pooled']['sure_right'])} av hundra. En reservation har provet dock lärt oss: i bandet 80–95 procent är modellen något för säker på ovanliga ord. Den påstår där i snitt {pr(HD['pooled']['band_said'])} procent men har rätt i {pr(HD['pooled']['band_right_sw'])} av hundra. Den som fyller en lucka där svaret inte kan vara ett formelord bör läsa procent i det bandet med den marginalen.

**Utgivarnas luckor.** Vi prövar modellen på {RG['restored']} luckor på {RG['stones']} runstenar som utgivarna har fyllt. Modellen lämnar ett förslag i {RG['known']} av dem, och {svn(100 * RG['right'])} procent av förslagen är samma ord som utgivarna valde. Formelorden blir rätt i {svn(PCT_CLS[0])} procent, namnen i {svn(PCT_CLS[2])} och övriga ord i {svn(PCT_CLS[1])} procent. Det provet är ändå lättare än verkligheten. Utgivare fyller helst luckor där svaret är givet och lämnar de svåra öppna, så luckorna de har fyllt är ofta de enkla.

**De dokumenterade luckorna.** Ett bättre prov finns i Rundata självt. Runor inom hakparentes är förlorade på stenen men kända från äldre avbildningar. De har fallit bort av fysiska skäl, inte för att de var lätta att gissa, och svaret är ändå dokumenterat. Vi gör varje sådan följd av en till fyra runor inne i ett ord till en lucka. På {DOC['gaps']} sådana luckor på runstenar ger modellen rätt ord i {pr(DOC['right'])} procent av fallen. Det är lägre än i de andra proven, och det är väntat: här ligger luckorna där skadorna råkade hamna, och resten av stenen är ofta också skadad. Det är det prov som mest liknar de luckor modellen ska användas på.

**Dateringsprovet.** Modellen kan också uppskatta när en text skrevs, ur stavningen och ordförrådet. Den läser texten med var och en av fyra tidsperioder, från 800-talet till 1100-talet, och väljer den där texten är mest sannolik. På {svn(DT['n'])} daterade runstenar väljer den rätt period i {pr(DT['right'])} procent av fallen. Att alltid gissa den vanligaste perioden ger {pr(DT['majority'])} procent. Den hamnar högst en period fel i {pr(DT['near'])} procent. Det räcker inte för att ersätta stilgrupperna, men kan ge en första datering åt de stenar som saknar en.

## Säger den 90 procent, menar den 90 procent

Det viktigaste är inte att modellen har rätt så ofta som möjligt, utan att dess procent går att lita på. En väderprognos som säger 70 procents risk för regn ska ha regn ungefär sju dagar av tio. Samma krav ställer vi på modellen.

Här var de dokumenterade luckorna avgörande. Med en kalibrering skattad bara på utgivarnas luckor stämde procenten där, men inte på de dokumenterade. När modellen sa ungefär {pr(DB0[1]['said'])} procent hade den rätt i bara {pr(DB0[1]['right'])} procent av fallen. Den var alltså för säker just där svaret var osäkert. Nu skattas kalibreringen på tre slags luckor tillsammans: utgivarnas luckor, de maskerade orden och de dokumenterade luckorna. Appen använder de dokumenterade luckornas nivå, eftersom de liknar verklig skada.

Kalibreringen gör mer än att justera siffror: modellen väljer numera det ord som får högst kalibrerad procent, inte nödvändigtvis språkmodellens eget förstaval. Ett ords procent kan aldrig gå om ett annat ord av samma ordklass, men ett formelord kan gå om ett hopsatt namn, eftersom hopsatta namn oftare är fel. I korsvaliderade prov höjde det valet andelen rätt ord från {svn(100 * DNY['first_choice_right'], 1)} till {svn(100 * DNY['chosen_right'], 1)} procent på de dokumenterade luckorna och från {svn(100 * RNY['first_choice_right'], 1)} till {svn(100 * RNY['chosen_right'], 1)} på utgivarnas.

:::chart Vad modellen säger och hur ofta den har rätt, på de dokumenterade luckorna
""" + "\n".join(
    f"# Modellen säger {BIN_SV(b)}\nSäger i snitt | {100 * b['said']:.0f}\n+Har rätt | {100 * b['right']:.0f} | {b['n']} luckor" for b in DB1) + f"""
Källa: {DOC['gaps']} dokumenterade luckor på runstenar (runor kända från äldre avbildningar). Varje lucka har fått sin procent från en kalibrering som är gjord utan dess sten.
:::

Staplarna i varje par ska vara lika långa, och i tre av de fyra nivåerna är de det. I mellanregistret, där luckorna är få, är modellen fortfarande något för säker. Det genomsnittliga avståndet mellan vad modellen säger och hur ofta den har rätt, det mått som kallas kalibreringsfel, sjönk på de dokumenterade luckorna från {svn(100 * ECE0, 1)} till {svn(100 * ECE1, 1)} procentenheter. När modellen säger minst 95 procent har den rätt i {svn(100 * SURE_DOC['right'])} procent av fallen. Det gäller {SURE_DOC['n']} av de dokumenterade luckorna.

Vi prövade också kalibreringen där den inte hade fått se svaren. I det svåra maskeringsprovet, som inte ingick när den skattades, sjönk kalibreringsfelet för luckor inne i ord från 17 till {svn(100 * HNY['ece'], 1)} procentenheter. I utgivarnas luckor kommer modellen till samma ord som utgivarna i {svn(100 * VAL['rundata_sure'], 1)} procent av de fall där den säger minst 95 procent. Och i läsprovet skilde sig modellens egna procent för orden i snitt {svn(100 * R['ece_raw'], 1)} procentenheter från hur ofta den faktiskt hade rätt; efter kalibreringen är skillnaden {svn(100 * R['ece'], 1)} procentenheter.

## Kontrollerad i detalj

Ett verktyg som ska användas i forskning måste gå att lita på också i de delar man inte ser. Vi har därför kontrollerat modellens räkningar mot oberoende program och mot sig själv:

- **Ordföljden** räknas exakt som i NLTK, ett vanligt bibliotek för språkteknologi. Den största skillnaden på 3 000 ordpar är {CK['nltk_diff']}, alltså inget annat än avrundning.
- **Kalibreringen** ger samma resultat som scikit-learn. Vi prövade också en annan metod, isoton kalibrering, men den gav sämre resultat och används inte.
- **Den snabbare uträkningen.** För varje förslag i en lucka läste modellen förut om hela texten. Eftersom ett ord aldrig går över ett skiljetecken räcker det att läsa om gruppen kring luckan. Den nya uträkningen ger samma svar som den gamla, med skillnader på högst {CK['split_diff']}, och är {CK['split_speed']} gånger snabbare.
- **Stenar med många luckor.** När luckornas förslag ger fler än 256 kombinationer söker modellen fram den bästa lucka för lucka. På U 512, med nio luckor, gav det samma svar som att pröva alla kombinationer.
- **Automatiska tester.** {CK['unit_tests']} tester körs vid varje ändring av koden.
- **Allt är öppet.** Koden, proven och siffrorna finns på [GitHub]({GITHUB}), och metoden beskrivs i [METHODS.md]({METHODS}), avsnitt 8.1.

## Ett blindtest, låst i förväg

Alla siffror ovan kommer från prov som vi själva har byggt och läst av under arbetets gång. Ingen teststen ingår någonsin i sin egen modell, men den som bygger ett verktyg kan ändå omedvetet forma det efter sina testdata. Därför avslutade vi med ett blindtest enligt ett förregistrerat protokoll. Population, dragningsregel, inställningar, mått och godkäntgränser skrevs ned och låstes i versionshistoriken innan en enda lucka fylldes, och dragningens slumpfrö är registreringens egen kontrollsumma – urvalet kan alltså inte ha valts i efterhand. Ur {BL['population']} runstenar med dokumenterade luckor, där varje sten som någonsin förekommit i våra artiklar, skanningar eller fallstudier var bortplockad i förväg, drogs {BL['stones']} stenar med {BL['n']} luckor. Det låsta kravet: mellan {BL['interval'][0]} och {BL['interval'][1]} rätt av {BL['n']} vore förenligt med riktmärket, testet körs en gång, och resultatet redovisas vad det än visar.

Modellen valde utgivarnas ord i {BL['right']} av {BL['n']} luckor, {pr(BL['right'] / BL['n'])} procent – mitt i det låsta intervallet. Alla {BL['claimed95']['n']} luckor där den påstod minst 95 procent blev rätt. Och fyra av de fem missarna bar modellens egen varning, med påståenden under 45 procent: *spaka* där utgivarna läser sammansättningen *malspaka*, gissningar på 14 procent där svaret är ortnamnet *svanaby* och det sällsynta namnet *liðsvaldr*. Den enda halvsäkra missen är värd att citera som den är: i Sm 121:s *---ur* föreslog modellen *faður*, "fader", med 77 procent – utgivarna läser *moðurbroður*, "morbror". Protokollet, urvalet och varje luckas utfall ligger orörda i versionshistoriken på GitHub.

## Sö 206: en enda runa avgör

Sö 206 står vid Överselö kyrka. Inskriften lyder i utgåvans översättning: "Här skall stånda stenarna dessa, av runor röda, reste dem Gudlög efter sina söner, och Hjälmlög efter sina bröder." Två ställen är skadade.

![Sö 206 med närbild av det vittrade bandet]({FIG['so206']['sv']})
Sö 206 vid Överselö kyrka, exporterad i hög upplösning ur Vitki av Viktor Kvant. Till höger toppen av det vänstra runbandet. Ringen visar ungefär var den förlorade runan i *ru?niR* satt. Bilden är beräknad ur {CREDIT_SV}.

I det första ordet, *ru?niR*, är runan enligt utgåvan "helt borta, därigenom att en flisa av stenytan fallit av". Modellen har två huvudförslag: *Hrungnir*, namnet på en jätte i Eddan, och *roðnir*, 'rödfärgade', som är utgivarnas läsning. Språkmodellen själv föredrar jätten, med {svn(100 * RAW206['hrungnir'])} procent mot {svn(100 * RAW206['roðnir'])}. Men i prov med känt svar visar sig sådana förstaval ofta fel, och efter kalibreringen återstår {svn(S206A[0][1])} procent för *Hrungnir* och {svn(S206A[1][1])} för *roðnir* – resten lämnas öppet. Språket ensamt avgör alltså inte saken.

Skillnaden mellan förslagen är en enda runa. *roðnir* skrivs med þ och *Hrungnir* med k, *rukniR*. Om skanningen hade visat en rest av den ena eller den andra skulle frågan nästan vara avgjord.

![Ett enda spår avgör]({FIG['spar']['sv']})
Modellens förslag för *ru?niR* på Sö 206, utan spår och med ett tänkt spår av þ eller k. Spåren räknas som troliga, inte säkra, och därför når inget förslag ända upp till 100 procent.

På Sö 206 finns ingen sådan rest, för flisan är borta. Utgivarna avgjorde i stället saken med betydelsen. Elias Wessén skriver i utgåvan att det är "icke möjligt att genom insättning av någon annan runa än þ få ett ord, som ger en förnuftig mening i sammanhanget". Han nämner att Hallström hade invänt mot läsningen i Fornvännen 1931, men avfärdar invändningarna som "en alltför långt driven skepsis". Modellen räknar med ord och ordföljd, inte med mening. Det den tillför är att visa exakt vad avgörandet vilar på: en enda runa, och betydelsen.

I det andra skadade ordet, *k???auk*, finns enligt utgåvan bara de nedre delarna av staplarna i tre runor kvar, "men läsningen är säker på grund av Sö 208". På den stenen, vid samma kyrka, står Guðlaug och Hjalmlaug tillsammans. Sö 208 ligger i samma provdel som Sö 206, och därför har den vanliga modellen inte sett den. Den ger inget förslag mer än {svn(S206B[0][1])} procent: *{NM(S206B[0][0])}* {svn(S206B[0][1])}, *{NM(S206B[1][0])}* {svn(S206B[1][1])} och *{NM(S206B[2][0])}* {svn(S206B[2][1])} procent. Den säger alltså att den inte vet. När en enskild sten ska analyseras på riktigt tränas modellen därför på allt utom just den stenen, så att den ser systerstenarna men aldrig stenens egen text.

:::box Fler skannade stenar ur samma serie
- **Sö 137, Aspa:** *þ??si* blir *þannsi*, 'denna', med {svn(S137[1], 1)} procent. Utgivarna läser þ[ann]si.
- **Sö 211, Ljunga:** *sta??* blir *stæin*, 'sten', med {svn(S211[1], 1)} procent. Utgivarna läser stæ[in].
- Formelord som dessa är de lättaste luckorna. Namnen är svårare: i *hak????* på Sö 211, där utgivarna läser Hak[i ok], ger modellen inget förslag över {svn(S211_NAME[1])} procent.
:::

## Alla runstenar med luckor

Vi har låtit modellen läsa alla {svn(N_WITH)} vikingatida runstenar som har luckor på en till fyra runor. {N_FEW} av dem har färre än fyra läsbara runor och kan inte läsas. De andra {svn(N_STONES)}, med sammanlagt {svn(N_GAPS)} luckor, läses i fem delar samtidigt på en vanlig dator, och körningen tar {hours(HOURS, 'sv')}. Den första körningen tog betydligt längre tid; den snabbare uträkningen ovan har kortat den. Samtidigt läste modellen {D['batch']['other_inscriptions']} inskrifter på andra stenar och lösa föremål, med {D['batch']['other_gaps']} luckor, men dem räknar vi inte med här.

:::chart Hur säker modellen är i alla {svn(N_GAPS)} luckor på runstenarna
+Minst 95 % | {share('≥95'):.1f} | {svn(ALL['≥95'])} luckor
80–95 % | {share('80–95'):.1f} | {svn(ALL['80–95'])} luckor
50–80 % | {share('50–80'):.1f} | {svn(ALL['50–80'])} luckor
Under 50 % | {share('<50'):.1f} | {svn(ALL['<50'])} luckor
Inget förslag | {share('inget förslag'):.1f} | {svn(ALL['inget förslag'])} luckor där ordet är okänt för modellen
Källa: Vitkis körning av {D['version']} på alla vikingatida runstenar i Rundata med luckor på 1–4 runor, också fragment och försvunna stenar.
:::

I {svn(share('≥95'))} procent av luckorna är modellen minst 95 procent säker. I {svn(share('<50'))} procent är den under 50 procent, och där ger den en lista med flera förslag i stället för ett svar.

Mest intressant är jämförelsen med utgivarna. Bland luckorna på svenska runstenar som utgivarna har fyllt säger modellen minst 95 procent i {REST_SURE} av {REST_N}. Bland dem som utgivarna har lämnat öppna {OPEN_SV}. Där runologerna inte kunde avgöra saken påstår sig modellen alltså {'aldrig' if OPEN_SURE == 0 else 'sällan'} veta. Så vill vi att den ska fungera.

I {BT['boundaries']} luckor står orden utan skiljetecken, och förslaget ändras om man delar orden som utgivarna gör. Där visar modellen båda förslagen.

## Varför det spelar roll

- **Säkerheten syns.** En hakparentes visar att något är ifyllt. Modellen visar också hur säkert det är och vilka andra möjligheter som finns, med procent som är prövade mot facit.
- **Samma måttstock för alla stenar.** Alla {svn(N_GAPS)} luckor på runstenarna är lästa efter samma regler. När modellen förbättras, eller när en ny läsning kommer, kan allt räknas om.
- **Den visar var man ska titta.** På Sö 206 hänger allt på om en rest av þ eller k finns kvar. Med 3D-skanningar kan sådana ställen granskas med en halv millimeters noggrannhet.
- **Allt är öppet.** Koden, proven och siffrorna finns på [GitHub]({GITHUB}), så att vem som helst kan pröva om dem.

Liknande verktyg har byggts för grekiska inskrifter, där modellen Ithaca föreslår förlorade bokstäver (Assael m.fl. 2022). Vitkis modell är byggd för runornas egna svårigheter: den tvetydiga stavningen, de många namnen och spåren i skanningarna. Den ersätter inte runologen. Den ger runologen en andra bedömning som går att räkna på.

## Innan modellen släpps

Det återstår arbete innan modellen kommer ut i appen:

- **Spår ur skanningarna.** I dag räknar modellen bara med spår som någon har lagt in för hand, men läsaren som ska hämta dem direkt ur 3D-skanningen är på god väg. Bistavarna, som skiljer runorna åt, går inte att lita på i de uttunnade spårlinjerna – de läses nu i stället ur själva djupbilden, viktade efter hur djupt de är huggna. I ett första prov på {SCN['stones']} skannade stenar, där hela ord maskerades och fylldes av en modell som aldrig sett stenen, steg andelen rätt från {svn(100 * SCN['utan'], 1)} till {svn(100 * SCN['skanner'], 1)} procent när skannerns spår fick hjälpa till – och med spåren slumpvis omflyttade mellan stenens runor försvann hela vinsten. Det är alltså stenen som läses, inte en räknelek. Vid svårt vittrade partier kan spåren vilseleda, så panelen visar vad skannern ser – bistavarna med huggdjup och de möjliga runorna – och spåren räknas först när användaren har bekräftat dem. En runa med fler djupa bistavar än någon runa har, en möjlig bindruna, föreslår inget alls.
- **Namnen.** Namn blir rätt i {svn(PCT_CLS[2])} procent av utgivarnas luckor, mot {svn(PCT_CLS[0])} för formelord. De flesta fel i de dokumenterade luckorna gäller namn. Den senaste versionen tog ett steg just här: namnbyggarens förslag föll tidigare bort ur kandidatlistan innan de hann vägas, och när de fick en egen plats (textmodel-18) vann modellen åtta maskerade luckor – bland dem namnen *Guðfastr* och *Þormóðr* – utan att förlora någon.
- **Fler texter från Danmark och Norge**, så att måttstocken blir lika rättvis för alla länder.
- **Böjningen.** Modellen kan inte kasus och kongruens. Det gäller dock bara omkring ett ord av hundra i läsprovet, mest namn i fel kasus. Det mesta av det som ser ut som fel form är i stället olika normaliseringar i Rundata, som *sin* och *sinn*.
- **Facit.** Utgivarnas ifyllning är själv en bedömning. Maskeringsprovet och de dokumenterade luckorna har säkrare facit.

När detta är på plats kommer modellen ut i panelen *Läsning och luckor* på varje inskrifts sida i Vitki.

## Den andra modellen: hur språklik är en runföljd?

Vitki har också en mindre modell som mäter hur mycket en runföljd liknar språk. Den använde vi i artikeln [Tyde den som kan]({SPRAK}) för att dela de otolkade inskrifterna i runrader, trasigt språk och följder som inte liknar språk. Också den har förbättrats genom prov som först gick fel. Korta, trasiga bitar såg obegripliga ut bara för att de var korta, så nu jämförs varje inskrift med riktiga texter som klippts i exakt samma längder. Danska och norska fragment mättes först mot en mest svensk måttstock; nu jämförs de med texter från samma land. Runraden på DR EM85;470C, *fuþrkhainsl*, bedömdes först som "inte språk" eftersom den avviker från den vanliga ordningen; nu känns också runrader med avvikelser igen. Och Rundatas alternativa läsningar räknas inte längre som en del av texten. Varje ändring står i koden.

## Så gjorde vi

- **Data:** Samnordisk runtextdatabas (Rundata). Modellen lär sig av alla {svn(D['viking_all'])} vikingatida inskrifter med translitterering och normalisering och av Eddans ordförråd. Proven och körningen redovisas för de {svn(D['viking_runestones'])} runstenarna, också fragment och försvunna stenar. Andra stenar och lösa föremål nämns för sig (utdata/modellartikel/runstenar.py).
- **Läsprovet:** scripts/runlm_calibrate.py, på {R['inscriptions']} inskrifter där Rundatas ord täcker den huggna texten exakt. Materialet delas i fem delar efter signum.
- **Maskeringsproven:** scripts/runlm_restore_test.py, {MK['inne i ord']['n'] + MK['helt ord']['n']} dolda luckor på runstenar, och med --hard bara ord utanför de 50 vanligaste. Spåren i det simulerade provet är ritade med typsnittet Apple Symbols.
- **Utgivarnas luckor:** scripts/runlm_gaps.py. Samma ord i annan böjning eller normalisering räknas som samma ord.
- **De dokumenterade luckorna:** scripts/runlm_documented_test.py. Runor inom hakparentes görs till luckor, och facit är de dokumenterade runorna och Rundatas normalisering.
- **Kalibreringen:** scripts/runlm_gap_calibrate.py, med alla tre slagen av luckor och korsvalidering där hela stenar hålls utanför.
- **Dateringsprovet:** scripts/runlm_dating.py, på {svn(DT['n'])} daterade runstenar.
- **Körningen över alla stenar:** scripts/textmodel_batch.py. Jämförelsen med utgivarna görs i utdata/modellartikel/batch_status.py.
- **Sö 206 med spår:** modellens svar när bara þ, eller bara k, är tillåten i luckan (src/textmodel.py, med spåren som troliga).
- **Bilderna:** Sö 45 i strykljus, beräknad i Vitki. Sö 206 exporterad i hög upplösning ur Vitki. Illustrationerna är ritade med utdata/modellartikel/figurer.py.
- **Hela metoden:** [METHODS.md]({METHODS}), avsnitt 8.1.

## Om skanningarna

Sö 45 och Sö 206 skannades av Laila Kitzler Åhfeldt vid Riksantikvarieämbetet inom forskningsprojektet Runristandets dynamik (2009–2014), med en skanner som mäter ytan med strukturerat ljus. Bara de ristade ytorna är skannade. År 2024 publicerade hon skanningarna av 35 sörmländska runstenar fritt på Zenodo, med licensen CC BY 4.0. Vi använder filerna *So 45_1_4 thin_closed holes.stl* och *So 206_thin03_closed holes.stl* som de är publicerade. Bilden av Sö 45 är beräknad i Vitki, och bilden av Sö 206 exporterade Viktor Kvant ur Vitki i hög upplösning. Hennes egna studier av skanningarna finns i Kitzler Åhfeldt 2015 och 2017. Vi tackar för att datamängden har gjorts fritt tillgänglig.

## Källor

- Kitzler Åhfeldt, L. 2024. *3D-data Runstenar i Södermanland* [Dataset]. Riksantikvarieämbetet. doi:[10.5281/zenodo.11951255]({KA}). CC BY 4.0.
- Kitzler Åhfeldt, L. 2015. Rune Carvers and Local Mobility. *Viking and Medieval Scandinavia* 11, s. 143–182.
- Kitzler Åhfeldt, L. 2017. *Runristare och mobilitet i Södermanland*. Rapport. Stockholm: Riksantikvarieämbetet.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Brate, E. & Wessén, E. 1924–36. *Södermanlands runinskrifter* (Sveriges runinskrifter 3). Stockholm: KVHAA. Digitaliserad av [Riksantikvarieämbetet]({SRI_URL}). Sö 45 på s. 34 f., Sö 206 och Sö 208 på s. 181 ff.
- Kneser, R. & Ney, H. 1995. Improved backing-off for M-gram language modeling. *Proceedings of the 1995 International Conference on Acoustics, Speech, and Signal Processing* 1, s. 181–184.
- Bird, S., Klein, E. & Loper, E. 2009. *Natural Language Processing with Python*. Sebastopol: O'Reilly. (NLTK)
- Pedregosa, F. m.fl. 2011. Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research* 12, s. 2825–2830.
- Platt, J. 1999. Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods. I: Smola, A. m.fl. (red.), *Advances in Large Margin Classifiers*. Cambridge, MA: MIT Press, s. 61–74.
- Assael, Y., Sommerschield, T., Shillingford, B. m.fl. 2022. Restoring and attributing ancient texts using deep neural networks. *Nature* 603, s. 280–283.
"""

title_en = "The missing runes – work in progress on Vitki's probability model"
summary_en = ("Many runestones have places where runes have been lost. We are building a model that proposes what stood "
              "there and says how sure it is. Here we report how far we have come and how the model is tested: six tests "
              "with a known answer, calibrated percentages and checks of the code. The model is not yet released in the app.")

body_en = f"""![Sö 45 in raking light, with a close-up of the damaged runes]({FIG['so45']['en']})
Sö 45 at Stora Släbro in Södermanland, in raking light from a 3D scan. On the right, a close-up of the left rune band. Inside the dashed ring two runes are damaged in the stone's first word, the man's name GæiRf[as]tr: one by flint, the other by a deep pit. The image is computed in Vitki from {CREDIT_EN}.

Hardly any runestone has survived a thousand years undamaged. Stones have cracked, flakes have come off and weathering has eaten into the carving. Of the {enn(D['viking_runestones'])} Viking-age runestones in the Scandinavian Runic-text Data Base, {enn(N_WITH)} have at least one place where one to four runes have been lost.

When runologists publish a stone they often fill such gaps. The restored runes are put in square brackets, as in GæiRf[as]tr. The brackets say that the runes cannot be seen on the stone. They do not say how sure the editor was, or which other possibilities were weighed.

In Vitki we are building a model that does the same work in a different way. It proposes what stood in the gap, ranks the proposals and states how sure it is. The percentage is tested against gaps where the answer is known, so that 90 per cent should mean that the proposal is right about nine times out of ten. Here we report how far we have come, and we account for every test, so that anyone who wishes can examine how the model is built and tested before it is released.

:::box Work in progress
- The model is part of Vitki's open source code but is **not yet released in the app**. We are still testing and improving it.
- The figures apply to the version we have today ({D['version']}, October 2026) and may change.
- The figures apply to runestones, fragments and lost stones included. The model also reads inscriptions on other stones and loose objects such as amulets and rune bones, and where it does we say so.
- The proposals are proposals, not interpretations. The model works with runes, words and word order, not with what a text means.
:::

## A puzzle with too few pieces

The younger futhark has only 16 runes, but the language had many more sounds. The same rune therefore had to stand for several sounds: ᚴ could be k, g or ng, and ᛁ could be i, e, æ or j. Nor did the carvers always put dividers between the words. A sequence of runes can thus be read in several ways even when all the runes survive. When some are missing, the possibilities multiply.

![One rune – several sounds]({FIG['runljud']['en']})
A selection from the model's spelling table, simplified. The model has learned how often each sound was written with each rune, in different periods and regions.

## How the model reasons

Take Sö 45 as an example. According to *Södermanlands runinskrifter* the stone is broken into three pieces. The first name begins with the runes kai on the lowest piece and continues with Rfastr on the upper left one. There the stave of the a is "indistinct because of flint", and of the s only "the upper stave and the starting point of the middle stroke" remain; "the rest of the rune is destroyed by a deep pit". The editors read GæiRf[as]tr. The model is shown the runes kaiRf??tr, where the two question marks are the lost runes.

![How the model reasons]({FIG['flode']['en']})
The model's steps, with the gap on Sö 45 as the example.

First the model tries which words can be spelled with the surviving runes plus two more. Then each proposal is weighed by how well it fits where it stands. It is the same principle as when a phone suggests the next word: some words tend to follow certain others. Here the word stands first in the text, followed by another name, Æistfari, and the verb *ræisþu*, 'raised'. The name GæiRfastr occurs on several other stones, for example Sö 227, Sm 111 and U 1144, so the model knows it. We did not enter any traces of the runes here.

The answer is GæiRfastr with {enn(S45[0][1])} per cent and GæiRfriðr with {enn(S45[1][1])}. The first proposal is the same name that the editors wrote in. The model has not seen the text of Sö 45 itself, because a stone is always read by a version of the model that was trained without it.

## The building blocks

The model is not one big machine but several parts, each of which can be tested on its own. Several of them are well-tried methods from language technology. The model learns the language from every kind of Viking-age inscription, not only the runestones, since it is the same on an amulet as on a stone.

- **Spelling.** The model has learned how sounds were written in runes from 27,218 pairs of carved words and their normalized form, from 2,877 inscriptions. Spelling is estimated for each period and region, so that a stone from the 900s is not read like one from the 1000s.
- **Word order.** How often one word follows another is counted with a method from speech recognition, Kneser–Ney smoothing (Kneser & Ney 1995). It also gives rare word pairs a reasonable chance.
- **Word classes.** Words that occur in similar contexts are grouped automatically. The genitives *hans*, *hennaR*, *sina* and *þæiRa* end up in the same class without anyone having told the model what a genitive is. This helps it with rare words. The classes are computed with scikit-learn.
- **Names.** Many names occur on one stone only. The model therefore builds unknown names from first elements, second elements and endings, spelled as the carvers spelled them. The first element Ragn-, for example, is carved as *rahn* 17 times in Rundata.
- **Neighbouring stones.** Names on stones within ten kilometres weigh a little more, since the same families often raised several stones in the same district.
- **Dividers.** Carvers differed. Most put dividers between nearly all words, some between none at all. The model therefore estimates for each stone how often that carver marked a word boundary, and lets this decide how readily it places a boundary itself where the carver put no sign.
- **Traces.** If a remnant of a rune is visible in the scan or in the edition's description, it can be entered. A trace counts as likely but not certain, so that a misread remnant does not shut out the right answer.
- **Calibration.** The model's own percentages were too high, especially for names. They are therefore adjusted with a logistic model, the same principle as in Platt (1999), separately for formula words, known names, names the model has composed itself and other words. All the proposals in a gap are calibrated together, and "none of the proposals" gets a probability of its own; the first choice gets a deduction of its own, since it was chosen precisely because its probability was the highest. The calibration is estimated on three kinds of gaps with a known answer, described below.
- **No cheating.** The material is split into five parts by signum. A stone is always read by a model trained on the other four, so that the editors' restoration never leaks in. When a single stone is to be analysed, the model can also be trained on everything except that stone.

## Six tests with a known answer

A proposal is only worth something if you know how often it is right. We therefore test the model in six ways, always on stones it was not trained on. Each test answers a question of its own:

- **The reading test:** does the model read whole texts correctly when it must decide for itself where the words begin?
- **The masking test:** can it fill runes that we hide in texts with a known answer?
- **The hard masking test:** can it do the same when the answer is never a formula word?
- **The editors' gaps:** does it arrive at the same word as the editors where they have filled a gap?
- **The documented gaps:** is it right where runes have really been lost but are known from older drawings?
- **The dating test:** can it tell when a text was written, from the language alone?

:::chart Right word in the tests, runestones
+The reading test | {100 * RK['runsten']['same']:.1f} | {enn(RK['runsten']['words'])} words on {RK['runsten']['inscriptions']} runestones
Masking, inside a word | {100 * MK['inne i ord']['right']:.1f} | {MK['inne i ord']['n']} gaps
Masking, whole word | {100 * MK['helt ord']['right']:.1f} | {MK['helt ord']['n']} gaps
Masking, whole word with half the rune visible | {100 * VAL['with_traces']:.1f} | simulated traces
Hard masking, inside a word | {100 * HD['inne i ord']['right']:.1f} | {HD['inne i ord']['n']} gaps without formula words
The editors' gaps | {100 * RG['right']:.1f} | {RG['known']} gaps
Documented gaps | {100 * DOC['right']:.1f} | {DOC['gaps']} gaps
Source: Vitki's tests with {D['version']}, in five parts. The tests measure different things and are hard in different ways, so the bars should not be compared as a contest.
:::

**The reading test.** The model reads {R['inscriptions']} inscriptions where the answer is known, {enn(R['words'])} words in all, without the editors' word boundaries. It chooses the same word as the editors in {enn(100 * R['same'], 1)} per cent of cases and divides the words correctly in {enn(100 * R['span'], 1)} per cent. When the first version was ready in October the figures were {R['first_same']} and {R['first_span']} per cent. Three percentage points may sound little, but it is about {enn(R['gain_words'])} more words read correctly, and about half of the gain came when the model learned to build names. The {R['inscriptions']} inscriptions are {RK['runsten']['inscriptions']} runestones, {RK['annan sten']['inscriptions']} other stones and {RK['lösa föremål']['inscriptions']} loose objects. On the runestones the model chooses the same word as the editors in {enn(100 * RK['runsten']['same'], 1)} per cent of cases and divides the words correctly in {enn(100 * RK['runsten']['span'], 1)} per cent. The loose objects are hardest, at {enn(100 * RK['lösa föremål']['same'])} and {enn(100 * RK['lösa föremål']['span'])} per cent.

:::chart The reading test, from the first version to today
# Same word as the editors
First version | {R['first_same']}
+Today | {100 * R['same']:.1f}
# Words divided correctly
First version | {R['first_span']}
+Today | {100 * R['span']:.1f}
Source: Vitki's reading test on {R['inscriptions']} inscriptions ({RK['runsten']['inscriptions']} runestones, {RK['annan sten']['inscriptions']} other stones and {RK['lösa föremål']['inscriptions']} loose objects) with {enn(R['words'])} words, in five parts.
:::

**The masking test.** Here we hide runes in texts where the answer is known and let the model fill them in. If a few runes inside a word on a runestone are missing, it gives the right word in {pr(MK['inne i ord']['right'])} per cent of cases. If a whole word is missing, the figure is {pr(MK['helt ord']['right'])} per cent, since then no runes are left to go on, only the words around it. In a simulated test on runestones, where half of each lost rune is visible, the share of whole words that are right rises to {pr(VAL['with_traces'])} per cent, and it is still {pr(VAL['with_misread_traces'])} per cent when one trace in five is misread. That test is simulated with clean rune shapes and shows what the traces are worth at best.

**The hard masking test.** Formula words such as *stone*, *raised* and *in memory of* are easy to guess. In this test we therefore hide only words outside the 50 most common. The model then gives the right word in {pr(HD['inne i ord']['right'])} per cent of cases when a few runes are missing inside the word, and in {pr(HD['helt ord']['right'])} per cent when the whole word is missing. The test shows how much the formulas help, and how hard it is to guess an unusual word without traces. What matters is that the model knows it, and it does so almost all the way: when it says at least 95 per cent it is right in {pr(HD['pooled']['sure_right_sw'])} cases out of a hundred here too, measured by the same rule as in the editors' gaps – counting every normalization variant as wrong instead, such as hakun against hakon, gives {pr(HD['pooled']['sure_right'])} out of a hundred. The test did teach us one reservation: in the 80–95 per cent band the model is somewhat too sure about unusual words. There it claims {pr(HD['pooled']['band_said'])} per cent on average but is right in {pr(HD['pooled']['band_right_sw'])} cases out of a hundred. Anyone filling a gap whose answer cannot be a formula word should read percentages in that band with that margin.

**The editors' gaps.** We test the model on {RG['restored']} gaps on {RG['stones']} runestones that the editors have filled. The model makes a proposal in {RG['known']} of them, and {enn(100 * RG['right'])} per cent of the proposals are the same word the editors chose. Formula words are right in {enn(PCT_CLS[0])} per cent, names in {enn(PCT_CLS[2])} and other words in {enn(PCT_CLS[1])} per cent. Even so, this test is easier than reality. Editors prefer to fill gaps where the answer is given and leave the hard ones open, so the gaps they have filled are often the simple ones.

**The documented gaps.** A better test is found in Rundata itself. Runes within square brackets are lost on the stone but known from older drawings. They fell off for physical reasons, not because they were easy to guess, and yet the answer is documented. We turn each such run of one to four runes inside a word into a gap. On {DOC['gaps']} such gaps on runestones the model gives the right word in {pr(DOC['right'])} per cent of cases. That is lower than in the other tests, as expected: here the gaps lie wherever the damage happened to fall, and the rest of the stone is often damaged too. It is the test that most resembles the gaps the model is meant for.

**The dating test.** The model can also estimate when a text was written, from its spelling and vocabulary. It reads the text with each of four periods, from the 800s to the 1100s, and chooses the one in which the text is most probable. On {enn(DT['n'])} dated runestones it chooses the right period in {pr(DT['right'])} per cent of cases. Always guessing the most common period gives {pr(DT['majority'])} per cent. It is at most one period off in {pr(DT['near'])} per cent. That is not enough to replace the style groups, but it can give a first date to the stones that have none.

## When it says 90 per cent, it means 90 per cent

What matters most is not that the model is right as often as possible, but that its percentages can be trusted. A weather forecast that says 70 per cent chance of rain should see rain on about seven days out of ten. We hold the model to the same standard.

Here the documented gaps were decisive. With a calibration estimated on the editors' gaps alone, the percentages held there, but not on the documented gaps. When the model said about {pr(DB0[1]['said'])} per cent, it was right in only {pr(DB0[1]['right'])} per cent of cases. It was too sure precisely where the answer was uncertain. The calibration is now estimated on three kinds of gaps together: the editors' gaps, the masked words and the documented gaps. The app uses the level of the documented gaps, since they resemble real damage.

The calibration does more than adjust figures: the model now chooses the word with the highest calibrated percentage, not necessarily the language model's own first choice. A word's percentage can never overtake another word of the same class, but a formula word can overtake a composed name, since composed names are more often wrong. In cross-validated tests this choice raised the share of right words from {enn(100 * DNY['first_choice_right'], 1)} to {enn(100 * DNY['chosen_right'], 1)} per cent on the documented gaps and from {enn(100 * RNY['first_choice_right'], 1)} to {enn(100 * RNY['chosen_right'], 1)} on the editors' gaps.

:::chart What the model says and how often it is right, on the documented gaps
""" + "\n".join(
    f"# The model says {BIN_EN(b)}\nSays on average | {100 * b['said']:.0f}\n+Is right | {100 * b['right']:.0f} | {b['n']} gaps" for b in DB1) + f"""
Source: {DOC['gaps']} documented gaps on runestones (runes known from older drawings). Each gap got its percentage from a calibration made without its stone.
:::

The bars in each pair should be equally long, and in three of the four bands they are. In the middle range, where the gaps are few, the model is still somewhat too sure. The average distance between what the model says and how often it is right, the measure called calibration error, fell on the documented gaps from {enn(100 * ECE0, 1)} to {enn(100 * ECE1, 1)} percentage points. When the model says at least 95 per cent it is right in {enn(100 * SURE_DOC['right'])} per cent of cases. That applies to {SURE_DOC['n']} of the documented gaps.

We also tested the calibration where it had not seen the answers. In the hard masking test, which was not used when it was estimated, the calibration error for gaps inside a word fell from 17 to {enn(100 * HNY['ece'], 1)} percentage points. In the editors' gaps the model arrives at the same word as the editors in {enn(100 * VAL['rundata_sure'], 1)} per cent of the cases where it says at least 95 per cent. And in the reading test the model's own percentages for the words differed on average by {enn(100 * R['ece_raw'], 1)} percentage points from how often it was actually right; after calibration the difference is {enn(100 * R['ece'], 1)} percentage points.

## Checked in detail

A tool meant for research must be trustworthy also in the parts one does not see. We have therefore checked the model's calculations against independent programs and against itself:

- **Word order** is computed exactly as in NLTK, a widely used library for language technology. The largest difference over 3,000 word pairs is {CK['nltk_diff']}, nothing but rounding.
- **The calibration** gives the same results as scikit-learn. We also tried another method, isotonic calibration, but it gave worse results and is not used.
- **The faster calculation.** For each proposal in a gap the model used to read the whole text again. Since a word never runs across a divider, it is enough to read the group around the gap again. The new calculation gives the same answers as the old one, with differences of at most {CK['split_diff']}, and is {CK['split_speed_en']} times faster.
- **Stones with many gaps.** When the proposals for the gaps give more than 256 combinations, the model searches for the best one gap by gap. On U 512, with nine gaps, this gave the same answer as trying every combination.
- **Automatic tests.** {CK['unit_tests']} tests run at every change to the code.
- **Everything is open.** The code, the tests and the figures are on [GitHub]({GITHUB}), and the method is described in [METHODS.md]({METHODS}), section 8.1.

## A blind test, locked in advance

Every figure above comes from tests we built and read off ourselves as the work went along. No test stone is ever part of its own model, but whoever builds a tool can still shape it, without noticing, after their test data. We therefore finished with a blind test under a pre-registered protocol. Population, drawing rule, settings, measures and pass limits were written down and locked in the version history before a single gap was filled, and the draw's random seed is the registration's own checksum – so the selection cannot have been picked after the fact. From {BL['population']} runestones with documented gaps, where every stone that had ever appeared in our articles, scans or case studies was removed in advance, {BL['stones']} stones with {BL['n']} gaps were drawn. The locked requirement: between {BL['interval'][0]} and {BL['interval'][1]} right out of {BL['n']} would be consistent with the benchmark, the test runs once, and the result is reported whatever it shows.

The model chose the editors' word in {BL['right']} of {BL['n']} gaps, {pr(BL['right'] / BL['n'])} per cent – in the middle of the locked interval. All {BL['claimed95']['n']} gaps where it claimed at least 95 per cent came out right. And four of the five misses carried the model's own warning, with claims below 45 per cent: *spaka* where the editors read the compound *malspaka*, guesses at 14 per cent where the answer is the place name *svanaby* and the rare name *liðsvaldr*. The one half-confident miss deserves quoting as it stands: in Sm 121's *---ur* the model proposed *faður*, "father", at 77 per cent – the editors read *moðurbroður*, "mother's brother". The protocol, the draw and every gap's outcome sit untouched in the version history on GitHub.

## Sö 206: a single rune decides

Sö 206 stands at Överselö church. Rundata translates the inscription: "Here shall these stones stand, reddened with runes: Guðlaug raised (them) in memory of her sons; and Hjalmlaug in memory of her brothers." Two places are damaged.

![Sö 206 with a close-up of the weathered band]({FIG['so206']['en']})
Sö 206 at Överselö church, exported at high resolution from Vitki by Viktor Kvant. On the right, the top of the left rune band. The ring shows roughly where the lost rune of *ru?niR* was. The image is computed from {CREDIT_EN}.

In the first word, *ru?niR*, the rune is according to the edition "entirely gone, because a flake of the stone surface has fallen off". The model has two main proposals: *Hrungnir*, the name of a giant in the Edda, and *roðnir*, 'reddened', which is the editors' reading. The language model itself prefers the giant, with {enn(100 * RAW206['hrungnir'])} per cent against {enn(100 * RAW206['roðnir'])}. But in tests with a known answer such first choices often prove wrong, and after calibration {enn(S206A[0][1])} per cent remain for *Hrungnir* and {enn(S206A[1][1])} for *roðnir* – the rest is left open. The language alone thus does not settle the matter.

The difference between the proposals is a single rune. *roðnir* is written with þ and *Hrungnir* with k, *rukniR*. Had the scan shown a remnant of one or the other, the question would be nearly settled.

![A single trace decides]({FIG['spar']['en']})
The model's proposals for *ru?niR* on Sö 206, without a trace and with an imagined trace of þ or k. Traces count as likely, not certain, which is why no proposal reaches 100 per cent.

On Sö 206 there is no such remnant, since the flake is gone. The editors instead settled the matter by meaning. Elias Wessén writes in the edition that it is "not possible, by inserting any rune other than þ, to obtain a word that makes sense in the context". He mentions that Hallström had objected to the reading in Fornvännen in 1931, but dismisses the objections as "a scepticism carried too far". The model works with words and word order, not with meaning. What it adds is to show exactly what the decision rests on: a single rune, and the meaning.

In the second damaged word, *k???auk*, only the lower parts of the staves of three runes remain according to the edition, "but the reading is certain because of Sö 208". On that stone, at the same church, Guðlaug and Hjalmlaug stand together. Sö 208 is in the same test part as Sö 206, and so the ordinary model has not seen it. It gives no proposal more than {enn(S206B[0][1])} per cent: *{NM(S206B[0][0])}* {enn(S206B[0][1])}, *{NM(S206B[1][0])}* {enn(S206B[1][1])} and *{NM(S206B[2][0])}* {enn(S206B[2][1])} per cent. In other words, it says that it does not know. When a single stone is to be analysed for real, the model is therefore trained on everything except that stone, so that it sees the sister stones but never the stone's own text.

:::box More scanned stones from the same series
- **Sö 137, Aspa:** *þ??si* becomes *þannsi*, 'this', with {enn(S137[1], 1)} per cent. The editors read þ[ann]si.
- **Sö 211, Ljunga:** *sta??* becomes *stæin*, 'stone', with {enn(S211[1], 1)} per cent. The editors read stæ[in].
- Formula words like these are the easiest gaps. Names are harder: in *hak????* on Sö 211, where the editors read Hak[i ok], the model gives no proposal above {enn(S211_NAME[1])} per cent.
:::

## Every runestone with gaps

We let the model read all {enn(N_WITH)} Viking-age runestones that have gaps of one to four runes. {N_FEW} of them have fewer than four legible runes and cannot be read. The other {enn(N_STONES)}, with {enn(N_GAPS)} gaps in all, are read in five parts at once on an ordinary computer, and the run takes {hours(HOURS, 'en')}. The first run took considerably longer; the faster calculation above has shortened it. At the same time the model read {D['batch']['other_inscriptions']} inscriptions on other stones and loose objects, with {D['batch']['other_gaps']} gaps, but we do not count them here.

:::chart How sure the model is in all {enn(N_GAPS)} gaps on the runestones
+At least 95 % | {share('≥95'):.1f} | {enn(ALL['≥95'])} gaps
80–95 % | {share('80–95'):.1f} | {enn(ALL['80–95'])} gaps
50–80 % | {share('50–80'):.1f} | {enn(ALL['50–80'])} gaps
Under 50 % | {share('<50'):.1f} | {enn(ALL['<50'])} gaps
No proposal | {share('inget förslag'):.1f} | {enn(ALL['inget förslag'])} gaps where the word is unknown to the model
Source: Vitki's run of {D['version']} on every Viking-age runestone in Rundata with gaps of 1–4 runes, fragments and lost stones included.
:::

In {enn(share('≥95'))} per cent of the gaps the model is at least 95 per cent sure. In {enn(share('<50'))} per cent it is under 50 per cent, and there it gives a list of several proposals instead of an answer.

Most interesting is the comparison with the editors. Among the gaps on Swedish runestones that the editors have filled, the model says at least 95 per cent in {REST_SURE} of {REST_N}. Among those the editors left open, {OPEN_EN}. Where the runologists could not settle the matter, the model thus {'never' if OPEN_SURE == 0 else 'seldom'} claims to know. That is how we want it to work.

In {BT['boundaries']} gaps the words stand without dividers, and the proposal changes if the words are divided as the editors divide them. There the model shows both proposals.

## Why it matters

- **The certainty is visible.** A square bracket shows that something is restored. The model also shows how certain it is and which other possibilities exist, with percentages tested against the answer.
- **The same yardstick for every stone.** All {enn(N_GAPS)} gaps on the runestones are read by the same rules. When the model improves, or a new reading appears, everything can be recalculated.
- **It shows where to look.** On Sö 206 everything depends on whether a remnant of þ or k survives. With 3D scans such places can be examined to half a millimetre.
- **Everything is open.** The code, the tests and the figures are on [GitHub]({GITHUB}), so that anyone can test them again.

Similar tools have been built for Greek inscriptions, where the model Ithaca proposes lost letters (Assael et al. 2022). Vitki's model is built for the runes' own difficulties: the ambiguous spelling, the many names and the traces in the scans. It does not replace the runologist. It gives the runologist a second opinion that can be counted on.

## Before the model is released

Work remains before the model comes out in the app:

- **Traces from the scans.** Today the model only counts traces that someone has entered by hand, but the reader that will take them straight from the 3D scan is well under way. The branches, which tell the runes apart, cannot be trusted in the thinned groove lines – they are now read from the depth image itself instead, weighted by how deeply they are carved. In a first test on {SCN['stones']} scanned stones, where whole words were masked and filled by a model that had never seen the stone, the share right rose from {enn(100 * SCN['utan'], 1)} to {enn(100 * SCN['skanner'], 1)} per cent when the scanner's traces were allowed to help – and with the traces randomly reshuffled among the stone's runes the whole gain vanished. So it is the stone that is being read, not an exercise in numbers. At badly weathered patches the traces can mislead, so the panel shows what the scanner sees – the branches with their carving depth and the possible runes – and the traces only count once the user has confirmed them. A rune with more deep branches than any rune holds, a possible bind rune, proposes nothing at all.
- **Names.** Names are right in {enn(PCT_CLS[2])} per cent of the editors' gaps, against {enn(PCT_CLS[0])} for formula words. Most errors in the documented gaps concern names. The latest version took a step right here: the name builder's proposals used to be cut from the candidate list before they could be weighed, and when they were given a place of their own (textmodel-18) the model won eight masked gaps – among them the names *Guðfastr* and *Þormóðr* – without losing any.
- **More texts from Denmark and Norway**, so that the yardstick is equally fair to every country.
- **Inflection.** The model does not know case and agreement. That concerns only about one word in a hundred in the reading test, however, mostly names in the wrong case. Most of what looks like a wrong form is instead different normalizations in Rundata, such as *sin* and *sinn*.
- **The answer key.** The editors' restoration is itself a judgement. The masking test and the documented gaps have a firmer answer.

When this is in place, the model will come out in the panel *Reading and gaps* on every inscription's page in Vitki.

## The other model: how language-like is a sequence of runes?

Vitki also has a smaller model that measures how much a sequence of runes resembles language. We used it in the article [Interpret, he who can]({SPRAK}) to divide the uninterpreted inscriptions into futhark rows, broken language and sequences that do not resemble language. It too has been improved by tests that first went wrong. Short, broken pieces looked incomprehensible just because they were short, so each inscription is now compared with real texts cut to exactly the same lengths. Danish and Norwegian fragments were at first measured against a mostly Swedish yardstick; now they are compared with texts from the same country. The futhark row on DR EM85;470C, *fuþrkhainsl*, was first judged "not language" because it departs from the usual order; now futhark rows with deviations are recognised too. And Rundata's alternative readings are no longer counted as part of the text. Every change is in the code.

## How we did it

- **Data:** the Scandinavian Runic-text Data Base (Rundata). The model learns from all {enn(D['viking_all'])} Viking-age inscriptions with transliteration and normalization and from the vocabulary of the Edda. The tests and the run are reported for the {enn(D['viking_runestones'])} runestones, fragments and lost stones included. Other stones and loose objects are named separately (utdata/modellartikel/runstenar.py).
- **The reading test:** scripts/runlm_calibrate.py, on {R['inscriptions']} inscriptions where Rundata's words cover the carved text exactly. The material is split into five parts by signum.
- **The masking tests:** scripts/runlm_restore_test.py, {MK['inne i ord']['n'] + MK['helt ord']['n']} hidden gaps on runestones, and with --hard only words outside the 50 most common. The traces in the simulated test are drawn with the typeface Apple Symbols.
- **The editors' gaps:** scripts/runlm_gaps.py. The same word in another inflection or normalization counts as the same word.
- **The documented gaps:** scripts/runlm_documented_test.py. Runes within square brackets are turned into gaps, and the answer is the documented runes and Rundata's normalization.
- **The calibration:** scripts/runlm_gap_calibrate.py, with all three kinds of gaps and cross-validation with whole stones held out.
- **The dating test:** scripts/runlm_dating.py, on {enn(DT['n'])} dated runestones.
- **The run over every stone:** scripts/textmodel_batch.py. The comparison with the editors is made in utdata/modellartikel/batch_status.py.
- **Sö 206 with traces:** the model's answer when only þ, or only k, is allowed in the gap (src/textmodel.py, with traces counted as likely).
- **The images:** Sö 45 in raking light, computed in Vitki. Sö 206 exported at high resolution from Vitki. The illustrations are drawn with utdata/modellartikel/figurer.py.
- **The whole method:** [METHODS.md]({METHODS}), section 8.1.

## About the scans

Sö 45 and Sö 206 were scanned by Laila Kitzler Åhfeldt of the Swedish National Heritage Board within the research project Runristandets dynamik (2009–2014), with a scanner that measures the surface with structured light. Only the carved surfaces were scanned. In 2024 she published the scans of 35 runestones from Södermanland openly on Zenodo, under the licence CC BY 4.0. We use the files *So 45_1_4 thin_closed holes.stl* and *So 206_thin03_closed holes.stl* as published. The image of Sö 45 is computed in Vitki, and the image of Sö 206 was exported at high resolution from Vitki by Viktor Kvant. Her own studies of the scans are Kitzler Åhfeldt 2015 and 2017. We are grateful that the dataset has been made freely available.

## Sources

- Kitzler Åhfeldt, L. 2024. *3D-data Runstenar i Södermanland* [Dataset]. Swedish National Heritage Board. doi:[10.5281/zenodo.11951255]({KA}). CC BY 4.0.
- Kitzler Åhfeldt, L. 2015. Rune Carvers and Local Mobility. *Viking and Medieval Scandinavia* 11, pp. 143–182.
- Kitzler Åhfeldt, L. 2017. *Runristare och mobilitet i Södermanland*. Report. Stockholm: Swedish National Heritage Board.
- The Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Brate, E. & Wessén, E. 1924–36. *Södermanlands runinskrifter* (Sveriges runinskrifter 3). Stockholm: KVHAA. Digitized by the [Swedish National Heritage Board]({SRI_URL}). Sö 45 on pp. 34 f., Sö 206 and Sö 208 on pp. 181 ff.
- Kneser, R. & Ney, H. 1995. Improved backing-off for M-gram language modeling. *Proceedings of the 1995 International Conference on Acoustics, Speech, and Signal Processing* 1, pp. 181–184.
- Bird, S., Klein, E. & Loper, E. 2009. *Natural Language Processing with Python*. Sebastopol: O'Reilly. (NLTK)
- Pedregosa, F. et al. 2011. Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research* 12, pp. 2825–2830.
- Platt, J. 1999. Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods. In: Smola, A. et al. (eds), *Advances in Large Margin Classifiers*. Cambridge, MA: MIT Press, pp. 61–74.
- Assael, Y., Sommerschield, T., Shillingford, B. et al. 2022. Restoring and attributing ancient texts using deep neural networks. *Nature* 603, pp. 280–283.
"""

out = {"slug": "runorna-som-fattas", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en}
path = os.path.join(ROOT, "utdata/blogg/modellartikel.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), len(body_en.split()),
      {"N_WITH": N_WITH, "gaps": N_GAPS, "hours": round(HOURS, 2), "S45": S45, "S206": (S206A, S206B),
       "S211": S211_NAME, "spar": {k: v for k, v in SPAR.items() if k != "loo"}})

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
                 "topic": "Sannolikhetsmodellen|pågående arbete", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
