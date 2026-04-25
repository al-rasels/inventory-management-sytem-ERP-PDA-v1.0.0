"""Analytics View — Business intelligence with timeframe filtering."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from src.ui.pyside.theme import Theme
from src.ui.pyside.widgets import KPICard


class PySideAnalytics(QWidget):
    def __init__(self, report_service):
        super().__init__()
        self.report_service = report_service
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        self._build_toolbar(layout)
        self._build_kpis(layout)
        self._build_tables(layout)

    def _build_toolbar(self, parent):
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"QFrame {{ background-color: {Theme.BG_SECONDARY}; border-radius: {Theme.RADIUS_MD}; border: 1px solid {Theme.BORDER}; }}")
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 16, 0)
        t = QLabel("📊  Business Analytics")
        t.setStyleSheet(Theme.label_title())
        h.addWidget(t)
        h.addStretch()
        h.addWidget(QLabel("Timeframe:", styleSheet=f"color: {Theme.TEXT_MUTED}; font-weight: bold; border:none; background:transparent;"))
        self.time_combo = QComboBox()
        self.time_combo.addItems(["Today", "Last 7 Days", "Last 30 Days", "This Year", "All Time"])
        self.time_combo.setCurrentIndex(2)
        self.time_combo.setStyleSheet(Theme.combo_style())
        self.time_combo.currentTextChanged.connect(self._load_data)
        h.addWidget(self.time_combo)
        parent.addWidget(bar)

    def _build_kpis(self, parent):
        row = QHBoxLayout()
        row.setSpacing(12)
        self.kpi_rev = KPICard("Revenue", "৳ 0", "📈", Theme.ACCENT)
        self.kpi_prof = KPICard("Profit", "৳ 0", "💰", Theme.SUCCESS)
        self.kpi_margin = KPICard("Avg Margin", "0%", "📐", Theme.PURPLE)
        self.kpi_orders = KPICard("Total Sales", "0", "🧾", Theme.ORANGE)
        for w in [self.kpi_rev, self.kpi_prof, self.kpi_margin, self.kpi_orders]: row.addWidget(w)
        parent.addLayout(row)

    def _build_tables(self, parent):
        tl = QHBoxLayout()
        tl.setSpacing(16)
        # Category breakdown
        cf = QFrame()
        cf.setStyleSheet(Theme.card_style())
        cl = QVBoxLayout(cf)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.addWidget(QLabel("Profit by Category", styleSheet=Theme.label_title()))
        self.cat_table = QTableWidget(0, 4)
        self.cat_table.setHorizontalHeaderLabels(["Category", "Revenue", "Profit", "Margin"])
        self.cat_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cat_table.setStyleSheet(Theme.table_style())
        self.cat_table.verticalHeader().setVisible(False)
        self.cat_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cat_table.setShowGrid(False)
        cl.addWidget(self.cat_table)
        tl.addWidget(cf)
        # Sales trend
        tf = QFrame()
        tf.setStyleSheet(Theme.card_style())
        tfl = QVBoxLayout(tf)
        tfl.setContentsMargins(16, 16, 16, 16)
        tfl.addWidget(QLabel("Daily Sales Trend", styleSheet=Theme.label_title()))
        self.trend_table = QTableWidget(0, 2)
        self.trend_table.setHorizontalHeaderLabels(["Date", "Revenue"])
        self.trend_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.trend_table.setStyleSheet(Theme.table_style())
        self.trend_table.verticalHeader().setVisible(False)
        self.trend_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.trend_table.setShowGrid(False)
        tfl.addWidget(self.trend_table)
        tl.addWidget(tf)
        parent.addLayout(tl, stretch=1)

    def _load_data(self):
        try:
            dm = {"Today": 1, "Last 7 Days": 7, "Last 30 Days": 30, "This Year": 365, "All Time": None}
            days = dm.get(self.time_combo.currentText(), 30)
            s = self.report_service.get_sales_summary(days=days)
            rev = s.get('revenue', 0)
            prof = s.get('profit', 0)
            orders = s.get('sales_count', 0)
            margin = (prof / rev * 100) if rev > 0 else 0
            self.kpi_rev.set_value(f"৳ {rev:,.0f}")
            self.kpi_prof.set_value(f"৳ {prof:,.0f}")
            self.kpi_margin.set_value(f"{margin:.1f}%")
            self.kpi_orders.set_value(str(orders))
            # Category table
            cdf = self.report_service.get_profit_by_category()
            self.cat_table.setRowCount(0)
            for _, row in cdf.iterrows():
                r = self.cat_table.rowCount()
                self.cat_table.insertRow(r)
                self.cat_table.setItem(r, 0, QTableWidgetItem(str(row['category'])))
                ri = QTableWidgetItem(f"৳ {row['rev']:,.0f}")
                ri.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.cat_table.setItem(r, 1, ri)
                pi = QTableWidgetItem(f"৳ {row['prof']:,.0f}")
                pi.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                pi.setForeground(QColor(Theme.SUCCESS if row['prof'] > 0 else Theme.DANGER))
                self.cat_table.setItem(r, 2, pi)
                mi = QTableWidgetItem(f"{row.get('margin', 0):.1f}%")
                mi.setTextAlignment(Qt.AlignCenter)
                self.cat_table.setItem(r, 3, mi)
            # Trend
            tdf = self.report_service.get_daily_sales_trend(days=days or 30)
            self.trend_table.setRowCount(0)
            for _, row in tdf.iterrows():
                r = self.trend_table.rowCount()
                self.trend_table.insertRow(r)
                self.trend_table.setItem(r, 0, QTableWidgetItem(str(row['date'])[:10]))
                di = QTableWidgetItem(f"৳ {row.get('daily_rev', 0):,.0f}")
                di.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.trend_table.setItem(r, 1, di)
        except Exception as e:
            print(f"Analytics error: {e}")

    def refresh(self): self._load_data()
    def showEvent(self, event):
        super().showEvent(event)
        self._load_data()
