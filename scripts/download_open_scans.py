"""Laddar ned de öppna skanningarna i data/scan_files.json som saknas på disken, till skanningar/<serie>/.

Varje fil kontrolleras mot Zenodos md5 innan den får sitt slutliga namn, och dess SHA-256 skrivs in i
data/scan_files.json (så känns filen igen vid uppladdning, oavsett namn). Avbrutna nedladdningar fortsätter där de
slutade (.part). Filer som redan ligger i projektets rot eller i skanningar/ hashas i stället för att laddas ned.
    .venv/bin/python scripts/download_open_scans.py              # visar vad som saknas
    .venv/bin/python scripts/download_open_scans.py --hämta      # laddar ned och uppdaterar scan_files.json
"""
import hashlib
import json
import os
import sys
import time
import urllib.parse

import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FILES = os.path.join(ROOT, "data", "scan_files.json")
SCANS = os.path.join(ROOT, "skanningar")
# Series folders that already existed before this script, by dataset key; the rest get their key as folder name
FOLDER = {"sodermanland": "", "medelpad": "medelpad", "gravmonument_og_sm": "gravmonument_og_sm"}


def digests(path: str) -> tuple[str, str]:
    md5, sha = hashlib.md5(), hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 22), b""):
            md5.update(block)
            sha.update(block)
    return md5.hexdigest(), sha.hexdigest()


def local_path(key: str, name: str) -> str | None:
    """Where the file already is, if anywhere: its series folder, skanningar/ or the project root."""
    for d in (os.path.join(SCANS, FOLDER.get(key, key)), SCANS, ROOT):
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return p
    return None


def download(url: str, dest: str, size: int):
    part = dest + ".part"
    for attempt in range(5):
        have = os.path.getsize(part) if os.path.exists(part) else 0
        if have >= size:
            break
        try:
            with requests.get(url, headers={"Range": f"bytes={have}-"} if have else {}, stream=True, timeout=120) as r:
                if r.status_code == 200 and have:
                    have = 0  # the server ignored the range: start over
                r.raise_for_status()
                with open(part, "ab" if have else "wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
        except requests.RequestException as e:
            print(f"   avbrott ({e!r}), försök {attempt + 2} av 5 om 20 s", flush=True)
            time.sleep(20)
    os.replace(part, dest)


def main():
    fetch = "--hämta" in sys.argv
    data = json.load(open(FILES, encoding="utf-8"))
    todo = [(k, ds, f) for k, ds in data["datasets"].items() for f in ds["files"] if not f.get("sha256")]
    print(f"{len(todo)} filer saknar SHA-256 ({sum(f['size'] for _, _, f in todo) / 1e9:.1f} GB)", flush=True)
    for i, (key, ds, f) in enumerate(todo, 1):
        path = local_path(key, f["name"])
        if not fetch:
            print(f"{i:3}. {key}: {f['name']} {'(finns lokalt)' if path else ''}")
            continue
        if not path:
            folder = os.path.join(SCANS, FOLDER.get(key, key))
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, f["name"])
            url = f"https://zenodo.org/records/{ds['record']}/files/{urllib.parse.quote(f['name'])}?download=1"
            print(f"{i:3}/{len(todo)} hämtar {f['name']} ({f['size'] / 1e6:.0f} MB)", flush=True)
            download(url, path, f["size"])
        md5, sha = digests(path)
        if md5 != f["md5"]:
            print(f"   FEL: md5 stämmer inte för {f['name']} ({md5} ≠ {f['md5']}); filen flyttas till .fel", flush=True)
            os.replace(path, path + ".fel")
            continue
        f["sha256"] = sha
        # Saved after every file, so that an interrupted run keeps what it verified
        json.dump(data, open(FILES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"   ok {f['name']}", flush=True)
    print("klart", flush=True)


if __name__ == "__main__":
    main()
