"""Artikeln "Ristarna som aldrig blev ihågkomna" (sv + en): Källströms katalog över ristarsignaturer mot Rundatas och Runor
2020:s ristarfält (utdata/signaturer/), och Vitkis försök att hitta ristarna ändå (r/anonymous.R, utdata/okanda_ristare/) –
modigt i tolkningen, tydligt i bristerna (Viktor 2026-10-29). Siffrorna låses mot signaturer.json, sri_par.json,
okanda_ristare.json och mastare_del12.json; litteraturen mot data/carver_literature.json.
    ../../../.venv/bin/python build_ristare_glomde.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import commons  # noqa: E402

FP = "3f58e9339191761e"
D = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
OK = os.path.join(ROOT, "utdata", "okanda_ristare")
AN = json.load(open(os.path.join(D, "anonymous.json"), encoding="utf-8"))
IND = json.load(open(os.path.join(OK, "okanda_ristare.json"), encoding="utf-8"))
P12 = json.load(open(os.path.join(OK, "mastare_del12.json"), encoding="utf-8"))
MOD = json.load(open(os.path.join(OK, "mastare_modell.json"), encoding="utf-8"))
LIT = json.load(open(os.path.join(ROOT, "data", "carver_literature.json"), encoding="utf-8"))
recs = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
BY = {r["signum"]: r for r in recs}
pc = lambda x: round(100 * x)  # noqa: E731
d1 = lambda x, en=False: f"{x:.1f}" if en else f"{x:.1f}".replace(".", ",")  # noqa: E731

# ---- the locked numbers -----------------------------------------------------------------------------------------------
G = {g["id"]: g for g in AN["groups"]}
cands = [g for g in AN["groups"] if g["status"] == "candidate"]
assert len(cands) == 8 and sum(1 for g in cands if g["robust"]) == 5
HO = AN["validation"]["heldout"]
assert (HO["purity"], HO["purity_geography"], HO["runs_above"], HO["runs"]) == (0.852, 0.692, 30, 30)
COV = AN["coverage"]["share_attributed"]
assert (pc(COV["U"]), pc(COV["Vg"]), pc(COV["Ög"]), round(100 * COV["Sm"], 1)) == (70, 1, 5, 1.5)
NAMES = {2: "Konungsund", 5: "Vetlanda", 6: "Kölaby", 12: "Leksberg", 13: "Husaby"}
N = {k: G[k]["n"] for k in NAMES}
assert N == {2: 28, 5: 14, 6: 13, 12: 6, 13: 6}
assert IND["holds"] == {"H1": True, "H2": False, "H3": True} and IND["holm"]["H1"] < 0.003
assert P12["part2"]["verdict"] == "håller" and P12["part2"]["H5"]["p"] < 0.005 and P12["part2"]["control"]["p"] < 1e-12
assert P12["part1"]["Kölaby"]["span"] == P12["part1"]["Konungsund"]["span"] == 32.5
DOM = {c["candidate"]: c["p"] for c in MOD["estimates"]["dom"]["candidates"]}
assert {k: pc(v) for k, v in DOM.items()} == {2: 76, 5: 98, 6: 78, 12: 94, 13: 88}
BASE = MOD["estimates"]["dom"]["base_rate"]
assert pc(BASE) == 84 and MOD["validation"]["dom_full"]["auc"] > 0.89
# Kölaby and Leksberg in the literature (data/carver_literature.json; quotes checked against the SRI text)
A = {tuple(a["stones"]): a for a in LIT["attributions"]}
assert ("Vg 181", "Vg 158") in A and ("Vg 179", "Vg 184") in A and ("Vg 11", "Vg 13", "Vg 15") in A and ("Sm 111",) in A
KOL = set(G[6]["stones"])
assert {"Vg 181", "Vg 158", "Vg 179", "Vg 184", "Vg 130", "Vg 152"} <= KOL
assert {"Vg 11", "Vg 13", "Vg 15"} <= set(G[12]["stones"]) and "Sm 111" in G[5]["stones"]
assert {"Ög 46", "Ög 233"} <= set(G[2]["stones"]) and "Ög 234" not in G[2]["stones"]
SPELL = {c["group"]: c["shared_rare"] for c in P12["part2"]["candidates"]}
assert SPELL["Kölaby"].get("æftir=eftR") == 2 and SPELL["Konungsund"].get("ræisti=rasti") == 3

Q = {s: BY[s]["normalization"].strip().replace('"', "") for s in ("Vg 181", "Vg 11", "Vg 13", "Ög 234", "Ög 233", "Sm 111")}
assert Q["Vg 181"].endswith("Havarðr(?) hiogg s[tæin].") and Q["Ög 234"].startswith("Karl ræist stæin")
assert Q["Sm 111"].endswith("Agau[tr](?) hio[gg](?).")

SIG = json.load(open(os.path.join(ROOT, "utdata", "signaturer", "signaturer.json"), encoding="utf-8"))
PAR = json.load(open(os.path.join(OK, "sri_par.json"), encoding="utf-8"))
assert (SIG["n_core"], SIG["n_missing"], SIG["n_missing_named"], SIG["n_missing_also_runor"]) == (177, 20, 13, 20)
BP = SIG["by_province"]
assert (BP["U"]["n"], BP["U"]["missing"], BP["Sö"]["missing"]) == (120, 2, 0)
OUT_US = SIG["outside_U_So"]
assert (OUT_US["n"], OUT_US["missing"]) == (38, 18)
assert (PAR["n_pairs"], PAR["same_group"], PAR["expected_from_neighbours"]) == (9, 6, 4.82) and PAR["merged_signed_carvers"]
# Signed runestones in Västergötland and Uppland: the database against Källström (the rates in the text)
import collections as _c  # noqa: E402
from src.research_gaps import is_runestone as _isr, province as _prov  # noqa: E402
_rs = [r for r in recs if _isr(r)]
_n = _c.Counter(_prov(r) for r in _rs)
_db = _c.Counter(_prov(r) for r in _rs if any(c["kind"] == "S" for c in r["carvers"]))
assert (_n["Vg"], _db["Vg"], BP["Vg"]["n"]) == (131, 1, 5) and round(_n["Vg"] / BP["Vg"]["n"]) == 26
assert round(_n["U"] / BP["U"]["n"]) == 10
MISS_NAMED = [m["signum"] for m in SIG["missing"] if m["named"]]
assert SIG["n_missing"] - SIG["n_missing_named"] == 7
assert set(MISS_NAMED) == {"G 200", "G 203", "G 276", "Vg 119", "Vg 130", "Vg 180", "Vg 181", "Ög 8", "Ög 64", "U 422",
                           "Hs 14", "M 2", "J RS1928;66"}

# ---- photographs ------------------------------------------------------------------------------------------------------
PH = ("Vg 181", "Vg 11", "Ög 234", "Sm 111")
FILES = commons.wikidata_files(list(PH))
INFO = commons.commons_info(list(FILES.values()))
LIC = {"CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/", "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/"}
for s in PH:
    assert INFO[FILES[s]]["licence"] in LIC, s


def photo(s, text, lang):
    i = INFO[FILES[s]]
    page = "https://commons.wikimedia.org/wiki/File:" + FILES[s].replace(" ", "_")
    alt = f"Runstenen {s}" if lang == "sv" else f"The runestone {s}"
    cr = (f"{'Foto' if lang == 'sv' else 'Photo'}: {i['author']}, [{i['licence']}]({LIC[i['licence']]}), "
          f"via [Wikimedia Commons]({page}).")
    return f"![{alt}]({i['thumb']})\n{text} {cr}"


def chart(lang):
    sv = lang == "sv"
    rows = [":::chart Runstenar med ristarsignatur som saknar ristare i databasen" if sv else
            ":::chart Runestones with a carver's signature but no carver in the database"]
    for p, lab in (("U", "Uppland"), ("Sö", "Södermanland"), ("_", "Övriga Sverige" if sv else "Rest of Sweden")):
        n, k = (OUT_US["n"], OUT_US["missing"]) if p == "_" else (BP[p]["n"], BP[p]["missing"])
        rows.append(f"{'+' if p == '_' else ''}{lab} | {pc(k / n)} | {k} {'av' if sv else 'of'} {n}")
    rows.append("Källa: Källström 2007 (Bilaga 1, ristarsignaturer av typ B:1–2 på runstenar) mot Samnordisk runtextdatabas "
                "(Rundata 3.1) och Runor 2020; Vitkis räkning (utdata/signaturer/jamfor.py)." if sv else
                "Source: Källström 2007 (Appendix 1, carver signatures of type B:1–2 on runestones) against the Scandinavian "
                "Runic-text Data Base (Rundata 3.1) and Runor 2020; Vitki's count (utdata/signaturer/jamfor.py).")
    return "\n".join(rows) + "\n:::"


title = "Ristarna som aldrig blev ihågkomna"
summary = (f"Utanför Uppland och Södermanland saknar rundatabasen ristaren på nästan varannan runsten som ristaren "
           f"signerade. Vi räknade, och försökte sedan hitta de glömda ristarna med en modell. Det gick halvvägs.")

body = f"""*{Q['Vg 181']}*

