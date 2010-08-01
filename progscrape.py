#!/usr/bin/python

# ``Constants''

db_name  = 'prog.db'
base_url = 'dis.4chan.org'
port     = 80
board    = '/prog/'

use_json = True
verify_trips = True

progress_bar = False


# Make sure we're using a compatible version

from sys import version_info, exit, argv, stdout

if version_info[0] != 2 or version_info[1] not in (5, 6):
    print "Your version of Python is not supported at this time.",\
          "Please use Python 2.5 or 2.6."
    exit(1)


# Parse command line arguments

from getopt import getopt

if '--help' in argv or '-h' in argv:
    print "\033[1mUSAGE\033[0m"
    print
    print "\t%s [ \033[4mOPTIONS\033[0m... ] [ \033[4mDB\033[0m ]" % argv[0]
    print
    print "\033[1mOPTIONS\033[0m"
    print
    print "\t\033[1m--json\033[0m"
    print "\t\tUse the JSON interface, if possible.", "(default)" if use_json else ""
    print
    print "\t\033[1m--html\033[0m"
    print "\t\033[1m--no-json\033[0m"
    print "\t\tUse the HTML interface.", "(default)" if not use_json else ""
    print
    print "\t\033[1m--verify-trips\033[0m"
    print "\t\033[1m--no-verify-trips\033[0m"
    print "\t\tWhen using JSON, whether or not to verify ambiguous tripcodes "
    print "\t\tthrough the HTML interface. (default: %s)" % ("no", "yes")[verify_trips]
    print
    print "\t\033[1m--no-html\033[0m"
    print "\t\tEquivalent to \033[1m--json --no-verify-trips\033[0m."
    print
    print "\t\033[1m--progress-bar\033[0m"
    print "\t\033[1m--no-progress-bar\033[0m"
    print "\t\tWhether to display an animated progress bar or the traditional "
    print "\t\tprogress report. (default: %s)" % ("no", "yes")[progress_bar]
    print
    print "\t\033[1m--base-url\033[0m \033[4murl\033[0m"
    print "\t\tSpecify base URL. (default: \033[7m%s\033[0m)" % base_url
    print
    print "\t\033[1m--port\033[0m \033[4mport\033[0m"
    print "\t\tSpecify the port the webserver is running on. (default: %d)" % port
    print
    print "\t\033[1m--board\033[0m \033[4mboard\033[0m"
    print "\t\tSpecify board to scrape. (default: \033[7m%s\033[0m)" % board
    print
    print "\t\033[1m--help\033[0m"
    print "\t\033[1m-h\033[0m"
    print "\t\tdisplay this message and exit"
    print

    exit(0)

try:
    optlist, args = getopt(argv[1:], 'h', ['json', 'html', 'no-html', 'no-json',
                                           'verify-trips', 'no-verify-trips',
                                           'progress-bar', 'no-progress-bar',
                                           'base-url=', 'port=', 'board=',
                                           'help'])
except:
    print "Invalid argument! Use \033[1m--help\033[0m for help."
    exit(1)

for (opt, arg) in optlist:
    if opt == '--json':
        use_json = True
    elif opt in ('--html', '--no-json'):
        use_json = False
    elif opt == '--no-html':
        use_json = True
        verify_trips = False
    elif opt == '--verify-trips':
        verify_trips = True
    elif opt == '--no-verify-trips':
        verify_trips = False
    elif opt == '--base-url':
        if arg[:7] == "http://":
            arg = arg[7:]
        base_url = arg
    elif opt == '--port':
        port = int(arg)
    elif opt == '--board':
        board = arg
    elif opt == '--progress-bar':
        progress_bar = True
    elif opt == '--no-progress-bar':
        progress_bar = False

if len(args) > 0:
    db_name = args[0]


if len(base_url) > 0 and base_url[-1] == '/':
    base_url = base_url[:-1]

if len(board) > 0:
    if board[-1] != '/':
        board += '/'
    if board[0] != '/':
        board = '/' + board

prog_url = board
read_url = "/read" + board
json_url = "/json" + board


# Set up the database connection first

import sqlite3

db_conn = sqlite3.connect(db_name)
db = db_conn.cursor()

try:
    db.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            thread INTEGER PRIMARY KEY,
            title TEXT,
            last_post INTEGER
        )""")
    db.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            thread INTEGER REFERENCES threads(thread),
            id INTEGER,
            author TEXT,
            email TEXT,
            trip TEXT,
            time INTEGER,
            body TEXT,
            PRIMARY KEY (thread, id)
        )""")
    db_conn.commit()
    
except sqlite3.DatabaseError:
    # Specified DB file exists, but isn't an SQLite DB file.
    print "Use a different filename for your DB."
    raise


# Try to fetch subject.txt

