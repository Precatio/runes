"""Palms jordar (analysplaner/2026-11-08-palm-jordarna.md, sha 85a70fa3): SGU:s Jordarter 1:25 000–1:100 000
(INSPIRE, GeoSciML 4.1, CC BY 4.0) till ett nationellt rutnät om 100 m i SWEREF 99 TM, en jordartsklass per cell.
Steg 1 (klasser): alla jordartsnamn i de hämtade länen klassas enligt planen och skrivs i jordartsklasser.csv – innan
stenarna läggs över. Steg 2 (raster): varje karterad yta ritas med sin klass (stora ytor först, så att öar i dem
hamnar ovanpå); jordart_100m.tif (uint8) och jordart_100m.json (utsträckning, klasskoder).
    .venv/bin/python utdata/palm_jordarna/jordarter.py klasser
    .venv/bin/python utdata/palm_jordarna/jordarter.py raster"""
import csv
import glob
import json
import os
import re
import sys
import zipfile

import numpy as np
from lxml import etree
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/sgu_jord"
LAN = ["01", "03", "04", "05", "06", "07", "08", "09", "14", "17", "18", "19", "20", "21", "22"]
E0, E1, N0, N1, RES = 250000.0, 930000.0, 6120000.0, 7700000.0, 100.0
CLASSES = {1: "lera_silt", 2: "sand_grus", 3: "moran", 4: "torv_gyttja", 5: "berg", 6: "vatten", 7: "ovrigt"}
NS = {"gml": "http://www.opengis.net/gml/3.2", "gsmlb": "http://www.opengis.net/gsml/4.1/GeoSciML-Basic",
      "xlink": "http://www.w3.org/1999/xlink"}
G = "{%s}" % NS["gml"]
B = "{%s}" % NS["gsmlb"]
XL = "{%s}href" % NS["xlink"]


def classify(name: str) -> int:
    """The plan's rule: clay and silt = names with lera or silt (and gyttjelera, lergyttja), not moraines or weathering
    soil; then descriptive groups."""
    n = name.lower()
    if n == "vatten":
        return 6
    if (re.search(r"lera|silt|lergyttja", n)) and "morän" not in n and "vittringsjord" not in n:
        return 1
    if "morän" in n:
        return 3
    if "torv" in n or "gyttja" in n or "bleke" in n:
        return 4
    if "berg" in n:
        return 5
    if re.search(r"sand|grus|isälv|svall|älvsediment|klapper|sten|block|rullstens", n):
        return 2
    return 7


def gml_of(lan: str):
    z = zipfile.ZipFile(os.path.join(SRC, f"lan{lan}.zip"))
    name = next(n for n in z.namelist() if n.endswith(".gml"))
    return z.open(name)


def units(lan: str) -> dict[str, str]:
    """GeologicUnit gml:id → its name (SGU:s jordartsnamn)."""
    out = {}
    for _, el in etree.iterparse(gml_of(lan), events=("end",), tag=B + "GeologicUnit", huge_tree=True):
        nm = el.find(G + "name")
        out[el.get(G + "id")] = (nm.text or "").strip() if nm is not None else ""
        el.clear()
    return out


def rings(feature):
    """Exterior rings of a MappedFeature's surface as (E, N) arrays (posList is N E)."""
    out = []
    for pl in feature.iter(G + "posList"):
        parent = pl.getparent()
        if parent is None or parent.getparent() is None or parent.getparent().tag != G + "exterior":
            continue
        v = np.array(pl.text.split(), dtype=float).reshape(-1, 2)
        out.append(np.c_[v[:, 1], v[:, 0]])
    return out


def main(step):
    if step == "klasser":
        names = {}
        for lan in LAN:
            for gid, nm in units(lan).items():
                names[nm] = names.get(nm, 0) + 1
            print("län", lan, len(names), "namn hittills", flush=True)
        with open(os.path.join(HERE, "jordartsklasser.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["jordartsnamn", "klass", "klassnamn"])
            for nm in sorted(names):
                k = classify(nm)
                w.writerow([nm, k, CLASSES[k]])
        print(len(names), "namn klassade")
        return
    W, H = int((E1 - E0) / RES), int((N1 - N0) / RES)
    img = Image.new("L", (W, H), 0)
    draw = ImageDraw.Draw(img)
    for lan in LAN:
        cls = {gid: classify(nm) for gid, nm in units(lan).items()}
        polys = []
        for _, el in etree.iterparse(gml_of(lan), events=("end",), tag=B + "MappedFeature", huge_tree=True):
            spec = el.find(B + "specification")
            k = cls.get((spec.get(XL) or "").lstrip("#")) if spec is not None else None
            if k:
                for r in rings(el):
                    px = np.c_[(r[:, 0] - E0) / RES, (N1 - r[:, 1]) / RES].astype(np.float32)
                    area = abs(np.dot(px[:-1, 0], px[1:, 1]) - np.dot(px[1:, 0], px[:-1, 1])) / 2
                    polys.append((area, k, px))
            el.clear()
            while el.getprevious() is not None:
                del el.getparent()[0]
        polys.sort(key=lambda p: -p[0])
        for _, k, px in polys:
            if len(px) >= 3:
                draw.polygon([tuple(p) for p in px], fill=k)
        print("län", lan, len(polys), "ytor", flush=True)
        del polys
    img.save(os.path.join(HERE, "jordart_100m.tif"), compression="tiff_lzw")
    json.dump({"crs": "EPSG:3006", "xmin": E0, "xmax": E1, "ymin": N0, "ymax": N1, "res": RES, "width": W, "height": H,
               "classes": CLASSES, "source": "SGU, Jordarter 1:25 000–1:100 000 (INSPIRE), CC BY 4.0"},
              open(os.path.join(HERE, "jordart_100m.json"), "w"), ensure_ascii=False, indent=1)
    a = np.asarray(img)
    print({CLASSES.get(k, "ingen"): int((a == k).sum()) for k in range(8)})


if __name__ == "__main__":
    main(sys.argv[1])
