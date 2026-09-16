import random

CROP_PRICES = {
    "Tomato": 2450, "Rice": 2183, "Wheat": 2275, "Cotton": 6620,
    "Maize": 2090, "Onion": 2000, "Potato": 1500, "Soybean": 4600,
    "Groundnut": 5850, "Sugarcane": 340, "Mustard": 5450, "Chickpea": 5440
}

def get_market_prices():
    prices = []
    for crop, base_price in CROP_PRICES.items():
        change = round(random.uniform(-6, 10), 1)
        current = int(base_price * (1 + change / 100))
        prices.append({
            "crop": crop,
            "price": current,
            "unit": "Quintal",
            "change_pct": abs(change),
            "trend": "up" if change > 0 else "down" if change < 0 else "stable",
            "market": random.choice(["APMC Mumbai", "Azadpur Delhi", "Hubli Market", "Chennai Market"])
        })
    return prices
