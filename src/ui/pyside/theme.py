"""
SunERP Professional Design System
Centralized theme, colors, and stylesheet generation for the entire application.
"""

class Theme:
    """Professional dark theme design tokens."""
    
    # === Core Palette ===
    BG_PRIMARY = "#0F172A"       # Main background
    BG_SECONDARY = "#1E293B"     # Card/panel background
    BG_TERTIARY = "#334155"      # Elevated elements
    BG_INPUT = "#0F172A"         # Input field background
    
    # === Accent Colors ===
    ACCENT = "#3B82F6"           # Primary blue
    ACCENT_HOVER = "#2563EB"     # Blue hover
    ACCENT_LIGHT = "#60A5FA"     # Light blue for text
    
    SUCCESS = "#10B981"          # Green
    SUCCESS_HOVER = "#059669"
    SUCCESS_BG = "#064E3B"       # Subtle green bg
    
    DANGER = "#EF4444"           # Red
    DANGER_HOVER = "#DC2626"
    DANGER_BG = "#450A0A"        # Subtle red bg
    
    WARNING = "#F59E0B"          # Amber
    WARNING_HOVER = "#D97706"
    WARNING_BG = "#451A03"       # Subtle amber bg
    
    ORANGE = "#F97316"
    ORANGE_HOVER = "#EA580C"
    
    PURPLE = "#8B5CF6"
    PURPLE_HOVER = "#7C3AED"
    
    # === Text Colors ===
    TEXT_PRIMARY = "#F8FAFC"     # Bright white
    TEXT_SECONDARY = "#CBD5E1"   # Muted white
    TEXT_MUTED = "#64748B"       # Gray
    TEXT_ACCENT = "#60A5FA"      # Blue text
    
    # === Border Colors ===
    BORDER = "#334155"
    BORDER_LIGHT = "#475569"
    BORDER_FOCUS = "#3B82F6"
    
    # === Sizing ===
    RADIUS_SM = "4px"
    RADIUS_MD = "8px"
    RADIUS_LG = "12px"
    RADIUS_XL = "16px"
    RADIUS_FULL = "9999px"
    
    FONT_FAMILY = "'Segoe UI', 'Inter', 'SF Pro Display', system-ui, sans-serif"
    
    # === Shadows ===
    SHADOW_SM = "0 1px 2px rgba(0,0,0,0.3)"
    SHADOW_MD = "0 4px 6px rgba(0,0,0,0.4)"
    SHADOW_LG = "0 10px 15px rgba(0,0,0,0.5)"
    
    @classmethod
    def global_stylesheet(cls):
        """Returns the master QSS stylesheet for the entire application."""
        return f"""
            /* === Global === */
            QWidget {{
                font-family: {cls.FONT_FAMILY};
                color: {cls.TEXT_PRIMARY};
                font-size: 13px;
            }}
            
            QMainWindow {{
                background-color: {cls.BG_PRIMARY};
            }}
            
            /* === Scrollbars === */
            QScrollBar:vertical {{
                background: {cls.BG_PRIMARY};
                width: 8px;
                margin: 0;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {cls.BG_TERTIARY};
                min-height: 30px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {cls.BORDER_LIGHT};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background: {cls.BG_PRIMARY};
                height: 8px;
                margin: 0;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: {cls.BG_TERTIARY};
                min-width: 30px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {cls.BORDER_LIGHT};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
            
            /* === Tooltips === */
            QToolTip {{
                background-color: {cls.BG_TERTIARY};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER};
                border-radius: {cls.RADIUS_SM};
                padding: 6px 10px;
                font-size: 12px;
            }}
        """
    
    @classmethod
    def card_style(cls, border_top_color=None):
        """Style for card/panel containers."""
        border_top = f"border-top: 3px solid {border_top_color};" if border_top_color else ""
        return f"""
            QFrame {{
                background-color: {cls.BG_SECONDARY};
                border-radius: {cls.RADIUS_LG};
                border: 1px solid {cls.BORDER};
                {border_top}
            }}
        """
    
    @classmethod
    def input_style(cls):
        """Style for QLineEdit inputs."""
        return f"""
            QLineEdit {{
                background-color: {cls.BG_INPUT};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER};
                border-radius: {cls.RADIUS_MD};
                padding: 10px 14px;
                font-size: 14px;
                selection-background-color: {cls.ACCENT};
            }}
            QLineEdit:focus {{
                border: 1px solid {cls.BORDER_FOCUS};
            }}
            QLineEdit:disabled {{
                color: {cls.TEXT_MUTED};
                background-color: {cls.BG_TERTIARY};
            }}
        """
    
    @classmethod
    def combo_style(cls):
        """Style for QComboBox dropdowns."""
        return f"""
            QComboBox {{
                background-color: {cls.BG_INPUT};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER};
                border-radius: {cls.RADIUS_MD};
                padding: 8px 12px;
                font-size: 13px;
                min-width: 120px;
            }}
            QComboBox:focus {{
                border: 1px solid {cls.BORDER_FOCUS};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {cls.BG_SECONDARY};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER};
                selection-background-color: {cls.ACCENT};
                selection-color: white;
                padding: 4px;
            }}
        """
    
    @classmethod
    def spin_style(cls):
        """Style for QSpinBox and QDoubleSpinBox."""
        return f"""
            QSpinBox, QDoubleSpinBox {{
                background-color: {cls.BG_INPUT};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER};
                border-radius: {cls.RADIUS_MD};
                padding: 8px 12px;
                font-size: 14px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 1px solid {cls.BORDER_FOCUS};
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                width: 20px;
                border: none;
                background: {cls.BG_TERTIARY};
            }}
        """
    
    @classmethod
    def table_style(cls):
        """Style for QTableWidget."""
        return f"""
            QTableWidget {{
                background-color: {cls.BG_PRIMARY};
                color: {cls.TEXT_SECONDARY};
                border: none;
                border-radius: {cls.RADIUS_MD};
                font-size: 13px;
                gridline-color: {cls.BORDER};
                selection-background-color: {cls.BG_TERTIARY};
                selection-color: {cls.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {cls.BG_SECONDARY};
                color: {cls.TEXT_MUTED};
                font-weight: bold;
                border: none;
                border-bottom: 2px solid {cls.BORDER};
                padding: 10px 8px;
                font-size: 12px;
                text-transform: uppercase;
            }}
            QTableWidget::item {{
                padding: 8px 6px;
                border-bottom: 1px solid {cls.BORDER};
            }}
            QTableWidget::item:selected {{
                background-color: {cls.BG_TERTIARY};
                color: {cls.TEXT_PRIMARY};
            }}
        """
    
    @classmethod
    def tableview_style(cls):
        """Style for QTableView (model-based)."""
        return f"""
            QTableView {{
                background-color: {cls.BG_SECONDARY};
                color: {cls.TEXT_SECONDARY};
                gridline-color: {cls.BORDER};
                border: none;
                border-radius: {cls.RADIUS_MD};
                font-size: 13px;
                selection-background-color: {cls.BG_TERTIARY};
                selection-color: {cls.TEXT_PRIMARY};
            }}
            QTableView::item {{
                padding: 6px;
                border-bottom: 1px solid {cls.BORDER};
            }}
            QTableView::item:selected {{
                background-color: {cls.BG_TERTIARY};
                color: {cls.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {cls.BG_PRIMARY};
                color: {cls.TEXT_MUTED};
                font-weight: bold;
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid {cls.BORDER};
                font-size: 12px;
            }}
        """
    
    @classmethod
    def btn_primary(cls):
        return f"""
            QPushButton {{
                background-color: {cls.ACCENT};
                color: white;
                border: none;
                border-radius: {cls.RADIUS_MD};
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {cls.ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #1D4ED8;
            }}
            QPushButton:disabled {{
                background-color: {cls.BG_TERTIARY};
                color: {cls.TEXT_MUTED};
            }}
        """
    
    @classmethod
    def btn_success(cls):
        return f"""
            QPushButton {{
                background-color: {cls.SUCCESS};
                color: white;
                border: none;
                border-radius: {cls.RADIUS_MD};
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {cls.SUCCESS_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #047857;
            }}
        """
    
    @classmethod
    def btn_danger(cls):
        return f"""
            QPushButton {{
                background-color: {cls.DANGER};
                color: white;
                border: none;
                border-radius: {cls.RADIUS_MD};
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {cls.DANGER_HOVER};
            }}
        """
    
    @classmethod
    def btn_warning(cls):
        return f"""
            QPushButton {{
                background-color: {cls.ORANGE};
                color: white;
                border: none;
                border-radius: {cls.RADIUS_MD};
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {cls.ORANGE_HOVER};
            }}
        """
    
    @classmethod
    def btn_ghost(cls):
        """Transparent button with border."""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {cls.TEXT_SECONDARY};
                border: 1px solid {cls.BORDER};
                border-radius: {cls.RADIUS_MD};
                padding: 8px 16px;
                font-weight: 500;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {cls.BG_TERTIARY};
                color: {cls.TEXT_PRIMARY};
                border-color: {cls.BORDER_LIGHT};
            }}
        """
    
    @classmethod
    def btn_icon_danger(cls):
        """Small icon-only danger button (e.g., remove from cart)."""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {cls.DANGER};
                border: 1px solid {cls.DANGER};
                border-radius: {cls.RADIUS_SM};
                padding: 4px 8px;
                font-size: 14px;
                font-weight: bold;
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {cls.DANGER};
                color: white;
            }}
        """
    
    @classmethod
    def btn_icon_primary(cls):
        """Small icon button for add-to-cart etc."""
        return f"""
            QPushButton {{
                background-color: {cls.ACCENT};
                color: white;
                border: none;
                border-radius: {cls.RADIUS_SM};
                padding: 5px 12px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {cls.ACCENT_HOVER};
            }}
        """
    
    @classmethod
    def label_title(cls):
        return f"font-size: 18px; font-weight: bold; color: {cls.TEXT_PRIMARY}; border: none; background: transparent;"
    
    @classmethod
    def label_subtitle(cls):
        return f"font-size: 14px; color: {cls.TEXT_SECONDARY}; border: none; background: transparent;"
    
    @classmethod
    def label_muted(cls):
        return f"font-size: 12px; color: {cls.TEXT_MUTED}; border: none; background: transparent;"
    
    @classmethod
    def label_value(cls, color=None):
        c = color or cls.TEXT_PRIMARY
        return f"font-size: 24px; font-weight: bold; color: {c}; border: none; background: transparent;"
    
    @classmethod
    def badge_style(cls, bg_color, text_color="white"):
        return f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: {cls.RADIUS_FULL};
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 600;
            }}
        """
