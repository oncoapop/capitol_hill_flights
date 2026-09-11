# Changelog — Capitol Hill Overflight Study Revision (v2.0)

Date: 2026-09-10  
Author: Damian Yap, PhD  
Branch: `revision-v2`  
Tag: `v1.0-superseded` (applied to prior repository HEAD)

Following an external referee review, all analyses, summary tables, figures, and manuscript text were systematically audited and rebuilt from a single authoritative source of truth (`data/capitol_hill_all_flights.csv`, containing 20,093 records across 2,050 unique ICAO addresses). The previous aggregation (`monthly_flight_summary_complete_months.csv`) has been quarantined to `deprecated/`.

Every numeric value changed between the superseded manuscript/report and this revision is documented below.

---

## 1. Fatal Internal Inconsistencies & Dataset Reconciliation

| Item | Old Value | Corrected Value | Reason for Change |
|---|---|---|---|
| **Table 2 Total Flights (M1)** | 19,938 | **20,093** | Old table was derived from an incomplete legacy aggregation run. Recomputed directly from record-level data. |
| **Table 2 Days with Data (M1)** | 600 days | **573 days** (out of 608 calendar days) | Old table counted calendar days irregularly; 35 days in the 20-month window had missing archives. |
| **Maximum Single-Day Overflights (M2)** | 125 (26 Aug 2026) | **128 (26 Aug 2026)** | Corrected from authoritative daily counts. |
| **Monthly Means & SEMs (M1, M2)** | Discredited values in old Table 2 | Recomputed strictly from record-level counts (see `analysis/monthly_summary_recomputed.csv`) | Replaced corrupted summary rows. |
| **Fleet: DH8D (Dash 8 Q400) (M3)** | 3,407 (17.0%) | **3,432 (17.08%)** | Computed from 20,093 record-level `type_code` census. |
| **Fleet: C172 (Cessna Skyhawk) (M3)** | 1,873 (9.3%) | **1,882 (9.37%)** | Computed from record-level census. |
| **Fleet: B38M (Boeing 737 MAX 8) (M3)** | 1,228 (6.1%) | **1,240 (6.17%)** | Computed from record-level census. |
| **Fleet: B738 (Boeing 737-800) (M3)** | 940 (4.7%) | **951 (4.73%)** | Computed from record-level census. |
| **Fleet: Boeing 7xx Family (M3)** | 4,115 (20.5%) | **3,985 (19.83%)** | Exact count of all Boeing 7-series aircraft (`B7*`) in dataset. |
| **Night Traffic Proportion (M4)** | "< 3.4%" (23:00–06:00) | **5.14%** (1,032 of 20,093 records, 23:00–05:59) | Recomputed from exact `cpa_hour_local` timestamps. Unsupported claims of late-night cargo/medevac attribution removed. |

---

## 2. Methodological Corrections

| Item | Old Text / Specification | Corrected Text / Specification | Justification |
|---|---|---|---|
| **Observation Denominators (M5)** | "330 pre-VAMP days, 278 post-VAMP days" | **317 pre-days with data (330 calendar days), 256 post-days with data (278 calendar days)** | Clarified distinction between calendar days and operational days with usable archives. |
| **Bootstrap Method (M6a)** | Claimed BCa bootstrap | **Percentile bootstrap (4,000 day-resamples)** | Corrected text to accurately reflect the non-parametric percentile bootstrap implemented in code. |
| **Callsign-Based Classification (M6b)** | Claimed classification used "callsign prefix" | **Broadcast `type_code` combined with CPA barometric altitude** | The `callsign` column is empty in all 20,093 records. Classification methodology corrected and validated with vertical rates. |
| **CPA Vertical Rate Telemetry (M6c)** | Claimed vertical rate was directly extracted at CPA | **Vertical rate computed from sequential altitude timestamps within the 1.5 km monitoring zone** | Raw file lacks a native vertical-rate column; computed from `matched_points_json` trajectory segments. |
| **Changepoint Identification (M7)** | Claimed "visual inspection" and deferred algorithmic detection to future work | **Exhaustive least-squares single changepoint detection confirms 2025-11-27** (cross-checked with `ruptures` PELT/Binseg) | Algorithmic detection implemented in §2.2. Bootstrap 95% CI degenerate on 27 Nov 2025. |
| **Unit of Observation (M12)** | Ambiguous mixing of flights and aircraft-days | **Primary results reported as discrete overflight passes** | 24,190 passes identified using a 10-minute gap threshold (inflation factor 1.204 over the 20,093 aircraft-days; pre 1.153, post 1.223). |

