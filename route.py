import json
import os

from core.base_message_router import Router, RouteMessageStatus
from core.pulsar_message_producer_provider import PulsarMessagingProducerProvider
from fastapi import UploadFile, File, APIRouter
from pydantic import ValidationError

from environment import storage
from http_exceptions import check_null_response

ROUTING_FILE = os.environ.get("ROUTING_FILE", '.routing.yaml')

message_provider = PulsarMessagingProducerProvider()
message_router = Router(
    provider=message_provider,
    yaml_file=ROUTING_FILE
)
route_router = APIRouter()


@route_router.post('/{state_id}/forward/entry')
@check_null_response
async def route_forward_query_state_entry(state_id: str, query_state_entry: dict) -> RouteMessageStatus:
    state = storage.fetch_state(state_id=state_id)
    if not state:
        raise ValidationError(f'input state id {state_id} does not exist')
    project = storage.fetch_user_project(state.project_id)

    # create a message envelop for the query state
    message = {
        "user_id": project.user_id if project else None,
        "project_id": project.project_id if project else None,
        "type": "query_state_entry",
        "input_state_id": state_id,
        "query_state": [
            query_state_entry
        ]
    }

    # convert to a string object for submission to the pub system
    message_string = json.dumps(message)
    status = message_router.send_message("state/router", message_string)
    return status


@route_router.post('/{state_id}/{processor_id}/forward/complete')
@check_null_response
async def route_forward_complete_state(state_id: str, processor_id: str) -> RouteMessageStatus:

    state = storage.fetch_state(state_id=state_id)
    if not state:
        raise ValidationError(f'input state id {state_id} does not exist')
    project = storage.fetch_user_project(state.project_id)

    # create a message envelop for running a complete state forward
    message = {
        "user_id": project.user_id if project else None,
        "project_id": project.project_id if project else None,
        "type": "query_state_complete",
        "input_state_id": state_id,
        "processor_id": processor_id
    }

    # convert to a string object for submission to the pub system
    message_string = json.dumps(message)
    status = message_router.send_message("state/router", message_string)
    return status
