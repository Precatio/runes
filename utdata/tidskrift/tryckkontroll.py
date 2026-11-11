"""Kontroller för Korpus före tryck (Viktor 2026-11-11; tryckeriet är Helloprint, häftad A4).

- baslinjer(pdf): för varje brödtextsida i tre spalter, att alla rader i brödtexten står på samma raster (13,5 pt) och
  att spalterna slutar på samma baslinje (en kortare sista spalt godtas bara på artikelns sista sida);
- rapport(): skriver tryck_kontroll.md för tryckfilerna: sidantal och format, TrimBox/BleedBox, typsnitt inbäddade,
  minsta avstånd från text till skärkant, bildernas effektiva upplösning i tryckt storlek (under 300 dpi listas,
  under 200 dpi är ett verkligt problem), färgrymder och övertryck, och baslinjekontrollen för skärmversionerna.
    .venv/bin/python utdata/tidskrift/tryckkontroll.py
"""
import os
import re
import subprocess
import xml.etree.ElementTree as ET

LH = 13.5
MM = 72 / 25.4


def _sidor(pdf):
    xml = subprocess.run(["pdftotext", "-bbox-layout", pdf, "-"], capture_output=True, text=True).stdout
    xml = re.sub(r"<!DOCTYPE[^>]*>", "", xml).replace(' xmlns="http://www.w3.org/1999/xhtml"', "")
    root = ET.fromstring(xml)
    for page in root.iter("page"):
        lines = []
        for ln in page.iter("line"):
            words = [w.text or "" for w in ln.iter("word")]
            lines.append(dict(x0=float(ln.get("xMin")), y0=float(ln.get("yMin")), x1=float(ln.get("xMax")), y1=float(ln.get("yMax")),
                              text=" ".join(words)))
        yield float(page.get("width")), float(page.get("height")), lines


def _mult(m, n):
    return [m[0] * n[0] + m[1] * n[2], m[0] * n[1] + m[1] * n[3], m[2] * n[0] + m[3] * n[2], m[2] * n[1] + m[3] * n[3],
            m[4] * n[0] + m[5] * n[2] + n[4], m[4] * n[1] + m[5] * n[3] + n[5]]


def _textrader(page):
    """(typsnitt, storlek, x, baslinje uppifrån, text) för varje textbit på sidan."""
    H = float(page.mediabox.height)
    runs = []

    def v(text, cm, tm, fd, fs):
        if text.strip():
            m = _mult(tm, cm)
            runs.append((str(fd.get("/BaseFont", "")) if fd else "", round(fs * (m[0] ** 2 + m[1] ** 2) ** .5, 2), m[4], H - m[5], text))
    page.extract_text(visitor_text=v)
    return runs


