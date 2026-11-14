"""Korpus i InDesign – ett sidospår (Viktor 2026-11-14: hans bror, formgivare, ska kunna ta över layouten om det blir så;
Korpus byggs tills vidare som förut med bygg_tidskrift.py). Skriver, UTANFÖR repot eftersom bilderna har andra
upphovspersoner (källregeln, METHODS §17):

  /Volumes/2TB/Antigrvity/Runes/korpus_indesign/
    LASMIG.md                     för formgivaren: vad som finns och hur det används
    mall/Korpus_mall.jsx          InDesign-skript: bygger ett dokument med format, färger, stycke- och teckenformat,
                                  baslinjerutnät och mallsidor ur korpus.css (sparas sedan som .indt)
    nr1/sidplan.pdf               de 20 sidorna som miniatyrer med vad som står på varje
    nr1/referens/                 de färdiga PDF:erna (sv, sv tryck, en)
    nr1/sidor/                    varje sida som bild (150 dpi) och som ren text
    nr1/texter/                   en fil per text i InDesign-taggad text (stilarna följer med) + samma text i Markdown
    nr1/bilder/                   bilderna i originalupplösning + KREDITER.md (fotograf, licens, källa)
    nr1/grafik/                   kartan (320 dpi), skärmbilderna, Vitkis bindruna (SVG) och diagrammens data

Stilnamnen står på ett ställe (STYCKEN, TECKEN nedan) och används både i skriptet och i de taggade texterna.
    ../../../.venv/bin/python bygg_indesign.py [--utan-bilder]
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
from urllib.parse import unquote

HERE = os.path.dirname(os.path.abspath(__file__))
TID = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(TID, "..", ".."))
sys.path.insert(0, TID)
import bygg_tidskrift as B  # noqa: E402

UT = "/Volumes/2TB/Antigrvity/Runes/korpus_indesign"
NR1 = os.path.join(UT, "nr1")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
UA = "Vitki-Korpus-materialpaket/1.0 (https://vitkirunor.se)"

# ---- designen ur korpus.css / korpus_tryck.css ----------------------------------------------------------------------------
FARGER = [  # namn, RGB (korpus.css :root)
    ("Bläck", (29, 34, 38)), ("Dämpad", (95, 106, 115)), ("Linje", (216, 220, 223)), ("Rost", (183, 65, 14)),
    ("Rost mörk", (143, 50, 9)), ("Rost ljus", (248, 236, 228)), ("Sten", (241, 242, 240)), ("Rost blek", (255, 217, 198)),
]
SERIF, SANS = "Charter", "Avenir Next"
# namn: typsnitt, stil, grad (pt), radavstånd (pt), färg, och övrigt (InDesign-egenskaper i skriptet)
STYCKEN = [
    ("Brödtext", SERIF, "Roman", 9.4, 13.5, "Bläck", dict(just="LEFT_JUSTIFIED", grid=True, indent=3.5)),
    ("Brödtext första", SERIF, "Roman", 9.4, 13.5, "Bläck", dict(base="Brödtext", indent=0, drop=3)),
    ("Brödtext utan indrag", SERIF, "Roman", 9.4, 13.5, "Bläck", dict(base="Brödtext", indent=0)),
    ("Runcitat", SERIF, "Italic", 9.4, 13.5, "Bläck", dict(base="Brödtext", indent=0, just="LEFT_ALIGN")),
    ("Mellanrubrik", SANS, "Bold", 9.6, 13.5, "Rost mörk", dict(grid=True, before=1)),
    ("Punktlista", SERIF, "Roman", 9.4, 13.5, "Bläck", dict(base="Brödtext", indent=-4, left=4, bullet=True, just="LEFT_ALIGN")),
    ("Citat", SERIF, "Italic", 9.4, 13.5, "Bläck", dict(base="Brödtext", indent=0, left=4, just="LEFT_ALIGN")),
    ("Lyftcitat", SERIF, "Bold Italic", 14, 17, "Rost mörk", dict(just="LEFT_ALIGN")),
    ("Faktaruta rubrik", SERIF, "Black", 11, 13.5, "Rost mörk", dict()),
    ("Faktaruta text", SANS, "Regular", 8, 11.4, "Bläck", dict()),
    ("Faktaruta punkt", SANS, "Regular", 8, 11.4, "Bläck", dict(base="Faktaruta text", indent=-3.5, left=3.5, bullet=True)),
    ("Bildtext", SANS, "Regular", 6.9, 9.5, "Dämpad", dict()),
    ("Källor rubrik", SANS, "Bold", 8, 11, "Dämpad", dict(before=1)),
    ("Källor", SANS, "Regular", 7.1, 9.8, "Dämpad", dict()),
    ("Etikett", SANS, "Bold", 7.2, 9, "Rost", dict(caps=True, track=160)),
    ("Flik", SANS, "Bold", 7.5, 9, "Paper", dict(caps=True, track=160)),
    ("Öppning rubrik", SERIF, "Black", 30, 30, "Bläck", dict(track=-20, nohyph=True)),
    ("Ingress", SERIF, "Roman", 11.6, 16.5, "Bläck", dict()),
    ("Byline", SANS, "Bold", 7.4, 10, "Dämpad", dict(caps=True, track=120)),
    ("Siffran", SANS, "Bold", 30, 30, "Paper", dict(track=-20)),
    ("Siffran text", SANS, "Medium", 8.6, 12, "Paper", dict()),
    ("30 sekunder punkt", SANS, "Regular", 8.5, 12, "Bläck", dict(indent=-4, left=4, bullet=True)),
    ("Ledare rubrik", SERIF, "Black", 30, 30.6, "Bläck", dict(track=-15)),
    ("Ledare text", SERIF, "Roman", 10.2, 15.3, "Bläck", dict(indent=3.5)),
    ("Signatur", SERIF, "Italic", 10.2, 15.3, "Bläck", dict(before=1)),
    ("Innehåll tema", SANS, "Bold", 6.6, 8, "Rost", dict(caps=True, track=150)),
    ("Innehåll titel", SERIF, "Black", 10.5, 12.4, "Bläck", dict()),
    ("Innehåll ingress", SANS, "Regular", 7.6, 10.3, "Dämpad", dict()),
    ("Innehåll sida", SERIF, "Black", 15, 15, "Rost", dict(just="RIGHT_ALIGN")),
    ("Omslag titel", SERIF, "Black", 92, 83, "Bläck", dict(track=-35)),
    ("Omslag undertitel", SANS, "Demi Bold", 10.5, 13, "Bläck", dict(track=20)),
    ("Omslag tal", SANS, "Bold", 64, 61, "Paper", dict(track=-30)),
    ("Omslag puff", SERIF, "Black", 25, 26, "Paper", dict()),
    ("Omslag band rubrik", SERIF, "Black", 13, 14.6, "Bläck", dict()),
    ("Omslag band text", SANS, "Regular", 8.8, 12.3, "Dämpad", dict()),
    ("Verkstad text", SERIF, "Roman", 10, 15, "Bläck", dict(indent=3.5)),
    ("Stort tal", SERIF, "Black", 30, 30, "Rost", dict()),
    ("Metodhörna rubrik", SERIF, "Black", 17, 20, "Bläck", dict()),
    ("Baksida text", SANS, "Regular", 9.4, 14.1, "Bläck", dict()),
    ("Folio", SANS, "Bold", 8, 9, "Bläck", dict()),
    ("Löpande fot", SANS, "Demi Bold", 7, 9, "Dämpad", dict(caps=True, track=120, just="RIGHT_ALIGN")),
]
TECKEN = [("Kursiv", None, "Italic"), ("Fet", None, "Bold"), ("Rost", "Rost", None), ("Runor", None, "Italic")]
NAMN = {s[0] for s in STYCKEN}

# Nr 1:s sidor: mallsida och vad som står där (sidplanen, och etiketter på sidorna i skriptet)
SIDOR = [
    ("C", "Omslag: helsidesbild U 489 Morby, masthuvud, puff 14 mot 268, band med tre teman, bindrunan"),
    ("D", "Från redaktören (vänster) + I detta nummer (höger spalt, 76 mm) + läsbandet längst ned"),
    ("C", "Kartan: alla runstenar som prickar, helsida med utfall; bildtext och teckenförklaring i rutor"),
    ("A", "Runstenarna i siffror: stora tal i rader, korta förklaringar"),
    ("B", "Öppning: Döttrarna som runstenarna glömde – hero U 29 Hillersjö, rubrik, ingress, Siffran + 30 sekunder"),
    ("A", "Döttrarna, brödtext tre spalter, lyftcitat efter tredje stycket"),
    ("A", "Döttrarna, brödtext forts., diagram över spaltbredd"),
    ("A", "Döttrarna, slut + källor"),
    ("B", "Öppning: Färderna var de ungas – hero Vg 61 Härlingstorp"),
    ("A", "Färderna, brödtext"),
    ("A", "Färderna, slut + källor"),
    ("B", "Öppning: Tor föll, hjälten blev dräng – stående hero (Frølichs Tor), bilden oskuren"),
    ("A", "Tor föll, brödtext"),
    ("A", "Tor föll, diagram: ord som lever kvar"),
    ("A", "Tor föll, brödtext forts."),
    ("A", "Tor föll, slut + källor + bildruta Altunastenen (Tor fiskar efter Midgårdsormen)"),
    ("A", "04 Verkstaden: Hundra års runforskning + tre stora tal + 05 Metodhörnan (rostfärgad ruta)"),
    ("A", "06 I appen: Människorna – vad den gör, så gör du, vad den inte kan, diagram, skärmbild"),
    ("A", "Nästa nummer: Nr 2, mars 2027, Det vi inte ser – fyra block + läs fritt"),
    ("A", "Baksida: Om Korpus, Om Vitki, redaktion, Jarlabankes bro (bild), bakmast med bindrunan"),
]
MALLSIDOR = {
    "A": ("Brödtext", dict(top=17, bottom=18, inside=15, outside=15, cols=3, gutter=5.5, folio=True)),
    "B": ("Öppning", dict(top=0, bottom=0, inside=0, outside=0, cols=1, gutter=5.5, folio=False)),
    "C": ("Helsida", dict(top=0, bottom=0, inside=0, outside=0, cols=1, gutter=5.5, folio=False)),
    "D": ("Ledare", dict(top=17, bottom=18, inside=15, outside=15, cols=1, gutter=10, folio=True)),
}


# ---- InDesign-skriptet -----------------------------------------------------------------------------------------------------
def jsx() -> str:
    js = lambda v: json.dumps(v, ensure_ascii=False)  # noqa: E731
    farger = ",\n  ".join(f"[{js(n)}, [{r}, {g}, {b}]]" for n, (r, g, b) in FARGER)
    stycken = ",\n  ".join(js({"namn": n, "font": f, "stil": st, "grad": g, "rad": r, "farg": c, **o})
                           for n, f, st, g, r, c, o in STYCKEN)
    tecken = ",\n  ".join(js({"namn": n, "farg": c, "stil": st}) for n, c, st in TECKEN)
    mallar = ",\n  ".join(js({"prefix": p, "namn": n, **o}) for p, (n, o) in MALLSIDOR.items())
    sidor = ",\n  ".join(js({"mall": m, "text": t}) for m, t in SIDOR)
    return f"""// Korpus – mall för InDesign. Bygger ett nytt dokument med Korpus format: A4 med 3 mm utfall, uppslag, marginaler och
