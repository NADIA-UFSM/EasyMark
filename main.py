from _tkinter import Tcl_Obj
from dataclasses import asdict
import tkinter as tk
from tkinter import filedialog, messagebox, font
import ttkbootstrap as tkb
from ttkbootstrap.dialogs.colorchooser import ColorChooserDialog as ColorDialog
from ttkbootstrap.tooltip import ToolTip

#teste 😍

import os
import json
from random import randint
from string import ascii_lowercase
from random import choices as randchoices
from collections import Counter
import webbrowser
import traceback

from PIL import ImageTk
from typing import Any, Literal, Optional, Iterable

# ========================================================== #
# ========================================================== #


from core import *
from core.typeAliases import CategoryDataType, _actionType, _annTypeGen
_ = translator

#TODO: Remove this at some point
#* Fully documented
class PlaceholderClass:
    """Placeholder class for testing purposes.
    """
    def __init__(self) -> None:
        """Placeholder class for testing purposes.
        """
        pass
    
    def __call__(self, **kw) -> None:
        """Placeholder function for testing purposes.
        
        Args:
            *args (tuple[Any]): Any number of arguments to be displayed on terminal.
        """
        print(kw)
        raise NotImplementedError('Tool in development')
placeholder = PlaceholderClass()


# ========================================================== #
# ========================================================== #

#* Fully documented
def base_toplevel_binds(win: tkb.Toplevel) -> None:
    """General binds and settings for TopLevel Window.

    Args:
        win (tkb.Toplevel): Reference to the TopLevel window.
    """
    win.wait_visibility(win)
    win.grab_set()
    win.bind('<Button>', lambda *x: keep_focus(win))
    win.protocol("WM_DELETE_WINDOW", lambda *x: close_window(win))

def keep_focus(win: tkb.Toplevel) -> None:
    if win.focus_get() is None:
        win.focus_set()
        win.lift()

def close_window(win: tkb.Toplevel) -> None:
    """Safely closes a TopLevel window.

    Args:
        win (tkb.Toplevel): Reference to the TopLevel window.
    """
    win.grab_release()
    win.destroy()

def get_icon(icon_name: str) -> tkb.PhotoImage:
    """Returns the requested icon in the correct theme.

    Args:
        icon_name (str): name of the icon.

    Returns:
        icon (tkb.PhotoImage): Icon to be displayed.
    """
    match CONFIG.theme:
        case 'dark': return tkb.PhotoImage(file=os.path.join(FOLDER_PATHS.IMAGE, f'{icon_name}_white.png'))
        case 'light': return tkb.PhotoImage(file=os.path.join(FOLDER_PATHS.IMAGE, f'{icon_name}_black.png'))
        case _:
            error_message = f'Theme not found "{CONFIG.theme}"'
            raise ProcessLookupError(error_message)

# ========================================================== #
# ========================================================== #

#* Fully documented
class MainWindow(tkb.Window):
    """Class object that constructs and handles the main window of the tool.
    """
    def __init__(self) -> None:
        """Class object that constructs and handles the main window of the tool.
        """
        super().__init__(title="EasyMark", minsize=(1000, 450))
        register_themes()
        use_theme(self, CONFIG.theme)
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        
        self.loader = ImageLoader(self, FOLDER_PATHS.CONFIG)
        self.images: list[ImageData | None] = self.loader.images
        self.saved: bool = True
        self.errors: dict[str, int] = {}
        
        self.main_binds()
        self.main_widgets()
        
        self.after(ms=1000, func= lambda *x: self.check_backup())
        self.after(ms=120000, func=lambda *x: self.backup())
    
    def main_widgets(self) -> None:
        """Calls to construct the menu bar and the main frame for display.
        """
        top_bar = MenuBar(self)
        self.config(menu=top_bar)
        
        self.display = DisplayMaker(self)
    
    def main_binds(self) -> None:
        """Sets the window's main shortcus.
        """
        self.bind("<Control-KeyRelease-s>", self._save)
        self.bind("<Control-KeyRelease-S>", self._save)
        self.bind("<Control-KeyRelease-n>", lambda *x: NewProjectMenu())
        
        self.bind("<ButtonPress>", self._unfocus)
        
        self.protocol('WM_DELETE_WINDOW', self._close_window)
        
        if CONFIG.dev_mode: self._bind_DEBUG()
        else: self.bind("<Alt-KeyPress-End>", self._bind_DEBUG)
    
    def check_backup(self) -> None:
        """Checks for backup project files on initialization.
        """
        check_baks = [file for file in os.listdir(FOLDER_PATHS.CONFIG) if '.bak' in file]
        if len(check_baks) == 0: return
        
        load_bak = messagebox.askyesno(title="Backup found",
                                       message="Backup file found, would you like to load it?")
        if load_bak:
            self.loader.select_datafile(preset_path=check_baks[0])
        for bak in check_baks:
            os.remove(os.path.join(FOLDER_PATHS.CONFIG, bak))
    
    def backup(self) -> None:
        """Creates a backup project file every five minutes.
        """
        if self.images[0] is not None:
            self.loader.save_project('backup')
        self.after(ms=120000, func= lambda *x: self.backup())
    
    # ---------------------------------------------------------- #
    
    def _unfocus(self, *_) -> None:
        """Forces the focus on the window.
        """
        x, y = self.winfo_pointerxy()
        widget = self.winfo_containing(x, y)
        if 'entry' not in str(widget): self.focus()
        if 'treeview' not in str(widget):
            table = self.display.side.val_table
            selected = table.selection()
            table.selection_remove(selected)
    
    def _save(self, event: tk.Event) -> None:
        """Handler for saving projects.

        Args:
            event (tk.Event): Tkinter click event.
        """
        print(event)
        e = str(event).lower()
        save_mode = 'choose' if 'shift' in e \
                 else 'normal'
        self.saved = self.loader.save_project(save_mode)
    
    def _close_window(self) -> None:
        """Handler for closing the main window. Prompts the user to save an unsaved project.
        """
        self.display.main._closing_funcs()
        if not self.saved:
            self.loader.save_project('backup')
            permit_close = self.loader.save_unsaved()
        else: permit_close = True
        
        with open(CONFIG_FILE_PATH, 'w') as file:
            json.dump(asdict(CONFIG), file, indent=4)
        
        if permit_close:
            if self.images[0] is not None:
                self.images[0].clean()
            self.destroy()
    
    def _update(self) -> None:
        """First step on the update cascade.
        """
        self.saved = True
        self.display._update()

    def report_callback_exception(self, *args):
        """Main error handler for the application.
        """
        val = args[1]
        err = ''.join(traceback.format_exception(*args))
        error_spec = str(val)
        if error_spec not in self.errors.keys(): 
            self.errors[error_spec] = 1
            messagebox.showerror(_('Error'), err)
        else:
            self.errors[error_spec] += 1
            if self.errors[error_spec] <= 10: 
                messagebox.showerror(_('Error'), err)
            elif self.errors[error_spec] == 11:
                message = _('Error message repetition limit exceeded.') + '\n' + _('Subsequent messages will be shown on terminal only.') + '\n' + err
                messagebox.showerror(_('Error'), message)
        print(err, end='')
        print(f"Error has been shown {self.errors[error_spec]} times")
    
    # ---------------------------------------------------------- #
    # Debug tools
    
    def _key_DEBUG(self, e: tk.Event) -> None:
        """Displays click event data for debug purposes.

        Args:
            e (tk.Event): Tkinter click event.
        """
        if not self.activate_debug_key.get(): return
        print(e)
        
        x, y = self.winfo_pointerxy()
        widget = self.winfo_containing(x, y)
        print(widget)

    def _bind_DEBUG(self, e: Optional[tk.Event] = None) -> None:
        """Shorcuts for debug purposes.

        Args:
            e (tk.Event, optional): Tkinter click event. Defaults to None.
        """
        if e is not None:
            event = str(e).lower()
            if "control" not in event or not 'shift' in event: return
            messagebox.showwarning(title='DEBUG', message='Debug mode active')
        
        self.activate_debug_key = tkb.BooleanVar(value=False)
        self.bind("<Control-Key-1>", lambda *x: print(self.images[0].categories)) # type: ignore
        self.bind("<Control-Key-2>", lambda *x: self.display.side._create_example_categories(6))
        self.bind("<Control-Key-3>", lambda *x: print(f'Undo Stack: {self.display._DisplayMaker__stacks.action_str()}')) # type: ignore
        self.bind("<Control-Key-4>", lambda *x: print(f'Redo Stack: {self.display._DisplayMaker__stacks.reaction_str()}')) # type: ignore
        self.bind("<Control-Key-5>", lambda *x: print(self.display.main.clean_canvas()))
        self.bind("<Control-Key-6>", lambda *x: print(f'Categoryes: {"".join([f"\n    > {id_tag}: {data}" for id_tag, data in self.images[0].categories.items()])}')) # type: ignore
        self.bind("<Control-Key-7>", lambda *x: print(int('aa')))
        self.bind("<Control-Key-8>", lambda *x: print(self.images[0].cur_image())) # type: ignore
        self.bind("<Control-Key-9>", lambda *x: print(f'Config: {"".join([f"\n  > {name}: {val}" for name, val in asdict(CONFIG).values()])}'))
        self.bind("<Control-Key-0>", lambda *x: self.activate_debug_key.set(value=False) if self.activate_debug_key.get()
                                                        else self.activate_debug_key.set(value=True))
        # self.bind("<Motion>", lambda *x: print(int('a')))
        self.bind("<KeyRelease-ccedilla>", lambda *x: self._autostart())
        self.bind("<KeyRelease>", self._key_DEBUG)

    def _autostart(self) -> None:
        self.loader.load_directory(FOLDER_PATHS.IMAGE, 'manual', {})
        SIDE._create_example_categories(6)
    
    def _nametowidget(self, name: str | tk.Misc | Tcl_Obj) -> Any:
        try:
            return super().nametowidget(name)
        except KeyError:
            return name

# ========================================================== #
# ========================================================== #

#* Fully documented
class MenuBar(tkb.Menu):
    """Class object for the top menu bar on the window."""
    def __init__(self, master: MainWindow) -> None:
        """
        Class object for the top menu bar on the window.
        
        Args:
            mestre (MainWindow): Reference to the MainWindow.
        """
        super().__init__(master=master,
                         borderwidth=5,
                         relief='raised',
                         type='menubar')
        self.window = master
        self.loader = master.loader
        self.file_menu()
        self.tools_menu()
        self.options_menu()

    #* ====================================================================== #

    def file_menu(self) -> None:
        """Constructs the "File" tab on the menu bar.
        """
        file_menu = tkb.Menu(master=self, tearoff=0, relief='ridge', borderwidth=5)
        
        open_menu = self.open_submenu(file_menu)
        
        file_menu.add_cascade(label=_("Open"), menu=open_menu)
        file_menu.add_command(label=_("Save project"), accelerator="(Ctrl+S)", command= lambda *x: self.save_project('normal'))
        file_menu.add_command(label=_("Save project as"), accelerator="(Ctrl+Shift+S)", command= lambda *x: self.save_project('choose'))
        file_menu.add_command(label=_("Export project"), accelerator="(Ctrl+E)", command= lambda *x: ExporterWindow(self.window))
        self.add_cascade(label=_('File'), menu=file_menu)
    
    def open_submenu(self, file_menu: tkb.Menu) -> tkb.Menu:
        """Constructs the "Open" submenu on the file tab.

        Args:
            file_menu (tkb.Menu): Reference to the file tab menu.

        Returns:
            open_menu (tkb.Menu): Reference to the constructed open submenu to be attached to the file tab menu.
        """
        open_menu = tkb.Menu(master=file_menu)
        
        recent_menu = self.recent_submenu(open_menu)
        
        open_menu.add_command(label=_("New project"), accelerator="(Ctrl+N)", command= lambda *x: NewProjectMenu())
        open_menu.add_command(label=_("Continue project"), accelerator="(Ctrl+O)", command= lambda *x: self.loader.select_datafile())
        open_menu.add_cascade(label=_("Recent projects"), menu=recent_menu)
        return open_menu    
    
    def recent_submenu(self, open_menu: tkb.Menu) -> tkb.Menu:
        """Constructs the "Recent project" submenu on the open submenu.

        Args:
            open_menu (tkb.Menu): Reference to the open submenu.

        Returns:
            recent_menu (tkb.Menu): Reference to the constructed recent submenu to be attached to the open submenu.
        """
        recent_menu = tkb.Menu(master=open_menu)
        for path in CONFIG.recent:
            recent_menu.add_command(label=path, command= lambda x=path, *y: self.loader.select_datafile(preset_path=x))
        return recent_menu

    #* ====================================================================== #
    
    def tools_menu(self) -> None:
        """Constructs the "Tools" tab on the menu bar
        """
        tools_menu = tkb.Menu(master=self, tearoff=0, relief='ridge', borderwidth=5)
        
        tools_menu.add_command(label=_("Automatic annotation"), command= lambda *x: DetectiontoProjectWindow(self.window))
        
        self.add_cascade(label=_("Tools"), menu=tools_menu)

    def options_menu(self) -> None:
        """Constructs the "Options" tab on the menu bar
        """
        options_menu = tkb.Menu(master=self, tearoff=0, relief='ridge', borderwidth=5)
        
        options_menu.add_command(label=_("Configs"),  command= lambda *x: ConfigMenu())
        options_menu.add_command(label=_("Shorcuts"), command= lambda *x: ShortcutsMenu())
        self.add_cascade(label=_("Options"), menu=options_menu)
    
    #* ====================================================================== #
    
    def save_project(self, save_mode: Literal['normal', 'choose']) -> None:
        """Calls the image loader to save the currently open project.

        Args:
            save_mode (Literal[&#39;normal&#39;, &#39;choose&#39;]): Sets the save mode to be called.
            
        - normal: Prompts the user for a save path on first call, reutilizes the path all other times. 
        - choose: Always prompts the user for a save path.
        """
        if self.window.images[0] == None: return
        self.loader.save_project(save_mode)

#* Fully documented
class NewProjectMenu(tkb.Toplevel):
    """Class object for the new project menu window.
    """
    def __init__(self) -> None:
        """Class object for the New Project window.
        """
        super().__init__(master=WINDOW, title=_("New project"), resizable=(False, False))
        base_toplevel_binds(self)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        self.open_popup_frame = tkb.Frame(master=self, relief='ridge', padding=5)
        self.open_popup_frame.pack(expand=True, fill='both')
        
        for i in range(4):
            self.open_popup_frame.columnconfigure(i, weight=2 if i < 3 else 1)
        for i in range(8):
            self.open_popup_frame.rowconfigure(i, weight=1)

        self.path_var = tkb.StringVar(value='')
        self.mode_display_var = tkb.StringVar(value=_('Manual'))
        self.mode_var = tkb.StringVar(value='manual')
        self.mode_desc_var = tkb.StringVar(value=_('Draw shapes around objects of interest.'))

        self.arq_icon = get_icon('arq')
        
        self.configs_constructor()
        
        self.bind('<KeyRelease-Return>', lambda *x: self.open_function())
        
    def configs_constructor(self) -> None:
        """Constructs the interactible inputs for project configuration.
        """
        mode_label = tkb.Label(master=self.open_popup_frame, text=_("Annotation mode"))
        mode_button = tkb.Menubutton(master=self.open_popup_frame, width=13, textvariable=self.mode_display_var)
        mode_menu = tkb.Menu(master=mode_button, tearoff=0, relief='ridge', borderwidth=5)
        for option, label in [('manual', _('Manual')), ('semiauto', _('Semi-automatic'))]:
            mode_menu.add_radiobutton(label=label, value=option,
                                      command=lambda x=option, y=label, *z: self.set_mode(x, y))
        mode_button.config(menu=mode_menu)
        mode_desc = tkb.Label(master=self.open_popup_frame, textvariable=self.mode_desc_var, font=("Arial", 10), style='EasyMark.secondary.TLabel')
        
        
        path_label = tkb.Label(master=self.open_popup_frame, text=_('Image directory'))
        path_entry = tkb.Entry(master=self.open_popup_frame, textvariable=self.path_var, width=50)
        path_button = tkb.Button(master=self.open_popup_frame, image=self.arq_icon, style='Outline.Toolbutton',
                                 command= lambda *x: self.get_imgdir())
        
        confirm_button = tkb.Button(master=self.open_popup_frame, text=_("Open"), command= lambda *x: self.open_function())
        
        
        mode_label.grid(column=0, row=0, pady=2, padx=(2, 0), sticky='w')
        mode_button.grid(column=0, row=1, columnspan=2, pady=2, padx=(2, 0), sticky='w')
        mode_desc.grid(column=0, row=2, sticky='w')
        
        path_label.grid(column=0, row=4, pady=2, padx=(2, 0), sticky='nswe')
        path_entry.grid(column=0, row=5, columnspan=3, pady=2, padx=(2, 0), sticky='we')
        path_button.grid(column=3, row=5, pady=2, padx=(2, 0))
        
        tkb.Separator(master=self.open_popup_frame).grid(column=0, columnspan=4, row=6, sticky='we', pady=(4, 0))
        confirm_button.grid(column=3, row=7, pady=2, padx=(2, 0), sticky='nsew')
        
    def set_mode(self, option: str, label: str) -> None:
        """Sets the annotation mode, visual display and description.

        Args:
            option (str): Annotation mode.
            label (str): Annotation display name.
        """
        self.mode_var.set(value=option)
        self.mode_display_var.set(value=label)
        
        match option:
            case 'manual': self.mode_desc_var.set(_('Draw shapes around objects of interest.'))
            case 'semiauto': self.mode_desc_var.set(_('Place seeds over objects of interest.'))
    
    def get_imgdir(self) -> None:
        """Prompts the user for a directory path with images.
        """
        path, _ = WINDOW.loader.select_directory(self)
        if path is None: self.path_var.set(value='')
        else: self.path_var.set(value = path)
    
    def open_function(self) -> None:
        """Gathers the configuration data and starts a new project.
        """
        path, categories = WINDOW.loader.select_directory(self, self.path_var.get())
        if path is None: return
        mode = self.mode_var.get()
        
        WINDOW.loader.load_directory(path, mode, categories) # type: ignore
        close_window(self)

