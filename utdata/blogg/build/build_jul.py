"""Julartikeln "Vikingarnas jul fanns i sagorna – men inte på en enda runsten" (sv + en), till julafton 2026
(Viktor 2026-11-13: "låter bra med julartikeln, skriv den så!"). Beskrivande, inga prov.

Underlag:
- Heimskringla i Linder & Haggsons utgåva 1869–72 (public domain, via heimskringla.no), utdata/varlden/korpus/heimskringla:
  varje ord som börjar på jól-, i sitt sammanhang. Träffar inom 350 tecken i samma saga räknas som en episod. Varje
  episod har fått EN huvudkategori efter Vitkis läsning (KATEGORI nedan) – det är en tolkning, och listan står öppet.
- Rundata: inga runstenar med jól; namnen Iuli (Sö 362) och Iula (Vg 184); de norska träinskrifterna N 151 och N 368.
- Peterson 2007 (Nordiskt runnamnslexikon, Isof): uppslagen Juli och Igull (korta citat, källregeln steg 2).
Varje citat kontrolleras som delsträng av källan innan något skrivs.
    ../../../.venv/bin/python build_jul.py [--write | --update DOC]"""
import collections
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
HK = os.path.join(ROOT, "utdata", "varlden", "korpus", "heimskringla")
PETERSON = "/Volumes/2TB/litteratur/peterson2007_runnamnslexikon.pdf"

# ---- Heimskringla: alla jól- och episoderna ------------------------------------------------------------------------------
flat = lambda s: re.sub(r"\s+", " ", s)  # noqa: E731
texter = {os.path.basename(f)[:-4]: flat(open(f, encoding="utf-8").read()) for f in sorted(glob.glob(HK + "/*.txt"))}
traffar, episoder = [], []
for saga, t in texter.items():
    sist = None
    for m in re.finditer(r"\bjól[a-zþðæöáéíóúý]*", t, re.I):
        traffar.append((saga, m.start()))
        if sist is not None and m.start() - sist < 350:
            episoder[-1]["traffar"].append(len(traffar) - 1)
        else:
            episoder.append({"saga": saga, "traffar": [len(traffar) - 1]})
        sist = m.start()
assert len(texter) == 16 and len(traffar) == 81 and len(episoder) == 52, (len(texter), len(traffar), len(episoder))

# Vitkis läsning, en huvudkategori per episod (episodens nummer i ordningen ovan)
T, G, S, R, K = "tidsangivelse", "gästabud och dryck", "strid och dråp", "tro och kalender", "gåvor och skatt"
KATEGORI = [R, G, G, R, R, T, G, T, T, S, G, S, G, G, K, T, T, R, G, G, G, S, T, G, K, T, T, T, T, G, G, G, T, G, T, G,
            K, T, T, S, T, T, T, K, G, S, R, G, T, T, S, S]
assert len(KATEGORI) == len(episoder)
antal = collections.Counter(KATEGORI)
assert antal == {T: 19, G: 17, S: 7, R: 5, K: 4}, antal
ol = sum(len(e["traffar"]) for e in episoder if e["saga"] == "Saga_Ólafs_hins_helga")
assert ol == 34


def i_saga(saga, *frags):
    for f in frags:
        assert f in texter[saga], (saga, f)


HAKON = "Saga_Hákonar_góða"
LAG = ("Hann setti þat í lögum at hefja jólahald þann tíma sem kristnir menn, ok skyldi þá hverr maðr eiga mælis öl, en "
       "gjalda fé ella, en halda heilagt meðan jólin ynnist. En áðr var jólahald hafit hökunótt, þat var miðsvetrar nótt, "
       "ok haldin þriggja nátta jól.")
i_saga(HAKON, LAG, "15. Kristnihald Hákonar konungs.")
i_saga("Haralds_saga_hins_hárfagra", "Úti vill jól drekka, ef skal einn ráða, fylkir framlyndi , ok Freys leik heyja")
i_saga("Saga_Magnús_blinda_ok_Haralds_gilla", "ok vildi eigi berjast um jólin fyrir helgi sakir",
       "eigi meir en 3 daga var heilagt haldit um jólin")
