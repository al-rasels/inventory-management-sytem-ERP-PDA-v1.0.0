import sqlite3
import pandas as pd
from datetime import datetime
from src.core.config import SQLITE_DB_PATH
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseEngine:
    def __init__(self):
        self.db_path = SQLITE_DB_PATH
        self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                sku_code TEXT UNIQUE,
                name TEXT NOT NULL,
                category TEXT DEFAULT '',
                unit TEXT DEFAULT 'pcs',
                status TEXT DEFAULT 'Active',
                sell_price REAL DEFAULT 0,
                cost_price REAL DEFAULT 0,
                reorder_qty INTEGER DEFAULT 50
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                purchase_id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                product_id TEXT NOT NULL,
                batch_id TEXT,
                supplier TEXT DEFAULT '',
                qty INTEGER NOT NULL,
                cost_per_unit REAL NOT NULL,
                total_cost REAL NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                sales_id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                product_id TEXT NOT NULL,
                customer TEXT DEFAULT 'Walk-in',
                qty INTEGER NOT NULL,
                sell_price REAL NOT NULL,
                discount REAL DEFAULT 0,
                revenue REAL NOT NULL,
                cogs REAL DEFAULT 0,
                profit REAL DEFAULT 0,
                payment_method TEXT DEFAULT 'Cash',
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'Cashier',
                full_name TEXT DEFAULT ''
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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS held_sales (
                hold_id TEXT PRIMARY KEY,
                customer TEXT DEFAULT 'Walk-in',
                cart_json TEXT NOT NULL,
                discount REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                note TEXT DEFAULT ''
            )
        ''')

        # Indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchases_product ON purchases(product_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchases_date ON purchases(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku_code)')

        # Seed default admin if users table is empty
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            import hashlib
            pw_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                ('admin', pw_hash, 'Admin', 'System Administrator')
            )

        conn.commit()
        conn.close()

    def execute_query(self, query, params=()):
        """Execute a SELECT query and return a pandas DataFrame."""
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query(query, conn, params=params)
            return df
        finally:
            conn.close()

    def execute_write(self, query, params=()):
        """Execute an INSERT/UPDATE/DELETE query."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Write failed: {e}")
            raise
        finally:
            conn.close()

    def execute_many(self, query, params_list):
        """Execute a batch write operation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.executemany(query, params_list)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Batch write failed: {e}")
            raise
        finally:
            conn.close()
