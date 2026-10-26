"""Artikeln om Maltstenen (DR NOR1988;5), version 3 (2026-10-14): Maltstenens text läst med sannolikhetslära.
Först de många tolkningarna och varför Vitki började här, sedan det alla är överens om, sedan hela språkmodellen:
hur den byggs, hur den prövas, vad den läser på stenen, vad språket säger om de omstridda runorna och vad en
fullständig text kostar i sannolikhet. Tidigare versioner: build_malt_v1.py (landskap, litteratur) och
build_malt_v2.py (släktskapen med Rök).
Körs efter src/runlm.py-analyserna (scripts/runlm_calibrate.py och scripts/malt_decode.py):
    PYTHONDONTWRITEBYTECODE=1 .venv/bin/python utdata/blogg/build/build_malt.py [--write | --update DOKUMENT-ID]
Skriver utdata/blogg/malt.json; --write sparar ett nytt opublicerat utkast, --update skriver över ett opublicerat utkast."""
_PROJ = str(__import__("pathlib").Path(__file__).resolve().parents[3])  # projektmappen, var den än ligger
import datetime as dt
import json
import math
import os
import sys

ROOT = _PROJ
sys.path.insert(0, ROOT)
from src import blog_maps  # noqa: E402

M = os.path.join(ROOT, "utdata/Malt")
J = lambda n: json.load(open(os.path.join(M, n)))

# ---- Det texten bygger på – kontrolleras mot analysernas filer ------------------------------------------------
tolk, cal, dec = J("malt_tolkningar.json"), J("malt_avkod_kalibrering_steg1.json"), J("malt_avkodning_steg1.json")

# Dagens modell (omkörningen 2026-10-18 med textmodel-18-generationens runlm: ordpar, epoker, namnbygget)
D2 = J("malt_avkodning.json")
R2 = {w["runes"]: w for w in D2["reading"]}
assert D2["n_known"] == 36 and D2["n_unk"] == 1 and 14 <= D2["exp_right"] <= 16
assert [w["runes"] for w in D2["reading"] if w["word"] == "<unk>"] == ["afr"]
assert R2["uifr"]["word"] == "§vifr" and R2["þuR"]["word"] == "þórr"
assert R2["alisti"]["word"] == "§alisti" and R2["osa"]["word"] == "asa"
assert R2["utu"]["word"] == "letu" and R2["karþi"]["word"] == "gærði" and R2["fauþr"]["word"] == "faður"
pc = lambda x: round(100 * x)
assert tolk["pairs"] == 133 and tolk["agree"] == 25 and tolk["full_consensus_text"] == 1 and tolk["n_text"] == 14
# the model
assert dec["n_pairs"] == 16479 and dec["n_pair_inscriptions"] == 1479 and dec["n_train"] == 3661
assert dec["n_vocab"] == 4567 and dec["n_edda"] == 14815 and round(dec["d"], 1) == 0.7 and cal["lam_edda"] == 0.03
SP = {w: [(s, pc(p)) for s, p in v] for w, v in dec["spell_examples"].items()}
assert SP["stæin"][:2] == [("stain", 44), ("stin", 32)] and SP["kumbl"][:3] == [("kubl", 46), ("kuml", 35), ("kumbl", 15)]
# the test on 808 inscriptions
assert cal["n_inscriptions"] == 808 and cal["n_gold"] == 10669 and pc(cal["same"]) == 81 and pc(cal["span"]) == 92
# What the 808 test inscriptions stand on (the same selection in every version of the reading test; per word in
# utdata/runlm_forfining/kalib_klass.json). Runestones: Rundata "runsten", also fragments and lost stones (2026-10-17)
_OBJ = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data/rundata.json")))["inscriptions"]}
_KK = json.load(open(os.path.join(ROOT, "utdata/runlm_forfining/kalib_klass.json")))
assert _KK["n_inscriptions"] == cal["n_inscriptions"] and _KK["n_gold"] == cal["n_gold"]
TEST_K = {"runsten": 0, "annan sten": 0, "lösa föremål": 0}
for _s in {w[0] for w in _KK["per_word"]}:
    _r = _OBJ[_s]
    TEST_K["runsten" if "runsten" in (_r.get("object") or "").lower() else "annan sten" if _r.get("material_type") == "sten" else "lösa föremål"] += 1
assert TEST_K == {"runsten": 698, "annan sten": 84, "lösa föremål": 26}
assert sum(1 for w in _KK["per_word"] if "runsten" in (_OBJ[w[0]].get("object") or "").lower()) / len(_KK["per_word"]) > 0.85  # "nästan nio av tio ord"
top = cal["cal"][-1]
assert pc(top["raw_p"]) == 99 and pc(top["raw_acc"]) == 93 and pc(top["p"]) == 98 and pc(top["acc"]) == 98
assert cal["ece"] < 0.005
assert [pc(c["p"]) for c in cal["cal"]] == [12, 29, 50, 71, 86, 98] and [pc(c["acc"]) for c in cal["cal"]] == [12, 30, 51, 70, 84, 98]
assert [pc(c["p_rare"]) for c in cal["cal"]][-1] == 96 and [pc(c["acc_rare"]) for c in cal["cal"]][-1] == 89
# the reading
R = dec["reading"]
W = {(x["runes"], x["word"]): x["pc"] for x in R}
assert pc(W[("karþi", "gærði")]) == 94 and pc(W[("uk", "ok")]) == 82 and pc(W[("tuli", "toli")]) == 82
assert pc(W[("fauþr", "faður")]) == 79 and pc(W[("runoR", "runaR")]) == 74
hv = sorted(pc(x["pc"]) for x in R if x["word"] == "hvaR")
assert hv == [64, 68, 69] and pc(W[("osa", "asa")]) == 57 and pc(W[("iuinrunoR", "ævinrúnar")]) == 50
assert pc(W[("raki", "raggi")]) == 48 and pc(W[("taiti", "teiti")]) == 41
assert [x["runes"] for x in R if x["word"] == "<unk>"] == ["ltitul", "sti", "uifrþuR", "afrafta", "utu"]
assert len(R) == 35 and dec["n_known"] == 30 and dec["n_unk"] == 5 and round(dec["exp_right"]) == 12
LOTTO = 1 / math.comb(35, 7)
assert dec["all_right"] < LOTTO ** 2 and 1e-17 < dec["all_right"] < 1e-16 and 1e-22 < dec["forced_all"] < 1e-21
FO = {(x["runes"], x["word"]): x["pc"] for x in dec["forced"]}
assert pc(FO[("þuR", "þórr")]) == 54 and pc(FO[("uifr", "vefr")]) == 38 and pc(FO[("tuR", "týr")]) == 9
# the disputed runes
P = dec["points"]
assert pc(P["B4:1"]["k"]) == 97 and pc(P["B5:22–23"]["ki"]) == 96 and pc(P["B1:23"][":"]) == 86
assert pc(P["B4 efter 14"][":"]) == 61 and pc(P["B3:11"]["s"]) == 57 and pc(P["B5:14"]["i"]) == 50
S = dec["sensitivity"]
rng = lambda name, rd: (min([pc(P[name][rd])] + [pc(v[name][rd]) for v in S.values()]), max([pc(P[name][rd])] + [pc(v[name][rd]) for v in S.values()]))
assert rng("B4:1", "k") == (90, 97) and rng("B5:22–23", "ki") == (89, 99) and rng("B1:23", ":") == (82, 91)
assert rng("B4 efter 14", ":") == (51, 65) and pc(S["0.01/0.0"]["B3:11"]["i"]) == 89
assert pc(W[("fals", "falls")]) == 32 and pc(FO[("utu", "óttu")]) == 9
t1, lit = J("malt_text.json"), J("malt_litteratur.json")
assert len(t1["concordance"]["Vífrøðr/Vífriðr (namnet)"]) == 4
assert {g["group"]: g for g in lit["groups"]}["aiuinrunoR"]["hits"] == 1 and "Rígsþula" in {g["group"]: g for g in lit["groups"]}["aiuinrunoR"]["examples"][0]
assert sorted(round(100 * v["B5:14"]["i"]) for v in dec["sensitivity"].values()) == [39, 47, 55, 89]
OK = dec["ok_spellings"]
assert OK.get("u", 0) == 0 and OK.get("o", 0) == 0 and OK["uk"] == 229 and sum(OK.values()) == 1164

