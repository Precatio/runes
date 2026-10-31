"""Artikeln "Hur bra är vår modell egentligen? En dag bakom kulisserna" (sv + en): Viktors fråga 2026-10-30 om hur
kompetent sannolikhetsmodellen är jämfört med annat, och vilka källor som kan utöka dess ordförråd – berättad som en
dagbok från den dagen. Siffrorna låses mot src/textmodel.VALIDATION, utdata/runlm_forfining/tm21_sammanfattning.json,
utdata/Rok/jamforelse.json, utdata/Malt/malt_avkodning.json och korpusarna i utdata/varlden/korpus.
    ../../../.venv/bin/python build_modell_dagbok.py [--write | --update DOC]"""
import datetime as dt
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import runlm as rl  # noqa: E402
from src import textmodel as tm  # noqa: E402

pc = lambda x: int(100 * x + 0.5)  # noqa: E731  (halva avrundas uppåt: 58,5 → 59)
sp = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en_ = lambda n: f"{n:,}"  # noqa: E731

# ---- the locked numbers -----------------------------------------------------------------------------------------------
V = tm.VALIDATION
assert tm.VERSION == "textmodel-19"
VERSION_N = int(tm.VERSION.split("-")[1])
assert VERSION_N == 19  # "nitton versioner" i texten
assert (pc(V["inside_word"]), pc(V["whole_word"]), pc(V["sure_right"]), pc(V["documented_right"])) == (76, 59, 95, 70)
assert (pc(V["dating_epoch"]), pc(V["dating_near"]), pc(V["with_traces"])) == (59, 95, 84)
N_V = sum(1 for r in rl.load_rundata() if rl.viking(r) and r.get("transliteration"))
assert N_V == 3662
M = json.load(open(os.path.join(ROOT, "utdata", "Malt", "malt_avkodning.json"), encoding="utf-8"))
assert (M["n_pairs"], M["n_vocab"], round(M["exp_right"]), len(M["reading"]), M["n_unk"]) == (26337, 4567, 15, 37, 1)
C = json.load(open(os.path.join(ROOT, "utdata", "Malt", "malt_avkod_kalibrering.json"), encoding="utf-8"))
assert C["n_inscriptions"] == 808 and C["ece"] < 0.01 and (pc(C["rare_acc"]), pc(C["rare_mean_pc"])) == (47, 47)
R = json.load(open(os.path.join(ROOT, "utdata", "Rok", "jamforelse.json"), encoding="utf-8"))
RT = R["total"]
assert (RT["comparable"], RT["span_ok"], RT["word_ok"], RT["sure"], RT["sure_ok"]) == (147, 79, 50, 8, 6)
assert R["dating"]["epochs"][1]["epoch"] == "900" and pc(R["dating"]["epochs"][1]["p"]) == 78
assert (R["epochs_in_training"]["800"], R["epochs_in_training"]["900"]) == (19, 440)
T = json.load(open(os.path.join(ROOT, "utdata", "runlm_forfining", "tm21_sammanfattning.json"), encoding="utf-8"))["A"]
assert (pc(T["accuracy"]["inne i ord"]["app"]), pc(T["accuracy"]["helt ord"]["app"])) == (77, 59)
assert T["sure"]["tol02"] == [409, 19] and T["sure"]["app"] == [342, 15] and T["words"]["inne i ord"]["n"] == 698
S = json.load(open(os.path.join(ROOT, "utdata", "runlm_forfining", "tm21_sammanfattning.json"), encoding="utf-8"))
B = S["B"]
assert not S["B_holds"] and B["words"]["inne i ord"]["won"] == 8 and B["words"]["inne i ord"]["lost"] == 6
assert B["words"]["helt ord"]["won"] == 16 and B["words"]["helt ord"]["lost"] == 22 and B["sure"]["app3"] == [430, 17]
# the text we have for the vocabulary step (analysplaner/2026-10-30-litteraturlexikon.md)
def words_in(folder):
    return sum(len(re.findall(r"\w+", open(f, encoding="utf-8").read())) for f in glob.glob(os.path.join(ROOT, "utdata", "varlden", "korpus", folder, "*.txt")))
SRC = {"edda": len(rl.edda_tokens()), "heimskringla": words_in("heimskringla"), "fornaldar": words_in("fornaldarsogur"),
       "samtid": words_in("samtidssagor"), "islanninga": words_in("islendingasogur")}
