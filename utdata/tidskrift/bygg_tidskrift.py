"""Förslag till Vitkis tidskrift (Viktor 2026-11-10: en egen tidskrift likt Futhark och Fornvännen, men för digital
forskning som Vitkis, tillgänglig för den som inte kan lägga all sin tid på att läsa; ljus, fräsch, professionell; PDF.
Version 2 samma dag: mer tidskrift – "tänk Populär Historia fast lite mer återhållsam" – och fler namnförslag).
Bygger ett provnummer av tre publicerade artiklar (utdata/blogg/*.json) som HTML och skriver ut det till PDF med Chrome,
i två varv så att innehållsförteckningen får rätt sidnummer. Skriver också ett blad med namnförslag.
    python3 utdata/tidskrift/bygg_tidskrift.py"""
import html
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BLOGG = os.path.join(HERE, "..", "blogg")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WM = "https://upload.wikimedia.org/wikipedia/commons/"

ARTIKLAR = [  # fil, tema, siffran, vad siffran betyder, öppningsbild (fil i Commons, fotokredit), lyftcitat
    dict(fil="dottrar.json", tema="Människorna", siffra="1 på 19", bilder=1,
         betyder="Så många stenar är resta efter en dotter för varje sten efter en son.",
         bild=("5/5f/U29%2C_Hillersjoh%C3%A4llen.jpg", "U 29, Hillersjöhällen i Uppland: en hel släkts historia i en ristning.",
               "Foto via Wikimedia Commons, se artikelns bildkälla på vitkirunor.se."),
         citat="Ändå är det nitton gånger så många stenar efter söner som efter döttrar."),
    dict(fil="unga.json", tema="Resorna", siffra="3–4 ×",
         betyder="Så mycket oftare dog söner och bröder utanför Norden än fäder och makar.",
         bild=("e/ec/Vg_61%2C_H%C3%A4rlingstorp.JPG", "Vg 61 vid Härlingstorp i Västergötland.",
               "Foto via Wikimedia Commons, se artikelns bildkälla på vitkirunor.se."),
         citat="Den unge mannen var drengr, en i följet; den äldre var þegn, en man med gård och ansvar."),
    dict(fil="overlevde.json", tema="Språket", siffra="1 av 5",
         betyder="Så stor del av namnen på runstenarna bärs fortfarande av svenskar i dag.",
         bild=("c/c3/Lorenz_Fr%C3%B8lich_-_%C3%86sir-Thor_-_NMH_425-1925_-_Nationalmuseum.jpg",
               "Tor, tecknad av Lorenz Frølich.", "Nationalmuseum, public domain, via Wikimedia Commons."),
         citat="Drengr, hjälten, blev dräng."),
]


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    return s


def caption(cap):
    c = inline(cap)
    m = re.match(r"([^:]{3,70}):(.*)", c, re.S)  # bildtextens början i fetstil, som i en tidskrift
    return f"<b>{m.group(1)}:</b>{m.group(2)}" if m else c


def chart(block):
    lines = [l for l in block.split("\n") if l.strip()]
    out = [f'<figure class="chart"><figcaption class="ctitle">{inline(lines[0])}</figcaption>']
    source = ""
    for l in lines[1:]:
        if l.startswith("Källa"):
            source = l
            continue
        if l.startswith("#"):
            out.append(f'<div class="cgroup">{inline(l.lstrip("# "))}</div>')
            continue
        parts = [p.strip() for p in l.lstrip("+").split("|")]
        if len(parts) < 2:
            continue
        val = float(parts[1].replace(",", "."))
        note = parts[2] if len(parts) > 2 else ""
        out.append(f'<div class="crow{" hi" if l.startswith("+") else ""}"><div class="clab">{inline(parts[0])}</div>'
                   f'<div class="cbar"><span style="width:{max(val, 0.8):.1f}%"></span></div>'
                   f'<div class="cval">{val:g} %</div><div class="cnote">{inline(note)}</div></div>')
    if source:
        out.append(f'<div class="csrc">{inline(source)}</div>')
    return "\n".join(out + ["</figure>"])


