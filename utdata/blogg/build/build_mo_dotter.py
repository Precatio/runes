"""Artikeln "Mö, dotter eller flicka? Ordet som kunde betyda ogift" (sv + en): ordet mær/møy på de vikingatida
inskrifterna – hur det används, vilka som reste stenarna och hur olika det har översatts. Beskrivande artikel (spår P),
ingen prövning mot slumpen. Fortsättning vid sidan av "Döttrarna som runstenarna glömde" (upprepar den inte).

Varje siffra räknas ur data/rundata.json och låses med asserts. Varje citat ur Fornvännen och Futhark kontrolleras mot
originalsidan i fulltextregistret downloads/tidskrifter/sok.sqlite (blanksteg och mjuka bindestreck borttagna, eftersom
OCR:en har mellanslag inne i orden). Bilderna kommer från Wikimedia Commons, licenser kontrollerade mot Commons API.
    ../../../.venv/bin/python build_mo_dotter.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import commons  # noqa: E402

INS = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
recs = {r["signum"]: r for r in INS}
nz = lambda s: re.sub(r"§[A-Z] ", "", recs[s]["normalization"].replace('"', "")).strip()  # noqa: E731
tl = lambda s: recs[s]["transliteration"]  # noqa: E731
sp = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en = lambda n: f"{n:,}"  # noqa: E731

# ---- räkningen ur Rundata -----------------------------------------------------------------------------------------
SE = ("U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Nä", "Vs", "Gs", "Hs", "M", "J", "D", "Bo", "Vr")
pre = lambda x: x["signum"].split(" ")[0]  # noqa: E731
is_stone = lambda x: "runsten" in (x.get("object") or "").lower()  # noqa: E731  (också fragment och förlorade stenar)
ows = lambda x: re.sub(r"[\[\]()?]", "", x.get("normalization_ows") or "")  # noqa: E731
MAER = re.compile(r"\b([Mm]ær|[Mm]ey|[Mm]eyj\w*)\b")   # fornvästnordisk normalisering: mær, mey, meyju, meyjar
DOTTIR = re.compile(r"\b(dóttur|dóttir|dœtr|dœtra|dóttra)\b")
V_SE = [x for x in INS if x["period"] == "V" and pre(x) in SE]
V_SE_STONES = [x for x in V_SE if is_stone(x)]
MAER_STONES = sorted(x["signum"] for x in V_SE_STONES if MAER.search(ows(x)))
MAER_OTHER = sorted(x["signum"] for x in V_SE if not is_stone(x) and MAER.search(ows(x)))
DOT_STONES = [x["signum"] for x in V_SE_STONES if DOTTIR.search(ows(x))]
assert len(V_SE_STONES) == 2320
assert MAER_STONES == ["U 126", "U 169", "U 341", "U 861"], MAER_STONES
assert MAER_OTHER == ["U 29", "Ög 239", "Ög Fv1958;252"], MAER_OTHER
N_ALL = len(MAER_STONES) + len(MAER_OTHER)
assert N_ALL == 7
SV_ORD = {3: "tre", 4: "fyra", 7: "sju"}
EN_ORD = {3: "three", 4: "four", 7: "seven"}
assert len(DOT_STONES) == 25  # två av dem osäkra (U 387 dóttur/Dóttur, Vg 177 dóttur/systur)
assert {recs[s]["object"] for s in MAER_OTHER} == {"gravhäll", "berghäll"}
assert recs["Ög 239"]["object"] == recs["Ög Fv1958;252"]["object"] == "gravhäll" and recs["U 29"]["object"] == "berghäll"
# Norge och Danmark för sig (runstenar, vikingatid)
NO = [x for x in INS if x["period"] == "V" and pre(x) == "N" and is_stone(x)]
DK = [x for x in INS if x["period"] == "V" and pre(x) == "DR" and is_stone(x)]
assert len(NO) == 66 and [x["signum"] for x in NO if MAER.search(ows(x))] == ["N 68"]
assert len(DK) == 239 and not [x for x in DK if MAER.search(ows(x))]
# utanför Sverige står ordet på en enda vikingatida runsten
assert [x['signum'] for x in INS if x['period'] == 'V' and pre(x) not in SE and is_stone(x) and MAER.search(ows(x))] == ['N 68']
assert not [x for x in INS if x["period"] == "V" and pre(x) == "DR" and MAER.search(ows(x))]

# ---- de citerade raderna står ordagrant i Rundata -------------------------------------------------------------------
assert "[G]unnarr lagði stæin þenna æftiR Guðlaug, kunu si[n]a goða, ok æftiR Asu, dottur sina, møy goða." in nz("Ög 239")
assert "totur : sina : mu" in tl("Ög 239")
assert "GæiRa let gærva kumbl þessa yfiR Þorð, bonda sinn, ok Sigriðr, maR, yfiR sinn faður." in nz("Ög Fv1958;252")
assert "Guð hialpi sial hans." in nz("Ög Fv1958;252") and "siriþr : mar" in tl("Ög Fv1958;252")
assert "æftiR Frøystæin, sun sinn, ok æftiR <uku>, møy sina." in nz("U 169")
assert "uk + iftiR × uku + my sina" in tl("U 169")
assert "æftiR Ragnvi, moður/møy sina. Nu hialpi Guð salu þæiRa ok Guðs moðiR." in nz("U 341")
assert "ragnui × mu sina" in tl("U 341") and "kus × muþiR" in tl("U 341")
assert {c["name"] for c in recs["U 169"]["carvers"]} == {c["name"] for c in recs["U 341"]["carvers"]} == {"Gunnar"}
assert all(c["kind"] == "A" for s in ("U 169", "U 341") for c in recs[s]["carvers"])  # attribuerad, inte signerad
assert "Guð hialpi [an]d þæiRa ok Guðs maR goð." in nz("U 126") and recs["U 126"]["carvers"] == []
assert "ok at Møy, dottur sina" in nz("U 861") and "mai : tutor" in tl("U 861")
assert "GæiRmundr [f]ikk GæiRlaug møydomi i." in nz("U 29") and "En maR æin lifði; hon het [In]ga." in nz("U 29")
assert "Ha[na] fikk Ragnfastr i Snutastaðum." in nz("U 29") and "Þar kvam GæiRlaug at arfi Ingu, dottur sinnaR." in nz("U 29")
N68 = "Gunnvôr gerði brú, Þrýðríks dóttir, eptir Ástríði, dóttur sína. Sú var mær hônnurst á Haðalandi."
assert N68 in nz("N 68") and "1025-1050" in recs["N 68"]["dating"]
assert "MøyaR, hafin iðra bøn retta." in nz("G 191") and recs["G 191"]["period"] == "M" and "1200" in recs["G 191"]["dating"]
assert "fru Maria møyu" in nz("G 104A") and "1400" in recs["G 104A"]["dating"]
assert "Iungfru eR min ro" in nz("Vg 204") and recs["Vg 204"]["object"] == "dörrbeslag" and "1200" in recs["Vg 204"]["dating"]
for s in ("U 126", "U 169", "U 341", "U 861"):
    assert recs[s]["period"] == "V" and is_stone(recs[s])
# I artikeln om döttrarna räknades Björkeby och Söderby inte med (handgenomgången lista DOT i dottrar_fakta.py)
_fakta = open(os.path.join(ROOT, "utdata", "blogg", "build", "dottrar_fakta.py"), encoding="utf-8").read()
_DOT = re.search(r"^DOT = (\[.*?\])", _fakta, re.M).group(1)
assert '"U 169"' not in _DOT and '"U 341"' not in _DOT and '"Ög 239"' in _DOT
DOTTRAR_ART = "/artiklar/dottrarna-som-runstenarna-glomde"

# ---- litteraturen: varje citat kontrolleras mot originalsidan ------------------------------------------------------
LIT = sqlite3.connect("file:" + "/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite?mode=ro", uri=True)
_flat = lambda t: re.sub("[\\s\u00ad]+", "", re.sub("-[ \\t]*\\n\\s*", "", t)).lower()  # noqa: E731  (radbrytningens bindestreck och mjuka bindestreck bort)


def lit(key, page, printed, *phrases):
    """Fraserna står på sidan (index `page` i registret, tryckt sidnummer `printed`)."""
    row = LIT.execute("select text from pages where key=? and page=?", (key, page)).fetchone()
    assert row, (key, page)
    if printed is not None:
        assert str(printed) in row[0], (key, page, printed)
    for p in phrases:
        assert _flat(p) in _flat(row[0]), (key, page, p)


OWE, SW, JAN, SVA, GUS, SO = ("futhark_7_137_1087631", "futhark_2_193_512981", "1958_241", "1970_301", "1976_096",
                              "futhark_3_89_616875")
lit(OWE, 5, 137, "Där hade den legat inmurad i en bakugn", "efter Åsa, sin dotter mycket god")
lit(OWE, 6, 138, "Wessén avböjer att", "ornamentik, och med honom överensstämmer Sven B. F. Jansson")
lit(OWE, 7, 139, "Den 13 augusti 2011 besökte jag stenmuseet",
    "ormhuvud i fågelperspektiv vilket återfinns ovanför runorna mu",
    "efter Åsa, sin dotter, en god mö",
    "Ög 239 visar att det fanns en skillnad mellan orden māʀ och dōttiʀ åtminstone under sen vikingatid",
    "Cecilia Ljung menar att skillnaden mellan ’mö’ och ’dotter’ handlar om juridisk status",
    "En mö, dvs. en ogift kvinna, tillhör sin", "Unga/Öga, sin dotter", "se Williams 1989 som översätter ordet med ’mö’")
lit(OWE, 8, 140, "biologiska familj (under faderns förmyndarskap) medan en dotter mycket väl kan vara gift",
    "Ljung i e-brev till artikelförfattaren", "Åsa var alltså ännu ogift när hon avled, kanske samtidigt med modern Gudlög",
    "Att øy ristas med enbart en u-runa", "frustin för Frøy", "Williams, Henrik. 1989")
lit(SW, 2, 194, "Sveriges runinskrifter translates flicka", "translates ungmö", "‘daughter’ is the earliest meaning",
    "died at such a tender age that she had not yet been given a name")
lit(SW, 6, 198, "‘Unga, their daughter’", "female byname Unga is found in Old Norse documents (Peterson 2007, 243")
lit(JAN, 13, 252, "runristade gravhällar", "Denna vackra, väl bevarade häll låg med ristningsytan nedåt",
    "N om kyrkans äldsta altarunderbyggnad", "några rester av ursprunglig färg hade bevarats")
lit(JAN, 14, 253, "Sigrid, ungmön, över sin fader", "flicka, (ren) mö")
lit(JAN, 15, 254, "flicka»", "brukats som personnamn; se U 861", "Resterna av denna gamla uppmålning", "mönja",
    "i den röda slingan ha åtminstone vissa runföljder varit svarta (sirijir)", "som samtliga voro så gotl som osynliga för blotta ögat")
lit(SVA, 3, 302)
lit(SVA, 5, 304)  # sidhuvudet på s. 303 är förvanskat i OCR:en ("'503"); sidan ligger mellan 302 och 304
lit(SVA, 4, None, "Gerlög som ungmö", "Men en enda flicka levde kvar", "dotter så länge, att hon fick arvingar")
lit(GUS, 4, 98, "lät resa den", "efter sin fader Kalv, sin broder Igull och sin", "moder Ragnvi.")  # två spalter i OCR:en
lit(SO, 12, 98, "mær ‘maiden, unmarried woman’")
URL = {k: v["url"] for k, v in json.load(open(os.path.join(ROOT, "data", "cache", "literature", "journals.json"),
                                               encoding="utf-8"))["articles"].items() if k in (OWE, SW, JAN, SVA, GUS, SO)}
assert len(URL) == 6, URL

# ---- bilderna -------------------------------------------------------------------------------------------------------
LARS = "Sankt Lars kyrka i Linköping, den 26 april 2007, bild 2.jpg"   # fotograf Harri Blomberg enligt filsidan
BJORK = "Upplands runinskrifter 169.png"
DYNNA = "Dynnasteinen - black white simple.jpg"
INFO = commons.commons_info([LARS, BJORK, DYNNA])
assert INFO[LARS]["licence"] == "CC BY-SA 3.0" and INFO[BJORK]["licence"] == "CC0" and INFO[DYNNA]["licence"] == "CC BY-SA 4.0"
assert INFO[BJORK]["author"] == "Gillis Olsson" and INFO[DYNNA]["author"] == "Kulturhistorisk museum, Oslo"
LIC = {"CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0", "CC0": "https://creativecommons.org/publicdomain/zero/1.0",
       "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0"}


def pic(f, alt, text, who, lang):
    i = INFO[f]
    return f"![{alt}]({i['thumb']})\n{text} {'Foto' if lang == 'sv' else 'Photo'}: {who}, [{i['licence']}]({LIC[i['licence']]}), via [Wikimedia Commons]({i['page']})."


title = "Mö, dotter eller flicka? Ordet som kunde betyda ogift"
summary = ("Ordet mö står på bara sju svenska minnesmärken från vikingatiden, och forskarna har översatt det med flicka, "
           "ungmö, mö och dotter – eller inte sett det alls. Vi räknade dem, läste om dem och följde forskningen till en "
           "gravhäll i Skänninge där samma kvinna kallas både dotter och mö. Där syns vad ordet sa: att hon ännu inte var gift.")

body = f"""Den som läser en runsten i översättning läser alltid någon annans val. Oftast märks det inte. Men ibland hänger en hel människa på ett enda ord.

