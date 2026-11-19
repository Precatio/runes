"use client";

// The review before approval, shown at each row of "Veckans publiceringar" (Admin's WeekApproval and /redaktion's
// RedaktionWeek), and the line that says how long the queue lasts. The findings come from src/article_lint.py (Admin,
// through the API) or web/src/lib/articleLint.ts (/redaktion, in the browser); the rules are the same.

export interface ReviewFinding { niva: "FEL" | "VARNING"; kod: string; sprak: string; text: string; utdrag?: string }
export interface Review { fel: number; varningar: number; fynd: ReviewFinding[] }

const chip = "inline-block text-[11px] font-semibold rounded-md px-1.5 py-0.5 border";
const ok = `${chip} border-emerald-300 bg-emerald-50 text-emerald-800`;
const warn = `${chip} border-amber-300 bg-amber-50 text-amber-800`;
const bad = `${chip} border-red-300 bg-red-50 text-red-700`;

/** "granskning: 2 fel, 3 varningar" as a chip. */
export function ReviewChip({ review }: { review: Review | null }) {
  if (!review) return null;
  if (!review.fel && !review.varningar) return <span className={ok}>granskning: inga anmärkningar</span>;
  return (
    <span className={review.fel ? bad : warn}>{`granskning: ${review.fel} fel, ${review.varningar} varningar`}</span>
  );
}

/** The findings, errors first, folded away until opened (open from the start when there are errors). */
export function ReviewList({ review }: { review: Review | null }) {
  if (!review || !review.fynd.length) return null;
  const sorted = [...review.fynd].sort((a, b) => (a.niva === b.niva ? 0 : a.niva === "FEL" ? -1 : 1));
  return (
    <details className="text-xs text-slate-700" open={review.fel > 0}>
      <summary className="cursor-pointer py-1 font-semibold">{`Granskningen (${review.fel} fel, ${review.varningar} varningar)`}</summary>
      <ul className="mt-1 space-y-1.5">
        {sorted.map((f, i) => (
          <li key={i} className={`rounded-lg border px-2 py-1.5 ${f.niva === "FEL" ? "border-red-200 bg-red-50/60" : "border-amber-200 bg-amber-50/60"}`}>
            <span className={`font-bold ${f.niva === "FEL" ? "text-red-700" : "text-amber-800"}`}>
              {f.niva === "FEL" ? "Fel" : "Varning"}
            </span>
            <span className="text-slate-500">{f.sprak === "en" ? " (engelska): " : " (svenska): "}</span>
            <span>{f.text}</span>
            {f.utdrag && <div className="mt-0.5 text-slate-500 break-words" translate="no">{f.utdrag}</div>}
          </li>
        ))}
      </ul>
    </details>
  );
}

/** In the confirmation: the chosen rows whose review found errors, and the box the editor must tick to go on. */
export function ErrorConfirmation({ titles, confirmed, onChange }: {
  titles: string[]; confirmed: boolean; onChange: (v: boolean) => void;
}) {
  if (!titles.length) return null;
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-2.5 space-y-1.5 text-sm text-red-800" role="alert">
      <p className="font-semibold">
        {titles.length === 1 ? "Granskningen hittade fel i en artikel:" : `Granskningen hittade fel i ${titles.length} artiklar:`}
      </p>
      <ul className="list-disc pl-5" translate="no">{titles.map(t => <li key={t}>{t}</li>)}</ul>
      <label className="flex items-start gap-2 pt-1">
        <input type="checkbox" checked={confirmed} onChange={e => onChange(e.target.checked)} className="mt-1 h-4 w-4 accent-[#b7410e]" />
        <span>Jag har läst felen och vill schemalägga ändå.</span>
      </label>
    </div>
  );
}

const longDay = (day: string) =>
  new Date(`${day}T12:00:00Z`).toLocaleDateString("sv-SE", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });

/** "Kön räcker till …", and a clear alarm when fewer than three weeks remain. */
export function QueueNotice({ until, daysLeft, alarm }: { until: string | null; daysLeft: number; alarm: boolean }) {
  if (!until) {
    return (
      <div role="alert" className="rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm font-semibold text-red-800">
        Kön är tom: ingen artikel är schemalagd eller planerad framåt.
      </div>
    );
  }
  if (alarm) {
    return (
      <div role="alert" className="rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">
        <span className="font-semibold">Kön räcker bara till </span>
        <span className="font-semibold" translate="no">{longDay(until)}</span>
        <span>{` – ${daysLeft} dagar kvar, mindre än tre veckor. Skriv och planera nya artiklar (en var tredje dag).`}</span>
      </div>
    );
  }
  return (
    <p className="text-sm text-slate-600">
      <span>Kön räcker till </span>
      <span className="font-semibold" translate="no">{longDay(until)}</span>
      <span>{` (${daysLeft} dagar kvar).`}</span>
    </p>
  );
}
