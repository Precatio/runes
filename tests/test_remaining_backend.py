"""The remaining audit items of 2026-10-22: a broken slice is skipped, half-written WebP files never reach the website's
commit, a commit whose push failed is pushed by the next publication, the engine's own /docs can write, and the R
cache is pruned without touching the current results."""
import json
import os
import subprocess
import time
import types

import numpy as np
import pytest


# ---- 1. measure_slices: one slice that fails, whatever the error, is skipped ------------------------------------------

def _fake_slices(monkeypatch, errors: dict):
    from api.routers import threed
    from src.stats import METRICS
    calls = []

    def profile(mesh, point, direction, up, window_mm, face_tree):
        i = len(calls)
        calls.append(i)
        if i in errors:
            raise errors[i]
        x = np.linspace(-1, 1, 21)
        return x, np.abs(x)

    def angle(x, z):
        return {**{k: 1.0 for k in METRICS}, "fit_r2": 0.99, "x": x, "z": z, "apex_idx": 10}
    monkeypatch.setattr(threed, "extract_2d_profile_from_mesh", profile)
    monkeypatch.setattr(threed, "calculate_v_angle", angle)
    return types.SimpleNamespace(mesh=None, info={"mock": True}, face_tree=None)


def test_a_slice_that_fails_with_any_error_is_skipped(monkeypatch):
    from api.routers import threed
    entry = _fake_slices(monkeypatch, {1: TypeError("trimesh"), 2: RuntimeError("scipy"), 3: ValueError("few points"),
                                       4: KeyError("x")})
    slices, main = threed.measure_slices(entry, [0, 0, 0], [1, 0, 0], [0, 0, 1], 7, 1.0, 5.0)
    assert len(slices) == 3 and main is not None
    assert [s["position_mm"] for s in slices] == [-3.0, 2.0, 3.0]


def test_an_unexpected_slice_error_is_logged_as_a_warning(monkeypatch):
    import logging

    from api.errors import logger
    from api.routers import threed
    seen = []

    class Collect(logging.Handler):
        def emit(self, record):
            seen.append(record)
    handler = Collect(level=logging.WARNING)
    logger.addHandler(handler)
    try:
        entry = _fake_slices(monkeypatch, {0: ValueError("few points"), 1: IndexError("edge")})
        threed.measure_slices(entry, [0, 0, 0], [1, 0, 0], [0, 0, 1], 5, 1.0, 5.0)
        assert seen == []  # what geometry normally fails with is skipped quietly
        entry = _fake_slices(monkeypatch, {i: TypeError("changed signature") for i in range(5)})
        slices, _ = threed.measure_slices(entry, [0, 0, 0], [1, 0, 0], [0, 0, 1], 5, 1.0, 5.0)
    finally:
        logger.removeHandler(handler)
    warn = [r.getMessage() for r in seen]
    assert slices == [] and len(warn) == 1 and "5 av 5 snitt" in warn[0] and "TypeError" in warn[0]


@pytest.mark.parametrize("err", [KeyboardInterrupt(), SystemExit(1), MemoryError()])
def test_interrupts_and_memory_errors_still_stop_the_analysis(monkeypatch, err):
    from api.routers import threed
    entry = _fake_slices(monkeypatch, {1: err})
    with pytest.raises(type(err)):
        threed.measure_slices(entry, [0, 0, 0], [1, 0, 0], [0, 0, 1], 3, 1.0, 5.0)


# ---- 2. WebP copies: the temporary file is never in the figure folder ---------------------------------------------------

def _png(path, size=(40, 30)):
    from PIL import Image
    Image.new("RGB", size, (200, 30, 30)).save(path)


