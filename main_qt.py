"""
VN SME Ledger — PyQt6 Main Application
Modern, professional accounting software for Vietnamese SMEs.
"""
import sys
import os
import json

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QMessageBox, QStatusBar, QLabel
)
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor
from PyQt6.QtCore import Qt

# Backend imports
import config
import db
import utils as utils_mod

# i18n
from utils.i18n import set_locale, tr

# UI tab imports (imported lazily where possible)
from ui.home_tab import HomeTab
from ui.settings_tab import SettingsTab

# ---------- QSS STYLESHEET (Modern Dark-Accent Theme) ----------
STYLESHEET = """
QMainWindow {
    background-color: #F5F7FA;
}

QTabWidget::pane {
    border: 1px solid #E0E0E0;
    background: #FFFFFF;
    border-radius: 4px;
}

QTabBar::tab {
    background: #E8EDF2;
    color: #555555;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    min-width: 90px;
}

QTabBar::tab:selected {
    background: #1565C0;
    color: #FFFFFF;
    font-weight: 700;
}

QTabBar::tab:hover:!selected {
    background: #BBDEFB;
    color: #0D47A1;
}

QPushButton {
    background-color: #1565C0;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1976D2;
}

QPushButton:pressed {
    background-color: #0D47A1;
}

QPushButton[cssClass="success"] {
    background-color: #388E3C;
}
QPushButton[cssClass="success"]:hover {
    background-color: #43A047;
}

QPushButton[cssClass="danger"] {
    background-color: #C62828;
}
QPushButton[cssClass="danger"]:hover {
    background-color: #D32F2F;
}

QPushButton[cssClass="secondary"] {
    background-color: #546E7A;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    border: 1px solid #BDBDBD;
    border-radius: 4px;
    padding: 6px 10px;
    background: #FFFFFF;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus {
    border: 2px solid #1565C0;
}

QTableWidget, QTableView, QTreeView {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    gridline-color: #EEEEEE;
    font-size: 12px;
    selection-background-color: #BBDEFB;
    selection-color: #0D47A1;
    alternate-background-color: #F8F9FA;
}

QHeaderView::section {
    background-color: #1565C0;
    color: white;
    padding: 8px;
    border: none;
    font-weight: 600;
    font-size: 12px;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    background: #FAFBFC;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #1565C0;
}

QLabel {
    font-size: 13px;
    color: #333333;
}

QStatusBar {
    background: #1565C0;
    color: white;
    font-size: 12px;
}

QScrollBar:vertical {
    border: none;
    background: #F0F0F0;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #BDBDBD;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #9E9E9E;
}
"""


class VnSmeLedgerApp(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Load settings
        self.settings = self._load_settings()

        # Init i18n
        locale_map = {"vi": "vi_VN", "en": "en_US"}
        locale = locale_map.get(self.settings.get("language", "vi"), "vi_VN")
        set_locale(locale)

        # Init backend
        self.lbl = config.load_language(self.settings.get("language", "vi"))
        self.db_conn = db.init_db()
        self.demo_active = False

        # Window setup
        self.setWindowTitle(tr("app_title", "VN SME Ledger — Phần mềm Kế toán Doanh nghiệp"))
        self.resize(1280, 860)
        self._set_icon()

        # Central tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.setCentralWidget(self.tabs)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(tr("support_footer", "VN SME Ledger 2026"), 0)

        # Build all tabs
        self._init_tabs()

    def _set_icon(self):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _load_settings(self):
        settings_path = os.path.join("db", "settings.json")
        s = config.DEFAULT_SETTINGS.copy()
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    s.update(json.load(f))
            except Exception:
                pass
        return s

    def _init_tabs(self):
        """Build and add all application tabs."""
        # 1. Home
        self.home_tab = HomeTab(self)
        self.tabs.addTab(self.home_tab, tr("tab_home", "Trang chủ"))

        # 2. Documents (Chứng từ)
        try:
            from ui.documents_tab import DocumentsTab
            self.documents_tab = DocumentsTab(self)
            self.tabs.addTab(self.documents_tab, tr("tab_documents", "Chứng từ"))
        except ImportError:
            self.tabs.addTab(QWidget(), tr("tab_documents", "Chứng từ"))

        # 3. Directories (Danh mục)
        try:
            from ui.directories_tab import DirectoriesTab
            self.directories_tab = DirectoriesTab(self)
            self.tabs.addTab(self.directories_tab, tr("tab_directories", "Danh mục"))
        except ImportError:
            self.tabs.addTab(QWidget(), tr("tab_directories", "Danh mục"))

        # 4. Invoices (Hóa đơn)
        try:
            from ui.invoices_tab import InvoicesTab
            self.invoices_tab = InvoicesTab(self)
            self.tabs.addTab(self.invoices_tab, tr("tab_invoices", "Hóa đơn"))
        except ImportError:
            self.tabs.addTab(QWidget(), tr("tab_invoices", "Hóa đơn"))

        # 5-10. Remaining tabs (will be migrated next)
        for key, fallback in [
            ("tab_ledger", "Sổ cái"),
            ("tab_reports", "Báo cáo"),
            ("tab_analytics", "Phân tích"),
            ("tab_hr", "Nhân sự"),
            ("tab_tools", "Công cụ"),
        ]:
            self.tabs.addTab(QWidget(), tr(key, fallback))

        # 11. Settings
        self.settings_tab = SettingsTab(self)
        self.tabs.addTab(self.settings_tab, tr("tab_settings", "Cài đặt"))

    def refresh_all(self):
        """Refresh all tabs that support it — called after posting entries, invoices, etc."""
        if hasattr(self, 'home_tab') and hasattr(self.home_tab, 'refresh'):
            self.home_tab.refresh()
        if hasattr(self, 'documents_tab') and hasattr(self.documents_tab, 'refresh_ledger'):
            self.documents_tab.refresh_ledger()
        if hasattr(self, 'directories_tab') and hasattr(self.directories_tab, 'refresh_all'):
            self.directories_tab.refresh_all()
        if hasattr(self, 'invoices_tab') and hasattr(self.invoices_tab, 'refresh'):
            self.invoices_tab.refresh()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    # Set global font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = VnSmeLedgerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
