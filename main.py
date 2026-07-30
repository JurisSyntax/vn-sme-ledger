import tkinter as tk
from tkinter import ttk, messagebox
import datetime, os, json
import db, tax_engine, analytics, sync, utils
import config, tabs_extra, debt_manager
from core.validation import ClientValidationError, InvoiceValidationError, validate_invoice_payload
from demo.simulator import seed_agri_demo
from demo.log_rotator import DemoLogRotator
from vas_mapper import auto_vas_lines, VAS_RULES
from presets_loader import get_vas_rules
from core.encryption import encrypt_value, decrypt_value
from core.ui_layout import dashboard_layout, form_column_count


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text: return
        x, y, _cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify="left",
                         background="#FFFFE1", relief="solid", borderwidth=1,
                         font=("Segoe UI", 9, "normal"), padx=5, pady=2)
        label.pack()

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw: tw.destroy()

class NotebookPlaceholder(tk.Frame):
    def __init__(self, master, change_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.tabs_dict = {}
        self.tab_names = []
        self.current_frame = None
        self.change_callback = change_callback

    def add(self, frame, text):
        self.tabs_dict[text] = frame
        self.tab_names.append(text)
        frame.pack_forget()

    def select(self, target):
        target_frame = None
        if isinstance(target, int):
            if 0 <= target < len(self.tab_names):
                text = self.tab_names[target]
                target_frame = self.tabs_dict[text]
        elif isinstance(target, str):
            if target in self.tabs_dict:
                target_frame = self.tabs_dict[target]
            else:
                # Substring matching fallback (e.g. "🏠" matches "🏠 Trang chủ (Home)")
                for k, f in self.tabs_dict.items():
                    if target in k:
                        target_frame = f
                        break
                if not target_frame:
                    for f in self.tabs_dict.values():
                        if str(f) == target:
                            target_frame = f
                            break
        else:
            target_frame = target

        if target_frame:
            if self.current_frame:
                self.current_frame.pack_forget()
            self.current_frame = target_frame
            target_frame.pack(fill="both", expand=True)
            if self.change_callback:
                class DummyEvent:
                    widget = self
                self.change_callback(DummyEvent())

    def tabs(self):
        return [str(f) for f in self.tabs_dict.values()]

    def tab(self, tab_id, option=None, **kwargs):
        if isinstance(tab_id, int):
            if 0 <= tab_id < len(self.tab_names):
                name = self.tab_names[tab_id]
                if option == "text":
                    return name
        for name, f in self.tabs_dict.items():
            if str(f) == tab_id or f == tab_id:
                if option == "text":
                    return name
        return ""

    def index(self, query):
        if query == "current":
            return str(self.current_frame) if self.current_frame else ""
        if isinstance(query, int) and 0 <= query < len(self.tab_names):
            return str(self.tabs_dict[self.tab_names[query]])
        if query in self.tab_names:
            return self.tab_names.index(query)
        # Substring matching fallback
        for i, name in enumerate(self.tab_names):
            if isinstance(query, str) and query in name:
                return i
        for i, f in enumerate(self.tabs_dict.values()):
            if str(f) == query or f == query:
                return i
        return query

    def current_index(self):
        if self.current_frame:
            for i, f in enumerate(self.tabs_dict.values()):
                if f == self.current_frame:
                    return i
        return 0

    def bind(self, event, callback, add=None):
        if event == "<<NotebookTabChanged>>":
            self.change_callback = callback
        else:
            super().bind(event, callback, add)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.settings = config.load_settings()
        self.lbl = config.get_labels(self.settings)
        self.title(config.APP_DISPLAY_NAME)
        self.geometry("1400x880")
        self.minsize(1250, 800)
        
        # Try to set icon
        for icon_name in ["logo.ico", "logo_fixed.png", "logo.png"]:
            p = utils.get_resource_path(icon_name)
            if os.path.exists(p):
                try:
                    if p.endswith(".ico"):
                        self.iconbitmap(p)
                    else:
                        img = tk.PhotoImage(file=p)
                        self.iconphoto(False, img)
                    break
                except: pass
                
        self._theme = self.settings.get("theme", "light")
        self.db = db.init_db("data/ledger.db")
        self.tax = tax_engine.load_tax()
        self.editing_entry_id = None
        self._current_inv_client_id = None
        self._sub_tips = {}
        self._current_tip = None
        self._current_tip_idx = -1
        self._browser_visible = False
        
        # ── APPLY MODERN UI STYLE (ĐÔNG HỒ THEME) ──────────────────
        style = ttk.Style()
        style.theme_use('clam')
        
        bg_color = "#F8F9FA"  # Soft off-white
        fg_color = "#0F172A"  # Dark Slate 900
        accent_color = "#00796B"  # Đông Hồ Teal Green
        deep_blue = "#1565C0"  # Đông Hồ Deep Blue
        
        self.configure(bg=bg_color)
        style.configure(".", font=("Segoe UI", 10), background="#FFFFFF", foreground=fg_color)
        
        # ── GLOBAL MOUSEWHEEL FIX (WINDOWS) ───────────────────────
        def _on_mousewheel(event):
            widget = self.winfo_containing(event.x_root, event.y_root)
            if widget:
                try:
                    widget.yview_scroll(int(-1*(event.delta/120)), "units")
                except:
                    pass
        self.bind_all("<MouseWheel>", _on_mousewheel)
        
        style.configure("TFrame", background="#FFFFFF")
        style.configure("TLabelframe", background="#FFFFFF", font=("Segoe UI", 10, "bold"), foreground=accent_color, bordercolor="#E2E8F0")
        style.configure("TLabelframe.Label", background="#FFFFFF", font=("Segoe UI", 10, "bold"), foreground=accent_color)
        
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=32, background="#FFFFFF", fieldbackground="#FFFFFF", borderwidth=0)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#E2E8F0", foreground=fg_color, padding=6)
        style.map("Treeview", background=[("selected", "#E0F2F1")], foreground=[("selected", "#004D40")])
        
        style.configure("TCombobox", padding=6)
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6, background="#E2E8F0")
        style.map("TButton", background=[("active", "#CBD5E1")])
        
        # ── MAIN LAYOUT CONTAINERS ─────────────────────────
        self.main_container = tk.Frame(self, bg=bg_color)
        self.main_container.pack(fill="both", expand=True)
        
        # Left Sidebar (Nav)
        self.frame_sidebar = tk.Frame(self.main_container, bg="#1E293B", width=220)
        self.frame_sidebar.pack(side="left", fill="y")
        self.frame_sidebar.pack_propagate(False)
        
        # Right Container
        self.right_container = tk.Frame(self.main_container, bg=bg_color)
        self.right_container.pack(side="right", fill="both", expand=True)
        
        # ── TOP BAR (inside right container) ──────────────────────────
        top = ttk.Frame(self.right_container)
        top.pack(fill="x", padx=10, pady=8)
        
        self._lbl_niche_icon = tk.Label(top, text="🏢", font=("Segoe UI", 16), bg="#FFFFFF")
        self._lbl_niche_icon.pack(side="left", padx=(5, 0))
        
        tk.Label(top, text=self.lbl["niche_label"], font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg=accent_color).pack(side="left", padx=(5, 0))
        self.niche_var = tk.StringVar(value="photocopy_print")
        niches = [
            "photocopy_print", "retail_grocery", "services_consulting", "clinic_pharmacy", 
            "fnb_cafe", "real_estate", "construction", "transport_logistics", 
            "education_training", "general_trade", "vics_2025_mfg", "vics_2025_agri", "vics_2025_it"
        ]
        self.cmb_niche = ttk.Combobox(top, textvariable=self.niche_var, values=niches, state="readonly", width=22)
        self.cmb_niche.pack(side="left", padx=6)
        self.cmb_niche.bind("<<ComboboxSelected>>", self._change_niche)
        
        self._change_niche()
        
        # Company quick-info bar
        co_info = ttk.Frame(top)
        co_info.pack(side="right", padx=8)
        self._lbl_co = tk.Label(co_info, text="", fg=deep_blue, font=("Segoe UI", 9, "bold"), bg="#FFFFFF")
        self._lbl_co.pack(side="right")
        self._refresh_co_label()
        
        # ── PANED WINDOW ──
        self.paned = ttk.PanedWindow(self.right_container, orient="horizontal")
        self.paned.pack(fill="both", expand=True, padx=8, pady=4)
        
        # Left Panel of PanedWindow (File Browser)
        self.frame_browser = ttk.Frame(self.paned)
        self.paned.add(self.frame_browser, weight=0)
        
        br_top = ttk.Frame(self.frame_browser)
        br_top.pack(fill="x")
        tk.Label(br_top, text="📁 File Browser", font=("Segoe UI", 9, "bold")).pack(side="left", padx=4, pady=4)
        tk.Button(br_top, text="❌", command=self._toggle_browser, relief="flat", bg="#FFFFFF").pack(side="right", padx=4)
        
        self.tree_files = ttk.Treeview(self.frame_browser, show="tree", selectmode="browse")
        sb_files = ttk.Scrollbar(self.frame_browser, orient="vertical", command=self.tree_files.yview)
        self.tree_files.configure(yscrollcommand=sb_files.set)
        self.tree_files.pack(fill="both", expand=True)
        sb_files.pack(side="right", fill="y")
        self.tree_files.bind("<Double-1>", self._on_file_double_click)
        self._populate_file_tree()
        
        # Right Panel of PanedWindow (NotebookPlaceholder Container)
        self.nb = NotebookPlaceholder(self.paned)
        self.paned.add(self.nb, weight=1)
        
        # Add toggle button to Top Bar
        self._btn_toggle_br = tk.Button(top, text="📂 Hiện File Browser", command=self._toggle_browser,
                                        bg="#E2E8F0", fg="#0F172A", font=("Segoe UI", 9), relief="flat")
        self._btn_toggle_br.pack(side="left", padx=10)

        # Build subframes
        self._build_home_tab()
        self._build_ledger_tab()
        self._build_dirs_tab()
        self._build_invoice_tab()
        self._build_invoice_history_tab()
        self._build_history_tab()
        self._build_reports_tab()
        self._build_analytics_tab()
        self._build_payroll_tab()
        self._build_tools_tab()
        self._build_settings_tab()
        
        # Build Left Navigation Sidebar items
        self._build_sidebar()
        
        # ── STATUS BAR ──
        self.status_bar = tk.Frame(self.right_container, bg="#FFFFFF", bd=1, relief="flat")
        self.status_bar.pack(side="bottom", fill="x")
        self.lbl_status = tk.Label(self.status_bar, text="Trạng thái: Sẵn sàng", font=("Segoe UI", 10), bg="#FFFFFF", fg=accent_color)
        self.lbl_status.pack(side="left", padx=15, pady=3)
        
        btn_help = tk.Button(self.status_bar, text="❔ Trợ giúp nhanh", command=lambda: self.nb.select("🛠️"), 
                             bg="#F1F5F9", fg=deep_blue, font=("Segoe UI", 9, "bold"), relief="flat", padx=10)
        btn_help.pack(side="right", padx=10)
        
        credit_status = tk.Label(self.status_bar, text="Tác giả: Du Quốc Hoàng Kim | GitHub: https://github.com/JurisSyntax", font=("Segoe UI", 9), bg="#FFFFFF", fg="#64748B")
        credit_status.pack(side="right", padx=15)
        credit_status.bind("<Button-3>", lambda e, w=credit_status: (self.clipboard_clear(), self.clipboard_append(w.cget("text"))))

        # Tab Hover Descriptions (Tooltips)
        self.tab_desc = {
            0: "🏠 Trang chủ", 1: "📑 Chứng từ", 2: "🗂️ Danh mục",
            3: "🧾 Hóa đơn", 4: "🕒 Sổ cái", 5: "📊 Báo cáo",
            6: "📈 Phân tích", 7: "👥 Nhân sự", 8: "🛠️ Công cụ", 9: "⚙️ Cài đặt"
        }
        self.nb.bind("<Motion>", self._on_nb_motion)
        self.nb.bind("<Leave>", self._on_nb_leave)

        # Global Hotkeys & Mouse Wheel
        self.bind("<Control-b>", lambda e: self._toggle_browser())
        self.bind("<Control-B>", lambda e: self._toggle_browser())
        self.bind_all("<MouseWheel>", self._on_mousewheel)

        # Log activity
        utils.log_activity("Ứng dụng khởi động")
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_change)

        # Hide browser by default
        self._browser_visible = True
        self._toggle_browser()

        # 4. Finalize UI and bind global events
        self._bind_global_copy_paste(self)
        
        # Trigger update check on startup in a background thread
        import threading
        def run_update():
            if not self.settings.get("update_check_enabled", False):
                return
            try:
                self.after(2000, lambda: utils.prompt_update(self))
            except:
                pass
        threading.Thread(target=run_update, daemon=True).start()

    def _bind_global_copy_paste(self, root_widget):
        """Recursively bind right-click context menu and shortcuts to all text widgets."""
        def make_menu(w):
            menu = tk.Menu(w, tearoff=0)
            menu.add_command(label="Sao chép (Copy)   Ctrl+C", command=lambda: w.event_generate("<<Copy>>"))
            menu.add_command(label="Cắt (Cut)        Ctrl+X", command=lambda: w.event_generate("<<Cut>>"))
            menu.add_command(label="Dán (Paste)      Ctrl+V", command=lambda: w.event_generate("<<Paste>>"))
            return menu
            
        def show_menu(event):
            w = event.widget
            if isinstance(w, (tk.Entry, ttk.Combobox, tk.Text)):
                w.focus()
                menu = make_menu(w)
                menu.tk_popup(event.x_root, event.y_root)
                
        # Bind globally for right-click
        root_widget.bind_all("<Button-3>", show_menu)
        
        # Ensure default Windows shortcuts work globally on text widgets
        root_widget.bind_all("<Control-c>", lambda e: e.widget.event_generate("<<Copy>>") if getattr(e, 'widget', None) and isinstance(e.widget, (tk.Entry, ttk.Combobox, tk.Text)) else None)
        root_widget.bind_all("<Control-v>", lambda e: e.widget.event_generate("<<Paste>>") if getattr(e, 'widget', None) and isinstance(e.widget, (tk.Entry, ttk.Combobox, tk.Text)) else None)
        root_widget.bind_all("<Control-x>", lambda e: e.widget.event_generate("<<Cut>>") if getattr(e, 'widget', None) and isinstance(e.widget, (tk.Entry, ttk.Combobox, tk.Text)) else None)

    def _on_tab_change(self, event):
        tab_id = self.nb.index("current")
        tab_name = self.nb.tab(tab_id, "text")
        utils.log_activity(f"Truy cập phân hệ: {tab_name}")
        if tab_name and "🏠" in tab_name: self._update_home_metrics()
        self._update_sidebar_highlight(tab_name)

    def _on_nb_leave(self, event):
        if self._current_tip:
            self._current_tip.destroy()
            self._current_tip = None
            self._current_tip_idx = -1
        self.lbl_status.config(text="Sẵn sàng", fg="#555")

    def _on_nb_motion(self, event):
        nb = event.widget
        try:
            index = nb.index(f"@{event.x},{event.y}")
        except:
            index = None
            
        desc_map = self.tab_desc if nb == self.nb else self._sub_tips.get(str(nb), {})
        
        if index is not None and isinstance(index, int) and index in desc_map:
            txt = desc_map[index]
            self.lbl_status.config(text=txt, fg="#0078D4")
            
            if not self._current_tip or self._current_tip_idx != (str(nb), index):
                if self._current_tip: self._current_tip.destroy()
                self._current_tip = tk.Toplevel(self)
                self._current_tip.wm_overrideredirect(1)
                self._current_tip.wm_geometry(f"+{event.x_root+30}+{event.y_root+10}")
                tk.Label(self._current_tip, text=txt, bg="#111", fg="#FFF", 
                         font=("Segoe UI", 10, "bold"), padx=10, pady=6, 
                         relief="solid", borderwidth=1).pack()
                self._current_tip_idx = (str(nb), index)
            else:
                self._current_tip.wm_geometry(f"+{event.x_root+30}+{event.y_root+10}")
        else:
            self._on_nb_leave(None)

    def _bind_sub_tips(self, nb, desc_map):
        self._sub_tips[str(nb)] = desc_map
        nb.bind("<Motion>", self._on_nb_motion)
        nb.bind("<Leave>", self._on_nb_leave)

    def _on_mousewheel(self, event):
        try:
            widget = self.winfo_containing(event.x_root, event.y_root)
        except:
            return
            
        while widget:
            if hasattr(widget, 'yview') and not isinstance(widget, (ttk.Treeview, tk.Text, tk.Listbox)):
                widget.yview_scroll(int(-1*(event.delta/120)), "units")
                break
            # If it's a Canvas (used in Settings/Home), it usually has a yview
            if isinstance(widget, tk.Canvas):
                widget.yview_scroll(int(-1*(event.delta/120)), "units")
                break
            widget = widget.master

    def _toggle_browser(self):
        if self._browser_visible:
            self.paned.forget(self.frame_browser)
            self._browser_visible = False
            utils.log_activity("Ẩn File Browser")
        else:
            self.paned.insert(0, self.frame_browser, weight=0)
            self._browser_visible = True
            self._populate_file_tree()
            utils.log_activity("Hiện File Browser")
        
        # Update top button text if it exists
        if hasattr(self, "_btn_toggle_br"):
            txt = "📂 Hiện File Browser" if not self._browser_visible else "📁 Ẩn File Browser"
            self._btn_toggle_br.config(text=txt)

    def _populate_file_tree(self):
        for i in self.tree_files.get_children(): self.tree_files.delete(i)
        base_dir = os.getcwd()
        
        # Helper to recursively add nodes
        def add_node(parent, path):
            try:
                for entry in os.listdir(path):
                    if entry in ["__pycache__", ".venv", ".git", "build", "dist"]: continue
                    full_path = os.path.join(path, entry)
                    is_dir = os.path.isdir(full_path)
                    icon = "📁 " if is_dir else "📄 "
                    node = self.tree_files.insert(parent, "end", text=icon + entry, values=(full_path,))
                    if is_dir:
                        # Add a dummy node to allow expansion
                        self.tree_files.insert(node, "end", text="...")
            except Exception: pass

        # Handle expansion to lazy-load directories
        def on_open(event):
            node = self.tree_files.focus()
            full_path = self.tree_files.item(node)['values'][0]
            if os.path.isdir(full_path):
                children = self.tree_files.get_children(node)
                if len(children) == 1 and self.tree_files.item(children[0])['text'] == "...":
                    self.tree_files.delete(children[0])
                    add_node(node, full_path)

        self.tree_files.bind("<<TreeviewOpen>>", on_open)
        
        # Add root folders
        for folder in ["data", "invoices", "contracts"]:
            fpath = os.path.join(base_dir, folder)
            os.makedirs(fpath, exist_ok=True)
            node = self.tree_files.insert("", "end", text="📁 " + folder, values=(fpath,), open=True)
            add_node(node, fpath)

    def _on_file_double_click(self, event):
        sel = self.tree_files.selection()
        if not sel: return
        fpath = self.tree_files.item(sel[0])['values'][0]
        if os.path.isfile(fpath):
            try: os.startfile(fpath)
            except Exception as e: messagebox.showerror("Lỗi mở file", str(e))

    def _update_sidebar_highlight(self, active_tab_name):
        if not hasattr(self, 'sidebar_buttons'): return
        for text, (btn, bf) in self.sidebar_buttons.items():
            if text == active_tab_name or (active_tab_name and active_tab_name in text):
                btn.config(bg="#00796B", fg="#FFFFFF", font=("Segoe UI", 10, "bold"))  # Đông Hồ Teal Green
                bf.config(bg="#00796B")
            else:
                btn.config(bg="#1E293B", fg="#F1F5F9", font=("Segoe UI", 10, "normal"))
                bf.config(bg="#1E293B")

    def _build_sidebar(self):
        for w in self.frame_sidebar.winfo_children():
            w.destroy()

        # Sidebar Title
        title_lbl = tk.Label(self.frame_sidebar, text="🏢 SME LEDGER", font=("Segoe UI", 14, "bold"), fg="#F8FAFC", bg="#1E293B")
        title_lbl.pack(pady=(20, 2), padx=10, anchor="w")
        sub_lbl = tk.Label(self.frame_sidebar, text=f"Phiên bản {config.APP_VERSION}", font=("Segoe UI", 8, "italic"), fg="#94A3B8", bg="#1E293B")
        sub_lbl.pack(pady=(0, 20), padx=10, anchor="w")

        self.sidebar_buttons = {}

        for text in self.nb.tab_names:
            btn_frame = tk.Frame(self.frame_sidebar, bg="#1E293B")
            btn_frame.pack(fill="x", padx=10, pady=2)

            btn = tk.Button(btn_frame, text=f" {text}", font=("Segoe UI", 10),
                            anchor="w", bg="#1E293B", fg="#F1F5F9", activebackground="#334155",
                            activeforeground="#FFFFFF", bd=0, relief="flat", padx=15, pady=8, cursor="hand2")
            btn.pack(fill="both", expand=True)

            btn.config(command=lambda t=text: self.nb.select(t))
            
            # Hover effects
            def on_enter(e, b=btn, bf=btn_frame, t=text):
                current_active = self.nb.tab(self.nb.index("current"), "text")
                if current_active != t:
                    b.config(bg="#334155")
                    bf.config(bg="#334155")
            def on_leave(e, b=btn, bf=btn_frame, t=text):
                current_active = self.nb.tab(self.nb.index("current"), "text")
                if current_active != t:
                    b.config(bg="#1E293B")
                    bf.config(bg="#1E293B")
                    
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            
            self.sidebar_buttons[text] = (btn, btn_frame)

        self.nb.select(0)

    def _refresh_co_label(self):
        s = self.settings
        name = s.get("company_name","")
        tax_c = s.get("company_tax_code","")
        addr = s.get("company_address","")
        self._lbl_co.config(text=f"{name}  |  MST: {tax_c}  |  {addr}")

    def _change_niche(self, event=None):
        n = self.niche_var.get() if hasattr(self,'niche_var') else "photocopy_print"
        icons = {
            "photocopy_print": "🖨️", "retail_grocery": "🛒", "services_consulting": "🤝",
            "clinic_pharmacy": "🏥", "fnb_cafe": "☕", "real_estate": "🏠",
            "construction": "🏗️", "transport_logistics": "🚚", "education_training": "🎓",
            "general_trade": "📦"
        }
        if hasattr(self, "_lbl_niche_icon"):
            self._lbl_niche_icon.config(text=icons.get(n, "🏢"))
            
        VAS_RULES.clear()
        VAS_RULES.update({"Sales":{"dr":"131","cr":"511","vat_cr":"3331"},
                          "Purchase":{"dr":"642","cr":"331","vat_dr":"133"},
                          "Expense":{"dr":"642","cr":"111"}})
        VAS_RULES.update(get_vas_rules(n))
        if hasattr(self, 'cmb_auto_vas'):
            self.cmb_auto_vas['values'] = list(VAS_RULES.keys())

    def _fmt(self, n):
        dec = int(self.settings.get("currency_decimals", 0))
        sym = self.settings.get("currency","VND")
        return f"{n:,.{dec}f} {sym}"

    def _build_home_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self.lbl.get("tab_home", "Trang chủ"))
        
        shell = ttk.Frame(tab)
        shell.pack(fill="both", expand=True)
        self.home_canvas = tk.Canvas(shell, bg="#F8F9FA", highlightthickness=0)
        home_scroll = ttk.Scrollbar(shell, orient="vertical", command=self.home_canvas.yview)
        self.home_canvas.configure(yscrollcommand=home_scroll.set)
        self.home_canvas.pack(side="left", fill="both", expand=True)
        home_scroll.pack(side="right", fill="y")
        self.home_dynamic_ids = []
        self.home_shortcut_frame = None
        self.home_canvas.bind("<Configure>", lambda _event: self._update_home_metrics())
        self._update_home_metrics()

    def _update_home_metrics(self):
        if not hasattr(self, 'home_canvas'): return
        c = self.home_canvas
        c.delete("all")
        self.home_dynamic_ids = []
        if getattr(self, "home_shortcut_frame", None):
            try: self.home_shortcut_frame.destroy()
            except Exception: pass
            self.home_shortcut_frame = None
        if hasattr(self, 'home_demo_btn') and self.home_demo_btn:
            try: self.home_demo_btn.destroy()
            except Exception: pass
            self.home_demo_btn = None

        def create_round_rect(canvas, x1, y1, x2, y2, radius=15, **kwargs):

            points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
            return canvas.create_polygon(points, **kwargs, smooth=True)

        width = c.winfo_width() if c.winfo_width() > 100 else 1150
        lay = dashboard_layout(width)
        h = lay["header"]
        create_round_rect(c, h["x"], h["y"], h["x"] + h["width"], h["y"] + h["height"], radius=28, fill="#005A9E")
        c.create_text(h["x"] + 34, h["y"] + 38, text=self.lbl["dashboard_subtitle"], font=("Segoe UI", 10, "bold"), fill="#B3D7FF", anchor="w", width=h["width"] - 210)
        title_font = ("Segoe UI", 24 if h["width"] < 760 else 28, "bold")
        c.create_text(h["x"] + 34, h["y"] + 76, text=self.lbl["dashboard_title"], font=title_font, fill="white", anchor="w", width=h["width"] - 220)
        create_round_rect(c, h["x"] + h["width"] - 138, h["y"] + 24, h["x"] + h["width"] - 34, h["y"] + 96, radius=18, fill="#FFFFFF")
        c.create_text(h["x"] + h["width"] - 86, h["y"] + 60, text="🚀", font=("Segoe UI", 30))

        if getattr(self, 'demo_active', False):
            self.home_demo_btn = tk.Button(c, text="🔴 THOÁT CHẾ ĐỘ DEMO", command=self._exit_demo_mode,
                                           bg="#D32F2F", fg="white", font=("Segoe UI", 9, "bold"), padx=8, pady=3, cursor="hand2")
            c.create_window(h["x"] + h["width"] - 230, h["y"] + h["height"] - 28, window=self.home_demo_btn, anchor="center")

        df = db.get_flat_df(self.db)
        rev = df[df['account'].astype(str).str.startswith('511') & (df['credit'] > 0)]['credit'].sum() if not df.empty else 0
        exp = df[df['account'].astype(str).str.startswith('64') & (df['debit'] > 0)]['debit'].sum() if not df.empty else 0
        profit = rev - exp
        
        metrics = [
            (self.lbl.get("total_rev", "TỔNG DOANH THU"), f"{rev:,.0f}", "#1B5E20", "#E8F5E9", "💰"),
            (self.lbl.get("total_exp", "TỔNG CHI PHÍ"),   f"{exp:,.0f}", "#B71C1C", "#FFEBEE", "💸"),
            (self.lbl.get("total_profit", "LỢI NHUẬN RÒNG"), f"{profit:,.0f}", "#0D47A1", "#E3F2FD", "📈")
        ]
        
        for card, (t, v, col, bg, ico) in zip(lay["metric_cards"], metrics):
            x, y, w, hgt = card["x"], card["y"], card["width"], card["height"]
            rect = create_round_rect(c, x, y, x+w, y+hgt, radius=20, fill=bg, outline="#E0E0E0")
            t1 = c.create_text(x+24, y+34, text=ico, font=("Segoe UI", 28), fill=col, anchor="w")
            t2 = c.create_text(x+24, y+76, text=t, font=("Segoe UI", 9, "bold"), fill="#666", anchor="w", width=w-48)
            t3 = c.create_text(x+24, y+116, text=v + " đ", font=("Segoe UI", 18, "bold"), fill=col, anchor="w", width=w-48)
            self.home_dynamic_ids.extend([rect, t1, t2, t3])

        recent_box = lay["recent"]
        rect_act = create_round_rect(c, recent_box["x"], recent_box["y"], recent_box["x"]+recent_box["width"], recent_box["y"]+recent_box["height"], radius=20, fill="#FFFFFF", outline="#E0E0E0")
        t_act = c.create_text(recent_box["x"]+20, recent_box["y"]+25, text=self.lbl["recent_activities"], font=("Segoe UI", 9, "bold"), fill="#1565C0", anchor="w")
        self.home_dynamic_ids.extend([rect_act, t_act])
        
        recent = utils.get_recent_activities(5)
        if not recent: recent = ["Chưa có dữ liệu."]
        for i, act in enumerate(recent):
            clean_act = act.split("] ", 1)[1] if "] " in act else act
            tid = c.create_text(recent_box["x"]+25, recent_box["y"]+55 + i*19, text=f"• {clean_act[:70]}", font=("Segoe UI", 8), fill="#555", anchor="w", width=recent_box["width"]-45)
            self.home_dynamic_ids.append(tid)

        quick_box = lay["quick"]
        rect_qa = create_round_rect(c, quick_box["x"], quick_box["y"], quick_box["x"]+quick_box["width"], quick_box["y"]+quick_box["height"], radius=20, fill="#FFFFFF", outline="#E0E0E0")
        t_qa = c.create_text(quick_box["x"]+20, quick_box["y"]+25, text=self.lbl["quick_access"], font=("Segoe UI", 9, "bold"), fill="#555", anchor="w")
        self.home_dynamic_ids.extend([rect_qa, t_qa])
        btn_f = tk.Frame(c, bg="#FFFFFF")
        self.home_shortcut_frame = btn_f

        def quick_btn(parent, text, cmd, color, icon, row, col_idx):
            b = tk.Button(parent, text=f"{icon} {text}", command=cmd, bg="#FFFFFF", fg=color,
                          font=("Segoe UI", 8, "bold"), relief="flat", width=13, padx=4, pady=4,
                          highlightbackground="#EEE", highlightthickness=1, cursor="hand2")
            b.grid(row=row, column=col_idx, padx=4, pady=3, sticky="ew")
            b.bind("<Enter>", lambda e, b=b, c=color: b.config(bg=c, fg="white"))
            b.bind("<Leave>", lambda e, b=b, c=color: b.config(bg="#FFFFFF", fg=c))

        shortcuts = [
            ("Chứng từ", lambda: self.nb.select("📑"), "#0078D4", "📑"),
            ("Hóa đơn", lambda: self.nb.select("🧾"), "#FB8C00", "🧾"),
            ("Sổ cái", lambda: self.nb.select("🕒"), "#E91E63", "🕒"),
            ("Kho hàng", lambda: self.nb.select("🗂️"), "#607D8B", "📦"),
            ("Báo cáo", lambda: self.nb.select("📊"), "#673AB7", "📊"),
            ("Công nợ", lambda: self.nb.select("📊"), "#D32F2F", "💸"),
            ("Nhân sự", lambda: self.nb.select("👥"), "#43A047", "👥"),
            ("Cài đặt", lambda: self.nb.select("⚙️"), "#546E7A", "⚙️"),
        ]
        btn_cols = 2 if quick_box["width"] < 520 else 4
        for idx, (text, cmd, color, icon) in enumerate(shortcuts):
            quick_btn(btn_f, text, cmd, color, icon, idx // btn_cols, idx % btn_cols)
        for col_idx in range(btn_cols):
            btn_f.grid_columnconfigure(col_idx, weight=1)
        c.create_window(quick_box["x"]+20, quick_box["y"]+52, window=btn_f, anchor="nw")

        rem_box = lay["reminders"]
        rect_rem = create_round_rect(c, rem_box["x"], rem_box["y"], rem_box["x"]+rem_box["width"], rem_box["y"]+rem_box["height"], radius=20, fill="#FFF9C4", outline="#FBC02D")
        t_rem = c.create_text(rem_box["x"]+20, rem_box["y"]+25, text=self.lbl["smart_reminders"], font=("Segoe UI", 10, "bold"), fill="#F57F17", anchor="w")
        self.home_dynamic_ids.extend([rect_rem, t_rem])
        
        reminders = []
        if df.empty: reminders.append("• Bạn chưa nhập dữ liệu nào. Hãy bắt đầu bằng cách 'Lập chứng từ'!")
        if rev == 0 and not df.empty: reminders.append("• Doanh thu đang bằng 0. Đừng quên ghi nhận các hóa đơn bán hàng!")
        if exp > 0 and profit < 0: reminders.append("• Cảnh báo: Chi phí đang cao hơn doanh thu. Hãy kiểm tra lại dòng tiền!")
        
        # Low stock check
        inv_df = db.get_inventory(self.db)
        if not inv_df.empty:
            low_items = inv_df[(inv_df['qty'] <= inv_df['min_qty']) & (inv_df['min_qty'] > 0)]
            if not low_items.empty:
                reminders.append(f"• Cảnh báo: Có {len(low_items)} mặt hàng sắp hết kho. Kiểm tra Danh mục > Kho hàng!")

        if not reminders: reminders.append("• Tuyệt vời! Hệ thống của bạn đang vận hành ổn định.")
        
        for i, r in enumerate(reminders[:3]):
            tid = c.create_text(rem_box["x"]+30, rem_box["y"]+55 + i*21, text=r, font=("Segoe UI", 9), fill="#444", anchor="w", width=rem_box["width"]-60)
            self.home_dynamic_ids.append(tid)

        ft = c.create_text(lay["margin"] + lay["content_width"], lay["height"] - 22, text=f"{self.lbl['support_footer']} | {self.lbl['dashboard_title']}", font=("Segoe UI", 8), fill="#AAA", anchor="e")
        self.home_dynamic_ids.append(ft)
        c.config(scrollregion=(0, 0, lay["content_width"] + lay["margin"] * 2, lay["height"]))

    def _refresh_all(self):
        self._refresh_reports()
        if hasattr(self, "_refresh_inv_history"):
            self._refresh_inv_history()
        # Re-build home tab to update stats
        for tab in self.nb.tabs():
            if self.nb.tab(tab, "text") == "🏠":
                # We can't easily re-build, so we'll just update stats next time we enter
                pass

    # ── REPORTS TAB ───────────────────────────────────────────
    def _build_reports_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="📊")
        
        sub = ttk.Notebook(tab); sub.pack(fill="both", expand=True, padx=12, pady=12)
        t1 = ttk.Frame(sub); sub.add(t1, text="⚖️")
        t2 = ttk.Frame(sub); sub.add(t2, text="📈")
        t3 = ttk.Frame(sub); sub.add(t3, text="🔍")
        t4 = ttk.Frame(sub); sub.add(t4, text="📝")
        
        t5 = ttk.Frame(sub); sub.add(t5, text="💸")
        
        self._build_b02_tt99_panel(t2)
        self._build_trial_balance_panel(t1) # New Trial Balance
        debt_manager.build_debt_tab(self, t5, self.db, self.lbl)
        self._bind_sub_tips(sub, {0:"Bảng cân đối số phát sinh (Trial Balance)", 1:"Báo cáo Kết quả kinh doanh (P&L)", 2:"Sổ chi tiết tài khoản", 3:"Tờ khai thuế GTGT", 4:"Quản lý Công nợ chi tiết"})

    def _build_trial_balance_panel(self, parent):
        f = ttk.Frame(parent); f.pack(fill="both", expand=True, padx=10, pady=10)
        self.txt_trial = tk.Text(f, font=("Consolas", 10), wrap="none", bg="#FDFDFD")
        sb_y = ttk.Scrollbar(f, command=self.txt_trial.yview)
        sb_x = ttk.Scrollbar(f, orient="horizontal", command=self.txt_trial.xview)
        self.txt_trial.config(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        
        tk.Button(f, text="🔄 Tải Bảng Cân đối Phát sinh", command=self._refresh_trial_balance, bg="#1565C0", fg="white").pack(pady=5)
        self.txt_trial.pack(side="top", fill="both", expand=True)
        sb_y.pack(side="right", fill="y", in_=self.txt_trial)
        sb_x.pack(side="bottom", fill="x")

    def _refresh_trial_balance(self):
        # Logic tính Trial Balance (Bảng cân đối số phát sinh)
        df = db.get_flat_df(self.db)
        if df.empty: return
        
        summary = df.groupby('account').agg({'debit':'sum', 'credit':'sum'}).reset_index()
        report = f"{'='*70}\n"
        report += f"{'BẢNG CÂN ĐỐI SỐ PHÁT SINH':^70}\n"
        report += f"{'='*70}\n"
        report += f"{'TK':<10} | {'Nợ Phát sinh':>25} | {'Có Phát sinh':>25}\n"
        report += f"{'-'*70}\n"
        
        total_dr = 0; total_cr = 0
        for _, r in summary.iterrows():
            report += f"{r['account']:<10} | {r['debit']:>25,.0f} | {r['credit']:>25,.0f}\n"
            total_dr += r['debit']; total_cr += r['credit']
            
        report += f"{'-'*70}\n"
        report += f"{'TỔNG CỘNG':<10} | {total_dr:>25,.0f} | {total_cr:>25,.0f}\n"
        report += f"{'='*70}\n"
        
        self.txt_trial.delete("1.0", "end")
        self.txt_trial.insert("1.0", report)

    # ── LEDGER TAB ───────────────────────────────────────────
    def _build_invoice_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="🧾")
        
        sub = ttk.Notebook(tab); sub.pack(fill="both", expand=True, padx=12, pady=12)
        t1 = ttk.Frame(sub); sub.add(t1, text="➕")
        t2 = ttk.Frame(sub); sub.add(t2, text="🕒")
        self._bind_sub_tips(sub, {0:"Lập hóa đơn mới", 1:"Lịch sử hóa đơn đã xuất"})
        
        self._build_invoice_main(t1)
        self._build_invoice_history_panel(t2)

    def _build_invoice_main(self, tab):
        h_f = ttk.Frame(tab); h_f.pack(fill="x")
        tk.Label(h_f, text="🧾 LẬP HÓA ĐƠN BÁN HÀNG", font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
        tk.Button(h_f, text="❓", command=lambda: messagebox.showinfo("Hướng dẫn", "Chọn Khách hàng và các mặt hàng từ Kho. Hệ thống tự động tính thuế GTGT và đơn giá theo lô."), relief="flat").pack(side="right")
        
        hdr = ttk.LabelFrame(tab, text="📦 Quản lý Kho & Quy đổi (UoM/Batches)")
        hdr.pack(fill="x", padx=10, pady=6)

        tk.Label(hdr, text=self.lbl["date"]).grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.ent_date = tk.Entry(hdr, width=14); self.ent_date.grid(row=0, column=1, padx=4)
        self.ent_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))

    def _build_ledger_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self.lbl.get("tab_documents", "Chứng từ"))

        h_hdr = ttk.Frame(tab); h_hdr.pack(fill="x")
        tk.Label(h_hdr, text="📑 LẬP CHỨNG TỪ KẾ TOÁN (TT133)", font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
        tk.Button(h_hdr, text="❓", command=lambda: messagebox.showinfo("Hướng dẫn", "Tại đây bạn hạch toán Nợ/Có. Có thể dùng 'Auto VAS' để điền nhanh các nghiệp vụ phổ biến."), relief="flat").pack(side="right")
        
        hdr = ttk.LabelFrame(tab, text="Thông tin chứng từ (Voucher Header)")
        hdr.pack(fill="x", padx=6, pady=4)

        tk.Label(hdr, text=self.lbl["date"]).grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.ent_date = tk.Entry(hdr, width=14); self.ent_date.grid(row=0, column=1, padx=4)
        self.ent_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))

        tk.Label(hdr, text=self.lbl["ref"]).grid(row=0, column=2, sticky="w", padx=8)
        self.ent_ref = tk.Entry(hdr, width=22); self.ent_ref.grid(row=0, column=3, padx=4)

        tk.Label(hdr, text=self.lbl["note"]).grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.ent_note = tk.Entry(hdr, width=55); self.ent_note.grid(row=1, column=1, columnspan=3, padx=4, sticky="w")

        af = ttk.LabelFrame(hdr, text="Auto VAS (Quick)")
        af.grid(row=0, column=4, rowspan=2, padx=14, pady=2)
        self.cmb_auto_vas = ttk.Combobox(af, values=list(VAS_RULES.keys()), state="readonly", width=16)
        self.cmb_auto_vas.pack(side="left", padx=4)
        if VAS_RULES: self.cmb_auto_vas.current(0)
        self.ent_auto_amt = tk.Entry(af, width=12); self.ent_auto_amt.pack(side="left", padx=4)
        tk.Button(af, text="Apply", command=self._apply_vas, bg="#1976D2", fg="white").pack(side="left", padx=4)

        lf = ttk.LabelFrame(tab, text="Chi tiết hạch toán (Debit/Credit Lines)")
        lf.pack(fill="both", padx=6, pady=2)
        inp = ttk.Frame(lf); inp.pack(fill="x", padx=10, pady=5)
        
        tk.Label(inp, text="Tài khoản:").grid(row=0, column=0, sticky="e", padx=4)
        df_acc = db.get_accounts(self.db)
        
        # Categorized Account List for Intuitive Selection
        acc_list = []
        if not df_acc.empty:
            for _, r in df_acc.iterrows():
                code = str(r['code'])
                cat = "Unknown"
                if code.startswith('1'): cat = "Tài sản (Asset)"
                elif code.startswith('2'): cat = "Tài sản dài hạn"
                elif code.startswith('3'): cat = "Nợ phải trả (Liability)"
                elif code.startswith('4'): cat = "Vốn chủ sở hữu (Equity)"
                elif code.startswith('5'): cat = "Doanh thu (Income)"
                elif code.startswith('6'): cat = "Chi phí (Expense)"
                elif code.startswith('7'): cat = "Thu nhập khác"
                elif code.startswith('8'): cat = "Chi phí khác"
                elif code.startswith('9'): cat = "Xác định KQKD"
                acc_list.append(f"[{cat}] {r['code']} - {r['name']}")

        self.v_acc = tk.StringVar()
        self.cmb_acc = ttk.Combobox(inp, textvariable=self.v_acc, values=acc_list, width=45)
        self.cmb_acc.grid(row=0, column=1, sticky="w", padx=4)
        
        tk.Label(inp, text="Nợ (Dr):").grid(row=0, column=2, sticky="e", padx=4)
        self.ent_dr = tk.Entry(inp, width=12); self.ent_dr.grid(row=0, column=3, sticky="w", padx=4)
        
        tk.Label(inp, text="Có (Cr):").grid(row=0, column=4, sticky="e", padx=4)
        self.ent_cr = tk.Entry(inp, width=12); self.ent_cr.grid(row=0, column=5, sticky="w", padx=4)
        
        tk.Button(inp, text="+ Thêm", command=self._add_vline, bg="#0078D4", fg="white", width=8).grid(row=0, column=6, padx=8)
        tk.Button(inp, text="Xóa", command=self._del_vline, width=8).grid(row=0, column=7, padx=2)

        self.tree_vlines = ttk.Treeview(lf, columns=("acc","dr","cr"), show="headings", height=4)
        for c,t,w in [("acc","Tài khoản",110),("dr","Nợ (Debit)",120),("cr","Có (Credit)",120)]:
            self.tree_vlines.heading(c,text=t); self.tree_vlines.column(c,width=w,anchor="e" if c!="acc" else "w")
        self.tree_vlines.pack(fill="both", expand=True)

        act = ttk.Frame(tab); act.pack(fill="x", padx=6, pady=4)
        self.btn_post = tk.Button(act, text=self.lbl["post_btn"], command=self._post_voucher, bg="#388E3C", fg="white", width=22)
        self.btn_post.pack(side="left")
        tk.Button(act, text="Làm mới bảng kê", command=self._clear_voucher).pack(side="left", padx=8)
        tk.Button(act, text="Xóa Chứng từ", command=self._delete_entry, bg="#C62828", fg="white").pack(side="right")
        
        # ── LEDGER FILTERS ────────────────────────────────────
        flt = ttk.Frame(tab); flt.pack(fill="x", padx=6, pady=2)
        tk.Label(flt, text="🔍 Bộ lọc:", font=("Arial", 9, "bold")).pack(side="left", padx=4)
        tk.Label(flt, text="TK:").pack(side="left", padx=2)
        self.ent_flt_acc = tk.Entry(flt, width=8); self.ent_flt_acc.pack(side="left", padx=2)
        tk.Label(flt, text="Từ:").pack(side="left", padx=2)
        self.ent_flt_from = tk.Entry(flt, width=10); self.ent_flt_from.pack(side="left", padx=2)
        tk.Label(flt, text="Đến:").pack(side="left", padx=2)
        self.ent_flt_to = tk.Entry(flt, width=10); self.ent_flt_to.pack(side="left", padx=2)
        tk.Label(flt, text="Tìm nội dung:").pack(side="left", padx=2)
        self.ent_flt_note = tk.Entry(flt, width=15); self.ent_flt_note.pack(side="left", padx=2)
        tk.Button(flt, text="Lọc dữ liệu", command=self._refresh_ledger, bg="#1565C0", fg="white", font=("Arial", 8)).pack(side="left", padx=10)

        cols = ("id","date","created_at","ref","note","acc","contra","debit","credit")
        self.tree_ledger = ttk.Treeview(tab, columns=cols, show="headings")
        widths = [35,80,120,100,160,75,75,100,100]
        heads  = ["ID","Ngày","Thời gian tạo","Số Chứng từ","Diễn giải","Tài khoản","Đối ứng","Nợ (Debit)","Có (Credit)"]
        for c,h,w in zip(cols,heads,widths):
            self.tree_ledger.heading(c,text=h); self.tree_ledger.column(c,width=w,anchor="e" if c in ("debit","credit") else "w")
        sb = ttk.Scrollbar(tab, orient="vertical", command=self.tree_ledger.yview)
        self.tree_ledger.configure(yscrollcommand=sb.set)
        self.tree_ledger.pack(fill="both", expand=True, padx=6, side="left")
        sb.pack(side="right", fill="y")
        self.tree_ledger.bind("<Double-1>", self._edit_entry_trigger)
        self._refresh_ledger()

    def _apply_vas(self):
        try:
            lines = auto_vas_lines(self.cmb_auto_vas.get(), float(self.ent_auto_amt.get()))
            for i in self.tree_vlines.get_children(): self.tree_vlines.delete(i)
            for a,d,c in lines: self.tree_vlines.insert("","end",values=(a,d,c))
            today = datetime.date.today().strftime("%Y%m%d")
            self.ent_ref.delete(0,"end")
            self.ent_ref.insert(0, f"CT-{self.cmb_auto_vas.get()[:3].upper()}-{today}")
        except Exception as e: messagebox.showerror("Error", str(e))

    def _add_vline(self):
        try:
            acc_val = self.cmb_acc.get().split(" - ")[0]
            if not acc_val:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn tài khoản!")
                return
            self.tree_vlines.insert("","end", values=(acc_val, float(self.ent_dr.get() or 0), float(self.ent_cr.get() or 0)))
            self.cmb_acc.set(""); self.ent_dr.delete(0,"end"); self.ent_cr.delete(0,"end")
        except: messagebox.showerror("Error","Debit/Credit must be numeric")

    def _del_vline(self):
        sel = self.tree_vlines.selection()
        if sel: self.tree_vlines.delete(sel[0])

    def _post_voucher(self):
        lines = [(str(self.tree_vlines.item(i)['values'][0]),
                  float(self.tree_vlines.item(i)['values'][1]),
                  float(self.tree_vlines.item(i)['values'][2]))
                 for i in self.tree_vlines.get_children()]
        if not lines: messagebox.showwarning("Warning","No lines in voucher."); return
        try:
            if self.editing_entry_id:
                db.update_entry(self.db, self.editing_entry_id, self.ent_date.get(),
                                self.ent_ref.get(), self.ent_note.get(), lines, self.cmb_auto_vas.get())
                messagebox.showinfo("OK", f"Updated #{self.editing_entry_id}")
            else:
                db.post_entry(self.db, self.ent_date.get(), self.ent_ref.get(),
                              self.ent_note.get(), lines, self.cmb_auto_vas.get())
                utils.log_activity(f"Lập chứng từ: {self.ent_ref.get()}")
                messagebox.showinfo("OK","Posted successfully.")
            self._clear_voucher(); self._refresh_all()
        except Exception as e: messagebox.showerror("Lỗi hạch toán", str(e))

    def _clear_voucher(self):
        self.editing_entry_id = None
        self.btn_post.config(text=self.lbl["post_btn"], bg="#388E3C")
        self.ent_ref.delete(0,"end"); self.ent_note.delete(0,"end")
        for i in self.tree_vlines.get_children(): self.tree_vlines.delete(i)

    def _edit_entry_trigger(self, event=None):
        sel = self.tree_ledger.selection()
        if not sel: return
        entry_id = self.tree_ledger.item(sel[0])['values'][0]
        details = db.get_entry_details(self.db, entry_id)
        if not details: return
        self._clear_voucher()
        self.editing_entry_id = entry_id
        self.btn_post.config(text=f"{self.lbl['update_btn']} #{entry_id}", bg="#1565C0")
        date, ref, note, type_ = details
        self.ent_date.delete(0,"end"); self.ent_date.insert(0, date)
        self.ent_ref.insert(0, ref); self.ent_note.insert(0, note)
        for a,d,c in db.get_entry_lines(self.db, entry_id):
            self.tree_vlines.insert("","end", values=(a,d,c))

    def _delete_entry(self):
        sel = self.tree_ledger.selection()
        if not sel: return
        eid = self.tree_ledger.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirm", f"Xóa chứng từ #{eid}?"):
            db.delete_entry(self.db, eid)
            utils.log_activity(f"Xóa chứng từ: #{eid}")
            if self.editing_entry_id == eid: self._clear_voucher()
            self._refresh_all()

    def _refresh_ledger(self):
        for i in self.tree_ledger.get_children(): self.tree_ledger.delete(i)
        df = db.get_flat_df(self.db)
        if df.empty: return
        
        # Apply filters
        acc_q = self.ent_flt_acc.get().strip()
        from_q = self.ent_flt_from.get().strip()
        to_q = self.ent_flt_to.get().strip()
        note_q = self.ent_flt_note.get().lower().strip() if hasattr(self, 'ent_flt_note') else ""
        
        if acc_q: df = df[df['account'].astype(str).str.contains(acc_q)]
        if from_q: df = df[df['date'] >= from_q]
        if to_q: df = df[df['date'] <= to_q]
        if note_q: df = df[df['note'].astype(str).str.lower().str.contains(note_q)]
        
        # Compute Correlative Accounts (TK Đối ứng)
        # For each line, the contra account is the primary account of the other side in the same entry
        entry_groups = df.groupby('entry_id')
        
        for entry_id, group in entry_groups:
            for idx, row in group.iterrows():
                # Simple logic: contra is the first account in the entry that is on the opposite side
                # or just any other account if it's a multi-line entry.
                others = group[group.index != idx]
                contra = others['account'].iloc[0] if not others.empty else "?"
                
                vals = [
                    row.entry_id, row.date, row.created_at, row.ref, row.note, 
                    row.account, contra,
                    f"{row.debit:,.0f}" if row.debit > 0 else "",
                    f"{row.credit:,.0f}" if row.credit > 0 else ""
                ]
                self.tree_ledger.insert("", "end", values=vals)

    # ── CRUD PANEL (shared by Directories sub-tabs) ───────────
    def _crud_panel(self, parent, field_defs, db_cols, fn_get, fn_add, fn_del, fn_upd,
                    tree_attr, ref_attr, pk_col=0):
        """Generic CRUD panel. field_defs = [(label, width),...] for input fields (skip id col)."""
        state = {'id': None}
        entries = []

        top = ttk.Frame(parent); top.pack(fill="x", padx=4, pady=4)
        input_cols = field_defs  # labels for entry fields (exclude pk id)
        form_cols = 2 if len(input_cols) > 3 else len(input_cols)
        for i,(lbl,w) in enumerate(input_cols):
            row = i // form_cols
            col = (i % form_cols) * 2
            tk.Label(top, text=lbl+":").grid(row=row, column=col, padx=5, pady=3, sticky="w")
            e = tk.Entry(top, width=w)
            e.grid(row=row, column=col+1, padx=5, pady=3, sticky="ew")
            top.grid_columnconfigure(col+1, weight=1)
            entries.append(e)

        btn_save = tk.Button(top, text=self.lbl["add_btn"], width=10,
                             bg="#388E3C", fg="white")
        btn_save.grid(row=0, column=form_cols*2, rowspan=max(1, (len(input_cols)+form_cols-1)//form_cols), padx=8, sticky="ns")

        bf = ttk.Frame(parent); bf.pack(fill="x", padx=4)
        tk.Button(bf, text=self.lbl["delete_btn"], bg="#C62828", fg="white",
                  command=lambda: _do_del()).pack(side="left")
        tk.Label(bf, text=self.lbl["edit_hint"], fg="#1565C0").pack(side="right", padx=6)

        # Determine display columns (always show all db_cols)
        show_cols = list(db_cols)
        tree_wrap = ttk.Frame(parent)
        tree_wrap.pack(fill="both", expand=True, padx=4, pady=2)
        tree = ttk.Treeview(tree_wrap, columns=show_cols, show="headings", height=12)
        col_widths = [40] + [f[1]*6 for f in field_defs]
        for col,w2 in zip(show_cols, col_widths):
            tree.heading(col, text=col); tree.column(col, width=min(w2,200))
        sb = ttk.Scrollbar(tree_wrap, orient="vertical", command=tree.yview)
        sb_x = ttk.Scrollbar(tree_wrap, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=sb.set, xscrollcommand=sb_x.set)
        tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")
        tree_wrap.grid_rowconfigure(0, weight=1)
        tree_wrap.grid_columnconfigure(0, weight=1)
        setattr(self, tree_attr, tree)

        def _refresh():
            for i in tree.get_children(): tree.delete(i)
            df = fn_get(self.db)
            if not df.empty:
                for r in df.itertuples(index=False):
                    tree.insert("","end", values=list(r))
            # Clear form after any refresh (fix: isolate per-client data)
            state['id'] = None
            btn_save.config(text=self.lbl["add_btn"], bg="#388E3C", fg="white")
            for e in entries: e.delete(0,"end")

        setattr(self, ref_attr, _refresh)

        def _do_save():
            vals = [e.get() for e in entries]
            try:
                if state['id'] is not None:
                    if fn_upd.__code__.co_argcount == len(vals) + 3:  # conn, pk, *vals
                        fn_upd(self.db, state['id'], *vals)
                    else:
                        fn_upd(self.db, *vals, state['id'])
                else:
                    fn_add(self.db, *vals)
                _refresh()
            except Exception as ex: messagebox.showerror("Error", str(ex))

        btn_save.config(command=_do_save)

        def _do_del():
            sel = tree.selection()
            if not sel: return
            pk = tree.item(sel[0])['values'][pk_col]
            if messagebox.askyesno("Confirm", f"Xóa mục này? (ID={pk})"):
                fn_del(self.db, pk)
                _refresh()

        def _on_double(event=None):
            sel = tree.selection()
            if not sel: return
            row = tree.item(sel[0])['values']
            # Skip pk column, fill entries
            data_vals = [v for i,v in enumerate(row) if i != pk_col]
            for i,e in enumerate(entries):
                if i < len(data_vals):
                    e.delete(0,"end"); e.insert(0, str(data_vals[i]))
            state['id'] = row[pk_col]
            btn_save.config(text=f"{self.lbl['update_btn']} #{state['id']}", bg="#1565C0", fg="white")

        tree.bind("<Double-1>", _on_double)
        _refresh()

    # ── DIRECTORIES TAB ──────────────────────────────────────
    def _build_dirs_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self.lbl.get("tab_directories", "Danh mục"))
        sub = ttk.Notebook(tab); sub.pack(fill="both", expand=True, padx=15, pady=15)

        t0 = ttk.Frame(sub)
        lbl_t0 = "📖 Hệ thống Tài khoản" if self.settings.get("language","vi") == "vi" else "📖 Chart of Accounts"
        sub.add(t0, text=lbl_t0)

        t1 = ttk.Frame(sub)
        lbl_t1 = "🤝 Khách hàng & Đối tác" if self.settings.get("language","vi") == "vi" else "🤝 Clients & Partners"
        sub.add(t1, text=lbl_t1)

        t2 = ttk.Frame(sub)
        lbl_t2 = "📦 Kho hàng & Vật tư" if self.settings.get("language","vi") == "vi" else "📦 Inventory & Materials"
        sub.add(t2, text=lbl_t2)

        t_log = ttk.Frame(sub)
        lbl_t_log = "🕒 Lịch sử Kho hàng" if self.settings.get("language","vi") == "vi" else "🕒 Inventory History"
        sub.add(t_log, text=lbl_t_log)

        t3 = ttk.Frame(sub)
        lbl_t3 = "🏗️ Tài sản Cố định" if self.settings.get("language","vi") == "vi" else "🏗️ Fixed Assets"
        sub.add(t3, text=lbl_t3)
        
        self._bind_sub_tips(sub, {0:"Tài khoản", 1:"Khách hàng", 2:"Kho hàng", 3:"Lịch sử Kho", 4:"Tài sản", 5:"Danh mục VSIC"})
        
        # Header with inline help
        h_acc = ttk.Frame(t0); h_acc.pack(fill="x")
        tk.Label(h_acc, text="📖 Danh mục Tài khoản", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        tk.Button(h_acc, text="❓", command=lambda: messagebox.showinfo("Hướng dẫn", "Quản lý hệ thống tài khoản theo Thông tư 133. Click đúp để sửa."), relief="flat").pack(side="right")
        
        self._crud_panel(t0, [("Mã Tài khoản",10),("Tên Tài khoản",40),("Loại",18)],
                         ("code","name","type"), db.get_accounts, db.add_account,
                         db.delete_account, db.update_account, "tree_acc","_ref_acc", pk_col=0)
        self._build_clients_panel(t1)
        self._build_inventory_panel(t2, t_log)
        
        h_ast = ttk.Frame(t3); h_ast.pack(fill="x")
        tk.Label(h_ast, text="🏗️ Tài sản cố định", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        tk.Button(h_ast, text="❓", command=lambda: messagebox.showinfo("Hướng dẫn", "Quản lý và tính khấu hao tài sản cố định hàng tháng."), relief="flat").pack(side="right")
        
        self._crud_panel(t3, [("Tên Tài sản",28),("Nguyên giá",13),("Khấu hao (tháng)",9),("Ngày mua",12)],
                         ("id","name","value","dep_months","start_date"),
                         db.get_assets, db.add_asset,
                         db.delete_asset, db.update_asset, "tree_assets","_ref_assets")

        tabs_extra.build_vsic_subtab(self, sub)
        # Note: tabs_extra.build_vsic_subtab adds its own tab, I should ensure it uses an icon

    def _build_clients_panel(self, parent):
        """Client/supplier panel with address field and per-client isolation."""
        state = {'id': None}
        top = ttk.LabelFrame(parent, text="Thông tin Khách hàng / NCC")
        top.pack(fill="x", padx=4, pady=4)

        fields = [("Tên đơn vị/Họ tên",26),("Mã số thuế",16),("Liên hệ",18),("Địa chỉ",32),("Tiền tệ",8),("Số lẻ",5),("Loại KH",14)]
        entries = []
        for i,(lbl,w) in enumerate(fields):
            tk.Label(top, text=lbl+":").grid(row=i//3, column=(i%3)*2, padx=4, pady=2, sticky="w")
            if lbl == "Loại KH":
                e = ttk.Combobox(top, values=["corporate", "individual"], state="readonly", width=w)
                e.set("corporate")
            else:
                e = tk.Entry(top, width=w)
            e.grid(row=i//3, column=(i%3)*2+1, padx=4, pady=2)
            entries.append(e)

        # Actions column
        af = ttk.Frame(top); af.grid(row=0, column=6, rowspan=2, padx=10, sticky="ns")
        btn_save = tk.Button(af, text=self.lbl["add_btn"], bg="#388E3C", fg="white", width=12)
        btn_save.pack(pady=2)
        btn_clear = tk.Button(af, text="Làm sạch mẫu", width=12,
                              command=lambda: [e.delete(0,"end") for e in entries] or
                              state.update({'id':None}) or
                              btn_save.config(text=self.lbl["add_btn"], bg="#388E3C"))
        btn_clear.pack(pady=2)
        
        tk.Button(top, text="❓", command=lambda: messagebox.showinfo("Hướng dẫn", "Nhập thông tin Khách hàng hoặc Nhà cung cấp. MST dùng để tự động lấy thông tin lên hóa đơn."), relief="flat").grid(row=0, column=7, padx=5)

        bf = ttk.Frame(parent); bf.pack(fill="x", padx=4)
        tk.Button(bf, text=self.lbl["delete_btn"], bg="#C62828", fg="white",
                  command=lambda: _do_del()).pack(side="left")
        tk.Label(bf, text=self.lbl["edit_hint"], fg="#1565C0").pack(side="right", padx=6)

        cols = ("id","name","tax_code","contact","address","currency","currency_decimals","client_type")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=14)
        widths2 = [35,180,110,130,200,65,55,90]
        heads2  = ["ID","Tên","MST","Liên hệ","Địa chỉ","Tiền tệ","Số lẻ","Loại"]
        for c,h,w in zip(cols,heads2,widths2):
            tree.heading(c,text=h); tree.column(c,width=w)
        sb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(fill="both", expand=True, padx=4, side="left")
        sb.pack(side="right", fill="y")
        self.tree_clients = tree

        def _refresh():
            for i in tree.get_children(): tree.delete(i)
            df = db.get_clients(self.db)
            if not df.empty:
                for r in df.itertuples(index=False): tree.insert("","end", values=list(r))
            # Isolation fix: clear form so previous client data doesn't bleed
            state['id'] = None
            for e in entries: e.delete(0,"end")
            btn_save.config(text=self.lbl["add_btn"], bg="#388E3C")
            if hasattr(self, '_refresh_inv_client_combo'):
                self._refresh_inv_client_combo()

        self._ref_clients = _refresh

        def _do_save():
            name,tax,contact,address,cur,dec,client_type = [e.get() for e in entries]
            try:
                if state['id'] is not None:
                    db.update_client(self.db, state['id'], name, tax, contact, address, cur, int(dec or 0), client_type)
                else:
                    db.add_client(self.db, name, tax, contact, address, cur, int(dec or 0), client_type)
                _refresh()
            except ClientValidationError as ex:
                messagebox.showwarning("Thiếu dữ liệu khách hàng", str(ex))
            except Exception as ex: messagebox.showerror("Error", str(ex))

        btn_save.config(command=_do_save)

        def _do_del():
            sel = tree.selection()
            if not sel: return
            pk = tree.item(sel[0])['values'][0]
            if messagebox.askyesno("Confirm", f"Xóa khách hàng ID={pk}?"):
                db.delete_client(self.db, pk)
                _refresh()

        def _on_double(event=None):
            sel = tree.selection()
            if not sel: return
            row = tree.item(sel[0])['values']
            # row = (id, name, tax_code, contact, address, currency, decimals)
            data = row[1:]  # skip id
            for i,e in enumerate(entries):
                e.delete(0,"end"); e.insert(0, str(data[i]) if i < len(data) else "")
            state['id'] = row[0]
            btn_save.config(text=f"{self.lbl['update_btn']} #{state['id']}", bg="#1565C0")

        tree.bind("<Double-1>", _on_double)
        _refresh()

    def _build_inventory_panel(self, parent, log_parent):
        """Kho vật tư với lịch sử nhập/xuất hàng - Modernized."""
        main_f = tk.Frame(parent, bg="#FFFFFF"); main_f.pack(fill="both", expand=True)
        
        # Input Form
        hdr = ttk.LabelFrame(main_f, text="📦 Cấu hình Vật tư & Quy đổi (UoM/Batches)")
        hdr.pack(fill="x", padx=10, pady=10)
        
        fields = [
            ("Tên hàng hóa", 28), ("Đơn vị tính Hiển thị", 10), ("Đơn vị tính Cơ sở", 10),
            ("Tỷ lệ quy đổi", 10), ("Số lượng tồn kho (Cơ sở)", 12), ("Giá vốn", 12),
            ("Giá bán", 12), ("Số lô / Hạn sử dụng", 15), ("Phân loại", 15), ("Ngưỡng báo động", 12)
        ]
        self._inv_entries = []
        inv_cats = ["Hàng hóa", "Nguyên liệu", "Công cụ", "Dịch vụ", "Thành phẩm", "Khác"]
        inv_cols = min(3, form_column_count(1100, preferred=5))
        for i, (lbl, w) in enumerate(fields):
            row = (i // inv_cols) * 2
            col = i % inv_cols
            tk.Label(hdr, text=lbl, font=("Arial", 8)).grid(row=row, column=col, padx=8, pady=(6,0), sticky="w")
            if i == 8: # Category
                e = ttk.Combobox(hdr, values=inv_cats, width=w-2, font=("Segoe UI", 9))
                e.current(0)
            else:
                e = tk.Entry(hdr, width=w, font=("Segoe UI", 9))
                if i == 3: e.insert(0, "1.0")
            e.grid(row=row+1, column=col, padx=8, pady=(0,6), sticky="ew")
            hdr.grid_columnconfigure(col, weight=1)
            self._inv_entries.append(e)
            
        self._inv_state = {'id': None}
        btn_row = ttk.Frame(hdr); btn_row.grid(row=((len(fields)+inv_cols-1)//inv_cols)*2, column=0, columnspan=inv_cols, pady=10, sticky="w")
        self._inv_btn = tk.Button(btn_row, text=f"➕ {self.lbl['add_btn']}", bg="#388E3C", fg="white", 
                                  font=("Segoe UI", 9, "bold"), width=18, command=self._inv_save)
        self._inv_btn.pack(side="left", padx=5)
        tk.Button(btn_row, text=f"🗑️ {self.lbl['delete_btn']}", command=self._inv_del, 
                  bg="#D32F2F", fg="white", font=("Segoe UI", 9)).pack(side="left", padx=5)
        
        cols = ("id","name","cat","unit","base_unit","conv","qty","cost","price","batch","min_qty")
        inv_tree_wrap = ttk.Frame(main_f)
        inv_tree_wrap.pack(fill="both", expand=True, padx=10)
        self.tree_inv = ttk.Treeview(inv_tree_wrap, columns=cols, show="headings", height=8)
        wds = [35, 180, 100, 100, 100, 60, 100, 100, 100, 110, 100]
        hds = ["ID","Tên hàng","Phân loại","ĐVT Hiển thị","ĐVT Cơ sở","Tỷ lệ","Tồn kho","Giá vốn","Giá bán","Số lô","Min Qty"]
        for c,h,w in zip(cols,hds,wds):
            self.tree_inv.heading(c,text=h); self.tree_inv.column(c,width=w,anchor="e" if c in ("qty","cost","price","min_qty") else "w")
        self.tree_inv.tag_configure("low_stock", background="#FFEBEE", foreground="#C62828")
        inv_sb_y = ttk.Scrollbar(inv_tree_wrap, orient="vertical", command=self.tree_inv.yview)
        inv_sb_x = ttk.Scrollbar(inv_tree_wrap, orient="horizontal", command=self.tree_inv.xview)
        self.tree_inv.configure(yscrollcommand=inv_sb_y.set, xscrollcommand=inv_sb_x.set)
        self.tree_inv.grid(row=0, column=0, sticky="nsew")
        inv_sb_y.grid(row=0, column=1, sticky="ns")
        inv_sb_x.grid(row=1, column=0, sticky="ew")
        inv_tree_wrap.grid_rowconfigure(0, weight=1)
        inv_tree_wrap.grid_columnconfigure(0, weight=1)
        self.tree_inv.bind("<Double-1>", self._inv_edit)

        log_frm = ttk.LabelFrame(log_parent, text="📋 Lịch sử nhập/xuất hàng — Inventory Log")
        log_frm.pack(fill="both", expand=True, padx=10, pady=10)
        log_ctrl = ttk.Frame(log_frm); log_ctrl.pack(fill="x", pady=5)
        
        tk.Label(log_ctrl, text="Mặt hàng:").pack(side="left", padx=4)
        self.cmb_log_item = ttk.Combobox(log_ctrl, state="readonly", width=25)
        self.cmb_log_item.pack(side="left", padx=4)
        tk.Label(log_ctrl, text="Ngày:").pack(side="left", padx=4)
        self.ent_log_date = tk.Entry(log_ctrl, width=12); self.ent_log_date.pack(side="left", padx=4)
        self.ent_log_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        
        tk.Label(log_ctrl, text="Số lượng:").pack(side="left", padx=4)
        self.ent_log_qty = tk.Entry(log_ctrl, width=8); self.ent_log_qty.pack(side="left", padx=4)
        
        tk.Button(log_ctrl, text="Nhập/Xuất", command=self._inv_log_add, 
                  bg="#1976D2", fg="white", font=("Segoe UI", 9, "bold")).pack(side="left", padx=10)

        self.tree_inv_log = ttk.Treeview(log_frm, columns=("date","item_name","type","qty","note","created_at"),
                                          show="headings", height=7)
        for c,t,w in [("date","Ngày",90),("item_name","Mặt hàng",160),("type","Loại",100),
                      ("qty","Số lượng",80),("note","Ghi chú",160),("created_at","Thời gian",130)]:
            self.tree_inv_log.heading(c,text=t); self.tree_inv_log.column(c,width=w)
        sb = ttk.Scrollbar(log_frm, orient="vertical", command=self.tree_inv_log.yview)
        self.tree_inv_log.configure(yscrollcommand=sb.set)
        self.tree_inv_log.pack(fill="both", expand=True, padx=4, side="left")
        sb.pack(side="right", fill="y")
        self._ref_inv()

    def _inv_save(self):
        vals = [e.get() for e in self._inv_entries]
        # vals order: name, unit, base_unit, conv, qty, cost, price, batch, category
        try:
            if self._inv_state['id'] is not None:
                db.update_inventory(self.db, self._inv_state['id'], *vals)
                self._inv_state['id'] = None; self._inv_btn.config(text=f"➕ {self.lbl['add_btn']}", bg="#388E3C")
            else:
                db.add_inventory(self.db, *vals)
            for i, e in enumerate(self._inv_entries): 
                if i != 3: # Keep conv ratio 1.0
                    e.delete(0,"end")
                    if i in [4,5,6,7]: e.insert(0,"0")
            self._ref_inv()
        except Exception as ex: messagebox.showerror("Error", str(ex))

    def _inv_del(self):
        sel = self.tree_inv.selection()
        if not sel: return
        pk = self.tree_inv.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirm", f"Xóa mặt hàng ID={pk}?"):
            db.delete_inventory(self.db, pk)
            self._inv_state['id'] = None; self._inv_btn.config(text=self.lbl["add_btn"], bg="#388E3C")
            self._ref_inv()

    def _inv_edit(self, event=None):
        sel = self.tree_inv.selection()
        if not sel: return
        row = self.tree_inv.item(sel[0])['values']
        # row: [id, name, cat, unit, base_unit, conv, qty, cost, price, batch]
        # entries order: [name(0), unit(1), base_unit(2), conv(3), qty(4), cost(5), price(6), batch(7), category(8)]
        mapping = [1, 3, 4, 5, 6, 7, 8, 9, 2, 10] # Map Treeview indices to Entry indices
        for entry_idx, tree_idx in enumerate(mapping):
            e = self._inv_entries[entry_idx]
            e.delete(0,"end"); e.insert(0, str(row[tree_idx]))
        self._inv_state['id'] = row[0]
        self._inv_btn.config(text=f"💾 Cập nhật #{row[0]}", bg="#1565C0")

    def _inv_log_add(self):
        item_name = self.cmb_log_item.get().strip()
        if not item_name: messagebox.showwarning("Warning","Chọn mặt hàng trước."); return
        df = db.get_inventory(self.db)
        match = df[df['name'] == item_name]
        if match.empty: messagebox.showerror("Error","Không tìm thấy mặt hàng."); return
        item_id = int(match.iloc[0]['id'])
        log_type = "import" if "import" in self.cmb_log_type.get() else "export"
        try:
            qty = float(self.ent_log_qty.get())
            db.add_inventory_log(self.db, item_id, self.ent_log_date.get(), log_type, qty, self.ent_log_note.get())
            self.ent_log_qty.delete(0,"end"); self.ent_log_note.delete(0,"end")
            self._ref_inv()
        except Exception as e: messagebox.showerror("Error", str(e))

    def _inv_log_del(self):
        sel = self.tree_inv_log.selection()
        if not sel: messagebox.showwarning("Warning","Chọn dòng log cần xóa."); return
        # We store log id as hidden; for now refresh — implement full log-id tracking if needed
        messagebox.showinfo("Thông báo","Chức năng xóa log: cần chọn đúng dòng. Liên hệ admin để xóa thủ công.")

    def _ref_inv(self):
        for i in self.tree_inv.get_children(): self.tree_inv.delete(i)
        df = db.get_inventory(self.db)
        if not df.empty:
            for r in df.itertuples(index=False): 
                tags = ()
                if float(r.qty) <= float(r.min_qty) and float(r.min_qty) > 0:
                    tags = ("low_stock",)
                self.tree_inv.insert("","end", values=list(r), tags=tags)
            self.cmb_log_item['values'] = df['name'].tolist()
        for i in self.tree_inv_log.get_children(): self.tree_inv_log.delete(i)
        logdf = db.get_inventory_log(self.db)
        if not logdf.empty:
            for r in logdf.itertuples(index=False):
                self.tree_inv_log.insert("","end", values=(r.date, r.item_name, r.type, r.qty, r.note, r.created_at))

    # ── INVOICE TAB ───────────────────────────────────────────
    def _build_invoice_tab(self):
        import invoice_gen
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self.lbl.get("tab_invoices", "Hóa đơn"))

        # Client selector — isolated per-client
        cf = ttk.LabelFrame(tab, text="1. Chọn Khách hàng" if self.settings.get("language","vi") == "vi" else "1. Client Selection")
        cf.pack(fill="x", padx=6, pady=4)
        tk.Label(cf, text=self.lbl["client"]).pack(side="left", padx=6)
        self.cmb_inv_client = ttk.Combobox(cf, state="readonly", width=30)
        self.cmb_inv_client.pack(side="left", padx=6)
        self.cmb_inv_client.bind("<<ComboboxSelected>>", self._on_inv_client_select)
        self._lbl_client_info = tk.Label(cf, text="", fg="#1565C0", font=("Arial",9))
        self._lbl_client_info.pack(side="left", padx=10)
        tk.Button(cf, text="🔄 Tải DS khách", command=self._load_inv_clients, width=14).pack(side="right", padx=6)

        # Invoice type + number
        hf = ttk.LabelFrame(tab, text="2. Thông tin hóa đơn")
        hf.pack(fill="x", padx=6, pady=2)
        tk.Label(hf, text="Loại Hóa đơn:").grid(row=0, column=0, padx=6, pady=3, sticky="w")
        self.inv_type_var = tk.StringVar(value="01GTGT")
        ttk.Combobox(hf, textvariable=self.inv_type_var,
                     values=["01GTGT (GTGT)","02BH (Bán hàng)"], state="readonly", width=16).grid(row=0, column=1, padx=4)
        self.inv_type_var.trace_add("write", self._auto_inv_number)

        tk.Label(hf, text="Ngày Hóa đơn:").grid(row=0, column=2, padx=6, sticky="w")
        self.ent_inv_date = tk.Entry(hf, width=14)
        self.ent_inv_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.ent_inv_date.grid(row=0, column=3, padx=4)

        tk.Label(hf, text="Số Hóa đơn (tự động):").grid(row=0, column=4, padx=6, sticky="w")
        self.ent_inv_num = tk.Entry(hf, width=22, state="readonly", fg="#1565C0",
                                    font=("Consolas",10,"bold"))
        self.ent_inv_num.grid(row=0, column=5, padx=4)

        tk.Label(hf, text="Thuế suất GTGT (%):").grid(row=0, column=6, padx=6, sticky="w")
        self.ent_inv_vat = tk.Entry(hf, width=6)
        vat_val = float(self.settings.get("vat_rate", 0.08))
        self.ent_inv_vat.insert(0, str(int(vat_val * 100)))
        self.ent_inv_vat.grid(row=0, column=7, padx=4)

        # Items table
        lf = ttk.LabelFrame(tab, text="3. Danh sách hàng hóa / dịch vụ" if self.settings.get("language","vi") == "vi" else "3. Items List")
        lf.pack(fill="both", padx=6, pady=2, expand=True)

        # Inventory picker row - SMART AUTO-FILL
        pick = ttk.Frame(lf); pick.pack(fill="x", pady=2)
        tk.Label(pick, text="📦 Chọn từ kho:", fg="#1565C0", font=("Arial",9,"bold")).pack(side="left", padx=4)
        self.cmb_inv_pick = ttk.Combobox(pick, state="readonly", width=32)
        self.cmb_inv_pick.pack(side="left", padx=4)
        self.cmb_inv_pick.bind("<<ComboboxSelected>>", lambda e: self._inv_pick_fill())
        tk.Button(pick, text="🔄", command=self._inv_pick_refresh, width=3).pack(side="left", padx=5)
        tk.Label(pick, text="(Tự động điền SL=1)", fg="#888", font=("Arial",8)).pack(side="left", padx=4)
        self._inv_pick_refresh()

        # Manual entry row
        inp2 = ttk.Frame(lf); inp2.pack(fill="x", pady=3)
        tk.Label(inp2, text="Tên hàng:").pack(side="left", padx=2)
        self.ent_item_name  = tk.Entry(inp2, width=28); self.ent_item_name.pack(side="left", padx=3)
        tk.Label(inp2, text="ĐVT").pack(side="left")
        self.ent_item_unit  = tk.Entry(inp2, width=8);  self.ent_item_unit.pack(side="left", padx=3)
        tk.Label(inp2, text="SL").pack(side="left")
        self.ent_item_qty   = tk.Entry(inp2, width=8);  self.ent_item_qty.pack(side="left", padx=3)
        tk.Label(inp2, text="Đơn giá").pack(side="left")
        self.ent_item_price = tk.Entry(inp2, width=14); self.ent_item_price.pack(side="left", padx=3)
        tk.Button(inp2, text="+ Thêm dòng", command=self._inv_add_item, bg="#388E3C", fg="white").pack(side="left", padx=6)
        tk.Button(inp2, text="Xóa dòng", command=self._inv_del_item, bg="#C62828", fg="white").pack(side="left")

        self.tree_inv_items = ttk.Treeview(lf, columns=("name","unit","qty","price","total"),
                                            show="headings", height=8)
        for c,t,w in [("name","Tên SP/DV",220),("unit","ĐVT",60),("qty","SL",70),
                      ("price","Đơn giá",110),("total","Thành tiền",110)]:
            self.tree_inv_items.heading(c,text=t); self.tree_inv_items.column(c,width=w)
        self.tree_inv_items.pack(fill="both", expand=True, padx=4)

        # Generate button
        bf2 = ttk.Frame(tab); bf2.pack(fill="x", padx=6, pady=4)
        tk.Button(bf2, text=self.lbl["gen_invoice_btn"], command=self._generate_invoice,
                  bg="#1565C0", fg="white", font=("Arial",11,"bold"), width=26).pack(side="left")
        self.lbl_inv_total = tk.Label(bf2, text="Tổng: —", font=("Arial",11,"bold"), fg="#388E3C")
        self.lbl_inv_total.pack(side="left", padx=20)
        tk.Button(bf2, text="🗑 Xóa mục hàng", command=self._inv_clear_items).pack(side="right", padx=6)

        self._load_inv_clients()
        self._auto_inv_number()

    def _load_inv_clients(self):
        df = db.get_clients(self.db)
        if not df.empty:
            self.cmb_inv_client['values'] = df['name'].tolist()
        else:
            self.cmb_inv_client['values'] = []
        self._current_inv_client_id = None
        self._lbl_client_info.config(text="")

    def _on_inv_client_select(self, event=None):
        name = self.cmb_inv_client.get()
        cli = db.get_client_by_name(self.db, name)
        if cli:
            self._current_inv_client_id = cli['id']
            info = f"MST: {cli.get('tax_code','')}  |  ĐC: {cli.get('address','')}"
            self._lbl_client_info.config(text=info)
        else:
            self._current_inv_client_id = None
            self._lbl_client_info.config(text="")

    def _auto_inv_number(self, *_):
        inv_type = self.inv_type_var.get()
        num = db.next_invoice_number(self.db, inv_type)
        self.ent_inv_num.config(state="normal")
        self.ent_inv_num.delete(0,"end"); self.ent_inv_num.insert(0, num)
        self.ent_inv_num.config(state="readonly")

    def _inv_add_item(self):
        try:
            name  = self.ent_item_name.get().strip()
            unit  = self.ent_item_unit.get().strip()
            qty   = float(self.ent_item_qty.get())
            price = float(self.ent_item_price.get().replace(",",""))
            total = qty * price
            self.tree_inv_items.insert("","end", values=(name, unit, f"{qty:,.2f}",
                                                          f"{price:,.0f}", f"{total:,.0f}"))
            self.ent_item_name.delete(0,"end"); self.ent_item_unit.delete(0,"end")
            self.ent_item_qty.delete(0,"end");  self.ent_item_price.delete(0,"end")
            self._update_inv_total()
        except Exception as e: messagebox.showerror("Error", str(e))
    def _inv_pick_refresh(self):
        """Refresh inventory picker dropdown from DB."""
        inv_df = db.get_inventory(self.db)
        if not inv_df.empty:
            self._inv_pick_data = {f"{r.name} ({r.unit}) — {r.price:,.0f}": r
                                   for r in inv_df.itertuples(index=False)}
            if hasattr(self, 'cmb_inv_pick'):
                self.cmb_inv_pick['values'] = list(self._inv_pick_data.keys())
        else:
            self._inv_pick_data = {}
            if hasattr(self, 'cmb_inv_pick'):
                self.cmb_inv_pick['values'] = ["(Chưa có hàng trong kho)"]

    def _inv_pick_fill(self):
        """Fill invoice item fields from selected inventory item."""
        sel = self.cmb_inv_pick.get()
        if not sel or sel.startswith("("): return
        row = self._inv_pick_data.get(sel)
        if row is None: return
        self.ent_item_name.delete(0,"end"); self.ent_item_name.insert(0, row.name)
        self.ent_item_unit.delete(0,"end"); self.ent_item_unit.insert(0, row.unit)
        self.ent_item_price.delete(0,"end"); self.ent_item_price.insert(0, f"{row.price:,.0f}")
        self.ent_item_qty.delete(0,"end"); self.ent_item_qty.insert(0, "1")

    def _inv_del_item(self):
        sel = self.tree_inv_items.selection()
        if sel: self.tree_inv_items.delete(sel[0]); self._update_inv_total()

    def _inv_clear_items(self):
        for i in self.tree_inv_items.get_children(): self.tree_inv_items.delete(i)
        self._update_inv_total()

    def _update_inv_total(self):
        total = sum(float(self.tree_inv_items.item(i)['values'][4].replace(",",""))
                    for i in self.tree_inv_items.get_children())
        self.lbl_inv_total.config(text=f"Tổng hàng: {total:,.0f} VND")

    def _generate_invoice(self):
        import invoice_gen
        if not self._current_inv_client_id:
            messagebox.showwarning("Cảnh báo","Chọn khách hàng trước!"); return
        rows = self.tree_inv_items.get_children()
        if not rows: messagebox.showwarning("Cảnh báo","Chưa có mặt hàng nào!"); return

        cli = db.get_client_by_name(self.db, self.cmb_inv_client.get())
        items = []
        for r in rows:
            v = self.tree_inv_items.item(r)['values']
            items.append({"name":v[0],"unit":v[1],
                          "qty":float(str(v[2]).replace(",","")),
                          "price":float(str(v[3]).replace(",",""))})

        s = self.settings
        inv_num = self.ent_inv_num.get()
        inv_date = self.ent_inv_date.get()
        inv_type = self.inv_type_var.get()
        vat_rate = float(self.ent_inv_vat.get()) / 100.0
        seller_name = s.get("company_legal_rep") or s.get("company_name", "")

        try:
            validate_invoice_payload({
                "company_name": s.get("company_name", ""),
                "buyer_full_name": cli.get("name", ""),
                "seller_full_name": seller_name,
                "address": cli.get("address", ""),
                "items": items,
            })
        except InvoiceValidationError as ex:
            messagebox.showwarning("Thiếu dữ liệu hóa đơn", str(ex))
            return

        try:
            if inv_type == "01GTGT":
                path, total = invoice_gen.gen_pdf_gtgt(
                    inv_num, inv_date,
                    s.get("company_name",""), s.get("company_address",""),
                    s.get("company_tax_code",""), s.get("bank_name",""), s.get("bank_account",""),
                    cli.get("name",""), cli.get("address",""), cli.get("tax_code",""),
                    items, vat_rate=vat_rate,
                    currency=s.get("currency","VND"), currency_decimals=int(s.get("currency_decimals",0)),
                    settings=s
                )
            else:
                path, total = invoice_gen.gen_pdf_bh(
                    inv_num, inv_date,
                    s.get("company_name",""), s.get("company_address",""),
                    s.get("company_tax_code",""), s.get("bank_name",""), s.get("bank_account",""),
                    cli.get("name",""), cli.get("address",""),
                    items, currency=s.get("currency","VND"),
                    currency_decimals=int(s.get("currency_decimals",0)),
                    settings=s
                )
            subtotal = sum(it["qty"]*it["price"] for it in items)
            vat_amt  = subtotal * vat_rate if inv_type=="01GTGT" else 0
            invoice_result = db.save_invoice(
                self.db, inv_num, inv_type, self._current_inv_client_id,
                inv_date, json.dumps(items, ensure_ascii=False),
                subtotal, vat_amt, total, path,
                company_name=s.get("company_name", ""),
                seller_full_name=s.get("company_legal_rep", "") or s.get("company_name", ""),
                auto_post=True,
            )
            messagebox.showinfo("Thành công", f"Đã xuất hóa đơn:\n{path}\nChứng từ kế toán đã được ghi sổ.")
            self._inv_clear_items(); self._auto_inv_number()
            self._refresh_all()
            os.startfile(path)
        except Exception as e: messagebox.showerror("Lỗi xuất HĐ", str(e))

    # ── INVOICE HISTORY TAB ───────────────────────────────────
    def _build_invoice_history_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self.lbl.get("tab_history", "Lịch sử Hóa đơn"))

        # Filter by client
        ff = ttk.Frame(tab); ff.pack(fill="x", padx=6, pady=4)
        tk.Label(ff, text="Lọc theo khách hàng:").pack(side="left", padx=4)
        self.cmb_inv_hist_client = ttk.Combobox(ff, state="readonly", width=28)
        self.cmb_inv_hist_client.pack(side="left", padx=4)
        self.cmb_inv_hist_client.bind("<<ComboboxSelected>>", lambda e: self._refresh_inv_history())
        tk.Button(ff, text="Tất cả", command=self._inv_hist_show_all).pack(side="left", padx=4)
        tk.Button(ff, text="🔄 Làm mới", command=self._refresh_inv_history).pack(side="left", padx=4)

        cols = ("inv_number","inv_type","client","date","subtotal","vat","total","pdf_path")
        self.tree_inv_hist = ttk.Treeview(tab, columns=cols, show="headings")
        widths3 = [170,70,160,90,110,90,110,200]
        heads3  = ["Số HĐ","Loại","Khách hàng","Ngày","Tiền hàng","VAT","Tổng cộng","File PDF"]
        for c,h,w in zip(cols,heads3,widths3):
            self.tree_inv_hist.heading(c,text=h); self.tree_inv_hist.column(c,width=w)
        sb = ttk.Scrollbar(tab, orient="vertical", command=self.tree_inv_hist.yview)
        self.tree_inv_hist.configure(yscrollcommand=sb.set)
        self.tree_inv_hist.pack(fill="both", expand=True, padx=6, side="left")
        sb.pack(side="right", fill="y")
        self.tree_inv_hist.bind("<Double-1>", self._open_invoice_pdf)
        
        # Action Buttons
        ab = ttk.Frame(tab); ab.pack(fill="x", padx=6, pady=2)
        tk.Button(ab, text="🗑 XÓA HÓA ĐƠN ĐÃ CHỌN", command=self._delete_invoice_hist, 
                  bg="#D32F2F", fg="white", font=("Segoe UI", 9, "bold"), padx=10).pack(side="right", padx=10)

        # Summary bar
        sf = ttk.Frame(tab); sf.pack(fill="x", padx=6, pady=2)
        self.lbl_inv_hist_sum = tk.Label(sf, text="", font=("Arial",10,"bold"), fg="#1565C0")
        self.lbl_inv_hist_sum.pack(side="left")

        self._refresh_inv_history()

    def _inv_hist_show_all(self):
        self.cmb_inv_hist_client.set("")
        self._refresh_inv_history()

    def _refresh_inv_history(self):
        if not hasattr(self, 'tree_inv_hist'): return
        for i in self.tree_inv_hist.get_children(): self.tree_inv_hist.delete(i)
        # Populate client filter combo
        df_cli = db.get_clients(self.db)
        if not df_cli.empty:
            self.cmb_inv_hist_client['values'] = [""] + df_cli['name'].tolist()

        sel_name = self.cmb_inv_hist_client.get().strip()
        client_id = None
        if sel_name and not df_cli.empty:
            match = df_cli[df_cli['name'] == sel_name]
            if not match.empty:
                client_id = int(match.iloc[0]['id'])

        df = db.get_invoices(self.db, client_id=client_id)
        total_sum = 0
        if not df.empty:
            for r in df.itertuples(index=False):
                cli_name = ""
                if not df_cli.empty:
                    m = df_cli[df_cli['id'] == r.client_id]
                    if not m.empty: cli_name = m.iloc[0]['name']
                self.tree_inv_hist.insert("","end", values=(
                    r.inv_number, r.inv_type, cli_name, r.date,
                    f"{r.subtotal:,.0f}", f"{r.vat:,.0f}", f"{r.total:,.0f}",
                    r.pdf_path or ""
                ))
                total_sum += float(r.total or 0)
        self.lbl_inv_hist_sum.config(text=f"Tổng giá trị hóa đơn: {total_sum:,.0f} VND  ({len(df) if not df.empty else 0} hóa đơn)")

    def _open_invoice_pdf(self, event=None):
        sel = self.tree_inv_hist.selection()
        if not sel: return
        pdf_path = self.tree_inv_hist.item(sel[0])['values'][7]
        if pdf_path and os.path.exists(str(pdf_path)):
            os.startfile(str(pdf_path))
        else:
            messagebox.showwarning("Không tìm thấy","File PDF không tồn tại hoặc chưa được tạo.")

    def _delete_invoice_hist(self):
        sel = self.tree_inv_hist.selection()
        if not sel:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn hóa đơn cần xóa!")
            return
        
        vals = self.tree_inv_hist.item(sel[0])['values']
        inv_num = vals[0]
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa hóa đơn {inv_num}?\nToàn bộ định khoản kế toán liên quan cũng sẽ bị xóa!"):
            try:
                db.delete_invoice(self.db, inv_num)
                messagebox.showinfo("Thành công", f"Đã xóa hóa đơn {inv_num}")
                self._refresh_inv_history()
                self._refresh_all()
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))

    # ── TRANSACTION HISTORY TAB ───────────────────────────────
    def _build_history_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self.lbl.get("tab_ledger", "Sổ cái"))

        ff = ttk.Frame(tab); ff.pack(fill="x", padx=6, pady=4)
        tk.Label(ff, text=self.lbl["account"]).pack(side="left", padx=4)
        self.ent_hist_acc = tk.Entry(ff, width=12); self.ent_hist_acc.pack(side="left", padx=4)
        tk.Button(ff, text="Tra cứu", command=self._refresh_history,
                  bg="#1565C0", fg="white").pack(side="left", padx=6)
        tk.Button(ff, text="Tất cả", command=self._hist_show_all).pack(side="left", padx=4)
        
        # ADVANCED FILTER BUTTON
        tk.Button(ff, text="🔍 Lọc Nâng Cao", command=self._open_advanced_filter,
                  bg="#FF9800", fg="white", font=("Segoe UI", 9, "bold")).pack(side="right", padx=4)

        # EXCEL EXPORT BUTTON
        tk.Button(ff, text="📥 Xuất ra Excel (Export)", command=self._export_history_excel,
                  bg="#388E3C", fg="white", font=("Segoe UI", 9, "bold")).pack(side="right", padx=10)

        cols = ("date","ref","note","type","account","debit","credit","running_balance")
        self.tree_history = ttk.Treeview(tab, columns=cols, show="headings")
        widths = [80,120,180,80,65,100,100,110]
        heads  = ["Ngày","Số CT","Diễn giải","Loại","TK","Nợ","Có","Số dư"]
        for c,h,w in zip(cols,heads,widths):
            self.tree_history.heading(c,text=h)
            self.tree_history.column(c,width=w,anchor="e" if c in ("debit","credit","running_balance") else "w")
        sb = ttk.Scrollbar(tab, orient="vertical", command=self.tree_history.yview)
        self.tree_history.configure(yscrollcommand=sb.set)
        self.tree_history.pack(fill="both", expand=True, padx=6, side="left")
        sb.pack(side="right", fill="y")
        self._refresh_history()

    def _hist_show_all(self):
        self.ent_hist_acc.delete(0,"end")
        self._refresh_history()

    def _refresh_history(self, start_date=None, end_date=None):
        for i in self.tree_history.get_children(): self.tree_history.delete(i)
        acc = self.ent_hist_acc.get().strip() or None
        df = db.get_account_history_df(self.db, acc)
        if not df.empty:
            if start_date:
                df = df[df['date'] >= start_date]
            if end_date:
                df = df[df['date'] <= end_date]
            for r in df.itertuples(index=False):
                self.tree_history.insert("","end", values=(
                    r.date, r.ref, r.note, r.type, r.account,
                    f"{r.debit:,.0f}" if r.debit > 0 else "",
                    f"{r.credit:,.0f}" if r.credit > 0 else "",
                    f"{r.running_balance:,.0f}"
                ))

    def _open_advanced_filter(self):
        win = tk.Toplevel(self)
        win.title("Lọc Giao Dịch Nâng Cao")
        win.geometry("350x200")
        win.transient(self)
        win.grab_set()

        f = ttk.Frame(win, padding=20)
        f.pack(fill="both", expand=True)

        tk.Label(f, text="Từ ngày (YYYY-MM-DD):").grid(row=0, column=0, pady=10, sticky="w")
        ent_start = tk.Entry(f, width=15)
        ent_start.grid(row=0, column=1, padx=10)

        tk.Label(f, text="Đến ngày (YYYY-MM-DD):").grid(row=1, column=0, pady=10, sticky="w")
        ent_end = tk.Entry(f, width=15)
        ent_end.grid(row=1, column=1, padx=10)

        def apply_filter():
            sd = ent_start.get().strip()
            ed = ent_end.get().strip()
            self._refresh_history(start_date=sd, end_date=ed)
            win.destroy()

        tk.Button(f, text="Áp dụng (Apply)", command=apply_filter, bg="#1565C0", fg="white", width=15).grid(row=2, column=0, columnspan=2, pady=20)

    def _export_history_excel(self):
        from tkinter import filedialog
        import pandas as pd
        import os
        
        acc = self.ent_hist_acc.get().strip() or None
        df = db.get_account_history_df(self.db, acc)
        if df.empty:
            messagebox.showinfo("Lỗi", "Không có dữ liệu để xuất!")
            return
            
        fpath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Lưu file Excel"
        )
        if fpath:
            try:
                # Format numeric columns for Excel
                df['debit'] = pd.to_numeric(df['debit'])
                df['credit'] = pd.to_numeric(df['credit'])
                df['running_balance'] = pd.to_numeric(df['running_balance'])
                df.to_excel(fpath, index=False, sheet_name="Transaction History")
                messagebox.showinfo("Thành công", f"Đã xuất ra Excel thành công:\n{fpath}")
                os.startfile(fpath)
            except Exception as e:
                messagebox.showerror("Lỗi xuất Excel", str(e))

    # ── REPORTS TAB ───────────────────────────────────────────
    def _build_reports_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self.lbl.get("tab_reports", "Báo cáo"))
        sub = ttk.Notebook(tab); sub.pack(fill="both", expand=True, padx=4, pady=4)

        # --- B02-DNN (TT133) ---
        t0 = ttk.Frame(sub)
        lbl_t0 = "📊 Kết quả Kinh doanh (TT 133)" if self.settings.get("language","vi") == "vi" else "📊 Income Statement (TT 133)"
        sub.add(t0, text=lbl_t0)
        self._build_b02_panel(t0)

        # --- B02-DN (TT99/2025) ---
        t1 = ttk.Frame(sub)
        lbl_t1 = "📊 Kết quả Kinh doanh (TT 99/2025)" if self.settings.get("language","vi") == "vi" else "📊 Income Statement (TT 99/2025)"
        sub.add(t1, text=lbl_t1)
        self._build_b02_tt99_panel(t1)

        # --- Revenue Summary ---
        t2 = ttk.Frame(sub)
        lbl_t2 = "📈 Tổng hợp Doanh thu" if self.settings.get("language","vi") == "vi" else "📈 Revenue Summary"
        sub.add(t2, text=lbl_t2)
        self._build_revenue_panel(t2)

    def _build_b02_panel(self, parent):
        """B02-DNN — Báo cáo KQHĐKD theo TT133."""
        ctl = ttk.Frame(parent); ctl.pack(fill="x", padx=6, pady=4)
        tk.Label(ctl, text="Kỳ báo cáo:").pack(side="left", padx=4)
        self.ent_rpt_from = tk.Entry(ctl, width=12)
        self.ent_rpt_from.insert(0, f"{datetime.date.today().year}-01-01"); self.ent_rpt_from.pack(side="left")
        tk.Label(ctl, text="đến").pack(side="left", padx=4)
        self.ent_rpt_to = tk.Entry(ctl, width=12)
        self.ent_rpt_to.insert(0, datetime.date.today().strftime("%Y-%m-%d")); self.ent_rpt_to.pack(side="left")
        tk.Button(ctl, text="Tạo báo cáo", command=self._refresh_reports,
                  bg="#1565C0", fg="white").pack(side="left", padx=10)

        self.txt_report = tk.Text(parent, font=("Consolas",10), wrap="none", height=32, padx=10, pady=6)
        
        def _add_copy_menu(w):
            m = tk.Menu(w, tearoff=0)
            m.add_command(label="Sao chép (Copy)", command=lambda: w.event_generate("<<Copy>>"))
            def show_m(e): m.post(e.x_root, e.y_root)
            w.bind("<Button-3>", show_m)
        _add_copy_menu(self.txt_report)

        def _make_readonly(event):
            if event.state & 4 and event.keysym.lower() in ('c', 'a'): return None
            if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Prior', 'Next', 'Home', 'End'): return None
            return "break"
        self.txt_report.bind("<Key>", _make_readonly)
        sb_y = ttk.Scrollbar(parent, orient="vertical", command=self.txt_report.yview)
        sb_x = ttk.Scrollbar(parent, orient="horizontal", command=self.txt_report.xview)
        self.txt_report.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        
        self.txt_report.pack(fill="both", expand=True, padx=6)
        sb_y.pack(side="right", fill="y", in_=self.txt_report) # Overlay or side
        sb_x.pack(side="bottom", fill="x")

    def _build_b02_tt99_panel(self, parent):
        """B02-DN — Mẫu mới theo Thông tư 99/2025/TT-BTC, Phụ lục IV."""
        # Warning banner
        warn = tk.Label(parent, text=(
            "⚠  Thông tư 99/2025/TT-BTC (Mẫu B 02 - DN, Phụ lục IV) áp dụng từ năm tài chính 2025.\n"
            "    Doanh nghiệp lập BCTC theo TT200/2014 dùng mẫu này. DN theo TT133 dùng tab B02-DNN.\n"
            "    Hãy kiểm tra với kế toán/kiểm toán trước khi nộp báo cáo chính thức."
        ), bg="#FFF9C4", fg="#5D4037", font=("Arial",9), justify="left", padx=8, pady=6, wraplength=900)
        warn.pack(fill="x", padx=6, pady=4)

        ctl = ttk.Frame(parent); ctl.pack(fill="x", padx=6, pady=4)
        tk.Label(ctl, text="Năm tài chính:").pack(side="left", padx=4)
        self.ent_tt99_year = tk.Entry(ctl, width=8)
        self.ent_tt99_year.insert(0, str(datetime.date.today().year)); self.ent_tt99_year.pack(side="left")
        tk.Button(ctl, text="Tự động điền từ dữ liệu", command=self._fill_tt99_from_data,
                  bg="#1565C0", fg="white").pack(side="left", padx=10)

        self.txt_tt99 = tk.Text(parent, font=("Consolas",10), wrap="none", height=30, padx=10)
        
        def _add_copy_menu(w):
            m = tk.Menu(w, tearoff=0)
            m.add_command(label="Sao chép (Copy)", command=lambda: w.event_generate("<<Copy>>"))
            def show_m(e): m.post(e.x_root, e.y_root)
            w.bind("<Button-3>", show_m)
        _add_copy_menu(self.txt_tt99)

        def _make_readonly(event):
            if event.state & 4 and event.keysym.lower() in ('c', 'a'): return None
            if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Prior', 'Next', 'Home', 'End'): return None
            return "break"
        self.txt_tt99.bind("<Key>", _make_readonly)
        sb_y2 = ttk.Scrollbar(parent, orient="vertical", command=self.txt_tt99.yview)
        sb_x2 = ttk.Scrollbar(parent, orient="horizontal", command=self.txt_tt99.xview)
        self.txt_tt99.configure(yscrollcommand=sb_y2.set, xscrollcommand=sb_x2.set)
        
        self.txt_tt99.pack(fill="both", expand=True, padx=6)
        sb_y2.pack(side="right", fill="y", in_=self.txt_tt99)
        sb_x2.pack(side="bottom", fill="x")
        self._fill_tt99_from_data()

    def _fill_tt99_from_data(self):
        year = self.ent_tt99_year.get().strip() if hasattr(self,"ent_tt99_year") else str(datetime.date.today().year)
        df = db.get_flat_df(self.db)
        rev = exp = cogs = gross = profit = tax = 0
        if not df.empty:
            rev_df = df[df['account'].astype(str).str.startswith('511') & (df['credit'] > 0)]
            exp_df = df[df['account'].astype(str).str.startswith('64') & (df['debit'] > 0)]
            cogs_df = df[df['account'].astype(str).str.startswith('632') & (df['debit'] > 0)]
            rev = rev_df['credit'].sum() if not rev_df.empty else 0
            cogs = cogs_df['debit'].sum() if not cogs_df.empty else 0
            exp = exp_df['debit'].sum() if not exp_df.empty else 0
            gross = rev - cogs
            profit = rev - cogs - exp
            tax = max(0, profit) * 0.20

        template = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH                                      ║