Gufi reste denna sten efter Olav, sin son, en mycket god *drengr*. Han blev dräpt i Estland. Håvard(?) högg stenen.

Stenen står vid Frugården i Norra Åsarp i Västergötland (Vg 181). Den sista meningen är en ristares signatur: *Havarðr hiogg stein*, Håvard högg stenen. Ändå står ingen ristare för stenen i Samnordisk runtextdatabas – inte heller i den nyare utgåvan Runor 2020. Det är den databas som nästan all statistik om runstenar bygger på. Också vår.

{photo('Vg 181', 'Vg 181 vid Frugården: Gufis sten efter sonen Olav, som dräptes i Estland. Längst ned står ristarens namn.', 'sv')}

:::box Kort sagt
- Magnus Källström har förtecknat alla vikingatida ristarsignaturer. Av de {SIG['n_core']} svenska runstenar där han räknar signaturen som säker eller trolig saknar {SIG['n_missing']} ristare i databasen – {OUT_US['missing']} av {OUT_US['n']} utanför Uppland och Södermanland, men bara {BP['U']['missing']} av {BP['U']['n']} i Uppland.
- På {SIG['n_missing_named']} av dem går namnet att läsa: Håvard, Viking och Grimulv, Lófi, Hrómundr, Tryggve, Funnen, Alrik med flera.
- All statistik om ristare utanför Mälardalen bygger alltså på ett ristarfält som är nästan tomt – också på de stenar där ristaren själv skrev sitt namn.
- Vi försökte hitta ristarna ändå med en modell. Den hittar bygdernas skrivmiljöer, men inte de enskilda ristarna. Tre grupper står kvar som frågor till runologerna.
:::

