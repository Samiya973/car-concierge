from __future__ import annotations
import asyncio
import datetime
import json
import os
import re
from dotenv import load_dotenv
load_dotenv()
from app.agent.state import AgentSession, Stage, RankedListing
from langfuse.langchain import CallbackHandler
from langchain_google_genai import ChatGoogleGenerativeAI

# Initialize the Langfuse handler and free Gemini model
langfuse_handler = CallbackHandler()
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
LISTINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "listings.json")
try:
    with open(LISTINGS_FILE, "r", encoding="utf-8") as f:
        RAW_LISTINGS = json.load(f)
except Exception:
    RAW_LISTINGS = []

CATEGORY_ALIASES = [
    ("luxury suv", "Luxury SUV"),
    ("luxury sedan", "Luxury Sedan"),
    ("pickup truck", "Pickup Truck"),
    ("off-roader", "Off-Roader"),
    ("off roader", "Off-Roader"),
    ("off road", "Off-Roader"),
    ("sports car", "Sports Car"),
    ("convertible", "Convertible"),
    ("hatchback", "Hatchback"),
    ("minivan", "Minivan"),
    ("electric", "Electric"),
    ("sedan", "Sedan"),
    ("suv", "SUV"),
    ("luxury", "Luxury SUV"),
    ("ev", "Electric"),
    ("truck", "Pickup Truck"),
    ("van", "Minivan"),
    ("sports", "Sports Car"),
]

FUEL_ALIASES = [
    ("petrol", "petrol"), ("diesel", "diesel"),
    ("electric", "electric"), ("hybrid", "hybrid"), ("cng", "cng"),
]

SKIP_WORDS = {"any", "no preference", "skip", "none", "n/a", "na", "flexible", "doesn't matter", "dont care", "don't care"}


def detect_category(msg_lower: str) -> str | None:
    for alias, canonical in CATEGORY_ALIASES:
        if alias in msg_lower:
            return canonical
    return None


def parse_budget(text: str) -> float | None:
    t = text.lower().replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(lakhs?|lac|l|crores?|cr)?", t)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2)
    if unit in ("lakh", "lakhs", "lac", "l"):
        val *= 100_000
    elif unit in ("crore", "crores", "cr"):
        val *= 10_000_000
    elif val < 1000:
        val *= 100_000
    return val


def parse_seats(text: str) -> int | None:
    low = text.lower()
    if any(w in low for w in SKIP_WORDS):
        return None
    m = re.search(r"\d+", text)
    if m:
        n = int(m.group(0))
        if 1 <= n <= 12:
            return n
    word_numbers = {"two": 2, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}
    for word, n in word_numbers.items():
        if word in low:
            return n
    return None


def parse_target_date(text: str) -> str | None:
    low = text.lower().strip()
    if not low or low in SKIP_WORDS:
        return "flexible"

    today = datetime.date.today()
    m = re.search(r"\d{4}-\d{2}-\d{2}", text)
    if m:
        return m.group(0)

    if any(w in low for w in ["today", "asap", "immediately", "now", "urgent"]):
        return today.isoformat()
    if "tomorrow" in low:
        return (today + datetime.timedelta(days=1)).isoformat()
    if "next week" in low:
        return (today + datetime.timedelta(days=7)).isoformat()
    if "next month" in low:
        return (today + datetime.timedelta(days=30)).isoformat()
    m = re.search(r"in\s+(\d+)\s*(day|week|month)s?", low)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        days = n if unit == "day" else n * 7 if unit == "week" else n * 30
        return (today + datetime.timedelta(days=days)).isoformat()

    return text.strip()[:60]


