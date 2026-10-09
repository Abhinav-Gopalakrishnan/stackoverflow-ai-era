"""Build pristine, publication-grade white-background presentation decks for Member 5 (Adhikkesh).

Outputs:
1. Adhikkesh_Member_5_Only_Slides.pptx  (6 dedicated technical model, time series & evaluation slides)
2. Member_5_Review_1_Slides_White.pptx (10 complete presentation slides including title, tracking, contributions, plan, thank you)
"""

from pathlib import Path
import pptx
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "reports" / "review1" / "deck_assets"
OUT_M5_ONLY = ROOT / "Adhikkesh_Member_5_Only_Slides.pptx"
OUT_M5_FULL = ROOT / "Member_5_Review_1_Slides_White.pptx"

# Crisp Academic Palette (Pure White Theme)
BG_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PANEL_BG = RGBColor(0xF8, 0xFA, 0xFC)        # Crisp light slate background
PANEL_BORDER = RGBColor(0xCB, 0xD5, 0xE1)    # Crisp slate hairline border (#CBD5E1)
NAVY_PRIMARY = RGBColor(0x1D, 0x4E, 0x89)    # Academic Deep Navy
NAVY_HEADER = RGBColor(0x0F, 0x2A, 0x4A)     # Darkest navy for main titles
SKY_ACCENT = RGBColor(0x02, 0x84, 0xC7)      # Vivid sky blue
ORANGE_ACCENT = RGBColor(0xD9, 0x77, 0x06)   # Warm amber/orange
TEAL_ACCENT = RGBColor(0x0F, 0x76, 0x6E)     # Emerald / teal
TEXT_INK = RGBColor(0x1F, 0x29, 0x37)        # High-contrast charcoal text
TEXT_MUTED = RGBColor(0x4B, 0x55, 0x63)      # Secondary slate text
TEXT_LIGHT = RGBColor(0x6B, 0x72, 0x80)      # Gray caption text
ROW_ALT = RGBColor(0xF1, 0xF5, 0xF9)         # Alternating table row
HIGHLIGHT_ROW = RGBColor(0xFE, 0xF3, 0xC7)   # Amber highlight row
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def set_slide_background_white(slide):
    """Ensure slide background is solid pure white."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = BG_WHITE


def add_text_run(paragraph, text, font="Arial", size=10, bold=False, color=TEXT_INK):
    """Helper to add formatted text run."""
    run = paragraph.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return run


def add_header(slide, title_text, kicker_text="MEMBER 5: PREDICTIVE MODELING & EVALUATION", slide_num=None):
    """Standardized top banner with category kicker and title."""
    set_slide_background_white(slide)

    header_box = slide.shapes.add_textbox(Inches(0.40), Inches(0.18), Inches(9.20), Inches(1.00))
    tf = header_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_kicker = tf.paragraphs[0]
    p_kicker.space_after = Pt(2)
    add_text_run(p_kicker, kicker_text.upper(), font="Arial", size=8.5, bold=True, color=SKY_ACCENT)

    p_title = tf.add_paragraph()
    p_title.space_after = Pt(0)
    add_text_run(p_title, title_text, font="Arial", size=18, bold=True, color=NAVY_HEADER)

    # Hairline divider
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.40), Inches(1.10), Inches(9.20), Inches(0.015))
    line.fill.solid()
    line.fill.fore_color.rgb = PANEL_BORDER
    line.line.fill.background()

    # Footer
    footer_box = slide.shapes.add_textbox(Inches(0.40), Inches(5.36), Inches(9.20), Inches(0.20))
    tff = footer_box.text_frame
    tff.margin_left = tff.margin_top = tff.margin_right = tff.margin_bottom = 0
    pf = tff.paragraphs[0]
    add_text_run(pf, "Stack Overflow in the AI Era  |  Course 23CSE452: Business Analytics  |  Member 5: Adhikkesh S K (CB.SC.U4CSE23101)",
                 font="Arial", size=7.5, color=TEXT_LIGHT)
    if slide_num is not None:
        p_num = tff.add_paragraph()
        p_num.alignment = PP_ALIGN.RIGHT
        add_text_run(p_num, str(slide_num), font="Arial", size=7.5, bold=True, color=TEXT_LIGHT)


def add_flat_card(slide, left, top, width, height, border_color=PANEL_BORDER, bg_color=PANEL_BG):
    """Add a flat card with crisp hairline border (no rounded distortion or drop shadows)."""
    card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1)
    return card


# -----------------------------------------------------------------------------
# SLIDE BUILDERS (True Aspect Ratios, Pure White Mats)
# -----------------------------------------------------------------------------

def build_slide_1_model_dev(prs, slide_num=1):
    """Slide 1: Predictive Model Development & Chronological Splitting."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "Predictive Model Development & Chronological Partitioning",
               "MEMBER 5: PREDICTIVE MODELING (COURSE OUTCOME 4)", slide_num)

    # Top Half: 3 structured cards
    w_card = Inches(2.95)
    h_top = Inches(1.50)
    top_pos = Inches(1.18)

    cards_data = [
        ("Task & Architecture", [
            ("Task: ", "Binary classification — will a newly posted question receive an accepted answer in 7 days?"),
            ("Models: ", "Majority Baseline, Logistic Regression (+Text SVD), Random Forest (472 trees), and XGBoost.")
        ], SKY_ACCENT),
        ("Chronological Split", [
            ("Train: ", "2019–2024 (248,294 rows, 85%)"),
            ("Validation: ", "Jan–Jun 2025 (28,132 rows, 10%)"),
            ("Held-Out Test: ", "Jul 2025–Jul 2026 (16,695 rows, 5%, scored once)")
        ], TEAL_ACCENT),
        ("Leakage & Tuning", [
            ("Purged Folds: ", "7-day blackout gap across splits prevents target outcome leakage."),
            ("Tuned XGBoost: ", "PR-AUC 0.482 (vs 0.473 RF, 0.471 LogReg), lr=0.029, depth=5, threshold=0.367.")
        ], ORANGE_ACCENT),
    ]

    for i, (head, items, border_c) in enumerate(cards_data):
        left_pos = Inches(0.40 + i * 3.12)
        add_flat_card(slide, left_pos, top_pos, w_card, h_top, border_color=border_c)

        tb = slide.shapes.add_textbox(left_pos + Inches(0.12), top_pos + Inches(0.10), w_card - Inches(0.24), h_top - Inches(0.20))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p0 = tf.paragraphs[0]
        p0.space_after = Pt(4)
        add_text_run(p0, head, font="Arial", size=9.5, bold=True, color=border_c)

        for tag_label, text in items:
            p = tf.add_paragraph()
            p.space_after = Pt(2)
            add_text_run(p, "• ", font="Arial", size=8.5, bold=True, color=border_c)
            add_text_run(p, tag_label, font="Arial", size=8.5, bold=True, color=NAVY_PRIMARY)
            add_text_run(p, text, font="Arial", size=8.2, bold=False, color=TEXT_INK)

    # Bottom Half: Full-width chronological split timeline chart (aspect ratio 2.63)
    split_img = ASSETS / "split_white.png"
    if split_img.exists():
        # Chart natural size: 9.20 in width x 2.40 in height
        slide.shapes.add_picture(str(split_img), Inches(0.40), Inches(2.78), Inches(9.20), Inches(2.45))


