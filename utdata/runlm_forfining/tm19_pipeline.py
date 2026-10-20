"""Valideringståget för textmodel-19-kandidaten (toleranslagret, λ = 0,02; analysplan_tm19.md punkt 7). Samma etapper
som tm18_pipeline.py, men allt skrivs till utdata/runlm_forfining/tm19/ och kalibreringen till en egen fil, så att den
levande appen (textmodel-18) inte rörs förrän beslutet är taget. src/textmodel.py patchas bara i arbetarprocesserna.
Utfall 2026-10-20: dok5 252/361, 2 säkra fel → textmodel-19 infört; tm19/ är nu den gällande generationen (validering_tm19.py).
  1 klass3   utgivarnas luckor (scripts/runlm_gaps --tolerance), 5 parallellt, + klass3_alla
  2 dokalts  dokumenterade luckor för skattningen (runlm_documented_test med MODEL+tolerance, FILL+name_cands), 5 parallellt
  3 svart4   svåra maskeringsprovet (--hard --tolerance), 5 parallellt; mask4_f* är tol02_f* (redan körda)
  4 fit      scripts/runlm_list_calibrate --write mot tm19/runlm_calibration_tm19.json (kopia av den levande)
  5 dok5     dokumenterade provet med den nya kalibreringen, 5 parallellt + sammanfattning
Loggar: /Volumes/2TB/Antigrvity/Runes/logs/tm19_*.log.
    PYTHONPATH=. .venv/bin/python utdata/runlm_forfining/tm19_pipeline.py [--stage N]
Arbetarläge (internt): --worker dok --fold K --out PATH"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tm19")
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LOGS = "/Volumes/2TB/Antigrvity/Runes/logs"
PY = os.path.join(ROOT, ".venv", "bin", "python")
TOL = "0.02"
CANDS = "40"
CAL19 = os.path.join(OUT, "runlm_calibration_tm19.json")
sys.path.insert(0, ROOT)

KLASS3_FLAGS = ["--max_gaps", "2000", "--lam_name", "0.05", "--lam_class", "0.2", "--window", "-1",
                "--char_fills", "15", "--context_cands", "--n_cands", "100", "--by_word",
                "--near", "0.1", "--near_km", "10.0", "--own_d", "--name_cands", CANDS, "--tolerance", TOL]


def run_parallel(cmds, tag, env=None):
    os.makedirs(LOGS, exist_ok=True)
    procs = []
    for i, cmd in enumerate(cmds):
        log = open(os.path.join(LOGS, f"tm19_{tag}_{i}.log"), "w")
        procs.append((subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                       env={**os.environ, "PYTHONPATH": ROOT, **(env or {})}), cmd))
    bad = [" ".join(cmd) for p, cmd in procs if p.wait() != 0]
    if bad:
        raise SystemExit(f"{tag}: misslyckades:\n" + "\n".join(bad))
    print(f"{tag}: klart ({len(cmds)} körningar)", flush=True)


def stage1():
    run_parallel([[PY, "-m", "scripts.runlm_gaps", "--fold", str(k), *KLASS3_FLAGS,
                   "--out", os.path.join(OUT, f"klass3_f{k}.json")] for k in range(5)], "klass3")
    rows, settings = [], None
    for k in range(5):
        d = json.load(open(os.path.join(OUT, f"klass3_f{k}.json")))
        settings = settings or {**d["settings"], "fold": None}
        rows += d["rows"]
    json.dump({"settings": settings, "rows": rows}, open(os.path.join(OUT, "klass3_alla.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"klass3_alla: {len(rows)} rader", flush=True)


def stage2():
    run_parallel([[PY, __file__, "--worker", "dok", "--fold", str(k), "--out", os.path.join(OUT, f"dok_alts_f{k}.json")]
                  for k in range(5)], "dokalts")


def stage3():
    for k in range(5):
        assert os.path.exists(os.path.join(OUT, f"mask4_f{k}.json")), f"mask4_f{k} saknas (kopiera tol02_f{k})"
    run_parallel([[PY, "-m", "scripts.runlm_restore_test", "--folds", str(k), "--own_d", "--hard",
                   "--name_cands", CANDS, "--tolerance", TOL, "--out", os.path.join(OUT, f"svart4_f{k}.json")]
                  for k in range(5)], "svart4")


def stage4():
    live = os.path.join(ROOT, "data", "runlm_calibration.json")
    shutil.copy2(live, CAL19)
    r = subprocess.run([PY, "-m", "scripts.runlm_list_calibrate", "--write"], cwd=ROOT, capture_output=True, text=True,
                       env={**os.environ, "PYTHONPATH": ROOT, "RUNLM_FORFINING_DIR": OUT, "RUNLM_CALIBRATION": CAL19})
    open(os.path.join(LOGS, "tm19_fit.log"), "w").write(r.stdout + r.stderr)
    if r.returncode != 0:
        raise SystemExit("fit misslyckades, se tm19_fit.log")
    assert json.load(open(live)) != json.load(open(CAL19)), "kalibreringen skrevs inte till tm19-filen"
    print("fit: klart (tm19/runlm_calibration_tm19.json; den levande filen orörd)", flush=True)


def stage5():
    run_parallel([[PY, __file__, "--worker", "dok", "--fold", str(k), "--out", os.path.join(OUT, f"dok5_f{k}.json")]
                  for k in range(5)], "dok5", env={"RUNLM_CALIBRATION": CAL19})
    rows = [x for k in range(5) for x in json.load(open(os.path.join(OUT, f"dok5_f{k}.json")))["rows"]]
    rs = [x for x in rows if x["kind"] == "runsten" and x.get("gold_word")]
    right = sum(x["word_ok"] for x in rs)
    hi = [x for x in rs if x["p"] >= 0.95]
    res = {"gaps": len(rs), "right": right, "word_ok": right / len(rs), "sure_n": len(hi),
           "sure_errors": sum(not x["word_ok"] for x in hi),
           "sure_right": sum(x["word_ok"] for x in hi) / max(1, len(hi)), "mean_p": sum(x["p"] for x in rs) / len(rs)}
    json.dump(res, open(os.path.join(OUT, "tm19_dok_sammanfattning.json"), "w"), indent=1)
    print("DOK5 (runstenar):", json.dumps(res), flush=True)


def worker_dok(fold, out):
    import src.textmodel as tm
    from scripts.runlm_documented_test import run
    tm.FILL = {**tm.FILL, "name_cands": int(CANDS)}
    tm.MODEL = {**tm.MODEL, "tolerance": float(TOL)}
    run(fold, out, own_d=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, default=None)
    ap.add_argument("--worker")
    ap.add_argument("--fold", type=int)
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.worker == "dok":
        return worker_dok(a.fold, a.out)
    os.makedirs(OUT, exist_ok=True)
    stages = {1: stage1, 2: stage2, 3: stage3, 4: stage4, 5: stage5}
    for n in ([a.stage] if a.stage else [1, 2, 3, 4, 5]):
        print(f"--- etapp {n}", flush=True)
        stages[n]()
    print("TÅGET KLART", flush=True)


if __name__ == "__main__":
    main()
