import os
import httpx
from typing import Dict, Any

GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "f8422dc1e1d0ae176d6e95df400f46ff")

def get_travel_news(destination: str) -> str:
    """Fetch travel-related news for a destination using GNews API."""
    if not GNEWS_API_KEY:
        return "News service unavailable (API key missing)."
    
    try:
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": f"travel {destination}",
            "lang": "en",
            "max": 3,
            "apikey": GNEWS_API_KEY
        }
        with httpx.Client(timeout=10) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            
            articles = data.get("articles", [])
            if not articles:
                return f"No recent travel news found for {destination}."
            
            news_summaries = []
            for art in articles:
                news_summaries.append(f"- {art['title']} ({art['source']['name']})")
            
            return "\n".join(news_summaries)
    except Exception as e:
        return f"Error fetching news: {str(e)}"

def generate_intelligence(booking_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate enriched travel intelligence for a booking."""
    destination = booking_data.get("destination", "Unknown")
    customer_name = booking_data.get("customer_name", "Traveler")
    
    # 1. Fetch News Alerts
    news = get_travel_news(destination)
    
    # 2. Generate Recommendations (Mock logic based on destination)
    recommendations = (
        f"Top 3 things for {customer_name} in {destination}:\n"
        f"1. Explore the local historical center.\n"
        f"2. Try the famous regional cuisine at highly-rated local spots.\n"
        f"3. Consider a guided day trip to nearby natural attractions."
    )
    
    # 3. Generate Travel Insights
    insights = (
        f"Travel demand for {destination} is currently high. "
        "We recommend booking local tours at least 48 hours in advance. "
        "The area is known for its vibrant culture and seasonal festivals."
    )
    
    # 4. Destination Intelligence
    dest_intel = (
        f"Destination: {destination}\n"
        "Safety: Generally safe for tourists, exercise normal precautions.\n"
        "Transport: Efficient public transport available; ride-sharing is common.\n"
        "Best time to visit: The current season is ideal for outdoor activities."
    )
    
    return {
        "recommendations": recommendations,
        "travel_insights": insights,
        "destination_intelligence": dest_intel,
        "news_alerts": news,
        "processing_status": "completed"
    }
