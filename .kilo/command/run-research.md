# run-research

Run the EuropaGrad research agent locally.

Arguments ($ARGUMENTS): country codes comma-separated + optional depth L1|L2|L3. Examples: "IT L1", "DE,NL L2", "IT" (defaults to L2).

1. Read docs/pipeline.md (usage section).
2. Verify apps/agent/.env has required keys: SUPABASE_URL, SUPABASE_SERVICE_KEY (writes), OPENROUTER_API_KEY, TAVILY_API_KEY. Missing keys → stop and print setup instructions from AGENTS.md.
3. Always dry-run first unless the user explicitly requested a real run:
   `cd apps/agent; uv run agent run --countries <CODES> --depth <LEVEL> --dry-run`
4. Review the printed plan (university inventory size, candidate URL estimate, depth caps). Confirm scope is sane before proceeding.
5. Real run: repeat without --dry-run. Never raise concurrency/politeness limits above defaults.
6. Summarize outcomes: programs/scholarships extracted, QC warnings, conflicts flagged, change_log entries written, job row final status.