PHOTO = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Maltstenen%2C_S%C3%B8nderskov_2022a.jpg/960px-Maltstenen%2C_S%C3%B8nderskov_2022a.jpg"
PHOTO_PAGE = "https://commons.wikimedia.org/wiki/File:Maltstenen,_S%C3%B8nderskov_2022a.jpg"
CCBYSA = "https://creativecommons.org/licenses/by-sa/4.0/"
FRIDELL = "https://doi.org/10.1484/J.VMS.5.142571"
HELTOFT = "https://tidsskrift.dk/danskestudier/article/view/146816"


def num(x, sv):
    return f"{x:,}".replace(",", " " if sv else ",")


def disp(runes):
    """Malt's runes as printed in the article: ʀ for R, ą for the a-rune Rundata writes o."""
    return runes.replace("R", "ʀ").replace("o", "ą")


# ---- the reading as a line of modern words, marked by how probable each word is -------------------------------
GLOSS = {"sv": {"svá": "så", "æi": "alltid", "hvaR": "vem", "asa": "asarnas", "es": "är", "gærði": "gjorde", "faður": "fader",
                "finnr": "Finn", "falls": "fals", "teiti": "glädje", "runaR": "runor", "ok": "och", "ævinrúnar": "evighetsrunor",
                "raggi": "Ragge", "toli": "Tole"},
         "en": {"svá": "so", "æi": "ever", "hvaR": "who", "asa": "of the Æsir", "es": "is", "gærði": "made", "faður": "father",
                "finnr": "Finnr", "falls": "fals", "teiti": "joy", "runaR": "runes", "ok": "and", "ævinrúnar": "runes of eternity",
                "raggi": "Raggi", "toli": "Tóli"}}
# The carved text of the most probable combination of the disputed runes: ':' a divider, '|' a sign or the futhark row,
# '/' a row break that is no divider. Must give exactly the decoder's text.
B = dec["best"]
TEMPLATE = ("suaai:titultitul|huaRisi:alistiosa:huaRis" + B[0] + "/uifrþuR:karþi:afraftasinifauþr/kul:finR:fal" + B[3] +
            ":taitirunoR:u/" + B[2] + "iuinrunoR:suli" + B[1] + "alta:huaR|utu:tuuutbilik" + B[4] + "kR:tuRra" + B[5] + "/tuli")
assert B == [":", ":", "k", "s", "i", "ki"]
pos, group, rowbreak, signs = 0, [], set(), {}
g = 0
for ch in TEMPLATE:
    if ch in ":|":
        if ch == "|":
            signs[pos] = len(signs)
        g += 1
    elif ch == "/":
        rowbreak.add(pos)
    else:
        group.append(g); pos += 1
assert "".join(x["runes"] for x in R) == "".join(ch for ch in TEMPLATE if ch not in ":|/")


def line(lang):
    sv = lang == "sv"
    sign_label = ["[runraden]", "[tecknet]"] if sv else ["[the rune row]", "[the sign]"]
    out, brk = [], None
    for x in R:
        i = x["start"]
        if i in signs and i > 0:
            if brk:
                out.append(f"[{disp(brk[1])}]"); brk = None
            out.append(sign_label[signs[i]])
        if i in rowbreak:
            if brk:
                out.append(f"[{disp(brk[1])}]"); brk = None
            out.append("/")
        p = x["pc"]
        gl = GLOSS[lang].get(x["word"])
        if p is None or p < 0.295 or gl is None:
            if brk and brk[0] == group[i]:
                brk = (brk[0], brk[1] + x["runes"])
            else:
                if brk:
                    out.append(f"[{disp(brk[1])}]")
                brk = (group[i], x["runes"])
            continue
        if brk:
            out.append(f"[{disp(brk[1])}]"); brk = None
        out.append(f"**{gl}**" if p >= 0.695 else gl if p >= 0.495 else f"{gl}(?)")
    if brk:
        out.append(f"[{disp(brk[1])}]")
    return " ".join(out)


LINE = {lang: line(lang) for lang in ("sv", "en")}
assert LINE["sv"] == ("så(?) alltid(?) [titultitul] [runraden] vem [isi] [alisti] asarnas vem är(?) / [uifrþuʀ] **gjorde** [afraftasini] **fader** / "
                      "[kul] Finn(?) fals(?) glädje(?) **runor** **och** evighetsrunor [suli] [alta] vem [tecknet] [utu] [tuuutbilikikʀ] [tuʀ] Ragge(?) / **Tole**"), LINE["sv"]


