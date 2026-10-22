"""Artikeln "Varför sten?": vad som skrevs på sten, trä, ben och metall, om de som högg visste att stenen skulle överleva,
och när stenen valdes. Varje siffra hämtas ur utdata/material/material.json (material.py, hela Rundata 3.1) och låses med
asserts; varje citerad inskrift står ordagrant i Rundatas normalisering. Tvåspråkig.
    ../../../.venv/bin/python build_material.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import commons  # noqa: E402

M = json.load(open(os.path.join(ROOT, "utdata", "material", "material.json"), encoding="utf-8"))
S, EX, ST = M["summary"], M["examples"], {x["signum"]: x for x in M["stand"]}
MB = M["material_by_period"]
pr = lambda x: round(100 * x)  # noqa: E731
sv = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en_n = lambda n: f"{n:,}"  # noqa: E731
share = lambda key, kind: pr(S[key]["kinds"].get(kind, 0) / S[key]["n"])  # noqa: E731
cnt = lambda key, kind: S[key]["kinds"].get(kind, 0)  # noqa: E731

# ---- låsningarna -----------------------------------------------------------------------------------
assert M["n_total"] == 6753 and M["period"] == {"V": 3662, "M": 2748, "?": 62, "U": 281}
assert MB["V"] == {"sten": 3264, "metall": 223, "ben/horn": 129, "trä": 34} and MB["M"]["trä"] == 1221 and MB["M"]["sten"] == 794
assert MB["U"] == {"sten": 70, "metall": 181, "ben/horn": 15, "trä": 14}
assert (S["V|sten"]["median_words"], share("V|sten", "minnesinskrift"), share("V|sten", "namn/ägare"), share("V|sten", "bön/religiös")) == (11, 61, 4, 3)
assert (S["V|ben/horn"]["median_words"], share("V|ben/horn", "namn/ägare"), share("V|ben/horn", "futhark"), share("V|ben/horn", "meddelande/annat")) == (4, 26, 14, 19)
assert (S["V|metall"]["median_words"], share("V|metall", "namn/ägare")) == (3, 64)
assert (S["V|trä"]["median_words"], share("V|trä", "tillverkare/ristare"), share("V|trä", "meddelande/annat")) == (8, 15, 24)
assert (share("U|metall", "besvärjelse/skydd"), share("U|metall", "namn/ägare"), S["U|sten"]["n"]) == (12, 27, 70)
assert (S["M|trä"]["median_words"], share("M|trä", "namn/ägare"), share("M|trä", "meddelande/annat"), share("M|trä", "bön/religiös"), share("M|trä", "futhark")) == (4, 27, 14, 11, 8)
assert (share("M|sten", "bön/religiös"), share("M|sten", "tillverkare/ristare"), share("M|sten", "minnesinskrift")) == (18, 17, 3)
assert (share("V|sten", "oläsligt"), share("M|trä", "oläsligt")) == (17, 35)
assert M["n_stand"] == 32 and M["n_v_stones"] == 3264
PL = M["places"]
assert PL["M|trä"]["Bryggen"] == 391 and PL["V|ben/horn"]["Sigtuna"] == 37 and PL["V|ben/horn"]["Lund"] == 14 and PL["V|trä"]["Folkebibliotekstomta"] == 8
assert M["m_wood_objects"]["märklapp"] == 138 and M["m_wood_objects"]["fyrkantig pinne"] == 181
UD = M["u_stone_dating"]
IMER = sum(v for k, v in UD.items() if "Imer 2007" in k)
assert IMER == 56 and sum(v for k, v in UD.items() if k.startswith("U 160")) == 20 and sum(v for k, v in UD.items() if "775/800" in k) == 3
# the quotations, verbatim
Q = {"Sm 16": "meþan stæinn lifiR ok stafiR runa", "U 114": "Þæt skal at minnum manna, meþan mænn lifa", "DR 212": "E mun standa, mæþ sten lifiR",
     "DR 131": "Sten kwæþsk hersi standa længi", "U 729": "Hiær mun standa stæinn miþli byia", "U 707": "Hiær mun standa stæinn næR br[aut]u",
     "Sö 137": "Stæinn saRsi standr at \"Øpi a þingstaþi", "G 343": "Æi meþan verald vakiR, liggR mærki hiar", "DR 40": "ÞeR stafaR munu \"Þorgunni miok længi lifa",
     "Sö 206": "Her skal standa stæinaR þessiR, runum ru[þ]niR", "DR 296": "Nu skal standa sten a biargi", "Ög 136": "Aft Vamoþ standa runaR þaR"}
for sig, text in Q.items():
    assert text in (ST[sig]["normalization"] or "").replace("ð", "þ"), (sig, text)
assert "Saxi risti runaR" in EX["DR AUD1997;264"]["normalization"] and EX["DR AUD1997;264"]["object"] == "pinne"
assert "Vindauga" in EX["N A240"]["normalization"] and "Rað þu" in EX["U NOR2000;34A"]["normalization"]
assert EX["Sö Fv1981;197"]["object"] == "dubbelkam" and "fuþork" in EX["Sö Fv1981;197"]["normalization"]
assert EX["DR M109"]["normalization"] == '"Þorsten i "Lundi.' and EX["N B540"]["normalization"] == "Kyss þú mik." and "sendir" in EX["N B333"]["normalization"]
assert "laukaz" in EX["DR IK149,1"]["normalization"] and "alu" in EX["DR IK149,1"]["normalization"] and "Ek erilaz" in EX["DR 196"]["normalization"]
assert EX["G 88"]["period"] == "U" and "fuþarkgw" in EX["G 88"]["normalization"].lower()
assert "dani gærþi kristna" in EX["DR 42"]["normalization"].replace("ð", "þ")

# ---- bilderna ----------------------------------------------------------------------------------------
FILES = commons.wikidata_files(["G 88", "U 729", "DR 196"])
INFO = commons.commons_info([FILES[s] for s in FILES])
CREDIT = {"G 88": ("Helena Bonnevier", "CC BY-SA 4.0"), "U 729": ("Bengt A. Lundberg", "CC BY 2.5 se"), "DR 196": ("Stephen", "Public domain")}


def photo(signum: str, text: str, lang: str = "sv") -> str:
    img = {**INFO[FILES[signum]], "signum": signum}
    assert (img["author"], img["licence"]) == CREDIT[signum], (signum, img["author"], img["licence"])
    cap = commons.caption(img, lang)
    word = "Foto" if lang == "sv" else "Photo"
    assert cap.startswith(f"{signum}. {word}: ")
    alt = f"Runstenen {signum}" if lang == "sv" else f"The runestone {signum}"
    return f"![{alt}]({img['thumb']})\n{text} {word}: {cap[len(signum) + len(word) + 4:]}"


PH_KYL = photo("G 88", "Kylverstenen (G 88) från Gotland, omkring år 400: hela runraden, den äldre futharken, huggen i en gravhäll – den äldsta kompletta i Norden.")
PH_AGE = photo("U 729", "Ågerstastenen (U 729) i Uppland: ”Här skall stenen stå mellan byarna.”")
PH_KRA = photo("DR 196", "Spjutskaftet från Kragehul på Fyn, 400-talet: ”Jag, Asgisls eril, kallas …”. Trä överlever bara där marken är vattendränkt, som i Kragehuls mosse.")
PH_KYL_EN = photo("G 88", "The Kylver stone (G 88) from Gotland, around AD 400: the whole rune row, the older futhark, cut into a grave slab – the oldest complete one in the North.", "en")
PH_AGE_EN = photo("U 729", "The Ågersta stone (U 729) in Uppland: “Here the stone shall stand between the villages.”", "en")
PH_KRA_EN = photo("DR 196", "The spear shaft from Kragehul on Funen, fifth century: “I, Ásgísl's eril, am called …”. Wood survives only where the ground is waterlogged, as in the Kragehul bog.", "en")

K = {"minnesinskrift": ("Minnesinskrift (efter någon)", "Memorial (in memory of someone)"), "namn/ägare": ("Namn eller ägare", "A name or an owner"),
     "bön/religiös": ("Bön eller kristet innehåll", "Prayer or Christian content"), "futhark": ("Runraden (futharken)", "The rune row (futhark)"),
     "besvärjelse/skydd": ("Besvärjelse eller skydd", "Charm or protection"), "tillverkare/ristare": ("Tillverkaren eller ristaren", "The maker or the carver"),
     "meddelande/annat": ("Meddelande eller annat", "A message or other"), "oläsligt": ("Oläsligt", "Illegible")}
ORDER = ["minnesinskrift", "namn/ägare", "meddelande/annat", "futhark", "bön/religiös", "besvärjelse/skydd", "tillverkare/ristare", "oläsligt"]


def chart(lang: str) -> str:
    sw = lang == "sv"
    groups = [("V|sten", "Vikingatidens stenar", "Viking-age stones"), ("V|ben/horn", "Vikingatidens ben och horn", "Viking-age bone and antler"),
              ("V|metall", "Vikingatidens metall (mynt, bleck, spännen)", "Viking-age metal (coins, sheets, brooches)"), ("M|trä", "Medeltidens trä (Bergen, Trondheim, Lödöse)", "Medieval wood (Bergen, Trondheim, Lödöse)")]
    lines = [f":::chart {'Vad texten gör, per material' if sw else 'What the text does, by material'}"]
    for key, gs, ge in groups:
        n = S[key]["n"]
        lines.append(f"# {gs if sw else ge} ({sv(n) if sw else en_n(n)} {'inskrifter' if sw else 'inscriptions'})")
        kinds = sorted(((k, v) for k, v in S[key]["kinds"].items() if k != "oläsligt"), key=lambda kv: -kv[1])[:4]
        for i, (k, v) in enumerate(kinds):
            lines.append(f"{'+' if i == 0 else ''}{K[k][0] if sw else K[k][1]} | {pr(v / n)} | {sv(v) if sw else en_n(v)} {'av' if sw else 'of'} {sv(n) if sw else en_n(n)}")
    lines.append("Källa: Samnordisk runtextdatabas 3.1, alla inskrifter och länder; en klass per inskrift, Vitkis grova indelning efter orden i normaliseringen och översättningen. Oläsliga inskrifter ingår i nämnaren." if sw else
                 "Source: Scandinavian Runic-text Database 3.1, all inscriptions and countries; one class per inscription, Vitki's rough division by the words of the normalisation and the translation. Illegible inscriptions are in the denominator.")
    lines.append(":::")
    return "\n".join(lines)


CHART, CHART_EN = chart("sv"), chart("en")
title = "Varför sten?"
summary = ("Runor ristades i trä, ben och metall lika gärna som i sten, men det är stenen som har överlevt. Visste de som högg "
           "att den skulle göra det? Trettiotvå vikingatida stenar säger det själva. Vi räknade vad som skrevs på vilket material "
           "– och fann att materialet valde orden. Och vi själva: vad av det vi skriver i dag finns kvar om tusen år?")
title_en = "Why Stone?"
summary_en = ("Runes were cut into wood, bone and metal as readily as into stone, but it is the stone that has survived. Did those "
              "who cut them know it would? Thirty-two Viking-age stones say so themselves. We counted what was written on which "
              "material – and found that the material chose the words. And ourselves: what of what we write today will remain in a thousand years?")

body = f"""Det vi har kvar är inte det som skrevs. Det är det som tålde marken. Samnordisk runtextdatabas rymmer {sv(M['n_total'])} runinskrifter från hela Norden och från utlandet, och av vikingatidens är {sv(MB['V']['sten'])} huggna i sten mot {MB['V']['trä']} skurna i trä. Ingen tror att förhållandet var sådant när de skrevs. Trä var det billiga, lätta materialet, det man hade i handen; sten var det tunga. Så frågan är inte bara vad de skrev, utan om de visste att bara det ena skulle vara kvar – och vad de i så fall valde att lägga i sten.

