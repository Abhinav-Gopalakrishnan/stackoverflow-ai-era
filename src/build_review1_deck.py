"""Generate the updated, professional presentations for Review 1.

Includes:
1. BA Final Project - Review 1_cpy.pptx (Complete 19-slide team deck)
2. Member_5_Review_1_Slides_Dark.pptx (Member 5 slides 10-19 for direct Google Slides import)
3. Adhikkesh_Member_5_Only_Slides.pptx (Specifically the 5 dedicated Member 5 model & evaluation slides)
"""

from pathlib import Path
import pptx
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path("/home/adhikkesh/adhikkesh/SEM7/BA/stackoverflow-ai-era")
SRC_PPTX = ROOT / "BA Final Project - Review 1_cpy_backup.pptx"
OUT_FULL_PPTX = ROOT / "BA Final Project - Review 1_cpy.pptx"
OUT_M5_DECK = ROOT / "Member_5_Review_1_Slides_Dark.pptx"
OUT_M5_ONLY = ROOT / "Adhikkesh_Member_5_Only_Slides_Dark.pptx"
ASSETS = ROOT / "reports" / "review1" / "deck_assets"

# Presentation Color Palette
DARK_BG = RGBColor(0x1A, 0x1D, 0x24)        # Deep slate background
DARK_CARD = RGBColor(0x13, 0x18, 0x22)      # Card background
DARK_ROW = RGBColor(0x1E, 0x24, 0x30)       # Alternating row background
MINT = RGBColor(0x1D, 0xE9, 0xB6)           # Neon mint accent (#1DE9B6)
CYAN = RGBColor(0x00, 0xBC, 0xD4)           # Secondary cyan
ORANGE = RGBColor(0xFF, 0x98, 0x00)         # Badge orange (#FF9800)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)          # Pure white
LIGHT = RGBColor(0xCF, 0xD8, 0xDC)          # Light slate text
MUTED = RGBColor(0x90, 0xA4, 0xAE)          # Muted subtext
HIGHLIGHT_ROW = RGBColor(0x1B, 0x38, 0x35)  # Teal highlight for selected model
DEEP_SLATE = RGBColor(0x13, 0x18, 0x22)     # Dark text for Slide 19 sky background


def add_text_run(paragraph, text, font="Nunito Sans", size=10, bold=False, color=WHITE):
    """Helper to add a formatted text run."""
    run = paragraph.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return run


def clear_placeholder_shapes(slide):
    """Remove default placeholder shapes so layout background graphics remain."""
    for sh in list(slide.shapes):
        sp = sh._element
        sp.getparent().remove(sp)


def add_slide_header(slide, title_text, category_text="MEMBER 5: PREDICTIVE MODELING & EVALUATION"):
    """Add standardized top header with category kicker and title."""
    header_box = slide.shapes.add_textbox(Inches(0.35), Inches(0.22), Inches(9.20), Inches(1.10))
    tf = header_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    # Category kicker
    p_cat = tf.paragraphs[0]
    p_cat.space_after = Pt(2)
    add_text_run(p_cat, category_text.upper(), font="Poppins", size=8.5, bold=True, color=MINT)

    # Main Title
    p_title = tf.add_paragraph()
    p_title.space_after = Pt(0)
    add_text_run(p_title, title_text, font="Poppins", size=20, bold=True, color=WHITE)

    # Accent underline
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.35), Inches(1.22), Inches(1.40), Inches(0.04))
    line.fill.solid()
    line.fill.fore_color.rgb = MINT
    line.line.fill.background()


