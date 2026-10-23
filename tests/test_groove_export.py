"""Export från huggspårsanalysen (src/groove_export.py, POST /api/3d/export): filerna återger analysens egna tal och
bilder, varje fil bär skanningens kreditering, och refaktoreringen av depth_figure och render_relief ändrar inga
bilder. Körs i processen med TestClient; inget skickas till det lokala API:t."""
import csv
import io
import json
import os
import zipfile

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api.main import app
from api.routers import threed
from src import groove_export, stone_report

ROOT = os.path.join(os.path.dirname(__file__), "..")
SO370 = os.path.join(ROOT, "skanningar", "So 370_1_4 thin05_closed holes.stl")
N = [0.0, -float(np.sin(np.radians(20))), float(np.cos(np.radians(20)))]
ALL = [x["id"] for x in groove_export.ITEMS]


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def stone():
    from src.synthetic import rune_stone
    m = rune_stone(opening_angle_deg=70, depth_mm=4, tilt_deg=20)
    return m, m.export(file_type="stl")


def _upload(client, stl: bytes, name="stone.stl") -> str:
    # The engine cache holds two models; uploading again is instant when it is still there
    r = client.post("/api/3d/upload", files={"file": (name, stl)})
    assert r.status_code == 200, r.text
    return r.json()["mesh_id"]


@pytest.fixture(scope="module")
def auto(client, stone):
    mid = _upload(client, stone[1])
    r = client.post("/api/3d/auto_analyze", data={"mesh_id": mid, "normal_x": N[0], "normal_y": N[1], "normal_z": N[2]})
    assert r.status_code == 200, r.text
    return r.json()


def _labels(result):
    return ["rune" if s["accepted"] else "excluded" for s in result["slices"]]


def _post_export(client, data: dict):
    """POST /api/3d/export as multipart/form-data, as the browser's FormData sends it (fields without a file name)."""
    return client.post("/api/3d/export", files={k: (None, str(v)) for k, v in data.items()})


def _export(client, mid, items, result=None, **extra):
    data = {"mesh_id": mid, "items": ",".join(items), **extra}
    if result is not None:
        data["result_json"] = json.dumps(result)
    return _post_export(client, data)


def _csv_rows(data: bytes):
    text = data.decode("utf-8")
    assert text.startswith("﻿#")
    lines = text.lstrip("﻿").splitlines()
    meta = [ln for ln in lines if ln.startswith("#")]
    rows = list(csv.reader([ln for ln in lines if not ln.startswith("#")]))
    return meta, rows[0], rows[1:]


def _zip(data: bytes) -> dict[str, bytes]:
    z = zipfile.ZipFile(io.BytesIO(data))
    assert all(i.compress_type == zipfile.ZIP_DEFLATED for i in z.infolist())
    return {name.split("/", 1)[1]: z.read(name) for name in z.namelist()}


# ---- refactors leave the images unchanged --------------------------------------------------------------------------

def _old_depth_figure(surf):
    """stone_report.depth_figure as it was before depth_array/depth_vmax were factored out."""
    plt = stone_report._plt()
    depth = np.clip(-surf.residual, 0, None)
    depth[~surf.inner] = np.nan
    vmax = float(np.nanpercentile(depth, 99.5)) if np.isfinite(depth).any() else 1.0
    w, hgt = surf.extent[1], surf.extent[3]
    fig, ax = plt.subplots(figsize=(7, 7 * hgt / w if w else 7))
    cmap = plt.get_cmap("magma_r").copy()
    cmap.set_bad("white")
    im = ax.imshow(depth, cmap=cmap, origin="lower", extent=surf.extent, vmin=0, vmax=max(vmax, 0.1),
                   interpolation="bilinear")
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("Djup under stenytan (mm)")
    stone_report._scalebar(ax, surf.extent)
    stone_report._clean_axes(ax)
    return stone_report._png(fig)


def _server_mesh(client, stone):
    """The model exactly as the engine holds it (STL round trip, centred by its bounds)."""
    from api import mesh_cache
    return mesh_cache.peek(_upload(client, stone[1])).mesh


def test_depth_figure_bytes_unchanged_by_refactor(client, stone):
    surf = stone_report.Surface(_server_mesh(client, stone), N)
    assert stone_report.depth_figure(surf) == _old_depth_figure(surf)


def test_render_relief_output_unchanged(client, stone):
    import base64
    mid = _upload(client, stone[1])
    body = client.post("/api/3d/render_relief", data={"mesh_id": mid, "normal_x": N[0], "normal_y": N[1],
                                                       "normal_z": N[2]}).json()
    # The old image math, written out
    surf = stone_report.Surface(_server_mesh(client, stone), N, None, max_px=1600)

    def png(gray):
        img = np.nan_to_num(gray, nan=1.0)
        pil = Image.fromarray((np.flipud(np.clip(img, 0, 1)) * 255).astype(np.uint8))
        scale = 1200 / max(pil.size)
        if scale > 1:
            pil = pil.resize((round(pil.width * scale), round(pil.height * scale)), Image.LANCZOS)
        buf = io.BytesIO()
        pil.save(buf, format="PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    views = {name: surf.shaded(az, 20) for name, az in
             (("nordväst", 315), ("nordost", 45), ("sydost", 135), ("sydväst", 225))}
    relief = np.nanmin(np.stack(list(views.values())), axis=0)
    relief = (relief - np.nanpercentile(relief, 1)) / max(np.nanpercentile(relief, 99) - np.nanpercentile(relief, 1), 1e-6)
    depth = np.clip(-surf.residual, 0, None)
    ref = float(np.nanpercentile(depth[surf.inner], 99))
    depth_img = 1 - np.clip(depth / max(ref, 1e-6), 0, 1)
    depth_img[~surf.inner] = np.nan
    assert body["relief"] == png(relief)
    assert body["depth"] == png(depth_img)
    assert body["raking"] == {name: png(v) for name, v in views.items()}
    assert body["resolution_mm"] == surf.res and body["depth_ref_mm"] == pytest.approx(ref)


