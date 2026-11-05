"""Den ändrade attribueringsmodellen (2026-11-04, commits fe616f4 och 7963a9d) i siffror, ur körningar som inte ligger i
git: data/cache/r/corpus/<fp>/attribution.json och Stenöversiktens cache data/cache/overview/<nyckel>.json. Skriver
modell_2026_11_04.json bredvid, så att metodrapporten om ristarförslagen (utdata/blogg/build/build_rapport_ristarmodellen.py,
rapportversion 2) kan assertera siffrorna mot en fil i repot.
    .venv/bin/python utdata/attribuering_provad/modell_2026_11_04.py"""
import hashlib
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FP = "3691a2c441dd03f4"  # korpusen räknad 2026-11-04 12.39, efter 7963a9d (12.07)
OV = "03105c9825cb9214"  # Stenöversikten för den korpusen (nyckeln räknas om nedan)
C = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()  # noqa: E731


def overview_key(fp: str) -> str:
    """Samma nyckel som api/routers/research.py _overview_key: korpusen, Rundata, måtten och koden bakom översikten."""
    parts = [fp]
    for rel in ("data/rundata.json", "data/stone_dimensions.json"):
        p = os.path.join(ROOT, rel)
        parts.append(str(os.path.getmtime(p)) if os.path.exists(p) else "-")
    for rel in ("src/stone_overview.py", "src/synthesis.py", "src/orthography.py", "src/language_profile.py",
                "src/geology.py", "src/research_gaps.py"):
        parts.append(hashlib.sha256(open(os.path.join(ROOT, rel), "rb").read()).hexdigest()[:12])
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


done = json.load(open(os.path.join(C, "done.json"), encoding="utf-8"))
assert done["fingerprint"] == FP and done["computed_at"].startswith("2026-11-04")
at_path = os.path.join(C, "attribution.json")
AT = json.load(open(at_path, encoding="utf-8"))
assert "Runor 2020" in AT["method"], "korsformen ur Runor ska vara ett drag"
P0 = AT["predictions"][0]
assert {"p", "p_cal", "p2_cal", "p3_cal"} <= set(P0), "kalibrerade sannolikheter i egna fält"
assert any(abs(x["p"] - x["p_cal"]) > 0.01 for x in AT["predictions"]), "p ska vara skogens okalibrerade"
AB = {a["features"]: a for a in AT["ablation"]}
GS = {a["features"]: a for a in AT["grouped_cv"]["Socken"]["ablation"]}
GH = {a["features"]: a for a in AT["grouped_cv"]["Härad"]["ablation"]}

assert overview_key(FP) == OV, "Stenöversiktens cache hör inte till korpusen"
ov_path = os.path.join(ROOT, "data", "cache", "overview", f"{OV}.json")
OVJ = json.load(open(ov_path, encoding="utf-8"))
counts = {k: OVJ["counts"][k] for k in ("nytt förslag", "möjligt förslag", "inget förslag")}

out = {
    "beskrivning": "Attribueringsmodellen efter ändringen 2026-11-04 (korsform ur Runor 2020 som drag, kalibrerade fält "
                   "p_cal, gränsen för 'någon annan' på sockengrupperade sannolikheter) och Stenöversiktens förslag med den.",
    "commits": ["fe616f4", "7963a9d"],
    "corpus": FP, "computed_at": done["computed_at"], "r_version": done["r_version"],
    "attribution_sha256": sha(at_path),
    "n_train": AT["n_train"], "n_carvers": len(AT["carvers"]),
    "accuracy": AB["Alla"]["accuracy"], "top3": AB["Alla"]["top3"],
    "accuracy_socken": GS["Alla"]["accuracy"], "accuracy_harad": GH["Alla"]["accuracy"],
    "accuracy_stil": AB["Stil"]["accuracy"],
    "someone_else_threshold": AT["open_set"]["threshold"],
    "cross_form_feature": True, "calibrated_fields": True,
    "overview": {"key": OV, "sha256": sha(ov_path), "counts": counts, "n_unattributed": sum(counts.values())},
}
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modell_2026_11_04.json")
json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(path, json.dumps({k: out[k] for k in ("accuracy", "top3", "accuracy_socken", "accuracy_harad", "accuracy_stil",
                                            "someone_else_threshold")}), counts)
