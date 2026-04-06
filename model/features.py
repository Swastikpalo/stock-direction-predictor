"""
model/features.py
Feature engineering: compute 13 technical indicators from raw OHLCV data.
"""

import pandas as pd
import numpy as np


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a DataFrame with Open, High, Low, Close, Volume columns,
    compute all technical indicator features and return a new
    DataFrame with the feature columns appended.

    Features (13 total):
        SMA_10, SMA_50, EMA_12, RSI_14, MACD, MACD_signal,
        BB_upper, BB_lower, daily_return, volume_change,
        volatility_10, price_vs_sma50, volume_sma_ratio
    """
    df = df.copy()

    # --- Moving Averages ---
    df["SMA_10"] = df["Close"].rolling(window=10).mean()
    df["SMA_50"] = df["Close"].rolling(window=50).mean()
    df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()

    # --- RSI (14-day) ---
    df["RSI_14"] = _compute_rsi(df["Close"], period=14)

    # --- MACD ---
    ema_12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema_26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema_12 - ema_26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # --- Bollinger Bands (20-day, 2 std) ---
    sma_20 = df["Close"].rolling(window=20).mean()
    std_20 = df["Close"].rolling(window=20).std()
    df["BB_upper"] = sma_20 + (2 * std_20)
    df["BB_lower"] = sma_20 - (2 * std_20)

    # --- Daily Return ---
    df["daily_return"] = df["Close"].pct_change()

    # --- Volume Change ---
    df["volume_change"] = df["Volume"].pct_change()

    # --- Volatility (10-day rolling std of returns) ---
    df["volatility_10"] = df["daily_return"].rolling(window=10).std()

    # --- Price vs SMA_50 ratio ---
    df["price_vs_sma50"] = df["Close"] / df["SMA_50"]

    # --- Volume SMA ratio (current volume / 10-day avg volume) ---
    df["volume_sma_ratio"] = df["Volume"] / df["Volume"].rolling(window=10).mean()

    return df


def get_feature_columns() -> list[str]:
    """Return the list of feature column names used by the model."""
    return [
        "SMA_10", "SMA_50", "EMA_12", "RSI_14",
        "MACD", "MACD_signal", "BB_upper", "BB_lower",
        "daily_return", "volume_change", "volatility_10",
        "price_vs_sma50", "volume_sma_ratio",
    ]


def prepare_training_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Compute features and create the target variable.

    Target: 1 if next day's close > today's close (UP), else 0 (DOWN).

    Returns:
        X: DataFrame of feature columns (rows with NaN dropped).
        y: Series of target labels aligned with X.
    """
    df = compute_features(df)

    # Target: shift Close back by 1 to compare tomorrow vs today
    df["target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

    # Drop rows with NaN from rolling windows and the last row (no target)
    df.dropna(inplace=True)

    feature_cols = get_feature_columns()
    X = df[feature_cols]
    y = df["target"]

    return X, y


def _compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Compute RSI using the standard smoothed method."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi