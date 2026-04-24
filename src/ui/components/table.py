import customtkinter as ctk
from src.core.config import COLORS

class DataTable(ctk.CTkFrame):
    """Reusable data table component."""
    
    def __init__(self, master, headers: list, **kwargs):
        super().__init__(master, fg_color=COLORS["card"], corner_radius=12, **kwargs)
        self.headers = headers
        self._build_header()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color=COLORS["sidebar"], height=40)
        header_frame.pack(fill="x", padx=2, pady=2)
        header_frame.pack_propagate(False)
        
        for header in self.headers:
            ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(weight="bold")).pack(side="left", expand=True)

    def set_data(self, rows: list):
        # Implementation for adding rows
        pass