## Hälften av signaturerna saknas

Magnus Källström gick i sin avhandling *Mästare och minnesmärken* (2007) igenom varje runinskrift där någon säger att hen ristade, högg eller målade. Vi lade hans förteckning bredvid databasens ristarfält, sten för sten. Vi räknade bara runstenar med det han kallar en ristarsignatur av de säkrare slagen – en mening som *Håvard högg stenen* bredvid stenens övriga text.

{chart('sv')}

Uppland är nästan komplett: {BP['U']['missing']} av {BP['U']['n']} signerade stenar saknar ristare. Det är där forskningen om ristare har bedrivits, med Öpir, Åsmund och Balle. I övriga landskap är bilden en annan. I Västergötland saknas {BP['Vg']['missing']} av {BP['Vg']['n']}, i Östergötland {BP['Ög']['missing']} av {BP['Ög']['n']}, på Gotland {BP['G']['missing']} av {BP['G']['n']}. Viking och Grimulv på Ög 8, Lófi på Ög 64 i Bjälbo, Hrómundr på Hs 14 i Hälsingland, Tryggve på Vg 130 och Funnen på Vg 180 – alla har skrivit sitt namn på stenen, och ingen av dem finns i databasens ristarfält.

Det är ingen slump i enstaka poster. Databasens ristaruppgifter bygger till stor del på forskning om Mälardalen och har bara delvis förts in för resten av landet. Följden syns i varje statistisk studie av ristare som bygger på databasen – vår egen inräknad. I Västergötland står 1 av 131 runstenar som signerad där; enligt Källström är de 5. Uppland dominerar ändå, också med hans siffror – en av tio uppländska runstenar är signerad, mot en av tjugosex i Västergötland – så att signerandet var vanligast i Mälardalen är ingen illusion. Men databasen gör skillnaden större än den var, och när vi tidigare skrev att en procent av Västergötlands runstenar har en ristare, var det databasen vi mätte, inte vad forskningen vet.

