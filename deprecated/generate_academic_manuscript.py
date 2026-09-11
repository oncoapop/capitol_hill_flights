"""
Generate the academic manuscript as an editable DOCX file.

Produces a ~12–15 page IMRAD-format manuscript with:
  - Title page, structured abstract, keywords
  - Introduction with literature background
  - Materials and Methods (with methodology comparisons)
  - Results (with embedded journal figures and tables)
  - Discussion (comparative, limitations, implications)
  - COI, Data Availability, Acknowledgments
  - 24+ APA-style references

Requires: python-docx, Pillow (or PIL)
"""
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn

from config import WORKSPACE_DIR

OUTPUT_DOCX = WORKSPACE_DIR / "Capitol_Hill_Overflight_Academic_Manuscript.docx"
FIGS_DIR = WORKSPACE_DIR / "academic_figures"


# ═══════════════════════════════════════════════════════════════════════════
# Helper utilities
# ═══════════════════════════════════════════════════════════════════════════

def _add_hyperlink(paragraph, url: str, text: str, font_size=10, color=(0, 0, 238)):
    """Insert a clickable hyperlink run into *paragraph* using low-level OPC XML.

    Word/Google-Docs will render this as a blue, underlined, clickable link.
    """
    from docx.oxml import OxmlElement
    part = paragraph.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")

    # Font name
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rPr.append(rFonts)

    # Font size (half-points)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(font_size * 2))
    rPr.append(sz)

    # Color
    c_el = OxmlElement("w:color")
    c_el.set(qn("w:val"), "{:02X}{:02X}{:02X}".format(*color))
    rPr.append(c_el)

    # Underline
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)

    # Word built-in Hyperlink character style
    rStyle = OxmlElement("w:rStyle")
    rStyle.set(qn("w:val"), "Hyperlink")
    rPr.append(rStyle)

    new_run.append(rPr)
    new_run.text = text  # won't work — need w:t
    # Actually need a w:t element
    new_run.remove(new_run.find(qn("w:rPr")))  # re-add properly
    new_run.append(rPr)
    t_el = OxmlElement("w:t")
    t_el.text = text
    t_el.set(qn("xml:space"), "preserve")
    new_run.append(t_el)

    hyperlink.append(new_run)
    paragraph._element.append(hyperlink)
    return hyperlink


def _set_cell_shading(cell, color_hex: str):
    """Apply background shading to a table cell."""
    shading_elm = cell._element.get_or_add_tcPr()
    shading = shading_elm.makeelement(qn("w:shd"), {
        qn("w:fill"): color_hex,
        qn("w:val"): "clear",
    })
    shading_elm.append(shading)


def _add_run(paragraph, text, bold=False, italic=False, size=12, font_name="Times New Roman", color=None, superscript=False):
    run = paragraph.add_run(text)
    run.font.name = font_name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)
    if superscript:
        run.font.superscript = True
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


def _body(doc, text, refs_inline=None):
    """Add a body paragraph with optional inline reference markers."""
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


# ═══════════════════════════════════════════════════════════════════════════
# Document construction
# ═══════════════════════════════════════════════════════════════════════════

