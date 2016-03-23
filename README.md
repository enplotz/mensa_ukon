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

# Telegram bot

The project also contains a bot for Telegram. Have a look in the `mensa_bot` directory.
