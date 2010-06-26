# /prog/scrape

/prog/scrape is a scraper for world4ch's /prog/ textboard, though it should be compatible with any Shiichan board. It requires Python 2.5 or 2.6 to run.

If possible, /prog/scrape will use gzip encoding and the board's JSON interface. If you're using Python 2.5, you will need to install the [`simplejson` module](http://pypi.python.org/pypi/simplejson/), if you haven't already. This is unnecessary for Python 2.6.

## Usage

If you just want to scrape world4ch's /prog/, you can run the script directly (`./progscrape.py`, or `python2.5 progscrape.py` if you have several versions of Python installed). If you want to scrape any other textboard, you'll need to change at least the `prog_url`, `read_url`, and `json_url` variables. For other world4ch boards, just replace `prog` with the relevant board name in the string.

If you want to scrape a Shiichan board that isn't on world4ch, you won't be able to use the JSON interface, as that's specific to world4ch. Set `use_json` to `False`, unless you enjoy seeing the same error message every time you run the scraper. You may also do this if you want to force using the HTML interface on world4ch boards. You should be aware that this will be slower and probably more error-prone.

There's a problem with world4ch's JSON interface, in that it can't always tell if a tripcode is genuine (i.e. the user put `#tea` as his name) or not (i.e. he just put `!WokonZwxw2` literally). To solve this problem, /prog/scrape used to rely on the HTML interface. This no longer works, though, so now no attempt is made to verify ambiguous names, and all tripcodes used without an email address are assumed to be fake. If world4ch ever lifts its ban on allowing scrapers access to the HTML interface, or you have another Shiichan board with a JSON interface identical to world4ch's, you can get /prog/scrape to verify tripcodes anyway by setting `verify_trips` to `True`.

The scraped content will be placed in an `sqlite3` database named `prog.db`. If you want to change this, adjust the `db_name` variable. It may be a good idea to use an absolute path.

## Using the database

You will need [SQLite 3](http://sqlite.org/). Just open the database file using `sqlite3 prog.db`, and run your SQL queries. Use `.schema` to see the database schema; everything should be pretty obvious.

*JSON interface peculiarity:* deleted posts will show up as being posted by SILENT!ABORN on timestamp 1234, with a body of "SILENT". If you're using the HTML interface, they just won't show up at all.

## Bugs

If you run into any difficulties which you think might be caused by a bug, either create a new issue on Github, or email **Xarn** at <cairnarvon@gmail.com>.

If you're scraping /prog/, specifically, you will see the following error messages:

> `subject.txt fail: <a href="mailto:sage"> </a><><>1277494135<><> <>81.43.183.81<><><>1277476613<>327<><>1277496126`

> `subject.txt fail: Anonymous<><>1220909598<><a href="read/prog/1220718054/17">&gt;&gt;17</a><br/>Don't ask me, aniki.<> <>131.116.254.199<><><>1220718054<>6<><>1231185336`

These are not /prog/scrape bugs; they're Shiichan bugs, which /prog/scrape correctly reports. Learn to love it, because they're not going away. Other Shiichan boards likely have similar issues.
