# Mensa UKON

Inofficial library to access the mensa plan of the Uni Konstanz. 
It uses the endpoint that the official website's JavaScript uses.

# Install

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
$ mensa_ukon.py -d 2016-02-22 -f fancy -i en
```

Help is available via `-h` flag.
