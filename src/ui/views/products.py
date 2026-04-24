import customtkinter as ctk
from src.core.config import COLORS, DEFAULT_CURRENCY
import tkinter.messagebox as messagebox

class ProductsView(ctk.CTkFrame):
    def __init__(self, master, db, im, app=None):
        super().__init__(master, fg_color="transparent")
        self.db = db
        self.im = im
        self.app = app
        self.all_products = None  # Cache for filtering
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(header, text="Product Management", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        
        self.add_btn = ctk.CTkButton(header, text="+ Add Product (F1)", fg_color=COLORS["success"],
                                      hover_color=COLORS["success_hover"], width=140,
                                      command=self._add_product)
        self.add_btn.pack(side="right", padx=5)

        # Filter bar
        filter_bar = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=10, height=50)
        filter_bar.pack(fill="x", pady=(0, 10))
        filter_bar.pack_propagate(False)

        ctk.CTkLabel(filter_bar, text="🔍", font=ctk.CTkFont(size=16)).pack(side="left", padx=(15, 5))
        self.search_entry = ctk.CTkEntry(filter_bar, placeholder_text="Search by SKU, Name, or Category...", 
                                          width=350, border_width=0, fg_color="transparent")
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self._on_search)

        # Category filter
        categories = self.db.execute_query("SELECT DISTINCT category FROM products ORDER BY category")
        cat_list = ["All Categories"] + categories['category'].tolist()
        self.cat_filter = ctk.CTkComboBox(filter_bar, values=cat_list, width=180, command=self._on_filter)
        self.cat_filter.set("All Categories")
        self.cat_filter.pack(side="right", padx=15)
        ctk.CTkLabel(filter_bar, text="Category:", text_color=COLORS["text_muted"]).pack(side="right")

        # Product count label
        self.count_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"])
        self.count_label.pack(anchor="w", pady=(0, 5))

        # Table
        self.table_container = ctk.CTkScrollableFrame(self, fg_color=COLORS["card"], corner_radius=10)
        self.table_container.pack(fill="both", expand=True)
        
        # Configure columns
        for i in range(7):
            self.table_container.columnconfigure(i, weight=1 if i == 1 else 0)

        self._load_and_render()

    def _load_and_render(self, search_term=None, category=None):
        """Load products and render the table."""
        query = """
            SELECT p.product_id, p.sku_code, p.name, p.category, p.unit, p.sell_price, p.cost_price, p.status,
                   (IFNULL(purch.total_in, 0) - IFNULL(sold.total_out, 0)) as current_stock
            FROM products p
            LEFT JOIN (SELECT product_id, SUM(qty) as total_in FROM purchases GROUP BY product_id) purch 
                ON p.product_id = purch.product_id
            LEFT JOIN (SELECT product_id, SUM(qty) as total_out FROM sales GROUP BY product_id) sold 
                ON p.product_id = sold.product_id
            WHERE 1=1
        """
        params = []
        
        if search_term:
            query += " AND (p.sku_code LIKE ? OR p.name LIKE ? OR p.category LIKE ?)"
            term = f"%{search_term}%"
            params.extend([term, term, term])
        
        if category and category != "All Categories":
            query += " AND p.category = ?"
            params.append(category)

        query += " ORDER BY p.product_id"
        df = self.db.execute_query(query, tuple(params))
        self.count_label.configure(text=f"Showing {len(df)} products")
        self._render_table(df)

    def _render_table(self, df):
        """Render the product table."""
        for widget in self.table_container.winfo_children():
            widget.destroy()

        headers = ["SKU", "Product Name", "Category", "Stock", "Sell Price", "Status", "Actions"]
        col_widths = [80, 200, 80, 70, 90, 90, 150]
        
        for i, h in enumerate(headers):
            lbl = ctk.CTkLabel(self.table_container, text=h, font=ctk.CTkFont(size=12, weight="bold"),
                              text_color=COLORS["text_muted"], width=col_widths[i])
            lbl.grid(row=0, column=i, padx=8, pady=(10, 8), sticky="w")

        # Divider
        ctk.CTkFrame(self.table_container, height=1, fg_color=COLORS["border"]).grid(
            row=1, column=0, columnspan=7, sticky="ew", padx=5)

        for idx, row in df.iterrows():
            r = idx + 2
            stock = int(row['current_stock'])
            
            # Stock color
            if stock <= 0:
                stock_color = COLORS["danger"]
                stock_text = f"⛔ {stock}"
            elif stock < 50:
                stock_color = COLORS["warning"]
                stock_text = f"⚠️ {stock}"
            else:
                stock_color = COLORS["success"]
                stock_text = f"✅ {stock}"
            
            # Status badge color
            status = row['status'] if row['status'] else 'Active'
            status_color = COLORS["success"] if status == 'Active' else COLORS["text_muted"]

            ctk.CTkLabel(self.table_container, text=row['sku_code'], font=ctk.CTkFont(size=11),
                        text_color=COLORS["accent"]).grid(row=r, column=0, padx=8, pady=4, sticky="w")
            ctk.CTkLabel(self.table_container, text=row['name'], font=ctk.CTkFont(size=11)).grid(
                row=r, column=1, padx=8, pady=4, sticky="w")
            ctk.CTkLabel(self.table_container, text=row['category'], font=ctk.CTkFont(size=11),
                        text_color=COLORS["text_secondary"]).grid(row=r, column=2, padx=8, pady=4, sticky="w")
            ctk.CTkLabel(self.table_container, text=stock_text, font=ctk.CTkFont(size=11),
                        text_color=stock_color).grid(row=r, column=3, padx=8, pady=4, sticky="w")
            ctk.CTkLabel(self.table_container, text=f"{DEFAULT_CURRENCY} {row['sell_price']:,.0f}",
                        font=ctk.CTkFont(size=11)).grid(row=r, column=4, padx=8, pady=4, sticky="w")
            ctk.CTkLabel(self.table_container, text=status, font=ctk.CTkFont(size=11),
                        text_color=status_color).grid(row=r, column=5, padx=8, pady=4, sticky="w")
            
            action_frame = ctk.CTkFrame(self.table_container, fg_color="transparent")
            action_frame.grid(row=r, column=6, padx=8, pady=4)

            ctk.CTkButton(action_frame, text="View", width=45, height=24, corner_radius=6,
                         fg_color=COLORS["border"], hover_color=COLORS["card_hover"],
                         font=ctk.CTkFont(size=10), 
                         command=lambda p=row: self._view_details(p)).pack(side="left", padx=1)

            ctk.CTkButton(action_frame, text="Edit", width=45, height=24, corner_radius=6,
                         fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                         font=ctk.CTkFont(size=10),
                         command=lambda p=row: self._edit_product(p)).pack(side="left", padx=1)

            ctk.CTkButton(action_frame, text="+ Cart", width=45, height=24, corner_radius=6,
                         fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
                         font=ctk.CTkFont(size=10),
                         command=lambda p=row: self._add_to_cart(p)).pack(side="left", padx=1)

    def _on_search(self, event=None):
        search_term = self.search_entry.get()
        category = self.cat_filter.get()
        self._load_and_render(search_term=search_term if search_term else None,
                              category=category if category != "All Categories" else None)

    def _on_filter(self, choice):
        search_term = self.search_entry.get()
        self._load_and_render(search_term=search_term if search_term else None,
                              category=choice if choice != "All Categories" else None)

    def _add_to_cart(self, prod):
        """Add product to the global cart without switching views. Respects stock and prevents duplicates."""
        if not self.app:
            return

        # Check if already in cart
        existing_item = next((item for item in self.app.cart if item['product_id'] == prod['product_id']), None)
        target_qty = (existing_item['qty'] + 1) if existing_item else 1

        # Check stock
        available, current = self.im.check_stock_available(prod['product_id'], target_qty)
        if not available:
            messagebox.showwarning("Out of Stock", f"Cannot add more! Only {int(current)} units available.")
            return

        if existing_item:
            existing_item['qty'] = target_qty
            existing_item['total'] = existing_item['qty'] * existing_item['price']
            messagebox.showinfo("Cart Updated", f"Increased {prod['name']} quantity to {target_qty}.")
        else:
            self.app.cart.append({
                "product_id": prod['product_id'],
                "name": prod['name'],
                "qty": 1,
                "price": prod['sell_price'],
                "total": prod['sell_price']
            })
            messagebox.showinfo("Added to Cart", f"Added {prod['name']} to cart.")


    def _add_product(self):
        """Basic add product dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Product")
        dialog.geometry("400x500")
        dialog.after(10, dialog.focus_get)
        dialog.transient(self.master)
        
        content = ctk.CTkFrame(dialog, fg_color=COLORS["card"], corner_radius=15)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(content, text="🆕 New Product", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        # Simple fields
        fields = ["SKU Code", "Product Name", "Category", "Unit", "Sell Price", "Cost Price"]
        entries = {}
        
        for f in fields:
            ctk.CTkLabel(content, text=f, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30)
            e = ctk.CTkEntry(content, width=300)
            e.pack(padx=30, pady=(0, 10))
            entries[f] = e

        def save():
            try:
                sku = entries["SKU Code"].get().strip()
                name = entries["Product Name"].get().strip()
                
                if not sku or not name: raise ValueError("SKU and Name are required")
                
                # Check if SKU exists
                exists = self.db.execute_query("SELECT 1 FROM products WHERE sku_code = ?", (sku,))
                if not exists.empty:
                    messagebox.showerror("Error", "SKU Code already exists!")
                    return

                # Generate Product ID
                res = self.db.execute_query("SELECT COUNT(*) as count FROM products")
                new_id = f"PROD-{res.iloc[0]['count'] + 1001}"

                self.db.execute_write(
                    "INSERT INTO products (product_id, sku_code, name, category, unit, sell_price, cost_price, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (new_id, sku, name, entries["Category"].get(), entries["Unit"].get(), 
                     float(entries["Sell Price"].get()), float(entries["Cost Price"].get()), "Active")
                )
                messagebox.showinfo("Success", f"Product {name} added successfully!")
                dialog.destroy()
                self._load_and_render()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {str(e)}")

        ctk.CTkButton(content, text="Save Product", command=save, fg_color=COLORS["success"]).pack(pady=20)

    def _view_details(self, prod):
        """Show product details in a popup."""
        # Fix: Store reference to prevent disappearing
        self.detail_popup = ctk.CTkToplevel(self)
        popup = self.detail_popup
        popup.title(f"Product Details - {prod['sku_code']}")
        popup.geometry("400x520")
        popup.after(10, popup.focus_get)
        popup.transient(self.master)

        # Center popup
        x = self.winfo_screenwidth() // 2 - 200
        y = self.winfo_screenheight() // 2 - 260
        popup.geometry(f"400x520+{x}+{y}")

        content = ctk.CTkFrame(popup, fg_color=COLORS["card"], corner_radius=15)
        content.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(content, text="Product Information", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 15))
        
        details = [
            ("ID", prod['product_id']),
            ("SKU", prod['sku_code']),
            ("Name", prod['name']),
            ("Category", prod['category']),
            ("Unit", prod['unit']),
            ("Sell Price", f"{DEFAULT_CURRENCY} {prod['sell_price']:,.2f}"),
            ("Cost Price", f"{DEFAULT_CURRENCY} {prod['cost_price']:,.2f}"),
            ("Status", prod['status']),
            ("Current Stock", str(int(prod['current_stock'])))
        ]

        for label, value in details:
            row = ctk.CTkFrame(content, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(row, text=f"{label}:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text_muted"]).pack(side="left")
            ctk.CTkLabel(row, text=str(value), font=ctk.CTkFont(size=12)).pack(side="right")

        ctk.CTkButton(content, text="Close", command=popup.destroy, fg_color=COLORS["border"]).pack(pady=30)

    def _edit_product(self, prod):
        """Show edit product dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit Product - {prod['sku_code']}")
        dialog.geometry("400x550")
        dialog.after(10, dialog.focus_get)
        dialog.transient(self.master)
        
        # Center popup
        x = self.winfo_screenwidth() // 2 - 200
        y = self.winfo_screenheight() // 2 - 275
        dialog.geometry(f"400x550+{x}+{y}")

        content = ctk.CTkFrame(dialog, fg_color=COLORS["card"], corner_radius=15)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(content, text="📝 Edit Product", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        fields = [
            ("SKU Code", "sku_code"),
            ("Product Name", "name"),
            ("Category", "category"),
            ("Unit", "unit"),
            ("Sell Price", "sell_price"),
            ("Cost Price", "cost_price")
        ]
        entries = {}
        
        for label, key in fields:
            ctk.CTkLabel(content, text=label, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30)
            e = ctk.CTkEntry(content, width=300)
            e.insert(0, str(prod[key]))
            e.pack(padx=30, pady=(0, 10))
            entries[key] = e

        def save():
            try:
                sku = entries["sku_code"].get().strip()
                name = entries["name"].get().strip()
                
                if not sku or not name: raise ValueError("SKU and Name are required")
                
                # Check if SKU exists (but not for this product)
                exists = self.db.execute_query(
                    "SELECT 1 FROM products WHERE sku_code = ? AND product_id != ?", 
                    (sku, prod['product_id'])
                )
                if not exists.empty:
                    messagebox.showerror("Error", "SKU Code already exists for another product!")
                    return

                self.db.execute_write(
                    """UPDATE products 
                       SET sku_code = ?, name = ?, category = ?, unit = ?, sell_price = ?, cost_price = ? 
                       WHERE product_id = ?""",
                    (sku, name, entries["category"].get(), entries["unit"].get(), 
                     float(entries["sell_price"].get()), float(entries["cost_price"].get()), 
                     prod['product_id'])
                )
                messagebox.showinfo("Success", f"Product {name} updated successfully!")
                dialog.destroy()
                self._load_and_render()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {str(e)}")

        ctk.CTkButton(content, text="Save Changes", command=save, fg_color=COLORS["success"]).pack(pady=20)
