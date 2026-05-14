import type { DomainPanel } from "../lib/types";

type DomainPanelProps = {
  panel: DomainPanel;
};

function metadataText(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return "n/a";
}

export function DomainPanel({ panel }: DomainPanelProps) {
  const isDegraded = panel.status === "degraded";
  const isEmpty = panel.status === "empty" || panel.item_count === 0;
  const visibleSummaries = panel.summaries.slice(0, 3);

  return (
    <article className="rounded-2xl border border-[var(--line)] bg-white/80 p-5 shadow-soft backdrop-blur">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-[var(--muted)]">{panel.domain}</p>
          <h3 className="mt-2 text-lg font-semibold text-[var(--ink)]">
            {metadataText(panel.metadata.title)}
          </h3>
        </div>
        <span
          className={
            isDegraded
              ? "rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800"
              : "rounded-full bg-[var(--accent-soft)] px-3 py-1 text-xs font-semibold text-[var(--accent)]"
          }
        >
          {panel.status}
        </span>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-3 text-sm">
        <div>
          <p className="text-[var(--muted)]">Items</p>
          <p className="mt-1 text-lg font-semibold">{panel.item_count}</p>
        </div>
        <div>
          <p className="text-[var(--muted)]">Source</p>
          <p className="mt-1 truncate font-semibold">{panel.source}</p>
        </div>
        <div>
          <p className="text-[var(--muted)]">Truth</p>
          <p className="mt-1 truncate font-semibold">
            {metadataText(panel.metadata.source_of_truth)}
          </p>
        </div>
      </div>

      <div className="mt-5 rounded-2xl border border-[var(--line)] bg-slate-50/70 p-4">
        {isEmpty ? (
          <p className="text-sm text-[var(--muted)]">No projection rows are available.</p>
        ) : (
          <ul className="space-y-3">
            {visibleSummaries.map((summary, index) => (
              <li key={`${panel.domain}-${index}`} className="text-sm">
                <p className="font-medium text-[var(--ink)]">
                  {metadataText(summary.label)}
                </p>
                <p className="mt-1 text-[var(--muted)]">{metadataText(summary.id)}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </article>
  );
}
