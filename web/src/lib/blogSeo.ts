// SEO for the blog, derived from each post when the page is rendered: the description, keywords, pictures, structured
// data (schema.org BlogPosting and BreadcrumbList) and a check of the post before it is published. Nothing has to be
// filled in by hand – a new post gets it all when it is published.
import { API_URL } from "@/lib/api";
import { authorOf, isPublicPath, PUBLIC_SITE, SITE_NAME, SITE_URL } from "@/lib/site";
import type { BlogPost } from "@/components/BlogBody";

export const BLOG_TITLE = "Artiklar – mönster i runstenarna";
export const BLOG_DESCRIPTION = "Populärvetenskapliga artiklar om mönster i Sveriges runstenar: vad vi ser, vad det kan "
  + "betyda och hur det prövas – med statistiken redovisad.";
const BASE_KEYWORDS = ["runstenar", "runinskrifter", "runforskning", "runologi", "vikingatiden", "statistik",
  "Samnordisk runtextdatabas", "artiklar om runstenar"];
const SIGNUM = /\b(?:U|Sö|Ög|Vg|Sm|Öl|Gs|Hs|Hä|Vs|Nä|DR|N|G)\s\d{1,4}[A-Z]?\b/g;

// On the public website (GitHub Pages) every address ends with a slash (next.config.ts)
const SLASH = PUBLIC_SITE ? "/" : "";
export const ARTICLES_PATH = `/artiklar${SLASH}`;
export const postPath = (slug: string) => `/artiklar/${encodeURIComponent(slug)}${SLASH}`;
export const EN_ARTICLES_PATH = `/en/artiklar${SLASH}`;
export const enPostPath = (slug: string) => `/en/artiklar/${encodeURIComponent(slug)}${SLASH}`;
/** The article's page in the reader's language: the English edition for a reader who has chosen English, when the
 *  article has one (the list carries title_en for exactly those), otherwise the Swedish original. */
export const readerPath = (p: Pick<BlogPost, "slug" | "title_en">, lang: string) =>
  lang === "en" && p.title_en ? enPostPath(p.slug) : postPath(p.slug);
export const enPostUrl = (slug: string) => `${SITE_URL}${enPostPath(slug)}`;
// hreflang pairs; Swedish is the original and the default for everyone else
export const languageAlternates = (slug?: string) => ({
  sv: slug ? postPath(slug) : ARTICLES_PATH,
  en: slug ? enPostPath(slug) : EN_ARTICLES_PATH,
  "x-default": slug ? postPath(slug) : ARTICLES_PATH,
});
export const BLOG_TITLE_EN = "Articles – patterns in the runestones";
export const BLOG_DESCRIPTION_EN = ("Popular-science articles on patterns in Sweden\u0027s runestones: what we see, what "
  + "it may mean and how it can be tested. The figures come from Vitki\u0027s open analyses and are explained in the text.");
export const postUrl = (slug: string) => `${SITE_URL}${postPath(slug)}`;
/** The article's share picture (app/artiklar/[slug]/delningsbild.png). */
export const sharePath = (slug: string) => `/artiklar/${encodeURIComponent(slug)}/delningsbild.png`;
export const SHARE_SIZE = { width: 1200, height: 630 };

/** A picture's address as a search engine or another site can fetch it. */
export function absolute(src: string) {
  if (src.startsWith("/api/blog/figures/") && PUBLIC_SITE) return `${SITE_URL}${src.replace("/api/blog/figures/", "/figurer/")}`;
  if (src.startsWith("/api/")) return `${API_URL}${src}`;
  if (src.startsWith("/")) return `${SITE_URL}${src}`;
  return src;
}

