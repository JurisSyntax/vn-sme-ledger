"""
tax_engine.py — Tax rate loader for analytics and reports.

Reads from settings (config.py) first, then from cache, then falls back to
statutory defaults.  Never touches the network.
"""

import json
import os

import config

CACHE = "data/tax_cache.json"


def load_tax(settings=None) -> dict:
    """Load current tax rates.

    Priority order:
    1. Explicit settings dict or user settings (config.load_settings)
    2. Cached file (data/tax_cache.json) — for custom overrides
    3. Statutory defaults
    """
    if settings is None:
        settings = config.load_settings()
    vat = float(settings.get("vat_rate", 0.08))
    cit = float(settings.get("cit_rate", 0.20))

    # Allow cache overrides for PIT or custom fields
    pit = None
    source = "settings"
    if os.path.exists(CACHE):
        try:
            with open(CACHE, encoding="utf-8") as f:
                cached = json.load(f)
            pit = cached.get("PIT")
            source = cached.get("updated", "cache")
        except Exception:
            pass

    return {"VAT": vat, "CIT": cit, "PIT": pit, "updated": source}


def save_tax_cache(rates: dict) -> None:
    """Persist custom tax rate overrides to the cache file."""
    os.makedirs("data", exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)


def update_tax_online():
    """Placeholder — returns current rates (no network call)."""
    return load_tax()
