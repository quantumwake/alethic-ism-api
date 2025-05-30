import logging
import os

import dotenv
from ismcore.utils.general_utils import str2bool
from ismdb.postgres_storage_class import PostgresDatabaseStorage

dotenv.load_dotenv()

HUGGING_FACE_TOKEN = os.environ.get("HUGGING_FACE_TOKEN", None)
DATABASE_URL = os.environ.get("DATABASE_URL", None)
API_ROOT_PATH = os.environ.get("API_ROOT_PATH", None)
ROUTING_FILE = os.environ.get("ROUTING_FILE", '.routing.yaml')
FIREBASE_CREDENTIALS_JSON_FILE = os.environ.get("FIREBASE_CREDENTIALS_JSON_FILE", ".firebase-credentials.json")
LOG_LEVEL = os.environ.get("LOG_LEVEL", logging.INFO)
ENABLED_LOCAL_AUTH = str2bool(os.environ.get("ENABLED_LOCAL_AUTH", "False"))
ENABLED_FIREBASE_AUTH = str2bool(os.environ.get("ENABLED_FIREBASE_AUTH", "False"))

if not DATABASE_URL:
    raise ValueError(f'invalid database url, no DATABASE_URL env was specified')

logging.basicConfig(level=LOG_LEVEL)
logging.info(DATABASE_URL[:20])
logging = logging.getLogger(__name__)

# set up the storage device for managing state, state configs, templates, models and so forth
storage = PostgresDatabaseStorage(database_url=DATABASE_URL)


