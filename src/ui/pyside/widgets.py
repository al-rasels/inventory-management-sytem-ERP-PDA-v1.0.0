"""
SunERP Reusable Widget Library
Professional-grade UI components used across all views.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QComboBox, QCompleter, QGraphicsDropShadowEffect,
    QDialog, QFormLayout, QDoubleSpinBox, QSpinBox, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel, QStringListModel, QTimer
from PySide6.QtGui import QColor, QFont
from src.ui.pyside.theme import Theme


class KPICard(QFrame):
    """Stylish KPI summary card with icon, title, and value."""
    
    def __init__(self, title: str, value: str, icon: str, color: str, parent=None):
        super().__init__(parent)
        self.color = color
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border-radius: {Theme.RADIUS_LG};
                border: 1px solid {Theme.BORDER};
                border-left: 4px solid {color};
            }}
        """)
        self.setFixedHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)
        
        # Top row: icon + title
        top = QHBoxLayout()
        top.setSpacing(8)
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 20px; background: transparent; border: none;")
        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED}; font-weight: 600; letter-spacing: 1px; background: transparent; border: none;")
        top.addWidget(icon_lbl)
        top.addWidget(title_lbl)
        top.addStretch()
        
        # Value
        self.val_lbl = QLabel(value)
        self.val_lbl.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color}; background: transparent; border: none;")
        
        layout.addLayout(top)
        layout.addWidget(self.val_lbl)
    
    def set_value(self, value: str):
        self.val_lbl.setText(value)
    
    def set_color(self, color: str):
        self.color = color
        self.val_lbl.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color}; background: transparent; border: none;")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border-radius: {Theme.RADIUS_LG};
                border: 1px solid {Theme.BORDER};
                border-left: 4px solid {color};
            }}
        """)


class SearchableComboBox(QWidget):
    """ComboBox with live search/filter capability."""
    
    currentDataChanged = Signal(object)
    
    def __init__(self, placeholder="Search...", parent=None):
        super().__init__(parent)
        self._items = []  # list of (display_text, data)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(placeholder)
        self.search_input.setStyleSheet(Theme.input_style())
        self.search_input.textChanged.connect(self._filter)
        
        self.combo = QComboBox()
        self.combo.setStyleSheet(Theme.combo_style())
        self.combo.currentIndexChanged.connect(self._on_selection)
        self.combo.setMaxVisibleItems(12)
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.combo)
    
    def set_items(self, items):
        """items: list of (display_text, data)"""
        self._items = items
        self._populate(items)
    
    def _populate(self, items):
        self.combo.blockSignals(True)
        self.combo.clear()
        for text, data in items:
            self.combo.addItem(text, data)
        self.combo.blockSignals(False)
    
    def _filter(self, text):
        text = text.lower()
        filtered = [(t, d) for t, d in self._items if text in t.lower()]
        self._populate(filtered)
    
    def _on_selection(self, idx):
        if idx >= 0:
            self.currentDataChanged.emit(self.combo.currentData())
    
    def current_data(self):
        return self.combo.currentData()
    
    def current_text(self):
        return self.combo.currentText()
    
    def count(self):
        return self.combo.count()


class StatusBar(QFrame):
    """Application status bar with user info, time, and DB status."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border-top: 1px solid {Theme.BORDER};
                border-radius: 0;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(20)
        
        lbl_style = f"font-size: 11px; color: {Theme.TEXT_MUTED}; border: none; background: transparent;"
        
        self.status_lbl = QLabel("● Ready")
        self.status_lbl.setStyleSheet(f"font-size: 11px; color: {Theme.SUCCESS}; border: none; background: transparent;")
        
        self.user_lbl = QLabel("👤 Admin")
        self.user_lbl.setStyleSheet(lbl_style)
        
        self.db_lbl = QLabel("💾 SQLite")
        self.db_lbl.setStyleSheet(lbl_style)
        
        self.time_lbl = QLabel("")
        self.time_lbl.setStyleSheet(lbl_style)
        
        layout.addWidget(self.status_lbl)
        layout.addStretch()
        layout.addWidget(self.db_lbl)
        layout.addWidget(self.user_lbl)
        layout.addWidget(self.time_lbl)
        
        # Auto-update time
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(1000)
        self._update_time()
    
    def _update_time(self):
        from datetime import datetime
        self.time_lbl.setText(datetime.now().strftime("🕐 %I:%M %p"))
    
    def set_status(self, msg: str, color: str = None):
        color = color or Theme.SUCCESS
        self.status_lbl.setText(f"● {msg}")
        self.status_lbl.setStyleSheet(f"font-size: 11px; color: {color}; border: none; background: transparent;")
    
    def set_user(self, name: str):
        self.user_lbl.setText(f"👤 {name}")


class EmptyState(QWidget):
    """Placeholder widget shown when a table or list has no data."""
    
    def __init__(self, icon: str, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"font-size: 48px; color: {Theme.TEXT_MUTED}; background: transparent;")
        
        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {Theme.TEXT_SECONDARY}; background: transparent;")
        
        sub_lbl = QLabel(subtitle)
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_MUTED}; background: transparent;")
        
        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl)
        if subtitle:
            layout.addWidget(sub_lbl)


