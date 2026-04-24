from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class PySideAnalytics(QWidget):
    def __init__(self, report_service):
        super().__init__()
        self.report_service = report_service
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(20)
        
        self._build_toolbar()
        self._build_charts()
        self._build_tables()
        self._load_data()
        
    def _build_toolbar(self):
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #2D3748; border-radius: 8px;")
        toolbar.setFixedHeight(60)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(15, 0, 15, 0)
        
        title = QLabel("📊 Advanced Analytics")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #F7FAFC;")
        layout.addWidget(title)
        layout.addStretch()
        
        layout.addWidget(QLabel("Timeframe:", styleSheet="color: #A0AEC0; font-weight: bold;"))
        self.time_combo = QComboBox()
        self.time_combo.addItems(["Today", "Last 7 Days", "Last 30 Days", "This Year", "All Time"])
        self.time_combo.setStyleSheet("QComboBox { background-color: #1A202C; color: #FFFFFF; border: 1px solid #4A5568; border-radius: 6px; padding: 5px; }")
        self.time_combo.currentTextChanged.connect(self._load_data)
        layout.addWidget(self.time_combo)
        
        self.layout.addWidget(toolbar)

    def _build_charts(self):
        # We will use simple summary cards and text for the prototype instead of QtCharts to avoid complex dependencies
        chart_layout = QHBoxLayout()
        
        self.rev_card = self._create_metric_card("Revenue", "৳ 0")
        self.profit_card = self._create_metric_card("Profit", "৳ 0")
        self.margin_card = self._create_metric_card("Avg Margin", "0%")
        self.orders_card = self._create_metric_card("Total Orders", "0")
        
        chart_layout.addWidget(self.rev_card['widget'])
        chart_layout.addWidget(self.profit_card['widget'])
        chart_layout.addWidget(self.margin_card['widget'])
        chart_layout.addWidget(self.orders_card['widget'])
        
        self.layout.addLayout(chart_layout)
        
    def _create_metric_card(self, title, value):
        card = QFrame()
        card.setStyleSheet("background-color: #2D3748; border-radius: 10px;")
        card.setFixedHeight(100)
        
        layout = QVBoxLayout(card)
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #A0AEC0; font-size: 14px;")
        t_lbl.setAlignment(Qt.AlignCenter)
        
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet("color: #63B3ED; font-size: 24px; font-weight: bold;")
        v_lbl.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(t_lbl)
        layout.addWidget(v_lbl)
        
        return {'widget': card, 'val_lbl': v_lbl}

    def _build_tables(self):
        tables_layout = QHBoxLayout()
        
        # Profit by Category
        cat_frame = QFrame()
        cat_frame.setStyleSheet("background-color: #2D3748; border-radius: 12px;")
        cat_layout = QVBoxLayout(cat_frame)
        cat_layout.addWidget(QLabel("Profit by Category", styleSheet="font-weight: bold; color: white;"))
        
        self.cat_table = QTableWidget(0, 3)
        self.cat_table.setHorizontalHeaderLabels(["Category", "Revenue", "Profit"])
        self.cat_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cat_table.setStyleSheet("QTableWidget { background-color: #1A202C; color: #E2E8F0; border: none; } QHeaderView::section { background-color: #2D3748; color: #A0AEC0; }")
        self.cat_table.verticalHeader().setVisible(False)
        cat_layout.addWidget(self.cat_table)
        tables_layout.addWidget(cat_frame)
        
        # Trend
        trend_frame = QFrame()
        trend_frame.setStyleSheet("background-color: #2D3748; border-radius: 12px;")
        trend_layout = QVBoxLayout(trend_frame)
        trend_layout.addWidget(QLabel("Daily Sales Trend", styleSheet="font-weight: bold; color: white;"))
        
        self.trend_table = QTableWidget(0, 3)
        self.trend_table.setHorizontalHeaderLabels(["Date", "Revenue", "Profit"])
        self.trend_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.trend_table.setStyleSheet(self.cat_table.styleSheet())
        self.trend_table.verticalHeader().setVisible(False)
        trend_layout.addWidget(self.trend_table)
        tables_layout.addWidget(trend_frame)
        
        self.layout.addLayout(tables_layout, stretch=1)

    def _load_data(self):
        val = self.time_combo.currentText()
        days_map = {"Today": 1, "Last 7 Days": 7, "Last 30 Days": 30, "This Year": 365, "All Time": None}
        days = days_map.get(val, 30)
        
        summary = self.report_service.get_sales_summary(days=days)
        rev = summary.get('revenue', 0)
        prof = summary.get('profit', 0)
        orders = summary.get('sales_count', 0)
        margin = (prof / rev * 100) if rev > 0 else 0
        
        self.rev_card['val_lbl'].setText(f"৳ {rev:,.0f}")
        self.profit_card['val_lbl'].setText(f"৳ {prof:,.0f}")
        self.margin_card['val_lbl'].setText(f"{margin:.1f}%")
        self.orders_card['val_lbl'].setText(str(orders))
        
        # Categories
        cat_df = self.report_service.get_profit_by_category()
        self.cat_table.setRowCount(0)
        for _, row in cat_df.iterrows():
            r = self.cat_table.rowCount()
            self.cat_table.insertRow(r)
            self.cat_table.setItem(r, 0, QTableWidgetItem(str(row['category'])))
            self.cat_table.setItem(r, 1, QTableWidgetItem(f"৳ {row['rev']:,.0f}"))
            self.cat_table.setItem(r, 2, QTableWidgetItem(f"৳ {row['prof']:,.0f}"))
            
        # Trend
        trend_df = self.report_service.get_daily_sales_trend(days=days or 30)
        self.trend_table.setRowCount(0)
        for _, row in trend_df.iterrows():
            r = self.trend_table.rowCount()
            self.trend_table.insertRow(r)
            self.trend_table.setItem(r, 0, QTableWidgetItem(str(row['date'])[:10]))
            self.trend_table.setItem(r, 1, QTableWidgetItem(f"৳ {row.get('daily_rev', 0):,.0f}"))
            self.trend_table.setItem(r, 2, QTableWidgetItem("-"))
