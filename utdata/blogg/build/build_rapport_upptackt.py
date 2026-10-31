"""Forskningsrapport, metodrapport (låst mall utdata/rapporter/MALL.md, version 4; Metodrapport, delvis prövad):
"En upptäcktsmotor som inte lurar sig själv: av 28 samband som hittades i ena halvan av runstenarna höll 14 i den andra"
(sv + en). Upptäcktsmotorn v1 (analysplaner/2026-10-28-upptacktsmotorn.md) och v2 (2026-10-29-upptacktsmotorn-v2.md).
Alla siffror asserteras mot utdata/upptackt/upptackt.json, utdata/upptackt_v2/upptackt.json och lokala.json.
    ../../../.venv/bin/python build_rapport_upptackt.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

APP_VERSION = json.load(open(os.path.join(ROOT, "web", "package.json")))["version"]
assert APP_VERSION == "3.0.0"
assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 1
TODAY = "2026-10-31"  # rapportversionens datum, fast i byggaren (mallen version 3)
TL_SV = "version 1:s plan låstes 2026-10-28; version 1 kördes 2026-10-28; version 2:s plan låstes 2026-10-29; version 2 kördes 2026-10-29"
TL_EN = "the plan of version 1 was locked 2026-10-28; version 1 was run 2026-10-28; the plan of version 2 was locked 2026-10-29; version 2 was run 2026-10-29"
U1 = json.load(open(os.path.join(ROOT, "utdata", "upptackt", "upptackt.json"), encoding="utf-8"))
U2 = json.load(open(os.path.join(ROOT, "utdata", "upptackt_v2", "upptackt.json"), encoding="utf-8"))
LK = json.load(open(os.path.join(ROOT, "utdata", "upptackt_v2", "lokala.json"), encoding="utf-8"))
SHA = {k: open(os.path.join(ROOT, "analysplaner", f"{k}.sha256")).read().split()[0][:16]
       for k in ("2026-10-28-upptacktsmotorn", "2026-10-29-upptacktsmotorn-v2")}
assert SHA["2026-10-28-upptacktsmotorn"].startswith("b5f9554d") and SHA["2026-10-29-upptacktsmotorn-v2"].startswith("54e02682")
d2 = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731

# ---- version 1 --------------------------------------------------------------------------------------------------------
assert (U1["n_stones"], U1["n_features"], U1["halves"]) == (1739, 59, {"A": 846, "B": 893})
M, SW = U1["main"], U1["swap"]
assert (M["tested"], M["n_cand"], M["sha256"][:8], SW["tested"], SW["n_cand"]) == (927, 28, "bcc73aae", 941, 15)
C1 = Counter(r["utslag"] for r in M["results"])
assert C1 == {"bekräftad": 14, "höll inte": 8, "mönster att pröva": 6} and len(U1["stable_both_ways"]) == 8
R1 = {(r["a"], r["b"]): r for r in M["results"]}
FAM = [("kvinna_ensam", "rel_make"), ("flera_resare", "rel_barn"), ("kvinna_resare", "rel_make"), ("flera_resare", "rel_foralder"),
       ("kvinna_resare", "rel_barn"), ("kvinna_ensam", "rel_barn"), ("kvinna_resare", "rel_foralder"), ("kvinna_ensam", "rel_foralder")]
assert all(R1[k]["utslag"] == "bekräftad" for k in FAM)
ART = R1[("o_runa", "rel_barn")]
assert ART["utslag"] == "bekräftad" and d2(ART["or2"]) == "0,08"
NEW = {"resa": R1[("msg_resa", "flera_resare")], "fard": R1[("cat_fard", "flera_resare")], "dod_far": R1[("msg_dod_uppgift", "rel_foralder")],
       "borta_far": R1[("msg_dod_borta", "rel_foralder")], "kors_apostrof": R1[("pm_kors", "skilj_apostrof")]}
assert all(r["utslag"] == "bekräftad" for r in NEW.values())
assert [d2(NEW[k]["or2"]) for k in ("resa", "fard", "dod_far", "borta_far", "kors_apostrof")] == ["0,33", "0,33", "0,36", "0,31", "2,56"]
assert 0.04 < NEW["kors_apostrof"]["holm"] < 0.05
FAILED = [r for r in M["results"] if r["utslag"] == "höll inte"]
assert all(r["q"] < 0.05 for r in FAILED) and max(r["or"] for r in FAILED) > 4.5  # strong-looking in A, gone in B
SIGPLUS = R1[("pm_signatur", "skilj_plus")]
assert (d2(SIGPLUS["or"]), d2(SIGPLUS["or2"])) == ("4,61", "1,12")

# ---- version 2 --------------------------------------------------------------------------------------------------------
assert (U2["n_stones"], U2["n_features"]) == (1739, 124)
M2, SW2 = U2["main"], U2["swap"]
assert (M2["tested"], M2["n_cand"], SW2["tested"], SW2["n_cand"]) == (1945, 5, 1953, 4)
assert Counter(r["utslag"] for r in M2["results"]) == {"höll inte": 2, "bekräftad": 2, "mönster att pröva": 1}
R2 = {(r["a"], r["b"]): r for r in M2["results"]}
assert d2(R2[("msg_resa", "rel_foralder")]["or2"]) == "0,44" and R2[("msg_dod_uppgift", "rel_foralder")]["utslag"] == "bekräftad"
OK2 = next(r for r in SW2["results"] if r["utslag"] == "bekräftad")
assert (OK2["a"], OK2["b"], d2(OK2["or2"])) == ("au_monoftong", "skilj_apostrof", "3,59")
assert (len(LK["scanned"]), len(LK["confirmed"]), LK["n_A"], LK["n_B"], LK["candidates_sha256"][:8]) == (63, 10, 619, 611, "fc0707cb")
LC = Counter(c["utslag"] for c in LK["confirmed"])
assert LC == {"höll inte": 8, "bekräftad": 1, "mönster att pröva": 1}
TH = next(c for c in LK["confirmed"] if c["utslag"] == "bekräftad")
assert (TH["feature"], TH["center"], round(TH["radius"] / 1000), TH["O"], TH["OB"], d2(TH["ratio"]), d2(TH["ratioB"]), TH["holm"]) == \
    ("ord_þennsa", "Sö 190", 21, 11, 7, "4,01", "3,13", 0.047)
assert len(TH["carvers"]) == 13
N_CAND = M["n_cand"] + M2["n_cand"] + len(LK["confirmed"])
N_OK = C1["bekräftad"] + 2 + LC["bekräftad"]
N_FAIL = C1["höll inte"] + 2 + LC["höll inte"]
assert (N_CAND, N_OK, N_FAIL) == (43, 17, 18)

SLUG = "upptacktsmotorn"
title = "En upptäcktsmotor som inte lurar sig själv: av 28 samband som hittades i ena halvan av runstenarna höll 14 i den andra"
title_en = "A discovery engine that does not fool itself: of 28 associations found in one half of the runestones, 14 held in the other"
summary = ("Metodrapport. En dator kan söka igenom alla par av drag på runstenarna efter samband som ingen har frågat efter, "
           "men många av träffarna blir slump. Upptäcktsmotorn söker i ena halvan av stenarna, fryser listan och prövar den "
           "på den andra. Av 28 samband höll 14, och av tio bygder som stack ut höll en. Utan den andra halvan hade alla "
           "rapporterats.")
summary_en = ("Methods report. A computer can search all pairs of traits on the runestones for associations nobody has asked about, "
              "but many of the hits will be chance. The discovery engine searches one half of the stones, freezes the list and "
              "tests it on the other. Of 28 associations, 14 held, and of ten districts that stood out, one held. Without the "
              "other half all would have been reported.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report (methods report), report version {REPORT_VERSION}; analysis in "
           f"Vitki {APP_VERSION}. https://vitkirunor.se/en/forskningsrapporter/{SLUG}")


def chart(sv):
    rows = [":::chart Kandidater från första halvan och hur de gick i den andra" if sv else ":::chart Candidates from the first half and how they fared in the second"]
    lab = ("Bekräftade", "Mönster att pröva", "Höll inte") if sv else ("Confirmed", "Patterns to test", "Did not hold")
    for g_sv, g_en, c in (("Parskanning, version 1", "Pair scan, version 1", C1),
                          ("Parskanning, version 2", "Pair scan, version 2", Counter(r["utslag"] for r in M2["results"])),
                          ("Lokala bygder, version 2", "Local districts, version 2", LC)):
        rows.append(f"# {g_sv if sv else g_en}")
        for k, lb in zip(("bekräftad", "mönster att pröva", "höll inte"), lab):
            rows.append(f"{'+' if k == 'bekräftad' else ''}{lb} | {c.get(k, 0)} |")
    rows += ["Källa: Rundata; antal kandidater." if sv else "Source: Rundata; number of candidates.", ":::"]
    return "\n".join(rows)


body = f"""*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, explorativ dataanalys, upptäckt, delat urval, multipla test, förregistrering, scanstatistik. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Vad som inte är prövat.** Prövningen var låst och den andra halvan dold, men planen satte ingen gräns i förväg för när metoden räknas som fungerande; andelen som håller är uppmätt, inte prövad mot en gräns. Version 2 utformades efter att version 1:s resultat var kända.
**Bakgrund och syfte.** Den som söker igenom många samband hittar alltid några som ser starka ut av en slump. Frågan här är om en sökning i två steg, där upptäckten görs på ena halvan av materialet och prövas på den andra, skiljer verkliga samband från slumpens.
**Material.** {U1['n_stones']} svenska vikingatida runstenar med minst fyra läsbara ord i Samnordisk runtextdatabas (Rundata), delade socken för socken i två halvor; {U1['n_features']} drag i version 1 och {U2['n_features']} i version 2.
**Metod.** I första halvan prövas alla tillåtna par av drag med logistisk regression, med landskap, tid och textlängd konstanta; de starkaste blir kandidater. Listan fryses med en kontrollsumma innan den andra halvan läses, och varje kandidat prövas där med ristaren som slumpeffekt och Holm-korrigering. Version 2 lägger till en sökning efter bygder där ett drag är ovanligt vanligt.
**Resultat.** Version 1 prövade {M['tested']} par och gav {M['n_cand']} kandidater; {C1['bekräftad']} bekräftades, {C1['mönster att pröva']} blev mönster att pröva och {C1['höll inte']} höll inte. Åtta av de bekräftade är kända familjemönster, ett är en följd av hur ett drag mäts, och fem är nya. Version 2 prövade {M2['tested']} par och gav {M2['n_cand']} kandidater, varav 2 bekräftades: sökningen efter par var uttömd. Av {len(LK['confirmed'])} bygder som stack ut i första halvan höll en.
**Slutsats.** Hälften av sambanden från första halvan höll på stenar som sökningen aldrig sett, och för bygderna en av tio. Metoden gör det möjligt att låta datorn föreslå frågor utan att rapportera slumpens träffar som fynd.

