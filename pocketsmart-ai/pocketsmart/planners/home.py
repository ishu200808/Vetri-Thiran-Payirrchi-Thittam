"""Scenario 1 - Home interior planning with smart budget allocation."""
from ..gemini_client import GeminiClient, GeminiError
from ..utils import allocate, search_link, to_number

# Relative share of the budget each room type typically needs.
ROOM_WEIGHTS = {
    "Living Room": 30, "Kitchen": 25, "Bedroom": 25, "Dining Room": 20,
    "Kids Room": 15, "Study/Office": 15, "Bathroom": 10, "Balcony": 5,
}
ITEM_CHOICES = [
    "Lights", "Ceiling Fans", "Dining Table", "Sofa", "Bed", "Wardrobe",
    "Curtains", "Rugs", "Wall Decor", "Storage Units", "Study Table", "Chairs",
]
PLATFORMS = ["IKEA", "Amazon", "Flipkart", "Pepperfry"]


def _prompt(budget, alloc, rooms, style, city):
    lines = []
    for room, items in rooms.items():
        wanted = ", ".join(f"{q} x {name}" for name, q in items.items() if q > 0)
        lines.append(f"- {room} (budget INR {alloc[room]}): {wanted}")
    return f"""Plan home interiors. Total budget INR {int(budget)}. Style: {style}. City: {city or 'India'}.
Rooms and items:
{chr(10).join(lines)}

For EVERY requested item pick ONE cost-effective product balancing functionality, style and price.
Choose the platform (IKEA, Amazon, Flipkart or Pepperfry) that suits the item best.
Keep each room's total within its budget.

Return JSON exactly like:
{{"rooms":[{{"room":"Living Room","items":[{{"item":"Lights","quantity":3,"platform":"IKEA",
"product":"product name","est_unit_price":1499,"why":"one short sentence","search_query":"short search text"}}]}}],
"tips":["short money-saving tip"]}}"""


def _fallback(alloc, rooms):
    """Offline demo data so the app runs without an API key."""
    data = {"rooms": [], "tips": ["Demo mode: add a GEMINI_API_KEY for real AI recommendations."]}
    for room, items in rooms.items():
        wanted = {k: q for k, q in items.items() if q > 0}
        total_qty = sum(wanted.values()) or 1
        unit = alloc[room] / total_qty * 0.9
        rows = []
        for i, (name, qty) in enumerate(wanted.items()):
            rows.append({
                "item": name, "quantity": qty, "platform": PLATFORMS[i % len(PLATFORMS)],
                "product": f"Budget-friendly {name.lower()}", "est_unit_price": round(unit),
                "why": "Placeholder pick sized to your room budget.",
                "search_query": f"{name} for {room}",
            })
        data["rooms"].append({"room": room, "items": rows})
    return data


def _postprocess(data, budget, alloc):
    grand = 0.0
    for room in data.get("rooms", []):
        room_total = 0.0
        for it in room.get("items", []):
            qty = int(to_number(it.get("quantity"), 1)) or 1
            unit = to_number(it.get("est_unit_price"))
            it["quantity"], it["est_unit_price"] = qty, unit
            it["est_total"] = unit * qty
            it["link"] = search_link(it.get("platform"), it.get("search_query") or it.get("product"))
            room_total += it["est_total"]
        room["allocated_budget"] = alloc.get(room.get("room"), 0)
        room["room_total"] = room_total
        grand += room_total
    data["grand_total"] = grand
    data["budget"] = budget
    data["within_budget"] = grand <= budget
    return data


def plan_home(client: GeminiClient, budget: int, rooms: dict, style: str = "Modern", city: str = "") -> dict:
    """rooms = {"Living Room": {"Lights": 3, "Ceiling Fans": 1}, ...}"""
    weights = {r: ROOM_WEIGHTS.get(r, 10) for r in rooms}
    alloc = allocate(int(budget), weights)
    data, mode = None, "demo"
    if client.available:
        try:
            data, mode = client.generate_json(_prompt(budget, alloc, rooms, style, city)), "gemini"
        except GeminiError as e:
            data = None
            err = str(e)
    if data is None:
        data = _fallback(alloc, rooms)
        if client.available:
            data["tips"].append(f"AI call failed, showing demo data. ({err})")
    data = _postprocess(data, budget, alloc)
    data["mode"] = mode
    return data
