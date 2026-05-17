# AI Setup State (Global)

Last Updated: 2026-05-17

## Purpose
This file is the source of truth for my global AI engineering workflow.

Any AI assistant must read this before modifying:
- Gemini CLI config
- Gemini agents
- Gemini skills
- Gemini extensions
- Serena setup
- AI workflow architecture

Preserve continuity unless explicitly instructed otherwise.

---

## Global Gemini CLI Setup

Base path:

C:\Users\Expellirmud\.gemini

Global agent:

C:\Users\Expellirmud\.gemini\agents\code.md

Behavior:
- senior software engineering assistant
- repository-aware
- Serena-aware
- safe implementation discipline
- exact validation only
- no implementation from memory
- project-local rules override global rules

---

## Global Skills Installed

Path:

C:\Users\Expellirmud\.gemini\skills

Installed:
- serena-repo-bootstrap
- safe-implementation
- root-cause-debugging
- review-validation
- code-design

Purpose:
- bootstrap repo safely
- enforce READ-FIRST
- root cause analysis
- implementation discipline
- architecture review

---

## Extensions Installed

Path:

C:\Users\Expellirmud\.gemini\extensions

Installed:
- conductor
- flutter

Status:
not core to current workflow

Do not redesign around these unless explicitly requested.

---

## Removed / Deprecated

Removed:
- broken legacy code.md
- apify-agent-skills
- global system.md
- conflicting old configs

Do not restore these automatically.

---

## Serena Setup

Installed globally.

Version:
1.3.0

Important CLI behavior:

INVALID:
- serena activate
- serena status
- serena tools symbols-list

VALID:
- serena --help
- serena project --help
- serena project index <repo>

Behavior:
Serena is repo-aware.
It is NOT a universal global project memory.

---

## Model Strategy

Default:
gemini-3.1-flash-lite-preview

Heavy reasoning:
gemini-3.1-pro-preview

Gemma:
gemma-4 unavailable under current entitlement

Notes:
- model role prompt != actual model switch
- always verify active model

---

## Known CLI Gotchas

- workspace path controls accessible repo scope
- launching Gemini from wrong folder limits access
- Gemini may hallucinate Serena CLI syntax
- Gemini may roleplay model identity from prompt text
- CLI extensions may inject additional behavior

---

## Global Workflow Principles

Required:
- inspect actual files
- READ-FIRST when repo work
- use Serena when relevant
- respect project-local governance
- no fake validation
- exact reporting

Forbidden:
- implementation from memory
- speculative refactors
- replacing configs without review
- silently redesigning workflow