def chart_spelling(lang):
    sv = lang == "sv"
    rows = [":::chart Så stavade runristarna två vanliga ord, enligt modellen" if sv else ":::chart How the carvers spelled two common words, according to the model",
            "# sten (stæinn)" if sv else "# stone (stæinn)"]
    rows += [f"{s} | {p}" for s, p in SP["stæin"]]
    rows += ["# kummel, minnesvård (kumbl)" if sv else "# monument (kumbl)"]
    rows += [f"{s} | {p}" for s, p in SP["kumbl"]]
    rows += [(f"Källa: Vitkis sannolikhetsmodell, skattad ur {num(dec['n_pairs'], sv)} huggna ord i Samnordisk runtextdatabas och deras normaliserade form." if sv else
              f"Source: Vitki's probability model, estimated from {num(dec['n_pairs'], sv)} carved words in the Scandinavian Runic-text Data Base and their normalized forms."), ":::"]
    return "\n".join(rows)


def chart_calibration(lang):
    sv = lang == "sv"
    rows = [":::chart När modellen säger … har den rätt i …" if sv else ":::chart When the model says … it is right in …",
            (f"# {num(cal['n_gold'], sv)} ord i {cal['n_inscriptions']} inskrifter som modellen inte hade sett" if sv else
             f"# {num(cal['n_gold'], sv)} words in {cal['n_inscriptions']} inscriptions the model had not seen")]
    for c in cal["cal"]:
        rows.append(f"{'Säger' if sv else 'Says'} {pc(c['p'])} % | {pc(c['acc'])} | {num(c['n'], sv)} {'ord' if sv else 'words'}")
    rows += [("Källa: Vitkis sannolikhetsmodell efter kalibrering, prövad i fem omgångar på inskrifter som inte fanns i träningen. Facit är Rundatas läsning; samma ord i en annan normalisering räknas som rätt." if sv else
              "Source: Vitki's probability model after calibration, tested in five rounds on inscriptions not used in training. The key is Rundata's reading; the same word in another normalization counts as right."), ":::"]
    return "\n".join(rows)


def chart_words(lang):
    sv = lang == "sv"
    G = GLOSS[lang]

    def row(runes, word, note=""):
        return f"{disp(runes)} – {G[word]} | {pc(W[(runes, word)])}" + (f" | {note}" if note else "")
    hvn = (f"tre gånger, {hv[0]}–{hv[-1]} %" if sv else f"three times, {hv[0]}–{hv[-1]} %")
    rows = [":::chart Maltstenens ord enligt modellen" if sv else ":::chart The Malt stone's words according to the model",
            "# Mer än 70 procent" if sv else "# More than 70 per cent",
            "+" + row("karþi", "gærði"), "+" + row("uk", "ok"), "+" + row("tuli", "toli", "mansnamn" if sv else "man's name"),
            "+" + row("fauþr", "faður"), "+" + row("runoR", "runaR"),
            "# 50–70 procent" if sv else "# 50–70 per cent",
            f"{disp('huaR')} – {G['hvaR']} | {hv[1]} | {hvn}", row("osa", "asa"), row("iuinrunoR", "ævinrúnar"),
            "# 30–50 procent" if sv else "# 30–50 per cent",
            row("raki", "raggi", "mansnamn" if sv else "man's name"), row("taiti", "teiti"), row("sua", "svá"),
            row("finR", "finnr", "eller ’finner’" if sv else "or 'finds'"), row("fals", "falls", "formen, inte betydelsen" if sv else "the form, not the meaning"),
            row("ai", "æi"), row("is", "es"),
            ("Källa: Vitkis sannolikhetsmodell, kalibrerade sannolikheter. Övriga runföljder får under 30 procent, och fem känner modellen inte som ord alls." if sv else
             "Source: Vitki's probability model, calibrated probabilities. The other rune sequences get under 30 per cent, and five the model does not know as words at all."), ":::"]
    return "\n".join(rows)


def chart_points(lang):
    sv = lang == "sv"
    a, b = rng("B4 efter 14", ":")
    rows = [":::chart Vad språket säger om de omstridda runorna" if sv else ":::chart What the language says about the disputed runes",
            f"+{'Rad B4, runa 1: k, inte a' if sv else 'Row B4, rune 1: k, not a'} | {pc(P['B4:1']['k'])} | {'ger uk, ’och’' if sv else 'gives uk, and'}",
            f"+{'Rad B5, runa 22–23: ki, inte il' if sv else 'Row B5, runes 22–23: ki, not il'} | {pc(P['B5:22–23']['ki'])} | {'ger ett mansnamn' if sv else 'gives a man’s name'}",
            f"+{'Rad B1, runa 23: skiljetecken, inte i' if sv else 'Row B1, rune 23: divider, not i'} | {pc(P['B1:23'][':'])}",
            f"{'Rad B4, efter runa 14: skiljetecken' if sv else 'Row B4, after rune 14: divider'} | {pc(P['B4 efter 14'][':'])} | {a}–{b} %",
            f"{'Rad B3, runa 11: s, inte i' if sv else 'Row B3, rune 11: s, not i'} | {pc(P['B3:11']['s'])} | {'osäkert' if sv else 'unsettled'}",
            f"{'Rad B5, runa 14: i, inte a' if sv else 'Row B5, rune 14: i, not a'} | {pc(P['B5:14']['i'])} | {'ingen skillnad' if sv else 'no difference'}",
            ("Källa: Vitkis sannolikhetsmodell; alla 64 kombinationer av de omstridda punkterna med lika förhandschans. Modellen ser inte stenen, bara språket." if sv else
             "Source: Vitki's probability model; all 64 combinations of the disputed points with equal prior chances. The model does not see the stone, only the language."), ":::"]
    return "\n".join(rows)


title = "Maltstenen – räknad i stället för tolkad"
summary = ("Sju forskare har gett Maltstenen sju olika innebörder. Vi lät i stället sannolikhetslära läsa den: en modell som har lärt sig "
           "runspråket ur tusentals andra inskrifter och som har prövats på 808 inskrifter med känt svar. Den bekräftar textens kärna, "
           "väljer mellan omstridda runor – och visar varför en fullständig text nästan inte går att få.")

