"""
explain.py — LLM-based plain-language explanation layer.

Standalone module: does not depend on the original oil-price-prediction
repo. It only needs a predicted price, a current price, and a small
dict of feature values (obtained by calling the existing live API).
"""

import os
import json
from anthropic import Anthropic

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
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

        response = _get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        raw_text = response.content[0].text.strip()
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        parsed = json.loads(raw_text)

        for key in ("summary", "key_drivers", "confidence_note"):
            if key not in parsed:
                return fallback

        return parsed

    except Exception:
        return fallback
