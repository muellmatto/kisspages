#!/usr/bin/env python3

import flask, os, markdown

workingPath = os.path.dirname(os.path.realpath(__file__)) + '/content'

app = flask.Flask(__name__)

# TODO
## wir brauchen hier nen Baum! children array muss wieder voll mit dicts sein!!
# { 'path': [children] }
pageDict =  {x[0][len(workingPath)+1:] : {
                                            'children': x[1],
                                            'path': x[0]
                                         }
            for x in os.walk(workingPath)}


# alles in den ram!!!! XD
contentDict = {}
for title in pageDict:
    if title is not '':
        with open(  pageDict[title]['path'] + '/index.txt' ) as pageContent:
            pageDict[title]['title'] = pageContent.readline()[7:]
            contentDict[title] = pageContent.read()[9:]



# we need to get the subnavigation....
@app.route('/', defaults={'path': ''}, strict_slashes=False)
@app.route('/<path:path>', strict_slashes=False)
def page(path):
    if path == '':
        # if path is empty, load first page!
        path=list(pageDict['']['children'])[0]
    filePath = os.path.join(workingPath, path, 'index.txt')
    if os.path.isfile(filePath):
        return flask.render_template('page.html', 
                                        content=markdown.markdown(contentDict[path]),
                                        navigation=pageDict[''],
                                        subnavigation=pageDict[path.split('/')[0]],
                                        path=path,
                                        page=pageDict[path])
    else:
        return filePath + ' not found'



if __name__ == '__main__':
    app.run(debug=True, port=64006)



