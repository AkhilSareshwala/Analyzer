import google.generativeai as genai
import os
import json
import re

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def setup_gemini():
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-2.5-flash")


def _ask_gemini(prompt: str) -> dict | list | None:
    """Call Gemini and return parsed JSON."""
    try:
        model = setup_gemini()
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        return json.loads(text)
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


def analyze_reviews(your_reviews: list, competitor_reviews_map: dict) -> dict:
    """
    Use Gemini to deeply analyze scraped reviews and surface real purchase criteria.
    your_reviews: list of {title, body, rating}
    competitor_reviews_map: {product_title: [reviews]}
    """
    all_your_text = "\n".join(
        f"[{r['rating']}★] {r.get('title', '')}: {r['body'][:300]}"
        for r in your_reviews[:80]
    )

    comp_summaries = []
    for prod_title, reviews in list(competitor_reviews_map.items())[:3]:
        sample = "\n".join(f"[{r['rating']}★] {r['body'][:200]}" for r in reviews[:25])
        comp_summaries.append(f"=== {prod_title[:50]} ===\n{sample}")
    comp_text = "\n\n".join(comp_summaries)

    prompt = f"""You are an expert Amazon market analyst. Analyze these REAL customer reviews.

YOUR PRODUCT REVIEWS ({len(your_reviews)} total, showing sample):
{all_your_text or "No reviews yet — new listing."}

COMPETITOR REVIEWS (sample):
{comp_text or "No competitor reviews scraped."}

From this review data, extract deep insights. Return ONLY valid JSON (no markdown, no explanation):
{{
  "purchase_criteria": [
    {{"criterion": "string", "importance": "High/Medium/Low", "percentage": number, "description": "string", "evidence": "brief pattern from reviews"}},
    {{"criterion": "string", "importance": "High/Medium/Low", "percentage": number, "description": "string", "evidence": "brief pattern from reviews"}},
    {{"criterion": "string", "importance": "High/Medium/Low", "percentage": number, "description": "string", "evidence": "brief pattern from reviews"}},
    {{"criterion": "string", "importance": "High/Medium/Low", "percentage": number, "description": "string", "evidence": "brief pattern from reviews"}},
    {{"criterion": "string", "importance": "High/Medium/Low", "percentage": number, "description": "string", "evidence": "brief pattern from reviews"}}
  ],
  "top_complaints": ["string", "string", "string"],
  "top_praises": ["string", "string", "string"],
  "competitor_weaknesses": ["string", "string", "string"],
  "unmet_needs": ["string", "string"],
  "sentiment_breakdown": {{"5_star_pct": number, "4_star_pct": number, "3_star_pct": number, "1_2_star_pct": number}},
  "review_insights_summary": "2-3 sentences on what the reviews reveal"
}}"""

    result = _ask_gemini(prompt)
    return result or get_fallback_review_analysis()


def analyze_market(product_title, your_product, competitors_data, review_analysis=None):
    your_info = f"""
Title: {product_title}
Price: {your_product.get('price', 0)}
Rating: {your_product.get('rating', 0)}★ ({your_product.get('review_count', 0)} reviews)
BSR: #{your_product.get('bsr', 'N/A')}
Brand: {your_product.get('brand', 'Unknown')}
Est. Monthly Revenue: {your_product.get('monthly_revenue', 0):,.0f}
"""

    comp_summary = ""
    for c in competitors_data:
        comp_summary += f"- {c.get('title', 'Unknown')[:60]} | Price: {c.get('price', 0)} | {c.get('rating', 0)}★ | {c.get('review_count', 0)} reviews | BSR: #{c.get('bsr','N/A')} | Est. Revenue: {c.get('monthly_revenue', 0):,.0f}/mo\n"

    review_context = ""
    if review_analysis:
        review_context = f"""
REVIEW ANALYSIS (from real scraped reviews):
Top praises: {', '.join(review_analysis.get('top_praises', []))}
Top complaints: {', '.join(review_analysis.get('top_complaints', []))}
Competitor weaknesses: {', '.join(review_analysis.get('competitor_weaknesses', []))}
Unmet needs: {', '.join(review_analysis.get('unmet_needs', []))}
"""

    prompt = f"""You are an elite Amazon market research analyst.

YOUR PRODUCT:
{your_info}

COMPETITOR LANDSCAPE ({len(competitors_data)} competitors):
{comp_summary}
{review_context}

Return ONLY valid JSON (no markdown, no explanation):
{{
  "purchase_criteria": [
    {{"criterion": "string", "importance": "High/Medium/Low", "percentage": number, "description": "string"}},
    {{"criterion": "string", "importance": "High/Medium/Low", "percentage": number, "description": "string"}},
    {{"criterion": "string", "importance": "High/Medium/Low", "percentage": number, "description": "string"}},
    {{"criterion": "string", "importance": "High/Medium/Low", "percentage": number, "description": "string"}},
    {{"criterion": "string", "importance": "High/Medium/Low", "percentage": number, "description": "string"}}
  ],
  "market_gap": "string describing the biggest unmet need in this market",
  "winning_angle": "string describing what a seller should focus on to dominate",
  "sentiment_score": number between 0 and 100,
  "customer_profile": "string describing who the typical buyer is",
  "price_sensitivity": "High/Medium/Low",
  "repeat_purchase_rate": "High/Medium/Low",
  "market_summary": "2-3 sentence summary of the overall market opportunity"
}}"""

    result = _ask_gemini(prompt)
    return result or get_fallback_analysis()


