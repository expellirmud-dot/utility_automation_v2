"use client";

import { StatePanel } from "../../components/state-panel";
import { useObservatoryFetch } from "../../hooks/use-observatory-fetch";
import { fetchEvidencePackage } from "../../lib/backend-client";
import type { EvidencePackageResponse } from "../../lib/types";

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

export default function EvidencePackagePage() {
  const data = useObservatoryFetch(fetchEvidencePackage);

  if (data.status === "loading") {
    return <StatePanel title="Loading" detail="Fetching governance evidence package..." />;
  }

  if (data.status === "error") {
    return <StatePanel title="Error" detail={data.message} />;
  }

  if (data.status === "ready" && data.data) {
    const pkg = data.data.package;
    const isVerified = pkg.package_status === "PACKAGE_VERIFIED";

    return (
      <>
        <header className="mb-8">
          <h2 className="text-3xl font-semibold text-[var(--ink)]">Governance Evidence Package</h2>
          <p className="text-base text-[var(--muted)] mt-2">
            Deterministic evidence bundle verifying the governance chain integrity.
          </p>
        </header>

        <div className="mb-8 flex items-center gap-4">
          <span className={`rounded-full px-4 py-2 text-sm font-bold uppercase tracking-wider ${
            isVerified 
              ? "bg-teal-100 text-teal-800" 
              : "bg-red-100 text-red-800"
          }`}>
            {isVerified ? "Verified" : "Invalid"}
          </span>
          <span className="text-sm text-[var(--muted)]">
            Version: {pkg.package_version}
          </span>
        </div>

        <div className="grid gap-6">
          <DetailSection 
            title="Package Identity" 
            items={[
              { label: "Package ID", value: pkg.package_id },
              { label: "Package Hash", value: pkg.package_hash },
              { label: "Version", value: pkg.package_version },
              { label: "Status", value: pkg.package_status },
            ]}
          />

          <DetailSection 
            title="Evidence References" 
            items={[
              { label: "Archive Hash", value: pkg.archive_hash },
              { label: "Human Record Hash", value: pkg.human_record_hash },
              { label: "Evidence Link Hash", value: pkg.evidence_link_hash },
            ]}
          />

          <DetailSection 
            title="Verification Details" 
            items={[
              { label: "Reason Codes", value: pkg.reason_codes.join(", ") },
            ]}
          />
        </div>
      </>
    );
  }

  return <StatePanel title="Error" detail="An unexpected error occurred while loading evidence package data." />;
}
