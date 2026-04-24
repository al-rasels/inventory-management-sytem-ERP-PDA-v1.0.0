import customtkinter as ctk
import os
from datetime import datetime
from src.core.config import APP_TITLE, COLORS, THEME, COLOR_THEME, WINDOW_SIZE, MIN_WINDOW_SIZE, SHORTCUTS, SQLITE_DB_PATH
from src.ui.views.dashboard import DashboardView
from src.ui.views.products import ProductsView
from src.ui.views.sales import SalesView
from src.ui.views.purchases import PurchaseView
from src.ui.views.inventory import InventoryView
from src.ui.views.analytics import AnalyticsView
from src.ui.views.settings import SettingsView
from src.ui.views.transactions import TransactionsView
from src.core.database import DatabaseEngine
from src.core.inventory_manager import InventoryManager

ctk.set_appearance_mode(THEME)
ctk.set_default_color_theme(COLOR_THEME)

class ERPApp(ctk.CTk):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(*MIN_WINDOW_SIZE)
        
        self.db = DatabaseEngine()
        self.im = InventoryManager(self.db)
        self.cart = []  # Shared cart across views
        self.active_nav = None
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ─── Sidebar ───
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=COLORS["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Logo area
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=100)
        logo_frame.pack(fill="x", pady=(30, 20))
        logo_frame.pack_propagate(False)
        
        self.logo_icon = ctk.CTkLabel(logo_frame, text="☀", font=ctk.CTkFont(size=42))
        self.logo_icon.pack()
        self.logo_label = ctk.CTkLabel(logo_frame, text="SUN WAREHOUSE", font=ctk.CTkFont(size=16, weight="bold"),
                                       text_color=COLORS["accent_light"])
        self.logo_label.pack()

        # Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=20, pady=10)

        # Nav Buttons
        self.nav_btns = {}
        nav_items = [
            ("📊  Dashboard", "Dashboard", self.show_dashboard),
            ("📦  Products", "Products", self.show_products),
            ("🧾  Sales", "Sales", self.show_sales),
            ("🚚  Purchases", "Purchases", self.show_purchases),
            ("📈  Inventory", "Inventory", self.show_inventory),
            ("🔍  Analytics", "Analytics", self.show_analytics),
            ("📜  Transactions", "Transactions", self.show_transactions),
            ("⚙️  Settings", "Settings", self.show_settings),
        ]

        for text, key, command in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=text, fg_color="transparent",
                text_color=COLORS["text_secondary"], hover_color=COLORS["sidebar_active"],
                anchor="w", command=command, height=42,
                font=ctk.CTkFont(size=14), corner_radius=10
            )
            btn.pack(fill="x", padx=15, pady=3)
            self.nav_btns[key] = btn

        # Bottom section
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=15, pady=25)
        
        ctk.CTkFrame(bottom_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=(0, 15))
        
        user_info = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        user_info.pack(fill="x")
        
        ctk.CTkLabel(user_info, text=f"👤 {user_data['full_name']}", 
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(user_info, text=f"Role: {user_data['role']}", 
                     font=ctk.CTkFont(size=11),
                     text_color=COLORS["text_muted"]).pack(anchor="w")
        
        self.logout_btn = ctk.CTkButton(
            bottom_frame, text="🚪 Logout", fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"], height=35,
            command=self.logout, font=ctk.CTkFont(size=13, weight="bold")
        )
        self.logout_btn.pack(fill="x", pady=(15, 0))

        # ─── Main Content Area ───
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["bg"])
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        # ─── Status Bar ───
        self.status_bar = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color=COLORS["sidebar"])
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        self.status_left = ctk.CTkLabel(self.status_bar, text=f"  System Ready | High Performance Mode (Excel Sync: Manual)", 
                                        font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"])
        self.status_left.pack(side="left", padx=15)
        
        self.status_right = ctk.CTkLabel(self.status_bar, text="", font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"])
        self.status_right.pack(side="right", padx=20)
        
        self._update_clock()

        self.current_view = None

        # Keyboard shortcuts
        self.bind(SHORTCUTS["new_sale"], lambda e: self.show_sales())
        self.bind(SHORTCUTS["new_purchase"], lambda e: self.show_purchases())
        self.bind(SHORTCUTS["dashboard"], lambda e: self.show_dashboard())

        self.show_dashboard()

    def _update_clock(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_right.configure(text=f"👤 {self.user_data['username']} | 🕒 {now}")
        self.after(1000, self._update_clock)

    def set_active_nav(self, key):
        """Highlight the active navigation button."""
        for name, btn in self.nav_btns.items():
            if name == key:
                btn.configure(fg_color=COLORS["sidebar_active"], text_color=COLORS["accent_light"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_secondary"])
        self.active_nav = key

    def clear_content(self):
        if self.current_view:
            self.current_view.destroy()

    def show_dashboard(self):
        self.clear_content()
        self.set_active_nav("Dashboard")
        self.current_view = DashboardView(self.content_frame, self.db, self.im)
        self.current_view.pack(fill="both", expand=True)

    def show_products(self):
        self.clear_content()
        self.set_active_nav("Products")
        self.current_view = ProductsView(self.content_frame, self.db, self.im, app=self)
        self.current_view.pack(fill="both", expand=True)

    def show_sales(self):
        self.clear_content()
        self.set_active_nav("Sales")
        self.current_view = SalesView(self.content_frame, self.db, app=self)
        self.current_view.pack(fill="both", expand=True)

    def show_purchases(self):
        self.clear_content()
        self.set_active_nav("Purchases")
        self.current_view = PurchaseView(self.content_frame, self.db)
        self.current_view.pack(fill="both", expand=True)

    def show_inventory(self):
        self.clear_content()
        self.set_active_nav("Inventory")
        self.current_view = InventoryView(self.content_frame, self.db, self.im)
        self.current_view.pack(fill="both", expand=True)

    def show_analytics(self):
        self.clear_content()
        self.set_active_nav("Analytics")
        self.current_view = AnalyticsView(self.content_frame, self.db, self.im)
        self.current_view.pack(fill="both", expand=True)

    def show_settings(self):
        self.clear_content()
        self.set_active_nav("Settings")
        self.current_view = SettingsView(self.content_frame, self.db, user_data=self.user_data)
        self.current_view.pack(fill="both", expand=True)

    def show_transactions(self):
        self.clear_content()
        self.set_active_nav("Transactions")
        self.current_view = TransactionsView(self.content_frame, self.db)
        self.current_view.pack(fill="both", expand=True)

    def logout(self):
        self.destroy()
        # Re-launch login screen
        from src.main import LoginScreen
        login = LoginScreen()
        login.mainloop()

if __name__ == "__main__":
    app = ERPApp({"username": "admin", "full_name": "System Admin", "role": "Admin"})
    app.mainloop()
