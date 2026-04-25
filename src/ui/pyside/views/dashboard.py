"""
Dashboard View — Executive overview of business metrics.
Auto-refreshes on navigation.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from src.ui.pyside.theme import Theme
from src.ui.pyside.widgets import KPICard


class PySideDashboard(QWidget):
    def __init__(self, inventory_service, reporting_service):
        super().__init__()
        self.inventory_service = inventory_service
        self.reporting_service = reporting_service
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)
        
        self._build_kpi_row(main_layout)
        self._build_bottom_section(main_layout)
    
    def _build_kpi_row(self, parent_layout):
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(12)
        
        self.kpi_revenue = KPICard("Revenue", "৳ 0", "📈", Theme.ACCENT)
        self.kpi_profit = KPICard("Net Profit", "৳ 0", "💰", Theme.SUCCESS)
        self.kpi_products = KPICard("Active Products", "0", "📦", Theme.PURPLE)
        self.kpi_alerts = KPICard("Low Stock Alerts", "0", "⚠️", Theme.SUCCESS)
        
        kpi_layout.addWidget(self.kpi_revenue)
        kpi_layout.addWidget(self.kpi_profit)
        kpi_layout.addWidget(self.kpi_products)
        kpi_layout.addWidget(self.kpi_alerts)
        
        parent_layout.addLayout(kpi_layout)
    
    def _build_bottom_section(self, parent_layout):
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(16)
        
        # Recent Activity
        recent_frame = QFrame()
        recent_frame.setStyleSheet(Theme.card_style())
        recent_layout = QVBoxLayout(recent_frame)
        recent_layout.setContentsMargins(16, 16, 16, 16)
        recent_layout.setSpacing(10)
        
        title = QLabel("🕐  Recent Activity")
        title.setStyleSheet(Theme.label_title())
        recent_layout.addWidget(title)
        
        self.activity_table = QTableWidget(0, 4)
        self.activity_table.setHorizontalHeaderLabels(["Type", "Product", "Amount", "Date"])
        self.activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.activity_table.setStyleSheet(Theme.table_style())
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.activity_table.setShowGrid(False)
        recent_layout.addWidget(self.activity_table, stretch=1)
        
        bottom_layout.addWidget(recent_frame, stretch=1)
        
        # Low Stock Alerts
        alert_frame = QFrame()
        alert_frame.setStyleSheet(Theme.card_style())
        alert_layout = QVBoxLayout(alert_frame)
        alert_layout.setContentsMargins(16, 16, 16, 16)
        alert_layout.setSpacing(10)
        
        alert_title = QLabel("⚠️  Low Stock Alerts")
        alert_title.setStyleSheet(Theme.label_title())
        alert_layout.addWidget(alert_title)
        
        self.alert_table = QTableWidget(0, 2)
        self.alert_table.setHorizontalHeaderLabels(["Product", "Stock"])
        self.alert_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alert_table.setStyleSheet(Theme.table_style())
        self.alert_table.verticalHeader().setVisible(False)
        self.alert_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.alert_table.setShowGrid(False)
        alert_layout.addWidget(self.alert_table, stretch=1)
        
        bottom_layout.addWidget(alert_frame, stretch=1)
        
        parent_layout.addLayout(bottom_layout, stretch=1)
    
    def refresh(self):
        """Reload all dashboard data."""
        try:
            # KPIs
            summary = self.reporting_service.get_sales_summary(days=None)
            self.kpi_revenue.set_value(f"৳ {summary.get('revenue', 0):,.0f}")
            self.kpi_profit.set_value(f"৳ {summary.get('profit', 0):,.0f}")
            
            stock_df = self.inventory_service.get_stock_status()
            self.kpi_products.set_value(str(len(stock_df)))
            
            low_stock = self.reporting_service.get_reorder_alerts()
            low_count = len(low_stock)
            self.kpi_alerts.set_value(str(low_count))
            alert_color = Theme.DANGER if low_count > 0 else Theme.SUCCESS
            self.kpi_alerts.set_color(alert_color)
            
            # Recent Activity
            self.activity_table.setRowCount(0)
            recent_df = self.reporting_service.get_recent_activity(limit=10)
            if not recent_df.empty:
                for _, row in recent_df.iterrows():
                    r = self.activity_table.rowCount()
                    self.activity_table.insertRow(r)
                    
                    type_item = QTableWidgetItem("🧾 Sale" if row['type'] == 'SALE' else "🚚 Purchase")
                    type_item.setForeground(QColor(Theme.SUCCESS if row['type'] == 'SALE' else Theme.ORANGE))
                    self.activity_table.setItem(r, 0, type_item)
                    self.activity_table.setItem(r, 1, QTableWidgetItem(str(row['name'])))
                    
                    amt_item = QTableWidgetItem(f"৳ {row['amt']:,.0f}")
                    amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.activity_table.setItem(r, 2, amt_item)
                    self.activity_table.setItem(r, 3, QTableWidgetItem(str(row['date'])[:10]))
            
            # Alerts
            self.alert_table.setRowCount(0)
            if not low_stock.empty:
                for _, row in low_stock.head(10).iterrows():
                    r = self.alert_table.rowCount()
                    self.alert_table.insertRow(r)
                    self.alert_table.setItem(r, 0, QTableWidgetItem(str(row['name'])))
                    
                    stock_item = QTableWidgetItem(str(int(row['current_stock'])))
                    stock_item.setForeground(QColor(Theme.DANGER))
                    stock_item.setTextAlignment(Qt.AlignCenter)
                    self.alert_table.setItem(r, 1, stock_item)
        except Exception as e:
            print(f"Dashboard refresh error: {e}")
    
    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
