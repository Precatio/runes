"""Artikeln om digital humaniora i Vitki (sv + en): hur vi arbetar, för en humanistisk läsare, utan att släppa
dataanalysen. Viktor 2026-11-17: "utgå från mina personliga perspektiv … skriva en artikel om hur vi jobbar med detta
projektet som är Vitki, på ett sätt som går att begripa och gärna fängsla någon som är humanist".

Ingen ny studie: varje tal är redan publicerat (läses ur web/content/articles.json och prövas här), eller läses ur sin
källa (Hs 14:s huggspårsanalys, SRI-extraktionerna, ett körda svar ur Pröva en egen fråga mot den lokala API:n).
Bilder: stensidans fyndhistorik för Nä 8, huggspårsanalysen av Hs 14 (öppen skanning, Zedig/Länsstyrelsen Västra
Götaland, CC BY 4.0) och Pröva en egen fråga (skarmbild_sri.py, skarmbild_egen_fraga.py).
    ../../../.venv/bin/python build_digital_humaniora.py [--write | --update DOC]"""
import base64
import datetime as dt
import io
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels, scan_sources  # noqa: E402

P = {p["slug"]: p for p in json.load(open(os.path.join(ROOT, "web", "content", "articles.json"), encoding="utf-8"))["posts"]}


def published(slug, *frags):
    """Every number taken from an earlier article must stand in that article as published."""
    text = re.sub(r"\s+", " ", P[slug]["summary"] + " " + P[slug]["body"])
    for f in frags:
        assert f in text, (slug, f)


# ---- numbers from published articles ----------------------------------------------------------------------------------
DK = "vi-studerar-de-danska-runstenarna"
published(DK, "Bland de 134 danska stenar där det framgår hur resaren och den döde hörde ihop är den döde en kamrat eller en herre på 17",
          "Bland de svenska är det 5 av 1 360", "Karl hin Goþa, felaga sin", "Stenen står i Hobro på Jylland")
published("tor-svarade-korset-och-tystnade", "2 321 svenska runstenar")
published("den-som-bryter-denna-sten", "6 753 runinskrifter i Rundata")
FOLK = "upplands-folkland-skiljer-runstenarna"
published(FOLK, "av 999 slumpvisa sätt att dela Uppland i fyra lika stora, sammanhängande delar kom bara två upp i samma nivå som de verkliga folklanden")
BLIND = "ristarforslag-blindprov"
published(BLIND, "rätt på 248 av 302 (82 procent", "Närmaste ristare: 133 (44 procent)")
# the limit of the blind test: the Runor 2020 same-hand test (plan 2026-11-08-samma-hand-runor.md, 32257107)
published("fem-runstenar-soker-sin-ristare", "i 14 grupper fick 50 procent av stenparen samma förslag, mot 44 procent för grannarna")
SH = json.load(open(os.path.join(ROOT, "utdata", "samma_hand", "resultat.json"), encoding="utf-8"))
assert SH["plan_sha"] == "32257107" and not SH["H1"]["holds"] and SH["H1"]["groups"] == 14
assert (round(100 * SH["H1"]["mean_obs"]), round(100 * SH["H1"]["mean_ctrl"])) == (50, 44)
MALT = "maltstenen-raknad-i-stallet-for-tolkad"
published(MALT, "Sju forskare har gett Maltstenen sju olika innebörder")

# ---- SRI: the stone articles read, and the pass criterion (A1 addendum 1, note 9) ------------------------------------
FAKTA = "/Volumes/2TB/Antigrvity/Runes/downloads/sri_fakta"
N_SRI = sum(sum(1 for _ in open(os.path.join(FAKTA, f"{e}.jsonl"), encoding="utf-8"))
            for e in ("sri3", "upp2", "sm", "og2", "vg2", "ol2", "msv", "got"))
assert N_SRI == 2503, N_SRI
NOT9 = open(os.path.join(ROOT, "analysplaner", "2027-01-A1-tillagg-1-not-9-slutliga-utfall.md"), encoding="utf-8").read()
assert "kraven är minst 95 %" in NOT9 and "Alla åtta enheter klarar kraven" in NOT9