#* Fully documented
class ConfigMenu(tkb.Toplevel):
    """Class object for the configurations menu window.
    """
    def __init__(self) -> None:
        """Class object for the configurations menu window
        """
        super().__init__(master=WINDOW, title=_("Configuration"), resizable=(False, False))
        base_toplevel_binds(self)
        
        self.config_frame = tkb.Frame(master=self, relief='raised', padding=10)
        self.config_frame.grid(column=0, row=0, sticky='nsew')
        for i in range(2):
            self.config_frame.rowconfigure(i, weight=1)
        self.config_frame.columnconfigure(0, weight=1)
        self.language_display = tkb.StringVar(value=f'{LANG.name if LANG.name != '' else "English"}')
        self.theme_display = tkb.StringVar(value=_(CONFIG.theme).capitalize())
        self.path_var = tkb.StringVar(value=CONFIG.default_output)
        self.arq_icon = get_icon('arq')
            
        self.configs_constructor()
       
    def configs_constructor(self) -> None:
        """Constructs the interactible inputs for software configuration.
        """
        menu_frame = tkb.Frame(master=self.config_frame)
        for i in range(2):
            menu_frame.columnconfigure(i, weight=i%2)
            menu_frame.rowconfigure(i, weight=i%2)
        menu_frame.pack(expand=True, fill='both')
        
        lang_label = tkb.Label(master=menu_frame, text=_("Language"))
        lang_button = tkb.Menubutton(master=menu_frame, width=7, textvariable=self.language_display)
        lang_menu = tkb.Menu(master=lang_button)
        for lang_code, name in LANGUAGES.items():
            lang_menu.add_command(label=name, command= lambda x=lang_code, *y: self.change_lang(x))
        lang_button.configure(menu=lang_menu)
        
        theme_label = tkb.Label(master=menu_frame, text=_("App theme"))
        theme_button = tkb.Menubutton(master=menu_frame, width=7, textvariable=self.theme_display)
        theme_menu = tkb.Menu(master=theme_button)
        for label, option in [(_('Light'), 'light'), (_('Dark'), 'dark')]:
            theme_menu.add_radiobutton(label=label, command= lambda x=option, y=label, *z: self.change_window_theme(x, y))
        theme_button.configure(menu=theme_menu)
        
        path_frame = tkb.Frame(master=self.config_frame)
        path_frame.rowconfigure(0, weight=1)
        path_frame.columnconfigure(0, weight=1)
        path_label = tkb.Label(master=path_frame, text=_('Default output'))
        path_entry = tkb.Entry(master=path_frame, textvariable=self.path_var, width=50)
        self.path_button = tkb.Button(master=path_frame, image=self.arq_icon, style='Outline.Toolbutton',
                                 command= lambda *x: self.get_output_dir())
        
        
        lang_label.grid(column=0, row=0, sticky='nsw', pady=3, padx=(0, 5))
        lang_button.grid(column=1, row=0, sticky='nw', pady=3)
        theme_label.grid(column=0, row=1, sticky='nsw', pady=3, padx=(0, 5))
        theme_button.grid(column=1, row=1, sticky='nw', pady=3)
        
        path_frame.pack(expand=True, fill='both')
        path_label.pack(fill='x', expand=True)
        path_entry.pack(fill='both', expand=True, side='left', padx=(0, 5))
        self.path_button.pack(side='left')
        
        path_entry.bind('<KeyRelease>', lambda *x: self.check_default_dir())
    
    def change_window_theme(self, theme: str, label: str) -> None:
        """Updates the display theme of the window.

        Args:
            theme (str): Theme code.
            label (str): Theme display name.
        """
        self.theme_display.set(label)
        CONFIG.theme = theme
        self.arq_icon = get_icon('arq')
        self.path_button.configure(image=self.arq_icon)
        use_theme(WINDOW, theme)
        WINDOW._update()
    
    def change_lang(self, lang_code: str) -> None:
        """Changes the language setting of the window. Prompts the user to restart the software.

        Args:
            lang_code (str): language code.
        """
        self.language_display.set(LANGUAGES[lang_code])
        CONFIG.lang_code = lang_code
        if lang_code == ":)": lang_code = 'smile'
        with open(os.path.join(FOLDER_PATHS.LOCALE,f'{lang_code}.json'), 'r') as file:
            lang = json.load(file)
        messagebox.showinfo(master=self, # type: ignore
                            title=lang['lines']["Language setting changed"],
                            message=lang['lines']["You will need to close and open the app for changes to take effect."])
    
    def get_output_dir(self) -> None:
        """Prompts the user to choose a default output directory for the software.
        """
        dir_path = filedialog.askdirectory(title=_("Select default output directory"), mustexist=True, parent=self)
        if dir_path in [None, '', ()]: return
        if not os.path.isdir(dir_path):
            messagebox.showerror(title=_("Invalid directory"),
                                 message=_("The selected directory does not exist."),
                                 master=self) # type: ignore
            return
        
        CONFIG.default_output = dir_path
    
    def check_default_dir(self) -> bool:
        """Checks if the written path is a valid directory. Saves it as default directory if `True`

        Returns:
            valid_directory (bool): If given path is a valid directory.
        """
        path = self.path_var.get()
        if os.path.isdir(path) and not path.isspace():
            CONFIG.default_output = path
            return True
        return False

#* Fully documented
class ShortcutsMenu(tkb.Toplevel):
    """Class object for the shotcuts menu window."""
    def __init__(self) -> None:
        """Class object for the shotcuts menu window."""
        super().__init__(master=WINDOW, title=_("Shortcuts"), resizable=(False, False))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        base_toplevel_binds(self)
        
        self.shortcuts_frame = tkb.Frame(master=self, relief='raised')
        self.shortcuts_frame.columnconfigure(0, weight=1)
        self.shortcuts_frame.rowconfigure(0, weight=1)
        self.shortcuts_frame.pack(fill='both', expand=True, ipadx=5, ipady=5)
        
        self.tree_constructor()
        
    def tree_constructor(self) -> None:
        """Constructs the keybind visualization grid.
        """  
        col_data = {
            'shortcut': (150, 'center', True, _("Shortcut")),
            'function': (150, 'center', True, _("Function"))
        }
        self.shortcuts_tree = tkb.Treeview(self.shortcuts_frame, show='headings', columns=list(col_data.keys()))
        self.shortcuts_tree.pack(fill='both', expand=True)
        
        for col, data in col_data.items():
            self.shortcuts_tree.column(col, 
                                  width=data[0],
                                  anchor=data[1], # type: ignore
                                  stretch=data[2])
            self.shortcuts_tree.heading(col, text=data[3])
        
        background1 = WINDOW.style.configure('EasyMark.Treeview.itemcolor')['background1']
        background2 = WINDOW.style.configure('EasyMark.Treeview.itemcolor')['background2']
        self.shortcuts_tree.tag_configure('True', background=background1)
        self.shortcuts_tree.tag_configure('False', background=background2)
        
        for i in range(len(SHORTCUTS)):
            self.shortcuts_tree.insert(index='end', parent='', tags=[f'{i%2==0}'], values=SHORTCUTS[i])


# ========================================================== #
# ========================================================== #

#* Fully documented
class DisplayMaker(tkb.Frame):
    """Class object container for the SideBar, LowerBar and MainVisualizer objects.
    """
    def __init__(self, mestre: MainWindow) -> None:
        """Class object container for the SideBar, LowerBar and MainVisualizer objects.

        Args:
            mestre (MainWindow): Reference to the MainWindow.
        """
        super().__init__(master=mestre, relief='raised')
        self.mestre = mestre
        self.images = mestre.images

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        
        self.grid(column=0, row=0, sticky='nsew')
        
        self.ann_in_progress: bool = False
        
        self.side = Sidebar(self)
        self.main = MainVisualizer(self)
        self.low = LowerBar(self)
        self.rodape()
        
        self.__stacks = ActionStacks(self.mestre, self.side, self.main)
        self.last_stack_len: int = 0
        
        self.side.binds(self.main.canvas)
        self.binds()

    def rodape(self) -> None:
        """Adds a footer to the software UI."""
        rodape = tkb.Frame(master=self, relief='groove', padding=3)
        rodape.grid(column=0, columnspan=2, row=2, sticky='nsew')
        
        texto_rodape = tkb.Label(master=rodape, text='Developed by NADIA - UFSM-CS', font=font.Font(size=7, weight='bold'), cursor='hand2')
        tooltip_rodape = ToolTip(texto_rodape, f"{_("Data Science and Artificial Inteligence Center")}\n{_("Federal University of Santa Maria - Cachoeira do Sul")}", wraplength=600)
        texto_rodape.bind("<Button-1>", lambda *x: webbrowser.open_new_tab('https://github.com/NADIA-UFSM/EasyMark'))
        texto_rodape.pack(side='right')
        
    def add_action(self, action_type: _actionType, *action_data: Any) -> None:
        """Adds an action to the stack.

        Args:
            action_type (_actionType): Type of action to be saved to the stacks.
            action_data (Any): Data to be attached to the action.
        """
        self.__stacks.new_action(action_type, *action_data)
    
    def clean_stacks(self, clear: bool = False) -> None:
        """Checks if the stack size changed. Trims it if necessary.

        Args:
            clear (bool, optional): If True, clears the stack completely. Defaults to False.
        """
        try:
            if len(self.__stacks) != self.last_stack_len:
                self.last_stack_len = len(self.__stacks) 
                self.mestre.saved = False
            else: self.mestre.saved = True
            self.__stacks.trim_stacks(clear)
        except AttributeError: pass
    
    def binds(self) -> None:
        """Binds for the stack actions."""
        self.mestre.bind("<Control-KeyRelease-z>", lambda *x: self.__stacks.activate_action())
        self.mestre.bind("<Control-KeyRelease-y>", lambda *x: self.__stacks.activate_reaction())
    
    def _update(self) -> None:
        """Second step on the update cascade."""
        self.side._update()
        self.main._update()
        self.low.update_labels()
        self.clean_stacks(clear=True)


# ========================================================== #
# ========================================================== #

#* Fully documented
class LowerBar(tkb.Frame):
    """Class object that displays basic data about the currently-open project.
    """
    def __init__(self, mestre: DisplayMaker) -> None:
        """Class object that displays basic data about the currently-open project.

        Args:
            mestre (DisplayMaker): Reference to the DisplayMaker.
        """
        super().__init__(master=mestre, 
                         relief='raised', 
                         borderwidth=5)

        self.loader = mestre.mestre.loader
        self.images = mestre.images
        
        self.lowerbar_vars = {
            'mode': tkb.StringVar(value= _('Mode') + ': ' + _('No project started')),
            'creation': tkb.StringVar(value=_('Creation') + ': ' + _('No date')),
            'last_mod': tkb.StringVar(value=_('Last modified') + ': ' + _('No date')),
            'lastbak': tkb.StringVar(value=_('Last backup') + ': ' + _('No backup')),
            'imgdir': tkb.StringVar(value=_('Image directory') + ': ' + _('No directory selected')),
            'marksdir': tkb.StringVar(value=_('Marks directory') + ': ' + _('No marks saved'))
        }
        
        for i in range(6):
            self.rowconfigure(0, weight=1)
        for i in range(10):
            self.columnconfigure(i, weight=1)
        
        self.grid(column=0, row=1, 
                  sticky='nsew', 
                  padx=(5, 2), pady=(2, 5))
        
        self.make_labels()
    
    def make_labels(self) -> None:
        """Constructs the text labels with all displayed data.
        """
        mode_label  = tkb.Label(master=self, 
                                textvariable=self.lowerbar_vars['mode'], 
                                justify='left',
                                style='EasyMark.DataDisplay.TLabel')
        creation_label = tkb.Label(master=self, 
                                   textvariable=self.lowerbar_vars['creation'], 
                                   justify='left',
                                   style='EasyMark.DataDisplay.TLabel')
        last_mod_label = tkb.Label(master=self, 
                                   textvariable=self.lowerbar_vars['last_mod'], 
                                   justify='left',
                                   style='EasyMark.DataDisplay.TLabel')
        lastbak_label = tkb.Label(master=self, 
                                  textvariable=self.lowerbar_vars['lastbak'], 
                                  justify='left',
                                  style='EasyMark.DataDisplay.TLabel')
        imgdir_label = tkb.Label(master=self, 
                                 textvariable=self.lowerbar_vars['imgdir'], 
                                 justify='left',
                                 width=50,
                                 style='EasyMark.DataDisplay.TLabel')
        marksdir_label = tkb.Label(master=self, 
                                   textvariable=self.lowerbar_vars['marksdir'], 
                                   justify='left',
                                   width=50,
                                   style='EasyMark.DataDisplay.TLabel')
        
        self.tooltips = {
            'imgdir' : ToolTip(imgdir_label, text=_('No directory selected')),
            'marksdir' : ToolTip(marksdir_label, text=_('No marks saved'))
            
        }
        
        mode_label.grid(column=0, columnspan=4, row=0, sticky='nsew')
        creation_label.grid(column=0, columnspan=4, row=1, sticky='nsew')
        last_mod_label.grid(column=0, columnspan=4, row=2, sticky='nsew')
        lastbak_label.grid(column=0, columnspan=4, row=3, sticky='nsew')
        imgdir_label.grid(column=0, columnspan=4, row=4, sticky='nsew')
        marksdir_label.grid(column=0, columnspan=4, row=5, sticky='nsew')

    def update_labels(self, bak_date: str = '') -> None:
        """Updates the text labels when a project is opened, closed, saved and backed-up.

        Args:
            bak_date (str, optional): Last time a backup of the project was created/updated. Defaults to ''.
        """
        if self.images[0] is None: 
            self.lowerbar_vars['mode'].set(_('Mode') + ':  ' + _('No project started'))
            self.lowerbar_vars['creation'].set(_('Creation') + ':  ' + _('No date'))
            self.lowerbar_vars['last_mod'].set(_('Last modified') + ':  ' + _('No date'))
            self.lowerbar_vars['lastbak'].set(_('Last backup') + ':  ' + _('No backup'))
            self.lowerbar_vars['imgdir'].set(_('Image directory') + ':  ' + _('No directory selected'))
            self.lowerbar_vars['marksdir'].set(_('Marks directory') + ':  ' + _('No marks saved'))
            return
        self.lowerbar_vars['mode'].set(_('Mode') + ':  ' + self.images[0].mode.capitalize())
        self.lowerbar_vars['creation'].set(_('Creation') + ':  ' + self.images[0].date_create)
        self.lowerbar_vars['imgdir'].set(_('Image directory') + ':  ' + self.images[0].directory)
        self.tooltips['imgdir'].text = self.images[0].directory
        if self.images[0].date_last != '':
            self.lowerbar_vars['last_mod'].set(_('Last modified') + ':  ' + self.images[0].date_last)
            self.lowerbar_vars['marksdir'].set(_('Marks directory') + ':  ' + self.loader.last_saved_dir)
            self.tooltips['marksdir'].text = self.loader.last_saved_dir
        if bak_date != '':
            self.lowerbar_vars['lastbak'].set(_('Last backup') + ':  ' + bak_date)


# ========================================================== #
# ========================================================== #

