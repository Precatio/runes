"""Så gör du-artikeln om Forskningsluckor: var uppgifter saknas, vad appen föreslår och hur raderna ska läsas.
Skärmbilder ur howto_luckor_bilder.py (utdata/blogg/howto_luckor/). Siffrorna hämtas ur den lokala analysmotorn när
artikeln byggs och låses med asserts (bara de som inte beror på R-körningens läge).
    ../../../.venv/bin/python build_howto_luckor.py [--write | --update DOC]"""
import datetime as dt
import io
import json
import os
import sys

import requests
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures  # noqa: E402

BILDER = os.path.join(ROOT, "utdata", "blogg", "howto_luckor")
API = os.environ.get("RUNFORSKNING_API", "http://localhost:8000")
g = requests.post(f"{API}/api/research/gaps", json={"measured_signa": []}, timeout=600).json()
T = g["coverage"]["totals"]
assert T["total"] == 2321 and T["carver"] == 771 and T["style"] == 1038
H = g["hypotheses"]
EV = H["evaluation"]
assert EV["n_carvers"] == 27 and 0.55 <= EV["top1_accuracy"] <= 0.65
NEW, RECON = len(H["new"]), len(H["reconsider"])
assert NEW == 44 and RECON == 17
PRIO = g["measurement_priorities"]
assert PRIO[0]["carver"] == "Öpir 1" and PRIO[0]["inscriptions"] == 95
UNINT, USTYLE = g["open_questions"]["uninterpreted"]["count"], g["open_questions"]["uncertain_style"]["count"]
assert UNINT == 465 and USTYLE == 719
tg = requests.get(f"{API}/api/research/gaps/textmodel", timeout=120).json()
assert tg["available"] and tg["counts"]["candidates"] == 27 and tg["counts"]["stones"] == 21 and tg["counts"]["open"] == 175  # textmodel-19
f = requests.post(f"{API}/api/research/findings", json={}, timeout=600).json()
ORT = f["summary"]["by_method"]["ortografi"]
assert ORT["stämmer"] == 182 and ORT["nytt"] == 53 and ORT["motsäger"] == 15
pr = lambda x: round(100 * x)  # noqa: E731
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


title = "Så gör du: hitta forskningsluckorna"
summary = ("Sidan Forskningsluckor svarar på tio frågor om var kunskapen saknas och vad Vitkis analyser föreslår. "
           "Här går vi igenom korten ett i taget – och hur man läser en rad utan att läsa in för mycket.")

