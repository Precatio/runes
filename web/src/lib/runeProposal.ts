// Runa för runa, faster: a PROPOSAL that ties the runes the automatic analysis grouped along the band (groove-7,
// result.runes with their boxes) to the runes of the transliteration, one by one in band order. Nothing in a proposal
// is a link until the user confirms it: a confirmed proposal becomes an ordinary click step (lib/runeLinks.ts), and a
// facit can be saved only when no proposal is left unconfirmed (AutoGrooveReview). Kept free of imports, so that
// tests/test_rune_proposal.py can run it with node.
//
// The order along the band is the analysis' own (src/staveless.group_runes numbers the runes by band piece and by the
// distance along it, from an arbitrary end), so the reading direction may be the reverse: the user can turn it.

export interface ProposalRune { id: number; box?: number[]; n_slices?: number }
export interface ProposalToken { i: number; kind: string; section: string }
export type ProposalStep = { kind: "mark"; xy: [number, number]; tokens: number[] } | { kind: "skip"; token: number };

export interface ProposalPoint { rune: number; xy: [number, number] }

const LINKABLE_KINDS = new Set(["rune", "uncertain", "lost"]);

/** The centre of every grouped rune (its box, fractions of the review image) in image pixels, in band order. */
export function proposalPoints(runes: ProposalRune[], width: number, height: number, reverse = false): ProposalPoint[] {
  const pts = runes
    .filter(r => Array.isArray(r.box) && r.box.length === 4 && (r.n_slices ?? 1) > 0)
    .sort((a, b) => a.id - b.id)
    .map(r => {
      const [x0, y0, x1, y1] = r.box as number[];
      return { rune: r.id, xy: [Math.round(((x0 + x1) / 2) * width), Math.round(((y0 + y1) / 2) * height)] as [number, number] };
    });
  return reverse ? pts.reverse() : pts;
}

const key = (xy: [number, number]) => `${xy[0]},${xy[1]}`;

/** The proposals still waiting for the user: neither confirmed (a click step at the same place) nor rejected. */
export function pendingPoints(points: ProposalPoint[], steps: ProposalStep[], rejected: ReadonlySet<number>): ProposalPoint[] {
  const taken = new Set(steps.flatMap(s => (s.kind === "mark" ? [key(s.xy)] : [])));
  return points.filter(p => !taken.has(key(p.xy)) && !rejected.has(p.rune));
}

/** The token each pending proposal would be tied to: the linkable tokens after the last one handled, in order
 *  (null when the transliteration has run out). */
export function proposedTokens(tokens: ProposalToken[], steps: ProposalStep[], pending: ProposalPoint[],
  section: string | null = null): (number | null)[] {
  let last = -1;
  for (const s of steps) for (const t of s.kind === "mark" ? s.tokens : [s.token]) last = Math.max(last, t);
  const free = tokens.filter(t => t.i > last && LINKABLE_KINDS.has(t.kind) && (section === null || t.section === section));
  return pending.map((_, k) => (k < free.length ? free[k].i : null));
}

/** Confirm the first pending proposal: the click step it becomes (with a bind rune's second token when asked). */
export function confirmStep(point: ProposalPoint, token: number, second: number | null = null): ProposalStep {
  return { kind: "mark", xy: point.xy, tokens: second !== null ? [token, second] : [token] };
}

/** Can a facit be saved? Only when the user has confirmed or rejected every proposal. */
export function facitAllowed(pending: ProposalPoint[], proposalActive: boolean): boolean {
  return !proposalActive || pending.length === 0;
}
