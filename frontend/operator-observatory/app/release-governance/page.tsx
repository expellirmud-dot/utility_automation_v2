"use client";

import { StatePanel } from "../../components/state-panel";
import { useObservatoryFetch } from "../../hooks/use-observatory-fetch";
import { fetchReleaseGovernance } from "../../lib/backend-client";
import type { ReleaseGovernanceResponse } from "../../lib/types";

function GovernanceSection({ title, data, items }: { 
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

export default function ReleaseGovernancePage() {
  const gov = useObservatoryFetch(fetchReleaseGovernance);

  if (gov.status === "loading") {
    return <StatePanel title="Loading" detail="Fetching release governance chain..." />;
  }

  if (gov.status === "error") {
    return <StatePanel title="Error" detail={gov.message} />;
  }

  if (gov.status === "ready" && gov.data) {
    const data = gov.data;
    const isPassed = data.authorization.passed;

    return (
      <>
        <header className="mb-8">
          <h2 className="text-3xl font-semibold text-[var(--ink)]">Release Governance Review</h2>
          <p className="text-base text-[var(--muted)] mt-2">
            Deterministic advisory chain for release authorization.
          </p>
        </header>

        <div className="mb-8 flex items-center gap-4">
          <span className={`rounded-full px-4 py-2 text-sm font-bold uppercase tracking-wider ${
            isPassed 
              ? "bg-teal-100 text-teal-800" 
              : "bg-red-100 text-red-800"
          }`}>
            {isPassed ? "Eligible for Review" : "Blocked"}
          </span>
          <span className="text-sm text-[var(--muted)]">
            Decision: {data.authorization.advisory_decision}
          </span>
        </div>

        <div className="grid gap-6">
          <GovernanceSection 
            title="1. Certification Evidence" 
            data={data.certification}
            items={[
              { label: "Artifact Hash", value: data.certification.artifact_hash },
              { label: "Overall Score", value: `${data.certification.overall_score}%` },
              { label: "Passed", value: data.certification.passed.toString() },
            ]}
          />

          <GovernanceSection 
            title="2. Promotion Gatekeeper" 
            data={data.gatekeeper}
            items={[
              { label: "Report Hash", value: data.gatekeeper.report_hash },
              { label: "Advisory Decision", value: data.gatekeeper.advisory_decision },
              { label: "Passed", value: data.gatekeeper.passed.toString() },
            ]}
          />

          <GovernanceSection 
            title="3. Release Authorization Advisory" 
            data={data.authorization}
            items={[
              { label: "Bundle Hash", value: data.authorization.authorization_hash },
              { label: "Final Advisory Decision", value: data.authorization.advisory_decision },
              { label: "Reason Codes", value: data.authorization.reason_codes.join(", ") },
              { label: "Passed", value: data.authorization.passed.toString() },
            ]}
          />
        </div>
      </>
    );
  }

  return <StatePanel title="Error" detail="An unexpected error occurred while loading governance data." />;
}
