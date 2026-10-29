"""Artikeln "Håvard högg stenen – ristarna som Rundata glömde" (sv + en): Vitkis grupper av stenar utan ristare jämförda
med Sveriges runinskrifter och Källström (2007). Två grupper är redan beskrivna i litteraturen – metoden hittade dem
blint – och tre står kvar som öppna frågor. Siffrorna låses mot r/anonymous.R (korpus 3f58e9339191761e) och de två
låsta planerna i utdata/okanda_ristare/ (2026-10-29); litteraturen mot data/carver_literature.json.
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
    rows = [":::chart Sannolikheten att minst tre fjärdedelar av gruppen är en hand" if sv else
            ":::chart The probability that at least three quarters of the group are one hand"]
    for k in (5, 12, 13, 6, 2):
        lab = {5: "Vetlanda (Sm)", 12: "Leksberg (Vg)", 13: "Husaby (Vg)", 6: "Kölaby (Vg)", 2: "Konungsund (Ög)"}[k]
        rows.append(f"{'+' if k in (6, 12) else ''}{lab} | {pc(DOM[k])} | {N[k]} {'stenar' if sv else 'stones'}")
    rows.append(f"{'Genomsnittlig grupp' if sv else 'Average group'} | {pc(BASE)} | {'jämförelse' if sv else 'comparison'}")
    rows.append("Källa: Vitkis mästarmodell, kalibrerad på 912 grupper av kända ristares stenar i Uppland och Södermanland. "
                "Markerade staplar: grupper som Sveriges runinskrifter redan knyter till en ristare." if sv else
                "Source: Vitki's master model, calibrated on 912 groups of known carvers' stones in Uppland and Södermanland. "
                "Highlighted bars: groups that Sveriges runinskrifter already ties to a carver.")
    return "\n".join(rows) + "\n:::"


title = "Håvard högg stenen – ristarna som Rundata glömde"
summary = ("Vi lät en modell leta efter ristare bland runstenar som saknar ristare i databasen. Två av de grupper den "
           "hittade visade sig redan finnas i Sveriges runinskrifter – med en signatur som databasen aldrig fått. "
           "Tre grupper står kvar som öppna frågor.")

body = f"""*{Q['Vg 181']}*

Gufi reste denna sten efter Olav, sin son, en mycket god *drengr*. Han blev dräpt i Estland. Håvard(?) högg stenen.

Stenen står vid Frugården i Norra Åsarp i Västergötland (Vg 181). Den sista meningen är en ristares signatur: *Havarðr hiogg stein*, Håvard högg stenen. Ändå står det ingen ristare för stenen i Samnordisk runtextdatabas, den databas som nästan all statistik om runstenar bygger på – också vår. Vi upptäckte det på omvägar, och omvägen är den här artikelns ämne.

{photo('Vg 181', 'Vg 181 vid Frugården: Gufis sten efter sonen Olav, som dräptes i Estland. Längst ned står ristarens namn.', 'sv')}

:::box Kort sagt
- Vitki letar efter grupper av runstenar utan känd ristare som liknar varandra lika mycket som en ristares stenar gör – i stavning, formler, runformer och stil.
- I Västergötland hittade modellen bland annat två grupper. När vi läste Sveriges runinskrifter visade det sig att utgivarna redan knutit flera av stenarna till samma ristare, och att en av dem är signerad av Håvard. Modellen hittade dem utan att känna till det.
- Rundatas ristarfält saknar de uppgifterna. Att {pc(COV['Vg'])} procent av Västergötlands runstenar har en ristare i databasen säger mer om databasen än om vad forskningen vet.
- Tre grupper – kring Konungsund i Östergötland, Vetlanda i Småland och Husaby på Kinnekulle – är inte beskrivna som ristargrupper i litteraturen vi läst. De är frågor till runologerna, inte upptäckter.
:::

## Att leta efter en hand

En ristare lämnar spår i texten: hur hen stavade *stæin* och *æftiR*, vilka skiljetecken hen satte, vilken formel stenen inleds med, vilka runor som brukar stå bredvid varandra. Vitki jämför varje sten utan ristare med alla andra i närheten på de dragen och letar efter grupper som hänger ihop lika tätt som en känd ristares stenar.

Det är lätt att hitta mönster som inte finns, så vi prövade metoden först där svaret är känt. Vi tog stenar med känd ristare i Uppland och Södermanland, gömde ristaren och lät metoden gruppera dem. Gränsen för vad som räknas som lika bestämdes på andra ristare än dem som prövades. I genomsnitt var {pc(HO['purity'])} procent av stenarna i en grupp samma ristares, mot {pc(HO['purity_geography'])} procent om man bara tar lika många närliggande stenar. Metoden ser alltså något mer än att grannar liknar varandra, och det höll i alla {HO['runs']} omgångar vi körde.

