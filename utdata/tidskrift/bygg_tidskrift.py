"""Vitkis tidskrift Korpus – Ristat & räknat (Viktor 2026-11-10: en egen tidskrift likt Futhark och Fornvännen, men för
digital forskning som Vitkis, för den som inte kan lägga all sin tid på att läsa; ljus, fräsch, professionell, PDF; "tänk
Populär Historia fast lite mer återhållsam"; namnet mellan Korpus och Ristat & räknat; en engelsk utgåva).
Bygger provnumret på svenska och engelska av tre publicerade artiklar (utdata/blogg/*.json, body och body_en) som HTML
och skriver ut dem till PDF med Chrome, i två varv så att innehållsförteckningen får rätt sidnummer. Skriver också en
omslagsjämförelse: Korpus mot Ristat & räknat som titel.
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
OMSLAG = WM + "9/9d/U_489%2C_Morby.jpg"
LOGO = "../../branding/vitki_logo.svg"  # Vitkis bindruna (Viktor 2026-11-10: på omslaget i stället för runraden)

ARTIKLAR = [  # per artikel: fil, öppningsbild i Commons, antal bilder i brödtexten, och per språk tema/siffran/lyftcitat
    dict(fil="dottrar.json", bild="5/5f/U29%2C_Hillersjoh%C3%A4llen.jpg", bilder=1,
         sv=dict(tema="Människorna", siffra="1 på 19", betyder="Så många stenar är resta efter en dotter för varje sten efter en son.",
                 citat="Ändå är det nitton gånger så många stenar efter söner som efter döttrar."),
         en=dict(bilder=0, tema="People", siffra="1 in 19", betyder="That many stones were raised for a daughter for every stone raised for a son.",
                 citat="Yet there are nineteen times as many stones for sons as for daughters.")),
    dict(fil="unga.json", bild="e/ec/Vg_61%2C_H%C3%A4rlingstorp.JPG", bilder=2,
         sv=dict(tema="Resorna", siffra="3–4 ×", betyder="Så mycket oftare dog söner och bröder utanför Norden än fäder och makar.",
                 citat="Den unge mannen var drengr, en i följet; den äldre var þegn, en man med gård och ansvar."),
         en=dict(bilder=0, tema="Journeys", siffra="3–4 ×", betyder="That much more often sons and brothers died outside the Nordic lands than fathers and husbands.",
                 citat="The young man was a drengr, one of the following; the older man was a þegn, a man with a farm and responsibilities.")),
    dict(fil="overlevde.json", bild="c/c3/Lorenz_Fr%C3%B8lich_-_%C3%86sir-Thor_-_NMH_425-1925_-_Nationalmuseum.jpg", bilder=2, staende=True,
         sv=dict(tema="Språket", siffra="1 av 5", betyder="Så stor del av namnen på runstenarna bärs fortfarande av svenskar i dag.",
                 citat="Drengr, hjälten, blev dräng."),
         en=dict(tema="Language", siffra="1 in 5", betyder="The share of the names on the runestones still borne by Swedes today.",
                 citat="Drengr, the hero, became dräng, the farmhand.")),
]

T = {
    "sv": dict(
        lang="sv", nr="Nr 1 · November 2026", fran="En tidskrift från Vitki", undertitel="Ristat & räknat – digital runforskning",
        fot="nr 1 · 2026", lastid="Text: Viktor Kvant · Lästid {m} minuter", siffran="Siffran", trettio="På 30 sekunder",
        webb="Hela artikeln med alla bilder, interaktiva diagram och data:",
        omtema="Människorna", omnum="14 <i>mot</i> 268",
        puffar=[("Resorna", None, "Söner och bröder dog borta tre till fyra gånger så ofta som fäder."),
                ("Språket", "Tor föll, hjälten blev dräng", "Vilka vikinganamn lever kvar – och vilka maktord bytte språk?"),
                ("Verkstaden", "Hundra års runforskning – lästa på en gång", "1 081 texter i Fornvännen och Futhark.")],
        provnummer="Provnummer<br>vitkirunor.se",
        omkredit="Omslag: U 489 vid Morby, Uppland – Gullaugs bro för dottern Gillaugs själ. Foto: Christine Jewell, CC BY-SA 2.0, via Wikimedia Commons.",
        ledare="Ledare", ledrubrik="Alla stenar på en gång",
        ledtext=["Runforskningen har länge handlat om den enskilda stenen: en läsning, en ristare, ett ord. Det har gett oss ett rikt material. Men det har också gjort att vissa frågor aldrig ställts – frågor som bara går att svara på om man räknar alla stenar på en gång.",
                 "{namn} är Vitkis tidskrift för just de frågorna. Vi mäter hela korpusen – drygt 2 300 svenska runstenar – mot jordarter, strandlinjer, ortnamn, gravfält och vägar, och vi prövar varje mönster mot slumpen innan vi kallar det ett fynd. Analysplanen låses innan vi räknar, och när ett resultat inte håller säger vi det.",
                 "I det här numret möter du döttrarna som nästan aldrig fick en sten, de unga männen som inte kom hem från färderna och namnen som fortfarande bärs av svenskar i dag. Bakom varje artikel ligger tusentals stenar – men varje artikel börjar med en.",
                 "Tidskriften är skriven för den som är nyfiken men har ont om tid. Varje artikel kan läsas på trettio sekunder, på fem minuter eller på djupet. Siffrorna förklaras i ord, och alla data finns öppet på vitkirunor.se."],
        sign="Viktor Kvant<br><span>Redaktör</span>", innehall="I detta nummer",
        extra=[("Verkstaden", "Hundra års runforskning – lästa på en gång"), ("Metodhörnan", "Vad betyder p = 0,003?")],
        lasband=[("30 sek", "Rubriken, <i>Siffran</i> och <i>På 30 sekunder</i> ger fyndet och hur säkert det är."),
                 ("5 min", "Artikeln: hur vi kom fram till det, med diagram i procent och stenarna som exempel."),
                 ("På djupet", "<i>Så säkra är vi</i>, källorna och öppna data på vitkirunor.se.")],
        vflik="04 · Verkstaden", vrubrik="Hundra års runforskning – lästa på en gång",
        vdeck="Vi har läst varje text om runor och vikingatid i Fornvännen sedan 1906 och i Futhark sedan starten, och ställt samma fråga till alla: vad har den svenska runforskningen missat?",
        tal=[("1 081", "texter lästa, 1906–2023"), ("3 794", "påståenden som går att mäta mot data"), ("1", "fråga ställd till alla: vad har fältet missat?")],
        v1=("Det som återkommer", "Samma blinda fläckar dyker upp i text efter text, oberoende av varandra. Stilgrupperna och språket daterar varandra, med få fasta punkter utanför. Placeringar som ”vid vägen” eller ”vid gravfältet” prövas sällan mot slumpvis valda platser i samma bygd. Och de stenar vi känner är de som överlevde plogen, kyrkbyggena och 1600-talets inventerare."),
        v2=("Det vi gör nu", "Varje återkommande fråga blir en låst analysplan som prövas på hela korpusen. Resultaten kommer här i {namn} – också de som inte håller. Läsningen själv, med citat och källa för varje påstående, publiceras öppet så att andra kan granska den."),
        mflik="05 · Metodhörnan", mrubrik="Vad betyder p = 0,003?",
        mtext="Det betyder: om det inte fanns något verkligt mönster alls, skulle en lika stor skillnad som den vi ser dyka upp av ren slump ungefär tre gånger på tusen försök. Det är ungefär lika sällsynt som att få krona åtta gånger i rad med ett mynt. Det bevisar inget ensamt – men det säger att slumpen är en dålig förklaring, och att mönstret är värt att ta på allvar.",
        bak=[("Om {namn}", "{namn} är en öppen tidskrift för digital och kvantitativ runforskning, utgiven av Vitki. Den samlar Vitkis artiklar, rapporter och metodnotiser i en form som går att läsa på en kaffepaus. Den kommer ut på svenska och engelska."),
             ("Om Vitki", "Vitki är en öppen forskningsplattform för Nordens runinskrifter. Analyserna förregistreras, och kod, data och rapporter publiceras öppet på Zenodo."),
             ("Redaktion", "Viktor Kvant, redaktör<br>vitkirunor.se/kontakt"),
             ("Licens", "Texterna får spridas fritt under CC BY 4.0. Bilder från Wikimedia Commons har egna licenser, angivna vid varje bild."),
             ("Data", "Samnordisk runtextdatabas, Riksantikvarieämbetets Runor, SGU, ISOF och Kulturmiljöregistret. Bearbetning: Vitki.")],
        bakrad="Nr 1 · 2026 · Provnummer",
    ),
    "en": dict(
        lang="en", nr="No. 1 · November 2026", fran="A journal from Vitki", undertitel="Carved & counted – digital runic research",
        fot="No. 1 · 2026", lastid="Text: Viktor Kvant · Reading time {m} minutes", siffran="The number", trettio="In 30 seconds",
        webb="The full article with all images, interactive charts and data:",
        omtema="People", omnum="14 <i>to</i> 268",
        puffar=[("Journeys", None, "Sons and brothers died abroad three to four times as often as fathers."),
                ("Language", "Thor fell, the hero became a farmhand", "Which Viking names live on – and which words of power changed language?"),
                ("Workshop", "A century of runic research – read at once", "1,081 texts in Fornvännen and Futhark.")],
        provnummer="Sample issue<br>vitkirunor.se",
        omkredit="Cover: U 489 at Morby, Uppland – Gullaug's bridge for the soul of her daughter Gillaug. Photo: Christine Jewell, CC BY-SA 2.0, via Wikimedia Commons.",
        ledare="Editorial", ledrubrik="Every stone at once",
        ledtext=["Runic research has long been about the single stone: one reading, one carver, one word. That has given us a rich body of knowledge. But it has also left some questions unasked – questions that can only be answered by counting every stone at once.",
                 "{namn} is Vitki's journal for exactly those questions. We measure the whole corpus – more than 2,300 Swedish runestones – against soils, shorelines, place names, grave fields and roads, and we test every pattern against chance before we call it a finding. The analysis plan is locked before we count, and when a result does not hold, we say so.",
                 "In this issue you will meet the daughters who almost never got a stone, the young men who did not come home from their journeys, and the names that Swedes still carry today. Behind every article lie thousands of stones – but every article begins with one.",
                 "The journal is written for the curious reader with little time. Every article can be read in thirty seconds, in five minutes or in depth. The numbers are explained in words, and all data are openly available at vitkirunor.se."],
        sign="Viktor Kvant<br><span>Editor</span>", innehall="In this issue",
        extra=[("Workshop", "A century of runic research – read at once"), ("Method corner", "What does p = 0.003 mean?")],
        lasband=[("30 sec", "The headline, <i>The number</i> and <i>In 30 seconds</i> give you the finding and how certain it is."),
                 ("5 min", "The article: how we got there, with charts in percent and the stones as examples."),
                 ("In depth", "<i>How sure we are</i>, the sources and open data at vitkirunor.se.")],
        vflik="04 · Workshop", vrubrik="A century of runic research – read at once",
        vdeck="We have read every text on runes and the Viking Age in Fornvännen since 1906 and in Futhark since its start, and put the same question to all of them: what has Swedish runic research missed?",
        tal=[("1,081", "texts read, 1906–2023"), ("3,794", "claims that can be measured against data"), ("1", "question put to all of them: what has the field missed?")],
        v1=("What keeps coming back", "The same blind spots appear in text after text, independently of each other. Style groups and language date each other, with few fixed points outside. Placements such as “by the road” or “at the grave field” are rarely tested against randomly chosen places in the same district. And the stones we know are the ones that survived the plough, the church builders and the antiquarians of the 1600s."),
        v2=("What we do now", "Every recurring question becomes a locked analysis plan, tested on the whole corpus. The results will appear here in {namn} – including those that do not hold. The reading itself, with quotation and source for every claim, is published openly so that others can check it."),
        mflik="05 · Method corner", mrubrik="What does p = 0.003 mean?",
        mtext="It means: if there were no real pattern at all, a difference as large as the one we see would turn up by pure chance about three times in a thousand tries. That is about as rare as getting heads eight times in a row with a coin. It proves nothing on its own – but it tells us that chance is a poor explanation, and that the pattern is worth taking seriously.",
        bak=[("About {namn}", "{namn} is an open journal for digital and quantitative runic research, published by Vitki. It gathers Vitki's articles, reports and method notes in a form that can be read over a coffee break. It appears in Swedish and English."),
             ("About Vitki", "Vitki is an open research platform for the runic inscriptions of the Nordic countries. Analyses are pre-registered, and code, data and reports are published openly on Zenodo."),
             ("Editors", "Viktor Kvant, editor<br>vitkirunor.se/kontakt"),
             ("Licence", "Texts may be shared freely under CC BY 4.0. Images from Wikimedia Commons carry their own licences, given with each image."),
             ("Data", "Scandinavian Runic-text Database, the Swedish National Heritage Board's Runor, SGU, ISOF and the Swedish register of ancient monuments. Processing: Vitki.")],
        bakrad="No. 1 · 2026 · Sample issue",
    ),
}


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
        if l.startswith(("Källa", "Source")):
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
    """BlogBody-markeringen till tidskriftens HTML. Första rutan ('Kort sagt'/'In short') blir 30-sekundersrutan på
    öppningssidan; den avslutande sammanfattningsrutan tas bort (upprepar början); anfang på första stycket; lyftcitat
    efter tredje stycket; källavsnitten i liten stil."""
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
            if kort is None and head.lower().startswith(("kort", "in short")):
                kort = items or text
            elif not re.search(r"viktigaste|essentials", head, re.I):
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
                if re.match(r"(Källor|Se själv|Sources|See for yourself)", h) and not tail:
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
                if runcitat:
                    parts.append(f'<p class="runcitat">{inline(l)}</p>')
                else:
                    if not tail:
                        nparas += 1
                    parts.append(f'<p{" class=forsta" if nparas == 1 and not tail else ""}>{inline(l)}</p>')
                    if nparas == 3 and not tail and citat:
                        parts.append(f'<blockquote class="pull">{html.escape(citat)}</blockquote>')
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



SNAP_JS = """<script>
// Baslinjeraster: varje element i brödtexten som inte är vanlig text får en höjd (med marginaler) som är ett helt antal rader.
window.addEventListener('load', () => {
  const LH = 18;  // 13,5 pt
  document.querySelectorAll('.text > figure, .text > aside, .text > blockquote, .text > .sources').forEach(el => {
    el.classList.add('snap');
    const h = el.getBoundingClientRect().height;
    const top = el.previousElementSibling ? LH * 0.5 : 0;
    const total = Math.ceil((h + top) / LH + 0.5) * LH;
    el.style.setProperty('margin-top', top + 'px', 'important');
    el.style.setProperty('margin-bottom', (total - h - top) + 'px', 'important');
  });
  document.body.dataset.snapped = '1';
});
</script>"""


def css_for(L, namn, arts):
    css = open(os.path.join(HERE, "korpus.css"), encoding="utf-8").read()
    css += f'\n@page {{ @bottom-right {{ content: "{namn} {L["fot"]}"; }} }}'
    for n, a in enumerate(arts, 1):  # löpande sidhuvud med artikelns tema
        css += (f'\n@page b{n} {{ @top-left {{ content: "{namn} · {a["tema"]}"; font: 700 7pt var(--sans); color: #b7410e; '
                f'letter-spacing: .14em; text-transform: uppercase; }} }}')
    return css


def omslag(L, namn, arts):
    lang = "lang" if len(namn) > 9 else ""
    p = L["puffar"]
    puffar = "".join(f'<div><div class="ptema">{t}</div><div class="pt">{html.escape(titel or arts[1]["title"])}</div><p>{txt}</p></div>'
                     for t, titel, txt in p)
    return f"""
