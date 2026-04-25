"""
Purchases View — Record purchases with searchable product dropdown,
history table, and professional icons. No emoji.
"""
from __future__ import annotations

import csv
import logging
from typing import Optional, List, Tuple, Any

from PySide6.QtCore import (
    Qt, QThread, Signal, Slot, QTimer
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QIcon, QAction, QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QTableView, QHeaderView, QMessageBox, QSpinBox, QDoubleSpinBox,
    QComboBox, QProgressBar, QStackedWidget, QTextEdit, QApplication,
    QStyle, QFileDialog, QMenu
)

from qtawesome import icon as qta_icon

from src.ui.pyside.theme import Theme

logger = logging.getLogger(__name__)


# =====================================================================
# Background worker – loads products and purchase history
# =====================================================================
class PurchasesWorker(QThread):
    """Fetches product list and purchase history in a background thread."""
    products_ready = Signal(list)   # list of (display_text, product_id) tuples
    history_ready = Signal(list)    # list of dicts with keys: date, product_name, supplier, qty, total_cost
    error_occurred = Signal(str)

    def __init__(self, product_service, report_service):
        super().__init__()
        self.product_service = product_service
        self.report_service = report_service

    def run(self):
        try:
            # Load all products
            products = []
            df = self.product_service.repo.get_all()
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    text = f"{row['sku_code']} — {row['name']}"
                    products.append((text, row['product_id']))
            self.products_ready.emit(products)

            # Load purchase history
            history = []
            hist_df = self.report_service.get_purchase_history()
            if hist_df is not None and not hist_df.empty:
                for _, row in hist_df.iterrows():
                    date_str = str(row['date'])[:10] if row['date'] else ''
                    history.append({
                        'date': date_str,
                        'product_name': str(row['product_name']),
                        'supplier': str(row.get('supplier', '')),
                        'qty': int(row['qty']),
                        'total_cost': float(row['total_cost']),
                    })
            self.history_ready.emit(history)

        except Exception as e:
            logger.exception("Purchase worker failed")
            self.error_occurred.emit(str(e))


