# Oil Price Explanation Service

A standalone LLM layer that adds plain-language explanations on top of an
existing WTI oil price forecasting API. Built as a separate repo so it
never touches the original graded project.

Uses Google's Gemini API (free tier — no credit card required).

## How it works
1. Calls the existing deployed prediction API to get `predicted_oil_price`.
2. Independently fetches the current WTI price via `yfinance`.
3. Sends both to Gemini to generate a short, plain-English explanation.
4. Exposes a single `/explain` endpoint returning the forecast + explanation.

## Setup
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your-key-here
export PREDICTION_API_URL=https://oil-price-api-3-0.onrender.com/predict/latest  # optional, this is the default
uvicorn app:app --reload
```

Then visit `http://localhost:8000/explain`.

Get a free Gemini API key at https://aistudio.google.com/api-keys — no
credit card needed.

## Known limitation
This repo is intentionally isolated from the original forecasting project,
so it does not have access to the 26 engineered model features
(Momentum_7, Volatility_21, etc.) that drove the prediction — those live
only inside the graded repo's `predict.py`. The explanation here is based
on price direction and magnitude only, not per-feature attribution.

## Deployment
Deploy on Render (or any host) as its own service, separate from the
existing prediction API deployment. Set `GEMINI_API_KEY` as an
environment variable on the host — never commit it to the repo.
