import json
from typing import Optional

from fastapi import APIRouter
from ismcore.messaging.base_message_route_model import RouteMessageStatus
from ismcore.model.base_model import ProcessorState, EdgeFunctionConfig
from pydantic import ValidationError

from environment import storage
from utils.http_exceptions import check_null_response
from message_router import message_router

# currently there is only one state router
SELECTOR_STATE_ROUTER = "processor/state/router"
SELECTOR_PROCESSOR_MONITOR = "processor/monitor"

processor_state_router = APIRouter()
monitor_route = message_router.find_route(SELECTOR_PROCESSOR_MONITOR)
state_router_route = message_router.find_route(SELECTOR_STATE_ROUTER)


@processor_state_router.post("")
@check_null_response
async def insert_processor_state_route(processor_state: ProcessorState) -> Optional[ProcessorState]:
    return storage.insert_processor_state_route(
        processor_state=processor_state
    )


@processor_state_router.delete('/{route_id}')
@check_null_response
async def delete_processor_state_route(route_id: str) -> int:
    return storage.delete_processor_state_route(route_id=route_id)

@processor_state_router.post('/{route_id}')
@check_null_response
async def execute_processor_state_route(route_id: str) -> RouteMessageStatus:
    processor_state = storage.fetch_processor_state_route(route_id=route_id)
    if not processor_state or len(processor_state) != 1:
        raise ValidationError(f'invalid processor state route')

    # create a message envelop for running a complete state forward
    message = {
        "type": "query_state_route",
        "route_id": route_id
    }

    # convert to a string object for submission to the pub system
    message_string = json.dumps(message)
    status = await state_router_route.publish(message_string)
    return status


@processor_state_router.get('/{route_id}/edge-function')
async def get_edge_function_config(route_id: str) -> Optional[EdgeFunctionConfig]:
    return storage.fetch_edge_function_config(route_id=route_id)


@processor_state_router.put('/{route_id}/edge-function')
@check_null_response
async def update_edge_function_config(route_id: str, config: EdgeFunctionConfig) -> Optional[EdgeFunctionConfig]:
    return storage.update_edge_function_config(route_id=route_id, config=config)
