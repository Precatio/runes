"""Bygger data/rundata.json från Samnordisk runtextdatabas (Rundata).

Källa: Samnordisk runtextdatabas, Institutionen för nordiska språk, Uppsala universitet.
Licens: Open Database License (databasen) / Database Contents License (innehållet).
Källan ska anges och länkas när uppgifterna används.

Kör från projektroten:
    .venv/bin/python -m scripts.build_rundata            # laddar ner srd2014.zip
    .venv/bin/python -m scripts.build_rundata --zip PATH # använder en lokal kopia
"""
import argparse
import datetime
import io
import json
import os
import re
import urllib.request
import zipfile

import xlrd
from pyproj import Transformer

SOURCE_URL = "http://www.runforum.nordiska.uu.se/filer/srd2014.zip"
ATTRIBUTION = (
    "Samnordisk runtextdatabas, Institutionen för nordiska språk, Uppsala universitet "
    "(www.nordiska.uu.se/forskn/samnord.htm). Licens: ODbL / DbCL."
)
OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rundata.json")

TEXT_FILES = {
    "RUNTEXT": "transliteration",
    "FORNSPR": "normalization",      # nationellt fornspråk (runsvenska, rundanska, fornvästnordiska)
    "FVN": "normalization_ows",       # fornvästnordisk normalisering
    "ENGLISH": "translation_en",
}

CARVER_RE = re.compile(r"([^;,()]+?)\s*\((S|A|P|L)\)")
NEGATED_RE = re.compile(r"\b(knappast|ej|inte)\b", re.IGNORECASE)
LEADING_RE = re.compile(r"^(och|samt|tillsammans med|tillsammans)\s+", re.IGNORECASE)
UNCERTAIN_RE = re.compile(r"\b(troligen|eventuellt|möjligen|kanske|osäker)\b|\?", re.IGNORECASE)
WGS_RE = re.compile(r"\(\s*(-?\d+(?:\.\d+)?)\s*;\s*(-?\d+(?:\.\d+)?)\s*\)")
RT90_RE = re.compile(r"^\s*(\d{7})\.(\d{7})\s*$")

# RT90 2.5 gon V (Rikets nät) -> WGS84
_rt90 = Transformer.from_crs("EPSG:3021", "EPSG:4326", always_xy=False)


def split_signum(raw: str):
    """'U 654 $ ' -> ('U 654', {'new_reading': True, ...}, alias_target_or_None)."""
    parts = raw.strip().split()
    base = " ".join(parts[:2])
    rest = parts[2:]
    alias = None
    flags = {"lost": False, "new_reading": False, "medieval": False, "proto_norse": False, "post_medieval": False}
    for tok in rest:
        if tok.startswith("="):
            alias = tok[1:].replace("_", " ")
            continue
        if tok == "SENTIDA":
            flags["post_medieval"] = True
            continue
        flags["lost"] |= "†" in tok
        flags["new_reading"] |= "$" in tok
        flags["medieval"] |= "M" in tok
        flags["proto_norse"] |= "U" in tok
    return base, flags, alias


def parse_coords(value: str):
    value = (value or "").strip()
    if not value:
        return None
    m = RT90_RE.match(value)
    if m:
        lat, lon = _rt90.transform(float(m.group(1)), float(m.group(2)))
        return round(lat, 6), round(lon, 6)
    m = WGS_RE.search(value)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return round(lat, 6), round(lon, 6)
    return None


def parse_carvers(value: str):
    carvers = []
    for m in CARVER_RE.finditer(value or ""):
        name = LEADING_RE.sub("", m.group(1).strip())
        if NEGATED_RE.search(name):
            continue
        uncertain = bool(UNCERTAIN_RE.search(name))
        name = UNCERTAIN_RE.sub("", name).strip(" ,.;")
        if name:
            carvers.append({"name": name, "kind": m.group(2), "uncertain": uncertain})
    return carvers


def parse_period(value: str):
    v = (value or "").strip()
    if v[:1] in ("U", "V", "M"):
        return v[:1]
    return None


def parse_style(value: str):
    v = (value or "").strip()
    m = re.match(r"^(RAK|Fp|KB|Pr[1-5])(\?)?$", v)
    if m:
        return m.group(1), bool(m.group(2))
    return (v or None), True if v else False