def body_html(body, skip_img, citat, max_images=2):
    """BlogBody-markeringen till tidskriftens HTML. Första rutan ('Kort sagt') blir 30-sekundersrutan på öppningssidan;
    'Det viktigaste i korthet' tas bort (upprepar början); anfang på första stycket; lyftcitat efter tredje stycket;
    källavsnitten i liten stil."""
    kort, parts, imgs, nparas, tail = None, [], 0, 0, False
    for b in re.split(r"(:::(?:box|chart)[^\n]*\n.*?\n:::)", body, flags=re.S):
        if b.startswith(":::chart"):
            parts.append(chart(b[len(":::chart"):].rsplit(":::", 1)[0]))
            continue
        if b.startswith(":::box"):
            head, inner = b[len(":::box"):].split("\n", 1)
            head, inner = head.strip(), inner.rsplit(":::", 1)[0]
            items = [inline(l[2:]) for l in inner.split("\n") if l.startswith("- ")]
            text = [inline(l) for l in inner.split("\n") if l.strip() and not l.startswith("- ")]
            if kort is None and head.lower().startswith("kort"):
                kort = items or text
            elif "viktigaste" not in head.lower():
                ul = "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>" if items else ""
                parts.append(f'<aside class="box"><div class="boxh">{inline(head)}</div>'
                             + "".join(f"<p>{t}</p>" for t in text) + ul + "</aside>")
            continue
        lines, i = b.split("\n"), 0
        while i < len(lines):
            l = lines[i].rstrip()
            if not l:
                i += 1
                continue
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", l)
            if m:
                nxt = lines[i + 1] if i + 1 < len(lines) else ""
                cap = nxt if nxt.strip() and not nxt.startswith(("!", "#", ":::")) else ""
                if imgs < max_images and not tail and skip_img not in m.group(2):
                    parts.append(f'<figure class="img"><img src="{m.group(2)}" alt="{html.escape(m.group(1))}">'
                                 f'<figcaption>{caption(cap)}</figcaption></figure>')
                    imgs += 1
                i += 2 if cap else 1
                continue
            if l.startswith("## "):
                h = l[3:]
                if re.match(r"(Källor|Se själv)", h) and not tail:
                    parts.append('<div class="sources">')
                    tail = True
                parts.append(f"<h3>{inline(h)}</h3>")
            elif l.startswith("> "):
                parts.append(f"<blockquote>{inline(l[2:])}</blockquote>")
            elif l.startswith("- "):
                items = []
                while i < len(lines) and lines[i].startswith("- "):
                    items.append(f"<li>{inline(lines[i][2:])}</li>")
                    i += 1
                parts.append("<ul>" + "".join(items) + "</ul>")
                continue
            else:
                runcitat = l.startswith("*") and l.endswith("*")
                cls = ""
                if not tail and not runcitat:
                    nparas += 1
                    cls = ' class="forsta"' if nparas == 1 else ""
                parts.append(f'<p{cls}{" class=runcitat" if runcitat else ""}>{inline(l)}</p>')
                if nparas == 3 and not tail and citat and "pull" not in "".join(parts[-1:]):
                    parts.append(f'<blockquote class="pull">{inline(citat)}</blockquote>')
                    citat = None
            i += 1
    if tail:
        parts.append("</div>")
    return kort or [], "\n".join(parts)


RUNOR = {"f": "M6 2V58M6 22L22 8M6 36L22 22", "u": "M6 58V2L22 18V58", "þ": "M6 2V58M6 18L20 30L6 42",
         "a": "M14 2V58M4 18L24 34", "r": "M6 58V2L20 14L6 28L22 58", "k": "M6 58V2M6 24L22 8"}


def runrad(scale=1.0):
    g = "".join(f'<path transform="translate({i * 34},0)" d="{RUNOR[k]}"/>' for i, k in enumerate("fuþark"))
    return (f'<svg class="runor" viewBox="0 0 204 60" width="{204 * scale:.0f}" height="{60 * scale:.0f}"><g fill="none" '
            f'stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">{g}</g></svg>')


