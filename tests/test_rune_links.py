"""Runa för runa (src/rune_links.py): tokeniseringen, facit version 2, granskningsbildens pixlar till modellens mm,
utgåvan i TEI/EpiDoc (src/tei_export.py), utvärderingen mot kopplade runor och spårläsarens blinda prov (stubben)."""
import json

import numpy as np
import pytest
import trimesh
from fastapi.testclient import TestClient

from src import rune_links, tei_export
from src.auto_grooves import analyze_grooves
from src.synthetic import rune_stone
from tests.test_auto_grooves import band_segments


def _tokens(signum):
    rec, part = rune_links.rundata_record(signum)
    return rune_links.transliteration_for(rec, part)


# ---- tokenisation ------------------------------------------------------------------------------------------------

def test_tokenize_kinds_words_and_flags():
    # Sö 211: "stinulfR + auk × ha(k)- --- × þ[ur]RikR + …"
    t = _tokens("Sö 211")["tokens"]
    s = "".join(x["char"] for x in t[:21])
    assert s == "stinulfR+auk×hak????×"
    assert [x["kind"] for x in t[13:20]] == ["rune", "rune", "uncertain", "lost", "lost", "lost", "lost"]
    assert t[16]["reason"] == "lost" and t[16]["orig"] == "-"
    assert t[8]["kind"] == "divider" and t[8]["word"] is None
    assert t[16]["word"] == t[13]["word"] and t[17]["word"] == t[16]["word"] + 1  # "ha(k)-" then "---"
    assert t[22]["older"] and t[23]["older"] and not t[24].get("older")  # þ[ur]RikR
    # Sö 319: '::' is one divider; Sö 207: '...' a gap of unknown length inside the word
    t319 = _tokens("Sö 319")["tokens"]
    assert any(x["kind"] == "divider" and x["char"] == "::" for x in t319)
    t207 = _tokens("Sö 207")["tokens"]
    assert t207[4]["kind"] == "gap" and t207[4]["word"] == t207[0]["word"] and t207[4]["pos"] is None
    # Rundata's bind rune (^) and a rune that is seen but cannot be read ('?')
    bind = rune_links.tokenize("a^b : ?c")
    assert bind[0]["bind_next"] and not bind[1].get("bind_next")
    assert bind[3]["kind"] == "lost" and bind[3]["reason"] == "illegible"


def test_token_positions_match_the_text_model():
    """pos is the place in textmodel.text_groups' text – the positions the trace reader and led F use."""
    import src.runlm as rl
    recs = [r for r in rl.load_rundata() if r["signum"].startswith(("Sö ", "U 1", "Ög 1")) and r.get("transliteration")]
    assert len(recs) > 500
    for r in recs:
        toks = rune_links.tokenize(r["transliteration"])
        got = "".join(rl.runekey(x["char"]) for x in toks if x["pos"] is not None)
        assert got == rune_links.model_text(r["transliteration"]), r["signum"]
        assert [x["pos"] for x in toks if x["pos"] is not None] == list(range(len(got)))


def test_part_stone_gets_its_section():
    whole, part = _tokens("Sö 137"), _tokens("Sö 137A")
    assert whole["sections"] == ["A", "B"] and part["part"] == "A"
    assert {x["section"] for x in part["tokens"]} == {"A"} and len(part["tokens"]) < len(whole["tokens"])
    # the alternative reading (§BQ) is left out, as in the text model
    assert "raknasuatau-i" not in "".join(x["char"] for x in whole["tokens"])
    assert whole["source"]["version"] == "2014 med RUNDATA.xls uppdaterad 2018"


# ---- the facit file ------------------------------------------------------------------------------------------------

def _facit_v2(tokens, links, skipped=()):
    return {"type": "vitki-rune-facit", "version": 2, "signum": "Sö 211", "labels": [], "rune_marks": [],
            "tokens": tokens, "rune_links": links, "skipped_tokens": list(skipped)}


