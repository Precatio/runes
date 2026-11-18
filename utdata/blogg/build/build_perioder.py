"""Artikeln "Vendeltid, vikingatid, medeltid – fanns gränserna?" (sv + en). Vitkis egna delar: begreppen i Fornvännen
1906–2023 och de svenska runinskrifterna över tiden (låst plan analysplaner/2026-11-17-perioderna.md, sha b1d1ed08;
utdata/perioder/resultat.json), runstenarna efter 1066 (utdata/runform/resultat.json, D3), huggspårsanalysens
granskningsbilder av M 1 och Ög 240–241 (öppna skanningar, CC BY 4.0) och SRI:s fyndhistorik. Citaten kontrolleras mot
källornas text (sok.sqlite; lokala PDF:er i /Volumes/2TB/Antigrvity/Runes/downloads/period_lit/src/).
    ../../../.venv/bin/python build_perioder.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels, commons  # noqa: E402
from utdata.norge.citat import check, letters  # noqa: E402

P = json.load(open(os.path.join(ROOT, "utdata", "perioder", "resultat.json"), encoding="utf-8"))
assert P["sha"] == "b1d1ed08"
RF = json.load(open(os.path.join(ROOT, "utdata", "runform", "resultat.json"), encoding="utf-8"))
RD = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
FIG = json.load(open(os.path.join(ROOT, "utdata", "blogg", "build", "perioder_figurer.json"), encoding="utf-8"))
for v in FIG.values():
    assert re.match(r"/api/blog/figures/[0-9a-f]{16}\.png$", v) and os.path.exists(os.path.join(ROOT, "data", "blog", "figures", v.split("/")[-1])), v

# ---- the numbers ------------------------------------------------------------------------------------------------------
A = {int(k): v for k, v in P["P1"]["andel"].items()}
F1 = P["P1"]["forsta"]
assert F1["vendeltid"]["ar"] == 1908 and F1["vendeltid"]["key"] == "1908_201" and F1["vikingatid"]["ar"] == 1906
assert round(100 * A[1990]["vikingatid"], 1) == 14.5 and round(100 * A[1900]["vikingatid"], 1) == 3.1
assert round(100 * A[2000]["vendeltid"], 1) == 4.1 and round(100 * A[1900]["vendeltid"], 1) == 0.1
HS = {int(k): v for k, v in P["P2"]["per_halvsekel"].items()}
tot = lambda b: sum(HS.get(b, {}).values())  # noqa: E731
DATED = sum(tot(b) for b in HS)
assert (HS[1050]["sten"], HS[1100]["sten"], HS[1150]["sten"]) == (496, 66, 4)
assert P["P2"]["inskrifter"] == 3723
D3 = RF["D3"]
assert (D3["pr4_pr5"], D3["stenar_med_sakert_stil"], D3["pr3"]) == (299, 1038, 140)

# SRI and Rundata on Ög 240 (the find in Hov church's foundation, 1913)
assert RD["Ög 240"]["object"] == "fragment av gravhäll" and RD["Ög 240"]["place"] == "Hovs kyrka"
assert "laid this vault" in RD["Ög 240"]["translation_en"] and "God help" in RD["Ög 240"]["translation_en"]
assert "Farþegn marked" in RD["M 1"]["translation_en"]
from src import sri_fyndhistorik  # noqa: E402
_s = sri_fyndhistorik.for_inscription({"signum": "Ög 240"})
assert _s and _s["built_in"]
_SRI = re.sub(r"\s+", " ", open("/Volumes/2TB/Antigrvity/Runes/downloads/sri/sri_ostergotland_b02_h03_text.txt", encoding="utf-8", errors="replace").read())
for _f in ("upptäcktes vid kyrkans reparation 1913 och tillhöra enligt byggmästaren, som ledde reparationen, kyrkans ursprungliga grund",
           "inmurad i kyrkans västra gavelvägg på insidan vid golvet", "löpa efter stenens kant", "Mittytan visar slingor"):
    assert _f in _SRI, _f  # SRI II, s. 223 (Ög 240)

# ---- the literature ---------------------------------------------------------------------------------------------------
SOK = sqlite3.connect("/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite")


def jcheck(key, page, *frags):
    text = letters(SOK.execute("select text from pages where key=? and page=?", (key, page)).fetchone()[0])
    for f in frags:
        assert letters(f) in text, (key, page, f)


Q = {"olsen10": "Första gången ordet Vendeltid förekommer är så vitt jag vet i Axel Romdahls 1916 utgivna bok Gammal konst",
     "malmer": "Det är meningslöst att fråga vilket år renässansen började",
     "ambros": "icke med objektiva medel kan avgöra vad som är först eller sist",
     "aker11": "ungefär ett sekel tidigare än den traditionella dateringen av vikingatidens början",
     "hill": "seem to take little note of the rise of the Viking Age in 793",
     "holm": "farms reverted to forests, and old settlements were forsaken",
     "lageras": "inget direkt stöd för att nedgången från den äldre till den yngre järnåldern skulle ha orsakats av klimathändelsen år 536",
     "ros": "som anlagts omkring år 980",
     "thun": "Medeltidens födelse ca 800",
     "low": "burial grounds have generally been abandoned or moved to another location"}
jcheck("1981_008", 4, "Första gången ordet Vendeltid", "Axel Romdahls 1916")  # Olsén 1981, s. 10
jcheck("1981_008", 5, "infört denna periodbeteckning")                         # s. 11
jcheck("1981_008", 6, "Mot slutet av 1930-talet kan")                          # s. 12
jcheck("1981_008", 7, "bestående i norsk arkeologi")                           # s. 13
jcheck("1968_081", 3, "renässansen", "plus minus 50")                          # Malmer 1968, s. 82
jcheck("1968_051", 5, Q["ambros"])                                             # Ambrosiani 1968, s. 54
jcheck("futhark_8_7_1333693", 5, Q["aker11"])                                  # Åkerström 2019, s. 11
jcheck("33_2025_1", 166, Q["hill"])                                            # Hillerdal 2025, s. 166
jcheck("futhark_9-10_7_1383036", 7, Q["holm"])                                 # Holmberg m.fl. 2020, s. 13
jcheck("2013_263", 10, "inget direkt stöd för att", "klimathändelsen år 536", "efter digerdöden")  # Lagerås 2013, s. 271
jcheck("2002_161", 2, Q["ros"], "under Olof Eriksson Skötkonung")                                                # Ros 2002, s. 161
jcheck("1989_159", 2, Q["thun"])                                               # Thunmark-Nylén 1989, s. 159
jcheck("1981_008", 7, "införde Johannes Bröndsted 1934 termen", "1940, 1960", "Studier i norsk mero")  # Olsén s. 13
jcheck("2016_007", 3, "occupational layers from the", "c. 750")                # Edberg & Karlsson 2016, s. 8
LOW = "../period_lit/src/lowenborg_2012_jaah4.txt"
check(LOW, Q["low"], 13)
check(LOW, "Migration period 29", 13)
check(LOW, "Vendel period: 82", 13)
check("../period_lit/src/daly_2022_northern_emporium_ch9.txt", "winter AD 707-708", 10)
check("../period_lit/src/daly_2022_northern_emporium_ch9.txt", "earliest exact date for felling activity on the site can now", 16)
check("../period_lit/src/daly_2022_northern_emporium_ch9.txt", "be placed at winter AD 707-708", 16)  # tryckt s. 338

# ---- pictures ---------------------------------------------------------------------------------------------------------
INFO = json.load(open(os.path.join(ROOT, "utdata", "blogg", "build", "perioder_imgs.json"), encoding="utf-8"))
IMG = {}
for label, f in (("Vendel I", "Vendel I helmet.jpg"), ("Birka", "Birka Svarta jorden 1991.jpg"),
                 ("Sigtuna", "Sankt Olofs kyrkoruin september 2013 01.jpg")):
    d = INFO[f]
    assert re.match(r"(CC BY|CC0|Public domain)", d["licence"]), f
    IMG[label] = {**d, "signum": label}


def pic(label, lang, extra=""):
    img = IMG[label]
    alt = img["signum"]
    return f"![{alt}]({img['thumb']})\n{commons.caption(img, lang)}{(' ' + extra) if extra else ''}"


# The captions say what Vitki's analysis did (utdata/blogg/build/huggspar_bildtext.py), then whose scan it is
from utdata.blogg.build import huggspar_bildtext  # noqa: E402
_GR = {k: json.load(open(os.path.join(ROOT, "utdata", "skanningar_g5", d, f), encoding="utf-8"))
       for k, d, f in (("M 1", "medelpad", "M_1.json"), ("Ög 240", "gravmonument_og_sm", "Ög_240.json"))}
assert (_GR["M 1"]["counts"]["accepted"], _GR["Ög 240"]["counts"]["accepted"]) == (128, 1172)
SCAN_M1 = {"sv": ("Skanningen är gjord av Henrik Zedig, Länsstyrelsen Västra Götalands län, i forskningsprojektet Evighetsrunor: "
                  "Kitzler Åhfeldt, L. & Zedig, H. 2024, 3D-data Runstenar i Medelpad, Riksantikvarieämbetet, "
                  "[doi:10.5281/zenodo.14141222](https://doi.org/10.5281/zenodo.14141222), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)."),
           "en": ("Scanned by Henrik Zedig, County Administrative Board of Västra Götaland, in the research project Evighetsrunor: "
                  "Kitzler Åhfeldt, L. & Zedig, H. 2024, 3D-data Runstenar i Medelpad, Swedish National Heritage Board, "
                  "[doi:10.5281/zenodo.14141222](https://doi.org/10.5281/zenodo.14141222), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).")}
SCAN_OG = {"sv": ("Skanningen är gjord av Laila Kitzler Åhfeldt 2008 (ATOS II) i Cecilia Ljungs avhandlingsprojekt om tidigkristna "
                  "gravmonument: Kitzler Åhfeldt, L. 2025, 3D-data Tidigkristna gravmonument Östergötland och Småland, "
                  "[doi:10.5281/zenodo.17571537](https://doi.org/10.5281/zenodo.17571537), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)."),
           "en": ("Scanned by Laila Kitzler Åhfeldt in 2008 (ATOS II) in Cecilia Ljung's doctoral project on early Christian grave "
                  "monuments: Kitzler Åhfeldt, L. 2025, 3D-data Tidigkristna gravmonument Östergötland och Småland, "
                  "[doi:10.5281/zenodo.17571537](https://doi.org/10.5281/zenodo.17571537), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).")}
WHAT = {("M 1", "sv"): "huggspårsanalysen av M 1 i Nolby, Medelpad", ("M 1", "en"): "the groove analysis of M 1 at Nolby, Medelpad",
        ("Ög 240", "sv"): "huggspårsanalysen av gravhällen Ög 240–241 i Hovs kyrka, Östergötland",
        ("Ög 240", "en"): "the groove analysis of the grave slab Ög 240–241 in Hov church, Östergötland"}
CREDIT_M1 = {l: huggspar_bildtext.text(l, WHAT["M 1", l], _GR["M 1"], SCAN_M1[l]) for l in ("sv", "en")}
CREDIT_OG = {l: huggspar_bildtext.text(l, WHAT["Ög 240", l], _GR["Ög 240"], SCAN_OG[l]) for l in ("sv", "en")}
APP_OG = lambda lang: f"![{'Gravhällen Ög 240–241' if lang == 'sv' else 'The grave slab Ög 240–241'}]({FIG['Ög 240']})\n{CREDIT_OG[lang]}"  # noqa: E731
APP_M1 = lambda lang: f"![{'Runstenen M 1' if lang == 'sv' else 'The runestone M 1'}]({FIG['M 1']})\n{CREDIT_M1[lang]}"  # noqa: E731

f_sv = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
CHART_SV, CHART_EN = "Diagram: Vitki.", "Chart: Vitki."
DECS = sorted(A)


def chart_words(lang):
    sv = lang == "sv"
    out = [":::chart " + ("Andel av Fornvännens sidor som nämner vikingatid och vendeltid, per decennium" if sv
                          else "Share of Fornvännen's pages that mention the Viking Age and the Vendel Period, by decade")]
    for name_sv, name_en, term in (("Vikingatid", "Viking Age", "vikingatid"), ("Vendeltid", "Vendel Period", "vendeltid")):
        out.append("# " + (name_sv if sv else name_en))
        for d in DECS:
            v = 100 * A[d][term]
            hi = (term == "vikingatid" and d == 1990) or (term == "vendeltid" and d == 2000)
            out.append(f"{'+' if hi else ''}{d}{'-talet' if sv else 's'} | {v:.1f} | ")
    out.append(("Källa: Fornvännen 1906–2023 (Kungl. Vitterhets Historie och Antikvitets Akademien och Riksantikvarieämbetet, "
                "CC BY 4.0), sidornas text efter OCR; böjda former räknas. 2020-talet till och med april 2023. " + CHART_SV) if sv else
               ("Source: Fornvännen 1906–2023 (Royal Swedish Academy of Letters, History and Antiquities and the Swedish National "
                "Heritage Board, CC BY 4.0), page text after OCR; inflected forms counted. The 2020s up to April 2023. " + CHART_EN))
    return "\n".join(out) + "\n:::"


BINS = [b for b in range(900, 1551, 50)]


def chart_runes(lang):
    sv = lang == "sv"
    out = [":::chart " + ("De svenska runinskrifterna med årtal: andel per halvsekel, och vad de står på" if sv
                          else "The Swedish runic inscriptions with a date: share per half-century, and what they are on")]
    for b in BINS:
        h = HS.get(b, {})
        n = sum(h.values())
        if not n:
            continue
        note = (f"{h.get('sten', 0)} runstenar, {h.get('kyrka_grav', 0)} i kyrka eller på grav, {h.get('losa', 0)} lösa föremål" if sv
                else f"{h.get('sten', 0)} runestones, {h.get('kyrka_grav', 0)} in church or on graves, {h.get('losa', 0)} portable objects")
        lab = f"{b}–{b + 49}"
        out.append(f"{'+' if b in (1050, 1150) else ''}{lab} | {100 * n / DATED:.1f} | {note}")
    out.append((f"Källa: Samnordisk runtextdatabas (Rundata), de {f_sv(DATED)} svenska runinskrifter som har ett årtal "
                "(vikingatida runstenar efter stilgruppens mitt, medeltida efter Rundatas århundrade). Procent av dem. "
                "Diagram: Vitki, efter Rundata (ODbL).") if sv else
               (f"Source: Scandinavian Runic-text Database (Rundata), the {DATED:,} Swedish runic inscriptions that have a date "
                "(Viking-age runestones by the middle of their style group, medieval ones by Rundata's century). Percent of them. "
                "Chart: Vitki, after Rundata (ODbL)."))
    return "\n".join(out) + "\n:::"


SLUG = "vendeltid-vikingatid-medeltid-fanns-granserna"
title = "Vendeltid, vikingatid, medeltid – fanns gränserna?"
title_en = "Vendel Period, Viking Age, Middle Ages – were the boundaries real?"
summary = ("Vikingatiden började 793 och slutade 1066 – i England. I Skandinavien är gränserna senare tiders etiketter, och "
           "landet bytte inte tidsålder en viss dag. Vi följer begreppen i hundra år av Fornvännen, räknar när runorna "
           "flyttade från runstenen till kyrkan och graven, och tittar med huggspårsanalysen på en gravhäll som står mitt i "
           "skiftet.")
summary_en = ("The Viking Age began in 793 and ended in 1066 – in England. In Scandinavia the boundaries are later labels, and "
              "the land did not change age on a given day. We follow the terms through a hundred years of Fornvännen, count "
              "when the runes moved from the runestone to the church and the grave, and use groove analysis to look at a grave "
              "slab that stands right in the shift.")

body = f"""År 1913 reparerades Hovs kyrka i Östergötland. Inmurad i västra gaveln, nere vid golvet, hittade man en kalkhäll med runor längs kanterna och slingor i mittytan. *Ketill lade detta valv*, står det, och: *Gud hjälpe Tunnes själ*. Det är en del av ett tidigkristet gravmonument, och enligt byggmästaren hörde den till kyrkans ursprungliga grund.

