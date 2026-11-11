// The article series: articles that belong together, recognised by the start of the Swedish title. The article library
// (components/ArticleLibrary.tsx) shows a series as soon as it has at least MIN_PARTS published parts, and can filter on
// it (?serie=…). A new series is added here.
import type { BlogPost } from "@/components/BlogBody";

export interface Series { key: string; sv: string; en: string; match: RegExp; about: string; aboutEn: string }

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
];
export const MIN_PARTS = 2;

export const seriesOf = (p: Pick<BlogPost, "title">): Series | null => SERIES.find(s => s.match.test(p.title)) ?? null;
