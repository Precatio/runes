"""Inzoomningen till artikeln: SGU:s jordarter (samma klasser som jordarter.py) ritade direkt ur vektordata i 10 m för ett
utsnitt, så att lerans kanter syns. Skriver jordart_zoom.tif och jordart_zoom.json (utsträckning).
    .venv/bin/python utdata/palm_jordarna/zoom_jord.py [x0 y0 storlek_m]   (standard: Täby–Vallentuna, 662000 6594000 20000)"""
import json
import os
import sys

import numpy as np
from lxml import etree
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jordarter as J  # noqa: E402

RES = 10.0
x0, y0, size = (float(a) for a in sys.argv[1:4]) if len(sys.argv) >= 4 else (662000.0, 6594000.0, 20000.0)
x1, y1 = x0 + size, y0 + size
W = H = int(size / RES)
img = Image.new("L", (W, H), 0)
draw = ImageDraw.Draw(img)
polys = []
for lan in ("01", "03"):
    cls = {gid: J.classify(nm) for gid, nm in J.units(lan).items()}
    for _, el in etree.iterparse(J.gml_of(lan), events=("end",), tag=J.B + "MappedFeature", huge_tree=True):
        spec = el.find(J.B + "specification")
        k = cls.get((spec.get(J.XL) or "").lstrip("#")) if spec is not None else None
        if k:
            for r in J.rings(el):
                if r[:, 0].max() < x0 or r[:, 0].min() > x1 or r[:, 1].max() < y0 or r[:, 1].min() > y1:
                    continue
                px = np.c_[(r[:, 0] - x0) / RES, (y1 - r[:, 1]) / RES].astype(np.float32)
                area = abs(np.dot(px[:-1, 0], px[1:, 1]) - np.dot(px[1:, 0], px[:-1, 1])) / 2
                polys.append((area, k, px))
        el.clear()
        while el.getprevious() is not None:
            del el.getparent()[0]
    print("län", lan, len(polys), "ytor i utsnittet", flush=True)
polys.sort(key=lambda p: -p[0])  # large areas first, so that islands in them land on top
for _, k, px in polys:
    if len(px) >= 3:
        draw.polygon([tuple(p) for p in px], fill=k)
HERE = os.path.dirname(os.path.abspath(__file__))
img.save(os.path.join(HERE, "jordart_zoom.tif"), compression="tiff_lzw")
json.dump({"crs": "EPSG:3006", "xmin": x0, "xmax": x1, "ymin": y0, "ymax": y1, "res": RES, "classes": J.CLASSES,
           "source": "SGU, Jordarter 1:25 000–1:100 000 (INSPIRE), CC BY 4.0"},
          open(os.path.join(HERE, "jordart_zoom.json"), "w"), ensure_ascii=False, indent=1)
a = np.asarray(img)
print({J.CLASSES.get(k, "ingen"): round(float((a == k).mean()), 3) for k in range(8)})
