#!/usr/bin/env python3

from configparser import ConfigParser
from os import listdir
from os.path import realpath, relpath, isdir, isfile, dirname, join, splitext, split
from sys import exit

from flask import render_template, Flask, send_from_directory, abort, redirect, url_for
from markdown import markdown

# -----------------------------------------------------

app = Flask(__name__)

# -----------------------------------------------------
# CONSTANTS AND GLOBALS
# -----------------------------------------------------

WORKING_PATH = dirname(realpath(__file__))
CONTENT_PATH = join(WORKING_PATH, 'content')
PAGES_PATH = join(CONTENT_PATH, 'pages')
WORKS_PATH = join(CONTENT_PATH, 'works')
KISS_CONFIG_PATH = join( WORKING_PATH, 'kisspages.conf')
KISSPORT = None
ALLOWED_EXTENSIONS = None


# -----------------------------------------------------
# read config 
# -----------------------------------------------------


try:
    kiss_config = ConfigParser()
    kiss_config.read(KISS_CONFIG_PATH)
    Name = kiss_config['KISS']['admin']
    Password = kiss_config['KISS']['password']
    KISS_PORT = int(kiss_config['KISS']['port'])
    ALLOWED_EXTENSIONS = set(map(str.strip, kiss_config['KISS']['allowed_extensions'].split(',')))
    ALLOWED_EXTENSIONS.discard('')
    print(Name, Password)
except:
    print('please check configfile: ', KISS_CONFIG_PATH)
    exit(1)


# -----------------------------------------------------
# page and work functions
# -----------------------------------------------------

def build_content(path, content_type='page'):
    '''
    returns a dict with keys:
    "title", "html", "tags", "short" and "date"
    '''
    if content_type == 'page':
        PARENT_PATH = PAGES_PATH
    elif content_type == 'work':
        PARENT_PATH = WORKS_PATH
    file_path = join(PARENT_PATH, path, 'index.txt')
    with open(file_path) as file_content:
        page_title = file_content.readline()[7:]
        if content_type == 'works':
            page_tags = file_content.readline()[6:]
            page_tags = {tag.strip('\n').strip(' ') for tag in page_tags.split(',')}
            date = file_content.readline()[6:]
            short = file_content.readline()[7:]
        else:
            page_tags = set()
            date = ''
            short = ''
        html_content = markdown(file_content.read())
    return {'title': page_title, 'html': html_content, 'tags': page_tags, 'date': date, 'short': short}


def get_all_works():
    '''
    Return a dict with keys "list_of_works" and "set_of_tags"
    each element of "list_of_works" is a dict with keys:
    "title"(str), "html"(str/html), "tags"(set) and "url"
    '''
    all_works = []
    all_tags = set()
    for folder in sorted(listdir(WORKS_PATH)):
        try:
            with open(join(WORKS_PATH, folder, 'index.txt')) as file_content:
                page_title = file_content.readline()[7:]
                print(page_title)
                page_tags = file_content.readline()[6:]
                page_tags = {tag.strip('\n').strip(' ') for tag in page_tags.split(',')}
                date = file_content.readline()[6:]
                short = file_content.readline()[7:]
                html_content = markdown(file_content.read())
            all_tags.update(page_tags)
            all_works.append({
                'title': page_title.strip('\n'),
                'html': html_content,
                'tags': page_tags,
                'url': "/works/" + folder
            })
        except:
            print('there was a problem with', join(WORKS_PATH, folder))
    return {"list_of_works": all_works, "set_of_tags": all_tags}


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
        url = '/' + relpath(join(path ,folder) , PAGES_PATH) + '/'
        navigation.append({ 'url': url, 'name': page_title})
    return navigation


def build_backlinks(path):
    '''
    Returns a list of links pointing back to the  root
    '''
    def append_backlink(path):
        with open( join(PAGES_PATH, path, 'index.txt')) as file_content:
            page_title = file_content.readline()[7:]
            if path != '':
                url = '/' + path + '/'
            else:
                url = '/'
        return {'url': url, 'name': page_title}
    backlinks = []
    if path != "":
        backlinks.append(append_backlink(path))
    while len( path.rsplit(sep ='/', maxsplit=1) ) > 1:
        path = path.rsplit(sep ='/', maxsplit = 1)[0]
        backlinks.append(append_backlink(path))
    backlinks.append(append_backlink(''))
    backlinks.reverse()
    return backlinks


# -----------------------------------------------------
# flask routes
# -----------------------------------------------------

# WORKS // TODO
@app.route('/works', defaults={'work': ''}, strict_slashes=False)
@app.route('/works/<work>', strict_slashes = False)
def work(work):
    set_of_all_tags = get_all_works()['set_of_tags']
    subnavigation = [{ 'url': "/tag/"+tag, 'name': tag} for tag in set_of_all_tags]
    if work == '':
        return render_template('works.html',
                            works = get_all_works()['list_of_works'],
                            navigation = build_navigation(''),
                            subnavigation = subnavigation,
                            path = work,
                            backlinks = build_backlinks(''))
    return render_template('work.html',
                        content = build_content(work, content_type='work'),
                        navigation = build_navigation(''),
                        subnavigation = subnavigation,
                        path = work,
                        backlinks = build_backlinks(''))
    # return str( get_work(work))


@app.route('/tag', defaults={'tag': ''}, strict_slashes=False)
@app.route('/tag/<tag>', strict_slashes = False)
def tag(tag):
    works = get_all_works()
    if tag == '':
        return redirect(url_for('work'))
    else:
        subnavigation = [{ 'url': "/tag/"+tag, 'name': tag} for tag in works['set_of_tags']]
        return render_template('works.html',
                            works = [work for work in works['list_of_works'] if tag in work['tags']],
                            navigation = build_navigation(''),
                            subnavigation = subnavigation,
                            path = work,
                            backlinks = build_backlinks(''))


# PAGES, IMAGES and FILES
@app.route('/', defaults={'path': ''}, strict_slashes=False)
@app.route('/<path:path>', strict_slashes=False)
def page(path):
    print('requested:', path)
    if isfile(join(PAGES_PATH, path)) and splitext(path)[1].strip('.') in ALLOWED_EXTENSIONS:
        directory, filename = split(join(PAGES_PATH, path))
        return send_from_directory(directory, filename)
    try:
        return render_template('page.html',
                            content = build_content(path, content_type='page'),
                            navigation = build_navigation(''),
                            subnavigation = build_navigation(path),
                            path = path,
                            backlinks = build_backlinks(path))
    except:
        return abort(404)


if __name__ == '__main__':
    app.run(debug=True, port=KISS_PORT)