def test_groove_map_scale_is_additive(auto):
    sc = auto["groove_map_scale"]
    assert set(sc) >= {"black_mm", "threshold_mm", "grid_mm"}
    assert sc["threshold_mm"] == auto["parameters"]["threshold_mm"] and sc["grid_mm"] == auto["parameters"]["resolution_mm"]
    assert "groove_map_scale" not in auto["parameters"]  # protocol compliance reads parameters
    assert sc["black_mm"] > sc["threshold_mm"]


# ---- catalogue and credit -------------------------------------------------------------------------------------------

def test_export_items_catalogue(client):
    r = client.get("/api/3d/export_items")
    assert r.status_code == 200
    body = r.json()
    ids = [x["id"] for x in body["items"]]
    assert ids == ALL and len(set(ids)) == len(ids)
    needs = {"mesh", "auto", "slices", "point>=1", "point>=3", "profile", "summary", "runes", "depth_profile",
             "groove_map", "review_image"}
    for x in body["items"]:
        assert x["group"] in ("skanning", "matning", "data") and x["label"] and len(x["explanation"]) > 80
        assert set(x["needs"]) <= needs and set(x["formats"]) <= {"PNG", "CSV", "ASC", "JSON"}
    # every item has a builder
    assert set(ALL) == set(groove_export.BUILDERS) | {"full_json"}
    assert body["readme_intro"]


SO370_NAME, SO370_BYTES = "So 370_1_4 thin05_closed holes.stl", 19272334
SO370_MD5 = "0755f478582e659414fae0140e1550c9"


def test_scan_credit_endpoint_identifies_the_file_not_the_signum(client, stone):
    # A typed signum alone never gives a third-party credit
    for s in ("Sö 370", "", "U 9999"):
        r = client.get("/api/3d/scan_credit", params={"signum": s})
        assert r.status_code == 200 and r.json()["known"] is False and r.json()["dataset"] is None
    # The published file: by name and size, by md5 (what Zenodo publishes), not under a published name with
    # another size or checksum
    c = client.get("/api/3d/scan_credit", params={"filename": SO370_NAME, "size": SO370_BYTES}).json()
    assert c["known"] and c["match"] == "filnamn och storlek" and c["file"]["signum"] == "Sö 370"
    d = c["dataset"]
    assert d["license"] == "CC BY 4.0" and d["doi"] == "10.5281/zenodo.11951255"
    assert d["license_url"] == "https://creativecommons.org/licenses/by/4.0/"
    assert d["scanned_by"] == "Laila Kitzler Åhfeldt" and d["institution"] == "Riksantikvarieämbetet"
    # the visible credit names scanner, institution, project, licence with its link and the DOI
    for part in ("Laila Kitzler Åhfeldt", "Riksantikvarieämbetet", "Runristandets dynamik", "CC BY 4.0",
                 "https://creativecommons.org/licenses/by/4.0/", "doi:10.5281/zenodo.11951255"):
        assert part in c["credit_text"], part
    assert c["computed_note"] == "Bilden är beräknad i Vitki."
    assert client.get("/api/3d/scan_credit", params={"filename": "x.stl", "md5": SO370_MD5}).json()["match"] == "md5"
    assert not client.get("/api/3d/scan_credit", params={"filename": SO370_NAME, "size": 5}).json()["known"]
    assert not client.get("/api/3d/scan_credit", params={"filename": SO370_NAME, "size": SO370_BYTES,
                                                          "md5": "0" * 32}).json()["known"]
    # an uploaded model that is not a published file, even under a published name
    mid = _upload(client, stone[1], SO370_NAME)
    assert client.get("/api/3d/scan_credit", params={"mesh_id": mid}).json()["known"] is False
    assert client.get("/api/3d/scan_credit").json()["known"] is False
    assert client.get("/api/3d/scan_credit", params={"filename": "x" * 2000}).status_code == 400
    # a file name alone (no size, no checksum) is not enough, with or without a path
    assert client.get("/api/3d/scan_credit", params={"filename": SO370_NAME}).json()["known"] is False
    assert groove_export.scan_credit("C:\\Users\\x\\Og 240_241_thin03.stl")["known"] is False
    # one file that shows two stones names both, and the dataset's note goes with the credit
    og = groove_export.scan_credit("Og 240_241_thin03.stl", size=245496284)
    assert og["known"] and og["file"]["signa"] == ["Ög 240", "Ög 241"]
    assert og["credit_text"].startswith("Skanningen av Ög 240 och Ög 241 ")
    assert "Bara inskriftsytorna är skannade." in og["credit_text"]


def test_slug():
    assert groove_export.slug("Sö 370") == "So_370"
    assert groove_export.slug("Sö Fv1948;282") == "So_Fv1948_282"
    assert groove_export.slug("") == "vitki" and groove_export.slug(None) == "vitki"


# ---- the export ------------------------------------------------------------------------------------------------------

