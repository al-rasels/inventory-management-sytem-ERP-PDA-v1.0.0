# 🎓 Developer Deep Dive: The Anatomy of SunERP Professional

This document is for a Python enthusiast who wants to understand how a production-grade desktop application is built from the ground up. Every layer, library, function, and design decision is explained.

---

## 📁 1. Project Structure — Why Each File Exists

```
src/
├── main.py                    ← "The Front Door" — launches LoginScreen
├── test_system.py             ← Automated test suite (18 tests)
├── core/                      ← "The Brain" — all business logic
│   ├── config.py              ← Global settings, colors, paths, rules
│   ├── database.py            ← DatabaseEngine class — talks to Excel + SQLite
│   ├── inventory_manager.py   ← FIFO math, stock checks, dead stock detection
│   ├── auth.py                ← AuthManager — SHA-256 login + user CRUD
│   └── safety.py              ← BackupManager, AuditLogger, CloudBackup stub
├── ui/                        ← "The Face" — all visual components
│   ├── app.py                 ← ERPApp — main window, sidebar, view switching
│   └── views/                 ← One file per screen
│       ├── dashboard.py       ← KPI cards + chart + alerts (real data)
│       ├── products.py        ← Searchable table with stock indicators
│       ├── sales.py           ← Full POS: cart, discount, stock check, PDF
│       ├── purchases.py       ← Product dropdown, supplier, live preview
│       ├── inventory.py       ← Ledger with filters + stock value calculation
│       ├── analytics.py       ← 4-tab business intelligence
│       └── settings.py        ← 3-tab: General, Users, Database management
└── utils/
    └── pdf_gen.py             ← ReportLab invoice builder
```

**The Rule**: Each file has ONE responsibility. If you need to change how invoices look, you only touch `pdf_gen.py`. If you need to change how stock is calculated, you only touch `inventory_manager.py`. This is called the **Single Responsibility Principle**.

---

## 📚 2. The Libraries — What They Do and Why

### `customtkinter` — The Modern UI Toolkit
**What**: A wrapper around Python's built-in `tkinter` that adds rounded corners, dark mode, and modern widgets.
**Why not raw tkinter?** Raw tkinter looks like a 1990s Windows app. CustomTkinter looks professional.
**Key classes used**:
- `CTkFrame` → Container (like a `<div>` in HTML)
- `CTkLabel` → Text display
- `CTkEntry` → Text input field
- `CTkButton` → Clickable button
- `CTkScrollableFrame` → A scrollable container for long lists
- `CTkTabview` → Tabbed interface (used in Analytics and Settings)
- `CTkComboBox` → Dropdown selector
- `CTkSwitch` → Toggle switch

### `sqlite3` — The Built-in Database
**What**: Python has a database engine built right in! No installation needed.
**Why**: It lets us search 50,000+ records in under 1ms using SQL indexes.
**Key functions**:
```python
conn = sqlite3.connect("data/erp_cache.db")  # Open/create database
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS ...")  # Create tables
cursor.execute("INSERT INTO sales VALUES (?, ?)", (val1, val2))  # Parameterized query (safe!)
conn.commit()   # Save changes
conn.close()    # Release the file
```

### `pandas` — The Data Transfer Tool
**What**: A library for handling tabular data (like Excel, but in Python).
**Why**: It can read an entire Excel sheet into memory and write it into SQLite in one line:
```python
df = pd.read_excel("file.xlsx", sheet_name="Products", skiprows=3)
df.to_sql("products", conn, if_exists="replace", index=False)
```
**Key concept**: A `DataFrame` is a table. `df.iloc[0]` is the first row. `df['name']` is a column.

### `openpyxl` — The Excel Surgery Tool
**What**: Reads and writes `.xlsx` files cell by cell.
**Why pandas can't do this**: Pandas overwrites the entire sheet. `openpyxl` lets us APPEND a single row while keeping all existing formulas intact.
```python
wb = openpyxl.load_workbook("file.xlsx")
ws = wb["Sales_Log"]
ws.cell(row=10, column=3).value = "P001"       # Write a value
ws.cell(row=10, column=7).value = '=E10*F10'   # Write a formula!
wb.save("file.xlsx")
```

