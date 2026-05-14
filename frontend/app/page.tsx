"use client";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bell,
  CheckCircle2,
  Clock3,
  DatabaseZap,
  FileClock,
  Home,
  Loader2,
  Menu,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { StatusPill } from "@/components/ui/status-pill";
import { cn } from "@/lib/utils";

type ViewState = "ready" | "loading" | "empty" | "error";
type StatusTone = "success" | "warning" | "danger" | "neutral";
type StatKey = "health" | "incidents" | "replay" | "review_time";

type StatItem = {
  key: StatKey;
  label: string;
  value: string;
  delta: string;
  tone: "teal" | "orange" | "emerald" | "slate";
};

type ActivityRecord = {
  title: string;
  detail: string;
  time: string;
};

type IncidentRow = {
  id: string;
  title: string;
  owner: string;
  status: string;
  risk: string;
  age: string;
};

type DashboardProjection = {
  bucket: string;
  stats: StatItem[];
  throughput: {
    bars: number[];
    summaries: Array<{ label: string; value: string }>;
  };
  activity: ActivityRecord[];
  incidents: IncidentRow[];
  generated_by: string;
  seed: number;
};

const navItems = [
  { label: "Overview", icon: Home, active: true },
  { label: "Ledger", icon: DatabaseZap },
  { label: "Incidents", icon: AlertTriangle },
  { label: "Reports", icon: FileClock },
  { label: "Operators", icon: Users },
];

const statIconMap = {
  health: ShieldCheck,
  incidents: AlertTriangle,
  replay: CheckCircle2,
  review_time: Clock3,
};

const statToneClass = {
  teal: "text-[#0f7c86]",
  orange: "text-orange-600",
  emerald: "text-emerald-600",
  slate: "text-slate-700",
};

export default function DashboardPage() {
  const [viewState, setViewState] = useState<ViewState>("loading");
  const [projection, setProjection] = useState<DashboardProjection | null>(null);

  const loadProjection = useCallback(async () => {
    setViewState("loading");
    try {
      const response = await fetch("/api/dashboard/projection", { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`Dashboard projection request failed: ${response.status}`);
      }

      const payload = (await response.json()) as DashboardProjection;
      setProjection(payload);

      const isEmpty =
        payload.stats.length === 0 &&
        payload.throughput.bars.length === 0 &&
        payload.activity.length === 0 &&
        payload.incidents.length === 0;
      setViewState(isEmpty ? "empty" : "ready");
    } catch {
      setProjection(null);
      setViewState("error");
    }
  }, []);

  useEffect(() => {
    void loadProjection();
  }, [loadProjection]);

  const tableRows = useMemo<IncidentRow[]>(() => {
    if (!projection || viewState === "empty") {
      return [];
    }

    return projection.incidents;
  }, [projection, viewState]);

  return (
    <main className="min-h-screen overflow-x-hidden p-3 text-slate-950 sm:p-5 lg:p-6">
      <div className="mx-auto grid max-w-[1480px] min-w-0 gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
        <Sidebar />

        <section className="min-w-0 space-y-4">
          <Topbar viewState={viewState} onRefresh={loadProjection} />

          {viewState === "error" ? (
            <ErrorState onReset={loadProjection} />
          ) : (
            <>
              <StatsGrid state={viewState} stats={projection?.stats ?? []} />

              <div className="grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
                <AnalyticsPanel state={viewState} throughput={projection?.throughput} />
                <ActivityPanel state={viewState} activity={projection?.activity ?? []} />
              </div>

              <IncidentTable rows={tableRows} state={viewState} />
            </>
          )}
        </section>
      </div>
    </main>
  );
}

function Sidebar() {
  return (
    <aside className="glass-surface min-w-0 overflow-hidden rounded-2xl p-4 lg:sticky lg:top-6 lg:h-[calc(100vh-3rem)]">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="grid size-11 place-items-center rounded-2xl bg-[#0f7c86] text-white shadow-[0_14px_30px_rgba(15,124,134,0.28)]">
            <ShieldCheck size={22} strokeWidth={2.2} />
          </div>
          <div>
            <p className="text-sm font-bold text-slate-950">GovOps</p>
            <p className="text-xs font-medium text-slate-500">Automation Console</p>
          </div>
        </div>
        <button
          aria-label="Open navigation"
          className="grid size-10 place-items-center rounded-2xl text-slate-500 hover:bg-white lg:hidden"
        >
          <Menu size={20} />
        </button>
      </div>

      <nav className="mt-6 grid max-w-full min-w-0 grid-cols-2 gap-2 sm:grid-cols-5 lg:block lg:space-y-1">
        {navItems.map((item) => (
          <a
            href="#"
            key={item.label}
            className={cn(
              "motion-safe group flex min-w-0 items-center gap-3 rounded-2xl px-3.5 py-3 text-sm font-semibold text-slate-500 hover:bg-white/80 hover:text-slate-950 hover:shadow-sm",
              item.active && "bg-white text-[#0f7c86] shadow-sm ring-1 ring-slate-200/70",
            )}
          >
            <item.icon
              size={18}
              strokeWidth={2}
              className={cn("text-slate-400 group-hover:text-[#0f7c86]", item.active && "text-[#0f7c86]")}
            />
            <span className="truncate">{item.label}</span>
          </a>
        ))}
      </nav>

      <div className="mt-6 rounded-2xl border border-[#c7e8ea] bg-[#e5f6f7]/70 p-4">
        <div className="flex items-center gap-2 text-sm font-bold text-[#0d6972]">
          <Sparkles size={17} />
          Advisory Mode
        </div>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          AI suggestions remain read-only until quorum approval is recorded.
        </p>
      </div>
    </aside>
  );
}

