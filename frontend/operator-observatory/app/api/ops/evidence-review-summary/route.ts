import { NextRequest, NextResponse } from "next/server";
import { getOpsApiBaseUrl } from "../../../../lib/backend-client";

export async function GET(request: NextRequest) {
  const baseUrl = getOpsApiBaseUrl();
  const targetUrl = `${baseUrl}/ops/api/evidence-review-summary`;

  try {
    const response = await fetch(targetUrl, {
      method: "GET",
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
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal Server Error" },
      { status: 500 }
    );
  }
}
