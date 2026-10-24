"""Artikeln om gravmonumentens hantverk (sv + en): studie 1 i analysplaner/2026-10-24-skanningarna.md (låst, SHA-256
55bb1048…). Runor mot de långa linjerna (ramar, slingkanter, ornamentik) inom varje objekt, 33 gravmonument kring 1100
mot 71 runstenar, ur de öppna 3D-skanningarna. Varje siffra läses ur utdata/forskningsplan/s_analys.json och
s3_varians.json och låses med asserts.
    cd utdata/blogg/build && ../../../.venv/bin/python build_gravhallar.py [--write | --update DOC]"""
import datetime as dt
import io
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "utdata", "forskningsplan"))
from src import blog_figures  # noqa: E402
from src.scan_sources import DATASETS  # noqa: E402
import s_analys as sa  # noqa: E402

FP = os.path.join(ROOT, "utdata", "forskningsplan")
R = json.load(open(os.path.join(FP, "s_analys.json"), encoding="utf-8"))
S1 = R["studie1"]
H = S1["huvud"]
V3 = json.load(open(os.path.join(FP, "s3_varians.json"), encoding="utf-8"))
DS = {d["key"]: d for d in DATASETS}

# ---- the locked numbers ------------------------------------------------------------------------------------------------
G = [x for x in S1["objekt"] if x["typ"] == "gravmonument"]
S = [x for x in S1["objekt"] if x["typ"] == "runsten"]
assert (len(G), len(S)) == (33, 71) and H["apex_vinkel_deg"]["n_grav"] == 33
med = lambda xs, m: float(np.median([x[m] for x in xs]))
assert (round(med(G, "apex_vinkel_deg"), 1), round(med(S, "apex_vinkel_deg"), 1)) == (-1.6, -0.4)
assert (round(med(G, "spårdjup_mm"), 2), round(med(S, "spårdjup_mm"), 2)) == (-0.13, -0.05)
A = H["apex_vinkel_deg"]
assert (round(A["skillnad"], 1), round(A["ci90"][0], 1), round(A["ci90"][1], 1), round(A["p"], 2)) == (-1.2, -3.2, 0.6, 0.29)
assert H["utfall"] == "samma mönster" and all(H[m]["q"] > 0.05 for m in ("spårdjup_mm", "spårbredd_mm", "bottenradie_mm"))
robust = [S1["robust_mjuk_bergart"], S1["robust_atos"], *S1["robust_utan_serie"].values()]
assert len(robust) == 8 and all(r and r["utfall"] == "samma mönster" for r in robust)
UV = S1["robust_utan_serie"]["vastergotland"]
assert UV["apex_vinkel_deg"]["n_grav"] == 9 and round(UV["spårdjup_mm"]["q"], 3) == 0.049
assert sum(1 for x in G if x["serie"] == "vastergotland") == 24
assert sum(1 for x in G if x["bergart"] == "okänd") == 15
# how much the angle differs between two runestones (object medians of the rune grooves), for scale
A_DATA = sa.load("automatisk_korning_alla")
ang = [sa.med([s for d in ds for s in d["slices"]], "apex_vinkel_deg", {"rune"})[0]
       for ds in sa.objects(A_DATA).values() if sa.object_type(ds[0]) == "runsten"]
SD_ANG = float(np.std([a for a in ang if a is not None], ddof=1))
assert 10 <= SD_ANG <= 20, SD_ANG
WITHIN = V3["apex_vinkel_deg"]["shares"]["Residual"]
# Two checks added after the plan was locked (utdata/forskningsplan/resultat.md, Avvikelser): lines at least 10 mm
# from every rune slice (misclassified staves left out), and runes against cracks and weathering (the method's
# sensitivity)
EH = json.load(open(os.path.join(FP, "s1_efterhand.json"), encoding="utf-8"))["10"]
assert EH["n"] == [33, 71] and EH["utfall"] == "samma mönster" and round(EH["apex_vinkel_deg"]["skillnad"], 1) == -1.1
KS = json.load(open(os.path.join(FP, "s1_kanslighet.json"), encoding="utf-8"))
assert round(KS["spårdjup_mm"]["runa_minus_oregelbundet"], 2) == 0.24 and KS["spårdjup_mm"]["p_irr"] < 1e-12
assert round(KS["apex_vinkel_deg"]["runa_minus_oregelbundet"], 1) == -2.5 and KS["apex_vinkel_deg"]["p_irr"] < 1e-4
assert KS["spårdjup_mm"]["n_irr"] == 103
assert round(100 * WITHIN) == 89


