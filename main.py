from _tkinter import Tcl_Obj
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

from PIL import ImageTk
from typing import Any, Literal, TypeAlias, Optional

# ========================================================== #
# ========================================================== #


from funcs import *
_ = translator

#TODO: Remove this at some point
class PlaceholderClass:
    """Placeholder class for testing purposes.
    """
    def __init__(self) -> None:
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


def base_toplevel_binds(win: tkb.Toplevel) -> None:
    win.wait_visibility(win)
    win.grab_set()
    win.bind('<Button>', lambda *x: keep_focus(win))
    win.protocol("WM_DELETE_WINDOW", lambda *x: close_window(win))

def keep_focus(win: tkb.Toplevel) -> None:
    if win.focus_get() is None:
        win.focus_set()
        win.lift()

def close_window(win: tkb.Toplevel) -> None:
    win.grab_release()
    win.destroy()

def get_icon() -> tkb.PhotoImage:
    match CONFIG.get('theme', 'dark'):
        case 'dark': return tkb.PhotoImage(file=os.path.join(FOLDER_PATHS['IMAGE'], 'arq_white.png'))
        case 'light': return tkb.PhotoImage(file=os.path.join(FOLDER_PATHS['IMAGE'], 'arq_black.png'))

_actionType: TypeAlias = Literal['markpoints_added', 'markpoints_deleted', 'markpoints_edited', 
                                 'classes_added'   , 'classes_deleted'   , 'class_edited',
                                 'polypoints_added', 'polypoints_deleted', 
                                 'annpolys_added'  , 'annpolys_deleted'  , 'annpolys_edited', 
                                 'moved_page']

class Action:
    """Object to store each action done by the user and it's corresponding reaction.
    """

    def __init__(self, 
                 action_name: _actionType, 
                 primary_data: Any, 
                 secondary_data: Optional[Any] = None):
        """Object to store each action done by the user and it's corresponding reaction.

        Actions
        ------
        - markpoints_added 
            -   Desc: When marking points are added to the image. 
            -   Takes: List of point indexes. 
            -   Form: ['index', ...] 
            -   Returns: markpoints_edited data.
        - markpoints_deleted  
            -   Desc: When marking points are deleted. 
            -   Takes: List of tuples with each of the point's tags. 
            -   Form: [('point', 'coordx coordy', 'index', 'tag_id'), ...] 
            -   Returns: markpoints_added data
        - markpoints_edited  
            -   Desc: When marking points are edited (class change). 
            -   Takes: List of tuples with each of the point's tags. 
            -   Form: [('point', 'coordx coordy', 'index', 'tag_id'), ...] 
            -   Returns: markpoints_edited data \\
        __________________________________________________________________________________________________________
        - classes_added 
            -   Desc: When one or more classes are added to the table, can take data for a point_added action. 
            -   Takes: List of tag ids for each class. 
            -   Form: ['tag_id', ...] 
            -   Returns: class_deleted and point_edited data.
        - classes_deleted
            -   Desc: When one or more classes are deleted to the table, can take data for a point_deleted action.
            -   Takes: Dictionary of tag ids for class data.
            -   Form: {'tag_id': ('identifier', 'class_name', 'hex_code', 'index'), ...}
            -   Returns: class_added and point_added data.
        - class_edited
            -   Desc: When a class' name, color and/or identifier number is modified.
            -   Takes: Tuple with the tag id and the class' previous attributes.
            -   Form: ('tag_id', 'identifier', 'class_name', 'hex_code')
            -   Returns: class_edited data. \\
        __________________________________________________________________________________________________________
        - polypoints_added 
            -   Desc: When polygon points are added to the image. 
            -   Takes: List of point indexes. 
            -   Form: ['index', ...] 
            -   Returns: markpoints_edited data.
        - polypoints_deleted  
            -   Desc: When polygon points are deleted. 
            -   Takes: List of tuples with each of the point's tags. 
            -   Form: [('point', 'coordx coordy', 'index', 'tag_id'), ...] 
            -   Returns: markpoints_added data \\
        __________________________________________________________________________________________________________
        - annpolys_added
            -   Desc: When one or more annotation polygons are completed.
            -   Takes: List of polygon ids.
            -   Form: ['polygon_id', ...]
            -   Returns: annpolys_deleted data.
        - annpolys_deleted
            -   Desc: When one or more annotation polygons are deleted.
            -   Takes: List of AnnPoly objects.
            -   Form: [AnnPoly obj, ...]
            -   Returns: annpolys_added data.
        - annpolys_edited
            -   Desc: When one or more annotaion polygons are edited. 
            -   Takes: Tuple with the polygon's tags.
            -   Form: ('ann-poly', 'polygon_id', 'x1 y1 x2 y2 ...', 'tag_id')
            -   Returns: annpolys_edited data.\\
        __________________________________________________________________________________________________________
        - moved_page
            -   Desc: When the user moves between pages.
            -   Takes: The number of the previous page.
            -   Form: page_number
            -   Returns: moved_page data.
    
        """
        self.action_name: _actionType = action_name
        self.primary_data = primary_data
        self.secondary_data = secondary_data
    
    def __call__(self) -> tuple[_actionType, Any, Any]:
        """Handles what reaction to run based on the given action.

        Returns:
            reaction_data (tuple[str, Any, (Any | None)]): Tuple containing the data for a reaction.
        """
        reaction_names: dict[_actionType, _actionType] = {
            'markpoints_added': 'markpoints_deleted',
            'markpoints_deleted': 'markpoints_added',
            'markpoints_edited': 'markpoints_edited',
            'classes_added': 'classes_deleted',
            'classes_deleted': 'classes_added',
            'class_edited': 'class_edited',
            'polypoints_added': 'polypoints_deleted',
            'polypoints_deleted': 'polypoints_added',
            'annpolys_added': 'annpolys_deleted',
            'annpolys_deleted': 'annpolys_added',
            'annpolys_edited': 'annpolys_edited',
            'moved_page': 'moved_page'
        }

        primary_reaction_data: Any = None
        secondary_reaction_data: Any  = None
        
        if self.action_name == 'markpoints_added': 
            primary_reaction_data = self.markpoints_added(self.primary_data)
        elif self.action_name == 'markpoints_deleted': 
            primary_reaction_data = self.markpoints_deleted(self.primary_data)
        elif self.action_name == 'markpoints_edited': 
            primary_reaction_data = self.markpoints_edited(self.primary_data)
        elif self.action_name == 'classes_added': 
            primary_reaction_data, secondary_reaction_data = self.classes_added(self.primary_data)
        elif self.action_name == 'classes_deleted':
            primary_reaction_data = self.classes_deleted(self.primary_data)
            if self.secondary_data is not None: Action(*self.secondary_data())
        elif self.action_name == 'class_edited': 
            primary_reaction_data = self.class_edited(self.primary_data)
        elif self.action_name == 'polypoints_added': 
            primary_reaction_data = self.polypoints_added(self.primary_data)
        elif self.action_name == 'polypoints_deleted': 
            primary_reaction_data = self.polypoints_deleted(self.primary_data)
        elif self.action_name == 'annpolys_added': 
            primary_reaction_data = self.annpoly_added(self.primary_data)
            if self.secondary_data is not None: secondary_reaction_data = Action(*self.secondary_data())
        elif self.action_name == 'annpolys_deleted': 
            primary_reaction_data = self.annpoly_deleted(self.primary_data)
            if self.secondary_data is not None: secondary_reaction_data = Action(*self.secondary_data())
        elif self.action_name == 'annpolys_edited': 
            primary_reaction_data = self.annpoly_edited(self.primary_data)
        elif self.action_name == 'moved_page': 
            primary_reaction_data = self.moved_page(self.primary_data)
            if self.secondary_data is not None: secondary_reaction_data = Action(*self.secondary_data())
        
        return reaction_names[self.action_name], primary_reaction_data, secondary_reaction_data
    
    def markpoints_added(self, point_indexes: Optional[list[str]]) -> list[tuple[str]] | None: 
        """Removes the added marking points.

        Args:
            point_indexes (list[str] | None): List of point indexes.

        Returns:
            point_tags (list[tuple[str]] | None): List of point tags.
        """
        if point_indexes is None: return
        tags = []
        for point in point_indexes:
            tags.append(MAIN.canvas.gettags(MAIN.canvas.find_withtag(point)))
            MAIN.canvas.delete(point)
        return tags

    def markpoints_deleted(self, point_tags: Optional[list[tuple[str]]]) -> list[str] | None: 
        """Re-adds deleted marking points.

        Args:
            point_tags (list[tuple[str]] | None): List of point tags.

        Returns:
            point_indexes (list[str] | None): List of point indexes.
        """
        if point_tags is None: return
        return [MAIN.redraw_markpoint(tags) for tags in point_tags]
    
    def markpoints_edited(self, point_tags: list[tuple[str]]) -> list[tuple[str]]:
        """Reverts a marking point edition.

        Args:
            point_tags (list[tuple[str]]): List of old point tags.

        Returns:
            point_tags (list[tuple[str]]): List of the edited point tags.
        """
        point_tags = []
        for tags in point_tags:
            point_tags += MAIN.change_markpoint_color(tags[3], tags[2])
        return point_tags
    
    def classes_added(self, class_tag_ids: list[str]) -> dict[str, tuple[Any]]: 
        """Removes added classes.

        Args:
            class_tag_ids (list[str]): List of class tag ids.

        Returns:
            class_data (dict[str, tuple[Any]]): Dictionary with class data.
        """
        return SIDE.remove_classes(False, class_tag_ids, False)

    def classes_deleted(self, classes_tags: dict[str, tuple[Any]]) -> list[str]:
        """Re-adds deleetd classes.

        Args:
            classes_tags (dict[str, tuple[Any]]): Dictionary with class data.

        Returns:
            class_tag_ids (list[str]): List of class tag ids.
        """
        for tag_id, data in classes_tags.items():
            SIDE.add_class(*data, tag_id)
        return list(classes_tags.keys())
        
    def class_edited(self, class_tags: tuple[str]) -> tuple[str]:
        """Reverts a class edition.

        Args:
            class_tags (tuple[str]): Tuple containing old class data. 

        Returns:
            tuple[str]: Tuple containing the edited class data.
        """
        tag_id, cur_index, class_name, class_color, *_ = class_tags
        cur_class = WINDOW.images[0].classes[tag_id]
        
        redo_action: tuple[str] = tag_id, *[str(value) for value in cur_class.values()]
        item = SIDE.val_table.tag_has(tag_id)[0]
        
        # checking each value against the original and acting/updating when needed 
        if cur_index != cur_class['id']:
            WINDOW.images[0].classes[tag_id].update({'id': cur_index})
            SIDE.move_class(item, int(cur_index))
        if class_name != cur_class['name']:
            WINDOW.images[0].classes[tag_id].update({'name': class_name})
            values = SIDE.val_table.item(item, 'values')
            SIDE.val_table.item(item, values= [values[0], values[1], class_name, values[3], values[4]])
        if class_color != cur_class['hex']:
            WINDOW.images[0].classes[tag_id].update({'hex': class_color})
            SIDE.color_table.tag_configure(tag_id, background=class_color)
            item = SIDE.color_table.tag_has(tag_id)
            SIDE.color_table.item(item, tag=(tag_id, class_color))
            mode = MAIN.images[0].mode
            if mode == 'semiauto': MAIN.change_markpoint_color(tag_id, tag_id)
            elif mode == 'manual': MAIN.change_annpolygon_color(tag_id)
            
        SIDE.check_pos()
        
        return redo_action

    def polypoints_added(self, tag: str) -> dict[str, list[float]]: 
        """Removes the added polygon points.

        Args:
            point_indexes (list[str]): List of point indexes.

        Returns:
            polypoint_data (tuple[list[tuple[str]], list[int], str]): Tuple containing data for reconstructing the deletd polygon points.
        """
        
        return MAIN.remove_polypoints(tag, False)

    def polypoints_deleted(self, point_pos: dict[str, list[float]]) -> list[str]: 
        """Re-adds deleted polygon points.

        Args:
            line_data (list[tuple[str, ...]]): List of tuples containg the tags of each deleted line.
            new_lines (list[int]): List of ids for each new_line
            tag_id (str): Class tag id.

        Returns:
            list[str]: List of point indexes.
        """
        
        tags = []
        for point_id, pos in point_pos.items():
            coords = pos[0]/MAIN.last_image_ratio[0], pos[1]/MAIN.last_image_ratio[1]
            tags.append(MAIN.draw_polypoint(*coords, False, point_id))
        
        if len(tags) == 1: return tags[0]
        else: return 'poly-point'
    
    def annpoly_added(self, polygon_ids: list[str]) -> list[AnnPoly]:
        """Removes added annotation polygons.

        Args:
            polygon_ids (list[str]): List of polygon ids.

        Returns:
            polygons (list[AnnPoly]): List of annotation polygon objects.
        """
        polygons: list[AnnPoly] = []
        for polygon_id in polygon_ids:
            polygons += MAIN.remove_annpolygons(polygon_id)
        return polygons
    
    def annpoly_deleted(self, polygons: list[AnnPoly]) -> list[str]:
        """Re-adds deleted annotation polygons.

        Args:
            polygons (list[AnnPoly]): List of annotation polygon objects.

        Returns:
            polygon_ids (list[str]): List of polygon ids.
        """
        MAIN.cur_image.ann_polys += polygons
        polygon_ids = []
        for polygon in polygons:
            polygon_ids.append(
                MAIN.redraw_annpolygon('ann-poly',
                                       polygon.polygon_id,
                                       ' '.join(str(coord) for coord in polygon.point_coords),
                                       polygon.classe)
            )
        return polygon_ids
        
    def annpoly_edited(self, tags: tuple[str]) -> tuple[str]:
        """Reverts annotation polygon edition.

        Args:
            tags (tuple[str]): Tuple containing old polygon tags.

        Returns:
            tags (tuple[str]): Tuple containing the edited polygon tags.
        """
        polygon_id = tags[1]
        old_tags = MAIN.canvas.gettags(MAIN.canvas.find_withtag(polygon_id))
        MAIN.canvas.delete(polygon_id)
        MAIN.redraw_annpolygon(*tags)
        return old_tags
    
    def moved_page(self, page_num: int) -> int: 
        """Goes back to the last visited image.

        Args:
            page_num (int): Index of the last visted image.

        Returns:
            int: Index of the current image.
        """
        cur_page = MAIN.cur_image.index
        MAIN.skip_image(page_num, False)
        return cur_page

    def __str__(self):
        return f'Action({self.action_name}, {self.primary_data}, {self.secondary_data})'


