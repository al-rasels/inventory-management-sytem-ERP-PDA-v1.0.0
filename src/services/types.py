from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class CartItem:
    product_id: str
    name: str
    qty: int
    price: float
    total: float

@dataclass
class SaleResult:
    success: bool
    sale_ids: List[str]
    revenue: float
    profit: float
    errors: List[str] = field(default_factory=list)

@dataclass
class PurchaseResult:
    success: bool
    purchase_id: str
    batch_id: str
    total_cost: float
    errors: List[str] = field(default_factory=list)

@dataclass
class AuthResult:
    success: bool
    user: Optional[dict] = None
    error_message: Optional[str] = None
