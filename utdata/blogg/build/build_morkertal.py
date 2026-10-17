"""Bygger artikeln "Stilgruppernas mörkertal" (sv + en) ur utdata/sprakprov/morkertal.json (+ stilgrupper.json via
dess base-fält). Alla tal läses ur datafilen och grindas med asserts; ingen siffra skrivs för hand i texten.
    cd utdata/blogg/build && PYTHONDONTWRITEBYTECODE=1 ../../../.venv/bin/python build_morkertal.py [--write]
--write sparar ett NYTT opublicerat utkast i Firestore (vägrar om adressen redan används)."""
import datetime as dt
import json
import os
import sys

ROOT = "/Volumes/2TB/Antigrvity/Runes/aagaard-research"
sys.path.insert(0, ROOT)

D = json.load(open(os.path.join(ROOT, "utdata", "sprakprov", "morkertal.json")))
B = D["base"]


def svn(x):
    return f"{x:,}".replace(",", " ")


def pr(x):
    return int(100 * x + 0.5)


def sv1(x):
    return f"{100 * x:.1f}".replace(".", ",")


def en1(x):
    return f"{100 * x:.1f}"


# ---- the numbers, gated -------------------------------------------------------------------------------------------
RS = B["runestones"]
DARK = RS["n"] - RS["with_style"]
assert RS["n"] == 2633 and RS["with_style"] == 1701 and 900 < DARK < 1000
PROV = B["se_runestones_by_province"]
assert pr(PROV["Vg"]["share"]) == 88 and pr(PROV["Öl"]["share"]) == 27
LOSTC, WHOLEC = B["se_runestones_lost"], B["se_runestones_whole"]
assert pr(LOSTC["share"]) == 54 and pr(WHOLEC["share"]) == 83 and D["style_damage_p"] < 1e-40
IRS, URS = B["interpreted_runestones"], B["uninterpreted_runestones"]
assert pr(IRS["share"]) == 73 and pr(URS["share"]) == 46
CTRY = B["runestones_by_country"]
SG = D["signing"]
SW, UW = SG["styled_whole"], SG["unstyled_whole"]
assert (SW["n"], SW["signed"], UW["n"], UW["signed"]) == (642, 102, 132, 8)
assert SG["p_fisher_whole"] < 0.005 and SG["p_binom_vs_mix"] < 0.001 and 0.15 < SG["expected_rate_unstyled"] < 0.17
RBS = SG["rate_by_style_whole"]
RAKR = D["rak_of_styled"]
assert (RAKR["DR"]["rak"], RAKR["DR"]["styled"]) == (182, 192) and (RAKR["Vg"]["rak"], RAKR["Vg"]["styled"]) == (81, 115)
assert RAKR["N"]["rak"] == RAKR["N"]["styled"] == 33 and RAKR["U"]["rak"] == 50
SER = D["seriation"]
SV_ = SER["validation"]
assert SER["n_unstyled_scored"] == 317 and SER["u_unstyled_total"] == 374 and SV_["rho"] == 0.543
assert SV_["mae_loo_years"] == 21 and SV_["mae_naive_years"] == 25
DM = D["dating_model"]
assert DM["epoch"] == 0.585 and DM["near"] == 0.948
UNC = D["uncertain_styles"]
assert 50 < UNC < 100

GITHUB = "https://github.com/Precatio/runes"
SPRAK = "/artiklar/hur-spraklik-ar-en-runfoljd"

