# 🍴 Mensa UKON

[![Build Status](https://travis-ci.org/enplotz/mensa_ukon.svg?branch=master)](https://travis-ci.org/enplotz/mensa_ukon)

Inofficial library to access the canteen plan of the Uni Konstanz (and all other SZ canteens).
Currently, it uses the endpoint that was used for the old canteen website, sooo beware of breaking functionality.
The project also includes a *Telegram* bot that uses the library, see below for instructions.

## ⚙ Install

The library/bot depends on a couple of packages and is only tested with Python 3 (as I have no time for Python 2 stuff).
For convenience there exists an *Anaconda environment* specification that can be used to setup a virtualenv-equivalent
python environment (really just says how the env should be called and what python version should be used).
The *installation* requirements are stored in a pip-compatible `requirements.txt` (which are also parsed by the setuptools script,
so even a call with `python setup.py [...]` should install all dependencies).

```bash
# Locate source folder
$ cd mensa_ukon
# Environment creation (optional)
$ conda env create
$ source activate mensa-bot # or just: `activate mensa-bot` if you are using fish instead of bash
# Dependency and bot/script installation
$ pip install .
# ... which will install the dependencies of the package located in the current folder
```

### 🐍 Why not use conda for dependencies?

Currently, I do not know how I can use one `requirements.txt` for both pip/setuptools and conda.
The problem seems to be that not all PyPi packages are available as Anaconda packages and conda does not understand
how to read pip `requirements.txt` files.
I found a [hacky way](https://github.com/drivendata/cookiecutter-data-science/issues/14#issuecomment-214792960) of using
conda for available packages, but for this project there seem to be no benefits.

So--for now--Anaconda is relegated to create the environment while pip manages dependencies.


## 🎉 Library Usage

The library can be used as is or through the script that gets installed.

```python
>>> from mensa_ukon import Mensa
>>> m = Mensa()
>>> m.retrieve()
[(Location("mensa_giessberg", "Uni", "giessberg"), {...}), (Location("themenpark_abendessen", "Themenpark & Abendessen", "themenpark"), {...})]
```

A command-line script is automatically installed by setuptools:

```bash
$ mensa
```

Help is available via the `--help` flag.

## 🤖 Telegram Bot

The Telegram bot uses the library to access the canteen plan of the Uni Konstanz. It has several commands
(shown via `\help` command) to retrieve specific/all meals on different days of the week.

### ⚙ Install

It is recommended that you use a *virtualenv* for the bot. The bot uses the same set of dependencies as the library
and is automatically installed together with the core library.

### 🎛 Configure

The bot can (and has to) be configured in the file `.env`. A sample config file is provided as `.env-sample`.
Filling in your Telegram Bot API Token is the minimum you have to configure.
Be sure that the config file is located in the working directory of the bot, i.e.,
the directory where you will run the bot script.

## 🏃 Run

```sh
$ source activate mensa # to activate the environmet if it got deactivated
$ # activate mensa # for miniconda in fish
mensa_bot
```

You can see available command line arguments/options via the `--help` flag.

### Systemd

A simple template file for systemd is included: `etc/mensabot@.service`. 
Before you copy it, you have to read it!
Once you made sure the file looks to fit your needs, you have to place it (or symlink it) to
`/etc/systemd/system/mensabot@.service`. Then you can enable the service.

For example, to enable the unit for the user `ubuntu`, with a working directory of `/home/ubuntu/mensa_ukon` and the
executable installed to `/home/ubuntu/.local/bin/mensa_bot`:

```bash
$ systemctl enable mensabot@ubuntu.service
```

*NOTE*: Because of a (recently fixed) bug in systemd, expansions in `ExecStart` are not yet supported.
Currently, the path to the `mensa_bot` executable is hardcoded as `/home/ubuntu/.local/bin/mensa_bot`.

Then you can start/stop/restart the bot:
```bash
$ systemctl start mensabot@ubuntu
$ systemctl restart mensabot@ubuntu
$ systemctl stop mensabot@ubuntu
```

Logs are handled using `syslog` and can be retrieved by systemd's `journalctl`. You can use `journalctl -u mensabot@ubuntu` to read the logs.
`-f` sets the log to follow (like `tail -f`).



## 💻 Development

In order to reproduce a known working development environment, `pip freeze` is used.
Its (current) output is located in `requirements-dev.txt` and lists dependencies with specific version numbers.
This is also a reason we cannot currently use Anaconda conveniently for dependencies.

To develop, it is recommended to create a new virtual environment (conda, virtualenv, whatever), install dependencies
using the development pip file and installing the library in *editable* mode: `pip install -e .`.

### 🔍 Running tests

Tests are written using `pytest` and can be run by: `python setup.py test`. The test will automatically install
`pytest-runner` if it is not installed already.

Sadly, the library has not many tests for now 😢.

## 💪 TODO

- [ ] Library to PyPi?
- [ ] subscription feature (daily meals for configured days of week)
- [ ] more tests (investigate what tox & nose are for)
- [ ] simplify `_mensa_plan` method
- [x] script install for bot --> specify .env file b/c it does not get bundled and `settings.py` cannot find it then
- [x] Conda environment


### Revised Settings

```
Python 3.6.0 |Continuum Analytics, Inc.| (default, Dec 23 2016, 13:19:00)
[GCC 4.2.1 Compatible Apple LLVM 6.0 (clang-600.0.57)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> from mensa_ukon.mensabot import MensaBot
>>> b = MensaBot(None)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "[...]/mensa_ukon/mensa_ukon/mensabot.py", line 90, in __init__
    super(MensaBot, self).__init__(MensaBot._token())
  File "[...]/mensa_ukon/mensa_ukon/mensabot.py", line 85, in _token
    raise BotConfigurationError('Missing bot token.')
mensa_ukon.mensabot.BotConfigurationError: Error configuring bot: 'Missing bot token.'.
>>> from mensa_ukon import utils
>>> utils.load_from_dict({'PTB_TELEGRAM_BOT_TOKEN': 'TOKENTOKENTOKEN'})
>>> utils.reload_settings()
>>> b = MensaBot(None)
```
