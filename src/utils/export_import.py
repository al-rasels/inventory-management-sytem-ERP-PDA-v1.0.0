"""
Export/Import and Data Migration Utilities for Sun Warehouse ERP.

Handles:
- Full system export (ZIP archive with Excel + SQLite + config)
- Full system import (restore from ZIP)
- CSV report export (products, sales, purchases, inventory)
- Excel report export
"""
import os
import shutil
import zipfile
import csv
from datetime import datetime
from src.core.config import BASE_DIR, EXCEL_DB_PATH, SQLITE_DB_PATH, DATA_DIR, BACKUP_DIR, INVOICE_DIR, EXPORTS_DIR

class DataExporter:
    """Exports data in various formats for reporting and migration."""

    @staticmethod
    def export_full_system(output_path=None):
        """
        Creates a complete ZIP archive of the entire system state.
        Used for migrating to a new computer or creating a full backup.
        
        Contents:
        - SunWarehouse_ERP_v3.xlsx (primary database)
        - data/erp_cache.db (SQLite cache)
        - All invoices
        - All backups (last 3)
        
        Returns: path to the created ZIP file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_path:
            output_path = os.path.join(EXPORTS_DIR, f"ERP_Migration_{timestamp}.zip")

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. Primary Excel database
            if os.path.exists(EXCEL_DB_PATH):
                zf.write(EXCEL_DB_PATH, "SunWarehouse_ERP_v3.xlsx")

            # 2. SQLite cache
            if os.path.exists(SQLITE_DB_PATH):
                zf.write(SQLITE_DB_PATH, "data/erp_cache.db")

            # 3. Latest 3 backups
            if os.path.exists(BACKUP_DIR):
                backups = sorted(
                    [f for f in os.listdir(BACKUP_DIR) if f.endswith('.xlsx')],
                    reverse=True
                )[:3]
                for b in backups:
                    zf.write(os.path.join(BACKUP_DIR, b), f"backups/{b}")

            # 4. All invoices
            if os.path.exists(INVOICE_DIR):
                for inv in os.listdir(INVOICE_DIR):
                    if inv.endswith('.pdf'):
                        zf.write(os.path.join(INVOICE_DIR, inv), f"invoices/{inv}")

        return output_path

    @staticmethod
    def export_csv(db, table_name, output_path=None):
        """
        Export a specific table to CSV format.
        table_name: 'products', 'sales', 'purchases', 'inventory'
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if table_name == "inventory":
            query = """
                SELECT p.product_id, p.sku_code, p.name, p.category, p.unit,
                       p.sell_price, p.cost_price,
                       IFNULL(purch.total_in, 0) as total_purchased,
                       IFNULL(sold.total_out, 0) as total_sold,
                       (IFNULL(purch.total_in, 0) - IFNULL(sold.total_out, 0)) as current_stock
                FROM products p
                LEFT JOIN (SELECT product_id, SUM(qty) as total_in FROM purchases GROUP BY product_id) purch 
                    ON p.product_id = purch.product_id
                LEFT JOIN (SELECT product_id, SUM(qty) as total_out FROM sales GROUP BY product_id) sold 
                    ON p.product_id = sold.product_id
                ORDER BY p.product_id
            """
        elif table_name == "products":
            query = "SELECT * FROM products ORDER BY product_id"
        elif table_name == "sales":
            query = "SELECT * FROM sales ORDER BY date DESC"
        elif table_name == "purchases":
            query = "SELECT * FROM purchases ORDER BY date DESC"
        else:
            raise ValueError(f"Unknown table: {table_name}")

        df = db.execute_query(query)
        
        if not output_path:
            output_path = os.path.join(EXPORTS_DIR, f"{table_name}_{timestamp}.csv")
        
        df.to_csv(output_path, index=False, encoding='utf-8-sig')  # utf-8-sig for Excel compatibility
        return output_path

    @staticmethod
    def export_excel_report(db, output_path=None):
        """
        Export a comprehensive Excel report with all tables in separate sheets.
        """
        import pandas as pd
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not output_path:
            output_path = os.path.join(EXPORTS_DIR, f"ERP_Report_{timestamp}.xlsx")
        
        products = db.execute_query("SELECT * FROM products ORDER BY product_id")
        sales = db.execute_query("SELECT * FROM sales ORDER BY date DESC")
        purchases = db.execute_query("SELECT * FROM purchases ORDER BY date DESC")
        
        # Inventory summary
        inventory = db.execute_query("""
            SELECT p.product_id, p.name, p.category,
                   IFNULL(purch.total_in, 0) as purchased,
                   IFNULL(sold.total_out, 0) as sold,
                   (IFNULL(purch.total_in, 0) - IFNULL(sold.total_out, 0)) as balance,
                   p.cost_price,
                   (IFNULL(purch.total_in, 0) - IFNULL(sold.total_out, 0)) * p.cost_price as stock_value
            FROM products p
            LEFT JOIN (SELECT product_id, SUM(qty) as total_in FROM purchases GROUP BY product_id) purch ON p.product_id = purch.product_id
            LEFT JOIN (SELECT product_id, SUM(qty) as total_out FROM sales GROUP BY product_id) sold ON p.product_id = sold.product_id
            ORDER BY p.product_id
        """)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            products.to_excel(writer, sheet_name='Products', index=False)
            sales.to_excel(writer, sheet_name='Sales', index=False)
            purchases.to_excel(writer, sheet_name='Purchases', index=False)
            inventory.to_excel(writer, sheet_name='Inventory Summary', index=False)
        
        return output_path


