import logging

import yaml
import os
import pulsar
import dotenv

from core.processor_state import InstructionTemplate, State, ProcessorStatus
from core.processor_state_storage import Processor, ProcessorState
from db.processor_state_db_storage import ProcessorStateDatabaseStorage

from exceptions import CustomException, custom_exception_handler

from typing import Optional, List, Union, Any
from fastapi import FastAPI
from pulsar.schema import schema

dotenv.load_dotenv()

MSG_URL = os.environ.get("MSG_URL", "pulsar://localhost:6650")
MSG_QA_TOPIC = os.environ.get("MSG_TOPIC", "ism_openai_qa")
MSG_QA_MANAGE_TOPIC = os.environ.get("MSG_MANAGEMENT_TOPIC", "ism_openai_manage_topic")
MSG_QA_TOPIC_SUBSCRIPTION = os.environ.get("MSG_TOPIC_SUBSCRIPTION", "ism_openai_qa_subscription")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres1@localhost:5432/postgres")
ROUTING_CONFIG_FILE = os.environ.get("ROUTING_CONFIG_FILE", 'routing.yaml')
root_path = os.environ.get("API_ROOT_PATH", None)


if root_path:
    app = FastAPI(root_path=root_path)
else:
    app = FastAPI()

# Register the custom exception handler
app.add_exception_handler(CustomException, custom_exception_handler)

# setup the storage device for managing state, state configs, templates, models and so forth
state_storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)

routes = {}
message_config = {}


def get_message_config(yaml_file: str = ROUTING_CONFIG_FILE):
    global message_config
    if message_config:
        return message_config

    with open(yaml_file, 'r') as file:
        message_config = yaml.safe_load(file)
        message_config = message_config['messageConfig']

    return message_config


def get_message_config_url(selector: str = None) -> str:
    config = get_message_config()

    url = MSG_URL
    if 'url' in config:
        url = config['url']

    # iterate each topic and check for specific urls, if any
    _topics = get_message_topics()

    # check if url is strictly specified in the route
    specific_url = [topic['url'] for topic in _topics
                    if 'url' in topic
                    and selector in topic['selector']]

    specific_url = specific_url[0] if specific_url else None

    # return route specific url, otherwise general
    return specific_url if specific_url else url


class Route:

    client: Union[pulsar.Client]
    process: Union[pulsar.Producer, pulsar.Consumer]
    manage: Union[pulsar.Producer, pulsar.Consumer]

    def __init__(self, topic: dict):

        # routing configuration
        self.selector = topic['selector']
        self.process_topic = topic['process_topic']
        self.manage_topic = topic['manage_topic']
        self.subscription = topic['subscription']
        self.url = get_message_config_url(self.selector)

        # routing client used to actual produce/consume data
        self.client = pulsar.Client(self.url)
        self.process = self.client.create_producer(
            self.process_topic,
            schema=schema.StringSchema()
        )

        self.manage = self.client.create_producer(
            self.manage_topic,
            schema=schema.StringSchema()
        ) if self.manage_topic else None


def get_message_topics():
    return get_message_config()['topics']


def get_message_topic(topic: str):
    topics = get_message_topics()
    topic = topics[topic] if topic in topics else None

    if topic:
        return topic

    logging.error(f'invalid topic name: {topic} requested from topics: {topics}')
    return None


def get_message_routes(selector: str = None):
    global routes

    if not routes:
        routes = {
            topic['selector']: Route(topic)
            for topic in get_message_topics()
        }

    if selector:
        return routes[selector]
    else:
        return routes


def get_route_by_processor(processor_id: str) -> Route:
    available_routes = get_message_routes()
    if processor_id not in available_routes:
        raise NotImplementedError(f'message routing is not defined for processor state id: {processor_id}, '
                                  f'please make sure to setup a route selector as part of the routing.yaml')

    return routes[processor_id]



def send_message(producer, msg):
    try:
        producer.send(msg, None)
    except Exception as e:
        print("Failed to send message: %s", e)
        raise e
    finally:
        try:
            producer.flush()
        except:
            pass


@app.get("/templates", tags=["Template"])
def get_instruction_templates() -> Optional[List[InstructionTemplate]]:
    return state_storage.fetch_templates()


@app.post('/template', tags=['Template'])
def merge_instruction_template(template: InstructionTemplate) -> InstructionTemplate:
    state_storage.insert_template(instruction_template=template)
    return template

@app.post('/template/text', tags=['Template'])
def merge_instruction_template_text(template_path: str, template_content: str, template_type: str):
    instruction = InstructionTemplate(
        template_path=template_path,
        template_content=template_content,
        template_type=template_type
    )
    return merge_instruction_template(instruction)

@app.get("/state/list", tags=["State"])
async def get_states():
    return state_storage.fetch_states()


@app.get('/state/{state_id}', tags=['State'])
async def get_state(state_id: str) -> Optional[State]:
    return state_storage.load_state(state_id=state_id)


@app.post("/state", tags=["State"])
async def merge_state(state: State) -> str:
    state_id = state_storage.save_state(state=state)
    state_storage.load_state(state_id=state_id)
    return state_id


@app.get("/template", tags=["Template"])
def get_instruction_template(template_path: str) -> Optional[InstructionTemplate]:
    return state_storage.fetch_template(template_path=template_path)


@app.get("/processor/{processor_id}", tags=["Processor"])
def get_processor(processor_id: str) -> Optional[Processor]:
    return state_storage.fetch_processor(processor_id=processor_id)


@app.get("/processors", tags=["Processor"])
def get_processors() -> Optional[List[Processor]]:
    return state_storage.fetch_processors()


@app.post("/processor", tags=["Processor"])
async def merge_processor(processor: Processor) -> Optional[ProcessorState]:
    return state_storage.insert_processor(processor=processor)


# @app.get("/processor/model/types", tags=["Processor"])
# def get_processor_model_types() -> Optional[List[Model]]:
#     return state_storage.fetch_models()


@app.post("/processor/execute", tags=["Processor"])
async def execute(processor_state: ProcessorState) -> ProcessorState:

    # identify the route
    route = get_route_by_processor(processor_id=processor_state.processor_id)

    # set the process to queued
    processor_state.status = ProcessorStatus.QUEUED
    state_storage.update_processor_state(processor_state)
    message = processor_state.model_dump_json()
    route.process.send(message)

    return processor_state


@app.put("/processor/terminate", tags=["Processor"])
async def terminate_processor(processor_state: ProcessorState) -> Optional[ProcessorState]:

    # set the process to queued
    processor_state.status = ProcessorStatus.TERMINATED
    state_storage.update_processor_state(processor_state)
    message = processor_state.model_dump_json()

    # identify the route
    route = get_route_by_processor(processor_id=processor_state.processor_id)

    if route.manage:
        route.manage.send(message)

    return processor_state


@app.get("/processor/state/list", tags=["Processor State"])
def get_processor_states() -> Optional[List[ProcessorState]]:
    return state_storage.fetch_processor_states()


@app.post("/processor/state", tags=["Processor State"])
async def merge_processor_state(processor_state: ProcessorState) -> Optional[ProcessorState]:
    return state_storage.update_processor_state(processor_state=processor_state)
