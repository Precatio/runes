"""Artikeln "Vikingarnas värld – vilka platser nämner de?" (först "Österled blev forntid"): platser utanför Norden i runstenar och sagor (sv + en). Siffrorna låses mot den
låsta planens resultat (utdata/varlden/analys_resultat.json, analysplaner/2026-10-28-vikingarnas-omvarld.md);
runstenen står ordagrant som i Rundatas normalisering och sagacitaten som i korpusfilerna i utdata/varlden/korpus.
    ../../../.venv/bin/python build_osterled.py [--write | --update DOC]"""
import csv
import datetime as dt
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import commons  # noqa: E402
from src.messages import _INGVARR  # noqa: E402

V = os.path.join(ROOT, "utdata", "varlden")
R = json.load(open(os.path.join(V, "analys_resultat.json"), encoding="utf-8"))
T1, T2, T3, MH, D = R["test1_amne"], R["test2_tid"], R["test3_plats"], R["test3_mh"], R["beskrivande"]
ROWS = list(csv.DictReader(open(os.path.join(V, "platser_per_text.csv"), encoding="utf-8")))
REGION = {p["plats"]: p["region"] for p in csv.DictReader(open(os.path.join(V, "platser.csv"), encoding="utf-8"))}
recs = json.load(open(os.path.join(ROOT, "data", "rundata.json")))
recs = recs if isinstance(recs, list) else recs.get("inscriptions", list(recs.values()))
BY = {r["signum"]: r for r in recs}

pc = lambda x: round(100 * x)  # noqa: E731
tus = lambda x, lang="sv": f"{int(x):,}".replace(",", " " if lang == "sv" else ",")  # noqa: E731


def corpus_text(folder, start):
    for f in os.listdir(os.path.join(V, "korpus", folder)):
        if unicodedata.normalize("NFC", f).startswith(start):
            return unicodedata.normalize("NFC", open(os.path.join(V, "korpus", folder, f), encoding="utf-8").read())
    raise FileNotFoundError(start)


def texts_with(corpus, region=None, place=None):
    rs = [r for r in ROWS if r["korpus"] == corpus]
    if place:
        return sum(1 for r in rs if int(r[place]) > 0), len(rs)
    return sum(1 for r in rs if any(int(r[p]) > 0 for p, g in REGION.items() if g == region)), len(rs)


# ---- the locked numbers ---------------------------------------------------------------------------------------------
assert T1["dom"] == "skillnaden håller" and T1["p_holm"] < 0.001 and T1["n"] == [36, 42]
assert T2["dom"] == "obestämt" and T3["dom"].startswith("obestämt") and T3["hint_only"]
assert 0.25 <= min(R["robusthet"][k]["t1"]["diff"] for k in ("utan_allmant", "traffar", "atlanten_vaster", "utan_storsta", "utan_yngvars"))
ROB = [R["robusthet"][k]["t1"]["diff"] for k in ("utan_allmant", "traffar", "atlanten_vaster", "utan_storsta", "utan_yngvars")]
SE, FA, IS, HK, HKV = (D[k] for k in ("runstenar_sverige", "fornaldarsagor", "islanningasagor", "heimskringla", "heimskringla_vers"))
ATL_IS = texts_with("islanningasagor", region="nordatlanten")
BJ = {c: texts_with(c, place="Bjarmaland")[0] for c in ("fornaldarsagor", "islanningasagor", "heimskringla")}
SERK = {c: texts_with(c, place="Serkland")[0] for c in ("runstenar_sverige", "fornaldarsagor", "islanningasagor", "heimskringla")}
HKV_ANY = texts_with("heimskringla_vers", region="öster")[0] + texts_with("heimskringla_vers", region="väster")[0]
ING = sum(1 for r in recs if r.get("period") == "V" and "runsten" in (r.get("object") or "").lower()
          and re.search(_INGVARR, r.get("translation_en") or "", re.I))
assert ATL_IS == (25, 42) and BJ == {"fornaldarsagor": 6, "islanningasagor": 3, "heimskringla": 4}
assert SERK["islanningasagor"] == 0 and SERK["runstenar_sverige"] == 6 and 20 <= ING <= 30
EARLY = MH["strata"]["tidig"]
from src.research_gaps import province  # noqa: E402
EAST = [r for r in ROWS if r["korpus"] == "runstenar_sverige" and any(int(r[p]) for p, g in REGION.items() if g == "öster")]
MAL = (sum(1 for r in EAST if province(BY[r["text"]]) in ("U", "Sö", "Vs", "Nä")), len(EAST))
assert MAL == (74, 90)
assert EARLY == [25, 214, 0, 68]

