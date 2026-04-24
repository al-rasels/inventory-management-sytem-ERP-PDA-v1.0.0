from typing import List, Optional, Dict, Any
from src.core.exceptions import DuplicateError, InvalidInputError, ProductNotFoundError
from src.core.safety import SafetyManager, AuditLogger
from src.utils.validators import Validator
from src.utils.logger import app_logger

class ProductService:
    """Manages product catalog with full validation."""
    
    def __init__(self, product_repo):
        self.repo = product_repo
        
    @SafetyManager.transactional
    def create_product(self, data: Dict[str, Any]):
        """Create a new product with validation and transaction safety."""
        Validator.validate_product_data(data)
        self._validate_business_rules(data)
        
        app_logger.info(f"Creating product: {data.get('name')} (SKU: {data.get('sku_code')})")
        
        # Check for duplicate SKU
        if self._sku_exists(data['sku_code']):
            raise DuplicateError("Product", "sku_code", data['sku_code'])
            
        # Generate Product ID if not provided
        if not data.get('product_id'):
            all_products = self.repo.get_all()
            next_id = len(all_products) + 1
            data['product_id'] = f"P{next_id:04d}"
            
        self.repo.create(data)
        
        AuditLogger.log_action("SYSTEM", "PRODUCT_CREATE", f"ID: {data['product_id']}, SKU: {data['sku_code']}")
        return data

    @SafetyManager.transactional
    def update_product(self, product_id: str, data: Dict[str, Any]):
        """Update an existing product with validation and transaction safety."""
        Validator.validate_product_data(data)
        
        app_logger.info(f"Updating product: {product_id}")
        if not self.repo.get_by_id(product_id):
            raise ProductNotFoundError(product_id)
            
        if 'sku_code' in data:
            if self._sku_exists(data['sku_code'], exclude_id=product_id):
                raise DuplicateError("Product", "sku_code", data['sku_code'])
        
        self._validate_business_rules(data, partial=True)
        self.repo.update(product_id, data)
        
        AuditLogger.log_action("SYSTEM", "PRODUCT_UPDATE", f"ID: {product_id}")
        return True

    def get_product(self, product_id: str) -> Dict[str, Any]:
        """Fetch product by ID."""
        product = self.repo.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(product_id)
        return product

    def search_products(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search products by name or SKU."""
        all_prods = self.repo.get_all()
        # Basic filtering logic since we're using repo.get_all()
        # In a real app, repo would have a search method
        filtered = all_prods[
            all_prods['name'].str.contains(query, case=False, na=False) | 
            all_prods['sku_code'].str.contains(query, case=False, na=False)
        ]
        if category and category != "All Categories":
            filtered = filtered[filtered['category'] == category]
            
        return filtered.to_dict('records')

    def _validate_business_rules(self, data: Dict[str, Any], partial: bool = False):
        if not partial:
            required = ['sku_code', 'name', 'sell_price']
            for field in required:
                if field not in data or not data[field]:
                    raise InvalidInputError(field, "Field is required")
        
        if 'sell_price' in data and float(data['sell_price']) < 0:
            raise InvalidInputError("sell_price", "Cannot be negative")
            
        if 'cost_price' in data and data['cost_price'] and float(data['cost_price']) < 0:
            raise InvalidInputError("cost_price", "Cannot be negative")

    def _sku_exists(self, sku: str, exclude_id: Optional[str] = None) -> bool:
        # This is a bit inefficient with get_all, but keeping it simple for now
        all_prods = self.repo.get_all()
        if exclude_id:
            all_prods = all_prods[all_prods['product_id'] != exclude_id]
        return not all_prods[all_prods['sku_code'] == sku].empty
