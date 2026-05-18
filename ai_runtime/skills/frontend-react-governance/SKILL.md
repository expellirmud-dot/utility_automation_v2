---
name: frontend-react-governance
description: Safe React/Next.js frontend implementation workflow for governed operator console changes.
---

# Frontend React Governance

Use this skill for React, Next.js, TypeScript, dashboard, modal, form, polling, and operator console UI work.

## Required Discipline

Before editing:
- inspect existing component structure
- identify existing state/data flow
- identify API/client/schema contracts
- state exact files to change

## Rules

Allowed:
- minimal frontend diffs
- controlled forms
- typed payload usage
- existing client functions
- frontend-only derived UI state
- read-only polling when scoped

Forbidden:
- generic runtime dispatchers
- payload typed as any when exact types exist
- hidden auto-submit
- hidden operational defaults
- backend route expansion unless explicitly approved
- certifier weakening
- authority wording/actions such as approve, commit, push, promotion, recovery unless explicitly scoped

## React Safety Checklist

Check:
- useEffect cleanup
- polling interval >= 10000ms unless explicitly approved
- no stale closure risk
- no runaway re-render loop
- no uncontrolled submit path
- no silent fallback defaults
- loading/error/success states present when relevant
