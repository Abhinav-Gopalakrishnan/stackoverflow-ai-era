"""Build consolidated Review 2 team deck (13 slides).

Strategy:
- Slides 5,6 (M5), 7,8 (M2), 9,10 (M4): copied verbatim from existing member pptx,
  with slide-number footer re-mapped to the consolidated 1-13 sequence.
- Slides 1,2,3,4,11,12,13 (M1/M3): generated fresh in M2/M5 styling.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from copy import deepcopy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/review2'
TEXT = OUT / 'text'
TS = OUT / 'ts'
PRES = ROOT / 'presentations'

BG_COLOR = RGBColor(0x10,0x14,0x13)
PANEL_COLOR = RGBColor(0x1B,0x22,0x20)
TEAL_COLOR = RGBColor(0x38,0xDD,0xB5)
WHITE_COLOR = RGBColor(0xF4,0xF8,0xF6)
MUTED_COLOR = RGBColor(0xAA,0xB9,0xB5)
BORDER_COLOR = RGBColor(0x39,0x45,0x41)

SLIDE_W, SLIDE_H = Inches(13.333), Inches(7.5)
FONT = 'Arial'

def load_data():
    d={}
    try: d['its']=pd.read_csv(TS/'its_results.csv')
    except: d['its']=pd.DataFrame()
    try: d['sel']=pd.read_csv(TEXT/'topic_model_selection.csv')
    except: d['sel']=pd.DataFrame()
    try: d['rec']=pd.read_csv(OUT/'recommendations.csv')
    except: d['rec']=pd.DataFrame()
    try: d['prepost']=pd.read_csv(TEXT/'topic_prepost.csv')
    except: d['prepost']=pd.DataFrame()
    try: d['outcomes']=pd.read_csv(TEXT/'topic_outcomes.csv')
    except: d['outcomes']=pd.DataFrame()
    try: d['bw']=pd.read_csv(TS/'backtest_winners.csv')
    except: d['bw']=pd.DataFrame()
    return d

def _style_run(r, size, color, bold=False):
    r.font.size=Pt(size); r.font.color.rgb=color; r.font.bold=bold; r.font.name=FONT

def _style_para(p, size, color, bold=False, after=0, align=PP_ALIGN.LEFT, line_spacing=1.05):
    p.font.size=Pt(size); p.font.color.rgb=color; p.font.bold=bold; p.font.name=FONT
    p.space_after=Pt(after); p.alignment=align
    try: p.line_spacing=line_spacing
    except: pass

def add_text(s, left, top, width, height, lines, align=PP_ALIGN.LEFT, valign='top'):
    tb=s.shapes.add_textbox(left, top, width, height)
    tf=tb.text_frame; tf.word_wrap=True; tf.margin_left=Pt(0); tf.margin_right=Pt(0); tf.margin_top=Pt(0); tf.margin_bottom=Pt(0)
    try: tf.vertical_anchor = {'top':1,'middle':2,'bottom':3}[valign]
    except: pass
    first=True
    for ln in lines:
        text, size, color, bold, after = ln
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first=False
        r=p.add_run(); r.text=text
        _style_run(r, size, color, bold=bold)
        _style_para(p, size, color, bold=bold, after=after, align=align)
    return tb

def add_rich_text(s, left, top, width, height, runs_list, align=PP_ALIGN.LEFT, after=6, line_spacing=1.1):
    tb=s.shapes.add_textbox(left, top, width, height)
    tf=tb.text_frame; tf.word_wrap=True; tf.margin_left=Pt(0); tf.margin_right=Pt(0); tf.margin_top=Pt(0); tf.margin_bottom=Pt(0)
    first=True
    for runs in runs_list:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first=False
        p.space_after=Pt(after); p.alignment=align
        try: p.line_spacing=line_spacing
        except: pass
        for text, size, color, bold in runs:
            r=p.add_run(); r.text=text
            _style_run(r, size, color, bold=bold)
    return tb

def base_slide(prs, num, speaker, title):
    blank=prs.slide_layouts[6]
    s=prs.slides.add_slide(blank)
    bg=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,0,0,SLIDE_W,SLIDE_H)
    bg.fill.solid(); bg.fill.fore_color.rgb=BG_COLOR; bg.line.color.rgb=BG_COLOR
    add_text(s, Inches(0.60),Inches(0.32),Inches(12.00),Inches(0.24), [(speaker, 10, TEAL_COLOR, True, 0)])
    add_text(s, Inches(0.60),Inches(0.75),Inches(12.10),Inches(0.72), [(title, 28, WHITE_COLOR, True, 0)])
    add_text(s, Inches(0.60),Inches(7.12),Inches(11.00),Inches(0.20), [('STACK OVERFLOW IN THE AI ERA / REVIEW 2', 9, MUTED_COLOR, False, 0)])
    n=s.shapes.add_textbox(Inches(12.30),Inches(7.12),Inches(0.40),Inches(0.20))
    tf_n=n.text_frame; tf_n.margin_top=Pt(0); tf_n.margin_bottom=Pt(0)
    p=tf_n.paragraphs[0]; p.text=str(num); p.alignment=PP_ALIGN.RIGHT
    _style_para(p, 9, MUTED_COLOR, bold=False)
    return s

def card(s,left,top,width,height):
    sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,left,top,width,height)
    sh.fill.solid(); sh.fill.fore_color.rgb=PANEL_COLOR; sh.line.color.rgb=BORDER_COLOR; sh.line.width=Pt(0.75)
    sh.adjustments[0] = 0.045
    return sh

def section_header(s, left, top, width, text):
    add_text(s, left, top, width, Inches(0.30), [(text.upper(), 13, TEAL_COLOR, True, 0)])

def body_block(s, left, top, width, height, items):
    runs_list=[]
    for lead, detail in items:
        runs=[(lead+': ', 16, WHITE_COLOR, True), (detail, 16, MUTED_COLOR, False)]
        runs_list.append(runs)
    add_rich_text(s, left, top, width, height, runs_list, after=7)

def metric_row(s, left, top, width, height, number, label, size=29):
    add_text(s, left, top, width, height, [(number, size, TEAL_COLOR, True, 0)])
    add_text(s, left, top+Inches(0.62), width, Inches(0.30), [(label, 15, MUTED_COLOR, False, 0)])

def table(s, left, top, col_widths, rows, header_fill=TEAL_COLOR, header_color=BG_COLOR,
          row_h=0.42, head_h=0.42, size=11, aligns=None):
    total=sum(col_widths)
    cx=[left]
    for wd in col_widths[:-1]: cx.append(cx[-1]+wd)
    yy=top
    for i,row in enumerate(rows):
        hh = head_h if i==0 else row_h
        if i==0:
            rf=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, yy, total, hh)
            rf.fill.solid(); rf.fill.fore_color.rgb=header_fill; rf.line.color.rgb=header_fill
            rf.adjustments[0]=0.12
        for j,cell in enumerate(row):
            al = aligns[j] if aligns else (PP_ALIGN.LEFT if j==0 else PP_ALIGN.CENTER)
            tb=s.shapes.add_textbox(Inches(cx[j]+0.08), Inches(yy), Inches(col_widths[j]-0.16), Inches(hh))
            tf=tb.text_frame; tf.word_wrap=True; tf.margin_left=Pt(0); tf.margin_right=Pt(0); tf.margin_top=Pt(0); tf.margin_bottom=Pt(0)
            p=tf.paragraphs[0]; p.text=str(cell); p.alignment=al
            bold = (i==0) or (j==0)
            color = header_color if i==0 else WHITE_COLOR
            _style_para(p, size, color, bold=bold, after=0, line_spacing=1.0)
            try: tf.vertical_anchor=2
            except: pass
        yy+=hh
    return total

def _fix_slide_number(slide, new_num):
    """Find the slide-number textbox (bottom-right) and set its text to new_num."""
    for shp in slide.shapes:
        if not (hasattr(shp,'has_text_frame') and shp.has_text_frame): continue
        tf = shp.text_frame
        if not tf.paragraphs or not tf.paragraphs[0].runs: continue
        txt = tf.paragraphs[0].text.strip()
        if txt.isdigit() and len(txt) <= 2:
            # only the footer number box (position ~12.3, 7.12)
            if shp.left and shp.left > Emu(11*914400) and shp.top and shp.top > Emu(6.5*914400):
                p = tf.paragraphs[0]
                # clear runs and set new text
                for r in list(p.runs):
                    r.text = ''
                p.text = str(new_num)
                for r in p.runs:
                    _style_para(p, 9, MUTED_COLOR, bold=False)
                return True
    return False

def copy_slide(src_pres, src_idx, dst_pres, new_num, new_speaker=None, new_title=None):
    """Copy a slide from src into dst by deep-copying each shape's XML element."""
    from io import BytesIO
    src_slide = src_pres.slides[src_idx]
    dst_slide = dst_pres.slides.add_slide(dst_pres.slide_layouts[6])

    for shp in src_slide.shapes:
        el = deepcopy(shp.element)
        blip_els = el.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
        if blip_els:
            # embedded picture: extract image bytes and re-add via add_picture
            embed = blip_els[0].get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            if embed:
                src_image_part = src_slide.part.rels[embed].target_part
                image_bytes = src_image_part.blob
                # skip adding deep-copied element; add picture fresh below
                el = None
        if el is not None:
            dst_slide.shapes._spTree.insert_element_before(el, 'p:extLst')

    # re-add pictures at their original positions
    for shp in src_slide.shapes:
        if shp.shape_type == MSO_SHAPE_TYPE.PICTURE:
            try:
                image = shp.image
                image_bytes = image.blob
                dst_slide.shapes.add_picture(
                    BytesIO(image_bytes),
                    shp.left, shp.top, shp.width, shp.height
                )
            except Exception:
                pass

    # renumber footer
    _fix_slide_number(dst_slide, new_num)
    # optionally replace speaker tag (top-left, y~0.32) and title text (y~0.75)
    if new_speaker or new_title:
        for shp in dst_slide.shapes:
            if not (hasattr(shp,'has_text_frame') and shp.has_text_frame): continue
            if shp.left is None or shp.top is None: continue
            left_in = shp.left / 914400
            top_in = shp.top / 914400
            tf = shp.text_frame
            if not tf.paragraphs: continue
            p = tf.paragraphs[0]
            if not p.runs: continue
            txt = p.text.strip()
            if new_speaker and abs(left_in - 0.60) < 0.05 and abs(top_in - 0.32) < 0.05:
                p.text = new_speaker
                _style_para(p, 10, TEAL_COLOR, bold=True)
            elif new_title and abs(left_in - 0.60) < 0.05 and abs(top_in - 0.75) < 0.10:
                p.text = new_title
                _style_para(p, 28, WHITE_COLOR, bold=True)
    return dst_slide

