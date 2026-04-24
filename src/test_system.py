import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.database import DatabaseEngine
from src.core.inventory_manager import InventoryManager
from src.core.safety import SafetyManager
from src.core.auth import AuthManager
from datetime import datetime

def run_tests():
    results = []
    
    def test(name, condition):
        status = "✅ PASS" if condition else "❌ FAIL"
        results.append((name, status))
        print(f"  {status}: {name}")

    print("=" * 60)
    print("  SunERP Professional v3.0 - Full System Test")
    print("=" * 60)

    # 1. Database Init & Sync
    print("\n📦 Phase 1: Database Engine")
    db = DatabaseEngine()
    db.sync_from_excel()
    
    products = db.execute_query("SELECT COUNT(*) as c FROM products")
    test("Products synced from Excel", products.iloc[0]['c'] > 0)
    
    purchases = db.execute_query("SELECT COUNT(*) as c FROM purchases")
    test("Purchases synced from Excel", purchases.iloc[0]['c'] > 0)
    
    sales = db.execute_query("SELECT COUNT(*) as c FROM sales")
    test("Sales synced from Excel", sales.iloc[0]['c'] > 0)

    # 2. Sequential IDs
    print("\n🔢 Phase 2: ID Generation")
    sid = db.get_next_sale_id()
    test("Sequential Sale ID generated", sid.startswith("SL-") and len(sid) == 8)
    
    pid = db.get_next_purchase_id()
    test("Sequential Purchase ID generated", pid.startswith("PUR-") and len(pid) == 8)

    # 3. Inventory Manager
    print("\n📊 Phase 3: Inventory Manager")
    im = InventoryManager(db)
    
    stock = im.get_current_stock("P001")
    test("Stock calculation works", not stock.empty)
    stock_val = stock.iloc[0]['current_stock']
    test("Stock returns numeric value", hasattr(stock_val, '__int__'))  # Works with numpy.int64 too
    
    available, current = im.check_stock_available("P001", 1)
    test("Stock availability check returns bool", isinstance(available, bool))
    test("Stock availability returns current count", hasattr(current, '__int__'))
    
    low = im.get_low_stock_items()
    test("Low stock query runs", low is not None)
    
    dead = im.get_dead_stock(days=30)
    test("Dead stock query runs", dead is not None)
    
    cogs, batches = im.calculate_fifo_cogs("P001", 5)
    test("FIFO COGS calculation returns value", cogs is not None and cogs > 0)
    test("FIFO returns batch details", len(batches) > 0)

    # 4. Auth
    print("\n🔐 Phase 4: Authentication")
    auth = AuthManager()
    user = auth.login("admin", "admin123")
    test("Admin login works", user is not None)
    test("Login returns role", user and user['role'] == 'Admin')
    
    bad = auth.login("fake", "wrong")
    test("Invalid login returns None", bad is None)

    # 5. Safety
    print("\n🛡️ Phase 5: Safety System")
    backup = SafetyManager.create_backup()
    test("Backup created successfully", backup is not None and os.path.exists(backup))

    # 6. Audit Log
    print("\n📝 Phase 6: Audit Logging")
    db.log_audit("test_user", "TEST", "System test audit entry")
    audit = db.execute_query("SELECT * FROM audit_logs WHERE user='test_user'")
    test("Audit log entry written", not audit.empty)

    # 7. Export/Import
    print("\n📦 Phase 7: Export / Import")
    from src.utils.export_import import DataExporter, DataImporter
    
    csv_path = DataExporter.export_csv(db, "products")
    test("CSV export works", csv_path is not None and os.path.exists(csv_path))
    
    csv_inv = DataExporter.export_csv(db, "inventory")
    test("Inventory CSV export works", csv_inv is not None and os.path.exists(csv_inv))
    
    xlsx_path = DataExporter.export_excel_report(db)
    test("Excel report export works", xlsx_path is not None and os.path.exists(xlsx_path))
    
    zip_path = DataExporter.export_full_system()
    test("Migration ZIP export works", zip_path is not None and os.path.exists(zip_path))
    
    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as zf:
        test("ZIP contains Excel file", "SunWarehouse_ERP_v3.xlsx" in zf.namelist())

    # 8. Password Change
    print("\n🔑 Phase 8: User Management")
    success, msg = auth.change_password("admin", "admin123", "admin123")
    test("Password change works", success)
    
    fail, msg = auth.change_password("admin", "wrong_old", "new_pass")
    test("Password change rejects wrong old password", not fail)

    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for _, s in results if "PASS" in s)
    failed = sum(1 for _, s in results if "FAIL" in s)
    print(f"  Results: {passed} passed, {failed} failed, {len(results)} total")
    print("=" * 60)
    
    if failed == 0:
        print("  🎉 ALL TESTS PASSED!")
    else:
        print("  ⚠️ Some tests failed. Review above.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
