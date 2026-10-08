import hashlib
import json
import sqlite3
import os
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation


class _LazyPandas:
    """Keep the database module lightweight until a DataFrame API is used."""

    def __getattr__(self, name):
        import pandas

        globals()["pd"] = pandas
        return getattr(pandas, name)


pd = _LazyPandas()

TT133_ACCOUNTS = [
    ("111",  "Tiền mặt",                                        "Tài sản"),
    ("112",  "Tiền gửi ngân hàng",                              "Tài sản"),
    ("131",  "Phải thu của khách hàng",                         "Tài sản"),
    ("133",  "Thuế GTGT được khấu trừ",                        "Tài sản"),
    ("1331", "Thuế GTGT được khấu trừ của hàng hóa, dịch vụ",  "Tài sản"),
    ("152",  "Nguyên liệu, vật liệu",                           "Tài sản"),
    ("156",  "Hàng hóa",                                        "Tài sản"),
    ("138",  "Phải thu khác",                                   "Tài sản"),
    ("242",  "Chi phí trả trước",                               "Tài sản"),
    ("211",  "Tài sản cố định hữu hình",                        "Tài sản"),
    ("214",  "Hao mòn tài sản cố định",                         "Tài sản"),
    ("331",  "Phải trả cho người bán",                          "Nguồn vốn"),
    ("333",  "Thuế và các khoản phải nộp NSNN",                 "Nguồn vốn"),
    ("3331", "Thuế GTGT phải nộp",                              "Nguồn vốn"),
    ("334",  "Phải trả người lao động",                         "Nguồn vốn"),
    ("338",  "Phải trả, phải nộp khác",                         "Nguồn vốn"),
    ("341",  "Vay và nợ thuê tài chính",                        "Nguồn vốn"),
    ("411",  "Vốn đầu tư của chủ sở hữu",                       "Nguồn vốn"),
    ("421",  "Lợi nhuận sau thuế chưa phân phối",               "Nguồn vốn"),
    ("511",  "Doanh thu bán hàng và cung cấp dịch vụ",          "Doanh thu"),
    ("515",  "Doanh thu hoạt động tài chính",                    "Doanh thu"),
    ("632",  "Giá vốn hàng bán",                                "Chi phí"),
    ("635",  "Chi phí tài chính",                               "Chi phí"),
    ("641",  "Chi phí bán hàng",                                "Chi phí"),
    ("642",  "Chi phí quản lý kinh doanh",                      "Chi phí"),
    ("811",  "Chi phí khác",                                    "Chi phí"),
    ("911",  "Xác định kết quả kinh doanh",                     "Khác"),
]

