"""Rule-based, evidence-backed observations and suggestions (fully local, no network)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from src.scoring.technical import fmt_t

T = fmt_t


def anonymise(text: str, names: list[str], teacher: str | None) -> str:
    """Replace speaker names (full and word-level) with Teacher / Student A, B, ..."""
    out = text
    alias: dict[str, str] = {}
    stu = [n for n in names if n and n != teacher]
    for i, n in enumerate(stu):
        alias[n] = f"Student {chr(65 + i % 26)}"
    if teacher:
        alias[teacher] = "Teacher"
    for full, a in sorted(alias.items(), key=lambda kv: -len(kv[0])):
        for tok in [full] + [w for w in re.split(r"\s+", full) if len(w) >= 3]:
            out = re.sub(rf"\b{re.escape(tok)}\b", a, out, flags=re.I)
    # The platform ASR mangles names, so speaker labels alone miss them: also redact ALL-CAPS words and vocatives ("Hello Priya").
    out = re.sub(r"[A-Z]{3,}", "[name]", out)
    out = re.sub(r"((?:hello|hi|hey|dear|okay|ok|good (?:job|morning|evening)|well done|thank you|thanks|bye|yes|no)[,!]?\s+)([A-Z][a-z]{2,})",
                 lambda m: m.group(1) + "[name]", out)
    # The platform ASR mangles names, so speaker labels alone miss them: also redact ALL-CAPS words and vocatives ("Hello Priya").
    out = re.sub(r"\b[A-Z]{3,}\b", "[name]", out)
    out = re.sub(r"\b((?i:hello|hi|hey|dear|okay|ok|good job|good morning|good evening|well done|thank you|thanks|bye|yes|no)[,!]?\s+)(?!Student\b|Teacher\b)([A-Z][a-z]{2,})\b",
                 lambda m: m.group(1) + "[name]", out)
    return out


@dataclass
class Observation:
    dimension: str
    polarity: str        # "strength" | "issue"
    importance: float    # 0..1, used to rank
    text: str
    at: float | None = None
    suggestion: str | None = None


def _q(t: str, names, teacher) -> str:
    return '"' + anonymise(t, names, teacher).strip()[:90] + '"'


def observations(f: dict, names: list[str] | None = None, teacher: str | None = None) -> list[Observation]:
    t, a, v = f.get("transcript") or {}, f.get("audio") or {}, f.get("video") or {}
    names = names or []
    obs: list[Observation] = []
    if t.get("ok") and t.get("has_speakers"):
        ev = t["evidence"]
        span_min = (t["session_end_s"] - t["session_start_s"]) / 60
        # --- issues ---
        m = (t["longest_monologues"] or [None])[0]
        if m and m["end"] - m["start"] >= 240:
            L = m["end"] - m["start"]
            obs.append(Observation("Structure & clarity", "issue", min(1, L / 600),
                                   f"Teacher spoke almost uninterrupted from {T(m['start'])} to {T(m['end'])} ({L / 60:.0f} min {L % 60:.0f}s) with only one-word replies from children.",
                                   m["start"], "Break long explanations into 60-90 s chunks and ask a child to show or say the next step after each."))
        ss = (t["student_silent_stretches"] or [None])[0]
        if m and ss and min(m["end"], ss["end"]) - max(m["start"], ss["start"]) >= 0.7 * min(m["end"] - m["start"], ss["end"] - ss["start"]):
            # same stretch seen two ways: keep the single most informative sentence
            obs = [o for o in obs if not o.text.startswith("Teacher spoke almost uninterrupted")]
            L = max(m["end"], ss["end"]) - min(m["start"], ss["start"])
            obs.append(Observation("Individual interaction", "issue", min(1, L / 600),
                                   f"From {T(min(m['start'], ss['start']))} to {T(max(m['end'], ss['end']))} ({L / 60:.0f} min {L % 60:.0f}s) the teacher talked on while no child spoke.",
                                   min(m["start"], ss["start"]), "Break long explanations into 60-90 s chunks and call a child by name after each."))
        elif ss and ss["end"] - ss["start"] >= 180:
            L = ss["end"] - ss["start"]
            obs.append(Observation("Individual interaction", "issue", min(1, L / 600),
                                   f"No child spoke for {L / 60:.1f} min between {T(ss['start'])} and {T(ss['end'])}.",
                                   ss["start"], "Call a child by name every 2-3 minutes, even during demonstrations."))
        fs = t.get("first_student_after_s")
        if fs is not None and fs > 150:
            obs.append(Observation("Rapport & opening", "issue", min(1, fs / 600),
                                   f"The first child spoke {fs / 60:.1f} min after the class began (at {T(t['session_start_s'] + fs)}).",
                                   t["session_start_s"], "Open with a quick round: ask each child one easy personal or recap question in the first 2 minutes."))
        if t["student_turns_per_min"] < 3.0 and t["n_student_turns"] > 0:
            obs.append(Observation("Individual interaction", "issue", 0.8,
                                   f"Children spoke only {t['student_turns_per_min']:.1f} times per minute and {t['n_students_asked_individually']} child(ren) answered a direct question; students had {100 - t['teacher_talk_share'] * 100:.0f}% of the talk time.",
                                   None, "Aim for at least 4-5 child turns per minute: ask one child, then ask another to comment on the answer."))
        if t["student_top_share"] > 0.5 and t["n_students_spoke"] >= 3:
            obs.append(Observation("Individual interaction", "issue", 0.6,
                                   f"One child accounted for {t['student_top_share'] * 100:.0f}% of all student turns while {t['n_students_spoke'] - 1} others spoke much less.",
                                   None, "Rotate questions so quieter children are called on by name."))
        if t["n_unanswered_questions"] >= 5 and ev.get("unanswered"):
            ux = ev["unanswered"][0]
            obs.append(Observation("Individual interaction", "issue", 0.55,
                                   f"{t['n_unanswered_questions']} teacher questions got no spoken reply within 20 s, e.g. {_q(ux[1], names, teacher)} at {T(ux[0])}.",
                                   ux[0], "Wait 5 s after a question and re-address it to a named child before moving on."))
        if not t["has_rapport"]:
            q0 = ev["greet"][0] if ev["greet"] else None
            obs.append(Observation("Rapport & opening", "issue", 0.6,
                                   "No rapport-building check-in ('how are you / how was your day') was found in the opening minutes" + (f"; the class opened with {_q(q0[1], names, teacher)} at {T(q0[0])}." if q0 else "."),
                                   q0[0] if q0 else None, "Spend the first 2-3 minutes on a friendly check-in before revising or teaching."))
        if not t["has_homework"]:
            obs.append(Observation("Structure & clarity", "issue", 0.5, "No homework was assigned (no mention of homework/assignment anywhere in the transcript).", None,
                                   "End every class by assigning a small homework task and saying it out loud."))
        if not t["has_closing"] and not t["has_recap"]:
            obs.append(Observation("Structure & clarity", "issue", 0.5, "The class ended without a recap or a closing (no summary of what was learned, no goodbye/next-class line in the last 15%).", t["session_end_s"],
                                   "Reserve the last 3 minutes: 'today we learned...', homework, goodbye."))
        if t["praise_per_10min"] < 2.0:
            obs.append(Observation("Energy & positivity", "issue", 0.5, f"Only {t['praise_count']} praise phrase(s) in {span_min:.0f} min of class ({t['praise_per_10min']:.1f} per 10 min).", None,
                                   "Praise specific effort ('good thinking on that move!') at least once a minute."))
        if t["tech_chatter_count"] >= 8:
            pass  # reported under platform faults, not as a teaching issue
        # --- strengths ---
        if t["n_students_asked_individually"] >= 4 and t["student_turns_per_min"] >= 4:
            obs.append(Observation("Individual interaction", "strength", 0.8,
                                   f"{t['n_students_asked_individually']} different children answered direct questions and children spoke {t['student_turns_per_min']:.1f} times per minute; median reply came {t['median_response_latency_s']:.1f}s after a question." if t["median_response_latency_s"] is not None else
                                   f"{t['n_students_asked_individually']} different children answered direct questions.", None))
        if t["praise_per_10min"] >= 5 and ev["praise"]:
            p = ev["praise"][0]
            obs.append(Observation("Energy & positivity", "strength", 0.7, f"Frequent encouragement ({t['praise_count']} praise phrases, e.g. {_q(p[1], names, teacher)} at {T(p[0])}).", p[0]))
        if t["has_rapport"] and ev["rapport"]:
            r = ev["rapport"][0]
            obs.append(Observation("Rapport & opening", "strength", 0.6, f"Warm opening with a personal check-in at {T(r[0])}: {_q(r[1], names, teacher)}.", r[0]))
        if t["has_homework"] and ev["homework"]:
            h = ev["homework"][0]
            obs.append(Observation("Structure & clarity", "strength", 0.5, f"Homework was assigned at {T(h[0])}: {_q(h[1], names, teacher)}.", h[0]))
        if t["has_recap"] and t["has_closing"]:
            obs.append(Observation("Structure & clarity", "strength", 0.45, f"Clear structure: recap at {T(ev['recap'][0][0])} and a proper close at {T(ev['closing'][0][0])}.", ev["recap"][0][0]))
        if t["check_per_10min"] >= 8:
            c = ev["check"][0]
            obs.append(Observation("Structure & clarity", "strength", 0.4, f"Regular comprehension checks ({t['check_per_10min']:.0f} per 10 min, e.g. {_q(c[1], names, teacher)} at {T(c[0])}).", c[0]))
    elif t and not t.get("has_speakers", True):
        obs.append(Observation("Individual interaction", "issue", 0.2, "The transcript has no speaker labels, so teacher/student talk balance and individual interaction could not be measured.", None,
                               "Supply the platform VTT (with speaker names) for a full assessment."))
    if a.get("ok"):
        s, e = (t.get("session_start_s", 0), t.get("session_end_s", a["duration_s"])) if t.get("ok") else (0, a["duration_s"])
        inside = [p for p in a["long_pauses"] if p["start"] >= s - 1 and p["end"] <= e + 1]
        inside.sort(key=lambda p: p["start"] - p["end"])
        if inside and inside[0]["end"] - inside[0]["start"] >= 40:
            p = inside[0]
            obs.append(Observation("Pacing & flow", "issue", min(1, (p["end"] - p["start"]) / 180),
                                   f"Dead air: no speech for {p['end'] - p['start']:.0f}s from {T(p['start'])} to {T(p['end'])} ({len(inside)} pauses over 8 s in total).", p["start"],
                                   "If children are working silently, give a time-box ('2 minutes, then tell me your move') so silence has a purpose."))
        if a["speech_ratio"] < 0.4:
            obs.append(Observation("Pacing & flow", "issue", 0.5, f"Only {a['speech_ratio'] * 100:.0f}% of the recording contains speech; the class is mostly silent.", None))
    if v.get("ok") and v["camera_off_runs"]:
        r = v["camera_off_runs"][0]
        obs.append(Observation("Presentation", "issue", 0.5, f"Screen went black / camera was off for {r['end'] - r['start']:.0f}s from {T(r['start'])} to {T(r['end'])}.", r["start"], "Keep the camera on while teaching so children can see the teacher."))
    return obs


def pick(obs: list[Observation], lo: int = 3, hi: int = 6) -> list[Observation]:
    """Top issues first (what the teacher should act on), balanced with strengths; chronological within each group."""
    issues = sorted([o for o in obs if o.polarity == "issue"], key=lambda o: -o.importance)
    strengths = sorted([o for o in obs if o.polarity == "strength"], key=lambda o: -o.importance)
    n_i = min(len(issues), 3 if strengths else hi)
    n_s = min(len(strengths), hi - n_i, 3)
    chosen = issues[:n_i] + strengths[:n_s]
    if len(chosen) < lo:
        chosen += [o for o in issues[n_i:] + strengths[n_s:]][: lo - len(chosen)]
    return chosen[:hi]
