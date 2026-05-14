"use client";

import { DomainPanel } from "../../components/domain-panel";
import { StatePanel } from "../../components/state-panel";
import { useObservatoryFetch } from "../../hooks/use-observatory-fetch";
import { fetchDomainPanels } from "../../lib/backend-client";
import type { DomainPanelsResponse } from "../../lib/types";

export default function PanelsPage() {
  const state = useObservatoryFetch<DomainPanelsResponse>(
    fetchDomainPanels,
    (data) => data.panels.length === 0
  );

  if (state.status === "loading") {
    return <StatePanel title="Loading" detail="Fetching domain panels..." />;
  }
  if (state.status === "error") {
    return <StatePanel title="Error" detail={state.message} />;
  }
  if (state.status === "empty") {
    return <StatePanel title="Empty" detail="No domain panels are currently available." />;
  }

  if (state.status === "ready") {
    return (
      <>
        <header>
          <h2 className="text-3xl font-semibold text-[var(--ink)]">Domain Panels</h2>
          <p className="text-base text-[var(--muted)] mt-2">Detailed view of domain projections and diagnostics.</p>
        </header>

        <section className="grid gap-5 lg:grid-cols-2">
          {state.data.panels.map((panel) => (
            <DomainPanel key={panel.domain} panel={panel} />
          ))}
        </section>
      </>
    );
  }

  return null;
}
