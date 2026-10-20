"""Så gör du-artikeln om Statistik i R: hur sidan är byggd, hur en modul läses, med Vem ristade?, Okända ristare och
Ordförrådet som exempel. Skärmbilder ur howto_statistik_bilder.py (utdata/blogg/howto_statistik/). Siffrorna hämtas ur
den senaste färdiga korpuskörningen och låses med asserts.
    ../../../.venv/bin/python build_howto_statistik.py [--write | --update DOC]"""
import datetime as dt
import glob
import io
import json
import os
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures  # noqa: E402

BILDER = os.path.join(ROOT, "utdata", "blogg", "howto_statistik")
runs = [(os.path.getmtime(p), os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, "data/cache/r/corpus/*/done.json"))
        if os.path.exists(os.path.join(os.path.dirname(p), "anonymous.json"))]
RUN = max(runs)[1]
A = json.load(open(os.path.join(RUN, "attribution.json")))
AN = json.load(open(os.path.join(RUN, "anonymous.json")))
W = json.load(open(os.path.join(RUN, "words.json")))
ab = {x["features"]: x for x in A["ablation"]}
assert set(ab) == {"Geografi", "Stil", "Språk och innehåll", "Bergart", "Alla"}
pr = lambda x: round(100 * x)  # noqa: E731
assert (pr(ab["Alla"]["accuracy"]), pr(ab["Alla"]["top3"]), pr(A["majority_baseline"])) == (73, 87, 19)
assert (pr(ab["Geografi"]["accuracy"]), pr(ab["Språk och innehåll"]["accuracy"]), pr(ab["Bergart"]["accuracy"])) == (44, 61, 19)
GC = {k: {x["features"]: x for x in v["ablation"]}["Alla"]["accuracy"] for k, v in A["grouped_cv"].items()}
assert pr(GC["Socken"]) == 69 and pr(GC["Härad"]) == 59
FAM = {x["family"]: x for x in A["material"]["per_family"]}
assert pr(FAM["granitoid"]["accuracy"]) == 74 and FAM["granitoid"]["n"] == 347 and pr(FAM["sandsten"]["accuracy"]) == 67
assert (len(AN["groups"]), AN["n_candidates"], AN["n_robust"]) == (16, 8, 5)
HO = AN["validation"]["heldout"]
assert (pr(HO["purity"]), pr(HO["purity_geography"])) == (85, 69) and HO["runs_above"] == 30
V = AN["validation"]
assert (pr(V["purity"]), pr(V["purity_geography"])) == (69, 43)
COV = AN["coverage"]["carvers_by_province"]
assert COV["U"] == 25 and COV["Sö"] == 8 and AN["coverage"]["n_carvers"] == 35
assert W["n_words_tested"] == 75 and W["n_stones"] == 1848 and len([r for r in W["region"] if r["holds"]]) == 14
sv = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731


def bild(fil: str, alt: str, text: str, max_w: int = 1600) -> str:
    path = os.path.join(BILDER, fil)
    assert os.path.exists(path), f"skärmbild saknas: {fil}"
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return f"![{alt}]({blog_figures.freeze(out.getvalue())})\n{text}"


title = "Så gör du: läs statistiken i R"
summary = ("Vitki räknar på hela korpusen i R: tolv analyser med en fråga, ett svar, en tolkning och ett förbehåll var. "
           "Så här är sidan byggd, så här läser du en modul – och så här ser du om en siffra faktiskt betyder något.")

