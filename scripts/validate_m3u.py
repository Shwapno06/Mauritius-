#!/usr/bin/env python3
"""Validate M3U playlists for syntax, duplicates, metadata completeness, and optional stream reachability."""

import argparse
import concurrent.futures
import glob
import os
import re
import ssl
import sys
import urllib.error
import urllib.request


def parse_m3u(filepath):
    """Parse an M3U file and return structural stats and entries."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = [line.strip() for line in f if line.strip()]

    has_header = bool(lines and lines[0].startswith("#EXTM3U"))
    entries = []
    orphan_urls = 0
    current_meta = None

    for line in lines:
        if line.startswith("#EXTINF"):
            current_meta = line
        elif line.startswith("#"):
            continue
        elif line.startswith(("http://", "https://")):
            if current_meta is None:
                orphan_urls += 1
            entries.append((current_meta or "", line))
            current_meta = None

    urls = [url for _, url in entries]
    duplicates = len(urls) - len(set(urls))
    missing_logo = sum(
        1 for meta, _ in entries if meta and ('tvg-logo=""' in meta or "tvg-logo=" not in meta)
    )
    missing_group = sum(
        1 for meta, _ in entries if meta and ('group-title=""' in meta or "group-title=" not in meta)
    )

    return {
        "file": os.path.basename(filepath),
        "has_header": has_header,
        "total": len(entries),
        "duplicates": duplicates,
        "orphan_urls": orphan_urls,
        "missing_logo": missing_logo,
        "missing_group": missing_group,
        "entries": entries,
    }


def check_stream(url, timeout=6):
    """Test whether a stream URL responds with HTTP 2xx/3xx."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "VLC/3.0.18 LibVLC/3.0.18", "Accept": "*/*"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            resp.read(256)
            return ("ALIVE", resp.status)
    except urllib.error.HTTPError as exc:
        return (f"HTTP_{exc.code}", exc.code)
    except Exception as exc:
        return ("UNREACHABLE", type(exc).__name__)


def main():
    parser = argparse.ArgumentParser(description="Validate M3U playlists.")
    parser.add_argument("--check-streams", action="store_true", help="Also probe HTTP reachability")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if syntax errors are found")
    args = parser.parse_args()

    m3u_files = sorted(glob.glob("*.m3u") + glob.glob("*.m3u8"))
    if not m3u_files:
        print("No .m3u or .m3u8 files found.")
        return 0

    summary_lines = ["## M3U Validation Report\n"]
    has_syntax_error = False

    for path in m3u_files:
        stats = parse_m3u(path)
        if not stats["has_header"] or stats["total"] == 0:
            has_syntax_error = True

        print(f"=== {stats['file']} ===")
        print(
            f"  Header(#EXTM3U): {stats['has_header']} | Entries: {stats['total']} | "
            f"Duplicates: {stats['duplicates']} | Missing logo: {stats['missing_logo']} | "
            f"Missing group: {stats['missing_group']}"
        )

        summary_lines.append(
            f"- **{stats['file']}**: {stats['total']} entries, "
            f"`#EXTM3U`={'OK' if stats['has_header'] else 'MISSING'}, "
            f"duplicates={stats['duplicates']}, missing_logo={stats['missing_logo']}, "
            f"missing_group={stats['missing_group']}"
        )

        if args.check_streams and stats["entries"]:
            urls = [url for _, url in stats["entries"]]
            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
                results = list(pool.map(check_stream, urls))
            counts = {}
            for status, _ in results:
                counts[status] = counts.get(status, 0) + 1
            print(f"  Stream reachability: {counts}")
            summary_lines.append(f"  - Stream health: `{counts}`")

    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as f:
            f.write("\n".join(summary_lines) + "\n")

    if args.strict and has_syntax_error:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
