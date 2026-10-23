import base64
import datetime
import hashlib
import io
import json
import os
import re
import threading

import numpy as np
import trimesh
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException

from api import mesh_cache
from api.config import APP_NAME, APP_VERSION, METHOD_VERSION
from api.errors import server_error
from api.mesh_cache import MeshEntry
from api.uploads import save_mesh_upload
from src.auto_grooves import analyze_grooves, auto_slice
from src.slice_analysis import (
    DEFAULT_WINDOW_MM,
    analyze_path as slice_analyze_path,
    calculate_v_angle,
    create_mock_v_groove_mesh,
    extract_2d_profile_from_mesh,
    raw_profile,
    snap_path_to_bottom,
)
from src import groove_export, limitations
from src.groove_export import gray_image, relief_images  # noqa: F401 - relief_images is part of this router's API
from src import protocol as protocol_spec
from src.stats import METRICS, summarize_by_rune, summarize_slices

router = APIRouter()

FEATURE_TYPES = ("rune", "ornament", "unknown")
MAX_VIEW_FACES = int(os.environ.get("MAX_VIEW_FACES", "1500000"))
NO_MESH = ("Ingen 3D-modell angiven. Ladda upp en STL-, OBJ- eller PLY-fil först "
           "(appen använder aldrig testdata i stället).")


def _digests(path: str) -> tuple[str, str, int]:
    """SHA-256 (the model's id), md5 (what Zenodo publishes for its files, src/scan_sources.identify) and size."""
    h, m, n = hashlib.sha256(), hashlib.md5(), 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
            m.update(chunk)
            n += len(chunk)
    return h.hexdigest(), m.hexdigest(), n


def _load_upload(file: UploadFile) -> MeshEntry:
    """Läser in en uppladdad fil, centrerar den som Three.js geo.center() och lägger den i cachen."""
    tmp_path = save_mesh_upload(file)
    try:
        digest, md5, size = _digests(tmp_path)
        cached = mesh_cache.peek(digest)
        if cached is not None:
            return cached
        mesh = trimesh.load(tmp_path, force="mesh")
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(e, "Kunde inte ladda 3D-filen. Kontrollera att filen är en giltig STL/OBJ/PLY.",
                           status_code=400) from e
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if mesh is None or len(mesh.faces) == 0:
        raise HTTPException(status_code=400, detail="3D-filen innehåller ingen yta att analysera.")
    centre = (mesh.bounds[0] + mesh.bounds[1]) / 2.0
    mesh.apply_translation(-centre)
    info = {
        "mock": False,
        "mesh_id": digest,
        "filename": file.filename,
        "sha256": digest,
        "md5": md5,
        "bytes": size,
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "extent_mm": [float(v) for v in mesh.extents],
        "centered_by": [float(v) for v in centre],
    }
    return mesh_cache.put(digest, MeshEntry(mesh, info))


_TRUE = {"1", "true", "t", "yes", "y", "on"}
_FALSE = {"0", "false", "f", "no", "n", "off"}


def form_flag(value: str | None, default: bool, name: str) -> bool:
    """A yes/no form field that is True when left out. Read as text, because FastAPI >= 0.160 turns a missing
    `bool = Form(True)` field into False (as an unticked HTML checkbox); accepts the same words as pydantic's bool."""
    if value is None:
        return default
    v = value.strip().lower()
    if v in _TRUE:
        return True
    if v in _FALSE:
        return False
    raise HTTPException(status_code=422, detail=f"{name} måste vara true eller false.")


def resolve_mesh(file: UploadFile | None, mesh_id: str | None, use_mock: bool = False) -> MeshEntry:
    """Hämtar modellen via id (cache), en uppladdad fil eller – bara om det uttryckligen begärs – testmodellen."""
    if mesh_id:
        return mesh_cache.get(mesh_id)
    if file is not None:
        return _load_upload(file)
    if use_mock:
        mesh = create_mock_v_groove_mesh()
        return MeshEntry(mesh, {"mock": True, "faces": int(len(mesh.faces))})
    raise HTTPException(status_code=400, detail=NO_MESH)


def tool_heuristic(angle: float, stone: str, weathering: str) -> dict:
    """Tumregel för verktygstyp utifrån V-vinkeln. Inte kalibrerad mot referensmaterial:
    justeringarna för vittring och mjuk sten är antaganden och redovisas därför öppet."""
    threshold = 85.0
    adjustments = []
    if weathering == "Hög":
        threshold += 5
        adjustments.append("+5° hög vittring (spåren vidgas)")
    elif weathering in ("Medel", "Mellan"):
        threshold += 2
        adjustments.append("+2° måttlig vittring")
    if stone in ("Sandsten", "Kalksten"):
        threshold += 2
        adjustments.append("+2° mjuk bergart")
    label = "Pikmejsel (spetsig profil)" if angle < threshold else "Bredmejsel (U-formad profil)"
    return {
        "label": label,
        "threshold_deg": threshold,
        "adjustments": adjustments,
        "note": "Heuristisk tumregel, ej kalibrerad mot referensmaterial.",
    }


