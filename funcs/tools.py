from tkinter import messagebox
import ttkbootstrap as tkb
from ttkbootstrap.scrolled import ScrolledText as tkbScrolledText

from ultralytics import YOLO
from ultralytics.models.fastsam import FastSAMPredictor
from ultralytics.engine.results import Results

import os, shutil, json
from datetime import datetime
from math import floor, ceil
from random import choices as randchoices, randint
from typing import Any, Optional
import logging

from .constants import LETTERS1, LETTERS2, log_catcher, translator as _

ultralytics_logger = logging.getLogger('ultralytics')
ch = logging.StreamHandler(log_catcher)
ultralytics_logger.addHandler(ch)



class DetectToProject: 
    """Tool for segmenting 
    """
    def __init__(self,
                 master: tkb.Toplevel,
                 image_dir: str,
                 output_dir: str,
                 ann_type: str, 
                 model_dir: str, 
                 model_type: str,
                 model_task: str,
                 binarize: bool,
                 proj_dir: Optional[str]) -> None:
        self.master = master
        self.image_dir = image_dir
        self.output_dir = output_dir
        self.ann_type = ann_type
        self.model_dir = model_dir
        self.model_type = model_type
        self.model_task = model_task
        self.binarize = binarize
        self.proj_dir = proj_dir
        
        self.perclass_filter = self.polygon_perclass_filters if self.ann_type == 'polygon' else self.bbox_perclass_filters
        self.general_filter = self.polygon_general_filters if self.ann_type == 'polygon' else self.bbox_general_filters
        
        if not self.prepare_output(): return
        self.progress_window = ProgressWindow(self.processing_length)
        self.master.after(500, lambda *x: self.run_model())
        
    def prepare_output(self) -> bool:
        if self.proj_dir: 
            if not self.extract_data(): return False
            self.processing_length = len(self.all_marks)
        else:
            self.data = self.make_data()
            self.processing_length = len([image for image in os.listdir(self.image_dir) if os.path.splitext(image)[-1] in ['.jpg', '.jpeg', '.png']])
        
        if not os.path.isdir(self.output_dir): os.makedirs(self.output_dir, exist_ok=True)
        base_name = os.path.basename(self.image_dir)
        self.out_filename = [f'{base_name} - bbox', f'{base_name} - polygon'] if self.ann_type == 'bboxpoly' else f'{base_name} - {self.ann_type}'
        return True
    
    def extract_data(self) -> bool:
        with open(self.proj_dir, 'r') as file:
            data: dict = json.load(file)
        
        if self.image_dir != data['directory']: 
            check_img = True
            img_in_dir: list[bool] = []
        else: 
            check_img: bool = False
            img_in_dir = [True]
        
        all_marks: dict[str, dict[str, list[str]]] = data['all_marks']
        self.all_marks: dict = {}
        for image_name, image_data in all_marks.items():
            if check_img: img_in_dir.append(image_name in os.listdir(self.image_dir))
            self.all_marks.update({os.path.join(self.image_dir, image_name) : {
                                        classe : [
                                            [float(coord.split()[0]), float(coord.split()[1])]
                                            for coord in coords
                                        ] 
                                        for classe, coords in image_data.items()
                                    }})
        if check_img:
            if all(img_in_dir): pass
            elif any(img_in_dir): 
                continue_missing = messagebox.askyesno(title=_('Missing images'),
                                                       message=f'{_('Not all images in the project are present in the given directory.')}\n{_('Do you wish to continue?')}',
                                                       icon='warning')
                if not continue_missing: return False
            else: 
                messagebox.showerror(title=_('No images found'),
                                    message=f'{_('None of the images in the project are present in the given directory.')}\n{_('Choose a new directory and try again.')}')
                return False
        
        self.data = self.make_data(data['date_create'], data['classes'])
                    
        if self.binarize:
            for image, marks in self.all_marks.items():
                all_points = []
                for points in marks.values():
                    all_points += points
                self.all_marks[image] = {'object': all_points}
        return True

    def make_data(self, date_create: Optional[str] = None, classes: Optional[dict[str, dict]] = None) -> dict[str, Any]:
        if date_create is None: date_create = datetime.now().strftime("%d/%m/%Y %H:%M")
        if classes is None: classes = {}
        
        return {
            'directory': self.image_dir,
            'mode': 'manual',
            'sec_mode': self.ann_type,
            'date_create': date_create,
            'date_last': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'classes': {'object': {'id': 0, 'name': "Object", 'hex': "#808080"}} if self.binarize else classes,
            'all_ann': {}
        }
        
    def run_model(self) -> None:
        if "FastSAM" in self.model_dir: self.run_fastsam()
        elif self.model_type == "yolov8": self.run_yolo()
    
    
    def run_fastsam(self) -> None:
        overrides = dict(conf=0.25, task="segment", mode="predict", model=self.model_dir, save=False, imgsz=1024)
        predictor = FastSAMPredictor(overrides=overrides)
        
        all_marks = [(image, marks) for image, marks in self.all_marks.items()]
        
        self.fastsam_loop(all_marks, predictor)
        
    def fastsam_loop(self, all_marks: list[tuple[str, dict[int, list[list[float]]]]], 
                     predictor: FastSAMPredictor, index: int = 0) -> None:
        image, marks = all_marks[index]
        gen_results: list[Results] = predictor(image)
        
        results: dict[str, list[list[float]]] = {}
        img_size: tuple[int, int] = gen_results[0].orig_shape # height, width
        for tag_id, points in marks.items():
            spec_results: list[Results] = predictor.prompt(results=gen_results, points=points)
            objects: list[list[float]] = [obj.flatten().tolist() for obj in spec_results[0].masks.xy] if self.ann_type == 'polygon' else spec_results[0].boxes.xyxy.tolist()
            fixed_objects = self.perclass_filter(objects, img_size)
            results[tag_id] = fixed_objects
        results = self.general_filter(results, img_size)
        
        self.compile_data(image, [img_size[1], img_size[0]], results)
        
        self.progress_window._update(os.path.basename(image).split('.')[0])
        if index+1 < self.processing_length: 
            self.master.after(10, lambda *x: self.fastsam_loop(all_marks, predictor, index+1))
        else:
            result_path = self.write_data()
            self.progress_window._destroy(result_path)
            self.master.ok_button.configure(state='normal')
    
    
    def run_yolo(self) -> None:
        model = YOLO(model=self.model_dir, task=self.model_task)
        image_paths = [os.path.join(self.image_dir, image) for image in os.listdir(self.image_dir) if os.path.splitext(image)[-1] in ['.jpg', '.jpeg', '.png']]
        
        self.yolo_loop(model, image_paths)
        
    def yolo_loop(self, model: YOLO, image_paths: list[str], tag_ids: Optional[dict[int, str]] = None, index: int = 0) -> None:
        if tag_ids is None: tag_ids = {}
        cur_img_path = image_paths[index]
        prediction = model.predict(cur_img_path)

        img_size: tuple[int, int] = prediction[0].orig_shape # height, width
        class_ids = [int(class_id) for class_id in prediction[0].boxes.cls.tolist()]
        objects: list[list[float]] = prediction[0].boxes.xyxy.tolist() if self.ann_type == 'bbox' else [obj.flatten().tolist() for obj in prediction[0].masks.xy]
        
        data = {}
        for class_id, objeto in zip(class_ids, objects):
            if class_id not in tag_ids.keys(): 
                tag_ids[class_id] = self.create_tag_id(tag_ids.values())
            data[class_id] = data.get(class_id, []) + [objeto]
        
        results: dict[str, list[list[float]]] = {}
        for class_id, objects in data.items():
            fixed_objects = self.perclass_filter(objects, img_size)
            results[tag_ids[class_id]] = fixed_objects
        results = self.general_filter(results, img_size)
        self.compile_data(cur_img_path, img_size, results)
        
        self.progress_window._update(os.path.basename(cur_img_path))
        if index+1 < self.processing_length:
            self.master.after(10, lambda *x: self.yolo_loop(model, image_paths, tag_ids, index+1))
        else:
            for class_id, name in model.names.items():
                if class_id not in tag_ids.keys(): 
                    tag_ids[class_id] = self.create_tag_id(tag_ids.values())
                rand_hex = f'#{randint(0, 255):02x}{randint(0, 255):02x}{randint(0, 255):02x}'
                self.data['classes'][tag_ids[class_id]] = {'id':class_id, 'name':name, 'hex':rand_hex, 'visible': True}
            result_path = self.write_data()
            self.progress_window._destroy(result_path)
            self.master.ok_button.configure(state='normal')
    
    
    @staticmethod    
    def create_tag_id(tag_ids: list[str]) -> str:
        tag_id = "".join(randchoices(LETTERS1, k=6))
        while tag_id in tag_ids:
            tag_id = "".join(randchoices(LETTERS1, k=6))
        return tag_id 
    
    def compile_data(self, image: str, image_size: tuple[int, int],
                     results: dict[str, list[list[float]]]) -> None:
        image_path = os.path.basename(image)
        
        polygons = [(label, bbox) 
                    for label, bboxes in results.items()
                    for bbox in bboxes]
        
        polygon_ids: list[str] = []
        for _ in range(len(polygons)):
            polygon_id = "".join(randchoices(LETTERS2, k=10))
            while polygon_id in polygon_ids:
                polygon_id = "".join(randchoices(LETTERS2, k=10))
            polygon_ids.append(polygon_id)
        
        image_data = {'image_size' : image_size} |\
            {
            polygon_ids[i] : [polygons[i][0], polygons[i][1], {}]
            for i in range(len(polygons))
        }

        self.data['all_ann'][image_path] = image_data

    
    def bbox_perclass_filters(self, bboxes: list[list[float]], img_size: tuple[int, int]) -> list[list[float]]:
        return bboxes
    
    def polygon_perclass_filters(self, polygons: list[list[float]], img_size: tuple[int, int]) -> list[list[float]]:
        return polygons
    
    def bbox_general_filters(self, results: dict[str, list[list[float]]], img_size: tuple[int, int]) -> dict[str, list[list[float]]]:
        return results
    
    def polygon_general_filters(self, results: dict[str, list[list[float]]], img_size: tuple[int, int]) -> dict[str, list[list[float]]]:
        return results
    
    
    def write_data(self) -> str:
        file_path = os.path.join(self.output_dir, self.out_filename+'.json')
        
        with open(file_path, 'w') as file:
            json.dump(self.data, file, indent=4)
        return file_path
        

