"""Plan analysplaner/2026-11-20-okant-ord-och-samma-ord.md (sha b18f81cd): dok5_f0–f4 räknade om från de sparade raderna.
Del 1: ett okänt ord (<unk>) får ingen sannolikhet och står utanför intervallen. Del 2: rätt ord också när del-modellens
lemma är detsamma (maskeringsprovets regel), lemmat ur textmodel.bundle(k) (tränad utan stenarna i del k).
Skriver resultat.json och resultat.md här. Ett tungt jobb: fem del-modeller efter varandra.
    PYTHONPATH=. .venv/bin/python utdata/runlm_forfining/matt_2026_11_20/omrakna.py"""
import json
import sys

sys.path.insert(0, ".")
from src import textmodel as tm  # noqa: E402

F = "utdata/runlm_forfining/"
HERE = F + "matt_2026_11_20/"
BINS = ((0, .5), (.5, .8), (.8, .95), (.95, 1.01))


def summarize(rows, p_key, ok_key):
    out = {}
    for kind in ("runsten", "annan sten", "löst föremål"):
        xs = [x for x in rows if x["kind"] == kind and x["gold_word"]]
        if not xs:
            continue
        b = []
        for lo, hi in BINS:
            ys = [x for x in xs if x[p_key] is not None and lo <= x[p_key] < hi]
            b.append({"lo": lo, "hi": hi, "n": len(ys), "said": round(sum(x[p_key] for x in ys) / max(1, len(ys)), 4),
                      "right": round(sum(x[ok_key] for x in ys) / max(1, len(ys)), 4), "wrong": sum(not x[ok_key] for x in ys)})
        out[kind] = {"word_n": len(xs), "word_ok": round(sum(x[ok_key] for x in xs) / len(xs), 4),
                     "unknown": sum(1 for x in xs if x[p_key] is None), "bins": b}
    return out


def main():
    rows = []
    for k in range(5):
        rs = json.load(open(F + f"dok5_f{k}.json"))["rows"]
        m = tm.bundle(k)["model"]
        for x in rs:
            w, g = (x["word"] or ""), x["gold_word"]
            x["p_old"], x["ok_old"] = x["p"], x["word_ok"]
            x["p_new"] = None if w == "<unk>" else x["p"]
            x["lemma_same"] = bool(g and w and w != "<unk>" and m.lemma(w.lstrip("§")) == m.lemma(g))
            x["ok_new"] = bool(x["word_ok"] or x["lemma_same"])
            x["fold"] = k
        rows += rs
        tm._bundles.clear()
        print(f"del {k} klar", flush=True)
    old, new = summarize(rows, "p_old", "ok_old"), summarize(rows, "p_new", "ok_new")
    flagged_old = [x for x in rows if x["kind"] in ("runsten", "annan sten") and x["p_old"] is not None and x["p_old"] >= .8 and not x["ok_old"]]
    reclass = [{"sig": x["sig"], "word": x["word"], "gold": x["gold_word"], "p": x["p_old"],
                "nu": "okänt ord" if x["p_new"] is None else ("samma ord (lemma)" if x["ok_new"] else "fortfarande annat ord")}
               for x in flagged_old]
    res = {"plan": "b18f81cd", "fore": old, "efter": new, "de_ifragasatta": reclass,
           "andrade_rader": {"till_okant": sum(1 for x in rows if x["p_old"] is not None and x["p_new"] is None),
                             "till_ratt": sum(1 for x in rows if x["ok_new"] and not x["ok_old"])}}
    json.dump(res, open(HERE + "resultat.json", "w"), ensure_ascii=False, indent=1)
    L = ["# Omräkning av dok5 (plan b18f81cd)", ""]
    for kind in new:
        o, n = old[kind], new[kind]
        L += [f"## {kind}", f"- rätt ord {o['word_ok']:.1%} → {n['word_ok']:.1%} (av {n['word_n']}); okända ord utan procent: {n['unknown']}"]
        for bo, bn in zip(o["bins"], n["bins"]):
            L.append(f"- {bo['lo']}–{bo['hi']}: före {bo['n']} luckor, sade {bo['said']}, rätt {bo['right']} ({bo['wrong']} fel) → "
                     f"efter {bn['n']}, sade {bn['said']}, rätt {bn['right']} ({bn['wrong']} fel)")
        L.append("")
    L += ["## De ifrågasatta (p ≥ 0,8 och fel ord före)"] + [f"- {r['sig']}: {r['word']} / {r['gold']} ({r['p']}) → {r['nu']}" for r in reclass]
    open(HERE + "resultat.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
