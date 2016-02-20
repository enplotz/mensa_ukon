#! /usr/bin/env python3

from distutils.core import setup

setup(name='mensa_ukon',
      version='0.1',
      description='Access the meal plan of the Uni Konstanz like a sane person.',
      author_email='manuel.hotz@uni-konstanz.de',
      py_modules=['mensa_ukon'],
      scripts=['mensa_ukon.py'],
      requires=['requests', 'beautifulsoup4'],
      )
