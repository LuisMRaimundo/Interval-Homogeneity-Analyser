#!/usr/bin/env sh
# Remove generated / local artefacts. Run from repo root:  sh scripts/clean_repo.sh
# Optional: also remove local virtualenvs (destructive):  sh scripts/clean_repo.sh --include-venv
set -e
cd "$(dirname "$0")/.."
find . -type d -name __pycache__ -print0 2>/dev/null | xargs -0 rm -rf
rm -rf .pytest_cache .mypy_cache .ruff_cache build dist .eggs
find . -type d -name "*.egg-info" -print0 2>/dev/null | xargs -0 rm -rf
find . -type f \( -name "*.docx" -o -name "*.mhtml" \) -delete 2>/dev/null || true
rm -f .coverage coverage.xml 2>/dev/null || true
rm -rf htmlcov 2>/dev/null || true
rm -rf results results_ci results_batch 2>/dev/null || true
if [ -d docs/reports ]; then
  find docs/reports -type f \( -name "*.csv" -o -name "*.json" -o -name "*.md" \) ! -name README.md -delete 2>/dev/null || true
  rm -rf docs/reports/_tmp 2>/dev/null || true
fi
if [ "${1:-}" = "--include-venv" ]; then
  rm -rf .venv venv env
  echo "Also removed .venv / venv / env if present."
fi
echo "Cleaned caches, build/dist/eggs, *.egg-info, *.docx, *.mhtml under $(pwd)"
if [ "${1:-}" != "--include-venv" ]; then
  echo "Tip: pass --include-venv to remove .venv / venv / env (you will need to recreate the env)."
fi