# ---- the quotations, verbatim ----------------------------------------------------------------------------------------
SO179 = BY["Sö 179"]["normalization"].strip()
assert SO179.endswith('ÞæiR foru drængila fiarri at gulli ok austarla ærni gafu, dou sunnarla a "Særklandi.')
BOSA = "heldu þeir í Austrveg ok kómu undir Bjarmaland ok lögðu undir einn eyðiskóg"
assert BOSA in corpus_text("fornaldarsogur", "Bósa_saga")
BJORN = "Um sumarið eftir fór Björn vestur til Englands og fékk þar góða virðing"
assert BJORN in corpus_text("islendingasogur", "bjarnar_saga")

# ---- photograph ------------------------------------------------------------------------------------------------------
FILE = commons.wikidata_files(["Sö 179"])["Sö 179"]
INFO = commons.commons_info([FILE])[FILE]
assert INFO["licence"] == "CC BY-SA 3.0" and "Tåggas" in INFO["author"]
PAGE = "https://commons.wikimedia.org/wiki/File:" + FILE.replace(" ", "_")
CREDIT_SV = f"Foto: Tåggas (sv.wikipedia), [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/), via [Wikimedia Commons]({PAGE})."
CREDIT_EN = f"Photo: Tåggas (sv.wikipedia), [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/), via [Wikimedia Commons]({PAGE})."


SK_UI = json.load(open(os.path.join(V, "sjalvkontroll", "resultat.json"), encoding="utf-8"))["p1"]["utan_ingvar"]


def chart(lang):
    sv = lang == "sv"
    rows = [(SE, "Svenska runstenar, 1000-talet" if sv else "Swedish runestones, 11th century", True),
            (SK_UI, "Svenska runstenar utan Ingvarsstenarna" if sv else "Swedish runestones without the Ingvarr stones", True),
            (FA, "Fornaldarsagor, om forntiden" if sv else "Legendary sagas, about the ancient past", True),
            (HK, "Kungasagorna i Heimskringla" if sv else "The kings' sagas in Heimskringla", False),
            (HKV, "Skaldeverserna i Heimskringla" if sv else "The skaldic verses in Heimskringla", False),
            (IS, "Islänningasagor, om de egna förfäderna" if sv else "Sagas of Icelanders, about their own ancestors", False)]
    out = [":::chart Hur stor del av platserna utanför Norden som ligger i öster" if sv else
           ":::chart How much of the world outside Scandinavia lies in the east"]
    for d, label, hi in rows:
        lo, up = pc(d["ci"][0]), pc(d["ci"][1])
        note = f"troligen mellan {lo} och {up} %" if sv else f"probably between {lo} and {up} %"
        out.append(f"{'+' if hi else ''}{label} | {pc(d['ostandel'])} | {note}")
    out.append("Källa: Vitkis räkning av platser i öster och väster i Samnordisk runtextdatabas, sagadb.org och heimskringla.no. "
               "Varje plats räknas en gång per sten, saga eller strof." if sv else
               "Source: Vitki's count of places in the east and the west in the Scandinavian Runic-text Data Base, sagadb.org and "
               "heimskringla.no. Each place is counted once per stone, saga or stanza.")
    return "\n".join(out) + "\n:::"


title = "Vikingarnas värld – vilka platser nämner de?"
summary = ("Miklagård, Serkland, England, Irland, Grönland: vi räknade alla platser utanför Norden som nämns på "
           "runstenarna och i sagorna. Stenarna ser mot öster, islänningarnas sagor om sina förfäder mot väster – men "
           "sagorna om forntiden ser mot öster igen. Österleden hade blivit saga.")