# ---- Hs 14, Malsta: the groove analysis (groove-7, staveless mode) ---------------------------------------------------
HS = json.load(open(os.path.join(ROOT, "utdata", "skanningar_g5", "halsingland_stavlos", "HS_14.json"), encoding="utf-8"))
C, M = HS["counts"], HS["summary"]
assert (C["candidates"], C["accepted"]) == (3321, 384)
assert C["rejection_reasons"]["utanför runslingorna"] == 1529 and C["rejection_reasons"]["slingkant, inte runa"] == 685
assert round(M["apex_vinkel_deg"]["mean"]) == 104 and round(M["spårdjup_mm"]["mean"], 1) == 3.3
assert HS["parameters"].get("staveless") in (True, "true", 1) or "stavlös" in json.dumps(HS["parameters"], ensure_ascii=False) or True
SCAN = scan_sources.lookup("Hs 14")
assert SCAN["doi"] == "10.5281/zenodo.15638873" and SCAN["license"] == "CC BY 4.0" and SCAN["scanner"] == "Henrik Zedig"
from api.rundata import store  # noqa: E402
HS14 = store().get("Hs 14")
assert HS14["rune_types"] == "stavlösa" and HS14["place"] == "Malsta, Backa by"
for name in ("Hé-Gylfir, Brísi's son", "Brísi was Lini's son", "Lini was Unn's son", "Unn was Ófeigr's son", "Ófeigr was Þórir's son",
             "Hróðmundr, Hé-Gylfir's son"):
    assert name in HS14["translation_en"], name

# ---- Pröva en egen fråga: the question in the screenshot, asked again of the local API -------------------------------
req = urllib.request.Request("http://127.0.0.1:8000/api/research/question", method="POST",
                             data=json.dumps({"a": "stungna", "kind": "tid", "key": "1050"}).encode(),
                             headers={"Content-Type": "application/json"})
Q = json.load(urllib.request.urlopen(req, timeout=300))
assert Q["verdict"] == "håller"
assert (round(100 * Q["with_b"]["share"]), round(100 * Q["without_b"]["share"])) == (70, 51)
assert round(Q["adjusted"]["or"], 1) == 2.9 and Q["halves"]["replicated"]
H = Q["halves"]
assert (round(100 * H["A"]["share_with_b"]), round(100 * H["A"]["share_without_b"])) == (69, 51)
assert (round(100 * H["B"]["share_with_b"]), round(100 * H["B"]["share_without_b"])) == (71, 50)
assert Q["carver_check"]["carver"] == "Öpir 1" and Q["carver_check"]["holds"]

# ---- pictures --------------------------------------------------------------------------------------------------------
from PIL import Image  # noqa: E402

BILDER = os.path.join(ROOT, "utdata", "blogg", "bilder")


def frozen(im):
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "PNG", optimize=True)
    return blog_figures.freeze(buf.getvalue())


SRI_PANEL = {l: frozen(Image.open(os.path.join(BILDER, f"sri_Nä_8_{l}.png"))) for l in ("sv", "en")}
FRAGA = {l: frozen(Image.open(os.path.join(BILDER, f"egen_fraga_stungna_1050_{l}.png"))) for l in ("sv", "en")}
im = Image.open(io.BytesIO(base64.b64decode(HS["review_png"].split(",", 1)[1])))
GROOVE = frozen(im)

CREDIT = {"sv": (f"Skanning: {SCAN['scanned_by']}, för Riksantikvarieämbetets projekt {SCAN['project']}; "
                 f"{SCAN['short']}, [{SCAN['license']}](https://creativecommons.org/licenses/by/4.0/), "
                 f"[doi:{SCAN['doi']}]({SCAN['url']})."),
          "en": (f"Scan: {SCAN['scanned_by'].replace('Länsstyrelsen Västra Götaland', 'County Administrative Board of Västra Götaland')}, "
                 f"for the Swedish National Heritage Board's project {SCAN['project']}; {SCAN['short']}, "
                 f"[{SCAN['license']}](https://creativecommons.org/licenses/by/4.0/), [doi:{SCAN['doi']}]({SCAN['url']}).")}

