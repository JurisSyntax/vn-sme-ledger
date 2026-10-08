"""tabs_extra.py — Tax Calculator, Manual, MST Guide, VSIC, AI Assistant, HR tabs"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os, datetime, subprocess, shutil, utils, threading
from pathlib import Path
from ai.llm_worker import OfflineAssistant
from ai.memory_profile import ProfileLimitError, ProfileStore
from core import legal_vault
from core import office_integration
from core.hr_compliance import payroll_snapshot, MONTHLY_OVERTIME_CAP_HOURS
from core.payroll import calculate_monthly_payroll
from core.encryption import decrypt_value, encrypt_value

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
    p = utils.get_resource_path(os.path.join("presets", "vsic_industries.json"))
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f: return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}
    return {}

def _add_copy_menu(w):
    m = tk.Menu(w, tearoff=0)
    def _copy():
        try:
            w.event_generate("<<Copy>>")
        except Exception:
            text = ""
            if hasattr(w, "cget"):
                try: text = w.cget("text")
                except Exception: text = ""
            if text:
                w.clipboard_clear()
                w.clipboard_append(text)
    def _paste():
        try:
            w.event_generate("<<Paste>>")
        except Exception:
            pass
    m.add_command(label="Sao chép (Copy)", command=_copy)
    if isinstance(w, (tk.Entry, tk.Text)):
        m.add_command(label="Dán (Paste)", command=_paste)
    w.bind("<Button-3>", lambda e: m.post(e.x_root, e.y_root))

def _make_readonly(event):
    if event.state & 4 and event.keysym.lower() in ('c', 'a'): return None
    if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Prior', 'Next', 'Home', 'End'): return None
    return "break"

# ── Tax Calculator tab ─────────────────────────────────────
def build_tax_calc_tab(app, nb, lbl):
    import tax_calculator
    tab = ttk.Frame(nb)
    nb.add(tab, text=lbl.get("sub_tax", "Tính thuế"))
    mode = ttk.Notebook(tab)
    mode.pack(fill="both", expand=True, padx=8, pady=4)
    
    # Household 2026 path. Keep calc_household_tax() available for legacy API
    # callers, but do not expose its pre-2026 threshold in the live UI.
    h = ttk.Frame(mode); mode.add(h, text="🏠")
    f = ttk.LabelFrame(h, text="🏠 Tính thuế Hộ kinh doanh (quy tắc 2026)"); f.pack(fill="x", padx=10, pady=8)
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
            r = tax_calculator.calc_household_tax_2026(
                float(e_rev.get().replace(",", "")),
                cats[cat_labels.index(v_cat.get())],
                pit_method="revenue",
            )
            res.delete("1.0", "end")
            if r["exempt"]: res.insert("end", f"⚡ {r['exempt_note']}\n\n")
            res.insert("end", f"Doanh thu: {r['revenue']:>20,.0f} VND\nNgành: {r['category']}\nVAT: {r['vat_amount']:>20,.0f} VND\nTNCN: {r['pit_amount']:>20,.0f} VND\nPhương pháp TNCN: {r['pit_method']}\n{'─'*50}\nTổng thuế: {r['total_tax']:>20,.0f} VND\n\nCăn cứ: {r['legal_basis']}\nĐây là kết quả lập kế hoạch; cần đối chiếu hồ sơ trước khi kê khai.\n")
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
    nb.add(tab, text=lbl.get("sub_manual", "Trợ giúp"))
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
    nb.add(tab, text=lbl.get("sub_legal", "Kho văn bản mẫu"))
    main_f = tk.Frame(tab, bg="#FFFFFF"); main_f.pack(fill="both", expand=True, padx=15, pady=15)
    
    h_f = tk.Frame(main_f, bg="#FFFFFF"); h_f.pack(fill="x")
    title_lbl = tk.Label(h_f, text="📁 KHO VĂN BẢN MẪU & QUY ĐỊNH PHÁP LUẬT 2026", font=("Segoe UI", 12, "bold"), bg="#FFFFFF", fg="#1565C0")
    title_lbl.pack(side="left", pady=10)
    _add_copy_menu(title_lbl)
    tk.Button(h_f, text="❓", command=lambda: messagebox.showinfo("Hướng dẫn", "Kho chỉ mở file đã lưu trong máy. Nếu chưa có bản lưu, phần mềm sẽ báo thiếu file để người dùng upload. Nút 'Mở bằng...' cho phép chọn Word/Excel, LibreOffice, OpenOffice, FreeOffice, WPS, Polaris hoặc ONLYOFFICE nếu đã cài."), relief="flat").pack(side="right")

    manifest_path = os.path.join("db", "legal_manifest.json")
    storage_dir = os.path.join("docs", "templates_2026")
    docs = legal_vault.ensure_manifest(manifest_path, storage_dir)

    cols = ("title", "purpose", "tag", "status", "basis")
    tree_holder = ttk.Frame(main_f)
    tree = ttk.Treeview(tree_holder, columns=cols, show="headings", height=15)
    heads = ["Tên Văn bản / Biểu mẫu", "Chức năng / Mô tả", "Tag", "Trạng thái / Lưu trữ", "Cơ sở pháp lý"]
    for c, h in zip(cols, heads):
        tree.heading(c, text=h)
        if c == "title":
            tree.column(c, width=220)
        elif c == "purpose":
            tree.column(c, width=320)
        elif c == "tag":
            tree.column(c, width=80)
        else:
            tree.column(c, width=150)
    # tree.pack will be called after the buttons frame is packed to avoid Z-order overflow.

    doc_by_item = {}
    def _refresh_docs():
        nonlocal docs
        docs = legal_vault.ensure_manifest(manifest_path, storage_dir)
        doc_by_item.clear()
        for item in tree.get_children(): tree.delete(item)
        for doc in docs:
            status = legal_vault.get_validity_status(doc)
            iid = tree.insert("", "end", values=(doc["title"], doc.get("purpose",""), doc.get("tag",""), status, doc["legal_basis"]))
            doc_by_item[iid] = doc
    _refresh_docs()

    def _selected_doc():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Thông báo", "Vui lòng chọn văn bản.")
            return None
        return doc_by_item.get(sel[0])

    def _copy_document():
        doc = _selected_doc()
        if not doc: return
        try:
            dest = legal_vault.make_document_copy(doc, os.path.join("docs", "copies"))
            messagebox.showinfo("Thành công", f"Đã tạo bản sao văn bản:\n{dest}")
            legal_vault.open_local_path(dest)
        except FileNotFoundError:
            messagebox.showwarning("Thiếu file", "⚠️ Không tìm thấy bản sao lưu. Hãy dùng nút Tải lên (Upload) để lưu file Word/Excel/PDF vào kho.")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _open_selected_file():
        doc = _selected_doc()
        if not doc: return
        path = legal_vault.resolve_original_path(doc)
        if not path.exists():
            messagebox.showwarning("Thiếu file", "⚠️ Không lưu trữ trên kho dữ liệu phần mềm")
            return
        try:
            legal_vault.open_local_path(path)
        except Exception as e:
            messagebox.showerror("Lỗi mở file", str(e))

    def _open_selected_with():
        """Choose a locally installed Word/Excel-compatible application."""
        doc = _selected_doc()
        if not doc:
            return
        path = legal_vault.resolve_original_path(doc)
        if not path.exists():
            messagebox.showwarning("Thiếu file", "Không tìm thấy file trong kho dữ liệu phần mềm.")
            return
        options = office_integration.menu_options(path)
        labels = [option["label"] for option in options]
        if len(options) == 1:
            result = office_integration.open_document(path, options[0]["id"])
            if not result.get("ok"):
                messagebox.showerror("Không thể mở file", str(result.get("message", "Lỗi không xác định.")))
            return

        win = tk.Toplevel(app)
        win.title("Mở tài liệu bằng bộ Office")
        win.geometry("460x170")
        win.transient(app)
        frame = ttk.Frame(win, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Chọn ứng dụng đã cài trên máy:").pack(anchor="w", pady=(0, 8))
        selected = tk.StringVar(value=labels[0])
        combo = ttk.Combobox(frame, textvariable=selected, values=labels, state="readonly", width=52)
        combo.pack(fill="x", pady=(0, 14))

        def launch():
            option = options[labels.index(selected.get())]
            result = office_integration.open_document(path, option["id"])
            if result.get("ok"):
                win.destroy()
            else:
                messagebox.showerror("Không thể mở file", str(result.get("message", "Lỗi không xác định.")), parent=win)

        ttk.Button(frame, text="Mở tài liệu", command=launch).pack(anchor="e")

    def _edit_selected():
        """Fill prepared DOCX/XLSX fields and save a separate working copy."""
        doc = _selected_doc()
        if not doc:
            return
        path = legal_vault.resolve_storage_path(doc)
        if path.suffix.lower() not in {".docx", ".xlsx"} or not path.exists():
            return messagebox.showinfo(
                "Không có trình điền",
                "Trình điền nội bộ hỗ trợ DOCX/XLSX hợp lệ. Dùng Mở bằng... cho định dạng khác.",
            )
        fields = [field for field in doc.get("editable_fields", []) if field]
        if not fields:
            return messagebox.showinfo("Chưa có trường điền", "Mẫu này chưa được chuẩn hóa trường điền.")

        from core.document_templates import FIELD_LABELS, extract_office_text, fill_office_template, preview_with_values

        win = tk.Toplevel(app)
        win.title(f"Điền mẫu: {doc.get('title', '')}")
        win.geometry("760x640")
        win.transient(app)
        outer = ttk.Frame(win, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=f"Trạng thái: {legal_vault.get_validity_status(doc)}", wraplength=720).pack(anchor="w", pady=(0, 8))
        form = ttk.Frame(outer)
        form.pack(fill="x")
        values = {}
        for field in fields:
            ttk.Label(form, text=FIELD_LABELS.get(field, field)).pack(anchor="w")
            value = tk.StringVar()
            values[field] = value
            ttk.Entry(form, textvariable=value).pack(fill="x", pady=(0, 4))

        preview = tk.Text(outer, height=14, wrap="word")
        preview.pack(fill="both", expand=True, pady=8)
        preview.configure(state="disabled")
        source_preview = extract_office_text(path)

        def refresh_preview(*_):
            preview.configure(state="normal")
            preview.delete("1.0", "end")
            preview.insert("1.0", preview_with_values(source_preview, {k: v.get() for k, v in values.items()}))
            preview.configure(state="disabled")

        for value in values.values():
            value.trace_add("write", refresh_preview)
        refresh_preview()

        def save_working_copy():
            output_dir = Path("docs") / "working_copies"
            output_dir.mkdir(parents=True, exist_ok=True)
            output = output_dir / f"{legal_vault.safe_filename(doc.get('title', 'mau'))}_{datetime.datetime.now():%Y%m%d_%H%M%S}{path.suffix.lower()}"
            try:
                fill_office_template(path, output, {k: v.get() for k, v in values.items()})
                messagebox.showinfo("Đã lưu", f"Đã lưu bản làm việc tại:\n{output}", parent=win)
                win.destroy()
                legal_vault.open_local_path(output)
            except Exception as exc:
                messagebox.showerror("Không thể lưu", str(exc), parent=win)

        ttk.Button(outer, text="Lưu bản làm việc và mở Office", command=save_working_copy).pack(anchor="e")

    def _upload():
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Thông báo", "Vui lòng chọn mục văn bản cần tải lên!")
        item_name = tree.item(sel[0])['values'][0]
        fpath = filedialog.askopenfilename(title=f"Chọn file cho: {item_name}", 
                                           filetypes=[("Excel/Word/PDF", "*.xlsx *.xls *.docx *.doc *.pdf"), ("All Files", "*.*")])
        if fpath:
            folder = os.path.join(os.getcwd(), "docs", "templates_2026")
            if not os.path.exists(folder): os.makedirs(folder)
            try:
                doc = doc_by_item[sel[0]]
                updated = legal_vault.register_upload(manifest_path, storage_dir, doc["id"], fpath)
                messagebox.showinfo("Thành công", f"Đã tải lên văn bản: {updated['storage_filename']}\nLưu tại: docs/templates_2026/")
                _refresh_docs()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tải lên: {e}")
        
    def _open_folder():
        folder = os.path.join(os.getcwd(), "docs", "templates_2026")
        if not os.path.exists(folder): os.makedirs(folder)
        os.startfile(folder)

    def _check():
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Thông báo", "Vui lòng chọn văn bản cần kiểm tra!")
        doc = doc_by_item[sel[0]]
        status = legal_vault.get_validity_status(doc)
        msg = f"{status}\nCơ sở đối chiếu: {doc['legal_basis']}\nPattern: {doc.get('effective_pattern','')}"
        messagebox.showinfo("Kiểm tra tính pháp lý", msg)

    def _delete_doc():
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Thông báo", "Vui lòng chọn văn bản cần xóa!")
        doc = doc_by_item[sel[0]]
        confirm = messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa văn bản '{doc['title']}' khỏi danh mục?")
        if confirm:
            rows = legal_vault.ensure_manifest(manifest_path, storage_dir)
            rows = [r for r in rows if r["id"] != doc["id"]]
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
            path = legal_vault.resolve_storage_path(doc)
            if path.exists():
                try: path.unlink()
                except: pass
            _refresh_docs()
            utils.log_activity(f"Xóa mẫu văn bản: {doc['title']}")
            messagebox.showinfo("Thành công", f"Đã xóa văn bản '{doc['title']}'!")

    def _add_custom():
        def _save():
            name = e_name.get().strip()
            if not name:
                return messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tên văn bản.", parent=win)
            try:
                legal_vault.add_custom_document(
                    manifest_path,
                    storage_dir,
                    name,
                    e_purpose.get().strip(),
                    e_basis.get().strip(),
                    e_tag.get().strip() or "manual",
                )
                _refresh_docs()
                utils.log_activity(f"Thêm mẫu văn bản thủ công: {name}")
                win.destroy()
            except Exception as ex:
                messagebox.showerror("Không thể thêm văn bản", str(ex), parent=win)
            
        win = tk.Toplevel(app)
        win.title("Thêm văn bản mới")
        win.geometry("400x300")
        f = ttk.Frame(win, padding=20)
        f.pack(fill="both", expand=True)
        tk.Label(f, text="Tên văn bản:").pack(anchor="w")
        e_name = tk.Entry(f, width=40); e_name.pack(pady=5)
        tk.Label(f, text="Chức năng / Mô tả:").pack(anchor="w")
        e_purpose = tk.Entry(f, width=40); e_purpose.pack(pady=5)
        tk.Label(f, text="Cơ sở pháp lý / mã văn bản:").pack(anchor="w")
        e_basis = tk.Entry(f, width=40); e_basis.pack(pady=5)
        tk.Label(f, text="Tag:").pack(anchor="w")
        e_tag = tk.Entry(f, width=20); e_tag.insert(0, "manual"); e_tag.pack(pady=5)
        tk.Button(f, text="Lưu", command=_save, bg="#388E3C", fg="white", width=15).pack(pady=15)

    def _run_scraper():
        confirm = messagebox.askyesno("Cập nhật", "Hệ thống sẽ kết nối và tải xuống hoặc cập nhật các văn bản mẫu chuẩn 2026 tự động. Tiếp tục?")
        if not confirm: return
        
        btn_scrape.config(state="disabled", text="Đang cập nhật...")
        app.update()
        
        def do_scrape():
            try:
                result = legal_vault.update_official_sources(
                    manifest_path,
                    storage_dir,
                    allow_online=bool(getattr(app, "settings", {}).get("online_document_fetch_enabled", False)),
                )
                def on_done():
                    _refresh_docs()
                    btn_scrape.config(state="normal", text="🌐 Cập nhật văn bản mẫu")
                    downloaded = result.get("downloaded", [])
                    errors = result.get("errors", [])
                    if downloaded:
                        msg = f"Đã cập nhật thành công {len(downloaded)} văn bản mẫu chính thức:\n" + "\n".join(downloaded)
                        if errors:
                            msg += "\n\nLỗi cần kiểm tra:\n" + "\n".join(str(error) for error in errors)
                        messagebox.showinfo("Thành công", msg)
                    elif errors:
                        messagebox.showwarning("Không cập nhật được", "\n".join(str(error) for error in errors))
                    else:
                        messagebox.showinfo("Thông báo", "Tất cả các văn bản mẫu đã có trong kho lưu trữ và còn hiệu lực.")
                app.after(0, on_done)
            except Exception as e:
                error_message = str(e)

                def on_fail(error_message=error_message):
                    btn_scrape.config(state="normal", text="🌐 Cập nhật văn bản mẫu")
                    messagebox.showerror("Lỗi", f"Không thể cập nhật văn bản: {error_message}")
                app.after(0, on_fail)
                
        threading.Thread(target=do_scrape, daemon=True).start()

    btn_f = tk.Frame(main_f, bg="#FFFFFF")
    btn_f.pack(side="top", fill="x", pady=10)
    
    tk.Button(btn_f, text="➕ Thêm văn bản", bg="#0288D1", fg="white", padx=10, command=_add_custom, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
    tk.Button(btn_f, text="❌ Xóa văn bản", bg="#D32F2F", fg="white", padx=10, command=_delete_doc, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
    tk.Button(btn_f, text="📥 Tải văn bản mẫu", bg="#1565C0", fg="white", padx=10, command=_copy_document, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
    tk.Button(btn_f, text="📂 Xem file", bg="#546E7A", fg="white", padx=10, command=_open_selected_file, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
    tk.Button(btn_f, text="Mở bằng...", bg="#455A64", fg="white", padx=10, command=_open_selected_with, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
    tk.Button(btn_f, text="Điền mẫu", bg="#00695C", fg="white", padx=10, command=_edit_selected, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
    tk.Button(btn_f, text="📤 Tải lên bản mới", bg="#2E7D32", fg="white", padx=10, command=_upload, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
    tk.Button(btn_f, text="🔍 Kiểm tra", bg="#FF9800", fg="white", padx=10, command=_check, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
    
    btn_scrape = tk.Button(btn_f, text="🌐 Cập nhật", bg="#7B1FA2", fg="white", padx=10, command=_run_scraper, font=("Segoe UI", 9, "bold"))
    btn_scrape.pack(side="left", padx=5)
    
    tk.Button(btn_f, text="📂 Thư mục gốc", bg="#455A64", fg="white", padx=10, command=_open_folder, font=("Segoe UI", 9, "bold")).pack(side="right", padx=5)

    # Put both scrollbars on the table. Long legal titles and status messages
    # must remain inspectable on small windows and at high display scaling.
    tree_holder.pack(side="top", fill="both", expand=True)
    tree_y = ttk.Scrollbar(tree_holder, orient="vertical", command=tree.yview)
    tree_x = ttk.Scrollbar(tree_holder, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=tree_y.set, xscrollcommand=tree_x.set)
    tree.grid(row=0, column=0, sticky="nsew")
    tree_y.grid(row=0, column=1, sticky="ns")
    tree_x.grid(row=1, column=0, sticky="ew")
    tree_holder.rowconfigure(0, weight=1)
    tree_holder.columnconfigure(0, weight=1)

# ── VSIC Industry Codes sub-tab ───────────────────────────
def build_vsic_subtab(app, sub_nb):
    tab = ttk.Frame(sub_nb)
    sub_nb.add(tab, text=app.lbl.get("sub_vsic", "Danh mục VSIC"))
    vsic = load_vsic()
    def _on_search(event=None):
        query = e_search.get().lower().strip()
        for i in tree.get_children(): tree.delete(i)
        count = 0
        for g_name in vsic:
            for it in vsic[g_name]:
                if query in it.get("vsic","").lower() or query in it.get("name","").lower():
                    tree.insert("","end", values=(it.get("vsic",""), it.get("name",""), it.get("tax_cat","")))
                    count += 1
        status.config(text=f"{count:,} mã ngành đang hiển thị" if count else "Không có dữ liệu VSIC. Kiểm tra file dữ liệu ứng dụng.")
    
    sf = ttk.Frame(tab); sf.pack(fill="x", padx=10, pady=5)
    tk.Label(sf, text="🔍 Tìm kiếm Ngành nghề (Mã hoặc Tên):", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
    e_search = tk.Entry(sf, width=40); e_search.pack(side="left", padx=5)
    e_search.bind("<KeyRelease>", _on_search)
    
    status = tk.Label(tab, text="", anchor="w", fg="#475569")
    status.pack(fill="x", padx=10, pady=(0, 4))
    tree_holder = ttk.Frame(tab)
    tree_holder.pack(fill="both", expand=True, padx=10, pady=(0, 8))
    tree = ttk.Treeview(tree_holder, columns=("v", "n", "t"), show="headings", height=12)
    for c,h,w in [("v","Mã Ngành",80),("n","Tên Ngành Nghề Kinh Doanh",400),("t","Thuế suất Thông tư 40",150)]:
        tree.heading(c, text=h); tree.column(c, width=w)
    tree_y = ttk.Scrollbar(tree_holder, orient="vertical", command=tree.yview)
    tree_x = ttk.Scrollbar(tree_holder, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=tree_y.set, xscrollcommand=tree_x.set)
    tree.grid(row=0, column=0, sticky="nsew")
    tree_y.grid(row=0, column=1, sticky="ns")
    tree_x.grid(row=1, column=0, sticky="ew")
    tree_holder.rowconfigure(0, weight=1)
    tree_holder.columnconfigure(0, weight=1)
    _on_search()

# ── ADVANCED AI AGENT TAB (v6.1 - Complete) ───────────────
def build_ai_tab(app, nb, lbl):
    """Offline AI assistant with profile memory and no HTTP/cloud calls."""
    tab = ttk.Frame(nb)
    nb.add(tab, text=lbl.get("sub_ai", "Trợ lý AI"))
    
    main_f = tk.Frame(tab, bg="#FFFFFF"); main_f.pack(fill="both", expand=True)
    HISTORY_FILE = "data/ai_history.json"
    store = ProfileStore("data/ai_profiles.json")

    hdr = tk.Frame(main_f, bg="#FFFFFF"); hdr.pack(fill="x", padx=10, pady=8)
    tk.Label(hdr, text="Trợ lý AI (Cục bộ & API)", font=("Segoe UI", 12, "bold"), bg="#FFFFFF", fg="#1565C0").pack(side="left")
    profile_var = tk.StringVar()
    cmb_profile = ttk.Combobox(hdr, textvariable=profile_var, width=30, state="readonly")
    cmb_profile.pack(side="left", padx=12)

    def _refresh_profiles():
        values = [p["name"] for p in store.list_profiles()]
        cmb_profile["values"] = values
        if values and not profile_var.get():
            profile_var.set(values[0])
    _refresh_profiles()

    def _active_profile_notes():
        for profile in store.list_profiles():
            if profile["name"] == profile_var.get():
                return profile.get("notes", "")
        return ""

    def _add_profile():
        win = tk.Toplevel(app)
        win.title("Tạo profile AI")
        win.geometry("460x260")
        f = ttk.Frame(win, padding=14); f.pack(fill="both", expand=True)
        tk.Label(f, text="Tên profile:").pack(anchor="w")
        e_name = tk.Entry(f, width=52); e_name.pack(fill="x", pady=4)
        tk.Label(f, text="Ghi nhớ / phạm vi công việc:").pack(anchor="w")
        e_notes = tk.Text(f, height=6, wrap="word"); e_notes.pack(fill="both", expand=True, pady=4)
        _add_copy_menu(e_name); _add_copy_menu(e_notes)
        def _save():
            try:
                store.add_profile(e_name.get(), e_notes.get("1.0", "end"))
                _refresh_profiles()
                win.destroy()
            except ProfileLimitError as ex:
                messagebox.showwarning("Giới hạn profile", str(ex))
            except Exception as ex:
                messagebox.showerror("Lỗi", str(ex))
        tk.Button(f, text="Lưu profile", command=_save, bg="#388E3C", fg="white").pack(pady=6)
    tk.Button(hdr, text="➕ Profile", command=_add_profile, bg="#2E7D32", fg="white").pack(side="left")

    # AI Config Settings
    cfg_f = tk.Frame(main_f, bg="#F0F4F8", bd=1, relief="solid")
    cfg_f.pack(fill="x", padx=10, pady=4)
    cfg_f.columnconfigure(4, weight=1)
    ai_online_var = tk.BooleanVar(value=bool(app.settings.get("ai_online_enabled", False)))
    tk.Checkbutton(cfg_f, text="Bật AI online (opt-in)", variable=ai_online_var, bg="#F0F4F8").grid(row=0, column=0, padx=8, pady=5, sticky="w")
    tk.Label(cfg_f, text="Nền tảng:", bg="#F0F4F8").grid(row=0, column=1, padx=(8, 3), pady=5, sticky="e")
    
    provider_var = tk.StringVar(value=app.settings.get("ai_provider", "offline"))
    cmb_prov = ttk.Combobox(cfg_f, textvariable=provider_var, values=["offline", "ollama", "groq", "huggingface", "custom", "gemini", "claude", "api"], state="readonly", width=12)
    cmb_prov.grid(row=0, column=2, padx=3, pady=5, sticky="w")
    
    tk.Label(cfg_f, text="Model:", bg="#F0F4F8").grid(row=0, column=3, padx=(8, 3), pady=5, sticky="e")
    model_var = tk.StringVar(value=app.settings.get("ai_model", "llama3-8b-8192"))
    tk.Entry(cfg_f, textvariable=model_var, width=24).grid(row=0, column=4, padx=3, pady=5, sticky="ew")
    
    tk.Label(cfg_f, text="API Key:", bg="#F0F4F8").grid(row=1, column=0, padx=8, pady=5, sticky="e")
    raw_api_key = str(app.settings.get("ai_api_key", ""))
    api_key_var = tk.StringVar(value=decrypt_value(raw_api_key) or raw_api_key)
    tk.Entry(cfg_f, textvariable=api_key_var, width=30, show="*").grid(row=1, column=1, columnspan=4, padx=3, pady=5, sticky="ew")

    endpoint_f = tk.Frame(main_f, bg="#F0F4F8", bd=1, relief="solid"); endpoint_f.pack(fill="x", padx=10, pady=2)
    tk.Label(endpoint_f, text="Custom AI Base URL:", bg="#F0F4F8").pack(side="left", padx=5)
    endpoint_var = tk.StringVar(value=app.settings.get("ai_base_url", ""))
    tk.Entry(endpoint_f, textvariable=endpoint_var, width=62).pack(side="left", padx=5, fill="x", expand=True)
    
    def _save_ai_cfg():
        app.settings["ai_online_enabled"] = ai_online_var.get()
        app.settings["ai_provider"] = provider_var.get()
        app.settings["ai_model"] = model_var.get()
        app.settings["ai_api_key"] = encrypt_value(api_key_var.get().strip())
        app.settings["ai_base_url"] = endpoint_var.get().strip()
        import config
        config.save_settings(app.settings)
        messagebox.showinfo("Lưu", "Đã lưu cấu hình AI!")
        
    tk.Button(cfg_f, text="Lưu cấu hình", command=_save_ai_cfg, bg="#FF9800", fg="white", font=("Segoe UI", 8, "bold")).grid(row=1, column=5, padx=8, pady=4, sticky="e")

    guide = tk.Label(
        main_f,
        text="Workflow: AI mặc định chạy offline và đọc dữ liệu nội bộ (Khách hàng, Kho, Lịch sử) làm context.\nOnline/API chỉ hoạt động khi bật opt-in và cấu hình key/model.",
        bg="#F8F9FA", fg="#333", justify="left", wraplength=900, padx=10, pady=4
    )
    guide.pack(fill="x", padx=10)
    _add_copy_menu(guide)

    chat_f = tk.Frame(main_f, bg="#F8F9FA")
    chat_f.pack(fill="both", expand=True, padx=10, pady=6)
    txt_chat = tk.Text(chat_f, wrap="word", font=("Segoe UI", 10), bg="#F8F9FA", relief="flat", height=20)
    txt_chat.tag_config("user_box", background="#E3F2FD", spacing1=5, spacing3=5, lmargin1=15)
    txt_chat.tag_config("ai_box", background="#FFFFFF", spacing1=5, spacing3=5, lmargin1=10)
    chat_scroll = ttk.Scrollbar(chat_f, orient="vertical", command=txt_chat.yview)
    txt_chat.configure(yscrollcommand=chat_scroll.set)
    txt_chat.pack(side="left", fill="both", expand=True)
    chat_scroll.pack(side="right", fill="y")
    _add_copy_menu(txt_chat)

    inp_f = tk.Frame(main_f, bg="#FFFFFF", bd=1, relief="solid"); inp_f.pack(fill="x", padx=10, pady=6)
    ent_msg = tk.Entry(inp_f, font=("Segoe UI", 10), relief="flat")
    ent_msg.pack(side="left", fill="x", expand=True, padx=5, pady=5)
    _add_copy_menu(ent_msg)

    def log_msg(sender, msg, style="ai"):
        txt_chat.config(state="normal")
        txt_chat.insert("end", f"{sender}\n", f"{style}_box")
        txt_chat.insert("end", f"{msg}\n\n", f"{style}_box")
        txt_chat.see("end")
        try:
            os.makedirs("data", exist_ok=True)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump({"chat": txt_chat.get("1.0", "end")}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def send_msg(e=None):
        txt = ent_msg.get().strip()
        if not txt: return
        ent_msg.delete(0, "end")
        log_msg("Bạn", txt, "user")
        
        # Display loading indicator
        txt_chat.config(state="normal")
        txt_chat.insert("end", "AI\n", "ai_box")
        placeholder_start = txt_chat.index("end-1c")
        txt_chat.insert("end", "⏳ Đang xử lý...\n\n", "ai_box")
        placeholder_end = txt_chat.index("end-1c")
        txt_chat.see("end")
        txt_chat.config(state="disabled")

        def run_query():
            try:
                from ai.hybrid_router import query_ai
                ans = query_ai(txt, _active_profile_notes(), app.db)
            except Exception as ex:
                ans = f"Lỗi kết nối Trợ lý AI: {ex}"
            
            def cb():
                txt_chat.config(state="normal")
                txt_chat.delete(placeholder_start, placeholder_end)
                txt_chat.insert(placeholder_start, f"{ans}\n\n", "ai_box")
                txt_chat.see("end")
                txt_chat.config(state="disabled")
                
                try:
                    os.makedirs("data", exist_ok=True)
                    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                        json.dump({"chat": txt_chat.get("1.0", "end")}, f, ensure_ascii=False, indent=2)
                except:
                    pass

            app.after(0, cb)

        threading.Thread(target=run_query, daemon=True).start()

    tk.Button(inp_f, text="Gửi", command=send_msg, bg="#1565C0", fg="white", font=("Segoe UI", 9, "bold")).pack(side="right", padx=5)
    ent_msg.bind("<Return>", send_msg)

    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                txt_chat.insert("end", json.load(f).get("chat", ""))
                txt_chat.see("end")
        except Exception:
            pass

# ── Payroll & HR Tab (ENHANCED 2026 - MISA Standard) ──────────────────────
def build_payroll_tab(app, nb, lbl):
    tab = ttk.Frame(nb)
    nb.add(tab, text=lbl.get("tab_payroll", "Nhân sự"))
    def EMP_FILE(): return "data/employees.json"
    def TS_FILE(): return "data/timesheets.json"
    
    def get_file_path(fpath):
        if getattr(app, 'demo_active', False):
            name, ext = os.path.splitext(fpath)
            return f"{name}_demo{ext}"
        return fpath

    def load_json(fpath):
        actual_path = get_file_path(fpath)
        if os.path.exists(actual_path):
            try:
                with open(actual_path, "r", encoding="utf-8") as f: return json.load(f)
            except: pass
        return []

    def save_json(fpath, data):
        actual_path = get_file_path(fpath)
        os.makedirs("data", exist_ok=True)
        with open(actual_path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

    h_f = ttk.Frame(tab); h_f.pack(fill="x")
    tk.Label(h_f, text="👥 QUẢN LÝ NHÂN SỰ & BẢNG LƯƠNG (CHUẨN 2026)", font=("Segoe UI", 11, "bold")).pack(side="left", padx=15, pady=5)
    tk.Button(h_f, text="❓ Trợ giúp", command=lambda: messagebox.showinfo("Trợ giúp", "Hệ thống chuẩn: Hồ sơ -> Chấm công -> Tính lương & Quyết toán. Giờ làm thêm cần nhập theo từng ngày và đánh dấu đã được phê duyệt trước khi tính lương."), relief="flat", fg="#1565C0").pack(side="right", padx=15)
    
    # Sub-notebook for HR modules
    hr_nb = ttk.Notebook(tab)
    hr_nb.pack(fill="both", expand=True, padx=10, pady=10)

    # --- TAB 1: HỒ SƠ NHÂN SỰ ---
    t_profile = ttk.Frame(hr_nb); hr_nb.add(t_profile, text=lbl.get("sub_profiles", "Hồ sơ Nhân sự"))
    
    p_left = ttk.LabelFrame(t_profile, text="Danh sách Cán bộ/Nhân viên")
    p_left.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    
    cols_prof = ("code", "name", "role", "sal", "allow", "deps")
    tree_prof = ttk.Treeview(p_left, columns=cols_prof, show="headings", height=15)
    for c, h, w in zip(cols_prof, ["Mã NV", "Họ Tên", "Chức vụ", "Lương CB", "Phụ cấp", "Số NPT"], [80, 150, 120, 100, 100, 60]):
        tree_prof.heading(c, text=h); tree_prof.column(c, width=w)
    tree_prof.pack(fill="both", expand=True, padx=5, pady=5)
    
    p_right = ttk.LabelFrame(t_profile, text="Thông tin chi tiết")
    p_right.pack(side="right", fill="y", padx=5, pady=5)
    
    def update_role_combobox():
        roles = set([
            "Giám đốc", "Phó Giám đốc", "Kế toán trưởng", "Kế toán tổng hợp", "Kế toán viên",
            "Trưởng phòng Kinh doanh", "Trưởng phòng Nhân sự", "Nhân viên bán hàng",
            "Nhân viên kỹ thuật", "Nhân viên kho", "Nhân viên văn phòng", "Lái xe", "Bảo vệ"
        ])
        for emp in load_json(EMP_FILE()):
            r = emp.get("role", "").strip()
            if r and r != "Thêm chức danh...":
                roles.add(r)
        combo_vals = sorted(list(roles)) + ["Thêm chức danh..."]
        ent_prof["role"]["values"] = combo_vals

    def _check_add_role(event):
        combo = event.widget
        if combo.get() == "Thêm chức danh...":
            from tkinter import simpledialog
            new_role = simpledialog.askstring("Thêm chức danh (Add Role)", "Nhập tên chức danh mới (Enter position name):")
            if new_role:
                new_role = new_role.strip()
                if new_role:
                    vals = list(combo["values"])
                    if "Thêm chức danh..." in vals:
                        vals.remove("Thêm chức danh...")
                    if new_role not in vals:
                        vals.append(new_role)
                    vals = sorted(vals) + ["Thêm chức danh..."]
                    combo["values"] = vals
                    combo.set(new_role)
                else:
                    combo.set("")
            else:
                combo.set("")

    fields_prof = [("Mã NV:", "code"), ("Họ Tên:", "name"), ("Chức vụ:", "role"), ("Lương Cơ bản:", "salary"), ("Phụ cấp định kỳ:", "allowance"), ("Người phụ thuộc:", "dependents")]
    ent_prof = {}
    for i, (lbl_txt, key) in enumerate(fields_prof):
        tk.Label(p_right, text=lbl_txt).grid(row=i, column=0, padx=5, pady=5, sticky="e")
        if key == "role":
            e = ttk.Combobox(p_right, width=18, state="readonly")
            e.bind("<<ComboboxSelected>>", _check_add_role)
        else:
            e = tk.Entry(p_right, width=20)
            if key in ["salary", "allowance", "dependents"]: e.insert(0, "0")
        e.grid(row=i, column=1, padx=5, pady=5, sticky="w")
        ent_prof[key] = e

    def refresh_prof():
        for i in tree_prof.get_children(): tree_prof.delete(i)
        for e in load_json(EMP_FILE()):
            tree_prof.insert("", "end", values=(e.get("code",""), e.get("name",""), e.get("role",""), f"{float(e.get('salary',0)):,.0f}", f"{float(e.get('allowance',0)):,.0f}", e.get("dependents","0")))
        update_role_combobox()

    def save_prof():
        data = load_json(EMP_FILE())
        new_e = {k: e.get() for k, e in ent_prof.items()}
        if not new_e['code']: return messagebox.showwarning("Lỗi", "Nhập Mã NV")
        data = [x for x in data if x['code'] != new_e['code']]
        data.append(new_e); save_json(EMP_FILE(), data); refresh_prof()
        messagebox.showinfo("Thành công", "Đã lưu hồ sơ!")

    tk.Button(p_right, text="💾 Lưu Hồ sơ", command=save_prof, bg="#388E3C", fg="white", width=20).grid(row=len(fields_prof), column=0, columnspan=2, pady=15)
    refresh_prof()

    # --- TAB 2: CHẤM CÔNG ---
    t_time = ttk.Frame(hr_nb); hr_nb.add(t_time, text=lbl.get("sub_timesheets", "Bảng Chấm công"))
    
    t_top = ttk.Frame(t_time); t_top.pack(fill="x", padx=5, pady=5)
    tk.Label(t_top, text="Tháng/Năm:").pack(side="left")
    ent_month = tk.Entry(t_top, width=10); ent_month.insert(0, datetime.datetime.now().strftime("%m/%Y"))
    ent_month.pack(side="left", padx=5)
    tk.Label(t_top, text="Số ngày công chuẩn:").pack(side="left", padx=(20,5))
    ent_std_days = tk.Entry(t_top, width=5); ent_std_days.insert(0, "26")
    ent_std_days.pack(side="left")
    
    t_mid = ttk.Frame(t_time); t_mid.pack(fill="both", expand=True, padx=5, pady=5)
    table_frame = ttk.Frame(t_mid)
    table_frame.pack(fill="both", expand=True)
    cols_ts = (
        "code", "name", "work_days", "standard_hours", "ot_hours",
        "ot_weekend_hours", "ot_holiday_hours", "ot_approved", "ot_reason", "advance",
    )
    tree_ts = ttk.Treeview(table_frame, columns=cols_ts, show="headings")
    for c, h, w in zip(
        cols_ts,
        ["Mã NV", "Họ Tên", "Ngày làm việc", "Giờ chuẩn", "OT thường", "OT cuối tuần", "OT ngày lễ", "OT duyệt?", "Lý do OT", "Tạm ứng"],
        [80, 150, 105, 90, 90, 105, 95, 85, 180, 110],
    ):
        tree_ts.heading(c, text=h); tree_ts.column(c, width=w)
    tree_y = ttk.Scrollbar(table_frame, orient="vertical", command=tree_ts.yview)
    tree_x = ttk.Scrollbar(table_frame, orient="horizontal", command=tree_ts.xview)
    tree_ts.configure(yscrollcommand=tree_y.set, xscrollcommand=tree_x.set)
    tree_ts.grid(row=0, column=0, sticky="nsew")
    tree_y.grid(row=0, column=1, sticky="ns")
    tree_x.grid(row=1, column=0, sticky="ew")
    table_frame.rowconfigure(0, weight=1)
    table_frame.columnconfigure(0, weight=1)

    ts_summary = tk.Label(t_time, text="", anchor="w", fg="#475569", wraplength=900, justify="left")
    ts_summary.pack(fill="x", padx=8, pady=(0, 3))

    def refresh_ts():
        for i in tree_ts.get_children(): tree_ts.delete(i)
        emps = load_json(EMP_FILE())
        ts_data = load_json(TS_FILE())
        month = ent_month.get()
        month_ts = {t["code"]: t for t in ts_data if t.get("month") == month}
        total_ot = 0.0
        pending = 0
        employees_with_ot = 0
        
        for e in emps:
            c = e.get("code", "")
            rec = month_ts.get(c, {})
            ot_ok = "Có" if str(rec.get("ot_approved", "")).lower() in ("1", "true", "yes", "có", "co") else "Không"
            regular_ot = float(rec.get("ot_hours", 0) or 0)
            weekend_ot = float(rec.get("ot_weekend_hours", 0) or 0)
            holiday_ot = float(rec.get("ot_holiday_hours", 0) or 0)
            row_ot = regular_ot + weekend_ot + holiday_ot
            total_ot += row_ot
            if row_ot > 0:
                employees_with_ot += 1
                if ot_ok != "Có":
                    pending += 1
            tree_ts.insert("", "end", values=(
                c,
                e.get("name", ""),
                rec.get("work_days", 26),
                rec.get("standard_hours", 208),
                rec.get("ot_hours", 0),
                rec.get("ot_weekend_hours", 0),
                rec.get("ot_holiday_hours", 0),
                ot_ok,
                rec.get("ot_reason", ""),
                rec.get("advance", 0),
            ))
        limit_note = " | Vượt ngưỡng theo dõi tháng" if total_ot > MONTHLY_OVERTIME_CAP_HOURS else ""
        ts_summary.config(
            text=f"Tháng {month}: {len(emps)} nhân viên | Tổng OT: {total_ot:g} giờ | "
                 f"Có OT: {employees_with_ot} | Chờ duyệt: {pending}{limit_note}"
        )

    def save_ts_row(event):
        # Quick inline edit simulation
        sel = tree_ts.selection()
        if not sel: return
        item = tree_ts.item(sel[0])
        code = item['values'][0]
        
        # In a real grid this would be inline. Here we popup a simple dialog.
        import tkinter.simpledialog as sd
        wd = sd.askfloat("Chấm công", f"Ngày làm việc cho {code}:", initialvalue=item['values'][2])
        if wd is None: return
        std_hours = sd.askfloat("Chấm công", f"Giờ công chuẩn trong tháng cho {code}:", initialvalue=item['values'][3])
        if std_hours is None: return
        ot = sd.askfloat("Tăng ca ngày thường", f"Giờ tăng ca ngày thường cho {code}:", initialvalue=item['values'][4])
        if ot is None: return
        ot_weekend = sd.askfloat("Tăng ca cuối tuần", f"Giờ tăng ca cuối tuần cho {code}:", initialvalue=item['values'][5])
        if ot_weekend is None: return
        ot_holiday = sd.askfloat("Tăng ca ngày lễ", f"Giờ tăng ca ngày lễ cho {code}:", initialvalue=item['values'][6])
        if ot_holiday is None: return
        total_ot = (ot or 0) + (ot_weekend or 0) + (ot_holiday or 0)
        ot_approved = messagebox.askyesno("Duyệt tăng ca", f"Tổng {total_ot:g} giờ tăng ca của {code} đã được duyệt/chấp thuận?")
        ot_reason = sd.askstring("Lý do tăng ca", f"Lý do tăng ca cho {code}:", initialvalue=item['values'][8] if len(item['values']) > 8 else "")
        adv = sd.askfloat("Tạm ứng", f"Tạm ứng cho {code} (VND):", initialvalue=item['values'][9])
        
        ts_data = load_json(TS_FILE())
        month = ent_month.get()
        # Remove old record for this month/code
        ts_data = [t for t in ts_data if not (t.get("code") == code and t.get("month") == month)]
        ts_data.append({
            "month": month,
            "code": code,
            "work_days": wd,
            "standard_hours": std_hours,
            "ot_hours": ot or 0,
            "ot_weekend_hours": ot_weekend or 0,
            "ot_holiday_hours": ot_holiday or 0,
            "ot_approved": ot_approved,
            "ot_reason": ot_reason or "",
            "advance": adv or 0,
        })
        save_json(TS_FILE(), ts_data)
        refresh_ts()

    tree_ts.bind("<Double-1>", save_ts_row)
    tk.Button(t_top, text="Tải danh sách", command=refresh_ts, bg="#1565C0", fg="white").pack(side="right")
    tk.Label(t_time, text="* Nhấp đúp vào dòng để nhập ngày công, OT ngày thường/cuối tuần/ngày lễ, duyệt OT, lý do và tạm ứng.", fg="#555", wraplength=900, justify="left").pack(anchor="w", padx=8, pady=(0, 5))
    
    # --- TAB 3: BẢNG LƯƠNG & QUYẾT TOÁN ---
    t_pay = ttk.Frame(hr_nb); hr_nb.add(t_pay, text=lbl.get("sub_payroll_calc", "Tính lương & Thuế thu nhập cá nhân"))
    
    p_top = ttk.Frame(t_pay); p_top.pack(fill="x", padx=5, pady=5)
    tk.Button(p_top, text="▶ Tính Lương Tháng Này", command=lambda: calc_payroll(), bg="#D84315", fg="white", font=("Segoe UI", 9, "bold")).pack(side="left")
    tk.Button(p_top, text="Xuất Phiếu Lương (Payslips)", command=lambda: export_payslips(), bg="#455A64", fg="white").pack(side="right", padx=5)

    cols_pay = ("code", "name", "gross", "ot_pay", "ins", "pit", "advance", "net", "warnings")
    tree_pay = ttk.Treeview(t_pay, columns=cols_pay, show="headings")
    for c, h, w in zip(
        cols_pay,
        ["Mã NV", "Họ Tên", "Tổng Thu nhập", "Tiền OT", "Trừ BH (10.5%)", "Thuế TNCN", "Trừ Tạm ứng", "THỰC LĨNH", "Cảnh báo"],
        [75, 140, 120, 110, 110, 110, 110, 120, 260],
    ):
        tree_pay.heading(c, text=h); tree_pay.column(c, width=w)
    tree_pay.pack(fill="both", expand=True, padx=5, pady=5)

    def calc_payroll():
        for i in tree_pay.get_children(): tree_pay.delete(i)
        emps = load_json(EMP_FILE())
        ts_data = load_json(TS_FILE())
        month = ent_month.get()
        std_days = float(ent_std_days.get() or 26)
        
        for row in calculate_monthly_payroll(emps, ts_data, month, standard_days=std_days):
            warnings = "; ".join(row["warnings"])
            tree_pay.insert("", "end", values=(
                row["code"],
                row["name"],
                f"{row['gross']:,.0f}",
                f"{row['ot_pay']:,.0f}",
                f"{row['insurance']:,.0f}",
                f"{row['pit']:,.0f}",
                f"{row['advance']:,.0f}",
                f"{row['net']:,.0f}",
                warnings,
            ))
            
    def export_payslips():
        rows = [tree_pay.item(item, "values") for item in tree_pay.get_children()]
        if not rows:
            return messagebox.showwarning("Chưa có dữ liệu", "Hãy tính lương trước khi xuất phiếu lương.")

        month = ent_month.get().strip() or "ky-luong"
        default_name = f"phieu_luong_{month.replace('/', '-')}.xlsx"
        output_path = filedialog.asksaveasfilename(
            title="Xuất bảng lương Excel",
            initialdir=os.path.join("exports", "payslips"),
            initialfile=default_name,
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
        )
        if not output_path:
            return

        try:
            import pandas as pd

            columns = [
                "Mã nhân viên", "Họ tên", "Tổng thu nhập", "Tiền làm thêm",
                "Bảo hiểm người lao động", "Thuế TNCN", "Tạm ứng",
                "Thực lĩnh", "Cảnh báo",
            ]
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            pd.DataFrame(rows, columns=columns).to_excel(output_path, index=False, sheet_name="Bảng lương")
            messagebox.showinfo("Xuất bảng lương", f"Đã xuất {len(rows)} phiếu lương:\n{output_path}")
        except Exception as ex:
            messagebox.showerror("Không thể xuất bảng lương", str(ex))
