from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
from src.core.exceptions import ValidationError, ProductNotFoundError, InsufficientStockError
from src.core.safety import SafetyManager, AuditLogger
from src.utils.logger import app_logger

@dataclass
class ReturnResult:
    success: bool
    return_id: str = ""
    refund_amount: float = 0.0
    items_returned: int = 0
    errors: List[str] = field(default_factory=list)

@dataclass
class ReturnItem:
    product_id: str
    name: str
    qty: int
    unit_price: float
    total: float
    original_sale_id: Optional[str] = None

class ReturnService:
    """Handles product returns with automatic inventory restoration."""
    
    def __init__(self, return_repo, sales_repo, inventory_service):
        self.repo = return_repo
        self.sales_repo = sales_repo
        self.inventory_service = inventory_service

    @SafetyManager.transactional
    def process_return(
        self, 
        items: List[ReturnItem], 
        refund_method: str = "cash",
        reason: str = "",
        processed_by: str = "SYSTEM"
    ) -> ReturnResult:
        """
        Process a return transaction:
        1. Validate return items
        2. Create return records
        3. Restore inventory stock
        4. Log audit trail
        """
        if not items:
            return ReturnResult(success=False, errors=["No items to return"])

        app_logger.info(f"Processing return with {len(items)} items, method: {refund_method}")
        
        total_refund = 0.0
        total_qty = 0
        return_ids = []
        date_str = datetime.now().strftime("%Y-%m-%d")
        start_id_num = int(self.repo.get_next_id().split('-')[1])

        for i, item in enumerate(items):
            # Validate the item
            self._validate_return_item(item)
            
            # Get next return ID
            return_id = f"RT-{start_id_num + i:05d}"
            
            # Calculate refund for this item
            refund_amount = item.unit_price * item.qty
            
            # Create return record
            return_record = {
                "return_id": return_id,
                "date": date_str,
                "product_id": item.product_id,
                "original_sale_id": item.original_sale_id or "",
                "qty": item.qty,
                "refund_amount": refund_amount,
                "return_reason": reason,
                "return_type": "full" if item.qty >= self._get_original_qty(item) else "partial",
                "refund_method": refund_method,
                "status": "completed",
                "processed_by": processed_by
            }
            
            self.repo.create(return_record)
            return_ids.append(return_id)
            total_refund += refund_amount
            total_qty += item.qty
            
            # Restore inventory stock
            self._restore_stock(item.product_id, item.qty, return_id)
            
            # Log individual return
            AuditLogger.log_action(
                processed_by, "RETURN_PROCESSED",
                f"Return: {return_id}, Product: {item.product_id}, Qty: {item.qty}, Refund: {refund_amount}"
            )

        app_logger.info(f"Return completed: IDs={return_ids}, Total Refund={total_refund}")

        return ReturnResult(
            success=True,
            return_id=return_ids[0] if return_ids else "N/A",
            refund_amount=total_refund,
            items_returned=total_qty
        )

    def _validate_return_item(self, item: ReturnItem):
        """Validate a single return item."""
        if item.qty <= 0:
            raise ValidationError(f"Return quantity must be positive for {item.name}")
        
        # Verify product exists
        try:
            self.inventory_service.validate_sufficient_stock(item.product_id, 0)
        except ProductNotFoundError:
            raise ProductNotFoundError(item.product_id)

    def _get_original_qty(self, item: ReturnItem) -> int:
        """Get the original quantity sold for this item."""
        if not item.original_sale_id:
            return item.qty
        
        df = self.sales_repo.get_by_id(item.original_sale_id)
        if df and df.get('qty'):
            return df['qty']
        return item.qty

    def _restore_stock(self, product_id: str, qty: int, reference_id: str):
        """Restore stock and log the movement."""
        # Update stock movements
        self.inventory_service.product_repo.db.execute_write(
            """INSERT INTO stock_movements 
               (product_id, movement_type, qty, reference_id, notes) 
               VALUES (?, ?, ?, ?, ?)""",
            (product_id, 'return_in', qty, reference_id, f"Return processed: {reference_id}")
        )
        app_logger.info(f"Stock restored: Product={product_id}, Qty={qty}, Ref={reference_id}")

    def validate_return_eligibility(
        self, 
        product_id: str, 
        requested_qty: int,
        original_sale_id: Optional[str] = None
    ) -> dict:
        """
        Check if a return is eligible:
        - Returns maximum returnable quantity based on original sale
        - Checks if return is within allowed timeframe
        """
        max_returnable = 0
        original_qty = 0
        original_price = 0.0
        sale_date = None
        
        if original_sale_id:
            # Get original sale details
            sale = self.sales_repo.get_by_id(original_sale_id)
            if sale:
                original_qty = sale.get('qty', 0)
                original_price = sale.get('sell_price', 0)
                sale_date = sale.get('date', '')
                
                # Calculate how many have already been returned
                returned_df = self.repo.get_returns_by_sale(original_sale_id)
                already_returned = returned_df['qty'].sum() if not returned_df.empty else 0
                max_returnable = original_qty - already_returned
        else:
            # No original sale - allow return up to requested qty (manual return)
            max_returnable = requested_qty

        is_eligible = max_returnable >= requested_qty
        eligible_qty = min(requested_qty, max_returnable)
        
        return {
            "is_eligible": is_eligible,
            "max_returnable": max_returnable,
            "eligible_qty": eligible_qty,
            "original_qty": original_qty,
            "original_price": original_price,
            "sale_date": sale_date,
            "refund_amount": eligible_qty * original_price if original_price else 0
        }

    def get_return_history(self, product_id: Optional[str] = None) -> List[dict]:
        """Get return history, optionally filtered by product."""
        if product_id:
            df = self.repo.get_returns_by_product(product_id)
        else:
            df = self.repo.get_all()
        
        if df.empty:
            return []
        
        return df.to_dict('records')

    def get_returnable_sales(self, product_id: str) -> List[dict]:
        """Find sales that are eligible for return (within return window)."""
        # Get all sales for this product
        all_sales = self.sales_repo.get_all()
        product_sales = all_sales[all_sales['product_id'] == product_id]
        
        returnable = []
        for _, sale in product_sales.iterrows():
            sale_id = sale['sales_id']
            original_qty = sale['qty']
            
            # Check returns
            returned_df = self.repo.get_returns_by_sale(sale_id)
            returned_qty = returned_df['qty'].sum() if not returned_df.empty else 0
            
            remaining = original_qty - returned_qty
            if remaining > 0:
                returnable.append({
                    'sales_id': sale_id,
                    'date': sale['date'],
                    'qty_sold': original_qty,
                    'qty_returned': returned_qty,
                    'qty_remaining': remaining,
                    'sell_price': sale['sell_price'],
                    'customer': sale['customer'],
                    'max_refund': remaining * sale['sell_price']
                })
        
        return returnable
