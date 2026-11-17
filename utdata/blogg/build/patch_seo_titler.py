"""Söktitlar (seo_title, seo_title_en) för de publicerade artiklarna och rapporterna, 2026-11-17 (Viktor: "se till så
artiklarna uppfyller alla googles senaste rekommendationer"). Söktiteln är bara sidans <title> och delningstitel – rubriken
på sidan, texten och citeringsuppgifterna är oförändrade, och updatedAt rörs inte (ingen innehållsändring).

Regler: varje söktitel bär ett ord som folk söker på (runstenar, runor, runinskrifter, vikingatiden, ristare …), säger
samma sak som rubriken och ryms i Googles cirka 60 tecken med " | Vitki" (rapporterna: " – rapport | Vitki").
    .venv/bin/python utdata/blogg/build/patch_seo_titler.py            # visa
    .venv/bin/python utdata/blogg/build/patch_seo_titler.py --write    # skriv och publicera webbplatsen"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

ARTIKLAR = {
    "varfor-ser-runorna-ut-som-de-gor": ("Runornas form: varför ser runorna ut som de gör?", "Rune shapes: why do the runes look as they do?"),
    "vi-studerar-de-danska-runstenarna": ("Danska runstenar – kamraten före släkten", "Danish runestones – the comrade before the kin"),
    "ingen-pa-runstenarna-hette-freja": ("Fornnordiska namn: ingen på runstenarna hette Freja", "Old Norse names: no one on the runestones was Freja"),
    "varfor-har-norge-bara-66-runstenar": ("Norges runstenar: 66 mot Sveriges 2 300 – varför?", "Why Norway has 66 runestones and Sweden 2,300"),
    "de-namnde-aldrig-hemmet": ("Runinskrifter på brittiska öarna, del 2: utvandrarna", "Runic inscriptions in the British Isles, part 2"),
    "de-gamla-landen-roden": ("Roden – Upplands kustland på vikingatiden", "Roden – Uppland's coastal land in the Viking Age"),
    "nar-askan-hade-ett-namn": ("Tor på runstenarna – när åskan hade ett namn", "Thor on the runestones – when the thunder had a name"),
    "de-gamla-landen-sotholm": ("Sotholm – Södertörn på vikingatiden", "Sotholm – Södertörn in the Viking Age"),
    "hur-bra-ar-var-modell-egentligen": ("Hur bra är Vitkis modell för runtexter?", "How good is Vitki's runic text model?"),
    "ristarna-som-aldrig-blev-ihagkomna": ("Okända runristare: de som aldrig blev ihågkomna", "Unknown rune carvers no one remembered"),
    "tor-foll-hjalten-blev-drang": ("Vikinganamn i dag: Tor föll, hjälten blev dräng", "Which Viking names live on today?"),
    "fardena-var-de-ungas": ("Vikingafärderna var de ungas", "The Viking journeys belonged to the young"),
    "vikingarnas-varld": ("Vikingarnas värld: platserna på runstenarna", "The Vikings' world: places on the runestones"),
    "vad-berattar-runskrifterna-pa-de-brittiska-oarna": ("Runinskrifter på brittiska öarna – vad berättar de?", "Runic inscriptions of the British Isles"),
    "mild-i-ord-och-god-pa-mat": ("Vikingatidens dygder: mild i ord och god på mat", "Viking Age virtues: gentle in speech, free with food"),
    "tre-punkter-i-texten": ("Luckor i runtexter – vad stod i luckan?", "Gaps in runic texts – what stood in the gap?"),
    "varfor-sten": ("Varför sten? Runor i trä, ben, metall och sten", "Why stone? Runes in wood, bone, metal and stone"),
    "hemma-mellan-rikena-skanes-runstenar": ("Skånes runstenar – hemma mellan rikena", "The runestones of Skåne – at home between the realms"),
    "vem-talar-i-havamal": ("Hávamál i dag – vad den Höge säger tusen år senare", "Hávamál today – what the High One says"),
    "fem-runstenar-soker-sin-ristare": ("Fem runstenar söker sin ristare – nya ristarförslag", "Five runestones looking for their carver"),
    "stenar-och-stavar": ("Stav – runordet med sex betydelser", "Stave – the runic word with six meanings"),
    "reste-sjalv-eller-lat-resa": ("Runstenarnas vanligaste ord, landskap för landskap", "The commonest runestone words, province by province"),
    "runorna-som-fattas": ("Saknade runor – Vitkis sannolikhetsmodell fyller i", "Missing runes – work on Vitki's probability model"),
    "stilgruppernas-morkertal": ("Runstenarnas stilgrupper och mörkertalet", "Runestone style groups and their dark number"),
    "hur-spraklik-ar-en-runfoljd": ("Olästa runinskrifter – kryptologi som metod", "Unread runic inscriptions – cryptology as method"),
    "undantaget-vid-randers": ("Randers runstenar – där danskarna bad på stenarna", "The Randers runestones – where the Danes prayed"),
    "den-som-bryter-denna-sten": ("Runmagi och förbannelser i tusen år", "Runic magic and curses through a thousand years"),
    "korpen-som-heter-minne": ("Hávamál och korpen som heter Minne", "Hávamál and the raven called Memory"),
    "maltstenen-raknad-i-stallet-for-tolkad": ("Maltstenen – runstenen räknad i stället för tolkad", "The Malt runestone – counted, not interpreted"),
    "dottrarna-som-runstenarna-glomde": ("Döttrar på runstenarna – de som glömdes", "Daughters on the runestones – the forgotten"),
    "hon-arvde-efter-sitt-barn-kvinnorna-pa-runstenarna": ("Kvinnorna på runstenarna – hon ärvde efter sitt barn", "The women on the runestones – heirs of their children"),
    "erik-skrev-r-och-bygden-skrev-efter": ("Yr-runan och ristaren Erik kring Enköping", "The yr rune and the carver Erik near Enköping"),
    "tor-svarade-korset-och-tystnade": ("Tor och korset på svenska runstenar", "Thor and the cross on Swedish runestones"),
    "2026-10-ristarsignatur-breder-ut-sig": ("Ristarsignaturer: ristaren tog sista ordet", "Carver signatures: the carver had the last word"),
    "2026-10-bonen-tystnade-korset-stod-kvar": ("Böner på runstenar: bönen tystnade, korset stod kvar", "Prayers on runestones: the prayer fell silent"),
    "vastgotarna-skrev-som-danskarna": ("Västergötlands runstenar skrevs som danskarnas", "Västergötland's runestones, written like the Danes'"),
}
RAPPORTER = {
    "upplands-folkland-skiljer-runstenarna": ("Upplands runstenar och folklandsgränserna", "Uppland runestones and folkland borders"),
    "runstenarna-vid-sin-tids-vatten": ("Runstenarna restes vid vattnet år 1050", "Runestones by the water of AD 1050"),
    "skanningen-som-ledtrad": ("3D-skanning som ledtråd i runtexter", "3D scans as a clue to runic texts"),
    "ristningen-vand-mot-vagen": ("Runstenarna vände texten mot vägen", "Runestones turned their text to the road"),
    "seriationen-foljer-stilkronologin": ("Runstenarnas språk följer stilkronologin", "Runic language follows style chronology"),
    "barnen-arvde-namnled": ("Barnen ärvde namnled på runstenarna", "Children inherited name parts on runestones"),
    "ristarforslag-blindprov": ("Statistiska ristarförslag i blindprov", "Statistical carver suggestions, blind test"),
    "monoftongstavningen-blir-ovanligare": ("Monoftongstavning på runstenarna minskar", "Monophthong spellings decline on runestones"),
    "familjegrupper-vid-gravfalten": ("Runstenar i familjegrupper vid gravfälten", "Runestones in family groups at grave fields"),
    "soner-och-broder-dog-utanfor-norden": ("Söner och bröder som dog utanför Norden", "Sons and brothers dying outside Scandinavia"),
    "kvinnor-bland-resarna-svealand-gotaland": ("Kvinnor som reste runstenar", "Women who raised runestones"),
    "r-for-yr-runan-vastra-uppland": ("Yr-runan byttes mot r i västra Uppland", "The yr rune gives way to r in west Uppland"),
}
# Google visar omkring 60 tecken; titeln får suffixet " | Vitki" (8) och rapporterna " – rapport | Vitki" (18)
for d, room in ((ARTIKLAR, 60 - 8), (RAPPORTER, 60 - 18)):
    for slug, (sv, en) in d.items():
        assert len(sv) <= room and len(en) <= room + 1, (slug, len(sv), len(en))


def main(write: bool):
    from api.routers import blog
    from src import site_export
    alla = {**ARTIKLAR, **RAPPORTER}
    docs = {d.to_dict().get("slug"): d for d in blog.firestore().collection(blog.COLLECTION).stream()}
    saknas = [s for s in alla if s not in docs or not docs[s].to_dict().get("published")]
    assert not saknas, saknas
    for slug, (sv, en) in alla.items():
        old = docs[slug].to_dict()
        print(f"{slug}\n   {old['title']}\n → {sv}\n   {old.get('title_en')}\n → {en}")
        if write:
            blog._backup(docs[slug].id, old)
            docs[slug].reference.set({"seo_title": sv, "seo_title_en": en}, merge=True)
    if write:
        blog._forget()
        print(json.dumps(site_export.publish_now(), ensure_ascii=False, default=str))


if __name__ == "__main__":
    main("--write" in sys.argv)