def build_slide_2_evaluation(prs, slide_num=2):
    """Slide 2: Model Evaluation & Benchmark Comparison."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "Model Evaluation & Benchmark Comparison on Held-Out Test Set",
               "MEMBER 5: EVALUATION FRAMEWORK & METRICS", slide_num)

    # Table on Left
    t_shape = slide.shapes.add_table(7, 7, Inches(0.40), Inches(1.20), Inches(5.60), Inches(2.25))
    table = t_shape.table
    table.columns[0].width = Inches(1.64)
    table.columns[1].width = Inches(0.63)
    table.columns[2].width = Inches(0.63)
    table.columns[3].width = Inches(0.63)
    table.columns[4].width = Inches(0.63)
    table.columns[5].width = Inches(0.70)
    table.columns[6].width = Inches(0.74)

    data = [
        ["Model Architecture", "Accuracy", "Precision", "Recall", "F1", "PR-AUC", "ROC-AUC"],
        ["Majority Class Baseline", "0.659", "0.000", "0.000", "0.000", "0.341", "0.500"],
        ["Baseline Logistic Regression", "0.412", "0.357", "0.909", "0.513", "0.394", "0.579"],
        ["Logistic Regression (+Text SVD)", "0.502", "0.389", "0.808", "0.525", "0.471", "0.636"],
        ["Random Forest (472 trees)", "0.496", "0.386", "0.813", "0.524", "0.473", "0.638"],
        ["XGBoost (Validation Selection)", "0.527", "0.400", "0.782", "0.529", "0.482", "0.645"],
        ["XGBoost (Held-out Test Period)", "0.530", "0.363", "0.771", "0.493", "0.431", "0.655"]
    ]

    for r_idx, row in enumerate(data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            cell.margin_left = cell.margin_right = Inches(0.03)
            cell.fill.solid()
            if r_idx == 0:
                cell.fill.fore_color.rgb = NAVY_PRIMARY
            elif r_idx == 6:
                cell.fill.fore_color.rgb = HIGHLIGHT_ROW
            elif r_idx % 2 == 1:
                cell.fill.fore_color.rgb = ROW_ALT
            else:
                cell.fill.fore_color.rgb = WHITE

            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.CENTER
            color = WHITE if r_idx == 0 else (NAVY_PRIMARY if r_idx == 6 else TEXT_INK)
            bold = (r_idx == 0 or r_idx >= 5 or c_idx == 0)
            add_text_run(p, val, font="Arial", size=8.2, bold=bold, color=color)

    # Right: Framed confusion_white.png (natural aspect ratio: 5.5 x 4.4 = 1.25)
    conf_img = ASSETS / "confusion_white.png"
    if conf_img.exists():
        # Width: 3.35, Height: 2.25
        slide.shapes.add_picture(str(conf_img), Inches(6.15), Inches(1.20), Inches(3.45), Inches(2.25))

    # Bottom Callout Cards: 3 Key Insights
    insights = [
        ("Accuracy vs Recall Tradeoff", "Raw accuracy is 53.0% because the decision threshold (0.367) was deliberately tuned on validation to capture 77.1% recall. Guessing 'unresolved' gives 65.9% accuracy with zero real utility (0% recall).", SKY_ACCENT),
        ("PR-AUC & ROC-AUC Lift", "In an imbalanced test setting (29.7% positive rate), PR-AUC of 0.431 represents a +45% lift over the no-skill baseline, while ROC-AUC (0.655) confirms stable question discrimination.", TEAL_ACCENT),
        ("Two-Stage Triage Accuracy", "Initial triage on answerability achieves 82.3% accuracy on target_answered_7d and 84.2% on confident predictions, guiding moderation triage effectively.", ORANGE_ACCENT)
    ]

    card_w = Inches(2.95)
    card_h = Inches(1.65)
    for i, (hd, body, border_c) in enumerate(insights):
        left_pos = Inches(0.40 + i * 3.12)
        add_flat_card(slide, left_pos, Inches(3.58), card_w, card_h, border_color=border_c)

        tb = slide.shapes.add_textbox(left_pos + Inches(0.12), Inches(3.66), card_w - Inches(0.24), card_h - Inches(0.16))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p0 = tf.paragraphs[0]
        p0.space_after = Pt(4)
        add_text_run(p0, hd, font="Arial", size=9, bold=True, color=border_c)

        p1 = tf.add_paragraph()
        add_text_run(p1, body, font="Arial", size=8.5, bold=False, color=TEXT_INK)


def build_slide_3_shap(prs, slide_num=3):
    """Slide 3: Model Interpretability & TreeSHAP Analysis."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "Model Interpretability: Feature Drivers & TreeSHAP Analysis",
               "MEMBER 5: EXPLAINABILITY & INSIGHTS", slide_num)

    # Left: Framed shap_bar_white.png (aspect ratio: 7.2 / 4.4 = 1.636)
    shap_img = ASSETS / "shap_bar_white.png"
    if shap_img.exists():
        # Width: 5.10 in, Height: 3.12 in
        slide.shapes.add_picture(str(shap_img), Inches(0.40), Inches(1.20), Inches(5.10), Inches(3.12))

    # Bottom-left: Summary takeaway card
    add_flat_card(slide, Inches(0.40), Inches(4.42), Inches(5.10), Inches(0.80), border_color=SKY_ACCENT)
    tb_b = slide.shapes.add_textbox(Inches(0.52), Inches(4.48), Inches(4.86), Inches(0.68))
    tf_b = tb_b.text_frame
    tf_b.word_wrap = True
    p_b0 = tf_b.paragraphs[0]
    add_text_run(p_b0, "Key Explainability Takeaway: ", font="Arial", size=8.8, bold=True, color=SKY_ACCENT)
    add_text_run(p_b0, "Platform congestion (tag volume) and asker tenure are 2x more predictive than question length. Content quality (code ratio) acts as a vital positive signal.",
                 font="Arial", size=8.5, color=TEXT_INK)

    # Right: Insights card
    add_flat_card(slide, Inches(5.65), Inches(1.20), Inches(3.95), Inches(4.02), border_color=PANEL_BORDER)
    tb = slide.shapes.add_textbox(Inches(5.78), Inches(1.28), Inches(3.70), Inches(3.85))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    drivers = [
        ("Tag Volume Dilution (0.176)", "Posting in high-volume tags exhibits the strongest negative impact on resolution. Heavy tag churn saturates community bandwidth, causing questions to get buried rapidly."),
        ("Community Trust & Tenure (0.125)", "Established askers have significantly higher resolution rates. Brand-new accounts (0 days tenure) suffer the steepest penalty due to unfamiliarity with platform conventions."),
        ("Code Block Sweet Spot (0.100 & 0.092)", "Questions containing code blocks achieve substantially higher acceptance. However, SHAP dependence reveals an inverted U-shape: questions that are purely raw code dumps without explanation suffer lower resolution."),
        ("Semantic Text Embeddings (0.075)", "Title SVD dimensions capture actionable error signatures and frameworks vs vague open-ended conceptual queries."),
        ("Methodological Soundness", "TreeSHAP feature rankings align with logistic regression coefficients, confirming tree models captured true structural relationships rather than spurious noise.")
    ]

    for i, (hd, body) in enumerate(drivers):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(6)
        add_text_run(p, "• ", font="Arial", size=8.8, bold=True, color=NAVY_PRIMARY)
        add_text_run(p, f"{hd}: ", font="Arial", size=8.8, bold=True, color=NAVY_PRIMARY)
        add_text_run(p, body, font="Arial", size=8.2, bold=False, color=TEXT_INK)


