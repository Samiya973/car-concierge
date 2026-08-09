"""Generates a mock car marketplace dataset satisfying the brief:
>= 100 listings, >= 10 categories, >= 10 brands per category.

Run: python -m app.data.generate_listings
Writes: app/data/listings.json
"""
import json
import random
import datetime
import os

random.seed(42)

CATEGORIES = {
    "Hatchback": ["Maruti Suzuki", "Hyundai", "Tata", "Volkswagen", "Ford",
                  "Honda", "Toyota", "Renault", "Nissan", "Kia"],
    "Sedan": ["Honda", "Hyundai", "Toyota", "Skoda", "Volkswagen",
              "Maruti Suzuki", "Nissan", "Ford", "Mahindra", "MG"],
    "SUV": ["Mahindra", "Tata", "Hyundai", "Kia", "Toyota",
            "MG", "Jeep", "Ford", "Honda", "Skoda"],
    "Luxury Sedan": ["BMW", "Mercedes-Benz", "Audi", "Jaguar", "Volvo",
                      "Lexus", "Genesis", "Cadillac", "Infiniti", "Maserati"],
    "Luxury SUV": ["BMW", "Mercedes-Benz", "Audi", "Land Rover", "Volvo",
                    "Porsche", "Lexus", "Cadillac", "Bentley", "Infiniti"],
    "Electric": ["Tesla", "Tata", "MG", "Hyundai", "BYD",
                 "Kia", "Mahindra", "BMW", "Mercedes-Benz", "Volvo"],
    "Pickup Truck": ["Ford", "Toyota", "Chevrolet", "Isuzu", "Mahindra",
                      "Ram", "GMC", "Nissan", "Volkswagen", "Great Wall"],
    "Minivan": ["Toyota", "Honda", "Kia", "Chrysler", "Mercedes-Benz",
                "Maruti Suzuki", "Renault", "Volkswagen", "Nissan", "Hyundai"],
    "Sports Car": ["Ford", "Chevrolet", "BMW", "Porsche", "Nissan",
                    "Audi", "Mercedes-Benz", "Toyota", "Jaguar", "Alfa Romeo"],
    "Convertible": ["BMW", "Mercedes-Benz", "Audi", "Mazda", "Ford",
                     "Chevrolet", "Porsche", "Mini", "Fiat", "Jaguar"],
    "Off-Roader": ["Jeep", "Land Rover", "Toyota", "Mahindra", "Ford",
                    "Suzuki", "Nissan", "Isuzu", "Mitsubishi", "GMC"],
}

FUEL_BY_CATEGORY = {
    "Electric": ["electric"],
}
DEFAULT_FUELS = ["petrol", "diesel", "hybrid"]

LOCATIONS = ["Aligarh", "Delhi", "Mumbai", "Bengaluru", "Pune", "Chennai", "Hyderabad", "Noida"]
DEALERS = ["CarNest Dealership", "DriveHub Marketplace", "UrbanWheels Rentals",
           "MetroCars Direct", "SwiftRent", "PrimeAuto Group", "RoadReady Motors"]

BASE_PRICE_RANGE = {
    "Hatchback": (500000, 900000),
    "Sedan": (800000, 1600000),
    "SUV": (1000000, 2200000),
    "Luxury Sedan": (4500000, 9000000),
    "Luxury SUV": (6000000, 15000000),
    "Electric": (1200000, 5000000),
    "Pickup Truck": (900000, 2500000),
    "Minivan": (1100000, 2600000),
    "Sports Car": (3500000, 12000000),
    "Convertible": (4000000, 11000000),
    "Off-Roader": (1500000, 4500000),
}

RENTAL_DAILY_DIVISOR = 900  # crude sale-price -> per-day-rental scaling


def gen_listing(category: str, brand: str, idx: int) -> dict:
    intent = random.choice(["buy", "rent", "buy", "rent", "buy"])
    lo, hi = BASE_PRICE_RANGE[category]
    sale_price = round(random.uniform(lo, hi), -3)
    price = sale_price if intent == "buy" else round(sale_price / RENTAL_DAILY_DIVISOR, -1)
    condition = random.choice(["new", "used", "used", "certified"])
    year = random.randint(2019, 2026) if condition != "new" else 2026
    fuels = FUEL_BY_CATEGORY.get(category, DEFAULT_FUELS + ["electric"] if category in ("SUV", "Sedan") else DEFAULT_FUELS)
    available_from = (datetime.date.today() + datetime.timedelta(days=random.randint(0, 21))).isoformat()
    return {
        "id": f"{category[:3].upper()}-{brand[:3].upper()}-{idx:04d}",
        "brand": brand,
        "model": f"{category.split()[0]} {random.choice(['X', 'S', 'GT', 'Pro', 'Plus', 'Line', 'Series'])}".strip(),
        "category": category,
        "year": year,
        "price": price,
        "intent": intent,
        "mileage_km": 0 if condition == "new" else random.randint(2000, 90000),
        "condition": condition,
        "seats": random.choice([2, 4, 5, 5, 5, 7]) if category != "Sports Car" else random.choice([2, 4]),
        "fuel_type": random.choice(fuels),
        "location": random.choice(LOCATIONS),
        "available_from": available_from,
        "dealer": random.choice(DEALERS),
        "image_seed": f"{brand}-{category}-{idx}".replace(" ", "-").lower(),
    }


def generate(min_total: int = 130) -> list[dict]:
    listings = []
    idx = 0
    for category, brands in CATEGORIES.items():
        for brand in brands:
            idx += 1
            listings.append(gen_listing(category, brand, idx))
    while len(listings) < min_total:
        idx += 1
        category = random.choice(list(CATEGORIES.keys()))
        brand = random.choice(CATEGORIES[category])
        listings.append(gen_listing(category, brand, idx))
    return listings


def main():
    listings = generate()
    out_path = os.path.join(os.path.dirname(__file__), "listings.json")
    with open(out_path, "w") as f:
        json.dump(listings, f, indent=2)
    print(f"Generated {len(listings)} listings across {len(CATEGORIES)} categories -> {out_path}")


if __name__ == "__main__":
    main()