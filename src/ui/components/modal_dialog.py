import customtkinter as ctk
from src.core.config import COLORS

class ModalDialog(ctk.CTkToplevel):
    """Base class for modal dialogs."""
    
    def __init__(self, master, title: str, width: int = 400, height: int = 500):
        super().__init__(master)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.transient(master)
        self.grab_set()
        
        self.configure(fg_color=COLORS["bg_dark"])
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
