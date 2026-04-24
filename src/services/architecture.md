# Service Layer Architecture

This document describes the design of the service layer for SunERP Professional.

## Overview
The service layer encapsulates the business logic and orchestrates workflows between the UI (Views) and the data access layer (Repositories).

## Services

### 1. SalesService
- **Responsibility:** Orchestrates sales workflows, including validation, FIFO cost calculation, persistence, and post-processing (PDF, Audit).
- **Depends on:** `DatabaseEngine` (until Repositories are built), `InventoryService`, `BackupService`, `AuditService`, `PDFService`.
- **Public Methods:**
  - `complete_sale(cart_items: List[CartItem], customer: str, discount_percent: float) -> SaleResult`
- **Error Types:** `ValidationError`, `InsufficientStockError`, `MaxDiscountError`.

### 2. InventoryService
- **Responsibility:** Single source of truth for all inventory operations.
- **Depends on:** `DatabaseEngine`.
- **Public Methods:**
  - `get_current_stock(product_id: str) -> StockInfo`
  - `validate_sufficient_stock(product_id: str, qty_needed: int) -> bool`
  - `calculate_item_cost(product_id: str, qty: int) -> float`
  - `get_low_stock_items(limit: int = 10) -> List[LowStockAlert]`
  - `get_dead_stock(days: int = None) -> List[DeadStockItem]`
  - `get_stock_value(product_id: str = None) -> float`
- **Error Types:** `ProductNotFoundError`, `InsufficientStockError`.

### 3. ProductService
- **Responsibility:** Manages product catalog with full validation.
- **Depends on:** `DatabaseEngine`, `AuditService`.
- **Public Methods:**
  - `create_product(data: CreateProductInput) -> Product`
  - `update_product(product_id: str, data: UpdateProductInput) -> Product`
  - `get_product(product_id: str) -> Product`
  - `search_products(query: str, category: str = None) -> List[Product]`
- **Error Types:** `DuplicateError`, `InvalidInputError`, `ProductNotFoundError`.

### 4. AuthService
- **Responsibility:** User authentication and authorization.
- **Depends on:** `DatabaseEngine`.
- **Public Methods:**
  - `login(username: str, password: str) -> AuthResult`
  - `create_user(username: str, full_name: str, password: str, role: str) -> User`
  - `change_password(username: str, old_password: str, new_password: str) -> bool`
- **Error Types:** `AuthenticationError`, `DuplicateError`, `ValidationError`.

### 5. PurchaseService
- **Responsibility:** Orchestrates purchase workflows.
- **Depends on:** `DatabaseEngine`, `ProductService`, `BackupService`, `AuditService`.
- **Public Methods:**
  - `record_purchase(product_id: str, qty: int, cost_per_unit: float, supplier: str = "") -> PurchaseResult`
- **Error Types:** `ProductNotFoundError`, `InvalidInputError`.

### 6. ReportService (Placeholder)
- **Responsibility:** Generates business reports and analytics.
- **Depends on:** All other services.

## Error Handling Strategy
- Services should raise typed exceptions defined in `src/core/exceptions.py`.
- Views are responsible for catching these exceptions and displaying appropriate messages to the user.

## Safety Strategy
- Critical write operations must follow the "Backup -> Write -> Rollback on Fail" pattern.
- Services should use `BackupService` for this purpose.