### `ReportLab` — The PDF Builder
**What**: Draws PDF documents programmatically.
**Key classes**: `SimpleDocTemplate`, `Table`, `Paragraph`, `Spacer`.
**Flow**: Create a list of "elements" (paragraphs, tables, etc.) → call `doc.build(elements)`.

### `matplotlib` — The Chart Engine
**What**: Creates professional charts.
**Integration trick**: We embed it inside CustomTkinter using `FigureCanvasTkAgg`:
```python
fig, ax = plt.subplots()
ax.plot(x, y)
canvas = FigureCanvasTkAgg(fig, master=some_frame)
canvas.draw()
canvas.get_tk_widget().pack()
```

### `hashlib` — The Password Scrambler
**What**: Built-in Python library for creating hash digests.
**How we use it**:
```python
import hashlib
password = "admin123"
hashed = hashlib.sha256(password.encode()).hexdigest()
# Result: "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
```
We store this 64-character string. Nobody can reverse it back to "admin123".

---

## 🧠 3. Core Logic Deep-Dive

### A. The FIFO Algorithm (`inventory_manager.py`)

**Problem**: When you sell 10 bags of flour, what was the exact cost of those 10 bags?

**Why not Average Cost?** If you bought:
- Batch 1: 100 bags at ৳150 each (January)
- Batch 2: 100 bags at ৳180 each (March)

Average cost says each bag costs ৳165. But FIFO says the first 100 bags you sell cost ৳150 (the oldest batch), and only after those are gone do you start costing at ৳180.

**The Algorithm**:
```python
# Step 1: Get all purchase batches, sorted by date (oldest first)
batches = [Batch1(qty=100, cost=150), Batch2(qty=100, cost=180)]

# Step 2: How many units were already sold in the past?
previously_sold = 90  # From the sales table

# Step 3: "Skip" through batches until we've skipped past sold units
#   Batch1 has 100, we skip 90 → 10 remain in Batch1

# Step 4: Start "consuming" for this sale (selling 15 units)
#   Take 10 from Batch1 at ৳150 = ৳1,500
#   Take 5 from Batch2 at ৳180  = ৳900
#   Total COGS = ৳2,400
```

**Fallback**: If batches are exhausted (more sold than purchased in data), we use the product's `cost_price` from the master table.

### B. The Excel Sync Engine (`database.py`)

**The Challenge**: Excel stores IDs and totals as **formulas** (e.g., `=IF(B5="","","SL-"&TEXT(1,"00000"))`). When Python reads this with `pandas`, the formulas come as `NaN` (Not a Number).

**Our Solution**:
```python
# 1. Cast the column to 'object' (string type) first
df['purchase_id'] = df['purchase_id'].astype(object)

# 2. Generate IDs for NaN rows
for i, row in df.iterrows():
    if pd.isna(row['purchase_id']):
        df.at[i, 'purchase_id'] = f"PUR-{i+1:04d}"
```

**Why `dropna(subset=['date'])` instead of `dropna(subset=['purchase_id'])`?**
Because `date` is always a real value (typed by the user), while `purchase_id` is a formula that evaluates to NaN in Python.

### C. View Switching (`app.py`)

```python
def show_sales(self):
    self.clear_content()                          # Step 1: Destroy old view
    self.set_active_nav("Sales")                  # Step 2: Highlight sidebar button
    self.current_view = SalesView(self.content_frame, self.db)  # Step 3: Create new view
    self.current_view.pack(fill="both", expand=True)            # Step 4: Display it
```

**Why destroy and recreate?** Memory efficiency. Only one view exists at a time. If we kept all 7 views alive, each with database queries and matplotlib charts, the app would consume excessive RAM.

### D. Stock Validation Before Sale (`sales.py`)

```python
# Before adding to cart:
available, current = self.im.check_stock_available(product_id, qty_needed)
if not available:
    messagebox.showwarning("Out of Stock", f"Only {current} units left!")
    return
```

This prevents negative stock — a critical business rule that many simple systems miss.

---

