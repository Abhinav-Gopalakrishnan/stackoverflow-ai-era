import pandas as pd
from typing import Tuple, List

def create_splits(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits the dataframe into train, validation, and test sets chronologically.
    Train: Jan 2019 to Dec 2024
    Validation: Jan 2025 to Jun 2025
    Test: Jul 2025 to Jul 2026
    """
    # Ensure creation_date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['creation_date']):
        df['creation_date'] = pd.to_datetime(df['creation_date'], unit='s', utc=True)
    
    train_mask = (df['creation_date'] >= '2019-01-01') & (df['creation_date'] < '2025-01-01')
    val_mask = (df['creation_date'] >= '2025-01-01') & (df['creation_date'] < '2025-07-01')
    test_mask = (df['creation_date'] >= '2025-07-01') & (df['creation_date'] < '2026-08-01')
    
    train_df = df[train_mask].copy()
    val_df = df[val_mask].copy()
    test_df = df[test_mask].copy()
    
    # Assert no overlapping IDs
    assert len(set(train_df['question_id']).intersection(set(val_df['question_id']))) == 0
    assert len(set(train_df['question_id']).intersection(set(test_df['question_id']))) == 0
    assert len(set(val_df['question_id']).intersection(set(test_df['question_id']))) == 0
    
    return train_df, val_df, test_df

def create_time_series_folds(train_df: pd.DataFrame, n_splits: int = 5) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Creates time-series cross-validation folds inside the training period.
    Returns a list of (train_fold, val_fold) dataframes.
    """
    # Ensure data is sorted chronologically
    train_df = train_df.sort_values('creation_date').reset_index(drop=True)
    
    folds = []
    fold_size = len(train_df) // (n_splits + 1)
    
    for i in range(1, n_splits + 1):
        train_end_idx = i * fold_size
        val_end_idx = (i + 1) * fold_size if i < n_splits else len(train_df)
        
        train_fold = train_df.iloc[:train_end_idx].copy()
        val_fold = train_df.iloc[train_end_idx:val_end_idx].copy()
        
        folds.append((train_fold, val_fold))
        
    return folds

def report_split_stats(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, target_col: str = 'is_answered'):
    """Reports row counts and class balance for each split."""
    splits = {'Train': train_df, 'Validation': val_df, 'Test': test_df}
    
    for name, split_df in splits.items():
        if split_df.empty:
            print(f"{name}: 0 rows")
            continue
            
        count = len(split_df)
        if target_col in split_df.columns:
            # Calculate class balance (percentage of positive cases)
            positives = split_df[target_col].sum()
            balance = (positives / count) * 100
            print(f"{name}: {count} rows, {balance:.1f}% positive for '{target_col}'")
        else:
            print(f"{name}: {count} rows (target '{target_col}' not found)")

if __name__ == "__main__":
    # Test on the final cleaned dataset
    print("Testing split module on cleaned data...")
    df = pd.read_parquet('data/processed/questions_clean_v1.parquet')
    
    train, val, test = create_splits(df)
    
    print("\n--- Split Report ---")
    report_split_stats(train, val, test, target_col='target_resolved_7d')
    
    print("\nAssertion passed: No question IDs overlap across splits!")
    
    print("\n--- Time-Series Folds Report ---")
    folds = create_time_series_folds(train, n_splits=5)
    for i, (f_train, f_val) in enumerate(folds):
        print(f"Fold {i+1}: Train rows = {len(f_train)}, Val rows = {len(f_val)}")
