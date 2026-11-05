"""Forskningsrapport (låst mall utdata/rapporter/MALL.md, version 4; Fullt prövat fynd): "Barnen ärvde led ur
föräldrarnas namn – förälder och barn delar ett namnled nästan dubbelt så ofta som slumpen ger" (sv + en). Den låsta
planen analysplaner/2026-10-29-namngivning-i-familjen.md (H1–H5), tilläggsplanen analysplaner/2026-10-31-namnled-trappan.md
och den explorativa omblandningen inom härad. Alla siffror asserteras mot utdata/namngivning/*.json (rapportversion 2:
också mot rapport_kontroll.json, som rapport_kontroll.py skriver ur korpusen och handkontrollen data/people_check.json).
Rapportversion 3 (2026-11-05): rättelser efter en andra, oberoende läsning av ändringarna i version 2 (H4 som skattning,
inte fynd; granskningscommit 6eae0af; det som version 2 inte loggade).
    ../../../.venv/bin/python build_rapport_namnled.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

APP_VERSION = "3.0.0"  # the Vitki version the analysis was made in (tag v3.0.0 + the commits named in Data och kod), not the current one
assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 3  # version 1: 2026-10-31; version 2: 2026-11-05
TODAY = "2026-11-05"  # rapportversionens datum, fast i byggaren (mallen version 3)
PUB_V1 = "2026-10-31"  # version 1 publicerades då; publiceringsdatumet behålls
SLUG = "barnen-arvde-namnled"
_pub = [a for a in json.load(open(os.path.join(ROOT, "web", "content", "articles.json"), encoding="utf-8"))["posts"]
        if a.get("slug") == SLUG]
assert len(_pub) == 1 and _pub[0]["publishedAt"][:10] == PUB_V1
TL_SV = ("materialet frystes 2026-10-28; analysplanen låstes 2026-10-29; analysen kördes 2026-10-29; tilläggsplanen för "
         "känslighetsanalyserna låstes och kördes 2026-10-31; den explorativa omblandningen inom härad kördes 2026-10-31")
TL_EN = ("the material was frozen 2026-10-28; the analysis plan was locked 2026-10-29; the analysis was run 2026-10-29; the "
         "addendum plan for the sensitivity analyses was locked and run 2026-10-31; the exploratory shuffle within hundreds "
         "was run 2026-10-31")
ND = os.path.join(ROOT, "utdata", "namngivning")
R = json.load(open(os.path.join(ND, "namngivning.json"), encoding="utf-8"))
TR = json.load(open(os.path.join(ND, "trappan.json"), encoding="utf-8"))
HR = json.load(open(os.path.join(ND, "harad.json"), encoding="utf-8"))
KO = json.load(open(os.path.join(ND, "rapport_kontroll.json"), encoding="utf-8"))  # rapport_kontroll.py
FP = "3f58e9339191761e"
assert KO["korpus"] == FP and KO["korpus_beraknad"] == "2026-10-28" and KO["n_runstenar"] == 2321
# the commits at which the result files were saved (the analysis was run on the code at these commits); in a copy of the
# repository with its history the files must be byte for byte those commits' files
COMMITS = {"namngivning.json": ("806b915", "2026-10-29"), "trappan.json": ("9e158b6", "2026-10-31"),
           "harad.json": ("d77c99f", "2026-10-31")}
if os.path.isdir(os.path.join(ROOT, ".git")):
    for f_, (c_, _) in COMMITS.items():
        rel = f"utdata/namngivning/{f_}"
        assert subprocess.run(["git", "show", f"{c_}:{rel}"], cwd=ROOT, capture_output=True, check=True).stdout == \
            open(os.path.join(ROOT, rel), "rb").read(), rel
        assert json.loads(subprocess.run(["git", "show", f"{c_}:web/package.json"], cwd=ROOT, capture_output=True,
                                         check=True).stdout)["version"] == APP_VERSION
        assert subprocess.run(["git", "log", "-1", "--format=%h %ad", "--date=short", "--", rel], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout.split() == [c_, COMMITS[f_][1]], rel
# rapportversion 3: the builder and the check file as reviewed before archiving (version 2) are in commit 6eae0af
REVIEW_COMMIT = "6eae0af"
if os.path.isdir(os.path.join(ROOT, ".git")):
    _files = subprocess.run(["git", "show", "--name-only", "--format=", REVIEW_COMMIT], cwd=ROOT, capture_output=True,
                            text=True, check=True).stdout.split()
    assert {"utdata/blogg/build/build_rapport_namnled.py", "utdata/namngivning/rapport_kontroll.json"} <= set(_files), _files
SHA = {k: open(os.path.join(ROOT, "analysplaner", f"{k}.sha256")).read().split()[0][:16]
       for k in ("2026-10-29-namngivning-i-familjen", "2026-10-31-namnled-trappan")}
assert SHA["2026-10-29-namngivning-i-familjen"].startswith("74eb5113") and SHA["2026-10-31-namnled-trappan"].startswith("9d0247a8")

d1 = lambda x: f"{100 * x:.1f}".replace(".", ",")  # noqa: E731  andel i procent
e1 = lambda x: f"{100 * x:.1f}"  # noqa: E731
n_sv = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731  1 292
n_en = lambda n: f"{n:,}"  # noqa: E731  1,292
NPERM = 9999  # omblandningar i analys.py, trappa.py och harad.py; det minsta möjliga p är 1 / (NPERM + 1)
P_FLOOR = 1 / (NPERM + 1)


def pfmt(p, en=False):
    if abs(p - P_FLOOR) < 1e-12:  # golvet: det sanna p-värdet kan vara mindre
        return "p ≤ 0.0001" if en else "p ≤ 0,0001"
    s = f"{p:.4f}" if p < 0.001 else f"{p:.3f}" if p < 0.1 else f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


FLOOR_SV = "p ≤ 0,0001 (det minsta möjliga med 9 999 omblandningar)"
FLOOR_EN = "p ≤ 0.0001 (the smallest possible with 9,999 shuffles)"


# ---- the locked plan --------------------------------------------------------------------------------------------------
A, RA, RB = R["resultat"]["alla"], R["resultat"]["A"], R["resultat"]["B"]
H1, H2, H3, H4, H5 = (A[k] for k in ("H1", "H2", "H3", "H4", "H5"))
assert R["status"] == {"H1": "håller", "H2": "antydan", "H3": "ingen skillnad påvisad", "H4": "ingen skillnad påvisad", "H5": "håller"}
assert (H1["par"], d1(H1["andel"]), d1(H1["vantat"]), H1["p"]) == (1292, "5,3", "2,8", 0.0001)
assert (H5["par"], d1(H5["andel"]), d1(H5["vantat"]), H5["p"]) == (1066, "6,7", "2,9", 0.0001)
assert abs(R["holm"]["H1"] - 0.0005) < 1e-9 and abs(R["holm"]["H5"] - 0.0005) < 1e-9 and abs(R["holm"]["H2"] - 0.0129) < 1e-4
assert (d1(RA["H1"]["andel"]), d1(RA["H1"]["vantat"]), d1(RB["H1"]["andel"]), d1(RB["H1"]["vantat"])) == ("4,9", "2,3", "5,8", "3,4")
assert RA["H1"]["p"] == 0.0002 and RB["H1"]["p"] == 0.0005 and RA["H5"]["p"] == 0.0001 and RB["H5"]["p"] == 0.0001
assert (d1(H2["andel"]), d1(H2["vantat"])) == ("14,9", "12,5") and RA["H2"]["p"] > 0.2 and RB["H2"]["p"] < 0.01
assert (d1(H3["overskott_1"]), d1(H3["overskott_0"]), round(H3["p"], 2)) == ("3,1", "2,6", 0.89)
assert (d1(H4["overskott_1"]), d1(H4["overskott_0"]), round(H4["p"], 2)) == ("1,1", "2,9", 0.22)
# rapportversion 2: H4 is smaller on the Christian stones in both halves, but not clear in either
assert (d1(RA["H4"]["skillnad"]), d1(RB["H4"]["skillnad"])) == ("-1,0", "-2,5") and RA["H4"]["p"] > 0.5 and RB["H4"]["p"] > 0.2
# rapportversion 3: the lede and the box give H4 as a smaller excess that may be chance (the plan's verdict: no difference)
assert (pfmt(H4["p"]), pfmt(H4["p"], True)) == ("p = 0,22", "p = 0.22") and H4["overskott_1"] < H4["overskott_0"]
assert f"den explorativa omblandningen inom härad kördes {COMMITS['harad.json'][1]}" in TL_SV and "exploratory shuffle within hundreds was run 2026-10-31" in TL_EN
for f_ in ("analys.py", "trappa.py", "harad.py"):
    assert f"NPERM = {NPERM}\n" in open(os.path.join(ND, f_), encoding="utf-8").read(), f_
assert H1["p"] == H5["p"] == P_FLOOR and abs(R["holm"]["H1"] - 5 * P_FLOOR) < 1e-12 and abs(R["holm"]["H5"] - 5 * P_FLOOR) < 1e-12
DE = R["beskrivning"]
assert (DE["par"], DE["syskonpar"], DE["samma_namn"]) == (1292, 1066, 6)
MOR = DE["mor_vs_far"]["true"]
assert (MOR["par"], d1(MOR["delat"])) == (27, "3,7")
# the hand check: the rule for the dead person's kin relation (src/people.py), sample 2, coded blind (rapport_kontroll.py)
PK = KO["personkontroll"]
assert (PK["n"], PK["relationsgrupp_ratt"]) == (40, 38) and "kodade före jämförelsen" in PK["urval"]
# the naming lies 30–50 years before the style group: early stones RAK–Pr2 (980–1050), late Pr3–Pr5 (1050–1130)
SY = KO["stilgrupper_ar"]
assert (SY["tidig_fran"], SY["sen_till"]) == (980, 1130) and (SY["tidig_fran"] - 30, SY["sen_till"] - 30) == (950, 1100)

# ---- the addendum ladder ----------------------------------------------------------------------------------------------
assert TR["plan"] == "analysplaner/2026-10-31-namnled-trappan.md" and TR["all_hold"] is True
T1, T5 = TR["H1"], TR["H5"]
assert T1["all_hold"] and T5["all_hold"] and T1["lopo_holds"] and T5["lopo_holds"]
assert abs(T1["rungs"]["huvud"]["andel"] - H1["andel"]) < 1e-12 and abs(T5["rungs"]["huvud"]["andel"] - H5["andel"]) < 1e-12
assert (T1["rungs"]["ett_par_per_sten"]["par"], T5["rungs"]["ett_par_per_sten"]["par"]) == (714, 488)
assert (T1["lopo"]["U"]["par"], round(T1["lopo"]["U"]["andel_kvar"], 2), round(T1["lopo"]["U"]["p"], 3)) == (534, 0.41, 0.011)
assert all(v["p"] == P_FLOOR for k, v in T1["lopo"].items() if k != "U") and T5["lopo"]["U"]["andel_kvar"] < 2 / 3
# the stones behind the pairs (Material): one pair per stone keeps one pair from each stone, so its count is the number
# of stones with a pair (714 and 488)
assert "drop_duplicates(\"signum\")" in open(os.path.join(ND, "trappa.py"), encoding="utf-8").read()
N_ST_PC, N_ST_SIB = T1["rungs"]["ett_par_per_sten"]["par"], T5["rungs"]["ett_par_per_sten"]["par"]

# ---- exploratory: within hundreds -------------------------------------------------------------------------------------
assert HR["explorativt"] is True
X1, X5 = HR["H1"]["harad"], HR["H5"]["harad"]
assert (d1(X1["vantat"]), X1["p"], d1(X5["vantat"]), round(X5["p"], 3)) == ("3,3", 0.0001, "5,6", 0.053)
assert (HR["H1"]["n_harader"], HR["H5"]["n_harader"]) == (113, 100)

title = "Barnen ärvde led ur föräldrarnas namn – förälder och barn delar ett namnled nästan dubbelt så ofta som slumpen ger"
title_en = "Children inherited parts of their parents' names – parent and child share a name element almost twice as often as chance gives"
summary = ("Förregistrerad studie. På runstenarna delar förälder och barn ett namnled, som Holm- i Holmger och Holmfast, i 5,3 "
           "procent av paren, mot 2,8 procent om namnen parades slumpvis. Det håller i båda halvorna av materialet och i "
           "alla känslighetsanalyser, och i en explorativ kontroll där bara namnen i samma härad blandas om. Någon försvagning "
           "under runstenstiden kan inte påvisas; på de kristna stenarna är överskottet mindre, men skillnaden kan vara slump "
           f"({pfmt(H4['p'])}). Seden gällde "
           "en minoritet av familjerna.")
summary_en = ("Pre-registered study. On the runestones parent and child share a name element, like Holm- in Holmger and Holmfast, "
              "in 5.3 percent of the pairs, against 2.8 percent if the names were paired at random. It holds in both halves of "
              "the material and in every sensitivity analysis, and in an exploratory check where only the names within the same hundred are shuffled. "
              "No weakening during the runestone period can be shown; on the Christian stones the excess is smaller, but the "
              f"difference may be chance ({pfmt(H4['p'], True)}). The custom concerned a minority of families.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki {APP_VERSION}. "
           f"https://vitkirunor.se/en/forskningsrapporter/{SLUG}")
GLOSS_SV = "[https://vitkirunor.se/forskningsrapporter/begrepp](https://vitkirunor.se/forskningsrapporter/begrepp)"
GLOSS_EN = "[https://vitkirunor.se/en/forskningsrapporter/begrepp](https://vitkirunor.se/en/forskningsrapporter/begrepp)"
for p_ in ("web/src/app/forskningsrapporter/begrepp/page.tsx", "web/src/app/en/forskningsrapporter/begrepp/page.tsx"):
    assert os.path.exists(os.path.join(ROOT, p_)), p_
GH = "[https://github.com/Precatio/runes](https://github.com/Precatio/runes)"
CM = {k: v[0] for k, v in COMMITS.items()}
# the Rundata reference (METHODS.md: "version 2014 med RUNDATA.xls från 2018"; data/README.md: ODbL 1.0 / DbCL 1.0)
_methods = open(os.path.join(ROOT, "METHODS.md"), encoding="utf-8").read()
_readme = open(os.path.join(ROOT, "data", "README.md"), encoding="utf-8").read()
assert "version 2014 med RUNDATA.xls från 2018" in _methods and "ODbL 1.0" in _readme and "DbCL 1.0" in _readme
RUNDATA_SV = ("Samnordisk runtextdatabas (Rundata), version 2014 med RUNDATA.xls uppdaterad 2018. Institutionen för nordiska språk, Uppsala universitet. "
              "Open Database License 1.0 / Database Contents License 1.0.")
RUNDATA_EN = ("Scandinavian Runic-text Database (Rundata), 2014 version with RUNDATA.xls updated 2018. Department of Scandinavian Languages, Uppsala "
              "University. Open Database License 1.0 / Database Contents License 1.0.")
LOG_SV = f"""## Ändringslogg

