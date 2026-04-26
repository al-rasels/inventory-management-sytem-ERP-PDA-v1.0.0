"""
Returns View — Product Return System with invoice-linked and manual returns.
Features: Return workflow, inventory sync, refund processing.
"""
from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QAction, QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QTableView, QHeaderView, QMessageBox, QSpinBox, QDoubleSpinBox,
    QComboBox, QProgressBar, QStackedWidget, QTextEdit, QApplication,
    QStyle, QFileDialog, QMenu, QAbstractItemView, QDialog, QTabWidget,
    QCompleter, QCheckBox
)
from qtawesome import icon as qta_icon

from src.ui.pyside.theme import Theme
from src.ui.pyside.widgets import ConfirmDialog

logger = logging.getLogger(__name__)


# =====================================================================
# Background worker for loading return data
# =====================================================================
class ReturnsWorker(QThread):
    """Fetches return history and sales eligible for return."""
    data_ready = Signal(list, list)  # returns list, eligible sales list
    error_occurred = Signal(str)

    def __init__(self, return_service, sales_repo, product_service):
        super().__init__()
        self.return_service = return_service
        self.sales_repo = sales_repo
        self.product_service = product_service

    def run(self):
        try:
            returns_list = []
            eligible_sales = []

            # Get return history
            returns = self.return_service.get_return_history()
            for r in returns:
                returns_list.append({
                    'return_id': str(r.get('return_id', '')),
                    'date': str(r.get('date', ''))[:10],
                    'product': str(r.get('product_name', r.get('product_id', ''))),
                    'sku': str(r.get('sku_code', '')),
                    'qty': int(r.get('qty', 0)),
                    'refund': float(r.get('refund_amount', 0)),
                    'reason': str(r.get('return_reason', '')),
                    'method': str(r.get('refund_method', '')),
                    'type': str(r.get('return_type', '')),
                    'status': str(r.get('status', '')),
                })

            # Get eligible sales for return lookup
            sales_df = self.sales_repo.get_all()
            if sales_df is not None and not sales_df.empty:
                for _, row in sales_df.head(50).iterrows():  # Limit for performance
                    eligible_sales.append({
                        'sales_id': str(row.get('sales_id', '')),
                        'date': str(row.get('date', ''))[:10],
                        'product_id': str(row.get('product_id', '')),
                        'customer': str(row.get('customer', 'Walk-in')),
                        'qty': int(row.get('qty', 0)),
                        'price': float(row.get('sell_price', 0)),
                    })

            self.data_ready.emit(returns_list, eligible_sales)

        except Exception as e:
            logger.exception("Returns worker failed")
            self.error_occurred.emit(str(e))


# =====================================================================
# Return Item Dialog
# =====================================================================
class ReturnItemDialog(QDialog):
    """Dialog for adding a return item."""
    
    def __init__(self, products: list, sales_history: list, parent=None):
        super().__init__(parent)
        self.result_data = None
        
        self.setWindowTitle("Add Return Item")
        self.setFixedSize(600, 450)
        self.setStyleSheet(f"QDialog {{ background-color: {Theme.BG_PRIMARY}; color: {Theme.TEXT_PRIMARY}; }}")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("Add Item to Return")
        title.setStyleSheet(Theme.label_title())
        layout.addWidget(title)
        
        # Product selection
        layout.addWidget(QLabel("Product:", styleSheet=Theme.label_muted()))
        self.product_combo = QComboBox()
        self.product_combo.setStyleSheet(Theme.combo_style())
        self.product_combo.setEditable(True)
        self.product_combo.setMinimumContentsLength(30)
        for p in products:
            self.product_combo.addItem(f"{p['sku']} - {p['name']}", p['product_id'])
        layout.addWidget(self.product_combo)
        
        # Link to original sale (optional)
        group = QFrame()
        group.setStyleSheet(f"QFrame {{ background-color: {Theme.BG_SECONDARY}; border-radius: {Theme.RADIUS_MD}; padding: 10px; }}")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(8)
        
        self.link_sale_check = QCheckBox("Link to original sale")
        self.link_sale_check.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        self.link_sale_check.stateChanged.connect(self._toggle_sale_lookup)
        group_layout.addWidget(self.link_sale_check)
        
        self.sale_combo = QComboBox()
        self.sale_combo.setStyleSheet(Theme.combo_style())
        self.sale_combo.setEnabled(False)
        for s in sales_history:
            self.sale_combo.addItem(
                f"{s['sales_id']} | {s['date']} | {s['customer']} | Qty: {s['qty']}",
                s['sales_id']
            )
        group_layout.addWidget(self.sale_combo)
        layout.addWidget(group)
        
        # Quantity
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Quantity:", styleSheet=Theme.label_muted()))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 9999)
        self.qty_spin.setStyleSheet(Theme.spin_style())
        self.qty_spin.setValue(1)
        qty_layout.addWidget(self.qty_spin)
        qty_layout.addStretch()
        layout.addLayout(qty_layout)
        
        # Reason
        layout.addWidget(QLabel("Return Reason:", styleSheet=Theme.label_muted()))
        self.reason_combo = QComboBox()
        self.reason_combo.setStyleSheet(Theme.combo_style())
        self.reason_combo.addItems([
            "Defective Product",
            "Wrong Item Delivered",
            "Changed Mind",
            "Item Damaged",
            "Not as Described",
            "Other"
        ])
        layout.addWidget(self.reason_combo)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(Theme.btn_ghost())
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        add_btn = QPushButton("Add Item")
        add_btn.setStyleSheet(Theme.btn_primary())
        add_btn.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(add_btn)
        layout.addLayout(btn_layout)

    def _toggle_sale_lookup(self, state):
        self.sale_combo.setEnabled(state == Qt.Checked)

    def _validate_and_accept(self):
        if self.product_combo.currentData() is None:
            QMessageBox.warning(self, "Validation", "Please select a product.")
            return
        self.result_data = {
            'product_id': self.product_combo.currentData(),
            'product_name': self.product_combo.currentText(),
            'sale_id': self.sale_combo.currentData() if self.link_sale_check.isChecked() else None,
            'qty': self.qty_spin.value(),
            'reason': self.reason_combo.currentText()
        }
        self.accept()


