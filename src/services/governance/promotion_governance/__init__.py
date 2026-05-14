"""
Promotion governance workflow for deterministic release eligibility assessment.

This module implements governance-only promotion workflows (no execution).
- Evaluates release eligibility deterministically
- Generates immutable promotion manifests
- Maintains ledger as sole source of truth
- No runtime promotion, ledger mutation, or mesh authority changes
"""
