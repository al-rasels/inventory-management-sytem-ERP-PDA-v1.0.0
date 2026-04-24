import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import customtkinter as ctk
from src.core.database import DatabaseEngine
from src.services.auth_service import AuthService
from src.ui.app import ERPApp
from src.core.config import COLORS, THEME, COLOR_THEME, APP_VERSION
from src.repositories.user_repository import UserRepository
import threading

class LoginScreen(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sun Warehouse ERP - Login")
        self.geometry("450x550")
        self.resizable(False, False)
        
        self.db = DatabaseEngine()
        self.user_repo = UserRepository(self.db)
        self.auth_service = AuthService(self.user_repo)

        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 225
        y = (self.winfo_screenheight() // 2) - 275
        self.geometry(f"450x550+{x}+{y}")
        
        # Background
        self.configure(fg_color=COLORS["bg_dark"])

        # Main card
        self.card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=20, width=380, height=480)
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)

        # Logo
        ctk.CTkLabel(self.card, text="☀", font=ctk.CTkFont(size=48)).pack(pady=(30, 5))
        ctk.CTkLabel(self.card, text="SUN WAREHOUSE", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COLORS["accent_light"]).pack()
        ctk.CTkLabel(self.card, text=f"Enterprise Resource Planning  •  v{APP_VERSION}",
                     font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(pady=(0, 25))

        # Username
        ctk.CTkLabel(self.card, text="Username", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text_secondary"]).pack(padx=40, anchor="w")
        self.username_entry = ctk.CTkEntry(self.card, placeholder_text="Enter username", 
                                           width=300, height=40, corner_radius=10)
        self.username_entry.pack(padx=40, pady=(3, 12))

        # Password
        ctk.CTkLabel(self.card, text="Password", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text_secondary"]).pack(padx=40, anchor="w")
        self.password_entry = ctk.CTkEntry(self.card, placeholder_text="Enter password", show="●",
                                           width=300, height=40, corner_radius=10)
        self.password_entry.pack(padx=40, pady=(3, 20))
        self.password_entry.bind("<Return>", lambda e: self.login())

        # Login button
        self.login_button = ctk.CTkButton(self.card, text="Login →", command=self.login,
                                           width=300, height=42, corner_radius=10,
                                           fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                           font=ctk.CTkFont(size=14, weight="bold"))
        self.login_button.pack(padx=40)

        # Status label
        self.status_label = ctk.CTkLabel(self.card, text="", font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=15)

        # Focus username
        self.username_entry.focus_set()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            self.status_label.configure(text="⚠️ Please enter both fields", text_color=COLORS["warning"])
            return

        self.login_button.configure(state="disabled", text="Authenticating...")
        self.status_label.configure(text="🔄 Verifying credentials...", text_color=COLORS["text_muted"])
        self.update()
        
        try:
            result = self.auth_service.login(username, password)
            if result.success:
                user = result.user
                self.status_label.configure(text="✅ Login successful! Loading...", text_color=COLORS["success"])
                self.update()
                
                # Sync in a thread-safe way
                self.status_label.configure(text="🔄 Syncing database from Excel...")
                self.update()
                try:
                    from src.repositories.sync_manager import SyncManager
                    SyncManager(self.db).sync_all()
                except Exception as e:
                    self.status_label.configure(text=f"⚠️ Sync warning: {str(e)[:50]}", text_color=COLORS["warning"])
                    self.update()

                self.destroy()
                app = ERPApp(user)
                app.mainloop()
            else:
                raise Exception("Authentication failed")
        except Exception as e:
            self.status_label.configure(text=f"❌ {str(e)}", text_color=COLORS["danger"])
            self.login_button.configure(state="normal", text="Login →")
            self.password_entry.delete(0, 'end')
            self.password_entry.focus_set()

if __name__ == "__main__":
    ctk.set_appearance_mode(THEME)
    ctk.set_default_color_theme(COLOR_THEME)
    login = LoginScreen()
    login.mainloop()
