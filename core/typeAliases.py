from typing import Literal, TypeAlias, TypedDict


AnnotationDataType: TypeAlias = tuple[str, list[float], Literal['bbox', 'obbox', 'poly', 'mark'], dict[str, str]]
ImageDataType: TypeAlias = dict[str, tuple[int, int] | AnnotationDataType]
class CategoryDataType(TypedDict):
    id: int
    name: str
    hex: str
    visible: bool
    
_annTypeGen: TypeAlias = Literal['bbox', 'obbox', 'poly', 'mark']
_actionType: TypeAlias = Literal['added_categories'   , 'deleted_categories'   , 'edited_category'   ,
                                 'added_points'       , 'deleted_points'       , 
                                 'finished_annotation', 'restarted_annotation', 
                                 'added_annotations'  , 'deleted_annotations'  , 'edited_annotations', 
                                 'moved_page']