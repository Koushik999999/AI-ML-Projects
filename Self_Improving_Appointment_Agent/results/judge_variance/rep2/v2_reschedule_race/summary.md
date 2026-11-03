# Eval: prompts/system_v2.md + prompts/tools_v2.json

Rubric v2 (hash ed9dc12a00f1), deterministic checks v2.

Models: agent `gemini-3.5-flash-lite`, sim `openai/gpt-oss-20b`, judge `qwen/qwen3.8-27b`. N=3 per scenario.

## heldout set: score 0.33 (mean pass rate over 1 scenarios)

| scenario | pass | deterministic | judge | judge skipped | judge pending | failing checks | failing judge items |
|---|---|---|---|---|---|---|---|
| reschedule_race | 1/3 | 3/3 | 1/3 | 0 | 0 | - | clarity x2 |

## Totals

- conversations: 3; judge skipped (deterministic already failed): 0; judge pending: 0
- malformed tool calls: 0; fallback replies: 0
- agent LLM calls: 45; simulator LLM calls: 15 (lines cut for speaking as the assistant: 1)
- judge tokens per call (actual): mean 2602, max 2650
