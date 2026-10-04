import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score

def run_baseline():
    print("Loading datasets...")
    train = pd.read_parquet('data/processed/features_train.parquet')
    val = pd.read_parquet('data/processed/features_val.parquet')
    
    # Drop secondary target and fix dummy variable trap (drop 'question_word_none')
    X_train = train.drop(columns=['target_resolved_7d', 'target_answered_7d', 'question_word_none'], errors='ignore')
    X_train = X_train.fillna(0)
    y_train = train['target_resolved_7d']
    
    X_val = val.drop(columns=['target_resolved_7d', 'target_answered_7d', 'question_word_none'], errors='ignore')
    X_val = X_val.fillna(0)
    y_val = val['target_resolved_7d']
    
    print("Training Logistic Regression Baseline...")
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train, y_train)
    
    print("Evaluating on Validation Set...")
    preds = model.predict(X_val)
    probs = model.predict_proba(X_val)[:, 1]
    
    acc = accuracy_score(y_val, preds)
    prec = precision_score(y_val, preds)
    rec = recall_score(y_val, preds)
    auc = roc_auc_score(y_val, probs)
    
    metrics = f"""
### M4-07 Baseline Model (Logistic Regression)
* **Accuracy**: {acc:.4f}
* **Precision**: {prec:.4f}
* **Recall**: {rec:.4f}
* **ROC AUC**: {auc:.4f}
"""
    print(metrics)
    return metrics

if __name__ == '__main__':
    metrics_md = run_baseline()
    
    import json
    with open('notebooks/04_features.ipynb', 'r') as f:
        nb = json.load(f)
        
    nb['cells'].append({
        'cell_type': 'markdown',
        'metadata': {},
        'source': [line + '\n' for line in metrics_md.strip().split('\n')]
    })
    
    with open('notebooks/04_features.ipynb', 'w') as f:
        json.dump(nb, f, indent=1)
    
    print("Updated 04_features.ipynb with baseline metrics!")