def generate_scorecard(your_product, competitors):
    your_info = f"""
Product: {your_product.get('title', '')[:80]}
Price: {your_product.get('price', 0)}
Rating: {your_product.get('rating', 0)}★
Reviews: {your_product.get('review_count', 0)}
BSR: #{your_product.get('bsr', 'N/A')}
Est. Monthly Revenue: {your_product.get('monthly_revenue', 0):,.0f}
"""
    comp_info = ""
    for i, c in enumerate(competitors[:5]):
        comp_info += f"\nCompetitor {i+1}: {c.get('title', '')[:60]}\nPrice: {c.get('price', 0)} | Rating: {c.get('rating', 0)}★ | Reviews: {c.get('review_count', 0)} | Revenue: {c.get('monthly_revenue', 0):,.0f}/mo\n"

    prompt = f"""You are a competitive intelligence expert. Score this Amazon product vs competitors.

YOUR PRODUCT:
{your_info}

COMPETITORS:
{comp_info}

Return ONLY valid JSON (no markdown):
{{
  "overall_score": number 0-100,
  "rank_in_market": number,
  "scores": {{
    "price_competitiveness": number 0-100,
    "social_proof": number 0-100,
    "market_position": number 0-100,
    "revenue_performance": number 0-100,
    "growth_potential": number 0-100
  }},
  "strengths": ["string", "string", "string"],
  "weaknesses": ["string", "string", "string"],
  "quick_wins": ["string", "string", "string"],
  "threat_level": "Low/Medium/High",
  "verdict": "one sentence verdict on this product's competitive position"
}}"""

    result = _ask_gemini(prompt)
    return result or get_fallback_scorecard()


