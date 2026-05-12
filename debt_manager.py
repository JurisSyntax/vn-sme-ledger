import tkinter as tk
from tkinter import ttk, messagebox
import db, utils

def build_debt_tab(app, parent, conn, lbl):
    """
    Builds the Debt Management tab UI.
    """
    main_f = ttk.Frame(parent)
    main_f.pack(fill="both", expand=True, padx=10, pady=10)
    
    # --- HEADER ---
    hdr = ttk.Frame(main_f)
    hdr.pack(fill="x", pady=(0, 10))
    tk.Label(hdr, text="💸 QUẢN LÝ CÔNG NỢ CHI TIẾT (DEBT MANAGEMENT)", font=("Segoe UI", 12, "bold"), fg="#1565C0").pack(side="left")
    
    # --- PANED VIEW (Left: Summary, Right: Details) ---
    paned = ttk.PanedWindow(main_f, orient="horizontal")
    paned.pack(fill="both", expand=True)
    
    # Left Frame: Summary Table
    left_f = ttk.LabelFrame(paned, text="📋 Tổng hợp Công nợ")
    paned.add(left_f, weight=1)
    
    cols = ("id", "name", "receivable", "payable")
    tree_sum = ttk.Treeview(left_f, columns=cols, show="headings", height=15)
    tree_sum.heading("id", text="ID"); tree_sum.column("id", width=40)
    tree_sum.heading("name", text="Tên Đối tác (Client/Vendor)"); tree_sum.column("name", width=250)
    tree_sum.heading("receivable", text="Phải thu (131)"); tree_sum.column("receivable", width=120, anchor="e")
    tree_sum.heading("payable", text="Phải trả (331)"); tree_sum.column("payable", width=120, anchor="e")
    
    sb_sum = ttk.Scrollbar(left_f, orient="vertical", command=tree_sum.yview)
    tree_sum.configure(yscrollcommand=sb_sum.set)
    tree_sum.pack(fill="both", expand=True, side="left")
    sb_sum.pack(fill="y", side="right")
    
    # Right Frame: Detailed View
    right_f = ttk.LabelFrame(paned, text="🔍 Chi tiết giao dịch")
    paned.add(right_f, weight=2)
    
    cols_det = ("date", "ref", "note", "acc", "dr", "cr")
    tree_det = ttk.Treeview(right_f, columns=cols_det, show="headings")
    tree_det.heading("date", text="Ngày"); tree_det.column("date", width=80)
    tree_det.heading("ref", text="Số CT"); tree_det.column("ref", width=100)
    tree_det.heading("note", text="Diễn giải"); tree_det.column("note", width=200)
    tree_det.heading("acc", text="TK"); tree_det.column("acc", width=60)
    tree_det.heading("dr", text="Phát sinh Nợ"); tree_det.column("dr", width=100, anchor="e")
    tree_det.heading("cr", text="Phát sinh Có"); tree_det.column("cr", width=100, anchor="e")
    
    sb_det = ttk.Scrollbar(right_f, orient="vertical", command=tree_det.yview)
    tree_det.configure(yscrollcommand=sb_det.set)
    tree_det.pack(fill="both", expand=True, side="left")
    sb_det.pack(fill="y", side="right")

    # --- ACTIONS ---
    btn_f = ttk.Frame(main_f)
    btn_f.pack(fill="x", pady=10)
    
    def refresh_summary():
        for i in tree_sum.get_children(): tree_sum.delete(i)
        df = db.get_debt_summary(conn)
        if df.empty: return
        for _, r in df.iterrows():
            tree_sum.insert("", "end", values=(
                r['client_id'], r['client_name'],
                f"{r['receivable']:,.0f}" if r['receivable'] != 0 else "-",
                f"{r['payable']:,.0f}" if r['payable'] != 0 else "-"
            ))

    def on_client_select(event):
        sel = tree_sum.selection()
        if not sel: return
        cid = tree_sum.item(sel[0])['values'][0]
        name = tree_sum.item(sel[0])['values'][1]
        right_f.config(text=f"🔍 Chi tiết giao dịch: {name}")
        
        for i in tree_det.get_children(): tree_det.delete(i)
        df = db.get_client_debt_details(conn, cid)
        for _, r in df.iterrows():
            tree_det.insert("", "end", values=(
                r['date'], r['ref'], r['note'], r['account'],
                f"{r['debit']:,.0f}" if r['debit'] > 0 else "",
                f"{r['credit']:,.0f}" if r['credit'] > 0 else ""
            ))

    tree_sum.bind("<<TreeviewSelect>>", on_client_select)
    
    tk.Button(btn_f, text="🔄 Tải lại dữ liệu", command=refresh_summary, bg="#388E3C", fg="white", width=20).pack(side="left", padx=5)
    tk.Button(btn_f, text="📄 Xuất Biên bản đối chiếu", command=lambda: messagebox.showinfo("Info", "Tính năng đang được phát triển..."), bg="#1565C0", fg="white", width=25).pack(side="left", padx=5)
    
    refresh_summary()
    return main_f
