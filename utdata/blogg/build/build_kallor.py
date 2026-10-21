"""Artikeln "Tre källor utanför Rundata": vad RuneS-DB:s runformer, Språkbankens fornsvenska ordböcker och Kielprojektets
Blekingematerial (via RuneS-DB) ger runstenarna, enligt den låsta planen utdata/kallor/analysplan_kallor.md. Varje siffra
hämtas ur utdata/kallor/*.json och låses med asserts.
    ../../../.venv/bin/python build_kallor.py [--write | --update DOC]
Skriver utdata/blogg/kallor.json; --write sparar ett nytt opublicerat utkast i Firestore."""
import datetime as dt
import io
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, commons  # noqa: E402

K = os.path.join(ROOT, "utdata", "kallor")
A = json.load(open(os.path.join(K, "skane_runformer.json"), encoding="utf-8"))
A2 = json.load(open(os.path.join(K, "skane_runformer_utan_skiljetecken.json"), encoding="utf-8"))
B = json.load(open(os.path.join(K, "fornsvenska.json"), encoding="utf-8"))
B2 = json.load(open(os.path.join(K, "fornsvenska_alla_former.json"), encoding="utf-8"))
B3 = json.load(open(os.path.join(K, "fornsvenska_en_form.json"), encoding="utf-8"))
C = json.load(open(os.path.join(K, "blekinge.json"), encoding="utf-8"))
SHA = open(os.path.join(K, "analysis_plan_kallor.sha256")).read().split()[0]
pr = lambda x: round(100 * x)  # noqa: E731
sv = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
d2 = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731

