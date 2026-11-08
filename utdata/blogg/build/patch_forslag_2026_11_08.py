"""Rättelse i den publicerade artikeln "Fem runstenar söker sin ristare" (PoSiCSxYlkiwpQMOp35u), Viktor 2026-11-08: "ok gör
ändringen". Efter proven mot Runor 2020 (analysplaner/2026-11-08-samma-hand-runor.md: modellen gav inte oftare samma
ristare inom runologernas grupper än grannstenar gör) har Stenöversiktens kategorier bytt namn (nytt förslag → förslag
bland kända, möjligt förslag → svagt förslag) och inget ristarförslag kallas längre starkt utan oberoende belägg (METHODS
14i). Rättelsen byter ord där artikeln sa att beläggen pekar "starkt", ger kategorierna deras nya namn inom parentes
(siffrorna står kvar som de räknades), säger att blindprovets "rätt" betyder samma ristare som Rundata, och lägger till
ett daterat tillägg före korthetsrutan. Den levande texten jämförs först med ögonblicksbilden
utdata/blogg/fem-runstenar.LIVE-2026-11-08.json; skriptet vägrar om den har ändrats.
    ../../../.venv/bin/python patch_forslag_2026_11_08.py [--live]"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
DOC = "PoSiCSxYlkiwpQMOp35u"
FIELDS = ("title", "summary", "body", "title_en", "summary_en", "body_en")
GH = "https://github.com/Precatio/runes/blob/main"
before = json.load(open(os.path.join(ROOT, "utdata", "blogg", "fem-runstenar.LIVE-2026-11-08.json"), encoding="utf-8"))

TILLAGG_SV = f"""## Tillägg 8 november 2026: vad blindprovet mäter

Blindprovet mäter hur ofta Vitki kommer fram till samma ristare som Rundata – och Rundatas tillskrivningar i Uppland och Södermanland bygger till stor del på samma slags spår som Vitki följer. Den 8 november prövade vi därför modellen mot ett facit den aldrig har sett: runologernas egna bedömningar i Runor 2020 av vilka stenar som är gjorda av samma hand, också när handen saknar namn. Där gav modellen inte oftare samma ristare inom en sådan grupp än vad grannstenar på samma avstånd får – i 14 grupper fick 50 procent av stenparen samma förslag, mot 44 procent för grannarna, en skillnad som slumpen lätt ger. Modellen kan bara välja bland namngivna ristare, så en hand utan namn hamnar hos någon av dem: U 1015–1024, som runologerna håller för en och samma onämnda ristare, får alla Öpir – men det får grannstenarna också.

Därför heter förslagen i Stenöversikten nu *förslag bland kända* och *svagt förslag*, och inget förslag kallas längre starkt utan ett belägg som är oberoende av stavning, plats och stil, som huggtekniken. Stenöversikten visar också ett nytt belägg, *likhet utöver grannarna*: hur lik stenens text är andra stenar, utöver vad grannar på samma avstånd brukar vara. Det känner igen runologernas egna grupper långt oftare än grannar gör – 89 mot 33 procent av paren – och en sten vars mest lika sten också saknar ristare märks som en *möjlig onämnd hand*. Siffrorna ovan står kvar som de räknades; de fem förslagen är fortfarande hypoteser att pröva. Metoden beskrivs i [Vitkis metoddokumentation, avsnitt 14i]({GH}/METHODS.md).

"""
TILLAGG_EN = f"""## Addendum 8 November 2026: what the blind test measures

The blind test measures how often Vitki arrives at the same carver as Rundata – and Rundata's attributions in Uppland and Södermanland rest largely on the same kind of traces that Vitki follows. On 8 November we therefore tested the model against a key it has never seen: the runologists' own judgements in Runor 2020 of which stones were made by the same hand, also when the hand has no name. There the model did not give the same carver within such a group more often than neighbouring stones at the same distance get – in 14 groups 50 per cent of the stone pairs got the same suggestion, against 44 per cent for the neighbours, a difference chance easily gives. The model can only choose among named carvers, so a hand without a name ends up with one of them: U 1015–1024, which the runologists hold to be one and the same unnamed carver, all get Œpir – but so do the neighbouring stones.

