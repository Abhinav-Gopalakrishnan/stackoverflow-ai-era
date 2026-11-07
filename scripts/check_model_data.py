"""Audit duplicate/entity overlap and record model input checksums."""
from pathlib import Path
import json,hashlib
import pandas as pd
root=Path(__file__).resolve().parents[1];out=root/'reports/final_validation'
q=pd.read_parquet(root/'data/processed/questions_clean_v1.parquet',columns=['question_id','created_at','user_hash'])
periods={'training':('2019-02-26','2024-12-25'),'calibration':('2025-01-01','2025-04-01'),'threshold':('2025-04-08','2025-06-24'),'august_evaluation':('2026-08-01','2026-09-01')}
groups={k:q[(q.created_at>=a)&(q.created_at<b)] for k,(a,b) in periods.items()}
rows=[]
for name,d in groups.items():
 rows.append({'split':name,'rows':len(d),'unique_questions':d.question_id.nunique(),'known_users':d.user_hash.nunique(),'users_also_in_training':len(set(d.user_hash.dropna()) & set(groups['training'].user_hash.dropna())) if name!='training' else None})
audit={'question_ids_unique':bool(q.question_id.is_unique),'periods':periods,'groups':rows,
 'no_question_overlap':all(set(groups[a].question_id).isdisjoint(groups[b].question_id) for a in groups for b in groups if a<b),
 'entity_overlap_interpretation':'Returning askers can occur in later chronological splits. User hashes are excluded from predictors. This evaluates future questions in the same platform, not exclusively unseen users; it is not an entity-disjoint validation.',
 'unresolved_limitations':['Original posting-time text and tags were not reconstructed from revisions.','Acceptance-event timestamps are unavailable.','Training-window cleaning limits from the prior dataset remain part of its provenance.']}
(out/'model_data_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
meta_path=root/'models/resolution_v2/metadata.json';meta=json.loads(meta_path.read_text())
actual={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['data/processed/questions_clean_v1.parquet','data/processed/weekly_counts.csv']}
assert actual==meta['input_sha256'], 'Data differs from the fitted-model release; do not relabel model provenance.'
print(json.dumps(audit,indent=2))
