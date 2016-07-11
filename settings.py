import os
from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# General
TOKEN = os.environ.get('PTB_TELEGRAM_BOT_TOKEN')
LOG_CONF = os.environ.get('PTB_LOG_CONF')
NOTIFY_CHATS = list(filter(lambda i : i is not None,
                      map(lambda s : None if s == '' else int(s),
                          os.environ.get('PTB_NOTIFY_CHAT_IDS', "").split(','))))

# Polling
USE_POLLING = os.environ.get('PTB_USE_POLLING', 'True') == 'True'
WORKERS = int(os.environ.get('PTB_WORKERS', 2))
# Webhook
URL = os.environ.get('PTB_WEBHOOK_URL')
LISTEN_IP = os.environ.get('PTB_WEBHOOK_LISTEN_IP')
LISTEN_PORT = int(os.environ.get('PTB_WEBHOOK_LISTEN_PORT', '8443'))
CERT = os.environ.get('PTB_CERT')
CERT_KEY = os.environ.get('PTB_CERT_KEY')
