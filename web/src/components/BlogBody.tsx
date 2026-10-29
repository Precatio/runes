import { Fragment, type ReactNode } from "react";
import { API_URL } from "@/lib/api";
import ZoomImage from "@/components/ZoomImage";
import { commonsAt, commonsFile, commonsOriginal, commonsSrcSet, type ImageSizes } from "@/lib/blogSeo";
import { isPublicPath, PUBLIC_SITE } from "@/lib/site";

// A blog post (GET /api/blog/posts, api/routers/blog.py). The English fields are optional; without them the Swedish
// text is shown also in English
export interface BlogPost {
  id: string;
  slug: string;
  title: string;
  summary: string;
  body?: string;
  title_en?: string;
  summary_en?: string;
  body_en?: string;
  month: string;
  author?: string;
  published?: boolean;
  publishedAt?: string | null;
  updatedAt?: string | null;
  // Page views on the public website (Swedish and English page together), exported with the article for "Mest lästa"
  views?: number;
  // The R pattern the post is about ("Förändring|bon"), set by a draft from a chosen topic
  topic?: string;
  // "Veckans artikel": first and large on the start page and first in the list, whatever its date
  featured?: boolean;
  // One type and some subjects from the fixed list in lib/labels.ts ("Forskning", "Ristare", …)
  labels?: string[];
  // The article's first photo (Wikimedia Commons), for the thumbnail in the list
  image?: string | null;
  image_alt?: string | null;
  // Its original's pixel size, when Commons gave it as the page was rendered (lib/blogSeo.ts withImageSizes)
  image_width?: number | null;
  image_height?: number | null;
}

/** The post in the chosen language: the English version when there is one. */
export function inLanguage(p: BlogPost, lang: string) {
  const en = lang === "en" && !!(p.title_en || p.body_en);
  return {
    en,
    title: (en && p.title_en) || p.title,
    summary: (en && p.summary_en) || p.summary,
    body: (en && p.body_en) || p.body || "",
  };
}

const MONTHS_SV = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober", "november", "december"];
const MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

/** "2026-10" → "oktober 2026" (or "October 2026"). */
export function monthLabel(month: string, lang = "sv") {
  const [y, m] = month.split("-").map(Number);
  if (!y || !m) return month;
  return `${(lang === "en" ? MONTHS_EN : MONTHS_SV)[m - 1]} ${y}`;
}

/** "2026-10-13T08:30:00Z" → "13 oktober 2026" (with the time: "13 oktober 2026 10:30"), in Swedish time on server and
 *  browser alike, so that the rendered date does not change when the page comes alive. */
export function dateLabel(iso: string | null | undefined, lang = "sv", withTime = false) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString(lang === "en" ? "en-GB" : "sv-SE", {
    day: "numeric", month: "long", year: "numeric", timeZone: "Europe/Stockholm",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  });
}

/** An article's date: when it was published, or its month for the older articles that have none. */
export const postDate = (p: Pick<BlogPost, "publishedAt" | "month">, lang = "sv") =>
  p.publishedAt ? dateLabel(p.publishedAt, lang) : monthLabel(p.month, lang);

