from .typeAliases import _actionType, _annTypeGen
from .image_storage import Annotation
from typing import Any, Optional, Literal

#* Fully documented
class BaseAction():
    """Base class for all Actions.

    Raises:
        NotImplementedError: `reaction` function has no implemented functionality.

    Returns:
        Action: Action class storing a reaction dependent on the user's action.
    """
    WINDOW: Any
    SIDE: Any
    MAIN: Any
    
    reaction_matches: dict[_actionType, _actionType] = {
            'added_categories': 'deleted_categories',
            'deleted_categories': 'added_categories',
            'edited_category': 'edited_category',
            'added_points': 'deleted_points',
            'deleted_points': 'added_points',
            'finished_annotation':'restarted_annotation',
            'restarted_annotation':'finished_annotation',
            'added_annotations': 'deleted_annotations',
            'deleted_annotations': 'added_annotations',
            'edited_annotations': 'edited_annotations',
            'moved_page': 'moved_page'
        }
    
    def __init__(self, action_type: _actionType, **kwargs):
        self.action_type: _actionType = action_type
    
    @classmethod
    def set_interface_variables(cls, W, S, M) -> None:
        cls.WINDOW = W
        cls.SIDE = S
        cls.MAIN = M
        
    def __call__(self): 
        return NewAction(action_type=self.reaction_matches[self.action_type], data=self.reaction())
    
    def reaction(self):
        raise NotImplementedError(f"No implemented reaction fucntionality for '{str(self)}'")
    
    def __str__(self) -> str:
        return f'Action({self.action_type})'

#! Not documented
class AddedPoints(BaseAction):
    def __init__(self, primary_data: Literal['all', 'last']):
        super().__init__('added_points')
        self.points = primary_data
    
    def reaction(self):
        return self.MAIN.remove_points(self.points, False)
    
    def __str__(self) -> str:
        return super().__str__()[-1] + f', {self.points})'
#! Not documented
class DeletedPoints(BaseAction):
    def __init__(self, primary_data: list[tuple[str, ...]]):
        super().__init__('deleted_points')
        self.deleted_points = primary_data
    
    def reaction(self):
        for i, deleted_point in enumerate(self.deleted_points):
            raw_point_type, point_id, raw_rel_pos, cat_id = deleted_point[1:5]
            pos = self.MAIN.coords_rel2canvas([float(val) for val in raw_rel_pos.split()])
            point_type = raw_point_type.split('-')[0]
            self.MAIN.draw_point(pos, point_type, cat_id)  # type: ignore
        
        return 'last' if len(self.deleted_points) == 1 else 'all'
    
    def __str__(self) -> str:
        return super().__str__()[-1] + f', {self.deleted_points})'
#! Not documented
class FinishedAnnotation(BaseAction):
    def __init__(self, primary_data: str):
        super().__init__('finished_annotation')
        self.annotation_id = primary_data
    
    def reaction(self):
        del_ann = self.MAIN.remove_annotations(self.annotation_id, direct_command=False)[0]
        coords = del_ann.coords
        fixed_coords = self.MAIN.coords_rel2canvas(coords)
        ann_type = del_ann.annotation_type
        cat_id = del_ann.cat_id
        match ann_type:
            case 'bbox':
                self.MAIN.draw_point(fixed_coords[0:2], ann_type, cat_id)
                return coords[4:6], ann_type, cat_id
            case 'obbox':
                self.MAIN.draw_point(fixed_coords[0:2], ann_type, cat_id)
                self.MAIN.draw_point(fixed_coords[2:4], ann_type, cat_id)
                return coords[4:6], ann_type, cat_id
            case 'poly':
                for i in range(int(len(fixed_coords)/2)):
                    self.MAIN.draw_point(fixed_coords[i*2:i*2+2], ann_type, cat_id)
                return coords[0:2], ann_type, cat_id
            case _:
                error_message = f'Invalid ann_type "{ann_type}"'
                raise ProcessLookupError(error_message)
    
    def __str__(self) -> str:
        return super().__str__()[-1] + f', {self.annotation_id})'
