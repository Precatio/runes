"""Williams 1990 (Åsrunan, Runrön 3), Bilaga "Inskrifter med genealogiskt samband", s. 185–187: förteckningen avskriven
för hand ur skanningen (/Volumes/2TB/litteratur/williams1990.pdf, PDF-sidorna 187–189, läst i 220 dpi 2026-11-01), en
rad per grupp exakt som i boken. Notation (Williams s. 185): "+" förenar inskrifter med samband; inskrifter inom parentes
har ett osäkert samband; står flera inskrifter inom samma parentes är sambandet mellan dem klart. Kursiva
hänvisningsrader ("111 se 68") är inte med, utom där en hänvisning nämner en inskrift som saknas på huvudraden (U Fv1972;172,
se nedan). Öland är inte med hos Williams. Skriver williams1990_bilaga.json.
    .venv/bin/python utdata/slakt/williams1990_bilaga.py"""
import json
import os
import re

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))

LINES = {
    "Ög": ["2+(3)", "4+(5)", "13+(15)", "27+28", "30+(149)+(152)", "32+(147)+(151)", "46+(233)", "68+111", "81+82+83+84+165",
           "93+(94)+(Fv1975;174)", "105+(106)+(107)", "162+Fv1970;310", "187+(189)", "207+(208)", "209+(210)", "234+235+237"],
    "Sö": ["2+(136)+141+(165)", "13+173+374", "14+(15)", "34+35", "45+367", "84+(363)", "92+(183)", "101+106+(U 11+U 16)+U 617",
           "108+(281)", "112+(113)", "134+Fv1948;282", "137+138+Fv1982;235", "160+(162)", "167+(168)", "179+(278)+(279)", "197+203",
           "206+208+(213)", "210+(U 718)", "280+328", "288+(305)", "290+(301)", "292+298+Fv1971;208", "308+(311+312)", "346+(353)",
           "348+(349)", "362+(Fv1958;242)", "Fv1948;289+(Fv1948;295)"],
    "Sm": ["36+37", "76+77", "143+SvS1973;4"],
    "Vg": ["9+12", "11+13", "102+(103)", "130+(139+149)"],
    "U": ["20+21+29+(38)+329+330+331+332", "49+(50)", "57+58", "72+73", "77+78",
          "100+(112)+160+161+225+226+328+336+343+344+364+(Fv1968;279b)",
          "101+(112)+127+135+136+137+140+142+143+147+148+149+150+164+165+212+(216)+(217)+261+(309+310)+(Fv1968;279b)",
          "130+433", "133+141", "144+152+(163)+(312+313+314+315+316)", "146+(214)+(215)", "153+155", "167+170+171", "180+(192)",
          "186+188", "194+203", "209+360", "210+229+231+232", "236+237+238", "240+241", "244+251", "252+(253)", "255+267+268+269",
          "256+(257)", "265+266+Fv1959;188", "273+276+277", "280+281", "285+286", "293+294+(Fv1972;172)", "295+(304)+(305)",
          "297+Fv1953;270+Fv1953;272+Fv1953;274", "302+(319)", "306+307+311", "326+327+(335)", "337+338+341+342", "346+356",
          "347+348", "353+(Fv1978;226)", "358+(Fv1979;244b)", "423+(424)", "429+430", "444+445", "453+454", "457+458+459+(461)",
          "463+(735)", "464+(465)", "472+(473)", "479+480", "496+497", "503+504", "510+511", "513+(517+558)+540", "532+533",
          "565+566", "618+(619)", "621+622", "631+632", "635+636", "640+648", "641+642", "643+644+654", "647+(650)+(744)",
          "668+669", "700+701+723+724", "705+706", "712+713", "762+779", "763+764", "766+767+(780)", "768+1165", "770+1151",
          "789+(790)", "793+(1155)", "821+(839)", "844+845", "851+854", "859+860", "884+885", "901+904", "918+(919)", "922+(925)",
          "937+990+991+999", "945+(958)", "978+(980+981+982)", "1006+(1007)", "1008+(1011+1012)", "1045+1113", "1050+1060",
          "1053+(1117)", "1079+(1087)", "1152+1164"],
    "Vs": ["18+19+20", "27+(28)"],
    "Hs": ["FA33;10+FA33;25"],
}
NOTES = {"U 293+294+(Fv1972;172)": "Huvudraden lyder 293+294; U Fv1972;172 står bara i hänvisningsraden 'Fv1972;172 se 293' "
                                    "och räknas här som osäker medlem.",
         "Hs FA33;10+FA33;25": "Signum i Williams form (Fornvännen 1933); översätts till Rundatas signum nedan om det går."}


