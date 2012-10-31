#!/usr/bin/python

import argparse
import datetime
import os
import re
import sqlite3
import sys
import textwrap
import time
from htmlentitydefs import name2codepoint

import whoosh.fields
import whoosh.index
import whoosh.qparser

def build_index(db, idir):
    start = time.time()
    print 'Building index %s in %s... ' % (db, idir),
    sys.stdout.flush()

    schema = whoosh.fields.Schema(thread=whoosh.fields.STORED,
                                  post=whoosh.fields.STORED,
                                  author=whoosh.fields.STORED,
                                  trip=whoosh.fields.STORED,
                                  email=whoosh.fields.STORED,
                                  time=whoosh.fields.DATETIME(stored=True),
                                  body=whoosh.fields.TEXT(stored=True))
    ix = whoosh.index.create_in(idir, schema, indexname=db)
    writer = ix.writer()

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('select * from posts')

    tags = re.compile('<.*?>')

    for thread, post, author, email, trip, timestamp, body in cur:
        
        author = scrub(author)
        body = scrub(body)

        try:
            timestamp = float(timestamp)
        except:  # Shiichan is lovely.
            timestamp = 0.0
        timestamp = datetime.datetime.fromtimestamp(timestamp)

        writer.add_document(thread=thread, post=post,
                            author=author, trip=trip, email=email,
                            time=timestamp, body=body)

    writer.commit()
    conn.close()

    dt = int(time.time() - start)
    print 'done. (%dm%02ds)' % (dt / 60, dt % 60)

def scrub(s, regices=[re.compile('<.*?>'),
                      re.compile(r'&#(\d+);'),
                      re.compile('&(%s);' % '|'.join(name2codepoint))]):
    if s is None:
        return u''
    s = s.replace('<br/>', '\n')
    s = s.replace("<span class='quote'>", '> ')
    s = regices[0].sub('', s)
    s = regices[1].sub(lambda m: unichr(int(m.group(1))) \
                                 if int(m.group(1)) <= 0x10ffff \
                                 else m.group(0), s)
    s = regices[2].sub(lambda m: unichr(name2codepoint[m.group(1)]), s)
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
        'Build or search an index based on a /prog/scrape database. You ' +
        "need an index before you can search; if it doesn't exist, one will " +
        'be built. If one exists, it will not be updated automatically; ' +
        'direct /prog/scrape to do so while scraping.')
    parser.add_argument('-i', '--index', metavar='DIR', dest='idir',
                        help='directory in which to store the index')
    parser.add_argument('-l', '--limit', metavar='N', type=int, default=10,
                        help='return at most N results (default 10)')
    parser.add_argument('-r', '--reverse', action='store_true',
                        help='reverse the result set')
    parser.add_argument('-s', '--sort', choices=('rel', 'time'), default='rel',
                        help='sort result set by relevance or time')
    parser.add_argument('-u', '--url', default='http://dis.4chan.org/read/prog',
                        help='board url (default http://dis.4chan.org/read/prog)')
    parser.add_argument('db', help='/prog/scrape DB file')
    parser.add_argument('query', nargs=argparse.REMAINDER,
                        help='query to run against the index')
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print >>sys.stderr, "%s does not exist!" % args.db
        sys.exit(1)

    if args.idir is None:
        args.idir = args.db + '.index'

    if not os.path.exists(args.idir):
        os.mkdir(args.idir)

    # Build index if it doesn't exist, or update if asked.
    if not whoosh.index.exists_in(args.idir, indexname=args.db):
        build_index(args.db, args.idir)
    elif not args.query:
        print >>sys.stderr, 'Index for %s exists in %s.' % (args.db, args.idir)

    # If we're only building the index, we're done.
    if not args.query:
        sys.exit(0)

    ix = whoosh.index.open_dir(args.idir, indexname=args.db)
    with ix.searcher() as searcher:
        qparse = whoosh.qparser.QueryParser('body', ix.schema)
        query = qparse.parse(' '.join(args.query).decode('utf8'))

        w = termwidth() - 2
        twrap = textwrap.TextWrapper(width=w,
                                     initial_indent='  ',
                                     subsequent_indent='  ')
        qwrap = textwrap.TextWrapper(width=w,
                                     initial_indent='  ',
                                     subsequent_indent='  > ')

        for result in searcher.search(query,
                                      sortedby=args.sort if args.sort != 'rel' \
                                               else None,
                                      reverse=args.reverse,
                                      limit=args.limit):
            author = result['author']
            if result.get('trip', None):
                author += result['trip']
            if result.get('email', None):
                author += ' (%s)' % result['email']

            print '%s/%d/%d' % (args.url, result['thread'], result['post'])
            print '%s on %s:' % (author,
                                 result['time'].strftime('%F %H:%M:%S'))
            for line in result['body'].split('\n'):
                quote = len(line) > 1 and line[:2] == '> '
                print (qwrap if quote else twrap).fill(line)
            print
