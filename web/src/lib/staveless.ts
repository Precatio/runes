// When the automatic analysis's staveless mode (src/staveless.py) is switched on by itself: Rundata gives staveless runes
// and no other rune type for the stone (Hs 10, 12, 14, 15). On stones with long-branch runes and staveless r and u
// (M 3, M 7, M 8, Sö 164) the mode divided the runes too finely (utdata/stavlosa/), so it is left to the user there.
export function allStaveless(runeTypes: string | null | undefined): boolean {
  const t = (runeTypes ?? "").trim().toLowerCase();
  return /^stavlös/.test(t) && !/kvist|\+|,| och /.test(t);
}

export function someStaveless(runeTypes: string | null | undefined): boolean {
  return /stavlös/i.test(runeTypes ?? "");
}
