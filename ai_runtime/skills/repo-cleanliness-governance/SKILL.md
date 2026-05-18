---
name: repo-cleanliness-governance
description: Git working tree and commit boundary discipline for governed tasks.
---

# Repo Cleanliness Governance

## Requirements

Before implementation:

- run git status
- stop if tracked files are dirty without controller approval
- separate runtime artifacts from committed scope

Before commit:

- review git diff
- stage only approved files
- exclude controller request/contracts unless explicitly approved
- no unrelated files

After commit:

- report commit SHA
- report push result
- report final git status

## Forbidden

- mixed task commits
- hidden untracked artifacts
- accidental prompt/temp file commits
- autonomous commit/push without explicit controller approval
