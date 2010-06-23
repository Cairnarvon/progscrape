#!/usr/bin/python -u

# ``Constants''

db_name  = 'prog.db'
prog_url = 'http://dis.4chan.org/prog/'
read_url = 'http://dis.4chan.org/read/prog/'


# Make sure we're using a compatible version

from sys import version, exit

if version[0] != '2':
    print "Your version of Python is not supported at this time.",\
          "Please use Python 2.5 or 2.6."
    exit(1)


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

import urllib2, re, gzip
from StringIO import StringIO

print "Fetching subject.txt...",

def urlopen(url):
    req = urllib2.Request(url)
    req.add_header('Accept-Encoding', 'gzip')
    req = urllib2.build_opener().open(req)

    if req.headers.get('Content-Encoding') == 'gzip':
        return gzip.GzipFile(fileobj=StringIO(req.read()))
    else:
        return req

try:
    subjecttxt = urlopen(prog_url + 'subject.txt')
except:
    print "Can't find it! Exiting."
    raise

print "Got it."


# Parse each line, check with DB, keep a list of all threads to be updated

regex = re.compile(u"""
    ^(.*?)      # Subject
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
    parsed = regex.search(unicode(line,"utf-8"))
    try:
        data = parsed.groups()
        result = db.execute('SELECT last_post FROM threads WHERE thread = ?', (unicode(data[3]), )).fetchone()
        if result is None:
            db.execute('INSERT INTO threads VALUES (?, ?, ?)', (unicode(data[3]), unicode(data[0]), 0))
            to_update.append((unicode(data[3]), unicode(data[6])))
        elif int(result[0]) < int(data[6]):
            to_update.append((unicode(data[3]), unicode(data[6])))

    except:
        # Failed to parse line; skip it
        print "subject.txt fail:", line

print "%d threads to update." % len(to_update)


# Fetch new posts

from datetime import datetime

postregex = u"""<h3><span class="postnum"><a href='javascript:quote\((?P<id>\d+),"post1"\);'>(?P=id)</a> </span><span class="postinfo"><span class="namelabel"> Name: </span><span class="postername">(?P<author>.*?)</span><span class="postertrip">(?P<trip>.*?)</span> : <span class="posterdate">(?P<time>.*?)</span> <span class="id">[^<]*</span></span></h3>
<blockquote>
\t<p>
(?P<body>.*?)
\t</p>
"""
postregex = re.compile(postregex, re.DOTALL)

meiruregex = u'<a href="mailto:(?P<meiru>.*?)">(?P<rest>[^<]*)</a>'
meiruregex = re.compile(meiruregex)

for thread in to_update:
    print "Updating thread %s..." % thread[0]

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


print "All done!"