Är den vikingatida eller medeltida? Rundata räknar den till vikingatiden. Den har runor som en runsten och en bön som många runstenar. Men den låg på en grav vid en kyrka, och det är ett medeltida sätt att minnas de döda.

{APP_OG("sv")}

Bilden kommer ur Vitkis huggspårsanalys. Skanningen visar hällens yta, och analysen har letat upp de ristade spåren och mätt dem i tvärsnitt. Uppgiften om fyndet 1913 står i *Sveriges runinskrifter*, som vi har läst sten för sten; den syns på stensidan i appen.

Hällen i Hov är en bra ingång till en fråga som sällan ställs: fanns vendeltiden, vikingatiden och medeltiden – eller är de etiketter som forskare har satt på en tid som inte bytte skepnad en viss dag?

## Etiketterna är yngre än man tror

Indelningen i tidsåldrar är en uppfinning från 1800-talet. Christian Jürgensen Thomsen gav ut sitt treperiodssystem – sten, brons, järn – 1837 (Nicklasson, Fornvännen 2017, s. 137). Oscar Montelius delade järnåldern i tre delar 1872 och i åtta perioder 1892–93. Då kallades hela tiden 400–800 folkvandringstid, och det vi i dag kallar vendeltid hette ”yngre folkvandringstid” (Pär Olsén, Fornvännen 1981, s. 8–10).