Sommaren 1913 revs ett hus vid ett gathörn i Skänninge. I bakugnen låg en gravhäll av kalksten med runor, Ög 239. En man som hette Gunnar hade lagt den efter två kvinnor:

> *[G]unnarr lagði stæin þenna æftiR Guðlaug, kunu si[n]a goða, ok æftiR Asu, dottur sina, møy goða.*

Gunnar lade denna sten efter Gudlög, sin goda hustru, och efter Åsa, sin dotter, en god mö.

Så har det inte alltid stått. Erik Brate, som gav ut hällen 1918, läste de två runorna *mu* som en förkortning för *mycket*: Åsa var en mycket god dotter. Elias Wessén och Sven B. F. Jansson såg inga runor där alls, bara ornamentik. Först Jan Owe, som granskade hällen 2011, läste *mu* som ordet *møy*, mö, och drog slutsatsen att Åsa var ogift när hon dog (Futhark 7, 2016). Två runor avgjorde om hon var en dotter som fick beröm eller en kvinna som aldrig hann gifta sig.

Det här är en artikel om det ordet. Det är sällsynt, och det har översatts på fler sätt än nästan något annat ord på stenarna.

:::box Kort sagt
- Ordet för mö, runsvenskans *mær* (böjt *møy*), står på {len(MAER_STONES)} av de {sp(len(V_SE_STONES))} vikingatida svenska runstenarna och på {len(MAER_OTHER)} andra minnesmärken. Ordet dotter står på {len(DOT_STONES)} runstenar.
- Forskarna har översatt det med flicka, ungmö, mö och dotter – och ibland inte sett det alls.
- Där ordet står bredvid dotter, på Åsas häll i Skänninge och på Dynnastenen i Norge, säger det något mer än släktbandet: att kvinnan ännu inte var gift.
- Hur gammal hon var säger ordet inte. Det gör översättningen flicka.
:::