## Kan en modell hitta dem ändå?

Om ristarna saknas i databasen kanske de syns i stenarna. En ristare lämnar spår i texten: hur hen stavade *stæin* och *æftiR*, vilka skiljetecken hen satte, vilken formel stenen inleds med. Vitki letar efter grupper av stenar utan känd ristare som hänger ihop lika tätt i de dragen som en känd ristares stenar.

I Uppland och Södermanland, där ristarna är kända, fungerar det. Med ristarna gömda var {pc(HO['purity'])} procent av en grupp samma ristares, mot {pc(HO['purity_geography'])} procent om man bara tar lika många grannstenar. Men det är just där metoden behövs minst.

Utanför Mälardalen kunde vi pröva den på det Sveriges runinskrifter säger. Utgivarna knyter på några ställen två eller tre stenar till samme ristare. Av nio sådana par, där båda stenarna finns i vår analys, hamnar {PAR['same_group']} i samma grupp. Det låter bra, men grannstenar på samma avstånd hamnar ofta i samma grupp ändå – {d1(PAR['expected_from_neighbours'])} par skulle göra det bara av närheten. Och gruppen kring Kölaby, som rymmer Håvards sten, rymmer också Vg 130, signerad av en annan ristare, Tryggve.

{photo('Vg 11', 'Vg 11 vid Leksbergs backe: Tore Skorpas sten efter sonen Kättil. Utgivarna menade att samme ristare gjort Vg 11, 13 och 15 – och vår modell lade dem i samma grupp, men också stenarna runt omkring.', 'sv')}

Så här ärligt vi kan säga det: modellen hittar skrivmiljöer, inte ristare. Grupperna delar bergart och ovanliga stavningar oftare än stenarna omkring dem – två stenar i Kölabygruppen skriver *eftR* för *æftiR*, tre i en grupp kring Konungsund skriver *rasti* för *ræisti* – och det är ett tecken på något verkligt: en verkstad, en skola, en bygds sätt att skriva. Men en grupp kan rymma flera händer, och vi kan inte se var gränsen går.

## Tre frågor till runologerna

Tre grupper finns inte beskrivna som en ristares verk i Sveriges runinskrifter eller hos Källström. Vi kallar dem inte nya ristare. Vi ställer frågorna, och vi tror att de är värda att ställa.

**Konungsund (Östergötland, {N[2]} stenar).** Erik Brate tillskrev två av stenarna, Ög 46 och Ög 233, samme ristare. Vid Östra Stenby kyrka, bredvid Ög 233, står Ög 234: *{Q['Ög 234']}* Karl ristade – eller reste – denna sten efter Åsmund, sin bror. Om *ræist* betyder ristade eller är en förkortning av reste har ingen kunnat avgöra (Källström 2007, s. 85 ff.). Karls sten ingår inte i gruppen, men bland de tre stenar i gruppen som liknar den mest finns just Ög 233 och Ög 46. Vår gissning: Karl var ristaren bakom Vebjörns två stenar. Den kan prövas på stenarna själva – huggspår och runformer.

{photo('Ög 234', 'Ög 234 vid Östra Stenby kyrka: ”Karl ræist stæin” – ristade eller reste Karl stenen?', 'sv')}

**Vetlanda (Småland, {N[5]} stenar).** Fjorton stenar som liknar varandra mycket, men som inte delar något utöver det de grupperats på – varken bergart, namn eller ovanliga stavningar. På en av dem, Sm 111 vid Fageräng, slutar texten med en skadad runföljd. Ragnar Kinander läste den som en bön; senare läsningar ser en signatur, *aku- hio[gg]*, någon högg (Källström 2007, s. 342). Om signaturen står sig har Njudung en ristare till.

**Husaby (Västergötland, {N[13]} stenar).** Sex stenar på Kinnekulle, utan någon anmärkning i litteraturen och utan något som binder dem utöver texten. Den tystaste gruppen – och därför den som behöver en runologs ögon mest.

