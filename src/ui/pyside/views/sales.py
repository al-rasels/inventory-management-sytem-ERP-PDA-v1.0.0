from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QMessageBox, QSpinBox, QDoubleSpinBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class PySideSales(QWidget):
    def __init__(self, sales_service, inventory_service):
        super().__init__()
        self.sales_service = sales_service
        self.inventory_service = inventory_service
        self.cart = []
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(20)
        
        self._build_catalog_pane()
        self._build_cart_pane()
        
    def _build_catalog_pane(self):
        catalog_frame = QFrame()
        catalog_frame.setStyleSheet("background-color: #2D3748; border-radius: 12px;")
        catalog_layout = QVBoxLayout(catalog_frame)
        
        title = QLabel("📦 Product Search")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #F7FAFC;")
        catalog_layout.addWidget(title)
        
        # Search Box
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Scan SKU or enter product name...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1A202C; color: #FFFFFF;
                border: 1px solid #4A5568; border-radius: 6px;
                padding: 10px; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #3182CE; }
        """)
        self.search_input.returnPressed.connect(self._search_product)
        
        search_btn = QPushButton("Search")
        search_btn.setStyleSheet("""
            QPushButton { background-color: #3182CE; color: white; border-radius: 6px; padding: 10px 20px; font-weight: bold; }
            QPushButton:hover { background-color: #2B6CB0; }
        """)
        search_btn.clicked.connect(self._search_product)
        
        search_layout.addWidget(self.search_input, stretch=1)
        search_layout.addWidget(search_btn)
        catalog_layout.addLayout(search_layout)
        
        # Results Table
        self.catalog_table = QTableWidget(0, 5)
        self.catalog_table.setHorizontalHeaderLabels(["SKU", "Name", "Stock", "Price", "Action"])
        self.catalog_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.catalog_table.setStyleSheet("""
            QTableWidget { background-color: #1A202C; color: #E2E8F0; border: none; border-radius: 8px; font-size: 13px; }
            QHeaderView::section { background-color: #2D3748; color: #A0AEC0; font-weight: bold; border: none; padding: 8px; }
            QTableWidget::item { padding: 5px; border-bottom: 1px solid #2D3748; }
        """)
        self.catalog_table.verticalHeader().setVisible(False)
        self.catalog_table.setEditTriggers(QTableWidget.NoEditTriggers)
        catalog_layout.addWidget(self.catalog_table, stretch=1)
        
        self.layout.addWidget(catalog_frame, stretch=2)

    def _build_cart_pane(self):
        cart_frame = QFrame()
        cart_frame.setStyleSheet("background-color: #2D3748; border-radius: 12px;")
        cart_layout = QVBoxLayout(cart_frame)
        
        title = QLabel("🛒 Current Sale")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #F7FAFC;")
        cart_layout.addWidget(title)
        
        # Customer Info
        self.customer_input = QLineEdit("Walk-in Customer")
        self.customer_input.setStyleSheet("""
            QLineEdit { background-color: #1A202C; color: #FFFFFF; border: 1px solid #4A5568; border-radius: 6px; padding: 8px; }
        """)
        cart_layout.addWidget(QLabel("Customer Name:"))
        cart_layout.addWidget(self.customer_input)
        
        # Cart Table
        self.cart_table = QTableWidget(0, 4)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Qty", "Price", "Total"])
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cart_table.setStyleSheet(self.catalog_table.styleSheet())
        self.cart_table.verticalHeader().setVisible(False)
        cart_layout.addWidget(self.cart_table, stretch=1)
        
        # Totals
        totals_frame = QFrame()
        totals_frame.setStyleSheet("background-color: #1A202C; border-radius: 8px;")
        t_layout = QVBoxLayout(totals_frame)
        
        self.subtotal_lbl = QLabel("Subtotal: ৳ 0")
        self.subtotal_lbl.setStyleSheet("font-size: 14px; color: #A0AEC0;")
        
        disc_layout = QHBoxLayout()
        disc_layout.addWidget(QLabel("Discount (%):", styleSheet="color: #A0AEC0;"))
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 100)
        self.discount_spin.setStyleSheet("background-color: #2D3748; color: white; padding: 5px;")
        self.discount_spin.valueChanged.connect(self._update_totals)
        disc_layout.addWidget(self.discount_spin)
        
        self.total_lbl = QLabel("Total: ৳ 0")
        self.total_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #38A169;")
        
        t_layout.addWidget(self.subtotal_lbl)
        t_layout.addLayout(disc_layout)
        t_layout.addWidget(self.total_lbl)
        cart_layout.addWidget(totals_frame)
        
        # Checkout Button
        checkout_btn = QPushButton("Complete Sale")
        checkout_btn.setStyleSheet("""
            QPushButton { background-color: #38A169; color: white; border-radius: 8px; padding: 15px; font-weight: bold; font-size: 16px; }
            QPushButton:hover { background-color: #2F855A; }
        """)
        checkout_btn.clicked.connect(self._checkout)
        cart_layout.addWidget(checkout_btn)
        
        self.layout.addWidget(cart_frame, stretch=1)

    def _search_product(self):
        term = self.search_input.text().strip()
        if not term: return
        
        df = self.inventory_service.product_repo.search(term)
        self.catalog_table.setRowCount(0)
        
        for _, row in df.iterrows():
            r = self.catalog_table.rowCount()
            self.catalog_table.insertRow(r)
            
            self.catalog_table.setItem(r, 0, QTableWidgetItem(str(row['sku_code'])))
            self.catalog_table.setItem(r, 1, QTableWidgetItem(str(row['name'])))
            
            stock = int(row['current_stock'] if 'current_stock' in row else 0)
            stock_item = QTableWidgetItem(str(stock))
            stock_item.setForeground(QColor("#38A169") if stock > 0 else QColor("#E53E3E"))
            self.catalog_table.setItem(r, 2, stock_item)
            
            self.catalog_table.setItem(r, 3, QTableWidgetItem(f"৳ {row['sell_price']:.0f}"))
            
            add_btn = QPushButton("+ Add")
            add_btn.setStyleSheet("background-color: #4299E1; color: white; border-radius: 4px; padding: 4px;")
            add_btn.clicked.connect(lambda ch, p=row: self._add_to_cart(p))
            self.catalog_table.setCellWidget(r, 4, add_btn)

    def _add_to_cart(self, product):
        pid = product['product_id']
        for item in self.cart:
            if item['product_id'] == pid:
                item['qty'] += 1
                self._render_cart()
                return
                
        self.cart.append({
            'product_id': pid,
            'name': product['name'],
            'price': float(product['sell_price']),
            'qty': 1
        })
        self._render_cart()

    def _render_cart(self):
        self.cart_table.setRowCount(0)
        for i, item in enumerate(self.cart):
            self.cart_table.insertRow(i)
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['name']))
            
            qty_spin = QSpinBox()
            qty_spin.setRange(0, 999)
            qty_spin.setValue(item['qty'])
            qty_spin.setStyleSheet("background-color: transparent; color: white;")
            qty_spin.valueChanged.connect(lambda v, idx=i: self._update_qty(idx, v))
            self.cart_table.setCellWidget(i, 1, qty_spin)
            
            self.cart_table.setItem(i, 2, QTableWidgetItem(f"৳ {item['price']:.0f}"))
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"৳ {item['price'] * item['qty']:.0f}"))
            
        self._update_totals()

    def _update_qty(self, idx, val):
        if val == 0:
            self.cart.pop(idx)
        else:
            self.cart[idx]['qty'] = val
        self._render_cart()

    def _update_totals(self):
        subtotal = sum(i['qty'] * i['price'] for i in self.cart)
        disc = self.discount_spin.value()
        total = subtotal * (1 - disc/100)
        
        self.subtotal_lbl.setText(f"Subtotal: ৳ {subtotal:,.0f}")
        self.total_lbl.setText(f"Total: ৳ {total:,.0f}")

    def _checkout(self):
        if not self.cart:
            QMessageBox.warning(self, "Error", "Cart is empty")
            return
            
        from src.services.types import CartItem
        items = [CartItem(i['product_id'], i['name'], i['qty'], i['price'], i['price']*i['qty']) for i in self.cart]
        
        try:
            res = self.sales_service.complete_sale(items, self.customer_input.text(), self.discount_spin.value())
            if res.success:
                QMessageBox.information(self, "Success", f"Sale completed! Total: ৳ {res.total_revenue:,.0f}")
                self.cart = []
                self.customer_input.setText("Walk-in Customer")
                self.discount_spin.setValue(0)
                self._render_cart()
            else:
                QMessageBox.warning(self, "Failed", "\n".join(res.errors))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
