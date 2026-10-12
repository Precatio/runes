import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { ImageResponse } from "next/og";
import type { BlogPost } from "@/components/BlogBody";
import { API_URL } from "@/lib/api";
import { monthLabel } from "@/components/BlogBody";
import { pictures } from "@/lib/blogSeo";

// The picture shown when a post is shared (Open Graph and Twitter/X): its title, month and first photo, made
// automatically for every post
export const alt = "Månadens fynd – Vitki";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const revalidate = 3600;

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  let post: BlogPost | null = null;
  try {
    const r = await fetch(`${API_URL}/api/blog/posts/${encodeURIComponent(decodeURIComponent(slug))}`, { next: { revalidate: 3600, tags: ["blog"] } });
    post = r.ok ? (await r.json()).post : null;
  } catch { /* the picture without the post */ }
  const logo = `data:image/png;base64,${(await readFile(join(process.cwd(), "public", "vitki_logo.png"))).toString("base64")}`;
  const title = post?.title ?? "Månadens fynd";
  const pic = post ? pictures(post.body ?? "").find(p => /wikimedia\.org/.test(p.src)) : undefined;
  const photo = pic?.src;
  const big = title.length > 48 ? 54 : 66;
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", background: "#f6f4f1", color: "#0f172a" }}>
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", padding: "70px", width: photo ? 760 : 1200 }}>
          <div style={{ display: "flex", alignItems: "center", fontSize: 26, fontWeight: 700, color: "#b7410e", letterSpacing: 3 }}>
            <img src={logo} alt="" width={48} height={40} style={{ marginRight: 16, borderRadius: 8 }} />
            VITKI · MÅNADENS FYND
          </div>
          <div style={{ fontSize: big, fontWeight: 800, lineHeight: 1.08, marginTop: 28 }}>{title}</div>
          <div style={{ fontSize: 26, color: "#64748b", marginTop: 32 }}>
            {post ? `${monthLabel(post.month)}${post.author ? ` · ${post.author}` : ""} · vitkirunor.se` : "vitkirunor.se"}
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