## Det som inte finns kvar

Trä och ben överlever bara där marken är blöt nog att stänga ute luften. Därför kommer vikingatidens {MB['V']['trä']} träinskrifter från en handfull platser – {PL['V|trä']['Folkebibliotekstomta']} från en utgrävning i Trondheim, några från Hedeby, Sigtuna, Oseberg och Dublin – och nästan alla medeltidens {sv(MB['M']['trä'])} från stadslagren i Bergen ({PL['M|trä']['Bryggen']} bara från Bryggen), Trondheim och Lödöse. Benen kommer från Sigtuna ({PL['V|ben/horn']['Sigtuna']}) och Lund ({PL['V|ben/horn']['Lund']}). Det är inte en bild av var man skrev på trä utan av var en brand eller ett vattensjukt kvarter råkade bevara det.

{PH_KRA}

Det betyder att en fråga inte går att besvara med siffror: om trä var vanligare än sten på vikingatiden, och hur mycket. Men två andra går. Vad skrev man på de olika materialen där båda finns kvar? Och sade stenarna själva något om varför de var sten?

## Materialet valde orden

Vi tog alla läsbara inskrifter och gav var och en en grov klass efter vad texten gör: minns någon, nämner ett namn eller en ägare, ber, skriver runraden, besvärjer, säger vem som gjorde föremålet, eller meddelar något annat.

