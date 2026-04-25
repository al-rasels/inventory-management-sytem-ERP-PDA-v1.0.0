from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
from src.utils.export_import import DataExporter

class ReportService:
    """Provides high-level reporting and analytics data."""
    
    def __init__(self, db, pdf_service):
        self.db = db
        self.pdf_service = pdf_service

    def export_sales_report(self, days: int = 30):
        """Generates a PDF sales report."""
        summary = self.get_sales_summary(days)
        headers = ["Metric", "Value"]
        data = [
            ["Total Revenue", f"{summary['revenue']:,.2f}"],
            ["Total Profit", f"{summary['profit']:,.2f}"],
            ["Total Units", str(summary['units'])]
        ]
        return self.pdf_service.generate_report(f"Sales Report (Last {days} Days)", headers, data, "Sales_Report")

    def export_inventory_valuation(self):
        """Generates a PDF inventory valuation report."""
        valuation = self.get_inventory_valuation()
        headers = ["Summary Item", "Amount"]
        data = [["Total Inventory Value", f"{valuation:,.2f}"]]
        return self.pdf_service.generate_report("Inventory Valuation Report", headers, data, "Inv_Valuation")

    def export_csv(self, table_name: str):
        """Export a table to CSV."""
        return DataExporter.export_csv(self.db, table_name)

    def export_excel(self):
        """Export full system report to Excel."""
        return DataExporter.export_excel_report(self.db)

    def get_sales_summary(self, days: Optional[int] = 30) -> Dict[str, Any]:
        """Returns summary of sales over a period, or all-time if days is None."""
        query = """
            SELECT SUM(revenue) as total_revenue, 
                   SUM(profit) as total_profit,
                   SUM(qty) as total_units,
                   COUNT(DISTINCT sales_id) as total_transactions
            FROM sales 
        """
        params = ()
        if days is not None:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            query += " WHERE date >= ?"
            params = (start_date,)
            
        df = self.db.execute_query(query, params)
        if df.empty or df.iloc[0]['total_revenue'] is None:
            return {"revenue": 0, "profit": 0, "units": 0, "sales_count": 0}
        
        return {
            "revenue": float(df.iloc[0]['total_revenue']),
            "profit": float(df.iloc[0]['total_profit']),
            "units": int(df.iloc[0]['total_units']),
            "sales_count": int(df.iloc[0]['total_transactions'])
        }

    def get_top_selling_products(self, limit: int = 5) -> pd.DataFrame:
        """Returns top products by revenue with category and profit."""
        query = """
            SELECT p.name, p.category, SUM(s.qty) as units, SUM(s.revenue) as rev, SUM(s.profit) as prof
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            GROUP BY p.product_id
            ORDER BY rev DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (limit,))

    def get_dead_stock(self, days: int = 30) -> pd.DataFrame:
        """Returns products with no sales in the given period."""
        query = """
            SELECT p.name, p.category, 
                   (SELECT MAX(date) FROM sales WHERE product_id = p.product_id) as last_sale_date
            FROM products p
            WHERE p.product_id NOT IN (
                SELECT DISTINCT product_id FROM sales WHERE date >= ?
            )
        """
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return self.db.execute_query(query, (start_date,))

    def get_inventory_valuation(self) -> float:
        """Calculates total value of current inventory based on cost price."""
        query = """
            SELECT SUM(balance * cost_price) as valuation
            FROM (
                SELECT p.cost_price,
                       (IFNULL((SELECT SUM(qty) FROM purchases WHERE product_id = p.product_id), 0) - 
                        IFNULL((SELECT SUM(qty) FROM sales WHERE product_id = p.product_id), 0)) as balance
                FROM products p
            )
        """
        df = self.db.execute_query(query)
        return float(df.iloc[0]['valuation'] or 0)

    def get_monthly_trends(self) -> pd.DataFrame:
        """Returns monthly revenue and profit trends."""
        query = """
            SELECT strftime('%Y-%m', date) as month, 
                   SUM(revenue) as revenue, 
                   SUM(profit) as profit
            FROM sales
            GROUP BY month
            ORDER BY month ASC
        """
        return self.db.execute_query(query)

    def get_reorder_alerts(self) -> pd.DataFrame:
        """Returns products with current stock below reorder threshold."""
        query = """
            SELECT p.name, 
                   (IFNULL((SELECT SUM(qty) FROM purchases WHERE product_id = p.product_id), 0) - 
                    IFNULL((SELECT SUM(qty) FROM sales WHERE product_id = p.product_id), 0)) as current_stock
            FROM products p
            WHERE current_stock < p.reorder_qty
            ORDER BY current_stock ASC
        """
        return self.db.execute_query(query)

    def get_profit_by_category(self) -> pd.DataFrame:
        """Returns revenue, profit, and margin by product category."""
        query = """
            SELECT p.category, SUM(s.revenue) as rev, SUM(s.profit) as prof,
                   CASE WHEN SUM(s.revenue) > 0 THEN SUM(s.profit) * 100.0 / SUM(s.revenue) ELSE 0 END as margin
            FROM sales s JOIN products p ON s.product_id = p.product_id
            GROUP BY p.category ORDER BY prof DESC
        """
        return self.db.execute_query(query)

    def get_recent_activity(self, limit: int = 8) -> pd.DataFrame:
        """Returns combined recent sales and purchases."""
        query = """
            SELECT 'SALE' as type, s.date, p.name, s.revenue as amt
            FROM sales s JOIN products p ON s.product_id = p.product_id
            UNION ALL
            SELECT 'PURCHASE' as type, pur.date, p.name, pur.total_cost as amt
            FROM purchases pur JOIN products p ON pur.product_id = p.product_id
            ORDER BY date DESC LIMIT ?
        """
        return self.db.execute_query(query, (limit,))

    def get_daily_sales_trend(self, days: int = 7) -> pd.DataFrame:
        """Returns daily revenue for charting."""
        query = """
            SELECT date, SUM(revenue) as daily_rev 
            FROM sales GROUP BY date ORDER BY date DESC LIMIT ?
        """
        return self.db.execute_query(query, (days,))

    def get_sales_history(self, search_term: Optional[str] = None) -> pd.DataFrame:
        """Returns sales history with optional filtering."""
        query = """
            SELECT s.sales_id, s.date, p.name as product_name, s.customer, s.qty, s.revenue 
            FROM sales s 
            JOIN products p ON s.product_id = p.product_id
            WHERE 1=1
        """
        params = []
        if search_term:
            query += " AND (s.sales_id LIKE ? OR p.name LIKE ? OR s.customer LIKE ?)"
            term = f"%{search_term}%"
            params.extend([term, term, term])
            
        query += " ORDER BY s.date DESC, s.sales_id DESC LIMIT 100"
        return self.db.execute_query(query, tuple(params))

    def get_purchase_history(self, search_term: Optional[str] = None) -> pd.DataFrame:
        """Returns purchase history with optional filtering."""
        query = """
            SELECT pur.purchase_id, pur.date, p.name as product_name, pur.supplier, pur.qty, pur.total_cost 
            FROM purchases pur
            JOIN products p ON pur.product_id = p.product_id
            WHERE 1=1
        """
        params = []
        if search_term:
            query += " AND (pur.purchase_id LIKE ? OR p.name LIKE ? OR pur.supplier LIKE ?)"
            term = f"%{search_term}%"
            params.extend([term, term, term])
            
        query += " ORDER BY pur.date DESC, pur.purchase_id DESC LIMIT 100"
        return self.db.execute_query(query, tuple(params))