Ordet vendeltid kommer från båtgravarna vid Vendels kyrka i Uppland, som grävdes ut 1881–82. Olsén skrev 1981: ”{Q['olsen10']}” (s. 10). Som periodnamn infördes det av Nils Åberg 1922, och mot slutet av 1930-talet var det allmänt accepterat (s. 11–12). Men ordet är äldre än så. Jan Peder Lamm har visat att Oscar Almgren skrev om den äldre vendeltiden redan 1901 (Fornvännen 2001, s. 39), och när vi sökte i Fornvännens alla årgångar hittade vi det i Statens historiska museums förvärvslista för 1908, där ett fynd från Gotland är ”från Vendeltiden”.

{pic("Vendel I", "sv", "Hjälmen ur båtgrav I i Vendel, fyndplatsen som gav perioden dess namn.")}

Grannländerna valde andra namn för samma tid. I Danmark införde Johannes Brøndsted 1934 germansk järnålder för hela 400–800 och delade den 1940 i en äldre och en yngre del; i Norge infördes merovingertid samma år, 1934 (Olsén s. 13). Samma århundraden heter alltså olika saker beroende på vilken sida av gränsen arkeologen står.

Ordet vikingatid finns redan i Fornvännens första årgång 1906. Men det blev ett huvudord först sent. Vi har räknat hur stor andel av Fornvännens sidor som nämner orden, decennium för decennium.