- **Version 2, {TODAY}.** Rättelser före den permanenta arkiveringen i Zenodo, efter en granskning av rapporten mot resultatfilerna och koden. Huvudresultaten (förälder–barn och syskon) och nivån är oförändrade.
- *Kristna kännetecken (H4).* Version 1 sade att seden var lika stark på stenar med kristna kännetecken och att den inte försvagades. Överskottet är mindre där ({d1(H4['overskott_1'])} mot {d1(H4['overskott_0'])} procentenheter, {pfmt(H4['p'])}), åt samma håll i båda halvorna, men inte säkert. Sammanfattningen, avsnitt 5.2, 6 och 7 och korthetsrutan säger nu att en försvagning inte kan påvisas och att seden är något svagare på de kristna stenarna, men inte säkert.
- *Kontrollen av relationerna.* Version 1 angav att relationerna var rätt på 38 av 40 stenar och att felen var omkring en på tjugo. Den kontrollen gällde en närliggande regel för den dödes släktrelation, inte namnparen, som inte har kontrollerats mot handkodning. Avsnitt 3 och svaghet 3 är rättade.
- *p-värdena vid golvet.* p = 0,0001 är det minsta möjliga med 9 999 omblandningar och skrivs nu p ≤ 0,0001 (Holm-korrigerat p ≤ 0,0005).
- *Syskonen inom härad.* Att omblandningen inom härad är skev uppåt för syskonen var ett antagande; det står nu som en möjlighet som inte har prövats.
- *Namngivningens tid.* Tidsjämförelsen gäller namngivningen omkring 950–1100, inte omkring år 1000.
- *Språk och form.* Korthetsrutan säger att barn *ibland*, inte ofta, fick ett led ur förälderns namn; meningen om resare med samma namn som den döde är förtydligad; antalet stenar står i Material; tidslinjen har frysdatumet; Data och kod anger commit och kommandon för att köra om analysen i stället för en framtida DOI; Rundata anges med version och licenser; länk till ordlistan, förklaring av ensidigt och tvåsidigt test och diagrammets källrad är tillagda.
- **Version 3, {TODAY}.** Rättelser efter en andra, oberoende läsning av ändringarna i version 2. Huvudresultaten (förälder–barn och syskon) och nivån är oförändrade.
- *Kristna kännetecken (H4).* Version 2 skrev att seden är ”något svagare” på de kristna stenarna, ”men inte säkert”. Det läste skattningen som en egenskap hos seden, fast testet enligt planen inte påvisade någon skillnad ({pfmt(H4['p'])}, och inte säkert i någon av halvorna). Ingressen, sammanfattningens slutsats och korthetsrutan säger nu att överskottet är mindre men att skillnaden kan vara slump.
- *Data och kod.* Byggaren och kontrollfilen i den form de granskades inför arkiveringen anges med commit `{REVIEW_COMMIT}`.
- *Det som version 2 också ändrade utan att det stod i loggen.* Tidslinjen fick också datumet för den explorativa omblandningen inom härad ({COMMITS['harad.json'][1]}).
"""
LOG_EN = f"""## Change log

