"""Generate Member 4 (Nishanth) Review 2 presentation slides in PPTX format.
Matches the official Review 2 dark design theme, layout, and exact findings.

Usage:
    python -m src.make_m4_slides
"""
from __future__ import annotations
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/review2'

# Color Palette matching Review 2 dark theme
BG_COLOR = RGBColor(0x10, 0x14, 0x13)      # 101413 dark charcoal
PANEL_COLOR = RGBColor(0x1B, 0x22, 0x20)   # 1B2220 card panel
TEAL_COLOR = RGBColor(0x38, 0xDD, 0xB5)    # 38DDB5 accent teal
WHITE_COLOR = RGBColor(0xF4, 0xF8, 0xF6)   # F4F8F6 white
MUTED_COLOR = RGBColor(0xAA, 0xB9, 0xB5)   # AAB9B5 muted grey
BORDER_COLOR = RGBColor(0x39, 0x45, 0x41)  # 394541 subtle border
GREEN_COLOR = RGBColor(0x4E, 0xCD, 0x8C)   # rising
RED_COLOR = RGBColor(0xFF, 0x6B, 0x6B)     # falling

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def add_slide_base(prs: Presentation, speaker_tag: str, title: str, slide_num: int):
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    
    # Background fill
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_COLOR
    bg.line.color.rgb = BG_COLOR
    
    # Header tag (Teal 11pt bold)
    tb_tag = slide.shapes.add_textbox(Inches(0.6), Inches(0.32), Inches(12.0), Inches(0.24))
    tf_tag = tb_tag.text_frame
    tf_tag.word_wrap = True
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = speaker_tag
    p_tag.font.size = Pt(11)
    p_tag.font.bold = True
    p_tag.font.color.rgb = TEAL_COLOR
    p_tag.font.name = "Arial"
    
    # Slide Title (White 26pt bold)
    tb_title = slide.shapes.add_textbox(Inches(0.6), Inches(0.68), Inches(12.1), Inches(0.72))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title
    p_title.font.size = Pt(25)
    p_title.font.bold = True
    p_title.font.color.rgb = WHITE_COLOR
    p_title.font.name = "Arial"
    
    # Footer Left
    tb_foot = slide.shapes.add_textbox(Inches(0.6), Inches(7.05), Inches(10.0), Inches(0.25))
    tf_foot = tb_foot.text_frame
    p_foot = tf_foot.paragraphs[0]
    p_foot.text = "STACK OVERFLOW IN THE AI ERA / REVIEW 2"
    p_foot.font.size = Pt(9)
    p_foot.font.color.rgb = MUTED_COLOR
    p_foot.font.name = "Arial"
    
    # Footer Right
    tb_num = slide.shapes.add_textbox(Inches(12.2), Inches(7.05), Inches(0.6), Inches(0.25))
    tf_num = tb_num.text_frame
    p_num = tf_num.paragraphs[0]
    p_num.text = str(slide_num)
    p_num.alignment = PP_ALIGN.RIGHT
    p_num.font.size = Pt(9)
    p_num.font.color.rgb = MUTED_COLOR
    p_num.font.name = "Arial"
    
    return slide


def add_card(slide, left, top, width, height):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = PANEL_COLOR
    shape.line.color.rgb = BORDER_COLOR
    shape.line.width = Pt(0.75)
    return shape


