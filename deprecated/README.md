# Deprecated and Discredited Legacy Files

The files in this directory have been quarantined and removed from the active research pipeline following an external referee review.

## Contents of this Directory

1. **`monthly_flight_summary_complete_months.csv` & `monthly_flight_summary.csv`**
   - **Reason for Deprecation:** Earlier aggregation run that is mutually inconsistent with the authoritative record-level dataset (`data/capitol_hill_all_flights.csv` / `exports/capitol_hill_all_flights.csv`).
   - Summed to **19,938 records** instead of the authoritative **20,093 records** (discrepancy of 155 records).
   - Claimed **600 days** instead of the actual **573 days with usable data** across 608 calendar days (35 absent dates).
   - Per-month medians, means, minima, maxima, and SEMs in this table disagree with statistics directly computed from record-level data.

2. **`monthly_overflights_boxplot.png` & `monthly_overflights_dotplot.png`**
   - Large infographic-style figures directly generated from the discredited monthly summary table above.

3. **`generate_academic_figures.py` & `academic_figures/`**
   - Interim academic figure generation script from earlier session before the comprehensive referee audit. Superseded by `generate_figures.py` and `figures/`.

4. **`generate_academic_manuscript.py` & `Capitol_Hill_Overflight_Academic_Manuscript.docx`**
   - Interim academic manuscript generator from earlier session that inherited the corrupted Table 2 values, unverified references, and pre-audit numbers. Superseded by `generate_manuscript_v2.py` and `Capitol_Hill_Overflight_Manuscript_v2.docx`.

5. **`generate_report_figures.py` & `generate_pdf_report.py` & `report_figures/`**
   - Legacy ReportLab 4-page infographic PDF generator and figures, superseded by the peer-reviewed IMRAD academic manuscript and publication-standard figures.

6. **`analyze.py` & `flight_density_heatmap.png`**
   - Legacy analysis and aggregation script that produced the discredited monthly summary CSV, boxplot, and density heatmap. Superseded by the reproducible `analysis/` pipeline (`build_all.py`).

7. **`Capitol_Hill_Overflight_Independent_Study_2025-2026.pdf`**
   - Legacy 12-page study report citing discredited summary counts (19,938 records, 600 days, 125 max daily flights). Superseded by `Capitol_Hill_Overflight_Manuscript_v2.docx`.

## Authoritative Source of Truth (Active Tree)

All revised analyses, tables, figures, and manuscript statistics in the active repository tree are generated strictly from:
- `data/capitol_hill_all_flights.csv` (authoritative 20,093 records, 2,050 unique ICAO addresses)
- `data/capitol_hill_passes.csv` (reconstructed discrete passes, 24,190 passes)
- `data/daily_flight_counts_complete_months.csv` (consistent with the above; used for calendar date coverage)
- Official Statistics Canada tables (23-10-0296, 23-10-0303, 23-10-0298)
- `analysis/build_all.py` (master analysis orchestrator emitting `analysis/results.json`)
- `generate_figures.py` (generates 300 DPI figures in `figures/`)
- `generate_manuscript_v2.py` (generates `Capitol_Hill_Overflight_Manuscript_v2.docx`)
- `verify.py` (automated replication suite asserting agreement)

Do not use or reference the files in this directory for any scientific or reporting purpose.
