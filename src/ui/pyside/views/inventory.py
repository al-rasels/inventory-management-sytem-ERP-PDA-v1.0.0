from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class PySideInventory(QWidget):
    def __init__(self, inventory_service):
        super().__init__()
        self.inventory_service = inventory_service
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(20)
        
        self._build_summary_cards()
        self._build_toolbar()
        self._build_table()
        self._load_data()
        
    def _build_summary_cards(self):
        self.summary_layout = QHBoxLayout()
        self.summary_layout.setSpacing(15)
        
        self.cards = {
            "Total Units": self._create_card("Total Units", "0", "📦", "#3182CE"),
            "Stock Value": self._create_card("Stock Value", "৳ 0", "💰", "#38A169"),
            "SKU Count": self._create_card("SKU Count", "0", "🏷️", "#805AD5"),
            "Out of Stock": self._create_card("Out of Stock", "0", "⚠️", "#E53E3E")
        }
        
        for card in self.cards.values():
            self.summary_layout.addWidget(card['widget'])
            
        self.layout.addLayout(self.summary_layout)
        
    def _create_card(self, title, value, icon, color):
        card = QFrame()
        card.setStyleSheet(f"background-color: #2D3748; border-radius: 10px; border-top: 3px solid {color};")
        card.setFixedHeight(90)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        
        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 18px; background: transparent;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 12px; color: #A0AEC0; background: transparent;")
        top.addWidget(icon_lbl)
        top.addWidget(title_lbl)
        top.addStretch()
        
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color}; background: transparent;")
        
        layout.addLayout(top)
        layout.addWidget(val_lbl)
        
        return {'widget': card, 'val_lbl': val_lbl, 'color': color}

    def _build_toolbar(self):
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #2D3748; border-radius: 8px;")
        toolbar.setFixedHeight(60)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(15, 0, 15, 0)
        
        layout.addWidget(QLabel("Filter:", styleSheet="color: #A0AEC0; font-weight: bold;"))
        
        self.stock_filter = QComboBox()
        self.stock_filter.addItems(["All", "Low Stock", "Out of Stock", "Healthy"])
        self.stock_filter.setStyleSheet("QComboBox { background-color: #1A202C; color: #FFFFFF; border: 1px solid #4A5568; border-radius: 6px; padding: 5px; }")
        self.stock_filter.currentTextChanged.connect(self._load_data)
        
        self.cat_filter = QComboBox()
        cats = ["All Categories"] + self.inventory_service.product_repo.get_categories()
        self.cat_filter.addItems(cats)
        self.cat_filter.setStyleSheet(self.stock_filter.styleSheet())
        self.cat_filter.currentTextChanged.connect(self._load_data)
        
        layout.addWidget(self.stock_filter)
        layout.addWidget(self.cat_filter)
        layout.addStretch()
        
        self.layout.addWidget(toolbar)

    def _build_table(self):
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["SKU", "Name", "Category", "Purchased", "Sold", "Balance", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1A202C; color: #E2E8F0; border: none; border-radius: 8px; font-size: 13px; }
            QHeaderView::section { background-color: #2D3748; color: #A0AEC0; font-weight: bold; border: none; padding: 8px; }
            QTableWidget::item { padding: 5px; border-bottom: 1px solid #2D3748; }
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.layout.addWidget(self.table, stretch=1)

    def _load_data(self):
        df = self.inventory_service.get_stock_status()
        
        # Summary updates
        total_val = df['inventory_value'].sum()
        total_units = df['current_stock'].sum()
        out_of_stock = len(df[df['current_stock'] <= 0])
        
        self.cards["Total Units"]['val_lbl'].setText(f"{total_units:,.0f}")
        self.cards["Stock Value"]['val_lbl'].setText(f"৳ {total_val:,.0f}")
        self.cards["SKU Count"]['val_lbl'].setText(f"{len(df)}")
        self.cards["Out of Stock"]['val_lbl'].setText(f"{out_of_stock}")
        self.cards["Out of Stock"]['val_lbl'].setStyleSheet(f"font-size: 20px; font-weight: bold; color: {'#E53E3E' if out_of_stock > 0 else '#38A169'}; background: transparent;")
        
        # Filters
        cat = self.cat_filter.currentText()
        if cat != "All Categories":
            df = df[df['category'] == cat]
            
        sf = self.stock_filter.currentText()
        
        self.table.setRowCount(0)
        for _, row in df.iterrows():
            bal = int(row['current_stock'])
            reorder = int(row['reorder_qty'] if row['reorder_qty'] == row['reorder_qty'] else 50)
            
            if sf == "Low Stock" and bal >= reorder: continue
            if sf == "Out of Stock" and bal > 0: continue
            if sf == "Healthy" and bal < reorder: continue
            
            r = self.table.rowCount()
            self.table.insertRow(r)
            
            self.table.setItem(r, 0, QTableWidgetItem(str(row['sku_code'])))
            self.table.setItem(r, 1, QTableWidgetItem(str(row['name'])))
            self.table.setItem(r, 2, QTableWidgetItem(str(row['category'])))
            self.table.setItem(r, 3, QTableWidgetItem(str(int(row.get('total_in', 0)))))
            self.table.setItem(r, 4, QTableWidgetItem(str(int(row.get('total_out', 0)))))
            
            bal_item = QTableWidgetItem(str(bal))
            if bal <= 0: bal_item.setForeground(QColor("#E53E3E"))
            elif bal < reorder: bal_item.setForeground(QColor("#DD6B20"))
            else: bal_item.setForeground(QColor("#38A169"))
            self.table.setItem(r, 5, bal_item)
            
            self.table.setItem(r, 6, QTableWidgetItem(f"৳ {row['inventory_value']:,.0f}"))