def init_db(path="data/ledger.db"):
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    conn.executescript('''
    CREATE TABLE IF NOT EXISTS accounts (code TEXT PRIMARY KEY, name TEXT, type TEXT);

    -- Compatibility shell for older local databases and reset checks. New
    -- accounting writes use journal_entries/journal_lines exclusively.
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY,
        account TEXT
    );

    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY,
        name TEXT,
        tax_code TEXT,
        contact TEXT,
        address TEXT DEFAULT "",
        currency TEXT DEFAULT "VND",
        currency_decimals INTEGER DEFAULT 0,
        client_type TEXT DEFAULT "corporate" CHECK(client_type IN ('individual','corporate'))
    );

    CREATE TABLE IF NOT EXISTS individual_customers (
        client_id INTEGER PRIMARY KEY,
        full_name TEXT NOT NULL,
        personal_id TEXT DEFAULT "",
        address TEXT NOT NULL,
        phone TEXT DEFAULT "",
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS corporate_customers (
        client_id INTEGER PRIMARY KEY,
        company_name TEXT NOT NULL,
        tax_code TEXT NOT NULL,
        address TEXT NOT NULL,
        contact_person TEXT DEFAULT "",
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS journal_entries (
        id INTEGER PRIMARY KEY,
        date TEXT,
        ref TEXT,
        note TEXT,
        type TEXT,
        client_id INTEGER DEFAULT NULL,
        supplier_id INTEGER DEFAULT NULL,
        invoice_id INTEGER DEFAULT NULL,
        source_type TEXT DEFAULT '',
        source_id INTEGER DEFAULT NULL,
        posting_key TEXT DEFAULT NULL,
        audit_hash TEXT DEFAULT "",
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
        category TEXT DEFAULT "Hàng hóa",
        min_qty REAL DEFAULT 0.0
    );
    CREATE TABLE IF NOT EXISTS fixed_assets (
        id INTEGER PRIMARY KEY,
        name TEXT,
        value REAL,
        dep_months INTEGER,
        start_date TEXT,
        accumulated_dep REAL DEFAULT 0.0,
        status TEXT DEFAULT 'ACTIVE'
    );

    CREATE TABLE IF NOT EXISTS inventory_log (
        id INTEGER PRIMARY KEY,
        item_id INTEGER,
        date TEXT,
        type TEXT,
        qty REAL,
        note TEXT,
        unit_cost REAL DEFAULT 0.0,
        total_cost REAL DEFAULT 0.0,
        remaining_qty REAL DEFAULT NULL,
        created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime')),
        FOREIGN KEY(item_id) REFERENCES inventory(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY,
        inv_number TEXT UNIQUE,
        inv_type TEXT,
        client_id INTEGER,
        supplier_id INTEGER DEFAULT NULL,
        date TEXT,
        items_json TEXT,
        subtotal REAL,
        vat REAL,
        total REAL,
        pdf_path TEXT,
        created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime')),
        FOREIGN KEY(client_id) REFERENCES clients(id)
    );

    CREATE TABLE IF NOT EXISTS employee_ledger (
        id INTEGER PRIMARY KEY,
        employee_code TEXT NOT NULL,
        employee_name TEXT NOT NULL,
        salary_year INTEGER NOT NULL,
        base_salary REAL NOT NULL,
        allowance REAL DEFAULT 0,
        union_due REAL DEFAULT 0,
        compliance_status TEXT DEFAULT "",
        created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        description TEXT,
        applied_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS period_locks (
        period TEXT PRIMARY KEY,
        is_closed INTEGER NOT NULL DEFAULT 1,
        closed_at TEXT,
        close_note TEXT DEFAULT '',
        reopened_at TEXT,
        reopen_reason TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS period_lock_events (
        id INTEGER PRIMARY KEY,
        period TEXT NOT NULL,
        event TEXT NOT NULL,
        reason TEXT DEFAULT '',
        created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime'))
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
        "ALTER TABLE journal_entries ADD COLUMN supplier_id INTEGER DEFAULT NULL",
        "ALTER TABLE journal_entries ADD COLUMN invoice_id INTEGER DEFAULT NULL",
        "ALTER TABLE journal_entries ADD COLUMN source_type TEXT DEFAULT ''",
        "ALTER TABLE journal_entries ADD COLUMN source_id INTEGER DEFAULT NULL",
        "ALTER TABLE journal_entries ADD COLUMN posting_key TEXT DEFAULT NULL",
        "ALTER TABLE inventory ADD COLUMN base_unit TEXT DEFAULT ''",
        "ALTER TABLE inventory ADD COLUMN conv_factor REAL DEFAULT 1.0",
        "ALTER TABLE inventory ADD COLUMN batch_no TEXT DEFAULT ''",
        "ALTER TABLE inventory ADD COLUMN min_qty REAL DEFAULT 0.0",
        "ALTER TABLE clients ADD COLUMN client_type TEXT DEFAULT 'corporate'",
        "ALTER TABLE journal_entries ADD COLUMN audit_hash TEXT DEFAULT ''",
        "ALTER TABLE fixed_assets ADD COLUMN accumulated_dep REAL DEFAULT 0.0",
        "ALTER TABLE fixed_assets ADD COLUMN status TEXT DEFAULT 'ACTIVE'",
        "ALTER TABLE inventory_log ADD COLUMN unit_cost REAL DEFAULT 0.0",
        "ALTER TABLE inventory_log ADD COLUMN total_cost REAL DEFAULT 0.0",
        "ALTER TABLE inventory_log ADD COLUMN remaining_qty REAL DEFAULT NULL",
    ]
    for sql in migrations:
        try: conn.execute(sql); conn.commit()
        except: pass

    # Register current schema version (Beta v6 -> Version 6)
    try:
        conn.execute("INSERT OR IGNORE INTO schema_version (version, description) VALUES (6, 'Beta v6 schema release')")
        conn.execute("INSERT OR IGNORE INTO schema_version (version, description) VALUES (7, 'Auditable posting and inventory transfer foundation')")
        conn.commit()
    except Exception:
        pass

    # Seed missing TT133 accounts for both new and existing databases.
    # INSERT OR IGNORE keeps user-created account names and codes intact.
    cur = conn.cursor()
    cur.executemany("INSERT OR IGNORE INTO accounts VALUES (?,?,?)", TT133_ACCOUNTS)
    conn.commit()

    _ensure_phase1_schema(conn)

    # A posting key is optional, but unique when supplied. It makes retries
    # safe for services that can be called again after an interrupted request.
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_journal_entries_posting_key "
        "ON journal_entries(posting_key) WHERE posting_key IS NOT NULL AND posting_key <> ''"
    )
    conn.commit()

    try:
        from core.inventory_transfer import ensure_inventory_transfer_schema
        ensure_inventory_transfer_schema(conn)
    except Exception:
        # Keep legacy startup resilient; transfer functions retry the schema
        # check before their first use and surface real migration errors.
        pass

    try:
        from core.asset_transfer import ensure_asset_transfer_schema
        ensure_asset_transfer_schema(conn)
    except Exception:
        # Legacy startup must remain resilient; asset functions retry schema
        # migration and surface real errors when the feature is used.
        pass

    return conn

def _ensure_phase1_schema(conn):
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        tax_code TEXT DEFAULT '',
        address TEXT DEFAULT '',
        bank_account TEXT DEFAULT '',
        bank_name TEXT DEFAULT '',
        contact_person TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        payment_terms_days INTEGER DEFAULT 30,
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS settlement_allocations (
        id INTEGER PRIMARY KEY,
        invoice_id INTEGER,
        payment_entry_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        allocated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime')),
        notes TEXT DEFAULT '',
        FOREIGN KEY(invoice_id) REFERENCES invoices(id),
        FOREIGN KEY(payment_entry_id) REFERENCES journal_entries(id)
    );

    CREATE TABLE IF NOT EXISTS tax_rule_versions (
        id INTEGER PRIMARY KEY,
        rule_type TEXT NOT NULL,
        effective_from TEXT NOT NULL,
        parameters_json TEXT NOT NULL,
        created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime'))
    );
    ''')
    conn.commit()
    
    migrations = [
        "ALTER TABLE journal_entries ADD COLUMN due_date TEXT DEFAULT NULL",
        "ALTER TABLE journal_entries ADD COLUMN supplier_id INTEGER DEFAULT NULL",
        "ALTER TABLE invoices ADD COLUMN due_date TEXT DEFAULT NULL",
        "ALTER TABLE invoices ADD COLUMN supplier_id INTEGER DEFAULT NULL",
    ]
    for sql in migrations:
        try: 
            conn.execute(sql)
            conn.commit()
        except Exception: 
            pass

    # Seed default tax rules
    try:
        from core.tax_rules import seed_default_rules
        seed_default_rules(conn)
    except Exception:
        pass


