# Mensa UKON

Inofficial library to access the canteen plan of the Uni Konstanz. 
It uses the endpoint that the official website's JavaScript uses, soooo...

# Install

The library depends on a couple of packages and is only tested with Python 3 (as I have no time for Python 2 stuff). 
For convenience they are mirrored in a pip file.

```bash
python3 setup.py install
```

# Usage

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

Help is available via `-h` flag.

# Telegram Bot

Telegram bot for the canteen of the Uni Konstanz.

## Install

It is recommended that you use a *virtualenv* for the bot.

```sh
mkvirtualenv -p /usr/local/bin/python3 mensa
pip install -r requirements.txt && pip install -r requirements-bot.txt
```

## Configure

The bot can (and has to) be configured in the file `.env`. A sample config file is provided as `.env-sample`.
 Filling in your Telegram Bot API Token is the minimum you have to configure.

## Run

```sh
workon mensa # to activate the virtualenv if it got deactivated
python bot.py
```

# TODO

- conda environment
- check that library install is correct
- library to PyPi?
- subscription feature (daily meals for configured days of week)
