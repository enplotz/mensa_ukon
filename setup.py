#! /usr/bin/env python3

import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='mensa_ukon',
      version='0.3',
      description='Access the canteen plan of the Uni Konstanz like a sane person.',
      author_email='manuel.hotz@uni-konstanz.de',
      # py_modules=['mensa_ukon'],
      modules = ["mensa_ukon"],
      entry_points={
          'console_scripts': [
              'mensa = mensa_ukon:main'
          ]
      },
      requires=['requests', 'lxml', 'cssselect'],
      long_description=read('README.md'),
      classifiers=[
        'Environment :: MacOS X',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 3.5',
        'Topic :: Information Retrieval',
        'Topic :: Utility',
      ]
      )
