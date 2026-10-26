"""Sparar strecken längs slingorna (slinga, början och slut längs slingan i mm) och slinghöjderna per fil, så att
regler för gränsen mellan runor kan prövas utan att analysen körs om. En fil i taget (minnet).

  .venv/bin/python -m utdata.stavlosa.dump halsingland HS_15_0_40_thin03
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from utdata.stavlosa.matning import DEPTH, text_runes  # noqa: E402


def main():
    series, stem = sys.argv[1:3]
    import trimesh
    from scripts.download_open_scans import local_path
    from src import protocol, staveless
    from src.auto_grooves import analyze_grooves
    cap = {}
    orig = staveless.group_runes

    def spy(bl, field, res):
        g = orig(bl, field, res)
        cap.update(items=g["items"], heights={int(k): v for k, v in g["heights"].items()})
        return g
    staveless.group_runes = spy
    meta = json.load(open(os.path.join(DEPTH, series, stem + ".json"), encoding="utf-8"))
    mesh = trimesh.load(local_path(series, meta["file"]), force="mesh")
    mesh.apply_translation(-(mesh.bounds[0] + mesh.bounds[1]) / 2.0)
    pp = protocol.PARAMETERS
    analyze_grooves(mesh, meta["normal"], up=meta.get("up"), spacing_mm=pp["spacing_mm"], sensitivity=pp["sensitivity"],
                    max_halfwidth_mm=pp["max_halfwidth_mm"], resolution_mm=pp["resolution_mm"],
                    harmonize_mm=pp["harmonize_mm"] or None, measure="runes", sha256=meta["sha256"], staveless=True)
    out = os.path.join(os.path.dirname(__file__), "streck")
    os.makedirs(out, exist_ok=True)
    json.dump({"signum": meta.get("signum"), "rune_types": meta.get("rune_types"), "text_runor": text_runes(meta.get("transliteration")),
               **cap}, open(os.path.join(out, stem + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(stem, len(cap.get("items", [])))


if __name__ == "__main__":
    main()
