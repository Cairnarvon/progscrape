#!/usr/bin/python

"""
This script examines subject.txt and figures out how many posts there
should be in total based on that.

If you're using progscrape with the HTML interface, the difference between
the number this script finds and the number of posts in your database
should be equal to the number of deleted posts.
If you're using the JSON interface, the two numbers should be the same (and
deleted posts will show up as SILENT!ABORN &c. as per the README).

You don't need to run this script yourself, but it's a nice first step to
verify database integrity.
"""

base_url = "http://dis.4chan.org"
board = '/prog/'


from sys import argv, exit
from getopt import getopt

try:
    optlist, args = getopt(argv[1:], 'h', ['base-url=', 'board='])
except:
    print "Invalid argument!"
    exit(1)

for (opt, arg) in optlist:
    if opt == '--base-url':
        if arg[-1] == '/':
            arg = arg[:-1]
        base_url = arg
    elif opt == '--board':
        if arg[-1] != '/':
            arg += '/'
        if arg[0] != '/':
            arg = '/' + arg
        board = arg

board_url = base_url + board


import urllib2, gzip, re, sys
from StringIO import StringIO

subjecttxt = urllib2.Request(board_url + "subject.txt")
subjecttxt.add_header('Accept-Encoding', 'gzip')
subjecttxt = urllib2.build_opener().open(subjecttxt)

if subjecttxt.headers.get('Content-Encoding') == 'gzip':
    subjecttxt = gzip.GzipFile(fileobj=StringIO(subjecttxt.read()))
 

regex = re.compile("^.*<>.*?<>.*?<>-?\d*<>(\d*)<>.*?<>\d*\\n$")

c = 0

for line in subjecttxt.readlines():
    m = regex.search(unicode(line, 'latin-1', 'ignore'))

    if m is not None:
        c += int(m.group(1))

    else:
        print >> sys.stderr, "subject.txt fail:", line

print c
