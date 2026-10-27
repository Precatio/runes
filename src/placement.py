"""Om en runsten står där den restes, enligt Rundatas placeringstext: används av appens flyttregel
(src/r_bridge.is_moved) och av fynden per sten (src/stone_findings). Rundata har ingen flyttflagga; placeringen är en
fri text om var stenen står i dag, och platsen är fyndplatsen. En sten räknas som flyttad när placeringen säger att den
flyttats ('Flyttad 100 m åt N', 'förd till Eskilstuna') eller nämner en annan plats än fyndplatsen (ett annat ortnamn,
en annan socken, en annan sten som står någon annanstans), men inte när den bara beskriver var på platsen stenen står
(väderstreck och avstånd, gårdsplanen, byn, en väg eller en bäck) eller när stenen har förts tillbaka ('Återfördes till
Brobybro 1955'). Ett fåtal texter är avgjorda för hand (PLACEMENT_CHECKED, med skälen). METHODS.md 1q och 17."""
from __future__ import annotations

import re

PLACEMENT_CHECKED = {
    "Sö 308": True,         # 'I planteringen utanför järnvägsstationen.' – the station's planting, not the road where found
    "Sö Fv1986;220": True,  # 'Fornhöjdens vårdcentrum' – a health centre
    "U 323": True,          # 'Skånelaholm' – the manor, not Sälna
    "Vg NOR1997;28": True,  # 'Ekehagens forntidsby' – an open-air museum
    "U 385": True,          # 'Sitter i en mur i V delen av ruinen.' – built into a wall
    "U 491": True,          # 'Inmurat i källaren vid Årby.' – built into a cellar
    "Sm 76": False,         # 'I Gästgivaregårdens trädgård.' – the inn's garden; not said to be away from Komstad
    "U 1079": False,        # 'En del i Sundbro, fyra i Forkarby.' – four of the five pieces are at the find place
    "Sm 80": True,          # 'Vid Vallsjö herrgård.' – the manor, not Vallsjö stomhemman where the stone was found
    "U Fv1992;157": True,   # 'I inrikeshallen Arlanda 2.' – the terminal hall, not the field on Måby land
}
_STONE_REF = re.compile(r"(?<![A-Za-zÅÄÖåäö])(U|Sö|Ög|Öl|Vg|Sm|Gs|Vs|Nä|Hs|M|Ån|D|Hr|J|Lp|Ds|Bo|G|DR|N)\s?(\d{1,4})(?!\d)")
_NAME = re.compile(r"[A-ZÅÄÖ][\wåäöé-]+")
# Compass points and distances describe where a stone stands at its place ('3,5 m ONO om Sö 140', '160 m NNV
# mangårdsbyggnaden', '400 m N Söderby gård'), not that it was moved
_COMPASS = re.compile(r"^(?:[NSÖVO]{1,3})$")
_RELATIVE = re.compile(r"\d+(?:,\d+)?\s*(?:m|km)\s+(?:åt\s+)?[NSÖVO]{1,3}\b", re.I)
# A stone brought back to where it stood ('Återfördes till Brobybro 1955', 'tillbaka till sin ursprungliga plats')
_RETURNED = re.compile(r"återför|tillbaka till sin ursprungliga|åter till .{0,40}ursprunglig plats(?!.*står vid)", re.I)
# A stone Rundata says was moved, even a short way ('Flyttad 100 m åt N', 'Flyttad över sockengränsen')
_SAID_MOVED = re.compile(r"\bflyttad|\bflyttades|\bförd till\b|\bnumera\b", re.I)
# Roads, streams, bridges and fields named in a placement are features of the site, not other places
_FEATURE = re.compile(r"\b(?:vägen|väg|bäcken|bäck|bron|ån|gravfältet|gravfält|åker|åkern)\b", re.I)


def placement_elsewhere(rec: dict, lookup=None) -> bool:
    """Om Rundatas placeringstext nämner en annan plats än fyndplatsen: ett ortnamn som inte ingår i platsen ('Vid
    Hummelsta, Stora Mellösa sn' för Tälje bro), en annan socken ('Vid Rosta kvarn, Bälinge sn' för en sten i Ärentuna)
    eller en annan sten som står någon annanstans ('Står vid Sö 109'). En text som bara beskriver hur stenen står ('På
    gårdsplanen', 'Rest vid den gamla vägen', 'Inmurat i källaren vid Årby' i Årby) räknas inte. Ett fåtal texter är
    avgjorda för hand (PLACEMENT_CHECKED)."""
    if rec["signum"] in PLACEMENT_CHECKED:
        return PLACEMENT_CHECKED[rec["signum"]]
    if lookup is None:
        from api.rundata import store
        lookup = store().get
    text = (rec.get("placement") or "").strip()
    if not text:
        return False
    if _RETURNED.search(text):
        return False
    if _SAID_MOVED.search(text):
        return True
    text = _RELATIVE.sub(" ", text)
    place = (rec.get("place") or "").lower()
    parish = set(re.findall(r"[\wåäöé-]+", (rec.get("parish") or "").lower()))
    parish |= {w[:-3] for w in parish if w.endswith("-sn")} | {re.sub(r"\s*sn$", "", (rec.get("parish") or "").lower())}
    for prefix, number in _STONE_REF.findall(text):
        other = lookup(f"{prefix} {number}")
        other_place = ((other or {}).get("place") or "").lower()
        if other and other is not rec and other_place and other_place not in place and place not in other_place:
            return True
    for sentence in re.split(r"[.;]\s*", _STONE_REF.sub(" ", text)):
        for m in _NAME.finditer(sentence):
            word = m.group(0).lower()
            if m.start() == 0 or len(word) < 2 or _COMPASS.match(m.group(0)):  # 'Vid', 'I', 'Nu'; 'V', 'ONO' for väderstreck
                continue
            if (word in parish and re.search(r"\bi\s+$", sentence[:m.start()])) \
                    or _FEATURE.search(sentence[max(0, m.start() - 25):m.end() + 12]):
                continue  # in the stone's own parish ('Vid ett gravfält i Husby-Oppunda'), a road or a stream
            if re.match(r"\s+sn\b", sentence[m.end():]):  # 'Bälinge sn': another parish
                if word not in parish:
                    return True
                continue
            stem = word[:-1] if word.endswith("s") and len(word) > 3 else word  # genitive 'Jönköpings'
            if word not in place and stem not in place:
                return True
    return False