def build_slide_4_drift(prs, slide_num=4):
    """Slide 4: Temporal Robustness & ChatGPT Impact (Rolling-Origin Windows)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "Temporal Robustness: 5-Year Rolling Windows & ChatGPT Impact",
               "MEMBER 5: MODEL DRIFT & GENERALIZATION", slide_num)

    # Left: Framed rolling_white.png (aspect ratio: 9.6 / 4.3 = 2.23)
    rolling_img = ASSETS / "rolling_white.png"
    if rolling_img.exists():
        # Width: 5.20 in, Height: 2.33 in
        slide.shapes.add_picture(str(rolling_img), Inches(0.40), Inches(1.20), Inches(5.20), Inches(2.33))

    # Bottom-left: Comparison card (Pre vs Post ChatGPT)
    add_flat_card(slide, Inches(0.40), Inches(3.62), Inches(5.20), Inches(1.60), border_color=TEAL_ACCENT)
    tb_c = slide.shapes.add_textbox(Inches(0.52), Inches(3.68), Inches(4.96), Inches(1.48))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True

    p0 = tf_c.paragraphs[0]
    p0.space_after = Pt(3)
    add_text_run(p0, "Pre-ChatGPT vs Post-ChatGPT Regime Shift Comparison", font="Arial", size=9, bold=True, color=TEAL_ACCENT)

    items_c = [
        ("Base Resolution Rate: ", "Fell from 44.0% (2021) down to 23.3% (2026), reflecting community drain to AI."),
        ("ROC-AUC Discrimination: ", "Remained rock-solid at 0.63–0.67 across all 11 windows (ranking ability invariant)."),
        ("PR-AUC Lift: ", "Consistently maintained a positive margin over the base rate (zero model collapse).")
    ]
    for tag_l, desc in items_c:
        p = tf_c.add_paragraph()
        p.space_after = Pt(2)
        add_text_run(p, "• ", font="Arial", size=8.5, bold=True, color=TEAL_ACCENT)
        add_text_run(p, tag_l, font="Arial", size=8.5, bold=True, color=NAVY_PRIMARY)
        add_text_run(p, desc, font="Arial", size=8.2, color=TEXT_INK)

    # Right: Insights card
    add_flat_card(slide, Inches(5.75), Inches(1.20), Inches(3.85), Inches(4.02), border_color=PANEL_BORDER)
    tb = slide.shapes.add_textbox(Inches(5.88), Inches(1.28), Inches(3.60), Inches(3.85))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    findings = [
        ("Platform-Wide Base Rate Collapse", "Prior to ChatGPT (Nov 2022), 44.0% of questions were resolved within 7 days. Post-launch, the resolution rate dropped to 23.3%–32.5% as developers offloaded simple queries to AI assistants."),
        ("Invariance of Ranking Ability", "Despite the massive volume drop and demographic shift, model ROC-AUC remained remarkably invariant (0.63–0.65 pre-ChatGPT vs 0.64–0.67 post-ChatGPT). The model reliably discriminates question quality across regimes."),
        ("Persistent PR-AUC Lift", "PR-AUC consistently maintained a positive margin over the drifting base rate across all 11 half-year rolling windows from 2021-H1 to 2026-H1, showing zero collapse."),
        ("Rigorous Rolling-Origin Protocol", "Each half-year test window was evaluated strictly against a model trained only on preceding historical data, guaranteeing zero temporal leakage."),
        ("Operational Deployment Strategy", "Feature relationships remain stable, but the base rate shifted. Re-calibrating the decision threshold quarterly preserves optimal precision-recall triage.")
    ]

    for i, (hd, body) in enumerate(findings):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(6)
        add_text_run(p, "• ", font="Arial", size=8.8, bold=True, color=TEAL_ACCENT)
        add_text_run(p, f"{hd}: ", font="Arial", size=8.8, bold=True, color=TEAL_ACCENT)
        add_text_run(p, body, font="Arial", size=8.2, bold=False, color=TEXT_INK)


def build_slide_5_errors(prs, slide_num=5):
    """Slide 5: Error Diagnostics & Business Triage Recommendations."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "Error Diagnostics & Business Triage Recommendations",
               "MEMBER 5: ERROR ANALYSIS & ACTIONABILITY", slide_num)

    # Left: Framed error_analysis_white.png (aspect ratio: 9.6 / 4.3 = 2.23)
    err_img = ASSETS / "error_analysis_white.png"
    if err_img.exists():
        # Width: 5.20 in, Height: 2.33 in
        slide.shapes.add_picture(str(err_img), Inches(0.40), Inches(1.20), Inches(5.20), Inches(2.33))

    # Bottom-left: Triage lift card
    add_flat_card(slide, Inches(0.40), Inches(3.62), Inches(5.20), Inches(1.60), border_color=ORANGE_ACCENT)
    tb_e = slide.shapes.add_textbox(Inches(0.52), Inches(3.68), Inches(4.96), Inches(1.48))
    tf_e = tb_e.text_frame
    tf_e.word_wrap = True

    p0 = tf_e.paragraphs[0]
    p0.space_after = Pt(3)
    add_text_run(p0, "Operational Moderation Triage Lift (1.21x Over Random)", font="Arial", size=9, bold=True, color=ORANGE_ACCENT)

    items_e = [
        ("Capture Rate: ", "Flagging the lowest 20% predicted scores captures 24.15% of all unresolved questions."),
        ("Queue Efficiency: ", "In a moderation queue of 10,000 weekly posts, this surfaces 415 additional at-risk questions."),
        ("Intervention Target: ", "Prioritizing day-0 askers and questions lacking code prevents community abandonment.")
    ]
    for tag_l, desc in items_e:
        p = tf_e.add_paragraph()
        p.space_after = Pt(2)
        add_text_run(p, "• ", font="Arial", size=8.5, bold=True, color=ORANGE_ACCENT)
        add_text_run(p, tag_l, font="Arial", size=8.5, bold=True, color=NAVY_PRIMARY)
        add_text_run(p, desc, font="Arial", size=8.2, color=TEXT_INK)

    # Right: Insights card
    add_flat_card(slide, Inches(5.75), Inches(1.20), Inches(3.85), Inches(4.02), border_color=PANEL_BORDER)
    tb = slide.shapes.add_textbox(Inches(5.88), Inches(1.28), Inches(3.60), Inches(3.85))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    points = [
        ("False Positive Diagnosis (67% Answered)", "In 10 of 15 top false positives, high-quality answers WERE received within 7 days, but the asker never clicked 'accept'. The model correctly identified answerable questions; the failure was user abandonment."),
        ("False Negative Diagnosis (53% Zero-Day Accounts)", "8 of 15 top false negatives came from brand-new users who posted well-structured questions with clear stack traces and received rapid expert answers despite account youth."),
        ("Business Triage Lift (1.21x Over Random)", "Flagging the bottom 20% predicted resolution scores captures 24.15% of all unresolved questions. For a moderation queue of 10,000 weekly posts, this surfaces 415 additional at-risk questions."),
        ("Actionable Platform Interventions", "1) Prompt askers to add code snippets if code_ratio == 0; 2) Provide interactive guidance for day-0 askers; 3) Send gentle automated reminders to askers to mark accepted answers.")
    ]

    for i, (hd, body) in enumerate(points):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(7)
        add_text_run(p, "• ", font="Arial", size=8.8, bold=True, color=ORANGE_ACCENT)
        add_text_run(p, f"{hd}: ", font="Arial", size=8.8, bold=True, color=ORANGE_ACCENT)
        add_text_run(p, body, font="Arial", size=8.2, bold=False, color=TEXT_INK)


