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
FREE = False  # --fri-riktning: the model may choose reading direction and up/down (before 2026-10-25 always)


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


def greedy(logp: torch.Tensor, frames: int | None = None) -> str:
    """Best path: the most probable class per step, repeats merged and blanks dropped (only the first `frames` steps,
    the strip itself without the padding)."""
    ids = logp.argmax(-1).squeeze(1).tolist()[:frames]
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


def stones(status: str | None, quality: set[str] | None = None, clean: bool = False) -> list[dict]:
    """The checked stones; with `quality` only those rated so (tydlig, medel, svår); with `clean` without fully staveless
    inscriptions, stones split over several files (each file would get the whole stone's text) and texts under 15
    characters."""
    out = []
    if not os.path.isdir(rm.BAND_DIR):
        return out
    for series in sorted(os.listdir(rm.BAND_DIR)):
        for f in sorted(os.listdir(os.path.join(rm.BAND_DIR, series))):
            if f.endswith(".json"):
                s = rm.stone_strip(series, f[:-5])
                if s and s["target"] and (status is None or s["status"] == status):
                    out.append(s)
    if quality:
        out = [s for s in out if s.get("quality") in quality]
    if clean:
        import collections
        files = collections.Counter(s["signum"] for s in out if s["signum"])
        out = [s for s in out if not ("stavlösa" in s["rune_types"] and "långkvist" not in s["rune_types"])
               and files.get(s["signum"], 1) == 1 and len(s["target"]) >= 15]
    return out


BUCKET = 256  # widths are padded to whole steps: the GPU (MPS) keeps a compiled variant per input shape, and hundreds
# of distinct strip widths made the process grow past 20 GB (2026-10-25)


