from src.repositories.base_repository import BaseRepository
from typing import List, Any, Optional
import pandas as pd

class ProductRepository(BaseRepository):
    """Handles data access for products."""
    
    def get_all(self) -> pd.DataFrame:
        return self.db.execute_query("SELECT * FROM products")

    def get_by_id(self, product_id: str) -> Optional[dict]:
        df = self.db.execute_query("SELECT * FROM products WHERE product_id = ?", (product_id,))
        return df.iloc[0].to_dict() if not df.empty else None

    def search(self, query: str) -> pd.DataFrame:
        sql = """
            SELECT * FROM products 
            WHERE LOWER(sku_code) = LOWER(?) 
               OR LOWER(product_id) = LOWER(?) 
               OR name LIKE ?
        """
        return self.db.execute_query(sql, (query, query, f"%{query}%"))

    def create(self, data: dict) -> bool:
        query = """INSERT INTO products 
            (product_id, sku_code, name, category, unit, status, sell_price, cost_price, reorder_qty) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        params = (
            data['product_id'], data.get('sku_code', ''), data['name'], 
            data.get('category', ''), data.get('unit', 'pcs'), data.get('status', 'Active'),
            data.get('sell_price', 0), data.get('cost_price', 0), data.get('reorder_qty', 0)
        )
        self.db.execute_write(query, params)
        return True

    def update(self, product_id: str, data: dict) -> bool:
        fields = []
        params = []
        for key, val in data.items():
            if key in ['sku_code', 'name', 'category', 'unit', 'status', 'sell_price', 'cost_price', 'reorder_qty']:
                fields.append(f"{key}=?")
                params.append(val)
        
        if not fields:
            return False
            
        query = f"UPDATE products SET {', '.join(fields)} WHERE product_id=?"
        params.append(product_id)
        self.db.execute_write(query, tuple(params))
        return True

    def delete(self, product_id: str) -> bool:
        self.db.execute_write("DELETE FROM products WHERE product_id = ?", (product_id,))
        return True
        
    def get_categories(self) -> List[str]:
        df = self.db.execute_query("SELECT DISTINCT category FROM products")
        return df['category'].tolist()
