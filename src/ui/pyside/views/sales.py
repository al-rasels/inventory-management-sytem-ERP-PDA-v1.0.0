"""
POS Sales View — Professional point‑of‑sale interface.

Uses QtAwesome for all icons, background catalog loading, and robust error handling.
All row heights, button closures, and signal blocking issues resolved.
"""
from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from PySide6.QtCore import (
    Qt, QThread, Signal, Slot, QTimer
)
from PySide6.QtGui import QShortcut, QKeySequence, QStandardItemModel, QStandardItem, QColor, QIcon, QAction, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QSpinBox, QDoubleSpinBox, QComboBox, QAbstractItemView, QDialog,
    QProgressBar, QStackedWidget, QTextEdit, QApplication, QStyle,
    QTableView, QInputDialog, QFileDialog
)
from qtawesome import icon as qta_icon

from src.ui.pyside.theme import Theme
from src.ui.pyside.widgets import ConfirmDialog

logger = logging.getLogger(__name__)


# =====================================================================
# Background worker – loads the full product catalog
# =====================================================================
class CatalogWorker(QThread):
    """Loads the inventory snapshot in a background thread."""
    data_ready = Signal(object)   # pandas DataFrame
    error_occurred = Signal(str)

    def __init__(self, inventory_service):
        super().__init__()
        self.inventory_service = inventory_service

    def run(self):
        try:
            df = self.inventory_service.get_stock_status()
            self.data_ready.emit(df)
        except Exception as e:
            logger.exception("Catalog worker failed")
            self.error_occurred.emit(str(e))