# ---- the figure: where the slices lie on a grave slab and a runestone, by stroke class ---------------------------------
def figure(lang: str) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    picks = {"Vg 50": None, "Hs 21": None}
    for d in A_DATA:
        if d.get("signum") in picks and picks[d["signum"]] is None:
            picks[d["signum"]] = d
    fig, axs = plt.subplots(1, 2, figsize=(11, 5.2))
    col = {"rune": "#1b7837", "ornament": "#c51b7d", "irregular": "#c8c8c8", "isolated": "#c8c8c8"}
    for ax, (sg, d) in zip(axs, picks.items()):
        P = np.array([s["point"] for s in d["slices"] if s.get("point")])
        F = [s.get("feature") for s in d["slices"] if s.get("point")]
        n = np.array(d["normal"], float); n /= np.linalg.norm(n)
        a = np.cross(n, [0, 0, 1] if abs(n[2]) < 0.9 else [1, 0, 0]); a /= np.linalg.norm(a)
        b = np.cross(n, a)
        X, Y = P @ a, P @ b
        for f in ("irregular", "isolated", "ornament", "rune"):
            m = np.array([x == f for x in F])
            ax.scatter(X[m], Y[m], s=2.2, c=col[f], linewidths=0)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_title({"Vg 50": ("Gravhällen Vg 50", "The grave slab Vg 50"),
                      "Hs 21": ("Runstenen Hs 21", "The runestone Hs 21")}[sg][lang == "en"], fontsize=12)
    from matplotlib.lines import Line2D
    lab = (("Runor", "Långa linjer: ramar, slingkanter, ornamentik", "Övriga spår") if lang == "sv"
           else ("Runes", "Long lines: frames, band edges, ornament", "Other grooves"))
    fig.legend([Line2D([], [], marker="o", ls="", color=c, ms=7) for c in ("#1b7837", "#c51b7d", "#c8c8c8")], lab,
               loc="lower center", ncol=3, frameon=False, fontsize=10)
    plt.tight_layout(rect=(0, 0.07, 1, 1))
    out = io.BytesIO()
    fig.savefig(out, format="png", dpi=110)
    plt.close(fig)
    vg, hs = DS["vastergotland"], DS["halsingland"]
    if lang == "sv":
        alt = "Två stenar sedda rakt framifrån, med varje uppmätt snitt som en prick: gröna runor, röda långa linjer."
        text = ("*Varje prick är ett tvärsnitt som Vitki har mätt, färgad efter vad spåret är. Till vänster gravhällen "
                "Vg 50, till höger runstenen Hs 21. På båda ligger runorna (grönt) inne i en ram eller slinga av långa "
                "linjer (rött); en del runstavar inne i bandet på Vg 50 har klassats som linjer, se texten. Skanningar: Vg 50 av Laila Kitzler Åhfeldt (Riksantikvarieämbetet) inom "
                f"{vg['project']}, CC BY 4.0, doi:{vg['doi']}; Hs 21 av Henrik Zedig (Länsstyrelsen Västra Götalands "
                f"län) inom projektet {hs['project']}, CC BY 4.0, doi:{hs['doi']}.*")
    else:
        alt = "Two stones seen straight on, every measured slice a dot: green runes, red long lines."
        text = ("*Every dot is a cross-section that Vitki has measured, coloured by what the groove is. Left the grave "
                "slab Vg 50, right the runestone Hs 21. On both the runes (green) lie inside a frame or band of long "
                "lines (red); some rune staves inside the band on Vg 50 have been classed as lines, see the text. Scans: Vg 50 by Laila Kitzler Åhfeldt (Swedish National Heritage Board) in the research "
                f"project Runristandets dynamik (2009–2014), CC BY 4.0, doi:{vg['doi']}; Hs 21 by Henrik Zedig "
                f"(Västra Götaland County Administrative Board) in the project {hs['project']}, CC BY 4.0, "
                f"doi:{hs['doi']}.*")
    return f"![{alt}]({blog_figures.freeze(out.getvalue())})\n{text}"