def provenance(mesh_info: dict, parameters: dict, feature_type: str) -> dict:
    return {
        "software": APP_NAME,
        "version": APP_VERSION,
        "method_version": METHOD_VERSION,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "mesh": mesh_info,
        "feature_type": feature_type,
        "parameters": parameters,
        # Which known limitations (src/limitations.py) applied when the measurement was made
        "known_limitations": {"version": limitations.VERSION,
                              "keys": limitations.keys(["grooves", "software"]
                                                       + (["auto"] if parameters.get("mode") == "automatic" else []))},
    }


def _slice_record(res: dict, position_mm: float, x=None, z=None, point=None, direction=None, up=None) -> dict:
    rec = {**{k: float(res[k]) for k in METRICS}, "position_mm": float(position_mm), "fit_r2": float(res["fit_r2"])}
    if x is not None:
        rec["profile"] = raw_profile(x, z)
    # Where the slice lies on the model, so that reports can show it on the surface
    for key, v in (("point", point), ("direction", direction), ("up", up)):
        if v is not None:
            rec[key] = [float(c) for c in v]
    return rec


def _means(slices: list[dict]) -> dict:
    return {k: float(np.mean([s[k] for s in slices])) for k in METRICS}


def _check_feature_type(feature_type: str):
    if feature_type not in FEATURE_TYPES:
        raise HTTPException(status_code=400, detail="feature_type måste vara rune, ornament eller unknown.")


# What a slice's geometry normally fails with (too few points, a degenerate fit): skipped without a warning
_GEOMETRY_ERRORS = (ValueError, IndexError, FloatingPointError, ZeroDivisionError, np.linalg.LinAlgError)


def measure_slices(entry: MeshEntry, origin, direction, up, slice_count: int, spacing_mm: float,
                   window_mm: float, noise_rng=None):
    """Snitt med jämna mellanrum längs spåret kring origin. Returnerar (slices, huvudsnitt)."""
    groove_direction = np.asarray(direction, dtype=float)
    norm = np.linalg.norm(groove_direction)
    if norm == 0:
        raise HTTPException(status_code=400, detail="Spårriktningen saknas. Markera spåret på nytt.")
    groove_direction = groove_direction / norm
    origin = np.asarray(origin, dtype=float)
    face_tree = None if entry.info.get("mock") else entry.face_tree
    slices, main, unexpected = [], None, []
    start = -(slice_count - 1) / 2.0 * spacing_mm
    for i in range(slice_count):
        offset = start + i * spacing_mm
        try:
            x_2d, z_2d = extract_2d_profile_from_mesh(entry.mesh, origin + groove_direction * offset,
                                                      groove_direction, np.asarray(up, dtype=float),
                                                      window_mm=window_mm, face_tree=face_tree)
            if noise_rng is not None:
                z_2d = z_2d + noise_rng.normal(0, 0.1, size=z_2d.shape)
            res = calculate_v_angle(x_2d, z_2d)
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception as e:  # noqa: BLE001 - one bad slice must not stop the others
            # A slice with too few points, a degenerate fit or an error inside trimesh/scipy at one spot is skipped
            # (logged with what went wrong); the analysis reports how many slices succeeded. Errors that geometry
            # normally gives are logged quietly; any other kind (a TypeError from a changed signature, say) is
            # logged as a warning below, so that a code bug that makes every slice fail does not go unseen
            from api.errors import logger
            logger.debug("Snitt %d (%.2f mm) hoppades över: %r", i, offset, e)
            if not isinstance(e, _GEOMETRY_ERRORS):
                unexpected.append((i, e))
            continue
        if not all(np.isfinite(res[k]) for k in (*METRICS, "fit_r2")):
            continue  # too few points for a wall fit
        slices.append(_slice_record(res, offset, x_2d, z_2d, origin + groove_direction * offset,
                                    groove_direction, up))
        if i == slice_count // 2 or main is None:
            main = {"x_2d": res["x"], "z_2d": res["z"], "res": res}
    if unexpected:
        from api.errors import logger
        i, e = unexpected[0]
        logger.warning("%d av %d snitt hoppades över av ett oväntat fel (%d lyckades); första, snitt %d: %r",
                       len(unexpected), slice_count, len(slices), i, e)
    return slices, main


