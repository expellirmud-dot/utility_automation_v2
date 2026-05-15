import { NextResponse } from "next/server";

export async function GET() {
  const backendUrl = process.env.OPS_API_BASE_URL || "http://127.0.0.1:8000";
  const response = await fetch(`${backendUrl}/ops/api/evidence-package-readiness`, {
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    return NextResponse.json(
      { error: `Backend returned ${response.status}` },
      { status: response.status }
    );
  }

  const data = await response.json();
  return NextResponse.json(data);
}
