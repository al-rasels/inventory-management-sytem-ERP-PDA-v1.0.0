from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QTableView, QHeaderView, QFrame, QComboBox)
from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtGui import QColor, QFont

class ProductTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self.headers = ["SKU", "Name", "Category", "Stock", "Price", "Status"]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = self._data.iloc[index.row()]
            col = index.column()
            
            if col == 0: return str(row['sku_code'])
            elif col == 1: return str(row['name'])
            elif col == 2: return str(row['category'])
            elif col == 3: return str(int(row['current_stock']))
            elif col == 4: return f"৳ {row['sell_price']:,.0f}"
            elif col == 5: return str(row['status'] if row['status'] else "Active")
            
        if role == Qt.ForegroundRole:
            row = self._data.iloc[index.row()]
            col = index.column()
            
            if col == 3: # Stock color
                stock = int(row['current_stock'])
                if stock <= 0: return QColor("#E53E3E")
                elif stock < 50: return QColor("#DD6B20")
                else: return QColor("#38A169")
                
        if role == Qt.TextAlignmentRole:
            if index.column() in [3, 4]:
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self.headers)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]

class PySideProducts(QWidget):
    def __init__(self, product_service, inventory_service):
        super().__init__()
        self.product_service = product_service
        self.inventory_service = inventory_service
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(15)
        
        self._build_toolbar()
        self._build_table()
        self._load_data()
        
    def _build_toolbar(self):
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #2D3748; border-radius: 8px;")
        toolbar.setFixedHeight(60)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(15, 0, 15, 0)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search products...")
        self.search_input.setFixedWidth(300)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1A202C;
                color: #FFFFFF;
                border: 1px solid #4A5568;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #3182CE; }
        """)
        self.search_input.textChanged.connect(self._load_data)
        
        # Category Filter
        self.cat_filter = QComboBox()
        self.cat_filter.setFixedWidth(200)
        self.cat_filter.setStyleSheet("""
            QComboBox {
                background-color: #1A202C;
                color: #FFFFFF;
                border: 1px solid #4A5568;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        cats = ["All Categories"] + self.product_service.repo.get_categories()
        self.cat_filter.addItems(cats)
        self.cat_filter.currentTextChanged.connect(self._load_data)
        
        # Add Button
        self.add_btn = QPushButton("+ Add Product")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #38A169;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2F855A; }
        """)
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.cat_filter)
        layout.addStretch()
        layout.addWidget(self.add_btn)
        
        self.layout.addWidget(toolbar)

    def _build_table(self):
        self.table = QTableView()
        self.table.setStyleSheet("""
            QTableView {
                background-color: #2D3748;
                color: #E2E8F0;
                gridline-color: #4A5568;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QTableView::item {
                padding: 5px;
                border-bottom: 1px solid #4A5568;
            }
            QTableView::item:selected {
                background-color: #4A5568;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #1A202C;
                color: #A0AEC0;
                font-weight: bold;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #4A5568;
            }
        """)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setShowGrid(False)
        
        self.layout.addWidget(self.table, stretch=1)
        
    def _load_data(self):
        df = self.inventory_service.get_stock_status()
        
        search_term = self.search_input.text().lower()
        if search_term:
            mask = (
                df['sku_code'].str.lower().str.contains(search_term, na=False) |
                df['name'].str.lower().str.contains(search_term, na=False)
            )
            df = df[mask]
            
        cat = self.cat_filter.currentText()
        if cat != "All Categories":
            df = df[df['category'] == cat]
            
        self.model = ProductTableModel(df)
        self.table.setModel(self.model)
