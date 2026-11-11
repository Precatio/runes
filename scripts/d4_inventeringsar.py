"""D4: fornminnesinventeringens år per socken och län (Kulturmiljöregistret, RAÄ, CC0).

    .venv/bin/python -m scripts.d4_inventeringsar text    # läser beskrivningarna i GeoPackagen -> d4_inventering_text.csv
    .venv/bin/python -m scripts.d4_inventeringsar build   # bygger socken- och länstabellerna
    .venv/bin/python -m scripts.d4_inventeringsar check   # tillförlitlighetskontroller (inga runstenar)

Två källor, båda ur registret självt:
1. Fältdatum (scripts/fetch_kmr_faltdatum.py): senaste fältbesöket för ett slumpurval om upp till k lämningar per socken,
   bara poster som är oförändrade sedan migreringen från FMIS 2018. Huvudkällan.
2. Årtal i beskrivningstexten ("inv 1946", "vid revideringsinventeringen 1984", "Förstagångsinventeringen 1952:",
   "1979 års inventering"). Täcker bara ~1–2 % av posterna men ger ibland förstagångsinventeringens år, som
   fältdatumet skriver över när en lämning besöktes igen.

Ingenting räknas här mot runstenarnas placering; runstenssocknarna används bara för att mäta täckningen.

Utdata (git-ignorerade):
    data/raa/d4_inventering_text.csv       en rad per årtalsträff i texten
    data/raa/d4_inventeringsar_socken.csv  en rad per socken (län + socken)
    data/raa/d4_inventeringsar_lan.csv     en rad per län
"""
from __future__ import annotations

import collections
import csv
import json
import os
import re
import sqlite3
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISK = os.path.dirname(ROOT)
GPKG = os.path.join(DISK, "geografi_kallor", "raa", "lamningar_sverige.gpkg")
FALT = os.path.join(DISK, "downloads", "kmr_faltdatum", "faltdatum.jsonl")
RUNSTENAR = os.path.join(ROOT, "data", "raa", "kmr_runstenar.json")
OUT_TEXT = os.path.join(ROOT, "data", "raa", "d4_inventering_text.csv")
OUT_SOCKEN = os.path.join(ROOT, "data", "raa", "d4_inventeringsar_socken.csv")
OUT_LAN = os.path.join(ROOT, "data", "raa", "d4_inventeringsar_lan.csv")

YEAR = r"(1[89]\d\d|20[0-2]\d)"
KW = (r"(förstagångsinventering\w*|första\s+inventering\w*|revideringsinventering\w*|rev\.?\s*inv\w*\.?|"
      r"fornminnesinventering\w*|fornlämningsinventering\w*|fmis-inventering\w*|skog\s+och\s+historia\w*|"
      r"inventering\w*|inventerad\w*|inventerades|inv\.?)")
AFTER = re.compile(r"(?i)\b" + KW + r"(?:\s+(?:år|av\s+[\wåäöÅÄÖ.]+(?:\s+[\wåäöÅÄÖ.]+)?|i\s+fält|på\s+platsen))?"
                   r"[\s:,(]{0,4}" + YEAR + r"\b")
BEFORE = re.compile(r"(?i)\b" + YEAR + r"\s+års\s+" + KW)


def kind(word: str, ctx: str) -> str:
    w = word.lower()
    c = ctx.lower()
    if "skog" in w or "skog och historia" in c:
        return "skog_och_historia"
    if w.startswith("förstagång") or w.startswith("första"):
        return "forsta"
    if w.startswith("rev"):
        return "revidering"
    if w.startswith("fornminnesinv") or w.startswith("fmis") or "raä inv" in c:
        return "fornminnesinventering"
    return "allman"


def text_scan() -> None:
    con = sqlite3.connect(f"file:{GPKG}?mode=ro", uri=True)
    n = hits = 0
    with open(OUT_TEXT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["uuid", "lan", "socken", "lamningstyp", "slag", "ar", "utdrag"])
        q = "select uuid, lan, socken, lamningstyp, beskrivning, antikvariskbedomning_motivering from lamning"
        for uuid, lan, soc, typ, besk, mot in con.execute(q):
            n += 1
            text = " ".join(t for t in (besk, mot) if t)
            if not text:
                continue
            seen = set()
            for rx, yi, ki in ((AFTER, 2, 1), (BEFORE, 1, 2)):
                for m in rx.finditer(text):
                    year = int(m.group(yi))
                    if not 1930 <= year <= 2026:
                        continue
                    ctx = text[max(0, m.start() - 40):m.end() + 10]
                    k = kind(m.group(ki), ctx)
                    if (k, year) in seen:
                        continue
                    seen.add((k, year))
                    hits += 1
                    w.writerow([uuid, lan, soc, typ, k, year, ctx.replace("\n", " ").strip()])
    print(f"{n} poster, {hits} årtalsträffar -> {OUT_TEXT}")


