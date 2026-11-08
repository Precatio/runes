"""Artikeln om runstenarna och jorden (sv + en): Rune Palms förklaring från 1992 prövad med SGU:s jordartskarta.
Varje tal läses ur utdata/palm_jordarna/resultat.json och diagram.json (låst plan analysplaner/2026-11-08-palm-jordarna.md,
sha 85a70fa3), varje citat kontrolleras mot källans text (utdata/norge/citat.py). Kartan: utdata/palm_jordarna/karta.R.
    ../../../.venv/bin/python build_palm_jordar.py [--write | --update DOC]"""
import datetime as dt
import io
import json
import math
import os
import re
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels  # noqa: E402
from utdata.norge.citat import check  # noqa: E402

PJ = os.path.join(ROOT, "utdata", "palm_jordarna")
R = json.load(open(os.path.join(PJ, "resultat.json"), encoding="utf-8"))
D = json.load(open(os.path.join(PJ, "diagram.json"), encoding="utf-8"))
NO = json.load(open(os.path.join(ROOT, "utdata", "norge", "resultat.json"), encoding="utf-8"))["stones"]
assert R["plan_sha"] == "85a70fa3"

# ---- the numbers ------------------------------------------------------------------------------------------------------
assert (NO["norge"], NO["sverige"]) == (66, 2321)
assert (R["cells"], R["stones"], R["gravefields"], R["lands"]) == (6190, 707, 17781, 36)
P1, P2, P3, P0 = R["P1"], R["P2"], R["P3"], R["P0"]
assert P1["holds"] and P2["holds"] and P3["holds"]
q25, q75 = R["clay_quartiles"]
assert (round(100 * q25), round(100 * q75)) == (2, 38) and round(R["ratio_q75_vs_q25"], 2) == 1.45
assert round(P1["rate_ratio"], 1) == 2.8 and round(P0["rate_ratio"], 1) == 4.0
assert 4000 < 1 / P1["p_one_sided"] < 5000  # "ungefär en gång på 4 700"
ONE_IN_P1 = round(1 / P1["p_one_sided"], -2)
assert ONE_IN_P1 == 4700
assert round(P2["unadjusted"]["ratio"], 1) == 6.5 and round(P2["adjusted"]["ratio"], 1) == 2.4
assert round(100 * P2["explained_share"]) == 52 and P2["adjusted"]["p_one_sided"] < 1e-5
DOUBLE = P3["rate_ratio"] ** math.log(2)
assert round(100 * (1 - DOUBLE)) == 20 and 400 < 1 / P3["p_one_sided"] < 500  # "ungefär en gång på 450"
ONE_IN_P3 = round(1 / P3["p_one_sided"], -1)
assert ONE_IN_P3 == 440
ROB = R["robustness"]
assert all(v["p_one_sided"] < 0.05 and v["rate_ratio"] > 1 for v in ROB.values())
pc = lambda d: round(100 * d["k"] / d["n"])  # noqa: E731
LBL = ["under 10 %", "10–25 %", "25–50 %", "över 50 %"]
assert [pc(D["malar"][k]) for k in LBL] == [7, 13, 16, 19] and [pc(D["gota"][k]) for k in LBL] == [3, 3, 3, 9]
assert D["gota"]["över 50 %"]["n"] == 98
N_KVAR = 834  # runestones not moved or lost in the Viking-age Swedish area (rutor.R prints it)
TOT = NO["sverige"]

# ---- the quotes, checked against Palm's text (printed page = pdf page − 5) -----------------------------------------
PALM = "text/palm_1992_runor_och_regionalitet.txt"
Q = {
    "s107": ("Den faktor som kanske inverkar mest är att ingen hänsyn tagits till olikheterna i områdenas marktyper, "
             "t ex odlingsbar jord och skog", 112),
    "s255a": ("Runstenarna är ett fenomen knutet till en jordägande klass och de har sina främsta utbredningsområden i "
              "anslutning till de bästa jordarna", 260),
    "s255b": ("En eventuellt lägre jordbrukspotential i runstensområdena i Danmark och Götaland än i runstensområdena i "
              "Svealand kan emellertid inte vara hela förklaringen till de stora skillnaderna i antal och täthet", 260),
    "s255c": ("eliten har så att säga varit bredare", 260),
    "s259": ("i öster ett expansivt område med utvecklad råvaruhantering och sjöfart", 264),
}
for q, pdf in Q.values():
    check(PALM, q, pdf)


