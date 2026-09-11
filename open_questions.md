# Open Questions and Methodological Limitations

This document plainly records unresolved questions, structural data boundaries, and analytical ambiguities identified during the revision process.

## 1. Westbound Corridor Boundary Truncation

- **Observation:** The primary westbound commercial arrival corridor traverses south of Capitol Hill with a median CPA latitude of 49.2740°N (1.44 km south of the summit) and median CPA altitude of 8,300 ft.
- **Limitation:** The study's 1.50 km geodesic monitoring radius cuts directly through the northern edge of this corridor. A radius-sensitivity scan demonstrates that 56.0% of post-VAMP arrival records (6,222 out of 11,103) enter only within the outermost 100 meters (1.4 to 1.5 km).
- **Resolution:** The manuscript must explicitly disclose this truncation, refrain from claiming a total census of westbound arrival traffic, and lead with the inner 500 m core metric (which is fully contained within the residential summit zone). Full quantification of the westbound corridor will require expanding the monitoring radius to 2.5–3.0 km in future research.

## 2. Helicopter Traffic Increase (April–May 2026)

- **Observation:** Helicopter passes over Capitol Hill increased from 1.59 to 4.38 passes/day (rate ratio 2.75, p = 2.65e-06), with a detected changepoint around 28 April / 3 May 2026. This was driven almost exclusively by heavy twin-engine types (Sikorsky S-76 and AgustaWestland AW139), while light training helicopters (Robinson R44) slightly declined (rate ratio 0.83).
- **Ambiguity:** Statistics Canada Table 23-10-0296 shows that total movements at Vancouver Harbour Water Aerodrome (CXH) rose 21.3% over the matched Jan–Jun window. However, S-76/AW139 passes over Capitol Hill rose by over 60-fold over the same period.
- **Resolution:** A 21% volume growth cannot explain a multi-fold increase. The residual discrepancy must arise from: (a) new commercial ADS-B Out equipage on regional helicopter fleets, (b) an unannounced corridor realignment between Vancouver Harbour, helipads, and eastern BC destinations, or (c) a combination of both. Because ADS-B telemetry does not include origin-destination flight plans, this attribution cannot be resolved from these data alone and is reported strictly as an unassigned limitation, dated five months after VAMP.

## 3. Absence of Ground Acoustic Measurements

- **Limitation:** ADS-B telemetry records spatial coordinates, barometric altitude, ground speed, and heading, but does not capture acoustic sound pressure levels (dB(A)).
- **Resolution:** The manuscript does not claim modeled sound levels. Instead, geometric proximity metrics (3D slant distance reduction from 2.26 km to 1.52 km, median altitude reduction from 7,700 ft to 5,300 ft) are reported alongside pass counts. Physical acoustic exposure should be quantified in follow-on work pairing ADS-B telemetry with calibrated Class 1 noise monitors measuring N-Above thresholds.

## 4. NAV CANADA Post-Implementation Review Status

- **Limitation:** The manuscript cannot cite a "final implementation report" for VAMP because NAV CANADA's 180-day post-implementation review is ongoing and unpublished as of mid-2026.
- **Resolution:** VAMP is described accurately as a two-stage operational project: conventional arrival procedures implemented on 27 November 2025 (AIRAC cycle 2513), followed by RNP procedure rollouts in spring 2026. The formal review is noted as pending publication.