## Sju minnesmärken

Vi gick igenom alla vikingatida inskrifter i Samnordisk runtextdatabas där ordet står i någon form. I Sverige är de {SV_ORD[N_ALL]}. {SV_ORD[len(MAER_STONES)].capitalize()} är runstenar. {SV_ORD[len(MAER_OTHER)].capitalize()} är andra minnesmärken: två gravhällar i Östergötland och en ristning i en berghäll i Uppland. Vi håller isär dem, som vi alltid gör, eftersom en gravhäll i en kyrka och en sten vid en väg är olika slags monument. Men ordet är detsamma.

Som jämförelse står ordet dotter på {len(DOT_STONES)} vikingatida svenska runstenar. Mö är alltså inte det vanliga ordet för en dotter. Det är ett ord som någon valde ibland, och då hade valet en mening.

Det här är de sju:

- **Björkeby i Östra Ryd, Uppland (U 169), runsten.** Holmsten i Rjóðr och Orm… reste stenen efter Frösten, sin son, *ok æftiR uku, møy sina* – och efter *uku*, sin mö. Vad *uku* är återkommer vi till.
- **Söderby i Orkesta, Uppland (U 341), runsten.** Ingjald(?) reste den efter sin far Kalv, sin bror Igul och *Ragnvi, moður/møy sina* – Ragnvi, sin mor eller sin mö. Läsningen är osäker.
- **Över-Järva i Solna, Uppland (U 126), runsten.** Forkunn ber att Gud och *Guðs maR goð*, Guds goda mö, ska hjälpa de dödas ande. Mön är jungfru Maria.
- **Norsta i Balingsta, Uppland (U 861), runsten.** Här är ordet ett namn: Sigtorn lät resa stenen och göra bron efter sonen Ådjärv *ok at Møy, dottur sina* – och efter Mö, sin dotter.
- **Skänninge, Östergötland (Ög 239), gravhäll.** Åsa, *dottur sina, møy goða*.
- **Sankt Lars kyrka i Linköping (Ög Fv1958;252), gravhäll.** *Sigriðr, maR* – Sigrid, mön, låter göra minnesmärket över sin far tillsammans med sin mor.
- **Hillersjö i Hilleshög, Uppland (U 29), berghäll.** Släktberättelsen: Gerlög gifte sig *møydomi i*, i sin mödom, och av barnen *maR æin lifði*, en mö levde.

Ordet gäller alltså en gång Guds moder, en gång ett namn och fem gånger en kvinna i familjen. På en av de fem är läsningen osäker.

Sökningen i de digitaliserade årgångarna av Fornvännen och Futhark gjordes med hjälp av Anthropics språkmodell Claude (Claude Opus). Allt vi citerar nedan har vi själva kontrollerat mot originalsidorna.

## Ett ord, fem översättningar

Det märkliga är inte att ordet är ovanligt. Det är hur olika det har översatts.

- **Flicka.** I *Upplands runinskrifter* blev Hillersjöhällens mö en *flicka* (enligt Stroh-Wollin, Futhark 2), och Sven B. F. Jansson återgav slutet på Björkebystenen som *efter sin unga flicka* (Fornvännen 1958).
- **Ungmö.** Jansson om Sigrid i Linköping: *Sigrid, ungmön, över sin fader* (1958). Elisabeth Svärdström om Gerlög på Hillersjö: *Germund fick till hustru Gerlög som ungmö* (Fornvännen 1970).
- **Mö.** Owe om Åsa: *en god mö* (2016). Henrik Williams om Guds mö på U 126 (1989, så som Owe återger honom).
- **Dotter.** Staffan Fridell har hävdat att ordets äldsta betydelse är just dotter (2008, så som Stroh-Wollin och Owe återger honom). Ulla Stroh-Wollin översätter Björkebystenen *Unga, their daughter* (2012).
- **Maid, maiden.** Samnordisk runtextdatabas på engelska.