def test_the_webp_conversion_writes_its_temporary_file_outside_the_figure_folder(tmp_path, monkeypatch):
    from src import blog_figures
    monkeypatch.setattr(blog_figures, "TMP_DIR", str(tmp_path / "tmp"))
    figures = tmp_path / "figurer"
    figures.mkdir()
    _png(tmp_path / "a.png")
    seen = []
    real_save = __import__("PIL.Image", fromlist=["Image"]).Image.save

    def save(im, fp, *a, **kw):
        seen.append(os.listdir(figures))  # while the WebP is being written, nothing is in the figure folder
        return real_save(im, fp, *a, **kw)
    monkeypatch.setattr("PIL.Image.Image.save", save)
    blog_figures.to_site(str(tmp_path / "a.png"), str(figures / "x.webp"))
    assert seen == [[]] and os.listdir(figures) == ["x.webp"] and os.listdir(tmp_path / "tmp") == []
    assert os.stat(figures / "x.webp").st_mode & 0o777 == 0o644  # not mkstemp's owner-only 0600


def test_a_figure_copied_across_disks_is_readable_too(tmp_path, monkeypatch):
    from src import blog_figures
    monkeypatch.setattr(blog_figures, "TMP_DIR", str(tmp_path / "tmp"))
    figures = tmp_path / "figurer"
    figures.mkdir()
    _png(tmp_path / "a.png")
    real_replace = os.replace

    def replace(a, b):  # the first rename (tmp -> figure folder) fails as across two disks
        if str(a).startswith(str(tmp_path / "tmp")):
            raise OSError(18, "Invalid cross-device link")
        return real_replace(a, b)
    monkeypatch.setattr(blog_figures.os, "replace", replace)
    blog_figures.to_site(str(tmp_path / "a.png"), str(figures / "x.webp"))
    assert os.listdir(figures) == ["x.webp"] and os.stat(figures / "x.webp").st_mode & 0o777 == 0o644


def test_an_interrupted_conversion_leaves_nothing_behind(tmp_path, monkeypatch):
    from src import blog_figures
    monkeypatch.setattr(blog_figures, "TMP_DIR", str(tmp_path / "tmp"))
    figures = tmp_path / "figurer"
    figures.mkdir()
    _png(tmp_path / "a.png")

    def broken(im, fp, *a, **kw):
        open(fp, "wb").write(b"half")
        raise OSError("killed")
    monkeypatch.setattr("PIL.Image.Image.save", broken)
    with pytest.raises(OSError):
        blog_figures.to_site(str(tmp_path / "a.png"), str(figures / "x.webp"))
    assert os.listdir(figures) == [] and os.listdir(tmp_path / "tmp") == []


def test_the_export_removes_stray_temporary_files_from_the_figure_folder():
    import datetime as dt
    from src import site_export
    os.makedirs(site_export.FIGURES, exist_ok=True)
    for name in ("abc.webp.tmp", ".abc.webp.part", "old.png"):
        open(os.path.join(site_export.FIGURES, name), "wb").write(b"x")
    post = {"id": "a", "slug": "a", "title": "A", "body": "Text", "published": True,
            "publishedAt": "2026-10-01T00:00:00+00:00", "updatedAt": "2026-10-01T00:00:00+00:00"}
    out = site_export.export([post], dt.datetime(2026, 10, 22, tzinfo=dt.timezone.utc).isoformat(), force=True)
    assert "blocked" not in out and os.listdir(site_export.FIGURES) == []


# ---- 3. push(): a commit whose push failed is pushed by the next publication -------------------------------------------

