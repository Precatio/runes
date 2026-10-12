"""Ämnen för Månadens fynd: de mönster som R-analyserna har hittat och som håller, och ett utkast kring ett av dem.

Kandidaterna är korpusmönstren (src/r_findings.py) som är *mönster att pröva* eller *bekräftar*, har en hypotes och håller i
båda halvorna av korpusen (nya mönster får vara med också när analysen saknar ett prov i halvor). Utkastet följer bloggens mall (rubrik, ingress, "Kort sagt", vad vi
ser med ett diagram när datan finns, "Så säkra är vi", hypotesen, hur den kan prövas, förbehåll, se själv och källor) och
är tänkt att skrivas om med egna ord: siffrorna och resonemangen kommer från appen, berättelsen från skribenten.
"""
from __future__ import annotations

import re

RANK = {"mönster att pröva": 0, "bekräftar": 1}
# Method checks rather than findings about the runestones; they do not make a post of the month
SKIP = {("Attribuering", "model"), ("Datering", "seriation"), ("Språk", "spelling")}
# The change analysis's features under the pattern map's names (src/pattern_map.py), for the link to the map
MAP_ALIAS = {"cross": "kors", "ai_alla": "monoftong", "ai_sten": "monoftong"}
STYLE_YEARS = {"RAK": 1000, "Fp": 1030, "Pr1": 1030, "Pr2": 1035, "Pr3": 1065, "Pr4": 1085, "Pr5": 1115}

WORDS = {
    "sv": {
        "short": "Kort sagt", "see": "Vad vi ser", "sure": "Så säkra är vi", "hyp": "Vår hypotes", "test": "Så kan den prövas",
        "caveats": "Förbehåll", "yourself": "Se själv", "sources": "Källor och data",
        "hyp_bullet": "Vår hypotes", "test_bullet": "Den kan prövas", "both": "Mönstret håller i båda halvorna av korpusen, "
        "uppdelad socken för socken.", "not_both": "Mönstret har inte prövats i båda halvorna, eller håller bara i den ena.",
        "many": "**Många test på en gång.** Mönstret har prövats tillsammans med appens andra mönster och klarar justeringen "
                "för många test ({sig}).",
        "halves": "**Båda halvorna.** Vi delade materialet i två halvor, socken för socken, och mönstret syns i båda var "
                  "för sig.",
        "draws": "**Osäkra årtal.** Stilgruppernas dateringar är ungefärliga; vi räknade om med årtal lottade inom varje "
                 "stilgrupps intervall, och {ok} av {n} omräkningar gav samma resultat.",
        "model": "**Samma ristare, samma trakt.** Modellen jämför stenar av samma ristare och i samma område, så att mönstret "
                 "inte bara är en enskild ristares vana eller en skillnad mellan landskap.",
        "cluster": "**Inte slumpen.** Klustret prövades mot {nsim} slumpvisa omfördelningar av mönstret över stenarna "
                   "(Kulldorffs scanstatistik).",
        "rewrite": "*Utkast: siffrorna och resonemangen kommer från Vitkis analyser. Skriv om texten med egna ord, börja "
                   "gärna med en inskrift som krok och lägg till vad som är nytt jämfört med tidigare forskning.*",
        "map": "Mönstret på [kartan]({href}).",
        "stats": "Modellerna och kurvorna under [Statistik](/statistik) och mönstret med hypotes i "
                 "[Forskningsluckor](/luckor); metoden i [Metodik och beräkningar](/docs/metod).",
        "rundata": "Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open "
                   "Database License.",
        "around": "omkring", "stones": "stenar", "in": "Inom klustret", "out": "Övriga stenar",
        "chart_time": "Andel runstenar med mönstret ({label}), efter stilgrupp",
        "chart_prov": "Andel runstenar med mönstret ({label}) omkring 1050, efter landskap",
        "chart_cluster": "Andel runstenar med mönstret ({label}) inom klustret och i resten av landet",
        "source_line": "Källa: Vitkis korpusanalys av Samnordisk runtextdatabas.",
    },
    "en": {
        "short": "In short", "see": "What we see", "sure": "How sure we are", "hyp": "Our hypothesis",
        "test": "How it can be tested", "caveats": "Caveats", "yourself": "See for yourself", "sources": "Sources and data",
        "hyp_bullet": "Our hypothesis", "test_bullet": "It can be tested", "both": "The pattern holds in both halves of the "
        "corpus, split parish by parish.", "not_both": "The pattern has not been tested in both halves, or holds in only one.",
        "many": "**Many tests at once.** The pattern was tested together with the app's other patterns and survives the "
                "adjustment for many tests ({sig}).",
        "halves": "**Both halves.** We split the material into two halves, parish by parish, and the pattern appears in each "
                  "on its own.",
        "draws": "**Uncertain years.** The style groups' dates are approximate; we recalculated with years drawn at random "
                 "within each group's interval, and {ok} of {n} recalculations gave the same result.",
        "model": "**Same carver, same area.** The model compares stones by the same carver and in the same area, so the "
                 "pattern is not just one carver's habit or a difference between provinces.",
        "cluster": "**Not chance.** The cluster was tested against {nsim} random redistributions of the pattern over the "
                   "stones (Kulldorff's scan statistic).",
        "rewrite": "*Draft: the numbers and the reasoning come from Vitki's analyses. Rewrite the text in your own words, "
                   "perhaps opening with an inscription as a hook, and add what is new compared with earlier research.*",
        "map": "The pattern on the [map]({href}).",
        "stats": "The models and curves under [Statistics](/statistik) and the pattern with its hypothesis under "
                 "[Research gaps](/luckor); the method in [Methods and calculations](/docs/metod).",
        "rundata": "Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala "
                   "University. Open Database License.",
        "around": "around", "stones": "stones", "in": "Within the cluster", "out": "Other stones",
        "chart_time": "Share of runestones with the pattern ({label}), by style group",
        "chart_prov": "Share of runestones with the pattern ({label}) around 1050, by province",
        "chart_cluster": "Share of runestones with the pattern ({label}) within the cluster and in the rest of the country",
        "source_line": "Source: Vitki's corpus analysis of the Scandinavian Runic-text Data Base.",
    },
}
REFS = {
    "time": "Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. "
            "(eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.",
    "holm": "Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6, "
            "pp. 65–70.",
    "bh": "Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate. *Journal of the Royal Statistical "
          "Society B* 57, pp. 289–300.",
    "kulldorff": "Kulldorff, M. 1997. A spatial scan statistic. *Communications in Statistics – Theory and Methods* 26, "
                 "pp. 1481–1496.",
}


