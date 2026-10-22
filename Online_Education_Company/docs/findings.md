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

## 5. Results and honest validation

Rubric scores (0-100): Excellent 82/86, Good 66/49, Average 50/48, Poor 33/71.

* **In-sample** (cut-offs 42/56/72 set by eye on these same 8): exact 6/8, within one class 7/8.
* **Leave-one-out** (cut-offs refit as midpoints between class means on 7 recordings): exact **4/8**, within one class **6/8**, Spearman 0.69; majority baseline 2/8. This is the number to trust, and with n=8 it is a sanity check, not a performance claim.
* **Reliable:** Excellent vs. the rest (both Excellent score >=81, everything else <=71) and the weakest class when its problems are visible in interaction (B482: 33).
* **Misses, kept in the report:**
  * **B558 (Poor) scores 71.** The reviewer's complaints (weak intro/conclusion, no time for new joiners, not pleasant enough) are about tone and structure that keyword matching cannot see: it greets, asks "how are you", praises often. Its real, detectable issue (7.5 min with no child speaking) is reported in the observations, but the overall score is too high.
  * **B435 Good scores 49** and lands in Average: its transcript is sparse (246 cues) and has little praise and a 14-min silent stretch, while the reviewer valued intro and individual consideration.
  * The class means are not even monotone (Poor 52 > Average 49) because of B558, so the Poor/Average/Good boundaries are weakly supported by 2 examples each.
* Changes made after looking at results, listed so they are not mistaken for clean tuning: fixed "Good evening" being counted as praise, "I'm good" not counted as praise, ignored lobby footage before the class starts when flagging frozen video, merged adjacent dropouts. None of them changed a label. Cut-offs were set once, by eye.

## 6. Limitations to state plainly

Calibrated on 8 labelled classes; keyword cues on machine transcripts; tone, friendliness and the 8x8 background itself are **not** measured (a template detector would need the brand asset and more examples); face detection is coarse because the face is a small tile; without a VTT there are no speaker labels, so interaction cannot be assessed; the local Whisper fallback could not be run on real audio here because model downloads were blocked on this machine.