{CHART}

Skillnaden är inte en nyans utan en annan sorts skrift. På vikingatidens stenar är {share('V|sten', 'minnesinskrift')} procent minnesinskrifter – *N reste stenen efter M* – och den typiska texten är {S['V|sten']['median_words']} ord lång. På samma tids ben är den typiska texten {S['V|ben/horn']['median_words']} ord: ett namn ({share('V|ben/horn', 'namn/ägare')} procent), en övning på runraden ({share('V|ben/horn', 'futhark')} procent) eller en uppmaning som den på ett revben från Sigtuna, *Rað þu!*, ”tyd du!”. Metallen bär till {share('V|metall', 'namn/ägare')} procent bara namn, mest för att myntmästarna i Lund satte sina på mynten: *Þorsten i Lundi*. Och de få träpinnarna säger vem som ristade – *Saxi risti runaR þessaR* på en pinne från Roskilde hamn – eller något så vardagligt som orden på en träslå från Trondheim: *Vindauga lokað*, fönstret stängt.

Medeltidens trä från Bergen visar vad vikingatidens trä måste ha varit fullt av: namn och ägarmärken ({share('M|trä', 'namn/ägare')} procent, {M['m_wood_objects']['märklapp']} av föremålen är märklappar till varor), böner ({share('M|trä', 'bön/religiös')} procent), meddelanden ({share('M|trä', 'meddelande/annat')} procent) – *Kyss þú mik*, kyss mig, på en svarvad skål, och brev där *Sire Jón sendir Gunnari Hvít kveðju Guðs ok sína*, herr Jon sänder Gunnar Vit Guds och sin hälsning. Trä var för det som skulle sägas en gång, till en person, nu. Sten var för det som skulle sägas till alla, och länge.

