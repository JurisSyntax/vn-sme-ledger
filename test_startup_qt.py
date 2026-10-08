"""PyQt6 startup smoke check, safe both as a script and under pytest."""

import os
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch

import db


def run_qt_startup_smoke() -> int:
    original_cwd = os.getcwd()
    window = None
    temp_dir = tempfile.TemporaryDirectory(prefix="vn_sme_qt_startup_")
    try:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication
        import main_qt

        os.chdir(temp_dir.name)
        app = QApplication.instance() or QApplication([])
        original_init_db = db.init_db
        isolated_db = str(Path(temp_dir.name) / "data" / "ledger.db")
        with patch.object(
            db, "init_db", side_effect=lambda _path="data/ledger.db": original_init_db(isolated_db)
        ):
            print("Instantiating VnSmeLedgerApp with an isolated database...")
            window = main_qt.VnSmeLedgerApp()
            window.show()
            app.processEvents()
            print("SUCCESS")
            window.close()
        return 0
    except Exception:
        print("CRASH!")
        traceback.print_exc()
        return 1
    finally:
        if window is not None:
            try:
                window.close()
            except Exception:
                pass
        os.chdir(original_cwd)
        temp_dir.cleanup()


if __name__ == "__main__":
    raise SystemExit(run_qt_startup_smoke())