- **Version 2, {TODAY}.** Corrections before the permanent archiving in Zenodo, after a review of the report against the result files and the code. The main results (parent–child and siblings) and the level are unchanged.
- *Christian markers (H4).* Version 1 said that the custom was as strong on stones with Christian markers and that it did not weaken. The excess is smaller there ({e1(H4['overskott_1'])} against {e1(H4['overskott_0'])} percentage points, {pfmt(H4['p'], True)}), in the same direction in both halves, but not clearly so. The abstract, sections 5.2, 6 and 7 and the essentials box now say that a weakening cannot be shown and that the custom is somewhat weaker on the Christian stones, but not clearly so.
- *The check of the relations.* Version 1 stated that the relations were right on 38 of 40 stones and that the errors were about one in twenty. That check concerned a related rule for the dead person's kin relation, not the name pairs, which have not been checked against hand coding. Section 3 and weakness 3 are corrected.
- *p-values at the floor.* p = 0.0001 is the smallest possible with 9,999 shuffles and is now written p ≤ 0.0001 (Holm-corrected p ≤ 0.0005).
- *Siblings within the hundred.* That the shuffle within the hundred is biased upwards for siblings was an assumption; it now stands as a possibility that has not been tested.
- *The time of the naming.* The comparison over time concerns name-giving around 950–1100, not around the year 1000.
- *Language and form.* The essentials box says that children *sometimes*, not often, received an element of a parent's name; the sentence on sponsors with the same name as the dead is clarified; the number of stones is given in Material; the timeline has the freeze date; Data and code gives the commits and commands to rerun the analysis instead of a future DOI; Rundata is cited with version and licences; a link to the glossary, an explanation of one-sided and two-sided tests and the chart's source line are added.
- **Version 3, {TODAY}.** Corrections after a second, independent reading of the changes in version 2. The main results (parent–child and siblings) and the level are unchanged.
- *Christian markers (H4).* Version 2 said that the custom is "somewhat weaker" on the Christian stones, "but not clearly so". That read the estimate as a property of the custom, although the test by the plan showed no difference ({pfmt(H4['p'], True)}, and not clear in either half). The lede, the abstract's conclusion and the essentials box now say that the excess is smaller but that the difference may be chance.
- *Data and code.* The builder and the check file as reviewed before archiving are named with commit `{REVIEW_COMMIT}`.
- *What version 2 also changed without logging it.* The timeline also gained the date of the exploratory shuffle within hundreds ({COMMITS['harad.json'][1]}).
"""


def chart(sv):
    f = d1 if sv else e1
    n = n_sv if sv else n_en
    lab = (("Förälder och barn", "Syskon", "Observerat", "Väntat, omblandning inom landskapet", "Väntat, omblandning inom häradet")
           if sv else ("Parent and child", "Siblings", "Observed", "Expected, shuffled within the province", "Expected, shuffled within the hundred"))
    rows = [":::chart Par som delar ett namnled, procent" if sv else ":::chart Pairs that share a name element, percent"]
    for g, h, x in ((lab[0], H1, X1), (lab[1], H5, X5)):
        rows += [f"# {g}", f"+{lab[2]} | {f(h['andel'])} | {n(h['par'])} {'par' if sv else 'pairs'}", f"{lab[3]} | {f(h['vantat'])} |",
                 f"{lab[4]} | {f(x['vantat'])} |"]
    rows += ["Källa: Rundata; omblandning 9 999 gånger. Diagram: Vitki, efter Rundata." if sv else
             "Source: Rundata; 9,999 shuffles. Chart: Vitki, after Rundata.", ":::"]
    return "\n".join(rows)


def rung(r, sv=True):
    f = d1 if sv else e1
    return f"{f(r['andel'])} {'mot' if sv else 'against'} {f(r['vantat'])} {'procent' if sv else 'percent'}, {pfmt(r['p'], not sv)}"


L1, L5 = T1["rungs"], T5["rungs"]

body = f"""*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY} (version 1 publicerad {PUB_V1}; ändringarna står sist). Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, personnamn, namnled, variation, namngivning, familj, permutationstest, förregistrering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** I det germanska namnskicket kunde ett barn få ett led ur en förälders namn, som Holmfast efter Holmger. Namnforskningen beskriver skicket, men hur ofta det syns på runstenarna har inte mätts mot slumpen. Frågan här är om förälder och barn, och syskon, delar namnled oftare än slumpen ger, och om seden försvagades med tiden och med kristendomen.
**Material.** {n_sv(H1['par'])} förälder–barn-par från {N_ST_PC} stenar och {n_sv(H5['par'])} syskonpar från {N_ST_SIB} stenar, ur relationerna på de {n_sv(KO['n_runstenar'])} svenska vikingatida runstenarna i Samnordisk runtextdatabas (Rundata).
**Metod.** Förregistrerad studie med fem test och Holm-korrigering. Namnen delas i förled och efterled ur materialet självt, och andelen par som delar ett led jämförs med 9 999 omblandningar av namnen inom landskapet. Intern replikering i två halvor och sex känslighetsanalyser enligt en låst tilläggsplan.
**Resultat.** Förälder och barn delar ett namnled i {d1(H1['andel'])} procent av paren, mot {d1(H1['vantat'])} procent vid slumpvis parning, Holm-korrigerat p ≤ 0,0005. Det håller i båda halvorna och i alla känslighetsanalyser, också utan Uppland, med tiden konstant och med ett par per sten, och i en explorativ omblandning inom häradet ({d1(X1['vantat'])} procent väntat). Syskon delar namnled i {d1(H5['andel'])} procent mot {d1(H5['vantat'])}; det överskottet krymper när namnen bara blandas om inom häradet. Ingen skillnad påvisas över tid (överskott {d1(H3['overskott_1'])} mot {d1(H3['overskott_0'])} procentenheter, {pfmt(H3['p'])}). På stenar med kristna kännetecken är överskottet mindre ({d1(H4['overskott_1'])} mot {d1(H4['overskott_0'])} procentenheter), men skillnaden är inte säker ({pfmt(H4['p'])}).
**Slutsats.** Barn fick led ur föräldrarnas namn, men det var en sed för en minoritet, ungefär ett par av tjugo. Någon försvagning under runstenstiden kan inte påvisas; på de kristna stenarna är överskottet mindre, men skillnaden kan vara slump.