def bygg(arts, sidor):
    css = open(os.path.join(HERE, "runmatt.css"), encoding="utf-8").read()
    for n, a in enumerate(arts, 1):  # löpande sidhuvud med artikelns tema
        css += (f'\n@page b{n} {{ @top-left {{ content: "Runmått · {a["tema"]}"; font: 700 7pt var(--sans); color: #b7410e; '
                f'letter-spacing: .14em; text-transform: uppercase; }} }}')
    nr = ["01", "02", "03"]
    innehall = "".join(
        f'<li><img src="{WM}{a["bild"][0]}" alt=""><div><span class="ttema">{a["tema"]}</span>'
        f'<span class="ttitle">{html.escape(a["title"])}</span><span class="tdeck">{a["betyder"]}</span></div>'
        f'<span class="tsida">{sidor.get(a["title"], "")}</span></li>' for a in arts)
    art_html = []
    for n, a in enumerate(arts, 1):
        kort = "".join(f"<li>{k}</li>" for k in a["kort"])
        art_html.append(f"""
<section class="opener">
  <figure class="hero"><img src="{WM}{a["bild"][0]}" alt=""><figcaption>{a["hero_cap"]}</figcaption></figure>
  <div class="opentext">
    <div class="flik">{nr[n - 1]} · {a["tema"]}</div>
    <h2>{html.escape(a["title"])}</h2>
    <p class="deck">{inline(a["summary"])}</p>
    <p class="byline">Text: Viktor Kvant · Lästid {a["minuter"]} minuter</p>
    <div class="snabb">
      <div class="siffran"><div class="slab">Siffran</div><div class="snum">{a["siffra"]}</div><p>{a["betyder"]}</p></div>
      <div class="trettio"><div class="slab">På 30 sekunder</div><ul>{kort}</ul></div>
    </div>
  </div>
</section>
<section class="brodtext b{n}">
  <div class="text">{a["body"]}<p class="slut">■</p>
  <p class="webb">Hela artikeln med alla bilder, interaktiva diagram och data: <b>vitkirunor.se/artiklar/{a["slug"]}</b></p></div>
</section>""")
    a0 = arts[0]
    return f"""<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Runmått nr 1 – förslag</title>
<style>{css}</style></head><body>

<section class="omslag">
  <img class="bg" src="{WM}9/9d/U_489%2C_Morby.jpg" alt="">
  <div class="omtopp">
    <div class="mastrad"><span>Nr 1 · November 2026</span><span>En tidskrift från Vitki</span></div>
    <h1>Runmått</h1>
    <div class="undertitel">Digital runforskning – hela korpusen, mätt</div>
  </div>
  <div class="ompuff">
    <div class="ptema">Människorna</div>
    <div class="pnum">14 <i>mot</i> 268</div>
    <div class="ptitel">{html.escape(a0["title"])}</div>
  </div>
  <div class="omband">
    <div><div class="ptema">Resorna</div><div class="pt">{html.escape(arts[1]["title"])}</div><p>Söner och bröder dog borta tre till fyra gånger så ofta som fäder.</p></div>
    <div><div class="ptema">Språket</div><div class="pt">Tor föll, hjälten blev dräng</div><p>Vilka vikinganamn lever kvar – och vilka maktord bytte språk?</p></div>
    <div><div class="ptema">Verkstaden</div><div class="pt">Hundra års runforskning – lästa på en gång</div><p>Drygt 1 000 texter i Fornvännen och Futhark.</p></div>
    <div class="omruna">{runrad(0.55)}<span>Provnummer<br>vitkirunor.se</span></div>
  </div>
  <div class="omkredit">Omslag: U 489 vid Morby, Uppland – Gullaugs bro för dottern Gillaugs själ. Foto: Christine Jewell, CC BY-SA 2.0, via Wikimedia Commons.</div>
</section>

<section class="vanlig ledsida">
  <div class="ledgrid">
    <div class="ledare">
      <div class="slab">Ledare</div>
      <h2>Alla stenar på en gång</h2>
      <p class="ingress">Runforskningen har länge handlat om den enskilda stenen: en läsning, en ristare, ett ord. Det har gett oss ett rikt material. Men det har också gjort att vissa frågor aldrig ställts – frågor som bara går att svara på om man räknar alla stenar på en gång.</p>
      <p class="forsta">Runmått är Vitkis tidskrift för just de frågorna. Vi mäter hela korpusen – drygt 2 300 svenska runstenar – mot jordarter, strandlinjer, ortnamn, gravfält och vägar, och vi prövar varje mönster mot slumpen innan vi kallar det ett fynd. Analysplanen låses innan vi räknar, och när ett resultat inte håller säger vi det.</p>
      <p>I det här numret möter du döttrarna som nästan aldrig fick en sten, de unga männen som inte kom hem från färderna och namnen som fortfarande bärs av svenskar i dag. Bakom varje artikel ligger tusentals stenar – men varje artikel börjar med en.</p>
      <p>Tidskriften är skriven för den som är nyfiken men har ont om tid. Varje artikel kan läsas på trettio sekunder, på fem minuter eller på djupet. Siffrorna förklaras i ord, och alla data finns öppet på vitkirunor.se.</p>
      <p class="sign">Viktor Kvant<br><span>Redaktör</span></p>
    </div>
    <div class="innehallsspalt">
      <div class="slab">I detta nummer</div>
      <ol class="innehall">{innehall}
        <li class="kort"><div><span class="ttema">Verkstaden</span><span class="ttitle">Hundra års runforskning – lästa på en gång</span></div><span class="tsida">{sidor.get("Verkstaden", "")}</span></li>
        <li class="kort"><div><span class="ttema">Metodhörnan</span><span class="ttitle">Vad betyder p = 0,003?</span></div><span class="tsida">{sidor.get("Verkstaden", "")}</span></li>
      </ol>
    </div>
  </div>
  <div class="lasband">
    <div><b>30 sek</b><span>Rubriken, <i>Siffran</i> och <i>På 30 sekunder</i> ger fyndet och hur säkert det är.</span></div>
    <div><b>5 min</b><span>Artikeln: hur vi kom fram till det, med diagram i procent och stenarna som exempel.</span></div>
    <div><b>På djupet</b><span><i>Så säkra är vi</i>, källorna och öppna data på vitkirunor.se.</span></div>
  </div>
</section>

{"".join(art_html)}

<section class="vanlig verkstad">
  <div class="flik">04 · Verkstaden</div>
  <h2>Hundra års runforskning – lästa på en gång</h2>
  <p class="deck">Vi har läst varje text om runor och vikingatid i Fornvännen sedan 1906 och i Futhark sedan starten, och ställt samma fråga till alla: vad har den svenska runforskningen missat?</p>
  <div class="tal">
    <div><b>1 000+</b><span>texter lästa, 1906–2023</span></div>
    <div><b>3 000+</b><span>påståenden som går att mäta mot data</span></div>
    <div><b>1</b><span>fråga ställd till alla: vad har fältet missat?</span></div>
  </div>
  <div class="tvaspalt">
    <div><h3>Det som återkommer</h3><p class="forsta">Samma blinda fläckar dyker upp i text efter text, oberoende av varandra. Stilgrupperna och språket daterar varandra, med få fasta punkter utanför. Placeringar som ”vid vägen” eller ”vid gravfältet” prövas sällan mot slumpvis valda platser i samma bygd. Och de stenar vi känner är de som överlevde plogen, kyrkbyggena och 1600-talets inventerare.</p></div>
    <div><h3>Det vi gör nu</h3><p>Varje återkommande fråga blir en låst analysplan som prövas på hela korpusen. Resultaten kommer här i Runmått – också de som inte håller. Läsningen själv, med citat och källa för varje påstående, publiceras öppet så att andra kan granska den.</p></div>
  </div>
  <div class="metod">
    <div class="flik">05 · Metodhörnan</div>
    <h3>Vad betyder p = 0,003?</h3>
    <p>Det betyder: om det inte fanns något verkligt mönster alls, skulle en lika stor skillnad som den vi ser dyka upp av ren slump ungefär tre gånger på tusen försök. Det är ungefär lika sällsynt som att få krona åtta gånger i rad med ett mynt. Det bevisar inget ensamt – men det säger att slumpen är en dålig förklaring, och att mönstret är värt att ta på allvar.</p>
  </div>
</section>

<section class="vanlig baksida">
  <div class="tvaspalt">
    <div>
      <div class="slab">Om Runmått</div>
      <p>Runmått är en öppen tidskrift för digital och kvantitativ runforskning, utgiven av Vitki. Den samlar Vitkis artiklar, rapporter och metodnotiser i en form som går att läsa på en kaffepaus.</p>
      <div class="slab">Om Vitki</div>
      <p>Vitki är en öppen forskningsplattform för Nordens runinskrifter. Analyserna förregistreras, och kod, data och rapporter publiceras öppet på Zenodo.</p>
    </div>
    <div>
      <div class="slab">Redaktion</div><p>Viktor Kvant, redaktör<br>vitkirunor.se/kontakt</p>
      <div class="slab">Licens</div><p>Texterna får spridas fritt under CC BY 4.0. Bilder från Wikimedia Commons har egna licenser, angivna vid varje bild.</p>
      <div class="slab">Data</div><p>Samnordisk runtextdatabas, Riksantikvarieämbetets Runor, SGU, ISOF och Kulturmiljöregistret. Bearbetning: Vitki.</p>
    </div>
  </div>
  <div class="bakmast">Runmått {runrad(0.5)}<span>Nr 1 · 2026 · Provnummer · ISSN ansöks</span></div>
</section>
</body></html>"""


