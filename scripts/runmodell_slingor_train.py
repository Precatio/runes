"""Steg B: slingmodellen – ett litet U-nät som på en djupbild markerar var runslingorna går (Viktors 95 granskade stenar
som facit, scripts/runmodell_slingdata.py). Tränas på slumpvisa utsnitt med vridning, spegling och djupskalning;
prövas på stenar som hålls utanför (en fjärdedel per serie), med överlappet (IoU) mellan modellens och Viktors slingor.
    .venv/bin/python -m scripts.runmodell_slingor_train [--epoker 150] [--ut FIL]"""
from __future__ import annotations

import argparse
import glob
import os
import random
import sys
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
DATA = "/Volumes/2TB/cache/runmodell/slingor"


class UNet(nn.Module):
    def __init__(self, c=24):
        super().__init__()
        def blk(i, o):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(),
                                 nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU())
        self.d1, self.d2, self.d3, self.d4 = blk(2, c), blk(c, 2 * c), blk(2 * c, 4 * c), blk(4 * c, 8 * c)
        self.u3, self.u2, self.u1 = blk(12 * c, 4 * c), blk(6 * c, 2 * c), blk(3 * c, c)
        self.out = nn.Conv2d(c, 1, 1)

    def forward(self, x):
        a = self.d1(x); b = self.d2(F.max_pool2d(a, 2)); c = self.d3(F.max_pool2d(b, 2)); d = self.d4(F.max_pool2d(c, 2))
        up = lambda t, ref: F.interpolate(t, size=ref.shape[-2:], mode="bilinear", align_corners=False)
        c = self.u3(torch.cat([up(d, c), c], 1)); b = self.u2(torch.cat([up(c, b), b], 1)); a = self.u1(torch.cat([up(b, a), a], 1))
        return self.out(a)


def load():
    out = []
    for f in sorted(glob.glob(os.path.join(DATA, "*.npz"))):
        z = np.load(f)
        out.append({"name": os.path.basename(f)[:-4], "series": os.path.basename(f).split("__")[0],
                    "depth": z["depth"].astype(np.float32), "mask": z["mask"].astype(np.float32),
                    "region": z["region"].astype(np.float32)})
    return out


def split(data, share=0.25, seed=1):
    rng = random.Random(seed); train, test = [], []
    for s in sorted({d["series"] for d in data}):
        g = sorted([d for d in data if d["series"] == s], key=lambda d: d["name"]); rng.shuffle(g)
        k = round(len(g) * share); test += g[:k]; train += g[k:]
    return train, test


def inputs(d):
    return np.stack([np.clip(d["depth"], 0, 3) / 3.0 * d["region"], d["region"]])


def crop(d, size, rng):
    H, W = d["depth"].shape
    ph, pw = max(0, size - H), max(0, size - W)
    x = np.pad(inputs(d), ((0, 0), (0, ph), (0, pw))); m = np.pad(d["mask"], ((0, ph), (0, pw)))
    y0 = rng.integers(0, x.shape[1] - size + 1); x0 = rng.integers(0, x.shape[2] - size + 1)
    x, m = x[:, y0:y0 + size, x0:x0 + size], m[y0:y0 + size, x0:x0 + size]
    k = rng.integers(4)
    x, m = np.rot90(x, k, axes=(1, 2)), np.rot90(m, k)
    if rng.random() < 0.5:
        x, m = x[:, :, ::-1], m[:, ::-1]
    x = x.copy(); x[0] *= rng.uniform(0.7, 1.3)
    return x, m.copy()


def predict(model, d, dev):
    x = torch.from_numpy(inputs(d))[None].to(dev)
    H, W = x.shape[-2:]
    ph, pw = (-H) % 8, (-W) % 8
    with torch.no_grad():
        p = torch.sigmoid(model(F.pad(x, (0, pw, 0, ph))))[0, 0, :H, :W].cpu().numpy()
    return p * d["region"]


def iou(p, m, thr=0.5):
    a, b = p >= thr, m > 0.5
    return float((a & b).sum() / max(1, (a | b).sum()))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--epoker", type=int, default=150)
    ap.add_argument("--ut", default="/Volumes/2TB/cache/runmodell/slingmodell.pt")
    a = ap.parse_args(argv)
    torch.manual_seed(1); rng = np.random.default_rng(1)
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    data = load(); train, test = split(data)
    print(f"{len(train)} stenar i träningen, {len(test)} prövas; {dev}", flush=True)
    model = UNet().to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, a.epoker)
    t0 = time.time()
    for ep in range(1, a.epoker + 1):
        model.train(); tot = 0.0
        for _ in range(8):  # eight batches of 16 random crops per epoch
            xs, ms = zip(*(crop(train[rng.integers(len(train))], 192, rng) for _ in range(16)))
            x = torch.from_numpy(np.stack(xs)).to(dev); m = torch.from_numpy(np.stack(ms))[:, None].to(dev)
            logit = model(x); p = torch.sigmoid(logit)
            dice = 1 - (2 * (p * m).sum() + 1) / (p.sum() + m.sum() + 1)
            loss = F.binary_cross_entropy_with_logits(logit, m) + dice
            opt.zero_grad(); loss.backward(); opt.step(); tot += loss.item()
        sched.step()
        if ep % max(1, a.epoker // 10) == 0 or ep == a.epoker:
            model.eval()
            ious = [iou(predict(model, d, dev), d["mask"]) for d in test]
            print(f"epok {ep} ({(time.time() - t0) / 60:.0f} min): förlust {tot / 8:.3f}, IoU prövning median {np.median(ious):.2f}", flush=True)
    torch.save({"state": model.state_dict()}, a.ut)
    model.eval()
    for d in test:
        print(f"   {d['name'][:45]:45} IoU {iou(predict(model, d, dev), d['mask']):.2f}")


if __name__ == "__main__":
    main()
