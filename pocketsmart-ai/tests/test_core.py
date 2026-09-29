import pytest

from pocketsmart.gemini_client import GeminiClient
from pocketsmart.planners import plan_home, plan_jewelry, plan_party
from pocketsmart.utils import allocate, extract_json, search_link

OFFLINE = GeminiClient(api_key="")  # forces demo mode


def test_allocate_sums_exactly():
    out = allocate(100001, {"a": 30, "b": 25, "c": 45})
    assert sum(out.values()) == 100001


def test_extract_json_handles_fences_and_noise():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Sure! {"a": 2} hope that helps') == {"a": 2}
    with pytest.raises(Exception):
        extract_json("no json here")


def test_search_link():
    assert "amazon.in" in search_link("Amazon", "led bulb")
    assert "amazon.in" in search_link("UnknownShop", "x")  # fallback


def test_home_demo_within_budget():
    res = plan_home(OFFLINE, 100000, {"Living Room": {"Lights": 3}, "Bedroom": {"Bed": 1, "Lights": 2}})
    assert res["within_budget"] and res["mode"] == "demo"
    assert all(i["link"].startswith("http") for r in res["rooms"] for i in r["items"])


def test_party_allocation_matches_budget():
    res = plan_party(OFFLINE, 100000, 50, "Wedding", "Banquet hall")
    assert sum(res["allocation"].values()) == 100000
    assert res["per_guest_catering"] > 0


def test_jewelry_demo_within_budget():
    res = plan_jewelry(OFFLINE, 10000, "Wedding", "Traditional")
    assert res["within_budget"] and len(res["recommendations"]) >= 3