<section class="omslag">
  <img class="bg" src="{OMSLAG}" alt="">
  <div class="omtopp">
    <div class="mastrad"><span>{L["nr"]}</span><span>{L["fran"]}</span></div>
    <h1 class="{lang}">{html.escape(namn)}</h1>
    <div class="undertitel">{L["undertitel"] if namn == "Korpus" else L["undertitel"].split(" – ", 1)[1].capitalize()}</div>
  </div>
  <div class="ompuff">
    <div class="ptema">{L["omtema"]}</div>
    <div class="pnum">{L["omnum"]}</div>
    <div class="ptitel">{html.escape(arts[0]["title"])}</div>
  </div>
  <div class="omband">{puffar}<div class="omruna"><img class="bindruna" src="{LOGO}" alt="Vitki"><span>{L["provnummer"]}</span></div></div>
  <div class="omkredit">{L["omkredit"]}</div>
</section>"""


def bygg(L, namn, arts, sidor):
    nr = ["01", "02", "03"]
    innehall = "".join(
        f'<li><img src="{WM}{a["bild"]}" alt=""><div><span class="ttema">{a["tema"]}</span>'
        f'<span class="ttitle">{html.escape(a["title"])}</span><span class="tdeck">{a["betyder"]}</span></div>'
        f'<span class="tsida">{sidor.get(a["title"], "")}</span></li>' for a in arts)
    innehall += "".join(f'<li class="kort"><div><span class="ttema">{t}</span><span class="ttitle">{html.escape(r)}</span></div>'
                        f'<span class="tsida">{sidor.get("verkstad", "")}</span></li>' for t, r in L["extra"])
    art_html = []
    for n, a in enumerate(arts, 1):
        kort = "".join(f"<li>{k}</li>" for k in a["kort"])
        art_html.append(f"""
