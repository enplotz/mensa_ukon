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
          python_requires='~=3.5',
          packages=find_packages(exclude=['tests*']),
          py_modules=['mensa', 'bot', 'settings'],
          # TODO structure canteen data source as plugins
          # see https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins
          entry_points={
              'console_scripts': [
                  'mensa = scripts.mensa_cli:meals',
                  'mensa_bot = scripts.bot:run_bot',
              ]
          },
          setup_requires=pytest_runner,
          tests_require=['pytest', 'requests-file'],
          install_requires=['python-telegram-bot',
                            'requests-html',
                            'lxml',
                            'html5lib',
                            'CacheControl',
                            'click',
                            'click-datetime',
                            'click-log',
                            'pendulum',
                            'aenum'],
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
