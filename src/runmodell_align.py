"""Runmodellen, steg A: runornas lägen genom tvingad inpassning (forced alignment). Texten är känd ur Rundata, så
modellen behöver inte gissa bokstäverna, bara lägga den kända texten längs remsan: den mest sannolika vägen genom CTC:s
gitter där varje tecken i texten måste användas i ordning (Viterbi). Ger för varje tecken de kolumner i remsan där
modellen placerar det, och via remsans mittlinje platsen på stenen."""
from __future__ import annotations

import numpy as np

from src import runmodell as rm


def forced_align(logp: np.ndarray, target: str) -> list[tuple[str, int, int]] | None:
    """logp: (T, C) log-probabilities from the model (class 0 = blank). Returns (character, first frame, last frame) for
    every character of target, or None when the strip is too short for the text."""
    y = rm.encode(target)
    T = logp.shape[0]
    S = 2 * len(y) + 1  # blank, y1, blank, y2, …, blank
    lab = [0 if s % 2 == 0 else y[s // 2] for s in range(S)]
    if T < len(y):
        return None
    NEG = -1e30
    dp = np.full((T, S), NEG)
    back = np.zeros((T, S), np.int8)  # 0 stay, 1 from s−1, 2 from s−2
    dp[0, 0] = logp[0, lab[0]]
    if S > 1:
        dp[0, 1] = logp[0, lab[1]]
    for t in range(1, T):
        for s in range(S):
            cands = [dp[t - 1, s]]
            if s >= 1:
                cands.append(dp[t - 1, s - 1])
            if s >= 2 and lab[s] != 0 and lab[s] != lab[s - 2]:
                cands.append(dp[t - 1, s - 2])
            k = int(np.argmax(cands))
            dp[t, s] = cands[k] + logp[t, lab[s]]
            back[t, s] = k
    s = S - 1 if S == 1 or dp[T - 1, S - 1] >= dp[T - 1, S - 2] else S - 2
    path = np.zeros(T, int)
    for t in range(T - 1, -1, -1):
        path[t] = s
        s -= int(back[t, s])
    out = []
    for i, ch in enumerate(target):
        frames = np.where(path == 2 * i + 1)[0]
        if len(frames):
            out.append((ch, int(frames[0]), int(frames[-1])))
        else:
            out.append((ch, -1, -1))
    return out