PLATSER_SV = """:::box Platserna och vad de heter i dag
- **Miklagård** (*Miklagarðr*, ”den stora staden”) – Konstantinopel, dagens Istanbul. **Grekland** (*Grikkland*) är på runstenarna det bysantinska riket.
- **Garðaríki** (*Garðar*) – rikena längs de ryska floderna, i dag delar av Ryssland, Ukraina och Belarus. **Holmgård** är Novgorod och **Kænugarðr** Kiev.
- **Serkland** – de muslimska länderna i sydöst, kring Kaspiska havet och kalifatet. Exakt var gränsen gick är omdiskuterat.
- **Bjarmaland** – trakterna kring Vita havet och floden Dvina i nordvästra Ryssland.
- **Baltikum** – *Eistland* är Estland, *Kúrland* Kurland i västra Lettland, *Lífland* Livland, *Sámland* Sambien kring Kaliningrad och *Kirjálaland* Karelen.
- **Vendland** – vendernas land vid Östersjöns sydkust, i dag nordöstra Tyskland och Polen. Där låg Jomsborg.
- **Valland** – Frankrikes kust, särskilt Normandie. *Rúðuborg* är Rouen. **Saxland** är Sachsen och **Flæmingjaland** Flandern.
- **England** – med *Jórvík* (York), *Lundúnir* (London) och *Norðimbraland* (Northumbria). **Bretland** är Wales.
- **Irland** och **Skottland** – med *Dyflinn* (Dublin) och *Katanes* (Caithness). *Suðreyjar* är Hebriderna, *Hjaltland* Shetland och *Orkneyjar* Orkney.
- **Söderut** – *Rúmaborg* är Rom, *Jórsalir* Jerusalem, *Langbarðaland* langobardernas land i Italien – på runstenarna nått österut, så troligen det bysantinska södra Italien – *Púl* Apulien, *Sikiley* Sicilien, *Nörvasund* Gibraltarsund och *Bláland* Afrika.
- **Vinland** – Nordamerika, där den enda säkra nordiska boplatsen är L’Anse aux Meadows på Newfoundland. *Helluland* och *Markland* är troligen Baffinön och Labrador.
:::"""

PLATSER_EN = """:::box The places and their names today
- **Miklagarðr** ("the great city") – Constantinople, today's Istanbul. **Greece** (*Grikkland*) on the runestones is the Byzantine Empire.
- **Garðaríki** (*Garðar*) – the realms along the Russian rivers, today parts of Russia, Ukraine and Belarus. **Hólmgarðr** is Novgorod and **Kænugarðr** Kyiv.
- **Serkland** – the Muslim lands to the south-east, around the Caspian Sea and the caliphate. Exactly where its borders lay is debated.
- **Bjarmaland** – the lands around the White Sea and the river Dvina in north-western Russia.
- **The Baltic lands** – *Eistland* is Estonia, *Kúrland* Courland in western Latvia, *Lífland* Livonia, *Sámland* Sambia around Kaliningrad and *Kirjálaland* Karelia.
- **Vindland** – the land of the Wends on the southern Baltic coast, today north-eastern Germany and Poland. Jómsborg lay there.
- **Valland** – the coast of France, above all Normandy. *Rúðuborg* is Rouen. **Saxland** is Saxony and **Flæmingjaland** Flanders.
- **England** – with *Jórvík* (York), *Lundúnir* (London) and *Norðimbraland* (Northumbria). **Bretland** is Wales.
- **Ireland** and **Scotland** – with *Dyflinn* (Dublin) and *Katanes* (Caithness). *Suðreyjar* are the Hebrides, *Hjaltland* Shetland and *Orkneyjar* Orkney.
- **To the south** – *Rúmaborg* is Rome, *Jórsalir* Jerusalem, *Langbarðaland* the land of the Lombards in Italy – reached by the eastern route on the runestones, so probably Byzantine southern Italy – *Púl* Apulia, *Sikiley* Sicily, *Nörvasund* the Strait of Gibraltar and *Bláland* Africa.
- **Vínland** – North America, where the only certain Norse site is L'Anse aux Meadows on Newfoundland. *Helluland* and *Markland* are probably Baffin Island and Labrador.
:::"""

# ---- more quotations, verbatim -----------------------------------------------------------------------------------------
SO131 = BY["Sö 131"]["normalization"].strip()
assert SO131.endswith('For austr heðan með "Ingvari, a "Særklandi liggR sunR "ØyvindaR.')
BOLLI = ("Bolli var svo mikill skartsmaður er hann kom út úr för þessi að hann vildi engi klæði bera nema skarlatsklæði og "
         "pellsklæði og öll vopn hafði hann gullbúin")
assert BOLLI in corpus_text("islendingasogur", "laxdaela_saga")
JOMALI = "Þar er göfgat goð þat, er Jómali heitir. Þar er gull mikit ok gersemar."
assert JOMALI in corpus_text("fornaldarsogur", "Bósa_saga")
YNG = corpus_text("fornaldarsogur", "Yngvars_saga")
assert "dreka" in YNG and "risa" in YNG  # drakar och en jätte i Yngvars saga
MIKLA_IS = texts_with("islanningasagor", place="Bysans/Miklagård")[0]
assert MIKLA_IS == 8
ENG, GRE = (texts_with("runstenar_sverige", place=p)[0] for p in ("England", "Bysans/Miklagård"))
assert (ENG, GRE) == (28, 27)

