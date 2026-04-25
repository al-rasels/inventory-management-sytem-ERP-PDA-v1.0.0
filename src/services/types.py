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
    sale_ids: List[str] = field(default_factory=list)
    total_revenue: float = 0.0
    total_profit: float = 0.0
    errors: List[str] = field(default_factory=list)

@dataclass
class PurchaseResult:
    success: bool
    purchase_id: str = ""
    batch_id: str = ""
    total_cost: float = 0.0
    errors: List[str] = field(default_factory=list)

@dataclass
class AuthResult:
    success: bool
    user: Optional[dict] = None
    error_message: Optional[str] = None

@dataclass
class HeldSale:
    hold_id: str
    customer: str
    cart: List[CartItem]
    discount: float
    note: str
    created_at: str
