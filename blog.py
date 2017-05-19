#!/usr/bin/env python3

from flask import render_template, Flask
from os import walk, listdir
from os.path import realpath, isfile, isdir, dirname, join, relpath
from markdown import markdown
from collections import OrderedDict

working_path = dirname(realpath(__file__)) + '/content'

app = Flask(__name__)

# TODO
# first page muss besser gerutet werden

def load_pages_into_dict():
    page_dict = {
            relpath(path, working_path) : 
                {'children': child_dirs, 'path': path}
                for path, child_dirs, child_files in walk(working_path)
                }
    return page_dict

page_dict = load_pages_into_dict()
print(page_dict.keys)

# alles in den ram!!!! XD
def load_content_into_dict():
    content_dict = {}
    for title in page_dict:
        if title is  '.':
            first_child = page_dict['.']['children'][0]
            file_path = page_dict[first_child]['path'] + '/index.txt'
        else:
            file_path = page_dict[title]['path'] + '/index.txt'
        try:
            with open(file_path) as pageContent:
                page_dict[title]['title'] = pageContent.readline()[7:]
                content_dict[title] = pageContent.read()[9:]
        except:
            pass
            # just go on, there is no page!
    return content_dict

content_dict = load_content_into_dict()

def build_page_content(path):
    file_path = join(working_path, path, 'index.txt')
    with open(file_path) as file_content:
        page_title = file_content.readline()[7:]
        html_content = markdown(file_content.read()[9:])
    content = {'title': page_title, 'html': html_content}
    return content


def build_navigation(path):
    navigation = []
    path = join('content',path)
    pages_folders = [folder for folder in listdir(path) if isdir(join(path, folder)) ]
    for folder in pages_folders:
        with open(join(path, folder, 'index.txt')) as file_content:
            page_title = file_content.readline()[7:]
        navigation.append({ 'url': '/'+folder, 'name': page_title})
    return navigation


# we need to get the subnavigation....
@app.route('/', defaults={'path': ''}, strict_slashes=False)
@app.route('/<path:path>', strict_slashes=False)
def page(path):
    if path == '':
        # load first Page
        path = [folder for folder in listdir('content') if isdir(join('content', folder)) ][0]
    navigation = build_navigation('')
    subnavigation = build_navigation(path)
    try:
        content = build_page_content(path),
        return render_template('page.html', 
                                        content=content[0],  # WTF [0] ??????
                                        navigation=navigation,
                                        subnavigation=subnavigation,
                                        path=path)
    except:
        return "404"


if __name__ == '__main__':
    app.run(debug=True, port=64006)



