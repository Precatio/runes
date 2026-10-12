import { Fragment, type ReactNode } from "react";

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

// Links only to the web or within the site, never javascript: or data:
const safeHref = (href: string) => (/^(https?:\/\/|\/)/.test(href) ? href : null);

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

/** The post body: "## " headings, "- " lists and paragraphs separated by blank lines. */
export default function BlogBody({ text }: { text: string }) {
  const blocks = text.replace(/\r\n/g, "\n").split(/\n\s*\n/).map(b => b.trim()).filter(Boolean);
  return (
    <div className="space-y-5 text-[17px] leading-relaxed text-slate-700">
      {blocks.map((b, i) => {
        if (b.startsWith("### ")) return <h3 key={i} className="pt-2 text-lg font-bold text-slate-900">{inline(b.slice(4))}</h3>;
        if (b.startsWith("## ")) return <h2 key={i} className="pt-4 text-2xl font-serif font-bold text-slate-900">{inline(b.slice(3))}</h2>;
        const lines = b.split("\n");
        if (lines.every(l => /^[-*] /.test(l))) {
          return <ul key={i} className="list-disc pl-6 space-y-1.5">{lines.map((l, j) => <li key={j}>{inline(l.slice(2))}</li>)}</ul>;
        }
        if (lines.every(l => l.startsWith("> "))) {
          return <blockquote key={i} className="border-l-4 border-[#b7410e]/50 pl-4 text-slate-600 italic">{inline(lines.map(l => l.slice(2)).join(" "))}</blockquote>;
        }
        return <p key={i}>{lines.map((l, j) => <Fragment key={j}>{j > 0 && <br />}{inline(l)}</Fragment>)}</p>;
      })}
    </div>
  );
}
