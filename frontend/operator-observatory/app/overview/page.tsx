"use client";

import { StatusCard } from "../../components/status-card";
import { RouteGovernancePanel } from "../../components/route-governance-panel";
import { ProjectionSummary } from "../../components/projection-summary";
import { DomainPanel } from "../../components/domain-panel";
import { StatePanel } from "../../components/state-panel";
import { useObservatoryFetch } from "../../hooks/use-observatory-fetch";
import { fetchOverview, fetchProjections, fetchSurfaces, fetchRouteGovernance, fetchDomainPanels } from "../../lib/backend-client";
import type { OverviewResponse, ProjectionsResponse, SurfacesResponse, RouteGovernanceResponse, DomainPanelsResponse } from "../../lib/types";

export default function OverviewPage() {
  // Note: For the overview page, we still want the aggregate view.
  // We'll use the granular fetchers.
  
  const overview = useObservatoryFetch(fetchOverview);
  const projections = useObservatoryFetch(fetchProjections);
  const surfaces = useObservatoryFetch(fetchSurfaces);
  const routeGov = useObservatoryFetch(fetchRouteGovernance);
  const panels = useObservatoryFetch(fetchDomainPanels);

  if (overview.status === "loading" || projections.status === "loading" || surfaces.status === "loading" || routeGov.status === "loading" || panels.status === "loading") {
    return <StatePanel title="Loading" detail="Reading GET projection endpoints." />;
  }

  if (overview.status === "error") return <StatePanel title="Error" detail={overview.message} />;
  if (projections.status === "error") return <StatePanel title="Error" detail={projections.message} />;
  if (surfaces.status === "error") return <StatePanel title="Error" detail={surfaces.message} />;
  if (routeGov.status === "error") return <StatePanel title="Error" detail={routeGov.message} />;
  if (panels.status === "error") return <StatePanel title="Error" detail={panels.message} />;

  if (overview.status === "ready" && projections.status === "ready" && surfaces.status === "ready" && routeGov.status === "ready" && panels.status === "ready") {
    const data = {
      overview: overview.data,
      projections: projections.data,
      surfaces: surfaces.data,
      routeGovernance: routeGov.data,
      domainPanels: panels.data,
    };

    if (data.domainPanels.panels.length === 0 && data.overview.cards.length === 0) {
      return <StatePanel title="Empty" detail="No projection data is currently available." />;
    }

    if (!data.routeGovernance.valid) {
      return <StatePanel title="Degraded" detail="Route governance reported violations." />;
    }

    return (
      <>
        <header>
          <h2 className="text-3xl font-semibold text-[var(--ink)]">Executive Summary</h2>
          <p className="text-base text-[var(--muted)] mt-2">High-level status of the governance platform.</p>
        </header>

        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {data.overview.cards.map((card) => (
            <StatusCard key={card.key} card={card} />
          ))}
        </section>

        <RouteGovernancePanel report={data.routeGovernance} />

        <ProjectionSummary
          projections={data.projections.cards}
          surfaces={data.surfaces.surfaces}
        />

        <section className="grid gap-5 lg:grid-cols-2">
          {data.domainPanels.panels.map((panel) => (
            <DomainPanel key={panel.domain} panel={panel} />
          ))}
        </section>
      </>
    );
  }

  return <StatePanel title="Error" detail="An unexpected error occurred while loading overview data." />;
}