def baslinjer(pdf, kant=0.0):
    """Brödtextsidorna i tre spalter. Rasterraderna är brödtexten (9,4 pt), rutornas text (8,4 pt) och rutornas
    rubrik (11 pt); deras baslinjer ska alla ligga på samma 13,5-punktsraster, och varje spalts sista rasterrad ska stå
    på samma baslinje som de andra spalternas. kant = utfallet i pt för tryckfilen."""
    from pypdf import PdfReader
    sidor = PdfReader(pdf).pages
    x0 = 15 * MM + kant
    bredd = (180 - 2 * 5.5) / 3 * MM
    steg = bredd + 5.5 * MM
    ut = []
    huvud = []
    for page in sidor:
        runs = _textrader(page)
        huvud.append(any(y < 32 + kant and "·" in t and sz < 7.5 for f, sz, x, y, t in runs))
    for nr, page in enumerate(sidor, 1):
        if not huvud[nr - 1]:
            continue
        runs = _textrader(page)
        raster = [(x, y) for f, sz, x, y, t in runs
                  if (abs(sz - 9.4) < .05 or (abs(sz - 8.4) < .05 and "Avenir" in f))
                  and 40 + kant < y < float(page.mediabox.height) - 40 - kant]
        faser = sorted({round((y - kant) % LH, 1) for x, y in raster})
        spalt = {0: [], 1: [], 2: []}
        for x, y in raster:
            c = int((x - x0 + 3) // steg)
            if c in spalt:
                spalt[c].append(y)
        botten = [round((max(v) - kant) / MM, 1) if v else None for v in spalt.values()]
        sista = nr == len(sidor) or not huvud[nr]
        b = [v for v in botten if v is not None]
        fas = [f for f in faser if f not in (0.0, round(LH, 1))]
        ut.append(dict(sida=nr, faser=faser, botten=botten, raster=max(faser) - min(faser) < 0.3 if faser else True,
                       jamn=len(b) == 3 and max(b) - min(b) < 0.5, sista=sista))
    return ut


def _run(*a):
    return subprocess.run(list(a), capture_output=True, text=True).stdout


def bilder(pdf):
    """pdfimages -list: sida, bredd, höjd, färgrymd och effektiv upplösning i tryckt storlek."""
    rader = []
    for ln in _run("pdfimages", "-list", pdf).splitlines()[2:]:
        f = ln.split()
        if len(f) < 14 or f[2] == "smask":
            continue
        rader.append(dict(sida=int(f[0]), nr=int(f[1]), typ=f[2], b=int(f[3]), h=int(f[4]), farg=f[5], xppi=int(f[12]), yppi=int(f[13])))
    return rader


def rapport(here, icc=None, sprak_lista=("sv",)):
    from pypdf import PdfReader
    md = ["# Korpus nr 1 – tryckkontroll", "",
          "Skrivs av `utdata/tidskrift/tryckkontroll.py` (anropas av `bygg_tidskrift.py --tryck`). Tryckeri: Helloprint, "
          "häftade broschyrer A4 (helloprint.com/sv-se/heftadebroschyrer).", ""]
    for sprak in sprak_lista:
        pdf = os.path.join(here, f"Korpus_nr1_{sprak}_tryck.pdf")
        r = PdfReader(pdf)
        p0 = r.pages[0]
        W, H = float(p0.mediabox.width) / MM, float(p0.mediabox.height) / MM
        m0 = [float(v) for v in p0.mediabox]
        tb = [round((float(v) - m0[i % 2]) / MM, 1) for i, v in enumerate(p0.trimbox)]
        bb = [round((float(v) - m0[i % 2]) / MM, 1) for i, v in enumerate(p0.bleedbox)]
        md += [f"## {'Svenska' if sprak == 'sv' else 'Engelska'}: `{os.path.basename(pdf)}`", "",
               f"- Sidor: **{len(r.pages)}** (delbart med 4: {'ja' if len(r.pages) % 4 == 0 else 'NEJ'}).",
               f"- Sidformat: {W:.1f} × {H:.1f} mm = A4 + 3 mm utfall på alla kanter. TrimBox {tb} mm, BleedBox {bb} mm. Inga skärmärken (Helloprint kräver inga; de ska inte ligga i utfallet).",
               ]
        fonts = _run("pdffonts", pdf).splitlines()[2:]
        ej = [f for f in fonts if f.split()[-5:-4] != ["yes"]]
        typs = sorted({f.split()[0].split("+")[-1] for f in fonts})
        md.append(f"- Typsnitt: {len(fonts)} delmängder ({', '.join(typs)}); inbäddade: {'alla' if not ej else 'INTE ALLA: ' + '; '.join(ej)}.")
        # minsta avstånd från text till skärkant
        minst = []
        for nr, (Wp, Hp, lines) in enumerate(_sidor(pdf), 1):
            t = 3 * MM
            for ln in lines:
                d = min(ln["x0"] - t, Wp - t - ln["x1"], ln["y0"] - t, Hp - t - ln["y1"])
                minst.append((d / MM, nr, ln["text"][:40]))
        minst.sort()
        d, nr, txt = minst[0]
        md.append(f"- Text närmast skärkanten: {d:.1f} mm (s. {nr}, ”{txt}”). Kravet är minst 4 mm (Helloprint) / 5 mm (vår regel).")
        under = sorted({(m[1], round(m[0], 1)) for m in minst if m[0] < 5})
        if under:
            md.append(f"  - Text närmare än 5 mm: {under}")
        raw = open(pdf, "rb").read()
        op = len(re.findall(rb"/OP\s+true|/op\s+true", raw))
        md.append(f"- Övertryck: {op} ställen med /OP true (ska vara 0)." if op else "- Övertryck: inget (/OP true saknas i filen).")
        cs = sorted({m.decode() for m in re.findall(rb"/(DeviceRGB|DeviceCMYK|DeviceGray|ICCBased)", raw)})
        md.append(f"- Färgrymder i filen: {', '.join(cs)}." + (" Filen är **RGB** (se nedan)." if not icc else ""))
        md += ["", "### Bilder: effektiv upplösning i tryckt storlek", "",
               "Under 300 dpi markeras; under 200 dpi är ett verkligt problem i tryck.", ""]
        for b in bilder(pdf):
            ppi = min(b["xppi"], b["yppi"])
            flagga = "**PROBLEM < 200 dpi**" if ppi < 200 else "under 300 dpi" if ppi < 300 else "ok"
            md.append(f"- s. {b['sida']:2d} bild {b['nr']}: {b['b']} × {b['h']} px, {b['farg']}, {ppi} dpi – {flagga}")
        md.append("")
    md += ["## Färg: RGB tills tryckeriets profil finns", "",
           "- Helloprint vill ha CMYK med FOGRA39 (ISO Coated v2), total färgmängd högst 300 % (bilder 260 %), liten svart text "
           "som 100 % K. Profilen finns inte på den här datorn (sökt i Ghostscript, /Library/ColorSync, ~/Library/ColorSync och "
           "Adobe-mapparna), så `Korpus_nr1_sv_tryck.pdf` är **RGB** med utfall och boxar. Inget har installerats.",
           "- Förberett i filen: all svart och grå text och alla grå linjer ligger i **DeviceGray** (svart text = ren svart), så "
           "att de går till bara K-plåten vid konverteringen. Rosten (#b7410e) och bilderna är RGB.",
           "- Konverteringen är byggd och provad: `bygg_tidskrift.py --bara-tryck --icc <profil.icc>` skriver "
           "`Korpus_nr1_sv_tryck_cmyk.pdf` som PDF/X-3 med profilen som OutputIntent (Ghostscript, ingen nedsampling). "
           "Provkörd med Ghostscripts egen default_cmyk.icc (inte för tryck): 20 sidor, TrimBox/BleedBox kvar, och "
           "separationerna visar 0 % C, M och Y under all svart text (bara K).",
           "- Att göra före tryck: hämta ECI:s profil **ISOcoated_v2_300_eci.icc** (ISO Coated v2 300 %, FOGRA39, gratis från "
           "eci.org) – den håller 300 %-gränsen – och kör kommandot ovan. Helloprints 260 % för bilder: be tryckeriet "
           "bekräfta om deras preflight gör det, eller använd deras egen profil om de har en.", "",
           "## Papper (förslag för 20 sidor, häftad)", "",
           "- Omslag 250 g/m² bestruket (silk eller gloss), gärna laminerat (matt), och inlaga 135 g/m² (eller 170 g/m² för en "
           "tyngre känsla). Med separat omslag är 20 sidor = 4 omslagssidor + 16 inlagesidor; fråga Helloprint hur de räknar.",
           "- Alternativ: självomslag – alla 20 sidor på samma papper (t.ex. 170 g/m²). Billigare och enklare, men omslaget blir "
           "mjukare och tål mindre.", "",
           "## Baslinjer i brödtexten (skärmversionerna, samma sats som tryck)", "",
           "Varje brödtextsida i tre spalter: alla rader på samma raster (13,5 pt) och spalterna slutar på samma baslinje. "
           "En kortare sista spalt godtas bara på artikelns sista sida.", ""]
    for sprak in ("sv", "en"):
        for s in baslinjer(os.path.join(here, f"Korpus_nr1_{sprak}.pdf")):
            status = "ok" if s["sista"] or (s["raster"] and s["jamn"]) else "AVVIKER"
            md.append(f"- {sprak} s. {s['sida']:2d}: spalternas sista baslinje {s['botten']} mm från sidans överkant; raster "
                      f"{'ett' if s['raster'] else 'FLERA: ' + str(s['faser'])}{' (artikelns sista sida: kortare sista spalt och källor på trekvartsrader godtas)' if s['sista'] else ''} – {status}")
    out = os.path.join(here, "tryck_kontroll.md")
    open(out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(out)
    return out


if __name__ == "__main__":
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1 and sys.argv[1] == "baslinjer":
        for sprak in ("sv", "en"):
            for s in baslinjer(os.path.join(here, f"Korpus_nr1_{sprak}.pdf")):
                print(sprak, s)
    else:
        rapport(here)