## 1. Inledning

Germanska personnamn är ofta sammansatta av två led, och namnforskningen har länge beskrivit hur leden gick i arv inom släkten, genom variation (ett led återkommer, Holmger och Holmfast), allitteration (samma begynnelseljud) och upprepning av hela namnet (Janzén 1947). Lena Peterson (2007) har förtecknat runstenarnas namn och deras led. Birgit Sawyer (2000) läste runstenarna som uttryck för familj och arv.

Det som saknas är ett mått på hur ofta namnleden faktiskt går i arv på runstenarna, jämfört med vad slumpen ger när man tar hänsyn till att vissa led är vanliga i en trakt, och om seden ändrades när kristendomen kom. Syftet här är att mäta det.

## 2. Förregistrering: hypotes och plan

Hypoteserna, måtten och tolkningsreglerna skrevs ned i en analysplan den 29 oktober 2026, innan några namnpar hade jämförts. Planen har kontrollsumman SHA-256 `{SHA['2026-10-29-namngivning-i-familjen']}…` (se Data och kod). Före låsningen var bara antalet relationer känt och ett exempel, U 135, där sonen bär faderns namn.

Planen prövar fem hypoteser med Holm-korrigering: H1 att förälder och barn delar namnled oftare än slumpen ger, H2 att de oftare allittererar, H3 att överskottet är mindre på sena stenar, H4 att det är mindre på stenar med kristna kännetecken och H5 att syskon delar namnled oftare än slumpen ger. En hypotes *håller* när Holm-p är under 0,05 och riktningen är densamma med p under 0,05 i båda halvorna.

Planen innehöll inte projektets fasta känslighetsanalyser, som är byggda för samband mellan två drag på en sten. Motsvarande steg för namnpar bestämdes därför i en tilläggsplan den 31 oktober 2026 (SHA-256 `{SHA['2026-10-31-namnled-trappan']}…`), innan de räknades. Ett av stegen, utan korta led, hade räknats efter huvudkörningen och låstes som steg i tilläggsplanen. En omblandning inom härad (avsnitt 5.4) är explorativ: den räknades efter tilläggsplanen, för att pröva en svaghet som planen inte tog upp.

## 3. Material

- **Stenarna.** De {n_sv(KO['n_runstenar'])} svenska vikingatida runstenarna i Samnordisk runtextdatabas (Rundata), fryst för analysen den 28 oktober 2026. Bara runstenar.
- **Relationerna** – far, mor, son, dotter, bror och syster – och namnen läses ur Rundatas översättning och normalisering med en egen regeluppsättning för personer och släktord. Den har inte kontrollerats mot handkodning av namnpar; en närliggande regel för den dödes släktrelation var rätt på {PK['relationsgrupp_ratt']} av {PK['n']} stenar i ett nytt urval. Paret räknas också när resaren bär samma namn som den döde fadern, modern eller sonen; reglerna gör annars aldrig en person släkt med sig själv.
- **Paren.** {n_sv(H1['par'])} förälder–barn-par från {N_ST_PC} stenar och {n_sv(H5['par'])} syskonpar från {N_ST_SIB} stenar, varje namnpar en gång per socken, så att en familj med många stenar, som Jarlabankes, inte räknas flera gånger.
- **Namnleden.** Ett namn delas i förled och efterled när båda leden finns i minst tre andra namn i materialet; annars räknas hela namnet som ett led. Två namn *delar ett led* när de har något led gemensamt eller är samma namn.
- **Tiden** efter stenens stilgrupp (Gräslund 2006): tidiga stenar RAK–Pr2, sena Pr3–Pr5.

## 4. Metod

Statistiska begrepp förklaras i ordlistan, {GLOSS_SV}.

**4.1 Måttet.** Andelen par som delar ett namnled jämförs med andelen när det andra namnet i varje par blandas om slumpvis bland paren inom samma landskap, 9 999 gånger. Omblandningen behåller landskapets namnförråd, så att ett led som är vanligt i en trakt inte räknas som arv. Testet är ensidigt: det frågar bara om paren delar led oftare än slumpen ger.

