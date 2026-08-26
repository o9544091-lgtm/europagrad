# qa-pass

Full quality sweep across web app and agent.

1. Static checks: `pnpm lint && pnpm typecheck && pnpm build` in apps/web; `uv run ruff check .` in apps/agent.
2. Tests: `pnpm test` in apps/web; `uv run pytest -q` in apps/agent.
3. Manual matrix against docs/ui-spec.md "Required states" on key screens (landing, search, results, program detail): loading skeletons, empty state, error+retry, mobile 360px layout, keyboard-only navigation, dark mode toggle.
4. Data integrity spot-check: open any program detail page — every critical fact must display a source link + verbatim quote or an explicit NOT_SPECIFIED marker (AGENTS.md golden rule 1).
5. Report findings grouped as blockers / should-fix / nice-to-have, then fix all blockers immediately before ending.
