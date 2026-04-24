from typing import List, Optional, Tuple, Literal
import pandas as pd
from src.core.exceptions import ProductNotFoundError, InsufficientStockError

class InventoryService:
    """Manages stock levels, FIFO costing, and inventory reports."""
    
    def __init__(self, product_repo, sales_repo, purchase_repo):
        self.product_repo = product_repo
        self.sales_repo = sales_repo
        self.purchase_repo = purchase_repo

    def get_stock_status(self, product_id: Optional[str] = None) -> pd.DataFrame:
        """Calculates current stock balance and valuation for all or specific products."""
        all_products = self.product_repo.get_all()
        all_purchases = self.purchase_repo.get_all()
        all_sales = self.sales_repo.get_all()
        
        if product_id:
            all_products = all_products[all_products['product_id'] == product_id]
            
        df = all_products.copy()
        
        # Calculate totals
        purch_sums = all_purchases.groupby('product_id')['qty'].sum().reset_index()
        sales_sums = all_sales.groupby('product_id')['qty'].sum().reset_index()
        
        df = df.merge(purch_sums, on='product_id', how='left').rename(columns={'qty': 'total_in'})
        df = df.merge(sales_sums, on='product_id', how='left').rename(columns={'qty': 'total_out'})
        
        df['total_in'] = df['total_in'].fillna(0)
        df['total_out'] = df['total_out'].fillna(0)
        df['current_stock'] = df['total_in'] - df['total_out']
        df['inventory_value'] = df['current_stock'] * df['cost_price'].fillna(0)
        
        return df

    def validate_sufficient_stock(self, product_id: str, qty_needed: int):
        """Ensures enough stock is available before a sale."""
        df = self.get_stock_status(product_id)
        if df.empty:
            raise ProductNotFoundError(product_id)
        
        current = df.iloc[0]['current_stock']
        if current < qty_needed:
            raise InsufficientStockError(product_id, current, qty_needed)

    def calculate_item_cost(self, product_id: str, qty_sold: int) -> float:
        """Calculates COGS using FIFO logic."""
        all_purchases = self.purchase_repo.get_all()
        batches = all_purchases[all_purchases['product_id'] == product_id].sort_values('date', ascending=True)
        
        all_sales = self.sales_repo.get_all()
        total_previously_sold = all_sales[all_sales['product_id'] == product_id]['qty'].sum()
        
        remaining_to_skip = total_previously_sold
        remaining_to_sell = qty_sold
        total_cogs = 0.0

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
                remaining_to_sell = 0
                break
            else:
                total_cogs += available_in_batch * batch_cost
                remaining_to_sell -= available_in_batch
        
        if remaining_to_sell > 0:
            product = self.product_repo.get_by_id(product_id)
            fallback_cost = product['cost_price'] if product else 0
            total_cogs += remaining_to_sell * (fallback_cost or 0)
            
        return total_cogs

    def get_low_stock_report(self) -> pd.DataFrame:
        """Returns products below their reorder threshold."""
        df = self.get_stock_status()
        return df[df['current_stock'] < df['reorder_qty']].sort_values('current_stock')

    def get_dead_stock(self, days: int = 30) -> pd.DataFrame:
        """Products with no sales in the last N days."""
        all_prods = self.product_repo.get_all()
        all_sales = self.sales_repo.get_all()
        
        # Calculate last sale date
        last_sales = all_sales.groupby('product_id')['date'].max().reset_index()
        df = all_prods.merge(last_sales, on='product_id', how='left').rename(columns={'date': 'last_sale_date'})
        
        # Filtering logic...
        return df # Simplified for now