assert SRC["edda"] == 90852 and SRC["heimskringla"] == 260876 and SRC["fornaldar"] == 357557 and SRC["islanninga"] == 897101
MED = [r for r in rl.load_rundata() if (r.get("period") or r.get("dating") or "")[:1] == "M" and r.get("transliteration") and r.get("normalization")]
MED_WORDS = sum(len(re.findall(r"[^\s]+", r["normalization"])) for r in MED)
assert len(MED) == 2748 and 16900 < MED_WORDS < 17000
PET = sum(1 for _ in open(os.path.join(ROOT, "data", "cache", "literature", "peterson2007_namn.csv"), encoding="utf-8")) - 1
assert PET == 1710
ITHACA = {"n": 78608, "restore": 62, "historians": 25, "together": 72, "years": 30, "place": 71}  # Assael m.fl., Nature 2022
MALT_ART = "/artiklar/maltstenen-raknad-i-stallet-for-tolkad"
RUNOR_ART = "/artiklar/runorna-som-fattas"


def chart_acc(lang):
    sv = lang == "sv"
    rows = [":::chart Hur ofta modellen har rätt, mätt på stenar den aldrig sett" if sv else
            ":::chart How often the model is right, measured on stones it has never seen",
            f"+{'Runor inne i ett ord' if sv else 'Runes inside a word'} | {pc(V['inside_word'])} | {'698 dolda luckor' if sv else '698 hidden gaps'}",
            f"{'Hela förlorade ord' if sv else 'Whole lost words'} | {pc(V['whole_word'])} | {'698 dolda ord' if sv else '698 hidden words'}",
            f"{'Dokumenterade luckor' if sv else 'Documented gaps'} | {pc(V['documented_right'])} | {'361 luckor kända från äldre teckningar' if sv else '361 gaps known from older drawings'}",
            f"{'Det den säger sig vara säker på' if sv else 'What it calls certain'} | {pc(V['sure_right'])} | {'svar på minst 95 %' if sv else 'answers at 95 % or more'}",
            f"{'Rökstenen, ord för ord' if sv else 'The Rök stone, word by word'} | {pc(RT['word_ok'] / RT['comparable'])} | {RT['word_ok']} {'av' if sv else 'of'} {RT['comparable']}",
            ("Källa: textmodel-19:s prov med hela stenar undanhållna (METHODS.md 8.1) och läsningen av Ög 136 utan Rök i träningen; Vitkis mätning." if sv else
             "Source: textmodel-19's tests with whole stones held out (METHODS.md 8.1) and the reading of Ög 136 with Rök left out of training; Vitki's measurement.")]
    return "\n".join(rows) + "\n:::"


def chart_src(lang):
    sv = lang == "sv"
    tot = SRC["edda"] + MED_WORDS + SRC["heimskringla"] + SRC["fornaldar"] + SRC["samtid"] + SRC["islanninga"]
    f = sp if sv else en_
    rows = [":::chart Fornnordisk text som kan ge modellen ord, i tusental ord" if sv else
            ":::chart Old Norse text that could give the model words, in thousands of words",
            f"{'Eddan (redan inlagd)' if sv else 'The Edda (already in)'} | {pc(SRC['edda'] / tot)} | {f(SRC['edda'])} {'ord' if sv else 'words'}",
            f"+{'Medeltida runinskrifter' if sv else 'Medieval runic inscriptions'} | {pc(MED_WORDS / tot)} | {f(MED_WORDS)} {'ord, samma skrift' if sv else 'words, the same script'}",
            f"{'Heimskringla' if sv else 'Heimskringla'} | {pc(SRC['heimskringla'] / tot)} | {f(SRC['heimskringla'])} {'ord' if sv else 'words'}",
            f"{'Fornaldarsagorna' if sv else 'The legendary sagas'} | {pc(SRC['fornaldar'] / tot)} | {f(SRC['fornaldar'])} {'ord' if sv else 'words'}",
            f"{'Samtidssagorna' if sv else 'The contemporary sagas'} | {pc(SRC['samtid'] / tot)} | {f(SRC['samtid'])} {'ord' if sv else 'words'}",
            f"{'Islänningasagorna' if sv else 'The sagas of Icelanders'} | {pc(SRC['islanninga'] / tot)} | {f(SRC['islanninga'])} {'ord, nutida stavning' if sv else 'words, modern spelling'}",
            ("Källa: Eddan ur appens textmodell; Rundata (medeltid); heimskringla.no och sagadb.org, hämtade till Vikingarnas värld. Procent = andel av alla orden." if sv else
             "Source: the Edda in the app's text model; Rundata (medieval); heimskringla.no and sagadb.org, fetched for Vikingarnas värld. Per cent = share of all the words.")]
    return "\n".join(rows) + "\n:::"


