import sys
import os
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add project root to sys.path
sys.path.append(r"C:\Users\AMD\.gemini\antigravity\scratch\vn-sme-ledger")
os.chdir(r"C:\Users\AMD\.gemini\antigravity\scratch\vn-sme-ledger")

import main_qt

def capture_all():
    app = QApplication(sys.argv)
    window = main_qt.VnSmeLedgerApp()
    window.show()

    out_dir = r"C:\Users\AMD\.gemini\antigravity\brain\8888d9a5-06b6-46b4-bec4-516506bee1c7"
    os.makedirs(out_dir, exist_ok=True)

    tab_widget = window.tabs
    count = tab_widget.count()

    def do_capture(idx):
        if idx >= count:
            print("Completed capturing all PyQt6 tabs!")
            window.close()
            app.quit()
            return

        tab_widget.setCurrentIndex(idx)
        # Process events to let UI redraw
        app.processEvents()

        # Brief delay to render
        def save_tab():
            try:
                screen = QApplication.primaryScreen()
                pixmap = screen.grabWindow(window.winId())
                tab_title = tab_widget.tabText(idx)
                safe_title = "".join([c if c.isalnum() else "_" for c in tab_title])
                out_path = os.path.join(out_dir, f"tab_qt_{idx}_{safe_title}.png")
                pixmap.save(out_path)
                print(f"Captured tab {idx} ({tab_title}) -> {out_path}")
            except Exception as e:
                print(f"Error capturing tab {idx}: {e}")

            # Schedule next tab
            QTimer.singleShot(1000, lambda: do_capture(idx + 1))

        QTimer.singleShot(500, save_tab)

    QTimer.singleShot(1000, lambda: do_capture(0))
    sys.exit(app.exec())

if __name__ == "__main__":
    capture_all()
