"""Dokumentation för webbplatsen: METHODS.md som HTML och förteckningar över moduler, skript och R-moduler.

Webbsidan visar alltid den metodbeskrivning som hör till koden som körs – det finns ingen separat text att
hålla i takt.
"""
import ast
import glob
import os
import re
from functools import lru_cache

from fastapi import APIRouter

from src import limitations

router = APIRouter()

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = "https://github.com/Precatio/runes/blob/main/"


def _link_sources(html: str) -> str:
    """`src/x.py`, `scripts/x.py`, `r/x.R` m.fl. i koden blir länkar till källkoden på GitHub."""
    def link(m):
        path = m.group(1)
        return (f'<a href="{REPO}{path}" target="_blank" rel="noopener noreferrer"><code>{path}</code></a>'
                if os.path.exists(os.path.join(ROOT, path)) else m.group(0))
    return re.sub(r"<code>((?:src|scripts|api|r|tests|web/src)/[\w./\-]+\.(?:py|R|ts|tsx))</code>", link, html)


LIST_ITEM = re.compile(r"^(\s*)([*-]|\d+\.) ")


def _blank_before_lists(text: str) -> str:
    """METHODS.md skrivs för GitHub; Python-Markdown kräver en tom rad före en lista och fyra mellanslags indrag
    för nästlade listor. Punkter indragna 1–3 mellanslag (och deras fortsättningsrader) flyttas till fyra."""
    out, prev = [], ""
    shift, base = 0, None
    for line in text.split("\n"):
        indent = len(line) - len(line.lstrip(" "))
        item = LIST_ITEM.match(line)
        if item and 0 < indent < 4:
            shift, base = 4 - indent, indent
            line = " " * shift + line
        elif shift and line.strip() and indent > base:
            line = " " * shift + line
        else:
            shift, base = 0, None
        if item and indent == 0 and prev.strip() and not LIST_ITEM.match(prev) and not prev.startswith((" ", "\t", "|")):
            out.append("")
        out.append(line)
        prev = line
    return "\n".join(out)


DOCS = ("METHODS.md", "PROTOCOL.md")


@lru_cache(maxsize=4)
def _methods(mtimes: tuple) -> dict:
    import markdown
    from markdown.extensions.toc import slugify_unicode

    text = "\n\n".join(open(os.path.join(ROOT, d), encoding="utf-8").read() for d in DOCS)
    md = markdown.Markdown(extensions=["tables", "toc", "sane_lists"],
                           extension_configs={"toc": {"slugify": slugify_unicode, "toc_depth": "2-3"}})
    html = _link_sources(md.convert(_blank_before_lists(text)))

    def flat(tokens):
        for t in tokens:
            yield {"level": t["level"], "id": t["id"], "text": t["name"]}
            yield from flat(t["children"])
    return {"html": html, "toc": list(flat(md.toc_tokens)), "markdown": text}


@router.get("/methods")
def methods():
    """METHODS.md (alla metoder, beräkningar, valideringar och kända brister) och PROTOCOL.md (Vitki-protokollet)
    som HTML med innehållsförteckning."""
    out = dict(_methods(tuple(os.path.getmtime(os.path.join(ROOT, d)) for d in DOCS)))
    out["source"] = REPO + "METHODS.md"
    out["protocol_source"] = REPO + "PROTOCOL.md"
    out["limitations_version"] = limitations.VERSION
    return out


def _docstring(path: str) -> str:
    try:
        return ast.get_docstring(ast.parse(open(path, encoding="utf-8").read())) or ""
    except SyntaxError:
        return ""


def _r_header(path: str) -> str:
    lines = []
    for line in open(path, encoding="utf-8"):
        if not line.startswith("#"):
            break
        lines.append(line.lstrip("#").strip())
    return " ".join(x for x in lines if x)


@router.get("/code")
def code():
    """Analysmoduler, skript och R-moduler med sina egna beskrivningar (docstrings och sidhuvuden)."""
    def entries(pattern, describe, skip=()):
        out = []
        for path in sorted(glob.glob(os.path.join(ROOT, pattern))):
            name = os.path.relpath(path, ROOT)
            if any(re.search(s, os.path.basename(path)) for s in skip):
                continue
            text = describe(path)
            if text:
                out.append({"path": name, "url": REPO + name, "summary": text.strip().split("\n\n")[0].replace("\n", " "),
                            "text": text.strip()})
        return out

    return {
        "modules": entries("src/*.py", _docstring, skip=[r"^__init__"]),
        "scripts": entries("scripts/*.py", _docstring, skip=[r"^test_", r"^list_", r"^generate_test", r"^__init__"]),
        "r": entries("r/*.R", _r_header, skip=[r"^install\.R$"]),
    }
