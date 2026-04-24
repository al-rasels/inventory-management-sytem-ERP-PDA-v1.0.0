import customtkinter as ctk
from src.core.config import COLORS, DEFAULT_CURRENCY
from datetime import datetime
import tkinter.messagebox as messagebox

class PurchaseView(ctk.CTkFrame):
    def __init__(self, master, db):
        super().__init__(master, fg_color="transparent")
        self.db = db
        
        # Title
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="Purchase & Stock Entry", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")

        # Main layout
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(1, weight=1)

        # ─── Left: New Purchase Form ───
        form_card = ctk.CTkFrame(content, fg_color=COLORS["card"], corner_radius=12)
        form_card.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(form_card, text="📥 New Purchase", font=ctk.CTkFont(size=18, weight="bold")).pack(
            pady=(15, 10), padx=20, anchor="w")
        ctk.CTkFrame(form_card, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=15)

        # Product dropdown
        products_df = self.db.execute_query("SELECT product_id, name FROM products ORDER BY name")
        self.product_map = {f"{r['product_id']} - {r['name']}": r['product_id'] for _, r in products_df.iterrows()}
        product_options = list(self.product_map.keys())

        self.product_combo = self._field(form_card, "Product *", "combo", options=product_options)
        self.supplier_entry = self._field(form_card, "Supplier Name", "entry", placeholder="Enter supplier name")
        self.qty_entry = self._field(form_card, "Quantity *", "entry", placeholder="e.g. 100")
        self.cost_entry = self._field(form_card, "Cost Per Unit *", "entry", placeholder="e.g. 155.50")

        # Live total preview
        preview = ctk.CTkFrame(form_card, fg_color=COLORS["card_hover"], corner_radius=8)
        preview.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(preview, text="Total Cost:", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_muted"]).pack(side="left", padx=15, pady=10)
        self.total_preview_lbl = ctk.CTkLabel(preview, text=f"{DEFAULT_CURRENCY} 0",
                                               font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["accent"])
        self.total_preview_lbl.pack(side="right", padx=15, pady=10)
        
        # Bind for live preview
        self.qty_entry.bind("<KeyRelease>", self._update_preview)
        self.cost_entry.bind("<KeyRelease>", self._update_preview)

        # Save button
        self.save_btn = ctk.CTkButton(form_card, text="💾 Save Purchase", height=42,
                                       fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
                                       font=ctk.CTkFont(size=14, weight="bold"), command=self.save_purchase)
        self.save_btn.pack(fill="x", padx=20, pady=(5, 20))

        # ─── Right: Recent Purchases ───
        history_card = ctk.CTkFrame(content, fg_color=COLORS["card"], corner_radius=12)
        history_card.grid(row=0, column=1, rowspan=2, sticky="nsew")

        ctk.CTkLabel(history_card, text="📋 Recent Purchases", font=ctk.CTkFont(size=18, weight="bold")).pack(
            pady=(15, 10), padx=20, anchor="w")
        ctk.CTkFrame(history_card, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=15)

        self.history_frame = ctk.CTkScrollableFrame(history_card, fg_color="transparent")
        self.history_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self._render_history()

    def _field(self, parent, label, field_type, placeholder="", options=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 3))
        
        if field_type == "combo":
            widget = ctk.CTkComboBox(frame, values=options or [], width=350, height=35)
            widget.set(options[0] if options else "")
        else:
            widget = ctk.CTkEntry(frame, placeholder_text=placeholder, height=35)
        widget.pack(fill="x")
        return widget

    def _update_preview(self, event=None):
        try:
            qty = int(self.qty_entry.get() or 0)
            cost = float(self.cost_entry.get() or 0)
            total = qty * cost
            self.total_preview_lbl.configure(text=f"{DEFAULT_CURRENCY} {total:,.2f}")
        except ValueError:
            self.total_preview_lbl.configure(text=f"{DEFAULT_CURRENCY} ---")

    def _render_history(self):
        for w in self.history_frame.winfo_children():
            w.destroy()

        df = self.db.execute_query("""
            SELECT pur.purchase_id, pur.date, p.name, pur.qty, pur.cost_per_unit, pur.total_cost
            FROM purchases pur
            JOIN products p ON pur.product_id = p.product_id
            ORDER BY pur.date DESC LIMIT 15
        """)

        if df.empty:
            ctk.CTkLabel(self.history_frame, text="No purchases recorded yet.",
                        text_color=COLORS["text_muted"]).pack(pady=20)
            return

        for _, row in df.iterrows():
            card = ctk.CTkFrame(self.history_frame, fg_color=COLORS["card_hover"], corner_radius=8)
            card.pack(fill="x", pady=3)
            
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", padx=12, pady=8)
            ctk.CTkLabel(left, text=row['name'], font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(left, text=f"{row['date'][:10]}  •  Qty: {row['qty']}",
                        font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"]).pack(anchor="w")
            
            ctk.CTkLabel(card, text=f"{DEFAULT_CURRENCY} {row['total_cost']:,.0f}",
                        font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["accent"]).pack(side="right", padx=12)

    def save_purchase(self):
        selected = self.product_combo.get()
        qty_str = self.qty_entry.get()
        cost_str = self.cost_entry.get()
        supplier = self.supplier_entry.get().strip()
        
        if not selected or not qty_str or not cost_str:
            messagebox.showwarning("Incomplete", "Please fill Product, Quantity, and Cost fields!")
            return
            
        try:
            pid = self.product_map.get(selected)
            if not pid:
                messagebox.showerror("Error", "Invalid product selection!")
                return
                
            qty = int(qty_str)
            cost = float(cost_str)
            
            if qty <= 0 or cost <= 0:
                messagebox.showwarning("Invalid", "Quantity and Cost must be positive numbers!")
                return

            date_str = datetime.now().strftime("%Y-%m-%d")
            purchase_id = self.db.get_next_purchase_id()
            batch_id = f"{pid}-{datetime.now().strftime('%Y%m%d')}-B{datetime.now().strftime('%H%M')}"
            
            self.db.write_purchase({
                "purchase_id": purchase_id,
                "date": date_str,
                "product_id": pid,
                "batch_id": batch_id,
                "supplier": supplier,
                "qty": qty,
                "cost_per_unit": cost
            })
            
            messagebox.showinfo("✅ Purchase Saved!", 
                f"ID: {purchase_id}\nBatch: {batch_id}\nTotal: {DEFAULT_CURRENCY} {qty * cost:,.2f}")
            
            # Clear and refresh
            self.qty_entry.delete(0, 'end')
            self.cost_entry.delete(0, 'end')
            self.supplier_entry.delete(0, 'end')
            self.total_preview_lbl.configure(text=f"{DEFAULT_CURRENCY} 0")
            self._render_history()
            
        except ValueError:
            messagebox.showerror("Input Error", "Quantity must be a whole number and Cost must be a number!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
