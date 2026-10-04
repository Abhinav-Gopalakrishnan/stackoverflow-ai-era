import pandas as pd
import numpy as np
import re
from sklearn.preprocessing import StandardScaler, OneHotEncoder, MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

def get_title_length(df: pd.DataFrame) -> pd.Series:
    return df['title'].str.len()

def get_body_length(df: pd.DataFrame) -> pd.Series:
    if 'plain_body' in df.columns:
        return df['plain_body'].str.len().fillna(0)
    return pd.Series([0]*len(df), index=df.index)

def get_tag_count(df: pd.DataFrame) -> pd.Series:
    if 'tags' in df.columns:
        return df['tags'].apply(len)
    elif 'collected_tags' in df.columns:
        return df['collected_tags'].apply(len)
    return pd.Series([0]*len(df), index=df.index)

def get_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    if pd.api.types.is_datetime64_any_dtype(df['creation_date']):
        dt = df['creation_date']
    else:
        dt = pd.to_datetime(df['creation_date'], unit='s', utc=True)
    return pd.DataFrame({
        'hour_posted': dt.dt.hour,
        'weekday_posted': dt.dt.weekday,
        'month_posted': dt.dt.month
    }, index=df.index)

def get_question_word(df: pd.DataFrame) -> pd.Series:
    question_words = ['how', 'why', 'what', 'when', 'where', 'who', 'is', 'are', 'can', 'could', 'should', 'would', 'do', 'does', 'did']
    pattern = r'^(' + '|'.join(question_words) + r')\b'
    return df['title'].str.extract(pattern, flags=re.IGNORECASE)[0].str.lower().fillna('none')

def calculate_lagged_volume(df: pd.DataFrame, weekly_counts_path: str = 'data/processed/weekly_counts.csv') -> pd.Series:
    print("Calculating lagged tag volume (4 weeks prior)...")
    if 'collected_tag' not in df.columns or 'creation_date' not in df.columns:
        return pd.Series([0]*len(df), index=df.index)
        
    w = pd.read_csv(weekly_counts_path)
    w['week_start'] = pd.to_datetime(w['week_start'], utc=True)
    
    if pd.api.types.is_datetime64_any_dtype(df['creation_date']):
        dt = df['creation_date']
    else:
        dt = pd.to_datetime(df['creation_date'], unit='s', utc=True)
        
    temp_df = pd.DataFrame({'collected_tag': df['collected_tag'], 'date': dt}, index=df.index)
    
    # Sort weekly counts for rolling
    w = w.sort_values('week_start')
    
    # We need to map each question's date and tag to the sum of the last 4 weeks.
    # To do this efficiently, we can use merge_asof or simply build a mapping.
    
    # Create rolling 4-week sum per tag
    w.set_index('week_start', inplace=True)
    lagged_sums = {}
    
    for tag, group in w.groupby('tag'):
        # resample to weekly to ensure no gaps, though they shouldn't exist
        group = group.resample('W').sum().fillna(0)
        # shift by 1 week so the week of posting doesn't leak
        shifted = group['count'].shift(1)
        # rolling sum over 4 weeks
        rolled = shifted.rolling(window=4, min_periods=1).sum()
        lagged_sums[tag] = rolled

    # Function to lookup
    def lookup_volume(row):
        tag = row['collected_tag']
        d = row['date']
        if tag in lagged_sums:
            s = lagged_sums[tag]
            # Get the value as of the question's date using exact or previous week
            idx = s.index.get_indexer([d], method='ffill')[0]
            if idx != -1:
                return s.iloc[idx]
        return 0
        
    return temp_df.apply(lookup_volume, axis=1)