# =====================================================================
# Main Purchases Widget
# =====================================================================
class PySidePurchases(QWidget):
    def __init__(self, purchase_service, product_service, report_service, parent=None):
        super().__init__(parent)
        self.purchase_service = purchase_service
        self.product_service = product_service
        self.report_service = report_service
        self._worker: Optional[PurchasesWorker] = None
        self._all_products: List[Tuple[str, int]] = []  # cache of full product list

        # Debounce timer for product search
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._apply_product_filter)

        self._setup_ui()
        self._connect_signals()
        self._start_loading()

    # ----- UI construction -------------------------------------------------
    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        # Left panel – entry form
        self._build_entry_panel(main_layout)

        # Right panel – history + loading/error overlay
        right_container = QVBoxLayout()
        right_container.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_history_panel())   # index 0
        self.stack.addWidget(self._build_loading_widget())  # index 1
        self.stack.addWidget(self._build_error_widget())    # index 2
        right_container.addWidget(self.stack, stretch=1)

        main_layout.addLayout(right_container, stretch=2)

        # Keyboard shortcuts
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self.refresh)
        self.addAction(refresh_action)

        export_action = QAction("Export History CSV", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_csv)
        self.addAction(export_action)

    def _build_entry_panel(self, parent_layout):
        frame = QFrame()
        frame.setStyleSheet(Theme.card_style())
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(14)

        # Title with icon
        title_layout = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(qta_icon('fa5s.truck', color=Theme.ORANGE).pixmap(20, 20))
        title_layout.addWidget(title_icon)
        title_label = QLabel("Record Purchase")
        title_label.setStyleSheet(Theme.label_title())
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        vl.addLayout(title_layout)

        # Product search
        vl.addWidget(QLabel("Product:", styleSheet=Theme.label_muted()))
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Type to search product...")
        self.product_search.setStyleSheet(Theme.input_style())
        # Add search icon inside field
        search_icon = QAction(
            qta_icon('fa5s.search', color=Theme.TEXT_MUTED),
            "", self.product_search
        )
        self.product_search.addAction(search_icon, QLineEdit.LeadingPosition)
        vl.addWidget(self.product_search)

        self.product_combo = QComboBox()
        self.product_combo.setStyleSheet(Theme.combo_style())
        self.product_combo.setMaxVisibleItems(12)
        vl.addWidget(self.product_combo)

        # Supplier
        vl.addWidget(QLabel("Supplier:", styleSheet=Theme.label_muted()))
        self.supplier_input = QLineEdit()
        self.supplier_input.setStyleSheet(Theme.input_style())
        self.supplier_input.setPlaceholderText("Supplier name (optional)")
        vl.addWidget(self.supplier_input)

        # Quantity + Unit Cost
        qc_layout = QHBoxLayout()
        # Quantity
        qty_layout = QVBoxLayout()
        qty_layout.addWidget(QLabel("Quantity:", styleSheet=Theme.label_muted()))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 99999)
        self.qty_spin.setStyleSheet(Theme.spin_style())
        self.qty_spin.valueChanged.connect(self._update_total)
        qty_layout.addWidget(self.qty_spin)
        qc_layout.addLayout(qty_layout)

        # Unit Cost
        cost_layout = QVBoxLayout()
        cost_layout.addWidget(QLabel("Unit Cost (৳):", styleSheet=Theme.label_muted()))
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0.01, 999999.99)
        self.cost_spin.setDecimals(2)
        self.cost_spin.setStyleSheet(Theme.spin_style())
        self.cost_spin.valueChanged.connect(self._update_total)
        cost_layout.addWidget(self.cost_spin)
        qc_layout.addLayout(cost_layout)

        vl.addLayout(qc_layout)

        # Total display
        self.total_lbl = QLabel("Total: ৳ 0.00")
        self.total_lbl.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {Theme.ORANGE};"
        )
        vl.addWidget(self.total_lbl)

        # Save button
        save_btn = QPushButton()
        save_btn.setIcon(qta_icon('fa5s.save', color='white'))
        save_btn.setText(" Save Purchase")
        save_btn.setStyleSheet(Theme.btn_warning())
        save_btn.setFixedHeight(48)
        save_btn.clicked.connect(self._save_purchase)
        vl.addWidget(save_btn)

        vl.addStretch()
        parent_layout.addWidget(frame, stretch=1)

    def _build_history_panel(self):
        """Panel containing history table and toolbar."""
        frame = QFrame()
        frame.setStyleSheet(Theme.card_style())
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(16, 16, 16, 16)
        vl.setSpacing(10)

        # Title with icon and refresh button
        title_layout = QHBoxLayout()
        history_icon = QLabel()
        history_icon.setPixmap(qta_icon('fa5s.history', color=Theme.TEXT_PRIMARY).pixmap(20, 20))
        title_layout.addWidget(history_icon)
        title_label = QLabel("Purchase History")
        title_label.setStyleSheet(Theme.label_title())
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        refresh_btn = QPushButton()
        refresh_btn.setIcon(qta_icon('fa5s.sync-alt', color='white'))
        refresh_btn.setToolTip("Refresh (F5)")
        refresh_btn.setStyleSheet(
            f"QPushButton {{ background: {Theme.ACCENT}; border-radius: {Theme.RADIUS_SM}; padding: 4px 8px; }}"
        )
        refresh_btn.clicked.connect(self.refresh)
        title_layout.addWidget(refresh_btn)

        export_btn = QPushButton()
        export_btn.setIcon(qta_icon('fa5s.file-csv', color='white'))
        export_btn.setToolTip("Export CSV (Ctrl+E)")
        export_btn.setStyleSheet(
            f"QPushButton {{ background: {Theme.ACCENT}; border-radius: {Theme.RADIUS_SM}; padding: 4px 8px; }}"
        )
        export_btn.clicked.connect(self.export_csv)
        title_layout.addWidget(export_btn)

        vl.addLayout(title_layout)

        # History table
        self.history_model = QStandardItemModel(0, 5)
        self.history_model.setHorizontalHeaderLabels(
            ["Date", "Product", "Supplier", "Qty", "Total Cost"]
        )
        self.history_table = QTableView()
        self.history_table.setModel(self.history_model)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setEditTriggers(QTableView.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableView.SelectRows)
        self.history_table.setSortingEnabled(True)
        self.history_table.setStyleSheet(Theme.tableview_style())
        self.history_table.setShowGrid(False)
        vl.addWidget(self.history_table, stretch=1)

        # Context menu for history
        self.history_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self._history_context_menu)

        return frame

    def _build_loading_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel("Loading purchase history...")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 16px;")
        layout.addWidget(lbl)
        prog = QProgressBar()
        prog.setRange(0, 0)
        prog.setFixedWidth(300)
        layout.addWidget(prog, alignment=Qt.AlignCenter)
        return w

    def _build_error_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            self.style().standardIcon(QStyle.SP_MessageBoxCritical).pixmap(32, 32)
        )
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)

        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet(f"color: {Theme.DANGER}; font-weight: bold;")
        layout.addWidget(self.error_label)

        self.error_detail = QTextEdit()
        self.error_detail.setReadOnly(True)
        self.error_detail.setMaximumHeight(80)
        self.error_detail.setVisible(False)
        layout.addWidget(self.error_detail)

        retry_btn = QPushButton("Retry")
        retry_btn.clicked.connect(self._start_loading)
        layout.addWidget(retry_btn, alignment=Qt.AlignCenter)

        return w

    # ----- Signal connections ----------------------------------------------
    def _connect_signals(self):
        self.product_search.textChanged.connect(self._on_search_text_changed)

    def _on_search_text_changed(self):
        """Debounce the product filtering."""
        self._search_timer.start()

    # ----- Data loading ----------------------------------------------------
    def _start_loading(self):
        try:
            if self._worker and self._worker.isRunning():
                self._worker.quit()
                self._worker.wait(2000)
        except RuntimeError:
            pass

        self.stack.setCurrentIndex(1)  # show loading

        self._worker = PurchasesWorker(self.product_service, self.report_service)
        self._worker.products_ready.connect(self._on_products_ready)
        self._worker.history_ready.connect(self._on_history_ready)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    @Slot(list)
    def _on_products_ready(self, products: list):
        self._all_products = products
        # Apply current search filter
        self._apply_product_filter()

    @Slot(list)
    def _on_history_ready(self, history: list):
        self.history_model.removeRows(0, self.history_model.rowCount())
        for item in history:
            date_item = QStandardItem(item['date'])
            prod_item = QStandardItem(item['product_name'])
            supplier_item = QStandardItem(item['supplier'])
            qty_item = QStandardItem(str(item['qty']))
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            cost_item = QStandardItem(f"৳ {item['total_cost']:,.2f}")
            cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.history_model.appendRow([
                date_item, prod_item, supplier_item, qty_item, cost_item
            ])

        # If history is empty, show a placeholder row
        if self.history_model.rowCount() == 0:
            placeholder = QStandardItem("No purchase records found")
            placeholder.setSelectable(False)
            self.history_model.appendRow([
                placeholder("")(""),
                QStandardItem("")("")
            ])

        self.stack.setCurrentIndex(0)  # show history panel

    @Slot(str)
    def _on_error(self, msg: str):
        logger.error(f"Purchase view error: {msg}")
        self.error_label.setText("Failed to load data.")
        self.error_detail.setPlainText(msg)
        self.error_detail.setVisible(True)
        self.stack.setCurrentIndex(2)

    # ----- Product filtering -----------------------------------------------
    def _apply_product_filter(self):
        """Rebuild the product combo based on current search text from the full list."""
        text = self.product_search.text().lower().strip()
        self.product_combo.blockSignals(True)
        self.product_combo.clear()
        for display, pid in self._all_products:
            if not text or text in display.lower():
                self.product_combo.addItem(display, pid)
        self.product_combo.blockSignals(False)

    # ----- Form logic ------------------------------------------------------
    def _update_total(self):
        total = self.qty_spin.value() * self.cost_spin.value()
        self.total_lbl.setText(f"Total: ৳ {total:,.2f}")

    def _save_purchase(self):
        if self.product_combo.count() == 0:
            QMessageBox.warning(self, "No Product", "Please select a product.")
            return
        pid = self.product_combo.currentData()
        qty = self.qty_spin.value()
        cost = self.cost_spin.value()
        supplier = self.supplier_input.text().strip()

        try:
            res = self.purchase_service.record_purchase(pid, qty, cost, supplier)
            if res.success:
                QMessageBox.information(
                    self, "Success",
                    f"Purchase recorded!\nBatch: {res.batch_id}\nTotal: ৳ {res.total_cost:,.2f}"
                )
                # Reset form
                self.qty_spin.setValue(1)
                self.cost_spin.setValue(0.01)
                self.supplier_input.clear()
                # Refresh history & products (stock may have changed)
                self._start_loading()
            else:
                QMessageBox.warning(self, "Failed", "\n".join(res.errors))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            logger.exception("Purchase save failed")

    # ----- History context menu --------------------------------------------
    def _history_context_menu(self, pos):
        index = self.history_table.indexAt(pos)
        if not index.isValid():
            return
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {Theme.BG_SECONDARY}; color: {Theme.TEXT_PRIMARY}; "
            f"border: 1px solid {Theme.BORDER}; padding: 4px; }} "
            f"QMenu::item {{ padding: 8px 20px; }} "
            f"QMenu::item:selected {{ background-color: {Theme.BG_TERTIARY}; }}"
        )
        menu.addAction(
            qta_icon('fa5s.copy', color=Theme.TEXT_PRIMARY),
            "Copy Cell", lambda: self._copy_cell(index)
        )
        menu.addAction(
            qta_icon('fa5s.file-csv', color=Theme.TEXT_PRIMARY),
            "Export History", self.export_csv
        )
        menu.exec_(self.history_table.viewport().mapToGlobal(pos))

    def _copy_cell(self, index):
        item = self.history_model.itemFromIndex(index)
        if item:
            QApplication.clipboard().setText(item.text())

    # ----- Public actions --------------------------------------------------
    def refresh(self):
        self._start_loading()

    def showEvent(self, event):
        super().showEvent(event)
        self._start_loading()

    def export_csv(self):
        """Export purchase history to CSV file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Purchase History", "purchases.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Product", "Supplier", "Qty", "Total Cost"])
                for row in range(self.history_model.rowCount()):
                    row_data = []
                    for col in range(5):
                        item = self.history_model.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Export", f"History exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
            logger.exception("CSV export failed")