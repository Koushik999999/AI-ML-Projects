**Approach.** I started from the reviewers' own notes (feedbacks.pdf), not generic teaching theory: rapport, asking children individually, energy, homework/conclusion, visible face and lighting. The app scores six weighted dimensions from signals computed locally (ffmpeg, OpenCV, numpy, faster-whisper): talk time, turns and silences from the speaker-labelled transcript; speech ratio and dead air from audio; face, shared screen, camera-off and frozen video from frames. Every observation has a timestamp and quote. Recordings stay local and are deleted after processing; the optional LLM narrative is off by default and sees only anonymised text.

**Judgement calls.** "Quality issue" classes are setup or platform faults, so they get a separate panel and aren't held against the teacher. With no transcript, the app transcribes locally and separates teacher/children by voice (~70% accurate), so who-spoke-when scores are dropped and a banner lists the missing signals. Clips under 20 min, or starting late, skip opening/closing checks (rapport, homework, goodbye).

**Hosting.** Hugging Face Docker Spaces were paid-only for my account, so it runs on Streamlit Community Cloud (free). With public videos, 5-min and 80-min clips without a transcript finished in 9 s and 122 s; Google Drive links gave identical results; YouTube links are rejected clearly.

**What worked.** Excellent is clearly separated (84-86 vs 75 or less); verdicts survived losing the transcript.

**What failed.** Leave-one-out is only 3/8 exact (6/8 within one class). A Poor class (B558) scores 75: its faults are tone, which keywords can't see. Three hypotheses (wait time, turn length, repetition) were contradicted by data and removed. Whisper writes Malayalam in Tamil script, so wording checks switch off.

**Limitations.** Eight labelled classes; hand-set cut-offs and 20/10-minute thresholds; tone and the 8x8 background unmeasured. Dropout detection can mistake natural silence in screen recordings for audio cut-outs. The 10-minute budget fallback was tested locally only.
