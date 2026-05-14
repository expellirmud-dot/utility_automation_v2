"use client";

import { useEffect, useState } from "react";
import { DomainPanel } from "../components/domain-panel";
import { ProjectionSummary } from "../components/projection-summary";
import { RouteGovernancePanel } from "../components/route-governance-panel";
import { StatusCard } from "../components/status-card";
import { fetchObservatoryData, getOpsApiBaseUrl } from "../lib/backend-client";
import type { ObservatoryData } from "../lib/types";

type LoadState =
  | { status: "loading" }
  | { status: "ready"; data: ObservatoryData }
  | { status: "empty" }
  | { status: "degraded"; message: string }
  | { status: "error"; message: string };

function classifyError(error: unknown): string {
  return error instanceof Error ? error.message : "Unable to read observability data.";
}

export default function OperatorObservatoryPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let active = true;

    fetchObservatoryData()
      .then((data) => {
        if (!active) {
          return;
        }
        if (data.domainPanels.panels.length === 0 && data.overview.cards.length === 0) {
          setState({ status: "empty" });
          return;
        }
        if (!data.routeGovernance.valid) {
          setState({ status: "degraded", message: "Route governance reported violations." });
          return;
        }
        setState({ status: "ready", data });
      })
      .catch((error: unknown) => {
        if (active) {
          setState({ status: "error", message: classifyError(error) });
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-8 px-5 py-6 sm:px-8 lg:px-10">
      <header className="grid gap-5 rounded-2xl border border-[var(--line)] bg-white/70 p-6 shadow-soft backdrop-blur lg:grid-cols-[1fr_auto] lg:items-end">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">
            Operator Observatory
          </p>
          <h1 className="mt-3 max-w-3xl text-4xl font-semibold tracking-normal text-[var(--ink)] sm:text-5xl">
            Read-only governance visibility
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--muted)]">
            Thin projection console for ops telemetry, route governance, and domain panels.
          </p>
        </div>
        <div className="rounded-2xl border border-[var(--line)] bg-white/80 p-4 text-sm shadow-sm">
          <p className="text-[var(--muted)]">Backend</p>
          <p className="mt-1 max-w-[20rem] truncate font-semibold">{getOpsApiBaseUrl()}</p>
        </div>
      </header>

      {state.status === "loading" ? <StatePanel title="Loading" detail="Reading GET projection endpoints." /> : null}
      {state.status === "empty" ? <StatePanel title="Empty" detail="No projection data is currently available." /> : null}
      {state.status === "degraded" ? <StatePanel title="Degraded" detail={state.message} /> : null}
      {state.status === "error" ? <StatePanel title="Error" detail={state.message} /> : null}

      {state.status === "ready" ? (
        <>
          <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {state.data.overview.cards.map((card) => (
              <StatusCard key={card.key} card={card} />
            ))}
          </section>

          <RouteGovernancePanel report={state.data.routeGovernance} />

          <ProjectionSummary
            projections={state.data.projections.cards}
            surfaces={state.data.surfaces.surfaces}
          />

          <section className="grid gap-5 lg:grid-cols-2">
            {state.data.domainPanels.panels.map((panel) => (
              <DomainPanel key={panel.domain} panel={panel} />
            ))}
          </section>
        </>
      ) : null}
    </main>
  );
}

function StatePanel({ title, detail }: { title: string; detail: string }) {
  return (
    <section className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-8 shadow-soft backdrop-blur">
      <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
        {title}
      </p>
      <p className="mt-3 text-base leading-7 text-[var(--muted)]">{detail}</p>
    </section>
  );
}
