"""Tränar runmodellen (minnet rune-recognizer): en CRNN med CTC som läser de uträtade runslingorna (src/runmodell.py)
mot Rundatas text. Läsriktningen ritas av en människa men kan vara fel, så förlusten för en sten är den bättre av
remsan och den spegelvända remsan; remsan vänds också upp och ned slumpvis, eftersom runorna kan stå på vilken sida
av linjen som helst.

    .venv/bin/python -m scripts.runmodell_train [--status granskad] [--holdout SERIE] [--epoker 300] [--ut FIL]
Utan --holdout tränas på alla stenar med ritade slingor (överanpassningsprov); med --holdout hålls en serie utanför
och teckenfelet (CER) redovisas för den, mot samma stenar lästa mot omflyttade texter.
"""
from __future__ import annotations

import argparse
import os
import random
import sys

import numpy as np
import torch
import torch.nn as nn

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from src import runmodell as rm  # noqa: E402

N_CLASSES = len(rm.ALPHABET) + 1  # + CTC blank


class CRNN(nn.Module):
    def __init__(self, n_classes: int = N_CLASSES, hidden: int = 128):
        super().__init__()
        def block(i, o, pool):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(), nn.MaxPool2d(pool))
        self.cnn = nn.Sequential(block(1, 32, (2, 2)), block(32, 64, (2, 2)), block(64, 128, (2, 1)),
                                 block(128, 128, (2, 1)), nn.Conv2d(128, 128, (4, 1)), nn.ReLU())
        self.rnn = nn.LSTM(128, hidden, num_layers=2, bidirectional=True, batch_first=True, dropout=0.2)
        self.out = nn.Linear(2 * hidden, n_classes)

    def forward(self, x):  # x: (B, 1, 64, W) → (T, B, C) log-probabilities, T = W / 4
        f = self.cnn(x).squeeze(2).permute(0, 2, 1)
        y, _ = self.rnn(f)
        return self.out(y).log_softmax(-1).permute(1, 0, 2)


def greedy(logp: torch.Tensor) -> str:
    """Best path: the most probable class per step, repeats merged and blanks dropped."""
    ids = logp.argmax(-1).squeeze(1).tolist()
    out, prev = [], 0
    for i in ids:
        if i != prev and i != 0:
            out.append(rm.ALPHABET[i - 1])
        prev = i
    return "".join(out)


def cer(pred: str, ref: str) -> float:
    """Character error rate: edit distance / length of the reference."""
    d = list(range(len(ref) + 1))
    for i, a in enumerate(pred, 1):
        prev, d[0] = d[0], i
        for j, b in enumerate(ref, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (a != b))
    return d[-1] / max(1, len(ref))


def stones(status: str | None) -> list[dict]:
    out = []
    if not os.path.isdir(rm.BAND_DIR):
        return out
    for series in sorted(os.listdir(rm.BAND_DIR)):
        for f in sorted(os.listdir(os.path.join(rm.BAND_DIR, series))):
            if f.endswith(".json"):
                s = rm.stone_strip(series, f[:-5])
                if s and s["target"] and (status is None or s["status"] == status):
                    out.append(s)
    return out


def tensor(img: np.ndarray, flip_lr=False, flip_ud=False) -> torch.Tensor:
    x = img[:, ::-1] if flip_lr else img
    x = x[::-1, :] if flip_ud else x
    return torch.from_numpy(np.ascontiguousarray(x / 2.5, dtype=np.float32))[None, None]


def loss_both(model, ctc, img, target, dev, flip_ud):
    """CTC loss for the strip and for it reversed; the smaller one (the reading direction that fits the text)."""
    y = torch.tensor(rm.encode(target), dtype=torch.long)
    losses = []
    for lr in (False, True):
        lp = model(tensor(img, lr, flip_ud).to(dev))
        losses.append(ctc(lp.cpu(), y[None], torch.tensor([lp.shape[0]]), torch.tensor([len(y)])))
    return torch.minimum(*losses), int(losses[1] < losses[0])


def evaluate(model, data, dev, shuffled=False, seed=7):
    """Mean CER over stones, reading each strip in the direction that fits best; with shuffled=True the reference is
    another stone's text of similar length (the control)."""
    rng = random.Random(seed)
    model.eval()
    out = []
    with torch.no_grad():
        for i, s in enumerate(data):
            ref = s["target"]
            if shuffled:
                others = [d["target"] for j, d in enumerate(data) if j != i] or [ref]
                ref = "".join(rng.sample(list(ref), len(ref))) if len(others) == 1 else rng.choice(others)
            best = min(cer(greedy(model(tensor(s["image"], lr, ud).to(dev)).cpu()), ref)
                       for lr in (False, True) for ud in (False, True))
            out.append(best)
    model.train()
    return float(np.mean(out)) if out else float("nan")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--status", default=None, help="bara stenar med denna status (granskad), annars alla ritade")
    ap.add_argument("--holdout", default=None, help="serie som hålls utanför träningen och prövas")
    ap.add_argument("--epoker", type=int, default=300)
    ap.add_argument("--ut", default="/Volumes/2TB/cache/runmodell/modell.pt")
    a = ap.parse_args(argv)
    torch.manual_seed(1); random.seed(1); np.random.seed(1)
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    data = stones(a.status)
    train = [s for s in data if s["series"] != a.holdout]
    test = [s for s in data if s["series"] == a.holdout] if a.holdout else []
    print(f"{len(train)} stenar i träningen ({sum(len(s['target']) for s in train)} tecken), {len(test)} prövas; {dev}", flush=True)
    model = CRNN().to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    ctc = nn.CTCLoss(blank=0, zero_infinity=True)
    for ep in range(1, a.epoker + 1):
        random.shuffle(train)
        tot = 0.0
        for s in train:
            loss, _ = loss_both(model, ctc, s["image"], s["target"], dev, random.random() < 0.5)
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            tot += loss.item()
        if ep % max(1, a.epoker // 10) == 0 or ep == a.epoker:
            msg = f"epok {ep}: förlust {tot / max(1, len(train)):.3f}, CER träning {evaluate(model, train, dev):.2f}"
            if test:
                msg += f", CER prövning {evaluate(model, test, dev):.2f} (mot omflyttad text {evaluate(model, test, dev, True):.2f})"
            print(msg, flush=True)
    os.makedirs(os.path.dirname(a.ut), exist_ok=True)
    torch.save({"state": model.state_dict(), "alphabet": rm.ALPHABET}, a.ut)
    for s in (test or train)[:3]:
        with torch.no_grad():
            model.eval()
            preds = [(cer(p := greedy(model(tensor(s["image"], lr, False).to(dev)).cpu()), s["target"]), p) for lr in (False, True)]
        e, p = min(preds)
        print(f"{s['signum']}: läst  {p[:70]}\n{'':{len(str(s['signum']))}}  text  {s['target'][:70]}  (CER {e:.2f})")


if __name__ == "__main__":
    main()
