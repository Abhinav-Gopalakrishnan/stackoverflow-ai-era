"""Shared fitted-model inference. User inputs never require outcome fields."""
from pathlib import Path
import hashlib
import html
import json
import joblib
import numpy as np
import pandas as pd
from src.build_features import build_features, DEFAULT_TAGS
from src.cleaning import split_html, ERROR_PATTERN

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / 'models/resolution_v2'
TARGET_DESCRIPTION = ('The answer accepted in the collected record was posted within 168 hours. '
                      'The time of acceptance and actual satisfaction are unknown.')

def load_bundle(folder=MODEL_DIR):
    folder = Path(folder)
    metadata = json.loads((folder/'metadata.json').read_text())
    path = folder/'pipeline.joblib'
    if hashlib.sha256(path.read_bytes()).hexdigest() != metadata['model_sha256']:
        raise ValueError('Model checksum differs from release metadata')
    return joblib.load(path), metadata

def question_frame(title, prose, code, tags, posted_at, account_age_days=None):
    if len(title.strip()) < 10 or len(title) > 500:
        raise ValueError('Use a title between 10 and 500 characters.')
    if len(prose.strip()) < 20 or len(prose) > 50000 or len(code) > 100000:
        raise ValueError('Use 20–50,000 characters of question prose and at most 100,000 characters of code.')
    tags = list(dict.fromkeys(tags))
    if not 1 <= len(tags) <= 5 or not set(tags).intersection(DEFAULT_TAGS):
        raise ValueError('Choose one to five tags, including a supported study technology.')
    if account_age_days is not None and (not np.isfinite(account_age_days) or not 0 <= account_age_days <= 20000):
        raise ValueError('Account age must be between 0 and 20,000 days, or unknown.')
    body = '<p>'+html.escape(prose)+'</p>'
    if code.strip(): body += '<pre><code>'+html.escape(code)+'</code></pre>'
    plain, extracted, blocks = split_html(body)
    total = len(plain)+len(extracted)
    return pd.DataFrame([dict(title=title.strip(), plain_body=plain[:4187], code_text=extracted,
        tags=tags, created_at=pd.to_datetime(posted_at, utc=True), n_code_blocks=blocks,
        code_ratio=len(extracted)/total if total else 0,
        has_error_text=bool(ERROR_PATTERN.search(plain+'\n'+extracted)),
        account_age_days=account_age_days, missing_account_age=account_age_days is None)])

def infer(bundle, metadata, question, weekly):
    dates = pd.to_datetime(question.created_at, utc=True)
    if not dates.between(pd.Timestamp(metadata['supported_start']), pd.Timestamp(metadata['supported_end'])).all():
        raise ValueError('This historical model demonstration supports '+metadata['supported_start'][:10]+' to '+metadata['supported_end'][:10]+'. Update and validate the data release before using current dates.')
    features = build_features(question, weekly, tags=metadata['study_tags'])
    if len(features) != len(question):
        raise ValueError('Eight complete prior weeks are required for the selected tags.')
    X = features[metadata['input_columns']]
    raw = bundle['pipeline'].predict_proba(X)[:, 1]
    probability = bundle['calibrator'].predict_proba(raw.reshape(-1, 1))[:, 1]
    return features, raw, probability

def explain(bundle, metadata, features):
    """Exact tree SHAP contributions to the raw margin, before calibration."""
    import xgboost as xgb
    pipe = bundle['pipeline']
    transformed = pipe['prep'].transform(features[metadata['input_columns']])
    values = pipe['model'].get_booster().predict(xgb.DMatrix(transformed), pred_contribs=True)[0, :-1]
    return pd.DataFrame({'feature':pipe['prep'].get_feature_names_out(), 'contribution':values}).assign(
        magnitude=lambda d:d.contribution.abs()).nlargest(10,'magnitude').drop(columns='magnitude')
