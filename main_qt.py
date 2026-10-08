"""
VN SME Ledger — PyQt6 Main Application
Modern, professional accounting software for Vietnamese SMEs.
"""
import sys
import os
import json
import html
import unicodedata
import ctypes

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QMessageBox, QStatusBar, QLabel, QScrollArea,
    QSizePolicy, QLineEdit, QStyle, QDialog, QTextBrowser, QDialogButtonBox
)
from PyQt6.QtGui import QIcon, QFont, QFontDatabase, QPalette, QColor
from PyQt6.QtCore import Qt, QSize, QTimer

# Backend imports
import config
import db
import utils as utils_mod

# i18n
from utils.i18n import set_locale, tr
from utils.ui_fonts import font_paths

# UI tab imports (imported lazily where possible)
from ui.home_tab import HomeTab
from ui.qt_motion import fade_widget
from ui.autocomplete import install_line_edit_completer





# ---------- QSS STYLESHEET (Modern Dark-Accent Theme) ----------
STYLESHEET = """
QMainWindow {
    background-color: #F4F6F8;
}

QTabWidget::pane {
    border: none;
    background: #F4F6F8;
}

QTabBar::tab {
    background: #E8EDF2;
    color: #555555;
    padding: 8px 12px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    min-width: 0;
}

QTabBar::tab:selected {
    background: #1F5B82;
    color: #FFFFFF;
    font-weight: 700;
}

QTabBar::tab:hover:!selected {
    background: #E7F0F5;
    color: #164A6B;
}

QPushButton {
    background-color: #1F5B82;
    color: white;
    border: none;
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 600;
    min-height: 38px;
}

QPushButton:hover {
    background-color: #2B6F98;
}

QPushButton:pressed {
    background-color: #164A6B;
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

QPushButton[compact="true"] {
    min-height: 32px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton[compact="true"]:hover {
    background-color: #E7F0F5;
    color: #164A6B;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    border: 1px solid #C9D5DF;
    border-radius: 4px;
    padding: 6px 10px;
    background: #FFFFFF;
    font-size: 14px;
    min-height: 32px;
}

QLineEdit:focus, QComboBox:focus {
    border: 2px solid #2B6F98;
}

QTableWidget, QTableView, QTreeView {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    gridline-color: #EEEEEE;
    font-size: 13px;
    selection-background-color: #D8EAF0;
    selection-color: #164A6B;
    alternate-background-color: #F8F9FA;
}

QHeaderView::section {
    background-color: #1F5B82;
    color: white;
    padding: 9px;
    border: none;
    font-weight: 600;
    font-size: 13px;
}

QGroupBox {
    font-size: 14px;
    font-weight: bold;
    border: 1px solid #D8E1EA;
    border-radius: 6px;
    margin-top: 18px;
    padding: 12px 10px 10px 10px;
    background: #FFFFFF;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
    color: #1F5B82;
    font-size: 13px;
    background: #FFFFFF;
}

QLabel {
    font-size: 14px;
    color: #333333;
    padding: 0;
    min-height: 0;
}

#appShell {
    background: #F4F6F8;
}

#contentShell {
    background: #F4F6F8;
}

#contentTopBar {
    background: #FFFFFF;
    border-bottom: 1px solid #D8E1EA;
}

#currentPageTitle {
    color: #102A43;
    font-size: 17px;
    font-weight: 800;
}

#currentPageContext {
    color: #64748B;
    font-size: 11px;
}

#onlineStatus {
    color: #166534;
    background: #ECFDF3;
    border: 1px solid #BBF7D0;
    border-radius: 12px;
    padding: 5px 10px;
    font-size: 11px;
    font-weight: 700;
}

#contentHelp {
    min-height: 32px;
    padding: 6px 12px;
    background: #E7F0F5;
    color: #164A6B;
    font-size: 12px;
}

#dashboardHeader {
    background: transparent;
}

#dashboardEyebrow {
    color: #2B6F98;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0;
}

#dashboardHeaderTitle {
    color: #102A43;
    font-size: 22px;
    font-weight: 800;
}

#dashboardHeaderSubtitle {
    color: #64748B;
    font-size: 11px;
}

#dashboardKpiStrip, #dashboardActionSurface {
    background: transparent;
}

#dashboardSurface {
    background: #FFFFFF;
    border: 1px solid #D8E1EA;
    border-radius: 7px;
}

#dashboardPane {
    background: #FFFFFF;
    border: 1px solid #D8E1EA;
    border-radius: 7px;
}

#dashboardSectionTitle {
    color: #102A43;
    font-size: 13px;
    font-weight: 800;
}

#dashboardSectionNote {
    color: #64748B;
    font-size: 10px;
}

#pageScroll {
    border: none;
    background: #F4F6F8;
}

#appSidebar {
    background: #FBFCFD;
    border-right: 1px solid #D9E2EC;
}

#navBrand {
    color: #102A43;
    font-size: 18px;
    font-weight: 800;
    padding: 2px 4px;
}

#navVersion {
    color: #64748B;
    font-size: 12px;
    padding: 0 4px 12px 4px;
}

#navSection {
    color: #94A3B8;
    font-size: 11px;
    font-weight: 700;
    padding: 12px 6px 5px 6px;
}

#navButton {
    background: transparent;
    color: #334155;
    border: none;
    border-radius: 5px;
    text-align: left;
    padding: 8px 10px;
    min-height: 40px;
    font-size: 14px;
    font-weight: 600;
}

#navButton:hover {
    background: #E7F0F5;
    color: #164A6B;
}

#navButton:checked {
    background: #1F5B82;
    color: #FFFFFF;
}

#navButton:focus {
    border: 2px solid #164A6B;
}

#navSearch {
    border: 1px solid #B8C7D9;
    background: #F8FAFC;
    color: #1E293B;
    font-size: 13px;
}

#navHelp {
    background: #E7F0F5;
    color: #164A6B;
    text-align: left;
}

QStatusBar {
    background: #102A43;
    color: white;
    font-size: 13px;
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

QScrollArea#pageScroll {
    padding: 0;
}

QScrollArea#pageScroll > QWidget > QWidget {
    background: #F5F7FA;
}

QTabWidget > QWidget {
    background: #F4F6F8;
}

QFrame#legalSourceStrip, QFrame#legalActionStrip {
    background: #FFFFFF;
    border: 1px solid #D9E2EC;
    border-radius: 6px;
}

QLabel#legalSectionLabel {
    color: #475569;
    font-size: 12px;
    font-weight: 700;
}
"""


