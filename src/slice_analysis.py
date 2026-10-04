import numpy as np
from scipy.stats import linregress
import trimesh
import matplotlib.pyplot as plt
import os

DEFAULT_WINDOW_MM = 25.0


def raw_profile(x, z, digits: int = 4) -> dict:
    """Rå tvärsnittsprofil (x, z i mm) för lagring, så att snittet kan räknas om med senare metoder."""
    return {"x": [round(float(v), digits) for v in x], "z": [round(float(v), digits) for v in z]}


def section_points(triangles: np.ndarray, plane_origin, plane_normal) -> np.ndarray:
    """Skärningspunkter mellan ett plan och trianglar (k, 3, 3): ändpunkterna för varje snittsegment."""
    d = (triangles - plane_origin) @ plane_normal  # (k, 3) signed distances
    pts = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        di, dj = d[:, i], d[:, j]
        cross = (di * dj) < 0
        if cross.any():
            t = di[cross] / (di[cross] - dj[cross])
            pi, pj = triangles[cross, i], triangles[cross, j]
            pts.append(pi + t[:, None] * (pj - pi))
    if not pts:
        return np.empty((0, 3))
    # Adjacent triangles share edges, so each point appears twice
    return np.unique(np.round(np.vstack(pts), 6), axis=0)


def extract_2d_profile_from_mesh(mesh, plane_origin, groove_direction, up_vector, window_mm=DEFAULT_WINDOW_MM,
                                 face_tree=None):
    """Tvärsnittsprofil genom spåret.

    Bara punkter inom ±window_mm från mätpunkten (i sidled och höjdled) tas med. Utan fönstret
    skulle snittet genom en sluten skanning även innehålla stenens baksida och kanter.
    Med face_tree (KD-träd över triangelcentra) snittas bara närliggande trianglar, vilket ger
    samma resultat men går mycket snabbare på stora skanningar."""
    N = groove_direction / np.linalg.norm(groove_direction)
    Z_dir = up_vector / np.linalg.norm(up_vector)
    X_dir = np.cross(N, Z_dir)
    X_dir = X_dir / np.linalg.norm(X_dir)
    Z_dir = np.cross(X_dir, N)
    plane_origin = np.asarray(plane_origin, dtype=float)

    if face_tree is not None and window_mm:
        idx = face_tree.query_ball_point(plane_origin, window_mm * 1.5 + 2.0)
        points_3d = section_points(mesh.vertices[mesh.faces[idx]], plane_origin, N) if idx else np.empty((0, 3))
    else:
        slice_path = mesh.section(plane_origin=plane_origin, plane_normal=N)
        points_3d = slice_path.vertices if slice_path is not None else np.empty((0, 3))
    if len(points_3d) < 4:
        raise ValueError("Ogiltigt snitt.")

    relative_points = points_3d - plane_origin
    x_2d = np.dot(relative_points, X_dir)
    z_2d = np.dot(relative_points, Z_dir)

    if window_mm:
        keep = (np.abs(x_2d) <= window_mm) & (np.abs(z_2d) <= window_mm)
        x_2d, z_2d = x_2d[keep], z_2d[keep]
        if len(x_2d) < 4:
            raise ValueError("För få punkter i snittet nära mätpunkten.")

    sort_idx = np.argsort(x_2d)
    return x_2d[sort_idx], z_2d[sort_idx]

WALL_BAND = (0.2, 0.8)


def _wall_band(xw, zw, z_bottom, z_top):
    """Väggpunkter mellan 20 % och 80 % av höjden från botten till spårkanten (minst tre punkter)."""
    span = z_top - z_bottom
    if span <= 0:
        return xw, zw
    lo, hi = z_bottom + WALL_BAND[0] * span, z_bottom + WALL_BAND[1] * span
    keep = (zw >= lo) & (zw <= hi)
    return (xw[keep], zw[keep]) if keep.sum() >= 3 else (xw, zw)