---

## 3. Substantive Additions & Statistical Targets

- **Direction of Travel (§2.6, M10):** Added heading band distribution table (E 060–120°, W 240–300°, N 330–030°, S 150–210°, Other). Demonstrates that commercial arrival overflights experienced a structural heading reversal from North–South (1,518 pre vs. 590 post) to East–West (94 pre vs. 10,321 post), while control categories maintained unchanged directional patterns.
- **Corridor Geometry & Boundary Truncation (§2.7, M11):** Localised the Eastbound corridor (median lat 49.2860°N, 0.10 km south of summit, median alt 5,150 ft) and Westbound corridor (median lat 49.2740°N, 1.44 km south, median alt 8,300 ft). Documented that 56.0% of post-VAMP arrival records enter in the outermost 100 meters (1.4–1.5 km), establishing that the westbound corridor is truncated by the 1.5 km boundary. The manuscript now leads with the inner 500 m measure.
- **Seasonality Robustness (§2.8, M9):** Season-matched sensitivity analysis (Jan–Aug 2025 vs. Jan–Aug 2026) confirms significant rate ratios: 6.84× (1.5 km arrivals), 6.31× (500 m arrivals), and 0.92× (light GA control).
- **External Validation against Statistics Canada (§2.9):** Benchmarked matched Jan–Jun 2025 vs. 2026 movements from Table 23-10-0296. YVR total airport movements were essentially flat (ratio 0.995), refuting macroeconomic traffic growth, while GA training airports declined (combined ratio 0.866), matching the ADS-B light GA decline (0.83).
- **Helicopter Finding Treated as Limitation (§4):** Documented secondary changepoint on 28 April / 3 May 2026 for S-76/AW139 helicopters. Explicitly decoupled from VAMP and contextualized with Vancouver Harbour movements (+21.3%) and fleet equipage confounds.

---

## 4. Factual Corrections & Reference Audit

- **Privacy / LADD / PIA Claims (M13a):** Deleted claims that raw ADS-B archives defeat PIA/LADD privacy protections (PIA aircraft broadcast alternate anonymous 24-bit addresses over the air; LADD is an FAA ground-feed filter).
- **Canadian ADS-B Mandate (M13b):** Corrected CAR 605.35 (which regulates Mode C transponders) to NAV CANADA's phased Class A (Aug 2023) and Class B (May 2024) mandates, noting that Class C/D/E airspace has no active mandate.
- **VAMP Phased Rollout (M14):** Reframed from "final implementation" to a two-stage rollout (November 2025 conventional arrivals; Spring 2026 RNP arrivals) with the 180-day review noted as pending.
- **AIRAC Cycle Duration (M15):** Corrected cycle duration from 56 days to **28 days** (Cycle 2513 ran 27 Nov – 25 Dec 2025).
- **Capitol Hill Distance to YVR:** Corrected from "approximately 14 km" to **17.8 km** (great-circle distance).
- **UAT 978 MHz:** Removed mention of 978 MHz UAT (US-only standard not utilized in Canadian airspace).
- **Acoustic Assertions:** Softened acoustic claims from unmeasured decibel levels to geometric proximity and 3D slant distance metrics.
- **References Audited:**
  - *Removed:* Asensio et al. (2017) (unverifiable; COVID lockdown paper conflation), Lim et al. (2023) (unverifiable), NAV CANADA (2025) (unpublished post-implementation review).
  - *Integrated:* Bai & Perron (2003) (structural breaks), Sun et al. (2019) (OpenAP aircraft performance), Schäfer et al. (2020) (updated page range).
- **Target Journal:** Formatted for the *Journal of Open Aviation Science* (JOAS), including mandatory generative-AI disclosure.
