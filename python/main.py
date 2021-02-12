import sys
import os
from os.path import dirname
from os.path import join
from datetime import datetime
from urllib import parse

from lib import NextCloud

DEFAULT_PATH = "/"
COMMAND_LIST = """
    ls      : show file&directory list(option -l : show file type)
    pwd     : show current directory path
    cls     : clear command line
    cd      : change directory
    mkdir   : make directory
    rm      : remove directory
    upfile  : upload file in current current directory
    getlink : get file or folder shared link
    exit    : exit shell
    == $command today : input today's date, ex - mkdir today) ==
"""

SCRIPT_NIFO =  """
Welcome to nxc script 
"""

endpoint  = "https://127.0.0.1:8888"
user      = "$username"
password  = "$password"

def start_nas_api():
    nxc = NextCloud.NextCloud(endpoint, user, password)
    print(SCRIPT_NIFO)
    path = DEFAULT_PATH

    while True:
        try:
            command = input(f"se@nas:se~{path}$ ").split(" ", 1)
        except KeyboardInterrupt:
            print("^C")
            continue
        try:
            if command[0] == "today" or command[0] == "td": print(str("%d%02d%02d"%(datetime.today().year%100, datetime.today().month, datetime.today().day))); continue
            for i in range(len(command)):
                if command[i] == "today" or command[i] == "td": command[i] = str("%d%02d%02d"%(datetime.today().year%100, datetime.today().month, datetime.today().day))
            if   command[0] == ""       : pass
            elif command[0] == "ls"     : 
                if len(command) < 2     : nxc.show_file_list(path)
                else                    : nxc.show_file_list(path, command[1])
            elif command[0] == "help"   : print(COMMAND_LIST) 
            elif command[0] == "pwd"    : print(path)
            elif command[0] == "cls"    : os.system("cls")
            elif command[0] == "exit"   : break
            elif command[0] == "cd"     : path = nxc.change_directory(path, command[1])
            elif command[0] == "mkdir"  : nxc.make_dir(path, command[1])
            elif command[0] == "rm"     : nxc.remove_files(path, command[1])
            elif command[0] == "upfile" : nxc.upload_files(path, command[1])
            elif command[0] == "getlink": nxc.get_shared_link(path, command[1])
            else: print("{}: command not found".format(command[0]))
        except Exception as e:
            print("error :", e)

if __name__ == "__main__":
    start_nas_api()