def topic_key(p: dict) -> str:
    return f"{p.get('topic')}|{p.get('key')}"


def first_sentence(text: str) -> str:
    s = re.split(r"(?<=[a-zåäö0-9)])\.\s", text or "", maxsplit=1)[0]
    s = re.split(r"\s\(|:\s", s, maxsplit=1)[0]
    return s.rstrip(".") if len(s) <= 110 else s[:107].rsplit(" ", 1)[0] + " …"


def _dot(t: str) -> str:
    t = t.strip()
    return t if t.endswith((".", "!", "?", "…")) else t + "."


def _feature(res: dict, key: str) -> dict | None:
    return next((f for f in (res.get("change") or {}).get("features") or [] if f.get("key") == key), None)


def _hotspot(res: dict, key: str) -> tuple[dict, dict] | None:
    """The hotspot pattern and cluster behind a key such as hotspot_r_for_R_U 768."""
    m = re.match(r"^hotspot_(.+)_([^_]+ \d+[A-Z]?)$", key or "")
    if not m:
        return None
    p = next((x for x in (res.get("hotspots") or {}).get("patterns") or [] if x.get("key") == m.group(1)), None)
    c = next((c for c in (p or {}).get("clusters") or [] if c.get("center") == m.group(2)), None)
    return (p, c) if p and c else None


def has_chart(p: dict, res: dict) -> bool:
    return bool(chart(p, res, "sv"))


def chart(p: dict, res: dict, lang: str = "sv", label: str | None = None, provinces: dict | None = None) -> str:
    """A :::chart block (components/BlogBody.tsx) for the pattern, or "" when there are no numbers to draw."""
    w, topic, key = WORDS[lang], p.get("topic"), p.get("key") or ""
    pct = (lambda v: f"{round(v * 100)}")
    num = (lambda n: f"{n} {w['stones']}")
    if topic == "Förändring" and (f := _feature(res, key)) and (rows := (f.get("time") or {}).get("by_style")):
        peak = max(rows, key=lambda r: r["share"])["style"]
        lines = [f"{'+' if r['style'] == peak else ''}{r['style']}, {w['around']} {STYLE_YEARS.get(r['style'], r.get('year'))} | "
                 f"{pct(r['share'])} | {num(r['n'])}" for r in rows if r.get("n")]
        return "\n".join([f":::chart {w['chart_time'].format(label=label or f.get('label', key))}", *lines, w["source_line"], ":::"])
    if topic == "Regional skillnad" and (f := _feature(res, key)):
        rows = [r for r in ((f.get("provinces") or {}).get("rows") or []) if (r.get("n_mid") or 0) >= 10 and r.get("share1050") is not None]
        if len(rows) >= 2:
            rows.sort(key=lambda r: -r["share1050"])
            names = provinces or {}
            lines = [f"{'+' if i == 0 else ''}{names.get(r['province'], r['province'])} | {pct(r['share1050'])} | {num(r['n_mid'])}"
                     for i, r in enumerate(rows)]
            return "\n".join([f":::chart {w['chart_prov'].format(label=label or f.get('label', key))}", *lines, w["source_line"], ":::"])
    if (hc := _hotspot(res, key)):
        _, c = hc
        return "\n".join([f":::chart {w['chart_cluster'].format(label=label or key)}",
                          f"+{w['in']} ({c['center']}, {c['radius_km']} km) | {pct(c['rate_in'])} | {num(c['n'])}",
                          f"{w['out']} | {pct(c['rate_out'])}", w["source_line"], ":::"])
    return ""


