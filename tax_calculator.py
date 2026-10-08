"""
tax_calculator.py — Bảng tính thuế cho hộ kinh doanh & DNNVV
Cập nhật: Luật Thuế GTGT sửa đổi (Luật 48/2024/QH15, Luật 149/2025/QH15, hiệu lực 01/01/2026)
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

# CIT rates for Vietnamese enterprises under the 2025 CIT law, applied from
# the 2025 tax period. The rate is selected from the qualifying annual
# revenue; users can still pass an explicit override for planning scenarios.
CIT_RATE = 0.20  # legacy fallback for callers that do not provide revenue
CIT_EXEMPT_REVENUE_THRESHOLD_2026 = 1_000_000_000
CIT_RATES_2026 = (
    (3_000_000_000, 0.15),
    (50_000_000_000, 0.17),
    (float("inf"), 0.20),
)


def get_cit_rate_2026(revenue):
    """Return the standard 2026 CIT rate for annual revenue."""
    revenue = max(0.0, float(revenue))
    return next(rate for ceiling, rate in CIT_RATES_2026 if revenue <= ceiling)

# 2026 household-business rules. NĐ 141/2026/NĐ-CP applies the 1 billion
# threshold retrospectively from 2026-01-01; keep the former threshold only
# for the explicitly legacy-compatible calc_household_tax() API below.
HOUSEHOLD_LEGACY_VAT_EXEMPT_THRESHOLD = 500_000_000
HOUSEHOLD_VAT_EXEMPT_THRESHOLD = 1_000_000_000
HOUSEHOLD_PIT_REVENUE_METHOD_MAX = 3_000_000_000
HOUSEHOLD_E_INVOICE_REVENUE_THRESHOLD = 1_000_000_000

# NĐ 68/2026/NĐ-CP and Luật 109/2025/QH15 rates used by the 2026 UI.
# A household with revenue from above 1 billion to 3 billion can choose the
# revenue method or the income method. Above 3 billion, the income method is
# mandatory. The threshold is applied in the calling function, not in rates.
HOUSEHOLD_PIT_INCOME_RATES = (
    (3_000_000_000, 0.15),
    (50_000_000_000, 0.17),
    (float("inf"), 0.20),
)


def calc_household_tax_2026(
    revenue,
    tax_category="distribution",
    expenses=0,
    pit_method="revenue",
):
    """Calculate the 2026 household-business tax planning result.

    VAT uses the direct-on-revenue category percentage. PIT uses either the
    category rate on revenue above the 1-billion non-taxable threshold, or
    documented income after expenses at the legal rate for the revenue band.
    This remains a planning aid: source documents, activity classification,
    filing method and tax-authority guidance must be checked before filing.
    """
    revenue = max(0.0, float(revenue))
    expenses = max(0.0, float(expenses))
    rates = TT40_RATES.get(tax_category, TT40_RATES["other"])
    exempt = revenue <= HOUSEHOLD_VAT_EXEMPT_THRESHOLD
    vat_amount = 0.0 if exempt else revenue * rates["vat"]
    taxable_revenue = max(0.0, revenue - HOUSEHOLD_VAT_EXEMPT_THRESHOLD)
    taxable_income = max(0.0, revenue - expenses)
    requested_method = pit_method if pit_method in {"revenue", "income"} else "revenue"
    selected_method = requested_method
    method_forced = False

    if revenue > HOUSEHOLD_PIT_REVENUE_METHOD_MAX and selected_method == "revenue":
        selected_method = "income"
        method_forced = True

    if exempt:
        pit_rate = 0.0
        pit_amount = 0.0
        method_label = "Không phát sinh thuế do doanh thu không quá 1 tỷ đồng/năm"
    elif selected_method == "income":
        pit_rate = next(rate for ceiling, rate in HOUSEHOLD_PIT_INCOME_RATES if revenue <= ceiling)
        pit_amount = taxable_income * pit_rate
        method_label = "Theo thu nhập (doanh thu trừ chi phí hợp lệ)"
        if method_forced:
            method_label += " - bắt buộc trên 3 tỷ đồng/năm"
    else:
        pit_rate = rates["pit"]
        pit_amount = taxable_revenue * pit_rate
        method_label = "Theo tỷ lệ trên phần doanh thu vượt 1 tỷ đồng/năm"

    total_tax = vat_amount + pit_amount
    return {
        "revenue": revenue,
        "expenses": expenses,
        "category": rates["name_vi"],
        "vat_rate": rates["vat"],
        "pit_rate": pit_rate,
        "vat_amount": vat_amount,
        "pit_amount": pit_amount,
        "total_tax": total_tax,
        "net_income": revenue - expenses - total_tax,
        "taxable_revenue": taxable_revenue,
        "taxable_income": taxable_income,
        "exempt": exempt,
        "pit_method_key": selected_method,
        "method_requested": requested_method,
        "method_forced": method_forced,
        "invoice_required": revenue > HOUSEHOLD_E_INVOICE_REVENUE_THRESHOLD,
        "pit_method": method_label,
        "legal_basis": "Luật 109/2025/QH15; Nghị định 68/2026/NĐ-CP; Nghị định 141/2026/NĐ-CP; Thông tư 18/2026/TT-BTC",
        "exempt_note": "Doanh thu không quá 1 tỷ đồng/năm: không phải nộp thuế GTGT và thuế TNCN, nhưng vẫn phải thực hiện thông báo doanh thu/tài khoản theo quy định." if exempt else "",
    }


def calc_household_tax(revenue, tax_category="distribution"):
    """Legacy TT40-style calculation retained for Stable compatibility.

    New 2026 workflows must call :func:`calc_household_tax_2026` so that the
    effective-dated 1-billion threshold and method rules are applied.
    """
    rates = TT40_RATES.get(tax_category, TT40_RATES["other"])
    revenue = max(0.0, float(revenue))
    exempt = revenue <= HOUSEHOLD_LEGACY_VAT_EXEMPT_THRESHOLD

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
        "exempt_note": "Tính tương thích legacy: doanh thu ≤ 500 triệu VND/năm → miễn thuế GTGT & TNCN" if exempt else ""
    }


def calc_sme_tax(revenue, expenses, vat_rate_key="reduced_8", input_vat=None, cit_rate=None):
    """Calculate taxes for SME (deduction method, TT133)."""
    vat_info = SME_VAT_RATES.get(vat_rate_key, SME_VAT_RATES["standard"])
    vat_rate = vat_info["rate"]

    cit_rate_is_override = cit_rate is not None
    if cit_rate is None:
        cit_rate = get_cit_rate_2026(revenue)
    else:
        cit_rate = float(cit_rate)

    vat_output = revenue * vat_rate
    input_vat_is_estimated = input_vat is None
    if input_vat_is_estimated:
        # Backward-compatible estimate when users have not entered source invoice VAT yet.
        vat_input = expenses * vat_rate * 0.7
    else:
        vat_input = max(0, float(input_vat))
    vat_payable = max(0, vat_output - vat_input)

    profit = revenue - expenses
    cit_exempt = not cit_rate_is_override and revenue <= CIT_EXEMPT_REVENUE_THRESHOLD_2026
    cit = 0.0 if cit_exempt else max(0, profit * cit_rate)
    net = profit - cit

    return {
        "revenue": revenue,
        "expenses": expenses,
        "vat_rate": vat_rate,
        "vat_label": vat_info["label"],
        "vat_output": vat_output,
        "vat_input": vat_input,
        "vat_input_est": vat_input,
        "vat_input_is_estimated": input_vat_is_estimated,
        "vat_payable": vat_payable,
        "profit_before_tax": profit,
        "cit_rate": cit_rate,
        "cit_amount": cit,
        "cit_rate_is_override": cit_rate_is_override,
        "cit_exempt": cit_exempt,
        "net_profit": net
    }
