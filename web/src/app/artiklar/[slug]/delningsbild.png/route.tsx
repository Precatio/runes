// The share picture of an article: drawn by @/lib/shareImage, built ahead for every article.
import { postSlugs } from "@/lib/articles";
import { shareImage } from "@/lib/shareImage";

export const revalidate = 3600;
export const generateStaticParams = postSlugs;

export async function GET(_req: Request, { params }: { params: Promise<{ slug: string }> }) {
  return shareImage((await params).slug, "sv");
}
