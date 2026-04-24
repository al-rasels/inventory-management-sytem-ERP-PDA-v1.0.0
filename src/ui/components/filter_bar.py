import customtkinter as ctk
from src.core.config import COLORS

class FilterBar(ctk.CTkFrame):
    """Search and filter component."""
    
    def __init__(self, master, on_search_callback, categories: list = None, **kwargs):
        super().__init__(master, fg_color=COLORS["card"], corner_radius=10, height=50, **kwargs)
        self.pack_propagate(False)
        
        ctk.CTkLabel(self, text="🔍", font=ctk.CTkFont(size=16)).pack(side="left", padx=(15, 5))
        self.entry = ctk.CTkEntry(self, placeholder_text="Search...", border_width=0, fg_color="transparent")
        self.entry.pack(side="left", fill="x", expand=True, padx=5)
        self.entry.bind("<KeyRelease>", lambda e: on_search_callback(self.entry.get()))

        if categories:
            self.cat_combo = ctk.CTkComboBox(self, values=["All Categories"] + categories, 
                                             command=lambda v: on_search_callback(self.entry.get(), v))
            self.cat_combo.pack(side="right", padx=15)
