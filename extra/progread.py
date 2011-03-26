#!/usr/bin/python

import os
import re
import sqlite3
import sys
import textwrap
import time
from htmlentitydefs import name2codepoint


def unescape(s):
    if isinstance(s, int):
        return s

    if s is None:
        return u''

    s = s.replace('<br/>', '\n')
    s = re.sub('<[^<]+?>', '', s)
    s = re.sub(r'&#(\d+);', lambda m: unichr(int(m.group(1))), s) 
    s = re.sub('&(%s);' % '|'.join(name2codepoint),
               lambda m: unichr(name2codepoint[m.group(1)]),
               s)
        
    return s

def termwidth():
    try:
        import fcntl
        import termios
        import struct
        h, w, hp, wp = struct.unpack('HHHH',
                                     fcntl.ioctl(0, termios.TIOCGWINSZ,
                                     struct.pack('HHHH', 0, 0, 0, 0)))
        return w
    except:
        pass

    try:
        h, w = os.popen('stty size', 'r').read().split()
        return int(w)
    except:
        pass

    return int(os.environ.get('COLUMNS', 80))

def display(thread, posts):
    w = termwidth() - 8
 
    print unescape(thread[1])
    print

    for post in posts:
        post = dict(zip(['_', 'id', 'name', 'email', 'trip', 'time', 'body'],
                        map(unescape, post)))
        try:
            post['time'] = time.ctime(post['time'])
        except:
            post['time'] = 'unknown time'

        print "%(id)d: %(name)s%(trip)s <%(email)s> at %(time)s" % post

        for line in post['body'].split('\n'):
            if line == '':
                print '    '

            for l in textwrap.wrap(re.sub('<[^<]+?>', '', line), w):
                print '    %s' % l

        print


usage = """\
\033[1mUSAGE\033[0m
    %s [\033[4mDB\033[0m] \033[4mTHREAD\033[0m [\033[4mPOST\033[0m...]

\033[1mARGUMENTS\033[0m
    \033[4mDB\033[0m
        SQLite3 database file produced by \033[1mprogscrape(1)\033[0m. (default: \033[7mprog.db\033[0m)

    \033[4mTHREAD\033[0m
        Numerical thread ID.

    \033[4mPOST\033[0m
        Single Post ID.
""" % sys.argv[0]

sys.argv = sys.argv[1:]

try:
    db = 'prog.db'
    try:
        int(sys.argv[0])
    except:
        db = sys.argv[0]
        sys.argv = sys.argv[1:]

    thread = int(sys.argv[0])
    sys.argv = sys.argv[1:]

    posts = map(int, sys.argv)

except:
    print usage
    sys.exit(1)

try:
    if not os.path.isfile(db):
        raise sqlite3.OperationalError("Penis.")

    conn = sqlite3.connect(db)
    c = conn.cursor()

    th = c.execute('select * from threads where thread = ?', [thread]).fetchone()
    if th is None:
        print 'Error: Invalid thread ID.'
        sys.exit(3)

    if posts != []:
        po = []
        for post in posts:
            po.append(c.execute('select * from posts where thread = ? and id = ?',
                                (thread, post)).fetchone())
    else:
        po = c.execute('select * from posts where thread = ?', [thread]).fetchall()

    display(th, po)

except sqlite3.OperationalError:
    print 'Error: Not a DB:', db
    sys.exit(2)
