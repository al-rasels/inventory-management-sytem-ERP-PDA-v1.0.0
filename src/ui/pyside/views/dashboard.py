from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
from PySide6.QtCore import Qt

class PySideDashboard(QWidget):
    def __init__(self, inventory_service, reporting_service):
        super().__init__()
        self.inventory_service = inventory_service
        self.reporting_service = reporting_service
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(20)
        
        self._build_kpi_row()
        self._build_charts_row()
        
    def _build_kpi_row(self):
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(15)
        
        summary = self.reporting_service.get_sales_summary(days=None)
        rev = summary.get('revenue', 0)
        prof = summary.get('profit', 0)
        
        stock_df = self.inventory_service.get_stock_status()
        items = len(stock_df)
        
        low_stock = self.reporting_service.get_reorder_alerts()
        low_count = len(low_stock)
        
        kpi_layout.addWidget(self._create_kpi_card("Total Revenue", f"৳ {rev:,.0f}", "📈", "#3182CE"))
        kpi_layout.addWidget(self._create_kpi_card("Net Profit", f"৳ {prof:,.0f}", "💰", "#38A169"))
        kpi_layout.addWidget(self._create_kpi_card("Active Products", f"{items}", "📦", "#805AD5"))
        kpi_layout.addWidget(self._create_kpi_card("Alerts", f"{low_count}", "⚠️", "#E53E3E" if low_count > 0 else "#38A169"))
        
        self.layout.addLayout(kpi_layout)
        
    def _create_kpi_card(self, title, value, icon, color):
        card = QFrame()
        card.setStyleSheet(f"background-color: #2D3748; border-radius: 12px; border-top: 4px solid {color};")
        card.setFixedHeight(120)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        
        top_layout = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 14px; color: #A0AEC0; background: transparent; border: none;")
        
        top_layout.addWidget(icon_lbl)
        top_layout.addWidget(title_lbl)
        top_layout.addStretch()
        
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {color}; background: transparent; border: none;")
        
        layout.addLayout(top_layout)
        layout.addWidget(val_lbl)
        
        return card
        
    def _build_charts_row(self):
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        
        # Recent Activity
        recent_frame = QFrame()
        recent_frame.setStyleSheet("background-color: #2D3748; border-radius: 12px;")
        recent_layout = QVBoxLayout(recent_frame)
        
        title = QLabel("Recent Activity")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #F7FAFC;")
        recent_layout.addWidget(title)
        
        recent_df = self.reporting_service.get_recent_activity(limit=8)
        if recent_df.empty:
            empty = QLabel("No recent transactions")
            empty.setStyleSheet("color: #A0AEC0;")
            recent_layout.addWidget(empty)
        else:
            for _, row in recent_df.iterrows():
                item = QLabel(f"{'🧾' if row['type'] == 'SALE' else '🚚'} {row['name']} - ৳ {row['amt']:,.0f}")
                item.setStyleSheet(f"color: {'#38A169' if row['type'] == 'SALE' else '#DD6B20'}; font-size: 13px;")
                recent_layout.addWidget(item)
                
        recent_layout.addStretch()
        bottom_layout.addWidget(recent_frame, stretch=1)
        
        # Low stock
        alert_frame = QFrame()
        alert_frame.setStyleSheet("background-color: #2D3748; border-radius: 12px;")
        alert_layout = QVBoxLayout(alert_frame)
        
        alert_title = QLabel("Low Stock Alerts")
        alert_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #F7FAFC;")
        alert_layout.addWidget(alert_title)
        
        low_stock = self.reporting_service.get_reorder_alerts()
        if low_stock.empty:
            empty = QLabel("All stock healthy")
            empty.setStyleSheet("color: #38A169;")
            alert_layout.addWidget(empty)
        else:
            for _, row in low_stock.head(8).iterrows():
                item = QLabel(f"⚠️ {row['name']} - {int(row['current_stock'])} left")
                item.setStyleSheet("color: #E53E3E; font-size: 13px;")
                alert_layout.addWidget(item)
                
        alert_layout.addStretch()
        bottom_layout.addWidget(alert_frame, stretch=1)
        
        self.layout.addLayout(bottom_layout, stretch=1)
