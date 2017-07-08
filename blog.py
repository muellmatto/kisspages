#!/usr/bin/env python3

from configparser import ConfigParser
from json import dumps as to_json, loads as from_json
from os import listdir, walk
from os.path import realpath, relpath, isdir, isfile, dirname, join, splitext, split
from sys import exit

from flask import render_template, Flask, send_from_directory, abort, redirect, request, url_for
import markdown
from redis import Redis

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
    redis_db_number = int(kiss_config['REDIS']['database'])
    if kiss_config['REDIS']['unixsocket'].upper() == 'TRUE':
        socket_path = kiss_config['REDIS']['SOCKETFILE']
    else:
        socket_path = None
    ALL_CONTENT = Redis(charset="utf-8", decode_responses=True ,db=redis_db_number, unix_socket_path=socket_path)
except:
    print('please check configfile: ', KISS_CONFIG_PATH)
    exit(1)


# -----------------------------------------------------
# page and work functions
# -----------------------------------------------------


def _build_content(path, content_type='page'):
    '''
    returns a dict with keys:
    "title", "html", "tags", "short", "path", "markdown_content" and "date"
    '''
    if content_type == 'page':
        PARENT_PATH = PAGES_PATH
        url = join('/', path)
    elif content_type == 'work':
        PARENT_PATH = WORKS_PATH
        url = join('/works', path)
    file_path = join(PARENT_PATH, path, 'index.txt')
    with open(file_path) as file_content:
        page_title = file_content.readline()[7:]
        page_tags = file_content.readline()[6:]
        #page_tags = {tag.strip('\n').strip(' ') for tag in page_tags.split(',')}
        date = file_content.readline()[6:]
        short = file_content.readline()[7:]
        markdown_content = file_content.read()
        html_content = markdown.markdown(markdown_content, ['markdown.extensions.extra'])
    return {'title': page_title, 'html': html_content, 'tags': page_tags, 'date': date, 'short': short, 'url': url, 'path': path, 'markdown_content': markdown_content}


def build_content(path, redis_object=None, content_type='page'):
    if redis_object is None:
        global ALL_CONTENT
        redis_object = ALL_CONTENT
    redis_key = join(content_type, path)
    print('++++++++build_content -> redis_key', redis_key)
    if not redis_key in redis_object:
        print('caching', redis_key)
        redis_object[redis_key] = to_json(_build_content(path, content_type))
    else:
        print('from cache:', redis_key)
    return from_json(redis_object[redis_key])


def set_content(path, content, content_type='page', new_path=None):
    redis_key = join(content_type, path)
    if content_type == 'page':
        PARENT_PATH = PAGES_PATH
    elif content_type == 'work':
        PARENT_PATH = WORKS_PATH
    file_path = join(PARENT_PATH, path, 'index.txt')
    with open(file_path, mode='w') as file_content:
        file_content.write('Title: ' + content['title'] + '\n')
        file_content.write('TAGS: ' + ','.join(content['tags']) + '\n')
        file_content.write('DATE: ' + content['date'] + '\n')
        file_content.write('SHORT: ' + content['short'] + '\n')
        file_content.writelines(content['markdown'])
    # temp hack until pyinotify...:
    global ALL_CONTENT
    ALL_CONTENT.delete(redis_key)


def _get_all_works():
    '''
    Return a dict with keys "list_of_works" and "set_of_tags"
    each element of "list_of_works" is a dict build from build_content():
    '''
    all_works = []
    all_tags = set()
    for folder in sorted(listdir(WORKS_PATH)):
        redis_key = join('work', folder)
        work = build_content(path=folder, content_type='work')
        tmp = work['tags'].split(',')
        tmp = set(map(str.strip , tmp))
        all_tags.update(tmp)
        all_works.append(work)
    return {"list_of_works": all_works, "set_of_tags": all_tags}

# new redis key : list of folders in worksdir
#
# temporary caching ... 
ALL_WORKS = None
def get_all_works():
    global ALL_WORKS
    if ALL_WORKS is None:
        print('caching works')
        ALL_WORKS = _get_all_works()
    return ALL_WORKS


#TODO navigation from redis-cache
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


def _build_redis_cache(redis_object):
    redis_object.flushdb()
    def read_all_files(redis_object, path, content_type):
        for folder, _, files in walk(path):
            if "index.txt" in files:
                _ = build_content(path=relpath(folder,path).rstrip('.'), redis_object=redis_object, content_type=content_type)
    read_all_files(redis_object, PAGES_PATH, 'page')
    read_all_files(redis_object, WORKS_PATH, 'work')


_build_redis_cache(ALL_CONTENT)

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
                        content = build_content(path=work, content_type='work'),
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


@app.route('/admin', defaults={'item': ''})
@app.route('/admin/<path:item>', methods=['POST', 'GET'])
def admin(item):
    if item == '':
        all_pages = [build_content(relpath(x[0],PAGES_PATH)) for x in walk(PAGES_PATH)]
        works = get_all_works()['list_of_works']
        return render_template('admin_dashboard.html', all_pages=all_pages, works=works) 
    if item.startswith('works'):
        item_type = 'work'
    else:
        item_type = 'page'
    if request.method == 'POST':
        #try:
        content = {i[0]: i[1][0] for i in dict(request.form).items()}
        content['tags'] = set(content['tags'].split(','))
        set_content(path=item, content=content, content_type=item_type, new_path=None)
        #except:
        #    return str(content)
    # return str(build_content(item))
    return render_template('admin_edit.html', content=build_content(path=item, content_type=item_type))


if __name__ == '__main__':
    app.run(debug=True, port=KISS_PORT)