// Links only to the web or to the public website's own pages (the start page and the articles), never javascript: or
// data:, and never into the app, which is not on the public website – such a link is shown as plain text
const safeHref = (href: string) => (/^https?:\/\//.test(href) ? href : isPublicPath(href) ? withSlash(href) : null);

// The public website is static with a trailing slash on every page (/artiklar/x/); a link without it gets a redirect,
// which search engines report as "page with redirect". Internal links get the slash there, before any ?query or #hash.
const withSlash = (href: string) => {
  if (!PUBLIC_SITE) return href;
  const m = href.match(/^([^?#]*)(.*)$/);
  const path = m?.[1] ?? href, rest = m?.[2] ?? "";
  return path.endsWith("/") || /\.[a-z0-9]+$/i.test(path) ? href : `${path}/${rest}`;
};

/** **bold**, *italic* and [text](url) inside a line. */
function inline(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  const re = /\*\*(.+?)\*\*|\*(.+?)\*|\[([^\]]+)\]\(([^)\s]+)\)/g;
  let last = 0, m: RegExpExecArray | null, i = 0;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index));
    if (m[1] !== undefined) out.push(<strong key={i++} className="font-semibold text-slate-900">{m[1]}</strong>);
    else if (m[2] !== undefined) out.push(<em key={i++}>{m[2]}</em>);
    else {
      const href = safeHref(m[4]);
      out.push(href
        ? <a key={i++} href={href} className="text-[#b7410e] underline underline-offset-2" {...(href.startsWith("http") ? { target: "_blank", rel: "noopener noreferrer" } : {})}>{m[3]}</a>
        : m[3]);
    }
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

// Pictures only from Wikimedia Commons (the stone photos the editor collects, with their licence), the blog's own copies
// of the R analyses' figures (served by the analysis engine, /api/blog/figures/) or the site itself. "/\\host/…" is
// refused like "//host/…": browsers read the backslash as a slash, which would lead to another site
const safeSrc = (src: string) => {
  if (/^\/api\/blog\/figures\/[0-9a-f]{16}\.png$/.test(src)) return PUBLIC_SITE ? src.replace("/api/blog/figures/", "/figurer/") : `${API_URL}${src}`;
  return /^(https:\/\/(upload|thumb)\.wikimedia\.org\/|\/(?![\/\\]|api\/))/.test(src) && !src.includes("\\") ? src : null;
};

/** Paragraphs, "## " and "### " headings, "- " lists, "> " quotes and pictures, separated by blank lines. */
function Blocks({ text, opening = false, sizes }: { text: string; opening?: boolean; sizes?: ImageSizes }) {
  const blocks = text.split(/\n\s*\n/).map(b => b.trim()).filter(Boolean);
  return (
    <>
      {blocks.map((b, i) => {
        // The article's opening quotation – an inscription or a quote in italics – set off as a quotation, indented
        const quote = /^\*([^*][^]*?)\*$/.exec(b);
        if (opening && i === 0 && quote && !quote[1].includes("*")) {
          return (
            <blockquote key={i} className="ml-4 sm:ml-8 border-l-4 border-[#b7410e] pl-5 sm:pl-6 py-1 font-serif text-xl italic leading-relaxed text-slate-800">
              {quote[1].split("\n").map((l, j) => <Fragment key={j}>{j > 0 && <br />}{inline(l)}</Fragment>)}
            </blockquote>
          );
        }
        if (b.startsWith("### ")) return <h3 key={i} className="pt-2 text-lg font-bold text-slate-900">{inline(b.slice(4))}</h3>;
        if (b.startsWith("## ")) return <h2 key={i} className="pt-4 text-2xl font-serif font-bold text-slate-900">{inline(b.slice(3))}</h2>;
        const lines = b.split("\n");
        const pic = /^!\[([^\]]*)\]\(([^)\s]+)\)$/.exec(lines[0]);
        if (pic) return <Picture key={i} alt={pic[1]} src={pic[2]} caption={lines.slice(1).join(" ")} sizes={sizes} />;
        if (lines.every(l => /^[-*] /.test(l))) {
          return <ul key={i} className="list-disc pl-6 space-y-1.5">{lines.map((l, j) => <li key={j}>{inline(l.slice(2))}</li>)}</ul>;
        }
        if (lines.every(l => /^\d+\. /.test(l))) {
          return <ol key={i} className="list-decimal pl-6 space-y-1.5">{lines.map((l, j) => <li key={j}>{inline(l.replace(/^\d+\. /, ""))}</li>)}</ol>;
        }
        if (lines.every(l => l.startsWith("> "))) {
          return <blockquote key={i} className="border-l-4 border-[#b7410e]/50 pl-4 text-slate-600 italic">{inline(lines.map(l => l.slice(2)).join(" "))}</blockquote>;
        }
        return <p key={i}>{lines.map((l, j) => <Fragment key={j}>{j > 0 && <br />}{inline(l)}</Fragment>)}</p>;
      })}
    </>
  );
}

