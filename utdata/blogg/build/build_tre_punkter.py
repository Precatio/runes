"""Artikeln "Tre punkter i texten": vad Vitkis sannolikhetsmodell föreslår i de luckor som utgivarna lämnat öppna, prövat
mot utgåvorna och mot språkprovet. Varje siffra läses ur data/textmodel_candidates.json (scripts/textmodel_candidates.py,
kalibrerad lista sedan 2026-10-23), utdata/luckartikel/del3/litteratur.json (genomgången av utgåvorna, motprövad) och
utdata/sprakprov/sprakprov.json (språkprovet, låst 2026-10-16), och låses med asserts; varje citat ur en utgåva står
ordagrant i genomgången. Runstenar i huvuddelen, andra föremål för sig. Tvåspråkig.
    ../../../.venv/bin/python build_tre_punkter.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import commons  # noqa: E402

C = json.load(open(os.path.join(ROOT, "data", "textmodel_candidates.json"), encoding="utf-8"))
L = json.load(open(os.path.join(ROOT, "utdata", "luckartikel", "del3", "litteratur.json"), encoding="utf-8"))
SP = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "utdata", "sprakprov", "sprakprov.json"), encoding="utf-8"))["rows"]}
LIT = {s["signum"]: s for s in L["stones"]}
pct = lambda x: round(100 * x)  # noqa: E731


def lit(sig: str, word: str | None = None) -> str:
    """Everything the review recorded for a stone (or one of its words): literature, traces and assessment."""
    gs = [g for g in LIT[sig]["gaps"] if word is None or g["word"] == word]
    assert gs, (sig, word)
    return " ".join(g["literature"] + " " + g["traces"] + " " + g["assessment"] for g in gs)


def row(sig: str, word: str) -> dict:
    rs = [c for c in C["candidates"] if c["signum"] == sig and c["word"] == word]
    assert rs, (sig, word)
    return max(rs, key=lambda c: c["p"])


# ---- the list, as the app shows it -------------------------------------------------------------------------------------
RS = C["counts"]["runsten"]
assert C["p_is"] == "calibrated" and C["model_version"] == "textmodel-19" and (C["min_p"], C["sure_p"]) == (0.5, 0.8)
assert (RS["gaps_inventoried"], RS["open"], RS["candidates"], RS["stones"], RS["sure"]) == (685, 112, 17, 15, 7)
OT = C["counts"]["annat"]
assert (OT["candidates"], OT["stones"]) == (12, 8)
rs_rows = [c for c in C["candidates"] if c["runestone"]]
STONES = sorted({c["signum"] for c in rs_rows})
assert len(STONES) == 15 and len(rs_rows) == 17
# raw against calibrated: the correction
EX = {("U 1180", "risti"): (93, 85), ("Sm 47", "þikra"): (100, 93), ("Sö 245", "mag"): (97, 73), ("Ög 115", "fyrir"): (96, 63),
      ("U 522", "heðingunnr"): (82, 56)}
for (s, w), (raw, cal) in EX.items():
    r = row(s, w)
    assert (pct(r["p_model"]), pct(r["p"])) == (raw, cal), (s, w, r["p_model"], r["p"])
# the earlier article's claim, recomputed with textmodel-19 (reconcile in the review)
assert L["reconcile"]["still_true"] is True
assert any("open runestone 0/70 >= 95 %" in n for n in L["reconcile"]["numbers"])
assert pct(row("U 765", "hans")["p"]) == 97

# ---- the five inscriptions the editions read as no language, and the language test (locked 2026-10-16) -----------------
NONSENSE = {"U 466": ("ok", "runrad"), "U 522": ("heðingunnr", "runrad"), "U 1180": ("risti", "inte språk"),
            "U 493": ("vaR", "inte språk"), "Sm 47": ("þikra", "inte språk")}
for s, (w, v) in NONSENSE.items():
    assert SP[s]["verdict"] == v, (s, SP[s]["verdict"])
    row(s, w)
assert "Inskriften ger ingen språklig mening" in lit("U 466") and "Inskriften ger ingen språklig mening" in lit("U 493")
assert "icke ger någon språklig mening" in lit("U 522")
assert "som icke ha någon språklig innebörd" in lit("U 1180")
assert "De ge ingen sammanhängande inskrift med någon mening i" in lit("Sm 47")
LANGLIKE = ["U 784", "U 246", "Öl ATA4377/56A"]
assert all(SP[s]["verdict"] == "språklik" and SP[s]["runes"] == 10 for s in LANGLIKE)
NOT_IN_TEST = [s for s in STONES if s not in SP]
assert sorted(NOT_IN_TEST) == sorted(["U 765", "Öl 57", "Öl ATA4701/43", "U 525", "Sö 245", "Ög 115", "U Fv1976;108"]), NOT_IN_TEST
sp_counts = json.load(open(os.path.join(ROOT, "utdata", "sprakprov", "sprakprov.json"), encoding="utf-8"))["verdicts"]
assert sp_counts == {"språklik": 35, "runrad": 18, "oklart": 4, "inte språk": 55}

# ---- traces that speak against the model, context it lacks, and agreement --------------------------------------------
assert "Runan 35 har möjligen varit k" in lit("U 525") and "Runan 38 förefaller att ha varit ett i" in lit("U 525")
assert {pct(c["p"]) for c in C["candidates"] if c["signum"] == "U 525"} == {76, 74, 73}
assert "runan kan hava varit n eller h" in lit("U 493")
assert "lēt rētta stæin þe[nna]" in lit("Öl 57") and "omöjligt att tolka" in lit("Öl 57") and pct(row("Öl 57", "ræisa")["p"]) == 86
assert "ma[g] sinn" in lit("Sö 245") and "Tolkad av redaktionen" in lit("Sö 245")
assert "Inskriften är tyvärr alltför skadad för att tillåta ett tolkningsförslag" in lit("U 765")
assert "hst och möjligen spår av en bst t. v. om hst" in lit("U 765")
assert "Ristningen är mycket förvittrad" in lit("Ög 115")
# other objects
assert "I runföljden 68—73 finnas måhända spår av ristarens namn" in lit("U Fv1946;258")
assert "Gud hjälpe ande och själ" in lit("Sö 23")
assert "Nonsensinskrift, magisk?" in lit("U NOR1994;26A") and "not lost runes" in lit("U NOR1994;26A")
assert pct(row("U Fv1946;258", "viseti")["p"]) == 61 and pct(row("Sö 23", "and")["p"]) == 78 and pct(row("U NOR1994;26A", "fængit")["p"]) == 62
OBJ = sorted({c["signum"] for c in C["candidates"] if not c["runestone"]})
from api.rundata import store  # noqa: E402
_by = {r["signum"]: r for r in store().inscriptions}
assert sorted((_by[x].get("object") or "") for x in OBJ) == sorted(["berghäll", "berghäll", "gravhäll", "runben, revben, fragment",
                                                                   "runben, revben", "bleck (amulett)", "bleck", "skifferbit"])
assert "Jansson 1946, Fornvännen 41 pp. 257–260" in " ".join(g for st in L["stones"] if st["signum"] == "U Fv1946;258"
                                                              for gp in st["gaps"] for g in gp["sources_checked"])
# the blind test figures as published in Runorna som fattas
_rsf = next(p for p in json.load(open(os.path.join(ROOT, "web", "content", "articles.json"), encoding="utf-8"))["posts"]
            if p["slug"] == "runorna-som-fattas")["body"]
assert "Modellen valde utgivarnas ord i 16 av 21 luckor" in _rsf and "Alla 13 luckor där den påstod minst 95 procent blev rätt" in _rsf
assert OBJ == sorted(["Sö 23", "Sö 280", "U Fv1946;258", "U Fv1992;161B", "U NOR1994;26A", "U NOR2000;34B", "Ån Fv1908;298A", "Öl Fv1976;96A"]), OBJ
# what is left when the editions and the two models are weighed together: runestone gaps where nothing in the editions we
# could read speaks against the word (the language test could judge only some of them)
KEEP = ["U 765", "U 784", "Öl ATA4701/43", "Sö 245", "Ög 115"]
assert all(s in STONES for s in KEEP) and not set(KEEP) & set(NONSENSE) and "U 525" not in KEEP and "Öl 57" not in KEEP
KEEP_WORDS = sorted({c["word"] for c in rs_rows if c["signum"] in KEEP})
assert KEEP_WORDS == ["fyrir", "hans", "mag", "ok"], KEEP_WORDS
DROPPED = ["U 525", "Öl 57", "U 246", "U Fv1976;108", "Öl ATA4377/56A"]
assert sorted(STONES) == sorted(KEEP + list(NONSENSE) + DROPPED)
assert "efter 3 a synes ett kort lodrätt streck, som kan vara ett sk, eller möjligen rest av en hst" in lit("U 246")
assert "(resa st)en efter" in lit("U 246") and pct(row("U 246", "sinn")["p"]) == 56
assert "Möjligen har den aldrig givit någon språklig mening, utan varit en imitation av inskriften på en runsten" in lit("U Fv1976;108")
assert pct(row("U Fv1976;108", "sinn")["p"]) == 52 and "U Fv1976;108" not in SP
# Öl ATA4377/56A: an archive reading (Owe 1998) disagrees with the fill; U 784: the reading comes from a work we could not read
assert "Owe läser" in lit("Öl ATA4377/56A") and "disagrees with the fill" in lit("Öl ATA4377/56A")
assert LIT["U 784"]["gaps"][0]["literature_status"] == "not_reachable" and "Stille (1999b:57f)" in lit("U 784")
# the language test judged only some of the fifteen
TESTED = [s for s in STONES if s in SP]
assert len(TESTED) == 8 and sorted(s for s in KEEP if s in SP) == ["U 784"]
assert SP["Sm 47"]["runes"] == 10
# the language test is not infallible (as published in the cryptology article)
_sp_art = next(p for p in json.load(open(os.path.join(ROOT, "web", "content", "articles.json"), encoding="utf-8"))["posts"]
               if p["slug"] == "hur-spraklik-ar-en-runfoljd")
assert "kallar Rundatas egna anteckningar 9 av de 27 som inte liknar språk för nonsensinskrifter" in _sp_art["body"]
assert _sp_art["title_en"].startswith("Interpret, he who can")
# words and stones the reviewer checked
from api.rundata import store as _store  # noqa: E402
_by2 = {r["signum"]: r for r in _store().inscriptions}
assert [r["signum"] for r in _store().inscriptions if "þikra" in (r.get("normalization") or "")] == ["Ög 60"]
assert "<þikra>" in _by2["Ög 60"]["normalization"]
assert _by2["Sm 47"]["dating"] == "V/M eller sentida?"
assert all(st["scan"].lower().startswith(("none", "no")) for st in L["stones"] if st["signum"] in STONES)
assert row("U 765", "hans")["carved"] == "a-s" and row("U 765", "hans")["fill"] == "n"
assert "36 %" in json.dumps(L["reconcile"], ensure_ascii=False) or "0.36" in json.dumps(L["reconcile"], ensure_ascii=False)
assert "Rundata §Q" in lit("U Fv1946;258") or "uisiti" in lit("U Fv1946;258")
assert "osäker" in lit("Sö 23")
assert "det är naturligtvis omöjligt att tolka" in lit("Öl 57")
assert "två stenar" in lit("Öl 57") or "two stones" in json.dumps(LIT["Öl 57"], ensure_ascii=False)

# ---- photos -----------------------------------------------------------------------------------------------------------
FILES = commons.wikidata_files(["Sö 245", "U 466", "U Fv1946;258"])
INFO = commons.commons_info([FILES[s] for s in FILES])
CREDIT = {"Sö 245": ("Erik Brate", "Public domain"), "U 466": ("HannaEF", "CC BY-SA 4.0"), "U Fv1946;258": ("Hedning", "CC BY-SA 3.0")}
KIND = {"Sö 245": ("Runstenen", "The runestone"), "U 466": ("Runstenen", "The runestone"), "U Fv1946;258": ("Berghällen", "The rock carving")}


def photo(signum: str, text: str, lang: str = "sv") -> str:
    img = {**INFO[FILES[signum]], "signum": signum}
    assert (img["author"], img["licence"]) == CREDIT[signum], (signum, img["author"], img["licence"])
    cap = commons.caption(img, lang)
    word = "Foto" if lang == "sv" else "Photo"
    assert cap.startswith(f"{signum}. {word}: ")
    alt = f"{KIND[signum][0 if lang == 'sv' else 1]} {signum}"
    return f"![{alt}]({img['thumb']})\n{text} {word}: {cap[len(signum) + len(word) + 4:]}"


PH_SO245 = photo("Sö 245", "Sö 245 vid Tungelsta, fotograferad av Erik Brate år 1900. I luckan efter ma föreslår modellen runan k, som här står för g: mag – samma ord som Runor-redaktionen redan fört in.")
PH_U466 = photo("U 466", "U 466 vid Tibble. Utgåvan: ”Inskriften ger ingen språklig mening.” Modellen fyller ändå i ok i en av luckorna.")
PH_FV1946 = photo("U Fv1946;258", "Berghällen vid Fällbro, U Fv1946;258. Där Sven B. F. Jansson 1946 anade ristarens namn föreslår modellen viseti.")
PH_SO245_EN = photo("Sö 245", "Sö 245 at Tungelsta, photographed by Erik Brate in 1900. In the gap after ma the model proposes the k-rune, which stands for g here: mag – the word the Runor editors have already entered.", "en")
PH_U466_EN = photo("U 466", "U 466 at Tibble. The edition: “The inscription gives no linguistic meaning.” The model still fills in ok in one of the gaps.", "en")
PH_FV1946_EN = photo("U Fv1946;258", "The rock carving at Fällbro, U Fv1946;258. Where Sven B. F. Jansson in 1946 sensed the carver's name, the model proposes viseti.", "en")


def raw_txt(x: float, sw: bool) -> str:
    v = ">99" if x >= 0.995 else str(pct(x))
    return f"rå {v} %" if sw else f"raw {v} %"


def chart(lang: str) -> str:
    sw = lang == "sv"
    best = {}
    for c in rs_rows:
        if c["signum"] not in best or c["p"] > best[c["signum"]]["p"]:
            best[c["signum"]] = c
    meaningless = list(NONSENSE) + ["U Fv1976;108"]
    lines = [f":::chart {'Modellens förslag i öppna luckor på runstenar, kalibrerat' if sw else 'The model’s proposals in open gaps on runestones, calibrated'}",
             f"# {'Utgåvan tar inte ställning till om texten är språk' if sw else 'The edition does not question that the text is language'}"]
    for s in sorted(best, key=lambda s: -best[s]["p"]):
        if s in meaningless:
            continue
        c = best[s]
        lines.append(f"{'+' if s in KEEP else ''}{s} {c['word']} | {pct(c['p'])} | {raw_txt(c['p_model'], sw)}")
    lines.append(f"# {'Utgåvan: ingen språklig mening, eller kanske ingen' if sw else 'The edition: no linguistic meaning, or perhaps none'}")
    for s in sorted(meaningless, key=lambda s: -best[s]["p"]):
        c = best[s]
        if s in SP:
            v = SP[s]["verdict"] if sw else {"inte språk": "not language", "runrad": "rune row"}[SP[s]["verdict"]]
            note = f"{'språkprovet' if sw else 'language test'}: {v}"
        else:
            note = "för kort för språkprovet" if sw else "too short for the language test"
        lines.append(f"{s} {c['word']} | {pct(c['p'])} | {note}")
    lines.append("Källa: Vitkis sannolikhetsmodell (textmodel-19), kalibrerad lista 2026-10-23; utgåvorna i Sveriges runinskrifter och senare publikationer; språkprovet låst 2026-10-16. Markerade rader är de som står kvar när allt vägts samman." if sw else
                 "Source: Vitki's probability model (textmodel-19), calibrated list 2026-10-23; the editions in Sveriges runinskrifter and later publications; the language test locked on 16 October 2026. Highlighted rows are those left standing when everything is weighed together.")
    lines.append(":::")
    return "\n".join(lines)


CHART, CHART_EN = chart("sv"), chart("en")
P = lambda s, w: pct(row(s, w)["p"])  # noqa: E731
U525 = sorted(pct(c["p"]) for c in C["candidates"] if c["signum"] == "U 525")
SURE = sorted((c for c in rs_rows if c["p"] >= 0.8), key=lambda c: -c["p"])
assert [(c["signum"], c["word"]) for c in SURE] == [("U 765", "hans"), ("Sm 47", "þikra"), ("U 784", "ok"), ("Öl 57", "ræisa"),
                                                    ("U 1180", "risti"), ("Öl ATA4377/56A", "ok"), ("Öl ATA4701/43", "ok")]
kept_sv = ", ".join(KEEP[:-1]) + " och " + KEEP[-1]
kept_en = ", ".join(KEEP[:-1]) + " and " + KEEP[-1]
words_sv = ", ".join(KEEP_WORDS[:-1]) + " och " + KEEP_WORDS[-1]
words_en = ", ".join(KEEP_WORDS[:-1]) + " and " + KEEP_WORDS[-1]

title = "Vad stod i luckan? Två modeller håller varandra i schack"  # Viktor 2026-10-25; tidigare "Tre punkter i texten"
summary = ("Där en runa saknas sätter utgivarna ett streck, och där de inte vågar tolka ordet skriver de tre punkter. Vi lät vår "
           "egen sannolikhetsmodell föreslå ord i just de luckorna och prövade förslagen mot utgåvorna och, där det gick, mot en "
           "andra modell. Resultatet är mindre än vi hoppades och bättre än vi fruktade: där forskare redan vågat ett förslag "
           "landar modellen ofta på samma ord, och där den fyller i ord i inskrifter som inte är språk säger den andra modellen ifrån.")
title_en = "What Stood in the Gap? Two Models Keep Each Other in Check"
summary_en = ("Where a rune is missing, the editors put a dash, and where they do not dare to interpret the word, they write three "
              "dots. We let our own probability model propose words in exactly those gaps and tested the proposals against the "
              "editions and, where possible, against a second model. The result is smaller than we hoped and better than we "
              "feared: where scholars have already ventured a proposal, the model often lands on the same word, and where it fills "
              "in words in inscriptions that are not language, the second model objects.")

body = f"""Den som läser en runinskrift i en utgåva möter förr eller senare tre punkter. Där en runa har flagnat bort, där stenen har spruckit eller där en ritning från 1600-talet inte går att lita på, sätter utgivaren ett streck för varje runa som fattas. Och där de runor som finns kvar inte räcker för att säga vilket ord det var, står det i tolkningen bara ”…”. Punkterna är inte slarv. De är ett beslut. En runolog har stått framför stenen, sett vad som finns kvar och valt att inte gissa.