body = f"""Den 3 april 1987 försökte ägaren till gården Ågård vid Kongeå i Jylland bli av med en sten som plogen gång på gång tagit i. När den sköts mot brinken ner till ån vände den sig, och 153 runor kom fram. Sedan dess har Maltstenen lästs som en minnessten med en gåta om solen och som en berättelse om ett gravöl och guden Tor. Den har lästs som en hälsning till var och en som ser den, som en förbannelse, som en ritual för att driva ut en dvärg och som en text där dolda runor stavar orden ’hos Freja’. Sju forskare, sju innebörder. Av 133 par av tolkningar som säger något om samma del av texten är bara 25 överens.

Det var den här stenen som fick mig att börja arbeta med Vitki. Det var inte för att jag hade en åttonde tolkning -  det var för att det fanns så många, och att de skiljde sig så kraftigt åt. Vi borde kunna förstå vår historia bättre än så. I stället för att välja den tolkning som låter bäst borde vi kunna låta runorna själva avgöra, och allt vi vet om hur vikingatidens människor skrev.

Den här artikeln är ett försök att göra just det. Vi har låtit sannolikhetslära läsa Maltstenen. Det är en modell som har lärt sig runspråket ur tusentals andra runinskrifter och som aldrig har sett någon tolkning av Maltstenen. Den anger för varje ord hur sannolikt det är, och den har prövats på 808 stenar där svaret är känt.

![Maltstenen på Museet på Sønderskov]({PHOTO})
Maltstenen på Museet på Sønderskov. Överst de två lodräta raderna och det lilla ansiktet, under den tvärgående sprickan de vågräta raderna. Foto: Hjart, [CC BY-SA 4.0]({CCBYSA}), via [Wikimedia Commons]({PHOTO_PAGE}).

## Grunden: det alla är överens om

Innan något kan tolkas måste runorna läsas, och där är läget bättre än ryktet. Runologerna är överens om 147 av de 153 runorna, 96 procent. Stenen är av rödaktig, skiktad gnejs, 2 405 kilo tung och omkring 220 centimeter hög. Runorna står i åtta rader: två lodräta överst, här kallade A1 och A2, och sex vågräta under dem, B1 till B6. Den lodräta raden A2 är hela runalfabetet. Bredvid den översta raden är ett litet mansansikte inhugget.

Mellan runorna har ristaren huggit skiljetecken. De är den viktigaste grunden vi har, för de visar var ristaren själv ansåg att något tog slut. Mellan två skiljetecken står runorna utan mellanrum. Så här står det, med stenens skiljetecken som punkter. Hakparentes betyder att läsarna är oense om just den runan:

- **A1:** suaai · titultitul
- **A2:** fuþąrkhniastbmlʀ (runraden)
- **B1:** huaʀisi · alistiąsa · huaʀis[i]
- **B2:** uifrþuʀ · karþi · afraftasinifauþr
- **B3:** kul · finʀ · fal[s] · taitirunąʀ · u
- **B4:** [a]iuinrunąʀ · suli[·]alta · huaʀ · [ett tecken som liknar tre sammanbundna t-runor]
- **B5:** utu · tuuutbilik[i]kʀ · tuʀra[ki]
- **B6:** tuli

Runan ą är den som Rundata skriver o, och ʀ är det r-ljud som senare försvann. Det enda som alla sju tolkningarna läser lika är början av rad B2: en man, Vifröd, ”gjorde” något. Allt annat skiljer sig åt. Det beror inte på att runorna är oläsliga. Det beror på att runorna mellan skiljetecknen måste delas upp i ord och förstås, och där har varje tolkare gjort sina egna val. Det är de valen som sannolikhetsläran kan pröva.

## Modellen som läser – utan att ha sett stenen

Läsningen görs av Vitkis sannolikhetsmodell för runtext – samma modell som i dag läser skadade inskrifter i appen. Hur den är byggd, hur den prövas i sex olika prov och hur väl dess procent håller berättar vi utförligt i en egen artikel, [Runorna som fattas](/artiklar/runorna-som-fattas). Här räcker det korta. Modellen har lärt sig stavning och ordföljd ur tiotusentals huggna ord i Samnordisk runtextdatabas: för varje bit text ställer den två frågor – hur sannolikt är det att en ristare skrev just det här ordet med just de här runorna, och hur sannolikt är ordet efter ordet före? Ordförrådet rymmer också Eddadikternas ord, med liten vikt, eftersom de är isländska och långt yngre än stenen.

Det viktiga för Maltstenen är två saker. För det första delar modellen själv upp runföljderna i ord: en grupp mellan två skiljetecken är ofta ett ord, men ibland två eller tre, och modellen väger alla sätt att dela den – det är precis de valen som skilt de sju tolkarna åt. För det andra har Maltstenen tagits bort ur allt modellen lärt sig. Den har aldrig sett Rundatas läsning av stenen, eller någon annans.

Innan modellen fick se stenen prövades den på {num(cal['n_gold'], True)} ord med känt svar: den läste rätt ord i {pc(cal['same'])} procent av fallen, och dess procentsatser är kalibrerade så att den har rätt ungefär så ofta som den säger. Ett förbehåll följer med in i det som kommer: för sällsynta ord – och Maltstenen är full av dem – är modellen fortfarande något för säker. När den säger {pc(cal['cal'][-1]['p_rare'])} procent om ett ord den knappt har sett, har den rätt i {pc(cal['cal'][-1]['acc_rare'])}.

## Maltstenen genom modellen

Sedan fick modellen läsa Maltstenen. Här är de ord den läser med minst 30 procents sannolikhet:

{chart_words('sv')}

Översatt till modern svenska blir den mest sannolika läsningen den här. **Fetstil** betyder mer än 70 procent, vanlig stil 50–70 procent och frågetecken 30–50 procent. Hakparentes står för runor som modellen inte kan göra till ett känt ord med minst 30 procents sannolikhet. Snedstreck markerar en ny rad:

> {LINE['sv']}

Modellen bekräftar kärnan. Raderna B1 och B4 ställer frågan ”vem” tre gånger. Någon ”gjorde” något, och en ”fader” nämns. Där står ”glädjerunor och evighetsrunor”, och stenen slutar med namnet Tole. Ordet för evighetsrunor, *ævinrúnar*, känner modellen bara från Eddan, där det står på ett enda ställe, i Rígsþula.

Modellen föreslår också något nytt. Runföljden raki i rad B5 kan vara mansnamnet Ragge, som står på en runsten i Södermanland (48 procent). Den läser fals med 32 procents säkerhet, men närmaste ordet den känner är *falls*, ’fallets’, inte ’dolde’, som flera tolkningar har det.

Men modellen fyller inte luckorna. Fem runföljder känner den inte som ord alls: delar av titultitul, delar av alistiąsa, uifrþuʀ, afrafta och utu. Ett av dem är ett misslyckande för modellen, inte för runorna. Namnet Vifröd, uifrþuʀ, finns på fyra andra runstenar, men inte i den här formen och stavningen, och därför känner modellen inte igen det. Den äldste av asarna, som flera tolkningar läser i alistiąsa, hittar modellen inte heller. Den finner bara asa, ’asarnas’ (57 procent). För utu är modellens näst bästa förslag *óttu*, ’i gryningen’, samma läsning som Heltofts ”tidigt om morgonen”. Men det får bara {pc(FO[('utu', 'óttu')])} procent när modellen tvingas välja.

Lägger vi ihop sannolikheterna för de 30 ord som modellen känner igen, får vi det väntade antalet rätta ord. Det är ungefär {round(dec['exp_right'])}. Med de fem okända runföljderna är det en tredjedel av en hel läsning, och vi vet inte säkert vilken tredjedel.

## Vad språket säger om de omstridda runorna

Sex punkter på stenen är omstridda. Modellen kan inte se stenen, men den kan säga vilken läsning språket föredrar. Vi lät den läsa texten med alla 64 kombinationer av de sex punkterna och räknade ut hur stor del av den totala sannolikheten varje läsning står för. Varje alternativ fick samma chans från början.

{chart_points('sv')}

Tre av punkterna avgör språket tydligt:

- **Rad B4, runa 1.** Stoklund och Heltoft läser a, Grønvik k. Språket ger k {pc(P['B4:1']['k'])} procent. Med k bildar runorna u och k ordet uk, ’och’, en vanlig stavning: av {num(sum(OK.values()), True)} gånger som ordet förekommer i Rundata är {OK['uk']} stavade så. Med a måste u stå ensamt för ’och’, och det gör det inte en enda gång. Här går ögat och språket isär, och det är därför den runan bör mätas först.
- **Rad B5, runa 22–23.** Grønvik läser ki, Stoklund håller il för möjligt. Språket ger ki {pc(P['B5:22–23']['ki'])} procent, eftersom raki då kan vara ett känt mansnamn.
- **Rad B1, runa 23.** Grønvik läser i, Stoklund ett skiljetecken. Språket ger skiljetecknet {pc(P['B1:23'][':'])} procent.

De tre resultaten håller när vi ändrar hur mycket vikt okända ord och Eddans ordförråd får. De stannar mellan 82 och 99 procent. De andra tre punkterna kan språket inte avgöra. Skiljetecknet efter runa 14 i rad B4 får mellan {rng('B4 efter 14', ':')[0]} och {rng('B4 efter 14', ':')[1]} procent beroende på inställningarna. För s eller i i rad B3 vänder svaret till i ({pc(S['0.01/0.0']['B3:11']['i'])} procent) om Eddans ord tas bort. Runa 14 i rad B5 står på hälften och vänder med inställningarna. Tecknet som liknar tre t-runor kan modellen inte bedöma alls, eftersom det kanske inte är runor.

## Priset för en hel text

Varför har då sju forskare fått sju olika texter? Sannolikhetsläran har ett enkelt svar. En fullständig läsning kräver att alla ord är rätt samtidigt. Sannolikheten för det är ungefär produkten av ordens sannolikheter, och den blir liten fort. För modellens mest sannolika läsning är den ungefär 2 på hundra biljarder, ett tal med 16 nollor efter decimalkommat. Det är mindre sannolikt än att vinna högsta vinsten på Lotto två veckor i rad. Och då har vi ändå låtit de fem okända runföljderna stå kvar som okända.

Tvingar vi modellen att göra ett känt ord av varje runföljd, blir texten komplett, men sannolikheten sjunker till ett tal med 21 nollor efter decimalkommat. Det händer också något med innehållet. Namnet Vifröd är det enda alla sju tolkningarna är överens om. Det blir då *vefr Þórr*, ’Tor väver’, eftersom namnets stavning inte finns i modellens ordförråd. Tor får {pc(FO[('þuR', 'þórr')])} procent och ’väver’ {pc(FO[('uifr', 'vefr')])}. Runföljden tuʀ blir guden Tyr, med {pc(FO[('tuR', 'týr')])} procent.

Det är inget argument för Tor eller Tyr. Det visar hur det går när man kräver en hel text av runor som inte räcker till det. Varje fullständig tolkning är en lång kedja av val. Kedjan är aldrig starkare än produkten av sina länkar, och där länkarna är svagast är det lättast att fylla i det man redan tror på.

## Maltstenens text, så långt den bär

Det här kan vi säga, med sannolikhetslärans stöd och utan att låna någon tolkning. Maltstenen talar om en fader, och en man, Vifröd, gjorde något. Den frågar ”vem” tre gånger. Den talar om asarna, om glädjerunor och evighetsrunor, och den slutar med namnet Tole. Resten är en handfull ord med låg sannolikhet och fem runföljder som inget känt språkmaterial kan förklara.

Det är mindre än vad varje tolkning lovar, men mer än ingenting. Det går att pröva, och det visar var nästa steg ligger. Den runa där ögat och språket går isär, rad B4 runa 1, kan mätas i en 3D-skanning. En huggen bistav har en V-formad profil, en spricka har det inte. När stenen på Museet på Sønderskov skannas kan modellen räkna om texten med de uppmätta runorna.

:::box Så säkra är vi
- **Modellen läser bara det den har sett.** Ord som saknas i Rundata och Eddan, eller som stavas på ett sätt den inte har mött, blir okända. Det gäller namnet Vifröd.
- **Eddan är inte runsvenska.** Den är isländsk och 400 år yngre. Därför får den liten vikt, och ord som bara finns där, som teiti och ævinrúnar, blir osäkrare.
- **Kalibreringen gäller vanliga stenar.** För sällsynta ord är modellen något för säker, och Maltstenen är ovanligare än nästan alla stenar.
- **Produkten är en storleksordning.** Den förutsätter att orden är oberoende av varandra, så talet för en hel text ska läsas som en storleksordning, inte som ett exakt värde.
- **Språket är inte en mätning.** Modellens besked om de omstridda runorna är språkets röst. Den ser inte stenen.
:::

## Modellen hann ikapp

Artikeln ovan beskriver modellen som den såg ut när den först mötte Maltstenen i mitten av oktober 2026. Sedan dess har den lärt sig mer: den stavar orden med ordpar ur fler inskrifter, den läser varje text i sin egen tid – och framför allt har den lärt sig att bygga namn av namnled, stavade som ristarna faktiskt stavade dem. Vi lät den läsa om Maltstenen.

Av de fem runföljder modellen inte kände som ord återstår en: afr i afrafta. Det väntade antalet rätta ord stiger från ungefär tolv till ungefär {round(D2['exp_right'])} av {len(D2['reading'])}. Och vid uifrþuʀ händer det intressantaste: modellen anar nu ett namn. Den läser §vifr som ett namn den själv har byggt ({pc(R2['uifr']['pc'])} procent kalibrerat) följt av Þórr ({pc(R2['þuR']['pc'])} procent) – den klipper alltså fortfarande Vifröd mitt itu, för namnets exakta stavning finns fortfarande ingen annanstans i det bevarade materialet. I alistiąsa bygger den namnet Alisti framför ’asarnas’ ({pc(R2['osa']['pc'])} procent för asa), och utu läser den nu som letu, ’läto’ ({pc(R2['utu']['pc'])} procent), i stället för óttu.

De byggda namnen ska läsas för vad de är: konstruktioner med låga kalibrerade procent. Modellen vågar mer än i oktober – den vet inte mer. Slutsatsen ovan står sig: texten bär så långt den bär, och det som på allvar kan flytta läsningen är fortfarande en 3D-skanning av stenen.

:::box Det viktigaste i korthet
- Maltstenens 153 runor har gett sju forskare sju olika texter. Det beror inte på oläsliga runor utan på alla val som krävs för att dela runföljderna i ord.
- Vi lät en sannolikhetsmodell, som aldrig sett någon tolkning av stenen, läsa den. Den bekräftar stommen: en fader, en man som gjorde något, tre ”vem”, asarna, glädje- och evighetsrunor, och namnet Tole sist.
- En fullständig, sammanhängande text är så osannolik att varje komplett tolkning måste läsas som en kedja av osäkra val – det är därför tolkningarna skiljer sig åt.
- Modellen har blivit bättre sedan artikeln skrevs och känner nu alla runföljder utom en, men namnet Vifröd – det enda alla tolkare är överens om – kan den fortfarande inte stava.
- Nästa steg är inte mer tolkning utan mätning: en 3D-skanning av stenen kan avgöra de omstridda runorna.
:::

## Se själv

{blog_maps.github_note('sv')} Sannolikhetsmodellen finns i src/runlm.py, och provet och läsningen av Maltstenen i scripts/runlm_calibrate.py och scripts/malt_decode.py.

## Källor och data

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Eddadikterna och Snorres Edda efter heimskringla.no (Guðni Jónssons utgåva).
- Grønvik, O. 1992. Runesteinen fra Malt i Jylland. *Arkiv för nordisk filologi* 107, s. 1–34.
- Heltoft, L. 2017. Maltstenens tekst. Hvordan dæmonen uddrives. *[Danske Studier]({HELTOFT})* 2017, s. 27–100.
- Fridell, S. 2024. A New Interpretation of the Malt Inscription. *Viking and Medieval Scandinavia* 20. [doi:10.1484/J.VMS.5.142571]({FRIDELL}) (läst i sammanfattning).
- Stoklund, M. 1994. Malt-stenen – en revurdering. *Runrön* 9, s. 179–202 (läst genom Rundata, Grønvik 1992 och Heltoft 2017).
- Thuesen, K. 1990. *Maltstenen*. UJDS-studier 7. København: Museum Tusculanums Forlag (läst genom Heltoft 2017).
- Braunmüller, K. 1992. Der Maltstein. Versuch einer Deutung. *Frühmittelalterliche Studien* 26, s. 149–164 (läst genom Heltoft 2017).
- Samplonius, K. 1992. Zum Runenstein vom Malt. *Amsterdamer Beiträge zur älteren Germanistik* 36, s. 65–91 (läst genom Heltoft 2017).
- Foto: Hjart, Wikimedia Commons, CC BY-SA 4.0."""