# ========================================================== #
# ========================================================== #


class ProgressWindow(tkb.Toplevel):
    def __init__(self, max_val: int):
        super().__init__(title=_("Progress"), topmost=True, minsize=[300, 130])
        self.max_val = max_val
        
        base_frame = tkb.Frame(master=self, relief='raised', padding=5)
        base_frame.pack(expand=True, fill='both')
        base_frame.columnconfigure(0, weight=1)
        
        bar_frame = tkb.Frame(master=base_frame,relief='ridge', padding=2, height=20)
        bar_frame.grid(column=0, row=0, sticky='new', pady=5)
        bar_frame.pack_propagate(False)
        self.create_bar(bar_frame)
        
        tkb.Separator(master=base_frame).grid(column=0, row=1, sticky='ew', pady=(4, 0))
        
        self.output_text = tkbScrolledText(master=base_frame, padding=5, autohide=True, wrap='word')
        self.output_text.text.insert('end', _('Initializing...'))
        self.output_text.text.config(state='disabled')
        self.output_text.grid(column=0, row=2, sticky='ew', pady=5)
           
    def create_bar(self, bar_frame: tkb.Frame) -> None:
        self.progress_value = tkb.IntVar(value=0)
        progress_text = tkb.StringVar(value= f'{_("Progress")}: 0 /{self.max_val}')
        self.progress_value.trace_add('write', lambda *x: progress_text.set(
                                        value=f'{_("Progress: ")} {self.progress_value.get()} /{self.max_val}')
                                      )
        progress_label = tkb.Label(master=bar_frame, textvariable=progress_text, justify='left')
        progress_label.pack(side='left')
        
        bar = tkb.Progressbar(master=bar_frame, 
                              variable=self.progress_value, 
                              maximum=self.max_val)
        
        bar.pack(side='bottom', expand=True, fill='both')

    def _update(self, cur_image: str = '') -> None:
        if cur_image == '': 
            self.progress_value.set(self.progress_value.get())
        self.progress_value.set(self.progress_value.get()+1)
        self.output_text.text.config(state='normal')
        self.output_text.text.insert('end', log_catcher.getvalue())
        self.output_text.text.config(state='disabled')
        log_catcher.clear()
    
    def _destroy(self, results_dir: str) -> None:
        if len(results_dir) > 45:
            if '\\' in results_dir:
                results_dir = '...' + '\\'.join(results_dir.split('\\')[-3:])
            elif '/' in results_dir:
                results_dir = '...' + '/'.join(results_dir.split('/')[-3:])
        infobox = messagebox.Message(title=_('Segmentation finished!'), 
                                     message=_('The results were placed in') + f':\n{results_dir}',
                                     icon='info', type='ok')
        infobox.show()
        
        self.destroy()


