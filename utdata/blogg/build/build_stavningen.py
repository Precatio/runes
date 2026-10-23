"""Artikeln "Prickarna, åsrunan och tiden" (sv + en): sammanslagningen av utkastet om de stungna runorna (build_prickar.py,
prickar.R) med R-korpusens förändringar över tid (change.json) och seriationen av Upplands stenar (chronology.json),
fingeravtryck 5fdfd1e095bfb6fb. Varje siffra läses ur de filerna och låses med asserts. Omskriven 2026-10-23 efter en
oberoende faktagranskning (38 punkter: måttens enhet, seriationens innehåll, samband mot orsak, tillskrivning).
    cd utdata/blogg/build && ../../../.venv/bin/python build_stavningen.py [--update muGHCwlG7TRFYgp77pAN]
Ersätter det opublicerade utkastet "Prickarna kom med korset" (samma dokument; den gamla texten sparas som FORE-fil)."""
import csv
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from src import commons  # noqa: E402

# The dotted-rune draft's computations, imported without its command line (it would otherwise write to Firestore)
_argv, sys.argv = sys.argv, [sys.argv[0]]
import build_prickar as BP  # noqa: E402
sys.argv = _argv

FP = "5fdfd1e095bfb6fb"
RD = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
CH = json.load(open(os.path.join(RD, "change.json"), encoding="utf-8"))
CR = json.load(open(os.path.join(RD, "chronology.json"), encoding="utf-8"))
F = {f["key"]: f for f in CH["features"]}
V = CR["validation"]
O = BP.O
pc, dec, num = BP.pc, BP.dec, BP.num

# ---- the seriation of Uppland's stones (language, formulas, crosses, short-twig runes, content; no style group) -----------
assert CR["region"] == "U" and (CR["n_stones"], CR["n_dated"]) == (818, 501)
assert (round(V["rho"], 2), V["mae_loo_years"], V["mae_naive_years"]) == (0.54, 21, 25) and V["p"] < 1e-6
RB = V["robustness"]
assert (round(RB["no_cross"]["rho"], 2), round(RB["no_anchor"]["rho"], 2), round(RB["no_changing"]["rho"], 2),
        round(RB["within_district"]["rho"], 2), round(RB["within_carver"]["rho"], 2)) == (0.55, 0.54, 0.54, 0.51, 0.25)
assert "utlandsfärder" in RB["no_anchor"]["label"] and RB["no_anchor"]["n"] == 501
PS = {x["style"]: x for x in CR["per_style"]}
assert (PS["RAK"]["mean_est"], PS["Fp"]["mean_est"], PS["Pr5"]["mean_est"]) == (1050, 1048, 1075)
D1, D2 = CR["corpus_dimensions"][0], CR["corpus_dimensions"][1]
assert set(D1["explained_by"]) == {"geografi", "ristare"} and round(D2["rho_time"], 2) == 0.59
assert "minst 4 drag" in CR["method"] and "kortkvistrunor" in CR["method"] and "Stilgruppen ingick inte" in CR["method"]

# ---- what changed: per STONE, modelled with place and carver constant (change.json) --------------------------------
CHG = {"o_runa": (4, 43, 998, 1085), "stungna": (35, 85, 998, 1115), "stungen_e": (30, 80, 998, 1115),
       "stungen_y": (11, 47, 998, 1115), "ai_alla": (69, 22, 998, 1115)}
for k, (a, b, y0, y1) in CHG.items():
    t = F[k]["time"]
    assert (round(100 * t["curve"][0]["share"]), round(100 * t["curve"][-1]["share"]), t["curve"][0]["year"], t["curve"][-1]["year"]) == (a, b, y0, y1), k
    assert t["halves"]["replicated"] and t["draws"]["n"] == 10 and t["draws"]["share_sig"] >= 0.9, k
assert F["o_runa"]["time"]["n"] == 354 and "o-runa" in F["o_runa"]["yes"]
assert F["ai_alla"]["time"]["draws"]["share_sig"] == 0.9 and F["ai_alla"]["time"]["shape"] == "falls"
assert "något ai-ord" in F["ai_alla"]["label"]
# per WORD the dots change less: raw e-dot share flat by style group, y per word not significant
PR = {x["rune"]: x for x in CH["dotted_robustness"]["per_rune"]}
assert (BP.pc(PR["e"]["by_style"][0]["share"]), BP.pc(PR["e"]["by_style"][-1]["share"]), PR["e"]["p"] < 0.001) == ("26", "22", True)
assert PR["y"]["p"] > 0.4 and PR["y"]["words"] == 138

