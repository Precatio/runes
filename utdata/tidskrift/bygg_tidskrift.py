"""Förslag till Vitkis tidskrift (Viktor 2026-11-10: en egen tidskrift likt Futhark och Fornvännen, men för digital
forskning som Vitkis, tillgänglig för den som inte kan lägga all sin tid på att läsa; ljus, fräsch, professionell; PDF).
Bygger ett provnummer av tre publicerade artiklar (utdata/blogg/*.json) som HTML och skriver ut det till PDF med Chrome.
    python3 utdata/tidskrift/bygg_tidskrift.py"""
import html
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BLOGG = os.path.join(HERE, "..", "blogg")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ARTIKLAR = [  # fil, tema, siffran, vad siffran betyder
    ("dottrar.json", "Människorna", "1 på 19",
     "Så många stenar är resta efter en dotter för varje sten efter en son."),
    ("unga.json", "Resorna", "3–4 ×",
     "Så mycket oftare dog söner och bröder utanför Norden än fäder och makar."),
    ("overlevde.json", "Språket", "1 av 5",
     "Så stor del av namnen på runstenarna bärs fortfarande av svenskar i dag."),
]


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    return s


def chart(block):
    lines = [l for l in block.split("\n") if l.strip()]
    title, rows, source = lines[0], [], ""
    out = [f'<figure class="chart"><figcaption class="ctitle">{inline(title)}</figcaption>']
    for l in lines[1:]:
        if l.startswith("Källa"):
            source = l
            continue
        if l.startswith("#"):
            out.append(f'<div class="cgroup">{inline(l.lstrip("# "))}</div>')
            continue
        hi = l.startswith("+")
        parts = [p.strip() for p in l.lstrip("+").split("|")]
        if len(parts) < 2:
            continue
        lab, val = parts[0], float(parts[1].replace(",", "."))
        note = parts[2] if len(parts) > 2 else ""
        out.append(f'<div class="crow{" hi" if hi else ""}"><div class="clab">{inline(lab)}</div>'
                   f'<div class="cbar"><span style="width:{max(val, 0.8):.1f}%"></span></div>'
                   f'<div class="cval">{val:g} %</div><div class="cnote">{inline(note)}</div></div>')
    if source:
        out.append(f'<div class="csrc">{inline(source)}</div>')
    out.append("</figure>")
    return "\n".join(out)


def body_html(body, max_images=2):
    """BlogBody-markeringen till HTML. Första rutan ('Kort sagt') lyfts ut som 30-sekundersrutan; den avslutande
    'Det viktigaste i korthet' tas bort (den upprepar början); källavsnitten sätts i liten stil."""
    kort, parts, imgs = None, [], 0
    blocks = re.split(r"(:::(?:box|chart)[^\n]*\n.*?\n:::)", body, flags=re.S)
    tail = False
    for b in blocks:
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
                continue
            if "viktigaste" in head.lower():
                continue
            ul = "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>" if items else ""
            parts.append(f'<aside class="box"><div class="boxh">{inline(head)}</div>'
                         + "".join(f"<p>{t}</p>" for t in text) + ul + "</aside>")
            continue
        lines = b.split("\n")
        i = 0
        while i < len(lines):
            l = lines[i].rstrip()
            if not l:
                i += 1
                continue
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", l)
            if m:
                cap = lines[i + 1] if i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].startswith("!") else ""
                if imgs < max_images and not tail:
                    parts.append(f'<figure class="img"><img src="{m.group(2)}" alt="{html.escape(m.group(1))}">'
                                 f'<figcaption>{inline(cap)}</figcaption></figure>')
                    imgs += 1
                i += 2 if cap else 1
                continue
            if l.startswith("## "):
                h = l[3:]
                if re.match(r"(Källor|Se själv)", h):
                    if not tail:
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
                parts.append(f"<p>{inline(l)}</p>")
            i += 1
    if tail:
        parts.append("</div>")
    return kort or [], "\n".join(parts)


RUNOR = {  # yngre futharks f u þ a r k som streck (för omslaget)
    "f": "M6 2V58M6 22L22 8M6 36L22 22", "u": "M6 58V2L22 18V58", "þ": "M6 2V58M6 18L20 30L6 42",
    "a": "M14 2V58M4 18L24 34", "r": "M6 58V2L20 14L6 28L22 58", "k": "M6 58V2M6 24L22 8",
}


def runrad(scale=1.0):
    g = []
    for i, k in enumerate("fuþark"):
        g.append(f'<path transform="translate({i * 34},0)" d="{RUNOR[k]}"/>')
    return (f'<svg class="runor" viewBox="0 0 {6 * 34} 60" width="{6 * 34 * scale:.0f}" height="{60 * scale:.0f}">'
            f'<g fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">'
            + "".join(g) + "</g></svg>")


