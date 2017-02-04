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
        if not os.path.exists(dotenv_path):
            raise BotConfigurationError('.env does not exist at {}'.format(dotenv_path))
        load_dotenv(dotenv_path)

    importlib.reload(settings)