# ---- låsningarna -----------------------------------------------------------------------------------
assert SHA.startswith("c11d3142f984") and A["plan_sha256"] == B["plan_sha256"] == C["plan_sha256"] == SHA
# A
assert (A["n_stones"], A["n_positions"], len(A["signs"]), sum(v["n_graphtypes"] for v in A["signs"].values())) == (43, 2837, 21, 63)
assert A["variable_signs"] == [":", "b", "f", "m", "r", "s", "þ", "ą", "ʀ"] and A["pairs_with_value"] == 902 and A["pairs_total"] == 903
assert (d2(A["mantel"]["r"]), A["mantel"]["p"] < 0.0002, d2(A["partial_mantel"]["r"]), A["partial_mantel"]["p"] < 0.0002, A["answer"]) == ("0,42", True, "0,42", True, True)
assert abs(A["mantel_geo_form"]["r"]) < 0.03 and abs(A["mantel_geo_spell"]["r"]) < 0.03 and A["mantel_geo_form"]["p"] > 0.3 and A["mantel_geo_spell"]["p"] > 0.3
assert (d2(A2["mantel"]["r"]), round(A2["mantel"]["p"], 3), A2["variable_signs"]) == ("0,15", 0.017, ["b", "f", "m", "r", "s", "þ", "ą", "ʀ"])
DIV, S_, THORN = A["signs"][":"], A["signs"]["s"], A["signs"]["þ"]
assert (DIV["n_positions"], DIV["n_graphtypes"], S_["n_graphtypes"], S_["n_positions"], THORN["n_graphtypes"]) == (510, 7, 10, 226, 4)
assert A["signs"]["i"]["n_graphtypes"] == 1 and A["signs"]["a"]["n_graphtypes"] == 2 and A["signs"]["a"]["n_positions"] == 312
assert A["mantel"]["perms"] == 10000
# B
assert (B["n_lemmas"], B["n_tokens"], B["n_dictionary_forms"], B["n_stones"]) == (1106, 11157, 39351, 2321)
assert (B["attested_types"], B["attested_tokens"], pr(B["attested_types"] / B["n_lemmas"]), pr(B["attested_tokens"] / B["n_tokens"])) == (401, 8807, 36, 79)
cls = {k: (v["attested"], v["n"]) for k, v in B["by_class"].items()}
assert cls == {"hapax": (217, 747), "2–4": (97, 215), "≥5": (87, 144)} and B["p_one_sided"] < 1e-12 and B["answer"]
cls2 = {k: (v["attested"], v["n"]) for k, v in B2["by_class"].items()}
assert cls2 == {"hapax": (273, 747), "2–4": (117, 215), "≥5": (110, 144)} and (B2["attested_types"], B2["attested_tokens"]) == (500, 10022)
cls3 = {k: (v["attested"], v["n"]) for k, v in B3["by_class"].items()}
assert cls3["hapax"] == (217, 747) and cls3["≥5"] == (84, 144) and B3["p_one_sided"] < 1e-10
UNATT = [(x["lemma"], x["n"]) for x in B2["unattested_frequent"]]
assert UNATT[:3] == [("kumbl", 81), ("hagva", 64), ("þosi", 18)] and ("hvitavaþum", 7) in UNATT and ("oniþingr", 6) in UNATT
assert ("sialfan", 13) in UNATT and ("drepin", 15) in UNATT and ("sialu", 11) in UNATT
ATT = dict((x["lemma"], x["n"]) for x in B2["attested_frequent"])
assert ATT["ok"] == 1663 and ATT["eftir"] == 1300 and ATT["resa"] == 576 and ATT["let"] == 448 and ATT["hialpi"] == 283 and ATT["bro"] == 114
# C
ST = {s["name"].split()[1]: s for s in C["stones"].values()}
BJ, STE, GU, IS = ST["6"], ST["3"], ST["2"], ST["4"]
assert [(s["n_interpretations"], s["years"][0], s["years"][-1]) for s in (GU, STE, IS, BJ)] == [(7, 1944, 2004), (19, 1961, 2004), (7, 1960, 2001), (12, 1966, 2004)]
assert [d2(s["translation_similarity"]) for s in (GU, STE, IS, BJ)] == ["0,72", "0,21", "0,57", "0,28"]
assert (BJ["groups"]["död"]["n"], BJ["groups"]["förstörelse"]["n"], BJ["groups"]["förutsägelse/skada"]["n"], BJ["n_english"]) == (9, 9, 5, 12)
assert (STE["groups"]["död"]["n"], STE["groups"]["förstörelse"]["n"], STE["n_english"]) == (9, 9, 19) and not C["answer"]
assert len(BJ["lines"]) == 7 and (pr(min(BJ["coverage"])), pr(max(BJ["coverage"])), pr(min(BJ["agreement"]))) == (67, 92, 78)
assert len(STE["lines"]) == 6 and round(STE["agreement"][3], 2) == 0.21 and STE["agreement"][0] == 1.0 and STE["agreement"][1] == 1.0
assert all(c == 1.0 for c in GU["coverage"] + IS["coverage"])
assert "monument of honour" in BJ["english"][11] and BJ["english"][10].strip().startswith("... is hidden")
N_INTERP = sum(s["n_interpretations"] for s in (GU, STE, IS, BJ))
assert N_INTERP == 45

# ---- bilderna ----------------------------------------------------------------------------------------
FILES = commons.wikidata_files(["DR 360", "DR 335"])
INFO = commons.commons_info([FILES[s] for s in FILES])
CREDIT = {"DR 360": ("Joachim Bowin", "CC BY-SA 3.0"), "DR 335": ("Hedning", "CC BY-SA 3.0")}


def photo(signum: str, text: str) -> str:
    img = {**INFO[FILES[signum]], "signum": signum}
    assert (img["author"], img["licence"]) == CREDIT[signum], (signum, img["author"], img["licence"])
    cap = commons.caption(img, "sv")
    assert cap.startswith(f"{signum}. Foto: ")
    return f"![Runstenen {signum}]({img['thumb']})\n{text} Foto: {cap[len(signum) + 8:]}"


def fig(fil: str, alt: str, text: str, max_w: int = 1600) -> str:
    im = Image.open(os.path.join(K, fil)).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return f"![{alt}]({blog_figures.freeze(out.getvalue())})\n{text}"


