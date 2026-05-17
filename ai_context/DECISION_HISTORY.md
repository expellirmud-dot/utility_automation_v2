# Decision History

## Why this document set exists
Long-running engineering context was being held inside ChatGPT conversations.

That created risk:
- UI slowdown
- lost nuance when starting new chats
- accidental redesign
- repeated explanations
- broken continuity

Decision:
Move institutional memory into repository markdown files.

## Why strict READ-FIRST
Past workflow risk came from agents implementing based on memory or assumption.

Decision:
All repo-aware work must inspect actual files first.

## Why Serena
Repository reality matters more than conversational memory.

Decision:
Use Serena when relevant for repo inspection.

## Why AI advisory only
AI can hallucinate, drift, or overreach.

Decision:
AI may advise and implement scoped code when authorized, but governance authority remains bounded.

## Why global + project split
Global AI defaults are useful across projects.

But project-local governance must override global behavior.

Decision:
Global agent/skills provide baseline discipline.
Project files define actual project rules.

## Why hybrid GPT / Gemini
Different tools serve different roles.

Decision:
GPT for architecture/review.
Gemini for repo operations.
Serena for repository intelligence.