import httplib, re, gzip
from StringIO import StringIO

print "Fetching subject.txt...",
stdout.flush()

def urlopen(url, con=[None]):
    if con[0] is None:
        con[0] = httplib.HTTPConnection(base_url, port)

    con[0].request('GET', url, headers={'User-Agent': 'progscrape/1.1',
                                        'Accept-Encoding': 'gzip'})
    resp = con[0].getresponse()

    if resp.getheader('Content-Encoding') == 'gzip':
        return gzip.GzipFile(fileobj=StringIO(resp.read()))
    else:
        return resp

try:
    subjecttxt = urlopen(prog_url + 'subject.txt')
except:
    print "Can't find it! Exiting."
    raise

print "Got it."


# Parse each line, check with DB, keep a list of all threads to be updated

regex = re.compile(u"""
    ^(.*)       # Subject
    <>
    (.*?)       # Name
    <>
    (.*?)       # E-mail
    <>
    (-?\d*)     # Time posted/thread ID
    <>
    (\d*)       # Number of replies
    <>
    (.*?)       # ???
    <>
    (\d*)       # Time of last post
    \\n$""", re.VERBOSE)
to_update = []

for line in subjecttxt.readlines():
    line = unicode(line, "latin-1")

    try:
        parsed = regex.match(line)

        data = map(lambda s: s.encode('latin-1').decode('utf-8', 'replace'),
                   parsed.groups())

        result = db.execute('SELECT last_post FROM threads WHERE thread = ?',
                            (data[3],)).fetchone()

        if result is None:
            db.execute('INSERT INTO threads VALUES (?, ?, ?)',
                       (data[3], data[0], 0))
            to_update.append((data[3], data[6]))

        elif int(result[0]) < int(data[6]):
            to_update.append((data[3], data[6]))

    except:
        # Failed to parse line; skip it
        print "subject.txt fail:", line

tot = len(to_update)

print "%d threads to update." % tot


# Fetch new posts

from datetime import datetime

def show_progress(idx, tot):
    perc = idx * 100.0 / tot
    bars = "".join(map(lambda i: '#' if i <= perc else ' ', range(5, 101, 5)))

    print '\033[1AScraping... [%s] %.2f%% (%d/%d)' % (bars, perc, idx, tot)

if tot > 0 and use_json:
    if version_info[1] == 6:
        import json

    else:
        try:
            import simplejson as json

        except ImportError:
            print "Couldn't load simplejson! Using HTML interface."
            use_json = False

    try:
        json_test = urlopen(json_url + to_update[0][0])

    except:
        print "Can't access JSON interface! Using HTML interface."
        use_json = False

idx = 1

if progress_bar:
    print