def calculate_v_angle(x, z):
    # Använd lätt utjämning för att hitta en mer stabil apex och axlar
    z_smooth = np.convolve(z, np.ones(5)/5, mode='same')
    apex_idx = np.argmin(z_smooth)
    
    # Beräkna derivatan (lutningen) för att hitta när plan stenyta börjar
    dz = np.gradient(z_smooth, x)
    slope_threshold = 0.15
    
    # Hitta vänster axel
    left_shoulder = 0
    for i in range(apex_idx - 1, -1, -1):
        if abs(dz[i]) < slope_threshold:
            left_shoulder = i
            break
            
    # Hitta höger axel
    right_shoulder = len(x) - 1
    for i in range(apex_idx + 1, len(x)):
        if abs(dz[i]) < slope_threshold:
            right_shoulder = i
            break
            
    # Fallback om axlarna hamnar för nära apex
    if apex_idx - left_shoulder < 5: left_shoulder = max(0, apex_idx - 15)
    if right_shoulder - apex_idx < 5: right_shoulder = min(len(x)-1, apex_idx + 15)
    
    x_left, z_left = x[left_shoulder:apex_idx], z[left_shoulder:apex_idx]
    x_right, z_right = x[apex_idx+1:right_shoulder], z[apex_idx+1:right_shoulder]
    
    # Om arrayerna är tomma pga konstiga snitt, fallback till original
    if len(x_left) < 2 or len(x_right) < 2:
        x_left, z_left = x[:apex_idx], z[:apex_idx]
        x_right, z_right = x[apex_idx+1:], z[apex_idx+1:]
        left_shoulder, right_shoulder = 0, len(x)-1
    
    # Anpassa väggarna bara mellan 20 % och 80 % av spårdjupet: den rundade botten och
    # spårkanten (läppen) planar annars ut väggarna och ger för stor vinkel (metod groove-3).
    z_bottom = z[apex_idx]
    x_left, z_left = _wall_band(x_left, z_left, z_bottom, z[left_shoulder])
    x_right, z_right = _wall_band(x_right, z_right, z_bottom, z[right_shoulder])

    res_left = linregress(x_left, z_left)
    res_right = linregress(x_right, z_right)
    
    k1, k2 = res_left.slope, res_right.slope
    # Väggarnas riktningar ut från apex: vänster vägg mot -x, höger mot +x.
    # (Med båda vektorerna mot +x blir resultatet supplementvinkeln, 180° - V.)
    v1, v2 = np.array([-1, -k1]), np.array([1, k2])
    
    cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    
    depth = abs(np.min(z[left_shoulder:right_shoulder]) - np.max(z[left_shoulder:right_shoulder]))
    # Bredd: där väggarnas linjer når stenytans nivå precis utanför spårkanterna (medel av sidorna)
    rim_left = np.max(z[max(0, left_shoulder - 3):left_shoulder + 1])
    rim_right = np.max(z[right_shoulder:right_shoulder + 4])
    rim = 0.5 * (rim_left + rim_right)
    if k1 < 0 < k2:
        width = abs((rim - res_right.intercept) / k2 - (rim - res_left.intercept) / k1)
    else:
        width = abs(x[right_shoulder] - x[left_shoulder])
    dw_ratio = depth / width if width > 0 else 0
    
    # Calculate R_b (Bottenradie) using parabolic fit near apex
    apex_pts_idx = slice(max(0, apex_idx - 5), min(len(x), apex_idx + 6))
    x_apex, z_apex = x[apex_pts_idx], z[apex_pts_idx]
    if len(x_apex) >= 3:
        p = np.polyfit(x_apex, z_apex, 2)
        a = p[0]
        Rb = abs(1.0 / (2 * a)) if a != 0 else 0
    else:
        Rb = 0
        
    # Calculate Ytråhet (R_a) as mean absolute deviation from linear fits
    z_fit_left = k1 * x_left + res_left.intercept
    Ra_left = np.mean(np.abs(z_left - z_fit_left)) if len(z_left) > 0 else 0
    z_fit_right = k2 * x_right + res_right.intercept
    Ra_right = np.mean(np.abs(z_right - z_fit_right)) if len(z_right) > 0 else 0
    Ra = (Ra_left + Ra_right) / 2.0
    
    return {
        "apex_vinkel_deg": np.degrees(np.arccos(cos_theta)),
        "asymmetri_deg": abs(np.degrees(np.arctan(abs(1/k1))) - np.degrees(np.arctan(abs(1/k2)))),
        "spårdjup_mm": depth,
        "spårbredd_mm": width,
        "djup_bredd_kvot": dw_ratio,
        "bottenradie_mm": Rb,
        "ytråhet_mm": Ra,
        "fit_r2": float(min(res_left.rvalue ** 2, res_right.rvalue ** 2)),
        "fit_left": (res_left.slope, res_left.intercept),
        "fit_right": (res_right.slope, res_right.intercept),
        "apex_idx": apex_idx,
        "left_shoulder": left_shoulder,
        "right_shoulder": right_shoulder
    }

