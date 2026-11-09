"""Litteraturgenomgången, steg 3: slår ihop läsningarna (fynd/*.jsonl) till en överblick – alla mätbara påståenden med
prioritet, idéerna till artiklar och rapporter, bristerna och överlappen med det Vitki redan har gjort – med källa och
ordagrant citat. Skriver sammanstallning.md och pastaenden.jsonl (en rad per mätbart påstående, med en status som kan
bockas av när vi har mätt det).
    .venv/bin/python utdata/litteraturgenomgang/sammanstall.py"""
import glob
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))


def short_authors(a):
    if isinstance(a, list):
        a = "; ".join(a)
    a = (a or "").split("(")[0]
    return a.strip()[:60]


def main():
    arts = []
    files = sorted(glob.glob(os.path.join(HERE, "fynd2", "*.jsonl"))) + sorted(glob.glob(os.path.join(HERE, "fynd", "*.jsonl")))
    for f in files:  # the second reading (broad brief, fynd2/) comes first and wins
        for line in open(f, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                r["_batch"] = os.path.basename(f)[:-6]
                arts.append(r)
    seen, uniq = set(), []
    for r in arts:  # a text read twice keeps its first reading
        if r["key"] not in seen:
            seen.add(r["key"])
            uniq.append(r)
    arts = uniq
    claims = []
    old = {}
    p = os.path.join(HERE, "pastaenden.jsonl")
    if os.path.exists(p):  # keep the status of claims already worked on
        for line in open(p, encoding="utf-8"):
            c = json.loads(line)
            old[c["id"]] = c.get("status", "ej prövat")
    for r in arts:
        for i, c in enumerate(r.get("claims") or [], 1):
            if not c.get("measurable"):
                continue
            cid = f"{r['key']}#{i}"
            claims.append({"id": cid, "key": r["key"], "journal": r.get("journal"), "year": r.get("year"),
                           "authors": short_authors(r.get("authors")), "title": r.get("title"), "priority": c.get("priority", 3),
                           "claim": c.get("claim"), "quote": c.get("quote"), "how": c.get("how"),
                           "beyond_author": c.get("beyond_author"), "discipline": c.get("discipline"),
                           "consequence": c.get("consequence"), "status": old.get(cid, "ej prövat")})
    needs = [{"key": r["key"], "authors": short_authors(r.get("authors")), "year": r.get("year"), "claim": c.get("claim"),
              "data_needed": c.get("data_needed"), "discipline": c.get("discipline")}
             for r in arts for c in (r.get("claims") or []) if not c.get("measurable") and c.get("data_needed")]
    claims.sort(key=lambda c: (c["priority"], str(c["year"]), c["id"]))
    with open(p, "w", encoding="utf-8") as fh:
        for c in claims:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    pri = Counter(c["priority"] for c in claims)
    L = ["# Litteraturgenomgången – sammanställning\n",
         f"{len(arts)} lästa texter ({Counter(r.get('journal') for r in arts)}), {sum(1 for r in arts if r.get('claims'))} med "
         f"påståenden; {len(claims)} mätbara påståenden (prioritet 1: {pri.get(1, 0)}, 2: {pri.get(2, 0)}, 3: {pri.get(3, 0)}).\n",
         "## Prioritet 1 – mätbara påståenden\n"]
    for c in [c for c in claims if c["priority"] == 1]:
        L.append(f"- **{c['authors']} {c['year']}** ({c['key']}), *{(c['title'] or '')[:90]}*  \n  {c['claim']}  \n"
                 f"  Mätning: {c['how']}  \n  Utöver författaren: {c['beyond_author']}"
                 + (f"  \n  > {c['quote']}" if c.get("quote") else ""))
    L.append("\n## Idéer till artiklar och rapporter\n")
    for r in arts:
        for idea in r.get("ideas") or []:
            L.append(f"- [{idea.get('kind')}] **{idea.get('title_sv')}** – {idea.get('question')} "
                     f"(data: {idea.get('data')}; varför: {idea.get('why')}) – efter {short_authors(r.get('authors'))} {r.get('year')} ({r['key']})")
    L.append("\n## Brister vi kan mäta\n")
    for r in arts:
        for g in r.get("gaps") or []:
            L.append(f"- {g} – {short_authors(r.get('authors'))} {r.get('year')} ({r['key']})")
    L.append("\n## Överlapp med Vitki (nyhetskontroll)\n")
    for r in arts:
        for o in r.get("overlap_vitki") or []:
            L.append(f"- {o} – {short_authors(r.get('authors'))} {r.get('year')} ({r['key']})")
    L.append("\n## Där Vitki har missat att forska\n")
    for r in arts:
        for m in r.get("vitki_missing") or []:
            L.append(f"- {m} – {short_authors(r.get('authors'))} {r.get('year')} ({r['key']})")
    L.append("\n## Data Vitki borde skaffa (påståenden som påverkar runforskningen men inte går att mäta än)\n")
    for x in needs:
        L.append(f"- {x['data_needed']} – för: {x['claim']} ({x['discipline']}; {x['authors']} {x['year']}, {x['key']})")
    L.append("\n## Prioritet 2\n")
    for c in [c for c in claims if c["priority"] == 2]:
        L.append(f"- {c['authors']} {c['year']} ({c['key']}): {c['claim']} – {c['how']}")
    open(os.path.join(HERE, "sammanstallning.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(len(arts), "texter,", len(claims), "mätbara påståenden", dict(pri))


if __name__ == "__main__":
    main()