// The picture's box: the text column (max-w-3xl less its padding) and at most 520 px high
const COLUMN = 720, MAX_HEIGHT = 520, GUTTER = 48;

// The copies the enlarged view chooses from: Commons' standard thumbnails from 960 px up (every one narrower than the
// original), and the original itself when it is no wider than the largest (a larger original is replaced by the 3840 px
// copy, which no screen draws wider)
const ZOOM_WIDTHS = [960, 1280, 1920, 3840];

/** ![alt](url) with the caption (photographer and licence) on the following lines. A Commons photo is shown as a
 *  thumbnail about as wide as the column, never wider than its original; the original (or, for a very large one, the
 *  largest copy the screen needs) opens when it is enlarged. The address in the text may already be a thumbnail (the
 *  website's export shortens the originals to 960 px copies), so the enlarged view goes back to the original. */
function Picture({ alt, src, caption, sizes }: { alt: string; src: string; caption: string; sizes?: ImageSizes }) {
  const ok = safeSrc(src);
  if (!ok) return null;
  const size = sizes?.[commonsFile(ok) ?? ""];
  const shown = commonsAt(ok, 960, size?.[0]);
  // How wide the picture is drawn: the column, or less for a tall picture that the height limit narrows
  const drawn = size ? Math.round(Math.min(COLUMN, (MAX_HEIGHT * size[0]) / size[1])) : 0;
  return (
    <figure className="mt-2 mb-9">
      <ZoomImage src={shown} zoomSrc={commonsOriginal(ok)} zoomSrcSet={commonsSrcSet(ok, size?.[0], ZOOM_WIDTHS, 1)} alt={alt} width={size?.[0]} height={size?.[1]} srcSet={commonsSrcSet(ok, size?.[0])}
        sizes={size ? `(min-width: ${drawn + GUTTER}px) ${drawn}px, calc(100vw - ${GUTTER}px)` : undefined}
        className="w-full max-h-[520px] object-contain rounded-xl bg-slate-100" />
      {caption && <figcaption className="mt-2.5 text-sm leading-snug text-slate-500">{inline(caption)}</figcaption>}
    </figure>
  );
}

/** ":::box Title" … ":::": a fact box (in short, how sure we are, the hypothesis). */
function Box({ title, text, sizes }: { title: string; text: string; sizes?: ImageSizes }) {
  return (
    <aside className="rounded-xl border border-[#b7410e]/20 bg-[#fbf3ee] px-5 py-4 space-y-3 text-[16px]">
      {title && <p className="text-xs font-bold uppercase tracking-wider text-[#9a350b]">{inline(title)}</p>}
      <Blocks text={text} sizes={sizes} />
    </aside>
  );
}

/**
 * ":::chart Title" … ":::": shares as horizontal bars, one row per line "label | percent | note"; a "+" before the label
 * marks the rows the text is about, "# " starts a group and a line "Källa: …" (or "Source: …") is the caption.
 */