def get_schema_version(conn) -> int:
    """Return latest integer schema version recorded in the database."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT MAX(version) FROM schema_version")
        row = cur.fetchone()
        return row[0] if row and row[0] is not None else 1
    except Exception:
        return 1


_PERIOD_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def normalize_period(value) -> str:
    """Normalize a YYYY-MM period or an ISO date into YYYY-MM."""
    text = str(value or "").strip()
    period = text[:7] if len(text) >= 7 else text
    if not _PERIOD_RE.fullmatch(period):
        raise ValueError("Kỳ kế toán phải có dạng YYYY-MM")
    return period


def is_period_closed(conn, value) -> bool:
    period = normalize_period(value)
    row = conn.execute(
        "SELECT is_closed FROM period_locks WHERE period=?",
        (period,),
    ).fetchone()
    return bool(row and int(row[0]))


def assert_period_open(conn, value):
    """Reject mutations dated in a closed accounting period."""
    period = normalize_period(value)
    if is_period_closed(conn, period):
        raise ValueError(f"Kỳ kế toán {period} đã khóa; hãy lập chứng từ điều chỉnh ở kỳ mở")
    return period


def get_closed_periods(conn):
    return conn.execute(
        "SELECT period, closed_at, close_note FROM period_locks WHERE is_closed=1 ORDER BY period DESC"
    ).fetchall()


def close_period(conn, value, note=""):
    """Close a period only when the current ledger passes integrity checks."""
    period = normalize_period(value)
    if is_period_closed(conn, period):
        return False
    integrity = validate_ledger_integrity(conn)
    if not integrity["ok"]:
        raise ValueError("Không thể khóa kỳ: sổ có lỗi toàn vẹn hoặc mất cân đối")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn:
        conn.execute(
            """INSERT INTO period_locks(period,is_closed,closed_at,close_note,reopened_at,reopen_reason)
               VALUES (?,?,?,?,NULL,'')
               ON CONFLICT(period) DO UPDATE SET is_closed=1, closed_at=excluded.closed_at,
               close_note=excluded.close_note, reopened_at=NULL, reopen_reason=''""",
            (period, 1, now, str(note or "").strip()),
        )
        conn.execute(
            "INSERT INTO period_lock_events(period,event,reason) VALUES (?,?,?)",
            (period, "CLOSE", str(note or "").strip()),
        )
    return True


def reopen_period(conn, value, reason=""):
    """Reopen a period with a mandatory reason and an audit event."""
    period = normalize_period(value)
    reason = str(reason or "").strip()
    if not reason:
        raise ValueError("Mở khóa kỳ phải có lý do")
    if not is_period_closed(conn, period):
        return False
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn:
        conn.execute(
            "UPDATE period_locks SET is_closed=0, reopened_at=?, reopen_reason=? WHERE period=?",
            (now, reason, period),
        )
        conn.execute(
            "INSERT INTO period_lock_events(period,event,reason) VALUES (?,?,?)",
            (period, "REOPEN", reason),
        )
    return True

def _audit_hash(
    date, ref, note, lines, tx_type="", client_id=None, supplier_id=None,
    source_type="", source_id=None, posting_key=None, invoice_id=None,
):
    payload = {
        "date": date,
        "ref": ref,
        "note": note,
        "type": tx_type,
        "client_id": client_id,
        "lines": [(str(a), float(d), float(c)) for a, d, c in lines],
    }
    # Keep legacy hashes stable while protecting the supplier party on new AP entries.
    if supplier_id is not None:
        payload["supplier_id"] = supplier_id
    # Preserve legacy hashes while protecting newly linked invoice entries.
    if invoice_id is not None:
        payload["invoice_id"] = invoice_id
    if str(source_type or "").strip():
        payload["source_type"] = str(source_type).strip()
    if source_id is not None:
        payload["source_id"] = source_id
    if str(posting_key or "").strip():
        payload["posting_key"] = str(posting_key).strip()
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

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
def _decimal_amount(value, field="amount"):
    try:
        amount = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field} phải là số hợp lệ")
    if not amount.is_finite():
        raise ValueError(f"{field} phải là số hữu hạn")
    return amount.quantize(Decimal("0.01"))


def _validate_journal_lines(conn, lines):
    """Validate account, sign, one-sided line, and balanced-entry rules."""
    rows = list(lines or [])
    if not rows:
        raise ValueError("Chứng từ phải có ít nhất một dòng hạch toán")

    account_codes = {str(row[0]) for row in conn.execute("SELECT code FROM accounts")}
    normalized = []
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")

    for index, line in enumerate(rows, start=1):
        if len(line) != 3:
            raise ValueError(f"Dòng hạch toán {index} phải có dạng (tài khoản, Nợ, Có)")
        account, debit, credit = line
        account = str(account or "").strip()
        valid_account = account in account_codes or any(
            account.startswith(code) and account[len(code):].isdigit()
            for code in account_codes
        )
        if not account or not account.isdigit() or not valid_account:
            raise ValueError(f"Tài khoản không hợp lệ: {account or '(trống)'}")

        debit = _decimal_amount(debit, f"Nợ dòng {index}")
        credit = _decimal_amount(credit, f"Có dòng {index}")
        if debit < 0 or credit < 0:
            raise ValueError(f"Nợ/Có dòng {index} không được âm")
        if debit > 0 and credit > 0:
            raise ValueError(f"Dòng {index} không được đồng thời có cả Nợ và Có")
        if debit == 0 and credit == 0:
            raise ValueError(f"Dòng {index} phải có số tiền khác 0")

        total_debit += debit
        total_credit += credit
        normalized.append((account, float(debit), float(credit)))

    if total_debit == 0 or abs(total_debit - total_credit) > Decimal("0.01"):
        raise ValueError(f"Mất cân đối: Nợ {total_debit:,.2f} ≠ Có {total_credit:,.2f}")
    return normalized


def _insert_journal_entry(
    conn, date, ref, note, normalized, tx_type="", client_id=None, supplier_id=None,
    invoice_id=None, source_type="", source_id=None, posting_key=None,
):
    """Insert a validated entry without committing; callers own the transaction."""
    cur = conn.cursor()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ahash = _audit_hash(
        date, ref, note, normalized, tx_type, client_id, supplier_id,
        source_type, source_id, posting_key, invoice_id,
    )
    cur.execute(
        "INSERT INTO journal_entries(date,ref,note,type,client_id,supplier_id,invoice_id,"
        "source_type,source_id,posting_key,audit_hash,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (date, ref, note, tx_type, client_id, supplier_id, invoice_id,
         source_type or "", source_id, posting_key, ahash, ts),
    )
    eid = cur.lastrowid
    cur.executemany("INSERT INTO journal_lines VALUES (NULL,?,?,?,?)",
                    [(eid, *line) for line in normalized])
    return eid


def post_entry(
    conn, date, ref, note, lines, tx_type="", client_id=None, supplier_id=None,
    invoice_id=None, source_type="", source_id=None, posting_key=None,
):
    assert_period_open(conn, date)
    normalized = _validate_journal_lines(conn, lines)
    with conn:
        return _insert_journal_entry(
            conn, date, ref, note, normalized, tx_type, client_id, supplier_id,
            invoice_id, source_type, source_id, posting_key,
        )


def _entry_is_invoice_linked(conn, entry_id, ref=None, tx_type=None, invoice_id=None):
    """Return whether an entry is owned by an invoice rather than the ledger UI."""
    if invoice_id is not None:
        return True
    if str(tx_type or "").strip().lower() != "sales" or not str(ref or "").strip():
        return False
    return conn.execute("SELECT 1 FROM invoices WHERE inv_number=?", (ref,)).fetchone() is not None


def _entry_is_source_linked(source_type=None, source_id=None, posting_key=None):
    return bool(
        str(source_type or "").strip()
        or source_id is not None
        or str(posting_key or "").strip()
    )


def _entry_is_protected(conn, entry_id, ref=None, tx_type=None, invoice_id=None,
                        source_type=None, source_id=None, posting_key=None):
    return _entry_is_invoice_linked(conn, entry_id, ref, tx_type, invoice_id) or _entry_is_source_linked(
        source_type, source_id, posting_key
    )

def update_entry(conn, entry_id, date, ref, note, lines, tx_type="", client_id=None, supplier_id=None):
    current = conn.execute(
        "SELECT date, ref, type, invoice_id, source_type, source_id, posting_key "
        "FROM journal_entries WHERE id=?", (entry_id,)
    ).fetchone()
    if not current:
        raise ValueError(f"Không tìm thấy chứng từ #{entry_id}")
    if _entry_is_protected(conn, entry_id, current[1], current[2], current[3], current[4], current[5], current[6]):
        raise ValueError("Không thể sửa bút toán liên kết hóa đơn; hãy điều chỉnh từ quy trình hóa đơn")
    assert_period_open(conn, current[0])
    assert_period_open(conn, date)
    normalized = _validate_journal_lines(conn, lines)
    with conn:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ahash = _audit_hash(date, ref, note, normalized, tx_type, client_id, supplier_id)
        cur = conn.execute(
            "UPDATE journal_entries SET date=?, ref=?, note=?, type=?, client_id=?, supplier_id=?, audit_hash=?, created_at=? WHERE id=?",
            (date, ref, note, tx_type, client_id, supplier_id, ahash, ts, entry_id)
        )
        if cur.rowcount != 1:
            raise ValueError(f"Không tìm thấy chứng từ #{entry_id}")
        conn.execute("DELETE FROM journal_lines WHERE entry_id=?", (entry_id,))
        conn.executemany("INSERT INTO journal_lines VALUES (NULL,?,?,?,?)",
                         [(entry_id, *line) for line in normalized])

def _check_balanced(lines):
    dr = sum((_decimal_amount(l[1], "Nợ") for l in lines), Decimal("0.00"))
    cr = sum((_decimal_amount(l[2], "Có") for l in lines), Decimal("0.00"))
    if abs(dr - cr) > Decimal("0.01"):
        raise ValueError(f"Mất cân đối (Unbalanced): Nợ {dr:,.2f} ≠ Có {cr:,.2f}")


def validate_ledger_integrity(conn):
    """Return a read-only integrity report for journal balance and audit hashes."""
    issues = []
    entries = conn.execute(
        "SELECT id,date,ref,note,type,client_id,supplier_id,invoice_id,source_type,source_id,posting_key,audit_hash "
        "FROM journal_entries ORDER BY id"
    ).fetchall()
    for entry_id, date, ref, note, tx_type, client_id, supplier_id, invoice_id, source_type, source_id, posting_key, audit_hash in entries:
        lines = conn.execute(
            "SELECT account,debit,credit FROM journal_lines WHERE entry_id=? ORDER BY id",
            (entry_id,),
        ).fetchall()
        try:
            normalized = _validate_journal_lines(conn, lines)
        except ValueError as exc:
            issues.append(f"Chứng từ #{entry_id}: {exc}")
            continue
        expected = _audit_hash(
            date, ref, note, normalized, tx_type or "", client_id, supplier_id,
            source_type, source_id, posting_key, invoice_id,
        )
        legacy_expected = _audit_hash(
            date, ref, note, normalized, tx_type or "", client_id, supplier_id,
            source_type, source_id, posting_key,
        )
        if not audit_hash:
            issues.append(f"Chứng từ #{entry_id}: thiếu audit hash")
        elif audit_hash != expected and audit_hash != legacy_expected:
            issues.append(f"Chứng từ #{entry_id}: audit hash không khớp")

    return {"ok": not issues, "entries_checked": len(entries), "issues": issues}

def export_audit_trail(conn):
    """Export complete audit trail with cryptographic verification status."""
    entries = conn.execute("""
        SELECT e.id, e.date, e.ref, e.note, e.type, e.client_id, e.supplier_id,
               e.invoice_id, e.source_type, e.source_id, e.posting_key, e.audit_hash, e.created_at,
               COUNT(l.id) as total_lines, SUM(l.debit) as total_debit, SUM(l.credit) as total_credit
        FROM journal_entries e
        LEFT JOIN journal_lines l ON e.id = l.entry_id
        GROUP BY e.id
        ORDER BY e.id ASC
    """).fetchall()

    audit_data = []
    for row in entries:
        eid, date, ref, note, tx_type, client_id, supplier_id, invoice_id, source_type, source_id, posting_key, ahash, created_at, lines_cnt, dr, cr = row
        lines = conn.execute("SELECT account,debit,credit FROM journal_lines WHERE entry_id=? ORDER BY id", (eid,)).fetchall()
        expected = ""
        is_valid = False
        try:
            norm = _validate_journal_lines(conn, lines)
            expected = _audit_hash(
                date, ref, note, norm, tx_type or "", client_id, supplier_id,
                source_type, source_id, posting_key, invoice_id,
            )
            legacy_expected = _audit_hash(
                date, ref, note, norm, tx_type or "", client_id, supplier_id,
                source_type, source_id, posting_key,
            )
            is_valid = ahash in {expected, legacy_expected}
        except Exception:
            is_valid = False

        audit_data.append({
            "entry_id": eid,
            "date": date,
            "ref": ref,
            "note": note,
            "type": tx_type,
            "client_id": client_id,
            "supplier_id": supplier_id,
            "invoice_id": invoice_id,
            "source_type": source_type or "",
            "source_id": source_id,
            "posting_key": posting_key,
            "total_debit": dr or 0.0,
            "total_credit": cr or 0.0,
            "stored_hash": ahash or "",
            "expected_hash": expected,
            "verified": is_valid,
            "created_at": created_at,
        })
    return pd.DataFrame(audit_data)

def delete_entry(conn, entry_id):
    current = conn.execute(
        "SELECT date, ref, type, invoice_id, source_type, source_id, posting_key "
        "FROM journal_entries WHERE id=?", (entry_id,)
    ).fetchone()
    if not current:
        return False
    if _entry_is_protected(conn, entry_id, current[1], current[2], current[3], current[4], current[5], current[6]):
        raise ValueError("Không thể xóa bút toán liên kết hóa đơn; hãy điều chỉnh từ quy trình hóa đơn")
    assert_period_open(conn, current[0])
    conn.execute("DELETE FROM journal_entries WHERE id=?", (entry_id,))
    conn.commit()
    return True


def reverse_entry(conn, entry_id, reversal_date, ref="", note=""):
    """Create an offsetting entry without changing the original entry."""
    row = conn.execute(
        "SELECT date, ref, note, type, client_id, supplier_id, invoice_id, "
        "source_type, source_id, posting_key FROM journal_entries WHERE id=?",
        (entry_id,),
    ).fetchone()
    if not row:
        raise ValueError(f"Không tìm thấy chứng từ #{entry_id}")
    if _entry_is_protected(conn, entry_id, row[1], row[3], row[6], row[7], row[8], row[9]):
        raise ValueError("Không thể đảo bút toán liên kết hóa đơn; hãy điều chỉnh từ quy trình hóa đơn")
    lines = conn.execute(
        "SELECT account, debit, credit FROM journal_lines WHERE entry_id=? ORDER BY id",
        (entry_id,),
    ).fetchall()
    if not lines:
        raise ValueError("Chứng từ gốc không có dòng hạch toán")
    reversal_ref = str(ref or f"REV-{row[1] or entry_id}").strip()
    reversal_note = str(note or f"Đảo chứng từ #{entry_id}: {row[2] or ''}").strip()
    reversed_lines = [(account, credit, debit) for account, debit, credit in lines]
    return post_entry(
        conn,
        reversal_date,
        reversal_ref,
        reversal_note,
        reversed_lines,
        "Reversal",
        client_id=row[4],
        supplier_id=row[5],
    )

def get_flat_df(conn):
    return pd.read_sql('''
        SELECT e.id AS entry_id, e.date, e.created_at, e.ref, e.note, e.type,
               l.account, l.debit, l.credit, e.client_id, e.supplier_id,
               e.source_type, e.source_id, e.posting_key
        FROM journal_entries e
        JOIN journal_lines l ON e.id = l.entry_id
        ORDER BY e.date DESC, e.created_at DESC, e.id DESC
    ''', conn)


def get_dashboard_totals(conn):
    """Return startup dashboard totals directly from SQLite, without Pandas."""
    cursor = conn.execute("""
        SELECT COUNT(l.id) AS line_count,
               COALESCE(SUM(CASE WHEN l.account LIKE '511%' AND l.credit > 0 THEN l.credit ELSE 0 END), 0) AS revenue_511,
               COALESCE(SUM(CASE WHEN l.account LIKE '515%' AND l.credit > 0 THEN l.credit ELSE 0 END), 0) AS revenue_515,
               COALESCE(SUM(CASE WHEN l.account LIKE '632%' AND l.debit > 0 THEN l.debit ELSE 0 END), 0) AS cogs_632,
               COALESCE(SUM(CASE WHEN l.account LIKE '635%' AND l.debit > 0 THEN l.debit ELSE 0 END), 0) AS expense_635,
               COALESCE(SUM(CASE WHEN l.account LIKE '641%' AND l.debit > 0 THEN l.debit ELSE 0 END), 0) AS expense_641,
               COALESCE(SUM(CASE WHEN l.account LIKE '642%' AND l.debit > 0 THEN l.debit ELSE 0 END), 0) AS expense_642,
               COALESCE(SUM(CASE WHEN l.account LIKE '811%' AND l.debit > 0 THEN l.debit ELSE 0 END), 0) AS expense_811,
               COALESCE(SUM(CASE WHEN l.account LIKE '3331%' AND l.credit > 0 THEN l.credit ELSE 0 END), 0) AS vat_output,
               COALESCE(SUM(CASE WHEN l.account LIKE '133%' AND l.debit > 0 THEN l.debit ELSE 0 END), 0) AS vat_input,
               COALESCE(SUM(CASE WHEN l.account LIKE '111%' OR l.account LIKE '112%' OR l.account LIKE '113%' THEN l.debit - l.credit ELSE 0 END), 0) AS cash,
               COALESCE(SUM(CASE WHEN l.account LIKE '131%' OR l.account LIKE '138%' THEN l.debit - l.credit ELSE 0 END), 0) AS receivable,
               COALESCE(SUM(CASE WHEN l.account LIKE '331%' OR l.account LIKE '333%' OR l.account LIKE '334%' OR l.account LIKE '338%' THEN l.credit - l.debit ELSE 0 END), 0) AS payable
        FROM journal_lines l
        JOIN journal_entries e ON e.id = l.entry_id
    """)
    row = cursor.fetchone()
    totals = dict(zip((column[0] for column in cursor.description), row))
    totals["has_data"] = bool(totals.pop("line_count", 0))
    return totals


def get_dashboard_revenue_summary(conn, limit=6):
    """Return recent monthly chart values as plain records, without Pandas."""
    limit = max(1, min(120, int(limit)))
    cursor = conn.execute("""
        SELECT substr(e.date, 1, 7) AS period,
               COALESCE(SUM(CASE WHEN l.credit > 0 AND (l.account LIKE '511%' OR l.account LIKE '515%') THEN l.credit ELSE 0 END), 0) AS revenue,
               COALESCE(SUM(CASE WHEN l.debit > 0 AND (l.account LIKE '632%' OR l.account LIKE '635%' OR l.account LIKE '641%' OR l.account LIKE '642%' OR l.account LIKE '811%') THEN l.debit ELSE 0 END), 0) AS expense
        FROM journal_entries e
        JOIN journal_lines l ON e.id = l.entry_id
        WHERE e.date IS NOT NULL AND length(e.date) >= 7
        GROUP BY substr(e.date, 1, 7)
        ORDER BY period DESC
        LIMIT ?
    """, (limit,))
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row)) for row in reversed(cursor.fetchall())]

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
def add_client(conn, name, tax_code, contact, address="", currency="VND", currency_decimals=0, client_type="corporate"):
    from core.validation import validate_client_payload

    cleaned = validate_client_payload({
        "name": name,
        "tax_code": tax_code,
        "contact": contact,
        "address": address,
        "currency": currency,
        "currency_decimals": currency_decimals,
        "client_type": client_type,
    })
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO clients (name,tax_code,contact,address,currency,currency_decimals,client_type)
           VALUES (?,?,?,?,?,?,?)""",
        (cleaned["name"], cleaned["tax_code"], contact, cleaned["address"], currency, currency_decimals, cleaned["client_type"])
    )
    client_id = cur.lastrowid
    if cleaned["client_type"] == "individual":
        cur.execute(
            """INSERT OR REPLACE INTO individual_customers
               (client_id,full_name,address,phone) VALUES (?,?,?,?)""",
            (client_id, cleaned["name"], cleaned["address"], contact or ""),
        )
    else:
        cur.execute(
            """INSERT OR REPLACE INTO corporate_customers
               (client_id,company_name,tax_code,address,contact_person) VALUES (?,?,?,?,?)""",
            (client_id, cleaned["name"], cleaned["tax_code"], cleaned["address"], contact or ""),
        )
    conn.commit()
    return client_id