{chart_words("sv")}

På 1900-talets första decennium nämner ungefär var trettionde sida vikingatiden. På 1990-talet gör var sjunde det. Vikingatiden blev ett huvudbegrepp i svensk arkeologi under seklets andra hälft. Mats P. Malmer påminde redan 1968 om vad sådana gränser är: ”{Q['malmer']}” – det räcker att säga ungefär när och var (Fornvännen 1968, s. 82).

## Var skiftena faktiskt syns

Om man släpper etiketterna och letar efter förändringar i det som finns kvar, framträder några skiften. De följer inte de vanliga årtalen.

**530–540-talen.** Vulkanutbrott gav kalla somrar. Vid mitten av 500-talet övergavs gårdar: ”{Q['holm']}”, skriver Per Holmberg och hans medförfattare (Futhark 9–10, 2020, s. 13). Daniel Löwenborg visar att bara 29 procent av gravfälten från folkvandringstiden fortsätter in i vendeltiden, mot 82 procent från vendeltid till vikingatid, även om han själv varnar för att siffrorna bara är en grov bild (2012, s. 13). Hur stor följden var är omstritt. Per Lagerås ser för det sydsvenska höglandet ”{Q['lageras']}” (Fornvännen 2013, s. 271); nedgången hade börjat långt tidigare.

