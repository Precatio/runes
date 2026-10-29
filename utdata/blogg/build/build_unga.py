"""Artikeln "Färderna var de ungas" (sv + en): söner och bröder dog oftare utanför Norden än fäder och makar, och
drengr och þegn följer den dödes plats i släkten. Siffrorna låses mot människomodulen (r/people.R, låst plan
analysplaner/2026-10-28-manniskorna.md) i korpusberäkningen nedan; citaten står ordagrant som i Rundatas normalisering.
    ../../../.venv/bin/python build_unga.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import commons  # noqa: E402

FP = "3f58e9339191761e"
D = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
R = {t["key"]: t for t in json.load(open(os.path.join(D, "people.json"), encoding="utf-8"))["tests"]}
DB, DR, TH = R["dod_borta_ung"], R["drengr_ung"], R["thegn_ung"]
recs = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
BY = {r["signum"]: r for r in recs}

pc = lambda x: round(100 * x)  # noqa: E731
d1 = lambda x, k=1: f"{x:.{k}f}".replace(".", ",")  # noqa: E731

# ---- the locked numbers -----------------------------------------------------------------------------------------------
assert DB["status"] == "bekräftar" and DR["status"] == "mönster att pröva" and TH["status"] == "mönster att pröva"
m = DB["main"]
assert (m["n"], m["k"]) == (945, 56) and m["p_holm"] < 1e-4
DB_Y, DB_O, DB_OR, DB_LO, DB_HI = m["shares"]["1"], m["shares"]["0"], m["or"], m["lo"], m["hi"]
HA, HB = DB["halves"]["A"], DB["halves"]["B"]
RB = DB["robustness"]
DR_Y, DR_O, DR_OR = DR["main"]["shares"]["1"], DR["main"]["shares"]["0"], DR["main"]["or"]
TH_Y, TH_O, TH_OR = TH["main"]["shares"]["1"], TH["main"]["shares"]["0"], TH["main"]["or"]
assert DR["halves"]["B"]["too_few"] and TH["halves"]["A"]["p"] > 0.05 and TH["halves"]["B"]["p"] > 0.05

# Raw counts, the same selection as r/people.R (legible Swedish stones, all dead men, young or older but not both)
c = pd.read_csv(os.path.join(D, "corpus.csv"), low_memory=False)
p = pd.read_csv(os.path.join(D, "people.csv"))
x = c.merge(p, on="signum")
x = x[(x.legible == 1) & x.region.isin(["Svealand", "Götaland", "Gotland", "Norrland"])]
young = ((x.rel_barn == 1) | (x.rel_syskon == 1)) & ~((x.rel_foralder == 1) | (x.rel_make == 1))
older = ((x.rel_foralder == 1) | (x.rel_make == 1)) & ~((x.rel_barn == 1) | (x.rel_syskon == 1))
men = (x.doda_k == 0) & (x.doda_m >= 1)
Y, O = x[young & men], x[older & men]
RAW = {"y_n": len(Y), "y_k": int(Y.dod_borta.sum()), "o_n": len(O), "o_k": int(O.dod_borta.sum()),
       "y_dr": int(Y.drengr.sum()), "o_dr": int(O.drengr.sum()), "y_th": int(Y.thegn.sum()), "o_th": int(O.thegn.sum())}
assert RAW == {"y_n": 393, "y_k": 41, "o_n": 552, "o_k": 15, "y_dr": 27, "o_dr": 4, "y_th": 5, "o_th": 26}, RAW
YB = Y[Y.dod_borta == 1]
WHO = {"barn": int(YB.rel_barn.sum()), "syskon": int(YB.rel_syskon.sum()), "kvinna": int((YB.resare_k > 0).sum())}
WHO["moder"] = int(((YB.resare_k > 0) & (YB.rel_barn == 1)).sum())  # a woman raising for her son: the mother
assert WHO == {"barn": 26, "syskon": 15, "kvinna": 13, "moder": 13}, WHO
ALL = x[men & (x.dod_borta == 1)]  # every stone for a man who died abroad, whatever the relation
WIDOW = {"n": len(ALL), "make": int(ALL.rel_make.sum())}
assert WIDOW == {"n": 69, "make": 4}, WIDOW

# ---- the quotations, verbatim -----------------------------------------------------------------------------------------
Q = {s: BY[s]["normalization"].strip() for s in ("Vg 61", "Vg 59", "U 1087", "Vg 181", "U 346")}
assert Q["Vg 61"] == '"Tola satti stæin þ[annsi æft]iR "GæiR, sun sinn, harða goðan dræng. Sa varð dauðr a vestrvegum i vikingu.'
assert "harða goðan þegn. Sva hæfiR \"Asa es æigi mun sum kvæn æft ver siðan gærva." in Q["Vg 59"]
assert Q["U 1087"].endswith('Annarr varð dauðr i "Grikkium.')
assert 'sun sinn, dræng harða goðan. Hann varð drepinn i "Æistlandum.' in Q["Vg 181"]
assert 'Hann fell a "Virlandi.' in Q["U 346"]
plain = lambda s: s.replace('"', "")  # noqa: E731  (Rundata's name marks)

# ---- photographs ------------------------------------------------------------------------------------------------------
FILES = commons.wikidata_files(["Vg 61", "Vg 59"])
INFO = commons.commons_info(list(FILES.values()))
for s in ("Vg 61", "Vg 59"):
    assert (INFO[FILES[s]]["author"], INFO[FILES[s]]["licence"]) == ("Berig", "CC BY-SA 3.0"), s


def credit(s, lang):
    page = "https://commons.wikimedia.org/wiki/File:" + FILES[s].replace(" ", "_")
    return (f"{'Foto' if lang == 'sv' else 'Photo'}: Berig, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/), "
            f"via [Wikimedia Commons]({page}).")


def photo(s, text, lang):
    alt = f"Runstenen {s}" if lang == "sv" else f"The runestone {s}"
    return f"![{alt}]({INFO[FILES[s]]['thumb']})\n{text} {credit(s, lang)}"


def chart(lang):
    sv = lang == "sv"
    st = "stenar" if sv else "stones"
    rows = [":::chart Vad stenarna säger om den döde, efter hans plats i släkten" if sv else
            ":::chart What the stones say about the dead man, by his place in the family",
            "# " + ("Dog utanför Norden" if sv else "Died outside Scandinavia"),
            f"+{'Söner och bröder' if sv else 'Sons and brothers'} | {pc(DB_Y)} | {RAW['y_k']} av {RAW['y_n']} {st}" if sv else
            f"+Sons and brothers | {pc(DB_Y)} | {RAW['y_k']} of {RAW['y_n']} {st}",
            f"{'Fäder och makar' if sv else 'Fathers and husbands'} | {pc(DB_O)} | {RAW['o_k']} {'av' if sv else 'of'} {RAW['o_n']} {st}",
            "# " + ("Kallas drengr" if sv else "Called drengr"),
            f"+{'Söner och bröder' if sv else 'Sons and brothers'} | {pc(DR_Y)} | {RAW['y_dr']} {st}",
            f"{'Fäder och makar' if sv else 'Fathers and husbands'} | {pc(DR_O)} | {RAW['o_dr']} {st}",
            "# " + ("Kallas þegn" if sv else "Called þegn"),
            f"{'Söner och bröder' if sv else 'Sons and brothers'} | {pc(TH_Y)} | {RAW['y_th']} {st}",
            f"+{'Fäder och makar' if sv else 'Fathers and husbands'} | {pc(TH_O)} | {RAW['o_th']} {st}",
            ("Källa: Vitkis människomodul (r/people.R) på Samnordisk runtextdatabas. Andelarna är modellens, med landsdel, tid "
             "och ristare konstanta; antalen är de råa." if sv else
             "Source: Vitki's people module (r/people.R) on the Scandinavian Runic-text Data Base. The shares are the model's, "
             "with region, time and carver held constant; the counts are raw.")]
    return "\n".join(rows) + "\n:::"


title = "Färderna var de ungas"
summary = ("Vem dog i öster och väster? Vi läste runstenarnas släktord och räknade: söner och bröder dog utanför Norden "
           f"ungefär fyra gånger så ofta som fäder och makar. Och orden för de döda följer samma linje – *drengr* om de unga, "
           f"*þegn* om de äldre.")

body = f"""*{plain(Q['Vg 61'])}*

