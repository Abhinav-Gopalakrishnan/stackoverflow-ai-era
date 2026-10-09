"""Populate Member 5's slides in BA Final Project - Review 1_cpy.pptx.

This script updates slides 10-16 in-place with the exact dark theme styling
from the presentation template (charcoal background, glowing cyan orbs,
neon mint accents, Poppins/Nunito fonts), and creates a standalone
Member_5_Review_1_Slides_Dark.pptx for Google Slides import.
"""

from pathlib import Path
import pptx
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path("/home/adhikkesh/adhikkesh/SEM7/BA/stackoverflow-ai-era")
SRC_PPTX = ROOT / "BA Final Project - Review 1_cpy_backup.pptx"
OUT_PPTX = ROOT / "BA Final Project - Review 1_cpy.pptx"
STANDALONE_PPTX = ROOT / "Member_5_Review_1_Slides_Dark.pptx"
ASSETS = ROOT / "reports" / "review1" / "deck_assets"

# Template color palette
DARK_BG = RGBColor(0x1A, 0x1D, 0x24)       # Deep slate
DARK_CARD = RGBColor(0x13, 0x18, 0x22)     # Card background
DARK_ROW = RGBColor(0x1E, 0x24, 0x30)      # Table alternating row
MINT = RGBColor(0x1D, 0xE9, 0xB6)          # Primary accent mint green
ORANGE = RGBColor(0xFF, 0x98, 0x00)        # Secondary badge orange
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xCF, 0xD8, 0xDC)
HIGHLIGHT_ROW = RGBColor(0x1B, 0x38, 0x35) # Dark teal highlight for best model
DEEP_SLATE = RGBColor(0x13, 0x18, 0x22)    # Dark text for Slide 16 sky background


def run_text(para, text, font="Nunito Sans", size=10, bold=False, color=WHITE):
    r = para.add_run()
    r.text = text
    r.font.name = font
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    return r