║  Mẫu số B 02 - DN  (Phụ lục IV — Thông tư 99/2025/TT-BTC)                  ║
║  Năm tài chính: {year:<60}║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Chỉ tiêu                                             Mã số    Số tiền (VND)║
╠══════════════════════════════════════════════════════════════════════════════╣
║  I. Doanh thu bán hàng & cung cấp dịch vụ              01   {rev:>18,.0f} ║
║  II. Các khoản giảm trừ doanh thu                       02              0   ║
║  III. Doanh thu thuần (01 - 02)                         10   {rev:>18,.0f} ║
║  IV. Giá vốn hàng bán                                   11   {cogs:>18,.0f} ║
║  V. Lợi nhuận gộp (10 - 11)                             20   {gross:>18,.0f} ║
║  VI. Doanh thu hoạt động tài chính                      21              0   ║
║  VII. Chi phí tài chính                                 22              0   ║
║  VIII. Chi phí quản lý kinh doanh                       25   {exp:>18,.0f} ║
║  IX. Lợi nhuận thuần từ HĐKD (20+21-22-25)             30   {profit:>18,.0f} ║
║  X. Thu nhập khác                                       31              0   ║
║  XI. Chi phí khác                                       32              0   ║
║  XII. Lợi nhuận khác (31 - 32)                         40              0   ║
║  XIII. Tổng lợi nhuận kế toán trước thuế (30+40)       50   {profit:>18,.0f} ║
║  XIV. Chi phí thuế TNDN (20%)                           51   {tax:>18,.0f} ║
║  XV. Lợi nhuận sau thuế TNDN (50 - 51)                 60   {max(0,profit-tax):>18,.0f} ║
╚══════════════════════════════════════════════════════════════════════════════╝

  ⚠ Lưu ý: Số liệu tự động từ sổ kế toán. Kiểm tra lại trước khi nộp chính thức.
  Thời điểm nộp BCTC: Trong vòng 90 ngày kể từ ngày kết thúc năm tài chính
  (Điều 109, Luật Doanh nghiệp 2020).