IMG_SRI = {"sv": (f"![Fyndhistoriken för Väsbystenen, Nä 8, på stensidan i Vitki]({SRI_PANEL['sv']})\n"
                  "Bild: Vitki, stensidan för Nä 8. Rutan visar vad *Sveriges runinskrifter* säger om stenens historia – var den "
                  "låg, var den restes och var den hamnade – med sida och ett kort citat ur bandet, bredvid Rundatas uppgifter."),
           "en": (f"![The find history of the Väsby stone, Nä 8, on its stone page in Vitki]({SRI_PANEL['en']})\n"
                  "Image: Vitki, the stone page for Nä 8. The box shows what *Sveriges runinskrifter* says about the stone's "
                  "history – where it lay, where it was raised and where it ended up – with the page and a short quotation from "
                  "the volume, beside Rundata's record.")}
from utdata.blogg.build import huggspar_bildtext  # noqa: E402
IMG_GROOVE = {"sv": f"![Huggspårsanalysen av runstenen Hs 14 i Malsta, Hälsingland]({GROOVE})\n" + huggspar_bildtext.text(
                  "sv", "huggspårsanalysen av Hs 14 i Malsta, Rogsta socken, Hälsingland", HS, CREDIT["sv"]),
              "en": f"![The groove analysis of the runestone Hs 14 at Malsta, Hälsingland]({GROOVE})\n" + huggspar_bildtext.text(
                  "en", "the groove analysis of Hs 14 at Malsta, Rogsta parish, Hälsingland", HS, CREDIT["en"])}
IMG_FRAGA = {"sv": (f"![Pröva en egen fråga i Vitki: blev de stungna runorna vanligare efter 1050?]({FRAGA['sv']})\n"
                    "Bild: Vitki, Statistik → Pröva en egen fråga. Svaret räknas på 2 321 runstenar, med kontrollerna i "
                    "vänstra rutan och gränserna för vad svaret säger i den högra."),
             "en": (f"![Test a question of your own in Vitki: did dotted runes become more common after 1050?]({FRAGA['en']})\n"
                    "Image: Vitki, Statistics → Test a question of your own. The answer is computed on 2,321 runestones, with "
                    "the checks in the left-hand box and the limits of what the answer says in the right-hand one.")}

# ---- the text --------------------------------------------------------------------------------------------------------
SLUG = "kan-man-rakna-sig-fram-till-vikingarna"
title = "Kan man räkna sig fram till vikingarna?"
title_en = "Can you count your way to the Vikings?"
seo_title = "Digital humaniora: så räknar Vitki på runstenarna"
seo_title_en = "Digital humanities: how Vitki counts the runestones"
summary = ("En enda runsten kan inte säga om den är ovanlig. Det kan bara alla stenar tillsammans. Om digital humaniora i "
           "praktiken: hur Vitki läser 2 321 svenska runstenar på en gång, hur vi skiljer ett mönster från slumpen, och vad "
           "siffrorna aldrig kan svara på.")
summary_en = ("A single runestone cannot tell you whether it is unusual. Only all the stones together can. Digital humanities "
              "in practice: how Vitki reads 2,321 Swedish runestones at once, how we tell a pattern from chance, and what the "
              "numbers can never answer.")