**Omkring 700–750.** Här börjar något nytt – ett halvt sekel före Lindisfarne. Ribe på Jylland anlades omkring 705–710; det tidigaste exakta fällningsåret för timret är vintern 707–708 (Daly 2022, s. 338). Birka har lager från mitten av 700-talet till slutet av 900-talet (Edberg och Karlsson, Fornvännen 2016, s. 8). Runraden krympte från 24 till 16 tecken omkring år 700, och Hanna Åkerström låter därför den vikingatida runtraditionen börja ”{Q['aker11']}” (Futhark 8, 2019, s. 11). Charlotta Hillerdal skriver om Ribes invånare att de ”{Q['hill']}” (Current Swedish Archaeology 2025, s. 166). Gränsen mellan vendeltid och vikingatid är suddig också i föremålen: Björn Ambrosiani konstaterade 1968 att man om övergångstidens föremål ”{Q['ambros']}” (Fornvännen 1968, s. 54).

{pic("Birka", "sv", "Utgrävningen av Svarta jorden på Björkö 1991. Birka anlades vid mitten av 700-talet.")}

**Omkring 965–1000.** Harald Blåtand gjorde danerna kristna; Jellingstenen nämner Danmark omkring 965. I Sverige kom städer och mynt: de första svenska mynten präglades omkring 995 under Olof Skötkonung i Sigtuna, ”{Q['ros']}” (Jonas Ros, Fornvännen 2002, s. 161). Och runstenarna blev ett mode.

**Omkring 1100–1130.** Det här är det tydligaste skiftet i vårt eget material, och det ligger inte vid 1050 eller 1066.

## Runorna flyttar in i kyrkan

Vi har räknat alla svenska runinskrifter i Rundata som har ett årtal – de vikingatida runstenarna efter stilgruppens mitt, de medeltida efter Rundatas århundrade – och sorterat dem efter vad de står på.

{chart_runes("sv")}

Till andra hälften av 1000-talet daterar stilgrupperna {HS[1050]['sten']} runstenar i vårt material. Under första hälften av 1100-talet var det {HS[1100]['sten']}, och under andra hälften {HS[1150]['sten']}. Runorna försvann inte – de flyttade. Från 1100-talet står de på gravhällar och i kyrkor, på dopfuntar och kyrkklockor, och på lösa föremål som ben och träpinnar.

Det betyder också att runstensmodet levde länge efter den engelska slutpunkten. Av de svenska runstenar som har en säker stilgrupp hör {D3['pr4_pr5']} av {f_sv(D3['stenar_med_sakert_stil'])}, nästan var tredje, till stilgrupperna Pr4 och Pr5, som dateras till efter 1066. Ytterligare {D3['pr3']} hör till Pr3, som går över gränsen. Med 1066 som gräns skulle en stor del av det vi kallar vikingatida runstenar vara medeltida.

{APP_M1("sv")}

Runstenen från Nolby i Medelpad är en vanlig vikingatida minnessten: tre bröder reste den efter sin far, och ristaren skrev sitt namn, *Farþegn*. Jämför den med hällen i Hov. Tekniken är densamma, ristade spår i sten, men platsen är en annan: stenen stod i landskapet, hällen låg i kyrkan. Det är det skiftet som skiljer vikingatid från medeltid i Sverige – och det hände inte en viss dag, utan under några generationer kring 1100. Lena Thunmark-Nylén beskrev ett symposium om just detta, och dess tema var ”{Q['thun']}–1200” (Fornvännen 1989, s. 159).

{pic("Sigtuna", "sv", "S:t Olofs kyrkoruin i Sigtuna, en av stadens stenkyrkor från 1100-talet.")}

**Omkring 1350.** Efter digerdöden övergavs gårdar igen; Lagerås ser nedgången i pollenkurvorna (s. 271). Runristandet tunnas ut under 1300-talet, men på Gotland och i Dalarna levde runorna kvar mycket länge.

## En svensk vikingatid

Om man ska sätta gränser utifrån det som syns i Sverige, börjar vikingatiden snarare omkring 700–750 än 793, och den slutar snarare omkring 1100 än 1050 eller 1066. Gränserna är praktiska – de ordnar samlingar och läroböcker – men de är inte händelser. Löwenborgs siffror tyder på att de flesta gravfält användes vidare från vendeltid till vikingatid.

## Svagheterna

- **Ordräkningen är grov.** En sida som nämner vikingatid säger inget om hur ordet används, och OCR-felen i de äldre årgångarna gör att en del förekomster missas.
- **Årtalen är ungefärliga.** De vikingatida runstenarnas år är stilgruppernas mitt, och stilgrupperna är själva daterade delvis med hjälp av språket. De medeltida inskrifterna har ofta bara ett århundrade, och därför samlas många vid mitten av seklet i diagrammet.
- **Runstenar utan säker stilgrupp** – mer än hälften – saknar årtal och är inte med i diagrammet.
- **Lösa föremål** beror på var man har grävt: stadsgrävningar ger många runpinnar.
- **Skiftena är litteraturens,** med källor i texten. Vårt bidrag är räkningen av begreppen, inskrifterna över tiden och bilderna ur huggspårsanalysen.