def update_client(conn, client_id, name, tax_code, contact, address="", currency="VND", currency_decimals=0, client_type="corporate"):
    from core.validation import validate_client_payload

    cleaned = validate_client_payload({
        "name": name,
        "tax_code": tax_code,
        "contact": contact,
        "address": address,
        "currency": currency,
        "currency_decimals": currency_decimals,
        "client_type": client_type,
    })
    conn.execute(
        "UPDATE clients SET name=?, tax_code=?, contact=?, address=?, currency=?, currency_decimals=?, client_type=? WHERE id=?",
        (cleaned["name"], cleaned["tax_code"], contact, cleaned["address"], currency, currency_decimals, cleaned["client_type"], client_id)
    )
    conn.execute("DELETE FROM individual_customers WHERE client_id=?", (client_id,))
    conn.execute("DELETE FROM corporate_customers WHERE client_id=?", (client_id,))
    if cleaned["client_type"] == "individual":
        conn.execute(
            """INSERT INTO individual_customers (client_id,full_name,address,phone)
               VALUES (?,?,?,?)""",
            (client_id, cleaned["name"], cleaned["address"], contact or ""),
        )
    else:
        conn.execute(
            """INSERT INTO corporate_customers (client_id,company_name,tax_code,address,contact_person)
               VALUES (?,?,?,?,?)""",
            (client_id, cleaned["name"], cleaned["tax_code"], cleaned["address"], contact or ""),
        )
    conn.commit()