function Chart({ title, text, en = false }: { title: string; text: string; en?: boolean }) {
  type Row = { label: string; value: number; note: string; hi: boolean };
  const groups: { name: string; rows: Row[] }[] = [];
  let caption = "";
  for (const raw of text.split("\n").map(l => l.trim()).filter(Boolean)) {
    if (/^(Källa|Source|Not|Note):/i.test(raw)) { caption = raw; continue; }
    if (raw.startsWith("# ")) { groups.push({ name: raw.slice(2), rows: [] }); continue; }
    const [label, value, note = ""] = raw.split("|").map(x => x.trim());
    const v = Number((value || "").replace(",", ".").replace(/[^\d.]/g, ""));
    if (!label || !Number.isFinite(v)) continue;
    if (!groups.length) groups.push({ name: "", rows: [] });
    const hi = label.startsWith("+");
    groups[groups.length - 1].rows.push({ label: hi ? label.slice(1).trim() : label, value: v, note, hi });
  }
  const max = Math.max(10, ...groups.flatMap(g => g.rows.map(r => r.value)));
  const top = Math.ceil(max / 10) * 10;
  const pct = (v: number) => `${en ? String(Math.round(v * 10) / 10) : String(Math.round(v * 10) / 10).replace(".", ",")} %`;
  return (
    <figure className="mt-2 mb-7 rounded-xl border border-slate-900/10 bg-white px-5 py-4">
      {title && <figcaption className="text-[15px] font-semibold text-slate-900">{inline(title)}</figcaption>}
      <div className="mt-3 space-y-4">
        {groups.map((g, gi) => (
          <div key={gi}>
            {g.name && <p className="mb-1.5 text-sm font-semibold text-slate-700">{inline(g.name)}</p>}
            <div className="space-y-2">
              {g.rows.map((r, ri) => (
                <div key={ri} className="grid grid-cols-1 sm:grid-cols-[minmax(0,15rem)_1fr] items-center gap-x-3 gap-y-1"
                  title={`${r.label}: ${pct(r.value)}${r.note ? ` (${r.note})` : ""}`}>
                  <span className="text-sm leading-tight text-slate-700">{inline(r.label)}</span>
                  <span className="flex items-center gap-2">
                    <span className="relative h-3 flex-1 rounded-full bg-slate-100">
                      <span className="absolute inset-y-0 left-0 rounded-full" style={{ width: `${(r.value / top) * 100}%`, background: r.hi ? "#b7410e" : "#94a3b8" }} />
                    </span>
                    <span className="w-28 shrink-0 text-sm tabular-nums text-slate-900">
                      <span className="font-semibold">{pct(r.value)}</span>
                      {r.note && <span className="block text-xs text-slate-500">{r.note}</span>}
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <p className="mt-3 text-xs text-slate-500">{en ? `The scale runs from 0 to ${top} %.` : `Skalan går från 0 till ${top} %.`}{caption ? " " : ""}{caption && inline(caption)}</p>
    </figure>
  );
}

/** The post body: the blocks of Blocks, with ":::box" and ":::chart" sections. sizes: the Commons photos' sizes
 *  (lib/blogSeo.ts commonsSizes), when the page knows them; lang: the text's language (the charts' decimal sign and
 *  scale note). */
export default function BlogBody({ text, sizes, lang = "sv" }: { text: string; sizes?: ImageSizes; lang?: "sv" | "en" }) {
  const parts: ReactNode[] = [];
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  let buf: string[] = [];
  const flush = () => {
    if (buf.join("").trim()) parts.push(<Blocks key={parts.length} text={buf.join("\n")} opening={parts.length === 0} sizes={sizes} />);
    buf = [];
  };
  for (let i = 0; i < lines.length; i++) {
    const open = /^:::(box|chart)\s*(.*)$/.exec(lines[i].trim());
    if (!open) { buf.push(lines[i]); continue; }
    const end = lines.findIndex((l, j) => j > i && l.trim() === ":::");
    if (end < 0) { buf.push(lines[i]); continue; }
    flush();
    const inner = lines.slice(i + 1, end).join("\n");
    parts.push(open[1] === "box"
      ? <Box key={parts.length} title={open[2]} text={inner} sizes={sizes} />
      : <Chart key={parts.length} title={open[2]} text={inner} en={lang === "en"} />);
    i = end;
  }
  flush();
  return <div className="space-y-5 text-[17px] leading-relaxed text-slate-700">{parts}</div>;
}
