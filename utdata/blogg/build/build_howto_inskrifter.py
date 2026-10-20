"""Så gör du-artikeln om Inskrifter: söka i Rundata, läsa en stens sida, Runor 2020 bredvid, ortografin och
sannolikhetsmodellens läsning med skannerns spår. Skärmbilder ur howto_inskrifter_bilder.py (utdata/blogg/howto_inskrifter/),
frysta i bloggens bildarkiv. Siffrorna om Sö 206 hämtas ur den lokala analysmotorn när artikeln byggs och låses med
asserts, så att texten inte kan säga något annat än modellen.
    ../../../.venv/bin/python build_howto_inskrifter.py [--write | --update DOC]"""
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
from api.rundata import store  # noqa: E402

BILDER = os.path.join(ROOT, "utdata", "blogg", "howto_inskrifter")
API = os.environ.get("RUNFORSKNING_API", "http://localhost:8000")
STONE = "Sö 206"
rec = store().get(STONE)
assert rec and rec["place"] == "Överselö kyrka" and rec["style"] == "Pr4" and rec["carver_raw"].startswith("Äsbjörn")
tm = requests.get(f"{API}/api/textmodel/{STONE.replace(' ', '%20')}", timeout=300).json()
assert tm["available"] and tm["version"].startswith("textmodel-") and len(tm["gaps"]) == 2
G0, G1 = tm["gaps"]
assert G0["carved"] == "ru?niR" and G0["n"] == 1 and G1["carved"] == "k???auk" and G1["n"] == 3
W0, W1 = G0["words"][0], G1["words"][0]
scan = requests.get(f"{API}/api/textmodel/scantraces/{STONE.replace(' ', '%20')}", timeout=300).json()
assert scan["available"]
VERSION = tm["version"]
pr = lambda x: round(100 * x)  # noqa: E731


def bild(fil: str, alt: str, text: str, max_w: int = 1600) -> str:
    path = os.path.join(BILDER, fil)
    assert os.path.exists(path), f"skärmbild saknas: {fil}"
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return f"![{alt}]({blog_figures.freeze(out.getvalue())})\n{text}"


title = "Så gör du: hitta en runsten och läs vad modellen ser i luckorna"
summary = ("Steg för steg i Vitkis inskriftssida: sök i Samnordisk runtextdatabas, läs stenens uppgifter, se vad Runor 2020 "
           "säger bredvid, jämför stavningen med ristarna – och låt sannolikhetsmodellen föreslå ord i de förlorade "
           "runorna, med skannerns spår som facit.")