class DataImporter:
    """Imports/restores data from migration archives."""

    @staticmethod
    def import_full_system(zip_path, db):
        """
        Restore the entire system from a migration ZIP archive.
        
        Steps:
        1. Backup current state
        2. Extract ZIP contents
        3. Replace Excel and SQLite files
        4. Re-sync database
        
        Returns: (success: bool, message: str)
        """
        if not os.path.exists(zip_path):
            return False, f"File not found: {zip_path}"
        
        if not zipfile.is_zipfile(zip_path):
            return False, "Invalid ZIP file"

        try:
            # Step 1: Backup current state first
            from src.core.safety import SafetyManager
            SafetyManager.create_backup()

            # Step 2: Extract
            with zipfile.ZipFile(zip_path, 'r') as zf:
                file_list = zf.namelist()
                
                # Step 3: Restore Excel if present
                if "SunWarehouse_ERP_v3.xlsx" in file_list:
                    zf.extract("SunWarehouse_ERP_v3.xlsx", BASE_DIR)
                
                # Step 4: Restore SQLite if present
                if "data/erp_cache.db" in file_list:
                    os.makedirs(DATA_DIR, exist_ok=True)
                    zf.extract("data/erp_cache.db", BASE_DIR)
                
                # Step 5: Restore invoices
                for f in file_list:
                    if f.startswith("invoices/") and f.endswith('.pdf'):
                        os.makedirs(INVOICE_DIR, exist_ok=True)
                        zf.extract(f, BASE_DIR)
                
                # Step 6: Restore backups
                for f in file_list:
                    if f.startswith("backups/") and f.endswith('.xlsx'):
                        os.makedirs(BACKUP_DIR, exist_ok=True)
                        zf.extract(f, BASE_DIR)

            # Step 7: Re-sync database
            db.sync_from_excel()
            
            return True, f"System restored from {os.path.basename(zip_path)}. {len(file_list)} files imported."
        
        except Exception as e:
            return False, f"Import failed: {str(e)}"

    @staticmethod
    def import_csv(db, csv_path, table_name):
        """
        Import data from a CSV file into a specific table.
        Appends to existing data (does not replace).
        
        Returns: (success: bool, message: str, rows_imported: int)
        """
        import pandas as pd
        import sqlite3
        
        if not os.path.exists(csv_path):
            return False, f"File not found: {csv_path}", 0
        
        try:
            df = pd.read_csv(csv_path)
            conn = sqlite3.connect(SQLITE_DB_PATH)
            rows_before = pd.read_sql_query(f"SELECT COUNT(*) as c FROM {table_name}", conn).iloc[0]['c']
            df.to_sql(table_name, conn, if_exists='append', index=False)
            rows_after = pd.read_sql_query(f"SELECT COUNT(*) as c FROM {table_name}", conn).iloc[0]['c']
            conn.close()
            
            imported = int(rows_after - rows_before)
            return True, f"Imported {imported} rows into {table_name}", imported
        except Exception as e:
            return False, f"CSV import failed: {str(e)}", 0
