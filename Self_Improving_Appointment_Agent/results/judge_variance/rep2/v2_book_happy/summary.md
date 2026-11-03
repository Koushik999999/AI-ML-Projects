# Eval: prompts\system_v2.md + prompts\tools_v2.json

Rubric v2 (hash ed9dc12a00f1), deterministic checks v2.

Models: agent `gemini-3.5-flash-lite`, sim `openai/gpt-oss-20b`, judge `qwen/qwen3.8-27b`. N=3 per scenario.

## main set: score 0.67 (mean pass rate over 1 scenarios)

| scenario | pass | deterministic | judge | judge skipped | judge pending | failing checks | failing judge items |
|---|---|---|---|---|---|---|---|
| book_happy | 2/3 | 3/3 | 2/3 | 0 | 0 | - | clarity |

## Totals

- conversations: 3; judge skipped (deterministic already failed): 0; judge pending: 0
- malformed tool calls: 0; fallback replies: 0
- agent LLM calls: 24; simulator LLM calls: 6 (lines cut for speaking as the assistant: 2)
- judge tokens per call (actual): mean 1768, max 1777
