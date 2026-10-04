"""Syntetiska runstenar med kända spårmått, för test och validering av mätmetoderna."""
import numpy as np
import trimesh


def _segment_distance(X, Y, p0, p1):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    t = np.clip(((X - p0[0]) * d[0] + (Y - p0[1]) * d[1]) / (d @ d), 0, 1)
    return np.hypot(X - (p0[0] + t * d[0]), Y - (p0[1] + t * d[1]))


def rune_stone(size=(160.0, 120.0), resolution=0.5, opening_angle_deg=70.0, depth_mm=4.0,
               noise_mm=0.03, curvature=0.0008, seed=0, segments=None, tilt_deg=0.0):
    """Höjdfältsyta med V-formade spår (öppningsvinkel och djup givna) längs linjesegment.

    Ytan välvs lätt (curvature) och får mätbrus. Med tilt_deg vrids hela stenen kring x-axeln,
    så att den ristade ytans normal inte längre är z."""
    w, h = size
    xs = np.arange(-w / 2, w / 2 + 1e-9, resolution)
    ys = np.arange(-h / 2, h / 2 + 1e-9, resolution)
    X, Y = np.meshgrid(xs, ys)
    Z = -curvature * (X ** 2 + Y ** 2)
    segments = segments or [((-50, -40), (-50, 40)), ((-50, 10), (-15, 40)), ((10, -40), (40, 40)),
                            ((10, 0), (50, -20))]
    half = np.radians(opening_angle_deg / 2)
    groove = np.zeros_like(Z)
    for p0, p1 in segments:
        d = _segment_distance(X, Y, p0, p1)
        groove = np.minimum(groove, np.minimum(0, d / np.tan(half) - depth_mm))
    rng = np.random.default_rng(seed)
    Z = Z + groove + rng.normal(0, noise_mm, Z.shape)

    ny, nx = Z.shape
    verts = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    i = np.arange(ny - 1)[:, None] * nx + np.arange(nx - 1)[None, :]
    i = i.ravel()
    faces = np.vstack([np.column_stack([i, i + 1, i + nx]), np.column_stack([i + 1, i + nx + 1, i + nx])])
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    if tilt_deg:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.radians(tilt_deg), [1, 0, 0]))
    return mesh