def populate_slide_10(s10):
    """Slide 10: Predictive Model Development."""
    # Remove old placeholder text box
    for sh in list(s10.shapes):
        if sh.name == "Google Shape;708;p69":
            sp = sh._element
            sp.getparent().remove(sp)

    # Text card on left
    card_t = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.30), Inches(1.40), Inches(4.55), Inches(3.85))
    card_t.fill.solid()
    card_t.fill.fore_color.rgb = DARK_CARD
    card_t.line.color.rgb = DARK_ROW
    card_t.line.width = Pt(1)

    tb10 = s10.shapes.add_textbox(Inches(0.45), Inches(1.50), Inches(4.25), Inches(3.65))
    tf10 = tb10.text_frame
    tf10.word_wrap = True
    tf10.margin_left = tf10.margin_top = tf10.margin_right = tf10.margin_bottom = 0

    sections = [
        ("Prediction Task: ", "Binary Classification — Predicting whether a newly posted question receives an accepted answer within 7 days (target_resolved_7d)."),
        ("Candidate Models: ", "Majority Class Baseline, Regularized Logistic Regression (+Text SVD), Random Forest Classifier (472 trees), and XGBoost Classifier."),
        ("Strict Chronological Split: ", "Train: 2019–2024 (248k, 85%) | Validation: Jan–Jun 2025 (28k, 10%) | Held-out Test: Jul 2025–Jul 2026 (16.7k, 6%, scored once)."),
        ("Leakage Prevention: ", "Purged time-series rolling cross-validation with a strict 7-day blackout gap to prevent target outcome leakage across split boundaries."),
        ("Optimal Tuning: ", "XGBoost chosen on validation PR-AUC (0.482 vs 0.473 RF vs 0.471 LogReg). Tuned with lr=0.029, depth=5, 628 trees via early stopping, threshold=0.367.")
    ]

    for i, (head, body) in enumerate(sections):
        p = tf10.paragraphs[0] if i == 0 else tf10.add_paragraph()
        p.space_after = Pt(7)
        add_text_run(p, "• ", font="Nunito Sans", size=9.5, bold=True, color=MINT)
        add_text_run(p, head, font="Nunito Sans", size=9.5, bold=True, color=MINT)
        add_text_run(p, body, font="Nunito Sans", size=9, bold=False, color=WHITE)

    # Visual on right: split_white.png
    split_img = ASSETS / "split_white.png"
    if split_img.exists():
        card_img = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.00), Inches(1.40), Inches(4.70), Inches(3.85))
        card_img.fill.solid()
        card_img.fill.fore_color.rgb = WHITE
        card_img.line.color.rgb = MINT
        card_img.line.width = Pt(1.5)
        # Position image inside card with padding
        s10.shapes.add_picture(str(split_img), Inches(5.08), Inches(1.70), Inches(4.54), Inches(3.25))

        # Card caption
        cap_box = s10.shapes.add_textbox(Inches(5.05), Inches(1.45), Inches(4.60), Inches(0.30))
        p_cap = cap_box.text_frame.paragraphs[0]
        p_cap.alignment = PP_ALIGN.CENTER
        add_text_run(p_cap, "Chronological Dataset Split & Resolution Rate Trend", font="Poppins", size=9, bold=True, color=DEEP_SLATE)


