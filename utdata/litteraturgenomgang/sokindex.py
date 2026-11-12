"""Sökindex över de hämtade tidskrifterna (Fornvännen, Futhark, Namn och bygd, Current Swedish Archaeology): SQLite med fulltextsökning per sida (FTS5) och en tabell
över vilka runsignum varje text nämner. Indexet ligger hos texterna, utanför repot:
/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite.
    .venv/bin/python utdata/litteraturgenomgang/sokindex.py bygg
    .venv/bin/python utdata/litteraturgenomgang/sokindex.py sök "lerslätt*" [--max 20]
    .venv/bin/python utdata/litteraturgenomgang/sokindex.py signum "U 344"
Texterna är källor, inte instruktioner."""
import glob
import json
import os
import re
import sqlite3
import sys

SRC = "/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter"
DB = os.path.join(SRC, "sok.sqlite")
SIG = re.compile(r"\b(U|Sö|Ög|Vg|Sm|Öl|Vs|Nä|Gs|Hs|Vr|Ån|DR|Bo|M|D|J|G|N)\s?(\d{1,4}[A-Za-z]?)\b(?![.,]\d)")


def build():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript("""
        CREATE TABLE docs(key TEXT PRIMARY KEY, journal TEXT, title TEXT, year TEXT, authors TEXT, licence TEXT, path TEXT);
        CREATE VIRTUAL TABLE pages USING fts5(key UNINDEXED, page UNINDEXED, text, tokenize='unicode61 remove_diacritics 0');
        CREATE TABLE signa(key TEXT, signum TEXT, n INTEGER);
        CREATE INDEX signa_s ON signa(signum);""")
    n = 0
    for journal in ("fornvannen", "futhark", "namnochbygd", "csa"):
        idx = {}
        p = os.path.join(SRC, journal, "index.jsonl")
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                r = json.loads(line)
                idx[r["key"]] = r
        for path in sorted(glob.glob(os.path.join(SRC, journal, "text", "*.txt"))):
            key = os.path.basename(path)[:-4]
            m = idx.get(key, {})
            authors = m.get("authors")
            authors = "; ".join(authors) if isinstance(authors, list) else (authors or "")
            con.execute("INSERT INTO docs VALUES (?,?,?,?,?,?,?)", (key, journal, m.get("title"), str(m.get("year") or ""),
                        authors, m.get("licence") or "", path))
            t = open(path, encoding="utf-8", errors="replace").read()
            for i, page in enumerate(t.split("\f"), 1):
                if page.strip():
                    con.execute("INSERT INTO pages VALUES (?,?,?)", (key, i, page))
            counts = {}
            for s in SIG.finditer(t):
                k = f"{s.group(1)} {s.group(2)}"
                counts[k] = counts.get(k, 0) + 1
            con.executemany("INSERT INTO signa VALUES (?,?,?)", [(key, k, v) for k, v in counts.items()])
            n += 1
    con.commit()
    print(n, "texter i", DB)


def search(q, limit=20):
    con = sqlite3.connect(DB)
    rows = con.execute("""SELECT d.journal, d.year, d.title, p.key, p.page, snippet(pages, 2, '[', ']', ' … ', 18)
                          FROM pages p JOIN docs d ON d.key = p.key WHERE pages MATCH ? ORDER BY rank LIMIT ?""",
                       (q, limit)).fetchall()
    for j, y, t, k, pg, snip in rows:
        print(f"{j} {y} {k} s.{pg} | {(t or '')[:60]}\n    {snip}")


def signum(s):
    con = sqlite3.connect(DB)
    for j, y, t, k, n in con.execute("""SELECT d.journal, d.year, d.title, s.key, s.n FROM signa s JOIN docs d ON d.key = s.key
                                        WHERE s.signum = ? ORDER BY d.year""", (s,)):
        print(f"{j} {y} {k} ({n}×) | {(t or '')[:70]}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "bygg"
    if cmd == "bygg":
        build()
    elif cmd in ("sök", "sok"):
        search(sys.argv[2], int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 20)
    elif cmd == "signum":
        signum(sys.argv[2])