def _result(slices, main, entry, params, feature_type, meta_stone, meta_weathering, meta_text=""):
    means = _means(slices)
    tool = tool_heuristic(means["apex_vinkel_deg"], meta_stone, meta_weathering)
    res = main["res"]
    return {
        "results": {
            **means,
            "troligt_verktyg": tool["label"],
            "apex_idx": int(res["apex_idx"]),
            "left_shoulder": int(res.get("left_shoulder", 0)),
            "right_shoulder": int(res.get("right_shoulder", len(main["x_2d"]) - 1)),
            "successful_slices": len(slices),
            "meta_stone": meta_stone,
            "meta_weathering": meta_weathering,
            "meta_text": meta_text,
            "threshold_used": tool["threshold_deg"],
        },
        "summary": summarize_slices(slices),
        "slices": slices,
        "tool_heuristic": tool,
        "provenance": provenance(entry.info, params, feature_type),
        "plot_data": {
            "x": main["x_2d"].tolist(),
            "z": main["z_2d"].tolist(),
            "fit_left": {"k": float(res["fit_left"][0]), "m": float(res["fit_left"][1])},
            "fit_right": {"k": float(res["fit_right"][0]), "m": float(res["fit_right"][1])},
        },
    }


@router.post("/upload")
def upload(file: UploadFile = File(...)):
    """Laddar upp en skanning en gång. Svaret innehåller mesh_id som används i alla andra anrop."""
    entry = _load_upload(file)
    return entry.info


@router.post("/analyze")
def analyze_3d(
    file: UploadFile = File(None),
    mesh_id: str = Form(None),
    use_mock: bool = Form(False),
    origin_x: float = Form(...),
    origin_y: float = Form(...),
    origin_z: float = Form(...),
    dir_x: float = Form(...),
    dir_y: float = Form(...),
    dir_z: float = Form(...),
    up_x: float = Form(0.0),
    up_y: float = Form(0.0),
    up_z: float = Form(1.0),
    slice_count: int = Form(1),
    slice_spacing_mm: float = Form(1.0),
    window_mm: float = Form(DEFAULT_WINDOW_MM),
    meta_stone: str = Form("Granit"),
    meta_weathering: str = Form("Låg"),
    meta_text: str = Form(""),
    feature_type: str = Form("rune"),
):
    _check_feature_type(feature_type)
    if not 1 <= slice_count <= 200:
        raise HTTPException(status_code=400, detail="Antal snitt måste vara mellan 1 och 200.")
    entry = resolve_mesh(file, mesh_id, use_mock)
    origin, direction, up = [origin_x, origin_y, origin_z], [dir_x, dir_y, dir_z], [up_x, up_y, up_z]
    # Fixed seed: the explicit mock analysis gives the same result every time
    rng = np.random.default_rng(0) if entry.info.get("mock") else None
    slices, main = measure_slices(entry, origin, direction, up, slice_count, slice_spacing_mm, window_mm, rng)
    if not slices:
        raise HTTPException(status_code=400, detail="Kunde inte extrahera något giltigt snitt vid den markerade punkten.")
    params = {"mode": "slices", "origin": origin, "direction": direction, "up": up, "slice_count": slice_count,
              "slice_spacing_mm": slice_spacing_mm, "window_mm": window_mm,
              "meta_stone": meta_stone, "meta_weathering": meta_weathering}
    return _result(slices, main, entry, params, feature_type, meta_stone, meta_weathering, meta_text)


@router.post("/auto_slice")
def auto_slice_endpoint(
    file: UploadFile = File(None),
    mesh_id: str = Form(None),
    point_x: float = Form(...),
    point_y: float = Form(...),
    point_z: float = Form(...),
    normal_x: float = Form(None),
    normal_y: float = Form(None),
    normal_z: float = Form(None),
    measure: str | None = Form(None),
    slice_count: int = Form(3),
    meta_stone: str = Form("Granit"),
    meta_weathering: str = Form("Låg"),
    feature_type: str = Form("rune"),
):
    """Ett klick per snitt: räknar ut snittets läge och riktning vid klicket och mäter direkt."""
    _check_feature_type(feature_type)
    measure = form_flag(measure, True, "measure")
    entry = resolve_mesh(file, mesh_id)
    hint = None if normal_x is None else [normal_x, normal_y, normal_z]
    try:
        sel = auto_slice(entry.mesh, [point_x, point_y, point_z], normal_hint=hint, tree=entry.vertex_tree)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    if not measure:
        return {"selection": sel}
    slices, main = measure_slices(entry, sel["origin"], sel["direction"], sel["up"], slice_count, 1.0, sel["window_mm"])
    if not slices:
        raise HTTPException(status_code=422, detail="Spåret hittades men kunde inte mätas här. Prova en annan punkt.")
    params = {"mode": "one-click", "click": [point_x, point_y, point_z], **sel, "slice_count": slice_count,
              "meta_stone": meta_stone, "meta_weathering": meta_weathering}
    return {"selection": sel, **_result(slices, main, entry, params, feature_type, meta_stone, meta_weathering)}


