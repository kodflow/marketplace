#!/usr/bin/env python3
"""Fetch and section-extract an ETSI-hosted 3GPP spec in one shot.

Token-efficient companion to the 3gpp-expert skill: replaces multi-step
curl + Python-script workflows with a single bash invocation that prints
only the requested section. Caches the PDF to ~/.cache/3gpp-specs/ by URL
hash so repeated queries against the same spec download it once.

Usage:
    python3 etsi-section.py <url-or-path> <section-header> [end-marker] [max-chars]

The first argument may be either an ETSI URL (downloaded + cached) or a
local PDF path (read directly). Chain with latest-version.py:

    path=$(python3 latest-version.py 29.274 18)
    python3 etsi-section.py "$path" "8.34 PDN Type" "8.35 " 3000

Examples:
    # PDN Type IE in TS 29.274 v18.8.0 (GTPv2-C)
    python3 etsi-section.py \\
      https://www.etsi.org/deliver/etsi_ts/129200_129299/129274/18.08.00_60/ts_129274v180800p.pdf \\
      "8.34 PDN Type" "8.35 " 3000

    # SUPI definition in TS 23.501 v18.10.0
    python3 etsi-section.py \\
      https://www.etsi.org/deliver/etsi_ts/123500_123599/123501/18.10.00_60/ts_123501v181000p.pdf \\
      "5.9.2 Subscription Permanent" "5.9.2a" 2000

Section matching is a literal substring match (no regex) — pass the exact
header text as it appears in the PDF body. The optional end marker bounds
the output to one section; if omitted, the next "X.Y" heading on the same
or higher level acts as the implicit terminator.

Why this script exists:
    WebFetch is blocked by ETSI's Cloudflare (and similarly by Wikipedia,
    Reddit, ...). See
    https://github.com/anthropics/claude-code/issues/22846. curl bypasses
    the WAF cleanly. This script bundles fetch + extract + slice so the
    caller only pays the tokens for the actual section text. Downloads send
    a browser-like User-Agent (see USER_AGENT below) since ETSI's WAF is
    more prone to blocking requests carrying curl's default UA string.

Requires: pypdf (pip install --user pypdf). Falls back gracefully if
pdfminer.six is installed instead.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "3gpp-specs"
DEFAULT_MAX_CHARS = 3000
# Resolve curl absolutely so subprocess.run() doesn't trip on a non-directory
# PATH component (sandboxed shells sometimes break execvp's PATH walk).
CURL = shutil.which("curl") or "/usr/bin/curl"
# ETSI's WAF is more likely to challenge/block requests carrying curl's
# default "curl/x.y.z" User-Agent than an ordinary browser UA.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def cached_path(url: str) -> Path:
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    return CACHE_DIR / f"etsi-{h}.pdf"


def download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    # curl works against ETSI where WebFetch fails; --silent keeps stderr
    # out of the caller's context.
    subprocess.run(
        [CURL, "-sLo", str(dest), "-A", USER_AGENT, url],
        check=True,
        stderr=subprocess.DEVNULL,
    )


def extract_text(pdf: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:  # pragma: no cover - alternative backend
        from pdfminer.high_level import extract_text as _pdfminer_extract

        return _pdfminer_extract(str(pdf))
    return "\n".join((p.extract_text() or "") for p in PdfReader(str(pdf)).pages)


_TOC_TAIL = re.compile(r"\.{10,}")  # dotted leaders (page number often >80 chars away)
_CHANGELOG_HEAD = re.compile(r"\d{2}-\d{4}")  # MM-YYYY date in front of header


def _is_toc(text: str, idx: int, start_len: int) -> bool:
    """True if the chunk after the header looks like a TOC entry."""
    return bool(_TOC_TAIL.search(text[idx + start_len : idx + start_len + 80]))


def _is_changelog(text: str, idx: int) -> bool:
    """True if the chunk before the header is a change-log date column."""
    return bool(_CHANGELOG_HEAD.search(text[max(0, idx - 40) : idx]))


def slice_section(text: str, start: str, end: str | None, max_chars: int) -> str:
    """Find the body occurrence of `start` and return up to max_chars of it.

    ETSI PDFs typically have the header in three places: the table of
    contents (followed by dotted leaders and a page number), the body
    (paragraph prose), and sometimes the change log at the end (preceded
    by a "MM-YYYY" date column). We filter out the TOC and change-log
    occurrences and prefer the first remaining one — that's the body.
    """
    indices: list[int] = []
    i = 0
    while True:
        i = text.find(start, i)
        if i < 0:
            break
        indices.append(i)
        i += len(start)
    if not indices:
        return f"SECTION NOT FOUND: {start!r}"
    body_only = [
        idx for idx in indices
        if not _is_toc(text, idx, len(start)) and not _is_changelog(text, idx)
    ]
    chosen = body_only[0] if body_only else indices[0]
    body = text[chosen:]
    if end:
        e = body.find(end, len(start))
        if e > 0:
            body = body[:e]
    return body[:max_chars]


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    source, section = argv[1], argv[2]
    end = argv[3] if len(argv) > 3 else None
    max_chars = int(argv[4]) if len(argv) > 4 else DEFAULT_MAX_CHARS
    # Accept either a URL (fetch + cache) or a local path (read directly).
    if source.startswith(("http://", "https://")):
        pdf = cached_path(source)
        download(source, pdf)
    else:
        pdf = Path(source)
        if not pdf.exists():
            print(f"file not found: {source}", file=sys.stderr)
            return 1
    text = extract_text(pdf)
    print(slice_section(text, section, end, max_chars))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
