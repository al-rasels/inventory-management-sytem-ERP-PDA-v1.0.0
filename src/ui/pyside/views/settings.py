"""Settings View — Database management, backup, and export."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from src.ui.pyside.theme import Theme
from src.ui.pyside.widgets import ConfirmDialog


class PySideSettings(QWidget):
    def __init__(self, db_engine):
        super().__init__()
        self.db = db_engine
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        self._build_header(layout)
        self._build_backup(layout)
        self._build_export(layout)
        self._build_sync(layout)
        layout.addStretch()

    def _build_header(self, parent):
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"QFrame {{ background-color: {Theme.BG_SECONDARY}; border-radius: {Theme.RADIUS_MD}; border: 1px solid {Theme.BORDER}; }}")
        h = QHBoxLayout(bar)
        h.setContentsMargins(20, 0, 20, 0)
        t = QLabel("⚙️  System Settings & Data Management")
        t.setStyleSheet(Theme.label_title())
        h.addWidget(t)
        parent.addWidget(bar)

    def _build_backup(self, parent):
        frame = QFrame()
        frame.setStyleSheet(Theme.card_style())
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(12)
        t = QLabel("💾  Database Backup & Restore")
        t.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.ACCENT_LIGHT}; border:none; background:transparent;")
        vl.addWidget(t)
        d = QLabel("Create a snapshot of your SQLite database. Use restore to recover from a backup file.")
        d.setStyleSheet(Theme.label_muted())
        d.setWordWrap(True)
        vl.addWidget(d)
        bl = QHBoxLayout()
        bb = QPushButton("📦 Create Backup")
        bb.setStyleSheet(Theme.btn_primary())
        bb.clicked.connect(self._create_backup)
        rb = QPushButton("♻️ Restore from Backup")
        rb.setStyleSheet(Theme.btn_ghost())
        rb.clicked.connect(self._restore_backup)
        bl.addWidget(bb)
        bl.addWidget(rb)
        bl.addStretch()
        vl.addLayout(bl)
        parent.addWidget(frame)

    def _build_export(self, parent):
        frame = QFrame()
        frame.setStyleSheet(Theme.card_style())
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(12)
        t = QLabel("📊  Export Reports")
        t.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.ACCENT_LIGHT}; border:none; background:transparent;")
        vl.addWidget(t)
        d = QLabel("Export your data as Excel or CSV for external analysis.")
        d.setStyleSheet(Theme.label_muted())
        d.setWordWrap(True)
        vl.addWidget(d)
        bl = QHBoxLayout()
        eb = QPushButton("📑 Export Full Excel Report")
        eb.setStyleSheet(Theme.btn_success())
        eb.clicked.connect(self._export_excel)
        cb = QPushButton("📄 Export CSV")
        cb.setStyleSheet(Theme.btn_ghost())
        cb.clicked.connect(self._export_csv)
        bl.addWidget(eb)
        bl.addWidget(cb)
        bl.addStretch()
        vl.addLayout(bl)
        parent.addWidget(frame)

    def _build_sync(self, parent):
        frame = QFrame()
        frame.setStyleSheet(Theme.card_style())
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(12)
        t = QLabel("🔄  Excel Legacy Sync")
        t.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.ACCENT_LIGHT}; border:none; background:transparent;")
        vl.addWidget(t)
        d = QLabel("Import data from a legacy Excel Master Database into SQLite.")
        d.setStyleSheet(Theme.label_muted())
        d.setWordWrap(True)
        vl.addWidget(d)
        bl = QHBoxLayout()
        ib = QPushButton("⬇️ Import from Excel")
        ib.setStyleSheet(Theme.btn_warning())
        ib.clicked.connect(self._import_excel)
        bl.addWidget(ib)
        bl.addStretch()
        vl.addLayout(bl)
        parent.addWidget(frame)

    def _create_backup(self):
        try:
            from src.core.safety import SafetyManager
            path = SafetyManager.create_backup()
            if path:
                QMessageBox.information(self, "Backup Created ✓", f"Backup saved to:\n{path}")
            else:
                QMessageBox.warning(self, "Backup Failed", "Could not create backup.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _restore_backup(self):
        from src.core.config import BACKUP_DIR
        path, _ = QFileDialog.getOpenFileName(self, "Select Backup File", BACKUP_DIR, "Database Files (*.db);;All Files (*)")
        if not path: return
        dlg = ConfirmDialog("Restore Backup", "This will replace your current database. Are you sure?",
                            confirm_text="Restore", confirm_color="danger", parent=self)
        if dlg.exec():
            try:
                from src.core.safety import SafetyManager
                SafetyManager.rollback(path)
                QMessageBox.information(self, "Restored ✓", "Database restored. Restart the application.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _export_excel(self):
        try:
            from src.utils.export_import import DataExporter
            path = DataExporter.export_excel_report(self.db)
            QMessageBox.information(self, "Export Complete ✓", f"Report saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _export_csv(self):
        from PySide6.QtWidgets import QInputDialog
        tables = ["products", "sales", "purchases", "inventory"]
        choice, ok = QInputDialog.getItem(self, "Export CSV", "Select data to export:", tables, 0, False)
        if ok and choice:
            try:
                from src.utils.export_import import DataExporter
                path = DataExporter.export_csv(self.db, choice)
                QMessageBox.information(self, "Export Complete ✓", f"CSV saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def _import_excel(self):
        from src.core.config import BASE_DIR
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel Database", BASE_DIR, "Excel Files (*.xlsx)")
        if not path: return
        dlg = ConfirmDialog("Import Excel", "This will replace products, sales, and purchases. Continue?",
                            confirm_text="Import", confirm_color="danger", parent=self)
        if dlg.exec():
            try:
                from src.repositories.sync_manager import SyncManager
                sm = SyncManager(self.db)
                sm.excel_path = path
                ok, msg = sm.sync_all_from_excel()
                if ok:
                    QMessageBox.information(self, "Import Complete ✓", msg)
                else:
                    QMessageBox.warning(self, "Import Issue", msg)
            except Exception as e:
                QMessageBox.critical(self, "Import Error", str(e))

    def refresh(self): pass
