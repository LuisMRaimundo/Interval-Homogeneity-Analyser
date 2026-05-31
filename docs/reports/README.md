# Generated reports (not versioned)

This folder holds **local / CI-generated** thesis tables. Contents are recreated by:

```bash
python scripts/sensitivity_report.py          # sensitivity_*.csv, sensitivity_*.md
python scripts/run_annotated_study.py         # annotated_pilot/
```

Do not commit CSV/JSON/Markdown outputs here; they are listed in `.gitignore`.