def get_clients(conn):
    df = pd.read_sql("SELECT * FROM clients", conn)
    if "currency_decimals" in df.columns:
        df["currency_decimals"] = pd.to_numeric(df["currency_decimals"], errors="coerce").fillna(0).clip(0, 6).astype(int)
    return df

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


def get_client_by_id(conn, client_id):
    """Return one customer by stable primary key for UI/data linkage."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE id=?", (client_id,))
    row = cur.fetchone()
    if row:
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    return None

# ── Inventory ────────────────────────────────────────────────
def add_inventory(conn, name, unit, base_unit, conv_factor, qty, cost, price, batch_no, category="Hàng hóa", min_qty=0.0):
    from core.validation import parse_number

    name = str(name or "").strip()
    if not name:
        raise ValueError("Tên hàng hóa không được trống")
    unit = str(unit or "Cái").strip() or "Cái"
    base_unit = str(base_unit or unit).strip() or unit
    conv_factor = parse_number(conv_factor, "Tỷ lệ quy đổi", minimum=0.000001)
    qty = parse_number(qty, "Số lượng tồn", default=0.0, minimum=0.0)
    cost = parse_number(cost, "Giá vốn", default=0.0, minimum=0.0)
    price = parse_number(price, "Giá bán", default=0.0, minimum=0.0)
    min_qty = parse_number(min_qty, "Ngưỡng cảnh báo", default=0.0, minimum=0.0)
    conn.execute(
        """INSERT INTO inventory
           (name,unit,base_unit,conv_factor,qty,cost,price,batch_no,category,min_qty)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (name, unit, base_unit, conv_factor, qty, cost, price,
         str(batch_no or "").strip(), str(category or "Hàng hóa").strip() or "Hàng hóa", min_qty),
    )
    conn.commit()