def build_deck():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    
    # =========================================================================
    # SLIDE 1 (Team Deck Slide 9): Topic Model Choice & Evaluation
    # =========================================================================
    s1 = add_slide_base(
        prs,
        "NISHANTH / MEMBER 4",
        "Topic model choice: coherence, diversity, stability, human agreement",
        9
    )
    
    # Left Card: Candidate Grid Design & Pre-registered Rule
    add_card(s1, Inches(0.6), Inches(1.55), Inches(4.5), Inches(5.25))
    
    tb_l = s1.shapes.add_textbox(Inches(0.85), Inches(1.75), Inches(4.0), Inches(4.85))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    
    p = tf_l.paragraphs[0]
    p.text = "CANDIDATE GRID & DECISION RULE"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = TEAL_COLOR
    p.space_after = Pt(10)
    
    bullets = [
        ("Corpus Sample", "80,000 stratified questions (5,000 per half-year across 2019 H1 - 2026 H2)."),
        ("Features", "TF-IDF 30,000 unigrams/bigrams (min_df=20, max_df=0.40)."),
        ("Model Grid", "NMF (Frobenius, KL) vs. LDA across k in {10, 15, 20, 25, 30, 40}."),
        ("Selection Rule", "Highest held-out NPMI topic coherence with diversity >= 0.70 and multi-seed stability >= 0.60."),
        ("Winning Model", "NMF k=10 selected objectively. Dominates LDA on coherence, diversity, and seed stability."),
        ("Human Validation", "Top 15 terms + 10 representative question titles exported for independent human labeling by Member 2.")
    ]
    
    for title, desc in bullets:
        p_b = tf_l.add_paragraph()
        p_b.space_after = Pt(6)
        r1 = p_b.add_run()
        r1.text = f"{title}: "
        r1.font.bold = True
        r1.font.size = Pt(12)
        r1.font.color.rgb = WHITE_COLOR
        r2 = p_b.add_run()
        r2.text = desc
        r2.font.size = Pt(11.5)
        r2.font.color.rgb = MUTED_COLOR

    # Right Card: Grid Comparison Table & Diagnostics
    add_card(s1, Inches(5.3), Inches(1.55), Inches(7.45), Inches(5.25))
    
    tb_r_head = s1.shapes.add_textbox(Inches(5.55), Inches(1.75), Inches(7.0), Inches(0.4))
    p_rh = tb_r_head.text_frame.paragraphs[0]
    p_rh.text = "MODEL EVALUATION GRID (NMF vs LDA)"
    p_rh.font.size = Pt(13)
    p_rh.font.bold = True
    p_rh.font.color.rgb = TEAL_COLOR
    
    # Table of candidate models
    table_shape = s1.shapes.add_table(7, 6, Inches(5.55), Inches(2.2), Inches(6.95), Inches(2.4))
    table = table_shape.table
    table.columns[0].width = Inches(1.2)
    table.columns[1].width = Inches(0.65)
    table.columns[2].width = Inches(1.35)
    table.columns[3].width = Inches(1.2)
    table.columns[4].width = Inches(1.2)
    table.columns[5].width = Inches(1.35)
    
    headers = ["Model", "k", "Held-out NPMI", "Diversity", "Stability", "Recon Error"]
    for col_idx, h in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(0x24, 0x2E, 0x2B)
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = TEAL_COLOR
        p.alignment = PP_ALIGN.CENTER
        
    rows_data = [
        ("NMF (Winner)", "10", "+0.2175", "0.8000", "1.0000", "268.7"),
        ("NMF", "15", "+0.1742", "0.8200", "0.9421", "258.4"),
        ("NMF", "20", "+0.1410", "0.8450", "0.8930", "251.2"),
        ("NMF", "25", "+0.1189", "0.8640", "0.8415", "245.9"),
        ("LDA", "10", "-0.0820", "0.6500", "0.5210", "1.24e5"),
        ("LDA", "20", "-0.1145", "0.6120", "0.4890", "1.31e5")
    ]
    
    for row_idx, r_vals in enumerate(rows_data, start=1):
        is_winner = "Winner" in r_vals[0]
        for col_idx, val in enumerate(r_vals):
            cell = table.cell(row_idx, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(0x1E, 0x29, 0x26) if is_winner else PANEL_COLOR
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(11)
            p.font.bold = is_winner
            p.font.color.rgb = GREEN_COLOR if (is_winner and col_idx == 0) else (WHITE_COLOR if is_winner else MUTED_COLOR)
            p.alignment = PP_ALIGN.CENTER
            
    # Bottom Callout Box inside Right Card
    tb_sub = s1.shapes.add_textbox(Inches(5.55), Inches(4.8), Inches(6.95), Inches(1.8))
    tf_sub = tb_sub.text_frame
    tf_sub.word_wrap = True
    
    p = tf_sub.paragraphs[0]
    p.text = "KEY METHODOLOGICAL TAKEAWAYS:"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = WHITE_COLOR
    p.space_after = Pt(4)
    
    sub_points = [
        "NMF achieves positive semantic coherence (+0.2175) on developer vocabulary, whereas LDA produces negative NPMI (-0.0820) due to broad, overlapping dirichlet priors.",
        "NMF k=10 exhibits 1.0000 Jaccard stability across 3 random seeds; higher k splits coherent topics into brittle micro-clusters.",
        "302,026 full corpus questions transformed to dominant topics; inter-annotator agreement tracking awaiting Member 2 independent names in topic_labels.csv."
    ]
    for pt in sub_points:
        p_pt = tf_sub.add_paragraph()
        p_pt.space_after = Pt(3)
        r = p_pt.add_run()
        r.text = f"- {pt}"
        r.font.size = Pt(10.5)
        r.font.color.rgb = MUTED_COLOR
        
    s1.notes_slide.notes_text_frame.text = (
        "Speaker Notes (Nishanth / Member 4 - 1:15 min):\n"
        "I evaluated candidate topic models across NMF and LDA for k between 10 and 40 using a stratified sample of "
        "80,000 questions balanced across 16 half-years. Candidate selection followed a pre-registered objective rule: "
        "maximizing held-out NPMI topic coherence while maintaining semantic diversity above 0.70 and multi-seed stability above 0.60.\n\n"
        "NMF k=10 won cleanly on all three criteria, achieving +0.2175 NPMI coherence, 0.80 diversity, and perfect 1.00 stability. "
        "In contrast, LDA struggled on this technical vocabulary with negative NPMI coherence (-0.082) and low stability across seeds. "
        "We transformed all 302,026 questions to dominant topics, and exported top terms and representative question titles to topic_labels.csv "
        "and topic_examples.csv so Member 2 can perform blind independent human naming."
    )

    # =========================================================================
    # SLIDE 2 (Team Deck Slide 10): Topic Share Shifts and Distinctive Keywords
    # =========================================================================
    s2 = add_slide_base(
        prs,
        "NISHANTH / MEMBER 4",
        "What developers still bring to humans: topic share change and rising/falling words",
        10
    )
    
    # Left Card: Topic Share Shifts & Outcomes
    add_card(s2, Inches(0.6), Inches(1.55), Inches(5.9), Inches(5.25))
    
    tb_s2_l = s2.shapes.add_textbox(Inches(0.85), Inches(1.75), Inches(5.4), Inches(4.85))
    tf_s2_l = tb_s2_l.text_frame
    tf_s2_l.word_wrap = True
    
    p = tf_s2_l.paragraphs[0]
    p.text = "TOPIC SHARE PRE -> POST SHIFTS & RESOLUTION"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = TEAL_COLOR
    p.space_after = Pt(8)
    
    # Metrics
    shifts = [
        ("SURGING: Docker & Cloud Deployment (Topic 7)", "+27.7% relative (+1.49pp)", "[+1.31pp, +1.67pp]", "34.2% resolved | 1.95h latency", GREEN_COLOR),
        ("SURGING: Python Execution Errors (Topic 0)", "+14.8% relative (+1.85pp)", "[+1.62pp, +2.07pp]", "33.2% resolved | 1.58h latency", GREEN_COLOR),
        ("COLLAPSED: Core Syntax & Arrays (Topic 8)", "-17.0% relative (-3.50pp)", "[-3.75pp, -3.24pp]", "58.6% resolved | 0.32h latency", RED_COLOR),
        ("COLLAPSED: Pandas Data Manipulation (Topic 1)", "-10.7% relative (-1.13pp)", "[-1.34pp, -0.92pp]", "48.7% resolved | 0.65h latency", RED_COLOR)
    ]
    
    for title, change, ci, outcome, color in shifts:
        p_t = tf_s2_l.add_paragraph()
        r = p_t.add_run()
        r.text = title
        r.font.bold = True
        r.font.size = Pt(11)
        r.font.color.rgb = color
        
        p_d = tf_s2_l.add_paragraph()
        p_d.space_after = Pt(4)
        r_d = p_d.add_run()
        r_d.text = f"Share: {change} (95% CI {ci})\nOutcomes: {outcome}"
        r_d.font.size = Pt(10)
        r_d.font.color.rgb = MUTED_COLOR

    p_div = tf_s2_l.add_paragraph()
    p_div.space_after = Pt(2)
    r_div = p_div.add_run()
    r_div.text = "Operational Triage Finding:"
    r_div.font.bold = True
    r_div.font.size = Pt(11)
    r_div.font.color.rgb = WHITE_COLOR
    
    p_div_desc = tf_s2_l.add_paragraph()
    r_dd = p_div_desc.add_run()
    r_dd.text = "Questions AI cannot answer (Docker/Cloud, execution errors) are surging but suffer low community resolution (~34%), directly justifying expert routing queues."
    r_dd.font.size = Pt(10)
    r_dd.font.color.rgb = MUTED_COLOR

    # Right Card: Monroe et al. Distinctive Keyword Shift
    add_card(s2, Inches(6.8), Inches(1.55), Inches(5.95), Inches(5.25))
    
    tb_s2_r = s2.shapes.add_textbox(Inches(7.05), Inches(1.75), Inches(5.45), Inches(4.85))
    tf_s2_r = tb_s2_r.text_frame
    tf_s2_r.word_wrap = True
    
    p = tf_s2_r.paragraphs[0]
    p.text = "DISTINCTIVE KEYWORDS (MONROE LOG-ODDS)"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = TEAL_COLOR
    p.space_after = Pt(8)
    
    kw_info = [
        ("Methodology", "Weighted log-odds ratio with informative Dirichlet prior (Monroe, Colaresi & Quinn 2008). Avoids small-sample count bias."),
        ("Top Rising (Post-AI Surges)", "Modern build tools, web frameworks & deployment:\n"
         "- nextjs (z = +126.7), vite (z = +115.2)\n"
         "- version (z = +102.2), fastapi (z = +89.1)\n"
         "- docker (z = +83.6), openai (z = +77.3)"),
        ("Top Falling (Post-AI Collapses)", "Routine language syntax & basic operations:\n"
         "- array (z = -129.4), list (z = -96.6)\n"
         "- loop (z = -79.1), jquery (z = -68.8)\n"
         "- string (z = -64.2), element (z = -58.9)"),
        ("Tag-Level Nuance", "In Python, 'toml' and 'pyproject' surge (+35z) as packaging shifts, while basic 'list' and 'dataframe' fall sharply.")
    ]
    
    for title, text_val in kw_info:
        p_k = tf_s2_r.add_paragraph()
        r = p_k.add_run()
        r.text = f"{title}: "
        r.font.bold = True
        r.font.size = Pt(11)
        r.font.color.rgb = WHITE_COLOR
        
        p_kd = tf_s2_r.add_paragraph()
        p_kd.space_after = Pt(4)
        r_kd = p_kd.add_run()
        r_kd.text = text_val
        r_kd.font.size = Pt(10)
        r_kd.font.color.rgb = MUTED_COLOR
        
    s2.notes_slide.notes_text_frame.text = (
        "Speaker Notes (Nishanth / Member 4 - 1:30 min):\n"
        "Tracking monthly topic shares before and after AI adoption shows a clear structural divergence in what developers bring to human peers. "
        "Routine syntax questions—such as basic arrays, loops, and simple pandas dataframe indexing—experienced steep relative drops of 11% to 17%, "
        "confirming that developers now use LLMs for routine syntax lookups.\n\n"
        "Conversely, infrastructure and multi-system integration questions surged dramatically. Docker and Cloud Deployment rose +27.7% in relative share "
        "(+1.49 percentage points, bootstrap 95% CI +1.31 to +1.67pp), and Runtime Execution Errors rose +14.8% (+1.85pp). "
        "Crucially, these surging topics have the lowest 7-day resolution rates on Stack Overflow—only 34% resolve, taking nearly 2 hours for a first answer, "
        "compared to 59% resolved in 19 minutes for basic syntax. This provides concrete evidence for our recommendation to route rising topics to expert queues.\n\n"
        "Finally, the Monroe et al. weighted log-odds analysis confirms this vocabulary shift: modern ecosystem frameworks like Next.js, Vite, and FastAPI, "
        "along with versioning and deployment terms, show the strongest post-AI z-scores, whereas array, list, and loop show the steepest declines."
    )

    # Save presentation
    out_file = OUT / 'member4_review2_slides.pptx'
    prs.save(str(out_file))
    print(f"Successfully generated Member 4 slides: {out_file}", flush=True)


if __name__ == '__main__':
    build_deck()