def populate_slide_11(s11):
    """Slide 11: Model Evaluation and Result Interpretation (Performance & Comparison)."""
    # Remove old placeholder text box
    for sh in list(s11.shapes):
        if sh.name == "Google Shape;720;p70":
            sp = sh._element
            sp.getparent().remove(sp)

    # Benchmark Comparison Table
    t_shape = s11.shapes.add_table(7, 7, Inches(0.25), Inches(1.35), Inches(5.95), Inches(2.10))
    table = t_shape.table
    table.columns[0].width = Inches(1.75)
    table.columns[1].width = Inches(0.65)
    table.columns[2].width = Inches(0.65)
    table.columns[3].width = Inches(0.65)
    table.columns[4].width = Inches(0.65)
    table.columns[5].width = Inches(0.78)
    table.columns[6].width = Inches(0.82)

    table_data = [
        ["Model (Validation)", "Accuracy", "Precision", "Recall", "F1 Score", "PR-AUC", "ROC-AUC"],
        ["Majority Class Baseline", "0.659", "0.000", "0.000", "0.000", "0.341", "0.500"],
        ["Baseline Logistic Regression", "0.412", "0.357", "0.909", "0.513", "0.394", "0.579"],
        ["Logistic Regression (+Text SVD)", "0.502", "0.389", "0.808", "0.525", "0.471", "0.636"],
        ["Random Forest (472 trees)", "0.496", "0.386", "0.813", "0.524", "0.473", "0.638"],
        ["XGBoost (Validation Selection)", "0.527", "0.400", "0.782", "0.529", "0.482", "0.645"],
        ["XGBoost (Held-out Test Period)", "0.530", "0.363", "0.771", "0.493", "0.431", "0.655"]
    ]

    for r in table.rows:
        r.height = Inches(0.28)

    for cell in table.iter_cells():
        cell.margin_top = Inches(0.02)
        cell.margin_bottom = Inches(0.02)
        cell.margin_left = Inches(0.04)
        cell.margin_right = Inches(0.04)

    for r_idx, row in enumerate(table_data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = ""
            cell.fill.solid()
            if r_idx == 0:
                cell.fill.fore_color.rgb = DARK_CARD
            elif r_idx == 6:
                cell.fill.fore_color.rgb = HIGHLIGHT_ROW
            elif r_idx % 2 == 1:
                cell.fill.fore_color.rgb = DARK_ROW
            else:
                cell.fill.fore_color.rgb = DARK_CARD

            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.CENTER
            color = MINT if (r_idx == 0 or r_idx == 6) else (WHITE if r_idx == 5 else LIGHT)
            add_text_run(p, val, font="Nunito Sans", size=8.5 if (r_idx == 6 and c_idx == 0) else 9, bold=(r_idx == 0 or r_idx >= 5), color=color)

    # Confusion matrix visual on right
    conf_img = ASSETS / "confusion_white.png"
    if conf_img.exists():
        card_c = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.35), Inches(1.35), Inches(3.35), Inches(2.20))
        card_c.fill.solid()
        card_c.fill.fore_color.rgb = WHITE
        card_c.line.color.rgb = MINT
        card_c.line.width = Pt(1.5)
        s11.shapes.add_picture(str(conf_img), Inches(6.40), Inches(1.40), Inches(3.25), Inches(2.10))

    # Bottom Callout Cards: 3 Key Evaluation Takeaways
    bottom_cards = [
        ("Accuracy vs Recall Tradeoff", "Raw accuracy is 53.0% because the decision threshold (0.367) was deliberately tuned to prioritize high recall (77.1%). Always guessing unresolved achieves 65.9% accuracy with zero utility (0% recall).", MINT),
        ("PR-AUC & ROC Significance", "In an imbalanced setting (30% test positive rate), PR-AUC of 0.431 represents a +45% lift over the 0.297 no-skill baseline, while ROC-AUC (0.655) confirms stable question discrimination.", CYAN),
        ("Classification Metric Integrity", "Standard regression metrics (R², MAE, MSE, RMSE) do not apply to this binary outcome task. Calibration and ranked thresholding drive real platform utility.", ORANGE)
    ]

    card_w = Inches(3.05)
    card_h = Inches(1.60)
    for i, (hd, body, border_color) in enumerate(bottom_cards):
        left_pos = Inches(0.25 + i * 3.25)
        card = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, Inches(3.70), card_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = DARK_CARD
        card.line.color.rgb = border_color
        card.line.width = Pt(1)

        tb = s11.shapes.add_textbox(left_pos + Inches(0.12), Inches(3.78), card_w - Inches(0.24), card_h - Inches(0.16))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p0 = tf.paragraphs[0]
        p0.space_after = Pt(4)
        add_text_run(p0, hd, font="Poppins", size=9, bold=True, color=border_color)

        p1 = tf.add_paragraph()
        add_text_run(p1, body, font="Nunito Sans", size=8.5, bold=False, color=WHITE)


def populate_slide_12_shap(s12):
    """Slide 12 (NEW): Feature Importance & Interpretability (SHAP Analysis)."""
    clear_placeholder_shapes(s12)
    add_slide_header(s12, "Model Interpretability: Feature Drivers & SHAP Analysis", "MEMBER 5: EXPLAINABILITY & INSIGHTS")

    # Chart container on left
    card_img = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.35), Inches(1.35), Inches(4.85), Inches(3.95))
    card_img.fill.solid()
    card_img.fill.fore_color.rgb = WHITE
    card_img.line.color.rgb = MINT
    card_img.line.width = Pt(1.5)

    shap_img = ASSETS / "shap_bar_white.png"
    if shap_img.exists():
        s12.shapes.add_picture(str(shap_img), Inches(0.42), Inches(1.42), Inches(4.71), Inches(3.81))

    # Insights card on right
    card_txt = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.35), Inches(1.35), Inches(4.35), Inches(3.95))
    card_txt.fill.solid()
    card_txt.fill.fore_color.rgb = DARK_CARD
    card_txt.line.color.rgb = DARK_ROW
    card_txt.line.width = Pt(1)

    tb = s12.shapes.add_textbox(Inches(5.50), Inches(1.45), Inches(4.05), Inches(3.75))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    drivers = [
        ("Tag Activity Dilution (lagged_tag_volume, 0.176): ", "Posting in high-volume tags exhibits the strongest negative effect on resolution. Heavy tag churn saturates community attention, causing questions to get buried rapidly."),
        ("Community Trust (account_age_days, 0.125): ", "Established askers have significantly higher resolution rates. Brand-new accounts (0 days old) suffer the steepest penalty due to unfamiliarity with platform norms."),
        ("Effort & Code Sweet Spot (code_ratio, 0.100): ", "Questions with code blocks achieve substantially higher acceptance rates. However, SHAP dependence reveals an inverted U-shape: questions that are entirely raw code without explanation suffer lower resolution."),
        ("Semantic Embeddings (title_tfidf_svd): ", "Title text SVD dimensions capture actionable error signatures and frameworks vs vague open-ended conceptual queries."),
        ("Methodological Soundness: ", "SHAP feature rankings align with logistic regression coefficients, confirming tree models captured true structural patterns rather than spurious noise.")
    ]

    for i, (hd, body) in enumerate(drivers):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(6)
        add_text_run(p, "• ", font="Nunito Sans", size=9, bold=True, color=MINT)
        add_text_run(p, hd, font="Nunito Sans", size=9, bold=True, color=MINT)
        add_text_run(p, body, font="Nunito Sans", size=8.5, bold=False, color=WHITE)


