import sys
import os

# Ensure the root project directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from src.core.database import DatabaseEngine
from src.repositories.product_repository import ProductRepository
from src.repositories.sales_repository import SalesRepository
from src.repositories.purchase_repository import PurchaseRepository
from src.repositories.audit_repository import AuditRepository
from src.services.inventory_service import InventoryService
from src.services.sales_service import SalesService
from src.services.purchase_service import PurchaseService
from src.services.product_service import ProductService
from src.services.report_service import ReportService
from src.ui.pyside.app import ERPAppWindow

def main():
    app = QApplication(sys.argv)
    
    # Initialize Core & Repositories
    db = DatabaseEngine()
    product_repo = ProductRepository(db)
    sales_repo = SalesRepository(db)
    purchase_repo = PurchaseRepository(db)
    audit_repo = AuditRepository(db)
    
    # Initialize PDF Service placeholder
    class DummyPDFService:
        def generate_receipt(self, sale_record): return True
    pdf_service = DummyPDFService()

    # Initialize Services
    product_service = ProductService(product_repo)
    inventory_service = InventoryService(product_repo, sales_repo, purchase_repo)
    sales_service = SalesService(sales_repo, inventory_service, pdf_service)
    purchase_service = PurchaseService(purchase_repo, product_service)
    report_service = ReportService(db, pdf_service)
    
    services = {
        'inventory': inventory_service,
        'sales': sales_service,
        'purchase': purchase_service,
        'product': product_service,
        'report': report_service,
        'db': db # Exposed for advanced debug/sync if needed
    }
    
    window = ERPAppWindow(services)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
