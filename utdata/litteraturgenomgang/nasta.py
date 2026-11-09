"""Kön för läsningen: vilka omgångar som återstår (ingen fynd2-fil) och inte redan är startade (startade.txt).
    python3 nasta.py            # visa läget och de nästa
    python3 nasta.py 3 --starta # skriv ut de 3 nästa och markera dem som startade
Instruktion per omgång: LASARE_RUN.md (fva/fvb/fvc) eller LASARE_GRANN.md (fvga/fvgb/fvgc)."""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
started_f = os.path.join(HERE, "startade.txt")
started = set(open(started_f).read().split()) if os.path.exists(started_f) else set()
batches = sorted(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(HERE, "omgangar", "*.json")))
done = {os.path.basename(f)[:-6] for f in glob.glob(os.path.join(HERE, "fynd2", "*.jsonl"))}
todo = [b for b in batches if b not in done and not b.startswith("omgang_")]
waiting = [b for b in todo if b not in started]
n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 0
print(f"klara {len(done)} · pågår {len([b for b in todo if b in started])} · väntar {len(waiting)}")
pick = waiting[:n]
for b in pick:
    print(b, "LASARE_GRANN.md" if b.startswith("fvg") else "LASARE_RUN.md")
if "--starta" in sys.argv and pick:
    with open(started_f, "a") as fh:
        fh.write("\n".join(pick) + "\n")
