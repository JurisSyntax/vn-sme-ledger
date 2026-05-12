# vas_mapper.py
VAS_RULES = {
    "Sales":          {"dr": "131", "cr": "511", "vat_cr": "3331"},
    "Purchase":       {"dr": "642", "cr": "331", "vat_dr": "133"},
    "Cash Receipt":   {"dr": "111", "cr": "131"},
    "Bank Payment":   {"dr": "331", "cr": "112"},
    "Expense":        {"dr": "642", "cr": "111"},
    "Owner Draw":     {"dr": "421", "cr": "111"}
}

def auto_vas_lines(tx_type, amount, vat_rate=0.10):
    m = VAS_RULES.get(tx_type)
    if not m: raise ValueError("Unknown type")
    base = amount / (1 + vat_rate) if tx_type in ["Sales", "Purchase"] else amount
    vat = amount - base if tx_type in ["Sales", "Purchase"] else 0.0
    if tx_type == "Sales":
        return [(m["dr"], amount, 0), (m["cr"], 0, base), (m["vat_cr"], 0, vat)]
    elif tx_type == "Purchase":
        return [(m["dr"], base, 0), (m["vat_dr"], vat, 0), (m["cr"], 0, amount)]
    return [(m["dr"], amount, 0), (m["cr"], 0, amount)]
