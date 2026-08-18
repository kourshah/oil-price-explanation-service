"""
app.py — Standalone LLM explanation service.

This is a SEPARATE, independent repo from the graded oil-price-prediction
project. It does not import or modify anything from that repo.

How it works:
1. It calls your already-deployed prediction API (Render) to get the
   latest forecast (predicted_oil_price only — that's all the graded
   API currently exposes).
2. It independently fetches the current WTI price via yfinance, since
   the graded API doesn't expose the raw feature row to this repo.
3. It sends the prediction + current price to Claude via explain.py and
   returns a plain-language explanation.

Note: because this repo is intentionally isolated from the graded
project, it does NOT have access to the 26 engineered model features
(Momentum_7, Volatility_21, etc.) — those live only inside the graded
repo. The explanation here is based on price direction/magnitude only,
not per-feature attribution. If you later want feature-level detail,
the graded repo's /predict/latest endpoint would need to expose the
raw input row.
"""

import os
import requests
import yfinance as yf
from fastapi import FastAPI, HTTPException

from explain import explain_prediction

PREDICTION_API_URL = os.getenv(
    "PREDICTION_API_URL",
    "https://oil-price-api-3-0.onrender.com/predict/latest"
)

app = FastAPI(
    title="Oil Price Explanation Service",
    description="Standalone LLM layer that explains forecasts from the existing prediction API.",
    version="1.0.0",
)


@app.get("/")
def home():
    return {"status": "ok", "upstream_api": PREDICTION_API_URL}


def _get_current_wti_price() -> float:
    """Fetches the latest WTI close price independently via yfinance."""
    ticker = yf.Ticker("CL=F")
    hist = ticker.history(period="5d")
    if hist.empty:
        raise ValueError("Could not fetch current WTI price from yfinance.")
    return float(hist["Close"].iloc[-1])


@app.get("/explain")
def explain():
    """
    Calls the existing prediction API, fetches the current price
    independently, then generates a plain-language explanation.
    """
    try:
        resp = requests.get(PREDICTION_API_URL, timeout=120)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Upstream prediction API failed: {exc}")

    predicted_price = payload.get("predicted_oil_price")
    if predicted_price is None:
        raise HTTPException(status_code=502, detail="Upstream response missing predicted_oil_price.")

    try:
        current_price = _get_current_wti_price()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch current price: {exc}")

    explanation = explain_prediction(
        predicted_price=predicted_price,
        current_price=current_price,
        top_features={},  # not available to this isolated repo — see module docstring
    )

    return {
        "predicted_oil_price": predicted_price,
        "current_price": current_price,
        "explanation": explanation,
    }
