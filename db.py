import sqlite3, pandas as pd
import os
from datetime import datetime

TT133_ACCOUNTS = [
    ("111",  "Tiền mặt",                                        "Tài sản"),
    ("112",  "Tiền gửi ngân hàng",                              "Tài sản"),
    ("131",  "Phải thu của khách hàng",                         "Tài sản"),
    ("133",  "Thuế GTGT được khấu trừ",                        "Tài sản"),
    ("152",  "Nguyên liệu, vật liệu",                           "Tài sản"),
    ("156",  "Hàng hóa",                                        "Tài sản"),
    ("211",  "Tài sản cố định hữu hình",                        "Tài sản"),
    ("214",  "Hao mòn tài sản cố định",                         "Tài sản"),
    ("331",  "Phải trả cho người bán",                          "Nguồn vốn"),
    ("333",  "Thuế và các khoản phải nộp NSNN",                 "Nguồn vốn"),
    ("3331", "Thuế GTGT phải nộp",                              "Nguồn vốn"),
    ("334",  "Phải trả người lao động",                         "Nguồn vốn"),
    ("338",  "Phải trả, phải nộp khác",                         "Nguồn vốn"),
    ("411",  "Vốn đầu tư của chủ sở hữu",                       "Nguồn vốn"),
    ("421",  "Lợi nhuận sau thuế chưa phân phối",               "Nguồn vốn"),
    ("511",  "Doanh thu bán hàng và cung cấp dịch vụ",          "Doanh thu"),
    ("632",  "Giá vốn hàng bán",                                "Chi phí"),
    ("642",  "Chi phí quản lý kinh doanh",                      "Chi phí"),
    ("811",  "Chi phí khác",                                    "Chi phí"),
    ("911",  "Xác định kết quả kinh doanh",                     "Khác"),
]

def init_db(path="data/ledger.db"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")

    conn.executescript('''
    CREATE TABLE IF NOT EXISTS accounts (code TEXT PRIMARY KEY, name TEXT, type TEXT);

    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY,
        name TEXT,
        tax_code TEXT,
        contact TEXT,
        address TEXT DEFAULT "",
        currency TEXT DEFAULT "VND",
        currency_decimals INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS journal_entries (
        id INTEGER PRIMARY KEY,
        date TEXT,
        ref TEXT,
        note TEXT,
        type TEXT,
        client_id INTEGER DEFAULT NULL,
        created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS journal_lines (
        id INTEGER PRIMARY KEY,
        entry_id INTEGER,
        account TEXT,
        debit REAL,
        credit REAL,
        FOREIGN KEY(entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY, 
        name TEXT, 
        unit TEXT, 
        base_unit TEXT DEFAULT "",
        conv_factor REAL DEFAULT 1.0,
        qty REAL, 
        cost REAL, 
        price REAL,
        batch_no TEXT DEFAULT "",
        category TEXT DEFAULT "Chung",
        min_qty REAL DEFAULT 0.0
    );
    CREATE TABLE IF NOT EXISTS fixed_assets (
        id INTEGER PRIMARY KEY, name TEXT, value REAL, dep_months INTEGER, start_date TEXT
    );

    CREATE TABLE IF NOT EXISTS inventory_log (
        id INTEGER PRIMARY KEY,
        item_id INTEGER,
        date TEXT,
        type TEXT,
        qty REAL,
        note TEXT,
        created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime')),
        FOREIGN KEY(item_id) REFERENCES inventory(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY,
        inv_number TEXT UNIQUE,
        inv_type TEXT,
        client_id INTEGER,
        date TEXT,
        items_json TEXT,
        subtotal REAL,
        vat REAL,
        total REAL,
        pdf_path TEXT,
        created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime')),
        FOREIGN KEY(client_id) REFERENCES clients(id)
    );
    ''')
    conn.commit()

    # ── Migrations for existing DBs ──
    migrations = [
        "ALTER TABLE journal_entries ADD COLUMN created_at TEXT",
        "ALTER TABLE clients ADD COLUMN currency TEXT DEFAULT 'VND'",
        "ALTER TABLE clients ADD COLUMN currency_decimals INTEGER DEFAULT 0",
        "ALTER TABLE clients ADD COLUMN address TEXT DEFAULT ''",
        "ALTER TABLE journal_entries ADD COLUMN client_id INTEGER DEFAULT NULL",
        "ALTER TABLE inventory ADD COLUMN base_unit TEXT DEFAULT ''",
        "ALTER TABLE inventory ADD COLUMN conv_factor REAL DEFAULT 1.0",
        "ALTER TABLE inventory ADD COLUMN batch_no TEXT DEFAULT ''",
        "ALTER TABLE inventory ADD COLUMN min_qty REAL DEFAULT 0.0",
    ]
    for sql in migrations:
        try: conn.execute(sql); conn.commit()
        except: pass

    # Seed TT133 accounts if empty
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM accounts")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO accounts VALUES (?,?,?)", TT133_ACCOUNTS)
        conn.commit()

    return conn

