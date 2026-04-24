from datetime import datetime
from typing import List
from src.core.exceptions import ValidationError, MaxDiscountError, InsufficientStockError
from src.services.types import CartItem, SaleResult
from src.core.safety import SafetyManager, AuditLogger
from src.utils.validators import Validator
from src.utils.logger import app_logger

class SalesService:
    """Orchestrates sales workflows with full safety guarantees."""
    
    def __init__(self, sales_repo, inventory_service, pdf_service):
        self.repo = sales_repo
        self.inventory_service = inventory_service
        self.pdf_service = pdf_service
    
    @SafetyManager.transactional
    def complete_sale(self, cart_items: List[CartItem], customer: str, 
                      discount_percent: float) -> SaleResult:
        """
        Complete a sale transaction atomically.
        """
        # 1. Validation
        Validator.validate_sale_input(len(cart_items), discount_percent)
        self._validate_sale_items(cart_items, discount_percent)
        
        app_logger.info(f"Processing sale for customer: {customer}")
        
        sale_ids = []
        total_revenue = 0.0
        total_profit = 0.0
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # 2. Get next base ID for this transaction set
        # Note: In a high-concurrency system we'd use a real sequence, 
        # but for this SQLite/Excel setup, we generate based on current count.
        start_id_num = int(self.repo.get_next_id().split('-')[1])
        
        for i, item in enumerate(cart_items):
            # 3. Stock check & FIFO calculation
            self.inventory_service.validate_sufficient_stock(item.product_id, item.qty)
            cogs = self.inventory_service.calculate_item_cost(item.product_id, item.qty)
            
            # 4. Prepare sale record
            sale_id = f"SL-{start_id_num + i:05d}"
            item_discount_pct = discount_percent
            item_discount_val = item.total * (item_discount_pct / 100)
            revenue = item.total - item_discount_val
            profit = revenue - cogs
            
            sale_record = {
                "sales_id": sale_id,
                "product_id": item.product_id,
                "qty": item.qty,
                "sell_price": item.price,
                "discount": item_discount_val,
                "revenue": revenue,
                "cogs": cogs,
                "profit": profit,
                "date": date_str,
                "customer": customer
            }
            
            self.repo.create(sale_record)
            sale_ids.append(sale_id)
            total_revenue += revenue
            total_profit += profit

        # 6. Generate PDF Invoice
        subtotal = sum(item.total for item in cart_items)
        discount_amount = subtotal * (discount_percent / 100)
        grand_total = subtotal - discount_amount
        
        invoice_data = {
            "invoice_id": sale_ids[0] if sale_ids else "N/A",
            "date": date_str,
            "customer": customer,
            "items": [{"name": item.name, "qty": item.qty, "price": item.price, "total": item.total} for item in cart_items],
            "subtotal": subtotal,
            "discount": discount_amount,
            "grand_total": grand_total
        }
        self.pdf_service.generate_invoice(invoice_data)

        # 7. Audit Log
        AuditLogger.log_action("SYSTEM", "SALE_COMPLETE", f"Customer: {customer}, Items: {len(cart_items)}, Revenue: {total_revenue}")
        
        return SaleResult(
            success=True,
            sale_ids=sale_ids,
            revenue=total_revenue,
            profit=total_profit
        )
            
    def _validate_sale_items(self, items: List[CartItem], discount_percent: float):
        if not items:
            raise ValidationError("Cart is empty")
        if discount_percent < 0 or discount_percent > 100:
            raise MaxDiscountError(discount_percent)
        for item in items:
            if item.qty <= 0:
                raise ValidationError(f"Invalid quantity for {item.name}")
            if item.price <= 0:
                raise ValidationError(f"Invalid price for {item.name}")
