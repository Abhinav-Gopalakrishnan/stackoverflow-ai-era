"""Disclosed single-human and AI-assisted checks; never fabricate human labels.

Run: python -m src.review2_validation
The original two-human annotation columns are preserved for later human input.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, cohen_kappa_score, confusion_matrix, f1_score

from src.review2_common import ROOT, TEXT, write_json

LABELS = ['negative', 'neutral', 'positive']


def summarize_tone(sheet_path=None):
    sheet_path = Path(sheet_path or TEXT / 'tone_validation_sample.csv')
    sheet = pd.read_csv(sheet_path, encoding='utf-8-sig')
    if len(sheet) != 200 or not sheet.question_id.is_unique:
        raise ValueError('Expected the original 200 unique sampled question IDs')
    if sheet.period.value_counts().to_dict() != {'post': 100, 'pre': 100}:
        raise ValueError('Expected 100 pre and 100 post questions')
    counts = {}
    for column in ['label_m2', 'label_m3', 'agreed_tone']:
        values = sheet[column].dropna()
        if not values.isin(LABELS).all():
            raise ValueError(f'Invalid labels in {column}')
        counts[column] = int(sheet[column].isin(LABELS).sum())
    predictions = pd.read_parquet(
        ROOT / 'data/processed/question_tone_v1.parquet', columns=['question_id', 'tone'])
    scored = sheet.merge(predictions, on='question_id', validate='one_to_one')
    if len(scored) != 200:
        raise ValueError('Scored sample IDs do not match the original sample')
    result = dict(required_rows=200, **counts, accuracy=None, macro_f1=None,
                  cohen_kappa=None, human_human_kappa=None,
                  original_two_human_requirement_complete=False)
    ai_path = TEXT / 'tone_ai_annotations.csv'
    if counts['label_m2'] == counts['label_m3'] == counts['agreed_tone'] == 200:
        reference = scored.agreed_tone
        result.update(status='complete', labelled_rows=200,
                      reference='Two-human adjudicated agreed_tone',
                      original_two_human_requirement_complete=True)
        result['cohen_kappa'] = result['human_human_kappa'] = float(
            cohen_kappa_score(scored.label_m2, scored.label_m3, labels=LABELS))
    elif counts['label_m3'] == 200 and ai_path.exists():
        ai = pd.read_csv(ai_path)
        if len(ai) != 200 or not ai.question_id.is_unique or not ai.label_ai.isin(LABELS).all():
            raise ValueError('AI annotations must cover all 200 unique sample IDs')
        scored = scored.merge(ai, on='question_id', validate='one_to_one')
        if len(scored) != 200:
            raise ValueError('AI annotation IDs do not match the original sample')
        reference = scored.label_m3
        result.update(
            status='complete_ai_assisted', labelled_rows=200, label_ai=200,
            reference='Akshay/M3 single-human labels; no adjudicated gold standard',
            ai_human_kappa=float(cohen_kappa_score(scored.label_m3, scored.label_ai, labels=LABELS)),
            ai_human_agreement=float(accuracy_score(scored.label_m3, scored.label_ai)),
            ai_macro_f1_vs_human=float(f1_score(scored.label_m3, scored.label_ai,
                                              labels=LABELS, average='macro', zero_division=0)),
            annotation_file_sha256=hashlib.sha256(ai_path.read_bytes()).hexdigest(),
            limitation='AI annotation is not a second independent human rating. '
                       'Original two-human kappa/adjudication remains unavailable.')
        scored['ai_matches_m3'] = scored.label_ai.eq(scored.label_m3)
        scored[['question_id', 'period', 'title', 'link', 'label_ai', 'label_m3',
                'ai_matches_m3', 'rationale', 'annotation_source']].to_csv(
                    TEXT / 'tone_rater_comparison.csv', index=False)
    else:
        result.update(status='awaiting_independent_human_labels', labelled_rows=0,
                      reference='Unavailable: complete human reference not supplied')
        pd.DataFrame([result]).to_csv(TEXT / 'tone_validation.csv', index=False)
        write_json(TEXT / 'tone_validation_status.json', result)
        return result
    result.update(accuracy=float(accuracy_score(reference, scored.tone)),
                  macro_f1=float(f1_score(reference, scored.tone, labels=LABELS,
                                          average='macro', zero_division=0)))
    for name, predicted in [('tone_confusion.csv', scored.tone)]:
        pd.DataFrame(confusion_matrix(reference, predicted, labels=LABELS),
                     index=LABELS, columns=LABELS).rename_axis('actual').to_csv(TEXT / name)
    if 'label_ai' in scored:
        pd.DataFrame(confusion_matrix(reference, scored.label_ai, labels=LABELS),
                     index=LABELS, columns=LABELS).rename_axis('human_m3').to_csv(
                         TEXT / 'tone_ai_human_confusion.csv')
    pd.DataFrame([result]).to_csv(TEXT / 'tone_validation.csv', index=False)
    write_json(TEXT / 'tone_validation_status.json', result)
    return result


def summarize_topics():
    names = pd.read_csv(TEXT / 'topic_labels.csv')
    model_status = json.loads((TEXT/'topics_status.json').read_text())
    if 'label_source' in names and names.label_source.eq('automatic top-term rules').all():
        result = dict(status='automatic_descriptions_not_human_validation', topics=len(names),
            model_fingerprint=model_status['fingerprint'], human_m2_names=int(names.name_m2.notna().sum()),
            human_m4_names=int(names.name_m4.notna().sum()), ai_names=0,
            original_two_human_requirement_complete=False, human_naming_agreement=None,
            interpretation='Automatic descriptions derived from current top terms; old model AI names archived',
            limitation='No independent human naming agreement. IDs and archived names from the previous model are not transferable.')
        write_json(TEXT/'topic_naming_status.json',result)
        return result
    ai = pd.read_csv(TEXT / 'topic_ai_annotations.csv')
    if not names.topic.is_unique or not ai.topic.is_unique or set(names.topic) != set(ai.topic):
        raise ValueError('AI topic IDs must exactly match the supplied topic model')
    comparison = names[['topic', 'name_m4', 'name_m2', 'final_name']].merge(
        ai, on='topic', validate='one_to_one')
    comparison.to_csv(TEXT / 'topic_naming_comparison.csv', index=False)
    result = dict(
        status='complete_ai_assisted', topics=len(comparison),
        human_m2_names=int(comparison.name_m2.notna().sum()), ai_names=len(ai),
        interpretation='AI naming and qualitative comparison with M4-provided names',
        original_two_human_requirement_complete=False,
        human_naming_agreement=None,
        limitation='AI names are disclosed assistance, not independent human M2 labels. '
                   'M4 names were visible during the earlier repository audit; '
                   'the topic comparison is not blind or a human agreement estimate.')
    write_json(TEXT / 'topic_naming_status.json', result)
    return result


def main():
    print(json.dumps({'tone': summarize_tone(), 'topics': summarize_topics()}, indent=2))


if __name__ == '__main__':
    main()
