import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from scraper import get_listing_data, get_competitors, get_reviews_bulk, estimate_monthly_revenue, extract_asin
from analyzer import analyze_reviews, analyze_market, generate_scorecard, generate_creative_brief, chat_with_data
from trends import get_trend_data
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Amazon Market Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── STYLES ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,400&display=swap');
* { font-family: 'DM Sans', sans-serif; }
h1,h2,h3 { font-family: 'Syne', sans-serif !important; }
.stApp { background: #0a0a0f; color: #e8e8f0; }

/* HEADER */
.main-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border: 1px solid #e94560; border-radius: 20px;
    padding: 3rem 2rem; text-align: center; margin-bottom: 2rem;
    position: relative; overflow: hidden;
}
.main-header::before {
    content: ''; position: absolute; top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle, rgba(233,69,96,0.1) 0%, transparent 60%);
    animation: pulse 4s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{transform:scale(1);opacity:.5} 50%{transform:scale(1.1);opacity:1} }
.main-header h1 {
    font-size: 3rem !important; font-weight: 800 !important;
    background: linear-gradient(135deg, #e94560, #f5a623, #e94560);
    background-size: 200%; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    animation: shimmer 3s linear infinite; margin: 0 !important;
}
@keyframes shimmer { 0%{background-position:0%} 100%{background-position:200%} }
.main-header p { color: #8888aa; font-size: 1.1rem; margin-top: 0.5rem; }

/* CARDS */
.metric-card {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #2a2a4a; border-radius: 16px; padding: 1.5rem; text-align: center;
}
.metric-card .value { font-family: 'Syne', sans-serif; font-size: 2rem; font-weight: 800; color: #e94560; }
.metric-card .label { color: #8888aa; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.3rem; }

.insight-card {
    background: #13131f; border: 1px solid #2a2a4a;
    border-left: 4px solid #e94560; border-radius: 12px;
    padding: 1.2rem 1.5rem; margin-bottom: 1rem;
}
.insight-card.green { border-left-color: #00d4aa; }
.insight-card.orange { border-left-color: #f5a623; }

.section-title {
    font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 700;
    color: #e8e8f0; margin-bottom: 1.2rem; padding-bottom: 0.5rem;
    border-bottom: 2px solid #e94560; display: inline-block;
}

/* BUTTONS */
.stButton > button {
    background: linear-gradient(135deg, #e94560, #c73652) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    padding: 0.8rem 2rem !important; font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important; font-size: 1rem !important; letter-spacing: 1px !important;
    width: 100% !important; transition: all 0.3s !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 25px rgba(233,69,96,0.4) !important; }

/* INPUTS */
.stTextInput > div > div > input {
    background: #13131f !important; border: 2px solid #2a2a4a !important;
    border-radius: 12px !important; color: #e8e8f0 !important;
    font-size: 1rem !important; padding: 0.8rem 1rem !important;
}
.stTextInput > div > div > input:focus { border-color: #e94560 !important; }
.stProgress > div > div > div { background: linear-gradient(90deg, #e94560, #f5a623) !important; }

/* SELECT BOX */
.stSelectbox > div > div {
    background: #13131f !important; border: 2px solid #2a2a4a !important;
    border-radius: 12px !important; color: #e8e8f0 !important;
}

/* GAP BOX */
.gap-box {
    background: linear-gradient(135deg, #1a1a2e, #0f3460); border: 2px solid #e94560;
    border-radius: 16px; padding: 2rem; text-align: center; margin: 1rem 0;
}
.gap-box h3 { color: #e94560; font-family: 'Syne', sans-serif; font-size: 1.3rem; }
.gap-box p { color: #e8e8f0; font-size: 1rem; margin: 0; }

/* REVIEW SECTION */
.review-banner {
    background: linear-gradient(135deg, #0a0f1e, #0d1530, #0a0f20);
    border: 2px solid #7c4dff; border-radius: 20px;
    padding: 2rem; margin: 2rem 0 1.5rem 0;
}
.review-banner h2 { font-family:'Syne',sans-serif !important; font-size:1.8rem !important; font-weight:800 !important; color:#a78bfa !important; margin:0 0 0.3rem 0 !important; }
.review-banner p { color:#8888aa; font-size:0.95rem; margin:0; }
.review-stat { background:#0d1030; border:1px solid #7c4dff33; border-radius:14px; padding:1.2rem 1.5rem; margin-bottom:1rem; }
.review-stat .label { color:#a78bfa; font-size:0.75rem; text-transform:uppercase; letter-spacing:1.5px; font-weight:600; margin-bottom:0.4rem; }
.review-stat .value { color:#e8e8f0; font-size:0.95rem; font-weight:500; }
.complaint-pill { display:inline-block; background:#1a0a0a; border:1px solid #e9456033; border-radius:100px; padding:0.3rem 0.9rem; margin:0.2rem; color:#e94560; font-size:0.82rem; }
.praise-pill { display:inline-block; background:#0a1a0a; border:1px solid #00d4aa33; border-radius:100px; padding:0.3rem 0.9rem; margin:0.2rem; color:#00d4aa; font-size:0.82rem; }
.weakness-pill { display:inline-block; background:#1a1a0a; border:1px solid #f5a62333; border-radius:100px; padding:0.3rem 0.9rem; margin:0.2rem; color:#f5a623; font-size:0.82rem; }

/* TRENDS */
.trends-banner {
    background: linear-gradient(135deg, #0a1a0f, #0d2a15, #0a1f10);
    border: 2px solid #00d4aa; border-radius: 20px;
    padding: 2rem; margin: 2rem 0 1.5rem 0;
}
.trends-banner h2 { font-family:'Syne',sans-serif !important; font-size:1.8rem !important; font-weight:800 !important; color:#00d4aa !important; margin:0 0 0.3rem 0 !important; }
.trends-banner p { color:#8888aa; font-size:0.95rem; margin:0; }
.trend-stat { background:#0d2a15; border:1px solid #00d4aa33; border-radius:14px; padding:1.2rem 1.5rem; margin-bottom:1rem; }
.trend-stat .label { color:#00d4aa; font-size:0.75rem; text-transform:uppercase; letter-spacing:1.5px; font-weight:600; margin-bottom:0.4rem; }
.trend-stat .value { color:#e8e8f0; font-size:1rem; font-weight:500; }
.query-pill { display:inline-block; background:#0d2a15; border:1px solid #00d4aa33; border-radius:100px; padding:0.3rem 0.9rem; margin:0.2rem; color:#00d4aa; font-size:0.82rem; }
.rising-pill { display:inline-block; background:#1a1a0a; border:1px solid #f5a62333; border-radius:100px; padding:0.3rem 0.9rem; margin:0.2rem; color:#f5a623; font-size:0.82rem; }

/* CREATIVE BRIEF */
.brief-banner {
    background: linear-gradient(135deg, #0f0a1e, #1a0a2e, #0a1020);
    border: 2px solid #7c4dff; border-radius: 20px;
    padding: 2.5rem 2rem; margin: 2rem 0 1.5rem 0;
}
.brief-banner h2 { font-family:'Syne',sans-serif !important; font-size:1.8rem !important; font-weight:800 !important; color:#a78bfa !important; margin:0 0 0.3rem 0 !important; }
.brief-meta-card { background:#0f0a1e; border:1px solid #7c4dff44; border-radius:14px; padding:1.2rem 1.5rem; margin-bottom:1rem; }
.brief-meta-card .label { color:#7c4dff; font-size:0.75rem; text-transform:uppercase; letter-spacing:1.5px; font-weight:600; margin-bottom:0.4rem; }
.brief-meta-card .value { color:#e8e8f0; font-size:1rem; font-weight:500; line-height:1.5; }
.image-slot-card { background:#0f0a1e; border:1px solid #2a2a4a; border-radius:14px; padding:1.3rem 1.5rem; margin-bottom:1rem; }
.slot-number { display:inline-block; background:linear-gradient(135deg,#7c4dff,#e94560); color:white; font-family:'Syne',sans-serif; font-weight:800; font-size:0.75rem; padding:0.2rem 0.6rem; border-radius:6px; margin-bottom:0.5rem; }
.slot-role { font-family:'Syne',sans-serif; font-weight:700; color:#a78bfa; font-size:1rem; margin-bottom:0.4rem; }
.slot-what { color:#e8e8f0; font-size:0.9rem; margin-bottom:0.4rem; }
.slot-why { color:#8888aa; font-size:0.82rem; font-style:italic; margin-bottom:0.6rem; }
.pixii-prompt-box { background:#1a1a2e; border:1px dashed #7c4dff66; border-radius:8px; padding:0.6rem 0.8rem; font-size:0.82rem; color:#a78bfa; }
.pixii-prompt-label { font-size:0.7rem; color:#7c4dff; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.3rem; font-weight:600; }
.headline-pill { display:inline-block; background:linear-gradient(135deg,#1a0a2e,#0f0a1e); border:1px solid #7c4dff44; border-radius:100px; padding:0.5rem 1.2rem; margin:0.3rem; color:#e8e8f0; font-size:0.9rem; }
.copy-angle-card { background:#0f0a1e; border:1px solid #7c4dff33; border-radius:12px; padding:1rem 1.3rem; margin-bottom:0.7rem; }
.copy-angle-card .angle-name { color:#7c4dff; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; font-weight:600; }
.copy-angle-card .one-liner { color:#e8e8f0; font-size:1rem; font-weight:500; margin-top:0.3rem; }
.mistake-box { background:linear-gradient(135deg,#1a0a0a,#0f0505); border:2px solid #e9456066; border-radius:14px; padding:1.3rem 1.5rem; margin-top:1rem; }
.mistake-box .label { color:#e94560; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; font-weight:600; margin-bottom:0.4rem; }
.mistake-box .value { color:#e8e8f0; font-size:0.95rem; }

/* AI CHAT */
.chat-banner {
    background: linear-gradient(135deg, #0a0f1e, #0d1530);
    border: 2px solid #e94560; border-radius: 20px;
    padding: 2rem; margin: 2rem 0 1.5rem 0;
}
.chat-banner h2 { font-family:'Syne',sans-serif !important; font-size:1.8rem !important; font-weight:800 !important; color:#e94560 !important; margin:0 0 0.3rem 0 !important; }
.chat-banner p { color:#8888aa; font-size:0.95rem; margin:0; }
.chat-msg-user { background:#1a1a2e; border:1px solid #2a2a4a; border-radius:12px 12px 4px 12px; padding:0.8rem 1.2rem; margin:0.5rem 0; max-width:80%; margin-left:auto; color:#e8e8f0; }
.chat-msg-ai { background:#13131f; border:1px solid #e9456033; border-left:3px solid #e94560; border-radius:12px 12px 12px 4px; padding:0.8rem 1.2rem; margin:0.5rem 0; max-width:85%; color:#e8e8f0; }
</style>
""", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🔬 Amazon Market Intelligence</h1>
    <p>Drop any Amazon listing. Get competitive intelligence + trend data + a Pixii-ready creative brief.</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    amazon_url = st.text_input(
        "Amazon Product URL",
        placeholder="Paste Amazon product URL here... e.g. https://www.amazon.in/dp/B0716GWQ7R",
        label_visibility="collapsed"
    )
    rc1, rc2 = st.columns(2)
    with rc1:
        review_pages = st.selectbox(
            "Reviews to scrape per product",
            options=[2, 5, 10],
            index=1,
            help="More pages = deeper analysis but slower. 5 pages ≈ 50 reviews per product."
        )
    with rc2:
        num_competitors = st.selectbox(
            "Competitors to analyze",
            options=[5, 7, 9],
            index=2,
        )
    analyze_btn = st.button("🚀 ANALYZE MARKET", use_container_width=True)


# ── CHART HELPERS ─────────────────────────────────────────────────────────────
def make_gauge(value, title):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        title={"text": title, "font": {"color": "#8888aa", "size": 14}},
        number={"font": {"color": "#e94560", "size": 36, "family": "Syne"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#2a2a4a"},
            "bar": {"color": "#e94560"}, "bgcolor": "#13131f", "bordercolor": "#2a2a4a",
            "steps": [{"range": [0, 40], "color": "#1a0a0a"}, {"range": [40, 70], "color": "#1a1a0a"}, {"range": [70, 100], "color": "#0a1a0a"}],
            "threshold": {"line": {"color": "#f5a623", "width": 3}, "thickness": 0.8, "value": value},
        }
    ))
    fig.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font={"color": "#e8e8f0"}, margin=dict(t=40, b=10, l=20, r=20))
    return fig

def make_radar(scores):
    categories = list(scores.keys())
    values = list(scores.values())
    categories_display = [c.replace("_", " ").title() for c in categories]
    fig = go.Figure(go.Scatterpolar(
        r=values + [values[0]], theta=categories_display + [categories_display[0]],
        fill="toself", fillcolor="rgba(233,69,96,0.2)", line=dict(color="#e94560", width=2),
    ))
    fig.update_layout(
        polar=dict(bgcolor="#13131f",
                   radialaxis=dict(visible=True, range=[0, 100], gridcolor="#2a2a4a", tickcolor="#8888aa"),
                   angularaxis=dict(gridcolor="#2a2a4a", tickcolor="#8888aa")),
        paper_bgcolor="rgba(0,0,0,0)", font={"color": "#e8e8f0", "family": "DM Sans"},
        height=350, showlegend=False, margin=dict(t=20, b=20, l=40, r=40),
    )
    return fig

def make_revenue_bar(your_product, competitors):
    all_products = [your_product] + competitors
    names = [p.get("title", "Unknown")[:35] + "..." for p in all_products]
    revenues = [p.get("monthly_revenue", 0) for p in all_products]
    colors = ["#e94560"] + ["#2a2a4a"] * len(competitors)
    fig = go.Figure(go.Bar(x=revenues, y=names, orientation="h", marker_color=colors, marker_line_width=0))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e8e8f0", "family": "DM Sans"},
        xaxis=dict(gridcolor="#2a2a4a", title="Est. Monthly Revenue", color="#8888aa"),
        yaxis=dict(gridcolor="#2a2a4a", color="#8888aa"),
        height=420, margin=dict(t=10, b=40, l=10, r=20),
    )
    return fig

def make_criteria_chart(criteria):
    labels = [c["criterion"] for c in criteria]
    values = [c["percentage"] for c in criteria]
    colors = ["#e94560", "#f5a623", "#00d4aa", "#7c4dff", "#00b4d8"]
    fig = go.Figure(go.Bar(
        x=labels, y=values, marker_color=colors[:len(labels)], marker_line_width=0,
        text=[f"{v}%" for v in values], textposition="outside", textfont={"color": "#e8e8f0"},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e8e8f0", "family": "DM Sans"},
        xaxis=dict(gridcolor="#2a2a4a", color="#8888aa"),
        yaxis=dict(gridcolor="#2a2a4a", color="#8888aa", range=[0, 115]),
        height=300, margin=dict(t=30, b=10, l=10, r=10), showlegend=False,
    )
    return fig

def make_trend_line(dates, values, keyword):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=values, mode="lines+markers",
        line=dict(color="#00d4aa", width=2.5),
        marker=dict(color="#00d4aa", size=5),
        fill="tozeroy", fillcolor="rgba(0,212,170,0.1)",
        name=keyword,
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e8e8f0", "family": "DM Sans"},
        xaxis=dict(gridcolor="#2a2a4a", color="#8888aa", tickangle=45),
        yaxis=dict(gridcolor="#2a2a4a", color="#8888aa", title="Search Interest (0-100)"),
        height=300, margin=dict(t=20, b=60, l=10, r=10), showlegend=False,
    )
    return fig

def make_sentiment_donut(breakdown):
    labels = ["5★", "4★", "3★", "1-2★"]
    values = [
        breakdown.get("5_star_pct", 60),
        breakdown.get("4_star_pct", 20),
        breakdown.get("3_star_pct", 10),
        breakdown.get("1_2_star_pct", 10),
    ]
    colors = ["#00d4aa", "#7c4dff", "#f5a623", "#e94560"]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.65,
        marker=dict(colors=colors, line=dict(color="#0a0a0f", width=2)),
        textfont=dict(color="#e8e8f0"),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font={"color": "#e8e8f0", "family": "DM Sans"},
        height=250, showlegend=True, margin=dict(t=20, b=20, l=10, r=10),
        legend=dict(font=dict(color="#8888aa")),
    )
    return fig


# ── MAIN FLOW ─────────────────────────────────────────────────────────────────
if analyze_btn and amazon_url:
    st.markdown("---")
    progress_bar = st.progress(0)
    status = st.empty()

    try:
        # 1. Scrape your listing
        status.markdown("**🔍 Scraping your product listing...**")
        progress_bar.progress(5)
        your_product = get_listing_data(amazon_url)

        if not your_product:
            progress_bar.empty(); status.empty()
            st.error("❌ Failed to scrape the listing. Check your ScraperAPI key or try again.")
            st.stop()

        is_india = "amazon.in" in amazon_url
        currency = "₹" if is_india else "$"
        geo = "IN" if is_india else "US"
        your_product["monthly_revenue"] = estimate_monthly_revenue(your_product["bsr"], your_product["price"])
        your_asin = your_product.get("asin") or extract_asin(amazon_url)

        # 2. Scrape your reviews
        status.markdown(f"**⭐ Scraping your product reviews ({review_pages} pages)...**")
        progress_bar.progress(12)
        your_reviews = get_reviews_bulk(amazon_url, your_asin, max_pages=review_pages)
        status.markdown(f"**⭐ Got {len(your_reviews)} reviews for your product.**")

        # 3. Find competitors
        status.markdown("**🕵️ Finding top competitors...**")
        progress_bar.progress(18)
        competitor_urls = get_competitors(amazon_url, num_competitors=num_competitors)

        if not competitor_urls:
            progress_bar.empty(); status.empty()
            st.error("❌ Could not find competitor listings. Try again.")
            st.stop()

        # 4. Scrape competitor listings + reviews
        competitors_data = []
        competitor_reviews_map = {}
        total_comps = len(competitor_urls)

        for i, comp_url in enumerate(competitor_urls):
            pct = 18 + int((i + 1) / total_comps * 35)
            status.markdown(f"**📦 Scraping competitor {i+1}/{total_comps} + reviews...**")
            progress_bar.progress(pct)
            comp_data = get_listing_data(comp_url)
            if comp_data:
                comp_data["monthly_revenue"] = estimate_monthly_revenue(comp_data["bsr"], comp_data["price"])
                competitors_data.append(comp_data)
                # Scrape reviews for this competitor (2 pages each to keep it fast)
                comp_asin = comp_data.get("asin") or extract_asin(comp_url)
                comp_reviews = get_reviews_bulk(comp_url, comp_asin, max_pages=2)
                if comp_reviews:
                    competitor_reviews_map[comp_data.get("title", f"Competitor {i+1}")] = comp_reviews

        if not competitors_data:
            progress_bar.empty(); status.empty()
            st.error("❌ Could not scrape any competitor data. Please try again.")
            st.stop()

        total_reviews_scraped = len(your_reviews) + sum(len(v) for v in competitor_reviews_map.values())

        # 5. AI review analysis
        status.markdown(f"**🧠 Analyzing {total_reviews_scraped} real customer reviews with Gemini AI...**")
        progress_bar.progress(57)
        review_analysis = analyze_reviews(your_reviews, competitor_reviews_map)

        # 6. Google Trends
        status.markdown("**📈 Fetching Google Trends data...**")
        progress_bar.progress(65)
        trend_data = get_trend_data(your_product.get("title", ""), geo=geo)

        # 7. Market analysis
        status.markdown("**🔮 Gemini AI analyzing market landscape...**")
        progress_bar.progress(73)
        insights = analyze_market(your_product.get("title", ""), your_product, competitors_data, review_analysis)

        # 8. Scorecard
        status.markdown("**📊 Generating competitive scorecard...**")
        progress_bar.progress(83)
        scorecard = generate_scorecard(your_product, competitors_data)

        # 9. Creative brief
        status.markdown("**🎨 Building Pixii creative brief...**")
        progress_bar.progress(93)
        creative_brief = generate_creative_brief(your_product.get("title", ""), insights, your_product, review_analysis)

        progress_bar.progress(100)
        status.empty()
        progress_bar.empty()

        # Save context for AI chat
        chat_context = {
            "title": your_product.get("title", ""),
            "currency": currency,
            "price": your_product.get("price", 0),
            "rating": your_product.get("rating", 0),
            "review_count": your_product.get("review_count", 0),
            "bsr": your_product.get("bsr", "N/A"),
            "monthly_revenue": your_product.get("monthly_revenue", 0),
            "total_market": your_product.get("monthly_revenue", 0) + sum(c.get("monthly_revenue", 0) for c in competitors_data),
            "num_competitors": len(competitors_data),
            "market_gap": insights.get("market_gap", ""),
            "winning_angle": insights.get("winning_angle", ""),
            "customer_profile": insights.get("customer_profile", ""),
            "top_complaints": review_analysis.get("top_complaints", []),
            "top_praises": review_analysis.get("top_praises", []),
            "competitor_weaknesses": review_analysis.get("competitor_weaknesses", []),
            "verdict": scorecard.get("verdict", ""),
            "trend_label": trend_data.get("trend_label", ""),
            "trend_pct": trend_data.get("trend_pct", 0),
            "total_reviews_scraped": total_reviews_scraped,
        }
        st.session_state["chat_context"] = chat_context
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        # ── PRODUCT HEADER ──────────────────────────────────────────────────
        st.markdown(f"""
        <div class="insight-card" style="border-left-color: #f5a623; margin-bottom: 2rem;">
            <div style="font-family:Syne; font-size:1.2rem; font-weight:700; color:#f5a623;">🎯 Analyzing</div>
            <div style="font-size:1rem; margin-top:0.3rem;">{your_product.get('title','Your Product')}</div>
            <div style="color:#8888aa; font-size:0.85rem; margin-top:0.3rem;">Brand: {your_product.get('brand','Unknown')} &nbsp;|&nbsp; ASIN: {your_product.get('asin','N/A')} &nbsp;|&nbsp; Reviews scraped: <span style="color:#00d4aa;">{total_reviews_scraped}</span></div>
        </div>
        """, unsafe_allow_html=True)

        # ── MARKET SNAPSHOT ─────────────────────────────────────────────────
        st.markdown('<div class="section-title">📈 Market Snapshot</div>', unsafe_allow_html=True)
        total_market = your_product.get("monthly_revenue", 0) + sum(c.get("monthly_revenue", 0) for c in competitors_data)
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1: st.markdown(f"""<div class="metric-card"><div class="value">{currency}{your_product.get('monthly_revenue',0):,.0f}</div><div class="label">Your Est. Revenue/mo</div></div>""", unsafe_allow_html=True)
        with m2: st.markdown(f"""<div class="metric-card"><div class="value">{currency}{total_market:,.0f}</div><div class="label">Total Market/mo</div></div>""", unsafe_allow_html=True)
        with m3: st.markdown(f"""<div class="metric-card"><div class="value">{your_product.get('rating',0)}★</div><div class="label">Your Rating</div></div>""", unsafe_allow_html=True)
        with m4: st.markdown(f"""<div class="metric-card"><div class="value">{your_product.get('review_count',0):,}</div><div class="label">Your Reviews</div></div>""", unsafe_allow_html=True)
        with m5: st.markdown(f"""<div class="metric-card"><div class="value">#{your_product.get('bsr','N/A')}</div><div class="label">Best Seller Rank</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">💰 Revenue Battlefield</div>', unsafe_allow_html=True)
        st.plotly_chart(make_revenue_bar(your_product, competitors_data), use_container_width=True)

        # ── REVIEW INTELLIGENCE (NEW) ────────────────────────────────────────
        st.markdown(f"""
        <div class="review-banner">
            <h2>⭐ Review Intelligence</h2>
            <p>Extracted from <strong style="color:#a78bfa;">{total_reviews_scraped} real scraped reviews</strong> — your product + {len(competitors_data)} competitors.</p>
        </div>
        """, unsafe_allow_html=True)

        rv1, rv2 = st.columns([1, 2])
        with rv1:
            st.markdown("**📊 Sentiment Breakdown**")
            st.plotly_chart(make_sentiment_donut(review_analysis.get("sentiment_breakdown", {})), use_container_width=True)
            st.markdown(f"""
            <div class="review-stat">
                <div class="label">📝 Key Insight</div>
                <div class="value">{review_analysis.get('review_insights_summary', '')}</div>
            </div>
            """, unsafe_allow_html=True)

        with rv2:
            rvc1, rvc2, rvc3 = st.columns(3)
            with rvc1:
                st.markdown("**✅ What Customers Love**")
                pills = "".join([f'<span class="praise-pill">👍 {p}</span>' for p in review_analysis.get("top_praises", [])])
                st.markdown(f'<div style="margin-top:0.5rem;">{pills}</div>', unsafe_allow_html=True)
            with rvc2:
                st.markdown("**❌ Top Complaints**")
                pills = "".join([f'<span class="complaint-pill">⚠️ {c}</span>' for c in review_analysis.get("top_complaints", [])])
                st.markdown(f'<div style="margin-top:0.5rem;">{pills}</div>', unsafe_allow_html=True)
            with rvc3:
                st.markdown("**🎯 Competitor Gaps**")
                pills = "".join([f'<span class="weakness-pill">💡 {w}</span>' for w in review_analysis.get("competitor_weaknesses", [])])
                st.markdown(f'<div style="margin-top:0.5rem;">{pills}</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            unmet = review_analysis.get("unmet_needs", [])
            if unmet:
                st.markdown("**🕳️ Unmet Needs (your opportunity)**")
                for need in unmet:
                    st.markdown(f"""<div class="insight-card green">🚀 {need}</div>""", unsafe_allow_html=True)

        # ── COMPETITIVE SCORECARD ────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">🏆 Competitive Scorecard</div>', unsafe_allow_html=True)
        sc1, sc2 = st.columns([1, 2])
        with sc1:
            overall = scorecard.get("overall_score", 65)
            color = "#00d4aa" if overall >= 70 else "#f5a623" if overall >= 50 else "#e94560"
            st.plotly_chart(make_gauge(overall, "Overall Score"), use_container_width=True)
            st.markdown(f"""
            <div style="text-align:center; color:{color}; font-family:Syne; font-size:1rem; font-weight:700;">Rank #{scorecard.get('rank_in_market','?')} in Market</div>
            <div style="text-align:center; color:#8888aa; font-size:0.85rem; margin-top:0.5rem;">Threat Level: <span style="color:#f5a623;">{scorecard.get('threat_level','Medium')}</span></div>
            """, unsafe_allow_html=True)
        with sc2:
            st.plotly_chart(make_radar(scorecard.get("scores", {})), use_container_width=True)

        st.markdown(f"""<div class="gap-box"><h3>⚖️ Verdict</h3><p>{scorecard.get('verdict','')}</p></div>""", unsafe_allow_html=True)

        sw1, sw2, sw3 = st.columns(3)
        with sw1:
            st.markdown("**💪 Strengths**")
            for s in scorecard.get("strengths", []): st.markdown(f"""<div class="insight-card green">✅ {s}</div>""", unsafe_allow_html=True)
        with sw2:
            st.markdown("**⚠️ Weaknesses**")
            for w in scorecard.get("weaknesses", []): st.markdown(f"""<div class="insight-card">❌ {w}</div>""", unsafe_allow_html=True)
        with sw3:
            st.markdown("**⚡ Quick Wins**")
            for q in scorecard.get("quick_wins", []): st.markdown(f"""<div class="insight-card orange">🚀 {q}</div>""", unsafe_allow_html=True)

        # ── PURCHASE CRITERIA ────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎯 Why Customers Buy</div>', unsafe_allow_html=True)
        criteria = insights.get("purchase_criteria", [])
        if criteria:
            st.plotly_chart(make_criteria_chart(criteria), use_container_width=True)
            for c in criteria:
                imp_color = "#e94560" if c["importance"] == "High" else "#f5a623" if c["importance"] == "Medium" else "#8888aa"
                evidence = c.get("evidence", "")
                st.markdown(f"""
                <div class="insight-card" style="border-left-color:{imp_color};">
                    <strong>{c['criterion']}</strong>
                    <span style="color:{imp_color}; font-size:0.8rem; margin-left:0.5rem;">{c['importance']} Impact · {c['percentage']}%</span>
                    <div style="color:#8888aa; font-size:0.9rem; margin-top:0.3rem;">{c['description']}</div>
                    {f'<div style="color:#7c4dff; font-size:0.82rem; margin-top:0.3rem; font-style:italic;">📝 Evidence: {evidence}</div>' if evidence else ''}
                </div>
                """, unsafe_allow_html=True)

        # ── INTELLIGENCE REPORT ──────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">🔮 Intelligence Report</div>', unsafe_allow_html=True)
        ig1, ig2 = st.columns(2)
        with ig1:
            st.markdown(f"""<div class="gap-box"><h3>🕳️ Market Gap</h3><p>{insights.get('market_gap','')}</p></div>""", unsafe_allow_html=True)
        with ig2:
            st.markdown(f"""<div class="gap-box" style="border-color:#00d4aa;"><h3 style="color:#00d4aa;">🏹 Winning Angle</h3><p>{insights.get('winning_angle','')}</p></div>""", unsafe_allow_html=True)

        cp1, cp2, cp3, cp4 = st.columns(4)
        with cp1: st.markdown(f"""<div class="metric-card"><div class="value">{insights.get('sentiment_score',0)}</div><div class="label">Sentiment Score</div></div>""", unsafe_allow_html=True)
        with cp2: st.markdown(f"""<div class="metric-card"><div class="value">{insights.get('price_sensitivity','Med')}</div><div class="label">Price Sensitivity</div></div>""", unsafe_allow_html=True)
        with cp3: st.markdown(f"""<div class="metric-card"><div class="value">{insights.get('repeat_purchase_rate','Med')}</div><div class="label">Repeat Purchase</div></div>""", unsafe_allow_html=True)
        with cp4: st.markdown(f"""<div class="metric-card"><div class="value">{total_reviews_scraped}</div><div class="label">Reviews Analyzed</div></div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="insight-card orange" style="margin-top:1rem;"><strong>👤 Customer Profile</strong><div style="color:#e8e8f0;margin-top:0.3rem;">{insights.get('customer_profile','')}</div></div>""", unsafe_allow_html=True)
        st.markdown(f"""<div class="insight-card green" style="margin-top:0.5rem;"><strong>📋 Market Summary</strong><div style="color:#e8e8f0;margin-top:0.3rem;">{insights.get('market_summary','')}</div></div>""", unsafe_allow_html=True)

        # ── COMPETITOR TABLE ─────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">🕵️ Competitor Intelligence</div>', unsafe_allow_html=True)
        if competitors_data:
            df = pd.DataFrame([{
                "Product": c.get("title","")[:45]+"...",
                "Brand": c.get("brand",""),
                f"Price ({currency})": c.get("price",0),
                "Rating": c.get("rating",0),
                "Reviews": f"{c.get('review_count',0):,}",
                "BSR": f"#{c.get('bsr','N/A')}",
                "Est. Revenue/mo": f"{currency}{c.get('monthly_revenue',0):,.0f}",
            } for c in competitors_data])
            st.dataframe(df, use_container_width=True, hide_index=True)

        # ── GOOGLE TRENDS ────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="trends-banner">
            <h2>📊 Google Trends Intelligence</h2>
            <p>Is this market growing or dying? Real search demand for <strong style="color:#00d4aa;">"{trend_data.get('keyword','')}"</strong> — last 12 months in {geo}.</p>
        </div>
        """, unsafe_allow_html=True)

        if trend_data.get("success") and trend_data.get("values"):
            st.plotly_chart(make_trend_line(trend_data["dates"], trend_data["values"], trend_data["keyword"]), use_container_width=True)
            t1, t2, t3, t4 = st.columns(4)
            with t1:
                st.markdown(f"""<div class="trend-stat"><div class="label">Trend Direction</div><div class="value" style="color:{trend_data['trend_color']}; font-size:1.1rem; font-weight:700;">{trend_data['trend_label']}</div></div>""", unsafe_allow_html=True)
            with t2:
                pct = trend_data['trend_pct']
                pct_color = "#00d4aa" if pct >= 0 else "#e94560"
                st.markdown(f"""<div class="trend-stat"><div class="label">12-Month Change</div><div class="value" style="color:{pct_color}; font-size:1.3rem; font-weight:700;">{"+" if pct >= 0 else ""}{pct}%</div></div>""", unsafe_allow_html=True)
            with t3:
                st.markdown(f"""<div class="trend-stat"><div class="label">Current Interest</div><div class="value">{trend_data['current_interest']}<span style="color:#8888aa;font-size:0.8rem;">/100</span></div></div>""", unsafe_allow_html=True)
            with t4:
                st.markdown(f"""<div class="trend-stat"><div class="label">Avg Interest</div><div class="value">{trend_data['avg_interest']}<span style="color:#8888aa;font-size:0.8rem;">/100</span></div></div>""", unsafe_allow_html=True)

            if trend_data.get("top_queries") or trend_data.get("rising_queries"):
                tq1, tq2 = st.columns(2)
                with tq1:
                    if trend_data.get("top_queries"):
                        st.markdown("**🔍 Top Search Queries**")
                        pills = "".join([f'<span class="query-pill">{q}</span>' for q in trend_data["top_queries"]])
                        st.markdown(f'<div style="margin-top:0.5rem;">{pills}</div>', unsafe_allow_html=True)
                with tq2:
                    if trend_data.get("rising_queries"):
                        st.markdown("**🚀 Rising Searches**")
                        pills = "".join([f'<span class="rising-pill">↑ {q}</span>' for q in trend_data["rising_queries"]])
                        st.markdown(f'<div style="margin-top:0.5rem;">{pills}</div>', unsafe_allow_html=True)
        else:
            st.markdown("""<div class="insight-card orange">⚠️ Google Trends data unavailable for this keyword. All other analysis is still accurate.</div>""", unsafe_allow_html=True)

        # ── CREATIVE BRIEF ───────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="brief-banner">
            <h2>🎨 Pixii Creative Brief</h2>
            <p>Your listing's visual strategy — built from real review data + market intelligence. Tell Pixii exactly what to make and why it converts.</p>
        </div>
        """, unsafe_allow_html=True)

        ba1, ba2, ba3 = st.columns(3)
        with ba1: st.markdown(f"""<div class="brief-meta-card"><div class="label">🎯 Hero Angle</div><div class="value">{creative_brief.get('hero_angle','')}</div></div>""", unsafe_allow_html=True)
        with ba2: st.markdown(f"""<div class="brief-meta-card"><div class="label">💜 Target Emotion</div><div class="value">{creative_brief.get('target_emotion','')}</div></div>""", unsafe_allow_html=True)
        with ba3: st.markdown(f"""<div class="brief-meta-card"><div class="label">🖼️ Visual Tone</div><div class="value">{creative_brief.get('tone','')}</div></div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="brief-meta-card" style="border-color:#7c4dff88; margin-bottom:1.5rem;"><div class="label">📋 Creative Direction</div><div class="value">{creative_brief.get('brief_summary','')}</div></div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-title" style="color:#a78bfa; border-color:#7c4dff;">🖼️ Your 7-Image Stack</div>', unsafe_allow_html=True)
        image_stack = creative_brief.get("image_stack", [])
        img_col1, img_col2 = st.columns(2)
        with img_col1:
            for slot in image_stack[:4]:
                st.markdown(f"""
                <div class="image-slot-card">
                    <div><span class="slot-number">IMAGE {slot.get('slot','?')}</span></div>
                    <div class="slot-role">{slot.get('role','')}</div>
                    <div class="slot-what">📸 {slot.get('what_to_show','')}</div>
                    <div class="slot-why">💡 {slot.get('why_it_converts','')}</div>
                    <div class="pixii-prompt-label">Pixii / AI Prompt</div>
                    <div class="pixii-prompt-box">{slot.get('pixii_prompt','')}</div>
                </div>""", unsafe_allow_html=True)
        with img_col2:
            for slot in image_stack[4:]:
                st.markdown(f"""
                <div class="image-slot-card">
                    <div><span class="slot-number">IMAGE {slot.get('slot','?')}</span></div>
                    <div class="slot-role">{slot.get('role','')}</div>
                    <div class="slot-what">📸 {slot.get('what_to_show','')}</div>
                    <div class="slot-why">💡 {slot.get('why_it_converts','')}</div>
                    <div class="pixii-prompt-label">Pixii / AI Prompt</div>
                    <div class="pixii-prompt-box">{slot.get('pixii_prompt','')}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        hl_col, ca_col = st.columns(2)
        with hl_col:
            st.markdown('<div class="section-title" style="color:#a78bfa; border-color:#7c4dff;">✍️ Headline Options</div>', unsafe_allow_html=True)
            for h in creative_brief.get("headline_options", []):
                st.markdown(f'<div class="headline-pill">"{h}"</div>', unsafe_allow_html=True)
        with ca_col:
            st.markdown('<div class="section-title" style="color:#a78bfa; border-color:#7c4dff;">🗣️ Copy Angles</div>', unsafe_allow_html=True)
            for angle in creative_brief.get("copy_angles", []):
                st.markdown(f"""<div class="copy-angle-card"><div class="angle-name">{angle.get('angle','')}</div><div class="one-liner">"{angle.get('one_liner','')}"</div></div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="mistake-box">
            <div class="label">⚠️ Biggest Mistake to Avoid in This Category</div>
            <div class="value">{creative_brief.get('biggest_mistake_to_avoid','')}</div>
        </div>""", unsafe_allow_html=True)

        # ── AI CHAT ASSISTANT ────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="chat-banner">
            <h2>🤖 Ask the AI Analyst</h2>
            <p>Ask anything about this product, the market, or your strategy. Powered by Gemini with full analysis context.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**💡 Try asking:** *What's my biggest threat? How do I beat the top competitor? What should my A+ content focus on?*")

        # Display chat history
        for msg in st.session_state.get("chat_history", []):
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-msg-user">🙋 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-msg-ai">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

        chat_input = st.text_input("Ask anything about this market...", key="chat_input", label_visibility="collapsed", placeholder="e.g. How do I beat the #1 competitor?")
        send_btn = st.button("💬 Ask", use_container_width=False)

        if send_btn and chat_input and st.session_state.get("chat_context"):
            with st.spinner("Thinking..."):
                reply = chat_with_data(chat_input, st.session_state["chat_context"], st.session_state.get("chat_history", []))
            st.session_state["chat_history"].append({"role": "user", "content": chat_input})
            st.session_state["chat_history"].append({"role": "assistant", "content": reply})
            st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center; color:#2a2a4a; font-size:0.8rem;">
            Built with ❤️ using ScraperAPI + Google Trends + Gemini AI + Streamlit &nbsp;|&nbsp; Real review scraping • AI chat • Pixii creative briefs
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Something went wrong: {str(e)}")
        st.info("💡 Tip: Make sure SCRAPER_API_KEY and GEMINI_API_KEY are set in your .env file")

elif analyze_btn and not amazon_url:
    st.warning("⚠️ Please paste an Amazon product URL first!")

# ── PERSISTENT CHAT (after analysis) ─────────────────────────────────────────
elif not analyze_btn and st.session_state.get("chat_context"):
    st.markdown("---")
    st.markdown("""
    <div class="chat-banner">
        <h2>🤖 Ask the AI Analyst</h2>
        <p>Your previous analysis is still loaded. Keep asking questions!</p>
    </div>
    """, unsafe_allow_html=True)

    for msg in st.session_state.get("chat_history", []):
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-msg-user">🙋 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-msg-ai">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    chat_input2 = st.text_input("Ask anything...", key="chat_input2", placeholder="e.g. What's the best pricing strategy?")
    if st.button("💬 Ask", key="send2") and chat_input2:
        with st.spinner("Thinking..."):
            reply = chat_with_data(chat_input2, st.session_state["chat_context"], st.session_state.get("chat_history", []))
        st.session_state["chat_history"].append({"role": "user", "content": chat_input2})
        st.session_state["chat_history"].append({"role": "assistant", "content": reply})
        st.rerun()