"""Scenario 2 - AI-based party budget planning."""
from ..gemini_client import GeminiClient, GeminiError
from ..utils import allocate, search_link, to_number

# Percentage split of the budget per event type.
EVENT_SPLITS = {
    "Birthday":     {"Catering": 45, "Decoration": 20, "Entertainment": 20, "Stay / Venue": 10, "Miscellaneous": 5},
    "Corporate":    {"Catering": 40, "Decoration": 10, "Entertainment": 15, "Stay / Venue": 30, "Miscellaneous": 5},
    "Wedding":      {"Catering": 40, "Decoration": 25, "Entertainment": 15, "Stay / Venue": 15, "Miscellaneous": 5},
    "Anniversary":  {"Catering": 40, "Decoration": 25, "Entertainment": 15, "Stay / Venue": 15, "Miscellaneous": 5},
    "Baby Shower":  {"Catering": 40, "Decoration": 30, "Entertainment": 15, "Stay / Venue": 10, "Miscellaneous": 5},
}
PLATFORMS = {"Catering": "Swiggy", "Decoration": "Amazon", "Entertainment": "Amazon",
             "Stay / Venue": "OYO", "Miscellaneous": "Amazon"}


def _prompt(budget, guests, event, venue, city, alloc, need_stay):
    cats = "\n".join(f"- {c}: INR {v}" for c, v in alloc.items())
    return f"""Plan a {event} party. Total budget INR {int(budget)}, {guests} guests, venue: {venue}, city: {city or 'India'}.
Guests need accommodation: {need_stay}.
Budget per category:
{cats}

For each category give 2-3 concrete options sourced from Swiggy, Zomato (catering/entertainment/venues),
OYO (stay/venue) or Amazon/Flipkart (decor, supplies). Keep option costs within the category budget and
tailor everything to a {event}.

Return JSON exactly like:
{{"categories":[{{"category":"Catering","options":[{{"name":"option name","platform":"Swiggy",
"est_cost":15000,"why":"one short sentence","search_query":"short search text"}}]}}],
"tips":["short tip"]}}"""


def _fallback(alloc, guests, event):
    data = {"categories": [], "tips": ["Demo mode: add a GEMINI_API_KEY for real AI recommendations."]}
    for cat, amount in alloc.items():
        plat = PLATFORMS.get(cat, "Amazon")
        data["categories"].append({"category": cat, "options": [{
            "name": f"{event} {cat.lower()} package", "platform": plat,
            "est_cost": round(amount * 0.9), "why": "Placeholder sized to the category budget.",
            "search_query": f"{event} {cat} for {guests} guests"}]})
    return data


def plan_party(client: GeminiClient, budget: int, guests: int, event_type: str,
               venue: str, city: str = "", need_stay: bool = False) -> dict:
    split = dict(EVENT_SPLITS.get(event_type, EVENT_SPLITS["Birthday"]))
    if not need_stay and event_type != "Corporate":
        # Move the stay share into catering + decoration when nobody needs a room.
        extra = split["Stay / Venue"] // 2
        split["Stay / Venue"] -= extra
        split["Catering"] += extra
    alloc = allocate(int(budget), split)
    data, err = None, ""
    if client.available:
        try:
            data = client.generate_json(_prompt(budget, guests, event_type, venue, city, alloc, need_stay))
            data["mode"] = "gemini"
        except GeminiError as e:
            err = str(e)
    if data is None:
        data = _fallback(alloc, guests, event_type)
        data["mode"] = "demo"
        if err:
            data["tips"].append(f"AI call failed, showing demo data. ({err})")

    total = 0.0
    for cat in data.get("categories", []):
        cat["allocated_budget"] = alloc.get(cat.get("category"), 0)
        for opt in cat.get("options", []):
            opt["est_cost"] = to_number(opt.get("est_cost"))
            opt["link"] = search_link(opt.get("platform"), opt.get("search_query") or opt.get("name"))
        # Assume the first (primary) option is the one chosen for the plan total.
        if cat.get("options"):
            total += cat["options"][0]["est_cost"]
    data.update({
        "budget": budget, "guests": guests, "allocation": alloc,
        "per_guest_catering": alloc.get("Catering", 0) / max(guests, 1),
        "primary_total": total, "within_budget": total <= budget,
    })
    return data