Vi har byggt en sannolikhetsmodell som gör precis det som runologen avstod från: den föreslår vad som kan ha stått där. Den är vår egen, den är ny, och ingen utanför Vitki har ännu granskat den. Det är därför den här artikeln handlar lika mycket om hur vi prövade förslagen som om förslagen själva. Vi påstår inte att något av orden nedan är fakta. Vi visar vad modellen säger, vad utgåvorna säger, och var de möts.

## Vad modellen föreslår

Inventeringen gick igenom {RS['gaps_inventoried']} luckor på vikingatida runstenar. {RS['open']} av dem har utgivarna lämnat öppna. I {RS['candidates']} av de öppna, på {RS['stones']} stenar, föreslår modellen ett ord ur sitt ordförråd med minst 50 procent kalibrerad sannolikhet, och i {RS['sure']} med minst 80 procent. Kalibrerad betyder att siffran är prövad på luckor där svaret redan är känt: när modellen säger 80 procent har den där haft rätt ungefär åtta gånger av tio. Modellens egen, okalibrerade siffra är ofta högre, och den står som ”rå” i diagrammet nedan.

Ett första mönster syns direkt: modellen är som säkrast där den behövs minst. Bland de sju förslagen på minst 80 procent står ok tre gånger, hans, ræisa och risti – formelord som varje runolog kan gissa och som utgivarna ändå lämnat öppna, oftast för att runorna inte syns – och þikra på Sm 47, som vi återkommer till. Det är mindre spännande än nya namn. Men det är också vad en ärlig modell ska göra: vara säkrast där mönstret är starkast.