Men där stod vi fast. Uppland och Södermanland är de enda landskap där tillräckligt många stenar har en känd ristare för att pröva metoden: {pc(COV['U'])} procent av Upplands runstenar har en ristare i Rundata, men bara {pc(COV['Ög'])} procent i Östergötland, {d1(100 * COV['Sm'])} i Småland och {pc(COV['Vg'])} i Västergötland. Där metodens förslag var som intressantast kunde vi inte se om de stämde.

## Svaret stod redan i tryck

I Västergötland gav metoden bland annat två grupper: tretton stenar kring Kölaby, Norra Åsarp och Böne i Ulricehamnstrakten, och sex stenar kring Leksberg vid Mariestad. Vi läste vad Hugo Jungner och Elisabeth Svärdström skrev om varje sten i *Västergötlands runinskrifter*, utgåvan i serien Sveriges runinskrifter.

För Kölabygruppen hade de redan sagt det mesta. Vg 181 är signerad av Håvard. Vg 158 är ”sannolikt utförd av samme man som har signerat Vg 181”. Vg 184 ”synes vara ristad av samme man, som utfört Vg 179”. Vg 130 är signerad av en annan ristare, Tryggve. För Leksbergsgruppen skrev de att det är ”troligt, att samme ristare utfört Vg 13 och 15 samt troligen även Vg 11” – två av stenarna restes av samme man, Tore Skorpa, efter sonen Kättil.

{photo('Vg 11', 'Vg 11 vid Leksbergs backe: Tore Skorpas sten efter sonen Kättil. Utgivarna av Västergötlands runinskrifter menade att samme ristare gjort Vg 11, 13 och 15.', 'sv')}

Inget av det står i Rundatas ristarfält. Modellen kände inte till det och kunde inte ha lärt sig det, och ändå lade den stenarna i samma grupp. Det är det första beskedet vi fått om att metoden fungerar också utanför Mälardalen – och det kom från runologer som arbetade för mer än ett halvsekel sedan, med ögon, avbildningar och tålamod.

## Vad grupperna delar

Grupperna bildas på stavning och formler, så att de liknar varandra i just det bevisar ingenting. Vi prövade därför två saker som inte ingår i likheten, enligt planer som låstes innan något räknades:

- **Bergarten.** Gruppernas stenar är oftare av samma bergart än stenar från samma trakt och tid. Det gör också de kända ristarnas stenar – en ristare hämtade sin sten där han brukade.
- **Ovanliga stavningar.** Två stenar i Kölabygruppen skriver *eftR* för *æftiR*, två skriver *stein*; i Konungsundsgruppen skrivs *ræisti* som *rasti* på tre stenar. Sådana egenheter delas sällan av slump i en bygd, och de kända ristarnas stenar delar dem på samma sätt.

Vi byggde också en modell som räknar ut hur sannolikt det är att en grupp i huvudsak är en hand. Den är kalibrerad på 912 grupper som metoden bildat av kända ristares stenar, och den skiljer de rena grupperna från de blandade i nio fall av tio.

{chart('sv')}

Siffrorna säger vad en grupp med de här dragen skulle betyda i Uppland och Södermanland. Att samma samband gäller i Västergötland och Småland kan vi inte visa – men de två grupper där litteraturen redan gett svaret hamnar där man skulle vänta sig.

## Tre frågor till runologerna

Tre grupper finns inte beskrivna som en ristares verk i det vi läst: Sveriges runinskrifter för Östergötland, Småland och Västergötland, och Magnus Källströms avhandling om de signerande ristarna, *Mästare och minnesmärken* (2007). Vi kallar dem inte nya ristare. Vi ställer frågan.

**Konungsund (Östergötland, {N[2]} stenar).** Gruppen är stor – för stor för att vara en enda hand, säger modellen, men troligen en mästare med några stenar av andra. Erik Brate tillskrev redan två av stenarna, Ög 46 och Ög 233, samme ristare. Vid Östra Stenby kyrka, bredvid Ög 233, står Ög 234: *{Q['Ög 234']}* Karl ristade – eller reste – denna sten efter Åsmund, sin bror. Om *ræist* betyder ristade eller är en förkortning av reste har forskarna inte kunnat avgöra (Källström 2007, s. 85 ff.). Karls sten ingår inte i gruppen, men bland de tre stenar i gruppen som liknar den mest finns just Ög 233 och Ög 46. Var Karl ristaren bakom dem?

