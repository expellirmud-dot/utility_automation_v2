import { z } from "zod";

const jsonPrimitiveSchema = z.union([z.string(), z.number(), z.boolean(), z.null()]);
export type JsonValue =
  | z.infer<typeof jsonPrimitiveSchema>
  | { [key: string]: JsonValue }
  | JsonValue[];

export const jsonValueSchema: z.ZodType<JsonValue> = z.lazy(() =>
  z.union([jsonPrimitiveSchema, z.array(jsonValueSchema), z.record(jsonValueSchema)]),
);

export const overviewCardSchema = z.object({
  key: z.string(),
  title: z.string(),
  projection_source: z.string(),
  read_only: z.boolean(),
  authority_coupled: z.boolean(),
  fallback_active: z.boolean(),
  status: z.string(),
  label: z.string(),
});

export const overviewResponseSchema = z.object({
  cards: z.array(overviewCardSchema),
});

export const providerStatusSchema = z.object({
  key: z.string(),
  status: z.string(),
  label: z.string(),
  source_ref: z.string(),
  provider_kind: z.string(),
  connected: z.boolean(),
  stale: z.boolean(),
});

export const projectionCardSchema = z.object({
  key: z.string(),
  title: z.string(),
  domain: z.string(),
  status: z.string(),
  label: z.string(),
  provider_status: providerStatusSchema,
  read_only: z.boolean(),
  authority_coupled: z.boolean(),
  source_type: z.string(),
  fallback_active: z.boolean(),
  fallback_reason: z.string(),
  item_count: z.number(),
  stable_order: z.number(),
});

export const projectionsResponseSchema = z.object({
  cards: z.array(projectionCardSchema),
});

export const surfaceSchema = z.object({
  key: z.string(),
  title: z.string(),
  route_prefix: z.string(),
  api_prefix: z.string(),
  allowed_methods: z.array(z.string()),
  status: z.string(),
  authority_coupled: z.boolean(),
  read_only: z.boolean(),
  exposed_in_ops: z.boolean(),
  stable_order: z.number(),
});

export const surfacesResponseSchema = z.object({
  surfaces: z.array(surfaceSchema),
});

export const routeGovernanceViolationSchema = z.object({
  path: z.string(),
  method: z.string(),
  reason: z.string(),
});

export const routeGovernanceResponseSchema = z.object({
  valid: z.boolean(),
  checked_routes: z.number(),
  registry_surface_count: z.number(),
  violations: z.array(routeGovernanceViolationSchema),
});

export const domainPanelSchema = z.object({
  domain: z.string(),
  status: z.string(),
  source: z.string(),
  items: z.array(z.record(jsonValueSchema)),
  advisory_only: z.boolean(),
  item_count: z.number(),
  summaries: z.array(z.record(jsonValueSchema)),
  diagnostics: z.record(jsonValueSchema),
  metadata: z.record(jsonValueSchema),
});

export const domainPanelsResponseSchema = z.object({
  panels: z.array(domainPanelSchema),
});

export const certificationSummarySchema = z.object({
  passed: z.boolean(),
  overall_score: z.number(),
  artifact_hash: z.string(),
});

export const gatekeeperSummarySchema = z.object({
  passed: z.boolean(),
  advisory_decision: z.string(),
  report_hash: z.string(),
});

export const authorizationSummarySchema = z.object({
  passed: z.boolean(),
  advisory_decision: z.string(),
  authorization_hash: z.string(),
  reason_codes: z.array(z.string()),
});

export const humanReviewIntentRecordSchema = z.object({
  archive_hash: z.string(),
  authorizer_id: z.string(),
  review_intent: z.string(),
  rationale: z.string(),
  authorization_epoch: z.number(),
  authorization_seq: z.number(),
  record_hash: z.string(),
  record_version: z.string(),
});

export const humanReviewIntentResponseSchema = z.array(humanReviewIntentRecordSchema);

export const evidencePackageResponseSchema = z.object({
  package: z.object({
    package_id: z.string(),
    package_version: z.string(),
    archive_hash: z.string(),
    human_record_hash: z.string(),
    evidence_link_hash: z.string(),
    certification_hash: z.string(),
    promotion_hash: z.string(),
    gatekeeper_report_hash: z.string(),
    package_status: z.string(),
    reason_codes: z.array(z.string()),
    package_hash: z.string(),
  }),
});