PH_BJ = photo("DR 360", "Björketorpsstenen (DR 360) i Listerby socken, Blekinge, med förbannelsen på sin ena sida.")
PH_SK = photo("DR 335", "Västra Strö 2 (DR 335) i Skåne, en av de 43 stenar vars runformer RuneS-DB har registrerat position för position.")
FIG_A = fig("skane_runformer.png", "Stavningsavstånd mot runformsavstånd för 902 stenpar i Skåne",
            "Varje punkt är ett par av runstenar i Skåne. Längre åt höger: de stavar mer olika; högre upp: de formar sina "
            "runor mer olika. Punkterna stiger åt höger. Källa: Vitkis stavningsmodell och RuneS-DB:s graftyper (CC BY-SA 4.0).")

CHART_B = f""":::chart Andel av runstenarnas ord som finns i de fornsvenska ordböckerna
# Bara uppslagsorden
Ord som står en gång på stenarna | {pr(cls['hapax'][0] / cls['hapax'][1])} | {cls['hapax'][0]} av {cls['hapax'][1]}
Ord som står 2–4 gånger | {pr(cls['2–4'][0] / cls['2–4'][1])} | {cls['2–4'][0]} av {cls['2–4'][1]}
+Ord som står minst 5 gånger | {pr(cls['≥5'][0] / cls['≥5'][1])} | {cls['≥5'][0]} av {cls['≥5'][1]}
# Uppslagsorden och deras böjningsformer
Ord som står en gång på stenarna | {pr(cls2['hapax'][0] / cls2['hapax'][1])} | {cls2['hapax'][0]} av {cls2['hapax'][1]}
Ord som står 2–4 gånger | {pr(cls2['2–4'][0] / cls2['2–4'][1])} | {cls2['2–4'][0]} av {cls2['2–4'][1]}
+Ord som står minst 5 gånger | {pr(cls2['≥5'][0] / cls2['≥5'][1])} | {cls2['≥5'][0]} av {cls2['≥5'][1]}
Källa: Rundata 3.1 (normaliseringen, namn uteslutna) och Språkbankens Karp: Söderwall med supplement, Schlyter och Fornsvensk lexikalisk databas. Vitkis beräkning; andelarna är nedre gränser.
:::"""

CHART_C = f""":::chart Andel tolkningar som nämner …
# Björketorp ({BJ['n_interpretations']} tolkningar, 1966–2004)
+… döden | {pr(BJ['groups']['död']['share'])} | {BJ['groups']['död']['n']} av {BJ['n_english']}
+… att stenen förstörs | {pr(BJ['groups']['förstörelse']['share'])} | {BJ['groups']['förstörelse']['n']} av {BJ['n_english']}
… en förutsägelse eller skada | {pr(BJ['groups']['förutsägelse/skada']['share'])} | {BJ['groups']['förutsägelse/skada']['n']} av {BJ['n_english']}
# Stentoften ({STE['n_interpretations']} tolkningar, 1961–2004)
+… döden | {pr(STE['groups']['död']['share'])} | {STE['groups']['död']['n']} av {STE['n_english']}
+… att stenen förstörs | {pr(STE['groups']['förstörelse']['share'])} | {STE['groups']['förstörelse']['n']} av {STE['n_english']}
Källa: de engelska översättningarna i RuneS-DB:s tolkningsregister (CC BY-SA 4.0). Vitkis beräkning.
:::"""

title = "Tre källor utanför Rundata"
summary = ("Vitki bygger på Samnordisk runtextdatabas. Vi prövade tre databaser som ligger utanför den: RuneS-DB:s runformer, "
           "Språkbankens fornsvenska ordböcker och Kielprojektets material om Blekingestenarna. Den som stavar lika formar "
           "runorna lika, engångsorden på stenarna är de sämst belagda – och inte ens förbannelsen på Björketorp är "
           "forskarna eniga om.")