@router.post("/auto_analyze")
def auto_analyze(
    file: UploadFile = File(None),
    mesh_id: str = Form(None),
    normal_x: float = Form(...),
    normal_y: float = Form(...),
    normal_z: float = Form(...),
    spacing_mm: float = Form(3.0),
    sensitivity: float = Form(3.0),
    max_halfwidth_mm: float = Form(8.0),
    up_x: float = Form(None),
    up_y: float = Form(None),
    up_z: float = Form(None),
    meta_stone: str = Form("Granit"),
    meta_weathering: str = Form("Låg"),
    resolution_mm: float = Form(None),
    harmonize_mm: float = Form(None),
    runes_only: str | None = Form(None),
    protocol: bool = Form(False),
):
    """Automatisk spåranalys av den ristade ytan som vetter mot normalen (oftast kamerans riktning).
    Med runes_only (standard) mäts bara spår som känns igen som runor. Med protocol används Vitki-protokollets
    fasta parametrar (src/protocol.py); proveniensen anger alltid om analysen följer protokollet."""
    runes_only = form_flag(runes_only, True, "runes_only")
    if protocol:
        pp = protocol_spec.PARAMETERS
        resolution_mm, sensitivity, spacing_mm = pp["resolution_mm"], pp["sensitivity"], pp["spacing_mm"]
        max_halfwidth_mm, harmonize_mm, runes_only = pp["max_halfwidth_mm"], pp["harmonize_mm"], pp["runes_only"]
    if not 0.5 <= spacing_mm <= 50 or not 1 <= sensitivity <= 10:
        raise HTTPException(status_code=400, detail="Ogiltiga parametrar för automatisk analys.")
    # Fixed grid resolution and harmonised profiles make stones from scans of different density comparable
    if (resolution_mm is not None and not 0.1 <= resolution_mm <= 3) or (harmonize_mm is not None and not 0 <= harmonize_mm <= 5):
        raise HTTPException(status_code=400, detail="Upplösning 0,1–3 mm och harmonisering 0–5 mm.")
    entry = resolve_mesh(file, mesh_id)
    if entry.info.get("mock"):
        raise HTTPException(status_code=400, detail=NO_MESH)
    try:
        result = analyze_grooves(entry.mesh, [normal_x, normal_y, normal_z], spacing_mm=spacing_mm,
                                 sensitivity=sensitivity, max_halfwidth_mm=max_halfwidth_mm,
                                 face_tree=entry.face_tree,
                                 up=None if up_x is None else [up_x, up_y, up_z],
                                 resolution_mm=resolution_mm, harmonize_mm=harmonize_mm or None,
                                 runes_only=runes_only)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        raise server_error(e, "Den automatiska analysen misslyckades.", status_code=500) from e

    accepted = [s for s in result["slices"] if s["accepted"]]
    if accepted:
        result["summary"] = summarize_slices(accepted)
        if runes_only:
            result["rune_summary"] = summarize_by_rune(accepted)
        result["tool_heuristic"] = tool_heuristic(float(np.mean([s["apex_vinkel_deg"] for s in accepted])),
                                                  meta_stone, meta_weathering)
    params = {"mode": "automatic", **result["parameters"], "meta_stone": meta_stone, "meta_weathering": meta_weathering}
    result["provenance"] = provenance(entry.info, params, "rune" if runes_only else "unknown")
    result["provenance"]["protocol"] = protocol_spec.compliance(result["parameters"], METHOD_VERSION)
    return result


@router.post("/auto_snap_path")
def auto_snap_path(
    file: UploadFile = File(None),
    mesh_id: str = Form(None),
    path_points_json: str = Form(...),
    up_x: float = Form(0.0),
    up_y: float = Form(0.0),
    up_z: float = Form(1.0),
):
    entry = resolve_mesh(file, mesh_id)
    path_points = _parse_points(path_points_json)
    return {"snapped_path": snap_path_to_bottom(entry.mesh, path_points, [up_x, up_y, up_z],
                                                vertex_tree=entry.vertex_tree)}


def _parse_points(raw: str) -> list:
    try:
        pts = json.loads(raw)
        if not isinstance(pts, list) or not all(isinstance(p, list) and len(p) == 3 for p in pts):
            raise ValueError
        return pts
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="path_points_json måste vara en lista av [x, y, z].") from None


