#!/usr/bin/env sh
# Fail if archive lists forbidden local/generated paths. Usage: sh scripts/verify_release_zip.sh /path/to/archive.zip
set -e
ZIP="${1:?usage: sh scripts/verify_release_zip.sh /path/to/archive.zip}"
if [ ! -f "$ZIP" ]; then
  echo "ZIP not found: $ZIP" >&2
  exit 1
fi
# Match both / and \ in listings (some tools emit backslashes on Windows).
BAD="$(tar -tf "$ZIP" | grep -E '(^|[\\/])\.venv([\\/]|$)|(^|[\\/])venv([\\/]|$)|(^|[\\/])env([\\/]|$)|__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|\.egg-info([\\/]|$)' || true)"
if [ -n "$BAD" ]; then
  echo "ZIP contains forbidden paths:" >&2
  echo "$BAD" | head -40 >&2
  exit 1
fi
echo "ZIP verification OK: no venv, caches, egg-info, or __pycache__ paths in listing."
