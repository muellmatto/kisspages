#!/usr/bin/env python3

from os import listdir
from os.path import realpath, relpath, isdir, dirname, join

from flask import render_template, Flask
from markdown import markdown

WORKING_PATH = dirname(realpath(__file__))
CONTENT_PATH = join(WORKING_PATH, 'content')
PAGES_PATH = join(CONTENT_PATH, 'pages')
WORKS_PATH = join(CONTENT_PATH, 'works')

app = Flask(__name__)

# -------------------------------------------

def build_page_content(path, only_title=False):
    '''
    returns a dict with keys "title" and "html"
    '''
    file_path = join(PAGES_PATH, path, 'index.txt')
    with open(file_path) as file_content:
        page_title = file_content.readline()[7:]
        html_content = markdown(file_content.read()[9:])
    content = {'title': page_title, 'html': html_content}
    return content


def build_navigation(path):
    ''' 
    Returns a list of dicts, with keys "url" and "name"
    '''
    navigation = []
    path = join(PAGES_PATH, path)
    sub_folders = [folder for folder in listdir(path) if isdir(join(path, folder)) ]
    for folder in sub_folders:
        with open(join(path, folder, 'index.txt')) as file_content:
            page_title = file_content.readline()[7:]
        url = '/' + relpath(join(path ,folder) , PAGES_PATH)
        navigation.append({ 'url': url, 'name': page_title})
    return navigation


def build_backlinks(path):
    '''
    Returns a list of links pointing back to the  root
    '''
    def append_backlink(path):
        with open( join(PAGES_PATH, path, 'index.txt')) as file_content:
            page_title = file_content.readline()[7:]
        return {'url': '/' + path, 'name': page_title}
    backlinks = []
    backlinks.append(append_backlink(path))
    while len( path.rsplit(sep ='/', maxsplit=1) ) > 1:
        path = path.rsplit(sep ='/', maxsplit = 1)[0]
        backlinks.append(append_backlink(path))
    backlinks.reverse()
    return backlinks


# -------------------------------------------


# WORKS // TODO
@app.route('/works', defaults={'path': ''}, strict_slashes=False)
@app.route('/works/<path>', strict_slashes = False)
def work(path):
    return 'works: ' + path


# PAGES
@app.route('/', defaults={'path': ''}, strict_slashes=False)
@app.route('/<path:path>', strict_slashes=False)
def page(path):
    navigation = build_navigation('')
    backlinks = build_backlinks(path)
    try:
        subnavigation = build_navigation(path)
        content = build_page_content(path)
    except:
        try:
            path = [folder for folder in listdir(PAGES_PATH) if isdir(join(PAGES_PATH, folder)) ][0]
            subnavigation = build_navigation(path)
            content = build_page_content(path)
        except:
            return "404"
    return render_template('page.html', 
                            content = content,
                            navigation = navigation,
                            subnavigation = subnavigation,
                            path = path,
                            backlinks = backlinks)


if __name__ == '__main__':
    app.run(debug=True, port=64006)



