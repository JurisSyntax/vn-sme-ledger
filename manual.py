"""
manual.py — In-app help text for each section.
"""

MANUAL = {
    "overview": {
        "title": "📘 Tổng quan / Overview",
        "content": """
VN SME Ledger là phần mềm kế toán offline dành cho doanh nghiệp nhỏ và hộ kinh doanh tại Việt Nam.

Phần mềm tuân thủ các quy định sau:
• Thông tư 133/2016/TT-BTC — Hệ thống tài khoản kế toán doanh nghiệp nhỏ
• Nghị định 123/2020/NĐ-CP — Quy định về hóa đơn, chứng từ
• Thông tư 78/2021/TT-BTC — Hướng dẫn hóa đơn điện tử
• Thông tư 40/2021/TT-BTC — Tỷ lệ thuế hộ kinh doanh
• Luật 48/2024/QH15 — Luật Thuế GTGT sửa đổi (hiệu lực 01/01/2026)
• NQ 204/2025/QH15 — Giảm thuế GTGT 10%→8% (01/07/2025–31/12/2026)
• QĐ 36/2025/QĐ-TTg — Hệ thống ngành kinh tế Việt Nam (VSIC 2025)

⚠ Lưu ý quan trọng:
Hóa đơn xuất từ phần mềm này là hóa đơn thương mại nội bộ.
Để nộp thuế điện tử hoặc phát hành hóa đơn điện tử hợp pháp,
doanh nghiệp cần sử dụng dịch vụ hóa đơn điện tử được Tổng cục Thuế phê duyệt
(ví dụ: MISA, E-Invoice, MeInvoice...) và nộp qua dichvucong.gdt.gov.vn.
"""
    },
    "ledger": {
        "title": "📒 Chứng từ / Ledger",
        "content": """
Tab Chứng từ hoạt động theo nguyên tắc kế toán kép (Double-entry):
• Mỗi giao dịch phải có tổng Nợ (Debit) = tổng Có (Credit)
• Hệ thống tự động kiểm tra cân đối trước khi lưu

Cách sử dụng:
1. Nhập ngày, số chứng từ, diễn giải
2. Dùng "Auto VAS" để tự động hạch toán theo loại giao dịch
   → Hoặc thêm từng dòng hạch toán thủ công (TK, Nợ, Có)
3. Nhấn "Lưu chứng từ" để ghi sổ
4. Nhấp đúp (double-click) vào bút toán đã lưu để sửa

Áp dụng: TT133/2016/TT-BTC — Hệ thống tài khoản chuẩn
"""
    },
    "directories": {
        "title": "📂 Danh mục / Directories",
        "content": """
Quản lý các danh mục cơ sở dữ liệu:

• Hệ thống Tài khoản (COA): Mã TK theo TT133, có thể thêm tài khoản phụ
• Khách hàng/NCC: Tên, MST, liên hệ, đơn vị tiền tệ riêng
• Kho/Vật tư: Quản lý hàng tồn kho đơn giản
• Tài sản cố định: Theo dõi nguyên giá và khấu hao
• Ngành nghề (VSIC): Mã ngành kinh doanh theo QĐ 36/2025/QĐ-TTg

Tất cả danh mục đều hỗ trợ Thêm / Sửa (nhấp đúp) / Xóa.
"""
    },
    "invoices": {
        "title": "🧾 Hóa đơn / Invoices",
        "content": """
Hỗ trợ 2 loại hóa đơn theo Nghị định 123/2020/NĐ-CP:

1. Hóa đơn GTGT (Mẫu 01/GTGT):
   → Dành cho DN kê khai thuế theo phương pháp khấu trừ
   → Có cột thuế GTGT riêng (hiện tại áp dụng 8% theo NQ204/2025)
   → Bắt buộc ghi: MST người bán, MST người mua, thuế suất

2. Hóa đơn bán hàng (Mẫu 02/BH):
   → Dành cho hộ kinh doanh / phương pháp trực tiếp
   → Không có cột thuế riêng (giá đã bao gồm thuế)

⚠ Đây là hóa đơn thương mại. Để phát hành hóa đơn điện tử hợp pháp,
cần sử dụng dịch vụ e-invoice được cấp phép và nộp qua GDT.
"""
    },
    "tax_calc": {
        "title": "🧮 Tính thuế / Tax Calculator",
        "content": """
Hai chế độ tính thuế:

A. Hộ kinh doanh (TT40/2021):
   Thuế = Doanh thu × Tỷ lệ %
   • Phân phối hàng hóa:    VAT 1%  + TNCN 0.5%
   • Dịch vụ:               VAT 5%  + TNCN 2%
   • Sản xuất, vận tải:     VAT 3%  + TNCN 1.5%
   • Hoạt động khác:        VAT 2%  + TNCN 1%

   ⚡ MỚI (Luật 48/2024/QH15, hiệu lực 01/01/2026):
   Doanh thu ≤ 500 triệu VND/năm → MIỄN thuế GTGT & TNCN
   (ngưỡng cũ: 100 triệu VND)

B. Doanh nghiệp nhỏ (phương pháp khấu trừ):
   VAT phải nộp = VAT đầu ra - VAT đầu vào
   CIT (Thuế TNDN) = 20% × Lợi nhuận trước thuế

   ⚡ NQ204/2025: Giảm VAT 10%→8% cho nhiều hàng hóa/dịch vụ
   (hiệu lực 01/07/2025 — 31/12/2026)
"""
    },
    "reports": {
        "title": "📊 Báo cáo / Reports",
        "content": """
Báo cáo tài chính đơn giản theo TT133:

• B02-DNN: Báo cáo kết quả hoạt động kinh doanh (Income Statement)
  → Tự động tổng hợp từ dữ liệu sổ cái
  → Doanh thu (511) - Chi phí (642) = Lợi nhuận

Lưu ý: Các báo cáo phức tạp hơn (B01a-DNN, B03-DNN) cần
được lập bởi kế toán viên hoặc phần mềm chuyên dụng.
"""
    },
    "legal_docs": {
        "title": "📜 Văn bản & Biểu mẫu / Legal Templates",
        "content": """
Kho lưu trữ offline các biểu mẫu chuẩn 2026:
• Tờ khai thuế GTGT, TNDN, TNCN theo Thông tư 80/2021
• Báo cáo tài chính chuẩn TT133 (B01, B02, B09)
• Hệ thống chứng từ: Phiếu thu, chi, nhập, xuất kho
• Bảng tính quản trị: Doanh thu, Công nợ, Lương

Tính năng:
1. Tải & Mở hướng dẫn: Tạo file chỉ dẫn cách tải từ nguồn uy tín (gdt.gov.vn).
2. Tải lên (Upload): Người dùng chọn file mẫu đã tải để lưu trữ trực tiếp vào phần mềm.
3. Kiểm tra hiệu lực: Xem văn bản còn giá trị pháp lý hay không.
"""
    }
}

def get_manual_text():
    """Return full manual as formatted string."""
    parts = []
    for key in ["overview","ledger","directories","invoices","tax_calc","reports","legal_docs"]:
        s = MANUAL[key]
        parts.append(f"{s['title']}\n{'─'*50}\n{s['content'].strip()}\n")
    
    parts.append("\n" + "─"*50 + "\n")
    parts.append("Author Credit: https://github.com/JurisSyntax\n")
    return "\n\n".join(parts)
