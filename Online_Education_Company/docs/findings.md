# Findings

Recordings are referred to by batch code only. All numbers come from `scripts/analyze.py` (output kept in the git-ignored `outputs/`).

## 1. What the human feedback says "good" means (`feedbacks.pdf`)

The PDF is a short per-batch note, written by a reviewer. It is the ground truth for the rubric:

| Rating | Praised | Criticised |
|---|---|---|
| Excellent (B491, B472) | one-to-one interaction, questions asked to children *individually*, rapport building, "consider everyone", homework given, topic videos | none |
| Good (B552, B435) | good intro, fixed 8x8 background, homework (B552) | "need more pleasant interaction"; B435: "should give HWs" |
| Average (B516, B435) | background kept, individual consideration, homework (B516) | "clarity issues with the background", "need more energetic communication", "more pleasant interaction", "sit where there is light", B435: no HW |
| Weak (B558, B482) | background kept, B482 asked individually | "need a better intro and conclusion", **no time for new joiners to introduce themselves**, "directly go to revision without rapport building", "need more energetic and pleasant interaction", **camera sometimes off while teaching** |
| Known quality issues (B392, B441) | B392: interaction was there | **no 8x8 background** (B392), **face not visible** (B441), no rapport, "happier communication", "informed about the quality issues several times" |

Rubric dimensions derived from this: **Rapport & opening**, **Individual interaction**, **Energy & positivity**, **Structure & clarity** (checks, recap, closing, homework), **Pacing & flow**, **Presentation** (face/screen visible, camera on, lighting).

## 2. Data facts

* 12 recordings, 1080p/25 fps/stereo 48 kHz, 38-89 min. Every recording has a speaker-labelled WebVTT, so teacher vs. student talk time is measured directly.
* Teacher = speaker with most words: correct for all 9 recordings where ground truth could be matched (names from the PDF, never printed).
* The VTT is **machine-generated**: names are mangled, and the "Malayalam" demo contains *no Malayalam script* (0 characters), only phonetic English-looking noise. The share of common English words is 0.45-0.57 in every English class and **0.32** in the Malayalam demo, which is how the app detects an unreliable transcript and switches off keyword checks.
* Audio is digitally clean (noise floor about -85 dB: platform noise gating). Noise/SNR is therefore a useless signal here; speech ratio and dead air are the informative ones.
* The video is a single-tile recording, mostly **shared screen (60-95% of frames)**; the teacher's face is a small tile, so face-based signals are coarse.

## 3. How the extra folders were treated

* `weak` -> **Poor** (confirmed by the PDF: "Weak").
* `quality issue` -> **not forced into the four labels.** The PDF shows these are *setup* problems (no branded background, face not visible, rapport). They are used to build the technical detection and are reported in a separate "Technical & platform flags" panel. Findings: B441 has the lowest face visibility of all recordings (1% of frames, matching "can't see his face"), 13 connection-chatter mentions ("can you hear me") and audio dropouts; B392 has 8 chatter mentions and frozen-video stretches. A **platform fault** (dropouts, frozen video, connection chatter) is not held against the teacher: when two different kinds occur, the Presentation dimension is excluded from the score. A **setup issue** (camera off, dim face, nothing visible) is reported *and* scored, because the reviewers treat it as a quality factor.
* `demo` -> not rated (different purpose). Used as extra validation: the Malayalam demo exposed the garbled-transcript failure mode above, and the English demo gets Good/59.

## 4. Which signals separate the classes (8 labelled recordings, Spearman rho vs. ordinal label)