def bild(path: str, alt: str, text: str, max_w: int = 1600) -> str:
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return f"![{alt}]({blog_figures.freeze(out.getvalue())})\n{text}"


KARTA = os.path.join(PJ, "karta_malardalen.png")
IMG = {
    True: bild(KARTA, "Mälardalen: lera och silt, vattnet omkring år 1050 och runstenarna",
               "Mälardalen från Västerås till Östersjön. Gult är lera och silt, ljust är annan jord eller berg, blått är "
               "vatten omkring år 1050 (landhöjningen har sedan dess gjort mycket av Mälarens vikar till land), och de "
               "röda prickarna är runstenar som står kvar på sin ursprungliga plats. Karta: Vitki, efter SGU:s "
               "jordartskarta 1:25 000–1:100 000 och strandförskjutningsmodell (båda CC BY 4.0) och Samnordisk "
               "runtextdatabas (ODbL)."),
    False: bild(KARTA, "The Mälaren valley: clay and silt, the water around 1050 and the runestones",
                "The Mälaren valley from Västerås to the Baltic. Yellow is clay and silt, light is other soils or rock, blue "
                "is water around 1050 (land uplift has since turned many of Lake Mälaren's bays into land), and the red "
                "dots are runestones still standing where they were raised. Map: Vitki, after SGU's soil map 1:25,000–"
                "1:100,000 and shore displacement model (both CC BY 4.0) and the Scandinavian Runic-text Database (ODbL)."),
}


def chart(sv: bool) -> str:
    out = [":::chart " + ("Andel bygderutor med minst en runsten, efter hur mycket av marken som är lera och silt" if sv else
                          "Share of settled squares with at least one runestone, by how much of the land is clay and silt")]
    en = {"under 10 %": "under 10 %", "10–25 %": "10–25 %", "25–50 %": "25–50 %", "över 50 %": "over 50 %"}
    for grp, name_sv, name_en in (("malar", "Mälardalen (Uppland, Södermanland, Västmanland)",
                                   "The Mälaren valley (Uppland, Södermanland, Västmanland)"),
                                  ("gota", "Götalands inland (Västergötland, Smålands små land)",
                                   "Inland Götaland (Västergötland, Småland's small lands)")):
        out.append("# " + (name_sv if sv else name_en))
        for k in LBL:
            d = D[grp][k]
            lab = ("lera och silt " + k) if sv else ("clay and silt " + en[k])
            note = f"{d['k']} av {d['n']} rutor" if sv else f"{d['k']} of {d['n']:,} squares"
            out.append(f"{lab} | {pc(d)} | {note}")
    out.append(("Källa: Vitkis prov av Palms förklaring (låst plan 2026-11-08). Bygderutor om 2 × 2 km med minst ett gravfält "
                "och minst en fjärdedel land år 1050; runstenar som står kvar på sin plats. Procent. Diagram: Vitki, efter "
                "SGU (CC BY 4.0), Kulturmiljöregistret och Rundata (ODbL).") if sv else
               ("Source: Vitki's test of Palm's explanation (locked plan 8 November 2026). Settled squares of 2 × 2 km with at "
                "least one grave field and at least a quarter land in 1050; runestones still in place. Percent. Chart: "
                "Vitki, after SGU (CC BY 4.0), the Swedish cultural heritage register and Rundata (ODbL)."))
    return "\n".join(out) + "\n:::"


f1 = lambda x, n=1: f"{x:.{n}f}".replace(".", ",")  # noqa: E731
GH = "https://github.com/Precatio/runes/blob/main"
SLUG = "runstenarna-foljde-leran"
title = "Runstenarna följde leran – men jorden förklarar bara halva Mälardalen"
title_en = "The runestones followed the clay – but the soil explains only half of the Mälaren valley"
summary = ("Rune Palm skrev 1992 att runstenarna står vid de bästa jordarna, men att jorden inte kan förklara hela "
           "skillnaden mellan Mälardalen och resten av Norden. Vi lade SGU:s jordartskarta över varje runsten som står kvar på "
           "sin plats. Han hade rätt i båda leden – och stenarna står dessutom nära vattenvägarna.")
