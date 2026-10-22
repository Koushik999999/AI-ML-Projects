# Hugging Face Docker Space (free CPU). Python 3.11, ffmpeg from apt, Whisper "tiny" baked into the image at build time.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# HF runs containers as uid 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    MODEL_DIR=/home/user/models \
    WHISPER_MODEL=tiny \
    PRELOAD_WHISPER=1 \
    MAX_VIDEO_MINUTES=90 \
    MAX_PROCESSING_SECONDS=600 \
    MAX_UPLOAD_MB=1024 \
    EXPLAINER_PROVIDER=rule \
    PYTHONUNBUFFERED=1
WORKDIR $HOME/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Pre-download the speech model into the image (build has internet; the running Space may be slow on first download otherwise)
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('tiny', device='cpu', compute_type='int8', download_root='/home/user/models')"

COPY --chown=user . .

EXPOSE 7860
# XSRF/CORS are off because the Space is served inside an iframe on huggingface.co, where file uploads otherwise fail with 403.
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=7860", "--server.address=0.0.0.0", \
     "--server.enableCORS=false", "--server.enableXsrfProtection=false", "--server.maxUploadSize=1024", \
     "--browser.gatherUsageStats=false"]