NAMN = [
    ("Runmått", "Kort och stramt som Futhark och Fornvännen. Säger vad som är nytt: vi mäter runorna."),
    ("Stenarnas tal", "Dubbel betydelse: siffrorna i stenarna och det stenarna säger. Varmast för en bred publik."),
    ("Mätstav", "Runstav och måttstock i ett ord – ristningen och mätningen."),
    ("Ristat & räknat", "Från ristning till siffra. Lätt att minnas, lite lekfullt."),
    ("Korpus", "Fackordet för hela samlingen. Akademiskt och sakligt, minst populärt."),
    ("Hela stenen", "Folkligt och tydligt: hela korpusen, inte bara de berömda stenarna."),
]


def namnblad():
    css = open(os.path.join(HERE, "runmatt.css"), encoding="utf-8").read()
    kort = "".join(f'<div class="namnkort"><div class="nkmast">{html.escape(n)}</div><div class="nksub">Digital runforskning · '
                   f'en tidskrift från Vitki</div><p>{html.escape(t)}</p></div>' for n, t in NAMN)
    return (f'<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Namnförslag</title><style>{css}</style>'
            f'</head><body><section class="vanlig namnsida"><div class="flik">Namnförslag</div><h2>Sex namn på tidskriften</h2>'
            f'<p class="deck">Samma typsnitt och färg som provnumret, så att namnen går att jämföra som de skulle se ut på omslaget.</p>'
            f'<div class="namngrid">{kort}</div></section></body></html>')


