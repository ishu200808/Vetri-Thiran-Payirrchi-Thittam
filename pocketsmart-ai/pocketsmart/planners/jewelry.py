"""Scenario 3 - Jewelry recommendations for occasions."""
from typing import Optional

from ..gemini_client import GeminiClient, GeminiError
from ..utils import search_link, to_number

OCCASIONS = ["Wedding", "Engagement", "Festival", "Party / Cocktail", "Office / Daily wear", "Anniversary", "Gifting"]
STYLES = ["Traditional", "Modern / Minimal", "Boho", "Statement", "Vintage", "Indo-western"]
PLATFORMS = ["Amazon", "Flipkart", "Myntra", "BlueStone"]


def _prompt(budget, occasion, style, metal, has_image):
    img = ("An outfit photo is attached: describe its main colours and neckline in 'outfit_analysis' "
           "and pick jewelry that colour-coordinates with it.") if has_image else \
          "No outfit image was provided; set 'outfit_analysis' to an empty string."
    return f"""Recommend jewelry. Total budget INR {int(budget)}. Occasion: {occasion}. Style: {style}.
Preferred metal/material: {metal}. {img}
Suggest 3-5 pieces that form a coherent set (e.g. necklace, earrings, bangles) from Amazon, Flipkart,
Myntra or BlueStone. The SUM of est_price must not exceed the budget.

Return JSON exactly like:
{{"outfit_analysis":"","recommendations":[{{"piece":"Kundan choker necklace","platform":"Amazon",
"est_price":1800,"why":"one short sentence","search_query":"short search text"}}],
"styling_tips":["short tip"]}}"""


def _fallback(budget, occasion, style):
    pieces = ["Necklace", "Earrings", "Bangles / Bracelet", "Ring"]
    share = budget * 0.85 / len(pieces)
    return {"outfit_analysis": "", "styling_tips": ["Demo mode: add a GEMINI_API_KEY for real AI recommendations."],
            "recommendations": [{"piece": f"{style} {p}", "platform": PLATFORMS[i % 4], "est_price": round(share),
                                 "why": f"Placeholder pick for {occasion}.", "search_query": f"{style} {p} {occasion}"}
                                for i, p in enumerate(pieces)]}


def plan_jewelry(client: GeminiClient, budget: int, occasion: str, style: str, metal: str = "Any",
                 image_bytes: Optional[bytes] = None, mime_type: str = "image/jpeg") -> dict:
    data, err = None, ""
    if client.available:
        try:
            data = client.generate_json(_prompt(budget, occasion, style, metal, bool(image_bytes)),
                                        image_bytes=image_bytes, mime_type=mime_type)
            data["mode"] = "gemini"
        except GeminiError as e:
            err = str(e)
    if data is None:
        data = _fallback(budget, occasion, style)
        data["mode"] = "demo"
        if err:
            data["styling_tips"].append(f"AI call failed, showing demo data. ({err})")

    total = 0.0
    for rec in data.get("recommendations", []):
        rec["est_price"] = to_number(rec.get("est_price"))
        rec["link"] = search_link(rec.get("platform"), rec.get("search_query") or rec.get("piece"))
        total += rec["est_price"]
    data.update({"budget": budget, "total": total, "within_budget": total <= budget})
    return data
