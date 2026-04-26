from src.repositories.base_repository import BaseRepository
from typing import Optional
import pandas as pd

class CustomerRepository(BaseRepository):
    """Handles data access for customers."""
    
    def get_all(self) -> pd.DataFrame:
        return self.db.execute_query("SELECT * FROM customers ORDER BY created_at DESC")

    def get_by_id(self, customer_id: str) -> Optional[dict]:
        df = self.db.execute_query("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
        return df.iloc[0].to_dict() if not df.empty else None

    def get_next_id(self) -> str:
        df = self.db.execute_query("SELECT COUNT(*) as cnt FROM customers")
        count = int(df.iloc[0]['cnt']) + 1
        return f"CUST-{count:04d}"

    def create(self, data: dict) -> bool:
        query = """INSERT INTO customers 
            (customer_id, name, phone, email, address, loyalty_points, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?)"""
        params = (
            data['customer_id'], data['name'], data.get('phone', ''),
            data.get('email', ''), data.get('address', ''),
            data.get('loyalty_points', 0), data.get('status', 'Active')
        )
        self.db.execute_write(query, params)
        return True

    def update(self, customer_id: str, data: dict) -> bool:
        fields = []
        params = []
        for key, val in data.items():
            if key in ['name', 'phone', 'email', 'address', 'loyalty_points', 'status']:
                fields.append(f"{key}=?")
                params.append(val)
        
        if not fields:
            return False
            
        query = f"UPDATE customers SET {', '.join(fields)} WHERE customer_id=?"
        params.append(customer_id)
        self.db.execute_write(query, tuple(params))
        return True

    def delete(self, customer_id: str) -> bool:
        self.db.execute_write("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
        return True

    def search(self, query: str) -> pd.DataFrame:
        sql = """
            SELECT * FROM customers 
            WHERE LOWER(name) LIKE ? OR LOWER(phone) LIKE ? OR LOWER(email) LIKE ?
        """
        term = f"%{query.lower()}%"
        return self.db.execute_query(sql, (term, term, term))

    def add_loyalty_points(self, customer_id: str, points: int) -> bool:
        self.db.execute_write(
            "UPDATE customers SET loyalty_points = loyalty_points + ? WHERE customer_id = ?",
            (points, customer_id)
        )
        return True

    def get_top_customers(self, limit: int = 10) -> pd.DataFrame:
        return self.db.execute_query("""
            SELECT c.*, SUM(s.revenue) as total_spent
            FROM customers c
            LEFT JOIN sales s ON c.name = s.customer
            GROUP BY c.customer_id
            ORDER BY total_spent DESC
            LIMIT ?
        """, (limit,))
