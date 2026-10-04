"""Fullständig stenanalys från terminalen – samma arbetsgång som sidan Stenanalys i appen.

  1. Skanningen laddas upp; reliefbilder räknas ur den (den ristade sidan skattas som stenens tunnaste
     riktning om ingen normal anges).
  2. Automatisk spåranalys med flera känsligheter (den första är huvudanalysen, de övriga känslighetsanalys).
  3. 2D-bildanalys av strykljusbilden.
  4. Blind läsning av strykljusbilden i en eller flera orienteringar, jämförd med Rundata utan AI.
  5. Syntes och attribuering (med berggrund ur SGU).
  6. Stenrapport i artikelform med bilaga om arbetsgången: Word, HTML, Markdown, LaTeX och figurer.

Kräver att analysmotorn körs (uvicorn api.main:app). AI-stegen kräver en Gemini-nyckel i .env; om de
misslyckas fortsätter arbetsgången och felet redovisas i rapporten.

Exempel:
  .venv/bin/python -m scripts.full_stone_analysis "So 113_1_4 thin_closed holes.stl" --signum "Sö 113" \\
      --out utdata/So113 --stone Gråsten --weathering Medel --author "Viktor Kvant"
"""
from __future__ import annotations

import argparse
import base64
import datetime
import io
import json
import os
import sys

import requests
from PIL import Image

METRICS = ["apex_vinkel_deg", "asymmetri_deg", "spårdjup_mm", "spårbredd_mm", "djup_bredd_kvot", "bottenradie_mm",
           "ytråhet_mm"]


def b64png(data_url: str) -> bytes:
    return base64.b64decode(data_url.split(",", 1)[1] if "," in data_url else data_url)


