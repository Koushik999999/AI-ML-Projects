# AI interaction history (redacted)

Assistant: Claude Code (Sonnet 5.5) in VS Code. Names of people (teachers, children) are never written here;
recordings are referred to by batch code only. No credentials were used.

## Session 1 — setup and data understanding

| # | Prompt / intent | Decision, result, failure, fix |
|---|---|---|
| 1 | Brief + hard constraints: local processing, no data in git, anonymised LLM input only, pluggable explainer, running log. | Did safety setup before any analysis: project `.gitignore` (data/, cache/, outputs/, media, transcripts, .env), `git check-ignore -v` proof, `scripts/check_no_data.sh` + pre-commit hook (tested by force-staging a dummy `.vtt`: blocked). |
| 2 | Failure: parent repo `.gitignore` ignores `*.txt` / `*.toml`, which would hide `requirements.txt` and `packages.txt` needed for deployment. | Added negations in the project `.gitignore` and verified with `git check-ignore`. |
| 3 | Read the challenge PDF and `feedbacks.pdf` with `pypdf` (poppler missing, so no page rendering). | `feedbacks.pdf` is a *human rubric by batch*: 8x8 branded background, one-to-one interaction (children asked by name), rapport/intro, homework, conclusion, time for new joiners to self-introduce, energetic/pleasant tone, face visible, camera on throughout, good lighting. Folder `weak` = Poor (confirmed). `quality issue` = setup/presentation issues (no background, face not visible, rapport), not necessarily broken audio. |
| 4 | **Self-correction on data handling.** I was about to view video frames to understand the layout. Frames show children, and viewing them would send them to an external API (me). | Switched to numeric-only inspection (luma grids, face-detector boxes). Transcript excerpts that I viewed were limited and speaker names aliased (S1, S2...). Rule going forward: no frame is ever opened by the assistant or written to disk. |
| 5 | Failure: `opencv-python-headless` 5.x has no `CascadeClassifier`. | Pinned `opencv-python-headless==4.10.0.84`, `numpy<2`. |
| 6 | Failure: very large shell heredoc broke the shell parser. | Wrote source files with the editor tool instead. |
| 7 | Teacher identification without names. | Heuristic "speaker with most words" validated against the names in `feedbacks.pdf`: correct in all 9 recordings where the ground truth could be matched (names never printed). One near-tie recording added a tie-break rule. |
| 8 | Audio probe. | Audio is digitally clean (noise floor about -85 dB, platform noise gating) so noise/SNR is a weak signal; speech ratio and long pauses are the useful ones. Measuring "pauses" must start at the first speech, not at t=0 (one recording starts 7 min late). |
| 9 | Transcript probe. | Platform VTT has speaker labels, but it is machine-transcribed: names are mangled and the "Malayalam" demo is garbled English-looking phonetics (0 Malayalam script characters). Lexicon features on it are unreliable; talk-time and turn-taking features are reliable. |

## Session 1 (continued) — features, rubric, app

| # | Prompt / intent | Decision, result, failure, fix |
|---|---|---|
| 10 | Note on item 3: `feedbacks.pdf` contains teacher names, and it was read once by the assistant (as instructed). Nothing derived from it that names a person is stored in the repo; docs use batch codes. | — |
| 11 | Plan: transcript features first (speaker labels exist), then audio, then video; rubric after looking at separations. | Video decode benchmark: keyframes are about 24 s apart (too sparse), so full decode at 1 frame / 3 s (about 95x realtime, about 1 min per recording) was chosen. |
| 12 | Failure: Hugging Face is unreachable from the dev machine (connect timeout), so faster-whisper model weights cannot be downloaded. | Whisper fallback is written and wired but **not tested on real audio**. This is stated in README, findings and explanation. The VTT path is the tested one. |
| 13 | First rubric run + leave-one-out. | Honest result: Excellent clearly separated; Poor/Average/Good muddled; one Poor class (B558) scores 71. Decision: do not tune weights to fit 8 points. |
| 14 | Hypothesis: the Poor classes are about tone ("energetic, pleasant"), so measure teacher vocal expressiveness by restricting audio to the teacher's VTT time spans (pitch std-dev, loudness dynamics). | Implemented and measured: **no signal** (Poor 2.9/3.8 semitones, Excellent 3.4, Good 2.8). Removed the code, recorded the negative finding in `docs/findings.md`. |
| 15 | Bug found by inspecting counts: `good` matched "Good evening", inflating praise (34 hits in one class). | Regex fixed with a negative lookahead; labels unchanged. Later also excluded "I'm good". |
| 16 | Malayalam demo: "very good" appears 55 times (ASR noise). | Added `english_rate` (share of common English words: 0.45-0.57 for English classes, 0.32 for the Malayalam demo). Below 0.40 the keyword items are switched off and the user is told why. |
| 17 | Read the generated explanations for 6 recordings instead of trusting aggregate metrics. | Found and fixed: duplicate monologue/silence observations, "I'm also good" quoted as praise, a bare "okay?" quoted as a comprehension check, lobby footage flagged as frozen video, adjacent dropouts listed separately, vague "e.g. around 00:57+" placeholder, excerpts cut before the matched word. |
| 18 | Privacy review of explanations: a child's name appeared in a quote because ASR mangled it so speaker-label matching missed it. | Added a second redaction pass (ALL-CAPS tokens and vocatives like "Hello Priya"), regression test added. Also noted in README that ASR-mangled names cannot be fully guaranteed redacted, which is another reason the LLM path is off by default. |
| 19 | App robustness test with Streamlit's AppTest: empty submit, loopback URL (SSRF guard), HTML page instead of video, full-result render for three recordings, a 4-minute clip end-to-end with and without VTT. | Fixed: transcript was not clipped to the analysed window; missing file raised a raw error; verdict without transcript data showed 36% confidence (now capped at 25% when under half the rubric has data). Replaced deprecated `use_container_width`. |
| 20 | Cut-offs. | Set once by eye to round numbers (42/56/72) and labelled as in-sample; the honest estimate is leave-one-out (4/8 exact, 6/8 within one). |
