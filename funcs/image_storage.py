"""
Module that handles image and data processing, saving and loading makrs, classes and images
"""
from tkinter import filedialog, messagebox
 
from dataclasses import dataclass, asdict
import json
from datetime import datetime
from os import listdir, path as ospath, remove as osremove

from PIL import Image
from PIL.ImageFile import ImageFile
from typing import Literal, Any, Optional
from collections.abc import Callable
from .constants import translator as _

# ========================================================== #
# ========================================================== #

class AnnPoly:
    """Object storing all data related to an annotation polygon.
    """
    classe: str
    point_coords: list[float]
    polygon_id: str
    metadata: dict[str, str]
    
    def __init__(self,
                 first_point: str = 'd0',
                 classe: str = '',
                 polygon_id: str = '',
                 point_coords: list[float] = None,
                 metadata: dict[str, str] = None, 
                 ):
        """Object storing all data related to an annotation polygon.

        Args:
            first_point (str, optional): Canvas id of the polygon's starting point. Defaults to 'd0'.
            classe (str, optional): Class tag_id of the polygon. Defaults to ''.
            polygon_id (str, optional): Polygon's unique id tag. Defaults to ''.
            point_coords (list[float], optional): Coordinates of each point making up the polygon in the form `[x1, y1, x2, y2, ...]`. Defaults to None.
            metadata (dict[str, str], optional): Dictionary with all metadata in the form `{"field1": "data", "field2", "data"}`. Defaults to None.
        """
        self.points = [first_point]
        self.classe = classe
        self.point_coords = point_coords
        self.polygon_id = polygon_id
        self.metadata = metadata
    
    def new_point(self, point: str) -> None:
        """Adds the canvas id of a point to the list of points.

        Args:
            point (str): Canvas id of the new point.
        """
        self.points.append(point)
    
    def new_points(self, points: list[str]) -> None:
        """Adds the canvas id of multiple points to the list of points.

        Args:
            points (list[str]): List with the canvas id of each new point.
        """
        self.points += points
    
    def remove_last(self) -> None:
        """Removes the last point id from the list of points
        """
        del self.points[-1]

    def __len__(self) -> int:
        return int(len(self.point_coords)/2)
        
    def __str__(self) -> str:
        return f'polygon_id = {self.polygon_id}'\
               f'\n  > classe = {self.classe}'\
               f'\n  > point_coords = {self.point_coords}'\
               f'\n  > points = {self.points}'\
               f'\n  > metadata = {self.metadata}'


class MarkedImage:
    """Object holding the image data to be loaded and all marking/annotation.
    """
    def __init__(self, path: str, index: int):
        """Object holding the image data to be loaded and all marking/annotation.

        Args:
            path (str): Image path.
            index (int): Index of the image within all images.
        """
        self.name: str = ospath.basename(path)
        self.path: str = path
        self.size: tuple[int, int] = (1, 1) #* (width, height)
        self.index: int = index
        self.image: ImageFile | None = None
        self.marks: dict[str, list[str]] = {} #* 'tag_id': ['coordx coordy', ...]
        self.wip_poly: AnnPoly | None = None
        self.ann_polys: list[AnnPoly] = []

    def load(self) -> None:
        """Loas the image onto memory for display.
        """
        self.image = Image.open(self.path)
        self.size = self.image.size

    def unload(self) -> None:
        """Unloads image from memory.
        """
        if self.image is None: return
        self.image.close()
        self.image = None

    def new_annpoly(self, polygon: AnnPoly) -> None:
        """Stores an AnnPoly in construction.

        Args:
            polygon (AnnPoly): AnnPoly to be stored.
        """
        self.wip_poly = polygon
    
    def store_annpoly(self) -> None:
        """Stores a completed AnnPoly alongside the others to be saved.
        """
        if self.wip_poly is None: return
        self.ann_polys.append(self.wip_poly)
    
    def clear_wip(self) -> None:
        """Clears the current AnnPoly work in progress.
        """
        self.wip_poly = None
    
    def find_annpoly(self, key: Callable[[AnnPoly], bool]) -> int | None:
        """Searches for the first annotation polygon that satisfy the search key. 

        Args:
            key (Callable[[AnnPoly], bool]): Search key.

        Returns:
            int | None: Index of the polygon within the list or None if not found.
        """
        for poly in self.ann_polys:
            if key(poly):
                return self.ann_polys.index(poly)
        else: return


    def __str__(self) -> str:
        text = f'name = {self.name}\npath = {self.path}\nindex = {self.index}'
        text += '\n     marks:'
        for classe, pontos in self.marks.items():
            text += f'\n > {classe}'
            for ponto in pontos:
                text += f'\n  - {ponto}'
        text += '\n     ann_polys: \n       '
        text += '\n       '.join([str(annpoly).replace('\n', '\n       ') for annpoly in self.ann_polys])
        return text

