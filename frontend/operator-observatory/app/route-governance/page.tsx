"use client";

import { RouteGovernancePanel } from "../../components/route-governance-panel";
import { StatePanel } from "../../components/state-panel";
import { useObservatoryFetch } from "../../hooks/use-observatory-fetch";
import { fetchRouteGovernance } from "../../lib/backend-client";
import type { RouteGovernanceResponse } from "../../lib/types";

export default function RouteGovernancePage() {
  const state = useObservatoryFetch<RouteGovernanceResponse>(fetchRouteGovernance);

  if (state.status === "loading") {
    return <StatePanel title="Loading" detail="Fetching route governance audit..." />;
  }
  if (state.status === "error") {
    return <StatePanel title="Error" detail={state.message} />;
  }

  if (state.status === "ready") {
    return (
      <>
        <header>
          <h2 className="text-3xl font-semibold text-[var(--ink)]">Route Governance</h2>
          <p className="text-base text-[var(--muted)] mt-2">Audit of route registry and governance invariants.</p>
        </header>

        <RouteGovernancePanel report={state.data} />
      </>
    );
  }

  return null;
}
