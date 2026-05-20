# MODEL SELECTION MATRIX
# Updated: 20/05/2569

## Purpose

Choose the right AI model/app for each work type based on capability, quota, and risk.

---

## Available Apps and Models

| App | Models | Notes |
|---|---|---|
| ChatGPT | GPT-5.5 | controller / planning / review |
| Codex | GPT-5.5 / Thinking | code review, independent verification |
| Gemini CLI | Gemini 3.1 Pro, Gemini 3.0 Flash, Gemini 3.1 Flash Lite Preview | repo implementation, CLI execution |
| Antigravity | Gemini 3.1 Pro H/L, Gemini 3.5 Flash H/M, Sonnet/Opus 4.6 Thinking | interactive agent runs |
| OpenCode | Gemma 4, Gemini Flash Lite, OpenRouter free models | low-cost coding and experiments |
| Aider | configured model | patch-based code edits |

---

## Routing Rules

| Task Type | Preferred | Fallback |
|---|---|---|
| Architecture planning | GPT-5.5 Thinking | Gemini 3.1 Pro |
| Controller review | GPT-5.5 | Codex |
| Independent code review | Codex GPT-5.5 / Thinking | GPT-5.5 |
| Heavy repo implementation | Gemini CLI 3.1 Pro | Antigravity 3.1 Pro |
| Fast CRUD / UI wiring | Gemini 3.5 Flash High/Medium | Gemini Flash Lite |
| Word/docx generation | Sonnet/Opus 4.6 Thinking | Gemini 3.1 Pro |
| Browser automation / Playwright | Gemini 3.1 Pro | Sonnet |
| Cheap experiments | OpenCode Gemma 4 / free models | Gemini Flash Lite |
| Emergency bugfix | Gemini 3.1 Pro or Codex | GPT review |

---

## Escalation Rule

Escalate to a stronger model when:

- repeated build/test failures
- architecture ambiguity
- brittle browser automation
- data correctness risk
- document formatting risk
- schema migration risk

Do not use expensive models for simple frontend wiring unless quota/cost makes sense.