# ---- the dots by region (prickar.R) ---------------------------------------------------------------------------------
assert (pc(BP.e("Sm")["p"]), pc(BP.e("U")["p"]), pc(BP.e("Sö")["p"]), pc(BP.e("Vs")["p"]), pc(BP.e("Vg")["p"])) == ("42", "17", "19", "30", "29")
assert BP.NORR == (0, 78)
HSM = [r for r in csv.DictReader(open(os.path.join(HERE, "prickar.csv"), encoding="utf-8")) if r["region"] in ("Hs", "M") and int(r["ows_e_exp"]) > 0]
from api.rundata import store  # noqa: E402
_by = {r["signum"]: r for r in store().inscriptions}
STAVLOS = sum(1 for r in HSM if "stavlös" in (_by[r["signum"]].get("rune_types") or "") or "kortkvist" in (_by[r["signum"]].get("rune_types") or ""))
assert (len(HSM), STAVLOS) == (23, 9)
LAT = BP.LAT["all"]
assert (dec(LAT["or"], 2), dec(LAT["lo"], 2), dec(LAT["hi"], 2)) == ("0,46", "0,36", "0,59")
SVU = O["south_vs_u_early"]["all"]
assert (int(round(SVU["or"])), int(SVU["lo"]), int(SVU["hi"])) == (12, 3, 46) and O["south_vs_u_early"]["holds"]
DKP = {p["period"]: p for p in O["dk_periods"]}
assert (pc(DKP["efter Jelling"]["e"]["p"]), pc(DKP["1050–1150"]["e"]["p"]), pc(BP.SG_EARLY[0] / BP.SG_EARLY[1])) == ("11", "44", "33")
CHS = BP.CH
assert (pc(CHS["Vg"]["christian"]["p"]), pc(CHS["Vg"]["other"]["p"]), pc(CHS["Ög"]["christian"]["p"]), pc(CHS["Ög"]["other"]["p"]),
        pc(CHS["Sm"]["christian"]["p"]), pc(CHS["Sm"]["other"]["p"])) == ("46", "21", "32", "5", "48", "44")
CS = BP.CHR["all"]
assert (dec(CS["or"], 1), dec(CS["lo"], 1), dec(CS["hi"], 1)) == ("4,1", "2,0", "8,5") and O["christian_south"]["holds"]
assert (pc(CHS["U"]["christian"]["p"]), pc(CHS["U"]["other"]["p"])) == ("17", "22")
assert not O["christian"]["holds"] and round(O["christian"]["all"]["or"], 2) == 1.37
assert not O["o_u_vs_so"]["holds"] and round(O["o_u_vs_so"]["all"]["or"], 2) == 0.99
assert not O["o_given_dots"]["holds"] and not O["o_u_time"]["holds"]
assert (BP.N_SE, BP.N_DK, BP.W_SE) == (1276, 141, 3165)

# ---- photos -----------------------------------------------------------------------------------------------------------
FILES = commons.wikidata_files(["Ög 133", "U 279"])
INFO = commons.commons_info([FILES[s] for s in FILES])
CREDIT = {"Ög 133": ("Marianne58", "CC BY-SA 3.0"), "U 279": ("Ingman No. 2", "CC BY-SA 3.0")}


def photo(signum: str, text: str, lang: str = "sv") -> str:
    img = {**INFO[FILES[signum]], "signum": signum}
    assert (img["author"], img["licence"]) == CREDIT[signum], (signum, img["author"], img["licence"])
    cap = commons.caption(img, lang)
    word = "Foto" if lang == "sv" else "Photo"
    assert cap.startswith(f"{signum}. {word}: ")
    alt = f"Runstenen {signum}" if lang == "sv" else f"The runestone {signum}"
    return f"![{alt}]({img['thumb']})\n{text} {word}: {cap[len(signum) + len(word) + 4:]}"


PH_OG = photo("Ög 133", "Ög 133 vid Häggestad i Heda socken, Östergötland. I fyra ord har ristaren satt en prick på i-runan: läs e, inte i.")
PH_U = photo("U 279", "U 279 vid Skälby i Hammarby socken, Uppland, ristad av Öpir. Åsrunan står för o, men e-orden får ingen prick.")
PH_OG_EN = photo("Ög 133", "Ög 133 at Häggestad, Heda parish, Östergötland. In four words the carver has put a dot on the i-rune: read e, not i.", "en")
PH_U_EN = photo("U 279", "U 279 at Skälby, Hammarby parish, Uppland, carved by Öpir. The ós-rune stands for o, but the e-words get no dot.", "en")

LAB = {"o_runa": ("Stenar med o-ljud där åsrunan används", "Stones with an o-sound where the ós-rune is used"),
       "stungna": ("Stenar med någon stungen runa", "Stones with any dotted rune"),
       "stungen_e": ("Stenar med minst en stungen i (e)", "Stones with at least one dotted i (e)"),
       "stungen_y": ("Stenar med minst en stungen u (y)", "Stones with at least one dotted u (y)"),
       "ai_alla": ("Stenar som skriver något ai-ord med enkel vokal (stin)", "Stones that write some ai-word with a single vowel (stin)")}


