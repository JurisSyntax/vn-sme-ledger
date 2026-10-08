"""Disposable-volume accounting workflow check for release QA.

Runs exclusively in a temporary directory. It is an engineering stress check,
not a certification of legal or tax compliance.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

import db
from core.cash_forecast import build_cash_forecast
from core.financial_analytics_pro import compute_executive_dashboard_metrics
from core.financial_statements import generate_b01_dnn, generate_b02_dnn, generate_b03_dnn
from core.inventory import post_stock_in
from core.payroll import calculate_monthly_payroll


def run_stress_workload() -> dict:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="vn_sme_accounting_stress_") as temp_dir:
        root = Path(temp_dir)
        conn = db.init_db(str(root / "ledger.db"))
        try:
            customer_ids = [
                db.add_client(
                    conn,
                    f"Khách hàng kiểm thử {index:02d}",
                    f"010{index:07d}",
                    f"090000{index:04d}",
                    "Hà Nội",
                )
                for index in range(1, 21)
            ]
            supplier_id = db.add_supplier(
                conn,
                "Nhà cung cấp kiểm thử",
                "0109999999",
                "Hà Nội",
                payment_terms_days=30,
            )
            db.add_inventory(conn, "Hàng hóa kiểm thử", "cái", "cái", 1, 0, 0, 25000, "STRESS-LOT")
            item_id = int(db.get_inventory(conn).iloc[0]["id"])
            post_stock_in(conn, item_id, 1000, 8000, date="2026-01-02", note="Lô hàng test")
            db.post_entry(
                conn,
                "2026-01-02",
                "STRESS-PURCHASE-OPENING",
                "Ghi nhận giá trị lô hàng kiểm thử",
                [("156", 8_000_000, 0), ("331", 0, 8_000_000)],
                "Purchase",
                supplier_id=supplier_id,
            )

            invoice_count = 0
            receipt_count = 0
            for month in range(1, 9):
                day = f"2026-{month:02d}-08"
                for _ in range(30):
                    invoice_count += 1
                    client_id = customer_ids[(invoice_count - 1) % len(customer_ids)]
                    inv_number = f"STRESS-SALE-{invoice_count:04d}"
                    result = db.save_invoice(
                        conn,
                        inv_number,
                        "01GTGT",
                        client_id,
                        day,
                        json.dumps([{
                            "item_id": item_id,
                            "name": "Hàng hóa kiểm thử",
                            "qty": 2,
                            "price": 25_000,
                        }], ensure_ascii=False),
                        50_000,
                        4_000,
                        54_000,
                        str(root / f"{inv_number}.pdf"),
                        auto_post=True,
                    )
                    assert result["inventory_cogs"] == 16_000
                    invoice_id = int(conn.execute(
                        "SELECT id FROM invoices WHERE inv_number=?", (inv_number,)
                    ).fetchone()[0])
                    receipt_count += 1
                    payment_id = db.post_entry(
                        conn,
                        day,
                        f"STRESS-RECEIPT-{receipt_count:04d}",
                        "Khách thanh toán một phần",
                        [("111", 45_000, 0), ("131", 0, 45_000)],
                        "Cash Receipt",
                        client_id=client_id,
                    )
                    db.allocate_settlement(conn, payment_id, invoice_id, 45_000)

                for index in range(10):
                    db.post_entry(
                        conn,
                        day,
                        f"STRESS-RETAIL-{month:02d}-{index:02d}",
                        "Bán lẻ thu tiền",
                        [("111", 400_000, 0), ("511", 0, 400_000)],
                        "Cash Sale",
                    )
                for index in range(4):
                    db.post_entry(
                        conn,
                        day,
                        f"STRESS-EXPENSE-{month:02d}-{index:02d}",
                        "Chi phí vận hành",
                        [("642", 250_000, 0), ("111", 0, 250_000)],
                        "Expense",
                    )

            months = [f"{month:02d}/2026" for month in range(1, 9)]
            employees = [
                {
                    "code": f"EMP-{index:03d}",
                    "name": f"Nhân viên {index:03d}",
                    "salary": 18_000_000 + (index % 5) * 1_000_000,
                    "allowance": 500_000,
                    "dependents": index % 3,
                }
                for index in range(1, 65)
            ]
            payroll_rows = 0
            for month_index, month in enumerate(months, start=1):
                timesheets = [
                    {
                        "month": month,
                        "code": employee["code"],
                        "work_days": 26,
                        "ot_hours": 8,
                        "ot_weekend_hours": 4,
                        "ot_holiday_hours": 0,
                        "ot_approved": True,
                        "advance": 500_000,
                    }
                    for employee in employees
                ]
                rows = calculate_monthly_payroll(
                    employees,
                    timesheets,
                    month,
                    conn=conn,
                    effective_date=f"2026-{month_index:02d}-28",
                )
                assert len(rows) == len(employees)
                assert all(row["net"] > 0 and row["ot_pay"] > 0 for row in rows)
                payroll_rows += len(rows)

            integrity = db.validate_ledger_integrity(conn)
            assert integrity["ok"] is True, integrity.get("issues", [])[:5]
            balance_sheet = generate_b01_dnn(conn, as_of_date="2026-08-31")
            income_statement = generate_b02_dnn(
                conn, from_date="2026-01-01", to_date="2026-08-31"
            )
            cash_flow = generate_b03_dnn(
                conn, from_date="2026-01-01", to_date="2026-08-31"
            )
            forecast = build_cash_forecast(conn, as_of="2026-09-29", horizon_days=14)
            executive = compute_executive_dashboard_metrics(conn, as_of_date="2026-08-31")

            assert invoice_count == 240
            assert receipt_count == 240
            assert balance_sheet["is_balanced"] is True, balance_sheet["balance_diff"]
            assert income_statement["revenue"] == 44_000_000
            assert income_statement["profit_before_tax"] == 32_160_000
            assert cash_flow["net_cash_flow"] != 0
            assert forecast["summary"]["open_invoice_count"] == invoice_count
            assert executive["financial_score"] >= 0
            stock_out_count, stock_out_qty = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(qty), 0) FROM inventory_log WHERE type='OUT'"
            ).fetchone()
            assert int(stock_out_count) == invoice_count
            assert float(stock_out_qty) == 480
            assert int(conn.execute("SELECT COUNT(*) FROM settlement_allocations").fetchone()[0]) == receipt_count

            return {
                "status": "passed",
                "isolated_temp_database": True,
                "customers": len(customer_ids),
                "suppliers": 1,
                "invoices": invoice_count,
                "partial_receipts": receipt_count,
                "inventory_movement_rows_out": int(stock_out_count),
                "inventory_units_out": float(stock_out_qty),
                "cash_sales": 80,
                "operating_expenses": 32,
                "journal_entries": int(conn.execute("SELECT COUNT(*) FROM journal_entries").fetchone()[0]),
                "journal_lines": int(conn.execute("SELECT COUNT(*) FROM journal_lines").fetchone()[0]),
                "payroll_calculations": payroll_rows,
                "ledger_integrity": integrity["ok"],
                "balance_sheet_balanced": balance_sheet["is_balanced"],
                "revenue_vnd": income_statement["revenue"],
                "profit_before_tax_vnd": income_statement["profit_before_tax"],
                "cash_forecast_open_invoices": forecast["summary"]["open_invoice_count"],
                "executive_grade": executive["financial_grade"],
                "elapsed_seconds": round(time.perf_counter() - started, 2),
            }
        finally:
            conn.close()


if __name__ == "__main__":
    print(json.dumps(run_stress_workload(), ensure_ascii=False, indent=2))