## 1. Inledning

Runologins frågor ställs i regel av forskaren: man har en idé och prövar den. Ett annat sätt är att låta en dator söka igenom alla par av drag och se vilka som hänger ihop. Det kan hitta det ingen har tänkt på, men det har en känd fälla: den som prövar hundratals samband hittar alltid några som ser starka ut av en slump, och den som väljer bland träffarna efteråt kan inte längre räkna p-värdena som vanligt (Ioannidis 2005; Gelman & Loken 2014). Justering för många test minskar risken men tar inte bort den när sökningen själv formar frågan.

Det säkraste skyddet är att söka på en del av materialet och pröva på en annan som sökningen inte har sett. Syftet här är att redovisa hur ett sådant tvåstegsförfarande fungerar på de svenska runstenarna: hur många av träffarna som håller, vad som håller, och vad som inte gör det.

## 2. Förregistrering: planerna

Version 1:s plan låstes den 28 oktober 2026, innan motorn hade körts (kontrollsumma SHA-256 `{SHA['2026-10-28-upptacktsmotorn']}…`). Den bestämde dragen, vilka par som inte får prövas, modellerna, gränserna för kandidater och för bekräftelse, och att kandidatlistan skulle frysas med en kontrollsumma innan den andra halvan lästes. Version 2:s plan låstes den 29 oktober 2026 (SHA-256 `{SHA['2026-10-29-upptacktsmotorn-v2']}…`), efter att version 1:s resultat var kända; den lade till fler drag, fler par som inte får prövas och en sökning efter bygder.