<section class="opener">
  <figure class="hero{" staende" if a.get("staende") else ""}"><img src="{WM}{a["bild"]}" alt=""><figcaption>{a["hero_cap"]}</figcaption></figure>
  <div class="opentext">
    <div class="flik">{nr[n - 1]} · {a["tema"]}</div>
    <h2>{html.escape(a["title"])}</h2>
    <p class="deck">{inline(a["summary"])}</p>
    <p class="byline">{L["lastid"].format(m=a["minuter"])}</p>
    <div class="snabb">
      <div class="siffran"><div class="slab">{L["siffran"]}</div><div class="snum">{a["siffra"]}</div><p>{a["betyder"]}</p></div>
      <div class="trettio"><div class="slab">{L["trettio"]}</div><ul>{kort}</ul></div>
    </div>
  </div>
</section>
<section class="brodtext b{n}">
  <div class="text">{a["body"]}<p class="slut">■</p>
  <p class="webb">{L["webb"]} <b>vitkirunor.se{"/en" if L["lang"] == "en" else ""}/artiklar/{a["slug"]}</b></p></div>
</section>""")
    led = "".join(f'<p{" class=forsta" if i == 1 else ""}>{t.format(namn=namn)}</p>' for i, t in enumerate(L["ledtext"]) if i)
    bak = "".join(f'<div class="bakblock"><div class="slab">{h.format(namn=namn)}</div><p>{t.format(namn=namn)}</p></div>' for h, t in L["bak"])
    return f"""<!doctype html><html lang="{L["lang"]}"><head><meta charset="utf-8"><title>{namn} 1/2026</title>