SDA = f"{SD_ANG:.0f}"
sv = lambda x, nd: f"{x:.{nd}f}".replace(".", ",")  # Swedish decimal comma
title = "Samma hantverk? Gravhällarna kring 1100 mätta mot runstenarna"
summary = ("Höggs de första kristna gravhällarna av runstenarnas hantverkare eller av en ny sorts stenhuggare? Vi mätte "
           "33 gravmonument och 71 runstenar i öppna 3D-skanningar och jämförde runorna med ramarna på samma sten.")
body = f"""Den som står framför en gravhäll vid Husaby eller Häggesleds kyrka i Västergötland ser något som både liknar och inte liknar en runsten. Runorna löper i ett band längs kanten, det finns ett kors och ibland ett djur, men stenen ligger ner, den är ofta av kalksten och den hör till en kyrka. Hällarna höggs kring år 1100, när runstenarna slutade resas och de första stenkyrkorna byggdes.

Vem som höll i mejseln är en öppen fråga i forskningen. Var det samma hantverkare som hade ristat runstenarna, som nu fick nya beställningar? Eller kom det en ny sorts stenhuggare med kyrkbyggena, som lärt sig sitt yrke på annat håll?

Den frågan går inte att avgöra med en enda mätning. Men en del av den går att pröva i själva stenytan, och det har vi gjort.

## Vad ett spår kan berätta

Ett huggspår är en liten fåra, några millimeter djup. Skär man tvärs igenom den får man en profil: smal och spetsig, eller bred och rundad. Profilen beror på verktyget, på hur det hölls och på stenen. Laila Kitzler Åhfeldt har i många år använt 3D-skanningar för att mäta just detta, och hon har tillsammans med Henrik Zedig gjort en stor del av skanningarna fritt tillgängliga.

Vitki mäter profilen automatiskt, tvärsnitt för tvärsnitt, och vet för varje spår om det är en runa eller en lång linje: en ram, kanten på en runslinga eller ornamentik.

Problemet är stenen. Kalksten och granit ger olika spår även med samma verktyg och samma hand. Jämför man gravhällarnas spår rakt av med runstenarnas mäter man mest skillnaden mellan bergarterna.

## Knepet: jämför inom samma sten

Vi jämförde därför runorna med de långa linjerna **på samma sten**. Det är som att jämföra två penndrag på samma papper: papperet är detsamma, så en skillnad mellan dragen ligger i pennan eller handen, inte i papperet.

{figure("sv")}

Om gravhällarna höggs av två slags hantverkare – en som gjorde ramarna och ornamentiken och en som lade till runorna – eller med andra verktyg för bokstäver än för linjer, borde runorna och linjerna skilja sig åt på ett annat sätt på gravhällarna än på runstenarna. Det är den förutsägelsen vi prövade. Vi låste planen, och gränsen för vad som skulle räknas som lika, innan vi såg ett enda resultat.

## Vad mätningen visar

På runstenarna är runorna och linjerna nästan likadant huggna. Spårens öppningsvinkel skiljer i mitten av materialet bara {sv(abs(med(S, 'apex_vinkel_deg')), 1)} grader mellan runor och linjer på samma sten. På gravhällarna är skillnaden {sv(abs(med(G, 'apex_vinkel_deg')), 1)} grader. Det kan jämföras med att vinkeln i regel skiljer omkring {SDA} grader mellan två olika runstenar.

Skillnaden mellan gravhällarna och runstenarna är alltså {sv(abs(A['skillnad']), 1)} grader. Med {len(G)} gravmonument och {len(S)} runstenar ligger den troliga skillnaden mellan {sv(abs(A['ci90'][0]), 1)} grader åt ena hållet och {sv(A['ci90'][1], 1)} åt det andra. Vi hade bestämt i förväg att en skillnad under 5 grader skulle räknas som samma mönster, och hela intervallet ligger inom den gränsen. En så stor skillnad som vi fick skulle slumpen ensam ge ungefär tre gånger av tio.

Spårens djup, bredd och bottens rundning säger samma sak: ingen skillnad som går att skilja från slumpen.

Resultatet håller när vi bara jämför med runstenar av sandsten och kalksten, när vi tar bort en skanningsserie i taget och när vi bara använder Riksantikvarieämbetets egna serier. I en av de åtta kontrollerna, utan Västergötland och med bara nio gravmonument kvar, ser spåren på gravhällarna något grundare ut i runorna än i linjerna. Det är en svag signal i en liten grupp, och vi redovisar den utan att bygga något på den.

Kan mätningen alls se en skillnad mellan två sorters spår på samma sten? Det prövade vi efteråt, med spår som verkligen är olika: runorna mot sprickor och vittring på samma sten. Där syns skillnaden tydligt. Runorna är i mitten av materialet {sv(KS['spårdjup_mm']['runa_minus_oregelbundet'], 2)} millimeter djupare och har {sv(abs(KS['apex_vinkel_deg']['runa_minus_oregelbundet']), 1)} grader smalare vinkel, och på {KS['spårdjup_mm']['n_irr']} stenar och hällar är det en skillnad som slumpen i praktiken aldrig skulle ge. Mätningen ser alltså skillnader på någon grad och några tiondels millimeter inom en sten. Att runor och ramar ser likadana ut är därför inte ett tecken på ett trubbigt instrument.

## Vad det betyder

På gravhällarna kring 1100 är bokstäverna och linjerna huggna med samma grepp, precis som på runstenarna. Vi ser inget spår av en arbetsdelning där någon annan högg ramarna, och inget spår av särskilda verktyg för runorna.

Det stämmer med tanken att gravmonumenten höggs inom samma hantverk som runstenarna, av människor som kunde både runor och ornamentik. Det är vår tolkning, inte något mätningen bevisar. Mätningen säger att om det fanns en ny sorts stenhuggare, så höll de samma förhållande mellan runor och ramar som runristarna: samma grepp för båda.

## Vad vi inte kan se

Metoden ser spårens form, alltså verktyget och hur det hölls. Den ser inte hur stenen planerades, hur bandet lades ut eller vem som beställde den. Två hantverkare med samma utbildning och samma verktyg skulle se likadana ut i våra mätningar.

Vi har heller inget facit: ingen gravhäll där vi vet att två händer var inblandade. Därför kan vi säga att vi inte ser någon skillnad, men inte hur stor skillnad en sådan arbetsdelning skulle ha gett.

Det Vitki kallar linjer är i praktiken alla långa och böjda spår. Vi kontrollerade på sex stenar innan vi räknade att runorna mestadels hamnar som runor och ramarna som linjer. Men klassningen är automatisk och inte felfri: på Vg 50 i bilden ovan har en del runstavar inne i bandet hamnat bland linjerna. Sådana fel gör runor och linjer mer lika i mätningen. Därför räknade vi om efteråt med bara de linjer som ligger minst en centimeter från varje runa, alltså ramar och ornamentik men inga stavar i bandet. Resultatet blev detsamma: en skillnad på {sv(abs(EH['apex_vinkel_deg']['skillnad']), 1)} grader och samma mönster.

{len([x for x in G if x['serie'] == 'vastergotland'])} av gravmonumenten kommer från Västergötland, och {len([x for x in G if x['bergart'] == 'okänd'])} av dem är fragment som bara har nummer i Cecilia Ljungs genomgång av gravmonumenten, inte någon egen post i Rundata, och därför ingen angiven bergart.

## Och ristarna?

Samma skanningar visar också hur mycket ett spår varierar på en och samma sten. Omkring {round(100 * WITHIN)} procent av variationen i vinkeln ligger mellan tvärsnitten på samma sten, inte mellan stenarna. Den som vill känna igen en ristare på spåren behöver därför många mätningar per sten, inte några enstaka. Vi har ännu för få stenar med säkra ristare i de öppna skanningarna för att säga hur stor del av variationen som är ristarens egen.

:::box Det viktigaste i korthet
- Gravhällarna kring 1100 visar i våra mätningar inga spår av en arbetsdelning mellan bokstäver och ornamentik: runor och ramar är huggna med samma grepp, precis som på runstenarna.
- Det talar för att gravmonumenten höggs inom samma hantverk som runstenarna, men det är en tolkning – mätningen ser verktyget och handen, inte vem som stod bakom.
- Jämförelsen inom en och samma sten gör att bergarten inte styr resultatet. Det är ett sätt att använda öppna 3D-skanningar som fungerar även när stenarna är av olika slag.
- Ett enskilt spår säger lite. Variationen på en sten är så stor att den som vill mäta en ristares hand behöver många tvärsnitt per sten.
:::

:::box Så räknade vi
Planen låstes 2026-10-24, innan något test kördes (analysplaner/2026-10-24-skanningarna.md, SHA-256 55bb1048…). Underlaget är 142 öppna skanningsfiler i sex serier, mätta med alla spår och med varje tvärsnitt klassat som runa, lång linje eller annat. För varje objekt med minst tio tvärsnitt i både runor och linjer räknade vi skillnaden mellan medianerna. Huvudtestet jämförde den skillnaden för öppningsvinkeln mellan gravmonument och runstenar med ett permutationstest (10 000 omflyttningar); 90-procentsintervallet kommer från 2 000 bootstrapdragningar, och gränsen för samma mönster var ±5 grader. Djup, bredd och bottenradie prövades som sidomått med Benjamini–Hochberg-justering. Två kontroller lades till efter att planen låsts och redovisas som sådana: linjer minst 10 mm från varje runa, och runor mot sprickor och vittring (Wilcoxons test). Alla siffror, skript och mätningar finns i Vitkis öppna kod.
:::

## Se själv

Alla 142 skanningar finns som projekt i Vitki, märkta automatisk körning, med tvärsnitten och syntesen. Skanningarna kan laddas ned från Zenodo och läsas in i huggspårsanalysen, där varje tvärsnitt går att granska.

## Källor

- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones.* Theses and Papers in Archaeology B:9. Stockholms universitet.
- Kitzler Åhfeldt, L. 2024. 3D-data Runstenar i Södermanland. Riksantikvarieämbetet. doi:{DS['sodermanland']['doi']}.
- Kitzler Åhfeldt, L. 2024. 3D-data Runstenar signerade av Åsmund Kåresson. Riksantikvarieämbetet. doi:{DS['asmund']['doi']}.
- Kitzler Åhfeldt, L. 2024. 3D-data Runstenar och tidigkristna gravmonument i Västergötland. Riksantikvarieämbetet. doi:{DS['vastergotland']['doi']}.
- Kitzler Åhfeldt, L. 2025. 3D-data Tidigkristna gravmonument Östergötland och Småland. Zenodo. doi:{DS['gravmonument_og_sm']['doi']}.
- Kitzler Åhfeldt, L. & Zedig, H. 2024. 3D-data Runstenar i Medelpad. Riksantikvarieämbetet. doi:{DS['medelpad']['doi']}.
- Kitzler Åhfeldt, L. & Zedig, H. 2025. 3D-data Runstenar i Hälsingland. Riksantikvarieämbetet. doi:{DS['halsingland']['doi']}.
- Ljung, C. 2016. *Under runristad häll. Tidigkristna gravmonument i 1000-talets Sverige.* Stockholm Studies in Archaeology 67. Stockholms universitet.
- Samnordisk runtextdatabas, version 3.1 (ODbL)."""

