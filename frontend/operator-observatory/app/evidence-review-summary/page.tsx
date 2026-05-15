"use client";

import { StatePanel } from "../../components/state-panel";
import { useObservatoryFetch } from "../../hooks/use-observatory-fetch";
import { fetchEvidenceReviewSummary } from "../../lib/backend-client";
import type { EvidenceReviewSummaryResponse } from "../../lib/types";

export default function EvidenceReviewSummaryPage() {
  const data = useObservatoryFetch(fetchEvidenceReviewSummary);

  if (data.status === "loading") {
    return <StatePanel title="Loading" detail="Fetching evidence review summary..." />;
  }

  if (data.status === "error") {
    return <StatePanel title="Error" detail={data.message} />;
  }

  if (data.status === "ready" && data.data) {
    const { summary } = data.data;

    return (
      <main className="p-8 max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-[var(--ink)]">Evidence Review Summary</h1>
          <p className="text-[var(--muted)]">
            Deterministic consolidated view of package integrity and readiness.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Core Identity */}
          <section className="p-6 bg-white border border-[var(--line)] rounded-xl shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--accent)] mb-4">
              Core Identity
            </h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center border-b border-[var(--line)] pb-2">
                <span className="text-sm text-[var(--muted)]">Package ID</span>
                <span className="text-sm font-mono font-medium text-[var(--ink)]">{summary.package_id}</span>
              </div>
              <div className="flex justify-between items-center border-b border-[var(--line)] pb-2">
                <span className="text-sm text-[var(--muted)]">Package Hash</span>
                <span className="text-xs font-mono text-[var(--ink)] truncate max-w-[200px]">{summary.package_hash}</span>
              </div>
              <div className="flex justify-between items-center border-b border-[var(--line)] pb-2">
                <span className="text-sm text-[var(--muted)]">Summary Version</span>
                <span className="text-sm font-mono text-[var(--ink)]">{summary.summary_version}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-[var(--muted)]">Summary Hash</span>
                <span className="text-xs font-mono text-[var(--ink)] truncate max-w-[200px]">{summary.summary_hash}</span>
              </div>
            </div>
          </section>

          {/* Governance Status */}
          <section className="p-6 bg-white border border-[var(--line)] rounded-xl shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--accent)] mb-4">
              Governance Status
            </h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center border-b border-[var(--line)] pb-2">
                <span className="text-sm text-[var(--muted)]">Package Status</span>
                <span className={`text-xs font-bold px-2 py-1 rounded ${
                  summary.package_status === "PACKAGE_VERIFIED" 
                    ? "bg-green-100 text-green-700" 
                    : "bg-yellow-100 text-yellow-700"
                }`}>
                  {summary.package_status}
                </span>
              </div>
              <div className="flex justify-between items-center border-b border-[var(--line)] pb-2">
                <span className="text-sm text-[var(--muted)]">Integrity Passed</span>
                <span className={`text-sm font-medium ${summary.integrity_passed ? "text-green-600" : "text-red-600"}`}>
                  {summary.integrity_passed ? "Yes" : "No"}
                </span>
              </div>
              <div className="flex justify-between items-center border-b border-[var(--line)] pb-2">
                <span className="text-sm text-[var(--muted)]">Readiness Decision</span>
                <span className={`text-sm font-medium ${
                  summary.readiness_decision === "READY" ? "text-green-600" : "text-red-600"
                }`}>
                  {summary.readiness_decision}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-[var(--muted)]">Reason Codes</span>
                <div className="flex gap-1 flex-wrap justify-end max-w-[200px]">
                  {summary.reason_codes.map((code: string) => (
                    <span key={code} className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded border border-gray-200 font-mono">
                      {code}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* Report Hashes */}
          <section className="p-6 bg-white border border-[var(--line)] rounded-xl shadow-sm md:col-span-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--accent)] mb-4">
              Referenced Report Hashes
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg border border-[var(--line)]">
                <p className="text-xs text-[var(--muted)] mb-1">Integrity Report Hash</p>
                <p className="text-xs font-mono text-[var(--ink)] truncate">{summary.integrity_report_hash}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg border border-[var(--line)]">
                <p className="text-xs text-[var(--muted)] mb-1">Readiness Report Hash</p>
                <p className="text-xs font-mono text-[var(--ink)] truncate">{summary.readiness_report_hash}</p>
              </div>
            </div>
          </section>
        </div>
      </main>
    );
  }

  return <StatePanel title="Error" detail="An unexpected error occurred while loading evidence review summary data." />;
}