def test_export_every_item_from_an_automatic_analysis(client, stone, auto):
    mid = _upload(client, stone[1])
    # the synthetic stone is not Sö 370's published scan: typing the signum gives no third-party credit
    r = _export(client, mid, ALL, auto, labels_json=json.dumps(_labels(auto)), mode="auto", signum="Sö 370")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/zip"
    assert 'filename="So_370_vitki_export_' in r.headers["content-disposition"]
    assert "filename*=UTF-8''So_370_vitki_export_" in r.headers["content-disposition"]
    assert "X-Export-Skipped" in r.headers["access-control-expose-headers"]
    files = _zip(r.content)
    assert {"README.txt", "kalla.json"} <= files.keys()
    expected = {"So_370_djup_under_stenytan.png", "So_370_djup_under_stenytan_mm.asc",
                "So_370_djup_under_stenytan_mm.json", "So_370_relief.png", "So_370_strykljus_nordvast.png",
                "So_370_strykljus_nordost.png", "So_370_strykljus_sydost.png", "So_370_strykljus_sydvast.png",
                "So_370_ristningskarta.png", "So_370_granskningsbild.png", "So_370_snittpositioner_v_vinkel.png",
                "So_370_djup_bredd_ytrahet.png", "So_370_tvarsnittsprofiler.png", "So_370_snitt.csv",
                "So_370_sammanfattning.csv", "So_370_runor.csv", "So_370_profiler.csv", "So_370_analys.json"}
    assert expected <= files.keys()
    assert r.headers["x-export-files"].split(",") == [n for n in r.headers["x-export-files"].split(",")]
    assert set(r.headers["x-export-files"].split(",")) == expected
    # a path-only item is skipped with a reason, not an error
    from urllib.parse import unquote
    assert r.headers["x-export-skipped"].isascii()
    assert unquote(r.headers["x-export-skipped"]) == "length_profile_csv:ingen längdprofil (bara mätning längs en ritad bana)"
    kalla = json.loads(files["kalla.json"])
    assert not kalla["credit"]["known"] and kalla["export"]["surface"]["normal_source"] == "analys"
    assert kalla["mode"] == "auto" and kalla["mesh"]["md5"] and kalla["mesh"]["bytes"] == len(stone[1])
    assert kalla["export"]["skipped"][0]["id"] == "length_profile_csv"
    readme = files["README.txt"].decode("utf-8")
    assert "Kitzler Åhfeldt" not in readme and groove_export.UNKNOWN_SCAN in readme and "utan uppskalning" in readme
    assert "DINA ETIKETTER" in readme
    for x in groove_export.ITEMS:
        if x["id"] != "length_profile_csv":
            assert x["label"] in readme
    # every PNG carries the credit in its metadata
    for name, data in files.items():
        if name.endswith(".png"):
            text = Image.open(io.BytesIO(data)).text
            assert "zenodo" not in text["Copyright"], name
            assert text["Author"] == "Vitki (beräknad); skanning: okänd skannare", name
            assert "Bilden är beräknad i Vitki" in text["Description"], name
            assert groove_export.UNKNOWN_SCAN in text["Description"], name
            assert text["Software"] == "Vitki 3.0.0" and json.loads(text["Comment"])["method_version"] == "groove-5"
    # the full JSON: the result without its images, plus labels, credit and export
    full = json.loads(files["So_370_analys.json"])
    assert full["type"] == "vitki-groove-export" and full["schema"] == 1 and full["mode"] == "auto"
    assert "image_base64" not in full["result"] and "groove_map_base64" not in full["result"]
    assert full["result"]["slices"] == auto["slices"] and full["result"]["counts"] == auto["counts"]
    assert full["labels"] == _labels(auto) and full["credit"]["credit_text"] is None
    assert set(full["groups"]) == {"rune"}


def test_slices_csv_numbers_equal_the_result(client, auto):
    r = _export(client, "", ["slices_csv"], auto, labels_json=json.dumps(_labels(auto)), mode="auto")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "text/csv; charset=utf-8"
    meta, header, rows = _csv_rows(r.content)
    assert header == groove_export.SLICE_COLUMNS
    keys = {m[2:].split(":", 1)[0] for m in meta}
    assert {"Tabell", "Källa", "Exporterad från", "Datum", "Programvara", "Citering", "Skanning", "Skanningsfil",
            "Mätmetod", "Parametrar", "Koordinater"} <= keys
    assert len(rows) == len(auto["slices"])  # rejected slices too
    col = {c: i for i, c in enumerate(header)}
    for row, s in zip(rows, auto["slices"], strict=True):
        assert row[col["accepted"]] == ("true" if s["accepted"] else "false")
        assert row[col["label"]] == ("rune" if s["accepted"] else "excluded")
        assert (row[col["reason"]] or None) == s.get("reason")
        for k in ("apex_vinkel_deg", "spårdjup_mm", "spårbredd_mm", "ytråhet_mm", "fit_r2", "halfwidth_mm", "img_x"):
            if s.get(k) is None:
                assert row[col[k]] == ""
            else:
                assert float(row[col[k]]) == s[k]  # exact: written with repr, no rounding
        if s.get("point"):
            assert [float(row[col[f"point_{a}"]]) for a in "xyz"] == s["point"]
    # in the automatic analysis the group is the label; feature_type is left empty rather than contradicting it
    assert {row[col["feature_type"]] for row in rows} == {""}
    assert any("feature_type är tom" in m for m in meta)
    # pandas reads it with the documented options
    pd = pytest.importorskip("pandas")
    df = pd.read_csv(io.BytesIO(r.content), comment="#", encoding="utf-8-sig")
    assert len(df) == len(auto["slices"]) and abs(df["apex_vinkel_deg"].mean() - np.nanmean(
        [s.get("apex_vinkel_deg", np.nan) for s in auto["slices"]])) < 1e-9


def test_summary_runes_and_profiles_csv(client, auto):
    r = _export(client, "", ["summary_csv", "runes_csv", "profiles_csv"], auto, mode="auto")
    files = _zip(r.content)
    _, header, rows = _csv_rows(files["vitki_sammanfattning.csv"])
    assert header == groove_export.SUMMARY_COLUMNS
    # no labels sent: every slice counts as unknown, as in fromSession; with all accepted slices in one group the
    # recomputed summary is the analysis' own
    per = {(row[0], row[1], row[2]): row for row in rows}
    assert {row[0] for row in rows} == {"unknown"}
    s = auto["summary"]["apex_vinkel_deg"]
    row = per[("unknown", "per_snitt", "apex_vinkel_deg")]
    assert float(row[4]) == s["mean"] and float(row[6]) == s["ci95"][0] and int(row[3]) == s["n"]
    # per rune only in the rune group: an unlabelled ("unknown") group gets per-slice rows only
    assert not any(k[1] == "per_runa" for k in per)
    # labelled as runes, the per-rune rows are the analysis' own rune summary
    r2 = _export(client, "", ["summary_csv"], auto, mode="auto", labels_json=json.dumps(_labels(auto)))
    _, _, rows2 = _csv_rows(r2.content)
    per2 = {(row[0], row[1], row[2]): row for row in rows2}
    rs = auto["rune_summary"]["metrics"]["apex_vinkel_deg"]
    row = per2[("rune", "per_runa", "apex_vinkel_deg")]
    assert float(row[4]) == rs["mean"] and int(row[11]) == auto["rune_summary"]["n_runes"]
    assert (row[10] == "" and rs["icc"] is None) or float(row[10]) == rs["icc"]
    # not when the analysis measured every groove (facit mode, runes_only false): it made no rune summary itself
    facit = json.loads(json.dumps(auto))
    facit["provenance"]["parameters"]["runes_only"] = False
    _, _, rows3 = _csv_rows(_export(client, "", ["summary_csv"], facit, mode="auto",
                                    labels_json=json.dumps(_labels(auto))).content)
    assert not any(row[1] == "per_runa" for row in rows3)
    meta, header, rows = _csv_rows(files["vitki_runor.csv"])
    assert header == groove_export.RUNE_COLUMNS and len(rows) == len(auto["runes"])
    assert any(f"candidates: {auto['counts']['candidates']}" in m for m in meta)
    assert float(rows[0][2]) == auto["runes"][0]["height_mm"]
    assert float(rows[0][4]) == pytest.approx(auto["runes"][0]["box"][0] * auto["image_width"])
    _, header, rows = _csv_rows(files["vitki_profiler.csv"])
    first = next(s for s in auto["slices"] if s.get("profile"))
    i = auto["slices"].index(first) + 1
    mine = [r_ for r_ in rows if int(r_[0]) == i]
    assert [float(r_[4]) for r_ in mine] == first["profile"]["x"]
    assert [float(r_[5]) for r_ in mine] == first["profile"]["z"]