#! Not documented
class RestartedAnnotation(BaseAction):
    def __init__(self, primary_data: tuple[list[float], _annTypeGen, str]):
        super().__init__('restarted_annotation')
        self.finish_point_data = primary_data
    
    def reaction(self) :
        coords, ann_type, cat_id = self.finish_point_data
        fixed_coors = self.MAIN.coords_rel2canvas(coords)
        obj_id = self.MAIN.draw_point(fixed_coors, ann_type, cat_id)
        assert isinstance(obj_id, str)
        return obj_id
    
    def __str__(self) -> str:
        return super().__str__()[-1] + f', {self.finish_point_data})'
#! Not documented
class AddedAnnotations(BaseAction):
    def __init__(self, primary_data: list[str]):
        super().__init__('added_annotations')
        self.target_annotation_ids = primary_data
    
    def reaction(self):
        deleted_annotations: list[Annotation] = []
        for annotation_id in self.target_annotation_ids:
            deleted_annotations += self.MAIN.remove_annotations(annotation_id, False)
        return deleted_annotations
    
    def __str__(self) -> str:
        return super().__str__()[-1] + f', {self.target_annotation_ids})'
#! Not documented
class DeletedAnnotations(BaseAction):
    def __init__(self, primary_data: list[Annotation]):
        super().__init__('deleted_annotations')
        self.deleted_annotations = primary_data
    
    def reaction(self):
        assert self.MAIN.cur_image is not None
        for annotation in self.deleted_annotations:
            self.MAIN.redraw_annotation(annotation.annotation_type, 
                                        annotation.annotation_id, 
                                        annotation.coords, 
                                        annotation.cat_id)
            self.MAIN.cur_image.store_annotation(annotation)
        return [ann.annotation_id for ann in self.deleted_annotations]
    
    def __str__(self) -> str:
        return super().__str__()[-1] + f', {'['+' | '.join(str(ann) for ann in self.deleted_annotations)+']'})'
#! Not documented
class EditedAnnotations(BaseAction):
    def __init__(self, primary_data: list[tuple[str, str, dict[str, str]]]):
        super().__init__('edited_annotations')
        self.annotation_data = primary_data
    
    def reaction(self):
        prev_data = []
        
        for ann_id, cat_id, metadata in self.annotation_data:
            prev_data += self.MAIN.edit_annotations([ann_id], cat_id, metadata, False)
        return prev_data
    
    def __str__(self) -> str:
        return super().__str__()[-1] + f', {self.annotation_data})'
#! Not documented
class AddedCategories(BaseAction):
    def __init__(self, primary_data: list[str]):
        super().__init__('added_categories')
        self.category_cat_ids = primary_data
    
    def reaction(self):
        reaction_data = self.SIDE.remove_categories(False, self.category_cat_ids, False)
        assert reaction_data is not None
        return reaction_data[0], NewAction(action_type='deleted_annotations', data=reaction_data[1])
    
    def __str__(self) -> str:
        return super().__str__()[-1] + f', {self.category_cat_ids})'
#! Not documented
class DeletedCategories(BaseAction):
    def __init__(self, primary_data: dict[str, tuple[Any]], secondary_data: Optional[DeletedAnnotations] = None):
        super().__init__('deleted_categories')
        self.categories_tags = primary_data
        self.secondary_data = secondary_data
    
    def __call__(self):
        if self.secondary_data is not None: self.secondary_data()
        return super().__call__()
    
    def reaction(self):
        for cat_id, data in self.categories_tags.items():
            self.SIDE.add_category(*data, cat_id)
        return list(self.categories_tags.keys())
    
    def __str__(self) -> str:
        return super().__str__()[-1] + f', {self.categories_tags}, {self.secondary_data})'
