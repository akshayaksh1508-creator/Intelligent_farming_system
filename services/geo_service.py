"""Reverse geocoding for phone GPS coordinates (free BigDataCloud client API, no key)."""

import requests


def reverse_geocode(lat, lon):
    try:
        resp = requests.get(
            "https://api.bigdatacloud.net/data/reverse-geocode-client",
            params={"latitude": lat, "longitude": lon, "localityLanguage": "en"},
            timeout=5,
        )
        if resp.status_code != 200:
            return None
        data = resp.json() or {}
        return {
            "city": data.get("city") or data.get("locality") or "",
            "region": data.get("principalSubdivision") or "",
            "country": data.get("countryName") or "India",
        }
    except Exception:
        return None