def read_text_file(data: bytes):
    """Returnerar {grundsignum: text}. Rader börjar med signum + flaggor, följt av texten."""
    out = {}
    text = data.decode("utf-8-sig")
    for line in text.splitlines():
        if not line or line.startswith("!"):
            continue
        parts = line.split(" ")
        if len(parts) < 2:
            continue
        base = f"{parts[0]} {parts[1]}"
        rest = parts[2:]
        # Hoppa över flaggtoken (†, $, M, U och kombinationer, SENTIDA, =alias)
        while rest and (rest[0] == "" or re.fullmatch(r"[†$MU]+", rest[0]) or rest[0] == "SENTIDA" or rest[0].startswith("=")):
            if rest[0].startswith("="):
                rest = []
                break
            rest = rest[1:]
        body = " ".join(rest).strip()
        if body:
            out[base] = body
    return out


def build(zip_bytes: bytes):
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    sheet = xlrd.open_workbook(file_contents=zf.read("RUNDATA.xls")).sheet_by_index(0)
    col = {sheet.cell_value(0, c): c for c in range(sheet.ncols)}

    def cell(r, name):
        return str(sheet.cell_value(r, col[name])).strip()

    texts = {field: read_text_file(zf.read(name)) for name, field in TEXT_FILES.items()}

    inscriptions = []
    aliases = {}
    for r in range(1, sheet.nrows):
        raw = sheet.cell_value(r, 0)
        base, flags, alias = split_signum(raw)
        if alias:
            aliases[base] = alias
            continue
        coords = parse_coords(cell(r, "Nuv. koord.")) or parse_coords(cell(r, "Koordinater"))
        style, style_uncertain = parse_style(cell(r, "Stilgruppering"))
        rec = {
            "signum": base,
            "flags": flags,
            "place": cell(r, "Plats"),
            "parish": cell(r, "Socken"),
            "district": cell(r, "Härad"),
            "municipality": cell(r, "Kommun"),
            "placement": cell(r, "Placering"),
            "lat": coords[0] if coords else None,
            "lon": coords[1] if coords else None,
            "rune_types": cell(r, "Runtyper"),
            "cross_form": cell(r, "Korsform"),
            "dating": cell(r, "Period/Datering"),
            "period": parse_period(cell(r, "Period/Datering")),
            "style": style,
            "style_uncertain": style_uncertain,
            "carver_raw": cell(r, "Ristare"),
            "carvers": parse_carvers(cell(r, "Ristare")),
            "material_type": cell(r, "Materialtyp"),
            "material": cell(r, "Material"),
            "object": cell(r, "Föremål"),
            "other": cell(r, "Övrigt"),
            "alt_signum": cell(r, "Alternativt signum"),
            "references": cell(r, "Referens"),
            "image_link": cell(r, "Bildlänk"),
        }
        for field, by_signum in texts.items():
            rec[field] = by_signum.get(base, "")
        inscriptions.append(rec)

    return {
        "meta": {
            "source": "Samnordisk runtextdatabas 2014 (RUNDATA.xls uppdaterad 2018)",
            "source_url": SOURCE_URL,
            "attribution": ATTRIBUTION,
            "license": "ODbL-1.0 / DbCL-1.0",
            "built": datetime.date.today().isoformat(),
            "count": len(inscriptions),
        },
        "inscriptions": inscriptions,
        "aliases": aliases,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", help="Lokal sökväg till srd2014.zip")
    ap.add_argument("--out", default=OUT_PATH)
    args = ap.parse_args()

    if args.zip:
        with open(args.zip, "rb") as f:
            data = f.read()
    else:
        print(f"Laddar ner {SOURCE_URL} ...")
        with urllib.request.urlopen(SOURCE_URL, timeout=120) as resp:
            data = resp.read()

    result = build(data)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
    with_coords = sum(1 for i in result["inscriptions"] if i["lat"] is not None)
    print(f"Skrev {args.out}: {result['meta']['count']} inskrifter ({with_coords} med koordinater), "
          f"{len(result['aliases'])} alias.")


if __name__ == "__main__":
    main()
