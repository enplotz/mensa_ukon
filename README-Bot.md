# MensaUKONBot

Telegram bot for the canteen of the Uni Konstanz.

## Install

It is recommended that you use a *virtualenv* for the bot.

```sh
mkvirtualenv -p /usr/local/bin/python3 mensa
pip install -r mensa_bot/requirements.txt
```

## Configure

The bot can (and has to) be configured in the file `.env`. A sample config file is provided as `.env-sample`.
 Filling in your Telegram Bot API Token is the minimum you have to configure.

## Run

```sh
workon mensa # to activate the virtualenv if it got deactivated
python mensa_bot/bot.py
```