Tola satte denna sten efter Geir, sin son, en mycket god *drengr*. Han dog i västerled, i viking.

På stenarna efter män som dog i öster och väster står ofta en mor eller en far, sällan en änka: av {WIDOW['n']} sådana stenar är bara {WIDOW['make']} resta efter en make. Tola i Härlingstorp i Västergötland (Vg 61) är en av dem. Hennes son for västerut och kom inte tillbaka. Vi ville veta om hon är ett undantag eller en regel: var det de unga som for, och de unga som inte kom hem?

{photo('Vg 61', 'Vg 61 vid Härlingstorp: Tolas sten efter sonen Geir, ”en mycket god drengr” som dog i viking i västerled.', 'sv')}

:::box Kort sagt
- Vi läste vem som reste varje runsten och efter vem, och jämförde stenar efter söner och bröder med stenar efter fäder och makar.
- Söner och bröder dog utanför Norden på {pc(DB_Y)} % av stenarna, fäder och makar på {pc(DB_O)} %, med landsdel, tid och ristare konstanta. Skillnaden håller i båda halvorna av materialet.
- Bakom de unga som dog borta står föräldrar och syskon – modern på var tredje sten.
- Orden följer samma linje: *drengr* sägs om söner och bröder, *þegn* om fäder och makar. Det är ett mönster att pröva, inte bekräftat.
:::