Planerna bestämde vad som räknas som en bekräftad kandidat, men inte hur många kandidater som måste hålla för att metoden ska räknas som fungerande. Andelen som håller är därför ett mått, inte ett prov mot en gräns. Det är skälet till att rapporten är *delvis prövad*.

## 3. Material

- **Stenarna.** {U1['n_stones']} svenska vikingatida runstenar i Samnordisk runtextdatabas (Rundata) med minst fyra läsbara ord. Bara runstenar.
- **Halvorna.** Projektets fasta indelning socken för socken: {U1['halves']['A']} stenar i halva A, som upptäcker, och {U1['halves']['B']} i halva B, som prövar.
- **Dragen** i version 1 ({U1['n_features']}): innehåll, tro, skrift och språk, skiljetecken, ristarsignatur, budskap, vilka som reste stenen och för vem, och stenens omgivning. Version 2 ({U2['n_features']}) lade till ordformer, material och ortnamnsmiljö.
- **Par som inte prövas.** Drag som hänger ihop genom hur de är definierade, till exempel kors och bön eller två slags resetext, prövas inte mot varandra.

## 4. Metod

**4.1 Upptäckten (halva A).** För varje tillåtet par av drag en logistisk regression med landskap, tidsskikt och textlängd konstanta, bland stenar där båda dragen kan avgöras. Ett par är kandidat när det klarar justeringen för alla par som prövades (Benjamini–Hochberg 1995, q under 0,05) och oddskvoten är minst 1,5 åt något håll; högst 50 kandidater.

