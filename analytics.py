import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import db, tax_engine, market_data
import os, subprocess, tkinter as tk
from tkinter import ttk

def run_dashboard(conn):
    df = db.get_flat_df(conn)
    if df.empty:
        raise ValueError("Không có dữ liệu. Nhập chứng từ trước!\n(No data — post transactions first!)")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    tax = tax_engine.load_tax()

    rev_df = df[df['account'].astype(str).str.startswith('511') & (df['credit'] > 0)]
    revenue = rev_df['credit'].sum() if not rev_df.empty else 0
    exp_df = df[df['account'].astype(str).str.startswith('64') & (df['debit'] > 0)]
    expense = exp_df['debit'].sum() if not exp_df.empty else 0

    vat = revenue * tax.get("VAT", 0.08)
    profit = max(0, revenue - expense)
    cit = profit * tax.get("CIT", 0.20)

    # Cash flow
    cash_df = df[df['account'].astype(str).str.startswith('11')].copy()
    if not cash_df.empty:
        cash_df['net'] = cash_df['debit'] - cash_df['credit']
        cf = cash_df.groupby('date')['net'].sum().cumsum().reset_index()
        cf.columns = ['date', 'balance']
    else:
        cf = pd.DataFrame({'date': [pd.Timestamp.now()], 'balance': [0]})

    exp_by_type = exp_df.groupby('type')['debit'].sum().reset_index() if not exp_df.empty else pd.DataFrame({'type': ['N/A'], 'debit': [0]})

    # Fetch market data
    rates = market_data.get_exchange_rates()
    cpi_data = market_data.get_cpi_data()

    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            "📈 Dòng tiền (Cash Flow)", "🧾 Thuế dự kiến (Tax Liability)",
            "💸 Chi phí (Expenses)", "📊 Tổng hợp (Summary)",
            "💱 Tỷ giá (Exchange Rates)", "📉 CPI Việt Nam (%)"
        )
    )

    fig.add_trace(go.Scatter(x=cf['date'], y=cf['balance'], mode="lines+markers",
                             name="Số dư", fill='tozeroy', line=dict(color='#1976D2', width=2)),
                  row=1, col=1)
    fig.add_trace(go.Bar(x=["VAT","CIT"], y=[vat,cit], name="Thuế",
                         marker_color=['#FF7043','#FFA726']),
                  row=1, col=2)
    fig.add_trace(go.Pie(labels=exp_by_type['type'], values=exp_by_type['debit'], name="Chi phí"),
                  row=2, col=1)
    fig.add_trace(go.Bar(x=["Doanh thu","Chi phí","Lợi nhuận"], y=[revenue,expense,profit],
                         marker_color=['#43A047','#E53935','#1E88E5'], name="Tổng hợp"),
                  row=2, col=2)

    # Exchange rates panel
    rate_keys = [k for k in rates if not k.startswith("_")]
    fig.add_trace(go.Bar(x=rate_keys, y=[rates[k] for k in rate_keys],
                         name=f"1 USD = ? ({rates.get('_source','')})",
                         marker_color='#7E57C2'),
                  row=3, col=1)

    # CPI panel
    cpi_entries = cpi_data.get("data", [])
    if cpi_entries:
        fig.add_trace(go.Bar(x=[e["year"] for e in cpi_entries],
                             y=[e["cpi_pct"] for e in cpi_entries],
                             name=f"CPI% ({cpi_data.get('_source','')})",
                             marker_color='#26A69A'),
                      row=3, col=2)

    fig.update_layout(
        height=900, title_text="📊 VN SME Analytics Dashboard (TT133 + Thị trường)",
        title_font_size=18, template="plotly_white", showlegend=False
    )

    os.makedirs("data", exist_ok=True)
    out_path = os.path.abspath("data/dashboard.html")
    fig.write_html(out_path, auto_open=False)

    # Open in Edge first, fallback to default
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    opened = False
    for edge in edge_paths:
        if os.path.exists(edge):
            subprocess.Popen([edge, out_path])
            opened = True
            break
    if not opened:
        import webbrowser
        webbrowser.open(f"file:///{out_path.replace(os.sep, '/')}")

    return out_path


