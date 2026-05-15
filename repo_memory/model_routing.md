# Model Routing

To optimize quality, context window usage, and deterministic correctness, the following AI routing is mandated.

## Model Roles

| Model | Primary Role | Specific Usage |
| :--- | :--- | :--- |
| **GPT** | Architecture & Governance | Architecture audits, governance boundary reviews, and final correctness gates. |
| **Gemma / Gemini (Long Context)** | Complex Implementation | Multi-file implementation and architecture-aware stitching. |
| **Gemini Flash / Lightweight** | Boilerplate & Plumbing | Boilerplate, repetitive UI components, and API plumbing. |
| **Serena** | Repository Inspection | Mandatory repository inspection, symbol lookup, and file navigation. |
| **Aider** | Mechanical Repair | Bounded mechanical repair only, performed after a triage gate. |

## Routing Constraints
- Never use Gemini Flash for governance logic or architecture design.
- Use Serena to verify the existence and state of code before suggesting edits.
- Final validation of critical governance paths must be reviewed by GPT.
