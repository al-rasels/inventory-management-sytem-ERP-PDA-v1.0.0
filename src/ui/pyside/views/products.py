"""
Products View — Full CRUD product management with QtAwesome icons,
background loading, debounced search, export, and error handling.
"""
from __future__ import annotations

import csv
import logging
from typing import Optional, Dict, Any

from PySide6.QtCore import (
    Qt, QThread, Signal, Slot, QAbstractTableModel, QModelIndex, QTimer
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QIcon, QAction, QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableView, QHeaderView, QFrame, QComboBox, QMessageBox, QMenu,
    QAbstractItemView, QDialog, QProgressBar, QStackedWidget, QTextEdit,
    QApplication, QStyle, QFileDialog
)

from qtawesome import icon as qta_icon  # icon library

from src.ui.pyside.theme import Theme
from src.ui.pyside.widgets import IconKPICard, ProductFormDialog, ConfirmDialog

logger = logging.getLogger(__name__)


# =====================================================================
# Icon‑based KPICard (same as used in other views)
# =====================================================================

# =====================================================================
# Table model (unchanged core, but now set via data-ready signal)
# =====================================================================
class ProductTableModel(QAbstractTableModel):
    HEADERS = ["SKU", "Name", "Category", "Stock", "Cost", "Sell Price", "Status"]

    def __init__(self, data):
        super().__init__()
        self._data = data  # expects a pandas DataFrame

    def data(self, index, role):
        if not index.isValid():
            return None
        row = self._data.iloc[index.row()]
        col = index.column()
        if role == Qt.DisplayRole:
            if col == 0: return str(row['sku_code'])
            elif col == 1: return str(row['name'])
            elif col == 2: return str(row.get('category', ''))
            elif col == 3: return str(int(row.get('current_stock', 0)))
            elif col == 4: return f"৳ {float(row.get('cost_price', 0)):,.0f}"
            elif col == 5: return f"৳ {float(row['sell_price']):,.0f}"
            elif col == 6: return str(row.get('status', 'Active'))
        if role == Qt.ForegroundRole:
            if col == 3:
                stock = int(row.get('current_stock', 0))
                rq = int(row.get('reorder_qty', 50) if row.get('reorder_qty') == row.get('reorder_qty') else 50)
                if stock <= 0: return QColor(Theme.DANGER)
                elif stock < rq: return QColor(Theme.WARNING)
                else: return QColor(Theme.SUCCESS)
            if col == 0: return QColor(Theme.TEXT_ACCENT)
        if role == Qt.TextAlignmentRole:
            if col in [3, 4, 5]: return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)

    def rowCount(self, parent=QModelIndex()): return len(self._data)
    def columnCount(self, parent=QModelIndex()): return len(self.HEADERS)
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
    def get_row_data(self, row_index):
        if 0 <= row_index < len(self._data):
            return self._data.iloc[row_index].to_dict()
        return None


# =====================================================================
# Background worker – fetches stock status without freezing UI
# =====================================================================
class ProductWorker(QThread):
    """Loads the complete stock status DataFrame in a background thread."""
    data_ready = Signal(object)  # emits the pandas DataFrame
    error_occurred = Signal(str)

    def __init__(self, inventory_service):
        super().__init__()
        self.inventory_service = inventory_service

    def run(self):
        try:
            df = self.inventory_service.get_stock_status()
            self.data_ready.emit(df)
        except Exception as e:
            logger.exception("Product worker failed")
            self.error_occurred.emit(str(e))