def test_depth_grid_header_and_values(client, stone, auto):
    mid = _upload(client, stone[1])
    r = _export(client, mid, ["depth_grid"], None, normal_x=N[0], normal_y=N[1], normal_z=N[2])
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"  # two files
    files = _zip(r.content)
    asc = files["vitki_djup_under_stenytan_mm.asc"].decode("ascii").splitlines()
    head = dict(line.split() for line in asc[:6])
    surf = stone_report.Surface(_server_mesh(client, stone), N, None)
    assert float(head["cellsize"]) == surf.res and head["NODATA_value"] == "-9999"
    assert (int(head["ncols"]), int(head["nrows"])) == (surf.H.shape[1], surf.H.shape[0])
    grid = np.array([[float(v) for v in line.split()] for line in asc[6:]])
    assert int((grid == -9999).sum()) == int((~surf.inner).sum())
    want = np.flipud(stone_report.depth_array(surf))
    ok = grid != -9999
    assert np.allclose(grid[ok], want[ok], atol=5e-4) and (grid[ok] >= 0).all()
    side = json.loads(files["vitki_djup_under_stenytan_mm.json"])
    assert side["cellsize_mm"] == surf.res and side["unit"] == "mm" and side["edge_zone_mm"] == 10
    assert side["normal_source"] == "vy" and side["nodata_cells"] == int((~surf.inner).sum())
    assert side["heatmap_vmax_mm"] == stone_report.depth_vmax(surf)
    assert np.allclose(side["origin_mm"], surf.origin) and np.allclose(side["basis"]["n"], surf.hf.n)


def test_single_files_and_media_types(client, stone, auto):
    mid = _upload(client, stone[1])
    for item, media in (("summary_csv", "text/csv; charset=utf-8"), ("full_json", "application/json"),
                        ("depth_heatmap", "image/png"),
                        # no visible credit on these, so never a bare image: always with README.txt
                        ("groove_map", "application/zip"), ("relief", "application/zip")):
        r = _export(client, mid, [item], auto, mode="auto")
        assert r.status_code == 200, (item, r.text)
        assert r.headers["content-type"] == media, item
        assert r.headers["x-export-files"].count(",") == 0
        if media == "application/zip":
            assert {"README.txt", "kalla.json"} <= _zip(r.content).keys()
    r = _export(client, mid, ["summary_csv"], auto, mode="auto", as_zip="1")
    assert r.headers["content-type"] == "application/zip"
    assert {"README.txt", "kalla.json", "vitki_sammanfattning.csv"} <= _zip(r.content).keys()


def test_images_keep_the_analysis_pixels(client, stone, auto):
    import base64
    mid = _upload(client, stone[1])
    files = _zip(_export(client, mid, ["groove_map", "review_image", "relief"], auto, mode="auto").content)
    gm = Image.open(io.BytesIO(files["vitki_ristningskarta.png"]))
    orig = Image.open(io.BytesIO(base64.b64decode(auto["groove_map_base64"].split(",", 1)[1])))
    assert gm.mode == "L" and np.array_equal(np.asarray(gm), np.asarray(orig))
    assert json.loads(gm.text["Comment"])["scale"]["black_mm"] == auto["groove_map_scale"]["black_mm"]
    rv = Image.open(io.BytesIO(files["vitki_granskningsbild.png"]))
    orig = Image.open(io.BytesIO(base64.b64decode(auto["image_base64"].split(",", 1)[1]))).convert("RGB")
    assert rv.width == orig.width and rv.height > orig.height  # legend and credit below
    assert np.array_equal(np.asarray(rv)[:orig.height], np.asarray(orig))  # img_x/img_y stay valid
    rel = Image.open(io.BytesIO(files["vitki_relief.png"]))
    meta = json.loads(rel.text["Comment"])
    assert rel.mode == "L" and meta["normal_source"] == "analys" and meta["mm_per_px"] > 0
    # the native grid, not upscaled: one pixel per Surface cell
    surf = stone_report.Surface(_server_mesh(client, stone), auto["parameters"]["normal"], auto["parameters"]["up"])
    assert rel.size == (surf.H.shape[1], surf.H.shape[0]) and meta["mm_per_px"] == surf.res
    assert "okänd" in rel.text["Author"]  # no signum: the credit says the scanner is unknown


def test_older_auto_result_without_scale(client, auto):
    old = {k: v for k, v in auto.items() if k != "groove_map_scale"}
    r = _export(client, "", ["groove_map"], old, mode="auto")
    text = Image.open(io.BytesIO(_zip(r.content)["vitki_ristningskarta.png"])).text
    assert groove_export.OLD_SCALE in text["Description"]


