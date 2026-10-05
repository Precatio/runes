"""Avstämning av appens förslag mot andra källor än appens Rundata (version 3.1, 2018).

  Runor (Riksantikvarieämbetet, utgåva 2020)  runor.raa.se – samma runtextdatabas, två år nyare, med ristare,
                                              stilgrupp och litteraturhänvisningar per inskrift
  Wikidata                                    skapare (P170) för runstenar med Rundata-ID (P1261)

Svaren cachas i data/cache/crosscheck/. En förslagen ristare klassas som

  finns redan     källan anger samma ristare – förslaget är inte nytt, men bekräftar metoden
  annan ristare   källan anger en annan ristare
  samma som       källan säger att stenen är gjord av samma (namngivna eller namnlösa) ristare som en annan sten
  nämns           ristaren nämns i en anmärkning (t.ex. "Tidigare tolkad som signerad av Traen")
  saknas          källan anger ingen ristare – förslaget kan vara nytt, men litteraturen bör kontrolleras
"""
from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from src.signum import fold_signum

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.environ.get("CROSSCHECK_CACHE", os.path.join(ROOT, "data", "cache", "crosscheck"))
RUNOR = "https://runor.raa.se/api/snrd"
RUNOR_EDITION = "2020"
RUNOR_WEB = "https://runor.raa.se/"
WIKIDATA = "https://query.wikidata.org/sparql"
UA = {"User-Agent": "Vitki/1.0 (runestone research; https://github.com/Precatio/runes)"}
SAME_AS = re.compile(r"^(?:Troligen |Kanske |Möjligen )?samma (?:som|ristare som) (?:gjort |ristat )?(.+?)\.*$", re.I)
SOURCES = {
    "runor": "Runor, Riksantikvarieämbetet (Samnordisk runtextdatabas, utgåva 2020). https://runor.raa.se",
    "wikidata": "Wikidata, egenskap P170 (skapare) för objekt med Rundata-ID (P1261). https://www.wikidata.org",
}


def enabled() -> bool:
    return os.environ.get("CROSSCHECK_DISABLED", "") not in ("1", "true")


