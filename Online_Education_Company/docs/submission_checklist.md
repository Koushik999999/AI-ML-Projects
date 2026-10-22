# Submission checklist (Google Form)

Before pushing / submitting:

- [ ] `bash scripts/check_no_data.sh --history` prints OK (no media/transcript/data file in any commit).
- [ ] `git ls-files | grep -Ei "\.(mp4|vtt|wav)$|^data/|cache/|outputs/"` prints nothing.
- [ ] `.env` is not tracked; `.env.example` is.
- [ ] `pytest -q` passes.
- [ ] `docs/ai_history.md` re-read: no credentials, no teacher/child names, only batch codes.
- [ ] Decide whether `Humaniti_AI_24_Hour_Build_Challenge.pdf` (the brief) should be in the public repo; it is not required.

Hosting (Streamlit Community Cloud):

1. Push the repo, then "New app" -> main file `streamlit_app.py`, Python 3.11 or 3.12 (numpy 1.26 pin).
2. Leave secrets empty. Do not set `EXPLAINER_PROVIDER` unless the organiser approved external APIs.
3. Open the hosted link in a private window and test with a short clip + its VTT, then a clip without a VTT.
4. Remember the trade-off: free tiers are small. Give the evaluators a VTT-capable path; without a VTT the app skips Whisper by default and the verdict is low-confidence.

Form fields: hosted link - GitHub repo - AI history (`docs/ai_history.md`) - explanation (`docs/explanation.md`, 300 words).