def chart_change(lang: str) -> str:
    sv = lang == "sv"
    rows = [":::chart Fem drag, räknat per sten: omkring år 1000 och omkring 1100" if sv else
            ":::chart Five features, counted per stone: around the year 1000 and around 1100"]
    for k, (a, b, y0, y1) in CHG.items():
        rows.append(f"# {LAB[k][0 if sv else 1]}")
        rows.append(f"{'omkring år 1000' if sv else 'around 1000'} | {a} | {'skattat' if sv else 'estimated'}")
        rows.append(f"+{'omkring' if sv else 'around'} {y1} | {b} | {'skattat' if sv else 'estimated'}"
                    + ((", mönster att pröva" if sv else ", pattern to test") if k == "ai_alla" else ""))
    rows.append("Källa: Vitkis analys i R av Samnordisk runtextdatabas, daterade runstenar i alla landskap; andelar av stenarna, "
                "skattade med plats och ristare konstanta. Åsrunans kurva slutar 1085, eftersom de senaste stenarna med o-ljud är för få." if sv else
                "Source: Vitki's analysis in R of the Scandinavian Runic-text Database, dated runestones in all provinces; shares of the "
                "stones, estimated with place and carver held constant. The ós-rune curve ends in 1085, since the latest stones with an o-sound are too few.")
    return "\n".join(rows) + "\n:::"


CHART_CHANGE, CHART_CHANGE_EN = chart_change("sv"), chart_change("en")
o = CHG["o_runa"]; s = CHG["stungna"]; ai = CHG["ai_alla"]  # noqa: E702
E26, E22 = pc(PR["e"]["by_style"][0]["share"]), pc(PR["e"]["by_style"][-1]["share"])

title = "Prickarna, åsrunan och tiden"
summary = ("Runstenar dateras efter ornamentikens stil, men på ett fragment finns ofta ingen ornamentik kvar. Kan inskriften själv "
           "berätta när den ristades? I Uppland ordnar inskrifternas språk, formler och innehåll stenarna delvis som stilen gör – en "
           "grov ordning, inte en exakt klocka. Och förändringarna gick inte i takt överallt: i Götaland hänger prickarna i runorna "
           "ihop med korset, i Uppland gör de det inte.")
title_en = "The Dots, the Ós-rune and Time"
summary_en = ("Runestones are dated by the style of their ornament, but a fragment often has no ornament left. Can the inscription "
              "itself tell when it was carved? In Uppland the inscriptions' language, formulas and content order the stones partly as "
              "the style does – a rough order, not a precise clock. And the changes did not keep pace everywhere: in Götaland the dots "
              "in the runes go with the cross, in Uppland they do not.")

