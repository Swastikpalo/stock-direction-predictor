"""
data/fetch.py
Utility functions to pull historical stock data via yfinance.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def fetch_historical_data(ticker: str, period_years: int = 2) -> pd.DataFrame:
    end = datetime.today()
    start = end - timedelta(days=period_years * 365)

    df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                     end=end.strftime("%Y-%m-%d"), progress=False)

    if df.empty:
        raise ValueError(f"No data returned for ticker '{ticker}'. Check the symbol.")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.dropna(inplace=True)
    return df


def fetch_recent_data(ticker: str, days: int = 60) -> pd.DataFrame:
    end = datetime.today()
    start = end - timedelta(days=days)

    df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                     end=end.strftime("%Y-%m-%d"), progress=False)

    if df.empty:
        raise ValueError(f"No recent data for ticker '{ticker}'.")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.dropna(inplace=True)
    return df


def fetch_price_history(ticker: str, days: int = 30) -> list[dict]:
    """
    Return recent OHLCV history as a list of dicts.
    Includes open, high, low, close, volume for candlestick + volume bars.
    """
    end = datetime.today()
    start = end - timedelta(days=days)

    df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                     end=end.strftime("%Y-%m-%d"), progress=False)

    if df.empty:
        raise ValueError(f"No price history for ticker '{ticker}'.")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    records = []
    for date, row in df.iterrows():
        records.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
        })

    return records