def build_slide_6_timeseries(prs, slide_num=6):
    """Slide 6: Advanced Time Series Demand Forecasting (Unit 3 Requirement)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "Advanced Time Series Forecasting: AI Shift & 2027 Projections",
               "MEMBER 5: ADVANCED ANALYTICS (UNIT 3)", slide_num)

    # Left: Framed timeseries_forecast_white.png (aspect ratio: 11.5 / 7.2 = 1.60)
    ts_img = ASSETS / "timeseries_forecast_white.png"
    if ts_img.exists():
        # Width: 5.25 in, Height: 3.28 in
        slide.shapes.add_picture(str(ts_img), Inches(0.40), Inches(1.20), Inches(5.25), Inches(3.28))

    # Bottom-left: High Accuracy Badge Card
    add_flat_card(slide, Inches(0.40), Inches(4.55), Inches(5.25), Inches(0.67), border_color=SKY_ACCENT)
    tb_b = slide.shapes.add_textbox(Inches(0.52), Inches(4.59), Inches(5.00), Inches(0.58))
    tf_b = tb_b.text_frame
    tf_b.word_wrap = True
    p0 = tf_b.paragraphs[0]
    add_text_run(p0, "Curriculum Unit 3 Requirement Met: ", font="Arial", size=8.8, bold=True, color=SKY_ACCENT)
    add_text_run(p0, "Demanded >80% accuracy; achieved 91.72% Site-Wide (R²=0.976, MAPE=8.28%) and 87.65% on Python across 87 test weeks.",
                 font="Arial", size=8.2, color=TEXT_INK)

    # Right: Insights card
    add_flat_card(slide, Inches(5.80), Inches(1.20), Inches(3.80), Inches(4.02), border_color=PANEL_BORDER)
    tb = slide.shapes.add_textbox(Inches(5.92), Inches(1.28), Inches(3.55), Inches(3.85))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    points = [
        ("High-Accuracy Time Series Model", "Holt's Damped Trend Exponential Smoothing achieves 91.72% Forecast Accuracy (MAPE 8.28%, R² = 0.976) on Site-Wide questions, and 87.65% Accuracy on the Python ecosystem over 87 test weeks."),
        ("Post-ChatGPT Structural Collapse", "Prior to Nov 2022, Stack Overflow generated over 35,000 questions weekly. Following ChatGPT, site volume experienced a permanent 92% structural drop down to ~1,400 questions/week."),
        ("Ecosystem Resilience Divergence", "General programming tags (Python, Java, JS) stabilized at a low baseline, whereas AI tooling (openai-api) emerged post-2023 with growing relative share and high volatility."),
        ("2027 Forward Projections", "Multi-step 26-week forecast through 2027 confirms platform activity will not rebound to pre-AI levels; communities must pivot toward high-complexity niche questions."),
        ("Curriculum Alignment", "Directly fulfills the Unit 3 Advanced Analytics syllabus requirement, supplementing our classification models with continuous demand forecasting exceeding the 80% accuracy threshold.")
    ]

    for i, (hd, body) in enumerate(points):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(6)
        add_text_run(p, "• ", font="Arial", size=8.8, bold=True, color=NAVY_PRIMARY)
        add_text_run(p, f"{hd}: ", font="Arial", size=8.8, bold=True, color=NAVY_PRIMARY)
        add_text_run(p, body, font="Arial", size=8.2, bold=False, color=TEXT_INK)


def build_slide_title(prs):
    """Title slide for Member 5's dedicated deck."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background_white(slide)

    # Blue top accent bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.40), Inches(0.50), Inches(9.20), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY_PRIMARY
    bar.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.40), Inches(1.20), Inches(9.20), Inches(3.20))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.space_after = Pt(4)
    add_text_run(p0, "23CSE452: BUSINESS ANALYTICS  |  REVIEW 1", font="Arial", size=10, bold=True, color=SKY_ACCENT)

    p1 = tf.add_paragraph()
    p1.space_after = Pt(8)
    add_text_run(p1, "Stack Overflow in the AI Era", font="Arial", size=26, bold=True, color=NAVY_HEADER)

    p2 = tf.add_paragraph()
    p2.space_after = Pt(16)
    add_text_run(p2, "Member 5: Predictive Modeling, Advanced Time Series & Evaluation", font="Arial", size=15, bold=True, color=TEXT_INK)

    p3 = tf.add_paragraph()
    p3.space_after = Pt(4)
    add_text_run(p3, "Presented by: ", font="Arial", size=11, bold=True, color=NAVY_PRIMARY)
    add_text_run(p3, "Adhikkesh S K  (CB.SC.U4CSE23101)", font="Arial", size=11, bold=False, color=TEXT_INK)

    p4 = tf.add_paragraph()
    add_text_run(p4, "Team 7 Members: ", font="Arial", size=9.5, bold=True, color=TEXT_MUTED)
    add_text_run(p4, "Adhikkesh S K  •  Abhinav Gopalakrishnan  •  Rishiikesh  •  Akshay Krishna  •  Nishanth Konchada", font="Arial", size=9.5, color=TEXT_MUTED)


