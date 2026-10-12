"""Färdiga JSON-svar för de stora svaren som sällan ändras (mönsterkartan, stenöversikten, korpusanalyserna, kartans
inskrifter, metodbeskrivningen och fynden).

Svaret serialiseras en gång per nyckel – nyckeln ska innehålla det som svaret bygger på, t.ex. korpusens fingeravtryck –
och skickas sedan som färdiga byte, utan FastAPI:s genomgång av hela strukturen vid varje anrop. Varje svar får en ETag:
webbläsaren frågar med If-None-Match och får 304 utan innehåll så länge svaret inte har ändrats (Cache-Control: no-cache,
alltså alltid en kontroll mot servern, aldrig ett gammalt svar).
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import threading
from typing import Callable

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder

MAX_ENTRIES = 48
_entries: dict[str, tuple[bytes, str]] = {}
_gzipped: dict[str, bytes] = {}
_lock = threading.Lock()


_building: dict[str, threading.Lock] = {}


def json_bytes(key: str, build: Callable[[], object]) -> tuple[bytes, str]:
    """Svaret som JSON-byte och dess ETag, byggt bara första gången för nyckeln. Kommer två anrop samtidigt (t.ex. under
    uppvärmningen när servern startar) väntar det andra på det första i stället för att räkna samma sak två gånger."""
    with _lock:
        hit = _entries.get(key)
        if hit is not None:
            return hit
        lock = _building.setdefault(key, threading.Lock())
    with lock:
        with _lock:
            hit = _entries.get(key)
        if hit is not None:
            return hit
        body = json.dumps(jsonable_encoder(build()), ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()
        hit = (body, '"' + hashlib.sha256(body).hexdigest()[:24] + '"')
        with _lock:
            while len(_entries) >= MAX_ENTRIES:
                _gzipped.pop(_entries.pop(next(iter(_entries)))[1], None)
            _entries[key] = hit
            _building.pop(key, None)
    return hit


def cached_json(request: Request | None, key: str, build: Callable[[], object]) -> Response:
    """Ett JSON-svar ur cachen, eller 304 när webbläsaren redan har det."""
    body, etag = json_bytes(key, build)
    headers = {"ETag": etag, "Cache-Control": "no-cache", "Vary": "Accept-Encoding"}
    if request is not None and etag in (request.headers.get("if-none-match") or ""):
        return Response(status_code=304, headers=headers)
    # Compressed once and kept, instead of once per request (the gzip middleware lets an encoded answer through)
    if request is not None and "gzip" in (request.headers.get("accept-encoding") or "") and len(body) > 1024:
        with _lock:
            gz = _gzipped.get(etag)
        if gz is None:
            gz = gzip.compress(body, compresslevel=6)
            with _lock:
                _gzipped[etag] = gz
        return Response(gz, media_type="application/json",
                        headers={**headers, "Content-Encoding": "gzip", "X-Content-Length": str(len(body))})
    return Response(body, media_type="application/json", headers=headers)


def clear() -> None:
    with _lock:
        _entries.clear()
        _gzipped.clear()


def dir_version(path: str) -> str:
    """Antal filer och senaste ändring i en katalog, som del av en nyckel (t.ex. avstämningarna mot Runor)."""
    try:
        stamps = [e.stat().st_mtime for e in os.scandir(path) if e.is_file()]
    except OSError:
        return "0"
    return f"{len(stamps)}:{max(stamps, default=0):.0f}"


class ContentLengthHeader:
    """Lägger svarets okomprimerade storlek i X-Content-Length, före komprimeringen, så att laddningsraden kan visa
    verklig andel också när svaret skickas gzip-komprimerat (components/LoadingBar.tsx)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def wrapped(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                length = next((v for k, v in headers if k.lower() == b"content-length"), None)
                if length is not None and not any(k.lower() == b"x-content-length" for k, _ in headers):
                    headers.append((b"x-content-length", length))
                    message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, wrapped)