i_saga("Saga_Magnús_konungs_Erlingssonar", "Um nóttina eptir fimta dag jóla fór Erlingr út í eyna ok tók hús á Özuri ok brendi hann inni, ok alls drap hann tíu tigi manna")
i_saga("Saga_Sigurðar_jórsalafara,_Eysteins_ok_Ólafs", "eigi er þat siðr í Noregi at eta slátr jólakveld")
i_saga("Saga_Ólafs_hins_helga", "ok þá at jólagjöf sverð gullbúit af konungi, ok með bœ þann, er Vettaland hét",
       "Þeir mágar skyldu drekka hálf jól at hvárs þeirra", "til þess at gefa vingjafir hit átta kveld jóla",
       "At jólum skyldi hverr maðr fá konungi mæli malts af arni hverjum, ok lær af oxa þrevetrum")
i_saga(HAKON, "Hákon konungr var vel kristinn, er hann kom í Noreg", "þá tók hann þat ráð, at fara leyniliga með kristni")

# ---- Rundata --------------------------------------------------------------------------------------------------------------
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
from src import research_gaps as rg  # noqa: E402
sten = [r for r in recs.values() if (r.get("object") or "").startswith("runsten") or rg.is_runestone(r)]
jol_sten = [r["signum"] for r in sten if re.search(r"\bjól", r.get("normalization") or "", re.I)]
assert jol_sten == [], jol_sten
jol_alla = sorted(s for s, r in recs.items() if re.search(r"\bjól", r.get("normalization") or "", re.I))
assert jol_alla == ["N 151", "N 368"], jol_alla
assert recs["N 368"]["object"] == "träinskrift" and recs["N 368"]["place"] == "Borgund kirke"
assert "sunnudag þann, er næstr er eptir jól" in recs["N 368"]["normalization"]
assert "Iuli ræistu stæin æftiR \"Ingvar, broður sinn" in recs["Sö 362"]["normalization"]
assert recs["Sö 362"]["place"] == "Tumbo kyrka" and "Iula" in recs["Vg 184"]["normalization"]
SV = [r for r in recs.values() if rg.is_runestone(r)]
KORS = sum(bool((r.get("cross_form") or "").strip()) for r in SV)
assert (len(SV), KORS) == (2321, 959)

# ---- Peterson 2007 --------------------------------------------------------------------------------------------------------
pt = flat(subprocess.run(["pdftotext", PETERSON, "-"], capture_output=True, text=True).stdout)
assert "Juli mn." in pt and "Kortform till mn. pá > Igul-." in pt, "Peterson: Juli"
assert "Av ett ord motsv. (fvn.) ígull m. 'sjöborre', här dock sannolikt med en ur- sprungligare bet. ”igelkott”" in pt

# ---- texten ---------------------------------------------------------------------------------------------------------------
title = "Vikingarnas jul fanns i sagorna – men inte på en enda runsten"
title_en = "The Vikings' Yule is in the sagas – but not on a single runestone"
summary = ("Vi läste varje gång ordet jól står i Heimskringla – 81 gånger, i 52 episoder. Där finns gästabud, gåvor, dråp och "
           "en kung som flyttade julen. På runstenarna finns ingenting. En julspecial om vad sagorna och stenarna säger, "
           "och om mannen som hette Juli.")
summary_en = ("We read every occurrence of the word jól in Heimskringla – 81 times, in 52 episodes. There are feasts, gifts, "
              "killings and a king who moved Yule. On the runestones there is nothing. A Christmas special on what the sagas "
              "and the stones say, and on the man called Júli.")

