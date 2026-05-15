"use client";

import { StatePanel } from "../../components/state-panel";
import { useObservatoryFetch } from "../../hooks/use-observatory-fetch";
import { fetchEvidencePackageIntegrity } from "../../lib/backend-client";
import type { EvidencePackageIntegrityResponse } from "../../lib/types";

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

export default function EvidencePackageIntegrityPage() {
  const data = useObservatoryFetch(fetchEvidencePackageIntegrity);

  if (data.status === "loading") {
    return <StatePanel title="Loading" detail="Fetching evidence package integrity report..." />;
  }

  if (data.status === "error") {
    return <StatePanel title="Error" detail={data.message} />;
  }

  if (data.status === "ready" && data.data) {
    const report = data.data.report;
    const isPassed = report.passed;

    return (
      <>
        <header className="mb-8">
          <h2 className="text-3xl font-semibold text-[var(--ink)]">Evidence Package Integrity Review</h2>
          <p className="text-base text-[var(--muted)] mt-2">
            Deterministic verification of evidence package structural and hash integrity.
          </p>
        </header>

        <div className="mb-8 flex items-center gap-4">
          <span className={`rounded-full px-4 py-2 text-sm font-bold uppercase tracking-wider ${
            isPassed 
              ? "bg-teal-100 text-teal-800" 
              : "bg-red-100 text-red-800"
          }`}>
            {isPassed ? "Integrity Verified" : "Integrity Failure"}
          </span>
          <span className="text-sm text-[var(--muted)]">
            Report Hash: {report.report_hash}
          </span>
        </div>

        <div className="grid gap-6">
          <DetailSection 
            title="Report Identity" 
            items={[
              { label: "Package ID", value: report.package_id },
              { label: "Expected Version", value: report.expected_version },
              { label: "Report Hash", value: report.report_hash },
              { label: "Passed", value: report.passed.toString() },
            ]}
          />

          {report.violations.length > 0 && (
            <DetailSection 
              title="Integrity Violations" 
              items={report.violations.map((v: any, i: number) => ({
                label: `Violation ${i + 1} (${v.field})`,
                value: v.reason,
              }))}
            />
          )}


          {report.violations.length === 0 && (
            <DetailSection 
              title="Verification Result" 
              items={[
                { label: "Status", value: "No integrity violations detected. Package is safe for audit." },
              ]}
            />
          )}
        </div>
      </>
    );
  }

  return <StatePanel title="Error" detail="An unexpected error occurred while loading integrity report." />;
}
