# /prog/scrape

/prog/scrape is a scraper for world4ch's /prog/ textboard, though it should be compatible with any Shiichan board. It requires Python 2.5 or 2.6 to run.

If possible, /prog/scrape will use gzip encoding and the board's JSON interface. If you're using Python 2.5, you will need to install the [`simplejson` module](http://pypi.python.org/pypi/simplejson/), if you haven't already. This is unnecessary for Python 2.6.

## Usage

*The only file you really need is `progscrape.py`. Everything else is optional.*

If you just want to scrape world4ch's /prog/, you can run the script directly (`./progscrape.py`, or `python2.5 -u progscrape.py` if you have several versions of Python installed). If you want to scrape any other textboard, you'll need to change at least the `board` variable. If the board you want to scrape is not on world4ch, you will also need to change the `base_url` variable.

If you want to scrape a Shiichan board that isn't on world4ch, you won't be able to use the JSON interface, as that's specific to world4ch. Set `use_json` to `False`, unless you enjoy seeing the same error message every time you run the scraper. You may also do this if you want to force using the HTML interface on world4ch boards. You should be aware that this will be slower and probably more error-prone.

There's a problem with world4ch's JSON interface, in that it can't always tell if a tripcode is genuine (i.e. the user put `#tea` as his name) or not (i.e. he just put `!WokonZwxw2` literally). To solve this problem, /prog/scrape can use the HTML interface to verify ambiguous tripcodes. By default it doesn't, but if you want it to, set `verify_trips` to `True`. If you don't, it will be assumed that any ambiguous tripcode is fake.

The scraped content will be placed in an `sqlite3` database named `prog.db`. If you want to change this, adjust the `db_name` variable. It may be a good idea to use an absolute path.

Alternatively, you can also configure all of these things by passing certain command line arguments, which will always override the hardcoded configuration. To learn about these, just run the script with the `-h` or `--help` argument.

If you intend to run /prog/scrape a lot with varying options and are using bash (version 2.04 or up), `progscrape.sh` provides sensible auto-completion. Just put it in `/etc/bash_completion.d/`, append it to `/etc/bash_completion`, or source it in your `.bashrc`, depending on your system.

**Caveat:** trying to scrape all of /prog/ through the HTML interface or through the JSON interface with tripcode verification turned on will eventually trigger world4ch's anti-spam measures and temporarily give you a *403 Forbidden* error. This isn't a huge deal (it won't ban you from /prog/), and you can just continue scraping a few hours later, but that's the reason `verify_trips` defaults to `False`.

## Using the database

You will need [SQLite 3](http://sqlite.org/). Just open the database file using `sqlite3 prog.db`, and run your SQL queries. Use `.schema` to see the database schema; everything should be pretty obvious.

*JSON interface peculiarity:* deleted posts will show up as being posted by SILENT!ABORN on timestamp 1234, with a body of "SILENT". If you're using the HTML interface, they just won't show up at all.

## Bugs

If you run into any difficulties which you think might be caused by a bug, either create a new issue on Github, or email **Xarn** at <cairnarvon@gmail.com>.
