// The app's two tones for marks, pills and boxes below the hero of a page: rust for what is strong, confirmed or new,
// slate for what is neutral, weak or a reservation. No green, amber, blue or pink – the glyphs (✓ ✗ ● ○ !) carry the
// meaning without colour, and the rust is the same #b7410e / #9a350b as everywhere else (no purple, rust accent).
export const RUST = "#b7410e";
export const RUST_DARK = "#9a350b";

export const TONE = {
  /** Filled rust: the key verdict – statistically significant, confirmed, holds in every check. */
  fill: "bg-[#b7410e] border-[#b7410e] text-white",
  /** Rust tint: new, worth testing, strong evidence – noticeable but not shouting. */
  tint: "bg-[#b7410e]/5 text-[#9a350b] border-[#b7410e]/25",
  /** Rust outline on white: a lighter emphasis (moderate, probable, holds in most checks). */
  outline: "bg-white text-[#9a350b] border-[#b7410e]/40",
  /** Slate: neutral, already known, weak, not tested. */
  neutral: "bg-slate-50 text-slate-700 border-slate-200",
  /** Slate, a shade darker: a reservation or a method problem – read it, but it is not an alarm. */
  caution: "bg-slate-100 text-slate-800 border-slate-300",
} as const;

/** Text colour for a glyph or label that answers yes / no / not applicable. */
export const MARK = { yes: "text-[#b7410e]", no: "text-slate-500", none: "text-slate-400" } as const;

/** A small segment (ladder meter): holds / fails / not tested. */
export const SEGMENT = { yes: "bg-[#b7410e]", no: "bg-slate-400", none: "bg-slate-200" } as const;

/** The toggle buttons that filter a list: on = rust, off = white with rust text. */
export const toggle = (on: boolean) =>
  `px-3 py-1.5 rounded-xl border text-xs font-bold ${on ? TONE.fill : "bg-white border-slate-300 text-[#9a350b] hover:bg-[#b7410e]/5"}`;

/** A box for a hypothesis, a reservation or a note inside a card. */
export const NOTE_BOX = "rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm leading-relaxed text-slate-800";
export const NOTE_LABEL = "font-semibold text-[#9a350b]";
