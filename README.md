# 📈 Stock Price Direction Predictor

An ML-powered web application that predicts whether a stock's next trading day close will be **UP** or **DOWN**, with a confidence score. Built with Flask, Scikit-learn, XGBoost, and Chart.js.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-orange)

---

## Features

- **13 technical indicators** engineered from raw OHLCV data (SMA, EMA, RSI, MACD, Bollinger Bands, volatility, volume ratios)
- **3 model comparison** — Logistic Regression, Random Forest, and XGBoost evaluated side-by-side
- **Time-series aware splitting** — walk-forward 80/20 split with no data leakage
- **REST API** serving real-time predictions via Flask
- **Live market data** integration through yfinance
- **Interactive dark-themed frontend** with Chart.js price visualization and color-coded confidence

---

## Tech Stack

| Layer            | Technology                              |
|------------------|-----------------------------------------|
| Backend          | Python, Flask, Flask-CORS               |
| Machine Learning | Scikit-learn, XGBoost                   |
| Data             | yfinance, Pandas, NumPy                 |
| Frontend         | HTML, CSS, JavaScript, Chart.js         |
| Serialization    | Joblib                                  |

---

## Project Structure

```
stock-predictor/
├── app.py                  # Flask API (main entry point)
├── model/
│   ├── train.py            # Model training script
│   ├── features.py         # Feature engineering (13 indicators)
│   ├── predict.py          # Prediction logic
│   └── saved/
│       └── model.joblib    # Trained model (generated)
├── data/
│   └── fetch.py            # yfinance data fetching utilities
├── static/
│   ├── style.css           # Frontend styles (dark theme)
│   └── script.js           # Frontend logic + Chart.js rendering
├── templates/
│   └── index.html          # Main frontend page
├── requirements.txt
└── README.md
```

---

## Setup & Run

### 1. Clone and install dependencies

```bash
git clone https://github.com/yourusername/stock-predictor.git
cd stock-predictor
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Train the model

```bash
python -m model.train           # Defaults to AAPL
python -m model.train MSFT      # Or specify a ticker
```

This will compare all three models and save the best performer to `model/saved/model.joblib`.

### 3. Start the server

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## API Endpoints

### `POST /predict`

Request:
```json
{ "ticker": "AAPL" }
```

Response:
```json
{
  "ticker": "AAPL",
  "direction": "UP",
  "confidence": 0.7342,
  "current_price": 185.42,
  "features_used": ["SMA_10", "SMA_50", "EMA_12", "..."]
}
```

### `GET /history/<ticker>`

Response:
```json
[
  { "date": "2026-03-06", "close": 185.42 },
  { "date": "2026-03-07", "close": 186.10 }
]
```

---

## Model Details

### Features (13 total)

| Feature          | Description                            |
|------------------|----------------------------------------|
| SMA_10           | 10-day simple moving average           |
| SMA_50           | 50-day simple moving average           |
| EMA_12           | 12-day exponential moving average      |
| RSI_14           | 14-day relative strength index         |
| MACD             | MACD line value                        |
| MACD_signal      | MACD signal line                       |
| BB_upper         | Bollinger Band upper                   |
| BB_lower         | Bollinger Band lower                   |
| daily_return     | Today's percentage return              |
| volume_change    | Percentage change in volume            |
| volatility_10    | 10-day rolling std of returns          |
| price_vs_sma50   | Current price / SMA_50 ratio           |
| volume_sma_ratio | Current volume / 10-day avg volume     |

### Training Approach

- **Target**: 1 if next day's close > today's close, else 0
- **Split**: Walk-forward (first 80% train, last 20% test) — no shuffling to prevent temporal data leakage
- **Models compared**: Logistic Regression (baseline), Random Forest, XGBoost
- **Best model selected by**: F1 score
- **Serialization**: Joblib

---

## Disclaimer

⚠️ **This tool is for educational and portfolio demonstration purposes only. It is not financial advice. Stock market predictions are inherently uncertain.**

---

## License
