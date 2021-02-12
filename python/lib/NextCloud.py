# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import unicodedata
from lib import get_terminal_size, nxc_requester
import sys
import re
import os
import glob


class NextCloud():
    def __init__(self, endpoint, user, password):
        self.oc = nxc_requester.Client(endpoint)
        self.oc.login(user, password)
        self.tools = Tools()

    def make_dir(self, path, dir_name):
        if dir_name[0] == "/":
            print("can't use root path")
            return

        dir_name = f"{path}/{dir_name}"

        r = self.oc.mkdir(dir_name)
        if r == 405:
            print(f"{dir_name} is already exists")
            return
        
        if r == 409:
            print(f"mkdir: invalid path {dir_name}")
            return

        print(f"{dir_name} created")
        return

    def show_file_list(self, path, option_type = None):
        file_list = self.oc.file_list(path, 1)
        file_list = [{"name"         : x.get_name(),
                      "path"         : x.path,
                      "file_type"    : x.is_dir(),
                      "size"         : x.get_size(),
                      "last_modified": datetime.strftime(x.get_last_modified(), "%Y-%m-%d %H:%M")}
                      for x in file_list]
        
        [x.update({"file_type":"D", "size":"4096", "path":x["path"][:-1]}) if x["file_type"]
        else x.update({"file_type":"F", "size":str(round(x["size"]/1024, 2)) + "kb"})
        for x in file_list]
        
        if option_type == None or option_type.replace(" ", "") == "":
            file_list = [x["name"] for x in file_list]
            if not file_list: return
            # r = [x["href"].split("/")[-1] for x in r]
            self.tools.print_ls(file_list)
        elif option_type == "-l":
            for line in file_list:
                print(f"{line['file_type']} {line['size']: <9} {line['last_modified']}  {line['name']}")

        elif option_type == "no_show_result":
            return [x["name"] for x in file_list]

        elif option_type == "no_show_result_onlyfolder":
            return [x["name"] for x in file_list if x["file_type"] == "D"]

    def change_directory(self, path, des_path):
        origin_path = path
        origin_des_path = des_path
        stringWithList = []

        if   des_path == "." : return path
        elif des_path == "..": 
            if origin_path == "/고객사": print("your current dir is root"); return origin_path
            else: return "/" + "/".join(path[1:].split("/")[:-1])
        
        if des_path in ["/고객사", "/", "/고객사"]:
            return "/고객사"

        elif "/" == des_path[-1]:
            des_path = des_path[:-1]

        elif "./" == des_path[0:2]:
            des_path = des_path[2:]

        file_list = self.show_file_list(origin_path, "no_show_result_onlyfolder")
        find_startwith_string_result = self.tools.find_startwith_string(file_list, des_path)
        

        if not find_startwith_string_result:
            print(f"{origin_des_path}: no such file or directory")
            return origin_path
        
        return (path + "/" + find_startwith_string_result).replace("//", "/")

    def remove_files(self, path, rm_filename):
        stringWithList = []
        file_list = self.show_file_list(path, "no_show_result")
        if rm_filename == "*":
            for fileName2 in file_list:
                print("{} is moved to recycleBin".format(stringWithList[0]))
            return

        find_startwith_string_result = self.tools.find_startwith_string(file_list, rm_filename)
        if not find_startwith_string_result:
            print("{}: No such directory".format(find_startwith_string_result)); return
        self.oc.move(path + "/" + find_startwith_string_result, "/고객사/recycleBin/")
        print("{} is moved to recycleBin".format(find_startwith_string_result))

    def upload_files(self, path, upload_file_name):
        upload_file_name = upload_file_name.replace('"', "").replace("\\", "/")
        if os.path.isdir(upload_file_name):
            self.upload_folder_to_nas(path, upload_file_name)
            
        else:
            self.upload_file_to_nas(path, upload_file_name)
    
    def upload_file_to_nas(self, path, upload_file_name):
        upload_file_name_without_path = upload_file_name.split("/")[-1]
        file_list = self.show_file_list(path, "no_show_result")

        if upload_file_name_without_path in file_list:
            while True:
                is_overwrite = input(f"{upload_file_name_without_path} is already exists, overwrite it? y/n [default : y]")
                if is_overwrite == "y" or is_overwrite == "":
                    self.oc.put_file(path + "/" + upload_file_name_without_path, upload_file_name)
                    print(f"{upload_file_name_without_path} is uploaded")
                    return

                elif is_overwrite == "n":
                    print("")
                    return

        self.oc.put_file(path + "/" + upload_file_name_without_path, upload_file_name)
        print(f"{upload_file_name_without_path} is uploaded")
    
    def upload_folder_to_nas(self, path, folder_name):
        file_list_with_path = {}
        file_list_with_path[path] = self.show_file_list(path, "no_show_result")
        folder_name_without_path = folder_name.split("/")[-1]

        file_and_folder_list = glob.glob("{}\\**".format(folder_name), recursive=True)
        file_and_folder_list = [x.replace("\\", "/") for x in file_and_folder_list if x != folder_name + "\\"]

        self.make_dir(path, folder_name_without_path)

        for content in file_and_folder_list:
            if os.path.isdir(content):
                self.make_dir(path, folder_name_without_path + content.replace(folder_name, ""))

        for content in file_and_folder_list:
            if os.path.isfile(content):
                file_path = "/".join(content.replace(folder_name, "").split("/")[:-1])
                self.upload_file_to_nas(path + "/" + folder_name_without_path + file_path, content)

    def get_shared_link(self, path, file_name):
        is_exist = False
        string_with_list = []

        file_list = self.show_file_list(path, "no_show_result")

        find_startwith_string_result = self.tools.find_startwith_string(file_list, file_name)
        if not find_startwith_string_result:
            print("{}: No such directory".format(file_name)); return

        filePath = "{}/{}".format(path, find_startwith_string_result)
        print("create share link to {} file".format(find_startwith_string_result))
        password = input("input password : ")
        if not password:
            password = None
            
        result = self.oc.share_file_with_link(path + "/" + file_name, password=password)
        shared_link = result.get_link().replace("http://172.16.13.168:8888", "https://nas.appsu.it")

        print(f"{result.get_path()} is shared")
        print(f"url: {shared_link}")
        if password: print("pw:", password)
        

