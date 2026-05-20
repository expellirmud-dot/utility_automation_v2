# CHAT PERFORMANCE DOCTRINE
# Updated: 20/05/2569

## Purpose

Prevent controller chat lag and token bloat while preserving project continuity and AI capability.

---

## Core Principle

```text
Conversation is disposable.
Repository artifacts are durable.
```

The chat is a controller channel, not a storage layer.

---

## Chat Role

Chat should carry:

- decisions
- short summaries
- approval gates
- risk calls
- model routing
- instructions to run specific reports/tests

Chat should not carry:

- full diffs
- full logs
- raw source dumps
- large markdown bundles
- repeated context dumps

---

## Artifact Role

Heavy evidence must live in files:

```text
D:\utility_automation_v2_light\ai_runtime\reports
```

Project memory must live in:

```text
D:\utility_automation_v2_light\repo_memory
D:\utility_automation_v2_light\docs
```

---

## Stateless Continuation Rule

When a chat starts lagging or a new session is needed, open a new chat and use:

```text
PROJECT CONTINUATION MODE

This chat is stateless.
Do not rely on prior chat history.

Source of truth:
- repository state
- docs
- repo_memory
- ai_runtime/reports
- Serena inspection
- latest controller instruction

Enter READ-FIRST mode.
Invoke Serena tools explicitly and return evidence.
Inspect current roadmap and latest reports.
Return current state and plan before implementation.

Do not implement until approved.
```

---

## Why This Works

Long chats become slow because browser/UI must render and retain large DOM, markdown, syntax-highlighted code blocks, images, logs, and diffs.

By moving heavy evidence into files and reconstructing context from artifacts, the chat can remain lightweight without losing continuity.