#* Fully documented
class Sidebar(tkb.Frame):
    """Class object for management and display of object categories.
    """
    def __init__(self, mestre: DisplayMaker) -> None:
        """Class object for management and display of object categories.

        Args:
            mestre (DisplayMaker): _description_
        """
        super().__init__(master=mestre, 
                         borderwidth=5, 
                         relief='ridge', 
                         width=200)
        self.mestre = mestre
        self.window = mestre.mestre
        self.images = mestre.images
        
        for i in range(2):
            self.rowconfigure(i, weight=1) 
        for i in range(4):
            self.columnconfigure(i, weight=1)
        self.columnconfigure(4, weight=0)
        
        self.grid(column=0, row=0, 
                  sticky='nsew',
                  padx=(5, 2), pady=(5, 0))
        
        self.tree_contructor()
        self.adder_constructor()
    
    # ---------------------------------------------------------- #
    
    def tree_contructor(self) -> None:
        """Constructs the treeview table to display the object categories.
        """
        col_data = {
            'color': (50, 'w', True, _('Color')),
            'sel': (20, 'center', False, ''),
            'id': (40, 'w', False, 'ID'),
            'category': (150, 'w', True, _('Category')),
            'num': (40, 'e', False, 'N°'),
            'vis': (40, 'center', False, 'Vis'),
        }
        
        self.color_table = tkb.Treeview(self, columns=list(col_data.keys())[0], show='headings')
        self.val_table = tkb.Treeview(self, columns=list(col_data.keys())[1:], show='headings')
        
        self.color_table.column('color', 
                                width=col_data['color'][0],
                                anchor=col_data['color'][1], # type: ignore
                                stretch=col_data['color'][2]) 
        self.color_table.heading('color', text=col_data['color'][3])
        for col, data in list(col_data.items())[1:]:
            self.val_table.column(col, 
                                  width=data[0],
                                  anchor=data[1], # type: ignore
                                  stretch=data[2])
            self.val_table.heading(col, text=data[3])
        
        self.update_item_color()
        
        self.color_table.grid(column=0, row=0, rowspan=2, sticky='nsew', pady=(0, 3))
        self.val_table.grid(column=1, columnspan=4, row=0, rowspan=2, sticky='nsew', pady=(0, 3))
    
    def update_item_color(self) -> None:
        """Sets and updates the background color of each line in the treeview table.
        """
        background1 = self.window.style.configure('EasyMark.Treeview.itemcolor')['background1']
        background2 = self.window.style.configure('EasyMark.Treeview.itemcolor')['background2']
        self.val_table.tag_configure('True', background=background1)
        self.val_table.tag_configure('False', background=background2)
    
    def _create_example_categories(self, quant: int):
        """Debug function. Creates a set of randomly-generated categories for testing.

        Args:
            quant (int): Quantity of categories to be created.
        """
        for i in range(quant):
            hex_code = f'#{randint(0, 255):02x}{randint(0, 255):02x}{randint(0, 255):02x}'            
            category_name = ''.join(randchoices(ascii_lowercase, k=randint(5, 15)))
            self.add_category(category_name=category_name, hex_code=hex_code)

    # ---------------------------------------------------------- #

    def adder_constructor(self) -> None:
        """Constructs the new category input section.
        """
        self.hex_var = tkb.StringVar(value=self.window.style.configure('EasyMark.ColorDisplay1.TFrame')['background'])
        name_var = tkb.StringVar(value=_('Category name'))

        color_frame = tkb.Frame(master=self, width=30, height=29,relief='groove', borderwidth=2,
                                style='EasyMark.ColorDisplay1.TFrame')
        ToolTip(color_frame, text=_('Pick a color'))
        name_entry = tkb.Entry(master=self,
                               textvariable=name_var,
                               name='category_name_entry',
                               style='EasyMark.Base.TEntry')
        add_button = tkb.Button(master=self, 
                                text=_('Add category'), 
                                command= lambda *x: \
                                    self.add_category(category_name=name_var.get(), hex_code=self.hex_var.get())
                                )
        
        color_frame.grid(column=0, row=2, sticky='new')
        name_entry.grid(column=1, columnspan=3, row=2, sticky='new', padx=2)
        add_button.grid(column=4, row=2, sticky='new')
        
        
        name_var.trace_add('write', callback= lambda*x: self.validate_name(name_entry, name_var))
        
        color_frame.bind('<Button-1>', lambda *x: self.choose_color())
        name_entry.bind("<FocusOut>", lambda *x: self.validate_name(name_entry, name_var))
        name_entry.bind("<FocusIn>", lambda *x: self.validate_name(name_entry, name_var))
        name_entry.bind("<KeyRelease-Return>", lambda *x: \
                                    self.add_category(category_name=name_var.get(), 
                                                   hex_code=self.hex_var.get()))
        
        self.validate_name(name_entry, name_var)

    def validate_name(self, name_entry: tkb.Entry, name_var: tkb.StringVar) -> None:
        """Checks if the entered category name is valid (not previously used) and updates entry styling accordingly.

        Args:
            name_entry (tkb.Entry): Entry object.
            name_var (tkb.StringVar): Tkinter variable in which the name is stored
        """
        name = name_var.get()
        name_entry.configure(style='EasyMark.Active.TEntry')
        if self.window.focus_get() != name_entry:
            if name == '':
                name_entry.configure(style='EasyMark.Base.TEntry')
                name_var.set(_("Category name"))
                return 
            if name == _("Category name"):
                name_entry.configure(style='EasyMark.Base.TEntry')
                return
        if name in [self.val_table.set(row, 'category') 
                    for row in self.val_table.get_children()]:
            name_entry.configure(style='EasyMark.Active.TEntry')
        if name == _("Category name"):
            name_var.set('')
        name_entry.configure(style='EasyMark.Active.TEntry')

    def choose_color(self) -> None:
        """Prompts the user to choose a color from a color picker.
        """
        color_picker = ColorDialog(title=_("Color Picker"))
        color_picker.show()
        color = color_picker.result
        if color is None: return
        hex_code = color.hex
        WINDOW.style.configure('EasyMark.ColorDisplay1.TFrame', background=hex_code)
        self.hex_var.set(hex_code)

    # ---------------------------------------------------------- #

    def add_category(self, 
                  identifier: Optional[int] = None, 
                  category_name: str = '', 
                  hex_code: str = '', 
                  visible: bool = True,
                  start_index: int | Literal['end'] = 'end', 
                  cat_id: Optional[str] = None) -> None:
        """Adds a new category to the project and treeview table.

        Args:
            identifier (Optional[int], optional): Category positional/numerical id. Defaults to None.
            category_name (str, optional): Category name. Defaults to ''.
            hex_code (str, optional): Category color hex code. Defaults to ''.
            visible (bool, optional): Category visibility status. Defaults to True.
            start_index (int | Literal[&#39;end&#39;], optional): Category position in the treeview table. Defaults to 'end'.
            cat_id (Optional[str], optional): Category unique identifier. Defaults to None.
        """
        if self.images[0] is None or self.mestre.ann_in_progress: return
        
        rand_hex = f'#{randint(0, 255):02x}{randint(0, 255):02x}{randint(0, 255):02x}'
        self.hex_var.set(rand_hex)
        self.window.style.configure('EasyMark.ColorDisplay1.TFrame', background=rand_hex)
        
        if category_name in [self.val_table.set(row, 'category') 
                        for row in self.val_table.get_children()]: return
        
        new_category = cat_id is None
        if new_category:
            cat_id = "".join(randchoices(LETTERS1, k=6))
            while cat_id in list(self.images[0].categories.keys()):
                cat_id = "".join(randchoices(LETTERS1, k=6))
        
        self.color_table.insert(parent='', index=start_index, values=[''], tags=(cat_id, hex_code))
        self.color_table.tag_configure(cat_id, background=hex_code)
        
        item = self.val_table.insert(parent='', index=start_index)
        index = self.val_table.index(item)
        
        self.val_table.item(item, tags=[cat_id, f'{index %2 == 0}'],
                            values=(
                                    f'{'X' if len(self.images[0].categories) == 0 else ''}', 
                                    int(f'{index if identifier is None else identifier}'), 
                                    category_name, 
                                    0,
                                    'V'
                                )
                            )
        if len(self.images[0].categories) == 0: self.select_mark(item)
        
        if (new_category or start_index != 'end'):
            self.images[0].update_categories(cat_id, 
                                          {'id': int(f'{index if identifier is None else identifier}'), 
                                           'name': category_name, 
                                           'hex': hex_code, 
                                           'visible': visible})
        if start_index == 'end': 
            self.mestre.add_action('added_categories', [cat_id])
        else: 
            self.check_pos()

    def delete_categories(self, 
                       selection: bool = True, 
                       cat_ids: list[str] | tuple[str, ...] | None = None, 
                       direct_command: bool = True
                       ) -> tuple[dict[str, list[CategoryDataType]], list[Annotation]] | None:
        """Deletes categories from the project.

        Args:
            selection (bool, optional): If the annotations to be deleted are user-selected. Defaults to True.
            cat_ids (list[str] | tuple[str, ...] | None, optional): Category unique ids to be deleted. Defaults to None.
            direct_command (bool, optional): If the function call was user made. Defaults to True.

        Returns:
            redo_data (tuple[dict[str, list[CategoryDataType]], list[Annotation]] | None): Tuple containing data of all deleted categories and related deleted annotations. Used by actions to create re-actions. 
        """
        x, y = self.winfo_pointerxy()
        widget = self.winfo_containing(x, y)
        if ('treeview' not in str(widget) and selection) or self.mestre.ann_in_progress: return
        
        if selection:
            deletion = self.val_table.selection()
            if len(deletion) == 0: return
            deletion = {self.val_table.item(item_id)['tags'][0] : item_id for item_id in deletion}
        elif not direct_command: 
            assert cat_ids is not None
            deletion = {cat_id : self.val_table.tag_has(cat_id)[0] for cat_id in cat_ids}
        else:
            assert cat_ids is not None
            deletion = [self.val_table.tag_has(cat_id)[0] for cat_id in cat_ids]
            if len(deletion) == 0: return
            deletion = {self.val_table.item(item_id)['tags'][0] : item_id for item_id in deletion}
        
        if direct_command:
            confirm = messagebox.askyesno(title=_('Delete Category'),
                                          message=_('Deleting the category will also delete all related annotations') + '\n' +
                                                  _('Do you want to proceed? (This action is reversible)'))
            if not confirm: return
        
        assert self.images[0] is not None
        redo_objects: list[Annotation] = []
        redo_categories: dict[str, list[Any]] = {}
        for cat_id in deletion.keys():
            redo_categories[cat_id] = list(self.images[0].categories.pop(cat_id).values()) + [self.val_table.index(deletion[cat_id])]
            if direct_command: redo_objects += MAIN.remove_annotations(cat_id, False)
            
        for item_id in deletion.values():
            self.val_table.delete(item_id)
            self.color_table.delete(item_id)
        
        self.check_pos()
        
        if not direct_command: return redo_categories, redo_objects
        else: 
            self.mestre.add_action('deleted_categories', redo_categories, redo_objects)

    def check_pos(self, items: Optional[tuple[str, ...]] = None, index: Optional[int] = None) -> None:
        """Recursevely checks the position of each category. Updates tags and numerical id accordingly.

        Args:
            items (Optional[tuple[str, ...]], optional): Tuple contaning the internal id of each treeview item. Defaults to None.
            index (Optional[int], optional): Index position of the recursive call. Defaults to None.
        """
        if items is None:
            items = self.val_table.get_children()
            self.check_pos(items, 0)
        elif index == len(items): 
            assert self.images[0] is not None
            self.images[0].sort_categories()
        else:
            assert index is not None
            item = items[index]
            val_data = self.val_table.item(item)
            
            assert self.images[0] is not None
            self.val_table.item(item,
                                values = (
                                    val_data['values'][0],
                                    index,
                                    val_data['values'][2],
                                    val_data['values'][3],
                                    val_data['values'][4]
                                ),
                                tags= [tag if ("True" != tag or "False" != tag)
                                        else f'{index %2 == 0}'
                                        for tag in val_data['tags']])
            self.images[0].categories[val_data['tags'][0]]['id'] = index
            
            self.check_pos(items, index+1)
        
            if len(self.val_table.tag_has('marker')) == 0:
                self.select_mark(items[0])

    def readd_categories(self) -> None:
        """Re-adds categories loaded from the project.
        """
        assert self.images[0] is not None
        if len(self.images[0].categories) == 0: return
        for identifier, data in self.images[0].categories.items():
            self.add_category(*list(data.values()), cat_id=identifier) #type: ignore
        self.check_pos()

    def select_mark(self, marker_id: str) -> None:
        """Updates the marker position indicating the selected category for annotation.

        Args:
            marker_id (str): Internal table id of the item to receive the marker
        """
        val_markers = self.val_table.tag_has('marker')
        for row in val_markers:
            val_data = self.val_table.item(row)
            self.val_table.item(row, 
                                values= [''] + list(val_data['values'][1:]),
                                tags= [tag for tag in val_data['tags'] if tag != 'marker'])
        
        val_data = self.val_table.item(marker_id)
        self.val_table.item(marker_id, 
                            values= ['X'] + list(val_data['values'][1:]),
                            tags= list(val_data['tags']) + ['marker'])
    
    # ---------------------------------------------------------- #
    
    def categories_menu(self, event: tk.Event) -> None:
        """Constructs the popup menu when right-clicking a category

        Args:
            event (tk.Event): Tkinter click event.
        """
        categories_menu = tkb.Menu(master=self, tearoff=0, relief='raised')
        selection=self.val_table.selection()
        if len(selection) == 0: return
        elif len(selection) == 1:
            cat_id = self.val_table.item(selection[0], 'tags')[0]
            visible = self.val_table.item(selection[0], 'values')[-1] == 'V'
            
            categories_menu.add_command(label=_('Edit category'), 
                                        command= lambda *x: \
                                            EditCategory(self, cat_id))
            categories_menu.add_command(label='\u25b2'+_(' Move up'), 
                                        command= lambda *x: \
                                            self.move_category(selection[0], 'up'))
            categories_menu.add_command(label="\u25bc"+_(' Move down'), 
                                        command= lambda *x: \
                                            self.move_category(selection[0], 'down'))
        assert self.images[0] is not None
        if self.images[0].mode == 'manual':
            visible = sum([self.val_table.item(sel, 'values')[-1] == 'V' for sel in selection]) != 0
            hide_label = _('Hide category') if visible and len(selection) == 1 else _('Hide categories') if visible \
                    else _('Unhide category') if len(selection) == 1 else _('Unhide categories')
            categories_menu.add_command(label=hide_label, command= lambda *x: self.hide_categories(selection, visible))
        categories_menu.add_command(label=_('Delete category') if len(selection) == 1 else _("Delete categories"), 
                                    command=lambda *x: self.delete_categories(False, selection))
        
        categories_menu.tk_popup(event.x_root, event.y_root)
    
    def move_category(self, 
                      item: str, 
                      to: Literal['up', 'down'] | int, 
                      direct_command: bool = True
                      ) -> tuple[str, int, str, str] | None:
        """Moves the selected category to a new position.

        Args:
            item (str): Internal treeview table id of the item to be moved.
            to (Literal[&#39;up&#39;, &#39;down&#39;] | int): Position to move the category. 
            direct_command (bool, optional): If the function call was user made. Defaults to True.

        Returns:
            tuple[str, int, str, str] | None: _description_
        """
        cur_index = self.val_table.index(item)
        num_categories = len(self.val_table.get_children())
        if isinstance(to, int): 
            if 0 > to: to = 0
            elif to > num_categories-1: to = num_categories-1
            index = to
        elif to == 'down':
            index = 0 if cur_index+1>=num_categories else cur_index+1
        elif to == 'up':
            index = num_categories-1 if cur_index <= 0 else cur_index-1
        else: return
        
        self.val_table.move(item, "", index)
        self.color_table.move(item, "", index)
        
        self.check_pos()
        
        cat_id: str = self.val_table.item(item, 'tags')[0]
        category_color: str = self.color_table.item(item, 'tags')[1]
        category_name: str = self.val_table.item(item, 'values')[2]
        reverse_action = cat_id, cur_index, category_name, category_color
        if direct_command:
            self.mestre.add_action('edited_category', reverse_action)
        else:
            return reverse_action      
    
    def hide_categories(self, selection: tuple[str, ...], visible: bool) -> None:
        """Toggles visibility of a category and related annotations.

        Args:
            selection (tuple[str, ...]): Internal treeview table ids with the selected items to be updated.
            visible (bool): Visibility setting.
        """
        assert self.images[0] is not None
        for item in selection:
            values = self.val_table.item(item, 'values')
            cat_id = self.val_table.item(item, 'tags')[0]
            self.images[0].categories[cat_id]['visible'] = not visible
            self.val_table.item(item, values = list(values[:-1]) + ['I' if visible else 'V'])
            MAIN.change_annotation_color(cat_id)
        MAIN.redraw_annotations_fromimage()
        
    # ---------------------------------------------------------- #
    
    def reset_count(self) -> None:
        """Resets the annotation counter of all categories on the treeview table.
        """
        for item in self.val_table.get_children():
            values = self.val_table.item(item, 'values')
            self.val_table.item(item, values=(*values[:3], 0, values[4]))
    
    def binds(self, canvas: tkb.Canvas) -> None:
        """Sets the necessary binds for setting the category for annotation and deleting categories. 

        Args:
            canvas (tkb.Canvas): Reference to the image canvas.
        """
        canvas.bind('<MouseWheel>', self.set_marker)
        canvas.bind('<Button>', self.set_marker)
        self.window.bind('<KeyRelease-Delete>', lambda *x: self.delete_categories())
        
        for table in [self.color_table, self.val_table]:
            table.bind('<MouseWheel>', self.synchronized_tables)
            table.bind('<ButtonRelease>', lambda e, x=table: self.handle_event(e, x))
            table.bind('<Motion>', lambda e, x=table: self.handle_event(e, x))
            table.bind('<Double-Button-1>', lambda e, x=table: self.handle_event(e, x, True))
            
    def handle_event(self, 
                     event: tk.Event, 
                     table: tkb.Treeview, 
                     double: bool = False
                     ) -> None:
        """Handler for events on the treeview table.

        Args:
            event (tk.Event): Tkinter click event.
            table (tkb.Treeview): Reference to the table that hosted the event.
            double (bool, optional): Determines if it was a double click. Defaults to False.
        """
        if self.images[0] is None or self.mestre.ann_in_progress: return
        e = str(event).lower()
        if ('motion' in e or ('button' in e and 'num=1' in e)) \
            and table.identify_region(event.x, event.y) == 'separator':
            return
        self.synchronized_tables(event)
        if 'num=3' in e: 
            self.categories_menu(event)
            return
        if double: self.set_marker(event)
    
    def synchronized_tables(self, event: tk.Event) -> None:
        """Synchronizes the position of both treeview tables.

        Args:
            event (tk.Event): Tkinter click event.
        """
        e = str(event).lower()
        x, y = self.winfo_pointerxy()
        widget = self.winfo_containing(x, y)
        if widget == self.color_table:
            main, inherit = self.color_table, self.val_table
        elif widget == self.val_table:
            main, inherit = self.val_table, self.color_table
        else: return
        
        if 'button' in e and 'num=1' in e or 'num=3' in e:
            selected = main.selection()
            inherit.selection_set(selected)
            self.color_table.selection_remove(selected)
                
        elif 'mousewheel' in e or ('button' in e and 'num=4' in e or 'num=5' in e):
            inherit.yview_moveto(main.yview()[0])

    def set_marker(self, event: tk.Event) -> None:
        """Sets the selection marker on a given treeview table item.

        Args:
            event (tk.Event): Tkinter click event.
        """
        if self.images[0] is None or self.mestre.ann_in_progress: return
        if len(self.images[0].categories) == 0: return
        e = str(event).lower()
        if 'mousewheel' in e:
            check_up = event.delta > 0
            check_down = event.delta < 0
        elif 'button' in e and 'num=4' in e or 'num=5' in e:
            check_up = event.num == 4
            check_down = event.num == 5
        else:
            check_up = None
            check_down = None
        
        if check_up is not None:
            val_markers = self.val_table.tag_has('marker')
            if len(val_markers) == 0: 
                marker_id = self.val_table.get_children()[0]
            elif check_up:
                prev_marker = self.val_table.prev(val_markers[0])
                marker_id = self.val_table.get_children()[-1] if prev_marker == '' \
                            else prev_marker
            elif check_down:
                next_marker = self.val_table.next(val_markers[0])
                marker_id = self.val_table.get_children()[0] if next_marker == '' \
                            else next_marker
            else:
                marker_id = self.val_table.get_children()[0]
        else:
            selected = self.val_table.selection()
            if len(selected) != 1: return
            marker_id = selected[0]
        self.select_mark(marker_id)
            
    # ---------------------------------------------------------- #
    
    def _update(self) -> None:
        """Third step on the update cascade."""
        if self.images[0] is not None:
            self.readd_categories()
        else:
            self.val_table.delete(*self.val_table.get_children())
            self.color_table.delete(*self.color_table.get_children())
        self.update_item_color()
        