**4.2 Frysningen.** Kandidatlistan skrivs till en fil och dess kontrollsumma sparas innan halva B läses. I version 1 har listan kontrollsumman `{M['sha256'][:16]}…`.

**4.3 Prövningen (halva B).** Varje kandidat prövas i halva B med samma modell och dessutom ristaren som slumpeffekt (Wood 2017), ensidigt i den riktning upptäckten fann. *Bekräftad* när Holm-p är under 0,05 över kandidaterna (Holm 1979), *mönster att pröva* när den bara klarar Benjamini–Hochberg, annars *höll inte*. Som kontroll görs samma två steg med halvorna bytta.

**4.4 Bygderna (version 2).** För varje drag söks den cirkel där draget är vanligast i förhållande till vad landskap och tid ger, med scanstatistik (Kulldorff 1997). De starkaste cirklarna i halva A fryses och prövas i samma cirkel i halva B.

**4.5 Avvikelser.** Ett kodfel i prövningssteget, som stoppade körningen när en modell inte kunde skattas, rättades i version 2; kandidatlistan var byte för byte densamma före och efter. Ett par i version 2 kunde inte skattas i halva B och räknas inte.

## 5. Resultat

**5.1 Version 1.** {M['tested']} par prövades i halva A och gav {M['n_cand']} kandidater. I halva B bekräftades {C1['bekräftad']}, {C1['mönster att pröva']} blev mönster att pröva och {C1['höll inte']} höll inte. Med halvorna bytta gav {SW['tested']} par {SW['n_cand']} kandidater, och {len(U1['stable_both_ways'])} par bekräftades åt båda hållen. I klartext: hälften av det som såg ut som fynd i första halvan höll när det prövades på stenar som sökningen aldrig hade sett; den andra hälften hade varit falska fynd om vi hade stannat efter första steget.

{chart(True)}

**5.2 Vad som bekräftades.**

- **Kända familjemönster (8).** Kvinnor reser stenar efter sina män (oddskvot {d2(R1[('kvinna_resare', 'rel_make')]['or2'])} i halva B), flera resare efter fäder och färre efter söner, kvinnor oftare efter söner och mer sällan efter fäder. Sanna men kända: de beskriver vem som fanns kvar att resa stenen. Att motorn hittar dem visar att den hittar det som finns.
- **En mätartefakt (1).** o-runan står sällan på stenar efter söner (oddskvot {d2(ART['or2'])}). Draget mäts bara i några bestämda ord, och en sten efter en son har ordet *sun*, som skrivs med u-runa. Sambandet kommer av vilka ord som finns, inte av en sed; version 2 slutade därför para sådana drag med relationer.
- **Nya (5).** Resestenar reses av färre personer (oddskvot {d2(NEW['resa']['or2'])}; med utlandsfärd {d2(NEW['fard']['or2'])}). Stenar efter fäder säger sällan hur eller var han dog ({d2(NEW['dod_far']['or2'])}) och sällan att han dog borta ({d2(NEW['borta_far']['or2'])}): fäderna dog hemma, och en död hemma var inget att berätta. Kors och apostrofliknande skiljetecken följs åt ({d2(NEW['kors_apostrof']['or2'])}, med landskap, tid, textlängd och ristare konstanta), ett hantverksdrag som ingen fråga hade ställts om.

**5.3 Vad som inte höll.** Alla {C1['höll inte']} kandidater som föll klarade justeringen i halva A, och några såg starka ut: ristarsignatur och plustecken som skiljetecken hade oddskvoten {d2(SIGPLUS['or'])} i halva A och {d2(SIGPLUS['or2'])} i halva B.

