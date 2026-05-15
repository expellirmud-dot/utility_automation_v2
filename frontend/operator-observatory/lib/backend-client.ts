import { z } from "zod";
import {
  domainPanelsResponseSchema,
  overviewResponseSchema,
  projectionsResponseSchema,
  routeGovernanceResponseSchema,
  releaseGovernanceResponseSchema,
  evidencePackageResponseSchema,
  evidencePackageIntegrityResponseSchema,
  evidencePackageReadinessResponseSchema,
  evidenceReviewSummaryResponseSchema,
  governanceReviewIndexResponseSchema,
  surfacesResponseSchema,
  humanReviewIntentResponseSchema,
} from "./schemas";


import type { ObservatoryData } from "./types";

const DEFAULT_OPS_API_BASE_URL = "http://127.0.0.1:8000";

const endpointSchemas = {
  overview: {
    path: "/api/ops/overview",
    schema: overviewResponseSchema,
  },
  projections: {
    path: "/api/ops/projections",
    schema: projectionsResponseSchema,
  },
  surfaces: {
    path: "/api/ops/surfaces",
    schema: surfacesResponseSchema,
  },
  routeGovernance: {
    path: "/api/ops/route-governance",
    schema: routeGovernanceResponseSchema,
  },
  releaseGovernance: {
    path: "/api/ops/release-governance",
    schema: releaseGovernanceResponseSchema,
  },
  evidencePackage: {
    path: "/api/ops/evidence-package",
    schema: evidencePackageResponseSchema,
  },
  evidencePackageIntegrity: {
    path: "/api/ops/evidence-package-integrity",
    schema: evidencePackageIntegrityResponseSchema,
  },
  evidencePackageReadiness: {
    path: "/api/ops/evidence-package-readiness",
    schema: evidencePackageReadinessResponseSchema,
  },
  evidenceReviewSummary: {
    path: "/api/ops/evidence-review-summary",
    schema: evidenceReviewSummaryResponseSchema,
  },
  governanceReviewIndex: {
    path: "/api/ops/governance-review-index",
    schema: governanceReviewIndexResponseSchema,
  },
  humanReviewIntent: {
    path: "/api/ops/human-review-intent",


    schema: humanReviewIntentResponseSchema,
  },
  domainPanels: {
    path: "/api/ops/panels",
    schema: domainPanelsResponseSchema,
  },
} as const;

type EndpointKey = keyof typeof endpointSchemas;

export function getOpsApiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_OPS_API_BASE_URL?.replace(/\/+$/, "") ??
    DEFAULT_OPS_API_BASE_URL
  );
}

async function fetchValidated<K extends EndpointKey>(
  key: K,
): Promise<z.infer<(typeof endpointSchemas)[K]["schema"]>> {
  const endpoint = endpointSchemas[key];
  const response = await fetch(endpoint.path, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`${endpoint.path} returned ${response.status}`);
  }

  return endpoint.schema.parse(await response.json());
}

export async function fetchOverview() {
  return fetchValidated("overview");
}

export async function fetchProjections() {
  return fetchValidated("projections");
}

export async function fetchSurfaces() {
  return fetchValidated("surfaces");
}

export async function fetchRouteGovernance() {
  return fetchValidated("routeGovernance");
}

export async function fetchReleaseGovernance() {
  return fetchValidated("releaseGovernance");
}

export async function fetchEvidencePackage() {
  return fetchValidated("evidencePackage");
}

export async function fetchEvidencePackageIntegrity() {
  return fetchValidated("evidencePackageIntegrity");
}

export async function fetchEvidencePackageReadiness() {
  return fetchValidated("evidencePackageReadiness");
}

export async function fetchEvidenceReviewSummary() {
  return fetchValidated("evidenceReviewSummary");
}

export async function fetchGovernanceReviewIndex() {
  return fetchValidated("governanceReviewIndex");
}

export async function fetchHumanReviewIntents() {


  return fetchValidated("humanReviewIntent");
}

export async function fetchDomainPanels() {
  return fetchValidated("domainPanels");
}

export async function fetchObservatoryData(): Promise<ObservatoryData> {
  const [overview, projections, surfaces, routeGovernance, domainPanels] =
    await Promise.all([
      fetchOverview(),
      fetchProjections(),
      fetchSurfaces(),
      fetchRouteGovernance(),
      fetchDomainPanels(),
    ]);

  return {
    overview,
    projections,
    surfaces,
    routeGovernance,
    domainPanels,
  };
}
