import datetime
import os
import tempfile
from pathlib import Path

import db
from presets_loader import get_vas_rules
from vas_mapper import VAS_RULES, auto_vas_lines


def _remove_sqlite_files(path):
    base = Path(path)
    for candidate in [base, Path(str(base) + "-wal"), Path(str(base) + "-shm")]:
        if candidate.exists():
            candidate.unlink()


def run_backend_smoke(db_path=None, verbose=True):
    if db_path is None:
        tmp_dir = tempfile.mkdtemp(prefix="vn_sme_ledger_")
        db_path = os.path.join(tmp_dir, "test_ledger.db")

    _remove_sqlite_files(db_path)

    if verbose:
        print("Starting backend test...")
    conn = db.init_db(db_path)
    try:
        VAS_RULES.update(get_vas_rules("photocopy_print"))
        if verbose:
            print("Loaded preset: photocopy_print")

        tx_type = "Sales"
        amount = 1100000
        lines = auto_vas_lines(tx_type, amount, vat_rate=0.10)
        ref = f"SAL-{datetime.datetime.now():%y%m%d}"
        eid = db.post_entry(conn, datetime.date.today().strftime("%Y-%m-%d"), ref, "Test Sale", lines, tx_type)
        if verbose:
            print(f"Posted {tx_type} transaction. Entry ID: {eid}")

        df = db.get_flat_df(conn)
        if verbose:
            print(f"Total journal lines in DB: {len(df)}")
        passed = len(df) == 3
        if verbose:
            print("Backend test PASSED." if passed else "Backend test FAILED.")
        return passed
    finally:
        conn.close()
        _remove_sqlite_files(db_path)


def test_backend_smoke():
    assert run_backend_smoke(verbose=False)


if __name__ == "__main__":
    raise SystemExit(0 if run_backend_smoke() else 1)

