# Stock Price Direction Predictor

A full-stack machine learning dashboard that predicts whether a stock's next trading day close will be **UP** or **DOWN**, with confidence scores, technical analysis, and interactive visualizations.

Built with Flask, XGBoost, and Chart.js.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-FF6600)
![Chart.js](https://img.shields.io/badge/Chart.js-4.4-FF6384?logo=chartdotjs&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Demo

<!-- Replace these with your actual screenshots -->
<!-- ![Dashboard](screenshots/dashboard.png) -->
<!-- ![Candlestick Chart](screenshots/candlestick.png) -->
<!-- ![Stock Comparison](screenshots/comparison.png) -->

> Take screenshots of the running app and add them here for best results.

---

## What It Does

Enter any stock ticker and the system will:

1. **Fetch live market data** from Yahoo Finance
2. **Engineer 13 technical indicators** from raw OHLCV data
3. **Run an XGBoost model** trained with time-series aware cross-validation
4. **Display the prediction** with confidence score, probability breakdown, and factor explanations
5. **Render interactive charts** with candlestick, volume, moving average overlays, and crosshair

---

## Key Features

**Machine Learning**
- 13 engineered features: SMA, EMA, RSI, MACD, Bollinger Bands, volatility, volume ratios
- 3 models compared: Logistic Regression, Random Forest, XGBoost
- Walk-forward 80/20 split with no data leakage (no random shuffling on time-series data)
- Best model selected by F1 score, not raw accuracy
- Prediction explanations showing which factors influenced the result

**Dashboard**
- Candlestick and line chart with volume bars
- SMA 20 / SMA 50 toggle overlays with crosshair cursor
- 1D, 5D, 1M, 6M, 1Y timeframe selection
- Stock comparison with normalized percentage performance
- Key statistics: Market Cap, P/E, EPS, Beta, Dividend Yield, 52-week range
- News feed with sentiment analysis (positive / neutral / negative)
- Watchlist with live prices and daily change
- Prediction log tracking all session predictions
- Recent search history

**API**
- `POST /predict` — ML prediction with confidence and explanations
- `GET /history/<ticker>` — OHLCV price data with timeframe support
- `GET /info/<ticker>` — Stock statistics and company info
- `GET /news/<ticker>` — Latest news headlines
- `GET /search?q=<query>` — Autocomplete by ticker or company name
- `POST /compare` — Normalized performance comparison
- `POST /watchlist_prices` — Batch price quotes

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, Flask-CORS |
| Machine Learning | Scikit-learn, XGBoost |
| Data | yfinance, Pandas, NumPy |
| Frontend | HTML, CSS, JavaScript (vanilla) |
| Charts | Chart.js 4.4 |
| Serialization | Joblib |

---

## Project Structure

```
stock-predictor/
├── app.py                  # Flask API — all routes
├── data/
│   └── fetch.py            # yfinance data fetching (OHLCV)
├── model/
│   ├── features.py         # 13 technical indicators
│   ├── train.py            # Training pipeline + model comparison
│   ├── predict.py          # Prediction + explanations
│   └── saved/
│       ├── model.joblib    # Trained model (generated)
│       └── metrics.json    # Model metrics (generated)
├── static/
│   ├── style.css           # Dashboard styling (dark theme)
│   └── script.js           # Frontend logic + Chart.js rendering
├── templates/
│   └── index.html          # Main page
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Swastikpalo/stock-direction-predictor.git
cd stock-direction-predictor
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Train the model

```bash
python -m model.train           # Defaults to AAPL
python -m model.train MSFT      # Or specify any ticker
```

This fetches 2 years of data, computes features, trains 3 models, compares them, and saves the best one.

### 4. Start the server

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## ML Details

### Features (13 total)

| Feature | Description |
|---|---|
| SMA_10 | 10-day simple moving average |
| SMA_50 | 50-day simple moving average |
| EMA_12 | 12-day exponential moving average |
| RSI_14 | 14-day relative strength index |
| MACD | MACD line value |
| MACD_signal | MACD signal line |
| BB_upper | Bollinger Band upper |
| BB_lower | Bollinger Band lower |
| daily_return | Daily percentage return |
| volume_change | Daily volume percentage change |
| volatility_10 | 10-day rolling std of returns |
| price_vs_sma50 | Price / SMA_50 ratio |
| volume_sma_ratio | Volume / 10-day avg volume |

### Training Approach

- **Target**: 1 if next day close > today's close, else 0
- **Split**: Walk-forward (first 80% train, last 20% test) — no shuffling to prevent temporal data leakage
- **Models**: Logistic Regression (baseline), Random Forest, XGBoost
- **Selection**: Best F1 score wins
- **Output**: Saved model + metrics JSON

### Why Walk-Forward Split Matters

Standard random train/test splits leak future information into the training set when working with time-series data. Walk-forward splitting ensures the model only trains on past data and tests on future data, which is how the model would actually be used in production.

---

## API Reference

### `POST /predict`

```json
// Request
{ "ticker": "AAPL" }

// Response
{
  "ticker": "AAPL",
  "direction": "UP",
  "confidence": 0.7342,
  "prob_up": 0.7342,
  "prob_down": 0.2658,
  "current_price": 185.42,
  "company_name": "Apple Inc.",
  "explanations": [...],
  "summary": "Multiple bullish signals detected...",
  "model_info": {
    "model_type": "XGBoost Classifier",
    "accuracy": 0.5624,
    "num_features": 13,
    "prediction_horizon": "Next Trading Day"
  }
}
```

### `GET /history/AAPL?tf=6m`

Returns OHLCV data for charting. Supported timeframes: `1d`, `5d`, `1m`, `6m`, `1y`

### `GET /info/AAPL`

Returns market cap, P/E, EPS, beta, dividend yield, 52-week range, daily change.

### `POST /compare`

```json
// Request
{ "tickers": ["NVDA", "AMD"], "timeframe": "6m" }

// Response — normalized price history for each ticker
```

---

## What I Learned

- **Time-series cross-validation** prevents data leakage — a critical detail for any ML work on sequential data
- **Feature engineering** (RSI, MACD, Bollinger Bands) has more impact on model performance than model selection
- **Probability scores** from `predict_proba` are more useful than binary predictions for communicating uncertainty
- **A clean frontend** turns a Jupyter notebook model into something that feels like a real product
- **Stock prediction is hard** — the model performs modestly, which is expected and honest. Markets are efficient.

---

## Disclaimer

**This tool is for educational and portfolio demonstration purposes only. It is not financial advice. Stock market predictions are inherently uncertain. Do not make investment decisions based on this tool.**

---

## License

MIT
