import { cloneElement, useMemo, useState } from "react";
import Link from "next/link";
import { InfoTip, Tip } from "@/components/Explain";
import { GLOSSARY } from "@/lib/glossary";
import type { Finding, SortState, SortValue, StoneExtras, Verdict } from "./typer";
import { MARK, TONE } from "@/lib/tone";

export function MaterialCell({ x }: { x: StoneExtras }) {
  if (!x.material) return <span className="text-slate-400">–</span>;
  const mark = x.material_fit === true ? "✓" : x.material_fit === false ? "!" : "";
  return (
    <span title={x.material_text ?? ""} className={x.material_fit === false ? "text-slate-800 font-semibold" : ""}>
      {x.material} {mark && <span className={`font-bold ${x.material_fit ? MARK.yes : MARK.no}`}>{mark}</span>}
    </span>
  );
}

export function LanguageCell({ x }: { x: StoneExtras }) {
  if (!x.language || !x.language.comparable) return <span className="text-slate-400">–</span>;
  return (
    <span title={x.language.text} className={x.language.fits === false ? "text-slate-800 font-semibold" : ""}>
      {x.language.agree}/{x.language.comparable}
    </span>
  );
}

export function useSorted<T>(rows: T[], get: Record<string, (r: T) => SortValue>, initial: SortState) {
  const [sort, setSort] = useState<SortState>(initial);
  const sorted = useMemo(() => {
    const f = get[sort.key];
    if (!f) return rows;
    return [...rows].sort((a, b) => {
      const va = f(a), vb = f(b);
      if (va == null && vb == null) return 0;
      if (va == null) return 1; // missing values last
      if (vb == null) return -1;
      const c = typeof va === "string" || typeof vb === "string"
        ? String(va).localeCompare(String(vb), "sv", { numeric: true })
        : Number(va) - Number(vb);
      return sort.desc ? -c : c;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows, sort]);
  const header = (key: string, label: string, title?: string) => (
    <th className="p-2 whitespace-nowrap">
      <button onClick={() => setSort(s => ({ key, desc: s.key === key ? !s.desc : rows.length > 0 && typeof get[key](rows[0]) !== "string" }))}
        className={`uppercase tracking-wider hover:text-slate-900 ${sort.key === key ? "text-slate-900" : ""}`}>
        {label}{sort.key === key ? (sort.desc ? " ↓" : " ↑") : ""}
      </button>
      <InfoTip text={GLOSSARY[label] ?? title} />
    </th>
  );
  return { sorted, header, sort, setSort };
}

export const VERDICT_STYLE: Record<Verdict, string> = {
  "stämmer": TONE.neutral,
  "nytt": TONE.tint,
  "motsäger": TONE.caution,
};

// The interpretation's conclusion, strongest first; dots make the scale readable without colour
export const LEVELS: { key: string; dots: string; style: string; help: string }[] = [
  { key: "starkt", dots: "●●●", style: TONE.fill,
    help: "Minst två oberoende belägg för och inget emot (för ortografin dessutom justerat p under 0,05)." },
  { key: "måttligt", dots: "●●○", style: TONE.tint,
    help: "Belägg för, minst lika många för som emot, men inte tillräckligt för starkt. En prövbar hypotes." },
  { key: "svagt", dots: "●○○", style: "bg-slate-50 text-slate-700 border-slate-300",
    help: "Lite stöd, belägg emot eller en stilgrupp som talar emot." },
  { key: "bekräftelse", dots: "✓", style: TONE.outline,
    help: "Metoden kommer fram till samma sak som Rundata." },
  { key: "redan känt", dots: "○", style: "bg-white text-slate-600 border-slate-200",
    help: "Förslaget finns redan i nyare källor (Runor 2020 eller Wikidata)." },
  { key: "metodfel", dots: "!", style: TONE.caution,
    help: "Fyndet motsäger en signerad sten – en svaghet i metoden, inte ett fel i Rundata." },
];
export const LEVEL_RANK = Object.fromEntries(LEVELS.map((l, i) => [l.key, LEVELS.length - i]));

export function SortTh({ className, children }: { className: string; children: React.ReactElement<{ className?: string }> }) {
  return cloneElement(children, { className: `${children.props.className ?? ""} ${className}` });
}

export function LevelBadge({ it }: { it?: Finding["interpretation"] }) {
  if (!it) return <span className="text-slate-400 text-xs">–</span>;
  const l = LEVELS.find(x => x.key === it.level);
  return (
    <div className="flex flex-col gap-0.5">
      <Tip text={`${l?.help ?? ""} Klicka på raden för hela resonemanget.`}>
        <span className={`inline-flex w-fit items-center gap-1.5 rounded-lg border px-2 py-0.5 text-xs font-bold ${l?.style ?? "border-slate-200"}`}>
          <span aria-hidden className="tracking-[-0.15em] text-[10px]">{l?.dots}</span>{it.level}
        </span>
      </Tip>
      {!["bekräftelse", "redan känt", "metodfel"].includes(it.level) && (
        <Tip text="Belägg utöver metodens eget: andra metoder, språkdrag, stil och bergart som talar för eller emot förslaget.">
          <span className="text-[11px] text-slate-500">andra belägg: {it.support} för, {it.against} emot</span>
        </Tip>
      )}
    </div>
  );
}

export function Score({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-1.5 min-w-[70px]">
      <div className="h-1.5 w-10 bg-slate-200 rounded-full overflow-hidden">
        <div className="h-full bg-slate-700 rounded-full" style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
      <span className="text-[11px] font-mono text-slate-600">{Math.round(value * 100)}</span>
    </div>
  );
}

export const pct = (n: number, d: number) => (d ? Math.round((100 * n) / d) : 0);
export const fmt = (v: number | null | undefined, digits = 2) => (v == null ? "–" : v.toFixed(digits).replace(".", ","));

function Bar({ value, total, color }: { value: number; total: number; color: string }) {
  return (
    <div className="flex items-center gap-2 min-w-[110px]">
      <div className="h-2 flex-1 bg-slate-200 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct(value, total)}%`, background: color }} />
      </div>
      <span className="text-[11px] font-mono text-slate-600 w-9 text-right">{pct(value, total)} %</span>
    </div>
  );
}

export function StoneLinks({ signum, stacked }: { signum: string; stacked?: boolean }) {
  return (
    <span className={stacked ? "flex flex-col text-xs" : "whitespace-nowrap text-xs"} onClick={e => e.stopPropagation()}>
      <Link href={`/inskrifter?signum=${encodeURIComponent(signum)}`} className={`font-bold text-slate-900 hover:text-[#b7410e] ${stacked ? "break-words" : ""}`}>{signum}</Link>
      <Link href={`/3d?signum=${encodeURIComponent(signum)}`} className={`${stacked ? "text-[11px]" : "ml-2"} text-[#b7410e] hover:underline`}
        title="Öppnar 3D-analysen för att mäta huggspåren. Länken betyder inte att stenen redan är mätt.">{stacked ? "mät i 3D" : "öppna i 3D-analysen"}</Link>
    </span>
  );
}

export const TH_ROW = "text-left text-[11px] uppercase tracking-wider text-slate-500";

// Links to the inscriptions behind a number: same definitions as in the table
export const gapHref = (gap: string, province?: string) =>
  `/inskrifter?gap=${gap}${province ? `&province=${encodeURIComponent(province)}` : ""}`;
export const signaHref = (signa: string[]) => `/inskrifter?signa=${encodeURIComponent(signa.join(","))}`;
export const CELL_LINK = "hover:text-[#b7410e] hover:underline decoration-[#b7410e]/40 underline-offset-2";

export function BarLink({ value, total, color, has, missing }: { value: number; total: number; color: string; has: string; missing: string }) {
  return (
    <div className="flex items-center gap-2">
      <Link href={has} title={`Visa de ${value} som har uppgiften`} className="flex-1"><Bar value={value} total={total} color={color} /></Link>
      {total - value > 0 && (
        <Link href={missing} title={`Visa de ${total - value} som saknar uppgiften`} className="text-[11px] text-slate-500 whitespace-nowrap hover:text-[#b7410e]">
          {total - value} saknar
        </Link>
      )}
    </div>
  );
}

export function Chip({ label, children, title }: { label: string; children: React.ReactNode; title?: string }) {
  return (
    <span title={title} className="inline-flex items-center gap-1 rounded-md bg-slate-900/[0.04] px-1.5 py-0.5 text-[11px] text-slate-700">
      <span className="text-slate-500">{label}</span>{children}
    </span>
  );
}
