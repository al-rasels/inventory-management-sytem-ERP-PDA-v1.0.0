# 🏗️ System Design Specification: SunERP Professional v3.0

This document outlines the complete technical architecture, data structures, design patterns, and system workflows.

---

## 1. High-Level Architecture

The system follows a **Layered Architecture** with a **Write-Through Cache** pattern.

```
┌─────────────────────────────────────────────────────────────┐
│                     UI LAYER (CustomTkinter)                │
│  LoginScreen → ERPApp → [Dashboard│Sales│Products│...]      │
├─────────────────────────────────────────────────────────────┤
│                   BUSINESS LOGIC LAYER                      │
│  InventoryManager (FIFO) │ AuthManager │ SafetyManager      │
├─────────────────────────────────────────────────────────────┤
│                     DATA ACCESS LAYER                       │
│           DatabaseEngine (Repository Pattern)               │
│     ┌──────────────┐         ┌──────────────────┐          │
│     │  SQLite Cache │◄───────►│  Excel Primary DB │          │
│     │  (Fast Reads) │  sync   │  (Source of Truth)│          │
│     └──────────────┘         └──────────────────┘          │
├─────────────────────────────────────────────────────────────┤
│                     UTILITY LAYER                           │
│         InvoiceGenerator (PDF) │ AuditLogger                │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Direction
- **READ**: UI → DatabaseEngine → SQLite (millisecond responses)
- **WRITE**: UI → Validation → Backup → SQLite → Excel → PDF → Audit Log

---

## 2. Project Structure

```
Inventory_management_sytem/
├── SunWarehouse_ERP_v3.xlsx    # Primary Excel database
├── src/
│   ├── main.py                 # Entry point (Login Screen)
│   ├── test_system.py          # Automated test suite (18 tests)
│   ├── core/
│   │   ├── config.py           # Colors, paths, business rules, shortcuts
│   │   ├── database.py         # DatabaseEngine (sync, read, write)
│   │   ├── inventory_manager.py# FIFO, stock checks, dead stock, low stock
│   │   ├── auth.py             # SHA-256 login + RBAC user management
│   │   └── safety.py           # Backup, rollback, audit, cloud placeholder
│   ├── ui/
│   │   ├── app.py              # Main window, sidebar nav, view switching
│   │   └── views/
│   │       ├── dashboard.py    # KPI cards, sales chart, alerts
│   │       ├── products.py     # Search + category filter, stock indicators
│   │       ├── sales.py        # POS: cart, discount, stock validation, PDF
│   │       ├── purchases.py    # Product dropdown, supplier, live preview
│   │       ├── inventory.py    # Ledger with filters, value calculations
│   │       ├── analytics.py    # Tabs: Overview, Top Products, Dead Stock
│   │       └── settings.py     # Tabs: General, Users, Database management
│   └── utils/
│       └── pdf_gen.py          # ReportLab invoice generation
├── data/
│   └── erp_cache.db            # SQLite performance cache
├── backups/                    # Timestamped Excel backups
├── invoices/                   # Generated PDF invoices
├── logs/
│   └── system.log              # Application event log
├── USER_GUIDE.md               # End-user documentation
├── DEVELOPER_DEEP_DIVE.md      # Learning-focused code walkthrough
└── SYSTEM_DESIGN.md            # This file
```

---

## 3. Data Schema

### SQLite Tables (`data/erp_cache.db`)

**`products`**
| Column | Type | Description |
|:--|:--|:--|
| product_id | TEXT PK | Unique ID (e.g. P001) |
| sku_code | TEXT | Barcode/SKU |
| name | TEXT | Display name |
| category | TEXT | Product category |
| unit | TEXT | Unit of measure |
| status | TEXT | Active/Inactive |
| sell_price | REAL | Customer-facing price |
| cost_price | REAL | Master cost (fallback for FIFO) |
| reorder_qty | INTEGER | Threshold for low-stock alerts |

**`purchases`**
| Column | Type | Description |
|:--|:--|:--|
| purchase_id | TEXT PK | Sequential (PUR-0001) |
| date | TEXT | ISO date string |
| product_id | TEXT FK | Links to products |
| batch_id | TEXT | Unique batch identifier for FIFO |
| supplier | TEXT | Vendor name |
| qty | INTEGER | Units received |
| cost_per_unit | REAL | Per-unit landed cost |
| total_cost | REAL | qty × cost_per_unit |

**`sales`**
| Column | Type | Description |
|:--|:--|:--|
| sales_id | TEXT PK | Sequential (SL-00001) |
| date | TEXT | ISO date string |
| product_id | TEXT FK | Links to products |
| customer | TEXT | Customer name (default: Walk-in) |
| qty | INTEGER | Units sold |
| sell_price | REAL | Price charged per unit |
| discount | REAL | Discount amount applied |
| revenue | REAL | Net revenue after discount |
| cogs | REAL | FIFO-calculated cost of goods |
| profit | REAL | revenue − cogs |

**`users`** — Stores SHA-256 hashed passwords with role assignments.

**`audit_logs`** — Auto-timestamped log of all system actions.

### Performance Indexes
```sql
CREATE INDEX idx_sales_date ON sales(date);
CREATE INDEX idx_sales_product ON sales(product_id);
CREATE INDEX idx_purchases_product ON purchases(product_id);
CREATE INDEX idx_purchases_date ON purchases(date);
```
These indexes ensure sub-millisecond lookups even at 50,000+ records.

### Excel Sheet Mapping
| Sheet | Purpose | Sync Direction |
|:--|:--|:--|
| `Product_Master` | SKU catalog | Excel → SQLite |
| `Purchase_Log` | Stock-in records | Bidirectional |
| `Sales_Log` | Transaction records | Bidirectional |

---

## 4. Transaction Flow ("The Safety Dance")

Every write follows this exact sequence to guarantee data integrity:

```
User clicks "Complete Sale"
    │
    ▼
