import { NextRequest, NextResponse } from "next/server";
import { startTaskPayloadSchema } from "../../../../../lib/schemas";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const payload = startTaskPayloadSchema.parse(body);

    const backendUrl = process.env.OPS_API_BASE_URL || "http://127.0.0.1:8000";
    const response = await fetch(`${backendUrl}/ops/api/runtime-tasks/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    const data = await response.json();
    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: "Invalid payload or backend error", details: error.message },
      { status: 400 }
    );
  }
}
