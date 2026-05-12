"""
tax_calculator.py — Bảng tính thuế cho hộ kinh doanh & DNNVV
Cập nhật: Luật Thuế GTGT sửa đổi (Luật 48/2024/QH15, hiệu lực 01/01/2026)
          NQ 204/2025/QH15 + NĐ 174/2025/NĐ-CP: giảm VAT 10%→8% (01/07/2025–31/12/2026)
          TT 40/2021/TT-BTC: tỷ lệ thuế hộ kinh doanh
"""

# TT40/2021 Phụ lục I — Tỷ lệ % thuế trên doanh thu
TT40_RATES = {
    "distribution": {
        "name_vi": "Phân phối, cung cấp hàng hóa",
        "name_en": "Distribution / Goods supply",
        "vat": 0.01,
        "pit": 0.005,
        "examples": "Bán buôn, bán lẻ, photocopy, đại lý"
    },
    "services": {
        "name_vi": "Dịch vụ, xây dựng không bao thầu NVL",
        "name_en": "Services / Construction (no materials)",
        "vat": 0.05,
        "pit": 0.02,
        "examples": "Tư vấn, IT, pháp lý, kế toán, nhà hàng, café"
    },
    "manufacturing": {
        "name_vi": "Sản xuất, vận tải, XD có bao thầu NVL",
        "name_en": "Manufacturing / Transport / Construction (with materials)",
        "vat": 0.03,
        "pit": 0.015,
        "examples": "Sản xuất, in ấn, vận chuyển, xây dựng"
    },
    "other": {
        "name_vi": "Hoạt động kinh doanh khác",
        "name_en": "Other business activities",
        "vat": 0.02,
        "pit": 0.01,
        "examples": "Cho thuê tài sản, BĐS, freelance"
    }
}

# VAT rates for SME (deduction method) — updated for 2026
SME_VAT_RATES = {
    "standard":   {"rate": 0.10, "label": "Thuế suất tiêu chuẩn (Standard 10%)"},
    "reduced_8":  {"rate": 0.08, "label": "Giảm thuế NQ204/2025 (Reduced 8%, valid 01/07/2025–31/12/2026)"},
    "reduced_5":  {"rate": 0.05, "label": "Thuế suất 5% (nông sản, y tế, giáo dục...)"},
    "zero":       {"rate": 0.00, "label": "Thuế suất 0% (xuất khẩu)"},
}

# CIT rate for SMEs (TT133)
CIT_RATE = 0.20

# New 2026 rule: household/individual revenue ≤ 500M VND/year → VAT exempt
HOUSEHOLD_VAT_EXEMPT_THRESHOLD = 500_000_000


def calc_household_tax(revenue, tax_category="distribution"):
    """Calculate taxes for household businesses (TT40 method)."""
    rates = TT40_RATES.get(tax_category, TT40_RATES["other"])
    exempt = revenue <= HOUSEHOLD_VAT_EXEMPT_THRESHOLD

    vat_amount = 0 if exempt else revenue * rates["vat"]
    pit_amount = 0 if exempt else revenue * rates["pit"]
    total_tax = vat_amount + pit_amount

    return {
        "revenue": revenue,
        "category": rates["name_vi"],
        "vat_rate": rates["vat"],
        "pit_rate": rates["pit"],
        "vat_amount": vat_amount,
        "pit_amount": pit_amount,
        "total_tax": total_tax,
        "net_income": revenue - total_tax,
        "exempt": exempt,
        "exempt_note": "Doanh thu ≤ 500 triệu VND/năm → miễn thuế GTGT & TNCN (Luật 48/2024/QH15)" if exempt else ""
    }


def calc_sme_tax(revenue, expenses, vat_rate_key="reduced_8"):
    """Calculate taxes for SME (deduction method, TT133)."""
    vat_info = SME_VAT_RATES.get(vat_rate_key, SME_VAT_RATES["standard"])
    vat_rate = vat_info["rate"]

    vat_output = revenue * vat_rate
    # Assume input VAT is roughly proportional to expenses
    vat_input = expenses * vat_rate * 0.7  # conservative estimate
    vat_payable = max(0, vat_output - vat_input)

    profit = revenue - expenses
    cit = max(0, profit * CIT_RATE)
    net = profit - cit

    return {
        "revenue": revenue,
        "expenses": expenses,
        "vat_rate": vat_rate,
        "vat_label": vat_info["label"],
        "vat_output": vat_output,
        "vat_input_est": vat_input,
        "vat_payable": vat_payable,
        "profit_before_tax": profit,
        "cit_rate": CIT_RATE,
        "cit_amount": cit,
        "net_profit": net
    }