## Vem dog borta?

En runsten säger nästan alltid vem som reste den och vem den döde var för dem: *sun sinn*, sin son; *faður sinn*, sin far; *broður sinn*, sin bror. Vi läste de relationerna på alla läsbara svenska runstenar med en regel i Rundatas översättning och kontrollerade den mot vår egen läsning av hundra stenar. Sedan delade vi de döda männen i två grupper: söner och bröder – de som oftast var unga när de dog – och fäder och makar, som hade hunnit få familj.

Skillnaden är stor. Av {RAW['y_n']} stenar efter söner och bröder säger {RAW['y_k']} att den döde dog utanför Norden. Av {RAW['o_n']} stenar efter fäder och makar gör {RAW['o_k']} det. När vi håller landsdel, tid och ristare konstanta blir det {pc(DB_Y)} mot {pc(DB_O)} procent. En son eller bror som dog hade alltså ungefär fyra gånger så stor chans att ha dött i öster eller väster som en far eller make (oddskvot {d1(DB_OR)}, troligen mellan {d1(DB_LO)} och {d1(DB_HI)}). En så tydlig skillnad skulle uppstå av en slump i färre än ett fall av tiotusen.

{chart('sv')}

Vi gjorde om provet i två halvor av materialet, delade socken för socken så att båda fick stenar från samma trakter och samma tid. Skillnaden syns i båda. Den syns också i Uppland för sig, på stenar med minst tio läsbara ord, och när vi bara jämför söner med fäder.

## Föräldrarna och syskonen

Vem reste då stenarna efter de unga som dog borta? Av de {RAW['y_k']} är {WHO['barn']} rest av föräldrar och {WHO['syskon']} av syskon. På {WHO['moder']} av dem står modern bland resarna, ensam eller med fadern.

*{plain(Q['U 1087'])}* Fastvi lät resa stenen efter Gerdar och Otrygg, sina söner. Den andre dog bland grekerna (U 1087, Lövsta i Uppland).

*{plain(Q['U 346'].split('. "Guð')[0])}.* Ragnfrid lät resa denna sten efter Björn, hennes och Kättilmunds son. Han föll i Virland (U 346, Frösunda i Uppland).

*{plain(Q['Vg 181'].split(' "Havarðr')[0])}* Gufi reste denna sten efter Olav, sin son, en mycket god *drengr*. Han blev dräpt i Estland (Vg 181, Frugården i Västergötland).

Det är stenar efter unga män som for i följe – med Ingvar, hos grekerna, i viking västerut – och som sörjdes av dem som hade fött och fostrat dem, inte av änkor och barn. Färderna tycks ha hört till livet innan man fick egen gård och egen familj.

## Två ord för två skeden

Samma linje syns i orden. *drengr* – ordet bakom vårt *dräng*, men på runstenarna en hedersbeteckning för en duglig ung man, ofta i ett följe – står på {pc(DR_Y)} procent av stenarna efter söner och bröder och på {pc(DR_O)} procent efter fäder och makar ({RAW['y_dr']} mot {RAW['o_dr']} stenar). *þegn* – som ofta tolkas som en man med ställning och egen gård – går åt andra hållet: {pc(TH_O)} procent efter fäder och makar mot {pc(TH_Y)} procent efter söner och bröder.

