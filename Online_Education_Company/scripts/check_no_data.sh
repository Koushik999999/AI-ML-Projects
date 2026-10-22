#!/usr/bin/env bash
# Fails if any media / transcript / data / secret file is staged.
# Usage: scripts/check_no_data.sh            (checks the git index; used by the pre-commit hook)
#        scripts/check_no_data.sh --history  (also scans all of git history for such files)
set -u
PAT='\.(mp4|mov|mkv|webm|avi|m4a|mp3|wav|flac|ogg|vtt|srt)$|(^|/)(data|cache|outputs)/|(^|/)\.env$'
# Scope: this project only (the parent repo holds other projects).
SCOPE="Online_Education_Company/"
bad=$(git diff --cached --name-only --diff-filter=ACMR | grep -E "^${SCOPE}" | grep -Ei "$PAT")
if [ -n "$bad" ]; then
  echo "BLOCKED: confidential/media files are staged:" >&2
  echo "$bad" | sed 's/^/  - /' >&2
  echo "Unstage with: git restore --staged <file>" >&2
  exit 1
fi
if [ "${1:-}" = "--history" ]; then
  hist=$(git log --all --name-only --pretty=format: | grep -E "^${SCOPE}" | grep -Ei "$PAT" | sort -u)
  if [ -n "$hist" ]; then
    echo "BLOCKED: data files found in git history:" >&2; echo "$hist" | sed 's/^/  - /' >&2; exit 1
  fi
  echo "OK: no data files in git history."
fi
echo "OK: no media/transcript/data files staged."