title_en = "The same craft? The grave slabs of around 1100 measured against the runestones"
summary_en = ("Were the first Christian grave slabs cut by the runestones' craftsmen or by a new kind of stonemason? We "
              "measured 33 grave monuments and 71 runestones in open 3D scans and compared the runes with the frames on "
              "the same stone.")
body_en = f"""Anyone standing in front of a grave slab at Husaby or Häggesled church in Västergötland sees something that both does and does not look like a runestone. The runes run in a band along the edge, there is a cross and sometimes an animal, but the stone lies flat, it is often limestone and it belongs to a church. The slabs were cut around the year 1100, when runestones stopped being raised and the first stone churches were built.

Who held the chisel is an open question in research. Was it the same craftsmen who had carved the runestones, now taking new commissions? Or did a new kind of stonemason come with the church building, someone who had learnt the trade elsewhere?

That question cannot be settled with a single measurement. But part of it can be tested in the stone surface itself, and that is what we have done.

## What a groove can tell

A carved groove is a small furrow, a few millimetres deep. Cut straight across it and you get a profile: narrow and pointed, or broad and rounded. The profile depends on the tool, on how it was held and on the stone. Laila Kitzler Åhfeldt has for many years used 3D scans to measure exactly this, and together with Henrik Zedig she has made a large share of the scans freely available.

Vitki measures the profile automatically, cross-section by cross-section, and knows for every groove whether it is a rune or a long line: a frame, the edge of a runic band or ornament.

The problem is the stone. Limestone and granite give different grooves even with the same tool and the same hand. Compare the grave slabs' grooves directly with the runestones' and you mostly measure the difference between the rocks.

## The trick: compare within the same stone

We therefore compared the runes with the long lines **on the same stone**. It is like comparing two pen strokes on the same sheet of paper: the paper is the same, so a difference between the strokes lies in the pen or the hand, not in the paper.

{figure("en")}

If the grave slabs had been cut by two kinds of craftsmen – one making the frames and ornament and one adding the runes – or with other tools for letters than for lines, the runes and the lines should differ in another way on the grave slabs than on the runestones. That is the prediction we tested. We locked the plan, and the bound for what would count as the same, before we saw a single result.

## What the measurement shows

On the runestones the runes and the lines are cut almost alike. In the middle of the material the grooves' opening angle differs by only {abs(med(S, 'apex_vinkel_deg')):.1f} degrees between runes and lines on the same stone. On the grave slabs the difference is {abs(med(G, 'apex_vinkel_deg')):.1f} degrees. For comparison, the angle usually differs by about {SDA} degrees between two different runestones.

The difference between the grave slabs and the runestones is thus {abs(A['skillnad']):.1f} degrees. With {len(G)} grave monuments and {len(S)} runestones the plausible difference lies between {abs(A['ci90'][0]):.1f} degrees one way and {A['ci90'][1]:.1f} the other. We had decided in advance that a difference under 5 degrees would count as the same pattern, and the whole interval lies within that bound. Chance alone would give a difference as large as ours about three times in ten.

The grooves' depth, width and the rounding of their bottom say the same: no difference that can be told apart from chance.

The result holds when we compare only with runestones of sandstone and limestone, when we leave out one scan series at a time and when we use only the National Heritage Board's own series. In one of the eight checks, without Västergötland and with only nine grave monuments left, the grooves on the grave slabs look somewhat shallower in the runes than in the lines. It is a weak signal in a small group, and we report it without building anything on it.

Can the measurement see a difference between two kinds of groove on the same stone at all? We tested that afterwards, with grooves that really are different: the runes against cracks and weathering on the same stone. There the difference shows clearly. In the middle of the material the runes are {KS['spårdjup_mm']['runa_minus_oregelbundet']:.2f} millimetres deeper and have a {abs(KS['apex_vinkel_deg']['runa_minus_oregelbundet']):.1f} degrees narrower angle, and across {KS['spårdjup_mm']['n_irr']} stones and slabs that is a difference chance would practically never give. So the measurement sees differences of a degree or so and a few tenths of a millimetre within one stone. That runes and frames look alike is therefore not a sign of a blunt instrument.

## What it means

On the grave slabs of around 1100 the letters and the lines are cut with the same grip, just as on the runestones. We see no trace of a division of labour where someone else cut the frames, and no trace of special tools for the runes.

That fits the idea that the grave monuments were cut within the same craft as the runestones, by people who could do both runes and ornament. That is our interpretation, not something the measurement proves. The measurement says that if there was a new kind of stonemason, they kept the same relation between runes and frames as the rune carvers: the same grip for both.

## What we cannot see

The method sees the shape of the grooves, that is the tool and how it was held. It does not see how the stone was planned, how the band was laid out or who commissioned it. Two craftsmen with the same training and the same tools would look alike in our measurements.

Nor do we have a key: no grave slab where we know that two hands were involved. So we can say that we see no difference, but not how large a difference such a division of labour would have given.

What Vitki calls lines is in practice every long and curved groove. Before counting, we checked on six stones that the runes mostly end up as runes and the frames as lines. But the classification is automatic and not flawless: on Vg 50 in the picture above some rune staves inside the band have ended up among the lines. Errors like that make runes and lines more alike in the measurement. So afterwards we recomputed with only the lines that lie at least a centimetre from every rune, that is frames and ornament but no staves in the band. The result was the same: a difference of {abs(EH['apex_vinkel_deg']['skillnad']):.1f} degrees and the same pattern.

{len([x for x in G if x['serie'] == 'vastergotland'])} of the grave monuments come from Västergötland, and {len([x for x in G if x['bergart'] == 'okänd'])} of them are fragments that only have numbers in Cecilia Ljung's survey of the grave monuments, not an entry of their own in Rundata, and therefore no stated rock type.

## And the carvers?

The same scans also show how much a groove varies on one and the same stone. About {round(100 * WITHIN)} per cent of the variation in the angle lies between the cross-sections on the same stone, not between the stones. Anyone who wants to recognise a carver by the grooves therefore needs many measurements per stone, not a few. We still have too few stones with certain carvers in the open scans to say how much of the variation is the carver's own.

:::box The essentials in brief
- In our measurements the grave slabs of around 1100 show no trace of a division of labour between letters and ornament: runes and frames are cut with the same grip, just as on the runestones.
- That speaks for the grave monuments having been cut within the same craft as the runestones, but it is an interpretation – the measurement sees the tool and the hand, not who stood behind them.
- Comparing within one and the same stone keeps the rock type from steering the result. It is a way of using open 3D scans that works even when the stones are of different kinds.
- A single groove says little. The variation on one stone is so large that anyone who wants to measure a carver's hand needs many cross-sections per stone.
:::

:::box How we counted
The plan was locked on 24 October 2026, before any test was run (analysplaner/2026-10-24-skanningarna.md, SHA-256 55bb1048…). The material is 142 open scan files in six series, measured with all grooves and with every cross-section classed as rune, long line or other. For every object with at least ten cross-sections in both runes and lines we computed the difference between the medians. The main test compared that difference for the opening angle between grave monuments and runestones with a permutation test (10,000 shuffles); the 90 per cent interval comes from 2,000 bootstrap draws, and the bound for the same pattern was ±5 degrees. Depth, width and bottom radius were tested as secondary measures with Benjamini–Hochberg adjustment. Two checks were added after the plan was locked and are reported as such: lines at least 10 mm from every rune, and runes against cracks and weathering (Wilcoxon's test). All figures, scripts and measurements are in Vitki's open code.
:::

## See for yourself

All 142 scans are projects in Vitki, labelled automatic run, with the cross-sections and the synthesis. The scans can be downloaded from Zenodo and loaded into the groove analysis, where every cross-section can be reviewed.

## Sources

- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones.* Theses and Papers in Archaeology B:9. Stockholm University.
- Kitzler Åhfeldt, L. 2024. 3D data Runestones in Södermanland. Swedish National Heritage Board. doi:{DS['sodermanland']['doi']}.
- Kitzler Åhfeldt, L. 2024. 3D data Runestones signed by Åsmund Kåresson. Swedish National Heritage Board. doi:{DS['asmund']['doi']}.
- Kitzler Åhfeldt, L. 2024. 3D data Runestones and early Christian grave monuments in Västergötland. Swedish National Heritage Board. doi:{DS['vastergotland']['doi']}.
- Kitzler Åhfeldt, L. 2025. 3D data Early Christian grave monuments in Östergötland and Småland. Zenodo. doi:{DS['gravmonument_og_sm']['doi']}.
- Kitzler Åhfeldt, L. & Zedig, H. 2024. 3D data Runestones in Medelpad. Swedish National Heritage Board. doi:{DS['medelpad']['doi']}.
- Kitzler Åhfeldt, L. & Zedig, H. 2025. 3D data Runestones in Hälsingland. Swedish National Heritage Board. doi:{DS['halsingland']['doi']}.
- Ljung, C. 2016. *Under runristad häll. Tidigkristna gravmonument i 1000-talets Sverige.* Stockholm Studies in Archaeology 67. Stockholm University.
- Scandinavian Runic-text Database, version 3.1 (ODbL)."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M)
assert body_en.count("## ") == body.count("## ") and ":::box Det viktigaste i korthet" in body
assert "insikt" not in body.lower() and "nyhet" not in body.lower()
out = {"slug": "samma-hantverk-gravhallarna-kring-1100", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Huggspår och 3D", "Datering och stil"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "gravhallar.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "gravhallar.json"), len(body.split()), "ord")

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
                 "topic": "gravhällar|huggspår", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
