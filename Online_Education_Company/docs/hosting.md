# Hosting guide

Two routes. **Route B (Hugging Face Space) is recommended**: it bakes the speech model into the image, so uploads without a transcript work on first use. Route A is the quickest fallback.

I (the assistant) did not run any of the commands below, and did not create or change anything inside `.git`. Neither route has been deployed or tested on the real hosts; the local code path is tested.

## Before either route

1. Run the local checks from this folder:
   ```bash
   pytest -q
   bash scripts/check_no_data.sh --history
   ```
2. Confirm nothing confidential would be published: `git status` and `git diff --cached --stat` after you stage should list only code and docs (no `data/`, `cache/`, `outputs/`, `.env`, `*.pdf`, `*.mp4`, `*.vtt`). The project `.gitignore` already blocks all of these, including both PDFs.
3. Decide on the organiser-approval question: hosting means the evaluators' recordings (which show children) are processed on the host's servers. The app never calls an external AI API by default (`EXPLAINER_PROVIDER=rule`), but the *host itself* is a third party. If in doubt, ask the organisers before submitting a public link.

---

## (a) Streamlit Community Cloud, pointing at the subfolder

This project lives in `Online_Education_Company/` inside a larger portfolio repo.

**Where Community Cloud looks for dependency files** (from Streamlit's "App dependencies" docs): it searches *the directory of your entrypoint file first, then the repository root*, and uses the first file it finds. So `Online_Education_Company/requirements.txt` is picked up automatically. Keep only one dependency file in that folder.

**`packages.txt` is different:** it is only read from the **root of the repository**. Here that is the portfolio root (`AI-ML-Projects/packages.txt`), not this folder, so `Online_Education_Company/packages.txt` is ignored by Community Cloud. You do not need it: `imageio-ffmpeg` (in `requirements.txt`) ships an ffmpeg binary and the code uses it automatically when no system ffmpeg exists. Only add a root-level `packages.txt` containing `ffmpeg` if you want the system package, and be aware that it would apply to every app deployed from that repo.

Steps:

1. Push the portfolio repo to GitHub (your normal git workflow; make sure `Online_Education_Company/` is included and `data/` is not).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app** -> **Deploy a public app from GitHub**.
4. Repository: your portfolio repo. Branch: `main`.
5. **Main file path:** `Online_Education_Company/streamlit_app.py`
6. Click **Advanced settings**:
   * **Python version: 3.11** (the pins, e.g. `numpy==1.26.4`, need 3.11 or 3.12; do not pick 3.13).
   * Secrets: leave empty.
   * Environment variables are not set here by default; if you want a different model, put `WHISPER_MODEL = "tiny"` in the Secrets box (it is exposed as an environment variable). Optional.
7. Click **Deploy**. First build takes a few minutes (installs `faster-whisper`, OpenCV, Streamlit).
8. Open the app URL in a private window and test:
   * upload a short clip **with** its `.vtt` -> full verdict;
   * upload the same clip **without** a `.vtt` -> banner about approximate speaker split, and a transcript produced locally (the Whisper `tiny` weights download from Hugging Face on first use, adding a minute).
9. Free-tier notes: about 1 GB RAM, shared CPU, the app sleeps when idle. Long recordings may hit the 10-minute processing budget; the app then reports exactly what was and was not analysed. Upload limit is 1024 MB from `.streamlit/config.toml`.

---

## (b) Hugging Face Space, created from a copy of this folder only

A Docker Space is used (the app is Streamlit, but Docker gives pinned Python 3.11, apt ffmpeg and a pre-downloaded Whisper model). Docker Spaces need `sdk: docker` and `app_port: 7860` in the README front matter and run as user id 1000; both are handled in `deploy/`.

### 1. Build a clean bundle (data-free by construction)

From `Online_Education_Company/`:

```bash
python scripts/make_space_bundle.py ../space_bundle
```

Pick any new, empty folder outside the repo. The script copies a whitelist only (`streamlit_app.py`, `src/*.py`, `requirements.txt`, `.streamlit/config.toml`, `calibration.json`, the Dockerfile and the Space README) and aborts if any media, transcript, PDF, `.env`, `data/` or `cache/` path appears. It prints the file list (24 files at the time of writing).

### 2. Create the Space

1. https://huggingface.co/new-space
2. Owner: you. Space name: e.g. `class-quality-assessor`.
3. **SDK: Docker** (choose the *Blank* template).
4. Hardware: **CPU basic (free)**.
5. Visibility: your choice (public is needed for evaluators to open it without an account).
6. Click **Create Space**.

### 3. Create a write token (once)

https://huggingface.co/settings/tokens -> **New token** -> type **Write** -> copy it. It is used as the git password below. Do not paste it into any file in the repo.

### 4. Push the bundle (commands for you to run)

```bash
cd ../space_bundle
git init -b main
git add .
git status          # check: only the 24 files listed by the bundle script
git commit -m "Class quality assessor"
git remote add space https://huggingface.co/spaces/<YOUR_HF_USERNAME>/class-quality-assessor
git push space main
# Username: <YOUR_HF_USERNAME>   Password: <the write token>
```

If the Space was created with an initial README commit and the push is rejected, use `git pull space main --allow-unrelated-histories` (keep **your** `README.md`), then push again.

Alternative without a local git history: clone the empty Space (`git clone https://huggingface.co/spaces/<user>/class-quality-assessor`), copy the bundle's contents into it, then `git add . && git commit -m ... && git push`.

### 5. Wait for the build and test

1. Open the Space -> **Logs** tab. The build downloads the Whisper `tiny` model into the image (about 75 MB); the app status turns to *Running*.
2. In the Space *Settings* -> *Variables and secrets* you can (optionally) add variables: `WHISPER_MODEL` (`tiny` default, `base` is more accurate but about 3x slower), `MAX_PROCESSING_SECONDS`, `MAX_VIDEO_MINUTES`, `MAX_UPLOAD_MB`. Leave `EXPLAINER_PROVIDER` unset (or `rule`).
3. Test as in route (a), step 8. **Test an upload of your largest realistic file**: Spaces sit behind a proxy and I could not verify its request-size limit; the app shows a clear message above `MAX_UPLOAD_MB`, but a proxy rejection would come from the platform. If large uploads fail, ask evaluators to use the *Paste link* tab or supply a shorter file.
4. Free CPU Spaces pause after inactivity and take a minute to wake; open the link once shortly before the deadline.

### What the Docker image does (for review)

* `python:3.11-slim`, `ffmpeg` from apt, pinned `requirements.txt`.
* Model cache in `/home/user/models`; the model is downloaded at build time, and loaded once per server process at app start.
* `--server.enableXsrfProtection=false --server.enableCORS=false`: Spaces serve the app inside an iframe, where file uploads otherwise fail. Trade-off: weaker CSRF protection on an app that holds no accounts or stored data.
* No volume is mounted; every upload and temp file lives in a per-request temp folder that is deleted in a `finally` block. The app writes no logs containing transcript text.

---

## Verify Whisper in the hosted environment

After deploy, upload any `.mp4` **without** a `.vtt` and expect:

* sidebar caption "Speech model: ready" (if it shows "unavailable", the message says why);
* in the result: a transcript source of local recognition, the info banner about the approximate teacher/child split, and a lower confidence than the same clip with a `.vtt`;
* if the speech model cannot run, the app must still return a verdict from audio/video and a yellow banner listing "transcript and who-said-what" as unavailable.

Smoke test from a shell inside the container (Space -> *Settings* -> not available on free tier; run locally with Docker instead):

```bash
docker build -t cqa deploy_bundle_folder && docker run --rm -p 7860:7860 cqa
```