def build_slide_contributions(prs, slide_num=7):
    """Slide 7: Individual Contributions Table."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "Individual Contributions & Project Ownership",
               "MEMBER 5: TEAM ALIGNMENT & DELIVERABLES", slide_num)

    t_shape = slide.shapes.add_table(6, 4, Inches(0.40), Inches(1.35), Inches(9.20), Inches(3.50))
    table = t_shape.table
    table.columns[0].width = Inches(2.20)
    table.columns[1].width = Inches(2.30)
    table.columns[2].width = Inches(2.35)
    table.columns[3].width = Inches(2.35)

    data = [
        ["TEAM MEMBER", "TASK AREA 1", "TASK AREA 2", "TASK AREA 3"],
        ["Member 1 (Abhinav)", "Data Collection & API", "309k Questions Pipeline", "Weekly Tag Counts"],
        ["Member 2 (Rishiikesh)", "Enrichment & Cleaning", "7-Day Outcome Labels", "Sampling Robustness"],
        ["Member 3 (Akshay)", "EDA & Problem Scoping", "Volume Shift Visuals", "Initial Findings"],
        ["Member 4 (Nishanth)", "Feature Engineering", "Temporal Train/Val Split", "Baseline LogReg Model"],
        ["Member 5 (Adhikkesh)\n[Current Speaker]", "Predictive Modeling\n(XGBoost, RF, LogReg)", "Model Evaluation & SHAP\n(Rolling Drift, Error Audit)", "Time Series Demand\n(Holt's Damped, >91% Acc)"]
    ]

    for r_idx, row in enumerate(data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.margin_top = cell.margin_bottom = Inches(0.04)
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.fill.solid()
            if r_idx == 0:
                cell.fill.fore_color.rgb = NAVY_PRIMARY
            elif r_idx == 5:
                cell.fill.fore_color.rgb = HIGHLIGHT_ROW
            elif r_idx % 2 == 1:
                cell.fill.fore_color.rgb = ROW_ALT
            else:
                cell.fill.fore_color.rgb = WHITE

            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.CENTER
            color = WHITE if r_idx == 0 else (NAVY_PRIMARY if r_idx == 5 else TEXT_INK)
            bold = (r_idx == 0 or r_idx == 5 or c_idx == 0)
            add_text_run(p, val, font="Arial", size=8.5, bold=bold, color=color)


def build_slide_review2_plan(prs, slide_num=8):
    """Slide 8: Review 2 Roadmap."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "Review 2 Plan: Advanced Analytics & Platform Evolution",
               "MEMBER 5: FUTURE SCOPE & REVIEW 2 ROADMAP", slide_num)

    cards = [
        ("Option 1: Deep Forecasting", [
            "Neural Time Series: Implement deep recurrent / transformer architectures (DeepAR / N-BEATS).",
            "Tag-Level Divergence: Forecast high-growth AI tags vs plateauing traditional languages.",
            "Capacity Planning: Estimate human moderator staffing requirements through 2028."
        ], SKY_ACCENT),
        ("Option 2: Text Mining & NLP", [
            "LLM Query Clustering: Semantic topic modeling (BERTopic) on post-ChatGPT questions.",
            "Question Complexity Shift: Analyze code-to-text ratios and lexical density across AI era.",
            "Developer Intent: Identify questions developers still ask humans vs AI tools."
        ], TEAL_ACCENT),
        ("Option 3: Calibrated Triage", [
            "Platt Scaling & Isotonic Calibration: Align predicted probabilities to empirical rates.",
            "Automated Interventions: Live routing to human experts for questions with <20% resolution score.",
            "End-to-End Pipeline: Deploy model artifact to Kaggle / Hugging Face model hub."
        ], ORANGE_ACCENT),
    ]

    card_w = Inches(2.95)
    card_h = Inches(3.85)
    for i, (head, items, color) in enumerate(cards):
        left = Inches(0.40 + i * 3.12)
        add_flat_card(slide, left, Inches(1.35), card_w, card_h, border_color=color)

        tb = slide.shapes.add_textbox(left + Inches(0.15), Inches(1.45), card_w - Inches(0.30), card_h - Inches(0.20))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p0 = tf.paragraphs[0]
        p0.space_after = Pt(8)
        add_text_run(p0, head, font="Arial", size=11, bold=True, color=color)

        for item in items:
            p = tf.add_paragraph()
            p.space_after = Pt(8)
            add_text_run(p, "• ", font="Arial", size=9, bold=True, color=color)
            add_text_run(p, item, font="Arial", size=8.5, bold=False, color=TEXT_INK)