function Topbar({
  viewState,
  onRefresh,
}: {
  viewState: ViewState;
  onRefresh: () => void;
}) {
  return (
    <header className="glass-surface min-w-0 overflow-hidden rounded-2xl p-4 sm:p-5">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <h1 className="text-2xl font-bold leading-tight tracking-normal text-slate-950 sm:text-3xl">
            Governance Dashboard
          </h1>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500">
            Monitor incident review, replay health, and advisory recovery signals from one read-only operations surface.
          </p>
        </div>

        <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-center">
          <label className="relative min-w-0 sm:w-72">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
            <input
              className="h-11 w-full rounded-2xl border border-slate-200 bg-white/82 pl-10 pr-3 text-sm font-medium text-slate-700 outline-none motion-safe placeholder:text-slate-400 focus:border-[#0f7c86] focus:ring-4 focus:ring-[#0f7c86]/10"
              placeholder="Search incidents"
            />
          </label>
          <button
            aria-label="Notifications"
            className="grid size-11 place-items-center rounded-2xl border border-slate-200 bg-white/82 text-slate-500 motion-safe hover:border-[#c7e8ea] hover:text-[#0f7c86] hover:shadow-sm"
          >
            <Bell size={18} />
          </button>
          <Button onClick={onRefresh} disabled={viewState === "loading"}>
            <RefreshCw size={17} />
            Refresh View
          </Button>
        </div>
      </div>
    </header>
  );
}

function StatsGrid({ state, stats }: { state: ViewState; stats: StatItem[] }) {
  if (state === "loading") {
    return (
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Status summary loading">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index} className="min-h-36">
            <div className="space-y-4">
              <div className="skeleton h-10 w-10 rounded-2xl" />
              <div className="skeleton h-4 w-24 rounded-full" />
              <div className="skeleton h-8 w-32 rounded-full" />
            </div>
          </Card>
        ))}
      </section>
    );
  }

  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Status summary">
      {stats.map((card) => (
        <Card key={card.label} className="min-h-36">
          <div className="flex items-start justify-between gap-3">
            <div className="grid size-11 place-items-center rounded-2xl bg-white text-slate-600 ring-1 ring-slate-200/80">
              <StatIcon item={card} />
            </div>
            <span className="rounded-full bg-white/86 px-2.5 py-1 text-xs font-bold text-[#0f7c86] ring-1 ring-[#c7e8ea]">
              {card.delta}
            </span>
          </div>
          <p className="mt-5 text-sm font-semibold text-slate-500">{card.label}</p>
          <p className="mt-2 text-3xl font-bold tracking-normal text-slate-950">{card.value}</p>
        </Card>
      ))}
    </section>
  );
}

function StatIcon({ item }: { item: StatItem }) {
  const Icon = statIconMap[item.key];
  return <Icon className={statToneClass[item.tone]} size={20} />;
}

