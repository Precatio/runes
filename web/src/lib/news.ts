import news from "../../content/news.json";

// Short notices about new features and work in progress (web/content/news.json), newest first: on the start page
// (the latest few) and at /nyheter (all of them). Written by hand and published with the site.
export interface NewsItem { id: string; date: string; status: "nytt" | "på gång"; title: string; text: string }

export const NEWS: NewsItem[] = [...(news.items as NewsItem[])].sort((a, b) => b.date.localeCompare(a.date));

export const NEWS_STATUS: Record<NewsItem["status"], { label: string; style: string }> = {
  "nytt": { label: "Nytt i appen", style: "bg-emerald-50 text-emerald-800 border-emerald-200" },
  "på gång": { label: "På gång", style: "bg-amber-50 text-amber-900 border-amber-200" },
};

export const newsDate = (d: string) =>
  new Date(`${d}T12:00:00Z`).toLocaleDateString("sv-SE", { day: "numeric", month: "long", year: "numeric" });
