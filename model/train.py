"""
model/train.py
Train and compare models, save the best one.

Usage:
    python -m model.train              # defaults to AAPL
    python -m model.train MSFT         # train on a specific ticker
"""

import sys
import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from data.fetch import fetch_historical_data
from model.features import prepare_training_data, get_feature_columns


def time_series_split(X: pd.DataFrame, y: pd.Series, train_ratio: float = 0.8):
    """
    Walk-forward split: first 80% for training, last 20% for testing.
    No shuffling — preserves temporal order to prevent data leakage.
    """
    split_idx = int(len(X) * train_ratio)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    return X_train, X_test, y_train, y_test


def get_models() -> dict:
    """Return a dict of model name → model instance."""
    return {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=10, random_state=42, n_jobs=-1
        ),
        "XGBoost": XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            use_label_encoder=False, eval_metric="logloss", random_state=42,
        ),
    }


def evaluate_model(model, X_test, y_test) -> dict:
    """Compute classification metrics for a trained model."""
    preds = model.predict(X_test)
    return {
        "accuracy": round(accuracy_score(y_test, preds), 4),
        "precision": round(precision_score(y_test, preds, zero_division=0), 4),
        "recall": round(recall_score(y_test, preds, zero_division=0), 4),
        "f1": round(f1_score(y_test, preds, zero_division=0), 4),
    }


def train_and_compare(ticker: str = "AAPL") -> None:
    """Full training pipeline: fetch → features → train → compare → save."""

    print(f"\n{'='*60}")
    print(f"  Stock Predictor — Training Pipeline")
    print(f"  Ticker: {ticker}")
    print(f"{'='*60}\n")

    # --- 1. Fetch data ---
    print("[1/5] Fetching historical data...")
    df = fetch_historical_data(ticker, period_years=2)
    print(f"      Retrieved {len(df)} trading days.\n")

    # --- 2. Feature engineering ---
    print("[2/5] Computing features...")
    X, y = prepare_training_data(df)
    print(f"      Feature matrix shape: {X.shape}")
    print(f"      Target distribution: UP={y.sum()} | DOWN={len(y) - y.sum()}\n")

    # --- 3. Time-series split ---
    print("[3/5] Splitting data (80/20 walk-forward)...")
    X_train, X_test, y_train, y_test = time_series_split(X, y)
    print(f"      Train: {len(X_train)} rows | Test: {len(X_test)} rows\n")

    # --- 4. Train & evaluate each model ---
    print("[4/5] Training models...\n")
    models = get_models()
    results = {}

    for name, model in models.items():
        print(f"  Training {name}...")
        model.fit(X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test)
        results[name] = {"model": model, "metrics": metrics}

        print(f"    Accuracy:  {metrics['accuracy']}")
        print(f"    Precision: {metrics['precision']}")
        print(f"    Recall:    {metrics['recall']}")
        print(f"    F1 Score:  {metrics['f1']}\n")

    # --- 5. Save best model (by F1 score) ---
    best_name = max(results, key=lambda k: results[k]["metrics"]["f1"])
    best_model = results[best_name]["model"]
    best_metrics = results[best_name]["metrics"]

    save_dir = os.path.join(os.path.dirname(__file__), "saved")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "model.joblib")

    joblib.dump(best_model, save_path)

    # Save metrics for the prediction module
    metrics_path = os.path.join(save_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(best_metrics, f)

    print(f"[5/5] Best model: {best_name}")
    print(f"      F1 Score:  {best_metrics['f1']}")
    print(f"      Saved to:  {save_path}")
    print(f"\n{'='*60}")
    print("  Training complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    train_and_compare(ticker)