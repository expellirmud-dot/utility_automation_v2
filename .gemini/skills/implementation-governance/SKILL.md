---
name: implementation-governance
description: Exact scoped implementation skill for deterministic governance code.
---

RULES:
- Implement approved scope only.
- Minimal diff only.
- No speculative refactor.
- No architecture expansion.
- No hidden dependency change.
- No authority mutation.
- No implementation from memory.

REQUIRED BEFORE EDITING:
A. files inspected
B. root cause/objective
C. exact files to change
D. implementation plan
E. validation commands

REQUIRED AFTER EDITING:
F. diff summary
G. validation results
H. git status
I. remaining risks