// tre spalter, baslinjerutnät 13,5 pt, Vitkis färger, stycke- och teckenformat och mallsidor (A Brödtext, B Öppning,
// C Helsida, D Ledare). Sidorna 1–20 får nr 1:s mallsidor och en etikett som inte skrivs ut.
// Kör: Fönster > Verktyg > Skript, högerklicka Användare > Visa i Finder, lägg filen där, dubbelklicka den i panelen.
// Spara sedan som InDesign-mall (.indt). Typsnitt: Charter (fritt) och Avenir Next (egen licens för tryck behövs).
// Genererat av utdata/tidskrift/indesign/bygg_indesign.py i Vitki (github.com/Precatio/runes).
#target indesign
(function () {{
var FARGER = [
  {farger}
];
var STYCKEN = [
  {stycken}
];
var TECKEN = [
  {tecken}
];
var MALLAR = [
  {mallar}
];
var SIDOR = [
  {sidor}
];
var fel = [];
function prova(f, vad) {{ try {{ f(); }} catch (e) {{ fel.push(vad + ": " + e); }} }}

app.scriptPreferences.measurementUnit = MeasurementUnits.MILLIMETERS;
var doc = app.documents.add();
prova(function () {{
  doc.viewPreferences.horizontalMeasurementUnits = MeasurementUnits.MILLIMETERS;
  doc.viewPreferences.verticalMeasurementUnits = MeasurementUnits.MILLIMETERS;
}}, "måttenheter");
with (doc.documentPreferences) {{
  pageWidth = 210; pageHeight = 297; facingPages = true; pagesPerDocument = SIDOR.length;
  documentBleedUniformSize = true; documentBleedTopOffset = 3;
}}
prova(function () {{
  with (doc.gridPreferences) {{
    baselineDivision = "13.5pt"; baselineStart = 17;
    baselineGridRelativeOption = BaselineGridRelativeOption.TOP_OF_PAGE_OF_BASELINE_GRID;
    baselineColor = UIColors.LIGHT_BLUE;
  }}
}}, "baslinjerutnät");

// färger (RGB som i webbversionen; tryckeriet tar RGB, Viktor 2026-11-11)
for (var i = 0; i < FARGER.length; i++) {{
  (function (f) {{ prova(function () {{
    doc.colors.add({{ name: f[0], model: ColorModel.PROCESS, space: ColorSpace.RGB, colorValue: f[1] }});
  }}, "färg " + f[0]); }})(FARGER[i]);
}}
function farg(n) {{ return n === "Paper" ? doc.swatches.item("Paper") : doc.colors.item(n); }}

// teckenformat
for (var i = 0; i < TECKEN.length; i++) {{
  (function (t) {{ prova(function () {{
    var c = doc.characterStyles.add({{ name: t.namn }});
    if (t.stil) c.fontStyle = t.stil;
    if (t.farg) c.fillColor = farg(t.farg);
  }}, "teckenformat " + t.namn); }})(TECKEN[i]);
}}

// styckeformat
var JUST = {{ LEFT_JUSTIFIED: Justification.LEFT_JUSTIFIED, LEFT_ALIGN: Justification.LEFT_ALIGN, RIGHT_ALIGN: Justification.RIGHT_ALIGN }};
for (var i = 0; i < STYCKEN.length; i++) {{
  (function (s) {{
    var p;
    prova(function () {{ p = doc.paragraphStyles.add({{ name: s.namn }}); }}, "styckeformat " + s.namn);
    if (!p) return;
    if (s.base) prova(function () {{ p.basedOn = doc.paragraphStyles.item(s.base); }}, s.namn + ": baserat på");
    prova(function () {{ p.appliedFont = s.font; }}, s.namn + ": typsnitt " + s.font);
    prova(function () {{ p.fontStyle = s.stil; }}, s.namn + ": stil " + s.stil);
    prova(function () {{ p.pointSize = s.grad; p.leading = s.rad; }}, s.namn + ": grad");
    prova(function () {{ p.fillColor = farg(s.farg); }}, s.namn + ": färg");
    prova(function () {{ p.appliedLanguage = "Swedish"; }}, s.namn + ": språk");
    if (s.just) prova(function () {{ p.justification = JUST[s.just]; }}, s.namn + ": justering");
    if (s.grid) prova(function () {{ p.alignToBaseline = true; }}, s.namn + ": baslinje");
    if (s.indent !== undefined) prova(function () {{ p.firstLineIndent = s.indent; }}, s.namn + ": indrag");
    if (s.left !== undefined) prova(function () {{ p.leftIndent = s.left; }}, s.namn + ": vänsterindrag");
    if (s.before) prova(function () {{ p.spaceBefore = s.before * 13.5 * 0.352778; }}, s.namn + ": avstånd före");
    if (s.caps) prova(function () {{ p.capitalization = Capitalization.ALL_CAPS; }}, s.namn + ": versaler");
    if (s.track) prova(function () {{ p.tracking = s.track; }}, s.namn + ": spärrning");
    if (s.nohyph) prova(function () {{ p.hyphenation = false; }}, s.namn + ": avstavning");
    if (s.drop) prova(function () {{ p.dropCapLines = s.drop; p.dropCapCharacters = 1; }}, s.namn + ": anfang");
    if (s.bullet) prova(function () {{
      p.bulletsAndNumberingListType = ListType.BULLET_LIST; p.bulletsTextAfter = "^t"; p.bulletsCharacterStyle = doc.characterStyles.item("Rost");
    }}, s.namn + ": punkter");
  }})(STYCKEN[i]);
}}

// mallsidor
function marginaler(sida, m) {{
  with (sida.marginPreferences) {{
    top = m.top; bottom = m.bottom; left = m.inside; right = m.outside; columnCount = m.cols; columnGutter = m.gutter;
  }}
}}
for (var i = 0; i < MALLAR.length; i++) {{
  (function (m, nr) {{ prova(function () {{
    var ms = nr === 0 ? doc.masterSpreads.item(0) : doc.masterSpreads.add();
    ms.namePrefix = m.prefix; ms.baseName = m.namn;
    for (var j = 0; j < ms.pages.length; j++) {{
      var sida = ms.pages.item(j);
      marginaler(sida, m);
      if (!m.folio) continue;
      var vanster = sida.side === PageSideOptions.LEFT_HAND;
      var b = sida.bounds;  // [y1, x1, y2, x2]
      var y1 = b[2] - 12, y2 = b[2] - 7;
      var folio = sida.textFrames.add({{ geometricBounds: vanster ? [y1, b[1] + 15, y2, b[1] + 40] : [y1, b[3] - 40, y2, b[3] - 15] }});
      folio.contents = SpecialCharacters.AUTO_PAGE_NUMBER;
      folio.parentStory.paragraphs.everyItem().appliedParagraphStyle = doc.paragraphStyles.item("Folio");
      if (!vanster) folio.parentStory.paragraphs.everyItem().justification = Justification.RIGHT_ALIGN;
      var fot = sida.textFrames.add({{ geometricBounds: vanster ? [y1, b[1] + 45, y2, b[3] - 15] : [y1, b[1] + 15, y2, b[3] - 45] }});
      fot.contents = "Korpus nr 1 · November 2026";
      fot.parentStory.paragraphs.everyItem().appliedParagraphStyle = doc.paragraphStyles.item("Löpande fot");
      if (vanster) fot.parentStory.paragraphs.everyItem().justification = Justification.LEFT_ALIGN;
    }}
  }}, "mallsida " + m.prefix); }})(MALLAR[i], i);
}}

// sidorna: nr 1:s mallsidor och en etikett som inte skrivs ut
for (var i = 0; i < SIDOR.length && i < doc.pages.length; i++) {{
  (function (s, sida, nr) {{
    prova(function () {{
      for (var j = 0; j < MALLAR.length; j++) if (MALLAR[j].prefix === s.mall) sida.appliedMaster = doc.masterSpreads.item(s.mall + "-" + MALLAR[j].namn);
    }}, "sida " + nr + ": mallsida");
    prova(function () {{
      var b = sida.bounds;
      var e = sida.textFrames.add({{ geometricBounds: [b[0] + 4, b[1] + 4, b[0] + 14, b[3] - 4], contents: "Sida " + nr + " · " + s.text }});
      e.nonprinting = true;
      e.parentStory.paragraphs.everyItem().appliedParagraphStyle = doc.paragraphStyles.item("Bildtext");
      e.fillColor = doc.colors.item("Rost ljus");
    }}, "sida " + nr + ": etikett");
  }})(SIDOR[i], doc.pages.item(i), i + 1);
}}

alert("Korpus-mallen är byggd: " + doc.paragraphStyles.length + " styckeformat, " + doc.characterStyles.length +
      " teckenformat, " + doc.masterSpreads.length + " mallsidor, " + doc.pages.length + " sidor." +
      (fel.length ? "\\n\\nDet här gick inte (oftast ett typsnitt som saknas):\\n" + fel.slice(0, 15).join("\\n") : "") +
      "\\n\\nSpara som InDesign-mall: Arkiv > Spara som > InDesign CC-mall (.indt).");
}})();
"""


# ---- taggad text ----------------------------------------------------------------------------------------------------------
def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("<", "\\<").replace(">", "\\>")


def inline_tt(s: str) -> str:
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)  # länkar: bara texten
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<CharStyle:Fet>\1<CharStyle:>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<CharStyle:Kursiv>\1<CharStyle:>", s)
    return s


def plain(s: str) -> str:
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)


def tt_fil(stycken: list[tuple[str, str]], path: str):
    """InDesign Tagged Text, UTF-16 LE med BOM (<UNICODE-WIN>): en rad per stycke, <ParaStyle:namn>text."""
    for st, _ in stycken:
        assert st in NAMN, st
    rader = ["<UNICODE-WIN>"] + [f"<ParaStyle:{st}>{t}" for st, t in stycken]
    with open(path, "wb") as fh:
        fh.write("\r\n".join(rader).encode("utf-16"))


def artikel_stycken(body: str, citat: str | None):
    """BlogBody-markeringen som stycken (stil, taggad text), i samma ordning och med samma regler som
    bygg_tidskrift.body_html: Kort sagt-rutan går till öppningssidan, sammanfattningsrutan tas bort, anfang på första
    stycket, lyftcitatet efter tredje, källorna i liten stil. Bilder och diagram blir platshållare."""
    ut, kort, n, svans, bilder, diagram = [], [], 0, False, [], 0
    for b in re.split(r"(:::(?:box|chart)[^\n]*\n.*?\n:::)", body, flags=re.S):
        if b.startswith(":::chart"):
            diagram += 1
            ut.append(("Bildtext", f"[DIAGRAM {diagram}: se grafik/diagram – över spaltbredd]"))
            continue
        if b.startswith(":::box"):
            head, inner = b[len(":::box"):].split("\n", 1)
            head, inner = head.strip(), inner.rsplit(":::", 1)[0]
            rader = [l for l in inner.split("\n") if l.strip()]
            if not kort and head.lower().startswith(("kort", "in short")):
                kort = [inline_tt(l[2:] if l.startswith("- ") else l) for l in rader]
                continue
            if re.search(r"viktigaste|essentials", head, re.I):
                continue
            ut.append(("Faktaruta rubrik", inline_tt(head)))
            ut += [("Faktaruta punkt" if l.startswith("- ") else "Faktaruta text", inline_tt(l[2:] if l.startswith("- ") else l)) for l in rader]
            continue
        rader = b.split("\n")
        i = 0
        while i < len(rader):
            l = rader[i].rstrip()
            i += 1
            if not l:
                continue
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", l)
            if m:
                cap = rader[i] if i < len(rader) and rader[i].strip() and not rader[i].startswith(("!", "#", ":::")) else ""
                if cap:
                    i += 1
                bilder.append((m.group(2), cap))
                ut.append(("Bildtext", f"[BILD: {bildnamn(m.group(2))}] " + inline_tt(cap)))
                continue
            if l.startswith("## "):
                h = l[3:]
                if re.match(r"(Källor|Se själv|Sources|See for yourself)", h):
                    svans = True
                ut.append(("Källor rubrik" if svans else "Mellanrubrik", inline_tt(h)))
            elif l.startswith("> "):
                ut.append(("Citat", inline_tt(l[2:])))
            elif l.startswith("- "):
                ut.append(("Källor" if svans else "Punktlista", inline_tt(l[2:])))
            elif l.startswith("*") and l.endswith("*") and not svans:
                ut.append(("Runcitat", inline_tt(l)))
            else:
                if svans:
                    ut.append(("Källor", inline_tt(l)))
                    continue
                n += 1
                ut.append(("Brödtext första" if n == 1 else "Brödtext", inline_tt(l)))
                if n == 3 and citat:
                    ut.append(("Lyftcitat", esc(citat)))
    return ut, kort, bilder


# ---- bilderna -------------------------------------------------------------------------------------------------------------
def original(url: str) -> str:
    """En Commons-miniatyr (thumb/…/1280px-Fil.jpg) eller originaladress → originalfilens adress."""
    m = re.match(r"https://(?:thumb|upload)\.wikimedia\.org/wikipedia/commons/thumb/([0-9a-f]/[0-9a-f]{2}/[^/]+)/", url)
    if m:
        return "https://upload.wikimedia.org/wikipedia/commons/" + m.group(1)
    return url


def bildnamn(url: str) -> str:
    return re.sub(r"[^\w.,-]", "_", unquote(original(url).rsplit("/", 1)[-1]))


def hamta(url: str, mal: str) -> bool:
    if os.path.exists(mal) and os.path.getsize(mal) > 10000:
        return True
    for forsok in range(4):
        r = subprocess.run(["curl", "-sfL", "--max-time", "300", "-A", UA, "-o", mal, url])
        if r.returncode == 0 and os.path.getsize(mal) > 10000:
            time.sleep(3)
            return True
        time.sleep(15 * (forsok + 1))  # Wikimedia svarar 429 vid täta anrop
    return False


# ---- grovlayouten för nr 1 (Viktor 2026-11-14: "ja" till en version som lägger ut innehållet) ------------------------------
def grovlayout_jsx() -> str:
    """Ett andra InDesign-skript som körs i dokumentet från Korpus_mall.jsx och lägger ut nr 1 enligt sidplanen: bilder i
    ramar (fyllda proportionellt), artiklarnas taggade text placerad i en kedja från öppningssidans ram till trespaltsramar
    på de följande sidorna, och de övriga sidornas texter i egna ramar. Allt är en grovlayout att finjustera.
    Data skrivs med ensure_ascii, så att skriptet fungerar oavsett hur InDesign läser filens teckenkodning."""
    hero = [bildnamn(B.WM + a["bild"]) for a in B.ARTIKLAR]
    plan = {
        "omslag": bildnamn(B.OMSLAG), "karta": "karta_alla.png", "altuna": bildnamn(B.SLUTRUTA["bild"]),
        "bak": bildnamn(B.BAKBILD["bild"]), "app": "app_manniskorna_sv.jpg",
        # artikel: öppningssida (1-baserad), brödtextsidor, textfil, öppningsbild
        "artiklar": [
            {"oppning": 5, "sidor": [6, 7, 8], "fil": "02_dottrar_sv.txt", "bild": hero[0]},
            {"oppning": 9, "sidor": [10, 11], "fil": "03_unga_sv.txt", "bild": hero[1]},
            {"oppning": 12, "sidor": [13, 14, 15, 16], "fil": "04_overlevde_sv.txt", "bild": hero[2]},
        ],
    }
    data = json.dumps(plan, ensure_ascii=True)
    return """// Korpus nr 1 – grovlayout. Kör EFTER Korpus_mall.jsx, i dokumentet som mallen skapade. Lägger ut bilder och texter