def populate_slide_13_drift(s13):
    """Slide 13 (NEW): Temporal Stability & Pre/Post ChatGPT Shift (Rolling-Origin Windows)."""
    clear_placeholder_shapes(s13)
    add_slide_header(s13, "Temporal Robustness: 5-Year Rolling Windows & ChatGPT Impact", "MEMBER 5: MODEL DRIFT & GENERALIZATION")

    # Chart container on left
    card_img = s13.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.35), Inches(1.35), Inches(4.85), Inches(3.95))
    card_img.fill.solid()
    card_img.fill.fore_color.rgb = WHITE
    card_img.line.color.rgb = CYAN
    card_img.line.width = Pt(1.5)

    rolling_img = ASSETS / "rolling_white.png"
    if rolling_img.exists():
        s13.shapes.add_picture(str(rolling_img), Inches(0.42), Inches(1.55), Inches(4.71), Inches(3.55))

    # Insights card on right
    card_txt = s13.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.35), Inches(1.35), Inches(4.35), Inches(3.95))
    card_txt.fill.solid()
    card_txt.fill.fore_color.rgb = DARK_CARD
    card_txt.line.color.rgb = DARK_ROW
    card_txt.line.width = Pt(1)

    tb = s13.shapes.add_textbox(Inches(5.50), Inches(1.45), Inches(4.05), Inches(3.75))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    findings = [
        ("The Platform-Wide Rate Collapse: ", "Prior to ChatGPT (Nov 2022), 44.0% of questions were resolved within 7 days. Post-launch, the resolution rate dropped to 23.3%–32.5% as developers offloaded simple queries to AI assistants."),
        ("Invariance of Ranking Ability: ", "Despite the massive volume drop and demographic shift, model ROC-AUC remained remarkably invariant (0.63–0.65 pre-ChatGPT vs 0.64–0.67 post-ChatGPT). The model reliably ranks question quality across regimes."),
        ("Positive PR Lift Maintained: ", "PR-AUC consistently maintained a positive margin over the drifting base rate across all 11 half-year rolling windows from 2021-H1 to 2026-H1, showing zero collapse."),
        ("Rigorous Rolling-Origin Protocol: ", "Each half-year test window was evaluated strictly against a model trained only on preceding historical data, guaranteeing zero temporal leakage."),
        ("Operational Deployment Strategy: ", "The feature relationships remain stable, but the base rate shifted. Re-calibrating the decision threshold quarterly preserves optimal precision-recall triage.")
    ]

    for i, (hd, body) in enumerate(findings):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(6)
        add_text_run(p, "• ", font="Nunito Sans", size=9, bold=True, color=CYAN)
        add_text_run(p, hd, font="Nunito Sans", size=9, bold=True, color=CYAN)
        add_text_run(p, body, font="Nunito Sans", size=8.5, bold=False, color=WHITE)


