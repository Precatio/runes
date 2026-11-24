"""Samla läsarnas koder ur arbetsflödenas journaler (journal.jsonl) till en fil.

    .venv/bin/python utdata/nya_ristare/ornamentik/samla.py UT.json JOURNAL [JOURNAL ...]
"""
import json
import re
import sys

out, seen = [], set()
for path in sys.argv[2:]:
    label = {}
    for line in open(path, encoding="utf-8"):
        e = json.loads(line)
        if e.get("type") == "started":
            label[e["key"]] = e.get("label", "")
        elif e.get("type") == "result":
            lab = label.get(e.get("key"), "")
            m = re.match(r"(.+)-läsare(\d)$", lab)
            r = e.get("result") or e.get("value")
            if not m or not isinstance(r, dict) or lab in seen:
                continue
            seen.add(lab)
            out.append({"batch": m.group(1), "coder": int(m.group(2)), "stenar": r.get("stenar")})
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "läsningar,", sum(len(r["stenar"] or []) for r in out), "stenkoder")