body = f"""Den som står framför ett fragment av en runsten har svårt att säga hur gammal den är. Runstenarna dateras i regel efter ornamentiken, efter hur runormens huvud och svans är tecknade. Den metoden, Anne-Sofie Gräslunds stilgrupper, är det bästa vi har. Men på ett fragment finns ofta ingen slinga kvar, och då får stenen ingen stilgrupp. Frågan i den här artikeln är om inskriften själv kan berätta något om tiden, och om förändringarna gick i samma takt överallt.

## Sexton runor för trettio ljud

Vikingatidens runrad, den yngre futharken, hade bara sexton tecken. Språket hade omkring dubbelt så många ljud. i-runan fick stå för i och e, a-runan för a och æ, u-runan för u, o, y och ø, k-runan för både k och g och t-runan för både t och d. Den som läste fick gissa ur sammanhanget.

Under 1000-talet prövade ristarna två sätt att få runorna att räcka. Det ena var att sätta en prick i en runa och göra en ny: *stungna runor*, som ᛂ för e, ᚤ för y, ᚵ för g och ᛑ för d. Det andra var att ge en gammal runa ett nytt ljud: åsrunan ᚬ, som tidigare stod för ett nasalt a, fick betyda o. Båda reformerna har fått egna avhandlingar, om de stungna runorna av Svante Lagman och om åsrunan av Henrik Williams, båda 1990. Mönster som de redan har sett ska tillskrivas dem; det vi lägger till är mätningar gjorda på samma sätt för hela korpusen.

{PH_OG}

## Det som ändrades

Vi följde fem drag genom alla daterade runstenar i korpusen. Varje drag räknas per sten: har stenen draget minst en gång eller inte. För att en ristare med många stenar inte ska väga som många, och för att olika trakter inte ska blandas ihop med olika tider, skattades andelarna med plats och ristare konstanta.

{CHART_CHANGE}

Bland stenarna med ord som har o-ljud går andelen som använder åsrunan minst en gång från {o[0]} procent omkring år 1000 till {o[1]} procent omkring {o[3]}. Andelen stenar med någon stungen runa går från {s[0]} till {s[1]} procent. Alla fem drag håller i båda halvorna av korpusen – vi delade stenarna i två grupper, socken för socken, och gjorde om analysen i varje grupp – och i minst nio av tio omräkningar där varje stens årtal drogs slumpvis inom stilgruppens intervall.

Att räkna per sten gynnar långa texter, som har fler chanser att få en prick. Räknat ord för ord är prickarna betydligt ovanligare och förändringen mindre: av alla e-ord har {E26} procent prick på de tidigaste stenarna och {E22} procent på de senaste. Med plats och ristare konstanta ökar prickarna ord för ord ändå, men för stungen u är ökningen per ord inte säker.

Det femte draget, att stenen skriver något ord som *stæinn* med enkel vokal (*stin*), går från {ai[0]} till {ai[1]} procent av stenarna. Det går i motsatt riktning mot den väntade ljudutvecklingen, där den enkla vokalen så småningom vann i fornsvenskan, och det försvagas när de tidigaste och senaste stilgrupperna eller ristarna räknas bort. Vi läser det därför som ett mönster att pröva, och troligen säger det mer om skrivvanor än om uttal.

## En grov ordning, inte en exakt klocka

Om inskrifterna ändrades i bestämda riktningar borde de gå att läsa baklänges: stenar med många nya drag borde vara sena. Vi prövade det på Upplands runstenar, det material som stilkronologin själv bygger på. En korrespondensanalys ordnade {CR['n_stones']} stenar efter drag i språk, formler, kors, kortkvistrunor och innehåll – utan stilgruppen och utan ornamentiken. Sedan jämförde vi den ordningen med stilgruppernas årtal för de {CR['n_dated']} stenar som har en stilgrupp.

De två ordningarna stämmer ganska väl överens. Rangkorrelationen är {dec(V['rho'], 2)}, där 1 skulle betyda samma ordning och 0 ingen likhet alls. Ett så tydligt samband skulle uppstå av en slump i färre än ett fall på en miljon. Det beror varken på enskilda drag eller på geografin:

- **utan korsen** är korrelationen {dec(RB['no_cross']['rho'], 2)}
- **utan utlandsfärderna som drag** – de som knyter Ingvars- och Englandsstenarna till historiskt daterbara händelser – {dec(RB['no_anchor']['rho'], 2)}
- **utan de föränderliga stavningsdragen ovan** – stungna runor, åsrunan och den enkla vokalen – {dec(RB['no_changing']['rho'], 2)}
- **inom samma härad** {dec(RB['within_district']['rho'], 2)}

Det tredje är värt att stanna vid. Ordningen blir lika god utan stavningsdragen. Det är alltså inte prickarna och åsrunan som bär den, utan formlerna och innehållet.

Inom en och samma ristares stenar är korrelationen bara {dec(RB['within_carver']['rho'], 2)}. Ordningen skiljer alltså mest mellan ristare. En del av sambandet kan därför vara ristarnas olika vanor snarare än tiden, och en enskild ristares bana är för kort för att märkas.

Som klocka är den grov. När vi lät analysen gissa årtalet för en sten vars årtal den inte fick se, blev felet i genomsnitt {V['mae_loo_years']} år. Att gissa samma år, medelåret, för alla stenar ger {V['mae_naive_years']}. Båda felen är mätta mot stilgruppens mittår, inte mot stenens verkliga årtal. För grupper av stenar skiljer ordningen tidigt från sent; för en enskild sten är vinsten liten, och de tidigaste stilgrupperna RAK och Fp skiljer den inte åt. Stenar med färre än fyra läsbara drag kunde inte tas med, och det är just många fragment.

Ordningen har vi bara prövat i Uppland. I hela korpusen ordnas stenarna i första hand efter ristare och trakt, och tiden syns först i andra hand.

## Förändringarna gick inte i takt

Prickarna är det tydligaste exemplet. Här räknade vi ord för ord: för varje ord med ett e-ljud frågade vi om ristaren skrev det med den stungna runan. Ord där e ingår i diftongen ei, som *stæinn*, räknas inte. Måttet gäller {num(BP.N_SE)} svenska och {num(BP.N_DK)} danska runstenar.

{BP.chart_provinces('sv')}

I Småland och på Gotland skrivs fyra av tio e-ord med prick ({pc(BP.e('Sm')['p'])} procent). I Uppland och Södermanland är det färre än två av tio ({pc(BP.e('U')['p'])} och {pc(BP.e('Sö')['p'])} procent). Västmanland, med få stenar, ligger något högre ({pc(BP.e('Vs')['p'])} procent). I Hälsingland och Medelpad har inte ett enda av {BP.NORR[1]} e-ord fått sin prick, men där är {STAVLOS} av de {len(HSM)} stenarna helt eller delvis ristade med stavlösa eller kortkvistiga runor, där prickar knappt förekommer.

Lutningen från söder till norr håller med tiden och ristaren konstanta: för varje tiotal mil längre norrut sjunker oddsen för en prick till knappt hälften (oddskvoten är {dec(LAT['or'], 2)}, med ett osäkerhetsintervall från {dec(LAT['lo'], 2)} till {dec(LAT['hi'], 2)}). Bland de äldsta stenarna, stilgrupperna RAK och Fp från omkring 980–1050, är oddsen i södra Götaland – Småland, Öland och Västergötland – omkring {int(round(SVU['or']))} gånger så höga som i Uppland. Hur mycket är osäkert: någonstans mellan {int(SVU['lo'])} och {int(SVU['hi'])} gånger.

Pricken var inte vanligare i Danmark – tvärtom. På de danska stenarna efter Jelling, omkring 1000–1050, har {pc(DKP['efter Jelling']['e']['p'])} procent av e-orden prick, mot {pc(BP.SG_EARLY[0] / BP.SG_EARLY[1])} procent på södra Götalands tidiga stenar. Först efter 1050, mest på Bornholm, blir prickarna vanliga där ({pc(DKP['1050–1150']['e']['p'])} procent). Var bruket uppstod säger siffrorna inget om.

I Götaland hänger pricken ihop med korset. Där har stenar med kors eller bön fler prickar än andra stenar från samma landskap och tid: i Västergötland {pc(CHS['Vg']['christian']['p'])} mot {pc(CHS['Vg']['other']['p'])} procent, i Östergötland {pc(CHS['Ög']['christian']['p'])} mot {pc(CHS['Ög']['other']['p'])}. I Småland, där prickarna är vanliga på alla slags stenar, är skillnaden liten ({pc(CHS['Sm']['christian']['p'])} mot {pc(CHS['Sm']['other']['p'])} procent). Sammantaget i Götaland är oddsen för en prick omkring fyra gånger så höga på en kristen sten (oddskvoten {dec(CS['or'], 1)}, med ett osäkerhetsintervall från {dec(CS['lo'], 1)} till {dec(CS['hi'], 1)}), och sambandet håller i båda halvorna. I Uppland syns inget sådant samband ({pc(CHS['U']['christian']['p'])} mot {pc(CHS['U']['other']['p'])} procent), men skillnaden mellan landskapen har vi inte prövat för sig, och räknat i alla landskap tillsammans är sambandet inte säkert.

{PH_U}

I Mälardalen prickades e-orden sällan, och där blev åsrunan för o vanlig på de sena stenarna. Om ristarna valde den *i stället för* prickar kan vi inte säga: stenar med prickar har inte mer sällan åsruna, och Uppland skiljer sig inte från Södermanland i hur ofta den används. I hela korpusen ökar åsrunan säkert, i båda halvorna. I Uppland för sig är ökningen lika tydlig att se men klarar inte kravet i den ena halvan, så för Uppland ska den läsas som en beskrivning, inte som ett fynd.

## Vad det kan betyda

Att pricken har förebild i det latinska alfabetet, som skiljer e från i, y från u, g från k och d från t, är en gammal tanke i runforskningen. Det nya här är att pricken i Götaland hänger ihop med kristna tecken på samma sten, mätt på samma sätt för alla landskap. Vår tolkning är att de stungna runorna där är ett spår av latinsk skrift i tidiga kristna miljöer, och att de bara långsamt nådde ristarna i Mälardalen, som under tiden fick ett liknande problem löst – o mot u i stället för e mot i – på sitt eget sätt med åsrunan.

Andra förklaringar är möjliga. En lokal ristarskola kan ha prickat och huggit kors utan att det ena berodde på det andra. Uttalet kan ha skilt sig, så att e och i hölls mer isär i söder. Och stilgruppernas årtal bygger på uppländska stenar, så götaländska stenar i samma stilgrupp kan vara något yngre. Det påverkar inte jämförelsen mellan kristna och andra stenar, som görs inom samma landskap och stilgrupp. Däremot kan det överdriva hur tidigt södra Götaland var ute, och jämförelsen med Danmark, där dateringen bygger på ett annat system.

För den som vill datera ett fragment betyder det två saker. Inskriften kan ge en grov fingervisning om tidigt eller sent, men inte ett årtal. Och samma drag betyder olika saker på olika håll: en prick på en götaländsk sten säger mer om korset än om årtalet.

:::box Det viktigaste i korthet
- Under 1000-talet blev åsrunan för o och de stungna runorna allt vanligare på stenarna, också när plats och ristare hålls konstanta. Räknat ord för ord är prickarna ovanligare och förändringen mindre.
- I Uppland räcker inskrifterna – språk, formler och innehåll, utan stilgrupp – för att ordna stenarna ungefär som stilkronologin gör. Det stöder stilkronologins ordning utan att bygga på ornamentiken, men eftersom både stil och språk följer ristaren är stödet inte helt oberoende, och för en enskild sten är det en grov fingervisning.
- Förändringarna gick inte i takt. Prickarna var vanligast i södra Götaland och sällsynta både i Danmark och i Mälardalen.
- Att pricken följer korset i Götaland är ett mätt samband; att det beror på latinsk skrift från kyrkan är vår tolkning, inte belagt.
:::

:::box Så räknade vi
Förändringarna skattades i R för alla daterade runstenar, per sten, med plats och ristare konstanta (en slumpeffekt per ristare, eller per socken när ristaren är okänd). Enligt projektets regel räknas ett drag som förändrat när det klarar justeringen för många prövningar, håller i båda halvorna av korpusen och i minst sju av tio omräkningar med årtalen dragna inom stilgruppernas intervall; den enkla vokalen klarar det men redovisas som mönster att pröva av skälen ovan. Seriationen är en korrespondensanalys av Upplands stenar med minst fyra drag (språkdrag, formler, kors, kortkvistrunor och innehållskategorier), utan stilgruppen, prövad med Spearmans rangkorrelation mot stilgruppens mittår och med korsvalidering för felet i år. Prickarna räknades ord för ord mot den fornvästnordiska normalformen, samma för svenska och danska stenar. Stilgruppernas årtal är uppskattningar efter Gräslund, och ett kors eller en bön är ett grovt mått på om en sten är kristen.
:::

## Källor

- Samnordisk runtextdatabas, version 3.1 (ODbL).
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. København: Museum Tusculanum Press, s. 117–139.
- Lagman, S. 1990. *De stungna runorna. Användning och ljudvärden i runsvenska steninskrifter*. Runrön 4. Uppsala.
- Williams, H. 1990. *Åsrunan. Användning och ljudvärde i runsvenska steninskrifter*. Runrön 3. Uppsala.
- Foton: se bildtexterna."""

