import customtkinter as ctk
from src.core.config import COLORS, DEFAULT_CURRENCY
import pandas as pd

class InventoryView(ctk.CTkFrame):
    def __init__(self, master, inventory_service):
        super().__init__(master, fg_color="transparent")
        self.inventory_service = inventory_service
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="Inventory Ledger", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")

        # Summary cards
        # Summary cards using service
        stock_df = self.inventory_service.get_stock_status()
        total_value = stock_df['inventory_value'].sum()
        total_items = stock_df['current_stock'].sum()
        out_of_stock = len(stock_df[stock_df['current_stock'] <= 0])

        summary = ctk.CTkFrame(self, fg_color="transparent")
        summary.pack(fill="x", pady=(0, 10))
        summary.columnconfigure((0, 1, 2, 3), weight=1)

        self._mini_card(summary, "Total Units", f"{total_items:,}", COLORS["accent"], 0)
        self._mini_card(summary, "Stock Value", f"{DEFAULT_CURRENCY} {total_value:,.0f}", COLORS["success"], 1)
        self._mini_card(summary, "SKU Count", str(len(stock_df)), COLORS["info"], 2)
        self._mini_card(summary, "Out of Stock", str(out_of_stock), COLORS["danger"] if out_of_stock > 0 else COLORS["success"], 3)

        # Filter bar
        filter_bar = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=8, height=45)
        filter_bar.pack(fill="x", pady=(0, 8))
        filter_bar.pack_propagate(False)

        ctk.CTkLabel(filter_bar, text="Filter:", text_color=COLORS["text_muted"]).pack(side="left", padx=15)
        self.stock_filter = ctk.CTkComboBox(filter_bar, values=["All", "Low Stock", "Out of Stock", "Healthy"],
                                             width=150, command=self._on_filter)
        self.stock_filter.set("All")
        self.stock_filter.pack(side="left", padx=5)

        categories = self.inventory_service.product_repo.get_categories()
        cat_list = ["All Categories"] + categories
        self.cat_filter = ctk.CTkComboBox(filter_bar, values=cat_list, width=160, command=self._on_filter)
        self.cat_filter.set("All Categories")
        self.cat_filter.pack(side="left", padx=5)

        # Table
        self.table = ctk.CTkScrollableFrame(self, fg_color=COLORS["card"], corner_radius=10)
        self.table.pack(fill="both", expand=True)
        for i in range(7):
            self.table.columnconfigure(i, weight=1 if i == 1 else 0)

        self._render_ledger()

    def _mini_card(self, parent, title, value, color, col):
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=10, height=65)
        card.grid(row=0, column=col, padx=4, sticky="nsew")
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(pady=(8, 0))
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack()

    def _render_ledger(self, stock_filter="All", cat_filter="All Categories"):
        for w in self.table.winfo_children():
            w.destroy()

        headers = ["Product ID", "Name", "Category", "Purchased", "Sold", "Balance", "Value"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.table, text=h, font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=COLORS["text_muted"]).grid(row=0, column=i, padx=12, pady=(10, 5), sticky="w")
        ctk.CTkFrame(self.table, height=1, fg_color=COLORS["border"]).grid(row=1, column=0, columnspan=7, sticky="ew", padx=5)

        df = self.inventory_service.get_stock_status()
        if cat_filter != "All Categories":
            df = df[df['category'] == cat_filter]
        
        df = df.sort_values('product_id')
        
        row_num = 2
        for _, row in df.iterrows():
            balance = int(row['current_stock'])
            reorder = int(row['reorder_qty'] if pd.notna(row['reorder_qty']) else 50)
            
            # Apply stock filter
            if stock_filter == "Low Stock" and balance >= reorder:
                continue
            elif stock_filter == "Out of Stock" and balance > 0:
                continue
            elif stock_filter == "Healthy" and balance < reorder:
                continue

            # Color coding
            if balance <= 0:
                bal_color = COLORS["danger"]
                bal_text = f"⛔ {balance}"
            elif balance < reorder:
                bal_color = COLORS["warning"]
                bal_text = f"⚠️ {balance}"
            else:
                bal_color = COLORS["success"]
                bal_text = f"✅ {balance}"
            
            cost = row['cost_price'] or 0
            value = balance * cost

            bg = COLORS["card_hover"] if row_num % 2 == 0 else "transparent"

            ctk.CTkLabel(self.table, text=row['product_id'], font=ctk.CTkFont(size=11),
                        text_color=COLORS["accent"]).grid(row=row_num, column=0, padx=12, pady=3, sticky="w")
            ctk.CTkLabel(self.table, text=row['name'], font=ctk.CTkFont(size=11)).grid(
                row=row_num, column=1, padx=12, pady=3, sticky="w")
            ctk.CTkLabel(self.table, text=row['category'], font=ctk.CTkFont(size=11),
                        text_color=COLORS["text_secondary"]).grid(row=row_num, column=2, padx=12, pady=3, sticky="w")
            ctk.CTkLabel(self.table, text=str(int(row['total_in'])), font=ctk.CTkFont(size=11)).grid(
                row=row_num, column=3, padx=12, pady=3, sticky="w")
            ctk.CTkLabel(self.table, text=str(int(row['total_out'])), font=ctk.CTkFont(size=11)).grid(
                row=row_num, column=4, padx=12, pady=3, sticky="w")
            ctk.CTkLabel(self.table, text=bal_text, font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=bal_color).grid(row=row_num, column=5, padx=12, pady=3, sticky="w")
            ctk.CTkLabel(self.table, text=f"{DEFAULT_CURRENCY} {value:,.0f}", font=ctk.CTkFont(size=11),
                        text_color=COLORS["text_secondary"]).grid(row=row_num, column=6, padx=12, pady=3, sticky="w")
            row_num += 1

    def _on_filter(self, choice=None):
        self._render_ledger(
            stock_filter=self.stock_filter.get(),
            cat_filter=self.cat_filter.get()
        )