function AnalyticsPanel({
  state,
  throughput,
}: {
  state: ViewState;
  throughput?: DashboardProjection["throughput"];
}) {
  const bars = throughput?.bars ?? [];
  const summaries = throughput?.summaries ?? [];

  return (
    <Card className="min-h-[360px]">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-950">Review Throughput</h2>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            Completed reviews and deterministic replay checks across the latest window.
          </p>
        </div>
        <Button variant="soft">
          <BarChart3 size={17} />
          Export
        </Button>
      </div>

      <div className="mt-8 flex h-52 items-end gap-3 rounded-2xl border border-slate-200/80 bg-white/70 p-4">
        {state === "loading"
          ? Array.from({ length: 8 }).map((_, index) => (
              <div key={index} className="skeleton flex-1 rounded-xl" style={{ height: `${42 + index * 5}%` }} />
            ))
          : bars.map((height, index) => (
              <div
                key={index}
                className="group flex flex-1 items-end rounded-xl bg-[#e5f6f7] p-1 motion-safe hover:bg-[#d4eff1]"
                style={{ height: `${height}%` }}
              >
                <div className="h-full w-full rounded-lg bg-[#0f7c86] shadow-[0_8px_18px_rgba(15,124,134,0.18)] group-hover:bg-[#0c6871]" />
              </div>
            ))}
      </div>
      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        {state === "loading" ? Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="rounded-2xl bg-white/72 p-4 ring-1 ring-slate-200/70">
            <p className="text-xs font-bold uppercase text-slate-400">
              Loading
            </p>
            <p className="mt-2 text-lg font-bold text-slate-950">
              --
            </p>
          </div>
        )) : summaries.map((summary) => (
          <div key={summary.label} className="rounded-2xl bg-white/72 p-4 ring-1 ring-slate-200/70">
            <p className="text-xs font-bold uppercase text-slate-400">{summary.label}</p>
            <p className="mt-2 text-lg font-bold text-slate-950">{summary.value}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function ActivityPanel({ state, activity }: { state: ViewState; activity: ActivityRecord[] }) {
  return (
    <Card className="min-h-[360px]">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-950">Recent Activity</h2>
          <p className="mt-1 text-sm text-slate-500">Latest operator-visible events.</p>
        </div>
        <Activity className="text-[#0f7c86]" size={21} />
      </div>

      <div className="mt-6 space-y-4">
        {state === "loading"
          ? Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="flex gap-3">
                <div className="skeleton size-9 rounded-full" />
                <div className="flex-1 space-y-2">
                  <div className="skeleton h-4 w-2/3 rounded-full" />
                  <div className="skeleton h-3 w-full rounded-full" />
                </div>
              </div>
            ))
          : activity.map((item) => (
              <article key={item.title} className="flex gap-3 rounded-2xl p-2 motion-safe hover:bg-white/72">
                <div className="mt-1 grid size-9 shrink-0 place-items-center rounded-full bg-[#e5f6f7] text-[#0f7c86]">
                  <CheckCircle2 size={17} />
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-bold text-slate-900">{item.title}</h3>
                  <p className="mt-1 text-sm leading-5 text-slate-500">{item.detail}</p>
                  <p className="mt-1 text-xs font-semibold text-slate-400">{item.time}</p>
                </div>
              </article>
            ))}
      </div>
    </Card>
  );
}

function IncidentTable({ rows, state }: { rows: IncidentRow[]; state: ViewState }) {
  return (
    <Card className="overflow-hidden p-0">
      <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-950">Incident Queue</h2>
          <p className="mt-1 text-sm text-slate-500">Operator review list with risk and status indicators.</p>
        </div>
      </div>

      {state === "empty" ? (
        <EmptyState />
      ) : (
        <div className="scrollbar-thin overflow-x-auto">
          <table className="w-full min-w-[760px] border-collapse">
            <thead>
              <tr className="border-y border-slate-200/80 bg-white/62 text-left text-xs font-bold uppercase text-slate-400">
                <th className="px-5 py-3">ID</th>
                <th className="px-5 py-3">Title</th>
                <th className="px-5 py-3">Owner</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Risk</th>
                <th className="px-5 py-3">Age</th>
              </tr>
            </thead>
            <tbody>
              {state === "loading"
                ? Array.from({ length: 4 }).map((_, index) => (
                    <tr key={index} className="border-b border-slate-200/70">
                      {Array.from({ length: 6 }).map((__, cellIndex) => (
                        <td key={cellIndex} className="px-5 py-4">
                          <div className="skeleton h-4 rounded-full" />
                        </td>
                      ))}
                    </tr>
                  ))
                : rows.map((row) => (
                    <tr
                      key={row.id}
                      className="border-b border-slate-200/70 text-sm font-medium text-slate-600 motion-safe hover:bg-white/78"
                    >
                      <td className="px-5 py-4 font-bold text-[#0f7c86]">{row.id}</td>
                      <td className="px-5 py-4 text-slate-900">{row.title}</td>
                      <td className="px-5 py-4">{row.owner}</td>
                      <td className="px-5 py-4">
                        <StatusPill tone={statusTone(row.status)}>{row.status}</StatusPill>
                      </td>
                      <td className="px-5 py-4">{row.risk}</td>
                      <td className="px-5 py-4">{row.age}</td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

function EmptyState() {
  return (
    <div className="grid min-h-72 place-items-center border-t border-slate-200/80 px-5 py-12 text-center">
      <div>
        <div className="mx-auto grid size-14 place-items-center rounded-2xl bg-[#e5f6f7] text-[#0f7c86]">
          <CheckCircle2 size={24} />
        </div>
        <h3 className="mt-4 text-lg font-bold text-slate-950">No incidents waiting</h3>
        <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
          The queue is clear. New operator review items will appear here when the ledger projection publishes them.
        </p>
      </div>
    </div>
  );
}

function ErrorState({ onReset }: { onReset: () => void }) {
  return (
    <Card className="grid min-h-[calc(100vh-12rem)] place-items-center text-center">
      <div>
        <div className="mx-auto grid size-16 place-items-center rounded-2xl bg-orange-50 text-orange-700 ring-1 ring-orange-200">
          <XCircle size={28} />
        </div>
        <h2 className="mt-5 text-2xl font-bold text-slate-950">Dashboard data unavailable</h2>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">
          The UI kept the shell available, but the current data projection failed to load. Retry keeps the operator inside the same workflow.
        </p>
        <Button className="mt-6" onClick={onReset}>
          <Loader2 size={17} />
          Retry
        </Button>
      </div>
    </Card>
  );
}

function statusTone(status: string): StatusTone {
  if (status === "Resolved") {
    return "success";
  }
  if (status === "Blocked") {
    return "danger";
  }
  if (status === "Reviewing") {
    return "warning";
  }
  return "neutral";
}
