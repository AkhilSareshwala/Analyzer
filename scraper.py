import requests
import time
import random
import os
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import streamlit as st
load_dotenv()

SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY") or st.secrets.get("SCRAPER_API_KEY")
BASE_URL = "https://api.scraperapi.com/" 
STRUCTURED_URL = "https://api.scraperapi.com/structured/amazon/product"


# ── STRUCTURED PRODUCT ENDPOINT ───────────────────────────────────────────────
def scrape_structured(asin: str, tld: str = "in") -> dict | None:
    """
    ScraperAPI structured Amazon product endpoint — returns listing data AND
    embedded reviews in JSON. Reviews page now requires login so we use this.
    https://docs.scraperapi.com/structured-data-endpoints/e-commerce/amazon/amazon-product-api
    """
    payload = {
        "api_key": SCRAPER_API_KEY,
        "asin": asin,
        "tld": tld,
        "country_code": tld if tld != "com" else "us",
    }
    try:
        r = requests.get(STRUCTURED_URL, params=payload, timeout=90)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"Structured endpoint {r.status_code}: {r.text[:300]}")
            return None
    except Exception as e:
        print(f"Structured request failed: {e}")
        return None


def scrape_autoparse(url: str) -> dict | None:
    payload = {
        "api_key": SCRAPER_API_KEY,
        "url": url,
        "autoparse": "true",
        "output_format": "json",
        "country_code": "in" if "amazon.in" in url else "us",
    }
    try:
        r = requests.get(BASE_URL, params=payload, timeout=60)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"Autoparse error {r.status_code}: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"Autoparse failed: {e}")
        return None


def scrape_raw_html(url: str) -> str | None:
    payload = {
        "api_key": SCRAPER_API_KEY,
        "url": url,
        "render": "true",
        "country_code": "in" if "amazon.in" in url else "us",
    }
    try:
        r = requests.get(BASE_URL, params=payload, timeout=60)
        if r.status_code == 200:
            return r.text
        return None
    except Exception as e:
        print(f"Raw scrape failed: {e}")
        return None


def extract_asin(url: str) -> str | None:
    try:
        match = re.search(r'/dp/([A-Z0-9]{10})', url)
        if match:
            return match.group(1)
        for part in url.split("/"):
            clean = part.split("?")[0]
            if re.match(r'^[A-Z0-9]{10}$', clean):
                return clean
    except:
        pass
    return None


def get_tld(url: str) -> str:
    match = re.search(r'amazon\.(\w+)', url)
    return match.group(1) if match else "com"


# ── EXTRACT REVIEWS FROM STRUCTURED RESPONSE ──────────────────────────────────
def extract_reviews_from_structured(data: dict) -> list:
    """Pull reviews from any key the structured endpoint may return them under."""
    reviews = []
    seen = set()

    # All the keys ScraperAPI may put reviews under
    candidates = (
        data.get("reviews") or
        data.get("top_reviews") or
        data.get("customer_reviews_list") or
        (data.get("customer_reviews") or {}).get("reviews") or
        []
    )

    if isinstance(candidates, list):
        for r in candidates:
            if not isinstance(r, dict):
                continue
            body = (r.get("body") or r.get("review_body") or
                    r.get("text") or r.get("content") or r.get("review_text") or "").strip()
            if not body or body in seen:
                continue
            seen.add(body)
            title = r.get("title") or r.get("review_title") or ""
            try:
                rating = float(str(r.get("rating") or r.get("stars") or r.get("star_rating") or 0).split()[0])
            except:
                rating = 0.0
            reviews.append({"title": title, "body": body, "rating": rating})

    return reviews


# ── MAIN GETTER ───────────────────────────────────────────────────────────────
def get_listing_and_reviews(url: str) -> tuple:
    """
    Returns (listing_dict, reviews_list).
    Uses structured endpoint first (gives reviews), falls back to autoparse.
    """
    asin = extract_asin(url)
    tld = get_tld(url)
    reviews = []
    structured_data = None

    if asin:
        structured_data = scrape_structured(asin, tld)
        if structured_data:
            reviews = extract_reviews_from_structured(structured_data)
            print(f"  Structured: {len(reviews)} reviews for {asin}")

    # Parse listing from structured
    listing = None
    if structured_data:
        listing = _parse_listing(structured_data, url, asin, source="structured")

    # Fallback to autoparse if structured gave no good title
    if not listing or not listing.get("price"):
        print(f"  Falling back to autoparse for {asin or url[:40]}")
        fallback = scrape_autoparse(url)
        if fallback:
            fallback_listing = _parse_listing(fallback, url, asin, source="autoparse")
            if listing:
                # Merge: prefer structured for reviews-related fields, autoparse for price
                if fallback_listing.get("price", 0) > 0:
                    listing["price"] = fallback_listing["price"]
                if fallback_listing.get("bsr", 999999) < listing.get("bsr", 999999):
                    listing["bsr"] = fallback_listing["bsr"]
                if not listing.get("title") or listing["title"] == "Unknown Product":
                    listing["title"] = fallback_listing.get("title", "Unknown Product")
            else:
                listing = fallback_listing

    return listing, reviews


