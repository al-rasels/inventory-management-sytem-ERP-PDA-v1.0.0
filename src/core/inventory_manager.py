import sqlite3
import pandas as pd
from src.core.config import SQLITE_DB_PATH

class InventoryManager:
    def __init__(self, db_engine):
        self.db = db_engine

    def get_current_stock(self, product_id=None):
        """Calculates current stock by subtracting sales from purchases."""
        query = """
            SELECT p.product_id, p.name, p.category, p.cost_price,
                   IFNULL(purch.total_in, 0) as total_in,
                   IFNULL(sold.total_out, 0) as total_out,
                   (IFNULL(purch.total_in, 0) - IFNULL(sold.total_out, 0)) as current_stock,
                   p.reorder_qty
            FROM products p
            LEFT JOIN (SELECT product_id, SUM(qty) as total_in FROM purchases GROUP BY product_id) purch 
                ON p.product_id = purch.product_id
            LEFT JOIN (SELECT product_id, SUM(qty) as total_out FROM sales GROUP BY product_id) sold 
                ON p.product_id = sold.product_id
        """
        if product_id:
            query += " WHERE p.product_id = ?"
            return self.db.execute_query(query, params=(product_id,))
        return self.db.execute_query(query)

    def get_stock_value(self, product_id):
        """Calculate stock value using average cost from purchases."""
        stock_df = self.get_current_stock(product_id)
        if stock_df.empty:
            return 0
        row = stock_df.iloc[0]
        avg_cost_query = """
            SELECT CASE WHEN SUM(qty) > 0 THEN SUM(total_cost) / SUM(qty) ELSE 0 END as avg_cost
            FROM purchases WHERE product_id = ?
        """
        avg_df = self.db.execute_query(avg_cost_query, params=(product_id,))
        avg_cost = avg_df.iloc[0]['avg_cost'] if not avg_df.empty else 0
        return row['current_stock'] * avg_cost

    def check_stock_available(self, product_id, qty_needed):
        """Check if enough stock is available before selling."""
        stock_df = self.get_current_stock(product_id)
        if stock_df.empty:
            return False, 0
        current = stock_df.iloc[0]['current_stock']
        return bool(current >= qty_needed), current

    def calculate_fifo_cogs(self, product_id, qty_sold):
        """
        Calculate COGS based on FIFO (First-In, First-Out).
        Returns (total_cogs, used_batches)
        """
        query = "SELECT batch_id, qty, cost_per_unit, date FROM purchases WHERE product_id = ? ORDER BY date ASC"
        batches = self.db.execute_query(query, params=(product_id,))
        
        sold_query = "SELECT IFNULL(SUM(qty), 0) as total_sold FROM sales WHERE product_id = ?"
        total_previously_sold = self.db.execute_query(sold_query, params=(product_id,)).iloc[0]['total_sold'] or 0
        
        remaining_to_skip = total_previously_sold
        remaining_to_sell = qty_sold
        total_cogs = 0.0
        used_batches = []

        for _, row in batches.iterrows():
            batch_qty = row['qty']
            batch_cost = row['cost_per_unit']
            
            if remaining_to_skip >= batch_qty:
                remaining_to_skip -= batch_qty
                continue
            
            available_in_batch = batch_qty - remaining_to_skip
            remaining_to_skip = 0
            
            if remaining_to_sell <= available_in_batch:
                total_cogs += remaining_to_sell * batch_cost
                used_batches.append({"batch_id": row['batch_id'], "qty": remaining_to_sell})
                remaining_to_sell = 0
                break
            else:
                total_cogs += available_in_batch * batch_cost
                used_batches.append({"batch_id": row['batch_id'], "qty": available_in_batch})
                remaining_to_sell -= available_in_batch
        
        if remaining_to_sell > 0:
            fallback_query = "SELECT cost_price FROM products WHERE product_id = ?"
            fallback_df = self.db.execute_query(fallback_query, params=(product_id,))
            fallback_cost = fallback_df.iloc[0]['cost_price'] if not fallback_df.empty else 0
            fallback_cost = fallback_cost or 0
            total_cogs += remaining_to_sell * fallback_cost
            used_batches.append({"batch_id": "FALLBACK", "qty": remaining_to_sell})
            
        return total_cogs, used_batches

    def get_low_stock_items(self):
        """Get products where current stock is below reorder quantity."""
        query = """
            SELECT p.product_id, p.name, p.category, p.reorder_qty,
                   (IFNULL(purch.total_in, 0) - IFNULL(sold.total_out, 0)) as current_stock
            FROM products p
            LEFT JOIN (SELECT product_id, SUM(qty) as total_in FROM purchases GROUP BY product_id) purch 
                ON p.product_id = purch.product_id
            LEFT JOIN (SELECT product_id, SUM(qty) as total_out FROM sales GROUP BY product_id) sold 
                ON p.product_id = sold.product_id
            WHERE current_stock < p.reorder_qty
            ORDER BY current_stock ASC
        """
        return self.db.execute_query(query)

    def get_dead_stock(self, days=30):
        """Products with no sales in the last N days."""
        query = """
            SELECT p.product_id, p.name, p.category,
                   MAX(s.date) as last_sale_date
            FROM products p
            LEFT JOIN sales s ON p.product_id = s.product_id
            GROUP BY p.product_id
            HAVING last_sale_date IS NULL 
                OR julianday('now') - julianday(last_sale_date) > ?
            ORDER BY last_sale_date ASC
        """
        return self.db.execute_query(query, params=(days,))
