// The share picture of a research report, drawn exactly as an article's (app/artiklar/[slug]/delningsbild.png): the
// title, the date and the first photo. Built ahead for every report.
import { reportSlugs } from "@/lib/articles";

export { GET } from "@/app/artiklar/[slug]/delningsbild.png/route";
export const revalidate = 3600;
export const generateStaticParams = reportSlugs;
