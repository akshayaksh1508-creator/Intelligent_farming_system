import random
import requests
from flask import current_app
from datetime import datetime

_PRICE_CACHE_TTL_SECONDS = 900
_cache = {}

CROP_PRICES = {
    "Tomato": 2450, "Rice": 2183, "Wheat": 2275, "Cotton": 6620,
    "Maize": 2090, "Onion": 2000, "Potato": 1500, "Soybean": 4600,
    "Groundnut": 5850, "Sugarcane": 340, "Mustard": 5450, "Chickpea": 5440
}

# Commodity names as they appear (uppercase) in the data.gov.in agmarknet records
COMMODITY_ALIASES = {
    "Tomato": ["TOMATO"],
    "Rice": ["RICE", "PADDY"],
    "Wheat": ["WHEAT"],
    "Cotton": ["COTTON", "KAPAS"],
    "Maize": ["MAIZE"],
    "Onion": ["ONION"],
    "Potato": ["POTATO"],
    "Soybean": ["SOYABEAN"],
    "Groundnut": ["GROUNDNUT", "GROUNDNUT PODS"],
    "Sugarcane": ["GUR", "GUR(JAGGERY)"],
    "Mustard": ["MUSTARD"],
    "Chickpea": ["CHICKPEA", "BENGAL GRAM", "CHANA"],
}

MARKETS = ["APMC Mumbai", "Azadpur Delhi", "Hubli Market", "Chennai Market"]


def _fetch_live_prices(state=None):
    api_key = current_app.config.get("DATA_GOV_API_KEY", "")
    if not api_key:
        return None
    try:
        resp = requests.get(
            "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
            params={"api-key": api_key, "format": "json", "limit": 5000},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        records = (resp.json() or {}).get("records") or []
    except Exception:
        return None

    def build(recs):
        dates = sorted({r.get("arrival_date") for r in recs if r.get("arrival_date")})
        if not dates:
            return None
        latest, prev = dates[-1], (dates[-2] if len(dates) > 1 else None)

        latest_by_crop, prev_by_crop = {}, {}
        for r in recs:
            arrival = r.get("arrival_date")
            bucket = None
            if arrival == latest:
                bucket = latest_by_crop
            elif prev and arrival == prev:
                bucket = prev_by_crop
            if bucket is None:
                continue
            try:
                modal = float(r.get("modal_price"))
            except (TypeError, ValueError):
                continue
            if modal <= 0:
                continue
            commodity = (r.get("commodity") or "").strip().upper()
            if commodity:
                bucket.setdefault(commodity, []).append((modal, r.get("market") or "Mandi"))

        prices = []
        for crop, aliases in COMMODITY_ALIASES.items():
            matches = []
            for alias in aliases:
                matches.extend(latest_by_crop.get(alias, []))
            if not matches:
                continue

            avg = sum(m[0] for m in matches) / len(matches)
            markets = sorted({m[1] for m in matches})

            prev_avg = None
            for alias in aliases:
                if alias in prev_by_crop:
                    prev_avg = sum(m[0] for m in prev_by_crop[alias]) / len(prev_by_crop[alias])
                    break
            change_pct = 0.0
            trend = "stable"
            if prev_avg:
                change_pct = round((avg - prev_avg) / prev_avg * 100, 1)
                trend = "up" if change_pct > 0 else "down" if change_pct < 0 else "stable"

            prices.append({
                "crop": crop,
                "price": int(round(avg)),
                "unit": "Quintal",
                "change_pct": abs(change_pct),
                "trend": trend,
                "market": markets[0] if markets else "APMC Mandi",
                "updated": latest,
            })
        return prices or None

    if state:
        state_records = [
            r for r in records
            if (r.get("state") or "").strip().lower() == state.strip().lower()
        ]
        if state_records:
            state_prices = build(state_records)
            if state_prices:
                return state_prices
        # No usable records for that state — fall back to national averages.
    return build(records)


def _fallback_prices():
    seed = datetime.utcnow().strftime("%Y-%m-%d")
    prices = []
    for crop, base_price in CROP_PRICES.items():
        rng = random.Random(f"{seed}:{crop}")
        change = round(rng.uniform(-5, 8), 1)
        current = int(base_price * (1 + change / 100))
        prices.append({
            "crop": crop,
            "price": current,
            "unit": "Quintal",
            "change_pct": abs(change),
            "trend": "up" if change > 0 else "down" if change < 0 else "stable",
            "market": rng.choice(MARKETS),
            "updated": seed,
        })
    return prices


def get_market_prices(limit=None, state=None):
    cache_key = state.strip().lower() if state else "all"
    now_ts = datetime.utcnow().timestamp()
    if _cache.get(f"expires:{cache_key}", 0) > now_ts:
        prices = _cache.get(f"prices:{cache_key}")
    else:
        prices = _fetch_live_prices(state=state) or _fallback_prices()
        _cache[f"prices:{cache_key}"] = prices
        _cache[f"expires:{cache_key}"] = now_ts + _PRICE_CACHE_TTL_SECONDS
    return prices[:limit] if limit else prices