def test_one_click_result(client, stone):
    m = stone[0]
    mid = _upload(client, stone[1])
    centre = (m.bounds[0] + m.bounds[1]) / 2
    p = m.vertices[np.argmin(np.linalg.norm(m.vertices[:, :2] - [-50, 0], axis=1))] - centre
    res = client.post("/api/3d/auto_slice", data={"mesh_id": mid, "point_x": p[0], "point_y": p[1], "point_z": p[2],
                                                   "slice_count": "5", "feature_type": "ornament"}).json()
    r = _export(client, mid, ["slices_csv", "positions_figure", "spatial_figure", "profiles_figure"], res,
                mode="oneclick", feature_type="ornament", normal_x=N[0], normal_y=N[1], normal_z=N[2],
                scan_note="Skannad av Testare, CC BY 4.0")
    assert r.status_code == 200, r.text
    files = _zip(r.content)
    _, header, rows = _csv_rows(files["vitki_snitt.csv"])
    col = {c: i for i, c in enumerate(header)}
    assert len(rows) == len(res["slices"]) and {row[col["label"]] for row in rows} == {"ornament"}
    assert {row[col["mode"]] for row in rows} == {"oneclick"} and {row[col["img_x"]] for row in rows} == {""}
    png = Image.open(io.BytesIO(files["vitki_snittpositioner_v_vinkel.png"]))
    meta = json.loads(png.text["Comment"])
    assert "Skannad av Testare" in png.text["Description"] and groove_export.USER_SCAN in png.text["Description"]
    # the exporter's own text is marked as theirs in every field, not only in Copyright
    for k in ("Copyright", "Source"):
        assert png.text[k] == "enligt den som exporterade: Skannad av Testare, CC BY 4.0", k
    assert png.text["Author"] == "Vitki (beräknad); skanning enligt den som exporterade: Skannad av Testare, CC BY 4.0"
    # the stone report's normal (the slices' mean up), not the 3D view that was sent; a figure has no mm per pixel
    assert meta["normal_source"] == "snitt" and meta["mm_per_px"] is None and meta["surface_cell_mm"] > 0
    assert "vitki_tvarsnittsprofiler.png" in files


def test_length_profile_and_build_directly():
    result = {"slices": [{"apex_vinkel_deg": 70.0, "asymmetri_deg": 1.0, "spårdjup_mm": 2.0, "spårbredd_mm": 5.0,
                          "djup_bredd_kvot": 0.4, "bottenradie_mm": 0.3, "ytråhet_mm": 0.02, "fit_r2": 0.99,
                          "position_mm": 0.0}],
              "summary": {}, "depth_profile": {"distances": [0.0, 1.5, 3.25], "depths": [1.0, 2.125, 1.5]}}
    files, skipped = groove_export.build(["length_profile_csv", "relief", "runes_csv"], result=result, mode="path",
                                         signum="U 9999")
    assert [f[0] for f in files] == ["U_9999_langdprofil.csv"]
    assert dict(skipped) == {"relief": "ingen 3D-modell", "runes_csv": "inga runor (bara automatisk analys)"}
    meta, header, rows = _csv_rows(files[0][1])
    assert header == ["distance_mm", "spårdjup_mm"] and rows == [["0.0", "1.0"], ["1.5", "2.125"], ["3.25", "1.5"]]
    assert any(groove_export.UNKNOWN_SCAN_TEXT in m for m in meta)


def test_export_errors(client, stone, auto, monkeypatch):
    mid = _upload(client, stone[1])
    assert _export(client, mid, ["nope"], auto).status_code == 400
    assert _post_export(client, {"mesh_id": mid, "items": "summary_csv", "result_json": "{not json"}).status_code == 400
    assert _post_export(client, {"items": "relief"}).status_code == 400  # an image needs the model
    assert _export(client, "0" * 64, ["relief"]).status_code == 404  # the client uploads again
    # data items need no model, so an id the engine has forgotten is harmless
    assert _export(client, "0" * 64, ["summary_csv"], auto).status_code == 200
    r = _export(client, mid, ["runes_csv", "length_profile_csv"], {"slices": []})
    assert r.status_code == 422 and r.json()["detail"] == "Inget av de valda kan exporteras för den här analysen."
    # larger than Starlette's 1 MB per field is fine; above the limit gives 413
    big = {**auto, "pad": "x" * 1_500_000}
    assert _export(client, "", ["summary_csv"], big).status_code == 200
    monkeypatch.setattr(threed, "MAX_EXPORT_JSON", 100_000)
    assert _export(client, "", ["summary_csv"], big).status_code == 413


@pytest.mark.skipif(not os.path.exists(SO370), reason="skanningen av Sö 370 finns inte på maskinen")
def test_real_scan_so370_heatmap_carries_the_credit(client):
    """Sö 370 ur Kitzler Åhfeldts Södermanlandsserie (CC BY 4.0, doi:10.5281/zenodo.11951255)."""
    with open(SO370, "rb") as f:
        mid = _upload(client, f.read(), os.path.basename(SO370))
    r = _export(client, mid, ["depth_heatmap"], None, signum="Sö 370")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/png"
    assert r.headers["content-disposition"].startswith('attachment; filename="So_370_djup_under_stenytan.png"')
    img = Image.open(io.BytesIO(r.content))
    # the uploaded file is the published one (SHA-256 and md5 match data/scan_files.json)
    credit = groove_export.scan_credit(os.path.basename(SO370), size=os.path.getsize(SO370))
    assert credit["known"] and img.mode == "RGBA" and round(img.info["dpi"][0]) == 220
    assert credit["credit_text"] in img.text["Description"]
    assert img.text["Copyright"] == "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), doi:10.5281/zenodo.11951255"
    assert img.text["Author"] == "Vitki (beräknad); skanning: Laila Kitzler Åhfeldt (Riksantikvarieämbetet)"
    assert "zenodo.11951255" in img.text["Source"]
    assert img.text["Title"] == "Sö 370 – djup under stenytan"
    meta = json.loads(img.text["Comment"])
    assert meta["normal_source"] == "uppskattad" and meta["mesh"]["filename"] == os.path.basename(SO370)
    assert meta["scan_identified"] and meta["scan_match"] == "sha256"
    # the figure itself is the stone report's figure 2, pixel for pixel, with the credit strip below
    import base64
    import trimesh
    m = trimesh.load(SO370, force="mesh")
    m.apply_translation(-(m.bounds[0] + m.bounds[1]) / 2)
    surf = stone_report.Surface(m, threed._estimated_normal(m), None)
    fig = Image.open(io.BytesIO(base64.b64decode(stone_report.depth_figure(surf))))
    assert img.width == fig.width and img.height > fig.height
    assert np.array_equal(np.asarray(img)[:fig.height], np.asarray(fig))
    assert meta["scale"]["vmax_mm"] == stone_report.depth_vmax(surf) and meta["mm_per_px"] is None
    assert meta["surface_cell_mm"] == surf.res