body = f"""Det här är den andra *Så gör du*-artikeln. Den handlar om sidan **Inskrifter**, där hela Samnordisk runtextdatabas ligger inbyggd, och om vad Vitki lägger till ovanpå den: en jämförelse av stavningen, Runors nyare uppgifter och sannolikhetsmodellens läsning av luckorna. Vi går igenom det med en sten som har både förlorade runor och en 3D-skanning: {STONE} vid {rec['place']}.

## Steg 1. Sök

Under *Forskning i hela korpusen* väljer du **Inskrifter**. Sökrutan tar signum, plats, runtext, normalisering eller översättning; menyerna bredvid avgränsar till landskap, period, stilgrupp och ristare. Skriv till exempel *Lid* så kommer stenarna vid Lids kyrka.

{bild("02_sok_lid.png", "Sökrutan på sidan Inskrifter med sökordet Lid", "Sökrutan och filtren. Sökningen slår i alla textfält samtidigt.")}

{bild("03_traffar.png", "Träfflistan för sökningen Lid", "Träffarna visas som kort med signum, plats och inskriftens början. Klicka på ett kort för stenens sida.")}

Längst ner i listan kan hela urvalet exporteras som CSV eller Excel, med samma filter.

## Steg 2. Läs stenens uppgifter

Stenens sida börjar med det Rundata vet: plats, datering, stilgrupp, ristare, material, föremål, placering, runtyper, och sedan själva texten i tre skepnader: translittereringen, normaliseringen och den engelska översättningen. {STONE} har stilgrupp {rec['style']} och ristaren {rec['carver_raw']}.

{bild("05_uppgifter.png", "Stenens uppgifter ur Rundata", "Uppgifterna ur Rundata 3.1 (2018). Ristarnamnet är en länk till alla ristarens stenar.")}

Under texten står **Runor 2020**, Riksantikvarieämbetets nyare utgåva, bredvid: om stenen står på sin ursprungliga plats eller är flyttad, om den är bevarad, dess datering, anteckningar och läsningen om den ändrats sedan 2018. Vitki räknar fortfarande på Rundata, men visar Runor så att du ser var utgåvorna skiljer sig.

{bild("06_runor.png", "Rutan Runor 2020 på stenens sida", "Runor 2020 bredvid Rundata. Det som står här räknas inte in i appens analyser än.")}

## Steg 3. Jämför stavningen

**Ortografisk profil** räknar hur stenen stavar vanliga ord, sätter skiljetecken och använder bindrunor, och jämför med de ristare som har flest inskrifter. Egennamn räknas inte, så att en signatur inte avslöjar ristaren. Likheten anges med ett p-värde: hur sällan en så stor likhet uppstår av en slump.

{bild("07_ortografi.png", "Ortografisk profil på stenens sida", "Stenens stavning jämförd med ristarnas. Det är ett belägg bland flera i Syntes & attribuering, inte en attribuering i sig.")}

## Steg 4. Låt modellen läsa luckorna

Längre ner finns **Läsning och luckor**. Klicka på *Läs med sannolikhetsmodellen*. Modellen ({VERSION}) har lärt sig hur orden följer på varandra och hur ristarna stavar, av alla vikingatida inskrifter utom den aktuella stenen, och föreslår ord för de förlorade runorna med en kalibrerad sannolikhet: när den säger 95 procent har den haft rätt i 95 procent av de prövade fallen.

{bild("08_lasning.png", "Panelen Läsning och luckor efter läsningen", "Läsningen ord för ord. Varje lucka har ett förstaval och en lista med alternativ.")}

På {STONE} finns två luckor. I *{G0['carved']}* saknas en runa; modellen föreslår *{W0['word']}* med {pr(W0['p'])} procent. I *{G1['carved']}* saknas tre runor, och det bästa förslaget, *{W1['word']}*, får bara {pr(W1['p'])} procent – det är modellens sätt att säga att den inte vet. Så ska siffrorna läsas: ett lågt tal är ett ärligt svar, inte ett misslyckande.

## Steg 5. Ange vad som syns

Klicka på *Ange vad som syns* vid en lucka. Där väljer du för varje förlorad runa vilken del som fortfarande går att se på stenen, till exempel övre halvan av en stav, och modellen räknar om med bara de runor som passar. Finns en 3D-skanning av stenen i mätkorpusen, som för {STONE}, säger rutan **Vad skannern ser i luckan** vilka spår den automatiska analysen hittat i luckan och vilka runor de tillåter. Spåren är ett förslag: du avgör, och modellen räknar om när du bekräftat.

{bild("09_lucka_oppen.png", "En lucka öppnad med valen för vad som syns", "Luckan öppnad: välj vad som syns av varje förlorad runa och räkna om.")}

{bild("10_skannern.png", "Rutan Vad skannern ser i luckan", "Skannerns förslag för luckan. Blå = runor som spåret tillåter.")}

## Vad det inte är

Modellen läser språket, inte stenen. Den vet ingenting om det som syns på ytan förrän du eller skannern säger det, och den är prövad på luckor som utgivarna redan fyllt; öppna luckor kan vara svårare. Ett förslag i en lucka är underlag för en läsning, inte en läsning. Och hela sidan bygger på Rundata 3.1 (2018): nyare läsningar finns i Runor-rutan men räknas inte in.

:::box Innan du går vidare
- Sök på vad som helst i texten, inte bara signum.
- Läs Runor 2020-rutan: där står om stenen är flyttad och om läsningen ändrats.
- Ett lågt tal i en lucka betyder att modellen inte vet, och det är rätt svar.
- Ange vad som syns innan du litar på ett förslag; skannerns spår är ett förslag som du bekräftar.
:::

*Metoden beskrivs i Vitkis metoddokumentation, avsnitt 7 (ortografi), 8.1 (sannolikhetsmodellen) och 17 (Runor 2020). Modellens prov och resultat står i panelen under läsningen.*"""

out = {"slug": "sa-gor-du-inskrifter-och-luckor", "title": title, "summary": summary, "body": body,
       "title_en": "", "summary_en": "", "body_en": "", "labels": ["Så gör du", "Sannolikhetsmodellen", "Språk och stavning"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "howto_inskrifter.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "howto_inskrifter.json"), len(body.split()), "ord")

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
                 "topic": "Så gör du|inskrifter", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
