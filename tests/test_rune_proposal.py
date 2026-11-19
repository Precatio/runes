"""Snabbare Runa för runa: förslaget som knyter analysens runor längs slingan till translittereringen
(web/src/lib/runeProposal.ts, 2026-11-19). Inget förslag blir en koppling förrän det bekräftas, och facit får
sparas först när varje förslag är bekräftat eller avvisat."""
import json

from tests.ts_runner import run_ts

RUNES = [{"id": 2, "box": [0.4, 0.1, 0.6, 0.3], "n_slices": 3}, {"id": 1, "box": [0.0, 0.0, 0.2, 0.2], "n_slices": 5},
         {"id": 3, "box": [0.8, 0.8, 1.0, 1.0], "n_slices": 2}, {"id": 4, "n_slices": 1}]
TOKENS = [{"i": 0, "kind": "rune", "section": "A"}, {"i": 1, "kind": "rune", "section": "A"},
          {"i": 2, "kind": "divider", "section": "A"}, {"i": 3, "kind": "uncertain", "section": "A"},
          {"i": 4, "kind": "lost", "section": "A"}]


def _run(body: str):
    return run_ts("runeProposal", f"const runes = {json.dumps(RUNES)}; const tokens = {json.dumps(TOKENS)};\n{body}")


def test_points_follow_band_order_and_can_be_turned():
    got = _run("console.log(JSON.stringify([M.proposalPoints(runes, 100, 50), M.proposalPoints(runes, 100, 50, true)]));")
    fwd, rev = got
    assert [p["rune"] for p in fwd] == [1, 2, 3]  # rune 4 has no box
    assert fwd[0]["xy"] == [10, 5] and fwd[1]["xy"] == [50, 10]
    assert [p["rune"] for p in rev] == [3, 2, 1]


def test_tokens_are_proposed_in_order_and_skip_dividers():
    got = _run("const pts = M.proposalPoints(runes, 100, 50);"
               "const pend = M.pendingPoints(pts, [], new Set());"
               "console.log(JSON.stringify(M.proposedTokens(tokens, [], pend)));")
    assert got == [0, 1, 3]


def test_nothing_is_linked_until_confirmed_and_facit_waits():
    got = _run("""
const pts = M.proposalPoints(runes, 100, 50);
let steps = [];
const rejected = new Set();
const out = {};
out.before = M.facitAllowed(M.pendingPoints(pts, steps, rejected), true);
// confirm the first, reject the second, skip a token in the text (the rune cannot be seen)
let pend = M.pendingPoints(pts, steps, rejected);
steps = [...steps, M.confirmStep(pend[0], M.proposedTokens(tokens, steps, pend)[0])];
out.afterConfirm = M.proposedTokens(tokens, steps, M.pendingPoints(pts, steps, rejected));
rejected.add(M.pendingPoints(pts, steps, rejected)[0].rune);
steps = [...steps, {kind: "skip", token: 1}];
pend = M.pendingPoints(pts, steps, rejected);
out.pending = pend.map(p => p.rune);
out.proposed = M.proposedTokens(tokens, steps, pend);
out.mid = M.facitAllowed(pend, true);
steps = [...steps, M.confirmStep(pend[0], out.proposed[0])];
out.end = M.facitAllowed(M.pendingPoints(pts, steps, rejected), true);
out.steps = steps;
out.withoutProposal = M.facitAllowed(pts, false);
console.log(JSON.stringify(out));
""")
    assert got["before"] is False
    assert got["afterConfirm"] == [1, 3]
    assert got["pending"] == [3] and got["proposed"] == [3]
    assert got["mid"] is False and got["end"] is True
    assert got["steps"][0] == {"kind": "mark", "xy": [10, 5], "tokens": [0]}
    assert got["steps"][-1]["tokens"] == [3]
    assert got["withoutProposal"] is True


def test_bind_rune_confirmation_takes_two_tokens():
    got = _run("console.log(JSON.stringify(M.confirmStep({rune: 1, xy: [1, 2]}, 0, 1)));")
    assert got == {"kind": "mark", "xy": [1, 2], "tokens": [0, 1]}
