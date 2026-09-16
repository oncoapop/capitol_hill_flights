The Editorial Board
Journal of Open Aviation Science (JOAS)
TU Delft OPEN Publishing / OpenSky Network Association

15 September 2026

Subject: Manuscript Submission — Quantifying the Impact of Airspace Modernization on Residential Overflights: A 20-Month Crowdsourced ADS-B Census of Capitol Hill, Burnaby, British Columbia

Dear Editors,

I am pleased to submit our original research manuscript, "Quantifying the Impact of Airspace Modernization on Residential Overflights: A 20-Month Crowdsourced ADS-B Census of Capitol Hill, Burnaby, British Columbia," for consideration for publication in the Journal of Open Aviation Science (JOAS).

Background & Research Scope
Worldwide implementations of Performance-Based Navigation (PBN) and Area Navigation (RNAV/RNP) procedures have improved air traffic management efficiency and reduced airline fuel burn, but they have also concentrated overflight noise into narrow corridors above residential communities. While previous scholarship has explored noise complaints following FAA NextGen rollouts in the United States, independent empirical quantification of terminal airspace redesigns in Canadian airspace has been hindered by proprietary flight-tracking data barriers and limited municipal noise monitoring infrastructure.

This study leverages 20 months of continuous, open-access ADS-B telemetry from the adsb.lol crowdsourced network (January 2025 – August 2026; 20,093 aircraft-day records across 573 operational days) to evaluate the localized impact of NAV CANADA’s Vancouver Airspace Modernization Project (VAMP) on Capitol Hill, a residential summit in Burnaby, BC.

Key Contributions & Findings
1. Reconstruction of Discrete Overflight Passes: Clustered ADS-B telemetry into 24,190 discrete passes using a 10-minute temporal threshold to accurately reflect resident noise event frequency rather than simple aircraft-day tallies.
2. Algorithmic Changepoint Detection: Unsupervised least-squares and binary segmentation identified an abrupt structural step-change on 27 November 2025 (parametric bootstrap 95% CI: 27 Nov – 1 Dec 2025), exactly corresponding to ICAO AIRAC cycle 2513's effective date.
3. Overhead Concentration & Altitude Drop: Overhead commercial arrivals within 500 m of the summit apex surged 6.72-fold from 2.23 to 15.00 passes/day (95% CI 5.84–7.81, p = 8.14e-55). Median altitude dropped by ~2,400 ft (7,700 ft to 5,300 ft ASL) and slant distance decreased by 0.74 km, representing a substantial localized acoustic transformation.
4. Directional Reversal & Corridor Geometry: Arrival tracks underwent a complete substitution from predominantly North–South trajectories (77.6% pre-VAMP) to East–West corridors (93.0% post-VAMP). Lateral profiling revealed that 56% of tracks within 1.5 km enter only in the outermost 100-m perimeter, driven by vertical deconfliction between an overhead eastbound corridor (5,150 ft) and a southern westbound corridor (8,300 ft).
5. Dual Methodological Controls:
   • Internal Negative Controls: Unaffected flight categories (light fixed-wing GA, rate ratio 0.90×, p = 0.12; high-altitude commercial flights ≥10,000 ft, rate ratio 1.03×, p = 0.71) exhibited no increase, refuting receiver-network growth artifacts.
   • Macro External Benchmark: Matched-window validation against official Statistics Canada airport movement counts demonstrated that total YVR airport movements were essentially unchanged (−0.5%), definitively proving that overhead increases represent localized route concentration rather than regional aviation traffic growth.

Alignment with the Journal of Open Aviation Science & TU Delft OPEN Publishing
This study directly aligns with the core open-science mission of JOAS:
• 100% Reproducible Open Science: The entire analysis pipeline, raw record-level datasets, discrete pass extractions, and verification test suites are published openly under MIT and CC BY 4.0 licenses at GitHub: https://github.com/oncoapop/capitol_hill_flights.
• Methodological Transparency: All statistical assertions are verified against an automated programmatic test suite (verify.py) asserting mathematical and census consistency.
• Citizen Environmental Surveillance: Demonstrates how open ADS-B telemetry empowers civil society and affected communities to conduct transparent, audit-grade environmental oversight when official monitoring is unavailable.

Declarations & Compliance Statements
• Conflict of Interest: In the interest of full scientific transparency, the author declares residency on Capitol Hill, Burnaby, within the study zone. The study was initiated following subjective observations of increased aircraft noise. The author has no financial interests in aviation, airlines, air navigation service providers, or acoustic monitoring companies. The study received no external funding. Public availability of all raw data and code guarantees that all findings are subject to independent replication.
• Author Privacy & Address: The author is an independent researcher based in Burnaby, British Columbia, Canada. To preserve residential privacy, no physical street address or postal code is included in the manuscript or correspondence.
• Corresponding Email: damian@oncoapop.com
• Declaration of Generative AI (TU Delft OPEN Publishing / COPE Compliance): In accordance with the policies of TU Delft OPEN Publishing and COPE, generative artificial intelligence and large language model assistants (Google DeepMind Antigravity, Anthropic Claude) were utilized during the preparation of this work to assist in writing/refactoring Python data extraction and statistical analysis scripts, executing algorithmic changepoint routines, formatting tables/figures, and language editing of draft text. Following the use of these tools, the author independently reviewed, executed, and verified all computational code, asserted all statistical figures against authoritative data records, and edited the manuscript. The author assumes full scientific responsibility for the integrity, accuracy, interpretations, and conclusions presented in this publication. AI tools are not credited with authorship.
• Originality: This manuscript is original, has not been published previously, and is not currently under consideration by any other journal.

Thank you for your time and consideration of our manuscript. I look forward to hearing from you.

Sincerely,

Damian Yap, PhD
Independent Researcher
Burnaby, British Columbia, Canada
Email: damian@oncoapop.com
Repository: https://github.com/oncoapop/capitol_hill_flights