class ProductFormDialog(QDialog):
    """Modal dialog for creating or editing a product."""
    
    def __init__(self, parent=None, product_data=None):
        super().__init__(parent)
        self.product_data = product_data
        self.result_data = None
        
        self.setWindowTitle("Edit Product" if product_data else "Add New Product")
        self.setFixedSize(480, 520)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("Edit Product" if product_data else "New Product")
        title.setStyleSheet(Theme.label_title())
        layout.addWidget(title)
        
        # Form
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)
        
        label_style = f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; font-weight: 500;"
        
        self.sku_input = QLineEdit()
        self.sku_input.setStyleSheet(Theme.input_style())
        self.sku_input.setPlaceholderText("e.g., SKU-001")
        
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(Theme.input_style())
        self.name_input.setPlaceholderText("Product name")
        
        self.category_input = QLineEdit()
        self.category_input.setStyleSheet(Theme.input_style())
        self.category_input.setPlaceholderText("e.g., Groceries")
        
        self.unit_input = QLineEdit("pcs")
        self.unit_input.setStyleSheet(Theme.input_style())
        
        self.sell_price = QDoubleSpinBox()
        self.sell_price.setRange(0, 9999999)
        self.sell_price.setDecimals(2)
        self.sell_price.setPrefix("৳ ")
        self.sell_price.setStyleSheet(Theme.spin_style())
        
        self.cost_price = QDoubleSpinBox()
        self.cost_price.setRange(0, 9999999)
        self.cost_price.setDecimals(2)
        self.cost_price.setPrefix("৳ ")
        self.cost_price.setStyleSheet(Theme.spin_style())
        
        self.reorder_qty = QSpinBox()
        self.reorder_qty.setRange(0, 999999)
        self.reorder_qty.setValue(50)
        self.reorder_qty.setStyleSheet(Theme.spin_style())
        
        for label_text, widget in [
            ("SKU Code *", self.sku_input),
            ("Product Name *", self.name_input),
            ("Category", self.category_input),
            ("Unit", self.unit_input),
            ("Sell Price *", self.sell_price),
            ("Cost Price", self.cost_price),
            ("Reorder Qty", self.reorder_qty),
        ]:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            form.addRow(lbl, widget)
        
        layout.addLayout(form)
        
        # Pre-fill if editing
        if product_data:
            self.sku_input.setText(str(product_data.get('sku_code', '')))
            self.name_input.setText(str(product_data.get('name', '')))
            self.category_input.setText(str(product_data.get('category', '')))
            self.unit_input.setText(str(product_data.get('unit', 'pcs')))
            self.sell_price.setValue(float(product_data.get('sell_price', 0)))
            self.cost_price.setValue(float(product_data.get('cost_price', 0)))
            self.reorder_qty.setValue(int(product_data.get('reorder_qty', 50)))
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(Theme.btn_ghost())
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Update Product" if product_data else "Create Product")
        save_btn.setStyleSheet(Theme.btn_primary())
        save_btn.clicked.connect(self._save)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
    
    def _save(self):
        sku = self.sku_input.text().strip()
        name = self.name_input.text().strip()
        
        if not sku or not name:
            QMessageBox.warning(self, "Validation", "SKU and Product Name are required.")
            return
        if self.sell_price.value() <= 0:
            QMessageBox.warning(self, "Validation", "Sell price must be greater than 0.")
            return
        
        self.result_data = {
            'sku_code': sku,
            'name': name,
            'category': self.category_input.text().strip() or 'General',
            'unit': self.unit_input.text().strip() or 'pcs',
            'sell_price': self.sell_price.value(),
            'cost_price': self.cost_price.value(),
            'reorder_qty': self.reorder_qty.value(),
            'status': 'Active'
        }
        if self.product_data:
            self.result_data['product_id'] = self.product_data.get('product_id')
        
        self.accept()


class ConfirmDialog(QDialog):
    """Professional confirmation dialog."""
    
    def __init__(self, title: str, message: str, details: str = "",
                 confirm_text: str = "Confirm", confirm_color: str = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(420, 220)
        self.setStyleSheet(f"QDialog {{ background-color: {Theme.BG_PRIMARY}; color: {Theme.TEXT_PRIMARY}; }}")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(Theme.label_title())
        layout.addWidget(title_lbl)
        
        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(f"font-size: 14px; color: {Theme.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(msg_lbl)
        
        if details:
            det_lbl = QLabel(details)
            det_lbl.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_MUTED}; background: transparent;")
            layout.addWidget(det_lbl)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(Theme.btn_ghost())
        cancel_btn.clicked.connect(self.reject)
        
        confirm_btn = QPushButton(confirm_text)
        style = Theme.btn_danger() if confirm_color == "danger" else Theme.btn_success() if confirm_color == "success" else Theme.btn_primary()
        confirm_btn.setStyleSheet(style)
        confirm_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)