def main():
    arts = []
    for fil, tema, siffra, betyder in ARTIKLAR:
        d = json.load(open(os.path.join(BLOGG, fil), encoding="utf-8"))
        kort, body = body_html(d["body"])
        words = len(d["body"].split())
        arts.append(dict(title=d["title"], summary=d["summary"], tema=tema, siffra=siffra, betyder=betyder,
                         kort=kort, body=body, minuter=max(1, round(words / 220)), slug=d["slug"]))

    innehall = "".join(
        f'<li><span class="tnum">{n}</span><span class="ttema">{a["tema"]}</span>'
        f'<span class="ttitle">{html.escape(a["title"])}</span><span class="tmin">{a["minuter"]} min</span></li>'
        for n, a in zip(("01", "02", "03"), arts))

    art_html = []
    for n, a in zip(("01", "02", "03"), arts):
        kort = "".join(f"<li>{k}</li>" for k in a["kort"])
        art_html.append(f"""
<article class="artikel">
  <header class="opener">
    <div class="kicker"><span>{n} · {a["tema"]}</span><span>Lästid {a["minuter"]} min</span></div>
    <h2>{html.escape(a["title"])}</h2>
    <p class="deck">{inline(a["summary"])}</p>
    <p class="byline">Viktor Kvant · Vitki</p>
  </header>
  <section class="snabb">
    <div class="siffran"><div class="slab">Siffran</div><div class="snum">{a["siffra"]}</div><p>{a["betyder"]}</p></div>
    <div class="trettio"><div class="slab">På 30 sekunder</div><ul>{kort}</ul></div>
  </section>
  <div class="text">{a["body"]}</div>
  <p class="webb">Hela artikeln med alla bilder, interaktiva diagram och data: <strong>vitkirunor.se/artiklar/{a["slug"]}</strong></p>
</article>""")

    doc = f"""<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Runmått nr 1 – förslag</title>
<style>{open(os.path.join(HERE, "runmatt.css"), encoding="utf-8").read()}</style></head><body>

<section class="omslag">
  <div class="mast">
    <div class="mastrad"><span>Vitki</span><span>Nr 1 · November 2026 · Provnummer</span></div>
    <h1>Runmått</h1>
    <div class="undertitel">Tidskrift för digital runforskning</div>
  </div>
  <div class="omslagsrunor">{runrad(1.6)}</div>
  <div class="huvudpuff">
    <div class="pnum">14 <span>mot</span> 268</div>
    <div class="ptext"><div class="ptema">Människorna</div><div class="ptitel">{html.escape(arts[0]["title"])}</div>
      <p>Stenarna efter döttrar mot stenarna efter söner. Där döttrarna syns, syns de på ett eget sätt.</p></div>
  </div>
  <figure class="omslagsbild"><img src="https://thumb.wikimedia.org/wikipedia/commons/thumb/9/9d/U_489%2C_Morby.jpg/1280px-U_489%2C_Morby.jpg" alt="U 489, Morby">
    <figcaption>Omslagsbild: U 489 vid Morby i Lagga socken, Uppland – Gullaugs bro för dottern Gillaugs själ. Foto: Christine Jewell, CC BY-SA 2.0, via Wikimedia Commons.</figcaption></figure>
  <div class="puffar">
    <div><div class="ptema">Resorna</div><div class="ptitel">{html.escape(arts[1]["title"])}</div><p>Söner och bröder dog borta tre till fyra gånger så ofta som fäder.</p></div>
    <div><div class="ptema">Språket</div><div class="ptitel">Tor föll, hjälten blev dräng</div><p>Vilka vikinganamn lever kvar – och vilka maktord bytte språk?</p></div>
    <div><div class="ptema">Verkstaden</div><div class="ptitel">Vi läste hundra års runforskning</div><p>Drygt 1 000 texter i Fornvännen och Futhark, och vad fältet har missat.</p></div>
  </div>
  <div class="omslagsfot">Hela korpusen, mätt · vitkirunor.se</div>
</section>

<section class="sida ledare">
  <div class="tvaspalt">
    <div>
      <div class="slab">Ledare</div>
      <h2 class="lh">Därför Runmått</h2>
      <p class="ingress">Runforskningen har länge handlat om den enskilda stenen: en läsning, en ristare, ett ord. Det har gett oss ett rikt material. Men det har också gjort att vissa frågor aldrig ställts – frågor som bara går att svara på om man räknar alla stenar på en gång.</p>
      <p>Runmått är Vitkis tidskrift för just de frågorna. Vi mäter hela korpusen – drygt 2 300 svenska runstenar – mot jordarter, strandlinjer, ortnamn, gravfält och vägar, och vi prövar varje mönster mot slumpen innan vi kallar det ett fynd. Analysplanen låses innan vi räknar, och när ett resultat inte håller säger vi det.</p>
      <p>Tidskriften är skriven för den som är nyfiken men har ont om tid. Varje artikel kan läsas på tre sätt: på trettio sekunder, på fem minuter eller på djupet. Siffrorna förklaras i ord, och alla data och metoder finns öppet på vitkirunor.se och Zenodo.</p>
      <p class="sign">Viktor Kvant<br><span>Redaktör</span></p>
    </div>
    <div>
      <div class="slab">Så läser du Runmått</div>
      <ol class="lasdjup">
        <li><b>30 sekunder</b><span>Rubriken, Siffran och rutan <i>På 30 sekunder</i> ger dig fyndet och hur säkert det är.</span></li>
        <li><b>5 minuter</b><span>Artikeln berättar hur vi kom fram till det, med diagram i procent och exempel från stenarna.</span></li>
        <li><b>På djupet</b><span>Rutan <i>Så säkra är vi</i>, källorna och data på webben låter dig pröva allt själv.</span></li>
      </ol>
      <div class="slab innehallsrubrik">I detta nummer</div>
      <ol class="innehall">{innehall}
        <li><span class="tnum">04</span><span class="ttema">Verkstaden</span><span class="ttitle">Hundra års runforskning, lästa på en gång</span><span class="tmin">2 min</span></li>
        <li><span class="tnum">05</span><span class="ttema">Metodhörnan</span><span class="ttitle">Vad betyder p = 0,003?</span><span class="tmin">1 min</span></li>
      </ol>
    </div>
  </div>
</section>

{"".join(art_html)}

<section class="sida verkstad">
  <div class="kicker"><span>04 · Verkstaden</span><span>Lästid 2 min</span></div>
  <h2>Hundra års runforskning, lästa på en gång</h2>
  <p class="deck">Vi har läst varje text om runor och vikingatid i Fornvännen sedan 1906 och i Futhark sedan starten – och frågat samma sak av alla: vad har den svenska runforskningen missat?</p>
  <div class="tal">
    <div><b>1 000+</b><span>texter lästa, 1906–2023</span></div>
    <div><b>3 000+</b><span>påståenden som går att mäta mot data</span></div>
    <div><b>1</b><span>fråga ställd till alla: vad har fältet missat?</span></div>
  </div>
  <div class="tvaspalt">
    <div>
      <h3>Det som återkommer</h3>
      <p>Samma blinda fläckar dyker upp i text efter text, oberoende av varandra. Stilgrupperna och språket daterar varandra, med få fasta punkter utanför. Placeringar som ”vid vägen” eller ”vid gravfältet” prövas sällan mot slumpvis valda platser i samma bygd. Och de stenar vi känner är de som överlevde plogen, kyrkbyggena och 1600-talets inventerare.</p>
    </div>
    <div>
      <h3>Det vi gör nu</h3>
      <p>Varje återkommande fråga blir en låst analysplan som prövas på hela korpusen. Resultaten kommer här i Runmått – också de som inte håller. Läsningen själv, med citat och källa för varje påstående, publiceras öppet så att andra kan granska den.</p>
    </div>
  </div>
  <div class="metod">
    <div class="kicker"><span>05 · Metodhörnan</span><span>Lästid 1 min</span></div>
    <h3>Vad betyder p = 0,003?</h3>
    <p>Det betyder: om det inte fanns något verkligt mönster alls, skulle en lika stor skillnad som den vi ser dyka upp av ren slump ungefär tre gånger på tusen försök. Det är ungefär lika sällsynt som att få krona åtta gånger i rad med ett mynt. Det bevisar inget ensamt – men det säger att slumpen är en dålig förklaring, och att mönstret är värt att ta på allvar.</p>
  </div>
</section>

<section class="baksida">
  <div class="tvaspalt">
    <div>
      <div class="slab">Om Runmått</div>
      <p>Runmått är en öppen tidskrift för digital och kvantitativ runforskning, utgiven av Vitki. Den kommer ut med fyra nummer om året och samlar Vitkis artiklar, rapporter och metodnotiser i en form som går att läsa på en kaffepaus.</p>
      <div class="slab">Om Vitki</div>
      <p>Vitki är en öppen forskningsplattform för Nordens runinskrifter. Analyserna förregistreras, och kod, data och rapporter publiceras öppet på Zenodo.</p>
    </div>
    <div>
      <div class="slab">Redaktion</div>
      <p>Viktor Kvant, redaktör<br>vitkirunor.se/kontakt</p>
      <div class="slab">Licens</div>
      <p>Texterna får spridas fritt under CC BY 4.0. Bilder från Wikimedia Commons har egna licenser, angivna vid varje bild.</p>
      <div class="slab">Data</div>
      <p>Samnordisk runtextdatabas, Riksantikvarieämbetets Runor, SGU, ISOF och Kulturmiljöregistret. Bearbetning: Vitki.</p>
    </div>
  </div>
  <div class="bakmast">Runmått {runrad(0.5)}<span>Nr 1 · 2026 · Provnummer · ISSN ansöks</span></div>
</section>
</body></html>"""
    out_html = os.path.join(HERE, "runmatt_nr1.html")
    open(out_html, "w", encoding="utf-8").write(doc)
    pdf = os.path.join(HERE, "Runmatt_nr1_forslag.pdf")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--hide-scrollbars",
                    "--virtual-time-budget=20000", f"--print-to-pdf={pdf}", "file://" + out_html],
                   check=True, capture_output=True)
    print(pdf)


if __name__ == "__main__":
    main()
