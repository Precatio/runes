import numpy as np
import pytest

from src.slice_analysis import (
    analyze_path,
    calculate_v_angle,
    create_mock_v_groove_mesh,
    extract_2d_profile_from_mesh,
    find_auto_slice,
    snap_path_to_bottom,
)

UP = np.array([0.0, 0.0, 1.0])


@pytest.fixture(scope="module")
def mesh():
    # V-groove along Y with wall slopes -1.5 (left) and 1.2 (right)
    return create_mock_v_groove_mesh()


@pytest.fixture(scope="module")
def profile(mesh):
    x, z = extract_2d_profile_from_mesh(mesh, np.zeros(3), np.array([0.0, 1.0, 0.0]), UP)[:2]
    return x, z


def test_wall_fits_recover_mock_slopes(profile):
    res = calculate_v_angle(*profile)
    assert res["fit_left"][0] == pytest.approx(-1.5, abs=0.05)
    assert res["fit_right"][0] == pytest.approx(1.2, abs=0.05)


def test_asymmetry_matches_slope_difference(profile):
    res = calculate_v_angle(*profile)
    expected = abs(np.degrees(np.arctan(1 / 1.5)) - np.degrees(np.arctan(1 / 1.2)))
    assert res["asymmetri_deg"] == pytest.approx(expected, abs=0.5)


def test_width_and_depth(profile):
    res = calculate_v_angle(*profile)
    assert res["spårbredd_mm"] == pytest.approx(20.0, abs=0.5)
    assert res["spårdjup_mm"] > 10
    assert res["djup_bredd_kvot"] == pytest.approx(res["spårdjup_mm"] / res["spårbredd_mm"])


def test_find_auto_slice_crosses_groove(mesh):
    p1, p2 = find_auto_slice(mesh, np.zeros(3), radius=5.0)
    assert p1 is not None and p2 is not None
    # Slice line should run across the groove (along X), centred on the click
    assert abs(p1[0] - p2[0]) > 10
    assert np.allclose((np.array(p1) + np.array(p2)) / 2, 0, atol=1e-6)


def test_find_auto_slice_needs_geometry(mesh):
    assert find_auto_slice(mesh, np.array([500.0, 500.0, 500.0])) == (None, None)


def test_snap_path_moves_points_to_groove_bottom(mesh):
    snapped = snap_path_to_bottom(mesh, [[1, 0, 3], [1, 1, 3], [1, 2, 3]], UP)
    assert all(abs(p[0]) < 1.0 and p[2] < 1.0 for p in snapped)


def test_analyze_path_averages_slices(mesh, profile):
    avg, plot_data, depth_profile, slices = analyze_path(mesh, [[0, -5, 0], [0, 0, 0], [0, 5, 0]], UP)
    single = calculate_v_angle(*profile)
    assert avg["apex_vinkel_deg"] == pytest.approx(single["apex_vinkel_deg"], abs=1.0)
    assert plot_data is not None and len(plot_data["x"]) == len(plot_data["z"])
    assert len(depth_profile["distances"]) == len(depth_profile["depths"]) == len(slices) > 0
    assert {"apex_vinkel_deg", "position_mm"} <= slices[0].keys()


def test_apex_angle_is_opening_angle_of_v(profile):
    # Walls with slopes -1.5 and 1.2 open by atan(1/1.5) + atan(1/1.2) ≈ 73.5°
    res = calculate_v_angle(*profile)
    expected = np.degrees(np.arctan(1 / 1.5) + np.arctan(1 / 1.2))
    assert res["apex_vinkel_deg"] == pytest.approx(expected, abs=1.0)


def test_apex_angle_on_75_degree_fixture():
    import os
    import trimesh

    path = os.path.join(os.path.dirname(__file__), "..", "test_runestone_groove_75deg.obj")
    if not os.path.exists(path):
        pytest.skip("75°-fixturen saknas (skapas med scripts/generate_test_stone.py)")
    mesh = trimesh.load(path)
    centre = (mesh.bounds[0] + mesh.bounds[1]) / 2
    centre[1] = 0
    # The fixture uses Y as the up axis and runs the groove along Z
    x, z = extract_2d_profile_from_mesh(mesh, centre, np.array([0.0, 0.0, 1.0]), np.array([0.0, 1.0, 0.0]))[:2]
    assert calculate_v_angle(x, z)["apex_vinkel_deg"] == pytest.approx(75.0, abs=3.0)
