"""Deterministic ranking engine.

Kept rule-based (not an LLM call) so it's fast, explainable, and free to run
many times during a demo. The LLM is used for the *interview* and for
turning the score breakdown into natural language, not for the arithmetic.
"""
from __future__ import annotations
import datetime
from .state import CarListing, UserPreferences, RankedListing


def _budget_score(price: float, prefs: UserPreferences) -> float:
    if prefs.budget_max is None:
        return 0.5
    lo = prefs.budget_min or 0
    hi = prefs.budget_max
    if lo <= price <= hi:
        return 1.0
    if price > hi:
        overshoot = (price - hi) / hi
        return max(0.0, 1.0 - overshoot * 1.5)
    undershoot = (lo - price) / max(lo, 1)
    return max(0.3, 1.0 - undershoot)


def _category_score(listing: CarListing, prefs: UserPreferences) -> float:
    if not prefs.category:
        return 0.5
    return 1.0 if listing.category.lower() == prefs.category.lower() else 0.15


def _intent_score(listing: CarListing, prefs: UserPreferences) -> float:
    if not prefs.intent:
        return 0.5
    return 1.0 if listing.intent == prefs.intent else 0.0


def _date_score(listing: CarListing, prefs: UserPreferences) -> float:
    if not prefs.target_date:
        return 0.5
    try:
        target = datetime.date.fromisoformat(prefs.target_date)
        avail = datetime.date.fromisoformat(listing.available_from)
    except ValueError:
        return 0.5
    delta_days = (avail - target).days
    if delta_days <= 0:
        return 1.0
    return max(0.0, 1.0 - delta_days / 30)


def _seats_score(listing: CarListing, prefs: UserPreferences) -> float:
    if not prefs.seats:
        return 0.5
    return 1.0 if listing.seats >= prefs.seats else 0.2


def _fuel_score(listing: CarListing, prefs: UserPreferences) -> float:
    if not prefs.fuel_type:
        return 0.5
    return 1.0 if listing.fuel_type == prefs.fuel_type else 0.4


WEIGHTS = {
    "intent": 0.30,
    "category": 0.25,
    "budget": 0.25,
    "date": 0.10,
    "seats": 0.06,
    "fuel": 0.04,
}


def score_listing(listing: CarListing, prefs: UserPreferences) -> tuple[float, dict]:
    parts = {
        "intent": _intent_score(listing, prefs),
        "category": _category_score(listing, prefs),
        "budget": _budget_score(listing.price, prefs),
        "date": _date_score(listing, prefs),
        "seats": _seats_score(listing, prefs),
        "fuel": _fuel_score(listing, prefs),
    }
    total = sum(parts[k] * WEIGHTS[k] for k in WEIGHTS)
    return round(total * 100, 1), parts


def explain(listing: CarListing, prefs: UserPreferences, parts: dict) -> str:
    bits = []
    if parts["intent"] == 1.0 and prefs.intent:
        bits.append(f"matches your {prefs.intent} intent")
    if parts["category"] == 1.0:
        bits.append(f"is the {listing.category} type you asked for")
    if parts["budget"] >= 0.9:
        bits.append("fits comfortably inside your budget")
    elif parts["budget"] < 0.6:
        bits.append("stretches your budget a bit")
    if parts["date"] == 1.0 and prefs.target_date:
        bits.append(f"is available by {prefs.target_date}")
    if parts["seats"] == 1.0 and prefs.seats:
        bits.append(f"seats {listing.seats}, enough for your group")
    if not bits:
        bits.append("is a reasonable general match")
    return f"{listing.brand} {listing.model} ({listing.year}) " + ", ".join(bits) + "."


def rank(listings: list[CarListing], prefs: UserPreferences, top_n: int = 6) -> list[RankedListing]:
    scored = []
    for listing in listings:
        score, parts = score_listing(listing, prefs)
        scored.append(RankedListing(listing=listing, score=score, explanation=explain(listing, prefs, parts)))
    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:top_n]