import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from src.core.config import COLORS, DEFAULT_CURRENCY

class AnalyticsView(ctk.CTkFrame):
    def __init__(self, master, reporting_service):
        super().__init__(master, fg_color="transparent")
        self.reporting_service = reporting_service
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="Business Analytics", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")

        # Tabs
        self.tab_view = ctk.CTkTabview(self, fg_color=COLORS["card"], corner_radius=12,
                                        segmented_button_fg_color=COLORS["sidebar"],
                                        segmented_button_selected_color=COLORS["accent"])
        self.tab_view.pack(fill="both", expand=True)

        self.tab_view.add("📊 Overview")
        self.tab_view.add("🏆 Top Products")
        self.tab_view.add("💀 Dead Stock")
        self.tab_view.add("📈 Profit Analysis")

        self._build_overview(self.tab_view.tab("📊 Overview"))
        self._build_top_products(self.tab_view.tab("🏆 Top Products"))
        self._build_dead_stock(self.tab_view.tab("💀 Dead Stock"))
        self._build_profit(self.tab_view.tab("📈 Profit Analysis"))

    def _build_overview(self, parent):
        parent.columnconfigure((0, 1), weight=1)
        parent.rowconfigure(0, weight=1)

        # Financial summary
        fin = ctk.CTkFrame(parent, fg_color=COLORS["card_hover"], corner_radius=10)
        fin.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)

        ctk.CTkLabel(fin, text="💰 Financial Summary", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COLORS["accent"]).pack(pady=(15, 10), padx=15, anchor="w")

        summary = self.reporting_service.get_sales_summary(days=365)
        rev = summary["revenue"]
        prof = summary["profit"]
        units = summary["units"]
        # Need COGS from somewhere - maybe add to summary or calculate here
        cogs = rev - prof
        margin = (prof / rev * 100) if rev > 0 else 0
        transactions = summary.get("transactions", 0)
        avg_sale = rev / transactions if transactions > 0 else 0

        metrics = [
            ("Total Revenue", f"{DEFAULT_CURRENCY} {rev:,.0f}", COLORS["accent"]),
            ("Total COGS", f"{DEFAULT_CURRENCY} {cogs:,.0f}", COLORS["warning"]),
            ("Net Profit", f"{DEFAULT_CURRENCY} {prof:,.0f}", COLORS["success"] if prof > 0 else COLORS["danger"]),
            ("Profit Margin", f"{margin:.1f}%", COLORS["success"] if margin > 15 else COLORS["warning"]),
            ("Total Transactions", str(int(transactions)), COLORS["text"]),
            ("Avg Sale Value", f"{DEFAULT_CURRENCY} {avg_sale:,.0f}", COLORS["info"]),
        ]

        for name, val, color in metrics:
            row = ctk.CTkFrame(fin, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=4)
            ctk.CTkLabel(row, text=name, font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(side="left")
            ctk.CTkLabel(row, text=val, font=ctk.CTkFont(size=13, weight="bold"), text_color=color).pack(side="right")

        # Reorder alerts
        reorder = ctk.CTkFrame(parent, fg_color=COLORS["card_hover"], corner_radius=10)
        reorder.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)

        ctk.CTkLabel(reorder, text="🔔 Reorder Alerts", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COLORS["warning"]).pack(pady=(15, 10), padx=15, anchor="w")

        low_df = self.reporting_service.get_reorder_alerts()
        if low_df.empty:
            ctk.CTkLabel(reorder, text="✅ All stock levels are healthy!", text_color=COLORS["success"],
                        font=ctk.CTkFont(size=13)).pack(padx=15, pady=10)
        else:
            for _, r in low_df.head(10).iterrows():
                s = int(r['current_stock'])
                icon = "⛔" if s <= 0 else "⚠️"
                color = COLORS["danger"] if s <= 0 else COLORS["warning"]
                row = ctk.CTkFrame(reorder, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=2)
                ctk.CTkLabel(row, text=f"{icon} {r['name']}", font=ctk.CTkFont(size=11)).pack(side="left")
                ctk.CTkLabel(row, text=f"{s} units", font=ctk.CTkFont(size=11, weight="bold"),
                            text_color=color).pack(side="right")

    def _build_top_products(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")

        df = self.reporting_service.get_top_selling_products(limit=15)
        # Adding profit calculation for the view since the service might not return it
        # Actually, let's update service to return profit too

        if df.empty:
            ctk.CTkLabel(frame, text="No sales data available yet.", text_color=COLORS["text_muted"]).pack(pady=30)
            return

        # Podium for top 3
        for i, (_, row) in enumerate(df.head(3).iterrows()):
            medals = ["🥇", "🥈", "🥉"]
            card = ctk.CTkFrame(frame, fg_color=COLORS["card_hover"], corner_radius=10)
            card.pack(fill="x", pady=4, padx=10)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", padx=15, pady=10)
            ctk.CTkLabel(left, text=f"{medals[i]} {row['name']}", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(left, text=f"{row['category']}  •  {int(row['units'])} units sold",
                        font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(anchor="w")

            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="right", padx=15, pady=10)
            ctk.CTkLabel(right, text=f"{DEFAULT_CURRENCY} {row['rev']:,.0f}", 
                        font=ctk.CTkFont(size=15, weight="bold"), text_color=COLORS["accent"]).pack(anchor="e")
            ctk.CTkLabel(right, text=f"Profit: {DEFAULT_CURRENCY} {row['prof']:,.0f}",
                        font=ctk.CTkFont(size=11), text_color=COLORS["success"]).pack(anchor="e")

        # Rest of list
        for _, row in df.iloc[3:].iterrows():
            r = ctk.CTkFrame(frame, fg_color="transparent")
            r.pack(fill="x", padx=15, pady=2)
            ctk.CTkLabel(r, text=f"• {row['name']} ({int(row['units'])} units)", font=ctk.CTkFont(size=11)).pack(side="left")
            ctk.CTkLabel(r, text=f"{DEFAULT_CURRENCY} {row['rev']:,.0f}", font=ctk.CTkFont(size=11),
                        text_color=COLORS["accent"]).pack(side="right")

    def _build_dead_stock(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")

        dead_df = self.reporting_service.get_dead_stock(days=30)

        ctk.CTkLabel(frame, text="Products with no sales in the last 30 days",
                    font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"]).pack(pady=(10, 15))

        if dead_df.empty:
            ctk.CTkLabel(frame, text="🎉 No dead stock! All products are moving.",
                        text_color=COLORS["success"], font=ctk.CTkFont(size=14)).pack(pady=20)
            return

        for _, row in dead_df.iterrows():
            card = ctk.CTkFrame(frame, fg_color=COLORS["card_hover"], corner_radius=8)
            card.pack(fill="x", padx=10, pady=3)
            
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", padx=15, pady=8)
            ctk.CTkLabel(left, text=f"💀 {row['name']}", font=ctk.CTkFont(size=12, weight="bold"),
                        text_color=COLORS["danger"]).pack(anchor="w")
            last_sale = row['last_sale_date'] if row['last_sale_date'] else "Never sold"
            ctk.CTkLabel(left, text=f"Last sale: {str(last_sale)[:10]}  •  {row['category']}",
                        font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"]).pack(anchor="w")

            ctk.CTkLabel(card, text="⚠️ Consider promotion", font=ctk.CTkFont(size=10),
                        text_color=COLORS["warning"]).pack(side="right", padx=15)

    def _build_profit(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")

        # Profit by category
        df = self.reporting_service.get_profit_by_category()

        if df.empty:
            ctk.CTkLabel(frame, text="No profit data available yet.", text_color=COLORS["text_muted"]).pack(pady=30)
            return

        ctk.CTkLabel(frame, text="Profit by Category", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))

        for _, row in df.iterrows():
            card = ctk.CTkFrame(frame, fg_color=COLORS["card_hover"], corner_radius=8)
            card.pack(fill="x", padx=10, pady=3)

            margin = row['margin']
            margin_color = COLORS["success"] if margin > 15 else (COLORS["warning"] if margin > 5 else COLORS["danger"])

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", padx=15, pady=8)
            ctk.CTkLabel(left, text=row['category'], font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(left, text=f"Revenue: {DEFAULT_CURRENCY} {row['rev']:,.0f}",
                        font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"]).pack(anchor="w")

            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="right", padx=15, pady=8)
            ctk.CTkLabel(right, text=f"{margin:.1f}% margin", font=ctk.CTkFont(size=13, weight="bold"),
                        text_color=margin_color).pack(anchor="e")
            ctk.CTkLabel(right, text=f"Profit: {DEFAULT_CURRENCY} {row['prof']:,.0f}",
                        font=ctk.CTkFont(size=10), text_color=COLORS["success"]).pack(anchor="e")