def build_features(df: pd.DataFrame, is_train: bool = False, scaler=None, encoder=None, mlb=None, tfidf=None, svd=None):
    """
    Build all advanced features as requested by M3 EDA.
    Returns (features_df, scaler, encoder, mlb, tfidf, svd).
    """
    print(f"Building advanced features (train={is_train})...")
    features = pd.DataFrame(index=df.index)
    
    # 1. Structural Characteristics
    features['title_length'] = get_title_length(df)
    features['body_length'] = get_body_length(df)
    features['tag_count'] = get_tag_count(df)
    
    for col in ['code_ratio', 'has_error_text', 'n_code_blocks']:
        if col in df.columns:
            features[col] = df[col].fillna(0)
            
    # 2. Account Maturity Barrier
    if 'account_age_days' in df.columns:
        features['account_age_days'] = df['account_age_days'].fillna(0)
        features['new_account'] = (features['account_age_days'] <= 7).astype(int)
    if 'missing_account_age' in df.columns:
        features['missing_account_age'] = df['missing_account_age'].astype(int)
        
    # 3. Cyclical Temporal Dynamics
    temporal = get_temporal_features(df)
    features = pd.concat([features, temporal], axis=1)
    
    # 4. Post-ChatGPT Volume Collapse (Lagged Volume & Multi-hot tags)
    features['lagged_tag_volume_4w'] = calculate_lagged_volume(df)
    
    if 'collected_tags' in df.columns:
        tags_series = df['collected_tags'].apply(lambda x: x if isinstance(x, np.ndarray) or isinstance(x, list) else [])
        if is_train:
            mlb = MultiLabelBinarizer()
            tag_matrix = mlb.fit_transform(tags_series)
        else:
            # ignore unknown tags
            tag_matrix = mlb.transform(tags_series)
        
        tag_df = pd.DataFrame(tag_matrix, columns=[f"tag_{c}" for c in mlb.classes_], index=features.index)
        features = pd.concat([features, tag_df], axis=1)
        
        # other tags count = total tags - known tags matched
        features['other_tags_count'] = features['tag_count'] - tag_df.sum(axis=1)

    # 5. Title Semantics & Vocabulary (TF-IDF + SVD)
    titles = df['title'].fillna('')
    if is_train:
        print("Fitting TF-IDF and SVD on titles (this may take a minute)...")
        tfidf = TfidfVectorizer(ngram_range=(1, 2), max_features=5000, stop_words='english')
        title_tfidf = tfidf.fit_transform(titles)
        
        svd = TruncatedSVD(n_components=100, random_state=42)
        title_svd = svd.fit_transform(title_tfidf)
    else:
        title_tfidf = tfidf.transform(titles)
        title_svd = svd.transform(title_tfidf)
        
    svd_df = pd.DataFrame(title_svd, columns=[f"title_svd_{i}" for i in range(100)], index=features.index)
    features = pd.concat([features, svd_df], axis=1)
    
    # 6. Question word encoding (Dummy Variable Trap fix)
    features['question_word'] = get_question_word(df)
    if is_train:
        encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore', drop='first')
        encoded_words = encoder.fit_transform(features[['question_word']])
    else:
        # handle unknown by skipping it if drop is used, which might require custom handling
        # For simplicity, we just transform
        encoded_words = encoder.transform(features[['question_word']])
        
    encoded_df = pd.DataFrame(encoded_words, columns=encoder.get_feature_names_out(['question_word']), index=features.index)
    features = pd.concat([features.drop('question_word', axis=1), encoded_df], axis=1)

    # Include targets if available
    for target in ['target_resolved_7d', 'target_answered_7d']:
        if target in df.columns:
            features[target] = df[target]

    # 7. Scale numeric features
    # Collect numeric columns (everything except targets and binary flags like tag_* and title_svd_*)
    # Actually, scaling SVD components is also standard. We can scale all columns except targets.
    numeric_cols = [c for c in features.columns if c not in ['target_resolved_7d', 'target_answered_7d']]
        
    if is_train:
        scaler = StandardScaler()
        features[numeric_cols] = scaler.fit_transform(features[numeric_cols])
    else:
        features[numeric_cols] = scaler.transform(features[numeric_cols])
        
    return features, scaler, encoder, mlb, tfidf, svd

if __name__ == "__main__":
    from src.split import create_splits
    import os
    
    print("Loading cleaned dataset...")
    df = pd.read_parquet('data/processed/questions_clean_v1.parquet')
    
    print("Splitting dataset...")
    train_df, val_df, test_df = create_splits(df)
    
    print("Building features for Train...")
    train_features, scaler, encoder, mlb, tfidf, svd = build_features(train_df, is_train=True)
    
    print("Building features for Validation...")
    val_features, _, _, _, _, _ = build_features(val_df, is_train=False, scaler=scaler, encoder=encoder, mlb=mlb, tfidf=tfidf, svd=svd)
    
    print("Building features for Test...")
    test_features, _, _, _, _, _ = build_features(test_df, is_train=False, scaler=scaler, encoder=encoder, mlb=mlb, tfidf=tfidf, svd=svd)
    
    print("Saving features to data/processed/...")
    train_features.to_parquet('data/processed/features_train.parquet')
    val_features.to_parquet('data/processed/features_val.parquet')
    test_features.to_parquet('data/processed/features_test.parquet')
    
    print(f"Done! Saved Train ({len(train_features)}), Val ({len(val_features)}), Test ({len(test_features)})")