def build_slide_thankyou(prs, slide_num=9):
    """Thank you slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background_white(slide)

    tb = slide.shapes.add_textbox(Inches(1.00), Inches(1.80), Inches(8.00), Inches(2.50))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.alignment = PP_ALIGN.CENTER
    p0.space_after = Pt(8)
    add_text_run(p0, "Thank you!", font="Arial", size=32, bold=True, color=NAVY_HEADER)

    p1 = tf.add_paragraph()
    p1.alignment = PP_ALIGN.CENTER
    p1.space_after = Pt(16)
    add_text_run(p1, "Questions & Discussion", font="Arial", size=16, bold=True, color=SKY_ACCENT)

    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    add_text_run(p2, "Adhikkesh S K (CB.SC.U4CSE23101)  •  Member 5: Predictive Modeling & Advanced Time Series", font="Arial", size=10, bold=True, color=TEXT_INK)


# -----------------------------------------------------------------------------
# MAIN COMPILERS
# -----------------------------------------------------------------------------

def build_all_white_decks():
    print("Building Crisp White Presentation Decks...")

    # 1. Dedicated Member 5 ONLY Deck (6 Core Slides)
    prs_only = pptx.Presentation()
    prs_only.slide_width = Inches(10.0)
    prs_only.slide_height = Inches(5.625)

    build_slide_1_model_dev(prs_only, 1)
    build_slide_2_evaluation(prs_only, 2)
    build_slide_3_shap(prs_only, 3)
    build_slide_4_drift(prs_only, 4)
    build_slide_5_errors(prs_only, 5)
    build_slide_6_timeseries(prs_only, 6)

    prs_only.save(OUT_M5_ONLY)
    print(f"✓ Saved Member 5 ONLY deck (6 slides) to: {OUT_M5_ONLY}")

    # 2. Complete Member 5 White Presentation Deck (10 Slides)
    prs_full = pptx.Presentation()
    prs_full.slide_width = Inches(10.0)
    prs_full.slide_height = Inches(5.625)

    build_slide_title(prs_full)
    build_slide_1_model_dev(prs_full, 2)
    build_slide_2_evaluation(prs_full, 3)
    build_slide_3_shap(prs_full, 4)
    build_slide_4_drift(prs_full, 5)
    build_slide_5_errors(prs_full, 6)
    build_slide_6_timeseries(prs_full, 7)
    build_slide_contributions(prs_full, 8)
    build_slide_review2_plan(prs_full, 9)
    build_slide_thankyou(prs_full, 10)

    prs_full.save(OUT_M5_FULL)
    print(f"✓ Saved complete Member 5 White presentation (10 slides) to: {OUT_M5_FULL}")


if __name__ == "__main__":
    build_all_white_decks()
