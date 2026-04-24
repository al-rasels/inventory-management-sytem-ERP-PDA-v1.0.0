from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt

class PySideSettings(QWidget):
    def __init__(self, db_engine):
        super().__init__()
        self.db = db_engine
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(20)
        
        self._build_header()
        self._build_sync_pane()
        self._build_backup_pane()
        self.layout.addStretch()
        
    def _build_header(self):
        header = QFrame()
        header.setStyleSheet("background-color: #2D3748; border-radius: 8px;")
        header.setFixedHeight(60)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel("⚙️ System Settings & Data Management")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #F7FAFC;")
        layout.addWidget(title)
        
        self.layout.addWidget(header)

    def _build_sync_pane(self):
        pane = QFrame()
        pane.setStyleSheet("background-color: #2D3748; border-radius: 12px;")
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("Excel Integration")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #63B3ED;")
        layout.addWidget(title)
        
        desc = QLabel("Sync your primary SQLite database with the legacy Excel tracking sheet.")
        desc.setStyleSheet("color: #A0AEC0;")
        layout.addWidget(desc)
        
        btn_layout = QHBoxLayout()
        
        import_btn = QPushButton("⬇️ Force Import from Excel")
        import_btn.setStyleSheet("""
            QPushButton { background-color: #DD6B20; color: white; border-radius: 6px; padding: 10px 20px; font-weight: bold; }
            QPushButton:hover { background-color: #C05621; }
        """)
        import_btn.clicked.connect(self._sync_excel)
        
        export_btn = QPushButton("⬆️ Export DB to Excel")
        export_btn.setStyleSheet("""
            QPushButton { background-color: #38A169; color: white; border-radius: 6px; padding: 10px 20px; font-weight: bold; }
            QPushButton:hover { background-color: #2F855A; }
        """)
        export_btn.clicked.connect(self._sync_excel)
        
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        self.layout.addWidget(pane)

    def _build_backup_pane(self):
        pane = QFrame()
        pane.setStyleSheet("background-color: #2D3748; border-radius: 12px;")
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("Database Backup & Restore")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #63B3ED;")
        layout.addWidget(title)
        
        desc = QLabel("Create secure ZIP backups of your entire SQLite database and Excel files.")
        desc.setStyleSheet("color: #A0AEC0;")
        layout.addWidget(desc)
        
        btn_layout = QHBoxLayout()
        
        backup_btn = QPushButton("📦 Create Full Backup")
        backup_btn.setStyleSheet("""
            QPushButton { background-color: #3182CE; color: white; border-radius: 6px; padding: 10px 20px; font-weight: bold; }
            QPushButton:hover { background-color: #2B6CB0; }
        """)
        backup_btn.clicked.connect(self._create_backup)
        
        btn_layout.addWidget(backup_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        self.layout.addWidget(pane)

    def _sync_excel(self):
        try:
            from src.repositories.sync_manager import SyncManager
            SyncManager(self.db).sync_all()
            QMessageBox.information(self, "Success", "Excel Synchronization Completed Successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Sync Error", str(e))
            
    def _create_backup(self):
        try:
            from src.core.safety import BackupService
            BackupService.create_backup(self.db.db_path)
            QMessageBox.information(self, "Success", "Backup Created Successfully in /backups directory!")
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", str(e))