body = f"""*Hann setti þat í lögum at hefja jólahald þann tíma sem kristnir menn …*

Han stiftade lag om att julen skulle börja vid samma tid som de kristnas, att var man då skulle ha ett mått öl eller böta, och att man skulle hålla helgt så länge julen varade. Förut hade julen börjat *hökunótt*, midvinternatten, och firats i tre nätter.

Så berättar Heimskringla om Håkon den gode, kungen i Norge som enligt sagan var *vel kristinn*, väl kristen, när han kom till landet (Saga Hákonar góða, kap. 15). Han höll sin tro i det tysta, eftersom landet var hedniskt. Och han flyttade folkets fest.

Det är en av de mest citerade raderna om vikingarnas jul. Men hur ofta talar sagorna egentligen om jól, och vad händer då? Och vad säger runstenarna? Vi räknade.

## Jól i siffror

I Heimskringlas sexton kungasagor står ett ord som börjar på *jól-* {len(traffar)} gånger: jól, jólaveizla, jólaboð, jólaaptan, jólagjöf. Flera står i samma berättelse, så vi slog ihop träffar som ligger nära varandra till episoder. Det blev {len(episoder)}. Sedan läste vi varje episod och gav den en huvudsak:

- **Tidsangivelse, {antal[T]} episoder.** "Fyrir jól", "eptir jól". Härar samlas efter julen, sändebud kommer fram strax före. Jól är årets fasta punkt, den tid allt annat räknas från.
- **Gästabud och dryck, {antal[G]}.** *Jólaveizla* och *jólaboð*, kungens julgille, och *samburðaröl*, öl som bönderna bryggde tillsammans. I Olav den heliges saga ska två svågrar dricka halva julen hos den ene och halva hos den andre.
- **Strid och dråp, {antal[S]}.** Natten efter femte juldagen bränner Erling skakke inne Özurr och dödar hundra man. Harald gille vill däremot inte strida under julen "för helgens skull", och han håller helgt i tre dagar – sedan anfaller han Bergen.
- **Tro och kalender, {antal[R]}.** Håkons lag. Skalden Torbjörn hornklove om Harald hårfager, som hellre vill dricka jól ute på havet och "leka Frejs lek". Och Sigurd Jorsalafar, som en julafton vill äta kött – "det är inte sed i Norge att äta kött på julaftonen", säger hans män. Julafton var redan en fastedag.
- **Gåvor och skatt, {antal[K]}.** Olav den helige ger Brynjolf ulvalde ett guldbeslaget svärd och gården Vettaland i julgåva, och delar ut gåvor den åttonde julkvällen. Och vid jul skulle kungen ha ett mått malt från varje härd och ett lår av en treårig oxe.

Olav den heliges saga står ensam för {ol} av de {len(traffar)} träffarna. Den är också den längsta sagan i Heimskringla.

## Och runstenarna?

Av de {len(SV):,} svenska vikingatida runstenarna nämner **ingen** jól. Inte heller någon annan runsten i Rundata gör det. Ordet står bara på två norska träinskrifter från medeltiden, och där som kalender igen: en man i Borgunds kyrka ristade sina runor "söndagen närmast efter jól" (N 368).

Tystnaden är inte konstig. Runstenarna talar om döden, om släkten, om vem som ärvde och om själen. De handlar om en enda människa och den som blev kvar, inte om årets fester. Men samma skifte som Håkons lag beskriver syns ändå på dem: {KORS} av de {len(SV):,} stenarna, {round(100 * KORS / len(SV))} procent, bär ett kors. Midvinterns fest fick ett kristet datum, och minnesstenarna fick ett kristet tecken.

## Mannen som hette Juli

Det finns ett namn på stenarna som låter som julen. Vid Tumbo kyrka i Södermanland står en sten som Kolbjörn och *Iuli* reste efter sin bror Ingvar (Sö 362), och i Västergötland nämns en *Iula* (Vg 184).

Men Juli har inget med julen att göra. Enligt Lena Petersons *Nordiskt runnamnslexikon* är det en kortform av namn som börjar på *Igul-*, och *Igull* kommer av ett ord som på fornvästnordiska betyder sjöborre, "här dock sannolikt med en ursprungligare betydelse 'igelkott'". Juli hette alltså ungefär Igelkotten.

## Det vi inte vet

- **Heimskringla skrevs på Island på 1200-talet,** om kungar som levde från 800-talet till 1100-talets slut. Den berättar om jól som 1200-talets islänningar mindes och tänkte sig den, inte som ett ögonvittne.
- **Indelningen är vår.** Varje episod har fått en huvudsak, och gränserna är inte skarpa: ett gästabud kan sluta i dråp. Listan står öppet, så att den kan prövas.
- **Tre nätter vid midvinter** är sagans uppgift. Vad vikingarna i Sverige gjorde vid jól vet vi mycket lite om, och runstenarna hjälper oss inte.

## God jul

Vi har räknat runstenar hela hösten. Det är kanske passande att årets sista text handlar om det de inte säger. Julen fanns, med öl och gåvor och ibland blod, men den som högg en runsten hade annat att minnas.

God jul från Vitki.

:::box Det viktigaste i korthet
- Ordet jól står {len(traffar)} gånger i Heimskringla, i {len(episoder)} episoder. Oftast är julen en tidsangivelse ({antal[T]}) eller ett gästabud ({antal[G]}); ibland strid ({antal[S]}), tro ({antal[R]}) och gåvor ({antal[K]}).
- Enligt sagan flyttade Håkon den gode julen till de kristnas datum. Förut började den midvinternatten och varade i tre nätter.
- Ingen runsten nämner jól. Ordet finns bara på två norska träinskrifter från medeltiden.
- Namnet Juli på Sö 362 kommer inte av julen utan av igelkotten.
:::

## Källor

- Snorre Sturluson, *Heimskringla*, i Linder och Haggsons utgåva (Uppsala 1869–72), public domain, via [heimskringla.no](https://heimskringla.no). Citaten ur Saga Hákonar góða kap. 15, Haralds saga hins hárfagra, Saga Magnús blinda ok Haralds gilla, Saga Magnús konungs Erlingssonar, Saga Sigurðar jórsalafara och Saga Ólafs hins helga. Översättningarna är våra.
- Samnordisk runtextdatabas (Rundata) 3.1, Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Peterson, Lena 2007. *Nordiskt runnamnslexikon*. Uppsala: Institutet för språk och folkminnen. Uppslagen Juli och Igull.
- Vitkis räkning och indelning: `utdata/blogg/build/build_jul.py` (alla 81 träffar, de 52 episoderna och deras huvudsak), github.com/Precatio/runes.
"""