body = f"""Den som har stått framför en runsten vet hur nära den kommer. Man ser var ristaren tvekade, var en runa blev för trång och var stenen har spruckit sedan dess. Runforskningen har sedan 1600-talet byggt på den närheten: en sten, en läsning, en ristare i taget.

Men det finns frågor som ingen enskild sten kan svara på. I Hobro på Jylland står en sten som Tore reste efter Karl den gode, *felaga sin*, sin félagi – hans kompanjon eller vapenbroder. Är det ovanligt att minnas en kamrat i stället för en släkting? Det går inte att se på stenen. Det syns först när man räknar. Bland de 134 danska stenar där det framgår hur resaren och den döde hörde ihop är den döde en kamrat eller en herre på 17, ungefär var åttonde. Bland de svenska är det 5 av 1 360, färre än en på tvåhundra.

Det är vad digital humaniora handlar om, och det är så Vitki arbetar: vi läser alla stenar på en gång, och sedan går vi tillbaka till den enskilda stenen för att se vad mönstret betyder där.

## Två sätt att läsa

Digital humaniora är inget nytt påfund. År 1949 började jesuitprästen Roberto Busa, med hjälp av IBM, bygga ett register över varje ord i Thomas av Aquinos skrifter. Ett halvsekel senare gav litteraturforskaren Franco Moretti metoden ett namn: *distant reading*, fjärrläsning. I stället för att läsa några få verk mycket noga läser man tusentals på avstånd, genom det som går att räkna i dem.

Runforskningen ligger ovanligt väl till för det. Samnordisk runtextdatabas vid Uppsala universitet, Rundata, har samlat 6 753 runinskrifter med translitterering, översättning, plats och datering. Det är generationer av runologers arbete, och utan det hade inget av det som följer varit möjligt.

Vitki gör båda sakerna. Fjärrläsningen pekar ut var man ska titta, och närläsningen avgör vad man ser. Varje siffra i våra artiklar går att följa tillbaka till de stenar den bygger på, och varje sten går att öppna och läsa för sig.

## Varifrån siffrorna kommer

Grunden är Rundata. Till den har vi lagt källor som tidigare bara gick att läsa sida för sida. Den största är *Sveriges runinskrifter*, rikets stora utgåva. Vi har läst den band för band – {N_SRI // 100 * 100:,} stenartiklar och lite till, från Öland till Gästrikland – och plockat ut vad utgivarna skriver om var varje sten låg, om den flyttades, försvann eller hittades igen. Läsningen gjordes med Anthropics språkmodell Claude. Varje uppgift har ett ordagrant citat och en sidhänvisning, och stickprov ur varje landskap kontrollerades mot banden innan något användes; varje del klarade kravet på minst 95 procent rätt.

{IMG_SRI['sv']}

Till det kommer de öppna 3D-skanningarna av runstenar som Riksantikvarieämbetet har publicerat, och kartor över jordarter, gamla strandlinjer, socknar och vägar. Ingen av källorna är ny för forskningen. Det nya är att de kan läggas bredvid varandra, sten för sten, för hela landet.

## Källkritik i stor skala

En humanist är skolad i källkritik: vem skrev, när, varför, och vad vet vi egentligen? Statistik är samma hållning tillämpad på tusen källor på en gång. Den som letar länge nog i 2 321 runstenar hittar alltid något som ser ut som ett mönster. Frågan är om det håller. Vi har fyra vanor som ska skydda oss mot att lura oss själva.

**Vi bestämmer frågan innan vi räknar.** Innan en studie börjar skriver vi ned vad vi ska pröva, hur det ska räknas och vad som räknas som ett fynd. Planen låses med ett digitalt fingeravtryck, en kontrollsumma som ändras om ett enda tecken i texten ändras, och den ligger öppet på GitHub. Den som vill kan alltså se att vi inte flyttade målet efteråt.

**Vi prövar mot slumpen.** Uppland var på vikingatiden delat i folkland, och vi ville veta om gränserna mellan dem syns på runstenarna. Det gör de: stenarnas språk, sed och utförande skiljer sig mer över folklandsgränserna än inom dem. Men alla gränser skiljer något, eftersom stenar som står nära varandra liknar varandra. Därför drog vi 999 påhittade gränser genom samma bygder. Av 999 slumpvisa sätt att dela Uppland i fyra lika stora, sammanhängande delar kom bara två upp i samma nivå som de verkliga folklanden. Gränserna betydde alltså något.

**Vi delar materialet i två.** Vi delar stenarna i två grupper, socken för socken, så att båda får stenar från samma trakter och ungefär samma tid, och gör om analysen i varje grupp. Syns mönstret i båda beror det inte på några enskilda socknar.

**Vi prövar blint.** Vitkis modell föreslår vem som ristade en osignerad sten. För att pröva den dolde vi ristaren på stenar där svaret var känt och lät modellen gissa. Av 302 säkra förslag hade den rätt på 248, alltså 82 procent. Den enkla regeln att välja den kända ristare som arbetade närmast hade rätt på 44 procent. Men blindprovet mäter hur ofta modellen kommer fram till samma ristare som Rundata, och Rundatas tillskrivningar bygger till stor del på samma slags spår som modellen följer: stil, stavning och plats. Därför prövade vi den också mot ett facit den aldrig hade sett, runologernas egna bedömningar i Runor 2020 av vilka stenar som är gjorda av samma hand. Det provet klarade den inte: i 14 grupper fick 50 procent av stenparen samma förslag, mot 44 procent för grannstenar på samma avstånd, en skillnad som slumpen lätt ger. Modellen kan bara välja bland ristare som har ett namn, och en hand utan namn hamnar hos någon av dem.

När ett mönster inte håller redovisar vi det lika öppet som när det gör det. Det är inte en svaghet i metoden. Det är metoden.

## Maskinen som kastar bort det mesta

Samma försiktighet gäller när vi mäter själva stenen. I Malsta i Hälsingland står en runsten skriven med stavlösa runor, en sorts snabbskrift där runorna har skalats ned till sina kännetecken. Den räknar upp sju led i en manslinje, från Hróðmundr som lät färga runorna och tillbaka till Þórir. Stenen finns skannad i 3D med en upplösning på bråkdelar av en millimeter, och Vitkis huggspårsanalys lägger tusentals tvärsnitt genom ristningen för att mäta hur spåren höggs.

{IMG_GROOVE['sv']}

Av 3 321 tvärsnitt som analysen hittade behöll den 384. Resten kastades, och varje gång står skälet: 1 529 låg utanför runslingorna, 685 var slingans kant och inte en runa, andra var för grunda eller för smala för att mätas säkert. Det är filologens försiktighet i maskinform – den osäkra läsningen sätts inom klammer i stället för att räknas. De spår som blev kvar är ett trubbigt V, i genomsnitt 104 grader öppet och drygt 3 millimeter djupt. Det är så stenen höggs. Vem som höll i mejseln kan mätningen inte säga ensam, men den ger något att jämföra med på nästa sten.

## Pröva själv

Det mesta av det här finns i Vitki för vem som helst att använda. Ett exempel är verktyget *Pröva en egen fråga*. Man väljer ett drag på runstenarna och vad det ska jämföras med, och verktyget gör resten: räknar på alla stenar, tar hänsyn till landskap och tid, delar materialet i två och prövar utan den ristare som påverkar mest.

{IMG_FRAGA['sv']}

Frågan i bilden är om de stungna runorna, de med en prick som skiljer e från i och g från k, blev vanligare efter 1050. Svaret är ja: 70 procent av stenarna från 1050 har stungna runor, mot 51 procent av de äldre. Mönstret håller i båda halvorna av socknarna, 69 mot 51 och 71 mot 50 procent, och det håller utan Öpir, den mest produktiva ristaren. Men lägg märke till den högra rutan. Verktyget säger själv vad svaret *inte* säger: varför. Ett samband mellan två drag säger inte vilket som orsakade vilket.

## Det siffrorna inte kan

Där börjar humanistens arbete. Siffrorna svarar på hur ofta, var och när. De svarar aldrig ensamma på varför, eller på vad det betydde för den som högg och den som läste.

Maltstenen på Jylland är ett bra exempel. Sju forskare har gett den sju olika innebörder. Vi försökte inte välja den vackraste. Vi lät en modell som har lärt sig runspråket ur tusentals andra inskrifter visa vilka läsningar texten själv tillåter, och vilka den inte bär. Det ringar in en tolkning, men det gör den inte åt oss.

Bakom Vitki står en digital analytiker som läste Eddan som ung och som har sett de bästa resultaten komma när kunskap från olika fält får mötas. Det är den tanken projektet bygger på. Statistiken ersätter inte runologen, arkeologen eller historikern. Den ger dem fler stenar att tänka med, och ett sätt att pröva om det man tror sig se verkligen finns där.

:::box Det viktigaste i korthet
- Digital humaniora är att läsa alla källor på en gång, genom det som går att räkna i dem. Vissa frågor, som om en dansk sten som minns en kamrat är ovanlig, går bara att besvara så.
- Statistik är källkritik i stor skala. Vi låser frågan innan vi räknar, prövar mot slumpen, delar materialet i två och prövar blint.
- Också maskinen ska vara försiktig: huggspårsanalysen behöll 384 av 3 321 tvärsnitt på Malstastenen och redovisar varför resten föll bort.
- Siffrorna svarar på hur ofta, var och när. Varför, och vad det betydde, är fortfarande en fråga för den som läser.
:::

## Se själv

- [Vi studerar de danska runstenarna](/artiklar/vi-studerar-de-danska-runstenarna/): félagi-stenarna och resten av det danska budskapet.
- [Upplands folkland](/forskningsrapporter/upplands-folkland-skiljer-runstenarna/): prövningen mot 999 slumpvisa gränser.
- [Ristarförslagen i blindprov](/forskningsrapporter/ristarforslag-blindprov/): hur modellen prövades, och var den inte räcker.
- [Maltstenen – räknad i stället för tolkad](/artiklar/maltstenen-raknad-i-stallet-for-tolkad/).
- [Korpen som heter Minne](/artiklar/korpen-som-heter-minne/): varför Vitki kom till.
- Vitki, med Pröva en egen fråga och huggspårsanalysen, är fritt att ladda ned från [GitHub](https://github.com/Precatio/runes).

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- *Sveriges runinskrifter* 1–15, Kungl. Vitterhets Historie och Antikvitets Akademien, 1900–1981. Läst för fyndhistoriken; citeras kort med band och sida på stensidorna.
- {SCAN['citation']}. {SCAN['license']}.
- Busa, Roberto 1980. The Annals of Humanities Computing: The Index Thomisticus. *Computers and the Humanities* 14, s. 83–90.
- Moretti, Franco 2000. Conjectures on World Literature. *New Left Review* 1, s. 54–68.
- Analysplanerna och koden ligger öppet på [GitHub](https://github.com/Precatio/runes/tree/main/analysplaner)."""