def update_inventory(conn, item_id, name, unit, base_unit, conv_factor, qty, cost, price, batch_no, category="Hàng hóa", min_qty=0.0):
    from core.validation import parse_number

    name = str(name or "").strip()
    if not name:
        raise ValueError("Tên hàng hóa không được trống")
    unit = str(unit or "Cái").strip() or "Cái"
    base_unit = str(base_unit or unit).strip() or unit
    conv_factor = parse_number(conv_factor, "Tỷ lệ quy đổi", minimum=0.000001)
    qty = parse_number(qty, "Số lượng tồn", default=0.0, minimum=0.0)
    cost = parse_number(cost, "Giá vốn", default=0.0, minimum=0.0)
    price = parse_number(price, "Giá bán", default=0.0, minimum=0.0)
    min_qty = parse_number(min_qty, "Ngưỡng cảnh báo", default=0.0, minimum=0.0)
    current = conn.execute(
        "SELECT qty, cost FROM inventory WHERE id=?", (item_id,)
    ).fetchone()
    if not current:
        raise ValueError(f"Không tìm thấy mặt hàng #{item_id}")
    try:
        location_rows = conn.execute(
            "SELECT COUNT(*) FROM inventory_location_balances WHERE item_id=?", (item_id,)
        ).fetchone()[0]
    except sqlite3.OperationalError:
        location_rows = 0
    if location_rows and (
        abs(float(current[0] or 0.0) - qty) > 0.000001
        or abs(float(current[1] or 0.0) - cost) > 0.01
    ):
        raise ValueError(
            "Mặt hàng đã theo dõi theo địa điểm; không sửa trực tiếp tồn hoặc giá vốn. "
            "Hãy dùng nhập/xuất/điều chuyển có lý do"
        )
    conn.execute(
        "UPDATE inventory SET name=?, unit=?, base_unit=?, conv_factor=?, qty=?, cost=?, price=?, batch_no=?, category=?, min_qty=? WHERE id=?",
        (name, unit, base_unit, conv_factor, qty, cost, price,
         str(batch_no or "").strip(), str(category or "Hàng hóa").strip() or "Hàng hóa", min_qty, item_id)
    )
    conn.commit()

def get_inventory(conn):
    df = pd.read_sql("SELECT * FROM inventory", conn)
    for column, default in {
        "conv_factor": 1.0, "qty": 0.0, "cost": 0.0,
        "price": 0.0, "min_qty": 0.0,
    }.items():
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(default)
    if "category" in df.columns:
        df["category"] = df["category"].fillna("").astype(str).map(
            lambda value: "Hàng hóa" if value.strip().lower() in {"", "chung", "none", "nan"} else value.strip()
        )
    return df

def delete_inventory(conn, item_id):
    conn.execute("DELETE FROM inventory WHERE id=?", (item_id,))
    conn.commit()

# ── Inventory Log (import/export tracking) ───────────────────
def add_inventory_log(conn, item_id, date, log_type, qty, note=""):
    """log_type: 'import' (nhập) or 'export' (xuất)"""
    from core.inventory import post_stock_in, post_stock_out
    row = conn.execute("SELECT cost FROM inventory WHERE id=?", (item_id,)).fetchone()
    if not row:
        raise ValueError(f"Mặt hàng #{item_id} không tồn tại")
    kind = str(log_type).lower()
    if kind in {"import", "in", "nhập"}:
        return post_stock_in(conn, item_id, qty, row[0] or 0, date=date, note=note)
    if kind in {"export", "out", "xuất"}:
        return post_stock_out(conn, item_id, qty, date=date, note=note)
    raise ValueError(f"Loại nhập/xuất không hợp lệ: {log_type}")

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
    conn.execute(
        "INSERT INTO fixed_assets(name, value, dep_months, start_date, accumulated_dep, status) VALUES (?,?,?,?,0.0,'ACTIVE')",
        (name, value, dep_months, start_date)
    )
    conn.commit()

def update_asset(conn, asset_id, name, value, dep_months, start_date):
    conn.execute(
        "UPDATE fixed_assets SET name=?, value=?, dep_months=?, start_date=? WHERE id=?",
        (name, value, dep_months, start_date, asset_id)
    )
    conn.commit()

def get_assets(conn):
    df = pd.read_sql("SELECT * FROM fixed_assets", conn)
    for column, default in {"value": 0.0, "dep_months": 36, "accumulated_dep": 0.0}.items():
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(default)
    return df

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

