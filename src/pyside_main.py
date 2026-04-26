"""
SunERP Professional — Application Entry Point
Initializes all services, repositories, and launches the PySide6 UI.

Icons are provided by QtAwesome in the UI layer (views, widgets, app window).
No icon or emoji strings are required at this level.
"""
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from src.core.database import DatabaseEngine
from src.core.safety import AuditLogger
from src.repositories.product_repository import ProductRepository
from src.repositories.sales_repository import SalesRepository
from src.repositories.purchase_repository import PurchaseRepository
from src.repositories.audit_repository import AuditRepository
from src.repositories.return_repository import ReturnRepository
from src.services.inventory_service import InventoryService
from src.services.sales_service import SalesService
from src.services.purchase_service import PurchaseService
from src.services.product_service import ProductService
from src.services.report_service import ReportService
from src.services.pdf_service import PDFService
from src.services.return_service import ReturnService
from src.ui.pyside.app import ERPAppWindow


def main():
    app = QApplication(sys.argv)

    # Global font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # ── Core ──
    db = DatabaseEngine()

    # Wire AuditLogger to write to SQLite
    AuditLogger.set_db(db)

    # ── Repositories ──
    product_repo = ProductRepository(db)
    sales_repo = SalesRepository(db)
    purchase_repo = PurchaseRepository(db)
    audit_repo = AuditRepository(db)
    return_repo = ReturnRepository(db)

    # ── Services ──
    pdf_service = PDFService()
    product_service = ProductService(product_repo)
    inventory_service = InventoryService(product_repo, sales_repo, purchase_repo)
    sales_service = SalesService(sales_repo, inventory_service, pdf_service)
    purchase_service = PurchaseService(purchase_repo, product_service)
    report_service = ReportService(db, pdf_service)
    return_service = ReturnService(return_repo, sales_repo, inventory_service)

    services = {
        'inventory': inventory_service,
        'sales': sales_service,
        'purchase': purchase_service,
        'product': product_service,
        'report': report_service,
        'return': return_service,
        'db': db,
    }

    # ── Launch ──
    window = ERPAppWindow(services)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