@router.post("/analyze_path")
def analyze_path_endpoint(
    file: UploadFile = File(None),
    mesh_id: str = Form(None),
    use_mock: bool = Form(False),
    path_points_json: str = Form(...),
    up_x: float = Form(0.0),
    up_y: float = Form(0.0),
    up_z: float = Form(1.0),
    window_mm: float = Form(DEFAULT_WINDOW_MM),
    meta_stone: str = Form("Granit"),
    meta_weathering: str = Form("Låg"),
    feature_type: str = Form("rune"),
):
    _check_feature_type(feature_type)
    entry = resolve_mesh(file, mesh_id, use_mock)
    path_points = _parse_points(path_points_json)
    up_vector = [up_x, up_y, up_z]
    face_tree = None if entry.info.get("mock") else entry.face_tree
    try:
        _, plot_data, depth_profile, slices = slice_analyze_path(entry.mesh, path_points, up_vector,
                                                                  window_mm=window_mm, face_tree=face_tree)
    except Exception as e:
        raise server_error(e, "Kunde inte mäta längs banan. Kontrollera att punkterna ligger i ett spår.",
                           status_code=400) from e

    means = _means(slices)
    tool = tool_heuristic(means["apex_vinkel_deg"], meta_stone, meta_weathering)
    params = {"mode": "path", "path_points": path_points, "up": up_vector, "window_mm": window_mm,
              "meta_stone": meta_stone, "meta_weathering": meta_weathering}
    return {
        "results": {**means, "troligt_verktyg": tool["label"], "successful_slices": len(slices),
                    "threshold_used": tool["threshold_deg"]},
        "summary": summarize_slices(slices),
        "slices": slices,
        "tool_heuristic": tool,
        "provenance": provenance(entry.info, params, feature_type),
        "plot_data": plot_data,
        "depth_profile": depth_profile,
    }


@router.post("/view_model")
def view_model(file: UploadFile = File(None), mesh_id: str = Form(None), max_faces: int = Form(MAX_VIEW_FACES)):
    """Skapar en lättare visningsmodell (binär STL) av en stor skanning.

    Modellen är centrerad med originalets mittpunkt, så att koordinater som väljs i den
    stämmer med analysen av originalfilen. Själva mätningarna görs alltid på originalet."""
    entry = resolve_mesh(file, mesh_id)
    faces = entry.info["faces"]
    target = max(10_000, min(int(max_faces), faces))
    # Decimated and exported once per mesh and size: the page asks again for the same model when it is reopened
    with entry.view_lock:
        if entry.view is None or entry.view[0] != target:
            mesh = entry.mesh
            if faces > target:
                try:
                    mesh = mesh.simplify_quadric_decimation(face_count=target)
                except Exception as e:
                    raise server_error(e, "Kunde inte förenkla modellen.", status_code=500) from e
            entry.view = (target, mesh.export(file_type="stl"), len(mesh.faces))
        _, data, view_faces = entry.view
    return Response(
        content=data,
        media_type="model/stl",
        headers={
            "X-Original-Faces": str(faces),
            "X-View-Faces": str(view_faces),
            "X-Pre-Centered": "1",
            "X-Mesh-Id": str(entry.info.get("mesh_id", "")),
            "Access-Control-Expose-Headers": "X-Original-Faces, X-View-Faces, X-Pre-Centered, X-Mesh-Id",
        },
    )


@router.post("/render_depth_map")
def render_depth_map(
    file: UploadFile = File(None),
    mesh_id: str = Form(None),
    resolution: int = Form(800),
):
    """Renderar en ortografisk djupkarta ovanifrån som base64-kodad PNG.

    LEGACY: inte spårdjup. Bilden är modellens globala Z-koordinat, sträckt min–max över hela föremålet, så den visar
    stenens form och lutning, inte hur djupt spåren ligger under stenytan. Den länkas inte från exporten; använd
    djupet under stenytan (stone_report.depth_figure / export depth_heatmap, depth_grid). Kan tas bort senare."""
    from PIL import Image

    resolution = max(64, min(int(resolution), 4000))
    entry = resolve_mesh(file, mesh_id)
    try:
        vertices = entry.mesh.vertices
        min_x, min_y, min_z = np.min(vertices, axis=0)
        max_x, max_y, _ = np.max(vertices, axis=0)
        width_range = max_x - min_x
        height_range = max_y - min_y
        if width_range > height_range:
            res_x, res_y = resolution, int(resolution * (height_range / width_range))
        else:
            res_y, res_x = resolution, int(resolution * (width_range / height_range))

        depth_buffer = np.full((res_y, res_x), min_z - 1.0)
        x_idx = ((vertices[:, 0] - min_x) / width_range * (res_x - 1)).astype(int)
        y_idx = ((max_y - vertices[:, 1]) / height_range * (res_y - 1)).astype(int)
        np.maximum.at(depth_buffer, (y_idx, x_idx), vertices[:, 2])

        mask = depth_buffer > (min_z - 0.5)
        if not np.any(mask):
            raise ValueError("Kunde inte projicera 3D-modellen korrekt (tom mask).")
        d_min, d_max = np.min(depth_buffer[mask]), np.max(depth_buffer[mask])
        norm = np.zeros_like(depth_buffer)
        norm[mask] = (depth_buffer[mask] - d_min) / (d_max - d_min)

        buffered = io.BytesIO()
        Image.fromarray((norm * 255).astype(np.uint8)).save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return {"image_base64": f"data:image/png;base64,{img_str}"}
    except Exception as e:
        raise server_error(e, "Djupkartan kunde inte skapas.", status_code=400) from e


