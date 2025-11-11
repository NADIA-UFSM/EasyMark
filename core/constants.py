import os, json
from sys import argv
from string import ascii_lowercase, ascii_uppercase, digits
from io import StringIO
from dataclasses import dataclass, asdict
from typing import Literal, NotRequired, TypeAlias, TypedDict

EXECUTION_PATH = os.path.abspath(os.path.dirname(argv[0]))

#* Fully documented
class FolderPaths:
    """Class to store the main paths used by the code.
    """
    IMAGE = os.path.join(EXECUTION_PATH, 'assets', 'images')
    LOCALE = os.path.join(EXECUTION_PATH, 'assets', 'locale')
    MODELS = os.path.join(EXECUTION_PATH, 'assets', 'modelos')
    CONFIG = os.path.join(EXECUTION_PATH, 'config')

FOLDER_PATHS = FolderPaths()

#* Fully documented
@dataclass
class Configs:
    """Class to store the configs.
    """
    lang_code: str
    theme: str
    default_output: str
    recent: list[str]
    dev_mode: bool
    
    def __init__(self, **kwargs):
        """Class to store the configs.
        """
        self.lang_code = kwargs.get('lang_code', 'en')
        self.theme = kwargs.get('theme', 'dark')
        self.default_output = kwargs.get('default_output', '')
        self.recent = kwargs.get('recent', [])
        self.dev_mode = kwargs.get('dev_mode', False)
        


CONFIG_FILE_PATH = os.path.join(FOLDER_PATHS.CONFIG, 'config.json')
if not os.path.isdir(FOLDER_PATHS.CONFIG):
    os.mkdir(FOLDER_PATHS.CONFIG)
if not os.path.isfile(CONFIG_FILE_PATH):
    CONFIG = Configs()
    with open(CONFIG_FILE_PATH, 'w') as file:
        json.dump(asdict(CONFIG), file)
else:
    with open(CONFIG_FILE_PATH, 'r') as file:
        try:
            CONFIG = Configs(**json.load(file))
        except json.decoder.JSONDecodeError:
            CONFIG = Configs()
    for path in CONFIG.recent.copy():
        if not os.path.isfile(path): CONFIG.recent.remove(path)
    if len(CONFIG.recent) > 10: CONFIG.recent = CONFIG.recent[-10:]

#* Fully documented
class Lang():
    """Class to store the currently-loaded translation."""
    def __init__(self, lang_code: str = 'ni', name: str = '', lines: dict[str, str] | None = None) -> None:
        """
            Class to store the currently-loaded translation.

        Args:
            lang_code (str, optional): Language code. Defaults to 'ni'.
            name (str, optional): Display name of the language. Defaults to ''.
            lines (dict[str, str] | None, optional): Dictionary containing the given translations. Defaults to None.
        """
        self.lang_code = lang_code
        self.name = name
        self.lines = lines if lines is not None else {} 

#* Fully documented
class LogCatcher(StringIO):
    """Class to catch and store pre-existing logs."""
    def __init__(self, *args) -> None:
        """Class to catch and store pre-existing logs."""
        super().__init__(*args)
        
    def clear(self) -> None:
        """Clears the catcher."""
        self.seek(0)
        self.truncate(0)
log_catcher = LogCatcher()
        
LANGUAGES = {}
LANG = Lang()
for path in os.listdir(FOLDER_PATHS.LOCALE):
    with open(os.path.join(FOLDER_PATHS.LOCALE, path), 'r') as file:
        lang_data = json.load(file)
    if list(lang_data.keys()) != ["lang_code", "name", "lines"]: continue
    if CONFIG.lang_code == lang_data['lang_code']: LANG = Lang(**lang_data)
    elif lang_data['lang_code'] == ':)' : continue
    LANGUAGES[lang_data['lang_code']] = lang_data['name']
if LANG.lang_code == 'ni': CONFIG.lang_code = 'en'

#* Fully documented
def translator(msg:str='') -> str:
    """Translates strings to their respective language counterparts. Returns the original string if non-existent."""
    if LANG.lang_code == 'ni': return msg
    return LANG.lines.get(msg, msg)
_ = translator

SHORTCUTS: list[tuple[str, str]] = [
    (_('Right Arrow / D'), _("Next Image")),
    (_('Left Arrow / A') , _("Previous Image")),
    (_('Double Click')   , _("Mark Object")),
    (_('Scroll')         , _("Switch classes")),
    ('Ctrl + Z'          , _("Undo")),
    ('Ctrl + Y'          , _("Redo")),
    ('Ctrl + S'          , _("Save")),
    ('Ctrl + Shift + S'  , _("Save as")),
    ('Ctrl + N'          , _("Load New")),
    ('Ctrl + Shift + N'  , _("Continue project"))
]

FORMATOS: list[str] = ['YOLOv8']

LETTERS1, LETTERS2 = ascii_lowercase+digits, ascii_uppercase+digits

