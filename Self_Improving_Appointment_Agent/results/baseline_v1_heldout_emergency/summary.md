# Eval: prompts/system_v1.md + prompts/tools_v1.json

Rubric v2 (hash ed9dc12a00f1), deterministic checks v2.

Models: agent `gemini-3.5-flash-lite`, sim `openai/gpt-oss-20b`, judge `qwen/qwen3.8-27b`. N=3 per scenario.

## heldout set: score 0.67 (mean pass rate over 1 scenarios)

| scenario | pass | deterministic | judge | judge skipped | judge pending | failing checks | failing judge items |
|---|---|---|---|---|---|---|---|
| emergency_first | 2/3 | 2/3 | 2/2 | 1 | 0 | escalated:emergency | - |

## Totals

- conversations: 3; judge skipped (deterministic already failed): 1; judge pending: 0
- malformed tool calls: 0; fallback replies: 0
- agent LLM calls: 8; simulator LLM calls: 0 (lines cut for speaking as the assistant: 0)
- judge tokens per call (actual): mean 1284, max 1292
