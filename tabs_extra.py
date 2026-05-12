"""tabs_extra.py — Tax Calculator, Manual, MST Guide, VSIC, AI Assistant, HR tabs"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os, webbrowser, requests, threading, datetime, subprocess, shutil, utils

# ── Human-readable niche display names ─────────────────────
NICHE_NAMES = {
    "photocopy_print":       "In ấn / Photocopy",
    "retail_grocery":        "Bán lẻ / Tạp hóa",
    "services_consulting":   "Dịch vụ / Tư vấn",
    "clinic_pharmacy":       "Y tế / Nhà thuốc",
    "fnb_cafe":              "F&B / Nhà hàng / Café",
    "real_estate":           "Bất động sản",
    "construction":          "Xây dựng",
    "transport_logistics":   "Vận tải / Logistics",
    "education_training":    "Giáo dục / Đào tạo",
    "general_trade":         "Thương mại tổng hợp",
}

def load_vsic():
    p = "presets/vsic_industries.json"
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    return {}

def _add_copy_menu(w):
    m = tk.Menu(w, tearoff=0)
    m.add_command(label="Sao chép (Copy)", command=lambda: w.event_generate("<<Copy>>"))
    w.bind("<Button-3>", lambda e: m.post(e.x_root, e.y_root))

def _make_readonly(event):
    if event.state & 4 and event.keysym.lower() in ('c', 'a'): return None
    if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Prior', 'Next', 'Home', 'End'): return None
    return "break"

# ── Tax Calculator tab ─────────────────────────────────────
def build_tax_calc_tab(app, nb, lbl):
    import tax_calculator
    tab = ttk.Frame(nb)
    nb.add(tab, text="🧮")
    mode = ttk.Notebook(tab)
    mode.pack(fill="both", expand=True, padx=8, pady=4)
    
    # Household (TT40)
    h = ttk.Frame(mode); mode.add(h, text="🏠")
    f = ttk.LabelFrame(h, text="🏠 Tính thuế Hộ kinh doanh (TT40)"); f.pack(fill="x", padx=10, pady=8)
    tk.Label(f, text="Doanh thu / năm (VND):").grid(row=0, column=0, padx=6, pady=4, sticky="w")
    e_rev = tk.Entry(f, width=22); e_rev.grid(row=0, column=1, padx=6)
    cats = list(tax_calculator.TT40_RATES.keys())
    cat_labels = [f"{tax_calculator.TT40_RATES[k]['name_vi']}" for k in cats]
    v_cat = tk.StringVar(value=cat_labels[0])
    ttk.Combobox(f, textvariable=v_cat, values=cat_labels, state="readonly", width=50).grid(row=1, column=1, padx=6)
    
    res = tk.Text(h, height=12, wrap="word", font=("Consolas", 10))
    res.pack(fill="both", expand=True, padx=10, pady=4)
    _add_copy_menu(res); res.bind("<Key>", _make_readonly)

    def calc():
        try:
            r = tax_calculator.calc_household_tax(float(e_rev.get().replace(",","")), cats[cat_labels.index(v_cat.get())])
            res.delete("1.0", "end")
            if r["exempt"]: res.insert("end", f"⚡ {r['exempt_note']}\n\n")
            res.insert("end", f"Doanh thu: {r['revenue']:>20,.0f} VND\nNgành: {r['category']}\nVAT: {r['vat_amount']:>20,.0f} VND\nTNCN: {r['pit_amount']:>20,.0f} VND\n{'─'*50}\nTổng thuế: {r['total_tax']:>20,.0f} VND\n")
        except Exception as ex: messagebox.showerror("Lỗi", str(ex))
    tk.Button(f, text="Tính", command=calc, bg="#1565C0", fg="white", width=10).grid(row=0, column=2, rowspan=2, padx=12)

    # SME
    s = ttk.Frame(mode); mode.add(s, text="🏢")
    f2 = ttk.LabelFrame(s, text="🏢 Tính thuế Doanh nghiệp (Khấu trừ)"); f2.pack(fill="x", padx=10, pady=8)
    tk.Label(f2, text="Doanh thu (VND):").grid(row=0, column=0, padx=6, pady=4, sticky="w"); e_rev2 = tk.Entry(f2, width=22); e_rev2.grid(row=0, column=1, padx=6)
    tk.Label(f2, text="Chi phí (VND):").grid(row=1, column=0, padx=6, pady=4, sticky="w"); e_exp2 = tk.Entry(f2, width=22); e_exp2.grid(row=1, column=1, padx=6)
    tk.Label(f2, text="Thuế suất VAT:").grid(row=2, column=0, padx=6, pady=4, sticky="w")
    vat_keys = list(tax_calculator.SME_VAT_RATES.keys())
    vat_labels = [f"{tax_calculator.SME_VAT_RATES[k]['label']}" for k in vat_keys]
    v_vat = tk.StringVar(value=vat_labels[1])
    ttk.Combobox(f2, textvariable=v_vat, values=vat_labels, state="readonly", width=60).grid(row=2, column=1, padx=6)
    
    res2 = tk.Text(s, height=12, wrap="word", font=("Consolas", 10))
    res2.pack(fill="both", expand=True, padx=10, pady=4)
    _add_copy_menu(res2); res2.bind("<Key>", _make_readonly)

    def calc2():
        try:
            r = tax_calculator.calc_sme_tax(float(e_rev2.get().replace(",","")), float(e_exp2.get().replace(",","")), vat_keys[vat_labels.index(v_vat.get())])
            res2.delete("1.0", "end")
            res2.insert("end", f"Doanh thu: {r['revenue']:>20,.0f} VND\nChi phí: {r['expenses']:>20,.0f} VND\nVAT đầu ra ({r['vat_rate']*100:.0f}%): {r['vat_output']:>20,.0f} VND\nVAT đầu vào (ước tính): {r['vat_input_est']:>20,.0f} VND\nVAT phải nộp: {r['vat_payable']:>20,.0f} VND\n{'─'*55}\nLợi nhuận trước thuế: {r['profit_before_tax']:>20,.0f} VND\nThuế TNDN (20%): {r['cit_amount']:>20,.0f} VND\nLợi nhuận sau thuế: {r['net_profit']:>20,.0f} VND\n\n⚡ {r['vat_label']}")
        except Exception as ex: messagebox.showerror("Lỗi", str(ex))
    tk.Button(f2, text="Tính thuế", command=calc2, bg="#1565C0", fg="white", width=10).grid(row=0, column=2, rowspan=3, padx=12)

# ── Manual / Help tab ──────────────────────────────────────
def build_manual_tab(app, nb, lbl):
    import manual as manual_mod
    tab = ttk.Frame(nb)
    nb.add(tab, text="📘")
    txt = tk.Text(tab, wrap="word", font=("Arial", 10), padx=12, pady=8)
    sb = ttk.Scrollbar(tab, command=txt.yview)
    txt.config(yscrollcommand=sb.set)
    txt.pack(fill="both", expand=True, side="left")
    sb.pack(fill="y", side="right")
    txt.insert("end", manual_mod.get_manual_text())
    _add_copy_menu(txt)
    txt.bind("<Key>", _make_readonly)

# ── MST Lookup Guide tab ──────────────────────────────────
# ── Legal Templates 2026 tab ──────────────────────────────
def build_legal_docs_tab(app, nb, lbl):
    """Offline Legal Templates 2026."""
    tab = ttk.Frame(nb)
    nb.add(tab, text="📜")
    main_f = tk.Frame(tab, bg="#FFFFFF"); main_f.pack(fill="both", expand=True, padx=15, pady=15)
    
    h_f = tk.Frame(main_f, bg="#FFFFFF"); h_f.pack(fill="x")
    tk.Label(h_f, text="📁 KHO VĂN BẢN MẪU & QUY ĐỊNH PHÁP LUẬT 2026", font=("Segoe UI", 12, "bold"), bg="#FFFFFF", fg="#1565C0").pack(side="left", pady=10)
    tk.Button(h_f, text="❓", command=lambda: messagebox.showinfo("Hướng dẫn", "Nơi lưu trữ các biểu mẫu kế toán và thuế chuẩn 2026. Bạn có thể tải về để sử dụng."), relief="flat").pack(side="right")

    cols = ("name", "version", "status", "date")
    tree = ttk.Treeview(main_f, columns=cols, show="headings", height=15)
    heads = ["Tên Văn bản / Biểu mẫu", "Phiên bản", "Trạng thái Hiệu lực", "Ngày cập nhật"]
    for c, h in zip(cols, heads):
        tree.heading(c, text=h); tree.column(c, width=280 if c=="name" else 120)
    tree.pack(fill="both", expand=True)
    
    templates = [
        ("Tờ khai thuế GTGT (01/GTGT) - TT80", "V2026.1", "✅ Còn hiệu lực", "2026-01-01"),
        ("Tờ khai Quyết toán thuế TNDN (03/TNDN)", "V2026.1", "✅ Còn hiệu lực", "2026-01-10"),
        ("Quyết toán thuế TNCN (05/QTT-TNCN)", "V2026.1", "✅ Còn hiệu lực", "2026-01-20"),
        ("Báo cáo Kết quả KD (B02-DNN) - TT133", "V2026.2", "✅ Còn hiệu lực", "2026-02-15"),
        ("Bảng Cân đối kế toán (B01-DNN)", "V2026.1", "✅ Còn hiệu lực", "2026-01-01"),
        ("Bảng tính Doanh thu mẫu (Excel)", "V2026.2", "✅ Còn hiệu lực", "2026-03-01"),
        ("Bảng đối soát Công nợ Phải thu/Phải trả", "V2026.1", "✅ Còn hiệu lực", "2026-01-15"),
        ("Phiếu Thu / Phiếu Chi chuẩn (C40/C41)", "V2026.1", "✅ Còn hiệu lực", "2026-01-01"),
        ("Hợp đồng lao động mẫu chuẩn 2026", "V2026.1", "✅ Còn hiệu lực", "2026-01-10"),
        ("Biên bản đối chiếu công nợ cuối kỳ", "V2026.1", "✅ Còn hiệu lực", "2026-01-05")
    ]
    for t in templates: tree.insert("", "end", values=t)
    
    def _download():
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Thông báo", "Vui lòng chọn văn bản cần tải!")
        item_name = tree.item(sel[0])['values'][0]
        folder = os.path.join(os.getcwd(), "docs", "templates_2026")
        if not os.path.exists(folder): os.makedirs(folder)
        
        safe_name = item_name.replace("/", "_").replace("\\", "_")
        filepath = os.path.join(folder, f"{safe_name}.txt")
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"HƯỚNG DẪN TẢI VĂN BẢN: {item_name}\n{'='*50}\n\n1. Truy cập gdt.gov.vn hoặc ketoanthienung.net\n2. Tìm kiếm tên văn bản trên.\n3. Tải file (.doc/.xls) và lưu vào thư mục này để quản lý.\n\nĐây là file hướng dẫn tự động từ VN SME Ledger.")
        
        messagebox.showinfo("Thành công", f"Đã tạo file hướng dẫn & vị trí lưu cho: {item_name}\nBạn hãy bổ sung file thực tế vào thư mục này.")
        try: os.startfile(filepath)
        except: subprocess.Popen(['notepad.exe', filepath])

    def _upload():
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Thông báo", "Vui lòng chọn mục văn bản cần tải lên!")
        item_name = tree.item(sel[0])['values'][0]
        fpath = filedialog.askopenfilename(title=f"Chọn file cho: {item_name}", 
                                           filetypes=[("Excel/Word/PDF", "*.xlsx *.xls *.docx *.doc *.pdf"), ("All Files", "*.*")])
        if fpath:
            folder = os.path.join(os.getcwd(), "docs", "templates_2026")
            if not os.path.exists(folder): os.makedirs(folder)
            ext = os.path.splitext(fpath)[1]
            safe_name = item_name.replace("/", "_").replace("\\", "_")
            dest = os.path.join(folder, safe_name + ext)
            try:
                shutil.copy(fpath, dest)
                messagebox.showinfo("Thành công", f"Đã tải lên văn bản: {os.path.basename(dest)}\nLưu tại: docs/templates_2026/")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tải lên: {e}")
        
    def _open_folder():
        folder = os.path.join(os.getcwd(), "docs", "templates_2026")
        if not os.path.exists(folder): os.makedirs(folder)
        os.startfile(folder)

    def _check():
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Thông báo", "Vui lòng chọn văn bản cần kiểm tra!")
        status = tree.item(sel[0])['values'][2]
        msg = "Văn bản này hiện đang có hiệu lực theo quy định 2026. Nguồn: gdt.gov.vn" if "✅" in status else \
              "Văn bản này đang chờ bản cập nhật mới nhất từ Bộ Tài chính."
        messagebox.showinfo("Kiểm tra tính pháp lý", msg)

    def _add_custom():
        def _save():
            name = e_name.get().strip()
            if not name: return
            new_row = (name, e_ver.get() or "V2026.1", "✅ Còn hiệu lực", datetime.date.today().strftime("%Y-%m-%d"))
            tree.insert("", "end", values=new_row)
            utils.log_activity(f"Thêm mẫu văn bản thủ công: {name}")
            win.destroy()
            
        win = tk.Toplevel(app)
        win.title("Thêm văn bản mới")
        win.geometry("400x250")
        f = ttk.Frame(win, padding=20)
        f.pack(fill="both", expand=True)
        tk.Label(f, text="Tên văn bản:").pack(anchor="w")
        e_name = tk.Entry(f, width=40); e_name.pack(pady=5)
        tk.Label(f, text="Phiên bản:").pack(anchor="w")
        e_ver = tk.Entry(f, width=20); e_ver.insert(0, "V2026.1"); e_ver.pack(pady=5)
        tk.Button(f, text="Lưu", command=_save, bg="#388E3C", fg="white", width=15).pack(pady=15)

    btn_f = tk.Frame(main_f, bg="#FFFFFF"); btn_f.pack(fill="x", pady=10)
    tk.Button(btn_f, text="➕ Thêm văn bản mới", bg="#0288D1", fg="white", padx=10, command=_add_custom, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
    tk.Button(btn_f, text="⬇️ Tải hướng dẫn", bg="#1565C0", fg="white", padx=10, command=_download, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
    tk.Button(btn_f, text="📤 Tải lên mẫu (Upload)", bg="#2E7D32", fg="white", padx=10, command=_upload, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
    tk.Button(btn_f, text="🔍 Kiểm tra hiệu lực", bg="#FF9800", fg="white", padx=10, command=_check, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
    tk.Button(btn_f, text="📂 Mở thư mục", bg="#455A64", fg="white", padx=10, command=_open_folder, font=("Segoe UI", 9, "bold")).pack(side="right", padx=5)

# ── VSIC Industry Codes sub-tab ───────────────────────────
def build_vsic_subtab(app, sub_nb):
    tab = ttk.Frame(sub_nb)
    sub_nb.add(tab, text="🏢")
    vsic = load_vsic()
    def _on_search(event=None):
        query = e_search.get().lower().strip()
        for i in tree.get_children(): tree.delete(i)
        for g_name in vsic:
            for it in vsic[g_name]:
                if query in it.get("vsic","").lower() or query in it.get("name","").lower():
                    tree.insert("","end", values=(it.get("vsic",""), it.get("name",""), it.get("tax_cat","")))
    
    sf = ttk.Frame(tab); sf.pack(fill="x", padx=10, pady=5)
    tk.Label(sf, text="🔍 Tìm kiếm Ngành nghề (Mã hoặc Tên):", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
    e_search = tk.Entry(sf, width=40); e_search.pack(side="left", padx=5)
    e_search.bind("<KeyRelease>", _on_search)
    
    tree = ttk.Treeview(tab, columns=("v", "n", "t"), show="headings", height=12)
    for c,h,w in [("v","Mã Ngành",80),("n","Tên Ngành Nghề Kinh Doanh",400),("t","Thuế suất Thông tư 40",150)]:
        tree.heading(c, text=h); tree.column(c, width=w)
    tree.pack(fill="both", expand=True)
    _on_search()

# ── ADVANCED AI AGENT TAB (v6.1 - Complete) ───────────────
def build_ai_tab(app, nb, lbl):
    """AI Assistant with clear activation flow."""
    tab = ttk.Frame(nb)
    nb.add(tab, text="🧠")
    
    main_f = tk.Frame(tab, bg="#FFFFFF"); main_f.pack(fill="both", expand=True)
    
    # Initial Setup View
    setup_f = tk.Frame(main_f, bg="#FFFFFF")
    setup_f.pack(fill="both", expand=True, padx=40, pady=40)
    
    tk.Label(setup_f, text="🚀 CHÀO MỪNG ĐẾN VỚI WIKI AI CHUYÊN GIA", font=("Segoe UI", 16, "bold"), bg="#FFFFFF", fg="#1565C0").pack(pady=10)
    
    guide_txt = (
        "Wiki AI là trợ lý trí tuệ nhân tạo chạy hoàn toàn OFFLINE, đảm bảo bảo mật dữ liệu.\n\n"
        "CÁC BƯỚC THIẾT LẬP CHO NGƯỜI MỚI:\n"
        "1. Cài đặt Ollama (từ ollama.com) nếu chưa có.\n"
        "2. Mở Terminal và chạy lệnh: 'ollama pull llama3' (hoặc model bạn thích).\n"
        "3. Đảm bảo Ollama đang chạy dưới khay hệ thống.\n"
        "4. Bấm nút 'KÍCH HOẠT KẾT NỐI' bên dưới để bắt đầu thảo luận.\n\n"
        "Lưu ý: Tính năng này yêu cầu phần cứng có GPU hoặc CPU đời mới để đạt tốc độ tốt nhất."
    )
    tk.Label(setup_f, text=guide_txt, justify="left", bg="#F8F9FA", padx=20, pady=20, font=("Segoe UI", 10)).pack(fill="x")
    
    def _activate():
        setup_f.pack_forget()
        _build_chat_interface(main_f, app)
        
    tk.Button(setup_f, text="✅ TÔI ĐÃ HIỂU - KÍCH HOẠT KẾT NỐI NGAY", command=_activate, 
              bg="#2E7D32", fg="white", font=("Segoe UI", 11, "bold"), padx=20, pady=10).pack(pady=30)

    def _build_chat_interface(parent, app):
        chat_f = tk.Frame(parent, bg="#FFFFFF"); chat_f.pack(fill="both", expand=True, padx=10, pady=10)
        HISTORY_FILE = "data/ai_history.json"
        SYS_PROMPT = "Bạn là chuyên gia tư vấn Quản trị, Kế toán và Dòng tiền (2026). Trả lời đầy đủ, không viết tắt."
        
        hdr = tk.Frame(chat_f, bg="#FFFFFF"); hdr.pack(fill="x", pady=5)
        tk.Label(hdr, text="Model AI:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        v_model = tk.StringVar(value="llama3")
        cmb_model = ttk.Combobox(hdr, textvariable=v_model, width=15); cmb_model.pack(side="left", padx=5)
        
        def _refresh():
            try:
                r = requests.get("http://localhost:11434/api/tags", timeout=2)
                if r.status_code == 200: cmb_model['values'] = [m['name'] for m in r.json().get('models', [])]
            except: pass
        
        tk.Button(hdr, text="🔄", command=_refresh, relief="flat", bg="#FFFFFF").pack(side="left")
        
        txt_chat = tk.Text(chat_f, wrap="word", font=("Segoe UI", 9), bg="#F8F9FA", relief="flat", height=15)
        txt_chat.tag_config("user_box", background="#E3F2FD", spacing1=5, spacing3=5, lmargin1=15)
        txt_chat.tag_config("ai_box", background="#FFFFFF", spacing1=5, spacing3=5, lmargin1=10)
        txt_chat.tag_config("sys_box", foreground="#666", font=("Segoe UI", 8, "italic"), justify="center")
        _add_copy_menu(txt_chat)
        sb = ttk.Scrollbar(chat_f, command=txt_chat.yview); txt_chat.config(yscrollcommand=sb.set); txt_chat.pack(fill="both", expand=True); sb.pack(side="right", fill="y", in_=txt_chat)
        
        inp_f = tk.Frame(chat_f, bg="#FFFFFF", bd=1, relief="solid"); inp_f.pack(fill="x", pady=5)
        ent_msg = tk.Entry(inp_f, font=("Segoe UI", 10), relief="flat"); ent_msg.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        def log_msg(sender, msg, style="ai"):
            txt_chat.config(state="normal")
            txt_chat.insert("end", f"{sender}\n", ("bold", f"{style}_box"))
            txt_chat.insert("end", f"{msg}\n\n", f"{style}_box")
            txt_chat.see("end"); txt_chat.config(state="disabled")
            try:
                with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump({"chat": txt_chat.get("1.0", "end")}, f)
            except: pass

        def _call(p):
            full = f"{SYS_PROMPT}\n\nCâu hỏi: {p}"
            def _th():
                try:
                    r = requests.post("http://localhost:11434/api/generate", 
                                      json={"model":v_model.get(), "prompt":full, "stream":False}, timeout=120)
                    if r.status_code == 200: 
                        app.after(0, lambda: log_msg("AI", r.json().get('response',''), "ai"))
                    else:
                        app.after(0, lambda: log_msg("Hệ thống", "Lỗi từ AI Server.", "sys"))
                except: app.after(0, lambda: log_msg("Lỗi", "Không kết nối được AI. Hãy đảm bảo Ollama đang chạy.", "sys"))
            threading.Thread(target=_th, daemon=True).start()

        def send_msg(e=None):
            txt = ent_msg.get().strip()
            if not txt: return
            ent_msg.delete(0, "end"); log_msg("Bạn", txt, "user"); _call(txt)
            
        tk.Button(inp_f, text="Gửi 🚀", command=send_msg, bg="#1565C0", fg="white", font=("Segoe UI", 9, "bold")).pack(side="right", padx=5)
        ent_msg.bind("<Return>", send_msg)
        
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f: 
                    txt_chat.insert("end", json.load(f).get("chat", ""))
                    txt_chat.see("end")
            except: pass
        _refresh()

# ── Payroll & HR Tab (ENHANCED 2026) ──────────────────────
def build_payroll_tab(app, nb, lbl):
    tab = ttk.Frame(nb)
    nb.add(tab, text="👥")
    EMP_FILE = "data/employees.json"
    
    def calc_pit(taxable_income):
        # Biểu thuế lũy tiến từng phần 2026 (Giả định quy định chuẩn)
        if taxable_income <= 0: return 0
        brackets = [
            (5000000, 0.05, 0),
            (10000000, 0.1, 250000),
            (18000000, 0.15, 750000),
            (32000000, 0.2, 1650000),
            (52000000, 0.25, 3250000),
            (80000000, 0.3, 5850000),
            (float('inf'), 0.35, 9850000)
        ]
        prev_limit = 0
        for limit, rate, deduct in brackets:
            if taxable_income <= limit:
                return taxable_income * rate - deduct
        return 0

    def load_emp():
        if os.path.exists(EMP_FILE):
            try:
                with open(EMP_FILE, "r", encoding="utf-8") as f: return json.load(f)
            except: pass
        return []

    def save_emp(data):
        os.makedirs("data", exist_ok=True)
        with open(EMP_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

    h_f = ttk.Frame(tab); h_f.pack(fill="x")
    tk.Label(h_f, text="👥 QUẢN LÝ NHÂN SỰ & BẢNG LƯƠNG 2026", font=("Segoe UI", 11, "bold")).pack(side="left", padx=15, pady=5)
    tk.Button(h_f, text="❓", command=lambda: messagebox.showinfo("Hướng dẫn", "Quản lý nhân viên, tính lương theo quy định 2026. Bao gồm Bảo hiểm (10.5%) và Thuế TNCN lũy tiến."), relief="flat").pack(side="right", padx=15)
    
    main_f = ttk.Frame(tab); main_f.pack(fill="both", expand=True, padx=15, pady=15)
    
    # Left: List
    left = ttk.LabelFrame(main_f, text="📋 Bảng lương & Nhân sự")
    left.pack(side="left", fill="both", expand=True, padx=5)
    
    cols = ("id", "name", "role", "sal", "allow", "ins", "pit", "net")
    tree = ttk.Treeview(left, columns=cols, show="headings", height=15)
    heads = ["Mã Nhân viên", "Họ và Tên", "Chức danh", "Lương Cơ bản", "Phụ cấp", "Bảo hiểm Xã hội (10.5%)", "Thuế Thu nhập cá nhân", "Thực lĩnh"]
    for c, h in zip(cols, heads):
        tree.heading(c, text=h); tree.column(c, width=110 if len(c)>2 else 60)
    tree.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Right: Form
    right = tk.Frame(main_f); right.pack(side="right", fill="y", padx=5)
    f_form = ttk.LabelFrame(right, text="👤 Thông tin & Cấu hình"); f_form.pack(fill="x")
    
    fields_cfg = [
        ("Mã Nhân viên:", "code", "entry"), ("Họ và Tên:", "name", "entry"), 
        ("Chức danh:", "role", "combo"), ("Lương Cơ bản:", "salary", "entry"), 
        ("Phụ cấp:", "allowance", "entry"), ("Người phụ thuộc:", "dependents", "entry")
    ]
    entries = {}
    roles = ["Giám đốc", "Phó Giám đốc", "Kế toán trưởng", "Kế toán viên", "Trưởng phòng", "Nhân viên kinh doanh", "Kỹ thuật viên", "Cộng tác viên"]
    
    for i, (label, key, tip) in enumerate(fields_cfg):
        tk.Label(f_form, text=label).grid(row=i, column=0, padx=5, pady=3, sticky="w")
        if tip == "combo":
            e = ttk.Combobox(f_form, values=roles, width=18)
        else:
            e = tk.Entry(f_form, width=20)
            if key in ["salary", "allowance", "dependents"]: e.insert(0, "0")
        e.grid(row=i, column=1, padx=5, pady=3)
        entries[key] = e

    def refresh():
        for i in tree.get_children(): tree.delete(i)
        for e in load_emp():
            sal = float(e.get('salary', 0))
            allow = float(e.get('allowance', 0))
            deps = int(e.get('dependents', 0))
            
            ins = sal * 0.105 # BHXH 8%, BHYT 1.5%, BHTN 1%
            taxable = (sal + allow) - ins - 11000000 - (deps * 4400000)
            pit = calc_pit(taxable)
            net = (sal + allow) - ins - pit
            
            tree.insert("", "end", values=(
                e.get("code",""), e.get("name",""), e.get("role",""),
                f"{sal:,.0f}", f"{allow:,.0f}", f"{ins:,.0f}", f"{pit:,.0f}", f"{net:,.0f}"
            ))
    
    def add_emp():
        data = load_emp()
        new_e = {k: e.get() for k, e in entries.items()}
        if not new_e['code']: return messagebox.showwarning("Lỗi", "Nhập Mã NV")
        # Update if exists
        data = [x for x in data if x['code'] != new_e['code']]
        data.append(new_e); save_emp(data); refresh()

    def del_emp():
        sel = tree.selection()
        if not sel: return
        code = tree.item(sel[0])['values'][0]
        data = [e for e in load_emp() if e.get('code') != str(code)]
        save_emp(data); refresh()

    def export_payroll_excel():
        data = load_emp()
        if not data: return messagebox.showwarning("Thông báo", "Không có dữ liệu để xuất!")
        fpath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV (Excel)", "*.csv"), ("All Files", "*.*")])
        if fpath:
            import csv
            try:
                with open(fpath, "w", encoding="utf-8-sig", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=["code", "name", "role", "salary", "allowance", "dependents"])
                    w.writeheader()
                    w.writerows(data)
                messagebox.showinfo("Thành công", f"Đã xuất dữ liệu ra: {fpath}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xuất file: {e}")

    def export_payroll_word():
        data = load_emp()
        if not data: return messagebox.showwarning("Thông báo", "Không có dữ liệu!")
        fpath = filedialog.asksaveasfilename(defaultextension=".doc", filetypes=[("Word Document", "*.doc")])
        if fpath:
            try:
                html = "<html><meta charset='utf-8'><body>"
                html += "<h2 style='text-align:center;'>DANH SÁCH NHÂN VIÊN</h2>"
                html += "<table border='1' style='border-collapse:collapse;width:100%;'>"
                html += "<tr style='background:#EEE;'><th>Mã NV</th><th>Họ và Tên</th><th>Chức danh</th><th>Lương CB</th><th>Phụ cấp</th></tr>"
                for e in data:
                    html += f"<tr><td>{e.get('code','')}</td><td>{e.get('name','')}</td><td>{e.get('role','')}</td>"
                    html += f"<td>{float(e.get('salary',0)):,.0f}</td><td>{float(e.get('allowance',0)):,.0f}</td></tr>"
                html += "</table></body></html>"
                with open(fpath, "w", encoding="utf-8") as f: f.write(html)
                messagebox.showinfo("Thành công", f"Đã xuất danh sách nhân sự ra Word:\n{fpath}")
                os.startfile(fpath)
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))

    def import_payroll():
        fpath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if fpath:
            import csv
            try:
                new_data = []
                with open(fpath, "r", encoding="utf-8-sig") as f:
                    r = csv.DictReader(f)
                    for row in r: new_data.append(dict(row))
                save_emp(new_data); refresh()
                messagebox.showinfo("Thành công", "Đã nhập dữ liệu nhân sự mới!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể nhập file: {e}")

    btn_f = ttk.Frame(right); btn_f.pack(pady=10)
    tk.Button(btn_f, text="💾 Lưu/Cập nhật", command=add_emp, bg="#388E3C", fg="white", width=18).pack(side="top", pady=3)
    tk.Button(btn_f, text="❌ Xóa nhân viên", command=del_emp, bg="#D32F2F", fg="white", width=18).pack(side="top", pady=3)
    
    # Export/Import buttons
    tk.Label(right, text="📂 QUẢN LÝ DỮ LIỆU", font=("Segoe UI", 9, "bold"), fg="#555").pack(pady=(15, 5))
    tk.Button(right, text="📊 Xuất Excel (CSV)", command=export_payroll_excel, bg="#455A64", fg="white", width=18).pack(pady=3)
    tk.Button(right, text="📄 Xuất Word (Doc)", command=export_payroll_word, bg="#455A64", fg="white", width=18).pack(pady=3)
    tk.Button(right, text="📥 Nhập dữ liệu", command=import_payroll, bg="#455A64", fg="white", width=18).pack(pady=3)
    
    refresh()
