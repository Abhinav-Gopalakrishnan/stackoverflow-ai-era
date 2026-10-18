"""Read-only final artifact consistency checks; never refresh exports before checking."""
import json
import hashlib
import re
import subprocess
import sys
from pathlib import Path
import nbformat
import numpy as np
import pandas as pd
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.export_dashboard_data import EXPORT_SPECS, DATA_DIR, FORBIDDEN_COLUMNS


def main():
    checks=[]
    total=0
    for name,spec in EXPORT_SPECS.items():
        expected=pd.read_csv(spec['src'])[spec['columns']]
        actual=pd.read_csv(DATA_DIR/name)
        pd.testing.assert_frame_equal(expected,actual,check_dtype=False)
        assert not FORBIDDEN_COLUMNS.intersection(actual.columns)
        total+=(DATA_DIR/name).stat().st_size
    assert total < 50*1024*1024
    checks.append(f'{len(EXPORT_SPECS)} shipped CSV exports equal their current sources; {total} bytes; no forbidden fields')
    v=json.loads((ROOT/'reports/review2/dataset/dataset_validation.json').read_text())
    assert v['all_passed'] and v['rows']==302026 and v['columns']==39
    sample=pd.read_csv(ROOT/'reports/review2/dataset/final_dataset_sample.csv')
    assert len(sample)==40 and sample.question_id.is_unique
    checks.append('Final dataset: 302026 unique rows, 39 columns, eight checks pass; 40 sanitized linked samples')
    model=json.loads((ROOT/'reports/review2/text/topics_status.json').read_text())
    grid=pd.read_csv(ROOT/'reports/review2/text/topic_model_selection.csv')
    assert len(grid)==12 and grid.seeds.eq(3).all()
    naming=json.loads((ROOT/'reports/review2/text/topic_naming_status.json').read_text())
    assert naming['model_fingerprint']==model['fingerprint']
    assert not naming['original_two_human_requirement_complete']
    checks.append('Measured topic grid and current automatic naming provenance are consistent')
    tone=pd.read_csv(DATA_DIR/'tone_validation.csv').iloc[0]
    assert tone.accuracy==.36 and pd.isna(tone.human_human_kappa)
    assert tone.label_m2==0 and tone.label_m3==200 and tone.label_ai==200
    checks.append('AI annotations remain separate from human labels and adjudication')
    notebooks={}
    for name in ['review2_main','07_timeseries','08_text_mining']:
        nb=nbformat.read(ROOT/f'notebooks/{name}.ipynb',as_version=4)
        code=[c for c in nb.cells if c.cell_type=='code']
        assert code and all(c.execution_count is not None for c in code)
        assert not any(o.output_type=='error' for c in code for o in c.outputs)
        notebooks[name]=len(code)
    checks.append(f'Genuinely executed notebooks without errors: {notebooks}')
    report=ROOT/'reports/review2/final_report.pdf'
    pdf=PdfReader(report)
    txt='\n'.join(p.extract_text() or '' for p in pdf.pages)
    assert 'TODO' not in txt and 'NMF k=10 wins' not in txt
    images=len({hashlib.sha256(im.data).hexdigest() for p in pdf.pages for im in p.images})
    assert images>=6
    for n in range(1,6): assert (ROOT/f'reports/review2/contribution_member{n}.md').exists()
    checks.append(f'Report: {len(pdf.pages)} pages, {images} embedded images, no TODO markers; five member contributions present')
    print(json.dumps({'status':'pass','checks':checks,'notebooks':notebooks,'pdf_pages':len(pdf.pages),'pdf_images':images},indent=2))

if __name__=='__main__':main()