#* Fully documented
class EditCategory(tkb.Toplevel):
    """Pop up window for editing annotation categories.
    """
    def __init__(self, mestre: Sidebar, cat_id: str) -> None:
        """Pop up window for editing annotation categories.

        Args:
            mestre (Sidebar): Sidebar frame.
            cat_id (str): cat_id of the annotation category to be edited.
        """
        self.mestre = mestre
        self.display = mestre.mestre
        self.main = self.display.main
        self.window = mestre.window
        
        x = self.window.winfo_rootx() + self.mestre.winfo_width()
        y = self.window.winfo_pointerxy()[1] - 20
        
        super().__init__(title=_("Edit category"), 
                         resizable=(False, False),
                         position=(x, y))
        
        self.images = mestre.images
        assert self.images[0] is not None
        self.val_table = mestre.val_table
        self.color_table = mestre.color_table
        
        self.cat_id = cat_id
        self.cur_category = self.images[0].categories[cat_id].copy()
        WINDOW.style.configure('EasyMark.ColorDisplay2.TFrame', background=self.cur_category['hex'])
        
        base = tkb.Frame(master=self, 
                         padding=2, 
                         relief='groove', 
                         borderwidth=3)
        base.pack(expand=True, fill='both')
        
        for i in range(4):
            base.columnconfigure(i, weight=1)
        base.rowconfigure(0, weight=1)
        base.rowconfigure(1, weight=1)
        
        self.edit_contructor(base)
        self.binds()
        base_toplevel_binds(self)
    
    def edit_contructor(self, base: tkb.Frame) -> None:
        """Constructor for the main widgets in the pop up.

        Args:
            base (tkb.Frame): Base frame.
        """
        self.hex_var = tkb.StringVar(value=self.cur_category['hex'])
        self.name_var = tkb.StringVar(value=self.cur_category['name'])
        self.id_var = tkb.StringVar(value=str(self.cur_category['id']))

        self.color_frame = tkb.Frame(master=base, 
                                     width=30,
                                     height=29,
                                     relief='groove', 
                                     borderwidth=2,
                                     style='EasyMark.ColorDisplay2.TFrame')
        self.name_entry = tkb.Entry(master=base,
                                    textvariable=self.name_var)
        self.id_entry = tkb.Entry(master=base,
                                  textvariable=self.id_var)
        
        cancel_button = tkb.Button(master=base,
                                   text=_("Cancel"),
                                   command= lambda *x: self.destroy())
        edit_button = tkb.Button(master=base, 
                                text=_('Confirm edit'),
                                command= lambda *x: \
                                    self.edit_category()
                                )
        
        self.color_frame.grid(column=0, row=0, sticky='new', pady=(0, 3))
        self.name_entry.grid(column=1, columnspan=2, row=0, sticky='new', padx=2, pady=(0, 3))
        self.id_entry.grid(column=3, row=0, sticky='new', pady=(0, 3))
        cancel_button.grid(column=2, row=1, sticky='sew')
        edit_button.grid(column=3, row=1, sticky='sew')
        
        self.validate('name')
        self.validate('id')
    
    def get_color(self) -> None:
        """Opens the color prompt.
        """
        self.grab_release()
        color_chooser = ColorDialog(title=_("Color Chooser"))
        color_chooser.show()
        self.grab_set()
        color = color_chooser.result
        if color is None: return
        hex_code = color.hex
        WINDOW.style.configure('EasyMark.ColorDisplay2.TFrame', background=hex_code)
        self.hex_var.set(hex_code)
    
    def validate(self, mode: Literal['name', 'id']) -> None:
        """Validates the given name or id for edition.

        Args:
            mode (Literal[&#39;name&#39;, &#39;id&#39;]): Validation mode.
        """
        if mode =='id':
            entry, var, val = self.id_entry, self.id_var, self.id_var.get()
            check = self.check_id
        elif mode == 'name':
            entry, var, val = self.name_entry, self.name_var, self.name_var.get()
            check = self.check_name
            
        entry.configure(style='default.TEntry')
        if self.focus_get() != entry:
            if val == '':
                entry.configure(foreground='#bbbbbb')
                var.set(str(self.cur_category[mode]))
                return
            if val == str(self.cur_category[mode]):
                entry.configure(foreground='#bbbbbb')
                return
        else:
            entry.configure(foreground='#ffffff')
        if check(val):
            entry.configure(style='danger.TEntry')
    
    def check_name(self, name: str) -> bool:
        """Checks if the name given doesn't already exist.

        Args:
            name (str): Name to be checked.

        Returns:
            valid (bool): Valid name.
        """
        return name != self.cur_category['name'] and \
               name in [self.val_table.set(row, 'category') 
                       for row in self.val_table.get_children()]
    
    def check_id(self, id: str) -> bool:
        """Checks if the given id is within the number of categories.

        Args:
            id (str): Id tp be checked.

        Returns:
            valid (bool): Valid id.
        """
        if id == '': return True
        try:
            assert self.images[0] is not None
            return 0 > int(id) > len(self.images[0].categories)
        except ValueError:
            return False

    def edit_category(self) -> None:
        """Executes the given edits.
        """
        hex_val, name_val, id_val = self.hex_var.get(), self.name_var.get(), self.id_var.get()
        assert self.images[0] is not None
        
        if self.check_id(id_val): return
        else: id_val = int(id_val)
        if self.check_name(name_val): return
        
        if [hex_val, name_val, id_val] == list(self.cur_category.values()): return
        
        category_undo = self.cat_id, *[str(value) for value in self.cur_category.values()]
        self.images[0].categories[self.cat_id].update({'hex': hex_val, 'name': name_val, 'id': id_val})
        
        item = self.val_table.tag_has(self.cat_id)[0]

        if name_val != self.cur_category['name']: 
            values = self.val_table.item(item, 'values')
            self.val_table.item(item, 
                                values=[
                                    values[0],
                                    values[1],
                                    name_val,
                                    values[3],
                                    values[4]
                                ])
        if id_val != self.cur_category['id']: 
            self.mestre.move_category(item, id_val, False)
        if hex_val != self.cur_category['hex']: 
            self.color_table.tag_configure(self.cat_id, background=hex_val)
            item = self.color_table.tag_has(self.cat_id)
            self.color_table.item(item[0], tags=(self.cat_id, hex_val))
            self.main.change_annotation_color(self.cat_id)
        
        self.display.add_action('edited_category', category_undo)
        self.destroy()
        
    def binds(self) -> None:
        """Pop up keybinds.
        """
        self.color_frame.bind('<Button-1>', lambda *x: self.get_color())
        self.name_entry.bind("<FocusIn>", lambda *x: self.validate('name'))
        self.name_entry.bind("<FocusOut>", lambda *x: self.validate('name'))
        self.id_entry.bind("<FocusIn>", lambda *x: self.validate('id'))
        self.id_entry.bind("<FocusOut>", lambda *x: self.validate('id'))
        
        self.name_var.trace_add('write', callback= lambda*x: self.validate('name'))
        self.id_var.trace_add('write', callback= lambda*x: self.validate('id'))
        
        
        self.bind("<ButtonPress>", self._unfocus)
        self.bind("<KeyRelease-Return>", lambda *x: \
                                            self.edit_category())
    
    def _unfocus(self, *_) -> None:
        """Forces focus out of an entry widget.
        """
        x, y = self.winfo_pointerxy()
        widget = self.winfo_containing(x, y)
        if 'entry' not in str(widget): self.focus()


# ========================================================== #
# ========================================================== #

