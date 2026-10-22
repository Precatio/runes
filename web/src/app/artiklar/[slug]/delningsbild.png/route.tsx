/* eslint-disable @next/next/no-img-element -- ImageResponse draws <img> into the picture itself */
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { ImageResponse } from "next/og";
import { getPost, postSlugs } from "@/lib/articles";
import { postDate } from "@/components/BlogBody";
import { commonsAt, commonsFile, commonsSizes, pictures } from "@/lib/blogSeo";
import { SITE_NAME, SITE_URL } from "@/lib/site";

// The picture shown when an article is shared (Open Graph and Twitter/X): its title, date and first photo, made
// automatically for every article, at /artiklar/…/delningsbild.png – a file with its extension, which also the static
// public website serves as a picture
const size = { width: 1200, height: 630 };
export const revalidate = 3600;
export const generateStaticParams = postSlugs;

const PANEL = { width: 440, height: 630 };
const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

/**
 * The photo as a data: address, fetched here rather than by ImageResponse: a thumbnail just large enough to fill the
 * panel (never wider than the original), with a User-Agent as Commons asks, tried three times. Commons sometimes
 * answers with an error page instead of the picture (rate limits); then null, and the card is drawn without the photo
 * and without its credit, instead of with an empty panel.
 */
async function photoData(src: string): Promise<string | null> {
  const [w, h] = (await commonsSizes([src]))[commonsFile(src) ?? ""] ?? [];
  // object-fit: cover fills the panel's height too, so a wide photo needs more width than the panel
  const want = w && h ? Math.max(PANEL.width, Math.ceil((PANEL.height * w) / h)) : 500;
  const url = commonsAt(src, want, w);
  for (let attempt = 0; attempt < 3; attempt++) {
    if (attempt) await sleep(1000 * attempt);
    try {
      const r = await fetch(url, { headers: { "User-Agent": `${SITE_NAME}/1.0 (${SITE_URL}; share pictures for the articles)` },
                                   signal: AbortSignal.timeout(15000) });
      const type = (r.headers.get("content-type") ?? "").split(";")[0].trim();
      if (!r.ok || !/^image\/(jpeg|png|gif)$/.test(type)) continue;
      return `data:${type};base64,${Buffer.from(await r.arrayBuffer()).toString("base64")}`;
    } catch {
      // try again
    }
  }
  return null;
}

export async function GET(_req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await getPost(decodeURIComponent(slug));
  const logo = `data:image/png;base64,${(await readFile(join(process.cwd(), "public", "vitki_logo.png"))).toString("base64")}`;
  const title = post?.title ?? "Artiklar";
  const pic = post ? pictures(post.body ?? "").find(p => /wikimedia\.org/.test(p.src)) : undefined;
  const photo = pic ? await photoData(pic.src) : null;
  const big = title.length > 48 ? 54 : 66;
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", background: "#f6f4f1", color: "#0f172a" }}>
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", padding: "70px", width: photo ? 760 : 1200 }}>
          <div style={{ display: "flex", alignItems: "center", fontSize: 26, fontWeight: 700, color: "#b7410e", letterSpacing: 3 }}>
            <img src={logo} alt="" width={48} height={40} style={{ marginRight: 16, borderRadius: 8 }} />
            VITKI · ARTIKLAR
          </div>
          <div style={{ fontSize: big, fontWeight: 800, lineHeight: 1.08, marginTop: 28 }}>{title}</div>
          <div style={{ fontSize: 26, color: "#64748b", marginTop: 32 }}>
            {post ? `${postDate(post)}${post.author ? ` · ${post.author}` : ""} · vitkirunor.se` : "vitkirunor.se"}
          </div>
        </div>
        {photo && (
          <div style={{ display: "flex", width: 440, height: "100%", overflow: "hidden", position: "relative" }}>
            <img src={photo} alt="" width={PANEL.width} height={PANEL.height} style={{ objectFit: "cover", width: PANEL.width, height: PANEL.height }} />
            {pic?.credit && (
              <div style={{ position: "absolute", right: 0, bottom: 0, background: "rgba(15,23,42,0.6)", color: "#ffffff",
                            fontSize: 15, padding: "5px 10px" }}>{`Foto: ${pic.credit}`}</div>
            )}
          </div>
        )}
      </div>
    ),
    { ...size },
  );
}
