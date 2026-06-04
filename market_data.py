"""Offline market reference data."""

import json
import os

CACHE_PATH = "data/market_cache.json"


def _load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_cache(data):
    os.makedirs("data", exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


import urllib.request
import datetime

def get_exchange_rates(base="VND", online_enabled=False):
    """Return local rates by default; fetch live rates only when opted in."""
    cache = _load_cache()
    if not online_enabled:
        if "exchange_rates" in cache:
            cache["exchange_rates"]["_source"] = "Local cache (offline)"
            return cache["exchange_rates"]
        return {
            "USD": 1.0,
            "VND": 25400,
            "EUR": 0.92,
            "JPY": 157,
            "CNY": 7.24,
            "_source": "Manual default (offline)",
            "_date": "N/A",
        }
    try:
        # Try fetching real-time online data
        req = urllib.request.Request("https://api.exchangerate-api.com/v4/latest/USD", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8')).get("rates", {})
        
        # Calculate rates relative to base (USD is base in API)
        usd_to_vnd = data.get("VND", 25400)
        
        rates = {
            "USD": 1.0,
            "VND": usd_to_vnd,
            "EUR": data.get("EUR", 0.92),
            "JPY": data.get("JPY", 157),
            "CNY": data.get("CNY", 7.24),
            "_source": "Live API (exchangerate-api.com)",
            "_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        # Save to cache
        cache["exchange_rates"] = rates
        _save_cache(cache)
        return rates
    except Exception:
        # Fallback to cache or hardcoded defaults
        if "exchange_rates" in cache:
            cache["exchange_rates"]["_source"] = "Local cache (offline)"
            return cache["exchange_rates"]
        
        return {
            "USD": 1.0,
            "VND": 25400,
            "EUR": 0.92,
            "JPY": 157,
            "CNY": 7.24,
            "_source": "Manual default (offline)",
            "_date": "N/A",
        }


def get_cpi_data():
    cache = _load_cache()
    if "cpi" in cache:
        return cache["cpi"]
    return {
        "data": [{"year": "2024", "cpi_pct": 3.6}, {"year": "2023", "cpi_pct": 3.25}, {"year": "2022", "cpi_pct": 3.15}],
        "_source": "Manual default (offline)",
        "_date": "N/A",
    }
