"""
Centralized validation logic for SunERP Professional.
"""
import re
from typing import Any, Dict, List
from src.core.exceptions import ValidationError

class Validator:
    @staticmethod
    def validate_product_data(data: Dict[str, Any]):
        """Validates product creation/update data."""
        if not data.get("sku_code"):
            raise ValidationError("SKU code is required")
        if not data.get("name"):
            raise ValidationError("Product name is required")
        if float(data.get("sell_price", 0)) < 0:
            raise ValidationError("Sell price cannot be negative")
        if float(data.get("cost_price", 0)) < 0:
            raise ValidationError("Cost price cannot be negative")

    @staticmethod
    def validate_purchase_data(qty: int, cost: float):
        """Validates purchase input."""
        if qty <= 0:
            raise ValidationError("Quantity must be greater than zero")
        if cost < 0:
            raise ValidationError("Cost cannot be negative")

    @staticmethod
    def validate_sale_input(qty: int, discount_pct: float):
        """Validates sale input."""
        if qty <= 0:
            raise ValidationError("Quantity must be greater than zero")
        if not (0 <= discount_pct <= 100):
            raise ValidationError("Discount must be between 0 and 100%")

    @staticmethod
    def validate_password_strength(password: str):
        """Ensures password meets minimum security standards."""
        if len(password) < 4:
            raise ValidationError("Password must be at least 4 characters long")
        # Add more complex rules if needed in future
