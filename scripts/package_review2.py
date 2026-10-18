"""Build a checksum-verified local submission, optionally with a separate full dataset."""
import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PREFIXES=('data/processed/','src/','tests/','dashboard/','docs/','notebooks/','reports/review1/m5/','reports/review2/','scripts/')
EXCLUDE=('reports/review2/archive/','reports/review2/member','notebooks/review1_main.ipynb','notebooks/colab_','src/make_white_decks.py','src/make_slides.py')

def checksum(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--include-dataset',action='store_true');args=parser.parse_args()
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    files=[]
    for name in tracked:
        if not name or not (name.startswith(PREFIXES) or name in ['README.md','requirements.txt','config.yaml','LICENSE']):continue
        if name.startswith(EXCLUDE) or name.endswith(('.pptx','.html')):continue
        if name.startswith('data/processed/') and not (name.endswith('.csv') or name.endswith('/README.md')):continue
        if name.startswith('notebooks/') and name not in ['notebooks/review2_main.ipynb','notebooks/07_timeseries.ipynb','notebooks/08_text_mining.ipynb','notebooks/01_collection.ipynb','notebooks/02_cleaning.ipynb','notebooks/04_features.ipynb','notebooks/05_models.ipynb','notebooks/06_evaluation.ipynb']:continue
        files.append(name)
    # Official template is included as an untouched reference, not as the final presentation.
    template='docs/review2_reference/Final_Project_Presentation_Template.pptx'
    if (ROOT/template).exists():files.append(template)
    files=sorted(set(files))
    out=ROOT/'submission';out.mkdir(exist_ok=True)
    manifest={'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        'presentation':'New final presentation is prepared in a subsequent task; member decks are excluded.',
        'files':[{'path':f,'bytes':(ROOT/f).stat().st_size,'sha256':checksum(ROOT/f)} for f in files]}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    archive=out/'review2_code_results.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for f in files:z.write(ROOT/f,f)
        z.write(out/'manifest.json','submission_manifest.json')
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    if args.include_dataset:
        path=ROOT/'data/processed/questions_clean_v1.parquet'
        expected=json.loads((ROOT/'reports/review2/dataset/dataset_validation.json').read_text())
        assert checksum(path)==expected['sha256']
        datazip=out/'review2_full_dataset.zip'
        with zipfile.ZipFile(datazip,'w',compression=zipfile.ZIP_STORED) as z:
            z.write(path,'data/processed/questions_clean_v1.parquet')
            z.write(ROOT/'reports/review2/dataset/dataset_validation.json','dataset_validation.json')
        with zipfile.ZipFile(datazip) as z:assert z.testzip() is None
    print(f'Created {archive}; {len(files)} files. ZIP integrity verified.')

if __name__=='__main__':main()
