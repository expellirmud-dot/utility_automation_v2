import type { z } from "zod";
import type {
  domainPanelSchema,
  domainPanelsResponseSchema,
  overviewCardSchema,
  overviewResponseSchema,
  projectionCardSchema,
  projectionsResponseSchema,
  routeGovernanceResponseSchema,
  releaseGovernanceResponseSchema,
  evidencePackageResponseSchema,
  evidencePackageIntegrityResponseSchema,
  evidencePackageReadinessResponseSchema,
  evidenceReviewSummaryResponseSchema,
  humanReviewIntentResponseSchema,
  surfaceSchema,
  surfacesResponseSchema,
  runtimeTaskSummarySchema,
  runtimeTasksResponseSchema,
  runtimeTaskDetailResponseSchema,
  createTaskPayloadSchema,
  startTaskPayloadSchema,
  finishTaskPayloadSchema,
} from "./schemas";




export type OverviewCard = z.infer<typeof overviewCardSchema>;
export type OverviewResponse = z.infer<typeof overviewResponseSchema>;
export type ProjectionCard = z.infer<typeof projectionCardSchema>;
export type ProjectionsResponse = z.infer<typeof projectionsResponseSchema>;
export type Surface = z.infer<typeof surfaceSchema>;
export type SurfacesResponse = z.infer<typeof surfacesResponseSchema>;
export type RouteGovernanceResponse = z.infer<typeof routeGovernanceResponseSchema>;
export type ReleaseGovernanceResponse = z.infer<typeof releaseGovernanceResponseSchema>;
export type EvidencePackageResponse = z.infer<typeof evidencePackageResponseSchema>;
export type EvidencePackageIntegrityResponse = z.infer<typeof evidencePackageIntegrityResponseSchema>;
export type EvidencePackageReadinessResponse = z.infer<typeof evidencePackageReadinessResponseSchema>;
export type EvidenceReviewSummaryResponse = z.infer<typeof evidenceReviewSummaryResponseSchema>;
export type HumanReviewIntentResponse = z.infer<typeof humanReviewIntentResponseSchema>;
export type RuntimeTaskSummary = z.infer<typeof runtimeTaskSummarySchema>;
export type RuntimeTasksResponse = z.infer<typeof runtimeTasksResponseSchema>;
export type RuntimeTaskDetailResponse = z.infer<typeof runtimeTaskDetailResponseSchema>;
export type CreateTaskPayload = z.infer<typeof createTaskPayloadSchema>;
export type StartTaskPayload = z.infer<typeof startTaskPayloadSchema>;
export type FinishTaskPayload = z.infer<typeof finishTaskPayloadSchema>;
export type RuntimeTaskAction = "create" | "start" | "finish";


export type DomainPanel = z.infer<typeof domainPanelSchema>;
export type DomainPanelsResponse = z.infer<typeof domainPanelsResponseSchema>;

export type ObservatoryData = {
  overview: OverviewResponse;
  projections: ProjectionsResponse;
  surfaces: SurfacesResponse;
  routeGovernance: RouteGovernanceResponse;
  domainPanels: DomainPanelsResponse;
};
