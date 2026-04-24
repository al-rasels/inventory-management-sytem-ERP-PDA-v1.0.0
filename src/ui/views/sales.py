import customtkinter as ctk
from src.core.config import COLORS, DEFAULT_CURRENCY, INVOICE_DIR
from src.core.inventory_manager import InventoryManager
from src.utils.pdf_gen import InvoiceGenerator
from datetime import datetime
import tkinter.messagebox as messagebox

class SalesView(ctk.CTkFrame):
    def __init__(self, master, db, app=None):
        super().__init__(master, fg_color="transparent")
        self.db = db
        self.app = app
        self.im = InventoryManager(db)
        self.pdf = InvoiceGenerator(output_dir=INVOICE_DIR)
        
        # Use app's cart if available
        if app and hasattr(app, 'cart'):
            self.cart = app.cart
        else:
            self.cart = []
        
        # Title
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="Point of Sale", font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        ctk.CTkLabel(header, text="Scan or Search to Add Items", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_muted"]).pack(side="left", padx=20)

        # Main layout
        self.grid_columnconfigure(0, weight=3)
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        # ─── Left: Search + Cart ───
        left = ctk.CTkFrame(main, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Customer + Search bar
        top_bar = ctk.CTkFrame(left, fg_color=COLORS["card"], corner_radius=15, height=60)
        top_bar.pack(fill="x", pady=(0, 15))
        top_bar.pack_propagate(False)
        
        ctk.CTkLabel(top_bar, text="👤", font=ctk.CTkFont(size=20)).pack(side="left", padx=(20, 5))
        self.customer_entry = ctk.CTkEntry(top_bar, placeholder_text="Customer name (optional)", 
                                           width=250, height=35, border_width=1, fg_color="transparent")
        self.customer_entry.pack(side="left", padx=10)

        search_frame = ctk.CTkFrame(left, fg_color=COLORS["card"], corner_radius=10, height=50)
        search_frame.pack(fill="x", pady=(0, 10))
        search_frame.pack_propagate(False)
        
        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=16)).pack(side="left", padx=(15, 5))
        self.search_bar = ctk.CTkEntry(search_frame, placeholder_text="Type SKU, product name, or scan barcode...",
                                       border_width=0, fg_color="transparent")
        self.search_bar.pack(side="left", fill="x", expand=True, padx=5)
        self.search_bar.bind("<Return>", self.add_to_cart)
        
        self.quick_add_btn = ctk.CTkButton(search_frame, text="+ Add Item", width=80, height=30, 
                                           fg_color=COLORS["accent"], command=self.add_to_cart)
        self.quick_add_btn.pack(side="right", padx=10)
        
        self.search_bar.focus_set()

        # Cart table
        self.cart_frame = ctk.CTkScrollableFrame(left, fg_color=COLORS["card"], corner_radius=10,
                                                  label_text="  Cart Items")
        self.cart_frame.pack(fill="both", expand=True)

        # ─── Right: Summary ───
        right = ctk.CTkFrame(main, fg_color=COLORS["card"], corner_radius=12, width=280)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_propagate(False)
        
        ctk.CTkLabel(right, text="💳 Sale Summary", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 15))
        ctk.CTkFrame(right, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=15)

        self.items_count_lbl = self._summary_row(right, "Items", "0")
        self.subtotal_lbl = self._summary_row(right, "Subtotal", f"{DEFAULT_CURRENCY} 0")
        
        # Discount input
        disc_frame = ctk.CTkFrame(right, fg_color="transparent")
        disc_frame.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(disc_frame, text="Discount %", font=ctk.CTkFont(size=13)).pack(side="left")
        self.discount_entry = ctk.CTkEntry(disc_frame, width=60, placeholder_text="0", justify="center")
        self.discount_entry.pack(side="right")
        self.discount_entry.bind("<KeyRelease>", lambda e: self.update_summary())

        self.discount_amt_lbl = self._summary_row(right, "Discount", f"- {DEFAULT_CURRENCY} 0")
        
        ctk.CTkFrame(right, height=2, fg_color=COLORS["accent"]).pack(fill="x", padx=15, pady=5)
        self.grand_total_lbl = self._summary_row(right, "GRAND TOTAL", f"{DEFAULT_CURRENCY} 0", 
                                                  size=20, color=COLORS["accent"])
        self.profit_lbl = self._summary_row(right, "Est. Profit", f"{DEFAULT_CURRENCY} 0", 
                                             size=13, color=COLORS["success"])

        # Buttons
        btn_frame = ctk.CTkFrame(right, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=15, pady=15)

        self.complete_btn = ctk.CTkButton(
            btn_frame, text="✅ COMPLETE SALE", height=45,
            fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
            font=ctk.CTkFont(size=14, weight="bold"), command=self.complete_sale
        )
        self.complete_btn.pack(fill="x", pady=(0, 8))

        self.clear_btn = ctk.CTkButton(
            btn_frame, text="🗑️ Clear Cart", height=32,
            fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            font=ctk.CTkFont(size=12), command=self.clear_cart
        )
        self.clear_btn.pack(fill="x")

        # Render existing cart items if any
        if self.cart:
            self.render_cart()
            self.update_summary()

    def _summary_row(self, parent, label, value, size=14, color=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=size), text_color=COLORS["text_muted"]).pack(side="left")
        lbl = ctk.CTkLabel(frame, text=value, font=ctk.CTkFont(size=size, weight="bold"), text_color=color)
        lbl.pack(side="right")
        return lbl

    def add_to_cart(self, event=None):
        search_val = self.search_bar.get().strip()
        if not search_val:
            return
        
        # More flexible search: Case-insensitive partial match for SKU, ID, or Name
        query = """
            SELECT * FROM products 
            WHERE LOWER(sku_code) = LOWER(?) 
               OR LOWER(product_id) = LOWER(?) 
               OR name LIKE ?
        """
        df = self.db.execute_query(query, (search_val, search_val, f"%{search_val}%"))
        
        if df.empty:
            messagebox.showwarning("Not Found", f"No product matches '{search_val}'")
            return
        
        prod = df.iloc[0]
        self.search_bar.delete(0, 'end')
        
        # Check if already in cart
        existing_item = next((item for item in self.cart if item['product_id'] == prod['product_id']), None)
        target_qty = (existing_item['qty'] + 1) if existing_item else 1

        # Check stock
        available, current = self.im.check_stock_available(prod['product_id'], target_qty)
        if not available:
            messagebox.showwarning("Out of Stock", f"Cannot add more! Only {int(current)} units available.")
            return

        if existing_item:
            existing_item['qty'] = target_qty
            existing_item['total'] = existing_item['qty'] * existing_item['price']
        else:
            self.cart.append({
                "product_id": prod['product_id'],
                "name": prod['name'],
                "qty": 1,
                "price": prod['sell_price'],
                "total": prod['sell_price']
            })
        
        self.render_cart()
        self.update_summary()


    def render_cart(self):
        for widget in self.cart_frame.winfo_children():
            widget.destroy()

        if not self.cart:
            ctk.CTkLabel(self.cart_frame, text="Cart is empty. Search and add products above.",
                        text_color=COLORS["text_muted"], font=ctk.CTkFont(size=13)).pack(pady=40)
            return
            
        # Header
        hdr = ctk.CTkFrame(self.cart_frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(5, 5))
        for text, w in [("Product", 200), ("Qty", 70), ("Price", 90), ("Total", 90), ("", 30)]:
            ctk.CTkLabel(hdr, text=text, width=w, font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=COLORS["text_muted"]).pack(side="left", padx=5)

        for i, item in enumerate(self.cart):
            row = ctk.CTkFrame(self.cart_frame, fg_color=COLORS["card_hover"] if i % 2 == 0 else "transparent",
                               corner_radius=6, height=45)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=item['name'], width=200, anchor="w", 
                        font=ctk.CTkFont(size=12)).pack(side="left", padx=5)

            # Qty Entry
            qty_entry = ctk.CTkEntry(row, width=60, height=28, justify="center")
            qty_entry.insert(0, str(item['qty']))
            qty_entry.pack(side="left", padx=5)
            qty_entry.bind("<KeyRelease>", lambda e, idx=i, entry=qty_entry: self._update_item(idx, entry, "qty"))

            # Price Entry
            price_entry = ctk.CTkEntry(row, width=80, height=28, justify="center")
            price_entry.insert(0, str(item['price']))
            price_entry.pack(side="left", padx=5)
            price_entry.bind("<KeyRelease>", lambda e, idx=i, entry=price_entry: self._update_item(idx, entry, "price"))
            
            total_lbl = ctk.CTkLabel(row, text=f"{DEFAULT_CURRENCY}{item['total']:,.0f}", width=80,
                                     font=ctk.CTkFont(size=12, weight="bold"))
            total_lbl.pack(side="left", padx=5)
            item['total_lbl'] = total_lbl
            
            ctk.CTkButton(row, text="✕", width=26, height=26, corner_radius=4,
                         fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                         font=ctk.CTkFont(size=11), command=lambda idx=i: self.remove_item(idx)).pack(side="right", padx=8)

    def _update_item(self, idx, entry, field):
        """Update cart item field dynamically with stock validation."""
        try:
            val = entry.get()
            if not val: return
            
            item = self.cart[idx]
            if field == "qty":
                new_qty = int(val) if val.isdigit() else item['qty']
                if new_qty <= 0: return
                
                # Stock validation
                available, current = self.im.check_stock_available(item['product_id'], new_qty)
                if not available:
                    # Visual feedback: reset entry to last known good value or show warning
                    entry.configure(text_color=COLORS["danger"])
                    return
                else:
                    entry.configure(text_color=COLORS["text"])
                item['qty'] = new_qty
            else:
                item['price'] = float(val) if val.replace('.','',1).isdigit() else item['price']

            item['total'] = item['qty'] * item['price']
            
            if 'total_lbl' in item:
                item['total_lbl'].configure(text=f"{DEFAULT_CURRENCY}{item['total']:,.0f}")
            
            self.update_summary()
        except:
            pass

    def remove_item(self, idx):
        self.cart.pop(idx)
        self.render_cart()
        self.update_summary()

    def clear_cart(self):
        self.cart.clear()
        self.render_cart()
        self.update_summary()

    def update_summary(self):
        subtotal = sum(item['total'] for item in self.cart)
        items_count = sum(item['qty'] for item in self.cart)
        
        try:
            disc_pct = float(self.discount_entry.get() or 0)
        except ValueError:
            disc_pct = 0
        
        discount_amt = subtotal * (disc_pct / 100)
        grand_total = subtotal - discount_amt

        self.items_count_lbl.configure(text=str(items_count))
        self.subtotal_lbl.configure(text=f"{DEFAULT_CURRENCY} {subtotal:,.0f}")
        self.discount_amt_lbl.configure(text=f"- {DEFAULT_CURRENCY} {discount_amt:,.0f}")
        self.grand_total_lbl.configure(text=f"{DEFAULT_CURRENCY} {grand_total:,.0f}")

        # Estimate profit
        est_profit = 0
        for item in self.cart:
            cogs, _ = self.im.calculate_fifo_cogs(item['product_id'], item['qty'])
            est_profit += item['total'] - (cogs or 0)
        est_profit -= discount_amt
        self.profit_lbl.configure(text=f"{DEFAULT_CURRENCY} {est_profit:,.0f}")

    def complete_sale(self):
        if not self.cart:
            messagebox.showinfo("Empty Cart", "Add items to the cart first!")
            return
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        customer = self.customer_entry.get().strip() or "Walk-in Customer"
        
        try:
            disc_pct = float(self.discount_entry.get() or 0)
        except ValueError:
            disc_pct = 0
        
        try:
            for item in self.cart:
                sales_id = self.db.get_next_sale_id()
                total_cogs, _ = self.im.calculate_fifo_cogs(item['product_id'], item['qty'])
                
                if total_cogs is None:
                    messagebox.showerror("Error", f"Cannot calculate cost for {item['name']}!")
                    return
                
                item_discount = item['total'] * (disc_pct / 100)
                revenue = item['total'] - item_discount

                self.db.write_sale({
                    "sales_id": sales_id,
                    "date": date_str,
                    "product_id": item['product_id'],
                    "customer": customer,
                    "qty": item['qty'],
                    "sell_price": item['price'],
                    "discount": item_discount,
                    "revenue": revenue,
                    "cogs": total_cogs,
                    "profit": revenue - total_cogs
                })
            
            # Calculate totals for the message
            subtotal = sum(item['total'] for item in self.cart)
            discount_amt = subtotal * (disc_pct / 100)
            grand_total = subtotal - discount_amt
            
            messagebox.showinfo("✅ Sale Complete!", 
                f"Sale recorded successfully!\nCustomer: {customer}\nTotal: {DEFAULT_CURRENCY} {grand_total:,.0f}")
            
            self.clear_cart()
            self.customer_entry.delete(0, 'end')
            self.discount_entry.delete(0, 'end')
            
        except Exception as e:
            messagebox.showerror("Critical Error", str(e))