Ben och trä är nästan tomma på minnesinskrifter. Av vikingatidens {sv(MB['V']['ben/horn'] + MB['V']['trä'])} inskrifter i ben och trä är {cnt('V|ben/horn', 'minnesinskrift') + cnt('V|trä', 'minnesinskrift')} minnesinskrifter. Att minnas en död gjorde man i sten, inte för att man inte kunde skriva det på en pinne, utan för att en pinne inte var poängen.

## Visste de?

Ja. De skrev det. {M['n_stand']} av vikingatidens {sv(M['n_v_stones'])} stenar säger uttryckligen att de ska stå kvar, och några säger hur länge.

{PH_AGE}

> *Hiær mun standa stæinn miþli byia.* – Här skall stenen stå mellan byarna. (U 729, Ågersta)

> *Þy mun goþs manns um gætit verþa, meþan stæinn lifiR ok stafiR runa.* – Så skall den gode mannen bli ihågkommen, så länge stenen lever och runornas stavar. (Sm 16, Nöbbele)

> *Þæt skal at minnum manna, meþan mænn lifa.* – Det skall vara till människors minne, så länge människor lever. (U 114, Runby)

> *E mun standa, mæþ sten lifiR, witrind su.* – Alltid skall det stå, så länge stenen lever, detta vittnesbörd. (DR 212, Tillitse)

> *Æi meþan verald vakiR, liggR mærki hiar.* – Så länge världen vakar ligger märket här. (G 343, Visby)

Stenen vid Års på Jylland talar i egen person: *Sten kwæþsk hersi standa længi*, stenen säger sig stå här länge (DR 131). Rökstenen börjar med orden *Aft Vamoþ standa runaR þaR*, efter Vämod står dessa runor (Ög 136), och vid Randbøl på Jylland säger en sten att *þeR stafaR munu Þorgunni miok længi lifa*, dessa stavar skall leva mycket länge för Torgunn (DR 40). De visste. Stenen *lever*, säger två av dem, och stavarna lever, säger en tredje – ett märkligt ord om ett material som valdes just för att det inte gör det.

Och de visste var. *Hiær mun standa stæinn næR brautu*, här skall stenen stå nära vägen (U 707); *a þingstaþi*, på tingsplatsen (Sö 137); *a biargi*, på berget (DR 296); *miþli byia*, mellan byarna (U 729). Platsen är en del av budskapet: där människor går förbi, ser och läser. En runpinne lades i en hand. En sten ställdes där alla skulle gå.

## När valde man sten?

