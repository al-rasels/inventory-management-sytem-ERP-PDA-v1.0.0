from src.repositories.base_repository import BaseRepository
from typing import Optional
import pandas as pd

class ReturnRepository(BaseRepository):
    """Handles data access for product returns."""
    
    def get_all(self) -> pd.DataFrame:
        return self.db.execute_query("""
            SELECT r.*, p.name as product_name, p.sku_code 
            FROM returns r 
            JOIN products p ON r.product_id = p.product_id 
            ORDER BY r.date DESC
        """)

    def get_by_id(self, return_id: str) -> Optional[dict]:
        df = self.db.execute_query("""
            SELECT r.*, p.name as product_name 
            FROM returns r 
            JOIN products p ON r.product_id = p.product_id 
            WHERE r.return_id = ?
        """, (return_id,))
        return df.iloc[0].to_dict() if not df.empty else None

    def get_next_id(self) -> str:
        df = self.db.execute_query("SELECT COUNT(*) as cnt FROM returns")
        count = int(df.iloc[0]['cnt']) + 1
        return f"RT-{count:05d}"

    def create(self, data: dict) -> bool:
        query = """INSERT INTO returns 
            (return_id, date, product_id, original_sale_id, qty, refund_amount, 
             return_reason, return_type, refund_method, status, processed_by) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        params = (
            data['return_id'], data['date'], data['product_id'], 
            data.get('original_sale_id', ''), data['qty'], data['refund_amount'],
            data.get('return_reason', ''), data.get('return_type', 'full'),
            data.get('refund_method', 'cash'), data.get('status', 'completed'),
            data.get('processed_by', 'SYSTEM')
        )
        self.db.execute_write(query, params)
        return True

    def get_returns_by_product(self, product_id: str) -> pd.DataFrame:
        return self.db.execute_query("""
            SELECT * FROM returns WHERE product_id = ? ORDER BY date DESC
        """, (product_id,))

    def get_returns_by_sale(self, sale_id: str) -> pd.DataFrame:
        return self.db.execute_query("""
            SELECT * FROM returns WHERE original_sale_id = ? ORDER BY date DESC
        """, (sale_id,))

    def get_return_summary(self, days: Optional[int] = None) -> dict:
        base_query = """
            SELECT COUNT(*) as total_returns, 
                   SUM(qty) as total_qty, 
                   SUM(refund_amount) as total_refunds
            FROM returns WHERE status = 'completed'
        """
        if days:
            from datetime import datetime, timedelta
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            base_query += f" AND date >= '{start_date}'"
        
        df = self.db.execute_query(base_query)
        if df.empty or df.iloc[0]['total_returns'] is None:
            return {"total_returns": 0, "total_qty": 0, "total_refunds": 0}
        
        return {
            "total_returns": int(df.iloc[0]['total_returns']),
            "total_qty": int(df.iloc[0]['total_qty']),
            "total_refunds": float(df.iloc[0]['total_refunds'])
        }

    def update(self, return_id: str, data: dict) -> bool:
        """Update a return record."""
        fields = []
        params = []
        allowed_fields = ['date', 'product_id', 'original_sale_id', 'qty', 
                         'refund_amount', 'return_reason', 'return_type', 
                         'refund_method', 'status', 'processed_by']
        for key, val in data.items():
            if key in allowed_fields:
                fields.append(f"{key}=?")
                params.append(val)
        
        if not fields:
            return False
            
        query = f"UPDATE returns SET {', '.join(fields)} WHERE return_id=?"
        params.append(return_id)
        self.db.execute_write(query, tuple(params))
        return True

    def delete(self, return_id: str) -> bool:
        """Delete a return record."""
        self.db.execute_write("DELETE FROM returns WHERE return_id = ?", (return_id,))
        return True
