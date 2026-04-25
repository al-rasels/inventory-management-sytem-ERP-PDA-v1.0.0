"""Purchases View — Record purchases with searchable product dropdown."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QSpinBox, QDoubleSpinBox, QComboBox
)
from PySide6.QtCore import Qt
from src.ui.pyside.theme import Theme


class PySidePurchases(QWidget):
    def __init__(self, purchase_service, product_service, report_service):
        super().__init__()
        self.purchase_service = purchase_service
        self.product_service = product_service
        self.report_service = report_service
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        self._build_entry(layout)
        self._build_history(layout)

    def _build_entry(self, parent):
        frame = QFrame()
        frame.setStyleSheet(Theme.card_style())
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(14)
        t = QLabel("🚚  Record Purchase")
        t.setStyleSheet(Theme.label_title())
        vl.addWidget(t)
        # Product search
        vl.addWidget(QLabel("Product:", styleSheet=Theme.label_muted()))
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("🔍 Type to search product...")
        self.product_search.setStyleSheet(Theme.input_style())
        self.product_search.textChanged.connect(self._filter_products)
        vl.addWidget(self.product_search)
        self.product_combo = QComboBox()
        self.product_combo.setStyleSheet(Theme.combo_style())
        self.product_combo.setMaxVisibleItems(12)
        vl.addWidget(self.product_combo)
        self._all_products = []
        self._load_products()
        # Supplier
        vl.addWidget(QLabel("Supplier:", styleSheet=Theme.label_muted()))
        self.supplier_input = QLineEdit()
        self.supplier_input.setStyleSheet(Theme.input_style())
        self.supplier_input.setPlaceholderText("Supplier name (optional)")
        vl.addWidget(self.supplier_input)
        # Qty + Cost
        qc = QHBoxLayout()
        ql = QVBoxLayout()
        ql.addWidget(QLabel("Quantity:", styleSheet=Theme.label_muted()))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 99999)
        self.qty_spin.setStyleSheet(Theme.spin_style())
        self.qty_spin.valueChanged.connect(self._update_total)
        ql.addWidget(self.qty_spin)
        qc.addLayout(ql)
        cl = QVBoxLayout()
        cl.addWidget(QLabel("Unit Cost (৳):", styleSheet=Theme.label_muted()))
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0.01, 999999.99)
        self.cost_spin.setDecimals(2)
        self.cost_spin.setStyleSheet(Theme.spin_style())
        self.cost_spin.valueChanged.connect(self._update_total)
        cl.addWidget(self.cost_spin)
        qc.addLayout(cl)
        vl.addLayout(qc)
        self.total_lbl = QLabel("Total: ৳ 0.00")
        self.total_lbl.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {Theme.ORANGE};")
        vl.addWidget(self.total_lbl)
        save_btn = QPushButton("💾  Save Purchase")
        save_btn.setStyleSheet(Theme.btn_warning())
        save_btn.setFixedHeight(48)
        save_btn.clicked.connect(self._save_purchase)
        vl.addWidget(save_btn)
        vl.addStretch()
        parent.addWidget(frame, stretch=1)

    def _build_history(self, parent):
        frame = QFrame()
        frame.setStyleSheet(Theme.card_style())
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(16, 16, 16, 16)
        vl.setSpacing(10)
        t = QLabel("🕐  Purchase History")
        t.setStyleSheet(Theme.label_title())
        vl.addWidget(t)
        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(["Date", "Product", "Supplier", "Qty", "Total Cost"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setStyleSheet(Theme.table_style())
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setShowGrid(False)
        vl.addWidget(self.history_table, stretch=1)
        parent.addWidget(frame, stretch=2)

    def _load_products(self):
        try:
            df = self.product_service.repo.get_all()
            self._all_products = []
            self.product_combo.clear()
            for _, row in df.iterrows():
                text = f"{row['sku_code']} — {row['name']}"
                self._all_products.append((text, row['product_id']))
                self.product_combo.addItem(text, row['product_id'])
        except Exception: pass

    def _filter_products(self, text):
        text = text.lower()
        self.product_combo.blockSignals(True)
        self.product_combo.clear()
        for t, d in self._all_products:
            if text in t.lower():
                self.product_combo.addItem(t, d)
        self.product_combo.blockSignals(False)

    def _update_total(self):
        self.total_lbl.setText(f"Total: ৳ {self.qty_spin.value() * self.cost_spin.value():,.2f}")

    def _save_purchase(self):
        if self.product_combo.count() == 0: return
        pid = self.product_combo.currentData()
        try:
            res = self.purchase_service.record_purchase(pid, self.qty_spin.value(), self.cost_spin.value(), self.supplier_input.text().strip())
            if res.success:
                QMessageBox.information(self, "Success ✓", f"Purchase recorded!\nBatch: {res.batch_id}\nTotal: ৳ {res.total_cost:,.2f}")
                self.qty_spin.setValue(1)
                self.supplier_input.clear()
                self._load_history()
            else:
                QMessageBox.warning(self, "Failed", "\n".join(res.errors))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _load_history(self):
        try:
            df = self.report_service.get_purchase_history()
            self.history_table.setRowCount(0)
            if df.empty: return
            for _, row in df.head(20).iterrows():
                r = self.history_table.rowCount()
                self.history_table.insertRow(r)
                self.history_table.setItem(r, 0, QTableWidgetItem(str(row['date'])[:10]))
                self.history_table.setItem(r, 1, QTableWidgetItem(str(row['product_name'])))
                self.history_table.setItem(r, 2, QTableWidgetItem(str(row.get('supplier', ''))))
                self.history_table.setItem(r, 3, QTableWidgetItem(str(row['qty'])))
                ci = QTableWidgetItem(f"৳ {row['total_cost']:,.2f}")
                ci.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.history_table.setItem(r, 4, ci)
        except Exception: pass

    def refresh(self):
        self._load_products()
        self._load_history()
    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
