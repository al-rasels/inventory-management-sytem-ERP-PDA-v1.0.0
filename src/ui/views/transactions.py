import customtkinter as ctk
from src.core.config import COLORS, DEFAULT_CURRENCY
from datetime import datetime

class TransactionsView(ctk.CTkFrame):
    def __init__(self, master, reporting_service):
        super().__init__(master, fg_color="transparent")
        self.reporting_service = reporting_service
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="Transaction History", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        ctk.CTkLabel(header, text="Audit logs for all operations", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_muted"]).pack(side="left", padx=15)

        # Filter bar
        filter_bar = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=10, height=50)
        filter_bar.pack(fill="x", pady=(0, 10))
        filter_bar.pack_propagate(False)

        ctk.CTkLabel(filter_bar, text="🔍", font=ctk.CTkFont(size=16)).pack(side="left", padx=(15, 5))
        self.search_entry = ctk.CTkEntry(filter_bar, placeholder_text="Search by ID, Product, or Customer...", 
                                          width=400, border_width=0, fg_color="transparent")
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self._on_search)

        self.refresh_btn = ctk.CTkButton(filter_bar, text="🔄 Refresh", width=100, height=30,
                                         fg_color=COLORS["border"], hover_color=COLORS["card_hover"],
                                         command=self._load_data)
        self.refresh_btn.pack(side="right", padx=15)

        # Tabs
        self.tab_view = ctk.CTkTabview(self, fg_color=COLORS["card"], corner_radius=12,
                                        segmented_button_fg_color=COLORS["sidebar"],
                                        segmented_button_selected_color=COLORS["accent"])
        self.tab_view.pack(fill="both", expand=True)

        self.sales_tab = self.tab_view.add("🧾 Sales History")
        self.purchase_tab = self.tab_view.add("🚚 Purchase History")

        # Scrollable containers
        self.sales_frame = ctk.CTkScrollableFrame(self.sales_tab, fg_color="transparent")
        self.sales_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.purchase_frame = ctk.CTkScrollableFrame(self.purchase_tab, fg_color="transparent")
        self.purchase_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._load_data()

    def _load_data(self, search_term=None):
        self._render_sales(search_term)
        self._render_purchases(search_term)

    def _render_sales(self, search_term=None):
        for w in self.sales_frame.winfo_children():
            w.destroy()

        df = self.reporting_service.get_sales_history(search_term)

        if df.empty:
            ctk.CTkLabel(self.sales_frame, text="No sales records found.", text_color=COLORS["text_muted"]).pack(pady=40)
            return

        # Header row
        hdr = ctk.CTkFrame(self.sales_frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(5, 10))
        headers = [("ID", 100), ("Date", 120), ("Product", 200), ("Customer", 150), ("Qty", 70), ("Revenue", 100)]
        for text, w in headers:
            ctk.CTkLabel(hdr, text=text, width=w, font=ctk.CTkFont(size=12, weight="bold"),
                        text_color=COLORS["text_muted"], anchor="w").pack(side="left", padx=5)

        for i, row in df.iterrows():
            r_frame = ctk.CTkFrame(self.sales_frame, fg_color=COLORS["card_hover"] if i % 2 == 0 else "transparent", corner_radius=6)
            r_frame.pack(fill="x", pady=1)
            
            ctk.CTkLabel(r_frame, text=row['sales_id'], width=100, font=ctk.CTkFont(size=11), text_color=COLORS["accent"], anchor="w").pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(r_frame, text=row['date'][:10], width=120, font=ctk.CTkFont(size=11), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=row['product_name'], width=200, font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=row['customer'], width=150, font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"], anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=str(row['qty']), width=70, font=ctk.CTkFont(size=11), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=f"{DEFAULT_CURRENCY} {row['revenue']:,.0f}", width=100, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["success"], anchor="w").pack(side="left", padx=5)

    def _render_purchases(self, search_term=None):
        for w in self.purchase_frame.winfo_children():
            w.destroy()

        df = self.reporting_service.get_purchase_history(search_term)

        if df.empty:
            ctk.CTkLabel(self.purchase_frame, text="No purchase records found.", text_color=COLORS["text_muted"]).pack(pady=40)
            return

        # Header row
        hdr = ctk.CTkFrame(self.purchase_frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(5, 10))
        headers = [("ID", 100), ("Date", 120), ("Product", 200), ("Supplier", 150), ("Qty", 70), ("Cost", 100)]
        for text, w in headers:
            ctk.CTkLabel(hdr, text=text, width=w, font=ctk.CTkFont(size=12, weight="bold"),
                        text_color=COLORS["text_muted"], anchor="w").pack(side="left", padx=5)

        for i, row in df.iterrows():
            r_frame = ctk.CTkFrame(self.purchase_frame, fg_color=COLORS["card_hover"] if i % 2 == 0 else "transparent", corner_radius=6)
            r_frame.pack(fill="x", pady=1)
            
            ctk.CTkLabel(r_frame, text=row['purchase_id'], width=100, font=ctk.CTkFont(size=11), text_color=COLORS["warning"], anchor="w").pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(r_frame, text=row['date'][:10], width=120, font=ctk.CTkFont(size=11), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=row['product_name'], width=200, font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=row['supplier'] or "N/A", width=150, font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"], anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=str(row['qty']), width=70, font=ctk.CTkFont(size=11), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=f"{DEFAULT_CURRENCY} {row['total_cost']:,.0f}", width=100, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["accent"], anchor="w").pack(side="left", padx=5)

    def _on_search(self, event=None):
        search_term = self.search_entry.get().strip()
        self._load_data(search_term if search_term else None)