def candidates(patterns: list[dict], res: dict, used: set[str] = frozenset()) -> list[dict]:
    """Ämnena att välja bland: nya mönster som håller i båda halvorna först, sedan bekräftade, högst ett par per område."""
    out, per_topic = [], {}
    # Confirmed patterns must hold in both halves; new ones too, unless the analysis has no test in halves (None)
    pool = [p for p in patterns if p.get("status") in RANK and p.get("hypothesis") and (p.get("topic"), p.get("key")) not in SKIP
            and (p.get("replicated") is True or (p["status"] == "mönster att pröva" and p.get("replicated") is None))]
    # A feature that is part of a broader one (stungen e within stungna runor) gives way to it
    from src.language_profile import REDUNDANT
    keys = {p.get("key") for p in pool}
    covered = {k for parent, kids in REDUNDANT.items() if parent in keys for k in kids}
    pool = [p for p in pool if p.get("key") not in covered]
    pool.sort(key=lambda p: (topic_key(p) in used, RANK[p["status"]], not p.get("replicated"), not has_chart(p, res)))
    for p in pool:
        t = p.get("topic") or ""
        if per_topic.get(t, 0) >= 4:
            continue
        per_topic[t] = per_topic.get(t, 0) + 1
        out.append({"key": topic_key(p), "topic": t, "status": p["status"], "replicated": bool(p.get("replicated")),
                    "title": first_sentence(p["text"]), "text": p["text"], "hypothesis": first_sentence(p["hypothesis"]),
                    "significance": (p.get("significance") or {}).get("label"), "chart": has_chart(p, res),
                    "used": topic_key(p) in used})
    return out[:14]


def draft(p: dict, res: dict, lang: str, tr=lambda t: t, label: str | None = None, provinces: dict | None = None,
          map_keys: frozenset = frozenset()) -> dict:
    """Rubrik, ingress och brödtext kring ett mönster, på ett språk."""
    w = WORDS[lang]
    text, hyp, test, note = tr(p["text"]), tr(p.get("hypothesis") or ""), tr(p.get("test") or ""), tr(p.get("note") or "")
    title = first_sentence(text)
    sig = (p.get("significance") or {}).get("label") or ""
    summary = _dot(first_sentence(text)) + (" " + _dot(first_sentence(hyp)) if hyp else "")
    sure = [w["many"].format(sig=sig) if sig else None]
    topic, key = p.get("topic"), p.get("key") or ""
    f = _feature(res, key) if topic in ("Förändring", "Regional skillnad") else None
    if f:
        sure.append(w["model"])
        draws = (f.get("time") or {}).get("draws") or {}
        if draws.get("n"):
            sure.append(w["draws"].format(ok=round(draws.get("share_sig", 0) * draws["n"]), n=draws["n"]))
    hc = _hotspot(res, key)
    if hc:
        sure.append(w["cluster"].format(nsim=(res.get("hotspots") or {}).get("nsim", 999)))
    if p.get("replicated"):
        sure.append(w["halves"])
    parts = [w["rewrite"], text,
             f":::box {w['short']}\n- {_dot(first_sentence(text))}\n- {w['both'] if p.get('replicated') else w['not_both']}"
             + (f"\n- {w['hyp_bullet']}: {_dot(first_sentence(hyp))[0].lower() + _dot(first_sentence(hyp))[1:]}" if hyp else "")
             + (f"\n- {w['test_bullet']}: {_dot(first_sentence(test))[0].lower() + _dot(first_sentence(test))[1:]}" if test else "")
             + "\n:::",
             f"## {w['see']}"]
    c = chart(p, res, lang, label, provinces)
    if c:
        parts.append(c)
    parts.append(f":::box {w['sure']}\n" + "\n".join(f"- {s}" for s in sure if s) + "\n:::")
    if hyp:
        parts += [f"## {w['hyp']}", hyp]
    if test:
        parts += [f"## {w['test']}", test]
    if note:
        parts += [f"## {w['caveats']}", note]
    see = [w["stats"]]
    pm = (hc[0]["key"] if hc else MAP_ALIAS.get(key, key)) if (hc or topic in ("Förändring", "Regional skillnad")) else None
    if pm and pm in map_keys:
        see.insert(0, w["map"].format(href=f"/karta?pattern={pm}" + ("&mode=kluster" if hc else "&mode=tid" if topic == "Förändring" else "")))
    parts += [f"## {w['yourself']}", "\n".join(f"- {s}" for s in see)]
    refs = [w["rundata"]]
    if f:
        refs.append(REFS["time"])
    refs.append(REFS["kulldorff"] if hc else REFS["holm"] if topic in ("Förändring", "Regional skillnad") else REFS["bh"])
    parts += [f"## {w['sources']}", "\n".join(f"- {r}" for r in refs)]
    return {"title": title, "summary": summary, "body": "\n\n".join(parts)}
