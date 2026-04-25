"""Transaction History View — Combined sales and purchase log."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from src.ui.pyside.theme import Theme


class PySideTransactions(QWidget):
    def __init__(self, report_service):
        super().__init__()
        self.report_service = report_service
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self._build_toolbar(layout)
        self._build_tabs(layout)

    def _build_toolbar(self, parent):
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"QFrame {{ background-color: {Theme.BG_SECONDARY}; border-radius: {Theme.RADIUS_MD}; border: 1px solid {Theme.BORDER}; }}")
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 16, 0)
        t = QLabel("📋  Transaction History")
        t.setStyleSheet(Theme.label_title())
        h.addWidget(t)
        h.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search by ID, product, or customer...")
        self.search.setFixedWidth(320)
        self.search.setStyleSheet(Theme.input_style())
        self.search.returnPressed.connect(self._load_data)
        h.addWidget(self.search)
        sb = QPushButton("Search")
        sb.setStyleSheet(Theme.btn_primary())
        sb.clicked.connect(self._load_data)
        h.addWidget(sb)
        parent.addWidget(bar)

    def _build_tabs(self, parent):
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {Theme.BORDER}; border-radius: {Theme.RADIUS_MD}; background: {Theme.BG_SECONDARY}; }}
            QTabBar::tab {{ background: {Theme.BG_PRIMARY}; color: {Theme.TEXT_MUTED}; padding: 10px 24px; border: 1px solid {Theme.BORDER}; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: 600; margin-right: 2px; }}
            QTabBar::tab:selected {{ background: {Theme.BG_SECONDARY}; color: {Theme.ACCENT_LIGHT}; border-bottom: 2px solid {Theme.ACCENT}; }}
            QTabBar::tab:hover {{ color: {Theme.TEXT_PRIMARY}; }}
        """)
        # Sales tab
        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setContentsMargins(12, 12, 12, 12)
        self.sales_table = QTableWidget(0, 6)
        self.sales_table.setHorizontalHeaderLabels(["Sale ID", "Date", "Product", "Customer", "Qty", "Revenue"])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sales_table.setStyleSheet(Theme.table_style())
        self.sales_table.verticalHeader().setVisible(False)
        self.sales_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.sales_table.setShowGrid(False)
        sl.addWidget(self.sales_table)
        self.tabs.addTab(sw, "🧾  Sales")
        # Purchases tab
        pw = QWidget()
        pl = QVBoxLayout(pw)
        pl.setContentsMargins(12, 12, 12, 12)
        self.purchase_table = QTableWidget(0, 6)
        self.purchase_table.setHorizontalHeaderLabels(["Purchase ID", "Date", "Product", "Supplier", "Qty", "Total Cost"])
        self.purchase_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.purchase_table.setStyleSheet(Theme.table_style())
        self.purchase_table.verticalHeader().setVisible(False)
        self.purchase_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.purchase_table.setShowGrid(False)
        pl.addWidget(self.purchase_table)
        self.tabs.addTab(pw, "🚚  Purchases")
        parent.addWidget(self.tabs, stretch=1)

    def _load_data(self):
        term = self.search.text().strip() or None
        try:
            # Sales
            sdf = self.report_service.get_sales_history(term)
            self.sales_table.setRowCount(0)
            for _, row in sdf.iterrows():
                r = self.sales_table.rowCount()
                self.sales_table.insertRow(r)
                sid = QTableWidgetItem(str(row['sales_id']))
                sid.setForeground(QColor(Theme.TEXT_ACCENT))
                self.sales_table.setItem(r, 0, sid)
                self.sales_table.setItem(r, 1, QTableWidgetItem(str(row['date'])[:10]))
                self.sales_table.setItem(r, 2, QTableWidgetItem(str(row['product_name'])))
                self.sales_table.setItem(r, 3, QTableWidgetItem(str(row.get('customer', ''))))
                self.sales_table.setItem(r, 4, QTableWidgetItem(str(row['qty'])))
                ri = QTableWidgetItem(f"৳ {row['revenue']:,.0f}")
                ri.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                ri.setForeground(QColor(Theme.SUCCESS))
                self.sales_table.setItem(r, 5, ri)
            # Purchases
            pdf = self.report_service.get_purchase_history(term)
            self.purchase_table.setRowCount(0)
            for _, row in pdf.iterrows():
                r = self.purchase_table.rowCount()
                self.purchase_table.insertRow(r)
                pid = QTableWidgetItem(str(row['purchase_id']))
                pid.setForeground(QColor(Theme.TEXT_ACCENT))
                self.purchase_table.setItem(r, 0, pid)
                self.purchase_table.setItem(r, 1, QTableWidgetItem(str(row['date'])[:10]))
                self.purchase_table.setItem(r, 2, QTableWidgetItem(str(row['product_name'])))
                self.purchase_table.setItem(r, 3, QTableWidgetItem(str(row.get('supplier', ''))))
                self.purchase_table.setItem(r, 4, QTableWidgetItem(str(row['qty'])))
                ci = QTableWidgetItem(f"৳ {row['total_cost']:,.0f}")
                ci.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                ci.setForeground(QColor(Theme.ORANGE))
                self.purchase_table.setItem(r, 5, ci)
        except Exception as e:
            print(f"Transaction load error: {e}")

    def refresh(self): self._load_data()
    def showEvent(self, event):
        super().showEvent(event)
        self._load_data()