## Vad utgåvorna säger

Vi läste vad utgåvorna skriver om varje lucka på runstenarna: Sveriges runinskrifter, Fornvännen, Nytt om runer och, för Öland, Magnus Källströms nyläsning i Futhark. En andra läsare gick sedan igenom varje påstående och försökte motbevisa det. Utgåvorna är sällan tysta. I de flesta fall har utgivaren sett luckan, beskrivit vad som syns och avstått från att fylla den.

På U 765 skriver utgåvan om runan i luckan: ”Av r. 12 återstår hst och möjligen spår av en bst t. v. om hst.” – en huvudstav och kanske spår av en bistav. Modellen fyller i n, så att det står ans, och läser det som hans; att h saknas godtar den, eftersom ristare ibland utelämnade det. Men utgåvans slutsats står kvar: ”Inskriften är tyvärr alltför skadad för att tillåta ett tolkningsförslag.” Listan säger {P('U 765', 'hans')} procent, men stenanalysen, som läser hela stenen på en gång, bara 36. Det är ett förslag som går att pröva på stenens fragment i Enköpings museum, inte ett svar.

{PH_SO245}

På Sö 245 vid Tungelsta föreslår modellen mag, ”måg”, med {P('Sö 245', 'mag')} procent. Rundata lämnar luckan öppen, men RAÄ:s nyare databas Runor har redan fört in samma ord: *ma[g] sinn*, med anteckningen ”Tolkad av redaktionen”. Modellen har aldrig sett den läsningen. Den kom fram till samma ord på egen hand, ur runorna och ur hur runstenarnas texter brukar vara formulerade.

