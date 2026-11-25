# Mauritius IPTV Playlists

Public M3U playlist collection with a built-in syntax, metadata, and stream health validator.

## Playlists

| Playlist | Raw URL |
| :--- | :--- |
| **All In One (Mauritius)** | `https://raw.githubusercontent.com/Shwapno06/Mauritius-/main/All%20In%20One-Mauritius.m3u` |
| **Sports (Mauritius)** | `https://raw.githubusercontent.com/Shwapno06/Mauritius-/main/Sports-Mauritius.m3u` |

## Usage

Copy either **Raw URL** above and load it into any M3U-compatible media player (VLC, Kodi, TiviMate, StreamSutra, etc.).

## Validation & Health Checks

This repository includes a zero-dependency Python 3 validator at `scripts/validate_m3u.py` that checks:

- `#EXTM3U` header presence and `#EXTINF` pairing
- Duplicate stream URLs
- Missing `tvg-logo` or `group-title` attributes
- Optional live HTTP/HTTPS reachability (`--check-streams`)

### Run Locally

```bash
# Syntax & metadata audit
python3 scripts/validate_m3u.py --strict

# Syntax + live stream reachability check
python3 scripts/validate_m3u.py --strict --check-streams
```
