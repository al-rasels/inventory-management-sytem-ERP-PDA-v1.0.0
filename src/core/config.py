import os

# Base Directories
BASE_DIR = os.path.normpath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
LOG_DIR = os.path.join(BASE_DIR, "logs")
INVOICE_DIR = os.path.join(BASE_DIR, "invoices")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")

# Ensure directories exist at import time
for d in [DATA_DIR, BACKUP_DIR, LOG_DIR, INVOICE_DIR, EXPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

# Excel Source
EXCEL_DB_PATH = os.path.join(BASE_DIR, "SunERP_Master_Database.xlsx")

# SQLite Cache
SQLITE_DB_PATH = os.path.join(DATA_DIR, "erp_cache.db")

# UI Settings
APP_TITLE = "SunERP Professional v3.0"
APP_VERSION = "3.0.0"
THEME = "dark"  # "light" or "dark"
COLOR_THEME = "blue"
WINDOW_SIZE = "1400x850"
MIN_WINDOW_SIZE = (1100, 700)

# Professional Dual-Theme Palette (Light, Dark)
COLORS = {
    # Backgrounds
    "bg": ("#F1F5F9", "#0F172A"),
    "bg_dark": ("#E2E8F0", "#0B1120"),
    "card": ("#FFFFFF", "#1E293B"),
    "card_hover": ("#F8FAFC", "#273548"),
    "sidebar": ("#F8FAFC", "#0B1120"),
    "sidebar_active": ("#E2E8F0", "#1E3A5F"),
    
    # Accents
    "accent": ("#3B82F6", "#3B82F6"),
    "accent_hover": ("#2563EB", "#2563EB"),
    "accent_light": ("#60A5FA", "#60A5FA"),
    
    # Semantic
    "success": ("#10B981", "#10B981"),
    "success_hover": ("#059669", "#059669"),
    "danger": ("#EF4444", "#EF4444"),
    "danger_hover": ("#DC2626", "#DC2626"),
    "warning": ("#F59E0B", "#F59E0B"),
    "warning_hover": ("#D97706", "#D97706"),
    "info": ("#06B6D4", "#06B6D4"),
    "info_hover": ("#0891B2", "#0891B2"),
    
    # Text
    "text": ("#1E293B", "#F8FAFC"),
    "text_secondary": ("#475569", "#CBD5E1"),
    "text_muted": ("#94A3B8", "#64748B"),
    "text_accent": ("#2563EB", "#60A5FA"),
    
    # Borders
    "border": ("#CBD5E1", "#334155"),
    "border_light": ("#E2E8F0", "#475569"),
}

# Slowness Settings
AUTO_SYNC_EXCEL = False  # Set to False to solve slowness. Users can sync manually in Settings.

# Business Rules
LOW_STOCK_THRESHOLD = 50
DEAD_STOCK_DAYS = 30
VAT_PERCENT = 0.0  # Adjustable in settings
DEFAULT_CURRENCY = "৳"
MAX_BACKUP_FILES = 50  # Auto-cleanup old backups

# Security
SESSION_TIMEOUT = 3600  # 1 hour
AUDIT_LOG_ENABLED = True
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "admin123"

# Keyboard Shortcuts
SHORTCUTS = {
    "new_sale": "<F2>",
    "new_purchase": "<F3>",
    "add_product": "<F1>",
    "dashboard": "<F5>",
    "search": "<Control-f>",
}
