import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def run_leakage_check():
    print("Loading training features...")
    df = pd.read_parquet('data/processed/features_train.parquet')
    
    # 1. Correlation Matrix with Target
    print("\nCalculating correlations with target_resolved_7d...")
    if 'target_resolved_7d' not in df.columns:
        print("Error: Target missing from features!")
        return
        
    corr = df.corr()['target_resolved_7d'].sort_values(ascending=False)
    print("\n--- Correlation with target_resolved_7d ---")
    print(corr.to_string())
    
    # 2. VIF for Multicollinearity
    print("\nCalculating Variance Inflation Factor (VIF)...")
    try:
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        
        # Select only numeric features (exclude targets)
        X = df.drop(columns=['target_resolved_7d', 'target_answered_7d'], errors='ignore')
        
        # Drop columns with zero variance
        X = X.loc[:, X.var() > 0.0]
        
        vif_data = pd.DataFrame()
        vif_data["feature"] = X.columns
        vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(len(X.columns))]
        
        print("\n--- VIF Check ---")
        print(vif_data.sort_values(by="VIF", ascending=False).to_string())
        
    except ImportError:
        print("statsmodels not installed, skipping VIF.")
        
if __name__ == "__main__":
    run_leakage_check()