Sten var inte något som kom. De äldsta inskrifterna i Norden, från 100-talet till 600-talet, är {MB['U']['metall']} i metall – brakteater, spännen, vapen, med namn och besvärjelser som *laþu, laukaz, alu* – men också {MB['U']['sten']} i sten, de flesta daterade efter Imers kronologi till tiden mellan omkring 160 och 700, några in på 700-talet. Kylverstenen på Gotland har hela runraden huggen i en gravhäll redan omkring år 400.

{PH_KYL}

Det som kom var inte stenen utan seden att låta den tala om en död: minnesstenen. Blekingestenarna på 600-talet och Rök på 800-talet har den, och under ett par hundra år omkring år 1000 reser Norden {sv(MB['V']['sten'])} av dem, fler än allt annat som skrivits med runor tillsammans. Sedan tar det slut, och stenen byter rum: medeltidens {MB['M']['sten']} steninskrifter sitter i kyrkan – gravhällar, murstenar, dopfuntar, klockor – och säger den döde ett *Ave Maria* eller tillverkarens namn, medan {share('M|sten', 'minnesinskrift')} procent längre är minnesinskrifter av det gamla slaget. Minnet flyttade in under kyrkgolvet. Vardagen fortsatte i trä, som den rimligen alltid gjort, och det är därför Bergens tusen pinnar ser ut som de gör.

Så svaret på frågan när man valde sten är: alltid, för det som skulle stå kvar. Det som ändrades var vad man ville skulle stå kvar. Några hundra år ville man att det skulle vara en människas namn vid vägen, utan präst och utan kyrka, med ett löfte om att stenen skulle leva så länge människor lever. Det löftet har hållit i tusen år, och det är det enda löfte från vikingatiden vi kan kontrollera.

## Och vi?

Det är lätt att se på dem med överseende: de trodde att stenen skulle leva. Men vänd frågan. Vad av det vi skriver i dag kommer någon att kunna läsa om tusen år?

Inte cd-skivan. Skivor som brändes på 1990-talet är redan i många fall oläsliga; det färgade skiktet bleknar, lagren släpper, och dessutom finns snart ingen spelare. Inte hårddisken, inte molnet: det som ligger där finns kvar bara så länge någon betalar för strömmen och kopierar över det till nästa format, vart tionde år, utan avbrott, i hundra generationer. Våra fotografier är fler än alla tidigare släktleds tillsammans, och de flesta av dem kommer att försvinna med ett konto som ingen längre loggar in på. Boken klarar sig bättre, men papper från 1900-talet gulnar och spricker av sitt eget syra, och det är pergamentet och kalvskinnet, inte pocketboken, som har visat sig hålla i tusen år. Det vi har gjort är att välja trä igen: det billiga, lätta materialet som rymmer allt och som ingen förväntar sig ska vara kvar.

Några har märkt det. På Svalbard ligger ett arkiv i en nedlagd gruva där text fotograferas på film som ska tåla fem hundra år i kyla; det är vår tids runsten, och den säger samma sak som Ågerstastenen: här skall det stå. Men det är ett undantag, och det är inte där vi skriver. Vikingatidens människor skrev också mest i trä, och de visste det. Skillnaden är att de hade ett material för det som skulle bestå och en bestämd idé om vad som förtjänade det: ett namn, en släkt, en plats vid vägen. *Deyr fé, deyja frændr*, fä dör, fränder dö, sade Hávamál, men eftermälet dör aldrig. Stenen var det ordet gjort i granit.

Så frågan går att ställa till oss, inte bara till dem. Om du fick välja ett budskap att hugga i sten, ett som människor skulle läsa om tusen år när allt annat är borta, utan dig att förklara det, utan din tid att sätta det i – vad skulle det vara? De som reste stenarna svarade med elva ord. De flesta valde någon annans namn.

:::box Det viktigaste i korthet
- Det bevarade är det som tålde marken: trä och ben finns kvar bara från blöta stadslager som Bergens, så förhållandet mellan sten och trä på vikingatiden går inte att räkna. Vad materialen användes till går däremot att se där båda finns.
- Materialet valde orden. Stenen bär minnet av en död ({share('V|sten', 'minnesinskrift')} procent av vikingatidens stenar), ben och trä bär namn, runrader, ägarmärken, brev och kyssar. Att minnas gjorde man i sten.
- De som högg visste att stenen skulle överleva: {M['n_stand']} vikingatida stenar säger det själva – ”så länge stenen lever”, ”så länge människor lever”, ”så länge världen vakar” – och de säger var: vid vägen, mellan byarna, på tinget.
- Stenen var alltid materialet för det som skulle bestå. Det som kom och gick var minnesstenen: under några hundra år ett namn vid vägen, sedan en gravhäll i kyrkan.
- Vi har valt trä igen. Cd-skivor, hårddiskar och moln lever så länge någon kopierar om dem; nästan inget av det vi skriver i dag är gjort för att läsas om tusen år, och vi har ingen bestämd idé om vad som skulle förtjäna det.
:::