body_en = f"""Anyone standing in front of a fragment of a runestone will find it hard to say how old it is. Runestones are usually dated by their ornament, by how the head and tail of the rune animal are drawn. That method, Anne-Sofie Gräslund's style groups, is the best we have. But a fragment often has no band left, and then the stone gets no style group. The question in this article is whether the inscription itself can tell us something about time, and whether the changes kept the same pace everywhere.

## Sixteen runes for thirty sounds

The runic alphabet of the Viking Age, the younger futhark, had only sixteen signs. The language had about twice as many sounds. The i-rune stood for i and e, the a-rune for a and æ, the u-rune for u, o, y and ø, the k-rune for both k and g and the t-rune for both t and d. The reader had to guess from the context.

During the eleventh century carvers tried two ways of making the runes suffice. One was to put a dot in a rune and make a new one: *dotted runes*, such as ᛂ for e, ᚤ for y, ᚵ for g and ᛑ for d. The other was to give an old rune a new sound: the ós-rune ᚬ, which had stood for a nasal a, came to mean o. Both reforms have their own dissertations, on the dotted runes by Svante Lagman and on the ós-rune by Henrik Williams, both 1990. Patterns they have already seen should be credited to them; what we add are measurements made the same way for the whole corpus.

{PH_OG_EN}

## What changed

We followed five features through every dated runestone in the corpus. Each feature is counted per stone: does the stone have it at least once or not. So that a carver with many stones does not weigh as many, and so that different districts are not mistaken for different times, the shares were estimated with place and carver held constant.

{CHART_CHANGE_EN}

Among the stones with words that have an o-sound, the share that uses the ós-rune at least once goes from {o[0]} per cent around the year 1000 to {o[1]} per cent around {o[3]}. The share of stones with any dotted rune goes from {s[0]} to {s[1]} per cent. All five features hold in both halves of the corpus – we split the stones into two groups, parish by parish, and repeated the analysis in each – and in at least nine of ten recalculations where each stone's year was drawn at random within its style group's range.

Counting per stone favours long texts, which have more chances of a dot. Counted word by word, the dots are much rarer and the change smaller: of all e-words, {E26} per cent have a dot on the earliest stones and {E22} per cent on the latest. With place and carver held constant the dots do increase word by word, but for the dotted u the increase per word is not certain.

The fifth feature, that the stone writes some word like *stæinn* with a single vowel (*stin*), goes from {ai[0]} to {ai[1]} per cent of the stones. It runs opposite to the expected sound change, in which the single vowel eventually won in Old Swedish, and it weakens when the earliest and latest style groups or the carvers are taken out. We therefore read it as a pattern to test, and it probably says more about writing habits than about pronunciation.

## A rough order, not a precise clock

If the inscriptions changed in definite directions, it should be possible to read them backwards: stones with many new features should be late. We tested that on the runestones of Uppland, the material the style chronology itself is built on. A correspondence analysis ordered {CR['n_stones']} stones by features of language, formulas, crosses, short-twig runes and content – without the style group and without the ornament. We then compared that order with the style groups' years for the {CR['n_dated']} stones that have a style group.

The two orders agree fairly well. The rank correlation is {dec(V['rho'], 2, 'en')}, where 1 would mean the same order and 0 no likeness at all. A link this clear would arise by chance in fewer than one case in a million. It depends neither on single features nor on geography:

- **without the crosses** the correlation is {dec(RB['no_cross']['rho'], 2, 'en')}
- **without journeys abroad as a feature** – those that tie the Ingvar and England stones to historically datable events – {dec(RB['no_anchor']['rho'], 2, 'en')}
- **without the changing spelling features above** – dotted runes, the ós-rune and the single vowel – {dec(RB['no_changing']['rho'], 2, 'en')}
- **within the same hundred** (district) {dec(RB['within_district']['rho'], 2, 'en')}

The third deserves a pause. The order is just as good without the spelling features. So it is not the dots and the ós-rune that carry it, but the formulas and the content.

Within one and the same carver's stones the correlation is only {dec(RB['within_carver']['rho'], 2, 'en')}. The order thus mostly separates carvers. Part of the link may therefore be the carvers' different habits rather than time, and a single carver's career is too short to show.

As a clock it is rough. When we let the analysis guess the year of a stone whose date it was not shown, the error was {V['mae_loo_years']} years on average. Guessing the same year, the average, for every stone gives {V['mae_naive_years']}. Both errors are measured against the style group's mid-year, not the stone's true date. For groups of stones the order tells early from late; for a single stone the gain is small, and it does not separate the earliest style groups, RAK and Fp. Stones with fewer than four readable features could not be included, and many fragments are just such stones.

We have tested the order only in Uppland. In the corpus as a whole the stones are ordered first by carver and district, and time comes second.

## The changes did not keep pace

The dots are the clearest example. Here we counted word by word: for each word with an e-sound we asked whether the carver wrote it with the dotted rune. Words where e is part of the diphthong ei, like *stæinn*, are not counted. The measure covers {num(BP.N_SE, 'en')} Swedish and {num(BP.N_DK, 'en')} Danish runestones.

{BP.chart_provinces('en')}

In Småland and on Gotland four in ten e-words are written with a dot ({pc(BP.e('Sm')['p'])} per cent). In Uppland and Södermanland it is fewer than two in ten ({pc(BP.e('U')['p'])} and {pc(BP.e('Sö')['p'])} per cent). Västmanland, with few stones, lies somewhat higher ({pc(BP.e('Vs')['p'])} per cent). In Hälsingland and Medelpad not one of {BP.NORR[1]} e-words got its dot, but there {STAVLOS} of the {len(HSM)} stones are wholly or partly carved in staveless or short-twig runes, where dots hardly occur.

The slope from south to north holds with time and carver held constant: for every hundred kilometres further north, the odds of a dot fall to just under half (the odds ratio is {dec(LAT['or'], 2, 'en')}, with an uncertainty interval from {dec(LAT['lo'], 2, 'en')} to {dec(LAT['hi'], 2, 'en')}). Among the oldest stones, the style groups RAK and Fp from about 980–1050, the odds in southern Götaland – Småland, Öland and Västergötland – are about {int(round(SVU['or']))} times as high as in Uppland. How much is uncertain: somewhere between {int(SVU['lo'])} and {int(SVU['hi'])} times.

The dot was not more common in Denmark – the reverse. On the Danish stones after Jelling, about 1000–1050, {pc(DKP['efter Jelling']['e']['p'])} per cent of the e-words have a dot, against {pc(BP.SG_EARLY[0] / BP.SG_EARLY[1])} per cent on southern Götaland's early stones. Only after 1050, mostly on Bornholm, do dots become common there ({pc(DKP['1050–1150']['e']['p'])} per cent). Where the practice arose, the figures do not say.

In Götaland the dot goes with the cross. There, stones with a cross or a prayer have more dots than other stones of the same province and time: in Västergötland {pc(CHS['Vg']['christian']['p'])} against {pc(CHS['Vg']['other']['p'])} per cent, in Östergötland {pc(CHS['Ög']['christian']['p'])} against {pc(CHS['Ög']['other']['p'])}. In Småland, where dots are common on all kinds of stones, the difference is small ({pc(CHS['Sm']['christian']['p'])} against {pc(CHS['Sm']['other']['p'])} per cent). Taken together in Götaland the odds of a dot are about four times as high on a Christian stone (the odds ratio {dec(CS['or'], 1, 'en')}, with an uncertainty interval from {dec(CS['lo'], 1, 'en')} to {dec(CS['hi'], 1, 'en')}), and the link holds in both halves. In Uppland no such link shows ({pc(CHS['U']['christian']['p'])} against {pc(CHS['U']['other']['p'])} per cent), but we have not tested the difference between the provinces on its own, and counted across all provinces together the link is not certain.

{PH_U_EN}

In the Mälaren valley the e-words were seldom dotted, and there the ós-rune for o became common on the late stones. Whether the carvers chose it *instead of* dots we cannot say: stones with dots are not less likely to have the ós-rune, and Uppland does not differ from Södermanland in how often it is used. In the corpus as a whole the ós-rune increases with certainty, in both halves. In Uppland on its own the increase is just as plain to see but does not meet the requirement in one half, so for Uppland it should be read as a description, not a finding.

## What it may mean

That the dot is modelled on the Latin alphabet, which tells e from i, y from u, g from k and d from t, is an old idea in runology. What is new here is that in Götaland the dot goes with Christian marks on the same stone, measured the same way for every province. Our interpretation is that the dotted runes there are a trace of Latin writing in early Christian milieus, and that they only slowly reached the carvers of the Mälaren valley, who in the meantime solved a similar problem – o against u rather than e against i – in their own way, with the ós-rune.

Other explanations are possible. A local school of carvers may have dotted and cut crosses without the one depending on the other. Pronunciation may have differed, so that e and i were kept more apart in the south. And the style groups' years are built on Uppland stones, so stones of the same style group in Götaland may be somewhat younger. That does not affect the comparison between Christian and other stones, which is made within the same province and style group. It may, however, exaggerate how early southern Götaland was, and the comparison with Denmark, where the dating rests on another system.

For anyone who wants to date a fragment this means two things. The inscription can give a rough indication of early or late, but not a year. And the same feature means different things in different places: a dot on a stone in Götaland says more about the cross than about the year.

:::box The essentials in brief
- During the eleventh century the ós-rune for o and the dotted runes became ever more common on the stones, also with place and carver held constant. Counted word by word, the dots are rarer and the change smaller.
- In Uppland the inscriptions – language, formulas and content, without the style group – are enough to order the stones roughly as the style chronology does. That supports the chronology's order without relying on the ornament, but since both style and language follow the carver the support is not fully independent, and for a single stone it is a rough indication.
- The changes did not keep pace. The dots were most common in southern Götaland and rare both in Denmark and in the Mälaren valley.
- That the dot goes with the cross in Götaland is a measured association; that it comes from Latin writing brought by the church is our interpretation, not established.
:::

:::box How we counted
The changes were estimated in R for all dated runestones, per stone, with place and carver held constant (a random effect per carver, or per parish when the carver is unknown). By the project's rule a feature counts as changed when it survives the adjustment for many tests, holds in both halves of the corpus and in at least seven of ten recalculations with the years drawn within the style groups' ranges; the single vowel passes but is reported as a pattern to test for the reasons above. The seriation is a correspondence analysis of Uppland's stones with at least four features (language features, formulas, crosses, short-twig runes and content categories), without the style group, tested with Spearman's rank correlation against the style group's mid-year and with cross-validation for the error in years. The dots were counted word by word against the standard Old West Norse form, the same for Swedish and Danish stones. The style groups' years are estimates after Gräslund, and a cross or a prayer is a rough measure of whether a stone is Christian.
:::

## Sources

- Scandinavian Runic-text Database, version 3.1 (ODbL).
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.
- Lagman, S. 1990. *De stungna runorna. Användning och ljudvärden i runsvenska steninskrifter*. Runrön 4. Uppsala.
- Williams, H. 1990. *Åsrunan. Användning och ljudvärde i runsvenska steninskrifter*. Runrön 3. Uppsala.
- Photos: see the captions."""

