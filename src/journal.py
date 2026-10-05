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
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from PIL import Image


def _text(t, anonymous: bool) -> str | None:
    if isinstance(t, dict):
        return t.get("anonymous") if anonymous else t.get("text")
    return t


FONT = "Linux Libertine O"   # the journal's typeface (Futhark template)


def _style(doc, name, base=None, size=None, italic=None, bold=None, align=None, indent=None, first=None,
           before=None, after=None, kind=WD_STYLE_TYPE.PARAGRAPH):
    st = doc.styles.add_style(name, kind)
    if base:
        st.base_style = doc.styles[base]
    f = st.font
    f.name = FONT
    rpr = st.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts"); rpr.append(fonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(a), FONT)
    if size:
        f.size = Pt(size)
    if italic is not None:
        f.italic = italic
    if bold is not None:
        f.bold = bold
    if kind == WD_STYLE_TYPE.PARAGRAPH:
        pf = st.paragraph_format
        if align:
            pf.alignment = align
        if indent is not None:
            pf.left_indent = Inches(indent)
        if first is not None:
            pf.first_line_indent = Inches(first)
        pf.space_before = Pt(before or 0)
        pf.space_after = Pt(after or 0)
    return st


def futhark_document() -> Document:
    """A document with the paragraph and character styles of the Futhark template (Linux Libertine O, 11 pt)."""
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(11)
    _style(doc, "F_paragraph", "Normal", align=WD_ALIGN_PARAGRAPH.JUSTIFY, first=0.1492)
    _style(doc, "F_header_1", "Normal", size=14, align=WD_ALIGN_PARAGRAPH.CENTER, after=12)
    _style(doc, "F_header_2", "Normal", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, before=12, after=6)
    _style(doc, "F_header_3", "Normal", size=11, italic=True, align=WD_ALIGN_PARAGRAPH.LEFT, before=6, after=3)
    _style(doc, "F_abstract", "Normal", size=10, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    _style(doc, "F_blockquote", "Normal", size=10, indent=0.1492, before=3, after=3)
    _style(doc, "F_list", "Normal", size=9)
    _style(doc, "F_bibliography", "Normal", indent=0.1492, first=-0.1492)
    _style(doc, "F_bold", bold=True, kind=WD_STYLE_TYPE.CHARACTER)
    _style(doc, "F_italics", italic=True, kind=WD_STYLE_TYPE.CHARACTER)
    return doc


def add_runs(par, text: str, size: float | None = None):
    """**runic transliteration** (character style F_bold) and *italics* (F_italics)."""
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not part:
            continue
        if part.startswith("**"):
            r = par.add_run(part[2:-2], style="F_bold")
        elif part.startswith("*"):
            r = par.add_run(part[1:-1], style="F_italics")
        else:
            r = par.add_run(part)
        if size:
            r.font.size = Pt(size)


def _first_refs(text: str, kind: str) -> list[int]:
    if kind == "fig":
        out = []
        for a, b in re.findall(r"Figs?\. (\d+)(?: and (\d+))?", text):
            out += [int(a)] + ([int(b)] if b else [])
        return out
    return [int(x) for x in re.findall(r"Table (\d+)", text)]


def _add_table(doc, headers, rows):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    for j, hd in enumerate(headers):
        c = t.rows[0].cells[j].paragraphs[0]; c.style = "F_abstract"; add_runs(c, hd)
    for r, row in enumerate(rows, 1):
        for j, v in enumerate(row):
            c = t.rows[r].cells[j].paragraphs[0]; c.style = "F_abstract"; add_runs(c, str(v))


def manuscript(spec: dict, anonymous: bool = False, figure_folder: str | None = None) -> Document:
    """Manuscript in the journal's template styles. With figure_folder: an illustrated reading version with figures
    and tables where they are first mentioned (not for submission)."""
    illustrated = figure_folder is not None
    placed_f, placed_t = set(), set()
    doc = futhark_document()
    title = spec["title"] + (f": {spec['subtitle']}" if spec.get("subtitle") else "")  # colon between title and subtitle
    doc.add_paragraph(title, style="F_header_1")
    if not anonymous:
        doc.add_paragraph(f"{spec['author']}, {spec['affiliation']}", style="F_paragraph")
    doc.add_paragraph("Abstract", style="F_header_2")
    add_runs(doc.add_paragraph(style="F_abstract"), _text(spec["abstract"], anonymous))
    if spec.get("keywords"):
        add_runs(doc.add_paragraph(style="F_abstract"), f"*Keywords:* {spec['keywords']}")
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    for kind, t in spec["body"]:
        text = _text(t, anonymous)
        if text is None:
            continue
        if kind == "h1":
            doc.add_paragraph(text, style="F_header_2")
        elif kind == "h2":
            doc.add_paragraph(text, style="F_header_3")
        elif kind == "quote":
            add_runs(doc.add_paragraph(style="F_blockquote"), text)
        else:
            add_runs(doc.add_paragraph(style="F_paragraph"), text)
        if illustrated and kind == "p":
            for k in _first_refs(text, "fig"):
                if k in placed_f or k > len(spec["figures"]):
                    continue
                placed_f.add(k)
                img = os.path.join(figure_folder, f"Fig{k:02d}.png")
                doc.add_picture(img, width=Inches(6.0))
                add_runs(doc.add_paragraph(style="F_abstract"), f"Fig. {k}. {spec['figures'][k - 1][1]}")
            for k in _first_refs(text, "table"):
                if k in placed_t or k > len(spec["tables"]):
                    continue
                placed_t.add(k)
                cap, headers, rows = spec["tables"][k - 1]
                add_runs(doc.add_paragraph(style="F_abstract"), f"Table {k}. {cap}")
                _add_table(doc, headers, rows)
    doc.add_paragraph("Bibliography", style="F_header_2")
    for b in spec["bibliography"]:
        add_runs(doc.add_paragraph(style="F_bibliography"), b)
    if illustrated:
        return doc
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    doc.add_paragraph("Captions", style="F_header_2")
    for i, (_, cap) in enumerate(spec["figures"], 1):
        add_runs(doc.add_paragraph(style="F_paragraph"), f"Fig. {i}. {cap}")
    for i, (cap, _, _) in enumerate(spec["tables"], 1):
        add_runs(doc.add_paragraph(style="F_paragraph"), f"Table {i}. {cap}")
    return doc


def write_tables(spec: dict, folder: str):
    os.makedirs(folder, exist_ok=True)
    for i, (_, headers, rows) in enumerate(spec["tables"], 1):
        doc = futhark_document()
        doc.add_paragraph(f"Table {i}", style="F_paragraph")
        _add_table(doc, headers, rows)
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
                    body.append(f"![Fig. {k}](figures/Fig{k:02d}.png)\n\n*Fig. {k}. {spec['figures'][k - 1][1]}*")
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
    # Only the package's own files are replaced; anything else in the folder (e.g. the author's copies) is left alone
    os.makedirs(folder, exist_ok=True)
    for sub in ("figures", "tables", "preview"):
        if os.path.isdir(os.path.join(folder, sub)):
            shutil.rmtree(os.path.join(folder, sub))
    write_figures(spec, os.path.join(folder, "figures"))
    write_tables(spec, os.path.join(folder, "tables"))
    manuscript(spec, False).save(os.path.join(folder, f"{basename}_manuscript.docx"))
    manuscript(spec, True).save(os.path.join(folder, f"{basename}_manuscript_anonymised.docx"))
    pv = os.path.join(folder, "preview", "figures")
    os.makedirs(pv, exist_ok=True)
    for k in range(1, len(spec["figures"]) + 1):  # PNG copies for the reading versions
        im = Image.open(os.path.join(folder, "figures", f"Fig{k:02d}.tif")).convert("RGB")
        im.thumbnail((2400, 2400))
        im.save(os.path.join(pv, f"Fig{k:02d}.png"))
    # Reading version with figures and tables in place (not for submission: the journal wants them as separate files)
    manuscript(spec, False, pv).save(os.path.join(folder, f"{basename}_illustrated_reading_version.docx"))
    preview_markdown(spec, os.path.join(folder, "preview", f"{basename}_preview.md"), pv)
    if spec.get("readme"):
        with open(os.path.join(folder, "README.txt"), "w", encoding="utf-8") as fh:
            fh.write(spec["readme"])
    return check(spec)
