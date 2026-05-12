from docxtpl import DocxTemplate
import sqlite3, datetime, os

def gen_contract(client_id, db_path="data/ledger.db", tpl="templates/service_contract.docx"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name, tax_code, contact FROM clients WHERE id=?", (client_id,))
    cli_data = c.fetchone()
    if cli_data:
        cli = dict(zip(["name","tax_code","contact"], cli_data))
    else:
        cli = {"name": "Unknown", "tax_code": "N/A", "contact": "N/A"}
        
    c.execute("SELECT COALESCE(SUM(credit),0) FROM journal_lines JOIN journal_entries ON journal_lines.entry_id = journal_entries.id WHERE account='511' AND note LIKE ?", (f"%{cli['name']}%",))
    rev = c.fetchone()[0]
    conn.close()

    ctx = {
        "client_name": cli["name"], "tax_code": cli["tax_code"], "contact": cli["contact"],
        "date": datetime.date.today().strftime("%d/%m/%Y"), "total_rev": f"{rev:,.0f}",
        "vat_clause": "Giá chưa bao gồm VAT 10%. Xuất hóa đơn theo TT133/2016/TT-BTC.",
        "pdpa_clause": "Tuân thủ NĐ 13/2023/NĐ-CP. Dữ liệu chỉ dùng cho mục đích kế toán & báo cáo."
    }
    
    if os.path.exists(tpl):
        doc = DocxTemplate(tpl)
        doc.render(ctx)
        out = f"contracts/HOPDONG_{cli['name'].replace(' ','_')}_{datetime.date.today():%Y%m%d}.docx"
        os.makedirs("contracts", exist_ok=True)
        doc.save(out)
        return out
    else:
        return None