def plot_profile(x, z, analysis_results, output_path):
    plt.figure(figsize=(8, 6))
    plt.plot(x, z, 'k.', label='Uppmätt data')
    
    apex_idx = analysis_results["apex_idx"]
    left_shoulder = analysis_results.get("left_shoulder", 0)
    right_shoulder = analysis_results.get("right_shoulder", len(x)-1)
    
    x_left = x[left_shoulder:apex_idx]
    x_right = x[apex_idx+1:right_shoulder]
    
    k1, m1 = analysis_results["fit_left"]
    k2, m2 = analysis_results["fit_right"]
    
    # Mark shoulders
    plt.plot(x[left_shoulder], z[left_shoulder], 'go', label='Vänster axel (ROI)')
    plt.plot(x[right_shoulder], z[right_shoulder], 'go', label='Höger axel (ROI)')
    
    plt.plot(x_left, k1 * x_left + m1, 'r-', label='Linjär anpassning (vänster)')
    plt.plot(x_right, k2 * x_right + m2, 'b-', label='Linjär anpassning (höger)')
    
    plt.title(f'V-spåranalys\\nVinkel: {analysis_results["apex_vinkel_deg"]:.1f}°, Asymmetri: {analysis_results["asymmetri_deg"]:.1f}°')
    plt.xlabel('X (mm)')
    plt.ylabel('Z (mm)')
    plt.legend()
    plt.grid(True)
    plt.axis('equal')
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()

def create_mock_v_groove_mesh():
    x = np.linspace(-10, 10, 50)
    y = np.linspace(-10, 10, 50)
    X, Y = np.meshgrid(x, y)
    
    # Skapa V-formen med lite asymmetri
    Z = np.where(X < 0, -1.5 * X, 1.2 * X)
    
    vertices = np.column_stack((X.flatten(), Y.flatten(), Z.flatten()))
    
    faces = []
    for i in range(49):
        for j in range(49):
            idx = i * 50 + j
            faces.append([idx, idx + 1, idx + 50])
            faces.append([idx + 1, idx + 51, idx + 50])
            
    return trimesh.Trimesh(vertices=vertices, faces=faces)

def find_auto_slice(mesh, click_point, radius=5.0):
    from scipy.spatial import cKDTree
    
    kdtree = cKDTree(mesh.vertices)
    indices = kdtree.query_ball_point(click_point, radius)
    local_verts = mesh.vertices[indices]
    
    if len(local_verts) < 10:
        return None, None
        
    centered_verts = local_verts - np.mean(local_verts, axis=0)
    cov = np.cov(centered_verts.T)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    
    normal = eigenvectors[:, 0]
    groove_dir = eigenvectors[:, 2]
    
    cross_dir = np.cross(groove_dir, normal)
    cross_dir = cross_dir / np.linalg.norm(cross_dir)
    
    p1 = click_point + cross_dir * (radius * 1.5)
    p2 = click_point - cross_dir * (radius * 1.5)
    
    return p1.tolist(), p2.tolist()

def snap_path_to_bottom(mesh, path_points, up_vector, search_radius=3.0, vertex_tree=None):
    from scipy.spatial import cKDTree
    snapped = []
    up_vector = np.array(up_vector)
    up_vector = up_vector / np.linalg.norm(up_vector)
    
    kdtree = vertex_tree or cKDTree(mesh.vertices)
    for p in path_points:
        indices = kdtree.query_ball_point(p, r=search_radius)
        if len(indices) == 0:
            snapped.append(p)
        else:
            local_verts = mesh.vertices[indices]
            z_vals = np.dot(local_verts, up_vector)
            lowest = local_verts[np.argmin(z_vals)]
            snapped.append(lowest.tolist())
            
    # Simple moving average to smooth the snapped path
    if len(snapped) >= 3:
        arr = np.array(snapped)
        smoothed = np.copy(arr)
        for i in range(1, len(arr)-1):
            smoothed[i] = (arr[i-1] + arr[i] + arr[i+1]) / 3.0
        snapped = smoothed.tolist()
            
    return snapped

