"use client";
/* eslint-disable @next/next/no-img-element -- the public site is a static export without image optimisation */

import Link from "next/link";
import { useEffect, useRef } from "react";
import { inLanguage, postDate, type BlogPost } from "@/components/BlogBody";
import { inOrder, type Order } from "@/lib/featured";
import { useLanguage } from "@/components/LanguageContext";
import { cardImage, commonsSrcSet, readerPath } from "@/lib/blogSeo";
import LabelChips from "@/components/LabelChips";

// The article's first photo, or a rune on the page colour when it has none. The first card is in the first view, so its
// photo is fetched at once (eager), the others when they come near. big: the article of the week's wide card
function Picture({ post, big, className, eager = false }: { post: BlogPost; big: boolean; className: string; eager?: boolean }) {
  if (!post.image) {
    return (
      <div className={`${className} flex items-center justify-center bg-[#f3ede4]`} aria-hidden="true">
        <span className="text-6xl text-[#b7410e]/30 select-none">ᚱ</span>
      </div>
    );
  }
  return (
    <div className={`${className} overflow-hidden bg-slate-200`}>
      <CardPhoto post={post} image={post.image} big={big} eager={eager} />
    </div>
  );
}

// The standard Commons widths a card chooses from. A small card stops at 960 px, and the article of the week's card at
// 1280 px; an original is offered only when it is no wider than that (a wide original can weigh several MB), and every
// thumbnail narrower than the original is offered, so that an original just wider than the limit still has a large copy
const SMALL_WIDTHS = [330, 500, 960], BIG_WIDTHS = [500, 960, 1280];

// The sharpness a card aims for: at most 1.5 device pixels per CSS pixel (a phone at DPR 2 or 3 gets a copy for 1.5,
// which looks the same on a card at a fraction of the weight), and a copy up to a tenth narrower than that still counts
const MAX_DENSITY = 1.5, ENOUGH = 1.1;

/** The width of the copy an address in the srcset is (a thumbnail's NNNpx- prefix), or the original's. */
function copyWidth(url: string, original: number): number {
  const m = /\/(\d+)px-[^/]*$/.exec(url);
  return m ? Number(m[1]) : original;
}

function CardPhoto({ post, image, big, eager }: { post: BlogPost; image: string; big: boolean; eager: boolean }) {
  const ref = useRef<HTMLImageElement>(null);
  const { image_width: w, image_height: h } = post;
  // The photo covers its box (object-cover), so a landscape photo in a tall box is drawn wider than the box: as wide as
  // the box's height times its aspect ratio. A small card's box is as tall as its text, which differs from card to card
  // (287–398 px measured), so once the page has come alive the box is measured and the card picks its copy itself: the
  // smallest that is sharp enough on this screen (MAX_DENSITY, ENOUGH), told to the browser through sizes (the copy's
  // width over the screen's density, so that the browser takes exactly that copy). A copy the browser has already
  // started on is kept whenever it is sharp enough, so that a box that grows a little (a title in English, a resize)
  // never fetches the same photo twice; only a box that needs a clearly larger copy gets one
  useEffect(() => {
    const img = ref.current;
    if (!img || !w || !h || !img.srcset) return;
    const copies = img.srcset.split(/,\s+/).map(c => copyWidth(c.trim().split(/\s+/)[0], w)).sort((a, b) => a - b);
    if (!copies.length) return;
    const fit = () => {
      if (!img.clientWidth || !img.clientHeight) return;
      const dpr = window.devicePixelRatio || 1;
      const want = Math.max(img.clientWidth, (img.clientHeight * w) / h) * Math.min(dpr, MAX_DENSITY);
      if (img.currentSrc && copyWidth(img.currentSrc, w) * ENOUGH >= want) return;
      // The first card's photo was already fetched from the server-rendered page, with the sizes it was rendered with
      // (cardSizes): until the browser has picked a copy for this element it keeps those, so that it takes the copy it
      // already has instead of fetching another
      if (eager && !img.currentSrc) return;
      const pick = copies.find(c => c * ENOUGH >= want) ?? copies[copies.length - 1];
      // rounded down, so that the chosen copy's density is never a hair short of the screen's (500 px at 166.67 px
      // would be 2.9999 at DPR 3, and the browser would take the next larger copy)
      const sizes = `${Math.floor((pick / dpr) * 100) / 100}px`;
      if (img.sizes !== sizes) img.sizes = sizes;
    };
    fit();
    const watch = new ResizeObserver(fit);
    watch.observe(img);
    return () => watch.disconnect();
  }, [w, h, eager]);
  return (
    <img ref={ref} src={cardImage(post, big ? 960 : 500)} srcSet={commonsSrcSet(image, w, big ? BIG_WIDTHS : SMALL_WIDTHS, 1)}
      sizes={w ? cardSizes(big, w, h) : undefined} alt={post.image_alt || post.title}
      loading={eager ? "eager" : "lazy"} fetchPriority={eager ? "high" : undefined} decoding="async"
      className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />
  );
}

