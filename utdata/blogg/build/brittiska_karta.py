"""Kartan till artikeln om runinskrifterna på de brittiska öarna (build_brittiska.py): de 84 vikingatida inskrifterna,
färgade efter vad de handlar om (vår kodning, utdata/brittiska/kodning.csv), på samma underlag som Vitkis karta
(Leaflet med OpenStreetMaps kartbilder, cirkelmarkörer som i web/src/components/RuneMap.tsx), med Isle of Man förstorad.

Rundata har inga koordinater för de irländska inskrifterna; vi sätter dem efter fyndplatsen (IRISH nedan, ungefärliga
lägen). Inskrifter på samma punkt läggs i en solrosspiral runt punkten så att alla syns.
    PLAYWRIGHT_BROWSERS_PATH=/Volumes/2TB/cache/ms-playwright .venv/bin/python utdata/blogg/build/brittiska_karta.py
Skriver utdata/blogg/brittiska/karta_sv.png och karta_en.png.
"""
import csv
import json
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402

OUT = os.path.join(ROOT, "utdata", "blogg", "brittiska")
os.makedirs(OUT, exist_ok=True)
LEAFLET = os.path.join(ROOT, "web", "node_modules", "leaflet", "dist")

# The find places of the Irish inscriptions (Rundata 'place'), placed by us: approximate positions
IRISH = {"Christ Church Place": (53.3434, -6.2711), "Fishamble Street": (53.3446, -6.2697), "Dublin Castle": (53.3429, -6.2674),
         "Greenmount": (53.9100, -6.3950), "Killaloe, St Flannan's Cathedral": (52.8063, -8.4403),
         "Beginish": (51.9280, -10.2960), "Roosky": (54.8500, -7.7000)}
GROUP = {"minne": "minne", "ägare": "vardag", "namn": "vardag", "vardag": "vardag", "futhark": "vardag",
         "ristare": "ristare", "magi": "magi", "oläsligt": "oläsligt"}
# Validated with the dataviz palette check (all pairs, light): Vitki's rust, cyan, violet, dark yellow; grey = unreadable
COLOR = {"minne": "#b7410e", "vardag": "#0891b2", "ristare": "#7c3aed", "magi": "#ca8a04", "oläsligt": "#94a3b8"}
LABEL = {"sv": {"minne": "minnesmonument", "vardag": "ägare, namn, vardag, futhark", "ristare": "ristarens eller tillverkarens namn",
                "magi": "magi, gudar, böner", "oläsligt": "går inte att läsa", "man": "Isle of Man", "osm": "© OpenStreetMap-bidragsgivare"},
         "en": {"minne": "memorials", "vardag": "owner, name, everyday, futhark", "ristare": "the carver's or maker's name",
                "magi": "magic, gods, prayers", "oläsligt": "cannot be read", "man": "Isle of Man", "osm": "© OpenStreetMap contributors"}}


def points():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "utdata", "brittiska", "kodning.csv"), encoding="utf-8")))
    s, out = store(), []
    for r in rows:
        rec = s.get(r["signum"])
        lat, lon = rec.get("lat"), rec.get("lon")
        if lat is None:
            lat, lon = IRISH[rec["place"]]
        out.append({"signum": r["signum"], "lat": lat, "lon": lon, "g": GROUP[r["kategori"]], "man": r["signum"].startswith("IM ")})
    assert len(out) == 84 and all(p["lat"] for p in out)
    return out


