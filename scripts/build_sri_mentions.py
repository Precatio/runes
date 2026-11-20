"""SRI:s artikel om varje sten, sammanfattad för "Redan känt?" i Forskningsluckor (src/redan_kant.py).

Läser artiklarna per sten ur Sveriges runinskrifter (scripts/sri_artiklar.py → /Volumes/2TB/Antigrvity/Runes/downloads/
sri_artiklar/<verk>.jsonl, med sidmarkörer [[sida N]]) och skriver data/cache/literature/sri_mentions.json: per sten
verket, sidorna, de ristarnamn ur Rundata som står i ett sammanhang om ristare (src/redan_kant.carver_mentions), de
stenar som SRI säger är gjorda av "samme ristare" och alla andra stenar som artikeln nämner, var och en med sida och ett
kort utdrag. Filen följer inte med kodförrådet: SRI III–XV saknar licens, så bara korta citat med källa och sida
(METHODS.md §17).

    .venv/bin/python scripts/build_sri_mentions.py
"""
import glob
import json
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src import literature, redan_kant as rk  # noqa: E402
from src.signum import fold_signum  # noqa: E402

SRC = "/Volumes/2TB/Antigrvity/Runes/downloads/sri_artiklar"
MARK = re.compile(r"\[\[sida ([^\]]+)\]\]")


def segments(text: str) -> list[tuple[str, str]]:
    """Artikeltexten delad på sidmarkörerna: (sida, platt text)."""
    parts = MARK.split(text)
    out = []
    page = None
    for i, p in enumerate(parts):
        if i % 2 == 1:
            page = p.strip()
        elif p.strip():
            out.append((page, rk.flat(p)))
    return out


def own_part(text: str, signum: str, covers: list[str]) -> tuple[str, bool]:
    """Artikeln utan det som hör till nästa sten: uppdelningen (scripts/sri_artiklar.py) missar ibland nästa artikels
    rubrik, så att den följer med ("Fig. 85. U 973." mitt i U 972:s artikel). Texten skärs vid den första
    bildtexten eller rubriken för någon av de tre följande stenarna i samma serie."""
    prefix = signum.split(" ")[0]
    nums = [int(m.group(1)) for c in covers for m in [re.fullmatch(r"\S+ (\d+)", c)] if m]
    if not nums:
        return text, False
    top = max(nums)
    cut = None
    for m in re.finditer(r"Fig\.\s*\d+\s*\.\s*" + re.escape(prefix) + r"\.?\s*(\d+)\b", text):
        if top < int(m.group(1)) <= top + 3:
            cut = m.start()
            break
    for m in literature.ENTRY.finditer(text):
        n = literature.entry_number(m.group(1))
        if n is not None and top < n <= top + 3 and (cut is None or m.start() < cut):
            cut = m.start()
            break
    return (text[:cut], True) if cut is not None else (text, False)


def summarize(article: dict, names: re.Pattern, rx_signum: re.Pattern, signa: dict[str, str]) -> dict:
    own = fold_signum(article["signum"])
    carvers: dict[str, dict] = {}
    same_as: list[dict] = []
    mentioned: dict[str, dict] = {}
    body, cut = own_part(article["text"], article["signum"], article.get("omfattar") or [article["signum"]])
    for page, text in segments(body):
        for base, ex in rk.carver_mentions(text, names, rx_signum, own).items():
            carvers.setdefault(base, {"page": page, "text": ex})
        for sig, ex in rk.same_carver_refs(text, rx_signum):
            if sig != own and sig in signa:
                same_as.append({"signum": sig, "page": page, "text": ex})
        for m in rx_signum.finditer(text):
            k = fold_signum(f"{m.group(1)} {m.group(2)}")
            if k != own and k in signa and k not in mentioned:
                mentioned[k] = {"page": page, "text": rk.excerpt(text, m.start(), m.end())}
    return {"signum": article["signum"], "work": article["work"], "pages": article.get("pages") or [],
            "covers": article.get("omfattar") or [article["signum"]], "carvers": carvers, "same_as": same_as,
            "signa": mentioned, "cut": cut}


def main() -> None:
    s = store()
    signa = {fold_signum(r["signum"]): r["signum"] for r in s.inscriptions}
    bases = sorted({b for r in s.inscriptions for c in r["carvers"] if c["kind"] in ("S", "A")
                    for b in [rk.carver_base(c["name"])] if b})
    names = rk.names_pattern(bases)
    rx_signum = literature.signum_pattern(sorted({v.split(" ")[0] for v in signa.values()}))
    stones: dict[str, dict] = {}
    for path in sorted(glob.glob(os.path.join(SRC, "*.jsonl"))):
        if "forskjuten" in path:
            continue  # Gotlands runinskrifter 3 before the OCR fix (scripts/sri_artiklar.py OCR_DIR)
        for line in open(path, encoding="utf-8"):
            a = json.loads(line)
            k = fold_signum(a["signum"])
            if k in signa and k not in stones:
                stones[k] = summarize(a, names, rx_signum, signa)
    out = os.path.join(ROOT, "data", "cache", "literature", "sri_mentions.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"built": date.today().isoformat(), "n_names": len(bases), "stones": stones}, fh, ensure_ascii=False)
    os.replace(tmp, out)
    n_c = sum(1 for v in stones.values() if v["carvers"])
    print(f"{len(stones)} stenar med SRI-artikel; {n_c} där artikeln nämner en ristare ur Rundata som ristare; "
          f"{sum(1 for v in stones.values() if v['cut'])} artiklar avskurna där nästa artikel följt med")


if __name__ == "__main__":
    main()