def _path(*parts: str) -> str:
    p = os.path.join(CACHE, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def _safe(signum: str) -> str:
    return re.sub(r"[^\w]+", "_", fold_signum(signum)).strip("_")


# ---- Runor ---------------------------------------------------------------------------------

def runor(signum: str, refresh: bool = False) -> dict | None:
    """Runors uppgifter om en inskrift: ristare, stilgrupp, referenser. None om den inte finns där."""
    path = _path("runor", f"{_safe(signum)}.json")
    if os.path.exists(path) and not refresh:
        data = json.load(open(path, encoding="utf-8"))
        return data or None
    target = fold_signum(signum)
    hits = requests.get(f"{RUNOR}/search", params={"edition_id": RUNOR_EDITION, "search_field": "SIGNUM",
                                                   "matching_text": signum}, headers=UA, timeout=30)
    hits.raise_for_status()
    match = next((h for h in hits.json() if fold_signum(f"{h['signum1']} {h['signum2']}") == target), None)
    out: dict = {}
    if match:
        r = requests.get(f"{RUNOR}/inscriptions/{match['inscription_id']}", params={"edition_id": RUNOR_EDITION},
                         headers=UA, timeout=30)
        r.raise_for_status()
        d = r.json()
        out = {
            "signum": f"{d['signum1']} {d['signum2']}", "id": d["inscription_id"],
            "url": (d.get("uri") or "").replace("http://", "https://") or RUNOR_WEB,
            "carvers": [{"name": c["name"], "attribution": c.get("attribution"), "certain": c.get("certainty")}
                        for c in d.get("carver") or []],
            "style": [s["style"].replace("\xa0", " ") for s in d.get("profile_style") or []],
            "references": [x["reference"].lstrip("$=") for x in d.get("references") or []],
            "edition": RUNOR_EDITION,
        }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    time.sleep(0.15)  # be polite to RAÄ's service
    return out or None


def _expand_signa(text: str, limit: int = 12) -> list[str]:
    """'U 1015 och 1018-1024' -> ['U 1015', 'U 1018', …]; 'U Fv1953;270 och U Fv1979;245' -> båda."""
    out, prefix = [], None
    for part in re.split(r",\s*|\s+och\s+", text):
        part = part.strip().rstrip(".")
        m = re.match(r"^([A-ZÅÄÖ][a-zåäö]?)\s+(.+)$", part)
        if m:
            prefix, rest = m.group(1), m.group(2)
        elif prefix:
            rest = part
        else:
            continue
        rng = re.match(r"^(\d+)\s*[-–]\s*(\d+)$", rest)
        if rng:
            a, b = int(rng.group(1)), int(rng.group(2))
            out += [f"{prefix} {n}" for n in range(a, min(b, a + limit) + 1)]
        else:
            out.append(f"{prefix} {rest}")
    return out[:limit]


def _is_name(text: str) -> bool:
    """Ristarnamn som 'Öpir 1' eller 'Torgöt Fotsarve' – inte anmärkningar som 'En ovan och osäker ristare.'"""
    t = (text or "").strip()
    words = t.split()
    return bool(t) and not t.endswith(".") and len(words) <= 4 and all(w[0].isupper() or w[0].isdigit() for w in words)


def _runor_names(rec: dict | None, depth: int = 0) -> tuple[list[str], list[dict], list[str]]:
    """Namngivna ristare i en Runor-post, 'Samma som gjort X' följt ett steg, och anmärkningar."""
    names, same, notes = [], [], []
    for c in (rec or {}).get("carvers") or []:
        text = (c["name"] or "").strip()
        m = SAME_AS.match(text)
        if m:
            targets = _expand_signa(m.group(1))
            linked_names = []
            if depth == 0:
                for t in targets:
                    try:
                        linked = runor(t)
                    except requests.RequestException:
                        linked = None
                    linked_names += _runor_names(linked, depth + 1)[0] if linked else []
            same.append({"signum": m.group(1).strip().rstrip("."), "targets": targets, "names": linked_names})
            names += linked_names
        elif _is_name(text):
            names.append(text)
        elif text:
            notes.append(text)
    return names, same, notes


# ---- Wikidata ------------------------------------------------------------------------------

def wikidata_creators(refresh: bool = False, max_age_days: int = 7) -> dict[str, list[str]]:
    path = _path("wikidata_creators.json")
    if os.path.exists(path) and not refresh and time.time() - os.path.getmtime(path) < max_age_days * 86400:
        return json.load(open(path, encoding="utf-8"))
    q = ('SELECT ?rid ?creatorLabel WHERE { ?item wdt:P1261 ?rid . ?item wdt:P170 ?creator . '
         'SERVICE wikibase:label { bd:serviceParam wikibase:language "sv,en". } }')
    r = requests.get(WIKIDATA, params={"query": q}, headers={**UA, "Accept": "application/sparql-results+json"},
                     timeout=60)
    r.raise_for_status()
    out: dict[str, list[str]] = {}
    for b in r.json()["results"]["bindings"]:
        out.setdefault(fold_signum(b["rid"]["value"]), []).append(b["creatorLabel"]["value"])
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    return out


def _name_match(a: str, b: str) -> bool:
    """'Öpir 1' ~ 'Öpir'; 'Åsmund' ~ 'Åsmund Kåresson'."""
    na, nb = re.sub(r"\s+\d+$", "", a).lower(), re.sub(r"\s+\d+$", "", b).lower()
    return na == nb or na.split()[0] == nb.split()[0]


# ---- comparison ----------------------------------------------------------------------------

def check(signum: str, suggested: str | None, wikidata: dict[str, list[str]] | None = None,
          fetch: bool = True) -> dict:
    """Jämför ett förslag med Runor 2020 och Wikidata. Utan fetch används bara cachen."""
    out = {"signum": signum, "suggested": suggested, "sources": []}
    rr = None
    path = _path("runor", f"{_safe(signum)}.json")
    if fetch:
        try:
            rr = runor(signum)
        except requests.RequestException as e:
            out["runor_error"] = str(e)[:200]
    elif os.path.exists(path):
        rr = json.load(open(path, encoding="utf-8")) or None
    elif not fetch:
        out["runor_unchecked"] = True
    if rr is not None or os.path.exists(path):
        names, same, notes = _runor_names(rr) if rr else ([], [], [])
        if not rr:
            status, text = "saknas", "Inskriften hittades inte i Runor 2020."
        elif suggested and not names and any(re.search(rf"\b{re.escape(re.sub(r'\s+\d+$', '', suggested))}\b", n)
                                             for n in notes):
            status = "nämns"
            text = f"Runor 2020 nämner {suggested} i en anmärkning: " + " ".join(notes)
        elif suggested and any(_name_match(suggested, n) for n in names):
            via = next((s["signum"] for s in same if any(_name_match(suggested, n) for n in s["names"])), None)
            status = "finns redan"
            text = (f"Runor 2020 anger redan {suggested}" + (f" (via 'samma som {via}')" if via else "") + ".")
        elif names:
            status, text = "annan ristare", f"Runor 2020 anger {', '.join(dict.fromkeys(names))}."
        elif same:
            status = "samma som"
            text = "Runor 2020: samma ristare som " + ", ".join(s["signum"] for s in same) + " (namnlös)."
        else:
            status, text = "saknas", "Runor 2020 anger ingen ristare" + (f" (anmärkning: {' '.join(notes)})" if notes else "") + "."
        out["runor"] = {"status": status, "text": text, "carvers": (rr or {}).get("carvers") or [],
                        "same_as": same, "notes": notes, "references": (rr or {}).get("references") or [],
                        "url": (rr or {}).get("url")}
        out["sources"].append("runor")
    wd = (wikidata or {}).get(fold_signum(signum))
    if wd is not None:
        same_wd = bool(suggested) and any(_name_match(suggested, n) for n in wd)
        out["wikidata"] = {"creators": wd, "status": "finns redan" if same_wd else "annan ristare",
                           "text": f"Wikidata anger {', '.join(wd)}."}
        out["sources"].append("wikidata")
    statuses = [x["status"] for x in (out.get("runor"), out.get("wikidata")) if x]
    order = ("finns redan", "nämns", "annan ristare", "samma som", "saknas")
    out["status"] = next((s_ for s_ in order if s_ in statuses), "ej kontrollerad")
    return out


def check_many(items: list[tuple[str, str | None]], workers: int = 4) -> dict[str, dict]:
    """Kontrollerar många förslag (hämtar det som inte är cachat)."""
    try:
        wd = wikidata_creators()
    except requests.RequestException:
        wd = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(lambda it: check(it[0], it[1], wd), items))
    return {r["signum"]: r for r in results}


