"""Runmodellen utan långt minne (2026-10-25, efter Viktors läsning av Gs 11 och Hs 21): CRNN-modellen lärde sig stenarnas
texter utantill och placerade bokstäverna fel. Den här modellen ser bara en kort bit av remsan åt gången (lite mer än en
runas bredd), så den måste känna igen varje runa på dess form. Texten får dessutom börja vid vilket skiljetecken som
helst (runslingor är slutna och början syns inte alltid); förlusten är den bästa av dessa vridningar av texten.

Steg: förträning på syntetiska remsor, finjustering på de granskade stenarna (med eller utan prövstenar), och prov mot
Viktors läsningar: Gs 11 kolumn 0–900 ska läsas "in osmuntr · kara sun", Hs 21:s första ruta "asmuntr".
    .venv/bin/python -m scripts.runmodell_lokal --synt-steg 4000 --epoker 300 --test-andel 0.25 --ut FIL
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

import numpy as np
import torch
import torch.nn as nn

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from scripts import runmodell_train as T  # noqa: E402
from src import runmodell as rm  # noqa: E402
from src.runmodell_align import forced_align  # noqa: E402

N_CLASSES = len(rm.ALPHABET) + 1


class LocalCNN(nn.Module):
    """Convolutions only: each output step sees about 60 pixels of the strip (a rune and a half), never the whole text."""
    def __init__(self, n_classes: int = N_CLASSES):
        super().__init__()
        def block(i, o, pool):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(), nn.MaxPool2d(pool))
        self.cnn = nn.Sequential(block(1, 32, (2, 2)), block(32, 64, (2, 2)), block(64, 128, (2, 1)),
                                 block(128, 160, (2, 1)), nn.Conv2d(160, 192, (4, 1)), nn.ReLU())
        self.seq = nn.Sequential(nn.Conv1d(192, 192, 5, padding=2), nn.BatchNorm1d(192), nn.ReLU(), nn.Dropout(0.2),
                                 nn.Conv1d(192, 192, 5, padding=2), nn.BatchNorm1d(192), nn.ReLU(), nn.Dropout(0.2),
                                 nn.Conv1d(192, n_classes, 1))

    def forward(self, x):  # (B, 1, 64, W) → (T, B, C), T = W / 4
        f = self.cnn(x).squeeze(2)
        return self.seq(f).log_softmax(1).permute(2, 0, 1)


def rotations(t: str) -> list[str]:
    """The text, and the text started after each word divider (the end then joins the beginning with a divider)."""
    out = [t]
    for i, ch in enumerate(t):
        if ch == rm.DIVIDER and 0 < i < len(t) - 1:
            out.append(t[i + 1:] + rm.DIVIDER + t[:i])
    return out


def best_rotation_losses(lp: torch.Tensor, frames: list[int], targets: list[str]) -> torch.Tensor:
    """Per strip in the batch, the CTC loss (per character) of the best-fitting rotation of its text."""
    ctc = nn.CTCLoss(blank=0, reduction="none", zero_infinity=True)
    out = []
    for k, (t, n) in enumerate(zip(targets, frames)):
        rots = rotations(t)
        lpk = lp[:n, k:k + 1, :].expand(n, len(rots), lp.shape[2])
        ys = [torch.tensor(rm.encode(r)) for r in rots]
        loss = ctc(lpk, torch.cat(ys), torch.full((len(rots),), n), torch.tensor([len(y) for y in ys])) / len(t)
        out.append(loss.min())
    return torch.stack(out)


def strips_tensor(imgs: list[np.ndarray]) -> torch.Tensor:
    W = T.padded(max(i.shape[1] for i in imgs))
    x = torch.zeros(len(imgs), 1, 64, W)
    for k, im in enumerate(imgs):
        x[k, 0, :, :im.shape[1]] = torch.as_tensor(im) / 2.5
    return x


def read(model, s, dev) -> tuple[str, str, list]:
    """The greedy reading, the rotation of the text that fits best, and the known text placed along the strip."""
    with torch.no_grad():
        lp = model(strips_tensor([s["image"]]).to(dev)).cpu()[: s["image"].shape[1] // 4]
    best = min(rotations(s["target"]), key=lambda r: float(nn.CTCLoss(blank=0, zero_infinity=True)(
        lp, torch.tensor(rm.encode(r))[None], torch.tensor([lp.shape[0]]), torch.tensor([len(r)]))))
    return T.greedy(lp), best, forced_align(lp[:, 0].numpy(), best)


def evaluate(model, data, dev, shuffled=False, seed=7) -> float:
    """Median CER (texts of at least 10 characters) against the best rotation; shuffled: another stone's text."""
    rng = random.Random(seed)
    model.eval(); out = []
    for i, s in enumerate(data):
        g, _, _ = read(model, s, dev)
        refs = rotations(s["target"])
        if shuffled:
            other = rng.choice([d for j, d in enumerate(data) if j != i] or [s])
            refs = rotations(other["target"])
        if len(s["target"]) >= 10:
            out.append(min(T.cer(g, r) for r in refs))
    model.train(); T.free_gpu()
    return float(np.median(out)) if out else float("nan")


