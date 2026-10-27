// Standardised rune tags so that the same rune can be compared across stones.
// Younger futhark (long-branch and short-twig variants) plus common medieval additions.
export const RUNE_TAGS: { tag: string; name: string; group: string }[] = [
  { tag: "ᚠ f", name: "fé", group: "Långkvist" },
  { tag: "ᚢ u", name: "úr", group: "Långkvist" },
  { tag: "ᚦ þ", name: "þurs", group: "Långkvist" },
  { tag: "ᚬ ą/o", name: "óss", group: "Långkvist" },
  { tag: "ᚱ r", name: "reið", group: "Långkvist" },
  { tag: "ᚴ k", name: "kaun", group: "Långkvist" },
  { tag: "ᚼ h", name: "hagall", group: "Långkvist" },
  { tag: "ᚾ n", name: "nauð", group: "Långkvist" },
  { tag: "ᛁ i", name: "íss", group: "Långkvist" },
  { tag: "ᛅ a", name: "ár", group: "Långkvist" },
  { tag: "ᛋ s", name: "sól", group: "Långkvist" },
  { tag: "ᛏ t", name: "týr", group: "Långkvist" },
  { tag: "ᛒ b", name: "bjarkan", group: "Långkvist" },
  { tag: "ᛘ m", name: "maðr", group: "Långkvist" },
  { tag: "ᛚ l", name: "lögr", group: "Långkvist" },
  { tag: "ᛦ R", name: "yr", group: "Långkvist" },
  { tag: "ᚽ h (kortkvist)", name: "hagall", group: "Kortkvist" },
  { tag: "ᚿ n (kortkvist)", name: "nauð", group: "Kortkvist" },
  { tag: "ᛆ a (kortkvist)", name: "ár", group: "Kortkvist" },
  { tag: "ᛌ s (kortkvist)", name: "sól", group: "Kortkvist" },
  { tag: "ᛐ t (kortkvist)", name: "týr", group: "Kortkvist" },
  { tag: "ᛙ m (kortkvist)", name: "maðr", group: "Kortkvist" },
  { tag: "ᛧ R (kortkvist)", name: "yr", group: "Kortkvist" },
  { tag: "ᛂ e (stungen)", name: "stungen i", group: "Stungna" },
  { tag: "ᚵ g (stungen)", name: "stungen k", group: "Stungna" },
  { tag: "ᛑ d (stungen)", name: "stungen t", group: "Stungna" },
  { tag: "ᛔ p", name: "stungen b", group: "Stungna" },
  { tag: "ᚤ y", name: "stungen u", group: "Stungna" },
  { tag: "Obestämd runa", name: "", group: "Övrigt" },
  { tag: "Skiljetecken", name: "", group: "Övrigt" },
  { tag: "Ornamentik", name: "", group: "Övrigt" },
  { tag: "Kors", name: "", group: "Övrigt" },
];

export const UNKNOWN_RUNE_TAG = "Obestämd runa";

// The tag for a transliterated rune (Rundata's conventions), e.g. "r" -> "ᚱ r", "e" -> "ᛂ e (stungen)"
export function tagForTranslit(t: string): string {
  const special: Record<string, string> = {
    e: "ᛂ e (stungen)", g: "ᚵ g (stungen)", d: "ᛑ d (stungen)", y: "ᚤ y", p: "ᛔ p", o: "ᚬ ą/o", "ą": "ᚬ ą/o",
  };
  if (special[t]) return special[t];
  const hit = RUNE_TAGS.find(r => r.group === "Långkvist" && r.tag.split(" ")[1] === t);
  return hit ? hit.tag : UNKNOWN_RUNE_TAG;
}

/** The letter a rune tag stands for in Rundata's transliteration ("ᛏ t" → "t", "ᚬ ą/o" → "o", "ᛐ t (kortkvist)" → "t"),
 * or null for tags that are not a rune (undetermined, dividers, ornament, cross). */
export function letterOfTag(tag: string): string | null {
  if (RUNE_TAGS.find(r => r.tag === tag)?.group === "Övrigt") return null;
  const m = tag.match(/^\S+\s+([^\s(]+)/u);
  if (!m || !/^[\p{L}/]+$/u.test(m[1])) return null;
  const parts = m[1].split("/");
  return parts[parts.length - 1] || null;
}
