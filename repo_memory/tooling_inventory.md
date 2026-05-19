# Tooling Inventory

This document inventories the local AI automation scripts used for repository maintenance and development.

## AI Task Automation Scripts

### 04-ai-task-new.ps1
- **Purpose**: Initializes a new task structure.
- **When to Use**: When beginning a new assigned task to ensure standardized tracking and initial setup.
- **Safety Boundaries**: Should not modify existing production code; only manages task metadata and tracking.

### 6-housekeeping.ps1
- **Purpose**: Performs general repository housekeeping and cleanup.
- **When to Use**: Periodically or before project handoffs to ensure consistency across docs and state files.
- **Safety Boundaries**: Limited to documentation and project state updates.

### ai-triage.ps1
- **Purpose**: Analyzes issues or bugs to determine scope and potential impact.
- **When to Use**: During the initial phase of a bug report or feature request.
- **Safety Boundaries**: Read-only analysis; does not apply fixes.

### ai-repair.ps1
- **Purpose**: Applies targeted fixes to code based on identified issues.
- **When to Use**: When a specific mechanical fix is identified and needs to be applied across the codebase.
- **Safety Boundaries**: Use only for low-risk, mechanical changes. Requires manual review.

### ai-safe-repair.ps1
- **Purpose**: A constrained version of `ai-repair.ps1` with stricter safety checks.
- **When to Use**: When applying fixes to critical governance or core architecture files.
- **Safety Boundaries**: Hard limits on the scope of changes and mandatory validation checks.

### ai-dev-cycle.ps1
- **Purpose**: Automates the iterative cycle of implementation, testing, and verification.
- **When to Use**: During the active implementation phase of a feature or bug fix.
- **Safety Boundaries**: Performs targeted-test only; does not execute full test suites or the deterministic certifier.

## External Tooling

### D:\ai-tools\ai-tools-kit
- **Role**: Unified AI automation master toolkit.
- **Usage**: Reference path for local utility scripts, runtimes, and skills.

### Gemini CLI
- **Role**: Command Line Interface for repository-aware execution.

### Antigravity
- **Role**: Premium agent runtime environment.

### Codex
- **Role**: Dedicated coding runtime environment.

### OpenCode
- **Role**: Portable orchestration runtime environment.

### Serena MCP
- **Role**: Model Context Protocol server validating 29 repository-aware intelligence tools.

### Aider
- **Role**: Bounded mechanical repair.
- **Usage**: Use only for localized, low-complexity fixes after a triage gate has identified the exact change required.
