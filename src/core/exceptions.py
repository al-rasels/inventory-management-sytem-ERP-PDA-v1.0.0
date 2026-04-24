"""
Custom exception hierarchy for SunERP Professional.
"""

class SunERPException(Exception):
    """Base for all domain exceptions."""
    pass

# Validation errors
class ValidationError(SunERPException):
    """Raised when input validation fails."""
    pass

class DuplicateError(ValidationError):
    """Raised when a unique constraint is violated."""
    def __init__(self, entity_type: str, field: str, value: str):
        self.entity_type = entity_type
        self.field = field
        self.value = value
        super().__init__(f"Duplicate {field} in {entity_type}: {value}")

class InvalidInputError(ValidationError):
    """Raised when input is malformed or invalid."""
    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"Invalid {field}: {reason}")

# Business rule errors
class BusinessLogicError(SunERPException):
    """Raised when a business rule is violated."""
    pass

class InsufficientStockError(BusinessLogicError):
    """Raised when an operation requires more stock than available."""
    def __init__(self, product_id: str, required: int, available: int):
        self.product_id = product_id
        self.required = required
        self.available = available
        super().__init__(f"Insufficient stock for {product_id}: need {required}, have {available}")

class ProductNotFoundError(BusinessLogicError):
    """Raised when a product cannot be found."""
    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Product not found: {product_id}")

class UserNotFoundError(BusinessLogicError):
    """Raised when a user cannot be found."""
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"User not found: {username}")

class AuthenticationError(BusinessLogicError):
    """Raised when login fails."""
    pass

class MaxDiscountError(BusinessLogicError):
    """Raised when discount exceeds the allowed maximum."""
    def __init__(self, discount: float, max_allowed: float = 100.0):
        self.discount = discount
        self.max_allowed = max_allowed
        super().__init__(f"Discount {discount}% exceeds maximum allowed {max_allowed}%")