## Så säkra är vi

:::box Så säkra är vi
- **Det vi visar:** att databasen saknar ristaren på {SIG['n_missing']} av {SIG['n_core']} signerade runstenar, och på {OUT_US['missing']} av {OUT_US['n']} utanför Uppland och Södermanland. Det är en räkning, inte en modell – Källströms förteckning mot databasens fält, sten för sten. Vi har tagit med bara de signaturer han räknar till de säkrare slagen. På sju av de saknade är namnet bortslaget, och några namn är osäkert lästa – Håvard och Tryggve skrivs med frågetecken.
- **Det vi tror:** att modellens grupper fångar verkliga skrivmiljöer. Bergarten och de ovanliga stavningarna talar för det, i tester som låstes innan de kördes.
- **Det vi inte kan visa:** att grupperna är enskilda ristare. Utanför Mälardalen hamnar stenar som litteraturen knyter till samme ristare i samma grupp knappt oftare än grannar gör ({PAR['same_group']} av 9 mot {d1(PAR['expected_from_neighbours'])}), och en grupp slår ihop två signerade ristare.
- **Det vi inte har läst:** Laila Kitzler Åhfeldts studier av huggtekniken och Per Stilles om attribuering kan säga mer om grupperna.
:::

:::box Det viktigaste i korthet
- Databasen som runstatistiken bygger på vet mindre än forskningen: utanför Uppland och Södermanland saknar den ristaren på nästan varannan runsten som ristaren signerade.
- Ristarna signerade oftast i Uppland – det håller. Men databasen gör skillnaden större än den var, och den som räknar ristare utanför Mälardalen räknar luckor i databasen.
- En modell kan hitta bygdernas skrivmiljöer i stenarna, men inte – ännu – de enskilda händerna.
- Nästa gång du läser en runsten: titta efter sista meningen. *Hiogg*, *risti*, *fáði* – där står ibland den som höll minnet vid liv åt andra, men som själv aldrig blev ihågkommen.
:::

## Källor

