"""Bygger litteraturregistrets index (src/literature.py): varje runsignum i verkens PDF:er, med tryckt sida och utdrag.
    .venv/bin/python scripts/build_literature_index.py        Läser LITERATURE_DIR, skriver data/cache/literature/index.json.
Verk utan fil i mappen hoppas över; lägg en PDF där med filnamnet ur data/literature/catalog.json och kör igen."""
import json
import os
import re
import subprocess
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src import literature  # noqa: E402
from src.signum import fold_signum  # noqa: E402


def pages(path: str) -> list[str]:
    out = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, timeout=600).stdout
    return out.split("\f")


def main():
    signa = {fold_signum(r["signum"]): r["signum"] for r in store().inscriptions}
    prefixes = sorted({s.split(" ")[0] for s in signa.values()})
    rx = literature.signum_pattern(prefixes)
    stones: dict[str, list[dict]] = {}
    works = {}
    for w in literature._load(literature.CATALOG).get("works") or []:
        paths = [os.path.join(literature.DIR, f) for f in literature.files(w)]
        paths = [p for p in paths if os.path.exists(p)]
        if not paths:
            continue
        found, n_pages = set(), 0
        for path in paths:
            raws = pages(path)
            printed = literature.fill_pages([literature.printed_page(raw, i) for i, raw in enumerate(raws, start=1)])
            for i, raw in enumerate(raws, start=1):
                n_pages += 1
                text = re.sub(r"-\n\s*", "", raw)          # words hyphenated over a line break
                flat = re.sub(r"\s+", " ", text)
                page = printed[i - 1]
                seen_here = set()
                # A register or list (an index of signa, a catalogue table): more signa than words on the page
                n_signa = len({fold_signum(f"{m.group(1)} {m.group(2)}") for m in rx.finditer(flat)} & signa.keys())
                n_words = len(re.findall(r"[A-Za-zÅÄÖåäöÆØæøÞþÐð]{4,}", flat))
                is_list = n_signa / max(n_words, 1) > literature.LIST_RATIO
                if w.get("entry_prefix"):  # the edition's own articles, headed "179. Kölaby sn …"
                    for m in literature.ENTRY.finditer(text):
                        key = fold_signum(f"{w['entry_prefix']} {m.group(1)}")
                        if key in signa and key not in seen_here:
                            seen_here.add(key)
                            stones.setdefault(key, []).append({"work": w["id"], "page": page, "file": os.path.basename(path),
                                                               "entry": True, "text": re.sub(r"\s+", " ", m.group(0)).strip()})
                            found.add(key)
                for m in rx.finditer(flat):
                    key = fold_signum(f"{m.group(1)} {m.group(2)}")
                    if key not in signa or key in seen_here:
                        continue
                    seen_here.add(key)  # one hit per stone and page
                    a, b = max(0, m.start() - literature.SNIPPET), min(len(flat), m.end() + literature.SNIPPET)
                    hit = {"work": w["id"], "page": page, "file": os.path.basename(path)}
                    if is_list:
                        hit["list"] = True
                    else:
                        hit["text"] = ("…" if a else "") + flat[a:b].strip() + ("…" if b < len(flat) else "")
                    stones.setdefault(key, []).append(hit)
                    found.add(key)
        works[w["id"]] = {"n_stones": len(found), "n_pages": n_pages}
        print(f"{w['id']}: {n_pages} sidor, {len(found)} stenar", flush=True)
    os.makedirs(os.path.dirname(literature.INDEX), exist_ok=True)
    tmp = literature.INDEX + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"built": date.today().isoformat(), "works": works, "stones": stones}, fh, ensure_ascii=False)
    os.replace(tmp, literature.INDEX)
    print(f"{len(stones)} stenar i indexet")


if __name__ == "__main__":
    main()
