import json, requests, os
from bs4 import BeautifulSoup

CACHE = "data/tax_cache.json"

def load_tax():
    if os.path.exists(CACHE):
        with open(CACHE) as f: return json.load(f)
    return {"VAT": 0.10, "CIT": 0.20, "PIT": None, "updated": "manual"}

def update_tax_online():
    try:
        # Example: scrape MOF/GDT public rate table (adjust URL/selectors as needed)
        r = requests.get("https://www.gdt.gov.vn/wps/portal/english/taxrates", timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        # Parse logic here → extract VAT/CIT/PIT → save to dict
        rates = {"VAT": 0.10, "CIT": 0.20, "updated": "auto"}
        os.makedirs("data", exist_ok=True)
        with open(CACHE, "w") as f: json.dump(rates, f)
        return rates
    except: return load_tax()  # fallback offline
