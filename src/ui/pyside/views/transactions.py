"""
Transaction History View — Combined sales and purchase log with background loading.
"""
from __future__ import annotations

import csv
import logging
from typing import Optional, Dict, Any, List

from PySide6.QtCore import (
    Qt, QThread, Signal, Slot
)
from PySide6.QtGui import QShortcut, QKeySequence, QStandardItemModel, QStandardItem, QColor, QIcon, QAction, QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QHeaderView, QTabWidget, QTableView,
    QAbstractItemView, QMenu, QMessageBox, QProgressBar,
    QStackedWidget, QTextEdit, QFileDialog, QApplication, QStyle
)
from qtawesome import icon as qta_icon

from src.ui.pyside.theme import Theme

logger = logging.getLogger(__name__)


# =====================================================================
# Background worker – fetches sales and purchase histories
# =====================================================================
class TransactionWorker(QThread):
    """Loads transaction data in a background thread."""
    data_ready = Signal(list, list)   # sales list, purchases list
    error_occurred = Signal(str)

    def __init__(self, report_service, search_term: Optional[str] = None):
        super().__init__()
        self.report_service = report_service
        self.search_term = search_term

    def run(self):
        try:
            sales_list = []
            purchases_list = []

            # Sales
            sdf = self.report_service.get_sales_history(self.search_term)
            if sdf is not None and not sdf.empty:
                for _, row in sdf.iterrows():
                    sales_list.append({
                        'id': str(row['sales_id']),
                        'date': str(row['date'])[:10],
                        'product': str(row['product_name']),
                        'customer': str(row.get('customer', '')),
                        'qty': int(row['qty']),
                        'revenue': float(row['revenue']),
                    })

            # Purchases
            pdf = self.report_service.get_purchase_history(self.search_term)
            if pdf is not None and not pdf.empty:
                for _, row in pdf.iterrows():
                    purchases_list.append({
                        'id': str(row['purchase_id']),
                        'date': str(row['date'])[:10],
                        'product': str(row['product_name']),
                        'supplier': str(row.get('supplier', '')),
                        'qty': int(row['qty']),
                        'total_cost': float(row['total_cost']),
                    })

            self.data_ready.emit(sales_list, purchases_list)

        except Exception as e:
            logger.exception("Transaction worker failed")
            self.error_occurred.emit(str(e))