def generate_creative_brief(product_title, insights, your_product, review_analysis=None):
    purchase_criteria = insights.get("purchase_criteria", [])
    criteria_text = "\n".join([
        f"- {c['criterion']} ({c['importance']} impact, {c['percentage']}%): {c['description']}"
        for c in purchase_criteria
    ])

    praises = ""
    complaints = ""
    if review_analysis:
        praises = "Real customer praises: " + ", ".join(review_analysis.get("top_praises", []))
        complaints = "Real customer complaints to address: " + ", ".join(review_analysis.get("top_complaints", []))

    prompt = f"""You are a world-class Amazon creative strategist who writes briefs for AI image generation tools like Pixii.

PRODUCT: {product_title}
PRICE: {your_product.get('price', 'N/A')} | RATING: {your_product.get('rating', 0)}★ | BRAND: {your_product.get('brand', 'Unknown')}

KEY PURCHASE CRITERIA:
{criteria_text}

{praises}
{complaints}

MARKET GAP: {insights.get('market_gap', '')}
WINNING ANGLE: {insights.get('winning_angle', '')}
CUSTOMER PROFILE: {insights.get('customer_profile', '')}

Return ONLY valid JSON (no markdown):
{{
  "hero_angle": "string",
  "target_emotion": "string",
  "tone": "string",
  "brief_summary": "string",
  "image_stack": [
    {{"slot": 1, "role": "Main Image", "what_to_show": "string", "why_it_converts": "string", "pixii_prompt": "string"}},
    {{"slot": 2, "role": "Hero Lifestyle", "what_to_show": "string", "why_it_converts": "string", "pixii_prompt": "string"}},
    {{"slot": 3, "role": "Problem-Solution", "what_to_show": "string", "why_it_converts": "string", "pixii_prompt": "string"}},
    {{"slot": 4, "role": "Key Feature Callout", "what_to_show": "string", "why_it_converts": "string", "pixii_prompt": "string"}},
    {{"slot": 5, "role": "Social Proof / Results", "what_to_show": "string", "why_it_converts": "string", "pixii_prompt": "string"}},
    {{"slot": 6, "role": "Objection Killer", "what_to_show": "string", "why_it_converts": "string", "pixii_prompt": "string"}},
    {{"slot": 7, "role": "Brand Story / Trust", "what_to_show": "string", "why_it_converts": "string", "pixii_prompt": "string"}}
  ],
  "headline_options": ["string", "string", "string"],
  "copy_angles": [
    {{"angle": "string", "one_liner": "string"}},
    {{"angle": "string", "one_liner": "string"}},
    {{"angle": "string", "one_liner": "string"}}
  ],
  "biggest_mistake_to_avoid": "string"
}}"""

    result = _ask_gemini(prompt)
    return result or get_fallback_creative_brief()


def chat_with_data(user_message: str, context: dict, history: list) -> str:
    """AI assistant that answers questions about the analysis."""
    history_text = ""
    for msg in history[-6:]:  # last 3 turns
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"

    prompt = f"""You are an expert Amazon market intelligence analyst. Answer the user's question using the analysis data below.

ANALYSIS DATA:
- Product: {context.get('title', 'Unknown')}
- Price: {context.get('currency','')}{context.get('price', 0)}
- Rating: {context.get('rating', 0)}★ ({context.get('review_count', 0)} reviews)
- BSR: #{context.get('bsr', 'N/A')}
- Est. Monthly Revenue: {context.get('currency','')}{context.get('monthly_revenue', 0):,.0f}
- Market Total: {context.get('currency','')}{context.get('total_market', 0):,.0f}/mo
- Competitors analyzed: {context.get('num_competitors', 0)}
- Market Gap: {context.get('market_gap', '')}
- Winning Angle: {context.get('winning_angle', '')}
- Customer Profile: {context.get('customer_profile', '')}
- Top Complaints: {', '.join(context.get('top_complaints', []))}
- Top Praises: {', '.join(context.get('top_praises', []))}
- Competitor Weaknesses: {', '.join(context.get('competitor_weaknesses', []))}
- Verdict: {context.get('verdict', '')}
- Trend: {context.get('trend_label', '')} ({context.get('trend_pct', 0):+}% over 12 months)

CONVERSATION HISTORY:
{history_text}

User: {user_message}

Reply in 2-4 sentences max. Be direct, specific, and actionable. No generic advice."""

    try:
        model = setup_gemini()
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Sorry, I couldn't process that question. Error: {e}"


# ── FALLBACKS ────────────────────────────────────────────────────────────────

def get_fallback_review_analysis():
    return {
        "purchase_criteria": [],
        "top_complaints": ["Delivery delays", "Packaging issues", "Value for money"],
        "top_praises": ["Good quality", "Fast shipping", "Works as described"],
        "competitor_weaknesses": ["Poor after-sales support", "Inconsistent quality"],
        "unmet_needs": ["Better warranty", "Clearer instructions"],
        "sentiment_breakdown": {"5_star_pct": 60, "4_star_pct": 20, "3_star_pct": 10, "1_2_star_pct": 10},
        "review_insights_summary": "Reviews suggest quality and delivery are the main drivers of satisfaction in this category.",
    }


