# 💰 PocketSmart AI

**A GenAI-powered, cross-platform, budget-based recommendation system.**
PocketSmart AI turns a budget and a few preferences into curated suggestions for home interiors, parties and jewelry, drawing on popular Indian platforms such as Amazon, Flipkart, IKEA, Pepperfry, Swiggy, Zomato, OYO, Myntra and BlueStone.

## ✨ Features

| Planner | What you enter | What you get |
|---|---|---|
| 🏠 **Home Budget Planner** | Budget, style, rooms, item quantities (lights, fans, dining table...) | Room-wise budget split + one cost-effective product per item (IKEA / Amazon / Flipkart / Pepperfry) balanced across function, style and price |
| 🎉 **Party Planner** | Budget, guest count, event type, venue, stay needed? | Budget split across catering, decoration, entertainment, stay/venue and misc, with options from Swiggy, Zomato, OYO and Amazon, tuned to birthday / corporate / wedding etc. |
| 💍 **Jewelry Planner** | Budget, occasion, style, material, *optional outfit photo* | A matching jewelry set from Amazon, Flipkart, Myntra, BlueStone, colour-coordinated with your outfit (multimodal Gemini) |

Extra touches: budget-fit banners, per-guest catering allowance, cost chart, "View" buttons that open a platform search, and a **demo mode** that works with no API key.

## 🏗️ Architecture

```
pocketsmart-ai/
├── app.py                     # Streamlit UI (3 planners)
├── pocketsmart/
│   ├── config.py              # env vars (API key, model)
│   ├── gemini_client.py       # Gemini wrapper -> parsed JSON (text + image)
│   ├── utils.py               # budget allocation, JSON parsing, search links
│   └── planners/
│       ├── home.py            # Scenario 1
│       ├── party.py           # Scenario 2
│       └── jewelry.py         # Scenario 3
├── tests/test_core.py         # unit tests (run offline)
├── requirements.txt
├── .env.example
└── LICENSE
```

**How it works:** Python does the deterministic budget maths (room weights and event-type splits, always summing exactly to your budget). Gemini then fills each slice with concrete products/vendors and reasons, returning strict JSON. Python validates the output, recomputes totals, attaches platform search links and flags overspend.

## 🚀 Getting started

```bash
git clone https://github.com/<your-username>/pocketsmart-ai.git
cd pocketsmart-ai

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then paste your key into .env
streamlit run app.py
```

Get a free Gemini API key at <https://aistudio.google.com/apikey>.
Without a key the app runs in **demo mode** with placeholder data.

### Configuration (`.env`)

| Variable | Default | Notes |
|---|---|---|
| `GEMINI_API_KEY` | - | Required for real recommendations |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Any Gemini model that supports JSON output and images |

> **Note on the model:** the original brief mentions "Gemini 1.5 Flash Pro". Google's 1.5 models (Flash and Pro are separate models) have been retired, so the default is a current Flash model. Change `GEMINI_MODEL` to switch, e.g. to a Pro model for higher quality.

## 🧪 Tests

```bash
pytest -q
```

## ⚠️ Limitations (please read)

- Amazon, Flipkart, Swiggy, Zomato, OYO etc. do **not** offer open public product APIs. Products and prices are **AI-generated estimates**, and "View" links open a **search** on the platform, not a verified product page.
- To get live prices, add per-platform integrations (official affiliate/partner APIs) inside `pocketsmart/planners/` and feed the results to Gemini as context.
- Platform names and trademarks belong to their owners; this project is not affiliated with them.

## 🗺️ Roadmap

- Live price/availability via partner APIs
- Save & export plans (PDF / CSV)
- Multi-currency and multi-city support
- User accounts and plan history

## 📄 License

MIT - see [LICENSE](LICENSE).
