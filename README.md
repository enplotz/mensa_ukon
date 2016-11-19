# 🍴 Mensa UKON

[![Build Status](https://travis-ci.org/enplotz/mensa_ukon.svg?branch=master)](https://travis-ci.org/enplotz/mensa_ukon)

Inofficial library to access the canteen plan of the Uni Konstanz (and all other SZ canteens). Currently, it uses
 the endpoint that was used for the old canteen website, sooo beware of breaking functionality.

## ⚙ Install

The library depends on a couple of packages and is only tested with Python 3 (as I have no time for Python 2 stuff).
For convenience the requirements are stored in a pip `requirements.txt` and parsed by the setuptools script.
So even a call with `python3 setup.py [...]` should install all dependencies.

```bash
python3 setup.py install
```

## 🎉 Usage

The library can be used as is or through the script that gets installed.

```python
>>> from mensa_ukon import Mensa
>>> m = Mensa()
>>> m.retrieve()
[(Location("mensa_giessberg", "Uni", "giessberg"), {...}), (Location("themenpark_abendessen", "Themenpark & Abendessen", "themenpark"), {...})]
```

A script is automatically installed by setuptools:

```bash
$ mensa
```

Help is available via the `--help` flag.

# 🤖 Telegram Bot

Telegram bot for the canteen of the Uni Konstanz (or all other SZ canteens).

## ⚙ Install

It is recommended that you use a *virtualenv* for the bot. The bot uses the same set of dependencies as the library
and is installed together with the core library.

```sh
mkvirtualenv -p /usr/local/bin/python3 mensa
python3 setup.py install
```

## 🎛 Configure

The bot can (and has to) be configured in the file `.env`. A sample config file is provided as `.env-sample`.
Filling in your Telegram Bot API Token is the minimum you have to configure.
Be sure that the config file is located in the working directory of the bot, i.e., the directory where you will run the bot script.

## 🏃 Run

```sh
workon mensa # to activate the virtualenv if it got deactivated
# activate mensa # for miniconda in fish
mensa_bot
```

You can see available command line arguments/options via the `--help` flag.

# 💪 TODO

- [ ] Conda environment
- [ ] Library to PyPi?
- [ ] subscription feature (daily meals for configured days of week)
- [ ] more tests (investigate what tox & nose are for)
- [x] script install for bot --> specify .env file b/c it does not get bundled and `settings.py` cannot find it then