class Tools():
    def __init__(self):
        self.hangul = re.compile('[^\u3131-\u3163\uac00-\ud7a3]+')

    def preformat_cjk(self, string, width, align='<', fill=' '):
        count = (width - sum(1 + (unicodedata.east_asian_width(c) in "WF")
                            for c in string))
        return {
            '>': lambda s: fill * count + s,
            '<': lambda s: s + fill * count,
            '^': lambda s: fill
             * (count / 2)
                        + s
                        + fill * (count / 2 + count % 2)
                }[align](string)

    def change_datetype(self, input_datetime):
        """
        chagne datetype "Wed, 11 Mar 2020 04:32:46 GMT" to "2020-03-11 13:32"
        """
        input_datetime = " ".join(input_datetime.split(" ")[1:-1])
        input_datetime = datetime.strptime(input_datetime, "%d %b %Y %H:%M:%S")
        input_datetime += timedelta(hours = 9)
        input_datetime = datetime.strftime(input_datetime, "%Y-%m-%d %H:%M")

        return input_datetime

    def print_ls(self, input_list):
        (term_width, term_height) = get_terminal_size.get_terminal_size()

        repr_list = [repr(x).replace("'", "") for x in input_list]
        min_chars_between = 3 # a comma and two spaces
        usable_term_width = term_width - 3 # For '[ ' and ']' at beginning and end
        min_element_width = min( sum(1 + (unicodedata.east_asian_width(c) in "WF") for c in x) for x in repr_list ) + min_chars_between
        max_element_width = max( sum(1 + (unicodedata.east_asian_width(c) in "WF") for c in x) for x in repr_list ) + min_chars_between

        if max_element_width >= usable_term_width:
            ncol = 1
            col_widths = [1]
        else:
            # Start with max possible number of columns and reduce until it fits
            ncol = min( len(repr_list), usable_term_width // min_element_width  )
            while True:
                col_widths = [ max( sum(1 + (unicodedata.east_asian_width(c) in "WF") for c in x) + min_chars_between \
                                    for j, x in enumerate( repr_list ) if j % ncol == i ) \
                                    for i in range(ncol) ]
                if sum( col_widths ) <= usable_term_width: break
                else: ncol -= 1

        sys.stdout.write('')

        for i, x in enumerate(repr_list):
            if i != len(repr_list)-1: x += ''
            sys.stdout.write( x.ljust(col_widths[i %ncol] - len(self.hangul.sub('', x))))
            if i == len(repr_list) - 1:
                sys.stdout.write('\n')
            elif (i+1) % ncol == 0:
                sys.stdout.write('\n')

    def find_startwith_string(self, file_list, dst_file_name):
        startwith_string_list = []
        index_num = 0

        if len(file_list) == 0:
            return False
        
        for file_name in file_list:
            if dst_file_name.upper() == file_name.upper():
                return file_name
            elif file_name.upper().startswith(dst_file_name.upper()):
                startwith_string_list.append(file_name)

        if len(startwith_string_list) == 0:
            return False
        elif len(startwith_string_list) == 1:
            return startwith_string_list[0]
        
        for startwith_string in startwith_string_list:
            index_num += 1
            print(f"{index_num} : {startwith_string}")

        while True:
            input_num = input("select num : ")

            try: return startwith_string_list[int(input_num) - 1]
            except: return False