# the province chart is the draft's; its database name is unified here for the English text
body_en = body_en.replace("Scandinavian Runic-text Data Base", "Scandinavian Runic-text Database")
# the draft's province chart claims a strict latitude order, but Öland (south of Småland) comes after it
body = body.replace("ordnade efter breddgrad med det nordligaste längst ned", "ordnade ungefär från söder till norr")
body_en = body_en.replace("ordered by latitude with the northernmost at the bottom", "ordered roughly from south to north")
assert "breddgrad" not in body and "by latitude" not in body_en
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M)
assert body.count("## ") == body_en.count("## ") and not re.search(r"\b(jag|mig|min)\b", body, re.I)
assert "Data Base" not in body_en
out = {"slug": "prickarna-asrunan-och-tiden", "title": title, "summary": summary, "body": body, "title_en": title_en,
       "summary_en": summary_en, "body_en": body_en, "labels": ["Forskning", "Språk och stavning", "Datering och stil"],
       "topic": "Förändring|stungna"}
path = os.path.join(ROOT, "utdata", "blogg", "stavningen.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord sv,", len(body_en.split()), "ord en")

if "--update" in sys.argv:
    from api.routers import blog
    doc = sys.argv[sys.argv.index("--update") + 1]
    ref = blog.firestore().collection(blog.COLLECTION).document(doc)
    old = ref.get().to_dict()
    assert old and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
    assert old.get("slug") in ("prickarna-kom-med-korset", out["slug"]), old.get("slug")
    json.dump({k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in old.items()},
              open(os.path.join(ROOT, f"utdata/blogg/{old['slug']}.FORE.json"), "w"), ensure_ascii=False, indent=1, default=str)
    ref.set({**out, "updatedAt": dt.datetime.now(dt.timezone.utc)}, merge=True)
    blog._forget()
    print("uppdaterat utkast:", doc)
