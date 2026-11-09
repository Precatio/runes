"""Litteraturgenomgången: alla forskningsidéer ur läsningarna, ordnade per tema (Viktor 2026-11-09: "skriv ner alla idéer
om vad vi ska forska kring i allt material vi går igenom"). Läser fynd2/ och fynd/ (fynd2 vinner), sorterar varje idé och
varje fältblindfläck till ett tema med nyckelord, räknar hur många olika texter som tar upp temat och skriver
FORSKNINGSIDEER.md: först de huvudspår som skrivits för hand (IDEER_HUVUDSPAR.md), sedan temana rangordnade efter antal
texter, sedan alla idéer per tema med källa. Körs om efter varje läsfönster, så växer listan med läsningen.
    python3 utdata/litteraturgenomgang/ideer.py"""
import glob
import json
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

# (tema, nyckelord) – ordningen avgör när en idé passar flera teman: det första som träffar flest ord vinner
THEMES = [
    ("Datering och fasta punkter", r"datering|daterad|kronologi|stilgrupp|Pr ?\d|dendro|terminus|fast punkt|fasta punkter|"
     r"myntdatering|Ingvar|byggår|ålder|C14|kol-14|kronologisk"),
    ("Bevarande, fynd och flyttning", r"bevar|överlev|flyttad|flytt|förlorad|försvunn|kyrkmur|inmurad|återanvän|fragment|"
     r"fyndomständ|upptäck|plöj|fyndbias|survival|bortfall|dubblett|rest igen|återrest"),
    ("Placering i landskapet", r"väg|vad\b|bro\b|broar|gravfält|gräns|placering|vid vattnet|farled|ås\b|åsar|rullstensås|"
     r"slumppunkt|slumpade punkter|synlig|siktlinje|tingsplats|gård|bytomt"),
    ("Mark, geologi och strandlinje", r"lera|leran|jordart|berggrund|bergart|material|granit|sandsten|kalksten|strandlinje|"
     r"landhöjning|pollen|SGU|geolog|odling|åker|sjösänkning|vatten"),
    ("Ristare och verkstäder", r"ristare|ristarn|signatur|signera|verkstad|attribu|hand\b|händer|mästare|Öpir|Åsmund|Fot\b|Balle"),
    ("Människorna: kvinnor, barn, ofria, släkt", r"kvinn|dotter|döttrar|barn|son\b|söner|ofri|träl|bryte|släkt|arv|"
     r"änka|hustru|maka|familj|personnamn|namn"),
    ("Kristnande, kult och religion", r"krist|kors\b|korset|kors|bön|gud hjälpe|kyrk|hedn|Tor\b|Torshammare|kult|gudanamn|"
     r"teofor|biskop|mission|Gud\b|själ"),
    ("Resor och kontakter utåt", r"österled|västerled|England|Grekland|Särkland|Bysans|Ryssland|Gårdarike|resa|resor|färd|"
     r"utland|utvandr|Normandie|Baltikum|Finland|Est"),
    ("Rikedom, handel och silver", r"silver|skatt|mynt|dirham|handel|Birka|Sigtuna|vikt|rikedom|status|elit|storman|"
     r"jordägande|ekonomi"),
    ("Språk, stavning och runformer", r"stavning|ortografi|runform|stungen|prickad|dialekt|ljud|språk|ordförråd|formel|"
     r"vers|fornyrdislag|metrik|nonsens|chiffer|kryptisk|lönnrun|translitter|tolkning|läsning|ord\b|ordet"),
    ("Ornamentik och bild", r"ornament|Urnes|Ringerike|djurhuvud|orm|rundjur|bild|figur|bildsten|Sigurd|ristningsyta|layout"),
    ("Makt, politik och territorier", r"hundare|härad|folkland|kung|husaby|ting\b|tinget|makt|politik|rike|riks|landskap|"
     r"bygd|territori|lag\b|landskapslag|ledung"),
    ("Andra föremål och senare runor", r"gravhäll|medeltida runor|medeltid|lösföremål|runkalender|amulett|bleck|ben\b|"
     r"föremål|dopfunt|kyrkklocka|runpinne|Gotland|bildsten|äldre runrad|urnordisk"),
    ("Forskningens egna vanor och metoder", r"källkritik|urval|forskningshistori|editor|utgåva|SRI|Upplands runinskrifter|"
     r"Uppland som norm|nollmodell|basfrekvens|slump|statistik|metod|cirkel|kvantitativ|antagande|konnässör"),
    ("Jämförelser i Norden och utanför", r"Danmark|dansk|Norge|norsk|Skåne|Bornholm|Island|brittisk|Man\b|Irland|Skottland|"
     r"Tyskland|Hedeby|Jylland"),
]
RX = [(t, re.compile(p, re.I)) for t, p in THEMES]


