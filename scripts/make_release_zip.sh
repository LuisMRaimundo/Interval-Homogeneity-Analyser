#!/usr/bin/env sh
# Build a portable source ZIP excluding venv, caches, git, and build artefacts.
# Default output: sibling of this repo folder, named "<folder>-source-<timestamp>.zip"
# Run from repo root:  sh scripts/make_release_zip.sh
# Optional output path:  sh scripts/make_release_zip.sh /path/to/out.zip
# Skip clean:  SKIP_CLEAN=1 sh scripts/make_release_zip.sh
set -e
SCRIPT_DIR="$(CDPATH= cd "$(dirname "$0")" && pwd)"
ROOT="$(CDPATH= cd "$SCRIPT_DIR/.." && pwd)"
REPO_NAME="$(basename "$ROOT")"
STAMP="$(date +%Y%m%d-%H%M%S)"

if [ "${SKIP_CLEAN:-}" != "1" ]; then
  sh "$SCRIPT_DIR/clean_repo.sh"
fi

if [ -n "${1:-}" ]; then
  OUT_ZIP="$1"
else
  OUT_ZIP="$(dirname "$ROOT")/${REPO_NAME}-source-${STAMP}.zip"
fi

tar -acf "$OUT_ZIP" \
  --exclude='.venv' \
  --exclude='venv' \
  --exclude='env' \
  --exclude='.git' \
  --exclude='.pytest_cache' \
  --exclude='.mypy_cache' \
  --exclude='.ruff_cache' \
  --exclude='build' \
  --exclude='dist' \
  --exclude='.eggs' \
  --exclude='.coverage' \
  --exclude='coverage.xml' \
  --exclude='htmlcov' \
  --exclude='__pycache__' \
  --exclude='*.egg-info' \
  -C "$ROOT" .

sh "$SCRIPT_DIR/verify_release_zip.sh" "$OUT_ZIP"

echo "Release ZIP written to: $OUT_ZIP"
echo "Recipients should: unzip, then pip install -e \".[dev]\" (see README)."