:::box Så räknade vi
Alla {sv(M['n_total'])} inskrifter i Samnordisk runtextdatabas 3.1, alla länder, med databasens materialtyp (sten, trä, ben/horn, metall) och period (urnordisk tid, vikingatid, medeltid). Klasserna är en grov indelning efter orden i normaliseringen och den engelska översättningen – minnesformeln *æftiR*, ord för Gud och Kristus, runraden, *alu* och andra besvärjelseord, ”gjorde” och ”ristade”, ägarformler – en klass per inskrift i fast ordning; en inskrift utan läsbara ord räknas som oläslig och ingår i nämnaren. Stenar som säger att de ska stå räknades med en ordlista (*standa, stændr, mæþan, aldri, længi, lifiR, minnum*) och lästes en och en. Dateringarna är Rundatas, för de äldsta stenarna efter Imer 2007. Allt är beskrivande, inga test, och ligger öppet i kodförrådet (utdata/material).
:::

## Källor

- Samnordisk runtextdatabas, version 3.1 (ODbL).
- Imer, L. M. 2007. *Runer og runeindskrifter. Kronologi, kontekst og funktion i Skandinaviens jernalder og vikingetid.* Diss. Københavns Universitet.
- Barnes, M. P. 2012. *Runes: A Handbook.* Woodbridge.
- Foton: se bildtexterna."""

body_en = f"""What we have left is not what was written. It is what the ground could bear. The Scandinavian Runic-text Database holds {en_n(M['n_total'])} runic inscriptions from the whole North and from abroad, and of the Viking Age's, {en_n(MB['V']['sten'])} are cut in stone against {MB['V']['trä']} carved in wood. No one believes the proportion was like that when they were written. Wood was the cheap, light material, the one in your hand; stone was the heavy one. So the question is not only what they wrote, but whether they knew that only one of the two would remain – and what, in that case, they chose to put in stone.

## What is not left

Wood and bone survive only where the ground is wet enough to keep the air out. That is why the Viking Age's {MB['V']['trä']} wood inscriptions come from a handful of places – {PL['V|trä']['Folkebibliotekstomta']} from one excavation in Trondheim, a few from Hedeby, Sigtuna, Oseberg and Dublin – and nearly all of the Middle Ages' {en_n(MB['M']['trä'])} from the town layers of Bergen ({PL['M|trä']['Bryggen']} from Bryggen alone), Trondheim and Lödöse. The bones come from Sigtuna ({PL['V|ben/horn']['Sigtuna']}) and Lund ({PL['V|ben/horn']['Lund']}). This is not a picture of where people wrote on wood but of where a fire or a waterlogged quarter happened to preserve it.

{PH_KRA_EN}

That means one question cannot be answered with numbers: whether wood was more common than stone in the Viking Age, and by how much. But two others can. What did people write on the different materials where both survive? And did the stones themselves say anything about why they were stone?

## The material chose the words

We took every legible inscription and gave each one a rough class by what the text does: remembers someone, names a person or an owner, prays, writes the rune row, charms, says who made the object, or communicates something else.

{CHART_EN}

The difference is not a shade but another kind of writing. On the Viking Age's stones, {share('V|sten', 'minnesinskrift')} per cent are memorials – *N raised the stone in memory of M* – and the typical text is {S['V|sten']['median_words']} words long. On the same period's bones the typical text is {S['V|ben/horn']['median_words']} words: a name ({share('V|ben/horn', 'namn/ägare')} per cent), a practice of the rune row ({share('V|ben/horn', 'futhark')} per cent), or a challenge like the one on a rib from Sigtuna, *Rað þu!*, “interpret this!”. Metal carries names alone in {share('V|metall', 'namn/ägare')} per cent of cases, mostly because the moneyers of Lund put theirs on the coins: *Þorsten i Lundi*. And the few wooden sticks say who carved – *Saxi risti runaR þessaR* on a stick from Roskilde harbour – or something as everyday as the words on a wooden bolt from Trondheim: *Vindauga lokað*, window closed.