def viktor_checks(model, data, dev) -> dict:
    """Viktor's readings 2026-10-25 as a key: the placed letters in Gs 11's columns 0–900 against "inosmuntrkarasun",
    and the first letters in Hs 21's box (columns 200–520) against "asmuntr". CER of the placed letters (dividers left
    out); lower is better."""
    by = {s["signum"]: s for s in data}
    checks = {"Gs 11": (0, 900, "inosmuntrkarasun"), "Hs 21": (200, 520, "asmuntr")}
    out = {}
    for sig, (a, b, truth) in checks.items():
        if sig not in by:
            continue
        _, rot, al = read(model, by[sig], dev)
        placed = "".join(ch for ch, f0, f1 in (al or []) if f0 >= 0 and a <= (f0 + f1 + 1) * 2 < b and ch != rm.DIVIDER)
        out[sig] = {"placed": placed, "truth": truth, "cer": T.cer(placed[:len(truth) + 4], truth), "text_starts": rot[:20]}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--synt-steg", type=int, default=0)
    ap.add_argument("--start", default=None)
    ap.add_argument("--epoker", type=int, default=300)
    ap.add_argument("--test-andel", type=float, default=0.0)
    ap.add_argument("--batch", type=int, default=12)
    ap.add_argument("--arbetare", type=int, default=8)
    ap.add_argument("--ut", required=True)
    a = ap.parse_args(argv)
    torch.manual_seed(1); random.seed(1); np.random.seed(1); rng = random.Random(1)
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    data = T.stones("granskad", {"tydlig", "medel", "svår"}, clean=True)
    train, test = T.split(data, a.test_andel, 1) if a.test_andel else (data, [])
    print(f"{len(train)} stenar i träningen, {len(test)} prövas; {dev}", flush=True)
    model = LocalCNN().to(dev)
    if a.start:
        model.load_state_dict(torch.load(a.start, map_location=dev)["state"])
    t0 = time.time()
    if a.synt_steg:
        from src import runmodell_synt as sy
        texts = sy.corpus_texts({s["signum"] for s in test if s["signum"]})
        dl = torch.utils.data.DataLoader(T.SyntheticStrips(texts, 32, 1), batch_size=None, num_workers=a.arbetare,
                                         persistent_workers=True, prefetch_factor=4)
        opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
        sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=2e-3, total_steps=a.synt_steg, pct_start=0.1)
        ctc = nn.CTCLoss(blank=0, zero_infinity=True); tot = 0.0
        for step, items in enumerate(dl, 1):
            x = strips_tensor([np.asarray(im) for im, _ in items])
            ys = [torch.tensor(rm.encode(t)) for _, t in items]
            lp = model(x.to(dev)).cpu()
            loss = ctc(lp, torch.cat(ys), torch.tensor([max(1, min(lp.shape[0], np.asarray(im).shape[1] // 4)) for im, _ in items]),
                       torch.tensor([len(y) for y in ys]))
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step(); sched.step()
            tot += loss.item()
            if step % max(1, a.synt_steg // 8) == 0:
                print(f"förträning {step}/{a.synt_steg} ({(time.time() - t0) / 60:.0f} min, {T.gpu_mb()}): förlust "
                      f"{tot / (a.synt_steg // 8):.3f}", flush=True); tot = 0.0; T.free_gpu()
            if step >= a.synt_steg:
                break
        torch.save({"state": model.state_dict()}, os.path.splitext(a.ut)[0] + "_fortranad.pt")
    opt = torch.optim.AdamW(model.parameters(), lr=5e-4, weight_decay=1e-4)
    for ep in range(1, a.epoker + 1):
        order = sorted(train, key=lambda s: s["image"].shape[1] * rng.uniform(0.8, 1.2))
        batches = [order[i:i + a.batch] for i in range(0, len(order), a.batch)]
        random.shuffle(batches); tot = 0.0
        for bt in batches:
            imgs = [T.augment(s["image"], rng) for s in bt]
            lp = model(strips_tensor(imgs).to(dev)).cpu()
            loss = best_rotation_losses(lp, [im.shape[1] // 4 for im in imgs], [s["target"] for s in bt]).mean()
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step()
            tot += loss.item()
        T.free_gpu()
        if ep % max(1, a.epoker // 10) == 0 or ep == a.epoker:
            msg = f"epok {ep} ({(time.time() - t0) / 60:.0f} min, {T.gpu_mb()}): förlust {tot / len(batches):.3f}, CER träning {evaluate(model, train, dev):.2f}"
            if test:
                msg += f", CER prövning {evaluate(model, test, dev):.2f} (mot omflyttad text {evaluate(model, test, dev, True):.2f})"
            vk = viktor_checks(model, data, dev)
            msg += " | Viktors facit: " + ", ".join(f"{k} {v['cer']:.2f}" for k, v in vk.items())
            print(msg, flush=True)
    torch.save({"state": model.state_dict()}, a.ut)
    res = {"viktor": viktor_checks(model, data, dev), "cer_train": evaluate(model, train, dev)}
    if test:
        res.update({"cer_test": evaluate(model, test, dev), "cer_shuffled": evaluate(model, test, dev, True),
                    "test": [{"signum": s["signum"], "read": read(model, s, dev)[0], "text": s["target"]} for s in test]})
    json.dump(res, open(os.path.splitext(a.ut)[0] + "_resultat.json", "w"), ensure_ascii=False, indent=1)
    for k, v in res["viktor"].items():
        print(f"{k}: placerat {v['placed'][:30]!r} mot Viktors {v['truth']!r} (CER {v['cer']:.2f}); texten börjar {v['text_starts']!r}")


if __name__ == "__main__":
    main()
