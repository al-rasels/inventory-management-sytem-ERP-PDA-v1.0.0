import customtkinter as ctk
from src.core.config import COLORS

class BaseView(ctk.CTkFrame):
    """Base class for all ERP views."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.pack(fill="both", expand=True)

    def create_header(self, title: str, subtitle: str = ""):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(header, text=title, font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        if subtitle:
            ctk.CTkLabel(header, text=subtitle, font=ctk.CTkFont(size=13),
                         text_color=COLORS["text_muted"]).pack(side="left", padx=20)
        return header

    def clear_view(self):
        for widget in self.winfo_children():
            widget.destroy()
