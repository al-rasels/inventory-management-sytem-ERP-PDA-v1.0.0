from src.repositories.base_repository import BaseRepository
from typing import Optional
import pandas as pd

class SupplierRepository(BaseRepository):
    """Handles data access for suppliers."""
    
    def get_all(self) -> pd.DataFrame:
        return self.db.execute_query("SELECT * FROM suppliers ORDER BY created_at DESC")

    def get_by_id(self, supplier_id: str) -> Optional[dict]:
        df = self.db.execute_query("SELECT * FROM suppliers WHERE supplier_id = ?", (supplier_id,))
        return df.iloc[0].to_dict() if not df.empty else None

    def get_next_id(self) -> str:
        df = self.db.execute_query("SELECT COUNT(*) as cnt FROM suppliers")
        count = int(df.iloc[0]['cnt']) + 1
        return f"SUP-{count:04d}"

    def create(self, data: dict) -> bool:
        query = """INSERT INTO suppliers 
            (supplier_id, name, phone, email, address, contact_person, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?)"""
        params = (
            data['supplier_id'], data['name'], data.get('phone', ''),
            data.get('email', ''), data.get('address', ''),
            data.get('contact_person', ''), data.get('status', 'Active')
        )
        self.db.execute_write(query, params)
        return True

    def update(self, supplier_id: str, data: dict) -> bool:
        fields = []
        params = []
        for key, val in data.items():
            if key in ['name', 'phone', 'email', 'address', 'contact_person', 'status']:
                fields.append(f"{key}=?")
                params.append(val)
        
        if not fields:
            return False
            
        query = f"UPDATE suppliers SET {', '.join(fields)} WHERE supplier_id=?"
        params.append(supplier_id)
        self.db.execute_write(query, tuple(params))
        return True

    def delete(self, supplier_id: str) -> bool:
        self.db.execute_write("DELETE FROM suppliers WHERE supplier_id = ?", (supplier_id,))
        return True

    def search(self, query: str) -> pd.DataFrame:
        sql = """
            SELECT * FROM suppliers 
            WHERE LOWER(name) LIKE ? OR LOWER(phone) LIKE ? OR LOWER(email) LIKE ?
        """
        term = f"%{query.lower()}%"
        return self.db.execute_query(sql, (term, term, term))

    def get_supplier_purchases(self, supplier_id: str) -> pd.DataFrame:
        return self.db.execute_query("""
            SELECT p.*, pr.name as product_name
            FROM purchases p
            JOIN products pr ON p.product_id = pr.product_id
            WHERE p.supplier = ?
            ORDER BY p.date DESC
        """, (supplier_id,))

    def get_top_suppliers(self, limit: int = 10) -> pd.DataFrame:
        return self.db.execute_query("""
            SELECT s.*, SUM(p.total_cost) as total_purchased
            FROM suppliers s
            LEFT JOIN purchases p ON s.name = p.supplier
            GROUP BY s.supplier_id
            ORDER BY total_purchased DESC
            LIMIT ?
        """, (limit,))
