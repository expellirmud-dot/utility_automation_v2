import { NextResponse } from "next/server";

const GOVERNANCE_API_URL = process.env.GOVERNANCE_API_URL ?? "http://127.0.0.1:8000";

const MOCK_DASHBOARD_PROJECTION = {
  bucket: "dashboard_projection",
  stats: [
    {
      key: "health",
      label: "Health Score",
      value: "98.1%",
      delta: "+2.1%",
      tone: "teal",
    },
    {
      key: "incidents",
      label: "Open Incidents",
      value: "12",
      delta: "-4 today",
      tone: "orange",
    },
    {
      key: "replay",
      label: "Replay Checks",
      value: "1,264",
      delta: "100% pass",
      tone: "emerald",
    },
    {
      key: "review_time",
      label: "Avg Review Time",
      value: "4m 38s",
      delta: "-38s",
      tone: "slate",
    },
  ],
  throughput: {
    bars: [58, 72, 63, 81, 76, 88, 67, 91],
    summaries: [
      { label: "Replay pass rate", value: "100%" },
      { label: "Median queue", value: "8m" },
      { label: "Open risk", value: "3 high" },
    ],
  },
  activity: [
    {
      title: "Quorum approval recorded",
      detail: "Recovery proposal REC-219 passed review",
      time: "2 min ago",
    },
    {
      title: "Ledger replay completed",
      detail: "No causal mismatch detected in current window",
      time: "14 min ago",
    },
    {
      title: "Operator note added",
      detail: "Incident INC-1042 updated by governance lead",
      time: "28 min ago",
    },
    {
      title: "Simulation finished",
      detail: "Policy candidate generated advisory report only",
      time: "51 min ago",
    },
  ],
  incidents: [
    {
      id: "INC-1042",
      title: "Invoice provider confidence drift",
      owner: "Nara",
      status: "Reviewing",
      risk: "Medium",
      age: "18m",
    },
    {
      id: "INC-1039",
      title: "Replay checkpoint delayed",
      owner: "Anan",
      status: "Queued",
      risk: "Low",
      age: "42m",
    },
    {
      id: "INC-1031",
      title: "Policy graph conflict candidate",
      owner: "Mali",
      status: "Blocked",
      risk: "High",
      age: "1h",
    },
    {
      id: "INC-1027",
      title: "Correction workflow needs operator note",
      owner: "Krit",
      status: "Resolved",
      risk: "Low",
      age: "2h",
    },
  ],
  generated_by: "inline_mock",
  seed: 41041,
};

export async function GET() {
  try {
    const response = await fetch(`${GOVERNANCE_API_URL}/dashboard/projection`, {
      cache: "no-store",
    });

    if (!response.ok) {
      console.warn(`Dashboard projection fallback: backend returned ${response.status}`);
      return NextResponse.json(MOCK_DASHBOARD_PROJECTION);
    }

    return NextResponse.json(await response.json());
  } catch {
    return NextResponse.json(MOCK_DASHBOARD_PROJECTION);
  }
}