{photo('Vg 59', 'Vg 59 vid Norra Härene: fyra söner reste stenen efter fadern Fot, ”en mycket god þegn”, och hans hustru Åsa fick sina egna ord.', 'sv')}

*{plain(Q['Vg 59'].split(' "HialmR')[0])}* Hrefning och Gjalle och Brynjulv och Gjavulv satte denna sten efter Fot, sin far, en mycket god *þegn*. Så har Åsa gjort, som ingen hustru härefter kommer att göra efter sin make (Vg 59, Norra Härene i Västergötland).

Att *drengr* och *þegn* kan höra till olika skeden i livet har forskningen föreslagit tidigare (Goetting 2006; Sukhino-Khomenko 2024). Det vi tillför är mätningen med landsdel, tid och ristare konstanta. Här ska vi vara noga: skillnaden är stor i hela materialet, men orden är för få för att hålla i båda halvorna var för sig. Den ena halvan har för få *drengr*-stenar för att pröva, och *þegn* når inte gränsen i någon av halvorna. Det är ett mönster att pröva, inte ett resultat.

## Så säkra är vi

:::box Så säkra är vi
- **Planen låstes först.** Vad som skulle prövas och när ett resultat räknas som säkert bestämdes innan något test kördes.
- **Samma tid, trakt och ristare.** Varje jämförelse hålls konstant för landsdel, tidsskikt och ristare, så att skillnaden inte bara speglar att vissa trakter eller verkstäder skrev mer om resor.
- **Två halvor.** Resultatet om döden borta syns i båda halvorna av materialet; orden *drengr* och *þegn* gör det inte, och de redovisas därför som ett mönster att pröva.
- **Läsningen är kontrollerad.** Relationen läses ur översättningen med regler som stämde med vår egen läsning i 38 av 40 nya stenar.
:::

## Vad det betyder

Runstenarna är inga folkbokföringar. De berättar om dem som inte kom hem, och det är de efterlevande som valt vad som skulle stå. Men just därför säger mönstret något. Den som dog i öster eller väster var oftast någons son eller bror, och den som reste stenen var en förälder eller ett syskon. Fäder och makar fick oftare stenar som inte säger hur de dog – de dog troligen hemma, och en död hemma var inget att berätta.

Vår hypotes är att färderna hörde till ungdomen, till tiden innan man ärvde eller byggde en egen gård. Den unge mannen var *drengr*, en i följet; den äldre var *þegn*, en man med gård och ansvar. Färden var ett skede i livet, inte ett yrke.

Den kan prövas vidare: om färderna var de ungas bör stenar efter döda borta sällan nämna barn eller hustru, och resestenarna bör oftare resas av en enda förälder än av en hel syskonskara. Vår upptäcktsmotor har redan sett det senare som ett mönster: resestenar reses av färre personer.

## Förbehåll

- Stenarna minns främst dem som dog. De som kom hem fick sällan en sten, och därför säger materialet inget om hur många som for.
- Söner och bröder var oftast unga, fäder och makar äldre – men inte alltid. En bror kunde vara gift och en far ung.
- Relationerna läses med regler som har fel på omkring en sten av tjugo, oftast där texten har luckor.
- *drengr* och *þegn* kan också säga något om ställning och följe, inte bara om ålder.

