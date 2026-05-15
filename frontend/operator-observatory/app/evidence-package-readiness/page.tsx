"use client";

import { StatePanel } from "../../components/state-panel";
import { useObservatoryFetch } from "../../hooks/use-observatory-fetch";
import { fetchEvidencePackageReadiness } from "../../lib/backend-client";
import type { EvidencePackageReadinessResponse } from "../../lib/types";

function DetailSection({ title, items }: { 
  title: string; 
  items: { label: string; value: any }[] 
}) {
  return (
    <section className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-6 shadow-soft backdrop-blur">
      <h3 className="mb-4 text-lg font-semibold text-[var(--ink)]">{title}</h3>
      <dl className="grid grid-cols-1 gap-y-4 sm:grid-cols-2">
        {items.map((item, i) => (
          <div key={i} className="flex flex-col">
            <dt className="text-sm text-[var(--muted)]">{item.label}</dt>
            <dd className="mt-1 text-sm font-medium text-[var(--ink)] break-all">
              {typeof item.value === "string" ? item.value : JSON.stringify(item.value)}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export default function EvidencePackageReadinessPage() {
  const data = useObservatoryFetch(fetchEvidencePackageReadiness);

  if (data.status === "loading") {
    return <StatePanel title="Loading" detail="Fetching evidence package readiness report..." />;
  }

  if (data.status === "error") {
    return <StatePanel title="Error" detail={data.message} />;
  }

  if (data.status === "ready" && data.data) {
    const report = data.data.report;
    const decision = report.decision;

    const isReady = decision === "READY_FOR_HUMAN_REVIEW";

    return (
      <>
        <header className="mb-8">
          <h2 className="text-3xl font-semibold text-[var(--ink)]">Evidence Package Readiness Review</h2>
          <p className="text-base text-[var(--muted)] mt-2">
            Advisory assessment of whether the evidence package is structurally ready for human review.
          </p>
        </header>

        <div className="mb-8 flex items-center gap-4">
          <span className={`rounded-full px-4 py-2 text-sm font-bold uppercase tracking-wider ${
            isReady 
              ? "bg-teal-100 text-teal-800" 
              : "bg-red-100 text-red-800"
          }`}>
            {isReady ? "Ready for Review" : "Review Blocked"}
          </span>
          <span className="text-sm text-[var(--muted)]">
            Report Hash: {report.report_hash}
          </span>
        </div>

        <div className="grid gap-6">
          <DetailSection 
            title="Readiness Decision" 
            items={[
              { label: "Package ID", value: report.package_id },
              { label: "Decision", value: decision },
              { label: "Report Hash", value: report.report_hash },
            ]}
          />

          <DetailSection 
            title="Reason Codes" 
            items={report.reason_codes.map((code: string, i: number) => ({
              label: `Reason ${i + 1}`,
              value: code,
            }))}
          />
        </div>
      </>
    );
  }

  return <StatePanel title="Error" detail="An unexpected error occurred while loading readiness report." />;
}