Och så de gånger ordet inte syntes. Brate läste Åsas *mu* som *mycket*. Wessén och Jansson såg ornamentik. På Söderby läste Helmer Gustavson *sin moder Ragnvi* (Fornvännen 1976).

Ingen av översättningarna är fel i sig. Men de säger olika saker till en läsare i dag. *Flicka* låter som ett barn. *Dotter* säger bara vems hon var. *Mö* och *ungmö* säger att hon var ogift, men orden är så gamla att få använder dem. Spänningen syns hos Wessén själv. I översättningen av Hillersjöhällen är Inga en flicka. I hans kommentar till samma inskrift är hon en dotter: *av dessa levde endast en dotter så länge, att hon fick arvingar* (citerad av Svärdström 1970).

## Åsa i Skänninge – dotter och mö

Det är Åsas häll som visar vad ordet betydde. Där står båda orden om samma kvinna: *dottur sina, møy goða*. Om mö bara betydde dotter hade Gunnar sagt samma sak två gånger. Owe drar slutsatsen att hällen ”visar att det fanns en skillnad mellan orden māʀ och dōttiʀ åtminstone under sen vikingatid”.

Vilken skillnad? Owe återger runologen Cecilia Ljungs svar, i ett brev till honom: skillnaden gällde den rättsliga ställningen. ”En mö, dvs. en ogift kvinna, tillhör sin biologiska familj (under faderns förmyndarskap) medan en dotter mycket väl kan vara gift och således ingå i en ny familj.” Och om Åsa: ”Åsa var alltså ännu ogift när hon avled, kanske samtidigt med modern Gudlög.”

Dotter säger vems hon var. Mö säger var i livet hon stod.

Det närmaste vi har i vårt eget språk är kanske *fröken*, som länge betydde just ogift kvinna, i vilken ålder som helst. En gravsten med orden ”sin dotter, en god fröken” låter konstig i dag. Men den säger två saker, och båda var viktiga för den som lät hugga den: att Åsa var hans, och att hon dog innan hon blev någon annans hustru.

## Sigrid i Linköping – mön som lät göra stenen

I Sankt Lars kyrka i Linköping låg en annan häll med ristningen nedåt, intill kyrkans äldsta altare. Den hittades vid restaureringen på 1950-talet och gavs ut av Sven B. F. Jansson 1958 (Ög Fv1958;252):

> *GæiRa let gærva kumbl þessa yfiR Þorð, bonda sinn, ok Sigriðr, maR, yfiR sinn faður. Guð hialpi sial hans.*

Geira lät göra detta minnesmärke över Tord, sin make, och Sigrid, mön, över sin far. Gud hjälpe hans själ.

{pic(LARS, 'Gravhällen Ög Fv1958;252 i Sankt Lars kyrka', 'Ög Fv1958;252 i Sankt Lars kyrka i Linköping: Geira och mön Sigrid lät göra minnesmärket över Tord.', 'Harri Blomberg', 'sv')}

Här är mön inte den döda. Hon är en av dem som låter göra minnesmärket, bredvid sin mor. Modern står där som hustru – Tord är *bonda sinn*, hennes make – och dottern som mö. Två kvinnor i två olika ställningar, kring en död man.

Hällen var målad. Vid undersökningen fann man färgspår som var så gott som osynliga för blotta ögat. Den slinga där inskriften börjar hade varit svart, den andra röd av mönja, och i den röda slingan hade Sigrids namn varit målat svart (Fornvännen 1958, s. 254). Jansson förklarade ordet *maR* med isländskans *mær*, ”flicka, (ren) mö”. En ren mö är en jungfru.

## Den namnlösa dottern på Björkeby

På Björkeby i Östra Ryd står en sten efter två barn. Runorna slutar *uk + iftiR × uku + my sina*. I *Upplands runinskrifter* lästes *uku* som adjektivet *ungu*, unga: efter sin unga flicka. Då har sonen ett namn och dottern inget.

{pic(BJORK, 'Runstenen U 169 vid Björkeby', 'U 169 vid Björkeby i Östra Ryd, Uppland, fotograferad 1940.', 'Gillis Olsson', 'sv')}

Ulla Stroh-Wollin frågade 2012 varför. Det enda goda skäl hon kunde tänka sig var att flickan ”died at such a tender age that she had not yet been given a name” – dog så liten att hon ännu inte fått något namn. Men hennes svar är språkligt. Ordföljden och böjningen i *ungu møy sina* passar inte vikingatidens språk, och *uku* är därför troligen ett namn, Unga eller Öga. Som binamn finns Unga i fornnordiska källor (Stroh-Wollin, med hänvisning till Lena Petersons *Nordiskt runnamnslexikon*). Owe instämmer: ”Unga/Öga, sin dotter”. Rundata skriver i dag namnet som *uku*, utan att tolka det.

Här står mö där dotter brukar stå, direkt efter namnet. Skänninge och Björkeby drar åt var sitt håll, och båda kan stämma: ett ord kan peka ut en dotter och ändå säga mer om henne.

Vi måste också vara ärliga om oss själva. När vi skrev [Döttrarna som runstenarna glömde]({DOTTRAR_ART}) lät vi Björkebystenen vara utanför som en osäker läsning, eftersom databasens *their maid* också kunde vara en tjänsteflicka. Om Stroh-Wollin och Owe har rätt är den en runsten till efter en dotter.

Björkeby och Söderby (U 341) har en sak gemensam: Rundata tillskriver båda samma ristare, Gunnar. På Söderby står det *ragnui × mu sina* – Ragnvi, hans mor eller hans mö. Gustavson läste mor. Vi lägger ingen egen läsning till, men två saker står i runorna. På samma sten skrev ristaren ut ordet för mor helt, *muþiR*, i bönen till Guds moder. Och Owe påpekar att ljudet i *møy* kan ristas med bara en u-runa, som i Åsas *mu* och i *frustin* för Frösten.

## Inga på Hillersjö – mön före giftet

