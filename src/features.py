import pandas as pd
import re

def get_title_length(df: pd.DataFrame) -> pd.Series:
    """Number of characters in the question title."""
    return df['title'].str.len()

def get_tag_count(df: pd.DataFrame) -> pd.Series:
    """Number of tags applied to the question."""
    return df['tags'].apply(len)

def get_hour_posted(df: pd.DataFrame) -> pd.Series:
    """Hour of the day the question was posted (UTC)."""
    # Assuming creation_date is unix timestamp
    dt = pd.to_datetime(df['creation_date'], unit='s', utc=True)
    return dt.dt.hour

def get_weekday_posted(df: pd.DataFrame) -> pd.Series:
    """Day of the week the question was posted (0=Monday, 6=Sunday)."""
    dt = pd.to_datetime(df['creation_date'], unit='s', utc=True)
    return dt.dt.weekday

def get_month_posted(df: pd.DataFrame) -> pd.Series:
    """Month the question was posted (1-12)."""
    dt = pd.to_datetime(df['creation_date'], unit='s', utc=True)
    return dt.dt.month

def get_question_word(df: pd.DataFrame) -> pd.Series:
    """Extracted leading question word (How, Why, What, Is, Are, etc.)."""
    # Look for common question words at the start of the title
    question_words = ['how', 'why', 'what', 'when', 'where', 'who', 'is', 'are', 'can', 'could', 'should', 'would', 'do', 'does', 'did']
    pattern = r'^(' + '|'.join(question_words) + r')\b'
    return df['title'].str.extract(pattern, flags=re.IGNORECASE)[0].str.lower().fillna('none')

if __name__ == "__main__":
    # Small test on 5 hand-checked rows from Member 1's test pull
    df = pd.read_parquet('data/processed/test_pull_python_sample.parquet').head(5)
    
    print("--- 5 Hand-checked Rows Test ---")
    print(f"Titles:\n{df['title'].tolist()}\n")
    
    features = pd.DataFrame({
        'title_length': get_title_length(df),
        'tag_count': get_tag_count(df),
        'hour_posted': get_hour_posted(df),
        'weekday_posted': get_weekday_posted(df),
        'month_posted': get_month_posted(df),
        'question_word': get_question_word(df),
    })
    
    print(features)