#! Needs doc update
class MainVisualizer(tkb.Frame):
    """Category for handling the image display and it's peripherals, object annotation and it's functions.
    """
    
    def __init__(self, mestre: DisplayMaker) -> None:
        """
        Category for handling the image display and it's peripherals, object annotation and it's functions.
        
        Args:
            mestre (DisplayMaker): The Displaycategory frame that holds the Main Visualizer.
        """
        super().__init__(master=mestre, borderwidth=5, relief='ridge')
        self.mestre = mestre
        self.window = mestre.mestre
        self.images = mestre.images
        self.val_table = mestre.side.val_table
        self.color_table = mestre.side.color_table
        
        self.cur_image: Optional[AnnImage] = None
        self.popup_open = False
        self.active_tool: tkb.StringVar = tkb.StringVar(value='')
        self.tool_icons = [get_icon(f'{icon}tool') for icon in ['move', 'bbox', 'obbox', 'poly']]
        self.larrow_icon = get_icon('larrow')
        self.rarrow_icon = get_icon('rarrow')
        
        self.last_window_size = (1, 1)
        self.last_image_size = (1, 1)
        self.last_image_ratio = (1, 1)
        self.last_image_name = ''
        self.last_index = 0
        
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)
        
        self.grid(column=1, row=0, rowspan=2, 
                  sticky='nsew',
                  padx=5, pady=5)
        
        self.page_display()
        self.image_display()
        self.refresh()
        
        self.binds()
    
    # ---------------------------------------------------------- #
    #* Page bar
    
    def page_display(self) -> None:
        """Constrcuts the bottom bar containing image name, current position out of total images and movement arrows.
        """
        page_frame = tkb.Frame(master=self)
        page_frame.columnconfigure(0, weight=1)
        page_frame.rowconfigure(0, weight=1)
        page_frame.grid(column=0, row=1, sticky='nsew', pady=4)
        
        self.top_display: list[tkb.StringVar] = [
            tkb.StringVar(value=_("No images loaded")),
            tkb.StringVar(value='0'),
            tkb.StringVar(value='/0')
        ]
        
        image_name = tkb.Label(master=page_frame, textvariable=self.top_display[0], justify='right', anchor='w')
        sub_page_frame   = tkb.Frame(master=page_frame)
        self.button_prev = tkb.Button(sub_page_frame, image=self.larrow_icon, command= lambda *x: self.skip_image('prev'), style="Outline.TButton")
        image_index      = tkb.Entry(master=sub_page_frame, textvariable=self.top_display[1], width=5, justify='right')
        total_images     = tkb.Label(master=sub_page_frame, textvariable=self.top_display[2], justify='left', anchor='w')
        self.button_next = tkb.Button(sub_page_frame, image=self.rarrow_icon, command= lambda *x: self.skip_image('next'), style="Outline.TButton")

        image_name.pack(side='left', pady=8)
        
        sub_page_frame.place(in_=page_frame, anchor='center', relx=0.5, rely=0.5)
        self.button_prev.pack(side='left', padx=5, ipadx=0)
        image_index.pack(side='left')
        total_images.pack(side='left')
        self.button_next.pack(side='left', padx=5, ipadx=0)
        
        image_index.bind('<Return>', func= lambda *x: self.check_index())
        image_index.bind('<FocusOut>', func= lambda *x: self.check_index())
        
    def check_index(self) -> None:
        """Checks if the index given is a valid index, jumping to the corresponding image if valid or resetting it's value if invalid.
        """
        new_index = self.top_display[1].get()
        try:
            new_index = int(new_index)
            if self.images[0] is None: raise ValueError
            if 0 >= new_index > len(self.images[0]): raise ValueError
            
            if new_index == self.last_index: return
            
            self.skip_image(new_index-1)
            self.last_index = new_index
        except ValueError: 
            self.top_display[1].set(f"{self.last_index}")
    
    def update_values(self) -> None:
        """Updates the displayed text and values.
        """
        if self.cur_image is None or self.images[0] is None: 
            self.top_display[0].set(value=_("No images loaded"))
            self.top_display[1].set('0')
            self.top_display[2].set(value='/0')
        else:
            self.top_display[0].set(value=f'{self.cur_image.name}')
            self.top_display[1].set(f"{self.cur_image.index+1}")
            self.top_display[2].set(value=f' / {len(self.images[0])}')
    
    def update_icons(self) -> None:
        """Updates the loaded arrow icons when switching themes.
        """
        self.larrow_icon = get_icon('larrow')
        self.rarrow_icon = get_icon('rarrow')
        self.button_prev.config(image=self.larrow_icon)
        self.button_next.config(image=self.rarrow_icon)
        
        self.update_toolbar_icons()
    
    # ---------------------------------------------------------- #
    #* Image/annotation display
    
    def image_display(self) -> None:
        """Constructs the tkinter canvas in which all following functions work upon.
        """
        self.image_frame = tkb.Frame(master=self, relief='groove', borderwidth=5, style='EasyMark.ImageDisplay.TFrame')
        self.image_frame.columnconfigure(0, weight=1)
        self.image_frame.rowconfigure(0, weight=1)
        self.image_frame.grid(column=0, row=0, sticky='nsew')
        
        self.canvas = tkb.Canvas(master=self.image_frame, confine=True)
        self.canvas.pack(fill='both', expand=True)
        self.toolbar_display()
        
        background_color = self.window.style.configure('EasyMark.ImageDisplay.TFrame')['background']
        text_color = self.window.style.configure('EasyMark.DataDisplay.TLabel')['foreground']
        self.canvas.create_rectangle(0, 0, self.image_frame.winfo_width(), self.image_frame.winfo_height(), fill=background_color, outline='', tags=['bg'])
        self.canvas.create_text((370, 212), text=_('No images loaded'), justify='center', anchor='center', fill=text_color, tags=['text'])
    
    def toolbar_display(self) -> None:
        """Constructs the floating tool bar with the different manual annotation options.
        """
        self.toolbar_frame = tkb.Frame(master=self.canvas, relief='raised', padding=2)
        for i in range(4): self.toolbar_frame.columnconfigure(i, weight=0)
        self.toolbar_frame.rowconfigure(0, weight=1)
        
        self.handle = tkb.Button(master=self.toolbar_frame, image=self.tool_icons[0], style='Link.Button')
        sel_bbox = tkb.Button(master=self.toolbar_frame, image=self.tool_icons[1], style='Outline.TButton')
        sel_obbox = tkb.Button(master=self.toolbar_frame, image=self.tool_icons[2], style='Outline.TButton')
        sel_poly = tkb.Button(master=self.toolbar_frame, image=self.tool_icons[3], style='Outline.TButton')
        self.tool_buttons = {sel_bbox: 'bbox', sel_obbox: 'obbox', sel_poly: 'poly'}
        for i, tool in enumerate(self.tool_buttons.keys()):
            tool.config(command= lambda x=i, *y: self.change_active_tool(x))
            
        
        self.handle.grid(row=0, column=0, sticky='wsn', pady=2)
        sel_bbox.grid(row=0, column=1, sticky='wsn', padx=2, pady=2)
        sel_obbox.grid(row=0, column=2, sticky='wsn', padx=2, pady=2)
        sel_poly.grid(row=0, column=3, sticky='wsn', padx=2, pady=2)
        
        self.handle.bind('<B1-Motion>', lambda *e: self.move_toolbar())
    
    def change_active_tool(self, active_tool: int | str) -> None:
        """Handles switching the active manual annotation tool

        Args:
            active_tool (int | str): Tool numerical index or name to be turned on.
        """
        if self.mestre.ann_in_progress: return
        
        for i, toolmode in enumerate(self.tool_buttons.items()):
            if i != active_tool and toolmode[1] != active_tool: toolmode[0].config(style='Outline.TButton')
            else:
                toolmode[0].config(style='success.Outline.TButton')
                self.active_tool.set(toolmode[1])
    
    def move_toolbar(self) -> None:
        """Handles moving the floating toolbar and limiting it's position within the image canvas.
        """
        mx, my = self.winfo_pointerx(), self.winfo_pointery()
        cpx, cpy = self.canvas.winfo_rootx(), self.canvas.winfo_rooty()
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        tw, th = self.toolbar_frame.winfo_width(), self.toolbar_frame.winfo_height()
        
        rel_x = 2 if mx-cpx-10 < 2 else cw-tw-2 if mx-cpx-10 > cw-tw-2 else mx-cpx-10
        rel_y = 18 if my-cpy < 18 else ch-int(th/2)-3 if my-cpy > ch-int(th/2)-3 else my-cpy
        self.toolbar_frame.place(in_=self.canvas, anchor='w', x=rel_x, y=rel_y)
    
    def update_toolbarpos(self) -> None:
        """Updates the toolbar position when resizing the window.
        """
        if self.images[0] is None or self.images[0].mode == 'semiauto': 
            self.toolbar_frame.place_forget()
            return
        cpx, cpy = self.canvas.winfo_rootx(), self.canvas.winfo_rooty()
        tpx, tpy = self.toolbar_frame.winfo_rootx(), self.toolbar_frame.winfo_rooty()
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        tw, th = self.toolbar_frame.winfo_width(), self.toolbar_frame.winfo_height()
        
        rel_x = 2 if tpx-cpx < 2 else cw-tw-2 if tpx-cpx > cw-tw-2 else tpx-cpx
        rel_y = 2 if tpy-cpy < 2 else ch-th-2 if tpy-cpy > ch-th-2 else tpy-cpy
        self.toolbar_frame.place(in_=self.canvas, anchor='nw', x=rel_x, y=rel_y)
    
    def update_toolbar_icons(self) -> None:
        """Updates the option icons when switching themes.
        """
        self.tool_icons = [get_icon(f'{icon}tool') for icon in ['move', 'bbox', 'obbox', 'poly']]
        self.handle.config(image=self.tool_icons[0])
        for i, tool in enumerate(self.tool_buttons.keys()):
            tool.config(image=self.tool_icons[i+1])
    
    def update_image(self, same_size: bool= False) -> None:
        """Handles updating the displayed image and text, alongside annotations.

        Args:
            same_size (bool, optional): Allows an early stop of the function if the update call was not due to window size change. Defaults to False.
        """
        if self.images[0] is None: return
        self.cur_image = self.images[0].cur_image()
        if self.cur_image is None: return
        if self.cur_image.image is None: self.cur_image.load()
        if self.cur_image.name == self.last_image_name and same_size: return
        self.last_image_name = self.cur_image.name
        self.update_values()
        self.keep_image_ratio(self.last_window_size)
        self.draw_image()
        
        self.update_annotations()
    
    def update_background(self) -> None:
        """Updates the background of the image display frame.
        """
        background_color = WINDOW.style.configure('EasyMark.ImageDisplay.TFrame')['background']
        self.canvas.itemconfigure('bg', fill=background_color)
        self.canvas.coords('bg', 0, 0, self.last_window_size[0], self.last_window_size[1])
        
        if self.cur_image is not None: return
        text_coords = self.canvas.bbox('text')
        text_color = WINDOW.style.configure('EasyMark.DataDisplay.TLabel')['foreground']
        newpos = (
            int(self.last_window_size[0]/2 - (text_coords[2] - text_coords[0])/2),
            int(self.last_window_size[1]/2 - (text_coords[3] - text_coords[1])/2)
        )
        self.canvas.moveto('text', newpos[0], newpos[1])
        self.canvas.itemconfigure('text', fill=text_color)
    
    def draw_image(self) -> None:
        """Places the image on the canvas and ensures to remove any previous ones.
        """
        self.canvas.create_image(0, 0, image=self.photo, anchor='nw', tags=['imagem'])
        self.canvas.tag_lower('imagem')
        self.canvas.tag_raise('imagem', 'text')
        img_index = self.canvas.find_withtag('imagem')
        img_qntd = len(img_index)
        if img_qntd <= 1: return
        for i in range(img_qntd-1):
            self.canvas.delete(img_index[i])

    def keep_image_ratio(self, window_size: tuple[int, int]) -> None:
        """Resizes the image according to the window size.

        Args:
            window_size (tuple[int]): Current window size. In the order (height, width).
        """
        assert self.cur_image is not None
        img = self.cur_image.image
        assert img is not None
        
        # All tuples are (width, height)
        img_size = img.size
        htow_ratio = img_size[1] / img_size[0]
        
        new_size = window_size[0], int(window_size[0]*htow_ratio)
        if new_size[1] > window_size[1]:
            new_size = int(window_size[1]/htow_ratio), window_size[1]
        self.last_image_ratio = img_size[0]/new_size[0], img_size[1]/new_size[1]
        
        self.last_image_size = new_size
        self.photo = ImageTk.PhotoImage(img.resize(new_size))

    def clean_canvas(self) -> None:
        """Cleans the canvas.
        """
        if self.images[0] is None or self.cur_image is None: return
        self.mestre.ann_in_progress = False
        items = [item
                  for tag in ['imagem', 'point', 'annotation', 'preview']
                  for item in self.canvas.find_withtag(tag)]
        self.canvas.delete(*items)
    
    # ---------------------------------------------------------- #
    #* Annotation polygons handling
    
    def _draw_point(self, 
                    pos: list[int] | tuple[int, int], 
                    rel_pos: list[float] | tuple[float, float], 
                    point_type: _annTypeGen, 
                    cat_id: str, 
                    annotation_id: Optional[str] = None) -> int:
        """Internal function for drawing points on the canvas.

        Args:
            pos (list[int] | tuple[int, int]): x y position of the point in relation to the canvas.
            rel_pos (list[float] | tuple[float, float]): x y position of the point in relation to the image.
            point_type (Literal[&#39;bbox&#39;, &#39;obbox&#39;, &#39;poly&#39;, &#39;mark&#39;]): Selected annotation mode.
            cat_id (str): Id of the selected object category.
            annotation_id (Optional[str], optional): Preset annotation id. Defaults to None.

        Returns:
            point_id (int): Internal numerical id of the point.
        """
        coords = (pos[0]-6, pos[1]-6, pos[0]+6, pos[1]+6)
        color = self.get_color_by_tagid(cat_id)
        fill = color if point_type == 'mark' else ''
        
        point = self.canvas.create_oval(coords, fill=fill, outline=color, width=2)
        point_id = f'p{point}' if annotation_id is None else annotation_id
        self.canvas.itemconfigure(point, {'tags': ['point', f'{point_type}-point', point_id, f'{rel_pos[0]} {rel_pos[1]}', cat_id]})
        return point
    
    def draw_point(self, pos: tuple[int, int] | list[int], point_type: _annTypeGen, cat_id: Optional[str] = None) -> str | int | None:
        """General function for handling drawing points and any extra actions.

        Args:
            pos (tuple[int, int] | list[int]): x y position of the point in relation to the canvas.
            point_type (Literal[&#39;bbox&#39;, &#39;obbox&#39;, &#39;poly&#39;, &#39;mark&#39;]): Selected annotation mode.
            cat_id (Optional[str], optional): Id of the selected object category. Defaults to None.

        Returns:
            point_id|annotation_id (int | str): Where point_id is the internal numerical id of a point object on canvas and annotation_id is the unique identifier of a completed annotation.
        """
        assert self.cur_image is not None
        if self.active_tool.get() == '': 
            self.change_active_tool(0)
        direct_command = False
        if cat_id == None: 
            direct_command = True
            cat_id = self.get_tagid()
            if cat_id == None: return
        rel_pos = self.coords_rel2image(pos) #type: ignore
        
        used_annids = [ann.annotation_id for ann in self.cur_image.annotations]
        annotation_id = "".join(['P'] + randchoices(LETTERS2, k=10))
        while annotation_id in used_annids:
            annotation_id = "".join(['P'] + randchoices(LETTERS2, k=10))
        
        if point_type == 'mark': 
            point = self._draw_point(pos, rel_pos, point_type, cat_id, annotation_id)
            self.canvas.itemconfigure(point, {'tags': ['annotation'] + list(self.canvas.gettags(point)[1:])})
            self.cur_image.new_annotation(Annotation(annotation_id, cat_id, rel_pos, point_type, point_id=point))
            self.cur_image.store_annotation()
            if direct_command: self.mestre.add_action('added_annotations', [annotation_id])
            return annotation_id
        
        if not self.mestre.ann_in_progress:
            self.mestre.ann_in_progress = True
            point = self._draw_point(pos, rel_pos, point_type, cat_id)
                
            self.cur_image.new_annotation(Annotation(annotation_id, cat_id, rel_pos, point_type, point_id=point))
            self.create_preview(pos, rel_pos, cat_id)
            if direct_command: self.mestre.add_action('added_points', 'last')
            return point
        
        self.canvas.delete(f'{point_type}-preview')
        match point_type:
            case 'bbox': obj = self.continue_bbox(pos, rel_pos, cat_id, direct_command)
            case 'obbox': obj = self.continue_obbox(pos, rel_pos, cat_id, direct_command)
            case 'poly': obj = self.continue_poly(pos, rel_pos, cat_id, direct_command)
        if isinstance(obj, str): 
            self.canvas.delete(f'{point_type}-preview')
        return obj
        
    def continue_bbox(self, pos: list[int] | tuple[int, int], rel_pos: list[float] | tuple[float, float], cat_id: str, direct_command: bool) -> str:
        """Handles the creation of a bounding box annotation object from the points made by the user. \n
        The first point makes one corner while the second makes the opposite corner. All other points are auto-completed.

        Args:
            pos (list[int] | tuple[int, int]): x y position of the point in relation to the canvas.
            rel_pos (list[float] | tuple[float, float]): x y position of the point in relation to the image.
            cat_id (str): Id of the selected object category.
            direct_command (bool): If the function call was originally user made.

        Returns:
            point_id (int): Internal numerical id of a point object on canvas.
        """

        assert self.cur_image is not None
        cur_poly = self.cur_image.wip_ann
        assert cur_poly is not None
        
        annotation_id = cur_poly.annotation_id
        fp_rel_pos = cur_poly.coords
        fp_pos = self.coords_rel2canvas(fp_rel_pos)
        coords = [fp_pos[0], fp_pos[1], pos[0], fp_pos[1], pos[0], pos[1], fp_pos[0], pos[1]]
        rel_coords = [fp_rel_pos[0], fp_rel_pos[1], rel_pos[0], fp_rel_pos[1], rel_pos[0], rel_pos[1], fp_rel_pos[0], rel_pos[1]]
        color = self.get_color_by_tagid(cat_id)
        
        bbox = self.canvas.create_polygon(*coords, outline=color, fill='', width=2)
        self.canvas.itemconfigure(bbox, {'tags': ['annotation', 'bbox', annotation_id, ' '.join([str(coord) for coord in rel_coords]), cat_id]})
        cur_poly.set(coords=rel_coords)
        self.cur_image.store_annotation()
        self.mestre.ann_in_progress = False
        
        self.remove_points('last')
        if direct_command: self.mestre.add_action('finished_annotation', annotation_id)
        return annotation_id

    def continue_obbox(self, pos: list[int] | tuple[int, int], rel_pos: list[float] | tuple[float, float], cat_id: str, direct_command: bool) -> int | str:
        """Handles the creation of an oriented bounding box annotation object from the points made by the user. \n
        The first two points have free range while the third is restrained to a 90° angle. The final point is auto-completed.

        Args:
            pos (list[int] | tuple[int, int]): x y position of the point in relation to the canvas.
            rel_pos (list[float] | tuple[float, float]): x y position of the point in relation to the image.
            cat_id (str): Id of the selected object category.
            direct_command (bool): If the function call was originally user made.

        Returns:
            point_id|annotation_id (int | str): Where point_id is the internal numerical id of a point object on canvas and annotation_id is the unique identifier of a completed annotation.
        """
        assert self.cur_image is not None
        cur_poly = self.cur_image.wip_ann
        assert cur_poly is not None
        
        annotation_id = cur_poly.annotation_id
        pp_rel_pos = tuple(cur_poly.coords[0:4])
        pp_pos = self.coords_rel2canvas(pp_rel_pos)
        color = self.get_color_by_tagid(cat_id)
        
        
        
        if len(cur_poly.point_ids) == 1:
            point = self._draw_point(pos, rel_pos, 'obbox', cat_id)
            cur_poly.point_ids.append(point)
            cur_poly.coords += list(rel_pos)
            self.canvas.create_line(*pp_pos, *pos, fill=color, width=2, tags=('edge', 'obbox-edge', f'd{cur_poly.point_ids[0]}', f'd{point}', ' '.join(str(val) for val in [*pp_pos, *pos]), cat_id))
            self.canvas.tag_lower('obbox-edge', 'obbox-point')
            
            if direct_command: self.mestre.add_action('added_points', 'last')
            return point
        
        elif len(cur_poly.point_ids) == 2:
            if all([isinstance(coord, int) for coord in pos]): x3, y3 = self.fixedline_coords(*pp_pos, *pos)
            else: x3, y3 = pos
            x1, y1, x2, y2 = pp_pos
            x4, y4 = self.final_point(x1, y1, x2, y2, x3, y3)

            coords = pp_pos + [x3, y3, x4, y4]
            rel_coords = list(pp_rel_pos) + self.coords_rel2image([x3, y3, x4, y4])
            
            self.canvas.create_polygon(*coords, outline=color, fill='', width=2, tags=['annotation', 'obbox', annotation_id, ' '.join([str(coord) for coord in rel_coords]), cat_id])
            cur_poly.set(coords=rel_coords)
            self.mestre.ann_in_progress = False
            self.cur_image.store_annotation()
            
            self.remove_points('all')
            if direct_command: self.mestre.add_action('finished_annotation', annotation_id)
            return annotation_id
        else:
            raise Exception(f"Too many point_ids ({cur_poly.point_ids})")
        
    def continue_poly(self, pos: list[int] | tuple[int, int], rel_pos: list[float] | tuple[float, float], cat_id: str, direct_command: bool) -> int | str:
        """Handles the creation of a polygon annotation object from the points made by the user.\n
        There are no restraints in point positioning. The Annotation object is auto-completed when a point is created close to the first point. 

        Args:
            pos (list[int] | tuple[int, int]): x y position of the point in relation to the canvas.
            rel_pos (list[float] | tuple[float, float]): x y position of the point in relation to the image.
            cat_id (str): Id of the selected object category.
            direct_command (bool): If the function call was originally user made.

        Returns:
            point_id|annotation_id (int | str): Where point_id is the internal numerical id of a point object on canvas and annotation_id is the unique identifier of a completed annotation.
        """
        assert self.cur_image is not None
        cur_poly = self.cur_image.wip_ann
        assert cur_poly is not None
        
        annotation_id = cur_poly.annotation_id
        pp_rel_pos = cur_poly.coords
        pp_pos = self.coords_rel2canvas(pp_rel_pos)
        coords = pp_pos + list(pos)
        rel_coords = pp_rel_pos + list(rel_pos)
        color = self.get_color_by_tagid(cat_id)

        enclosed = [self.canvas.gettags(point)[2] for point in self.canvas.find_enclosed(pos[0]-20, pos[1]-20, pos[0]+20, pos[1]+20) if 'poly-point' in self.canvas.gettags(point)]
        if f'p{cur_poly.point_ids[0]}' in enclosed and len(cur_poly.point_ids) > 2:
            self.canvas.create_polygon(*coords[:-2], outline=color, fill='', width=2, tags=['annotation', 'poly', annotation_id, ' '.join([str(coord) for coord in rel_coords[:-2]]), cat_id])
            cur_poly.set(coords=rel_coords)
            cur_poly.remove_points()
            self.mestre.ann_in_progress = False
            self.cur_image.store_annotation()
            
            self.remove_points('all')
            if direct_command: self.mestre.add_action('finished_annotation', annotation_id)
            return annotation_id
        
        point = self._draw_point(pos, rel_pos, 'poly', cat_id)
        ppoint = cur_poly.point_ids[-1]
        cur_poly.add_point(point, list(rel_pos))
        
        self.canvas.create_line(*coords[-4:], fill=color, width=3, tags=['edge', 'poly-edge', f"d{point}", f"d{ppoint}", ' '.join([str(coord) for coord in rel_coords[-4:]]), cat_id])
        self.canvas.tag_lower('poly-edge', 'poly-point')
        self.create_preview(pos, rel_pos, cat_id)
        
        if direct_command: self.mestre.add_action('added_points', 'last')
        return point
    
    def create_preview(self, pos: list[int] | tuple[int, int], rel_pos: list[float] | tuple[float, float], cat_id: str) -> None:
        """Handles creating previews of the annotation objects in construction.

        Args:
            pos (list[int] | tuple[int, int]): x y position of the point in relation to the canvas.
            rel_pos (list[float] | tuple[float, float]): x y position of the point in relation to the image.
            cat_id (str): Selected annotation mode.

        Returns:
            point_id|annotation_id (int | str): Where point_id is the internal numerical id of a point object on canvas and annotation_id is the unique identifier of a completed annotation.
        """
        if self.cur_image is None or self.cur_image.wip_ann is None:
            self.mestre.ann_in_progress = False
            return
        color = self.get_color_by_tagid(cat_id)
        
        match self.active_tool.get():
            case 'bbox': 
                self.canvas.create_rectangle(*pos, *pos, fill='', outline=color, width=1, tags=['preview', 'bbox-preview', f'{rel_pos[0]} {rel_pos[1]}'])
            case 'obbox': 
                point_num = len(self.cur_image.wip_ann.point_ids)
                if point_num == 1: self.canvas.create_line(*pos, *pos, fill=color, width=1, tags=['preview', 'obbox-preview', f'{rel_pos[0]} {rel_pos[1]}'])
                if point_num == 2:
                    self.canvas.delete('obbox-preview')
                    pp_rel_pos = self.cur_image.wip_ann.coords
                    pp_pos = self.coords_rel2canvas(pp_rel_pos) 
                    x3, y3 = self.fixedline_coords(*pp_pos, pos[0], pos[1]) # type: ignore
                    x4, y4 = self.final_point(*pp_pos, x3, y3) # type: ignore
                    self.canvas.create_polygon(*pp_pos, x3, y3, x4, y4, width=1, fill='', outline=color, tags=['obbox-preview'])
            case 'poly':
                self.canvas.create_line(*pos, *pos, fill=color, width=1, tags=['preview', 'poly-preview', f'{rel_pos[0]} {rel_pos[1]}'])
    
    def update_preview(self, *mouse_pos: int) -> None:
        """Handles updating the preview in relation to mouse position.
        
        Args:
            *mouse_pos (int): tuple containing the x and y positions of the mouse in relation to the canvas.
        """
        if not self.mestre.ann_in_progress: return
        if self.cur_image is None or self.cur_image.wip_ann is None:
            self.mestre.ann_in_progress = False
            return
        mx, my = mouse_pos
        cat_id = self.get_tagid()
        assert cat_id is not None
        match self.active_tool.get():
            case 'bbox':
                rel_pos = [float(val) for val in self.canvas.gettags('bbox-preview')[2].split()]
                pos = self.coords_rel2canvas(rel_pos)
                self.canvas.coords('bbox-preview', *pos, mx, my)
            case 'obbox': 
                point_num = len(self.cur_image.wip_ann)
                if point_num == 1: 
                    rel_pos = [float(val) for val in self.canvas.gettags('obbox-preview')[2].split()]
                    pos = self.coords_rel2canvas(rel_pos)
                    self.canvas.coords('obbox-preview', *pos, mx, my)
                if point_num == 2:
                    self.canvas.delete('obbox-preview')
                    color = self.get_color_by_tagid(cat_id)
                    pp_rel_pos = self.cur_image.wip_ann.coords
                    pp_pos = self.coords_rel2canvas(pp_rel_pos)
                    x3, y3 = self.fixedline_coords(*pp_pos, mx, my) # type: ignore
                    x4, y4 = self.final_point(*pp_pos, x3, y3) # type: ignore
                    self.canvas.create_polygon(*pp_pos, x3, y3, x4, y4, width=1, fill='', outline=color, tags=['preview', 'obbox-preview'])
            case 'poly':
                rel_pos = [float(val) for val in self.canvas.gettags('poly-preview')[2].split()]
                pos = self.coords_rel2canvas(rel_pos)
                self.canvas.coords('poly-preview', *pos, mx, my)
           
    def update_annwip(self) -> None:
        """Handles updating the size and position of annotations in progress in relation to the window when resizing.
        """
        points = [point for point in self.canvas.find_withtag(f'point')]
        for point in points:
            rel_pos = [float(val) for val in self.canvas.gettags(point)[3].split()]
            pos = self.coords_rel2canvas(rel_pos)
            coords = (pos[0]-6, pos[1]-6, pos[0]+6, pos[1]+6)
            self.canvas.coords(point, *coords)
        edges = [edge for edge in self.canvas.find_withtag('edge')]
        for edge in edges:
            rel_pos = [float(val) for val in self.canvas.gettags(edge)[4].split()]
            pos = self.coords_rel2canvas(rel_pos)
            self.canvas.coords(edge, *pos)
    
    def update_annotations(self) -> None:
        """Handles updating size and position of completed annotations in relation to the window when resizing.
        """
        if self.mestre.ann_in_progress:
            self.update_annwip()
        annotations = [annpoly for annpoly in self.canvas.find_withtag('annotation')]
        for annpoly in annotations:
            annpoly_tags = self.canvas.gettags(annpoly)
            color = self.get_color_by_tagid(annpoly_tags[4])
            rel_coords = [float(val) for val in annpoly_tags[3].split()]
            coords = self.coords_rel2canvas(rel_coords)
            self.canvas.delete(annpoly)
            if 'mark-point' in annpoly_tags:
                coords = (coords[0]-6, coords[1]-6, coords[0]+6, coords[1]+6)
                self.canvas.create_oval(*coords, fill='', outline=color, width=2, tags=annpoly_tags)
                continue
            self.canvas.create_polygon(*coords, outline=color, fill='', width=2, tags=annpoly_tags)
    
    def redraw_points(self, coords: list[tuple[int, int]], point_type: _annTypeGen, cat_id: str) -> list[int]:
        """Redraws a set of points of equal type and category.

        Args:
            coords (list[tuple[int, int]]): List containing the x y coordinates of each point.
            point_type (Literal[&#39;bbox&#39;, &#39;obbox&#39;, &#39;poly&#39;, &#39;mark&#39;]): Selected annotation mode.
            cat_id (str): Object category id.

        Returns:
            point_ids: (list[int]): List containing the internal numerical ids of each point.
        """
        point_ids = [self.draw_point(pos, point_type, cat_id) for pos in coords]
        assert all([isinstance(point_id, int) for point_id in point_ids])
        return point_ids # type: ignore

    def redraw_markpoint(self, rel_pos: list[float] | tuple[float, float], annotation_id: str, cat_id: str) -> None:
        """Redraws a mark point (seed annotation) on the canvas.

        Args:
            rel_pos (list[float] | tuple[float, float]): x y point position relative to the image.
            annotation_id (str): Unique annotation id.
            cat_id (str): Object category id.
        """
        pos = self.coords_rel2canvas(rel_pos)
        self._draw_point(pos, rel_pos, 'mark', cat_id, annotation_id)
    
    def redraw_annotation(self, polygon_type: str, annotation_id: str, rel_coords: list[float], cat_id: str) -> None:
        """Redraws an annotation on the canvas.

        Args:
            polygon_type (str): Type of annotation.
            annotation_id (str): Unique annotation id.
            rel_coords (list[float]): List containing the x y coordinates of each point of the annotation .
            cat_id (str): Object category id.
        """
        color = self.get_color_by_tagid(cat_id)
        coords = self.coords_rel2canvas(rel_coords)
        self.canvas.create_polygon(*coords, outline=color, fill='', width=2, tags=['annotation', polygon_type, annotation_id, ' '.join([str(val) for val in rel_coords]), cat_id])
        
    def redraw_annotations_fromimage(self) -> None:
        """Redraws tha annotations saved to the image when loaded.
        """
        if self.images[0] is None or self.cur_image is None: return
        
        if self.images[0].mode == 'semiauto':
            for ann in self.cur_image.annotations: 
                self.redraw_markpoint(ann.coords, ann.annotation_id, ann.cat_id)
        else:
            for ann in self.cur_image.annotations:
                self.redraw_annotation(ann.annotation_type, ann.annotation_id, ann.coords, ann.cat_id)
    
    def remove_points(self, target_point: Literal['all', 'last'] = 'all', clean_up: bool = True, direct_command: bool = False) -> list[tuple[str, ...]]:
        """Removes the target points from the canvas, along any connected edges. Recreates preview if necessary, terminates a WIP annotation if no points remain.

        Args:
            target_point (Literal[&#39;all&#39;, &#39;last&#39;], optional): If either all or only the last added point should be removed. Defaults to 'all'.
            clean_up (bool, optional): If the WIP annotation should be updated of the removed point. Defaults to True.
            direct_command (bool, optional): If the function call was originally user made. Defaults to False.

        Returns:
            deleted_data (list[tuple[str, ...]]): A list of tuples containing the tags of all deleted points.
        """
        assert self.cur_image is not None
        if target_point == 'all': 
            deleted_data = [self.canvas.gettags(annotation) 
                            for point_type in ['mark', 'bbox', 'obbox', 'poly'] 
                            for annotation in self.canvas.find_withtag(f'{point_type}-point')]
            self.canvas.delete('point', 'edge', 'preview')
            self.cur_image.clear_wip()
            return deleted_data
        
        last_point = max(self.canvas.find_withtag('point'))
        deleted_data = self.canvas.gettags(last_point)
        match self.active_tool.get():
            case 'bbox': self.canvas.delete(last_point)
            case 'obbox': self.canvas.delete(last_point, 'obbox-edge')
            case 'poly': self.canvas.delete(last_point, *self.canvas.find_withtag(f"d{last_point}"))
        if not clean_up and self.cur_image.wip_ann is not None: 
            self.cur_image.wip_ann.remove_points()
        
        self.canvas.delete('preview')
        points = self.canvas.find_withtag('point')
        if len(points) == 0: 
            self.mestre.ann_in_progress = False
            self.cur_image.clear_wip()
            return [deleted_data]
        new_last_point_tags = self.canvas.gettags(max(points))
        cat_id = new_last_point_tags[4]
        rel_pos = [float(val) for val in new_last_point_tags[3].split()]
        pos = self.coords_rel2canvas(rel_pos)
        self.create_preview(pos, rel_pos, cat_id)
        
        if direct_command: self.mestre.add_action('deleted_points', [deleted_data])
        return [deleted_data]

    def remove_annotations(self, target_tag: str = 'annotation', direct_command: bool = True) -> list[Annotation]:
        """Removes annotations from the project.

        Args:
            target_tag (str, optional): Target tag for removal, targets all, one in specific or a category tag. Defaults to 'annotation'.
            direct_command (bool, optional): If the function call was originally user made. Defaults to True.

        Returns:
            deleted_annotations (list[Annotation]): List containing all removed annotation objects.
        """
        assert self.cur_image is not None
        deleted_annotations: list[Annotation] = []
        for annotation in self.canvas.find_withtag(target_tag):
            ann_id = self.canvas.gettags(annotation)[2]
            ann_index = self.cur_image.find_annotation(lambda ann: ann.annotation_id == ann_id)
            assert ann_index is not None
            deleted_annotations.append(self.cur_image.annotations.pop(ann_index))
        self.canvas.delete(target_tag)
        
        if direct_command: self.mestre.add_action('deleted_annotations', deleted_annotations)
        return deleted_annotations
    
    def select_annotation(self, pos: tuple[int, int], control: bool = False, 
                          shift: bool = False, deselect: bool = False) -> None:
        """Handles selecting and deselecting annotations.

        Args:
            pos (tuple[int, int]): x y coordinates of the mouse.
            control (bool, optional): If the user is pressing control when selecting. Defaults to False.
            shift (bool, optional): If the user is pressing shift when selecting. Defaults to False.
            deselect (bool, optional): If the call is only to deselect all selected objects. Defaults to False.
        """
        selected = self.canvas.find_withtag('selected')
        x, y = pos
        
        if len(selected) != 0 and not shift:
            for annotation in selected:
                tags = self.canvas.gettags(annotation)
                color = self.get_color_by_tagid(tags[4])
                self.canvas.itemconfigure(annotation, {
                    'outline': color,
                    'width': 2,
                    'tags': [tag for tag in tags if tag != 'selected']
                })
        if deselect: return
        
        closest = self.canvas.find_closest(x, y, halo=10)
        overlapping = self.canvas.find_overlapping(x-20, y-20, x+20, y+20)
        if closest[0] not in overlapping: return
        if self.canvas.gettags(closest[0])[0] != 'annotation': return
        
        if control: 
            cat_id = self.canvas.gettags(closest[0])[4]
            color = self.get_color_by_tagid(cat_id)
            for annotation in self.canvas.find_withtag(cat_id):
                self.canvas.itemconfigure(annotation, {
                    'outline': color,
                    'width': 4,
                    'tags': list(self.canvas.gettags(annotation)) + ['selected']
                })
        else: 
            cat_id = self.canvas.gettags(closest[0])[4]
            color = self.get_color_by_tagid(cat_id)
            self.canvas.itemconfigure(closest[0], {
                'outline': color,
                'width': 4,
                'tags': list(self.canvas.gettags(closest[0])) + ['selected']
            })
    
    def change_annotation_color(self, cat_id: str, target_annotations: str = '') -> None:
        """Updates targetted annotation' color.

        Args:
            cat_id (str): Object category id as the new color to be inherited.
            target_annotations (str): Target tag for recoloring. Defaults to '' (uses cat_id as target).
        """
        if target_annotations == '': target_annotations = cat_id
        annotations = self.canvas.find_withtag(target_annotations)
        annotation_tags = [self.canvas.gettags(poly) for poly in annotations]
        self.canvas.delete(*annotations)
        for tags in annotation_tags: 
            anntype, annid, rel_coords_str = tags[1:4]
            rel_coords = [float(val) for val in rel_coords_str.split()]
            if anntype == 'mark': self.redraw_markpoint(rel_coords, annid, cat_id)
            else: self.redraw_annotation(anntype, annid, rel_coords, cat_id)
    
    def annotation_menu(self, *pos: int) -> None:
        """Constrcuts the pop up menu after selecting an annotation polygon.

        Args:
            *pos (int): x and y position of the cursor.
        """
        assert self.cur_image is not None
        selected = self.canvas.find_withtag('selected')
        if len(selected) == 0 or self.mestre.ann_in_progress: return
        
        annpolygon_options = tkb.Menu(master=self, 
                                  tearoff=0, 
                                  relief='raised')
        
        if len(selected) > 1:
            polygon_ids = [self.canvas.gettags(ann)[2] for ann in selected]
            annpolygon_options.add_command(label=_('Edit annotations'), command= lambda *x: self.edit_annotation_window(polygon_ids))
            annpolygon_options.add_command(label=_('Remove annotations'), command= lambda *x: self.remove_annotations('selected', True))
            annpolygon_options.tk_popup(*pos)
            self.popup_open = True
            return
        
        tags = self.canvas.gettags(selected[0])
        polygon_id, cat_id = tags[2], tags[4]
        category_name = self.val_table.item(self.val_table.tag_has(cat_id)[0], 'values')[2]
        polygon_index = self.cur_image.find_annotation(lambda poly: poly.annotation_id == polygon_id)
        assert polygon_index is not None
        polygon = self.cur_image.annotations[polygon_index]
        metadata = polygon.metadata
        
        metadata_options = tkb.Menu(master=annpolygon_options)
        for field, data in metadata.items(): metadata_options.add_command(label=f'{field}: {data}')
        
        annpolygon_options.add_command(label=f'{_('Category')}: {category_name}')
        annpolygon_options.add_cascade(label=_('Metadata'), menu=metadata_options)
        annpolygon_options.add_command(label=_('Edit annotation'), command= lambda *x: self.edit_annotation_window([polygon_id]))
        annpolygon_options.add_command(label=_('Remove annotation'), command= lambda *x: self.remove_annotations('selected', True))
        annpolygon_options.tk_popup(*pos)
        self.popup_open = True
    
    def edit_annotation_window(self, annotation_ids: list[str]) -> None:
        """Constrcuts the window for editing the currently-selected annotations' data.

        Args:
            annotation_ids (list[str]): List of unique ids of each annotation object to be edited.
        """
        assert self.cur_image is not None
        edit_window = tkb.Toplevel('Edit Annotation')
        edit_frame = tkb.Frame(master=edit_window, relief='groove', padding=5)
        for i in range(3):
            edit_frame.columnconfigure(i, weight=i)
            edit_frame.rowconfigure(i, weight=1)
        edit_frame.pack(expand=True, fill='both')
        
        if len(annotation_ids) == 1:
            annotation_index = self.cur_image.find_annotation(lambda annotation: annotation.annotation_id == annotation_ids[0])
            assert annotation_index is not None
            annotation = self.cur_image.annotations[annotation_index]
            cat_id = annotation.cat_id
            category_name = self.val_table.item(self.val_table.tag_has(cat_id)[0], 'values')[2]
            metadata = annotation.metadata
        else:
            cat_id = ''
            category_name = f'<{_('Multiple categories')}>'
            metadata = {_('Multiple metadata instances'): ''}
        
        category_label = tkb.Label(master=edit_frame, text=f'{_('Annotation category')}:')
        category_name_var, category_tagid_var = tkb.StringVar(value=category_name), tkb.StringVar(value=cat_id)
        category_menubutton = tkb.Menubutton(master=edit_frame, textvariable=category_name_var)
        category_menu = tkb.Menu(master=category_menubutton)
        for item_id in self.val_table.get_children():
            category_name = self.val_table.item(item_id, 'values')[2]
            cat_id = self.val_table.item(item_id, 'tags')[0]
            category_menu.add_radiobutton(label=category_name, command= lambda x=category_name, y=cat_id, *z: category_name_var.set(x) or category_tagid_var.set(y))
        category_menubutton.config(menu=category_menu)
        
        metadata_label = tkb.Label(master=edit_frame, text=f'{_('Annotation metadata')}:')
        metadata_string = '; '.join([f'{key}: {value}' for key, value in metadata.items()])
        metadata_entry = tkb.Text(master=edit_frame, wrap='word', height=8, width=40)
        metadata_entry.insert('end', metadata_string)
        ToolTip(metadata_entry, text=f"{_('Metadata written in the form: key1: value1; key2: value2;...')}\n{_('(All whitespaces are ignored)')})")
        
        confirm_button = tkb.Button(master=edit_frame, text=_("Confirm"))
        
        confirm_button.configure(command= lambda *x: 
                                    self.edit_annotations(annotation_ids, 
                                                      category_tagid_var.get(), 
                                                      {keyvalue.split(':')[0]: keyvalue.split(':')[1] 
                                                        for keyvalue in ''.join(metadata_entry.get('0.1', 'end').split()).split(';') 
                                                        if ':' in keyvalue}) or edit_window.destroy())
        
        category_label.grid(column=0, row=0, pady=2, sticky='nw')
        category_menubutton.grid(column=1, row=0, pady=2, sticky='nw')
        metadata_label.grid(column=0, row=1, pady=2, sticky='nw')
        metadata_entry.grid(column=1, row=1, pady=2, sticky='nsew')
        confirm_button.grid(column=1, row=2, pady=(5, 2), sticky='es')
    
    def edit_annotations(self, annotation_ids: list[str], cat_id: str, metadata: dict[str, str], direct_command: bool = True) -> list[tuple[str, str, dict[str, str]]]:
        """Updates the selected annotations with the data set in the annotation window.

        Args:
            annotation_ids (list[str]): List of unique ids of each annotation object to be edited.
            cat_id (str): Object category id as the new color to be inherited.
            metadata (dict[str, str]): New metadata for the given annotations.
            direct_command (bool, optional): If the function call was originally user made. Defaults to True.

        Returns:
            prev_data (list[tuple[str, str, dict[str, str]]]): Previous data of each annnotation.
        """
        assert self.cur_image is not None
        prev_data: list[tuple[str, str, dict[str, str]]] = []
        for annotation_id in annotation_ids:
            annotation_index = self.cur_image.find_annotation(lambda ann: ann.annotation_id == annotation_id)
            if annotation_index is None: continue
            annotation = self.cur_image.annotations[annotation_index]
            prev_data.append((annotation_id, annotation.cat_id, annotation.metadata))
            if cat_id != '': annotation.cat_id = cat_id
            annotation.metadata = metadata
            self.change_annotation_color(cat_id, annotation_id)
        if direct_command: self.mestre.add_action('edited_annotations', prev_data)
        return prev_data
    
    def canvas_click(self, event: tk.Event) -> None:
        """Handler for clicking actions in while annotating.

        Args:
            event (tk.Event): Tkinter click event.
            double (bool, optional): Determines if it was a double click. Defaults to False.
        """
        if self.cur_image is None: return
        
        pos = x, y = event.x, event.y
        in_image = ['imagem' in tags 
                     for item in self.canvas.find_overlapping(x-1, y-1, x+1, y+1) 
                     for tags in self.canvas.gettags(item)]
        if sum(in_image) == 0: return
        
        shift, control = 'shift' in str(event).lower(), 'control' in str(event).lower()
        point_type = self.active_tool.get()
        if event.num == 1:
            if self.popup_open: 
                self.popup_open = False
                return
            if not self.mestre.ann_in_progress: 
                self.select_annotation(pos, deselect=True)
            self.draw_point(pos, point_type) # type: ignore
        elif not self.mestre.ann_in_progress:
            self.select_annotation(pos, control, shift)
            self.annotation_menu(event.x_root, event.y_root) 

    # ---------------------------------------------------------- #
    #* commonly used functions and mathmetical methods
    
    @staticmethod
    def fixedline_coords(x1: float | int, y1: float | int, x2: float | int, y2: float | int, mx: float | int, my: float | int) -> tuple[float, float]:
        a = (x1 - x2)/(y2-y1) if y2 != y1 else y2
        x3 = (my+a*x2-y2)/a if abs(a)>=1 else mx
        y3 = a*(x3-x2)+y2
        return x3, y3
    
    @staticmethod
    def final_point(x1: float | int, y1: float | int, x2: float | int, y2: float | int, x3: float | int, y3: float | int) -> tuple[float, float]:
        if y3==y2 or x3==x2: return x1, y1 
        a = (x2-x3)/(y3-y2) 
        xa = x3+1
        ya = a+y3
        xb = x1+1
        yb = (y3-y2)/(x3-x2)+y1
        x4 = (x1*yb-y1*xb-x3*ya+y3*xa)/(yb-y1-a)
        y4 = a*(x4-x3) + y3
        return x4, y4
    
    @staticmethod
    def coordlist2str(coordlist: Iterable[int|float]) -> str:
        return ' '.join(str(coord) for coord in coordlist)
    
    def coords_rel2image(self, coords: list[int | float] | tuple[int|float, ...]) -> list[float]:
        return [coords[i]*self.last_image_ratio[i%2] for i in range(len(coords))]
    
    def coords_rel2canvas(self, coords: list[float] | tuple[float, ...]) -> list[int]:
        return [int(coords[i]/self.last_image_ratio[i%2]) for i in range(len(coords))]
    
    def get_tagid(self) -> str | None:
        if self.images[0] is None: return
        if len(self.images[0].categories) == 0: return
        item_id = self.val_table.tag_has('marker')
        if len(item_id) == 0: return
        if self.val_table.item(item_id[0], 'values')[4] == 'I': return
        return self.val_table.item(item_id[0], 'tags')[0]
    
    def get_color_by_tagid(self, cat_id: str) -> str:
        assert self.images[0] is not None
        visible = self.images[0].categories[cat_id]['visible']
        return self.images[0].categories[cat_id]['hex'] if visible else ''
    
    # ---------------------------------------------------------- #
    #* General object handling

    def select_all(self) -> None:
        """Selects all marking/annotations in the image.
        """
        if self.cur_image is None: return
        target = 'annotation' 
        for point in self.canvas.find_withtag(target):
            self.canvas.itemconfigure(point, {
            'outline': 'red',
            'width': 2,
            'tags': [tag for tag in self.canvas.gettags(point)] + ['selected']
            })
    
    def remove_objects_handler(self) -> None:
        """Main handler for removing markings/annotations off images. 
        """
        if self.mestre.ann_in_progress: self.remove_points('last', False, True)
        self.remove_annotations('selected')
    
    # ---------------------------------------------------------- #
    #* Background and non-specific functions
    
    def binds(self) -> None:
        """Function with all the main binds for annotation.
        """
        self.window.bind("<KeyRelease-Right>", lambda e: self.skip_image('next'))
        self.window.bind("<KeyRelease-d>", lambda e: self.skip_image('next'))
        self.window.bind("<KeyRelease-Left>", lambda e: self.skip_image('prev'))
        self.window.bind("<KeyRelease-a>", lambda e: self.skip_image('prev'))
        
        self.canvas.bind("<Button-1>", lambda e: self.canvas_click(e))
        self.window.bind("<Button-1>", lambda e: self.select_annotation((0, 0), deselect=True))
        self.canvas.bind("<ButtonRelease-3>", lambda e: self.canvas_click(e))
        self.canvas.bind("<Motion>", lambda e: self.update_preview(e.x, e.y))
        
        for i in range(len(self.tool_buttons.keys())):
            self.window.bind(f'<KeyRelease-{i+1}>', lambda e, x=i: self.change_active_tool(x))
    
        self.window.bind("<Control-KeyRelease-a>", lambda e: self.select_all())
        self.window.bind("<KeyPress-Delete>", lambda e: self.remove_objects_handler())
    
    def skip_image(self, movement: int | Literal['next', 'prev'], direct_command: bool = True) -> None:
        """Handles all functions related to before and after jumping to an image.

        Args:
            movement (int | Literal['next', 'prev']): Image index or jump direction.
            keybind (bool, optional): If True, action will added to the undo stack. Defaults to True.
        """
        active_widget = str(self.window.focus_get())
        if self.images[0] is None or \
            'category_name_entry' in active_widget or \
                (isinstance(movement, str) and 'entry' in active_widget): return
        elif direct_command: 
            assert self.cur_image is not None
            self.mestre.add_action('moved_page', self.cur_image.index)
        
        self.remove_points()
        self.clean_canvas()
        self.images[0].jump_to(movement)
        self.refresh(True)
        self.mestre.side.reset_count()
        self.redraw_annotations_fromimage()
        self.mestre.ann_in_progress = False
        self.count_objects()
    
    def count_objects(self) -> None:
        """Counts how many objects of each category are in the image to be displayed in the side bar.
        """
        tags = [self.canvas.gettags(obj)[4]  for obj in self.canvas.find_withtag('annotation')]
        tag_qnt = dict(Counter(tags))
        
        for item in self.val_table.get_children():
            cat_id = self.val_table.item(item, 'tags')[0]
            values = self.val_table.item(item, 'values')
            quant = tag_qnt.setdefault(cat_id, 0)
            self.val_table.item(item, values=(*values[:3], quant, values[4]))
    
    def refresh(self, single: bool = False) -> None:
        """Checks if the window size has chnged and refreshes the displayed image if necessary.

        Args:
            single (bool, optional): If False, activates the looping fucnctionality. Defaults to False.
        """
        cur_size = self.image_frame.winfo_width(), self.image_frame.winfo_height()
        same_size: bool = cur_size == self.last_window_size
        if not same_size: 
            self.last_window_size = cur_size
            self.update_background()
            self.update_toolbarpos()
        self.update_image(same_size)
        self.mestre.clean_stacks()
        if not single: self.after(ms=200, func= lambda *x: self.refresh())
    
    def _update(self) -> None:
        """Third and last step of the cascade update function.
        """
        self.clean_canvas()
        if self.images[0] is None: self.cur_image = None
        self.update_image()
        self.update_values()
        self.redraw_annotations_fromimage()
        self.update_background()
        self.update_toolbarpos()
        self.update_icons()
    
    def _closing_funcs(self) -> None:
        """Backend function to be run when closing the program.
        """
        if self.images[0] is None: return


