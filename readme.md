# 🔬 Amazon Market Intelligence

> Drop any Amazon listing URL → Get real review analysis + competitive intelligence + Google Trends + a Pixii-ready creative brief + AI chat analyst.

## What's new vs v1
| Feature | v1 (original) | v2 (this) |
|---|---|---|
| Review scraping | ❌ None | ✅ 50–150 real reviews per product |
| AI model | Gemini 2.5 Flash | Gemini 2.5 Flash |
| Purchase criteria | Inferred from titles | **From real review text** |
| Review sentiment chart | ❌ | ✅ Donut with star breakdown |
| Competitor weaknesses | ❌ | ✅ From their bad reviews |
| AI Chat assistant | ❌ | ✅ Ask anything about the market |
| Configurable depth | ❌ | ✅ Choose review pages + competitor count |

## Setup

```bash
git clone <your-repo>
cd amazon_intel
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
streamlit run app.py
```

## .env keys needed
```
SCRAPER_API_KEY=   # from scraperapi.com (~$50/mo, free tier available)
GEMINI_API_KEY=    # from aistudio.google.com (free)
```

## APIs used
1. **ScraperAPI** — scrapes Amazon listings + reviews + competitor search results
2. **Google Trends (pytrends)** — real search demand data, no API key needed
3. **Gemini 2.5 Flash** — review analysis, market insights, scorecard, creative brief, AI chat

## How it works
1. Paste any Amazon product URL
2. App scrapes your listing + up to 150 reviews from your product
3. Finds 5–9 competitors and scrapes their listings + reviews (~20 reviews each)
4. Gemini AI analyzes ALL reviews to find real purchase criteria, complaints, praises
5. Generates competitive scorecard, Google Trends chart, and 7-image Pixii creative brief
6. AI chat lets you ask follow-up questions about the market