The medieval wood from Bergen shows what the Viking Age's wood must have been full of: names and owner's marks ({share('M|trä', 'namn/ägare')} per cent, {M['m_wood_objects']['märklapp']} of the objects are labels for goods), prayers ({share('M|trä', 'bön/religiös')} per cent), messages ({share('M|trä', 'meddelande/annat')} per cent) – *Kyss þú mik*, kiss me, on a turned bowl, and letters where *Sire Jón sendir Gunnari Hvít kveðju Guðs ok sína*, Sir Jón sends Gunnar White God's greeting and his own. Wood was for what was to be said once, to one person, now. Stone was for what was to be said to everyone, and for a long time.

Bone and wood are almost empty of memorials. Of the Viking Age's {en_n(MB['V']['ben/horn'] + MB['V']['trä'])} inscriptions in bone and wood, {cnt('V|ben/horn', 'minnesinskrift') + cnt('V|trä', 'minnesinskrift')} are memorials. Remembering the dead was done in stone, not because it could not be written on a stick, but because a stick was not the point.

## Did they know?

Yes. They wrote it. {M['n_stand']} of the Viking Age's {en_n(M['n_v_stones'])} stones say explicitly that they are to remain standing, and some say for how long.

{PH_AGE_EN}

> *Hiær mun standa stæinn miþli byia.* – Here the stone shall stand between the villages. (U 729, Ågersta)

> *Þy mun goþs manns um gætit verþa, meþan stæinn lifiR ok stafiR runa.* – So the good man will be remembered, as long as the stone lives and the staves of the runes. (Sm 16, Nöbbele)

> *Þæt skal at minnum manna, meþan mænn lifa.* – This shall be in memory of men, as long as men live. (U 114, Runby)

> *E mun standa, mæþ sten lifiR, witrind su.* – Ever shall it stand, as long as the stone lives, this testimony. (DR 212, Tillitse)

> *Æi meþan verald vakiR, liggR mærki hiar.* – As long as the world wakes, the monument lies here. (G 343, Visby)

The stone at Års in Jutland speaks in its own person: *Sten kwæþsk hersi standa længi*, the stone declares that it will stand here long (DR 131). The Rök stone begins with the words *Aft Vamoþ standa runaR þaR*, in memory of Vámóðr stand these runes (Ög 136), and at Randbøl in Jutland a stone says that *þeR stafaR munu Þorgunni miok længi lifa*, these staves will live very long for Þorgunnr (DR 40). They knew. The stone *lives*, two of them say, and the staves live, says a third – a strange word for a material chosen precisely because it does not.

And they knew where. *Hiær mun standa stæinn næR brautu*, here the stone shall stand near the road (U 707); *a þingstaþi*, at the assembly place (Sö 137); *a biargi*, on the hill (DR 296); *miþli byia*, between the villages (U 729). The place is part of the message: where people pass, see and read. A rune stick was put into a hand. A stone was set where everyone would walk.

## When was stone chosen?

Stone was not something that arrived. The oldest inscriptions in the North, from the second century to the seventh, are {MB['U']['metall']} in metal – bracteates, brooches, weapons, with names and charms such as *laþu, laukaz, alu* – but also {MB['U']['sten']} in stone, most of them dated by Imer's chronology to the time between about 160 and 700, a few into the eighth century. The Kylver stone on Gotland has the whole rune row cut into a grave slab as early as about AD 400.

{PH_KYL_EN}

What arrived was not the stone but the custom of letting it speak of a dead person: the memorial stone. The Blekinge stones of the seventh century and Rök in the ninth have it, and in a couple of centuries around the year 1000 the North raises {en_n(MB['V']['sten'])} of them, more than everything else ever written in runes put together. Then it ends, and the stone changes room: the Middle Ages' {MB['M']['sten']} stone inscriptions sit in the church – grave slabs, wall stones, fonts, bells – and say an *Ave Maria* for the dead or the maker's name, while only {share('M|sten', 'minnesinskrift')} per cent are still memorials of the old kind. Memory moved in under the church floor. Everyday life went on in wood, as it presumably always had, and that is why Bergen's thousand sticks look the way they do.

So the answer to when stone was chosen is: always, for what was to remain. What changed was what people wanted to remain. For a few hundred years they wanted it to be a person's name by the road, without priest and without church, with a promise that the stone would live as long as people live. That promise has held for a thousand years, and it is the only promise from the Viking Age we can check.