body = f"""Nästan allt Vitki räknar på kommer från en enda källa, Samnordisk runtextdatabas. Den är ryggraden, men den är inte allt. Runt den finns databaser som beskriver runstenarna från andra håll: hur varje enskild runa är formad, vilka ord som levde kvar i det medeltida svenska språket, och vad forskare under ett sekel har läst in i de äldsta inskrifterna. Vi valde tre sådana källor och ställde en fråga till var och en. Frågorna och måtten skrev vi ner och låste innan vi räknade, så att svaren inte kunde formas av det vi hoppades se.

## 1. Skåne: den som stavar lika formar runorna lika

RuneS-DB är Göttingenakademiens databas över Europas runfynd, över åtta tusen inskrifter. Det som gör den unik är graftyperna: för en del av inskrifterna har varje runa, position för position, fått en typ som beskriver dess form – hur bistavarna sitter, om tecknet är spegelvänt, hur skiljetecknet ser ut. För den yngre futharken finns det gjort för Skåne. Där överlappar RuneS-DB med Vitkis stavningsmodell, som för varje inskrift räknar ut hur ristaren stavar och sätter skiljetecken, utan att se namnen.

{PH_SK}

Så vi kunde ställa frågan: formar två stenar som stavar lika också sina runor lika? {A['n_stones']} runstenar i Skåne har både graftyper och plats i stavningsmodellen, {sv(A['n_positions'])} runpositioner sammanlagt, {len(A['signs'])} tecken med {sum(v['n_graphtypes'] for v in A['signs'].values())} olika former. De flesta tecken har bara en form – i-runan {A['signs']['i']['n_graphtypes']}, a-runan {A['signs']['a']['n_graphtypes']} på {A['signs']['a']['n_positions']} positioner – men s-runan har {S_['n_graphtypes']} former, þ-runan {THORN['n_graphtypes']}, och skiljetecknet {DIV['n_graphtypes']} på {DIV['n_positions']} positioner. För varje par av stenar räknade vi hur olika de fördelar formerna av de tecken som varierar, och jämförde med hur olika de stavar.

{FIG_A}

Sambandet är tydligt. Ju mer olika två stenar stavar, desto mer olika formar de sina runor: Spearmans korrelation {d2(A['mantel']['r'])}, och av {sv(A['mantel']['perms'])} slumpmässiga omkastningar av stenarna nådde ingen upp till det (p = {A['mantel']['p']:.4f}). Det är inte geografin som gör det. Avståndet i kilometer mellan stenarna hänger varken ihop med runformerna (korrelation {d2(A['mantel_geo_form']['r'])}) eller med stavningen ({d2(A['mantel_geo_spell']['r'])}), och när vi räknar bort det blir sambandet detsamma, {d2(A['partial_mantel']['r'])}.

En sak ska sägas rakt ut. Större delen av sambandet sitter i skiljetecknet. Om vi tar bort det och bara ser på de åtta runtecken som varierar – b, f, m, r, s, þ, ą och ʀ – faller korrelationen till {d2(A2['mantel']['r'])}, fortfarande positiv och fortfarande mer än slumpen klarar (p = {A2['mantel']['p']:.3f}), men mycket svagare. Skiljetecknet är nämligen det drag där de två källorna möts: Vitki registrerar om ristaren satte punkt, kolon eller kryss mellan orden, RuneS-DB registrerar vilken form tecknet har. Det är samma vana sedd från två håll, inte två oberoende vittnen. Men det är också resultatet: den personligaste vanan på en skånsk runsten är inte hur a-runan ser ut, utan hur ristaren skilde orden åt. Runtecknen bär resten av sambandet, och det är där RuneS-DB tillför något vi inte haft – en mätning av handen som inte går genom stavningen.

## 2. Fornsvenskan: engångsorden är de sämst belagda

Språkbanken vid Göteborgs universitet håller de stora fornsvenska ordböckerna maskinläsbara: Söderwalls ordbok över medeltidsspråket med sitt supplement, Schlyters ordbok till de gamla lagarna och Fornsvensk lexikalisk databas, tillsammans {sv(B['n_dictionary_forms'])} uppslagsord. De beskriver svenskan från omkring 1225 och framåt, ett par hundra år efter runstenarna. Vi ville veta hur mycket av runstenarnas ordförråd som finns kvar där – och framför allt om de ord som står en enda gång på stenarna, så kallade hapax, är belagda lika ofta som de vanliga.

Frågan har en udd. Ett ord som står på hundra stenar är säkert läst: det finns hundra chanser att se att det är rätt. Ett ord som står på en enda sten vilar på en enda läsning av en enda skadad yta. Om engångsorden saknas i ordböckerna långt oftare än de vanliga, så säger det något om hur många av dem som är lästa rätt – och om hur försiktig Vitkis textmodell bör vara när den föreslår ett ord den bara sett en gång.

Vi tog alla ord på de {sv(B['n_stones'])} svenska vikingatida runstenarna, {sv(B['n_lemmas'])} olika ord med {sv(B['n_tokens'])} förekomster när namnen är borttagna, och letade efter dem i ordböckerna med en fast lista av stavningsregler: runsvenskans *stæin* får bli fornsvenskans *sten*, *æftiR* får bli *äfter*, *ð* och *þ* får skrivas *th* eller *dh*. Reglerna fångar inte allt. Bland de vanligaste ord som inte hittas finns böjningar som reglerna inte klarar – *haggva* för hugga, *sialfan* för själv, *dræpinn* för dräpa – så andelarna nedan är nedre gränser.

{CHART_B}

Av de vanliga orden, de som står minst fem gånger, hittar vi {pr(cls['≥5'][0] / cls['≥5'][1])} procent i ordböckerna; av engångsorden {pr(cls['hapax'][0] / cls['hapax'][1])} procent. Skillnaden är inte en slump: om de två sorternas ord vore belagda lika ofta skulle ett så stort gap uppstå i färre än ett fall på tusen miljarder (p = {B['p_one_sided']:.0e}). Den står sig när ordböckernas böjningsformer räknas med ({pr(cls2['hapax'][0] / cls2['hapax'][1])} mot {pr(cls2['≥5'][0] / cls2['≥5'][1])} procent) och när varje ord bara får en enda form att matcha med, så att de vanliga orden inte får fler chanser genom sina många böjningar ({pr(cls3['hapax'][0] / cls3['hapax'][1])} mot {pr(cls3['≥5'][0] / cls3['≥5'][1])} procent).

Räknat i förekomster är bilden ljus: {pr(B2['attested_tokens'] / B['n_tokens'])} procent av allt som står på stenarna är ord som levde vidare i medeltidens svenska – *ok*, *æftiR*, *ræisa*, *stæinn*, *hialpa*, *bro*. Det som saknas är en lång svans av ord som står en eller ett par gånger. En del är ord som ordböckerna faktiskt kan sakna: *kumbl* för minnesmärket, som står på {UNATT[0][1]} stenar, *hvitavaðum*, ”i vita kläder”, om den som dog nydöpt, eller *oniðingR*, ”ingen niding”. Men bland engångsorden finns också former som *fulgin*, *drogr* och *rogstarkr*, som bara en läsning av en sten står bakom. Där har textmodellen anledning att vara ödmjuk, och där kan ordböckerna bli ett stöd: ett föreslaget ord som finns i Söderwall är ett bättre förslag än ett som inte finns någonstans.

## 3. Blekinge: inte ens förbannelsen är forskarna eniga om

Kiels runprojekt byggde under många år den stora databasen över inskrifterna i den äldre futharken, den runrad som användes före vikingatiden. Dess material ingår i dag i RuneS-DB, och det var tur, för Kielservern avvisade våra anslutningar. Där finns Blekingestenarna: Gummarp, Stentoften, Istaby och Björketorp, stenarna från omkring år 600 med den formel som vår artikelserie om magi utgår från – den som lovar en försåtlig död åt den som bryter minnesmärket.

{PH_BJ}

Det RuneS-DB har, och som ingen annan källa har, är tolkningarna. För varje inskrift ligger forskarnas läsningar sida vid sida: translitterering, normaliserad text, tysk och engelsk översättning, litteratur. Gummarp har {GU['n_interpretations']} tolkningar, Istaby {IS['n_interpretations']}, Björketorp {BJ['n_interpretations']} och Stentoften {STE['n_interpretations']}, {N_INTERP} sammanlagt, publicerade mellan {GU['years'][0]} och {BJ['years'][-1]}. Vi läste ingen av dem som rätt eller fel. Vi räknade i stället på hur mycket de skiljer sig åt, som vi gjorde med Maltstenen.

Först raderna. För varje rad i en inskrift räknade vi hur många tolkningar som alls translittererar den och hur många som läser runorna som majoriteten gör. På Gummarp och Istaby läser alla alla rader, och enigheten är 71–100 procent. På Björketorp läser 67–92 procent av tolkningarna varje rad, och de som gör det är eniga till 78–100 procent: om själva runorna råder ingen större strid. Stentoften är annorlunda. De två första raderna, *niuhᴀborumz niuhagestumz*, läser alla likadant – men vad de betyder går isär i allt från ”nio bockar, nio hingstar” till ”de nya bönderna, de nya främlingarna” – och på raden *hᴀriwolᴀfz(m)ᴀ(2?)usnuh(1?)e* är bara {pr(STE['agreement'][3])} procent av tolkningarna eniga om vilka runor som står där.

Sedan översättningarna. Vi mätte hur lika de engelska översättningarna är parvis, på en skala där 1 är ordagrant samma text. Gummarp {d2(GU['translation_similarity'])}, Istaby {d2(IS['translation_similarity'])}, Björketorp {d2(BJ['translation_similarity'])}, Stentoften {d2(STE['translation_similarity'])}. De korta inskrifterna med namn är stabila; de långa med formler är det inte.

Vår låsta hypotes gällde förbannelsen. Vi gissade att den var den fasta punkten: att minst 80 procent av tolkningarna av Björketorp och Stentoften nämner döden och att stenen förstörs, medan orden för förutsägelse och skada i Björketorps inledning skulle vara mer omstridda.

{CHART_C}

Hypotesen föll. På Björketorp nämner {BJ['groups']['död']['n']} av {BJ['n_english']} tolkningar döden och {BJ['groups']['förstörelse']['n']} att stenen förstörs, {pr(BJ['groups']['död']['share'])} procent. Två av de tre som inte gör det är fragment som bara översätter en del av texten, men den tredje läser hela stenen som något annat: en hedersvård åt en vän, utan förbannelse. På Stentoften är det {STE['groups']['död']['n']} av {STE['n_english']}: där stannar hälften av tolkningarna vid offer- och årsväxtraderna och tar sig aldrig an förbannelsen. Inledningens förutsägelse på Björketorp, *uþᴀrᴀbᴀsbᴀ*, nämns av {BJ['groups']['förutsägelse/skada']['n']} av {BJ['n_english']}. Vi hade alltså rätt om rangordningen men fel om nivån. Förbannelsen är det stabilaste i de två inskrifterna – och ändå står en fjärdedel av tolkningarna utanför den.

Det är ett användbart tal. När vår magiserie bygger på att Björketorp och Stentoften bär en förbannelse står den på det som tre av fyra forskare sedan 1960-talet läst där, inte på en enighet som inte finns.

## Och fynden runt stenarna?

Vi prövade också en fjärde källa, K-samsök, Riksantikvarieämbetets samlade museidata, för att lägga Statens historiska museers vikingatida fynd runt stenarna. Fynden finns där, {sv(246543)} föremål från vikingatiden, men inget av dem har en fyndplats i det som går att söka på: varken socken, landskap eller koordinater följer med. Museets egen webbplats går dessutom inte att nå från vår maskin. Fyndkartan får vänta.

:::box Det viktigaste i korthet
- Rundata beskriver *vad* som står på stenarna. Tre källor utanför den beskriver *hur* runorna är formade, *vilka ord* som levde vidare och *hur oense* forskarna är – och alla tre går att räkna på.
- I Skåne stavar och formar ristarna i samma riktning, oberoende av var stenarna står. Det tydligaste personliga draget är skiljetecknet; runformerna bär ett svagare men verkligt samband av eget.
- Ord som bara står en gång på runstenarna hittas i de medeltida ordböckerna hälften så ofta som de vanliga orden. Det är där läsningarna är minst säkra, och där textmodellen ska vara försiktigast.
- Inte ens förbannelsen på Björketorp och Stentoften är forskarna eniga om: tre av fyra tolkningar läser den, en av fyra inte. En hypotes som bygger på den vilar på en majoritet, inte på en enighet.
:::

:::box Så räknade vi
- Planen låstes 2026-10-21 innan måtten räknades (SHA-256 {SHA[:12]}…; metoddokumentationen avsnitt 14h och 17). Alla tre frågorna fick ett förutbestämt ja och nej; den tredje blev nej.
- Skåne: {A['n_stones']} runstenar med graftyper i RuneS-DB, DR-signum i Rundata och plats i stavningsmodellen. Runformsavstånd över tecken med minst två former på minst fem positioner var; stavningsavstånd 1 − cosinus; Manteltest med {sv(A['mantel']['perms'])} permutationer och partiell Mantel mot log-avståndet i km. Känslighet utan skiljetecknet.
- Fornsvenskan: lemman ur textmodellen, namn uteslutna, en fast regellista för stavningen. Tvåproportionstest mellan engångsord och ord med minst fem förekomster. Två känslighetskörningar: bara en form per ord, och ordböckernas böjda former medräknade.
- Blekinge: RuneS-DB:s tolkningsregister. Täckning och enighet per rad, parvis likhet mellan de engelska översättningarna (difflib), och ordgrupperna död, förstörelse och förutsägelse/skada i översättningarna. Inga egna läsningar.
- Avvikelser: urvalet i Skåne blev 43 stenar, inte 42 som inventeringen sa; en bugg i tolkningsläsaren (bara första raden lästes) rättades innan måtten redovisades; känslighetskörningarna är tillägg.
:::

## Se själv

Skripten och resultaten ligger öppet i Vitkis källkod under `utdata/kallor/`. RuneS-DB finns på runesdb.de och Språkbankens ordböcker i Karp på spraakbanken.gu.se; båda går att läsa utan konto.

## Källor

- RuneS-DB. *Runische Schriftlichkeit in den germanischen Sprachen.* Niedersächsische Akademie der Wissenschaften zu Göttingen. runesdb.de (beta; data CC BY-SA 4.0). Poster för Skåne och Blekinge hämtade 2026-10-21.
- Språkbanken Text, Göteborgs universitet: Söderwall, K. F. *Ordbok öfver svenska medeltids-språket* med supplement; Schlyter, C. J. *Ordbok till Samlingen af Sweriges Gamla Lagar*; Fornsvensk lexikalisk databas. Karp v7, hämtade 2026-10-21.
- Kieler Runenprojekt (Christian-Albrechts-Universität zu Kiel), via RuneS-DB.
- K-samsök, Riksantikvarieämbetet (kulturarvsdata.se).
- Krause, W. & Jankuhn, H. 1966. *Die Runeninschriften im älteren Futhark.* Göttingen.
- Antonsen, E. H. 1975. *A Concise Grammar of the Older Runic Inscriptions.* Tübingen.
- Samnordisk runtextdatabas, version 3.1 (ODbL).
- Foton: se bildtexterna."""

for word in (" han ", " hans ", " hon ", " henne ", " hennes "):  # no pronouns for carvers or scholars
    assert word not in body, word
assert not re.search(r"\b(jag|mig|min)\b", body, re.I) and not re.search(r"^\|", body, re.M)
assert "kumbl* för minnesmärket, som står på 81 stenar" in body

out = {"slug": "tre-kallor-utanfor-rundata", "title": title, "summary": summary, "body": body,
       "title_en": "", "summary_en": "", "body_en": "", "labels": ["Forskning", "Språk och stavning", "Tro och magi", "Norden"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "kallor.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "kallor.json"), len(body.split()), "ord")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and old.get("slug") == out["slug"] and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    else:
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Källor|runes-karp-kiel", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
