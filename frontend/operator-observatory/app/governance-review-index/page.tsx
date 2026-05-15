"use client";

import { StatePanel } from "../../components/state-panel";
import { useObservatoryFetch } from "../../hooks/use-observatory-fetch";
import { fetchGovernanceReviewIndex } from "../../lib/backend-client";

function IndexSection({ title, data, items }: { 
  title: string; 
  data: any; 
  items: { label: string; value: any }[] 
}) {
  return (
    <section className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-6 shadow-soft backdrop-blur">
      <h3 className="mb-4 text-lg font-semibold text-[var(--ink)]">{title}</h3>
      <dl className="grid grid-cols-1 gap-y-4 sm:grid-cols-2">
        {items.map((item, i) => (
          <div key={i} className="flex flex-col">
            <dt className="text-sm text-[var(--muted)]">{item.label}</dt>
            <dd className="mt-1 text-sm font-medium text-[var(--ink)]">
              {typeof item.value === "string" ? item.value : JSON.stringify(item.value)}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export default function GovernanceReviewIndexPage() {
  const gov = useObservatoryFetch(fetchGovernanceReviewIndex);

  if (gov.status === "loading") {
    return <StatePanel title="Loading" detail="Fetching governance review index..." />;
  }

  if (gov.status === "error") {
    return <StatePanel title="Error" detail={gov.message} />;
  }

  if (gov.status === "ready" && gov.data) {
    const index = gov.data.index;
    const isReady = index.index_status === "INDEX_READY";

    return (
      <>
        <header className="mb-8">
          <h2 className="text-3xl font-semibold text-[var(--ink)]">Governance Review Index</h2>
          <p className="text-base text-[var(--muted)] mt-2">
            Consolidated deterministic audit index for the governance review chain.
          </p>
        </header>

        <div className="mb-8 flex items-center gap-4">
          <span className={`rounded-full px-4 py-2 text-sm font-bold uppercase tracking-wider ${
            isReady 
              ? "bg-teal-100 text-teal-800" 
              : "bg-red-100 text-red-800"
          }`}>
            {isReady ? "Index Ready" : "Index Blocked"}
          </span>
          <span className="text-sm text-[var(--muted)]">
            Status: {index.index_status}
          </span>
        </div>

        <div className="grid gap-6">
          <IndexSection 
            title="1. Index Metadata" 
            data={index}
            items={[
              { label: "Index Version", value: index.index_version },
              { label: "Index Hash", value: index.index_hash },
              { label: "Index Status", value: index.index_status },
            ]}
          />

          <IndexSection 
            title="2. Governance References" 
            data={index}
            items={[
              { label: "Certification Hash", value: index.certification_artifact_hash || "MISSING" },
              { label: "Promotion Governance Hash", value: index.promotion_governance_hash || "MISSING" },
              { label: "Evidence Package Hash", value: index.evidence_package_hash || "MISSING" },
              { label: "Integrity Report Hash", value: index.integrity_report_hash || "MISSING" },
              { label: "Readiness Report Hash", value: index.readiness_report_hash || "MISSING" },
              { label: "Review Summary Hash", value: index.review_summary_hash || "MISSING" },
            ]}
          />

          <IndexSection 
            title="3. Review Status" 
            data={index}
            items={[
              { label: "Readiness Decision", value: index.readiness_decision },
              { label: "Integrity Passed", value: index.integrity_passed.toString() },
              { label: "Invariant Keys", value: index.invariant_keys.join(", ") },
              { label: "Reason Codes", value: index.reason_codes.join(", ") },
            ]}
          />
        </div>
      </>
    );
  }

  return <StatePanel title="Error" detail="An unexpected error occurred while loading the review index." />;
}
