"""Optional LLM narrative. OFF by default (EXPLAINER_PROVIDER=rule).

Privacy contract: the payload contains ONLY numeric features and short transcript excerpts in which every speaker
name has been replaced by Teacher / Student A / B. No audio, video or frames are ever sent. Using an external
provider with real recordings requires organiser approval (see README).
"""
from __future__ import annotations

import json
import os

import requests

from src.scoring.explain import anonymise

NUMERIC_KEYS = ["teacher_talk_share", "student_turns_per_min", "n_students_spoke", "n_students_asked_individually",
                "questions_per_min", "open_question_share", "median_response_latency_s", "longest_monologue_s",
                "longest_student_silence_s", "praise_per_10min", "check_per_10min", "has_rapport", "has_homework",
                "has_recap", "has_closing", "has_new_joiner_intro"]


def build_payload(result: dict, names: list[str], teacher: str | None, max_excerpts: int = 8) -> dict:
    f, sc = result["features"], result["score"]
    t = f.get("transcript") or {}
    nums = {k: t.get(k) for k in NUMERIC_KEYS if t.get(k) is not None}
    ev = t.get("evidence", {})
    excerpts = []
    for kind in ("questions", "praise", "rapport", "homework", "closing"):
        for ts, text in ev.get(kind, [])[:2]:
            excerpts.append({"kind": kind, "t": round(ts), "text": anonymise(text, names, teacher)})
    return {"rubric_label": sc["label"], "rubric_score": sc["overall"], "dimensions": sc["dimensions"],
            "features": nums, "excerpts": excerpts[:max_excerpts]}


def assert_payload_safe(payload: dict, names: list[str]) -> None:
    blob = json.dumps(payload).lower()
    for n in names:
        for tok in [n] + n.split():
            if len(tok) >= 3 and tok.lower() in blob:
                raise ValueError("Refusing to send: payload still contains a speaker name token.")


PROMPT = ("You are reviewing an online children's class using ONLY the numbers and anonymised excerpts below. "
          "Write 4 sentences: overall impression, the strongest observed behaviour, the biggest issue, and one concrete next step. "
          "Use timestamps (seconds) from the excerpts when you cite them. Do not invent facts.\n\n")


def llm_narrative(result: dict, names: list[str], teacher: str | None) -> str | None:
    provider = os.environ.get("EXPLAINER_PROVIDER", "rule").lower()
    key = os.environ.get("LLM_API_KEY", "")
    if provider == "rule" or not key:
        return None
    payload = build_payload(result, names, teacher)
    assert_payload_safe(payload, names)
    body = PROMPT + json.dumps(payload)
    try:
        if provider == "anthropic":
            r = requests.post("https://api.anthropic.com/v1/messages", timeout=40,
                              headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                              json={"model": os.environ.get("LLM_MODEL") or "claude-haiku-5-5", "max_tokens": 400,
                                    "messages": [{"role": "user", "content": body}]})
            r.raise_for_status()
            return r.json()["content"][0]["text"]
        if provider == "openai":
            r = requests.post("https://api.openai.com/v1/chat/completions", timeout=40,
                              headers={"Authorization": f"Bearer {key}"},
                              json={"model": os.environ.get("LLM_MODEL") or "gpt-4o-mini", "max_tokens": 400,
                                    "messages": [{"role": "user", "content": body}]})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception:  # noqa: BLE001 - never let the optional narrative break the assessment
        return None
    return None