def main():
    d = load_data()
    its=d['its']; sel=d['sel']; rec=d['rec']; pre=d['prepost']; out=d['outcomes']; bw=d['bw']

    prs = Presentation()
    prs.slide_width, prs.slide_height = SLIDE_W, SLIDE_H

    # ---- Remove the default blank slide that Presentation() creates ----
    # xml: first slide layout placeholder; we'll just add 13 slides and it'll be 14 total
    # Actually Presentation() starts with 0 slides. Let's verify and proceed.

    # Slide order map: consolidated position -> (source_file, source_index, new_num, speaker, title)
    # source_index is 0-based within that file
    copies = [
        # M5 slides 5,6 (source idx 0,1 -> consolidated 5,6)
        (5, 'member5_review2_slides.pptx', 0, 5, 'MEMBER 5 / ADHIKKESH', 'Forecast Setup: Baselines, Rolling Origin, Leakage Control'),
        (6, 'member5_review2_slides.pptx', 1, 6, 'MEMBER 5 / ADHIKKESH', 'Forecast Results: 26-week Horizons + Skill vs Naive'),
        # M2 slides 7,8 (source idx 0,1 -> consolidated 7,8)
        (7, 'member2_review2_slides.pptx', 0, 7, 'MEMBER 2 / RISHIIKESH', 'Text Preparation: Cleaning, Sampling, NMF Corpus'),
        (8, 'member2_review2_slides.pptx', 1, 8, 'MEMBER 2 / RISHIIKESH', 'Tone & Complexity (VADER + Structural Metrics)'),
        # M4 slides 9,10 (source idx 0,1 -> consolidated 9,10; numbers already match)
        (9, 'member4_review2_slides.pptx', 0, 9, 'MEMBER 4 / NISHANTH', 'Topic Model Choice: Coherence, Diversity, Stability, Human Agreement'),
        (10,'member4_review2_slides.pptx', 1, 10,'MEMBER 4 / NISHANTH', 'Topic Shifts + Distinctive Keywords (Monroe)'),
    ]

    # Add copied slides in order. But pptx slide order is determined by insertion order,
    # so we need to insert generated slides at the right positions too.
    # Strategy: build the full sequence, inserting generated slides between copies.
    # We'll collect all operations as (position, kind, data) and execute in order.

    generated = {
        1:  ('M1', 'Title, Team & Methodological Evolution since Review 1', 'MEMBER 1 / ABHINAV'),
        2:  ('M1', 'RQ4/RQ5 & Two Methods (Rubric Order)', 'MEMBER 1 / ABHINAV'),
        3:  ('M3', 'Patterns: Trend & Yearly Seasonality per Tag (STL)', 'MEMBER 3 / AKSHAY'),
        4:  ('M3', 'Nov 2022 Break: Changepoints + Segmented ITS (with Placebo)', 'MEMBER 3 / AKSHAY'),
        11: ('M1', 'Dashboard Demo: Explore All Findings', 'MEMBER 1 / ABHINAV'),
        12: ('M3', 'Combined Recommendations (Evidence-Linked)', 'MEMBER 3 / AKSHAY'),
        13: ('M1', 'Limitations, Governance & Team Contributions', 'MEMBER 1 / ABHINAV'),
    }

    copy_map = {pos: (fname, sidx, num, spk, title) for pos, fname, sidx, num, spk, title in copies}

    # Open source presentations once
    src_pres = {}
    for fname in set(fname for _,fname,_,_,_,_ in copies):
        src_pres[fname] = Presentation(str(OUT/fname))

    for pos in range(1, 14):
        if pos in copy_map:
            fname, sidx, num, spk, title = copy_map[pos]
            copy_slide(src_pres[fname], sidx, prs, num, new_speaker=spk, new_title=title)
        else:
            _, title, speaker = generated[pos]
            gen_slide(prs, pos, speaker, title, d)

    out = PRES/'review2_team_deck.pptx'
    prs.save(str(out))
    print('Saved', out, 'with', len(prs.slides.__iter__.__self__._sldIdLst), 'slides')