# ========================================================== #
# ========================================================== #


@dataclass
class ImageData:
    """Object to store the data of a marking/annotation project.
    """
    
    directory: str
    mode: Literal['manual', 'semiauto']
    sec_mode: Literal['polygon', 'bbox']
    date_create: str
    date_last: str
    classes: dict[str, Any]
    
    def __init__(self, 
                 directory: str = '',
                 mode: Literal['manual', 'semiauto'] = 'manual', 
                 sec_mode: Literal['polygon', 'bbox'] = 'polygon',
                 date_create: str = '',
                 date_last: str = '',
                 classes: dict[str, dict[str, Any]] | None = None):
        """Class to store the data of a marking project.

        Args:
            directory (str) : The root directory of the images folder.
            mode (Literal['manual', 'semiauto']) : Mode of this project
                - manual: For manual annotation.
                - semiauto: For semiautomatic annotation ('marking').
            date_create (str) : The date and hour in which this project started
            date_create (str) : The date and hour in which this project was last worked on
            classes (dict[int, list[str]]) : Dictionary with the data of each class, with the format:
                {tag_id: {'id': 0, 'name': 'Car' 'hex_code': '#000000'}, ...} 
        """
        self.directory = directory
        self.mode = mode
        self.sec_mode = sec_mode
        self.date_create = date_create if date_create != '' \
                           else datetime.now().strftime("%d/%m/%Y %H:%M")
        self.date_last = date_last
        self.classes: dict[str, dict[str, Any]] = {} if classes is None else classes
        
        self.list_images: list[MarkedImage] = []
        self.active_index = 0
        
    # ---------------------------------------------------------- #
    
    def append(self, name: str) -> None:
        """Appends a MarkedImage to the list of images.

        Args:
            name (str): Image name to be added to the list.
        """
        path = ospath.join(self.directory, name)
        index = len(self.list_images)
        image = MarkedImage(path, index)
        self.list_images.append(image)
    
    def cur_image(self) -> MarkedImage | None:
        """Returns the currently loaded MarkedImage, returns None if empty.

        Returns:
            active_image (MarkedImage | None) : Currently loaded MarkedImage.
        """
        if len(self.list_images) == 0: return None
        return self.list_images[self.active_index]
    
    # ---------------------------------------------------------- #
    
    def jump_to(self, to: Literal['next', 'prev'] | int) -> None:
        """Handles jumping between indexes, either via numerica
        index or move command (forward or backwards), wrapping
        if necessary to prevent overflow.

        Args:
            to (Literal[&#39;next&#39;, &#39;prev&#39;] | int): 
                Move command or index value.
        """
        if len(self.list_images) == 0: return
        cur_index = self.active_index
        self.list_images[cur_index].unload()
        if isinstance(to, int): index = to
        elif to == 'next':
            index = 0 if cur_index+1>=len(self) else cur_index+1
        elif to == 'prev':
            index = len(self)-1 if cur_index <= 0 else cur_index-1
        else: return
        self.active_index = index
    
    # ---------------------------------------------------------- #
    
    def update_date(self, mode: str) -> str:
        """Updates date of last editing or returns a string with the date.

        Args:
            mode (str): Current save mode.

        Returns:
            now (str): Datetime string.
        """
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        if mode == 'backup': return now
        self.date_last = now
    
    def update_classes(self, tag_id: str, class_data: dict[str, Any]) -> None:
        """Adds or updates the classes dictionary with the given tag_id.

        Args:
            tag_id (str): Class tag_id to be aded or updated.
            class_data (dict[str, Any]): Data of the class with the format:
                {'id': 0, 'name': 'Car' 'hex_code': '#000000'}
        """
        self.classes.update({tag_id:class_data})    
    
    # ---------------------------------------------------------- #
    
    def load_directory(self) -> None:
        """Opens, sorts and loads the directory of images given in `self.directory`.
        """
        if self.date_create == '': 
            self.date_create = datetime.now().strftime("%d/%m/%Y %H:%M)")
        
        images = sorted([image for image in listdir(self.directory)
                            if image.split('.')[-1] in ['jpg', 'jpeg', 'png']], 
                        key= lambda name: name.lower())

        for image in images:
            self.append(image)
    
    def load_marks(self, all_marks: dict[str, dict[str, list[str]]]) -> tuple[int, str]:
        """Loads all marking points to their corresponding images. 

        Args:
            all_marks (dict[str, dict[str, list[str]]]) : Dicitionary with the data of each marked image of format:
                {"image_name.png": {"class_tag_id": ["x y", ...], ...}, ...}

        Returns:
            last (tuple[int, str]): Index and name of the last image to be marked.
        """
        if len(self) == 0:
            self.load_directory()
        last = (0, '')
        for image in self.list_images:
            if image.name not in all_marks.keys(): continue
            image.marks = all_marks[image.name]
            last = (image.index, image.name)
        return last
    
    def load_annpolygons(self, all_polys: dict[str, dict[str, tuple[str, list[float], dict[str, str]]]]) -> tuple[int, str]:
        """Loads all annotation polygons to their corresponding images.

        Args:
            all_polys (dict[str, dict[str, tuple[str, list[float], dict[str, str]]]]): Dictionary with the data of each annotatd image with format:
                {"image_name.png": {"polygon_id": ("class_tag_id", [x1, y1, x2, y2, ...], {"field1": "metadata1", "field2": "metadata2", ...}), ...}, ...}

        Returns:
            last (tuple[int, str]): Index and name of the last image to be annotated.
        """
        if len(self) == 0:
            self.load_directory()
        
        last = (0, self.list_images[0].name)
        for image in self.list_images:
            if image.name not in all_polys.keys(): continue
            for polygon_id, polygon_data in all_polys[image.name].items():
                if polygon_id == 'image_size':
                    image.size = polygon_data
                    continue
                image.ann_polys.append(AnnPoly(polygon_id=polygon_id, 
                                               classe=polygon_data[0], 
                                               point_coords=polygon_data[1],
                                               metadata=polygon_data[2]))
            last = (image.index, image.name)
        return last
            
    def sort_annotations(self, ann_dir: str) -> dict[str, dict[str, list[list[float]]]]:
        """Returns a dictionary where every key is an annotation file in ``ann_dir`` and each item is a secondary dictionary.\\
        This secondary dictionary holds each class present in the annotation file, connected to a list of polygons (list of floats).
        
        Args:
            ann_dir (str) : The path for the directory holding the txt files.
        
        Returns:
            annotations (dict[str, dict[int, list[list[float]]]]) : Dictonary holding all annotations of each file, sorted alphabeticaly of format:
                {'file_name1': {0: [[x1, y1, x2, y2,...], ...], ...}, ...}
        
        """
        
        ann_data: dict[str, dict[int: list[list[float]]]] = {}
        for ann_file in listdir(ann_dir):
            *file_name, ext = ann_file.split('.')
            if ext != 'txt': continue
            else: file_name = '.'.join(file_name)
            
            ann_data[file_name] = {}
            with open(ospath.join(ann_dir, ann_file), 'r') as file_data:
                cur_ann_data: dict[int: list[list[float]]] = {}
                for line in file_data:
                    classe, *poly = line.split()
                    poly = [float(coord) for coord in poly]
                    if classe not in cur_ann_data:
                        cur_ann_data[classe] = [poly]
                    else:
                        cur_ann_data[classe].append(poly)
                        
            ann_data[file_name] = dict(sorted(cur_ann_data.items(), key=lambda classe: classe[0]))
            
        return dict(sorted(ann_data.items(), key=lambda classe: classe[0]))
    
    def unload_marks(self) -> dict[str, dict[str, list[str]]]:
        """Returns a dictionary with each image's marking point data.

        Returns:
            dict[str, dict[str, list[str]]]: Dictionary with each image's marking point data of format:
                {"image_name.png": {"class_tag_id": ["x y", ...], ...}, ...}
        """
        return {image.name : image.marks
                  for image in self.list_images 
                    for classe in image.marks 
                      if len(image.marks) > 0
                      if len(image.marks[classe]) > 0
                 }
    
    def unload_polys(self) -> dict[str, dict[str, tuple[str, list[float], dict[str, str]]]]:
        """Returns a dictionary with each image's annotation polygon data.

        Returns:
            dict[str, dict[str, list[str]]]: Dictionary with each image's annotation polygon data of format:
                {"image_name.png": {"polygon_id": ("class_tag_id", [x1, y1, x2, y2, ...], {"field1": "metadata1", "field2": "metadata2", ...}), ...}, ...}
        """
        return {image.name : {'image_size': image.size} |\
                             {poly.polygon_id : 
                                (poly.classe, 
                                 poly.point_coords, 
                                 poly.metadata)
                                    for poly in image.ann_polys}
                  for image in self.list_images
                    if len(image.ann_polys) > 0
                }

    def sort_classes(self) -> None:
        """Sorts the classes either alphabetically (in visualization mode) or by id value (marking/annotation mode).
        """
        key = lambda classe: classe[1]['id']
        self.classes = dict(sorted(self.classes.items(), key=key))
        
    # ---------------------------------------------------------- #
    
    def clean(self, clear_classes: bool = True) -> None:
        """Completely wipes the data in ImageData.
        """
        self.directory = ''
        self.date = ''
        self.list_images[self.active_index].unload()
        self.list_images.clear()
        self.active_index = 0
        self.classes.clear()
        
    # ---------------------------------------------------------- #
        
    def __len__(self) -> int:
        return len(self.list_images)

    def __str__(self) -> str:
        return f"direcotry = {self.directory} \nmode = {self.mode} \nsecondary mode = {self.sec_mode} \ndate_create = {self.date_create} \ndate_last = {self.date_last}" +\
                "\nclasses: \n  > " + "\n  > ".join([f"{index} - {'; '.join([f"{name} : {data}" for name, data in class_data.items()])}" for index, class_data in self.classes.items()]) +\
                "\nlist_images: \n  " + '\n  '.join([str(image).replace('\n', '\n  ') for image in self.list_images])
