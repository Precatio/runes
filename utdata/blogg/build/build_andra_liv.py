"""Artikeln om runstenarnas andra liv (sv + en): broar, golv, spisar, kvarnstenar och brunnar, med enskilda citerade
exempel ur Sveriges runinskrifter (A1, tillägg 1, not 7: flyttningarna används bara beskrivande, med citerade exempel,
aldrig i en andel). Varje citat kontrolleras mot utgåvans text (artiklarna utanför repot,
/Volumes/2TB/Antigrvity/Runes/downloads/sri_artiklar/) och sidan räknas fram ur sidmarkörerna. Skärmbild av
fyndhistoriken på stensidan (utdata/blogg/build/skarmbild_sri.py).
    ../../../.venv/bin/python build_andra_liv.py [--write | --update DOC]"""
import datetime as dt
import glob
import io
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels, commons  # noqa: E402
from utdata.norge.citat import letters  # noqa: E402

ART = {}
for f in glob.glob("/Volumes/2TB/Antigrvity/Runes/downloads/sri_artiklar/*.jsonl"):
    if "forskjuten" in f:
        continue
    for ln in open(f, encoding="utf-8"):
        a = json.loads(ln)
        ART[a["signum"]] = a
RD = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}


def page(sig, frag):
    """The page (from the [[sida N]] markers) where the quote stands in SRI's article; None if it is not there."""
    parts = re.split(r"\[\[sida ([^\]]+)\]\]", ART[sig]["text"])
    segs = [(parts[i], parts[i + 1]) for i in range(1, len(parts), 2)]
    q = letters(frag)
    for k, (p, txt) in enumerate(segs):
        if q in letters(txt):
            return p
        if k + 1 < len(segs) and q in letters(txt + segs[k + 1][1]):
            return p
    return None


# (signum in whose SRI article the quote stands, quote as printed, expected page or None for a pdf page)
Q = {
    "gs10a": ("Gs 9", "tagit till att bruka till Ungshäll att grädda bröd på, eftersom ugnarne eij till räckte", None),
    "gs10b": ("Gs 9", "Då skiämdes hon, och sprack", None),
    "ol37a": ("Öl 37", "hafver fört honom af sitt forna rum, i en stenbro", "101"),
    "ol37b": ("Öl 37", "om dän lefde som förden i bron, borde han straffas till lifvet", "101"),
    "ol36": ("Öl 36", "Lågh till broo, restes opp 1634", "99"),
    "na8": ("Nä 8", "Denna häll ligger till en bro twert öfver Landswägen, ther hon legat öfver 150 åhr", None),
    "vg130a": ("Vg 130", "inlagd till golfhall i ladugården", "250"),
    "vg130b": ("Vg 130", "otur med kreatur", "250"),
    "vg116": ("Vg 116", "Uti torpet Koohagen står en runsten inmurad i dess spis eller ugn", None),
    "g70a": ("G 70", "at bepryda sin spis med", "98"),
    "g70b": ("G 70", "trampas dagligen", "98"),
    "u705a": ("U 705", "underliggaren till en handqvarn", "228"),
    "u705b": ("U 705", "som tydligen blivit tillverkad av en runsten", "228"),
    "u869": ("U 869", "Den skall ha legat som trappsten vid en gammal 1700-talsstuga", "536"),
    "ol47": ("Öl 47", "legat som broläggningssten vid brunnen, där boskapen vattnades", "119"),
    "sm21": ("Sm 21", "där den utgjort ett slags klappbrygga och bro, från vilken man hämtade vatten", "78"),
    "og200a": ("Ög 200", "efterspaningarne voro länge fåfänga", "190"),
    "og200b": ("Ög 200", "mörkare streck på en af ringmurens portstolpar", "190"),
}
for k, (sig, quote, want) in Q.items():
    got = page(sig, quote)
    assert got is not None, (k, sig, quote)
    assert want is None or got == want, (k, got, want)
Qt = {k: v[1] for k, v in Q.items()}
# Gs 10 (Alborga) is printed as entry [10] right after Gs 9; the quote stands in that entry
assert "Alborga by, Valbo sn" in re.sub(r"\s+", " ", ART["Gs 9"]["text"]) and RD["Gs 10"]["place"] == "Alborga by"
for s in ("Öl 37", "Öl 36", "Nä 8", "Vg 130", "Vg 116", "G 70", "U 705", "U 869", "Öl 47", "Sm 21", "Ög 200"):
    assert s in RD, s

# ---- pictures ---------------------------------------------------------------------------------------------------------
from PIL import Image  # noqa: E402