:::box Det viktigaste i korthet
- Vendeltid, vikingatid och medeltid är etiketter från 1800- och 1900-talen. Ordet vendeltid användes redan 1901 och 1908, men blev periodnamn först på 1920-talet. Vikingatiden blev ett huvudord i svensk arkeologi först under 1900-talets andra hälft.
- Grannländerna använder andra namn och andra gränser för samma tid.
- De tydliga skiftena i Skandinavien ligger omkring 540, 700–750, 965–1000, 1100–1130 och 1350 – inte vid 793 och 1066.
- I vårt material slutar runstenarna kring 1100–1130, och runorna flyttar in i kyrkan och på gravarna. Nästan var tredje svensk runsten med säker stilgrupp är från tiden efter 1066.
:::

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Sveriges runinskrifter II, Östergötlands runinskrifter (Ög 240), via Vitkis fyndhistorik.
- Olsén, Pär 1981. Om ”vendeltidens” ålder och ursprung. *Fornvännen* 76, s. 8–15. CC BY 4.0.
- Lamm, Jan Peder 2001. Oscar Almgren och vendeltiden – en kronologihistorisk notis. *Fornvännen* 96, s. 39–40. CC BY 4.0.
- Nicklasson, Påvel 2017. Sven Nilsson och Ledetraaden, Christian Thomsen och Ur-invånarna. *Fornvännen* 112, s. 137–153. CC BY 4.0.
- Malmer, Mats P. 1968. De kronologiska grundbegreppen. *Fornvännen* 63, s. 81–91. CC BY 4.0.
- Ambrosiani, Björn 1968. Vendeltid eller vikingatid? *Fornvännen* 63, s. 51–55. CC BY 4.0.
- Holmberg, Per, Bo Gräslund, Olof Sundqvist och Henrik Williams 2020. The Rök Runestone and the End of the World. *Futhark* 9–10, s. 7–38. CC BY 4.0.
- Löwenborg, Daniel 2012. An Iron Age Shock Doctrine. *Journal of Archaeology and Ancient History* 4, s. 3–29. CC BY 4.0.
- Lagerås, Per 2013. Agrara fluktuationer och befolkningsutveckling på sydsvenska höglandet tolkade utifrån röjningsrösen. *Fornvännen* 108, s. 263–277. CC BY 4.0.
- Daly, Aoife 2022. Dendrochronology. Oak from Ribe. I S. M. Sindbæk (red.), *Northern Emporium* 1, s. 327–339. CC BY 4.0.
- Edberg, Rune och Johnny Karlsson 2016. Bone skates and young people in Birka and Sigtuna. *Fornvännen* 111, s. 7–16. CC BY 4.0.
- Åkerström, Hanna 2019. Det tidigvikingatida runmaterialet: En inventering. *Futhark* 8, s. 7–88. CC BY 4.0.
- Hillerdal, Charlotta 2025. Recension av *Northern Emporium* 1–2. *Current Swedish Archaeology* 33, s. 165–170. CC BY 4.0.
- Ros, Jonas 2002. Sigtuna och folklanden. *Fornvännen* 97, s. 161–175. CC BY 4.0.
- Thunmark-Nylén, Lena 1989. Medeltidens födelse – Krapperupssymposiet 1988. *Fornvännen* 84, s. 159. CC BY 4.0.
- Analysplanen (låst före räkningen) och koden finns öppet på [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-17-perioderna.md). Om runornas form: [Varför ser runorna ut som de gör?](/artiklar/varfor-ser-runorna-ut-som-de-gor)
- Foton: Wikimedia Commons, med fotograf och licens i bildtexterna. Huggspårsbilderna: Vitki, efter de öppna skanningarna som anges i bildtexterna."""

body_en = f"""In 1913 Hov church in Östergötland was being repaired. Built into the west gable, down by the floor, a limestone slab was found with runes along its edges and interlace in the central field. *Ketill laid this vault*, it says, and: *May God help Tunni's soul*. It is part of an early Christian grave monument, and according to the builder it belonged to the church's original foundation.

Is it Viking-age or medieval? Rundata counts it as Viking-age. It has runes like a runestone and a prayer like many runestones. But it lay on a grave by a church, and that is a medieval way of remembering the dead.

{APP_OG("en")}

The image comes from Vitki's groove analysis. The scan shows the slab's surface, and the analysis has found the carved grooves and measured them in cross-section. The record of the find in 1913 is in *Sveriges runinskrifter*, which we have read stone by stone; it shows on the stone's page in the app.

The slab at Hov is a good way into a question that is seldom asked: did the Vendel Period, the Viking Age and the Middle Ages exist – or are they labels that scholars have put on a time that did not change its shape on a particular day?

## The labels are younger than one thinks

Dividing the past into ages is a nineteenth-century invention. Christian Jürgensen Thomsen published his three-age system – stone, bronze, iron – in 1837 (Nicklasson, Fornvännen 2017, p. 137). Oscar Montelius divided the Iron Age into three parts in 1872 and into eight periods in 1892–93. At that point the whole span 400–800 was called the Migration Period, and what we now call the Vendel Period was the "later Migration Period" (Pär Olsén, Fornvännen 1981, pp. 8–10).

The word Vendel Period comes from the boat graves at Vendel church in Uppland, excavated in 1881–82. Olsén wrote in 1981 that, as far as he knew, the word first appears in the art historian Axel Romdahl's book *Gammal konst* of 1916 (p. 10). As a period name it was introduced by Nils Åberg in 1922, and by the end of the 1930s it was generally accepted (pp. 11–12). But the word is older than that. Jan Peder Lamm has shown that Oscar Almgren wrote of the earlier Vendel Period as early as 1901 (Fornvännen 2001, p. 39), and when we searched all the volumes of Fornvännen we found it in the Swedish History Museum's list of acquisitions for 1908, where a find from Gotland is "from the Vendel Period".

