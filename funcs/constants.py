import os, json
from sys import argv
from string import ascii_lowercase, ascii_uppercase, digits
from io import StringIO

EXECUTION_PATH = os.path.abspath(os.path.dirname(argv[0]))
FOLDER_PATHS = {
    'IMAGE': os.path.join(EXECUTION_PATH, 'assets', 'images'),
    'LOCALE': os.path.join(EXECUTION_PATH, 'assets', 'locale'),
    'MODELS': os.path.join(EXECUTION_PATH, 'assets', 'modelos'),
    'CONFIG': os.path.join(EXECUTION_PATH, 'config')
}
CONFIG_FILE_PATH = os.path.join(FOLDER_PATHS['CONFIG'], 'config.json')
if not os.path.isdir(FOLDER_PATHS['CONFIG']):
    os.mkdir(FOLDER_PATHS['CONFIG'])
if not os.path.isfile(CONFIG_FILE_PATH):
    CONFIG = {"lang_code": "en", 
              "recent": [],
              'theme': 'dark',
              'default_output': ''}
    with open(CONFIG_FILE_PATH, 'w') as file:
        json.dump(CONFIG, file)
else:
    with open(CONFIG_FILE_PATH, 'r') as file:
        CONFIG: dict = json.load(file)
    for path in CONFIG['recent'].copy():
        if not os.path.isfile(path): CONFIG['recent'].remove(path)
    if len(CONFIG['recent']) > 10: CONFIG['recent'] = CONFIG['recent'][-10:]

class Lang():
    def __init__(self, lang_code: str = 'ni', name: str = '', lines: dict[str, str] | None = None) -> None:
        self.lang_code = lang_code
        self.name = name
        self.lines = lines

class LogCatcher(StringIO):
    def clear(self) -> None:
        self.seek(0)
        self.truncate(0)
log_catcher = LogCatcher()
        
LANGUAGES = {}
LANG = Lang()
for path in os.listdir(FOLDER_PATHS['LOCALE']):
    with open(os.path.join(FOLDER_PATHS['LOCALE'], path), 'r') as file:
        lang_data = json.load(file)
    if list(lang_data.keys()) != ["lang_code", "name", "lines"]: continue
    if CONFIG['lang_code'] == lang_data['lang_code']: LANG = Lang(**lang_data)
    elif lang_data['lang_code'] == ':)' : continue
    LANGUAGES[lang_data['lang_code']] = lang_data['name']
if LANG.lang_code == 'ni': CONFIG['lang_code'] = 'en'

def translator(msg:str) -> str:
    if LANG.lang_code == 'ni': return msg
    return LANG.lines.get(msg, msg)
_ = translator

SHORTCUTS: list[tuple[str, str]] = [
    (_('Right Arrow / D'), _("Next Image")),
    (_('Left Arrow / A'), _("Previous Image")),
    (_('Double Click'), _("Mark Object")),
    (_('Scroll'), _("Switch classes")),
    ('Ctrl + Z', _("Undo")),
    ('Ctrl + Y', _("Redo")),
    ('Ctrl + S', _("Save")),
    ('Ctrl + Shift + S', _("Save as")),
    ('Ctrl + N', _("Load New")),
    ('Ctrl + Shift + N', _("Continue project"))
]

FORMATOS: list[str] = ['YOLOv8']

LETTERS1, LETTERS2 = ascii_lowercase+digits, ascii_uppercase+digits