def padded(w: int) -> int:
    return -(-w // BUCKET) * BUCKET


def tensor(img: np.ndarray, flip_lr=False, flip_ud=False) -> torch.Tensor:
    x = img[:, ::-1] if flip_lr else img
    x = x[::-1, :] if flip_ud else x
    out = np.zeros((x.shape[0], padded(x.shape[1])), np.float32)
    out[:, :x.shape[1]] = x / 2.5
    return torch.from_numpy(out)[None, None]


def free_gpu():
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()


def gpu_mb() -> str:
    return f"{torch.mps.driver_allocated_memory() / 2**20:.0f} MB GPU" if torch.backends.mps.is_available() else ""


def augment(img: np.ndarray, rng: random.Random) -> np.ndarray:
    """Training variation, so that the model learns the runes rather than the 28 strips: the strip stretched or
    squeezed along the band (other carvers, other spacing), the depth scaled (other weathering, other scanner) and a
    little noise."""
    from PIL import Image
    w = max(8, round(img.shape[1] * rng.uniform(0.8, 1.25)))
    x = np.asarray(Image.fromarray(img.astype(np.float32)).resize((w, img.shape[0]), Image.BILINEAR))
    x = x * rng.uniform(0.75, 1.25) + np.random.default_rng(rng.randrange(1 << 30)).normal(0, 0.05, x.shape)
    return np.clip(x, 0, 3.0).astype(np.float32)


def split(data: list[dict], share: float, seed: int) -> tuple[list[dict], list[dict]]:
    """A share of each series' stones held out for testing (the same stones every run with the same seed)."""
    rng = random.Random(seed)
    train, test = [], []
    for series in sorted({s["series"] for s in data}):
        g = sorted((s for s in data if s["series"] == series), key=lambda s: s["stem"])
        rng.shuffle(g)
        k = round(len(g) * share)
        test += g[:k]
        train += g[k:]
    return train, test


class SyntheticStrips(torch.utils.data.IterableDataset):
    """Endless batches of synthetic strips (src/runmodell_synt.py), generated in the DataLoader's worker processes."""
    def __init__(self, texts: list[str], batch: int, seed: int):
        self.texts, self.batch, self.seed = texts, batch, seed

    def __iter__(self):
        from src import runmodell_synt as sy
        info = torch.utils.data.get_worker_info()
        rng = np.random.default_rng(self.seed + (info.id if info else 0) * 7919)
        while True:
            items = []
            for _ in range(self.batch):
                t = sy.sample_text(self.texts, rng)
                im = sy.strip(t, rng)
                if FREE and rng.random() < 0.5:
                    im = im[::-1, :].copy()  # runes upside down (only when the orientation is left to the model)
                items.append((im, t))
            yield items


def batch_loss(model, imgs: list[np.ndarray], targets: list[str], dev, flips_ud: list[bool]) -> torch.Tensor:
    """Mean CTC loss over a batch of strips padded to the same width; per strip the smaller of read as drawn and
    read reversed (the reading direction that fits the text)."""
    ctc = nn.CTCLoss(blank=0, reduction="none", zero_infinity=True)
    W = padded(max(i.shape[1] for i in imgs))
    ys = [torch.tensor(rm.encode(t), dtype=torch.long) for t in targets]
    y = torch.cat(ys)
    ylen = torch.tensor([len(t) for t in ys])
    per_dir = []
    for lr in ((False, True) if FREE else (False,)):
        x = torch.zeros(len(imgs), 1, imgs[0].shape[0], W)
        for k, (im, ud) in enumerate(zip(imgs, flips_ud)):
            x[k, 0, :, :im.shape[1]] = tensor(im, lr, ud)[0, 0, :, :im.shape[1]]
        lp = model(x.to(dev)).cpu()  # (T, B, C)
        T = lp.shape[0]
        xlen = torch.tensor([max(1, min(T, im.shape[1] // 4)) for im in imgs])
        per_dir.append(ctc(lp, y, xlen, ylen) / ylen.clamp(min=1))
    return (torch.minimum(*per_dir) if len(per_dir) > 1 else per_dir[0]).mean()


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
            orients = [(lr, ud) for lr in (False, True) for ud in (False, True)] if FREE else [(False, False)]
            best = min(cer(greedy(model(tensor(s["image"], lr, ud).to(dev)).cpu(), s["image"].shape[1] // 4), ref)
                       for lr, ud in orients)
            out.append(best)
    model.train()
    free_gpu()
    return float(np.median([c for c, d in zip(out, data) if len(d["target"]) >= 10])) if out else float("nan")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--status", default=None, help="bara stenar med denna status (granskad), annars alla ritade")
    ap.add_argument("--holdout", default=None, help="serie som hålls utanför träningen och prövas")
    ap.add_argument("--epoker", type=int, default=300)
    ap.add_argument("--test-andel", type=float, default=0.0, help="andel av varje series stenar som hålls utanför")
    ap.add_argument("--frö", type=int, default=1)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--fri-riktning", action="store_true", help="låt modellen välja läsriktning och upp/ned (det gamla "
                    "sättet); annars gäller den ritade riktningen och runorna står upprätt i remsan")
    ap.add_argument("--kvalitet", default=None, help="bara stenar med dessa betyg, t.ex. tydlig eller tydlig,medel")
    ap.add_argument("--ren", action="store_true", help="utan stavlösa, delade stenar och texter under 15 tecken")
    ap.add_argument("--start", default=None, help="börja från en sparad modell (t.ex. den syntetiskt förtränade)")
    ap.add_argument("--forst-tydlig", type=int, default=0, help="så många epoker först med bara tydliga stenar (läroplan)")
    ap.add_argument("--synt-steg", type=int, default=0, help="förträning: så många batchar syntetiska remsor först")
    ap.add_argument("--synt-batch", type=int, default=32)
    ap.add_argument("--arbetare", type=int, default=8, help="processer som tillverkar syntetiska remsor")
    ap.add_argument("--ut", default="/Volumes/2TB/cache/runmodell/modell.pt")
    a = ap.parse_args(argv)
    global FREE
    FREE = a.fri_riktning
    torch.manual_seed(1); random.seed(1); np.random.seed(1)
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    data = stones(a.status, set(a.kvalitet.split(",")) if a.kvalitet else None, a.ren)
    if a.test_andel:
        train, test = split(data, a.test_andel, a.frö)
    else:
        train = [s for s in data if s["series"] != a.holdout]
        test = [s for s in data if s["series"] == a.holdout] if a.holdout else []

    print(f"{len(train)} stenar i träningen ({sum(len(s['target']) for s in train)} tecken), {len(test)} prövas; {dev}", flush=True)
    rng = random.Random(a.frö)
    import time
    t0 = time.time()
    model = CRNN().to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    if a.start:
        model.load_state_dict(torch.load(a.start, map_location=dev)["state"])
        opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
        print(f"start från {a.start}", flush=True)
    if a.synt_steg:
        from src import runmodell_synt as sy
        texts = sy.corpus_texts({s["signum"] for s in test if s["signum"]})
        dl = torch.utils.data.DataLoader(SyntheticStrips(texts, a.synt_batch, a.frö), batch_size=None,
                                         num_workers=a.arbetare, persistent_workers=True, prefetch_factor=4)
        print(f"förträning: {a.synt_steg} batchar à {a.synt_batch} syntetiska remsor ur {len(texts)} texter, {a.arbetare} processer", flush=True)
        sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=2e-3, total_steps=a.synt_steg, pct_start=0.1)
        tot = 0.0
        for step, items in enumerate(dl, 1):
            ctc_f = nn.CTCLoss(blank=0, reduction="mean", zero_infinity=True)
            W = padded(max(im.shape[1] for im, _ in items))
            x = torch.zeros(len(items), 1, 64, W)
            for k, (im, _) in enumerate(items):
                x[k, 0, :, :im.shape[1]] = torch.as_tensor(im) / 2.5
            ys = [torch.tensor(rm.encode(t)) for _, t in items]
            lp = model(x.to(dev)).cpu()
            xlen = torch.tensor([max(1, min(lp.shape[0], im.shape[1] // 4)) for im, _ in items])
            loss = ctc_f(lp, torch.cat(ys), xlen, torch.tensor([len(y) for y in ys]))
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step(); sched.step()
            tot += loss.item()
            if step % max(1, a.synt_steg // 10) == 0:
                msg = f"förträning {step}/{a.synt_steg} ({(time.time() - t0) / 60:.0f} min): förlust {tot / (a.synt_steg // 10):.3f}"
                tot = 0.0
                if test:
                    msg += f", CER prövning {evaluate(model, test, dev):.2f} (mot omflyttad text {evaluate(model, test, dev, True):.2f})"
                print(msg, flush=True)
            if step >= a.synt_steg:
                break
        torch.save({"state": model.state_dict(), "alphabet": rm.ALPHABET}, os.path.splitext(a.ut)[0] + "_fortranad.pt")
        opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)  # gentler fine-tuning on the real stones
    for ep in range(1, a.epoker + 1):
        # Batches of strips of similar width (less padding), in a new order every epoch
        pool = [s for s in train if s.get("quality") == "tydlig"] if ep <= a.forst_tydlig else train
        if ep == 1 and a.forst_tydlig:
            print(f"läroplan: epok 1–{a.forst_tydlig} med {len(pool)} tydliga stenar, sedan alla {len(train)}", flush=True)
        order = sorted(pool, key=lambda s: s["image"].shape[1] * rng.uniform(0.8, 1.2))
        batches = [order[i:i + a.batch] for i in range(0, len(order), a.batch)]
        random.shuffle(batches)
        tot = 0.0
        for bt in batches:
            loss = batch_loss(model, [augment(s["image"], rng) for s in bt], [s["target"] for s in bt], dev,
                              [FREE and random.random() < 0.5 for _ in bt])
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            tot += loss.item() * len(bt)
        free_gpu()
        if ep % max(1, a.epoker // 10) == 0 or ep == a.epoker:
            msg = f"epok {ep} ({(time.time() - t0) / 60:.0f} min, {gpu_mb()}): förlust {tot / max(1, len(train)):.3f}, CER träning {evaluate(model, train, dev):.2f}"
            if test:
                msg += f", CER prövning {evaluate(model, test, dev):.2f} (mot omflyttad text {evaluate(model, test, dev, True):.2f})"
            print(msg, flush=True)
    os.makedirs(os.path.dirname(a.ut), exist_ok=True)
    torch.save({"state": model.state_dict(), "alphabet": rm.ALPHABET}, a.ut)
    rows = []
    for s in (test or train[:3]):
        with torch.no_grad():
            model.eval()
            preds = [(cer(p := greedy(model(tensor(s["image"], lr, False).to(dev)).cpu(), s["image"].shape[1] // 4), s["target"]), p) for lr in ((False, True) if FREE else (False,))]
        e, p = min(preds)
        print(f"{s['signum']}: läst  {p[:70]}\n{'':{len(str(s['signum']))}}  text  {s['target'][:70]}  (CER {e:.2f})")
        rows.append({"signum": s["signum"], "series": s["series"], "stem": s["stem"], "cer": e, "read": p, "text": s["target"],
                     "quality": s.get("quality")})
    import json
    for q in ("tydlig", "medel", "svår"):
        sub = [s for s in test if s.get("quality") == q]
        if sub:
            print(f"prövning, {q}: {len(sub)} stenar, median-CER {evaluate(model, sub, dev):.2f} (mot omflyttad {evaluate(model, sub, dev, True):.2f})")
    json.dump({"train": [s["stem"] for s in train], "test": rows,
               "cer_test": evaluate(model, test, dev) if test else None,
               "cer_shuffled": evaluate(model, test, dev, True) if test else None},
              open(os.path.splitext(a.ut)[0] + "_resultat.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
