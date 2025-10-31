"""
UI Theme and Styling Configuration
"""
from tkinter import ttk

class UITheme:
    """Centralized theme configuration"""
    
    # Color Palette
    BACKGROUND_DARK = "#0f1419"
    BACKGROUND_MEDIUM = "#1a1f29"
    BACKGROUND_LIGHT = "#2c3440"
    ACCENT_BLUE = "#0f75bc"
    ACCENT_BLUE_DARK = "#357ABD"
    ACCENT_BLUE_LIGHT = "#87CEEB"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#8a92a3"
    SUCCESS_GREEN = "#1a3d4d"
    ERROR_RED = "#fd5e1f"
    WARNING_ORANGE = "#ff9500"
    
    @staticmethod
    def configure_ttk_styles(style):
        """Configure TTK styles"""
        style.theme_use('clam')
        
        # Progress bar style
        style.configure(
            'Modern.Horizontal.TProgressbar',
            background=UITheme.ACCENT_BLUE,
            troughcolor=UITheme.BACKGROUND_LIGHT,
            borderwidth=0,
            lightcolor=UITheme.ACCENT_BLUE,
            darkcolor=UITheme.ACCENT_BLUE
        )
        
        # Notebook styles
        style.configure('TNotebook', background=UITheme.BACKGROUND_DARK, borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background=UITheme.BACKGROUND_LIGHT, 
                       foreground=UITheme.TEXT_PRIMARY, 
                       padding=[12, 8], 
                       focuscolor='none')
        style.map('TNotebook.Tab', 
                  background=[('selected', UITheme.ACCENT_BLUE)], 
                  foreground=[('selected', UITheme.TEXT_PRIMARY)])
    
    @staticmethod
    def get_button_style(button_type="primary"):
        """Get button styling configuration"""
        styles = {
            "primary": {
                "bg": UITheme.ACCENT_BLUE,
                "fg": UITheme.TEXT_PRIMARY,
                "activebackground": UITheme.ACCENT_BLUE_DARK,
                "disabledforeground": UITheme.TEXT_PRIMARY,  # Keep white text when disabled
                "relief": "flat",
                "cursor": "hand2"
            },
            "success": {
                "bg": UITheme.SUCCESS_GREEN,
                "fg": UITheme.TEXT_PRIMARY,
                "activebackground": UITheme.ACCENT_BLUE_DARK,
                "disabledforeground": UITheme.TEXT_PRIMARY,  # Keep white text when disabled
                "relief": "flat",
                "cursor": "hand2"
            },
            "danger": {
                "bg": UITheme.ERROR_RED,
                "fg": UITheme.TEXT_PRIMARY,
                "activebackground": "#ff9500",
                "disabledforeground": UITheme.TEXT_PRIMARY,  # Keep white text when disabled
                "relief": "flat",
                "cursor": "hand2"
            },
            "secondary": {
                "bg": UITheme.BACKGROUND_LIGHT,
                "fg": UITheme.TEXT_PRIMARY,
                "activebackground": UITheme.BACKGROUND_MEDIUM,
                "disabledforeground": UITheme.TEXT_PRIMARY,  # Keep white text when disabled
                "relief": "flat",
                "cursor": "hand2"
            },
            "disabled": {
                "bg": "#808080",  # Gray background for disabled state
                "fg": UITheme.TEXT_PRIMARY,
                "activebackground": "#808080",
                "disabledforeground": UITheme.TEXT_PRIMARY,  # White text when disabled
                "relief": "flat",
                "cursor": "arrow"
            }
        }
        return styles.get(button_type, styles["primary"])
    
    @staticmethod
    def get_font_config(font_type="body"):
        """Get font configuration"""
        fonts = {
            "title": ("Segoe UI", 16, "bold"),
            "subtitle": ("Segoe UI", 10),
            "header": ("Segoe UI", 14, "bold"),
            "subheader": ("Segoe UI", 12, "bold"),
            "body": ("Segoe UI", 10),
            "small": ("Segoe UI", 9),
            "mono": ("Consolas", 9),
            "mono_small": ("Consolas", 8)
        }
        return fonts.get(font_type, fonts["body"])