"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { StatePanel } from "../../components/state-panel";
import { fetchRuntimeTasks, fetchRuntimeTaskDetail, createRuntimeTask, startRuntimeTask, finishRuntimeTask } from "../../lib/backend-client";
import type {
  CreateTaskPayload,
  FinishTaskPayload,
  RuntimeTaskAction,
  RuntimeTasksResponse,
  RuntimeTaskSummary,
  StartTaskPayload,
} from "../../lib/types";

const POLL_INTERVAL_MS = 10000;
const RECENT_TASK_LIMIT = 6;

type RuntimeLoadState =
  | { status: "loading" }
  | { status: "ready"; data: RuntimeTasksResponse }
  | { status: "error"; message: string };

function formatUpdatedAt(value: Date | null): string {
  return value ? value.toLocaleTimeString() : "Not yet synced";
}

function getLifecycleProgress(task: RuntimeTaskSummary): number {
  if (task.state === "VALIDATED_COMPLETION") return 100;
  if (task.state === "EVIDENCE_VALIDATION_FAILED" || task.state === "CORRUPT_EVIDENCE") return 80;
  if (task.evidence_found) return 75;
  if (task.state === "ACTIVE" || task.state === "EXPIRED") return 50;
  if (task.contract) return 35;
  return 15;
}

function getValidationLabel(task: RuntimeTaskSummary): string {
  if (task.state === "VALIDATED_COMPLETION") return "Validated";
  if (task.state === "EVIDENCE_VALIDATION_FAILED") return "Validation failed";
  if (task.state === "CORRUPT_EVIDENCE" || task.state === "CORRUPT_CONTRACT") return "Corrupt artifact";
  if (task.evidence_found) return "Evidence present";
  return "Awaiting evidence";
}

type TimelineStepState = "complete" | "active" | "blocked" | "pending";

type TimelineStep = {
  key: string;
  label: string;
  state: TimelineStepState;
};

function getEvidenceStatus(task: RuntimeTaskSummary): string | null {
  const status = task.evidence?.status;
  return typeof status === "string" ? status.toUpperCase() : null;
}

function getTimelineSteps(task: RuntimeTaskSummary): TimelineStep[] {
  const state = task.state.toUpperCase();
  const evidenceStatus = getEvidenceStatus(task);
  const isValidated = state === "VALIDATED_COMPLETION";
  const isCorruptEvidence = state === "CORRUPT_EVIDENCE";
  const isEvidenceValidationFailed = state === "EVIDENCE_VALIDATION_FAILED";
  const isFailed = state === "EXPIRED" || state === "CORRUPT_CONTRACT" || evidenceStatus === "FAILED";
  const hasContract = Boolean(task.contract);
  const hasEvidence = task.evidence_found;

  return [
    {
      key: "created",
      label: "Created",
      state: hasContract || state !== "ISSUANCE_PENDING" ? "complete" : "active",
    },
    {
      key: "started",
      label: "Started",
      state: hasContract ? (state === "ACTIVE" && !hasEvidence ? "active" : "complete") : "pending",
    },
    {
      key: "validating",
      label: "Validating",
      state: hasEvidence && !isValidated && !isCorruptEvidence && !isEvidenceValidationFailed && !isFailed ? "active" : hasEvidence || isValidated || isCorruptEvidence || isEvidenceValidationFailed ? "complete" : "pending",
    },
    {
      key: "validated_completion",
      label: "Validated completion",
      state: isValidated ? "complete" : "pending",
    },
    {
      key: "failed",
      label: "Failed",
      state: isFailed ? "blocked" : "pending",
    },
    {
      key: "corrupt_evidence",
      label: "Corrupt evidence",
      state: isCorruptEvidence ? "blocked" : "pending",
    },
    {
      key: "evidence_validation_failed",
      label: "Evidence validation failed",
      state: isEvidenceValidationFailed ? "blocked" : "pending",
    },
  ];
}