def parse(prov: str, line: str) -> list[dict]:
    """Members with their bracket group: 0 = outside brackets (sure), k > 0 = the k-th bracket (unsure towards the rest)."""
    out, depth, k, buf = [], 0, 0, ""

    def flush():
        nonlocal buf
        t = buf.strip()
        if t:
            sig = t if re.match(r"^[A-ZÅÄÖ][a-zåäö]? ", t) else f"{prov} {t}"
            out.append({"signum": sig, "bracket": k if depth else 0})
        buf = ""
    for ch in line:
        if ch == "(":
            flush(); depth += 1; k += 1
        elif ch == ")":
            flush(); depth -= 1
        elif ch == "+":
            flush()
        else:
            buf += ch
    flush()
    return out


ins = {x["signum"]: x for x in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}
norm = lambda s: re.sub(r"\s+", "", s).lower()  # noqa: E731
BYN = {norm(s): s for s in ins}
# FA33 = Filologiskt arkiv 33, Jansson 1985 "Två runstenar i Hälsingland: Malsta och Sunnå" (Williams litteraturlista):
# s. 10 Malsta (Hs 14) och s. 25 Sunnå (Hs 15); båda nämner Hroðmundr och He-Gylfi
ALIAS = {"Hs FA33;10": "Hs 14", "Hs FA33;25": "Hs 15"}
groups = []
for prov, lines in LINES.items():
    for line in lines:
        mem = parse(prov, line)
        for m in mem:
            s = m["signum"]
            hit = ALIAS.get(s) or BYN.get(norm(s))
            if hit is None:   # Rundata's later signum: look in alt_signum
                hit = next((k for k, r in ins.items() if norm(s) in {norm(a) for a in re.split(r"[,;]\s*(?=[A-ZÅÄÖ])", r.get("alt_signum") or "")}), None)
            m["rundata"] = hit
            m["object"] = (ins[hit].get("object") if hit else None)
        groups.append({"province": prov, "line": line, "members": mem, "note": NOTES.get(f"{prov} {line}")})
# Pairs: sure when both stones are outside brackets or inside the same bracket
pairs = []
for g in groups:
    m = g["members"]
    for i in range(len(m)):
        for j in range(i + 1, len(m)):
            a, b = m[i], m[j]
            pairs.append({"a": a["rundata"] or a["signum"], "b": b["rundata"] or b["signum"], "line": g["line"],
                          "sure": a["bracket"] == b["bracket"]})
out = {"source": "Williams, H. 1990. Åsrunan. Runrön 3. Uppsala. Bilaga, s. 185–187.", "groups": groups, "pairs": pairs,
       "n_groups": len(groups), "n_members": sum(len(g["members"]) for g in groups), "n_pairs": len(pairs),
       "n_pairs_sure": sum(p["sure"] for p in pairs),
       "unmatched": sorted({m["signum"] for g in groups for m in g["members"] if not m["rundata"]})}
json.dump(out, open(os.path.join(OUT, "williams1990_bilaga.json"), "w"), ensure_ascii=False, indent=1)
print({k: out[k] for k in ("n_groups", "n_members", "n_pairs", "n_pairs_sure", "unmatched")})
