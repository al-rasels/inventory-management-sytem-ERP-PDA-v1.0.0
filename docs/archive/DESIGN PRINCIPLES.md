🎨 DESIGN PRINCIPLES (WHAT MAKES THIS “PRO LEVEL”)
Clean, minimal, no clutter
Dark + light mode support
Fast access (≤2 clicks for any action)
Data-first (numbers always visible)
Color meaning:
🟢 Profit / Positive
🔴 Loss / Alerts
🟡 Warning / Low stock
🔵 Info / Neutral
🧱 GLOBAL LAYOUT (ALL SCREENS)
┌──────────────────────────────┐
│ Sidebar (Navigation)         │
│------------------------------│
│ Logo                         │
│ Dashboard                    │
│ Products                     │
│ Purchases                    │
│ Sales                        │
│ Inventory                    │
│ Reports                      │
│ Analytics                    │
│ Settings                     │
│------------------------------│
│ User Profile / Logout        │
└──────────────┬───────────────┘
               │
        Main Content Area
               │
        Top Bar (Search + Actions)
🏠 1. DASHBOARD (MAIN SCREEN)
🎯 Purpose:

Instant business visibility

UI Layout:
┌──────────────────────────────────────────────┐
│ Top Bar: Search | Notifications | Date       │
├──────────────────────────────────────────────┤
│ KPI CARDS                                    │
│ [Revenue] [Profit] [Stock Value] [Sales]      │
├──────────────────────────────────────────────┤
│ Charts Row                                   │
│ Sales Trend     | Profit Trend               │
├──────────────────────────────────────────────┤
│ Bottom Section                               │
│ Top Products | Low Stock | Recent Sales      │
└──────────────────────────────────────────────┘
💡 Features:
Live refresh
Click KPI → drill-down
Alerts panel:
Low stock
High profit items
Dead stock
📦 2. PRODUCT MANAGEMENT
Layout:
┌──────────────────────────────────────────────┐
│ Search | Filter | + Add Product              │
├──────────────────────────────────────────────┤
│ Table:                                      │
│ SKU | Name | Category | Cost | Price | Stock │
├──────────────────────────────────────────────┤
│ Right Panel (on select):                     │
│ - Product details                           │
│ - Price history                             │
│ - Stock history                             │
└──────────────────────────────────────────────┘
💡 Modern Features:
Inline editing
Color highlight:
Low stock = yellow
Quick actions:
Edit
Delete
View analytics
🚚 3. PURCHASE SCREEN
Layout:
┌──────────────────────────────────────────────┐
│ Supplier Dropdown | Date | Invoice No        │
├──────────────────────────────────────────────┤
│ Add Items Table                             │
│ Product | Qty | Cost | Extra Cost | Total   │
├──────────────────────────────────────────────┤
│ Summary Panel                               │
│ Total Qty | Total Cost                      │
├──────────────────────────────────────────────┤
│ [Save Purchase] [Cancel]                    │
└──────────────────────────────────────────────┘
💡 Smart UX:
Auto-calc totals
Batch creation
Add multiple products fast (tab navigation)
🧾 4. SALES & INVOICE SCREEN (CRITICAL)
Layout:
┌──────────────────────────────────────────────┐
│ Customer | Date | Invoice ID                │
├──────────────────────────────────────────────┤
│ Add Product Section                         │
│ Scan / Search Product                      │
├──────────────────────────────────────────────┤
│ Sales Table                                 │
│ Product | Qty | Price | Discount | Total    │
├──────────────────────────────────────────────┤
│ Right Summary Panel                         │
│ Subtotal                                    │
│ Discount                                    │
│ Profit                                      │
│ Grand Total                                 │
├──────────────────────────────────────────────┤
│ Payment: Cash / Due / Partial               │
│ [Generate Invoice] [Complete Sale]          │
└──────────────────────────────────────────────┘
🔥 Advanced Features:
Barcode scanner support
Real-time profit display
Stock auto-check (prevent oversell)
📊 5. INVENTORY SCREEN
Layout:
┌──────────────────────────────────────────────┐
│ Filters: Category | Stock Level | Batch      │
├──────────────────────────────────────────────┤
│ Inventory Table                             │
│ Product | Batch | Qty | Cost | Age | Value  │
├──────────────────────────────────────────────┤
│ Right Panel                                │
│ - Stock movement history                   │
│ - Purchase batches                         │
└──────────────────────────────────────────────┘
💡 Features:
FIFO tracking
Stock aging (🔥 important for profit)
📈 6. REPORTS SCREEN
Layout:
┌──────────────────────────────────────────────┐
│ Filters: Date | Product | Category           │
├──────────────────────────────────────────────┤
│ Report Table                                │
├──────────────────────────────────────────────┤
│ Export Options                              │
│ [Export Excel] [Export PDF]                 │
└──────────────────────────────────────────────┘
📊 7. ANALYTICS (HIGH VALUE)
Layout:
┌──────────────────────────────────────────────┐
│ Tabs:                                       │
│ Sales | Profit | Products | Trends           │
├──────────────────────────────────────────────┤
│ Charts + Insights                           │
│ - Top selling products                      │
│ - Profit margin analysis                    │
│ - Dead stock                               │
└──────────────────────────────────────────────┘
💡 Smart Insights:
“This product gives highest profit”
“This product is not selling”
⚙️ 8. SETTINGS
User management
Backup settings
Pricing rules
Theme (Dark/Light)
🔐 9. LOGIN SCREEN
Centered Card UI:
- Logo
- Username
- Password
- Login button
🎨 UI STYLE GUIDE
Colors:
Background: #0F172A (dark)
Card: #1E293B
Accent: #3B82F6
Success: #10B981
Danger: #EF4444
Typography:
Header: Bold
Body: Clean sans-serif
Components:
Rounded cards
Soft shadows
Hover effects
⚡ UX ENHANCEMENTS (IMPORTANT)
Keyboard shortcuts:
F1 → Add product
F2 → New sale
Auto-save drafts
Undo last action
Toast notifications (success/error)