row_sv = [(s, RBS[s]) for s in ("RAK", "Fp", "KB", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5") if RBS[s]["n"] >= 17]
chart_sign_sv = "\n".join(f"{s} | {sv1(v['rate'])} | {v['signed'] if 'signed' in v else round(v['rate'] * v['n'])} av {v['n']} hela stenar"
                          for s, v in row_sv)
chart_sign_en = "\n".join(f"{s} | {en1(v['rate'])} | {round(v['rate'] * v['n'])} of {v['n']} whole stones"
                          for s, v in row_sv)

title = "Stilgruppernas mörkertal"
title_en = "The style groups' dark number"

summary = (f"Runstenarna dateras med sina ornament, men mer än var tredje runsten saknar stilgrupp i Samnordisk "
           f"runtextdatabas – och bortfallet är inte slumpmässigt. De skadade, de otolkade och stenarna utanför "
           f"Mälardalen och Västergötland försvinner oftast. Vi visar att de osynliga stenarna inte heller beter sig "
           f"som de synliga, att kategorin RAK gör hela bestånd tidiga per definition, och hur mörkertalet kan tändas.")
summary_en = ("Runestones are dated by their ornament, yet more than a third of all runestones lack a style group in "
              "the Scandinavian Runic-text Database – and the loss is not random. The damaged, the uninterpreted and "
              "the stones outside the Mälaren valley and Västergötland drop out most often. We show that the invisible "
              "stones do not behave like the visible ones either, that the category RAK makes whole corpora early by "
              "definition, and how the dark number can be lit.")

body = f"""När Anne-Sofie Gräslund delade in runstenarna efter runbandens och djurornamentikens form fick forskningen sitt kanske vassaste verktyg: en runsten kan dateras på några decenniers när, utan ett enda årtal i texten. Stilgrupperna bär i dag stora delar av vad vi tror oss veta om vikingatidens slut – när ristarna började signera, när bönerna kom, hur korset spred sig.

Men ett verktyg ser bara det som ligger i dess ljus. Den här artikeln ställer frågan som sällan ställs: vilka runstenar ser stilgrupperna – och vilka står i mörkret? Svaret är att mer än var tredje runsten saknar stilgrupp i Samnordisk runtextdatabas, och att bortfallet inte är slumpmässigt. De stenar som saknas är systematiskt de skadade, de otolkade och de perifera. Och de beter sig inte som de synliga.

:::box I korthet
- Av {svn(RS['n'])} vikingatida runstenar har {svn(RS['with_style'])} en stilgrupp i Samnordisk runtextdatabas. Drygt nio hundra, {pr(1 - RS['share'])} procent, står utanför.
- Bortfallet följer skadan: en hel svensk runsten har stilgrupp i {pr(WHOLEC['share'])} fall av hundra, en med förlorade runor i {pr(LOSTC['share'])}. Att en så stor skillnad skulle uppstå av slump är i praktiken uteslutet.
- Det följer också tolkningen och geografin: de otolkade runstenarna har stilgrupp i {pr(URS['share'])} fall av hundra mot de tolkades {pr(IRS['share'])}, och Öland, Gotland och Småland ligger under hälften.
- De osynliga stenarna är inte som de synliga: hela runstenar utan stilgrupp är signerade i {pr(UW['signed'] / UW['n'])} fall av hundra, mot {pr(SW['signed'] / SW['n'])} bland de stilsatta – de signerar som den äldsta stilgruppen.
- Kategorin RAK definieras av något som saknas. Bland Danmarks stilsatta runstenar är {pr(RAKR['DR']['rak'] / RAKR['DR']['styled'])} av hundra RAK, bland Norges alla, i Uppland {pr(RAKR['U']['rak'] / RAKR['U']['styled'])} av hundra. Läst som datering blir hela länder tidiga per definition.
- Mörkertalet kan tändas: en seriation daterar {SER['n_unstyled_scored']} av Upplands {SER['u_unstyled_total']} runstenar utan stilgrupp, och textmodellen prickar rätt århundrade för {sv1(DM['epoch'])} procent av runstenarna i korsvaliderade prov.
:::

## Verktyget som daterar djuren

Gräslunds system går från RAK, där runbandet har raka ändar utan djurhuvud, över fågelperspektivets Fp och korsbandsstilens KB till profilstilarna Pr1–Pr5, där djuret ses från sidan och blir allt smalare och mer utdraget. Ordningen är prövad mot myntdaterade depåer och mot stenarnas inbördes hänvisningar, och den håller: när vi själva seriationsprövar Upplands runstenar, som vi visar längre ned, följer textens och innehållets drag Gräslunds ordning med god marginal. Inget i den här artikeln ifrågasätter systemet. Frågan är vad systemet inte ser.

## Vem som står i mörkret

:::chart Andel runstenar med stilgrupp i Samnordisk runtextdatabas
# Efter land
Danmark | {pr(CTRY['Danmark']['share'])} | {CTRY['Danmark']['with_style']} av {CTRY['Danmark']['n']}
Sverige | {pr(CTRY['Sverige']['share'])} | {svn(CTRY['Sverige']['with_style'])} av {svn(CTRY['Sverige']['n'])}
+Norge | {pr(CTRY['Norge']['share'])} | {CTRY['Norge']['with_style']} av {CTRY['Norge']['n']}
# Svenska runstenar efter landskap
Västergötland | {pr(PROV['Vg']['share'])} | {PROV['Vg']['with_style']} av {PROV['Vg']['n']}
Östergötland | {pr(PROV['Ög']['share'])} | {PROV['Ög']['with_style']} av {PROV['Ög']['n']}
Uppland | {pr(PROV['U']['share'])} | {PROV['U']['with_style']} av {svn(PROV['U']['n'])}
Södermanland | {pr(PROV['Sö']['share'])} | {PROV['Sö']['with_style']} av {PROV['Sö']['n']}
+Småland | {pr(PROV['Sm']['share'])} | {PROV['Sm']['with_style']} av {PROV['Sm']['n']}
+Gotland | {pr(PROV['G']['share'])} | {PROV['G']['with_style']} av {PROV['G']['n']}
+Öland | {pr(PROV['Öl']['share'])} | {PROV['Öl']['with_style']} av {PROV['Öl']['n']}
# Svenska runstenar, hela och skadade
Utan förlorade runor | {pr(WHOLEC['share'])} | {WHOLEC['with_style']} av {WHOLEC['n']}
+Med förlorade runor | {pr(LOSTC['share'])} | {LOSTC['with_style']} av {svn(LOSTC['n'])}
# Runstenar, tolkade och otolkade
Tolkade | {pr(IRS['share'])} | {svn(IRS['with_style'])} av {svn(IRS['n'])}
+Otolkade | {pr(URS['share'])} | {URS['with_style']} av {URS['n']}
Källa: Samnordisk runtextdatabas 3.1, vikingatida runstenar. En stilgrupp räknas när Rundata anger en annan än "?". Vitkis beräkning.
:::

Mönstret är detsamma var man än skär. Skadan väger tyngst: den som vill datera en skadad sten har stilgruppen till hjälp i ungefär hälften av fallen, för en hel sten i fem av sex. Skillnaden är så stor att slumpen är utesluten som förklaring – sannolikheten att den skulle uppstå av en slump är mindre än en på en kvintiljon. Och den är ingen gåta: ornamentiken sitter på ytan, och det är ytan som vittrar, spricker och muras in. Men följden är densamma oavsett orsak. De stenar som är svårast att läsa är också de som är svårast att datera, och varje kronologisk slutsats vilar på de hela, tolkade stenarna i de välbevarade landskapen.

Också föremålen utanför runstenarna hör till bilden: gravhällar och berghällar har stilgrupp i {pr(B['by_kind']['annan sten']['share'])} fall av hundra, lösa föremål aldrig. Det är väntat – systemet är byggt för runstenar – men det betyder att stilgruppsdatering över huvud taget inte når dit.

## De osynliga är inte som de synliga

Om de niohundra stenarna utan stilgrupp vore ett slumpmässigt urval vore mörkertalet ett irritationsmoment och inget mer: slutsatserna från de synliga stenarna skulle gälla även de osynliga. Det går att pröva. Signaturen – att ristaren skriver sitt namn – är ett drag som inte kräver någon stilbestämning för att räknas, och som forskningen brukar knyta till de senare stilgrupperna.

Här måste skadan först hållas isär: en skadad sten kan ha förlorat både sin ornamentik och sin signatur, och då ser sambandet starkare ut än det är. Vi jämför därför bara hela stenar, utan förlorade runor. Bland Sveriges hela runstenar med stilgrupp är {SW['signed']} av {SW['n']} signerade, {sv1(SW['signed'] / SW['n'])} procent. Hade de hela stenarna utan stilgrupp haft samma blandning av stilar skulle ungefär {pr(SG['expected_rate_unstyled'])} av hundra vara signerade. I verkligheten är det {UW['signed']} av {UW['n']}, {sv1(UW['signed'] / UW['n'])} procent. Så få signaturer bland så många stenar uppstår av slump ungefär en gång på två tusen.

:::chart Andel signerade bland hela svenska runstenar, per stilgrupp
{chart_sign_sv}
+Utan stilgrupp | {sv1(UW['signed'] / UW['n'])} | {UW['signed']} av {UW['n']} hela stenar
Källa: Samnordisk runtextdatabas 3.1. Bara stenar utan förlorade runor, så att skadan inte förväxlas med stilen.
:::

Stenarna utan stilgrupp signerar alltså som RAK-stenarna, den grupp som räknas som äldst – inte som genomsnittet. Det finns två läsningar, och båda har följder. Antingen är de ostilsatta stenarna inte slumpmässigt spridda i tiden utan väger mot det tidiga – då är de kronologiska kurvor som ritas på de stilsatta stenarna skeva, eftersom en tidig tredjedel saknas. Eller så speglar bortfallet hur stilbestämningarna har gjorts – vilka stenar som blev granskade, avbildade och inpassade – och då är stilgruppernas täckning själv en historisk källa som ingen har läst. Siffrorna kan inte skilja läsningarna åt. Men ingen av dem tillåter att de osynliga stenarna behandlas som om de inte fanns.

## RAK: kategorin av det som saknas

Den tidigaste gruppen, RAK, definieras inte av ett formspråk utan av frånvaron av ett: raka bandändar, inget djurhuvud. Det fungerar i Uppland, där RAK är en liten minoritet omgiven av daterbara grannar. Men se vad kategorin gör med andra bestånd:

:::chart RAK:s andel av de stilsatta runstenarna
Norge | {pr(RAKR['N']['rak'] / RAKR['N']['styled'])} | {RAKR['N']['rak']} av {RAKR['N']['styled']}
Danmark | {pr(RAKR['DR']['rak'] / RAKR['DR']['styled'])} | {RAKR['DR']['rak']} av {RAKR['DR']['styled']}
+Småland | {pr(RAKR['Sm']['rak'] / RAKR['Sm']['styled'])} | {RAKR['Sm']['rak']} av {RAKR['Sm']['styled']}
+Västergötland | {pr(RAKR['Vg']['rak'] / RAKR['Vg']['styled'])} | {RAKR['Vg']['rak']} av {RAKR['Vg']['styled']}
Södermanland | {pr(RAKR['Sö']['rak'] / RAKR['Sö']['styled'])} | {RAKR['Sö']['rak']} av {RAKR['Sö']['styled']}
Uppland | {pr(RAKR['U']['rak'] / RAKR['U']['styled'])} | {RAKR['U']['rak']} av {RAKR['U']['styled']}
Källa: Samnordisk runtextdatabas 3.1, vikingatida runstenar med stilgrupp. Vitkis beräkning.
:::

I Danmark är i stort sett varje stilsatt runsten RAK, i Norge varenda en, i Västergötland och Småland tre av fyra. Läses RAK som en datering – ungefär 980 till 1015 i Gräslunds kronologi – blir nästan hela dessa bestånd tidiga per definition, inte per iakttagelse. För Danmark finns oberoende hållpunkter som pekar åt samma håll, men i varje statistisk jämförelse mellan landskapen blir cirkeln sluten: den som räknar "tidiga" och "sena" stenar per region räknar till stor del var djurornamentiken brukades, inte när stenarna restes. Utanför Mälardalen är RAK mindre en datering än en anteckning om att det inte finns något djur att datera.

## Vad det betyder för forskningens slutsatser

Varje undersökning som sorterar runstenar efter stilgrupp – när signerandet började, när en böneformel kom och försvann, hur korsen spred sig, vår egen statistik inräknad – gäller i själva verket de två tredjedelar av runstenarna som har en stilgrupp, och den tredjedelen är vald av bevarandet, tolkningen och geografin. Det gör inte slutsatserna fel, men det gör dem villkorade på ett sätt som sällan skrivs ut.

Det enklaste botemedlet kostar en rad: att redovisa täckningen tillsammans med slutsatsen. "Bland de stilsatta stenarna" är en annan utsaga än "bland stenarna", och läsaren bör få veta vilken som görs – med antal: hur många stenar som bär kurvan, och hur många som står utanför den. Vi har börjat göra det i våra egna artiklar, och mönstret i den här artikeln är skälet.

## Mörkertalet kan tändas

Det går att göra mer än att redovisa. Tre lampor finns redan:

- **Seriation på textens och innehållets drag.** Vi har ordnat Upplands runstenar efter språkdrag, formler och innehåll, utan att använda ornamentiken som indata, och prövat ordningen mot de stilsatta stenarna: den följer Gräslunds kronologi med rangkorrelationen {str(SV_['rho']).replace('.', ',')} och skattar styldaterade stenars tid med ett medelfel på {SV_['mae_loo_years']} år, mot {SV_['mae_naive_years']} om man gissar medelåret. Rangkorrelationen betyder att ordningen till god del är rätt även när årtalen är osäkra; sambandet står kvar inom enskilda härader. Vinsten är att metoden inte behöver något djur: av Upplands {SER['u_unstyled_total']} runstenar utan stilgrupp får {SER['n_unstyled_scored']} en tidsplacering, med breda men redovisade osäkerheter. Placeringarna visas sten för sten i Vitkis forskningsvy.
- **Textmodellens datering.** Sannolikhetsmodellen i Vitki, som [läser och fyller runföljder]({SPRAK}), daterar också: i korsvaliderade prov träffar den rätt århundrade för {sv1(DM['epoch'])} procent av runstenarna, och i {sv1(DM['near'])} fall av hundra ligger den högst en epok fel. Det är grovt jämfört med stilgruppernas decennier – men det är en datering som når varje sten med läsbar text, även de niohundra i mörkret.
- **Det forskningen redan vet men databasen inte rymmer.** I stilfältet skymtar bedömningar som aldrig blev regelrätta poster: hänvisningar till muntliga uppgifter och tryckta supplement, och {UNC} stenar bär sin stilgrupp med frågetecken. Litteraturen vet mer än databasen. Att samla in stilbedömningar ur Sveriges runinskrifter och senare granskningar till databasens stilfält vore det billigaste enskilda sättet att krympa mörkertalet på riktigt.

## Det siffrorna inte säger

- **Mörkertalet är databasens, inte forskningens.** Vi mäter Rundatas stilfält. Stilbedömningar kan finnas i litteraturen utan att stå där – men varje undersökning som bygger på databasen, vår egen inräknad, ärver ändå just det här bortfallet.
- **Signaturjämförelsen har två läsningar.** Att hela stenar utan stilgrupp signerar som de äldsta kan betyda att de är tidiga, eller att stilbestämmandet valt bort en viss sorts stenar. Våra tal skiljer inte läsningarna åt; det kräver att de ostilsatta stenarna dateras på annan väg.
- **Seriationen är prövad i Uppland.** Utanför Uppland vet vi ännu inte hur väl textens drag bär en tidsordning; inom ristare är sambandet svagare, som väntat när en ristares verksamma år är få.
- **Stilgrupp med frågetecken räknas som stilgrupp.** Vi räknar generöst: även osäkra bestämningar står på ljussidan. Mörkertalet är alltså snarare under- än överskattat.

## Så gjorde vi

- **Underlaget:** alla vikingatida inskrifter i Samnordisk runtextdatabas (3.1, 2018). Runsten är det Rundata kallar runsten eller fragment av runsten; en stilgrupp räknas när stilfältet anger något annat än "?". Skadad betyder förlorade runor eller förlorad text i Rundatas läsning. Signerad betyder att Rundata anger ristaren som signerad (S), inte bara attribuerad.
- **Testerna:** skillnaderna i stilgruppstäckning och signering är prövade med Fishers exakta test, och signeringen bland de ostilsatta mot den väntade andelen med ett exakt binomialtest; alla jämförelser av signering gäller enbart hela stenar. Seriationens validering är korsvaliderad mot de styldaterade stenarna (leave-one-out), med robusthetsprov utan kors, utan utlandsfärdsstenar, utan föränderliga språkdrag samt inom härader och ristare.
- **Skripten:** utdata/sprakprov/stilgrupper.py och utdata/sprakprov/morkertal.py i [kodförrådet]({GITHUB}); seriationen i r/chronology.R. Alla tal i artikeln läses ur skriptens utdata med automatiska kontroller.

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139.
- Källström, M. 2007. *Mästare och förlagor. Studier kring runristare och skriftmiljöer i vikingatidens Sverige* (Runrön 23). Uppsala universitet.
"""

body_en = f"""When Anne-Sofie Gräslund sorted the runestones by the shape of their rune bands and animal ornament, research gained perhaps its sharpest tool: a runestone can be dated to within a few decades without a single year in its text. The style groups today carry much of what we believe we know about the end of the Viking Age – when the carvers began to sign, when the prayers arrived, how the cross spread.

But a tool only sees what lies in its light. This article asks the question that is rarely asked: which runestones do the style groups see – and which stand in the dark? The answer is that more than every third runestone lacks a style group in the Scandinavian Runic-text Database, and that the loss is not random. The stones that are missing are systematically the damaged, the uninterpreted and the peripheral ones. And they do not behave like the visible ones.

:::box In short
- Of {svn(RS['n'])} Viking-age runestones, {svn(RS['with_style'])} have a style group in the Scandinavian Runic-text Database. More than nine hundred, {pr(1 - RS['share'])} per cent, stand outside.
- The loss follows the damage: a whole Swedish runestone has a style group in {pr(WHOLEC['share'])} cases out of a hundred, one with lost runes in {pr(LOSTC['share'])}. That so large a difference should arise by chance is in practice excluded.
- It also follows interpretation and geography: the uninterpreted runestones have a style group in {pr(URS['share'])} cases out of a hundred against {pr(IRS['share'])} for the interpreted, and Öland, Gotland and Småland lie below half.
- The invisible stones are not like the visible ones: whole runestones without a style group are signed in {pr(UW['signed'] / UW['n'])} cases out of a hundred, against {pr(SW['signed'] / SW['n'])} among the styled – they sign like the oldest style group.
- The category RAK is defined by something that is missing. Among Denmark's styled runestones {pr(RAKR['DR']['rak'] / RAKR['DR']['styled'])} out of a hundred are RAK, in Norway every one, in Uppland {pr(RAKR['U']['rak'] / RAKR['U']['styled'])} out of a hundred. Read as a date, whole countries become early by definition.
- The dark number can be lit: a seriation dates {SER['n_unstyled_scored']} of Uppland's {SER['u_unstyled_total']} runestones without a style group, and the text model hits the right century for {en1(DM['epoch'])} per cent of runestones in cross-validated tests.
:::

## The tool that dates the animals

Gräslund's system runs from RAK, where the rune band has straight ends and no animal head, through the bird's-eye-view Fp and the cross-band style KB to the profile styles Pr1–Pr5, where the animal is seen from the side and grows ever more slender and elongated. The order has been tested against coin-dated hoards and the stones' internal references, and it holds: when we ourselves test Uppland's runestones by seriation, as we show further down, the traits of text and content follow Gräslund's order by a clear margin. Nothing in this article questions the system. The question is what the system does not see.

## Who stands in the dark

:::chart Share of runestones with a style group in the Scandinavian Runic-text Database
# By country
Denmark | {pr(CTRY['Danmark']['share'])} | {CTRY['Danmark']['with_style']} of {CTRY['Danmark']['n']}
Sweden | {pr(CTRY['Sverige']['share'])} | {svn(CTRY['Sverige']['with_style'])} of {svn(CTRY['Sverige']['n'])}
+Norway | {pr(CTRY['Norge']['share'])} | {CTRY['Norge']['with_style']} of {CTRY['Norge']['n']}
# Swedish runestones by province
Västergötland | {pr(PROV['Vg']['share'])} | {PROV['Vg']['with_style']} of {PROV['Vg']['n']}
Östergötland | {pr(PROV['Ög']['share'])} | {PROV['Ög']['with_style']} of {PROV['Ög']['n']}
Uppland | {pr(PROV['U']['share'])} | {PROV['U']['with_style']} of {svn(PROV['U']['n'])}
Södermanland | {pr(PROV['Sö']['share'])} | {PROV['Sö']['with_style']} of {PROV['Sö']['n']}
+Småland | {pr(PROV['Sm']['share'])} | {PROV['Sm']['with_style']} of {PROV['Sm']['n']}
+Gotland | {pr(PROV['G']['share'])} | {PROV['G']['with_style']} of {PROV['G']['n']}
+Öland | {pr(PROV['Öl']['share'])} | {PROV['Öl']['with_style']} of {PROV['Öl']['n']}
# Swedish runestones, whole and damaged
Without lost runes | {pr(WHOLEC['share'])} | {WHOLEC['with_style']} of {WHOLEC['n']}
+With lost runes | {pr(LOSTC['share'])} | {LOSTC['with_style']} of {svn(LOSTC['n'])}
# Runestones, interpreted and uninterpreted
Interpreted | {pr(IRS['share'])} | {svn(IRS['with_style'])} of {svn(IRS['n'])}
+Uninterpreted | {pr(URS['share'])} | {URS['with_style']} of {URS['n']}
Source: Scandinavian Runic-text Database 3.1, Viking-age runestones. A style group counts when Rundata gives one other than "?". Vitki's calculation.
:::

The pattern is the same wherever one cuts. Damage weighs heaviest: whoever wants to date a damaged stone has the style group's help in about half of the cases, for a whole stone in five of six. The difference is so large that chance is excluded as an explanation – the probability that it would arise by chance is less than one in a quintillion. Nor is it a mystery: the ornament sits on the surface, and it is the surface that weathers, cracks and gets walled in. But the consequence is the same whatever the cause. The stones that are hardest to read are also the hardest to date, and every chronological conclusion rests on the whole, interpreted stones in the well-preserved provinces.

The objects beyond the runestones belong to the picture too: grave slabs and rock faces have a style group in {pr(B['by_kind']['annan sten']['share'])} cases out of a hundred, loose objects never. That is expected – the system is built for runestones – but it means style dating does not reach there at all.

## The invisible are not like the visible

If the nine hundred stones without a style group were a random sample, the dark number would be an annoyance and nothing more: conclusions from the visible stones would hold for the invisible as well. That can be tested. The signature – the carver writing their own name – is a trait that needs no style assessment to be counted, and one research usually ties to the later style groups.

The damage must first be kept apart: a damaged stone may have lost both its ornament and its signature, and the connection then looks stronger than it is. We therefore compare whole stones only, without lost runes. Among Sweden's whole runestones with a style group, {SW['signed']} of {SW['n']} are signed, {en1(SW['signed'] / SW['n'])} per cent. Had the whole stones without a style group had the same mix of styles, about {pr(SG['expected_rate_unstyled'])} in a hundred would be signed. In reality it is {UW['signed']} of {UW['n']}, {en1(UW['signed'] / UW['n'])} per cent. So few signatures among so many stones arise by chance about once in two thousand.

:::chart Share signed among whole Swedish runestones, by style group
{chart_sign_en}
+No style group | {en1(UW['signed'] / UW['n'])} | {UW['signed']} of {UW['n']} whole stones
Source: Scandinavian Runic-text Database 3.1. Only stones without lost runes, so that damage is not confused with style.
:::

The stones without a style group thus sign like the RAK stones, the group counted as oldest – not like the average. There are two readings, and both have consequences. Either the unstyled stones are not randomly spread in time but lean early – then the chronological curves drawn on the styled stones are skewed, because an early third is missing. Or the loss reflects how the style assessments were made – which stones were examined, drawn and fitted in – and then the style groups' coverage is itself a historical source that no one has read. The figures cannot tell the readings apart. But neither of them permits treating the invisible stones as if they did not exist.

## RAK: the category of what is missing

The earliest group, RAK, is defined not by a form language but by the absence of one: straight band ends, no animal head. That works in Uppland, where RAK is a small minority surrounded by datable neighbours. But see what the category does to other corpora:

:::chart RAK's share of the styled runestones
Norway | {pr(RAKR['N']['rak'] / RAKR['N']['styled'])} | {RAKR['N']['rak']} of {RAKR['N']['styled']}
Denmark | {pr(RAKR['DR']['rak'] / RAKR['DR']['styled'])} | {RAKR['DR']['rak']} of {RAKR['DR']['styled']}
+Småland | {pr(RAKR['Sm']['rak'] / RAKR['Sm']['styled'])} | {RAKR['Sm']['rak']} of {RAKR['Sm']['styled']}
+Västergötland | {pr(RAKR['Vg']['rak'] / RAKR['Vg']['styled'])} | {RAKR['Vg']['rak']} of {RAKR['Vg']['styled']}
Södermanland | {pr(RAKR['Sö']['rak'] / RAKR['Sö']['styled'])} | {RAKR['Sö']['rak']} of {RAKR['Sö']['styled']}
Uppland | {pr(RAKR['U']['rak'] / RAKR['U']['styled'])} | {RAKR['U']['rak']} of {RAKR['U']['styled']}
Source: Scandinavian Runic-text Database 3.1, Viking-age runestones with a style group. Vitki's calculation.
:::

In Denmark virtually every styled runestone is RAK, in Norway every single one, in Västergötland and Småland three of four. If RAK is read as a date – roughly 980 to 1015 in Gräslund's chronology – nearly all of these corpora become early by definition, not by observation. For Denmark there are independent anchors pointing the same way, but in every statistical comparison between regions the circle closes: whoever counts "early" and "late" stones per region is largely counting where animal ornament was practised, not when the stones were raised. Outside the Mälaren valley, RAK is less a date than a note that there is no animal to date.

## What it means for research's conclusions

Every study that sorts runestones by style group – when signing began, when a prayer formula came and went, how the crosses spread, our own statistics included – in fact concerns the two thirds of runestones that have a style group, and that two thirds is selected by preservation, interpretation and geography. That does not make the conclusions wrong, but it makes them conditional in a way that is seldom written out.

The simplest remedy costs one line: reporting the coverage together with the conclusion. "Among the styled stones" is a different statement from "among the stones", and the reader should be told which one is being made – with numbers: how many stones carry the curve, and how many stand outside it. We have begun doing so in our own articles, and the pattern in this article is the reason.

## The dark number can be lit

More can be done than reporting. Three lamps already exist:

- **Seriation on the traits of text and content.** We have ordered Uppland's runestones by language traits, formulas and content, without using the ornament as input, and tested the order against the styled stones: it follows Gräslund's chronology with rank correlation {SV_['rho']} and estimates style-dated stones' time with a mean error of {SV_['mae_loo_years']} years, against {SV_['mae_naive_years']} if one guesses the mean year. The rank correlation means the order is largely right even where the years are uncertain; the connection stands within individual districts. The gain is that the method needs no animal: of Uppland's {SER['u_unstyled_total']} runestones without a style group, {SER['n_unstyled_scored']} receive a placement in time, with wide but stated uncertainties. The placements are shown stone by stone in Vitki's research view.
- **The text model's dating.** The probability model in Vitki, which [reads and fills rune sequences]({SPRAK}), also dates: in cross-validated tests it hits the right century for {en1(DM['epoch'])} per cent of the runestones, and in {en1(DM['near'])} cases out of a hundred it is at most one epoch off. That is coarse beside the style groups' decades – but it is a dating that reaches every stone with readable text, including the nine hundred in the dark.
- **What research already knows but the database does not hold.** In the style field one glimpses assessments that never became proper entries: references to oral statements and printed supplements, and {UNC} stones carry their style group with a question mark. The literature knows more than the database. Collecting style assessments from Sveriges runinskrifter and later examinations into the database's style field would be the cheapest single way to truly shrink the dark number.

## What the figures do not say

- **The dark number is the database's, not research's.** We measure Rundata's style field. Style assessments may exist in the literature without standing there – but every study built on the database, our own included, still inherits exactly this loss.
- **The signature comparison has two readings.** That whole stones without a style group sign like the oldest ones may mean they are early, or that style assessment has passed over a certain kind of stone. Our figures cannot tell the readings apart; that requires dating the unstyled stones by another route.
- **The seriation is tested in Uppland.** Outside Uppland we do not yet know how well the traits of text carry a time order; within carvers the connection is weaker, as expected when a carver's active years are few.
- **A style group with a question mark counts as a style group.** We count generously: even uncertain assessments stand on the lit side. The dark number is thus under- rather than overestimated.

## How we did it

- **The material:** all Viking-age inscriptions in the Scandinavian Runic-text Database (3.1, 2018). A runestone is what Rundata calls a runestone or fragment of one; a style group counts when the style field gives anything other than "?". Damaged means lost runes or lost text in Rundata's reading. Signed means Rundata marks the carver as signed (S), not merely attributed.
- **The tests:** the differences in style-group coverage and signing are tested with Fisher's exact test, and the signing among the unstyled against the expected share with an exact binomial test; all signing comparisons concern whole stones only. The seriation's validation is cross-validated against the style-dated stones (leave-one-out), with robustness checks without crosses, without the voyage stones, without the changing language traits, and within districts and carvers.
- **The scripts:** utdata/sprakprov/stilgrupper.py and utdata/sprakprov/morkertal.py in [the repository]({GITHUB}); the seriation in r/chronology.R. Every figure in the article is read from the scripts' output with automatic checks.

## Sources

- Scandinavian Runic-text Database (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.
- Källström, M. 2007. *Mästare och förlagor. Studier kring runristare och skriftmiljöer i vikingatidens Sverige* (Runrön 23). Uppsala University.
"""

out = {"slug": "stilgruppernas-morkertal", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en}
path = os.path.join(ROOT, "utdata/blogg/morkertal.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), len(body_en.split()))

if "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
    ref = col.document()
    ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
             "topic": "Datering|stilgrupper", "createdAt": now, "updatedAt": now})
    print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
elif "--update" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    doc = sys.argv[sys.argv.index("--update") + 1]
    ref = col.document(doc)
    old = ref.get().to_dict()
    assert old and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
    json.dump(old, open(os.path.join(ROOT, f"utdata/blogg/morkertal.FORE-{dt.date.today()}.json"), "w"),
              ensure_ascii=False, indent=1, default=str)
    ref.set({**out, "updatedAt": now}, merge=True)
    print("uppdaterat utkast:", doc)
    blog._forget()
