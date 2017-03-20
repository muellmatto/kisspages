#!/usr/bin/env python3

# from flask import Flask, session, redirect, url_for, escape, request
import os


workingPath = os.path.dirname(os.path.realpath(__file__)) + '/content'



# tree = [x for x in os.walk(workingPath)]
tree = [x[0] for x in os.walk(workingPath)]

## rawTree := ( #depth , $relpath , [children)
rawTree = [ (x[0][len(workingPath):].count('/') , x[0][len(workingPath):], x[1]) for x in os.walk(workingPath)]
pageDict =  {x[0][len(workingPath):] : x[1]  for x in os.walk(workingPath)}

print(rawTree)


#maxDepth = 0
#for t in tree:
#    link = t[len(workingPath):]
#    linkDepth = link.count('/')
#    if linkDepth > maxDepth:
#        maxDepth=linkDepth
#
#for d in range(maxDepth + 1):
#    print('ebene : ' + str(d))
#    for t in tree:
#        link = t[len(workingPath):]
#        if link.count('/') == d:
#            print(link)