## Fem stenar som inte talar

Det andra mönstret är det viktigaste. Fem av de {RS['stones']} stenarna har inskrifter som utgåvorna inte läser som språk alls:

- **U 466** vid Tibble: ”Inskriften ger ingen språklig mening.”
- **U 493** vid Brunnby, känd bara från Peringskiölds teckningar och träsnitt från 1684: ”Inskriften ger ingen språklig mening.”
- **U 522**, en rund sandstensplatta från Hammarby: en inskrift ”som icke ger någon språklig mening” och som slutar med runraden.
- **U 1180** vid Åby: ”ytterligare ett exempel på inskrifter, som icke ha någon språklig innebörd.”
- **Sm 47** vid Håringe: runorna ”ge ingen sammanhängande inskrift med någon mening i”. Stenen kan dessutom vara medeltida eller yngre.

{PH_U466}

Ändå fyller modellen i ord där: risti med {P('U 1180', 'risti')} procent, þikra med {P('Sm 47', 'þikra')} – en runföljd som bara finns otolkad på en annan sten, Ög 60 – vaR med {P('U 493', 'vaR')}, ok med {P('U 466', 'ok')} och ett namn med {P('U 522', 'heðingunnr')}. Den är byggd för att hitta språk, och den hittar språk också där det inte finns något. Den vet inte att en ristare ibland högg runor utan att skriva ord – som prydnad, som runrad, kanske som magi.

Men Vitki har en andra modell, som gör det motsatta. Språkprovet, som vi beskrev i [Tyde den som kan](/artiklar/hur-spraklik-ar-en-runfoljd/), mäter hur språklik en runföljd är: hur väl den kan förutsägas av en modell tränad på tolkade inskrifter, jämfört med riktiga texter klippta i samma längder och med samma runor i slumpvis ordning. Provets regler låstes den 16 oktober, med en rättelse av underlaget den 17 oktober, innan den här artikeln var tänkt. Det har bedömt alla fem: U 1180, U 493 och Sm 47 som ”inte språk”, U 466 och U 522 som ”runrad”, vilket betyder att minst sex runor står i futharkens ordning. Det är just de fem som utgåvorna kallar meningslösa. Tre andra stenar i listan, U 784, U 246 och Öl ATA4377/56A, bedömer provet som språklika, och där säger utgåvorna inget om att texten skulle sakna mening. De tre har, liksom Sm 47, bara tio läsbara runor, det minsta provet godtar, så de bedömningarna är svagare.