# ── Accounts ────────────────────────────────────────────────
def add_account(conn, code, name, acc_type):
    conn.execute("INSERT INTO accounts VALUES (?,?,?)", (code, name, acc_type))
    conn.commit()

def update_account(conn, code, name, acc_type, old_code):
    conn.execute("UPDATE accounts SET code=?, name=?, type=? WHERE code=?",
                 (code, name, acc_type, old_code))
    conn.commit()

def get_accounts(conn):
    return pd.read_sql("SELECT * FROM accounts ORDER BY code", conn)

def delete_account(conn, code):
    conn.execute("DELETE FROM accounts WHERE code=?", (code,))
    conn.commit()

# ── Ledger ───────────────────────────────────────────────────
def post_entry(conn, date, ref, note, lines, tx_type="", client_id=None):
    _check_balanced(lines)
    cur = conn.cursor()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT INTO journal_entries(date,ref,note,type,client_id,created_at) VALUES (?,?,?,?,?,?)",
                (date, ref, note, tx_type, client_id, ts))
    eid = cur.lastrowid
    cur.executemany("INSERT INTO journal_lines VALUES (NULL,?,?,?,?)",
                    [(eid, *l) for l in lines])
    conn.commit()
    return eid

def update_entry(conn, entry_id, date, ref, note, lines, tx_type="", client_id=None):
    _check_balanced(lines)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE journal_entries SET date=?, ref=?, note=?, type=?, client_id=?, created_at=? WHERE id=?",
        (date, ref, note, tx_type, client_id, ts, entry_id)
    )
    conn.execute("DELETE FROM journal_lines WHERE entry_id=?", (entry_id,))
    conn.executemany("INSERT INTO journal_lines VALUES (NULL,?,?,?,?)",
                     [(entry_id, *l) for l in lines])
    conn.commit()

def _check_balanced(lines):
    dr = sum(float(l[1]) for l in lines)
    cr = sum(float(l[2]) for l in lines)
    if abs(dr - cr) > 0.01:
        raise ValueError(f"Mất cân đối (Unbalanced): Nợ {dr:,.0f} ≠ Có {cr:,.0f}")

def delete_entry(conn, entry_id):
    conn.execute("DELETE FROM journal_entries WHERE id=?", (entry_id,))
    conn.commit()

def get_flat_df(conn):
    return pd.read_sql('''
        SELECT e.id AS entry_id, e.date, e.created_at, e.ref, e.note, e.type,
               l.account, l.debit, l.credit, e.client_id
        FROM journal_entries e
        JOIN journal_lines l ON e.id = l.entry_id
        ORDER BY e.date DESC, e.created_at DESC, e.id DESC
    ''', conn)

def get_entry_lines(conn, entry_id):
    cur = conn.cursor()
    cur.execute("SELECT account, debit, credit FROM journal_lines WHERE entry_id=?",
                (entry_id,))
    return cur.fetchall()

def get_entry_details(conn, entry_id):
    cur = conn.cursor()
    cur.execute("SELECT date, ref, note, type FROM journal_entries WHERE id=?",
                (entry_id,))
    return cur.fetchone()

def get_account_history_df(conn, account_prefix=None):
    """Running balance view for a specific account prefix (e.g. '111')."""
    sql = '''
        SELECT e.date, e.created_at, e.ref, e.note, e.type,
               l.account, l.debit, l.credit
        FROM journal_entries e
        JOIN journal_lines l ON e.id = l.entry_id
        {where}
        ORDER BY e.date ASC, e.created_at ASC, e.id ASC
    '''
    if account_prefix:
        df = pd.read_sql(
            sql.format(where="WHERE l.account LIKE ?"), conn,
            params=(f"{account_prefix}%",)
        )
    else:
        df = pd.read_sql(sql.format(where=""), conn)

    if not df.empty:
        df["net"] = df["debit"].fillna(0) - df["credit"].fillna(0)
        df["running_balance"] = df["net"].cumsum()
    return df

# ── Clients ──────────────────────────────────────────────────
def add_client(conn, name, tax_code, contact, address="", currency="VND", currency_decimals=0):
    conn.execute("INSERT INTO clients VALUES (NULL,?,?,?,?,?,?)",
                 (name, tax_code, contact, address, currency, currency_decimals))
    conn.commit()

