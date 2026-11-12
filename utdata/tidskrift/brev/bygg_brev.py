"""Följebrev till tryckta Korpus nr 1 (Viktor 2026-11-12): ett allmänt och ett till Riksantikvarieämbetet. HTML -> PDF med Chrome."""
import os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
LOGO = "../../../branding/vitki_logo.svg"
ALLM = "Allt i tidningen bygger på ert arbete och på arbetet hos andra som har samlat in, katalogiserat och digitaliserat vårt kulturarv. Det gäller Samnordisk runtextdatabas och Riksantikvarieämbetets register över fornlämningar och runinskrifter, men också årgångarna av Fornvännen och de öppna kartorna."
RAA = "Allt i tidningen bygger på ert arbete och på arbetet hos andra som har samlat in, katalogiserat och digitaliserat vårt kulturarv. Runor och Fornsök är två av de källor vi använder mest, tillsammans med Samnordisk runtextdatabas, årgångarna av Fornvännen och de öppna kartorna."
def stycken(s2):
    return ["Här är första numret av Korpus, en tidskrift om runstenar från Vitki. Lägg den gärna i fikarummet eller där den kan bli läst.",
            s2 + " När materialet är fritt tillgängligt kan man ställa frågor till alla stenar på en gång, och inte bara till en sten i taget. Var stenarna står, vem som reste dem och vilka namn som lever kvar i dag är sådana frågor.",
            "Artiklarna är bara några nedslag i det vi har kunnat utläsa ur materialet. Det mesta finns i appen Vitki på <b>vitkirunor.se</b>, där det går att utforska varje sten, pröva egna frågor mot hela korpusen och se kartor, diagram och källor. Allt är fritt och öppet.",
            "Tack för det arbete som gör det här möjligt. Hör gärna av er om ni har synpunkter, frågor eller vill ha fler exemplar."]
CSS = """
@page { size: A4; margin: 0; }
:root { --rust: #b7410e; --ink: #1d2226; --mute: #5b646b; --serif: "Charter", "Iowan Old Style", Georgia, serif; --sans: "Avenir Next", "Helvetica Neue", Arial, sans-serif; }
html, body { margin: 0; } body { width: 210mm; height: 297mm; position: relative; color: var(--ink); background: #fff; }
.topp { position: absolute; left: 25mm; right: 25mm; top: 22mm; display: flex; align-items: flex-end; justify-content: space-between; border-bottom: 1.4pt solid var(--rust); padding-bottom: 4mm; }
.mast { font: 900 30pt/1 var(--serif); letter-spacing: -.01em; }
.mast small { display: block; font: 600 8.5pt var(--sans); letter-spacing: .02em; color: var(--mute); margin-top: 2.5mm; }
.topp img { height: 22mm; margin-bottom: -2mm; }
.brev { position: absolute; left: 25mm; right: 25mm; top: 62mm; font: 400 11pt/1.6 var(--serif); }
.datum { font: 600 8.5pt var(--sans); letter-spacing: .14em; text-transform: uppercase; color: var(--mute); margin-bottom: 10mm; }
.brev p { margin: 0 0 4.5mm; max-width: 150mm; hyphens: manual; }
.halsning { margin-top: 9mm !important; }
.namn { font: 700 11pt/1.45 var(--serif); margin: 12mm 0 0 !important; }
.titel { font: 400 9.5pt/1.5 var(--sans); color: var(--mute); margin: 0 !important; }
.fot { position: absolute; left: 25mm; right: 25mm; bottom: 18mm; border-top: .6pt solid #d5d9dc; padding-top: 3.5mm; display: flex; justify-content: space-between; font: 600 7.5pt var(--sans); letter-spacing: .14em; text-transform: uppercase; color: var(--mute); }
.fot b { color: var(--rust); }
"""
def html(s2):
    p = "".join(f"<p>{x}</p>" for x in stycken(s2))
    return f"""<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Korpus nr 1 – följebrev</title><style>{CSS}</style></head><body>
<div class="topp"><div class="mast">Korpus<small>Digital runforskning från Vitki</small></div><img src="{LOGO}" alt="Vitki"></div>
<div class="brev"><div class="datum">November 2026</div><p>Hej!</p>{p}
<p class="halsning">Med vänliga hälsningar</p><p class="namn">Viktor Kvant</p><p class="titel">Redaktör, Korpus<br>vitkirunor.se</p></div>
<div class="fot"><span>Korpus nr 1 · November 2026</span><b>vitkirunor.se</b></div></body></html>"""
for namn, s2 in (("Foljebrev_Korpus_nr1", ALLM), ("Foljebrev_Korpus_nr1_RAA", RAA)):
    h = os.path.join(HERE, namn + ".html"); open(h, "w", encoding="utf-8").write(html(s2))
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={os.path.join(HERE, namn + '.pdf')}", "file://" + h],
                   check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    print(namn + ".pdf")