PANEL = {}
for lang in ("sv", "en"):
    im = Image.open(os.path.join(ROOT, "utdata", "blogg", "bilder", f"sri_Vg_130_{lang}.png")).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    PANEL[lang] = blog_figures.freeze(buf.getvalue())
IMGS = {x["signum"]: x for x in commons.stone_images(["Vg 130", "Öl 36", "Nä 8"])}
for s in ("Vg 130", "Öl 36", "Nä 8"):
    assert s in IMGS and re.match(r"(CC BY|CC0|Public domain)", IMGS[s]["licence"]), s
PIC = lambda s, lang: commons.markdown(IMGS[s], lang)  # noqa: E731
CAP = {"sv": ("Bild: Vitki, stensidan för Vg 130 under Inskrifter. Rutan visar vad *Sveriges runinskrifter* säger om stenens "
              "historia, med sidhänvisning och ett kort citat ur bandet."),
       "en": ("Image: Vitki, the stone page for Vg 130 under Inscriptions. The box shows what *Sveriges runinskrifter* says about "
              "the stone's history, with a page reference and a short quotation from the volume.")}
APP = lambda lang: f"![{'Fyndhistoriken för Vg 130' if lang == 'sv' else 'The find history of Vg 130'}]({PANEL[lang]})\n{CAP[lang]}"  # noqa: E731

SLUG = "bakhall-bro-och-kvarnsten-runstenarnas-andra-liv"
title = "Bakhäll, bro och kvarnsten – runstenarnas andra liv"
title_en = "Baking slab, bridge and millstone – the second lives of the runestones"
summary = ("En runsten blev bakhäll åt inkvarterade soldater, en annan låg i tvåhundra år som bro under landsvägen, en tredje "
           "höggs om till kvarnsten. Vi har läst *Sveriges runinskrifter* sten för sten och samlat vad stenarna blev efter "
           "vikingatiden – och vad som hände när någon ville ha dem tillbaka.")
summary_en = ("One runestone became a baking slab for billeted soldiers, another lay for two hundred years as a bridge under the "
              "highway, a third was cut down into a millstone. We have read *Sveriges runinskrifter* stone by stone and gathered "
              "what the stones became after the Viking Age – and what happened when someone wanted them back.")