# =====================================================================
# Main Products Widget
# =====================================================================
class PySideProducts(QWidget):
    def __init__(self, product_service, inventory_service, parent=None):
        super().__init__(parent)
        self.product_service = product_service
        self.inventory_service = inventory_service
        self._worker: Optional[ProductWorker] = None
        self._full_data = None  # original unfiltered DataFrame
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)  # ms
        self._debounce_timer.timeout.connect(self._apply_filters)

        self._setup_ui()
        self._connect_signals()
        self._start_loading()

    # ----- UI construction -------------------------------------------------
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        # KPI row
        self._build_kpi_row(main_layout)

        # Toolbar
        self._build_toolbar(main_layout)

        # Stacked content (table + loading + error)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_table_view())     # index 0
        self.stack.addWidget(self._build_loading_widget()) # index 1
        self.stack.addWidget(self._build_error_widget())   # index 2
        main_layout.addWidget(self.stack, stretch=1)

        # Keyboard shortcuts
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self.refresh)
        self.addAction(refresh_action)

        export_action = QAction("Export CSV", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_csv)
        self.addAction(export_action)

    def _build_kpi_row(self, parent_layout):
        row = QHBoxLayout()
        row.setSpacing(12)

        self.kpi_total = IconKPICard(
            "Total Products", "0",
            qta_icon('fa5s.box', color=Theme.ACCENT), Theme.ACCENT
        )
        self.kpi_active = IconKPICard(
            "Active", "0",
            qta_icon('fa5s.check-circle', color=Theme.SUCCESS), Theme.SUCCESS
        )
        self.kpi_low = IconKPICard(
            "Low Stock", "0",
            qta_icon('fa5s.exclamation-triangle', color=Theme.WARNING), Theme.WARNING
        )
        self.kpi_out = IconKPICard(
            "Out of Stock", "0",
            qta_icon('fa5s.times-circle', color=Theme.DANGER), Theme.DANGER
        )

        for w in [self.kpi_total, self.kpi_active, self.kpi_low, self.kpi_out]:
            row.addWidget(w)
        parent_layout.addLayout(row)

    def _build_toolbar(self, parent_layout):
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(
            f"QFrame {{ background-color: {Theme.BG_SECONDARY}; "
            f"border-radius: {Theme.RADIUS_MD}; border: 1px solid {Theme.BORDER}; }}"
        )
        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(10)

        # Search field with icon
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search products...")
        self.search_input.setFixedWidth(320)
        self.search_input.setStyleSheet(Theme.input_style())
        search_icon = QAction(
            qta_icon('fa5s.search', color=Theme.TEXT_MUTED), "", self.search_input
        )
        self.search_input.addAction(search_icon, QLineEdit.LeadingPosition)
        h.addWidget(self.search_input)

        # Category filter
        self.cat_filter = QComboBox()
        self.cat_filter.setFixedWidth(200)
        self.cat_filter.setStyleSheet(Theme.combo_style())
        self.cat_filter.addItem("All Categories")
        h.addWidget(self.cat_filter)

        h.addStretch()

        # Add product button
        add_btn = QPushButton()
        add_btn.setIcon(qta_icon('fa5s.plus', color='white'))
        add_btn.setText(" Add Product")
        add_btn.setStyleSheet(Theme.btn_success())
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add_product)
        h.addWidget(add_btn)

        # Export button
        export_btn = QPushButton()
        export_btn.setIcon(qta_icon('fa5s.file-csv', color='white'))
        export_btn.setToolTip("Export CSV (Ctrl+E)")
        export_btn.setStyleSheet(
            f"QPushButton {{ background: {Theme.ACCENT}; border-radius: {Theme.RADIUS_SM}; padding: 6px; }}"
        )
        export_btn.clicked.connect(self.export_csv)
        h.addWidget(export_btn)

        parent_layout.addWidget(bar)

    def _build_table_view(self):
        self.table = QTableView()
        self.table.setStyleSheet(Theme.tableview_style())
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setShowGrid(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._ctx_menu)
        self.table.doubleClicked.connect(self._on_dbl_click)
        return self.table

    def _build_loading_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel("Loading products...")
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

    # ----- Signal wiring ---------------------------------------------------
    def _connect_signals(self):
        self.search_input.textChanged.connect(self._on_search_changed)
        self.cat_filter.currentTextChanged.connect(self._apply_filters)

    def _on_search_changed(self):
        # Debounce search
        self._debounce_timer.start()

    # ----- Data loading (background) ---------------------------------------
    def _start_loading(self):
        try:
            if self._worker and self._worker.isRunning():
                self._worker.quit()
                self._worker.wait(2000)
        except RuntimeError:
            pass

        self.stack.setCurrentIndex(1)  # loading

        self._worker = ProductWorker(self.inventory_service)
        self._worker.data_ready.connect(self._on_data_ready)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    @Slot(object)
    def _on_data_ready(self, df):
        if df is None:
            df = self.inventory_service.get_stock_status()  # fallback if possible
        self._full_data = df

        # Update KPIs
        total = len(df)
        oos = len(df[df['current_stock'] <= 0])
        ls = len(df[(df['current_stock'] > 0) & (df['current_stock'] < df['reorder_qty'].fillna(50))])
        self.kpi_total.set_value(str(total))
        self.kpi_active.set_value(str(total - oos))
        self.kpi_low.set_value(str(ls))
        self.kpi_out.set_value(str(oos))

        # Update category combo
        cats = sorted(df['category'].dropna().unique().tolist())
        current_cat = self.cat_filter.currentText()
        self.cat_filter.blockSignals(True)
        self.cat_filter.clear()
        self.cat_filter.addItem("All Categories")
        self.cat_filter.addItems(cats)
        idx = self.cat_filter.findText(current_cat)
        if idx >= 0:
            self.cat_filter.setCurrentIndex(idx)
        self.cat_filter.blockSignals(False)

        # Apply current filters
        self._apply_filters()
        self.stack.setCurrentIndex(0)  # back to table

    @Slot(str)
    def _on_error(self, msg):
        logger.error(f"Products error: {msg}")
        self.error_label.setText("Failed to load product data.")
        self.error_detail.setPlainText(msg)
        self.error_detail.setVisible(True)
        self.stack.setCurrentIndex(2)

    # ----- Filtering & model update ---------------------------------------
    def _apply_filters(self):
        if self._full_data is None:
            return
        df = self._full_data.copy()
        # Search filter
        text = self.search_input.text().lower().strip()
        if text:
            mask = (
                df['sku_code'].str.lower().str.contains(text, na=False) |
                df['name'].str.lower().str.contains(text, na=False)
            )
            df = df[mask]
        # Category filter
        cat = self.cat_filter.currentText()
        if cat and cat != "All Categories":
            df = df[df['category'] == cat]

        # Create model and set to table
        self.model = ProductTableModel(df)
        self.table.setModel(self.model)

    # ----- CRUD operations -------------------------------------------------
    def _add_product(self):
        dlg = ProductFormDialog(parent=self)
        if dlg.exec() == QDialog.Accepted and dlg.result_data:
            try:
                self.product_service.create_product(dlg.result_data)
                QMessageBox.information(
                    self, "Success", f"Product '{dlg.result_data['name']}' created."
                )
                self._start_loading()  # refresh
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                logger.exception("Failed to create product")

    def _on_dbl_click(self, index):
        rd = self.model.get_row_data(index.row())
        if rd:
            self._edit_product(rd)

    def _edit_product(self, product_data):
        dlg = ProductFormDialog(parent=self, product_data=product_data)
        if dlg.exec() == QDialog.Accepted and dlg.result_data:
            try:
                pid = dlg.result_data.pop('product_id', product_data.get('product_id'))
                self.product_service.update_product(pid, dlg.result_data)
                QMessageBox.information(self, "Success", "Product updated.")
                self._start_loading()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                logger.exception("Failed to update product")

    def _ctx_menu(self, pos):
        index = self.table.indexAt(pos)
        if not index.isValid():
            return
        rd = self.model.get_row_data(index.row())
        if not rd:
            return
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {Theme.BG_SECONDARY}; color: {Theme.TEXT_PRIMARY}; "
            f"border: 1px solid {Theme.BORDER}; padding: 4px; }} "
            f"QMenu::item {{ padding: 8px 20px; }} "
            f"QMenu::item:selected {{ background-color: {Theme.BG_TERTIARY}; }}"
        )
        edit_action = menu.addAction(
            qta_icon('fa5s.edit', color=Theme.TEXT_PRIMARY), "Edit Product"
        )
        delete_action = menu.addAction(
            qta_icon('fa5s.trash-alt', color=Theme.DANGER), "Delete Product"
        )
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == edit_action:
            self._edit_product(rd)
        elif action == delete_action:
            dlg = ConfirmDialog(
                "Delete Product", f"Delete '{rd['name']}'?",
                confirm_text="Delete", confirm_color="danger", parent=self
            )
            if dlg.exec() == QDialog.Accepted:
                try:
                    self.product_service.repo.delete(rd['product_id'])
                    self._start_loading()
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
                    logger.exception("Failed to delete product")

    # ----- Public helpers --------------------------------------------------
    def refresh(self):
        self._start_loading()

    def showEvent(self, event):
        super().showEvent(event)
        self._start_loading()

    def export_csv(self):
        """Export currently visible product data to CSV."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Products", "products.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            model = self.table.model()
            if model is None or not isinstance(model, ProductTableModel):
                QMessageBox.warning(self, "Export", "No data to export.")
                return
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(ProductTableModel.HEADERS)
                for row_idx in range(model.rowCount()):
                    row_data = model._data.iloc[row_idx]
                    writer.writerow([
                        row_data['sku_code'],
                        row_data['name'],
                        row_data.get('category', ''),
                        row_data.get('current_stock', 0),
                        row_data.get('cost_price', 0),
                        row_data['sell_price'],
                        row_data.get('status', 'Active'),
                    ])
            QMessageBox.information(self, "Export", f"Data exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
            logger.exception("CSV export failed")