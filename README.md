        __                        __                             
       / / __  _ __ ___   __ _   / /__  ___ _ __ __ _ _ __   ___ 
      / / '_ \| '__/ _ \ / _` | / / __|/ __| '__/ _` | '_ \ / _ \
     / /| |_) | | | (_) | (_| |/ /\__ \ (__| | | (_| | |_) |  __/
    /_/ | .__/|_|  \___/ \__, /_/ |___/\___|_|  \__,_| .__/ \___|
        |_|              |___/                       |_|         

/prog/scrape is a webscraper for world4ch's /prog/ textboard, though it should be compatible with any Shiichan board. It stores scraped content in an SQLite 3 database file.


## System requirements

/prog/scrape requires Python 2.5 or newer (but not Python 3.x) to run. If you're using Python 2.5, you will need to install the [`simplejson` module](http://pypi.python.org/pypi/simplejson/), if you haven't already. This is unnecessary for Python 2.6 or newer.

You will also need the [`requests`](http://pypi.python.org/pypi/requests/) library.

The optional progress bar requires a terminal which supports ANSI escape sequences. This includes most recent terminals and terminal emulators (post-1970s), but may not be supported on Windows.

If you want to use the database it creates, you will need [SQLite 3](http://sqlite.org/).


## Installation instructions

The only file you really need is `progscrape.py`. Everything else is optional. Just put it somewhere you can run it and that's that.

If you're using Bash and want auto-completion for command line options and database filenames, put `progscrape.sh` (or a symlink to it) in your `/etc/bash_completion.d/` folder, or source it in your `.bashrc`.

If you want a man page for /prog/scrape, put `progscrape.1` (or a symlink to it) somewhere in your MANPATH, possibly in `/usr/local/man/man1/`. Note that all of the information in the man page is also available by running /prog/scrape with the `-h` or `--help` command line argument.


## Usage

/prog/scrape doesn't have a GUI and never will, so run it from the command line.

If you just want to scrape world4ch's /prog/, you can run the script without any arguments (`./progscrape.py` or `python2.5 progscrape.py`, if you have several versions of Python installed). This will scrape the entire contents of /prog/ into an sqlite3 database named `prog.db`.

If you run /prog/scrape without any arguments (i.e., `./progscrape.py` or `python2.5 progscrape.py`, if you have several versions of Python installed), it scrapes world4ch's /prog/ through the JSON interface, dropping to the HTML interface to verify any ambiguous tripcodes it comes across. It puts the scraped content into a database called `prog.db`, and it also prints the thread IDs it's working on to standard out as it goes.

If this isn't what you want to do, you can pass it arguments to modify its behaviour. `./progscrape --help` (or the man page) will show you a complete list of options. If you prefer, you can also edit the source code directly; the relevant variables are all at the top of the script.

### Using the scraped content

When /prog/scrape is done scraping, the content will be in the aforementioned database. Open it with `sqlite3 prog.db` (or equivalent) and use `.schema` to see its schema. If you don't know any SQL, tutorials can be found all over the Internet and classes are offered at most institutes of higher education.

### Updating an existing database

Just run /prog/scrape again. It will compare the database to the board's `subject.txt` and only retrieve new posts.

### Caveats and miscellany

#### `--json`

By default, /prog/scrape uses the JSON interface. If you want to scrape Shiichan boards that aren't on world4ch, however, you will need to use the HTML interface, as the JSON interface is specific to world4ch.

#### `--verify-trips`

The JSON interface doesn't split up poster names, tripcodes, and e-mails into separate fields, so if the poster didn't use an e-mail address, it's not possible to tell the difference between someone who used a tripcode (that is, put `#tea` as his name) and someone who is faking one (put `!WokonZwxw2` literally). The HTML interface is unambiguous about these, so by default, /prog/scrape will use the HTML interface to figure out if an ambiguous tripcode is genuine or not. If you don't want it to do this, you can disable it. In that case, all ambiguous tripcodes are assumed to be fake.

#### SILENT!ABORN

When using the JSON interface, you may notice a lot of posts posted by SILENT!ABORN on timestamp 1234, with a body of "SILENT". These are deleted posts. If you are haunted by them, using `--no-aborn` will prevent them from being entered into the database, and they don't show up in the HTML interface at all.

#### `postcount.py`

This script looks at `subject.txt` and counts how many posts there should be. If you suspect your database is screwy, run it and compare that to the number of posts you have. Note that `subject.txt`'s tally includes deleted posts, so the script is fairly pointless if you aren't using the JSON interface. It takes optional `--base-url` and `--board` arguments, same as /prog/scrape.

#### `progread.py`

This script displays posts from your scraped database in plain text, if you enjoy that sort of thing. Run it without arguments to see the syntax.

#### `progsearch.py`

This script builds an index based a /prog/scrape database and lets you run search engine-style queries on it. It's nice if you don't need the power of SQL and want faster full-text search, but it does take up quite a bit of space and can take a long time to build the first time.

Once the index is built, you will need to instruct /prog/scrape itself to keep it up to date with the `--index` argument.

This requires the `Whoosh` module, which may be downloaded [here](http://bitbucket.org/mchaput/whoosh) or through pip or whatever.

## Bugs and feature requests

If you run into any difficulties which you think might be caused by a bug, or if there's some feature you would like to see added to /prog/scrape, either create a new issue on Github, or email **Xarn** at <cairnarvon@gmail.com>.