// enligt sidplanen (nr1/sidplan.pdf) som en grovlayout att finjustera. Filerna läses från paketet: skriptet ska ligga i
// mappen mall/ bredvid nr1/ (som i zip-filen).
// Genererat av utdata/tidskrift/indesign/bygg_indesign.py i Vitki (github.com/Precatio/runes).
#target indesign
(function () {
var P = """ + data + """;
var fel = [];
function prova(f, vad) { try { f(); } catch (e) { fel.push(vad + ": " + e); } }
if (app.documents.length === 0) { alert("Inget dokument \\u00e4r \\u00f6ppet. K\\u00f6r f\\u00f6rst Korpus_mall.jsx."); return; }
var doc = app.activeDocument;
if (!doc.paragraphStyles.item("Br\\u00f6dtext").isValid) { alert("Dokumentet saknar Korpus format. K\\u00f6r f\\u00f6rst Korpus_mall.jsx."); return; }
app.scriptPreferences.measurementUnit = MeasurementUnits.MILLIMETERS;
var paket = File($.fileName).parent.parent;  // mall/ -> paketets rot
if (!Folder(paket.fullName + "/nr1").exists) {
  paket = Folder.selectDialog("V\u00e4lj mappen korpus_indesign (den som inneh\u00e5ller mappen nr1)");
  if (!paket) return;
}
var NR1 = paket.fullName + "/nr1";
function fil(rel) { var f = File(NR1 + "/" + rel); if (!f.exists) fel.push("saknas: " + rel); return f; }
prova(function () { app.taggedTextImportPreferences.styleConflict = StyleConflict.PUBLICATION_DEFINITION; }, "importinst\\u00e4llning");
function sida(n) { return doc.pages.item(n - 1); }
function bild(s, gb, rel) {
  var r = s.rectangles.add({ geometricBounds: gb, strokeWeight: 0 });
  prova(function () { r.place(fil(rel)); r.fit(FitOptions.FILL_PROPORTIONALLY); r.fit(FitOptions.CENTER_CONTENT); }, "bild " + rel);
  return r;
}
function ram(s, gb, kol) {
  var t = s.textFrames.add({ geometricBounds: gb });
  t.textFramePreferences.textColumnCount = kol || 1;
  t.textFramePreferences.textColumnGutter = 5.5;
  return t;
}
function satsyta(s) { var b = s.bounds; return [b[0] + 17, b[1] + 15, b[2] - 18, b[3] - 15]; }
function placera(t, rel) { prova(function () { t.place(fil(rel), false); }, "text " + rel); }

// 1 omslaget och 3 kartan: helsida med utfall
prova(function () {
  var b = sida(1).bounds; bild(sida(1), [b[0] - 3, b[1] - 3, b[2] + 3, b[3] + 3], "bilder/" + P.omslag);
  var t = ram(sida(1), [b[0] + 11, b[1] + 14, b[0] + 55, b[3] - 14]);
  t.contents = "Korpus\\rDigital runforskning fr\\u00e5n Vitki";
  t.paragraphs.item(0).appliedParagraphStyle = doc.paragraphStyles.item("Omslag titel");
  t.paragraphs.item(1).appliedParagraphStyle = doc.paragraphStyles.item("Omslag undertitel");
}, "omslaget");
prova(function () { var b = sida(3).bounds; bild(sida(3), [b[0] - 3, b[1] - 3, b[2] + 3, b[3] + 3], "grafik/" + P.karta); }, "kartan");

// 2 ledaren (v\\u00e4nster) och inneh\\u00e5llet (h\\u00f6ger spalt, 76 mm)
prova(function () {
  var a = satsyta(sida(2));
  placera(ram(sida(2), [a[0], a[1], a[2] - 40, a[3] - 86]), "texter/01_ledare_sv.txt");
  var t = ram(sida(2), [a[0], a[3] - 76, a[2] - 40, a[3]]);
  t.contents = "I detta nummer"; t.paragraphs.item(0).appliedParagraphStyle = doc.paragraphStyles.item("Etikett");
}, "sida 2");

// 4 siffrorna och 19 n\\u00e4sta nummer: sidans text (r\\u00e4knas fram ur data i Vitki)
prova(function () { placera(ram(sida(4), satsyta(sida(4)), 3), "sidor/sida-04.txt"); }, "sida 4");
prova(function () { placera(ram(sida(19), satsyta(sida(19)), 2), "sidor/sida-19.txt"); }, "sida 19");

// artiklarna: \\u00f6ppningsbild, \\u00f6ppningsram och kedja av trespaltsramar
for (var i = 0; i < P.artiklar.length; i++) {
  (function (A) { prova(function () {
    var s = sida(A.oppning), b = s.bounds;
    bild(s, [b[0] - 3, b[1] - 3, b[0] + 111, b[3] + 3], "bilder/" + A.bild);
    var forsta = ram(s, [b[0] + 122, b[1] + 18, b[2] - 15, b[3] - 18], 1);
    var forra = forsta;
    for (var j = 0; j < A.sidor.length; j++) {
      var nu = ram(sida(A.sidor[j]), satsyta(sida(A.sidor[j])), 3);
      forra.nextTextFrame = nu; forra = nu;
    }
    placera(forsta, "texter/" + A.fil);
  }, "artikeln " + A.fil); })(P.artiklar[i]);
}

// 16 bildrutan Altuna, l\\u00e4ngst ned p\\u00e5 Tor-artikelns sista sida
prova(function () {
  var a = satsyta(sida(16));
  bild(sida(16), [a[2] - 70, a[1], a[2], a[1] + 55], "bilder/" + P.altuna);
  placera(ram(sida(16), [a[2] - 70, a[1] + 60, a[2], a[3]], 1), "texter/04b_bildruta_altuna_sv.txt");
}, "sida 16 bildrutan");

// 17 Verkstaden + Metodh\\u00f6rnan, 18 I appen, 20 baksidan
prova(function () { placera(ram(sida(17), satsyta(sida(17)), 2), "texter/05_verkstaden_metodhornan_sv.txt"); }, "sida 17");
prova(function () {
  var a = satsyta(sida(18));
  placera(ram(sida(18), [a[0], a[1], a[0] + 160, a[3]], 2), "texter/06_i_appen_sv.txt");
  bild(sida(18), [a[0] + 165, a[1], a[2], a[3]], "grafik/" + P.app);
}, "sida 18");
prova(function () {
  var a = satsyta(sida(20));
  placera(ram(sida(20), [a[0], a[1], a[0] + 95, a[3]], 2), "texter/08_baksida_sv.txt");
  bild(sida(20), [a[0] + 100, a[1], a[0] + 232, a[3]], "bilder/" + P.bak);
}, "sida 20");

alert("Grovlayouten f\\u00f6r Korpus nr 1 \\u00e4r utlagd." + (fel.length ? "\\n\\nDet h\\u00e4r gick inte:\\n" + fel.slice(0, 15).join("\\n") : "") +
      "\\n\\nText som inte f\\u00e5r plats syns som \\u00f6versatt text (r\\u00f6tt plus) i sista ramen: l\\u00e4gg till en ram eller korta enligt PDF:en.");
})();
"""


# ---- inga Markdown-filer till formgivaren (Viktor 2026-11-14: "han blev irriterad över md-formatet") ----------------------
CSS_DOK = ("body{font:10.5pt/1.5 'Avenir Next',Helvetica,sans-serif;color:#1d2226;max-width:170mm;margin:0 auto}"
           "h1,h2{font-family:Charter,Georgia,serif;color:#1d2226}h1{font-size:22pt}h2{font-size:14pt;margin-top:8mm}"
           "code{font-size:9pt}table{border-collapse:collapse}td,th{border-bottom:.5pt solid #d8dcdf;padding:3px 6px;text-align:left;vertical-align:top}"
           "a{color:#b7410e}@page{size:A4;margin:18mm}")


def md_till_pdf(md: str, pdf: str):
    """Markdown → PDF (pandoc → HTML → Chrome), och Markdown-filen tas bort."""
    tmp = pdf[:-4] + ".tmp.html"
    subprocess.run(["pandoc", md, "-s", "--metadata", "title= ", "-o", tmp], check=True)
    t = open(tmp, encoding="utf-8").read().replace("</head>", f"<style>{CSS_DOK}</style></head>")
    t = re.sub(r'<header id="title-block-header">.*?</header>', "", t, flags=re.S)
    open(tmp, "w", encoding="utf-8").write(t)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", "file://" + tmp],
                   capture_output=True, timeout=180)
    os.remove(tmp)
    os.remove(md)


def md_till_docx(md: str, docx: str):
    subprocess.run(["pandoc", md, "-f", "markdown", "-o", docx], check=True)
    os.remove(md)


def utan_markdown():
    for rot, _, filer in os.walk(UT):
        for f in filer:
            p = os.path.join(rot, f)
            if not f.endswith(".md"):
                continue
            if os.path.basename(rot) == "texter":
                md_till_docx(p, p[:-3] + ".docx")
            else:  # KREDITER: ren text
                t = open(p, encoding="utf-8").read()
                t = re.sub(r"\*\*(.+?)\*\*", r"\1", t).replace("# ", "").replace("  - ", "    ")
                open(p[:-3] + ".txt", "w", encoding="utf-8").write(t)
                os.remove(p)


LASMIG = """KORPUS NR 1 – MATERIAL FÖR INDESIGN
====================================