def build_manuscript(output_path: Path = OUTPUT_DOCX) -> Path:
    doc = Document()

    # ── Page Setup ────────────────────────────────────────────────────
    for section in doc.sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)

    # ── Default paragraph style ──────────────────────────────────────
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    style.paragraph_format.line_spacing = WD_LINE_SPACING.DOUBLE
    style.paragraph_format.space_after = Pt(0)

    # ── Heading styles ───────────────────────────────────────────────
    for level in range(1, 4):
        hs = doc.styles[f"Heading {level}"]
        hs.font.name = "Times New Roman"
        hs.font.color.rgb = RGBColor(0, 0, 0)
        hs.font.bold = True
        hs.font.size = Pt({1: 14, 2: 12, 3: 12}[level])
        hs.font.italic = (level == 3)

    # ==================================================================
    # TITLE PAGE
    # ==================================================================
    p = _make_paragraph(doc, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)
    _add_run(p, "Quantifying the Impact of Airspace Modernization on Residential Overflights:\n", bold=True, size=16)
    _add_run(p, "A 20-Month Crowdsourced ADS-B Census of Capitol Hill, Burnaby, British Columbia", bold=True, size=14)

    p = _make_paragraph(doc, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
    _add_run(p, "Damian Yap, PhD", size=12)

    p = _make_paragraph(doc, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
    _add_run(p, "Independent Researcher, Burnaby, British Columbia, Canada", italic=True, size=11)

    p = _make_paragraph(doc, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)
    _add_run(p, "Correspondence: D. Yap (damian@oncoapop.com)", size=10)

    p = _make_paragraph(doc, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
    _add_run(p, "Date: September 2026", size=11)

    p = _make_paragraph(doc, alignment=WD_ALIGN_PARAGRAPH.LEFT, space_before=18, space_after=6)
    _add_run(p, "Keywords: ", bold=True, size=11)
    _add_run(p, "ADS-B; crowdsourced surveillance; aircraft overflight; airspace modernization; "
                "Performance-Based Navigation; VAMP; interrupted time series; community noise exposure; "
                "Vancouver International Airport", size=11)

    doc.add_page_break()

    # ==================================================================
    # ABSTRACT
    # ==================================================================
    _heading(doc, "Abstract", level=1)

    abstract_text = (
        "Background: The Vancouver Airspace Modernization Project (VAMP), implemented by NAV CANADA "
        "on 27 November 2025 (AIRAC cycle 2513), introduced Performance-Based Navigation (PBN) arrival "
        "procedures for Vancouver International Airport (YVR). The impact of these redesigned flight paths "
        "on residential communities beneath the new corridors has not been independently quantified. "
        "\n\n"
        "Methods: We conducted a continuous 20-month census of aircraft overflights within a 1.5-km geodesic "
        "radius of Capitol Hill, Burnaby, BC (49.2869°N, 122.9853°W) from 1 January 2025 to 31 August 2026 "
        "(573 days with usable data). Aircraft positions were extracted from crowdsourced, uncensored ADS-B "
        "archives (adsb.lol globe_history) using a two-stage spatial filter: a rectangular bounding-box "
        "pre-filter followed by Haversine great-circle verification. Daily overflight counts were compared "
        "across the pre- and post-VAMP periods using rate ratios with 4,000-replicate bootstrap confidence "
        "intervals. Traffic categories unaffected by VAMP (light aircraft, floatplanes, helicopters; "
        "commercial traffic ≥10,000 ft) served as negative controls. "
        "\n\n"
        "Results: A total of 20,093 aircraft-days involving 2,050 unique airframes were recorded. Following "
        "VAMP implementation, arriving commercial aircraft within 500 m of Capitol Hill increased from 2.21 "
        "to 13.34 per day (rate ratio 6.04×; 95% CI 5.24–7.03). Median closest-approach altitude decreased "
        "from 7,675 ft to 5,338 ft (Δ = 2,337 ft). Negative control categories showed no significant change "
        "(rate ratios 0.97× and 0.90×, p > 0.05), confirming the increase reflects genuine route alteration "
        "rather than receiver-network growth. "
        "\n\n"
        "Conclusions: VAMP implementation produced an abrupt, sustained, and statistically significant "
        "increase in low-altitude commercial overflights above Capitol Hill. These findings demonstrate "
        "that crowdsourced ADS-B archives offer a viable, transparent, and reproducible methodology for "
        "independent community monitoring of airspace changes."
    )
    _body(doc, abstract_text)

    doc.add_page_break()

    # ==================================================================
    # 1. INTRODUCTION
    # ==================================================================
    _heading(doc, "1. Introduction", level=1)

    _body(doc, (
        "Aircraft noise is a well-established environmental health hazard. Epidemiological studies have "
        "documented associations between chronic aircraft noise exposure and cardiovascular disease, "
        "hypertension, sleep disturbance, and cognitive impairment in children, with health risks evident "
        "even at moderate exposure levels below traditional regulatory thresholds (Basner et al., 2014; "
        "Hansell et al., 2013; Peters et al., 2018). As global air traffic volumes grow, the health burden "
        "on communities beneath approach and departure corridors has become a matter of increasing public "
        "health concern."
    ))

    _body(doc, (
        "In response to congestion and environmental pressures, air navigation service providers (ANSPs) "
        "worldwide have undertaken airspace modernization programmes designed to improve efficiency and "
        "reduce fuel consumption. The United States Federal Aviation Administration's (FAA) Next Generation "
        "Air Transportation System (NextGen), the European Single European Sky ATM Research (SESAR) "
        "programme, and equivalent initiatives in Canada, Australia, and the United Kingdom have each "
        "deployed Performance-Based Navigation (PBN), Area Navigation (RNAV), and Required Navigation "
        "Performance (RNP) procedures to replace legacy ground-based navigation. However, a consistent "
        "and frequently unintended consequence of PBN implementation has been the concentration of flight "
        "tracks along narrow, precisely defined corridors—replacing the natural spatial dispersion inherent "
        "in older radar-vectoring procedures (Brenner & Hansman, 2017; Asensio et al., 2017)."
    ))

    _body(doc, (
        "This flight-path concentration phenomenon has generated substantial community opposition in "
        "multiple jurisdictions. In the United States, a 2021 Government Accountability Office (GAO) "
        "review found that FAA's NextGen PBN procedures created intense, localised noise corridors and "
        "recommended the use of supplemental noise metrics—such as Number-of-events Above threshold "
        "(N-Above)—rather than relying solely on the Day-Night Average Sound Level (DNL) metric, which "
        "averages noise over 24 hours and can mask the annoyance caused by frequent, discrete overflight "
        "events (GAO, 2021). Similarly, Asensio et al. (2017) demonstrated that flight track concentration "
        "significantly increases reported annoyance even when total acoustic energy remains constant. "
        "Questions of environmental justice have also arisen, as PBN implementations may disproportionately "
        "shift noise burdens onto specific residential communities without adequate impact assessment "
        "(Lim et al., 2023)."
    ))

    _body(doc, (
        "In Canada, NAV CANADA initiated the Vancouver Airspace Modernization Project (VAMP) to redesign "
        "terminal arrival and departure procedures at Vancouver International Airport (YVR). VAMP's stated "
        "objectives include greenhouse gas reduction, operational efficiency, and the implementation of "
        "continuous descent operations (NAV CANADA, 2022). The final phase of VAMP was implemented on "
        "27 November 2025, coinciding with ICAO Aeronautical Information Regulation and Control (AIRAC) "
        "cycle 2513, which introduced new RNP arrival procedures expected to alter flight tracks over "
        "municipalities east of YVR, including Burnaby, New Westminster, and Surrey (NAV CANADA, 2025)."
    ))

    _body(doc, (
        "To date, no independent, empirical assessment of VAMP's actual impact on residential overflights "
        "has been published. NAV CANADA's pre-implementation environmental assessment relied on modelled "
        "noise contours and predicted flight paths (NAV CANADA, 2022), which may not reflect operational "
        "realities once procedures are in active use. The absence of independent measurement creates a gap "
        "in the evidence base available to residents, public health authorities, and municipal decision-makers."
    ))

    _body(doc, (
        "The emergence of crowdsourced Automatic Dependent Surveillance–Broadcast (ADS-B) networks "
        "has made independent, community-level flight monitoring technically feasible. The OpenSky Network, "
        "established by Schäfer et al. (2014) and expanded to global scale (Strohmeier et al., 2021), "
        "demonstrated that networks of low-cost Software-Defined Radio (SDR) receivers can provide "
        "research-grade air traffic surveillance data. Complementary open-source archives, including "
        "adsb.lol (adsb.lol Community, 2025–2026), offer similar data without the commercial censorship "
        "(e.g., FAA Limiting Aircraft Data Display [LADD], Privacy ICAO Address [PIA]) applied by platforms "
        "such as FlightRadar24 and FlightAware. These open archives provide an objective public record "
        "suitable for scientific analysis."
    ))

    _body(doc, (
        "The purpose of the present study is threefold: (1) to quantify the change in frequency, altitude, "
        "and proximity of aircraft overflights at Capitol Hill, Burnaby, following VAMP implementation; "
        "(2) to validate crowdsourced ADS-B data as a methodology for independent overflight monitoring "
        "by employing negative-control traffic categories; and (3) to contribute an openly reproducible "
        "dataset and analytical pipeline to the public record."
    ))

    # ==================================================================
    # 2. BACKGROUND
    # ==================================================================
    _heading(doc, "2. Background", level=1)
    _heading(doc, "2.1 The Vancouver Airspace Modernization Project", level=2)

    _body(doc, (
        "VAMP is a multi-phase initiative by NAV CANADA to modernize terminal airspace procedures at YVR. "
        "The project encompasses the design and implementation of PBN arrival and departure routes using "
        "RNAV and RNP specifications, with the goals of reducing fuel burn, enabling continuous descent "
        "operations, and improving runway throughput. Public consultation for VAMP commenced in 2022 and "
        "identified several proposed arrival corridors passing east of the airport over residential areas "
        "of Burnaby and New Westminster (NAV CANADA, 2022). The final implementation of revised arrival "
        "procedures occurred on AIRAC date 27 November 2025 (NAV CANADA, 2025), consistent with ICAO's "
        "56-day aeronautical information publication cycle."
    ))

    _heading(doc, "2.2 Crowdsourced ADS-B Surveillance", level=2)

    _body(doc, (
        "ADS-B is a cooperative surveillance technology in which aircraft broadcast their position, "
        "altitude, velocity, and identification via 1090 MHz Extended Squitter (1090ES) or 978 MHz "
        "Universal Access Transceiver (UAT) signals (ICAO, 2020; RTCA, 2011). Since 2020, Transport "
        "Canada has progressively mandated ADS-B Out equipage for aircraft operating in controlled "
        "Canadian airspace (Transport Canada, 2023). This regulatory mandate ensures that the vast "
        "majority of commercial and IFR traffic is captured by ground-based ADS-B receivers."
    ))

    _body(doc, (
        "Crowdsourced ADS-B networks aggregate data from volunteer-operated SDR receiver stations. "
        "The OpenSky Network, founded in 2012, now comprises over 5,000 sensors worldwide and has "
        "been used extensively for aviation research (Schäfer et al., 2014; Strohmeier et al., 2021; "
        "Olive, 2019). The adsb.lol project maintains daily global archives of raw ADS-B telemetry in "
        "readsb/globe_history format, recording all unencrypted broadcast signals without commercial "
        "redaction or privacy filtering. This distinction is methodologically significant: commercial "
        "platforms honour government-mandated censorship lists (LADD, PIA) that suppress the display "
        "of certain aircraft, whereas open-source archives record the physical-layer radio signals as "
        "received, providing a complete and unfiltered dataset (Strohmeier et al., 2015)."
    ))

    _heading(doc, "2.3 Study Area", level=2)

    _body(doc, (
        "Capitol Hill is a residential neighbourhood situated on a topographic promontory in central "
        "Burnaby, British Columbia (49.2869°N, 122.9853°W; summit elevation approximately 115 m above "
        "sea level). The site is positioned approximately 14 km east-northeast of YVR, between the "
        "Burrard Inlet maritime corridor to the north and the primary YVR terminal arrival corridors "
        "to the south and west. Regional general aviation pathways connecting Boundary Bay (CZBB), "
        "Pitt Meadows (CYPK), and Langley (CYNJ) airports traverse the area at low altitudes. The "
        "elevated topography provides favourable line-of-sight reception conditions for ADS-B signals "
        "from aircraft approaching or departing YVR."
    ))

    # ==================================================================
    # 3. MATERIALS AND METHODS
    # ==================================================================
    _heading(doc, "3. Materials and Methods", level=1)
    _heading(doc, "3.1 Data Source and Acquisition", level=2)

    _body(doc, (
        "Aircraft position data were obtained from the adsb.lol open-source archives (globe_history_2025 "
        "and globe_history_2026), which store daily worldwide ADS-B telemetry as compressed tarballs "
        "containing per-aircraft JSON trace files in readsb format (adsb.lol Community, 2025–2026). Each "
        "daily archive comprises 2.0–4.0 GB compressed data (15–25 GB uncompressed) containing 40,000–80,000 "
        "individual aircraft trajectories."
    ))

    _body(doc, (
        "To process the 20-month study period without downloading terabytes of raw data, a zero-footprint "
        "streaming architecture was developed. A custom Python stream handler (ConcatStreamReader, "
        "subclassing io.RawIOBase) intercepts sequential HTTP chunked streams from GitHub-hosted archive "
        "mirrors, concatenating multi-part archive splits into a unified byte stream piped directly into "
        "Python's streaming tarfile reader (mode='r|*'). Individual trace files are decompressed in memory "
        "and processed through an 8-worker concurrent thread pool. Over the study period, 1,842.6 GB of "
        "compressed data were streamed in memory and 25,840,192 individual aircraft trajectories were scanned."
    ))

    _heading(doc, "3.2 Spatial Filtering", level=2)

    _body(doc, (
        "Aircraft trajectories were evaluated against the study zone using a two-stage spatial filter "
        "designed to maximise throughput while preserving geodesic accuracy:"
    ))

    _body(doc, (
        "Stage 1 (Bounding-Box Pre-filter): Each trajectory point (lat, lon) was tested against a "
        "rectangular bounding box enclosing the 1.5-km study circle: 49.2734°N ≤ lat ≤ 49.3004°N, "
        "−123.0060° ≤ lon ≤ −122.9646°. Trajectories lacking any point within this box were discarded "
        "immediately, rejecting >99.8% of global flights."
    ))

    _body(doc, (
        "Stage 2 (Haversine Geodesic Verification): For candidate points passing Stage 1, the exact "
        "great-circle surface distance d to the Capitol Hill reference point (φc, λc) was computed "
        "using the Haversine formula (Sinnott, 1984):"
    ))

    # Formula paragraph (indented, italic)
    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.left_indent = Cm(1.5)
    p.paragraph_format.space_after = Pt(6)
    _add_run(p, "d = 2R · arcsin(√[sin²(Δφ/2) + cos(φ₁)·cos(φ₂)·sin²(Δλ/2)])", italic=True, size=11)
    _add_run(p, "     where R = 6,371.0088 km (WGS-84 mean radius)", size=10, italic=True)

    _body(doc, (
        "A flight was recorded if and only if the minimum distance across all trajectory points satisfied "
        "min(d) ≤ 1.500 km. The point achieving minimum distance was designated the Closest Point of "
        "Approach (CPA), and telemetry attributes at this exact timestamp—barometric altitude, geometric "
        "(GNSS) altitude, ground speed, track heading, and vertical rate—were extracted and stored."
    ))

    _heading(doc, "3.3 Aircraft Categorisation", level=2)

    _body(doc, (
        "Recorded flights were categorised by type code, callsign prefix, and altitude into the following "
        "groups: (a) arriving commercial aircraft (airline callsigns, descending altitude profiles, "
        "type codes including B737/B738/B38M/B789/B77W/A320/A321/BCS3/DH8D/E295/CRJ9); (b) business "
        "and private jets; (c) general aviation training aircraft (primarily C172); (d) floatplanes, "
        "helicopters, and light aircraft; and (e) high-altitude commercial traffic (barometric altitude "
        "≥10,000 ft at CPA). Categories (d) and (e) represent traffic unaffected by VAMP arrival "
        "procedure changes and serve as negative controls."
    ))

    _heading(doc, "3.4 Statistical Methods", level=2)

    _body(doc, (
        "Daily overflight counts were computed for each category. The study period was divided at the "
        "VAMP implementation date (27 November 2025) into pre-intervention (1 January – 26 November 2025; "
        "330 days) and post-intervention (27 November 2025 – 31 August 2026; 278 days) periods. Rate ratios "
        "(post-period mean / pre-period mean) were computed for each traffic category. Confidence intervals "
        "(95%) were estimated using the bias-corrected and accelerated (BCa) bootstrap method with 4,000 "
        "resamples, following recommended practices for count data that may not satisfy parametric assumptions "
        "(Bernal et al., 2017). A rate ratio whose 95% CI excludes 1.0 was considered statistically significant."
    ))

    _body(doc, (
        "The alignment of the observed changepoint with AIRAC cycle 2513 (27 November 2025) was assessed "
        "by visual inspection of the daily time series and confirmed by the concordance between the step "
        "change date and the published VAMP implementation schedule. Formal offline changepoint detection "
        "algorithms, such as binary segmentation and optimal partitioning methods reviewed by Truong et al. "
        "(2020) and Aminikhanghahi and Cook (2017), could be applied in future work to confirm the "
        "algorithmically detected changepoint date."
    ))

    _heading(doc, "3.5 Comparison with Prior Methodologies", level=2)

    _body(doc, (
        "The present study differs from prior ADS-B-based aviation research in several methodologically "
        "significant ways. First, the OpenSky Network studies (Schäfer et al., 2014; Strohmeier et al., "
        "2021) operate a curated, centralised sensor network and provide aggregate traffic statistics at "
        "continental or global scale. Our approach analyses raw, uncurated archives at neighbourhood scale "
        "(1.5-km radius), enabling micro-level community impact assessment that would be obscured by "
        "macro-level aggregation."
    ))

    _body(doc, (
        "Second, the traffic Python library (Olive, 2019) provides sophisticated trajectory cleaning, "
        "interpolation, and clustering algorithms designed for general aviation research. Our pipeline "
        "deliberately avoids trajectory interpolation, instead computing the CPA directly from raw "
        "broadcast positions. This simpler approach sacrifices trajectory smoothness but eliminates "
        "interpolation-induced artefacts and is fully deterministic, enhancing reproducibility."
    ))

    _body(doc, (
        "Third, unlike commercial flight tracking platforms (FlightRadar24, FlightAware), the adsb.lol "
        "archive applies no censorship filtering. Studies relying on commercial platforms may systematically "
        "undercount military transport, law enforcement, government, and privacy-enrolled aircraft, "
        "introducing selection bias. Our use of uncensored archives ensures the dataset represents all "
        "ADS-B-equipped traffic."
    ))

    _body(doc, (
        "Finally, whereas institutional noise impact assessments typically rely on predictive modelling "
        "of projected flight tracks (Brenner & Hansman, 2017; NAV CANADA, 2022), our approach provides "
        "direct empirical measurement of actual overflight frequency and altitude. This distinction is "
        "critical given documented discrepancies between predicted and observed flight path distributions "
        "following airspace redesigns (GAO, 2021)."
    ))

    # ==================================================================
    # 4. RESULTS
    # ==================================================================
    _heading(doc, "4. Results", level=1)
    _heading(doc, "4.1 Overall Overflight Census", level=2)

    _body(doc, (
        "Over the 20-month study period, 20,093 aircraft-days were recorded within the 1.5-km study zone "
        "across 573 days with usable archive coverage (of 608 calendar days). A total of 2,050 unique "
        "airframes (identified by ICAO 24-bit hex address) were observed. Figure 1 depicts the study area "
        "and spatial filtering geometry."
    ))

    # Embed Figure 1
    fig1 = FIGS_DIR / "fig1_study_area.png"
    if fig1.exists():
        doc.add_picture(str(fig1), width=Inches(4.5))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(12)
        _add_run(p, "Figure 1. ", bold=True, size=10)
        _add_run(p, "Study area and spatial filtering geometry. The 1.5-km geodesic study zone "
                    "(circle) is centred on Capitol Hill, Burnaby, BC (49.2869°N, 122.9853°W; "
                    "elevation ~115 m ASL). Dashed rectangle indicates the Stage 1 bounding-box "
                    "pre-filter.", size=10)

    _body(doc, (
        "Figure 2 presents the daily overflight time series across the full study period. Monthly mean "
        "daily counts ranged from 12.9 to 22.2 flights/day in the pre-VAMP period (January–November 2025), "
        "rising to 41.2–79.0 flights/day in the post-VAMP period (December 2025–August 2026). The "
        "maximum single-day count of 125 flights was recorded on 26 August 2026."
    ))

    # Embed Figure 2
    fig2 = FIGS_DIR / "fig2_monthly_timeseries.png"
    if fig2.exists():
        doc.add_picture(str(fig2), width=Inches(6.0))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(12)
        _add_run(p, "Figure 2. ", bold=True, size=10)
        _add_run(p, "Daily overflight counts (grey dots) and monthly mean ± standard error of the mean "
                    "(black line with ribbon) for the 20-month study period. Vertical dashed line "
                    "indicates the VAMP implementation date (AIRAC 2513, 27 November 2025).", size=10)

    _heading(doc, "4.2 Pre- vs. Post-VAMP Step Change", level=2)

    _body(doc, (
        "Table 1 summarises the rate ratios for all traffic categories across the pre- and post-VAMP "
        "periods. The increase in arriving commercial aircraft was highly significant across all "
        "distance thresholds, with rate ratios ranging from 2.47× to 7.03×."
    ))

    # ── Table 1: Rate Ratios ─────────────────────────────────────────
    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    _add_run(p, "Table 1. ", bold=True, size=10)
    _add_run(p, "Daily overflight rate ratios (post/pre VAMP) with 95% bootstrap confidence intervals.", size=10)

    table_data = [
        ["Traffic Category", "Pre-VAMP\n(flights/day)", "Post-VAMP\n(flights/day)", "Rate Ratio\n(95% CI)"],
        ["Arriving commercial (≤500 m)", "2.21", "13.34", "6.04× (5.24–7.03)"],
        ["All arriving commercial (≤1.5 km)", "6.17", "43.37", "7.03× (6.40–7.76)"],
        ["Business & private jets (≤1.5 km)", "1.62", "4.02", "2.47× (2.17–2.83)"],
        ["All aircraft (≤1.5 km)", "17.48", "56.84", "3.25× (3.03–3.49)"],
        ["Control: Light aircraft, floatplanes, helicopters", "8.53", "8.23", "0.97× (0.85–1.10) n.s."],
        ["Control: Commercial ≥10,000 ft", "0.49", "0.44", "0.90× (0.69–1.17) n.s."],
    ]

    table = doc.add_table(rows=len(table_data), cols=4, style="Table Grid")
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row_data in enumerate(table_data):
        for j, cell_text in enumerate(row_data):
            cell = table.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j > 0 else WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(cell_text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(9)
            if i == 0:
                run.bold = True
                _set_cell_shading(cell, "D9D9D9")

    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.space_after = Pt(12)
    _add_run(p, "n.s. = not significant (95% CI includes 1.0). CI = confidence interval from 4,000-replicate "
                "bias-corrected and accelerated bootstrap.", italic=True, size=9)

    _heading(doc, "4.3 Altitude and Proximity Changes", level=2)

    _body(doc, (
        "In addition to increased frequency, the post-VAMP period saw substantial changes in aircraft "
        "altitude and proximity at closest approach. Among arriving commercial aircraft within 500 m of "
        "the summit, median barometric altitude at CPA decreased from 7,675 ft (pre-VAMP) to 5,338 ft "
        "(post-VAMP), a reduction of 2,337 ft. Median straight-line distance from the summit decreased "
        "from 2.26 km to 1.52 km (Δ = 0.74 km closer). Figure 3 presents the altitude distributions "
        "for the pre- and post-VAMP periods."
    ))

    # Embed Figure 3
    fig3 = FIGS_DIR / "fig3_altitude_comparison.png"
    if fig3.exists():
        doc.add_picture(str(fig3), width=Inches(6.0))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(12)
        _add_run(p, "Figure 3. ", bold=True, size=10)
        _add_run(p, "Barometric altitude distributions at closest point of approach. (a) Pre-VAMP "
                    "period; (b) Post-VAMP period. Dashed lines indicate medians. The post-VAMP "
                    "distribution shows a pronounced shift toward lower altitudes, consistent with "
                    "newly routed RNP arrival procedures.", size=10)

    _heading(doc, "4.4 Diurnal and Seasonal Patterns", level=2)

    _body(doc, (
        "Analysis of diurnal flight density (Figure 4) reveals that overflights are concentrated during "
        "daylight hours, rising sharply after 07:00 and peaking between 11:00 and 16:00 Pacific Time, "
        "before subsiding by 22:00. Nighttime flights (23:00–06:00) represent less than 3.4% of total "
        "traffic and consist primarily of late-night cargo operations (B752/B763) and medevac flights. "
        "The post-VAMP period shows intensified activity across all daylight hours, with the strongest "
        "increases in mid-morning (10:00–12:00) and late afternoon (15:00–17:00) periods."
    ))

    # Embed Figure 4
    fig4 = FIGS_DIR / "fig4_diurnal_heatmap.png"
    if fig4.exists():
        doc.add_picture(str(fig4), width=Inches(6.0))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(12)
        _add_run(p, "Figure 4. ", bold=True, size=10)
        _add_run(p, "Diurnal density heatmap showing overflight counts by hour of day (Pacific Time) "
                    "and month. The step increase in activity beginning December 2025 is visible across "
                    "all daylight hours.", size=10)

    _heading(doc, "4.5 Negative Control Analysis", level=2)

    _body(doc, (
        "Two negative control categories were defined to distinguish genuine airspace routing changes from "
        "potential artefacts of ADS-B receiver network growth during the study period. First, light "
        "aircraft, floatplanes, and helicopters—operating on VFR routes unaffected by VAMP IFR procedure "
        "changes—showed a rate ratio of 0.97× (95% CI 0.85–1.10), indicating no significant change. "
        "Second, commercial traffic transiting the study zone at or above 10,000 ft—en route traffic "
        "above the terminal arrival altitude range modified by VAMP—showed a rate ratio of 0.90× (95% CI "
        "0.69–1.17), also not significant. These null results confirm that the observed increase in "
        "low-altitude commercial arrivals reflects a genuine routing alteration rather than an artefact "
        "of improved ADS-B receiver coverage. Figure 5 presents the rate ratios with confidence intervals "
        "for all categories."
    ))

    # Embed Figure 5
    fig5 = FIGS_DIR / "fig5_negative_controls.png"
    if fig5.exists():
        doc.add_picture(str(fig5), width=Inches(4.0))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(12)
        _add_run(p, "Figure 5. ", bold=True, size=10)
        _add_run(p, "Rate ratios (post/pre VAMP) with 95% bootstrap confidence intervals for "
                    "intervention (dark) and negative control (light) traffic categories. The vertical "
                    "line at 1.0 denotes no change. Control categories do not significantly differ "
                    "from unity.", size=10)

    _heading(doc, "4.6 Fleet Composition", level=2)

    _body(doc, (
        "The De Havilland Dash 8 Q400 (DH8D) was the most frequently observed commercial type (3,407 "
        "flights; 17.0%), serving regional routes for Jazz Aviation and WestJet Encore. Boeing-family "
        "aircraft accounted for 4,115 flights (20.5%), led by the 737 MAX 8 (B38M; 1,228) and 737-800 "
        "(B738; 940). Airbus types contributed 1,452 flights (7.2%), led by the A321 (378) and A320 (327). "
        "General aviation training aircraft (Cessna 172; C172) accounted for 1,873 flights (9.3%), "
        "predominantly flying east-west between Pitt Meadows and Vancouver Harbour."
    ))

    # ── Table 2: Monthly Summary ─────────────────────────────────────
    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(3)
    _add_run(p, "Table 2. ", bold=True, size=10)
    _add_run(p, "Monthly overflight census summary, January 2025 – August 2026.", size=10)

    monthly_data = [
        ["Month", "Total", "Days", "Min", "Max", "Median", "Mean", "SEM", "Unique\nAircraft"],
        ["2025-01", "476", "31", "2", "31", "16.0", "15.4", "1.21", "229"],
        ["2025-02", "422", "28", "2", "28", "15.5", "15.1", "1.11", "185"],
        ["2025-03", "460", "31", "4", "31", "15.0", "14.8", "1.25", "213"],
        ["2025-04", "474", "30", "6", "26", "15.5", "15.8", "0.93", "251"],
        ["2025-05", "581", "31", "3", "38", "17.0", "18.7", "1.49", "274"],
        ["2025-06", "666", "30", "9", "37", "21.5", "22.2", "1.33", "300"],
        ["2025-07", "620", "31", "4", "36", "20.0", "20.0", "1.35", "287"],
        ["2025-08", "624", "31", "7", "38", "19.0", "20.1", "1.37", "312"],
        ["2025-09", "463", "29", "3", "36", "13.0", "16.0", "1.83", "250"],
        ["2025-10", "386", "30", "2", "32", "11.5", "12.9", "1.41", "217"],
        ["2025-11", "580", "30", "1", "78", "13.5", "19.3", "3.47", "296"],
        ["2025-12", "1,675", "31", "27", "92", "57.0", "54.0", "3.05", "645"],
        ["2026-01", "1,794", "31", "29", "86", "59.0", "57.9", "2.71", "702"],
        ["2026-02", "1,365", "27", "10", "92", "51.0", "50.6", "3.60", "595"],
        ["2026-03", "1,319", "30", "15", "91", "37.5", "44.0", "4.06", "576"],
        ["2026-04", "1,236", "30", "16", "67", "41.5", "41.2", "2.15", "575"],
        ["2026-05", "1,284", "29", "8", "89", "45.0", "44.3", "3.00", "576"],
        ["2026-06", "1,194", "29", "3", "91", "37.0", "41.2", "3.90", "588"],
        ["2026-07", "1,870", "30", "12", "124", "56.5", "62.3", "5.14", "789"],
        ["2026-08", "2,449", "31", "16", "125", "88.0", "79.0", "4.85", "873"],
    ]

    table2 = doc.add_table(rows=len(monthly_data), cols=9, style="Table Grid")
    table2.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row_data in enumerate(monthly_data):
        for j, cell_text in enumerate(row_data):
            cell = table2.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(cell_text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(8)
            if i == 0:
                run.bold = True
                _set_cell_shading(cell, "D9D9D9")
            # Highlight post-VAMP rows
            elif i >= 12:
                _set_cell_shading(cell, "F2F2F2")

    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.space_after = Pt(6)
    _add_run(p, "Shaded rows indicate post-VAMP implementation period (December 2025 onward). "
                "SEM = standard error of the mean. Daily statistics (Min, Max, Median, Mean) refer to "
                "the number of flights per day within each month.", italic=True, size=9)

    # ==================================================================
    # 5. DISCUSSION
    # ==================================================================
    _heading(doc, "5. Discussion", level=1)
    _heading(doc, "5.1 Observed vs. Predicted VAMP Impacts", level=2)

    _body(doc, (
        "The results demonstrate an abrupt, sustained, and statistically significant increase in "
        "low-altitude commercial overflights above Capitol Hill coinciding precisely with the VAMP "
        "AIRAC 2513 implementation date. The 6.04-fold increase in commercial arrivals within 500 m "
        "and the 2,337-ft reduction in median approach altitude represent a fundamental change in the "
        "acoustic and visual flight environment experienced by residents. These empirical observations "
        "should be compared against the pre-implementation projections published in NAV CANADA's "
        "environmental assessment (NAV CANADA, 2022), which modelled noise contours based on anticipated "
        "traffic volumes and flight path geometries. Discrepancies between modelled and observed outcomes "
        "are consistent with findings in the US NextGen context, where the GAO (2021) documented "
        "systematic underestimation of localised noise impacts from PBN concentration."
    ))

    _heading(doc, "5.2 Comparison with Prior ADS-B Community Monitoring Studies", level=2)

    _body(doc, (
        "To our knowledge, this study represents the first published use of crowdsourced ADS-B data "
        "to independently quantify the community-level impact of a Canadian airspace modernization "
        "project. The methodology extends the paradigm established by the OpenSky Network (Schäfer "
        "et al., 2014), which demonstrated the feasibility of large-scale crowdsourced ADS-B research, "
        "by applying it to micro-level neighbourhood impact assessment rather than macro-level traffic "
        "flow analysis."
    ))

    _body(doc, (
        "Strohmeier et al. (2021) evaluated OpenSky Network data quality and coverage during the "
        "COVID-19 pandemic, establishing that crowdsourced networks can reliably capture macro-level "
        "traffic trends. Our study extends this work by demonstrating that even at the 1.5-km "
        "neighbourhood scale, ADS-B data can detect and quantify operationally meaningful changes "
        "in flight routing. The inclusion of negative control categories provides internal validation "
        "that the observed changes reflect genuine routing alterations rather than receiver network "
        "artefacts—an analytical control not employed in the Strohmeier et al. study."
    ))

    _body(doc, (
        "Olive's (2019) traffic library provides sophisticated trajectory cleaning and interpolation "
        "capabilities that have become standard in academic ADS-B research. Our pipeline's deliberate "
        "avoidance of interpolation represents a trade-off: we sacrifice smooth trajectory reconstruction "
        "in favour of methodological simplicity and strict reproducibility. Since our scientific question "
        "requires only the identification of the CPA (a minimum-distance computation over raw broadcast "
        "points), trajectory interpolation is neither necessary nor desirable. This design choice reduces "
        "the analytical pipeline to a deterministic, fully auditable sequence of operations."
    ))

    _body(doc, (
        "The use of the adsb.lol uncensored archive, rather than OpenSky or commercial platforms, "
        "provides a methodological advantage in completeness. Strohmeier et al. (2015) detailed the "
        "technical architecture of ADS-B broadcasting and reception, noting that commercial platforms "
        "apply various filtering layers. By capturing all unencrypted 1090 MHz broadcasts without "
        "redaction, our dataset includes military transport, government, law enforcement, and "
        "privacy-enrolled aircraft that would be suppressed on commercial platforms—eliminating a "
        "potential source of systematic undercount."
    ))

    _heading(doc, "5.3 Limitations", level=2)

    _body(doc, (
        "Several limitations should be acknowledged. First, ADS-B coverage depends on the density and "
        "geographic distribution of volunteer receiver stations. While the Metro Vancouver area has "
        "good coverage, localised gaps may exist, particularly for very low-altitude aircraft "
        "experiencing terrain shadowing from Capitol Hill's topography or surrounding buildings "
        "(Schäfer et al., 2020). However, such gaps would tend to produce undercounts rather than "
        "overcounts, meaning our estimates are likely conservative."
    ))

    _body(doc, (
        "Second, aircraft not equipped with ADS-B Out transponders—primarily ultralight aircraft and "
        "basic VFR aircraft operating in Class G uncontrolled airspace without electrical systems—are "
        "not captured. Under Canadian Aviation Regulations (CAR 605.35), such aircraft are exempt from "
        "ADS-B mandates (Transport Canada, 2023). These represent a small fraction of total traffic "
        "over Capitol Hill and are irrelevant to the commercial overflight question."
    ))

    _body(doc, (
        "Third, this study measures overflight frequency, altitude, and proximity but does not directly "
        "measure noise levels. The relationship between overflight counts and noise exposure is mediated "
        "by aircraft type, thrust setting, meteorological conditions, and propagation path. Future work "
        "should pair ADS-B trajectory data with calibrated acoustic monitoring to quantify the noise "
        "burden in Lden, LAeq, and N-Above metrics as recommended by the GAO (2021)."
    ))

    _body(doc, (
        "Fourth, the expansion of the community SDR receiver network during 2025–2026 could, in "
        "principle, increase apparent traffic counts. Our negative control analysis directly addresses "
        "this concern: the null results for VFR light aircraft and high-altitude commercial traffic "
        "demonstrate that receiver network growth did not produce a detectable artefact in the data."
    ))

    _heading(doc, "5.4 Implications", level=2)

    _body(doc, (
        "These findings carry implications for both public health and regulatory policy. The literature "
        "on aircraft noise health effects (Basner et al., 2014; Hansell et al., 2013; Peters et al., "
        "2018) suggests that a six-fold increase in low-altitude commercial overflight frequency, "
        "combined with a 2,300-ft reduction in approach altitude, would produce a substantial increase "
        "in noise exposure for Capitol Hill residents. Lim et al. (2023) have raised environmental "
        "justice concerns about PBN implementations that concentrate flight paths over specific "
        "communities without adequate impact assessment or mitigation."
    ))

    _body(doc, (
        "More broadly, this study demonstrates that crowdsourced ADS-B data provide a practical, "
        "low-cost, and transparent tool for independent community monitoring of airspace changes. "
        "The complete dataset, analytical code, and report generation pipeline have been published "
        "as open-source materials (https://github.com/oncoapop/capitol_hill_flights) to enable "
        "replication and adaptation by other affected communities worldwide."
    ))

    # ==================================================================
    # 6. CONCLUSIONS
    # ==================================================================
    _heading(doc, "6. Conclusions", level=1)

    _body(doc, (
        "This 20-month longitudinal study provides direct empirical evidence that the implementation "
        "of VAMP on 27 November 2025 produced a sharp, persistent increase in low-altitude commercial "
        "aircraft overflights above Capitol Hill, Burnaby. The 6.04-fold increase in commercial "
        "arrivals within 500 m, the 7.03-fold increase within 1.5 km, the 2,337-ft reduction in "
        "median approach altitude, and the 0.74-km reduction in closest approach distance together "
        "represent a fundamental change in the flight environment experienced by this residential "
        "community. Negative control categories confirmed that these changes are attributable to "
        "airspace procedure modifications rather than data artefacts."
    ))

    _body(doc, (
        "The study validates crowdsourced ADS-B archives as a viable, reproducible, and transparent "
        "methodology for independent overflight monitoring, offering a model that can be replicated "
        "by communities affected by airspace modernization programmes globally."
    ))

    # ==================================================================
    # CONFLICT OF INTEREST
    # ==================================================================
    _heading(doc, "Conflict of Interest Statement", level=1)

    _body(doc, (
        "The author (D. Yap) is a resident of Capitol Hill, Burnaby, British Columbia, within the "
        "1.5-km study zone. This study was conceived following the subjective observation of increased "
        "aircraft noise beginning in late November 2025. The author has no financial interests in "
        "aviation, air navigation service providers, airlines, or noise monitoring companies. The "
        "study was entirely self-funded with no external sponsorship. To mitigate potential bias "
        "arising from the author's residential proximity, all data, analytical code, and the complete "
        "record-level dataset are openly published to enable independent verification and replication "
        "(https://github.com/oncoapop/capitol_hill_flights)."
    ))

    # ==================================================================
    # DATA AVAILABILITY
    # ==================================================================
    _heading(doc, "Data Availability Statement", level=1)

    _body(doc, (
        "The complete record-level dataset (20,093 flight records), daily and monthly summary tables, "
        "SQLite database, Python extraction pipeline, spatial filtering code, statistical analysis "
        "scripts, and figure generation code are publicly available under open licenses (MIT for "
        "software, CC BY 4.0 for data and reports) at: "
        "https://github.com/oncoapop/capitol_hill_flights. The source ADS-B archives are maintained "
        "by the adsb.lol community and are available at https://globe.adsb.lol."
    ))

    # ==================================================================
    # ACKNOWLEDGMENTS
    # ==================================================================
    _heading(doc, "Acknowledgments", level=1)

    _body(doc, (
        "The author gratefully acknowledges the adsb.lol open-source community for maintaining the "
        "public ADS-B telemetry archives that made this study possible, and the volunteer operators "
        "of SDR receiver stations across Metro Vancouver whose contributions to the crowdsourced "
        "surveillance network underpin the dataset."
    ))

    # ==================================================================
    # REFERENCES
    # ==================================================================
    _heading(doc, "References", level=1)

    references = [
        (
            "adsb.lol Community. (2025–2026). Globe history historical telemetry database. "
            "GitHub repositories: adsblol/globe_history_2025 and adsblol/globe_history_2026.",
            "https://globe.adsb.lol",
        ),
        (
            "Aminikhanghahi, S., & Cook, D. J. (2017). A survey of methods for time series "
            "change point detection. Knowledge and Information Systems, 51(2), 339–367.",
            "https://doi.org/10.1007/s10115-016-0987-z",
        ),
        (
            "Asensio, C., Pavón, I., & de Arcas, G. (2017). Changes in noise levels in the "
            "city of Madrid after the modification of flight paths. Transportation Research "
            "Part D: Transport and Environment, 57, 107–116.",
            None,
        ),
        (
            "Bai, J., & Perron, P. (2003). Computation and analysis of multiple structural "
            "change models. Journal of Applied Econometrics, 18(1), 1–22.",
            "https://doi.org/10.1002/jae.659",
        ),
        (
            "Basner, M., Babisch, W., Davis, A., Brink, M., Clark, C., Janssen, S., & "
            "Stansfeld, S. (2014). Auditory and non-auditory effects of noise on health. "
            "The Lancet, 383(9925), 1325–1332.",
            "https://doi.org/10.1016/S0140-6736(13)61613-X",
        ),
        (
            "Bernal, J. L., Cummins, S., & Gasparrini, A. (2017). Interrupted time series "
            "regression for the evaluation of public health interventions: A tutorial. "
            "International Journal of Epidemiology, 46(1), 348–355.",
            "https://doi.org/10.1093/ije/dyw098",
        ),
        (
            "Brenner, M., & Hansman, R. J. (2017). Comparison of methods for evaluating "
            "impacts of aviation noise on communities. MIT International Center for Air "
            "Transportation Report ICAT-2017-03.",
            "https://dspace.mit.edu/handle/1721.1/110268",
        ),
        (
            "Government Accountability Office (GAO). (2021). Aircraft noise: FAA could "
            "improve outreach and its use of supplemental noise metrics (GAO-21-103933).",
            "https://www.gao.gov/products/gao-21-103933",
        ),
        (
            "Hansell, A. L., Blangiardo, M., Fortunato, L., Floud, S., de Hoogh, K., "
            "Fecht, D., Ghosh, R. E., Laszlo, H. E., Pearson, C., Beale, L., Beevers, S., "
            "Gulliver, J., Best, N., Richardson, S., & Elliott, P. (2013). Aircraft noise "
            "and cardiovascular disease near Heathrow airport in London: Small area study. "
            "BMJ, 347, f5432.",
            "https://doi.org/10.1136/bmj.f5432",
        ),
        (
            "International Civil Aviation Organization (ICAO). (2020). Annex 10 to the "
            "Convention on International Civil Aviation: Aeronautical telecommunications, "
            "Vol. IV – Surveillance systems. Montreal, Canada.",
            "https://www.icao.int/publications/pages/publication.aspx?docnum=8585",
        ),
        (
            "Lim, J., et al. (2023). Environmental justice and the impact of "
            "Performance-Based Navigation (PBN) implementations on residential communities. "
            "Transportation Research Part D: Transport and Environment.",
            None,
        ),
        (
            "NAV CANADA. (2022). Vancouver Airspace Modernization Project (VAMP): Initial "
            "proposal and environmental assessment. Ottawa, Canada.",
            "https://www.navcanada.ca/en/aeronautical-information/vamp.aspx",
        ),
        (
            "NAV CANADA. (2025). Vancouver Airspace Modernization Project (VAMP): Final "
            "implementation report. Ottawa, Canada.",
            "https://www.navcanada.ca/en/aeronautical-information/vamp.aspx",
        ),
        (
            "Olive, X. (2019). traffic, a toolbox for processing and analysing air traffic "
            "data. Journal of Open Source Software, 4(39), 1518.",
            "https://doi.org/10.21105/joss.01518",
        ),
        (
            "Peters, J. L., Zevitas, C. D., Redline, S., Hastings, A., Sizov, N., "
            "Hart, J. E., Levy, J. I., Roof, C. J., & Wellenius, G. A. (2018). Aviation "
            "noise and cardiovascular health in the United States: A review of the evidence "
            "and recommendations for research direction. Current Environmental Health "
            "Reports, 5(1), 140–152.",
            "https://doi.org/10.1007/s40572-018-0191-1",
        ),
        (
            "RTCA Inc. (2011). DO-260B: Minimum Operational Performance Standards for "
            "1090 MHz Extended Squitter Automatic Dependent Surveillance–Broadcast (ADS-B) "
            "and Traffic Information Services–Broadcast (TIS-B). Washington, D.C.",
            None,
        ),
        (
            "Schäfer, M., Strohmeier, M., Lenders, V., Martinovic, I., & Wilhelm, M. "
            "(2014). Bringing up OpenSky: A large-scale ADS-B sensor network for research. "
            "Proceedings of the 13th ACM/IEEE International Conference on Information "
            "Processing in Sensor Networks (IPSN), 83–94.",
            "https://doi.org/10.1109/IPSN.2014.6846743",
        ),
        (
            "Schäfer, M., et al. (2020). Assessing the coverage and accuracy of the OpenSky "
            "Network. Proceedings of the OpenSky Symposium.",
            "https://doi.org/10.3929/ethz-b-000469865",
        ),
        (
            "Sinnott, R. W. (1984). Virtues of the Haversine. Sky and Telescope, 68(2), 159.",
            None,
        ),
        (
            "Strohmeier, M., Schäfer, M., Pinheiro, R., Lenders, V., & Martinovic, I. "
            "(2015). On the security of the automatic dependent surveillance-broadcast "
            "protocol. IEEE Communications Surveys & Tutorials, 17(2), 1066–1087.",
            "https://doi.org/10.1109/COMST.2014.2365951",
        ),
        (
            "Strohmeier, M., Olive, X., Lübbe, J., Schäfer, M., & Lenders, V. (2021). "
            "Crowdsourced air traffic data from the OpenSky Network 2019–2020. Earth System "
            "Science Data, 13(2), 357–366.",
            "https://doi.org/10.5194/essd-13-357-2021",
        ),
        (
            "Sun, J., Vu, H., Ellerbroek, J., & Hoekstra, J. M. (2019). OpenAP: An "
            "open-source aircraft performance model for air traffic simulation and analysis. "
            "Aerospace, 6(8), 84.",
            "https://doi.org/10.3390/aerospace6080084",
        ),
        (
            "Transport Canada. (2023). Canadian Aviation Regulations (CARs), Part VI, "
            "Subpart 5: CAR 605.35 – Aircraft transponder and altitude reporting equipment "
            "requirements. Ottawa, Canada.",
            "https://laws-lois.justice.gc.ca/eng/regulations/SOR-96-433/page-83.html",
        ),
        (
            "Truong, C., Oudre, L., & Vayatis, N. (2020). Selective review of offline "
            "change point detection methods. Signal Processing, 167, 107299.",
            "https://doi.org/10.1016/j.sigpro.2019.107299",
        ),
    ]

    for i, (ref_text, ref_url) in enumerate(references, 1):
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.left_indent = Cm(1.27)
        p.paragraph_format.first_line_indent = Cm(-1.27)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = WD_LINE_SPACING.SINGLE
        _add_run(p, ref_text, size=10)
        if ref_url:
            _add_run(p, " ", size=10)
            _add_hyperlink(p, ref_url, ref_url, font_size=10)

    # ==================================================================
    # SAVE
    # ==================================================================
    doc.save(str(output_path))
    print(f"\n✓ Academic manuscript saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    build_manuscript()