# ========================================================== #
# ========================================================== #


class ImageLoader:
    """Class to handle loading and saving folders and projects."""
    def __init__(self,
                 master,
                 config_path: str,
                 config: dict[str, Any],
                 gettext: Callable[[str], str]) -> None:
        """Class to handle loading and saving folders and projects.

        Args:
            master (_type_): MainWindow class.
            config_path (str): Path of configuration file.
            config (dict[str, Any]): Current active configurations.
            gettext (Callable[[str], str]): Text translation function.
        """
        
        self.master = master
        self.images: list[ImageData | None] = [None]
        self.config_path: str = config_path
        self.config = config
        _ = gettext
        self.img_dir: str = ''
        self.last_saved_dir: str = ''
    
    def directory_prompt(self, parent: Optional[Any] = None, all_data: Optional[dict] = None) -> str | None:
        """Prompts the user at choosing an image directory, checking if it is valid.\\
        If a project is already loaded, it checks if the chosen directory constains the project's images.

        Args:
            parent (Any, optional): 
                Widget parent for the directory prompt. Defaults to None. 
            all_data (dict, optional): 
                Loaded project data. Defaults to None.

        Returns:
            directory (str | None): 
                Chosen directory path if valid, None if invalid.
        """
        directory = filedialog.askdirectory(title=_("Select image directory"), mustexist=True, parent=parent)
        
        if not self.check_imgdir(directory): return
        
        if all_data is None: return directory
        
        data_type = 'all_ann' if all_data['mode'] == "manual" else 'all_marks'
        marked_images = [image_name for image_name in all_data[data_type].keys()]
        has_images = sum([file in marked_images for file in listdir(directory)])
        if has_images == 0:
            messagebox.showerror(
                title=_("Invalid directory"),
                message=_("The selected directory does not have any of the images marked in the project.")
            )
            return
        if has_images < len(marked_images):
            load_images = messagebox.askyesno(
                title=_("Marked images missing"), 
                message=_("There are marked images in the project not found in the directory selected.")+'\n'+\
                        _("Would you like to continue?")
            )
            if not load_images: return
        return directory

    def check_imgdir(self, directory: str) -> bool:
        """Function to check validity of an image directory.

        Args:
            directory (str): Direcotry to be checked.

        Returns:
            valid_dir (bool): If the given directory is a valid image directory.
        """
        if directory in [None, '', ()]: return False
        
        if not ospath.isdir(directory):
            messagebox.showerror(
                title=_("Invalid directory"),
                message=_("The selected directory does not exist.")
                )
            return False
        
        has_format = sum([ospath.splitext(file)[-1] in ['.jpg', '.jpeg', '.png'] for file in listdir(directory)])
        if has_format == 0:
            messagebox.showerror(
                title=_("Invalid directory"),
                message=_("The selected directory does not have any of the following formats")+':\n' +\
                            f"{', '.join(['.jpg', '.jpeg', '.png'])}"
                            )
            return False
        return True
    
    def select_directory(self, parent: Any, preset_directory: Optional[str] = None) -> tuple[(str | None), dict]:
        """Prompts the user to save unsaved data, keep already created classes for the new project and choose an image directory.
        
        Args:
            parent (Any): 
                Widget parent for the directory prompt. 
            preset_directory (str, Optional):
                Preset directory to be loaded instead of prompting for a new one. Defaults to None.
        
        Returns:
            directory&classes (tuple[str | None, dict]): 
                Tuple containing chosen directory path & classes preset to be loaded with the project.
        """
        self.save_unsaved()
        
        if self.images[0] is not None and len(self.images[0].classes) > 0:
            keep_classes = messagebox.askyesno(
                                title=_("Keep classes"), 
                                message=_("Would you like to keep the classes already set up on your new project?")
                            )
            if keep_classes: classes = self.images[0].classes.copy()
            self.images[0].clean()
            self.images[0] = None
        else: classes = {}
        self.master._update()
        
        if preset_directory:
            directory = preset_directory if self.check_imgdir(preset_directory) else None
        else:
            directory = self.directory_prompt(parent)
        
        return directory, classes
    
    def load_directory(self, directory: str, mode: str, sec_mode: str, classes: dict) -> None:
        """Creates a new ImageData object with the given data and loads the given directory.

        Args:
            directory (str): Image directory path.
            mode (str): Project mode.
            sec_mode (str): Project mode specification.
            classes (dict): Classes preset to be added to the project.
        """
        self.img_dir = directory
        self.images[0] = ImageData(directory, mode, sec_mode, classes=classes)
        self.images[0].load_directory()
        
        self.master._update()

    def select_datafile(self, preset_path: str = '') -> None:
        """Prompts the user to select a project, checks if it's valid and loads it.

        Args:
            preset_path (str, optional): Data file to be loaded. Defaults to ''.

        """
        self.save_unsaved()
        if self.images[0] is not None:
            self.images[0].clean()
            self.images[0] = None
            self.master._update()
        
        if preset_path == '':
            file_path = filedialog.askopenfilename(
                title=_('Select project file'),
                filetypes=[(_("json file"), "*.json")])
            if file_path in [None, '', ()]: return (None, None)
            elif not ospath.isfile(file_path): 
                messagebox.showerror(
                    title=_("Invalid file"),
                    message=_("The selected file does not exist.")
                                )
                
            self.last_saved_dir = file_path
        else:
            file_path = ospath.join(self.config_path, preset_path)
        
        with open(file_path, 'r') as file:
            all_data: dict = json.load(file)
        
        try:
            for data_section in ['directory', 'mode', 'date_create', 'date_last', 'classes']:
                all_data[data_section]
        except KeyError:
            messagebox.showerror(
                title=_("Invalid file"),
                message=_("The selected file is not a proper project file.")
                            )
            return
        
        self.projectfile_actions(file_path, all_data)  
        
    def projectfile_actions(self, file_path: str, all_data: dict) -> None:
        """Checks the content of the data within the project file and loads if in order.

        
        Args:
            parent (Any): 
                Widget parent for the directory prompt. 
            file_path (str): 
                Path of the project file.
            all_data (dict): 
                Project data.
        """
        
        if not ospath.isdir(all_data['directory']): # Checks if the image directory exist
            load_images = messagebox.askokcancel(
                            title=_("Image directory not found"), 
                            message=_("The image directory for the project was not found.")+'\n'+\
                                    _("You have to load a different directory with the project images.")
                            )
            if not load_images: return
            new_directory = self.directory_prompt(all_data=all_data)
            if new_directory == None: return
            all_data['directory'] = new_directory
        
        if 'save_dir' in all_data.keys(): # In case of a backup save file, the last save directory.
            self.last_saved_dir = all_data.pop('save_dir')
        
        if file_path not in self.config['recent'] and '.bak' not in file_path:
            self.config['recent'].append(file_path) # Adds to the recent loaded files.
        
        self.images[0] = ImageData(all_data['directory'],
                                   all_data['mode'],
                                   all_data['sec_mode'],
                                   all_data['date_create'],
                                   all_data['date_last'],
                                   all_data['classes'])
        self.img_dir = all_data['directory']
        
        if all_data['mode'] == 'semiauto':
            last = self.images[0].load_marks(all_data['all_marks'])
        elif all_data['mode'] == 'manual':
            self.images[0].sec_mode = all_data['sec_mode']
            last = self.images[0].load_annpolygons(all_data['all_ann'])
        self.master._update()
        if last[0] == 0: return
        from_last = messagebox.askyesno(
                        title=_("Continue from last"),
                        message=f"{_('The last marked image in the project was')}\n{_('Image')}:{last[0]+1} - {last[1]}\n{_("Would you like to continue from it?")}"
                        )
        if from_last: self.master.display.main.skip_image(last[0])
      
    def save_unsaved(self) -> bool:
        """Prompts the user to save unsaved data.

        Returns:
            move_forward (bool): If the process should be continued or halted (the user canceled).
        """
        if self.images[0] is None or self.master.saved: return True
        prev_action = messagebox.askyesnocancel(
                            title=_("Save marks"), 
                            message=_("You have unsaved marked images currently loaded in.")+'\n'+\
                                    _("Would you like to save them before loading another project?")
                        )
    
        if prev_action is None: return False
        elif prev_action: 
            self.master.saved = self.save_project('normal')
            if not self.master.saved: return False
            self.last_saved_dir = ''
            return True
        else:
            self.last_saved_dir = ''
            return True

    def save_project(self, save_mode: Literal['normal', 'choose', 'backup']) -> bool:
        """Saves the currently loaded project. \\
        Either by saving on a previously chosen directory, prompting the user to choose a new directory or on a preset directory as a backup file.

        Args:
            save_mode (Literal[&#39;normal&#39;, &#39;choose&#39;, &#39;backup&#39;]): Saving mode.

        Returns:
            saved (bool): If the project was saved.
        """
        if self.images[0] is None: return False
        
        project_mode = self.images[0].mode
        
        file_name = ospath.basename(self.last_saved_dir) if self.last_saved_dir != '' \
                    else _("Marks") + ' - ' + ospath.split(self.img_dir)[1] if project_mode == 'semiauto' \
                    else _("Annotations") + ' - ' + ospath.split(self.img_dir)[1]
       
        now = self.images[0].update_date(save_mode)
        all_data = asdict(self.images[0])
        if project_mode == 'semiauto':
            all_data['all_marks'] = self.images[0].unload_marks()
        elif project_mode == 'manual':
            all_data['all_ann'] = self.images[0].unload_polys()
            
        if save_mode == 'backup':
            file_path = ospath.join(self.config_path, file_name + '.bak.json')
            all_data['date_last'] = now
            all_data['save_dir'] = self.last_saved_dir
            with open(file_path, 'w') as output:
                json.dump(all_data, output, indent=4, separators=(', ', ': '))
            
            self.master.display.low.update_labels(now) 
            return True
        
        elif save_mode == 'normal' and self.last_saved_dir != '':
            with open(self.last_saved_dir, 'w') as output:
                json.dump(all_data, output, indent=4, separators=(', ', ': '))
        
        else:
            initialdir = self.img_dir if self.config['default_output'] == '' \
                else self.config['default_output']
            file_path = filedialog.asksaveasfilename(
                title=_('Choose annotation output'),
                initialdir=initialdir,
                initialfile= file_name,
                defaultextension=".json", 
                filetypes=[(_("json file"), "*.json")]
                )
            if file_path in [None, '', ()]: return False
            if not ospath.isdir(ospath.dirname(file_path)):
                messagebox.showerror(
                    title=_("Invalid directory"),
                    message=_("Selected directory does not exist.")
                )
                return False
            
            with open(file_path, 'w') as output:
                json.dump(all_data, output, indent=4, separators=(', ', ': '))
            self.last_saved_dir = file_path

        for file in listdir(self.config_path):
            if '.bak' not in file: continue
            osremove(ospath.join(self.config_path, file))
        messagebox.showinfo(_("Saved"), _("Marks saved with success!"))
        
        self.master.display.low.update_labels()
        return True