1. GÖR MALLEN
   Dubbelklicka mall/Korpus_mall.jsx i InDesigns skriptpanel.
   (Fönster > Verktyg > Skript. Högerklicka Användare > Visa i Finder
   och lägg mappen mall där.)
   Du får ett dokument med Korpus format, färger, styckeformat,
   mallsidor och 20 tomma sidor. Varje sida har en etikett om vad
   som ska stå där.

2. LÄGG UT NR 1 (valfritt)
   Dubbelklicka mall/Korpus_nr1_grovlayout.jsx i samma dokument.
   Bilder och texter läggs ut ungefär som i PDF:en.
   Hittar skriptet inte materialet frågar det efter mappen
   korpus_indesign.

3. FINJUSTERA
   Jämför med nr1/referens/Korpus_nr1_sv_tryck.pdf (det som trycktes)
   och nr1/sidplan.pdf.

MAPPARNA
   nr1/texter   .txt  = text för InDesign (Arkiv > Placera,
                        behåll formatmallar).
                .docx = samma text i Word.
   nr1/bilder   bilderna i full upplösning.
                KREDITER.txt = fotograf och licens. Krediten ska stå
                vid bilden.
   nr1/grafik   karta, skärmbilder och Vitkis bindruna (SVG).
   nr1/sidor    varje sida som bild och som text.

