import type { OverviewCard } from "../lib/types";

type StatusCardProps = {
  card: OverviewCard;
};

export function StatusCard({ card }: StatusCardProps) {
  const tone = card.fallback_active || card.status !== "connected" ? "amber" : "teal";

  return (
    <article className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-5 shadow-soft backdrop-blur">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-[var(--muted)]">{card.key}</p>
          <h2 className="mt-2 text-xl font-semibold tracking-normal text-[var(--ink)]">
            {card.title}
          </h2>
        </div>
        <span
          className={
            tone === "teal"
              ? "rounded-full bg-[var(--accent-soft)] px-3 py-1 text-xs font-semibold text-[var(--accent)]"
              : "rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800"
          }
        >
          {card.status}
        </span>
      </div>
      <p className="mt-4 text-sm leading-6 text-[var(--muted)]">{card.label}</p>
      <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
        <div>
          <dt className="text-[var(--muted)]">Read only</dt>
          <dd className="mt-1 font-semibold">{card.read_only ? "true" : "false"}</dd>
        </div>
        <div>
          <dt className="text-[var(--muted)]">Authority</dt>
          <dd className="mt-1 font-semibold">
            {card.authority_coupled ? "coupled" : "decoupled"}
          </dd>
        </div>
      </dl>
    </article>
  );
}
