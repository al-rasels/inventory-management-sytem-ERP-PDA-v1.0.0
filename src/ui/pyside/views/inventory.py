"""
Inventory View — Stock levels, filtering, valuation, with background loading
and proper icons (QtAwesome). No emoji used.
"""
from __future__ import annotations

import csv
import logging
from typing import Optional, List, Dict, Any

from PySide6.QtCore import (
    Qt, QThread, Signal, Slot
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QIcon, QAction, QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame,
    QTableView, QHeaderView, QAbstractItemView, QPushButton,
    QProgressBar, QStackedWidget, QTextEdit, QMessageBox, QMenu,
    QApplication, QStyle, QFileDialog
)

from qtawesome import icon as qta_icon  # <-- icon library

from src.ui.pyside.theme import Theme
from src.ui.pyside.widgets import IconKPICard

logger = logging.getLogger(__name__)


# =====================================================================
# Icon‑based KPICard (adapted to use QIcon instead of emoji)
# =====================================================================

# =====================================================================
# Background worker — all heavy queries off the main thread
# =====================================================================
class InventoryWorker(QThread):
    """Fetches inventory data without blocking the UI."""
    data_ready = Signal(dict)         # contains 'df' (DataFrame), 'total_units', 'total_value', 'sku_count', 'oos_count'
    error_occurred = Signal(str)

    def __init__(self, inventory_service, stock_filter: str, cat_filter: str):
        super().__init__()
        self.inventory_service = inventory_service
        self.stock_filter = stock_filter
        self.cat_filter = cat_filter

    def run(self):
        try:
            df = self.inventory_service.get_stock_status()
            if df is None or df.empty:
                self.data_ready.emit({
                    'df': None,
                    'total_units': 0, 'total_value': 0,
                    'sku_count': 0, 'oos_count': 0,
                    'categories': []
                })
                return

            # Basic KPIs from full dataset (before filtering)
            total_units = int(df['current_stock'].sum())
            total_value = float(df['inventory_value'].sum())
            sku_count = len(df)
            oos_count = len(df[df['current_stock'] <= 0])

            # Extract categories
            categories = sorted(df['category'].dropna().unique().tolist())

            # Apply category filter
            if self.cat_filter and self.cat_filter != "All Categories":
                df = df[df['category'] == self.cat_filter]

            # Apply stock filter
            if self.stock_filter == "Low Stock":
                df = df[df['current_stock'] < df['reorder_qty']]
            elif self.stock_filter == "Out of Stock":
                df = df[df['current_stock'] <= 0]
            elif self.stock_filter == "Healthy":
                df = df[df['current_stock'] >= df['reorder_qty']]

            self.data_ready.emit({
                'df': df,
                'total_units': total_units,
                'total_value': total_value,
                'sku_count': sku_count,
                'oos_count': oos_count,
                'categories': categories,
            })

        except Exception as e:
            logger.exception("Inventory worker failed")
            self.error_occurred.emit(str(e))


