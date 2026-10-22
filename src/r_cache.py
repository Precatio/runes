"""Städning av R-cachen (data/cache/r): varje ny version av korpusen eller R-skripten ger en ny mapp
corpus/<fingeravtryck>/ (med stenarnas och landskapets resultat inuti), och Pröva en egen fråga en ny mapp
question/<fingeravtryck>/, så att cachen annars växer utan gräns (ca 10 MB per korpusversion).

Det som behålls:

* allt för den aktuella korpusversionen (de resultat appen visar nu);
* allt som har ändrats eller skrivits de senaste KEEP_DAYS dygnen (bland annat en körning som pågår);
* av de äldre de KEEP_OTHER senast ändrade versionerna per slag (corpus, question), så att en modul som inte har ändrats
  fortfarande kan kopieras från en tidigare körning i stället för att räknas om (src/r_bridge._reusable).

Annat i cachen (Natural Earths vattenlager, höjdmodellens rutor, status.json) rörs aldrig. Städningen körs högst en
gång om dygnet, i bakgrunden när servern startar (api/main.py); R_CACHE_PRUNE=0 stänger av den. Står "hold": true
i data/cache/r/prune.json väntar städningen tills ägaren släpper den (--release), hur länge det än dröjer.

    .venv/bin/python -m src.r_cache            # visa vad som skulle tas bort (inget tas bort)
    .venv/bin/python -m src.r_cache --hold     # pausa städningen tills vidare
    .venv/bin/python -m src.r_cache --release  # släpp pausen: nästa serverstart städar enligt planen ovan
"""
from __future__ import annotations

import json
import os
import re
import shutil
import time

KEEP_DAYS = 14
KEEP_OTHER = 3
KINDS = ("corpus", "question")
EVERY_S = 24 * 3600
FOLDER = re.compile(r"^[0-9a-f]{16}$")  # a fingerprint (src/r_bridge.fingerprint); nothing else is ever removed
MARK = "prune.json"


def _root(root: str | None) -> str:
    if root is not None:
        return root
    from src import r_bridge
    return r_bridge.CACHE_DIR


def _scan(path: str) -> tuple[float, int]:
    """The newest change anywhere in a folder (its own, its subfolders' and its files' mtimes) and its size in bytes."""
    newest, size = os.path.getmtime(path), 0
    for d, dirs, files in os.walk(path):
        for is_file, names in ((False, dirs), (True, files)):
            for name in names:
                try:
                    st = os.lstat(os.path.join(d, name))
                except OSError:
                    continue
                newest = max(newest, st.st_mtime)
                if is_file:
                    size += st.st_size
    return newest, size


def plan(current_fp: str, root: str | None = None, now: float | None = None, keep_days: float = KEEP_DAYS,
         keep_other: int = KEEP_OTHER) -> dict:
    """Vad städningen skulle ta bort, utan att ta bort något: {"delete": [{kind, name, path, bytes, touched}],
    "keep": [...], "count", "bytes"}. Utan aktuellt fingeravtryck tas ingenting bort."""
    root = _root(root)
    now = time.time() if now is None else now
    delete, keep = [], []
    for kind in KINDS:
        base = os.path.join(root, kind)
        try:
            names = os.listdir(base)
        except OSError:
            continue
        entries = []
        for name in names:
            path = os.path.join(base, name)
            if not FOLDER.match(name) or not os.path.isdir(path) or os.path.islink(path):
                continue
            touched, size = _scan(path)
            entries.append({"kind": kind, "name": name, "path": path, "bytes": size, "touched": touched})
        # the current version and the recently touched ones stay; of the rest, the keep_other newest
        recent = [e for e in entries if e["name"] == current_fp or now - e["touched"] < keep_days * 86400]
        older = sorted((e for e in entries if e not in recent), key=lambda e: -e["touched"])
        keep += recent
        for rank, e in enumerate(older):
            (keep if (not current_fp or rank < keep_other) else delete).append(e)
    return {"current": current_fp, "delete": delete, "keep": keep, "count": len(delete),
            "bytes": sum(e["bytes"] for e in delete)}


def prune(current_fp: str, root: str | None = None, dry_run: bool = True, now: float | None = None) -> dict:
    """Tar bort det som plan() pekar ut (dry_run=False); med dry_run=True (standard) bara planen."""
    out = plan(current_fp, _root(root), now=now)
    if dry_run or not current_fp:
        return {**out, "dry_run": True}
    removed = 0
    for e in out["delete"]:
        shutil.rmtree(e["path"], ignore_errors=True)
        removed += not os.path.exists(e["path"])
    return {**out, "dry_run": False, "removed": removed}


def _mark(root: str) -> dict | None:
    try:
        with open(os.path.join(root, MARK), encoding="utf-8") as fh:
            mark = json.load(fh)
    except (OSError, ValueError):
        return None
    return mark if isinstance(mark, dict) else None


def held(root: str | None = None) -> bool:
    """Har ägaren pausat städningen ("hold": true i prune.json)?"""
    mark = _mark(_root(root))
    return bool(mark and mark.get("hold") is True)


def due(root: str | None = None, now: float | None = None) -> bool:
    """Har det gått ett dygn sedan den senaste städningen, och är den inte pausad?"""
    now = time.time() if now is None else now
    mark = _mark(_root(root))
    if mark is None:
        return True
    if mark.get("hold") is True:
        return False
    try:
        return now - float(mark["at"]) >= EVERY_S
    except (ValueError, KeyError, TypeError):
        return True


def set_hold(on: bool, root: str | None = None) -> dict:
    """Pausar (on=True) eller släpper städningen; tiden för den senaste städningen behålls."""
    root = _root(root)
    mark = _mark(root) or {}
    if on:
        mark.update(hold=True, note="paused by the owner: no prune until `python -m src.r_cache --release`")
    else:
        mark.pop("hold", None)
        mark["note"] = "released by the owner: prunes at most once a day from the next server start"
        mark["at"] = 0  # the next server start prunes (after R_CACHE_PRUNE_DELAY)
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, MARK), "w", encoding="utf-8") as fh:
        json.dump(mark, fh)
    return mark


def prune_daily(current_fp: str, root: str | None = None) -> dict | None:
    """Städar högst en gång om dygnet (None när det inte är dags); antecknar när det gjordes i prune.json."""
    root = _root(root)
    if not current_fp or not due(root):
        return None
    out = prune(current_fp, root, dry_run=False)
    try:
        with open(os.path.join(root, MARK), "w", encoding="utf-8") as fh:
            json.dump({"at": time.time(), "current": current_fp, "removed": out.get("removed", 0),
                       "bytes": out["bytes"]}, fh)
    except OSError:
        pass
    return out


def main() -> None:
    import sys
    if "--hold" in sys.argv[1:] or "--release" in sys.argv[1:]:
        print(json.dumps(set_hold("--hold" in sys.argv[1:]), ensure_ascii=False))
        return
    from api.routers import rstats
    out = prune(rstats.fingerprint(), dry_run=True)
    print(json.dumps({"current": out["current"], "held": held(), "count": out["count"], "bytes": out["bytes"],
                      "delete": [f"{e['kind']}/{e['name']}" for e in out["delete"]]}, indent=1))


if __name__ == "__main__":
    main()
