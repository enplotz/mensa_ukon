#! /usr/bin/env python3

import sys
from setuptools import setup, find_packages
from mensa_ukon import version

def requirements():
    rs = []
    with open('requirements.txt') as f:
        for i in f:
            rs.append(i.strip())

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner>=2.0,<3dev'] if needs_pytest else []

with open('README.md', 'r') as fd:
    setup(name='mensa-ukon',
          version=version.__version__,
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
                  'mensa = mensa_ukon.mensa_cli:meals',
                  # 'mensa_bot = bot:main_bot', # TODO Needs external .env file location...
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
