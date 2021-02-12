import json
import os

BASE_DATA    = "Windows Registry Editor Version 5.00\n"
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
BATFILE_PATH = "\\\\".join(CURRENT_PATH.split("\\")[:-1])
JSON_PATH    = CURRENT_PATH + "\\set.json"

with open(JSON_PATH) as read_json:
    data = json.load(read_json)
    MENU_NAME   = data["menu_name"]
    SCRIPT_NAME = data["script_name"]

add_menubar = f'[HKEY_CLASSES_ROOT\\Directory\\Background\\shell\\{MENU_NAME}\\command]\n' +\
              f'@="{BATFILE_PATH}\\\\{SCRIPT_NAME}"\n'

rm_menubar = f'[-HKEY_CLASSES_ROOT\\Directory\\Background\\shell\\{MENU_NAME}]'

with open(CURRENT_PATH + "\\add.reg", "w") as f:
    f.write(BASE_DATA + add_menubar)

with open(CURRENT_PATH + "\\rm.reg", "w") as f:
    f.write(BASE_DATA + rm_menubar)