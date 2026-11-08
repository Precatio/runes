"""Bergartskontrollen vid lika vanliga bergartsfamiljer (2026-11-08): en tvetydig benämning avgörs av den familj där
den skiljer minst, inte av ordningen i en mängd (som Python slumpar per process)."""
from src import geology, synthesis


def test_ambiguous_rock_name_is_decided_by_the_least_distinctive_family(monkeypatch):
    prof = {"n": 9, "families": {"granitoid": 0.778, "gnejs": 0.778},
            "materials": [{"material": "gråsten", "n": 5}, {"material": "granit", "n": 2}, {"material": "gnejs", "n": 2}]}
    monkeypatch.setattr(geology, "carver_materials", lambda *a, **k: prof)
    monkeypatch.setattr(synthesis, "_province_families", lambda *a, **k: ({"granitoid": 0.688, "gnejs": 0.401}, 247))
    rec = {"signum": "Sö 245", "material": "gråsten"}
    assert geology.families("gråsten") == {"granitoid", "gnejs"}
    out = synthesis.material_check(rec, "Halvdan", [])
    # granitoid: 0.778 / 0.688 = 1.13 < 1.5 → the rock does not tell carvers apart, whatever the order of the set
    assert out["fits"] is None
    assert "Granit och närstående" in out["text"] and "(69 %" in out["text"]


def test_distinctive_family_still_counts(monkeypatch):
    prof = {"n": 9, "families": {"granitoid": 0.778, "gnejs": 0.778}, "materials": [{"material": "gråsten", "n": 9}]}
    monkeypatch.setattr(geology, "carver_materials", lambda *a, **k: prof)
    monkeypatch.setattr(synthesis, "_province_families", lambda *a, **k: ({"granitoid": 0.30, "gnejs": 0.40}, 247))
    out = synthesis.material_check({"signum": "Sö 245", "material": "gråsten"}, "Halvdan", [])
    assert out["fits"] is True  # both readings are distinctive (2.6 and 1.9)