body = f"""Den 22 juli 1726 kom Olof Celsius till Alborga by i Valbo socken i Gästrikland. Han letade efter en runsten och fick höra av en gammal man, Lars Hansson, vad som hade hänt med den. Stenen hade stått i en stenbacke mitt för kyrkvärdens gård, men finska soldater som var inkvarterade i byn hade

> {Qt['gs10a']}.

Hällen hade alltså fått bli bakhäll när ugnarna inte räckte. Sedan, berättade Lars Hansson, ”{Qt['gs10b']}” sönder när regnet föll på den, och 1726 fanns den inte längre (Gästriklands runinskrifter, Gs 10).

Runstenarna restes för att stå länge. Många av dem gjorde det inte. De blev broar, golv, trappsteg, spishällar och kvarnstenar, och vi vet det för att utgivarna av *Sveriges runinskrifter* noterade varje uppgift de kunde hitta om var en sten hade varit. Vitki har läst alla band sten för sten – över 2 500 stenartiklar – och lagt utgivarnas uppgifter om stenens öden på stensidan i appen.

{APP("sv")}

Det här är en samling av de stenar vi fastnade för. Hur vanligt det var att en runsten fick ett andra liv räknar vi inte här; det gör vi i studien om flyttade och försvunna stenar, som körs i januari.

## Under landsvägen

Den vanligaste andra användningen var kanske den mest praktiska: en flat, stor sten passar som bro över ett dike. På Öland noterade fornforskaren Johannes Rhezelius på 1630-talet flera stenar som hade legat i broar och som restes 1634. Om stenen i Bjärby står det kort: ”{Qt['ol36']}” (Ölands runinskrifter, Öl 36, s. 99).

{PIC("Öl 36", "sv")} Bjärbystenen, som låg i en bro och restes 1634.

Vid Lerkaka hade en bonde ”{Qt['ol37a']}”. Redan på Johan III:s tid hade en av rikets herrar av Bielkesläkten sett stenens vanära och sagt att om den som fört den till bron levde, ”{Qt['ol37b']}”. Stenen fördes tillbaka 1634 (Öl 37, s. 101).

I Närke låg Väsbystenen tvärs över landsvägen i Kräcklinge. När Celsius korrespondent J. G. Hallman rapporterade om den 1725 hette det: ”{Qt['na8']}” (Närkes runinskrifter, Nä 8). Den grävdes fram 1860, restes på sin gamla plats, vältes omkull av några okynniga personer 1867 och murades till sist in i kyrkogårdsmuren.

{PIC("Nä 8", "sv")} Väsbystenen som Herman Hofberg tecknade den 1868, efter att den grävts fram ur landsvägen.

## Golv, trösklar och trappor

I kyrkorna lades stenarna ofta i golvet eller som tröskel, och på gårdarna blev de trappsteg. Vid Skånum i Västergötland blev en runsten flyttad till säteriet Simonstorp och ”{Qt['vg130a']}”. Det gick inte bra. ”{Qt['vg130b'].capitalize()}”, står det i utgivarens källa, gjorde att stenen fördes tillbaka till sitt förra ställe, där den står än (Västergötlands runinskrifter, Vg 130, s. 250).

{PIC("Vg 130", "sv")}

På Gotland gick en sten den omvända vägen, från finrummet till farstun. Den hade suttit som förflis över en spis, där en bonde köpt den ”{Qt['g70a']}”, men låg 1901 som trappsten hos en smed i Eksta, där den ”{Qt['g70b']}” (Gotlands runinskrifter, G 70, s. 98–99). I dag finns den i Gotlands museum.

## Spisar och ugnar

Bakhällen i Alborga var inte ensam. I Västergötland antecknade prästen Elaus Benedicti 1672: ”{Qt['vg116']}” (Vg 116). Torpet är rivet, och stenen har inte gått att hitta.

## Kvarnstenar

Den mest genomgripande förvandlingen var att hugga om stenen. På O. Hermelins teckning av en sten från Öster-Dalby i Uppland står att runorna satt ”på undre sidan af {Qt['u705a']}”, och 1926 hittades ”en mindre kvarnsten av grå sandsten, {Qt['u705b']}” (Upplands runinskrifter, U 705, s. 228–229). En annan kvarnsten med runslingor hittades 1938 i Gryta socken: ”{Qt['u869']}” (U 869, s. 536).

## Vid brunnen

Några stenar låg där människor och djur hämtade vatten. En gavelsten till en gravkista från Köpings kyrkogård på Öland hade i många år ”{Qt['ol47']}” (Öl 47, s. 120), och i Småland hade en sten vid Mörrumsån varit ett slags klappbrygga ”{Qt['sm21'].split('klappbrygga')[1].strip()}” (Smålands runinskrifter, Sm 21, s. 78).

## Att hitta dem igen

En del stenar kom tillbaka för att någon letade. I Sya socken i Östergötland hade en kyrkoherde sett runor på en av stenarna som sprängdes till en ny ringmur, men ”{Qt['og200a']}”. Till sist, just vid solnedgången, såg man ”{Qt['og200b']}” (Östergötlands runinskrifter, Ög 200, s. 190).

## Vad det säger

Runstenarna var under hundratals år byggmaterial, och det säger något om hur de sågs. En flat sten var värd mer som bro eller spishäll än som minne, så länge ingen kunde läsa runorna. Men redan på 1500- och 1600-talen fanns det de som tyckte annorlunda – Bielkes vrede och Rhezelius resta stenar på Öland är några av de tidigaste exemplen på att runstenar skulle skyddas.

För oss betyder det också att en runsten sällan står där den restes. Det har vi skrivit om förut, och i januari mäter vi det i hela materialet.

## Svagheterna

- **Utgivarna återger ofta äldre källor,** som Rhezelius, Celsius och lokala berättare, och det är deras uppgifter som citeras.
- **Citaten är korta och ordagranna,** med stavningen i utgåvan. Vi har kontrollerat varje citat mot bandets text och sida.
- **Det här är exempel, inte en räkning.** Hur vanligt det var visar studien i januari.
- **Om metoden:** uppgifterna om stenarnas öden har plockats ut ur banden av Anthropics språkmodell Claude och granskats i stickprov; varje uppgift som används här har vi läst själva i originalet.

:::box Det viktigaste i korthet
- Efter vikingatiden blev många runstenar byggmaterial: broar under landsvägen, golv och trösklar i kyrkorna, trappsteg, spishällar och till och med kvarnstenar.
- En sten i Gästrikland blev bakhäll åt inkvarterade soldater och sprack; en i Västergötland fördes tillbaka från en ladugård efter otur med kreaturen.
- Redan på 1500- och 1600-talen ville en del att stenarna skulle skyddas, och på Öland restes stenar ur broarna 1634.
- Vitki har läst *Sveriges runinskrifter* sten för sten; uppgifterna finns på stensidorna i appen.
:::

## Källor

- *Sveriges runinskrifter* (Kungl. Vitterhets Historie och Antikvitets Akademien), banden: Ölands runinskrifter (SRI I), Östergötlands runinskrifter (II), Smålands runinskrifter (IV), Västergötlands runinskrifter (V), Upplands runinskrifter 3 (VIII), Gotlands runinskrifter 1 (XI), Närkes runinskrifter (XIV:1) och Gästriklands runinskrifter (XV:1). [Digitala Sveriges runinskrifter](https://www.raa.se/kulturarv/runor-och-runstenar/digitala-sveriges-runinskrifter/), Riksantikvarieämbetet. Korta citat med sida.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Om metoden och kontrollen: analysplan A1, tillägg 1, på [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2027-01-A1-tillagg-1-sri-fyndhistorik.md). Om var runstenarna står: [Vendeltid, vikingatid, medeltid – fanns gränserna?](/artiklar/vendeltid-vikingatid-medeltid-fanns-granserna)
- Foton och teckningar: Wikimedia Commons, med upphov och licens i bildtexterna."""

