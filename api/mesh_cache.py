"""Minnescache för uppladdade 3D-modeller.

En skanning laddas upp en gång och får ett id (filens SHA-256). Alla senare anrop (snitt, ett klick,
automatisk analys, visningsmodell) använder id:t i stället för att skicka filen igen.

Minnet: en trimesh-modell ingår i referenscykler (modellen och dess cache pekar på varandra), så den frigörs inte när
den lämnar cachen utan först när Pythons skräpsamlare körs – och den körs sällan i en server som mest hanterar stora
numpy-fält. Efter nio skanningar på 0,5–1,6 GB höll analysmotorn 30 GB (2026-10-24). Därför städas det uttryckligen
när en modell lämnar cachen (put) och efter de tunga 3D-anropen (api/main.py, CollectAfter3D).
"""
import gc
import os
import threading
from collections import OrderedDict

from fastapi import HTTPException
from scipy.spatial import cKDTree

MAX_ENTRIES = int(os.environ.get("MESH_CACHE_SIZE", "2"))


class MeshEntry:
    def __init__(self, mesh, info: dict):
        self.mesh = mesh
        self.info = info
        self._lock = threading.Lock()
        self._vertex_tree = None
        self._face_tree = None
        # The last view model (api/routers/threed.view_model): (target face count, binary STL, its face count), and a
        # lock so that two requests for it decimate once
        self.view = None
        self.view_lock = threading.Lock()

    @property
    def vertex_tree(self) -> cKDTree:
        with self._lock:
            if self._vertex_tree is None:
                self._vertex_tree = cKDTree(self.mesh.vertices)
            return self._vertex_tree

    @property
    def face_tree(self) -> cKDTree:
        with self._lock:
            if self._face_tree is None:
                self._face_tree = cKDTree(self.mesh.triangles_center)
            return self._face_tree


_cache: "OrderedDict[str, MeshEntry]" = OrderedDict()
_lock = threading.Lock()


def put(mesh_id: str, entry: MeshEntry) -> MeshEntry:
    evicted = []
    with _lock:
        _cache[mesh_id] = entry
        _cache.move_to_end(mesh_id)
        while len(_cache) > MAX_ENTRIES:
            evicted.append(_cache.popitem(last=False)[1])
    if evicted:
        evicted.clear()
        gc.collect()  # the evicted models are in reference cycles: free them now, not at some later collection
    return entry


def peek(mesh_id: str) -> MeshEntry | None:
    with _lock:
        entry = _cache.get(mesh_id)
        if entry is not None:
            _cache.move_to_end(mesh_id)
        return entry


def get(mesh_id: str) -> MeshEntry:
    entry = peek(mesh_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail="3D-modellen finns inte längre i analysmotorns minne (t.ex. efter omstart). Ladda upp filen igen.",
        )
    return entry
