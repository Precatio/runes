"""Del C i analysplan_kallor.md: vad forskarna är överens om på Blekingestenarna Gummarp (Bl 2), Stentoften (Bl 3),
Istaby (Bl 4) och Björketorp (Bl 6), räknat på RuneS-DB:s tolkningssidor (Kiels runprojekts material; hämtade
2026-10-21, CC BY-SA 4.0): täckning och läsningsenighet per rad, översättningsenighet och stabila innehållsord.
Skriver utdata/kallor/blekinge.json.
    PYTHONPATH=. .venv/bin/python utdata/kallor/blekinge_tolkningar.py"""
import difflib
import json
import os
import re
import unicodedata
from collections import Counter
from itertools import combinations

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
KALLOR = os.path.join(ROOT, "data", "raa", "kallor")
STONES = {"91": "Bl 2 Gummarp", "92": "Bl 3 Stentoften", "94": "Bl 4 Istaby", "93": "Bl 6 Björketorp"}
BRACTEATES = {"137": "IK 184 Tjurkö I", "125": "IK 185 Tjurkö II"}
STOP = set("the a an of to in and or is are was were be been by for with this that these those it its he she they them his her "
           "their here there who which what as at on from into out i me my we our you your not no one ones".split())
GROUPS = {"död": ("death", "die", "dead", "dying"), "förstörelse": ("destroy", "break", "broke", "damage"), "förutsägelse/skada": ("prophe", "harm")}
recs = json.load(open(os.path.join(KALLOR, "runes_records.json"), encoding="utf-8"))


def clean_runes(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("ʀ", "z").replace("ᴀ", "a").replace("ᴍ", "m")
    return re.sub(r"[\[\]()?\-… .:ˈ|\d]", "", s)


def lines_of(translit: str) -> list[str]:
    parts = [p.strip() for p in translit.split("|") if p.strip()]
    if len(parts) % 2 == 0 and parts[: len(parts) // 2] == parts[len(parts) // 2:]:  # the record shows its lines twice
        parts = parts[: len(parts) // 2]
    return parts


def stem(w: str) -> str:
    w = re.sub(r"[^a-z]", "", w.lower())
    for suf in ("ing", "ed", "es", "s", "ly"):
        if len(w) > 4 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def content(text: str) -> set[str]:
    return {stem(w) for w in re.findall(r"[A-Za-z][A-Za-z'-]*", text or "") if w.lower() not in STOP and len(w) > 2}


out = {"plan_sha256": open(os.path.join(ROOT, "utdata", "kallor", "analysis_plan_kallor.sha256")).read().split()[0], "stones": {}}
for fid, name in {**STONES, **BRACTEATES}.items():
    r = recs[fid]
    lines = lines_of(r["translit"])
    interps = r["interpretations"]
    years = sorted({y for x in interps for y in x["years"]})
    # reading per line: each interpretation's transliteration lines matched to the record's lines by similarity
    cover, agree = [], []
    per_line = [{} for _ in lines]  # line → {interpretation: its reading of the line}, one reading per interpretation
    for k, x in enumerate(interps):
        for part in lines_of(x["translit"] or ""):
            c = clean_runes(part)
            if not c:
                continue
            best = max(range(len(lines)), key=lambda i: difflib.SequenceMatcher(None, c, clean_runes(lines[i])).ratio())
            if difflib.SequenceMatcher(None, c, clean_runes(lines[best])).ratio() >= 0.6:
                per_line[best].setdefault(k, c)
    for i, d in enumerate(per_line):
        lst = list(d.values())
        cover.append(len(lst) / len(interps) if interps else None)
        agree.append((Counter(lst).most_common(1)[0][1] / len(lst)) if lst else None)
    en = [x["en"] for x in interps if x.get("en")]
    sims = [difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() for a, b in combinations(en, 2)]
    words = Counter(w for t in en for w in content(t))
    stable = sorted(w for w, c in words.items() if c >= 0.8 * len(en))
    unstable = sorted(w for w, c in words.items() if c < 0.5 * len(en))
    groups = {g: {"n": sum(any(k in t.lower() for k in keys) for t in en), "share": (sum(any(k in t.lower() for k in keys) for t in en) / len(en)) if en else None}
              for g, keys in GROUPS.items()}
    out["stones"][fid] = {"name": name, "n_interpretations": len(interps), "years": years, "n_english": len(en), "lines": lines,
                          "coverage": cover, "agreement": agree, "translation_similarity": (sum(sims) / len(sims)) if sims else None,
                          "stable_words": stable, "unstable_words": unstable[:60], "groups": groups,
                          "literature": sorted({l for x in interps for l in x["literature"]}),
                          "english": [x["en"] for x in interps]}
    print(f"{name}: {len(interps)} tolkningar ({years[0] if years else '?'}–{years[-1] if years else '?'}), engelska {len(en)}, "
          f"översättningslikhet {out['stones'][fid]['translation_similarity'] and round(out['stones'][fid]['translation_similarity'], 2)}")
    for ln, c, a in zip(lines, cover, agree):
        print(f"   {ln[:28]:30} täckning {c and round(c, 2)}  enighet {a and round(a, 2)}")
    print("   stabila:", stable[:25])
    print("   grupper:", {g: v["share"] and round(v["share"], 2) for g, v in groups.items()})
# the hypothesis: on Bl 6 and Bl 3 death and destruction are stable (≥ 80 %), the prophecy/harm words of Bl 6 are not
s6, s3 = out["stones"]["93"]["groups"], out["stones"]["92"]["groups"]
out["answer"] = bool(all(v["share"] is not None and v["share"] >= 0.8 for v in (s6["död"], s6["förstörelse"], s3["död"], s3["förstörelse"]))
                     and (s6["förutsägelse/skada"]["share"] or 0) < 0.8)
json.dump(out, open(os.path.join(ROOT, "utdata", "kallor", "blekinge.json"), "w"), ensure_ascii=False, indent=1)
print("svar:", "ja" if out["answer"] else "nej")