body = f"""Den fjärde *Så gör du*-artikeln handlar om sidan **Statistik (R)**, där alla Sveriges vikingatida runstenar analyseras på en gång. Det är den sida som artiklarna på vitkirunor.se bygger på, och den sida där det är lättast att läsa in för mycket i en siffra. Vi går igenom hur den är uppbyggd och tar tre moduler som exempel.

## Steg 1. Översikten

Sidan öppnas med en översikt: ett kort per analys med frågan den svarar på, svaret i korthet och hur säkert det är. *Säkert* betyder att resultatet är prövat med korsvalidering eller permutationstest och stämmer med vad forskningen utgår från; *troligt* att det håller statistiskt men med reservationer; *osäkert* att det är ett mönster att pröva. Överst står när analysen beräknades och på hur många stenar.

{bild("01_oversikt.png", "Översikten på sidan Statistik (R)", "Översikten: en fråga per modul, svaret i korthet och säkerheten. Klicka på ett kort för modulen.")}

Varje modul har samma form: *vad vi ser* (påståendet, med signifikans och osäkerhet), *hypotes* (vad det kan betyda, märkt som hypotes) och *det här säger resultatet inte*. Läs alla tre. Den sista delen är skriven för att läsas.

## Steg 2. Vem ristade? – en modell och dess nollnivåer

Modulen **Vem ristade?** är en statistisk modell som lärt sig de kända ristarnas drag – plats, stilgrupp, språkdrag, formler, innehåll – och föreslår ristare för stenar som saknar. Det första du ska titta på är inte träffen utan vad den jämförs med. Modellen hittar rätt ristare först i {pr(ab['Alla']['accuracy'])} procent av fallen ({pr(ab['Alla']['top3'])} bland de tre främsta) när varje sten bedöms av modeller som inte sett den. Att alltid gissa den vanligaste ristaren ger {pr(A['majority_baseline'])} procent. Geografin ensam ger {pr(ab['Geografi']['accuracy'])}, språket och innehållet ensamt {pr(ab['Språk och innehåll']['accuracy'])}.

{bild("02_vem_ristade.png", "Modulen Vem ristade? med delmodellerna", "Vem ristade?: träffen för hela modellen och för varje slags belägg för sig, mot nollnivån.")}

Två kontroller till står under. *Fungerar modellen på platser den inte sett?* håller hela socknar respektive härader utanför träningen: träffen sjunker till {pr(GC['Socken'])} och {pr(GC['Härad'])} procent, så en del av träffen kommer från platsen, men inte allt. *Kommer träffen från bergarten?* är ny: ristare och bergart hänger ihop, så bergartsfamiljen ensam prövas som delmodell. Den träffar {pr(ab['Bergart']['accuracy'])} procent, lika mycket som att gissa den vanligaste, eftersom {FAM['granitoid']['n']} av träningsstenarna är granit. Hela modellen träffar {pr(FAM['granitoid']['accuracy'])} procent på granit och {pr(FAM['sandsten']['accuracy'])} på sandsten. Modellens träff kommer alltså inte från bergarten – till skillnad från huggspårsmåtten, där bergarten ensam träffar lika bra som måtten.

{bild("03_bergart.png", "Tabellen Kommer träffen från bergarten?", "Träffen per bergartsfamilj. Det är den här sortens kontroll som skiljer en modell som lärt sig ristaren från en som lärt sig trakten.")}

## Steg 3. Okända ristare – när en metod inte kan prövas där den används

**Okända ristare** söker grupper av stenar utan ristare som liknar varandra i handens drag – stavning, formler, stil, runpar – lika mycket som en ristares stenar. Just nu finns {len(AN['groups'])} grupper, varav {AN['n_candidates']} inte liknar någon känd ristare och {AN['n_robust']} av dem håller även när de drag som följer tiden tas bort.

Läs rutorna i ordning. Prövad på kända ristare, som om de vore okända, blev en grupp i genomsnitt {pr(V['purity'])} procent samma ristare mot {pr(V['purity_geography'])} för lika många närliggande stenar. Men gränsvärdena justerades efter den kontrollen, så den överskattar; det strängare provet, där gränsen tas fram på andra ristare än de som prövas, ger {pr(HO['purity'])} mot {pr(HO['purity_geography'])} procent – till gruppernas fördel i {HO['runs_above']} av {HO['runs']} upprepningar.

{bild("04_okanda.png", "Modulen Okända ristare", "Okända ristare: sammanfattningsrutorna, täckningsvarningen och gruppernas tabell.")}

Och så den gula rutan. Av de {AN['coverage']['n_carvers']} kända ristarna med minst tre stenar finns {COV['U']} i Uppland och {COV['Sö']} i Södermanland, men kandidatgrupperna ligger i Östergötland, Småland, Västergötland och Medelpad, där nästan inga stenar har en ristare i Rundata. Metoden är alltså prövad där ristare är kända, inte där den används. Det står i appen för att det ska stå i varje artikel som bygger på den.

{bild("05_tackningsvarning.png", "Täckningsvarningen i modulen Okända ristare", "Täckningsvarningen. En metod som bara kan prövas i Mälardalen säger mindre om Västergötland än tabellen ser ut att göra.")}

## Steg 4. Ordförrådet – när ett ord håller

**Ordförrådet** prövar de {W['n_words_tested']} vanligaste orden på {sv(W['n_stones'])} runstenar: är ordet vanligare i ett landskap än i resten av landet när tiden och textlängden räknats bort, och ändras det över tid? Ristaren räknas som slumpeffekt, så att en flitig ristares vana inte blir landskapets. Bara {len([r for r in W['region'] if r['holds']])} regionala signaler överlever alla kontroller – och det är de som finns i artikeln *Västgöten reste själv – upplänningen lät resa*.

{bild("07_ordforradet.png", "Modulen Ordförrådet", "Ordförrådet: orden som håller per landskap, med observerade andelar och justerade p-värden.")}

## Så läser du en siffra på sidan

- **Mot vad?** Varje träff står bredvid en nollnivå: slump, majoritetsgissning, närliggande stenar, bergart. Skillnaden mot nollnivån är resultatet, inte träffen.
- **Prövad var?** Korsvaliderad betyder att stenen bedömts av en modell som inte sett den. Grupperad korsvalidering betyder att inte heller stenens socken setts. Hållet-utanför betyder att inte heller gränsvärdena justerats på den.
- **Justerat p** tar hänsyn till att många ord eller mönster prövats samtidigt. Ett ojusterat p under 0,05 bland 75 ord är väntat.
- **Materialet** är Rundata 3.1 (2018), svenska vikingatida runstenar, inte andra föremål. Siffrorna gäller inom det.

:::box Innan du går vidare
- Läs rutan "Det här säger resultatet inte" före tabellen.
- Jämför alltid med nollnivån bredvid, inte med 100 procent.
- En grupp eller en hypotes på sidan är ett förslag till en runolog, inte ett resultat.
- Datum och fingeravtryck överst säger vilken beräkning du tittar på; artiklarna låser sina siffror mot en bestämd körning.
:::

*Metoderna beskrivs i Vitkis metoddokumentation, avsnitt 1 (Statistik i R), med 1g (okända ristare), 1i (korsvalidering och bergart), 1l (begränsningar) och 1m (ordförrådet). All kod ligger i kodförrådets katalog r/.*"""

out = {"slug": "sa-gor-du-statistiken-i-r", "title": title, "summary": summary, "body": body,
       "title_en": "", "summary_en": "", "body_en": "", "labels": ["Så gör du", "Ristare", "Språk och stavning"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "howto_statistik.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "howto_statistik.json"), len(body.split()), "ord")

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
                 "topic": "Så gör du|statistik i R", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