def _parse_listing(data: dict, url: str, asin: str, source: str = "structured") -> dict:
    # Price
    price = 0.0
    for key in ["price", "price_upper", "list_price", "pricing"]:
        raw = data.get(key, "") or ""
        if raw:
            try:
                p = float(str(raw).replace("₹","").replace("$","").replace(",","").replace("INR","").strip())
                if p > 0:
                    price = p
                    break
            except:
                pass

    # Rating
    rating = 0.0
    for key in ["average_rating", "stars", "rating"]:
        raw = data.get(key) or (data.get("customer_reviews") or {}).get("stars", 0)
        try:
            r = float(str(raw).split()[0])
            if r > 0:
                rating = r
                break
        except:
            pass

    # Review count
    review_count = 0
    for key in ["total_reviews", "ratings_count", "total_ratings", "review_count"]:
        raw = data.get(key) or (data.get("customer_reviews") or {}).get("ratings_count", 0)
        try:
            rc = int(str(raw).replace(",", ""))
            if rc > 0:
                review_count = rc
                break
        except:
            pass

    # BSR
    bsr = 999999
    bsr_raw = ((data.get("product_information") or {}).get("Best Sellers Rank") or
               data.get("best_sellers_rank") or data.get("Best Sellers Rank") or [])
    if isinstance(bsr_raw, list) and bsr_raw:
        try:
            num = "".join(c for c in str(bsr_raw[0]).split("in")[0] if c.isdigit() or c == ",")
            bsr = int(num.replace(",", ""))
        except:
            pass
    elif isinstance(bsr_raw, str) and bsr_raw:
        try:
            num = "".join(c for c in bsr_raw.split("in")[0] if c.isdigit() or c == ",")
            bsr = int(num.replace(",", ""))
        except:
            pass

    # Brand
    brand = str(data.get("brand", "") or (data.get("product_information") or {}).get("Brand", "") or "")
    brand = brand.replace("Visit the ", "").replace(" Store", "").strip() or "Unknown"

    # Title
    title = data.get("name") or data.get("title") or "Unknown Product"

    return {
        "title": title, "price": price, "rating": rating,
        "review_count": review_count, "bsr": bsr, "brand": brand,
        "asin": data.get("asin") or asin, "url": url,
    }


def get_listing_data(url: str) -> dict | None:
    """Backwards-compatible wrapper."""
    listing, _ = get_listing_and_reviews(url)
    return listing


# ── COMPETITORS ───────────────────────────────────────────────────────────────
def get_competitors(url: str, num_competitors: int = 9) -> list:
    asin = extract_asin(url)
    base_domain = "https://www.amazon.in" if "amazon.in" in url else "https://www.amazon.com"

    listing = scrape_autoparse(url)
    if not listing:
        return []

    title = listing.get("name") or listing.get("title") or ""
    words = title.split()
    search_words = words[1:5] if len(words) > 4 else words[:4]
    search_query = "+".join(search_words).replace("&", "and")
    search_url = f"{base_domain}/s?k={search_query}"
    print(f"Competitor search: {search_query}")

    html = scrape_raw_html(search_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    competitor_urls = []
    seen_asins = {asin} if asin else set()

    for item in soup.find_all("div", {"data-asin": True}):
        item_asin = item.get("data-asin", "").strip()
        if not item_asin or item_asin in seen_asins:
            continue
        if item.find(class_=lambda c: c and 'sponsored' in c.lower()):
            continue
        competitor_urls.append(f"{base_domain}/dp/{item_asin}")
        seen_asins.add(item_asin)
        if len(competitor_urls) >= num_competitors:
            break

    # Fallback: scan all hrefs
    if len(competitor_urls) < 3:
        for a_tag in soup.find_all("a", href=True):
            m = re.search(r'/dp/([A-Z0-9]{10})', a_tag.get("href", ""))
            if m:
                fa = m.group(1)
                if fa not in seen_asins:
                    competitor_urls.append(f"{base_domain}/dp/{fa}")
                    seen_asins.add(fa)
                    if len(competitor_urls) >= num_competitors:
                        break

    print(f"Found {len(competitor_urls)} competitors")
    return competitor_urls[:num_competitors]


def get_reviews_bulk(url: str, asin: str, max_pages: int = 1) -> list:
    """
    Fetch reviews for a product URL. The max_pages parameter is provided for
    compatibility but the ScraperAPI structured endpoint returns all available reviews
    in a single request (since Amazon review pages now require login).
    Returns a list of review dictionaries with 'title', 'body', and 'rating' keys.
    """
    _, reviews = get_listing_and_reviews(url)
    return reviews


def estimate_monthly_revenue(bsr, price):
    if not bsr or bsr <= 0 or bsr >= 999999:
        return 0
    bsr_sales_map = [
        (1, 3000), (5, 2500), (10, 2000), (25, 1500), (50, 1200),
        (100, 900), (200, 700), (500, 500), (1000, 350), (2000, 250),
        (5000, 150), (10000, 80), (20000, 40), (50000, 15),
        (100000, 5), (200000, 2), (500000, 1),
    ]
    monthly_sales = 1
    for rank, sales in bsr_sales_map:
        if bsr <= rank:
            monthly_sales = sales
            break
    return round(monthly_sales * price, 2)