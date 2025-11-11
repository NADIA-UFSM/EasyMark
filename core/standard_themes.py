import ttkbootstrap as tkb
from ttkbootstrap.style import ThemeDefinition, Style
from random import randint

rand_hex = f'#{randint(0, 255):02x}{randint(0, 255):02x}{randint(0, 255):02x}'

LIGHT_THEME_SETTINGS = {
    "type": "light",
    "colors": {
        "primary": "#4582ec",
        "secondary": "#adb5bd",
        "success": "#02b875",
        "info": "#17a2b8",
        "warning": "#f0ad4e",
        "danger": "#d9534f",
        "light": "#F8F9FA",
        "dark": "#343A40",
        "bg": "#ebebeb",
        "fg": "#343a40",
        "selectbg": "#adb5bd",
        "selectfg": "#ffffff",
        "border": "#bfbfbf",
        "inputfg": "#343a40",
        "inputbg": "#fff",
        "active": "#e5e5e5",
    },
    'extra_settings': {
        'EasyMark.ColorDisplay1.TFrame': {'background': rand_hex},
        'EasyMark.ColorDisplay2.TFrame': {'background': "#8d8d8d"},
        'EasyMark.ImageDisplay.TFrame': {'background': "#cfcfcf"},
        'EasyMark.DataDisplay.TLabel': {'foreground': "#494e53"},
        'EasyMark.TooltipSignal.TLabel': {'foreground': "#ff6600"},
        'EasyMark.secondary.TLabel': {'foreground': "#555555"},
        'EasyMark.Base.TEntry': {'foreground': "#494e53", 'bordercolor': '#bfbfbf'},
        'EasyMark.Active.TEntry': {'foreground': "#343a40", 'bordercolor': '#bfbfbf'},
        'EasyMark.Wrong.TEntry': {'foreground': "#343a40", 'bordercolor': "#740505"},
        'Treeview': {'relief': 'flat', 'borderwidth': 0, 'bordercolor': "#ebebeb", 'background': "#d4d4d4"},
        'Treeview.Heading': {'relief': 'solid'},
        'EasyMark.Treeview.itemcolor': {'background1': "#D5DADF", 'background2': '#f1f3f5'}
    }
}

DARK_THEME_SETTINGS = {
    "type": "dark",
    "colors": {
        "primary": "#375a7f",
        "secondary": "#444444",
        "success": "#00bc8c",
        "info": "#3498db",
        "warning": "#f39c12",
        "danger": "#e74c3c",
        "light": "#ADB5BD",
        "dark": "#303030",
        "bg": "#222222",
        "fg": "#ffffff",
        "selectbg": "#555555",
        "selectfg": "#ffffff",
        "border": "#222222",
        "inputfg": "#ffffff",
        "inputbg": "#2f2f2f",
        "active": "#1F1F1F",
    },
    'extra_settings': {
        'EasyMark.ColorDisplay1.TFrame': {'background': rand_hex},
        'EasyMark.ColorDisplay2.TFrame': {'background': "#8d8d8d"},
        'EasyMark.ImageDisplay.TFrame': {'background': "#3B3B3B"},
        'EasyMark.DataDisplay.TLabel': {'foreground': "#dddddd"},
        'EasyMark.TooltipSignal.TLabel': {'foreground': "#FDF900"},
        'EasyMark.secondary.TLabel': {'foreground': "#BBBBBB"},
        'EasyMark.Base.TEntry': {'foreground': "#bbbbbb", 'bordercolor': '#555555'},
        'EasyMark.Active.TEntry': {'foreground': "#ffffff", 'bordercolor': '#555555'},
        'EasyMark.Wrong.TEntry': {'foreground': "#ffffff", 'bordercolor': "#B60505"},
        'Treeview': {'relief': 'flat', 'borderwidth': 0, 'bordercolor': "#2b3e50", 'background': "#2f2f2f"},
        'Treeview.Heading': {'relief': 'solid'},
        'EasyMark.Treeview.itemcolor': {'background1': '#363636', 'background2': '#2f2f2f'}
    }
}

LIGHT_THEMEDEFINITION = ThemeDefinition('EM_light_standard', LIGHT_THEME_SETTINGS['colors'], LIGHT_THEME_SETTINGS['type'])
DARK_THEMEDEFINITION = ThemeDefinition('EM_dark_standard', DARK_THEME_SETTINGS['colors'], DARK_THEME_SETTINGS['type'])

#* Fully documented
def register_themes() -> None:
    """Registers the standard themes to be used by the window."""
    base_style = Style()
    base_style.register_theme(LIGHT_THEMEDEFINITION)
    base_style.register_theme(DARK_THEMEDEFINITION)

def use_theme(window: tkb.Window, theme_name:str) -> Style:
    """Sets the theme to be used by the window.

    Args:
        theme_name (str): Name of the theme
    """
    
    if theme_name == 'light':
        window.style.theme_use('EM_light_standard')
        for style, query in LIGHT_THEME_SETTINGS['extra_settings'].items():
            window.style.configure(style, **query)
    elif theme_name == 'dark':
        window.style.theme_use('EM_dark_standard')
        for style, query in DARK_THEME_SETTINGS['extra_settings'].items():
            window.style.configure(style, **query)
    
    return window.style
    
    