def update_client(conn, client_id, name, tax_code, contact, address="", currency="VND", currency_decimals=0):
    conn.execute(
        "UPDATE clients SET name=?, tax_code=?, contact=?, address=?, currency=?, currency_decimals=? WHERE id=?",
        (name, tax_code, contact, address, currency, currency_decimals, client_id)
    )
    conn.commit()

def get_clients(conn):
    return pd.read_sql("SELECT * FROM clients", conn)

def delete_client(conn, client_id):
    conn.execute("DELETE FROM clients WHERE id=?", (client_id,))
    conn.commit()

def get_client_by_name(conn, name):
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE name=?", (name,))
    row = cur.fetchone()
    if row:
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    return None

# ── Inventory ────────────────────────────────────────────────
def add_inventory(conn, name, unit, base_unit, conv_factor, qty, cost, price, batch_no, category="Chung", min_qty=0.0):
    conn.execute("INSERT INTO inventory VALUES (NULL,?,?,?,?,?,?,?,?,?,?)",
                 (name, unit, base_unit, conv_factor, qty, cost, price, batch_no, category, min_qty))
    conn.commit()

def update_inventory(conn, item_id, name, unit, base_unit, conv_factor, qty, cost, price, batch_no, category="Chung", min_qty=0.0):
    conn.execute(
        "UPDATE inventory SET name=?, unit=?, base_unit=?, conv_factor=?, qty=?, cost=?, price=?, batch_no=?, category=?, min_qty=? WHERE id=?",
        (name, unit, base_unit, conv_factor, qty, cost, price, batch_no, category, min_qty, item_id)
    )
    conn.commit()

def get_inventory(conn):
    return pd.read_sql("SELECT * FROM inventory", conn)

def delete_inventory(conn, item_id):
    conn.execute("DELETE FROM inventory WHERE id=?", (item_id,))
    conn.commit()

# ── Inventory Log (import/export tracking) ───────────────────
def add_inventory_log(conn, item_id, date, log_type, qty, note=""):
    """log_type: 'import' (nhập) or 'export' (xuất)"""
    conn.execute("INSERT INTO inventory_log VALUES (NULL,?,?,?,?,?,datetime('now','localtime'))",
                 (item_id, date, log_type, qty, note))
    # Update inventory qty
    if log_type == "import":
        conn.execute("UPDATE inventory SET qty = qty + ? WHERE id = ?", (qty, item_id))
    elif log_type == "export":
        conn.execute("UPDATE inventory SET qty = qty - ? WHERE id = ?", (qty, item_id))
    conn.commit()

def get_inventory_log(conn, item_id=None):
    if item_id:
        return pd.read_sql("""
            SELECT il.*, i.name as item_name FROM inventory_log il
            JOIN inventory i ON il.item_id = i.id
            WHERE il.item_id = ?
            ORDER BY il.date DESC, il.created_at DESC
        """, conn, params=(item_id,))
    return pd.read_sql("""
        SELECT il.*, i.name as item_name FROM inventory_log il
        JOIN inventory i ON il.item_id = i.id
        ORDER BY il.date DESC, il.created_at DESC
    """, conn)

# ── Fixed Assets ─────────────────────────────────────────────
def add_asset(conn, name, value, dep_months, start_date):
    conn.execute("INSERT INTO fixed_assets VALUES (NULL,?,?,?,?)",
                 (name, value, dep_months, start_date))
    conn.commit()

def update_asset(conn, asset_id, name, value, dep_months, start_date):
    conn.execute(
        "UPDATE fixed_assets SET name=?, value=?, dep_months=?, start_date=? WHERE id=?",
        (name, value, dep_months, start_date, asset_id)
    )
    conn.commit()

def get_assets(conn):
    return pd.read_sql("SELECT * FROM fixed_assets", conn)

def delete_asset(conn, asset_id):
    conn.execute("DELETE FROM fixed_assets WHERE id=?", (asset_id,))
    conn.commit()

# ── Invoices ─────────────────────────────────────────────────
def next_invoice_number(conn, inv_type="01GTGT"):
    """Generate next invoice number: HD-01GTGT-YYYYMM-0001"""
    prefix = f"HD-{inv_type}-{datetime.now().strftime('%Y%m')}"
    cur = conn.cursor()
    cur.execute("SELECT inv_number FROM invoices WHERE inv_number LIKE ? ORDER BY inv_number DESC LIMIT 1",
                (f"{prefix}-%",))
    row = cur.fetchone()
    if row:
        last_seq = int(row[0].split("-")[-1])
        seq = last_seq + 1
    else:
        seq = 1
    return f"{prefix}-{seq:04d}"

