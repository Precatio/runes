"""Publiceringsschemat till Firestore, så att webbadmin /redaktion kan visa och godkänna veckan från mobilen.

Källan är data/publiceringsschema.json, som du redigerar som förut (den lokala appens Veckans publiceringar läser den
direkt, api/routers/blog_week.py). Skriptet lägger varje rad i samlingen publiceringsschema i databasen vitki, med id
<datum>_<artikelns id> och samma fält som i filen. Raderna uppdateras eller läggs till; inget tas bort utan --rensa, och
inte ens då en rad vars artikel redan är schemalagd eller publicerad (den är godkänd). Webbläsaren får bara läsa
samlingen (web/firestore.rules); bara det här skriptet, med den lokala appens behörighet, skriver i den.

    .venv/bin/python scripts/publiceringsschema_sync.py            # visar vad som skulle skrivas
    .venv/bin/python scripts/publiceringsschema_sync.py --skriv    # skriver och läser tillbaka
    .venv/bin/python scripts/publiceringsschema_sync.py --skriv --rensa   # tar också bort rader som inte står i filen
                                                                          # och inte är godkända
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

SCHEMA = os.path.join(ROOT, "data", "publiceringsschema.json")
COLLECTION = "publiceringsschema"
FIELDS = ("datum", "tid", "id", "titel", "spar", "bluesky", "godkand")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME = re.compile(r"^\d{2}:\d{2}$")


def _env() -> None:
    from dotenv import dotenv_values
    for f in (".env", "api/.env"):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            for k, v in dotenv_values(p).items():
                os.environ.setdefault(k, v or "")


def doc_id(row: dict) -> str:
    return f"{row['datum']}_{row['id']}"


def rows_of(schema: dict) -> dict[str, dict]:
    """The plan's rows as Firestore documents, by document id. A row that cannot be read stops the whole sync."""
    out: dict[str, dict] = {}
    for n, row in enumerate(schema.get("poster", []), 1):
        if not (DATE.match(str(row.get("datum", ""))) and TIME.match(str(row.get("tid", "")))
                and isinstance(row.get("id"), str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", row["id"])):
            raise SystemExit(f"Rad {n} i publiceringsschemat har fel datum, tid eller id: {row}")
        dt.date.fromisoformat(row["datum"])
        out[doc_id(row)] = {k: row.get(k) for k in FIELDS}
    return out


def approved(row: dict, post: dict | None) -> bool:
    """A row is approved when its article is scheduled or published (or the local tool has marked it)."""
    return bool(row.get("godkand")) or bool(post and post.get("published"))


def plan(rows: dict[str, dict], existing: dict[str, dict], posts: dict[str, dict], prune: bool):
    """What a sync does: (documents to write, ids to delete, ids kept although missing from the file)."""
    write = {i: r for i, r in rows.items() if existing.get(i) != r}
    gone = [i for i in existing if i not in rows]
    delete = [i for i in gone if prune and not approved(existing[i], posts.get(existing[i].get("id")))]
    kept = [i for i in gone if i not in delete]
    return write, delete, kept


def sync(db, schema: dict, write_it: bool, prune: bool) -> dict:
    rows = rows_of(schema)
    col = db.collection(COLLECTION)
    existing = {d.id: d.to_dict() or {} for d in col.stream()}
    posts = {}
    if prune:
        ids = {r.get("id") for r in existing.values()}
        posts = {i: (db.collection("posts").document(i).get().to_dict() or {}) for i in ids if i}
    write, delete, kept = plan(rows, existing, posts, prune)
    for i, r in write.items():
        print(f"{'skriver' if write_it else 'skulle skriva'} {i}: {r.get('titel')}")
        if write_it:
            col.document(i).set(r)
    for i in delete:
        print(f"{'tar bort' if write_it else 'skulle ta bort'} {i} (står inte i filen och är inte godkänd)")
        if write_it:
            col.document(i).delete()
    for i in kept:
        print(f"behålls {i}: står inte i filen" + (" men är godkänd" if prune else " (ta bort med --rensa)"))
    if not write and not delete:
        print("Firestore stämmer redan med filen.")
    return {"write": list(write), "delete": delete, "kept": kept}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    _env()
    write_it, prune = "--skriv" in argv, "--rensa" in argv
    with open(SCHEMA, encoding="utf-8") as fh:
        schema = json.load(fh)
    from api.auth import firestore
    db = firestore()
    sync(db, schema, write_it, prune)
    if write_it:
        back = {d.id: d.to_dict() for d in db.collection(COLLECTION).stream()}
        wrong = [i for i, r in rows_of(schema).items() if back.get(i) != r]
        print(f"Läst tillbaka: {len(back)} rader i Firestore; "
              + ("alla stämmer med filen." if not wrong else f"AVVIKER: {', '.join(wrong)}"))
        return 1 if wrong else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