def skriv_pdf(doc, namn):
    h = os.path.join(HERE, namn + ".html")
    open(h, "w", encoding="utf-8").write(doc)
    pdf = os.path.join(HERE, namn + ".pdf")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--hide-scrollbars",
                    "--virtual-time-budget=30000", f"--print-to-pdf={pdf}", "file://" + h], check=True, capture_output=True)
    return pdf


def main():
    arts = []
    for a in ARTIKLAR:
        d = json.load(open(os.path.join(BLOGG, a["fil"]), encoding="utf-8"))
        fn = a["bild"][0].split("/")[-1]
        kort, body = body_html(d["body"], fn, a["citat"], a.get("bilder", 2))
        bl = d["body"].split("\n")  # öppningsbildens bildtext och fotokredit tas ordagrant från artikeln
        cap = next((bl[j + 1] for j, l in enumerate(bl) if l.startswith("![") and fn in l and j + 1 < len(bl)), "")
        a = dict(a, hero_cap=caption(cap) if cap else f"<b>{a['bild'][1]}</b> {a['bild'][2]}")
        arts.append(dict(a, title=d["title"], summary=d["summary"], kort=kort, body=body, slug=d["slug"],
                         minuter=max(1, round(len(d["body"].split()) / 220))))
    # två varv: först utan sidnummer, sedan med sidorna där artiklarna börjar
    pdf = skriv_pdf(bygg(arts, {}), "Runmatt_nr1_forslag")
    sidtext = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True).stdout.split("\f")
    sidor = {}
    for key, needle in [(a["title"], " ".join(a["title"].split()[:2])) for a in arts] + [("Verkstaden", "04 · Verkstaden")]:
        for p, t in enumerate(sidtext[2:], 3):
            if needle in t.replace("\n", " "):
                sidor[key] = p
                break
    print("sidor:", sidor)
    print(skriv_pdf(bygg(arts, sidor), "Runmatt_nr1_forslag"))
    print(skriv_pdf(namnblad(), "Runmatt_namnforslag"))


if __name__ == "__main__":
    main()