def data_url(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode()


def log(msg: str):
    print(msg, flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="3D-skanning (STL, OBJ eller PLY)")
    ap.add_argument("--signum", default="", help="t.ex. 'Sö 113' – används för Rundata, jämförelser och syntes")
    ap.add_argument("--out", default="utdata/stenanalys", help="mapp för resultaten")
    ap.add_argument("--api", default=os.environ.get("RUNFORSKNING_API", "http://localhost:8000"))
    ap.add_argument("--sensitivity", default="3,5", help="känsligheter; den första är huvudanalysen")
    ap.add_argument("--orientations", default="0,180", help="vridningar (grader) av bilden för blind läsning")
    ap.add_argument("--feature-type", default="rune", choices=["rune", "ornament", "unknown"])
    ap.add_argument("--stone", default="Okänd"); ap.add_argument("--weathering", default="Medel")
    ap.add_argument("--author", default=""); ap.add_argument("--institution", default="")
    ap.add_argument("--device", default=""); ap.add_argument("--scan-license", default="")
    ap.add_argument("--no-ai", action="store_true", help="hoppa över 2D-analys, läsning och AI-text")
    a = ap.parse_args(argv)

    api, out = a.api.rstrip("/"), a.out
    os.makedirs(f"{out}/artikel/figurer", exist_ok=True)
    notes, steps = [], []
    key = os.environ.get("GEMINI_API_KEY", "")
    headers = {"X-Gemini-Api-Key": key} if key else {}

    # 1. Upload and images from the scan
    log("1/6 Laddar upp skanningen …")
    with open(a.file, "rb") as fh:
        r = requests.post(f"{api}/api/3d/upload", files={"file": (os.path.basename(a.file), fh)}, timeout=3600)
    r.raise_for_status()
    info = r.json()
    mid = info["mesh_id"]
    relief = requests.post(f"{api}/api/3d/render_relief", data={"mesh_id": mid}, timeout=1800).json()
    normal = relief["normal"]
    for name, url in [("relief", relief["relief"]), ("djup", relief["depth"])] + [(f"strykljus_{k}", v) for k, v in relief["raking"].items()]:
        open(f"{out}/{name}.png", "wb").write(b64png(url))
    faces = f"{info['faces']:,}".replace(",", " ")
    res_mm = f"{relief['resolution_mm']:.2f}".replace(".", ",")
    steps.append({"name": "Bilder ur skanningen",
                  "result": f"{faces} trianglar; relief, djup och strykljus ur fyra riktningar ({res_mm} mm per pixel)"})

    # 2. Groove analysis with sensitivity analysis
    sens_list = [float(x) for x in a.sensitivity.split(",") if x.strip()]
    sensitivity, main_auto = [], None
    for k, sens in enumerate(sens_list):
        log(f"2/6 Spåranalys, känslighet {sens:g} …")
        d = requests.post(f"{api}/api/3d/auto_analyze", data={"mesh_id": mid, "normal_x": normal[0], "normal_y": normal[1],
                          "normal_z": normal[2], "sensitivity": sens, "meta_stone": a.stone, "meta_weathering": a.weathering},
                          timeout=3600).json()
        if "summary" not in d:
            notes.append(f"Spåranalysen med känslighet {sens:g} gav inga godkända snitt ({d.get('detail', '')}).")
            continue
        main_auto = main_auto or d
        s = d["summary"]
        sensitivity.append({"sensitivity": sens, "threshold_mm": d["parameters"]["threshold_mm"], "candidates": d["counts"]["candidates"],
                            "accepted": d["counts"]["accepted"], "wide_area_mm2": d["counts"]["wide_area_mm2"],
                            "angle_mean": s["apex_vinkel_deg"]["mean"], "angle_sd": s["apex_vinkel_deg"]["sd"],
                            "depth_mean": s["spårdjup_mm"]["mean"], "width_mean": s["spårbredd_mm"]["mean"],
                            "review_png": d["image_base64"]})
        open(f"{out}/granskning_k{sens:g}.png", "wb").write(b64png(d["image_base64"]))
        if k == 0:
            json.dump(d, open(f"{out}/spåranalys.json", "w"))
    if not main_auto:
        sys.exit("Spåranalysen hittade inga godkända tvärsnitt – vrid stenen i 3D-vyn och ange normalen, eller sänk känsligheten.")
    acc = [x for x in main_auto["slices"] if x["accepted"]]
    slices = [{**{m: x[m] for m in METRICS}, "position_mm": x["position_mm"], "fit_r2": x.get("fit_r2"), "profile": x.get("profile"),
               "point": x.get("point"), "direction": x.get("direction"), "up": x.get("up")} for x in acc]
    analysis = {"id": "auto-1", "feature_type": a.feature_type, "savedAt": main_auto["provenance"]["timestamp"],
                "slices": slices, "provenance": {**main_auto["provenance"], "feature_type": a.feature_type}}
    m0 = sensitivity[0]
    steps.append({"name": "Spåranalys", "result": f"{m0['accepted']} godkända av {m0['candidates']} snitt; V-vinkel "
                  f"{m0['angle_mean']:.1f}° ± {m0['angle_sd']:.1f}°".replace(".", ",")})

    raking = open(f"{out}/strykljus_nordväst.png", "rb").read()
    twod, readings = None, []
    if not a.no_ai:
        # 3. 2D image analysis
        log("3/6 2D-bildanalys …")
        r = requests.post(f"{api}/api/2d/analyze", files={"file": ("strykljus.png", raking, "image/png")}, headers=headers, timeout=900)
        if r.ok:
            twod = r.json()
            steps.append({"name": "2D-bildanalys", "result": f"stilgrupp {twod['predicted_style']} (AI, okalibrerad {twod['confidence']} %)"})
        else:
            notes.append(f"2D-bildanalysen misslyckades: {r.json().get('detail', r.status_code)}")
        # 4. Blind reading in each orientation
        for deg in [int(x) for x in a.orientations.split(",") if x.strip()]:
            log(f"4/6 Blind läsning, {deg}° …")
            img = Image.open(io.BytesIO(raking)).rotate(deg, expand=True)
            buf = io.BytesIO(); img.save(buf, format="PNG")
            r = requests.post(f"{api}/api/phonetics/analyze", headers=headers, timeout=900,
                              json={"image_base64": data_url(buf.getvalue()), "signum": a.signum or "Okänd"})
            if r.ok:
                readings.append({"label": f"Strykljus, {deg}°", **r.json()})
            else:
                readings.append({"label": f"Strykljus, {deg}°", "error": "misslyckades"})
                notes.append(f"Blind läsning ({deg}°) misslyckades: {r.json().get('detail', r.status_code)}")
        ok = [x for x in readings if x.get("transliteration")]
        # Validation with the other readings of the same image (consistency), Rundata and known inscriptions
        for x in ok:
            others = [y["transliteration"] for y in ok if y is not x]
            x.update(requests.post(f"{api}/api/phonetics/compare", timeout=300, json={
                "signum": a.signum, "transliteration": x["transliteration"], "normalization": x.get("normalization", ""),
                "other_readings": others}).json())
        if ok:
            c = ok[0].get("reading_comparison") or {}
            v = ok[0].get("validation") or {}
            steps.append({"name": "Blind läsning", "result": f"{len(ok)} av {len(readings)} lyckades; den första: "
                          + (v.get("status") or "ej validerad")
                          + (f" ({round(c.get('char_agreement', 0) * 100)} % av runorna stämmer med Rundata)" if c else "")})
    else:
        notes.append("AI-stegen (2D-analys, läsning, AI-text) hoppades över.")

    # 5. Synthesis
    log("5/6 Syntes och attribuering …")
    reading = next((x for x in readings if x.get("transliteration")), None)
    syn_body = {
        "signum": a.signum or "Okänd", "stoneType": a.stone, "weathering": a.weathering,
        "analyses": [{"id": "auto-1", "feature_type": a.feature_type, "savedAt": analysis["savedAt"],
                      "slices": [{m: x[m] for m in METRICS} | {"position_mm": x["position_mm"]} for x in slices]}],
        "analysis_id": "auto-1", "corpus": [], "corpus_note": "mätkorpusen ingår inte i körningar från terminalen (kräver inloggning).",
        "reading": {"transliteration": reading["transliteration"], "normalization": reading.get("normalization", ""),
                    "others": [x["transliteration"] for x in readings if x.get("transliteration") and x is not reading]} if reading else None,
        "two_d": {"predicted_style": twod["predicted_style"], "confidence": twod["confidence"], "reasoning": twod["reasoning"]} if twod else None,
        "include_geology": True,
    }
    synthesis = requests.post(f"{api}/api/synthesis/analyze", json=syn_body, headers=headers, timeout=900).json()
    json.dump(synthesis, open(f"{out}/syntes.json", "w"), ensure_ascii=False, indent=1)
    if synthesis.get("outcome"):
        steps.append({"name": "Syntes", "result": synthesis["outcome"]["text"]})
    if not synthesis.get("ai_used") and not a.no_ai:
        notes.append("Syntesens AI-text var inte tillgänglig (ingen nyckel, slut på kvot eller tidsgräns); texterna är framräknade.")

    # 6. Stone report with the workflow appendix
    log("6/6 Stenrapport …")
    workflow = {"date": datetime.date.today().isoformat(), "steps": steps, "sensitivity": sensitivity,
                "relief_png": relief["relief"], "two_d_reasoning": (twod or {}).get("reasoning"),
                "readings": readings, "notes": notes + ["Skanningens upplösning, utrustning och licens bör fyllas i om de saknas."]}
    body = {"signum": a.signum, "author": a.author, "institution": a.institution,
            "meta": {"stone": a.stone, "weathering": a.weathering, "text": a.signum},
            "scan": {"device": a.device, "license": a.scan_license}, "condition": {"weathering": a.weathering.lower()},
            "analyses": [analysis], "counts": main_auto["counts"], "mesh_id": mid, "view": {"normal": normal},
            "corpus": [], "synthesis": synthesis, "reading": {k: v for k, v in reading.items() if k != "markers"} if reading else None,
            "two_d": {"image": data_url(raking), "result": twod, "crops": [],
                      "caption": "Digitalt strykljus från nordväst, räknat ur 3D-skanningen – bilden som 2D-analysen och läsningen fick."},
            "workflow": workflow, "use_ai": not a.no_ai}
    rep = requests.post(f"{api}/api/reports/stone", json=body, headers=headers, timeout=1800).json()
    art = f"{out}/artikel"
    base = (a.signum or "sten").replace(" ", "_")
    for f in rep["figures"]:
        open(f"{art}/figurer/{f['name']}", "wb").write(base64.b64decode(f["png"]))
    open(f"{art}/{base}_artikel.md", "w").write(rep["markdown"].replace("](figur", "](figurer/figur"))
    open(f"{art}/{base}_artikel.tex", "w").write(rep["latex"].replace("{figur", "{figurer/figur"))
    open(f"{art}/{base}_artikel.html", "w").write('<!doctype html><meta charset="utf-8"><title>' + (a.signum or "Stenanalys")
                                                   + '</title><style>body{font-family:Georgia,serif;max-width:860px;margin:2rem auto;'
                                                   'padding:0 1rem;line-height:1.55}img{max-width:100%}table{border-collapse:collapse;'
                                                   'font-size:.85em}td,th{border-top:1px solid #ddd;padding:2px 6px;text-align:left}'
                                                   '.caption,figcaption{font-size:.85em;font-style:italic;color:#555}</style>' + rep["html"])
    body.update({"format": "docx", "ai_text": rep.get("ai_text")})
    d = requests.post(f"{api}/api/reports/stone", json=body, headers=headers, timeout=1800)
    open(f"{art}/{base}_artikel.docx", "wb").write(d.content)
    log(f"Klart: {art} ({len(rep['figures'])} figurer{'' if rep.get('surface') else '; ytbilder saknas: ' + str(rep.get('surface_note'))})")


if __name__ == "__main__":
    main()