// How wide a card draws its photo, before the page has come alive (CardPhoto measures it then). Below 640 px every
// card's box is the column (the window less 48 px) at 16:9, so only a photo wider than 16:9 is drawn wider than the
// box; from 640 px a small card's box is 224 px wide and typically about 330 px tall, and the large card's box is the
// column (at most 720 px) at 16:9.
const CARD_HEIGHT = 330;
function cardSizes(big: boolean, width: number, height?: number | null): string {
  const ratio = height ? width / height : 1;
  const wide = Math.max(1, (ratio * 9) / 16);
  const column = wide > 1 ? `calc((100vw - 48px) * ${Math.ceil(wide * 100) / 100})` : "calc(100vw - 48px)";
  if (big) return `(min-width: 768px) ${Math.ceil(720 * wide)}px, ${column}`;
  return `(min-width: 640px) ${Math.max(224, Math.ceil(CARD_HEIGHT * ratio))}px, ${column}`;
}

// The published posts: the article of the week first and large, then the others newest first, each a card that is
// a link as a whole; rendered on the server in Swedish and shown in English when chosen
export default function BlogList({ posts, failed, order = "senaste" }: { posts: BlogPost[]; failed: boolean; order?: Order }) {
  const { lang } = useLanguage();
  if (!posts.length) {
    return <p className="text-slate-500">{failed ? "Artiklarna kunde inte hämtas just nu." : "Inga artiklar ännu. Den första kommer snart."}</p>;
  }
  const read = lang === "en" ? "Read the article →" : "Läs artikeln →";
  return (
    <>
      {inOrder(posts, order).map((p, i) => {
        const v = inLanguage(p, lang);
        const big = i === 0 && p.featured && order === "senaste";
        const meta = (
          <div className="text-sm text-slate-500">
            {p.featured && (
              <span className="mr-2 text-xs font-bold uppercase tracking-wider text-[#b7410e]">
                {lang === "en" ? "Article of the week" : "Veckans artikel"}
              </span>
            )}
            <time dateTime={p.publishedAt ?? p.month}>{postDate(p, lang)}</time>{p.author ? ` · ${p.author}` : ""}
          </div>
        );
        const chips = (
          <div className="mt-3">
            <LabelChips labels={p.labels} lang={lang} />
          </div>
        );
        return (
          <article key={p.id}>
            <Link href={readerPath(p, lang)} prefetch={false}
              className={`group block rounded-2xl border border-slate-200 bg-white/70 overflow-hidden transition hover:-translate-y-0.5 hover:border-[#b7410e]/50 hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#b7410e] ${big ? "" : "sm:flex"}`}>
              <Picture post={p} big={!!big} eager={i === 0}
                className={big ? "aspect-[16/9] w-full" : "aspect-[16/9] w-full sm:aspect-auto sm:w-56 sm:min-h-[11rem] shrink-0"} />
              <div className="p-5 sm:p-6 flex flex-col">
                {meta}
                <h2 className={`mt-1 font-serif font-bold leading-snug group-hover:text-[#b7410e] ${big ? "text-3xl" : "text-2xl"}`} translate="no">
                  {v.title}
                </h2>
                <p className="mt-2 text-slate-600 leading-relaxed line-clamp-4" translate="no">{v.summary}</p>
                {chips}
                <span className="mt-3 text-sm font-bold text-[#b7410e] group-hover:underline">{read}</span>
              </div>
            </Link>
          </article>
        );
      })}
    </>
  );
}