def save_invoice(conn, inv_number, inv_type, client_id, date, items_json, subtotal, vat, total, pdf_path):
    conn.execute("""INSERT INTO invoices (inv_number, inv_type, client_id, date, items_json,
                    subtotal, vat, total, pdf_path) VALUES (?,?,?,?,?,?,?,?,?)""",
                 (inv_number, inv_type, client_id, date, items_json, subtotal, vat, total, pdf_path))
    
    # --- Sync Stock ---
    import json
    items = json.loads(items_json)
    for it in items:
        # Try to find item in inventory by name
        cur = conn.cursor()
        cur.execute("SELECT id, qty, conv_factor FROM inventory WHERE name=?", (it['name'],))
        row = cur.fetchone()
        if row:
            iid, current_qty, factor = row
            deduct_qty = float(it['qty']) * float(factor or 1.0)
            new_qty = current_qty - deduct_qty
            conn.execute("UPDATE inventory SET qty=? WHERE id=?", (new_qty, iid))
            # Log stock out
            conn.execute("INSERT INTO inventory_log (item_id, date, type, qty, note) VALUES (?,?,?,?,?)",
                         (iid, date, "export", deduct_qty, f"HĐ {inv_number}"))
    
    conn.commit()

def get_invoices(conn, client_id=None):
    if client_id:
        return pd.read_sql("SELECT * FROM invoices WHERE client_id=? ORDER BY created_at DESC", conn, params=(client_id,))
    return pd.read_sql("SELECT * FROM invoices ORDER BY created_at DESC", conn)

def delete_invoice(conn, inv_number):
    """Delete an invoice and all linked accounting entries."""
    cur = conn.cursor()
    # Find linked entry IDs
    cur.execute("SELECT id FROM journal_entries WHERE ref=?", (inv_number,))
    entry_ids = [r[0] for r in cur.fetchall()]
    for eid in entry_ids:
        cur.execute("DELETE FROM journal_lines WHERE entry_id=?", (eid,))
        cur.execute("DELETE FROM journal_entries WHERE id=?", (eid,))
    # Delete invoice record
    cur.execute("DELETE FROM invoices WHERE inv_number=?", (inv_number,))
    conn.commit()

def get_revenue_summary(conn, period="month"):
    """Get revenue totals by day/month/year."""
    if period == "day":
        group = "e.date"
    elif period == "year":
        group = "substr(e.date, 1, 4)"
    else:
        group = "substr(e.date, 1, 7)"
    sql = f"""
        SELECT {group} as period,
               SUM(CASE WHEN l.credit > 0 AND l.account LIKE '511%' THEN l.credit ELSE 0 END) as revenue,
               SUM(CASE WHEN l.debit > 0 AND l.account LIKE '64%' THEN l.debit ELSE 0 END) as expense
        FROM journal_entries e
        JOIN journal_lines l ON e.id = l.entry_id
        GROUP BY {group}
        ORDER BY {group} DESC
    """
    return pd.read_sql(sql, conn)


# ── Debt Management ──────────────────────────────────────────
def get_debt_summary(conn):
    """
    Calculate balance for accounts 131 (Receivable) and 331 (Payable) per client.
    Returns a DataFrame with columns: client_id, client_name, receivable, payable.
    """
    sql = """
        SELECT 
            c.id AS client_id, 
            c.name AS client_name,
            SUM(CASE WHEN l.account LIKE '131%' THEN l.debit - l.credit ELSE 0 END) AS receivable,
            SUM(CASE WHEN l.account LIKE '331%' THEN l.credit - l.debit ELSE 0 END) AS payable
        FROM clients c
        LEFT JOIN journal_entries e ON c.id = e.client_id
        LEFT JOIN journal_lines l ON e.id = l.entry_id
        GROUP BY c.id
        HAVING receivable <> 0 OR payable <> 0
    """
    return pd.read_sql(sql, conn)

def get_client_debt_details(conn, client_id):
    """
    List all transactions affecting debt for a specific client.
    """
    sql = """
        SELECT e.date, e.ref, e.note, l.account, l.debit, l.credit
        FROM journal_entries e
        JOIN journal_lines l ON e.id = l.entry_id
        WHERE e.client_id = ? AND (l.account LIKE '131%' OR l.account LIKE '331%')
        ORDER BY e.date DESC, e.id DESC
    """
    return pd.read_sql(sql, conn, params=(client_id,))
