# Serena / Gemini Rules

## Serena

Serena is repo-aware tooling.

It is not universal memory.

Known Serena version:
1.3.0

Known valid commands:
- serena --help
- serena project --help
- serena project index <repo>

Known invalid commands observed:
- serena activate
- serena status
- serena tools symbols-list

If an AI invents Serena syntax, verify first.

## Gemini CLI

Gemini workspace depends on current directory or added directories.

Wrong workspace can cause access failure.

Use:
- cd <project-root>
- gemini

or:
- /directory add <path>

## Project Override
Project-local instructions override global Gemini defaults.
