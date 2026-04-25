"""Inventory View — Stock levels, filtering, and valuation."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from src.ui.pyside.theme import Theme
from src.ui.pyside.widgets import KPICard


class PySideInventory(QWidget):
    def __init__(self, inventory_service):
        super().__init__()
        self.inventory_service = inventory_service
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        self._build_kpis(layout)
        self._build_toolbar(layout)
        self._build_table(layout)

    def _build_kpis(self, parent):
        row = QHBoxLayout()
        row.setSpacing(12)
        self.kpi_units = KPICard("Total Units", "0", "📦", Theme.ACCENT)
        self.kpi_value = KPICard("Stock Value", "৳ 0", "💰", Theme.SUCCESS)
        self.kpi_skus = KPICard("SKU Count", "0", "🏷️", Theme.PURPLE)
        self.kpi_oos = KPICard("Out of Stock", "0", "⚠️", Theme.DANGER)
        for w in [self.kpi_units, self.kpi_value, self.kpi_skus, self.kpi_oos]: row.addWidget(w)
        parent.addLayout(row)

    def _build_toolbar(self, parent):
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"QFrame {{ background-color: {Theme.BG_SECONDARY}; border-radius: {Theme.RADIUS_MD}; border: 1px solid {Theme.BORDER}; }}")
        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(10)
        h.addWidget(QLabel("Filter:", styleSheet=f"color: {Theme.TEXT_MUTED}; font-weight: bold; border:none; background:transparent;"))
        self.stock_filter = QComboBox()
        self.stock_filter.addItems(["All", "Low Stock", "Out of Stock", "Healthy"])
        self.stock_filter.setStyleSheet(Theme.combo_style())
        self.stock_filter.currentTextChanged.connect(self._load_data)
        self.cat_filter = QComboBox()
        self.cat_filter.addItem("All Categories")
        self.cat_filter.setStyleSheet(Theme.combo_style())
        self.cat_filter.currentTextChanged.connect(self._load_data)
        h.addWidget(self.stock_filter)
        h.addWidget(self.cat_filter)
        h.addStretch()
        parent.addWidget(bar)

    def _build_table(self, parent):
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["SKU", "Name", "Category", "Purchased", "Sold", "Balance", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet(Theme.table_style())
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setShowGrid(False)
        parent.addWidget(self.table, stretch=1)

    def _load_data(self):
        try:
            df = self.inventory_service.get_stock_status()
            tv = df['inventory_value'].sum()
            tu = df['current_stock'].sum()
            oos = len(df[df['current_stock'] <= 0])
            self.kpi_units.set_value(f"{tu:,.0f}")
            self.kpi_value.set_value(f"৳ {tv:,.0f}")
            self.kpi_skus.set_value(str(len(df)))
            self.kpi_oos.set_value(str(oos))
            self.kpi_oos.set_color(Theme.DANGER if oos > 0 else Theme.SUCCESS)
            # Load categories
            cats = sorted(df['category'].dropna().unique().tolist())
            cur = self.cat_filter.currentText()
            self.cat_filter.blockSignals(True)
            self.cat_filter.clear()
            self.cat_filter.addItem("All Categories")
            self.cat_filter.addItems(cats)
            idx = self.cat_filter.findText(cur)
            if idx >= 0: self.cat_filter.setCurrentIndex(idx)
            self.cat_filter.blockSignals(False)
            cat = self.cat_filter.currentText()
            if cat != "All Categories": df = df[df['category'] == cat]
            sf = self.stock_filter.currentText()
            self.table.setRowCount(0)
            for _, row in df.iterrows():
                bal = int(row['current_stock'])
                rq = int(row['reorder_qty'] if row['reorder_qty'] == row['reorder_qty'] else 50)
                if sf == "Low Stock" and bal >= rq: continue
                if sf == "Out of Stock" and bal > 0: continue
                if sf == "Healthy" and bal < rq: continue
                r = self.table.rowCount()
                self.table.insertRow(r)
                sku_item = QTableWidgetItem(str(row['sku_code']))
                sku_item.setForeground(QColor(Theme.TEXT_ACCENT))
                self.table.setItem(r, 0, sku_item)
                self.table.setItem(r, 1, QTableWidgetItem(str(row['name'])))
                self.table.setItem(r, 2, QTableWidgetItem(str(row['category'])))
                self.table.setItem(r, 3, QTableWidgetItem(str(int(row.get('total_in', 0)))))
                self.table.setItem(r, 4, QTableWidgetItem(str(int(row.get('total_out', 0)))))
                bi = QTableWidgetItem(str(bal))
                bi.setTextAlignment(Qt.AlignCenter)
                if bal <= 0: bi.setForeground(QColor(Theme.DANGER))
                elif bal < rq: bi.setForeground(QColor(Theme.WARNING))
                else: bi.setForeground(QColor(Theme.SUCCESS))
                self.table.setItem(r, 5, bi)
                vi = QTableWidgetItem(f"৳ {row['inventory_value']:,.0f}")
                vi.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(r, 6, vi)
        except Exception as e:
            print(f"Inventory load error: {e}")

    def refresh(self): self._load_data()
    def showEvent(self, event):
        super().showEvent(event)
        self._load_data()
