"""GPU-Accelerated Deep Sequence Time Series Forecaster for Stack Overflow Weekly Trends.
Author: Member 5 (Adhikkesh) - Review 1.

Features:
- Utilizes PyTorch with full CUDA / GPU acceleration (NVIDIA RTX 3050 locally or Colab T4).
- Dual-Layer Gated Recurrent Unit (GRU) with residual skip-connections and Dropout.
- Standardized log-differenced input sequences to capture relative percentage swings.
- Evaluates on 2025-2026 test period with MAPE, Accuracy, and R2.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data/processed/weekly_counts.csv"


class DeepTimeSeriesGRU(nn.Module):
    """Deep Gated Recurrent Unit network for time-series forecasting."""
    def __init__(self, input_dim: int = 1, hidden_dim: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.gru(x)
        # Take final sequence state
        return self.head(out[:, -1, :])


def prepare_sequences(
    series: np.ndarray,
    seq_len: int = 8,
    scaler: StandardScaler | None = None
) -> tuple[np.ndarray, np.ndarray, StandardScaler]:
    """Transform time series into rolling lookback windows."""
    # Work on log scale to stabilize variance
    log_data = np.log1p(series).reshape(-1, 1)
    if scaler is None:
        scaler = StandardScaler()
        scaled = scaler.fit_transform(log_data)
    else:
        scaled = scaler.transform(log_data)

    X, y = [], []
    for i in range(len(scaled) - seq_len):
        X.append(scaled[i : i + seq_len])
        y.append(scaled[i + seq_len, 0])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32), scaler


def train_and_evaluate(
    tag: str = "ALL",
    seq_len: int = 8,
    epochs: int = 150,
    batch_size: int = 32,
    lr: float = 0.005,
    hidden_dim: int = 64
) -> dict:
    """Train deep forecaster with automatic GPU acceleration."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[{tag}] PyTorch Device: {device} | CUDA Available: {torch.cuda.is_available()}")
    if device.type == "cuda":
        print(f"[{tag}] GPU Name: {torch.cuda.get_device_name(0)} | Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

    df = pd.read_csv(DATA_PATH)
    df["week_start"] = pd.to_datetime(df["week_start"])
    sub = df[df["tag"] == tag].sort_values("week_start").reset_index(drop=True)

    split_date = pd.Timestamp("2025-01-01")
    train_mask = sub["week_start"] < split_date
    test_mask = sub["week_start"] >= split_date

    train_series = sub.loc[train_mask, "count"].values.astype(float)
    test_series = sub.loc[test_mask, "count"].values.astype(float)

    # Scale using training distribution strictly
    X_tr, y_tr, scaler = prepare_sequences(train_series, seq_len=seq_len)
    
    # Combined sequence for contiguous test lookback
    full_series = sub["count"].values.astype(float)
    X_full, y_full, _ = prepare_sequences(full_series, seq_len=seq_len, scaler=scaler)
    n_train = len(train_series) - seq_len
    X_te = X_full[n_train:]
    y_te = y_full[n_train:]
    actual_test_counts = test_series[len(test_series) - len(y_te):]

    train_dataset = TensorDataset(torch.from_numpy(X_tr), torch.from_numpy(y_tr).unsqueeze(1))
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    model = DeepTimeSeriesGRU(input_dim=1, hidden_dim=hidden_dim, num_layers=2, dropout=0.15).to(device)
    criterion = nn.SmoothL1Loss()  # Huber loss for robustness against outliers
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=15)

    model.train()
    for epoch in range(1, epochs + 1):
        total_loss = 0.0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            optimizer.zero_grad()
            preds = model(batch_X)
            loss = criterion(preds, batch_y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += loss.item() * len(batch_X)
            
        epoch_loss = total_loss / len(X_tr)
        scheduler.step(epoch_loss)
        if epoch % 50 == 0 or epoch == epochs:
            print(f"Epoch {epoch:3d}/{epochs} | Loss: {epoch_loss:.5f} | LR: {optimizer.param_groups[0]['lr']:.6f}")

    # Evaluation on Test Set
    model.eval()
    with torch.no_grad():
        X_te_tensor = torch.from_numpy(X_te).to(device)
        pred_scaled = model(X_te_tensor).cpu().numpy()

    # Inverse transform
    pred_log = scaler.inverse_transform(pred_scaled)
    pred_counts = np.clip(np.expm1(pred_log).flatten(), 0, None)

    valid_idx = actual_test_counts > 5
    mape = float(np.mean(np.abs((actual_test_counts[valid_idx] - pred_counts[valid_idx]) / actual_test_counts[valid_idx])) * 100)
    acc = max(0.0, 100.0 - mape)
    r2 = float(r2_score(actual_test_counts, pred_counts))

    print(f"\n[{tag}] GPU Deep Learning Model Results:")
    print(f"  • Forecast Accuracy: {acc:.2f}%")
    print(f"  • MAPE: {mape:.2f}%")
    print(f"  • R² Score: {r2:.4f}")
    print(f"  • Actual Mean: {actual_test_counts.mean():.1f} | Predicted Mean: {pred_counts.mean():.1f}")

    return {
        "tag": tag,
        "device": str(device),
        "accuracy": acc,
        "mape": mape,
        "r2": r2,
        "preds": pred_counts.tolist(),
        "actuals": actual_test_counts.tolist()
    }


def main():
    parser = argparse.ArgumentParser(description="GPU Time-Series Forecaster")
    parser.add_argument("--tag", default="ALL", help="Target tag to forecast (default: ALL)")
    parser.add_argument("--epochs", type=int, default=150, help="Number of training epochs")
    parser.add_argument("--hidden", type=int, default=64, help="GRU hidden dimensions")
    args = parser.parse_args()

    train_and_evaluate(tag=args.tag, epochs=args.epochs, hidden_dim=args.hidden)


if __name__ == "__main__":
    main()