HTML = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="file://LEAFLET/leaflet.css">
<script src="file://LEAFLET/leaflet.js"></script>
<style>
 html,body{margin:0;background:#fff;font-family:-apple-system,Helvetica,Arial,sans-serif}
 #wrap{position:relative;width:740px;height:1000px}
 #main{position:absolute;inset:0}
 #manbox{position:absolute;left:16px;top:16px;width:270px;height:250px;border:2px solid #0f172a;border-radius:10px;overflow:hidden;z-index:900;background:#aad3df}
 #man{width:100%;height:100%}
 .tag{position:absolute;z-index:1000;background:rgba(255,255,255,.92);border-radius:8px;color:#0f172a}
 #mantag{left:26px;top:24px;padding:3px 8px;font-size:15px;font-weight:600}
 #legend{left:16px;bottom:16px;padding:12px 14px;font-size:15px;line-height:1.55}
 #legend i{display:inline-block;width:13px;height:13px;border-radius:50%;margin-right:8px;vertical-align:-1px;border:1px solid #0f172a}
 #osm{right:6px;bottom:6px;padding:2px 6px;font-size:11px;color:#475569}
 .leaflet-control-attribution,.leaflet-control-zoom{display:none}
</style></head><body><div id="wrap"><div id="main"></div><div id="manbox"><div id="man"></div></div>
<div class="tag" id="mantag"></div><div class="tag" id="legend"></div><div class="tag" id="osm"></div></div>
<script>
const P = POINTS, C = COLORS, L = LABELS, COUNT = COUNTS;
document.getElementById('mantag').textContent = L.man;
document.getElementById('osm').textContent = L.osm;
document.getElementById('legend').innerHTML = ['minne','vardag','ristare','magi','oläsligt']
  .map(k => `<div><i style="background:${C[k]}"></i>${L[k]} (${COUNT[k]})</div>`).join('');
window.tiles = 0;
function make(id, pts, bounds, r, pad) {
  const m = L_.map(id, {zoomControl:false, attributionControl:false, zoomSnap:1});
  const t = L_.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:18});
  window.tiles++; t.on('load', () => window.tiles--); t.addTo(m);
  m.fitBounds(bounds, {padding: pad});
  // points on one spot: a sunflower spiral in screen space around it, so that every inscription shows
  // (points closer on screen than two markers count as one spot: Christ Church Place and Fishamble Street, Lincoln I/II)
  const spots = [];
  pts.forEach(p => {
    const q = m.latLngToLayerPoint([p.lat, p.lon]);
    const s = spots.find(s => s.c.distanceTo(q) < r * 2.4);
    if (s) s.g.push(p); else spots.push({c: q, g: [p]});
  });
  spots.forEach(({c, g}) => {
    g.forEach((p, i) => {
      const a = i * 2.39996, d = g.length > 1 ? (r * 1.15) * Math.sqrt(i + 0.5) : 0;
      const ll = m.layerPointToLatLng(L_.point(c.x + d * Math.cos(a), c.y + d * Math.sin(a)));
      L_.circleMarker(ll, {radius:r, color:'#0f172a', weight:1, fillColor:C[p.g], fillOpacity:0.9}).addTo(m);
    });
  });
  return m;
}
const L_ = window.L;
const all = L_.latLngBounds(P.map(p => [p.lat, p.lon]));
const manPts = P.filter(p => p.man), manB = L_.latLngBounds(manPts.map(p => [p.lat, p.lon]));
const main = make('main', P.filter(p => !p.man), all, 5.5, [12, 12]);
L_.rectangle(manB.pad(0.25), {color:'#0f172a', weight:2, fill:false}).addTo(main);
make('man', manPts, manB, 6, [24, 24]);
</script></body></html>"""


def render(lang: str, pts: list) -> str:
    counts = {k: sum(p["g"] == k for p in pts) for k in COLOR}
    assert counts == {"minne": 35, "vardag": 19, "ristare": 6, "magi": 3, "oläsligt": 21}, counts
    html = (HTML.replace("LEAFLET", LEAFLET).replace("POINTS", json.dumps(pts)).replace("COLORS", json.dumps(COLOR))
            .replace("LABELS", json.dumps(LABEL[lang], ensure_ascii=False)).replace("COUNTS", json.dumps(counts)))
    path = os.path.join(OUT, f"karta_{lang}.html")
    open(path, "w", encoding="utf-8").write(html)
    return path


if __name__ == "__main__":
    pts = points()
    with sync_playwright() as p:
        b = p.chromium.launch()
        # OpenStreetMap's tile servers ask for a referring site; the same tiles as on Vitki's map
        ctx = b.new_context(viewport={"width": 740, "height": 1000}, device_scale_factor=2,
                            extra_http_headers={"Referer": "https://vitkirunor.se/"})
        for lang in ("sv", "en"):
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto("file://" + render(lang, pts), wait_until="networkidle", timeout=120000)
            pg.wait_for_function("window.tiles === 0 && [...document.querySelectorAll('img.leaflet-tile')]"
                                 ".every(i => i.complete && i.naturalWidth > 0)", timeout=120000)
            pg.wait_for_timeout(1500)
            assert not errs, errs
            pg.locator("#wrap").screenshot(path=os.path.join(OUT, f"karta_{lang}.png"))
            print("sparade", f"karta_{lang}.png")
        b.close()