def test_read_facit_version_1_and_2():
    v1 = {"type": "vitki-rune-facit", "version": 1, "signum": "Sö 134", "labels": [{"point": [0, 0, 0], "label": "rune"}],
          "rune_marks": [[1, 2]]}
    f = rune_links.read_facit(v1)
    assert f["version"] == 1 and f["rune_links"] == [] and f["tokens"] is None and f["labels"] == v1["labels"]
    assert rune_links.read_facit({k: v for k, v in v1.items() if k != "version"})["version"] == 1
    toks = _tokens("Sö 211")["tokens"]
    ok = _facit_v2(toks, [{"mark": 0, "token_index": 0, "tokens": [0], "image_xy": [1, 2], "point_mm": [1, 2, 3]},
                          {"mark": 1, "token_index": 1, "tokens": [1, 2], "image_xy": [5, 2], "point_mm": None}], [16])
    f = rune_links.read_facit(ok)
    assert f["version"] == 2 and len(f["rune_links"]) == 2 and f["skipped_tokens"] == [16]
    assert rune_links.link_points(f).shape == (1, 3)
    bad = [
        _facit_v2(toks, [{"mark": 0, "token_index": 1, "tokens": [0]}]),                      # token_index not first
        _facit_v2(toks, [{"mark": 0, "token_index": 0, "tokens": [0, 1, 2]}]),                # three runes in a click
        _facit_v2(toks, [{"mark": 0, "token_index": 0, "tokens": [0]}], [0]),                 # linked and skipped
        _facit_v2(toks, [{"mark": 0, "token_index": 999, "tokens": [999]}]),                  # outside the text
        {"type": "annat", "version": 2},
        {**ok, "version": 3},
    ]
    for b in bad:
        with pytest.raises(ValueError):
            rune_links.read_facit(b)


# ---- pixels to millimetres ----------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def tilted():
    """The band stone, centred as the app loads it and tilted, so that the frame is not the identity."""
    mesh = rune_stone(size=(420, 240), resolution=0.6, segments=band_segments(), depth_mm=3.0, opening_angle_deg=80)
    mesh.apply_translation(-(mesh.bounds[0] + mesh.bounds[1]) / 2.0)
    R = trimesh.transformations.rotation_matrix(0.4, [1, 0.3, 0])
    mesh.apply_transform(R)
    n, up = R[:3, :3] @ np.array([0, 0, 1.0]), R[:3, :3] @ np.array([0, 1.0, 0])
    return mesh, analyze_grooves(mesh, n, up=list(up), runes_only=False)


def test_pixel_to_mm_lands_on_the_slices(tilted):
    mesh, r = tilted
    fr = r["image_frame"]
    assert fr["image_width"] == r["image_width"] and fr["rows"] > 0 and abs(np.dot(fr["u"], fr["n"])) < 1e-9
    acc = [s for s in r["slices"] if s["accepted"] and s.get("point")]
    assert len(acc) > 100
    n = np.array(fr["n"])
    for verts in (mesh.vertices, None):  # height from the model, and from the nearest slices
        an = rune_links.anchors(rune_links.frame_from_result(r), [[s["img_x"], s["img_y"]] for s in acc],
                                mesh_vertices=verts, slices=r["slices"])
        d = np.array([a["point_mm"] for a in an]) - np.array([s["point"] for s in acc])
        plane = np.linalg.norm(d - np.outer(d @ n, n), axis=1)
        # the slice point is the groove bottom found near the sample: within a millimetre in the plane
        assert np.median(plane) < 0.5 and plane.max() < 1.5
        assert np.abs(d @ n).max() < 6.0  # near the surface: about the groove depth (3 mm) above the bottom
        assert {a["height_from"] for a in an} == {"modellen" if verts is not None else "snitten"}
    view = an[0]["normal_or_view"]["view"]
    assert np.allclose(np.subtract(view["position"], view["target"]) / rune_links.VIEW_DISTANCE_MM, n, atol=1e-4)
    # the round trip, and an older analysis without image_frame: the frame fitted from the slices agrees
    x, y = rune_links.plane_to_pixel(fr, *rune_links.pixel_to_plane(fr, 123.4, 56.7))
    assert abs(x - 123.4) < 1e-9 and abs(y - 56.7) < 1e-9
    old = {k: v for k, v in r.items() if k != "image_frame"}
    fit = rune_links.frame_from_result(old)
    assert fit["source"] == "anpassad ur snitten" and fit["a_rms_mm"] < 0.5 and fit["b_rms_mm"] < 0.5
    for px in ([10, 10], [300, 200], [600, 350]):
        assert np.hypot(*np.subtract(rune_links.pixel_to_plane(fit, *px), rune_links.pixel_to_plane(fr, *px))) < 1.0


