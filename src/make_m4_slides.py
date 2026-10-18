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
    import json
    import pandas as pd
    text=OUT/'text'
    status=json.loads((text/'topics_status.json').read_text())
    grid=pd.read_csv(text/'topic_model_selection.csv')
    chosen=grid[(grid.model_family==status['model_family'])&(grid.k==status['k'])].iloc[0]
    shifts=pd.read_csv(text/'topic_prepost.csv').merge(pd.read_csv(text/'topic_labels.csv'),on='topic')
    prs=Presentation();prs.slide_width=SLIDE_W;prs.slide_height=SLIDE_H
    def paragraph(slide, text, x,y,w,h,size=17):
        frame=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)).text_frame
        frame.word_wrap=True
        for line in text.split('\n'):
            p=frame.paragraphs[0] if not frame.paragraphs[0].text else frame.add_paragraph()
            p.text=line;p.font.size=Pt(size);p.font.color.rgb=WHITE_COLOR;p.font.name='Arial'
    s=add_slide_base(prs,'NISHANTH / MEMBER 4 — CORRECTED REFERENCE','Measured topic comparison and selection',1)
    paragraph(s,f"{chosen.model_family} k={int(chosen.k)} selected by the written rule\nDocument NPMI {chosen.coherence_npmi:.4f} | diversity {chosen.diversity:.3f} | stability {chosen.stability:.3f}",.6,1.5,12,1.1,19)
    s.shapes.add_picture(str(text/'topic_model_selection.png'),Inches(.6),Inches(2.7),width=Inches(12))
    paragraph(s,'Same training IDs and vocabulary; 3 seeds. Document NPMI differs from sliding-window c_npmi. Names are automatic; no human agreement claimed.',.6,6.35,12,.55,13)
    s.notes_slide.notes_text_frame.text='This reference replaces the superseded hardcoded grid. Read current per-seed results and protocol. Coherence is not accuracy.'
    s=add_slide_base(prs,'NISHANTH / MEMBER 4 — CORRECTED REFERENCE','Observed topic share changes',2)
    for i,(_,r) in enumerate(pd.concat([shifts.nsmallest(2,'change'),shifts.nlargest(2,'change')]).iterrows()):
        paragraph(s,f"T{int(r.topic)}: {r.final_name}\n{r.change*100:+.2f} pp; 95% CI [{r.lower95*100:+.2f}, {r.upper95*100:+.2f}] pp",.7,1.55+i*1.1,11.8,1.0,19)
    paragraph(s,'Weighted question bootstrap: 1,000 resamples. Pre/post excludes transition. Changes do not demonstrate AI substitution, difficulty or causality.',.7,6.15,11.8,.65,14)
    s.notes_slide.notes_text_frame.text='Topic names are automatic descriptions from this fitted model. Original topic IDs and human/AI labels are archived and cannot be transferred.'
    prs.save(OUT/'member4_review2_slides.pptx')
    print('Updated existing two-slide member reference from measured outputs; final team presentation is a separate task.')

if __name__=='__main__':build_deck()
