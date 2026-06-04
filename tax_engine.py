import json, os

CACHE = "data/tax_cache.json"

def load_tax():
    if os.path.exists(CACHE):
        with open(CACHE) as f: return json.load(f)
    return {"VAT": 0.10, "CIT": 0.20, "PIT": None, "updated": "manual"}

def update_tax_online():
    return load_tax()