**5.4 Version 2.** Med fler drag och fler förbjudna par prövades {M2['tested']} par. Bara {M2['n_cand']} blev kandidater och 2 bekräftades: att stenar efter fäder sällan berättar hur han dog (redan i version 1) och sällan nämner en resa ({d2(R2[('msg_resa', 'rel_foralder')]['or2'])}). Med halvorna bytta bekräftades ett: monoftongen i *ok* följer apostrofliknande skiljetecken ({d2(OK2['or2'])}). Sökningen efter par var uttömd på det här materialet.

**5.5 Bygderna.** {len(LK['scanned'])} drag söktes igenom i halva A ({LK['n_A']} stenar), och {len(LK['confirmed'])} cirklar blev kandidater. I halva B ({LK['n_B']} stenar) höll en: formen *þennsa* (’denna’) i en cirkel om {round(TH['radius'] / 1000)} km kring Sö 190 i Ytterenhörna, {TH['O']} stenar mot {d2(TH['E'])} väntade i halva A och {TH['OB']} mot {d2(TH['EB'])} i halva B, Holm-korrigerat p = {str(TH['holm']).replace('.', ',')}. Formen går över gränsen mellan Södermanland och Uppland och används av {len(TH['carvers'])} ristare: en bygdens form snarare än en ristares vana. En cirkel blev mönster att pröva, och {LC['höll inte']} höll inte.

## 6. Diskussion

**Vad metoden klarar.** Av {N_CAND} kandidater sammanlagt bekräftades {N_OK} och {N_FAIL} höll inte. Det betyder att ungefär varannan träff från en sökning som redan var justerad för många test inte håller på nytt material, och att bygder som sticker ut nästan alltid är slump. Tvåstegsförfarandet gör det möjligt att låta datorn föreslå frågor och ändå bara rapportera det som håller. Det hittade det kända, vilket visar att det fungerar, och några saker som ingen hade frågat om.

**Mot tidigare forskning.** Faran med att välja bland många prövningar efter att resultaten är kända är väl beskriven (Ioannidis 2005; Gelman & Loken 2014). Här syns den i siffror på ett humanistiskt material: utan den andra halvan hade arton träffar rapporterats som inte höll på nytt material.

**Svagheter, i ordning efter vikt.**

1. **Halvorna är inte nytt material.** De är två delar av samma korpus, delad socken för socken. Ett samband som bara finns i en region syns i båda halvorna. Prövningen skyddar mot slump, inte mot fel i Rundata som finns i hela materialet.
2. **Mätningen syns också.** o-runan och sönerna visar att motorn hittar struktur i hur dragen mäts, inte bara i det de mäter. Varje bekräftat samband måste läsas mot hur dragen är definierade.
3. **Ingen gräns för metoden.** Planen bestämde inte i förväg hur många kandidater som skulle hålla.
4. **Avtagande avkastning.** Version 2 fann nästan inga nya par; det mesta som kan hittas på det här sättet i det här materialet är redan funnet.

**Var metoden inte ska användas.** Som bevis: en bekräftad kandidat är en fråga som har klarat ett första prov och behöver en egen, låst plan innan den kallas ett fynd.

**Vad som skulle fälla metoden.** Att bekräftade kandidater regelbundet föll när de prövades under egna planer på annat material.

## 7. Slutsats

En upptäcktsmotor som söker i ena halvan av runstenarna och prövar i den andra fann {N_OK} samband som höll av {N_CAND} kandidater. Den visar både vad datorn kan hitta och hur mycket av det som är slump. Nästa steg är att pröva de nya sambanden under egna planer och att använda samma förfarande på Danmarks och Norges runstenar.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts efter den versionen fram till den 31 oktober 2026. Någon release med DOI finns ännu inte; när den görs hänvisar rapporten till den. All kod, analysplanerna och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Planerna: `analysplaner/2026-10-28-upptacktsmotorn.md` och `analysplaner/2026-10-29-upptacktsmotorn-v2.md`, med kontrollsummorna i `.sha256`-filerna bredvid.
- Version 1: `src/discovery.py`, `r/discovery.R`; resultat och frysta listor i `utdata/upptackt/`.
- Version 2: `src/discovery_v2.py`, `r/discovery_v2.R`, `r/discovery_lokal.R`; resultat och frysta listor i `utdata/upptackt_v2/`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_upptackt.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer.

## Referenser

- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 57 (1), s. 289–300.
- Gelman, A. & Loken, E. 2014. The statistical crisis in science. *American Scientist* 102 (6), s. 460–465.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Ioannidis, J. P. A. 2005. Why most published research findings are false. *PLoS Medicine* 2 (8), e124.
- Kulldorff, M. 1997. A spatial scan statistic. *Communications in Statistics – Theory and Methods* 26 (6), s. 1481–1496.
- Kvant, V. 2026. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md). https://github.com/Precatio/runes
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Wood, S. N. 2017. *Generalized Additive Models: An Introduction with R*. 2 uppl. Boca Raton: Chapman & Hall/CRC.

:::box Det viktigaste i korthet
- En dator kan föreslå frågor om runstenarna som ingen har ställt, men ungefär hälften av det den hittar är slump.
- Genom att söka i ena halvan och pröva i den andra kan man skilja de två åt innan något rapporteras.
- Det som höll var mest det kända, och några nya ting: fäderna dog hemma, och korsen följer ett visst skiljetecken.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Methods report, partially tested. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, exploratory data analysis, discovery, split sample, multiple testing, pre-registration, scan statistic. Competing interests: none. Funding: none.*

## Abstract

**What has not been tested.** The test was locked and the second half hidden, but the plan set no limit in advance for when the method counts as working; the share that holds is measured, not tested against a limit. Version 2 was designed after the results of version 1 were known.
**Background and aim.** Whoever searches through many associations always finds some that look strong by chance. The question here is whether a search in two steps, with the discovery made on one half of the material and tested on the other, tells real associations from chance ones.
**Material.** {U1['n_stones']:,} Swedish Viking-Age runestones with at least four legible words in the Scandinavian Runic-text Database (Rundata), divided parish by parish into two halves; {U1['n_features']} traits in version 1 and {U2['n_features']} in version 2.
**Method.** In the first half all permitted pairs of traits are tested by logistic regression, with province, time and text length held constant; the strongest become candidates. The list is frozen with a checksum before the second half is read, and each candidate is tested there with the carver as a random effect and Holm correction. Version 2 adds a search for districts where a trait is unusually common.
**Results.** Version 1 tested {M['tested']} pairs and gave {M['n_cand']} candidates; {C1['bekräftad']} were confirmed, {C1['mönster att pröva']} became patterns to test and {C1['höll inte']} did not hold. Eight of the confirmed are known family patterns, one follows from how a trait is measured, and five are new. Version 2 tested {M2['tested']:,} pairs and gave {M2['n_cand']} candidates, of which 2 were confirmed: the search for pairs was exhausted. Of {len(LK['confirmed'])} districts that stood out in the first half, one held.
**Conclusion.** Half of the associations from the first half held on stones the search had never seen, and for the districts one in ten. The method makes it possible to let the computer suggest questions without reporting the hits of chance as findings.

## 1. Introduction

The questions of runology are usually asked by the researcher: one has an idea and tests it. Another way is to let a computer search through all pairs of traits and see which go together. That can find what nobody has thought of, but it has a known trap: whoever tests hundreds of associations always finds some that look strong by chance, and whoever chooses among the hits afterwards can no longer count the p-values as usual (Ioannidis 2005; Gelman & Loken 2014). Adjustment for multiple testing reduces the risk but does not remove it when the search itself shapes the question.

The safest protection is to search one part of the material and test on another that the search has not seen. The aim here is to report how such a two-step procedure works on the Swedish runestones: how many of the hits hold, what holds, and what does not.

## 2. Pre-registration: the plans

The plan of version 1 was locked on 28 October 2026, before the engine had been run (SHA-256 checksum `{SHA['2026-10-28-upptacktsmotorn']}…`). It fixed the traits, which pairs may not be tested, the models, the limits for candidates and for confirmation, and that the list of candidates would be frozen with a checksum before the second half was read. The plan of version 2 was locked on 29 October 2026 (SHA-256 `{SHA['2026-10-29-upptacktsmotorn-v2']}…`), after the results of version 1 were known; it added more traits, more pairs that may not be tested and a search for districts.

The plans fixed what counts as a confirmed candidate, but not how many candidates must hold for the method to count as working. The share that holds is therefore a measurement, not a test against a limit. That is why the report is *partially tested*.

## 3. Material

- **The stones.** {U1['n_stones']:,} Swedish Viking-Age runestones in the Scandinavian Runic-text Database (Rundata) with at least four legible words. Runestones only.
- **The halves.** The project's fixed division parish by parish: {U1['halves']['A']} stones in half A, which discovers, and {U1['halves']['B']} in half B, which tests.
- **The traits** in version 1 ({U1['n_features']}): content, belief, writing and language, word dividers, carver's signature, messages, who raised the stone and for whom, and the stone's surroundings. Version 2 ({U2['n_features']}) added word forms, material and place-name setting.
- **Pairs not tested.** Traits that go together through how they are defined, for example cross and prayer or two kinds of travel text, are not tested against each other.

