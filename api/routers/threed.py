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

from api.config import APP_NAME, APP_VERSION, METHOD_VERSION
from api.errors import server_error
from api.uploads import save_mesh_upload
from src.slice_analysis import (
    analyze_path as slice_analyze_path,
    calculate_v_angle,
    create_mock_v_groove_mesh,
    extract_2d_profile_from_mesh,
    snap_path_to_bottom,
)
from src.stats import METRICS, summarize_slices

router = APIRouter()

FEATURE_TYPES = ("rune", "ornament", "unknown")
MAX_VIEW_FACES = int(os.environ.get("MAX_VIEW_FACES", "1500000"))


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_mesh(file: UploadFile | None, use_mock: bool):
    """Läser in mesh och centrerar den på samma sätt som Three.js geo.center() i webbläsaren,
    så att klickkoordinater från gränssnittet motsvarar backendens koordinater.
    Returnerar (mesh, mesh_info) där mesh_info ingår i analysens proveniens."""
    if use_mock or file is None:
        mesh = create_mock_v_groove_mesh()
        return mesh, {"mock": True, "faces": int(len(mesh.faces))}

    tmp_path = save_mesh_upload(file)
    try:
        digest = _sha256(tmp_path)
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
    return mesh, {
        "mock": False,
        "filename": file.filename,
        "sha256": digest,
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "extent_mm": [float(v) for v in mesh.extents],
        "centered_by": [float(v) for v in centre],
    }


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


def _slice_record(res: dict, position_mm: float) -> dict:
    return {**{k: float(res[k]) for k in METRICS}, "position_mm": float(position_mm)}


def _means(slices: list[dict]) -> dict:
    return {k: float(np.mean([s[k] for s in slices])) for k in METRICS}


@router.post("/analyze")
async def analyze_3d(
    file: UploadFile = File(None),
    use_mock: bool = Form(False),
    origin_x: float = Form(0.0),
    origin_y: float = Form(0.0),
    origin_z: float = Form(0.0),
    dir_x: float = Form(0.0),
    dir_y: float = Form(1.0),
    dir_z: float = Form(0.0),
    up_x: float = Form(0.0),
    up_y: float = Form(0.0),
    up_z: float = Form(1.0),
    slice_count: int = Form(1),
    slice_spacing_mm: float = Form(1.0),
    meta_stone: str = Form("Granit"),
    meta_weathering: str = Form("Låg"),
    meta_text: str = Form(""),
    feature_type: str = Form("rune"),
):
    if feature_type not in FEATURE_TYPES:
        raise HTTPException(status_code=400, detail="feature_type måste vara rune, ornament eller unknown.")
    if not 1 <= slice_count <= 200:
        raise HTTPException(status_code=400, detail="Antal snitt måste vara mellan 1 och 200.")
    mesh, mesh_info = load_mesh(file, use_mock)

    plane_origin = np.array([origin_x, origin_y, origin_z])
    groove_direction = np.array([dir_x, dir_y, dir_z], dtype=float)
    up_vector = np.array([up_x, up_y, up_z])
    gd_norm = np.linalg.norm(groove_direction)
    if gd_norm > 0:
        groove_direction = groove_direction / gd_norm

    # Fast slumpfrö: mockanalysen ska ge samma resultat varje gång
    rng = np.random.default_rng(0)
    slices = []
    main = None
    start_offset = -(slice_count - 1) / 2.0 * slice_spacing_mm
    for i in range(slice_count):
        offset = start_offset + i * slice_spacing_mm
        try:
            x_2d, z_2d = extract_2d_profile_from_mesh(mesh, plane_origin + groove_direction * offset,
                                                      groove_direction, up_vector)
            if use_mock:
                z_2d = z_2d + rng.normal(0, 0.1, size=z_2d.shape)
            res = calculate_v_angle(x_2d, z_2d)
        except Exception:
            continue
        slices.append(_slice_record(res, offset))
        if i == slice_count // 2 or main is None:
            main = {"x_2d": x_2d, "z_2d": z_2d, "res": res}

    if not slices:
        raise HTTPException(status_code=400, detail="Kunde inte extrahera något giltigt snitt.")

    means = _means(slices)
    tool = tool_heuristic(means["apex_vinkel_deg"], meta_stone, meta_weathering)
    res = main["res"]
    params = {
        "mode": "slices",
        "origin": plane_origin.tolist(),
        "direction": groove_direction.tolist(),
        "up": up_vector.tolist(),
        "slice_count": slice_count,
        "slice_spacing_mm": slice_spacing_mm,
        "meta_stone": meta_stone,
        "meta_weathering": meta_weathering,
    }
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
        "provenance": provenance(mesh_info, params, feature_type),
        "plot_data": {
            "x": main["x_2d"].tolist(),
            "z": main["z_2d"].tolist(),
            "fit_left": {"k": float(res["fit_left"][0]), "m": float(res["fit_left"][1])},
            "fit_right": {"k": float(res["fit_right"][0]), "m": float(res["fit_right"][1])},
        },
    }


