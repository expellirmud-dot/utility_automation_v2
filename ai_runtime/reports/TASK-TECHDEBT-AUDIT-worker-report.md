# Technical Debt Audit Report

## 1. Architecture Hotspots
- **Governance Policy Graph (`src/services/governance/policy_graph/`)**: Highly fragmented. The module is split into numerous specialized "Engine" classes (e.g., `audit_query_engine`, `governance_explanation_engine`, `incremental_repair`, etc.). While modular, this fragmentation increases cognitive load and complicates the overall data flow.
- **Promotion Governance (`src/services/governance/promotion_governance/`)**: Significant complexity centered around evidence package creation and readiness providers.

## 2. Risky Modules
- **Consensus Layer (`src/services/consensus/`)**:
  - `causal_validator.py`: Contains a critical TODO: "Implement actual cryptographic signature validation against ValidatorRegistry". This is a security gap in a core authority module.
  - `quorum_engine.py`: Contains a TODO: "broadcast to peers", indicating incomplete communication logic in the mesh authority.

## 3. Duplication & Fragmentation
- **Pipeline Proliferation**: Pattern of creating "Wrapped" versions of pipelines rather than utilizing a middleware or strategy pattern.
  - `HardenedProductionPipeline` wraps `ProductionPipeline`.
  - `GovernanceWrappedSemanticPipeline` wraps `SemanticVoucherPipeline`.
- **Semantic Layer Versions**: Presence of both `semantic_pipeline.py` and `semantic_pipeline_with_governance.py` suggests a lack of a unified configuration-driven pipeline approach.

## 4. Validation Gaps
- **Unit Test Density**: While high-level integration tests and deterministic certification tests are comprehensive (in `tests/` and `src/tests/certification/`), there is a noticeable gap in granular unit tests for the individual specialized engines in the `policy_graph` and `promotion_governance` modules.
- **Edge Case Coverage**: Lack of explicit stress tests for the `causal_validator` given the missing signature logic.

## 5. Governance Risks
- **Core Invariant Vulnerability**: The missing cryptographic validation in `causal_validator.py` directly threatens the "Mesh quorum is the only authority" and "Determinism is mandatory" invariants. If signatures aren't validated, the authority of the state transition is compromised.

## 6. Maintainability Concerns
- **Layering Overload**: The wrapping pattern (`Base` -> `Wrapped` -> `GovernanceWrapped`) creates deep call stacks and makes it harder to track the actual execution path of a request.
- **Fragmented Logic**: The high number of small files in `policy_graph` makes it difficult to perform a comprehensive audit of the graph's state transitions.

## 7. Quick Wins
- **Implement Missing Consensus Logic**: Resolve the TODOs in `causal_validator.py` and `quorum_engine.py` to secure the authority layer.
- **Consolidate Semantic Pipelines**: Merge `SemanticVoucherPipeline` and `GovernanceWrappedSemanticPipeline` into a single class with a `governance_enabled` flag or configuration.

## 8. Major Refactor Candidates
- **Policy Graph Consolidation**: Refactor the `policy_graph` module to use a more cohesive graph processing framework, reducing the number of specialized "Engine" classes in favor of a more flexible query/mutation API.
- **Pipeline Middleware Architecture**: Replace the "Wrapped" pipeline pattern with a standard middleware or decorator architecture to handle hardening and governance consistently across all workflows.