Provet är inte ofelbart. Bland alla otolkade runstenar kallar det 27 ”inte språk”, och bara 9 av dem har Rundatas egna anteckningar kallat nonsensinskrifter. Det har heller bara kunnat bedöma {len(TESTED)} av de {RS['stones']} stenarna här; de andra är för korta eller redan delvis tolkade. Men där det säger ifrån, gör det det på rätt ställen.

En sjätte sten kan höra hit. U Fv1976;108 står vid Tibble, några meter från U 466, och utgivaren Helmer Gustavson skrev 1976 att inskriften ”möjligen har … aldrig givit någon språklig mening, utan varit en imitation av inskriften på en runsten”. Modellen föreslår sinn där, med {P('U Fv1976;108', 'sinn')} procent. Stenen har för få läsbara runor för språkprovet.

Två modeller som håller varandra i schack: den ena fyller i, den andra säger var det inte finns något att fylla. Det är, tror vi, det mest användbara vi har lärt oss av det här arbetet.

{CHART}

## Där stenen säger emot

På U 525 vid Österlisa, tre fragment av samma sten, föreslår modellen ett ortnamn, hiortstaðum, med {U525[0]}–{U525[-1]} procent i de tre luckorna. Det vore ett fint fynd: en gård vars namn började på Hjort-. Men det huggna börjar med au, inte hio, så ordet passar bara därför att modellen tillåter vissa avvikelser i stavningen. Och utgåvan har beskrivit vad som syns: ”Runan 35 har möjligen varit k” och ”Runan 38 förefaller att ha varit ett i”. Modellen behöver andra runor på båda ställena. Den utgår från de runor som saknas, inte från spåren som utgivaren såg. Här säger stenen emot, och då väger stenen tyngre.

På U 246 vid Mällösa, ett fragment inmurat i en källarvägg, föreslår modellen sinn med {P('U 246', 'sinn')} procent. Utgåvan ser efter den tredje runan ”ett kort lodrätt streck, som kan vara ett sk, eller möjligen rest av en hst” – ordet kan alltså fortsätta efter luckan. En äldre läsare tog dessutom ordet före eftiR som slutet av ”sten”. Förslaget är inte omöjligt, men utgåvan ger det inget stöd.

På Öl ATA4377/56A i Hulterstads kyrka föreslår modellen ok med {P('Öl ATA4377/56A', 'ok')} procent. Ingen utgåva tolkar stället, men en senare arkivläsning har ett annat tecken där modellen sätter r, och läser runan före som en del av en binderuna. Också där går läsningen av stenen före.

På Öl 57 vid Källa föreslår modellen ræisa i slutet av inskriften, med {P('Öl 57', 'ræisa')} procent. Magnus Källström har pusslat ihop stenens fragment och läser den som ”… lēt rētta stæin þe[nna] …” – resformeln står redan tidigare i inskriften, så ett andra ”resa” på slutet vore oväntat. Om de runor som var kända före hans nyläsning, just slutet, skrev han att ”det är naturligtvis omöjligt att tolka”. En äldre anteckning antyder visserligen att fragmenten kan komma från två stenar. Men modellen läser Rundatas äldre text och saknar i vilket fall det sammanhang som nyläsningen ger.

## Andra föremål

Listan tar också med inskrifter som inte är runstenar, och dem räknar vi för sig: två berghällar, en gravhäll, två runben, två metallbleck – det ena en amulett – och en skifferbit. Dem har vi inte granskat lika noggrant som runstenarna, och för kopparblecket Öl Fv1976;96A har vi inte läst utgåvan alls. Men där finns två av de tydligaste överensstämmelserna, båda med förbehåll.

{PH_FV1946}

På berghällen vid Fällbro, U Fv1946;258, skrev Sven B. F. Jansson 1946: ”I runföljden 68—73 finnas måhända spår av ristarens namn.” Han tillskrev hällen ristaren Visäte på andra grunder. I just de runorna föreslår modellen viseti, med {P('U Fv1946;258', 'viseti')} procent. Överensstämmelsen är dock inte helt oberoende: Rundatas andra läsning av hällen har redan namnet Viseti, och modellen väger in ristarnamn från stenar i närheten.

På berghällen Sö 23 på Mörkö, som skadades av eld redan före 1600-talet och där just det här partiet bara finns i Bureus ritning, tyder utgåvan med reservation slutet som ”Gud hjälpe ande och själ!”. Modellen fyller i and, ande, med {P('Sö 23', 'and')} procent – samma ord, men den placerar det annorlunda än utgåvan och utelämnar hjälpe.

Amuletten från Alsnö hus, U NOR1994;26A, visar en annan gräns. Där föreslår modellen fængit med {P('U NOR1994;26A', 'fængit')} procent. Men tecknen som modellen fyller är inte förlorade runor. De är ristade tecken som ingen har kunnat identifiera, och Rundata kallar inskriften ”Nonsensinskrift, magisk?”. Modellen behandlar ett oidentifierat tecken som en tom plats. Det ska vi ändra.

## Vad vi har på fötterna

Här är det vi kan stå för:

- **Modellen är prövad där svaret är känt.** På luckor som utgivarna själva har fyllt hade den rätt i 16 av 21 i ett blindtest som låstes i förväg, och alla 13 förslag där den sade sig vara minst 95 procent säker höll. Blindtestet gjordes med en tidigare version av modellen.
- **Där forskare har vågat ett förslag hamnar den ofta på samma ord** – mag på Sö 245, och med förbehåll viseti vid Fällbro och ande på Sö 23 – utan att ha sett deras läsningar.
- **Den vet inte när en text saknar mening,** men språkprovet säger ifrån. Av de stenar provet kunde bedöma kallade det just de fem som utgåvorna kallar meningslösa för inte språk eller runrad.

