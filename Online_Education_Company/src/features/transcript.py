"""Transcript-derived interaction and pedagogy features, with timestamps for evidence.

Works on speaker-labelled cues (platform VTT). Without speaker labels (e.g. local Whisper output)
teacher/student split is unavailable and `has_speakers` is False.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from src.vtt import Cue

# --- lexicons (English; the platform ASR emits Latin script even for Malayalam speech) ---
PRAISE = re.compile(r"\b(good(?!\s+(?:morning|evening|afternoon|night|bye|day|luck))|very good|great|excellent|well done|super|perfect|wonderful|nice|awesome|brilliant|"
                    r"fantastic|amazing|bravo|exactly|clap|keep it up|proud|superb|smart)\b", re.I)
CHECK = re.compile(r"\b(understood|understand|got it|caught it|clear|any doubt|any question|do you know|"
                   r"makes sense|are you with me|can you see|can you hear)\b|(ok|okay|right)\?", re.I)
GREET = re.compile(r"\b(how are you|how was your|good (morning|evening|afternoon)|welcome|nice to see|hello|hi)\b", re.I)
INTRO = re.compile(r"\b(introduce yourself|your name|tell (me|us) about yourself|new (joiner|student|friend)|"
                   r"say hi to|meet our|self[- ]?introduction|introduction)\b", re.I)
HOMEWORK = re.compile(r"\b(home ?work|assignment|practice (at|in) home|worksheet|project work|task for)\b", re.I)
RECAP = re.compile(r"\b(today we (learn|learned|learnt|did|covered)|recap|summar(y|ise|ize)|revise|revision|"
                   r"what did we learn|what we learn)", re.I)
CLOSING = re.compile(r"\b(see you|next class|next session|bye|thank you|thanks for|that'?s all for today|"
                     r"we will meet|class is over|end of (the )?class|time is up)\b", re.I)
PREV = re.compile(r"\b(last class|previous class|last session|last time|yesterday|we learned|we learnt)\b", re.I)
TECH = re.compile(r"\b(can you hear|can'?t hear|not (able to )?hear|unmute|mute|camera|network|internet|connection|"
                  r"audio|sound|lag|freez|frozen|disconnect|rejoin|reconnect|share (my )?screen|not visible|can'?t see)\b", re.I)
OPEN_Q = re.compile(r"\b(why|how|what|which|where|who|explain|describe|tell me)\b", re.I)
QSTART = re.compile(r"^(can|could|do|does|did|is|are|was|were|will|would|have|has|should|shall)\b", re.I)
ENERGY = re.compile(r"(!|\b(wow|yay|hurray|great|awesome|super|fun|let'?s|come on|amazing)\b)", re.I)
COMMON_EN = frozenset("the a an is are was to and you your it of in that we this i do what can so okay yes no now will on for have with be not "
                      "let me my he she they there here how why when which one two three move next if then or but all very good like just up out see well right at as by from".split())
SELF_GOOD = re.compile(r"(i'?m|i am|am)\s+(also\s+|very\s+|so\s+)?(good|great|fine|nice)", re.I)
BARE_TAG = re.compile(r"(ok|okay|right)\?")
RAPPORT = re.compile(r"how are you|how was|how'?s your|how is your|are you ready|how('| i)?s it going", re.I)


@dataclass
class Turn:
    start: float
    end: float
    speaker: str
    text: str


def pick_teacher(cues: list[Cue]) -> str | None:
    """Teacher = speaker with most words (true for 9/9 recordings with known teachers).
    If the runner-up is within 15% and asks clearly more questions/instructions, prefer the runner-up."""
    w: Counter[str] = Counter()
    q: Counter[str] = Counter()
    for c in cues:
        if c.speaker:
            w[c.speaker] += c.words
            q[c.speaker] += c.text.count("?") + bool(re.search(r"\b(okay|let'?s|now|next|today)\b", c.text, re.I))
    if not w:
        return None
    (a, wa), *rest = w.most_common()
    if rest and rest[0][1] >= 0.85 * wa and q[rest[0][0]] > q[a] * 1.25:
        return rest[0][0]
    return a


def merge_turns(cues: list[Cue], gap: float = 1.5) -> list[Turn]:
    """Merge consecutive cues from the same speaker (gap < `gap` s) into turns."""
    turns: list[Turn] = []
    for c in sorted(cues, key=lambda c: c.start):
        sp = c.speaker or "?"
        if turns and turns[-1].speaker == sp and c.start - turns[-1].end < gap:
            t = turns[-1]
            t.end = max(t.end, c.end)
            t.text += " " + c.text
        else:
            turns.append(Turn(c.start, c.end, sp, c.text))
    return turns


def _is_question(t: str) -> bool:
    return "?" in t or bool(QSTART.match(t.strip()))


def transcript_features(cues: list[Cue], media_duration: float | None = None) -> dict:
    cues = [c for c in cues if c.text.strip()]
    if not cues:
        return {"ok": False, "reason": "empty transcript"}
    has_speakers = any(c.speaker for c in cues)
    teacher = pick_teacher(cues) if has_speakers else None
    first, last = cues[0].start, cues[-1].end
    dur = media_duration or last
    span = max(last - first, 1.0)
    is_t = lambda c: (c.speaker == teacher) if teacher else True  # noqa: E731
    t_cues = [c for c in cues if is_t(c)]
    s_cues = [c for c in cues if teacher and not is_t(c)]
    t_time = sum(min(c.end - c.start, 15) for c in t_cues)
    s_time = sum(min(c.end - c.start, 15) for c in s_cues)
    t_words, s_words = sum(c.words for c in t_cues), sum(c.words for c in s_cues)
    turns = merge_turns(cues)
    t_turns = [t for t in turns if t.speaker == teacher]
    s_turns = [t for t in turns if teacher and t.speaker != teacher]

    stu = Counter(c.speaker for c in s_cues if c.speaker)
    stu_turns = Counter(t.speaker for t in s_turns)
    substantial = {s for s, n in stu_turns.items() if n >= 3}
    top_share = max(stu_turns.values(), default=0) / (sum(stu_turns.values()) or 1)

    # teacher questions -> next non-teacher turn = student response
    questions, latencies, unanswered = [], [], []
    unanswered_ex: list[tuple[float, str]] = []
    for i, t in enumerate(turns):
        if t.speaker != teacher:
            continue
        sentences = re.split(r"(?<=[?.!])\s+", t.text)
        qs = [s for s in sentences if _is_question(s)]
        for s in qs:
            questions.append({"t": t.start, "text": s[:140], "open": bool(OPEN_Q.search(s)) and not QSTART.match(s.strip())})
        if qs and _is_question(sentences[-1]):
            nxt = next((u for u in turns[i + 1:i + 4] if u.speaker != teacher), None)
            if nxt and nxt.start - t.end < 20:
                latencies.append(max(0.0, nxt.start - t.end))
            else:
                unanswered.append(t.end)
                unanswered_ex.append((t.start, qs[-1][:120]))
    n_open = sum(q["open"] for q in questions)

    # teacher-only stretches (student backchannels of <=2 words do not break a monologue)
    mono: list[tuple[float, float]] = []
    cur_s = cur_e = None
    for c in cues:
        if is_t(c) or c.words <= 2:
            cur_s = c.start if cur_s is None else cur_s
            cur_e = c.end
        elif cur_s is not None:
            mono.append((cur_s, cur_e))
            cur_s = None
    if cur_s is not None:
        mono.append((cur_s, cur_e))
    mono.sort(key=lambda m: m[1] - m[0], reverse=True)

    # stretches with no student speech at all (>= 2 words), measured inside the session
    st_times = sorted(c.start for c in s_cues if c.words >= 2)
    first_student = st_times[0] if st_times else None
    edges = [first] + st_times + [last]
    gaps = sorted(((b - a, a, b) for a, b in zip(edges, edges[1:])), reverse=True)
    silent_stretches = [{"start": a, "end": b} for g, a, b in gaps[:3] if g >= 120] if teacher else []

    scs = sorted(cues, key=lambda c: c.start)
    overlaps =[b.start for a, b in zip(scs, scs[1:]) if a.speaker != b.speaker and b.start < a.end - 0.5]

    def hits(rx: re.Pattern, who: list[Cue], pred=lambda c: True) -> list[tuple[float, str]]:
        out = []
        for c in who:
            m = rx.search(c.text) if pred(c) else None
            if m:  # excerpt centred on the match so the cited phrase is always visible
                out.append((c.start, c.text[max(0, m.start() - 45): m.end() + 60]))
        return out

    early = lambda c: c.start - first < 0.12 * span  # noqa: E731
    late = lambda c: c.start - first > 0.85 * span  # noqa: E731
    praise = [(c.start, c.text[:120]) for c in t_cues if PRAISE.search(SELF_GOOD.sub("", c.text))]
    check = hits(CHECK, t_cues)
    check.sort(key=lambda h: bool(BARE_TAG.search(h[1].lower())))  # real checks ('understood?', 'any doubt?') before a bare "okay?"
    greet = hits(GREET, t_cues, early)
    rapport = hits(RAPPORT, t_cues, early)
    intro = hits(INTRO, cues, lambda c: c.start - first < 0.4 * span)
    hw = hits(HOMEWORK, t_cues)
    recap = hits(RECAP, t_cues, lambda c: c.start - first > 0.6 * span)
    closing = hits(CLOSING, t_cues, late)
    prev = hits(PREV, t_cues, lambda c: c.start - first < 0.3 * span)
    tech = hits(TECH, cues)
    energy = sum(len(ENERGY.findall(c.text)) for c in t_cues)

    # children individually engaged = answered within 10 s of a teacher turn ending in a question
    engaged: Counter[str] = Counter()
    for i, t in enumerate(turns[:-1]):
        if t.speaker == teacher and "?" in t.text[-60:]:
            for u in turns[i + 1:i + 3]:
                if u.speaker != teacher and u.start - t.end < 10:
                    engaged[u.speaker] += 1
                    break

    nb = int(dur // 60) + 1
    tb, sb = [0.0] * nb, [0.0] * nb
    for c in cues:
        (tb if is_t(c) else sb)[min(int(c.start // 60), nb - 1)] += min(c.end - c.start, 15)

    toks = [w for c in cues for w in re.findall(r"[a-z']+", c.text.lower())]
    english_rate = sum(w in COMMON_EN for w in toks) / max(len(toks), 1)
    per_min = lambda n: n / max(span / 60, 1e-6)  # noqa: E731
    per_10 = lambda n: n / max(span / 600, 1e-6)  # noqa: E731
    return {
        "ok": True, "has_speakers": has_speakers, "n_cues": len(cues),
        # English classes score 0.45-0.57 on this; the Malayalam demo (garbled phonetic ASR) scores 0.32.
        "english_rate": english_rate, "lexicon_reliable": english_rate >= 0.40,
        "session_start_s": first, "session_end_s": last, "media_duration_s": dur,
        "tail_after_last_cue_s": max(0.0, dur - last),
        "n_students_spoke": len(stu), "n_students_substantial": len(substantial),
        "n_students_asked_individually": len(engaged), "student_top_share": top_share,
        "teacher_time_s": t_time, "student_time_s": s_time,
        "teacher_talk_share": t_time / max(t_time + s_time, 1e-6) if teacher else None,
        "teacher_words": t_words, "student_words": s_words,
        "teacher_words_per_min": t_words / (t_time / 60) if t_time else None,
        "n_teacher_turns": len(t_turns), "n_student_turns": len(s_turns),
        "student_turns_per_min": per_min(len(s_turns)),
        "n_questions": len(questions), "questions_per_min": per_min(len(questions)),
        "open_question_share": n_open / len(questions) if questions else 0.0,
        "median_response_latency_s": sorted(latencies)[len(latencies) // 2] if latencies else None,
        "n_unanswered_questions": len(unanswered),
        "first_student_after_s": (first_student - first) if first_student is not None else None,
        "student_silent_stretches": silent_stretches,
        "longest_student_silence_s": (gaps[0][0] if gaps and teacher else 0.0),
        "longest_monologues": [{"start": a, "end": b} for a, b in mono[:3]],
        "longest_monologue_s": (mono[0][1] - mono[0][0]) if mono else 0.0,
        "n_overlaps": len(overlaps), "overlaps_per_min": per_min(len(overlaps)),
        "praise_count": len(praise), "praise_per_10min": per_10(len(praise)),
        "check_count": len(check), "check_per_10min": per_10(len(check)),
        "energy_marks_per_min": per_min(energy),
        "has_greeting": bool(greet), "has_rapport": bool(rapport), "has_new_joiner_intro": bool(intro),
        "has_homework": bool(hw), "has_recap": bool(recap), "has_closing": bool(closing),
        "has_prev_class_revision": bool(prev), "tech_chatter_count": len(tech),
        "evidence": {"praise": praise[:5], "check": check[:5], "greet": greet[:2], "rapport": rapport[:2],
                     "intro": intro[:2], "homework": hw[:3], "recap": recap[:2], "closing": closing[:2],
                     "prev": prev[:2], "tech": tech[:6],
                     "questions": [(q["t"], q["text"]) for q in questions[:6]], "overlaps": overlaps[:5],
                     "unanswered": unanswered_ex[:5]},
        "talk_bins_teacher": tb, "talk_bins_student": sb,
        "_student_turn_counts": dict(stu_turns), "_teacher_label": teacher,
    }
