"use client";

import { StatePanel } from "../../components/state-panel";
import { useObservatoryFetch } from "../../hooks/use-observatory-fetch";
import { fetchSurfaces } from "../../lib/backend-client";
import type { SurfacesResponse, Surface } from "../../lib/types";

function SurfaceRow({ surface }: { surface: Surface }) {
  return (
    <tr className="border-b border-[var(--line)]">
      <td className="py-3 px-4 font-medium text-[var(--ink)]">{surface.title}</td>
      <td className="py-3 px-4 text-sm text-[var(--muted)] font-mono">{surface.route_prefix}</td>
      <td className="py-3 px-4 text-sm text-[var(--muted)] font-mono">{surface.api_prefix}</td>
      <td className="py-3 px-4 text-center">
        <span className={`text-xs px-2 py-1 rounded-full font-semibold ${
          surface.status === "active" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
        }`}>
          {surface.status}
        </span>
      </td>
      <td className="py-3 px-4 text-center">
        {surface.read_only ? "Yes" : "No"}
      </td>
    </tr>
  );
}

export default function SurfacesPage() {
  const state = useObservatoryFetch<SurfacesResponse>(
    fetchSurfaces,
    (data) => data.surfaces.length === 0
  );

  if (state.status === "loading") {
    return <StatePanel title="Loading" detail="Fetching surfaces..." />;
  }
  if (state.status === "error") {
    return <StatePanel title="Error" detail={state.message} />;
  }
  if (state.status === "empty") {
    return <StatePanel title="Empty" detail="No surfaces are currently available." />;
  }

  if (state.status === "ready") {
    return (
      <>
        <header>
          <h2 className="text-3xl font-semibold text-[var(--ink)]">Surface Registry</h2>
          <p className="text-base text-[var(--muted)] mt-2">Detailed registry of all exposed observability surfaces.</p>
        </header>

        <div className="overflow-x-auto rounded-xl border border-[var(--line)] bg-white">
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wider text-[var(--muted)] border-b border-[var(--line)]">
              <tr>
                <th className="py-3 px-4">Title</th>
                <th className="py-3 px-4">Route Prefix</th>
                <th className="py-3 px-4">API Prefix</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-center">Read-Only</th>
              </tr>
            </thead>
            <tbody>
              {state.data.surfaces.map((surface) => (
                <SurfaceRow key={surface.key} surface={surface} />
              ))}
            </tbody>
          </table>
        </div>
      </>
    );
  }

  return null;
}
