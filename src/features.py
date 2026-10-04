import pandas as pd
import re

def get_title_length(df: pd.DataFrame) -> pd.Series:
    """Number of characters in the question title."""
    return df['title'].str.len()

def get_tag_count(df: pd.DataFrame) -> pd.Series:
    """Number of tags applied to the question."""
    if 'tags' in df.columns:
        return df['tags'].apply(len)
    elif 'collected_tags' in df.columns:
        return df['collected_tags'].apply(len)
    return pd.Series([0]*len(df), index=df.index)

def get_hour_posted(df: pd.DataFrame) -> pd.Series:
    """Hour of the day the question was posted (UTC)."""
    # Assuming creation_date is unix timestamp or datetime
    if pd.api.types.is_datetime64_any_dtype(df['creation_date']):
        dt = df['creation_date']
    else:
        dt = pd.to_datetime(df['creation_date'], unit='s', utc=True)
    return dt.dt.hour

def get_weekday_posted(df: pd.DataFrame) -> pd.Series:
    """Day of the week the question was posted (0=Monday, 6=Sunday)."""
    if pd.api.types.is_datetime64_any_dtype(df['creation_date']):
        dt = df['creation_date']
    else:
        dt = pd.to_datetime(df['creation_date'], unit='s', utc=True)
    return dt.dt.weekday

def get_month_posted(df: pd.DataFrame) -> pd.Series:
    """Month the question was posted (1-12)."""
    if pd.api.types.is_datetime64_any_dtype(df['creation_date']):
        dt = df['creation_date']
    else:
        dt = pd.to_datetime(df['creation_date'], unit='s', utc=True)
    return dt.dt.month

def get_question_word(df: pd.DataFrame) -> pd.Series:
    """Extracted leading question word (How, Why, What, Is, Are, etc.)."""
    question_words = ['how', 'why', 'what', 'when', 'where', 'who', 'is', 'are', 'can', 'could', 'should', 'would', 'do', 'does', 'did']
    pattern = r'^(' + '|'.join(question_words) + r')\b'
    return df['title'].str.extract(pattern, flags=re.IGNORECASE)[0].str.lower().fillna('none')

def build_features(df: pd.DataFrame, is_train: bool = False, scaler=None, encoder=None):
    """
    Build all features, apply scaling and encoding.
    Returns (features_df, scaler, encoder).
    """
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    
    # 1. Extract base features
    features = pd.DataFrame(index=df.index)
    features['title_length'] = get_title_length(df)
    features['tag_count'] = get_tag_count(df)
    features['hour_posted'] = get_hour_posted(df)
    features['weekday_posted'] = get_weekday_posted(df)
    features['month_posted'] = get_month_posted(df)
    features['question_word'] = get_question_word(df)
    
    # Include features from Member 2 if available
    for col in ['code_ratio', 'has_error_text', 'account_age_days', 'n_code_blocks']:
        if col in df.columns:
            features[col] = df[col].fillna(0)
            
    # Include targets if available
    for target in ['target_resolved_7d', 'target_answered_7d']:
        if target in df.columns:
            features[target] = df[target]
            
    # 2. Encode categorical (question_word)
    if is_train:
        encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        encoded_words = encoder.fit_transform(features[['question_word']])
    else:
        encoded_words = encoder.transform(features[['question_word']])
        
    encoded_df = pd.DataFrame(encoded_words, columns=encoder.get_feature_names_out(['question_word']), index=features.index)
    features = pd.concat([features.drop('question_word', axis=1), encoded_df], axis=1)
    
    # 3. Scale numeric features
    numeric_cols = ['title_length', 'tag_count', 'hour_posted', 'weekday_posted', 'month_posted']
    if 'code_ratio' in features.columns:
        numeric_cols.extend(['code_ratio', 'account_age_days', 'n_code_blocks'])
        
    if is_train:
        scaler = StandardScaler()
        features[numeric_cols] = scaler.fit_transform(features[numeric_cols])
    else:
        features[numeric_cols] = scaler.transform(features[numeric_cols])
        
    return features, scaler, encoder

if __name__ == "__main__":
    from src.split import create_splits
    import os
    
    print("Loading cleaned dataset...")
    df = pd.read_parquet('data/processed/questions_clean_v1.parquet')
    
    print("Splitting dataset...")
    train_df, val_df, test_df = create_splits(df)
    
    print("Building features for Train...")
    train_features, scaler, encoder = build_features(train_df, is_train=True)
    
    print("Building features for Validation...")
    val_features, _, _ = build_features(val_df, is_train=False, scaler=scaler, encoder=encoder)
    
    print("Building features for Test...")
    test_features, _, _ = build_features(test_df, is_train=False, scaler=scaler, encoder=encoder)
    
    print("Saving features to data/processed/...")
    train_features.to_parquet('data/processed/features_train.parquet')
    val_features.to_parquet('data/processed/features_val.parquet')
    test_features.to_parquet('data/processed/features_test.parquet')
    
    print(f"Done! Saved Train ({len(train_features)}), Val ({len(val_features)}), Test ({len(test_features)})")

