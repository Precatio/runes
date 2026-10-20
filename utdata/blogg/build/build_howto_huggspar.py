"""Så gör du-artikeln: en huggspårsanalys i Vitki, steg för steg med skärmbilder ur appen (howto_huggspar_bilder.py →
utdata/blogg/howto/). Bilderna fryses i bloggens bildarkiv (src/blog_figures.freeze) och skalas till högst 1600 px bredd.
Siffrorna om metoden hämtas ur METHODS.md:s källor i koden (src/limitations.py, web/src/lib/mesh.ts) och låses här.
    ../../../.venv/bin/python build_howto_huggspar.py [--write | --update DOC]"""
import datetime as dt
import io
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, limitations  # noqa: E402

BILDER = os.path.join(ROOT, "utdata", "blogg", "howto")
MESH_TS = open(os.path.join(ROOT, "web", "src", "lib", "mesh.ts"), encoding="utf-8").read()
MIN_DESCRIBE = int(re.search(r"MIN_RUNES_DESCRIBE\s*=\s*(\d+)", MESH_TS).group(1))
MIN_COMPARE = int(re.search(r"MIN_RUNES_COMPARE\s*=\s*(\d+)", MESH_TS).group(1))
assert (MIN_DESCRIBE, MIN_COMPARE) == (limitations.MIN_RUNES_DESCRIBE, limitations.MIN_RUNES_COMPARE) == (10, 20)
PROTOKOLL = open(os.path.join(ROOT, "PROTOCOL.md"), encoding="utf-8").read()
assert "0,6 mm" in PROTOKOLL and "3 mm" in PROTOKOLL


def bild(fil: str, alt: str, text: str, max_w: int = 1600) -> str:
    """Skärmbilden fryst i bloggens arkiv, som markdown med bildtext."""
    path = os.path.join(BILDER, fil)
    assert os.path.exists(path), f"skärmbild saknas: {fil} (kör howto_huggspar_bilder.py)"
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    url = blog_figures.freeze(out.getvalue())
    return f"![{alt}]({url})\n{text}"


title = "Så gör du en huggspårsanalys i Vitki"
summary = ("Steg för steg: ladda upp en 3D-skanning, låt Vitki hitta och mäta runorna enligt protokollet, granska "
           "resultatet och spara det – och vad siffrorna kan och inte kan säga om ristaren.")