def test_anchor_endpoint(tilted):
    from api.main import app
    mesh, r = tilted
    client = TestClient(app)
    up = client.post("/api/3d/upload", files={"file": ("tilted.stl", mesh.export(file_type="stl"))})
    assert up.status_code == 200, up.text
    acc = [s for s in r["slices"] if s["accepted"] and s.get("point")][:3]
    rows = [[s["img_x"], s["img_y"], *s["point"], s["spårdjup_mm"]] for s in acc]
    data = {"marks_json": json.dumps([[s["img_x"], s["img_y"]] for s in acc]), "frame_json": json.dumps(r["image_frame"]),
            "parameters_json": json.dumps({"normal": r["parameters"]["normal"], "up": r["parameters"]["up"]}),
            "slices_json": json.dumps(rows), "mesh_id": up.json()["mesh_id"]}
    res = client.post("/api/3d/rune_anchors", data=data)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["frame_source"] == "analys" and len(body["anchors"]) == 3
    # the mesh is centred again on upload, so its points equal the analysis' only up to that shift: compare in the plane
    assert all(a["height_from"] == "modellen" for a in body["anchors"])
    # without the model and without the frame: fitted from the slices, height from the slices
    res = client.post("/api/3d/rune_anchors", data={**data, "mesh_id": "", "frame_json": "null",
                                                   "slices_json": json.dumps([[s["img_x"], s["img_y"], *s["point"], 0.0]
                                                                              for s in r["slices"] if s["accepted"]])})
    assert res.status_code == 200 and res.json()["frame_source"] == "anpassad ur snitten"
    assert client.post("/api/3d/rune_anchors", data={"marks_json": "[[1, 2, 3]]"}).status_code == 400
    assert client.post("/api/3d/rune_anchors", data={**data, "mesh_id": "saknas"}).status_code == 404
    tok = client.get("/api/rundata/tokens", params={"signum": "Sö 137A"})
    assert tok.status_code == 200 and tok.json()["part"] == "A"
    assert client.get("/api/rundata/tokens", params={"signum": "Sö 99999"}).status_code == 404


# ---- TEI/EpiDoc ---------------------------------------------------------------------------------------------------

def _edition(signum="Sö 211"):
    tr = _tokens(signum)
    toks = tr["tokens"]
    links, skipped, x = [], [], 20.0
    runes = [t for t in toks if t["kind"] in rune_links.LINKABLE]
    k = 0
    while k < len(runes):
        t = runes[k]
        if t["kind"] == "lost":
            skipped.append(t["i"])
            k += 1
            continue
        ts = [t["i"], runes[k + 1]["i"]] if len(links) == 3 else [t["i"]]  # click 4 is a bind rune
        links.append({"mark": len(links), "token_index": ts[0], "tokens": ts, "char": "", "image_xy": [x, 50.0],
                      "point_mm": [x * 0.6, 10.0, 2.0], "height_from": "modellen",
                      "normal_or_view": {"normal": [0, 0, 1], "view": {"position": [x * 0.6, 10, 302],
                                                                        "target": [x * 0.6, 10, 2], "up": [0, 1, 0]}}})
        x += 30
        k += len(ts)
    return {"signum": signum, "labeller": "Testaren", "created": "2026-11-06T12:00:00Z",
            "transliteration": {"text": tr["transliteration"], "source": tr["source"]}, "tokens": toks,
            "rune_links": links, "skipped_tokens": skipped, "image_width": 1600, "image_height": 900,
            "mesh": {"filename": "So 211_thin03_closed holes.stl", "sha256": "ab" * 32, "centered_by": [1.0, 2.0, 3.0]}}


