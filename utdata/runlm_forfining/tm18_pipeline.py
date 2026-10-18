"""Omvalideringståget för textmodel-18 (namnkvoten, name_cands=40). Regenererar kalibreringens underlag med
namnkandidaterna på, skattar om listkalibreringen och kör det dokumenterade provet från ände till ände – UTAN att
röra src/textmodel.py: FILL patchas bara i arbetarprocesserna, och versionsflippen görs för hand efteråt om
siffrorna håller. Etapper:
  1 klass3   utgivarnas luckor (scripts/runlm_gaps), 5 falder parallellt, + sammanslagning till klass3_alla
  2 dokalts  dokumenterade luckor för skattningen (runlm_documented_test med FILL+name_cands), 5 parallellt
  3 mask     maskeringsproven för skattningen (runlm_restore_test --own_d [--hard] --name_cands), 10 körningar
  4 fit      scripts/runlm_list_calibrate --write (kalibreringsfilen säkerhetskopieras först)
  5 dok5     dokumenterade provet med nya kalibreringen, 5 parallellt + sammanfattning
Allt loggas till /Volumes/2TB/Antigrvity/Runes/logs/tm18_*.log. Kör en etapp eller allt:
    PYTHONPATH=. .venv/bin/python utdata/runlm_forfining/tm18_pipeline.py [--stage N] [--cands 40]
Arbetarläge (internt): --worker dok --fold K --out PATH --cands N"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LOGS = "/Volumes/2TB/Antigrvity/Runes/logs"
PY = os.path.join(ROOT, ".venv", "bin", "python")
sys.path.insert(0, ROOT)

KLASS3_FLAGS = ["--max_gaps", "2000", "--lam_name", "0.05", "--lam_class", "0.2", "--window", "-1",
                "--char_fills", "15", "--context_cands", "--n_cands", "100", "--by_word",
                "--near", "0.1", "--near_km", "10.0", "--own_d"]


def run_parallel(cmds, tag):
    os.makedirs(LOGS, exist_ok=True)
    procs = []
    for i, cmd in enumerate(cmds):
        log = open(os.path.join(LOGS, f"tm18_{tag}_{i}.log"), "w")
        procs.append((subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                       env={**os.environ, "PYTHONPATH": ROOT}), cmd))
    bad = []
    for p, cmd in procs:
        if p.wait() != 0:
            bad.append(" ".join(cmd))
    if bad:
        raise SystemExit(f"{tag}: misslyckades:\n" + "\n".join(bad))
    print(f"{tag}: klart ({len(cmds)} körningar)", flush=True)


def stage1(cands):
    run_parallel([[PY, "-m", "scripts.runlm_gaps", "--fold", str(k), *KLASS3_FLAGS,
                   "--name_cands", str(cands), "--out", os.path.join(HERE, f"klass3_f{k}.json")]
                  for k in range(5)], "klass3")
    rows, settings = [], None
    for k in range(5):
        d = json.load(open(os.path.join(HERE, f"klass3_f{k}.json")))
        settings = settings or {**d["settings"], "fold": None}
        rows += d["rows"]
    json.dump({"settings": settings, "rows": rows}, open(os.path.join(HERE, "klass3_alla.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"klass3_alla: {len(rows)} rader", flush=True)


def stage2(cands):
    run_parallel([[PY, __file__, "--worker", "dok", "--fold", str(k), "--cands", str(cands),
                   "--out", os.path.join(HERE, f"dok_alts_f{k}.json")] for k in range(5)], "dokalts")


def stage3(cands):
    # two waves of five: ten parallel model builds was what froze the machine this morning
    run_parallel([[PY, "-m", "scripts.runlm_restore_test", "--folds", str(k), "--own_d",
                   "--name_cands", str(cands), "--out", os.path.join(HERE, f"mask4_f{k}.json")]
                  for k in range(5)], "mask4")
    run_parallel([[PY, "-m", "scripts.runlm_restore_test", "--folds", str(k), "--own_d", "--hard",
                   "--name_cands", str(cands), "--out", os.path.join(HERE, f"svart4_f{k}.json")]
                  for k in range(5)], "svart4")


def stage4():
    cal = os.path.join(ROOT, "data", "runlm_calibration.json")
    shutil.copy2(cal, cal + f".fore-tm18-{datetime.date.today()}")
    r = subprocess.run([PY, "-m", "scripts.runlm_list_calibrate", "--write"], cwd=ROOT,
                       capture_output=True, text=True, env={**os.environ, "PYTHONPATH": ROOT})
    open(os.path.join(LOGS, "tm18_fit.log"), "w").write(r.stdout + r.stderr)
    if r.returncode != 0:
        raise SystemExit("fit misslyckades, se tm18_fit.log")
    print("fit: klart (säkerhetskopia av kalibreringen ligger bredvid)", flush=True)


def stage5(cands):
    run_parallel([[PY, __file__, "--worker", "dok", "--fold", str(k), "--cands", str(cands),
                   "--out", os.path.join(HERE, f"dok5_f{k}.json")] for k in range(5)], "dok5")
    rows = [x for k in range(5) for x in json.load(open(os.path.join(HERE, f"dok5_f{k}.json")))["rows"]]
    rs = [x for x in rows if x["kind"] == "runsten" and x.get("gold_word")]
    right = sum(x["word_ok"] for x in rs)
    hi = [x for x in rs if x["p"] >= 0.95]
    res = {"gaps": len(rs), "word_ok": right / len(rs), "sure_n": len(hi),
           "sure_right": sum(x["word_ok"] for x in hi) / max(1, len(hi)),
           "mean_p": sum(x["p"] for x in rs) / len(rs)}
    json.dump(res, open(os.path.join(HERE, "tm18_dok_sammanfattning.json"), "w"), indent=1)
    print("DOK5 (runstenar):", json.dumps(res), flush=True)


def worker_dok(fold, out, cands):
    import src.textmodel as tm
    from scripts.runlm_documented_test import run
    tm.FILL = {**tm.FILL, "name_cands": cands}
    run(fold, out, own_d=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, default=0, help="0 = alla etapper i följd")
    ap.add_argument("--cands", type=int, default=40)
    ap.add_argument("--worker")
    ap.add_argument("--fold", type=int)
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.worker == "dok":
        return worker_dok(a.fold, a.out, a.cands)
    stages = {1: lambda: stage1(a.cands), 2: lambda: stage2(a.cands), 3: lambda: stage3(a.cands),
              4: stage4, 5: lambda: stage5(a.cands)}
    for n in ([a.stage] if a.stage else [1, 2, 3, 4, 5]):
        print(f"=== etapp {n} ({datetime.datetime.now():%H:%M}) ===", flush=True)
        stages[n]()


if __name__ == "__main__":
    main()