def populate_slide_14_errors(s14):
    """Slide 14 (NEW): Error Analysis & Business Decision Triage."""
    clear_placeholder_shapes(s14)
    add_slide_header(s14, "Error Diagnostics & Business Triage Recommendations", "MEMBER 5: ERROR ANALYSIS & ACTIONABILITY")

    # Chart container on left
    card_img = s14.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.35), Inches(1.35), Inches(4.85), Inches(3.95))
    card_img.fill.solid()
    card_img.fill.fore_color.rgb = WHITE
    card_img.line.color.rgb = ORANGE
    card_img.line.width = Pt(1.5)

    err_img = ASSETS / "error_analysis_white.png"
    if err_img.exists():
        s14.shapes.add_picture(str(err_img), Inches(0.42), Inches(1.55), Inches(4.71), Inches(3.55))

    # Insights card on right
    card_txt = s14.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.35), Inches(1.35), Inches(4.35), Inches(3.95))
    card_txt.fill.solid()
    card_txt.fill.fore_color.rgb = DARK_CARD
    card_txt.line.color.rgb = DARK_ROW
    card_txt.line.width = Pt(1)

    tb = s14.shapes.add_textbox(Inches(5.50), Inches(1.45), Inches(4.05), Inches(3.75))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    points = [
        ("False Positive Diagnosis (67% Answered): ", "In 10 of 15 top false positives, high-quality answers WERE received within 7 days, but the asker never clicked 'accept'. The model correctly identified answerable questions; the failure was user abandonment."),
        ("False Negative Diagnosis (53% Zero-Day Accounts): ", "8 of 15 top false negatives came from brand-new users who posted well-structured questions with clear stack traces and received rapid expert answers despite account youth."),
        ("Business Triage Lift (1.21x Over Random): ", "Flagging the bottom 20% predicted resolution scores captures 24.15% of all unresolved questions. For a moderation queue of 10,000 weekly posts, this surfaces 415 additional at-risk questions."),
        ("Actionable Platform Interventions: ", "1) Prompt askers to add code snippets if code_ratio == 0; 2) Provide interactive guidance for day-0 askers; 3) Send gentle automated reminders to askers to mark accepted answers.")
    ]

    for i, (hd, body) in enumerate(points):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(7)
        add_text_run(p, "• ", font="Nunito Sans", size=9, bold=True, color=ORANGE)
        add_text_run(p, hd, font="Nunito Sans", size=9, bold=True, color=ORANGE)
        add_text_run(p, body, font="Nunito Sans", size=8.5, bold=False, color=WHITE)


def populate_slide_timeseries(s_ts):
    """Slide: Advanced Analytics - Time Series Volume Forecasting (Unit 3)."""
    clear_placeholder_shapes(s_ts)
    add_slide_header(s_ts, "Advanced Time Series Forecasting: AI Shift & 2027 Projections", "MEMBER 5: ADVANCED ANALYTICS (UNIT 3)")

    # Chart container on left
    card_img = s_ts.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.35), Inches(1.35), Inches(4.85), Inches(3.95))
    card_img.fill.solid()
    card_img.fill.fore_color.rgb = WHITE
    card_img.line.color.rgb = MINT
    card_img.line.width = Pt(1.5)

    ts_img = ASSETS / "timeseries_forecast_white.png"
    if ts_img.exists():
        s_ts.shapes.add_picture(str(ts_img), Inches(0.42), Inches(1.42), Inches(4.71), Inches(3.81))

    # Insights card on right
    card_txt = s_ts.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.35), Inches(1.35), Inches(4.35), Inches(3.95))
    card_txt.fill.solid()
    card_txt.fill.fore_color.rgb = DARK_CARD
    card_txt.line.color.rgb = DARK_ROW
    card_txt.line.width = Pt(1)

    tb = s_ts.shapes.add_textbox(Inches(5.50), Inches(1.45), Inches(4.05), Inches(3.75))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    points = [
        ("High-Accuracy Time Series Model: ", "Holt's Damped Trend Exponential Smoothing achieves 91.72% Forecast Accuracy (MAPE 8.28%, R² = 0.976) on Site-Wide questions, and 87.65% Accuracy on the Python ecosystem over 87 test weeks."),
        ("Post-ChatGPT Structural Collapse: ", "Prior to Nov 2022, Stack Overflow generated over 35,000 questions weekly. Following ChatGPT, site volume experienced a permanent 92% structural drop down to ~1,400 questions/week."),
        ("Ecosystem Resilience Divergence: ", "General programming tags (Python, Java, JS) stabilized at a low baseline, whereas AI tooling (openai-api) emerged post-2023 with growing relative share and high volatility."),
        ("2027 Forward Projections: ", "Multi-step 26-week forecast through 2027 confirms platform activity will not rebound to pre-AI levels; communities must pivot toward high-complexity niche questions."),
        ("Curriculum Alignment: ", "Directly fulfills the Unit 3 Advanced Analytics syllabus requirement, supplementing our classification models with continuous demand forecasting.")
    ]

    for i, (hd, body) in enumerate(points):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(6)
        add_text_run(p, "• ", font="Nunito Sans", size=9, bold=True, color=MINT)
        add_text_run(p, hd, font="Nunito Sans", size=9, bold=True, color=MINT)
        add_text_run(p, body, font="Nunito Sans", size=8.5, bold=False, color=WHITE)


