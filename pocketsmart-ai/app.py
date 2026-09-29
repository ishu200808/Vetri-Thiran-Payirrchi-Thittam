"""PocketSmart AI - Streamlit front end.  Run with:  streamlit run app.py"""
import pandas as pd
import streamlit as st

from pocketsmart.config import GEMINI_MODEL
from pocketsmart.gemini_client import GeminiClient
from pocketsmart.planners import plan_home, plan_jewelry, plan_party
from pocketsmart.planners.home import ITEM_CHOICES, ROOM_WEIGHTS
from pocketsmart.planners.jewelry import OCCASIONS, STYLES
from pocketsmart.planners.party import EVENT_SPLITS
from pocketsmart.utils import inr

st.set_page_config(page_title="PocketSmart AI", page_icon="💰", layout="wide")


@st.cache_resource
def get_client() -> GeminiClient:
    return GeminiClient()


client = get_client()

with st.sidebar:
    st.title("💰 PocketSmart AI")
    page = st.radio("Planner", ["🏠 Home Budget Planner", "🎉 Party Planner", "💍 Jewelry Planner"])
    st.divider()
    if client.available:
        st.success(f"Gemini connected\n\n`{GEMINI_MODEL}`")
    else:
        st.warning("No GEMINI_API_KEY found - running in **demo mode** with placeholder data.")
    st.caption("Prices are AI estimates. Links open a search on the platform, not a specific product page.")


def budget_banner(total, budget):
    if total <= budget:
        st.success(f"Estimated total {inr(total)} is within your budget of {inr(budget)} "
                   f"(saving {inr(budget - total)}).")
    else:
        st.error(f"Estimated total {inr(total)} exceeds your budget of {inr(budget)} by {inr(total - budget)}.")


def show_tips(tips):
    if tips:
        with st.expander("💡 Tips", expanded=True):
            for t in tips:
                st.write(f"- {t}")


# ----------------------------------------------------------------- HOME
if page.startswith("🏠"):
    st.header("🏠 Home Interior Planner")
    c1, c2, c3 = st.columns(3)
    budget = c1.number_input("Total budget (₹)", min_value=5000, value=150000, step=5000)
    style = c2.selectbox("Style", ["Modern", "Minimalist", "Scandinavian", "Traditional", "Industrial", "Boho"])
    city = c3.text_input("City (optional)")
    rooms_sel = st.multiselect("Rooms", list(ROOM_WEIGHTS), default=["Living Room", "Bedroom"])

    rooms = {}
    for room in rooms_sel:
        with st.expander(f"{room} - items & quantities", expanded=True):
            picked = st.multiselect("Items", ITEM_CHOICES, default=ITEM_CHOICES[:2], key=f"items_{room}")
            cols = st.columns(max(len(picked), 1))
            rooms[room] = {}
            for col, item in zip(cols, picked):
                rooms[room][item] = col.number_input(item, 1, 20, 1, key=f"{room}_{item}")

    if st.button("Generate plan", type="primary", disabled=not rooms):
        with st.spinner("Planning your home..."):
            res = plan_home(client, int(budget), rooms, style, city)
        budget_banner(res["grand_total"], budget)
        for room in res["rooms"]:
            st.subheader(f"{room['room']}  ·  budget {inr(room['allocated_budget'])}  ·  spent {inr(room['room_total'])}")
            for it in room["items"]:
                a, b, c, d = st.columns([3, 2, 2, 1])
                a.markdown(f"**{it['item']}** x{it['quantity']}  \n{it.get('product', '')}  \n*{it.get('why', '')}*")
                b.write(it.get("platform", ""))
                c.write(f"{inr(it['est_unit_price'])} each  \n**{inr(it['est_total'])}**")
                d.link_button("View", it["link"])
        show_tips(res.get("tips"))

# ---------------------------------------------------------------- PARTY
elif page.startswith("🎉"):
    st.header("🎉 Party Planner")
    c1, c2, c3 = st.columns(3)
    budget = c1.number_input("Total budget (₹)", min_value=5000, value=100000, step=5000)
    guests = c2.number_input("Guests", 2, 2000, 50)
    event = c3.selectbox("Event type", list(EVENT_SPLITS))
    c4, c5, c6 = st.columns(3)
    venue = c4.selectbox("Venue", ["Home", "Banquet hall", "Restaurant", "Hotel", "Outdoor / Farmhouse"])
    city = c5.text_input("City")
    stay = c6.checkbox("Guests need accommodation (OYO)")

    if st.button("Plan my party", type="primary"):
        with st.spinner("Allocating your budget..."):
            res = plan_party(client, int(budget), int(guests), event, venue, city, stay)
        budget_banner(res["primary_total"], budget)
        st.caption(f"Catering allowance ≈ {inr(res['per_guest_catering'])} per guest")
        chart = pd.DataFrame({"Category": list(res["allocation"]), "Budget": list(res["allocation"].values())})
        st.bar_chart(chart, x="Category", y="Budget")
        for cat in res["categories"]:
            st.subheader(f"{cat['category']}  ·  {inr(cat['allocated_budget'])}")
            for opt in cat["options"]:
                a, b, c, d = st.columns([3, 1, 1, 1])
                a.markdown(f"**{opt.get('name', '')}**  \n*{opt.get('why', '')}*")
                b.write(opt.get("platform", ""))
                c.write(inr(opt["est_cost"]))
                d.link_button("View", opt["link"])
        show_tips(res.get("tips"))

# -------------------------------------------------------------- JEWELRY
else:
    st.header("💍 Jewelry Planner")
    c1, c2, c3, c4 = st.columns(4)
    budget = c1.number_input("Budget (₹)", min_value=500, value=10000, step=500)
    occasion = c2.selectbox("Occasion", OCCASIONS)
    style = c3.selectbox("Style", STYLES)
    metal = c4.selectbox("Material", ["Any", "Gold-plated", "Silver / Oxidised", "Diamond-look (AD/CZ)", "Pearl", "Kundan / Polki"])
    upload = st.file_uploader("Optional: upload your outfit photo", type=["jpg", "jpeg", "png", "webp"])
    if upload:
        st.image(upload, width=240)

    if st.button("Find jewelry", type="primary"):
        with st.spinner("Matching jewelry to your look..."):
            res = plan_jewelry(client, int(budget), occasion, style, metal,
                               upload.getvalue() if upload else None,
                               upload.type if upload else "image/jpeg")
        budget_banner(res["total"], budget)
        if res.get("outfit_analysis"):
            st.info(f"👗 Outfit analysis: {res['outfit_analysis']}")
        for rec in res["recommendations"]:
            a, b, c, d = st.columns([3, 1, 1, 1])
            a.markdown(f"**{rec.get('piece', '')}**  \n*{rec.get('why', '')}*")
            b.write(rec.get("platform", ""))
            c.write(inr(rec["est_price"]))
            d.link_button("View", rec["link"])
        show_tips(res.get("styling_tips"))
