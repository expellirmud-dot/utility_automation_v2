# SKILL SYNC POLICY
# Updated: 20/05/2569

## Purpose

This document defines how AI skills are maintained and synchronized across apps.

---

## Central Source of Truth

Primary source:

```text
D:\ai-tools\ai-tools-kit
```

Main skill source:

```text
D:\ai-tools\ai-tools-kit\skills
```

All skill edits must start at the central source.

Do not edit global/app copies directly unless performing an explicitly approved emergency hotfix.

---

## Sync Targets

Skills may be copied to:

```text
D:\utility_automation_v2_light\ai_runtime\skills
C:\Users\Expellirmud\.gemini\skills
C:\Users\Expellirmud\.codex\skills
C:\Users\Expellirmud\.gemini\antigravity\skills
```

Other apps may be added as sync targets as needed.

---

## Sync Rule

```text
Edit central source first → sync outward → verify activation
```

Do not edit app-local copies directly.

Reason:

- prevents skill drift
- keeps behavior consistent across apps
- simplifies debugging
- makes READ-FIRST behavior predictable

---

## Suggested Sync Modes

Safe copy mode:

```powershell
robocopy D:\ai-tools\ai-tools-kit\skills C:\Users\Expellirmud\.gemini\skills /E /XO /XD ".git" "__pycache__" /XF "*.tmp" "*.bak"
```

Force mirror mode:

```powershell
robocopy D:\ai-tools\ai-tools-kit\skills C:\Users\Expellirmud\.gemini\skills /MIR /XD ".git" "__pycache__" /XF "*.tmp" "*.bak"
```

Use force mirror only when the target should exactly match the central skill source.

---

## Verification Prompt

After sync, test activation:

```text
TOOLING / SKILL VERIFICATION ONLY.

Activate READ-FIRST governance skill.
Activate frontend-react-governance if available.
Report loaded skill names and paths.
Invoke Serena find_file for a known project file.
Do not implement.
```

---

## External Reference Docs

Codex:

- https://developers.openai.com/codex/guides/agents-md
- https://developers.openai.com/codex/skills
- https://developers.openai.com/codex/mcp

Gemini CLI:

- https://geminicli.com/docs/cli/skills/
- https://geminicli.com/docs/cli/tutorials/memory-management/
- https://geminicli.com/docs/cli/tutorials/automation/
- https://geminicli.com/docs/hooks/
- https://geminicli.com/docs/tools/mcp-server/

Antigravity:

- https://antigravity.google/docs/skills
- https://antigravity.google/docs/mcp
- https://antigravity.google/docs/hooks
- https://antigravity.google/docs/ide-getting-started
