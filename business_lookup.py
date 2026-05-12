"""
business_lookup.py — Tra cứu thông tin doanh nghiệp qua masothue.com
"""
import requests

def lookup_tax_code(tax_code):
    """Look up a Vietnamese business by tax code via masothue.com."""
    try:
        url = f"https://api.vietqr.io/v2/business/{tax_code}"
        r = requests.get(url, timeout=8, headers={"Accept": "application/json"})
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == "00" and data.get("data"):
                d = data["data"]
                return {
                    "found": True,
                    "name": d.get("name", ""),
                    "short_name": d.get("shortName", ""),
                    "address": d.get("address", ""),
                    "tax_code": tax_code,
                    "source": "VietQR / masothue"
                }
    except: pass

    # Fallback: try masothue.com directly (scraping)
    try:
        url = f"https://masothue.com/{tax_code}"
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code == 200 and tax_code in r.text:
            return {
                "found": True,
                "name": "(See masothue.com for details)",
                "address": "",
                "tax_code": tax_code,
                "source": f"masothue.com/{tax_code}",
                "url": url
            }
    except: pass

    return {"found": False, "tax_code": tax_code, "error": "Không tìm thấy (Not found)"}