## 🔐 4. Security Deep-Dive

### Password Flow
```
User types "admin123"
    → hashlib.sha256("admin123".encode()).hexdigest()
    → "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
    → Compare with stored hash in `users` table
    → Match? → Return user dict. No match? → Return None.
```

### SQL Injection Prevention
**BAD** (what we FIXED):
```python
query = f"SELECT * FROM products WHERE product_id = '{user_input}'"
# If user_input = "'; DROP TABLE products; --" → disaster!
```

**GOOD** (what we use everywhere):
```python
query = "SELECT * FROM products WHERE product_id = ?"
db.execute_query(query, params=(user_input,))
# The ? placeholder is automatically escaped by sqlite3
```

---

## 🔧 5. The Config System (`config.py`)

All "magic values" live in one file:
```python
# Colors — change these to restyle the entire app instantly
COLORS = {
    "accent": "#3B82F6",       # Blue buttons and highlights
    "success": "#10B981",      # Green for positive actions
    "danger": "#EF4444",       # Red for warnings
    "card_dark": "#1E293B",    # Card background
    ...
}

# Business rules — adjust without touching code
LOW_STOCK_THRESHOLD = 50
MAX_BACKUP_FILES = 50
DEFAULT_CURRENCY = "৳"
```

**Why this matters**: If a client says "change the theme to purple", you edit ONE line. If they say "alert me when stock drops below 100", you change ONE number.

---

## 🚀 6. Running & Building

### Development Mode
```powershell
$env:PYTHONPATH = "."
python src/main.py
```

### Run Tests
```powershell
$env:PYTHONPATH = "."
python src/test_system.py
```

### Build Production EXE
```powershell
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed ^
    --add-data "src;src/" ^
    --add-data "SunWarehouse_ERP_v3.xlsx;." ^
    src/main.py
```

**Flags explained**:
- `--onedir` → Creates a folder with EXE + dependencies (faster startup than `--onefile`)
- `--windowed` → No black terminal window
- `--add-data "src;src/"` → Include Python source files in the bundle
- `--add-data "SunWarehouse_ERP_v3.xlsx;."` → Include the database

---

## 🧪 7. Testing Strategy

The test suite (`test_system.py`) covers 18 automated checks across 6 phases:

| Phase | Tests | What's Verified |
|:--|:--|:--|
| Database Engine | 3 | Excel → SQLite sync for all 3 tables |
| ID Generation | 2 | Sequential, unique IDs (SL-00001, PUR-0001) |
| Inventory Manager | 6 | Stock math, FIFO, availability, low/dead stock |
| Authentication | 3 | Valid login, invalid login, role assignment |
| Safety System | 1 | Backup file creation |
| Audit Logging | 1 | Database audit entry |

Run anytime after code changes to catch regressions.

---

## 🎯 8. Learning Exercises

1. **Change a Color**: Edit `COLORS["accent"]` in `config.py` to `"#8B5CF6"` (purple). Restart. Watch the entire app transform.

2. **Add a Field**: Add "Customer Phone" to the Sales flow:
   - Add a `CTkEntry` in `sales.py`
   - Add `phone TEXT` column in `database.py` schema
   - Pass it through `write_sale()`
   - Add it to `pdf_gen.py` invoice output

3. **New Report**: Create a "Monthly Sales Report" in `analytics.py`:
   ```python
   df = self.db.execute_query(
       "SELECT strftime('%Y-%m', date) as month, SUM(revenue) as rev FROM sales GROUP BY month"
   )
   ```

4. **Switch to LIFO**: In `inventory_manager.py`, change `ORDER BY date ASC` to `ORDER BY date DESC`. Now the newest batch is consumed first.

---

## 🏁 9. Summary

This ERP system demonstrates:
- **Layered Architecture** — UI, Logic, and Data are cleanly separated
- **Dual-Persistence** — SQLite for speed, Excel for portability
- **FIFO Accounting** — Professional-grade cost tracking
- **Defensive Programming** — Backups before writes, parameterized queries, input validation

You built a tool that businesses pay thousands of dollars for. Now you understand every line of it. Happy coding! 🐍
