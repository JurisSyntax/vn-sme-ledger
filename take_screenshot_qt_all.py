"""Capture each PyQt6 page without reading or writing the real user ledger."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def capture_all(output_dir: Path | None = None) -> int:
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication

    sys.path.insert(0, str(PROJECT_ROOT))
    output_dir = Path(output_dir or Path(tempfile.gettempdir()) / "VN_SME_Ledger_QA_Screenshots").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    original_cwd = os.getcwd()
    temp_dir = tempfile.TemporaryDirectory(prefix="vn_sme_qt_capture_")
    window = None
    try:
        os.chdir(temp_dir.name)
        import main_qt

        app = QApplication.instance() or QApplication(sys.argv[:1])
        window = main_qt.VnSmeLedgerApp()
        window.show()
        tabs = window.tabs

        def capture_page(index: int) -> None:
            if index >= tabs.count():
                print(f"Captured {tabs.count()} pages to {output_dir}")
                window.close()
                app.quit()
                return

            tabs.setCurrentIndex(index)
            app.processEvents()

            def save_page() -> None:
                screen = QApplication.primaryScreen()
                if screen is not None:
                    title = tabs.tabText(index) or f"page_{index}"
                    safe_title = "".join(char if char.isalnum() else "_" for char in title)
                    path = output_dir / f"page_{index}_{safe_title}.png"
                    if screen.grabWindow(window.winId()).save(str(path)):
                        print(f"Captured page {index}: {path}")
                QTimer.singleShot(250, lambda: capture_page(index + 1))

            QTimer.singleShot(400, save_page)

        QTimer.singleShot(700, lambda: capture_page(0))
        exit_code = app.exec()
        window.close()
        app.processEvents()
        return exit_code
    finally:
        if window is not None:
            try:
                window.close()
            except Exception:
                pass
        os.chdir(original_cwd)
        temp_dir.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="Screenshot output directory (default: system temp)")
    raise SystemExit(capture_all(parser.parse_args().output_dir))
