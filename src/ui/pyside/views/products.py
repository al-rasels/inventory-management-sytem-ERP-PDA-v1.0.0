"""Products View — Full CRUD product management."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableView, QHeaderView, QFrame, QComboBox, QMessageBox, QMenu,
    QAbstractItemView, QDialog
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor, QCursor
from src.ui.pyside.theme import Theme
from src.ui.pyside.widgets import ProductFormDialog, ConfirmDialog, KPICard


class ProductTableModel(QAbstractTableModel):
    HEADERS = ["SKU", "Name", "Category", "Stock", "Cost", "Sell Price", "Status"]
    
    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index, role):
        if not index.isValid(): return None
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
        if role == Qt.DisplayRole and orientation == Qt.Horizontal: return self.HEADERS[section]
    def get_row_data(self, row_index):
        if 0 <= row_index < len(self._data): return self._data.iloc[row_index].to_dict()
        return None


class PySideProducts(QWidget):
    def __init__(self, product_service, inventory_service):
        super().__init__()
        self.product_service = product_service
        self.inventory_service = inventory_service
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self._build_kpis(layout)
        self._build_toolbar(layout)
        self._build_table(layout)

    def _build_kpis(self, parent):
        row = QHBoxLayout()
        row.setSpacing(12)
        self.kpi_total = KPICard("Total Products", "0", "📦", Theme.ACCENT)
        self.kpi_active = KPICard("Active", "0", "✅", Theme.SUCCESS)
        self.kpi_low = KPICard("Low Stock", "0", "⚠️", Theme.WARNING)
        self.kpi_out = KPICard("Out of Stock", "0", "🚫", Theme.DANGER)
        for w in [self.kpi_total, self.kpi_active, self.kpi_low, self.kpi_out]: row.addWidget(w)
        parent.addLayout(row)

    def _build_toolbar(self, parent):
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"QFrame {{ background-color: {Theme.BG_SECONDARY}; border-radius: {Theme.RADIUS_MD}; border: 1px solid {Theme.BORDER}; }}")
        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search products...")
        self.search_input.setFixedWidth(320)
        self.search_input.setStyleSheet(Theme.input_style())
        self.search_input.textChanged.connect(self._load_data)
        self.cat_filter = QComboBox()
        self.cat_filter.setFixedWidth(200)
        self.cat_filter.setStyleSheet(Theme.combo_style())
        self.cat_filter.addItem("All Categories")
        self.cat_filter.currentTextChanged.connect(self._load_data)
        add_btn = QPushButton("+ Add Product")
        add_btn.setStyleSheet(Theme.btn_success())
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add_product)
        h.addWidget(self.search_input)
        h.addWidget(self.cat_filter)
        h.addStretch()
        h.addWidget(add_btn)
        parent.addWidget(bar)

    def _build_table(self, parent):
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
        parent.addWidget(self.table, stretch=1)

    def _load_data(self):
        try:
            df = self.inventory_service.get_stock_status()
            oos = len(df[df['current_stock'] <= 0])
            ls = len(df[(df['current_stock'] > 0) & (df['current_stock'] < df['reorder_qty'].fillna(50))])
            self.kpi_total.set_value(str(len(df)))
            self.kpi_active.set_value(str(len(df) - oos))
            self.kpi_low.set_value(str(ls))
            self.kpi_out.set_value(str(oos))
            cats = sorted(df['category'].dropna().unique().tolist())
            cur = self.cat_filter.currentText()
            self.cat_filter.blockSignals(True)
            self.cat_filter.clear()
            self.cat_filter.addItem("All Categories")
            self.cat_filter.addItems(cats)
            idx = self.cat_filter.findText(cur)
            if idx >= 0: self.cat_filter.setCurrentIndex(idx)
            self.cat_filter.blockSignals(False)
            t = self.search_input.text().lower()
            if t:
                m = df['sku_code'].str.lower().str.contains(t, na=False) | df['name'].str.lower().str.contains(t, na=False)
                df = df[m]
            c = self.cat_filter.currentText()
            if c and c != "All Categories": df = df[df['category'] == c]
            self.model = ProductTableModel(df)
            self.table.setModel(self.model)
        except Exception as e:
            print(f"Product load error: {e}")

    def _add_product(self):
        dlg = ProductFormDialog(parent=self)
        if dlg.exec() == QDialog.Accepted and dlg.result_data:
            try:
                self.product_service.create_product(dlg.result_data)
                QMessageBox.information(self, "Success", f"Product '{dlg.result_data['name']}' created.")
                self._load_data()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _on_dbl_click(self, index):
        rd = self.model.get_row_data(index.row())
        if rd: self._edit_product(rd)

    def _edit_product(self, pd):
        dlg = ProductFormDialog(parent=self, product_data=pd)
        if dlg.exec() == QDialog.Accepted and dlg.result_data:
            try:
                pid = dlg.result_data.pop('product_id', pd.get('product_id'))
                self.product_service.update_product(pid, dlg.result_data)
                QMessageBox.information(self, "Success", "Product updated.")
                self._load_data()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _ctx_menu(self, pos):
        index = self.table.indexAt(pos)
        if not index.isValid(): return
        rd = self.model.get_row_data(index.row())
        if not rd: return
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu {{ background-color: {Theme.BG_SECONDARY}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER}; padding: 4px; }} QMenu::item {{ padding: 8px 20px; }} QMenu::item:selected {{ background-color: {Theme.BG_TERTIARY}; }}")
        ea = menu.addAction("✏️ Edit Product")
        da = menu.addAction("🗑 Delete Product")
        action = menu.exec(QCursor.pos())
        if action == ea: self._edit_product(rd)
        elif action == da:
            dlg = ConfirmDialog("Delete Product", f"Delete '{rd['name']}'?", confirm_text="Delete", confirm_color="danger", parent=self)
            if dlg.exec() == QDialog.Accepted:
                try:
                    self.product_service.repo.delete(rd['product_id'])
                    self._load_data()
                except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def refresh(self): self._load_data()
    def showEvent(self, event):
        super().showEvent(event)
        self._load_data()
