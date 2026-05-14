"use client";

import { StatePanel } from "../../components/state-panel";
import { useObservatoryFetch } from "../../hooks/use-observatory-fetch";
import { fetchHumanReviewIntents } from "../../lib/backend-client";
import type { HumanReviewIntentResponse } from "../../lib/types";

function IntentRecordSection({ record }: { record: any }) {
  const intentColors: Record<string, string> = {
    "REVIEW_INTENT_APPROVE": "bg-teal-100 text-teal-800",
    "REVIEW_INTENT_REJECT": "bg-red-100 text-red-800",
    "REVIEW_INTENT_DEFER": "bg-amber-100 text-amber-800",
  };

  return (
    <section className="rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-6 shadow-soft backdrop-blur">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-[var(--ink)]">Review Record</h3>
        <span className={`rounded-full px-4 py-2 text-sm font-bold uppercase tracking-wider ${intentColors[record.review_intent] || "bg-gray-100 text-gray-800"}`}>
          {record.review_intent}
        </span>
      </div>
      
      <dl className="grid grid-cols-1 gap-y-4 sm:grid-cols-2">
        <div className="flex flex-col">
          <dt className="text-sm text-[var(--muted)]">Authorizer ID</dt>
          <dd className="mt-1 text-sm font-medium text-[var(--ink)]">{record.authorizer_id}</dd>
        </div>
        <div className="flex flex-col">
          <dt className="text-sm text-[var(--muted)]">Archive Hash</dt>
          <dd className="mt-1 text-sm font-mono text-[var(--ink)] break-all">{record.archive_hash}</dd>
        </div>
        <div className="flex flex-col">
          <dt className="text-sm text-[var(--muted)]">Record Hash</dt>
          <dd className="mt-1 text-sm font-mono text-[var(--ink)] break-all">{record.record_hash}</dd>
        </div>
        <div className="flex flex-col">
          <dt className="text-sm text-[var(--muted)]">Epoch / Sequence</dt>
          <dd className="mt-1 text-sm font-medium text-[var(--ink)]">{record.authorization_epoch} / {record.authorization_seq}</dd>
        </div>
      </dl>

      <div className="mt-6 border-t border-[var(--line)] pt-4">
        <dt className="text-sm text-[var(--muted)] mb-2">Rationale</dt>
        <dd className="text-sm text-[var(--ink)] italic bg-[var(--panel-alt)] p-4 rounded-lg border border-[var(--line)]">
          "{record.rationale}"
        </dd>
      </div>
    </section>
  );
}

export default function HumanReviewIntentPage() {
  const records = useObservatoryFetch(fetchHumanReviewIntents);

  if (records.status === "loading") {
    return <StatePanel title="Loading" detail="Fetching human review intent records..." />;
  }

  if (records.status === "error") {
    return <StatePanel title="Error" detail={records.message} />;
  }

  if (records.status === "ready" && records.data) {
    const data = records.data;

    return (
      <>
        <header className="mb-8">
          <h2 className="text-3xl font-semibold text-[var(--ink)]">Human Review Intent Archive</h2>
          <p className="text-base text-[var(--muted)] mt-2">
            Read-only record of human review intent for release governance.
          </p>
        </header>

        {data.length === 0 ? (
          <StatePanel title="No Records" detail="No human review intent records are available in the current projection." />
        ) : (
          <div className="grid gap-6">
            {data.map((record: any, i) => (
              <IntentRecordSection key={i} record={record} />
            ))}
          </div>
        )}
      </>
    );
  }

  return <StatePanel title="Error" detail="An unexpected error occurred while loading review intent records." />;
}
