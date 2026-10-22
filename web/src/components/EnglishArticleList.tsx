"use client";

import Link from "next/link";
import { postDate, type BlogPost } from "@/components/BlogBody";
import LabelChips from "@/components/LabelChips";
import LabelFilter, { useLabelFromAddress, withLabel } from "@/components/LabelFilter";
import SortToggle, { useOrderFromAddress } from "@/components/SortToggle";
import { inOrder } from "@/lib/featured";
import { enPostPath, metaDescription } from "@/lib/blogSeo";

// The English list of articles with the label filter (the Swedish list is BlogList inside ArticleSearch)
export default function EnglishArticleList({ posts }: { posts: BlogPost[] }) {
  const [label, setLabel] = useLabelFromAddress();
  const [order, setOrder] = useOrderFromAddress();
  const shown = inOrder(withLabel(posts, label), order);
  return (
    <>
      <div className="mt-10"><LabelFilter posts={posts} lang="en" value={label} onChange={setLabel} /></div>
      <SortToggle posts={posts} lang="en" value={order} onChange={setOrder} className="mt-5" />
      {label && shown.length === 0 && <p className="mt-8 text-slate-500">No article in English carries that label yet.</p>}
      <ul className="mt-10 space-y-10">
        {shown.map(p => (
          <li key={p.slug} className="border-t border-slate-200 pt-8">
            <p className="text-sm text-slate-500">{postDate(p, "en")}{p.author && <> · {p.author}</>}</p>
            <h2 className="mt-1.5 text-2xl font-serif font-bold text-slate-900">
              <Link href={enPostPath(p.slug)} prefetch={false} className="hover:text-[#b7410e]">{p.title_en}</Link>
            </h2>
            {p.summary_en && <p className="mt-2 text-slate-600 leading-relaxed">{metaDescription(p.summary_en, 220)}</p>}
            <LabelChips labels={p.labels} lang="en" linked className="mt-3" />
            <Link href={enPostPath(p.slug)} prefetch={false} className="inline-block mt-3 text-sm font-bold text-[#b7410e] hover:underline">
              Read the article →
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
