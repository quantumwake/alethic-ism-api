import json
from typing import Optional

from core.messaging.base_message_route_model import RouteMessageStatus
from core.processor_state_storage import ProcessorState
from fastapi import APIRouter
from pydantic import ValidationError

from environment import storage
from http_exceptions import check_null_response
from message_router import message_router

# currently there is only one state router
SELECTOR_STATE_ROUTER = "processor/state/router"
SELECTOR_PROCESSOR_MONITOR = "processor/monitor"

processor_state_router = APIRouter()
monitor_route = message_router.find_route(SELECTOR_PROCESSOR_MONITOR)
state_router_route = message_router.find_route(SELECTOR_STATE_ROUTER)

@processor_state_router.post("")
@check_null_response
async def insert_processor_state_route(processor_state: ProcessorState) \
        -> Optional[ProcessorState]:

    return storage.insert_processor_state_route(
        processor_state=processor_state
    )


@processor_state_router.delete('/{route_id}')
@check_null_response
async def delete_processor_state_route(route_id: str) -> int:
    return storage.delete_processor_state_route(route_id=route_id)


@processor_state_router.post('/{state_id}/forward/entry')
@check_null_response
async def route_forward_query_state_entry(state_id: str, query_state_entry: dict) -> RouteMessageStatus:
    state = storage.fetch_state(state_id=state_id)
    if not state:
        raise ValidationError(f'input state id {state_id} does not exist')

    # project = storage.fetch_user_project(state.project_id)

    route_id = None ## TODO
    raise NotImplementedError('route_forward_query_state_entry')

    # create a message envelop for the query state
    message = {
        # "user_id": project.user_id if project else None,
        # "project_id": project.project_id if project else None,
        "route_id": route_id,
        "type": "query_state_route",
        "input_state_id": state_id,
        "query_state": [
            query_state_entry
        ]
    }

    # convert to a string object for submission to the pub system
    message_string = json.dumps(message)
    status = message_router.send_message("state/router", message_string)
    return status


@processor_state_router.post('/{route_id}')
@check_null_response
async def execute_processor_state_route(route_id: str) -> RouteMessageStatus:

    processor_state = storage.fetch_processor_state_route(route_id=route_id)

    if not processor_state or len(processor_state) != 1:
        #
        # monitor_message = json.dumps({
        #     "type": "processor_state",
        #     "route_id": route_id,
        #     "status": ProcessorStatusCode.FAILED.name.,
        #     "exception": str(exception) if exception else None,
        # })
        #
        # processor_state_route_monitor.send_message()
        raise ValidationError(f'invalid processor state route')


    # fetch the state information as input
    # state = storage.fetch_state(state_id=processor_state.state_id)
    # if not state:
    #     raise ValidationError(f'input state id {state.id} does not exist')
    # # fetch project information associated to this processor state
    # project = storage.fetch_user_project(state.project_id)

    # create a message envelop for running a complete state forward
    message = {
        # "user_id": project.user_id if project else None,
        # "project_id": project.project_id if project else None,
        "type": "query_state_route",
        "route_id": route_id
        # "input_state_id": state_id,
        # "processor_id": processor_id
    }

    # convert to a string object for submission to the pub system
    message_string = json.dumps(message)
    # status = message_router.send_message(SELECTOR_STATE_ROUTER, message_string)
    status = await state_router_route.publish(message_string)
    return status
