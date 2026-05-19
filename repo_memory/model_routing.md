# Model Routing

To optimize quality, context window usage, and deterministic correctness, the following AI routing is mandated.

## Model Roles

| Model / Runtime | Primary Role |
| :--- | :--- |
| **GPT-5.5** | controller / architecture / final review |
| **Gemini** | executor / implementation |
| **Claude** | frontend specialist |
| **Serena** | repository intelligence |
| **Aider** | surgical repair |
| **Antigravity** | premium agent runtime |
| **Codex** | coding runtime |
| **OpenCode** | portable orchestration runtime |

## Routing Constraints
- Never use lightweight models for governance logic or architecture design.
- Use Serena to verify the existence and state of code before suggesting edits.
- Final validation of critical governance paths must be reviewed by the controller (GPT-5.5).