title_en = "The Malt stone – calculated instead of interpreted"
summary_en = ("Seven scholars have given the Malt stone seven different meanings. We let probability theory read it instead: a model that "
              "has learned the runic language from thousands of other inscriptions and has been tested on 808 inscriptions with known answers. "
              "It confirms the core of the text, chooses between disputed runes – and shows why a complete text is almost impossible to get.")

body_en = f"""On 3 April 1987 the owner of the farm of Ågård by the Kongeå river in Jutland tried to get rid of a stone that the plough had struck again and again. As it was pushed towards the bank down to the river, it turned over and 153 runes came into view. Since then the Malt stone has been read as a memorial with a riddle about the sun and as an account of a funeral ale and the god Thor. It has been read as a greeting to everyone who sees it, as a curse, as a ritual for driving out a dwarf, and as a text in which hidden runes spell the words 'with Freyja'. Seven scholars, seven meanings. Of 133 pairs of interpretations that say something about the same part of the text, only 25 agree.

It was this stone that made me start working on Vitki. It was not because I had an eighth interpretation. It was because there were so many, and so little to tell a good interpretation from a poor one. We ought to be able to understand our history better than that. Instead of choosing the interpretation that sounds best, we ought to be able to let the runes themselves decide, together with everything we know about how people wrote in the Viking Age.

This article is an attempt to do just that. We let probability theory read the Malt stone. It is a model that has learned the runic language from thousands of other runic inscriptions and has never seen any interpretation of the Malt stone. It gives, for every word, how probable it is, and it has been tested on 808 stones where the answer is known.

![The Malt stone at the Museum at Sønderskov]({PHOTO})
The Malt stone at the Museum at Sønderskov. At the top the two vertical rows and the small face, below the transverse crack the horizontal rows. Photo: Hjart, [CC BY-SA 4.0]({CCBYSA}), via [Wikimedia Commons]({PHOTO_PAGE}).

## The ground: what everyone agrees on

Before anything can be interpreted, the runes must be read, and there the situation is better than its reputation. Runologists agree on 147 of the 153 runes, 96 per cent. The stone is a reddish, layered gneiss, weighing 2,405 kilos and about 220 centimetres high. The runes stand in eight rows: two vertical ones at the top, here called A1 and A2, and six horizontal ones below them, B1 to B6. The vertical row A2 is the whole runic alphabet. A small man's face is carved next to the top row.

Between the runes the carver cut dividers. They are the most important ground we have, because they show where the carver himself thought something ended. Between two dividers the runes stand without spaces. This is what the stone says, with its dividers as dots. Square brackets mean that the readers disagree about that particular rune:

- **A1:** suaai · titultitul
- **A2:** fuþąrkhniastbmlʀ (the rune row)
- **B1:** huaʀisi · alistiąsa · huaʀis[i]
- **B2:** uifrþuʀ · karþi · afraftasinifauþr
- **B3:** kul · finʀ · fal[s] · taitirunąʀ · u
- **B4:** [a]iuinrunąʀ · suli[·]alta · huaʀ · [a sign that looks like three t-runes bound together]
- **B5:** utu · tuuutbilik[i]kʀ · tuʀra[ki]
- **B6:** tuli

The rune ą is the one Rundata writes o, and ʀ is an r-sound that later disappeared. The only thing all seven interpretations read alike is the beginning of row B2: a man, Vífrøðr, 'made' something. Everything else differs. That is not because the runes are illegible. It is because the runes between the dividers have to be divided into words and understood, and there every interpreter has made his own choices. Those choices are what probability theory can test.

## The model that reads – without having seen the stone

The reading is made by Vitki's probability model for runic text – the same model that today reads damaged inscriptions in the app. How it is built, how it is tested in six different ways and how well its percentages hold, we tell at length in an article of its own, [Runorna som fattas](/artiklar/runorna-som-fattas). Here the short version will do. The model has learnt spelling and word order from tens of thousands of carved words in the Scandinavian Runic Text Database: for every piece of text it asks two questions – how probable is it that a carver wrote this word with these runes, and how probable is the word after the word before? The vocabulary also holds the words of the Eddic poems, at a small weight, since they are Icelandic and far younger than the stone.

What matters for the Malt stone is two things. First, the model divides the rune sequences into words by itself: a group between two separators is often one word, but sometimes two or three, and the model weighs every way of dividing it – precisely the choices that set the seven interpreters apart. Second, the Malt stone has been removed from everything the model has learnt. It has never seen Rundata's reading of the stone, or anyone else's.

Before the model saw the stone it was tested on {num(cal['n_gold'], False)} words with known answers: it read the right word in {pc(cal['same'])} per cent of cases, and its percentages are calibrated so that it is right about as often as it claims. One caveat follows into what comes next: for rare words – and the Malt stone is full of them – the model is still somewhat overconfident. When it claims {pc(cal['cal'][-1]['p_rare'])} per cent about a word it has barely seen, it is right in {pc(cal['cal'][-1]['acc_rare'])}.

## The Malt stone through the model

Then the model read the Malt stone. Here are the words it reads with at least 30 per cent probability:

{chart_words('en')}

Translated into modern English, the most probable reading is this. **Bold** means more than 70 per cent, plain text 50–70 per cent and a question mark 30–50 per cent. Square brackets stand for runes the model cannot turn into a known word with at least 30 per cent probability. A slash marks a new row:

> {LINE['en']}

The model confirms the core. Rows B1 and B4 ask 'who' three times. Someone 'made' something, and a 'father' is named. There are 'runes of joy and runes of eternity', and the stone ends with the name Tóli. The word for runes of eternity, *ævinrúnar*, the model knows only from the Edda, where it occurs in a single place, in Rígsþula.

The model also suggests something new. The rune sequence raki in row B5 may be the man's name Raggi, found on a runestone in Södermanland (48 per cent). It reads fals with 32 per cent certainty, but the nearest word it knows is *falls*, 'of the fall', not 'hid', as several interpretations have it.

But the model does not fill the gaps. Five rune sequences it does not know as words at all: parts of titultitul, parts of alistiąsa, uifrþuʀ, afrafta and utu. One of them is a failure of the model, not of the runes. The name Vífrøðr, uifrþuʀ, occurs on four other runestones, but not in this form and spelling, and so the model does not recognise it. Nor does the model find the eldest of the Æsir, which several interpretations read in alistiąsa. It finds only asa, 'of the Æsir' (57 per cent). For utu the model's second-best suggestion is *óttu*, 'at dawn', the same reading as Heltoft's 'early in the morning'. But it gets only {pc(FO[('utu', 'óttu')])} per cent when the model is forced to choose.

If we add up the probabilities of the 30 words the model recognises, we get the expected number of right words. It is about {round(dec['exp_right'])}. With the five unknown rune sequences, that is a third of a complete reading, and we do not know for certain which third.

## What the language says about the disputed runes

Six points on the stone are disputed. The model cannot see the stone, but it can say which reading the language prefers. We let it read the text with all 64 combinations of the six points and worked out what share of the total probability each reading accounts for. Every alternative started with the same chance.

{chart_points('en')}

The language clearly settles three of the points:

- **Row B4, rune 1.** Stoklund and Heltoft read a, Grønvik k. The language gives k {pc(P['B4:1']['k'])} per cent. With k, the runes u and k form the word uk, 'and', a common spelling: of the {num(sum(OK.values()), False)} times the word occurs in Rundata, {OK['uk']} are spelled that way. With a, u would have to stand alone for 'and', which it does not do a single time. Here the eye and the language disagree, and that is why this rune should be measured first.
- **Row B5, runes 22–23.** Grønvik reads ki, Stoklund considers il possible. The language gives ki {pc(P['B5:22–23']['ki'])} per cent, because raki can then be a known man's name.
- **Row B1, rune 23.** Grønvik reads i, Stoklund a divider. The language gives the divider {pc(P['B1:23'][':'])} per cent.

These three results hold when we change how much weight unknown words and the Eddic vocabulary get. They stay between 82 and 99 per cent. The other three points the language cannot decide. The divider after rune 14 in row B4 gets between {rng('B4 efter 14', ':')[0]} and {rng('B4 efter 14', ':')[1]} per cent depending on the settings. For s or i in row B3 the answer turns to i ({pc(S['0.01/0.0']['B3:11']['i'])} per cent) if the Eddic words are removed. Rune 14 in row B5 stands at half and turns with the settings. The sign that looks like three t-runes the model cannot judge at all, since it may not be runes.

## The price of a complete text

Why, then, have seven scholars arrived at seven different texts? Probability theory has a simple answer. A complete reading requires every word to be right at the same time. The probability of that is roughly the product of the words' probabilities, and it shrinks fast. For the model's most probable reading it is about 2 in a hundred quadrillion, a number with 16 zeros after the decimal point. That is less likely than winning the top prize in the Swedish Lotto two weeks in a row. And that is with the five unknown rune sequences left as unknown.

If we force the model to make a known word of every rune sequence, the text becomes complete, but the probability drops to a number with 21 zeros after the decimal point. Something also happens to the content. The name Vífrøðr is the one thing all seven interpretations agree on. It becomes *vefr Þórr*, 'Thor weaves', because the name's spelling is not in the model's vocabulary. Thor gets {pc(FO[('þuR', 'þórr')])} per cent and 'weaves' {pc(FO[('uifr', 'vefr')])}. The rune sequence tuʀ becomes the god Týr, with {pc(FO[('tuR', 'týr')])} per cent.

That is no argument for Thor or Týr. It shows what happens when one demands a whole text from runes that are not enough for it. Every complete interpretation is a long chain of choices. The chain is never stronger than the product of its links, and where the links are weakest it is easiest to fill in what one already believes.

## The Malt stone's text, as far as it goes

This is what we can say, with the support of probability theory and without borrowing any interpretation. The Malt stone speaks of a father, and a man, Vífrøðr, made something. It asks 'who' three times. It speaks of the Æsir, of runes of joy and runes of eternity, and it ends with the name Tóli. The rest is a handful of words with low probability and five rune sequences that no known language material can explain.

That is less than every interpretation promises, but more than nothing. It can be tested, and it shows where the next step lies. The rune where the eye and the language disagree, row B4 rune 1, can be measured in a 3D scan. A carved branch has a V-shaped profile, a crack does not. When the stone at the Museum at Sønderskov is scanned, the model can recalculate the text with the measured runes.

:::box How sure we are
- **The model reads only what it has seen.** Words missing from Rundata and the Edda, or spelled in a way it has not met, become unknown. That applies to the name Vífrøðr.
- **The Edda is not runic Norse.** It is Icelandic and 400 years younger. So it gets little weight, and words found only there, such as teiti and ævinrúnar, become less certain.
- **The calibration holds for ordinary stones.** For rare words the model is somewhat overconfident, and the Malt stone is more unusual than almost any stone.
- **The product is an order of magnitude.** It assumes the words are independent of one another, so the figure for a whole text should be read as an order of magnitude, not an exact value.
- **Language is not a measurement.** The model's verdict on the disputed runes is the voice of the language. It does not see the stone.
:::

## The model caught up

The article above describes the model as it was when it first met the Malt stone in mid-October 2026. Since then it has learnt more: it spells the words with word pairs from more inscriptions, it reads every text in its own time – and above all it has learnt to build names from name elements, spelled as the carvers actually spelled them. We let it read the Malt stone again.

Of the five rune sequences the model did not know as words, one remains: afr in afrafta. The expected number of right words rises from about twelve to about {round(D2['exp_right'])} of {len(D2['reading'])}. And at uifrþuʀ the most interesting thing happens: the model now senses a name. It reads §vifr as a name it has built itself ({pc(R2['uifr']['pc'])} per cent calibrated) followed by Þórr ({pc(R2['þuR']['pc'])} per cent) – so it still cuts Vífrøðr in two, because the name's exact spelling still occurs nowhere else in the surviving material. In alistiąsa it builds the name Alisti before 'of the Æsir' ({pc(R2['osa']['pc'])} per cent for asa), and utu it now reads as letu, 'had raised' ({pc(R2['utu']['pc'])} per cent), instead of óttu.

The built names should be read for what they are: constructions with low calibrated percentages. The model dares more than in October – it does not know more. The conclusion above stands: the text carries as far as it carries, and what can truly move the reading is still a 3D scan of the stone.

:::box The essentials in brief
- The Malt stone's 153 runes have given seven scholars seven different texts. That is not because the runes are illegible, but because of all the choices required to divide the rune sequences into words.
- We let a probability model that has never seen any interpretation of the stone read it. It confirms the frame: a father, a man who made something, three "who", the Æsir, joy-runes and eternity-runes, and the name Tóli at the end.
- A complete, coherent text is so improbable that every full interpretation must be read as a chain of uncertain choices – which is why the interpretations differ.
- The model has improved since the article was written and now knows every rune sequence but one, yet the name Vífrøðr – the only thing all interpreters agree on – it still cannot spell.
- The next step is not more interpretation but measurement: a 3D scan of the stone can settle the disputed runes.
:::

## See for yourself

{blog_maps.github_note('en')} The probability model is in src/runlm.py, and the test and the reading of the Malt stone in scripts/runlm_calibrate.py and scripts/malt_decode.py.

## Sources and data

- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- The Eddic poems and Snorri's Edda from heimskringla.no (Guðni Jónsson's edition).
- Grønvik, O. 1992. Runesteinen fra Malt i Jylland. *Arkiv för nordisk filologi* 107, pp. 1–34.
- Heltoft, L. 2017. Maltstenens tekst. Hvordan dæmonen uddrives. *[Danske Studier]({HELTOFT})* 2017, pp. 27–100.
- Fridell, S. 2024. A New Interpretation of the Malt Inscription. *Viking and Medieval Scandinavia* 20. [doi:10.1484/J.VMS.5.142571]({FRIDELL}) (read in abstract).
- Stoklund, M. 1994. Malt-stenen – en revurdering. *Runrön* 9, pp. 179–202 (read through Rundata, Grønvik 1992 and Heltoft 2017).
- Thuesen, K. 1990. *Maltstenen*. UJDS-studier 7. Copenhagen: Museum Tusculanum (read through Heltoft 2017).
- Braunmüller, K. 1992. Der Maltstein. Versuch einer Deutung. *Frühmittelalterliche Studien* 26, pp. 149–164 (read through Heltoft 2017).
- Samplonius, K. 1992. Zum Runenstein vom Malt. *Amsterdamer Beiträge zur älteren Germanistik* 36, pp. 65–91 (read through Heltoft 2017).
- Photo: Hjart, Wikimedia Commons, CC BY-SA 4.0."""

out = {"slug": "maltstenen-raknad-i-stallet-for-tolkad", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en}
path = os.path.join(ROOT, "utdata/blogg/malt.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), len(body_en.split()))
print(LINE["en"])

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        assert not [p for p in blog._all() if p.get("slug") == out["slug"] and p.get("id") not in (None, doc)], "Adressen används redan"
        json.dump({k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in old.items()},
                  open(os.path.join(ROOT, f"utdata/blogg/{old['slug']}.FORE.json"), "w"), ensure_ascii=False, indent=1, default=str)
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    else:
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Tolkning|Malt", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
