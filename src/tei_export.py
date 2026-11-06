"""Utgåva i TEI/EpiDoc med ett 3D-ankare per runa (Runa för runa, src/rune_links.py).

Ur ett facit av version 2 (eller granskningens kopplingar i exportmenyn) och Rundatas post blir det en XML-fil per
sten, tänkt för digitala utgåvor som EVT (Edition Visualization Technology):

* **teiHeader**: titel, signum, Rundata som källa med version och licens (ODbL), skanningens kreditering när filen
  känns igen som en öppen skanning (src/scan_sources.py), och vem som kopplade runorna (responsibility).
* **facsimile**: två ytor. Granskningsbilden (pixlar, med en zon kring varje klick, så att en bildvisare kan länka bild
  och text) och 3D-modellen (skanningsfilens namn och SHA-256), med en zon per länkad runa. TEI:s koordinater
  (@points, @ulx …) är tvådimensionella, så 3D-punkten, normalen och kameravyn ligger i teiHeader/xenoData som
  element i Vitkis namnrymd (ANKARE_NS), och 3D-zonen pekar dit med @ana. Valet står också i filens editorialDecl.
* **text/body/div[@type='edition']**: translittereringen med ett element per tecken och xml:id på varje: runor som
  `<c>`, osäkra runor i `<unclear>`, runor kända ur äldre dokumentation i `<supplied reason="lost"
  evidence="previouseditor">`, förlorade runor som `<gap reason="lost" quantity="1" unit="character"/>` (oläsliga
  '?' med reason="illegible"), luckor av okänd längd som `<gap extent="unknown">`, skiljetecken som
  `<g type="divider">` och ord som `<w>`. En länkad runa har @facs mot sina zoner; en bindruna (två runor, ett klick)
  pekar på samma zoner och har rend="ligature".

Filen kontrolleras innan den lämnas ut (`check`): välformad, unika xml:id och att varje @facs och @ana pekar på
något som finns. Mot TEI-schemat valideras den inte här (schemat finns inte lokalt); se tests/test_rune_links.py.

    .venv/bin/python -m src.tei_export utdata/facit/Sö_134_facit.json --out utdata/facit/tei
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

import numpy as np

from src import rune_links

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ANKARE_NS = "https://vitkirunor.se/ns/ankare/1"
EPIDOC_RNG = "https://epidoc.stoa.org/schema/latest/tei-epidoc.rng"
RUNDATA_URL = "http://www.runforum.nordiska.uu.se/filer/srd2014.zip"
ODBL_URL = "https://opendatacommons.org/licenses/odbl/1-0/"
MIME = {".stl": "model/stl", ".obj": "model/obj", ".ply": "application/ply"}
ET.register_namespace("", TEI_NS)
ET.register_namespace("vitki", ANKARE_NS)

ENCODING_NOTE = (
    "3D-ankarna: TEI:s koordinatattribut (@points, @ulx, @uly, @lrx, @lry) är tvådimensionella. Zonerna på ytan "
    "'granskningsbild' är därför pixlar i Vitkis granskningsbild (origo uppe till vänster), en kvadrat kring klicket "
    "med halva medelavståndet till grannrunan åt varje håll; de visar var runan är, inte dess kontur. Zonerna på ytan "
    "'modell-3d' har inga koordinater utan pekar med @ana på ett vitki:ankare i teiHeader/xenoData (namnrymden "
    f"{ANKARE_NS}): punkten i mm i 3D-modellen centrerad på sin omslutande lådas mitt (som i Vitki), samma punkt i "
    "skanningsfilens egna koordinater (punkten + centered_by), ytans normal och en kameravy (position, mål och uppåt) "
    "som ser rakt på den ristade ytan. Punkten ligger på stenytan: den högsta punkten i modellen inom 1 mm i stenytans "
    "plan (height_from='modellen'), eller uppskattad ur de närmaste snitten (height_from='snitten'). Varje klick gäller "
    "en runa, eller två när forskaren angett en bindruna; runor som inte syns och hoppats över har ingen @facs.")
EDITION_NOTE = (
    "Translittereringen följer Rundata tecken för tecken. Runor är <c>; inom parentes i Rundata (osäker läsning) "
    "<unclear>; inom hakparentes (kända ur äldre dokumentation) <supplied reason='lost' evidence='previouseditor'>; "
    "'-' (förlorad runa) <gap reason='lost' quantity='1' unit='character'/>; '?' (runa som syns men inte kan läsas) "
    "<gap reason='illegible' quantity='1' unit='character'/>; '...' <gap reason='lost' extent='unknown'/>; "
    "skiljetecken <g type='divider'>; Rundatas ord (mellanslag och skiljetecken) <w>; bindrunor (^) rend='ligature'; "
    "radbyte (¶) <lb/>; runor inom < > type='uninterpreted'; latinska bokstäver och tecken inom { } type='other'. "
    "Varje tecken har xml:id t + tokenindex (src/rune_links.tokenize). Rundatas alternativa läsningar (§…Q) är inte med.")


def _q(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


def _sub(parent, tag: str, text: str | None = None, **attrs) -> ET.Element:
    el = ET.SubElement(parent, _q(tag) if not tag.startswith("{") else tag)
    for k, v in attrs.items():
        if v is None:
            continue
        key = f"{{{XML_NS}}}{k[4:]}" if k.startswith("xml_") else k
        el.set(key, str(v))
    if text is not None:
        el.text = text
    return el


def _version() -> str:
    try:
        from api.config import APP_VERSION
        return APP_VERSION
    except Exception:  # noqa: BLE001 - outside the app the module's own version is enough
        from src.groove_export import APP_VERSION
        return APP_VERSION


def _fmt(v: float, d: int = 3) -> str:
    return f"{float(v):.{d}f}"


def _xyz(el: ET.Element, p) -> ET.Element:
    el.set("x", _fmt(p[0]))
    el.set("y", _fmt(p[1]))
    el.set("z", _fmt(p[2]))
    return el


def _zone_half_px(links: list[dict]) -> float:
    pts = [ln["image_xy"] for ln in links if ln.get("image_xy")]
    gaps = [float(np.hypot(b[0] - a[0], b[1] - a[1])) for a, b in zip(pts, pts[1:], strict=False)]
    return max(8.0, 0.5 * float(np.median(gaps))) if gaps else 12.0


def build(edition: dict, record: dict | None = None, credit: dict | None = None,
          now: datetime.datetime | None = None) -> bytes:
    """The TEI/EpiDoc file (UTF-8 bytes) for an edition: a facit of version 2 or the review's links, as
    rune_links.read_facit gives them, with point_mm and normal_or_view per link (rune_links.anchors)."""
    now = now or datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    signum = (record or {}).get("signum") or edition.get("signum") or "okänd sten"
    tr = edition.get("transliteration") or {}
    text = tr.get("text") if isinstance(tr, dict) else None
    tokens = edition.get("tokens") or (rune_links.tokenize(text) if text else [])
    if not tokens:
        raise ValueError("Utgåvan saknar translitterering.")
    links = [ln for ln in edition.get("rune_links") or [] if ln.get("tokens")]
    mesh = edition.get("mesh") or {}
    labeller = (edition.get("labeller") or "").strip() or "okänd"
    centred_by = mesh.get("centered_by")

    tei = ET.Element(_q("TEI"))
    tei.set(f"{{{XML_NS}}}lang", "sv")
    header = _sub(tei, "teiHeader")
    fd = _sub(header, "fileDesc")
    ts = _sub(fd, "titleStmt")
    _sub(ts, "title", f"{signum} – utgåva med 3D-ankare per runa")
    rs = _sub(ts, "respStmt")
    _sub(rs, "resp", "kopplade varje runa i translittereringen till 3D-modellen, ett klick per runa")
    _sub(rs, "persName", labeller, xml_id="kopplare")
    rs2 = _sub(ts, "respStmt")
    _sub(rs2, "resp", "XML-filen genererad av")
    _sub(rs2, "name", f"Vitki {_version()} (https://vitkirunor.se, src/tei_export.py)")
    ps = _sub(fd, "publicationStmt")
    _sub(ps, "authority", "Vitki")
    _sub(ps, "date", now.date().isoformat(), when=now.date().isoformat())
    av = _sub(ps, "availability")
    _sub(av, "licence", "Translittereringen kommer ur Samnordisk runtextdatabas och omfattas av Open Database "
         "License (ODbL 1.0); uppgifterna i den av Database Contents License (DbCL 1.0). 3D-skanningen har sin egen "
         "licens, se källorna.", target=ODBL_URL)
    sd = _sub(fd, "sourceDesc")
    ms = _sub(sd, "msDesc")
    mi = _sub(ms, "msIdentifier")
    place = ", ".join(x for x in ((record or {}).get("place"), (record or {}).get("parish")) if x)
    if place:
        _sub(mi, "settlement", place)
    _sub(mi, "idno", signum, type="signum")
    if (record or {}).get("material") or (record or {}).get("object"):
        pd = _sub(ms, "physDesc")
        od = _sub(pd, "objectDesc", form=(record or {}).get("object") or None)
        sup = _sub(_sub(od, "supportDesc"), "support")
        if (record or {}).get("material"):
            _sub(sup, "material", record["material"])
    if (record or {}).get("dating"):
        _sub(_sub(_sub(ms, "history"), "origin"), "origDate", f"Rundatas datering: {record['dating']}")
    lb = _sub(sd, "listBibl")
    src = tr.get("source") if isinstance(tr, dict) else {}
    b = _sub(lb, "bibl", type="translitteration")
    _sub(b, "title", (src or {}).get("database") or "Samnordisk runtextdatabas")
    _sub(b, "edition", (src or {}).get("version") or rune_links.RUNDATA_VERSION)
    _sub(b, "publisher", (src or {}).get("publisher") or "Institutionen för nordiska språk, Uppsala universitet")
    _sub(b, "idno", (src or {}).get("signum") or signum, type="signum")
    _sub(b, "ptr", target=RUNDATA_URL)
    _sub(b, "note", f"Licens: {(src or {}).get('licence') or rune_links.RUNDATA_LICENCE} ({ODBL_URL}).", type="licens")
    if text:
        _sub(b, "note", text, type="translitteration")
    ds = (credit or {}).get("dataset") if (credit or {}).get("known") else None
    bs = _sub(lb, "bibl", type="skanning")
    if ds:
        _sub(bs, "author", ds.get("scanned_by") or ds.get("creator"))
        if ds.get("institution"):
            _sub(bs, "orgName", ds["institution"])
        _sub(bs, "title", ds.get("citation"))
        _sub(bs, "idno", ds.get("doi"), type="DOI")
        _sub(bs, "ptr", target=ds.get("url"))
        _sub(bs, "note", f"Licens: {ds.get('license')}" + (f" ({ds['license_url']})" if ds.get("license_url") else ""),
             type="licens")
        _sub(bs, "note", (credit or {}).get("credit_text"), type="kreditering")
    else:
        note = ((credit or {}).get("scan_note") or "").strip()
        _sub(bs, "note", ("Skanningen enligt den som exporterade: " + note) if note else
             "Vitki känner inte igen skanningsfilen som en öppen skanning; vem som skannat stenen är inte angivet.",
             type="kreditering")
    if mesh.get("sha256"):
        _sub(bs, "idno", mesh["sha256"], type="SHA-256")
    if mesh.get("filename"):
        _sub(bs, "note", f"Skanningsfil: {mesh['filename']}", type="fil")

    ed = _sub(header, "encodingDesc")
    _sub(_sub(ed, "projectDesc"), "p", "Runorna är kopplade till 3D-skanningen i Vitkis granskning av den automatiska "
         "spåranalysen (Runa för runa): ett klick mitt på varje runa, i läsordning, kopplat till nästa runa i "
         "translittereringen. METHODS.md, avsnitt 2c.")
    edl = _sub(ed, "editorialDecl")
    _sub(edl, "p", EDITION_NOTE)
    _sub(edl, "p", ENCODING_NOTE)
    pr = _sub(header, "profileDesc")
    _sub(_sub(pr, "langUsage"), "language", "fornnordiska (runsvenska), translittererad med latinska bokstäver",
         ident="non-Latn")

    # 3D anchors in Vitki's namespace
    xd = _sub(header, "xenoData")
    root = ET.SubElement(xd, f"{{{ANKARE_NS}}}ankare")
    root.set("koordinater", rune_links.COORDS)
    if mesh.get("sha256"):
        root.set("skanning-sha256", mesh["sha256"])
    if centred_by:
        root.set("centered_by", " ".join(_fmt(v) for v in centred_by))
    anchor_ids: dict[int, str] = {}
    for k, ln in enumerate(links):
        m = int(ln.get("mark", k))
        p = ln.get("point_mm")
        if p is None:
            continue
        aid = f"ankare-m{m + 1}"
        anchor_ids[m] = aid
        a = ET.SubElement(root, f"{{{ANKARE_NS}}}punkt")
        a.set(f"{{{XML_NS}}}id", aid)
        a.set("markering", str(m + 1))
        a.set("token", " ".join(f"t{t}" for t in ln["tokens"]))
        a.set("height_from", str(ln.get("height_from") or ""))
        _xyz(ET.SubElement(a, f"{{{ANKARE_NS}}}mm"), p)
        if centred_by:
            _xyz(ET.SubElement(a, f"{{{ANKARE_NS}}}mm_i_filen"), [p[i] + centred_by[i] for i in range(3)])
        nv = ln.get("normal_or_view") or {}
        if nv.get("normal"):
            _xyz(ET.SubElement(a, f"{{{ANKARE_NS}}}normal"), nv["normal"])
        view = nv.get("view")
        if view:
            v = ET.SubElement(a, f"{{{ANKARE_NS}}}vy")
            for key in ("position", "target", "up"):
                _xyz(ET.SubElement(v, f"{{{ANKARE_NS}}}{key}"), view[key])
    rev = _sub(header, "revisionDesc")
    created = edition.get("created")
    when = created[:10] if isinstance(created, str) and re.match(r"\d{4}-\d{2}-\d{2}", created) else now.date().isoformat()
    _sub(rev, "change", f"{len(links)} klick kopplade till {sum(len(ln['tokens']) for ln in links)} runor; "
         f"{len(edition.get('skipped_tokens') or [])} runor överhoppade (syns inte).", when=when, who="#kopplare")

    # facsimile: the review image (pixels) and the 3D model
    fac = _sub(tei, "facsimile")
    W, H = edition.get("image_width"), edition.get("image_height")
    zones2d: dict[int, str] = {}
    if W and H:
        surf = _sub(fac, "surface", xml_id="granskningsbild", ulx=0, uly=0, lrx=int(W), lry=int(H))
        _sub(surf, "graphic", url=quote(f"{_slug(signum)}_granskningsbild.png"), width=f"{int(W)}px",
             height=f"{int(H)}px", mimeType="image/png")
        half = _zone_half_px(links)
        for k, ln in enumerate(links):
            if not ln.get("image_xy"):
                continue
            m = int(ln.get("mark", k))
            x, y = ln["image_xy"]
            zid = f"zon-bild-m{m + 1}"
            zones2d[m] = zid
            _sub(surf, "zone", xml_id=zid, ulx=_fmt(max(0.0, x - half), 1), uly=_fmt(max(0.0, y - half), 1),
                 lrx=_fmt(min(float(W), x + half), 1), lry=_fmt(min(float(H), y + half), 1), n=m + 1)
    surf3 = _sub(fac, "surface", xml_id="modell-3d", type="3d-modell")
    ext = os.path.splitext(mesh.get("filename") or "")[1].lower()
    g = _sub(surf3, "graphic", url=quote(mesh.get("filename") or "skanning"), mimeType=MIME.get(ext))
    _sub(g, "desc", f"3D-skanningen{(' ' + mesh['filename']) if mesh.get('filename') else ''}"
         + (f", SHA-256 {mesh['sha256']}" if mesh.get("sha256") else "") + f". Koordinater: {rune_links.COORDS}.")
    zones3d: dict[int, str] = {}
    for m, aid in anchor_ids.items():
        zid = f"zon-3d-m{m + 1}"
        zones3d[m] = zid
        _sub(surf3, "zone", xml_id=zid, ana=f"#{aid}", n=m + 1)

    # the edition
    facs_of: dict[int, str] = {}
    lig: set[int] = set()
    for k, ln in enumerate(links):
        m = int(ln.get("mark", k))
        targets = " ".join(f"#{z}" for z in (zones2d.get(m), zones3d.get(m)) if z)
        for t in ln["tokens"]:
            if targets:
                facs_of[int(t)] = targets
        if len(ln["tokens"]) == 2:
            lig.update(int(t) for t in ln["tokens"])
    for t in tokens:
        if t.get("bind_next"):
            nxt = next((u for u in tokens if u["i"] > t["i"] and u["kind"] in rune_links.LINKABLE), None)
            lig.add(t["i"])
            if nxt:
                lig.add(nxt["i"])
    body = _sub(_sub(tei, "text"), "body")
    edition_div = _sub(body, "div", type="edition", xml_lang="non-Latn")
    sections = []
    for t in tokens:
        if not sections or sections[-1][0] != t["section"]:
            sections.append((t["section"], []))
        sections[-1][1].append(t)
    for sec, toks in sections:
        parent = edition_div
        if len(sections) > 1:
            parent = _sub(edition_div, "div", type="textpart", n=sec)
        ab = _sub(parent, "ab")
        _fill_ab(ab, toks, facs_of, lig)

    ET.indent(tei, space=" ")
    for w in tei.iter(_q("w")):  # a word's characters without whitespace between them
        _tighten(w)
    xml = ET.tostring(tei, encoding="unicode")
    head = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<?xml-model href="{EPIDOC_RNG}" schematypens="http://relaxng.org/ns/structure/1.0"?>\n')
    return (head + xml + "\n").encode("utf-8")


def _tighten(el: ET.Element) -> None:
    if len(el):
        el.text = None if (el.text or "").strip() == "" else el.text
    for ch in el:
        ch.tail = None if (ch.tail or "").strip() == "" else ch.tail
        _tighten(ch)


def _slug(signum: str) -> str:
    from src.groove_export import slug
    return slug(signum)


def _fill_ab(ab: ET.Element, toks: list[dict], facs_of: dict[int, str], lig: set[int]) -> None:
    """Words as <w>, dividers as <g type='divider'>, each token with xml:id; runs of older/uncertain runes wrapped."""
    cur_word, w = None, None
    stack: list[tuple[str, ET.Element]] = []  # open wrappers inside the word: ('supplied'|'unclear', element)
    for t in toks:
        if t["kind"] == "divider":
            cur_word, w, stack = None, None, []
            if t.get("line_break"):
                _sub(ab, "lb")
            _sub(ab, "g", t["char"], type="divider", xml_id=f"t{t['i']}")
            continue
        if t["word"] != cur_word or w is None:
            cur_word, stack = t["word"], []
            w = _sub(ab, "w")
        want = (["supplied"] if t.get("older") else []) + (["unclear"] if t["kind"] == "uncertain" else [])
        while stack and [s for s, _ in stack] != want[:len(stack)]:
            stack.pop()
        parent = stack[-1][1] if stack else w
        for kind in want[len(stack):]:
            el = (_sub(parent, "supplied", reason="lost", evidence="previouseditor") if kind == "supplied"
                  else _sub(parent, "unclear"))
            stack.append((kind, el))
            parent = el
        if t.get("line_break"):
            _sub(parent, "lb", **({"break": "no"} if len(w) or (w.text or "") else {}))
        tid = f"t{t['i']}"
        facs = facs_of.get(t["i"])
        if t["kind"] == "lost":
            _sub(parent, "gap", reason=t.get("reason") or "lost", quantity=1, unit="character", xml_id=tid, facs=facs)
        elif t["kind"] == "gap":
            _sub(parent, "gap", reason="lost", extent="unknown", unit="character", xml_id=tid)
        elif t["kind"] == "other":
            _sub(parent, "c", t["orig"], type="other", xml_id=tid)
        else:
            _sub(parent, "c", t["char"], xml_id=tid, facs=facs, rend="ligature" if t["i"] in lig else None,
                 type="uninterpreted" if t.get("uninterpreted") else None)


def check(xml: bytes) -> list[str]:
    """Problems with the file: not well-formed, duplicate xml:id, or an @facs/@ana/@who that points nowhere."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        return [f"inte välformad XML: {e}"]
    ids: dict[str, int] = {}
    for el in root.iter():
        i = el.get(f"{{{XML_NS}}}id")
        if i:
            ids[i] = ids.get(i, 0) + 1
    out = [f"xml:id {i} förekommer {n} gånger" for i, n in ids.items() if n > 1]
    for el in root.iter():
        for att in ("facs", "ana", "who"):
            for ref in (el.get(att) or "").split():
                if ref.startswith("#") and ref[1:] not in ids:
                    out.append(f"@{att}={ref} pekar inte på något element")
    if root.find(f".//{_q('div')}[@type='edition']") is None:
        out.append("div[@type='edition'] saknas")
    return out


def edition_from_facit(facit: dict) -> dict:
    """A facit of version 2 (rune_links.read_facit) as an edition for build."""
    f = rune_links.read_facit(facit)
    if f["version"] < 2 or not f["rune_links"]:
        raise ValueError("Facitet har inga runor kopplade till translittereringen (version 2 behövs).")
    return f


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("facit", nargs="+", help="facitfiler av version 2")
    ap.add_argument("--out", required=True, help="mapp för XML-filerna")
    a = ap.parse_args(argv)
    from api.rundata import store
    from src.groove_export import credit_for_mesh, slug
    os.makedirs(a.out, exist_ok=True)
    for path in a.facit:
        ed = edition_from_facit(json.load(open(path, encoding="utf-8")))
        rec = store().get(ed.get("signum") or "")
        xml = build(ed, rec, credit_for_mesh(ed.get("mesh")))
        problems = check(xml)
        if problems:
            raise SystemExit(f"{path}: " + "; ".join(problems))
        out = os.path.join(a.out, f"{slug(ed.get('signum') or 'sten')}_utgava_tei.xml")
        open(out, "wb").write(xml)
        print(out)


if __name__ == "__main__":
    main()