summary_en = ("Rune Palm wrote in 1992 that the runestones stand by the best soils, but that the soil cannot explain the whole "
              "difference between the Mälaren valley and the rest of the North. We laid the Swedish soil map over every "
              "runestone still in its place. He was right on both counts – and the stones also stand near the waterways.")

body = f"""Den som kör genom Uppland ser det utan karta. Runstenarna står där landskapet öppnar sig: vid åkrarna på lerslätten, vid vägen över ån, där gårdarna har legat i tusen år. I skogen mellan bygderna står de nästan aldrig. Det ser självklart ut. Men det betyder inte att det är förklaringen till varför Mälardalen har så många runstenar och resten av Norden så få – Sverige har {TOT:,} vikingatida runstenar i Samnordisk runtextdatabas, Norge {NO['norge']}.

Runologen Rune Palm gav ett svar i sin avhandling *Runor och regionalitet* 1992. Det är två påståenden i samma resonemang, och de drar åt olika håll:

> {Q['s255a'][0]}.

> {Q['s255b'][0]} […]

Jorden förklarar en del, alltså, men inte allt. Resten söker Palm i ekonomin: Mälardalen var enligt arkeologen Åke Hyenstrand, som han citerar, ”{Q['s259'][0]}”. Där hade fler råd att resa sten – ”{Q['s255c'][0]}”, skriver Palm.

Det fanns en sak han inte kunde göra 1992. Han räknade runstenar per tusen hektar och landskap, och skrev själv om svagheten: ”{Q['s107'][0]}”. I dag finns Sveriges geologiska undersöknings jordartskarta öppen, ytbit för ytbit. Så vi gjorde det han inte kunde: lade kartan över varje runsten och frågade om stenarna verkligen följer jorden – och hur mycket av Mälardalen jorden förklarar.

## Så mätte vi

Vi delade det vikingatida Sverige i rutor om två gånger två kilometer och behöll de rutor där människor bevisligen bodde under järnåldern: rutor med minst ett registrerat gravfält i Riksantikvarieämbetets kulturmiljöregister, och minst en fjärdedel land på den tiden. Landhöjningen är viktig här – mycket av det som i dag är åker kring Mälaren låg under vatten år 1050, och den marken räknas inte. Det gav {R['cells']:,} bygderutor med {R['gravefields']:,} gravfält och {R['stones']} runstenar.

I varje ruta mätte vi hur stor del av marken som är lera och silt – de fina sedimenten som Mälardalens lerslätter består av – enligt SGU:s karta. Och vi räknade bara runstenar som står kvar där de restes: en sten som flyttats till en kyrka eller ett museum säger inget om jorden den en gång stod på. Det är {N_KVAR} av de {TOT:,}, och det är provets största svaghet; vi återkommer till den.

Sedan jämförde vi rutor inom samma vikingatida land – Attundaland med Attundaland, Västergötland med Västergötland – och med lika många gravfält. Gravfälten är vårt mått på var folk bodde. Frågan blir då inte om runstenarna står där människor fanns, utan om de står på den bästa jorden *bland* de platser där människor fanns. Allt detta bestämde vi och låste i en analysplan innan något räknades.

{IMG[True]}

## Stenarna följer leran

De gör det. Inom samma land och vid lika många gravfält står det fler runstenar där marken är lera och silt. Går man från en ruta där {round(100*q25)} procent av marken är lera till en där {round(100*q75)} procent är det – från en vanlig skogsbygd till en vanlig slättbygd – blir det {f1(R['ratio_q75_vs_q25'], 2)} gånger så många runstenar. Ett så tydligt samband skulle slumpen ge ungefär en gång på {ONE_IN_P1:,.0f}.

Det håller hur vi än vänder på det: med rutor om en och fem kilometer i stället för två, i Mälardalen för sig och i Götalands inland för sig, och med eller utan vattnet i räkningen. Diagrammet visar det enklaste måttet – hur stor andel av bygderutorna som har minst en runsten:

{chart(True)}

## Men jorden räcker inte

Diagrammet visar också det andra. Mälardalens rutor ligger högre än Götalands på varje nivå: också där marken är lika lerig står det fler stenar i Uppland och Södermanland än i Västergötland och Småland.

Räknat i hela modellen har Mälardalens bygder {f1(P2['unadjusted']['ratio'])} gånger så många runstenar per kvadratkilometer som Götalands inland. Tar vi hänsyn till jorden, gravfälten och vattnet återstår {f1(P2['adjusted']['ratio'])} gånger. Jorden och bygden förklarar alltså ungefär hälften av skillnaden – och den andra hälften står kvar. Det är precis vad Palm skrev: jorden kan inte vara hela förklaringen.

## Nära vattnet

Den andra halvan pekade Palm, efter Hyenstrand, mot sjöfarten. Också det syns. Vid samma jord, i samma land och med lika många gravfält står det färre runstenar ju längre det är till vattnet som det låg år 1050: dubbelt så långt till stranden ger ungefär {round(100*(1-DOUBLE))} procent färre stenar. Ett sådant samband skulle slumpen ge ungefär en gång på {ONE_IN_P3:,.0f}.

## Vad det betyder

Vi visar var stenarna står. Varför de står där är en tolkning, och vi gör den med Palm: en runsten var ett uttalande av den som ägde jorden, om arv, släkt och rätt till marken. Den bästa jorden hade de som hade råd att låta resa sten. Men i Mälardalen var de fler än jorden ensam räcker till för att förklara. Där fanns också vattenvägarna, handeln och de yrkesristare som levde av att hugga stenar åt dem som beställde – eliten var, med Palms ord, bredare.

Det gör också Norges få runstenar lättare att förstå. Där är den bästa jorden smala dalgångar och kustremsor. Men jorden förklarar bara en del också där, och resten är samma fråga som i Götaland: vilka fler var det som hade både råd och anledning att resa sten i Mälardalen?

## Det som är osäkert

- **Bara stenar som står kvar.** {N_KVAR} av {TOT:,} runstenar står där de restes. Gotland och stora delar av Småland, där nästan alla stenar flyttats till kyrkor, faller i praktiken bort. Om de flyttade stenarna ursprungligen stod på annan jord än de som står kvar kan det ändra bilden.
- **Gravfälten är från hela järnåldern**, inte bara vikingatiden, och inventeringen är ojämn mellan landskapen.
- **Lera i rutan är inte gårdens jord.** På vikingatiden brukades ofta de lättare jordarna i lerslätternas kanter. Måttet säger att stenarna står där det finns lera i närheten, inte vilken jord gården odlade.
- **Jordartskartan är dagens**, och dess kvalitet varierar mellan områden enligt SGU själv.

:::box Det viktigaste i korthet
- Runstenarna står vid den bästa jorden också inom bygden: där marken är lera och silt står det fler stenar än på skogsmarken intill, i Mälardalen och i Götaland.
- Jorden och bygden förklarar ungefär hälften av varför Mälardalen har så många fler runstenar än Götaland. Den andra hälften står kvar, som Rune Palm skrev 1992.
- Stenarna står också nära vattenvägarna som de låg för tusen år sedan – ett tecken på att handel och sjöfart var en del av förklaringen.
- Vi visar var stenarna står; att det var den jordägande klassen som reste dem är Palms tolkning, och vi delar den.
:::

## Källor

- Palm, R. 1992. *Runor och regionalitet. Studier av variation i de nordiska minnesinskrifterna*. Uppsala: Institutionen för nordiska språk (Runrön 7). Citaten från s. 107 och 255; Hyenstrand 1989 (s. 19) citerad på s. 259.
- Sveriges geologiska undersökning. *Jordarter 1:25 000–1:100 000* (INSPIRE-version) och *Strandförskjutningsmodell*. CC BY 4.0.
- Riksantikvarieämbetet. *Kulturmiljöregistret* (gravfält). Institutet för språk och folkminnen, ortnamnsregistret (socknar och landskap), CC BY.
- Samnordisk runtextdatabas (Rundata), Uppsala universitet, ODbL.
- Vitki 2026. Analysplan: följer runstenarna de bästa jordarna? Låst 2026-11-08. [analysplaner/2026-11-08-palm-jordarna.md]({GH}/analysplaner/2026-11-08-palm-jordarna.md)
- Vitki 2026. Resultat. [utdata/palm_jordarna/resultat.md]({GH}/utdata/palm_jordarna/resultat.md)"""