def runestone_parishes() -> set[tuple[str, str]]:
    ids = [r["kmr_id"] for r in json.load(open(RUNSTENAR, encoding="utf-8"))["records"]]
    con = sqlite3.connect(f"file:{GPKG}?mode=ro", uri=True)
    out = set()
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        for lan, soc in con.execute(f"select lan, socken from lamning where uuid in ({','.join('?' * len(chunk))})", chunk):
            for la in (lan or "").split(","):
                for s in (soc or "").split(","):
                    out.add((la.strip(), s.strip()))
    return out


def period(y: int | None) -> str:
    if y is None:
        return ""
    if y < 1974:
        return "forstagang (1938-1973)"
    if y <= 1977:
        return "overlapp (1974-1977)"
    if y <= 2003:
        return "revidering (1978-2003)"
    return "efter 2003"


def main_year(years: list[int]) -> tuple[int | None, float]:
    """Året med flest besök inom ±1 år (en inventering kunde sträcka sig över två fältsäsonger)."""
    if not years:
        return None, 0.0
    best, best_n = None, -1
    for y in sorted(set(years)):
        n = sum(1 for x in years if abs(x - y) <= 1)
        exact = years.count(y)
        if n > best_n or (n == best_n and exact > years.count(best)):
            best, best_n = y, n
    return best, best_n / len(years)


def mode(vals: list[int]) -> int | None:
    if not vals:
        return None
    c = collections.Counter(vals)
    top = max(c.values())
    return min(y for y, k in c.items() if k == top)


OUT_LANDSKAP = os.path.join(ROOT, "data", "raa", "d4_forstagang_landskap.csv")
# Förstagångsinventeringens ordning per landskap, bara det Hyenstrand uttryckligen skriver (Fornvännen 73, 1978,
# s. 69–71, CC BY 4.0; downloads/tidskrifter/fornvannen/text/1978_069.txt). Decennienivå, inte socken.
HYENSTRAND_1978 = [
    ("Gotland", "omkring 1940", 1938, 1942, "Åren omkring 1940 inventerades Gotland och Öland"),
    ("Öland", "omkring 1940", 1938, 1942, "Åren omkring 1940 inventerades Gotland och Öland"),
    ("Småland", "senare 1940-talet", 1944, 1949, "och senare under 1940-talet Småland och Östergötland"),
    ("Östergötland", "senare 1940-talet", 1944, 1949, "och senare under 1940-talet Småland och Östergötland"),
    ("Uppland", "1950-talet", 1950, 1959, "1950-talet, som kom att ägnas Mälarområdet. I landskapen Uppland och Södermanland och Västmanland"),
    ("Södermanland", "1950-talet", 1950, 1959, "1950-talet ... Mälarområdet"),
    ("Västmanland", "1950-talet", 1950, 1959, "1950-talet ... Mälarområdet"),
    ("Norrlands kustlandskap", "1960-talet, klart omkring 1970", 1960, 1971, "Under 1960-talet berördes de norrländska kustlandskapen"),
    ("Dalarna", "1960-talet, klart omkring 1970", 1960, 1971, "Under 1960-talet berördes ... Dalarna; omkring 1970 färdigställdes Norrland–Dalarna"),
    ("Norrlands inland (utom fjällen och nordligaste delarna)", "1960-talet, klart omkring 1970", 1960, 1971, "stora delar av det norrländska inlandet"),
    ("Västergötland (västra Sverige)", "1960-talet", 1960, 1969, "samt västra Sverige ... I Västsverige kom fr. a. bilden av Västergötlands"),
    ("Skåne", "klart omkring 1970", 1965, 1971, "Åren omkring 1970 färdigställdes Norrland–Dalarna samt Skåne och Blekinge"),
    ("Blekinge", "klart omkring 1970", 1965, 1971, "Åren omkring 1970 färdigställdes ... Skåne och Blekinge"),
    ("Bohuslän", "1973–1977", 1973, 1977, "åren 1973–77 slutligen Bohuslän"),
    ("Gotland (revidering)", "från 1974", 1974, None, "Sedan 1974 pågår revidering, bl. a. av Gotland"),
]