# =====================================================================
# Main POS Sales Widget
# =====================================================================
class PySideSales(QWidget):
    """Professional POS Sales Interface."""

    sale_completed = Signal()  # Emitted after a successful sale

    def __init__(self, sales_service, inventory_service, parent=None):
        super().__init__(parent)
        self.sales_service = sales_service
        self.inventory_service = inventory_service
        self.cart: List[Dict[str, Any]] = []
        self._all_products = None          # Full DataFrame
        self._catalog_model: Optional[QStandardItemModel] = None
        self._catalog_worker: Optional[CatalogWorker] = None

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        # Left – catalog pane (with loading/error overlay)
        self._build_catalog_pane(main_layout)
        # Right – cart pane
        self._build_cart_pane(main_layout)

        # Keyboard shortcuts
        self._setup_shortcuts()

        # Load catalog on first show (delayed to let UI paint first)
        QTimer.singleShot(50, self.refresh)

    # ----- Shortcuts ------------------------------------------------------
    def _setup_shortcuts(self):
        refresh_sc = QShortcut(QKeySequence("F5"), self)
        refresh_sc.activated.connect(self.refresh)

        focus_sc = QShortcut(QKeySequence("Ctrl+F"), self)
        focus_sc.activated.connect(lambda: self.search_input.setFocus())

        export_sc = QShortcut(QKeySequence("Ctrl+E"), self)
        export_sc.activated.connect(self.export_catalog_csv)

    # ─── CATALOG PANE (LEFT) ──────────────────────────────────────────────
    def _build_catalog_pane(self, parent_layout):
        """Build the catalog panel with stacked loading/table/error."""
        catalog_frame = QFrame()
        catalog_frame.setStyleSheet(Theme.card_style())
        catalog_layout = QVBoxLayout(catalog_frame)
        catalog_layout.setContentsMargins(16, 16, 16, 16)
        catalog_layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(qta_icon('fa5s.box', color=Theme.TEXT_PRIMARY).pixmap(18, 18))
        header.addWidget(title_icon)

        title = QLabel("Product Catalog")
        title.setStyleSheet(Theme.label_title())
        header.addWidget(title)
        header.addStretch()

        self.product_count_lbl = QLabel("0 products")
        self.product_count_lbl.setStyleSheet(Theme.label_muted())
        header.addWidget(self.product_count_lbl)

        # Refresh button
        refresh_btn = QPushButton()
        refresh_btn.setIcon(qta_icon('fa5s.sync-alt', color='white'))
        refresh_btn.setToolTip("Refresh catalog (F5)")
        refresh_btn.setStyleSheet(
            f"QPushButton {{ background: {Theme.ACCENT}; border-radius: {Theme.RADIUS_SM}; padding: 4px; }}"
        )
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)

        # Export button
        export_btn = QPushButton()
        export_btn.setIcon(qta_icon('fa5s.file-csv', color='white'))
        export_btn.setToolTip("Export catalog (Ctrl+E)")
        export_btn.setStyleSheet(
            f"QPushButton {{ background: {Theme.ACCENT}; border-radius: {Theme.RADIUS_SM}; padding: 4px; }}"
        )
        export_btn.clicked.connect(self.export_catalog_csv)
        header.addWidget(export_btn)

        catalog_layout.addLayout(header)

        # Search row
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Scan barcode or type product name / SKU...")
        self.search_input.setStyleSheet(Theme.input_style())
        self.search_input.setMinimumHeight(44)
        # Add search icon inside field
        search_action = QAction(
            qta_icon('fa5s.search', color=Theme.TEXT_MUTED),
            "", self.search_input
        )
        self.search_input.addAction(search_action, QLineEdit.LeadingPosition)
        self.search_input.textChanged.connect(self._filter_catalog)
        self.search_input.returnPressed.connect(self._quick_add_first)

        clear_btn = QPushButton()
        clear_btn.setIcon(qta_icon('fa5s.times', color=Theme.TEXT_MUTED))
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

        # Stacked widget for catalog content
        self.catalog_stack = QStackedWidget()
        catalog_layout.addWidget(self.catalog_stack, stretch=1)

        # Page 0: Table view
        self.catalog_table = QTableView()
        self.catalog_table.setStyleSheet(Theme.tableview_style())
        self.catalog_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.catalog_table.verticalHeader().setVisible(False)
        self.catalog_table.verticalHeader().setDefaultSectionSize(38)   # ⬅ row height for Add buttons
        self.catalog_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.catalog_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.catalog_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.catalog_table.setShowGrid(False)
        self.catalog_table.doubleClicked.connect(self._on_catalog_double_click)
        self.catalog_stack.addWidget(self.catalog_table)

        # Page 1: Loading
        loading_widget = QWidget()
        loading_layout = QVBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignCenter)
        loading_lbl = QLabel("Loading catalog...")
        loading_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 16px;")
        loading_layout.addWidget(loading_lbl)
        progress = QProgressBar()
        progress.setRange(0, 0)
        progress.setFixedWidth(250)
        loading_layout.addWidget(progress, alignment=Qt.AlignCenter)
        self.catalog_stack.addWidget(loading_widget)

        # Page 2: Error
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        error_layout.setAlignment(Qt.AlignCenter)
        icon_label = QLabel()
        icon_label.setPixmap(
            self.style().standardIcon(QStyle.SP_MessageBoxCritical).pixmap(32, 32)
        )
        icon_label.setAlignment(Qt.AlignCenter)
        error_layout.addWidget(icon_label)
        self.catalog_error_label = QLabel()
        self.catalog_error_label.setAlignment(Qt.AlignCenter)
        self.catalog_error_label.setStyleSheet(f"color: {Theme.DANGER}; font-weight: bold;")
        error_layout.addWidget(self.catalog_error_label)
        self.catalog_error_detail = QTextEdit()
        self.catalog_error_detail.setReadOnly(True)
        self.catalog_error_detail.setMaximumHeight(80)
        self.catalog_error_detail.setVisible(False)
        error_layout.addWidget(self.catalog_error_detail)
        retry_btn = QPushButton("Retry")
        retry_btn.clicked.connect(self.refresh)
        error_layout.addWidget(retry_btn, alignment=Qt.AlignCenter)
        self.catalog_stack.addWidget(error_widget)

        parent_layout.addWidget(catalog_frame, stretch=3)

    # ─── CART PANE (RIGHT) ────────────────────────────────────────────────
    def _build_cart_pane(self, parent_layout):
        cart_frame = QFrame()
        cart_frame.setStyleSheet(Theme.card_style())
        cart_layout = QVBoxLayout(cart_frame)
        cart_layout.setContentsMargins(16, 16, 16, 16)
        cart_layout.setSpacing(12)

        # Cart header
        cart_header = QHBoxLayout()
        cart_icon = QLabel()
        cart_icon.setPixmap(qta_icon('fa5s.shopping-cart', color=Theme.TEXT_PRIMARY).pixmap(18, 18))
        cart_header.addWidget(cart_icon)
        cart_title = QLabel("Current Sale")
        cart_title.setStyleSheet(Theme.label_title())
        cart_header.addWidget(cart_title)

        self.cart_badge = QLabel("0 items")
        self.cart_badge.setStyleSheet(Theme.badge_style(Theme.ACCENT))
        cart_header.addWidget(self.cart_badge)
        cart_header.addStretch()

        hold_btn = QPushButton()
        hold_btn.setIcon(qta_icon('fa5s.pause', color=Theme.TEXT_PRIMARY))
        hold_btn.setText(" Hold")
        hold_btn.setStyleSheet(Theme.btn_ghost())
        hold_btn.setToolTip("Hold this sale")
        hold_btn.clicked.connect(self._hold_sale)
        cart_header.addWidget(hold_btn)

        recall_btn = QPushButton()
        recall_btn.setIcon(qta_icon('fa5s.play', color=Theme.TEXT_PRIMARY))
        recall_btn.setText(" Recall")
        recall_btn.setStyleSheet(Theme.btn_ghost())
        recall_btn.setToolTip("Recall a held sale")
        recall_btn.clicked.connect(self._recall_sale)
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

        # Cart table (still QTableWidget for cell widgets)
        self.cart_table = QTableWidget(0, 5)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Qty", "Price", "Total", ""])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.cart_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.cart_table.setColumnWidth(1, 75)
        self.cart_table.setColumnWidth(4, 36)                     # ⬅ adjusted for smaller remove button
        self.cart_table.setStyleSheet(Theme.table_style())
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.verticalHeader().setDefaultSectionSize(44)   # ⬅ row height
        self.cart_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cart_table.setShowGrid(False)
        cart_layout.addWidget(self.cart_table, stretch=1)

        # Totals panel
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

        sub_row = QHBoxLayout()
        sub_row.addWidget(QLabel("Subtotal", styleSheet=Theme.label_muted()))
        self.subtotal_lbl = QLabel("৳ 0")
        self.subtotal_lbl.setStyleSheet(f"font-size: 15px; color: {Theme.TEXT_SECONDARY}; border: none; background: transparent;")
        sub_row.addWidget(self.subtotal_lbl)
        t_layout.addLayout(sub_row)

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

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {Theme.BORDER};")
        t_layout.addWidget(divider)

        total_row = QHBoxLayout()
        total_lbl_left = QLabel("TOTAL")
        total_lbl_left.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.TEXT_PRIMARY}; border: none; background: transparent;")
        self.total_lbl = QLabel("৳ 0")
        self.total_lbl.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {Theme.SUCCESS}; border: none; background: transparent;")
        total_row.addWidget(total_lbl_left)
        total_row.addWidget(self.total_lbl)
        t_layout.addLayout(total_row)

        cart_layout.addWidget(totals_frame)

        # Payment method
        pay_layout = QHBoxLayout()
        pay_lbl = QLabel("Payment:")
        pay_lbl.setStyleSheet(Theme.label_muted())
        self.payment_combo = QComboBox()
        self.payment_combo.addItem(qta_icon('fa5s.money-bill', color=Theme.SUCCESS), "Cash")
        self.payment_combo.addItem(qta_icon('fa5s.credit-card', color=Theme.ACCENT), "Card")
        self.payment_combo.addItem(qta_icon('fa5s.mobile-alt', color=Theme.PURPLE), "Mobile Banking")
        self.payment_combo.setStyleSheet(Theme.combo_style())
        pay_layout.addWidget(pay_lbl)
        pay_layout.addWidget(self.payment_combo, stretch=1)
        cart_layout.addLayout(pay_layout)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        clear_btn = QPushButton()
        clear_btn.setIcon(qta_icon('fa5s.trash-alt', color='white'))
        clear_btn.setText(" Clear")
        clear_btn.setStyleSheet(Theme.btn_danger())
        clear_btn.setFixedHeight(48)
        clear_btn.clicked.connect(self._clear_cart)

        checkout_btn = QPushButton()
        checkout_btn.setIcon(qta_icon('fa5s.check-circle', color='white'))
        checkout_btn.setText(" Complete Sale")
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

    # ─── CATALOG LOADING & RENDERING ─────────────────────────────────────
    def refresh(self):
        """Reload the full catalog from the inventory service."""
        try:
            if self._catalog_worker and self._catalog_worker.isRunning():
                self._catalog_worker.quit()
                self._catalog_worker.wait(2000)
        except RuntimeError:
            pass

        self.catalog_stack.setCurrentIndex(1)  # show loading spinner

        self._catalog_worker = CatalogWorker(self.inventory_service)
        self._catalog_worker.data_ready.connect(self._on_catalog_loaded)
        self._catalog_worker.error_occurred.connect(self._on_catalog_error)
        self._catalog_worker.finished.connect(self._catalog_worker.deleteLater)
        self._catalog_worker.start()

    @Slot(object)
    def _on_catalog_loaded(self, df):
        """Process the loaded DataFrame."""
        self._all_products = df
        # Update categories
        if df is not None and not df.empty:
            cats = sorted(df['category'].dropna().unique().tolist())
            self.cat_filter.blockSignals(True)
            current_cat = self.cat_filter.currentText()
            self.cat_filter.clear()
            self.cat_filter.addItem("All Categories")
            self.cat_filter.addItems(cats)
            idx = self.cat_filter.findText(current_cat)
            if idx >= 0:
                self.cat_filter.setCurrentIndex(idx)
            self.cat_filter.blockSignals(False)
        # Apply current filters (search text, category)
        self._apply_catalog_filters()
        self.catalog_stack.setCurrentIndex(0)  # show table

    @Slot(str)
    def _on_catalog_error(self, msg):
        logger.error(f"Catalog load error: {msg}")
        self.catalog_error_label.setText("Failed to load product catalog.")
        self.catalog_error_detail.setPlainText(msg)
        self.catalog_error_detail.setVisible(True)
        self.catalog_stack.setCurrentIndex(2)

    def _apply_catalog_filters(self):
        """Apply search text and category filter, then render."""
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

    def _filter_catalog(self):
        """Triggered by search text or category change."""
        self._apply_catalog_filters()

    def _render_catalog(self, df):
        """Rebuild the QStandardItemModel for the catalog."""
        model = QStandardItemModel(0, 4)  # columns: SKU, Name, Stock, Price
        model.setHorizontalHeaderLabels(["SKU", "Name", "Stock", "Price"])

        for _, row in df.iterrows():
            sku = str(row['sku_code'])
            name = str(row['name'])
            stock = int(row['current_stock'])
            reorder = int(row.get('reorder_qty', 50))
            price = float(row['sell_price'])

            sku_item = QStandardItem(sku)
            sku_item.setForeground(QColor(Theme.TEXT_ACCENT))
            name_item = QStandardItem(name)

            stock_item = QStandardItem(str(stock))
            stock_item.setTextAlignment(Qt.AlignCenter)
            if stock <= 0:
                stock_item.setForeground(QColor(Theme.DANGER))
            elif stock < reorder:
                stock_item.setForeground(QColor(Theme.WARNING))
            else:
                stock_item.setForeground(QColor(Theme.SUCCESS))

            price_item = QStandardItem(f"৳ {price:,.0f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            model.appendRow([sku_item, name_item, stock_item, price_item])

        self._catalog_model = model
        self.catalog_table.setModel(model)

        # Now add "Add" buttons in column 4 via setIndexWidget
        model.setColumnCount(5)
        model.setHeaderData(4, Qt.Horizontal, "")  # column header empty

        for r in range(model.rowCount()):
            pid = df.iloc[r]['product_id']
            stock_val = int(df.iloc[r]['current_stock'])

            add_btn = QPushButton()
            if stock_val > 0:
                add_btn.setIcon(qta_icon('fa5s.plus', color=Theme.ACCENT))
                add_btn.setText("Add")
                add_btn.setStyleSheet(Theme.btn_icon_primary())
                add_btn.setToolTip("Add to cart")
                add_btn.clicked.connect(lambda ch, p=df.iloc[r].to_dict(): self._add_to_cart(p))
            else:
                add_btn.setIcon(qta_icon('fa5s.lock', color=Theme.TEXT_MUTED))
                add_btn.setText("Out")
                add_btn.setStyleSheet(Theme.btn_icon_primary())
                add_btn.setEnabled(False)
                add_btn.setToolTip("Out of stock")
            self.catalog_table.setIndexWidget(model.index(r, 4), add_btn)

        # Adjust column widths
        self.catalog_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.catalog_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.catalog_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.catalog_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.catalog_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.catalog_table.setColumnWidth(4, 80)

        self.product_count_lbl.setText(f"{len(df)} products")

    # Catalog interaction
    def _on_catalog_double_click(self, index):
        """Double-click a catalog row to add to cart."""
        if self._catalog_model is None or self._all_products is None:
            return
        sku_idx = self._catalog_model.index(index.row(), 0)
        if sku_idx.isValid():
            sku = self._catalog_model.itemFromIndex(sku_idx).text()
            df = self._all_products[self._all_products['sku_code'] == sku]
            if not df.empty:
                self._add_to_cart(df.iloc[0].to_dict())

    def _quick_add_first(self):
        """On Enter, add first visible product."""
        if not self._catalog_model or self._catalog_model.rowCount() == 0:
            return
        first_sku = self._catalog_model.item(0, 0).text()
        df = self._all_products[self._all_products['sku_code'] == first_sku]
        if not df.empty:
            self._add_to_cart(df.iloc[0].to_dict())
            self.search_input.clear()

    # ─── CART LOGIC ───────────────────────────────────────────────────────
    def _add_to_cart(self, product):
        """Add product to cart with stock validation."""
        pid = product['product_id']
        stock = int(product.get('current_stock', 0))

        current_in_cart = 0
        for item in self.cart:
            if item['product_id'] == pid:
                current_in_cart = item['qty']
                break

        if current_in_cart + 1 > stock:
            QMessageBox.warning(
                self, "Stock Limit",
                f"Cannot add more — only {stock} units available for '{product['name']}'."
            )
            return

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
            # Apply styling
            qty_spin.setButtonSymbols(QSpinBox.NoButtons)
            qty_spin.setAlignment(Qt.AlignCenter)
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
            # Block signals while setting value to prevent premature _update_qty
            qty_spin.blockSignals(True)
            qty_spin.setValue(item['qty'])
            qty_spin.blockSignals(False)
            qty_spin.valueChanged.connect(lambda v, idx=i: self._update_qty(idx, v))
            self.cart_table.setCellWidget(i, 1, qty_spin)

            # Unit price
            price_item = QTableWidgetItem(f"৳ {item['price']:,.0f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
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
            rm_btn = QPushButton()
            rm_btn.setIcon(qta_icon('fa5s.times', color=Theme.DANGER))
            rm_btn.setStyleSheet(Theme.btn_icon_danger())
            rm_btn.setToolTip("Remove item")
            # Correct lambda closure capturing idx=i
            rm_btn.clicked.connect(lambda ch, idx=i: self._remove_item(idx))
            self.cart_table.setCellWidget(i, 4, rm_btn)

        self._update_totals()
        self.cart_badge.setText(f"{sum(i['qty'] for i in self.cart)} items")

    def _update_qty(self, idx, val):
        if 0 <= idx < len(self.cart):
            self.cart[idx]['qty'] = val
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
        dlg = ConfirmDialog(
            "Clear Cart",
            "Remove all items from the current sale?",
            confirm_text="Clear All", confirm_color="danger", parent=self
        )
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

    # ─── CHECKOUT ─────────────────────────────────────────────────────────
    def _checkout(self):
        if not self.cart:
            QMessageBox.warning(self, "Empty Cart", "Add products to the cart before checkout.")
            return

        subtotal = sum(i['qty'] * i['price'] for i in self.cart)
        disc = self.discount_spin.value()
        total = subtotal * (1 - disc / 100)
        payment = self.payment_combo.currentText()

        items_summary = "\n".join(
            f"  • {i['name']} × {i['qty']}  =  ৳ {i['price']*i['qty']:,.0f}"
            for i in self.cart
        )
        dlg = ConfirmDialog(
            "Confirm Sale",
            f"Complete sale for {self.customer_input.text()}?",
            f"Items: {len(self.cart)} | Payment: {payment}\nTotal: ৳ {total:,.0f}",
            confirm_text="Complete Sale", confirm_color="success",
            parent=self
        )
        if dlg.exec() != QDialog.Accepted:
            return

        from src.services.types import CartItem
        items = [
            CartItem(i['product_id'], i['name'], i['qty'], i['price'], i['price'] * i['qty'])
            for i in self.cart
        ]

        try:
            res = self.sales_service.complete_sale(
                items, self.customer_input.text(),
                self.discount_spin.value(), payment
            )
            if res.success:
                QMessageBox.information(
                    self, "Sale Complete ✓",
                    f"Sale recorded successfully!\n\n"
                    f"Invoice: {res.sale_ids[0] if res.sale_ids else 'N/A'}\n"
                    f"Revenue: ৳ {res.total_revenue:,.0f}\n"
                    f"Profit: ৳ {res.total_profit:,.0f}"
                )
                self.cart = []
                self.customer_input.setText("Walk-in Customer")
                self.discount_spin.setValue(0)
                self._render_cart()
                self.refresh()  # refresh catalog to update stock
                self.sale_completed.emit()
            else:
                QMessageBox.warning(self, "Sale Failed", "\n".join(res.errors))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            logger.exception("Checkout failed")

    # ─── HOLD / RECALL ────────────────────────────────────────────────────
    def _hold_sale(self):
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
            QMessageBox.information(
                self, "Sale Held",
                f"Sale parked as {hold_id}.\nYou can recall it anytime."
            )
            self.cart = []
            self.customer_input.setText("Walk-in Customer")
            self.discount_spin.setValue(0)
            self._render_cart()
        except Exception as e:
            QMessageBox.critical(self, "Hold Error", str(e))
            logger.exception("Failed to hold sale")

    def _recall_sale(self):
        try:
            db = self.sales_service.repo.db
            df = db.execute_query("SELECT * FROM held_sales ORDER BY created_at DESC LIMIT 10")

            if df.empty:
                QMessageBox.information(self, "No Held Sales", "There are no parked sales to recall.")
                return

            items = [
                f"{row['hold_id']} — {row['customer']} ({row['created_at'][:16]})"
                for _, row in df.iterrows()
            ]
            choice, ok = QInputDialog.getItem(self, "Recall Sale", "Select a held sale:", items, 0, False)
            if ok and choice:
                hold_id = choice.split(" — ")[0]
                row = df[df['hold_id'] == hold_id].iloc[0]

                self.cart = json.loads(row['cart_json'])
                self.customer_input.setText(row['customer'])
                self.discount_spin.setValue(float(row['discount']))
                self._render_cart()

                db.execute_write("DELETE FROM held_sales WHERE hold_id = ?", (hold_id,))
        except Exception as e:
            QMessageBox.critical(self, "Recall Error", str(e))
            logger.exception("Failed to recall sale")

    # ─── EXPORT CATALOG ───────────────────────────────────────────────────
    def export_catalog_csv(self):
        """Export the currently visible catalog to a CSV file."""
        if self._catalog_model is None or self._catalog_model.rowCount() == 0:
            QMessageBox.warning(self, "Export", "No data to export.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Catalog", "products.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["SKU", "Name", "Stock", "Price"])
                for row in range(self._catalog_model.rowCount()):
                    row_data = []
                    for col in range(4):
                        item = self._catalog_model.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Export", f"Catalog exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
            logger.exception("CSV export failed")