# ========================================================== #
# ========================================================== #

#! Not documented
class DetectiontoProjectWindow(tkb.Toplevel):
    def __init__(self, window: tkb.Window) -> None:
        x = window.winfo_pointerxy()[0] - 20
        y = window.winfo_pointerxy()[1] - 20
        
        super().__init__(title=_("Automatic Annotation"), position=(x, y), resizable=[False, False])

        self.main_frame = tkb.Frame(master=self, padding=5, relief='raised', borderwidth=5)
        self.main_frame.pack(fill='both', expand=True)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
        self.ann_type       = tkb.StringVar(value='bbox')
        self.det_model_dir  = tkb.StringVar(value= os.path.join(FOLDER_PATHS.MODELS, 'FastSAM-x.pt'))
        self.model_type     = tkb.StringVar(value='yolov8')
        self.model_task     = tkb.StringVar(value='segment')
        self.binarize       = tkb.BooleanVar(value=False)
        self.seg_from_proj  = tkb.BooleanVar(value=False)
        self.image_dir      = tkb.StringVar(value='')
        self.output_dir     = tkb.StringVar(value='')
        self.project_dir    = tkb.StringVar(value='')

        self.detection_config()
        self.checks()
        tkb.Separator(master=self.main_frame).pack(expand=True, fill='x', pady=5)
        self.dir_entry()
        tkb.Separator(master=self.main_frame).pack(expand=True, fill='x', pady=5)
        self.ok_button = tkb.Button(master=self.main_frame, text="OK", command=lambda *x: self.confirm())
        self.ok_button.pack(side='right')
        
        base_toplevel_binds(self)
        self.focus_force()
    
    def detection_config(self) -> None:
        config_frame = tkb.Frame(master=self.main_frame)
        config_frame.pack(expand=True, fill='x')
        for i in range(4): config_frame.rowconfigure(i, weight=1)
        for i in range(3): config_frame.columnconfigure(i, weight=1)
        
        self.detect_model_display = tkb.StringVar(value=_("Default") + ' (FastSAM-x)')
        self.model_type_display = tkb.StringVar(value=_("YOLOv8"))
        self.model_task_display = tkb.StringVar(value=_('Segmentation'))
        self.ann_type_display  = tkb.StringVar(value=_("Bounding Box"))
        
        detect_model_label  = tkb.Label(master=config_frame, text=_('Model'), justify='left')
        detect_model_button = tkb.Menubutton(master=config_frame, width=15, textvariable=self.detect_model_display)
        self.detect_model_menu   = tkb.Menu(master=detect_model_button)
        for label, option in [(_("Default") + ' (FastSAM-x)', 'default'), (_('Choose Model'), 'choose')]:                
            self.detect_model_menu.add_radiobutton(label=label, command= lambda x=option, *y: self.detect_model_selection(x))
        detect_model_button.config(menu=self.detect_model_menu)
        
        self.model_type_button = tkb.Menubutton(master=config_frame, width=15, textvariable=self.model_type_display, state='disabled')
        self.model_type_menu   = tkb.Menu(master=self.model_type_button)
        for label, option in [("YOLOv8", 'yolov8')]:
            self.model_type_menu.add_radiobutton(label=label, value=option, variable=self.model_type, command= lambda x=label, *y: self.model_type_display.set(value=x))
        self.model_type_button.config(menu=self.model_type_menu)
        
        self.model_task_button = tkb.Menubutton(master=config_frame, width=15, textvariable=self.model_task_display, state='disabled')
        self.model_task_menu   = tkb.Menu(master=self.model_task_button)
        for label, option in [(_('Detection'), 'detect'), (_('Segmentation'), 'segment')]:                
            self.model_task_menu.add_radiobutton(label=label, value=option, variable=self.model_task, command= lambda x=option, *y: self.model_task_selection(x))
        self.model_task_button.config(menu=self.model_task_menu)
        
        
        ann_type_label  = tkb.Label(master=config_frame, text=_('Type'), justify='left')
        self.ann_type_button = tkb.Menubutton(master=config_frame, width=15, textvariable=self.ann_type_display)
        self.ann_type_menu   = tkb.Menu(master=self.ann_type_button)
        for label, option in [(_('Bounding Box'), 'bbox'), (_('Polygon'), 'polygon')]:                
            self.ann_type_menu.add_radiobutton(label=label, value=option, variable=self.ann_type, 
                                      command= lambda x=label, *y: self.ann_type_display.set(value=x))
        self.ann_type_button.config(menu=self.ann_type_menu)
        
        detect_model_label.grid(column=0, row=0, sticky='we', pady=(0, 1))
        detect_model_button.grid(column=0, row=1, sticky='we', pady=(0, 1), padx=(0, 5))
        self.model_type_button.grid(column=1, row=1, sticky='we', pady=(0, 1), padx=5)
        self.model_task_button.grid(column=2, row=1, sticky='we', pady=(0, 1), padx=(5, 0))
        ann_type_label.grid(column=0, row=2, sticky='we', pady=(0, 1))
        self.ann_type_button.grid(column=0, columnspan=2, row=3, sticky='we', pady=(0, 1), padx=(0, 5))

    def detect_model_selection(self, option: str) -> None:
        if option == "default":
            self.det_model_dir.set(os.path.join(FOLDER_PATHS.MODELS, 'FastSAM-x.pt'))
            self.detect_model_display.set(_("Default") + ' (FastSAM-x)')
            
            self.ann_type_button.config(state='normal')
            self.model_type_menu.invoke(0)
            self.model_task_menu.invoke(1)
            self.model_type_button.config(state='disabled')
            self.model_task_button.config(state='disabled')
            
        else:
            file_path = filedialog.askopenfilename(title=_("Select model weights file"), filetypes=[(_('model weights'), "*.pt")])
            if file_path in [None, '', ()]: return
            self.det_model_dir.set(file_path)
            self.detect_model_display.set(os.path.basename(file_path).split('.')[0])
            
            self.model_type_button.config(state='normal')
            self.model_task_button.config(state='normal')
            
        self.focus_force()

    def model_task_selection(self, selection: str) -> None:
        if selection == 'detect': 
            self.ann_type_menu.invoke(0)
            self.ann_type_button.config(state='disabled')
            self.model_task_display.set(_("Detection"))
        else:
            self.ann_type_button.config(state='normal')
            self.model_task_display.set(_("Segmentation"))

    def checks(self) -> None:
        check_frame = tkb.Frame(master=self.main_frame)
        check_frame.pack(expand=True, fill='x', pady=5)
        check_frame.rowconfigure(0, weight=1)
        for i in range(2): check_frame.columnconfigure(i, weight=i%2)
        
        binary_label = tkb.Label(master=check_frame, text=_('Binarize values'), justify='left')
        binary_check = tkb.Checkbutton(master=check_frame, variable=self.binarize)
        
        binary_label.grid(row=0, column=0, sticky='nw', pady=(2, 3))
        binary_check.grid(row=0, column=1, sticky='nws', pady=(2, 3), padx=2)

    def dir_entry(self) -> None:
        dir_frame = tkb.Frame(master=self.main_frame)
        dir_frame.pack(expand=True, fill='x')
        for i in range(7): dir_frame.rowconfigure(i, weight=1)
        for i in range(3): dir_frame.columnconfigure(i, weight=i%2)
        
        self.arq_icon = get_icon('arq')
        
        imagedir_label         = tkb.Label(master=dir_frame, text=_('Images directory'), justify='left')
        imagedir_entry         = tkb.Entry(master=dir_frame, textvariable=self.image_dir, width=50)
        imagedir_prompt_button = tkb.Button(master=dir_frame, image=self.arq_icon, style='Outline.Toolbutton',
                                            command= lambda *x: self.get_dir('img'))
        
        resultsdir_label         = tkb.Label(master=dir_frame, text=_('Result directory'), justify='left')
        resultsdir_entry         = tkb.Entry(master=dir_frame, textvariable=self.output_dir, width=50)
        resultsdir_prompt_button = tkb.Button(master=dir_frame, image=self.arq_icon, style='Outline.Toolbutton',
                                              command= lambda *x: self.get_dir('res'))
        
        prompt_frame = tkb.Frame(master=dir_frame, padding=0)
        prompt_label = tkb.Label(master=prompt_frame, text=_('Project directory'), justify='left')
        prompt_check = tkb.Checkbutton(master=prompt_frame, variable=self.seg_from_proj, command= lambda *x: self.from_proj_check())
        prompt_tooltip_signal = tkb.Label(master=prompt_frame, text="!", font=("Arial", 12, 'bold'), style='EasyMark.TooltipSignal.TLabel')
        ToolTip(prompt_tooltip_signal, text=f"{_('Segmentation based on user-made points on a semi-automatic project.')}\n{_('Compatible with FastSam models only!!')})")
        self.projectdir_entry         = tkb.Entry(master=dir_frame, textvariable=self.project_dir, state='disabled', width=50)
        self.projectdir_prompt_button = tkb.Button(master=dir_frame, image=self.arq_icon, state='disabled', style='Outline.Toolbutton',
                                              command= lambda *x: self.get_dir('proj'))


        imagedir_label.grid(column=0, row=0, sticky='n')
        imagedir_entry.grid(column=0, columnspan=2, row=1, sticky='nsew', padx=2)
        imagedir_prompt_button.grid(column=2, row=1, sticky='ne')
        
        resultsdir_label.grid(column=0, row=2, sticky='n')
        resultsdir_entry.grid(column=0, columnspan=2, row=3, sticky='nsew', padx=2)
        resultsdir_prompt_button.grid(column=2, row=3, sticky='ne')
        
        prompt_frame.grid(column=0, columnspan=3, row=4, sticky='sew')
        prompt_label.pack(side='left')
        prompt_check.pack(side='left')
        prompt_tooltip_signal.pack(side='left')
        self.projectdir_entry.grid(column=0, columnspan=2, row=5, sticky='nsew', padx=2)
        self.projectdir_prompt_button.grid(column=2, row=5, sticky='ne')
    
    def from_proj_check(self) -> None:
        check = self.seg_from_proj.get()
        if check: 
            self.projectdir_entry.config(state='normal')
            self.projectdir_prompt_button.config(state='normal')
        else:
            self.projectdir_entry.config(state='disabled')
            self.projectdir_prompt_button.config(state='disabled')
    
    def get_dir(self, mode: Literal['img', 'res', 'proj']) -> None:
        match mode:
            case 'img':
                path = filedialog.askdirectory(title=_('Select image directory'), mustexist=True, parent=self)
                if self.check_dir(path, mode): self.image_dir.set(path)
                else:
                    messagebox.showerror(
                        title=_("Invalid directory"),
                        message=_("The selected directory does not have any of the following formats")+':\n'+\
                                f"{', '.join(['.jpg', '.jpeg', '.png'])}",
                        master=self # type: ignore
                    )
                    
            case 'res':
                path = filedialog.askdirectory(title=_('Select result directory'), mustexist=True, parent=self)
                self.output_dir.set(path)
                    
            case 'proj':
                path = filedialog.askopenfilename(title=_('Select project file'), filetypes=[(_("json file"), "*.json")], parent=self)
                if self.check_dir(path, mode): self.project_dir.set(path)
                else:
                    messagebox.showerror(
                        title=_("Invalid file"),
                        message=_("The selected file is not a proper project file."),
                        master=self # type: ignore
                    )
        self.focus_force()

    def check_dir(self, path: str, mode: Literal['img', 'res', 'proj']) -> bool:
        if path in [None, '', ()]: return False
        match mode:
            case 'img': 
                format_check = sum([os.path.splitext(file)[1] in ['.jpg', '.jpeg', '.png'] 
                                for file in os.listdir(path)])
                return format_check != 0 and os.path.isdir(path)
            case 'res': 
                return True
            case 'proj':
                if not os.path.isfile(path): return False
                with open(path, 'r') as file:
                    data: dict = json.load(file)
                return list(data.keys()) == ['directory', 'mode', 'sec_mode', 'date_create', 
                                            'date_last', 'categories', 'all_marks']
    
    def confirm(self) -> None:
        paths: list[str | None] = [self.image_dir.get(), self.output_dir.get(), self.project_dir.get()]
        check = 0
        for i in range(3): 
            check += self.check_dir(paths[i], ['img', 'res', 'proj'][i]) # type: ignore
        if not self.seg_from_proj.get(): 
            check += 1; 
            paths[2] = None
        if check < 3: return
        
        DetectToProject(master=self, image_dir=paths[0], output_dir=paths[1], ann_type=self.ann_type.get(), # type: ignore
                        model_dir=self.det_model_dir.get(), model_type=self.model_type.get(), model_task=self.model_task.get(),
                        binarize=self.binarize.get(), proj_dir=paths[2])
            