| Signal | Poor | Avg | Good | Excel | rho | Verdict |
|---|---|---|---|---|---|---|
| student turns per min | 4.0 | 2.5 | 5.0 | 8.4 | +0.67 | **useful** |
| median reply latency (s) | 1.1 | 2.4 | 0.8 | 0.5 | -0.71 | **useful** |
| longest teacher monologue (s) | 747 | 429 | 417 | 98 | -0.71 | **useful** |
| longest stretch with no child speaking (s) | 522 | 195 | 472 | 68 | -0.69 | **useful** |
| speech ratio (audio) | 0.44 | 0.51 | 0.52 | 0.71 | +0.69 | **useful** |
| praise per 10 min | 5.6 | 1.4 | 2.0 | 7.7 | +0.45 | partly (Poor B558 has a lot of "great/excellent") |
| teacher talk share | 0.68 | 0.68 | 0.51 | 0.55 | -0.50 | partly: **more teacher talk is not simply bad** (Intermediate Excellent has 47%, Beginner Excellent 62%) |
| share of one child's turns | 0.45 | 0.43 | 0.35 | 0.47 | -0.02 | **misleading**: excellent classes also have a dominant child |
| energetic wording (!, "wow") | 0.37 | 0.61 | 0.17 | 0.35 | -0.10 | **misleading** in ASR text |
| teacher vocal pitch variation (tested, **not used**) | 2.9-3.8 st | 3.5-4.1 | 2.7-3.0 | 3.4 | none | no signal: I tried it as a proxy for "energetic" and dropped it |
| median speech loudness (-29 to -24 dB) | -28.9 | -27.3 | -24.9 | -24.4 | +0.74 | **not used**: a ~5 dB spread reflects microphone gain and platform levelling, not teaching quality |
| black-screen share | 0.00 | 0.00 | 0.00 | 0.01 | +0.74 | **not used as a quality signal**: the correlation comes from a single recording with a 30 s black stretch; kept only as a camera-off flag |
| noise floor, clipping | | | | | | uninformative (clean platform audio) |

Level matters: the same signal has different baselines. Intermediate classes have fewer, longer child turns (student turns/min 1.7-2.4 for the three non-excellent Intermediate classes vs. 3.3-5.6 for the non-excellent Beginner ones; Excellent: 7.4 vs. 9.4) and longer teacher stretches because children work on a board while the teacher is silent. The rubric uses the same ranges for both levels (no level input exists for an unseen upload), which is a known weakness.

## 5. Results and honest validation (round 2: before / after)

Cut-offs were **not changed** (42 / 56 / 72). "v1" = rubric of round 1. "v3" = after adding general interaction features (below).

| | v1 | v3 (current) |
|---|---|---|
| Scores: Excellent | 82 / 86 | 84 / 86 |
| Scores: Good | 66 / 49 | 68 / 48 |
| Scores: Average | 50 / 48 | 52 / 50 |
| Scores: Poor | 33 / **71** (B482 / B558) | 35 / **75** |
| In-sample exact / within one (cut-offs set by eye on the same 8) | 6/8, 7/8 | 6/8, 7/8 |
| **Leave-one-out** exact / within one | **4/8**, 6/8 | **3/8**, 6/8 |
| Spearman(score, label) | 0.69 | 0.67 |
| Majority-class baseline | 2/8 | 2/8 |

**Result: no improvement; slightly worse.** B558 (Poor) went from 71 to 75, so it is still scored Excellent in-sample. The one-recording drop in leave-one-out (4/8 -> 3/8) comes from the refit cut-offs moving, i.e. it is noise at n=8, but it is not better either.

### The new general features and what happened to each

Definitions and the "good" direction were fixed **before** looking at any result; none was designed around B558.

| Feature | Expected | Observed across the 8 (Spearman) | Decision |
|---|---|---|---|
| student-initiated turns per min (child speaks without a teacher question just before) | more is better | +0.67 (Excellent 3.7, Good-B552 3.6, Poor 0.9 / 2.2) | **kept** |
| share of teacher questions that get an answer within 20 s | more is better | +0.43, but 0.73-0.99 everywhere (saturates) | **kept**, low information |
| wait (silence) after a question before anyone speaks | 1.5-6 s is better ("think time") | **-0.62**: the best classes wait least (0.5 s); it is reply latency in disguise | **removed** (premise contradicted) |
| teacher turn length, 90th percentile words | shorter is better | **+0.50**: wrong sign (Excellent 25, Average 32) | **removed** (flipping the sign to fit would be fitting) |
| near-repeated teacher instruction (Jaccard >= 0.8 within 2 min) | less is better | 0-3% in every class; sign opposite | **removed** (no information at this base rate) |

