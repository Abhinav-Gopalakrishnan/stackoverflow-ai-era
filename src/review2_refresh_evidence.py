"""Refresh light findings, chart captions and provenance from current saved results."""
import json
import pandas as pd
from src.review2_common import ROOT, TEXT, TS, write_json

R=ROOT/'reports/review2'

def main():
    status=json.loads((TEXT/'topics_status.json').read_text())
    selection=pd.read_csv(TEXT/'topic_model_selection.csv')
    winner=selection[(selection.model_family==status['model_family'])&(selection.k==status['k'])].iloc[0]
    labels=pd.read_csv(TEXT/'topic_labels.csv').set_index('topic')
    change=pd.read_csv(TEXT/'topic_prepost.csv').sort_values('change')
    k=winner.k
    finding=[f"Measured selection: {winner.model_family} k={int(k)}; document NPMI {winner.coherence_npmi:.4f}, diversity {winner.diversity:.3f}, three-seed stability {winner.stability:.3f}.",
        f"Both families use {status['training_rows']:,} identical training IDs, a shared vocabulary and {status['reference_rows']:,} disjoint reference questions. Document NPMI is explicitly different from sliding-window c_npmi.",
        f"Transformed {status['corpus_rows']:,} questions; {status['zero_projection_documents']:,} zero-vocabulary records have no assigned topic.",
        'Names are automatic top-term descriptions; independent human naming agreement is unavailable. Old model IDs/names are archived.']
    for direction,group in [('Largest decreases',change.head(3)),('Largest increases',change.tail(3).iloc[::-1])]:
        finding.append(direction+': '+'; '.join(f"T{r.topic} {labels.loc[r.topic,'final_name']}: {r.change*100:+.2f} pp (95% CI {r.lower95*100:+.2f} to {r.upper95*100:+.2f})" for r in group.itertuples()))
    finding.append('These are changes within the observed collection. They do not demonstrate AI offloading, topic difficulty or causal effects. Keyword rankings remain a separate saved analysis.')
    (R/'m4_findings.md').write_text('# Topics and keywords — corrected findings\n\n'+'\n'.join('- '+f for f in finding)+'\n')
    (R/'m4_viva.md').write_text('# Topic analysis: viva\n\n'+ '\n'.join('- '+f for f in finding)+'\n\n- Why three seeds? To measure sensitivity to initialisation.\n- Why bootstrap? To estimate question-sampling uncertainty while retaining historic weights.\n- Is NPMI accuracy? No; it measures term cooccurrence coherence.\n')
    tone=json.loads((TEXT/'tone_validation_status.json').read_text())
    (R/'m2_findings.md').write_text('# Tone and complexity — corrected evidence\n\n'+
        f"- Corpus: {status['corpus_rows']:,} questions. Code is excluded from topic/tone prose and measured separately for complexity.\n"+
        f"- VADER vs 200 existing M3 human labels: {tone['accuracy']:.1%} accuracy, macro F1 {tone['macro_f1']:.3f}.\n"+
        f"- AI–human agreement: {tone['ai_human_agreement']:.1%}, kappa {tone['ai_human_kappa']:.3f}; this is not two-human validation.\n"+
        '- Frustration phrases are exploratory, not a validated emotion classifier.\n'+
        '- Current topic names are automatic descriptions; archived AI names do not apply to the corrected model.\n'+
        '- All pre/post estimates retain survey weights and exclude the transition; inspect saved intervals.\n')
    text_caps=[('Topic model comparison','topic_model_selection.png',finding[0],'Document NPMI; three seeds; no human naming agreement.'),
        ('Topic shifts','topic_prepost_by_tag.csv','Use actual weighted within-tag changes with 1,000-resample confidence intervals.','Automatic names; observed associations, not destination traffic.'),
        ('Tone and complexity','tone_complexity.png',f"VADER accuracy {tone['accuracy']:.1%} against one human reference.",'Weak sentiment validity; technical phrasing and one-rater subjectivity.'),
        ('Frustration phrases','tone_prepost.csv','Compare phrase shares with their confidence intervals.','Phrase flags are not independently validated emotions.'),
        ('Complexity intervals','complexity_prepost.csv','Compare weighted medians/means under fixed pre/post periods.','Reading ease is imperfect for technical prose.')]
    pd.DataFrame(text_caps,columns=['chart','file','takeaway','caveat']).to_csv(TEXT/'dashboard_captions.csv',index=False)
    for folder,owner in [(TEXT,'Original M2/M4 with disclosed corrections integration'),(TS,'M3/M5')]:
        write_json(folder/'dashboard_handoff.json',{'owner':owner,'schemas':{p.name:list(pd.read_csv(p,nrows=0).columns) for p in folder.glob('*.csv')},'captions_file':'dashboard_captions.csv','full_parquet_not_for_dashboard':True,'license':'CC BY-SA 4.0 title-only examples and canonical links'})
    print('Refreshed current findings and method handoff schemas.')

if __name__=='__main__':main()
