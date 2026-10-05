"""Inlämningspaket för tidskriftsartiklar (byggt för Futhark: International Journal of Runic Studies).

En artikel beskrivs som en specifikation (dict) och skrivs ut enligt tidskriftens riktlinjer:

  * manus i Word med titel, abstract och nyckelord på egen första sida, onumrerade rubriker i två nivåer,
    litteraturlista och figur- och tabelltexter på egen sista sida;
  * en anonymiserad version för granskning;
  * figurer som separata TIFF-filer (300–600 dpi, utan text i bilden) och tabeller som separata Word-filer;
  * en förhandsversion i Markdown med figurer och tabeller på plats, för läsning;
  * kontroller: varje verk i litteraturlistan citeras, varje figur och tabell hänvisas till i texten.

Markering i texten: **fetstil** (bara runisk translitterering, enligt Futharks stilmall) och *kursiv*
(normalisering, metaspråkliga ord, titlar). Specifikationen:

  {"title", "subtitle", "author", "affiliation", "abstract", "keywords",
   "body": [(kind, text)],   kind: h1 | h2 | p | quote; text kan vara {"text": …, "anonymous": …}
   "figures": [(källfil, bildtext)], "tables": [(bildtext, rubriker, rader)],
   "bibliography": [post], "citations": {etikett: söksträng i texten}, "readme": text}
"""
from __future__ import annotations

import os
import re
import shutil

from docx import Document
from docx.enum.text import WD_BREAK
from docx.shared import Pt
from PIL import Image


def _text(t, anonymous: bool) -> str | None:
    if isinstance(t, dict):
        return t.get("anonymous") if anonymous else t.get("text")
    return t


def add_runs(par, text: str, size: float | None = None):
    """**fetstil** och *kursiv* i ett Word-stycke."""
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not part:
            continue
        if part.startswith("**"):
            r = par.add_run(part[2:-2]); r.bold = True
        elif part.startswith("*"):
            r = par.add_run(part[1:-1]); r.italic = True
        else:
            r = par.add_run(part)
        if size:
            r.font.size = Pt(size)


def manuscript(spec: dict, anonymous: bool = False) -> Document:
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(12)
    doc.add_heading(spec["title"], 0)
    if spec.get("subtitle"):
        doc.add_paragraph(spec["subtitle"])
    if not anonymous:
        doc.add_paragraph(f"{spec['author']}\n{spec['affiliation']}")
    doc.add_heading("Abstract", 1)
    add_runs(doc.add_paragraph(), _text(spec["abstract"], anonymous))
    if spec.get("keywords"):
        add_runs(doc.add_paragraph(), f"*Keywords:* {spec['keywords']}")
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    for kind, t in spec["body"]:
        text = _text(t, anonymous)
        if text is None:
            continue
        if kind in ("h1", "h2"):
            doc.add_heading(text, 1 if kind == "h1" else 2)
        elif kind == "quote":
            add_runs(doc.add_paragraph(style="Quote"), text)
        else:
            add_runs(doc.add_paragraph(), text)
    doc.add_heading("Bibliography", 1)
    for b in spec["bibliography"]:
        add_runs(doc.add_paragraph(), b)
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    doc.add_heading("Captions", 1)
    for i, (_, cap) in enumerate(spec["figures"], 1):
        add_runs(doc.add_paragraph(), f"Fig. {i}. {cap}")
    for i, (cap, _, _) in enumerate(spec["tables"], 1):
        add_runs(doc.add_paragraph(), f"Table {i}. {cap}")
    return doc


def write_tables(spec: dict, folder: str):
    os.makedirs(folder, exist_ok=True)
    for i, (_, headers, rows) in enumerate(spec["tables"], 1):
        doc = Document()
        doc.add_paragraph(f"Table {i}")
        t = doc.add_table(rows=1 + len(rows), cols=len(headers))
        t.style = "Table Grid"
        for j, hd in enumerate(headers):
            add_runs(t.rows[0].cells[j].paragraphs[0], hd)
        for r, row in enumerate(rows, 1):
            for j, v in enumerate(row):
                add_runs(t.rows[r].cells[j].paragraphs[0], str(v))
        doc.save(os.path.join(folder, f"Table{i:02d}.docx"))


def write_figures(spec: dict, folder: str, dpi: int = 300):
    """En TIFF per figur. TIFF-källor (t.ex. R-figurer i 600 dpi) kopieras; andra bilder sparas som TIFF."""
    os.makedirs(folder, exist_ok=True)
    for i, (src, _) in enumerate(spec["figures"], 1):
        dst = os.path.join(folder, f"Fig{i:02d}.tif")
        if src.lower().endswith((".tif", ".tiff")):
            shutil.copy(src, dst)
        else:
            Image.open(src).convert("RGB").save(dst, dpi=(dpi, dpi), compression="tiff_lzw")


