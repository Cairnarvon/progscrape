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
    parsed = regex.search(unicode(line,"iso-8859-1"))
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
        print "subjects.txt fail:", line

print "%d threads to update." % len(to_update)


# Fetch new posts

import time, datetime as dt

for thread in to_update:
    print "Updating thread %s..." % thread[0]

    try:
        page = urlopen(read_url + thread[0] + '/1-').read()
    except:
        print "Can't access %s! Exiting." % (read_url + thread[0])
        raise
    
    ids, authors, emails, trips, times, posts, starts, ends = [], [], [], [], [], [], [], []
    for a in enumerate(page):
        try:
            if a[1] == '<':
                if page[a[0] : a[0] + 22] == '<span class="postnum">':
                    i = 48
                    while page[a[0] + i] != ',':
                        i += 1
                    ids.append(page[a[0] + 48 : a[0] + i])
                if page[a[0] : a[0] + 25] == '<span class="postername">':
                    i = 25
                    while page[a[0] + i : a[0] + i + 7] != '</span>':
                        i += 1
                    auth = page[a[0] + 25 : a[0] + i]
                    if len(auth) > 1 and auth[:2] == '<a':
                        i = 16
                        while auth[i] != '"':
                            i += 1
                        emails.append(auth[16:i])
                        auth = auth[i + 2 : -4]
                    else:
                        emails.append('')
                    authors.append(auth)
                    
                elif page[a[0] : a[0] + 25] == '<span class="postertrip">':
                    i = 25
                    while page[a[0] + i] != '<':
                        i += 1
                    trips.append(page[a[0] + 25 : a[0] + i])
            
                elif page[a[0] : a[0] + 25] == '<span class="posterdate">':
                    i = 25
                    while page[a[0] + i] != '<':
                        i += 1
                
                    d = page[a[0] + 25 : a[0] + i]
                    d = int(time.mktime(dt.datetime(int(d[:4]),
                                                    int(d[5:7]),
                                                    int(d[8:10]),
                                                    int(d[11:13]),
                                                    int(d[14:16])).timetuple()))
                    times.append(d)
            
                elif page[a[0] : a[0] + 12] == '<blockquote>':
                    starts.append(a[0] + 18)
                
                elif page[a[0] : a[0] + 13] == '</blockquote>':
                    ends.append(a[0] - 7)
    
        except:
            print "! Broken post in thread %s" % thread[0]
            lens = map(len, [ids, authors, emails, trips, times, posts, starts, ends])
            minl = min(lens)
            if max(lens) != minl:
                for a in [ids, authors, emails, trips, times, posts, starts, ends]:
                    if len(a) > minl:
                        a = a[:-1]

    for i in xrange(len(starts)):
        posts.append(page[starts[i] : ends[i]])

    l = db.execute('SELECT MAX(time) FROM posts WHERE thread = ?', (unicode(thread[0]),)).fetchone()
    l = None if l == None else l[0]

    for a in zip(ids, authors, emails, trips, times, posts):
        if a[4] > l:
            b = [unicode(thread[0])]
            
            for y in a:
                if isinstance(y,str): b.append(unicode(y,"utf-8","replace"))
                else: b.append(y)
                               
            db.execute(u'INSERT INTO posts (thread, id, author, email, trip, time, body) VALUES (?, ?, ?, ?, ?, ?, ?)', b)
            
    db.execute(u'UPDATE threads SET last_post = ? WHERE thread = ?', (unicode(thread[1]), unicode(thread[0])))
    db_conn.commit()


print "All done!"