def _run(cwd, *args):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A temporary clone with a bare remote (never the real repository), with site_export pointed at it."""
    from src import site_export
    base = tmp_path  # pytest's own temporary directory (pass --basetemp to put it elsewhere)
    remote, work = base / "remote.git", base / "work"
    _run(base, "init", "--bare", "-q", "-b", "main", str(remote))
    _run(base, "clone", "-q", str(remote), str(work))
    for k, v in (("user.email", "test@example.invalid"), ("user.name", "Test"), ("commit.gpgsign", "false")):
        _run(work, "config", k, v)
    (work / "README").write_text("x\n")
    _write_site(work, '{"posts": []}\n')  # as in the real repository: the website's files are tracked already
    (work / "web" / "public" / "figurer" / "first.webp").write_bytes(b"webp")
    _run(work, "add", "-A")
    _run(work, "commit", "-q", "-m", "start")
    _run(work, "push", "-q", "-u", "origin", "main")
    monkeypatch.setattr(site_export, "ROOT", str(work))
    monkeypatch.setattr(site_export, "CONTENT", str(work / "web" / "content" / "articles.json"))
    monkeypatch.setattr(site_export, "SEARCH", str(work / "web" / "public" / "artiklar-sok.json"))
    monkeypatch.setattr(site_export, "FIGURES", str(work / "web" / "public" / "figurer"))
    monkeypatch.setattr(site_export.time, "sleep", lambda s: None)
    yield types.SimpleNamespace(work=work, remote=remote)


def _write_site(work, text):
    os.makedirs(work / "web" / "content", exist_ok=True)
    os.makedirs(work / "web" / "public" / "figurer", exist_ok=True)
    (work / "web" / "content" / "articles.json").write_text(text)
    (work / "web" / "public" / "artiklar-sok.json").write_text(text)


def test_a_commit_whose_push_failed_is_pushed_next_time(repo, monkeypatch):
    from src import site_export
    _write_site(repo.work, '{"posts": [1]}\n')
    real = site_export._git
    monkeypatch.setattr(site_export, "_git", lambda *a: subprocess.CompletedProcess(a, 1, "", "offline")
                        if a[0] == "push" else real(*a))
    out = site_export.push()
    assert out["pushed"] is False and out["note"].startswith("Committat men inte pushat")
    assert site_export._ahead() == 1 and site_export.status()["unpushed"] is True
    monkeypatch.setattr(site_export, "_git", real)
    out = site_export.push()  # nothing new to commit, but the branch is ahead of origin
    assert out["pushed"] is True
    assert _run(repo.work, "rev-parse", "HEAD") == _run(repo.remote, "rev-parse", "main")
    assert site_export._ahead() == 0 and site_export.status()["unpushed"] is False
    assert site_export.push()["note"] == "Webbplatsen har redan de senaste artiklarna."


def test_an_unpushed_code_commit_neither_triggers_a_push_nor_shows_as_unpublished(repo):
    from src import site_export
    (repo.work / "README").write_text("held back locally\n")
    _run(repo.work, "commit", "-q", "-am", "code, not pushed yet")
    assert site_export._ahead() == 0 and site_export._ahead(site_only=False) == 1
    assert site_export.status()["unpushed"] is False
    assert site_export.push()["note"] == "Webbplatsen har redan de senaste artiklarna."
    assert _run(repo.remote, "rev-list", "--count", "main").strip() == "1"  # the code commit stayed local
    # an article commit on top of it has to take it along, and the answer says so
    _write_site(repo.work, '{"posts": [3]}\n')
    out = site_export.push()
    assert out["pushed"] is True and out["others"] == 1 and "1 andra commit på grenen följde med" in out["note"]


def test_no_upstream_is_handled(repo):
    from src import site_export
    _run(repo.work, "branch", "--unset-upstream")
    assert site_export._ahead() is None
    assert site_export.push()["note"] == "Webbplatsen har redan de senaste artiklarna."


def test_half_written_figures_are_never_committed(repo):
    from src import site_export
    _write_site(repo.work, '{"posts": [2]}\n')
    figures = repo.work / "web" / "public" / "figurer"
    (figures / "good.webp").write_bytes(b"webp")
    (figures / "good.webp.tmp").write_bytes(b"half")
    (figures / ".good.webp.part").write_bytes(b"half")
    assert site_export.push()["pushed"] is True
    files = _run(repo.work, "ls-files").split()
    assert "web/public/figurer/good.webp" in files
    assert not any(f.endswith((".tmp", ".part")) for f in files)
    assert site_export.check_git() is True or not site_export.enabled()


# ---- 4. SameSiteWrites: the engine's own /docs page may write, its other pages may not---------------------------------------------------------

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


DOCS = "http://localhost:8000/docs"


@pytest.mark.parametrize("host,origin,site,referer,refused", [
    ("localhost:8000", "http://localhost:8000", "same-origin", DOCS, False),     # Swagger's "Try it out"
    ("127.0.0.1:8000", "http://127.0.0.1:8000", None, "http://127.0.0.1:8000/redoc", False),
    ("localhost:8000", "http://localhost:8000", "same-origin", DOCS + "/oauth2-redirect?x=1", False),
    ("localhost:8000", "http://localhost:3000", "same-site", None, False),       # the app (CORS_ORIGINS)
    ("localhost:8000", "https://evil.example", "cross-site", DOCS, True),        # a foreign page
    ("localhost:8000", "http://localhost:8001", "same-site", DOCS, True),        # another port is another origin
    ("localhost:8000", "http://localhost:8000", "cross-site", DOCS, True),       # the browser says cross-site
    # other pages from the engine's own origin may not write: an R html_map figure, a lookalike path, no Referer
    ("localhost:8000", "http://localhost:8000", "same-origin", "http://localhost:8000/api/r/figure/x/map.html", True),
    ("localhost:8000", "http://localhost:8000", "same-origin", "http://localhost:8000/docsx", True),
    ("localhost:8000", "http://localhost:8000", "same-origin", "http://localhost:8001/docs", True),
    ("localhost:8000", "http://localhost:8000", "same-origin", None, True),
    ("localhost:8000", None, "cross-site", None, True),
    ("localhost:8000", None, None, None, False),                                 # scripts and the Next server
])
def test_same_origin_writes_from_the_engines_own_pages(client, host, origin, site, referer, refused):
    headers = {"host": host}
    if origin:
        headers["origin"] = origin
    if site:
        headers["sec-fetch-site"] = site
    if referer:
        headers["referer"] = referer
    r = client.post("/api/__no_such_route__", headers=headers)
    assert (r.status_code == 403) == refused, r.text


def test_the_own_origin_needs_an_allowed_host():
    import asyncio
    from api.main import SameSiteWrites
    seen = []

    async def app(scope, receive, send):
        seen.append(scope["path"])
    mw = SameSiteWrites(app, origins=[], hosts=["localhost"])
    sent = []

    async def send(msg):
        sent.append(msg)

    async def receive():
        return {"type": "http.request", "body": b""}
    for host, ok in ((b"localhost:8000", True), (b"evil.example:8000", False)):
        scope = {"type": "http", "method": "POST", "scheme": "http", "path": "/x",
                 "headers": [(b"host", host), (b"origin", b"http://" + host), (b"referer", b"http://" + host + b"/docs")]}
        seen.clear(), sent.clear()
        asyncio.run(mw(scope, receive, send))
        assert bool(seen) == ok


# ---- 5. The R cache: older versions are pruned, the current one never --------------------------------------------------

def _folder(root, kind, name, age_days, size=10):
    d = root / kind / name
    os.makedirs(d / "stones" / "k", exist_ok=True)
    f = d / "stones" / "k" / "stone.json"
    f.write_bytes(b"x" * size)
    t = time.time() - age_days * 86400
    for p in (f, d / "stones" / "k", d / "stones", d):
        os.utime(p, (t, t))
    return d


def test_the_r_cache_keeps_the_current_the_recent_and_the_newest_few(tmp_path):
    from src import r_cache
    cur = "a" * 16
    _folder(tmp_path, "corpus", cur, 400)                  # the current version, however old
    old = [_folder(tmp_path, "corpus", f"{i:016x}", 20 + i) for i in range(6)]  # all older than 14 days
    recent = _folder(tmp_path, "corpus", "b" * 16, 3)       # touched this week
    _folder(tmp_path, "question", cur, 100)
    q_old = [_folder(tmp_path, "question", f"{i:016x}", 30 + i) for i in range(5)]
    for keep in ("naturalearth/coastline", "terrain/12"):
        os.makedirs(tmp_path / keep)
    (tmp_path / "status.json").write_text("{}")
    os.makedirs(tmp_path / "corpus" / "not-a-fingerprint")

    plan = r_cache.prune(cur, str(tmp_path))  # a dry run by default
    gone = {(e["kind"], e["name"]) for e in plan["delete"]}
    # the recent one and the 3 newest other versions are kept; the 3 oldest corpus and 2 oldest question folders go
    assert gone == {("corpus", o.name) for o in old[3:]} | {("question", q.name) for q in q_old[3:]}
    assert plan["count"] == 5 and plan["bytes"] == 50 and plan["dry_run"] is True
    assert all(os.path.isdir(o) for o in old)  # nothing removed by the dry run

    out = r_cache.prune_daily(cur, str(tmp_path))
    assert out["removed"] == 5 and not any(os.path.exists(o) for o in old[3:])
    assert os.path.isdir(tmp_path / "corpus" / cur) and os.path.isdir(recent) and os.path.isdir(old[0])
    assert os.path.isdir(tmp_path / "naturalearth" / "coastline") and os.path.isdir(tmp_path / "corpus" / "not-a-fingerprint")
    assert r_cache.prune_daily(cur, str(tmp_path)) is None  # at most once a day
    assert not r_cache.due(str(tmp_path)) and r_cache.due(str(tmp_path), now=time.time() + 86401)


def test_the_r_cache_is_never_pruned_without_the_current_version(tmp_path):
    from src import r_cache
    for i in range(6):
        _folder(tmp_path, "corpus", f"{i:016x}", 60)
    assert r_cache.prune("", str(tmp_path), dry_run=False)["dry_run"] is True
    assert r_cache.prune_daily("", str(tmp_path)) is None
    assert len(os.listdir(tmp_path / "corpus")) == 6


def test_a_held_r_cache_waits_for_the_owner(tmp_path):
    from src import r_cache
    cur = "a" * 16
    for i in range(6):
        _folder(tmp_path, "corpus", f"{i:016x}", 60)
    (tmp_path / "prune.json").write_text(json.dumps({"at": 0, "hold": True}))
    # however long ago the last prune was, a hold keeps everything
    assert r_cache.held(str(tmp_path)) and not r_cache.due(str(tmp_path), now=time.time() + 365 * 86400)
    assert r_cache.prune_daily(cur, str(tmp_path)) is None and len(os.listdir(tmp_path / "corpus")) == 6
    r_cache.set_hold(False, str(tmp_path))
    assert not r_cache.held(str(tmp_path)) and r_cache.due(str(tmp_path))
    assert r_cache.prune_daily(cur, str(tmp_path))["removed"] == 3
    r_cache.set_hold(True, str(tmp_path))
    assert r_cache.held(str(tmp_path)) and not r_cache.due(str(tmp_path), now=time.time() + 365 * 86400)


# ---- yes/no form fields that default to True are read as text (FastAPI >= 0.160 reads a missing bool as False) ---------

def test_form_flag_keeps_true_default_and_pydantic_words():
    from fastapi import HTTPException

    from api.routers.threed import form_flag
    assert form_flag(None, True, "measure") is True and form_flag(None, False, "x") is False
    for word in ("true", "True", "1", "on", "yes", " t "):
        assert form_flag(word, False, "measure") is True
    for word in ("false", "0", "off", "no", "F"):
        assert form_flag(word, True, "measure") is False
    with pytest.raises(HTTPException) as e:
        form_flag("kanske", True, "measure")
    assert e.value.status_code == 422
