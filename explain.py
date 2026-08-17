"""
explain.py — LLM-based plain-language explanation layer.

Standalone module: does not depend on the original oil-price-prediction
repo. It only needs a predicted price, a current price, and a small
dict of feature values (obtained by calling the existing live API).

Uses Google's Gemini API (free tier) instead of a paid API — no credit
card required. Get a key at https://aistudio.google.com/api-keys
"""

import os
import json
from google import genai

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def explain_prediction(predicted_price: float, current_price: float, top_features: dict) -> dict:
    """
    Turns a raw price forecast + a few interpretable feature values into
    a short plain-language explanation.

    Returns dict with keys: "summary", "key_drivers" (list[str]), "confidence_note".
    Falls back to a safe default if anything fails, so it never crashes the caller.
    """
    fallback = {
        "summary": "Explanation temporarily unavailable.",
        "key_drivers": [],
        "confidence_note": "Model estimate only — not financial advice."
    }

    try:
        direction = "up" if predicted_price > current_price else "down"
        change_pct = abs(predicted_price - current_price) / current_price * 100

        prompt = f"""You are explaining a WTI crude oil price forecast to a non-technical reader.

Current price: ${current_price:.2f}
Predicted next-value price: ${predicted_price:.2f} ({direction}, {change_pct:.1f}% change)
Key model input values (most recent trading day): {json.dumps(top_features)}

Respond with ONLY valid JSON, no other text, in exactly this shape:
{{
  "summary": "2 sentence plain-English explanation of the forecast",
  "key_drivers": ["short phrase 1", "short phrase 2", "short phrase 3"],
  "confidence_note": "1 sentence noting this is a model estimate, not financial advice"
}}"""

        response = _get_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        raw_text = response.text.strip()
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        parsed = json.loads(raw_text)

        for key in ("summary", "key_drivers", "confidence_note"):
            if key not in parsed:
                return fallback

        return parsed

    except Exception:
        return fallback
