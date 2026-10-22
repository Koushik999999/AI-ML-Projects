"""Build a clean, data-free copy of the app for a Hugging Face Docker Space.

    python scripts/make_space_bundle.py OUTPUT_DIR

Copies ONLY a whitelist (app code, pinned requirements, Dockerfile, Space README). No data/, docs/, scripts/, tests/,
cache/, .env, PDFs or media can end up in the bundle, and the script refuses to finish if a forbidden file slips in.
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = re.compile(r"\.(mp4|mov|mkv|webm|avi|m4a|mp3|wav|flac|ogg|vtt|srt|pdf|env)$|(^|/)(data|cache|outputs|\.env)(/|$)", re.I)


def main(out: Path) -> None:
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} is not empty; choose a new folder.")
    out.mkdir(parents=True, exist_ok=True)
    files = [ROOT / "streamlit_app.py", ROOT / "requirements.txt", ROOT / ".streamlit" / "config.toml",
             ROOT / "src" / "scoring" / "calibration.json"]
    files += [p for p in (ROOT / "src").rglob("*.py")]
    for src in files:
        dst = out / src.relative_to(ROOT)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    shutil.copy2(ROOT / "deploy" / "Dockerfile", out / "Dockerfile")
    shutil.copy2(ROOT / "deploy" / "SPACE_README.md", out / "README.md")
    (out / ".gitignore").write_text(".env\n__pycache__/\n*.pyc\ncache/\n")
    bad = [str(p.relative_to(out)) for p in out.rglob("*") if p.is_file() and FORBIDDEN.search(p.relative_to(out).as_posix())
           and p.name != ".gitignore"]
    if bad:
        shutil.rmtree(out)
        sys.exit(f"ABORTED, forbidden files in bundle: {bad}")
    n = sum(1 for p in out.rglob("*") if p.is_file())
    print(f"Bundle ready: {out} ({n} files)")
    for p in sorted(out.rglob("*")):
        if p.is_file():
            print("  ", p.relative_to(out).as_posix())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]).resolve())
