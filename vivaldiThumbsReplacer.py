#!/usr/bin/env python3

# Copyright 2016 Lars Grueter <github.com/larsgru>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import time
import shutil
import json
import sqlite3


# PATHs - edit only these!
# --------------------------------------------------------------------------- #
topSites_path = "Path to 'Top Sites' file"
bookmark_path = "Path to 'Bookmarks' file"

backup_path = "Path to Backup directory"
customThumbs_path = "Path to directory with thumbnails"
# --------------------------------------------------------------------------- #


def load_thumbs(dir_path):
    """
    Load custom thumbnails in specified directory and return as dictionary
    """
    thumbs = os.listdir(dir_path)
    return {x[0]: dir_path + "_".join(x)
            for x in [y.split("_") for y in thumbs]}


def recurser(recurse_val,bookmark_dict,updated,not_found,thumbnails):
    for val in recurse_val:
        # if 'children' tag not present then it is not a folder
        if not 'children' in val:
            key=val['id']
            bookmark_dict.update({key:val['name']})
            '''
                Replace thumbnails where thumbnail id matches bookmark id
            '''
            if key in thumbnails.keys():
                with open(thumbnails[key], "rb") as bfile:
                    pic = bfile.read()
                up_time = str(int(time.time()))
                sql = "INSERT OR REPLACE INTO thumbnails(thumbnail,url,url_rank,title,redirects,at_top,load_completed,last_updated,last_forced) VALUES(?,?,?,?,?,?,?,?,?)"
                cur.execute(sql, (
                    pic, "http://bookmark_thumbnail/" + str(key), '-1', '',
                    'http://bookmark_thumbnail/' + str(key), '1', '1', up_time, up_time))
                meta = {
                    'Thumbnail': 'chrome://thumb/' + 'http://bookmark_thumbnail/' + str(key) + "?" + up_time}
                val['meta_info'] = meta
                conn.commit()
                updated.append(key)
            else:
                not_found.append(key)

        else:
            # if it is a folder then recursing
            if len(val['children'])!=0:
                recurser(val['children'],bookmark_dict,updated,not_found,thumbnails)



def update_thumbs(bookmark_path,topSites_path, thumbnails):

    bookmark_dict={}
    updated = []
    not_found = []

    global conn,cur
    # open database
    conn = sqlite3.connect(topSites_path)
    cur = conn.cursor()

    with open(bookmark_path, encoding="UTF-8") as jfile:
        bookmarks = json.load(jfile)

    # access bookmark entries
    bookmarks_data = bookmarks["roots"]["bookmark_bar"]["children"]

    # checking if bookmark content is an Active speeddial or not
    for i in bookmarks_data:
        if 'meta_info' in i:
            if 'Speeddial' in i['meta_info']:
                if i['meta_info']['Speeddial'] == 'true':
                    recurser(i['children'],bookmark_dict,updated,not_found,thumbnails)

    conn.close()

    # Writing changes to bookmarks file
    with open(bookmark_path, 'w') as bmk:
        json.dump(bookmarks, bmk)

    # print results
    if updated:
        print("\nUpdated:")
        for key in updated:
            print("{}: {}".format(key, bookmark_dict[key]))
    if not_found:
        print("\nNot updated (no custom thumbnails found):")
        for key in not_found:
            print("{}: {}".format(key, bookmark_dict[key]))


def main():
    print("Python Script for replacing thumbnails in Vivaldi Speedial")
    input("\nWARNING: Please make sure that Vivaldi isn't running. Press 'Enter' to continue.")

    global backup_path, customThumbs_path
    if not backup_path[-1] in "/\\":
        backup_path += "/"
    if not customThumbs_path[-1] in "/\\":
        customThumbs_path += "/"

    # validate paths
    if not os.path.isfile(bookmark_path):
        print("\nERROR: Vivaldis bookmark file wasn't found under the path "
              "'{}'!".format(bookmark_path))
    elif not os.path.isfile(topSites_path):
        print("\nERROR: Vivaldis 'Top Sites' file wasn't found under the path "
              "'{}'!".format(topSites_path))
    elif not os.path.isdir(backup_path):
        print("\nERROR: '{}' is no valid directory!".format(backup_path))
    elif not os.path.isdir(customThumbs_path):
        print("\nERROR: '{}' is no valid directory!".format(customThumbs_path))

    # start script
    else:
        # load files
        custom_thumbnails = load_thumbs(customThumbs_path)

        # create backup
        shutil.copy(topSites_path, backup_path)
        shutil.copy(bookmark_path, backup_path)
        print("\nCreated backup of 'Top Sites' and 'Bookmarks' in '{}'".format(backup_path))

        update_thumbs(bookmark_path,topSites_path, custom_thumbnails)

    input("\nPress 'Enter' to exit.")
    exit()


if __name__ == "__main__":
    main()
