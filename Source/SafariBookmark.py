# -*- coding: utf-8 -*-
# @author = joslyn

import sys
import os
from workflow import Workflow
from biplist import *

bookmark_path = '~/Library/Safari/Bookmarks.plist'

bm_type = 'WebBookmarkType'
bm_type_dict = 'WebBookmarkTypeList'
bm_type_page = 'WebBookmarkTypeLeaf'
web_list = []
sub_list = []

SEARCH_TYPE_NORMAL = 0
SEARCH_TYPE_FOLDER = 1


def filter_plist(bm_folder):
    if bm_folder[bm_type] in [bm_type_dict, bm_type_page]:
        if 'Title' in bm_folder.keys():
            if bm_folder['Title'] != 'BookmarksMenu':
                return True
            else:
                return False
        else:
            return True
    else:
        return False


def adjust_folder_name_for(lst):
    temp_lst = []
    for bm_dir in lst:
        if bm_dir[1] == 'BookmarksBar':
            temp_lst.append((bm_dir[0], 'Favorite', u'个人收藏', bm_dir[3], bm_dir[4], bm_dir[5], bm_dir[6]))
        elif bm_dir[1] == 'com.apple.ReadingList':
            temp_lst.append((bm_dir[0], 'ReadingList', u'阅读列表', bm_dir[3], bm_dir[4], bm_dir[5], bm_dir[6]))
        else:
            temp_lst.append(bm_dir)
    else:
        return temp_lst


def get_sub_list(children, parent):
    for i, child in enumerate(children):
        sub_parent = child['Title'] if 'Title' in child.keys() else 'web'
        if child[bm_type] == bm_type_dict:
            sub_list.append(get_sub_from_dict(child, parent))
            get_sub_list(child['Children'], sub_parent)
        else:
            sub_list.append(get_sub_from_def(child, parent))
            web_list.append(get_sub_from_def(child))
    return list(set(web_list)), adjust_folder_name_for(sub_list)


def get_main_children():
    temp_list = []
    try:
        plist = readPlist(os.path.expanduser(bookmark_path))
        temp_list = list(filter(filter_plist, plist['Children']))

    except (InvalidPlistException, NotBinaryPlistException) as e:
        print("Not a plist:", e)
    return temp_list


def get_sub_from_def(child, parent=''):
    return child[bm_type], child['URIDictionary']['title'], child['URLString'],\
           child['URLString'], 'image/web.png', True, parent


def get_sub_from_dict(child, parent):
    return child[bm_type], child['Title'], None, child[bm_type], 'image/folder.png', False, parent


main_children = get_main_children()
all_web_list, all_sub_list = get_sub_list(main_children, 'top')
one_level_dir = list(filter(lambda x: x[6] == 'top', all_sub_list))


def main(wf):
    if len(wf.args):
        query = wf.args[0].lstrip()
        search_type = SEARCH_TYPE_FOLDER if query[:1] == '/' else SEARCH_TYPE_NORMAL
    else:
        search_type = SEARCH_TYPE_NORMAL
        query = None

    if query:
        if search_type == SEARCH_TYPE_NORMAL:
            main_plist = wf.filter(query, all_web_list, key=lambda x: x[1], max_results=12)
        else:
            query_folder = query.split('/')
            if len(query_folder) > 2:
                main_plist = filter(lambda x: x[6] == query_folder[:-1][-1], all_sub_list)
            else:
                main_plist = one_level_dir
            main_plist = wf.filter(query_folder[-1], main_plist, key=lambda x: x[1], max_results=12)
    else:
        main_plist = one_level_dir

    for item_type, title, subtitle, target, icon, valid, parent in main_plist:
        if search_type == SEARCH_TYPE_FOLDER:
            pro_query = query[:str(query).rfind('/')]
            tab_auto = u'{0}/{1}/'.format(pro_query, title)
            autocomplete = tab_auto if item_type == bm_type_dict else None
        else:
            autocomplete = None
        wf.add_item(title=title, subtitle=subtitle, arg=target, icon=icon, valid=valid,
                    autocomplete=autocomplete, copytext=subtitle)

    wf.send_feedback()


if __name__ == '__main__':
    update_settings = {u'github_slug': u'JoslynWu/Alfred-SafariBookmark'}
    wf = Workflow(update_settings=update_settings)
    sys.exit(wf.run(main))