Why B558 does not move: its remaining deficits per the reviewer (weak intro/conclusion, no time for new joiners, not "energetic and pleasant") are tone and structure. Its children do speak up on their own (2.2 initiated turns/min) and its questions are answered (0.98), so general interaction features rightly score it well. **These features cannot, and should not, be expected to fix it.**

### Confidence (changed)

Old confidence ignored how weakly the labels are supported. New formula: `label ceiling x boundary distance x signal availability x signal reliability`.
* boundary distance: 0.25 on a cut-off rising to 1.0 at 15+ points away;
* ceilings from the validation above: Excellent 0.85, Poor/Average/Good 0.65 (2 examples each);
* availability: share of rubric weight that had data (under half caps at 0.25); reliability x0.85 for a local-ASR transcript, x0.85 for a garbled language.
Examples: clear Excellent B491 0.82; borderline Average B435 0.28; Good B552 0.28; the B558 miss 0.35 (3 points under the Excellent cut); Malayalam demo 0.23.

### What to trust

* **Reliable:** Excellent vs the rest, and a very weak interaction profile (B482).
* **Not reliable:** Poor vs Average vs Good ordering, and any single mid-range score. B558 is an acknowledged miss; B435-Good (48) lands in Average because its transcript is sparse and has a 14-minute silent stretch.
* Earlier post-hoc bug fixes (listed so they are not mistaken for tuning): "Good evening" no longer counts as praise, "I'm good" ignored, lobby footage before the session ignored for frozen video, adjacent dropouts merged. None changed a label.

## 6. No-transcript path (the likely test scenario)

The organisers may upload an `.mp4` with no `.vtt`. The app then runs **local faster-whisper** (int8, CPU, 5-minute windows, time budget, progress messages), then infers teacher/children from voice.