# =====================================================================
# Main Inventory View Widget
# =====================================================================
class PySideInventory(QWidget):
    def __init__(self, inventory_service, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self._worker: Optional[InventoryWorker] = None
        self._current_df = None
        self._current_categories = []

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

        # Toolbar (filters + search)
        self._build_toolbar(main_layout)

        # Stacked content (table + loading + error)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_table_view())     # index 0
        self.stack.addWidget(self._build_loading_widget()) # index 1
        self.stack.addWidget(self._build_error_widget())   # index 2
        main_layout.addWidget(self.stack, stretch=1)

        # Shortcuts & context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

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

        # Icons from QtAwesome (FontAwesome 5 solid)
        self.kpi_units = IconKPICard(
            "Total Units", "0",
            qta_icon('fa5s.box', color=Theme.ACCENT),
            Theme.ACCENT
        )
        self.kpi_value = IconKPICard(
            "Stock Value", "৳ 0",
            qta_icon('fa5s.money-bill', color=Theme.SUCCESS),
            Theme.SUCCESS
        )
        self.kpi_skus = IconKPICard(
            "SKU Count", "0",
            qta_icon('fa5s.tags', color=Theme.PURPLE),
            Theme.PURPLE
        )
        self.kpi_oos = IconKPICard(
            "Out of Stock", "0",
            qta_icon('fa5s.exclamation-triangle', color=Theme.DANGER),
            Theme.DANGER
        )

        for w in [self.kpi_units, self.kpi_value, self.kpi_skus, self.kpi_oos]:
            row.addWidget(w)
        parent_layout.addLayout(row)

    def _build_toolbar(self, parent_layout):
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(
            f"QFrame {{ background-color: {Theme.BG_SECONDARY}; "
            f"border-radius: {Theme.RADIUS_MD}; "
            f"border: 1px solid {Theme.BORDER}; }}"
        )
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        # Filter icon + label
        filter_icon = QLabel()
        filter_icon.setPixmap(qta_icon('fa5s.filter', color=Theme.TEXT_MUTED).pixmap(16, 16))
        layout.addWidget(filter_icon)

        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-weight: bold; "
            "border:none; background:transparent;"
        )
        layout.addWidget(filter_label)

        # Stock status filter
        self.stock_filter = QComboBox()
        self.stock_filter.addItems(["All", "Low Stock", "Out of Stock", "Healthy"])
        self.stock_filter.setStyleSheet(Theme.combo_style())
        layout.addWidget(self.stock_filter)

        # Category filter (populated after data load)
        self.cat_filter = QComboBox()
        self.cat_filter.addItem("All Categories")
        self.cat_filter.setStyleSheet(Theme.combo_style())
        layout.addWidget(self.cat_filter)

        layout.addStretch()

        # Manual refresh button
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(qta_icon('fa5s.sync-alt', color='white'))
        self.refresh_btn.setToolTip("Refresh (F5)")
        self.refresh_btn.setStyleSheet(
            f"QPushButton {{ background: {Theme.ACCENT}; border-radius: {Theme.RADIUS_SM}; padding: 6px; }}"
        )
        layout.addWidget(self.refresh_btn)

        parent_layout.addWidget(bar)

    def _build_table_view(self):
        """The main inventory table (QTableView + model)."""
        self.model = QStandardItemModel(0, 7)
        self.model.setHorizontalHeaderLabels([
            "SKU", "Name", "Category", "Purchased", "Sold", "Balance", "Value"
        ])

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.setStyleSheet(Theme.tableview_style())
        self.table.setShowGrid(False)

        return self.table

    def _build_loading_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)

        self.loading_label = QLabel("Loading inventory data...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 16px;")
        layout.addWidget(self.loading_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setFixedWidth(300)
        layout.addWidget(self.progress, alignment=Qt.AlignCenter)

        return w

    def _build_error_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        icon_label.setPixmap(
            self.style().standardIcon(QStyle.SP_MessageBoxCritical).pixmap(32, 32)
        )
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

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
        retry_btn.clicked.connect(self.refresh)
        layout.addWidget(retry_btn, alignment=Qt.AlignCenter)

        return w

    # ----- Signal wiring ---------------------------------------------------
    def _connect_signals(self):
        self.stock_filter.currentTextChanged.connect(self._start_loading)
        self.cat_filter.currentTextChanged.connect(self._start_loading)
        self.refresh_btn.clicked.connect(self.refresh)

    # ----- Data loading (background thread) --------------------------------
    def _start_loading(self):
        """Cancel any running worker and start a new one."""
        try:
            if self._worker and self._worker.isRunning():
                self._worker.quit()
                self._worker.wait(2000)
        except RuntimeError:
            pass

        # Show loading overlay
        self.stack.setCurrentIndex(1)

        self._worker = InventoryWorker(
            self.inventory_service,
            self.stock_filter.currentText(),
            self.cat_filter.currentText()
        )
        self._worker.data_ready.connect(self._on_data_ready)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    @Slot(dict)
    def _on_data_ready(self, data: dict):
        # Update KPIs (always from full dataset)
        self.kpi_units.set_value(f"{data['total_units']:,}")
        self.kpi_value.set_value(f"৳ {data['total_value']:,.0f}")
        self.kpi_skus.set_value(str(data['sku_count']))
        oos = data['oos_count']
        self.kpi_oos.set_value(str(oos))
        self.kpi_oos.set_color(Theme.DANGER if oos > 0 else Theme.SUCCESS)

        # Update category combo
        cats = data['categories']
        current_cat = self.cat_filter.currentText()
        self.cat_filter.blockSignals(True)
        self.cat_filter.clear()
        self.cat_filter.addItem("All Categories")
        if cats:
            self.cat_filter.addItems(cats)
        idx = self.cat_filter.findText(current_cat)
        if idx >= 0:
            self.cat_filter.setCurrentIndex(idx)
        self.cat_filter.blockSignals(False)

        # Populate table
        df = data['df']
        self.model.removeRows(0, self.model.rowCount())

        if df is not None and not df.empty:
            for _, row in df.iterrows():
                sku = str(row['sku_code'])
                name = str(row['name'])
                category = str(row['category'])
                purchased = int(row.get('total_in', 0))
                sold = int(row.get('total_out', 0))
                balance = int(row['current_stock'])
                reorder = int(row.get('reorder_qty', 50))
                value = float(row['inventory_value'])

                # Create items
                sku_item = QStandardItem(sku)
                sku_item.setForeground(QColor(Theme.TEXT_ACCENT))
                name_item = QStandardItem(name)
                cat_item = QStandardItem(category)
                pur_item = QStandardItem(str(purchased))
                sold_item = QStandardItem(str(sold))

                bal_item = QStandardItem(str(balance))
                bal_item.setTextAlignment(Qt.AlignCenter)
                if balance <= 0:
                    bal_item.setForeground(QColor(Theme.DANGER))
                elif balance < reorder:
                    bal_item.setForeground(QColor(Theme.WARNING))
                else:
                    bal_item.setForeground(QColor(Theme.SUCCESS))

                val_item = QStandardItem(f"৳ {value:,.0f}")
                val_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                self.model.appendRow([
                    sku_item, name_item, cat_item, pur_item, sold_item, bal_item, val_item
                ])
        else:
            # Empty state message
            placeholder = QStandardItem("No inventory items found")
            placeholder.setSelectable(False)
            self.model.appendRow([placeholder] + [QStandardItem("") for _ in range(6)])

        # Show the table view (hide loading/error)
        self.stack.setCurrentIndex(0)

    @Slot(str)
    def _on_error(self, msg: str):
        logger.error(f"Inventory error: {msg}")
        self.error_label.setText("Failed to load inventory data.")
        self.error_detail.setPlainText(msg)
        self.error_detail.setVisible(True)
        self.stack.setCurrentIndex(2)

    # ----- Public actions --------------------------------------------------
    def refresh(self):
        self._start_loading()

    def showEvent(self, event):
        super().showEvent(event)
        self._start_loading()

    def export_csv(self):
        """Export visible table data to CSV."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Inventory", "inventory.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Header
                writer.writerow(["SKU", "Name", "Category", "Purchased", "Sold", "Balance", "Value"])
                # Data rows
                for row in range(self.model.rowCount()):
                    row_data = []
                    for col in range(7):
                        item = self.model.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Export", f"Data exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.addAction(
            qta_icon('fa5s.sync-alt', color=Theme.TEXT_PRIMARY),
            "Refresh", self.refresh, QKeySequence("F5")
        )
        menu.addAction(
            qta_icon('fa5s.file-csv', color=Theme.TEXT_PRIMARY),
            "Export CSV", self.export_csv, QKeySequence("Ctrl+E")
        )
        menu.exec_(self.mapToGlobal(pos))