title = "Hur bra är vår sannolikhetsmodell egentligen? En dag bakom kulisserna"
summary = ("Vi fick frågan hur kompetent vår sannolikhetsmodell är jämfört med annat som finns, och om den går att "
           "göra bättre. Här är svaret, berättat från den dagen: fem processer som räknar, en Rökläsning som misslyckas på "
           "rätt sätt, en jämförelse med DeepMinds Ithaca, och en lista på vad vi tänker mata modellen med.")

body = f"""**11.11.** Fem processer startar. Var och en bygger sin egen upplaga av textmodellen, med en femtedel av stenarna undanhållna, och fyller sedan {T['words']['inne i ord']['n']} dolda luckor inne i ord och lika många hela dolda ord med appens egen inställning. Det är ett prov vi aldrig gjort förut, fast vi borde: siffrorna appen visar var mätta med en enklare inställning än den appen själv använder. Ingen av processerna skriver något förrän den är klar. Det är ett fel i provskriptet, inte i modellen, och det ska rättas.

Textmodellen är Vitkis sätt att läsa runor med siffror. Den möter du på varje stensida under fliken *Läsning och luckor*, där den delar upp runföljden i ord, ger varje ord en sannolikhet och föreslår vad som kan ha stått i skadade partier. Du möter den i *Forskningsluckor* under *Luckor i texten*, där den fyller luckor som utgivarna lämnat öppna, i stenrapporten, och i våra artiklar om Maltstenen och om runorna som fattas. Den daterar också en text på dess språk, med en siffra som säger hur osäker dateringen är. Allt annat i appen – huggspåren, ristarna, statistiken – klarar sig utan den; men när det gäller vad runorna säger är det den som talar.

Så ser en dag ut när vi arbetar med modellen, och sådana dagar har det blivit många. Modellen har byggts om i nitton versioner sedan mitten av oktober: stavningsmodellen, ordföljden, Eddans ordförråd, kalibreringen, ristarens egen stavning, namnen byggda av namnled, spåren från 3D-skanningar, toleransen för ovanliga stavningar. Varje version har körts genom samma prov med stenar undanhållna, och flera försök har förkastats därför att de inte höll – en variantkvot i förra veckan, en gemensam datering, en imputering av odaterade stenar. Den här artikeln är ett försök att visa hur det går till, och om modellen går att göra bättre.

:::box Kort sagt
- Modellen läser och fyller luckor i vikingatida runtexter med sannolikheter. Mätt på stenar den aldrig sett har den rätt i {pc(V['inside_word'])} procent av runorna inne i ett ord och {pc(V['whole_word'])} procent av hela förlorade ord, och det den kallar säkert stämmer i {pc(V['sure_right'])} procent.
- Det är samma nivå som DeepMinds Ithaca för grekiska inskrifter, byggd på tjugo gånger mer text. Men Ithacas viktigaste lärdom är en annan: forskare och modell tillsammans slår båda var för sig.
- Modellen vet bara ord den sett. På Rökstenen läser den formeln rätt och faller på allt som bara står där. Den säger själv att den är osäker, och det är dess bästa egenskap.
- Nästa steg är ett större ordförråd: medeltida runinskrifter, Heimskringla, sagorna, lagarna och ett namnlexikon. Planen är låst, och den godkänner bara det som ger fler rätt utan fler säkra fel.
:::

## Vad modellen är

Den är ingen stor språkmodell. Den är en statistisk modell byggd på {sp(N_V)} vikingatida runinskrifter i Samnordisk runtextdatabas, med en stavningsmodell lärd på {sp(M['n_pairs'])} par av huggen runföljd och normaliserat ord, ett ordförråd på {sp(M['n_vocab'])} ord plus Eddans, och en modell för vilka ord som följer på vilka. Den läser en runsten genom att pröva alla sätt att dela upp runorna i ord och väga dem mot varandra. Varje ord får en sannolikhet, och sannolikheten är kalibrerad: när modellen säger 80 procent ska den ha rätt fyra gånger av fem. Den detaljen är hela poängen. Vi har [skrivit om hur den läste Maltstenen]({MALT_ART}) och om [luckorna den fyller]({RUNOR_ART}).

Tre regler gäller alltid. Modellen får aldrig träna på den sten den ska läsa. Varje påstående kommer med sin sannolikhet. Och varje förbättring prövas mot en plan som låses innan vi ser resultatet, så att vi inte kan välja de siffror som ser bäst ut.

**10.32, samma morgon.** Innan frågan kom hade vi redan låtit modellen läsa Rökstenen, byggd utan Rök i träningen. Det tog fem minuter. Av Rundatas {RT['comparable']} jämförbara ord avgränsade den {RT['span_ok']} rätt och läste {RT['word_ok']} som samma ord. Den klarade minnesformeln – *standa runaR þaR*, *faði faðiR*, *kunungaR tvæiR* – och föll på vartenda ord som bara finns på Rök: *mogminni*, *valraufaR*, *Þioðrik*, *Siolundi*, chiffren. Modellen kan bara ord den har sett, och Rökstenens hela särart är orden ingen annan sten har. Men den var ärlig: den satte minst 95 procent på bara {RT['sure']} ord, och {RT['sure_ok']} av dem stämde. Dateringen blev 900-talet med {pc(R['dating']['epochs'][1]['p'])} procent, mot Rundatas 800-tal, av ett enkelt skäl: modellen har lärt sig på {R['epochs_in_training']['800']} stenar från 800-talet och {R['epochs_in_training']['900']} från 900-talet.

## Så mäter vi

{chart_acc('sv')}

Siffrorna kommer från prov där hela stenar hålls undan. Vi döljer runor i texter vi känner, låter modellen fylla dem, och räknar. Inne i ett ord, där grannrunorna hjälper, blir {pc(V['inside_word'])} procent rätt. När hela ordet är borta {pc(V['whole_word'])} procent. På de {361} luckor där runorna är kända från äldre teckningar men förlorade i dag – de luckor appen faktiskt möter – {pc(V['documented_right'])} procent. Med spår från en 3D-skanning, där halva runan syns, stiger hela ord till {pc(V['with_traces'])} procent.

Och kalibreringen: av de svar modellen ger minst 95 procent stämmer {pc(V['sure_right'])} procent. I ett prov på {C['n_inscriptions']} inskrifter var kalibreringsfelet under en procentenhet, och för sällsynta ord, där modeller brukar skryta, sade den i snitt {pc(C['rare_mean_pc'])} procent och hade rätt i {pc(C['rare_acc'])}. Det är därför Rökläsningen inte är ett misslyckande. En modell som läser fel och vet om det är användbar. En som läser fel med säkerhet är farlig.

**11.52.** Första steget klart. Med appens egen inställning blev det {pc(T['accuracy']['inne i ord']['app'])} procent inne i ord och {pc(T['accuracy']['helt ord']['app'])} procent hela ord: samma som de publicerade siffrorna. Men appen är försiktigare: {T['sure']['app'][0]} säkra svar med {T['sure']['app'][1]} fel, mot {T['sure']['tol02'][0]} med {T['sure']['tol02'][1]} i det enklare provet. Det var dagens viktigaste besked, och det var inte spännande, vilket är som det ska. Steg två – om modellen blir bättre av att bedöma kandidaterna efter följder om tre ord – startar direkt.

## Jämfört med annat

Det finns, såvitt vi vet, ingen annan modell som läser vikingatida runtexter med sannolikheter prövade på undanhållna stenar. Rundata och Runor är databaser. De stora språkmodellerna kan återge tolkningen av en känd sten därför att de har läst den, men på en okänd text gissar de utan att veta hur säkra de är, och ingen har prövat dem på stenar de inte sett. När vi lät en bild-AI gissa stilgrupp på 57 stenar fick den rätt i 35 procent av fallen.

Den närmaste jämförelsen är Ithaca, DeepMinds modell för grekiska inskrifter, publicerad i *Nature* 2022. Den är ett neuralt nät tränat på {sp(ITHACA['n'])} inskrifter. Den återställer skadad text rätt i {ITHACA['restore']} procent av fallen, daterar med ett medelfel på omkring {ITHACA['years']} år och placerar en inskrift geografiskt rätt i {ITHACA['place']} procent. Våra {pc(V['whole_word'])} och {pc(V['inside_word'])} procent ligger i samma trakt, på en korpus som är tjugo gånger mindre, och vår datering är sämre: rätt epok i {pc(V['dating_epoch'])} procent av fallen, rätt eller intilliggande i {pc(V['dating_near'])}. Jämförelsen haltar – olika språk, olika uppgifter, olika mått – men den säger ungefär var vi står.

Det viktigaste i Ithaca-studien var inte modellens siffra. Historiker ensamma återställde texterna rätt i {ITHACA['historians']} procent av fallen, modellen i {ITHACA['restore']}, och historiker med modellen som hjälp i {ITHACA['together']}. Det är den arbetsordningen Vitki är byggd för: modellen föreslår och säger hur säker den är, runologen avgör.

## Vad som fattas

Modellen har tre svagheter som vi vet om. Ordförrådet är Rundata och Eddan, så ett ord som bara står på en sten är osynligt. Sammanhanget är två ord i rad. Och korpusen är liten, vilket ingen kan ändra: det finns inte fler vikingatida runtexter. Den första svagheten går att göra något åt.

**14.00.** Nästa fråga: kan ordförrådet utökas, och med vad? Vi tog fram vad som finns.

{chart_src('sv')}

Källorna är inte likvärdiga, och ordningen är viktig:

- **De medeltida runinskrifterna** ligger redan i Rundata men används inte av modellen: {sp(len(MED))} inskrifter, mest norska från Bryggen i Bergen, gotländska och danska. Det är samma skrift, samma sätt att stava med runor, bara ett par hundra år senare. Det är den källa som ligger närmast.
- **Heimskringla och fornaldarsagorna** är normaliserad fornvästnordiska, drygt 600 000 ord, hämtade i våras till vår artikel om vikingarnas omvärld. Språket är isländskt 1200-tal, men ordförrådet är i stort det samma.
- **Islänningasagorna** är den största källan, nära 900 000 ord, men i nutida isländsk stavning. De kan bara användas om stavningen går att föra tillbaka till fornnordisk form med regler som vi först prövar på de normaliserade texterna.
- **De fornsvenska lagarna**, Västgötalagen och Upplandslagen, är det som står närmast runsvenskan i tid och dialekt. Vi har dem inte ännu.
- **Lexikonen:** Zoëgas ordbok över fornisländskan är fri att använda, och Lena Petersons *Nordiskt runnamnslexikon* ligger sedan i dag som en tabell med {sp(PET)} uppslag. Det är lexikonet som kan lära modellen bygga namn som Vífrøðr, som alla uttolkare av Maltstenen läser och som modellen inte kan stava.

Risken är lika tydlig som vinsten. Fler ord betyder fler kandidater, och fler kandidater betyder fler falska träffar på korta luckor. Därför är planen låst innan något räknas: varje källa får en egen vikt som väljs på ett enda prov, och lexikonet godkänns bara om modellen vinner fler ord än den förlorar utan att de säkra felen blir fler. Sedan läser vi om Malt och Rök och räknar hur många okända följder som återstår. Det är det provet som avgör om Maltstenen kommer en bit närmare, eller inte alls.

**17.48.** Steg två klart, efter sex timmar. Trigrammen vinner {B['words']['inne i ord']['won']} ord och förlorar {B['words']['inne i ord']['lost']} inne i ord, men förlorar fler hela ord än de vinner ({B['words']['helt ord']['won']} mot {B['words']['helt ord']['lost']}), och de gör modellen säkrare på fler svar – {B['sure']['app3'][0]} i stället för {T['sure']['app'][0]} – med fler fel, {B['sure']['app3'][1]} mot {T['sure']['app'][1]}. Planen krävde vinst i båda slagen utan fler säkra fel. Den håller inte. Ingenting ändras i appen, och det står i loggen som ett negativt resultat, som variantkvoten förra veckan. Så slutar de flesta dagar med modellen: ett prov som visar var den inte blir bättre. Det är de dagarna som gör att siffrorna går att lita på.

## Vad vi inte gör

Vi kommer inte att byta ut modellen mot en stor språkmodell. Inte för att de är dåliga, utan för att vi inte kan pröva dem: de har läst tolkningarna, och vi kan inte hålla en sten undan från dem. En modell vars siffror vi inte kan mäta kan inte sitta i en app som lovar att säga hur säker den är.

:::box Det viktigaste i korthet
- Modellen är ungefär så bra som det bästa som publicerats för andra inskriftsmaterial, på mycket mindre data, och den är ärligt mätt: det den kallar säkert stämmer i {pc(V['sure_right'])} procent.
- Den läser formler, inte unika texter. Rökstenen visar var gränsen går, och modellen visar den själv.
- Nästa steg är inte en smartare modell utan mer text: runinskrifter från medeltiden, sagorna, lagarna och ett namnlexikon, prövade mot en låst plan.
- Det bästa resultatet kommer inte från modellen ensam utan från runologen som använder den.
:::

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Assael, Y., Sommerschield, T., Shillingford, B. m.fl. 2022. Restoring and attributing ancient texts using deep neural networks. *Nature* 603, 280–283 (Ithaca).
- Peterson, Lena 2007. *Nordiskt runnamnslexikon*, 5 uppl. Institutet för språk och folkminnen.
- Zoëga, Geir T. 1910. *A Concise Dictionary of Old Icelandic*. Oxford.
- heimskringla.no och sagadb.org för sagatexterna; Vitkis metodbeskrivning (METHODS.md 8.1), proven och de låsta planerna ligger öppet på [GitHub](https://github.com/Precatio/runes)."""

