"""Shared helpers: budget maths, JSON parsing, platform search links."""
import json
import re
from urllib.parse import quote_plus

from .config import CURRENCY

PLATFORM_SEARCH = {
    "amazon": "https://www.amazon.in/s?k={q}",
    "flipkart": "https://www.flipkart.com/search?q={q}",
    "ikea": "https://www.ikea.com/in/en/search/?q={q}",
    "pepperfry": "https://www.pepperfry.com/site_product/search?q={q}",
    "urban ladder": "https://www.urbanladder.com/products?q={q}",
    "myntra": "https://www.myntra.com/{q}",
    "swiggy": "https://www.swiggy.com/search?query={q}",
    "zomato": "https://www.zomato.com/search?q={q}",
    "oyo": "https://www.oyorooms.com/search?query={q}",
    "bluestone": "https://www.bluestone.com/search?q={q}",
}


def allocate(total: int, weights: dict) -> dict:
    """Split `total` by weights into integers that add up exactly to `total`."""
    if not weights:
        return {}
    s = sum(weights.values())
    out = {k: int(total * v / s) for k, v in weights.items()}
    remainder = total - sum(out.values())
    for k in list(out)[:remainder]:
        out[k] += 1
    return out


def extract_json(text: str) -> dict:
    """Parse JSON from a model reply, tolerating code fences and stray prose."""
    text = re.sub(r"```(?:json)?", "", text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def search_link(platform: str, query: str) -> str:
    """Best-effort search URL on the given platform (falls back to Amazon)."""
    template = PLATFORM_SEARCH.get((platform or "").strip().lower(), PLATFORM_SEARCH["amazon"])
    return template.format(q=quote_plus(query or ""))


def to_number(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def inr(amount: float) -> str:
    return f"{CURRENCY}{amount:,.0f}"
