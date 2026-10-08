"""Stable Tk startup smoke check, safe both as a script and under pytest."""

import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch

import db
import main


def run_startup_smoke(interactive=False) -> int:
    original_cwd = os.getcwd()
    app = None
    temp_dir = tempfile.TemporaryDirectory(prefix="vn_sme_startup_")
    try:
        os.chdir(temp_dir.name)
        isolated_db = str(Path(temp_dir.name) / "data" / "ledger.db")
        original_init_db = db.init_db
        with patch.object(
            db, "init_db", side_effect=lambda _path="data/ledger.db": original_init_db(isolated_db)
        ):
            print("Initializing App in an isolated data directory...")
            app = main.App()
            print("SUCCESS")
            if interactive:
                print("Starting mainloop (Close window to finish test)...")
                app.mainloop()
            else:
                app.destroy()
        return 0
    except Exception:
        print("CRASH!")
        traceback.print_exc()
        return 1
    finally:
        if app is not None and getattr(app, "db", None) is not None:
            try:
                app.db.close()
            except Exception:
                pass
        os.chdir(original_cwd)
        temp_dir.cleanup()


def test_startup_smoke():
    assert run_startup_smoke() == 0


if __name__ == "__main__":
    raise SystemExit(run_startup_smoke(interactive="--interactive" in sys.argv))