Och det här kan vi inte stå för:

- **De öppna luckorna är svårare än de luckor den prövats på.** Utgivarna lämnade dem öppna av goda skäl, ofta för att stenen är skadad just där. Siffrorna kan vara för höga i dem.
- **Modellen ser inte stenen.** Där utgåvan beskriver spår som talar emot, som på U 525, går spåren före. Ingen av de femton stenarna finns bland de öppna 3D-skanningar vi har tillgång till.
- **Den saknar sammanhang som en runolog har,** som Källströms nyläsning av Öl 57.

När allt vägs samman står {len(KEEP)} stenar kvar där inget i de utgåvor vi kunnat läsa talar emot förslaget: {kept_sv}. Orden är {words_sv}. För U 784 kommer läsningen av själva luckan från en senare avhandling som vi inte har kunnat läsa. Det är ingen lista över nya fynd. Det är en lista över var en runolog med stenen framför sig skulle kunna avgöra saken – med ett förslag att pröva och en siffra som säger hur säkert det är.

## Pröva själv

Under *Forskningsluckor* i Vitki finns listan med alla förslag, den kalibrerade och den råa siffran, Rundatas beteckning på föremålet och ett svenskt översättningsutkast av modellens läsning. Utkastet är ord för ord ur en ordlista som modellen lärt sig av Rundatas egna översättningar, och ord den inte kan översätta står kvar på fornspråk. Öppna en sten, läs vad utgåvan skriver om luckan och se om du håller med modellen. Ofta gör man inte det, och det är just därför det är värt att pröva.

:::box Det viktigaste i korthet
- Utgivarnas tre punkter är ett beslut att inte gissa. Vår modell gissar, och därför måste varje förslag prövas mot vad utgåvan faktiskt såg på stenen.
- Där forskare redan vågat ett förslag hamnar modellen ofta på samma ord, utan att ha sett läsningen. Det stämmer med blindtestet, som gjordes på en tidigare version av modellen och är det starkaste stödet vi har.
- Modellen hittar språk också där det inte finns något, men en andra modell, språkprovet, säger ifrån just vid de inskrifter som utgåvorna kallar meningslösa. Tillsammans är de mer att lita på än var för sig.
- Det som återstår är formelord på {len(KEEP)} stenar: inga nya namn, men en kort lista över var stenen själv kan avgöra saken.
:::

:::box Så gjorde vi
Listan är Vitkis inventering av luckorna i Rundatas vikingatida inskrifter med sannolikhetsmodellen textmodel-19, där modellen inte har tränats på den sten den läser. Varje förslag är kalibrerat mot luckor som utgivarna själva fyllt (METHODS.md 8.1 och 14); vi visar förslag med minst 50 procent. Runstenar och andra föremål räknas för sig. För varje lucka på runstenarna läste vi det som gick att nå av utgåvorna, och en andra granskare försökte motbevisa varje påstående om vad de säger; för några finns bara opublicerade arkivrapporter eller en avhandling som vi inte har kunnat läsa. Språkprovets regler (kryptologins mått på hur förutsägbar en runföljd är, jämfört med verkliga och omkastade texter av samma längd) låstes 2026-10-16 och ändrades inte för den här artikeln. Inga nya statistiska test görs här; siffrorna beskriver.
:::

## Källor

- Samnordisk runtextdatabas, version 3.1 (ODbL), och Riksantikvarieämbetets runregister Runor (2020).
- Sveriges runinskrifter: Ölands (bd 1), Östergötlands (bd 2), Södermanlands (bd 3), Smålands (bd 4) och Upplands runinskrifter (bd 6–9). Stockholm 1900–1961.
- Gustavson, H. 1976. Runfynd 1975. *Fornvännen* 71, s. 96 ff. (Tibble s. 108–109).
- Jansson, S. B. F. 1946. Några okända uppländska runinskrifter. *Fornvännen* 41, s. 257–280 (Fällbro s. 259–260).
- Källström, M. 2020. En återuppstånden runsten från Källa ödekyrka på Öland (Öl 57). *Futhark* 9–10, s. 179–191.
- *Nytt om runer* 9 (1994), s. 26.
- Foton: se bildtexterna."""

body_en = f"""Anyone who reads a runic inscription in an edition sooner or later meets three dots. Where a rune has flaked away, where the stone has cracked, or where a seventeenth-century drawing cannot be trusted, the editor puts a dash for each missing rune. And where the runes that remain are not enough to say which word it was, the interpretation just reads “…”. The dots are not carelessness. They are a decision. A runologist has stood in front of the stone, seen what is left, and chosen not to guess.

We have built a probability model that does exactly what the runologist refrained from: it proposes what may have stood there. It is our own, it is new, and no one outside Vitki has yet examined it. That is why this article is as much about how we tested the proposals as about the proposals themselves. We do not claim that any of the words below are facts. We show what the model says, what the editions say, and where they meet.

## What the model proposes

The inventory went through {RS['gaps_inventoried']} gaps on Viking-age runestones. {RS['open']} of them the editors have left open. In {RS['candidates']} of the open ones, on {RS['stones']} stones, the model proposes a word from its vocabulary with at least 50 per cent calibrated probability, and in {RS['sure']} with at least 80 per cent. Calibrated means that the figure has been tested on gaps where the answer is already known: when the model says 80 per cent, it has been right there about eight times out of ten. The model's own, uncalibrated figure is often higher, and it appears as “raw” in the chart below.

A first pattern shows at once: the model is surest where it is needed least. Among the seven proposals of at least 80 per cent, ok appears three times, with hans, ræisa and risti – formula words that any runologist can guess and that the editors still left open, mostly because the runes are not visible – and þikra on Sm 47, to which we will return. That is less exciting than new names. But it is also what an honest model should do: be surest where the pattern is strongest.

## What the editions say

We read what the editions write about every gap on the runestones: Sveriges runinskrifter, Fornvännen, Nytt om runer and, for Öland, Magnus Källström's new reading in Futhark. A second reader then went through every claim and tried to refute it. The editions are seldom silent. In most cases the editor has seen the gap, described what is visible, and refrained from filling it.

