"""The mesh cache frees a model as soon as it is evicted (api/mesh_cache.py): trimesh models sit in reference cycles,
so without an explicit collection they lived on until a rare full garbage collection (30 GB after nine scans)."""
import gc
import weakref

import trimesh

from api import mesh_cache


def test_an_evicted_model_is_freed_at_once(monkeypatch):
    monkeypatch.setattr(mesh_cache, "MAX_ENTRIES", 1)
    monkeypatch.setattr(mesh_cache, "_cache", type(mesh_cache._cache)())
    was = gc.isenabled()
    gc.disable()  # prove that the cache itself frees it, not an automatic collection
    try:
        m1 = trimesh.creation.icosphere(subdivisions=3)
        _ = m1.triangles_center, m1.face_normals
        e1 = mesh_cache.MeshEntry(m1, {})
        _ = e1.face_tree
        mesh_cache.put("a", e1)
        ref = weakref.ref(m1)
        del m1, e1, _
        assert ref() is not None  # still cached
        mesh_cache.put("b", mesh_cache.MeshEntry(trimesh.creation.box(), {}))
        assert ref() is None  # evicted and freed, cycles included
    finally:
        if was:
            gc.enable()
