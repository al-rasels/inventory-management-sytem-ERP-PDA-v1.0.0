import sqlite3
import pandas as pd
import openpyxl
from datetime import datetime
from src.core.config import EXCEL_DB_PATH, SQLITE_DB_PATH
from src.core.safety import SafetyManager
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseEngine:
    def __init__(self):
        self.sqlite_path = SQLITE_DB_PATH
        self.excel_path = EXCEL_DB_PATH
        self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite schema if it doesn't exist."""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                sku_code TEXT,
                name TEXT,
                category TEXT,
                unit TEXT,
                status TEXT,
                sell_price REAL,
                cost_price REAL,
                reorder_qty INTEGER
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                purchase_id TEXT PRIMARY KEY,
                date TEXT,
                product_id TEXT,
                batch_id TEXT,
                supplier TEXT DEFAULT '',
                qty INTEGER,
                cost_per_unit REAL,
                total_cost REAL,
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                sales_id TEXT PRIMARY KEY,
                date TEXT,
                product_id TEXT,
                customer TEXT DEFAULT 'Walk-in',
                qty INTEGER,
                sell_price REAL,
                discount REAL DEFAULT 0,
                revenue REAL,
                cogs REAL,
                profit REAL,
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                user TEXT,
                action TEXT,
                details TEXT
            )
        ''')

        # Indexes for performance on 50,000+ records
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchases_product ON purchases(product_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchases_date ON purchases(date)')

        conn.commit()
        conn.close()

    def execute_query(self, query, params=()):
        """Execute a SELECT query and return a pandas DataFrame."""
        conn = sqlite3.connect(self.sqlite_path)
        try:
            df = pd.read_sql_query(query, conn, params=params)
            return df
        finally:
            conn.close()

    def execute_write(self, query, params=()):
        """Execute an INSERT/UPDATE/DELETE query."""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
        finally:
            conn.close()
        """Manually sync all SQLite data back to the Master Excel file."""
        import openpyxl
        try:
            wb = openpyxl.load_workbook(self.excel_path)
            
            # Sync Sales
            ws_sales = wb['Sales_Log']
            df_sales = self.execute_query("SELECT * FROM sales")
            # Clear old rows (starting from row 5)
            for row in range(5, ws_sales.max_row + 1):
                for col in range(1, 10):
                    ws_sales.cell(row=row, column=col).value = None
            
            for i, row in df_sales.iterrows():
                r = i + 5
                ws_sales.cell(row=r, column=1).value = row['sales_id']
                ws_sales.cell(row=r, column=2).value = row['date']
                ws_sales.cell(row=r, column=3).value = row['product_id']
                ws_sales.cell(row=r, column=5).value = row['qty']
                ws_sales.cell(row=r, column=6).value = row['sell_price']
                ws_sales.cell(row=r, column=7).value = row['revenue']
            
            wb.save(self.excel_path)
            return True, "Sync to Excel completed successfully!"
        except Exception as e:
            return False, str(e)