#! Not documented
class EditedCategories(BaseAction):
    def __init__(self, primary_data: tuple[str, ...]):
        super().__init__('edited_category')
        self.category_tags = primary_data
    
    def reaction(self):
        cat_id, cur_index, category_name, category_color, *_ = self.category_tags
        cur_index = int(cur_index)
        assert self.WINDOW.images[0] is not None
        cur_category = self.WINDOW.images[0].categories[cat_id]
        
        redo_action = tuple([cat_id] + [str(value) for value in cur_category.values()])
        item = self.SIDE.val_table.tag_has(cat_id)[0]
        
        # checking each value against the original and acting/updating when needed 
        if cur_index != cur_category['id']:
            self.WINDOW.images[0].categories[cat_id].update({'id': cur_index})
            self.SIDE.move_category(item, int(cur_index), False)
        if category_name != cur_category['name']:
            self.WINDOW.images[0].categories[cat_id].update({'name': category_name})
            values = self.SIDE.val_table.item(item, 'values')
            self.SIDE.val_table.item(item, values= [values[0], values[1], category_name, values[3], values[4]])
        if category_color != cur_category['hex']:
            self.WINDOW.images[0].categories[cat_id].update({'hex': category_color})
            self.SIDE.color_table.tag_configure(cat_id, background=category_color)
            item = self.SIDE.color_table.tag_has(cat_id)
            self.SIDE.color_table.item(item, tag=(cat_id, category_color)) # type: ignore
            self.MAIN.change_annotation_color(cat_id)
            
        self.SIDE.check_pos()
        
        return redo_action
    
    def __str__(self) -> str:
        return super().__str__()[-1] + f', {self.category_tags})'
#! Not documented
class MovedPage(BaseAction):
    def __init__(self, primary_data: int):
        super().__init__('moved_page')
        self.page_num = primary_data
    
    def reaction(self):
        assert self.MAIN.cur_image is not None
        cur_page = self.MAIN.cur_image.index
        self.MAIN.skip_image(self.page_num, False)
        return cur_page
    
    def __str__(self) -> str:
        return super().__str__()[-1] + f', {self.page_num})'

#! Not documented
class NewAction():
    def __new__(cls, action_type: _actionType, data: Any) -> Any:
        match action_type:
            case 'added_categories': obj = AddedCategories(data)
            case 'deleted_categories': obj = DeletedCategories(*data)
            case 'edited_category': obj = EditedCategories(data)
            case 'added_points': obj = AddedPoints(data)
            case 'deleted_points': obj = DeletedPoints(data)
            case 'finished_annotation': obj = FinishedAnnotation(data)
            case 'restarted_annotation': obj = RestartedAnnotation(data)
            case 'added_annotations': obj = AddedAnnotations(data)
            case 'deleted_annotations': obj = DeletedAnnotations(data)
            case 'edited_annotations': obj = EditedAnnotations(data)
            case 'moved_page': obj = MovedPage(data)
            case 'no_action':
                raise TypeError("No action type given")
            case _: 
                raise ProcessLookupError(f'No reverse action found for {action_type}')
            
        return obj

#! Not documented
class ActionStacks:
    def __init__(self, W, S, M, max_stack_size: int = 40):
        self.max_stack_size = max_stack_size
        self.__action_stack: list[BaseAction] = []
        self.__reaction_stack: list[BaseAction] = []
        
        BaseAction.set_interface_variables(W, S, M)
    
    def new_action(self, action_type: _actionType, *action_data: Any) -> None:
        self.__action_stack.append(NewAction(action_type=action_type, data=action_data))
    
    def activate_action(self) -> None:
        if len(self.__action_stack) == 0: return
        action = self.__action_stack.pop()
        reaction = action()
        self.__reaction_stack.append(reaction)
        self.trim_stacks()
    
    def activate_reaction(self) -> None:
        if len(self.__reaction_stack) == 0: return
        reaction = self.__reaction_stack.pop()
        action = reaction()
        self.__action_stack.append(action)
        self.trim_stacks()
    
    def trim_stacks(self, clear: bool = False) -> None:
        max_stack = 0 if clear else self.max_stack_size
        while len(self.__action_stack) > max_stack:
            del self.__action_stack[0]
        while len(self.__reaction_stack) > max_stack:
            del self.__reaction_stack[0]
    
    def __len__(self) -> int:
        return len(self.__action_stack)
    
    def action_str(self) -> str:
        return "[ " + '\n '.join([str(act) for act in self.__action_stack]) + "]"
    
    def reaction_str(self) -> str:
        return "[ " + '\n '.join([str(react) for react in self.__reaction_stack]) + "]"