---
name: mcp-connector-governance
description: Governance rules for MCP servers, OpenAI connectors, external tools, and tool approval boundaries.
---

# MCP Connector Governance

Use this skill when adding, configuring, reviewing, or invoking MCP servers, OpenAI connectors, external APIs, or tool integrations.

## Core Rules

- MCP/connectors are external capability layers, not governance authority.
- Do not connect untrusted MCP servers to governed runtime workflows.
- Use explicit allowed tools only.
- Mutation tools require human approval.
- Read tools may be allowed only when scoped.
- Never expose ledger, mesh, quorum, promotion, recovery, commit, or push authority through MCP without explicit controller approval.

## Required Review Before Tool Use

Check:

1. server identity
2. tool list
3. read/write capability
4. data sent to tool
5. approval requirement
6. audit/logging surface
7. failure behavior

## Forbidden

- arbitrary external tool access
- broad tool allowlists
- hidden write actions
- automatic approval
- self-approval
- direct ledger/quorum/mesh mutation
- secret leakage
- prompt-injection-sensitive tool chains

## Required Output

Return:

- connector/server used
- allowed tools
- approval policy
- data exposure risk
- mutation risk
- PASS/FAIL
