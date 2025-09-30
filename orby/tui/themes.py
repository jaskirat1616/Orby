"""Theme management for Orby TUI with customizable color palettes."""
from typing import Dict, Any
from textual.app import App
from rich.style import Style
from rich.theme import Theme as RichTheme


class ThemeManager:
    """Manage multiple color themes for Orby TUI."""
    
    THEMES: Dict[str, Dict[str, Any]] = {
        "default": {
            "primary": "#6f42c1",      # Purple
            "secondary": "#20c4be",    # Teal
            "accent": "#ffd43b",       # Yellow
            "success": "#4caf50",       # Green
            "warning": "#ff9800",       # Orange
            "error": "#f44336",         # Red
            "surface": "#212529",        # Dark Gray
            "text": "#e9ecef",          # Light Gray
            "text-muted": "#adb5bd",    # Muted Gray
            "panel": "#343a40",         # Panel Gray
        },
        "cyberpunk": {
            "primary": "#bd10e0",        # Magenta
            "secondary": "#00feff",      # Cyan
            "accent": "#39ff14",         # Neon Green
            "success": "#00ff00",        # Bright Green
            "warning": "#ffff00",        # Yellow
            "error": "#ff0000",          # Red
            "surface": "#0a0a0a",        # Black
            "text": "#00ffcc",          # Neon Teal
            "text-muted": "#444444",    # Dark Gray
            "panel": "#111111",         # Almost Black
        },
        "zen": {
            "primary": "#6f42c1",        # Purple
            "secondary": "#20c4be",      # Teal
            "accent": "#8e44ad",         # Deep Purple
            "success": "#1abc9c",        # Turquoise
            "warning": "#f39c12",        # Orange
            "error": "#e74c3c",          # Red
            "surface": "#f8f9fa",        # Light Gray
            "text": "#212529",          # Dark Gray
            "text-muted": "#6c757d",    # Muted Gray
            "panel": "#e9ecef",         # Panel Light
        },
        "solarized": {
            "primary": "#268bd2",        # Blue
            "secondary": "#2aa198",      # Cyan
            "accent": "#b58900",         # Yellow
            "success": "#859900",        # Green
            "warning": "#cb4b16",        # Orange
            "error": "#dc322f",          # Red
            "surface": "#073642",        # Dark Blue-Gray
            "text": "#fdf6e3",          # Off-white
            "text-muted": "#657b83",    # Muted Blue-Gray
            "panel": "#002b36",         # Darker Blue-Gray
        },
        "dracula": {
            "primary": "#bd93f9",        # Purple
            "secondary": "#ff79c6",      # Pink
            "accent": "#f1fa8c",         # Yellow
            "success": "#50fa7b",        # Green
            "warning": "#ffb86c",        # Orange
            "error": "#ff5555",          # Red
            "surface": "#282a36",        # Dark Purple-Gray
            "text": "#f8f8f2",          # Light Gray
            "text-muted": "#6272a4",    # Muted Purple-Gray
            "panel": "#44475a",         # Panel Purple-Gray
        },
    }
    
    @classmethod
    def get_theme_css(cls, theme_name: str = "default") -> str:
        """Get CSS variables for a specific theme."""
        if theme_name not in cls.THEMES:
            theme_name = "default"
        
        theme_colors = cls.THEMES[theme_name]
        
        css_vars = []
        for var_name, color in theme_colors.items():
            css_vars.append(f"    --{var_name}: {color};")
        
        return f"""
/* {theme_name.title()} Theme */
:root {{
{'\n'.join(css_vars)}
}}

Screen {{
    background: var(--surface);
    color: var(--text);
}}

/* Header */
Header {{
    background: var(--primary);
    color: var(--text);
}}

/* Panels */
.dashboard-container {{ 
    background: var(--panel); 
    border: solid var(--primary);
}}

#status-panel {{ 
    border: solid var(--primary); 
}}

#memory-panel {{ 
    border: solid var(--secondary); 
}}

#model-panel {{ 
    border: solid var(--success); 
}}

/* Chat */
.chat-container {{ 
    border: solid var(--primary); 
}}

.user-message {{ 
    color: var(--primary); 
}}

.agent-message {{ 
    color: var(--accent); 
}}

/* Status */
.status-ready {{ 
    color: var(--success); 
}}

.status-thinking {{ 
    color: var(--warning); 
}}

.status-error {{ 
    color: var(--error); 
}}
    
    @classmethod
    def get_available_themes(cls) -> list:
        """Get list of available theme names."""
        return list(cls.THEMES.keys())
    
    @classmethod
    def apply_theme(cls, app: App, theme_name: str) -> bool:
        """Apply a theme to the application."""
        try:
            # Update CSS with new theme
            css_content = cls.get_theme_css(theme_name)
            
            # For now, we'll store theme name in app for reference
            app.current_theme = theme_name
            return True
        except Exception:
            return False


# Predefined theme instances
DEFAULT_THEME = ThemeManager.get_theme_css("default")
CYBERPUNK_THEME = ThemeManager.get_theme_css("cyberpunk")
ZEN_THEME = ThemeManager.get_theme_css("zen")
SOLARIZED_THEME = ThemeManager.get_theme_css("solarized")
DRACULA_THEME = ThemeManager.get_theme_css("dracula")