#! /usr/bin/env python3

import sys
from setuptools import setup, find_packages
from distutils.util import convert_path
import codecs

ns = {}
version_path = convert_path('mensa_ukon/version.py')

with codecs.open(version_path, 'r', 'utf-8') as vf:
    exec(vf.read(), ns)

def requirements():
    rs = []
    with codecs.open('requirements.txt', 'r', 'utf-8') as f:
        for i in f:
            rs.append(i.strip())

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner>=2.0,<3dev'] if needs_pytest else []

with codecs.open('README.md', 'r', 'utf-8') as fd:
    setup(name='mensa-ukon',
          version=ns['__version__'],
          author='Manuel Hotz',
          author_email='manuel.hotz@uni-konstanz.de',
          description='Python library to access the canteen plan of the Uni Konstanz.',
          long_description=fd.read(),
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
          setup_requires=[
              # ... (other setup requirements)
          ] + pytest_runner,
          tests_require=['pytest'],
          install_requires=requirements(),
          include_package_data=True,
          classifiers=[
              'Environment :: MacOS X',
              'Operating System :: MacOS :: MacOS X',
              'Programming Language :: Python :: 3.5',
              'Topic :: Information Retrieval',
              'Topic :: Utility',
          ]
    )
