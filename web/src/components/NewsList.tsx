import { NEWS_STATUS, newsDate, type NewsItem } from "@/lib/news";

// The news notices (lib/news.ts): date, whether it is in the app or under way, a title and a few sentences
export default function NewsList({ items, compact = false }: { items: NewsItem[]; compact?: boolean }) {
  return (
    <ul className={compact ? "grid grid-cols-1 md:grid-cols-2 gap-5" : "space-y-6"}>
      {items.map(n => {
        const st = NEWS_STATUS[n.status];
        return (
          <li key={n.id} id={n.id} className="rounded-2xl border border-slate-900/10 bg-white p-5 scroll-mt-20">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <time dateTime={n.date} className="font-semibold text-slate-500">{newsDate(n.date)}</time>
              <span className={`px-2 py-0.5 rounded-full border font-bold ${st.style}`}>{st.label}</span>
            </div>
            <h3 className="mt-2 text-lg font-bold text-slate-900">{n.title}</h3>
            <p className={`mt-1.5 text-slate-600 leading-relaxed ${compact ? "text-sm" : ""}`}>{n.text}</p>
          </li>
        );
      })}
    </ul>
  );
}
