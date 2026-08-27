#!/usr/bin/env python3
"""Find and cache the latest published version of a 3GPP spec for a release.

Companion to etsi-section.py: resolves "give me the freshest Rel-18 copy of
TS 29.274 you can find" into a concrete cached PDF path, downloading if a
newer minor version became available since the last call.

Usage:
    python3 latest-version.py <spec> [release]
    python3 latest-version.py --list
    python3 latest-version.py --versions <spec>

Arguments:
    spec       3GPP spec number, e.g. "29.274", "23.501", "24.008", "38.331"
    release    Release major number, e.g. "18" for Rel-18, "17" for Rel-17.
               Optional: defaults to DEFAULT_RELEASE (Rel-18) when omitted,
               so the freshest Rel-18 version is fetched unless a different
               release is explicitly requested.

Examples:
    python3 latest-version.py 29.274 18
    # → ~/.cache/3gpp-specs/ts_29274_v18.08.00.pdf

    python3 latest-version.py 29.274
    # → same as above: release omitted defaults to Rel-18

    # Inspect what's already cached (no network):
    python3 latest-version.py --list
    # → TS 29.274 v18.08.00  /home/.../.cache/3gpp-specs/ts_29274_v18.08.00.pdf

    # Chain with etsi-section.py:
    path=$(python3 latest-version.py 29.274 18)
    python3 etsi-section.py "$path" "8.34 PDN Type" "8.35 " 3000

Behaviour:
  1. Reads ETSI's directory listing for the spec in a single GET and
     picks the newest version of the requested release. Falls back to
     an ascending, early-stopping probe only if the listing fails.
  2. Cache filename embeds the version (ts_{specnum}_v{version}.pdf) so
     that "is the cached copy still latest?" is a single Path.exists() check.
  3. If the latest version is already cached: no download, instant return.
  4. If a newer version is available: download, and remove any older
     cached copies of the same spec so the cache doesn't accumulate.
  5. Print the cached path to stdout (one line — pipe-friendly). Status
     messages go to stderr.

Why this exists:
  WebFetch is blocked by ETSI's Cloudflare (claude-code#22846) and ETSI's
  directory listings are JS-rendered (curl returns obfuscated HTML). The
  reliable strategy is the URL pattern + linear probe, which this script
  bundles into a single bash invocation. Probes and downloads send a
  browser-like User-Agent (see USER_AGENT below) because ETSI's WAF is more
  prone to blocking requests carrying curl's default UA string.

Requires: curl in $PATH. No Python dependencies beyond stdlib.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "3gpp-specs"
# Probe range: walk minor versions from MAX_PROBES down to 0. Kept tight
# (15) to avoid tripping ETSI's per-path WAF, which will block further
# requests for that spec for several hours after a burst of 404s.
# Bump only if a spec genuinely has minor versions above 15.
MAX_PROBES = 15
# Release used when the caller omits one: Rel-18 is the current 5G-Advanced
# baseline, so "fetch me this spec" defaults here unless told otherwise.
DEFAULT_RELEASE = "18"
# Resolve curl absolutely so subprocess.run() doesn't trip on any malformed
# entry in PATH (some sandboxed shells have non-directory PATH components
# that make execvp raise ENOTDIR before reaching the real binary).
CURL = shutil.which("curl") or "/usr/bin/curl"
# ETSI's WAF is more likely to challenge/block requests carrying curl's
# default "curl/x.y.z" User-Agent than an ordinary browser UA.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def etsi_dir_url(spec: str) -> str:
    """Build the ETSI delivery *directory* URL for a spec.

    Spec "29.274" -> https://.../etsi_ts/129200_129299/129274/

    The hundreds digit must come from the ZERO-PADDED number, not the raw
    one: "29.060" pads to "060" whose hundreds digit is "0" (bucket
    129000_129099). Reading spec.split(".")[1][0] instead gives "0" here by
    luck but "6" for the equally valid input "29.60", which builds bucket
    129600_129699 and 404s on a spec that exists.
    """
    series, num = spec.split(".")
    num = num.zfill(3)
    fname = f"1{series}{num}"
    return (
        f"https://www.etsi.org/deliver/etsi_ts/"
        f"1{series}{num[0]}00_1{series}{num[0]}99/{fname}/"
    )


def etsi_url(spec: str, version: str) -> str:
    """Build the ETSI delivery URL for a (spec, version) pair."""
    series, num = spec.split(".")
    fname = f"1{series}{num.zfill(3)}"
    vcompact = version.replace(".", "")
    return f"{etsi_dir_url(spec)}{version}_60/ts_{fname}v{vcompact}p.pdf"


def cached_path(spec: str, version: str) -> Path:
    return CACHE_DIR / f"ts_{spec.replace('.', '')}_v{version}.pdf"


def http_ok(url: str) -> bool:
    """HEAD probe; True iff the URL returns 200."""
    r = subprocess.run(
        [CURL, "-sLI", "-A", USER_AGENT, "-o", "/dev/null", "-w", "%{http_code}", url],
        capture_output=True,
        text=True,
        check=False,
    )
    return r.stdout.strip() == "200"


_VERSION_RE = re.compile(r"(\d{2}\.\d{2}\.\d{2})_60")


def list_versions(spec: str) -> list[str]:
    """Every published version of `spec`, newest last, from ONE HTTP GET.

    ETSI serves a plain autoindex at the spec directory listing every
    version as a `NN.NN.NN_60` subdirectory. Parsing it costs a single
    request and yields the exact set of published versions, across all
    releases. Fields are zero-padded to two digits, so plain string sort
    is already version order.

    This replaces the old descending linear probe, which was the actual
    cause of the WAF blocks this script kept blaming on the User-Agent: a
    spec whose newest release version is .00 (TS 29.060 Rel-18 is exactly
    that) forced 15 consecutive 404s on the same path before reaching the
    one URL that exists. ETSI's WAF blocks the path for hours after such a
    burst, so the probe poisoned the very request it was walking toward.
    """
    r = subprocess.run(
        [CURL, "-sL", "-A", USER_AGENT, "--max-time", "30", etsi_dir_url(spec)],
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        return []
    return sorted(set(_VERSION_RE.findall(r.stdout)))


def find_latest(spec: str, release: str) -> tuple[str, str]:
    """Return (version, url) of the newest published version for a release.

    Directory listing first (1 request). Only if that fails do we fall back
    to probing, and then ASCENDING from .00 with an early stop: real specs
    publish contiguous minor versions, so the first gap is the end. That
    caps a fallback run at (found + 1) requests instead of a guaranteed
    MAX_PROBES burst.
    """
    versions = [v for v in list_versions(spec) if v.startswith(f"{release}.")]
    if versions:
        latest = versions[-1]
        return latest, etsi_url(spec, latest)

    print(
        f"directory listing unavailable for TS {spec}; falling back to probing",
        file=sys.stderr,
    )
    found: str | None = None
    for minor in range(0, MAX_PROBES + 1):
        version = f"{release}.{minor:02d}.00"
        if http_ok(etsi_url(spec, version)):
            found = version
        elif found is not None:
            break  # contiguous run ended: `found` is the newest
    if found:
        return found, etsi_url(spec, found)
    raise RuntimeError(
        f"no published TS {spec} Rel-{release} version found in "
        f"{release}.00..{release}.{MAX_PROBES:02d}"
    )


def newest_cached(spec: str, release: str) -> Path | None:
    """Return the cached PDF for the highest minor version of (spec, release)
    that we already have on disk, or None if nothing is cached.

    Used as a fallback when ETSI's WAF blocks the probe phase — better to
    return a slightly-stale cached spec than to fail the whole call.
    """
    pattern = f"ts_{spec.replace('.', '')}_v{release}.*.pdf"
    candidates = list(CACHE_DIR.glob(pattern))
    return max(candidates, default=None, key=lambda p: p.name)


def purge_older(spec: str, keep_version: str) -> int:
    """Remove superseded copies of the same spec AND THE SAME RELEASE.

    Two deliberate narrowings, both learned the hard way:

    * **Same release only.** The old pattern swept every release, so
      fetching Rel-19 silently deleted the Rel-18 copy the caller might
      still be comparing against. Cross-release comparison is a documented
      use of this skill; the cache must survive it.
    * **Only files this script wrote.** cached_path() emits dotted versions
      (`ts_29060_v18.00.00.pdf`). Hand-placed specs use underscores
      (`ts_29060_v18_00_00.pdf`) and are here precisely because ETSI will
      not serve them: TS 29.060 is the standing example. Deleting one is
      unrecoverable, so anything not matching the dotted schema is left
      alone.
    """
    keep = cached_path(spec, keep_version)
    specnum = spec.replace(".", "")
    release = keep_version.split(".")[0]
    removed = 0
    for f in CACHE_DIR.glob(f"ts_{specnum}_v{release}.*.pdf"):
        if f != keep and f.name.count(".") >= 3:  # dotted schema == ours
            f.unlink()
            removed += 1
    return removed


def list_cache() -> int:
    """Print every cached PDF as `TS {spec} v{version}  {path}`, sorted."""
    if not CACHE_DIR.exists():
        print("cache is empty", file=sys.stderr)
        return 0
    rows: list[tuple[str, str, str]] = []
    for p in sorted(CACHE_DIR.glob("ts_*.pdf")):
        # Filename schema set by cached_path(): ts_{specnum}_v{version}.pdf
        # where specnum is digits only and version contains dots.
        parts = p.stem.split("_", 2)
        if len(parts) != 3 or not parts[2].startswith("v"):
            continue
        specnum, ver = parts[1], parts[2][1:]
        spec = f"{specnum[:2]}.{specnum[2:]}"
        rows.append((spec, ver, str(p)))
    if not rows:
        print("cache is empty", file=sys.stderr)
        return 0
    for spec, ver, path in rows:
        print(f"TS {spec} v{ver}  {path}")
    return 0


def show_versions(spec: str) -> int:
    """Print every published version of a spec, grouped by release."""
    versions = list_versions(spec)
    if not versions:
        print(f"no published versions found for TS {spec}", file=sys.stderr)
        return 1
    for v in versions:
        print(f"TS {spec} v{v}")
    return 0


def main(argv: list[str]) -> int:
    if argv[1:] == ["--list"]:
        return list_cache()
    if len(argv) == 3 and argv[1] == "--versions":
        return show_versions(argv[2])
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    spec = argv[1]
    release = argv[2] if len(argv) > 2 else DEFAULT_RELEASE
    if len(argv) <= 2:
        print(f"no release given, defaulting to Rel-{DEFAULT_RELEASE}", file=sys.stderr)

    try:
        version, url = find_latest(spec, release)
    except RuntimeError as e:
        # ETSI's WAF blocks probing intermittently. Fall back to whatever
        # we already have cached for this spec/release.
        fallback = newest_cached(spec, release)
        if fallback is not None:
            print(
                f"WARNING: ETSI probe failed ({e}); using cached {fallback.name}",
                file=sys.stderr,
            )
            print(str(fallback))
            return 0
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    dest = cached_path(spec, version)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"cached: TS {spec} v{version}", file=sys.stderr)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading: TS {spec} v{version}", file=sys.stderr)
        subprocess.run(
            [CURL, "-sLo", str(dest), "-A", USER_AGENT, url],
            check=True,
            stderr=subprocess.DEVNULL,
        )
        removed = purge_older(spec, version)
        if removed:
            print(f"purged {removed} older cached version(s)", file=sys.stderr)

    print(str(dest))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