{pic("Vendel I", "en", "The helmet from boat grave I at Vendel, the site that gave the period its name.")}

The neighbouring countries chose other names for the same time. In Denmark Johannes Brøndsted introduced the Germanic Iron Age for all of 400–800 in 1934 and divided it into an Early and a Late part in 1940; in Norway the Merovingian Period was introduced the same year, 1934 (Olsén p. 13). The same centuries thus have different names depending on which side of the border the archaeologist stands.

The word Viking Age (*vikingatid*) is already in Fornvännen's first volume of 1906. But it became a key term only late. We have counted what share of Fornvännen's pages mention the words, decade by decade.

{chart_words("en")}

In the first decade of the twentieth century about one page in thirty mentions the Viking Age. In the 1990s one in seven does. The Viking Age became a key term in Swedish archaeology in the second half of the century. Mats P. Malmer reminded his readers in 1968 what such boundaries are: it is meaningless to ask in which year the Renaissance began – it is enough to say roughly when and where (Fornvännen 1968, p. 82).

## Where the shifts actually show

If one lets go of the labels and looks for changes in what remains, a few shifts appear. They do not follow the usual dates.

**The 530s–540s.** Volcanic eruptions brought cold summers. Around the middle of the sixth century farms were abandoned: “{Q['holm']}”, write Per Holmberg and his co-authors (Futhark 9–10, 2020, p. 13). Daniel Löwenborg shows that only 29 per cent of the burial grounds of the Migration Period continue into the Vendel Period, against 82 per cent from the Vendel Period into the Viking Age, though he warns himself that the figures are only a rough picture (2012, p. 13). How large the consequences were is debated. For the South Swedish uplands Per Lagerås finds no direct support in cairn dates and pollen for the decline being caused by the climate event of 536 (Fornvännen 2013, p. 271); the decline had begun much earlier.

**Around 700–750.** Here something new begins – half a century before Lindisfarne. Ribe in Jutland was founded around 705–710; the earliest exact felling year for its timber is the winter of 707–708 (Daly 2022, p. 338). Birka has layers from the middle of the eighth century to the end of the tenth (Edberg and Karlsson, Fornvännen 2016, p. 8). The rune row shrank from 24 to 16 signs around 700, and Hanna Åkerström therefore lets the Viking-age runic tradition begin about a century earlier than the traditional start of the Viking Age (Futhark 8, 2019, p. 11). Charlotta Hillerdal writes of Ribe's inhabitants that they “{Q['hill']}” (Current Swedish Archaeology 2025, p. 166). The boundary between the Vendel Period and the Viking Age is blurred in the objects too: Björn Ambrosiani noted in 1968 that the objects of the transition cannot by objective means be put in order (Fornvännen 1968, p. 54).

{pic("Birka", "en", "The excavation of the Black Earth on Björkö in 1991. Birka was founded in the middle of the eighth century.")}

**Around 965–1000.** Harald Bluetooth made the Danes Christian; the Jelling stone names Denmark around 965. In Sweden came towns and coins: the first Swedish coinage began around 995 under Olof Skötkonung in Sigtuna, which was founded around 980 (Jonas Ros, Fornvännen 2002, p. 161). And runestones became a fashion.

**Around 1100–1130.** This is the clearest shift in our own material, and it lies neither at 1050 nor at 1066.

## The runes move into the church

We have counted all the Swedish runic inscriptions in Rundata that have a date – the Viking-age runestones by the middle of their style group, the medieval ones by Rundata's century – and sorted them by what they are on.

{chart_runes("en")}

To the second half of the eleventh century the style groups date {HS[1050]['sten']} runestones in our material. In the first half of the twelfth century there were {HS[1100]['sten']}, and in the second half {HS[1150]['sten']}. The runes did not disappear – they moved. From the twelfth century they stand on grave slabs and in churches, on fonts and church bells, and on portable objects such as bone and wooden sticks.

It also means that the runestone fashion lived on long after the English end point. Of the Swedish runestones with a secure style group, {D3['pr4_pr5']} of {D3['stenar_med_sakert_stil']:,}, almost one in three, belong to the style groups Pr4 and Pr5, dated after 1066. Another {D3['pr3']} belong to Pr3, which straddles the line. With 1066 as the boundary, much of what we call Viking-age runestones would be medieval.

{APP_M1("en")}

The runestone from Nolby in Medelpad is an ordinary Viking-age memorial: three brothers raised it in memory of their father, and the carver signed his name, *Farþegn*. Compare it with the slab at Hov. The technique is the same, grooves carved in stone, but the place is different: the stone stood in the landscape, the slab lay in the church. That is the shift that separates the Viking Age from the Middle Ages in Sweden – and it did not happen on a given day, but over a few generations around 1100. Lena Thunmark-Nylén described a symposium on exactly this, and its theme was “the birth of the Middle Ages, c. 800–1200” (Fornvännen 1989, p. 159).

{pic("Sigtuna", "en", "The ruin of St Olof's church in Sigtuna, one of the town's twelfth-century stone churches.")}

**Around 1350.** After the Black Death farms were abandoned again; Lagerås sees the decline in the pollen curves (p. 271). Runic carving thins out in the fourteenth century, but on Gotland and in Dalarna the runes lived on for a very long time.