Hillersjöhällen (U 29) har vi berättat om förut. Men den har ordet två gånger, och båda gångerna handlar det om tiden före giftet. Gerlög gifte sig med Germund *møydomi i*, i sin mödom – ”som ungmö”. Av barnen med Gudrik levde *en mö*, Inga, och henne fick Ragnfast i Snottsta. Ordet följer Inga fram till bröllopet. När hon dör och modern ärver henne är hon *Ingu, dottur sinnaR*, Inga, sin dotter.

Så används orden här: mö om den ogifta, dotter om släktbandet, som håller hela livet.

## Norge: den händigaste mön på Hadeland

Utanför Sverige står ordet på en enda vikingatida runsten, och den är norsk. Bland Norges {len(NO)} vikingatida runstenar är det Dynnastenen på Hadeland (N 68), från omkring 1025–1050. Bland Danmarks {len(DK)} står ordet inte på någon.

> *{N68}*

Gunnvor, Trydriks dotter, gjorde bron efter Astrid, sin dotter. Hon var den händigaste mö på Hadeland.

{pic(DYNNA, 'Dynnastenen, N 68', 'N 68, Dynnastenen från Gran på Hadeland, i dag i Kulturhistorisk museum i Oslo.', 'Kulturhistorisk museum, Oslo', 'sv')}

Det är samma mönster som i Skänninge: dotter i släktformeln, mö i berömmet. Och berömmet säger något om åldern. Det är svårt att tänka sig att någon kallas den händigaste i hela sin bygd för det hon gjorde som barn. Astrid var troligen vuxen, och om Owe och Ljung har rätt om ordet var hon ogift. Här skulle *flicka* leda en läsare fel.

## Från gården till kyrkan

Redan under vikingatiden fick ordet en ny bärare. På Över-Järva i Solna (U 126) är *Guðs maR goð*, Guds goda mö, jungfru Maria. I medeltidens kyrkor fortsätter det, och här rör det sig om andra föremål än runstenar, som vi håller för sig. På en kyrkdörr i Mästerby på Gotland (G 191, från andra hälften av 1200-talet eller början av 1300-talet) står *MøyaR, hafin iðra bøn retta* – mör, läs era böner rätt. I putsen i Lye kyrka (G 104A, 1400-talet) kallas Maria *fru Maria møyu*. Och på ett dörrbeslag från Götlunda kyrka i Västergötland (Vg 204, omkring 1200) står ett nytt ord: *Iungfru eR min ro*, jungfrun är min ro.

I kyrkans språk blev mön en jungfru.

## Så säkra är vi

:::box Så säkra är vi
- **En räkning, ingen prövning.** Vi har räknat och läst, inte prövat något mot slumpen. Sju inskrifter räcker inte till en sådan prövning, och det vi säger här behöver ingen.
- **Normaliseringen är redan en tolkning.** När vi söker på *mær* och *møy* söker vi i Rundatas tolkning av runorna, inte i runorna själva. En mö som ingen ännu har läst ut – som Åsas *mu* före Owe – hittar vi inte. Det kan finnas fler.
- **Åldern står aldrig på stenen.** Att mö betydde ogift bygger på Åsas häll, på Hillersjöhällen och på Owes och Ljungs läsning, inte på någon uppgift om ålder. Dottern på Björkeby kan ha varit ett barn.
- **Några källor har vi bara i andra hand.** Fridell (2008), Ljungs brev, Wessén (1940), Brate (1918) och Williams (1989) har vi läst så som Stroh-Wollin, Owe och Svärdström återger dem, och det står vid varje citat. Allt annat har vi kontrollerat mot originalsidan.
- **Bara runstenar i siffrorna.** Talen {len(MAER_STONES)} av {sp(len(V_SE_STONES))} och {len(DOT_STONES)} gäller runstenar, också förlorade och fragment. Gravhällarna och berghällen är nämnda för sig. På två av de {len(DOT_STONES)} stenarna med dotter är läsningen osäker.
:::

:::box Det viktigaste i korthet
- Mö och dotter var inte samma ord. Dotter sa vems hon var; mö sa att hon ännu inte var gift.
- Därför kan översättningen flicka leda fel. Den gör en ogift kvinna till ett barn, och åldern står aldrig på stenen.
- Ordet är så sällsynt – sju svenska minnesmärken – att nästan varje forskare har fått översätta det på egen hand. Skillnaderna visar hur mycket som kan hänga på ett enda ord.
- Det tog ett sekel och en ny granskning av två runor innan Åsa i Skänninge fick tillbaka ordet som sa att hon dog ogift.
:::

## Se själv

Åsas häll låg i stenmuseet vid Sankta Ingrids kloster i Skänninge när Owe granskade den 2011. Den som letar på hällen hittar ett litet ormhuvud, sett ovanifrån. Det sitter ovanför de två runorna *mu* och visar, enligt Owe, var läsningen börjar.

Och nästa gång du läser *flicka* i en översättning av en runtext: slå upp stenen i Samnordisk runtextdatabas och se vilket ord som står där.