def get_fallback_analysis():
    return {
        "purchase_criteria": [
            {"criterion": "Quality", "importance": "High", "percentage": 85, "description": "Customers prioritize build quality and durability"},
            {"criterion": "Price", "importance": "High", "percentage": 75, "description": "Value for money is a key decision factor"},
            {"criterion": "Ease of Use", "importance": "Medium", "percentage": 65, "description": "Simple setup and usage preferred"},
            {"criterion": "Brand Trust", "importance": "Medium", "percentage": 55, "description": "Established brands get preference"},
            {"criterion": "Shipping Speed", "importance": "Low", "percentage": 40, "description": "Fast delivery appreciated"},
        ],
        "market_gap": "No product fully addresses durability concerns at an affordable price point",
        "winning_angle": "Focus on superior packaging, clearer instructions, and bundled accessories",
        "sentiment_score": 72,
        "customer_profile": "Value-conscious shoppers aged 25-45 looking for reliable everyday products",
        "price_sensitivity": "Medium",
        "repeat_purchase_rate": "Medium",
        "market_summary": "This is a competitive but growing market with room for a quality-focused brand to dominate.",
    }


def get_fallback_scorecard():
    return {
        "overall_score": 65,
        "rank_in_market": 4,
        "scores": {
            "price_competitiveness": 70,
            "social_proof": 60,
            "market_position": 65,
            "revenue_performance": 55,
            "growth_potential": 75,
        },
        "strengths": ["Competitive pricing", "Good rating", "Growing review count"],
        "weaknesses": ["Lower brand recognition", "Fewer reviews than top competitors", "BSR needs improvement"],
        "quick_wins": ["Add more product images", "Optimize title with keywords", "Bundle with accessories"],
        "threat_level": "Medium",
        "verdict": "Solid product with room to grow — focus on review acquisition and listing optimization.",
    }


def get_fallback_creative_brief():
    return {
        "hero_angle": "The product that does exactly what it promises.",
        "target_emotion": "Confidence and relief",
        "tone": "Clean and trustworthy",
        "brief_summary": "Lead with clarity and trust. Every image should answer a question or kill a doubt.",
        "image_stack": [
            {"slot": 1, "role": "Main Image", "what_to_show": "Product on clean white background", "why_it_converts": "Clarity wins clicks in search", "pixii_prompt": "Studio product shot on pure white background, sharp focus, professional lighting"},
            {"slot": 2, "role": "Hero Lifestyle", "what_to_show": "Happy customer using product in real-life setting", "why_it_converts": "Buyers imagine themselves using it", "pixii_prompt": "Lifestyle photo of person using product in bright natural setting, warm tones"},
            {"slot": 3, "role": "Problem-Solution", "what_to_show": "Before/after split showing the problem this solves", "why_it_converts": "Reminds buyer of the pain and positions product as the fix", "pixii_prompt": "Split image showing problem on left, solution on right"},
            {"slot": 4, "role": "Key Feature Callout", "what_to_show": "Close-up of the most praised feature", "why_it_converts": "Validates the top purchase criterion", "pixii_prompt": "Close-up detail shot with bold annotation arrows and feature text"},
            {"slot": 5, "role": "Social Proof / Results", "what_to_show": "Star rating graphic + number of happy customers", "why_it_converts": "Reduces perceived risk", "pixii_prompt": "Infographic with 5-star rating and trust badges"},
            {"slot": 6, "role": "Objection Killer", "what_to_show": "Address the #1 concern visually", "why_it_converts": "Removes the last blocker before purchase", "pixii_prompt": "Reassuring visual showing quality and ease of use with checkmarks"},
            {"slot": 7, "role": "Brand Story / Trust", "what_to_show": "Brand values and quality promise", "why_it_converts": "Builds brand equity and justifies the price", "pixii_prompt": "Brand-focused image with logo and premium aesthetic"},
        ],
        "headline_options": ["Finally — a product that actually works.", "Designed for people who are tired of settling.", "The last one you'll ever need to buy."],
        "copy_angles": [
            {"angle": "Quality Promise", "one_liner": "Built to last, priced to be a no-brainer."},
            {"angle": "Problem Solver", "one_liner": "Stop putting up with products that almost work."},
            {"angle": "Value Play", "one_liner": "Premium results. Everyday price."},
        ],
        "biggest_mistake_to_avoid": "Using generic stock-style images — your visuals must prove your specific claims.",
    }