# ---- credit, labels, mode, view and robustness ------------------------------------------------------------------------

def test_published_file_in_the_provenance_gets_the_credit(client, auto):
    """A data export of an analysis made on the published Sö 370 file credits the dataset; the same name with another
    checksum does not."""
    res = json.loads(json.dumps(auto))
    res["provenance"]["mesh"] = {"filename": SO370_NAME, "bytes": SO370_BYTES}
    r = _export(client, "", ["summary_csv"], res, signum="U 9999")
    meta, _, _ = _csv_rows(r.content)
    line = next(m for m in meta if m.startswith("# Skanning:"))
    assert "Laila Kitzler Åhfeldt (Riksantikvarieämbetet)" in line and "doi:10.5281/zenodo.11951255" in line
    assert "https://creativecommons.org/licenses/by/4.0/" in line and "Runristandets dynamik" in line
    res["provenance"]["mesh"]["sha256"] = "ab" * 32
    meta, _, _ = _csv_rows(_export(client, "", ["summary_csv"], res).content)
    assert any(groove_export.UNKNOWN_SCAN_TEXT in m for m in meta)


def test_stone_report_credits_the_file_not_the_signum(auto):
    """The stone report decides the scan credit as the export does: a typed signum with an unrecognised file gives no
    third-party credit; the published file (from the provenance or the loaded model) does."""
    def facts(mesh, mesh_info=None, signum="Sö 370"):
        prov = {**auto["provenance"], "mesh": mesh}
        return stone_report.build_facts({"signum": signum, "analyses": [{"feature_type": "rune", "slices": [],
                                                                          "provenance": prov}]},
                                        lambda s: None, mesh_info)
    f = facts({"filename": "egen.stl", "sha256": "ab" * 32, "md5": "cd" * 16, "bytes": 5})
    assert f["scan_source"] is None and not f["scan"].get("citation")
    f = facts({"filename": SO370_NAME, "md5": SO370_MD5, "bytes": SO370_BYTES}, signum="U 9999")
    assert f["scan_source"]["key"] == "sodermanland" and f["scan_file"]["signum"] == "Sö 370"
    assert f["scan"]["license"] == "CC BY 4.0"
    # the loaded model completes the provenance only when it is the same file
    f = facts({"filename": SO370_NAME}, {"filename": SO370_NAME, "md5": SO370_MD5, "bytes": SO370_BYTES})
    assert f["scan_source"]["key"] == "sodermanland"
    f = facts({"filename": SO370_NAME, "sha256": "ab" * 32}, {"sha256": "cd" * 32, "md5": SO370_MD5,
                                                               "bytes": SO370_BYTES})
    assert f["scan_source"] is None
    f = facts({"filename": SO370_NAME})  # a name alone is not enough
    assert f["scan_source"] is None


def test_labels_are_honoured_as_in_the_stone_report(client, stone, auto):
    """Excluded slices leave the summaries and figures, the other labels form groups, and the summaries are the
    project's own functions on those groups (fromSession, stone_report.build_facts)."""
    from src.stats import summarize_by_rune, summarize_slices
    acc = [i for i, s in enumerate(auto["slices"]) if s["accepted"]]
    assert len(acc) >= 6
    labels = ["excluded" if not s["accepted"] else "rune" for s in auto["slices"]]
    for i in acc[:2]:
        labels[i] = "excluded"
    for i in acc[2:4]:
        labels[i] = "ornament"
    labels = labels[:-1]  # a missing label counts as unknown
    mid = _upload(client, stone[1])
    r = _export(client, mid, ["summary_csv", "slices_csv", "full_json", "positions_figure"], auto,
                labels_json=json.dumps(labels), mode="oneclick")
    assert r.status_code == 200, r.text
    files = _zip(r.content)
    want_labels = [*labels, "unknown"]
    groups = {}
    for i, s in enumerate(auto["slices"]):
        if s["accepted"] and want_labels[i] != "excluded":
            groups.setdefault(want_labels[i], []).append(s)
    _, header, rows = _csv_rows(files["vitki_sammanfattning.csv"])
    col = {c: i for i, c in enumerate(header)}
    per = {(row[0], row[1], row[2]): row for row in rows}
    assert {row[0] for row in rows} == set(groups)
    for g, sl in groups.items():
        want = summarize_slices(sl)["apex_vinkel_deg"]
        row = per[(g, "per_snitt", "apex_vinkel_deg")]
        assert float(row[col["medel"]]) == want["mean"] and int(row[col["n"]]) == want["n"]
        if g == "rune":
            rw = summarize_by_rune(sl)
            row = per[(g, "per_runa", "apex_vinkel_deg")]
            assert float(row[col["medel"]]) == rw["metrics"]["apex_vinkel_deg"]["mean"]
            assert int(row[col["n_runor"]]) == rw["n_runes"]
        else:
            # the ornament and unknown groups get no per-rune rows: their rune_id is the automatic recognition's
            assert not any(k[0] == g and k[1] == "per_runa" for k in per), g
    # the mode is the analysis' own (automatic), not the form's
    _, header, rows = _csv_rows(files["vitki_snitt.csv"])
    col = {c: i for i, c in enumerate(header)}
    assert {row[col["mode"]] for row in rows} == {"auto"}
    assert [row[col["label"]] for row in rows] == want_labels
    full = json.loads(files["vitki_analys.json"])
    assert full["mode"] == "auto" and full["labels"] == want_labels and set(full["groups"]) == set(groups)
    assert full["groups"]["rune"]["n_slices"] == len(groups["rune"])
    # the figure uses the grouped slices only, in the stone report's order
    ctx = groove_export._Context(mesh_entry=None, surface_factory=None, result=auto, labels=labels, signum="",
                                 credit=None, view=None, mode=None, feature_type="rune")
    assert ctx.measured == [s for g in ("rune", "ornament", "unknown") for s in groups.get(g, [])]
    assert all(want_labels[auto["slices"].index(s)] != "excluded" for s in ctx.measured)