- Samnordisk runtextdatabas (Rundata 3.1), Institutionen för nordiska språk, Uppsala universitet. Open Database License. Runor 2020, Riksantikvarieämbetet.
- Källström, Magnus 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden*. Stockholms universitet. Bilaga 1, s. 333 ff.; s. 85 ff., 342.
- Jungner, Hugo & Svärdström, Elisabeth 1940–70. *Västergötlands runinskrifter* (Sveriges runinskrifter V), s. 20, 25, 29, 250 f., 296, 323–331.
- Brate, Erik 1911–18. *Östergötlands runinskrifter* (Sveriges runinskrifter II), s. 217.
- Kinander, Ragnar 1935–61. *Smålands runinskrifter* (Sveriges runinskrifter IV), s. 249.
- Vitkis räkning, metod och de låsta planerna ligger öppet på [GitHub](https://github.com/Precatio/runes).
- Foton: Wikimedia Commons, med fotograf och licens i bildtexterna."""

title_en = "The carvers no one remembered"
summary_en = ("Outside Uppland and Södermanland, the runic database lacks the carver on nearly every other runestone that "
              "the carver signed. We counted, and then tried to find the forgotten carvers with a model. We got halfway.")

body_en = f"""*{Q['Vg 181']}*

Gufi raised this stone in memory of Ólafr, his son, a very good *drengr*. He was killed in Estonia. Hávarðr(?) cut the stone.

The stone stands at Frugården in Norra Åsarp in Västergötland (Vg 181). The last sentence is a carver's signature: *Havarðr hiogg stein*, Hávarðr cut the stone. Yet no carver is given for the stone in the Scandinavian Runic-text Data Base – nor in the newer edition, Runor 2020. It is the database that nearly all statistics on runestones rest on. Ours too.

{photo('Vg 181', 'Vg 181 at Frugården: Gufi’s stone for his son Ólafr, who was killed in Estonia. At the bottom stands the carver’s name.', 'en')}

:::box In short
- Magnus Källström has listed every Viking-age carver's signature. Of the {SIG['n_core']} Swedish runestones where he counts the signature as certain or likely, {SIG['n_missing']} have no carver in the database – {OUT_US['missing']} of {OUT_US['n']} outside Uppland and Södermanland, but only {BP['U']['missing']} of {BP['U']['n']} in Uppland.
- On {SIG['n_missing_named']} of them the name can be read: Hávarðr, Víkingr and Grímulfr, Lófi, Hrómundr, Tryggvi, Fundinn, Alríkr and more.
- All statistics on carvers outside the Mälaren region thus rest on a carver field that is nearly empty – even on the stones where the carver wrote his own name.
- We tried to find the carvers anyway with a model. It finds the districts' writing milieus, but not the individual carvers. Three groups remain as questions for runologists.
:::

## Half the signatures are missing

In his dissertation *Mästare och minnesmärken* (2007), Magnus Källström went through every runic inscription in which someone says that he carved, cut or painted. We laid his list beside the database's carver field, stone by stone. We counted only runestones with what he calls a carver's signature of the more certain kinds – a sentence such as *Hávarðr cut the stone* beside the stone's other text.

{chart('en')}

Uppland is nearly complete: {BP['U']['missing']} of {BP['U']['n']} signed stones lack a carver. That is where research on carvers has been done, with Œpir, Ásmundr and Balli. Elsewhere the picture is different. In Västergötland {BP['Vg']['missing']} of {BP['Vg']['n']} are missing, in Östergötland {BP['Ög']['missing']} of {BP['Ög']['n']}, on Gotland {BP['G']['missing']} of {BP['G']['n']}. Víkingr and Grímulfr on Ög 8, Lófi on Ög 64 at Bjälbo, Hrómundr on Hs 14 in Hälsingland, Tryggvi on Vg 130 and Fundinn on Vg 180 – all wrote their names on the stone, and none of them is in the database's carver field.

This is no accident of single records. The database's carver data rest largely on research on the Mälaren region and have only partly been entered for the rest of the country. The consequence shows in every statistical study of carvers that rests on the database – ours included. In Västergötland 1 of 131 runestones is listed as signed there; according to Källström there are 5. Uppland still dominates, even with his figures – one in ten Uppland runestones is signed, against one in twenty-six in Västergötland – so that signing was most common in the Mälaren region is no illusion. But the database makes the difference larger than it was, and when we wrote earlier that one per cent of Västergötland's runestones have a carver, it was the database we measured, not what research knows.

## Can a model find them anyway?

If the carvers are missing from the database, perhaps they show in the stones. A carver leaves traces in the text: how he spelled *stæin* and *æftiR*, which word dividers he used, which formula the stone opens with. Vitki looks for groups of stones without a known carver that hang together as tightly in those traits as a known carver's stones.

In Uppland and Södermanland, where the carvers are known, it works. With the carvers hidden, {pc(HO['purity'])} per cent of a group were the same carver's, against {pc(HO['purity_geography'])} per cent if one simply takes as many neighbouring stones. But that is exactly where the method is needed least.

Outside the Mälaren region we could test it on what Sveriges runinskrifter says. In a few places the editors tie two or three stones to the same carver. Of nine such pairs where both stones are in our analysis, {PAR['same_group']} land in the same group. That sounds good, but neighbouring stones at the same distance often land in the same group anyway – {PAR['expected_from_neighbours']:.1f} pairs would do so from nearness alone. And the group around Kölaby, which holds Hávarðr's stone, also holds Vg 130, signed by another carver, Tryggvi.

{photo('Vg 11', 'Vg 11 at Leksbergs backe: Þórir Skorpa’s stone for his son Ketill. The editors held that the same carver made Vg 11, 13 and 15 – and our model put them in the same group, but also the stones around them.', 'en')}

As honestly as we can put it: the model finds writing milieus, not carvers. The groups share rock and unusual spellings more often than the stones around them – two stones in the Kölaby group write *eftR* for *æftiR*, three in a group around Konungsund write *rasti* for *ræisti* – and that is a sign of something real: a workshop, a school, a district's way of writing. But a group can hold several hands, and we cannot see where the line runs.

## Three questions for runologists

Three groups are not described as one carver's work in Sveriges runinskrifter or by Källström. We do not call them new carvers. We ask the questions, and we think they are worth asking.

**Konungsund (Östergötland, {N[2]} stones).** Erik Brate assigned two of the stones, Ög 46 and Ög 233, to the same carver. At Östra Stenby church, next to Ög 233, stands Ög 234: *{Q['Ög 234']}* Karl carved – or raised – this stone in memory of Ásmundr, his brother. Whether *ræist* means carved or is a shortening of raised, no one has been able to decide (Källström 2007, p. 85 ff.). Karl's stone is not in the group, but among the three stones in the group most like it are precisely Ög 233 and Ög 46. Our guess: Karl was the carver behind Vébjôrn's two stones. It can be tested on the stones themselves – grooves and rune forms.

{photo('Ög 234', 'Ög 234 at Östra Stenby church: “Karl ræist stæin” – did Karl carve or raise the stone?', 'en')}

**Vetlanda (Småland, {N[5]} stones).** Fourteen stones that resemble each other closely, but share nothing beyond what they were grouped on – neither rock, names nor unusual spellings. On one of them, Sm 111 at Fageräng, the text ends in a damaged sequence of runes. Ragnar Kinander read it as a prayer; later readings see a signature, *aku- hio[gg]*, someone cut (Källström 2007, p. 342). If the signature holds, Njudung has one more carver.

**Husaby (Västergötland, {N[13]} stones).** Six stones on Kinnekulle, with no remark in the literature and nothing that binds them beyond the text. The quietest group – and therefore the one that most needs a runologist's eyes.

## How sure we are

:::box How sure we are
- **What we show:** that the database lacks the carver on {SIG['n_missing']} of {SIG['n_core']} signed runestones, and on {OUT_US['missing']} of {OUT_US['n']} outside Uppland and Södermanland. It is a count, not a model – Källström's list against the database's field, stone by stone. We included only the signatures he counts among the more certain kinds. On seven of the missing ones the name is lost, and some names are uncertain readings – Hávarðr and Tryggvi carry question marks.
- **What we believe:** that the model's groups capture real writing milieus. The rock and the unusual spellings speak for it, in tests locked before they were run.
- **What we cannot show:** that the groups are individual carvers. Outside the Mälaren region, stones that the literature ties to the same carver land in the same group barely more often than neighbours do ({PAR['same_group']} of 9 against {PAR['expected_from_neighbours']:.1f}), and one group merges two signed carvers.
- **What we have not read:** Laila Kitzler Åhfeldt's studies of carving technique and Per Stille's on attribution may say more about the groups.
:::

:::box The essentials in brief
- The database that runic statistics rest on knows less than research does: outside Uppland and Södermanland it lacks the carver on nearly every other runestone that the carver signed.
- Carvers signed most often in Uppland – that holds. But the database makes the difference larger than it was, and whoever counts carvers outside the Mälaren region is counting gaps in the database.
- A model can find the districts' writing milieus in the stones, but not – yet – the individual hands.
- Next time you read a runestone, look at the last sentence. *Hiogg*, *risti*, *fáði* – there, sometimes, stands the one who kept the memory of others alive, but was never remembered himself.
:::

## Sources

- Scandinavian Runic-text Data Base (Rundata 3.1), Department of Scandinavian Languages, Uppsala University. Open Database License. Runor 2020, Swedish National Heritage Board.
- Källström, Magnus 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden*. Stockholm University. Appendix 1, pp. 333 ff.; pp. 85 ff., 342.
- Jungner, Hugo & Svärdström, Elisabeth 1940–70. *Västergötlands runinskrifter* (Sveriges runinskrifter V), pp. 20, 25, 29, 250 f., 296, 323–331.
- Brate, Erik 1911–18. *Östergötlands runinskrifter* (Sveriges runinskrifter II), p. 217.
- Kinander, Ragnar 1935–61. *Smålands runinskrifter* (Sveriges runinskrifter IV), p. 249.
- Vitki's count, method and the locked plans are open on [GitHub](https://github.com/Precatio/runes).
- Photos: Wikimedia Commons, with photographer and licence in the captions."""

import re  # noqa: E402
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"

out = {"slug": "ristarna-som-aldrig-blev-ihagkomna", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Ristare", "Sannolikhetsmodellen"]}
path = os.path.join(ROOT, "utdata", "blogg", "ristare_glomde.json")
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
                 "topic": "Forskning|ristare", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
