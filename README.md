# Mensa UKON

[![Build Status](https://travis-ci.org/enplotz/mensa_ukon.svg?branch=master)](https://travis-ci.org/enplotz/mensa_ukon)

Inofficial library to access the canteen plan of the Uni Konstanz. Currently, it uses
 the endpoint that was used for the old canteen website, sooo beware of breaking functionality. 

## Install

The library depends on a couple of packages and is only tested with Python 3 (as I have no time for Python 2 stuff). 
For convenience the requirements are stored in a pip `requirements.txt` and parsed by the setuptools script.

```bash
python3 setup.py install
```

## Usage

The library can be used as is or through the script that gets installed.

```python
>>> import mensa_ukon
>>> mensa_ukon.get_meals('2016-02-22')
{'stammessen': ... }
```

Usage as a script:

```bash
$ mensa -d 2016-02-22 -f plain -i en
```

Help is available via the `-h` flag.

# Telegram Bot

Telegram bot for the canteen of the Uni Konstanz.

## Install

It is recommended that you use a *virtualenv* for the bot. The bot uses the same set of dependencies as the library
and is installed together with the core library.

```sh
mkvirtualenv -p /usr/local/bin/python3 mensa
python3 setup.py install
```

## Configure

The bot can (and has to) be configured in the file `.env`. A sample config file is provided as `.env-sample`.
 Filling in your Telegram Bot API Token is the minimum you have to configure.

## Run

```sh
workon mensa # to activate the virtualenv if it got deactivated
# activate mensa # for miniconda in fish
python bot.py
```

# TODO

- conda environment
- library to PyPi?
- subscription feature (daily meals for configured days of week)
- more tests
- script install for bot --> specify .env file b/c it does not get bundled and `settings.py` cannot find it then
