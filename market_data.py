"""
market_data.py — Exchange rates & CPI data
- Frankfurter API (free, no key) for exchange rates
- GSO Vietnam / World Bank for CPI
- Manual fallback for offline use
"""
import requests, json, os
from datetime import datetime

CACHE_PATH = "data/market_cache.json"

def _load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r") as f: return json.load(f)
        except: pass
    return {}

def _save_cache(data):
    os.makedirs("data", exist_ok=True)
    with open(CACHE_PATH, "w") as f: json.dump(data, f, indent=2)


def get_exchange_rates(base="VND"):
    """Fetch exchange rates from Frankfurter (ECB data, no API key)."""
    cache = _load_cache()
    try:
        # Frankfurter uses EUR as base, so we convert
        r = requests.get("https://api.frankfurter.dev/v1/latest?base=USD&symbols=VND,EUR,JPY,CNY,KRW,SGD",
                         timeout=5)
        if r.status_code == 200:
            data = r.json()
            rates = data.get("rates", {})
            rates["USD"] = 1.0
            rates["_source"] = "Frankfurter (ECB)"
            rates["_date"] = data.get("date", str(datetime.now().date()))
            cache["exchange_rates"] = rates
            _save_cache(cache)
            return rates
    except: pass

    # Fallback to cache
    if "exchange_rates" in cache:
        cache["exchange_rates"]["_source"] = "Cached (offline)"
        return cache["exchange_rates"]

    # Hardcoded fallback
    return {
        "USD": 1.0, "VND": 25400, "EUR": 0.92, "JPY": 157, "CNY": 7.24,
        "_source": "Manual default", "_date": "N/A"
    }


def get_cpi_data():
    """Fetch VN CPI from World Bank Open Data API (no key needed)."""
    cache = _load_cache()
    try:
        # World Bank: FP.CPI.TOTL.ZG = CPI inflation (annual %)
        url = "https://api.worldbank.org/v2/country/VNM/indicator/FP.CPI.TOTL.ZG?format=json&per_page=5&date=2020:2025"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            raw = r.json()
            if len(raw) > 1 and raw[1]:
                entries = [{"year": e["date"], "cpi_pct": e["value"]} for e in raw[1] if e["value"]]
                cache["cpi"] = {"data": entries, "_source": "World Bank Open Data", "_date": str(datetime.now().date())}
                _save_cache(cache)
                return cache["cpi"]
    except: pass

    if "cpi" in cache: return cache["cpi"]

    return {
        "data": [{"year":"2024","cpi_pct":3.6},{"year":"2023","cpi_pct":3.25},{"year":"2022","cpi_pct":3.15}],
        "_source": "GSO Vietnam (manual)", "_date": "N/A"
    }
