---
name: react-polling-review
description: Review React polling, auto-refresh, lifecycle visibility, and cleanup safety.
---

# React Polling Review

Use this skill when adding or reviewing polling, auto-refresh, live status, sync indicators, or task detail refresh.

## PASS Criteria

Polling is acceptable only if:
- interval is explicit and reasonable
- default interval is >= 10000ms unless explicitly approved
- every setInterval has cleanup
- async effects prevent stale updates after unmount
- dependencies do not recreate intervals unnecessarily
- failures are visible but non-fatal
- polling is read-only

## FAIL Criteria

Fail if:
- interval is too aggressive
- missing cleanup
- polling triggers mutation
- polling causes rerender loop
- effect dependency includes full object when stable id is available
- hidden retry storm possible
- UI hides sync failures

## Required Review Output

Return:
- polling interval
- cleanup mechanism
- dependency analysis
- mutation safety
- failure handling
- PASS/FAIL
