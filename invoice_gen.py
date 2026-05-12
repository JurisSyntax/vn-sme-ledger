"""
invoice_gen.py — Tạo hóa đơn theo Nghị định 123/2020/NĐ-CP
Hỗ trợ 2 loại hóa đơn:
  - Hóa đơn GTGT (01GTGT)  : Doanh nghiệp kê khai theo phương pháp khấu trừ
  - Hóa đơn bán hàng (02BH): Hộ kinh doanh / phương pháp trực tiếp
"""
from fpdf import FPDF
import datetime, os

os.makedirs("invoices", exist_ok=True)
os.makedirs("data", exist_ok=True)

def _setup_pdf():
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    try:
        pdf.add_font("Unicode", "", "C:/Windows/Fonts/arial.ttf", uni=True)
        pdf.add_font("Unicode", "B", "C:/Windows/Fonts/arialbd.ttf", uni=True)
        pdf.add_font("Unicode", "I", "C:/Windows/Fonts/ariali.ttf", uni=True)
        FONT = "Unicode"
    except:
        FONT = "Helvetica"
    return pdf, FONT


def gen_pdf_gtgt(
    inv_id, date,
    seller_name, seller_address, seller_tax, seller_bank, seller_bank_acc,
    buyer_name, buyer_address, buyer_tax,
    items, vat_rate=0.10,
    currency="VND", currency_decimals=0
):
    """
    Hóa đơn GTGT — Mẫu 01/GTGT (Nghị định 123/2020/NĐ-CP)
    Required fields (Điều 10 ND 123/2020):
      Header : Tên HĐ, Ký hiệu mẫu, Số HĐ, Ngày lập
      Seller : Tên, địa chỉ, MST, Ngân hàng
      Buyer  : Tên, địa chỉ, MST
      Table  : STT, Tên hàng, ĐVT, Số lượng, Đơn giá, Thành tiền
      Footer : Cộng tiền hàng, Thuế suất, Tiền thuế, Tổng thanh toán,
               Số tiền bằng chữ, Chữ ký người mua / người bán
    """
    pdf, FONT = _setup_pdf()
    W = 190  # usable width mm

    def fmt(n):
        if currency_decimals == 0:
            return f"{n:,.0f}"
        return f"{n:,.{currency_decimals}f}"

    # ── RED HEADER (Government stamp style) ───────────────
    pdf.set_font(FONT, "B", 9)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(W, 5, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", ln=True, align="C")
    pdf.cell(W, 5, "Độc lập - Tự do - Hạnh phúc", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # Invoice title
    pdf.set_font(FONT, "B", 14)
    pdf.cell(W, 8, "HÓA ĐƠN GIÁ TRỊ GIA TĂNG", ln=True, align="C")
    pdf.set_font(FONT, "", 9)
    pdf.cell(W, 5, f"(VAT INVOICE)  |  Ký hiệu: AA/24E  |  Số (No.): {inv_id}  |  Ngày (Date): {date}", ln=True, align="C")
    pdf.set_font(FONT, "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(W, 4, "Nghị định 123/2020/NĐ-CP — Thông tư 78/2021/TT-BTC", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # ── SELLER INFO ────────────────────────────────────────
    pdf.set_font(FONT, "B", 10)
    pdf.cell(W, 6, "THÔNG TIN NGƯỜI BÁN (SELLER)", ln=True)
    pdf.set_font(FONT, "", 9)
    pdf.cell(W, 5, f"Đơn vị bán hàng (Seller): {seller_name}", ln=True)
    pdf.cell(W, 5, f"Địa chỉ (Address): {seller_address}", ln=True)
    pdf.cell(W, 5, f"Mã số thuế (Tax Code): {seller_tax}", ln=True)
    pdf.cell(W, 5, f"Ngân hàng (Bank): {seller_bank}  |  Số TK (Acc): {seller_bank_acc}", ln=True)
    pdf.ln(2)

    # ── BUYER INFO ─────────────────────────────────────────
    pdf.set_font(FONT, "B", 10)
    pdf.cell(W, 6, "THÔNG TIN NGƯỜI MUA (BUYER)", ln=True)
    pdf.set_font(FONT, "", 9)
    pdf.cell(W, 5, f"Người mua hàng (Buyer): {buyer_name}", ln=True)
    pdf.cell(W, 5, f"Địa chỉ (Address): {buyer_address}", ln=True)
    pdf.cell(W, 5, f"Mã số thuế (Tax Code): {buyer_tax if buyer_tax else 'N/A'}", ln=True)
    pdf.ln(3)

    # ── ITEM TABLE ─────────────────────────────────────────
    pdf.set_font(FONT, "B", 9)
    pdf.set_fill_color(220, 230, 245)
    pdf.cell(8,  7, "STT", border=1, align="C", fill=True)
    pdf.cell(65, 7, "Tên hàng hóa, dịch vụ (Item)", border=1, align="C", fill=True)
    pdf.cell(15, 7, "ĐVT", border=1, align="C", fill=True)
    pdf.cell(18, 7, "Số lượng", border=1, align="C", fill=True)
    pdf.cell(30, 7, "Đơn giá", border=1, align="R", fill=True)
    pdf.cell(30, 7, "Thành tiền", border=1, align="R", fill=True)
    pdf.cell(24, 7, f"Thuế GTGT\n({int(vat_rate*100)}%)", border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font(FONT, "", 9)
    subtotal = 0
    for idx, it in enumerate(items, 1):
        line_total = it["qty"] * it["price"]
        subtotal += line_total
        vat_line = line_total * vat_rate
        pdf.cell(8,  6, str(idx), border=1, align="C")
        pdf.cell(65, 6, it["name"], border=1)
        pdf.cell(15, 6, it.get("unit", ""), border=1, align="C")
        pdf.cell(18, 6, fmt(it["qty"]), border=1, align="R")
        pdf.cell(30, 6, fmt(it["price"]), border=1, align="R")
        pdf.cell(30, 6, fmt(line_total), border=1, align="R")
        pdf.cell(24, 6, fmt(vat_line), border=1, align="R")
        pdf.ln()

    vat_total = subtotal * vat_rate
    grand_total = subtotal + vat_total

    # ── TOTALS ────────────────────────────────────────────
    pdf.ln(2)
    pdf.set_font(FONT, "", 9)
    pdf.cell(136, 6, "Cộng tiền hàng (Subtotal):", align="R")
    pdf.cell(30, 6, fmt(subtotal), align="R"); pdf.cell(24, 6, ""); pdf.ln()
    pdf.cell(136, 6, f"Thuế GTGT ({int(vat_rate*100)}%) (VAT):", align="R")
    pdf.cell(30, 6, ""); pdf.cell(24, 6, fmt(vat_total), align="R"); pdf.ln()
    pdf.set_font(FONT, "B", 10)
    pdf.cell(136, 7, "TỔNG CỘNG THANH TOÁN (Grand Total):", align="R")
    pdf.cell(30+24, 7, f"{fmt(grand_total)} {currency}", align="R"); pdf.ln()

    pdf.set_font(FONT, "I", 9)
    pdf.cell(W, 5, f"Số tiền bằng chữ (Amount in words): {_number_to_words_vn(int(grand_total))} {currency}", ln=True)

    # ── SIGNATURES ────────────────────────────────────────
    pdf.ln(8)
    pdf.set_font(FONT, "B", 9)
    pdf.cell(W/2, 5, "Người mua hàng (Buyer)", align="C")
    pdf.cell(W/2, 5, "Người bán hàng (Seller)", ln=True, align="C")
    pdf.set_font(FONT, "I", 8)
    pdf.set_text_color(130,130,130)
    pdf.cell(W/2, 4, "(Ký, ghi rõ họ tên)", align="C")
    pdf.cell(W/2, 4, "(Ký, ghi rõ họ tên)", ln=True, align="C")
    pdf.set_text_color(0,0,0)
    pdf.ln(12)
    pdf.cell(W/2, 4, "____________________________", align="C")
    pdf.cell(W/2, 4, "____________________________", ln=True, align="C")

    # ── LEGAL NOTICE ──────────────────────────────────────
    pdf.ln(5)
    pdf.set_font(FONT, "I", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(W, 4, "⚠ Đây là hóa đơn thương mại nội bộ. Để nộp thuế điện tử, xuất file XLSX và upload lên Cổng thông tin điện tử của Tổng Cục Thuế (https://hoadondientu.gdt.gov.vn). "
                         "Hóa đơn lập theo Nghị định 123/2020/NĐ-CP và Thông tư 78/2021/TT-BTC.")

    path = f"invoices/HDGTGT_{inv_id}.pdf"
    pdf.output(path)
    return path, grand_total


def gen_pdf_bh(
    inv_id, date,
    seller_name, seller_address, seller_tax, seller_bank, seller_bank_acc,
    buyer_name, buyer_address,
    items, currency="VND", currency_decimals=0
):
    """
    Hóa đơn bán hàng — Mẫu 02/BH
    Dành cho: Hộ kinh doanh, cá nhân kinh doanh,
              doanh nghiệp tính thuế GTGT theo phương pháp trực tiếp.
    Không có cột thuế GTGT riêng — giá đã bao gồm thuế (nếu có).
    """
    pdf, FONT = _setup_pdf()
    W = 190

    def fmt(n):
        if currency_decimals == 0:
            return f"{n:,.0f}"
        return f"{n:,.{currency_decimals}f}"

    pdf.set_font(FONT, "B", 9)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(W, 5, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", ln=True, align="C")
    pdf.cell(W, 5, "Độc lập - Tự do - Hạnh phúc", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.set_font(FONT, "B", 14)
    pdf.cell(W, 8, "HÓA ĐƠN BÁN HÀNG", ln=True, align="C")
    pdf.set_font(FONT, "", 9)
    pdf.cell(W, 5, f"(SALES RECEIPT / Mẫu 02/BH)  |  Số (No.): {inv_id}  |  Ngày (Date): {date}", ln=True, align="C")
    pdf.set_font(FONT, "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(W, 4, "Nghị định 123/2020/NĐ-CP — Dành cho hộ kinh doanh / phương pháp trực tiếp", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    pdf.set_font(FONT, "B", 10)
    pdf.cell(W, 6, "THÔNG TIN NGƯỜI BÁN (SELLER)", ln=True)
    pdf.set_font(FONT, "", 9)
    pdf.cell(W, 5, f"Đơn vị (Seller): {seller_name}", ln=True)
    pdf.cell(W, 5, f"Địa chỉ (Address): {seller_address}", ln=True)
    pdf.cell(W, 5, f"MST / CCCD (Tax Code / ID): {seller_tax}", ln=True)
    pdf.cell(W, 5, f"Ngân hàng (Bank): {seller_bank}  |  Số TK: {seller_bank_acc}", ln=True)
    pdf.ln(2)

    pdf.set_font(FONT, "B", 10)
    pdf.cell(W, 6, "THÔNG TIN NGƯỜI MUA (BUYER)", ln=True)
    pdf.set_font(FONT, "", 9)
    pdf.cell(W, 5, f"Người mua (Buyer): {buyer_name}", ln=True)
    pdf.cell(W, 5, f"Địa chỉ (Address): {buyer_address if buyer_address else 'N/A'}", ln=True)
    pdf.ln(3)

    # Table (no VAT column for 02/BH)
    pdf.set_font(FONT, "B", 9)
    pdf.set_fill_color(200, 235, 200)
    pdf.cell(10,  7, "STT", border=1, align="C", fill=True)
    pdf.cell(80,  7, "Tên hàng hóa, dịch vụ (Item)", border=1, align="C", fill=True)
    pdf.cell(20,  7, "ĐVT", border=1, align="C", fill=True)
    pdf.cell(20,  7, "Số lượng", border=1, align="C", fill=True)
    pdf.cell(30,  7, "Đơn giá", border=1, align="R", fill=True)
    pdf.cell(30,  7, "Thành tiền", border=1, align="R", fill=True)
    pdf.ln()

    pdf.set_font(FONT, "", 9)
    total = 0
    for idx, it in enumerate(items, 1):
        line_total = it["qty"] * it["price"]
        total += line_total
        pdf.cell(10,  6, str(idx), border=1, align="C")
        pdf.cell(80,  6, it["name"], border=1)
        pdf.cell(20,  6, it.get("unit", ""), border=1, align="C")
        pdf.cell(20,  6, fmt(it["qty"]), border=1, align="R")
        pdf.cell(30,  6, fmt(it["price"]), border=1, align="R")
        pdf.cell(30,  6, fmt(line_total), border=1, align="R")
        pdf.ln()

    pdf.ln(2)
    pdf.set_font(FONT, "B", 10)
    pdf.cell(150, 7, "TỔNG TIỀN THANH TOÁN (Total Amount):", align="R")
    pdf.cell(40,  7, f"{fmt(total)} {currency}", align="R"); pdf.ln()
    pdf.set_font(FONT, "I", 9)
    pdf.cell(W, 5, f"Số tiền bằng chữ (Amount in words): {_number_to_words_vn(int(total))} {currency}", ln=True)

    pdf.ln(8)
    pdf.set_font(FONT, "B", 9)
    pdf.cell(W/2, 5, "Người mua hàng (Buyer)", align="C")
    pdf.cell(W/2, 5, "Người bán hàng (Seller)", ln=True, align="C")
    pdf.set_font(FONT, "I", 8)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(W/2, 4, "(Ký, ghi rõ họ tên)", align="C")
    pdf.cell(W/2, 4, "(Ký, ghi rõ họ tên)", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(12)
    pdf.cell(W/2, 4, "____________________________", align="C")
    pdf.cell(W/2, 4, "____________________________", ln=True, align="C")

    pdf.ln(5)
    pdf.set_font(FONT, "I", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(W, 4, "⚠ Hóa đơn bán hàng theo Nghị định 123/2020/NĐ-CP. "
                         "Giá đã bao gồm các khoản thuế theo phương pháp trực tiếp.")

    path = f"invoices/HDBH_{inv_id}.pdf"
    pdf.output(path)
    return path, total


def _number_to_words_vn(n):
    """Basic VN number-to-words for amounts up to billions."""
    units = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    teens = ["mười", "mười một", "mười hai", "mười ba", "mười bốn",
             "mười lăm", "mười sáu", "mười bảy", "mười tám", "mười chín"]

    if n == 0: return "không đồng"
    if n >= 1_000_000_000:
        b = n // 1_000_000_000
        r = n % 1_000_000_000
        return f"{_number_to_words_vn(b)} tỷ {_number_to_words_vn(r) if r else ''}".strip()
    if n >= 1_000_000:
        m = n // 1_000_000; r = n % 1_000_000
        return f"{_number_to_words_vn(m)} triệu {_number_to_words_vn(r) if r else ''}".strip()
    if n >= 1_000:
        th = n // 1_000; r = n % 1_000
        return f"{_number_to_words_vn(th)} nghìn {_number_to_words_vn(r) if r else ''}".strip()
    if n >= 100:
        h = n // 100; r = n % 100
        rest = ""
        if r >= 20: rest = _number_to_words_vn(r)
        elif r >= 10: rest = teens[r - 10]
        elif r > 0: rest = f"lẻ {units[r]}"
        return f"{units[h]} trăm {rest}".strip()
    if n >= 20:
        t = n // 10; r = n % 10
        return f"{units[t]} mươi {units[r] if r else ''}".strip()
    if n >= 10: return teens[n - 10]
    return units[n]
