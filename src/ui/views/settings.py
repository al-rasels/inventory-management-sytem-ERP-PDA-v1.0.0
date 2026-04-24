import customtkinter as ctk
from src.core.config import COLORS, BACKUP_DIR, MAX_BACKUP_FILES
from src.utils.export_import import DataExporter, DataImporter
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
import os
import glob

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, db, auth_service, sync_manager=None, 
                 report_service=None, backup_service=None, user_data=None):
        super().__init__(master, fg_color="transparent")
        self.db = db
        self.auth_service = auth_service
        self.sync_manager = sync_manager
        self.report_service = report_service
        self.backup_service = backup_service
        self.user_data = user_data or {"username": "admin"}
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="System Settings", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")

        # Tabs
        self.tabs = ctk.CTkTabview(self, fg_color=COLORS["card"], corner_radius=12,
                                    segmented_button_fg_color=COLORS["sidebar"],
                                    segmented_button_selected_color=COLORS["accent"])
        self.tabs.pack(fill="both", expand=True)

        self.tabs.add("⚙️ General")
        self.tabs.add("👥 Users")
        self.tabs.add("🗄️ Database")
        self.tabs.add("📦 Export / Import")

        self._build_general(self.tabs.tab("⚙️ General"))
        self._build_users(self.tabs.tab("👥 Users"))
        self._build_database(self.tabs.tab("🗄️ Database"))
        self._build_export_import(self.tabs.tab("📦 Export / Import"))

    # ═══════════════════════════════════════════
    # TAB 1: General
    # ═══════════════════════════════════════════
    def _build_general(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Appearance
        ctk.CTkLabel(scroll, text="Appearance", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=(10, 5), padx=15, anchor="w")
        self.theme_switch = self._toggle(scroll, "Dark Mode", ctk.get_appearance_mode() == "Dark", self._toggle_theme)

        # Safety
        ctk.CTkFrame(scroll, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(scroll, text="Safety", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=5, padx=15, anchor="w")
        self._toggle(scroll, "Auto-Backup before every write", True)
        self._toggle(scroll, "Audit Logging", True)

        # Password Change
        ctk.CTkFrame(scroll, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(scroll, text="🔑 Change Password", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=5, padx=15, anchor="w")

        pw_card = ctk.CTkFrame(scroll, fg_color=COLORS["card_hover"], corner_radius=8)
        pw_card.pack(fill="x", padx=15, pady=5)

        pw_grid = ctk.CTkFrame(pw_card, fg_color="transparent")
        pw_grid.pack(fill="x", padx=15, pady=10)
        pw_grid.columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(pw_grid, text="Current Password:", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w")
        self.old_pw = ctk.CTkEntry(pw_grid, show="●", height=30)
        self.old_pw.grid(row=1, column=0, padx=3, sticky="ew")

        ctk.CTkLabel(pw_grid, text="New Password:", font=ctk.CTkFont(size=11)).grid(row=0, column=1, sticky="w")
        self.new_pw = ctk.CTkEntry(pw_grid, show="●", height=30)
        self.new_pw.grid(row=1, column=1, padx=3, sticky="ew")

        ctk.CTkLabel(pw_grid, text="Confirm New:", font=ctk.CTkFont(size=11)).grid(row=0, column=2, sticky="w")
        self.confirm_pw = ctk.CTkEntry(pw_grid, show="●", height=30)
        self.confirm_pw.grid(row=1, column=2, padx=3, sticky="ew")

        ctk.CTkButton(pw_card, text="Update Password", fg_color=COLORS["accent"],
                     hover_color=COLORS["accent_hover"], height=32,
                     command=self._change_password).pack(padx=15, pady=(5, 10), anchor="e")

        # Backup info
        ctk.CTkFrame(scroll, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(scroll, text="Backup Management", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=5, padx=15, anchor="w")

        backup_count, backup_size_mb = 0, 0
        if self.backup_service:
            backup_count, backup_size_mb = self.backup_service.get_backup_stats()

        info = ctk.CTkFrame(scroll, fg_color=COLORS["card_hover"], corner_radius=8)
        info.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(info, text=f"📁 {backup_count} backups  •  {backup_size_mb:.1f} MB total",
                    font=ctk.CTkFont(size=12), text_color=COLORS["text_secondary"]).pack(padx=15, pady=10, side="left")
        ctk.CTkButton(info, text="🧹 Cleanup Old", width=120, height=30,
                     fg_color=COLORS["warning"], hover_color=COLORS["warning_hover"],
                     command=self._cleanup_backups).pack(side="right", padx=15)

    # ═══════════════════════════════════════════
    # TAB 2: Users
    # ═══════════════════════════════════════════
    def _build_users(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text="User Management", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=(10, 10), padx=15, anchor="w")

        form = ctk.CTkFrame(scroll, fg_color=COLORS["card_hover"], corner_radius=10)
        form.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(form, text="➕ Add New User", font=ctk.CTkFont(size=14, weight="bold")).pack(
            pady=(10, 5), padx=15, anchor="w")

        fields = ctk.CTkFrame(form, fg_color="transparent")
        fields.pack(fill="x", padx=15, pady=5)
        fields.columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(fields, text="Username:", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w")
        self.new_user = ctk.CTkEntry(fields, placeholder_text="username", height=30)
        self.new_user.grid(row=1, column=0, padx=3, sticky="ew")

        ctk.CTkLabel(fields, text="Full Name:", font=ctk.CTkFont(size=11)).grid(row=0, column=1, sticky="w")
        self.new_name = ctk.CTkEntry(fields, placeholder_text="Full Name", height=30)
        self.new_name.grid(row=1, column=1, padx=3, sticky="ew")

        ctk.CTkLabel(fields, text="Password:", font=ctk.CTkFont(size=11)).grid(row=0, column=2, sticky="w")
        self.new_pass = ctk.CTkEntry(fields, placeholder_text="password", show="*", height=30)
        self.new_pass.grid(row=1, column=2, padx=3, sticky="ew")

        ctk.CTkLabel(fields, text="Role:", font=ctk.CTkFont(size=11)).grid(row=0, column=3, sticky="w")
        self.new_role = ctk.CTkComboBox(fields, values=["Admin", "Manager", "Cashier"], height=30, width=100)
        self.new_role.set("Cashier")
        self.new_role.grid(row=1, column=3, padx=3, sticky="ew")

        ctk.CTkButton(form, text="Create User", fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
                     height=32, command=self._create_user).pack(padx=15, pady=10, anchor="e")

        ctk.CTkFrame(scroll, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(scroll, text="Existing Users", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=15, anchor="w")

        self.user_list = ctk.CTkFrame(scroll, fg_color="transparent")
        self.user_list.pack(fill="x", padx=15, pady=5)
        self._refresh_users()

    # ═══════════════════════════════════════════
    # TAB 3: Database
    # ═══════════════════════════════════════════
    def _build_database(self, parent):
        ctk.CTkLabel(parent, text="Database Management", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=(10, 10), padx=15, anchor="w")

        info_card = ctk.CTkFrame(parent, fg_color=COLORS["card_hover"], corner_radius=10)
        info_card.pack(fill="x", padx=15, pady=5)

        prod_count = self.db.execute_query("SELECT COUNT(*) as c FROM products").iloc[0]['c']
        sale_count = self.db.execute_query("SELECT COUNT(*) as c FROM sales").iloc[0]['c']
        pur_count = self.db.execute_query("SELECT COUNT(*) as c FROM purchases").iloc[0]['c']

        stats = f"📦 {int(prod_count)} Products  •  🧾 {int(sale_count)} Sales  •  🚚 {int(pur_count)} Purchases"
        ctk.CTkLabel(info_card, text=stats, font=ctk.CTkFont(size=13),
                    text_color=COLORS["text_secondary"]).pack(padx=15, pady=12)

        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(actions, text="🔄 Sync Excel -> SQLite", height=38, width=200,
                     fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                     command=self._resync).pack(side="left", padx=5)
        
        ctk.CTkButton(actions, text="💾 Sync SQLite -> Excel", height=38, width=200,
                     fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
                     command=self._sync_to_excel).pack(side="left", padx=5)

        ctk.CTkButton(actions, text="🗑️ Reset Cache", height=38, width=150,
                     fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                     command=self._reset_cache).pack(side="left", padx=5)

    # ═══════════════════════════════════════════
    # TAB 4: Export / Import
    # ═══════════════════════════════════════════
    def _build_export_import(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # --- EXPORT SECTION ---
        ctk.CTkLabel(scroll, text="📤 Export Data", font=ctk.CTkFont(size=18, weight="bold")).pack(
            pady=(10, 5), padx=15, anchor="w")
        ctk.CTkLabel(scroll, text="Export your data for reports, analysis, or migration to another computer.",
                    font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(padx=15, anchor="w")

        # Full system migration
        migrate_card = ctk.CTkFrame(scroll, fg_color=COLORS["card_hover"], corner_radius=10)
        migrate_card.pack(fill="x", padx=15, pady=8)
        left = ctk.CTkFrame(migrate_card, fg_color="transparent")
        left.pack(side="left", padx=15, pady=12)
        ctk.CTkLabel(left, text="🚚 Full System Migration", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left, text="Creates a ZIP with Excel DB + SQLite + Invoices + Backups",
                    font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(anchor="w")
        ctk.CTkButton(migrate_card, text="Export ZIP", width=120, height=34,
                     fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                     command=self._export_migration).pack(side="right", padx=15)

        # Excel report
        report_card = ctk.CTkFrame(scroll, fg_color=COLORS["card_hover"], corner_radius=10)
        report_card.pack(fill="x", padx=15, pady=4)
        left2 = ctk.CTkFrame(report_card, fg_color="transparent")
        left2.pack(side="left", padx=15, pady=12)
        ctk.CTkLabel(left2, text="📊 Excel Report", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left2, text="Multi-sheet report: Products, Sales, Purchases, Inventory",
                    font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(anchor="w")
        ctk.CTkButton(report_card, text="Export .xlsx", width=120, height=34,
                     fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
                     command=self._export_excel).pack(side="right", padx=15)

        # CSV exports
        csv_card = ctk.CTkFrame(scroll, fg_color=COLORS["card_hover"], corner_radius=10)
        csv_card.pack(fill="x", padx=15, pady=4)
        left3 = ctk.CTkFrame(csv_card, fg_color="transparent")
        left3.pack(side="left", padx=15, pady=12)
        ctk.CTkLabel(left3, text="📋 CSV Export", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left3, text="Individual table exports for spreadsheets or data analysis",
                    font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(anchor="w")
        btn_row = ctk.CTkFrame(csv_card, fg_color="transparent")
        btn_row.pack(side="right", padx=15)
        for table in ["products", "sales", "purchases", "inventory"]:
            ctk.CTkButton(btn_row, text=table.capitalize(), width=80, height=28,
                         fg_color=COLORS["border"], hover_color=COLORS["card_hover"],
                         font=ctk.CTkFont(size=11),
                         command=lambda t=table: self._export_csv(t)).pack(side="left", padx=2)

        # --- IMPORT SECTION ---
        ctk.CTkFrame(scroll, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(scroll, text="📥 Import Data", font=ctk.CTkFont(size=18, weight="bold")).pack(
            pady=(0, 5), padx=15, anchor="w")
        ctk.CTkLabel(scroll, text="Restore from a migration archive or import CSV data.",
                    font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(padx=15, anchor="w")

        # Import migration ZIP
        imp_card = ctk.CTkFrame(scroll, fg_color=COLORS["card_hover"], corner_radius=10)
        imp_card.pack(fill="x", padx=15, pady=8)
        left4 = ctk.CTkFrame(imp_card, fg_color="transparent")
        left4.pack(side="left", padx=15, pady=12)
        ctk.CTkLabel(left4, text="🚚 Restore from Migration ZIP", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left4, text="Replaces current data with the contents of a migration archive",
                    font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(anchor="w")
        ctk.CTkButton(imp_card, text="Import ZIP", width=120, height=34,
                     fg_color=COLORS["warning"], hover_color=COLORS["warning_hover"],
                     command=self._import_migration).pack(side="right", padx=15)

        # Import CSV
        csv_imp = ctk.CTkFrame(scroll, fg_color=COLORS["card_hover"], corner_radius=10)
        csv_imp.pack(fill="x", padx=15, pady=4)
        left5 = ctk.CTkFrame(csv_imp, fg_color="transparent")
        left5.pack(side="left", padx=15, pady=12)
        ctk.CTkLabel(left5, text="📋 Import CSV into Table", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left5, text="Append rows from a CSV file into products, sales, or purchases",
                    font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(anchor="w")

        imp_btns = ctk.CTkFrame(csv_imp, fg_color="transparent")
        imp_btns.pack(side="right", padx=15)
        for table in ["products", "sales", "purchases"]:
            ctk.CTkButton(imp_btns, text=table.capitalize(), width=80, height=28,
                         fg_color=COLORS["border"], hover_color=COLORS["card_hover"],
                         font=ctk.CTkFont(size=11),
                         command=lambda t=table: self._import_csv(t)).pack(side="left", padx=2)

    # ═══════════════════════════════════════════
    # ACTION HANDLERS
    # ═══════════════════════════════════════════
    def _toggle(self, parent, text, default, command=None):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["card_hover"], corner_radius=8)
        frame.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(frame, text=text, font=ctk.CTkFont(size=13)).pack(side="left", padx=15, pady=8)
        switch = ctk.CTkSwitch(frame, text="", command=command)
        if default:
            switch.select()
        switch.pack(side="right", padx=15)
        return switch

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "light" if current == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)

    def _change_password(self):
        old = self.old_pw.get()
        new = self.new_pw.get()
        confirm = self.confirm_pw.get()

        if not old or not new or not confirm:
            messagebox.showwarning("Incomplete", "All password fields are required!")
            return
        if new != confirm:
            messagebox.showerror("Mismatch", "New password and confirmation don't match!")
            return
        if len(new) < 4:
            messagebox.showwarning("Too Short", "Password must be at least 4 characters!")
            return

        try:
            self.auth_service.change_password(self.user_data["username"], old, new)
            messagebox.showinfo("✅ Success", "Password changed successfully")
            self.old_pw.delete(0, 'end')
            self.new_pw.delete(0, 'end')
            self.confirm_pw.delete(0, 'end')
        except Exception as e:
            messagebox.showerror("Failed", str(e))

    def _cleanup_backups(self):
        if self.backup_service:
            deleted = self.backup_service.cleanup_old_backups(keep=5)
            if deleted > 0:
                messagebox.showinfo("Cleanup Done", f"Removed {deleted} old backups. Kept the 5 most recent.")
            else:
                messagebox.showinfo("Info", "Backups are already within limits.")
        else:
            messagebox.showerror("Error", "BackupService not initialized")

    def _create_user(self):
        username = self.new_user.get().strip()
        full_name = self.new_name.get().strip()
        password = self.new_pass.get()
        role = self.new_role.get()

        if not username or not full_name or not password:
            messagebox.showwarning("Incomplete", "All fields are required!")
            return

        try:
            self.auth_service.create_user(username, full_name, password, role)
            messagebox.showinfo("✅ User Created", f"User '{username}' created as {role}")
            self.new_user.delete(0, 'end')
            self.new_name.delete(0, 'end')
            self.new_pass.delete(0, 'end')
            self._refresh_users()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _refresh_users(self):
        for w in self.user_list.winfo_children():
            w.destroy()
        
        df = self.auth_service.list_users()
        for _, row in df.iterrows():
            card = ctk.CTkFrame(self.user_list, fg_color=COLORS["card_hover"], corner_radius=6)
            card.pack(fill="x", pady=2)
            ctk.CTkLabel(card, text=f"👤 {row['full_name']}", font=ctk.CTkFont(size=12, weight="bold")).pack(
                side="left", padx=15, pady=6)
            
            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="right", padx=10)
            ctk.CTkLabel(right, text=f"{row['role']}  •  @{row['username']}", font=ctk.CTkFont(size=11),
                        text_color=COLORS["text_muted"]).pack(side="left", padx=5)
            if row['username'] != 'admin':
                ctk.CTkButton(right, text="✕", width=26, height=24, corner_radius=4,
                             fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                             font=ctk.CTkFont(size=10),
                             command=lambda u=row['username']: self._delete_user(u)).pack(side="left", padx=3)

    def _delete_user(self, username):
        if messagebox.askyesno("Confirm", f"Delete user '{username}'?"):
            try:
                self.auth_service.delete_user(username)
                messagebox.showinfo("Deleted", f"User '{username}' deleted")
                self._refresh_users()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _resync(self):
        try:
            if self.sync_manager:
                self.sync_manager.sync_all_from_excel()
                messagebox.showinfo("✅ Sync Complete", "SQLite cache has been rebuilt from the Excel file.")
            else:
                raise Exception("SyncManager not initialized")
        except Exception as e:
            messagebox.showerror("Sync Failed", str(e))

    def _sync_to_excel(self):
        if self.sync_manager:
            success, msg = self.sync_manager.full_sync_to_excel()
            if success:
                messagebox.showinfo("✅ Sync Success", msg)
            else:
                messagebox.showerror("Sync Error", msg)
        else:
            messagebox.showerror("Error", "SyncManager not initialized")

    def _reset_cache(self):
        if messagebox.askyesno("Confirm Reset", "This will delete the SQLite cache and rebuild it from Excel.\nContinue?"):
            from src.core.config import SQLITE_DB_PATH
            if os.path.exists(SQLITE_DB_PATH):
                os.remove(SQLITE_DB_PATH)
            self.db._init_sqlite()
            if self.sync_manager:
                self.sync_manager.sync_all_from_excel()
            messagebox.showinfo("✅ Reset Complete", "Cache has been rebuilt.")

    # --- Export/Import handlers ---
    def _export_migration(self):
        try:
            if self.backup_service:
                path = self.backup_service.export_migration_zip()
                messagebox.showinfo("✅ Export Complete", f"Migration archive created:\n{path}")
            else:
                raise Exception("BackupService not initialized")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def _export_excel(self):
        try:
            if self.report_service:
                path = self.report_service.export_excel()
                messagebox.showinfo("✅ Report Generated", f"Excel report saved:\n{path}")
            else:
                raise Exception("ReportService not initialized")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def _export_csv(self, table):
        try:
            if self.report_service:
                path = self.report_service.export_csv(table)
                messagebox.showinfo("✅ CSV Exported", f"{table.capitalize()} exported to:\n{path}")
            else:
                raise Exception("ReportService not initialized")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def _import_migration(self):
        path = filedialog.askopenfilename(
            title="Select Migration ZIP",
            filetypes=[("ZIP files", "*.zip")]
        )
        if not path:
            return
        if messagebox.askyesno("⚠️ Confirm Import", 
            "This will replace your current data with the contents of the archive.\n"
            "A backup of your current data will be created first.\n\nContinue?"):
            if self.backup_service:
                success, msg = self.backup_service.import_migration_zip(path)
                if success:
                    messagebox.showinfo("✅ Import Complete", msg)
                else:
                    messagebox.showerror("Import Failed", msg)
            else:
                messagebox.showerror("Error", "BackupService not initialized")

    def _import_csv(self, table):
        path = filedialog.askopenfilename(
            title=f"Select CSV for {table}",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return
        success, msg, count = DataImporter.import_csv(self.db, path, table)
        if success:
            messagebox.showinfo("✅ Import Complete", msg)
        else:
            messagebox.showerror("Import Failed", msg)