:::box Det viktigaste i korthet
- Runstenarna efter dem som dog i öster och väster restes oftast av föräldrar och syskon, inte av änkor och barn.
- Söner och bröder dog utanför Norden ungefär fyra gånger så ofta som fäder och makar, också när tid, trakt och ristare hålls konstanta.
- Färderna tycks ha hört till ungdomen, till tiden innan egen gård och familj – och orden för de döda, *drengr* om de unga och *þegn* om de äldre, pekar åt samma håll, även om de är för få för att vara säkra.
- Nästa gång du står vid en runsten: se vem som reste den. En mor eller en bror vid stenen berättar ofta om en ung man som for.
:::

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Goetting, Lauren 2006. ”Þegn and drengr in the Viking Age”. *Scandinavian Studies* 78 (4).
- Sukhino-Khomenko, Denis 2024. *Thegns Around the North Sea*. Göteborgs universitet.
- Vitkis människomodul (r/people.R) och den låsta analysplanen ligger öppet på [GitHub](https://github.com/Precatio/runes). Om dygderna på stenarna: [Mild i ord och god på mat](/artiklar/mild-i-ord-och-god-pa-mat).
- Foton: Wikimedia Commons, med fotograf och licens i bildtexterna."""

title_en = "The journeys belonged to the young"
summary_en = ("Who died in the east and the west? We read the runestones' words for kin and counted: sons and brothers "
              "died outside Scandinavia about four times as often as fathers and husbands. And the words for the dead "
              "follow the same line – *drengr* for the young, *þegn* for the older.")

body_en = f"""*{plain(Q['Vg 61'])}*

Tóla placed this stone in memory of Geirr, her son, a very good *drengr*. He died on the western route, on a viking raid.

On the stones for men who died in the east and the west, a mother or a father often stands by the stone, seldom a widow: of {WIDOW['n']} such stones only {WIDOW['make']} were raised for a husband. Tóla at Härlingstorp in Västergötland (Vg 61) is one of them. Her son went west and did not come back. We wanted to know whether she is an exception or a rule: was it the young who went, and the young who did not come home?

{photo('Vg 61', 'Vg 61 at Härlingstorp: Tóla’s stone for her son Geirr, “a very good drengr” who died on a viking raid in the west.', 'en')}

:::box In short
- We read who raised each runestone and for whom, and compared stones for sons and brothers with stones for fathers and husbands.
- Sons and brothers died outside Scandinavia on {pc(DB_Y)} % of the stones, fathers and husbands on {pc(DB_O)} %, with region, time and carver held constant. The difference holds in both halves of the material.
- Behind the young who died abroad stand parents and siblings – the mother on one stone in three.
- The words follow the same line: *drengr* is said of sons and brothers, *þegn* of fathers and husbands. That is a pattern to test, not a confirmed one.
:::

## Who died abroad?

A runestone nearly always says who raised it and who the dead man was to them: *sun sinn*, his son; *faður sinn*, his father; *broður sinn*, his brother. We read those relations on all legible Swedish runestones with a rule in Rundata's translation and checked it against our own reading of a hundred stones. Then we divided the dead men into two groups: sons and brothers – most often young when they died – and fathers and husbands, who had had time to found a family.

The difference is large. Of {RAW['y_n']} stones for sons and brothers, {RAW['y_k']} say that the dead man died outside Scandinavia. Of {RAW['o_n']} stones for fathers and husbands, {RAW['o_k']} do. With region, time and carver held constant that is {pc(DB_Y)} against {pc(DB_O)} per cent. A son or brother who died was thus about four times as likely to have died in the east or the west as a father or husband (odds ratio {DB_OR:.1f}, probably between {DB_LO:.1f} and {DB_HI:.1f}). A difference this clear would arise by chance in fewer than one case in ten thousand.

{chart('en')}

We repeated the test in two halves of the material, split parish by parish so that both had stones from the same districts and the same time. The difference shows in both. It also shows in Uppland on its own, on stones with at least ten legible words, and when we compare only sons with fathers.

## The parents and the siblings

Who, then, raised the stones for the young who died abroad? Of the {RAW['y_k']}, {WHO['barn']} were raised by parents and {WHO['syskon']} by siblings. On {WHO['moder']} of them the mother stands among the raisers, alone or with the father.

*{plain(Q['U 1087'])}* Faství had the stone raised in memory of Gerðarr and Ótryggr, her sons. The other died among the Greeks (U 1087, Lövsta in Uppland).

*{plain(Q['U 346'].split('. "Guð')[0])}.* Ragnfríðr had this stone erected in memory of Bjôrn, her son and Ketilmundr's. He fell in Virland (U 346, Frösunda in Uppland).

*{plain(Q['Vg 181'].split(' "Havarðr')[0])}* Gufi raised this stone in memory of Ólafr, his son, a very good *drengr*. He was killed in Estonia (Vg 181, Frugården in Västergötland).

These are stones for young men who went in a following – with Ingvarr, among the Greeks, on viking raids to the west – and who were mourned by those who had borne and raised them, not by widows and children. The journeys seem to have belonged to life before one had a farm and a family of one's own.

## Two words for two stages

The same line shows in the words. *drengr* – the word behind Swedish *dräng*, but on the runestones a title of honour for a capable young man, often in a following – stands on {pc(DR_Y)} per cent of the stones for sons and brothers and on {pc(DR_O)} per cent of those for fathers and husbands ({RAW['y_dr']} against {RAW['o_dr']} stones). *þegn* – often read as a man of standing with a farm of his own – goes the other way: {pc(TH_O)} per cent for fathers and husbands against {pc(TH_Y)} per cent for sons and brothers.

{photo('Vg 59', 'Vg 59 at Norra Härene: four sons raised the stone for their father Fótr, “a very good þegn”, and his wife Ása was given words of her own.', 'en')}

*{plain(Q['Vg 59'].split(' "HialmR')[0])}* Hrefningr and Gjalli and Brynjulfr and Gjafulfr placed this stone in memory of Fótr, their father, a very good *þegn*. Thus has Ása made, as no other wife in memory of her husband will (Vg 59, Norra Härene in Västergötland).

That *drengr* and *þegn* may belong to different stages of life has been suggested before (Goetting 2006; Sukhino-Khomenko 2024). What we add is the measurement with region, time and carver held constant. Here we must be careful: the difference is large in the whole material, but the words are too few to hold in both halves separately. One half has too few *drengr* stones to test, and *þegn* does not reach the threshold in either half. It is a pattern to test, not a result.

## How sure we are

:::box How sure we are
- **The plan was locked first.** What would be tested, and when a result counts as firm, was decided before any test was run.
- **The same time, district and carver.** Every comparison holds region, time layer and carver constant, so that the difference does not merely reflect that some districts or workshops wrote more about journeys.
- **Two halves.** The result on death abroad shows in both halves of the material; the words *drengr* and *þegn* do not, and are therefore reported as a pattern to test.
- **The reading is checked.** The relation is read from the translation with rules that agreed with our own reading on 38 of 40 new stones.
:::

## What it means

Runestones are no parish registers. They tell of those who did not come home, and it was the survivors who chose what would be said. But that is exactly why the pattern says something. The man who died in the east or the west was most often someone's son or brother, and the one who raised the stone was a parent or a sibling. Fathers and husbands more often got stones that do not say how they died – they probably died at home, and a death at home was nothing to tell.

Our hypothesis is that the journeys belonged to youth, to the time before one inherited or built a farm of one's own. The young man was a *drengr*, one of the following; the older man was a *þegn*, a man with a farm and responsibilities. The journey was a stage of life, not a profession.

It can be tested further: if the journeys belonged to the young, stones for those who died abroad should seldom name children or a wife, and the travel stones should more often be raised by a single parent than by a whole band of siblings. Our discovery engine has already seen the latter as a pattern: travel stones are raised by fewer people.

## Caveats

- The stones mainly remember those who died. Those who came home seldom got a stone, so the material says nothing about how many went.
- Sons and brothers were most often young, fathers and husbands older – but not always. A brother could be married and a father young.
- The relations are read with rules that are wrong on about one stone in twenty, mostly where the text has gaps.
- *drengr* and *þegn* can also say something about standing and following, not only about age.

:::box The essentials in brief
- The runestones for those who died in the east and the west were most often raised by parents and siblings, not by widows and children.
- Sons and brothers died outside Scandinavia about four times as often as fathers and husbands, also when time, district and carver are held constant.
- The journeys seem to have belonged to youth, to the time before a farm and a family of one's own – and the words for the dead, *drengr* for the young and *þegn* for the older, point the same way, although they are too few to be sure.
- Next time you stand by a runestone: look at who raised it. A mother or a brother by the stone often tells of a young man who went away.
:::

## Sources

- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Goetting, Lauren 2006. “Þegn and drengr in the Viking Age”. *Scandinavian Studies* 78 (4).
- Sukhino-Khomenko, Denis 2024. *Thegns Around the North Sea*. University of Gothenburg.
- Vitki's people module (r/people.R) and the locked analysis plan are open on [GitHub](https://github.com/Precatio/runes). On the virtues on the stones: [Gentle in speech and free with food](/en/artiklar/mild-i-ord-och-god-pa-mat).
- Photos: Wikimedia Commons, with photographer and licence in the captions."""

import re  # noqa: E402
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"

out = {"slug": "fardena-var-de-ungas", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Kvinnor och barn", "Formler och syfte"]}
path = os.path.join(ROOT, "utdata", "blogg", "unga.json")
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
                 "topic": "Forskning|manniskor", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