# ========================================================== #
# ========================================================== #

#! Not documented
class ExporterWindow(tkb.Toplevel):
    def __init__(self, window: tkb.Window) -> None:
        
        x = window.winfo_pointerxy()[0] - 20
        y = window.winfo_pointerxy()[1] - 20

        super().__init__(title=_("Organize"), 
                         resizable=(False, False),
                         position=(x, y))
        
        self.focus_force()
        
        organizer_frame = tkb.Frame(master=self, borderwidth=5, relief='raised', padding=5)
        organizer_frame.pack(fill='both', expand=True)
        
        for i in range(12):
            organizer_frame.columnconfigure(i, weight=1)
        for i in range(6):
            organizer_frame.rowconfigure(i, weight=1)
        
        self.format_funcs(organizer_frame)
        self.partition_constructor(organizer_frame)
        self.checks(organizer_frame)
        self.dir_selection_funcs(organizer_frame)
        
        tkb.Separator(master=organizer_frame).grid(column=0, columnspan=7, row=12, sticky='nsew', pady=5)
        ok_button = tkb.Button(master=organizer_frame, text="OK", command=lambda *x: self.finish_func())
        ok_button.grid(column=6, row=13, sticky='we', pady=(3, 0))
        
        self.check_partitions()
        
        base_toplevel_binds(self)
    
    # ---------------------------------------------------------- #

    def format_funcs(self, organizer_frame: tkb.Frame) -> None:
        format_label = tkb.Label(master=organizer_frame, text=_('Format'), justify='left')
        
        self.format_option = tkb.StringVar(value='YOLOv8')
        format_button = tkb.Menubutton(master=organizer_frame, width=10, 
                                       textvariable=self.format_option)
        format_menu = tkb.Menu(master=format_button)
        for option in FORMATOS:
            format_menu.add_radiobutton(label=option, value=option, variable=self.format_option)
        format_button.config(menu=format_menu)
        
        format_label.grid(column=0, columnspan=2, 
                          row=0, sticky='we', pady=(0, 2))
        format_button.grid(column=2, columnspan=5, 
                           row=0, sticky='we', pady=(0, 2))
    
    # ---------------------------------------------------------- #

    def partition_constructor(self, organizer_frame: tkb.Frame) -> None:
        partition_list: list[tuple[Any, ...]] = [
            (_("Train"), 1, 60),
            (_("Validation"), 2, 20),
            (_("Test"), 3, 20)
        ]
        self.partition_vals: list[tkb.IntVar] = [
            tkb.IntVar(value=60),
            tkb.IntVar(value=20),
            tkb.IntVar(value=20),
            tkb.IntVar(value=3)
        ]
        
        self.lock_closed = tkb.PhotoImage(file=os.path.join(FOLDER_PATHS.IMAGE, 'lock_closed.png'))
        self.lock_open = tkb.PhotoImage(file=os.path.join(FOLDER_PATHS.IMAGE, 'lock_open.png'))
        
        self.sliders: list[tkb.Scale] = [tkb.Scale(master=organizer_frame) for i in range(3)]
        self.locks: list[tkb.Radiobutton] = [tkb.Radiobutton(master=organizer_frame) for i in range(3)]
        self.percents: list[tkb.Spinbox] = [tkb.Spinbox(master=organizer_frame) for i in range(3)]
        for partition in partition_list:
            self.partition_funcs(organizer_frame, *partition)
            
    def partition_funcs(self, organizer_frame: tkb.Frame, 
                        part: str, row: int, value: int) -> None:
        index = row-1
        var_display = tkb.IntVar(value=value) # Criada pq o display do IntVar fica com decimal mesmo sendo int por algum motivo >:/
        self.partition_vals[index].trace_add('write', 
                                             callback= lambda *x, y=index: \
                                                 var_display.set(self.partition_vals[y].get()))
        
        partition_label = tkb.Label(master=organizer_frame, text=part, justify='right')
        self.sliders[index].config(to=100, 
                                   variable=self.partition_vals[index],
                                   command=lambda *x, y=index: \
                                       self.update_partition_vals(y, self.partition_vals[y])
                                   )
        self.percents[index].config(from_=0, to=100, width=3, 
                                    textvariable=var_display, 
                                    validate='focus',
                                    validatecommand=lambda *x, y=index: \
                                        self.validate_percent(y),
                                    invalidcommand=lambda *x, y=index: \
                                        self.percents[y].set(self.partition_vals[index].get()),
                                    command=lambda *x, y=index: \
                                        self.update_partition_vals(y, var_display)
                                    ) #type: ignore
        self.locks[index].config(image=self.lock_open, 
                                 value=index, 
                                 padding=0, 
                                 variable=self.partition_vals[3], 
                                 style='Outline.Toolbutton', 
                                 command=lambda *x: \
                                     self.lock_command())

        partition_label.grid(column=0, columnspan=2, row=row, sticky='we')
        self.locks[index].grid(column=2, row=row, sticky='w')
        self.sliders[index].grid(column=3, columnspan=3, row=row, sticky='we', padx=3)
        self.percents[index].grid(column=6, row=row)
    
    def check_partitions(self) -> None:
        for i in range(3):
            if i == self.partition_vals[3].get(): continue
            self.validate_percent(i)
        self.after(500, lambda *x: self.check_partitions())
    
    def lock_command(self) -> None:
        val = self.partition_vals[3].get()
        for i in range(3):
            if i == val:
                self.locks[i].config(image=self.lock_closed)
                self.sliders[i].config(state='disabled')
                self.percents[i].config(state='disabled')
            else:
                self.locks[i].config(image=self.lock_open)
                self.sliders[i].config(state='normal')
                self.percents[i].config(state='normal')
    
    def validate_percent(self, index: int) -> bool:
        value = self.percents[index].get()
        try:
            value = int(value)
            if 0 > value or value > 100: return False
            self.partition_vals[index].set(value)
            self.update_partition_vals(index, self.partition_vals[index])
            return True
        except ValueError:
            return False
        
    def update_partition_vals(self, index: int, 
                              var_update: tkb.IntVar) -> None:
        self.partition_vals[index].set(var_update.get())
        self.equalize_partitions(index)
    
    def equalize_partitions(self, index: int) -> None:
        vals = self.partition_vals
        remainder = vals[0].get() + vals[1].get() + vals[2].get() - 100
        for tries in range(100):
            for i in range(3):
                if vals[2-i].get() > 0 \
                    and index != 2-i \
                    and remainder > 0 \
                    and vals[3].get() != 2-i:
                        vals[2-i].set(vals[2-i].get()-1)
                        remainder -= 1
                        
                if vals[i].get() < 100 \
                    and index != i \
                    and remainder < 0 \
                    and vals[3].get() != i: 
                        vals[i].set(vals[i].get()+1)
                        remainder += 1
                if remainder == 0: break
            if remainder == 0: break
    
    # ---------------------------------------------------------- #

    def checks(self, organizer_frame: tkb.Frame) -> None:
        self.stratify_var = tkb.BooleanVar(value=True)
        self.empty_var = tkb.BooleanVar(value=False)
        
        stratify_label = tkb.Label(master=organizer_frame, text=_('Stratify'))
        stratify_check = tkb.Checkbutton(master=organizer_frame, 
                                          variable=self.stratify_var,
                                          command= lambda *x: \
                                              self.stratify_var.get()
                                          )
        
        empty_label = tkb.Label(master=organizer_frame, text=_('Keep empty'), justify='right')
        empty_check = tkb.Checkbutton(master=organizer_frame, 
                                          variable=self.empty_var,
                                          command= lambda *x: \
                                              self.empty_var.get()
                                          )
        
        stratify_label.grid(column=0, row=4, sticky='w', pady=2)
        stratify_check.grid(column=1, row=4, pady=2)
        empty_label.grid(column=3, row=4, sticky='w', pady=2)
        empty_check.grid(column=4, row=4, pady=2)
    
    # ---------------------------------------------------------- #

    def dir_selection_funcs(self, organizer_frame: tkb.Frame) -> None:
        tkb.Separator(master=organizer_frame).grid(column=0, columnspan=7, row=5, sticky='nsew', pady=5)
        
        self.arq_icon = get_icon('arq')
        
        self.datafile_path = tkb.StringVar(value='')
        self.imagedir_path = tkb.StringVar(value='')
        self.resdir_path = tkb.StringVar(value='')
        
        datafile_label = tkb.Label(master=organizer_frame, text=_('Data'), justify='left')
        datafile_entry = tkb.Entry(master=organizer_frame, textvariable=self.datafile_path, width=50)
        datafile_button = tkb.Button(master=organizer_frame, image=self.arq_icon, style='Outline.Toolbutton',
                                     command= lambda *x: self.get_datafile())
        
        imagedir_label = tkb.Label(master=organizer_frame, text=_('Images'), justify='left')
        imagedir_entry = tkb.Entry(master=organizer_frame, textvariable=self.imagedir_path, width=50)
        imagedir_button = tkb.Button(master=organizer_frame, image=self.arq_icon, style='Outline.Toolbutton',
                                     command= lambda *x: self.get_imagedir())

        resdir_label = tkb.Label(master=organizer_frame, text=_('Results'), justify='left')
        resdir_entry = tkb.Entry(master=organizer_frame, textvariable=self.resdir_path, width=50)
        resdir_button = tkb.Button(master=organizer_frame, image=self.arq_icon, style='Outline.Toolbutton',
                                   command= lambda *x: self.get_resdir())

        
        datafile_label.grid(column=0, columnspan=2, row=6, sticky='nsew', pady=1)
        datafile_entry.grid(column=0, columnspan=6, row=7, sticky='nsew', pady=1)
        datafile_button.grid(column=6, row=7, pady=1, sticky='e')
        imagedir_label.grid(column=0, columnspan=2, row=8, sticky='nsew', pady=1)
        imagedir_entry.grid(column=0, columnspan=6, row=9, sticky='nsew', pady=1)
        imagedir_button.grid(column=6, row=9, pady=1, sticky='e')
        resdir_label.grid(column=0, columnspan=2, row=10, sticky='nsew', pady=1)
        resdir_entry.grid(column=0, columnspan=6, row=11, sticky='nsew', pady=1)
        resdir_button.grid(column=6, row=11, pady=1, sticky='e')
    
    def get_datafile(self, preset_path: Optional[str] = None) -> bool: 
        if preset_path: path = preset_path
        else:
            path = filedialog.askopenfilename(title=_("Select annotation project file"), filetypes=[(_("json file"), "*.json")], parent=self)
            if path in [None, '', ()]: return False
    
        if not os.path.isfile(path): 
            messagebox.showerror(title=_("Invalid file"), message=_("The selected file does not exist."), master=self) # type: ignore
            return False
        
        with open(path, 'r') as file: 
            data: dict = json.load(file)
        if not list(data.keys()) == ['directory', 'mode', 'sec_mode', 'date_create', 'date_last', 'categories', 'all_ann']:
            messagebox.showerror( title=_("Invalid file"), message=_("The selected file is not a proper annotation project file."), master=self) # type: ignore
            return False

        self.datafile_path.set(value=path)
        
        image_dir = data['directory']
        if not self.get_imagedir(image_dir, True):
            messagebox.showerror(title=_("Invalid image directory"), message=_("Image directory in project file does not exist."), master=self) # type: ignore
        elif self.imagedir_path.get().isspace(): self.imagedir_path.set(value=image_dir)
        return True
                
    def get_imagedir(self, preset_path: Optional[str] = None, proj_preset: bool = False) -> bool: 
        if preset_path: path = preset_path
        else:
            path = filedialog.askdirectory(title=_("Select image directory"), mustexist=True, parent=self)
            if path in [None, '', ()]: return False
        
        if not os.path.isdir(path):
            if not proj_preset:
                messagebox.showerror(title=_("Invalid image directory"), message=_("Image directory does not exist."), master=self) # type: ignore
            return False

        format_check = sum([os.path.splitext(file)[1] in ['.jpg', '.jpeg', '.png']
                             for file in os.listdir(path)])
        if format_check == 0:
            messagebox.showerror(
                    title=_("Invalid directory"),
                    message=_("The selected directory does not have any of the following formats")+':\n' +\
                            f"{', '.join(['.jpg', '.jpeg', '.png'])}",
                    master=self # type: ignore
                )
            return False
        self.imagedir_path.set(value=path)
        return True
        
    def get_resdir(self, preset_path: Optional[str] = None) -> bool: 
        if preset_path: path = preset_path
        else:
            path = filedialog.askdirectory(title=_("Select results directory"), mustexist=True, parent=self)
            if path in [None, '', ()]: return False
        if not os.path.isdir(path): 
            messagebox.showerror(title=_("Invalid directory"), message=_("Results directory does not exist."), master=self) # type: ignore
            return False
        self.resdir_path.set(value=path)
        return True
    
    def finish_func(self) -> None:
        if self.format_option.get() == _("Empty"): return
        
        datafile_path = self.datafile_path.get()
        if not self.get_datafile(datafile_path): return
        imagedir_path = self.imagedir_path.get()
        if not self.get_imagedir(imagedir_path): return
        resdir_path = self.resdir_path.get()
        if not self.get_resdir(resdir_path): return
        
        partitions = [part.get() for part in self.partition_vals][:3]
        ExportAnnotations(datafile_path, imagedir_path, resdir_path, partitions,
                          self.format_option.get(), self.stratify_var.get(), self.empty_var.get())


# ========================================================== #
# ========================================================== #

if __name__ == "__main__":
    window = MainWindow()
    
    WINDOW: MainWindow = window
    DISPLAY: DisplayMaker = window.display
    SIDE: Sidebar = window.display.side
    MAIN: MainVisualizer = window.display.main
    
    window.mainloop()
        
    