def test_tei_export_is_well_formed_and_consistent():
    from lxml import etree
    from src.groove_export import credit_for_mesh
    ed = _edition()
    rec, _ = rune_links.rundata_record("Sö 211")
    credit = credit_for_mesh({"filename": "So 211_thin03_closed holes.stl", "bytes": 1})
    xml = tei_export.build(rune_links.read_facit({"type": "vitki-rune-facit", "version": 2, **ed}), rec, credit)
    assert tei_export.check(xml) == []
    root = etree.fromstring(xml)  # well-formed for lxml too
    ns = {"t": tei_export.TEI_NS, "v": tei_export.ANKARE_NS}
    X = "{http://www.w3.org/XML/1998/namespace}id"
    ids = [e.get(X) for e in root.iter() if e.get(X)]
    assert len(ids) == len(set(ids))
    # every token has an element with xml:id t<i>; every linked rune points at both of its click's zones
    assert {f"t{t['i']}" for t in ed["tokens"]} <= set(ids)
    for ln in ed["rune_links"]:
        for t in ln["tokens"]:
            el = root.find(f".//*[@{{http://www.w3.org/XML/1998/namespace}}id='t{t}']")
            m = ln["mark"] + 1
            assert el.get("facs") == f"#zon-bild-m{m} #zon-3d-m{m}"
            zone = root.find(f".//t:zone[@{{http://www.w3.org/XML/1998/namespace}}id='zon-3d-m{m}']", ns)
            anchor = root.find(f".//v:punkt[@{{http://www.w3.org/XML/1998/namespace}}id='ankare-m{m}']", ns)
            assert zone.get("ana") == f"#ankare-m{m}" and anchor.find("v:mm", ns).get("x") == f"{ln['point_mm'][0]:.3f}"
            # in the scan file's own coordinates: the point plus centered_by
            assert anchor.find("v:mm_i_filen", ns).get("z") == f"{ln['point_mm'][2] + 3.0:.3f}"
    bind = ed["rune_links"][3]["tokens"]
    assert all(root.find(f".//*[@{{http://www.w3.org/XML/1998/namespace}}id='t{t}']").get("rend") == "ligature" for t in bind)
    # skipped (lost) runes are <gap> without @facs; dividers <g type="divider">; Rundata as source with its version
    gaps = root.findall(".//t:gap[@reason='lost'][@quantity='1']", ns)
    assert gaps and all(g.get("facs") is None for g in gaps)
    assert root.findall(".//t:g[@type='divider']", ns)
    assert root.find(".//t:supplied[@reason='lost']", ns) is not None and root.find(".//t:unclear", ns) is not None
    assert root.find(".//t:bibl[@type='translitteration']/t:edition", ns).text == rune_links.RUNDATA_VERSION
    assert root.find(".//t:respStmt/t:persName", ns).text == "Testaren"
    assert root.find(".//t:div[@type='edition']", ns).get("{http://www.w3.org/XML/1998/namespace}lang") == "non-Latn"
    # a word's characters stand without whitespace between them
    w = root.find(".//t:w", ns)
    assert "".join(w.itertext()) == "stinulfR"
    # an unknown scan gets no third-party credit; the known open scan of Sö 211 would
    assert b"Kitzler" not in xml and "känner inte igen" in xml.decode()


def test_tei_check_finds_broken_references():
    xml = tei_export.build(_edition())
    broken = xml.replace(b'xml:id="zon-3d-m1"', b'xml:id="zon-3d-x"')
    assert any("zon-3d-m1" in p for p in tei_export.check(broken))
    assert tei_export.check(b"<TEI><text>") and "välformad" in tei_export.check(b"<TEI><text>")[0]


# ---- evaluation with linked runes ---------------------------------------------------------------------------------

def test_link_metrics_on_a_synthetic_layout():
    from scripts.evaluate_rune_detection import link_metrics
    links = np.array([[0, 0, 0], [50, 0, 0], [100, 0, 0], [150, 0, 0]], float)

    def sl(x, y, rid, feature="rune", accepted=True):
        return {"accepted": accepted, "point": [x, y, 0.0], "feature": feature, "rune_id": rid}
    slices = ([sl(0, y, 1) for y in (-20, 0, 20)]                 # rune 1: one detected group of its own
              + [sl(50, 10, 2), sl(48, -10, 3)]                    # rune 2: two groups (split)
              + [sl(100, 0, 4), sl(150, 0, 4)]                     # runes 3 and 4 share one group (merged)
              + [sl(400, 0, 9)]                                    # a rune slice far from every click
              + [sl(0, 5, None, feature="ornament"), sl(50, 0, 2, accepted=False)])
    m = link_metrics(links, slices, [0, 0, 1])
    assert m["reach_mm"] == 75.0 and m["n_links"] == 4 and m["n_rune_slices"] == 8
    assert m["found"] == 4 and m["recall"] == 1.0
    assert m["assigned"] == 7 and m["precision"] == pytest.approx(7 / 8)
    assert m["one_to_one"] == 1 and m["one_to_one_share"] == 0.25
    empty = link_metrics(np.zeros((0, 3)), slices, [0, 0, 1])
    assert empty["recall"] is None and empty["n_links"] == 0