{photo('Ög 234', 'Ög 234 vid Östra Stenby kyrka: ”Karl ræist stæin” – ristade eller reste Karl stenen?', 'sv')}

**Vetlanda (Småland, {N[5]} stenar).** Modellen ger gruppen den högsta sannolikheten av alla, men den har inga oberoende stöd: varken bergart, namn eller ovanliga stavningar binder ihop den. På en av stenarna, Sm 111 vid Fageräng, slutar texten med en skadad runföljd. Ragnar Kinander läste den som en bön; senare läsningar ser en signatur, *aku- hio[gg]*, någon högg (Källström 2007, s. 342). Om signaturen står sig kan gruppen ha ett namn.

**Husaby (Västergötland, {N[13]} stenar).** Sex stenar på Kinnekulle, utan någon anmärkning i litteraturen. Den minsta och tystaste gruppen – och därför den som behöver en runologs ögon mest.

## Så säkra är vi

:::box Så säkra är vi
- **Prövat där svaret är känt.** På kända ristare i Uppland och Södermanland, med ristarna gömda, var {pc(HO['purity'])} procent av en grupp samma ristares, mot {pc(HO['purity_geography'])} procent för grannstenar.
- **Planerna låstes först.** Vad som skulle prövas – bergart, storlek, namn, stavningar, tid – och när det räknas som ett stöd bestämdes innan något räknades. Storleken gav inget utslag.
- **Litteraturen som facit.** Att två grupper redan finns i Sveriges runinskrifter är det starkaste belägget, och det är oberoende av oss.
- **Inte prövat där kandidaterna står.** I Östergötland, Småland och Västergötland har nästan inga stenar en känd ristare i Rundata, så metodens gräns kan inte prövas där. Sannolikheterna är lånade från Mälardalen.
:::

## Förbehåll

- En grupp kan vara en ristare, en verkstad med flera händer eller en bygds skrivsed. Metoden kan inte skilja dem åt; bergarten och stavningarna talar för en hand men bevisar den inte.
- Vi har läst Sveriges runinskrifter och Källström (2007), inte all litteratur. Laila Kitzler Åhfeldts studier av huggtekniken och Per Stilles om attribuering kan säga mer.
- Ingen av stenarna i de tre öppna grupperna är 3D-skannad, så huggspåren – det starkaste beviset för en hand – har vi inte kunnat jämföra.

