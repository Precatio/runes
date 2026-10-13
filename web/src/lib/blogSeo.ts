// SEO for the blog, derived from each post when the page is rendered: the description, keywords, pictures, structured
// data (schema.org BlogPosting and BreadcrumbList) and a check of the post before it is published. Nothing has to be
// filled in by hand – a new post gets it all when it is published.
import { API_URL } from "@/lib/api";
import { authorOf, isPublicPath, SITE_NAME, SITE_URL } from "@/lib/site";
import type { BlogPost } from "@/components/BlogBody";

export const BLOG_TITLE = "Artiklar – mönster i runstenarna";
export const BLOG_DESCRIPTION = "Artiklar om de mest intressanta mönstren i de svenska vikingatida runstenarna: vad vi "
  + "ser, vad det kan betyda och hur det kan prövas – populärvetenskapligt och med statistiken redovisad.";
const BASE_KEYWORDS = ["runstenar", "runinskrifter", "runforskning", "runologi", "vikingatiden", "statistik",
  "Samnordisk runtextdatabas", "artiklar om runstenar"];
const SIGNUM = /\b(?:U|Sö|Ög|Vg|Sm|Öl|Gs|Hs|Hä|Vs|Nä|DR|N|G)\s\d{1,4}[A-Z]?\b/g;

export const postPath = (slug: string) => `/artiklar/${encodeURIComponent(slug)}`;
export const postUrl = (slug: string) => `${SITE_URL}${postPath(slug)}`;

/** A picture's address as a search engine or another site can fetch it. */
export function absolute(src: string) {
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
  if (out.trim().length >= 70) return out.trim();
  return t.slice(0, max - 1).replace(/\s+\S*$/, "").replace(/[,;:–-]$/, "") + "…";
}

export const signaIn = (md: string) => [...new Set(md.match(SIGNUM) ?? [])];

export function keywords(post: BlogPost) {
  return [...new Set([...BASE_KEYWORDS, ...signaIn(`${post.title} ${post.summary} ${post.body ?? ""}`).slice(0, 8)])];
}

/** The pictures in the post (photos and figures), with their alt texts and, for photos, the credit from the caption
 *  ("Foto: Berig, CC BY 3.0"), which has to follow the picture also when it is shown elsewhere. */
export function pictures(md: string) {
  return [...md.matchAll(/^!\[([^\]]*)\]\(([^)\s]+)\)\n?(.*)$/gm)].map(m => {
    const credit = /(?:Foto|Photo): ([^,]+), \[?([^\](,]+)/.exec(m[3] ?? "");
    return { alt: m[1], src: absolute(m[2]), credit: credit ? `${credit[1].trim()}, ${credit[2].trim()}` : null };
  });
}

export const wordCount = (md: string) => plainText(md).split(" ").filter(Boolean).length;

/** schema.org BlogPosting and BreadcrumbList for the post page (JSON-LD). */
export function articleJsonLd(post: BlogPost) {
  const url = postUrl(post.slug);
  const body = post.body ?? "";
  const published = post.publishedAt ?? undefined;
  return [
    {
      "@context": "https://schema.org",
      "@type": "BlogPosting",
      headline: post.title.slice(0, 110),
      description: metaDescription(post.summary || body),
      url,
      mainEntityOfPage: { "@type": "WebPage", "@id": url },
      datePublished: published,
      dateModified: post.updatedAt ?? published,
      author: { "@type": "Person", name: post.author || "Viktor Kvant",
                ...(authorOf(post.author) ? { url: authorOf(post.author)!.url, sameAs: [authorOf(post.author)!.url], jobTitle: authorOf(post.author)!.role } : {}) },
      publisher: { "@type": "Organization", name: SITE_NAME, url: SITE_URL, logo: { "@type": "ImageObject", url: `${SITE_URL}/vitki_logo.png` } },
      image: [`${url}/opengraph-image`, ...pictures(body).map(p => p.src)].slice(0, 5),
      inLanguage: "sv-SE",
      articleSection: "Artiklar",
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
        { "@type": "ListItem", position: 2, name: "Artiklar", item: `${SITE_URL}/artiklar` },
        { "@type": "ListItem", position: 3, name: post.title, item: url },
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
    url: `${SITE_URL}/artiklar`,
    inLanguage: "sv-SE",
    publisher: { "@type": "Organization", name: SITE_NAME, url: SITE_URL },
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