## A Swedish Viking Age

If one is to draw boundaries from what shows in Sweden, the Viking Age begins around 700–750 rather than 793, and ends around 1100 rather than 1050 or 1066. The boundaries are practical – they order collections and textbooks – but they are not events. Löwenborg's figures suggest that most burial grounds stayed in use from the Vendel Period into the Viking Age.

## The weaknesses

- **The word count is coarse.** A page that mentions the Viking Age says nothing about how the word is used, and the OCR errors in the older volumes mean some occurrences are missed.
- **The dates are approximate.** The Viking-age runestones' years are the middle of their style groups, and the style groups are themselves partly dated by the language. The medieval inscriptions often have only a century, and so many of them gather at the middle of the century in the chart.
- **Runestones without a secure style group** – more than half – have no date and are not in the chart.
- **Portable objects** depend on where people have dug: town excavations give many rune sticks.
- **The shifts are the literature's,** with sources in the text. Our contribution is the count of the terms, the inscriptions over time and the images from the groove analysis.

:::box The essentials in brief
- The Vendel Period, the Viking Age and the Middle Ages are labels from the nineteenth and twentieth centuries. The word Vendel Period was used as early as 1901 and 1908, but became a period name only in the 1920s. The Viking Age became a key term in Swedish archaeology only in the second half of the twentieth century.
- The neighbouring countries use other names and other boundaries for the same time.
- The clear shifts in Scandinavia lie around 540, 700–750, 965–1000, 1100–1130 and 1350 – not at 793 and 1066.
- In our material the runestones end around 1100–1130, and the runes move into the church and onto the graves. Almost one Swedish runestone in three with a secure style group dates from after 1066.
:::

## Sources

- Scandinavian Runic-text Database (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Sveriges runinskrifter II, Östergötlands runinskrifter (Ög 240), via Vitki's find history.
- Olsén, Pär 1981. Om ”vendeltidens” ålder och ursprung. *Fornvännen* 76, pp. 8–15. CC BY 4.0.
- Lamm, Jan Peder 2001. Oscar Almgren och vendeltiden – en kronologihistorisk notis. *Fornvännen* 96, pp. 39–40. CC BY 4.0.
- Nicklasson, Påvel 2017. Sven Nilsson och Ledetraaden, Christian Thomsen och Ur-invånarna. *Fornvännen* 112, pp. 137–153. CC BY 4.0.
- Malmer, Mats P. 1968. De kronologiska grundbegreppen. *Fornvännen* 63, pp. 81–91. CC BY 4.0.
- Ambrosiani, Björn 1968. Vendeltid eller vikingatid? *Fornvännen* 63, pp. 51–55. CC BY 4.0.
- Holmberg, Per, Bo Gräslund, Olof Sundqvist and Henrik Williams 2020. The Rök Runestone and the End of the World. *Futhark* 9–10, pp. 7–38. CC BY 4.0.
- Löwenborg, Daniel 2012. An Iron Age Shock Doctrine. *Journal of Archaeology and Ancient History* 4, pp. 3–29. CC BY 4.0.
- Lagerås, Per 2013. Agrara fluktuationer och befolkningsutveckling på sydsvenska höglandet tolkade utifrån röjningsrösen. *Fornvännen* 108, pp. 263–277. CC BY 4.0.
- Daly, Aoife 2022. Dendrochronology. Oak from Ribe. In S. M. Sindbæk (ed.), *Northern Emporium* 1, pp. 327–339. CC BY 4.0.
- Edberg, Rune and Johnny Karlsson 2016. Bone skates and young people in Birka and Sigtuna. *Fornvännen* 111, pp. 7–16. CC BY 4.0.
- Åkerström, Hanna 2019. Det tidigvikingatida runmaterialet: En inventering. *Futhark* 8, pp. 7–88. CC BY 4.0.
- Hillerdal, Charlotta 2025. Review of *Northern Emporium* 1–2. *Current Swedish Archaeology* 33, pp. 165–170. CC BY 4.0.
- Ros, Jonas 2002. Sigtuna och folklanden. *Fornvännen* 97, pp. 161–175. CC BY 4.0.
- Thunmark-Nylén, Lena 1989. Medeltidens födelse – Krapperupssymposiet 1988. *Fornvännen* 84, p. 159. CC BY 4.0.
- The analysis plan (locked before the count) and the code are open on [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-17-perioderna.md). On the shape of the runes: [Why do the runes look the way they do?](/en/artiklar/varfor-ser-runorna-ut-som-de-gor)
- Photos: Wikimedia Commons, with photographer and licence in the captions. The groove images: Vitki, after the open scans named in the captions."""

# ---- checks ----------------------------------------------------------------------------------------------------------
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index(":::box") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 5 and all(re.match(r"https://(upload|thumb)\.wikimedia\.org/|/api/blog/figures/[0-9a-f]{16}\.png$", u) for u in imgs), imgs
labels = ["Forskning", "Datering och stil", "Huggspår och 3D"]
err = blog_labels.check(labels)
assert err is None, err
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
path = os.path.join(ROOT, "utdata", "blogg", "perioder.json")
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
                 "topic": "Forskning|perioder", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
