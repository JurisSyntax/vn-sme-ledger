"""Offline business lookup placeholder.

Automatic MST lookup is disabled in offline-only mode. Users can paste verified
business data into the customer directory manually.
"""


def lookup_business(tax_code):
    return {
        "tax_code": str(tax_code or "").strip(),
        "name": "",
        "address": "",
        "source": "offline-manual",
        "error": "Offline-only: tự nhập hoặc dán thông tin doanh nghiệp đã kiểm chứng.",
    }