body = f"""Den tredje *Så gör du*-artikeln handlar om sidan **Forskningsluckor**, den sida där Vitki försöker vara mest användbar för en runolog: inte genom att svara, utan genom att peka ut var ett svar skulle göra störst nytta. Sidan är byggd som frågekort. Varje kort är en fråga, och under det står ett svar, ett tolkningsförslag och vad svaret *inte* säger.

## Steg 1. Välj en fråga

Överst ligger korten. Klicka på ett så öppnas dess tabell under. Siffran på kortet är en snabbsiffra: hur många stenar eller fynd frågan gäller just nu.

{bild("02_fragekort.png", "Frågekorten på sidan Forskningsluckor", "Frågekorten. Det aktiva kortet är markerat; tabellen under byter när du klickar.")}

Raden ovanför korten säger vilket underlag siffrorna bygger på: Rundata-utgåvan, när statistiken i R beräknades och vilken version av sannolikhetsmodellen som inventerat luckorna. Täckning, hypoteser och prioriteringar räknas om vid varje anrop; R-resultaten och luckinventeringen är beräknade i förväg.

## Steg 2. Var saknas uppgifter?

Kortet **Luckor** visar täckningen landskap för landskap. Av Sveriges {sv(T['total'])} vikingatida runstenar har {sv(T['carver'])} en ristare i Rundata ({pr(T['carver'] / T['total'])} procent), {sv(T['style'])} en säker stilgrupp, {T['dated']} ett årtal och {T['lost']} är försvunna. Varje siffra i tabellen är klickbar och leder till stenarna bakom den, med samma filter.

{bild("04_tackning.png", "Täckningstabellen per landskap", "Täckningen per landskap. Uppland och Södermanland är väl attribuerade (Axelson 1993); i Götaland saknar nästan alla stenar ristare i Rundata.")}

Det här kortet är också det viktigaste förbehållet för alla de andra: det Rundata saknar är inte nödvändigtvis okänt för forskningen. En attribuering kan stå i Sveriges runinskrifter utan att finnas i databasen.

## Steg 3. Vad säger appens analyser?

**Våra resultat** ställer appens metoder mot Rundata, som här får stå för den publicerade forskningen. Varje fynd har tre delar: *belägg* (hur stark metodens signal är), *nyhet* (säger den något Rundata saknar?) och *relevans*. Stavningsjämförelsen ger just nu {ORT['stämmer']} fynd som stämmer med Rundata, {ORT['nytt']} som säger något Rundata saknar och {ORT['motsäger']} som pekar på en annan ristare. När statistiken i R är beräknad tillkommer attribueringsmodellens, seriationens och de okända ristarnas fynd.

{bild("03_vara_resultat.png", "Fliken Våra resultat", "Våra resultat: appens fynd mot Rundata, med belägg, nyhet och relevans per rad. Klicka på en rad för hela resonemanget.")}

Bekräftelserna är inte tråkiga: att metoden ofta landar på samma ristare som forskningen är det som ger de nya förslagen vikt.

## Steg 4. Nya ristare och omprövningar

**Nya ristare** är stenar utan ristare i Rundata vars stavning liknar en känd ristares – {NEW} stycken just nu. **Ompröva** är det omvända: {RECON} attribuerade stenar där stavningen pekar på någon annan. Metodens träffsäkerhet står alltid bredvid: rätt ristare först i {pr(EV['top1_accuracy'])} procent av fallen bland {EV['n_carvers']} ristare, där slumpen ger {pr(EV['chance_top1'])}. Det är ett belägg, inte en attribuering; Syntes & attribuering väger det mot de andra.

{bild("05_nya_ristare.png", "Fliken Nya ristare", "Stenar utan ristare med tydlig stavningslikhet, med p-värde, precision för den föreslagna ristaren, bergart och språkdrag.")}

## Steg 5. Vad vore värt att mäta?

**3D-mätning** listar ristare med många inskrifter men få uppmätta stenar – {PRIO[0]['carver']} överst med {PRIO[0]['inscriptions']} inskrifter – och föreslår vilka stenar som vore värda att skanna, signerade först. Sedan mätkorpusen fylldes med Kitzler Åhfeldts 36 skanningar finns ett första underlag; målet är fem uppmätta stenar per ristare.

{bild("06_3d_matning.png", "Fliken 3D-mätning", "Ristare som skulle vinna mest på fler skanningar.")}

## Steg 6. Luckor i texten

Det nyaste kortet, **Luckor i texten**, kommer från sannolikhetsmodellen ({tg['model_version']}). Den har gått igenom {tg['counts']['gaps_inventoried']} luckor i runstenarnas texter; {tg['counts']['open']} av dem har Rundata lämnat oåterställda, och för {tg['counts']['candidates']} luckor på {tg['counts']['stones']} stenar fyller modellen i ett känt ord med minst 80 procent kalibrerad sannolikhet. Tabellen visar det huggna, ifyllnaden, ordet, sannolikheten och näst bästa ord; stenens signum leder till inskriftssidan där du kan ange vad som syns och låta modellen räkna om.

{bild("08_luckor_tabell.png", "Tabellen Luckor i texten", "Modellens kandidater i öppna luckor. Underlag att granska mot foto och skanning – inte fynd.")}

Två kort till finns för den som vill läsa och se: **Tolkning** ({UNINT} inskrifter med osäker normalisering) och **Stilgrupp** ({USTYLE} stenar med osäker stilgrupp).

## Hur man läser en rad

- Belägget är metodens signal, inte sanningen. Ett p-värde säger hur sällan likheten uppstår av en slump, inte att attribueringen är rätt.
- Nyhet mäts mot Rundata 3.1 (2018). Rutan Runor 2020 på stenens sida visar om nyare utgåvor redan säger något.
- Relevansen är en tumregel för att prioritera, inte en sannolikhet.
- Öppna raden: där står hela resonemanget, det som talar emot, och vad som skulle avgöra.

:::box Innan du går vidare
- Börja med Luckor: där kan en ny mätning eller läsning göra störst nytta.
- Läs Våra resultat som ett test av metoderna först, som förslag sedan.
- En rad i Luckor i texten är ett ord att pröva mot stenen, inte ett ord på stenen.
- Allt på sidan har sina förbehåll under varje kort – de är skrivna för att läsas.
:::

*Sidan beskrivs i Vitkis metoddokumentation, avsnitt 14 (Forskningsluckor) med 14b (resultaten mot forskningen) och 14d (tolkningen av fynden).*"""

out = {"slug": "sa-gor-du-forskningsluckor", "title": title, "summary": summary, "body": body,
       "title_en": "", "summary_en": "", "body_en": "", "labels": ["Så gör du", "Ristare", "Sannolikhetsmodellen"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "howto_luckor.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "howto_luckor.json"), len(body.split()), "ord")

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
                 "topic": "Så gör du|forskningsluckor", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