Om döttrarna på runstenarna: [Döttrarna som runstenarna glömde]({DOTTRAR_ART}). Vitki är ett öppet verktyg för runstensforskning som du kan ladda ner från [GitHub](https://github.com/Precatio/runes).

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Gustavson, Helmer 1976. ”Runfynd 1975.” *Fornvännen* 71, s. 96–109 (U 341 s. 98). [Fri fulltext]({URL[GUS]})
- Jansson, Sven B. F. 1958. ”Runstensfynd i kyrkmurar.” *Fornvännen* 53, s. 241–257 (Ög Fv1958;252 s. 252–254). [Fri fulltext]({URL[JAN]})
- Owe, Jan 2016. ”Åsa, en mö i Skänninge (Ög 239).” *Futhark* 7 (2016, utg. 2017), s. 137–141. [Fri fulltext]({URL[OWE]})
- Steenholt Olesen, Rikke 2013. ”Runes about a Snow-White Woman: The Lund Gaming-Piece Revisited.” *Futhark* 3 (2012), s. 89–104 (om *mær* som ’maiden, unmarried woman’ s. 98). [Fri fulltext]({URL[SO]})
- Stroh-Wollin, Ulla 2012. ”U 169 Björkeby: A Daughter without a Name?” *Futhark* 2 (2011), s. 193–200. [Fri fulltext]({URL[SW]})
- Svärdström, Elisabeth 1970. ”Runfynd 1969.” *Fornvännen* 65 (U 29 och Wesséns kommentar s. 303). [Fri fulltext]({URL[SVA]})
- Lästa i andra hand, så som de återges ovan: Brate, Erik 1911–18, *Östergötlands runinskrifter* (SRI 2); Fridell, Staffan 2008, ”Möjbro”, *Ortnamnssällskapets i Uppsala årsskrift* 2008, s. 43–49; Ljung, Cecilia 2004, ”’Henne fick Ragnfast i Snottsta till hustru’”, i *Kystkultur*, s. 75–84; Peterson, Lena 2007, *Nordiskt runnamnslexikon*, 5 uppl., Uppsala; Wessén, Elias & Jansson, Sven B. F. 1940–58, *Upplands runinskrifter* (SRI 6–9); Williams, Henrik 1989, ”Åsgisl och Guds moder?”, *Runrön* 1, s. 39–50.
- Bilder: Wikimedia Commons, med fotograf och licens i bildtexterna."""

title_en = "Maiden, daughter or girl? The runic word that could mean unmarried"
summary_en = ("The word for maiden appears on only seven Swedish memorials from the Viking Age, and scholars have translated "
              "it as girl, young maiden, maiden and daughter – or not seen it at all. We counted them, read them again and "
              "followed the research to a grave slab in Skänninge where the same woman is called both daughter and maiden. "
              "There it shows what the word said: that she was not yet married.")

body_en = f"""Anyone who reads a runestone in translation is reading someone else's choices. Usually it goes unnoticed. But sometimes a whole person hangs on a single word.

In the summer of 1913 a house on a street corner in Skänninge was pulled down. In its bread oven lay a limestone grave slab with runes, Ög 239. A man called Gunnarr had laid it in memory of two women:

> *[G]unnarr lagði stæin þenna æftiR Guðlaug, kunu si[n]a goða, ok æftiR Asu, dottur sina, møy goða.*

Gunnarr laid this stone in memory of Guðlaug, his good wife, and in memory of Ása, his daughter, a good maiden.

It has not always read like that. Erik Brate, who published the slab in 1918, read the two runes *mu* as an abbreviation for *very*: Ása was a very good daughter. Elias Wessén and Sven B. F. Jansson saw no runes there at all, only ornament. Only Jan Owe, who examined the slab in 2011, read *mu* as the word *møy*, maiden, and concluded that Ása was unmarried when she died (Futhark 7, 2016). Two runes decided whether she was a daughter being praised or a woman who never had time to marry.

This is an article about that word. It is rare, and it has been translated in more ways than almost any other word on the stones.

:::box In short
- The word for maiden, Runic Swedish *mær* (inflected *møy*), stands on {len(MAER_STONES)} of the {en(len(V_SE_STONES))} Viking-age Swedish runestones and on {len(MAER_OTHER)} other memorials. The word daughter stands on {len(DOT_STONES)} runestones.
- Scholars have translated it as girl, young maiden, maiden and daughter – and sometimes not seen it at all.
- Where the word stands next to daughter, on Ása's slab in Skänninge and on the Dynna stone in Norway, it says something beyond kinship: that the woman was not yet married.
- How old she was, the word does not say. The translation girl does.
:::

## Seven memorials

We went through every Viking-age inscription in the Scandinavian Runic-text Data Base where the word appears in any form. In Sweden there are {EN_ORD[N_ALL]}. {EN_ORD[len(MAER_STONES)].capitalize()} are runestones. {EN_ORD[len(MAER_OTHER)].capitalize()} are other memorials: two grave slabs in Östergötland and a carving on a rock face in Uppland. We keep them apart, as we always do, because a grave slab in a church and a stone by a road are different kinds of monument. But the word is the same.

For comparison, the word daughter stands on {len(DOT_STONES)} Viking-age Swedish runestones. So maiden is not the ordinary word for a daughter. It is a word someone chose now and then, and when they did, the choice meant something.

These are the seven:

- **Björkeby in Östra Ryd, Uppland (U 169), runestone.** Holmsteinn in Rjóðr and Orm-… raised the stone in memory of Freysteinn, their son, *ok æftiR uku, møy sina* – and in memory of *uku*, their maiden. We come back to what *uku* is.
- **Söderby in Orkesta, Uppland (U 341), runestone.** Ingjaldr(?) raised it in memory of his father Kalfr, his brother Ígull and *Ragnvi, moður/møy sina* – Ragnvé, his mother or his maiden. The reading is uncertain.
- **Över-Järva in Solna, Uppland (U 126), runestone.** Forkunnr prays that God and *Guðs maR goð*, God's good maiden, will help the spirits of the dead. The maiden is the Virgin Mary.
- **Norsta in Balingsta, Uppland (U 861), runestone.** Here the word is a name: Sigþorn had the stone raised and the bridge made in memory of his son Ádjarfr *ok at Møy, dottur sina* – and in memory of Mey, his daughter.
- **Skänninge, Östergötland (Ög 239), grave slab.** Ása, *dottur sina, møy goða*.
- **St Lars Church in Linköping (Ög Fv1958;252), grave slab.** *Sigriðr, maR* – Sigríðr, the maiden, has the monument made over her father together with her mother.
- **Hillersjö in Hilleshög, Uppland (U 29), rock face.** The family history: Geirlaug married *møydomi i*, in her maidenhood, and of the children *maR æin lifði*, one maiden lived.

So the word refers once to the mother of God, once to a name and five times to a woman in the family. On one of the five the reading is uncertain.

The search of the digitised volumes of Fornvännen and Futhark was made with the help of Anthropic's language model Claude (Claude Opus). Everything we quote below we have checked ourselves against the original pages.

## One word, five translations

What is striking is not that the word is rare. It is how differently it has been translated.

- **Girl.** In *Upplands runinskrifter* the maiden of the Hillersjö rock became a *flicka*, a girl (according to Stroh-Wollin, Futhark 2), and Sven B. F. Jansson rendered the end of the Björkeby stone as *efter sin unga flicka*, in memory of their young girl (Fornvännen 1958).
- **Young maiden.** Jansson on Sigríðr in Linköping: *Sigrid, ungmön, över sin fader*, Sigríðr, the young maiden, over her father (1958). Elisabeth Svärdström on Geirlaug at Hillersjö: Geirmundr took Geirlaug to wife *som ungmö*, as a young maiden (Fornvännen 1970).
- **Maiden.** Owe on Ása: *en god mö*, a good maiden (2016). Henrik Williams on God's maiden on U 126 (1989, as Owe reports him).
- **Daughter.** Staffan Fridell has argued that the oldest meaning of the word is precisely daughter (2008, as Stroh-Wollin and Owe report him). Ulla Stroh-Wollin translates the Björkeby stone *Unga, their daughter* (2012).
- **Maid, maiden.** The Scandinavian Runic-text Data Base in English.

And then the times the word was not seen. Brate read Ása's *mu* as *very*. Wessén and Jansson saw ornament. At Söderby Helmer Gustavson read *sin moder Ragnvi*, his mother Ragnvé (Fornvännen 1976).

None of these translations is wrong in itself. But they tell a reader today different things. *Girl* sounds like a child. *Daughter* only says whose she was. *Maiden* and *young maiden* say that she was unmarried, but the words are so old that few people use them. The tension shows in Wessén himself. In the translation of the Hillersjö rock, Inga is a girl. In his commentary on the same inscription she is a daughter: of the children *only one daughter lived long enough to have heirs* (quoted by Svärdström 1970).

## Ása in Skänninge – daughter and maiden

It is Ása's slab that shows what the word meant. Both words stand there about the same woman: *dottur sina, møy goða*. If maiden only meant daughter, Gunnarr would have said the same thing twice. Owe concludes that the slab "shows that there was a difference between the words māʀ and dōttiʀ, at least in the late Viking Age".

What difference? Owe reports the runologist Cecilia Ljung's answer, in a letter to him: the difference concerned legal status. "A maiden, that is an unmarried woman, belongs to her biological family (under her father's guardianship), whereas a daughter may very well be married and so belong to a new family." And of Ása: "So Ása was still unmarried when she died, perhaps at the same time as her mother Guðlaug."