**4.2 De andra hypoteserna.** H2 som H1 med samma begynnelseljud som mått. H3 och H4 jämför överskottet per par, det observerade minus det väntade, mellan sena och tidiga stenar respektive stenar med och utan kristna kännetecken. De testen är tvåsidiga: en skillnad åt vilket håll som helst räknas.

**4.3 Korrigering och replikering.** Holm-korrigering (Holm 1979) över de fem testen. Varje hypotes prövas också i var halva för sig.

**4.4 Känslighetsanalyserna** enligt tilläggsplanen, för H1 och H5: halvorna; utan ett landskap i taget (landskap med minst 30 par; signifikans krävs bara där minst två tredjedelar av paren är kvar); tiden konstant, med omblandning inom landskap och tidsskikt; ett par per sten; utan korta led och de datadrivna skräpleden -ni, -bbi och -einn; och bara delade led, utan par där båda bär samma hela namn. Ett steg håller när andelen är större än den väntade och p är under 0,05.

**4.5 Avvikelser från planen.** Inga. Tilläggsplanens körning ger samma andelar som huvudkörningen; halvornas p-värden skiljer sig i sista decimalen eftersom slumpdragningarna kommer i en annan ordning.

## 5. Resultat

**5.1 Förälder och barn (H1).** {n_sv(H1['par'])} par: {d1(H1['andel'])} mot {d1(H1['vantat'])} procent, {FLOOR_SV}, Holm-korrigerat p ≤ 0,0005. Halva A: {d1(RA['H1']['andel'])} mot {d1(RA['H1']['vantat'])} procent, {pfmt(RA['H1']['p'])}. Halva B: {d1(RB['H1']['andel'])} mot {d1(RB['H1']['vantat'])} procent, {pfmt(RB['H1']['p'])}. H1 *håller*. I klartext: ungefär ett förälder–barn-par av tjugo delar ett namnled, mot ett av trettiofem om namnen fördelades slumpvis i samma landskap. Oftast går leden *-björn*, *Tor-*, *-sten*, *-fast*, *Sig-* och *-mund* i arv, till exempel Holmger och Holmfast (U 289), Ingevald och Ingemund (U 296) och Gudmar och Gudbjörn (Sö 164). På {DE['samma_namn']} stenar bär sonen faderns hela namn, som Östen efter Östen (U 135).

{chart(True)}

**5.2 Syskon, allitteration, tid och kristendom (H5, H2, H3, H4).** Syskon: {n_sv(H5['par'])} par, {rung(H5)}, Holm-korrigerat p ≤ 0,0005, och i båda halvorna ({pfmt(RA['H5']['p'])} och {pfmt(RB['H5']['p'])}); H5 *håller*. Allitteration mellan förälder och barn: {d1(H2['andel'])} mot {d1(H2['vantat'])} procent, Holm-korrigerat p = 0,013, men bara i halva B; en antydan. Över tid: överskottet är {d1(H3['overskott_1'])} procentenheter på sena stenar och {d1(H3['overskott_0'])} på tidiga, {pfmt(H3['p'])}; ingen skillnad påvisas. Kristna kännetecken: överskottet är {d1(H4['overskott_1'])} procentenheter på stenar med kristna kännetecken mot {d1(H4['overskott_0'])} på de andra, {pfmt(H4['p'])}. Det är mindre i båda halvorna ({d1(RA['H4']['skillnad']).replace('-', '−')} och {d1(RB['H4']['skillnad']).replace('-', '−')} procentenheter), men inte säkert i någon; skillnaden är inte påvisad. Mor och barn: bara {MOR['par']} par, för få för att säga något.

**5.3 Känslighetsanalyserna.** Alla håller, för både förälder–barn och syskon:

- Tiden konstant: förälder–barn {rung(L1['tiden_konstant'])}; syskon {rung(L5['tiden_konstant'])}.
- Ett par per sten: förälder–barn ({L1['ett_par_per_sten']['par']} par) {rung(L1['ett_par_per_sten'])}; syskon ({L5['ett_par_per_sten']['par']} par) {rung(L5['ett_par_per_sten'])}.
- Utan korta led: förälder–barn {rung(L1['utan_korta_led'])}; syskon {rung(L5['utan_korta_led'])}.
- Bara delade led, utan samma hela namn: förälder–barn {rung(L1['bara_delade_led'])}; syskon {rung(L5['bara_delade_led'])}.
- Utan ett landskap i taget: utan Uppland står {T1['lopo']['U']['par']} förälder–barn-par kvar, färre än två tredjedelar, och riktningen håller ({rung(T1['lopo']['U'])}); utan vart och ett av de andra landskapen med minst 30 par är p ≤ 0,0001. Syskonen likadant.

**5.4 Omblandning inom härad (explorativt).** Familjer i samma bygd delar ett lokalt namnförråd, och omblandning inom landskapet kan därför överskatta arvet. Blandas namnen bara om inom häradet blir den väntade andelen för förälder–barn {d1(X1['vantat'])} procent mot observerade {d1(H1['andel'])}, {pfmt(X1['p'])}, i {HR['H1']['n_harader']} härader: fyndet står kvar. För syskon blir den väntade andelen {d1(X5['vantat'])} procent mot {d1(H5['andel'])}, {pfmt(X5['p'])}: överskottet krymper och är inte längre säkert. Den omblandningen kan dock vara skev uppåt för syskonen, eftersom en sten med flera syskon ger många par och den slumpvisa partnern i ett litet härad ofta blir ett annat syskon i samma familj; det har inte prövats.

## 6. Diskussion

**Vad fyndet säger.** Barn fick led ur föräldrarnas namn oftare än slumpen ger, också när bygdens namnförråd hålls konstant, och oberoende av tid, landskap och hur många namn en sten har. Men skicket gällde en minoritet: ungefär ett par av tjugo, mot ett av trettiofem väntat. Det var en möjlighet i namngivningen, inte en regel. Över tid syns ingen förändring. På stenar med kristna kännetecken är överskottet mindre, men skillnaden är inte säker: materialet kan varken visa att skicket försvagades i de kristna familjerna eller att det höll sig oförändrat.

**Mot tidigare forskning.** Resultatet ger ett mått åt det namnskick som namnforskningen har beskrivit (Janzén 1947) och visar att det syns i runstenarnas relationer, inte bara i enskilda exempel. Om skicket var svagare i de familjer som markerade sin kristna tro kan materialet inte avgöra; riktningen pekar dit, men skillnaden ligger inom slumpens ram.

**Svagheter, i ordning efter vikt.**

1. **Bygdens namnförråd.** Grannar delar namn, och en del av överskottet kan vara lokalt namnmode. För förälder–barn står fyndet kvar inom härad; för syskon krymper det (5.4).
2. **Leddelningen är grov.** Den bygger på materialet självt och ger några skräpled. Utan korta led och skräpled står fyndet kvar, men smeknamnsformer som Holmi räknas som enledade och kan dölja arv.
3. **Relationerna är lästa med regler.** Namnparen har inte kontrollerats mot handkodning (avsnitt 3). En felläst relation ger ett falskt par eller tappar ett verkligt.
4. **Barnen är vuxna.** Den som reser stenen är oftast vuxen, så namngivningen ligger 30–50 år före stenens stilgrupp. Tidsjämförelsen gäller alltså namngivningen omkring {SY['tidig_fran'] - 30}–{SY['sen_till'] - 30}, med tidiga stenar RAK–Pr2 och sena Pr3–Pr5, inte stenarna själva.

