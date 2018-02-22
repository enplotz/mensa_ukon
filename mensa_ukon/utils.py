import importlib
import os

from dotenv import load_dotenv
from os import path, getcwd

from mensa_ukon import settings
from mensa_ukon.mensabot import BotConfigurationError


def load_from_cwd():
    load_from_env(None)


def load_from_dict(d):
    for k, v in d.items():
        os.environ.setdefault(k, v)


def reload_settings():
    importlib.reload(settings)


def load_from_env(env_path):
    # TODO improve this...
    if env_path:
        load_dotenv(env_path)
    else:
        dotenv_path = path.join(getcwd(), '.env')
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
    # e.g. for deploy on heroku we have no .env file, but everything is already in ConfigVars

    importlib.reload(settings)
