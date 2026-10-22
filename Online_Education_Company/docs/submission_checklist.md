# Submission checklist (Google Form)

Everything below is for you to run; the assistant does not run git commands that change state.

## Before pushing

- [ ] `pytest -q` passes (17+ tests).
- [ ] `bash scripts/check_no_data.sh --history` prints OK (no media/transcript/data in any commit).
- [ ] After staging: `git diff --cached --name-only` shows only code/docs. Nothing under `data/`, `cache/`, `outputs/`, no `.env`, no `*.pdf`, `*.mp4`, `*.vtt`, `*.wav`.
- [ ] `git ls-files | grep -Ei "\.(mp4|vtt|wav|pdf)$|/data/|/cache/|/outputs/"` prints nothing.
- [ ] `docs/ai_history.md` re-read: no credentials, no teacher/child names, only batch codes.
- [ ] Note the pre-commit hook in `.git/hooks/pre-commit` (see final report for how to keep or remove it).
- [ ] If you add the packaged hosting: `docs/hosting.md` followed; no token written to any file.

## Hosting (see `docs/hosting.md`)

- [ ] Space (recommended) or Streamlit Cloud deployed; opened in a private browser window.
- [ ] Test A: short clip **with** `.vtt` -> full verdict, no banner about missing signals.
- [ ] Test B: same clip **without** `.vtt` -> "Speech model: ready" in the sidebar, banner about approximate speaker split, lower confidence.
- [ ] Test C: your largest realistic upload (proxy size limits are unverified).
- [ ] Open the link again shortly before the deadline (free CPU Spaces sleep).

## Known gaps to be upfront about

- Leave-one-out accuracy 3/8 exact, 6/8 within one class; only Excellent vs the rest is reliable.
- One Poor class (B558) is scored Excellent; tone is not measured.
- Docker image and both hosted deployments are untested.
- Free-tier CPU may transcribe only part of a long class within the time budget.

## Form fields

Hosted link - GitHub repo - AI history (`docs/ai_history.md`) - explanation (`docs/explanation.md`, 265 words).