def test_mode_comes_from_the_analysis(client, stone):
    m = stone[0]
    mid = _upload(client, stone[1])
    centre = (m.bounds[0] + m.bounds[1]) / 2
    p = m.vertices[np.argmin(np.linalg.norm(m.vertices[:, :2] - [-50, 0], axis=1))] - centre
    res = client.post("/api/3d/auto_slice", data={"mesh_id": mid, "point_x": p[0], "point_y": p[1], "point_z": p[2],
                                                   "slice_count": "5", "feature_type": "ornament"}).json()
    r = _export(client, "", ["slices_csv"], res, mode="path", feature_type="rune")
    _, header, rows = _csv_rows(r.content)
    col = {c: i for i, c in enumerate(header)}
    assert {row[col["mode"]] for row in rows} == {"oneclick"}
    assert {row[col["feature_type"]] for row in rows} == {"ornament"}  # the analysis' own type
    assert groove_export.analysis_mode({}, "path") == "path"
    assert groove_export.analysis_mode({"provenance": {"parameters": {"mode": "slices"}}}, "auto") == "manual"


def test_surface_normal_is_the_stone_reports(client, stone):
    """The heat map of a one-click measurement is the stone report's figure 2 with the report's own normal."""
    import base64
    from api.routers import reports
    m = stone[0]
    mid = _upload(client, stone[1])
    centre = (m.bounds[0] + m.bounds[1]) / 2
    p = m.vertices[np.argmin(np.linalg.norm(m.vertices[:, :2] - [-50, 0], axis=1))] - centre
    res = client.post("/api/3d/auto_slice", data={"mesh_id": mid, "point_x": p[0], "point_y": p[1], "point_z": p[2],
                                                   "slice_count": "5"}).json()
    req = reports.StoneReportRequest(analyses=[{"feature_type": "rune", "slices": res["slices"],
                                                "provenance": res["provenance"]}])
    normal, up = reports._view(req)
    assert normal is not None
    r = _export(client, mid, ["depth_heatmap"], res, normal_x=1, normal_y=0, normal_z=0)  # the view is not used
    img = Image.open(io.BytesIO(r.content))
    assert json.loads(img.text["Comment"])["normal_source"] == "snitt"
    surf = stone_report.Surface(_server_mesh(client, stone), normal, up)
    fig = Image.open(io.BytesIO(base64.b64decode(stone_report.depth_figure(surf))))
    assert np.array_equal(np.asarray(img)[:fig.height], np.asarray(fig))


def _png_b64(img) -> str:
    import base64
    buf = io.BytesIO()
    img.save(buf, format=img.format or "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def test_malformed_input_gives_400(client, stone, auto):
    import base64
    mid = _upload(client, stone[1])
    labels = json.dumps(_labels(auto))
    bad = [
        dict(items="summary_csv", result_json=json.dumps({**auto, "slices": "x"})),
        dict(items="summary_csv", result_json=json.dumps({**auto, "slices": [1, 2]})),
        dict(items="summary_csv", result_json=json.dumps({**auto, "slices": [{**auto["slices"][0], "point": "a"}]})),
        dict(items="summary_csv", result_json=json.dumps({**auto, "summary": []})),
        dict(items="summary_csv", result_json=json.dumps({**auto, "slices": [{**auto["slices"][0], "rune_id": {"x": 1}}]}),
             labels_json=json.dumps(["rune"])),
        dict(items="summary_csv", result_json=json.dumps({**auto, "slices": [{**auto["slices"][0], "stroke_id": True}]})),
        dict(items="summary_csv", result_json=json.dumps(auto), labels_json=json.dumps(["rune", "nope"])),
        dict(items="summary_csv", result_json=json.dumps(auto), labels_json=json.dumps(["rune"] * 100000)),
        dict(items="summary_csv", result_json=json.dumps(auto), labels_json="{}"),
        dict(items="summary_csv", result_json="[1]"),
        dict(items="relief", normal_x="a", normal_y="0", normal_z="1"),
        dict(items="relief", normal_x="0", normal_y="0"),
        dict(items="relief", normal_x="0", normal_y="0", normal_z="0"),
        dict(items="summary_csv", signum="S" * 150),
        dict(items="summary_csv", mesh_id="../etc"),
        dict(items="summary_csv", as_zip="maybe"),
        dict(items="summary_csv", mode="x"),
        dict(items="summary_csv", feature_type="x"),
        dict(items="x" * 3000),
    ]
    for data in bad:
        data.setdefault("mesh_id", mid)
        r = _post_export(client, data)
        assert r.status_code == 400, (list(data), r.status_code, r.text[:200])
    # embedded images: PNG only, within the size limits
    jpg = Image.new("RGB", (10, 10))
    buf = io.BytesIO()
    jpg.save(buf, format="JPEG")
    as_png_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    for img in (as_png_url, "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii"),
                "data:image/png;base64,!!!", _png_b64(Image.new("L", (groove_export.MAX_IMAGE_SIDE + 1, 2)))):
        r = _export(client, "", ["groove_map"], {**auto, "groove_map_base64": img}, labels_json=labels)
        assert r.status_code == 400, r.text
    # a result from another scan than the loaded model
    other = json.loads(json.dumps(auto))
    other["provenance"]["mesh"]["sha256"] = "f" * 64
    assert _export(client, mid, ["relief"], other).status_code == 400


def test_signum_is_sanitised(client, auto):
    r = _export(client, "", ["full_json"], auto, signum="Sö\u0000 370\n\t ")
    assert r.status_code == 200, r.text
    assert json.loads(r.content)["signum"] == "Sö 370"
    assert groove_export.clean_signum("  Sö\u200b  370 ") == "Sö 370"


