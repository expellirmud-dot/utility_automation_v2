# Model Strategy

## Gemini Model Routing

### Flash Lite
Use for:
- READ-FIRST
- scans
- summaries
- low-cost repo inspection
- broad context loading

### Flash
Use for:
- normal implementation
- moderate debugging
- code edits

### Pro
Use for:
- architecture audits
- governance reasoning
- high-risk review
- difficult debugging
- large design decisions

## GPT Strategy

GPT-5.5 / premium GPT quota should be reserved for:
- deep architecture
- critical review
- governance arbitration
- complex reasoning
- final decision support

## Known Lesson
Model persona in prompt does not guarantee actual model switch.

Always verify active model in CLI status.