body_en = f"""On 22 July 1726 Olof Celsius came to Alborga in Valbo parish in Gästrikland. He was looking for a runestone, and an old man, Lars Hansson, told him what had become of it. The stone had stood on a stony knoll opposite the churchwarden's farm, but Finnish soldiers billeted in the village had

> {Qt['gs10a']}

– taken it to use as a baking slab, since the ovens were not enough. Then it was ruined and cracked when the rain fell on it, and by 1726 it was gone (Gästriklands runinskrifter, Gs 10).

Runestones were raised to stand for a long time. Many did not. They became bridges, floors, steps, hearth slabs and millstones, and we know it because the editors of *Sveriges runinskrifter*, the corpus edition of Sweden's runic inscriptions, noted every report they could find of where a stone had been. Vitki has read all the volumes stone by stone – more than 2,500 stone entries – and put the editors' records of each stone's fate on the stone's page in the app.

{APP("en")}

This is a collection of the stones that caught our eye. How common it was for a runestone to get a second life we do not count here; we do that in the study of moved and lost stones, which runs in January.

## Under the highway

The most common second use was perhaps the most practical: a large flat stone makes a good bridge over a ditch. On Öland the antiquarian Johannes Rhezelius recorded in the 1630s several stones that had lain in bridges and were raised in 1634. Of the stone at Bjärby it says briefly: “{Qt['ol36']}” – ‘lay as a bridge, raised up 1634’ (Ölands runinskrifter, Öl 36, p. 99).

{PIC("Öl 36", "en")} The Bjärby stone, which lay in a bridge and was raised in 1634.

At Lerkaka a farmer had moved the stone from its old place into a stone bridge. Already in the time of King John III, one of the lords of the realm, of the Bielke family, had seen the stone's dishonour and said that if the man who had put it in the bridge were alive, he ought to be punished with his life (“{Qt['ol37b']}”). The stone was taken back in 1634 (Öl 37, p. 101).

In Närke the Väsby stone lay across the highway at Kräcklinge. When Celsius's correspondent J. G. Hallman reported on it in 1725, the report read: “{Qt['na8']}” – ‘this slab lies as a bridge across the highway, where it has lain for more than 150 years’ (Närkes runinskrifter, Nä 8). It was dug out in 1860, raised at its old place, overturned by some mischievous people in 1867, and finally set into the churchyard wall.

{PIC("Nä 8", "en")} The Väsby stone as Herman Hofberg drew it in 1868, after it had been dug out of the highway.

## Floors, thresholds and steps

In the churches the stones were often laid in the floor or as thresholds, and on the farms they became steps. At Skånum in Västergötland a runestone was moved to the manor of Simonstorp and laid as a floor slab in the cow barn (“{Qt['vg130a']}”). It did not go well. “{Qt['vg130b'].capitalize()}” – bad luck with the cattle – says the editor's source, caused the stone to be taken back to its former place, where it still stands (Västergötlands runinskrifter, Vg 130, p. 250).

{PIC("Vg 130", "en")}

On Gotland a stone went the other way, from the best room to the porch. It had sat as a mantel slab over a hearth, bought by a farmer “{Qt['g70a']}” – to adorn his hearth – but in 1901 it lay as a doorstep at a smith's in Eksta, where it was “{Qt['g70b']}”, trodden daily (Gotlands runinskrifter, G 70, pp. 98–99). Today it is in the Gotland Museum.

## Hearths and ovens

The baking slab at Alborga was not alone. In Västergötland the priest Elaus Benedicti noted in 1672 that in the croft of Kohagen a runestone was built into its hearth or oven (“{Qt['vg116']}”, Vg 116). The croft is gone, and the stone has not been found.

## Millstones

The most thorough transformation was to cut the stone down. O. Hermelin's drawing of a stone from Öster-Dalby in Uppland notes that the runes sat on the underside of the lower stone of a hand quern (“{Qt['u705a']}”), and in 1926 a small millstone of grey sandstone was found that had clearly been made from a runestone (Upplands runinskrifter, U 705, pp. 228–229). Another millstone with rune bands was found in 1938 in Gryta parish; it is said to have lain as a step at an old eighteenth-century cottage (U 869, p. 536).

## By the well

Some stones lay where people and animals fetched water. An end slab of a grave cist from Köping churchyard on Öland had for many years lain as paving by the well where the cattle were watered (Öl 47, p. 120), and in Småland a stone by the river Mörrumsån had served as a kind of washing jetty and bridge from which water was fetched (Smålands runinskrifter, Sm 21, p. 78).

## Finding them again

Some stones came back because someone looked. In Sya parish in Östergötland a vicar had seen runes on one of the stones blasted for a new churchyard wall, but the searches “{Qt['og200a']}” – were long in vain. At last, just at sunset, someone saw darker lines on one of the wall's gateposts (Östergötlands runinskrifter, Ög 200, p. 190).

## What it says

For hundreds of years runestones were building material, and that says something about how they were seen. A flat stone was worth more as a bridge or a hearth slab than as a memorial, as long as nobody could read the runes. But as early as the sixteenth and seventeenth centuries there were those who thought otherwise – Bielke's anger and Rhezelius's raised stones on Öland are among the earliest examples of the idea that runestones should be protected.

For us it also means that a runestone seldom stands where it was raised. We have written about that before, and in January we measure it across the whole material.

## The weaknesses

- **The editors often relay older sources,** such as Rhezelius, Celsius and local informants, and it is their reports that are quoted.
- **The quotations are short and verbatim,** in the spelling of the edition. We have checked every quotation against the volume's text and page.
- **These are examples, not a count.** How common it was will be shown by the study in January.
- **On the method:** the records of the stones' fates were extracted from the volumes by Anthropic's language model Claude and audited in samples; every record used here we have read ourselves in the original.

:::box The essentials in brief
- After the Viking Age many runestones became building material: bridges under the highway, floors and thresholds in churches, steps, hearth slabs and even millstones.
- A stone in Gästrikland became a baking slab for billeted soldiers and cracked; one in Västergötland was taken back from a cow barn after bad luck with the cattle.
- As early as the sixteenth and seventeenth centuries some wanted the stones protected, and on Öland stones were raised out of bridges in 1634.
- Vitki has read *Sveriges runinskrifter* stone by stone; the records are on the stone pages in the app.
:::

## Sources

- *Sveriges runinskrifter* (Royal Swedish Academy of Letters, History and Antiquities), the volumes: Ölands runinskrifter (SRI I), Östergötlands runinskrifter (II), Smålands runinskrifter (IV), Västergötlands runinskrifter (V), Upplands runinskrifter 3 (VIII), Gotlands runinskrifter 1 (XI), Närkes runinskrifter (XIV:1) and Gästriklands runinskrifter (XV:1). [Digital Sveriges runinskrifter](https://www.raa.se/kulturarv/runor-och-runstenar/digitala-sveriges-runinskrifter/), Swedish National Heritage Board. Short quotations with page.
- Scandinavian Runic-text Database (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- On the method and the checks: analysis plan A1, addendum 1, on [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2027-01-A1-tillagg-1-sri-fyndhistorik.md). On where runestones stand: [Vendel Period, Viking Age, Middle Ages – were the boundaries real?](/en/artiklar/vendeltid-vikingatid-medeltid-fanns-granserna)
- Photos and drawings: Wikimedia Commons, with author and licence in the captions."""

# ---- checks ----------------------------------------------------------------------------------------------------------
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M))
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index(":::box") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 4 and all(re.match(r"https://(upload|thumb)\.wikimedia\.org/|/api/blog/figures/[0-9a-f]{16}\.png$", u) for u in imgs), imgs
labels = ["Forskning", "Geografi"]
err = blog_labels.check(labels)
assert err is None, err
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
path = os.path.join(ROOT, "utdata", "blogg", "andra_liv.json")
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
                 "topic": "Forskning|andra-liv", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
