#! /usr/bin/env python3

import sys
from setuptools import setup, find_packages
from distutils.util import convert_path
import codecs

with codecs.open('README.md', 'r', 'utf-8') as readme_f, \
    codecs.open(convert_path('mensa_ukon/version.py'), 'r', 'utf-8') as vf:

    needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
    pytest_runner = ['pytest-runner>=2.0,<3dev'] if needs_pytest else []

    # get version information without importing to circumvent dependency issues
    ns = {}
    exec(vf.read(), ns)

    setup(name='mensa-ukon',
          version=ns['__version__'],
          author='Manuel Hotz',
          author_email='manuel.hotz@uni-konstanz.de',
          description='Python library/bot to access the canteen plan of the Uni Konstanz.',
          long_description=readme_f.read(),
          url='https://github.com/enplotz/mensa_ukon',
          keywords='python canteen api wrapper bot',
          packages=find_packages(exclude=['tests*']),
          py_modules=['mensa', 'bot', 'settings'],
          entry_points={
              'console_scripts': [
                  'mensa = scripts.mensa_cli:meals',
                  'mensa_bot = scripts.bot:run_bot', # TODO Needs external .env file location... like in $HOME/.config/mensabot
              ]
          },
          setup_requires=pytest_runner,
          tests_require=['pytest'],
          # Not really sure how to keep in sync with Pipfile
          # see ongoing issue at: https://github.com/pypa/pipenv/issues/1263
          install_requires=['python-dotenv>=0.5.1', 'python-telegram-bot==6.0.1', 'pyyaml', 'lxml', 'cssselect', 'click', 'click-datetime', 'click-log', 'pendulum'],
          include_package_data=True,
          classifiers=[
              'Intended Audience :: Developers',
              'Operating System :: MacOS :: MacOS X',
              'Operating System :: GNU/Linux',
              'Programming Language :: Python',
              'Programming Language :: Python :: 3.5',
              'Programming Language :: Python :: 3.6',
              'Topic :: Information Retrieval',
              'Topic :: Utility',
          ]
    )
