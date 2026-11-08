// The share picture of a research report in English (title_en, English labels): drawn by @/lib/shareImage, built ahead for every report.
import { reportSlugs } from "@/lib/articles";
import { shareImage } from "@/lib/shareImage";

export const revalidate = 3600;
export const generateStaticParams = reportSlugs;

export async function GET(_req: Request, { params }: { params: Promise<{ slug: string }> }) {
  return shareImage((await params).slug, "en");
}
