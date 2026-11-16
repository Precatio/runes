"""Viktors kontrollsida för en granskningsenhet (A1, tillägg 1, noterna 2 och 5): hans 10 lottade stenar, bara läget och
flyttningarna, med SRI-texten att fälla ut. Sidan ligger utanför repot (den innehåller SRI:s text).
    .venv/bin/python scripts/sri_kontrollsida.py sm [og vg ol got msv]
Resultatet klistras in i chatten och sparas som granskning/<enhet>_viktor.jsonl.
"""
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = "/Volumes/2TB/Antigrvity/Runes/downloads/sri_fakta/granskning"
F = ["lage_vid_utgavan", "ursprunglig_plats_text", "inmurad", "forsvunnen", "aterfunnen"]  # not 7
NAMN = {"lage_vid_utgavan": "Läge när bandet skrevs", "ursprunglig_plats_text": "Ursprunglig plats", "inmurad": "Inmurad",
        "forsvunnen": "Försvunnen", "aterfunnen": "Återfunnen"}
CSS = """:root{--rust:#b7410e;--ink:#1d2226;--bg:#faf8f4} body{font:15px/1.5 -apple-system,Helvetica,sans-serif;color:var(--ink);background:var(--bg);max-width:1000px;margin:0 auto;padding:16px}
h1{font-family:Georgia,serif} h2{border-top:3px solid var(--rust);padding-top:8px} small{color:#666;font-weight:400} table{width:100%;border-collapse:collapse} td{border-bottom:1px solid #ddd;padding:6px;vertical-align:top} td:first-child{width:160px;color:#555}
q{color:#444;font-style:italic} .tom{color:#999} .om{color:var(--rust);font-weight:600} pre{white-space:pre-wrap;font-size:12px;background:#fff;padding:8px;max-height:420px;overflow:auto} button{background:var(--rust);color:#fff;border:0;padding:10px 16px;font-size:15px;cursor:pointer} textarea{width:100%;height:120px}"""
JS = ("function ut(){const m={};document.querySelectorAll('select').forEach(s=>{(m[s.dataset.s]=m[s.dataset.s]||{})[s.dataset.f]=s.value});"
      "document.getElementById('r').value=Object.entries(m).map(([k,v])=>JSON.stringify({signum:k,bedomning:v})).join('\\n');document.getElementById('r').select()}")


def visa(v):
    if v in (None, [], {}):
        return '<span class="tom">nämns inte</span>'
    out = []
    for p in (v if isinstance(v, list) else [v]):
        d = {k: x for k, x in p.items() if k not in ("citat", "sida")}
        out.append("<div><b>" + html.escape(json.dumps(d, ensure_ascii=False)[1:-1]) + "</b><br><q>" + html.escape(p.get("citat") or "")
                   + "</q> <i>s. " + html.escape(str(p.get("sida"))) + "</i></div>")
    return "".join(out)


def sida(enhet: str) -> str:
    rap = json.load(open(os.path.join(ROOT, "utdata", "sri_fakta", f"{enhet}_kontroll.json"), encoding="utf-8"))
    S = {json.loads(l)["signum"]: json.loads(l) for l in open(os.path.join(G, f"{enhet}_stickprov.jsonl"), encoding="utf-8")}
    rows = []
    for sig in rap["viktor"]:
        s = S[sig]
        om = s.get("omfattar") or [sig]
        note = f'<p class="om">Artikeln gäller {", ".join(om)} – bedöm bara {sig}.</p>' if len(om) > 1 else ""
        tr = "".join(f'<tr><td>{NAMN[f]}</td><td>{visa(s["utplockning"].get(f))}</td><td><select data-s="{html.escape(sig)}" data-f="{f}">'
                     f"<option>rätt</option><option>fel</option><option>saknat</option></select></td></tr>" for f in F)
        rows.append(f'<section><h2>{html.escape(sig)} <small>SRI, s. {html.escape(", ".join(dict.fromkeys(s["pages"])))}</small></h2>{note}'
                    f'<details><summary>Visa SRI-texten</summary><pre>{html.escape(s["text"])}</pre></details><table>{tr}</table></section>')
    doc = f"""<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Kontroll SRI {enhet}</title><style>{CSS}</style></head><body>
<h1>Kontroll av SRI-utplockningen – {html.escape(", ".join(rap['verk']))}</h1>
<p>{len(rap['viktor'])} stenar ur stickprovet. Bara läget och försvunnen/återfunnen (not 7). En sten som hittades inmurad har läget "flyttad". En fyndplats är inte ursprunglig plats om
utgivaren inte säger det. Ett första fynd ("förut okänd", "nyfunnen") är inget återfynd. <b>rätt</b> = rätt värde, eller "nämns inte" och artikeln nämner det inte. <b>fel</b> = ifyllt men fel.
<b>saknat</b> = artikeln nämner det men fältet är tomt eller ofullständigt. Allt står på "rätt" – ändra bara där något inte stämmer,
tryck på knappen och klistra in texten i chatten.</p>
{"".join(rows)}<p><button onclick="ut()">Skapa resultat</button></p><textarea id="r"></textarea><script>{JS}</script></body></html>"""
    p = os.path.join(G, f"Kontroll_SRI_{enhet}.html")
    open(p, "w", encoding="utf-8").write(doc)
    return p


if __name__ == "__main__":
    for e in sys.argv[1:]:
        print(sida(e))