def populate_slide_15_tracking(s15):
    """Slide 15: Project Tracking and Progress."""
    # Remove old placeholder text box
    for sh in list(s15.shapes):
        if sh.name == "Google Shape;725;p71":
            sp = sh._element
            sp.getparent().remove(sp)

    tb15 = s15.shapes.add_textbox(Inches(0.30), Inches(1.55), Inches(3.90), Inches(3.70))
    tf15 = tb15.text_frame
    tf15.word_wrap = True

    items = [
        ("Tool & Board Link: ", "https://github.com/users/Abhinav-Gopalakrishnan/projects/3"),
        ("Workflow Stages: ", "Backlog, To Do, In Progress, Review/Testing, Completed"),
        ("Task Structure: ", "[MX-NN] 16 - 17 tasks per person split into 5 phases"),
        ("Verified Deliverables: ", "Linked pull requests & commits; Adhikkesh completed [M5-01] Eval Plan, [M5-02] Skeleton, [M5-03] Eval Module, [M5-05] Leakage Review, [M5-07] SHAP & Error Analysis, [M5-TS] Time Series Forecasting.")
    ]
    for i, (hd, txt) in enumerate(items):
        p = tf15.paragraphs[0] if i == 0 else tf15.add_paragraph()
        p.space_after = Pt(8)
        add_text_run(p, "• ", font="Nunito Sans", size=10, bold=True, color=MINT)
        add_text_run(p, hd, font="Nunito Sans", size=10, bold=True, color=MINT)
        add_text_run(p, txt, font="Nunito Sans", size=9.5, bold=False, color=WHITE)


def populate_slide_16_contributions(s16):
    """Slide 16: Individual Contributions (With Clean Native Table and Member 5 Highlight)."""
    # Remove old individual placeholder shapes (shapes 735 through 758)
    for sh in list(s16.shapes):
        if sh.name.startswith("Google Shape;") and sh.name != "Google Shape;734;p72":
            sp = sh._element
            sp.getparent().remove(sp)

    # Clean native PowerPoint Table
    t_shape = s16.shapes.add_table(6, 4, Inches(0.40), Inches(1.50), Inches(9.20), Inches(3.60))
    table = t_shape.table

    table.columns[0].width = Inches(2.20)
    table.columns[1].width = Inches(2.30)
    table.columns[2].width = Inches(2.35)
    table.columns[3].width = Inches(2.35)

    data = [
        ["TEAM MEMBER", "TASK AREA 1", "TASK AREA 2", "TASK AREA 3"],
        ["Member 1 (Abhinav)", "Data Collection & API", "309k Questions Pipeline", "Weekly Tag Counts"],
        ["Member 2 (Rishiikesh)", "Enrichment & Cleaning", "7-Day Outcome Labels", "Sampling Robustness"],
        ["Member 3 (Akshay)", "Problem Statement", "EDA Charts & Events", "Slide Template & Theme"],
        ["Member 4 (Nishanth)", "Chronological Split", "Feature Pipeline & VIF", "Baseline Logistic Model"],
        ["Member 5 (Adhikkesh)", "Advanced Models (XGB/RF)", "Time Series Forecast (91.7% Acc)", "SHAP & Error Analysis Triage"]
    ]

    for r_idx, row in enumerate(data):
        row_obj = table.rows[r_idx]
        row_obj.height = Inches(0.45) if r_idx == 0 else Inches(0.60)
        is_header = (r_idx == 0)
        is_m5 = (r_idx == 5)

        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = ""
            cell.fill.solid()

            if is_header:
                cell.fill.fore_color.rgb = DARK_ROW
            elif is_m5:
                cell.fill.fore_color.rgb = HIGHLIGHT_ROW
            elif r_idx % 2 == 1:
                cell.fill.fore_color.rgb = DARK_CARD
            else:
                cell.fill.fore_color.rgb = DARK_ROW

            cell.margin_left = Inches(0.12)
            cell.margin_right = Inches(0.12)
            cell.margin_top = Inches(0.08)
            cell.margin_bottom = Inches(0.08)

            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT

            font_name = "Poppins" if is_header else "Nunito Sans"
            font_size = 9.5 if is_header else (10 if is_m5 else 9.5)
            font_color = MINT if (is_header or is_m5) else WHITE

            add_text_run(p, val, font=font_name, size=font_size, bold=(is_header or is_m5), color=font_color)