## 4. Method

**4.1 The discovery (half A).** For each permitted pair of traits a logistic regression with province, period and text length held constant, among stones where both traits can be determined. A pair is a candidate when it passes the adjustment for all pairs tested (Benjamini–Hochberg 1995, q below 0.05) and the odds ratio is at least 1.5 either way; at most 50 candidates.

**4.2 The freezing.** The list of candidates is written to a file and its checksum saved before half B is read. In version 1 the list has the checksum `{M['sha256'][:16]}…`.

**4.3 The test (half B).** Each candidate is tested in half B with the same model and in addition the carver as a random effect (Wood 2017), one-sided in the direction the discovery found. *Confirmed* when Holm p is below 0.05 over the candidates (Holm 1979), *pattern to test* when it passes only Benjamini–Hochberg, otherwise *did not hold*. As a check the same two steps are made with the halves swapped.

**4.4 The districts (version 2).** For each trait the circle is sought where the trait is most common relative to what province and time give, with a scan statistic (Kulldorff 1997). The strongest circles in half A are frozen and tested in the same circle in half B.

**4.5 Deviations.** A coding error in the test step, which stopped the run when a model could not be estimated, was corrected in version 2; the list of candidates was byte for byte the same before and after. One pair in version 2 could not be estimated in half B and is not counted.

## 5. Results

**5.1 Version 1.** {M['tested']} pairs were tested in half A and gave {M['n_cand']} candidates. In half B {C1['bekräftad']} were confirmed, {C1['mönster att pröva']} became patterns to test and {C1['höll inte']} did not hold. With the halves swapped, {SW['tested']} pairs gave {SW['n_cand']} candidates, and {len(U1['stable_both_ways'])} pairs were confirmed both ways. In plain words: half of what looked like findings in the first half held when tested on stones the search had never seen; the other half would have been false findings had we stopped after the first step.

{chart(False)}

**5.2 What was confirmed.**

- **Known family patterns (8).** Women raise stones for their husbands (odds ratio {R1[('kvinna_resare', 'rel_make')]['or2']:.2f} in half B), several sponsors for fathers and fewer for sons, women more often for sons and less often for fathers. True but known: they describe who was left to raise the stone. That the engine finds them shows that it finds what is there.
- **A measurement artefact (1).** The ós-rune rarely stands on stones for sons (odds ratio {ART['or2']:.2f}). The trait is measured only in a few particular words, and a stone for a son has the word *sun*, which is written with the u-rune. The association comes from which words are present, not from a custom; version 2 therefore stopped pairing such traits with relations.
- **New (5).** Travel stones are raised by fewer people (odds ratio {NEW['resa']['or2']:.2f}; with a journey abroad {NEW['fard']['or2']:.2f}). Stones for fathers rarely say how or where he died ({NEW['dod_far']['or2']:.2f}) and rarely that he died abroad ({NEW['borta_far']['or2']:.2f}): the fathers died at home, and a death at home was nothing to tell. Crosses and apostrophe-like word dividers go together ({NEW['kors_apostrof']['or2']:.2f}, with province, time, text length and carver constant), a craft trait nobody had asked about.

**5.3 What did not hold.** All {C1['höll inte']} candidates that failed passed the adjustment in half A, and some looked strong: carver's signature and the plus sign as word divider had the odds ratio {SIGPLUS['or']:.2f} in half A and {SIGPLUS['or2']:.2f} in half B.

**5.4 Version 2.** With more traits and more forbidden pairs, {M2['tested']:,} pairs were tested. Only {M2['n_cand']} became candidates and 2 were confirmed: that stones for fathers rarely tell how he died (already in version 1) and rarely mention a journey ({R2[('msg_resa', 'rel_foralder')]['or2']:.2f}). With the halves swapped one was confirmed: the monophthong in *ok* goes with apostrophe-like word dividers ({OK2['or2']:.2f}). The search for pairs was exhausted on this material.

