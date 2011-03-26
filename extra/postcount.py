#!/usr/bin/python

"""
This script examines subject.txt and figures out how many posts or threads or
both there should be in total based on that.

If you're using progscrape with the HTML interface or the JSON interface with
--no-aborn, the difference between the number this script finds and the number
of posts in your database should be equal to the number of deleted posts.
If you're using the JSON interface with --aborn (default), the two numbers should
be the same (and deleted posts will show up as SILENT!ABORN &c. as per the
README).

You don't need to run this script yourself, but it's a nice first step to
verify database integrity.
"""

base_url = "http://dis.4chan.org"
board = '/prog/'

mode = 0    # 0 = postcount, 1 = threadcount, 2 = both
verbose = False


import urllib2, gzip, re, sys
from getopt import getopt
from StringIO import StringIO


def usage():
    print "\033[1mUSAGE\033[0m"
    print "\t%s [\033[4mOPTION\033[0m...]" % sys.argv[0]
    print
    print "\033[1mOPTIONS\033[0m"
    print "\t\033[1m--base-url\033[0m \033[4murl\033[0m"
    print "\t\tSpecify base URL. (default: \033[7m%s\033[0m)" % base_url
    print 
    print "\t\033[1m--board\033[0m \033[4mboard\033[0m"
    print "\t\tSpecify board to examine. (default: \033[7m%s\033[0m)" % board
    print
    print "\t\033[1m--mode posts\033[0m|\033[1mthreads\033[0m|\033[1mboth\033[0m"
    print "\t\tSpecify which we should count (default: %s)" % ('posts',
                                                               'threads',
                                                               'both')[mode]
    print
    print "\t\033[1m--verbose\033[0m"
    print "\t\033[1m--no-verbose\033[0m"
    print "\t\tControl verbosity. (default: %s)" % ('no', 'yes')[verbose]
    print
    print "\t\033[1m-h\033[0m"
    print "\t\033[1m--help\033[0m"
    print "\t\tDisplay this message and exit."
    print


# Parse command line arguments

try:
    optlist, args = getopt(sys.argv[1:], 'h', ('base-url=', 'board=',
                                               'mode=', 'verbose', 'no-verbose',
                                               'help'))
except:
    print "Invalid argument!"
    usage()
    sys.exit(1)

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
    elif opt == '--mode':
        if arg in ('post', 'posts'):
            mode = 0
        elif arg in ('thread', 'threads'):
            mode = 1
        elif arg == 'both':
            mode = 2
        else:
            print >> sys.stderr, "Invalid option: --mode=\033[1m%s\033[0m" % arg
            sys.exit(1)
    elif opt == '--verbose':
        verbose = True
    elif opt == '--no-verbose':
        verbose = False
    elif opt in ('-h', '--help'):
        usage()
        sys.exit(0)

if base_url[:7] != 'http://':
    base_url = 'http://' + base_url

board_url = base_url + board


# Fetch subject.txt

subjecttxt = urllib2.Request(board_url + "subject.txt")
subjecttxt.add_header('Accept-Encoding', 'gzip')
subjecttxt = urllib2.build_opener().open(subjecttxt)

if subjecttxt.headers.get('Content-Encoding') == 'gzip':
    subjecttxt = gzip.GzipFile(fileobj=StringIO(subjecttxt.read()))

subjecttxt = subjecttxt.read().splitlines(True)


# Counting functions

def postcount():
    global subjecttxt

    regex = re.compile("^.*<>.*?<>.*?<>-?\d*<>(\d*)<>.*?<>\d*\\n$")

    posts = 0

    for line in subjecttxt:
        m = regex.search(unicode(line, 'latin-1', 'ignore'))

        if m is not None:
            posts += int(m.group(1))

        else:
            print >> sys.stderr, "subject.txt fail:", line

    return posts

def threadcount():
    global subjecttxt

    return len(subjecttxt)


# Show results

if not verbose:
    if mode == 0:
        print postcount()
    elif mode == 1:
        print threadcount()
    else:
        print postcount(), threadcount()

else:
    print "%s on %s has" % (board, base_url),

    if mode == 0:
        print postcount(), "posts."
    elif mode == 1:
        print threadcount(), "threads."
    else:
        print postcount(), "posts in", threadcount(), "threads."