def save_invoice(
    conn, inv_number, inv_type, client_id, date, items_json, subtotal, vat, total, pdf_path,
    company_name="", seller_full_name="", auto_post=False,
):
    assert_period_open(conn, date)
    cur = conn.cursor()
    row = cur.execute("SELECT name, address FROM clients WHERE id=?", (client_id,)).fetchone()
    if not row:
        raise ValueError(f"Không tìm thấy khách hàng #{client_id}")
    try:
        items = json.loads(items_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Danh sách hàng hóa của hóa đơn không hợp lệ") from exc

    from core.validation import validate_invoice_payload
    validate_invoice_payload({
        "company_name": company_name or "LOCAL_COMPANY_VALIDATED_BY_UI",
        "buyer_full_name": row[0],
        "seller_full_name": seller_full_name or "LOCAL_SELLER_VALIDATED_BY_UI",
        "address": row[1],
        "items": items,
    })

    # Keep invoice persistence and inventory deduction in one transaction.
    inventory_cogs = 0.0
    journal_entry_id = None
    with conn:
        invoice_id = conn.execute(
            """INSERT INTO invoices (inv_number, inv_type, client_id, date, items_json,
               subtotal, vat, total, pdf_path) VALUES (?,?,?,?,?,?,?,?,?)""",
            (inv_number, inv_type, client_id, date, items_json, subtotal, vat, total, pdf_path),
        ).lastrowid

        from core.inventory import post_stock_out
        for item in items:
            item_id = item.get("item_id")
            if item_id:
                stock_row = cur.execute(
                    "SELECT id, conv_factor FROM inventory WHERE id=?", (item_id,)
                ).fetchone()
                if not stock_row:
                    raise ValueError(f"Mặt hàng #{item_id} không tồn tại")
            else:
                stock_row = cur.execute(
                    "SELECT id, conv_factor FROM inventory WHERE name=?", (item.get("name",),)
                ).fetchone()
            if stock_row:
                iid, factor = stock_row
                from core.validation import parse_number
                safe_factor = parse_number(factor, "Tỷ lệ quy đổi", default=1.0, minimum=0.000001)
                deduct_qty = float(item["qty"]) * safe_factor
                inventory_cogs += float(post_stock_out(
                    conn,
                    iid,
                    deduct_qty,
                    date=date,
                    note=f"HĐ {inv_number}",
                    method="weighted_avg",
                    commit=False,
                ) or 0.0)

        if auto_post:
            journal_lines = [("511", 0, subtotal), ("131", subtotal + vat, 0)]
            if float(vat or 0) > 0:
                journal_lines.append(("3331", 0, vat))
            if inventory_cogs > 0:
                journal_lines.extend([("632", inventory_cogs, 0), ("156", 0, inventory_cogs)])
            normalized = _validate_journal_lines(conn, journal_lines)
            journal_entry_id = _insert_journal_entry(
                conn,
                date,
                inv_number,
                f"HĐ {inv_number} — {row[0]}",
                normalized,
                "Sales",
                client_id,
                invoice_id=invoice_id,
            )

    # The caller can use this cost to post the matching Dr 632 / Cr 156 lines.
    # Keeping that step explicit preserves compatibility with older callers.
    return {"inventory_cogs": inventory_cogs, "journal_entry_id": journal_entry_id}

def get_invoices(conn, client_id=None):
    if client_id:
        df = pd.read_sql(
            "SELECT i.*, c.name AS client_name FROM invoices i "
            "LEFT JOIN clients c ON c.id=i.client_id "
            "WHERE i.client_id=? ORDER BY i.created_at DESC",
            conn,
            params=(client_id,),
        )
    else:
        df = pd.read_sql(
            "SELECT i.*, c.name AS client_name FROM invoices i "
            "LEFT JOIN clients c ON c.id=i.client_id ORDER BY i.created_at DESC",
            conn,
        )
    for column in ("subtotal", "vat", "total"):
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0)
    return df

def delete_invoice(conn, inv_number):
    """Delete a locally issued, unsettled invoice and safely reverse its stock effect.

    An invoice is only removable while its own period remains open. Later stock
    movements make a physical rollback ambiguous, so those cases must use an
    explicit correction workflow instead of rewriting history.
    """
    cur = conn.cursor()
    invoice = cur.execute(
        "SELECT id, date, client_id FROM invoices WHERE inv_number=?", (inv_number,)
    ).fetchone()
    if not invoice:
        return False
    invoice_id, invoice_date, client_id = invoice
    assert_period_open(conn, invoice_date)

    settlement_count = cur.execute(
        "SELECT COUNT(*) FROM settlement_allocations WHERE invoice_id=?", (invoice_id,)
    ).fetchone()[0]
    if settlement_count:
        raise ValueError("Không thể xóa hóa đơn đã được cấn trừ; hãy lập chứng từ điều chỉnh")

    stock_rows = cur.execute(
        "SELECT id, item_id, qty FROM inventory_log WHERE type='OUT' AND note=? ORDER BY id",
        (f"HĐ {inv_number}",),
    ).fetchall()
    for log_id, item_id, _ in stock_rows:
        later_movement = cur.execute(
            "SELECT 1 FROM inventory_log WHERE item_id=? AND id>? LIMIT 1", (item_id, log_id)
        ).fetchone()
        if later_movement:
            raise ValueError(
                "Không thể xóa hóa đơn vì hàng đã có biến động kho sau đó; hãy lập chứng từ điều chỉnh"
            )

    entry_ids = [
        row[0]
        for row in cur.execute("SELECT id FROM journal_entries WHERE invoice_id=?", (invoice_id,)).fetchall()
    ]
    if not entry_ids:
        # Older databases have no invoice_id link. Only accept one unambiguous
        # sales entry; never delete an unrelated voucher that shares a ref.
        entry_ids = [
            row[0]
            for row in cur.execute(
                "SELECT id FROM journal_entries WHERE ref=? AND type='Sales' AND client_id=?",
                (inv_number, client_id),
            ).fetchall()
        ]
        if len(entry_ids) > 1:
            raise ValueError("Không thể xác định duy nhất bút toán hóa đơn cũ; hãy lập chứng từ điều chỉnh")

    with conn:
        for _, item_id, qty in stock_rows:
            cur.execute("UPDATE inventory SET qty=COALESCE(qty, 0)+? WHERE id=?", (qty, item_id))
        if stock_rows:
            cur.executemany("DELETE FROM inventory_log WHERE id=?", [(row[0],) for row in stock_rows])
        cur.executemany("DELETE FROM journal_entries WHERE id=?", [(entry_id,) for entry_id in entry_ids])
        cur.execute("DELETE FROM invoices WHERE id=?", (invoice_id,))
    return True

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
               SUM(CASE WHEN l.credit > 0 AND (l.account LIKE '511%' OR l.account LIKE '515%') THEN l.credit ELSE 0 END) as revenue,
               SUM(CASE WHEN l.debit > 0 AND (
                   l.account LIKE '632%' OR l.account LIKE '635%' OR l.account LIKE '641%' OR
                   l.account LIKE '642%' OR l.account LIKE '811%'
               ) THEN l.debit ELSE 0 END) as expense
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

# ── Suppliers ─────────────────────────────────────────────────
def add_supplier(conn, name, tax_code='', address='', bank_account='', bank_name='',
                 contact_person='', phone='', email='', payment_terms_days=30, notes=''):
    cur = conn.cursor()
    cur.execute(
        '''INSERT INTO suppliers(name, tax_code, address, bank_account, bank_name,
           contact_person, phone, email, payment_terms_days, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?)''',
        (name, tax_code, address, bank_account, bank_name,
         contact_person, phone, email, payment_terms_days, notes))
    conn.commit()
    return cur.lastrowid

def get_suppliers(conn):
    return pd.read_sql("SELECT * FROM suppliers ORDER BY name", conn)

