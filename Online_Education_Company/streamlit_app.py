"""Class Quality Assessor: upload (or link) an online class recording -> Poor / Average / Good / Excellent + evidence.

Privacy: everything is analysed locally inside this process; the recording and temp files are deleted afterwards.
No audio/video/frames are sent anywhere. An optional LLM narrative (off by default) receives anonymised text only.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from src.assess import assess
from src.fetch import FetchError, fetch
from src.llm import llm_narrative
from src.pipeline import analyze
from src.scoring.rubric import DIMENSIONS, LABELS
from src.scoring.technical import fmt_t

MAX_MIN = float(os.environ.get("MAX_VIDEO_MINUTES", 90))
MAX_SECONDS = float(os.environ.get("MAX_PROCESSING_SECONDS", 600))
MAX_UPLOAD_MB = float(os.environ.get("MAX_UPLOAD_MB", 1024))
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "tiny")
COLORS = {"Poor": "#c0392b", "Average": "#d68910", "Good": "#2e86c1", "Excellent": "#1e8449"}
TEACHER_C, STUDENT_C = "#2e5eaa", "#e08a1e"

st.set_page_config(page_title="Class Quality Assessor", page_icon="🎓", layout="wide")


@st.cache_resource(show_spinner="Preparing the local speech model (first run only)...")
def _warm_speech_model(size: str) -> str | None:
    """Load the Whisper model once per server process. Returns an error message, or None when ready."""
    from src.features.asr import WhisperUnavailable, load_model
    try:
        load_model(size)
        return None
    except WhisperUnavailable as e:
        return str(e)
st.title("🎓 Class Quality Assessor")
st.caption("Upload an 8x8 class recording (and its transcript if you have it) to get a quality verdict with evidence.")

with st.sidebar:
    st.header("Privacy")
    st.markdown("- Analysis runs **inside this app**; audio, video and frames are never sent to any external service.\n"
                "- The uploaded recording and temp files are **deleted** when processing ends.\n"
                "- Nothing is stored or logged.\n"
                "- An LLM summary is **off** unless the operator enables it; it would receive anonymised text and numbers only.")
    st.header("Options")
    use_asr = st.checkbox("Transcribe locally when no transcript is provided", value=True,
                          help=f"Runs the '{WHISPER_MODEL}' speech model on this server's CPU. Slower on free hosting; stops at the time budget. "
                               "Without a transcript the who-spoke-when (interaction) scores are not used.")
    asr_err = _warm_speech_model(WHISPER_MODEL) if use_asr and os.environ.get("PRELOAD_WHISPER", "1") == "1" else None
    if use_asr and os.environ.get("PRELOAD_WHISPER", "1") == "1":
        st.caption("Speech model: ready" if asr_err is None else f"Speech model unavailable: {asr_err}")
    st.caption(f"Limits: first {MAX_MIN:.0f} min analysed; {MAX_SECONDS / 60:.0f} min time budget.")

tab_up, tab_link = st.tabs(["Upload", "Paste link"])
with tab_up:
    up_video = st.file_uploader("Class recording", type=["mp4", "mov", "mkv", "webm", "m4v"])
    up_vtt = st.file_uploader("Transcript (optional, WebVTT with speaker names)", type=["vtt"], key="vtt1")
with tab_link:
    link = st.text_input("Direct video link or public Google Drive link")
    link_vtt = st.file_uploader("Transcript (optional)", type=["vtt"], key="vtt2")

go_btn = st.button("Assess class", type="primary")


def _render(res: dict) -> None:
    sc = res["score"]
    label = sc["label"]
    c1, c2, c3 = st.columns([1.2, 1, 1])
    c1.markdown(f"<div style='font-size:14px;color:#666'>Verdict</div><div style='font-size:46px;font-weight:700;color:{COLORS[label]}'>{label}</div>", unsafe_allow_html=True)
    c2.metric("Overall score", f"{sc['overall']:.0f} / 100")
    c3.metric("Confidence", f"{sc['confidence'] * 100:.0f}%", help="Distance from the nearest label boundary × how much of the rubric had data. With a tiny calibration set, treat it as indicative.")
    if res.get("unavailable"):
        lines = "\n".join(f"- **{u['signal']}** - {u['reason']}" for u in res["unavailable"])
        st.warning(f"**Some signals could not be used, so this verdict is less certain (confidence was lowered):**\n{lines}")
    if res.get("speakers_approximate"):
        st.info("Teacher/children were separated by voice only (no transcript with speaker names). That split was right about 70% of the time "
                "on test classes, so who-spoke-when scores were left out of the verdict.")
    for n in res["notes"]:
        st.warning(n)

    t = res["technical"]
    if t["platform"] or t["setup"]:
        with st.expander(f"Technical & platform flags ({len(t['platform'])} platform, {len(t['setup'])} setup)", expanded=bool(t["platform"])):
            if t["platform"]:
                st.markdown("**Platform / connection faults** (not the teacher's fault, not penalised)")
                for p in t["platform"]:
                    st.markdown(f"- {p['text']}")
            if t["setup"]:
                st.markdown("**Setup issues** (teacher-controlled, included in the Presentation score)")
                for p in t["setup"]:
                    st.markdown(f"- {p['text']}")

    left, right = st.columns([1, 1.3])
    with left:
        st.subheader("Scores by dimension")
        dims = [(d, v) for d, v in sc["dimensions"].items()]
        fig = go.Figure(go.Bar(x=[v if v is not None else 0 for _, v in dims], y=[d for d, _ in dims], orientation="h",
                               marker_color=[("#9aa5b1" if v is None else COLORS[LABELS[min(3, int(v // 25))]]) for _, v in dims],
                               text=[("n/a" if v is None else f"{v:.0f}") for _, v in dims], textposition="outside"))
        fig.update_layout(xaxis=dict(range=[0, 110], title="0-100"), yaxis=dict(autorange="reversed"), height=320, margin=dict(l=0, r=10, t=10, b=30))
        st.plotly_chart(fig, width="stretch")
        st.caption("Weights: " + ", ".join(f"{d} {int(s['weight'] * 100)}%" for d, s in DIMENSIONS.items()))
    with right:
        st.subheader("What happened, and when")
        obs = res["observations"]
        if not obs:
            st.info("Not enough evidence for specific observations.")
        for o in sorted(obs, key=lambda o: (o["polarity"] != "issue", o["at"] if o["at"] is not None else 1e9)):
            icon = "🔴" if o["polarity"] == "issue" else "🟢"
            stamp = f" `{fmt_t(o['at'])}`" if o["at"] is not None else ""
            st.markdown(f"{icon} **{o['dimension']}**{stamp} — {o['text']}")
            if o.get("suggestion"):
                st.caption(f"→ {o['suggestion']}")

    tr = res["features"].get("transcript") or {}
    if tr.get("ok") and tr.get("has_speakers"):
        st.subheader("Timeline: who is talking, minute by minute")
        mins = list(range(len(tr["talk_bins_teacher"])))
        fig2 = go.Figure()
        fig2.add_bar(x=mins, y=tr["talk_bins_teacher"], name="Teacher", marker_color=TEACHER_C)
        fig2.add_bar(x=mins, y=tr["talk_bins_student"], name="Children", marker_color=STUDENT_C)
        for o in res["observations"]:
            if o["at"] is not None:
                fig2.add_vline(x=o["at"] / 60, line_dash="dot", line_color="#c0392b" if o["polarity"] == "issue" else "#1e8449")
        fig2.update_layout(barmode="stack", height=280, xaxis_title="minute of recording", yaxis_title="seconds of speech", margin=dict(t=10),
                           legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig2, width="stretch")
        st.caption("Dotted lines mark the moments mentioned above (red = issue, green = strength).")

    a = res["features"].get("audio") or {}
    if a.get("ok") and res["features"].get("video", {}).get("ok"):
        v = res["features"]["video"]
        fig3 = go.Figure()
        xs = [i * v["step_s"] / 60 for i in range(len(v["series"]["face"]))]
        fig3.add_scatter(x=xs, y=v["series"]["face"], name="face visible", mode="lines", line=dict(color=TEACHER_C, shape="hv"))
        fig3.add_scatter(x=xs, y=[x * 0.8 for x in v["series"]["screen"]], name="shared screen", mode="lines", line=dict(color=STUDENT_C, shape="hv"))
        fig3.add_scatter(x=xs, y=[x * 0.6 for x in v["series"]["black"]], name="black / camera off", mode="lines", line=dict(color="#c0392b", shape="hv"))
        fig3.update_layout(height=200, xaxis_title="minute", yaxis=dict(visible=False), margin=dict(t=10), legend=dict(orientation="h", y=1.2))
        with st.expander("What the video shows over time"):
            st.plotly_chart(fig3, width="stretch")

    narrative = llm_narrative(res, res["names"], res["teacher"])
    if narrative:
        st.subheader("Summary (LLM, anonymised input)")
        st.write(narrative)
    with st.expander("How the score was computed"):
        for d, items in sc["items"].items():
            st.markdown(f"**{d}** — {sc['dimensions'][d] if sc['dimensions'][d] is not None else 'n/a'}")
            for it in items:
                s = "n/a" if it["score"] is None else f"{it['score'] * 100:.0f}"
                st.caption(f"{it['item']} (weight {it['weight']}): {s} — {it['why']}")
    st.caption("Limitations: calibrated on 8 labelled classes only; keyword-based pedagogy detection on machine-made transcripts (names and Malayalam are often garbled); "
               "video checks are coarse. Use it as a first-pass, evidence-based triage, not a final judgement.")


if go_btn:
    tmp = Path(tempfile.mkdtemp(prefix="cqa_"))
    started = time.time()
    bar = st.progress(0.0, text="Starting")
    try:
        vtt_file = (up_vtt if up_video else link_vtt) or up_vtt or link_vtt
        if up_video is not None:
            if up_video.size > MAX_UPLOAD_MB * 1024 * 1024:
                st.error(f"This file is {up_video.size / 1e6:.0f} MB; the limit on this server is {MAX_UPLOAD_MB:.0f} MB. "
                         "Trim the recording or paste a link instead.")
                st.stop()
            video = tmp / "recording.mp4"
            with video.open("wb") as fh:
                shutil.copyfileobj(up_video, fh)
        elif link.strip():
            bar.progress(0.01, text="Downloading")
            video = fetch(link, tmp, lambda fr, m: bar.progress(min(0.05, fr * 0.05), text=m))
        else:
            st.error("Please upload a recording or paste a link first.")
            st.stop()
        vtt_path = None
        if vtt_file is not None:
            vtt_path = tmp / "t.vtt"
            vtt_path.write_bytes(vtt_file.getvalue())
        features = analyze(video, vtt_path, use_cache=False, max_minutes=MAX_MIN, whisper_model=WHISPER_MODEL if use_asr else "skip",
                           progress=lambda f, m: bar.progress(min(1.0, 0.05 + 0.9 * f), text=m), deadline_s=MAX_SECONDS)
        bar.progress(1.0, text=f"Done in {time.time() - started:.0f}s")
        _render(assess(features))
    except FetchError as e:
        bar.empty()
        st.error(str(e))
    except ValueError as e:
        bar.empty()
        st.error(str(e))
    except Exception as e:  # noqa: BLE001
        bar.empty()
        st.error(f"Something went wrong while analysing this recording ({type(e).__name__}). Try a shorter clip or supply the transcript.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)  # recording + transcript never outlive the request