[1] VALIDATE ── InventoryManager.check_stock_available()
    │             Returns (bool, current_stock)
    ▼
[2] CALCULATE ── InventoryManager.calculate_fifo_cogs()
    │             Walks oldest batches to compute exact cost
    ▼
[3] BACKUP ──── SafetyManager.create_backup()
    │             Copies Excel to backups/backup_ERP_YYYYMMDD_HHMMSS.xlsx
    ▼
[4] CACHE ───── DatabaseEngine.execute_write() → SQLite
    │             Instant UI update
    ▼
[5] PERSIST ─── openpyxl.load_workbook() → Excel
    │             Appends row with formulas intact
    ▼
[6] INVOICE ─── InvoiceGenerator.generate() → PDF
    │             Saved to invoices/ folder
    ▼
[7] AUDIT ───── DatabaseEngine.log_audit()
    │             Recorded in audit_logs table
    ▼
[8] CONFIRM ─── messagebox.showinfo() → User
```

---

## 5. Design Patterns

| Pattern | Where | Purpose |
|:--|:--|:--|
| **Repository** | `DatabaseEngine` | Abstracts data access. UI never touches Excel directly. Swap to PostgreSQL by changing one file. |
| **View Manager** | `ERPApp.show_*()` | Each screen is a self-contained `CTkFrame` class. One active at a time. |
| **Singleton-like** | `DatabaseEngine`, `AuthManager` | Initialized once in `main.py`, passed by reference to all views. |
| **Write-Through Cache** | `write_sale()`, `write_purchase()` | Every write hits both SQLite (speed) and Excel (persistence). |
| **Strategy** | `InventoryManager.calculate_fifo_cogs()` | FIFO algorithm can be swapped for LIFO or Weighted Average. |

---

## 6. Security Model

| Layer | Mechanism |
|:--|:--|
| **Authentication** | SHA-256 password hashing (never stored in plaintext) |
| **Authorization** | Role-based: Admin, Manager, Cashier |
| **Data Safety** | Auto-backup before every write operation |
| **Audit Trail** | Every action logged with user, timestamp, and details |
| **Input Validation** | Parameterized SQL queries (no SQL injection) |
| **Backup Rotation** | Configurable MAX_BACKUP_FILES with cleanup utility |

---

## 7. Scalability Roadmap

### Current Capacity
- **50,000+ records**: SQLite with indexed columns handles this with ease.
- **50 daily transactions**: Well within single-file SQLite's capabilities.

### Cloud Migration Path
To evolve from single-user desktop to multi-user cloud:

1. **Replace `sqlite3`** with `SQLAlchemy` or `psycopg2` in `database.py`.
2. **Connect to PostgreSQL/MySQL** on a cloud server.
3. **Remove `openpyxl` writes** (Excel becomes an export-only feature).
4. **UI code stays 100% unchanged** thanks to the Repository Pattern.

### Optional Enhancements
- `CloudBackup` class in `safety.py` is ready for Google Drive / AWS S3 integration.
- Barcode scanner: The `<Return>` binding on the search bar already supports HID scanners.
- Multi-language: All display strings can be moved to a `locale.py` config file.

---

## 8. Keyboard Shortcuts

| Key | Action |
|:--|:--|
| `F2` | Open Sales POS |
| `F3` | Open Purchases |
| `F5` | Return to Dashboard |
| `Enter` | Add item to cart (in Sales) |
| `Ctrl+F` | Focus search bar |
