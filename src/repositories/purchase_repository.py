from src.repositories.base_repository import BaseRepository
from typing import List, Any, Optional
import pandas as pd

class PurchaseRepository(BaseRepository):
    def __init__(self, db, sync_manager=None):
        super().__init__(db)
        self.sync_manager = sync_manager
    
    def get_all(self) -> pd.DataFrame:
        return self.db.execute_query("SELECT * FROM purchases ORDER BY date DESC")

    def get_by_id(self, batch_id: str) -> Optional[dict]:
        df = self.db.execute_query("SELECT * FROM purchases WHERE batch_id = ?", (batch_id,))
        return df.iloc[0].to_dict() if not df.empty else None

    def get_next_id(self) -> str:
        df = self.db.execute_query("SELECT COUNT(*) as cnt FROM purchases")
        count = int(df.iloc[0]['cnt']) + 1
        return f"PUR-{count:04d}"

    def create(self, data: dict) -> bool:
        query = """INSERT INTO purchases 
            (purchase_id, date, product_id, batch_id, supplier, qty, cost_per_unit, total_cost) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        params = (
            data.get('purchase_id', ''), data['date'], data['product_id'], data['batch_id'],
            data.get('supplier', 'Standard'), data['qty'], data['cost_per_unit'], data['total_cost']
        )
        self.db.execute_write(query, params)
        
        if self.sync_manager:
            self.sync_manager.sync_purchase_to_excel(data)
            
        return True

    def update(self, batch_id: str, data: dict) -> bool:
        query = "UPDATE purchases SET supplier=? WHERE batch_id=?"
        self.db.execute_write(query, (data['supplier'], batch_id))
        return True

    def delete(self, batch_id: str) -> bool:
        self.db.execute_write("DELETE FROM purchases WHERE batch_id = ?", (batch_id,))
        return True
