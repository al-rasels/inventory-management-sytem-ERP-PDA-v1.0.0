import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from src.core.config import COLORS, DEFAULT_CURRENCY

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, db, im):
        super().__init__(master, fg_color="transparent")
        self.db = db
        self.im = im
        
        # Title bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="Dashboard", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        ctk.CTkLabel(header, text="Live business overview", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_muted"]).pack(side="left", padx=15)

        # KPI Row
        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, 15))
        kpi_frame.columnconfigure((0, 1, 2, 3), weight=1)

        # Fetch real KPI data
        rev_df = self.db.execute_query("SELECT IFNULL(SUM(revenue), 0) as val FROM sales")
        total_revenue = rev_df.iloc[0]['val']

        prof_df = self.db.execute_query("SELECT IFNULL(SUM(profit), 0) as val FROM sales")
        total_profit = prof_df.iloc[0]['val']

        stock_df = self.im.get_current_stock()
        total_products = len(stock_df)

        low_stock = self.im.get_low_stock_items()
        low_count = len(low_stock)

        self._kpi_card(kpi_frame, "Total Revenue", f"{DEFAULT_CURRENCY} {total_revenue:,.0f}", COLORS["accent"], "📈", 0)
        self._kpi_card(kpi_frame, "Total Profit", f"{DEFAULT_CURRENCY} {total_profit:,.0f}", COLORS["success"], "💰", 1)
        self._kpi_card(kpi_frame, "Active Products", str(total_products), COLORS["info"], "📦", 2)
        self._kpi_card(kpi_frame, "Low Stock Alerts", str(low_count), COLORS["danger"] if low_count > 0 else COLORS["success"], "⚠️", 3)

        # Charts + Info Row
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="both", expand=True)
        bottom.columnconfigure(0, weight=3)
        bottom.columnconfigure(1, weight=1)
        bottom.rowconfigure(0, weight=1)

        # Sales Chart
        chart_card = ctk.CTkFrame(bottom, fg_color=COLORS["card"], corner_radius=15)
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        self._render_chart(chart_card)

        # Right panel: Low stock + Recent sales
        right = ctk.CTkFrame(bottom, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure((0, 1), weight=1)

        # Low Stock Panel
        low_card = ctk.CTkFrame(right, fg_color=COLORS["card"], corner_radius=15)
        low_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        ctk.CTkLabel(low_card, text="⚠️ Low Stock Alerts", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COLORS["warning"]).pack(pady=(15, 10), padx=20, anchor="w")
        
        if low_stock.empty:
            ctk.CTkLabel(low_card, text="All stock levels healthy ✅", text_color=COLORS["success"],
                         font=ctk.CTkFont(size=13)).pack(padx=20, anchor="w")
        else:
            for _, row in low_stock.head(5).iterrows():
                stock_val = int(row['current_stock'])
                color = COLORS["danger"] if stock_val <= 0 else COLORS["warning"]
                ctk.CTkLabel(low_card, text=f"• {row['name']}: {stock_val} left",
                            font=ctk.CTkFont(size=12), text_color=color).pack(padx=20, pady=2, anchor="w")

        # Recent Transactions Panel
        recent_card = ctk.CTkFrame(right, fg_color=COLORS["card"], corner_radius=15)
        recent_card.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        ctk.CTkLabel(recent_card, text="🧾 Recent Activity", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COLORS["accent"]).pack(pady=(15, 10), padx=20, anchor="w")
        
        # Combined query for sales and purchases
        combined_query = """
            SELECT 'SALE' as type, s.date, p.name, s.revenue as amt
            FROM sales s JOIN products p ON s.product_id = p.product_id
            UNION ALL
            SELECT 'PURCHASE' as type, pur.date, p.name, pur.total_cost as amt
            FROM purchases pur JOIN products p ON pur.product_id = p.product_id
            ORDER BY date DESC LIMIT 8
        """
        recent_df = self.db.execute_query(combined_query)
        
        if recent_df.empty:
            ctk.CTkLabel(recent_card, text="No transactions recorded today", text_color=COLORS["text_muted"],
                         font=ctk.CTkFont(size=13)).pack(padx=20, anchor="w")
        else:
            for _, row in recent_df.iterrows():
                icon = "🧾" if row['type'] == 'SALE' else "🚚"
                color = COLORS["success"] if row['type'] == 'SALE' else COLORS["warning"]
                ctk.CTkLabel(recent_card, text=f"{icon} {row['name']}: {DEFAULT_CURRENCY}{row['amt']:,.0f}",
                            font=ctk.CTkFont(size=12), text_color=color).pack(padx=20, pady=2, anchor="w")

    def _kpi_card(self, parent, title, value, color, icon, col):
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=15, height=120)
        card.grid(row=0, column=col, padx=8, sticky="nsew")
        card.pack_propagate(False)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(18, 0))
        ctk.CTkLabel(top, text=icon, font=ctk.CTkFont(size=24)).pack(side="left")
        ctk.CTkLabel(top, text=title, font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"]).pack(side="left", padx=10)

        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=26, weight="bold"), text_color=color).pack(padx=20, pady=(8, 15), anchor="w")

    def _render_chart(self, parent):
        ctk.CTkLabel(parent, text="📊 Sales Performance (Last 7 Days)", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLORS["text"]).pack(pady=(15, 0), padx=20, anchor="w")

        # Try to get real grouped data
        df = self.db.execute_query("""
            SELECT date, SUM(revenue) as daily_rev 
            FROM sales GROUP BY date ORDER BY date DESC LIMIT 7
        """)
        
        if df.empty or len(df) < 2:
            ctk.CTkLabel(parent, text="Insufficient data for trend analysis.\nContinue logging sales to unlock visualizations.",
                        text_color=COLORS["text_muted"], font=ctk.CTkFont(size=14)).pack(expand=True)
            return

        df = df.iloc[::-1]
        labels = [str(d)[-5:] for d in df['date']]
        values = df['daily_rev'].tolist()

        # Theme aware background for matplotlib
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = COLORS["card"][1] if is_dark else COLORS["card"][0]
        text_color = COLORS["text_muted"][1] if is_dark else COLORS["text_muted"][0]
        grid_color = COLORS["border"][1] if is_dark else COLORS["border"][0]

        fig, ax = plt.subplots(figsize=(8, 4), facecolor=bg_color)
        ax.fill_between(range(len(values)), values, alpha=0.1, color=COLORS["accent"][0])
        ax.plot(range(len(values)), values, marker='o', color=COLORS["accent"][0], linewidth=3, markersize=7)
        
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=9, color=text_color)
        ax.set_facecolor(bg_color)
        ax.tick_params(colors=text_color, labelsize=9)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}k'))
        
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.grid(axis='y', color=grid_color, alpha=0.2, linestyle='--')
        fig.tight_layout(pad=1.5)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(5, 15))
        plt.close(fig)