if use_json:    # JSON interface

    # Tripcode and email, but no name
    name1 = u'^!<a href="mailto:(?P<meiru>[^"]*)">(?P<trip>![a-zA-Z./]{10}(?:![a-zA-Z+/]{15})?)</a>$'
    name1 = re.compile(name1, re.DOTALL)

    # Email and name, optional tripcode
    name2 = u'^<a href="mailto:(?P<meiru>[^"]*)">(?P<name>[^<]*)</a>(?P<trip>![a-zA-Z./]{10}(?:![a-zA-Z+/]{15})?)?$'
    name2 = re.compile(name2, re.DOTALL)

    # Anything without email (ambiguous)
    name3 = u'^(?P<name>.*)$'
    name3 = re.compile(name3, re.DOTALL)

    htripregex = u'<h3><span class="postnum"><a href=\'javascript:quote\(%s,"post1"\);\'>%s</a> </span><span class="postinfo"><span class="namelabel"> Name: </span><span class="postername">(?P<author>.*?)</span><span class="postertrip">(?P<trip>.*?)</span> : <span class="posterdate">[^<]*</span> <span class="id">.*?</span></span></h3>'

    for thread in to_update:
        if progress_bar:
            show_progress(idx, tot)
        else:
            print "[%d/%d] Updating thread %s..." % (idx, tot, thread[0])
        idx += 1

        l = db.execute('SELECT MAX(id) FROM posts WHERE thread = ?',
                       (thread[0],)).fetchone()
        l = 1 if l[0] == None else (int(l[0]) + 1)

        try:
            page = urlopen(json_url + thread[0] + '/%d-' % l).read()
        except:
            print "Can't access %s! Exiting." % (json_url + thread[0])
            raise

        page = json.loads(page)


        # Parse names, because the JSON interface sucks

        tripv, hp = [], None

        for post in page:
            p = page[post]

            if p['name'] is None: p['name'] = u''

            m = name1.match(p['name'])

            if m is not None:
                for n in ('meiru', 'trip'):
                    p[n] = m.group(n)

                p['name'] = u''

            else:
                m = name2.match(p['name'])

                if m is not None:
                    for n in ('meiru', 'trip', 'name'):
                        p[n] = m.group(n)

                else:
                    m = name3.match(p['name'])

                    if m is not None:
                        for n in ('meiru', 'trip'):
                            p[n] = u''

                        if u'!' in p['name']:
                            if p['name'] == u'SILENT!ABORN' and \
                               p['com'] == u'SILENT' and \
                               p['now'] == u'1234':
                                # Deleted post
                                pass

                            else:
                                tripv.append(post)


        if verify_trips and len(tripv) > 0:
            tripv_url = read_url + thread[0] + '/'
            if len(tripv) < 200:
                tripv_url += ','.join(tripv)
            try:
                hp = urlopen(tripv_url)

            except:
                print "Couldn't access HTML interface to verify tripcodes.",\
                      "Exiting."
                raise

            hp = hp.read()


        # Verify trips if needed, insert data

        for post in page:
            p = page[post]

            if verify_trips and post in tripv:
                htripper = re.compile(htripregex % (post, post), re.DOTALL)
                m = htripper.search(hp)

                if m is None:
                    print "Malformed post header! Exiting."
                    print read_url + thread[0] + '/' + post
                    exit(1)

                else:
                    p['name'], p['trip'] = m.group('author'), m.group('trip')

            db.execute(u'INSERT INTO posts (thread, id, author, email, trip, time, body) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (thread[0], post, p['name'], p['meiru'], p['trip'], p['now'], p['com']))

        db.execute(u'UPDATE threads SET last_post = ? WHERE thread = ?',
                   (unicode(thread[1]), unicode(thread[0])))
        db_conn.commit()


else:           # HTML interface

    postregex = u"""\
<h3><span class="postnum"><a href='javascript:quote\((?P<id>\d+),"post1"\);'>(?P=id)</a> </span><span class="postinfo"><span class="namelabel"> Name: </span><span class="postername">(?P<author>.*?)</span><span class="postertrip">(?P<trip>.*?)</span> : <span class="posterdate">(?P<time>.*?)</span> <span class="id">.*?</span></span></h3>
<blockquote>
\t(?:<div class="aa">)?<p>
(?P<body>.*?)
\t</p>(?:</div>)?
"""
    postregex = re.compile(postregex, re.DOTALL)

    meiruregex = u'<a href="mailto:(?P<meiru>.*?)">(?P<rest>[^<]*)</a>'
    meiruregex = re.compile(meiruregex)

    for thread in to_update:
        if progress_bar:
            show_progress(idx, tot)
        else:
            print "[%d/%d] Updating thread %s..." % (idx, tot, thread[0])
        idx += 1

        l = db.execute('SELECT MAX(id) FROM posts WHERE thread = ?',
                       (thread[0],)).fetchone()
        l = 1 if l[0] == None else (int(l[0]) + 1)

        try:
            page = urlopen(read_url + thread[0] + '/%d-' % l).read()
        except:
            print "Can't access %s! Exiting." % (read_url + thread[0])
            raise
    
        ids, authors, emails, trips, times, posts = [], [], [], [], [], []

        erred = False

        for p in re.split('</blockquote>', unicode(page, 'utf-8', 'ignore')):
            m = postregex.search(p)
            if m is None:
                if erred:
                    print "! Broken post in thread %s" % thread[0]
                erred = True
                continue

            ids.append(m.group('id'))

            meiru = False
            mm = meiruregex.match(m.group('author'))
            if mm is not None:
                authors.append(mm.group('rest'))
                emails.append(mm.group('meiru'))
                meiru = True
            else:
                authors.append(m.group('author'))

            mm = meiruregex.match(m.group('trip'))
            if not meiru and mm is not None:
                trips.append(mm.group('rest'))
                emails.append(mm.group('meiru'))
                meiru = True
            else:
                trips.append(m.group('trip'))

            if not meiru:
                emails.append('')

            times.append(datetime.strptime(m.group('time'),
                                           "%Y-%m-%d %H:%M").strftime("%s"))

            posts.append(m.group('body'))
    
        for post in zip(ids, authors, emails, trips, times, posts):
            if int(post[0]) >= l:
                b = [unicode(thread[0])]
                
                for y in post:
                    if isinstance(y,str): b.append(unicode(y,"utf-8","replace"))
                    else: b.append(y)
                
                db.execute(u'INSERT INTO posts (thread, id, author, email, trip, time, body) VALUES (?, ?, ?, ?, ?, ?, ?)', b)
            
        db.execute(u'UPDATE threads SET last_post = ? WHERE thread = ?',
                   (unicode(thread[1]), unicode(thread[0])))
        db_conn.commit()


try:
    urlopen.func_defaults[0][0].close()
except:
    pass

print "All done!"