body_en = f"""Anyone driving through Uppland sees it without a map. The runestones stand where the landscape opens up: by the fields on the clay plain, by the road across the river, where the farms have lain for a thousand years. In the forest between the settled districts they almost never stand. It looks obvious. But that does not make it the reason why the Mälaren valley has so many runestones and the rest of the North so few – Sweden has {TOT:,} Viking-age runestones in the Scandinavian Runic-text Database, Norway {NO['norge']}.

The runologist Rune Palm gave an answer in his dissertation *Runor och regionalitet* in 1992. It is two claims in the same argument, and they pull in different directions (our translation):

> The runestones are a phenomenon tied to a land-owning class, and their main areas of distribution are close to the best soils.

> A possibly lower agricultural potential in the runestone areas of Denmark and Götaland than in those of Svealand cannot, however, be the whole explanation of the great differences in number and density […]

The soil explains part, then, but not all. Palm looks for the rest in the economy: the Mälaren region was, according to the archaeologist Åke Hyenstrand, whom he quotes, "an expansive area in the east with developed handling of raw materials and seafaring". There, more people could afford to raise a stone – “the elite has, so to speak, been broader”, Palm writes.

There was one thing he could not do in 1992. He counted runestones per thousand hectares and province, and himself named the weakness: "The factor that perhaps matters most is that no account has been taken of the differences in the areas' types of land, e.g. arable land and forest." Today the Geological Survey of Sweden's soil map is open, patch by patch. So we did what he could not: laid the map over every runestone and asked whether the stones really follow the soil – and how much of the Mälaren valley the soil explains.

## How we measured

We divided Viking-age Sweden into squares of two by two kilometres and kept the squares where people demonstrably lived in the Iron Age: squares with at least one registered grave field in the Swedish National Heritage Board's register, and at least a quarter land at the time. Land uplift matters here – much of what is field around Lake Mälaren today lay under water in 1050, and that land is not counted. This gave {R['cells']:,} settled squares with {R['gravefields']:,} grave fields and {R['stones']} runestones.

In each square we measured how much of the land is clay and silt – the fine sediments the clay plains of the Mälaren valley are made of – according to the SGU map. And we counted only runestones still standing where they were raised: a stone moved to a church or a museum says nothing about the soil it once stood on. That is {N_KVAR} of the {TOT:,}, and it is the test's greatest weakness; we return to it.

Then we compared squares within the same Viking-age land – Attundaland with Attundaland, Västergötland with Västergötland – and with as many grave fields. The grave fields are our measure of where people lived. The question is then not whether the runestones stand where people were, but whether they stand on the best soil *among* the places where people were. We decided all of this and locked it in an analysis plan before anything was counted.

{IMG[False]}

## The stones follow the clay

They do. Within the same land and with as many grave fields, more runestones stand where the land is clay and silt. Going from a square where {round(100*q25)} percent of the land is clay to one where {round(100*q75)} percent is – from an ordinary forest district to an ordinary plain – gives {R['ratio_q75_vs_q25']:.2f} times as many runestones. A connection this clear would arise by chance about once in {ONE_IN_P1:,.0f}.

It holds whichever way we turn it: with squares of one and five kilometres instead of two, in the Mälaren valley on its own and in inland Götaland on its own, and with or without the water in the count. The chart shows the simplest measure – how many of the settled squares have at least one runestone:

{chart(False)}

## But the soil is not enough

The chart also shows the other thing. The Mälaren valley's squares lie higher than Götaland's at every level: even where the land is just as clayey, more stones stand in Uppland and Södermanland than in Västergötland and Småland.

Counted in the full model, the Mälaren valley's settled districts have {P2['unadjusted']['ratio']:.1f} times as many runestones per square kilometre as inland Götaland. Taking the soil, the grave fields and the water into account, {P2['adjusted']['ratio']:.1f} times remain. The soil and the settlement thus explain roughly half of the difference – and the other half remains. That is exactly what Palm wrote: the soil cannot be the whole explanation.

## Near the water

Palm, after Hyenstrand, pointed the other half towards seafaring. That shows too. With the same soil, in the same land and with as many grave fields, fewer runestones stand the farther it is to the water as it lay in 1050: twice as far to the shore gives about {round(100*(1-DOUBLE))} percent fewer stones. A connection like that would arise by chance about once in {ONE_IN_P3:,.0f}.

## What it means

We show where the stones stand. Why they stand there is an interpretation, and we make it with Palm: a runestone was a statement by whoever owned the land, about inheritance, kin and the right to the land. The best soil belonged to those who could afford to have a stone raised. But in the Mälaren valley they were more than the soil alone can explain. There were also the waterways, the trade and the professional carvers who lived by carving stones for those who commissioned them – the elite was, in Palm's words, broader.

It also makes Norway's few runestones easier to understand. There the best soil is narrow valleys and coastal strips. But the soil explains only part there too, and the rest is the same question as in Götaland: who were the many more who had both the means and a reason to raise a stone in the Mälaren valley?

## What is uncertain

- **Only stones still in place.** {N_KVAR} of {TOT:,} runestones stand where they were raised. Gotland and much of Småland, where almost all stones were moved to churches, practically drop out. If the moved stones originally stood on different soil from those still standing, the picture could change.
- **The grave fields are from the whole Iron Age**, not only the Viking Age, and the survey is uneven between provinces.
- **Clay in the square is not the farm's soil.** In the Viking Age the lighter soils at the edges of the clay plains were often the ones farmed. The measure says that the stones stand where there is clay nearby, not which soil the farm worked.
- **The soil map is today's**, and its quality varies between areas, according to SGU itself.

:::box The essentials in brief
- The runestones stand by the best soil even within the settled districts: where the land is clay and silt, more stones stand than on the forest land next to it, in the Mälaren valley and in Götaland.
- The soil and the settlement explain roughly half of why the Mälaren valley has so many more runestones than Götaland. The other half remains, as Rune Palm wrote in 1992.
- The stones also stand near the waterways as they lay a thousand years ago – a sign that trade and seafaring were part of the explanation.
- We show where the stones stand; that it was the land-owning class that raised them is Palm's interpretation, and we share it.
:::

## Sources

- Palm, R. 1992. *Runor och regionalitet. Studier av variation i de nordiska minnesinskrifterna*. Uppsala: Department of Scandinavian Languages (Runrön 7). Quotations from pp. 107 and 255 (our translations); Hyenstrand 1989 (p. 19) quoted on p. 259.
- Geological Survey of Sweden (SGU). *Jordarter 1:25 000–1:100 000* (INSPIRE version) and *Strandförskjutningsmodell*. CC BY 4.0.
- Swedish National Heritage Board. *Kulturmiljöregistret* (grave fields). Institute for Language and Folklore, place-name register (parishes and provinces), CC BY.
- Scandinavian Runic-text Database (Rundata), Uppsala University, ODbL.
- Vitki 2026. Analysis plan: do the runestones follow the best soils? Locked 8 November 2026 (in Swedish). [analysplaner/2026-11-08-palm-jordarna.md]({GH}/analysplaner/2026-11-08-palm-jordarna.md)
- Vitki 2026. Results (in Swedish). [utdata/palm_jordarna/resultat.md]({GH}/utdata/palm_jordarna/resultat.md)"""

body = re.sub(r"(\d),(\d{3})\b", r"\1 \2", body)  # Swedish thousands: 6 190, not 6,190 (decimals keep their comma)
assert "6 190" in body and "4 700" in body and "2 321" in body and "1,45" in body
for lang, b in (("sv", body), ("en", body_en)):
    assert not re.search(r"^\|", b, re.M), "BlogBody visar inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M))
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index(":::box") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 1 and re.match(r"/api/blog/figures/[0-9a-f]{16}\.png$", imgs[0])
    assert "Karta: Vitki" in b or "Map: Vitki" in b
labels = ["Forskning", "Geografi"]
assert blog_labels.check(labels) is None
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
path = os.path.join(ROOT, "utdata", "blogg", "palm_jordar.json")
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
                 "topic": "Forskning|palm-jordar", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
