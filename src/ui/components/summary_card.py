import customtkinter as ctk
from src.core.config import COLORS

class SummaryCard(ctk.CTkFrame):
    """KPI summary card component."""
    
    def __init__(self, master, title: str, value: str, icon: str = "", color: str = None, **kwargs):
        super().__init__(master, fg_color=COLORS["card"], corner_radius=12, **kwargs)
        
        self.title_label = ctk.CTkLabel(self, text=f"{icon} {title}", font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"])
        self.title_label.pack(pady=(15, 0), padx=15, anchor="w")
        
        self.value_label = ctk.CTkLabel(self, text=value, font=ctk.CTkFont(size=24, weight="bold"), 
                                        text_color=color if color else COLORS["text"])
        self.value_label.pack(pady=(5, 15), padx=15, anchor="w")

    def update_value(self, new_value: str):
        self.value_label.configure(text=new_value)