def update_deck():
    # Load fresh from backup so modifications are always clean and repeatable
    prs = pptx.Presentation(SRC_PPTX)

    # -------------------------------------------------------------
    # SLIDE 10: Predictive Model Development
    # -------------------------------------------------------------
    s10 = prs.slides[9]
    # Remove old placeholder text box (Google Shape;708;p69)
    for sh in list(s10.shapes):
        if sh.name == "Google Shape;708;p69":
            sp = sh._element
            sp.getparent().remove(sp)

    # Create fresh clean text box without inherited bullet formatting
    tb10 = s10.shapes.add_textbox(Inches(0.30), Inches(1.50), Inches(4.35), Inches(3.80))
    tf10 = tb10.text_frame
    tf10.word_wrap = True

    sections = [
        ("Prediction task: ", "Binary Classification — Predicting if a newly posted question receives an accepted answer within 7 days (target_resolved_7d)."),
        ("Model(s): ", "Majority Class Baseline, Baseline Logistic Regression, Random Forest, and XGBoost Classifier."),
        ("Model selection: ", "Chosen on validation PR-AUC: XGBoost (0.482) vs Random Forest (0.473) vs Logistic Regression (0.471) vs Majority (0.341)."),
        ("Data split: ", "Strict Chronological Split — Train: 2019–2024 (248k, 85%), Validation: Jan–Jun 2025 (28k, 10%), Test: Jul 2025–Jul 2026 (16.7k, 6%, evaluated once)."),
        ("Model settings: ", "Tuned on time-series folds with 7-day gap; XGBoost (lr=0.029, depth=5, 628 trees via early stopping, threshold=0.367); Random Forest (472 trees, depth=16).")
    ]

    for i, (head, body) in enumerate(sections):
        p = tf10.paragraphs[0] if i == 0 else tf10.add_paragraph()
        p.space_after = Pt(6)
        run_text(p, "• ", font="Nunito Sans", size=10, bold=True, color=MINT)
        run_text(p, head, font="Nunito Sans", size=10, bold=True, color=MINT)
        run_text(p, body, font="Nunito Sans", size=9.5, bold=False, color=WHITE)

    # Add split_dark.png on the right with mint border
    split_img = ASSETS / "split_dark.png"
    if split_img.exists():
        card = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.85), Inches(1.55), Inches(4.85), Inches(3.20))
        card.fill.solid()
        card.fill.fore_color.rgb = DARK_CARD
        card.line.color.rgb = MINT
        card.line.width = Pt(1.5)
        s10.shapes.add_picture(str(split_img), Inches(4.90), Inches(1.60), Inches(4.75), Inches(3.10))

    # -------------------------------------------------------------
    # SLIDE 11: Model Evaluation and Result Interpretation
    # -------------------------------------------------------------
    s11 = prs.slides[10]
    # Remove old placeholder text box (Google Shape;720;p70)
    for sh in list(s11.shapes):
        if sh.name == "Google Shape;720;p70":
            sp = sh._element
            sp.getparent().remove(sp)

    # Add Model Comparison Table on left (compact, starting at 1.35 in)
    t_shape = s11.shapes.add_table(7, 7, Inches(0.25), Inches(1.35), Inches(5.85), Inches(2.05))
    table = t_shape.table
    table.columns[0].width = Inches(1.70)
    table.columns[1].width = Inches(0.65)
    table.columns[2].width = Inches(0.65)
    table.columns[3].width = Inches(0.65)
    table.columns[4].width = Inches(0.65)
    table.columns[5].width = Inches(0.75)
    table.columns[6].width = Inches(0.80)

    table_data = [
        ["Model (validation)", "Acc", "Prec", "Rec", "F1", "PR-AUC", "ROC"],
        ["Majority class", "0.659", "0.000", "0.000", "0.000", "0.341", "0.500"],
        ["Baseline LogReg", "0.412", "0.357", "0.909", "0.513", "0.394", "0.579"],
        ["LogReg (+Text)", "0.502", "0.389", "0.808", "0.525", "0.471", "0.636"],
        ["Random forest", "0.496", "0.386", "0.813", "0.524", "0.473", "0.638"],
        ["XGBoost (Val)", "0.527", "0.400", "0.782", "0.529", "0.482", "0.645"],
        ["XGBoost (Test Period)", "0.530", "0.363", "0.771", "0.493", "0.431", "0.655"]
    ]

    for r in table.rows:
        r.height = Inches(0.28)

    for cell in table.iter_cells():
        cell.margin_top = Inches(0.02)
        cell.margin_bottom = Inches(0.02)
        cell.margin_left = Inches(0.03)
        cell.margin_right = Inches(0.03)

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
            run_text(p, val, font="Nunito Sans", size=8.5 if (r_idx == 6 and c_idx == 0) else 9, bold=(r_idx == 0 or r_idx >= 5), color=color)

    # Add Confusion Matrix image on right
    conf_img = ASSETS / "confusion_dark.png"
    if conf_img.exists():
        card_c = s11.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.30), Inches(1.35), Inches(3.40), Inches(2.20))
        card_c.fill.solid()
        card_c.fill.fore_color.rgb = DARK_CARD
        card_c.line.color.rgb = MINT
        card_c.line.width = Pt(1.5)
        s11.shapes.add_picture(str(conf_img), Inches(6.35), Inches(1.40), Inches(3.30), Inches(2.10))

    # Add 3 Key Takeaways across bottom with zero overlap
    box_b = s11.shapes.add_textbox(Inches(0.25), Inches(3.85), Inches(9.50), Inches(1.50))
    tf_b = box_b.text_frame
    tf_b.word_wrap = True

    takeaways = [
        ("• Accuracy Context: ", "Raw accuracy is 53.0% because threshold (0.367) was tuned on validation to prioritize high recall (77.1%). Always guessing unresolved achieves 65.9% accuracy with zero utility (0% recall)."),
        ("• Top Drivers (SHAP): ", "Tag question volume in prior 4 weeks, asker account age, and code block share provide the strongest predictive signals."),
        ("• Business Triage Lift: ", "Flagging the lowest 20% of predicted resolution scores captures 24.15% of all unresolved questions (1.21x lift over random).")
    ]

    for i, (hd, txt) in enumerate(takeaways):
        p = tf_b.paragraphs[0] if i == 0 else tf_b.add_paragraph()
        p.space_after = Pt(3)
        run_text(p, hd, font="Nunito Sans", size=9, bold=True, color=MINT)
        run_text(p, txt, font="Nunito Sans", size=9, bold=False, color=WHITE)

    # -------------------------------------------------------------
    # SLIDE 12: Project Tracking and Progress
    # -------------------------------------------------------------
    s12 = prs.slides[11]
    # Remove old placeholder text box (Google Shape;725;p71)
    for sh in list(s12.shapes):
        if sh.name == "Google Shape;725;p71":
            sp = sh._element
            sp.getparent().remove(sp)

    # Fresh textbox for tracking bullets
    tb12 = s12.shapes.add_textbox(Inches(0.30), Inches(1.55), Inches(3.90), Inches(3.70))
    tf12 = tb12.text_frame
    tf12.word_wrap = True

    items = [
        ("Tool and board link: ", "https://github.com/users/Abhinav-Gopalakrishnan/projects/3"),
        ("Stages: ", "Backlog, To Do, In Progress, Review/Testing, Completed"),
        ("Task Format: ", "[MX-NN] 16 - 17 tasks per person split into 5 phases"),
        ("Evidence: ", "Linked pull requests & commits; Adhikkesh completed [M5-01] Eval Plan, [M5-02] Skeleton, [M5-03] Eval Module, [M5-05] Leakage Review.")
    ]
    for i, (hd, txt) in enumerate(items):
        p = tf12.paragraphs[0] if i == 0 else tf12.add_paragraph()
        p.space_after = Pt(8)
        run_text(p, "• ", font="Nunito Sans", size=10, bold=True, color=MINT)
        run_text(p, hd, font="Nunito Sans", size=10, bold=True, color=MINT)
        run_text(p, txt, font="Nunito Sans", size=9.5, bold=False, color=WHITE)

    # -------------------------------------------------------------
    # SLIDE 13: Individual Contributions
    # -------------------------------------------------------------
    s13 = prs.slides[12]
    # Widen columns and align clean text
    col_layout = {
        # Col 1: Member Name
        "Google Shape;736;p72": (Inches(0.36), Inches(2.10), "Member 1 (Abhinav)", False),
        "Google Shape;741;p72": (Inches(0.36), Inches(2.10), "Member 2 (Rishiikesh)", False),
        "Google Shape;745;p72": (Inches(0.36), Inches(2.10), "Member 3 (Akshay)", False),
        "Google Shape;750;p72": (Inches(0.36), Inches(2.10), "Member 4 (Nishanth)", False),
        "Google Shape;755;p72": (Inches(0.36), Inches(2.10), "Member 5 (Adhikkesh)", True),

        # Col 2: Task 1
        "Google Shape;738;p72": (Inches(2.65), Inches(2.45), "Data Collection", False),
        "Google Shape;742;p72": (Inches(2.65), Inches(2.45), "Enrichment & Cleaning", False),
        "Google Shape;746;p72": (Inches(2.65), Inches(2.45), "Problem Statement", False),
        "Google Shape;751;p72": (Inches(2.65), Inches(2.45), "Chronological Split", False),
        "Google Shape;756;p72": (Inches(2.65), Inches(2.45), "Advanced Models (XGB/RF)", True),

        # Col 3: Task 2
        "Google Shape;739;p72": (Inches(5.25), Inches(2.40), "309k Questions API", False),
        "Google Shape;743;p72": (Inches(5.25), Inches(2.40), "7-Day Outcome Labels", False),
        "Google Shape;747;p72": (Inches(5.25), Inches(2.40), "EDA Charts & Events", False),
        "Google Shape;752;p72": (Inches(5.25), Inches(2.40), "Feature Pipeline & VIF", False),
        "Google Shape;757;p72": (Inches(5.25), Inches(2.40), "Evaluation & SHAP", True),

        # Col 4: Task 3
        "Google Shape;740;p72": (Inches(7.75), Inches(2.05), "Weekly Tag Counts", False),
        "Google Shape;744;p72": (Inches(7.75), Inches(2.05), "Sampling Robustness", False),
        "Google Shape;748;p72": (Inches(7.75), Inches(2.05), "Slide Template", False),
        "Google Shape;753;p72": (Inches(7.75), Inches(2.05), "Baseline Logistic Model", False),
        "Google Shape;758;p72": (Inches(7.75), Inches(2.05), "Error Analysis & Findings", True),
    }

    for sh in s13.shapes:
        if sh.name in col_layout:
            new_left, new_w, text_val, is_m5 = col_layout[sh.name]
            sh.left = new_left
            sh.width = new_w
            tf = sh.text_frame
            tf.clear()
            tf.word_wrap = False
            p = tf.paragraphs[0]
            color = MINT if is_m5 else WHITE
            run_text(p, text_val, font="Nunito Sans", size=9.5, bold=is_m5, color=color)

    # -------------------------------------------------------------
    # SLIDE 14: Review 2 Plan
    # -------------------------------------------------------------
    s14 = prs.slides[13]
    # Remove any existing custom shapes if re-running
    for sh in list(s14.shapes):
        if sh.name.startswith("Review2Card"):
            sp = sh._element
            sp.getparent().remove(sp)

    card_data = [
        ("Topics & Complexity", MINT, [
            "Mine question bodies using NLP/LLMs to find topics developers still bring to human experts.",
            "Quantify question complexity shifts before and after AI assistant adoption."
        ]),
        ("Technology Forecasting", ORANGE, [
            "Forecast weekly volume per tag using Prophet/ARIMA on complete counts.",
            "Identify tags facing terminal decline vs. resilient demand to guide DevRel support."
        ]),
        ("Advanced Prediction Model", MINT, [
            "Ingest full question body & code snippets with DeBERTa and CodeBERT.",
            "Engineer point-in-time leak-free user acceptance history.",
            "Calibrate probabilities for reliable automated forum triage."
        ])
    ]

    card_w = Inches(2.90)
    card_h = Inches(3.20)
    top_pos = Inches(1.80)

    for i, (heading, pill_color, bullets) in enumerate(card_data):
        left_pos = Inches(0.40 + i * 3.15)

        base = s14.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, top_pos, card_w, card_h)
        base.name = f"Review2Card_Base_{i}"
        base.fill.solid()
        base.fill.fore_color.rgb = DARK_CARD
        base.line.color.rgb = pill_color
        base.line.width = Pt(1)

        pill = s14.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos + Inches(0.15), top_pos + Inches(0.15), card_w - Inches(0.30), Inches(0.45))
        pill.name = f"Review2Card_Pill_{i}"
        pill.fill.solid()
        pill.fill.fore_color.rgb = pill_color
        pill.line.fill.background()
        p_pill = pill.text_frame.paragraphs[0]
        p_pill.alignment = PP_ALIGN.CENTER
        run_text(p_pill, heading, font="Poppins", size=10, bold=True, color=DARK_ROW)

        tb = s14.shapes.add_textbox(left_pos + Inches(0.15), top_pos + Inches(0.75), card_w - Inches(0.30), card_h - Inches(0.90))
        tb.name = f"Review2Card_Text_{i}"
        tf = tb.text_frame
        tf.word_wrap = True
        for b_idx, bullet in enumerate(bullets):
            p = tf.paragraphs[0] if b_idx == 0 else tf.add_paragraph()
            p.space_after = Pt(8)
            run_text(p, f"• {bullet}", font="Nunito Sans", size=9.5, bold=False, color=WHITE)

    # -------------------------------------------------------------
    # SLIDE 15: Submissions
    # -------------------------------------------------------------
    s15 = prs.slides[14]
    # Widen labels to not collide, and right-align links
    label_shapes = {
        "Google Shape;781;p74": "Notebooks",
        "Google Shape;782;p74": "Documentation",
        "Google Shape;783;p74": "Kanban Board"
    }
    for sh in s15.shapes:
        if sh.name in label_shapes:
            sh.width = Inches(2.20)

    link_updates = {
        "Google Shape;785;p74": "kaggle.com/code/abhinavgopalakrishnan/stackoverflow-in-the-ai-era",
        "Google Shape;786;p74": "github.com/Abhinav-Gopalakrishnan/.../dataset_documentation.md",
        "Google Shape;787;p74": "github.com/users/Abhinav-Gopalakrishnan/projects/3"
    }
    for sh in s15.shapes:
        if sh.name in link_updates:
            tf = sh.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.RIGHT
            sh.left = Inches(5.60)
            sh.width = Inches(4.10)
            run_text(p, link_updates[sh.name], font="Nunito Sans", size=8, bold=True, color=MINT)

    # -------------------------------------------------------------
    # SLIDE 16: Thank you! (Sky blue background, dark text)
    # -------------------------------------------------------------
    s16 = prs.slides[15]
    tb_ty = s16.shapes.add_textbox(Inches(1.50), Inches(3.20), Inches(7.00), Inches(1.80))
    tf_ty = tb_ty.text_frame
    tf_ty.word_wrap = True

    p_q = tf_ty.paragraphs[0]
    p_q.alignment = PP_ALIGN.CENTER
    p_q.space_after = Pt(8)
    run_text(p_q, "Questions?", font="Poppins", size=18, bold=True, color=DEEP_SLATE)

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
    run_text(p_t, names_str, font="Nunito Sans", size=9.5, bold=True, color=DEEP_SLATE)

    p_t2 = tf_ty.add_paragraph()
    p_t2.alignment = PP_ALIGN.CENTER
    names_str2 = "    •    ".join([f"{name} ({reg})" for name, reg in team_members[3:]])
    run_text(p_t2, names_str2, font="Nunito Sans", size=9.5, bold=True, color=DEEP_SLATE)

    prs.save(OUT_PPTX)
    print(f"Saved updated deck to {OUT_PPTX}")

    # -------------------------------------------------------------
    # Create Standalone Deck: Member_5_Review_1_Slides_Dark.pptx
    # -------------------------------------------------------------
    prs_m5 = pptx.Presentation(OUT_PPTX)
    # Remove first 9 slides (slides 0 to 8)
    for _ in range(9):
        rId = prs_m5.slides._sldIdLst[0].rId
        prs_m5.part.drop_rel(rId)
        del prs_m5.slides._sldIdLst[0]

    prs_m5.save(STANDALONE_PPTX)
    print(f"Saved standalone Member 5 dark deck to {STANDALONE_PPTX} ({len(prs_m5.slides)} slides)")


if __name__ == "__main__":
    update_deck()
