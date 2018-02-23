# 🍴 Mensa UKON

[![Build Status](https://travis-ci.org/enplotz/mensa_ukon.svg?branch=master)](https://travis-ci.org/enplotz/mensa_ukon)

Inofficial *Telegram* bot to access the canteen plan of the Uni Konstanz (and all other SZ canteens).
Currently, it uses the endpoint that was used for the old canteen website, sooo beware of breaking functionality.
The project is structured into bot/command-line and library, so you can choose what you want to use.
Below you will find instructions on how to run/deploy the *bot* (it's primarily for me that I can remember where the heck I host the bot currently).

## ⚙ Install

The library/bot depends on a couple of packages and is only tested with Python `>=3.5`.
Currently the project uses [Pipenv](https://docs.pipenv.org) to manage dependencies (so, e.g. Heroku is able to install them automatically).
I'm currently in the process of streamlining installation and sync of requirements between `Pipfile` and `setup.py` (so that it can be distributed as a library). For now it is "synced" manually.

Anyway, make sure you are running at least Python 3.5.

```bash
# Locate source folder
$ cd mensa_ukon
# Install Pipenv (if you don't have already)
$ pip3 install pipenv
# Dependency and bot/script installation
$ pipenv install
# ... which will install the dependencies of the package located in the current folder
```

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

### 🎛 Configure

The bot can (and has to) be configured in the file `.env`. A sample config file is provided as `.env-sample`.
Be sure that this file is located in the working directory of the bot, i.e., the directory where you will run the bot script.
If you don't have such a file when running the bot, make sure that all variables you need are already defined in the environment! For example, use an external script to populate variables.
Filling in your Telegram Bot API Token is the minimum you have to configure.

## 🏃 Run

```sh
$ pipenv shell # to activate the environmet if it got deactivated
Loading .env environment variables…
Spawning environment shell (/usr/local/bin/bash). Use 'exit' to leave.
[...]
$ mensa_bot
```

You can see available command line arguments/options via the `--help` flag.

### 🚒 Systemd

A simple template file for systemd is included: `etc/mensabot@.service`. 
Before you copy it, you have to read it!
Once you made sure the file looks to fit your needs, you have to place it (or symlink it) to
`/etc/systemd/system/mensabot@.service`. Then you can enable the service.

For example, to enable the unit for the user `ubuntu`, with a working directory of `/home/ubuntu/mensa_ukon` and the
executable installed to `/home/ubuntu/.local/bin/mensa_bot`:

```bash
$ systemctl enable mensabot@ubuntu.service
```

Then you can start/stop/restart the bot:
```bash
$ systemctl start mensabot@ubuntu
$ systemctl restart mensabot@ubuntu
$ systemctl stop mensabot@ubuntu
```

Logs are handled using `syslog` and can be retrieved by systemd's `journalctl`. You can use `journalctl -u mensabot@ubuntu` to read the logs.
`-f` sets the log to follow (like `tail -f`).

### ☁️ Heroku

Heroku currently provides a *free tier* where the bot is able to run just fine.
Create an account and follow the [guide](https://devcenter.heroku.com/articles/getting-started-with-python) until "View Logs". 
Then your bot should already be able to reply to messages.

For example, after installing the [Heroku CLI](https://devcenter.heroku.com/articles/getting-started-with-python#set-up), to something like this:

```
$ cd mensa_bot
$ heroku login # do the login
$ heroku create # this also adds the correct remote for git
```

Now configure your `.env` file locally.
Then install [heroku-config](https://github.com/xavdid/heroku-config) plugin and push your config to your application.

```
$ heroku plugins:install heroku-config
$ heroku config:push
```

Now your app should be ready for the bot code:

```
$ git push heroku master
$ heroku ps:scale web=1
$ heroku logs -t
```


## 💻 Development 

Development libraries are specified in `Pipfile` under `[dev-packages]`.
If you want to develop either the library or the bot, 
simply run `pipenv install --dev` to install all dev and runtime dependencies.

### 🔍 Running tests

Tests are written using `pytest` and can be run by: `pipenv run python setup.py test`. The test will automatically install
`pytest-runner` if it is not installed already.

Sadly, the library has not many tests for now 😢.

## 💪 TODO

- [ ] Library to PyPi?
- [ ] subscription feature (daily meals for configured days of week)
- [ ] more tests (investigate what tox & nose are for)
- [ ] simplify `_mensa_plan` method
- [ ] development workflow up-to-date, c.f. [pypa/pipenv #1263](https://github.com/pypa/pipenv/issues/1263)
