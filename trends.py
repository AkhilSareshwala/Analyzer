from pytrends.request import TrendReq
import re


def extract_search_keywords(product_title: str) -> str:
    title = re.sub(r'\b(UK|US|EU|CM)\d+\b', '', product_title, flags=re.IGNORECASE)
    title = re.sub(r'\b[A-Z]{2,}\d+[A-Z0-9]*\b', '', title)
    title = re.sub(r'\d+\s*(ml|mg|kg|g|l|pack|piece|pcs|count)\b', '', title, flags=re.IGNORECASE)
    words = [w for w in title.split() if len(w) > 2][:4]
    return " ".join(words)


def get_trend_data(product_title: str, geo: str = "IN"):
    keyword = extract_search_keywords(product_title)
    print(f"Fetching Google Trends for: '{keyword}' in {geo}")
    try:
        pytrends = TrendReq(hl='en-US', tz=330 if geo == "IN" else 360, timeout=(10, 25))
        pytrends.build_payload([keyword], cat=0, timeframe='today 12-m', geo=geo)
        interest_df = pytrends.interest_over_time()

        if interest_df.empty or keyword not in interest_df.columns:
            return get_fallback_trends(keyword)

        values = interest_df[keyword].tolist()
        dates = [str(d.date()) for d in interest_df.index.tolist()]

        if len(values) >= 8:
            first_quarter = sum(values[:len(values)//4]) / (len(values)//4)
            last_quarter = sum(values[-len(values)//4:]) / (len(values)//4)
            trend_pct = ((last_quarter - first_quarter) / max(first_quarter, 1)) * 100
        else:
            trend_pct = 0

        peak_idx = values.index(max(values))
        peak_date = dates[peak_idx] if peak_idx < len(dates) else "N/A"
        current_interest = values[-1] if values else 0
        avg_interest = sum(values) / len(values) if values else 0

        if trend_pct > 15:
            trend_label = "🚀 Rapidly Growing"; trend_color = "#00d4aa"
        elif trend_pct > 5:
            trend_label = "📈 Growing"; trend_color = "#00d4aa"
        elif trend_pct > -5:
            trend_label = "➡️ Stable"; trend_color = "#f5a623"
        elif trend_pct > -15:
            trend_label = "📉 Declining"; trend_color = "#e94560"
        else:
            trend_label = "⚠️ Sharply Declining"; trend_color = "#e94560"

        try:
            related = pytrends.related_queries()
            top_queries = []
            if keyword in related and related[keyword].get('top') is not None:
                top_queries = related[keyword]['top']['query'].head(5).tolist()
            rising_queries = []
            if keyword in related and related[keyword].get('rising') is not None:
                rising_queries = related[keyword]['rising']['query'].head(5).tolist()
        except:
            top_queries = []; rising_queries = []

        return {
            "keyword": keyword, "dates": dates, "values": values,
            "trend_pct": round(trend_pct, 1), "trend_label": trend_label,
            "trend_color": trend_color, "current_interest": current_interest,
            "avg_interest": round(avg_interest, 1), "peak_date": peak_date,
            "top_queries": top_queries, "rising_queries": rising_queries,
            "geo": geo, "success": True,
        }
    except Exception as e:
        print(f"Google Trends error: {e}")
        return get_fallback_trends(keyword)


def get_fallback_trends(keyword="product"):
    return {
        "keyword": keyword, "dates": [], "values": [],
        "trend_pct": 0, "trend_label": "➡️ Stable", "trend_color": "#f5a623",
        "current_interest": 50, "avg_interest": 50, "peak_date": "N/A",
        "top_queries": [], "rising_queries": [], "geo": "IN", "success": False,
    }