export const evidencePackageIntegrityResponseSchema = z.object({
  report: z.object({
    passed: z.boolean(),
    violations: z.array(z.object({
      field: z.string(),
      reason: z.string(),
    })),
    package_id: z.string().optional(),
    expected_version: z.string().optional(),
    report_hash: z.string(),
  }),
});

export const evidencePackageReadinessResponseSchema = z.object({
  report: z.object({
    package_id: z.string(),
    decision: z.string(),
    reason_codes: z.array(z.string()),
    report_hash: z.string(),
  }),
});

export const evidenceReviewSummaryResponseSchema = z.object({
  summary: z.object({
    package_id: z.string(),
    package_hash: z.string(),
    integrity_report_hash: z.string(),
    readiness_report_hash: z.string(),
    readiness_decision: z.string(),
    integrity_passed: z.boolean(),
    package_status: z.string(),
    reason_codes: z.array(z.string()),
    summary_version: z.string(),
    summary_hash: z.string(),
  }),
});

export const governanceReviewIndexResponseSchema = z.object({
  index: z.object({
    index_version: z.string(),
    index_status: z.string(),
    certification_artifact_hash: z.string(),
    promotion_governance_hash: z.string(),
    evidence_package_hash: z.string(),
    integrity_report_hash: z.string(),
    readiness_report_hash: z.string(),
    review_summary_hash: z.string(),
    readiness_decision: z.string(),
    integrity_passed: z.boolean(),
    invariant_keys: z.array(z.string()),
    reason_codes: z.array(z.string()),
    index_hash: z.string(),
  }),
});

export const releaseGovernanceResponseSchema = z.object({


  certification: certificationSummarySchema,
  gatekeeper: gatekeeperSummarySchema,
  authorization: authorizationSummarySchema,
});

export const runtimeTaskSummarySchema = z.object({
  task_id: z.string(),
  contract_id: z.string().nullable(),
  state: z.string(),
  contract: z.record(jsonValueSchema).nullable(),
  evidence_found: z.boolean(),
  evidence: z.record(jsonValueSchema).nullable().optional(),
  reports: z.object({
    evidence_json: z.boolean(),
    execution_transcript: z.boolean(),
    tool_trace: z.boolean(),
    worker_report: z.boolean(),
  }),
  summary: z.string(),
});

export const runtimeTasksResponseSchema = z.object({
  timestamp: z.string(),
  count: z.number(),
  tasks: z.array(runtimeTaskSummarySchema),
});

export const runtimeTaskDetailResponseSchema = z.object({
  task: runtimeTaskSummarySchema,
});

const requiredFormStringSchema = z.string().trim().min(1);
const requiredFormStringListSchema = z.array(requiredFormStringSchema).min(1);

export const createTaskPayloadSchema = z.object({
  task_id: requiredFormStringSchema,
  title: requiredFormStringSchema,
  objective: requiredFormStringSchema,
  rationale: requiredFormStringSchema,
  scope: requiredFormStringListSchema,
  candidate_modules: z.array(z.string()),
  tests: z.array(z.string()),
  validation: z.array(z.string()),
  acceptance: z.array(z.string()),
  next_task: z.string().optional(),
  output_file: z.string().optional(),
});

export const startTaskPayloadSchema = z.object({
  task_id: requiredFormStringSchema,
  actor_id: requiredFormStringSchema,
  request_file: z.string().optional(),
  title: z.string().optional(),
  objective: z.string().optional(),
  rationale: z.string().optional(),
  scope: z.array(z.string()).default([]),
  candidate_modules: z.array(z.string()).default([]),
  tests: z.array(z.string()).default([]),
  validation: z.array(z.string()).default([]),
  acceptance: z.array(z.string()).default([]),
  next_task: z.string().optional(),
  allow_read: z.array(z.string()).default([]),
  allow_write: z.array(z.string()).default([]),
  expected_output: requiredFormStringListSchema,
  allow_command: z.array(z.string()).optional(),
  forbid_pattern: z.array(z.string()).optional(),
  duration_mins: z.number().default(60),
});

export const finishTaskPayloadSchema = z.object({
  task_id: requiredFormStringSchema,
  worker_id: requiredFormStringSchema,
  actual_output: requiredFormStringListSchema,
});
