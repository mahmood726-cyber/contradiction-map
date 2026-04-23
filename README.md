<!-- sentinel:skip-file — hardcoded paths are fixture/registry/audit-narrative data for this repo's research workflow, not portable application configuration. Same pattern as push_all_repos.py and E156 workbook files. -->

# ContradictionMap

ContradictionMap detects contradictory conclusions across Cochrane meta-analyses that share the same primary studies. The pipeline recomputes meta-analyses from Pairwise70, finds cross-review overlap, classifies contradictions, links them to MetaAudit severity, and exports the analysis for the dashboard and manuscript.

## Inputs

- `C:\Users\user\OneDrive - NHS\Documents\Pairwise70\data`
- `C:\MetaAudit\results\audit_results.json`

## Repository Layout

- `detect_contradictions.py`: main pipeline
- `data/study_membership.json`: study to MA membership export
- `data/overlapping_pairs.csv`: overlapping MA pairs
- `results/contradictions.csv`: contradiction-level output
- `results/summary.json`: corpus summary
- `dashboard.html`: interactive dashboard artifact
- `paper/manuscript.md`: manuscript draft
- `tests/test_contradictions.py`: test suite

## Run

```powershell
python detect_contradictions.py
python detect_contradictions.py --max-reviews 100 --min-shared 2
```

## Validate

```powershell
python -m pytest -q
```

## Current Outputs

- `results/contradictions.csv` contains contradiction pairs and contradiction type
- `results/summary.json` contains corpus-level counts and quality linkage summary
- `dashboard.html` is the shipped browser-facing artifact backed by the exported data

## Notes

- `--min-shared` defaults to `2`, which matches the manuscript definition of cross-review overlap.
- The dashboard is stored in the repo root; the pipeline exports the analysis data under `data/` and `results/`.
