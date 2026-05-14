import type { ProjectionCard, Surface } from "../lib/types";

type ProjectionSummaryProps = {
  projections: ProjectionCard[];
  surfaces: Surface[];
};

export function ProjectionSummary({ projections, surfaces }: ProjectionSummaryProps) {
  return (
    <section className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
      <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-6 shadow-soft backdrop-blur">
        <h2 className="text-xl font-semibold text-[var(--ink)]">Projection Federation</h2>
        <div className="mt-5 overflow-x-auto stable-scrollbar">
          <table className="w-full min-w-[720px] border-separate border-spacing-0 text-left text-sm">
            <thead className="text-[var(--muted)]">
              <tr>
                <th className="border-b border-[var(--line)] pb-3 font-medium">Domain</th>
                <th className="border-b border-[var(--line)] pb-3 font-medium">Status</th>
                <th className="border-b border-[var(--line)] pb-3 font-medium">Provider</th>
                <th className="border-b border-[var(--line)] pb-3 font-medium">Items</th>
                <th className="border-b border-[var(--line)] pb-3 font-medium">Order</th>
              </tr>
            </thead>
            <tbody>
              {projections.map((card) => (
                <tr key={card.key}>
                  <td className="border-b border-[var(--line)] py-3 font-medium">
                    {card.title}
                  </td>
                  <td className="border-b border-[var(--line)] py-3">{card.status}</td>
                  <td className="border-b border-[var(--line)] py-3">
                    {card.provider_status.provider_kind}
                  </td>
                  <td className="border-b border-[var(--line)] py-3">{card.item_count}</td>
                  <td className="border-b border-[var(--line)] py-3">{card.stable_order}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-6 shadow-soft backdrop-blur">
        <h2 className="text-xl font-semibold text-[var(--ink)]">Read-only Surfaces</h2>
        <ul className="mt-5 space-y-4">
          {surfaces.map((surface) => (
            <li key={surface.key} className="rounded-2xl border border-[var(--line)] bg-white/70 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">{surface.title}</p>
                  <p className="mt-1 text-sm text-[var(--muted)]">{surface.api_prefix}</p>
                </div>
                <span className="rounded-full bg-[var(--accent-soft)] px-3 py-1 text-xs font-semibold text-[var(--accent)]">
                  {surface.allowed_methods.join(", ")}
                </span>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
