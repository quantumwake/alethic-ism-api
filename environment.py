import os

import dotenv
from db.processor_state_db_storage import PostgresDatabaseStorage

dotenv.load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres1@localhost:5432/postgres")
API_ROOT_PATH = os.environ.get("API_ROOT_PATH", None)

# setup the storage device for managing state, state configs, templates, models and so forth
storage = PostgresDatabaseStorage(database_url=DATABASE_URL)