def populate_slide_17_plan(s17):
    """Slide 17: Review 2 Plan."""
    for sh in list(s17.shapes):
        if sh.name.startswith("Review2Card"):
            sp = sh._element
            sp.getparent().remove(sp)

    card_data = [
        ("Topics & Complexity", MINT, [
            "Mine question bodies using NLP/LLMs to find topics developers still bring to human experts.",
            "Quantify question complexity shifts before and after AI assistant adoption across domains."
        ]),
        ("Technology Forecasting", ORANGE, [
            "Forecast weekly volume per tag using Prophet/ARIMA on complete API tag history.",
            "Identify tags facing terminal decline vs. resilient demand to guide DevRel community support."
        ]),
        ("Advanced Prediction Model", MINT, [
            "Ingest full question body & code snippets with DeBERTa and CodeBERT transformer embeddings.",
            "Engineer point-in-time leak-free user acceptance history and tag tenure features.",
            "Calibrate output probabilities to deploy automated forum triage bots in real time."
        ])
    ]

    card_w = Inches(2.95)
    card_h = Inches(3.15)
    top_pos = Inches(2.05)  # Completely clears the curved title arrow

    for i, (heading, pill_color, bullets) in enumerate(card_data):
        left_pos = Inches(0.40 + i * 3.15)

        base = s17.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, top_pos, card_w, card_h)
        base.name = f"Review2Card_Base_{i}"
        base.fill.solid()
        base.fill.fore_color.rgb = DARK_CARD
        base.line.color.rgb = pill_color
        base.line.width = Pt(1)

        pill = s17.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos + Inches(0.15), top_pos + Inches(0.15), card_w - Inches(0.30), Inches(0.45))
        pill.name = f"Review2Card_Pill_{i}"
        pill.fill.solid()
        pill.fill.fore_color.rgb = pill_color
        pill.line.fill.background()
        p_pill = pill.text_frame.paragraphs[0]
        p_pill.alignment = PP_ALIGN.CENTER
        add_text_run(p_pill, heading, font="Poppins", size=10, bold=True, color=DARK_ROW)

        tb = s17.shapes.add_textbox(left_pos + Inches(0.15), top_pos + Inches(0.70), card_w - Inches(0.30), card_h - Inches(0.80))
        tb.name = f"Review2Card_Text_{i}"
        tf = tb.text_frame
        tf.word_wrap = True
        for b_idx, bullet in enumerate(bullets):
            p = tf.paragraphs[0] if b_idx == 0 else tf.add_paragraph()
            p.space_after = Pt(7)
            add_text_run(p, f"• {bullet}", font="Nunito Sans", size=9.5, bold=False, color=WHITE)


def populate_slide_18_submissions(s18):
    """Slide 18: Submissions."""
    label_shapes = {
        "Google Shape;781;p74": "Notebooks",
        "Google Shape;782;p74": "Documentation",
        "Google Shape;783;p74": "Kanban Board"
    }
    for sh in s18.shapes:
        if sh.name in label_shapes:
            sh.width = Inches(2.20)

    link_updates = {
        "Google Shape;785;p74": "kaggle.com/code/abhinavgopalakrishnan/stackoverflow-in-the-ai-era",
        "Google Shape;786;p74": "github.com/Abhinav-Gopalakrishnan/.../dataset_documentation.md",
        "Google Shape;787;p74": "github.com/users/Abhinav-Gopalakrishnan/projects/3"
    }
    for sh in s18.shapes:
        if sh.name in link_updates:
            tf = sh.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.RIGHT
            sh.left = Inches(5.60)
            sh.width = Inches(4.10)
            add_text_run(p, link_updates[sh.name], font="Nunito Sans", size=8.5, bold=True, color=MINT)


def populate_slide_19_thankyou(s19):
    """Slide 19: Thank you!"""
    # Remove any existing custom text box
    for sh in list(s19.shapes):
        if sh.name.startswith("ThankYouBox"):
            sp = sh._element
            sp.getparent().remove(sp)

    tb_ty = s19.shapes.add_textbox(Inches(1.50), Inches(3.20), Inches(7.00), Inches(1.80))
    tb_ty.name = "ThankYouBox"
    tf_ty = tb_ty.text_frame
    tf_ty.word_wrap = True

    p_q = tf_ty.paragraphs[0]
    p_q.alignment = PP_ALIGN.CENTER
    p_q.space_after = Pt(8)
    add_text_run(p_q, "Questions?", font="Poppins", size=18, bold=True, color=DEEP_SLATE)

    team_members = [
        ("Adhikkesh S K", "CB.SC.U4CSE23101"),
        ("Abhinav Gopalakrishnan", "CB.SC.U4CSE23201"),
        ("Rishiikesh", "CB.SC.U4CSE23236"),
        ("Akshay Krishna", "CB.SC.U4CSE23403"),
        ("Nishanth Konchada", "CB.SC.U4CSE23523"),
    ]

    p_t = tf_ty.add_paragraph()
    p_t.alignment = PP_ALIGN.CENTER
    p_t.space_after = Pt(3)
    names_str = "    •    ".join([f"{name} ({reg})" for name, reg in team_members[:3]])
    add_text_run(p_t, names_str, font="Nunito Sans", size=9.5, bold=True, color=DEEP_SLATE)

    p_t2 = tf_ty.add_paragraph()
    p_t2.alignment = PP_ALIGN.CENTER
    names_str2 = "    •    ".join([f"{name} ({reg})" for name, reg in team_members[3:]])
    add_text_run(p_t2, names_str2, font="Nunito Sans", size=9.5, bold=True, color=DEEP_SLATE)