Daughter says whose she was. Maiden says where in life she stood.

The closest we have in English is perhaps *Miss*, which for a long time meant just that: an unmarried woman, of any age. A gravestone reading "his daughter, a good Miss" sounds odd today. But it says two things, and both mattered to the man who had it carved: that Ása was his, and that she died before she became anyone's wife.

## Sigríðr in Linköping – the maiden who had the stone made

In St Lars Church in Linköping another slab lay face down, next to the church's oldest altar. It was found during the restoration in the 1950s and published by Sven B. F. Jansson in 1958 (Ög Fv1958;252):

> *GæiRa let gærva kumbl þessa yfiR Þorð, bonda sinn, ok Sigriðr, maR, yfiR sinn faður. Guð hialpi sial hans.*

Geira had this monument made over Þórðr, her husband, and Sigríðr, the maiden, over her father. May God help his soul.

{pic(LARS, 'The grave slab Ög Fv1958;252 in St Lars Church', 'Ög Fv1958;252 in St Lars Church, Linköping: Geira and the maiden Sigríðr had the monument made over Þórðr.', 'Harri Blomberg', 'en')}

Here the maiden is not the dead. She is one of those who have the monument made, beside her mother. The mother stands there as a wife – Þórðr is *bonda sinn*, her husband – and the daughter as a maiden. Two women in two different positions, around a dead man.

The slab was painted. The examination found traces of colour that were all but invisible to the naked eye. The band where the inscription begins had been black, the other red with red lead, and in the red band Sigríðr's name had been painted black (Fornvännen 1958, p. 254). Jansson explained the word *maR* by Icelandic *mær*, "girl, (pure) maiden". A pure maiden is a virgin.

## The nameless daughter at Björkeby

At Björkeby in Östra Ryd stands a stone in memory of two children. The runes end *uk + iftiR × uku + my sina*. In *Upplands runinskrifter*, *uku* was read as the adjective *ungu*, young: in memory of their young girl. Then the son has a name and the daughter none.

{pic(BJORK, 'The runestone U 169 at Björkeby', 'U 169 at Björkeby in Östra Ryd, Uppland, photographed in 1940.', 'Gillis Olsson', 'en')}