# ========================================================== #
# ========================================================== #


class ExportAnnotations:
    def __init__(self,
            data_dir: str,
            image_dir: str,
            res_dir: str,
            partitions: list[int],
            format: str, 
            harmonize: bool,
            empty: bool) -> None:
        
        self.data_dir = data_dir
        self.image_dir = image_dir
        self.res_dir = res_dir
        self.partitions = partitions
        self.format = format
        self.harmonize = harmonize 
        self.empty = empty
        
        self.extract_data()
        self.create_directories()
        self.write_yaml()
        images_per_partition = self.setup_partition_size()
        self.transfer_files(images_per_partition)
    
    def extract_data(self) -> None:
        with open(self.data_dir, 'r') as file:
            data: dict = json.load(file)

        classes: dict[str, dict[str, Any]] = data['classes']
        all_ann: dict[str, dict[str, list[Any]]] = data['all_ann']
        
        self.classes: list[tuple[int, str]] = [(int(classe['id']), classe['name']) for classe in classes]
        self.all_ann: dict[str, dict[int, list[list[int | float]]]] = {}
        self.classes_per_image: dict[str, dict[int, int]] = {}
        self.total_classes: dict[int, int] = {}
        
        for image_name, polygons in all_ann.items():
            image_data, image_classes = {}, {}
            
            if image_name not in os.listdir(self.image_dir): continue
            
            for polygon_id, polygon_data in polygons.items():
                if polygon_id == 'image_size':
                    cur_image_size = polygon_data
                    continue
                class_id: int = int(classes[polygon_data[0]]['id'])
                
                if class_id not in image_data.keys(): image_data[class_id] = []
                image_data[class_id].append(self.modelfix_coordinates(cur_image_size, polygon_data[1]))
                if class_id not in image_classes.keys(): image_classes[class_id] = 0
                image_classes[class_id] += 1
                if class_id not in self.total_classes.keys(): self.total_classes[class_id] = 0
                self.total_classes[class_id] += 1
            
            self.classes_per_image[image_name] = image_classes
            self.all_ann[image_name] = image_data
        
        self.total_classes = dict(sorted(self.total_classes.items(), key=lambda x:x[1]))
    
    def modelfix_coordinates(self, image_size: tuple[int, int], coordinates: list[float]) -> list[float]:
        if self.format == 'YOLOv8':
            if len(coordinates) > 4:
                return coordinates
            else:
                x1, y1, x2, y2 = coordinates
                return [(x1+x2)/2, (y1+y2)/2,
                        x2-x1, y2-y1]
        else:
            return [int(coordinates[i]*image_size[i%2]) for i in range(len(coordinates))]

    def create_directories(self) -> None:
        name = os.path.splitext(os.path.basename(self.data_dir))[0] + ' - Results'
        self.results_directory = os.path.join(self.res_dir, name)
        [os.makedirs(os.path.join(self.results_directory, partition, sub) ) 
         for partition in ['train', 'val', 'test'] 
         for sub in ['images', 'labels']]
    
    def setup_partition_size(self) -> list[list[str]]:
        partition_sizes: list[int] = [
            ceil(len(os.listdir(self.image_dir))*self.partitions[0]/100),
            floor(len(os.listdir(self.image_dir))*self.partitions[1]/100),
            floor(len(os.listdir(self.image_dir))*self.partitions[2]/100)
        ] if self.empty else [
            ceil(len(self.all_ann)*self.partitions[0]/100),
            floor(len(self.all_ann)*self.partitions[1]/100),
            floor(len(self.all_ann)*self.partitions[2]/100)
        ]
        
        classes_per_partition = [
            {
                class_id : ceil(size*self.partitions[i]/100) if i == 0 else 
                            floor(size*self.partitions[i]/100)
                    for class_id, size in self.total_classes.items()
            } for i in range(3)
        ] if self.harmonize else []
        
        return self.organize_images(partition_sizes, classes_per_partition)
    
    def organize_images(self, partition_sizes: list[int], classes_per_partition: list[dict[int, int]]) -> list[list[str]]:
        if len(classes_per_partition) > 0: 
            images_per_partition: list[list[str]] = []
            classes_per_image = self.classes_per_image
            empty_images = [image_name 
                            for image_name in os.listdir(self.image_dir) 
                            if image_name not in classes_per_image.keys()]
            
            for i in range(3):
                images_in_partition: list[str] = []
                classes_in_cur_partition = {n:0 for n in classes_per_partition[i].keys()}
                
                for class_id, size in classes_per_partition[i].items():
                    for image_name, image_classes in classes_per_image.copy().items():
                        if classes_in_cur_partition[class_id] >= size: break
                        if class_id not in image_classes.keys(): continue
                        images_in_partition.append(image_name)
                        classes_in_cur_partition.update({class_id: classes_in_cur_partition[class_id] + quant
                                                         for class_id, quant in image_classes.items()})
                        del classes_per_image[image_name]
            
                if self.empty: 
                    for image_name in empty_images.copy():
                        if len(images_in_partition) >= partition_sizes[i]: break
                        images_in_partition.append(image_name)
                        empty_images.remove(image_name)
            
                images_per_partition.append(images_in_partition)

        elif self.empty: 
            images_per_partition = [
                os.listdir(self.image_dir)[ : partition_sizes[0]],
                os.listdir(self.image_dir)[partition_sizes[0] : partition_sizes[0]+partition_sizes[1]],
                os.listdir(self.image_dir)[partition_sizes[0]+partition_sizes[1] : ]
            ]
        
        else: 
            images_per_partition = [
                self.all_ann.keys()[ : partition_sizes[0]],
                self.all_ann.keys()[partition_sizes[0] : partition_sizes[0]+partition_sizes[1]],
                self.all_ann.keys()[partition_sizes[0]+partition_sizes[1] : ]
            ]
        
        return images_per_partition
    
    def transfer_files(self, images_per_partition: list[list[str]]) -> None:
        partition_names = ['train', 'val', 'test']
        for i in range(3):
            images_dir = os.path.join(self.results_directory, 'images', partition_names[i])
            annotations_dir = os.path.join(self.results_directory, 'annotations', partition_names[i])
            for image_name in images_per_partition[i]:
                shutil.copyfile(os.path.join(self.image_dir, image_name), os.path.join(images_dir, image_name))
                self.write_annfile(image_name, annotations_dir)
    
    def write_annfile(self, image_name: str, annotations_dir: str) -> None:
        full_annotations_dir = os.path.join(annotations_dir, os.path.splitext(image_name)[0] + '.txt')
        if "\\" in full_annotations_dir: full_annotations_dir = full_annotations_dir.replace('/', '\\')
        with open(full_annotations_dir, mode='w') as file:
            if image_name in self.all_ann.keys():
                for class_id, polygons in self.all_ann[image_name].items():
                    for polygon in polygons:
                        file.write(f'{class_id} {" ".join([str(point) for point in polygon])}\n')

    def write_yaml(self) -> None:
        if self.format == 'YOLOv8':
            with open(os.path.join(self.results_directory, 'dataset_config.yaml'), mode='w') as yaml:
                yaml.write(f"path: {self.results_directory}\n")
                for partition in ['train', 'val', 'test']:
                    yaml.write(f'{partition}: {partition}\n')
                yaml.write('\nnames:\n')
                for id, name in self.classes:
                    yaml.write(f'    {id}: {name}')
                
            
# ========================================================== #
# ========================================================== #


class FilterImages:
    def __init__(self) -> None:
        raise NotImplementedError("If you are seeing this. How???")