# =====================================================================
# Main Returns Widget
# =====================================================================
class PySideReturns(QWidget):
    """Product Returns Management Interface."""
    
    return_processed = Signal()  # Emitted after successful return

    def __init__(self, return_service, sales_service, inventory_service, parent=None):
        super().__init__(parent)
        self.return_service = return_service
        self.sales_service = sales_service
        self.inventory_service = inventory_service
        self._worker: Optional[ReturnsWorker] = None
        self._return_items: List[Dict[str, Any]] = []
        self._all_products: List[Dict] = []
        self._all_sales: List[Dict] = []
        
        self._setup_ui()
        self._connect_signals()
        self._start_loading()

    # ----- UI Construction -------------------------------------------------
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        # Toolbar
        self._build_toolbar(main_layout)
        
        # Tab area
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_MD};
                background: {Theme.BG_SECONDARY};
            }}
            QTabBar::tab {{
                background: {Theme.BG_PRIMARY};
                color: {Theme.TEXT_MUTED};
                padding: 12px 24px;
                border: 1px solid {Theme.BORDER};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {Theme.BG_SECONDARY};
                color: {Theme.ACCENT_LIGHT};
                border-bottom: 2px solid {Theme.ACCENT};
            }}
        """)
        
        # New Return Tab
        self.tabs.addTab(self._build_new_return_tab(), 
                        qta_icon('fa5s.undo', color=Theme.TEXT_PRIMARY), " New Return")
        
        # Return History Tab
        self.tabs.addTab(self._build_history_tab(),
                        qta_icon('fa5s.history', color=Theme.TEXT_PRIMARY), " History")
        
        main_layout.addWidget(self.tabs)
        
        # Shortcuts
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self.refresh)
        self.addAction(refresh_action)

    def _build_toolbar(self, parent_layout):
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(
            f"QFrame {{ background-color: {Theme.BG_SECONDARY}; "
            f"border-radius: {Theme.RADIUS_MD}; border: 1px solid {Theme.BORDER}; }}"
        )
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 16, 0)

        # Icon + Title
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta_icon('fa5s.undo-alt', color=Theme.ACCENT).pixmap(20, 20))
        h.addWidget(icon_lbl)

        title = QLabel("Product Returns")
        title.setStyleSheet(Theme.label_title())
        h.addWidget(title)
        h.addStretch()

        # Refresh button
        refresh_btn = QPushButton()
        refresh_btn.setIcon(qta_icon('fa5s.sync-alt', color='white'))
        refresh_btn.setText(" Refresh")
        refresh_btn.setStyleSheet(Theme.btn_primary())
        refresh_btn.clicked.connect(self.refresh)
        h.addWidget(refresh_btn)

        parent_layout.addWidget(bar)

    def _build_new_return_tab(self):
        """Build the new return form tab."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left: Return items form
        left_frame = QFrame()
        left_frame.setStyleSheet(Theme.card_style())
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("Return Items", styleSheet=Theme.label_title()))
        header.addStretch()
        add_item_btn = QPushButton()
        add_item_btn.setIcon(qta_icon('fa5s.plus', color='white'))
        add_item_btn.setText(" Add Item")
        add_item_btn.setStyleSheet(Theme.btn_success())
        add_item_btn.clicked.connect(self._add_return_item)
        header.addWidget(add_item_btn)
        left_layout.addLayout(header)

        # Return items table
        self.return_items_model = QStandardItemModel(0, 5)
        self.return_items_model.setHorizontalHeaderLabels(["Product", "Qty", "Price", "Total", ""])
        self.return_items_table = QTableView()
        self.return_items_table.setModel(self.return_items_model)
        self.return_items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.return_items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.return_items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.return_items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.return_items_table.setColumnWidth(4, 40)
        self.return_items_table.verticalHeader().setVisible(False)
        self.return_items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.return_items_table.setStyleSheet(Theme.tableview_style())
        left_layout.addWidget(self.return_items_table, stretch=1)

        layout.addWidget(left_frame, stretch=2)

        # Right: Processing options
        right_frame = QFrame()
        right_frame.setStyleSheet(Theme.card_style())
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(14)

        # Header
        right_layout.addWidget(QLabel("Return Details", styleSheet=Theme.label_title()))

        # Refund method
        right_layout.addWidget(QLabel("Refund Method:", styleSheet=Theme.label_muted()))
        self.refund_method = QComboBox()
        self.refund_method.setStyleSheet(Theme.combo_style())
        self.refund_method.addItem(qta_icon('fa5s.money-bill', color=Theme.SUCCESS), " Cash")
        self.refund_method.addItem(qta_icon('fa5s.credit-card', color=Theme.ACCENT), " Original Payment")
        self.refund_method.addItem(qta_icon('fa5s.gift', color=Theme.PURPLE), " Store Credit")
        right_layout.addWidget(self.refund_method)

        # Reason
        right_layout.addWidget(QLabel("Reason:", styleSheet=Theme.label_muted()))
        self.reason_combo = QComboBox()
        self.reason_combo.setStyleSheet(Theme.combo_style())
        self.reason_combo.addItems([
            "Defective", "Wrong Item", "Changed Mind", "Damaged", "Other"
        ])
        right_layout.addWidget(self.reason_combo)

        # Totals
        totals_frame = QFrame()
        totals_frame.setStyleSheet(f"background-color: {Theme.BG_TERTIARY}; border-radius: {Theme.RADIUS_MD}; padding: 12px;")
        totals_layout = QVBoxLayout(totals_frame)
        totals_layout.setSpacing(8)

        self.total_refund_lbl = QLabel("Total Refund: ৳ 0.00")
        self.total_refund_lbl.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {Theme.SUCCESS};")
        totals_layout.addWidget(self.total_refund_lbl)

        self.item_count_lbl = QLabel("0 items")
        self.item_count_lbl.setStyleSheet(Theme.label_muted())
        totals_layout.addWidget(self.item_count_lbl)
        right_layout.addWidget(totals_frame)

        right_layout.addStretch()

        # Buttons
        clear_btn = QPushButton()
        clear_btn.setIcon(qta_icon('fa5s.trash-alt', color='white'))
        clear_btn.setText(" Clear")
        clear_btn.setStyleSheet(Theme.btn_danger())
        clear_btn.setFixedHeight(48)
        clear_btn.clicked.connect(self._clear_return_items)
        right_layout.addWidget(clear_btn)

        process_btn = QPushButton()
        process_btn.setIcon(qta_icon('fa5s.check', color='white'))
        process_btn.setText(" Process Return")
        process_btn.setStyleSheet(Theme.btn_success())
        process_btn.setFixedHeight(48)
        font = process_btn.font()
        font.setPointSize(14)
        font.setBold(True)
        process_btn.setFont(font)
        process_btn.clicked.connect(self._process_return)
        right_layout.addWidget(process_btn)

        layout.addWidget(right_frame, stretch=1)

        return widget

    def _build_history_tab(self):
        """Build the return history tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header with search
        header = QHBoxLayout()
        header.addWidget(QLabel("Return History", styleSheet=Theme.label_title()))
        header.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search returns...")
        self.search_input.setStyleSheet(Theme.input_style())
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self._filter_history)
        header.addWidget(self.search_input)

        export_btn = QPushButton()
        export_btn.setIcon(qta_icon('fa5s.file-csv', color='white'))
        export_btn.setStyleSheet(Theme.btn_primary())
        export_btn.clicked.connect(self._export_history)
        header.addWidget(export_btn)

        layout.addLayout(header)

        # History table
        self.history_model = QStandardItemModel(0, 8)
        self.history_model.setHorizontalHeaderLabels([
            "Return ID", "Date", "Product", "Qty", "Refund", "Reason", "Method", "Status"
        ])
        self.history_table = QTableView()
        self.history_table.setModel(self.history_model)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setSortingEnabled(True)
        self.history_table.setStyleSheet(Theme.tableview_style())
        layout.addWidget(self.history_table)

        return widget

    # ----- Signal Connections ---------------------------------------------
    def _connect_signals(self):
        pass

    # ----- Data Loading --------------------------------------------------
    def _start_loading(self):
        try:
            if self._worker and self._worker.isRunning():
                self._worker.quit()
                self._worker.wait(2000)
        except RuntimeError:
            pass

        self._worker = ReturnsWorker(
            self.return_service,
            self.sales_service.repo,
            self.sales_service.inventory_service.product_repo
        )
        self._worker.data_ready.connect(self._on_data_ready)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    @Slot(list, list)
    def _on_data_ready(self, returns: list, sales: list):
        self._return_history = returns
        self._all_sales = sales
        
        # Load products for return dialog
        products_df = self.sales_service.inventory_service.product_repo.get_all()
        if products_df is not None and not products_df.empty:
            self._all_products = products_df.to_dict('records')

        # Populate history table
        self._populate_history(returns)

    @Slot(str)
    def _on_error(self, msg: str):
        logger.error(f"Returns error: {msg}")
        QMessageBox.critical(self, "Error", f"Failed to load returns data: {msg}")

    def _populate_history(self, returns: list):
        self.history_model.removeRows(0, self.history_model.rowCount())
        
        for r in returns:
            row = []
            # Return ID
            id_item = QStandardItem(r['return_id'])
            id_item.setForeground(QColor(Theme.TEXT_ACCENT))
            row.append(id_item)
            
            # Date
            row.append(QStandardItem(r['date']))
            
            # Product
            row.append(QStandardItem(r['product']))
            
            # Qty
            qty_item = QStandardItem(str(r['qty']))
            qty_item.setTextAlignment(Qt.AlignCenter)
            row.append(qty_item)
            
            # Refund
            refund_item = QStandardItem(f"৳ {r['refund']:,.0f}")
            refund_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            refund_item.setForeground(QColor(Theme.SUCCESS))
            row.append(refund_item)
            
            # Reason
            row.append(QStandardItem(r['reason']))
            
            # Method
            row.append(QStandardItem(r['method']))
            
            # Status
            status_item = QStandardItem(r['status'])
            if r['status'] == 'completed':
                status_item.setForeground(QColor(Theme.SUCCESS))
            elif r['status'] == 'pending':
                status_item.setForeground(QColor(Theme.WARNING))
            row.append(status_item)
            
            self.history_model.appendRow(row)

    def _filter_history(self, text: str):
        """Filter history table by search text."""
        if not hasattr(self, '_return_history'):
            return
        
        text = text.lower()
        filtered = [r for r in self._return_history 
                   if text in r['return_id'].lower() 
                   or text in r['product'].lower()
                   or text in r['reason'].lower()]
        self._populate_history(filtered)

    # ----- Return Processing ---------------------------------------------
    def _add_return_item(self):
        if not self._all_products:
            QMessageBox.warning(self, "No Products", "Please wait for data to load.")
            return

        products_for_dialog = [
            {'product_id': p['product_id'], 'sku': p['sku_code'], 'name': p['name']}
            for p in self._all_products
        ]
        
        dialog = ReturnItemDialog(products_for_dialog, self._all_sales, self)
        if dialog.exec() == QDialog.Accepted and dialog.result_data:
            data = dialog.result_data
            
            # Find product info
            product = next((p for p in self._all_products 
                          if p['product_id'] == data['product_id']), None)
            
            if product:
                item = {
                    'product_id': data['product_id'],
                    'name': product['name'],
                    'qty': data['qty'],
                    'price': float(product['sell_price']),
                    'sale_id': data['sale_id'],
                    'reason': data['reason']
                }
                self._return_items.append(item)
                self._render_return_items()

    def _render_return_items(self):
        """Render the return items table."""
        self.return_items_model.removeRows(0, self.return_items_model.rowCount())
        
        total_refund = 0.0
        for i, item in enumerate(self._return_items):
            row = []
            
            # Product name
            row.append(QStandardItem(item['name']))
            
            # Quantity
            qty_item = QStandardItem(str(item['qty']))
            qty_item.setTextAlignment(Qt.AlignCenter)
            row.append(qty_item)
            
            # Price
            price_item = QStandardItem(f"৳ {item['price']:,.0f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.append(price_item)
            
            # Total
            item_total = item['price'] * item['qty']
            total_item = QStandardItem(f"৳ {item_total:,.0f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            total_item.setForeground(QColor(Theme.TEXT_PRIMARY))
            row.append(total_item)
            
            # Remove button placeholder
            row.append(QStandardItem(""))
            
            self.return_items_model.appendRow(row)
            total_refund += item_total

        self.total_refund_lbl.setText(f"Total Refund: ৳ {total_refund:,.0f}")
        self.item_count_lbl.setText(f"{len(self._return_items)} item(s)")

    def _remove_return_item(self, idx: int):
        if 0 <= idx < len(self._return_items):
            self._return_items.pop(idx)
            self._render_return_items()

    def _clear_return_items(self):
        if not self._return_items:
            return
        dlg = ConfirmDialog(
            "Clear Return Items",
            "Remove all items from the return?",
            confirm_text="Clear All", confirm_color="danger", parent=self
        )
        if dlg.exec() == QDialog.Accepted:
            self._return_items = []
            self._render_return_items()

    def _process_return(self):
        if not self._return_items:
            QMessageBox.warning(self, "No Items", "Add items to return before processing.")
            return

        # Confirm dialog
        total = sum(item['price'] * item['qty'] for item in self._return_items)
        method = self.refund_method.currentText().strip()
        reason = self.reason_combo.currentText()
        
        items_text = "\n".join([f"• {item['name']} x {item['qty']}" for item in self._return_items])
        
        dlg = ConfirmDialog(
            "Confirm Return",
            f"Process return for {len(self._return_items)} item(s)?",
            f"Total Refund: ৳ {total:,.0f}\nMethod: {method}\n\n{items_text}",
            confirm_text="Process Return", confirm_color="success", parent=self
        )
        
        if dlg.exec() != QDialog.Accepted:
            return

        try:
            # Convert to ReturnItem objects
            from src.services.return_service import ReturnItem
            items = [
                ReturnItem(
                    product_id=item['product_id'],
                    name=item['name'],
                    qty=item['qty'],
                    unit_price=item['price'],
                    total=item['price'] * item['qty'],
                    original_sale_id=item.get('sale_id')
                )
                for item in self._return_items
            ]
            
            # Process return
            result = self.return_service.process_return(
                items=items,
                refund_method=method.lower(),
                reason=reason,
                processed_by="Admin"
            )
            
            if result.success:
                QMessageBox.information(
                    self, "Return Processed",
                    f"Return completed successfully!\n\n"
                    f"Return ID: {result.return_id}\n"
                    f"Items Returned: {result.items_returned}\n"
                    f"Total Refund: ৳ {result.refund_amount:,.0f}"
                )
                
                # Clear items
                self._return_items = []
                self._render_return_items()
                
                # Refresh data
                self._start_loading()
                self.return_processed.emit()
            else:
                QMessageBox.warning(self, "Return Failed", "\n".join(result.errors))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            logger.exception("Return processing failed")

    def _export_history(self):
        """Export return history to CSV."""
        if not hasattr(self, '_return_history') or not self._return_history:
            QMessageBox.warning(self, "Export", "No data to export.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Returns", "returns.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        
        try:
            import csv
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Return ID", "Date", "Product", "Qty", "Refund", "Reason", "Method", "Status"])
                for r in self._return_history:
                    writer.writerow([
                        r['return_id'], r['date'], r['product'], r['qty'],
                        r['refund'], r['reason'], r['method'], r['status']
                    ])
            QMessageBox.information(self, "Export", f"Returns exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    # ----- Public Methods ------------------------------------------------
    def refresh(self):
        self._start_loading()

    def showEvent(self, event):
        super().showEvent(event)
        self._start_loading()
