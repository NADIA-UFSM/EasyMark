"""
Module that handles image and data processing, saving and loading makrs, categories and images
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
from .constants import CONFIG, translator as _
from .typeAliases import AnnotationDataType, ImageDataType, CategoryDataType


# ========================================================== #
# ========================================================== #



class Annotation:
    """Object storing all data related to an annotation polygon.
    """
    cat_id: str
    coords: list[float]
    annotation_id: str
    annotation_type: Literal['bbox', 'obbox', 'poly', 'mark']
    metadata: dict[str, str]
    
    def __init__(self,
                 annotation_id: str,
                 cat_id: str,
                 point_coords: list[float],
                 annotation_type: Literal['bbox', 'obbox', 'poly', 'mark'] = 'poly',
                 metadata: Optional[dict[str, str]] = None, 
                 point_id: int = 0, 
                 ):
        """Object storing all data related to an annotation polygon.

        Args:
            point_coords (list[float]): Coordinates of each point making up the polygon in the form `[x1, y1, x2, y2, ...]`..
            cat_id (str): Class cat_id of the polygon.
            annotation_id (str): Polygon's unique id tag.
            metadata (dict[str, str], optional): Dictionary with all metadata in the form `{"field1": "data", "field2", "data"}`. Defaults to ''.
        """
        self.annotation_type = annotation_type
        self.cat_id = cat_id
        self.coords = point_coords
        self.annotation_id = annotation_id
        self.metadata = {} if metadata is None else metadata
        self.point_ids = [point_id]
    
    def add_point(self, point_id: int, point_coords: list[float]) -> None:
        """Adds the canvas id of a point to the list of points.

        Args:
            point (str): Canvas id of the new point.
        """
        self.point_ids.append(point_id)
        self.coords += point_coords
    
    def remove_points(self, num_points: int = 1) -> tuple[list[int], list[float]]:
        """Removes the last point id from the list of points
        """
        match self.annotation_type:
            case 'mark':
                return self.point_ids, self.coords                
            case 'bbox':
                num_points = min(num_points, 2)
                deleted_points = self.point_ids[-num_points:]
                del self.point_ids[-num_points:]
                
                if num_points == 1:
                    deleted_coords = self.coords[4:6]
                    del self.coords[2:]
                else:
                    deleted_coords = self.coords[0:2] + self.coords[4:6]
                    del self.coords[:] 
            case 'obbox':
                num_points = min(num_points, 3)
                deleted_points = self.point_ids[-num_points:]
                del self.point_ids[-num_points:]
                
                del self.coords[6:]
                deleted_coords = self.coords[-num_points*2:]
                del self.coords[-num_points*2:]
            case 'poly':
                deleted_points = self.point_ids[-num_points:]
                del self.point_ids[-num_points:]
                
                deleted_coords = self.coords[-num_points*2:]
                del self.coords[-num_points*2:]
        return deleted_points, deleted_coords
    
    def set(self, coords: Optional[list[float]] = None, point_ids: Optional[list[int]] = None, metadata: Optional[dict[str, str]] = None) -> None:
        if coords is not None: self.coords = coords
        if point_ids is not None: self.point_ids = point_ids
        if metadata is not None: self.metadata = metadata
    
    def data(self) -> AnnotationDataType:
        return self.cat_id, self.coords, self.annotation_type, self.metadata
    
    def __len__(self) -> int:
        return int(len(self.coords)/2)

    def __str__(self) -> str:
        return f'{self.cat_id = }, {self.coords = }, {self.point_ids = }, {self.annotation_id = }, {self.annotation_type = }, {self.metadata = }'

class AnnImage:
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
        self.wip_ann: Annotation | None = None
        self.annotations: list[Annotation] = []

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

    def new_annotation(self, polygon: Annotation) -> None:
        """Stores an Annotation in construction.

        Args:
            polygon (Annotation): Annotation to be stored.
        """
        self.wip_ann = polygon
    
    def store_annotation(self, annotation: Optional[Annotation] = None) -> None:
        """Stores a completed Annotation alongside the others to be saved.
        """
        if annotation is not None: self.annotations.append(annotation)
        elif self.wip_ann is not None: self.annotations.append(self.wip_ann)
    
    def clear_wip(self) -> None:
        """Clears the current Annotation work in progress.
        """
        self.wip_ann = None
    
    def find_annotation(self, key: Callable[[Annotation], bool]) -> int | None:
        """Searches for the first annotation polygon that satisfy the search key. 

        Args:
            key (Callable[[Annotation], bool]): Search key.

        Returns:
            Index (int | None): Index of the polygon within the list or None if not found.
        """
        for ann in self.annotations:
            if key(ann):
                return self.annotations.index(ann)
        else: return

    def __str__(self) -> str:
        return f'name: {self.name} \npath: {self.path} \nsize: {self.size} \nindex: {self.index} \nannotations:\n {'\n '.join([str(ann) for ann in self.annotations])}'
        
# ========================================================== #
# ========================================================== #





@dataclass
class ImageData:
    """Object to store the data of a marking/annotation project.
    """
    
    directory: str
    mode: Literal['manual', 'semiauto']
    date_create: str
    date_last: str
    categories: dict[str, CategoryDataType]
    
    def __init__(self, 
                 directory: str = '',
                 mode: Literal['manual', 'semiauto'] = 'manual',
                 date_create: str = '',
                 date_last: str = '',
                 categories: Optional[dict[str, CategoryDataType]] = None):
        """Class to store the data of a marking project.

        Args:
            directory (str) : The root directory of the images folder.
            mode (Literal['manual', 'semiauto']) : Mode of this project
                - manual: For manual annotation.
                - semiauto: For semiautomatic annotation ('marking').
            date_create (str) : The date and hour in which this project started
            date_create (str) : The date and hour in which this project was last worked on
            categories (dict[int, list[str]]) : Dictionary with the data of each categories, with the format:
                {cat_id: {'id': 0, 'name': 'Car' 'hex_code': '#000000'}, ...} 
        """
        self.directory = directory
        self.mode = mode
        self.date_create = date_create if date_create != '' \
                           else datetime.now().strftime("%d/%m/%Y %H:%M")
        self.date_last = date_last
        self.categories = {} if categories is None else categories
        
        self.list_images: list[AnnImage] = []
        self.active_index = 0
        
    # ---------------------------------------------------------- #
    
    def append(self, name: str) -> None:
        """Appends a MarkedImage to the list of images.

        Args:
            name (str): Image name to be added to the list.
        """
        path = ospath.join(self.directory, name)
        index = len(self.list_images)
        image = AnnImage(path, index)
        self.list_images.append(image)
    
    def cur_image(self) -> AnnImage | None:
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
    
    def update_date(self, mode: str) -> str | None:
        """Updates date of last editing or returns a string with the date.

        Args:
            mode (str): Current save mode.

        Returns:
            now (str): Datetime string.
        """
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        if mode == 'backup': return now
        self.date_last = now
    
    def update_categories(self, cat_id: str, categories_data: CategoryDataType) -> None:
        """Adds or updates the categories dictionary with the given cat_id.

        Args:
            cat_id (str): Class cat_id to be aded or updated.
            categories_data (dict[str, Any]): Data of the categories with the format:
                {'id': 0, 'name': 'Car' 'hex_code': '#000000'}
        """
        self.categories.update({cat_id:categories_data})    
    
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
    
    def load_annpolygons(self, all_polys: dict[str, ImageDataType]) -> tuple[int, str]:
        """Loads all annotation polygons to their corresponding images.

        Args:
            all_polys (dict[str, dict[str, tuple[str, list[float], dict[str, str]]]]): Dictionary with the data of each annotatd image with format:
                {"image_name.png": {"annotation_id": ([x1, y1, x2, y2, ...], "cat_id", "polygon_type", {"field1": "metadata1", "field2": "metadata2", ...}), ...}, ...}

        Returns:
            last (tuple[int, str]): Index and name of the last image to be annotated.
        """
        if len(self) == 0: self.load_directory()
        
        last = (0, self.list_images[0].name)
        for image in self.list_images:
            if image.name not in all_polys.keys(): continue
            for annotation_id, annotation_data in all_polys[image.name].items():
                if annotation_id == 'image_size':
                    assert len(annotation_data) == 2
                    image.size = annotation_data; 
                    continue
                assert len(annotation_data) == 4
                image.annotations.append(Annotation(annotation_id, *annotation_data))
            last = (image.index, image.name)
        return last

    def unload_polys(self) -> dict[str, ImageDataType]:
        """Returns a dictionary with each image's annotation polygon data.

        Returns:
            dict[str, dict[str, list[str]]]: Dictionary with each image's annotation polygon data of format:
                {"image_name.png": {"annotation_id": ("category_id", [x1, y1, x2, y2, ...], {"field1": "metadata1", "field2": "metadata2", ...}), ...}, ...}
        """
        return {image.name : {'image_size': image.size} |\
                             {poly.annotation_id : poly.data() for poly in image.annotations}
                  for image in self.list_images
                    if len(image.annotations) > 0
                }

    def sort_categories(self) -> None:
        """Sorts the categories either by id value.
        """
        key = lambda category: category[1]['id']
        self.categories = dict(sorted(self.categories.items(), key=key))
        
    # ---------------------------------------------------------- #
    
    def clean(self, clear_categories: bool = True) -> None:
        """Completely wipes the data in ImageData.
        """
        self.directory = ''
        self.date = ''
        self.list_images[self.active_index].unload()
        self.list_images.clear()
        self.active_index = 0
        if clear_categories: self.categories.clear()
        
    # ---------------------------------------------------------- #
        
    def __len__(self) -> int:
        return len(self.list_images)

    def __str__(self) -> str:
        return f"direcotry = {self.directory} \nmode = {self.mode} \ndate_create = {self.date_create} \ndate_last = {self.date_last}" +\
                "\ncategories: \n  > " + "\n  > ".join([f"{index} - {'; '.join([f"{name} : {data}" for name, data in categories_data.items()])}" for index, categories_data in self.categories.items()]) +\
                "\nlist_images: \n  " + '\n  '.join([str(image).replace('\n', '\n  ') for image in self.list_images])
# ========================================================== #
# ========================================================== #


class ImageLoader:
    """Class to handle loading and saving folders and projects."""
    def __init__(self,
                 master,
                 config_path: str) -> None:
        """Class to handle loading and saving folders and projects.

        Args:
            master (_type_): MainWindow categories.
            config_path (str): Path of configuration file.
            gettext (Callable[[str], str]): Text translation function.
        """
        
        self.master = master
        self.images: list[ImageData | None] = [None]
        self.config_path: str = config_path
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
        """Prompts the user to save unsaved data, keep already created categories for the new project and choose an image directory.
        
        Args:
            parent (Any): 
                Widget parent for the directory prompt. 
            preset_directory (str, Optional):
                Preset directory to be loaded instead of prompting for a new one. Defaults to None.
        
        Returns:
            directory&categories (tuple[str | None, dict]): 
                Tuple containing chosen directory path & categories preset to be loaded with the project.
        """
        self.save_unsaved()
        
        if self.images[0] is not None and len(self.images[0].categories) > 0:
            keep_categories = messagebox.askyesno(
                                title=_("Keep categories"), 
                                message=_("Would you like to keep the categories already set up on your new project?")
                            )
            categories = self.images[0].categories.copy() if keep_categories else {}
            
            self.images[0].clean(keep_categories)
            self.images[0] = None
        else: categories = {}
        self.master._update()
        
        if preset_directory:
            directory = preset_directory if self.check_imgdir(preset_directory) else None
        else:
            directory = self.directory_prompt(parent)
        
        return directory, categories
    
    def load_directory(self, directory: str, mode: Literal['manual', 'semiauto'], categories: dict) -> None:
        """Creates a new ImageData object with the given data and loads the given directory.

        Args:
            directory (str): Image directory path.
            mode (str): Project mode.
            categories (dict): categories preset to be added to the project.
        """
        self.img_dir = directory
        self.images[0] = ImageData(directory, mode, categories=categories)
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
            if file_path in [None, '', ()]: return 
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
            for data_section in ['directory', 'mode', 'date_create', 'date_last', 'categories']:
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
        
        if file_path not in CONFIG.recent and '.bak' not in file_path:
            CONFIG.recent.append(file_path) # Adds to the recent loaded files.
        
        self.images[0] = ImageData(all_data['directory'],
                                   all_data['mode'],
                                   all_data['date_create'],
                                   all_data['date_last'],
                                   all_data['categories'])
        self.img_dir = all_data['directory']
        
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
            initialdir = self.img_dir if CONFIG.default_output == '' \
                else CONFIG.default_output
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
