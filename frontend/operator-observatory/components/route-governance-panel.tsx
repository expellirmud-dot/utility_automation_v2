import type { RouteGovernanceResponse } from "../lib/types";

type RouteGovernancePanelProps = {
  report: RouteGovernanceResponse;
};

export function RouteGovernancePanel({ report }: RouteGovernancePanelProps) {
  return (
    <section className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-6 shadow-soft backdrop-blur">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.14em] text-[var(--accent)]">
            Route Governance
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-[var(--ink)]">
            GET-only observability boundary
          </h2>
        </div>
        <span
          className={
            report.valid
              ? "w-fit rounded-full bg-[var(--accent-soft)] px-3 py-1 text-sm font-semibold text-[var(--accent)]"
              : "w-fit rounded-full bg-amber-100 px-3 py-1 text-sm font-semibold text-amber-800"
          }
        >
          {report.valid ? "valid" : "degraded"}
        </span>
      </div>

      <dl className="mt-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-[var(--line)] bg-white/70 p-4">
          <dt className="text-sm text-[var(--muted)]">Checked routes</dt>
          <dd className="mt-2 text-2xl font-semibold">{report.checked_routes}</dd>
        </div>
        <div className="rounded-2xl border border-[var(--line)] bg-white/70 p-4">
          <dt className="text-sm text-[var(--muted)]">Registry surfaces</dt>
          <dd className="mt-2 text-2xl font-semibold">{report.registry_surface_count}</dd>
        </div>
        <div className="rounded-2xl border border-[var(--line)] bg-white/70 p-4">
          <dt className="text-sm text-[var(--muted)]">Violations</dt>
          <dd className="mt-2 text-2xl font-semibold">{report.violations.length}</dd>
        </div>
      </dl>
    </section>
  );
}