On U 765 the edition writes of the rune in the gap: “Av r. 12 återstår hst och möjligen spår av en bst t. v. om hst” – a main staff and perhaps traces of a branch. The model fills in n, so that it reads ans, and takes it as hans; it accepts the missing h because carvers sometimes left it out. But the edition's conclusion stands: “Inskriften är tyvärr alltför skadad för att tillåta ett tolkningsförslag” – the inscription is unfortunately too damaged to allow any proposed interpretation. The list says {P('U 765', 'hans')} per cent, but the stone analysis, which reads the whole stone at once, only 36. It is a proposal that can be tested on the stone's fragment in the Enköping museum, not an answer.

{PH_SO245_EN}

On Sö 245 at Tungelsta the model proposes mag, “kinsman by marriage”, with {P('Sö 245', 'mag')} per cent. Rundata leaves the gap open, but the Swedish National Heritage Board's newer database Runor has already entered the same word: *ma[g] sinn*, with the note “Tolkad av redaktionen” – interpreted by the editors. The model has never seen that reading. It reached the same word on its own, from the runes and from how runestone texts are usually phrased.

## Five stones that do not speak

The second pattern is the most important. Five of the {RS['stones']} stones have inscriptions that the editions do not read as language at all:

- **U 466** at Tibble: “Inskriften ger ingen språklig mening” – the inscription gives no linguistic meaning.
- **U 493** at Brunnby, known only from Peringskiöld's drawings and woodcut of 1684: the same words.
- **U 522**, a round sandstone plate from Hammarby: an inscription “som icke ger någon språklig mening” – which gives no linguistic meaning – and which ends with the rune row.
- **U 1180** at Åby: “yet another example of inscriptions that have no linguistic meaning”.
- **Sm 47** at Håringe: the runes “give no coherent inscription with any meaning in it”. The stone may also be medieval or later.

{PH_U466_EN}

Still the model fills in words there: risti with {P('U 1180', 'risti')} per cent, þikra with {P('Sm 47', 'þikra')} – a rune sequence found only uninterpreted on another stone, Ög 60 – vaR with {P('U 493', 'vaR')}, ok with {P('U 466', 'ok')} and a name with {P('U 522', 'heðingunnr')}. It is built to find language, and it finds language even where there is none. It does not know that a carver sometimes cut runes without writing words – as ornament, as a rune row, perhaps as magic.

But Vitki has a second model that does the opposite. The language test, which we described in [Interpret, he who can](/en/artiklar/hur-spraklik-ar-en-runfoljd/), measures how language-like a rune sequence is: how well it can be predicted by a model trained on interpreted inscriptions, compared with real texts clipped to the same lengths and with the same runes in random order. The rules of the test were locked on 16 October, with a correction of the data on 17 October, before this article was conceived. It has judged all five: U 1180, U 493 and Sm 47 as “not language”, U 466 and U 522 as “rune row”, which means that at least six runes stand in the order of the futhark. Those are exactly the five that the editions call meaningless. Three other stones in the list, U 784, U 246 and Öl ATA4377/56A, the test judges language-like, and there the editions say nothing about the text lacking meaning. Those three, like Sm 47, have only ten readable runes, the minimum the test accepts, so those judgements are weaker.

The test is not infallible. Among all uninterpreted runestones it calls 27 “not language”, and Rundata's own notes call only 9 of them nonsense inscriptions. It has also been able to judge only {len(TESTED)} of the {RS['stones']} stones here; the others are too short or already partly interpreted. But where it objects, it objects in the right places.

A sixth stone may belong here. U Fv1976;108 stands at Tibble, a few metres from U 466, and its editor Helmer Gustavson wrote in 1976 that the inscription “may never have given any linguistic meaning, but been an imitation of the inscription on a runestone”. The model proposes sinn there, with {P('U Fv1976;108', 'sinn')} per cent. The stone has too few readable runes for the language test.

Two models keeping each other in check: one fills in, the other says where there is nothing to fill. That is, we think, the most useful thing we have learned from this work.

{CHART_EN}

## Where the stone disagrees

On U 525 at Österlisa, three fragments of the same stone, the model proposes a place-name, hiortstaðum, with {U525[0]}–{U525[-1]} per cent in the three gaps. That would be a fine find: a farm whose name began with Hjort-. But the carved text begins with au, not hio, so the word fits only because the model allows certain deviations in spelling. And the edition has described what is visible: “Runan 35 har möjligen varit k” and “Runan 38 förefaller att ha varit ett i” – rune 35 may have been k, rune 38 seems to have been i. The model needs other runes in both places. It works from the runes that are missing, not from the traces the editor saw. Here the stone disagrees, and then the stone carries more weight.

On U 246 at Mällösa, a fragment built into a cellar wall, the model proposes sinn with {P('U 246', 'sinn')} per cent. After the third rune the edition sees “a short vertical stroke, which may be a divider, or possibly the rest of a main staff” – so the word may continue past the gap. An older reader also took the word before eftiR as the end of “stone”. The proposal is not impossible, but the edition gives it no support.

On Öl ATA4377/56A in Hulterstad church the model proposes ok with {P('Öl ATA4377/56A', 'ok')} per cent. No edition interprets the place, but a later archive reading has a different sign where the model puts r, and reads the rune before it as part of a bind-rune. There too the reading of the stone comes first.

On Öl 57 at Källa the model proposes ræisa at the end of the inscription, with {P('Öl 57', 'ræisa')} per cent. Magnus Källström has pieced the stone's fragments together and reads it as “… lēt rētta stæin þe[nna] …” – the raising formula already stands earlier in the inscription, so a second “raise” at the end would be unexpected. Of the runes known before his new reading, which is just the end, he wrote that “it is of course impossible to interpret”. An older note does suggest that the fragments may come from two stones. But the model reads Rundata's older text and in any case lacks the context the new reading gives.

## Other objects