:::box Det viktigaste i korthet
- Databaserna vet mindre än forskningen. Håvards signatur på Vg 181 och utgivarnas iakttagelser om samme ristare har stått i tryck i decennier men aldrig förts in i Rundatas ristarfält.
- En statistisk modell som letar efter en hand i stavning och formler hittade samma ristare som runologerna – utan att veta om dem. Det gör det värt att ta dess andra förslag på allvar.
- Konungsund, Vetlanda och Husaby är frågor, inte svar: var Karl vid Östra Stenby en ristare, och vem högg Sm 111?
- Nästa gång du läser en runsten: titta efter sista meningen. *Hiogg*, *risti*, *fáði* – där står ibland en människa som annars försvunnit.
:::

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Jungner, Hugo & Svärdström, Elisabeth 1940–70. *Västergötlands runinskrifter* (Sveriges runinskrifter V), s. 20, 25, 29, 250 f., 296, 323–331.
- Brate, Erik 1911–18. *Östergötlands runinskrifter* (Sveriges runinskrifter II), s. 217.
- Kinander, Ragnar 1935–61. *Smålands runinskrifter* (Sveriges runinskrifter IV), s. 249.
- Källström, Magnus 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden*. Stockholms universitet, s. 85 ff., 342, 350.
- Vitkis metod (r/anonymous.R), de låsta planerna och läslistan per sten ligger öppet på [GitHub](https://github.com/Precatio/runes).
- Foton: Wikimedia Commons, med fotograf och licens i bildtexterna."""

title_en = "Hávarðr cut the stone – the carvers the database forgot"
summary_en = ("We let a model search for carvers among runestones that have none in the database. Two of the groups it "
              "found turned out to be in Sveriges runinskrifter already – with a signature the database never received. "
              "Three groups remain open questions.")

body_en = f"""*{Q['Vg 181']}*

Gufi raised this stone in memory of Ólafr, his son, a very good *drengr*. He was killed in Estonia. Hávarðr(?) cut the stone.

The stone stands at Frugården in Norra Åsarp in Västergötland (Vg 181). The last sentence is a carver's signature: *Havarðr hiogg stein*, Hávarðr cut the stone. Yet no carver is given for the stone in the Scandinavian Runic-text Data Base, the database that nearly all statistics on runestones rest on – ours too. We found out by a detour, and the detour is the subject of this article.

{photo('Vg 181', 'Vg 181 at Frugården: Gufi’s stone for his son Ólafr, who was killed in Estonia. At the bottom stands the carver’s name.', 'en')}

:::box In short
- Vitki searches for groups of runestones without a known carver that resemble each other as closely as one carver's stones do – in spelling, formulas, rune forms and style.
- In Västergötland the model found, among others, two groups. Reading Sveriges runinskrifter, we found that the editors had already tied several of the stones to the same carver, and that one of them is signed by Hávarðr. The model found them without knowing.
- Rundata's carver field lacks that information. That {pc(COV['Vg'])} per cent of Västergötland's runestones have a carver in the database says more about the database than about what research knows.
- Three groups – around Konungsund in Östergötland, Vetlanda in Småland and Husaby on Kinnekulle – are not described as carver groups in the literature we have read. They are questions for runologists, not discoveries.
:::

## Looking for a hand

A carver leaves traces in the text: how he spelled *stæin* and *æftiR*, which word dividers he used, which formula the stone opens with, which runes tend to stand next to each other. Vitki compares every stone without a carver with all others nearby on those traits and looks for groups that hang together as tightly as a known carver's stones.

It is easy to find patterns that are not there, so we first tested the method where the answer is known. We took stones with a known carver in Uppland and Södermanland, hid the carver and let the method group them. The threshold for what counts as alike was set on other carvers than those tested. On average {pc(HO['purity'])} per cent of the stones in a group were the same carver's, against {pc(HO['purity_geography'])} per cent if one simply takes as many nearby stones. The method thus sees something more than that neighbours resemble each other, and that held in all {HO['runs']} rounds we ran.

But there we were stuck. Uppland and Södermanland are the only provinces where enough stones have a known carver to test the method: {pc(COV['U'])} per cent of Uppland's runestones have a carver in Rundata, but only {pc(COV['Ög'])} per cent in Östergötland, {d1(100 * COV['Sm'], en=True)} in Småland and {pc(COV['Vg'])} in Västergötland. Where the method's suggestions were most interesting, we could not see whether they were right.

## The answer was already in print

In Västergötland the method gave, among others, two groups: thirteen stones around Kölaby, Norra Åsarp and Böne near Ulricehamn, and six stones around Leksberg near Mariestad. We read what Hugo Jungner and Elisabeth Svärdström wrote about each stone in *Västergötlands runinskrifter*, the edition in the series Sveriges runinskrifter.

For the Kölaby group they had already said most of it. Vg 181 is signed by Hávarðr. Vg 158 is “probably made by the same man who signed Vg 181”. Vg 184 “seems to be carved by the same man who made Vg 179”. Vg 130 is signed by another carver, Tryggvi. For the Leksberg group they wrote that it is “likely that the same carver made Vg 13 and 15 and probably also Vg 11” – two of the stones were raised by the same man, Þórir Skorpa, for his son Ketill.

{photo('Vg 11', 'Vg 11 at Leksbergs backe: Þórir Skorpa’s stone for his son Ketill. The editors of Västergötlands runinskrifter held that the same carver made Vg 11, 13 and 15.', 'en')}

None of this is in Rundata's carver field. The model did not know it and could not have learnt it, and yet it put the stones in the same group. It is the first sign we have had that the method works outside the Mälaren region too – and it came from runologists working more than half a century ago, with their eyes, drawings and patience.

## What the groups share

The groups are formed on spelling and formulas, so their resemblance in exactly that proves nothing. We therefore tested two things that are not part of the likeness, following plans locked before anything was counted:

- **The rock.** The groups' stones are more often of the same rock than stones from the same district and time. So are the known carvers' stones – a carver fetched his stone where he usually did.
- **Unusual spellings.** Two stones in the Kölaby group write *eftR* for *æftiR*, two write *stein*; in the Konungsund group *ræisti* is spelled *rasti* on three stones. Such quirks are seldom shared by chance in a district, and the known carvers' stones share them in the same way.

We also built a model that estimates how likely it is that a group is mainly one hand. It is calibrated on 912 groups that the method formed from known carvers' stones, and it tells the pure groups from the mixed ones in nine cases out of ten.

{chart('en')}

The figures say what a group with these traits would mean in Uppland and Södermanland. That the same relation holds in Västergötland and Småland we cannot show – but the two groups where the literature has already given the answer land where one would expect.

## Three questions for runologists

Three groups are not described as one carver's work in what we have read: Sveriges runinskrifter for Östergötland, Småland and Västergötland, and Magnus Källström's dissertation on the signing carvers, *Mästare och minnesmärken* (2007). We do not call them new carvers. We ask the question.

**Konungsund (Östergötland, {N[2]} stones).** The group is large – too large to be a single hand, the model says, but probably a master with a few stones by others. Erik Brate already assigned two of the stones, Ög 46 and Ög 233, to the same carver. At Östra Stenby church, next to Ög 233, stands Ög 234: *{Q['Ög 234']}* Karl carved – or raised – this stone in memory of Ásmundr, his brother. Whether *ræist* means carved or is a shortening of raised, scholars have not been able to decide (Källström 2007, p. 85 ff.). Karl's stone is not in the group, but among the three stones in the group most like it are precisely Ög 233 and Ög 46. Was Karl the carver behind them?

{photo('Ög 234', 'Ög 234 at Östra Stenby church: “Karl ræist stæin” – did Karl carve or raise the stone?', 'en')}

**Vetlanda (Småland, {N[5]} stones).** The model gives the group the highest probability of all, but it has no independent support: neither rock, names nor unusual spellings bind it together. On one of the stones, Sm 111 at Fageräng, the text ends in a damaged sequence of runes. Ragnar Kinander read it as a prayer; later readings see a signature, *aku- hio[gg]*, someone cut (Källström 2007, p. 342). If the signature holds, the group may have a name.

**Husaby (Västergötland, {N[13]} stones).** Six stones on Kinnekulle, without any remark in the literature. The smallest and quietest group – and therefore the one that most needs a runologist's eyes.

## How sure we are

:::box How sure we are
- **Tested where the answer is known.** On known carvers in Uppland and Södermanland, with the carvers hidden, {pc(HO['purity'])} per cent of a group were the same carver's, against {pc(HO['purity_geography'])} per cent for neighbouring stones.
- **The plans were locked first.** What would be tested – rock, size, names, spellings, time – and when it counts as support was decided before anything was counted. Size gave no result.
- **The literature as the key.** That two groups are already in Sveriges runinskrifter is the strongest evidence, and it is independent of us.
- **Not tested where the candidates stand.** In Östergötland, Småland and Västergötland almost no stones have a known carver in Rundata, so the method's threshold cannot be tested there. The probabilities are borrowed from the Mälaren region.
:::

## Caveats

- A group may be one carver, a workshop with several hands, or a district's writing custom. The method cannot tell them apart; the rock and the spellings point to one hand but do not prove it.
- We have read Sveriges runinskrifter and Källström (2007), not all the literature. Laila Kitzler Åhfeldt's studies of carving technique and Per Stille's on attribution may say more.
- None of the stones in the three open groups has been 3D-scanned, so the carving grooves – the strongest evidence of one hand – we have not been able to compare.

:::box The essentials in brief
- The databases know less than research does. Hávarðr's signature on Vg 181 and the editors' observations on the same carver have stood in print for decades but were never entered in Rundata's carver field.
- A statistical model that looks for a hand in spelling and formulas found the same carvers as the runologists – without knowing about them. That makes its other suggestions worth taking seriously.
- Konungsund, Vetlanda and Husaby are questions, not answers: was Karl at Östra Stenby a carver, and who cut Sm 111?
- Next time you read a runestone, look at the last sentence. *Hiogg*, *risti*, *fáði* – there, sometimes, stands a person who has otherwise vanished.
:::

## Sources

- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Jungner, Hugo & Svärdström, Elisabeth 1940–70. *Västergötlands runinskrifter* (Sveriges runinskrifter V), pp. 20, 25, 29, 250 f., 296, 323–331.
- Brate, Erik 1911–18. *Östergötlands runinskrifter* (Sveriges runinskrifter II), p. 217.
- Kinander, Ragnar 1935–61. *Smålands runinskrifter* (Sveriges runinskrifter IV), p. 249.
- Källström, Magnus 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden*. Stockholm University, pp. 85 ff., 342, 350.
- Vitki's method (r/anonymous.R), the locked plans and the reading list per stone are open on [GitHub](https://github.com/Precatio/runes).
- Photos: Wikimedia Commons, with photographer and licence in the captions."""

import re  # noqa: E402
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"

out = {"slug": "havard-hogg-stenen", "title": title, "summary": summary, "body": body,
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