def analyze_path(mesh, path_points, up_vector, window_mm=DEFAULT_WINDOW_MM, face_tree=None):
    if len(path_points) < 2:
        raise ValueError("Bananalys kräver minst 2 punkter.")
        
    path_points = np.array(path_points)
    up_vector = np.array(up_vector)
    up_vector = up_vector / np.linalg.norm(up_vector)
    
    # Calculate tangents
    tangents = np.zeros_like(path_points)
    tangents[0] = path_points[1] - path_points[0]
    tangents[-1] = path_points[-1] - path_points[-2]
    if len(path_points) > 2:
        tangents[1:-1] = path_points[2:] - path_points[:-2]
        
    results_list = []
    profiles = []
    plot_data_list = []
    distances = []
    depths = []
    current_distance = 0.0
    
    for i in range(len(path_points)):
        p = path_points[i]
        t = tangents[i]
        t = t / (np.linalg.norm(t) + 1e-9)
        
        # Beräkna avstånd från förra punkten
        if i > 0:
            current_distance += np.linalg.norm(path_points[i] - path_points[i-1])
            
        try:
            x_2d, z_2d = extract_2d_profile_from_mesh(mesh, p, t, up_vector, window_mm=window_mm, face_tree=face_tree)
            res = calculate_v_angle(x_2d, z_2d)
            if np.isfinite(res["apex_vinkel_deg"]) and np.isfinite(res["fit_r2"]) and res["apex_vinkel_deg"] > 0:
                results_list.append(res)
                profiles.append((x_2d, z_2d))
                distances.append(current_distance)
                depths.append(res["spårdjup_mm"])
                # Keep the first valid one for plotting purposes
                if len(plot_data_list) == 0:
                    plot_data_list.append({"x": x_2d.tolist(), "z": z_2d.tolist()})
        except Exception:
            continue
            
    if len(results_list) == 0:
        raise ValueError("Kunde inte extrahera några giltiga tvärsnitt längs banan.")
        
    # Average the results
    avg_results = {
        "apex_vinkel_deg": np.mean([r["apex_vinkel_deg"] for r in results_list]),
        "asymmetri_deg": np.mean([r["asymmetri_deg"] for r in results_list]),
        "spårdjup_mm": np.mean([r["spårdjup_mm"] for r in results_list]),
        "spårbredd_mm": np.mean([r["spårbredd_mm"] for r in results_list]),
        "djup_bredd_kvot": np.mean([r["djup_bredd_kvot"] for r in results_list]),
        "bottenradie_mm": np.mean([r["bottenradie_mm"] for r in results_list]),
        "ytråhet_mm": np.mean([r["ytråhet_mm"] for r in results_list]),
        "troligt_verktyg": "" # Låter threed.py bestämma verktyg utifrån vinkeln
    }
    
    depth_profile = {
        "distances": distances,
        "depths": depths
    }

    slices = [
        {**{k: float(r[k]) for k in ("apex_vinkel_deg", "asymmetri_deg", "spårdjup_mm", "spårbredd_mm",
                                     "djup_bredd_kvot", "bottenradie_mm", "ytråhet_mm")},
         "position_mm": float(dist), "fit_r2": float(r["fit_r2"]), "profile": raw_profile(*prof)}
        for r, dist, prof in zip(results_list, distances, profiles)
    ]

    return avg_results, plot_data_list[0] if len(plot_data_list) > 0 else None, depth_profile, slices

if __name__ == "__main__":
    print("Testar Modul för 3D-snittning och V-spåranalys...")
    
    mesh = create_mock_v_groove_mesh()
    
    plane_origin = [0, 0, 0]
    groove_direction = [0, 1, 0]
    up_vector = [0, 0, 1]
    
    x_2d, z_2d = extract_2d_profile_from_mesh(mesh, plane_origin, groove_direction, up_vector)
    
    # Lägg till lite brus för realism
    z_2d += np.random.normal(0, 0.1, size=z_2d.shape)
    
    results = calculate_v_angle(x_2d, z_2d)
    
    print(f"Resultat: Vinkel = {results['apex_vinkel_deg']:.2f} grader, Djup = {results['spårdjup_mm']:.2f} mm")
    
    # Vi sparar output direkt i rotmappen för att scriptet convert_to_cmyk ska hitta det om vi pekar på det
    plot_path = os.path.join(os.path.dirname(__file__), "..", "v_groove_plot.pdf")
    plot_profile(x_2d, z_2d, results, plot_path)
    print(f"Plot sparad till: {plot_path}")
