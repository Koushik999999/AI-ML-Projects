**Approach.** I started from the reviewers' own notes (feedbacks.pdf), not generic teaching theory: rapport, asking children individually, energy, homework/conclusion, visible face and lighting. The app scores six weighted dimensions from signals computed locally (ffmpeg, OpenCV, numpy, faster-whisper): talk time, turns and silences from the speaker-labelled transcript; speech ratio and dead air from audio; face, shared screen, camera-off and frozen video from frames. Every observation has a timestamp and quote. Recordings stay local and are deleted after processing; the optional LLM narrative is off by default and sees only anonymised text.

**Judgement calls.** "Quality issue" classes are setup or platform faults, so they get a separate panel; platform faults aren't held against the teacher. With no transcript, the app transcribes locally and separates teacher/children by voice, which was only ~70% accurate, so who-spoke-when scores are dropped and a banner lists the missing signals.

Clips are handled too: under 20 min, or starting late, opening and closing checks (rapport, homework, recap, goodbye) are marked not assessable and excluded, with a banner and lower confidence.

**What worked.** Excellent is clearly separated (84-86 vs 75 or less). On two classes the verdict survived losing the transcript.

**What failed.** Leave-one-out is only 3/8 exact (6/8 within one class; chance ~2/8). A Poor class (B558) scores 75: its faults are tone, which keywords can't see. New general interaction features didn't help it, and three of my hypotheses (wait time, turn length, repetition) were contradicted by the data and removed. Pitch variation and pitch-based speaker splitting were no better than baseline. Whisper writes Malayalam in Tamil script, so wording checks switch off there.

**Limitations.** Eight labelled classes; hand-set cut-offs; confidence is deliberately low near boundaries. Tone and the 8x8 background aren't measured. Free hosting may transcribe only part of a long class.
