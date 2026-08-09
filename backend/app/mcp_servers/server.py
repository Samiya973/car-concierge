"""MCP Server providing car marketplace and auxiliary tools for the agent."""
from __future__ import annotations
import json
import os
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Car Matchmaker MCP Server")

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "listings.json"))

def _load_listings() -> list[dict]:
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r") as f:
        return json.load(f)

@mcp.tool()
def search_listings(
    category: str | None = None,
    intent: str | None = None,
    max_price: float | None = None,
    fuel_type: str | None = None,
    location: str | None = None,
    min_seats: int | None = None,
) -> str:
    """Search car listings in the marketplace dataset based on optional filters."""
    listings = _load_listings()
    filtered = []
    
    for item in listings:
        if category and item["category"].lower() != category.lower():
            continue
        if intent and item["intent"].lower() != intent.lower():
            continue
        if max_price and item["price"] > max_price:
            continue
        if fuel_type and item["fuel_type"].lower() != fuel_type.lower():
            continue
        if location and item["location"].lower() != location.lower():
            continue
        if min_seats and item["seats"] < min_seats:
            continue
        filtered.append(item)
        
    return json.dumps(filtered[:20], indent=2)

@mcp.tool()
def get_insurance_estimate(brand: str, model: str, price: float, intent: str) -> str:
    """Calculate an estimated insurance quote for a given vehicle configuration."""
    if intent == "rent":
        # Daily insurance estimate for rentals
        daily_insurance = round(price * 0.05, 2)
        return json.dumps({
            "type": "rental_daily_protection",
            "cost_per_day": daily_insurance,
            "details": "Includes roadside assistance and comprehensive third-party coverage."
        })
    else:
        # Annual comprehensive insurance estimate for purchase
        annual_insurance = round(price * 0.035, -2)
        return json.dumps({
            "type": "annual_comprehensive",
            "cost_per_year": annual_insurance,
            "details": "Includes zero-depreciation cover, engine protection, and personal accident cover."
        })

if __name__ == "__main__":
    mcp.run()