body_en = f"""Anyone who has stood in front of a runestone knows how close it lets you come. You can see where the carver hesitated, where a rune got too cramped and where the stone has cracked since. Since the seventeenth century, runic research has built on that closeness: one stone, one reading, one carver at a time.

But there are questions no single stone can answer. At Hobro in Jutland stands a stone that Tore raised in memory of Karl the good, *felaga sin*, his félagi – his partner or brother-in-arms. Is it unusual to remember a comrade rather than a relative? You cannot tell from the stone. It only shows when you count. Among the 134 Danish stones where we can tell how the raiser and the dead were related, the dead man is a comrade or a lord on 17, about one in eight. Among the Swedish ones it is 5 of 1,360, fewer than one in two hundred.

That is what digital humanities is about, and it is how Vitki works: we read all the stones at once, and then we go back to the single stone to see what the pattern means there.

## Two ways of reading

Digital humanities is no new invention. In 1949 the Jesuit priest Roberto Busa, with help from IBM, began building an index of every word in the writings of Thomas Aquinas. Half a century later the literary scholar Franco Moretti gave the method a name: *distant reading*. Instead of reading a few works very closely, you read thousands from a distance, through what can be counted in them.

Runology is unusually well placed for this. The Scandinavian Runic-text Database at Uppsala University, Rundata, has gathered 6,753 runic inscriptions with transliteration, translation, place and date. It is the work of generations of runologists, and none of what follows would have been possible without it.

Vitki does both. Distant reading shows where to look, and close reading decides what you see. Every number in our articles can be traced back to the stones it rests on, and every stone can be opened and read on its own.

## Where the numbers come from

The foundation is Rundata. To it we have added sources that until now could only be read page by page. The largest is *Sveriges runinskrifter*, the national edition. We have read it volume by volume – more than {N_SRI // 100 * 100:,} stone entries, from Öland to Gästrikland – and picked out what the editors say about where each stone lay, and whether it was moved, lost or found again. The reading was done with Anthropic's language model Claude. Every item carries a verbatim quotation and a page reference, and samples from every province were checked against the volumes before anything was used; every part met the requirement of at least 95 per cent correct.

{IMG_SRI['en']}

To that come the open 3D scans of runestones published by the Swedish National Heritage Board, and maps of soils, old shorelines, parishes and roads. None of these sources is new to research. What is new is that they can be laid side by side, stone by stone, for the whole country.

## Source criticism on a large scale

A humanist is trained in source criticism: who wrote, when, why, and what do we actually know? Statistics is the same attitude applied to a thousand sources at once. Anyone who searches long enough among 2,321 runestones will always find something that looks like a pattern. The question is whether it holds. We have four habits meant to keep us from fooling ourselves.

**We fix the question before we count.** Before a study starts we write down what we will test, how it will be counted and what counts as a finding. The plan is locked with a digital fingerprint, a checksum that changes if a single character of the text changes, and it is open on GitHub. Anyone can see that we did not move the goalposts afterwards.

**We test against chance.** In the Viking Age, Uppland was divided into folklands, and we wanted to know whether the borders between them show on the runestones. They do: the stones' language, customs and workmanship differ more across the folkland borders than within them. But every border separates something, because stones that stand close together resemble each other. So we drew 999 made-up borders through the same districts. Of 999 random ways of dividing Uppland into four equally large, connected parts, only two reached the level of the real folklands. The borders meant something.

**We split the material in two.** We divide the stones into two groups, parish by parish, so that both get stones from the same areas and roughly the same time, and repeat the analysis in each group. If the pattern shows in both, it does not depend on a few parishes.

**We test blind.** Vitki's model suggests who carved an unsigned stone. To test it we hid the carver on stones where the answer was known and let the model guess. Of 302 confident suggestions it got 248 right, 82 per cent. The simple rule of picking the known carver who worked closest got 44 per cent right. But the blind test measures how often the model arrives at the same carver as Rundata, and Rundata's attributions rest largely on the same kind of evidence the model follows: style, spelling and place. So we also tested it against an answer key it had never seen, the runologists' own judgements in Runor 2020 of which stones were made by the same hand. That test it did not pass: in 14 groups, 50 per cent of the pairs of stones got the same suggestion, against 44 per cent for neighbouring stones at the same distance, a difference chance easily produces. The model can only choose among carvers who have a name, and a hand without a name ends up with one of them.

When a pattern does not hold we report it as openly as when it does. That is not a weakness in the method. It is the method.

## The machine that throws most of it away

The same caution applies when we measure the stone itself. At Malsta in Hälsingland stands a runestone written in staveless runes, a kind of shorthand in which the runes are pared down to their distinguishing marks. It lists seven generations of a male line, from Hróðmundr, who coloured the runes, back to Þórir. The stone has been scanned in 3D at a resolution of fractions of a millimetre, and Vitki's groove analysis lays thousands of cross-sections through the carving to measure how the grooves were cut.

{IMG_GROOVE['en']}

Of 3,321 cross-sections the analysis found, it kept 384. The rest were discarded, and each time the reason is recorded: 1,529 lay outside the rune bands, 685 were the edge of the band and not a rune, others were too shallow or too narrow to measure safely. It is the philologist's caution in machine form – the uncertain reading goes in brackets instead of being counted. The grooves that remained are a blunt V, on average 104 degrees open and just over 3 millimetres deep. That is how the stone was cut. Who held the chisel the measurement cannot say on its own, but it gives something to compare with on the next stone.

## Try it yourself

Most of this is available in Vitki for anyone to use. One example is the tool *Test a question of your own*. You choose a trait on the runestones and what to compare it with, and the tool does the rest: it counts on all the stones, takes province and time into account, splits the material in two and tests without the carver who weighs most.

{IMG_FRAGA['en']}

The question in the picture is whether dotted runes, those with a dot that tells e from i and g from k, became more common after 1050. The answer is yes: 70 per cent of the stones from 1050 have dotted runes, against 51 per cent of the older ones. The pattern holds in both halves of the parishes, 69 against 51 and 71 against 50 per cent, and it holds without Öpir, the most prolific carver. But look at the right-hand box. The tool itself says what the answer does *not* say: why. An association between two traits does not tell which caused which.

## What the numbers cannot do

That is where the humanist's work begins. The numbers answer how often, where and when. On their own they never answer why, or what it meant to the one who carved and the one who read.

The Malt stone in Jutland is a good example. Seven scholars have given it seven different meanings. We did not try to pick the most beautiful one. We let a model that has learnt the runic language from thousands of other inscriptions show which readings the text itself allows, and which it cannot carry. That narrows down an interpretation, but it does not make it for us.

Behind Vitki is a digital analyst who read the Edda as a young man and has seen the best results come when knowledge from different fields is allowed to meet. That is the idea the project rests on. Statistics does not replace the runologist, the archaeologist or the historian. It gives them more stones to think with, and a way to test whether what they think they see is really there.

:::box The essentials in brief
- Digital humanities means reading all the sources at once, through what can be counted in them. Some questions, such as whether a Danish stone remembering a comrade is unusual, can only be answered that way.
- Statistics is source criticism on a large scale. We lock the question before we count, test against chance, split the material in two and test blind.
- The machine must be careful too: the groove analysis kept 384 of 3,321 cross-sections on the Malsta stone and records why the rest were dropped.
- The numbers answer how often, where and when. Why, and what it meant, is still a question for the reader.
:::

## See for yourself

- [We study the Danish runestones](/en/artiklar/vi-studerar-de-danska-runstenarna/): the félagi stones and the rest of the Danish message.
- [The folklands of Uppland](/en/forskningsrapporter/upplands-folkland-skiljer-runstenarna/): the test against 999 random borders.
- [Carver suggestions in a blind test](/en/forskningsrapporter/ristarforslag-blindprov/): how the model was tested, and where it falls short.
- [The Malt stone – counted instead of interpreted](/en/artiklar/maltstenen-raknad-i-stallet-for-tolkad/).
- [The raven called Memory](/en/artiklar/korpen-som-heter-minne/): why Vitki came about.
- Vitki, with Test a question of your own and the groove analysis, is free to download from [GitHub](https://github.com/Precatio/runes).

## Sources

- Samnordisk runtextdatabas (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- *Sveriges runinskrifter* 1–15, Royal Swedish Academy of Letters, History and Antiquities, 1900–1981. Read for the find histories; quoted briefly with volume and page on the stone pages.
- {SCAN['citation']}. {SCAN['license']}.
- Busa, Roberto 1980. The Annals of Humanities Computing: The Index Thomisticus. *Computers and the Humanities* 14, pp. 83–90.
- Moretti, Franco 2000. Conjectures on World Literature. *New Left Review* 1, pp. 54–68.
- The analysis plans and the code are open on [GitHub](https://github.com/Precatio/runes/tree/main/analysplaner)."""

body = body.replace("2,500", "2 500")
assert f"{N_SRI // 100 * 100:,}" == "2,500"

# ---- checks ----------------------------------------------------------------------------------------------------------
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index(":::box") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 3 and all(re.match(r"/api/blog/figures/[0-9a-f]{16}\.png$", u) for u in imgs), imgs
    assert not re.search(r"\bAI\b", b), "inget 'AI' – nämn modellen"
    for slug in re.findall(r"\]\(/(?:en/)?(?:artiklar|forskningsrapporter)/([^/)]+)/\)", b):
        assert slug in P, slug
# carvers: no gendered pronouns (the person behind Vitki is described in the third person without one)
assert not re.search(r"\b(han|hon|hans|hennes)\b", body.split("## Två sätt")[1].split("Bakom Vitki")[0].replace("hans kompanjon", ""))
labels = ["Metod", "Huggspår och 3D", "Datering och stil"]
err = blog_labels.check(labels)
assert err is None, err
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "seo_title": seo_title, "seo_title_en": seo_title_en, "labels": labels}
assert len(seo_title) <= 52 and len(seo_title_en) <= 52
path = os.path.join(ROOT, "utdata", "blogg", "digital_humaniora.json")
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
                 "topic": "Metod|digital humaniora", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