"""
        if hasattr(self, "txt_tt99"):
            self.txt_tt99.delete("1.0","end")
            self.txt_tt99.insert("1.0", template.strip())

    def _build_revenue_panel(self, parent):
        """Revenue summary filter by day/month/year."""
        ctl = ttk.Frame(parent); ctl.pack(fill="x", padx=6, pady=4)
        tk.Label(ctl, text="Lọc theo:").pack(side="left", padx=4)
        self.rev_period_var = tk.StringVar(value="month")
        for v,t in [("day","Ngày"),("month","Tháng"),("year","Năm")]:
            tk.Radiobutton(ctl, text=t, variable=self.rev_period_var, value=v,
                           command=self._refresh_revenue).pack(side="left", padx=6)

        cols2 = ("period","revenue","expense","profit")
        self.tree_revenue = ttk.Treeview(parent, columns=cols2, show="headings")
        for c,t,w in [("period","Kỳ",110),("revenue","Doanh thu",140),
                      ("expense","Chi phí",140),("profit","Lợi nhuận ước",140)]:
            self.tree_revenue.heading(c,text=t); self.tree_revenue.column(c,width=w,anchor="e" if c!="period" else "w")
        sb3 = ttk.Scrollbar(parent, orient="vertical", command=self.tree_revenue.yview)
        self.tree_revenue.configure(yscrollcommand=sb3.set)
        self.tree_revenue.pack(fill="both", expand=True, padx=6, side="left")
        sb3.pack(side="right", fill="y")
        self._refresh_revenue()

    def _refresh_revenue(self):
        for i in self.tree_revenue.get_children(): self.tree_revenue.delete(i)
        period = self.rev_period_var.get() if hasattr(self,"rev_period_var") else "month"
        df = db.get_revenue_summary(self.db, period)
        if not df.empty:
            for r in df.itertuples(index=False):
                profit = float(r.revenue) - float(r.expense)
                self.tree_revenue.insert("","end", values=(
                    r.period,
                    f"{r.revenue:,.0f}",
                    f"{r.expense:,.0f}",
                    f"{profit:,.0f}"
                ))

    def _refresh_reports(self):
        """Refresh B02-DNN income statement."""
        if not hasattr(self, "txt_report"): return
        df = db.get_flat_df(self.db)
        if df.empty:
            self.txt_report.config(state="normal")
            self.txt_report.delete("1.0","end")
            self.txt_report.insert("1.0","(Chưa có dữ liệu)\n"); return

        rev_df  = df[df['account'].astype(str).str.startswith('511') & (df['credit']>0)]
        exp_df  = df[df['account'].astype(str).str.startswith('64') & (df['debit']>0)]
        cogs_df = df[df['account'].astype(str).str.startswith('632') & (df['debit']>0)]
        rev   = rev_df['credit'].sum() if not rev_df.empty else 0
        cogs  = cogs_df['debit'].sum() if not cogs_df.empty else 0
        exp   = exp_df['debit'].sum() if not exp_df.empty else 0
        profit = rev - cogs - exp
        tax    = max(0, profit) * 0.20

        report = (
            f"{'─'*62}\n"
            f"  BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH (B02-DNN)\n"
            f"  Mẫu theo Thông tư 133/2016/TT-BTC\n"
            f"{'─'*62}\n"
            f"  Doanh thu bán hàng (TK 511):   {rev:>18,.0f} VND\n"
            f"  Giá vốn hàng bán (TK 632):    ({cogs:>18,.0f}) VND\n"
            f"  Chi phí QLDN (TK 64x):        ({exp:>18,.0f}) VND\n"
            f"{'─'*62}\n"
            f"  Lợi nhuận trước thuế:          {profit:>18,.0f} VND\n"
            f"  Thuế TNDN (20%):              ({tax:>18,.0f}) VND\n"
            f"{'─'*62}\n"
            f"  LỢI NHUẬN SAU THUẾ:            {max(0,profit-tax):>18,.0f} VND\n"
            f"{'─'*62}\n\n"
            f"  Ngày tạo: {datetime.datetime.now():%d/%m/%Y %H:%M}\n"
        )
        self.txt_report.delete("1.0","end")
        self.txt_report.insert("1.0", report)
        self._fill_tt99_from_data()
        self._refresh_revenue()

    # ── TAB CREATION METHODS ─────────────────────────────────────────
    def _build_analytics_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self.lbl.get("tab_analytics", "Phân tích"))
        try:
            analytics.build_analytics_tab(self, tab, self.db, self.settings, self.lbl)
        except Exception as e:
            tk.Label(tab, text=f"Analytics error: {e}", fg="red").pack(pady=20)

    def _build_payroll_tab(self):
        tabs_extra.build_payroll_tab(self, self.nb, self.lbl)

    def _build_tools_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self.lbl.get("tab_tools", "Công cụ"))
        sub = ttk.Notebook(tab); sub.pack(fill="both", expand=True, padx=12, pady=12)
        
        t1 = ttk.Frame(sub); tabs_extra.build_tax_calc_tab(self, sub, self.lbl)
        t2 = ttk.Frame(sub); tabs_extra.build_legal_docs_tab(self, sub, self.lbl)
        t3 = ttk.Frame(sub); tabs_extra.build_manual_tab(self, sub, self.lbl)
        t4 = ttk.Frame(sub); tabs_extra.build_ai_tab(self, sub, self.lbl)
        
        self._bind_sub_tips(sub, {0:"Tính toán thuế & Lương", 1:"Văn bản pháp luật & Biểu mẫu 2026", 2:"Hướng dẫn sử dụng", 3:"Trợ lý AI (Offline)"})

    def _build_settings_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self.lbl.get("tab_settings", "Cài đặt"))
        canvas = tk.Canvas(tab); sb = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set); canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        inner = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        tab.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        tab.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))

        def section(title): return ttk.LabelFrame(inner, text=title)

        # ── Company info ──────────────────────────────────────
        co = section("🏢 Thông tin Doanh nghiệp (Company Info)")
        co.pack(fill="x", padx=10, pady=6)

        co_fields = [
            ("Tên công ty (Company Name)", "company_name", 48),
            ("Địa chỉ DN (Company Address)", "company_address", 60),
            ("Mã số thuế (Tax Code)", "company_tax_code", 20),
            ("Số điện thoại (Phone)", "company_phone", 20),
            ("Email", "company_email", 30),
            ("Tên ngân hàng (Bank Name)", "bank_name", 36),
            ("Số tài khoản (Bank Account)", "bank_account", 24),
            ("Người đại diện (Legal Rep)", "company_legal_rep", 30),
            ("Chức danh (Title)", "company_legal_rep_title", 24),
        ]
        self._setting_entries = {}
        for row_i, (lbl_txt, key, width) in enumerate(co_fields):
            tk.Label(co, text=lbl_txt+":", anchor="e", width=30, wraplength=250, justify="right").grid(row=row_i, column=0, padx=6, pady=3, sticky="e")
            e = tk.Entry(co, width=width)
            e.insert(0, self.settings.get(key,""))
            e.grid(row=row_i, column=1, padx=6, pady=3, sticky="w")
            self._setting_entries[key] = e

        # ── Financial settings ────────────────────────────────
        fin = section("💰 Tài chính & Thuế (Finance & Tax)")
        fin.pack(fill="x", padx=10, pady=6)
        fin_fields = [
            ("Đơn vị tiền tệ (Currency)", "currency", 8),
            ("Số chữ số lẻ", "currency_decimals", 4),
            ("Thuế GTGT % (VAT Rate)", "vat_rate", 6),
            ("Thuế TNDN % (CIT Rate)", "cit_rate", 6),
            ("Số hóa đơn đầu (Start Invoice No)", "invoice_start", 8),
        ]
        for row_i, (lbl_txt, key, width) in enumerate(fin_fields):
            tk.Label(fin, text=lbl_txt+":", anchor="e", width=32).grid(row=row_i, column=0, padx=6, pady=3, sticky="e")
            e = tk.Entry(fin, width=width)
            val = self.settings.get(key,"")
            if key == "vat_rate": val = str(int(float(val or 0.08)*100))
            if key == "cit_rate": val = str(int(float(val or 0.20)*100))
            e.insert(0, str(val))
            e.grid(row=row_i, column=1, padx=6, pady=3, sticky="w")
            self._setting_entries[key] = e

        # ── Language ──────────────────────────────────────────
        lng = section("🌐 Ngôn ngữ (Language)")
        lng.pack(fill="x", padx=10, pady=6)
        tk.Label(lng, text="Ngôn ngữ:").grid(row=0, column=0, padx=6, pady=3, sticky="e")
        self.lng_var = tk.StringVar(value=self.settings.get("language","vi"))
        for val, lbl_t in [("vi","Tiếng Việt"),("en","English")]:
            tk.Radiobutton(lng, text=lbl_t, variable=self.lng_var, value=val).grid(
                row=0, column=1 if val=="vi" else 2, padx=6)

        # ── Offline-first / Online opt-in ─────────────────────
        online_sec = section("🌐 Offline-first / Online opt-in")
        online_sec.pack(fill="x", padx=10, pady=6)
        tk.Label(
            online_sec,
            text="Mặc định phần mềm chạy offline. Chỉ bật từng tính năng online khi người dùng chủ động chọn.",
            fg="#555",
            wraplength=860,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, padx=8, pady=(8, 4), sticky="w")
        self.update_check_enabled_var = tk.BooleanVar(value=bool(self.settings.get("update_check_enabled", False)))
        self.online_market_data_enabled_var = tk.BooleanVar(value=bool(self.settings.get("online_market_data_enabled", False)))
        self.online_ocr_enabled_var = tk.BooleanVar(value=bool(self.settings.get("online_ocr_enabled", False)))
        self.online_embeddings_enabled_var = tk.BooleanVar(value=bool(self.settings.get("online_embeddings_enabled", False)))
        self.online_document_fetch_enabled_var = tk.BooleanVar(value=bool(self.settings.get("online_document_fetch_enabled", False)))
        self.online_qr_enabled_var = tk.BooleanVar(value=bool(self.settings.get("online_qr_enabled", False)))
        online_opts = [
            ("Kiểm tra cập nhật phần mềm khi mở app", self.update_check_enabled_var),
            ("Tải tỷ giá thị trường online trong Phân tích", self.online_market_data_enabled_var),
            ("Cho phép OCR chứng từ qua OCR.Space", self.online_ocr_enabled_var),
            ("Cho phép tạo chỉ mục AI qua Jina", self.online_embeddings_enabled_var),
            ("Cho phép cập nhật văn bản pháp luật/biểu mẫu từ nguồn online", self.online_document_fetch_enabled_var),
            ("Tải ảnh VietQR online khi xuất hóa đơn", self.online_qr_enabled_var),
        ]
        for idx, (text, var) in enumerate(online_opts, start=1):
            tk.Checkbutton(online_sec, text=text, variable=var).grid(row=idx, column=0, padx=8, pady=2, sticky="w")

        # ── Cloud Sync (Supabase) ──────────────────────────────
        cloud_title = self.lbl.get("settings_cloud_title", "ĐỒNG BỘ ĐÁM MÂY (SUPABASE)")
        cloud_sec = section(cloud_title)
        cloud_sec.pack(fill="x", padx=10, pady=6)
        
        # Checkbox to enable
        self.cloud_sync_enabled_var = tk.BooleanVar(value=str(self.settings.get("cloud_sync_enabled", False)).lower() == 'true')
        cb_sync = tk.Checkbutton(cloud_sec, text=self.lbl.get("settings_cloud_enable", "Bật đồng bộ đám mây:"), variable=self.cloud_sync_enabled_var)
        cb_sync.grid(row=0, column=0, columnspan=2, padx=6, pady=3, sticky="w")
        
        # Supabase URL and Key
        tk.Label(cloud_sec, text=self.lbl.get("settings_supabase_url", "Supabase URL:")).grid(row=1, column=0, padx=6, pady=3, sticky="e")
        self.e_supabase_url = tk.Entry(cloud_sec, width=60)
        self.e_supabase_url.insert(0, self.settings.get("supabase_url", ""))
        self.e_supabase_url.grid(row=1, column=1, padx=6, pady=3, sticky="w")
        
        tk.Label(cloud_sec, text=self.lbl.get("settings_supabase_key", "Supabase Key:")).grid(row=2, column=0, padx=6, pady=3, sticky="e")
        self.e_supabase_key = tk.Entry(cloud_sec, width=60, show="*")
        raw_sub_key = decrypt_value(self.settings.get("supabase_key", ""))
        self.e_supabase_key.insert(0, raw_sub_key)
        self.e_supabase_key.grid(row=2, column=1, padx=6, pady=3, sticky="w")
        
        # ── AI Keys ───────────────────────────────────────────
        ai_title = self.lbl.get("settings_ai_title", "TÀI KHOẢN TRỢ LÝ AI (CLOUD FALLBACK)")
        ai_sec = section(ai_title)
        ai_sec.pack(fill="x", padx=10, pady=6)
        self.ai_online_enabled_var = tk.BooleanVar(value=bool(self.settings.get("ai_online_enabled", False)))
        tk.Checkbutton(ai_sec, text="Bật AI online/API (mặc định tắt)", variable=self.ai_online_enabled_var).grid(row=0, column=0, columnspan=2, padx=6, pady=3, sticky="w")
        
        tk.Label(ai_sec, text=self.lbl.get("settings_gemini_key", "Gemini API Key:")).grid(row=1, column=0, padx=6, pady=3, sticky="e")
        self.e_gemini_key = tk.Entry(ai_sec, width=60, show="*")
        raw_gemini_key = decrypt_value(self.settings.get("gemini_key", ""))
        self.e_gemini_key.insert(0, raw_gemini_key)
        self.e_gemini_key.grid(row=1, column=1, padx=6, pady=3, sticky="w")
        
        tk.Label(ai_sec, text=self.lbl.get("settings_claude_key", "Claude API Key:")).grid(row=2, column=0, padx=6, pady=3, sticky="e")
        self.e_claude_key = tk.Entry(ai_sec, width=60, show="*")
        raw_claude_key = decrypt_value(self.settings.get("claude_key", ""))
        self.e_claude_key.insert(0, raw_claude_key)
        self.e_claude_key.grid(row=2, column=1, padx=6, pady=3, sticky="w")
        
        # Toggle keys visibility button
        def _toggle_keys_visibility():
            show_val = "" if self.e_supabase_key.cget("show") == "*" else "*"
            self.e_supabase_key.config(show=show_val)
            self.e_gemini_key.config(show=show_val)
            self.e_claude_key.config(show=show_val)
            btn_toggle.config(text="🙈 Ẩn Key" if show_val == "" else "👁️ " + self.lbl.get("settings_show_keys", "Hiển thị Key"))
            
        btn_toggle = tk.Button(ai_sec, text="👁️ " + self.lbl.get("settings_show_keys", "Hiển thị Key"), command=_toggle_keys_visibility, bg="#757575", fg="white", font=("Segoe UI", 9))
        btn_toggle.grid(row=3, column=1, padx=6, pady=3, sticky="w")
        
        # Test connection button
        def _test_cloud_connection():
            url = self.e_supabase_url.get().strip()
            key = self.e_supabase_key.get().strip()
            if not url or not key:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập Supabase URL và Key trước khi kiểm tra.")
                return
            from sync.cloud_connector import test_connection
            btn_test.config(state="disabled", text="Đang kết nối...")
            self.update()
            try:
                success = test_connection(url, key)
                if success:
                    messagebox.showinfo("Thành công", "Kết nối tới Supabase hoạt động tốt!")
                else:
                    messagebox.showerror("Thất bại", "Không thể kết nối. Kiểm tra URL, Key hoặc kết nối mạng.")
            except ConnectionError:
                messagebox.showwarning("Cảnh báo", "Đã kết nối với Supabase, nhưng các bảng dữ liệu chưa được khởi tạo.\nHãy chạy SQL Schema trong Supabase SQL Editor.")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi: {e}")
            finally:
                btn_test.config(state="normal", text="🔄 " + self.lbl.get("settings_test_conn", "Kiểm tra kết nối"))
                
        btn_test = tk.Button(cloud_sec, text="🔄 " + self.lbl.get("settings_test_conn", "Kiểm tra kết nối"), command=_test_cloud_connection, bg="#1565C0", fg="white", font=("Segoe UI", 9))
        btn_test.grid(row=3, column=1, padx=6, pady=3, sticky="w")

        # ── Save & Updates ────────────────────────────────────
        bf = ttk.Frame(inner); bf.pack(fill="x", padx=10, pady=10)
        tk.Button(bf, text="💾 Lưu cài đặt (Save Settings)", command=self._save_settings,
                  bg="#388E3C", fg="white", font=("Arial",11,"bold"), width=30).pack(side="left", padx=6)
        
        def _install_deps():
            messagebox.showinfo("Offline-only", "Chế độ offline-only: phần mềm không tự tải thư viện qua mạng. Hãy cài requirements.txt thủ công khi chạy bản source.")
            
        tk.Button(bf, text="🔌 Kiểm tra thư viện (offline)", command=_install_deps,
                  bg="#1565C0", fg="white", font=("Arial", 10), width=32).pack(side="left", padx=6)
                  
        tk.Label(bf, text="💡 Cài đặt sẽ tự áp dụng cho các tab mới.", fg="#555", font=("Arial",9)).pack(side="left", padx=10)

        # ── MST lookup hint ───────────────────────────────────
        hint = section("🔍 Tra cứu Mã số thuế DN (MST Lookup Guide)")
        hint.pack(fill="x", padx=10, pady=6)
        tk.Label(hint, text=(
            "Chế độ offline-only: phần mềm không mở website tra cứu MST tự động."
        ), justify="left", pady=4).pack(anchor="w", padx=8)
        tk.Label(hint, text=(
            "Hướng dẫn: Người dùng tự đối chiếu nguồn chính thức bên ngoài phần mềm, sau đó dán MST vào danh mục khách hàng/NCC.\n"
            "Mọi ô nhập liệu trong phần này giữ nguyên khả năng copy-paste."
        ), justify="left", fg="#555555", wraplength=700).pack(anchor="w", padx=8, pady=4)

        # ── Backup & Security ─────────────────────────────────
        bk = section("🛡️ Bảo mật & Sao lưu (Security & Backup)")
        bk.pack(fill="x", padx=10, pady=6)
        
        # --- Local Backup Configuration ---
        cb = ttk.Frame(bk)
        cb.pack(fill="x", padx=10, pady=10)
        
        tk.Label(cb, text="Phương thức sao lưu:").grid(row=0, column=0, sticky="w")
        self.backup_method_var = tk.StringVar(value=self.settings.get("backup_method", "none"))
        cmb_bm = ttk.Combobox(cb, textvariable=self.backup_method_var, values=["none"], state="readonly", width=15)
        cmb_bm.grid(row=0, column=1, padx=5, sticky="w")
        tk.Label(cb, text="Sao lưu luôn tạo bản local. Đồng bộ online chỉ chạy nếu bật mục Supabase ở trên.", fg="#555").grid(row=1, column=0, columnspan=3, sticky="w", pady=4)

        def _do_backup():
            path = utils.create_backup()
            res_cloud = sync.upload_to_cloud(path, self.settings)
            messagebox.showinfo("Thành công", f"Đã tạo bản sao lưu dữ liệu toàn bộ!\nLưu tại: {path}\nTrạng thái: {res_cloud}")
            utils.log_activity(f"Sao lưu dữ liệu: {os.path.basename(path)} | {res_cloud}")
            
        tk.Button(bk, text="TẠO BẢN SAO LƯU CỤC BỘ", command=_do_backup, bg="#00796B", fg="white", font=("Segoe UI", 9, "bold"), padx=20).pack(side="right", padx=10)

        # ── Demo Mode ─────────────────────────────────────────
        demo_box = section("🧪 Chế độ Demo")
        demo_box.pack(fill="x", padx=10, pady=6)
        tk.Label(demo_box, text="Nạp dữ liệu mẫu doanh nghiệp vật tư nông nghiệp để kiểm thử phần mềm như một doanh nghiệp đang hoạt động. Log demo xoay vòng tối đa 02 file, 50KB/file.").pack(side="left", padx=10, pady=12)
        tk.Button(demo_box, text="NẠP DEMO VẬT TƯ NÔNG NGHIỆP", command=self._load_demo_mode, bg="#6A1B9A", fg="white", font=("Segoe UI", 9, "bold"), padx=15).pack(side="right", padx=10)

        # ── Author & Donate ───────────────────────────────────
        donate = section("❤️ Ủng hộ Tác giả (Donate & Credit)")
        donate.pack(fill="x", padx=10, pady=6)
        d_left = tk.Frame(donate)
        d_left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(d_left, text="Phần mềm Kế toán SME Việt Nam - Mã nguồn mở 100% miễn phí.", font=("Segoe UI", 10, "bold"), fg="#1565C0").pack(anchor="w", pady=(0, 5))
        lbl_author = tk.Label(d_left, text="Tác giả: Du Quốc Hoàng Kim\nGitHub: https://github.com/JurisSyntax", justify="left")
        lbl_author.pack(anchor="w")
        lbl_donate = tk.Label(d_left, text="Ủng hộ tác giả qua Vietcombank:\nSTK: 0631000472374\nChi nhánh: Tân Long An", justify="left", font=("Segoe UI", 10, "bold"), fg="#2E7D32")
        lbl_donate.pack(anchor="w", pady=(10, 0))
        
        tabs_extra._add_copy_menu(lbl_author)
        tabs_extra._add_copy_menu(lbl_donate)

        # Load QR Image
        try:
            from PIL import Image, ImageTk
            img_path = utils.get_resource_path("data/Vietcombank.jpg")
            if os.path.exists(img_path):
                img = Image.open(img_path)
                img.thumbnail((160, 160), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                lbl_qr = tk.Label(donate, image=photo)
                lbl_qr.image = photo # keep reference
                lbl_qr.pack(side="right", padx=20, pady=10)
        except ImportError:
            tk.Label(donate, text="(Cài đặt thư viện Pillow để xem mã QR)", fg="#555").pack(side="right", padx=20)
        except Exception as e:
            pass

        # ── Danger Zone ───────────────────────────────────────
        dz = ttk.LabelFrame(inner, text="🚨 Khu vực nguy hiểm (Danger Zone)")
        dz.pack(fill="x", padx=10, pady=20)
        tk.Label(dz, text="Xóa toàn bộ dữ liệu (Ledger, Invoices, Employees) và thiết lập lại ứng dụng từ đầu.", fg="#D32F2F").pack(side="left", padx=10, pady=15)
        tk.Button(dz, text="RESET TOÀN BỘ DỮ LIỆU", command=self._factory_reset, bg="#D32F2F", fg="white", font=("Segoe UI", 9, "bold"), padx=15).pack(side="right", padx=10)

    def _load_demo_mode(self):
        if getattr(self, 'demo_active', False):
            return messagebox.showinfo("Demo", "Bạn đang ở chế độ Demo rồi!")
        if not messagebox.askyesno("Vào chế độ Sandbox Demo", "Chuyển sang chế độ DEMO an toàn?\n\nDữ liệu thật của bạn sẽ được bảo vệ tuyệt đối. Hệ thống sẽ tạo một cơ sở dữ liệu ảo để bạn thử nghiệm."):
            return
        try:
            # Sandbox activation
            if hasattr(self, 'db') and self.db: self.db.close()
            demo_db_path = "data/demo_ledger.db"
            if os.path.exists(demo_db_path): os.remove(demo_db_path)
            self.db = db.init_db(demo_db_path)
            self.demo_active = True
            
            # Seed Demo Employees
            demo_emp_path = "data/employees_demo.json"
            demo_ts_path = "data/timesheets_demo.json"
            if os.path.exists(demo_emp_path): os.remove(demo_emp_path)
            if os.path.exists(demo_ts_path): os.remove(demo_ts_path)
            
            demo_employees = [
                {"code": "NV001", "name": "Nguyễn Văn Hùng", "role": "Giám đốc", "salary": "25000000", "allowance": "3000000", "dependents": "1"},
                {"code": "NV002", "name": "Trần Thị Mai", "role": "Kế toán trưởng", "salary": "18000000", "allowance": "2000000", "dependents": "0"},
                {"code": "NV003", "name": "Lê Hoàng Nam", "role": "Trưởng phòng Kinh doanh", "salary": "15000000", "allowance": "1500000", "dependents": "2"},
                {"code": "NV004", "name": "Phạm Minh Đức", "role": "Nhân viên bán hàng", "salary": "8000000", "allowance": "1000000", "dependents": "0"}
            ]
            with open(demo_emp_path, "w", encoding="utf-8") as f:
                json.dump(demo_employees, f, ensure_ascii=False, indent=2)
                
            # Seed Demo Timesheets (for current month)
            current_month = datetime.date.today().strftime("%m/%Y")
            demo_timesheets = [
                {"month": current_month, "code": "NV001", "work_days": "22", "standard_hours": "208", "ot_hours": "0", "ot_approved": True, "ot_reason": "", "advance": "0"},
                {"month": current_month, "code": "NV002", "work_days": "22", "standard_hours": "208", "ot_hours": "5", "ot_approved": True, "ot_reason": "Chốt sổ cuối tháng", "advance": "1000000"},
                {"month": current_month, "code": "NV003", "work_days": "20", "standard_hours": "208", "ot_hours": "10", "ot_approved": True, "ot_reason": "Hỗ trợ bán hàng", "advance": "0"},
                {"month": current_month, "code": "NV004", "work_days": "22", "standard_hours": "208", "ot_hours": "15", "ot_approved": False, "ot_reason": "Cần kiểm tra phê duyệt", "advance": "500000"}
            ]
            with open(demo_ts_path, "w", encoding="utf-8") as f:
                json.dump(demo_timesheets, f, ensure_ascii=False, indent=2)

            result = seed_agri_demo(self.db, DemoLogRotator("logs"))
            # Backup original settings
            self._real_settings = self.settings.copy()
            self.settings.update({
                "company_name": "Công ty TNHH Vật tư Nông nghiệp Mẫu Xanh [DEMO]",
                "company_address": "Ấp Mẫu, xã Long An, tỉnh Long An",
                "company_tax_code": "1100000000",
                "company_legal_rep": "Nguyễn Văn A",
            })
            
            self._show_demo_exit_button()
            self._refresh_all()
            self._refresh_co_label()
            messagebox.showinfo("Demo", f"Đã vào chế độ Demo. Nhấn 'THOÁT DEMO' màu đỏ ở trên để trở về dữ liệu thật.")
        except Exception as ex:
            messagebox.showerror("Lỗi demo", str(ex))

    def _exit_demo_mode(self):
        if not messagebox.askyesno("Thoát Demo", "Trở về dữ liệu thật của bạn?"): return
        try:
            self.db.close()
            if os.path.exists("data/demo_ledger.db"): os.remove("data/demo_ledger.db")
            if os.path.exists("data/employees_demo.json"): os.remove("data/employees_demo.json")
            if os.path.exists("data/timesheets_demo.json"): os.remove("data/timesheets_demo.json")
            
            self.db = db.init_db("data/ledger.db")
            self.demo_active = False
            self.settings = self._real_settings
            
            if hasattr(self, 'btn_demo_exit') and self.btn_demo_exit.winfo_exists():
                self.btn_demo_exit.destroy()
                
            self._refresh_all()
            self._refresh_co_label()
            messagebox.showinfo("Thành công", "Đã trở về dữ liệu thật của bạn.")
        except Exception as ex:
            messagebox.showerror("Lỗi", f"Lỗi khi thoát demo: {ex}")
            
    def _show_demo_exit_button(self):
        if hasattr(self, 'btn_demo_exit') and self.btn_demo_exit.winfo_exists(): return
        self.btn_demo_exit = tk.Button(self, text="🔴 ĐANG Ở CHẾ ĐỘ DEMO - BẤM ĐỂ THOÁT", command=self._exit_demo_mode,
                                       bg="#D32F2F", fg="white", font=("Segoe UI", 12, "bold"), relief="raised", borderwidth=4, padx=20, pady=5)
        self.btn_demo_exit.place(relx=0.5, y=30, anchor="n")

    def _save_settings(self):
        for key, entry in self._setting_entries.items():
            val = entry.get().strip()
            if key == "vat_rate":
                try: val = str(float(val)/100)
                except: val = "0.08"
            if key == "cit_rate":
                try: val = str(float(val)/100)
                except: val = "0.20"
            self.settings[key] = val
        self.settings["language"] = self.lng_var.get()
        self.settings["backup_method"] = self.backup_method_var.get()
        self.settings["update_check_enabled"] = self.update_check_enabled_var.get()
        self.settings["online_market_data_enabled"] = self.online_market_data_enabled_var.get()
        self.settings["online_ocr_enabled"] = self.online_ocr_enabled_var.get()
        self.settings["online_embeddings_enabled"] = self.online_embeddings_enabled_var.get()
        self.settings["online_document_fetch_enabled"] = self.online_document_fetch_enabled_var.get()
        self.settings["online_qr_enabled"] = self.online_qr_enabled_var.get()
        self.settings["cloud_sync_enabled"] = self.cloud_sync_enabled_var.get()
        self.settings["ai_online_enabled"] = self.ai_online_enabled_var.get()
        self.settings["supabase_url"] = self.e_supabase_url.get().strip()
        self.settings["supabase_key"] = encrypt_value(self.e_supabase_key.get().strip())
        self.settings["gemini_key"] = encrypt_value(self.e_gemini_key.get().strip())
        self.settings["claude_key"] = encrypt_value(self.e_claude_key.get().strip())
        config.save_settings(self.settings)
        utils.log_activity("Cập nhật cài đặt hệ thống")
        self._refresh_co_label()
        messagebox.showinfo("Đã lưu", "Cài đặt đã được lưu thành công!")

    def _factory_reset(self):
        if messagebox.askyesno("XÁC NHẬN LẦN 1", "BẠN CÓ CHẮC CHẮN MUỐN XÓA TOÀN BỘ DỮ LIỆU?\nThao tác này sẽ xóa sạch sổ cái, danh mục và hóa đơn!"):
            if messagebox.askyesno("XÁC NHẬN CUỐI CÙNG", "Dữ liệu sau khi xóa KHÔNG THỂ khôi phục. Bạn vẫn muốn tiếp tục?"):
                # Close DB connection first
                if hasattr(self, 'db') and self.db:
                    try:
                        self.db.close()
                    except: pass
                
                reset_to_original()
                self.settings = config.load_settings()
                self.lbl = config.get_labels(self.settings)
                self.db = db.init_db("data/ledger.db")
                self._refresh_all()
                self._refresh_co_label()
                messagebox.showinfo("Hoàn tất", "Đã reset dữ liệu gốc. Có thể tiếp tục sử dụng mà không cần mở lại phần mềm.")


    def _apply_language_restart(self):
        self._save_settings()
        self.destroy()
        import subprocess, sys
        subprocess.Popen([sys.executable, __file__])

    def _refresh_inv_client_combo(self):
        """Called after client list changes to update invoice combo."""
        df = db.get_clients(self.db)
        if hasattr(self, "cmb_inv_client") and not df.empty:
            self.cmb_inv_client['values'] = df['name'].tolist()
        if hasattr(self, "cmb_inv_hist_client") and not df.empty:
            self.cmb_inv_hist_client['values'] = [""] + df['name'].tolist()


def reset_to_original():
    files = ["data/ledger.db", "data/settings.json", "data/employees.json"]
    for f in files:
        if os.path.exists(f): 
            try: os.remove(f)
            except Exception as e: print(f"Error deleting {f}: {e}")
    # Re-initialize DB
    import db
    conn = db.init_db("data/ledger.db")
    try:
        conn.close()
    except:
        pass


if __name__ == "__main__":
    app = App()
    app.mainloop()