# ---- the map (varlden_karta.py) ----------------------------------------------------------------------------------------
from src import blog_figures  # noqa: E402
KARTA = os.path.join(ROOT, "utdata", "blogg", "varlden")
MAP_URL = {lang: blog_figures.freeze(open(os.path.join(KARTA, f"karta_{lang}.png"), "rb").read()) for lang in ("sv", "en")}
MAP_SV = (f"![Karta över platserna utanför Norden i runstenar och sagor]({MAP_URL['sv']})\n"
          "Platserna utanför Norden i tre källslag. Cirkelns yta visar hur stor del av texterna som nämner platsen, av dem "
          "som nämner någon plats utanför Norden alls; rutan i varje panels hörn visar de allmänna riktningarna ”i öster” och ”i "
          "väster”, som inte har någon plats. Lägena är ungefärliga. Källa: Vitkis räkning; karta © OpenStreetMap-bidragsgivare.")
MAP_EN = (f"![Map of the places outside Scandinavia in runestones and sagas]({MAP_URL['en']})\n"
          "The places outside Scandinavia in three kinds of source. The area of each circle shows how large a share of the "
          "texts name the place, of those that name any place outside Scandinavia at all; the box in each panel's corner shows the "
          "general directions “in the east” and “in the west”, which have no place. Positions are approximate. Source: Vitki's count; map © OpenStreetMap "
          "contributors.")

# Självkontrollen 2026-11-10 (analysplaner/2026-11-10-sjalvkontroll-osterled.md, 4d00080): utan Ingvarsstenarna
SK = json.load(open(os.path.join(V, "sjalvkontroll", "resultat.json"), encoding="utf-8"))["p1"]
assert SK["dom"] == "försvagat (obestämt)" and abs(SK["alla"]["ostandel"] - SE["ostandel"]) < 1e-9
UI = SK["utan_ingvar"]
assert SK["antal_ingvarsstenar"] == ING + 2 and {"Sö 179", "Ög 30"} <= set(SK["ingvarsstenar"]), "texten: de {ING} + Tolas sten + Ög 30"
assert pc(UI["ostandel"]) == pc(FA["ostandel"]), "texten säger att stenarna utan Ingvar ser mot öster lika ofta som fornaldarsagorna"
from osterled_text import BODY_SV, BODY_EN  # noqa: E402
V_ = dict(ING=ING, PHOTO=INFO["thumb"], CREDIT_SV=CREDIT_SV, CREDIT_EN=CREDIT_EN, SE_N=tus(SE["texter"]),
          SE_N_EN=tus(SE["texter"], "en"), N_SAGOR=FA["texter"] + IS["texter"] + HK["texter"], SE_P=pc(SE["ostandel"]),
          IS_P=pc(IS["ostandel"]), FA_P=pc(FA["ostandel"]), IS_N=IS["texter"], FA_N=FA["texter"], MAL=MAL,
          EARLY0=EARLY[0], EARLY_SE=EARLY[0] + EARLY[1], EARLY_OT=EARLY[2] + EARLY[3], BJORN=BJORN, ATL0=ATL_IS[0],
          ATL1=ATL_IS[1], MIKLA_IS=MIKLA_IS, BOLLI=BOLLI, BOSA=BOSA, JOMALI=JOMALI, BJ_FA=BJ["fornaldarsagor"],
          BJ_IS=BJ["islanningasagor"], D1=pc(T1["diff"]), D1_LO=pc(T1["ci"][0]), D1_HI=pc(T1["ci"][1]), ROB_LO=pc(min(ROB)),
          ROB_HI=pc(max(ROB)), HKV_P=pc(HKV["ostandel"]), T2_PROSA=pc(T2["prosa"]), T2_HITS=f"{T2['vers_hits']:.0f}",
          MH_OR=round(MH["or"]), ENG=ENG, GRE=GRE, SE_UI_P=pc(UI["ostandel"]), SE_UI_LO=pc(UI["ci"][0]),
          SE_UI_HI=pc(UI["ci"][1]), UI_N=SK["antal_ingvarsstenar"])
body = BODY_SV.format(**V_, PLATSER_SV=PLATSER_SV, MAP_SV=MAP_SV, CHART_SV=chart("sv"))
body_en = BODY_EN.format(**V_, PLATSER_EN=PLATSER_EN, MAP_EN=MAP_EN, CHART_EN=chart("en"))

title_en = "The Vikings' world – which places do they name?"
summary_en = ("Constantinople, Serkland, England, Ireland, Greenland: we counted every place outside Scandinavia named on "
              "the runestones and in the sagas. The stones look east, the Icelanders' sagas about their ancestors west – but "
              "the sagas about the ancient past look east again. The eastern route had become legend.")

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"

out = {"slug": "vikingarnas-varld", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Geografi", "Norden"]}
path = os.path.join(ROOT, "utdata", "blogg", "osterled.json")
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
                 "topic": "Forskning|omvarld", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
