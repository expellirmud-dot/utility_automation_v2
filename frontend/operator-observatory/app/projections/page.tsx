"use client";

import { ProjectionSummary } from "../../components/projection-summary";
import { StatePanel } from "../../components/state-panel";
import { useObservatoryFetch } from "../../hooks/use-observatory-fetch";
import { fetchProjections, fetchSurfaces } from "../../lib/backend-client";
import type { ProjectionsResponse, SurfacesResponse } from "../../lib/types";

export default function ProjectionsPage() {
  const projState = useObservatoryFetch<ProjectionsResponse>(
    fetchProjections,
    (data) => data.cards.length === 0
  );
  const surfState = useObservatoryFetch<SurfacesResponse>(fetchSurfaces);

  if (projState.status === "loading" || surfState.status === "loading") {
    return <StatePanel title="Loading" detail="Fetching projections and surfaces..." />;
  }
  if (projState.status === "error") return <StatePanel title="Error" detail={projState.message} />;
  if (surfState.status === "error") return <StatePanel title="Error" detail={surfState.message} />;
  if (projState.status === "empty") {
    return <StatePanel title="Empty" detail="No projections are currently available." />;
  }

  if (projState.status === "ready" && surfState.status === "ready") {
    return (
      <>
        <header>
          <h2 className="text-3xl font-semibold text-[var(--ink)]">Projection Registry</h2>
          <p className="text-base text-[var(--muted)] mt-2">Registry of all active projections and their provider status.</p>
        </header>

        <ProjectionSummary
          projections={projState.data.cards}
          surfaces={surfState.data.surfaces}
        />
      </>
    );
  }

  return null;
}