def build_presentations():
    print("Loading fresh presentation from backup...")
    prs = pptx.Presentation(SRC_PPTX)

    # 1. Update Slide 10 (Predictive Model Development)
    populate_slide_10(prs.slides[9])

    # 2. Update Slide 11 (Model Evaluation & Performance)
    populate_slide_11(prs.slides[10])

    # 3. Add 4 NEW SLIDES dedicated to Member 5 right after Slide 11
    layout_dark = prs.slides[10].slide_layout

    # Add Slide 12: SHAP Analysis
    s12 = prs.slides.add_slide(layout_dark)
    populate_slide_12_shap(s12)
    # Move from end of deck to position 11 (0-indexed, so 12th slide)
    sldId12 = prs.slides._sldIdLst[-1]
    prs.slides._sldIdLst.insert(11, sldId12)

    # Add Slide 13: Temporal Drift & ChatGPT Impact
    s13 = prs.slides.add_slide(layout_dark)
    populate_slide_13_drift(s13)
    # Move to position 12 (13th slide)
    sldId13 = prs.slides._sldIdLst[-1]
    prs.slides._sldIdLst.insert(12, sldId13)

    # Add Slide 14: Error Analysis & Triage
    s14 = prs.slides.add_slide(layout_dark)
    populate_slide_14_errors(s14)
    # Move to position 13 (14th slide)
    sldId14 = prs.slides._sldIdLst[-1]
    prs.slides._sldIdLst.insert(13, sldId14)

    # Add Slide 15: Advanced Time Series Forecasting (Unit 3 Requirement)
    s_ts = prs.slides.add_slide(layout_dark)
    populate_slide_timeseries(s_ts)
    # Move to position 14 (15th slide)
    sldId_ts = prs.slides._sldIdLst[-1]
    prs.slides._sldIdLst.insert(14, sldId_ts)

    # 4. Update the concluding slides (now at indices 15 to 19)
    populate_slide_15_tracking(prs.slides[15])
    populate_slide_16_contributions(prs.slides[16])
    populate_slide_17_plan(prs.slides[17])
    populate_slide_18_submissions(prs.slides[18])
    populate_slide_19_thankyou(prs.slides[19])

    print(f"Total slides in updated full presentation: {len(prs.slides)}")
    prs.save(OUT_FULL_PPTX)
    print(f"✓ Saved complete 20-slide presentation to: {OUT_FULL_PPTX}")

    # 5. Build Member 5 Standalone Deck (Slides 10-20: All slides from Member 5 onwards)
    prs_m5_deck = pptx.Presentation(OUT_FULL_PPTX)
    # Drop first 9 slides (slides 0 through 8)
    for _ in range(9):
        rId = prs_m5_deck.slides._sldIdLst[0].rId
        prs_m5_deck.part.drop_rel(rId)
        del prs_m5_deck.slides._sldIdLst[0]

    prs_m5_deck.save(OUT_M5_DECK)
    print(f"✓ Saved Member 5 full section deck ({len(prs_m5_deck.slides)} slides) to: {OUT_M5_DECK}")

    # 6. Build Member 5 ONLY Deck (Specifically the 6 predictive model, time series & evaluation slides)
    prs_m5_only = pptx.Presentation(OUT_FULL_PPTX)
    # Drop first 9 slides
    for _ in range(9):
        rId = prs_m5_only.slides._sldIdLst[0].rId
        prs_m5_only.part.drop_rel(rId)
        del prs_m5_only.slides._sldIdLst[0]
    # Now slides 0 to 5 are the 6 model & time series slides. Drop remaining slides (6 to end)
    while len(prs_m5_only.slides) > 6:
        rId = prs_m5_only.slides._sldIdLst[6].rId
        prs_m5_only.part.drop_rel(rId)
        del prs_m5_only.slides._sldIdLst[6]

    prs_m5_only.save(OUT_M5_ONLY)
    print(f"✓ Saved Member 5 ONLY (6 core model slides) to: {OUT_M5_ONLY}")


if __name__ == "__main__":
    build_presentations()