@router.post("/auto_snap_path")
async def auto_snap_path(
    file: UploadFile = File(None),
    use_mock: bool = Form(False),
    path_points_json: str = Form(...),
    up_x: float = Form(0.0),
    up_y: float = Form(0.0),
    up_z: float = Form(1.0),
):
    mesh, _ = load_mesh(file, use_mock)
    path_points = _parse_points(path_points_json)
    return {"snapped_path": snap_path_to_bottom(mesh, path_points, [up_x, up_y, up_z])}


def _parse_points(raw: str) -> list:
    try:
        pts = json.loads(raw)
        if not isinstance(pts, list) or not all(isinstance(p, list) and len(p) == 3 for p in pts):
            raise ValueError
        return pts
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="path_points_json måste vara en lista av [x, y, z].")


@router.post("/analyze_path")
async def analyze_path_endpoint(
    file: UploadFile = File(None),
    use_mock: bool = Form(False),
    path_points_json: str = Form(...),
    up_x: float = Form(0.0),
    up_y: float = Form(0.0),
    up_z: float = Form(1.0),
    meta_stone: str = Form("Granit"),
    meta_weathering: str = Form("Låg"),
    feature_type: str = Form("rune"),
):
    if feature_type not in FEATURE_TYPES:
        raise HTTPException(status_code=400, detail="feature_type måste vara rune, ornament eller unknown.")
    mesh, mesh_info = load_mesh(file, use_mock)
    path_points = _parse_points(path_points_json)
    up_vector = [up_x, up_y, up_z]

    try:
        avg_results, plot_data, depth_profile, slices = slice_analyze_path(mesh, path_points, up_vector)
    except Exception as e:
        raise server_error(e, "3D-analysen misslyckades.", status_code=400)

    means = _means(slices)
    tool = tool_heuristic(means["apex_vinkel_deg"], meta_stone, meta_weathering)
    params = {"mode": "path", "path_points": path_points, "up": up_vector,
              "meta_stone": meta_stone, "meta_weathering": meta_weathering}
    return {
        "results": {**means, "troligt_verktyg": tool["label"], "successful_slices": len(slices),
                    "threshold_used": tool["threshold_deg"]},
        "summary": summarize_slices(slices),
        "slices": slices,
        "tool_heuristic": tool,
        "provenance": provenance(mesh_info, params, feature_type),
        "plot_data": plot_data,
        "depth_profile": depth_profile,
    }


@router.post("/view_model")
def view_model(file: UploadFile = File(...), max_faces: int = Form(MAX_VIEW_FACES)):
    """Skapar en lättare visningsmodell (binär STL) av en stor skanning.

    Modellen är centrerad med originalets mittpunkt, så att koordinater som väljs i den
    stämmer med analysen av originalfilen. Själva mätningarna görs alltid på originalet."""
    mesh, info = load_mesh(file, use_mock=False)
    target = max(10_000, min(int(max_faces), info["faces"]))
    if info["faces"] > target:
        try:
            mesh = mesh.simplify_quadric_decimation(face_count=target)
        except Exception as e:
            raise server_error(e, "Kunde inte förenkla modellen.", status_code=500)
    data = mesh.export(file_type="stl")
    return Response(
        content=data,
        media_type="model/stl",
        headers={
            "X-Original-Faces": str(info["faces"]),
            "X-View-Faces": str(len(mesh.faces)),
            "X-Pre-Centered": "1",
            "Access-Control-Expose-Headers": "X-Original-Faces, X-View-Faces, X-Pre-Centered",
        },
    )


@router.post("/render_depth_map")
def render_depth_map(
    file: UploadFile = File(...),
    resolution: int = Form(800),
):
    """Renderar en ortografisk djupkarta ovanifrån som base64-kodad PNG."""
    from PIL import Image

    resolution = max(64, min(int(resolution), 4000))
    mesh, _ = load_mesh(file, use_mock=False)
    try:
        vertices = mesh.vertices
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