def gen_slide(prs, num, speaker, title, d):
    its=d['its']; sel=d['sel']; rec=d['rec']; pre=d['prepost']; out=d['outcomes']; bw=d['bw']

    if num == 1:
        s=base_slide(prs,1,speaker,title)
        card(s,Inches(0.6),Inches(1.72),Inches(7.02),Inches(4.88))
        section_header(s, Inches(0.9), Inches(2.02), Inches(6.4), 'About')
        body_block(s, Inches(0.9), Inches(2.42), Inches(6.4), Inches(4.0), [
            ('Project','Stack Overflow in the AI Era: Macro Trajectories & Content Evolution'),
            ('Team','Member 1: Abhinav; Member 2: Rishiikesh; Member 3: Akshay; Member 4: Nishanth; Member 5: Adhikkesh'),
            ('Upgrades','Zero leakage, benchmarked against naive/drift with Diebold-Mariano, reproducible notebooks, 2021 placebo for ITS.'),
            ('Reproducibility','All notebooks execute top-to-bottom; 27 CSVs under 1.62 MB; CC BY-SA 4.0.'),
        ])
        card(s,Inches(7.88),Inches(1.72),Inches(4.85),Inches(4.88))
        section_header(s, Inches(8.2), Inches(2.02), Inches(4.3), 'Scope')
        body_block(s, Inches(8.2), Inches(2.42), Inches(4.3), Inches(4.0), [
            ('Tags','13 curated technologies, 400 weeks per tag.'),
            ('Period','Pre/post break around Nov 2022; forecasts to Feb 2027.'),
            ('Methods','STL, changepoints, segmented ITS, NMF topics, VADER, rolling-origin backtests.'),
            ('Data','27 schema-validated CSVs <1.62 MB; CC BY-SA 4.0.'),
        ])
        s.notes_slide.notes_text_frame.text='Team structure and Review 1->Review 2 upgrades.'

    elif num == 2:
        s=base_slide(prs,2,speaker,title)
        card(s,Inches(0.6),Inches(1.72),Inches(7.02),Inches(4.88))
        section_header(s, Inches(0.9), Inches(2.02), Inches(6.4), 'Research Questions')
        body_block(s, Inches(0.9), Inches(2.42), Inches(6.4), Inches(4.0), [
            ('RQ5 (Technology Forecasting)','STL, ADF/KPSS, PELT, segmented ITS + 2021 placebo, rolling-origin backtests.'),
            ('RQ4 (Topic & Complexity Shifts)','NMF (k=10 selected), Monroe log-odds, VADER, 1000-resample bootstrap CIs.'),
            ('Focus','Structural breaks; topics/complexity; forecasts with intervals.'),
        ])
        card(s,Inches(7.88),Inches(1.72),Inches(4.85),Inches(4.88))
        section_header(s, Inches(8.2), Inches(2.02), Inches(4.3), 'Scale & Validation')
        body_block(s, Inches(8.2), Inches(2.42), Inches(4.3), Inches(4.0), [
            ('Corpus','400 weeks per tag across 13 technologies.'),
            ('Backtest','Rolling-origin; model parameters locked pre-fit.'),
            ('Significance','Diebold-Mariano vs naive/drift baselines.'),
        ])
        s.notes_slide.notes_text_frame.text='RQ mapping corrected: RQ4 topics/complexity, RQ5 forecasting.'

    elif num == 3:
        s=base_slide(prs,3,speaker,title)
        card(s,Inches(0.6),Inches(1.72),Inches(7.02),Inches(4.88))
        section_header(s, Inches(0.9), Inches(2.02), Inches(6.4), 'Method')
        body_block(s, Inches(0.9), Inches(2.42), Inches(6.4), Inches(4.0), [
            ('Decomposition','STL robust seasonal-trend decomposition (period 52).'),
            ('Scope','400 weeks, 13 curated tags.'),
            ('Takeaway','Visible yearly seasonality; strong declines post-Nov 2022 for many tags.'),
        ])
        from pathlib import Path as _P
        img=_P(ROOT)/'reports/review2/ts/stl_small_multiples.png'
        if img.exists():
            card(s,Inches(7.88),Inches(1.72),Inches(4.85),Inches(4.88))
            s.shapes.add_picture(str(img),Inches(8.05),Inches(1.95),Inches(4.55),Inches(4.5))
        s.notes_slide.notes_text_frame.text='STL seasonal-trend decomposition per tag.'

    elif num == 4:
        s=base_slide(prs,4,speaker,title)
        card(s,Inches(0.6),Inches(1.72),Inches(5.0),Inches(4.88))
        section_header(s, Inches(0.9), Inches(2.02), Inches(4.4), 'Segmented ITS')
        py=-2.34
        if len(its)>0:
            try:
                sub=its[its.tag=='python']
                if len(sub)>0: py=float(sub.iloc[0].get('slope_change_pct', -2.34))
            except Exception: pass
        body_block(s, Inches(0.9), Inches(2.42), Inches(4.4), Inches(4.0), [
            ('Break','Most tags show significant post-break slope decline; placebo (2021) fails.'),
            ('Example (python)','Slope change ~ %.2f%%/wk post-intervention.'%py),
            ('Placebo','2021 placebo rejects spurious seasonality.'),
        ])
        metric_row(s, Inches(0.9), Inches(5.62), Inches(4.4), Inches(0.8), '%.2f%%/wk'%py, 'python slope change (post-break)', size=22)
        img=ROOT/'reports/review2/ts/its_forest.png'
        if img.exists():
            card(s,Inches(6.0),Inches(1.72),Inches(6.73),Inches(4.88))
            s.shapes.add_picture(str(img),Inches(6.15),Inches(1.95),Inches(6.4),Inches(4.5))
        s.notes_slide.notes_text_frame.text='Segmented ITS with 2021 placebo; python slope change -2.34%/wk.'

    elif num == 11:
        s=base_slide(prs,11,speaker,title)
        card(s,Inches(0.6),Inches(1.72),Inches(7.02),Inches(4.88))
        section_header(s, Inches(0.9), Inches(2.02), Inches(6.4), 'Live Dashboard')
        body_block(s, Inches(0.9), Inches(2.42), Inches(6.4), Inches(4.0), [
            ('URL','https://stackoverflow-ai-era.streamlit.app'),
            ('Pages','Overview, Patterns & 2022 Break, Forecasts, Topics, Tone & Complexity, Recommendations.'),
            ('Highlights','Python ITS -2.34%/wk (p<0.001); 6 steep-decline tags; runtime error topics 33.2% resolve in 7d.'),
            ('Bands','80%/95% intervals; synchronized cross-page state.'),
        ])
        card(s,Inches(7.88),Inches(1.72),Inches(4.85),Inches(4.88))
        section_header(s, Inches(8.2), Inches(2.02), Inches(4.3), 'Governance')
        body_block(s, Inches(8.2), Inches(2.42), Inches(4.3), Inches(4.0), [
            ('Data','27 schema-validated CSVs <1.62 MB, CC BY-SA 4.0.'),
            ('Repo','abhinav-gopalakrishnan/stackoverflow-ai-era.'),
            ('Tests','54 tests passing.'),
        ])
        s.notes_slide.notes_text_frame.text='Dashboard demo: explore all findings.'

    elif num == 12:
        s=base_slide(prs,12,speaker,title)
        card(s,Inches(0.6),Inches(1.72),Inches(12.13),Inches(4.88))
        section_header(s, Inches(0.9), Inches(2.02), Inches(11.5), 'Recommendations')
        if len(rec)>0:
            runs_list=[]
            for i,row in rec.head(6).iterrows():
                t=str(row.get('finding','Rec')); act=str(row.get('action','')); aud=str(row.get('stakeholder',''))
                runs_list.append([('%s -> %s: '%(t,aud), 13, WHITE_COLOR, True), (act, 13, MUTED_COLOR, False)])
            add_rich_text(s, Inches(0.9), Inches(2.42), Inches(11.5), Inches(4.0), runs_list, after=7)
        else:
            add_text(s, Inches(0.9), Inches(2.42), Inches(11.5), Inches(4.0), [('Recommendations loaded from reports/review2/recommendations.csv.', 13, MUTED_COLOR, False, 0)])
        s.notes_slide.notes_text_frame.text='Combined recommendations, evidence-linked.'

    elif num == 13:
        s=base_slide(prs,13,speaker,title)
        card(s,Inches(0.6),Inches(1.72),Inches(7.02),Inches(4.88))
        section_header(s, Inches(0.9), Inches(2.02), Inches(6.4), 'Limitations')
        body_block(s, Inches(0.9), Inches(2.42), Inches(6.4), Inches(4.0), [
            ('Scope','Weights pre-2025; 13 tags scope; resolution proxy; VADER lexicon; English-only.'),
            ('Causality','Association≠cause; steep-decline uncertainty.'),
        ])
        card(s,Inches(7.88),Inches(1.72),Inches(4.85),Inches(4.88))
        section_header(s, Inches(8.2), Inches(2.02), Inches(4.3), 'Contributions')
        body_block(s, Inches(8.2), Inches(2.42), Inches(4.3), Inches(4.0), [
            ('M1','Dashboard & synthesis.'),
            ('M2','Text prep / tone & complexity.'),
            ('M3','STL / changepoints / ITS / recommendations.'),
            ('M4','Topics / keywords / model choice.'),
            ('M5','Forecasts / backtests.'),
        ])
        s.notes_slide.notes_text_frame.text='Limitations, governance, team contributions.'

if __name__=='__main__':
    main()
