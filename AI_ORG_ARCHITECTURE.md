# AI Organization Architecture

Last Updated: 2026-05-20

## Objective
This document outlines the organization structure and integration topology of the AI Tooling Layer.

## Architecture Topology

```
                   +----------------------------------+
                   |       Human Operator / Controller|
                   +-----------------+----------------+
                                     |
                                     v
                   +-----------------+----------------+
                   |       AI Governance CLI / Agent   |
                   +-----------------+----------------+
                                     |
              +----------------------+----------------------+
              |                                             |
              v                                             v
+-------------+---------------+               +-------------+---------------+
|    Serena MCP (LSP Tools)   |               |     Project Local Rules     |
|  - Symbols, Files, Search   |               |  - Invariants, Governance   |
+-----------------------------+               +-----------------------------+
```

## Integration Boundaries
1. **Master Path**: `D:\ai-tools\ai-tools-kit`
2. **Local Synced Path**: `D:\utility_automation_v2_light\.agent\skills`
3. **Core Truth Model**: AI remains advisory. The mesh quorum is the sole runtime authority.