<style>{css_for(L, namn, arts)}</style>{SNAP_JS}</head><body>
{omslag(L, namn, arts)}
<section class="vanlig ledsida">
  <div class="ledgrid">
    <div class="ledare">
      <div class="slab">{L["ledare"]}</div>
      <h2>{L["ledrubrik"]}</h2>
      <p class="ingress">{L["ledtext"][0]}</p>
      {led}
      <p class="sign">{L["sign"]}</p>
    </div>
    <div class="innehallsspalt"><div class="slab">{L["innehall"]}</div><ol class="innehall">{innehall}</ol></div>
  </div>
  <div class="lasband">{"".join(f"<div><b>{b}</b><span>{s}</span></div>" for b, s in L["lasband"])}</div>
</section>
{"".join(art_html)}
<section class="vanlig verkstad">
  <div class="flik">{L["vflik"]}</div>
  <h2>{L["vrubrik"]}</h2>
  <p class="deck">{L["vdeck"]}</p>
  <div class="tal">{"".join(f"<div><b>{b}</b><span>{s}</span></div>" for b, s in L["tal"])}</div>
  <div class="tvaspalt">
    <div><h3>{L["v1"][0]}</h3><p class="forsta">{L["v1"][1]}</p></div>
    <div><h3>{L["v2"][0]}</h3><p>{L["v2"][1].format(namn=namn)}</p></div>
  </div>
  <div class="metod"><div class="flik">{L["mflik"]}</div><h3>{L["mrubrik"]}</h3><p>{L["mtext"]}</p></div>
