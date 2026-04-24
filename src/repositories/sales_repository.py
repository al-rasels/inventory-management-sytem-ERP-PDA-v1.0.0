from src.repositories.base_repository import BaseRepository
from typing import List, Any, Optional
import pandas as pd

class SalesRepository(BaseRepository):
    def __init__(self, db, sync_manager=None):
        super().__init__(db)
        self.sync_manager = sync_manager
    
    def get_all(self) -> pd.DataFrame:
        return self.db.execute_query("SELECT * FROM sales ORDER BY date DESC")

    def get_by_id(self, sale_id: str) -> Optional[dict]:
        df = self.db.execute_query("SELECT * FROM sales WHERE sales_id = ?", (sale_id,))
        return df.iloc[0].to_dict() if not df.empty else None

    def get_next_id(self) -> str:
        df = self.db.execute_query("SELECT COUNT(*) as cnt FROM sales")
        count = int(df.iloc[0]['cnt']) + 1
        return f"SL-{count:05d}"

    def create(self, data: dict) -> bool:
        query = """INSERT INTO sales 
            (sales_id, date, product_id, customer, qty, sell_price, discount, revenue, cogs, profit) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        params = (
            data['sales_id'], data['date'], data['product_id'], data.get('customer', 'Walk-in'),
            data['qty'], data['sell_price'], data.get('discount', 0), 
            data['revenue'], data['cogs'], data['profit']
        )
        self.db.execute_write(query, params)
        
        if self.sync_manager:
            self.sync_manager.sync_sale_to_excel(data)
            
        return True

    def update(self, sale_id: str, data: dict) -> bool:
        # Sales are typically immutable, but update method is here for completeness
        query = "UPDATE sales SET customer=? WHERE sales_id=?"
        self.db.execute_write(query, (data['customer'], sale_id))
        return True

    def delete(self, sale_id: str) -> bool:
        self.db.execute_write("DELETE FROM sales WHERE sales_id = ?", (sale_id,))
        return True