BRA ATT VETA
   - Ändra inte i texterna. Be Viktor om ändringar
     (siffrorna är kontrollerade mot data).
   - Typsnitt: Charter och Avenir Next.
   - Skripten är inte provkörda i InDesign. Rutan som kommer upp
     på slutet listar det som inte gick – skicka den till Viktor.
"""

# ---- bygget ---------------------------------------------------------------------------------------------------------------
def main():
    for d in ("mall", "nr1/referens", "nr1/sidor", "nr1/texter", "nr1/bilder", "nr1/grafik"):
        os.makedirs(os.path.join(UT, d), exist_ok=True)
    open(os.path.join(UT, "mall", "Korpus_mall.jsx"), "w", encoding="utf-8-sig").write(jsx())
    open(os.path.join(UT, "mall", "Korpus_nr1_grovlayout.jsx"), "w", encoding="utf-8-sig").write(grovlayout_jsx())

    # referens-PDF:erna och sidorna
    for f in ("Korpus_nr1_sv.pdf", "Korpus_nr1_sv_tryck.pdf", "Korpus_nr1_en.pdf"):
        shutil.copy2(os.path.join(TID, f), os.path.join(NR1, "referens", f))
    pdf = os.path.join(TID, "Korpus_nr1_sv.pdf")
    subprocess.run(["pdftoppm", "-r", "150", "-jpeg", "-jpegopt", "quality=85", pdf, os.path.join(NR1, "sidor", "sida")], check=True)
    for i in range(1, len(SIDOR) + 1):
        subprocess.run(["pdftotext", "-layout", "-f", str(i), "-l", str(i), pdf, os.path.join(NR1, "sidor", f"sida-{i:02d}.txt")], check=True)

    # texterna
    krediter, alla_bilder = [], {}
    for nr, a in enumerate(B.ARTIKLAR, 1):
        d = json.load(open(os.path.join(B.BLOGG, a["fil"]), encoding="utf-8"))
        for sprak in ("sv", "en"):
            suf = "_en" if sprak == "en" else ""
            L = a[sprak]
            st, kort, bilder = artikel_stycken(d["body" + suf], L["citat"])
            oppning = [("Etikett", esc(L["tema"])), ("Öppning rubrik", esc(d["title" + suf])), ("Ingress", inline_tt(d["summary" + suf])),
                       ("Byline", "Viktor Kvant · Vitki"), ("Siffran", esc(L["siffra"])), ("Siffran text", esc(L["betyder"]))]
            oppning += [("30 sekunder punkt", k) for k in kort]
            namn = f"{nr + 1:02d}_{os.path.splitext(a['fil'])[0]}_{sprak}"
            tt_fil(oppning + st, os.path.join(NR1, "texter", namn + ".txt"))
            md = [f"# {d['title' + suf]}", "", d["summary" + suf], "", d["body" + suf]]
            open(os.path.join(NR1, "texter", namn + ".md"), "w", encoding="utf-8").write("\n".join(md))
            for url, cap in bilder:
                alla_bilder.setdefault(original(url), cap)
        hero = B.WM + a["bild"]
        cap = next((l for l in d["body"].split("\n") if False), "")
        alla_bilder.setdefault(hero, next((d["body"].split("\n")[j + 1] for j, l in enumerate(d["body"].split("\n"))
                                           if l.startswith("![") and a["bild"].split("/")[-1] in l), ""))
    # ledaren, Verkstaden + Metodhörnan, I appen, baksidan, bildrutan
    red = json.load(open(os.path.join(TID, "redaktor_nr1.json"), encoding="utf-8"))
    for sprak in ("sv", "en"):
        T, R, A = B.T[sprak], red[sprak], B.APP[sprak]
        tt_fil([("Etikett", "Från redaktören" if sprak == "sv" else "From the editor"), ("Ledare rubrik", esc(R["rubrik"]))]
               + [("Ledare text", inline_tt(p)) for p in R["text"]] + [("Signatur", "Viktor Kvant, redaktör" if sprak == "sv" else "Viktor Kvant, editor")],
               os.path.join(NR1, "texter", f"01_ledare_{sprak}.txt"))
        v = [("Flik", esc(T["vflik"])), ("Ledare rubrik", esc(T["vrubrik"])), ("Ingress", esc(T["vdeck"]))]
        v += [("Stort tal", esc(t)) if j % 2 == 0 else ("Innehåll ingress", esc(t)) for tal in T["tal"] for j, t in enumerate(tal)]
        for rub, txt in (T["v1"], T["v2"]):
            v += [("Mellanrubrik", esc(rub)), ("Verkstad text", inline_tt(txt.replace("{namn}", "Korpus")))]
        v += [("Flik", esc(T["mflik"])), ("Metodhörna rubrik", esc(T["mrubrik"])), ("Verkstad text", inline_tt(T["mtext"]))]
        tt_fil(v, os.path.join(NR1, "texter", f"05_verkstaden_metodhornan_{sprak}.txt"))
        ap = [("Flik", esc(A["flik"])), ("Ledare rubrik", esc(A["rubrik"])), ("Ingress", esc(A["deck"])), ("Mellanrubrik", esc(A["gor_rubrik"]))]
        ap += [("Verkstad text", esc(t)) for t in A["gor"]] + [("Mellanrubrik", esc(A["steg_rubrik"]))]
        ap += [("Punktlista", esc(t)) for t in A["steg"]] + [("Mellanrubrik", esc(A["kan_inte_rubrik"])), ("Verkstad text", esc(A["kan_inte"]))]
        ap += [("Faktaruta rubrik", esc(A["panel"]))] + [("Faktaruta text", esc(f"{rad}: " + ", ".join(f"{n} {p} %" for n, p, _ in grupper))) for rad, grupper in A["rader"]]
        ap += [("Källor", esc(A["kalla"])), ("Källor", esc(A["fot"])), ("Bildtext", f"[BILD: grafik/{os.path.basename(A['bild'])}] " + html.unescape(re.sub('<[^>]+>', '', A['bildtext'])))]
        tt_fil(ap, os.path.join(NR1, "texter", f"06_i_appen_{sprak}.txt"))
        bak = []
        for rub, txt in T["bak"]:
            bak += [("Mellanrubrik", esc(rub.replace("{namn}", "Korpus"))), ("Baksida text", inline_tt(txt.replace("{namn}", "Korpus")))]
        bak.append(("Bildtext", f"[BILD: {bildnamn(B.BAKBILD['bild'])}] " + esc(B.BAKBILD[sprak])))
        tt_fil(bak, os.path.join(NR1, "texter", f"08_baksida_{sprak}.txt"))
        S = B.SLUTRUTA[sprak]
        tt_fil([("Flik", esc(S["flik"])), ("Faktaruta rubrik", esc(S["rubrik"])), ("Faktaruta text", esc(S["text"])),
                ("Bildtext", f"[BILD: {bildnamn(B.SLUTRUTA['bild'])}] " + esc(S["kredit"]))],
               os.path.join(NR1, "texter", f"04b_bildruta_altuna_{sprak}.txt"))
    alla_bilder.setdefault(B.OMSLAG, B.T["sv"]["omkredit"])
    alla_bilder.setdefault(B.SLUTRUTA["bild"], B.SLUTRUTA["sv"]["kredit"])
    alla_bilder.setdefault(B.BAKBILD["bild"], B.BAKBILD["sv"])
    open(os.path.join(UT, "LASMIG.txt"), "w", encoding="utf-8").write(LASMIG)
    for gammal in (os.path.join(UT, "LASMIG.md"), os.path.join(UT, "LASMIG.pdf"), os.path.join(NR1, "texter", "LASMIG.txt")):
        if os.path.exists(gammal):
            os.remove(gammal)
    _ = (
        "Filerna *.txt är InDesign-taggad text (UTF-16): Arkiv > Placera, kryssa i Visa importalternativ och välj att använda\n"
        "textens formatmallar. Styckeformaten heter som i Korpus_mall.jsx. *.docx är samma artiklar som Word-filer.\n"
        "Sidorna 3, 4 och 19 (kartan, siffrorna, nästa nummer) räknas fram ur data: deras text står i ../sidor/sida-NN.txt.\n")

    # bilderna i originalupplösning
    if "--utan-bilder" not in sys.argv:
        for url, cap in alla_bilder.items():
            namn = bildnamn(url)
            ok = hamta(url, os.path.join(NR1, "bilder", namn))
            krediter.append((namn, url, re.sub(r"\s+", " ", plain(cap)).strip(), ok))
        with open(os.path.join(NR1, "bilder", "KREDITER.md"), "w", encoding="utf-8") as fh:
            fh.write("# Bilderna i Korpus nr 1\n\nOriginalfilerna från Wikimedia Commons. Krediten ska stå vid bilden i tryck, "
                     "som i PDF:en. Licensen står i krediten; se filsidan på Commons för detaljer.\n\n")
            for namn, url, cap, ok in krediter:
                fh.write(f"- **{namn}**{'' if ok else ' (KUNDE INTE HÄMTAS – hämta för hand)'}\n  - Källa: {url}\n  - Kredit: {cap or '(se PDF:en)'}\n")

    # grafiken
    for f in ("karta_alla.png", "app_manniskorna_sv.jpg", "app_manniskorna_en.jpg"):
        shutil.copy2(os.path.join(TID, "bilder", f), os.path.join(NR1, "grafik", f))
    shutil.copy2(os.path.join(ROOT, "branding", "vitki_logo.svg"), os.path.join(NR1, "grafik", "vitki_bindruna.svg"))
    shutil.copy2(os.path.join(TID, "bilder", "karta_punkter.json"), os.path.join(NR1, "grafik", "karta_punkter.json"))
    for nr, a in enumerate(B.ARTIKLAR, 1):
        d = json.load(open(os.path.join(B.BLOGG, a["fil"]), encoding="utf-8"))
        for k, blk in enumerate(re.findall(r":::chart([^\n]*\n.*?)\n:::", d["body"], flags=re.S), 1):
            open(os.path.join(NR1, "grafik", f"diagram_{os.path.splitext(a['fil'])[0]}_{k}.txt"), "w", encoding="utf-8").write(blk)

    # sidplanen
    kort = "".join(f'<figure><img src="sidor/sida-{i:02d}.jpg"><figcaption><b>{i}</b> · mallsida {m}<br>{html.escape(t)}</figcaption></figure>'
                   for i, (m, t) in enumerate(SIDOR, 1))
    mallar = "".join(f"<li><b>{p} {n}</b>: marginaler {o['top']}/{o['bottom']}/{o['inside']}/{o['outside']} mm, {o['cols']} spalt(er)"
                     f"{', folio och löpande fot' if o['folio'] else ''}</li>" for p, (n, o) in MALLSIDOR.items())
    sida = f"""<!doctype html><html lang="sv"><head><meta charset="utf-8"><style>
