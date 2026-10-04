"""Minnescache för uppladdade 3D-modeller.

En skanning laddas upp en gång och får ett id (filens SHA-256). Alla senare anrop (snitt, ett klick,
automatisk analys, visningsmodell) använder id:t i stället för att skicka filen igen.
"""
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
    with _lock:
        _cache[mesh_id] = entry
        _cache.move_to_end(mesh_id)
        while len(_cache) > MAX_ENTRIES:
            _cache.popitem(last=False)
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