body_en = f"""*Hann setti þat í lögum at hefja jólahald þann tíma sem kristnir menn …*

He made it law that Yule should begin at the same time as the Christians', that every man should then have a measure of ale or pay a fine, and that the holy days should be kept as long as Yule lasted. Before, Yule had begun on *hökunótt*, midwinter night, and been kept for three nights.

So Heimskringla tells of Hákon the Good, the king in Norway who according to the saga was *vel kristinn*, a good Christian, when he came to the country (Saga Hákonar góða, ch. 15). He kept his faith quietly, because the land was heathen. And he moved the people's feast.

It is one of the most quoted lines about the Vikings' Yule. But how often do the sagas actually speak of jól, and what happens then? And what do the runestones say? We counted.

## Yule in numbers

In Heimskringla's sixteen kings' sagas a word beginning with *jól-* occurs {len(traffar)} times: jól, jólaveizla, jólaboð, jólaaptan, jólagjöf. Several stand in the same story, so we merged hits that lie close together into episodes. That gave {len(episoder)}. Then we read each episode and gave it one main matter:

- **A point in time, {antal[T]} episodes.** "Before Yule", "after Yule". Armies gather after Yule, envoys arrive just before. Yule is the fixed point of the year, the time everything else is reckoned from.
- **Feasts and drink, {antal[G]}.** *Jólaveizla* and *jólaboð*, the king's Yule feast, and *samburðaröl*, ale the farmers brewed together. In the saga of Óláfr the Saint two brothers-in-law are to drink half the Yule at one's house and half at the other's.
- **Fighting and killing, {antal[S]}.** On the night after the fifth day of Yule, Erlingr skakki burns Özurr in his house and kills a hundred men. Haraldr gilli, on the other hand, will not fight during Yule "for the holiness' sake", and he keeps three days holy – then he attacks Bergen.
- **Faith and calendar, {antal[R]}.** Hákon's law. The skald Þorbjörn hornklofi on Haraldr Fairhair, who would rather drink Yule out at sea and "play Freyr's game". And Sigurðr the Crusader, who wants to eat meat one Yule eve – "it is not the custom in Norway to eat meat on Yule eve", his men say. Yule eve was already a fast day.
- **Gifts and tribute, {antal[K]}.** Óláfr the Saint gives Brynjólfr úlfaldi a gold-mounted sword and the farm Vettaland as a Yule gift, and hands out gifts on the eighth evening of Yule. And at Yule the king was to have a measure of malt from every hearth and a leg of a three-year-old ox.

The saga of Óláfr the Saint alone accounts for {ol} of the {len(traffar)} hits. It is also the longest saga in Heimskringla.

## And the runestones?

Of the {len(SV):,} Swedish Viking-age runestones, **none** mentions jól. Nor does any other runestone in the runic database. The word occurs only on two Norwegian wooden inscriptions from the Middle Ages, and there as a calendar again: a man in Borgund church carved his runes "the Sunday next after Yule" (N 368).

The silence is not strange. The runestones speak of death, of kin, of who inherited and of the soul. They are about one person and the one who was left behind, not about the feasts of the year. Yet the same shift that Hákon's law describes shows on them: {KORS} of the {len(SV):,} stones, {round(100 * KORS / len(SV))} per cent, carry a cross. The midwinter feast got a Christian date, and the memorial stones got a Christian sign.

## The man called Júli

There is a name on the stones that sounds like Yule. At Tumbo church in Södermanland stands a stone that Kolbeinn and *Iuli* raised for their brother Ingvarr (Sö 362), and in Västergötland an *Iula* is named (Vg 184).

But Júli has nothing to do with Yule. According to Lena Peterson's *Nordiskt runnamnslexikon* it is a short form of names beginning with *Igul-*, and *Igull* comes from a word that in Old West Norse means sea urchin, "here, however, probably with an older meaning 'hedgehog'". So Júli was called something like the Hedgehog.

## What we do not know

- **Heimskringla was written in Iceland in the 13th century,** about kings who lived from the 9th century to the end of the 12th. It tells of Yule as 13th-century Icelanders remembered and imagined it, not as an eyewitness.
- **The grouping is ours.** Each episode has been given one main matter, and the borders are not sharp: a feast can end in a killing. The list is open, so that it can be tested.
- **Three nights at midwinter** is the saga's statement. What the Vikings in Sweden did at Yule we know very little about, and the runestones do not help us.

## Merry Christmas

We have counted runestones all autumn. It is perhaps fitting that the last text of the year is about what they do not say. Yule was there, with ale and gifts and sometimes blood, but the one who carved a runestone had other things to remember.

Merry Christmas from Vitki.

:::box The main points in brief
- The word jól occurs {len(traffar)} times in Heimskringla, in {len(episoder)} episodes. Most often Yule is a point in time ({antal[T]}) or a feast ({antal[G]}); sometimes fighting ({antal[S]}), faith ({antal[R]}) and gifts ({antal[K]}).
- According to the saga, Hákon the Good moved Yule to the Christians' date. Before, it began on midwinter night and lasted three nights.
- No runestone mentions jól. The word occurs only on two Norwegian wooden inscriptions from the Middle Ages.
- The name Júli on Sö 362 comes not from Yule but from the hedgehog.
:::

## Sources

- Snorri Sturluson, *Heimskringla*, in Linder and Haggson's edition (Uppsala 1869–72), public domain, via [heimskringla.no](https://heimskringla.no). Quotations from Saga Hákonar góða ch. 15, Haralds saga hins hárfagra, Saga Magnús blinda ok Haralds gilla, Saga Magnús konungs Erlingssonar, Saga Sigurðar jórsalafara and Saga Ólafs hins helga. The translations are ours.
- Scandinavian Runic-text Database (Samnordisk runtextdatabas) 3.1, Department of Scandinavian Languages, Uppsala University. Open Database License.
- Peterson, Lena 2007. *Nordiskt runnamnslexikon*. Uppsala: Institute for Language and Folklore. Entries Juli and Igull.
- Vitki's count and grouping: `utdata/blogg/build/build_jul.py` (all 81 hits, the 52 episodes and their main matter), github.com/Precatio/runes.
"""

out = {"slug": "vikingarnas-jul", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Tro och magi", "Norden"]}
from src import blog_labels  # noqa: E402
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
os.makedirs(os.path.join(ROOT, "utdata", "jul"), exist_ok=True)
json.dump({"traffar": len(traffar), "episoder": [{**e, "kategori": k} for e, k in zip(episoder, KATEGORI)],
           "kategorier": dict(antal), "runstenar_sv": len(SV), "med_kors": KORS},
          open(os.path.join(ROOT, "utdata", "jul", "resultat.json"), "w"), ensure_ascii=False, indent=1)
path = os.path.join(ROOT, "utdata", "blogg", "jul.json")
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
                 "topic": "Tro och magi|jul", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
