# UI Port Prompt

Goal:
Port visual design into the existing ops console only.

Do not introduce Next.js or React into production unless explicitly assigned.

Keep:
- FastAPI backend
- existing static ops console
- existing /ops GET-only APIs
- read-only dashboard semantics
- DOM-safe rendering
- createElement / textContent / replaceChildren
- no innerHTML
- no action buttons
- no mutation controls

Allowed:
- layout improvements
- typography
- cards
- badges
- charts
- loading states
- empty states
- degraded states
- visual hierarchy

Forbidden:
- POST/PUT/PATCH/DELETE
- control actions
- replay triggers
- policy promotion
- recovery execution
- backend authority changes
- framework migration

Validation:
- run ops console tests
- run full pytest if behavior changed

Report exact files changed and test results.