# ========================================================== #
# ========================================================== #

#* Completamente documentado
class MainWindow(tkb.Window):
    """Class that constructs and handles the main window of program.
    """
    def __init__(self) -> None:
        """Class that constructs and handles the main window of program.
        """
        super().__init__(title="EasyMark", minsize=(1000, 450))
        register_themes()
        use_theme(self, CONFIG.get('theme', 'dark'))
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        self.loader = ImageLoader(self, FOLDER_PATHS['CONFIG'], CONFIG, _)
        self.images: list[ImageData | None] = self.loader.images
        self.saved: bool = True
        self.gen_vars = {
            'default_output': tkb.StringVar(value=CONFIG['default_output'])
        }
        
        self.main_binds()
        self.main_widgets()
        
        if 'DEBUG' in CONFIG:
            self._bind_DEBUG(None)
        
        self.after(ms=1000, func= lambda *x: self.check_backup())
        self.after(ms=120000, func=lambda *x: self.backup())
    
    def main_widgets(self) -> None:
        """Calls to construct the menu bar and the main frame for display.
        """
        top_bar = MenuBar(self)
        self.config(menu=top_bar)
        
        self.display = DisplayMaker(self)
    
    def main_binds(self) -> None:
        """Sets the windows main shortcus.
        """
        self.bind("<Control-KeyRelease-s>", self._save)
        self.bind("<Control-KeyRelease-S>", self._save)
        self.bind("<Control-KeyRelease-n>", self._load)
        
        self.bind("<ButtonPress>", self._unfocus)
        
        self.protocol('WM_DELETE_WINDOW', self._close_window)
        
        if CONFIG.get('dev_mode', False): self._bind_DEBUG()
        else: self.bind("<Alt-KeyPress-End>", self._bind_DEBUG)
    
    def check_backup(self) -> None:
        """Checks for backup project files on initialization.
        """
        check_baks = [file for file in os.listdir(FOLDER_PATHS['CONFIG']) if '.bak' in file]
        if len(check_baks) == 0: return
        
        load_bak = messagebox.askyesno(title="Backup found",
                                       message="Backup file found, would you like to load it?")
        if load_bak:
            self.loader.select_datafile(preset_path=check_baks[0])
        for bak in check_baks:
            os.remove(os.path.join(FOLDER_PATHS['CONFIG'], bak))
    
    def backup(self) -> None:
        """Creates abackup project file every five minutes.
        """
        if self.images[0] is not None and self.images[0].mode != 'resuts':
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
        self.display.main.save_markpoints_toimage()
        e = str(event).lower()
        save_mode = 'choose' if 'shift' in e \
                 else 'normal'
        self.saved = self.loader.save_project(save_mode)
        
    def _load(self, event: tk.Event) -> None:
        """Handler for loading projects.

        Args:
            event (tk.Event): Tkinter click event.
        """
        e = str(event).lower()
        if 'shift' in e:
            self.loader.select_datafile()
        else:
            self.loader.select_directory(self)
    
    def _close_window(self) -> None:
        """Handler for closing the main window. Prompts the user to save an unsaved project.
        """
        self.display.main._closing_funcs()
        if not self.saved:
            self.loader.save_project('backup')
            permit_close = self.loader.save_unsaved()
        else: permit_close = True
        
        with open(CONFIG_FILE_PATH, 'w') as file:
            json.dump(CONFIG, file, indent=4)
        
        if permit_close:
            if self.images[0] is not None:
                self.images[0].clean()
            self.destroy()
    
    def _update(self) -> None:
        """First step on the update cascade.
        """
        self.saved = True
        self.display._update()

    # ---------------------------------------------------------- #
    
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
            e (tk.Event, optional): Tkinter click event.. Defaults to None.
        """
        if e is not None:
            event = str(e).lower()
            if "control" not in event or not 'shift' in event: return
            messagebox.showwarning(title='DEBUG', message='Debug mode active')
        
        self.activate_debug_key = tkb.BooleanVar(value=False)
        self.bind("<Control-Key-1>", lambda *x: print(self.images[0].classes))
        self.bind("<Control-Key-2>", lambda *x: self.display.side._create_example_info(6))
        self.bind("<Control-Key-3>", lambda *x: print(f'Undo Stack: {''.join([f"\n> {action}"  for action in self.display.undo_stack])}'))
        self.bind("<Control-Key-4>", lambda *x: print(f'Redo Stack: {''.join([f"\n   > {action}"  for action in self.display.redo_stack])}'))
        self.bind("<Control-Key-5>", lambda *x: print(self.display.main.clean_canvas()))
        self.bind("<Control-Key-6>", lambda *x: print(f'Classes: {"".join([f"\n    > {id_tag}: {data}" for id_tag, data in self.images[0].classes.items()])}'))
        self.bind("<Control-Key-7>", lambda *x: print(f'Marks {"".join([f"\n    > {id_tag}: {coords}" for id_tag, coords in self.images[0].cur_image().marks.items()])}'))
        self.bind("<Control-Key-8>", lambda *x: print(self.images[0].cur_image()))
        self.bind("<Control-Key-9>", lambda *x: print(f'Config: {"".join([f"\n  > {name}: {val}" for name, val in CONFIG.items()])}'))
        self.bind("<Control-Key-0>", lambda *x: self.activate_debug_key.set(value=False) if self.activate_debug_key.get()
                                                        else self.activate_debug_key.set(value=True))
        self.bind("<KeyRelease-space>", self._key_DEBUG)

    def _nametowidget(self, name: str | tk.Misc | Tcl_Obj) -> Any:
        try:
            return super().nametowidget(name)
        except KeyError:
            return name

# ========================================================== #
# ========================================================== #


class MenuBar(tkb.Menu):
    def __init__(self, mestre: MainWindow) -> None:
        super().__init__(master=mestre,
                         borderwidth=5,
                         relief='raised',
                         type='menubar')
        self.window = mestre
        self.loader = mestre.loader
        self.file_menu()
        self.tools_menu()
        self.options_menu()

#* ====================================================================== #

    def file_menu(self) -> None:
        file_options = tkb.Menu(master=self, tearoff=0, relief='ridge', borderwidth=5)
        
        open_menu = self.open_menu(file_options)
        
        file_options.add_cascade(label=_("Open"), menu=open_menu)
        file_options.add_command(label=_("Save"), command= lambda *x: self.save_project('normal'))
        file_options.add_command(label=_("Save as"), command= lambda *x: self.save_project('choose'))
        file_options.add_command(label=_("Export"), command= lambda *x: ExporterWindow(self.window))
        self.add_cascade(label=_('File'), menu=file_options)
    
    def save_project(self, save_mode: Literal['normal', 'choose', 'backup']) -> None:
        if self.window.images[0] == None: return
        if self.window.images[0].mode == 'semiauto': self.window.display.main.save_markpoints_toimage()
        self.loader.save_project(save_mode)
    
    def open_menu(self, mark_options: tkb.Menu) -> tkb.Menu:
        open_options = tkb.Menu(master=mark_options)
        
        recent_options = self.recent_menu(open_options)
        
        open_options.add_command(label=_("New"), command= lambda *x: newProjectMenu())
        open_options.add_command(label=_("Continue"), command= lambda *x: self.loader.select_datafile())
        open_options.add_cascade(label=_("Recent"), menu=recent_options)
        return open_options    
    
    def recent_menu(self, open_options: tkb.Menu) -> tkb.Menu:
        recent_options = tkb.Menu(master=open_options)
        for path in CONFIG['recent']:
            recent_options.add_command(label=path, command= lambda x=path, *y: self.loader.select_datafile(preset_path=x))
        return recent_options

#* ====================================================================== #
    
    def tools_menu(self) -> None:
        tools_options = tkb.Menu(master=self, tearoff=0, relief='ridge', borderwidth=5)
        
        tools_options.add_command(label=_("Automatic annotation"), command= lambda *x: DetectiontoProjectWindow(self.window))
        
        self.add_cascade(label=_("Tools"), menu=tools_options)

    def options_menu(self) -> None:
        extra_options = tkb.Menu(master=self, tearoff=0, relief='ridge', borderwidth=5)
        
        extra_options.add_command(label=_("Configs"),  command= lambda *x: configMenu())
        extra_options.add_command(label=_("Shorcuts"), command= lambda *x: shortcutsMenu())
        self.add_cascade(label=_("Options"), menu=extra_options)
    
    def _unfocus(self, config_window: tkb.Toplevel) -> None:
        x, y = self.winfo_pointerxy()
        widget = str(self.winfo_containing(x, y))
        if 'entry' not in widget \
          or 'spinbox' not in widget: 
              config_window.focus()

class newProjectMenu(tkb.Toplevel):
    def __init__(self) -> None:
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
        self.sec_mode_display_var = tkb.StringVar(value=_('Polygon'))
        self.sec_mode_var = tkb.StringVar(value='polygon')

        self.arq_icon = get_icon()
        
        self.configs_constructor()
        
    def configs_constructor(self) -> None:
        mode_label = tkb.Label(master=self.open_popup_frame, text=_("Annotation mode"))
        mode_tooltip_signal = tkb.Label(master=self.open_popup_frame, text="!", font=("Arial", 12, 'bold'), style='EasyMark.TooltipSignal.TLabel')
        tooltip_text = f'{_("Manual annotation")}: \n'+\
                       f'{_("    Draw shapes around objects of interest to annotate them.")}\n'+\
                       f'{_("Semi-automatic annotation")}: \n'+\
                       f'{_("    Place seeds on objects of interest and later run an AI model to isolate them.")}'
        mode_tooltip = ToolTip(widget=mode_tooltip_signal, text=tooltip_text, wraplength=600)
        
        mode_button = tkb.Menubutton(master=self.open_popup_frame, width=15, textvariable=self.mode_display_var)
        mode_menu = tkb.Menu(master=mode_button, tearoff=0, relief='ridge', borderwidth=5)
        for option, label in [('manual', _('Manual')), ('semiauto', _('Semi-automatic'))]:
            mode_menu.add_radiobutton(label=label, value=option,
                                      command=lambda x=option, y=label, *z: self.set_mode(sec_mode_button, mode_tooltip, x, y))
        mode_button.config(menu=mode_menu)
        
        sec_mode_button = tkb.Menubutton(master=self.open_popup_frame, width=15, textvariable=self.sec_mode_display_var)
        sec_mode_menu = tkb.Menu(master=sec_mode_button, tearoff=0, relief='ridge', borderwidth=5)
        for option, label in {'polygon': _('Polygon'), 'bbox': _('Bounding Box')}.items():
            sec_mode_menu.add_radiobutton(label=label, value=option,
                                          command=lambda x=option, y=label, *z: self.set_sec_mode(x, y))
        sec_mode_button.config(menu=sec_mode_menu)
        
        
        path_label = tkb.Label(master=self.open_popup_frame, text=_('Image directory'))
        path_entry = tkb.Entry(master=self.open_popup_frame, textvariable=self.path_var, width=50)
        path_button = tkb.Button(master=self.open_popup_frame, image=self.arq_icon, style='Outline.Toolbutton',
                                 command= lambda *x: self.get_imgdir())
        
        confirm_button = tkb.Button(master=self.open_popup_frame, text=_("Open"), command= lambda *x: self.open_function())
        
        
        mode_label.grid(column=0, row=0, pady=2, padx=(2, 0), sticky='w')
        mode_tooltip_signal.grid(column=1, row=0, sticky='w')
        mode_button.grid(column=0, row=1, columnspan=2, pady=2, padx=(2, 0), sticky='we')
        sec_mode_button.grid(column=2, row=1, pady=2, padx=(2, 0), sticky='we')
        
        path_label.grid(column=0, row=4, pady=2, padx=(2, 0), sticky='nswe')
        path_entry.grid(column=0, row=5, columnspan=3, pady=2, padx=(2, 0), sticky='we')
        path_button.grid(column=3, row=5, pady=2, padx=(2, 0))
        
        tkb.Separator(master=self.open_popup_frame).grid(column=0, columnspan=4, row=6, sticky='we', pady=(4, 0))
        confirm_button.grid(column=3, row=7, pady=2, padx=(2, 0), sticky='nsew')
        
    def set_mode(self, sec_mode_button: tkb.Button, mode_tooltip: ToolTip, option: str, label: str) -> None:
        self.mode_var.set(value=option)
        self.mode_display_var.set(value=label)
        
        if option == 'manual':
            sec_mode_button.config(state='normal')
            self.sec_mode_var.set(value='polygon')
            mode_tooltip.text = _('Draw shapes around objects of interest to annotate them.')
            self.sec_mode_display_var.set(value=_("Polygon"))
        elif option == 'semiauto':
            sec_mode_button.config(state='disabled')
            self.sec_mode_var.set(value='')
            mode_tooltip.text = _('Place seeds over objects of interest and run an AI to annotate the images automatically.')
            self.sec_mode_display_var.set(value="")
    
    def set_sec_mode(self, option: str, label: str) -> None:
        self.sec_mode_var.set(option)
        self.sec_mode_display_var.set(label)
    
    def get_imgdir(self) -> None:
        path, _ = WINDOW.loader.select_directory(self)
        if path is None: self.path_var.set(value='')
        else: self.path_var.set(value = path)
    
    def open_function(self) -> None:
        path, classes = WINDOW.loader.select_directory(self, self.path_var.get())
        if path is None: return
        mode = self.mode_var.get()
        sec_mode = self.sec_mode_var.get()
        
        WINDOW.loader.load_directory(path, mode, sec_mode, classes)
        close_window(self)

class configMenu(tkb.Toplevel):
    def __init__(self) -> None:
        super().__init__(master=WINDOW, title=_("Configuration"), resizable=(False, False))
        base_toplevel_binds(self)
        
        self.config_frame = tkb.Frame(master=self, relief='raised', padding=10)
        self.config_frame.grid(column=0, row=0, sticky='nsew')
        for i in range(2):
            self.config_frame.rowconfigure(i, weight=1)
        self.config_frame.columnconfigure(0, weight=1)
        self.language_display = tkb.StringVar(value=f'{LANG.name if LANG.name != '' else "English"}')
        self.theme_display = tkb.StringVar(value=_(CONFIG.get('theme', 'dark').capitalize()))
        self.path_var = tkb.StringVar(value=CONFIG['default_output'])
        self.arq_icon = get_icon()
            
        self.configs_constructor()
       
    def configs_constructor(self) -> None:
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
        
        path_entry.bind('<KeyRelease>', lambda *x: self.check_dir())
    
    def change_window_theme(self, theme: str, label: str) -> None:
        self.theme_display.set(label)
        CONFIG['theme'] = theme
        self.arq_icon = get_icon()
        self.path_button.configure(image=self.arq_icon)
        use_theme(WINDOW, theme)
        WINDOW._update()
    
    def change_lang(self, lang_code: str) -> None:
        self.language_display.set(LANGUAGES[lang_code])
        CONFIG['lang_code'] = lang_code
        if lang_code == ":)": lang_code = 'smile'
        with open(os.path.join(FOLDER_PATHS['LOCALE'],f'{lang_code}.json'), 'r') as file:
            lang = json.load(file)
        messagebox.showinfo(master=self,
                            title=lang['lines']["Language setting changed"],
                            message=lang['lines']["You will need to close and open the app for changes to take effect."])
    
    def get_output_dir(self) -> None:
        dir_path = filedialog.askdirectory(title=_("Select default output directory"), mustexist=True, parent=self)
        if dir_path in [None, '', ()]: return
        if not os.path.isdir(dir_path):
            messagebox.showerror(title=_("Invalid directory"),
                                message=_("The selected directory does not exist."),
                                master=self)
            return
        
        CONFIG['default_output'] = dir_path
    
    def check_dir(self) -> bool:
        path = self.path_var.get()
        if os.path.isdir(path) and not path.isspace():
            CONFIG['default_output'] = path
            return True
        return False

class shortcutsMenu(tkb.Toplevel):
    def __init__(self) -> None:
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
        col_data = {
            'shortcut': (150, 'center', True, _("Shortcut")),
            'function': (150, 'center', True, _("Function"))
        }
        self.shortcuts_tree = tkb.Treeview(self.shortcuts_frame, show='headings', columns=list(col_data.keys()))
        self.shortcuts_tree.pack(fill='both', expand=True)
        
        for col, data in col_data.items():
            self.shortcuts_tree.column(col, 
                                  width=data[0],
                                  anchor=data[1],
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


class DisplayMaker(tkb.Frame):
    def __init__(self, mestre: MainWindow) -> None:
        super().__init__(master=mestre, relief='raised')
        self.mestre = mestre
        self.images = mestre.images

        self.undo_stack: list[Action] = []
        self.redo_stack: list[Action] = []
        self.last_stack_len: int = 0
        self.max_stack_size = 40

        
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        
        self.grid(column=0, row=0, sticky='nsew')
        
        self.poly_progress: bool = False
        
        self.side = Sidebar(self)
        self.main = MainVisualizer(self)
        self.low = LowerBar(self)
        
        self.side.binds(self.main.canvas)
        self.binds()

    def rodape(self) -> None:
        rodape = tkb.Frame(master=self, relief='groove', padding=3)
        rodape.grid(column=0, columnspan=2, row=2, sticky='nsew')
        
        texto_rodape = tkb.Label(master=rodape, text='Developed by NADIA - UFSM-CS', font=font.Font(size=7, weight='bold'), cursor='hand2')
        tooltip_rodape = ToolTip(texto_rodape, f"{_("Data Science and Artificial Inteligence Center")}\n{_("Federal University of Santa Maria - Cachoeira do Sul")}", wraplength=600)
        texto_rodape.bind("<Button-1>", lambda *x: webbrowser.open_new_tab('https://github.com/NADIA-UFSM/EasyMark'))
        texto_rodape.pack(side='right')
        
    def action_handler(self, handle: Optional[Literal['undo', 'redo']] = None) -> None:
        if handle == 'undo':
            stack_a = self.undo_stack
            stack_b = self.redo_stack
        elif handle == 'redo':
            stack_a = self.redo_stack
            stack_b = self.undo_stack
            
        if len(stack_a) == 0: 
            return
        action = stack_a.pop()
        reverse_action = action()
        if reverse_action[1] is None: return
        stack_b.append(Action(*reverse_action))
        
    def clean_stacks(self, clear: bool = False) -> None:
        try:
            if len(self.undo_stack) != self.last_stack_len:
                self.last_stack_len = len(self.undo_stack) 
                self.mestre.saved = False
            else: self.mestre.saved = True
        except AttributeError: pass
        
        max_stack = 0 if clear else self.max_stack_size
        while len(self.undo_stack) > max_stack:
            del self.undo_stack[0]
        while len(self.redo_stack) > max_stack:
            del self.redo_stack[0]
    
    def binds(self) -> None:
        self.mestre.bind("<Control-KeyRelease-z>", lambda *x: self.action_handler('undo'))
        self.mestre.bind("<Control-KeyRelease-y>", lambda *x: self.action_handler('redo'))
    
    def style_update(self) -> None:
        self.style.configure
        pass
    
    def _update(self) -> None:
        self.side._update()
        self.main._update()
        self.low.update_labels()
        self.clean_stacks(True)


# ========================================================== #
# ========================================================== #


class LowerBar(tkb.Frame):
    def __init__(self, mestre: DisplayMaker) -> None:
        super().__init__(master=mestre, 
                         relief='raised', 
                         borderwidth=5)

        self.mestre = mestre
        self.window = mestre.mestre
        self.loader = mestre.mestre.loader
        self.images = mestre.images
        
        self.lowerbar_vars = {
            'mode': tkb.StringVar(value= _('Mode: ') + _('No project started')),
            'creation': tkb.StringVar(value=_('Creation: ') + _('No date')),
            'last_mod': tkb.StringVar(value=_('Last modified: ') + _('No date')),
            'lastbak': tkb.StringVar(value=_('Last backup: ') + _('No backup')),
            'imgdir': tkb.StringVar(value=_('Image directory: ') + _('No directory selected')),
            'marksdir': tkb.StringVar(value=_('Marks directory: ') + _('No marks saved'))
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
        if self.images[0] is None: 
            self.lowerbar_vars['mode'].set(_('Mode: ') + _('No project started'))
            self.lowerbar_vars['creation'].set(_('Creation: ') + _('No date'))
            self.lowerbar_vars['last_mod'].set(_('Last modified: ') + _('No date'))
            self.lowerbar_vars['lastbak'].set(_('Last backup: ') + _('No backup'))
            self.lowerbar_vars['imgdir'].set(_('Image directory: ') + _('No directory selected'))
            self.lowerbar_vars['marksdir'].set(_('Marks directory: ') + _('No marks saved'))
            return
        self.lowerbar_vars['mode'].set(_('Mode: ') + self.images[0].mode.capitalize() + ' - ' + self.images[0].sec_mode.capitalize())
        self.lowerbar_vars['creation'].set(_('Creation: ') + self.images[0].date_create)
        self.lowerbar_vars['imgdir'].set(_('Image directory: ') + self.images[0].directory)
        self.tooltips['imgdir'].text = self.images[0].directory
        if self.images[0].date_last != '':
            self.lowerbar_vars['last_mod'].set(_('Last modified: ') + self.images[0].date_last)
            self.lowerbar_vars['marksdir'].set(_('Marks directory: ') + self.loader.last_saved_dir)
            self.tooltips['marksdir'].text = self.loader.last_saved_dir
        if bak_date != '':
            self.lowerbar_vars['lastbak'].set(_('Last backup: ') + bak_date)


# ========================================================== #
# ========================================================== #


class Sidebar(tkb.Frame):
    def __init__(self, mestre: DisplayMaker) -> None:
        super().__init__(master=mestre, 
                         borderwidth=5, 
                         relief='ridge', 
                         width=200)
        self.mestre = mestre
        self.window = mestre.mestre
        self.images = mestre.images

        self.undo_stack = mestre.undo_stack
        self.redo_stack = mestre.redo_stack
        
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
        col_data = {
            'color': (50, 'w', True, _('Color')),
            'sel': (20, 'center', False, ''),
            'id': (40, 'w', False, 'ID'),
            'class': (150, 'w', True, _('Class')),
            'num': (40, 'e', False, 'N°'),
            'vis': (40, 'center', False, 'Vis'),
        }
        
        self.color_table = tkb.Treeview(self, 
                                        columns=list(col_data.keys())[0], 
                                        show='headings')
        self.val_table = tkb.Treeview(self, 
                                      columns=list(col_data.keys())[1:], 
                                      show='headings')
        
        self.color_table.column('color', 
                                width=col_data['color'][0],
                                anchor=col_data['color'][1],
                                stretch=col_data['color'][2])
        self.color_table.heading('color', text=col_data['color'][3])
        for col, data in list(col_data.items())[1:]:
            self.val_table.column(col, 
                                  width=data[0],
                                  anchor=data[1],
                                  stretch=data[2])
            self.val_table.heading(col, text=data[3])
        
        self.update_item_color()
        
        self.color_table.grid(column=0, row=0, rowspan=2, sticky='nsew', pady=[0, 3])
        self.val_table.grid(column=1, columnspan=4, row=0, rowspan=2, sticky='nsew', pady=[0, 3])
    
    def update_item_color(self) -> None:
        background1 = self.window.style.configure('EasyMark.Treeview.itemcolor')['background1']
        background2 = self.window.style.configure('EasyMark.Treeview.itemcolor')['background2']
        self.val_table.tag_configure('True', background=background1)
        self.val_table.tag_configure('False', background=background2)
    
    def _create_example_info(self, quant: int, i: int = 0):
        hex_code = f'#{randint(0, 255):02x}{randint(0, 255):02x}{randint(0, 255):02x}'            
        class_name = ''.join(randchoices(ascii_lowercase, k=randint(5, 15)))

        self.add_class(class_name=class_name, hex_code=hex_code, )
        
        i += 1
        if quant - i > 0:
            self._create_example_info(quant, i)

    # ---------------------------------------------------------- #

    def adder_constructor(self) -> None:
        self.hex_var = tkb.StringVar(value=self.window.style.configure('EasyMark.ColorDisplay1.TFrame')['background'])
        name_var = tkb.StringVar(value=_('Class name'))

        color_frame = tkb.Frame(master=self, width=30, height=29,relief='groove', borderwidth=2,
                                style='EasyMark.ColorDisplay1.TFrame')
        ToolTip(color_frame, text=_('Pick a color'))
        name_entry = tkb.Entry(master=self,
                               textvariable=name_var,
                               name='class_name_entry',
                               style='EasyMark.Base.TEntry')
        add_button = tkb.Button(master=self, 
                                text=_('Add class'), 
                                command= lambda *x: \
                                    self.add_class(class_name=name_var.get(), hex_code=self.hex_var.get())
                                )
        
        color_frame.grid(column=0, row=2, sticky='new')
        name_entry.grid(column=1, columnspan=3, row=2, sticky='new', padx=2)
        add_button.grid(column=4, row=2, sticky='new')
        
        
        name_var.trace_add('write', callback= lambda*x: self.validate_name(name_entry, name_var))
        
        color_frame.bind('<Button-1>', lambda *x: self.choose_color())
        name_entry.bind("<FocusOut>", lambda *x: self.validate_name(name_entry, name_var))
        name_entry.bind("<FocusIn>", lambda *x: self.validate_name(name_entry, name_var))
        name_entry.bind("<KeyRelease-Return>", lambda *x: \
                                    self.add_class(class_name=name_var.get(), 
                                                   hex_code=self.hex_var.get()))
        
        self.validate_name(name_entry, name_var)

    def validate_name(self, name_entry: tkb.Entry, name_var: tkb.StringVar) -> None:
        name = name_var.get()
        name_entry.configure(style='EasyMark.Active.TEntry')
        if self.window.focus_get() != name_entry:
            if name == '':
                name_entry.configure(style='EasyMark.Base.TEntry')
                name_var.set(_("Class name"))
                return 
            if name == _("Class name"):
                name_entry.configure(style='EasyMark.Base.TEntry')
                return
        if name in [self.val_table.set(row, 'class') 
                    for row in self.val_table.get_children()]:
            name_entry.configure(style='EasyMark.Active.TEntry')
        if name == _("Class name"):
            name_var.set('')
        name_entry.configure(style='EasyMark.Active.TEntry')

    def choose_color(self) -> None:
        color_chooser = ColorDialog(title=_("Color Chooser"))
        color_chooser
        color_chooser.show()
        color = color_chooser.result
        if color is None: return
        hex_code = color.hex
        WINDOW.style.configure('EasyMark.ColorDisplay1.TFrame', background=hex_code)
        self.hex_var.set(hex_code)

    # ---------------------------------------------------------- #

    def add_class(self, 
                  identifier: Optional[int] = None, 
                  class_name: str = '', 
                  hex_code: str = '', 
                  visible: bool = True,
                  start_index: int | str = 'end', 
                  tag_id: Optional[str] = None) -> str:
        if self.images[0] is None or self.mestre.poly_progress: return
        
        rand_hex = f'#{randint(0, 255):02x}{randint(0, 255):02x}{randint(0, 255):02x}'
        self.hex_var.set(rand_hex)
        self.window.style.configure('EasyMark.ColorDisplay1.TFrame', background=rand_hex)
        
        new_class = tag_id is None
        
        if class_name in [self.val_table.set(row, 'class') 
                        for row in self.val_table.get_children()]: return
        
        if new_class:
            tag_id = "".join(randchoices(LETTERS1, k=6))
            while tag_id in list(self.images[0].classes.keys()):
                tag_id = "".join(randchoices(LETTERS1, k=6))
        
        self.color_table.insert(parent='', index=start_index, values=(''), tags=(tag_id, hex_code))
        self.color_table.tag_configure(tag_id, background=hex_code)
        
        item = self.val_table.insert(parent='', index=start_index)
        index = self.val_table.index(item)
        
        self.val_table.item(item, tags=[tag_id, f'{index %2 == 0}'],
                            values=(
                                    f'{'X' if len(self.images[0].classes) == 0 else ''}', 
                                    int(f'{index if identifier is None else identifier}'), 
                                    class_name, 
                                    0,
                                    'V'
                                )
                            )
        if len(self.images[0].classes) == 0: self.select_mark(item)
        
        if (new_class or start_index != 'end'):
            self.images[0].update_classes(tag_id, 
                                          {'id': int(f'{index if identifier is None else identifier}'), 
                                           'name': class_name, 
                                           'hex': hex_code, 
                                           'visible': visible})
        if start_index == 'end': 
            self.undo_stack.append(Action('classes_added', [tag_id]))
        else: 
            self.check_pos()
            return tag_id

    def remove_classes(self, 
                       selection: bool = True, 
                       tag_ids: list[str] | tuple[str] | None = None, 
                       delete_points: bool = True
                       ) -> dict[str, tuple[Any]] | None:
        x, y = self.winfo_pointerxy()
        widget = self.winfo_containing(x, y)
        if ('treeview' not in str(widget) and selection) or self.mestre.poly_progress: return
        
        if isinstance(tag_ids, list):
            deletion = {tag_id : self.val_table.tag_has(tag_id)[0] 
                         for tag_id in tag_ids}
        else:
            deletion = self.val_table.selection() if selection else tag_ids
            if len(deletion) == 0: return
            deletion = {self.val_table.item(item_id)['tags'][0] : item_id 
                         for item_id in deletion}
        
        if delete_points:
            confirm = messagebox.askyesno(title=_('Delete Class'),
                                          message=_('Deleting the class will also delete all related points') + '\n' +
                                                  _('Do you want to proceed? (This action is reversible)'))
            if not confirm: return
        
        
        redo_objects: list[tuple[str]|AnnPoly] = []
        redo_classes: dict[str, list[Any]] = {}
        for tag_id in deletion.keys():
            if self.images[0].mode == 'semiauto': redo_objects += [self.mestre.main.canvas.gettags(item) for item in self.mestre.main.canvas.find_withtag(tag_id)]
            else: redo_objects += MAIN.remove_annpolygons(tag_id)
            redo_classes[tag_id] = list(self.images[0].classes.pop(tag_id).values()) + [self.val_table.index(deletion[tag_id])]
            if delete_points: self.mestre.main.remove_markpoints(tag_id)
            
        for item_id in deletion.values():
            self.val_table.delete(item_id)
            self.color_table.delete(item_id)
        
        self.check_pos()
        
        secondary = None if len(redo_objects) == 0 else Action('markpoints_deleted', redo_objects) if self.images[0].mode == 'semiauto' else Action('annpolys_deleted', redo_objects)
        if not delete_points: return redo_classes, secondary
        else: 
            self.undo_stack.append(Action('classes_deleted', redo_classes, secondary))

    def check_pos(self, items: Optional[tuple[str]] = None, index: Optional[int] = None) -> None:
        if items is None:
            items = self.val_table.get_children()
            self.check_pos(items, 0)
        elif index == len(items): 
            self.images[0].sort_classes()
        else:
            item = items[index]
            val_data = self.val_table.item(item)
            
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
            self.images[0].classes[val_data['tags'][0]]['id'] = index
            
            self.check_pos(items, index+1)
        
            if len(self.val_table.tag_has('marker')) == 0:
                self.select_mark(items[0])

    def readd_classes(self) -> None:
        if len(self.images[0].classes) == 0: return
        for identifier, data in self.images[0].classes.items():
            self.add_class(*list(data.values()), tag_id=identifier)
        self.check_pos()

    def select_mark(self, marker_id: str) -> None:
        val_markers = self.val_table.tag_has('marker')
        for row in val_markers:
            val_data = self.val_table.item(row)
            self.val_table.item(row, 
                                values= [''] + val_data['values'][1:],
                                tags= [tag for tag in val_data['tags'] if tag != 'marker'])
        
        val_data = self.val_table.item(marker_id)
        self.val_table.item(marker_id, 
                            values= ['X'] + val_data['values'][1:],
                            tags= val_data['tags'] + ['marker'])
    
    # ---------------------------------------------------------- #
    
    def classes_menu(self, event: tk.Event) -> None:
        classes_options = tkb.Menu(master=self, 
                                   tearoff=0, 
                                   relief='raised')
        selection=self.val_table.selection()
        if len(selection) == 0: return
        elif len(selection) == 1:
            tag_id = self.val_table.item(selection[0], 'tags')[0]
            visible = self.val_table.item(selection[0], 'values')[-1] == 'V'
            
            classes_options.add_command(label=_('Edit class'), 
                                        command= lambda *x: \
                                            EditClass(self, tag_id))
            classes_options.add_command(label='\u25b2'+_(' Move up'), 
                                        command= lambda *x: \
                                            self.move_class(selection, 'prev', 'action'))
            classes_options.add_command(label="\u25bc"+_(' Move down'), 
                                        command= lambda *x: \
                                            self.move_class(selection, 'next', 'action'))
        if self.images[0].mode == 'manual':
            visible = sum([self.val_table.item(sel, 'values')[-1] == 'V' for sel in selection]) != 0
            hide_label = _('Hide class') if visible and len(selection) == 1 else _('Hide classes') if visible \
                    else _('Unhide class') if len(selection) == 1 else _('Unhide classes')
            classes_options.add_command(label=hide_label, 
                                        command= lambda *x: self.hide_classes(selection, visible))
        classes_options.add_command(label=_('Delete class') if len(selection) == 1 else _("Delete classes"), 
                                    command=lambda *x: self.remove_classes(False, selection))
        
        classes_options.tk_popup(event.x_root, event.y_root)
    
    def move_class(self, item: str, 
                   to: Literal['prev', 'next'] | int, 
                   mode: Optional[Literal['action', 'unaction']] = None) -> str | None:
        cur_index = self.val_table.index(item)
        num_classes = len(self.val_table.get_children())
        if isinstance(to, int): 
            if 0 > to > num_classes-1: return
            index = to
        elif to == 'next':
            index = 0 if cur_index+1>=num_classes else cur_index+1
        elif to == 'prev':
            index = num_classes-1 if cur_index <= 0 else cur_index-1
        
        self.val_table.move(item, "", index)
        self.color_table.move(item, "", index)
        
        self.check_pos()
        
        if mode is None: return
        
        tag_id: str = self.val_table.item(item, 'tags')[0]
        class_color: str = self.color_table.item(item, 'tags')[1]
        class_name: str = self.val_table.item(item, 'values')[2]
        reverse_action = tag_id, cur_index, class_name, class_color
        if mode == 'action':
            self.undo_stack.append(Action('class_edited', reverse_action))
        elif mode == 'unaction':
            return reverse_action      
    
    def hide_classes(self, selection: list[str], visible: bool) -> None:
        for item in selection:
            values = self.val_table.item(item, 'values')
            tag_id = self.val_table.item(item, 'tags')[0]
            self.images[0].classes[tag_id]['visible'] = not visible
            self.val_table.item(item, values = values[:-1] + tuple('I' if visible else 'V'))
            MAIN.change_annpolygon_color(tag_id)
        MAIN.redraw_fromimage_mainhandler()
    
    # ---------------------------------------------------------- #
    
    def reset_count(self) -> None:
        for item in self.val_table.get_children():
            values = self.val_table.item(item, 'values')
            self.val_table.item(item, values=(*values[:3], 0, values[4]))
    
    def binds(self, canvas: tkb.Canvas) -> None:
        canvas.bind('<MouseWheel>', self.set_marker)
        canvas.bind('<Button>', self.set_marker)
        self.window.bind('<KeyRelease-Delete>', lambda *x: self.remove_classes())
        
        for table in [self.color_table, self.val_table]:
            table.bind('<MouseWheel>', self.synchronized_tables)
            table.bind('<ButtonRelease>', lambda e, x=table: self.handle_event(e, x))
            table.bind('<Motion>', lambda e, x=table: self.handle_event(e, x))
            table.bind('<Double-Button-1>', lambda e, x=table: self.handle_event(e, x, True))
            
    def handle_event(self, 
                     event: tk.Event, 
                     table: tkb.Treeview, 
                     double: bool = False) -> None:
        if self.images[0] is None or self.mestre.poly_progress: return
        e = str(event).lower()
        if ('motion' in e or ('button' in e and 'num=1' in e)) \
            and table.identify_region(event.x, event.y) == 'separator':
            return "break"
        self.synchronized_tables(event)
        if 'num=3' in e: 
            self.classes_menu(event)
            return
        if double: self.set_marker(event)
    
    def synchronized_tables(self, event: tk.Event) -> None:
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
        if self.images[0] is None or self.mestre.poly_progress: return
        if len(self.images[0].classes) == 0: return
        e = str(event).lower()
        if 'mousewheel' in e:
            check_up = event.delta > 0
            check_down = event.delta < 0
        elif 'button' in e and 'num=4' in e or 'num=5' in e:
            check_up = event.num == 4
            check_down = event.num == 5
        else:
            check_up = None
        
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
            selected = self.val_table.selection()
            if len(selected) != 1: return
            marker_id = selected[0]
        self.select_mark(marker_id)
            
    # ---------------------------------------------------------- #
    
    def _update(self) -> None:
        if self.images[0] is not None:
            self.readd_classes()
        else:
            self.val_table.delete(*self.val_table.get_children())
            self.color_table.delete(*self.color_table.get_children())
        self.update_item_color()

class EditClass(tkb.Toplevel):
    """Pop up window for editing annotation classes.
    """
    def __init__(self, mestre: Sidebar, tag_id: str) -> None:
        """Pop up window for editing annotation classes.

        Args:
            mestre (Sidebar): Sidebar frame.
            tag_id (str): Tag_id of the annotation class to be edited.
        """
        self.mestre = mestre
        self.display = mestre.mestre
        self.main = self.display.main
        self.window = mestre.window
        
        x = self.window.winfo_rootx() + self.mestre.winfo_width()
        y = self.window.winfo_pointerxy()[1] - 20
        
        super().__init__(title=_("Edit class"), 
                         resizable=(False, False),
                         position=(x, y))
        
        self.images = mestre.images
        self.val_table = mestre.val_table
        self.color_table = mestre.color_table
        self.undo_stack = mestre.undo_stack
        
        self.tag_id = tag_id
        self.cur_class = self.images[0].classes[tag_id].copy()
        WINDOW.style.configure('EasyMark.ColorDisplay2.TFrame', background=self.cur_class['hex'])
        
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
        self.hex_var = tkb.StringVar(value=self.cur_class['hex'])
        self.name_var = tkb.StringVar(value=self.cur_class['name'])
        self.id_var = tkb.StringVar(value=self.cur_class['id'])

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
                                    self.edit_class()
                                )
        
        self.color_frame.grid(column=0, row=0, sticky='new', pady=[0, 3])
        self.name_entry.grid(column=1, columnspan=2, row=0, sticky='new', padx=2, pady=[0, 3])
        self.id_entry.grid(column=3, row=0, sticky='new', pady=[0, 3])
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
                var.set(self.cur_class[mode])
                return
            if val == str(self.cur_class[mode]):
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
        return name != self.cur_class['name'] and \
               name in [self.val_table.set(row, 'class') 
                       for row in self.val_table.get_children()]
    
    def check_id(self, id: str) -> bool:
        """Checks if the given id is within the number of classes.

        Args:
            id (str): Id tp be checked.

        Returns:
            valid (bool): Valid id.
        """
        if id == '': return True
        try:
            return 0 > int(id) > len(self.images[0].classes)
        except ValueError:
            return False

    def edit_class(self) -> None:
        """Executes the given edits.
        """
        hex_val, name_val, id_val = self.hex_var.get(), self.name_var.get(), self.id_var.get()
        
        if self.check_id(id_val): return
        else: id_val = int(id_val)
        if self.check_name(name_val): return
        
        if [hex_val, name_val, id_val] == list(self.cur_class.values()): return
        
        class_undo = self.tag_id, *[str(value) for value in self.cur_class.values()]
        self.images[0].classes[self.tag_id].update({'hex': hex_val, 'name': name_val, 'id': id_val})
        
        item = self.val_table.tag_has(self.tag_id)[0]

        if hex_val != self.cur_class['hex']: 
            self.color_table.tag_configure(self.tag_id, background=hex_val)
            item = self.color_table.tag_has(self.tag_id)
            self.color_table.item(item, tags=(self.tag_id, hex_val))
            if self.images[0].mode == 'semiauto': self.main.change_markpoint_color(self.tag_id, self.tag_id)
            elif self.images[0].mode == 'manual': self.main.change_annpolygon_color(self.tag_id)
        if name_val != self.cur_class['name']: 
            values = self.val_table.item(item, 'values')
            self.val_table.item(item, 
                                values=[
                                    values[0],
                                    values[1],
                                    name_val,
                                    values[3],
                                    values[4]
                                ])
        if id_val != self.cur_class['id']: 
            self.mestre.move_class(item, id_val)
        
        self.undo_stack.append(Action('class_edited', class_undo))
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
                                            self.edit_class())
    
    def _unfocus(self, *_) -> None:
        """Forces focus out of an entry widget.
        """
        x, y = self.winfo_pointerxy()
        widget = self.winfo_containing(x, y)
        if 'entry' not in str(widget): self.focus()


# ========================================================== #
# ========================================================== #

#* Completamente documentado
class MainVisualizer(tkb.Frame):
    """Class for handling the image display and it's peripherals, object annotation and it's functions.
    """
    
    def __init__(self, mestre: DisplayMaker) -> None:
        """
        Class for handling image display  and it's peripherals, object annotation and it's functions.
        
        Args:
            mestre (DisplayMaker): The Displayclass frame that holds the Main Visualizer.
        """
        super().__init__(master=mestre, borderwidth=5, relief='ridge')
        self.mestre = mestre
        self.window = mestre.mestre
        self.images = mestre.images
        self.val_table = mestre.side.val_table
        self.color_table = mestre.side.color_table
        
        self.cur_image: Optional[MarkedImage] = None
        self.popup_open = False
        self.radius = 6
        
        self.last_window_size = (1, 1)
        self.last_image_size = (1, 1)
        self.last_image_ratio = (1, 1)
        self.last_image_name = ''
        self.last_index = 0
        
        self.undo_stack = mestre.undo_stack
        self.redo_stack = mestre.redo_stack
        
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=10)
        self.columnconfigure(0, weight=1)
        
        self.grid(column=1, row=0, rowspan=2, 
                  sticky='nsew',
                  padx=5, pady=5)
        
        self.display_text()
        self.image_display()
        self.refresh()
        
        self.binds()
        
        
    # ---------------------------------------------------------- #
    #* Upper bar
    
    def display_text(self) -> None:
        """Handle displaying the name of the current image and it's index in relation to the total number of images at the top of the display.
        Allows quick jumps between images by changing the current index.
        """
        text_frame = tkb.Frame(master=self)
        for i in range(3):
            text_frame.columnconfigure(i, weight=1-(i%2))
        text_frame.rowconfigure(0, weight=1)
        text_frame.grid(column=0, row=0, sticky='nsew', pady=4)
        
        self.top_display: list[tkb.StringVar] = [
            tkb.StringVar(value=_("No images loaded") + ' - '),
            tkb.StringVar(value='0'),
            tkb.StringVar(value='/0')
        ]
        image_name = tkb.Label(master=text_frame, 
                               textvariable=self.top_display[0],
                               justify='right',
                               anchor='e')
        image_index = tkb.Entry(master=text_frame, 
                                textvariable=self.top_display[1],
                                width=10,
                                justify='right')
        total = tkb.Label(master=text_frame, 
                          textvariable=self.top_display[2], 
                          justify='left',
                          anchor='w')

        image_name.grid(row=0, column=0, sticky='nsew')
        image_index.grid(row=0, column=1, sticky='nsew')
        total.grid(row=0, column=2, sticky='nsew')
        
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
            
            self.save_markpoints_toimage()
            if new_index == self.last_index: return
            
            self.skip_image(new_index-1)
            self.last_index = new_index
        except ValueError: 
            self.top_display[1].set(self.last_index)
    
    def update_text(self) -> None:
        """Updates the displayed text and values.
        """
        if self.cur_image is None: 
            self.top_display[0].set(value=_("No images loaded") + ' - ')
            self.top_display[1].set(0)
            self.top_display[2].set(value='/0')
        else:
            self.top_display[0].set(value=f'{self.cur_image.name} - ')
            self.top_display[1].set(self.cur_image.index+1)
            self.top_display[2].set(value=f' / {len(self.images[0])}')
        
    # ---------------------------------------------------------- #
    #* Image handling
    
    def image_display(self) -> None:
        """Constructs the tkinter canvas in which all following functions work upon.
        """
        self.image_frame = tkb.Frame(master=self, relief='groove', borderwidth=5, style='EasyMark.ImageDisplay.TFrame')
        self.image_frame.columnconfigure(0, weight=1)
        self.image_frame.rowconfigure(0, weight=1)
        self.image_frame.grid(column=0, row=1, sticky='nsew')
        
        self.canvas = tkb.Canvas(master=self.image_frame, confine=True)
        self.canvas.pack(fill='both', expand='True')
        
        background_color = self.window.style.configure('EasyMark.ImageDisplay.TFrame')['background']
        text_color = self.window.style.configure('EasyMark.DataDisplay.TLabel')['foreground']
        self.canvas.create_rectangle(0, 0, self.image_frame.winfo_width(), self.image_frame.winfo_height(), fill=background_color, outline='', tags=['bg'])
        self.canvas.create_text((370, 212), text=_('No images loaded'), justify='center', anchor='center', fill=text_color, tags=['text'])
        
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
        self.update_text()
        self.keep_image_ratio(self.last_window_size)
        self.draw_image()
        
        if self.images[0].mode == 'semiauto': self.update_markpoints()
        elif self.images[0].mode == 'manual': self.update_annobjects()
    
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

    def keep_image_ratio(self, window_size: tuple[int]) -> None:
        """Resizes the image according to the window size.

        Args:
            window_size (tuple[int]): Current window size. In the order (height, width).
        """
        img = self.cur_image.image
        
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
        if self.images[0] is not None or self.cur_image is None: return
        items = [item
                  for tag in ['imagem', 'point', 'poly-point', 'ann-poly', 'poly-line']
                  for item in self.canvas.find_withtag(tag)]
        self.canvas.delete(*items)
    
    # ---------------------------------------------------------- #
    #* Marking point handling
    
    def draw_markpoint(self, x: int, y: int) -> None:
        """Draws a marking point in the given x y coordinates (cursor position).

        Args:
            x (int): The x position of the cursor.
            y (int): The y position of the cursor.
        """
        in_image = ['imagem' in tags 
                     for item in self.canvas.find_overlapping(x-1, y-1, x+1, y+1) 
                     for tags in self.canvas.gettags(item)]
        if sum(in_image) == 0: return
        
        if len(self.images[0].classes) == 0: return
        item_id = self.val_table.tag_has('marker')
        if len(item_id) == 0: return
        tag_id = self.val_table.item(item_id, 'tags')[0]
        color = self.images[0].classes[tag_id]['hex']
        
        coords = (x-self.radius, y-self.radius, x+self.radius, y+self.radius)
        rel_pos = ( self.last_image_ratio[0]*x, self.last_image_ratio[1]*y)
        
        point = self.canvas.create_oval(coords, fill=color)
        self.canvas.itemconfigure(point, {'tags':['point', f'{rel_pos[0]} {rel_pos[1]}', f'i{point}', tag_id ]})
        self.undo_stack.append(Action('markpoints_added', [f'i{point}']))
        
        self.count_objects()
    
    def redraw_markpoint(self, *tags: str) -> None:
        """Redraws marking points based on the given set of tags.

        Returns:
            *tags (str): Set of tags with the order:
            'point', x y positions (float), 'i'index (int), tag_id (str)
        """
        pos = tags[1].split()
        index = tags[2]
        tag_id = tags[3]
        
        x, y = int(float(pos[0])/self.last_image_ratio[0]), int(float(pos[1])/self.last_image_ratio[1])
        coords = (x-self.radius, y-self.radius, x+self.radius, y+self.radius)
        color = self.images[0].classes[tag_id]['hex']
        
        self.canvas.create_oval(coords, fill=color, tags=tags)
        self.count_objects()
        return index
    
    def select_markpoint(self, x: int = 0, y: int = 0, 
                         control: bool = False, shift: bool = False, 
                         deselect: bool = False) -> None:
        """Selects the marking point closest to the x y coordinates (cursor position) given.

        Args:
            x (int, optional): The x position of the cursor. Defaults to 0.
            y (int, optional): The y position of the cursor. Defaults to 0.
            control (bool, optional): If True, selects all points of the same class. Defaults to False.
            shift (bool, optional): If True, doesn't deselect previously selected points. Defaults to False.
            deselect (bool, optional): If True, no points are selected. Defaults to False.
        """
        selected = self.canvas.find_withtag('selected')
        
        if len(selected) != 0 and not shift:
            for point in selected:
                self.canvas.itemconfigure(point, {
                    'outline': 'black',
                    'width': 1,
                    'tags': [tag for tag in self.canvas.gettags(point) if tag != 'selected']
                })
        if deselect: return
        
        closest = self.canvas.find_closest(x, y, halo=10)
        enclosed = self.canvas.find_enclosed(x-20, y-20, x+20, y+20)
        
        if closest[0] not in enclosed: return
        if 'point' not in self.canvas.gettags(closest): return
        
        if control: 
            tag_id = self.canvas.gettags(closest)[3]
            for point in self.canvas.find_withtag(tag_id):
                self.canvas.itemconfigure(point, {
                'outline': 'red',
                'width': 2,
                'tags': list(self.canvas.gettags(point)) + ['selected']
                })
        else: 
            self.canvas.itemconfigure(closest, {
                'outline': 'red',
                'width': 2,
                'tags': list(self.canvas.gettags(closest)) + ['selected']
            })
    
    def remove_markpoints(self, tag: str, keybind: bool = False) -> list[tuple[str]]:
        """Removes all marking points with the determined tag.

        Args:
            tag (str): Targetted tag for deletion.
            keybind (bool, optional): If True, action will added to the undo stack. Defaults to False.

        Returns:
            list[tuple[str]]: List of tags of all deleted points.
        """
        if self.cur_image is None: return
        selected_tags = [self.canvas.gettags(item) 
                          for item in self.canvas.find_withtag(tag)]
        self.canvas.delete(tag)
        
        
        if keybind and len(selected_tags) > 0:
            self.undo_stack.append(Action('markpoints_deleted', selected_tags))
        return selected_tags
    
    def update_markpoints(self) -> None:
        """Updates point position.
        """
        points = self.canvas.find_withtag('point')
        for point in points:
            pos = self.canvas.gettags(point)[1].split()
            newpos = (
                int(float(pos[0])/self.last_image_ratio[0])-self.radius,
                int(float(pos[1])/self.last_image_ratio[1])-self.radius
            )
            self.canvas.moveto(point, newpos[0], newpos[1])

    def save_markpoints_toimage(self) -> None:
        """Saves the existing marking points to the loaded image.
        """
        if self.images[0] is None: return
        image_marks = self.cur_image.marks
        if len(image_marks) > 0: image_marks.clear()
        for point in self.canvas.find_withtag('point'):
            tags = self.canvas.gettags(point)
            pos = tags[1]
            tag_id = tags[3]
            if tag_id not in image_marks.keys(): image_marks[tag_id] = [pos]
            else: image_marks[tag_id].append(pos)
                    
    def redraw_markpoints_fromimage(self) -> None:
        """Redraws the marking points saved to the image when loaded.
        """
        
        if self.cur_image is None: return
        image_marks = self.cur_image.marks
        if len(image_marks) == 0: 
            self.remove_markpoints('point')
            return
        classcoord_pair = [(tag_id, coords.split()) 
                            for tag_id, coord_list in image_marks.items() 
                            for coords in coord_list]
        
        for tag_id, pos in classcoord_pair:
            if tag_id not in self.images[0].classes.keys(): continue 
            # If the image's tag_id is not withing the classes keys, means the class has been deleted, the marking point is skipped
            
            x, y = int(float(pos[0])/self.last_image_ratio[0]), \
                   int(float(pos[1])/self.last_image_ratio[1])
            fixed_coords = (x-self.radius, y-self.radius, x+self.radius, y+self.radius)
            color = self.images[0].classes[tag_id]['hex']
    
            point = self.canvas.create_oval(fixed_coords, fill=color)
            self.canvas.itemconfigure(point, {'tags': ['point', 
                                                       f'{pos[0]} {pos[1]}', 
                                                       f'i{point}', 
                                                       tag_id]})
        self.count_objects()
    
    def change_markpoint_color(self, 
                           tag_id: str, 
                           target_points: str | Literal['selected'] = 'selected'
                           ) -> list[tuple[str]]:
        """Recolours targetted marking points' with the selected class' color.
        
        Args:
            tag_id (str): The selected class the new color will be derived from.
            target_points (str | Literal[&#39;selected&#39;], optional): Target points to be recolored. Defaults to 'selected'.

        Returns:
            list[tuple[str]]: List with the original tags of the recoloured points.
        """
        points = self.remove_markpoints(target_points)
        for tags in points:
            self.redraw_markpoint(*tags[:3], tag_id)
        
        self.count_objects()
        if target_points == 'selected': self.undo_stack.append(Action('markpoints_edited', points))
        else: return points

    def click_handler_markpoint(self, event: tk.Event, double: bool = False) -> None:
        """Handler for clicking actions in semi-automatic annotation (marking) mode.

        Args:
            event (tk.Event): Tkinter click event.
            double (bool, optional): Determines if it was a double click. Defaults to False.
        """
        x, y = event.x, event.y
        shift, control = 'shift' in str(event).lower(), 'control' in str(event).lower()
        if event.num == 1:
            if self.popup_open: 
                self.popup_open = False
                return
            self.select_markpoint(deselect=True)
            if not double: return 
            self.draw_markpoint(x, y)
        else:
            self.select_markpoint(x, y, control, shift)
            self.markpoints_menu(event.x_root, event.y_root)
    
    def markpoints_menu(self, x: int, y: int) -> None:
        """Pop up menu to show up at the cursor after right selecting a marking point.

        Args:
            x (int): The x position of the cursor.
            y (int): The y position of the cursor. 
        """
        points_options = tkb.Menu(master=self, tearoff=0, relief='raised')
        
        selected = self.canvas.find_withtag('selected')
        if len(selected) == 0: return
        
        classes_menu = self.classes_menu(points_options)
        
        if len(selected) == 1:
            tags = self.canvas.gettags(selected)
            coords = tags[1].split()
            class_name = self.val_table.item(self.val_table.tag_has(tags[3]), 'values')[2]
            
            points_options.add_command(label=_('Position: ') + f'{float(coords[0]):.2f}, {float(coords[1]):.2f}')
            points_options.add_cascade(label=_('Class') + f': {class_name}', menu=classes_menu)
            points_options.add_command(label=_('Remove point'), command= lambda *x: self.remove_markpoints('selected', True))
        else:
            points_options.add_cascade(label=_("Edit class"), menu=classes_menu)
            points_options.add_command(label=_('Remove points'), command= lambda *x: self.remove_markpoints('selected', True))
        
        points_options.tk_popup(x, y)
        self.popup_open = True
    
    def classes_menu(self, points_options: tkb.Menu) -> tkb.Menu:
        """Sub-menu listing all available classes the marking point can be changed to.

        Args:
            points_options (tkb.Menu): The master pop up menu class.

        Returns:
            tkb.Menu: Sub-menu class.
        """
        classes_options = tkb.Menu(master=points_options)
        
        for item_id in self.val_table.get_children():
            class_name = self.val_table.item(item_id, 'values')[2]
            tag_id = self.val_table.item(item_id, 'tags')[0]
            classes_options.add_radiobutton(label=class_name, command= lambda x=tag_id, *y: self.change_markpoint_color(x))
        
        return classes_options    
    
    # ---------------------------------------------------------- #
    #* Annotation polygons handling
    
    def draw_polypoint(self, x: int, y: int, keybind: bool = True, point_id: Optional[str] = None) -> str:
        """Draws a polygon point in the given x y coordinates (cursor position). \\
        If another point exists, it will connect them with a line to aid in drawing the polygon. \\
        The polygon will be created after a new point is drawn on top of the first point created.

        Args:
            x (int): The x position of the cursor.
            y (int): The y position of the cursor.
            keybind (bool): If the method is being caled by a keybind. Defaults to True.
            point_id (str | None): Preset point id. Defaults to None.
        """
        
        in_image = ['imagem' in tags 
                     for item in self.canvas.find_overlapping(x-1, y-1, x+1, y+1) 
                     for tags in self.canvas.gettags(item)]
        if sum(in_image) == 0: return
        
        if len(self.images[0].classes) == 0: return
        item_id = self.val_table.tag_has('marker')
        if len(item_id) == 0: return
        if self.val_table.item(item_id, 'values')[4] == 'I': return
        tag_id = self.val_table.item(item_id, 'tags')[0]
        color = self.images[0].classes[tag_id]['hex']
        
        coords = (x-self.radius, y-self.radius, x+self.radius, y+self.radius)
        rel_pos = (self.last_image_ratio[0]*x, self.last_image_ratio[1]*y)
        
        point = self.canvas.create_oval(coords, fill=color)
        self.canvas.itemconfigure(point, {'tags': ['poly-point', f'{rel_pos[0]} {rel_pos[1]}', tag_id, f"{f"p{point}" if point_id is None else point_id}"]})
        if point_id is not None: point = point_id[1:]
        
        self.canvas.delete('mouse-line')
        self.canvas.create_line(x, y, x, y, fill=color, width=2, tags=['mouse-line', f"d{point}", f'{rel_pos[0]} {rel_pos[1]}'])
        
        if self.mestre.poly_progress is False:
            self.mestre.poly_progress = True # disabling class modifications so classes can't be edited/changed while constructing the polygon
            self.cur_image.new_annpoly(AnnPoly(first_point=f"p{point}", classe=tag_id))
            if keybind: self.undo_stack.append(Action('polypoints_added', f"p{point}"))
            return f"p{point}"
        
        cur_annpolygon = self.cur_image.wip_poly
        cur_annpolygon.new_point(point=f"p{point}")
        
        point1, point2 = cur_annpolygon.points[-2], cur_annpolygon.points[-1]
        raw_line_coords = [float(coord) for coord in self.canvas.gettags(point1)[1].split() + self.canvas.gettags(point2)[1].split()]
        line_coords = ( int(raw_line_coords[0]/self.last_image_ratio[0]), int(raw_line_coords[1]/self.last_image_ratio[1]), 
                        int(raw_line_coords[2]/self.last_image_ratio[0]), int(raw_line_coords[3]/self.last_image_ratio[1]))
        
        self.canvas.create_line(*line_coords, fill=color, width=3, tags=['poly-line', f"d{point1[1:]}", f"d{point2[1:]}", ' '.join([str(coord) for coord in raw_line_coords]), tag_id])
        self.canvas.tag_lower('poly-line', 'poly-point')
        
        if keybind: self.undo_stack.append(Action('polypoints_added', f"p{point}"))
        
        enclosed = [self.canvas.gettags(point)[3] for point in self.canvas.find_enclosed(x-20, y-20, x+20, y+20) if 'poly-point' in self.canvas.gettags(point)]
        if cur_annpolygon.points[0] in enclosed and len(cur_annpolygon.points) > 2 and keybind: # checking for a closed polygon with three of more points to confirm
            self.confirm_annpolygon(cur_annpolygon, closed_polygon=True)
            
        return f'p{point}'
    
    def remove_polypoints(self, target_tag: str = 'poly-point', keybind: bool = True) -> dict[str, list[float]]:
        """Removes all polygon points with the determined tag.\\
        Connected lines will be deleted alongside it's point and resulting gaps will be filled with a new line to connect remaining points.

        Args:
            target_tag (str): Targetted tag for deletion. Defaults to "poly-point".
            keybind (bool): If the method is being caled by a keybind. Defaults to True.
        
        Returns:
            point_data (dict[str, list[float]]): Dictionary containing the id and postion of each deleted polygon point.
        
        """
        if target_tag == 'poly-point': target_line = ['poly-line']
        else: target_line = self.canvas.find_withtag(f"d{target_tag[1:]}")
        
        point_data = {self.canvas.gettags(point)[3] : [float(coord) for coord in self.canvas.gettags(point)[1].split()] 
                     for point in sorted(self.canvas.find_withtag(target_tag))}
        
        self.canvas.delete(target_tag, *target_line, 'mouse-line')
        
        if target_tag == 'poly-point' or len(self.cur_image.wip_poly.points)-1 == 0:
            self.mestre.poly_progress = False
            self.cur_image.clear_wip()
        else:
            self.cur_image.wip_poly.remove_last()
            last_point_tags = self.canvas.gettags(self.cur_image.wip_poly.points[-1])
            
            raw_coords = [float(coord) for coord in last_point_tags[1].split()]
            coords = [raw_coords[0]/self.last_image_ratio[0], raw_coords[1]/self.last_image_ratio[1]]
            tag_id = last_point_tags[2]
            color = self.images[0].classes[tag_id]['hex']
            
            self.canvas.create_line(*coords, *coords, fill=color, tags=['mouse-line', f"d{last_point_tags[3][1:]}", f'{raw_coords[0]} {raw_coords[1]}'])
            
        if keybind: self.undo_stack.append(Action('polypoints_deleted', point_data))
        return point_data

    def update_polypoints(self) -> None:
        """Updates polygon point position and their lines.
        """
        if not self.mestre.poly_progress: return
        
        for line in self.canvas.find_withtag('poly-line'):
            line_tags = self.canvas.gettags(line)
            x1, y1, x2, y2 = line_tags[3].split()
            line_coords = ( int(float(x1)/self.last_image_ratio[0]), int(float(y1)/self.last_image_ratio[1]), 
                            int(float(x2)/self.last_image_ratio[0]), int(float(y2)/self.last_image_ratio[1]))
            self.canvas.coords(line, *line_coords)

        for point in self.canvas.find_withtag('poly-point'):
            pos = self.canvas.gettags(point)[1].split()
            newpos = (
                int(float(pos[0])/self.last_image_ratio[0])-self.radius,
                int(float(pos[1])/self.last_image_ratio[1])-self.radius
            )
            self.canvas.moveto(point, newpos[0], newpos[1])
        
        mouse_lines = self.canvas.find_withtag('mouse-line')
        mouse_line = mouse_lines[0]
        raw_coords = [float(coord) for coord in self.canvas.gettags(mouse_line)[2].split()]
        coords = [raw_coords[0]/self.last_image_ratio[0], raw_coords[1]/self.last_image_ratio[1]]
        self.canvas.coords(mouse_line, coords+coords)
        
    def update_mouseline(self, event: tk.Event) -> None:
        if not self.mestre.poly_progress: return
        
        mouse_lines = self.canvas.find_withtag('mouse-line')
        if len(mouse_lines) == 0: return
        x, y = event.x, event.y
        
        mouse_line = mouse_lines[0]
        raw_coords = [float(coord) for coord in self.canvas.gettags(mouse_line)[2].split()]
        coords = [raw_coords[0]/self.last_image_ratio[0], raw_coords[1]/self.last_image_ratio[1], x, y]
        self.canvas.coords(mouse_line, coords)
    
    def confirm_annpolygon(self, 
                           cur_annpolygon: AnnPoly,
                           title: str = _("Confirm polygon"),
                           metadata: str = _('field1:data, field2:data'),
                           closed_polygon: bool = False
                           ) -> None:
        """Makes a pop up window to confirm drawing a new annotation polygon from a set of drawn polygon points.

        Args:
            cur_annpolygon (AnnPoly): AnnPoly class holding the polygon's data.
            title (str, optional): Title of the pop up screen. Defaults to _("Confirm polygon").
            metadata (_type_, optional): Preset metadata values to be given to the polygon. Defaults to _('field1:data, field2:data').
            closed_polygon (bool, optional): Determines if the polygon was closed manually or by other means. Defaults to False.
        """
        x, y = window.winfo_pointerxy()
        confirmation_window = tkb.Toplevel(title=title, position=(x-20, y-20), minsize=[350, 100])
        confirmation_window.columnconfigure(0, weight=1)
        confirmation_window.rowconfigure(0, weight=1)
        
        base_toplevel_binds(confirmation_window)
        
        base_frame = tkb.Frame(master=confirmation_window, relief='raised', padding=5)
        for i in range(5): base_frame.columnconfigure(i, weight=1)
        for i in range(3): base_frame.rowconfigure(i, weight=1)
        base_frame.pack(expand=True, fill='both')
        
        metadata_var = tkb.StringVar(value=metadata)
        metadata_text = tkb.Label(master=base_frame, text="Metadata")
        metadata_entry = tkb.Entry(master=base_frame, textvariable=metadata_var, foreground='#bbbbbb', justify='left', width=30)
        confirm_button = tkb.Button(master=base_frame, text=_("Confirm"), 
                                    command = lambda *x: self.finish_annpolygon(confirmation_window, metadata_var, closed_polygon, cur_annpolygon) )
        metadata_text.grid(row=0, column=0, columnspan=2, sticky='ew')
        metadata_entry.grid(row=0, column=2, columnspan=3, sticky='ew')
        confirm_button.grid(row=2, column=4, sticky='se')
        
        confirmation_window.bind('<Return>', func= lambda *x:  self.finish_annpolygon(confirmation_window, metadata_var, closed_polygon, cur_annpolygon))
        
        if title != _('Confirm polygon'):
            tag_id = cur_annpolygon.classe
            tag_id_var = tkb.StringVar(value=tag_id)
            class_text = tkb.Label(master=base_frame, text=_('Class'))
            class_button = tkb.Menubutton(master=base_frame, width=15, text=_('Class'))
            class_menu = tkb.Menu(master=class_button)
            for item_id in self.val_table.get_children():
                class_name = self.val_table.item(item_id, 'values')[2]
                class_tag_id = self.val_table.item(item_id, 'tags')[0]
                class_menu.add_command(label=class_name, 
                                       command= lambda *x, classname=class_name, classtagid=class_tag_id:
                                           self.class_button_command(class_button, tag_id_var, classname, classtagid)
                                      )
                if class_tag_id == tag_id: class_button.configure(text=class_name)
            class_button.configure(menu=class_menu)
                
            confirm_button.config(command= lambda *x: self.finish_annpolygon(confirmation_window, metadata_var, closed_polygon, cur_annpolygon,tag_id_var))
            
            class_text.grid(row=0, column=0, columnspan=2, sticky= 'ew')
            class_button.grid(row=0, column=2, columnspan=3, sticky= 'ew')
            metadata_text.grid(row=1, column=0, columnspan=2, sticky= 'ew')
            metadata_entry.grid(row=1, column=2, columnspan=3, sticky= 'ew')
            
            confirmation_window.unbind('<Return>')
            confirmation_window.bind('<Return>', func= lambda *x: self.finish_annpolygon(confirmation_window, metadata_var, closed_polygon, cur_annpolygon,tag_id_var))
        
    def class_button_command(self,
                             class_button: tkb.Menubutton, 
                             tag_id_var: tkb.StringVar, 
                             class_name: str, 
                             class_tag_id: str
                             ) -> None:
        """Changes the set class for the new polygon and the displayed text on the menubutton.

        Args:
            class_button (tkb.Menubutton): Class selection menu button.
            tag_id_var (tkb.StringVar): Variable holding the current class' tag_id.
            class_name (str): The selected class' name.
            class_tag_id (str): The selected class' tag_id.
        """
        
        class_button.configure(text=class_name)
        tag_id_var.set(value=class_tag_id)
    
    def finish_annpolygon(self,
                          confirmation_window: tkb.Toplevel, 
                          metadata_var: tkb.StringVar, 
                          closed_polygon: bool,
                          cur_annpolygon: AnnPoly,
                          tag_id_var: Optional[tkb.StringVar] = None
                          ) -> None:
        """Finishes the process of drawing a new annotation polygon.

        Args:
            confirmation_window (tkb.Toplevel): Confirmation pop up window to be closed if successful.
            metadata_var (tkb.StringVar): Variable holding the given metadata for the new polygon.
            closed_polygon (bool):  Determines if the polygon was closed manually or by other means.
            cur_annpolygon (AnnPoly): Annotation Polygon class holding the polygon's data.
            tag_id_var (tkb.StringVar | None, optional): Class tag_id. Defaults to None.
        """
        
        metadata_text = metadata_var.get()
        try:
            if metadata_text != '':
                if metadata_text.count(',')+1 != metadata_text.count(':'): raise IndexError
                metadata =  {" ".join(pair.split(':')[0].split()) : " ".join(pair.split(':')[1].split())
                                for pair in metadata_text.split(',')}
                if "" in metadata.keys(): raise IndexError
            else: metadata = ""
        
        except IndexError: 
            messagebox.showerror(title="Invalid metadata", 
                                 message='Metadata given is not properly written.\n'+\
                                         'Make sure it follows the proper syntax:\n'+\
                                         '> field1:data, field2:data, ...')
            return
        
        cur_annpolygon.metadata = metadata
        if tag_id_var is None:
            self.draw_annpolygon(cur_annpolygon, closed_polygon)
            self.mestre.poly_progress = False # enabling class modifications after the polygon is constructed
        else:
            cur_annpolygon.classe = tag_id_var.get()
            old_tags = MAIN.canvas.gettags(MAIN.canvas.find_withtag(cur_annpolygon.polygon_id))
            self.canvas.delete(cur_annpolygon.polygon_id)
            tags = ('ann-poly', cur_annpolygon.polygon_id, ' '.join(str(coord) for coord in cur_annpolygon.point_coords), cur_annpolygon.classe)
            self.redraw_annpolygon(*tags)
            self.undo_stack.append(Action('annpolys_edited', old_tags, metadata.get()))
        
        close_window(confirmation_window)

    def draw_annpolygon(self, annpolygon: AnnPoly,  closed_polygon: bool) -> None:
        """Draws an annotation polygon.

        Args:
            annpolygon (AnnPoly): AnnPoly class holding the polygon's data.
            closed_polygon (bool): Determines if the polygon was closed manually or by other means.
        """
        
        if closed_polygon: annpolygon.remove_last()
        
        item_id = self.val_table.tag_has('marker')
        tag_id = self.val_table.item(item_id, 'tags')[0]
        color = self.images[0].classes[tag_id]['hex']
        
        polygon_id = "".join(randchoices(LETTERS2, k=10))
        while self.cur_image.find_annpoly(lambda poly: poly.polygon_id == polygon_id) is not None:
            polygon_id = "".join(randchoices(LETTERS2, k=10))
        
        raw_point_coords = [float(coord) 
                            for point_id in annpolygon.points 
                            if len(self.canvas.gettags(point_id)) > 0 
                            for coord in self.canvas.gettags(point_id)[1].split()]
        fixed_coords = [int(raw_point_coords[i]/self.last_image_ratio[i%2]) for i in range(len(raw_point_coords))]
        
        polygon = self.canvas.create_polygon(*fixed_coords, width=2, outline=color, fill='')
        if self.images[0].sec_mode == 'bbox':
            annpolygon.metadata.update({'polygon_coords': ' '.join([str(coord) for coord in raw_point_coords])})
            bbox_coords = self.canvas.bbox(polygon)
            raw_point_coords = [ bbox_coords[i]*self.last_image_ratio[i%2] for i in range(4)]
            self.canvas.delete(polygon)
            polygon = self.canvas.create_rectangle(*bbox_coords, outline=color, fill='')
            
        self.canvas.itemconfigure(polygon, {'tags': ['ann-poly', polygon_id, ' '.join([str(coord) for coord in raw_point_coords]), tag_id], 'width': 2})
        annpolygon.point_coords = raw_point_coords
        annpolygon.polygon_id = polygon_id
        
        
        self.cur_image.store_annpoly()
        removed_polypoint_pos = self.remove_polypoints('poly-point', False)
        
        self.count_objects()
        self.undo_stack.append(Action('annpolys_added', [polygon_id], Action('polypoints_deleted', removed_polypoint_pos)))
    
    def redraw_annpolygon(self, *tags: str) -> str:
        """Redraws annotation polygons based on the given set of tags.

        Returns:
            *tags (str): Set of tags with the order:
            'ann-poly', polygon_id (str), x1 y1 x2 y2 ... coords (float), tag_id (str)
        """
        polygon_id = tags[1]
        raw_coords = tags[2].split()
        tag_id = tags[3]
        visible = self.images[0].classes[tag_id]['visible']
        
        color = self.images[0].classes[tag_id]['hex'] if visible else ''
        coords = [int(float(raw_coords[i])/self.last_image_ratio[i%2]) for i in range(len(raw_coords))]
        
        
        if len(coords) == 4: # Turns bounding box coordinates (two points) into polygon coordinates (4 points) 
            coords = [
                coords[0], coords[1],
                coords[0], coords[3],
                coords[2], coords[3],
                coords[2], coords[1],
            ]
        self.canvas.create_polygon(*coords, outline=color, fill='', width=2, tags=tags)
        
        return polygon_id
    
    def select_annpolygon(self, x: int = 0, y: int = 0, 
                          control: bool = False, shift: bool = False, 
                          deselect: bool = False) -> None:
        """Selects the annotation polygon closest to the x y coordinates (cursor position) given.

        Args:
            x (int, optional): The x position of the cursor. Defaults to 0.
            y (int, optional): The y position of the cursor. Defaults to 0.
            control (bool, optional): If True, selects all polygons of the same class. Defaults to False.
            shift (bool, optional): If True, doesn't deselect previously selected polygons. Defaults to False.
            deselect (bool, optional): If True, no polygons are selected. Defaults to False.
        """
        selected = self.canvas.find_withtag('selected')
        
        if len(selected) != 0 and not shift:
            for annpolygon in selected:
                tags = self.canvas.gettags(annpolygon)
                color = self.images[0].classes[tags[3]]['hex']
                self.canvas.itemconfigure(annpolygon, {
                    'outline': color,
                    'width': 2,
                    'tags': [tag for tag in tags if tag != 'selected']
                })
        if deselect: return
        
        closest = self.canvas.find_closest(x, y, halo=10)
        overlapping = self.canvas.find_overlapping(x-20, y-20, x+20, y+20)
        
        if closest[0] not in overlapping: return
        if 'ann-poly' not in self.canvas.gettags(closest): return
        
        if control: 
            tag_id = self.canvas.gettags(closest)[3]
            color = self.images[0].classes[tag_id]['hex']
            for annpolygon in self.canvas.find_withtag(tag_id):
                self.canvas.itemconfigure(annpolygon, {
                    'outline': color,
                    'width': 4,
                    'tags': list(self.canvas.gettags(annpolygon)) + ['selected']
                })
        else: 
            tag_id = self.canvas.gettags(closest)[3]
            color = self.images[0].classes[tag_id]['hex']
            self.canvas.itemconfigure(closest, {
                'outline': color,
                'width': 4,
                'tags': list(self.canvas.gettags(closest)) + ['selected']
            })
    
    def remove_annpolygons(self, tag: str, keybind: bool = False) -> list[AnnPoly]:
        """Removes all annotation polygons with the determined tag.

        Args:
            tag (str): Targetted tag for deletion.
            keybind (bool, optional): If True, action will added to the undo stack. Defaults to False.

        Returns:
            list[AnnPoly]: List with the AnnPoly of each deleted polygon.
        """
        target_polygons: list[AnnPoly] = []
        for target in self.canvas.find_withtag(tag):
            polygon_id = self.canvas.gettags(target)[1]
            polygon_index = self.cur_image.find_annpoly(lambda poly: poly.polygon_id == polygon_id)
            target_polygons.append(self.cur_image.ann_polys.pop(polygon_index))
            self.canvas.delete(polygon_id)
        
        if keybind and len(target_polygons) > 0:
            self.undo_stack.append(Action('annpolys_deleted', target_polygons))
        return target_polygons
    
    def update_annobjects(self) -> None:
        """Updates position of all annotation-related canvas objects.
        """
        self.update_polypoints()
        self.canvas.delete('ann-poly')
        self.redraw_annpolygons_fromimage()
    
    def redraw_annpolygons_fromimage(self) -> None:
        """Redraws tha annotation polygons saved to the image when loaded.
        """
        if self.images[0] is None or self.cur_image is None: return
        
        for annpolygon in self.cur_image.ann_polys:
            self.redraw_annpolygon('ann-poly', 
                                   annpolygon.polygon_id, 
                                   ' '.join([str(coord) for coord in annpolygon.point_coords]), 
                                   annpolygon.classe)
    
    def change_annpolygon_color(self, target_annpolys: str) -> None:
        """Updates targetted annotation polygons' color. This is only called when the class' color is changed.

        Args:
            target_annpolys (str): target anntation polygon tag.
        """
        polygons = self.canvas.find_withtag(target_annpolys)
        polygon_tags = [self.canvas.gettags(poly) for poly in polygons]
        self.canvas.delete(polygons)
        for tags in polygon_tags: self.redraw_annpolygon(*tags)
    
    def click_handler_polypoint(self, event: tk.Event, double: bool = False) -> None:
        """Handler for clicking actions in manual annotation mode.

        Args:
            event (tk.Event): Tkinter click event.
            double (bool, optional): Determines if it was a double click. Defaults to False.
        """
        x, y = event.x, event.y
        shift, control = 'shift' in str(event).lower(), 'control' in str(event).lower()
        if event.num == 1:
            if self.popup_open: 
                self.popup_open = False
                return
            if not self.mestre.poly_progress: 
                self.select_annpolygon(deselect=True)
            if not double: return 
            self.draw_polypoint(x, y)
        else:
            if not self.mestre.poly_progress:
                self.select_annpolygon(x, y, control, shift)
                self.annpolygon_menu(event.x_root, event.y_root)
    
    def annpolygon_menu(self, x: int, y: int) -> None:
        """Pop up menu to show up at the cursor after selecting an annotation polygon.

        Args:
            x (int): The x position of the cursor.
            y (int): The y position of the cursor. 
        """
        selected = self.canvas.find_withtag('selected')
        if len(selected) == 0 or self.mestre.poly_progress: return
        
        annpolygon_options = tkb.Menu(master=self, 
                                  tearoff=0, 
                                  relief='raised')
        
        if len(selected) == 1:
            tags = self.canvas.gettags(selected)
            class_name = self.val_table.item(self.val_table.tag_has(tags[3]), 'values')[2]
            polygon_index = self.cur_image.find_annpoly(lambda poly: poly.polygon_id == tags[1])
            polygon: AnnPoly = self.cur_image.ann_polys[polygon_index]
            metadata = polygon.metadata
            
            metadata_menu = self.metadata_menu(annpolygon_options, metadata)
            
            annpolygon_options.add_command(label=f'{_('Class')}: {class_name}')
            annpolygon_options.add_cascade(label=_('Metadata'), menu=metadata_menu)
            annpolygon_options.add_command(label=_('Edit polygon'), command= lambda *x: self.confirm_annpolygon(polygon, _('Edit polygon'), ', '.join([f'{field}: {data}' for field, data in metadata.items()])))
            annpolygon_options.add_command(label=_('Remove polygon'), command= lambda *x: self.remove_annpolygons('selected', True))
        else:
            annpolygon_options.add_command(label=_('Remove polygons'), 
                                       command= lambda *x: \
                                           self.remove_annpolygons('selected', True))
        annpolygon_options.tk_popup(x, y)
        self.popup_open = True
    
    def metadata_menu(self, annpolygon_menu: tkb.Menu, metadata: dict[str ,str]) -> tkb.Menu:
        """Sub-menu listing the polygon's metadata.

        Args:
            annpolygon_menu (tkb.Menu): The master pop up menu class.
            metadata (dict[str, str]): Polygon's metadata.

        Returns:
            tkb.Menu: Sub-menu class.
        """
        metadata_options = tkb.Menu(master=annpolygon_menu)
        
        if metadata == '': return metadata_options
        
        for field, data in metadata.items(): metadata_options.add_command(label=f'{field}: {data}')
        return metadata_options
    
    # ---------------------------------------------------------- #
    #* General object handling

    def select_all(self) -> None:
        """Selects all marking/annotations in the image.
        """
        if self.cur_image is None: return
        target = 'point' if self.images[0].mode == 'semiauto' else 'poly-point' 
        for point in self.canvas.find_withtag(target):
            self.canvas.itemconfigure(point, {
            'outline': 'red',
            'width': 2,
            'tags': [tag for tag in self.canvas.gettags(point)] + ['selected']
            })
    
    def remove_objects_handler(self) -> None:
        """Main handler for removing markings/annotations off images. 
        """
        if self.images[0].mode == 'semiauto': 
            self.remove_markpoints('selected', True)
        elif self.images[0].mode == 'manual':
            if self.mestre.poly_progress: self.remove_polypoints('selected')
            else: self.remove_annpolygons('selected', True)
    
    def redraw_fromimage_mainhandler(self) -> None:
        """Main handler for loading markings/annotations from images according to the project type.
        """
        if self.images[0] is None: return
        elif self.images[0].mode == 'semiauto':
            self.remove_markpoints('point')
            self.redraw_markpoints_fromimage()
        elif self.images[0].mode == 'manual':
            self.remove_polypoints('poly-point')
            self.canvas.delete('ann-poly')
            self.redraw_annpolygons_fromimage()
    
    def canvas_click_mainhandler(self, event: tk.Event, double: bool = False) -> None:
        """Main handler for click actions on the image.

        Args:
            event (tk.Event): Tkinter click event.
            double (bool, optional): Determines if it was double click. Defaults to False.
        """
        if self.cur_image is None: return
        if self.images[0].mode == 'semiauto': self.click_handler_markpoint(event, double)
        elif self.images[0].mode == 'manual': self.click_handler_polypoint(event, double)

    # ---------------------------------------------------------- #
    #* Background and non-specific functions
    
    def binds(self) -> None:
        """Function with all the main binds.
        """
        self.window.bind("<KeyRelease-Right>", lambda *x: self.skip_image('next'))
        self.window.bind("<KeyRelease-d>", lambda *x: self.skip_image('next'))
        self.window.bind("<KeyRelease-Left>", lambda *x: self.skip_image('prev'))
        self.window.bind("<KeyRelease-a>", lambda *x: self.skip_image('prev'))
        
        self.canvas.bind("<Button-1>", lambda e: self.canvas_click_mainhandler(e))
        self.canvas.bind("<Double-Button-1>", lambda e: self.canvas_click_mainhandler(e, True))
        self.canvas.bind("<ButtonRelease-3>", lambda e: self.canvas_click_mainhandler(e))
        self.canvas.bind("<Motion>", lambda e: self.update_mouseline(e))
        
        self.window.bind("<Control-KeyRelease-a>", lambda *x: self.select_all())
        self.window.bind("<KeyPress-Delete>", lambda *x: self.remove_objects_handler())
    
    def skip_image(self, movement: int | Literal['next', 'prev'], keybind: bool = True) -> None:
        """Handles all functions related to before and after jumping to an image.

        Args:
            movement (int | Literal['next', 'prev']): Image index or jump direction.
            keybind (bool, optional): If True, action will added to the undo stack. Defaults to True.
        """
        active_widget = str(self.window.focus_get())
        if self.images[0] is None or 'class_name_entry' in active_widget or (isinstance(movement, str) and 'entry' in active_widget):
            return
        elif keybind:
            self.undo_stack.append(Action('moved_page', self.cur_image.index))
        
        if self.images[0].mode == 'semiauto':
            self.save_markpoints_toimage()
            self.remove_markpoints('point')
            self.images[0].jump_to(movement)
            self.refresh(True)
            self.mestre.side.reset_count()
            self.redraw_markpoints_fromimage()
        elif self.images[0].mode == 'manual':
            if self.mestre.poly_progress:
                poly_point_data = self.remove_polypoints('poly-point', False)
                self.undo_stack[-1].secondary_data = Action('polypoints_deleted', poly_point_data)
            self.canvas.delete('ann-poly')
            self.images[0].jump_to(movement)
            self.refresh(True)
        
        self.mestre.poly_progress = False
        self.count_objects()
    
    def count_objects(self) -> None:
        """Counts how many objects of each class are in the image to be displayed in the side bar.
        """
        mode = self.images[0].mode
        target = 'point' if mode == 'semiauto' else 'ann-poly'
        tags = [self.canvas.gettags(obj)[3] 
                  for obj in self.canvas.find_withtag(target)]
        tag_qnt = dict(Counter(tags))
        
        for item in self.val_table.get_children():
            tag_id = self.val_table.item(item, 'tags')[0]
            values = self.val_table.item(item, 'values')
            quant = tag_qnt.setdefault(tag_id, 0)
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
        self.update_image(same_size)
        self.mestre.clean_stacks()
        if not single: self.after(ms=200, func= lambda *x: self.refresh())
    
    def _update(self) -> None:
        """Backend function part of a general cascade update.
        """
        self.clean_canvas()
        if self.images[0] is None: self.cur_image = None
        self.update_image()
        self.update_text()
        self.redraw_fromimage_mainhandler()
        self.update_background()
    
    def _closing_funcs(self) -> None:
        """Backend function to be run when closing the program.
        """
        if self.images[0] is None: return
        self.save_markpoints_toimage()


# ========================================================== #
# ========================================================== #


class DetectiontoProjectWindow(tkb.Toplevel):
    def __init__(self, window: tkb.Window) -> None:
        x = window.winfo_pointerxy()[0] - 20
        y = window.winfo_pointerxy()[1] - 20
        
        super().__init__(title=_("Automatic Annotation"), position=(x, y), resizable=[False, False])

        
        self.main_frame = tkb.Frame(master=self, padding=5, relief='raised', borderwidth=5)
        self.main_frame.pack(fill='both', expand=True)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
        self.ann_type      = tkb.StringVar(value='bbox')
        self.det_model_dir = tkb.StringVar(value= os.path.join(FOLDER_PATHS['MODELS'], 'FastSAM-x.pt'))
        self.model_type = tkb.StringVar(value='yolov8')
        self.model_task = tkb.StringVar(value='segment')
        self.binarize      = tkb.BooleanVar(value=False)
        self.seg_from_proj = tkb.BooleanVar(value=False)
        self.image_dir       = tkb.StringVar(value='')
        self.output_dir   = tkb.StringVar(value='')
        self.project_dir   = tkb.StringVar(value='')

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
            self.det_model_dir.set(os.path.join(FOLDER_PATHS['MODELS'], 'FastSAM-x.pt'))
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
        
        self.arq_icon = get_icon()
        
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
                        master=self
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
                        master=self
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
                                            'date_last', 'classes', 'all_marks']
    
    def confirm(self) -> None:
        paths = [self.image_dir.get(), self.output_dir.get(), self.project_dir.get()]
        check = 0
        for i in range(3): 
            check += self.check_dir(paths[i], ['img', 'res', 'proj'][i])
        if not self.seg_from_proj.get(): check += 1; paths[i] = None
        if check < 3: return
        
        DetectToProject(master=self, image_dir=paths[0], output_dir=paths[1], ann_type=self.ann_type.get(), 
                        model_dir=self.det_model_dir.get(), model_type=self.model_type.get(), model_task=self.model_task.get(),
                        binarize=self.binarize.get(), proj_dir=paths[2])
            

# ========================================================== #
# ========================================================== #


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
        partition_list: tuple[Any] = [
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
        
        self.lock_closed = tkb.PhotoImage(file=os.path.join(FOLDER_PATHS['IMAGE'], 'lock_closed.png'))
        self.lock_open = tkb.PhotoImage(file=os.path.join(FOLDER_PATHS['IMAGE'], 'lock_open.png'))
        
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
        self.percents[index].config(from_=0, to=100, 
                                    width=3, 
                                    textvariable=var_display, 
                                    validate='focus',
                                    validatecommand=lambda *x, y=index: \
                                        self.validate_percent(y),
                                    invalidcommand=lambda *x, y=index: \
                                        self.percents[y].set(self.partition_vals[index].get()),
                                    command=lambda *x, y=index: \
                                        self.update_partition_vals(y, var_display)
                                    )
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
        
        self.arq_icon = get_icon()
        
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
            messagebox.showerror(title=_("Invalid file"), message=_("The selected file does not exist."), master=self)
            return False
        
        with open(path, 'r') as file: 
            data: dict = json.load(file)
        if not list(data.keys()) == ['directory', 'mode', 'sec_mode', 'date_create', 'date_last', 'classes', 'all_ann']:
            messagebox.showerror( title=_("Invalid file"), message=_("The selected file is not a proper annotation project file."), master=self)
            return False

        self.datafile_path.set(value=path)
        
        image_dir = data['directory']
        if not self.get_imagedir(image_dir, True):
            messagebox.showerror(title=_("Invalid image directory"), message=_("Image directory in project file does not exist."), master=self)
        elif self.imagedir_path.get().isspace(): self.imagedir_path.set(value=image_dir)
        return True
                
    def get_imagedir(self, preset_path: Optional[str] = None, proj_preset: bool = False) -> bool: 
        if preset_path: path = preset_path
        else:
            path = filedialog.askdirectory(title=_("Select image directory"), mustexist=True, parent=self)
            if path in [None, '', ()]: return False
        
        if not os.path.isdir(path):
            if not proj_preset:
                messagebox.showerror(title=_("Invalid image directory"), message=_("Image directory does not exist."), master=self)
            return False

        format_check = sum([os.path.splitext(file)[1] in ['.jpg', '.jpeg', '.png']
                             for file in os.listdir(path)])
        if format_check == 0:
            messagebox.showerror(
                    title=_("Invalid directory"),
                    message=_("The selected directory does not have any of the following formats")+':\n' +\
                            f"{', '.join(['.jpg', '.jpeg', '.png'])}",
                    master=self
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
            messagebox.showerror(title=_("Invalid directory"), message=_("Results directory does not exist."), master=self)
            return False
        self.resdir_path.set(value=path)
        return True
    
    def finish_func(self) -> None:
        datafile_path = self.datafile_path.get()
        if not self.get_datafile(datafile_path): return
        imagedir_path = self.imagedir_path.get()
        if not self.get_imagedir(imagedir_path): return
        resdir_path = self.resdir_path.get()
        if not self.get_resdir(resdir_path): return
        
        paths = [path_var.get() for path_var in self.paths.values()]
        partitions = [part.get() for part in self.partition_vals][:3]
        if '' in paths or self.format_option.get() == _("Empty"): return
        ExportAnnotations(datafile_path,
                        imagedir_path,
                        resdir_path,
                        partitions,
                        self.format_option.get(),
                        self.stratify_var.get(),
                        self.empty_var.get())


# ========================================================== #
# ========================================================== #

if __name__ == "__main__":
    window = MainWindow()
    
    WINDOW: MainWindow = window
    DISPLAY: DisplayMaker = window.display
    SIDE: Sidebar = window.display.side
    MAIN: MainVisualizer = window.display.main
    
    window.mainloop()
        
    