**Vad som skulle fälla fyndet.** Att överskottet försvann med en omblandning inom socknen, när materialet blir stort nog för det, eller att en handkodning av leden gav samma andel för förälder–barn som för slumpvisa par.

## 7. Slutsats

På runstenarna delar förälder och barn ett namnled i {d1(H1['andel'])} procent av paren, mot {d1(H1['vantat'])} procent vid slumpvis parning, och det tål varje känslighetsanalys. Barnen ärvde led ur föräldrarnas namn, men bara i en minoritet av familjerna. Någon försvagning under runstenstiden kan inte påvisas.

## Data och kod

Analysen kördes i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([https://vitkirunor.se](https://vitkirunor.se)): huvudanalysen vid commit `{CM['namngivning.json']}` (2026-10-29), känslighetsanalyserna vid commit `{CM['trappan.json']}` och omblandningen inom härad vid commit `{CM['harad.json']}` (båda 2026-10-31) i {GH}, där resultatfilerna lades in. All kod, analysplanerna och resultatfilerna finns där öppet under GPL-3.0.

- Materialet: korpus `{FP}`, Rundatas svenska vikingatida runstenar som de frystes 2026-10-28 (`data/cache/r/corpus/{FP}/corpus.csv`, byggd ur `data/rundata.json`).
- Analysplanerna: `analysplaner/2026-10-29-namngivning-i-familjen.md` och `analysplaner/2026-10-31-namnled-trappan.md`, med kontrollsummorna i `.sha256`-filerna bredvid.
- Analysen: `utdata/namngivning/analys.py` (resultat `namngivning.json`, paren i `par.csv`); känslighetsanalyserna `trappa.py` (`trappan.json`); den explorativa omblandningen inom härad `harad.py` (`harad.json`).
- Köra om analysen, från projektmappen: `.venv/bin/python utdata/namngivning/analys.py`, `.venv/bin/python utdata/namngivning/trappa.py` och `.venv/bin/python utdata/namngivning/harad.py`.
- Namnen och relationerna: `src/entities.py`; kontrollen av den dödes släktrelation: `src/people.py` mot `data/people_check.json` (`utdata/namngivning/rapport_kontroll.py`).
- Rapporten byggs av `utdata/blogg/build/build_rapport_namnled.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer; byggaren och kontrollfilen i den form de granskades inför arkiveringen finns i commit `{REVIEW_COMMIT}`.

## Referenser

- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Janzén, A. (red.) 1947. *Personnamn*. Nordisk kultur 7. Stockholm: Bonnier.
- Kvant, V. 2026. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md). [https://github.com/Precatio/runes](https://github.com/Precatio/runes)
- Peterson, L. 2007. *Nordiskt runnamnslexikon*. 5 uppl. Uppsala: Institutet för språk och folkminnen.
- {RUNDATA_SV}
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford: Oxford University Press.

:::box Det viktigaste i korthet
- Barn fick ibland ett led ur förälderns namn, som Holmfast efter Holmger, och det syns på runstenarna mer än slumpen ger.
- Det var en möjlighet för några familjer, inte en regel för alla: ungefär ett par av tjugo.
- Någon försvagning av namnskicket under runstenstiden kan inte påvisas; på de kristna stenarna är överskottet mindre, men det kan vara slump.
:::

{LOG_SV}
"""

body_en = f"""*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY} (version 1 published {PUB_V1}; the changes are listed at the end). Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, personal names, name elements, variation, name-giving, family, permutation test, pre-registration. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** In the Germanic naming custom a child could receive an element of a parent's name, like Holmfast after Holmger. Onomastics describes the custom, but how often it shows on the runestones has not been measured against chance. The question here is whether parent and child, and siblings, share name elements more often than chance gives, and whether the custom weakened over time and with Christianity.
**Material.** {n_en(H1['par'])} parent–child pairs from {N_ST_PC} stones and {n_en(H5['par'])} sibling pairs from {N_ST_SIB} stones, from the relations on the {n_en(KO['n_runstenar'])} Swedish Viking-Age runestones in the Scandinavian Runic-text Database (Rundata).
**Method.** A pre-registered study with five tests and Holm correction. The names are divided into first and second elements from the material itself, and the share of pairs sharing an element is compared with 9,999 shuffles of the names within the province. Internal replication in two halves and six sensitivity analyses under a locked addendum plan.
**Results.** Parent and child share a name element in {e1(H1['andel'])} percent of the pairs, against {e1(H1['vantat'])} percent with random pairing, Holm-corrected p ≤ 0.0005. It holds in both halves and in every sensitivity analysis, also without Uppland, with time held constant and with one pair per stone, and in an exploratory shuffle within the hundred ({e1(X1['vantat'])} percent expected). Siblings share name elements in {e1(H5['andel'])} percent against {e1(H5['vantat'])}; that excess shrinks when the names are shuffled only within the hundred. No difference is shown over time (excess {e1(H3['overskott_1'])} against {e1(H3['overskott_0'])} percentage points, {pfmt(H3['p'], True)}). On stones with Christian markers the excess is smaller ({e1(H4['overskott_1'])} against {e1(H4['overskott_0'])} percentage points), but the difference is not clear ({pfmt(H4['p'], True)}).
**Conclusion.** Children received elements of their parents' names, but it was a custom for a minority, about one pair in twenty. No weakening during the runestone period can be shown; on the Christian stones the excess is smaller, but the difference may be chance.

## 1. Introduction

Germanic personal names are often compounds of two elements, and onomastics has long described how the elements passed on within the family, through variation (an element recurs, Holmger and Holmfast), alliteration (the same initial sound) and repetition of the whole name (Janzén 1947). Lena Peterson (2007) has listed the names of the runestones and their elements. Birgit Sawyer (2000) read the runestones as expressions of family and inheritance.

What is missing is a measure of how often the name elements actually pass on on the runestones, compared with what chance gives when one allows for some elements being common in a district, and whether the custom changed when Christianity came. The aim here is to measure that.

## 2. Pre-registration: hypothesis and plan

The hypotheses, measures and rules of interpretation were written down in an analysis plan on 29 October 2026, before any name pairs had been compared. The plan has the SHA-256 checksum `{SHA['2026-10-29-namngivning-i-familjen']}…` (see Data and code). Before locking only the number of relations was known and one example, U 135, where the son bears the father's name.

The plan tests five hypotheses with Holm correction: H1 that parent and child share name elements more often than chance gives, H2 that they alliterate more often, H3 that the excess is smaller on late stones, H4 that it is smaller on stones with Christian markers and H5 that siblings share name elements more often than chance gives. A hypothesis *holds* when Holm p is below 0.05 and the direction is the same with p below 0.05 in both halves.

The plan did not contain the project's fixed sensitivity analyses, which are built for associations between two traits on a stone. The corresponding steps for name pairs were therefore fixed in an addendum plan on 31 October 2026 (SHA-256 `{SHA['2026-10-31-namnled-trappan']}…`), before they were computed. One of the steps, without short elements, had been computed after the main run and was locked as a step in the addendum plan. A shuffle within the hundred (section 5.4) is exploratory: it was computed after the addendum plan, to test a weakness the plan did not address.

## 3. Material

- **The stones.** The {n_en(KO['n_runstenar'])} Swedish Viking-Age runestones in the Scandinavian Runic-text Database (Rundata), frozen for the analysis on 28 October 2026. Runestones only.
- **The relations** – father, mother, son, daughter, brother and sister – and the names are read from Rundata's translation and normalisation with a purpose-built rule set for persons and kin terms. It has not been checked against hand coding of name pairs; a related rule for the dead person's kin relation was right on {PK['relationsgrupp_ratt']} of {PK['n']} stones in a new sample. The pair is also counted when the sponsor bears the same name as the dead father, mother or son; otherwise the rules never make a person kin to themselves.
- **The pairs.** {n_en(H1['par'])} parent–child pairs from {N_ST_PC} stones and {n_en(H5['par'])} sibling pairs from {N_ST_SIB} stones, each pair of names once per parish, so that a family with many stones, like Jarlabanke's, is not counted several times.
- **The name elements.** A name is divided into a first and a second element when both elements occur in at least three other names in the material; otherwise the whole name counts as one element. Two names *share an element* when they have an element in common or are the same name.
- **Time** by the stone's style group (Gräslund 2006): early stones RAK–Pr2, late Pr3–Pr5.

## 4. Method

Statistical terms are explained in the glossary, {GLOSS_EN}.

**4.1 The measure.** The share of pairs sharing a name element is compared with the share when the second name in each pair is shuffled at random among the pairs within the same province, 9,999 times. The shuffle keeps the province's stock of names, so that an element common in a district is not counted as inheritance. The test is one-sided: it asks only whether the pairs share elements more often than chance gives.

**4.2 The other hypotheses.** H2 as H1 with the same initial sound as the measure. H3 and H4 compare the excess per pair, observed minus expected, between late and early stones and between stones with and without Christian markers respectively. Those tests are two-sided: a difference in either direction counts.

**4.3 Correction and replication.** Holm correction (Holm 1979) over the five tests. Each hypothesis is also tested in each half on its own.

**4.4 The sensitivity analyses** under the addendum plan, for H1 and H5: the halves; without one province at a time (provinces with at least 30 pairs; significance required only where at least two thirds of the pairs remain); time held constant, with the shuffle within province and period; one pair per stone; without short elements and the data-driven junk elements -ni, -bbi and -einn; and only shared elements, without pairs where both bear the same whole name. A step holds when the share is greater than the expected one and p is below 0.05.

**4.5 Deviations from the plan.** None. The addendum run gives the same shares as the main run; the halves' p-values differ in the last decimal because the random draws come in a different order.

## 5. Results

**5.1 Parent and child (H1).** {n_en(H1['par'])} pairs: {e1(H1['andel'])} against {e1(H1['vantat'])} percent, {FLOOR_EN}, Holm-corrected p ≤ 0.0005. Half A: {e1(RA['H1']['andel'])} against {e1(RA['H1']['vantat'])} percent, {pfmt(RA['H1']['p'], True)}. Half B: {e1(RB['H1']['andel'])} against {e1(RB['H1']['vantat'])} percent, {pfmt(RB['H1']['p'], True)}. H1 *holds*. In plain words: about one parent–child pair in twenty shares a name element, against one in thirty-five if the names were distributed at random within the same province. The elements most often passed on are *-björn*, *Tor-*, *-sten*, *-fast*, *Sig-* and *-mund*, for example Holmger and Holmfast (U 289), Ingevald and Ingemund (U 296) and Gudmar and Gudbjörn (Sö 164). On {DE['samma_namn']} stones the son bears his father's whole name, as Östen after Östen (U 135).

{chart(False)}

**5.2 Siblings, alliteration, time and Christianity (H5, H2, H3, H4).** Siblings: {n_en(H5['par'])} pairs, {rung(H5, False)}, Holm-corrected p ≤ 0.0005, and in both halves ({pfmt(RA['H5']['p'], True)} and {pfmt(RB['H5']['p'], True)}); H5 *holds*. Alliteration between parent and child: {e1(H2['andel'])} against {e1(H2['vantat'])} percent, Holm-corrected p = 0.013, but only in half B; an indication. Over time: the excess is {e1(H3['overskott_1'])} percentage points on late stones and {e1(H3['overskott_0'])} on early ones, {pfmt(H3['p'], True)}; no difference is shown. Christian markers: the excess is {e1(H4['overskott_1'])} percentage points on stones with Christian markers against {e1(H4['overskott_0'])} on the others, {pfmt(H4['p'], True)}. It is smaller in both halves ({e1(RA['H4']['skillnad']).replace('-', '−')} and {e1(RB['H4']['skillnad']).replace('-', '−')} percentage points), but not clearly so in either; the difference is not shown. Mother and child: only {MOR['par']} pairs, too few to say anything.

**5.3 The sensitivity analyses.** All hold, for both parent–child and siblings:

- Time held constant: parent–child {rung(L1['tiden_konstant'], False)}; siblings {rung(L5['tiden_konstant'], False)}.
- One pair per stone: parent–child ({L1['ett_par_per_sten']['par']} pairs) {rung(L1['ett_par_per_sten'], False)}; siblings ({L5['ett_par_per_sten']['par']} pairs) {rung(L5['ett_par_per_sten'], False)}.
- Without short elements: parent–child {rung(L1['utan_korta_led'], False)}; siblings {rung(L5['utan_korta_led'], False)}.
- Only shared elements, without the same whole name: parent–child {rung(L1['bara_delade_led'], False)}; siblings {rung(L5['bara_delade_led'], False)}.
- Without one province at a time: without Uppland {T1['lopo']['U']['par']} parent–child pairs remain, fewer than two thirds, and the direction holds ({rung(T1['lopo']['U'], False)}); without each of the other provinces with at least 30 pairs p ≤ 0.0001. The siblings likewise.

**5.4 Shuffling within the hundred (exploratory).** Families in the same district share a local stock of names, and shuffling within the province may therefore overstate the inheritance. If the names are shuffled only within the hundred, the expected share for parent–child becomes {e1(X1['vantat'])} percent against the observed {e1(H1['andel'])}, {pfmt(X1['p'], True)}, in {HR['H1']['n_harader']} hundreds: the finding remains. For siblings the expected share becomes {e1(X5['vantat'])} percent against {e1(H5['andel'])}, {pfmt(X5['p'], True)}: the excess shrinks and is no longer clear. That shuffle may however be biased upwards for siblings, since a stone with several siblings gives many pairs and in a small hundred the random partner often becomes another sibling in the same family; this has not been tested.

## 6. Discussion

**What the finding says.** Children received elements of their parents' names more often than chance gives, also with the district's stock of names held constant, and regardless of time, province and how many names a stone has. But the custom concerned a minority: about one pair in twenty, against one in thirty-five expected. It was a possibility in name-giving, not a rule. Over time no change is seen. On stones with Christian markers the excess is smaller, but the difference is not clear: the material can show neither that the custom weakened in the Christian families nor that it stayed unchanged.

**Against earlier research.** The result gives a measure to the naming custom onomastics has described (Janzén 1947) and shows that it is visible in the runestones' relations, not only in single examples. Whether the custom was weaker in the families that marked their Christian faith the material cannot decide; the direction points that way, but the difference lies within the range of chance.

**Weaknesses, in order of weight.**

1. **The district's stock of names.** Neighbours share names, and part of the excess may be local fashion. For parent–child the finding remains within the hundred; for siblings it shrinks (5.4).
2. **The division into elements is crude.** It rests on the material itself and gives some junk elements. Without short and junk elements the finding remains, but hypocoristic forms like Holmi count as single-element names and may hide inheritance.
3. **The relations are read by rules.** The name pairs have not been checked against hand coding (section 3). A misread relation creates a false pair or loses a real one.
4. **The children are adults.** The sponsor is usually an adult, so the naming lies 30–50 years before the stone's style group. The comparison over time thus concerns name-giving around {SY['tidig_fran'] - 30}–{SY['sen_till'] - 30}, with early stones RAK–Pr2 and late ones Pr3–Pr5, not the stones themselves.

**What would overturn the finding.** If the excess disappeared with a shuffle within the parish, once the material is large enough for it, or if a hand coding of the elements gave the same share for parent–child as for random pairs.

## 7. Conclusion

On the runestones parent and child share a name element in {e1(H1['andel'])} percent of the pairs, against {e1(H1['vantat'])} percent with random pairing, and it withstands every sensitivity analysis. Children inherited elements of their parents' names, but only in a minority of families. No weakening during the runestone period can be shown.

## Data and code

The analysis was run in Vitki {APP_VERSION}, an open research tool for runestones ([https://vitkirunor.se/en](https://vitkirunor.se/en)): the main analysis at commit `{CM['namngivning.json']}` (2026-10-29), the sensitivity analyses at commit `{CM['trappan.json']}` and the shuffle within hundreds at commit `{CM['harad.json']}` (both 2026-10-31) in {GH}, where the result files were saved. All code, the analysis plans and the result files are openly available there under GPL-3.0.

- The material: corpus `{FP}`, Rundata's Swedish Viking-Age runestones as frozen on 2026-10-28 (`data/cache/r/corpus/{FP}/corpus.csv`, built from `data/rundata.json`).
- The analysis plans: `analysplaner/2026-10-29-namngivning-i-familjen.md` and `analysplaner/2026-10-31-namnled-trappan.md`, with their checksums in the `.sha256` files beside them.
- The analysis: `utdata/namngivning/analys.py` (results `namngivning.json`, the pairs in `par.csv`); the sensitivity analyses `trappa.py` (`trappan.json`); the exploratory shuffle within hundreds `harad.py` (`harad.json`).
- To rerun the analysis, from the project folder: `.venv/bin/python utdata/namngivning/analys.py`, `.venv/bin/python utdata/namngivning/trappa.py` and `.venv/bin/python utdata/namngivning/harad.py`.
- The names and relations: `src/entities.py`; the check of the dead person's kin relation: `src/people.py` against `data/people_check.json` (`utdata/namngivning/rapport_kontroll.py`).
- The report is built by `utdata/blogg/build/build_rapport_namnled.py`, which reads every number from the result files and stops if anything disagrees; the builder and the check file as reviewed before archiving are in commit `{REVIEW_COMMIT}`.

## References

- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Janzén, A. (ed.) 1947. *Personnamn*. Nordisk kultur 7. Stockholm: Bonnier.
- Kvant, V. 2026. *Vitki {APP_VERSION}: method description* (METHODS.md). [https://github.com/Precatio/runes](https://github.com/Precatio/runes)
- Peterson, L. 2007. *Nordiskt runnamnslexikon*. 5th ed. Uppsala: Institute for Language and Folklore.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford: Oxford University Press.
- {RUNDATA_EN}

:::box The essentials
- Children sometimes received an element of a parent's name, like Holmfast after Holmger, and it shows on the runestones more than chance gives.
- It was a possibility for some families, not a rule for all: about one pair in twenty.
- No weakening of the naming custom during the runestone period can be shown; on the Christian stones the excess is smaller, but that may be chance.
:::

{LOG_EN}
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
assert body.split("\n", 1)[0].startswith(f"*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY} (version 1 publicerad {PUB_V1}; ändringarna står sist). Tidslinje: materialet frystes 2026-10-28; ")
assert body_en.split("\n", 1)[0].startswith(f"*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY} (version 1 published {PUB_V1}; ")
assert REPORT_VERSION == 3 and f"Version {REPORT_VERSION}, {TODAY}" in body and f"Version {REPORT_VERSION}, {TODAY}" in body_en
assert f"commit `{REVIEW_COMMIT}`" in body.split("## Data")[1] and f"commit `{REVIEW_COMMIT}`" in body_en.split("## Data")[1]
# rapportversion 2: the corrected statements, and none of the withdrawn ones
for b, ok, bad in ((body, ["kan inte påvisas", "men skillnaden är inte säker", "överskottet mindre, men skillnaden kan vara slump", "omkring 950–1100",
                           "har inte kontrollerats mot handkodning av namnpar", "rätt på 38 av 40 stenar", FLOOR_SV, "1 292", "1 066",
                           "Barn fick ibland", "det har inte prövats", "Diagram: Vitki, efter Rundata.", "ensidigt:", "tvåsidiga:",
                           "forskningsrapporter/begrepp", "## Ändringslogg"],
                    ["lika stark", "försvagades inte", "levde kvar oförändrat", "år 1000", "en på tjugo i kontrollen", "Barn fick ofta",
                     "är dock skev", "Någon release med DOI finns ännu inte", "p = 0,0001", "Holm-korrigerat p = 0,0005",
                     "något svagare"]),
                   (body_en, ["cannot be shown", "but the difference is not clear", "the excess is smaller, but the difference may be chance", "around 950–1100",
                              "has not been checked against hand coding of name pairs", "right on 38 of 40 stones", FLOOR_EN, "1,292", "1,066",
                              "Children sometimes", "this has not been tested", "Chart: Vitki, after Rundata.", "one-sided:", "two-sided:",
                              "en/forskningsrapporter/begrepp", "## Change log"],
                    ["as strong", "did not weaken", "unchanged through", "year 1000", "one in twenty in the check", "often received",
                     "is however biased", "No release with a DOI exists yet", "p = 0.0001", "Holm-corrected p = 0.0005",
                     "somewhat weaker"])):
    for x in ok:
        assert x in b, x
    for x in bad:  # the change log quotes version 1, so only the report itself is searched
        assert x not in re.split(r"## (?:Ändringslogg|Change log)", b)[0], x
for b in (body, body_en):  # every link is absolute
    assert all(u.startswith("https://") for u in re.findall(r"\]\(([^)]+)\)", b)), re.findall(r"\]\(([^)]+)\)", b)
    assert len(b.split("## Data")[0].split()) <= 3000

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Kvinnor och barn"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_namnled.json")
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
                 "topic": "Rapport|namnled", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
