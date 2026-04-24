import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QStackedWidget, QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QIcon, QFont, QColor

class AnimatedButton(QPushButton):
    def __init__(self, text, icon_text=""):
        super().__init__(f"{icon_text}  {text}")
        self.setFixedHeight(45)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #A0AEC0;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2D3748;
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: #3182CE;
                color: #FFFFFF;
                font-weight: bold;
            }
        """)
        self.setCheckable(True)

class ERPAppWindow(QMainWindow):
    def __init__(self, services):
        super().__init__()
        self.services = services
        self.setWindowTitle("Sun Warehouse ERP - Premium")
        self.resize(1280, 800)
        self.setStyleSheet("background-color: #1A202C; color: #FFFFFF; font-family: 'Segoe UI', Inter, sans-serif;")
        
        # Main Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self._setup_sidebar()
        self._setup_content_area()

    def _setup_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet("background-color: #2D3748; border-right: 1px solid #4A5568;")
        
        # Shadow for sidebar
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(3, 0)
        self.sidebar.setGraphicsEffect(shadow)

        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(15, 30, 15, 30)
        self.sidebar_layout.setSpacing(10)

        # Logo Area
        self.logo_lbl = QLabel("☀ SunERP")
        self.logo_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #63B3ED; border: none;")
        self.logo_lbl.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(self.logo_lbl)
        self.sidebar_layout.addSpacing(40)

        # Navigation Buttons
        self.nav_group = []
        nav_items = [
            ("Dashboard", "📊"),
            ("Products", "📦"),
            ("Inventory", "📋"),
            ("Sales", "🛒"),
            ("Purchases", "🚚"),
            ("Analytics", "📈"),
            ("Settings", "⚙️")
        ]

        for text, icon in nav_items:
            btn = AnimatedButton(text, icon)
            btn.clicked.connect(lambda checked, b=btn, t=text: self._on_nav_clicked(b, t))
            self.sidebar_layout.addWidget(btn)
            self.nav_group.append(btn)

        self.sidebar_layout.addStretch()

        # Logout
        self.logout_btn = AnimatedButton("Logout", "🚪")
        self.logout_btn.setStyleSheet(self.logout_btn.styleSheet().replace("#3182CE", "#E53E3E"))
        self.sidebar_layout.addWidget(self.logout_btn)

        self.main_layout.addWidget(self.sidebar)
        
        # Default active
        if self.nav_group:
            self.nav_group[0].setChecked(True)

    def _setup_content_area(self):
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

        # Top Bar
        self.top_bar = QHBoxLayout()
        self.title_lbl = QLabel("Dashboard")
        self.title_lbl.setStyleSheet("font-size: 28px; font-weight: bold; color: #F7FAFC;")
        
        self.user_lbl = QLabel("👤 Admin User")
        self.user_lbl.setStyleSheet("font-size: 14px; color: #A0AEC0; background-color: #2D3748; padding: 8px 15px; border-radius: 15px;")
        
        self.top_bar.addWidget(self.title_lbl)
        self.top_bar.addStretch()
        self.top_bar.addWidget(self.user_lbl)
        
        self.content_layout.addLayout(self.top_bar)

        # Stacked Widget for Views
        self.stacked_widget = QStackedWidget()
        self.content_layout.addWidget(self.stacked_widget)
        
        from src.ui.pyside.views.dashboard import PySideDashboard
        
        # Initialize views dictionary
        self.views = {}
        
        # 0: Dashboard
        dashboard = PySideDashboard(self.services['inventory'], self.services['report'])
        self.stacked_widget.addWidget(dashboard)
        self.views["Dashboard"] = 0
        
        from src.ui.pyside.views.products import PySideProducts
        
        # 1: Products
        products_view = PySideProducts(self.services['product'], self.services['inventory'])
        self.stacked_widget.addWidget(products_view)
        self.views["Products"] = 1
        
        from src.ui.pyside.views.sales import PySideSales
        from src.ui.pyside.views.purchases import PySidePurchases
        from src.ui.pyside.views.inventory import PySideInventory
        from src.ui.pyside.views.analytics import PySideAnalytics
        from src.ui.pyside.views.settings import PySideSettings
        
        inventory_view = PySideInventory(self.services['inventory'])
        self.stacked_widget.addWidget(inventory_view)
        self.views["Inventory"] = self.stacked_widget.count() - 1
            
        sales_view = PySideSales(self.services['sales'], self.services['inventory'])
        self.stacked_widget.addWidget(sales_view)
        self.views["Sales"] = self.stacked_widget.count() - 1
        
        purchases_view = PySidePurchases(self.services['purchase'], self.services['product'], self.services['report'])
        self.stacked_widget.addWidget(purchases_view)
        self.views["Purchases"] = self.stacked_widget.count() - 1

        analytics_view = PySideAnalytics(self.services['report'])
        self.stacked_widget.addWidget(analytics_view)
        self.views["Analytics"] = self.stacked_widget.count() - 1

        settings_view = PySideSettings(self.services['db'])
        self.stacked_widget.addWidget(settings_view)
        self.views["Settings"] = self.stacked_widget.count() - 1

        self.main_layout.addWidget(self.content_area, stretch=1)

    def _on_nav_clicked(self, clicked_btn, text):
        for btn in self.nav_group:
            if btn != clicked_btn:
                btn.setChecked(False)
        clicked_btn.setChecked(True)
        
        # Update title
        self.title_lbl.setText(text)
        
        # Switch stacked widget index
        if text in self.views:
            self.stacked_widget.setCurrentIndex(self.views[text])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # High DPI scaling is enabled by default in Qt6
    
    window = ERPAppWindow(services={})
    window.show()
    sys.exit(app.exec())
