# 📖 SunERP Professional v3.0 — User Guide

Welcome to your professional Desktop ERP system. This guide covers every feature.

---

## 🚀 1. Getting Started

### Installation
```powershell
pip install customtkinter openpyxl reportlab matplotlib pandas pillow
```

### Launch
```powershell
$env:PYTHONPATH = "."
python src/main.py
```

### Default Login
- **Username**: `admin`
- **Password**: `admin123`

---

## 🧭 2. Navigation

The **sidebar** on the left contains all modules. Click any item to switch screens.  
The currently active screen is highlighted in blue.

| Icon | Screen | Shortcut |
|:--|:--|:--|
| 📊 | Dashboard | F5 |
| 📦 | Products | — |
| 🧾 | Sales (POS) | F2 |
| 🚚 | Purchases | F3 |
| 📈 | Inventory | — |
| 🔍 | Analytics | — |
| ⚙️ | Settings | — |

Your **name and role** are shown at the bottom of the sidebar.  
Click **🚪 Logout** to return to the login screen.

---

## 📊 3. Dashboard

The dashboard shows **live data** from your database:

- **Total Revenue**: Sum of all sales revenue
- **Total Profit**: Revenue minus cost of goods (FIFO-calculated)
- **Active Products**: Number of products in your catalog
- **Low Stock Alerts**: Products below their reorder threshold (shown in red)

Below the KPIs:
- **Sales Trend Chart**: Shows revenue by day
- **Low Stock Panel**: Lists the most critical stock shortages
- **Recent Sales Panel**: Your latest 5 transactions

---

## 📦 4. Products

### Viewing Products
All products are displayed in a table with:
- **SKU** (highlighted in blue)
- **Product Name**
- **Category**
- **Stock** (color-coded: ✅ healthy, ⚠️ low, ⛔ out of stock)
- **Sell Price**
- **Status** (Active/Inactive)

### Searching
Type in the search bar to **instantly filter** by SKU, name, or category.

### Category Filter
Use the dropdown on the right to show only products from a specific category.

---

## 🧾 5. Sales (Point of Sale)

### Making a Sale
1. **Customer** (optional): Enter the customer's name in the top bar.
2. **Search**: Type a SKU, product name, or scan a barcode → press **Enter**.
3. **Cart**: Items appear with their price. Use **+/-** buttons to adjust quantity.
4. **Discount**: Enter a discount percentage in the summary panel.
5. **Complete**: Click **✅ COMPLETE SALE**.

### What Happens Automatically
- ✅ Stock is validated (you can't sell more than available)
- ✅ Profit is calculated using **FIFO** (exact cost from oldest batch)
- ✅ Data is saved to both SQLite and Excel
- ✅ A **backup** is created before writing
- ✅ A **PDF invoice** is generated in `invoices/`
- ✅ An **audit log** entry is recorded

### Cart Controls
- **+/−**: Increase or decrease quantity per item
- **✕**: Remove an item from the cart
- **🗑️ Clear Cart**: Remove all items

---

## 🚚 6. Purchases

### Recording a New Purchase
1. **Product**: Select from the dropdown (shows all products).
2. **Supplier**: Enter the vendor name.
3. **Quantity**: Number of units received.
4. **Cost / Unit**: Price paid per unit.
5. Click **💾 Save Purchase**.

### Live Preview
As you type quantity and cost, the **Total Cost** updates in real time.

### Purchase History
The right panel shows your **15 most recent purchases** with product name, date, quantity, and total cost.

---

## 📈 7. Inventory Ledger

### Summary Cards
At the top, see:
- **Total Units** in stock across all products
- **Stock Value** (units × cost price)
- **SKU Count** (number of distinct products)
- **Out of Stock** count

### Filtering
- **Stock Level**: All / Low Stock / Out of Stock / Healthy
- **Category**: Filter by product category

### Table Columns
- **Purchased**: Total units ever received
- **Sold**: Total units ever sold
- **Balance**: Current stock (color-coded with icons)
- **Value**: Stock value based on cost price

---

## 🔍 8. Analytics

Analytics is divided into **4 tabs**:

### 📊 Overview
- Financial summary: Revenue, COGS, Profit, Margin %, Avg Sale Value
- Reorder alerts with per-product unit counts

### 🏆 Top Products
- Top 3 shown with medals (🥇🥈🥉), revenue, and profit
- Remaining products listed below

### 💀 Dead Stock
- Products with no sales in the last 30 days
- Includes "last sale date" and promotion suggestions

### 📈 Profit Analysis
- Profit breakdown by category
- Color-coded margins: Green (>15%), Yellow (5-15%), Red (<5%)

---

## ⚙️ 9. Settings

Settings has **4 tabs**:

### ⚙️ General Tab
- **Dark Mode**: Toggle between dark and light themes
- **Auto-Backup**: Toggle automatic backups before writes
- **Audit Logging**: Toggle event logging
- **🔑 Change Password**: Enter current password + new password + confirmation
- **Backup Cleanup**: Remove old backups (keeps the 5 most recent)

### 👥 Users Tab
- **Create User**: Enter username, full name, password, and role (Admin/Manager/Cashier)
- **View Users**: See all registered users with their roles
- **Delete User**: Click ✕ next to a user to remove them (admin cannot be deleted)

### 🗄️ Database Tab
- **Stats**: View total count of products, sales, and purchases
- **Re-sync from Excel**: Rebuild the SQLite cache from the Excel file
- **Reset SQLite Cache**: Delete and rebuild the entire cache (use if Excel was manually edited)

### 📦 Export / Import Tab

#### Exporting Data
| Export Type | What It Does |
|:--|:--|
| **🚚 Full Migration ZIP** | Creates a complete archive (Excel + SQLite + Invoices + Backups) for moving to a new computer |
| **📊 Excel Report** | Multi-sheet `.xlsx` file with Products, Sales, Purchases, and Inventory Summary |
| **📋 CSV Export** | Export any individual table (Products / Sales / Purchases / Inventory) to CSV |

All exports are saved to the `exports/` folder in your project directory.

#### Importing Data
| Import Type | What It Does |
|:--|:--|
| **🚚 Restore from ZIP** | Replaces all current data with the contents of a migration archive. Creates a backup first. |
| **📋 Import CSV** | Appends rows from a CSV file into Products, Sales, or Purchases |

---

## 🚚 10. Migrating to a New Computer

1. On the **old computer**: Go to Settings → Export / Import → **Export ZIP**
2. Copy the ZIP file to the new computer (USB, cloud, email)
3. Install the software on the new computer (see Getting Started)
4. Launch the app and log in
5. Go to Settings → Export / Import → **Import ZIP**
6. Select the ZIP file → Confirm → Done!

Your entire history — products, sales, purchases, invoices, and backups — will be restored.

---

## 🛡️ 11. Safety & Backups

### Automatic Backups
Every sale and purchase creates a timestamped backup:
- Location: `backups/backup_ERP_YYYYMMDD_HHMMSS.xlsx`
- Clean up old backups from Settings → General → Cleanup Old

### Manual Recovery
1. Go to `backups/` folder
2. Find the latest healthy backup
3. Rename it to `SunWarehouse_ERP_v3.xlsx`
4. Replace the original file in the project root
5. Open Settings → Database → Re-sync from Excel

### Audit Trail
All actions are logged in `logs/system.log` with timestamps.

