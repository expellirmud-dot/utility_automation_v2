"use client";

import { useState } from "react";
import { StatePanel } from "../../components/state-panel";
import { useObservatoryFetch } from "../../hooks/use-observatory-fetch";
import { fetchRuntimeTasks, createRuntimeTask, startRuntimeTask, finishRuntimeTask } from "../../lib/backend-client";
import type { RuntimeTaskSummary } from "../../lib/types";

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

export default function RuntimeConsolePage() {
  const data = useObservatoryFetch(fetchRuntimeTasks);
  const [filter, setFilter] = useState<string>("ALL");
  const [selectedTask, setSelectedTask] = useState<RuntimeTaskSummary | null>(null);

  const handleAction = async (action: 'create' | 'start' | 'finish') => {
    try {
      const taskId = window.prompt(`Enter Task ID to ${action} (e.g. TASK-999):`);
      if (!taskId) return;

      let payload: any = { task_id: taskId };

      if (action === 'create') {
        const titleInput = window.prompt("Task Title:");
        if (!titleInput) throw new Error("Title is required");
        const objectiveInput = window.prompt("Objective:");
        if (!objectiveInput) throw new Error("Objective is required");
        const rationaleInput = window.prompt("Rationale:");
        if (!rationaleInput) throw new Error("Rationale is required");
        const scopeInput = window.prompt("Scope (comma separated):");
        if (!scopeInput) throw new Error("Scope is required");
        
        payload = {
          ...payload,
          title: titleInput.trim(),
          objective: objectiveInput.trim(),
          rationale: rationaleInput.trim(),
          scope: scopeInput.split(",").map(s => s.trim()).filter(Boolean),
          candidate_modules: [],
          tests: [],
          validation: [],
          acceptance: []
        };
        await createRuntimeTask(payload);
      } else if (action === 'start') {
        const actorId = window.prompt("Enter Actor ID:");
        if (!actorId) throw new Error("Actor ID is required");
        const expectedOutput = window.prompt("Expected Output (comma separated):");
        if (!expectedOutput) throw new Error("Expected output is required");
        
        payload = {
          ...payload,
          actor_id: actorId.trim(),
          allow_read: (window.prompt("Allow Read (comma separated):") || "").split(",").map(s => s.trim()).filter(Boolean),
          allow_write: (window.prompt("Allow Write (comma separated):") || "").split(",").map(s => s.trim()).filter(Boolean),
          expected_output: expectedOutput.split(",").map(s => s.trim()).filter(Boolean)
        };
        await startRuntimeTask(payload);
      } else if (action === 'finish') {
        const workerId = window.prompt("Enter Worker ID:");
        if (!workerId) throw new Error("Worker ID is required");
        const actualOutput = window.prompt("Actual Output (comma separated):");
        if (!actualOutput) throw new Error("Actual output is required");
        
        payload = {
          ...payload,
          worker_id: workerId.trim(),
          actual_output: actualOutput.split(",").map(s => s.trim()).filter(Boolean)
        };
        await finishRuntimeTask(payload);
      }

      alert(`${action.toUpperCase()} action successfully dispatched for ${taskId}.`);
      window.location.reload();
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    }
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
            <button onClick={() => handleAction('create')} className="px-3 py-1.5 text-xs font-bold bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm">
              Create Task
            </button>
            <button onClick={() => handleAction('start')} className="px-3 py-1.5 text-xs font-bold bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm">
              Start Task
            </button>
            <button onClick={() => handleAction('finish')} className="px-3 py-1.5 text-xs font-bold bg-[var(--accent)] text-white border border-[var(--accent)] rounded-lg hover:opacity-90 transition-opacity shadow-sm">
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
      </>
    );
  }

  return <StatePanel title="Error" detail="An unexpected error occurred while loading runtime task data." />;
}
