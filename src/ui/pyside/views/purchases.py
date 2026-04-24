from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QMessageBox, QSpinBox, QDoubleSpinBox, QComboBox)
from PySide6.QtCore import Qt

class PySidePurchases(QWidget):
    def __init__(self, purchase_service, product_service, report_service):
        super().__init__()
        self.purchase_service = purchase_service
        self.product_service = product_service
        self.report_service = report_service
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(20)
        
        self._build_entry_pane()
        self._build_history_pane()
        
    def _build_entry_pane(self):
        entry_frame = QFrame()
        entry_frame.setStyleSheet("background-color: #2D3748; border-radius: 12px;")
        entry_layout = QVBoxLayout(entry_frame)
        
        title = QLabel("🚚 Record Purchase")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #F7FAFC;")
        entry_layout.addWidget(title)
        
        # Product Selection
        entry_layout.addWidget(QLabel("Select Product:"))
        self.product_combo = QComboBox()
        self.product_combo.setStyleSheet("""
            QComboBox { background-color: #1A202C; color: #FFFFFF; border: 1px solid #4A5568; border-radius: 6px; padding: 8px; font-size: 14px; }
        """)
        self._load_products()
        entry_layout.addWidget(self.product_combo)
        
        # Supplier
        entry_layout.addWidget(QLabel("Supplier (Optional):"))
        self.supplier_input = QLineEdit()
        self.supplier_input.setStyleSheet("QLineEdit { background-color: #1A202C; color: #FFFFFF; border: 1px solid #4A5568; border-radius: 6px; padding: 8px; }")
        entry_layout.addWidget(self.supplier_input)
        
        # Qty and Cost
        qc_layout = QHBoxLayout()
        
        qty_layout = QVBoxLayout()
        qty_layout.addWidget(QLabel("Quantity:"))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 99999)
        self.qty_spin.setStyleSheet("QSpinBox { background-color: #1A202C; color: #FFFFFF; border: 1px solid #4A5568; border-radius: 6px; padding: 8px; font-size: 14px; }")
        self.qty_spin.valueChanged.connect(self._update_total)
        qty_layout.addWidget(self.qty_spin)
        qc_layout.addLayout(qty_layout)
        
        cost_layout = QVBoxLayout()
        cost_layout.addWidget(QLabel("Unit Cost (৳):"))
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0.01, 999999.99)
        self.cost_spin.setDecimals(2)
        self.cost_spin.setStyleSheet("QDoubleSpinBox { background-color: #1A202C; color: #FFFFFF; border: 1px solid #4A5568; border-radius: 6px; padding: 8px; font-size: 14px; }")
        self.cost_spin.valueChanged.connect(self._update_total)
        cost_layout.addWidget(self.cost_spin)
        qc_layout.addLayout(cost_layout)
        
        entry_layout.addLayout(qc_layout)
        
        # Total Preview
        self.total_lbl = QLabel("Total: ৳ 0.00")
        self.total_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #DD6B20; margin-top: 15px;")
        entry_layout.addWidget(self.total_lbl)
        
        # Save Button
        save_btn = QPushButton("Save Purchase")
        save_btn.setStyleSheet("""
            QPushButton { background-color: #DD6B20; color: white; border-radius: 8px; padding: 15px; font-weight: bold; font-size: 16px; margin-top: 10px; }
            QPushButton:hover { background-color: #C05621; }
        """)
        save_btn.clicked.connect(self._save_purchase)
        entry_layout.addWidget(save_btn)
        
        entry_layout.addStretch()
        self.layout.addWidget(entry_frame, stretch=1)

    def _build_history_pane(self):
        history_frame = QFrame()
        history_frame.setStyleSheet("background-color: #2D3748; border-radius: 12px;")
        history_layout = QVBoxLayout(history_frame)
        
        title = QLabel("🕒 Recent Purchases")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #F7FAFC;")
        history_layout.addWidget(title)
        
        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["Date", "Product", "Qty", "Total Cost"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setStyleSheet("""
            QTableWidget { background-color: #1A202C; color: #E2E8F0; border: none; border-radius: 8px; font-size: 13px; }
            QHeaderView::section { background-color: #2D3748; color: #A0AEC0; font-weight: bold; border: none; padding: 8px; }
            QTableWidget::item { padding: 5px; border-bottom: 1px solid #2D3748; }
        """)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        history_layout.addWidget(self.history_table, stretch=1)
        
        self.layout.addWidget(history_frame, stretch=2)
        self._load_history()

    def _load_products(self):
        df = self.product_service.repo.get_all()
        self.product_combo.clear()
        for _, row in df.iterrows():
            self.product_combo.addItem(f"{row['sku_code']} - {row['name']}", row['product_id'])

    def _update_total(self):
        qty = self.qty_spin.value()
        cost = self.cost_spin.value()
        self.total_lbl.setText(f"Total: ৳ {qty * cost:,.2f}")

    def _save_purchase(self):
        if self.product_combo.count() == 0:
            return
            
        pid = self.product_combo.currentData()
        qty = self.qty_spin.value()
        cost = self.cost_spin.value()
        supplier = self.supplier_input.text().strip()
        
        try:
            res = self.purchase_service.record_purchase(pid, qty, cost, supplier)
            if res.success:
                QMessageBox.information(self, "Success", "Purchase recorded successfully!")
                self.qty_spin.setValue(1)
                self.supplier_input.clear()
                self._load_history()
            else:
                QMessageBox.warning(self, "Failed", "\n".join(res.errors))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _load_history(self):
        df = self.report_service.get_purchase_history()
        self.history_table.setRowCount(0)
        
        if df.empty:
            return
            
        for i, row in df.head(15).iterrows():
            r = self.history_table.rowCount()
            self.history_table.insertRow(r)
            self.history_table.setItem(r, 0, QTableWidgetItem(str(row['date'])[:10]))
            self.history_table.setItem(r, 1, QTableWidgetItem(str(row['product_name'])))
            self.history_table.setItem(r, 2, QTableWidgetItem(str(row['qty'])))
            self.history_table.setItem(r, 3, QTableWidgetItem(f"৳ {row['total_cost']:.2f}"))
