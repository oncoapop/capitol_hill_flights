"""
Revised Academic Manuscript Generator (v2.0)
Formats the complete peer-reviewed study for the Journal of Open Aviation Science (JOAS).
Rebuilt from authoritative data (results.json), embeds regenerated figures from figures/,
and provides clickable APA-style verified references and mandatory AI disclosure.

Output: Capitol_Hill_Overflight_Manuscript_v2.docx
Date: 2026-09-10
"""
import json
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

RESULTS_FILE = Path("analysis/results.json")
OUTPUT_DOCX = Path("Capitol_Hill_Overflight_Manuscript_v2.docx")
FIGS_DIR = Path("figures")

def _add_hyperlink(paragraph, url: str, text: str, font_size=10, color=(0, 0, 238)):
    part = paragraph.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")

    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rPr.append(rFonts)

    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(font_size * 2))
    rPr.append(sz)

    c_el = OxmlElement("w:color")
    c_el.set(qn("w:val"), "{:02X}{:02X}{:02X}".format(*color))
    rPr.append(c_el)

    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)

    rStyle = OxmlElement("w:rStyle")
    rStyle.set(qn("w:val"), "Hyperlink")
    rPr.append(rStyle)

    new_run.append(rPr)
    t_el = OxmlElement("w:t")
    t_el.text = text
    t_el.set(qn("xml:space"), "preserve")
    new_run.append(t_el)

    hyperlink.append(new_run)
    paragraph._element.append(hyperlink)
    return hyperlink

def _set_cell_shading(cell, color_hex: str):
    shading_elm = cell._element.get_or_add_tcPr()
    shading = shading_elm.makeelement(qn("w:shd"), {
        qn("w:fill"): color_hex,
        qn("w:val"): "clear",
    })
    shading_elm.append(shading)

def _add_run(paragraph, text, bold=False, italic=False, size=12, font_name="Times New Roman", color=None):
    run = paragraph.add_run(text)
    run.font.name = font_name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)
    return run

def _make_paragraph(doc, text="", style="Normal", alignment=None, space_after=None, space_before=None, line_spacing=None):
    p = doc.add_paragraph(text, style=style)
    if alignment is not None:
        p.alignment = alignment
    fmt = p.paragraph_format
    if space_after is not None:
        fmt.space_after = Pt(space_after)
    if space_before is not None:
        fmt.space_before = Pt(space_before)
    if line_spacing is not None:
        fmt.line_spacing = line_spacing
    return p

def _body(doc, text):
    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = WD_LINE_SPACING.DOUBLE
    _add_run(p, text, size=12)
    return p

def _heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = "Times New Roman"
        run.font.color.rgb = RGBColor(0, 0, 0)
    return h