body = f"""Det här är den första av våra *Så gör du*-artiklar: korta handledningar med skärmbilder, för dig som vill använda Vitki själv. Den här går igenom hur man mäter huggspåren i en 3D-skanning av en runsten. Allt sker i webbläsaren; mätningen görs av Vitkis analysmotor.

Vad som mäts är spårens form: V-vinkeln i botten, djupet, bredden och några mått till, i tvärsnitt över varje spår. Stenens resultat är medelvärdet över många runor. Varför det är intressant – och varför det inte räcker för att känna igen en ristare – kommer sist.

## Vad du behöver

- **En 3D-skanning** i STL-, OBJ- eller PLY-format. Egna skanningar går bra, och det finns fritt tillgängliga: Laila Kitzler Åhfeldts skanningar av Södermanlands runstenar ligger öppet på Zenodo med licensen CC BY, liksom skanningar från Medelpad och Hälsingland. Ange alltid skannern, institutionen och licensen när du använder dem.
- **Ett konto i Vitki** om du vill spara mätningen i ett projekt eller jämföra med andra stenar. Själva mätningen kräver ingen inloggning.
- **Lite tålamod** med stora filer: en skanning på hundra megabyte tar en stund att läsa in, och appen visar då en förenklad modell på skärmen medan mätningarna görs på originalet.

## Steg 1. Öppna 3D-huggspårsanalysen

I menyn till vänster, under *Analysera*, väljer du **3D-Huggspårsanalys**. Sidan har tre delar: inställningarna till vänster, 3D-vyn i mitten och resultaten nedanför.

{bild("01_sidan.png", "3D-huggspårsanalysens sida i Vitki innan någon fil är uppladdad", "Sidan innan en fil är uppladdad: inställningarna till vänster, den tomma 3D-vyn till höger.")}

## Steg 2. Ladda upp skanningen

Klicka på **Välj fil** under *Ladda upp 3D-mesh* och välj din skanning. Statusrutan visar vad som händer: filen laddas upp till analysmotorn, modellen läses in, och när den är klar står hur många ytor (trianglar) den har. Stenen dyker upp i 3D-vyn, där du kan vrida den med musen.

{bild("03_status_inlast.png", "Statusrutan när modellen är inläst", "Statusrutan när modellen är inläst. Nästa punkt säger vad som behövs för att mäta med det valda mätsättet.")}

## Steg 3. Välj mätsätt

När filen är inläst visas tre mätsätt:

- **Ett klick:** håll Shift och klicka mitt i ett spår – appen hittar riktningen och botten och mäter ett snitt där. Bra för att pröva enskilda runor.
- **Manuellt:** du sätter själv två punkter tvärs över spåret, eller flera längs det, och styr exakt var snittet tas.
- **Automatiskt:** appen hittar alla spår på den sida som vetter mot dig och mäter dem med jämna mellanrum. Det är det sätt som ger ett resultat för hela stenen, och det vi går igenom här.

{bild("04_matsatt.png", "Valet av mätsätt: Ett klick, Manuellt eller Automatiskt", "Mätsättet väljs med tre knappar. Texten under förklarar vad varje sätt gör.")}

Vrid stenen så att den ristade sidan vetter mot dig innan du startar den automatiska analysen. Appen mäter det den ser.

## Steg 4. Kör den automatiska analysen enligt protokollet

Välj **Automatiskt**. Panelen som öppnas har en kryssruta för **Vitki-protokollet**: fasta inställningar – 0,6 mm rutnät, normal känslighet och 3 mm mellan snitten – så att din sten kan jämföras med andra stenar som mätts på samma sätt. Låt den vara ikryssad om du inte har ett särskilt skäl. Den automatiska analysen mäter bara spår som känns igen som runor; ornamentik, slingkanter och sprickor hoppas över.

Klicka på **Kör automatisk analys**. Analysen tar från en halv minut till några minuter beroende på skanningens storlek.

{bild("05_automatisk_panel.png", "Panelen för automatisk analys med Vitki-protokollet ikryssat", "Panelen för den automatiska analysen. Protokollet är förvalt; inställningarna under är låsta tills du kryssar ur det.")}

*Facit-läget* i samma panel är för den som vill pröva runigenkänningen: då mäts alla spår, och du märker själv vilka som är runor. Det behövs inte för en vanlig mätning.

## Steg 5. Granska resultatet

När analysen är klar visas rutan **Granska den automatiska analysen**. Den säger hur många snitt som godkänts, hur många runor som känts igen och om protokollet följts. I 3D-vyn är varje mätt snitt en orange punkt; grå punkter är spår som var för breda för att vara huggspår, eller som inte känts igen som runor.

{bild("09_granska.png", "Granskningsrutan efter den automatiska analysen", "Granskningsrutan: antal godkända snitt, antal runor och om protokollet följdes. Här kan du också exportera alla snitt som CSV.")}

Titta igenom punkterna. Dra en ruta i 3D-vyn för att märka punkter som *Runa*, *Ornamentik* eller *Utesluten*, och klicka på en punkt för att se dess tvärsnittsprofil. Det är här du rättar det appen gjort fel: en korsarm som tagits för en runa, en spricka som mätts.

{bild("10_3d_vy.png", "3D-vyn med de mätta snitten som punkter", "Stenen i 3D-vyn med de mätta snitten. Orange är mätta spår, grått sådant som inte mäts.")}

När du är nöjd med granskningen klickar du på **Använd runorna som resultat**. Då räknas stenens mått fram ur de godkända snitten och visas under granskningen. (Knapparna bredvid använder ornamentiken, eller allt som inte uteslutits, för den som vill jämföra spårtyperna.)

Två riktvärden är bra att känna till. Appen vill ha minst {MIN_DESCRIBE} runor för att beskriva en sten och minst {MIN_COMPARE} för att jämföra den med andra: med tio runor är osäkerheten i stenens vinkel ungefär ±6°, med tjugo ±4°. Har analysen hittat färre säger granskningsrutan det.

## Steg 6. Läs måtten

Under granskningen står stenens mått: medelvärden med osäkerhetsintervall för V-vinkel, djup, bredd, djup/bredd och de övriga måtten, uppdelat på spårtyp. Vinkel, djup och bredd är de stabila måtten; bottenradie och asymmetri är osäkrare och ska läsas med försiktighet. Verktygsklassningen (pik- eller bredmejsel) är en tumregel och inte kalibrerad mot kända verktyg.

{bild("11b_resultat_allt.png", "Resultatpanelen med stenens mått, jämförelsen med mätkorpusen och exportknapparna", "Stenens mått som medelvärden med spridning (SD) och antal snitt, verktygsbedömningen överst (en tumregel), jämförelsen med mätkorpusen och knapparna för export och bidrag. Sö 128 är en sandstenshäll med grunda, breda spår: V-vinkeln 140° är trubbigare än hos de flesta stenar i Södermanlandsserien, och djupet under två millimeter hör till de minsta.")}

## Steg 7. Spara, rapportera, dela

{bild("12_stenrapport.png", "Kortet Stenrapport med knappen Skapa stenrapport", "Stenrapporten skapas med ett klick och öppnas under Rapporter.")}

- **Spara snitt i Projekt** (kräver inloggning) sparar mätningen med skanningens fingeravtryck, inställningarna och metodversionen, så att du kan återuppta arbetet och så att det går att se i efterhand hur mätningen gjordes.
- **Skapa stenrapport** ger ett artikelutkast om stenen med strykljus, djupkarta, snittpositioner, profiler och mått, räknat direkt ur skanningen.
- **Exportera snitt (CSV)** eller **Exportera allt (JSON)** ger dig rådata att räkna vidare på i R eller Excel.
- **Bidra till korpusen** lägger stenens mått i den delade mätkorpusen (CC BY 4.0), så att andra kan jämföra med den. Här är det viktigt att signum och spårtyp är rätt angivna.

## Steg 8. Tolka med måtta

Det här är den viktigaste delen av handledningen. Måtten beskriver hur spåren är huggna. De är stabila: mäts samma skanning om med andra inställningar ändras stenens medelvärden lite. Men de är **inte visade att skilja ristare åt**. När vi körde analysen på Kitzler Åhfeldts 36 skanningar från Södermanland återskapades inte hennes indelning i huggtekniska grupper, och när appens egen attribuering prövades på stenarna med känd ristare träffade den inte bättre än en gissning efter bergarten. Granit huggs annorlunda än sandsten, och en ristare högg oftast i traktens sten – så det som ser ut som en hand kan vara ett material.

Därför: använd måtten för att beskriva en sten, jämföra två stenar som mätts på samma sätt, och ställa frågor. Använd dem inte ensamma för att säga vem som ristade. Appen säger detsamma själv, i rutan *Kända brister* under varje analys och i varje rapport.

:::box Innan du går vidare
- Ristade sidan mot dig innan du startar, och Vitki-protokollet ikryssat.
- Minst {MIN_DESCRIBE} runor för att beskriva stenen, minst {MIN_COMPARE} för att jämföra den.
- Gå igenom punkterna i 3D-vyn och rätta det som inte är runor.
- Jämför bara stenar som mätts med samma inställningar, och helst på samma bergart.
- Skriv alltid vem som skannat stenen, och med vilken licens.
:::

## Mer att läsa

Metoden är beskriven i detalj i Vitkis metoddokumentation (avsnitt 2, *Huggspårsmått*) och protokollet i PROTOCOL.md, båda öppna i kodförrådet. Bristerna i metoden förs i en enda lista som följer med varje analys (version {limitations.VERSION}).

*Skanningen i bilderna är Sö 128 vid Lids kyrka i Södermanland, en sandstenshäll i stilgrupp Pr2, skannad av Laila Kitzler Åhfeldt (Riksantikvarieämbetet) och fritt tillgänglig på Zenodo under CC BY 4.0. Skanningens punktavstånd, 1,1 mm, är glesare än protokollets rekommenderade 0,5 mm, och appen säger det själv i granskningsrutan – ett bra exempel på en varning att ta på allvar.*"""

out = {"slug": "sa-gor-du-en-huggsparsanalys", "title": title, "summary": summary, "body": body,
       "title_en": "", "summary_en": "", "body_en": "", "labels": ["Så gör du", "Huggspår och 3D"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "howto_huggspar.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "howto_huggspar.json"), len(body.split()), "ord")

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
                 "topic": "Så gör du|huggspår", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
