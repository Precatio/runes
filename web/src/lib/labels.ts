// The labels on the articles: one TYPE per article (what kind of text) and one or more SUBJECTS (what it is about).
// The same fixed list stands in src/blog_labels.py, which validates what Admin saves; tests/test_blog_labels.py
// compares the two. The Swedish name is the key stored on the article; the English name is shown on the English pages.
export const TYPES: [string, string][] = [
  ["Forskning", "Research"],
  ["Metod", "Method"],
  ["Så gör du", "How to"],
  ["Pågående arbete", "Work in progress"],
  ["Personligt", "Personal"],
];
export const SUBJECTS: [string, string][] = [
  ["Ristare", "Carvers"],
  ["Språk och stavning", "Language and spelling"],
  ["Formler och syfte", "Formulas and purpose"],
  ["Tro och magi", "Belief and magic"],
  ["Kvinnor och barn", "Women and children"],
  ["Norden", "The Nordic countries"],
  ["Datering och stil", "Dating and style"],
  ["Geografi", "Geography"],
  ["Kryptologi", "Cryptology"],
  ["Tolkning", "Interpretation"],
  ["Sannolikhetsmodellen", "The probability model"],
  ["Huggspår och 3D", "Grooves and 3D"],
  ["Eddan", "The Edda"],
];
export const MAX_LABELS = 5;

const ENGLISH = new Map([...TYPES, ...SUBJECTS]);
const TYPE_SET = new Set(TYPES.map(([sv]) => sv));

export const labelName = (label: string, lang: string) => (lang === "en" ? ENGLISH.get(label) ?? label : label);
export const isType = (label: string) => TYPE_SET.has(label);
/** The article's type label, if it has one. */
export const typeOf = (labels: string[] | undefined) => (labels ?? []).find(isType) ?? null;
/** The address of the list filtered on a label. */
export const labelPath = (label: string, lang: string) =>
  `${lang === "en" ? "/en/artiklar/" : "/artiklar/"}?etikett=${encodeURIComponent(label)}`;