**Measured here on real audio** (model `tiny`, int8, on the development laptop's CPU; the platform transcript is the reference, which is itself machine-made):

| Recording | Audio | Transcription time | Word-overlap F1 vs platform transcript | Speaker split agreement | Verdict with VTT -> without VTT (confidence) |
|---|---|---|---|---|---|
| B491 (Excellent) | 53.9 min | 3.0 min (0.06x realtime) | 0.80 | 0.68 | Excellent -> Excellent (0.82 -> 0.17) |
| B482 (Poor) | 59.2 min | 1.1 min (0.02x; VAD skips silence) | 0.79 | 0.72 | Poor -> Poor (0.48 -> 0.46) |

Two recordings, so this shows the path works and the verdict can survive, not that it always will. A free-tier CPU will be several times slower than this laptop: the 10-minute budget may transcribe only part of a long class (the app says so and lowers confidence).

**Speaker separation without labels** (`scripts/speaker_eval.py`, ground truth = VTT speaker names, time-weighted, 12 recordings):

| Method | Accuracy | "Call everyone Teacher" baseline |
|---|---|---|
| pitch + spectral centroid, 2-means | 0.63 | 0.64 (**no better than baseline**) |
| voice timbre (mean log-mel), 2-means, bigger cluster = Teacher | **0.68** | 0.64 |

It beats the baseline on 8 of 12 recordings and is inverted (roles swapped) on 4 (e.g. B435-Good 0.07, B558 0.36), and its own separation score does not predict which. **Decision:** the split is shipped as approximate, the app says so, and all role-dependent scoring items (child turns, latency, initiated turns, answered share, monologue, talk balance) are **switched off** when roles are inferred. Wording cues are computed over all speech instead, so a mislabelled role cannot hide or invent a "teacher said it" cue. Consequence: without a VTT the "Individual interaction" dimension is n/a, coverage drops to about 0.72, and confidence is lowered and the missing signals are listed in a banner.

**Malayalam, tested on the Malayalam demo (5 min):** Whisper `tiny` and `base` both detect language `ml` but write the text in **Tamil script** (about 310 non-Latin characters, 0 Malayalam script), i.e. the output is wrong, not just noisy. Its English-word rate is 0.18 (< 0.40), so the garbled-language guard switches off the wording checks and the verdict is built from audio, video and, only if a VTT exists, turn-taking. A larger Whisper model would be needed for real Malayalam support; it is not feasible on a free CPU tier.

Failure behaviour (tested): model cannot load -> `WhisperUnavailable` -> verdict from audio/video only, banner "transcript and who-said-what: unavailable, reason ...", confidence capped at 0.25; time budget hit -> partial transcript with a warning; Whisper fails mid-way -> keeps the transcript so far.
Network note: Hugging Face was unreachable from this machine at the start of the session and reachable later (intermittent); the model download that finally worked is what made the real evaluation above possible. On the Space the model is baked into the Docker image.

## 7. Partial recordings (clips, late starts, cut-off analysis)

**Problem.** A clip from the middle of a lesson has no greeting, recap, goodbye or homework only because those moments are not in it. Scoring their absence is a measurement error, and so is praising their presence.

**General rule** (round-number thresholds, not fitted to any sample class; `src/scoring/partial.py`):

| Trigger | Opening checks (rapport check-in, greeting, new-joiner intro) | Closing checks (homework, recap, closing) |
|---|---|---|
| recording shorter than 20 min | not assessable | not assessable |
| first speech after 10 min | not assessable | not assessable |
| analysis cut off before the end (90-min cap, or Whisper time budget hit) | assessed | not assessable |

What changes: those items are marked "not assessable on a partial recording", left out of the score **and** of the "is there enough evidence" threshold, so the remaining items in the same dimension are reweighted (a dimension whose items are all opening-only, "Rapport & opening", drops out and the other dimensions are reweighted by the existing mechanism). The explainer stops reporting absent *or* present opening/closing behaviour. Per-minute rate signals are untouched: praise rate, talk balance, child turns, reply latency, silences, monologues, pacing, presentation. The result shows a banner naming the reason and the checks that were skipped. Confidence is multiplied by 0.8 (opening and closing skipped) or 0.9 (end only), on top of the existing coverage term.

**Effect on the labelled classes: none.** All local recordings run 38-89 min and start speaking between 0:21 and 4:08, so none is partial. I re-ran the analysis and diffed it against the saved pre-change output: raw feature table, per-class scores, in-sample result, leave-one-out (3/8 exact, 6/8 within one) and Spearman (0.67) are byte-identical, and label, score and confidence for six spot-checked recordings are identical.

**Real-data check.** A 4-minute clip taken from minute 10 of an Excellent class (with its re-timed transcript): Rapport & opening is n/a, six checks are listed as not assessable, the score rests on interaction, energy, the remaining structure items (comprehension checks, monologue), pacing and presentation (Excellent, 75, confidence 0.25), and the praise rate and talk share are still reported.

**Caveats.** After reweighting, "Structure & clarity" on a clip rests on only two items (comprehension checks and longest monologue), so it is a thin dimension there. The 20-minute and 10-minute thresholds are conventions: a 25-minute lesson that is genuinely short would be treated as complete. A clip whose transcript timestamps are re-based to 0:00 can only be caught by its duration.

## 8. Limitations to state plainly

Calibrated on 8 labelled classes (2 per label); keyword cues on machine transcripts; tone, friendliness and the 8x8 background itself are **not** measured; the teacher's face is a small tile so face signals are coarse; Malayalam is not handled by either ASR (see section 6), so wording cues switch off there; the speaker split without a VTT is only about 70% right; the Docker/Space deployment and the Streamlit Cloud deployment have not been run.