title_en = "How good is our probability model, really? A day behind the scenes"
summary_en = ("We were asked how capable our probability model is compared with what else exists, and "
              "whether it can be made better. Here is the answer, told from that day: five processes computing, a reading of "
              "the Rök stone that fails in the right way, a comparison with DeepMind's Ithaca, and a list of what we plan to feed the model.")

body_en = f"""**11.11.** Five processes start. Each builds its own edition of the text model with a fifth of the stones held out, and then fills {T['words']['inne i ord']['n']} hidden gaps inside words and as many whole hidden words with the app's own settings. It is a test we have never run before, though we should have: the figures the app shows were measured with a simpler setting than the one the app itself uses. None of the processes writes anything until it is done. That is a flaw in the test script, not in the model, and it will be fixed.

The text model is Vitki's way of reading runes with numbers. You meet it on every stone page under the tab *Läsning och luckor* (reading and gaps), where it divides the rune sequence into words, gives every word a probability and proposes what may have stood in damaged stretches. You meet it in *Forskningsluckor* under *Luckor i texten*, where it fills gaps the editors left open, in the stone report, and in our articles on the Malt stone and on the runes that are missing. It also dates a text by its language, with a figure that says how uncertain the dating is. Everything else in the app – the grooves, the carvers, the statistics – manages without it; but when it comes to what the runes say, it is the one that speaks.

That is what a day looks like when we work on the model, and there have been many such days. The model has been rebuilt in nineteen versions since mid-October: the spelling model, the word order, the Edda's vocabulary, the calibration, the carver's own spelling, names built from name elements, the traces from 3D scans, the tolerance for unusual spellings. Every version has been run through the same tests with stones held out, and several attempts have been discarded because they did not hold – a variant quota last week, a joint dating, an imputation of undated stones. This article is an attempt to show how that works, and whether the model can be made better.

:::box In short
- The model reads and fills gaps in Viking-age runic texts with probabilities. Measured on stones it has never seen, it gets {pc(V['inside_word'])} per cent of the runes inside a word right and {pc(V['whole_word'])} per cent of whole lost words, and what it calls certain is right {pc(V['sure_right'])} per cent of the time.
- That is the level of DeepMind's Ithaca for Greek inscriptions, built on twenty times more text. But Ithaca's main lesson is another: scholars and the model together beat either alone.
- The model knows only words it has seen. On the Rök stone it reads the formula right and fails on everything that stands only there. It says itself that it is unsure, and that is its best quality.
- The next step is a larger vocabulary: medieval runic inscriptions, Heimskringla, the sagas, the law codes and a name lexicon. The plan is locked, and it approves only what gives more right answers without more confident errors.
:::

## What the model is

It is not a large language model. It is a statistical model built on {en_(N_V)} Viking-age runic inscriptions in the Scandinavian Runic-text Data Base, with a spelling model learned from {en_(M['n_pairs'])} pairs of carved rune sequence and normalised word, a vocabulary of {en_(M['n_vocab'])} words plus the Edda's, and a model of which words follow which. It reads a runestone by trying every way of dividing the runes into words and weighing them against each other. Every word gets a probability, and the probability is calibrated: when the model says 80 per cent, it should be right four times in five. That detail is the whole point. We have written about [how it read the Malt stone](/en{MALT_ART}) and about [the gaps it fills](/en{RUNOR_ART}).

Three rules always apply. The model never trains on the stone it is to read. Every claim comes with its probability. And every improvement is tested against a plan locked before we see the result, so that we cannot pick the figures that look best.

**10.32, the same morning.** Before the question came, we had already let the model read the Rök stone, built without Rök in its training. It took five minutes. Of Rundata's {RT['comparable']} comparable words it delimited {RT['span_ok']} correctly and read {RT['word_ok']} as the same word. It managed the memorial formula – *standa runaR þaR*, *faði faðiR*, *kunungaR tvæiR* – and failed on every word that exists only on Rök: *mogminni*, *valraufaR*, *Þioðrik*, *Siolundi*, the ciphers. The model knows only words it has seen, and the whole singularity of the Rök stone is the words no other stone has. But it was honest: it put 95 per cent or more on only {RT['sure']} words, and {RT['sure_ok']} of them were right. The dating came out as the tenth century at {pc(R['dating']['epochs'][1]['p'])} per cent, against Rundata's ninth, for a simple reason: the model has learned from {R['epochs_in_training']['800']} stones of the ninth century and {R['epochs_in_training']['900']} of the tenth.

## How we measure

{chart_acc('en')}

The figures come from tests where whole stones are held out. We hide runes in texts we know, let the model fill them, and count. Inside a word, where the neighbouring runes help, {pc(V['inside_word'])} per cent come out right. When the whole word is gone, {pc(V['whole_word'])} per cent. On the {361} gaps where the runes are known from older drawings but lost today – the gaps the app actually meets – {pc(V['documented_right'])} per cent. With traces from a 3D scan, where half the rune is visible, whole words rise to {pc(V['with_traces'])} per cent.

And the calibration: of the answers the model gives at 95 per cent or more, {pc(V['sure_right'])} per cent are right. In a test on {C['n_inscriptions']} inscriptions the calibration error was under one percentage point, and for rare words, where models tend to boast, it said {pc(C['rare_mean_pc'])} per cent on average and was right {pc(C['rare_acc'])} per cent of the time. That is why the Rök reading is not a failure. A model that reads wrongly and knows it is useful. One that reads wrongly with confidence is dangerous.

**11.52.** Step one done. With the app's own settings it came to {pc(T['accuracy']['inne i ord']['app'])} per cent inside words and {pc(T['accuracy']['helt ord']['app'])} per cent whole words: the same as the published figures. But the app is more cautious: {T['sure']['app'][0]} confident answers with {T['sure']['app'][1]} errors, against {T['sure']['tol02'][0]} with {T['sure']['tol02'][1]} in the simpler test. That was the day's most important news, and it was not exciting, which is as it should be. Step two – whether the model improves by judging candidates on sequences of three words – starts at once.

## Compared with others

As far as we know there is no other model that reads Viking-age runic texts with probabilities tested on held-out stones. Rundata and Runor are databases. The large language models can reproduce the interpretation of a known stone because they have read it, but on an unknown text they guess without knowing how sure they are, and no one has tested them on stones they have not seen. When we let an image AI guess the style group of 57 stones, it was right 35 per cent of the time.

The closest comparison is Ithaca, DeepMind's model for Greek inscriptions, published in *Nature* in 2022. It is a neural network trained on {en_(ITHACA['n'])} inscriptions. It restores damaged text correctly in {ITHACA['restore']} per cent of cases, dates with a mean error of about {ITHACA['years']} years and places an inscription geographically in {ITHACA['place']} per cent. Our {pc(V['whole_word'])} and {pc(V['inside_word'])} per cent are in the same region, on a corpus twenty times smaller, and our dating is worse: the right epoch in {pc(V['dating_epoch'])} per cent of cases, the right or the neighbouring one in {pc(V['dating_near'])}. The comparison limps – different languages, tasks and measures – but it says roughly where we stand.

The most important thing in the Ithaca study was not the model's figure. Historians alone restored the texts correctly in {ITHACA['historians']} per cent of cases, the model in {ITHACA['restore']}, and historians with the model's help in {ITHACA['together']}. That is the working order Vitki is built for: the model proposes and says how sure it is, the runologist decides.

## What is missing

The model has three weaknesses we know of. Its vocabulary is Rundata and the Edda, so a word that stands on one stone only is invisible. Its context is two words in a row. And the corpus is small, which no one can change: there are no more Viking-age runic texts. The first weakness can be addressed.

**14.00.** The next question: can the vocabulary be extended, and with what? We took stock of what exists.

{chart_src('en')}

The sources are not equal, and the order matters:

- **The medieval runic inscriptions** are already in Rundata but unused by the model: {en_(len(MED))} inscriptions, mostly Norwegian from Bryggen in Bergen, Gotlandic and Danish. It is the same script, the same way of spelling with runes, only a couple of centuries later. It is the closest source there is.
- **Heimskringla and the legendary sagas** are normalised Old West Norse, some 600,000 words, fetched this spring for our article on the Vikings' world. The language is thirteenth-century Icelandic, but the vocabulary is largely the same.
- **The sagas of Icelanders** are the largest source, nearly 900,000 words, but in modern Icelandic spelling. They can be used only if the spelling can be brought back to Old Norse form by rules we first test on the normalised texts.
- **The Old Swedish law codes**, the Västgöta and Uppland laws, are what stands closest to runic Swedish in time and dialect. We do not have them yet.
- **The lexica:** Zoëga's dictionary of Old Icelandic is free to use, and Lena Peterson's *Nordiskt runnamnslexikon* has since today been a table of {en_(PET)} entries. It is the lexicon that can teach the model to build names like Vífrøðr, which every interpreter of the Malt stone reads and which the model cannot spell.

The risk is as clear as the gain. More words mean more candidates, and more candidates mean more false hits in short gaps. That is why the plan is locked before anything is counted: each source gets a weight of its own chosen on a single test, and the lexicon is approved only if the model wins more words than it loses without the confident errors growing. Then we read Malt and Rök again and count how many unknown sequences remain. That test decides whether the Malt stone comes a step closer, or not at all.

**17.48.** Step two done, after six hours. The trigrams win {B['words']['inne i ord']['won']} words and lose {B['words']['inne i ord']['lost']} inside words, but lose more whole words than they win ({B['words']['helt ord']['won']} against {B['words']['helt ord']['lost']}), and they make the model confident about more answers – {B['sure']['app3'][0]} instead of {T['sure']['app'][0]} – with more errors, {B['sure']['app3'][1]} against {T['sure']['app'][1]}. The plan required gains in both kinds without more confident errors. It does not hold. Nothing changes in the app, and it goes in the log as a negative result, like the variant quota last week. That is how most days with the model end: a test that shows where it does not get better. Those are the days that make the figures trustworthy.

## What we will not do

We will not replace the model with a large language model. Not because they are bad, but because we cannot test them: they have read the interpretations, and we cannot hold a stone back from them. A model whose figures we cannot measure cannot sit in an app that promises to say how sure it is.

:::box The essentials in brief
- The model is about as good as the best published for other epigraphic material, on far less data, and it is honestly measured: what it calls certain is right {pc(V['sure_right'])} per cent of the time.
- It reads formulas, not unique texts. The Rök stone shows where the limit lies, and the model shows it itself.
- The next step is not a cleverer model but more text: medieval runic inscriptions, the sagas, the law codes and a name lexicon, tested against a locked plan.
- The best result comes not from the model alone but from the runologist who uses it.
:::

## Sources

- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Assael, Y., Sommerschield, T., Shillingford, B. et al. 2022. Restoring and attributing ancient texts using deep neural networks. *Nature* 603, 280–283 (Ithaca).
- Peterson, Lena 2007. *Nordiskt runnamnslexikon*, 5th ed. Institute for Language and Folklore.
- Zoëga, Geir T. 1910. *A Concise Dictionary of Old Icelandic*. Oxford.
- heimskringla.no and sagadb.org for the saga texts; Vitki's method description (METHODS.md 8.1), the tests and the locked plans are open on [GitHub](https://github.com/Precatio/runes)."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"

out = {"slug": "hur-bra-ar-var-modell-egentligen", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Pågående arbete", "Sannolikhetsmodellen"]}
from src import blog_labels  # noqa: E402  (Admin avvisar ogiltiga etiketter med 422; samma kontroll här)
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
path = os.path.join(ROOT, "utdata", "blogg", "modell_dagbok.json")
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
                 "topic": "Metod|textmodellen", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