def _load_application_font() -> str:
    """Load the bundled Be Vietnam font without installing it system-wide."""
    family = utils_mod.FONT_FAMILY
    for path in font_paths(utils_mod.get_resource_path):
        font_id = QFontDatabase.addApplicationFont(path)
        if font_id >= 0:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                family = families[0]
    app = QApplication.instance()
    if app is not None:
        app.setFont(QFont(family, 10))
    return family


def _set_windows_app_identity() -> None:
    """Set the taskbar identity before any top-level window is created."""
    if os.name == "nt":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "VN.SME.Ledger.Desktop"
            )
        except (AttributeError, OSError):
            pass


class VnSmeLedgerApp(QMainWindow):
    """Main application window."""

    def __init__(self):
        _set_windows_app_identity()
        super().__init__()

        self.ui_font_family = _load_application_font()

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
        self._page_animation = None
        # Let the first window paint before importing Matplotlib-heavy chart
        # backends. Standalone tab consumers without this flag keep the old
        # synchronous canvas contract.
        self.defer_heavy_charts = True

        # Window setup
        self.setWindowTitle(tr("app_title", f"{config.APP_DISPLAY_NAME} — Phần mềm Kế toán Doanh nghiệp"))
        self.resize(1280, 860)
        self.setMinimumSize(900, 600)
        self._set_icon()

        # Central tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setUsesScrollButtons(False)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.tabBar().hide()

        # Use a compact semantic navigation rail instead of squeezing ten
        # long Vietnamese tab labels into a single horizontal strip.
        shell = QWidget()
        shell.setObjectName("appShell")
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("appSidebar")
        self.sidebar.setFixedWidth(230)
        self.sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 12)
        sidebar_layout.setSpacing(4)

        brand = QLabel("VN SME Ledger")
        brand.setObjectName("navBrand")
        sidebar_layout.addWidget(brand)
        version = QLabel(config.APP_VERSION)
        version.setObjectName("navVersion")
        sidebar_layout.addWidget(version)

        section = QLabel("CHỌN CHỨC NĂNG")
        section.setObjectName("navSection")
        sidebar_layout.addWidget(section)

        self.nav_search = QLineEdit()
        self.nav_search.setObjectName("navSearch")
        self.nav_search.setPlaceholderText("Tìm tính năng...")
        self.nav_search.setToolTip("Gõ tên chức năng, nghiệp vụ hoặc thuật ngữ rồi nhấn Enter để mở")
        self.nav_search.textChanged.connect(self._filter_navigation)
        self.nav_search.returnPressed.connect(self._navigate_from_search)
        sidebar_layout.addWidget(self.nav_search)

        nav_container = QWidget()
        self._nav_layout = QVBoxLayout(nav_container)
        self._nav_layout.setSpacing(3)
        self._nav_layout.setContentsMargins(0, 0, 0, 0)
        self._nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.nav_empty = QLabel("Không tìm thấy chức năng")
        self.nav_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nav_empty.setStyleSheet("color: #64748B; font-size: 12px; padding: 8px;")
        self.nav_empty.setVisible(False)
        self.nav_scroll = QScrollArea()
        self.nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.nav_scroll.setWidgetResizable(True)
        self.nav_scroll.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.nav_scroll.setWidget(nav_container)
        sidebar_layout.addWidget(self.nav_scroll, 1)

        self.nav_playbook = QPushButton("Lộ trình kinh doanh")
        self.nav_playbook.setObjectName("navPlaybook")
        self.nav_playbook.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView))
        self.nav_playbook.setIconSize(QSize(20, 20))
        self.nav_playbook.setToolTip("Xem các bước vận hành doanh nghiệp tại Việt Nam")
        self.nav_playbook.clicked.connect(self._open_business_playbook)
        sidebar_layout.addWidget(self.nav_playbook)

        self.nav_help = QPushButton("Trợ giúp")
        self.nav_help.setObjectName("navHelp")
        self.nav_help.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogHelpButton))
        self.nav_help.setIconSize(QSize(20, 20))
        self.nav_help.setToolTip("Mở trợ giúp theo trang đang mở")
        self.nav_help.clicked.connect(self._open_help)
        sidebar_layout.addWidget(self.nav_help)

        self.nav_policy = QLabel("Offline mặc định · Online khi bật")
        self.nav_policy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nav_policy.setStyleSheet("color: #64748B; font-size: 11px; padding-top: 5px;")
        sidebar_layout.addWidget(self.nav_policy)

        self.author_credit = QLabel(
            "Tác giả: Du Quốc Hoàng Kim\n"
            '<a href="https://github.com/JurisSyntax">GitHub: JurisSyntax</a>'
        )
        self.author_credit.setOpenExternalLinks(True)
        self.author_credit.setTextFormat(Qt.TextFormat.RichText)
        self.author_credit.setWordWrap(True)
        self.author_credit.setStyleSheet("color: #64748B; font-size: 10px; padding-top: 4px;")
        sidebar_layout.addWidget(self.author_credit)

        self._nav_buttons = {}
        self._nav_labels = {}

        content_shell = QWidget()
        content_shell.setObjectName("contentShell")
        content_layout = QVBoxLayout(content_shell)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.content_top_bar = QFrame()
        self.content_top_bar.setObjectName("contentTopBar")
        self.content_top_bar.setMinimumHeight(58)
        top_bar_layout = QHBoxLayout(self.content_top_bar)
        top_bar_layout.setContentsMargins(18, 10, 18, 10)
        top_bar_layout.setSpacing(10)

        page_heading = QVBoxLayout()
        page_heading.setSpacing(1)
        self.current_page_title = QLabel("Trang chủ")
        self.current_page_title.setObjectName("currentPageTitle")
        self.current_page_context = QLabel("Tổng quan hoạt động và việc cần xử lý")
        self.current_page_context.setObjectName("currentPageContext")
        page_heading.addWidget(self.current_page_title)
        page_heading.addWidget(self.current_page_context)
        top_bar_layout.addLayout(page_heading)
        top_bar_layout.addStretch()

        self.online_status = QLabel("Offline mặc định · Online khi bật")
        self.online_status.setObjectName("onlineStatus")
        self.online_status.setToolTip(
            "Dữ liệu chỉ gọi mạng khi người dùng bật đúng tính năng trong Cài đặt."
        )
        top_bar_layout.addWidget(self.online_status)
        content_help = QPushButton("Trợ giúp")
        content_help.setObjectName("contentHelp")
        content_help.setToolTip("Mở hướng dẫn cụ thể cho trang đang mở")
        content_help.clicked.connect(self._open_help)
        top_bar_layout.addWidget(content_help)

        content_layout.addWidget(self.content_top_bar)
        content_layout.addWidget(self.tabs, 1)
        shell_layout.addWidget(self.sidebar)
        shell_layout.addWidget(content_shell, 1)
        self.setCentralWidget(shell)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(tr("support_footer", "VN SME Ledger 2026"), 0)

        # Build all tabs
        self.tab_indices = {}
        self._tab_pages = {}
        self._lazy_tabs = {}
        self._init_tabs()
        self.tabs.currentChanged.connect(self._ensure_tab_loaded)
        self._setup_navigation_autocomplete()
        self._normalize_legacy_styles()
        self.tabs.currentChanged.connect(self._sync_page_header)
        self._sync_page_header(self.tabs.currentIndex())

    def _set_icon(self):
        # Use the bundled resource path so one-file PyInstaller launches also
        # resolve the icon from the temporary extraction directory.
        icon_path = utils_mod.get_resource_path("logo.ico")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)
            application = QApplication.instance()
            if application is not None:
                application.setWindowIcon(icon)

    def _load_settings(self):
        return config.load_settings()

    def _add_tab(self, key, widget, label):
        """Register a tab by semantic key so links survive tab reordering."""
        # Every page gets a real viewport. Dense accounting screens must remain
        # usable when the window is restored, scaled to 125/150%, or opened on
        # a smaller laptop display.
        page = QScrollArea()
        page.setObjectName("pageScroll")
        page.setWidgetResizable(True)
        page.setFrameShape(QFrame.Shape.NoFrame)
        page.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Let the viewport decide. Forms are kept responsive; genuinely wide
        # accounting tables retain a compact horizontal scrollbar instead of
        # clipping data at 125/150% Windows scaling.
        page.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        page.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        widget.setMinimumSize(0, 0)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        page.setWidget(widget)
        index = self.tabs.addTab(page, label)
        self.tab_indices[key] = index
        self._tab_pages[key] = page

        compact_labels = {
            "home": "Trang chủ",
            "documents": "Chứng từ",
            "directories": "Danh mục",
            "invoices": "Hóa đơn",
            "ledger": "Sổ cái",
            "ar_ap": "Công nợ",
            "reports": "Báo cáo",
            "analytics": "Phân tích",
            "hr": "Nhân sự",
            "tools": "Công cụ",
            "settings": "Cài đặt",
        }
        nav_button = QPushButton(compact_labels.get(key, label))
        nav_button.setObjectName("navButton")
        nav_button.setCheckable(True)
        nav_button.setMinimumHeight(40)
        nav_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        nav_button.setToolTip(label)
        icon_map = {
            "home": QStyle.StandardPixmap.SP_DesktopIcon,
            "documents": QStyle.StandardPixmap.SP_FileIcon,
            "directories": QStyle.StandardPixmap.SP_DirIcon,
            "invoices": QStyle.StandardPixmap.SP_FileDialogDetailedView,
            "ledger": QStyle.StandardPixmap.SP_FileDialogListView,
            "ar_ap": QStyle.StandardPixmap.SP_DialogApplyButton,
            "reports": QStyle.StandardPixmap.SP_FileDialogInfoView,
            "analytics": QStyle.StandardPixmap.SP_FileDialogContentsView,
            "hr": QStyle.StandardPixmap.SP_DirHomeIcon,
            "tools": QStyle.StandardPixmap.SP_ComputerIcon,
            "settings": QStyle.StandardPixmap.SP_FileDialogDetailedView,
        }
        if key in icon_map:
            nav_button.setIcon(self.style().standardIcon(icon_map[key]))
            nav_button.setIconSize(QSize(20, 20))
        nav_button.clicked.connect(lambda checked=False, i=index: self.tabs.setCurrentIndex(i))
        self._nav_layout.addWidget(nav_button)
        self._nav_buttons[key] = nav_button
        self._nav_labels[key] = self._fold_search(f"{compact_labels.get(key, label)} {label}")
        return index

    def _add_lazy_tab(self, key, label, attr_name, factory):
        """Register a real navigation page and defer its costly construction."""
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message = QLabel(f"{label} sẽ được tải khi mở.")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet("color: #64748B; font-size: 13px;")
        layout.addWidget(message)
        self._lazy_tabs[key] = (attr_name, factory, label)
        self._add_tab(key, placeholder, label)

    def _ensure_tab_loaded(self, index):
        key = next((name for name, page_index in self.tab_indices.items() if page_index == index), None)
        pending = self._lazy_tabs.pop(key, None)
        if pending is None:
            return

        attr_name, factory, label = pending
        try:
            widget = factory()
        except Exception as exc:
            widget = self._make_error_tab(label, exc)
        setattr(self, attr_name, widget)
        page = self._tab_pages[key]
        previous = page.takeWidget()
        page.setWidget(widget)
        if previous is not None:
            previous.deleteLater()
        self._normalize_legacy_styles(widget)

    def _init_tabs(self):
        """Build the dashboard shell and register other pages for lazy loading."""
        # 1. Home
        self.home_tab = HomeTab(self)
        self._add_tab("home", self.home_tab, tr("tab_home", "Trang chủ"))

        # 2. Documents (Chứng từ)
        def build_documents():
            from ui.documents_tab import DocumentsTab
            return DocumentsTab(self)
        self._add_lazy_tab("documents", tr("tab_documents", "Chứng từ"), "documents_tab", build_documents)

        # 3. Directories (Danh mục)
        def build_directories():
            from ui.directories_tab import DirectoriesTab
            return DirectoriesTab(self)
        self._add_lazy_tab("directories", tr("tab_directories", "Danh mục"), "directories_tab", build_directories)

        # 4. Invoices (Hóa đơn)
        def build_invoices():
            from ui.invoices_tab import InvoicesTab
            return InvoicesTab(self)
        self._add_lazy_tab("invoices", tr("tab_invoices", "Hóa đơn"), "invoices_tab", build_invoices)

        # 5. Ledger (Sổ cái)
        def build_ledger():
            from ui.ledger_tab import LedgerTab
            return LedgerTab(self)
        self._add_lazy_tab("ledger", tr("tab_ledger", "Sổ cái"), "ledger_tab", build_ledger)

        # 5.5 AR/AP (Công nợ)
        def build_ar_ap():
            from ui.ar_ap_tab import ArApTab
            return ArApTab(self)
        self._add_lazy_tab("ar_ap", tr("tab_ar_ap", "Công nợ"), "ar_ap_tab", build_ar_ap)

        # 6. Reports (Báo cáo)
        def build_reports():
            from ui.reports_tab import ReportsTab
            return ReportsTab(self)
        self._add_lazy_tab("reports", tr("tab_reports", "Báo cáo"), "reports_tab", build_reports)

        # 7. Analytics (Phân tích)
        def build_analytics():
            from ui.analytics_tab import AnalyticsTab
            return AnalyticsTab(self)
        self._add_lazy_tab("analytics", tr("tab_analytics", "Phân tích"), "analytics_tab", build_analytics)

        # 8. HR & Payroll
        def build_hr():
            from ui.hr_tab import HRTab
            return HRTab(self)
        self._add_lazy_tab("hr", tr("tab_hr", "Nhân sự"), "hr_tab", build_hr)

        # 9. Tools & Legal
        def build_tools():
            from ui.tools_tab import ToolsTab
            return ToolsTab(self)
        self._add_lazy_tab("tools", tr("tab_tools", "Công cụ"), "tools_tab", build_tools)

        # 10. Settings
        def build_settings():
            from ui.settings_tab import SettingsTab
            return SettingsTab(self)
        self._add_lazy_tab("settings", tr("tab_settings", "Cài đặt"), "settings_tab", build_settings)
        self._nav_layout.addWidget(self.nav_empty)
        self.tabs.currentChanged.connect(self._sync_nav)
        self._sync_nav(self.tabs.currentIndex())

    def _sync_nav(self, index):
        """Keep the sidebar selection synchronized with the hidden tab widget."""
        for key, button in self._nav_buttons.items():
            button.setChecked(self.tab_indices.get(key) == index)

    def _sync_page_header(self, index: int):
        """Keep the shared page context synchronized with semantic navigation."""
        key = next(
            (name for name, page_index in self.tab_indices.items() if page_index == index),
            "home",
        )
        metadata = {
            "home": ("Trang chủ", "Tổng quan hoạt động và việc cần xử lý"),
            "documents": ("Chứng từ", "Ghi nhận thu, chi, mua, bán và nhập xuất"),
            "directories": ("Danh mục", "Dữ liệu dùng chung cho toàn bộ nghiệp vụ"),
            "invoices": ("Hóa đơn", "Lập hóa đơn từ khách hàng và hàng hóa đã có"),
            "ledger": ("Sổ cái", "Đối chiếu phát sinh, số dư và bút toán"),
            "ar_ap": ("Công nợ", "Theo dõi phải thu, phải trả và hạn thanh toán"),
            "reports": ("Báo cáo", "Tổng hợp số liệu theo kỳ và mục đích sử dụng"),
            "analytics": ("Phân tích", "Nhìn xu hướng doanh thu, chi phí và lợi nhuận"),
            "hr": ("Nhân sự", "Hồ sơ, chấm công, tăng ca, lương và TNCN"),
            "tools": ("Công cụ", "Thuế, VSIC, văn bản mẫu và kết nối tùy chọn"),
            "settings": ("Cài đặt", "Thông tin doanh nghiệp, thuế và quyền online"),
        }
        title, context = metadata.get(key, metadata["home"])
        self.current_page_title.setText(title)
        self.current_page_context.setText(context)
        for button_key, button in self._nav_buttons.items():
            button.setChecked(button_key == key)

    def _normalize_legacy_styles(self, root=None):
        """Bring older tab-local QSS colors into the current 2026 palette."""
        color_map = {
            "#1565C0": "#1F5B82",
            "#0D47A1": "#164A6B",
            "#1976D2": "#2B6F98",
            "#BBDEFB": "#D8EAF0",
            "#E8F1FB": "#E7F0F5",
        }
        widgets = (
            [root, *root.findChildren(QWidget)]
            if root is not None
            else self.findChildren(QWidget)
        )
        for widget in widgets:
            style = widget.styleSheet()
            if not style:
                continue
            normalized = style
            for old_color, new_color in color_map.items():
                normalized = normalized.replace(old_color, new_color)
            if normalized != style:
                widget.setStyleSheet(normalized)

    def _filter_navigation(self, query: str):
        """Filter navigation by the visible Vietnamese/English page names."""
        needle = self._fold_search(query)
        matches = 0
        for key, button in self._nav_buttons.items():
            visible = not needle or needle in self._nav_labels.get(key, "")
            button.setVisible(visible)
            matches += int(visible)
        self.nav_empty.setVisible(bool(needle) and matches == 0)

    def _setup_navigation_autocomplete(self):
        """Offer route-aware suggestions while preserving the existing filter."""
        routes = [
            ("Trang chủ", "home"), ("Chứng từ", "documents"),
            ("Danh mục", "directories"), ("Khách hàng", "directories"),
            ("Nhà cung cấp", "directories"), ("Kho hàng", "directories"),
            ("Tài sản cố định", "directories"), ("Công cụ", "tools"),
            ("Hóa đơn", "invoices"), ("Đơn hàng", "invoices"),
            ("Nhập hóa đơn XML", "documents"), ("Sổ cái", "ledger"),
            ("Công nợ", "ar_ap"), ("Phải thu phải trả", "ar_ap"),
            ("Báo cáo", "reports"), ("Phân tích", "analytics"),
            ("Nhân sự", "hr"), ("Chấm công", "hr"),
            ("Tính lương", "payroll"), ("Thuế thu nhập cá nhân", "payroll"),
            ("VSIC", "tools"), ("VietQR", "tools"),
            ("Trợ lý AI", "ai"), ("Online opt-in", "ai"),
            ("Cài đặt", "settings"), ("Lộ trình kinh doanh", "playbook"),
            ("Business playbook", "playbook"),
        ]
        self._search_routes = routes
        completer = install_line_edit_completer(self.nav_search, [label for label, _route in routes])
        completer.activated.connect(lambda _text: self._navigate_from_search())

    def _navigate_from_search(self):
        """Open the best matching route when the user confirms a suggestion."""
        query = self.nav_search.text().strip()
        if not query:
            return
        folded = self._fold_search(query)
        selected = None
        for label, route in self._search_routes:
            if self._fold_search(label) == folded:
                selected = route
                break
        if selected is None:
            for label, route in self._search_routes:
                if folded in self._fold_search(label) or self._fold_search(label) in folded:
                    selected = route
                    break
        if selected == "payroll":
            self.open_payroll()
        elif selected == "ai":
            self.open_ai_assistant()
        elif selected == "playbook":
            self._open_business_playbook()
        elif selected:
            self.go_to_tab(selected)
        else:
            self.status.showMessage("Chưa có lối tắt phù hợp; hãy chọn một gợi ý.", 3000)

    def _open_business_playbook(self):
        """Show local business guidance and explicit, user-invoked official links."""
        from core.business_playbook import get_business_playbook, get_next_actions

        dialog = QDialog(self)
        dialog.setWindowTitle("Lộ trình vận hành doanh nghiệp Việt Nam")
        dialog.resize(820, 650)
        layout = QVBoxLayout(dialog)
        intro = QLabel(
            "Checklist offline giúp biết nên đi đâu và làm gì. Liên kết ngoài chỉ mở khi bạn bấm; "
            "nội dung cần đối chiếu với cơ quan có thẩm quyền."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#475569; padding:4px 2px;")
        layout.addWidget(intro)

        actions = get_next_actions(self.db_conn, self.settings)
        action_group = QFrame()
        action_layout = QHBoxLayout(action_group)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.addWidget(QLabel("Việc nên làm tiếp theo:"))
        for action in actions[:3]:
            button = QPushButton(action["title"])
            button.setToolTip(action["reason"])
            button.clicked.connect(lambda _checked=False, route=action["route"]: self._playbook_route(dialog, route))
            action_layout.addWidget(button)
        action_layout.addStretch()
        layout.addWidget(action_group)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setOpenLinks(True)
        blocks = []
        for step in get_business_playbook():
            checklist = "".join(f"<li>{html.escape(item)}</li>" for item in step["checklist"])
            links = "".join(
                f'<li><a href="{html.escape(url, quote=True)}">{html.escape(label)}</a></li>'
                for label, url in step.get("official_links", [])
            )
            links_html = f"<p><b>Nguồn mở khi cần:</b></p><ul>{links}</ul>" if links else ""
            blocks.append(
                f"<h3>{html.escape(step['title'])}</h3>"
                f"<p>{html.escape(step['summary'])}</p><ul>{checklist}</ul>{links_html}"
            )
        browser.setHtml("<h2>Trợ lý vận hành doanh nghiệp</h2>" + "".join(blocks))
        layout.addWidget(browser, 1)

        footer = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        footer.rejected.connect(dialog.reject)
        layout.addWidget(footer)
        dialog.exec()

    def _playbook_route(self, dialog, route):
        if route == "payroll":
            self.open_payroll()
        elif route == "ai":
            self.open_ai_assistant()
        else:
            self.go_to_tab(route)
        dialog.accept()

    @staticmethod
    def _fold_search(value: str) -> str:
        """Make navigation search forgiving for users who omit Vietnamese marks."""
        normalized = unicodedata.normalize("NFD", str(value or "").lower())
        return "".join(char for char in normalized if not unicodedata.combining(char))

    def go_to_tab(self, key):
        """Open a top-level workflow area by stable semantic key."""
        index = self.tab_indices.get(key)
        if index is None:
            return False
        self.tabs.setCurrentIndex(index)
        self._ensure_tab_loaded(index)
        page = self.tabs.widget(index)
        if page is not None and not getattr(self, "reduce_motion", False):
            target = page.widget() if hasattr(page, "widget") and page.widget() is not None else page
            self._page_animation = fade_widget(target, duration=140)
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

    def _open_help(self):
        """Show concrete help for the page currently selected by the user."""
        key = next(
            (name for name, index in self.tab_indices.items()
             if index == self.tabs.currentIndex()),
            "home",
        )
        pages = {
            "home": {
                "title": "Trang chủ",
                "purpose": "Tóm tắt doanh thu, chi phí, lợi nhuận sau thuế và cảnh báo cần xử lý.",
                "steps": ["Kiểm tra kỳ báo cáo.", "Đọc biểu đồ doanh thu, chi phí và lợi nhuận.", "Bấm vào cảnh báo để mở đúng nghiệp vụ cần hoàn thiện."],
            },
            "documents": {
                "title": "Chứng từ",
                "purpose": "Ghi nhận nghiệp vụ thu, chi, nhập, xuất, mua hàng và bán hàng theo bút toán cân đối.",
                "steps": ["Chọn loại chứng từ và ngày phát sinh.", "Chọn khách hàng hoặc nhà cung cấp, sau đó nhập các dòng Nợ/Có.", "Chỉ lưu khi tổng Nợ bằng tổng Có; kiểm tra lại nội dung trước khi ghi sổ."],
            },
            "directories": {
                "title": "Danh mục",
                "purpose": "Quản lý tài khoản, khách hàng, nhà cung cấp, hàng hóa, tài sản cố định và công cụ.",
                "steps": ["Tạo danh mục gốc trước khi nhập chứng từ.", "Dùng tìm kiếm để lọc, nhấp đúp để sửa, và kiểm tra mã định danh trước khi xóa.", "VSIC là mã ngành kinh tế; dùng để đối chiếu ngành đăng ký, không thay thế tư vấn pháp lý."],
            },
            "invoices": {
                "title": "Hóa đơn",
                "purpose": "Lập và quản lý hóa đơn bán hàng dựa trên dữ liệu khách hàng và hàng hóa đã có.",
                "steps": ["Chọn khách hàng từ danh mục, không gõ tên rời để tránh trùng dữ liệu.", "Thêm hàng hóa, số lượng, đơn giá và thuế suất.", "Kiểm tra thông tin người bán, người mua và địa chỉ trước khi xuất file."],
            },
            "ledger": {
                "title": "Sổ cái",
                "purpose": "Tra cứu toàn bộ phát sinh theo tài khoản, chứng từ, ngày và số dư lũy kế.",
                "steps": ["Nhập mã tài khoản, hoặc để trống để xem toàn bộ.", "Dùng Lọc nâng cao để giới hạn khoảng ngày.", "Xuất Excel sau khi kiểm tra số liệu; Nợ (Debit) và Có (Credit) phải khớp theo từng chứng từ."],
            },
            "ar_ap": {
                "title": "Công nợ",
                "purpose": "Theo dõi số phải thu khách hàng, phải trả nhà cung cấp, hạn thanh toán và dòng tiền liên quan.",
                "steps": ["Chọn đối tượng công nợ.", "Đối chiếu số phát sinh với chứng từ và sổ cái.", "Ghi nhận thu/chi thanh toán để giảm số dư còn phải thu hoặc phải trả."],
            },
            "reports": {
                "title": "Báo cáo",
                "purpose": "Tổng hợp số liệu từ sổ cái thành báo cáo quản trị và báo cáo tài chính cơ bản.",
                "steps": ["Chọn kỳ báo cáo.", "Đối chiếu doanh thu, chi phí, thuế và lợi nhuận.", "Xuất báo cáo sau khi kiểm tra các chứng từ chưa cân đối hoặc còn thiếu."],
            },
            "analytics": {
                "title": "Phân tích",
                "purpose": "Biến số liệu kế toán thành chỉ báo dễ đọc để quyết định về doanh thu, chi phí, tồn kho và dòng tiền.",
                "steps": ["Chọn khoảng thời gian và loại chỉ số.", "Đọc xu hướng trên biểu đồ, không chỉ nhìn một con số đơn lẻ.", "Kiểm tra lại chứng từ gốc khi chỉ số thay đổi bất thường."],
            },
            "hr": {
                "title": "Nhân sự",
                "purpose": "Quản lý hồ sơ, ngày công, giờ làm thêm, lương và thuế thu nhập cá nhân.",
                "steps": ["Tạo hồ sơ nhân viên và mức lương trước.", "Chấm công theo từng ngày, nhập giờ vào/ra và đánh dấu làm thêm có phê duyệt.", "Kiểm tra bảng lương, bảo hiểm và thuế thu nhập cá nhân trước khi ghi nhận chi phí."],
            },
            "tools": {
                "title": "Công cụ",
                "purpose": "Tính thuế, tra cứu VSIC, quản lý kho văn bản mẫu và sử dụng các kết nối online đã chủ động bật.",
                "steps": ["Dùng các tab phụ theo thứ tự: Tính thuế, Kho văn bản mẫu, VSIC, Optional online.", "Online mặc định tắt; chỉ bật từng nguồn trong Cài đặt khi cần.", "AI chỉ nhận dữ liệu sổ kế toán và nội dung văn bản người dùng chọn; mọi đề xuất ghi sổ phải được kiểm tra và duyệt."],
            },
            "settings": {
                "title": "Cài đặt",
                "purpose": "Thiết lập doanh nghiệp, thuế, tiền tệ, ngân hàng, quyền online và trợ lý cục bộ.",
                "steps": ["Hoàn thiện thông tin doanh nghiệp trước khi lập hóa đơn.", "Kiểm tra tiền tệ, số lẻ, thuế suất và phương thức thanh toán.", "Chỉ bật đúng tính năng online cần dùng; giữ Ollama ở địa chỉ cục bộ nếu muốn AI không rời khỏi máy."],
            },
        }
        page = pages.get(key, pages["home"])
        terms = (
            "<b>Thuật ngữ:</b> Nợ/Có = Debit/Credit; "
            "GTGT = giá trị gia tăng; TNCN = thu nhập cá nhân; "
            "TNDN = thu nhập doanh nghiệp; VSIC = mã ngành kinh tế Việt Nam."
        )
        steps_html = "".join(f"<li>{step}</li>" for step in page["steps"])
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Trợ giúp · {page['title']}")
        dialog.resize(680, 500)
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(
            f"<h2>{page['title']}</h2><p>{page['purpose']}</p>"
            f"<h3>Cách dùng</h3><ol>{steps_html}</ol>"
            f"<p style='color:#475569'>{terms}</p>"
        )
        layout.addWidget(browser)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.exec()

    @staticmethod
    def _make_error_tab(name: str, error: Exception) -> QWidget:
        """Create a clean error placeholder for a tab that failed to load."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading = QLabel(f"Không thể tải {name}")
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
        if hasattr(self, 'ar_ap_tab') and hasattr(self.ar_ap_tab, 'refresh'):
            self.ar_ap_tab.refresh()
        if hasattr(self, 'reports_tab') and hasattr(self.reports_tab, 'refresh'):
            self.reports_tab.refresh()
        if hasattr(self, 'analytics_tab') and hasattr(self.analytics_tab, 'refresh'):
            self.analytics_tab.refresh()
        if hasattr(self, 'hr_tab') and hasattr(self.hr_tab, 'refresh'):
            self.hr_tab.refresh()
        if hasattr(self, 'tools_tab') and hasattr(self.tools_tab, 'refresh'):
            self.tools_tab.refresh()

    def closeEvent(self, event):
        conn = getattr(self, "db_conn", None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
            self.db_conn = None
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    _set_windows_app_identity()
    icon_path = utils_mod.get_resource_path("logo.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
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

    _load_application_font()

    window = VnSmeLedgerApp()
    window.show()
    ready_marker = os.environ.get("VN_SME_QA_READY_FILE")
    if ready_marker:
        def write_ready_marker():
            try:
                with open(ready_marker, "w", encoding="utf-8") as marker_file:
                    marker_file.write(window.windowTitle())
            except OSError as exc:
                print(f"Could not write QA readiness marker: {exc}", file=sys.stderr)
            if os.environ.get("VN_SME_QA_AUTOQUIT") == "1":
                QTimer.singleShot(500, lambda: (window.close(), app.quit()))

        QTimer.singleShot(100, write_ready_marker)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
