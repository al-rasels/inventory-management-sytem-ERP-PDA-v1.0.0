"""
POS Sales View — The heart of the system.
Professional point-of-sale interface with:
- Full product catalog with search and stock badges
- Real-time cart with qty adjustment and remove buttons
- Payment method selection
- Hold/Recall sale system
- Checkout confirmation dialog
"""
import json
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QSpinBox, QDoubleSpinBox, QComboBox, QSizePolicy, QStackedWidget,
    QDialog, QScrollArea, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QShortcut, QKeySequence
from src.ui.pyside.theme import Theme
from src.ui.pyside.widgets import KPICard, ConfirmDialog


class PySideSales(QWidget):
    """Professional POS Sales Interface."""
    
    sale_completed = Signal()  # Emitted after a successful sale to refresh dashboard
    
    def __init__(self, sales_service, inventory_service):
        super().__init__()
        self.sales_service = sales_service
        self.inventory_service = inventory_service
        self.cart = []
        self._all_products = None  # Cached product list
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)
        
        self._build_catalog_pane(main_layout)
        self._build_cart_pane(main_layout)
        
        # Load catalog on first show
        QTimer.singleShot(100, self._load_full_catalog)

    # ─── CATALOG (LEFT PANE) ─────────────────────────────────
    def _build_catalog_pane(self, parent_layout):
        catalog_frame = QFrame()
        catalog_frame.setStyleSheet(Theme.card_style())
        catalog_layout = QVBoxLayout(catalog_frame)
        catalog_layout.setContentsMargins(16, 16, 16, 16)
        catalog_layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("📦  Product Catalog")
        title.setStyleSheet(Theme.label_title())
        
        self.product_count_lbl = QLabel("0 products")
        self.product_count_lbl.setStyleSheet(Theme.label_muted())
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.product_count_lbl)
        catalog_layout.addLayout(header)
        
        # Search Bar (auto-focus for barcode scanner)
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Scan barcode or type product name / SKU...")
        self.search_input.setStyleSheet(Theme.input_style())
        self.search_input.setMinimumHeight(44)
        self.search_input.textChanged.connect(self._filter_catalog)
        self.search_input.returnPressed.connect(self._quick_add_first)
        
        clear_btn = QPushButton("✕")
        clear_btn.setFixedSize(44, 44)
        clear_btn.setStyleSheet(Theme.btn_ghost())
        clear_btn.setToolTip("Clear search")
        clear_btn.clicked.connect(lambda: self.search_input.clear())
        
        search_layout.addWidget(self.search_input, stretch=1)
        search_layout.addWidget(clear_btn)
        catalog_layout.addLayout(search_layout)
        
        # Category filter
        cat_layout = QHBoxLayout()
        cat_lbl = QLabel("Category:")
        cat_lbl.setStyleSheet(Theme.label_muted())
        self.cat_filter = QComboBox()
        self.cat_filter.setStyleSheet(Theme.combo_style())
        self.cat_filter.setMinimumWidth(180)
        self.cat_filter.addItem("All Categories")
        self.cat_filter.currentTextChanged.connect(self._filter_catalog)
        
        cat_layout.addWidget(cat_lbl)
        cat_layout.addWidget(self.cat_filter)
        cat_layout.addStretch()
        catalog_layout.addLayout(cat_layout)
        
        # Product Table
        self.catalog_table = QTableWidget(0, 5)
        self.catalog_table.setHorizontalHeaderLabels(["SKU", "Product Name", "Stock", "Price", ""])
        self.catalog_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.catalog_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.catalog_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.catalog_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.catalog_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.catalog_table.setColumnWidth(4, 80)
        self.catalog_table.setStyleSheet(Theme.table_style())
        self.catalog_table.verticalHeader().setVisible(False)
        self.catalog_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.catalog_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.catalog_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.catalog_table.setShowGrid(False)
        self.catalog_table.doubleClicked.connect(self._on_catalog_double_click)
        catalog_layout.addWidget(self.catalog_table, stretch=1)
        
        parent_layout.addWidget(catalog_frame, stretch=3)

    # ─── CART (RIGHT PANE) ────────────────────────────────────
    def _build_cart_pane(self, parent_layout):
        cart_frame = QFrame()
        cart_frame.setStyleSheet(Theme.card_style())
        cart_layout = QVBoxLayout(cart_frame)
        cart_layout.setContentsMargins(16, 16, 16, 16)
        cart_layout.setSpacing(12)
        
        # Cart Header
        cart_header = QHBoxLayout()
        cart_title = QLabel("🛒  Current Sale")
        cart_title.setStyleSheet(Theme.label_title())
        
        self.cart_badge = QLabel("0 items")
        self.cart_badge.setStyleSheet(Theme.badge_style(Theme.ACCENT))
        
        hold_btn = QPushButton("⏸ Hold")
        hold_btn.setStyleSheet(Theme.btn_ghost())
        hold_btn.setToolTip("Hold this sale and start a new one")
        hold_btn.clicked.connect(self._hold_sale)
        
        recall_btn = QPushButton("▶ Recall")
        recall_btn.setStyleSheet(Theme.btn_ghost())
        recall_btn.setToolTip("Recall a held sale")
        recall_btn.clicked.connect(self._recall_sale)
        
        cart_header.addWidget(cart_title)
        cart_header.addWidget(self.cart_badge)
        cart_header.addStretch()
        cart_header.addWidget(hold_btn)
        cart_header.addWidget(recall_btn)
        cart_layout.addLayout(cart_header)
        
        # Customer
        cust_layout = QHBoxLayout()
        cust_lbl = QLabel("Customer:")
        cust_lbl.setStyleSheet(Theme.label_muted())
        self.customer_input = QLineEdit("Walk-in Customer")
        self.customer_input.setStyleSheet(Theme.input_style())
        cust_layout.addWidget(cust_lbl)
        cust_layout.addWidget(self.customer_input, stretch=1)
        cart_layout.addLayout(cust_layout)
        
        # Cart Table
        self.cart_table = QTableWidget(0, 5)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Qty", "Price", "Total", ""])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.cart_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.cart_table.setColumnWidth(1, 75)
        self.cart_table.setColumnWidth(4, 40)
        self.cart_table.setStyleSheet(Theme.table_style())
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cart_table.setShowGrid(False)
        cart_layout.addWidget(self.cart_table, stretch=1)
        
        # Totals Panel
        totals_frame = QFrame()
        totals_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_PRIMARY};
                border-radius: {Theme.RADIUS_MD};
                border: 1px solid {Theme.BORDER};
            }}
        """)
        t_layout = QVBoxLayout(totals_frame)
        t_layout.setContentsMargins(14, 12, 14, 12)
        t_layout.setSpacing(8)
        
        # Subtotal
        sub_row = QHBoxLayout()
        sub_row.addWidget(QLabel("Subtotal", styleSheet=Theme.label_muted()))
        self.subtotal_lbl = QLabel("৳ 0")
        self.subtotal_lbl.setStyleSheet(f"font-size: 15px; color: {Theme.TEXT_SECONDARY}; font-weight: 500; border: none; background: transparent;")
        self.subtotal_lbl.setAlignment(Qt.AlignRight)
        sub_row.addWidget(self.subtotal_lbl)
        t_layout.addLayout(sub_row)
        
        # Discount
        disc_row = QHBoxLayout()
        disc_row.addWidget(QLabel("Discount %", styleSheet=Theme.label_muted()))
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 100)
        self.discount_spin.setFixedWidth(90)
        self.discount_spin.setStyleSheet(Theme.spin_style())
        self.discount_spin.valueChanged.connect(self._update_totals)
        disc_row.addStretch()
        disc_row.addWidget(self.discount_spin)
        t_layout.addLayout(disc_row)
        
        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {Theme.BORDER};")
        t_layout.addWidget(divider)
        
        # Grand Total
        total_row = QHBoxLayout()
        total_lbl_left = QLabel("TOTAL")
        total_lbl_left.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.TEXT_PRIMARY}; border: none; background: transparent;")
        self.total_lbl = QLabel("৳ 0")
        self.total_lbl.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {Theme.SUCCESS}; border: none; background: transparent;")
        self.total_lbl.setAlignment(Qt.AlignRight)
        total_row.addWidget(total_lbl_left)
        total_row.addWidget(self.total_lbl)
        t_layout.addLayout(total_row)
        
        cart_layout.addWidget(totals_frame)
        
        # Payment Method
        pay_layout = QHBoxLayout()
        pay_lbl = QLabel("Payment:")
        pay_lbl.setStyleSheet(Theme.label_muted())
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["💵 Cash", "💳 Card", "📱 Mobile Banking"])
        self.payment_combo.setStyleSheet(Theme.combo_style())
        pay_layout.addWidget(pay_lbl)
        pay_layout.addWidget(self.payment_combo, stretch=1)
        cart_layout.addLayout(pay_layout)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        clear_btn = QPushButton("🗑 Clear")
        clear_btn.setStyleSheet(Theme.btn_danger())
        clear_btn.setFixedHeight(48)
        clear_btn.clicked.connect(self._clear_cart)
        
        checkout_btn = QPushButton("✅  Complete Sale")
        checkout_btn.setStyleSheet(Theme.btn_success())
        checkout_btn.setFixedHeight(48)
        font = checkout_btn.font()
        font.setPointSize(14)
        font.setBold(True)
        checkout_btn.setFont(font)
        checkout_btn.clicked.connect(self._checkout)
        
        btn_layout.addWidget(clear_btn, stretch=1)
        btn_layout.addWidget(checkout_btn, stretch=3)
        cart_layout.addLayout(btn_layout)
        
        parent_layout.addWidget(cart_frame, stretch=2)

    # ─── CATALOG LOGIC ────────────────────────────────────────
    def _load_full_catalog(self):
        """Load all products with stock info."""
        try:
            df = self.inventory_service.get_stock_status()
            self._all_products = df
            
            # Load categories
            cats = sorted(df['category'].dropna().unique().tolist())
            self.cat_filter.blockSignals(True)
            self.cat_filter.clear()
            self.cat_filter.addItem("All Categories")
            self.cat_filter.addItems(cats)
            self.cat_filter.blockSignals(False)
            
            self._render_catalog(df)
        except Exception as e:
            self.product_count_lbl.setText(f"Error: {e}")
    
    def _filter_catalog(self):
        """Filter catalog by search text and category."""
        if self._all_products is None:
            return
        
        df = self._all_products.copy()
        
        # Category filter
        cat = self.cat_filter.currentText()
        if cat and cat != "All Categories":
            df = df[df['category'] == cat]
        
        # Text search
        term = self.search_input.text().strip().lower()
        if term:
            mask = (
                df['sku_code'].str.lower().str.contains(term, na=False) |
                df['name'].str.lower().str.contains(term, na=False) |
                df['product_id'].str.lower().str.contains(term, na=False)
            )
            df = df[mask]
        
        self._render_catalog(df)
    
    def _render_catalog(self, df):
        """Render product catalog table."""
        self.catalog_table.setRowCount(0)
        self.product_count_lbl.setText(f"{len(df)} products")
        
        for _, row in df.iterrows():
            r = self.catalog_table.rowCount()
            self.catalog_table.insertRow(r)
            
            # SKU
            sku_item = QTableWidgetItem(str(row['sku_code']))
            sku_item.setForeground(QColor(Theme.TEXT_ACCENT))
            self.catalog_table.setItem(r, 0, sku_item)
            
            # Name
            self.catalog_table.setItem(r, 1, QTableWidgetItem(str(row['name'])))
            
            # Stock with color coding
            stock = int(row['current_stock'])
            reorder = int(row['reorder_qty'] if row['reorder_qty'] == row['reorder_qty'] else 50)
            stock_item = QTableWidgetItem(str(stock))
            stock_item.setTextAlignment(Qt.AlignCenter)
            if stock <= 0:
                stock_item.setForeground(QColor(Theme.DANGER))
            elif stock < reorder:
                stock_item.setForeground(QColor(Theme.WARNING))
            else:
                stock_item.setForeground(QColor(Theme.SUCCESS))
            self.catalog_table.setItem(r, 2, stock_item)
            
            # Price
            price_item = QTableWidgetItem(f"৳ {row['sell_price']:,.0f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.catalog_table.setItem(r, 3, price_item)
            
            # Add button
            add_btn = QPushButton("+ Add")
            add_btn.setStyleSheet(Theme.btn_icon_primary())
            add_btn.setCursor(Qt.PointingHandCursor)
            if stock <= 0:
                add_btn.setEnabled(False)
                add_btn.setText("—")
                add_btn.setToolTip("Out of stock")
            else:
                add_btn.clicked.connect(lambda ch, p=row.to_dict(): self._add_to_cart(p))
            self.catalog_table.setCellWidget(r, 4, add_btn)
        
        self.catalog_table.setRowCount(self.catalog_table.rowCount())  # Force layout refresh
    
    def _on_catalog_double_click(self, index):
        """Double-click a catalog row to add to cart."""
        row = index.row()
        sku = self.catalog_table.item(row, 0)
        if sku and self._all_products is not None:
            sku_val = sku.text()
            match = self._all_products[self._all_products['sku_code'] == sku_val]
            if not match.empty:
                self._add_to_cart(match.iloc[0].to_dict())
    
    def _quick_add_first(self):
        """On Enter in search, add the first visible product."""
        if self.catalog_table.rowCount() > 0:
            sku = self.catalog_table.item(0, 0)
            if sku and self._all_products is not None:
                sku_val = sku.text()
                match = self._all_products[self._all_products['sku_code'] == sku_val]
                if not match.empty:
                    self._add_to_cart(match.iloc[0].to_dict())
                    self.search_input.clear()

    # ─── CART LOGIC ───────────────────────────────────────────
    def _add_to_cart(self, product):
        """Add product to cart with stock validation."""
        pid = product['product_id']
        stock = int(product.get('current_stock', 0))
        
        # Check current qty in cart
        current_in_cart = 0
        for item in self.cart:
            if item['product_id'] == pid:
                current_in_cart = item['qty']
                break
        
        if current_in_cart + 1 > stock:
            QMessageBox.warning(self, "Stock Limit",
                                f"Cannot add more — only {stock} units available for '{product['name']}'.")
            return
        
        # Update existing or add new
        for item in self.cart:
            if item['product_id'] == pid:
                item['qty'] += 1
                self._render_cart()
                return
        
        self.cart.append({
            'product_id': pid,
            'name': product['name'],
            'price': float(product['sell_price']),
            'qty': 1,
            'max_stock': stock
        })
        self._render_cart()
    
    def _render_cart(self):
        """Render cart table with qty spinners and remove buttons."""
        self.cart_table.setRowCount(0)
        
        for i, item in enumerate(self.cart):
            self.cart_table.insertRow(i)
            
            # Product name
            name_item = QTableWidgetItem(item['name'])
            name_item.setForeground(QColor(Theme.TEXT_PRIMARY))
            self.cart_table.setItem(i, 0, name_item)
            
            # Qty spinner
            qty_spin = QSpinBox()
            qty_spin.setRange(1, item.get('max_stock', 999))
            qty_spin.setValue(item['qty'])
            qty_spin.setStyleSheet(f"""
                QSpinBox {{
                    background-color: {Theme.BG_TERTIARY};
                    color: {Theme.TEXT_PRIMARY};
                    border: none;
                    border-radius: 4px;
                    padding: 4px;
                    font-size: 14px;
                    font-weight: bold;
                }}
            """)
            qty_spin.valueChanged.connect(lambda v, idx=i: self._update_qty(idx, v))
            self.cart_table.setCellWidget(i, 1, qty_spin)
            
            # Unit price
            price_item = QTableWidgetItem(f"৳ {item['price']:,.0f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            price_item.setForeground(QColor(Theme.TEXT_SECONDARY))
            self.cart_table.setItem(i, 2, price_item)
            
            # Line total
            total = item['price'] * item['qty']
            total_item = QTableWidgetItem(f"৳ {total:,.0f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            total_item.setForeground(QColor(Theme.TEXT_PRIMARY))
            font = total_item.font()
            font.setBold(True)
            total_item.setFont(font)
            self.cart_table.setItem(i, 3, total_item)
            
            # Remove button
            rm_btn = QPushButton("✕")
            rm_btn.setStyleSheet(Theme.btn_icon_danger())
            rm_btn.setCursor(Qt.PointingHandCursor)
            rm_btn.setToolTip("Remove item")
            rm_btn.clicked.connect(lambda ch, idx=i: self._remove_item(idx))
            self.cart_table.setCellWidget(i, 4, rm_btn)
        
        self._update_totals()
        self.cart_badge.setText(f"{sum(i['qty'] for i in self.cart)} items")
    
    def _update_qty(self, idx, val):
        if 0 <= idx < len(self.cart):
            self.cart[idx]['qty'] = val
            # Update line total in-place without full re-render
            total = self.cart[idx]['price'] * val
            total_item = self.cart_table.item(idx, 3)
            if total_item:
                total_item.setText(f"৳ {total:,.0f}")
            self._update_totals()
    
    def _remove_item(self, idx):
        if 0 <= idx < len(self.cart):
            self.cart.pop(idx)
            self._render_cart()
    
    def _clear_cart(self):
        if not self.cart:
            return
        dlg = ConfirmDialog("Clear Cart", "Remove all items from the current sale?",
                            confirm_text="Clear All", confirm_color="danger", parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.cart = []
            self.customer_input.setText("Walk-in Customer")
            self.discount_spin.setValue(0)
            self._render_cart()
    
    def _update_totals(self):
        subtotal = sum(i['qty'] * i['price'] for i in self.cart)
        disc = self.discount_spin.value()
        total = subtotal * (1 - disc / 100)
        
        self.subtotal_lbl.setText(f"৳ {subtotal:,.0f}")
        self.total_lbl.setText(f"৳ {total:,.0f}")

    # ─── CHECKOUT ─────────────────────────────────────────────
    def _checkout(self):
        if not self.cart:
            QMessageBox.warning(self, "Empty Cart", "Add products to the cart before checkout.")
            return
        
        subtotal = sum(i['qty'] * i['price'] for i in self.cart)
        disc = self.discount_spin.value()
        total = subtotal * (1 - disc / 100)
        payment = self.payment_combo.currentText()
        
        # Confirmation dialog
        items_summary = "\n".join([f"  • {i['name']} × {i['qty']}  =  ৳ {i['price']*i['qty']:,.0f}" for i in self.cart])
        dlg = ConfirmDialog(
            "Confirm Sale",
            f"Complete sale for {self.customer_input.text()}?",
            f"Items: {len(self.cart)} | Payment: {payment}\nTotal: ৳ {total:,.0f}",
            confirm_text="Complete Sale ✓",
            confirm_color="success",
            parent=self
        )
        
        if dlg.exec() != QDialog.Accepted:
            return
        
        from src.services.types import CartItem
        items = [CartItem(i['product_id'], i['name'], i['qty'], i['price'], i['price'] * i['qty']) for i in self.cart]
        
        # Extract clean payment method
        payment_clean = payment.split(" ", 1)[1] if " " in payment else payment
        
        try:
            res = self.sales_service.complete_sale(
                items, self.customer_input.text(),
                self.discount_spin.value(), payment_clean
            )
            if res.success:
                QMessageBox.information(self, "Sale Complete ✓",
                    f"Sale recorded successfully!\n\n"
                    f"Invoice: {res.sale_ids[0] if res.sale_ids else 'N/A'}\n"
                    f"Revenue: ৳ {res.total_revenue:,.0f}\n"
                    f"Profit: ৳ {res.total_profit:,.0f}")
                self.cart = []
                self.customer_input.setText("Walk-in Customer")
                self.discount_spin.setValue(0)
                self._render_cart()
                self._load_full_catalog()  # Refresh stock
                self.sale_completed.emit()
            else:
                QMessageBox.warning(self, "Sale Failed", "\n".join(res.errors))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    # ─── HOLD / RECALL ────────────────────────────────────────
    def _hold_sale(self):
        """Park the current cart for later."""
        if not self.cart:
            QMessageBox.information(self, "Nothing to Hold", "Cart is empty.")
            return
        
        hold_id = f"HOLD-{datetime.now().strftime('%H%M%S')}"
        cart_json = json.dumps(self.cart)
        
        try:
            self.sales_service.repo.db.execute_write(
                "INSERT INTO held_sales (hold_id, customer, cart_json, discount, note) VALUES (?, ?, ?, ?, ?)",
                (hold_id, self.customer_input.text(), cart_json, self.discount_spin.value(), "")
            )
            QMessageBox.information(self, "Sale Held ⏸", f"Sale parked as {hold_id}.\nYou can recall it anytime.")
            self.cart = []
            self.customer_input.setText("Walk-in Customer")
            self.discount_spin.setValue(0)
            self._render_cart()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def _recall_sale(self):
        """Recall a held sale."""
        try:
            db = self.sales_service.repo.db
            df = db.execute_query("SELECT * FROM held_sales ORDER BY created_at DESC LIMIT 10")
            
            if df.empty:
                QMessageBox.information(self, "No Held Sales", "There are no parked sales to recall.")
                return
            
            # Show selection dialog
            from PySide6.QtWidgets import QInputDialog
            items = [f"{row['hold_id']} — {row['customer']} ({row['created_at'][:16]})" for _, row in df.iterrows()]
            choice, ok = QInputDialog.getItem(self, "Recall Sale", "Select a held sale:", items, 0, False)
            
            if ok and choice:
                hold_id = choice.split(" — ")[0]
                row = df[df['hold_id'] == hold_id].iloc[0]
                
                self.cart = json.loads(row['cart_json'])
                self.customer_input.setText(row['customer'])
                self.discount_spin.setValue(float(row['discount']))
                self._render_cart()
                
                # Remove from held
                db.execute_write("DELETE FROM held_sales WHERE hold_id = ?", (hold_id,))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def refresh(self):
        """Called when navigating to this view."""
        self._load_full_catalog()
        self.search_input.setFocus()