def _estimated_normal(mesh) -> np.ndarray:
    """Den ristade sidans normal när ingen vy är angiven: minsta variansriktningen (stenens tjocklek),
    vänd mot den sida där mest yta pekar."""
    pts = mesh.vertices - mesh.vertices.mean(axis=0)
    _, vecs = np.linalg.eigh(pts.T @ pts)
    n = vecs[:, 0]
    if float((mesh.face_normals @ n * mesh.area_faces).sum()) < 0:
        n = -n
    return n


@router.post("/render_relief")
def render_relief(
    file: UploadFile = File(None),
    mesh_id: str = Form(None),
    normal_x: float = Form(None),
    normal_y: float = Form(None),
    normal_z: float = Form(None),
    up_x: float = Form(None),
    up_y: float = Form(None),
    up_z: float = Form(None),
):
    """Bilder av den ristade ytan för läsning: strykljus från fyra håll, ett kombinerat relief och djup
    under stenytan. Utan normal används stenens tunnaste riktning."""
    from PIL import Image
    from src.stone_report import Surface

    entry = resolve_mesh(file, mesh_id)
    if entry.info.get("mock"):
        raise HTTPException(status_code=400, detail=NO_MESH)
    normal = [normal_x, normal_y, normal_z] if normal_x is not None else _estimated_normal(entry.mesh)
    up = [up_x, up_y, up_z] if up_x is not None else None
    try:
        surf = Surface(entry.mesh, normal, up, max_px=1600)
    except Exception as e:
        raise server_error(e, "Ytan kunde inte räknas fram ur modellen.", status_code=500) from e

    def png(gray: np.ndarray) -> str:
        pil = gray_image(gray)
        # Small scans give small images; enlarge so that the runes can be read
        scale = 1200 / max(pil.size)
        if scale > 1:
            pil = pil.resize((round(pil.width * scale), round(pil.height * scale)), Image.LANCZOS)
        buf = io.BytesIO()
        pil.save(buf, format="PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    imgs = relief_images(surf)
    return {
        "relief": png(imgs["relief"]),
        "depth": png(imgs["depth_img"]),
        "raking": {name: png(v) for name, v in imgs["raking"].items()},
        "resolution_mm": surf.res,
        "normal": [float(v) for v in surf.hf.n],
        # the depth that is black in "depth" (99th percentile outside the 10 mm edge zone); the export's heat map
        # uses the 99.5th
        "depth_ref_mm": imgs["depth_ref_mm"],
    }


# ---- export ----------------------------------------------------------------------------------------------------------
# What the groove analysis can be exported as (src/groove_export.py, METHODS.md 2f): images computed from the scan,
# the analysis' own images and the measurements as tables, with the scan's credit and provenance in every file.

MAX_EXPORT_JSON = 60 * 1024 * 1024  # result_json from the browser (an automatic analysis with its images)
# The whole request: result_json and labels_json at most MAX_EXPORT_JSON each, plus the short fields. Refused from
# Content-Length before anything is read. The page never sends the model with an export (it sends mesh_id after
# /api/3d/upload), so a model sent in the same request must fit in the margin
EXPORT_BODY_MARGIN = 5 * 1024 * 1024
MAX_EXPORT_FIELDS = 20  # the page sends 15 at most (FIELD_LIMITS, result_json, labels_json)
MAX_EXPORT_FILES = 3
MAX_SCAN_NOTE = 500
# The short form fields: longer values are refused (400) instead of being cut
FIELD_LIMITS = {"items": 2000, "signum": 400, "feature_type": 20, "mode": 20, "mesh_id": 128, "scan_note": 2000,
                "as_zip": 10, "normal_x": 64, "normal_y": 64, "normal_z": 64, "up_x": 64, "up_y": 64, "up_z": 64}
_MESH_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
# One export at a time: an image export builds the stone surface (up to 3 million cells) and matplotlib figures,
# and two at once would double the memory. The slot is taken before the body is read, so a second request gets 429
# instead of waiting, and its body is never buffered.
_EXPORT_SLOT = threading.BoundedSemaphore(1)
TOO_BIG = "Analysen är för stor för att exporteras (max 60 MB)."


@router.get("/export_items")
def export_items():
    """Exportvalen med filnamn, förklaring och vad de kräver; samma texter som README.txt i paketet."""
    return groove_export.catalogue()


@router.get("/scan_credit")
def scan_credit(mesh_id: str = "", filename: str = "", sha256: str = "", md5: str = "", size: int | None = None):
    """Krediteringen som exporterade filer får för skanningen: bara när filen känns igen som en publicerad fil i en
    öppen serie (src/scan_sources.identify; den inlästa modellen med mesh_id, annars filnamn, kontrollsummor och
    storlek ur analysens proveniens). Ett signum räcker inte; okänd fil ger known: false."""
    if len(mesh_id) > 128 or len(filename) > 1000 or len(sha256) > 64 or len(md5) > 32:
        raise HTTPException(status_code=400, detail="För långa uppgifter om skanningsfilen.")
    entry = mesh_cache.peek(mesh_id) if mesh_id and _MESH_ID.match(mesh_id) else None
    if entry is not None and not entry.info.get("mock"):
        return groove_export.credit_for_mesh(entry.info)
    return groove_export.scan_credit(filename or None, sha256 or None, md5 or None, size)


def _bad(detail: str) -> HTTPException:
    return HTTPException(status_code=400, detail=detail)


def _form_vector(form: dict, keys: tuple[str, str, str], what: str) -> list[float] | None:
    """[x, y, z] ur tre formulärfält: None när alla saknas, 400 när de är ofullständiga eller inte tal."""
    raw = [form.get(k) for k in keys]
    if all(v in (None, "") for v in raw):
        return None
    v = groove_export.unit_vector(raw) if all(v not in (None, "") for v in raw) else None
    if v is None:
        raise _bad(f"{what} måste anges som tre tal ({', '.join(keys)}) och får inte vara nollvektorn.")
    return v


async def _form_text(form, key: str, limit: int) -> str | None:
    raw = form.get(key)
    if raw is None:
        return None
    if hasattr(raw, "read"):  # sent as a Blob
        data = await raw.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(status_code=413, detail=TOO_BIG)
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            raise _bad(f"{key} måste vara UTF-8.") from None
    if len(raw) > limit:
        raise HTTPException(status_code=413, detail=TOO_BIG)
    return raw


def export_response(out: dict) -> Response:
    """The file with its name and what was left out. Header values must be ASCII, so X-Export-Skipped
    ("id:skäl;id:skäl") is percent-encoded UTF-8: the page reads it with decodeURIComponent."""
    from urllib.parse import quote
    name = out["name"]
    skipped = quote(";".join(f"{i}:{r}" for i, r in out["skipped"]), safe=" :;,()-_.")
    return Response(content=out["data"], media_type=out["media"], headers={
        "Content-Disposition": f"attachment; filename=\"{name}\"; filename*=UTF-8''{quote(name)}",
        "X-Export-Files": ",".join(out["files"]),
        "X-Export-Skipped": skipped,
        "Access-Control-Expose-Headers": "Content-Disposition, X-Export-Files, X-Export-Skipped",
    })


def _export_locked(form: dict, upload) -> Response:
    try:
        items = groove_export.parse_items(form.get("items") or "")
        signum = groove_export.clean_signum(form.get("signum") or "")
    except ValueError as e:
        raise _bad(str(e)) from e
    try:
        result = json.loads(form["result_json"]) if form.get("result_json") else None
        labels = json.loads(form["labels_json"]) if form.get("labels_json") else None
    except (ValueError, TypeError, RecursionError):
        raise _bad("result_json och labels_json måste vara giltig JSON.") from None
    if result is not None and not isinstance(result, dict):
        raise _bad("result_json måste vara ett objekt.")
    if labels is not None and not isinstance(labels, list):
        raise _bad("labels_json måste vara en lista.")
    scan_note = (form.get("scan_note") or "").strip()
    if len(scan_note) > MAX_SCAN_NOTE:
        raise _bad(f"Texten om skanningen får vara högst {MAX_SCAN_NOTE} tecken.")
    feature_type = form.get("feature_type") or "rune"
    _check_feature_type(feature_type)
    mode = form.get("mode") or None
    if mode not in (None, "oneclick", "manual", "path", "auto"):
        raise _bad("mode måste vara oneclick, manual, path eller auto.")
    try:
        as_zip = form_flag(form.get("as_zip"), False, "as_zip")
    except HTTPException as e:
        raise _bad(e.detail) from None
    view_n = _form_vector(form, ("normal_x", "normal_y", "normal_z"), "Vyns riktning")
    view_up = _form_vector(form, ("up_x", "up_y", "up_z"), "Vyns uppåtriktning")
    mesh_id = form.get("mesh_id") or None
    if mesh_id is not None and not _MESH_ID.match(mesh_id):
        raise _bad("Ogiltigt mesh_id.")
    try:
        groove_export.validate_result(result)
    except ValueError as e:
        raise _bad(str(e)) from e

    needs_mesh = any(i in groove_export.IMAGE_ITEMS for i in items)
    entry = None
    if needs_mesh:
        if not mesh_id and upload is None:
            raise _bad(NO_MESH)
        entry = resolve_mesh(upload, mesh_id)  # 404 when the model has left the cache: the client uploads again
        if entry.info.get("mock"):
            raise _bad(NO_MESH)
    elif mesh_id:
        entry = mesh_cache.peek(mesh_id)  # only for the file name and fingerprint; data items need no model
    prov_mesh = ((result or {}).get("provenance") or {}).get("mesh") or {}
    if (entry is not None and prov_mesh.get("sha256") and entry.info.get("sha256")
            and prov_mesh["sha256"] != entry.info["sha256"]):
        if needs_mesh:
            raise _bad("Analysen hör till en annan skanning än den inlästa 3D-modellen. Läs in samma fil eller mät om.")
        # Tables and data need no model: the scan file and its credit are the analysis' own (its provenance)
        entry = None

    # The carved face's normal as the stone report chooses it (groove_export.view_normal, shared with
    # api/routers/reports.py): the analysis' own normal, else the slices' mean up direction; with no analysis the
    # 3D view, else the stone's thinnest direction
    normal, up, source = groove_export.view_normal(None, [result] if result else [])
    if normal is None and view_n:
        normal, up, source = view_n, view_up, "vy"
    elif normal is None:
        source = "uppskattad"

    def surface():
        from src.stone_report import Surface
        n = normal if normal is not None else _estimated_normal(entry.mesh)
        return Surface(entry.mesh, n, up)  # max_px 1800, as the stone report (api/routers/reports.py)

    mesh_info = entry.info if entry is not None else prov_mesh
    credit = {**groove_export.credit_for_mesh(mesh_info), "scan_note": scan_note}
    try:
        out = groove_export.export(items, as_zip=as_zip, mesh_entry=entry,
                                   surface_factory=surface if entry is not None and needs_mesh else None,
                                   result=result, labels=labels, signum=signum, credit=credit,
                                   view={"normal_source": source}, mode=mode, feature_type=feature_type,
                                   tool_fn=tool_heuristic)
    except groove_export.BadInput as e:
        raise _bad(str(e)) from e
    except LookupError as e:
        raise HTTPException(status_code=422, detail="Inget av de valda kan exporteras för den här analysen.") from e
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(e, "Exporten kunde inte skapas.", status_code=500) from e
    return export_response(out)


@router.post("/export")
async def export(request: Request):
    """Valda filer ur huggspårsanalysen (src/groove_export.py): en fil som den är, flera som ZIP med README.txt och
    kalla.json. Formuläret läses här och inte med Form-parametrar, eftersom result_json från en automatisk analys
    med sina bilder är större än Starlettes gräns på 1 MB per fält. Bara multipart/form-data (som webbläsarens
    FormData), med Content-Length högst 2 × MAX_EXPORT_JSON + EXPORT_BODY_MARGIN och högst MAX_EXPORT_FIELDS fält;
    exportplatsen tas innan något läses, så att en andra export får 429 utan att dess innehåll buffras."""
    ctype = (request.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
    if ctype != "multipart/form-data":
        raise HTTPException(status_code=415, detail="Exporten skickas som multipart/form-data.")
    length = request.headers.get("content-length")
    if length is None:
        raise HTTPException(status_code=411, detail="Content-Length saknas.")
    try:
        n = int(length)
    except ValueError:
        raise _bad("Ogiltig Content-Length.") from None
    if n < 0:
        raise _bad("Ogiltig Content-Length.")
    if n > 2 * MAX_EXPORT_JSON + EXPORT_BODY_MARGIN:
        raise HTTPException(status_code=413, detail=TOO_BIG)
    slot = _EXPORT_SLOT  # the module's semaphore at the time of the request (tests replace it)
    if not slot.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="En export pågår redan. Vänta tills den är klar och försök igen.")
    try:
        return await _export_request(request)
    finally:
        slot.release()


async def _export_request(request: Request) -> Response:
    try:
        form = await request.form(max_files=MAX_EXPORT_FILES, max_fields=MAX_EXPORT_FIELDS,
                                  max_part_size=MAX_EXPORT_JSON)
    except StarletteHTTPException as e:
        if "maximum size" in str(e.detail).lower():
            raise HTTPException(status_code=413, detail=TOO_BIG) from e
        raise _bad("Formuläret kunde inte läsas.") from e
    except Exception as e:  # a malformed multipart body
        raise _bad("Formuläret kunde inte läsas.") from e
    try:
        fields = {}
        for key, limit in FIELD_LIMITS.items():
            v = form.get(key)
            if v is None or hasattr(v, "read"):
                fields[key] = None
                continue
            v = str(v)
            if len(v) > limit:
                raise _bad(f"Fältet {key} är för långt (högst {limit} tecken).")
            fields[key] = v
        for key in ("result_json", "labels_json"):
            fields[key] = await _form_text(form, key, MAX_EXPORT_JSON)
        upload = form.get("file")
        upload = upload if hasattr(upload, "read") and getattr(upload, "filename", None) else None
        return await run_in_threadpool(_export_locked, fields, upload)
    finally:
        await form.close()