**5.5 The districts.** {len(LK['scanned'])} traits were searched in half A ({LK['n_A']} stones), and {len(LK['confirmed'])} circles became candidates. In half B ({LK['n_B']} stones) one held: the form *þennsa* ('this') in a circle of {round(TH['radius'] / 1000)} km around Sö 190 at Ytterenhörna, {TH['O']} stones against {TH['E']:.2f} expected in half A and {TH['OB']} against {TH['EB']:.2f} in half B, Holm-corrected p = {TH['holm']}. The form crosses the border between Södermanland and Uppland and is used by {len(TH['carvers'])} carvers: a form of the district rather than a carver's habit. One circle became a pattern to test, and {LC['höll inte']} did not hold.

## 6. Discussion

**What the method can do.** Of {N_CAND} candidates in all, {N_OK} were confirmed and {N_FAIL} did not hold. That means that roughly every other hit from a search already adjusted for multiple testing does not hold on new material, and that districts that stand out are almost always chance. The two-step procedure makes it possible to let the computer suggest questions and still report only what holds. It found the known, which shows that it works, and a few things nobody had asked about.

**Against earlier research.** The danger of choosing among many tests after the results are known is well described (Ioannidis 2005; Gelman & Loken 2014). Here it shows in numbers on a humanistic material: without the second half, eighteen hits would have been reported that did not hold on new material.

**Weaknesses, in order of weight.**

1. **The halves are not new material.** They are two parts of the same corpus, divided parish by parish. An association found in only one region shows in both halves. The test protects against chance, not against errors in Rundata present throughout the material.
2. **The measurement shows too.** The ós-rune and the sons show that the engine finds structure in how the traits are measured, not only in what they measure. Every confirmed association must be read against how the traits are defined.
3. **No limit for the method.** The plan did not fix in advance how many candidates should hold.
4. **Diminishing returns.** Version 2 found almost no new pairs; most of what can be found this way in this material has been found.

**Where the method should not be used.** As proof: a confirmed candidate is a question that has passed a first test and needs a plan of its own, locked, before it is called a finding.

**What would overturn the method.** If confirmed candidates regularly failed when tested under their own plans on other material.

## 7. Conclusion

A discovery engine that searches one half of the runestones and tests in the other found {N_OK} associations that held out of {N_CAND} candidates. It shows both what the computer can find and how much of it is chance. The next step is to test the new associations under plans of their own and to use the same procedure on the runestones of Denmark and Norway.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)), with the changes made after that version up to 31 October 2026. No release with a DOI exists yet; when one is made, the report will refer to it. All code, the analysis plans and the result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The plans: `analysplaner/2026-10-28-upptacktsmotorn.md` and `analysplaner/2026-10-29-upptacktsmotorn-v2.md`, with their checksums in the `.sha256` files beside them.
- Version 1: `src/discovery.py`, `r/discovery.R`; results and frozen lists in `utdata/upptackt/`.
- Version 2: `src/discovery_v2.py`, `r/discovery_v2.R`, `r/discovery_lokal.R`; results and frozen lists in `utdata/upptackt_v2/`.
- The report is built by `utdata/blogg/build/build_rapport_upptackt.py`, which reads every number from the result files and stops if anything disagrees.

## References

- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 57 (1), pp. 289–300.
- Gelman, A. & Loken, E. 2014. The statistical crisis in science. *American Scientist* 102 (6), pp. 460–465.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Ioannidis, J. P. A. 2005. Why most published research findings are false. *PLoS Medicine* 2 (8), e124.
- Kulldorff, M. 1997. A spatial scan statistic. *Communications in Statistics – Theory and Methods* 26 (6), pp. 1481–1496.
- Kvant, V. 2026. *Vitki {APP_VERSION}: method description* (METHODS.md). https://github.com/Precatio/runes
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.
- Wood, S. N. 2017. *Generalized Additive Models: An Introduction with R*. 2nd ed. Boca Raton: Chapman & Hall/CRC.

:::box The essentials
- A computer can suggest questions about the runestones that nobody has asked, but roughly half of what it finds is chance.
- By searching one half and testing in the other, the two can be told apart before anything is reported.
- What held was mostly the known, and a few new things: the fathers died at home, and the crosses follow a particular word divider.
:::
"""

JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS"
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body
assert "I klartext" in body and "In plain words" in body_en  # mallen version 4
assert "## Sammanfattning\n\n**Vad som inte är prövat.**" in body
assert body.split("\n", 1)[0].startswith("*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion 1, 2026-10-31. Tidslinje: ")

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Formler och syfte"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_upptackt.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", len(body.split("## Data")[0].split()), "före Data och kod;", len(body_en.split()), "words")

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
        assert not [p_ for p_ in blog._all() if p_.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Rapport|upptackt", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