async def handle_user_message_stream(session: AgentSession, user_message: str, chat_history: list | None = None):
    """Multi-turn interview: intent -> use_case -> category -> budget ->
    seats -> target_date -> fuel_type -> recommend."""
    msg_lower = user_message.lower()
    prefs = session.preferences

    # --- MCP CHECKOUT APP TRIGGER (FORM FIRST, THEN PAYMENT) ---
    if session.results:
        is_checkout = any(kw in msg_lower for kw in ["reserve", "book", "checkout", "pay", "buy", "purchase", "secure", "first", "second", "third", "1", "2", "3"])
        
        if is_checkout:
            car_idx = 0
            if "second" in msg_lower or "2" in msg_lower:
                car_idx = 1
            elif "third" in msg_lower or "3" in msg_lower:
                car_idx = 2
            
            if car_idx >= len(session.results):
                car_idx = 0

            target_car = session.results[car_idx].listing
            
            if isinstance(target_car, dict):
                car_id = str(target_car.get("id", "1"))
                car_name = f"{target_car.get('brand', target_car.get('make', 'Vehicle'))} {target_car.get('model', '')}"
                price = target_car.get("price") or target_car.get("rental_price") or 1500000
            else:
                car_id = str(getattr(target_car, "id", "1"))
                car_name = f"{getattr(target_car, 'brand', getattr(target_car, 'make', 'Vehicle'))} {getattr(target_car, 'model', '')}"
                price = getattr(target_car, 'price', None) or getattr(target_car, 'rental_price', None) or 1500000

            if hasattr(Stage, "PAYMENT"):
                session.stage = Stage.PAYMENT

            # Step 1 Payload: Form Filling App first (just like real websites)
            form_payload = {
                "type": "mcp_app_render",
                "app_name": "FormFillingApp",
                "data": {
                    "title": f"Step 1: Booking Details for {car_name}",
                    "amount": price,
                    "intent": prefs.intent or "buy",
                    "car_id": car_id,
                    "car_name": car_name,
                    "submit_endpoint": "/api/checkout/proceed-to-payment",
                    "form_fields": [
                        {"id": "name", "label": "Full Name", "type": "text", "required": True},
                        {"id": "email", "label": "Email Address", "type": "email", "required": True},
                        {"id": "phone", "label": "Phone Number", "type": "tel", "required": True},
                        {"id": "date", "label": "Booking / Rental Date", "type": "date", "required": True}
                    ]
                }
            }
            yield json.dumps(form_payload)
            return

    # --- INTERVIEW PROFILE FILLING ---
    if not prefs.intent:
        if "rent" in msg_lower:
            prefs.intent = "rent"
        elif "buy" in msg_lower or "purchase" in msg_lower:
            prefs.intent = "buy"

    elif not prefs.use_case:
        prefs.use_case = user_message.strip()[:80]

    elif not prefs.category:
        detected = detect_category(msg_lower)
        if detected:
            prefs.category = detected

    elif not prefs.budget_max and prefs.intent != "rent":
        val = parse_budget(user_message)
        if val:
            prefs.budget_max = val

    elif not prefs.seats:
        seats = parse_seats(user_message)
        if seats:
            prefs.seats = seats
        elif any(w in msg_lower for w in SKIP_WORDS):
            prefs.seats = 5

    elif not prefs.target_date:
        prefs.target_date = parse_target_date(user_message)

    elif not prefs.fuel_type:
        matched = False
        for alias, canonical in FUEL_ALIASES:
            if alias in msg_lower:
                prefs.fuel_type = canonical
                matched = True
                break
        if not matched and any(w in msg_lower for w in SKIP_WORDS):
            prefs.fuel_type = "any"

    intent = prefs.intent
    use_case = prefs.use_case
    category = prefs.category
    budget_val = prefs.budget_max
    seats = prefs.seats
    target_date = prefs.target_date
    fuel_val = prefs.fuel_type

    # --- QUESTIONING & RECOMMENDATION GENERATION ---
    if not intent:
        response_chunk = "Welcome! Are you looking to **buy** or **rent** a vehicle today?"
    elif not use_case:
        response_chunk = "What will you mainly use it for — daily commute, family trips, weekend getaways, work?"
    elif not category:
        response_chunk = (
            "What type of car — SUV, Sedan, Hatchback, Electric, Luxury SUV, "
            "Luxury Sedan, Minivan, Pickup Truck, Sports Car, Convertible, or Off-Roader?"
        )
    elif not budget_val and intent != "rent":
        response_chunk = "What's your max budget? (e.g. 15 lakhs, 1500000, 1.5 cr)"
    elif not seats:
        response_chunk = "How many seats do you need? (e.g. 5, 7, or 'any')"
    elif not target_date:
        response_chunk = "By when do you need it? (a date, 'next week', 'ASAP', or 'flexible')"
    elif not fuel_val:
        response_chunk = "Any engine/fuel preference — Petrol, Diesel, Electric, Hybrid, CNG, or 'any'?"
    else:
        if hasattr(Stage, "RECOMMEND"):
            session.stage = Stage.RECOMMEND
        elif hasattr(Stage, "RECOMMENDING"):
            session.stage = Stage.RECOMMENDING
            
        # Prevent infinite loop if recommendations already exist
        if getattr(session, "results", None) and len(session.results) > 0:
            response_chunk = "I've already found some great matches for you in the panel! Would you like to **reserve** one of them?"
            for word in response_chunk.split(" "):
                yield word + " "
                await asyncio.sleep(0.01)
            return

        pool = RAW_LISTINGS
        pool = [c for c in pool if str(c.get("intent", "")).lower() == intent.lower()]
        after_intent = pool

        pool = [c for c in pool if str(c.get("category", "")).lower() == category.lower()]
        category_matched = len(pool) > 0
        if not category_matched:
            pool = after_intent

        budget_matched = True
        if budget_val and intent != "rent":
            bf = []
            for c in pool:
                p = c.get("price")
                if p is not None:
                    try:
                        if float(p) <= float(budget_val) * 1.25:  # Slightly expanded margin
                            bf.append(c)
                    except (TypeError, ValueError):
                        pass
            budget_matched = len(bf) > 0
            if budget_matched:
                pool = bf

        seats_matched = True
        if seats and category_matched and budget_matched:
            sf = [c for c in pool if c.get("seats", 0) >= seats]
            if len(sf) >= 2:  # Only filter strictly if we have enough items
                pool = sf

        fuel_matched = True
        if fuel_val and fuel_val not in ("any",) and category_matched and budget_matched:
            ff = [c for c in pool if str(c.get("fuel_type", "")).lower() == fuel_val.lower()]
            if len(ff) >= 2:
                pool = ff

        # Fallback / Padding: Ensure we always have at least 3 ranked matches
        if len(pool) < 3:
            existing_ids = {c.get("id") for c in pool}
            for car in RAW_LISTINGS:
                if car.get("id") not in existing_ids:
                    pool.append(car)
                if len(pool) >= 4:
                    break

        if not pool:
            pool = RAW_LISTINGS[:4]

        # Assign ranked results with descending scores (Top 4 ranked)
        session.results = [
            RankedListing(
                listing=car,
                score=round(98.0 - (i * 3.5), 1),
                explanation=(
                    f"Rank #{i+1}: Matches your {intent} {category} preference for {use_case}, seats {car.get('seats')}, "
                    f"available around {target_date}. Offered by {car.get('dealer', 'a trusted dealer')}."
                ),
            )
            for i, car in enumerate(pool[:4])
        ]
        session.log(f"Generated {len(session.results)} ranked recommendations for {intent}/{category}.")

        if intent == "rent":
            header = f"Based on your preferences (**RENT**, **{category}**, daily rate structure, {seats} seats)"
        else:
            header = f"Based on your preferences (**BUY**, **{category}**, up to **\u20b9{budget_val:,.0f}**, {seats} seats)"
        
        prompt = (
            f"The user wants to {intent} a {category} for {use_case}, budget up to {budget_val}, "
            f"{seats} seats, fuel type {fuel_val}. We found {len(session.results)} matching vehicles. "
            f"Write a concise, friendly summary message introducing these top ranked matches. Context header: {header}"
        )
        try:
            llm_result = llm.invoke(prompt, config={"callbacks": [langfuse_handler]})
            response_chunk = llm_result.content
        except Exception as e:
            response_chunk = f"{header}, I found **{len(session.results)} top-tier matching vehicles** ranked for you! Check out the **Matches** panel."
    
    for word in response_chunk.split(" "):
        yield word + " "
        await asyncio.sleep(0.01)