def test_evaluation_with_a_synthetic_facit_v2(tmp_path):
    """The whole chain: a version-2 facit whose clicks sit on the synthetic stone's staves finds every rune."""
    import hashlib

    from scripts.evaluate_rune_detection import evaluate, load_like_app
    mesh = rune_stone(size=(420, 240), resolution=0.6, segments=band_segments(), depth_mm=3.0, opening_angle_deg=80)
    path = tmp_path / "band.stl"
    mesh.export(path)
    app_mesh = load_like_app(str(path))
    shift = -(mesh.bounds[0] + mesh.bounds[1]) / 2.0
    full = analyze_grooves(app_mesh, [0, 0, 1], runes_only=False)
    fr = rune_links.frame_from_result(full)
    # band_segments: rune i is a stave at x = −160 + 55 i and a 25 mm branch; the click goes mid-rune
    centres = [np.array([-160 + 55 * i + 12.0 + shift[0], shift[1], 0.0]) for i in range(6)]
    marks = [rune_links.plane_to_pixel(fr, float(c @ fr["u"]), float(c @ fr["v"])) for c in centres]
    anc = rune_links.anchors(fr, marks, mesh_vertices=app_mesh.vertices, slices=full["slices"])
    tokens = rune_links.tokenize("abcdef")
    facit = {"type": "vitki-rune-facit", "version": 2, "signum": "Syntetisk",
             "mesh": {"filename": "band.stl", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
             "parameters": full["parameters"], "labels": [], "rune_marks": [list(m) for m in marks],
             "image_width": full["image_width"], "image_height": full["image_height"], "tokens": tokens,
             "rune_links": [{"mark": k, "token_index": k, "tokens": [k], "char": tokens[k]["char"], "image_xy": list(m),
                             "point_mm": a["point_mm"]} for k, (m, a) in enumerate(zip(marks, anc))],
             "skipped_tokens": []}
    res = evaluate(json.loads(json.dumps(facit)), [str(tmp_path)])
    links = res["links"]
    assert res["facit_version"] == 2 and links["n_links"] == 6 and links["recall"] == 1.0
    assert links["precision"] > 0.9 and links["max_recomputed_diff_mm"] < 0.01
    # a version-1 facit gives no link measures
    v1 = {k: v for k, v in facit.items() if k not in ("tokens", "rune_links", "skipped_tokens")}
    assert "links" not in evaluate({**v1, "version": 1}, [str(tmp_path)])


# ---- the blind trace-reader test (stub) ---------------------------------------------------------------------------

def test_blind_pairing_and_refusal(tmp_path):
    from scripts import sparlasare_blind as sb
    links = np.array([[0, 0], [40, 0], [80, 0], [120, 0]], float)
    runes = np.array([[2, 1], [41, -2], [300, 0], [118, 3], [125, 0]], float)
    # mutual nearest within 1.5 × 40 mm; the stray rune at 300 mm and the second candidate near 120 mm are left out
    assert sb.pair_links(links, runes) == {0: 0, 1: 1, 3: 3}
    assert sb.pair_links(links, np.zeros((0, 2))) == {}
    # fewer than eight usable facits: the test refuses to run (and never writes a lock)
    toks = rune_links.tokenize("þurulfR")
    for i, sig in enumerate(("Sö 134", "Sö 113", "Sö 211")):
        f = {"type": "vitki-rune-facit", "version": 2, "signum": sig, "created": f"2026-11-0{i + 1}", "tokens": toks,
             "rune_links": [{"mark": 0, "token_index": 0, "tokens": [0], "image_xy": [1, 1], "point_mm": None}],
             "skipped_tokens": [], "labels": [], "rune_marks": [[1, 1]]}
        (tmp_path / f"f{i}.json").write_text(json.dumps(f))
    (tmp_path / "v1.json").write_text(json.dumps({"type": "vitki-rune-facit", "version": 1, "signum": "Sö 143"}))
    chosen, notes = sb.eligible_facits(str(tmp_path))
    assert [f["_signum"] for f in chosen] == ["Sö 134"]
    assert any("utvecklingssten" in n for n in notes) and any("ordkontroll" in n for n in notes)
    assert any("version 1" in n for n in notes)
    with pytest.raises(SystemExit, match="minst 8"):
        sb.main(["--check", "--facit", str(tmp_path)])
