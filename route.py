import json

from core.base_message_router import Router, RouteMessageStatus
from core.pulsar_message_producer_provider import PulsarMessagingProducerProvider
from fastapi import APIRouter
from pydantic import ValidationError

from environment import storage, ROUTING_FILE
from http_exceptions import check_null_response

message_provider = PulsarMessagingProducerProvider()
message_router = Router(
    provider=message_provider,
    yaml_file=ROUTING_FILE
)
route_router = APIRouter()