The suggestions in the stone overview are therefore now called *suggestions among known carvers* and *weak suggestions*, and no suggestion is called strong any more without evidence independent of spelling, place and style, such as the carving technique. The stone overview also shows a new kind of evidence, *similarity beyond the neighbours*: how alike the stone's text is to other stones, beyond what neighbours at the same distance usually are. It recognises the runologists' own groups far more often than neighbours do – 89 against 33 per cent of the pairs – and a stone whose most alike stone also lacks a carver is marked as a *possible unnamed hand*. The figures above stand as they were computed; the five suggestions are still hypotheses to test. The method is described in [Vitki's method documentation, section 14i (in Swedish)]({GH}/METHODS.md).

"""

REPL = {
    "summary": [("hade de nya förslagen rätt fyra gånger av fem", "stämde de nya förslagen med Rundatas ristare fyra gånger av fem")],
    "summary_en": [("the new suggestions were right four times out of five", "the new suggestions matched Rundata's carver four times out of five")],
    "body": [
        ("Där får 86 stenar utan ristare ett *nytt förslag*, vilket betyder att beläggen pekar starkt mot en ristare. Ytterligare 292 får ett *möjligt förslag*.",
         "Där fick 86 stenar utan ristare ett *nytt förslag* (sedan 8 november *förslag bland kända*), vilket betyder att beläggen pekar mot en av de ristare Vitki känner. Ytterligare 292 fick ett *möjligt förslag* (i dag *svagt förslag*)."),
        ("och ju längre åt höger, desto starkare pekar beläggen mot en ristare. Mörkblått är nytt förslag (styrka minst 0,5), ljusblått möjligt förslag (minst 0,3).",
         "och ju längre åt höger, desto mer pekar beläggen mot en av de namngivna ristarna. Mörkblått är nytt förslag (styrka minst 0,5; i dag förslag bland kända), ljusblått möjligt förslag (minst 0,3; i dag svagt förslag)."),
        ("alla statusar utom nytt förslag avstängda", "alla statusar utom nytt förslag (i dag förslag bland kända) avstängda"),
        ("Det som gör förslaget starkt är att två vittnen", "Det som talar för förslaget är att två vittnen"),
        ("ordnad efter hur starkt beläggen pekar", "ordnad efter hur tydligt beläggen pekar"),
        ("stäng av alla statusar utom *nytt förslag*", "stäng av alla statusar utom *förslag bland kända* (så heter *nytt förslag* sedan 8 november)"),
        ("kan dessutom säga hur ofta det stämmer: i ett blindprov där svaret var dolt hade de nya förslagen rätt fyra gånger av fem, ungefär dubbelt så ofta som en gissning på närmaste kända ristare.",
         "kan dessutom säga hur ofta det stämmer med forskningens attribueringar: i ett blindprov där svaret var dolt stämde de nya förslagen med Rundatas ristare fyra gånger av fem, ungefär dubbelt så ofta som en gissning på närmaste kända ristare. Mot runologernas egna grupper av samma hand gjorde modellen däremot inte bättre än geografin (tillägget ovan)."),
        (":::box Det viktigaste i korthet", TILLAGG_SV + ":::box Det viktigaste i korthet"),
    ],
    "body_en": [
        ("There 86 stones without a carver get a *new suggestion*, which means that the evidence points strongly to a carver. Another 292 get a *possible suggestion*.",
         "There 86 stones without a carver got a *new suggestion* (since 8 November a *suggestion among known carvers*), which means that the evidence points to one of the carvers Vitki knows. Another 292 got a *possible suggestion* (today a *weak suggestion*)."),
        ("and the further right, the more strongly the evidence points to a carver. Dark blue is a new suggestion (strength at least 0.5), light blue a possible suggestion (at least 0.3).",
         "and the further right, the more the evidence points to one of the named carvers. Dark blue is a new suggestion (strength at least 0.5; today a suggestion among known carvers), light blue a possible suggestion (at least 0.3; today a weak suggestion)."),
        ("every status except new suggestion switched off", "every status except new suggestion (today suggestion among known carvers) switched off"),
        ("ordered by how strongly the evidence points", "ordered by how clearly the evidence points"),
        ("switch off every status except *new suggestion*", "switch off every status except *suggestion among known carvers* (the name of *new suggestion* since 8 November)"),
        ("and can also say how often it holds: in a blind test with the answer hidden, the new suggestions were right four times out of five, about twice as often as a guess at the nearest known carver.",
         "and can also say how often it agrees with the scholars' attributions: in a blind test with the answer hidden, the new suggestions matched Rundata's carver four times out of five, about twice as often as a guess at the nearest known carver. Against the runologists' own groups of the same hand, however, the model did no better than geography (the addendum above)."),
        (":::box The essentials in brief", TILLAGG_EN + ":::box The essentials in brief"),
    ],
}

from api.routers import blog  # noqa: E402

ref = blog.firestore().collection(blog.COLLECTION).document(DOC)
live = ref.get().to_dict()
assert live and live.get("published") and live.get("slug") == "fem-runstenar-soker-sin-ristare"
changed = [k for k in FIELDS if live.get(k) != before.get(k)]
assert not changed, f"Den levande texten har ändrats sedan ögonblicksbilden ({changed}); slå ihop för hand"
new = {k: live[k] for k in FIELDS}
for field, pairs in REPL.items():
    for old, rep in pairs:
        n = new[field].count(old)
        assert n == 1, (field, old[:60], n)
        new[field] = new[field].replace(old, rep)
for lang, key in (("sv", "body"), ("en", "body_en")):
    b = new[key]
    assert b.count(":::box") == live[key].count(":::box") and "{" not in b and "}" not in b
    assert b.index("Tillägg 8 november" if lang == "sv" else "Addendum 8 November") < b.index(":::box")
for k in FIELDS:
    if new[k] != live[k]:
        print(k, len(live[k]), "->", len(new[k]))
if "--live" in sys.argv:
    ref.set({**{k: new[k] for k in FIELDS}, "updatedAt": dt.datetime.now(dt.timezone.utc)}, merge=True)
    blog._forget()
    after = ref.get().to_dict()
    assert all(after[k] == new[k] for k in FIELDS)
    json.dump({k: new[k] for k in FIELDS}, open(os.path.join(ROOT, "utdata", "blogg", "fem-runstenar.EFTER-2026-11-08.json"), "w",
                                                 encoding="utf-8"), ensure_ascii=False, indent=1)
    print("uppdaterad:", DOC)
else:
    print("torrkörning; --live skriver")