/** The text without markup: for the word count and the description. */
export function plainText(md: string) {
  return md.split("\n")
    .filter(l => !/^(:::|!\[|[+]?[^|]+\|[^|]+(\|.*)?$|#\s|Källa:|Source:)/.test(l.trim()))
    .join(" ")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/[*_>#]/g, "").replace(/\s+/g, " ").trim();
}

/** A description of at most max characters: whole sentences while they fit, otherwise cut at a word. */
export function metaDescription(text: string, max = 158) {
  const t = plainText(text);
  if (t.length <= max) return t;
  let out = "";
  for (const sentence of t.match(/[^.!?]+[.!?]+(\s|$)/g) ?? []) {
    if ((out + sentence).trim().length > max) break;
    out += sentence;
  }
  if (out.trim().length >= 110) return out.trim();  // a lone short first sentence says too little: cut mid-sentence instead
  return t.slice(0, max - 1).replace(/\s+\S*$/, "").replace(/[,;:–-]$/, "") + "…";
}

export const signaIn = (md: string) => [...new Set(md.match(SIGNUM) ?? [])];

export function keywords(post: BlogPost) {
  return [...new Set([...BASE_KEYWORDS, ...signaIn(`${post.title} ${post.summary} ${post.body ?? ""}`).slice(0, 8)])];
}

/** The pictures in the post (photos and figures), with their alt texts and, for photos, the credit from the caption
 *  ("Foto: Berig, CC BY 3.0"), which has to follow the picture also when it is shown elsewhere. */
// The thumbnail widths Wikimedia Commons serves; other widths are refused
const COMMONS_WIDTHS = [120, 250, 330, 500, 960, 1280];

/** A smaller copy of a Wikimedia Commons picture, at the smallest standard width of at least `width`, for lists. */
export function thumbnail(src: string, want = 500) {
  const width = COMMONS_WIDTHS.find(w => w >= want) ?? 1280;
  const thumb = /^(https:\/\/(?:upload|thumb)\.wikimedia\.org\/wikipedia\/commons)\/thumb\/(.+)\/\d+px-([^/]+)$/.exec(src);
  if (thumb) return `${thumb[1]}/thumb/${thumb[2]}/${width}px-${thumb[3]}`;
  const full = /^(https:\/\/upload\.wikimedia\.org\/wikipedia\/commons)\/([0-9a-f]\/[0-9a-f]{2})\/([^/]+)$/.exec(src);
  if (full && !/\.svg$/i.test(full[3])) return `${full[1]}/thumb/${full[2]}/${full[3]}/${width}px-${full[3]}`;
  return src;
}

// A Commons picture's address, as an original (…/commons/a/ab/Name.jpg) or as a thumbnail (…/commons/thumb/a/ab/Name.jpg/960px-Name.jpg)
const COMMONS = /^https:\/\/(?:upload|thumb)\.wikimedia\.org\/wikipedia\/commons\/(?:thumb\/)?([0-9a-f]\/[0-9a-f]{2})\/([^/]+)(?:\/(\d+)px-[^/]+)?$/;
const COMMONS_BASE = "https://upload.wikimedia.org/wikipedia/commons";
const BITMAP = /\.(?:jpe?g|png|gif|webp)$/i;

/** The file name of a Commons picture (as in its address, with underscores), or null for other pictures. */
export function commonsFile(src: string): string | null {
  const m = COMMONS.exec(src);
  if (!m) return null;
  try { return decodeURIComponent(m[2]).replace(/ /g, "_"); } catch { return null; }
}

/** The pixel size of Commons originals, by file name (commonsFile). */
export type ImageSizes = Record<string, [number, number]>;

/**
 * A Commons picture about `want` pixels wide (at Commons' standard thumbnail width), never larger than its original:
 * Commons enlarges a thumbnail that is wider than the original, which only makes the file bigger. So a thumbnail wider
 * than that is made smaller, and an original is replaced by a thumbnail only when its width (`width`, from
 * commonsSizes) is known to be larger. Other pictures, SVG originals and anything already small enough are kept.
 */
export function commonsAt(src: string, want: number, width?: number | null): string {
  const m = COMMONS.exec(src);
  // Only photos and drawings whose thumbnails are named "960px-<name>" (not SVG, TIFF or PDF)
  if (!m || !BITMAP.test(m[2])) return src;
  const target = COMMONS_WIDTHS.find(w => w >= want) ?? 1280;
  const [, dir, name, px] = m;
  const thumb = `${COMMONS_BASE}/thumb/${dir}/${name}/${target}px-${name}`;
  // A thumbnail wider than wanted: the wanted width, or the original when that is narrower still
  if (px) return Number(px) <= target ? src : width && width <= target ? `${COMMONS_BASE}/${dir}/${name}` : thumb;
  return width && width > target ? thumb : src;
}

/** srcset for a Commons picture whose original width is known: the standard thumbnails clearly narrower than the
 *  original (a thumbnail almost as wide saves nothing), then the original itself when it is no wider than the largest.
 *  below: how much narrower than the original a thumbnail must be; 1 takes every narrower one, where the original is
 *  left out for its weight (an original wider than the largest width). */
export function commonsSrcSet(src: string, width?: number | null, widths = [500, 960, 1280], below = 0.8): string | undefined {
  const m = COMMONS.exec(src);
  if (!m || !width || !BITMAP.test(m[2])) return undefined;
  const [, dir, name] = m;
  const list = widths.filter(w => w < width * below).map(w => `${COMMONS_BASE}/thumb/${dir}/${name}/${w}px-${name} ${w}w`);
  if (width <= Math.max(...widths)) list.push(`${COMMONS_BASE}/${dir}/${name} ${width}w`);
  return list.join(", ");
}

/** The original of a Commons picture (for the enlarged view), or the address itself. */
export function commonsOriginal(src: string): string {
  const m = COMMONS.exec(src);
  return m ? `${COMMONS_BASE}/${m[1]}/${m[2]}` : src;
}

/**
 * The sizes of the Commons pictures among `srcs`, from the Commons API, when the page is rendered on the server (50
 * files per request, cached with the page's data). A picture the API does not answer for is left out, and is then
 * shown as before (commonsAt keeps an original whose width is not known).
 */
export async function commonsSizes(srcs: (string | null | undefined)[]): Promise<ImageSizes> {
  const files = [...new Set(srcs.map(s => (s ? commonsFile(s) : null)).filter((f): f is string => !!f))].sort();
  const out: ImageSizes = {};
  for (let i = 0; i < files.length; i += 50) {
    const batch = files.slice(i, i + 50);
    const url = "https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2&prop=imageinfo&iiprop=size&titles="
      + encodeURIComponent(batch.map(f => `File:${f.replace(/_/g, " ")}`).join("|"));
    try {
      const r = await fetch(url, { headers: { "User-Agent": `${SITE_NAME}/1.0 (${SITE_URL}; picture sizes for the articles)` },
                                   cache: "force-cache", signal: AbortSignal.timeout(8000) });
      if (!r.ok) continue;
      const data = await r.json() as { query?: { pages?: { title: string; imageinfo?: { width: number; height: number }[] }[] } };
      for (const page of data.query?.pages ?? []) {
        const info = page.imageinfo?.[0];
        if (!info?.width || !info?.height) continue;
        // "File:A b.jpg" → "A_b.jpg"; Commons capitalises only the first letter, as the address already does
        const key = page.title.replace(/^File:/, "").replace(/ /g, "_");
        const own = batch.find(f => f === key || f.charAt(0).toUpperCase() + f.slice(1) === key);
        if (own) out[own] = [info.width, info.height];
      }
    } catch {
      // Commons unreachable: the pictures are shown as they are
    }
  }
  return out;
}

/** A list card's photo about `want` pixels wide: no wider than the original when its size is known (withImageSizes),
 *  otherwise the standard thumbnail as before. */
export function cardImage(post: Pick<BlogPost, "image" | "image_width">, want: number): string {
  if (!post.image) return "";
  return post.image_width ? commonsAt(post.image, want, post.image_width) : thumbnail(post.image, want);
}

/** The list's posts with the size of their first photo (BlogPost.image_width/image_height), when Commons knows it. */
export async function withImageSizes(posts: BlogPost[]): Promise<BlogPost[]> {
  const sizes = await commonsSizes(posts.map(p => p.image));
  return posts.map(p => {
    const size = p.image ? sizes[commonsFile(p.image) ?? ""] : undefined;
    return size ? { ...p, image_width: size[0], image_height: size[1] } : p;
  });
}

export function pictures(md: string) {
  return [...md.matchAll(/^!\[([^\]]*)\]\(([^)\s]+)\)\n?(.*)$/gm)].map(m => {
    const credit = /(?:Foto|Photo): ([^,]+), \[?([^\](,]+)/.exec(m[3] ?? "");
    return { alt: m[1], src: absolute(m[2]), credit: credit ? `${credit[1].trim()}, ${credit[2].trim()}` : null };
  });
}

export const wordCount = (md: string) => plainText(md).split(" ").filter(Boolean).length;

/** The bullets of the closing box "Det viktigaste i korthet" / "The essentials in brief": the article's own summary of
 *  what it carries, which answer engines and search summaries can quote as a whole. */
export function keyPoints(md: string) {
  const m = /^:::box (?:Det viktigaste i korthet|The essentials in brief)\n([\s\S]*?)^:::/m.exec(md);
  return m ? m[1].split("\n").filter(l => l.startsWith("- ")).map(l => plainText(l.slice(2))) : [];
}

/** The bullets under "## Källor" / "## Sources", as plain text. */
export function citations(md: string) {
  const m = /^## (?:Källor(?: och data)?|Sources(?: and data)?)\n([\s\S]*?)(?=^## |$(?![\s\S]))/m.exec(md);
  return m ? m[1].split("\n").filter(l => l.startsWith("- ")).map(l => plainText(l.slice(2))).filter(c => !/^(Foton|Bilder|Photos|Images)[: ]/.test(c)) : [];
}

/** schema.org BlogPosting and BreadcrumbList for the post page (JSON-LD). */
export function articleJsonLd(post: BlogPost, lang: "sv" | "en" = "sv") {
  const en = lang === "en";
  const url = en ? enPostUrl(post.slug) : postUrl(post.slug);
  const body = (en ? post.body_en : post.body) ?? "";
  const published = post.publishedAt ?? undefined;
  return [
    {
      "@context": "https://schema.org",
      "@type": "BlogPosting",
      headline: ((en && post.title_en) || post.title).slice(0, 110),
      description: plainText((en ? post.summary_en : post.summary) || metaDescription(body)).slice(0, 500),
      ...(keyPoints(body).length ? { abstract: keyPoints(body).join(" ") } : {}),
      ...(citations(body).length ? { citation: citations(body) } : {}),
      isPartOf: { "@type": "Blog", "@id": `${SITE_URL}/artiklar/#blog`, name: SITE_NAME },
      url,
      mainEntityOfPage: { "@type": "WebPage", "@id": url },
      datePublished: published,
      dateModified: post.updatedAt ?? published,
      author: { "@type": "Person", ...(post.author === "Viktor Kvant" || !post.author ? { "@id": `${SITE_URL}/#founder` } : {}), name: post.author || "Viktor Kvant",
                ...(authorOf(post.author) ? { url: authorOf(post.author)!.url, sameAs: [authorOf(post.author)!.linkedin], jobTitle: authorOf(post.author)!.role } : {}) },
      publisher: { "@type": "Organization", "@id": `${SITE_URL}/#organization`, name: SITE_NAME, url: SITE_URL, logo: { "@type": "ImageObject", url: `${SITE_URL}/vitki_logo.png` } },
      image: [`${SITE_URL}${sharePath(post.slug)}`, ...pictures(body).map(p => absolute(p.src))].slice(0, 5),
      inLanguage: en ? "en" : "sv-SE",
      articleSection: en ? "Articles" : "Artiklar",
      keywords: keywords(post).join(", "),
      wordCount: wordCount(body),
      isAccessibleForFree: true,
      about: [{ "@type": "Thing", name: "Runstenar" }, { "@type": "Thing", name: "Runinskrifter" }],
      mentions: signaIn(body).slice(0, 12).map(s => ({ "@type": "Thing", name: `Runstenen ${s}` })),
      ...(post.title_en ? { alternativeHeadline: post.title_en } : {}),
    },
    {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement: [
        { "@type": "ListItem", position: 1, name: SITE_NAME, item: SITE_URL },
        { "@type": "ListItem", position: 2, name: en ? "Articles" : "Artiklar", item: `${SITE_URL}${en ? "/en" : ""}/artiklar` },
        { "@type": "ListItem", position: 3, name: (en && post.title_en) || post.title, item: url },
      ],
    },
  ];
}

/** schema.org Blog with the published posts, for the blog's front page. */
export function blogJsonLd(posts: BlogPost[]) {
  return {
    "@context": "https://schema.org",
    "@type": "Blog",
    name: BLOG_TITLE,
    description: BLOG_DESCRIPTION,
    url: `${SITE_URL}${ARTICLES_PATH}`,
    inLanguage: "sv-SE",
    publisher: { "@type": "Organization", name: SITE_NAME, url: SITE_URL, logo: { "@type": "ImageObject", url: `${SITE_URL}/vitki_logo.png` } },
    blogPost: posts.map(p => ({ "@type": "BlogPosting", headline: p.title, url: postUrl(p.slug), datePublished: p.publishedAt ?? undefined,
                                 description: metaDescription(p.summary || "") })),
  };
}

export interface SeoCheck { ok: boolean; text: string }

/** What a search engine will see, checked before publishing (Admin). */
/** Links in the article into the app, which the public website does not have (the start page and the articles only). */
export const appLinks = (post: Pick<BlogPost, "body" | "body_en">) =>
  [...`${post.body ?? ""}\n${post.body_en ?? ""}`.matchAll(/\]\((\/[^)\s]*)\)/g)].map(m => m[1]).filter(h => !isPublicPath(h));

export function seoChecks(post: Pick<BlogPost, "title" | "summary" | "slug" | "body" | "title_en" | "body_en">): SeoCheck[] {
  const body = post.body ?? "";
  const pics = pictures(body);
  const words = wordCount(body);
  const desc = plainText(post.summary || "");
  const topical = /runsten|runinskrift|runristare|vikingatid|rune/i.test(`${post.title} ${post.summary}`);
  return [
    { ok: post.title.length >= 25 && post.title.length <= 65, text: `Rubriken är ${post.title.length} tecken (bäst 25–65, annars kortas den i sökträffen).` },
    { ok: desc.length >= 70 && metaDescription(post.summary || "").length >= 70 && !metaDescription(post.summary || "").endsWith("…"),
      text: `Ingressen är ${desc.length} tecken; beskrivningen i sökträffen blir ${metaDescription(post.summary || "").length} tecken med hela meningar (bäst 70–160).` },
    { ok: topical, text: "Rubriken eller ingressen nämner runstenar, runinskrifter eller vikingatiden – orden folk söker på." },
    { ok: /^[a-z0-9-]{1,75}$/.test(post.slug), text: `Adressen /artiklar/${post.slug || "…"} är kort, med små bokstäver och bindestreck.` },
    { ok: (body.match(/^## /gm) ?? []).length >= 3, text: "Texten har minst tre mellanrubriker (##), så att den går att överblicka." },
    { ok: pics.length > 0 && pics.every(p => p.alt.trim().length >= 5), text: `${pics.length} bilder${pics.length ? ", alla med beskrivande alt-text" : " – lägg gärna till en"}.` },
    { ok: words >= 600, text: `Texten har ${words} ord (bäst minst 600 för en artikel).` },
    { ok: appLinks(post).length === 0, text: appLinks(post).length
        ? `Texten länkar in i appen, som inte finns på webbplatsen: ${appLinks(post).slice(0, 3).join(", ")}. Visa en bild ur R (Figurer) eller länka till GitHub i stället.`
        : "Texten länkar inte in i appen (den finns inte på webbplatsen) – kartor och kurvor visas som bilder." },
    { ok: /^## (Källor|Sources)/m.test(body), text: "Texten har ett avsnitt med källor." },
    { ok: !!(post.title_en && post.body_en), text: "Det finns en engelsk version, som når fler läsare." },
  ];
}
