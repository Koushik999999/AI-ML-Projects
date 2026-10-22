"""Download a recording from a direct URL or a (public) Google Drive share link into a temp file."""
from __future__ import annotations

import ipaddress
import re
import socket
from pathlib import Path
from urllib.parse import urlparse

import requests

MAX_BYTES = int(1.5 * 1024 ** 3)
UA = {"User-Agent": "Mozilla/5.0 (class-quality-assessor)"}


class FetchError(RuntimeError):
    """Raised with a user-readable message."""


def drive_id(url: str) -> str | None:
    m = re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?(?:[^#]*&)?id=)([\w-]{20,})", url)
    return m[1] if m else None


def _check_host(url: str) -> None:
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise FetchError("Please paste a full http(s) link.")
    try:
        for fam, *_rest, sockaddr in socket.getaddrinfo(p.hostname, None):
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                raise FetchError("That address is not allowed (private/internal network).")
    except socket.gaierror as e:
        raise FetchError("Could not resolve that host.") from e


def fetch(url: str, dest_dir: str | Path, progress=lambda frac, msg: None) -> Path:
    url = url.strip()
    gid = drive_id(url)
    session = requests.Session()
    session.headers.update(UA)
    target = f"https://drive.google.com/uc?export=download&id={gid}" if gid else url
    _check_host(target)
    try:
        r = session.get(target, stream=True, timeout=30, allow_redirects=True)
        if gid and "text/html" in r.headers.get("content-type", ""):
            # large-file interstitial: extract the confirm form
            html = r.text
            m = re.search(r'action="([^"]+)"', html)
            params = dict(re.findall(r'name="(\w+)" value="([^"]*)"', html))
            if not m or "id" not in params:
                raise FetchError("Google Drive refused the download. Make sure the file is shared as 'Anyone with the link'.")
            r = session.get(m[1].replace("&amp;", "&"), params=params, stream=True, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        raise FetchError(f"Download failed: {type(e).__name__}. Check the link is public and direct.") from e
    ctype = r.headers.get("content-type", "")
    if "text/html" in ctype:
        raise FetchError("That link returned a web page, not a video file. Use a direct link to the .mp4, or a public Google Drive file link.")
    total = int(r.headers.get("content-length") or 0)
    if total and total > MAX_BYTES:
        raise FetchError(f"File is {total / 1e9:.1f} GB; the limit is {MAX_BYTES / 1e9:.1f} GB.")
    out = Path(dest_dir) / "recording.mp4"
    got = 0
    with out.open("wb") as fh:
        for chunk in r.iter_content(1 << 20):
            got += len(chunk)
            if got > MAX_BYTES:
                raise FetchError("File exceeds the size limit.")
            fh.write(chunk)
            if total:
                progress(got / total, f"Downloading {got / 1e6:.0f} / {total / 1e6:.0f} MB")
    return out