def theme_of(text):
    best, score = "Övrigt", 0
    for t, rx in RX:
        s = len(set(m.group(0).lower() for m in rx.finditer(text)))
        if s > score:
            best, score = t, s
    return best


def short(a):
    if isinstance(a, list):
        a = "; ".join(a)
    return (a or "").split("(")[0].strip()[:50]


def main():
    seen, arts = set(), []
    for f in sorted(glob.glob(os.path.join(HERE, "fynd2", "*.jsonl"))) + sorted(glob.glob(os.path.join(HERE, "fynd", "*.jsonl"))):
        for line in open(f, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                if r["key"] not in seen:
                    seen.add(r["key"])
                    arts.append(r)
    ideas, texts = defaultdict(list), defaultdict(set)
    for r in arts:
        src = f"{short(r.get('authors'))} {r.get('year')} ({r['key']})"
        for i in r.get("ideas") or []:
            t = theme_of(" ".join(str(i.get(k) or "") for k in ("title_sv", "question", "data", "why")))
            ideas[t].append((i, src))
            texts[t].add(r["key"])
        for b in r.get("field_blindspots") or []:
            s = " ".join(str(v) for v in b.values()) if isinstance(b, dict) else str(b)
            texts[theme_of(s)].add(r["key"])
        for m in r.get("vitki_missing") or []:
            texts[theme_of(str(m))].add(r["key"])
    order = sorted(texts, key=lambda t: -len(texts[t]))
    n_ideas = sum(len(v) for v in ideas.values())
    L = ["# Forskningsidéer ur litteraturgenomgången\n",
         f"Ur {len(arts)} lästa texter i Fornvännen och Futhark: {n_ideas} idéer till artiklar och rapporter. Filen skrivs om av "
         "`ideer.py` efter varje läsfönster; huvudspåren överst skrivs för hand i `IDEER_HUVUDSPAR.md`.\n"]
    hp = os.path.join(HERE, "IDEER_HUVUDSPAR.md")
    if os.path.exists(hp):
        L.append(open(hp, encoding="utf-8").read().strip() + "\n")
    L.append("## Temana, efter hur många texter som tar upp dem\n")
    L.append("Räknat på idéer, fältblindfläckar och det läsarna såg att Vitki saknar; en text räknas en gång per tema.\n")
    for t in order:
        L.append(f"- **{t}**: {len(texts[t])} texter, {len(ideas[t])} idéer")
    for t in order:
        if not ideas[t]:
            continue
        L.append(f"\n## {t} ({len(ideas[t])} idéer)\n")
        for i, src in sorted(ideas[t], key=lambda x: (x[0].get("kind") or "", x[0].get("title_sv") or "")):
            L.append(f"- [{i.get('kind')}] **{i.get('title_sv')}** – {i.get('question')}  \n"
                     f"  Data: {i.get('data')}. Varför: {i.get('why')} – efter {src}")
    open(os.path.join(HERE, "FORSKNINGSIDEER.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(len(arts), "texter,", n_ideas, "idéer;", ", ".join(f"{t} {len(texts[t])}" for t in order))


if __name__ == "__main__":
    main()