def preview_markdown(spec: dict, path: str, figure_folder: str):
    """Läsversion: figurer och tabeller vid första hänvisningen."""
    body = []
    placed_f, placed_t = set(), set()
    for kind, t in spec["body"]:
        text = _text(t, False)
        if text is None:
            continue
        body.append({"h1": f"## {text}", "h2": f"### {text}", "quote": f"> {text}"}.get(kind, text))
        for n in re.findall(r"Figs?\. (\d+)(?: and (\d+))?", text):
            for k in (x for x in n if x):
                k = int(k)
                if k not in placed_f and k <= len(spec["figures"]):
                    placed_f.add(k)
                    preview = os.path.join(figure_folder, f"Fig{k:02d}.png")
                    body.append(f"![Fig. {k}](figures/Fig{k:02d}.png)\n\n*Fig. {k}. {spec['figures'][k - 1][1]}*")
                    Image.open(os.path.join(figure_folder, f"Fig{k:02d}.tif")).convert("RGB").save(preview)
        for k in (int(x) for x in re.findall(r"Table (\d+)", text)):
            if k not in placed_t and k <= len(spec["tables"]):
                placed_t.add(k)
                cap, headers, rows = spec["tables"][k - 1]
                md = "| " + " | ".join(headers) + " |\n|" + "---|" * len(headers) + "\n"
                md += "\n".join("| " + " | ".join(str(c) for c in r) + " |" for r in rows)
                body.append(f"{md}\n\n*Table {k}. {cap}*")
    out = [f"# {spec['title']}", f"*{spec.get('subtitle', '')}*", f"{spec['author']}, {spec['affiliation']}",
           "## Abstract", _text(spec["abstract"], False), f"*Keywords:* {spec.get('keywords', '')}"] + body
    out += ["## Bibliography"] + spec["bibliography"]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(out) + "\n")


def check(spec: dict) -> dict:
    """Kontroller enligt riktlinjerna: citeringar, hänvisningar till figurer och tabeller, numrerade rubriker."""
    text = " ".join(filter(None, [_text(spec["abstract"], False)] + [_text(t, False) for _, t in spec["body"]]))
    uncited = [k for k, needle in spec.get("citations", {}).items() if needle not in text]
    figs = set()
    for a, b in re.findall(r"Figs?\. (\d+)(?: and (\d+))?", text):
        figs |= {int(a)} | ({int(b)} if b else set())
    tabs = {int(x) for x in re.findall(r"Table (\d+)", text)}
    numbered = [t for k, t in spec["body"] if k in ("h1", "h2") and re.match(r"^\d", _text(t, False) or "")]
    bold_outside = []  # bold should only mark runic transliteration: lower-case runic letters, no spaces between words
    for m in re.findall(r"\*\*([^*]+)\*\*", text):
        if re.search(r"[A-Z]{2,}|\d", m.replace("R", "")):
            bold_outside.append(m)
    return {"uncited": uncited,
            "figures_not_referred": sorted(set(range(1, len(spec["figures"]) + 1)) - figs),
            "tables_not_referred": sorted(set(range(1, len(spec["tables"]) + 1)) - tabs),
            "numbered_headings": numbered, "suspicious_bold": bold_outside,
            "words": len(text.split())}


def build(spec: dict, folder: str, basename: str) -> dict:
    """Skriver hela paketet till mappen och returnerar kontrollerna."""
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    write_figures(spec, os.path.join(folder, "figures"))
    write_tables(spec, os.path.join(folder, "tables"))
    manuscript(spec, False).save(os.path.join(folder, f"{basename}_manuscript.docx"))
    manuscript(spec, True).save(os.path.join(folder, f"{basename}_manuscript_anonymised.docx"))
    os.makedirs(os.path.join(folder, "preview", "figures"), exist_ok=True)
    preview_markdown(spec, os.path.join(folder, "preview", f"{basename}_preview.md"), os.path.join(folder, "figures"))
    for k in range(1, len(spec["figures"]) + 1):
        src = os.path.join(folder, "figures", f"Fig{k:02d}.png")
        if os.path.exists(src):
            shutil.move(src, os.path.join(folder, "preview", "figures", f"Fig{k:02d}.png"))
    if spec.get("readme"):
        with open(os.path.join(folder, "README.txt"), "w", encoding="utf-8") as fh:
            fh.write(spec["readme"])
    return check(spec)