def build_analytics_tab(app, tab, conn, settings, lbl):
    """Build the in-app Analytics tab widget (called from main.py)."""
    lang = settings.get("language", "vi")

    # Summary cards frame
    cards = ttk.LabelFrame(tab, text="📊 Tóm tắt tài chính / Financial Summary")
    cards.pack(fill="x", padx=10, pady=8)

    def _refresh_summary():
        for w in cards.winfo_children(): w.destroy()
        df = db.get_flat_df(conn)
        if df.empty:
            tk.Label(cards, text="(Chưa có dữ liệu — nhập chứng từ trước)",
                     fg="#888", font=("Arial", 10)).pack(pady=10)
            return
        tax = tax_engine.load_tax()
        rev = df[df['account'].astype(str).str.startswith('511') & (df['credit'] > 0)]['credit'].sum()
        exp = df[df['account'].astype(str).str.startswith('64')  & (df['debit']  > 0)]['debit'].sum()
        profit = rev - exp
        vat_est = rev * tax.get("VAT", 0.08)
        cit_est = max(0, profit) * tax.get("CIT", 0.20)

        metrics = [
            ("💰 Doanh thu", f"{rev:,.0f}", "#2E7D32"),
            ("💸 Chi phí",   f"{exp:,.0f}", "#C62828"),
            ("📈 Lợi nhuận", f"{profit:,.0f}", "#1565C0"),
            ("🧾 VAT ước",   f"{vat_est:,.0f}", "#E65100"),
            ("🏛 CIT ước",   f"{cit_est:,.0f}", "#4A148C"),
        ]
        for col, (title, value, color) in enumerate(metrics):
            f = tk.Frame(cards, bg="#FFFFFF", padx=10, pady=10, highlightbackground="#EEE", highlightthickness=1)
            f.grid(row=0, column=col, padx=8, pady=10, sticky="nsew")
            cards.columnconfigure(col, weight=1)
            tk.Label(f, text=title, font=("Segoe UI", 10), fg="#666", bg="#FFFFFF").pack()
            tk.Label(f, text=value, font=("Segoe UI", 14, "bold"), fg=color, bg="#FFFFFF").pack(pady=4)
            tk.Label(f, text="VND", font=("Segoe UI", 8), fg="#AAA", bg="#FFFFFF").pack()

        # --- Business Summary Tree (The "Study-Tree") ---
        tree_frame = ttk.LabelFrame(tab, text="🌳 Cây cơ cấu kinh doanh (Business Structure Tree)")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=4)
        
        tree = ttk.Treeview(tree_frame, columns=("value", "pct"), show="tree headings", height=8)
        tree.heading("#0", text="Hạng mục (Category)", anchor="w")
        tree.heading("value", text="Giá trị (VND)", anchor="e")
        tree.heading("pct", text="Tỷ trọng (%)", anchor="center")
        tree.column("#0", width=300)
        tree.column("value", width=150, anchor="e")
        tree.column("pct", width=100, anchor="center")
        tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Populate Tree
        rev_id = tree.insert("", "end", text="💰 TỔNG DOANH THU", open=True, values=(f"{rev:,.0f}", "100%"))
        # Breakdown revenue by note
        rev_entries = df[df['account'].astype(str).str.startswith('511') & (df['credit'] > 0)]
        if not rev_entries.empty:
            sources = rev_entries.groupby('note')['credit'].sum().to_dict()
            for src, val in sources.items():
                p = (val/rev*100) if rev > 0 else 0
                tree.insert(rev_id, "end", text=f"└ {src}", values=(f"{val:,.0f}", f"{p:.1f}%"))

        exp_id = tree.insert("", "end", text="💸 TỔNG CHI PHÍ", open=True, values=(f"{exp:,.0f}", "100%"))
        # Breakdown expense by type (6421, 6422, etc. or just by note if type is note)
        exp_entries = df[df['account'].astype(str).str.startswith('64') & (df['debit'] > 0)]
        if not exp_entries.empty:
            e_sources = exp_entries.groupby('note')['debit'].sum().to_dict()
            for src, val in e_sources.items():
                p = (val/exp*100) if exp > 0 else 0
                tree.insert(exp_id, "end", text=f"└ {src}", values=(f"{val:,.0f}", f"{p:.1f}%"))

        # --- Matplotlib Integrated Charts (Visual Excellence) ---
        chart_frame = ttk.LabelFrame(tab, text="📊 Phân tích Trực quan (Visual Analytics)")
        chart_frame.pack(fill="both", expand=True, padx=10, pady=4)
        
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import matplotlib.pyplot as plt
            
            # Create a figure with a 2x2 layout
            fig = Figure(figsize=(12, 8), dpi=100, facecolor='#FFFFFF')
            
            # 1. Pie Chart: Revenue Structure (Top Left)
            ax1 = fig.add_subplot(221)
            if not rev_entries.empty:
                sources = rev_entries.groupby('note')['credit'].sum()
                ax1.pie(sources, labels=sources.index, autopct='%1.1f%%', startangle=140, 
                        colors=['#43A047', '#1E88E5', '#FFB300', '#E53935'], wedgeprops={'edgecolor': 'white'})
                ax1.set_title("Cơ cấu Doanh thu", fontsize=10, fontweight='bold', color='#1565C0')
            else:
                ax1.text(0.5, 0.5, "Chưa có dữ liệu Doanh thu", ha='center', va='center')
                ax1.axis('off')

            # 2. Bar Chart: Monthly Trends (Top Right)
            ax2 = fig.add_subplot(222)
            sum_df = db.get_revenue_summary(conn, period="month").sort_values("period").tail(6)
            if not sum_df.empty:
                x = range(len(sum_df))
                ax2.bar(x, sum_df['revenue'], width=0.4, label='Doanh thu', color='#43A047', align='center')
                ax2.bar([i + 0.4 for i in x], sum_df['expense'], width=0.4, label='Chi phí', color='#E53935', align='center')
                ax2.set_xticks([i + 0.2 for i in x])
                ax2.set_xticklabels(sum_df['period'], fontsize=8)
                ax2.legend(fontsize=8)
                ax2.set_title("Xu hướng Tháng", fontsize=10, fontweight='bold', color='#1565C0')
                ax2.spines['top'].set_visible(False)
                ax2.spines['right'].set_visible(False)
            else:
                ax2.text(0.5, 0.5, "Chưa có dữ liệu xu hướng", ha='center', va='center')
                ax2.axis('off')

            # 3. Cash Flow Forecast (Bottom Left/Span)
            ax3 = fig.add_subplot(212) # Span across the bottom
            cf_data = db.get_account_history_df(conn, "11") # Cash & Bank
            if not cf_data.empty:
                cf_data['date'] = pd.to_datetime(cf_data['date'])
                daily = cf_data.groupby('date')['running_balance'].last().reset_index()
                ax3.plot(daily['date'], daily['running_balance'], label='Thực tế', color='#1565C0', linewidth=2)
                
                if len(daily) > 2:
                    try:
                        from scipy import stats
                        import numpy as np
                        x_num = np.arange(len(daily))
                        slope, intercept, r_value, p_value, std_err = stats.linregress(x_num, daily['running_balance'])
                        last_date = daily['date'].max()
                        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 16)]
                        future_x = np.arange(len(daily), len(daily) + 15)
                        forecast_vals = slope * future_x + intercept
                        ax3.plot(future_dates, forecast_vals, label='Dự báo (15 ngày)', color='#FF9800', linestyle='--')
                    except: pass
                
                ax3.set_title("Dự báo Dòng tiền (Cash Flow Forecast)", fontsize=10, fontweight='bold', color='#1565C0')
                ax3.legend(fontsize=7)
                ax3.tick_params(axis='x', rotation=30, labelsize=7)
                ax3.grid(True, linestyle=':', alpha=0.6)
            else:
                ax3.text(0.5, 0.5, "Chưa có dữ liệu dòng tiền", ha='center', va='center')
                ax3.axis('off')

            fig.tight_layout()
            canvas_mtl = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas_mtl.draw()
            canvas_mtl.get_tk_widget().pack(fill="both", expand=True, pady=5)
            
        except Exception as e:
            tk.Label(chart_frame, text=f"Cần cài đặt Matplotlib để xem biểu đồ: {e}", fg="#666").pack(pady=20)

    _refresh_summary()

    _refresh_summary()

    # Market data frame with rounded look
    mkt = ttk.LabelFrame(tab, text="🌐 Dữ liệu thị trường (Global Market Data)")
    mkt.pack(fill="x", padx=15, pady=10)
    mkt_txt = tk.Text(mkt, height=4, font=("Consolas", 10), state="disabled", wrap="word", bg="#F8F9FA", relief="flat", padx=10, pady=10)
    mkt_txt.pack(fill="x", padx=5, pady=5)


    def _load_market():
        mkt_txt.config(state="normal"); mkt_txt.delete("1.0", "end")
        mkt_txt.insert("end", "⏳ Đang tải dữ liệu thị trường...\n")
        mkt_txt.config(state="disabled"); tab.update_idletasks()
        try:
            rates = market_data.get_exchange_rates()
            cpi   = market_data.get_cpi_data()
            lines = [f"📅 Tỷ giá ngày {rates.get('_date','N/A')} (Nguồn: {rates.get('_source','')})"]
            for k in ["VND","EUR","JPY","CNY","SGD"]:
                if k in rates: lines.append(f"   1 USD = {rates[k]:>12,.2f} {k}")
            lines.append("")
            lines.append(f"📉 CPI Việt Nam (Nguồn: {cpi.get('_source','')}):")
            for e in cpi.get("data", [])[:3]:
                lines.append(f"   {e['year']}: {e['cpi_pct']}%")
            mkt_txt.config(state="normal"); mkt_txt.delete("1.0","end")
            mkt_txt.insert("end", "\n".join(lines)); mkt_txt.config(state="disabled")
        except Exception as ex:
            mkt_txt.config(state="normal"); mkt_txt.delete("1.0","end")
            mkt_txt.insert("end", f"❌ Lỗi kết nối: {ex}"); mkt_txt.config(state="disabled")

    # Button row
    btn_row = ttk.Frame(tab); btn_row.pack(fill="x", padx=10, pady=6)
    tk.Button(btn_row, text="🔄 Cập nhật tóm tắt", command=_refresh_summary,
              bg="#388E3C", fg="white", width=20).pack(side="left", padx=4)
    tk.Button(btn_row, text="🌍 Tải dữ liệu thị trường", command=_load_market,
              bg="#1565C0", fg="white", width=22).pack(side="left", padx=4)

    status_lbl = tk.Label(tab, text="", fg="#388E3C"); status_lbl.pack(pady=2)
    app._analytics_status_lbl = status_lbl


def _open_html_dashboard(app, conn):
    try:
        if hasattr(app, '_analytics_status_lbl'):
            app._analytics_status_lbl.config(text="⏳ Đang tạo...", fg="#1565C0")
            app.update_idletasks()
        out = run_dashboard(conn)
        if hasattr(app, '_analytics_status_lbl'):
            app._analytics_status_lbl.config(text=f"✅ Dashboard: {out}", fg="#388E3C")
    except Exception as e:
        if hasattr(app, '_analytics_status_lbl'):
            app._analytics_status_lbl.config(text=f"❌ {e}", fg="#C62828")
