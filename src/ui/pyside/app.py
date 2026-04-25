"""
SunERP Professional — Main Application Window
Features: sidebar navigation with QtAwesome icons, status bar, keyboard shortcuts.
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QShortcut, QKeySequence, QColor
from qtawesome import icon as qta_icon

from src.ui.pyside.theme import Theme
from src.ui.pyside.widgets import StatusBar


class NavButton(QPushButton):
    """Sidebar navigation button with icon and active state."""
    def __init__(self, text: str, icon: QIcon = None):
        super().__init__(text)
        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(18, 18))
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_MUTED};
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 12px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background-color: {Theme.ACCENT};
                color: white;
                font-weight: 600;
            }}
        """)


class ERPAppWindow(QMainWindow):
    def __init__(self, services):
        super().__init__()
        self.services = services
        self.setWindowTitle("SunERP Professional — POS & Inventory")
        self.resize(1360, 820)
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(Theme.global_stylesheet())

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._setup_sidebar(body)
        self._setup_content(body)
        root.addLayout(body, stretch=1)

        # Status Bar
        self.status_bar = StatusBar()
        root.addWidget(self.status_bar)

        self._setup_shortcuts()

    # ----- Sidebar ---------------------------------------------------------
    def _setup_sidebar(self, parent):
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border-right: 1px solid {Theme.BORDER};
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(2, 0)
        sidebar.setGraphicsEffect(shadow)

        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(12, 24, 12, 24)
        sl.setSpacing(6)

        # Logo with QtAwesome icon
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        logo_icon = QLabel()
        logo_icon.setPixmap(qta_icon('fa5s.store-alt', color=Theme.ACCENT_LIGHT).pixmap(24, 24))
        logo_icon.setStyleSheet("border: none; background: transparent;")
        logo_text = QLabel("SunERP")
        logo_text.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {Theme.ACCENT_LIGHT}; border: none; background: transparent;"
        )
        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(logo_text)
        sl.addLayout(logo_layout)

        ver = QLabel("Professional v3.0")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet(Theme.label_muted())
        sl.addWidget(ver)
        sl.addSpacing(30)

        self.nav_buttons = []
        # Define navigation items with QtAwesome icons
        nav_items = [
            ("Dashboard", qta_icon('fa5s.tachometer-alt', color=Theme.TEXT_MUTED), "F5"),
            ("Products", qta_icon('fa5s.box', color=Theme.TEXT_MUTED), "F1"),
            ("Inventory", qta_icon('fa5s.clipboard-list', color=Theme.TEXT_MUTED), ""),
            ("Sales", qta_icon('fa5s.shopping-cart', color=Theme.TEXT_MUTED), "F2"),
            ("Purchases", qta_icon('fa5s.truck', color=Theme.TEXT_MUTED), "F3"),
            ("Transactions", qta_icon('fa5s.list-alt', color=Theme.TEXT_MUTED), ""),
            ("Analytics", qta_icon('fa5s.chart-line', color=Theme.TEXT_MUTED), ""),
            ("Settings", qta_icon('fa5s.cog', color=Theme.TEXT_MUTED), ""),
        ]

        for text, icon, shortcut in nav_items:
            btn = NavButton(text, icon)
            if shortcut:
                btn.setToolTip(f"{text} ({shortcut})")
            btn.clicked.connect(lambda ch, b=btn, t=text: self._on_nav(b, t))
            sl.addWidget(btn)
            self.nav_buttons.append((btn, text))

        sl.addStretch()

        # Logout button with icon
        logout_btn = NavButton("Logout", qta_icon('fa5s.sign-out-alt', color=Theme.DANGER))
        logout_btn.setStyleSheet(
            logout_btn.styleSheet().replace(Theme.ACCENT, Theme.DANGER)
        )
        sl.addWidget(logout_btn)

        parent.addWidget(sidebar)
        if self.nav_buttons:
            self.nav_buttons[0][0].setChecked(True)

    # ----- Content area ----------------------------------------------------
    def _setup_content(self, parent):
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(24, 20, 24, 16)
        cl.setSpacing(16)

        # Top bar with title and user badge
        top = QHBoxLayout()
        self.title_lbl = QLabel("Dashboard")
        self.title_lbl.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        top.addWidget(self.title_lbl)
        top.addStretch()

        # User badge (icon + label)
        badge_widget = QWidget()
        badge_widget.setStyleSheet(f"""
            background-color: {Theme.BG_SECONDARY};
            border-radius: 16px;
            border: 1px solid {Theme.BORDER};
            padding: 2px 8px;
        """)
        badge_layout = QHBoxLayout(badge_widget)
        badge_layout.setContentsMargins(6, 2, 10, 2)
        badge_layout.setSpacing(4)
        user_icon = QLabel()
        user_icon.setPixmap(qta_icon('fa5s.user', color=Theme.TEXT_SECONDARY).pixmap(14, 14))
        user_icon.setStyleSheet("background: transparent; border: none;")
        badge_layout.addWidget(user_icon)
        user_label = QLabel("Admin")
        user_label.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_SECONDARY}; background: transparent; border: none;")
        badge_layout.addWidget(user_label)
        top.addWidget(badge_widget)
        cl.addLayout(top)

        # Stacked views
        self.stack = QStackedWidget()
        cl.addWidget(self.stack, stretch=1)

        self._init_views()
        parent.addWidget(content, stretch=1)

    def _init_views(self):
        from src.ui.pyside.views.dashboard import PySideDashboard
        from src.ui.pyside.views.products import PySideProducts
        from src.ui.pyside.views.inventory import PySideInventory
        from src.ui.pyside.views.sales import PySideSales
        from src.ui.pyside.views.purchases import PySidePurchases
        from src.ui.pyside.views.transactions import PySideTransactions
        from src.ui.pyside.views.analytics import PySideAnalytics
        from src.ui.pyside.views.settings import PySideSettings

        self.views = {}

        dash = PySideDashboard(self.services['inventory'], self.services['report'])
        self.stack.addWidget(dash)
        self.views["Dashboard"] = (self.stack.count() - 1, dash)

        prods = PySideProducts(self.services['product'], self.services['inventory'])
        self.stack.addWidget(prods)
        self.views["Products"] = (self.stack.count() - 1, prods)

        inv = PySideInventory(self.services['inventory'])
        self.stack.addWidget(inv)
        self.views["Inventory"] = (self.stack.count() - 1, inv)

        sales = PySideSales(self.services['sales'], self.services['inventory'])
        sales.sale_completed.connect(lambda: self._refresh_view("Dashboard"))
        self.stack.addWidget(sales)
        self.views["Sales"] = (self.stack.count() - 1, sales)

        purch = PySidePurchases(self.services['purchase'], self.services['product'], self.services['report'])
        self.stack.addWidget(purch)
        self.views["Purchases"] = (self.stack.count() - 1, purch)

        trans = PySideTransactions(self.services['report'])
        self.stack.addWidget(trans)
        self.views["Transactions"] = (self.stack.count() - 1, trans)

        analytics = PySideAnalytics(self.services['report'])
        self.stack.addWidget(analytics)
        self.views["Analytics"] = (self.stack.count() - 1, analytics)

        settings = PySideSettings(self.services['db'])
        self.stack.addWidget(settings)
        self.views["Settings"] = (self.stack.count() - 1, settings)

    # ----- Navigation ------------------------------------------------------
    def _on_nav(self, clicked_btn, text):
        for btn, _ in self.nav_buttons:
            if btn != clicked_btn:
                btn.setChecked(False)
        clicked_btn.setChecked(True)
        self.title_lbl.setText(text)
        if text in self.views:
            idx, view = self.views[text]
            self.stack.setCurrentIndex(idx)
            if hasattr(view, 'refresh'):
                view.refresh()
            self.status_bar.set_status(f"Viewing {text}")

    def _refresh_view(self, name):
        if name in self.views:
            _, view = self.views[name]
            if hasattr(view, 'refresh'):
                view.refresh()

    def _navigate_to(self, name):
        for btn, text in self.nav_buttons:
            if text == name:
                self._on_nav(btn, text)
                break

    # ----- Shortcuts -------------------------------------------------------
    def _setup_shortcuts(self):
        QShortcut(QKeySequence("F5"), self, lambda: self._navigate_to("Dashboard"))
        QShortcut(QKeySequence("F1"), self, lambda: self._navigate_to("Products"))
        QShortcut(QKeySequence("F2"), self, lambda: self._navigate_to("Sales"))
        QShortcut(QKeySequence("F3"), self, lambda: self._navigate_to("Purchases"))
        QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search)

    def _focus_search(self):
        idx = self.stack.currentIndex()
        for name, (i, view) in self.views.items():
            if i == idx and hasattr(view, 'search_input'):
                view.search_input.setFocus()
                view.search_input.selectAll()
                return