## And we?

It is easy to look at them indulgently: they believed the stone would live. But turn the question around. What of what we write today will anyone be able to read in a thousand years?

Not the CD. Discs burned in the 1990s are already in many cases unreadable; the dye layer fades, the layers come apart, and soon there is no player anyway. Not the hard drive, not the cloud: what lies there remains only as long as someone pays for the electricity and copies it over to the next format, every ten years, without interruption, for a hundred generations. Our photographs outnumber those of all earlier generations together, and most of them will vanish with an account no one logs into any more. The book fares better, but twentieth-century paper yellows and cracks from its own acid, and it is parchment and vellum, not the paperback, that have proved to last a thousand years. What we have done is choose wood again: the cheap, light material that holds everything and that no one expects to remain.

Some have noticed. On Svalbard an archive lies in a closed mine where text is photographed onto film meant to withstand five hundred years of cold; it is our age's runestone, and it says the same thing as the Ågersta stone: here it shall stand. But it is an exception, and it is not where we write. The people of the Viking Age also wrote mostly in wood, and they knew it. The difference is that they had a material for what was to last and a definite idea of what deserved it: a name, a family, a place by the road. *Deyr fé, deyja frændr*, cattle die, kinsmen die, said Hávamál, but a reputation never dies. The stone was that word made in granite.

So the question can be put to us, not only to them. If you could choose one message to cut in stone, one that people would read in a thousand years when everything else is gone, without you to explain it, without your time to set it in – what would it be? Those who raised the stones answered in eleven words. Most of them chose someone else's name.

:::box The essentials in brief
- What survives is what the ground could bear: wood and bone remain only from wet town layers like Bergen's, so the proportion of stone to wood in the Viking Age cannot be counted. What the materials were used for can be seen where both exist.
- The material chose the words. Stone carries the memory of a dead person ({share('V|sten', 'minnesinskrift')} per cent of the Viking Age's stones); bone and wood carry names, rune rows, owner's marks, letters and kisses. Remembering was done in stone.
- Those who cut them knew the stone would outlast them: {M['n_stand']} Viking-age stones say so themselves – “as long as the stone lives”, “as long as men live”, “as long as the world wakes” – and they say where: by the road, between the villages, at the assembly.
- Stone was always the material for what should last. What came and went was the memorial stone: for a few hundred years a name by the road, then a grave slab in the church.
- We have chosen wood again. CDs, hard drives and clouds live as long as someone recopies them; almost nothing we write today is made to be read in a thousand years, and we have no definite idea of what would deserve it.
:::

:::box How we counted
All {en_n(M['n_total'])} inscriptions in the Scandinavian Runic-text Database 3.1, every country, with the database's material type (stone, wood, bone/antler, metal) and period (Proto-Norse, Viking Age, Middle Ages). The classes are a rough division by the words of the normalisation and the English translation – the memorial formula *æftiR*, words for God and Christ, the rune row, *alu* and other charm words, “made” and “carved”, owner's formulas – one class per inscription in a fixed order; an inscription without legible words counts as illegible and stays in the denominator. Stones that say they will stand were found with a word list (*standa, stændr, mæþan, aldri, længi, lifiR, minnum*) and read one by one. The datings are Rundata's, for the oldest stones after Imer 2007. Everything is descriptive, no tests, and lies open in the repository (utdata/material).
:::

## Sources

- Scandinavian Runic-text Database, version 3.1 (ODbL).
- Imer, L. M. 2007. *Runer og runeindskrifter. Kronologi, kontekst og funktion i Skandinaviens jernalder og vikingetid.* Diss. University of Copenhagen.
- Barnes, M. P. 2012. *Runes: A Handbook.* Woodbridge.
- Photos: see the captions."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M)
assert body.count("## ") == body_en.count("## ")
VOICE = re.findall(r"[^.!?]*\b(?:jag|mig|min)\b[^.!?]*", body, re.I)
assert len(VOICE) == 2 and "Jag, Asgisls eril" in VOICE[0] and "kyss mig" in VOICE[1], VOICE  # bara citerade inskrifter, inte vår röst
out = {"slug": "varfor-sten", "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Formler och syfte", "Norden"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "material.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "material.json"), len(body.split()), "ord sv,", len(body_en.split()), "ord en")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and old.get("slug") == out["slug"] and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    else:
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Material|sten", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