Ulla Stroh-Wollin asked why in 2012. The only good reason she could think of was that the girl "died at such a tender age that she had not yet been given a name". But her answer is linguistic. The word order and the inflection of *ungu møy sina* do not fit the language of the Viking Age, so *uku* is probably a name, Unga or Ǿga. As a byname, Unga occurs in Old Norse sources (Stroh-Wollin, citing Lena Peterson's *Nordiskt runnamnslexikon*). Owe agrees: "Unga/Ǿga, their daughter". The database now writes the name as *uku*, without interpreting it.

Here maiden stands where daughter usually stands, straight after the name. Skänninge and Björkeby pull in different directions, and both may be right: a word can point out a daughter and still say more about her.

We must also be honest about ourselves. When we wrote [The daughters the runestones forgot](/en{DOTTRAR_ART}) we left the Björkeby stone out as an uncertain reading, because the database's *their maid* could also be a servant girl. If Stroh-Wollin and Owe are right, it is one more runestone for a daughter.

Björkeby and Söderby (U 341) have one thing in common: the database attributes both to the same carver, Gunnarr. At Söderby the runes read *ragnui × mu sina* – Ragnvé, his mother or his maiden. Gustavson read mother. We add no reading of our own, but two things stand in the runes. On the same stone the carver wrote the word for mother out in full, *muþiR*, in the prayer to the mother of God. And Owe points out that the sound in *møy* can be carved with a single u-rune, as in Ása's *mu* and in *frustin* for Freysteinn.

## Inga at Hillersjö – the maiden before the wedding

We have told the story of the Hillersjö rock (U 29) before. But it has the word twice, and both times it is about the time before marriage. Geirlaug married Geirmundr *møydomi i*, in her maidenhood – "as a young maiden". Of the children with Guðríkr *one maiden* lived, Inga, and Ragnfastr of Snottsta took her to wife. The word follows Inga up to the wedding. When she dies and her mother inherits from her, she is *Ingu, dottur sinnaR*, Inga, her daughter.

That is how the words are used here: maiden for the unmarried woman, daughter for the bond of kinship, which lasts all one's life.

## Norway: the handiest maiden in Hadeland

Outside Sweden the word stands on a single Viking-age runestone, and it is Norwegian. Of Norway's {len(NO)} Viking-age runestones it is the Dynna stone in Hadeland (N 68), from around 1025–1050. Of Denmark's {len(DK)} it stands on none.

> *{N68}*

Gunnvôr, Þryðríkr's daughter, made the bridge in memory of her daughter Ástríðr. She was the handiest maiden in Hadeland.

{pic(DYNNA, 'The Dynna stone, N 68', 'N 68, the Dynna stone from Gran in Hadeland, now in the Museum of Cultural History in Oslo.', 'Kulturhistorisk museum, Oslo', 'en')}

It is the same pattern as in Skänninge: daughter in the kinship formula, maiden in the praise. And the praise says something about age. It is hard to imagine anyone being called the handiest in a whole district for what she did as a child. Ástríðr was probably grown up, and if Owe and Ljung are right about the word, she was unmarried. Here *girl* would lead a reader astray.

## From the farm to the church

Already in the Viking Age the word found a new bearer. At Över-Järva in Solna (U 126), *Guðs maR goð*, God's good maiden, is the Virgin Mary. In the medieval churches it continues, and here we are dealing with objects other than runestones, which we keep apart. On a church door at Mästerby on Gotland (G 191, from the second half of the 1200s or the early 1300s) stands *MøyaR, hafin iðra bøn retta* – maidens, say your prayers rightly. In the plaster of Lye church (G 104A, 1400s) Mary is called *fru Maria møyu*, Lady Mary the maiden. And on a door mount from Götlunda church in Västergötland (Vg 204, around 1200) a new word appears: *Iungfru eR min ro*, the virgin is my peace.

In the language of the church, the maiden became a virgin.

## How sure we are

:::box How sure we are
- **A count, not a test.** We have counted and read, not tested anything against chance. Seven inscriptions are too few for such a test, and what we say here needs none.
- **The normalisation is already an interpretation.** When we search for *mær* and *møy* we search the database's interpretation of the runes, not the runes themselves. A maiden that no one has yet read out – like Ása's *mu* before Owe – we cannot find. There may be more.
- **Age is never on the stone.** That maiden meant unmarried rests on Ása's slab, on the Hillersjö rock and on Owe's and Ljung's reading, not on any statement of age. The daughter at Björkeby may have been a child.
- **Some sources we have only second-hand.** Fridell (2008), Ljung's letter, Wessén (1940), Brate (1918) and Williams (1989) we have read as Stroh-Wollin, Owe and Svärdström report them, and that is stated at each quotation. Everything else we have checked against the original page.
- **Only runestones in the figures.** The numbers {len(MAER_STONES)} of {en(len(V_SE_STONES))} and {len(DOT_STONES)} concern runestones, including lost ones and fragments. The grave slabs and the rock face are named separately. On two of the {len(DOT_STONES)} stones with daughter the reading is uncertain.
:::

:::box The essentials in brief
- Maiden and daughter were not the same word. Daughter said whose she was; maiden said that she was not yet married.
- That is why the translation girl can mislead. It turns an unmarried woman into a child, and age is never on the stone.
- The word is so rare – seven Swedish memorials – that nearly every scholar has had to translate it on their own. The differences show how much can hang on a single word.
- It took a century and a fresh look at two runes before Ása in Skänninge got back the word that said she died unmarried.
:::

## See for yourself

Ása's slab lay in the stone museum at St Ingrid's Priory in Skänninge when Owe examined it in 2011. Anyone who looks closely will find a small serpent's head, seen from above. It sits above the two runes *mu* and shows, according to Owe, where the reading begins.

And the next time you read *girl* in a translation of a runic text: look the stone up in the Scandinavian Runic-text Data Base and see which word stands there.

On the daughters on the runestones: [The daughters the runestones forgot](/en{DOTTRAR_ART}). Vitki is an open tool for runestone research that you can download from [GitHub](https://github.com/Precatio/runes).

## Sources

- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Gustavson, Helmer 1976. "Runfynd 1975." *Fornvännen* 71, pp. 96–109 (U 341 p. 98). [Free full text]({URL[GUS]})
- Jansson, Sven B. F. 1958. "Runstensfynd i kyrkmurar." *Fornvännen* 53, pp. 241–257 (Ög Fv1958;252 pp. 252–254). [Free full text]({URL[JAN]})
- Owe, Jan 2016. "Åsa, en mö i Skänninge (Ög 239)." *Futhark* 7 (2016, publ. 2017), pp. 137–141. [Free full text]({URL[OWE]})
- Steenholt Olesen, Rikke 2013. "Runes about a Snow-White Woman: The Lund Gaming-Piece Revisited." *Futhark* 3 (2012), pp. 89–104 (on *mær* as 'maiden, unmarried woman' p. 98). [Free full text]({URL[SO]})
- Stroh-Wollin, Ulla 2012. "U 169 Björkeby: A Daughter without a Name?" *Futhark* 2 (2011), pp. 193–200. [Free full text]({URL[SW]})
- Svärdström, Elisabeth 1970. "Runfynd 1969." *Fornvännen* 65 (U 29 and Wessén's commentary p. 303). [Free full text]({URL[SVA]})
- Read second-hand, as reported above: Brate, Erik 1911–18, *Östergötlands runinskrifter* (SRI 2); Fridell, Staffan 2008, "Möjbro", *Ortnamnssällskapets i Uppsala årsskrift* 2008, pp. 43–49; Ljung, Cecilia 2004, "'Henne fick Ragnfast i Snottsta till hustru'", in *Kystkultur*, pp. 75–84; Peterson, Lena 2007, *Nordiskt runnamnslexikon*, 5th ed., Uppsala; Wessén, Elias & Jansson, Sven B. F. 1940–58, *Upplands runinskrifter* (SRI 6–9); Williams, Henrik 1989, "Åsgisl och Guds moder?", *Runrön* 1, pp. 39–50.
- Images: Wikimedia Commons, with photographer and licence in the captions."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    assert "<uku>" not in b, "vinkelparenteser tolkas som HTML"
    assert not re.search(r"\bAI\b", b), "skriv modellens namn, inte AI"
assert "Det viktigaste i korthet" in body and "The essentials in brief" in body_en
assert body.index("Det viktigaste i korthet") < body.index("## Se själv") < body.index("## Källor")
assert "Anthropics språkmodell Claude" in body and "Anthropic's language model Claude" in body_en

out = {"slug": "mo-dotter-eller-flicka", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Kvinnor och barn", "Språk och stavning", "Tolkning"]}
from src import blog_labels  # noqa: E402  (Admin avvisar ogiltiga etiketter med 422; samma kontroll här)
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
path = os.path.join(ROOT, "utdata", "blogg", "mo_dotter.json")
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
                 "topic": "Kvinnor|mö", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