# =====================================================================
# Main Transactions Widget
# =====================================================================
class PySideTransactions(QWidget):
    def __init__(self, report_service, parent=None):
        super().__init__(parent)
        self.report_service = report_service
        self._worker: Optional[TransactionWorker] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        # Toolbar
        self._build_toolbar(main_layout)

        # Tab area wrapped in a stacked widget (normal/loading/error)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_tabs())           # index 0
        self.stack.addWidget(self._build_loading_widget()) # index 1
        self.stack.addWidget(self._build_error_widget())   # index 2
        main_layout.addWidget(self.stack, stretch=1)

        # Keyboard shortcuts
        self._setup_shortcuts()

        # Initial load
        self._start_loading()

    # ----- UI construction -------------------------------------------------
    def _build_toolbar(self, parent):
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(
            f"QFrame {{ background-color: {Theme.BG_SECONDARY}; "
            f"border-radius: {Theme.RADIUS_MD}; border: 1px solid {Theme.BORDER}; }}"
        )
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 16, 0)

        # Icon + title
        title_icon = QLabel()
        title_icon.setPixmap(qta_icon('fa5s.list-alt', color=Theme.TEXT_PRIMARY).pixmap(20, 20))
        h.addWidget(title_icon)

        title = QLabel("Transaction History")
        title.setStyleSheet(Theme.label_title())
        h.addWidget(title)
        h.addStretch()

        # Search field with icon
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by ID, product, or customer...")
        self.search_input.setFixedWidth(320)
        self.search_input.setStyleSheet(Theme.input_style())
        # Add search icon
        search_icon_action = QAction(
            qta_icon('fa5s.search', color=Theme.TEXT_MUTED),
            "", self.search_input
        )
        self.search_input.addAction(search_icon_action, QLineEdit.LeadingPosition)
        self.search_input.returnPressed.connect(self._start_loading)
        h.addWidget(self.search_input)

        # Clear search button (icon only)
        clear_btn = QPushButton()
        clear_btn.setIcon(qta_icon('fa5s.times', color=Theme.TEXT_MUTED))
        clear_btn.setFixedSize(36, 36)
        clear_btn.setStyleSheet(Theme.btn_ghost())
        clear_btn.setToolTip("Clear search")
        clear_btn.clicked.connect(self._clear_search)
        h.addWidget(clear_btn)

        # Search button
        search_btn = QPushButton("Search")
        search_btn.setIcon(qta_icon('fa5s.search', color='white'))
        search_btn.setStyleSheet(Theme.btn_primary())
        search_btn.clicked.connect(self._start_loading)
        h.addWidget(search_btn)

        parent.addWidget(bar)

    def _build_tabs(self):
        """Create the tab widget containing both tables."""
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
                padding: 10px 24px;
                border: 1px solid {Theme.BORDER};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {Theme.BG_SECONDARY};
                color: {Theme.ACCENT_LIGHT};
                border-bottom: 2px solid {Theme.ACCENT};
            }}
            QTabBar::tab:hover {{
                color: {Theme.TEXT_PRIMARY};
            }}
        """)

        # Sales tab
        sales_widget = QWidget()
        sales_layout = QVBoxLayout(sales_widget)
        sales_layout.setContentsMargins(12, 12, 12, 12)

        self.sales_model = QStandardItemModel(0, 6)
        self.sales_model.setHorizontalHeaderLabels([
            "Sale ID", "Date", "Product", "Customer", "Qty", "Revenue"
        ])
        self.sales_table = QTableView()
        self.sales_table.setModel(self.sales_model)
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sales_table.verticalHeader().setVisible(False)
        self.sales_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sales_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sales_table.setSortingEnabled(True)
        self.sales_table.setStyleSheet(Theme.tableview_style())
        self.sales_table.setShowGrid(False)
        self.sales_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sales_table.customContextMenuRequested.connect(
            lambda pos: self._table_context_menu(pos, self.sales_table, "sales")
        )
        sales_layout.addWidget(self.sales_table)

        self.tabs.addTab(sales_widget, qta_icon('fa5s.receipt', color=Theme.TEXT_PRIMARY), " Sales")

        # Purchases tab
        purchase_widget = QWidget()
        purchase_layout = QVBoxLayout(purchase_widget)
        purchase_layout.setContentsMargins(12, 12, 12, 12)

        self.purchase_model = QStandardItemModel(0, 6)
        self.purchase_model.setHorizontalHeaderLabels([
            "Purchase ID", "Date", "Product", "Supplier", "Qty", "Total Cost"
        ])
        self.purchase_table = QTableView()
        self.purchase_table.setModel(self.purchase_model)
        self.purchase_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.purchase_table.verticalHeader().setVisible(False)
        self.purchase_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.purchase_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.purchase_table.setSortingEnabled(True)
        self.purchase_table.setStyleSheet(Theme.tableview_style())
        self.purchase_table.setShowGrid(False)
        self.purchase_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.purchase_table.customContextMenuRequested.connect(
            lambda pos: self._table_context_menu(pos, self.purchase_table, "purchases")
        )
        purchase_layout.addWidget(self.purchase_table)

        self.tabs.addTab(purchase_widget, qta_icon('fa5s.truck', color=Theme.TEXT_PRIMARY), " Purchases")

        return self.tabs

    def _build_loading_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel("Loading transaction history...")
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

    def _setup_shortcuts(self):
        refresh_sc = QShortcut(QKeySequence("F5"), self)
        refresh_sc.activated.connect(self._start_loading)
        export_sc = QShortcut(QKeySequence("Ctrl+E"), self)
        export_sc.activated.connect(self.export_current_tab)

    # ----- Data loading (background) ---------------------------------------
    def _start_loading(self):
        try:
            if self._worker and self._worker.isRunning():
                self._worker.quit()
                self._worker.wait(2000)
        except RuntimeError:
            pass

        self.stack.setCurrentIndex(1)  # loading

        term = self.search_input.text().strip() or None
        self._worker = TransactionWorker(self.report_service, term)
        self._worker.data_ready.connect(self._on_data_ready)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    @Slot(list, list)
    def _on_data_ready(self, sales: list, purchases: list):
        # Populate sales table
        self.sales_model.removeRows(0, self.sales_model.rowCount())
        for s in sales:
            id_item = QStandardItem(s['id'])
            id_item.setForeground(QColor(Theme.TEXT_ACCENT))
            date_item = QStandardItem(s['date'])
            product_item = QStandardItem(s['product'])
            customer_item = QStandardItem(s['customer'])
            qty_item = QStandardItem(str(s['qty']))
            rev_item = QStandardItem(f"৳ {s['revenue']:,.0f}")
            rev_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            rev_item.setForeground(QColor(Theme.SUCCESS))
            self.sales_model.appendRow([id_item, date_item, product_item, customer_item, qty_item, rev_item])

        if not sales:
            placeholder = QStandardItem("No sales found")
            placeholder.setSelectable(False)
            self.sales_model.appendRow([placeholder] + [QStandardItem("") for _ in range(5)])

        # Populate purchases table
        self.purchase_model.removeRows(0, self.purchase_model.rowCount())
        for p in purchases:
            id_item = QStandardItem(p['id'])
            id_item.setForeground(QColor(Theme.TEXT_ACCENT))
            date_item = QStandardItem(p['date'])
            product_item = QStandardItem(p['product'])
            supplier_item = QStandardItem(p['supplier'])
            qty_item = QStandardItem(str(p['qty']))
            cost_item = QStandardItem(f"৳ {p['total_cost']:,.0f}")
            cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            cost_item.setForeground(QColor(Theme.ORANGE))
            self.purchase_model.appendRow([id_item, date_item, product_item, supplier_item, qty_item, cost_item])

        if not purchases:
            placeholder = QStandardItem("No purchases found")
            placeholder.setSelectable(False)
            self.purchase_model.appendRow([placeholder] + [QStandardItem("") for _ in range(5)])

        self.stack.setCurrentIndex(0)  # show tabs

    @Slot(str)
    def _on_error(self, msg: str):
        logger.error(f"Transactions error: {msg}")
        self.error_label.setText("Failed to load transaction history.")
        self.error_detail.setPlainText(msg)
        self.error_detail.setVisible(True)
        self.stack.setCurrentIndex(2)

    # ----- UI helpers ------------------------------------------------------
    def _clear_search(self):
        self.search_input.clear()
        self._start_loading()

    # ----- Context menu & export -------------------------------------------
    def _table_context_menu(self, pos, table_view, tab_name):
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {Theme.BG_SECONDARY}; color: {Theme.TEXT_PRIMARY}; "
            f"border: 1px solid {Theme.BORDER}; padding: 4px; }} "
            f"QMenu::item {{ padding: 8px 20px; }} "
            f"QMenu::item:selected {{ background-color: {Theme.BG_TERTIARY}; }}"
        )
        export_action = menu.addAction(
            qta_icon('fa5s.file-csv', color=Theme.TEXT_PRIMARY),
            f"Export {tab_name.capitalize()} CSV"
        )
        menu.addAction(
            qta_icon('fa5s.copy', color=Theme.TEXT_PRIMARY),
            "Copy Cell", lambda: self._copy_selected_cell(table_view)
        )
        action = menu.exec_(table_view.viewport().mapToGlobal(pos))
        if action == export_action:
            self.export_tab(tab_name)

    def _copy_selected_cell(self, table_view):
        index = table_view.currentIndex()
        if index.isValid():
            item = table_view.model().itemFromIndex(index)
            if item:
                QApplication.clipboard().setText(item.text())

    def export_current_tab(self):
        tab_idx = self.tabs.currentIndex()
        tab_name = "sales" if tab_idx == 0 else "purchases"
        self.export_tab(tab_name)

    def export_tab(self, tab_name: str):
        """Export the currently visible tab's data to CSV."""
        if tab_name == "sales":
            model = self.sales_model
            default_name = "sales_history.csv"
            headers = ["Sale ID", "Date", "Product", "Customer", "Qty", "Revenue"]
        else:
            model = self.purchase_model
            default_name = "purchase_history.csv"
            headers = ["Purchase ID", "Date", "Product", "Supplier", "Qty", "Total Cost"]

        path, _ = QFileDialog.getSaveFileName(
            self, f"Export {tab_name.capitalize()}", default_name, "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in range(model.rowCount()):
                    row_data = []
                    for col in range(6):
                        item = model.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Export", f"Data exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
            logger.exception("CSV export failed")

    # ----- Public methods --------------------------------------------------
    def refresh(self):
        self._start_loading()

    def showEvent(self, event):
        super().showEvent(event)
        self._start_loading()