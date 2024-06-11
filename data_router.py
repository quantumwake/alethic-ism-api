import logging

import pulsar
import yaml

from typing import Union
from pulsar.schema import schema
from environment import MSG_URL, ROUTING_CONFIG_FILE


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

