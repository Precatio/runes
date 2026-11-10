"""Litteraturgenomgången, syntes: räknar hur många olika texter som tar upp varje återkommande blind fläck (ur
field_blindspots, vitki_missing, gaps och de mätbara påståendena), och mellan vilka år. Skriver blindflackar.json och
en tabell till stdout. Kategorierna är nyckelordsmönster, satta efter läsningen; en text räknas en gång per kategori.
    python3 utdata/litteraturgenomgang/blindflackar.py"""
import glob, json, os, re
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
KAT = [
 ("Dateringen är cirkulär: stilgrupper utan oberoende fasta punkter", r"cirkul|stilgrupp\w*.{0,40}(datering|daterar|tidsaxel|klocka)|typolog\w*.{0,30}kronolog|fasta punkt|oberoende datering|termini|dendro|C ?14|kol-14|radiokol"),
 ("Bevarande och bortfall styr vilka stenar vi känner", r"bevar|överlev|bortfall|försvunn|förlorad|plöj|bortodl|grustäkt|bortsprängd|survival"),
 ("Flyttade, inmurade och återresta stenar", r"flyttad|flytt|inmur|kyrkmur|återanvän|återrest|sekundär"),
 ("Placeringar prövas inte mot slumpen", r"slump|nollmodell|random|baslinje"),
 ("Fornminnesregistrets täckning är ojämn", r"inventer\w*|registr\w*.{0,30}(täckning|ojämn|fullständ)|fornminnesregist|fornlämningsregist"),
 ("Skattfynd, mynt och silver används inte", r"skattfynd|silverskatt|mynt|dirham|numismat|\bCNS\b"),
 ("Kyrkornas ålder: träkyrkor syns inte", r"träkyrk|kyrk\w*.{0,20}(ålder|byggår|datering)|byggnadsår"),
 ("Centralortsnamnen (Husby, Tuna, Hov) är oprövade", r"husby|husaby|\btuna|\bhov\b|hov-|centralort"),
 ("Tingsplatserna är oprövade", r"tingsplats|tingstad|tingshög|domarring|\btinget\b|\bting\b"),
 ("Uppland och Mälardalen som norm", r"uppland\w* som norm|uppländsk\w*.{0,20}norm|mälardal\w*.{0,30}(norm|centr)|som normen"),
 ("Utgivare, antikvarier och dokumentationshistoria", r"utgivar|sveriges runinskrifter|\bSRI\b|editor|dokumentationshistori|antikvari|hadorph|peringskiöld|1600-talets"),
 ("Forskarnas uppmärksamhet är ojämn", r"litteraturhänvisning|litteraturreferens|forskningsuppmärksamhet|uppmärksamhet"),
 ("De ofria, tjänstefolket och hushållet saknas", r"ofri|träl|tjänstefolk|hushåll"),
 ("Kvinnor och barn", r"kvinn|döttrar|\bdotter|\bbarn"),
 ("Gravhällar, medeltida runor och lösföremål används inte", r"gravhäll|medeltida run|lösföremål|runpinne|föremålstyp"),
 ("Korset läses som tro utan prövning; korstypologin oanvänd", r"korstyp|korsform|korset som|kors\w*.{0,30}(tro|markör|bekännelse)"),
 ("Strandlinje, landhöjning och vattennivå", r"strandlinje|landhöjning|vattenstånd|sjösänkning|mälarens nivå"),
 ("Stenens bergart och proveniens", r"berggrund|bergart|proveniens|stenbrott|lokal sten"),
 ("Vägarnas ålder och vintervägar", r"vägarnas ålder|vägens ålder|hålväg|vinterväg|isväg|daterade vägar"),
 ("Gravfältens ålder och samtidighet med stenen", r"gravfält\w*.{0,25}(ålder|samtid|odaterad|daterad)|samtidig"),
 ("Socken-, härads- och landskapsgränser är yngre än stenarna", r"anakronis|socken\w*.{0,40}(yngre|senare|medeltid)|landskapsgräns|moderna gräns|gränser\w*.{0,20}(yngre|sena)"),
 ("Naturvetenskapliga metoder (isotoper, DNA, pollen, fosfat, LiDAR)", r"isotop|strontium|\baDNA\b|\bDNA\b|pollen|fosfat|lidar|georadar"),
 ("Ristartillskrivning utan basfrekvens", r"tillskriv|attribu|kännarskap|mästarnamn|verkstad"),
 ("Stenarna läses som befolkning eller rikedom utan nämnare", r"befolkning|rikedom|välstånd|nämnare"),
 ("Norrland, samer och periferin", r"\bsame|samisk|norrland|periferi"),
 ("Färg och ommålning", r"målade|\bmålad\b|pigment|ommålning|färgspår"),
 ("Sena källor (sagor, lagar, Adam) som facit", r"\bsaga|snorre|landskapslag|sena källor|adam av bremen"),
 ("Regional eftersläpning i stil och kristnande", r"eftersläp|fördröjning|periferin.{0,30}senare"),
]
RX = [(k, re.compile(p, re.I)) for k, p in KAT]

def text_of(r):
    parts = [r.get("summary_sv") or ""]
    for b in r.get("field_blindspots") or []:
        parts.append(" ".join(str(v) for v in b.values()) if isinstance(b, dict) else str(b))
    parts += [str(x) for x in (r.get("vitki_missing") or []) + (r.get("gaps") or [])]
    for c in r.get("claims") or []:
        parts.append(f"{c.get('claim','')} {c.get('how','')}")
    return " ".join(parts)

def main():
    seen, arts = set(), []
    for f in sorted(glob.glob(os.path.join(HERE, "fynd2", "*.jsonl"))) + sorted(glob.glob(os.path.join(HERE, "fynd", "*.jsonl"))):
        for l in open(f, encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                if r["key"] not in seen:
                    seen.add(r["key"]); r["_b"] = os.path.basename(f)[:-6]; arts.append(r)
    res = defaultdict(list)
    for r in arts:
        t = text_of(r)
        for k, rx in RX:
            if rx.search(t):
                res[k].append(r)
    out = []
    for k, _ in KAT:
        rs = res[k]
        yrs = sorted(int(str(r.get("year"))[:4]) for r in rs if str(r.get("year", ""))[:4].isdigit())
        dec = defaultdict(int)
        for y in yrs: dec[f"{y//10*10}"] += 1
        tiers = defaultdict(int)
        for r in rs:
            tiers["run" if r.get("journal") == "futhark" or not r["_b"].startswith(("fvg", "fvn")) else ("grann" if r["_b"].startswith("fvg") else "nara")] += 1
        first = sorted(rs, key=lambda r: str(r.get("year")))[:3]
        out.append(dict(kategori=k, texter=len(rs), andel=round(100 * len(rs) / len(arts), 1), forsta=yrs[0] if yrs else None,
                        sista=yrs[-1] if yrs else None, nivaer=dict(tiers), decennier=dict(dec),
                        tidigast=[f"{(r.get('authors') or ['?'])[0] if isinstance(r.get('authors'), list) else r.get('authors')} {r.get('year')} ({r['key']})" for r in first]))
    out.sort(key=lambda x: -x["texter"])
    json.dump(dict(texter=len(arts), kategorier=out), open(os.path.join(HERE, "blindflackar.json"), "w"), ensure_ascii=False, indent=1)
    print(len(arts), "texter")
    for x in out:
        print(f"{x['texter']:5d} {x['andel']:5.1f}% {x['forsta']}–{x['sista']}  {x['kategori']}  {x['nivaer']}")

if __name__ == "__main__":
    main()
