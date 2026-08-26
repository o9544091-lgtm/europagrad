---
description: Execute the next pending EuropaGrad task end to end
---

Execute the next unit of work for EuropaGrad. Use $ARGUMENTS to override task selection (e.g., a specific task number).

1. Read AGENTS.md, docs/state.md, docs/tasks.md.
2. Choose the lowest-numbered ⬜ task whose dependencies are met (blocked if any required input is missing — e.g., DB tasks need Supabase project credentials; UI integration tasks need generated screens or existing primitives).
3. If the task requires external credentials not yet configured (Supabase keys, OpenRouter, Tavily), state exactly which `.env` values are missing and stop with setup instructions — do not fake progress.
4. Load relevant skills first (`data-integrity` for pipeline/data/display code; `ui-drop-in` when integrating externally generated UI).
5. Implement to the task's Acceptance Criteria in docs/tasks.md. No placeholder implementations.
6. Verify: `pnpm lint && pnpm typecheck && pnpm test` in apps/web and/or `uv run ruff check . && uv run pytest -q` in apps/agent (only the side you touched). Fix failures at root cause before finishing.
7. Update docs/tasks.md (⬜→☑ or 🚧) and docs/state.md (phase, decisions, known bugs) in the same change set.
8. Report outcome in one line: "Task N done: <what now works>".
