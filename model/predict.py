"""
model/predict.py
Load the saved model and return a prediction with explanations.
"""

import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

from data.fetch import fetch_recent_data
from model.features import compute_features, get_feature_columns


_MODEL_PATH = os.path.join(os.path.dirname(__file__), "saved", "model.joblib")
_model = None
_model_load_time = None
_model_accuracy = None


def _load_model():
    global _model, _model_load_time, _model_accuracy
    if _model is None:
        if not os.path.exists(_MODEL_PATH):
            raise FileNotFoundError(
                "No trained model found. Run `python -m model.train` first."
            )
        _model = joblib.load(_MODEL_PATH)
        _model_load_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Try to load accuracy from saved metrics
        metrics_path = os.path.join(os.path.dirname(__file__), "saved", "metrics.json")
        if os.path.exists(metrics_path):
            import json
            with open(metrics_path) as f:
                metrics = json.load(f)
                _model_accuracy = metrics.get("accuracy")
    return _model


def _get_model_type(model) -> str:
    name = type(model).__name__
    model_names = {
        "XGBClassifier": "XGBoost Classifier",
        "RandomForestClassifier": "Random Forest Classifier",
        "LogisticRegression": "Logistic Regression",
    }
    return model_names.get(name, name)


def _generate_explanation(features_row: pd.DataFrame) -> list[dict]:
    explanations = []

    rsi = float(features_row["RSI_14"].iloc[0])
    if rsi > 70:
        explanations.append({
            "factor": "RSI Trend",
            "signal": "bearish",
            "detail": f"RSI at {rsi:.1f} — overbought territory (>70), suggesting potential pullback",
            "icon": "📉"
        })
    elif rsi < 30:
        explanations.append({
            "factor": "RSI Trend",
            "signal": "bullish",
            "detail": f"RSI at {rsi:.1f} — oversold territory (<30), suggesting potential bounce",
            "icon": "📈"
        })
    else:
        signal = "bullish" if rsi > 50 else "bearish"
        explanations.append({
            "factor": "RSI Trend",
            "signal": signal,
            "detail": f"RSI at {rsi:.1f} — {'above' if rsi > 50 else 'below'} neutral (50)",
            "icon": "📈" if rsi > 50 else "📉"
        })

    macd = float(features_row["MACD"].iloc[0])
    macd_signal = float(features_row["MACD_signal"].iloc[0])
    if macd > macd_signal:
        explanations.append({
            "factor": "MACD Signal",
            "signal": "bullish",
            "detail": f"MACD ({macd:.3f}) above signal ({macd_signal:.3f}) — bullish momentum",
            "icon": "📈"
        })
    else:
        explanations.append({
            "factor": "MACD Signal",
            "signal": "bearish",
            "detail": f"MACD ({macd:.3f}) below signal ({macd_signal:.3f}) — bearish momentum",
            "icon": "📉"
        })

    price_vs_sma = float(features_row["price_vs_sma50"].iloc[0])
    if price_vs_sma > 1.02:
        explanations.append({
            "factor": "Price Momentum",
            "signal": "bullish",
            "detail": f"Price {((price_vs_sma - 1) * 100):.1f}% above 50-day MA — strong uptrend",
            "icon": "🚀"
        })
    elif price_vs_sma < 0.98:
        explanations.append({
            "factor": "Price Momentum",
            "signal": "bearish",
            "detail": f"Price {((1 - price_vs_sma) * 100):.1f}% below 50-day MA — downtrend",
            "icon": "⬇️"
        })
    else:
        explanations.append({
            "factor": "Price Momentum",
            "signal": "neutral",
            "detail": "Price near 50-day MA — consolidating",
            "icon": "➡️"
        })

    vol_ratio = float(features_row["volume_sma_ratio"].iloc[0])
    if vol_ratio > 1.5:
        explanations.append({
            "factor": "Volume Trend",
            "signal": "high",
            "detail": f"Volume {vol_ratio:.1f}x average — unusually high activity",
            "icon": "🔊"
        })
    elif vol_ratio < 0.5:
        explanations.append({
            "factor": "Volume Trend",
            "signal": "low",
            "detail": f"Volume {vol_ratio:.1f}x average — unusually low activity",
            "icon": "🔇"
        })
    else:
        explanations.append({
            "factor": "Volume Trend",
            "signal": "normal",
            "detail": f"Volume {vol_ratio:.1f}x average — normal range",
            "icon": "🔈"
        })

    volatility = float(features_row["volatility_10"].iloc[0])
    if volatility > 0.025:
        explanations.append({
            "factor": "Volatility",
            "signal": "high",
            "detail": f"10-day volatility at {volatility:.3f} — elevated risk",
            "icon": "⚡"
        })
    else:
        explanations.append({
            "factor": "Volatility",
            "signal": "low",
            "detail": f"10-day volatility at {volatility:.3f} — relatively calm",
            "icon": "😌"
        })

    # Bollinger Band position
    bb_upper = float(features_row["BB_upper"].iloc[0])
    bb_lower = float(features_row["BB_lower"].iloc[0])
    sma_10 = float(features_row["SMA_10"].iloc[0])
    bb_mid = (bb_upper + bb_lower) / 2
    bb_pos = (sma_10 - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5

    if bb_pos > 0.8:
        explanations.append({
            "factor": "Bollinger Position",
            "signal": "bearish",
            "detail": f"Price near upper Bollinger Band ({bb_pos:.0%}) — potential resistance",
            "icon": "🔴"
        })
    elif bb_pos < 0.2:
        explanations.append({
            "factor": "Bollinger Position",
            "signal": "bullish",
            "detail": f"Price near lower Bollinger Band ({bb_pos:.0%}) — potential support",
            "icon": "🟢"
        })
    else:
        explanations.append({
            "factor": "Bollinger Position",
            "signal": "neutral",
            "detail": f"Price in middle of Bollinger Bands ({bb_pos:.0%})",
            "icon": "🟡"
        })

    return explanations


def _generate_summary(direction: str, explanations: list[dict]) -> str:
    bullish = sum(1 for e in explanations if e["signal"] == "bullish")
    bearish = sum(1 for e in explanations if e["signal"] == "bearish")

    if direction == "UP":
        if bullish > bearish:
            return f"Multiple bullish signals detected ({bullish} of {len(explanations)} factors favor upward movement). Technical indicators suggest positive momentum for the next trading day."
        else:
            return f"Despite mixed signals, the model predicts upward movement. {bullish} bullish vs {bearish} bearish factors — the model weighs feature interactions beyond individual signals."
    else:
        if bearish > bullish:
            return f"Multiple bearish signals detected ({bearish} of {len(explanations)} factors suggest downward pressure). Technical indicators point to a potential decline next trading day."
        else:
            return f"Despite mixed signals, the model predicts downward movement. {bearish} bearish vs {bullish} bullish factors — the model detects patterns beyond individual indicators."


def predict_direction(ticker: str) -> dict:
    model = _load_model()

    df = fetch_recent_data(ticker, days=120)

    if len(df) < 50:
        raise ValueError(
            f"Not enough trading data for '{ticker}' to compute features. "
            f"Got {len(df)} rows, need at least 50."
        )

    df = compute_features(df)

    feature_cols = get_feature_columns()
    latest = df[feature_cols].dropna().iloc[-1:]

    if latest.empty:
        raise ValueError(f"Could not compute features for '{ticker}'.")

    current_price = round(float(df["Close"].iloc[-1]), 2)

    prediction = model.predict(latest)[0]
    direction = "UP" if prediction == 1 else "DOWN"

    # Full probability breakdown
    proba = model.predict_proba(latest)[0]
    prob_down = round(float(proba[0]), 4)
    prob_up = round(float(proba[1]), 4)
    confidence = round(max(prob_up, prob_down), 4)

    explanations = _generate_explanation(latest)
    summary = _generate_summary(direction, explanations)

    model_info = {
        "model_type": _get_model_type(model),
        "num_features": len(feature_cols),
        "last_loaded": _model_load_time,
        "accuracy": _model_accuracy,
        "prediction_horizon": "Next Trading Day",
    }

    return {
        "ticker": ticker.upper(),
        "direction": direction,
        "confidence": confidence,
        "prob_up": prob_up,
        "prob_down": prob_down,
        "current_price": current_price,
        "features_used": feature_cols,
        "explanations": explanations,
        "summary": summary,
        "model_info": model_info,
    }