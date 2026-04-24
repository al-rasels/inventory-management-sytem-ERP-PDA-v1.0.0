from datetime import datetime
from src.core.exceptions import ValidationError, ProductNotFoundError, InvalidInputError
from src.services.types import PurchaseResult
from src.core.safety import SafetyManager, AuditLogger
from src.utils.validators import Validator
from src.utils.logger import app_logger

class PurchaseService:
    """Orchestrates purchase workflows."""
    
    def __init__(self, purchase_repo, product_service):
        self.repo = purchase_repo
        self.product_service = product_service
        
    @SafetyManager.transactional
    def record_purchase(self, product_id: str, qty: int, cost_per_unit: float,
                        supplier: str = "") -> PurchaseResult:
        """Record stock entry (purchase) with transaction safety."""
        # 1. Validation
        Validator.validate_purchase_data(qty, cost_per_unit)
        self._validate_purchase_inputs(product_id, qty, cost_per_unit)
        
        app_logger.info(f"Processing purchase for product: {product_id} from: {supplier}")
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # ID generation logic
        purchase_id = self.repo.get_next_id()
        batch_id = self._generate_batch_id(product_id)
        total_cost = qty * cost_per_unit
        
        purchase_record = {
            "purchase_id": purchase_id,
            "batch_id": batch_id,
            "product_id": product_id,
            "qty": qty,
            "cost_per_unit": cost_per_unit,
            "total_cost": total_cost,
            "date": date_str,
            "supplier": supplier
        }
        
        # 3. Persist
        self.repo.create(purchase_record)
        
        # 4. Audit
        AuditLogger.log_action("SYSTEM", "PURCHASE_RECORD", f"Product: {product_id}, Total: {total_cost}")
        
        return PurchaseResult(
            success=True,
            purchase_id=purchase_id,
            batch_id=batch_id,
            total_cost=total_cost
        )

    def _validate_purchase_inputs(self, product_id, qty, cost):
        try:
            self.product_service.get_product(product_id)
        except ProductNotFoundError:
            raise ProductNotFoundError(product_id)
            
        if qty <= 0:
            raise InvalidInputError("qty", "Must be greater than 0")
        if cost < 0:
            raise InvalidInputError("cost_per_unit", "Cannot be negative")

    def _generate_batch_id(self, product_id: str) -> str:
        timestamp = datetime.now().strftime("%y%m%d%H%M")
        return f"B-{product_id}-{timestamp}"