def build_manuscript():
    print("=== BUILDING REVISED ACADEMIC MANUSCRIPT (v2.0) ===")
    with open(RESULTS_FILE) as f:
        res = json.load(f)
        
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    style.paragraph_format.line_spacing = WD_LINE_SPACING.DOUBLE
    style.paragraph_format.space_after = Pt(0)

    for level in range(1, 4):
        hs = doc.styles[f"Heading {level}"]
        hs.font.name = "Times New Roman"
        hs.font.color.rgb = RGBColor(0, 0, 0)
        hs.font.bold = True
        hs.font.size = Pt({1: 14, 2: 12, 3: 12}[level])
        hs.font.italic = (level == 3)

    # ── TITLE PAGE ────────────────────────────────────────────────────────
    p = _make_paragraph(doc, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)
    _add_run(p, "Quantifying the Impact of Airspace Modernization on Residential Overflights:\n", bold=True, size=16)
    _add_run(p, "A 20-Month Crowdsourced ADS-B Census of Capitol Hill, Burnaby, British Columbia", bold=True, size=14)

    p = _make_paragraph(doc, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    _add_run(p, "Damian Yap, PhD", bold=True, size=12)

    p = _make_paragraph(doc, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    _add_run(p, "Independent Researcher, Burnaby, British Columbia, Canada", italic=True, size=11)

    p = _make_paragraph(doc, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)
    _add_run(p, "Correspondence: D. Yap (damian@oncoapop.com)", size=10)

    p = _make_paragraph(doc, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)
    _add_run(p, "Target Journal: Journal of Open Aviation Science (JOAS)\nManuscript Version: 2.0 (Post-Referee Revision)\nDate: September 2026", italic=True, size=10)

    p = _make_paragraph(doc, alignment=WD_ALIGN_PARAGRAPH.LEFT, space_before=12, space_after=6)
    _add_run(p, "Keywords: ", bold=True, size=11)
    _add_run(p, "ADS-B; crowdsourced surveillance; aircraft overflight census; airspace modernization; "
                "Performance-Based Navigation; VAMP; changepoint detection; community noise exposure; "
                "Vancouver International Airport", size=11)

    doc.add_page_break()

    # ── ABSTRACT ──────────────────────────────────────────────────────────
    _heading(doc, "Abstract", level=1)
    
    abs_text = (
        "Background: Airspace modernization programs globally employ Performance-Based Navigation (PBN) "
        "to increase throughput and reduce emissions, but frequently concentrate flight tracks over residential "
        "communities. On 27 November 2025 (AIRAC cycle 2513), NAV CANADA implemented the first phase of the "
        "Vancouver Airspace Modernization Project (VAMP) for Vancouver International Airport (YVR). Independent "
        "empirical quantification of localized overflight changes beneath the revised corridors has been lacking.\n\n"
        "Methods: We conducted a continuous 20-month census of aircraft overflights within a 1.5-km geodesic radius "
        "(and an inner 500-m core zone) of Capitol Hill, Burnaby, BC (17.8 km east-northeast of YVR; summit elevation "
        "115 m ASL) from 1 January 2025 to 31 August 2026 (573 days with usable data across 608 calendar days). Aircraft "
        "trajectories were extracted from open crowdsourced ADS-B archives (adsb.lol globe_history). Discrete overflight "
        "passes (n = 24,190) were reconstructed using a 10-minute clustering threshold (inflation factor 1.204 over the "
        "20,093 aircraft-day records). Pre- and post-intervention daily pass rates were evaluated across operational categories "
        "using rate ratios (RR) with 4,000 percentile bootstrap 95% confidence intervals and two-sided Mann–Whitney U tests. "
        "Light fixed-wing aircraft and commercial traffic ≥10,000 ft served as negative controls, benchmarked against official "
        "Statistics Canada airport movement data.\n\n"
        "Results: Algorithmic least-squares changepoint detection identified an abrupt structural break on 27 November 2025 "
        "(parametric bootstrap 95% CI: 27 Nov – 1 Dec 2025). Commercial arrival passes within the 500-m summit core increased "
        "6.73-fold from 2.23 to 15.03 passes/day (95% CI 5.85–7.81; p = 1.03e-54), while median CPA altitude decreased from "
        "7,700 ft to 5,300 ft (Δ = 2,400 ft) and 3D slant distance decreased from 2.26 km to 1.52 km. Commercial arrivals "
        "within 1.5 km increased 7.87-fold (6.57 to 51.71 passes/day; 95% CI 7.15–8.67; p = 2.23e-93), accompanied by a complete "
        "directional reversal from North–South to East–West tracks. Negative control categories showed no significant increase "
        "(light GA RR = 0.90, 95% CI 0.78–1.03, p = 0.13; high commercial RR = 1.05, 95% CI 0.80–1.37, p = 0.76). Statistics Canada "
        "data confirmed YVR total movements were flat (−0.5%), refuting regional traffic growth.\n\n"
        "Conclusions: VAMP implementation produced an immediate, persistent, and statistically significant concentration of "
        "low-altitude commercial arrivals above Capitol Hill. These findings demonstrate that open, uncensored ADS-B archives "
        "enable rigorous, independent, and reproducible community-level monitoring of airspace interventions."
    )
    _body(doc, abs_text)
    doc.add_page_break()

    # ── 1. INTRODUCTION ───────────────────────────────────────────────────
    _heading(doc, "1. Introduction", level=1)
    
    _body(doc, (
        "Environmental noise from aviation is an established public health concern. Chronic exposure to aircraft "
        "overflights has been linked in large-scale epidemiological investigations to elevated risks of cardiovascular "
        "disease, myocardial infarction, hypertension, arterial stiffness, severe sleep disruption, and impaired cognitive "
        "development in children (Basner et al., 2014; Hansell et al., 2013; Peters et al., 2018). Importantly, modern "
        "health research emphasizes that adverse autonomic reactions and nighttime awakenings occur even at moderate "
        "sound exposure levels outside traditional regulatory contours, driven primarily by the frequency and peak sound "
        "levels of individual overflight events rather than 24-hour time-averaged acoustic energy."
    ))

    _body(doc, (
        "Over the past decade, civil aviation authorities worldwide have undertaken extensive airspace modernization "
        "initiatives. Programmes such as the Federal Aviation Administration's (FAA) NextGen in the United States, Europe's "
        "Single European Sky ATM Research (SESAR), and modernization projects across Canada have transitioned air traffic "
        "management from legacy ground-based radio navigation (VOR/DME) and tactical radar vectoring to satellite-based "
        "Performance-Based Navigation (PBN), Area Navigation (RNAV), and Required Navigation Performance (RNP). While PBN "
        "significantly improves navigational precision, fuel efficiency, and terminal capacity, it introduces a well-documented "
        "structural consequence: the extreme spatial concentration of flight paths into narrow, highly repeatable lateral corridors "
        "(Brenner & Hansman, 2017; GAO, 2021)."
    ))

    _body(doc, (
        "Whereas conventional radar vectoring dispersed flights across a broad geographic swath, PBN procedures concentrate "
        "repeated low-altitude overflights over the exact same residential parcels. A comprehensive audit by the United States "
        "Government Accountability Office (GAO, 2021) concluded that PBN implementations created severe community backlash "
        "and intense noise corridors across multiple metropolitan areas. The GAO specifically mandated the adoption of "
        "supplemental event-based noise metrics—such as the Number-of-events Above threshold (N-Above)—noting that conventional "
        "Day-Night Average Sound Level (DNL) contours systematically average out and obscure the intrusive impact of frequent, "
        "punctual overflights on suburban populations (Brenner & Hansman, 2017; GAO, 2021)."
    ))

    _body(doc, (
        "In southwestern British Columbia, NAV CANADA initiated the Vancouver Airspace Modernization Project (VAMP) to redesign "
        "terminal airspace for Vancouver International Airport (YVR). VAMP's stated objectives include modernizing arrival routes, "
        "facilitating Continuous Descent Operations (CDO), and reducing greenhouse gas emissions (NAV CANADA, 2022). The first "
        "operational phase of VAMP was implemented on 27 November 2025, coinciding with ICAO Aeronautical Information Regulation "
        "and Control (AIRAC) cycle 2513, introducing revised arrival procedures over municipalities east of YVR, including Burnaby "
        "and New Westminster."
    ))

    _body(doc, (
        "To date, no independent, empirical post-implementation evaluation of VAMP's overflight impacts has been published. "
        "Official pre-implementation documentation relied on simulated noise contours and projected traffic assignments "
        "(NAV CANADA, 2022). To provide an objective, transparent, and reproducible empirical assessment, this study employs "
        "crowdsourced Automatic Dependent Surveillance–Broadcast (ADS-B) telemetry archives (adsb.lol Community, 2025–2026). "
        "Extending the crowdsourced surveillance paradigm established by the OpenSky Network (Schäfer et al., 2014; Strohmeier "
        "et al., 2021), we present a 20-month continuous census of overflights at Capitol Hill, Burnaby, BC, evaluating changes "
        "in frequency, proximity, altitude, and heading, validated against official Statistics Canada aviation movement counts."
    ))

    # ── 2. BACKGROUND ─────────────────────────────────────────────────────
    _heading(doc, "2. Background", level=1)
    _heading(doc, "2.1 The Vancouver Airspace Modernization Project (VAMP)", level=2)

    _body(doc, (
        "Vancouver International Airport (YVR) is Canada's second busiest airport, handling over 25 million passengers and "
        "approximately 260,000 aircraft movements annually. The terminal airspace surrounding YVR is constrained by international "
        "borders to the south, the Coast Mountains to the north, and complex terrain to the east. Following an initial proposal "
        "and public consultation phase initiated in 2022 (NAV CANADA, 2022), NAV CANADA scheduled a two-stage operational rollout "
        "for VAMP. The primary structural phase took effect on 27 November 2025 (AIRAC cycle 2513), introducing revised conventional "
        "arrival corridors. A secondary phase introducing specialized RNP procedures rolled out in spring 2026. Consistent with "
        "ICAO standards, aeronautical publications adhere strictly to a 28-day AIRAC cycle (Cycle 2513 spanning 27 November to "
        "25 December 2025). As of mid-2026, the official 180-day post-implementation review of VAMP remains underway."
    ))

    _heading(doc, "2.2 Crowdsourced ADS-B Telemetry and Regulatory Mandates", level=2)

    _body(doc, (
        "ADS-B is a satellite-enabled surveillance technology whereby aircraft avionics broadcast unencrypted 1090 MHz Extended "
        "Squitter (1090ES) radio messages containing 24-bit ICAO airframe addresses, barometric altitude, GNSS position, ground speed, "
        "and heading at sub-second intervals (ICAO, 2020; RTCA, 2011). In Canada, Transport Canada and NAV CANADA have implemented "
        "a phased ADS-B Out equipage mandate: Class A airspace (above 18,000 ft ASL) became mandatory on 10 August 2023, followed "
        "by Class B airspace (12,500 ft to 17,999 ft ASL) on 16 May 2024 (Transport Canada, 2023). Class C, D, and E terminal "
        "airspaces have no active ADS-B mandate in effect until at least 2028. Consequently, commercial air transport fleets operating "
        "in Canadian controlled airspace are universally ADS-B equipped, whereas general aviation and VFR traffic operate under no "
        "statutory mandate. This institutional framework ensures complete surveillance capture for commercial operations while "
        "maintaining stable baseline equipage in local general aviation."
    ))

    _body(doc, (
        "Surveillance data were acquired from the adsb.lol open-source community archive (adsb.lol Community, 2025–2026). "
        "Unlike commercial tracking aggregators (e.g., FlightAware, FlightRadar24) that modify live feeds to honour administrative "
        "censorship registries such as the FAA Limiting Aircraft Data Display (LADD), adsb.lol captures and archives physical-layer "
        "1090 MHz radio broadcasts directly from volunteer-operated Software-Defined Radio (SDR) receiver stations without commercial "
        "redaction. This provides a transparent, scientific public record suitable for independent academic research."
    ))

    _heading(doc, "2.3 Study Area", level=2)

    _body(doc, (
        "Capitol Hill is a prominent residential landform in north-central Burnaby, British Columbia (49.2869°N, 122.9853°W), "
        "rising to an elevation of approximately 115 m ASL. Located 17.8 km east-northeast of YVR, the hill sits directly south of "
        "the Burrard Inlet maritime waterway and north of the Trans-Canada highway corridor (Figure 1). Capitol Hill's elevated "
        "topography provides unobstructed radio line-of-sight to the terminal arrival paths converging from the interior of British "
        "Columbia into YVR. The study establishes a primary 1.5-km geodesic monitoring circle and a conservative 500-m core "
        "summit zone."
    ))

    # Embed Figure 1
    fig1_path = FIGS_DIR / "fig1_study_area.png"
    if fig1_path.exists():
        doc.add_picture(str(fig1_path), width=Inches(4.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(12)
        _add_run(p, "Figure 1. ", bold=True, size=10)
        _add_run(p, "Geographic monitoring geometry of Capitol Hill, Burnaby, BC (summit: 49.2869°N, 122.9853°W; 115 m ASL). "
                    "The primary 1.5-km geodesic monitoring zone (dashed line) and 500-m inner core zone (solid line) are shown "
                    "relative to the Burrard Inlet waterway to the north.", size=10)

    # ── 3. MATERIALS AND METHODS ──────────────────────────────────────────
    _heading(doc, "3. Materials and Methods", level=1)
    _heading(doc, "3.1 Data Acquisition and Streaming Pipeline", level=2)

    _body(doc, (
        "Historical trajectory telemetry was harvested from the public adsb.lol archive mirrors covering 1 January 2025 through "
        "31 August 2026 (globe_history_2025 and globe_history_2026). Each daily tarball contains compressed per-aircraft JSON trace "
        "files recorded in readsb format. To process terabytes of global tracking data efficiently, a streaming byte-level "
        "extractor (ConcatStreamReader) was deployed, intercepting chunked HTTP responses and decompressing archive members in memory "
        "without disk writes. Over the 20-month monitoring period, 25.84 million individual global aircraft traces were evaluated."
    ))

    _heading(doc, "3.2 Unit of Observation and Discrete Pass Reconstruction", level=2)

    _body(doc, (
        "In the primary database, raw records are indexed by unique (date, icao) pairs, representing aircraft-days rather than "
        "individual flights. An aircraft transiting the terminal area multiple times in a single day (e.g., regional turboprops, "
        "flight training aircraft) produces multiple passes recorded within a single record's trajectory array (matched_points_json). "
        "To establish a true flight-event census, discrete passes were reconstructed algorithmically by clustering trajectory "
        "timestamps across temporal gaps."
    ))

    _body(doc, (
        "Temporal gap sensitivity analysis demonstrated extreme bimodal stability: the median intra-pass point interval was 3.65 s, "
        "with 95.23% of intervals ≤ 60 s, while inter-pass returns occurred hours later. Evaluating clustering thresholds yielded "
        "24,403 passes at 5 min, 24,190 passes at 10 min, 23,945 passes at 15 min, and 23,462 passes at 30 min. The standard "
        "10-minute threshold was adopted, defining a total of 24,190 discrete passes (overall inflation factor of 1.204 relative "
        "to the 20,093 aircraft-days; 1.153 pre-VAMP and 1.223 post-VAMP). For each pass, the Closest Point of Approach (CPA) was "
        "defined as the point minimizing great-circle Haversine distance (Sinnott, 1984) to the Capitol Hill reference coordinates."
    ))

    _heading(doc, "3.3 Operational Categorisation and Vertical-Rate Validation", level=2)

    _body(doc, (
        "Because ADS-B broadcast callsigns are frequently omitted or null in crowdsourced receivers (empty in all 20,093 deposited "
        "records), aircraft classification was established strictly using broadcast ICAO airframe type codes (type_code) combined "
        "with barometric altitude at CPA into four operational categories:\n"
        "1. Commercial Arrivals: Airline passenger jets and regional turboprops (e.g., B738, B38M, DH8D, A321, E295, CRJ9) at CPA "
        "barometric altitude < 10,000 ft ASL.\n"
        "2. Commercial High (Control): Identical airline types operating at en-route altitudes ≥ 10,000 ft ASL.\n"
        "3. Business and Private: Purpose-built business jets and corporate turboprops (e.g., King Air 350, Citation, Challenger, Learjet).\n"
        "4. Light and Floatplane (Control): Light piston singles and twins, flight training airframes (C172, PA28), and coastal floatplanes (DHC2, DHC3, DHC6). "
        "Crucially, helicopters were excluded from this negative control due to an independent late-spring 2026 fleet signal (§5.3).\n\n"
        "A total of 409 records (2.04%) could not be uniquely categorized due to missing or non-standard ICAO type codes and were excluded "
        "from category totals. Operational categories were independently validated by calculating trajectory vertical rates (ft/min) "
        "within the study zone: commercial arrivals demonstrated strong descent (median −927 ft/min; 68.6% actively descending), "
        "commercial high demonstrated active en-route climb/cruise (median +2,289 ft/min; 93.6% climbing/level), while light aircraft "
        "exhibited level flight (median 0 ft/min), confirming robust categorization without callsign reliance."
    ))

    _heading(doc, "3.4 Statistical Testing and Algorithmic Changepoint Detection", level=2)

    _body(doc, (
        "Daily overflight rates were computed using operational days with usable archives as denominators: 317 days in the pre-intervention "
        "period (across 330 calendar days) and 256 days in the post-intervention period (across 278 calendar days), accounting for 35 missing "
        "calendar dates. Rate ratios (RR = mean post / mean pre) were evaluated. Confidence intervals (95%) were estimated via a non-parametric "
        "percentile bootstrap using 4,000 day-level resamples, and two-sided Mann–Whitney U tests evaluated distribution shifts.\n\n"
        "To formally verify the intervention date without prior assumption, an exhaustive least-squares single changepoint search was executed "
        "across all 573 observation days, cross-validated against the PELT and binary segmentation algorithms (Truong et al., 2020; "
        "Bai & Perron, 2003; Aminikhanghahi & Cook, 2017). Parametric bootstrap simulations (4,000 iterations) evaluated changepoint stability."
    ))

    # ── 4. RESULTS ────────────────────────────────────────────────────────
    _heading(doc, "4. Results", level=1)
    _heading(doc, "4.1 Algorithmic Changepoint Verification", level=2)

    _body(doc, (
        "Exhaustive least-squares scanning detected an abrupt, singular structural break in daily overflight volume on 27 November 2025 "
        "(index 317), exactly coinciding with the implementation of ICAO AIRAC cycle 2513. Binary segmentation confirmed a structural break "
        "at 30 November 2025, and PELT identified 24 November 2025. Parametric bootstrap resamples demonstrated that 71.3% of simulated "
        "changepoints fell precisely on 27 November 2025, with a 95% bootstrap confidence interval spanning 27 November to 1 December 2025. "
        "This confirms algorithmically that the overflight increase was an immediate consequence of VAMP rather than gradual traffic growth."
    ))

    _heading(doc, "4.2 Overflight Census and Rate Ratios", level=2)

    _body(doc, (
        "Across the 20-month study period, 20,093 aircraft-days and 24,190 discrete passes involving 2,050 unique ICAO airframes were "
        "recorded. Figure 2 and Table 1 present the pass-based daily overflight rates and rate ratios across operational categories."
    ))

    # Embed Figure 2
    fig2_path = FIGS_DIR / "fig2_rate_ratios_forest.png"
    if fig2_path.exists():
        doc.add_picture(str(fig2_path), width=Inches(4.5))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(12)
        _add_run(p, "Figure 2. ", bold=True, size=10)
        _add_run(p, "Forest plot of pass-based overflight rate ratios (post / pre VAMP) with 95% percentile bootstrap confidence intervals "
                    "(4,000 day-resamples). Dark bars represent intervention categories; light bars represent negative controls. "
                    "The vertical line at 1.0 indicates no change.", size=10)

    # ── Table 1: Rate Ratios ──────────────────────────────────────────────
    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    _add_run(p, "Table 1. ", bold=True, size=10)
    _add_run(p, "Pass-based daily overflight rates, rate ratios (RR), 95% bootstrap confidence intervals, and Mann–Whitney U test p-values.", size=10)

    cats = res["section2_4_rate_ratios"]["categories"]
    t1_data = [
        ["Operational Category", "Pre-VAMP\n(passes/day)", "Post-VAMP\n(passes/day)", "Rate Ratio\n(95% CI)", "p-value"],
        ["Commercial arrivals (≤500 m)", f"{cats['commercial_arrivals_500m']['pre_mean']:.2f}", f"{cats['commercial_arrivals_500m']['post_mean']:.2f}",
         f"{cats['commercial_arrivals_500m']['rate_ratio']:.2f}× ({cats['commercial_arrivals_500m']['ci_95_percentile'][0]:.2f}–{cats['commercial_arrivals_500m']['ci_95_percentile'][1]:.2f})", f"{cats['commercial_arrivals_500m']['p_value']:.2e}"],
        ["Commercial arrivals (≤1.5 km)", f"{cats['commercial_arrivals_1500m']['pre_mean']:.2f}", f"{cats['commercial_arrivals_1500m']['post_mean']:.2f}",
         f"{cats['commercial_arrivals_1500m']['rate_ratio']:.2f}× ({cats['commercial_arrivals_1500m']['ci_95_percentile'][0]:.2f}–{cats['commercial_arrivals_1500m']['ci_95_percentile'][1]:.2f})", f"{cats['commercial_arrivals_1500m']['p_value']:.2e}"],
        ["Business & private aircraft", f"{cats['business_private']['pre_mean']:.2f}", f"{cats['business_private']['post_mean']:.2f}",
         f"{cats['business_private']['rate_ratio']:.2f}× ({cats['business_private']['ci_95_percentile'][0]:.2f}–{cats['business_private']['ci_95_percentile'][1]:.2f})", f"{cats['business_private']['p_value']:.2e}"],
        ["All aircraft combined (≤1.5 km)", f"{cats['all_aircraft_1500m']['pre_mean']:.2f}", f"{cats['all_aircraft_1500m']['post_mean']:.2f}",
         f"{cats['all_aircraft_1500m']['rate_ratio']:.2f}× ({cats['all_aircraft_1500m']['ci_95_percentile'][0]:.2f}–{cats['all_aircraft_1500m']['ci_95_percentile'][1]:.2f})", f"{cats['all_aircraft_1500m']['p_value']:.2e}"],
        ["Control: Light fixed-wing GA", f"{cats['control_light_fixed_wing_floatplane']['pre_mean']:.2f}", f"{cats['control_light_fixed_wing_floatplane']['post_mean']:.2f}",
         f"{cats['control_light_fixed_wing_floatplane']['rate_ratio']:.2f}× ({cats['control_light_fixed_wing_floatplane']['ci_95_percentile'][0]:.2f}–{cats['control_light_fixed_wing_floatplane']['ci_95_percentile'][1]:.2f})", f"{cats['control_light_fixed_wing_floatplane']['p_value']:.2f}"],
        ["Control: Commercial ≥10,000 ft", f"{cats['control_commercial_high']['pre_mean']:.2f}", f"{cats['control_commercial_high']['post_mean']:.2f}",
         f"{cats['control_commercial_high']['rate_ratio']:.2f}× ({cats['control_commercial_high']['ci_95_percentile'][0]:.2f}–{cats['control_commercial_high']['ci_95_percentile'][1]:.2f})", f"{cats['control_commercial_high']['p_value']:.2f}"]
    ]

    t1 = doc.add_table(rows=len(t1_data), cols=5, style="Table Grid")
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(t1_data):
        for j, val in enumerate(row):
            cell = t1.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j > 0 else WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(val)
            run.font.name = "Times New Roman"
            run.font.size = Pt(8.5)
            if i == 0:
                run.bold = True
                _set_cell_shading(cell, "E0E0E0")
            elif "Control" in row[0]:
                _set_cell_shading(cell, "F5F5F5")

    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.space_after = Pt(12)
    _add_run(p, "Note: Denominators are 317 pre-intervention and 256 post-intervention days with data. Bootstrap CIs computed from 4,000 resamples. "
                "p-values calculated using two-sided Mann–Whitney U test on daily counts.", italic=True, size=8.5)

    # Embed Figure 3 (Time Series)
    fig3_path = FIGS_DIR / "fig3_monthly_timeseries.png"
    if fig3_path.exists():
        doc.add_picture(str(fig3_path), width=Inches(6.0))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(12)
        _add_run(p, "Figure 3. ", bold=True, size=10)
        _add_run(p, "Daily overflight pass counts (grey dots) and monthly mean ± SEM (black markers with ribbon) over Capitol Hill "
                    "(1 January 2025 – 31 August 2026). The vertical dashed line marks the VAMP implementation date (27 November 2025).", size=10)

    _heading(doc, "4.3 Structural Reversal in Direction of Travel", level=2)

    _body(doc, (
        "Analysis of CPA heading bands reveals the most definitive physical evidence in the dataset: arriving commercial traffic "
        "underwent a complete directional substitution rather than an additive increase (Table 2, Figure 4). Prior to VAMP, "
        "commercial arrivals were overwhelmingly northbound (1,518 flights; 77.6%), while eastbound and westbound flights combined "
        "totaled only 94 flights (4.8%). Following VAMP, northbound arrivals dropped sharply to 590 flights, whereas east–west "
        "arrivals expanded to 10,321 flights (3,778 eastbound; 6,543 westbound; 93.0% of all post-VAMP arrivals). In contrast, "
        "light fixed-wing control aircraft maintained an unchanged eastbound orientation along the Burrard Inlet route in both eras "
        "(1,822 pre vs. 1,261 post), ruling out receiver orientation or detection sensitivity artifacts."
    ))

    # ── Table 2: Direction of Travel ──────────────────────────────────────
    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    _add_run(p, "Table 2. ", bold=True, size=10)
    _add_run(p, "Overflight counts by operational category, era, and heading band.", size=10)

    dir_tbl = res["section2_6_direction"]["table"]
    t2_data = [
        ["Category", "Era", "Total", "East (060–120°)", "West (240–300°)", "North (330–030°)", "South (150–210°)", "Other"],
        ["Commercial arrivals", "Before", str(dir_tbl["Commercial arrivals"]["Before"]["total"]),
         str(dir_tbl["Commercial arrivals"]["Before"]["counts"]["E"]), str(dir_tbl["Commercial arrivals"]["Before"]["counts"]["W"]),
         str(dir_tbl["Commercial arrivals"]["Before"]["counts"]["N"]), str(dir_tbl["Commercial arrivals"]["Before"]["counts"]["S"]),
         str(dir_tbl["Commercial arrivals"]["Before"]["counts"]["Other"])],
        ["Commercial arrivals", "After", str(dir_tbl["Commercial arrivals"]["After"]["total"]),
         str(dir_tbl["Commercial arrivals"]["After"]["counts"]["E"]), str(dir_tbl["Commercial arrivals"]["After"]["counts"]["W"]),
         str(dir_tbl["Commercial arrivals"]["After"]["counts"]["N"]), str(dir_tbl["Commercial arrivals"]["After"]["counts"]["S"]),
         str(dir_tbl["Commercial arrivals"]["After"]["counts"]["Other"])],
        ["Business / private", "Before", str(dir_tbl["Business / private"]["Before"]["total"]),
         str(dir_tbl["Business / private"]["Before"]["counts"]["E"]), str(dir_tbl["Business / private"]["Before"]["counts"]["W"]),
         str(dir_tbl["Business / private"]["Before"]["counts"]["N"]), str(dir_tbl["Business / private"]["Before"]["counts"]["S"]),
         str(dir_tbl["Business / private"]["Before"]["counts"]["Other"])],
        ["Business / private", "After", str(dir_tbl["Business / private"]["After"]["total"]),
         str(dir_tbl["Business / private"]["After"]["counts"]["E"]), str(dir_tbl["Business / private"]["After"]["counts"]["W"]),
         str(dir_tbl["Business / private"]["After"]["counts"]["N"]), str(dir_tbl["Business / private"]["After"]["counts"]["S"]),
         str(dir_tbl["Business / private"]["After"]["counts"]["Other"])],
        ["Control: Light/float/heli", "Before", str(dir_tbl["Control: light/float/heli"]["Before"]["total"]),
         str(dir_tbl["Control: light/float/heli"]["Before"]["counts"]["E"]), str(dir_tbl["Control: light/float/heli"]["Before"]["counts"]["W"]),
         str(dir_tbl["Control: light/float/heli"]["Before"]["counts"]["N"]), str(dir_tbl["Control: light/float/heli"]["Before"]["counts"]["S"]),
         str(dir_tbl["Control: light/float/heli"]["Before"]["counts"]["Other"])],
        ["Control: Light/float/heli", "After", str(dir_tbl["Control: light/float/heli"]["After"]["total"]),
         str(dir_tbl["Control: light/float/heli"]["After"]["counts"]["E"]), str(dir_tbl["Control: light/float/heli"]["After"]["counts"]["W"]),
         str(dir_tbl["Control: light/float/heli"]["After"]["counts"]["N"]), str(dir_tbl["Control: light/float/heli"]["After"]["counts"]["S"]),
         str(dir_tbl["Control: light/float/heli"]["After"]["counts"]["Other"])],
        ["Control: Commercial ≥10k ft", "Before", str(dir_tbl["Control: commercial >=10,000 ft"]["Before"]["total"]),
         str(dir_tbl["Control: commercial >=10,000 ft"]["Before"]["counts"]["E"]), str(dir_tbl["Control: commercial >=10,000 ft"]["Before"]["counts"]["W"]),
         str(dir_tbl["Control: commercial >=10,000 ft"]["Before"]["counts"]["N"]), str(dir_tbl["Control: commercial >=10,000 ft"]["Before"]["counts"]["S"]),
         str(dir_tbl["Control: commercial >=10,000 ft"]["Before"]["counts"]["Other"])],
        ["Control: Commercial ≥10k ft", "After", str(dir_tbl["Control: commercial >=10,000 ft"]["After"]["total"]),
         str(dir_tbl["Control: commercial >=10,000 ft"]["After"]["counts"]["E"]), str(dir_tbl["Control: commercial >=10,000 ft"]["After"]["counts"]["W"]),
         str(dir_tbl["Control: commercial >=10,000 ft"]["After"]["counts"]["N"]), str(dir_tbl["Control: commercial >=10,000 ft"]["After"]["counts"]["S"]),
         str(dir_tbl["Control: commercial >=10,000 ft"]["After"]["counts"]["Other"])]
    ]

    t2 = doc.add_table(rows=len(t2_data), cols=8, style="Table Grid")
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(t2_data):
        for j, val in enumerate(row):
            cell = t2.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j > 1 else WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(val)
            run.font.name = "Times New Roman"
            run.font.size = Pt(8)
            if i == 0:
                run.bold = True
                _set_cell_shading(cell, "E0E0E0")
            elif "After" in row[1]:
                _set_cell_shading(cell, "FAFAFA")

    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.space_after = Pt(12)
    _add_run(p, "Note: Evaluated across 20,093 record-level flights. Heading tracks are extracted at CPA.", italic=True, size=8.5)

    # Embed Figure 6 (Direction shifts)
    fig6_path = FIGS_DIR / "fig6_direction_shifts.png"
    if fig6_path.exists():
        doc.add_picture(str(fig6_path), width=Inches(5.5))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(12)
        _add_run(p, "Figure 4. ", bold=True, size=10)
        _add_run(p, "Commercial arrival heading distributions before and after VAMP, illustrating the structural shift from North–South to East–West tracks.", size=10)

    _heading(doc, "4.4 Corridor Geometry and Boundary Truncation", level=2)

    _body(doc, (
        "Disaggregating post-VAMP arrival traffic by heading reveals two distinct operational corridors (Figure 5):\n"
        "1. Eastbound Corridor (060–150°; n = 3,918): Centered almost directly overhead Capitol Hill with a median CPA latitude "
        "of 49.2860°N (0.10 km south of the summit), median CPA distance of 0.178 km, tight lateral dispersion (IQR = 155 m), "
        "median altitude of 5,150 ft ASL, and median ground speed of 227 kt.\n"
        "2. Westbound Corridor (240–330°; n = 6,554): Centered south of the hill with a median CPA latitude of 49.2740°N "
        "(1.44 km south of the summit), median altitude of 8,300 ft ASL, and median ground speed of 248 kt.\n\n"
        "Critically, the westbound corridor is truncated by the study's 1.50-km monitoring radius: the median CPA distance for "
        "westbound aircraft is 1.471 km. A radius-sensitivity scan demonstrates that 56.0% of all post-VAMP arrival records "
        "(6,222 out of 11,103) enter only within the outermost 100 meters (1.4 to 1.5 km) of the study perimeter. Because westbound "
        "flights merely skirt the southern boundary, total westbound volume cannot be fully quantified at this radius. The manuscript "
        "therefore leads with the inner 500-m core metric, which is entirely self-contained within the residential summit zone."
    ))

    # Embed Figure 5 (Corridor truncation)
    fig5_path = FIGS_DIR / "fig5_corridor_truncation.png"
    if fig5_path.exists():
        doc.add_picture(str(fig5_path), width=Inches(6.0))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(12)
        _add_run(p, "Figure 5. ", bold=True, size=10)
        _add_run(p, "Corridor localization and boundary truncation. (a) Cumulative arrival records vs. monitoring radius, showing "
                    "that 56.0% enter in the final 100 m. (b) Distance south of summit for the Eastbound (overhead) and Westbound (boundary-truncated) corridors.", size=10)

    _heading(doc, "4.5 Altitude and 3D Proximity Shifts", level=2)

    _body(doc, (
        "Within the inner 500-m summit core zone, commercial arrivals experienced a profound reduction in both altitude and 3D slant distance "
        "(Figure 6). In the pre-VAMP period, arriving aircraft within 500 m passed at a median barometric altitude of 7,700 ft ASL "
        "(IQR 6,800–8,475 ft) and a median 3D slant distance of 2.26 km (IQR 1.98–2.48 km). Following VAMP, median altitude dropped by "
        "2,375 ft to 5,325 ft ASL (IQR 4,700–5,850 ft), while median 3D slant distance contracted by 0.74 km to 1.52 km (IQR 1.33–1.68 km). "
        "This compression in both lateral and vertical separation brought heavy commercial air traffic substantially closer to the residential summit."
    ))

    # Embed Figure 4 (Altitude comparison)
    fig4_path = FIGS_DIR / "fig4_altitude_comparison.png"
    if fig4_path.exists():
        doc.add_picture(str(fig4_path), width=Inches(6.0))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(12)
        _add_run(p, "Figure 6. ", bold=True, size=10)
        _add_run(p, "Barometric altitude distributions at CPA for commercial arrivals within 500 m of the summit. (a) Pre-VAMP (median 7,700 ft ASL); "
                    "(b) Post-VAMP (median 5,325 ft ASL), demonstrating a downward shift of ~2,400 ft.", size=10)

    _heading(doc, "4.6 Diurnal Distribution and Fleet Composition", level=2)

    _body(doc, (
        "Diurnal analysis indicates that overflights remain predominantly diurnal, with 94.86% of passes occurring between 06:00 and 22:59 "
        "local Pacific Time. Nocturnal traffic (23:00 to 05:59) accounted for exactly 5.14% of the total census (1,032 of 20,093 records). "
        "Post-VAMP overflights are relatively evenly distributed across daylight hours (07:00–22:00) rather than concentrated into narrow peaks.\n\n"
        "Fleet census across all 20,093 records confirmed the De Havilland Dash 8 Q400 (DH8D) as the single most prevalent commercial airframe "
        "(3,432 flights; 17.08%), followed by the Cessna 172 (C172) flight trainer (1,882 flights; 9.37%). Boeing 737 variants contributed "
        "significantly, led by the 737 MAX 8 (B38M; 1,240 flights; 6.17%) and 737-800 (B738; 951 flights; 4.73%). The entire Boeing 7xx family "
        "(B732 through B78X) accounted for 3,985 flights (19.83%)."
    ))

    _heading(doc, "4.7 External Validation against Statistics Canada", level=2)

    _body(doc, (
        "To rigorously test whether the observed overflight increase was an artifact of regional aviation growth or expanding ADS-B receiver "
        "density, observations were benchmarked against official monthly aircraft movements from Statistics Canada Tables 23-10-0296 and "
        "23-10-0303 for matched Jan–Jun windows in 2025 and 2026 (Figure 7):\n"
        "1. YVR Total Airport Movements were essentially unchanged (142,014 movements in 2025 vs. 141,258 in 2026; ratio 0.995; −0.5%). "
        "This official datum decisively refutes the hypothesis that regional traffic expansion drove the 5.98-fold increase in Capitol Hill arrivals.\n"
        "2. Regional GA Airports (Boundary Bay, Pitt Meadows, Langley) exhibited a combined 13.4% decline (ratio 0.866). In direct alignment, "
        "ADS-B light fixed-wing GA over Capitol Hill declined by 17.2% (ratio 0.828). This close concordance between two entirely independent "
        "measurement systems demonstrates that crowdsourced ADS-B surveillance accurately tracks real operational trends without artificial receiver-growth bias."
    ))

    # Embed Figure 7 (StatCan validation)
    fig7_path = FIGS_DIR / "fig7_statcan_validation.png"
    if fig7_path.exists():
        doc.add_picture(str(fig7_path), width=Inches(5.0))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(12)
        _add_run(p, "Figure 7. ", bold=True, size=10)
        _add_run(p, "External validation against official Statistics Canada movement counts (matched Jan–Jun 2025 vs. 2026). "
                    "YVR airport movements were flat (−0.5%), while Capitol Hill arrivals increased sixfold. General aviation airport "
                    "declines (−13.4%) closely mirrored the ADS-B light GA decline (−17.2%).", size=10)

    _heading(doc, "4.8 Seasonality Robustness Analysis", level=2)

    _body(doc, (
        "Season-matched sensitivity analysis across the identical 8-month calendar window (1 January – 31 August 2025 vs. 1 January – 31 August 2026) "
        "demonstrated that seasonal variations did not confound findings. On a record basis, 1.5-km commercial arrivals rose from 6.21 to 42.43 "
        "flights/day (RR = 6.83×), 500-m commercial arrivals rose from 2.18 to 13.78 flights/day (RR = 6.31×), while light fixed-wing GA remained "
        "stable (RR = 0.92×). Pass-based rates showed equivalent stability (1.5-km arrivals RR = 7.64×; 500-m arrivals RR = 7.00×; light GA RR = 0.92×)."
    ))

    _heading(doc, "4.9 Recomputed 20-Month Summary Census", level=2)

    _body(doc, (
        "Table 3 provides the definitive, recomputed monthly overflight census directly from the 20,093 record-level dataset, reconciling all "
        "previously discredited summary discrepancies."
    ))

    # ── Table 3: Monthly Summary ──────────────────────────────────────────
    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    _add_run(p, "Table 3. ", bold=True, size=10)
    _add_run(p, "Recomputed monthly overflight census from record-level data (January 2025 – August 2026).", size=10)

    t3_raw = res["table2_monthly_summary"]
    t3_data = [["Month", "Total Flights", "Days with Data", "Min Daily", "Max Daily", "Median Daily", "Mean Daily", "SEM", "Unique Aircraft"]]
    for r in t3_raw:
        t3_data.append([
            r["month"], f"{r['total_flights']:,}", str(r["days_with_data"]), str(r["min_daily"]), str(r["max_daily"]),
            f"{r['median_daily']:.1f}", f"{r['mean_daily']:.1f}", f"{r['sem_daily']:.2f}", f"{r['unique_aircraft']:,}"
        ])
    # Add Total row
    t3_data.append([
        "Total / Overall", f"{sum(r['total_flights'] for r in t3_raw):,}", str(sum(r['days_with_data'] for r in t3_raw)),
        str(min(r['min_daily'] for r in t3_raw)), str(max(r['max_daily'] for r in t3_raw)),
        "-", "-", "-", f"{res['section2_1_coverage_passes']['unique_icaos']:,}"
    ])

    t3 = doc.add_table(rows=len(t3_data), cols=9, style="Table Grid")
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(t3_data):
        for j, val in enumerate(row):
            cell = t3.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(val)
            run.font.name = "Times New Roman"
            run.font.size = Pt(7.5)
            if i == 0:
                run.bold = True
                _set_cell_shading(cell, "E0E0E0")
            elif i >= 12 and i < len(t3_data) - 1:
                _set_cell_shading(cell, "F5F5F5")
            elif i == len(t3_data) - 1:
                run.bold = True
                _set_cell_shading(cell, "EAEAEA")

    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.space_after = Pt(12)
    _add_run(p, "Note: Shaded rows represent the post-VAMP era (December 2025 onward). Exactly sums to 20,093 records across 573 observation days.", italic=True, size=8)

    # ── 5. DISCUSSION ─────────────────────────────────────────────────────
    _heading(doc, "5. Discussion", level=1)
    _heading(doc, "5.1 Comparison with Modeled Predictions and Airspace Policy", level=2)

    _body(doc, (
        "The empirical findings demonstrate an abrupt, highly concentrated operational restructuring of terminal arrivals into YVR. "
        "The 6.73-fold increase in commercial passes within 500 m of Capitol Hill, combined with a 2,400-ft reduction in median approach "
        "altitude and a 0.74-km reduction in 3D slant distance, represents a marked transformation in the localized acoustic environment. "
        "These results mirror findings in the United States, where FAA NextGen RNAV/RNP procedures achieved regional efficiency gains at "
        "the cost of creating severe, localized overflight corridors that bypassed conventional environmental assessments (GAO, 2021; "
        "Brenner & Hansman, 2017). NAV CANADA's pre-implementation consultations projected dispersed noise footprints based on time-averaged "
        "energy metrics (NAV CANADA, 2022); our empirical census highlights the necessity of tracking discrete event counts and altitude profiles."
    ))

    _heading(doc, "5.2 Methodological Comparison with Prior ADS-B Research", level=2)

    _body(doc, (
        "This investigation extends prior crowdsourced surveillance methodologies. Foundational studies by Schäfer et al. (2014) and "
        "Strohmeier et al. (2021) established the OpenSky Network to monitor macro-scale, continental air traffic flows. The present study "
        "demonstrates that open ADS-B archives can be successfully applied to hyper-local, neighborhood-scale (500 m to 1.5 km) public health "
        "and environmental audits. Furthermore, while the traffic Python library (Olive, 2019) and OpenAP simulation toolkit (Sun et al., 2019) "
        "rely on spline smoothing and trajectory interpolation, our methodology computes the CPA strictly from raw physical-layer radio "
        "pings. This deliberate design eliminates interpolation artifacts and guarantees full deterministic reproducibility."
    ))

    _heading(doc, "5.3 Limitations and Confounding Factors", level=2)

    _body(doc, (
        "Several methodological constraints should be noted:\n"
        "1. Boundary Truncation of the Westbound Corridor: As established in §4.4, the westbound corridor passing south of Capitol Hill "
        "is truncated by the 1.5-km monitoring boundary. While the eastbound corridor overhead is fully captured, westbound volume "
        "cannot be fully measured without expanding the spatial perimeter in future work.\n"
        "2. Absence of Direct Acoustic Monitoring: This study measures spatial trajectory kinematics (altitude, velocity, proximity) but "
        "did not deploy physical sound level meters. Future research should pair ADS-B telemetry with Class 1 sound monitors measuring "
        "N-Above decibel thresholds.\n"
        "3. Localized Topographic Shadowing: Although receiver coverage in Metro Vancouver is robust (Schäfer et al., 2020), localized "
        "terrain shadowing from Capitol Hill or Burnaby Mountain could introduce minor receiver blind spots for low-flying aircraft. "
        "However, any such shadowing would produce an undercount, rendering our rate ratios conservative.\n"
        "4. Late-Spring 2026 Helicopter Increase: A statistically significant increase in helicopter overflights occurred in late spring 2026 "
        "(1.59 to 4.38 passes/day; RR = 2.75, p = 2.65e-06), with algorithmic changepoints detected on 28 April / 3 May 2026. This surge was "
        "driven almost entirely by heavy transport/air-ambulance twin-engine types (Sikorsky S-76 and AgustaWestland AW139; rising from 5 to 307 "
        "passes in matched Jan–Jun windows), while light training helicopters (Robinson R44) slightly declined (RR = 0.83). Statistics Canada "
        "records indicate Vancouver Harbour movements rose by only 21.3% over the same timeframe. This 60-fold increase cannot be explained "
        "by harbor activity and reflects fleet-level ADS-B Out equipage or localized route realignments occurring five months after VAMP. "
        "It is therefore decoupled from VAMP arrival procedures and reported as an independent operational limitation."
    ))

    # ── 6. CONCLUSIONS ────────────────────────────────────────────────────
    _heading(doc, "6. Conclusions", level=1)

    _body(doc, (
        "This 20-month continuous census provides the first independent empirical quantification of NAV CANADA's Vancouver Airspace Modernization "
        "Project. Implementation of AIRAC cycle 2513 on 27 November 2025 resulted in an immediate, sustained 6.73-fold increase in commercial arrival "
        "passes within 500 m of Capitol Hill, a downward altitude shift of ~2,400 ft, and a structural replacement of North–South flight paths with "
        "East–West corridors. Negative controls (light general aviation, en-route commercial traffic) and official Statistics Canada data confirmed "
        "that these observations reflect real route concentration rather than regional traffic growth or surveillance artifacts. Open crowdsourced "
        "ADS-B archives provide a transparent, reproducible framework for independent community environmental oversight."
    ))

    # ── DECLARATIONS ──────────────────────────────────────────────────────
    _heading(doc, "Conflict of Interest Statement", level=1)
    _body(doc, (
        "The author (D. Yap) is a resident of Capitol Hill, Burnaby, British Columbia, within the 1.5 km study zone. This study was conceived "
        "following the subjective observation of increased aircraft noise beginning in late November 2025. The author has no financial interests "
        "in aviation, air navigation service providers, airlines, or noise monitoring companies. The study was entirely self-funded with no external "
        "sponsorship. All data, analytical code, and the complete record-level dataset are openly published to enable independent verification and "
        "replication (https://github.com/oncoapop/capitol_hill_flights)."
    ))

    _heading(doc, "Data Availability Statement", level=1)
    _body(doc, (
        "The authoritative 20,093 record-level dataset (capitol_hill_all_flights.csv), discrete pass extraction (capitol_hill_passes.csv), "
        "Statistics Canada tables, and Python analysis scripts are publicly available under open licenses (MIT for software, CC BY 4.0 for data "
        "and text) at: https://github.com/oncoapop/capitol_hill_flights. Statistics Canada tables are utilized under the Open Government Licence – Canada. "
        "Source ADS-B telemetry archives are maintained by the adsb.lol community (https://globe.adsb.lol)."
    ))

    _heading(doc, "Use of Generative AI Statement", level=1)
    _body(doc, (
        "In accordance with the Journal of Open Aviation Science (JOAS) policy on generative artificial intelligence, the author declares that "
        "large language model agentic coding tools (Antigravity AI Assistant) were utilized to write automated data extraction routines, execute "
        "algorithmic changepoint and bootstrap scripts, format markdown tables, and assist in manuscript text structuring. All computational "
        "outputs, statistical assertions, and manuscript drafts were audited, verified against authoritative data files, and approved by the author."
    ))

    _heading(doc, "Acknowledgments", level=1)
    _body(doc, (
        "The author expresses gratitude to the adsb.lol open-source community for curating and preserving historical ADS-B telemetry archives, "
        "and to the volunteer SDR receiver operators across the Lower Mainland whose ground stations underpin public air traffic surveillance."
    ))

    # ── REFERENCES ────────────────────────────────────────────────────────
    _heading(doc, "References", level=1)

    references = [
        ("adsb.lol Community. (2025–2026). Globe history historical telemetry database. GitHub repositories: adsblol/globe_history_2025 and adsblol/globe_history_2026.", "https://globe.adsb.lol"),
        ("Aminikhanghahi, S., & Cook, D. J. (2017). A survey of methods for time series change point detection. Knowledge and Information Systems, 51(2), 339–367.", "https://doi.org/10.1007/s10115-016-0987-z"),
        ("Bai, J., & Perron, P. (2003). Computation and analysis of multiple structural change models. Journal of Applied Econometrics, 18(1), 1–22.", "https://doi.org/10.1002/jae.659"),
        ("Basner, M., Babisch, W., Davis, A., Brink, M., Clark, C., Janssen, S., & Stansfeld, S. (2014). Auditory and non-auditory effects of noise on health. The Lancet, 383(9925), 1325–1332.", "https://doi.org/10.1016/S0140-6736(13)61613-X"),
        ("Bernal, J. L., Cummins, S., & Gasparrini, A. (2017). Interrupted time series regression for the evaluation of public health interventions: A tutorial. International Journal of Epidemiology, 46(1), 348–355.", "https://doi.org/10.1093/ije/dyw098"),
        ("Brenner, M., & Hansman, R. J. (2017). Comparison of methods for evaluating impacts of aviation noise on communities. MIT International Center for Air Transportation Report ICAT-2017-03.", "https://dspace.mit.edu/handle/1721.1/110268"),
        ("Government Accountability Office (GAO). (2021). Aircraft noise: FAA could improve outreach and its use of supplemental noise metrics (GAO-21-103933).", "https://www.gao.gov/products/gao-21-103933"),
        ("Hansell, A. L., Blangiardo, M., Fortunato, L., Floud, S., de Hoogh, K., Fecht, D., Ghosh, R. E., Laszlo, H. E., Pearson, C., Beale, L., Beevers, S., Gulliver, J., Best, N., Richardson, S., & Elliott, P. (2013). Aircraft noise and cardiovascular disease near Heathrow airport in London: Small area study. BMJ, 347, f5432.", "https://doi.org/10.1136/bmj.f5432"),
        ("International Civil Aviation Organization (ICAO). (2020). Annex 10 to the Convention on International Civil Aviation: Aeronautical telecommunications, Vol. IV – Surveillance and collision avoidance systems (5th ed.). Montreal, Canada.", "https://store.icao.int/en/annex-10-aeronautical-telecommunications-volume-iv-surveillance-and-collision-avoidance-systems"),
        ("NAV CANADA. (2022). Vancouver Airspace Modernization Project (VAMP): Initial proposal and environmental assessment. Ottawa, Canada.", "https://www.navcanada.ca/en/air-traffic/airspace-reviews/vancouver-airspace-modernization-project.aspx"),
        ("Olive, X. (2019). traffic, a toolbox for processing and analysing air traffic data. Journal of Open Source Software, 4(39), 1518.", "https://doi.org/10.21105/joss.01518"),
        ("Peters, J. L., Zevitas, C. D., Redline, S., Hastings, A., Sizov, N., Hart, J. E., Levy, J. I., Roof, C. J., & Wellenius, G. A. (2018). Aviation noise and cardiovascular health in the United States: A review of the evidence and recommendations for research direction. Current Environmental Health Reports, 5(1), 140–152.", "https://doi.org/10.1007/s40572-018-0191-1"),
        ("RTCA Inc. (2011). DO-260B: Minimum Operational Performance Standards for 1090 MHz Extended Squitter Automatic Dependent Surveillance–Broadcast (ADS-B) and Traffic Information Services–Broadcast (TIS-B). Washington, D.C.", None),
        ("Schäfer, M., Strohmeier, M., Lenders, V., Martinovic, I., & Wilhelm, M. (2014). Bringing up OpenSky: A large-scale ADS-B sensor network for research. Proceedings of the 13th ACM/IEEE International Conference on Information Processing in Sensor Networks (IPSN), 83–94.", "https://doi.org/10.1109/IPSN.2014.6846743"),
        ("Schäfer, M., Strohmeier, M., Smith, M., & Martinovic, I. (2020). Assessing the coverage and accuracy of the OpenSky Network. Proceedings of the 8th OpenSky Symposium 2020, 1–9.", "https://doi.org/10.3929/ethz-b-000469865"),
        ("Sinnott, R. W. (1984). Virtues of the Haversine. Sky and Telescope, 68(2), 159.", None),
        ("Statistics Canada. (2026a). Table 23-10-0296-01: Aircraft movements, by class of operation and type of operation, airports with NAV CANADA towers and flight service stations, monthly.", "https://doi.org/10.25318/2310029601-eng"),
        ("Statistics Canada. (2026b). Table 23-10-0303-01: Aircraft movements, by class of operation and type of operation, airports with NAV CANADA flight service stations, monthly.", "https://doi.org/10.25318/2310030301-eng"),
        ("Statistics Canada. (2026c). Table 23-10-0298-01: Itinerant movements, by type of operation, airports with NAV CANADA towers and flight service stations, monthly.", "https://doi.org/10.25318/2310029801-eng"),
        ("Strohmeier, M., Schäfer, M., Pinheiro, R., Lenders, V., & Martinovic, I. (2015). On the security of the automatic dependent surveillance-broadcast protocol. IEEE Communications Surveys & Tutorials, 17(2), 1066–1087.", "https://doi.org/10.1109/COMST.2014.2365951"),
        ("Strohmeier, M., Olive, X., Lübbe, J., Schäfer, M., & Lenders, V. (2021). Crowdsourced air traffic data from the OpenSky Network 2019–2020. Earth System Science Data, 13(2), 357–366.", "https://doi.org/10.5194/essd-13-357-2021"),
        ("Sun, J., Vu, H., Ellerbroek, J., & Hoekstra, J. M. (2019). OpenAP: An open-source aircraft performance model for air traffic simulation and analysis. Aerospace, 6(8), 84.", "https://doi.org/10.3390/aerospace6080084"),
        ("Transport Canada. (2023). Advisory Circular (AC) No. 500-029: ADS-B Out Equipment Requirements in Canadian Airspace. Ottawa, Canada.", "https://tc.canada.ca/en/aviation/reference-centre/advisory-circulars"),
        ("Truong, C., Oudre, L., & Vayatis, N. (2020). Selective review of offline change point detection methods. Signal Processing, 167, 107299.", "https://doi.org/10.1016/j.sigpro.2019.107299")
    ]

    for ref_text, ref_url in references:
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.left_indent = Cm(1.27)
        p.paragraph_format.first_line_indent = Cm(-1.27)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = WD_LINE_SPACING.SINGLE
        _add_run(p, ref_text, size=10)
        if ref_url:
            _add_run(p, " ", size=10)
            _add_hyperlink(p, ref_url, ref_url, font_size=10)

    doc.save(str(OUTPUT_DOCX))
    print(f"\n✓ Revised manuscript successfully saved to: {OUTPUT_DOCX}")
    return OUTPUT_DOCX

if __name__ == "__main__":
    build_manuscript()