The list also includes inscriptions that are not runestones, and those we count separately: two rock carvings, a grave slab, two rune bones, two metal sheets – one of them an amulet – and a piece of slate. We have not examined them as closely as the runestones, and for the copper sheet Öl Fv1976;96A we have not read the edition at all. But two of the clearest agreements are there, both with reservations.

{PH_FV1946_EN}

On the rock carving at Fällbro, U Fv1946;258, Sven B. F. Jansson wrote in 1946: “I runföljden 68—73 finnas måhända spår av ristarens namn” – in runes 68–73 there may be traces of the carver's name. He attributed the carving to the carver Visäte on other grounds. In exactly those runes the model proposes viseti, with {P('U Fv1946;258', 'viseti')} per cent. The agreement is not fully independent, though: Rundata's second reading of the carving already has the name Viseti, and the model weighs in carver names from nearby stones.

On the rock carving Sö 23 on Mörkö, damaged by fire before the seventeenth century, where this passage survives only in Bureus's drawing, the edition reads the end, with reservation, as “Gud hjälpe ande och själ!” – God help spirit and soul. The model fills in and, spirit, with {P('Sö 23', 'and')} per cent – the same word, but it places it differently from the edition and leaves out hjälpe.

The amulet from Alsnö hus, U NOR1994;26A, shows a different limit. There the model proposes fængit with {P('U NOR1994;26A', 'fængit')} per cent. But the signs the model fills are not lost runes. They are carved signs that no one has been able to identify, and Rundata calls the inscription “Nonsensinskrift, magisk?” – a nonsense inscription, magical? The model treats an unidentified sign as an empty place. We will change that.

## What we have to stand on

This is what we can stand behind:

- **The model is tested where the answer is known.** On gaps the editors themselves filled, it was right in 16 of 21 in a blind test locked in advance, and all 13 proposals where it said it was at least 95 per cent sure held. The blind test was made with an earlier version of the model.
- **Where scholars have ventured a proposal, it often lands on the same word** – mag on Sö 245, and with reservations viseti at Fällbro and ande on Sö 23 – without having seen their readings.
- **It does not know when a text lacks meaning,** but the language test objects. Of the stones the test could judge, it called exactly the five that the editions call meaningless not language or a rune row.

And this we cannot stand behind:

- **The open gaps are harder than the gaps it was tested on.** The editors left them open for good reasons, often because the stone is damaged just there. The figures may be too high in them.
- **The model does not see the stone.** Where the edition describes traces that speak against it, as on U 525, the traces come first. None of the fifteen stones is among the open 3D scans available to us.
- **It lacks context a runologist has,** such as Källström's new reading of Öl 57.

When everything is weighed together, {len(KEEP)} stones remain where nothing in the editions we have been able to read speaks against the proposal: {kept_en}. The words are {words_en}. For U 784 the reading of the gap itself comes from a later dissertation we have not been able to read. It is not a list of new finds. It is a list of where a runologist with the stone in front of them could settle the matter – with a proposal to test and a figure that says how sure it is.

## Try it yourself

Under *Research gaps* in Vitki is the list with every proposal, the calibrated and the raw figure, Rundata's term for the object, and a Swedish draft translation of the model's reading. The draft is word for word, from a glossary the model learned from Rundata's own translations, and words it cannot translate stay in Old Norse. Open a stone, read what the edition writes about the gap, and see whether you agree with the model. Often one does not, and that is exactly why it is worth trying.

:::box The essentials in brief
- The editors' three dots are a decision not to guess. Our model guesses, and so every proposal must be tested against what the edition actually saw on the stone.
- Where scholars have already ventured a proposal, the model often lands on the same word without having seen the reading. That agrees with the blind test, which was made on an earlier version of the model and is the strongest support we have.
- The model finds language even where there is none, but a second model, the language test, objects at exactly the inscriptions the editions call meaningless. Together they are more trustworthy than either alone.
- What remains are formula words on {len(KEEP)} stones: no new names, but a short list of where the stone itself can settle the matter.
:::

:::box How we did it
The list is Vitki's inventory of the gaps in Rundata's Viking-age inscriptions with the probability model textmodel-19, where the model has not been trained on the stone it reads. Each proposal is calibrated against gaps the editors themselves filled (METHODS.md 8.1 and 14); we show proposals of at least 50 per cent. Runestones and other objects are counted separately. For every gap on the runestones we read what could be reached of the editions, and a second reviewer tried to refute every claim about what they say; for a few there are only unpublished archive reports or a dissertation we have not been able to read. The language test's rules (the cryptologist's measure of how predictable a rune sequence is, compared with real and shuffled texts of the same length) were locked on 16 October 2026 and were not changed for this article. No new statistical tests are made here; the figures describe.
:::

## Sources

- Scandinavian Runic-text Database, version 3.1 (ODbL), and the Swedish National Heritage Board's runic register Runor (2020).
- Sveriges runinskrifter: the volumes for Öland (1), Östergötland (2), Södermanland (3), Småland (4) and Uppland (6–9). Stockholm 1900–1961.
- Gustavson, H. 1976. Runfynd 1975. *Fornvännen* 71, pp. 96 ff. (Tibble pp. 108–109).
- Jansson, S. B. F. 1946. Några okända uppländska runinskrifter. *Fornvännen* 41, pp. 257–280 (Fällbro pp. 259–260).
- Källström, M. 2020. En återuppstånden runsten från Källa ödekyrka på Öland (Öl 57). *Futhark* 9–10, pp. 179–191.
- *Nytt om runer* 9 (1994), p. 26.
- Photos: see the captions."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M)
assert body.count("## ") == body_en.count("## ")
VOICE = re.findall(r"[^.!?]*\b(?:jag|mig|min)\b[^.!?]*", body, re.I)
assert not VOICE, VOICE
out = {"slug": "tre-punkter-i-texten", "title": title, "summary": summary, "body": body, "title_en": title_en,
       "summary_en": summary_en, "body_en": body_en, "labels": ["Forskning", "Sannolikhetsmodellen", "Tolkning"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "tre_punkter.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "tre_punkter.json"), len(body.split()), "ord sv,", len(body_en.split()), "ord en")

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
                 "topic": "Sannolikhetsmodellen|luckor", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
