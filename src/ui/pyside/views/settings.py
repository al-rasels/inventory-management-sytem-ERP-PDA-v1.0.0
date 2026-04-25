"""
Settings View — Database management, backup, export, and import.
All icons use QtAwesome. Long operations run in background threads.
"""
from __future__ import annotations

import logging
from typing import Callable, Optional, Any

from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QFileDialog, QStackedWidget, QProgressBar,
    QTextEdit, QApplication, QStyle, QScrollArea
)
from qtawesome import icon as qta_icon

from src.ui.pyside.theme import Theme
from src.ui.pyside.widgets import ConfirmDialog

logger = logging.getLogger(__name__)


# =====================================================================
# Generic background worker for settings operations
# =====================================================================
class SettingsWorker(QThread):
    """Runs a callable in a background thread and reports result."""
    finished_ok = Signal(str)      # success message
    finished_error = Signal(str)   # error message

    def __init__(self, target: Callable[..., Any], *args, **kwargs):
        super().__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.target(*self.args, **self.kwargs)
            # If the callable returns a path (str) or None, we'll emit that
            msg = str(result) if result else "Operation completed successfully."
            self.finished_ok.emit(msg)
        except Exception as e:
            logger.exception("Settings worker failed")
            self.finished_error.emit(str(e))


# =====================================================================
# Main Settings Widget
# =====================================================================
class PySideSettings(QWidget):
    def __init__(self, db_engine, parent=None):
        super().__init__(parent)
        self.db = db_engine
        self._worker: Optional[SettingsWorker] = None

        # Main layout with a stacked widget for content / loading / error
        self.stack = QStackedWidget(self)
        # Page 0: normal content (Scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        normal_layout = QVBoxLayout(scroll_content)
        normal_layout.setContentsMargins(10, 10, 10, 10)
        normal_layout.setSpacing(20)
        
        self._build_header(normal_layout)
        self._build_appearance(normal_layout)
        self._build_info(normal_layout)
        self._build_backup(normal_layout)
        self._build_maintenance(normal_layout)
        self._build_export(normal_layout)
        self._build_sync(normal_layout)
        self._build_about(normal_layout)
        normal_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        self.stack.addWidget(scroll)  # index 0
        
        # Page 1: loading overlay
        loading_page = self._create_loading_widget()
        self.stack.addWidget(loading_page)  # index 1
        
        # Page 2: error overlay
        error_page = self._create_error_widget()
        self.stack.addWidget(error_page)   # index 2

        # Set as main layout
        main_wrapper = QVBoxLayout(self)
        main_wrapper.setContentsMargins(0, 0, 0, 0)
        main_wrapper.addWidget(self.stack)

    # ----- UI construction -------------------------------------------------
    def _build_header(self, parent):
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(
            f"QFrame {{ background-color: {Theme.BG_SECONDARY}; "
            f"border-radius: {Theme.RADIUS_MD}; border: 1px solid {Theme.BORDER}; }}"
        )
        h = QHBoxLayout(bar)
        h.setContentsMargins(20, 0, 20, 0)

        icon_label = QLabel()
        icon_label.setPixmap(qta_icon('fa5s.cog', color=Theme.TEXT_PRIMARY).pixmap(20, 20))
        h.addWidget(icon_label)

        title = QLabel("System Settings & Data Management")
        title.setStyleSheet(Theme.label_title())
        h.addWidget(title)
        h.addStretch()

        parent.addWidget(bar)

    def _build_appearance(self, parent):
        frame = QFrame()
        frame.setObjectName("SettingsCard")
        frame.setStyleSheet(Theme.card_style())
        frame.setMinimumHeight(120)
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(12)

        # Title
        title_row = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(qta_icon('fa5s.palette', color=Theme.ACCENT_LIGHT).pixmap(18, 18))
        title_row.addWidget(title_icon)
        title = QLabel("Appearance & Theme")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {Theme.ACCENT_LIGHT}; "
            "border:none; background:transparent;"
        )
        title_row.addWidget(title)
        title_row.addStretch()
        vl.addLayout(title_row)

        desc = QLabel("Choose your preferred visual style for the application.")
        desc.setStyleSheet(Theme.label_muted())
        vl.addWidget(desc)

        btn_row = QHBoxLayout()
        dark_btn = QPushButton(" Dark Mode")
        dark_btn.setIcon(qta_icon('fa5s.moon', color='white'))
        dark_btn.setStyleSheet(Theme.btn_primary() if Theme.current_theme == Theme.DARK else Theme.btn_ghost())
        dark_btn.clicked.connect(lambda: self._switch_theme(Theme.DARK))
        btn_row.addWidget(dark_btn)

        light_btn = QPushButton(" Light Mode")
        light_btn.setIcon(qta_icon('fa5s.sun', color=Theme.TEXT_PRIMARY))
        light_btn.setStyleSheet(Theme.btn_primary() if Theme.current_theme == Theme.LIGHT else Theme.btn_ghost())
        light_btn.clicked.connect(lambda: self._switch_theme(Theme.LIGHT))
        btn_row.addWidget(light_btn)

        btn_row.addStretch()
        vl.addLayout(btn_row)
        parent.addWidget(frame)

    def _switch_theme(self, mode):
        if Theme.current_theme == mode:
            return
        
        Theme.apply_theme(mode)
        # Apply to entire application
        app = QApplication.instance()
        if app:
            app.setStyleSheet(Theme.global_stylesheet())
        
        # Refresh current view manually to update icons and colors
        self._refresh_icons_and_styles()
        
        # In a real app, we might emit a global signal. For now, we update the main app's components if possible.
        # But global_stylesheet should handle most things.
        
        # Refresh the settings view buttons state
        self.stack.setCurrentIndex(0) 
        # Re-build or just update button styles? Re-building is easier for a prototype.
        # Let's just update the specific button styles.
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QStackedWidget):
                # This is a bit deep. For now, let's just warn that some icons might need restart.
                pass
        
        QMessageBox.information(self, "Theme Changed", f"Switched to {mode.capitalize()} mode. Some UI elements may require a restart for full effect.")

    def _refresh_icons_and_styles(self):
        # Refresh this specific widget's custom styles
        self.setStyleSheet(f"background-color: {Theme.BG_PRIMARY};")
        pass

    def _build_info(self, parent):
        frame = QFrame()
        frame.setObjectName("SettingsCard")
        frame.setStyleSheet(Theme.card_style())
        frame.setMinimumHeight(80)
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(10)

        title_row = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(qta_icon('fa5s.info-circle', color=Theme.ACCENT_LIGHT).pixmap(18, 18))
        title_row.addWidget(title_icon)
        title = QLabel("System Information")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.ACCENT_LIGHT}; border:none; background:transparent;")
        title_row.addWidget(title)
        title_row.addStretch()
        vl.addLayout(title_row)

        import os
        from src.core.config import SQLITE_DB_PATH
        db_size = os.path.getsize(SQLITE_DB_PATH) / (1024 * 1024) if os.path.exists(SQLITE_DB_PATH) else 0
        
        info_grid = QHBoxLayout()
        info_grid.addWidget(QLabel(f"Database Path: {SQLITE_DB_PATH}", styleSheet=Theme.label_muted()))
        info_grid.addStretch()
        info_grid.addWidget(QLabel(f"Size: {db_size:.2f} MB", styleSheet=Theme.label_muted()))
        vl.addLayout(info_grid)
        parent.addWidget(frame)

    def _build_maintenance(self, parent):
        frame = QFrame()
        frame.setObjectName("SettingsCard")
        frame.setStyleSheet(Theme.card_style())
        frame.setMinimumHeight(120)
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(12)

        title_row = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(qta_icon('fa5s.tools', color=Theme.ACCENT_LIGHT).pixmap(18, 18))
        title_row.addWidget(title_icon)
        title = QLabel("System Maintenance")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.ACCENT_LIGHT}; border:none; background:transparent;")
        title_row.addWidget(title)
        title_row.addStretch()
        vl.addLayout(title_row)

        btn_row = QHBoxLayout()
        compact_btn = QPushButton(" Optimize Database")
        compact_btn.setIcon(qta_icon('fa5s.compress-arrows-alt', color='white'))
        compact_btn.setStyleSheet(Theme.btn_primary())
        compact_btn.clicked.connect(self._compact_db)
        btn_row.addWidget(compact_btn)
        
        open_logs_btn = QPushButton(" View System Logs")
        open_logs_btn.setIcon(qta_icon('fa5s.file-alt', color=Theme.TEXT_PRIMARY))
        open_logs_btn.setStyleSheet(Theme.btn_ghost())
        open_logs_btn.clicked.connect(self._open_logs)
        btn_row.addWidget(open_logs_btn)
        
        btn_row.addStretch()
        vl.addLayout(btn_row)
        parent.addWidget(frame)

    def _open_logs(self):
        import os
        from src.core.config import LOG_DIR
        if os.path.exists(LOG_DIR):
            os.startfile(LOG_DIR)
        else:
            QMessageBox.warning(self, "Error", "Log directory not found.")

    def _build_about(self, parent):
        frame = QFrame()
        frame.setObjectName("SettingsCard")
        frame.setStyleSheet(Theme.card_style())
        frame.setMinimumHeight(120)
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setAlignment(Qt.AlignCenter)
        
        logo = QLabel("SunERP Professional")
        logo.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {Theme.ACCENT}; border:none; background:transparent;")
        vl.addWidget(logo, alignment=Qt.AlignCenter)
        
        ver = QLabel("Version 1.0.0 Stable")
        ver.setStyleSheet(Theme.label_muted())
        vl.addWidget(ver, alignment=Qt.AlignCenter)
        
        copy = QLabel("© 2026 Sun Warehouse Solutions. All rights reserved.")
        copy.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED}; border:none; background:transparent;")
        vl.addWidget(copy, alignment=Qt.AlignCenter)
        
        parent.addWidget(frame)

    def _compact_db(self):
        def compact_target():
            self.db.execute_query("VACUUM")
            return "Database optimized and compacted successfully."
        self._start_operation(compact_target)

    def _build_backup(self, parent):
        frame = QFrame()
        frame.setObjectName("SettingsCard")
        frame.setStyleSheet(Theme.card_style())
        frame.setMinimumHeight(140)
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(12)

        # Title row
        title_row = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(qta_icon('fa5s.database', color=Theme.ACCENT_LIGHT).pixmap(18, 18))
        title_row.addWidget(title_icon)
        title = QLabel("Database Backup & Restore")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {Theme.ACCENT_LIGHT}; "
            "border:none; background:transparent;"
        )
        title_row.addWidget(title)
        title_row.addStretch()
        vl.addLayout(title_row)

        desc = QLabel("Create a snapshot of your SQLite database. Use restore to recover from a backup file.")
        desc.setStyleSheet(Theme.label_muted())
        desc.setWordWrap(True)
        vl.addWidget(desc)

        btn_row = QHBoxLayout()
        backup_btn = QPushButton()
        backup_btn.setIcon(qta_icon('fa5s.download', color='white'))
        backup_btn.setText(" Create Backup")
        backup_btn.setStyleSheet(Theme.btn_primary())
        backup_btn.clicked.connect(self._create_backup)
        btn_row.addWidget(backup_btn)

        restore_btn = QPushButton()
        restore_btn.setIcon(qta_icon('fa5s.upload', color=Theme.TEXT_PRIMARY))
        restore_btn.setText(" Restore from Backup")
        restore_btn.setStyleSheet(Theme.btn_ghost())
        restore_btn.clicked.connect(self._restore_backup)
        btn_row.addWidget(restore_btn)

        btn_row.addStretch()
        vl.addLayout(btn_row)
        parent.addWidget(frame)

    def _build_export(self, parent):
        frame = QFrame()
        frame.setObjectName("SettingsCard")
        frame.setStyleSheet(Theme.card_style())
        frame.setMinimumHeight(140)
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(12)

        # Title
        title_row = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(qta_icon('fa5s.file-export', color=Theme.ACCENT_LIGHT).pixmap(18, 18))
        title_row.addWidget(title_icon)
        title = QLabel("Export Reports")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {Theme.ACCENT_LIGHT}; "
            "border:none; background:transparent;"
        )
        title_row.addWidget(title)
        title_row.addStretch()
        vl.addLayout(title_row)

        desc = QLabel("Export your data as Excel or CSV for external analysis.")
        desc.setStyleSheet(Theme.label_muted())
        desc.setWordWrap(True)
        vl.addWidget(desc)

        btn_row = QHBoxLayout()
        excel_btn = QPushButton()
        excel_btn.setIcon(qta_icon('fa5s.file-excel', color='white'))
        excel_btn.setText(" Export Full Excel Report")
        excel_btn.setStyleSheet(Theme.btn_success())
        excel_btn.clicked.connect(self._export_excel)
        btn_row.addWidget(excel_btn)

        csv_btn = QPushButton()
        csv_btn.setIcon(qta_icon('fa5s.file-csv', color=Theme.TEXT_PRIMARY))
        csv_btn.setText(" Export CSV")
        csv_btn.setStyleSheet(Theme.btn_ghost())
        csv_btn.clicked.connect(self._export_csv)
        btn_row.addWidget(csv_btn)

        btn_row.addStretch()
        vl.addLayout(btn_row)
        parent.addWidget(frame)

    def _build_sync(self, parent):
        frame = QFrame()
        frame.setObjectName("SettingsCard")
        frame.setStyleSheet(Theme.card_style())
        frame.setMinimumHeight(140)
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(12)

        # Title
        title_row = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(qta_icon('fa5s.sync-alt', color=Theme.ACCENT_LIGHT).pixmap(18, 18))
        title_row.addWidget(title_icon)
        title = QLabel("Excel Legacy Sync")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {Theme.ACCENT_LIGHT}; "
            "border:none; background:transparent;"
        )
        title_row.addWidget(title)
        title_row.addStretch()
        vl.addLayout(title_row)

        desc = QLabel("Import data from a legacy Excel Master Database into SQLite.")
        desc.setStyleSheet(Theme.label_muted())
        desc.setWordWrap(True)
        vl.addWidget(desc)

        btn_row = QHBoxLayout()
        import_btn = QPushButton()
        import_btn.setIcon(qta_icon('fa5s.file-import', color='white'))
        import_btn.setText(" Import from Excel")
        import_btn.setStyleSheet(Theme.btn_warning())
        import_btn.clicked.connect(self._import_excel)
        btn_row.addWidget(import_btn)
        btn_row.addStretch()
        vl.addLayout(btn_row)

        parent.addWidget(frame)

    # ----- Loading & Error overlays ----------------------------------------
    def _create_loading_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel("Please wait, operation in progress...")
        lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 16px;")
        layout.addWidget(lbl)
        prog = QProgressBar()
        prog.setRange(0, 0)   # indeterminate
        prog.setFixedWidth(300)
        layout.addWidget(prog, alignment=Qt.AlignCenter)
        return w

    def _create_error_widget(self):
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
        retry_btn.clicked.connect(self._retry_last_action)
        layout.addWidget(retry_btn, alignment=Qt.AlignCenter)

        return w

    # ----- Operation helpers (start worker) --------------------------------
    def _start_operation(self, target, *args, **kwargs):
        """Show loading overlay, start worker, connect signals."""
        try:
            if self._worker and self._worker.isRunning():
                self._worker.quit()
                self._worker.wait(2000)
        except RuntimeError:
            pass

        self.stack.setCurrentIndex(1)  # loading page

        self._worker = SettingsWorker(target, *args, **kwargs)
        self._worker.finished_ok.connect(self._on_operation_success)
        self._worker.finished_error.connect(self._on_operation_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    @Slot(str)
    def _on_operation_success(self, msg):
        self.stack.setCurrentIndex(0)  # back to normal content
        QMessageBox.information(self, "Operation Complete", msg)

    @Slot(str)
    def _on_operation_error(self, msg):
        self.error_label.setText("Operation failed.")
        self.error_detail.setPlainText(msg)
        self.error_detail.setVisible(True)
        self.stack.setCurrentIndex(2)  # show error page

    def _retry_last_action(self):
        """Retry the last failed operation by re‑calling the appropriate method."""
        # For simplicity, just return to main page; user must re‑click the button.
        self.stack.setCurrentIndex(0)

    # ----- Action handlers -------------------------------------------------
    def _create_backup(self):
        from src.core.safety import SafetyManager
        # The backup function returns the path of the created file (or None)
        def backup_target():
            path = SafetyManager.create_backup()
            if not path:
                raise RuntimeError("Backup creation returned no path.")
            return f"Backup saved to:\n{path}"
        self._start_operation(backup_target)

    def _restore_backup(self):
        from src.core.config import BACKUP_DIR
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", BACKUP_DIR,
            "Database Files (*.db);;All Files (*)"
        )
        if not path:
            return

        dlg = ConfirmDialog(
            "Restore Backup",
            "This will replace your current database. Are you sure?",
            confirm_text="Restore", confirm_color="danger", parent=self
        )
        if dlg.exec() != ConfirmDialog.Accepted:
            return

        from src.core.safety import SafetyManager
        def restore_target():
            SafetyManager.rollback(path)
            return "Database restored. Please restart the application."
        self._start_operation(restore_target)

    def _export_excel(self):
        from src.utils.export_import import DataExporter
        def export_target():
            path = DataExporter.export_excel_report(self.db)
            return f"Report saved to:\n{path}"
        self._start_operation(export_target)

    def _export_csv(self):
        from PySide6.QtWidgets import QInputDialog
        tables = ["products", "sales", "purchases", "inventory"]
        choice, ok = QInputDialog.getItem(
            self, "Export CSV", "Select data to export:", tables, 0, False
        )
        if not ok or not choice:
            return

        from src.utils.export_import import DataExporter
        def export_target():
            path = DataExporter.export_csv(self.db, choice)
            return f"CSV saved to:\n{path}"
        self._start_operation(export_target)

    def _import_excel(self):
        from src.core.config import BASE_DIR
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel Database", BASE_DIR, "Excel Files (*.xlsx)"
        )
        if not path:
            return

        dlg = ConfirmDialog(
            "Import Excel",
            "This will replace products, sales, and purchases. Continue?",
            confirm_text="Import", confirm_color="danger", parent=self
        )
        if dlg.exec() != ConfirmDialog.Accepted:
            return

        from src.repositories.sync_manager import SyncManager
        def import_target():
            sm = SyncManager(self.db)
            sm.excel_path = path
            ok, msg = sm.sync_all_from_excel()
            if not ok:
                raise RuntimeError(msg)
            return msg
        self._start_operation(import_target)

    def refresh(self):
        """No dynamic content to refresh."""
        pass