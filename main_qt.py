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
        self.lbl = config.get_labels(self.settings)
        self.db_conn = db.init_db()
        self.demo_active = False

        # Window setup
        self.setWindowTitle(tr("app_title", f"{config.APP_DISPLAY_NAME} — Phần mềm Kế toán Doanh nghiệp"))
        self.resize(1280, 860)
        self._set_icon()

        # Central tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setUsesScrollButtons(True)
        self.tabs.tabBar().setExpanding(False)
        self.setCentralWidget(self.tabs)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(tr("support_footer", "VN SME Ledger 2026"), 0)

        # Build all tabs
        self.tab_indices = {}
        self._init_tabs()

    def _set_icon(self):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _load_settings(self):
        return config.load_settings()

    def _add_tab(self, key, widget, label):
        """Register a tab by semantic key so links survive tab reordering."""
        index = self.tabs.addTab(widget, label)
        self.tab_indices[key] = index
        return index

    def _init_tabs(self):
        """Build and add all application tabs."""
        # 1. Home
        self.home_tab = HomeTab(self)
        self._add_tab("home", self.home_tab, tr("tab_home", "🏠 Trang chủ"))

        # 2. Documents (Chứng từ)
        try:
            from ui.documents_tab import DocumentsTab
            self.documents_tab = DocumentsTab(self)
            self._add_tab("documents", self.documents_tab, tr("tab_documents", "📑 Chứng từ"))
        except Exception as e:
            self._add_tab("documents", self._make_error_tab("Chứng từ", e), tr("tab_documents", "📑 Chứng từ"))

        # 3. Directories (Danh mục)
        try:
            from ui.directories_tab import DirectoriesTab
            self.directories_tab = DirectoriesTab(self)
            self._add_tab("directories", self.directories_tab, tr("tab_directories", "🗂️ Danh mục"))
        except Exception as e:
            self._add_tab("directories", self._make_error_tab("Danh mục", e), tr("tab_directories", "🗂️ Danh mục"))

        # 4. Invoices (Hóa đơn)
        try:
            from ui.invoices_tab import InvoicesTab
            self.invoices_tab = InvoicesTab(self)
            self._add_tab("invoices", self.invoices_tab, tr("tab_invoices", "🧾 Hóa đơn"))
        except Exception as e:
            self._add_tab("invoices", self._make_error_tab("Hóa đơn", e), tr("tab_invoices", "🧾 Hóa đơn"))

        # 5. Ledger (Sổ cái)
        try:
            from ui.ledger_tab import LedgerTab
            self.ledger_tab = LedgerTab(self)
            self._add_tab("ledger", self.ledger_tab, tr("tab_ledger", "🕒 Sổ cái"))
        except Exception as e:
            self._add_tab("ledger", self._make_error_tab("Sổ cái", e), tr("tab_ledger", "🕒 Sổ cái"))

        # 6. Reports (Báo cáo)
        try:
            from ui.reports_tab import ReportsTab
            self.reports_tab = ReportsTab(self)
            self._add_tab("reports", self.reports_tab, tr("tab_reports", "📊 Báo cáo"))
        except Exception as e:
            self._add_tab("reports", self._make_error_tab("Báo cáo", e), tr("tab_reports", "📊 Báo cáo"))

        # 7. Analytics (Phân tích)
        try:
            from ui.analytics_tab import AnalyticsTab
            self.analytics_tab = AnalyticsTab(self)
            self._add_tab("analytics", self.analytics_tab, tr("tab_analytics", "📈 Phân tích"))
        except Exception as e:
            self._add_tab("analytics", self._make_error_tab("Phân tích", e), tr("tab_analytics", "📈 Phân tích"))

        # 8. HR & Payroll
        try:
            from ui.hr_tab import HRTab
            self.hr_tab = HRTab(self)
            self._add_tab("hr", self.hr_tab, tr("tab_hr", "👥 Nhân sự"))
        except Exception as e:
            self._add_tab("hr", self._make_error_tab("Nhân sự", e), tr("tab_hr", "👥 Nhân sự"))

        # 9. Tools & Legal
        try:
            from ui.tools_tab import ToolsTab
            self.tools_tab = ToolsTab(self)
            self._add_tab("tools", self.tools_tab, tr("tab_tools", "🛠️ Công cụ"))
        except Exception as e:
            self._add_tab("tools", self._make_error_tab("Công cụ", e), tr("tab_tools", "🛠️ Công cụ"))

        # 10. Settings
        self.settings_tab = SettingsTab(self)
        self._add_tab("settings", self.settings_tab, tr("tab_settings", "⚙️ Cài đặt"))

    def go_to_tab(self, key):
        """Open a top-level workflow area by stable semantic key."""
        index = self.tab_indices.get(key)
        if index is None:
            return False
        self.tabs.setCurrentIndex(index)
        return True

    def open_payroll(self):
        """Open the payroll sub-tab without relying on top-level tab numbers."""
        if not self.go_to_tab("hr"):
            return False
        sub_tabs = getattr(getattr(self, "hr_tab", None), "sub_tabs", None)
        if sub_tabs is not None and sub_tabs.count() >= 3:
            sub_tabs.setCurrentIndex(2)
        return True

    def open_ai_assistant(self):
        """Open the opt-in AI/online tools area."""
        if not self.go_to_tab("tools"):
            return False
        sub_tabs = getattr(getattr(self, "tools_tab", None), "sub_tabs", None)
        if sub_tabs is not None and sub_tabs.count() >= 4:
            sub_tabs.setCurrentIndex(3)
        return True

    @staticmethod
    def _make_error_tab(name: str, error: Exception) -> QWidget:
        """Create a clean error placeholder for a tab that failed to load."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading = QLabel(f"⚠️ Không thể tải {name}")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setStyleSheet("font-size: 16px; font-weight: 700; color: #C62828;")
        detail = QLabel(f"Lỗi: {error}")
        detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail.setWordWrap(True)
        detail.setStyleSheet("font-size: 12px; color: #666; max-width: 500px;")
        layout.addWidget(heading)
        layout.addWidget(detail)
        return widget

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
        if hasattr(self, 'ledger_tab') and hasattr(self.ledger_tab, 'refresh_ledger'):
            self.ledger_tab.refresh_ledger()
        if hasattr(self, 'reports_tab') and hasattr(self.reports_tab, 'refresh'):
            self.reports_tab.refresh()
        if hasattr(self, 'analytics_tab') and hasattr(self.analytics_tab, 'refresh'):
            self.analytics_tab.refresh()
        if hasattr(self, 'hr_tab') and hasattr(self.hr_tab, 'refresh'):
            self.hr_tab.refresh()
        if hasattr(self, 'tools_tab') and hasattr(self.tools_tab, 'refresh'):
            self.tools_tab.refresh()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Force clean, consistent bright/light theme palette (ignores OS dark mode)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#F8FAFC"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#1E293B"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#F1F5F9"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#1E293B"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#1E293B"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#F1F5F9"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#1E293B"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#2563EB"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#DBEAFE"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#1E40AF"))
    app.setPalette(palette)
    
    app.setStyleSheet(STYLESHEET)

    # Set global font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = VnSmeLedgerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