</section>
<section class="vanlig baksida">
  <div class="baktext">{bak}</div>
  <div class="bakmast">{html.escape(namn)} <img class="bindruna" src="{LOGO}" alt="Vitki"><span>{L["bakrad"]}</span></div>
</section>
</body></html>"""


def skriv_pdf(doc, namn):
    h = os.path.join(HERE, namn + ".html")
    open(h, "w", encoding="utf-8").write(doc)
    pdf = os.path.join(HERE, namn + ".pdf")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--hide-scrollbars",
                    "--virtual-time-budget=30000", f"--print-to-pdf={pdf}", "file://" + h], check=True, capture_output=True)
    return pdf


def artiklar(sprak):
    arts = []
    for a in ARTIKLAR:
        d = json.load(open(os.path.join(BLOGG, a["fil"]), encoding="utf-8"))
        suf = "_en" if sprak == "en" else ""
        body = d["body" + suf]
        fn = a["bild"].split("/")[-1]
        L = a[sprak]
        kort, html_body = body_html(body, fn, L["citat"], L.get("bilder", a["bilder"]))
        bl = body.split("\n")  # öppningsbildens bildtext och fotokredit tas ordagrant från artikeln
        cap = next((bl[j + 1] for j, l in enumerate(bl) if l.startswith("![") and fn in l and j + 1 < len(bl)), "")
        arts.append(dict(L, bild=a["bild"], staende=a.get("staende", False), hero_cap=caption(cap), title=d["title" + suf], summary=d["summary" + suf],
                         kort=kort, body=html_body, slug=d["slug"], minuter=max(1, round(len(body.split()) / 220))))
    return arts


def utgava(sprak, namn="Korpus"):
    L, arts = T[sprak], artiklar(sprak)
    fil = f"Korpus_nr1_{sprak}"
    pdf = skriv_pdf(bygg(L, namn, arts, {}), fil)  # varv 1: utan sidnummer
    sidtext = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True).stdout.split("\f")
    sidor = {}
    for key, needle in [(a["title"], " ".join(a["title"].split()[:2])) for a in arts] + [("verkstad", L["vflik"])]:
        for p, t in enumerate(sidtext[2:], 3):
            if needle in t.replace("\n", " "):
                sidor[key] = p
                break
    print(sprak, "sidor:", sidor)
    return skriv_pdf(bygg(L, namn, arts, sidor), fil)  # varv 2: med sidnummer


def jamforelse():
    """Omslagen sida vid sida: Korpus och Ristat & räknat som titel, och Korpus på engelska."""
    sv, en = artiklar("sv"), artiklar("en")
    css = open(os.path.join(HERE, "korpus.css"), encoding="utf-8").read()
    doc = (f'<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Omslag</title><style>{css}</style></head><body>'
           + omslag(T["sv"], "Korpus", sv) + omslag(T["sv"], "Ristat & räknat", sv) + omslag(T["en"], "Korpus", en)
           + "</body></html>")
    return skriv_pdf(doc, "Omslag_Korpus_eller_Ristat")


if __name__ == "__main__":
    print(utgava("sv"))
    print(utgava("en"))
    print(jamforelse())
