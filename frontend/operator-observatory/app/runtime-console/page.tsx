"use client";

import { useState, type FormEvent } from "react";
import { StatePanel } from "../../components/state-panel";
import { useObservatoryFetch } from "../../hooks/use-observatory-fetch";
import { fetchRuntimeTasks, createRuntimeTask, startRuntimeTask, finishRuntimeTask } from "../../lib/backend-client";
import type {
  CreateTaskPayload,
  FinishTaskPayload,
  RuntimeTaskAction,
  RuntimeTaskSummary,
  StartTaskPayload,
} from "../../lib/types";

function Modal({ task, onClose }: { task: RuntimeTaskSummary | null; onClose: () => void }) {
  if (!task) return null;

  const [activeTab, setActiveTab] = useState<"contract" | "evidence" | "reports">("contract");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="flex flex-col w-full max-w-4xl max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-[var(--line)] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-[var(--line)] bg-gray-50/50">
          <div>
            <div className="flex items-center gap-3">
              <h3 className="text-xl font-bold text-[var(--ink)]">{task.task_id}</h3>
              <span className={`px-3 py-1 text-xs font-bold rounded-full uppercase tracking-wider ${
                task.state === "VALIDATED_COMPLETION" ? "bg-teal-100 text-teal-800" :
                task.state === "ACTIVE" ? "bg-blue-100 text-blue-800" :
                task.state === "EXPIRED" ? "bg-amber-100 text-amber-800" :
                task.state === "ISSUANCE_PENDING" ? "bg-purple-100 text-purple-800" :
                "bg-red-100 text-red-800"
              }`}>
                {task.state}
              </span>
            </div>
            <p className="text-xs text-[var(--muted)] mt-1 font-mono">
              Contract ID: {task.contract_id ?? "None"}
            </p>
          </div>
          <div
            onClick={onClose}
            role="presentation"
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer text-lg font-bold"
          >
            ✕
          </div>
        </div>

        <div className="flex border-b border-[var(--line)] bg-gray-50/30 px-6 gap-2 pt-2">
          <div
            onClick={() => setActiveTab("contract")}
            role="presentation"
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
              activeTab === "contract"
                ? "border-[var(--accent)] text-[var(--ink)] font-semibold"
                : "border-transparent text-[var(--muted)] hover:text-[var(--ink)]"
            }`}
          >
            Contract Payload
          </div>
          <div
            onClick={() => setActiveTab("evidence")}
            role="presentation"
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
              activeTab === "evidence"
                ? "border-[var(--accent)] text-[var(--ink)] font-semibold"
                : "border-transparent text-[var(--muted)] hover:text-[var(--ink)]"
            }`}
          >
            Completion Evidence
          </div>
          <div
            onClick={() => setActiveTab("reports")}
            role="presentation"
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
              activeTab === "reports"
                ? "border-[var(--accent)] text-[var(--ink)] font-semibold"
                : "border-transparent text-[var(--muted)] hover:text-[var(--ink)]"
            }`}
          >
            Report Manifests
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 font-mono text-xs text-[var(--ink)] bg-gray-900/5">
          {activeTab === "contract" && (
            <pre className="p-4 bg-gray-900 text-gray-100 rounded-xl overflow-x-auto shadow-inner font-mono text-xs">
              {task.contract ? JSON.stringify(task.contract, null, 2) : "No execution contract payload active."}
            </pre>
          )}
          {activeTab === "evidence" && (
            <pre className="p-4 bg-gray-900 text-gray-100 rounded-xl overflow-x-auto shadow-inner font-mono text-xs">
              {task.evidence ? JSON.stringify(task.evidence, null, 2) : "No completion evidence bundle active."}
            </pre>
          )}
          {activeTab === "reports" && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sans font-sans">
              {Object.entries(task.reports).map(([key, found]) => (
                <div key={key} className="flex items-center justify-between p-4 bg-white rounded-xl border border-[var(--line)] shadow-sm">
                  <span className="text-sm font-medium capitalize text-[var(--ink)] font-mono">
                    {key.replace("_", " ")}
                  </span>
                  <span className={`px-3 py-1 text-xs font-bold rounded-full ${
                    found ? "bg-teal-100 text-teal-800" : "bg-gray-100 text-gray-500"
                  }`}>
                    {found ? "Found" : "Missing"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-4 border-t border-[var(--line)] bg-gray-50 flex justify-end">
          <div
            onClick={onClose}
            role="presentation"
            className="px-5 py-2 text-sm font-semibold bg-[var(--accent)] text-white rounded-lg hover:opacity-90 shadow-sm transition-opacity cursor-pointer inline-block"
          >
            Close Inspector
          </div>
        </div>
      </div>
    </div>
  );
}

type RuntimeActionPayload = CreateTaskPayload | StartTaskPayload | FinishTaskPayload;

type ActionFormState = {
  taskId: string;
  title: string;
  objective: string;
  rationale: string;
  scope: string;
  candidateModules: string;
  tests: string;
  validation: string;
  acceptance: string;
  nextTask: string;
  outputFile: string;
  actorId: string;
  requestFile: string;
  allowRead: string;
  allowWrite: string;
  expectedOutput: string;
  workerId: string;
  actualOutput: string;
};

const emptyActionFormState: ActionFormState = {
  taskId: "",
  title: "",
  objective: "",
  rationale: "",
  scope: "",
  candidateModules: "",
  tests: "",
  validation: "",
  acceptance: "",
  nextTask: "",
  outputFile: "",
  actorId: "",
  requestFile: "",
  allowRead: "",
  allowWrite: "",
  expectedOutput: "",
  workerId: "",
  actualOutput: "",
};

function parseListInput(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function requireText(value: string, label: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error(`${label} is required.`);
  }
  return trimmed;
}

function requireList(value: string, label: string): string[] {
  const items = parseListInput(value);
  if (items.length === 0) {
    throw new Error(`${label} requires at least one value.`);
  }
  return items;
}

function buildActionPayload(action: RuntimeTaskAction, form: ActionFormState): RuntimeActionPayload {
  const task_id = requireText(form.taskId, "Task ID");

  if (action === "create") {
    return {
      task_id,
      title: requireText(form.title, "Title"),
      objective: requireText(form.objective, "Objective"),
      rationale: requireText(form.rationale, "Rationale"),
      scope: requireList(form.scope, "Scope"),
      candidate_modules: parseListInput(form.candidateModules),
      tests: parseListInput(form.tests),
      validation: parseListInput(form.validation),
      acceptance: parseListInput(form.acceptance),
      ...(form.nextTask.trim() ? { next_task: form.nextTask.trim() } : {}),
      ...(form.outputFile.trim() ? { output_file: form.outputFile.trim() } : {}),
    };
  }

  if (action === "start") {
    return {
      task_id,
      actor_id: requireText(form.actorId, "Actor ID"),
      ...(form.requestFile.trim() ? { request_file: form.requestFile.trim() } : {}),
      scope: [],
      candidate_modules: [],
      tests: [],
      validation: [],
      acceptance: [],
      allow_read: parseListInput(form.allowRead),
      allow_write: parseListInput(form.allowWrite),
      expected_output: requireList(form.expectedOutput, "Expected output"),
      duration_mins: 60,
    };
  }

  return {
    task_id,
    worker_id: requireText(form.workerId, "Worker ID"),
    actual_output: requireList(form.actualOutput, "Actual output"),
  };
}

function ActionField({
  label,
  value,
  onChange,
  required = false,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className="block text-xs font-bold uppercase tracking-wider text-[var(--muted)] mb-2">
        {label}{required ? " *" : ""}
      </span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-[var(--line)] bg-white px-3 py-2 text-sm text-[var(--ink)] shadow-sm focus:border-[var(--accent)] focus:outline-none"
      />
    </label>
  );
}

function ActionTextArea({
  label,
  value,
  onChange,
  required = false,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className="block text-xs font-bold uppercase tracking-wider text-[var(--muted)] mb-2">
        {label}{required ? " *" : ""}
      </span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        rows={3}
        className="w-full resize-y rounded-lg border border-[var(--line)] bg-white px-3 py-2 text-sm text-[var(--ink)] shadow-sm focus:border-[var(--accent)] focus:outline-none"
      />
    </label>
  );
}

function ActionModal({
  action,
  onClose,
  onSubmit,
}: {
  action: RuntimeTaskAction;
  onClose: () => void;
  onSubmit: (action: RuntimeTaskAction, payload: RuntimeActionPayload) => Promise<void>;
}) {
  const [form, setForm] = useState<ActionFormState>(emptyActionFormState);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const setField = (field: keyof ActionFormState, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const submitAction = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await onSubmit(action, buildActionPayload(action, form));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Action failed closed.");
      setSubmitting(false);
    }
  };

  const title = action === "create" ? "Create Runtime Task" : action === "start" ? "Start Runtime Task" : "Finish Runtime Task";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <form onSubmit={submitAction} className="flex max-h-[88vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-[var(--line)] bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-[var(--line)] bg-gray-50/70 p-5">
          <div>
            <h3 className="text-xl font-bold text-[var(--ink)]">{title}</h3>
            <p className="mt-1 text-xs font-mono text-[var(--muted)]">Controlled operator input. Invalid payloads are not dispatched.</p>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg px-3 py-2 text-sm font-bold text-gray-500 hover:bg-gray-100 hover:text-gray-700">
            X
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto p-5">
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">
              {error}
            </div>
          )}

          <ActionField
            label="Task ID"
            value={form.taskId}
            onChange={(value) => setField("taskId", value)}
            required
            placeholder="TASK-089"
          />

          {action === "create" && (
            <>
              <ActionField label="Title" value={form.title} onChange={(value) => setField("title", value)} required />
              <ActionTextArea label="Objective" value={form.objective} onChange={(value) => setField("objective", value)} required />
              <ActionTextArea label="Rationale" value={form.rationale} onChange={(value) => setField("rationale", value)} required />
              <ActionTextArea label="Scope" value={form.scope} onChange={(value) => setField("scope", value)} required placeholder="One item per line or comma separated" />
              <ActionTextArea label="Candidate modules" value={form.candidateModules} onChange={(value) => setField("candidateModules", value)} placeholder="Optional, one item per line or comma separated" />
              <ActionTextArea label="Tests" value={form.tests} onChange={(value) => setField("tests", value)} placeholder="Optional, one item per line or comma separated" />
              <ActionTextArea label="Validation" value={form.validation} onChange={(value) => setField("validation", value)} placeholder="Optional, one item per line or comma separated" />
              <ActionTextArea label="Acceptance" value={form.acceptance} onChange={(value) => setField("acceptance", value)} placeholder="Optional, one item per line or comma separated" />
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <ActionField label="Next task" value={form.nextTask} onChange={(value) => setField("nextTask", value)} placeholder="Optional" />
                <ActionField label="Output file" value={form.outputFile} onChange={(value) => setField("outputFile", value)} placeholder="Optional" />
              </div>
            </>
          )}

          {action === "start" && (
            <>
              <ActionField label="Actor ID" value={form.actorId} onChange={(value) => setField("actorId", value)} required />
              <ActionField label="Request file" value={form.requestFile} onChange={(value) => setField("requestFile", value)} placeholder="Optional" />
              <ActionTextArea label="Allow read" value={form.allowRead} onChange={(value) => setField("allowRead", value)} placeholder="Optional, one item per line or comma separated" />
              <ActionTextArea label="Allow write" value={form.allowWrite} onChange={(value) => setField("allowWrite", value)} placeholder="Optional, one item per line or comma separated" />
              <ActionTextArea label="Expected output" value={form.expectedOutput} onChange={(value) => setField("expectedOutput", value)} required placeholder="One item per line or comma separated" />
            </>
          )}

          {action === "finish" && (
            <>
              <ActionField label="Worker ID" value={form.workerId} onChange={(value) => setField("workerId", value)} required />
              <ActionTextArea label="Actual output" value={form.actualOutput} onChange={(value) => setField("actualOutput", value)} required placeholder="One item per line or comma separated" />
            </>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 border-t border-[var(--line)] bg-gray-50 p-4">
          <button type="button" onClick={onClose} className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50">
            Cancel
          </button>
          <button type="submit" disabled={submitting} className="rounded-lg border border-[var(--accent)] bg-[var(--accent)] px-4 py-2 text-sm font-bold text-white shadow-sm hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60">
            {submitting ? "Dispatching..." : title}
          </button>
        </div>
      </form>
    </div>
  );
}

export default function RuntimeConsolePage() {
  const data = useObservatoryFetch(fetchRuntimeTasks);
  const [filter, setFilter] = useState<string>("ALL");
  const [selectedTask, setSelectedTask] = useState<RuntimeTaskSummary | null>(null);
  const [actionDialog, setActionDialog] = useState<RuntimeTaskAction | null>(null);

  const handleActionSubmit = async (action: RuntimeTaskAction, payload: RuntimeActionPayload) => {
    if (action === "create") {
      await createRuntimeTask(payload as CreateTaskPayload);
    } else if (action === "start") {
      await startRuntimeTask(payload as StartTaskPayload);
    } else {
      await finishRuntimeTask(payload as FinishTaskPayload);
    }

    window.location.reload();
  };

  if (data.status === "loading") {
    return <StatePanel title="Loading" detail="Fetching deterministic runtime task matrix..." />;
  }

  if (data.status === "error") {
    return <StatePanel title="Error" detail={data.message} />;
  }

  if (data.status === "ready" && data.data) {
    const tasks = data.data.tasks;
    const filteredTasks = filter === "ALL" ? tasks : tasks.filter(t => t.state.toUpperCase() === filter.toUpperCase());

    const statesCount = tasks.reduce((acc, t) => {
      acc[t.state] = (acc[t.state] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return (
      <>
        <header className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-3xl font-semibold text-[var(--ink)]">Runtime Operator Console</h2>
            <p className="text-base text-[var(--muted)] mt-2">
              Deterministic read-only inspection of active and completed AI runtime execution contracts, completion evidence, and audit trails.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setActionDialog("create")} className="px-3 py-1.5 text-xs font-bold bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm">
              Create Task
            </button>
            <button onClick={() => setActionDialog("start")} className="px-3 py-1.5 text-xs font-bold bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm">
              Start Task
            </button>
            <button onClick={() => setActionDialog("finish")} className="px-3 py-1.5 text-xs font-bold bg-[var(--accent)] text-white border border-[var(--accent)] rounded-lg hover:opacity-90 transition-opacity shadow-sm">
              Finish Task
            </button>
            <div className="flex items-center gap-2 bg-gray-50 p-2 rounded-xl border border-[var(--line)] shadow-sm ml-2">
              <span className="text-xs font-mono font-bold text-[var(--muted)] px-2">MATRIX:</span>
              <span className="bg-[var(--accent)] text-white text-xs font-bold px-3 py-1 rounded-lg shadow-sm">
                {tasks.length} Total
              </span>
            </div>
          </div>
        </header>

        <div className="mb-8 flex flex-wrap gap-2 items-center pb-4 border-b border-[var(--line)]">
          <span className="text-xs font-bold text-[var(--muted)] tracking-wider uppercase mr-2 font-mono">Filter State:</span>
          <div
            onClick={() => setFilter("ALL")}
            role="presentation"
            className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all cursor-pointer inline-block ${
              filter === "ALL"
                ? "bg-[var(--ink)] text-white shadow-sm"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            All ({tasks.length})
          </div>
          {Object.entries(statesCount).map(([st, count]) => (
            <div
              key={st}
              onClick={() => setFilter(st)}
              role="presentation"
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all cursor-pointer inline-block ${
                filter === st
                  ? "bg-[var(--accent)] text-white shadow-sm"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {st} ({count})
            </div>
          ))}
        </div>

        {filteredTasks.length === 0 ? (
          <StatePanel title="Empty Matrix" detail="No runtime tasks match the selected state filter." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTasks.map((t) => {
              const isVal = t.state === "VALIDATED_COMPLETION";
              const isAct = t.state === "ACTIVE";
              const isExp = t.state === "EXPIRED";
              const isPend = t.state === "ISSUANCE_PENDING";

              return (
                <div key={t.task_id} className="flex flex-col bg-white rounded-2xl border border-[var(--line)] p-6 shadow-soft hover:shadow-md transition-shadow relative overflow-hidden group">
                  <div className="absolute top-0 left-0 right-0 h-1 bg-[var(--accent)] opacity-0 group-hover:opacity-100 transition-opacity" />
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div>
                      <h3 className="text-lg font-bold font-mono text-[var(--ink)]">{t.task_id}</h3>
                      <p className="text-xs font-mono text-[var(--muted)] mt-1 truncate max-w-[180px]">
                        {t.contract_id ? `ID: ${t.contract_id.substring(0, 12)}...` : "No Contract"}
                      </p>
                    </div>
                    <span className={`px-2.5 py-1 text-xs font-bold rounded-full uppercase tracking-wider font-mono shadow-sm ${
                      isVal ? "bg-teal-100 text-teal-800" :
                      isAct ? "bg-blue-100 text-blue-800" :
                      isExp ? "bg-amber-100 text-amber-800" :
                      isPend ? "bg-purple-100 text-purple-800" :
                      "bg-red-100 text-red-800"
                    }`}>
                      {t.state}
                    </span>
                  </div>

                  <p className="text-sm text-[var(--ink)] mb-6 flex-1 line-clamp-2 leading-relaxed">
                    {t.summary}
                  </p>

                  <div className="space-y-3 mb-6 pt-4 border-t border-gray-100 font-mono text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-[var(--muted)]">Evidence:</span>
                      <span className={`font-bold ${t.reports.evidence_json ? "text-teal-600" : "text-gray-400"}`}>
                        {t.reports.evidence_json ? "✔ Present" : "✖ Missing"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[var(--muted)]">Transcript:</span>
                      <span className={`font-bold ${t.reports.execution_transcript ? "text-teal-600" : "text-gray-400"}`}>
                        {t.reports.execution_transcript ? "✔ Present" : "✖ Missing"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[var(--muted)]">Tool Trace:</span>
                      <span className={`font-bold ${t.reports.tool_trace ? "text-teal-600" : "text-gray-400"}`}>
                        {t.reports.tool_trace ? "✔ Present" : "✖ Missing"}
                      </span>
                    </div>
                  </div>

                  <div
                    onClick={() => setSelectedTask(t)}
                    role="presentation"
                    className="w-full py-2.5 px-4 bg-gray-50 hover:bg-[var(--accent)] hover:text-white text-[var(--ink)] font-semibold text-xs rounded-xl border border-[var(--line)] shadow-sm transition-all text-center flex items-center justify-center gap-2 cursor-pointer"
                  >
                    <span>Inspect Payload</span>
                    <span>→</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <Modal task={selectedTask} onClose={() => setSelectedTask(null)} />
        {actionDialog && (
          <ActionModal
            action={actionDialog}
            onClose={() => setActionDialog(null)}
            onSubmit={handleActionSubmit}
          />
        )}
      </>
    );
  }

  return <StatePanel title="Error" detail="An unexpected error occurred while loading runtime task data." />;
}