@page {{ size: A4 landscape; margin: 10mm; }} body {{ font: 9pt/1.35 "Avenir Next", Helvetica, sans-serif; color: #1d2226; }}
h1 {{ font: 900 20pt Charter, Georgia, serif; margin: 0 0 2mm; }} .grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 5mm; }}
figure {{ margin: 0; break-inside: avoid; }} img {{ width: 100%; border: .3pt solid #d8dcdf; }}
figcaption {{ font-size: 7pt; color: #3a4249; margin-top: 1mm; }} b {{ color: #b7410e; }} ul {{ margin: 0 0 4mm; padding-left: 4mm; }}
</style></head><body><h1>Korpus nr 1 – sidplan</h1>
<p>20 sidor, A4 med 3 mm utfall, häftad. Brödtext Charter 9,4/13,5 pt på baslinjerutnät 13,5 pt, tre spalter med 5,5 mm mellanrum.
Rost #b7410e är enda accentfärgen. Mallsidorna i Korpus_mall.jsx:</p><ul>{mallar}</ul><div class="grid">{kort}</div></body></html>"""
    hp = os.path.join(NR1, "sidplan.html")
    open(hp, "w", encoding="utf-8").write(sida)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={os.path.join(NR1, 'sidplan.pdf')}",
                    "file://" + hp], capture_output=True, timeout=180)
    utan_markdown()
    print("klart:", UT, "| bilder:", len(krediter), "| misslyckade:", [k[0] for k in krediter if not k[3]])


if __name__ == "__main__":
    main()