function TimelineRail({ task, compact = false }: { task: RuntimeTaskSummary; compact?: boolean }) {
  const steps = getTimelineSteps(task);

  return (
    <div className={compact ? "space-y-2" : "space-y-3"}>
      {steps.map((step) => (
        <div key={step.key} className="flex items-center gap-3">
          <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${
            step.state === "complete" ? "bg-teal-500" :
            step.state === "active" ? "bg-blue-500" :
            step.state === "blocked" ? "bg-red-500" :
            "bg-gray-300"
          }`} />
          <span className={`${compact ? "text-[11px]" : "text-xs"} font-mono ${
            step.state === "pending" ? "text-[var(--muted)]" : "font-bold text-[var(--ink)]"
          }`}>
            {step.label}
          </span>
        </div>
      ))}
    </div>
  );
}

type ArtifactTabKey =
  | "contract"
  | "evidence"
  | "transcript"
  | "trace"
  | "report"
  | "validation"
  | "manifest"
  | "certification";

type ArtifactTab = {
  key: ArtifactTabKey;
  label: string;
  enabled: boolean;
  content: string | null;
};

function stringifyArtifact(value: unknown): string | null {
  if (!value) return null;
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function ArtifactBrowser({ task }: { task: RuntimeTaskSummary }) {
  const [activeTab, setActiveTab] = useState<ArtifactTabKey>("contract");

  const tabs: ArtifactTab[] = [
    { key: "contract", label: "Contract JSON", enabled: !!task.contract, content: stringifyArtifact(task.contract) },
    { key: "evidence", label: "Evidence Payload", enabled: !!task.evidence || !!task.artifact_contents?.evidence_json, content: task.artifact_contents?.evidence_json ?? stringifyArtifact(task.evidence) },
    { key: "transcript", label: "Transcript", enabled: !!task.reports.execution_transcript, content: task.artifact_contents?.execution_transcript ?? null },
    { key: "trace", label: "Tool Trace", enabled: !!task.reports.tool_trace, content: task.artifact_contents?.tool_trace ?? null },
    { key: "report", label: "Worker Report", enabled: !!task.reports.worker_report, content: task.artifact_contents?.worker_report ?? null },
    { key: "validation", label: "Validation Output", enabled: !!task.reports.validation_output, content: task.artifact_contents?.validation_output ?? null },
    { key: "manifest", label: "Runtime Manifest", enabled: !!task.reports.runtime_manifest, content: task.artifact_contents?.runtime_manifest ?? null },
    { key: "certification", label: "Certification Artifact", enabled: !!task.reports.certification_artifact, content: task.artifact_contents?.certification_artifact ?? null },
  ];

  const activeArtifact = tabs.find((tab) => tab.key === activeTab) ?? tabs[0];

  return (
    <div className="rounded-xl border border-[var(--line)] bg-white p-4 font-sans">
      <div className="flex gap-2 mb-3">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            disabled={!tab.enabled}
            className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
              activeTab === tab.key ? "bg-[var(--accent)] text-white" :
              tab.enabled ? "bg-gray-100 text-[var(--ink)] hover:bg-gray-200" :
              "bg-gray-50 text-[var(--muted)] cursor-not-allowed"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="h-64 overflow-auto rounded-lg border border-[var(--line)] bg-gray-50 p-4 font-mono text-[11px] text-[var(--ink)]">
        {activeArtifact.content ? <pre className="whitespace-pre-wrap">{activeArtifact.content}</pre> :
                   <p className="text-[var(--muted)]">No {activeArtifact.label.toLowerCase()} available.</p>}
      </div>
    </div>
  );
}

function Modal({
  task,
  onClose,
  syncing,
  lastUpdated,
}: {
  task: RuntimeTaskSummary | null;
  onClose: () => void;
  syncing: boolean;
  lastUpdated: Date | null;
}) {
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
            <p className="text-xs text-[var(--muted)] mt-1 font-mono">
              Inspector sync: {syncing ? "Syncing..." : formatUpdatedAt(lastUpdated)}
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
          <div className="mb-4 grid grid-cols-1 sm:grid-cols-3 gap-3 font-sans">
            <div className="rounded-xl border border-[var(--line)] bg-white p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted)]">Lifecycle</p>
              <div className="mt-3 h-2 rounded-full bg-gray-100">
                <div className="h-2 rounded-full bg-[var(--accent)]" style={{ width: `${getLifecycleProgress(task)}%` }} />
              </div>
            </div>
            <div className="rounded-xl border border-[var(--line)] bg-white p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted)]">Validation</p>
              <p className="mt-2 text-sm font-bold text-[var(--ink)]">{getValidationLabel(task)}</p>
            </div>
            <div className="rounded-xl border border-[var(--line)] bg-white p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted)]">Evidence</p>
              <p className="mt-2 text-sm font-bold text-[var(--ink)]">{task.evidence_found ? "Available" : "Pending"}</p>
            </div>
          </div>
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
          <div className="mt-4 rounded-xl border border-[var(--line)] bg-white p-4 font-sans">
            <p className="mb-3 text-[10px] font-bold uppercase tracking-wider text-[var(--muted)]">Runtime Timeline</p>
            <TimelineRail task={task} />
          </div>

          <div className="mt-6">
            <p className="mb-3 text-[10px] font-bold uppercase tracking-wider text-[var(--muted)]">Artifact Browser</p>
            <ArtifactBrowser task={task} />
          </div>
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

type TaskTemplate = {
  label: string;
  form: Partial<ActionFormState>;
};

const taskTemplates: TaskTemplate[] = [
  {
    label: "Implementation Task",
    form: {
      title: "Implementation Task",
      objective: "Implement the assigned scoped change.",
      rationale: "Complete assigned implementation work while preserving governance constraints.",
      scope: "Read assigned task scope\nInspect relevant files\nImplement minimal targeted change",
      candidateModules: "frontend/operator-observatory/app/runtime-console/page.tsx",
      tests: "tests/test_runtime_console.py\ntests/test_runtime_console_api.py\ntests/test_runtime_operator_actions.py",
      validation: "python -m pytest -q\ncd frontend/operator-observatory && npm run typecheck",
      acceptance: "Existing behavior preserved\nValidation passes\nNo unrelated changes",
    },
  },
  {
    label: "Review Task",
    form: {
      title: "Review Task",
      objective: "Review the assigned change for defects and governance risk.",
      rationale: "Provide read-first review findings before approval or follow-up work.",
      scope: "Inspect diff\nCheck governance boundaries\nReport findings with file references",
      tests: "python -m pytest -q",
      validation: "git diff --check\npython -m pytest -q",
      acceptance: "Findings are evidence-backed\nNo implementation changes unless explicitly requested",
    },
  },
  {
    label: "Certification Task",
    form: {
      title: "Certification Task",
      objective: "Run required deterministic validation and collect completion evidence.",
      rationale: "Confirm repository invariants and certification integrity after scoped work.",
      scope: "Run targeted validation\nRun full validation\nRun deterministic certifier",
      tests: "python -m pytest -q",
      validation: "python -m pytest -q\n$env:PYTHONPATH=\".\"; python src/tests/certification/deterministic_certifier.py",
      acceptance: "Validation output recorded\nCertification artifact exists\nRemaining risks documented",
    },
  },
  {
    label: "Continuity Update",
    form: {
      title: "Continuity Update",
      objective: "Update repository continuity state after completed task validation.",
      rationale: "Keep handoff and project memory aligned with the latest completed work.",
      scope: "Update current completed task\nUpdate next task\nPreserve standing invariants",
      candidateModules: "AI_HANDOFF.md\nrepo_memory/project_state.json",
      validation: "git diff -- AI_HANDOFF.md repo_memory/project_state.json",
      acceptance: "Current task and next task are accurate\nNo unrelated handoff edits",
    },
  },
  {
    label: "Documentation Update",
    form: {
      title: "Documentation Update",
      objective: "Update scoped documentation for the assigned repository change.",
      rationale: "Keep operator-facing or handoff documentation consistent with implementation.",
      scope: "Inspect current docs\nApply minimal documentation update\nVerify wording against source",
      validation: "git diff --check",
      acceptance: "Documentation matches implementation\nNo architecture drift introduced",
    },
  },
];

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
  initialForm,
}: {
  action: RuntimeTaskAction;
  onClose: () => void;
  onSubmit: (action: RuntimeTaskAction, payload: RuntimeActionPayload) => Promise<void>;
  initialForm?: ActionFormState;
}) {
  const [form, setForm] = useState<ActionFormState>(initialForm ?? emptyActionFormState);
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
  const [data, setData] = useState<RuntimeLoadState>({ status: "loading" });
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("ALL");
  const [taskSearch, setTaskSearch] = useState("");
  const [selectedTask, setSelectedTask] = useState<RuntimeTaskSummary | null>(null);
  const [inspectorLastUpdated, setInspectorLastUpdated] = useState<Date | null>(null);
  const [inspectorSyncing, setInspectorSyncing] = useState(false);
  const [actionDialog, setActionDialog] = useState<RuntimeTaskAction | null>(null);
  const [createTemplateForm, setCreateTemplateForm] = useState<ActionFormState | null>(null);

  const syncTasks = useCallback(async (background = false) => {
    if (background) {
      setIsSyncing(true);
    } else {
      setData((current) => current.status === "ready" ? current : { status: "loading" });
    }

    try {
      const nextData = await fetchRuntimeTasks();
      setData({ status: "ready", data: nextData });
      setLastUpdated(new Date());
      setSyncError(null);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Unable to read runtime task data.";
      setSyncError(message);
      setData((current) => current.status === "ready" ? current : { status: "error", message });
    } finally {
      setIsSyncing(false);
    }
  }, []);

  useEffect(() => {
    void syncTasks(false);
    const interval = window.setInterval(() => {
      void syncTasks(true);
    }, POLL_INTERVAL_MS);

    return () => window.clearInterval(interval);
  }, [syncTasks]);

  useEffect(() => {
    if (!selectedTask) return;

    let active = true;
    const syncSelectedTask = async (background = true) => {
      if (background) setInspectorSyncing(true);
      try {
        const detail = await fetchRuntimeTaskDetail(selectedTask.task_id);
        if (!active) return;
        setSelectedTask(detail.task);
        setInspectorLastUpdated(new Date());
      } catch {
        if (active) setInspectorLastUpdated(new Date());
      } finally {
        if (active) setInspectorSyncing(false);
      }
    };

    void syncSelectedTask(false);
    const interval = window.setInterval(() => {
      void syncSelectedTask(true);
    }, POLL_INTERVAL_MS);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, [selectedTask?.task_id]);

  const handleActionSubmit = async (action: RuntimeTaskAction, payload: RuntimeActionPayload) => {
    if (action === "create") {
      await createRuntimeTask(payload as CreateTaskPayload);
    } else if (action === "start") {
      await startRuntimeTask(payload as StartTaskPayload);
    } else {
      await finishRuntimeTask(payload as FinishTaskPayload);
    }

    setActionDialog(null);
    setCreateTemplateForm(null);
    await syncTasks(false);
  };

  const openCreateTask = (form?: Partial<ActionFormState>) => {
    setCreateTemplateForm(form ? { ...emptyActionFormState, ...form } : null);
    setActionDialog("create");
  };

  if (data.status === "loading") {
    return <StatePanel title="Loading" detail="Fetching deterministic runtime task matrix..." />;
  }

  if (data.status === "error") {
    return <StatePanel title="Error" detail={data.message} />;
  }

  if (data.status === "ready" && data.data) {
    const tasks = data.data.tasks;
    const normalizedSearch = taskSearch.trim().toUpperCase();
    const filteredTasks = tasks.filter((task) => {
      const matchesState = filter === "ALL" || task.state.toUpperCase() === filter.toUpperCase();
      const matchesSearch = !normalizedSearch || task.task_id.toUpperCase().includes(normalizedSearch);
      return matchesState && matchesSearch;
    });
    const recentTasks = tasks.slice(-RECENT_TASK_LIMIT).reverse();

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
            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs font-mono text-[var(--muted)]">
              <span className="rounded-lg border border-[var(--line)] bg-gray-50 px-3 py-1">
                Last updated: {formatUpdatedAt(lastUpdated)}
              </span>
              <span className="rounded-lg border border-[var(--line)] bg-gray-50 px-3 py-1">
                Auto sync: {POLL_INTERVAL_MS / 1000}s
              </span>
              {isSyncing && (
                <span className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-1 font-bold text-blue-700">
                  Syncing...
                </span>
              )}
              {syncError && (
                <span className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-1 font-bold text-amber-700">
                  Last sync failed
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => openCreateTask()} className="px-3 py-1.5 text-xs font-bold bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm">
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
            <button onClick={() => syncTasks(true)} className="px-3 py-1.5 text-xs font-bold bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm">
              Sync
            </button>
          </div>
        </header>

        <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.6fr)]">
          <section className="rounded-xl border border-[var(--line)] bg-white p-4 shadow-sm">
            <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="text-sm font-bold text-[var(--ink)]">Task History</h3>
                <p className="text-xs text-[var(--muted)]">Most recent tasks from the runtime task matrix.</p>
              </div>
              <input
                value={taskSearch}
                onChange={(event) => setTaskSearch(event.target.value)}
                placeholder="Search task id"
                className="w-full rounded-lg border border-[var(--line)] bg-gray-50 px-3 py-2 font-mono text-xs text-[var(--ink)] shadow-sm focus:border-[var(--accent)] focus:outline-none sm:w-56"
              />
            </div>
            <div className="divide-y divide-gray-100">
              {recentTasks.map((task) => (
                <button
                  key={task.task_id}
                  type="button"
                  onClick={() => setSelectedTask(task)}
                  className="flex w-full items-center justify-between gap-4 py-3 text-left"
                >
                  <span>
                    <span className="block font-mono text-sm font-bold text-[var(--ink)]">{task.task_id}</span>
                    <span className="block truncate text-xs text-[var(--muted)]">{task.summary}</span>
                  </span>
                  <span className="shrink-0 rounded-lg border border-[var(--line)] bg-gray-50 px-2 py-1 font-mono text-[10px] font-bold text-[var(--muted)]">
                    {task.state}
                  </span>
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-xl border border-[var(--line)] bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-bold text-[var(--ink)]">Timeline Focus</h3>
              <span className="font-mono text-[10px] font-bold text-[var(--muted)]">
                {filteredTasks.length} shown
              </span>
            </div>
            {filteredTasks[0] ? (
              <div>
                <div className="mb-3">
                  <p className="font-mono text-sm font-bold text-[var(--ink)]">{filteredTasks[0].task_id}</p>
                  <p className="text-xs text-[var(--muted)]">{filteredTasks[0].state}</p>
                </div>
                <TimelineRail task={filteredTasks[0]} compact />
              </div>
            ) : (
              <p className="text-sm text-[var(--muted)]">No task matches the current search and lifecycle filter.</p>
            )}
          </section>
        </div>

        <div className="mb-6 rounded-xl border border-[var(--line)] bg-gray-50 p-4">
          <div className="mb-3 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">Task Templates</span>
            <span className="text-xs font-mono text-[var(--muted)]">Prefill only. Review and submit manually.</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {taskTemplates.map((template) => (
              <button
                key={template.label}
                onClick={() => openCreateTask(template.form)}
                className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-bold text-gray-700 shadow-sm transition-colors hover:bg-gray-100"
              >
                {template.label}
              </button>
            ))}
          </div>
        </div>

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
          <StatePanel title="Empty Matrix" detail="No runtime tasks match the selected task id search and lifecycle filter." />
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

                  <div className="mb-5">
                    <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-[var(--muted)]">
                      <span>Lifecycle</span>
                      <span>{getLifecycleProgress(t)}%</span>
                    </div>
                    <div className="mt-2 h-2 rounded-full bg-gray-100">
                      <div className="h-2 rounded-full bg-[var(--accent)] transition-all" style={{ width: `${getLifecycleProgress(t)}%` }} />
                    </div>
                    <div className="mt-2 text-xs font-mono font-bold text-[var(--ink)]">
                      {getValidationLabel(t)}
                    </div>
                  </div>

                  <div className="mb-6 rounded-xl border border-gray-100 bg-gray-50 p-3">
                    <div className="mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--muted)]">
                      Timeline
                    </div>
                    <TimelineRail task={t} compact />
                  </div>

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
                    <div className="flex items-center justify-between">
                      <span className="text-[var(--muted)]">Worker Report:</span>
                      <span className={`font-bold ${t.reports.worker_report ? "text-teal-600" : "text-gray-400"}`}>
                        {t.reports.worker_report ? "✔ Present" : "✖ Missing"}
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

        <Modal
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
          syncing={inspectorSyncing}
          lastUpdated={inspectorLastUpdated}
        />
        {actionDialog && (
          <ActionModal
            action={actionDialog}
            onClose={() => setActionDialog(null)}
            onSubmit={handleActionSubmit}
            initialForm={actionDialog === "create" ? createTemplateForm ?? undefined : undefined}
          />
        )}
      </>
    );
  }

  return <StatePanel title="Error" detail="An unexpected error occurred while loading runtime task data." />;
}