def cached(signum: str, suggested: str | None) -> dict | None:
    """Avstämning ur cachen, utan nätverk; None om stenen inte är kontrollerad."""
    if not os.path.exists(_path("runor", f"{_safe(signum)}.json")):
        return None
    wd_path = _path("wikidata_creators.json")
    wd = json.load(open(wd_path, encoding="utf-8")) if os.path.exists(wd_path) else {}
    return check(signum, suggested, wd, fetch=False)



def apply(finding: dict, cc: dict) -> dict:
    """Lägger avstämningen på ett fynd och justerar nyheten: ett förslag som redan finns i en nyare källa är inte nytt."""
    f = dict(finding)
    f["crosscheck"] = cc
    st = cc.get("status")
    if st == "finns redan":
        f["novelty"] = 0.05
        f["score"] = round(f["evidence"] * f["novelty"] * f["relevance"], 3)
        f["assessment"] = "Finns redan i nyare källa – bekräftar metoden"
        f.setdefault("reasons", {}).setdefault("nyhet", []).append(cc["runor"]["text"] if cc.get("runor") else
                                                                    cc["wikidata"]["text"])
    elif st == "annan ristare" and f["verdict"] == "nytt":
        f["assessment"] = "Motsägs av nyare källa – värd en omprövning"
        f.setdefault("reasons", {}).setdefault("nyhet", []).append(
            (cc.get("runor") or {}).get("text") or (cc.get("wikidata") or {}).get("text"))
    elif st == "nämns":
        f["novelty"] = round(min(f["novelty"], 0.3), 3)
        f["score"] = round(f["evidence"] * f["novelty"] * f["relevance"], 3)
        f["assessment"] = "Nämns i nyare källa – oberoende stöd för en äldre tolkning"
        f.setdefault("reasons", {}).setdefault("nyhet", []).append(cc["runor"]["text"])
    elif st in ("saknas", "samma som") and cc.get("runor"):
        f.setdefault("reasons", {}).setdefault("nyhet", []).append(
            cc["runor"]["text"] + (" Litteratur att kontrollera: " + "; ".join(cc["runor"]["references"])
                                   if cc["runor"]["references"] else ""))
    return f