def write_landskap() -> None:
    with open(OUT_LANDSKAP, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["omrade", "period_text", "ar_fran_ungefar", "ar_till_ungefar", "citat",
                    "kalla"])
        for r in HYENSTRAND_1978:
            w.writerow([*r, "Hyenstrand 1978, Fornvännen 73 s. 69–71 (CC BY 4.0)"])


def build() -> None:
    write_landskap()
    con = sqlite3.connect(f"file:{GPKG}?mode=ro", uri=True)
    universe: dict[tuple[str, str], list] = {}
    q = ("select lan, socken, count(*), sum(publiceringsdatum like '2018%') from lamning "
         "where socken <> '' and socken not like '%,%' and lan not like '%,%' group by lan, socken")
    for lan, soc, n, n18 in con.execute(q):
        universe[(lan, soc)] = [n, n18]
    con.close()
    falt: dict[tuple[str, str], list] = collections.defaultdict(list)
    if os.path.exists(FALT):
        for line in open(FALT, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            falt[(r["lan"], r["socken"])].append(r)
    text: dict[tuple[str, str], list] = collections.defaultdict(list)
    for r in csv.DictReader(open(OUT_TEXT, encoding="utf-8")):
        for la in r["lan"].split(","):
            for s in r["socken"].split(","):
                text[(la.strip(), s.strip())].append((r["slag"], int(r["ar"])))
    rs = runestone_parishes()
    cols = ["lan", "socken", "runstenssocken", "n_lamningar", "n_fmis_oforandrade", "n_urval", "n_faltdatum",
            "n_bara_ar", "huvudar", "andel_huvudar", "period", "tidigaste_faltdatum", "senaste_faltdatum",
            "median_faltdatum", "faltdatum_ar", "n_text", "text_forsta", "text_revidering", "text_ovrigt",
            "text_tidigaste", "osakerhet", "anmarkning"]
    rows = []
    for key in sorted(universe):
        lan, soc = key
        recs = falt.get(key, [])
        dates = [r["faltdatum"] for r in recs if r.get("faltdatum")]
        years = sorted(int(d[:4]) for d in dates)
        hy, share = main_year(years)
        t = text.get(key, [])
        tf = [y for k, y in t if k == "forsta"]
        tr = [y for k, y in t if k == "revidering"]
        to = [y for k, y in t if k in ("allman", "fornminnesinventering")]
        notes = []
        n = len(years)
        if n >= 5 and share >= 0.6:
            unc = "låg"
        elif n >= 3 and share >= 0.4:
            unc = "medel"
        elif n >= 1:
            unc = "hög"
        else:
            unc = "saknas"
        if hy and hy > 2003:
            notes.append("huvudåret efter fornminnesinventeringen (länsstyrelse/Skog och historia/uppdrag)")
            if unc == "låg":
                unc = "medel"
        if not recs and universe[key][1] == 0:
            notes.append("inga oförändrade FMIS-poster")
        if 0 < n < 3:
            notes.append("för få fältdatum")
        rows.append({
            "lan": lan, "socken": soc, "runstenssocken": int(key in rs), "n_lamningar": universe[key][0],
            "n_fmis_oforandrade": universe[key][1], "n_urval": len(recs), "n_faltdatum": n,
            "n_bara_ar": sum(1 for d in dates if d[4:] == "-01-01"), "huvudar": hy or "",
            "andel_huvudar": round(share, 2) if years else "", "period": period(hy),
            "tidigaste_faltdatum": min(dates) if dates else "", "senaste_faltdatum": max(dates) if dates else "",
            "median_faltdatum": int(statistics.median(years)) if years else "", "faltdatum_ar": " ".join(map(str, years)),
            "n_text": len(t), "text_forsta": mode(tf) or "", "text_revidering": mode(tr) or "",
            "text_ovrigt": mode(to) or "", "text_tidigaste": min((y for _, y in t), default=""),
            "osakerhet": unc, "anmarkning": "; ".join(notes)})
    with open(OUT_SOCKEN, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    # länstabell
    by_lan = collections.defaultdict(list)
    for r in rows:
        by_lan[r["lan"]].append(r)
    lcols = ["lan", "n_socknar", "n_med_huvudar", "andel_lag_eller_medel_osakerhet", "huvudar_p10", "huvudar_median",
             "huvudar_p90", "andel_forstagang", "andel_overlapp", "andel_revidering", "andel_efter_2003",
             "text_forsta_median", "n_runstenssocknar", "runstenssocknar_med_huvudar"]
    lrows = []
    for lan in sorted(by_lan):
        rr = by_lan[lan]
        hs = sorted(int(r["huvudar"]) for r in rr if r["huvudar"] != "")
        def q(p):
            return hs[min(len(hs) - 1, int(p * len(hs)))] if hs else ""
        per = collections.Counter(r["period"] for r in rr if r["period"])
        tf = sorted(int(r["text_forsta"]) for r in rr if r["text_forsta"] != "")
        rsr = [r for r in rr if r["runstenssocken"]]
        lrows.append({
            "lan": lan, "n_socknar": len(rr), "n_med_huvudar": len(hs),
            "andel_lag_eller_medel_osakerhet": round(sum(r["osakerhet"] in ("låg", "medel") for r in rr) / len(rr), 2),
            "huvudar_p10": q(0.1), "huvudar_median": q(0.5), "huvudar_p90": q(0.9),
            "andel_forstagang": round(per["forstagang (1938-1973)"] / max(1, len(hs)), 2),
            "andel_overlapp": round(per["overlapp (1974-1977)"] / max(1, len(hs)), 2),
            "andel_revidering": round(per["revidering (1978-2003)"] / max(1, len(hs)), 2),
            "andel_efter_2003": round(per["efter 2003"] / max(1, len(hs)), 2),
            "text_forsta_median": tf[len(tf) // 2] if tf else "", "n_runstenssocknar": len(rsr),
            "runstenssocknar_med_huvudar": sum(r["huvudar"] != "" for r in rsr)})
    with open(OUT_LAN, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=lcols)
        w.writeheader()
        w.writerows(lrows)
    # täckning
    rsp = [r for r in rows if r["runstenssocken"]]
    print(f"socknar {len(rows)}, med huvudår {sum(r['huvudar'] != '' for r in rows)}")
    print(f"runstenssocknar (enkel socken) {len(rsp)} av {len(rs)} par; med huvudår {sum(r['huvudar'] != '' for r in rsp)}; "
          f"låg/medel osäkerhet {sum(r['osakerhet'] in ('låg', 'medel') for r in rsp)}; "
          f"med textårtal {sum(r['n_text'] > 0 for r in rsp)}; med förstagångsår i text {sum(r['text_forsta'] != '' for r in rsp)}")
    missing = sorted(p for p in rs if p not in universe)
    print(f"runstenssocknar utan egen post i universum: {len(missing)}: {missing[:15]}")


def check() -> None:
    """Tillförlitlighet utan runstenar: (a) delat urval – stämmer huvudåret ur poster 1–3 med det ur poster 4–6 i
    samma socken? (b) stämmer huvudåret med revideringsåret som beskrivningstexten anger i samma socken?"""
    by = collections.defaultdict(list)
    for line in open(FALT, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        if r.get("faltdatum"):
            by[(r["lan"], r["socken"])].append(int(r["faltdatum"][:4]))
    agree = tot = 0
    diffs = []
    for ys in by.values():
        if len(ys) >= 6:
            a, _ = main_year(ys[:3])
            b, _ = main_year(ys[3:6])
            tot += 1
            agree += abs(a - b) <= 1
            diffs.append(abs(a - b))
    print(f"(a) delat urval, socknar med 6 fältdatum: {tot}; huvudår inom ±1 år: {agree} ({agree / max(1, tot):.0%}); "
          f"median skillnad {statistics.median(diffs) if diffs else ''} år")
    rows = list(csv.DictReader(open(OUT_SOCKEN, encoding="utf-8")))
    both = [r for r in rows if r["huvudar"] and r["text_revidering"]]
    ok = sum(abs(int(r["huvudar"]) - int(r["text_revidering"])) <= 1 for r in both)
    near = sum(abs(int(r["huvudar"]) - int(r["text_revidering"])) <= 3 for r in both)
    print(f"(b) socknar med både huvudår och revideringsår i texten: {len(both)}; inom ±1 år: {ok} "
          f"({ok / max(1, len(both)):.0%}); inom ±3 år: {near} ({near / max(1, len(both)):.0%})")
    gl = [r for r in rows if r["lan"] == "Gotland" and r["text_tidigaste"]]
    early = sum(1938 <= int(r["text_tidigaste"]) <= 1942 for r in gl)
    print(f"(c) Gotland: socknar med textårtal {len(gl)}, tidigaste årtal 1938–1942 (Hyenstrand: omkring 1940): {early}")


if __name__ == "__main__":
    {"text": text_scan, "build": build, "check": check}[sys.argv[1] if len(sys.argv) > 1 else "build"]()
