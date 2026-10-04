import base64
import datetime
import hashlib
import io
import json
import os

import numpy as np
import trimesh
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

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
from src.stats import METRICS, summarize_slices

router = APIRouter()

FEATURE_TYPES = ("rune", "ornament", "unknown")
MAX_VIEW_FACES = int(os.environ.get("MAX_VIEW_FACES", "1500000"))
NO_MESH = ("Ingen 3D-modell angiven. Ladda upp en STL-, OBJ- eller PLY-fil först "
           "(appen använder aldrig testdata i stället).")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_upload(file: UploadFile) -> MeshEntry:
    """Läser in en uppladdad fil, centrerar den som Three.js geo.center() och lägger den i cachen."""
    tmp_path = save_mesh_upload(file)
    try:
        digest = _sha256(tmp_path)
        cached = mesh_cache.peek(digest)
        if cached is not None:
            return cached
        mesh = trimesh.load(tmp_path, force="mesh")
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(e, "Kunde inte ladda 3D-filen. Kontrollera att filen är en giltig STL/OBJ/PLY.",
                           status_code=400)
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
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "extent_mm": [float(v) for v in mesh.extents],
        "centered_by": [float(v) for v in centre],
    }
    return mesh_cache.put(digest, MeshEntry(mesh, info))


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
    }


def _slice_record(res: dict, position_mm: float, x=None, z=None) -> dict:
    rec = {**{k: float(res[k]) for k in METRICS}, "position_mm": float(position_mm), "fit_r2": float(res["fit_r2"])}
    if x is not None:
        rec["profile"] = raw_profile(x, z)
    return rec


def _means(slices: list[dict]) -> dict:
    return {k: float(np.mean([s[k] for s in slices])) for k in METRICS}


def _check_feature_type(feature_type: str):
    if feature_type not in FEATURE_TYPES:
        raise HTTPException(status_code=400, detail="feature_type måste vara rune, ornament eller unknown.")


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
    slices, main = [], None
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
        except Exception:
            continue
        if not all(np.isfinite(res[k]) for k in (*METRICS, "fit_r2")):
            continue  # too few points for a wall fit
        slices.append(_slice_record(res, offset, x_2d, z_2d))
        if i == slice_count // 2 or main is None:
            main = {"x_2d": x_2d, "z_2d": z_2d, "res": res}
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
    measure: bool = Form(True),
    slice_count: int = Form(3),
    meta_stone: str = Form("Granit"),
    meta_weathering: str = Form("Låg"),
    feature_type: str = Form("rune"),
):
    """Ett klick per snitt: räknar ut snittets läge och riktning vid klicket och mäter direkt."""
    _check_feature_type(feature_type)
    entry = resolve_mesh(file, mesh_id)
    hint = None if normal_x is None else [normal_x, normal_y, normal_z]
    try:
        sel = auto_slice(entry.mesh, [point_x, point_y, point_z], normal_hint=hint, tree=entry.vertex_tree)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
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
):
    """Automatisk spåranalys av den ristade ytan som vetter mot normalen (oftast kamerans riktning)."""
    if not 0.5 <= spacing_mm <= 50 or not 1 <= sensitivity <= 10:
        raise HTTPException(status_code=400, detail="Ogiltiga parametrar för automatisk analys.")
    entry = resolve_mesh(file, mesh_id)
    if entry.info.get("mock"):
        raise HTTPException(status_code=400, detail=NO_MESH)
    try:
        result = analyze_grooves(entry.mesh, [normal_x, normal_y, normal_z], spacing_mm=spacing_mm,
                                 sensitivity=sensitivity, max_halfwidth_mm=max_halfwidth_mm,
                                 face_tree=entry.face_tree,
                                 up=None if up_x is None else [up_x, up_y, up_z])
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise server_error(e, "Den automatiska analysen misslyckades.", status_code=500)

    accepted = [s for s in result["slices"] if s["accepted"]]
    if accepted:
        result["summary"] = summarize_slices(accepted)
        result["tool_heuristic"] = tool_heuristic(float(np.mean([s["apex_vinkel_deg"] for s in accepted])),
                                                  meta_stone, meta_weathering)
    params = {"mode": "automatic", **result["parameters"], "meta_stone": meta_stone, "meta_weathering": meta_weathering}
    result["provenance"] = provenance(entry.info, params, "unknown")
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
        raise HTTPException(status_code=400, detail="path_points_json måste vara en lista av [x, y, z].")


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
                           status_code=400)

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
    mesh = entry.mesh
    faces = entry.info["faces"]
    target = max(10_000, min(int(max_faces), faces))
    if faces > target:
        try:
            mesh = mesh.simplify_quadric_decimation(face_count=target)
        except Exception as e:
            raise server_error(e, "Kunde inte förenkla modellen.", status_code=500)
    data = mesh.export(file_type="stl")
    return Response(
        content=data,
        media_type="model/stl",
        headers={
            "X-Original-Faces": str(faces),
            "X-View-Faces": str(len(mesh.faces)),
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
    """Renderar en ortografisk djupkarta ovanifrån som base64-kodad PNG."""
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
        raise server_error(e, "Djupkartan kunde inte skapas.", status_code=400)