def test_one_export_at_a_time(client, auto, monkeypatch):
    sem = __import__("threading").BoundedSemaphore(1)
    monkeypatch.setattr(threed, "_EXPORT_SLOT", sem)
    assert sem.acquire(blocking=False)
    try:
        r = _export(client, "", ["summary_csv"], auto)
        assert r.status_code == 429
    finally:
        sem.release()
    assert _export(client, "", ["summary_csv"], auto).status_code == 200


def test_texts_match_the_code():
    """The help texts say what the code does (findings on percentile direction, fit_r2, rim level, hands, ICC)."""
    by = groove_export.BY_ID
    assert "djupare än analysens tröskel" in by["groove_map"]["explanation"]
    assert "under tröskeln" not in json.dumps(groove_export.catalogue(), ensure_ascii=False)
    assert "Den automatiska analysen sorterar bort snitt med fit_r2 under 0,8" in by["slices_csv"]["explanation"]
    assert "spårkanternas nivå" in by["profiles_figure"]["explanation"]
    assert "hand" not in by["positions_figure"]["explanation"]
    assert "negativ" in by["summary_csv"]["explanation"]
    assert "oftast omkring 1 mm" not in by["depth_grid"]["explanation"]


def test_malformed_summaries_give_400_not_500(client, auto):
    """Shapes that validate_result used to let through to the builders (a 500 with a server traceback)."""
    for extra in ({"rune_summary": {"metrics": [1]}}, {"rune_summary": {"metrics": {"apex_vinkel_deg": 5}}},
                  {"rune_summary": {"n_runes": "x"}}, {"tool_heuristic": {"label": "x", "adjustments": 5}},
                  {"summary": {"apex_vinkel_deg": 5}}):
        res = {"slices": auto["slices"][:3], "summary": {}, **extra}
        r = _export(client, "", ["summary_csv"], res, mode="manual")
        assert r.status_code == 400, (extra, r.status_code, r.text[:200])


def test_form_limits(client, auto):
    data = {"items": "summary_csv", "result_json": json.dumps(auto)}
    # URL-encoded bodies have no part limit in Starlette: refused
    assert client.post("/api/3d/export", data=data).status_code == 415
    # too many fields
    assert threed.MAX_EXPORT_FIELDS >= 15  # what the page sends
    many = {**{f"x{i}": "1" for i in range(threed.MAX_EXPORT_FIELDS)}, "items": "full_json"}
    assert _post_export(client, many).status_code == 400
    # Content-Length above the limit is refused before the body is read
    big = threed.MAX_EXPORT_JSON * 2 + threed.EXPORT_BODY_MARGIN + 1
    r = client.post("/api/3d/export", content=b"x", headers={"content-type": "multipart/form-data; boundary=b",
                                                               "content-length": str(big)})
    assert r.status_code == 413


def test_table_export_after_another_model_is_loaded(client, stone, auto):
    """Tables need no model: an analysis of another scan than the loaded model is exported with its own provenance;
    images are still refused."""
    mid = _upload(client, stone[1])
    other = json.loads(json.dumps(auto))
    other["provenance"]["mesh"] = {"filename": SO370_NAME, "bytes": SO370_BYTES, "sha256": "f" * 64}
    r = _export(client, mid, ["slices_csv"], other, mode="auto")
    assert r.status_code == 200, r.text
    meta, _, _ = _csv_rows(r.content)
    assert any("f" * 64 in m and SO370_NAME in m for m in meta if m.startswith("# Skanningsfil:"))
    assert _export(client, mid, ["relief"], other).status_code == 400


def test_csv_credit_is_not_doubled_and_says_table(client, auto):
    r = _export(client, "", ["slices_csv"], auto, mode="auto")
    meta, _, _ = _csv_rows(r.content)
    line = next(m for m in meta if m.startswith("# Skanning:"))
    assert line == "# Skanning: " + groove_export.UNKNOWN_SCAN_TEXT + " " + groove_export.TABLE_NOTE
    assert not any("Bilden är beräknad" in m for m in meta)
    assert any("position_mm är provpunktens ordningsnummer" in m for m in meta)


def test_readme_lists_the_stone_specific_limits(client, auto):
    """README.txt carries the per-group warnings and the protocol notes, not only the summary CSV."""
    res = json.loads(json.dumps(auto))
    res["provenance"]["protocol"] = {"version": "p1", "compliant": False, "deviations": ["rutnät 0,9 mm"],
                                     "notes": ["skanningens punktavstånd 0,80 mm är större än rekommenderade 0,5 mm"]}
    files = _zip(_export(client, "", ["summary_csv"], res, mode="auto", as_zip="1").content)
    readme = " ".join(files["README.txt"].decode("utf-8").split())
    ctx = groove_export._Context(mesh_entry=None, surface_factory=None, result=res, labels=None, signum="",
                                 credit=None, view=None, mode=None, feature_type="rune")
    notes = ctx.specific_notes()
    assert notes and all(" ".join(n.split()) in readme for n in notes)
    assert "rutnät 0,9 mm" in readme and "punktavstånd 0,80 mm" in readme


def test_profile_letters_follow_the_picks():
    """A profile that cannot be refitted keeps its letter empty instead of shifting the following ones."""
    from src.stone_report import profiles_figure
    good = {"x": list(np.linspace(-5, 5, 41)), "z": [abs(v) - 3 for v in np.linspace(-5, 5, 41)]}
    s = {"apex_vinkel_deg": 90.0, "spårdjup_mm": 2.0, "spårbredd_mm": 6.0}
    slices = [{**s, "profile": {"x": [0, 1], "z": [0, 1]}}, {**s, "profile": good}]
    import matplotlib.axes
    titles = []
    orig = matplotlib.axes.Axes.set_title
    matplotlib.axes.Axes.set_title = lambda self, label, *a, **k: (titles.append(label), orig(self, label, *a, **k))[1]
    try:
        assert profiles_figure(slices, [0, 1]) is not None
    finally:
        matplotlib.axes.Axes.set_title = orig
    assert [t.split()[0] for t in titles] == ["B"]
