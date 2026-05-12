import json, os, sys

DEFAULT_SETTINGS = {
    "language": "vi",
    "currency": "VND",
    "currency_decimals": 0,
    "company_name": "",
    "company_address": "",
    "company_province": "",
    "company_phone": "",
    "company_email": "",
    "company_tax_code": "",
    "company_legal_rep": "",
    "company_legal_rep_title": "Giám đốc",
    "bank_name": "Vietcombank",
    "bank_account": "",
    "invoice_type": "01GTGT",
    "invoice_start": 1,
    "vat_rate": 0.08,
    "cit_rate": 0.20,
}

NAPAS_BANKS = {
    "Vietcombank": "970436",
    "Vietinbank": "970415",
    "BIDV": "970418",
    "Agribank": "970405",
    "MBBank": "970422",
    "Techcombank": "970407",
    "ACB": "970416",
    "VPBank": "970432",
    "TPBank": "970423",
    "Sacombank": "970403",
    "HDBank": "970437",
    "VIB": "970441",
    "SHB": "970443",
}

LABELS = {
    "vi": {
        "tab_ledger": "Chứng từ (Ledger)",
        "tab_directories": "Danh mục (Directories)",
        "tab_invoices": "Hóa đơn (Invoices)",
        "tab_reports": "Báo cáo (Reports)",
        "tab_history": "Lịch sử GD (History)",
        "tab_analytics": "Phân tích (Analytics)",
        "tab_settings": "Cài đặt (Settings)",
        "tab_tax": "🧮 Tính thuế",
        "tab_manual": "📘 Hướng dẫn",
        "tab_mst_lookup": "🔍 Tra cứu MST",
        "niche_label": "Ngành nghề:",
        "date": "Ngày (Date):",
        "ref": "Số CT (Ref):",
        "note": "Diễn giải (Note):",
        "account": "Tài khoản (Account):",
        "debit": "Nợ (Debit):",
        "credit": "Có (Credit):",
        "post_btn": "Lưu chứng từ (Post Voucher)",
        "update_btn": "Cập nhật (Update)",
        "clear_btn": "Xóa mẫu (Clear)",
        "delete_btn": "Xóa (Delete)",
        "add_btn": "Thêm (Add)",
        "refresh_btn": "Làm mới (Refresh)",
        "edit_hint": "💡 Nhấp đúp để sửa (Double-click to Edit)",
        "client": "Khách hàng:",
        "gen_invoice_btn": "Xuất hóa đơn PDF",
        "add_line_btn": "Thêm dòng (Add Line)",
        "remove_line_btn": "Xóa dòng (Remove)",
        "running_balance": "Số dư (Balance)",
        "settings_lang": "Ngôn ngữ (Language):",
        "settings_currency": "Đơn vị tiền (Currency):",
        "settings_company": "Tên công ty:",
        "settings_address": "Địa chỉ DN:",
        "settings_province": "Tỉnh/Thành phố:",
        "settings_phone": "Điện thoại:",
        "settings_email": "Email:",
        "settings_tax": "Mã số thuế:",
        "settings_bank": "Ngân hàng:",
        "settings_bank_acc": "Số tài khoản:",
        "settings_inv_type": "Loại hóa đơn:",
        "settings_save": "Lưu cài đặt (Save)",
        "dashboard_title": "VN SME Ledger Suit (Beta v1)",
        "dashboard_subtitle": "HỆ THỐNG QUẢN TRỊ DOANH NGHIỆP",
        "recent_activities": "🕒 HOẠT ĐỘNG",
        "quick_access": "🚀 TRUY CẬP NHANH",
        "smart_reminders": "🔔 NHẮC VIỆC THÔNG MINH",
        "support_footer": "Hỗ trợ: 1900-AI-SME | Made in 2026",
    },
    "en": {
        "tab_ledger": "Ledger",
        "tab_directories": "Directories",
        "tab_invoices": "Invoices",
        "tab_reports": "Reports",
        "tab_history": "Transaction History",
        "tab_analytics": "Analytics",
        "tab_settings": "Settings",
        "tab_tax": "🧮 Tax Calculator",
        "tab_manual": "📘 User Manual",
        "tab_mst_lookup": "🔍 Tax ID Lookup",
        "niche_label": "Business Niche:",
        "date": "Date (YYYY-MM-DD):",
        "ref": "Ref No.:",
        "note": "Description:",
        "account": "Account Code:",
        "debit": "Debit:",
        "credit": "Credit:",
        "post_btn": "Post Voucher",
        "update_btn": "Update",
        "clear_btn": "Clear Form",
        "delete_btn": "Delete",
        "add_btn": "Add",
        "refresh_btn": "Refresh",
        "edit_hint": "💡 Double-click a row to Edit",
        "client": "Client:",
        "gen_invoice_btn": "Generate Invoice PDF",
        "add_line_btn": "Add Item",
        "remove_line_btn": "Remove",
        "running_balance": "Running Balance",
        "settings_lang": "Language:",
        "settings_currency": "Currency:",
        "settings_company": "Company Name:",
        "settings_address": "Business Address:",
        "settings_province": "Province / City:",
        "settings_phone": "Phone:",
        "settings_email": "Email:",
        "settings_tax": "Tax Code:",
        "settings_bank": "Bank Name:",
        "settings_bank_acc": "Bank Account No:",
        "settings_inv_type": "Invoice Type:",
        "settings_save": "Save Settings",
        "dashboard_title": "VN SME Ledger Suit (Beta v1)",
        "dashboard_subtitle": "ENTERPRISE RESOURCE PLANNING",
        "recent_activities": "🕒 ACTIVITIES",
        "quick_access": "🚀 QUICK ACCESS",
        "smart_reminders": "🔔 SMART REMINDERS",
        "support_footer": "Support: 1900-AI-SME | Made in 2026",
    }
}

def _settings_path():
    return "data/settings.json"

def load_settings():
    p = _settings_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                s = json.load(f)
                merged = DEFAULT_SETTINGS.copy()
                merged.update(s)
                return merged
        except: pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    os.makedirs("data", exist_ok=True)
    with open(_settings_path(), "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def get_labels(settings):
    lang = settings.get("language", "vi")
    base = LABELS["vi"].copy()
    if lang in LABELS and lang != "vi":
        base.update(LABELS[lang])
    
    # Safe dictionary wrapper to prevent KeyError crashes
    class SafeDict(dict):
        def __missing__(self, key):
            print(f"WARNING: Missing language key '{key}'")
            return key
            
    return SafeDict(base)

def fmt_currency(amount, settings):
    dec = settings.get("currency_decimals", 0)
    sym = settings.get("currency", "VND")
    if dec == 0:
        return f"{amount:,.0f} {sym}"
    return f"{amount:,.{dec}f} {sym}"
