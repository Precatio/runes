/* eslint-disable @next/next/no-img-element -- ImageResponse draws <img> into the picture itself */
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { ImageResponse } from "next/og";
import { getPost, postSlugs } from "@/lib/articles";
import { postDate } from "@/components/BlogBody";
import { pictures } from "@/lib/blogSeo";

// The picture shown when an article is shared (Open Graph and Twitter/X): its title, date and first photo, made
// automatically for every article, at /artiklar/…/delningsbild.png – a file with its extension, which also the static
// public website serves as a picture
const size = { width: 1200, height: 630 };
export const revalidate = 3600;
export const generateStaticParams = postSlugs;

export async function GET(_req: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await getPost(decodeURIComponent(slug));
  const logo = `data:image/png;base64,${(await readFile(join(process.cwd(), "public", "vitki_logo.png"))).toString("base64")}`;
  const title = post?.title ?? "Artiklar";
  const pic = post ? pictures(post.body ?? "").find(p => /wikimedia\.org/.test(p.src)) : undefined;
  const photo = pic?.src;
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
            <img src={photo} alt="" width={440} height={630} style={{ objectFit: "cover", width: 440, height: 630 }} />
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
