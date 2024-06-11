import os

import dotenv
from db.processor_state_db_storage import ProcessorStateDatabaseStorage, PostgresDatabaseStorage

dotenv.load_dotenv()

MSG_URL = os.environ.get("MSG_URL", "pulsar://localhost:6650")
MSG_QA_TOPIC = os.environ.get("MSG_TOPIC", "ism_openai_qa")
MSG_QA_MANAGE_TOPIC = os.environ.get("MSG_MANAGEMENT_TOPIC", "ism_openai_manage_topic")
MSG_QA_TOPIC_SUBSCRIPTION = os.environ.get("MSG_TOPIC_SUBSCRIPTION", "ism_openai_qa_subscription")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres1@localhost:5432/postgres")
ROUTING_CONFIG_FILE = os.environ.get("ROUTING_CONFIG_FILE", 'routing.yaml')
API_ROOT_PATH = os.environ.get("API_ROOT_PATH", None)


# setup the storage device for managing state, state configs, templates, models and so forth
storage = PostgresDatabaseStorage(database_url=DATABASE_URL)


