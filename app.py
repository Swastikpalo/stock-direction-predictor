"""
app.py
Flask API for the Stock Price Direction Predictor.
"""

import json
import yfinance as yf
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime, timedelta

from model.predict import predict_direction
from data.fetch import fetch_price_history

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Prediction history (in-memory for demo)
# ---------------------------------------------------------------------------
_prediction_history = []

# ---------------------------------------------------------------------------
# Stock list for autocomplete
# ---------------------------------------------------------------------------
_STOCK_LIST = None

def _load_stock_list():
    global _STOCK_LIST
    if _STOCK_LIST is not None:
        return _STOCK_LIST

    _STOCK_LIST = [
        {"ticker": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
        {"ticker": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ"},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ"},
        {"ticker": "GOOG", "name": "Alphabet Inc. Class C", "exchange": "NASDAQ"},
        {"ticker": "AMZN", "name": "Amazon.com Inc.", "exchange": "NASDAQ"},
        {"ticker": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ"},
        {"ticker": "META", "name": "Meta Platforms Inc.", "exchange": "NASDAQ"},
        {"ticker": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ"},
        {"ticker": "BRK.B", "name": "Berkshire Hathaway Inc.", "exchange": "NYSE"},
        {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "exchange": "NYSE"},
        {"ticker": "JNJ", "name": "Johnson & Johnson", "exchange": "NYSE"},
        {"ticker": "V", "name": "Visa Inc.", "exchange": "NYSE"},
        {"ticker": "UNH", "name": "UnitedHealth Group Inc.", "exchange": "NYSE"},
        {"ticker": "HD", "name": "The Home Depot Inc.", "exchange": "NYSE"},
        {"ticker": "PG", "name": "Procter & Gamble Co.", "exchange": "NYSE"},
        {"ticker": "MA", "name": "Mastercard Inc.", "exchange": "NYSE"},
        {"ticker": "DIS", "name": "The Walt Disney Company", "exchange": "NYSE"},
        {"ticker": "ADBE", "name": "Adobe Inc.", "exchange": "NASDAQ"},
        {"ticker": "CRM", "name": "Salesforce Inc.", "exchange": "NYSE"},
        {"ticker": "NFLX", "name": "Netflix Inc.", "exchange": "NASDAQ"},
        {"ticker": "CSCO", "name": "Cisco Systems Inc.", "exchange": "NASDAQ"},
        {"ticker": "PFE", "name": "Pfizer Inc.", "exchange": "NYSE"},
        {"ticker": "TMO", "name": "Thermo Fisher Scientific Inc.", "exchange": "NYSE"},
        {"ticker": "AVGO", "name": "Broadcom Inc.", "exchange": "NASDAQ"},
        {"ticker": "COST", "name": "Costco Wholesale Corporation", "exchange": "NASDAQ"},
        {"ticker": "ABT", "name": "Abbott Laboratories", "exchange": "NYSE"},
        {"ticker": "NKE", "name": "Nike Inc.", "exchange": "NYSE"},
        {"ticker": "KO", "name": "The Coca-Cola Company", "exchange": "NYSE"},
        {"ticker": "PEP", "name": "PepsiCo Inc.", "exchange": "NASDAQ"},
        {"ticker": "WMT", "name": "Walmart Inc.", "exchange": "NYSE"},
        {"ticker": "MRK", "name": "Merck & Co. Inc.", "exchange": "NYSE"},
        {"ticker": "LLY", "name": "Eli Lilly and Company", "exchange": "NYSE"},
        {"ticker": "AMD", "name": "Advanced Micro Devices Inc.", "exchange": "NASDAQ"},
        {"ticker": "INTC", "name": "Intel Corporation", "exchange": "NASDAQ"},
        {"ticker": "QCOM", "name": "Qualcomm Inc.", "exchange": "NASDAQ"},
        {"ticker": "TXN", "name": "Texas Instruments Inc.", "exchange": "NASDAQ"},
        {"ticker": "ORCL", "name": "Oracle Corporation", "exchange": "NYSE"},
        {"ticker": "IBM", "name": "International Business Machines", "exchange": "NYSE"},
        {"ticker": "NOW", "name": "ServiceNow Inc.", "exchange": "NYSE"},
        {"ticker": "UBER", "name": "Uber Technologies Inc.", "exchange": "NYSE"},
        {"ticker": "LYFT", "name": "Lyft Inc.", "exchange": "NASDAQ"},
        {"ticker": "SQ", "name": "Block Inc.", "exchange": "NYSE"},
        {"ticker": "PYPL", "name": "PayPal Holdings Inc.", "exchange": "NASDAQ"},
        {"ticker": "SHOP", "name": "Shopify Inc.", "exchange": "NYSE"},
        {"ticker": "SPOT", "name": "Spotify Technology S.A.", "exchange": "NYSE"},
        {"ticker": "SNAP", "name": "Snap Inc.", "exchange": "NYSE"},
        {"ticker": "PINS", "name": "Pinterest Inc.", "exchange": "NYSE"},
        {"ticker": "ZM", "name": "Zoom Video Communications", "exchange": "NASDAQ"},
        {"ticker": "ROKU", "name": "Roku Inc.", "exchange": "NASDAQ"},
        {"ticker": "COIN", "name": "Coinbase Global Inc.", "exchange": "NASDAQ"},
        {"ticker": "PLTR", "name": "Palantir Technologies Inc.", "exchange": "NASDAQ"},
        {"ticker": "RIVN", "name": "Rivian Automotive Inc.", "exchange": "NASDAQ"},
        {"ticker": "LCID", "name": "Lucid Group Inc.", "exchange": "NASDAQ"},
        {"ticker": "F", "name": "Ford Motor Company", "exchange": "NYSE"},
        {"ticker": "GM", "name": "General Motors Company", "exchange": "NYSE"},
        {"ticker": "BA", "name": "The Boeing Company", "exchange": "NYSE"},
        {"ticker": "CAT", "name": "Caterpillar Inc.", "exchange": "NYSE"},
        {"ticker": "GS", "name": "Goldman Sachs Group Inc.", "exchange": "NYSE"},
        {"ticker": "MS", "name": "Morgan Stanley", "exchange": "NYSE"},
        {"ticker": "C", "name": "Citigroup Inc.", "exchange": "NYSE"},
        {"ticker": "BAC", "name": "Bank of America Corporation", "exchange": "NYSE"},
        {"ticker": "WFC", "name": "Wells Fargo & Company", "exchange": "NYSE"},
        {"ticker": "AXP", "name": "American Express Company", "exchange": "NYSE"},
        {"ticker": "T", "name": "AT&T Inc.", "exchange": "NYSE"},
        {"ticker": "VZ", "name": "Verizon Communications Inc.", "exchange": "NYSE"},
        {"ticker": "TMUS", "name": "T-Mobile US Inc.", "exchange": "NASDAQ"},
        {"ticker": "CVX", "name": "Chevron Corporation", "exchange": "NYSE"},
        {"ticker": "XOM", "name": "Exxon Mobil Corporation", "exchange": "NYSE"},
        {"ticker": "COP", "name": "ConocoPhillips", "exchange": "NYSE"},
        {"ticker": "ABNB", "name": "Airbnb Inc.", "exchange": "NASDAQ"},
        {"ticker": "BKNG", "name": "Booking Holdings Inc.", "exchange": "NASDAQ"},
        {"ticker": "MAR", "name": "Marriott International Inc.", "exchange": "NASDAQ"},
        {"ticker": "SBUX", "name": "Starbucks Corporation", "exchange": "NASDAQ"},
        {"ticker": "MCD", "name": "McDonald's Corporation", "exchange": "NYSE"},
        {"ticker": "CMG", "name": "Chipotle Mexican Grill Inc.", "exchange": "NYSE"},
        {"ticker": "LOW", "name": "Lowe's Companies Inc.", "exchange": "NYSE"},
        {"ticker": "TGT", "name": "Target Corporation", "exchange": "NYSE"},
        {"ticker": "AMGN", "name": "Amgen Inc.", "exchange": "NASDAQ"},
        {"ticker": "GILD", "name": "Gilead Sciences Inc.", "exchange": "NASDAQ"},
        {"ticker": "MRNA", "name": "Moderna Inc.", "exchange": "NASDAQ"},
        {"ticker": "ISRG", "name": "Intuitive Surgical Inc.", "exchange": "NASDAQ"},
        {"ticker": "PANW", "name": "Palo Alto Networks Inc.", "exchange": "NASDAQ"},
        {"ticker": "CRWD", "name": "CrowdStrike Holdings Inc.", "exchange": "NASDAQ"},
        {"ticker": "ZS", "name": "Zscaler Inc.", "exchange": "NASDAQ"},
        {"ticker": "FTNT", "name": "Fortinet Inc.", "exchange": "NASDAQ"},
        {"ticker": "SNOW", "name": "Snowflake Inc.", "exchange": "NYSE"},
        {"ticker": "DDOG", "name": "Datadog Inc.", "exchange": "NASDAQ"},
        {"ticker": "MDB", "name": "MongoDB Inc.", "exchange": "NASDAQ"},
        {"ticker": "NET", "name": "Cloudflare Inc.", "exchange": "NYSE"},
        {"ticker": "TTD", "name": "The Trade Desk Inc.", "exchange": "NASDAQ"},
        {"ticker": "SMCI", "name": "Super Micro Computer Inc.", "exchange": "NASDAQ"},
        {"ticker": "ARM", "name": "Arm Holdings plc", "exchange": "NASDAQ"},
        {"ticker": "MRVL", "name": "Marvell Technology Inc.", "exchange": "NASDAQ"},
        {"ticker": "MU", "name": "Micron Technology Inc.", "exchange": "NASDAQ"},
        {"ticker": "LRCX", "name": "Lam Research Corporation", "exchange": "NASDAQ"},
        {"ticker": "AMAT", "name": "Applied Materials Inc.", "exchange": "NASDAQ"},
        {"ticker": "KLAC", "name": "KLA Corporation", "exchange": "NASDAQ"},
        {"ticker": "ASML", "name": "ASML Holding N.V.", "exchange": "NASDAQ"},
        {"ticker": "TSM", "name": "Taiwan Semiconductor Manufacturing", "exchange": "NYSE"},
        {"ticker": "SONY", "name": "Sony Group Corporation", "exchange": "NYSE"},
        {"ticker": "DELL", "name": "Dell Technologies Inc.", "exchange": "NYSE"},
    ]
    return _STOCK_LIST


def get_company_name(ticker: str) -> str:
    stock_list = _load_stock_list()
    for stock in stock_list:
        if stock["ticker"].upper() == ticker.upper():
            return stock["name"]
    try:
        info = yf.Ticker(ticker).info
        return info.get("longName") or info.get("shortName") or ticker
    except Exception:
        return ticker


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    query = request.args.get("q", "").strip().upper()
    if not query:
        return jsonify([])

    stock_list = _load_stock_list()
    matches = []

    for stock in stock_list:
        ticker_match = stock["ticker"].upper().startswith(query)
        name_match = query in stock["name"].upper()
        if ticker_match or name_match:
            matches.append(stock)
        if len(matches) >= 10:
            break

    if not matches and len(query) >= 1:
        try:
            info = yf.Ticker(query).info
            name = info.get("longName") or info.get("shortName")
            if name:
                matches.append({"ticker": query, "name": name, "exchange": info.get("exchange", "")})
        except Exception:
            pass

    return jsonify(matches)


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)
    if not data or "ticker" not in data:
        return jsonify({"error": "Missing 'ticker' in request body."}), 400

    ticker = data["ticker"].strip().upper()
    if len(ticker) > 10:
        return jsonify({"error": f"Invalid ticker symbol: '{ticker}'"}), 400

    try:
        result = predict_direction(ticker)
        result["company_name"] = get_company_name(ticker)

        # Store prediction in history
        _prediction_history.append({
            "ticker": ticker,
            "direction": result["direction"],
            "confidence": result["confidence"],
            "price": result["current_price"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        # Keep last 20
        if len(_prediction_history) > 20:
            _prediction_history.pop(0)

        return jsonify(result)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


@app.route("/history/<ticker>")
def history(ticker: str):
    ticker = ticker.strip().upper()
    tf = request.args.get("tf", "1m").lower()
    days_map = {"1d": 2, "5d": 7, "1m": 30, "6m": 180, "1y": 365}
    days = days_map.get(tf, 30)

    try:
        prices = fetch_price_history(ticker, days=days)
        return jsonify(prices)
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Failed to fetch history: {str(e)}"}), 500


@app.route("/info/<ticker>")
def info(ticker: str):
    ticker = ticker.strip().upper()
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return jsonify({
            "ticker": ticker,
            "company_name": info.get("longName") or info.get("shortName") or ticker,
            "exchange": info.get("exchange", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap"),
            "volume": info.get("volume"),
            "avg_volume": info.get("averageVolume"),
            "pe_ratio": info.get("trailingPE"),
            "eps": info.get("trailingEps"),
            "beta": info.get("beta"),
            "dividend_yield": info.get("dividendYield"),
            "week_52_high": info.get("fiftyTwoWeekHigh"),
            "week_52_low": info.get("fiftyTwoWeekLow"),
            "day_change": info.get("regularMarketChange"),
            "day_change_pct": info.get("regularMarketChangePercent"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose"),
            "open_price": info.get("open") or info.get("regularMarketOpen"),
            "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
        })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch info: {str(e)}"}), 500


@app.route("/news/<ticker>")
def news(ticker: str):
    ticker = ticker.strip().upper()
    try:
        stock = yf.Ticker(ticker)
        news_data = stock.news or []

        articles = []
        for item in news_data[:8]:
            content = item.get("content", {})
            articles.append({
                "title": content.get("title", "No title"),
                "publisher": content.get("provider", {}).get("displayName", "Unknown"),
                "link": content.get("canonicalUrl", {}).get("url", "#"),
                "published": content.get("pubDate", ""),
            })

        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch news: {str(e)}"}), 500


@app.route("/watchlist_prices", methods=["POST"])
def watchlist_prices():
    """Return current price and day change for a list of tickers."""
    data = request.get_json(silent=True)
    if not data or "tickers" not in data:
        return jsonify([])

    results = []
    for ticker in data["tickers"]:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            results.append({
                "ticker": ticker,
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "change_pct": info.get("regularMarketChangePercent"),
            })
        except Exception:
            results.append({"ticker": ticker, "price": None, "change_pct": None})

    return jsonify(results)


@app.route("/compare", methods=["POST"])
def compare():
    """Return price history for two tickers for comparison."""
    data = request.get_json(silent=True)
    if not data or "tickers" not in data or len(data["tickers"]) < 2:
        return jsonify({"error": "Provide at least 2 tickers."}), 400

    tf = data.get("timeframe", "1m")
    days_map = {"1d": 2, "5d": 7, "1m": 30, "6m": 180, "1y": 365}
    days = days_map.get(tf, 30)

    result = {}
    for ticker in data["tickers"][:2]:
        ticker = ticker.strip().upper()
        try:
            prices = fetch_price_history(ticker, days=days)
            result[ticker] = prices
        except Exception:
            result[ticker] = []

    return jsonify(result)


@app.route("/prediction_history")
def prediction_history_route():
    """Return recent prediction history."""
    return jsonify(_prediction_history[-20:][::-1])


if __name__ == "__main__":
    app.run(debug=True, port=5000)