// The article series: articles that belong together, recognised by the start of the Swedish title (match) or listed by
// address (slugs) when the titles do not share a beginning. The article library (components/ArticleLibrary.tsx) shows
// every series with at least MIN_PARTS published parts – in the panel, as a strip above the articles, and on each card
// ("del 2") – and can filter on it (?serie=…). An article in a series gets the series box (components/SeriesNav.tsx):
// which part it is, all the published parts in reading order, and the next one. A new series is added here.
import type { BlogPost } from "@/components/BlogBody";

export interface Series {
  key: string; sv: string; en: string; about: string; aboutEn: string;
  match?: RegExp;      // the start of the Swedish title
  slugs?: string[];    // or the articles' addresses, in any order (the parts are ordered by publication date)
}

export const SERIES: Series[] = [
  { key: "de-gamla-landen", sv: "De gamla landen", en: "The old lands", match: /^De gamla landen:/,
    about: "Vikingatidens land och bygder, som de kan ha sett ut och levt.",
    aboutEn: "The lands and districts of the Viking Age, as they may have looked and lived." },
  { key: "tyde-den-som-kan", sv: "Tyde den som kan", en: "Read it who can", match: /^Tyde den som kan/,
    about: "De olästa runinskrifterna, prövade med kryptologins metoder.",
    aboutEn: "The unread runic inscriptions, tested with the methods of cryptology." },
  { key: "hundra-ar-av-runfragor", sv: "Hundra år av runfrågor", en: "A hundred years of runic questions", match: /^Hundra år av runfrågor/,
    about: "Vad Fornvännen och Futhark har frågat om runorna och runstenarna, årtionde för årtionde sedan 1906.",
    aboutEn: "What Fornvännen and Futhark have asked about runes and runestones, decade by decade since 1906." },
  { key: "brittiska-oarna", sv: "Runskrifterna på de brittiska öarna", en: "The runic inscriptions of the British Isles",
    slugs: ["vad-berattar-runskrifterna-pa-de-brittiska-oarna", "de-namnde-aldrig-hemmet"],
    about: "Vad runorna i England, Skottland, Irland och på Isle of Man berättar om dem som stannade västerut.",
    aboutEn: "What the runes in England, Scotland, Ireland and on the Isle of Man tell about those who stayed in the west." },
  { key: "vikingarnas-varld", sv: "Vikingarnas värld", en: "The Vikings' world",
    slugs: ["vikingarnas-varld", "osterled-eller-bara-ingvars"],
    about: "Vilka platser utanför Norden runstenarna och sagorna nämner – och hur mycket av österleden som var ett enda tåg.",
    aboutEn: "Which places beyond the North the runestones and the sagas name – and how much of the eastern route was one expedition." },
  { key: "nordiska-vasen", sv: "Fornnordiska väsen", en: "Old Norse beings", match: /^Fornnordiska väsen – /,
    slugs: ["var-bodde-trollen", "var-tog-alverna-vagen", "jattekvinnans-ugn", "var-sjatte-runsten-bar-en-bjorn", "draken-var-ett-skepp", "valkyriorna-gots-i-birka", "vargarna-i-gunnars-drom", "de-doda-som-kom-hem"],
    about: "Jättar, troll, alver, dvärgar och de andra väsendena i den fornnordiska litteraturen – räknade och lästa.",
    aboutEn: "Giants, trolls, elves, dwarves and the other beings of Old Norse literature – counted and read." },
];
export const MIN_PARTS = 1;

type Member = Pick<BlogPost, "title" | "slug">;
export const belongs = (s: Series, p: Member) => !!(s.slugs?.includes(p.slug) || s.match?.test(p.title));
export const seriesOf = (p: Member): Series | null => SERIES.find(s => belongs(s, p)) ?? null;

const dateOf = (p: Pick<BlogPost, "publishedAt" | "month">) => p.publishedAt ?? p.month ?? "";
/** The published parts of a series, in reading order (oldest first). */
export const partsOf = <T extends BlogPost>(posts: T[], key: string): T[] =>
  posts.filter(p => seriesOf(p)?.key === key).sort((a, b) => dateOf(a).localeCompare(dateOf(b)));