def update_supplier(conn, supplier_id, **kwargs):
    allowed = {'name','tax_code','address','bank_account','bank_name',
               'contact_person','phone','email','payment_terms_days','notes'}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    sets = ', '.join(f'{k}=?' for k in fields)
    vals = list(fields.values()) + [supplier_id]
    conn.execute(f'UPDATE suppliers SET {sets} WHERE id=?', vals)
    conn.commit()

def delete_supplier(conn, supplier_id):
    conn.execute('DELETE FROM suppliers WHERE id=?', (supplier_id,))
    conn.commit()

# ── Settlement Allocation ─────────────────────────────────────
def allocate_settlement(conn, payment_entry_id, invoice_id, amount, notes='', commit=True):
    """Allocate a valid AR/AP payment to a specific invoice.

    The allocation cannot exceed either the invoice outstanding amount or the
    payment's posted 131/331 control-account capacity.
    """
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError('Số tiền phân bổ không hợp lệ')
    if amount <= 0:
        raise ValueError('Số tiền phân bổ phải lớn hơn 0')

    invoice = conn.execute(
        'SELECT total, client_id, supplier_id FROM invoices WHERE id=?', (invoice_id,)
    ).fetchone()
    if invoice is None:
        raise ValueError('Không tìm thấy hóa đơn cần phân bổ')

    payment = conn.execute(
        'SELECT id, date, client_id, supplier_id FROM journal_entries WHERE id=?', (payment_entry_id,)
    ).fetchone()
    if payment is None:
        raise ValueError('Không tìm thấy bút toán thanh toán')

    _, payment_date, payment_client_id, payment_supplier_id = payment
    assert_period_open(conn, payment_date)
    _, invoice_client_id, invoice_supplier_id = invoice
    if invoice_client_id is not None and invoice_supplier_id is not None:
        raise ValueError('Hóa đơn không thể đồng thời thuộc khách hàng và nhà cung cấp')
    if invoice_client_id is not None:
        if payment_client_id != invoice_client_id:
            raise ValueError('Bút toán thanh toán không thuộc khách hàng của hóa đơn')
        control_balance = conn.execute(
            "SELECT COALESCE(SUM(credit - debit), 0) FROM journal_lines "
            "WHERE entry_id=? AND account LIKE '131%'",
            (payment_entry_id,),
        ).fetchone()[0]
        control_label = 'ghi Có TK 131'
    elif invoice_supplier_id is not None:
        if payment_supplier_id != invoice_supplier_id:
            raise ValueError('Bút toán thanh toán không thuộc nhà cung cấp của hóa đơn')
        control_balance = conn.execute(
            "SELECT COALESCE(SUM(debit - credit), 0) FROM journal_lines "
            "WHERE entry_id=? AND account LIKE '331%'",
            (payment_entry_id,),
        ).fetchone()[0]
        control_label = 'ghi Nợ TK 331'
    else:
        raise ValueError('Hóa đơn thiếu thông tin khách hàng hoặc nhà cung cấp')
    control_balance = float(control_balance or 0)
    if control_balance <= 0:
        raise ValueError(f'Bút toán thanh toán phải {control_label}')

    settled = conn.execute(
        'SELECT COALESCE(SUM(amount), 0) FROM settlement_allocations WHERE invoice_id=?',
        (invoice_id,),
    ).fetchone()[0] or 0
    outstanding = float(invoice[0] or 0) - float(settled)
    if amount > outstanding + 0.01:
        raise ValueError(
            f'Số tiền phân bổ vượt số dư hóa đơn còn lại ({outstanding:,.2f})'
        )

    allocated_from_payment = conn.execute(
        'SELECT COALESCE(SUM(amount), 0) FROM settlement_allocations WHERE payment_entry_id=?',
        (payment_entry_id,),
    ).fetchone()[0] or 0
    remaining_capacity = control_balance - float(allocated_from_payment)
    if amount > remaining_capacity + 0.01:
        raise ValueError(
            f'Số tiền phân bổ vượt khả năng cấn trừ của chứng từ ({remaining_capacity:,.2f})'
        )

    cursor = conn.execute(
        'INSERT INTO settlement_allocations(invoice_id, payment_entry_id, amount, notes) VALUES (?,?,?,?)',
        (invoice_id, payment_entry_id, amount, notes))
    if commit:
        conn.commit()
    return cursor.lastrowid

def get_invoice_settlements(conn, invoice_id):
    """Get all settlements for an invoice."""
    return pd.read_sql(
        '''SELECT sa.id, sa.payment_entry_id, sa.amount, sa.allocated_at, sa.notes,
                  e.date as payment_date, e.ref as payment_ref
           FROM settlement_allocations sa
           JOIN journal_entries e ON sa.payment_entry_id = e.id
           WHERE sa.invoice_id = ?
           ORDER BY sa.allocated_at''',
        conn, params=(invoice_id,))

def get_open_invoices(conn, client_id=None, supplier_id=None):
    """Get invoices with outstanding balance (total - settled)."""
    clauses = ['1=1']
    params = []
    if client_id is not None:
        clauses.append('i.client_id = ?')
        params.append(client_id)
    if supplier_id is not None:
        clauses.append('i.supplier_id = ?')
        params.append(supplier_id)
    where = ' AND '.join(clauses)
    sql = f'''
        SELECT i.id, i.inv_number, i.inv_type, i.date, i.due_date,
               i.total, i.client_id, i.supplier_id,
               COALESCE(c.name, s.name, '') AS party_name,
               COALESCE(SUM(sa.amount), 0) as settled,
               i.total - COALESCE(SUM(sa.amount), 0) as outstanding
        FROM invoices i
        LEFT JOIN clients c ON c.id = i.client_id
        LEFT JOIN suppliers s ON s.id = i.supplier_id
        LEFT JOIN settlement_allocations sa ON i.id = sa.invoice_id
        WHERE {where}
        GROUP BY i.id
        HAVING outstanding > 0.01
        ORDER BY i.date
    '''
    return pd.read_sql(sql, conn, params=params)

def get_supplier_debt_summary(conn):
    """AP summary grouped by supplier."""
    sql = '''
        SELECT s.id as supplier_id, s.name as supplier_name,
               SUM(CASE WHEN l.account LIKE '331%' THEN l.credit - l.debit ELSE 0 END) AS payable
        FROM suppliers s
        LEFT JOIN journal_entries e ON s.id = e.supplier_id
        LEFT JOIN journal_lines l ON e.id = l.entry_id
        GROUP BY s.id
        HAVING payable <> 0
    '''
    return pd.read_sql(sql, conn)


def get_supplier_debt_details(conn, supplier_id):
    """List transactions affecting account 331 for one supplier."""
    sql = """
        SELECT e.date, e.ref, e.note, l.account, l.debit, l.credit
        FROM journal_entries e
        JOIN journal_lines l ON e.id = l.entry_id
        WHERE e.supplier_id = ? AND l.account LIKE '331%'
        ORDER BY e.date DESC, e.id DESC
    """
    return pd.read_sql(sql, conn, params=(supplier_id,))
