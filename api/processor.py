from typing import Optional, List

from fastapi import APIRouter, Depends
from ismcore.model.base_model import Processor, ProcessorStateDirection, ProcessorState, ProcessorStatusCode

from api import token_service
from environment import storage
from utils.http_exceptions import check_null_response
from models.models import ProcessorStatusUpdated

processor_router = APIRouter()


@check_null_response
@processor_router.get("/{processor_id}")
async def fetch_processor(processor_id: str, user_id: str = Depends(token_service.verify_jwt)) -> Processor | None:
    return storage.fetch_processor(processor_id=processor_id)

@check_null_response
@processor_router.delete("/{processor_id}")
async def delete_processor(processor_id: str):
    routes = storage.fetch_processor_state_route(processor_id=processor_id)
    if routes:
        for route in routes:
            storage.delete_processor_state_route_by_id(processor_state_id=route.id)

    # delete all workflow edges given the node it is connected to, in any direction.
    storage.delete_workflow_edges_by_node_id(node_id=processor_id)

    # delete the processor and the node
    storage.delete_processor(processor_id=processor_id)
    storage.delete_workflow_node(node_id=processor_id)

@processor_router.post("/create")
@check_null_response
async def merge_processor(processor: Processor) \
        -> Optional[Processor]:

    return storage.insert_processor(processor=processor)


@processor_router.get("/{processor_id}/states")
@check_null_response
async def fetch_processor_states(
        processor_id: str,
        direction: ProcessorStateDirection = ProcessorStateDirection.INPUT) \
        -> Optional[List[ProcessorState]]:

    connected_states =  storage.fetch_processor_state_route(
        processor_id=processor_id,
        direction=direction
    )

    if not connected_states:
        return []

    return connected_states

@processor_router.post("/{processor_id}/status/{status}")
@check_null_response
async def change_processor_status(processor_id: str, status: str = "TERMINATE") -> ProcessorStatusUpdated:
    statusCode = ProcessorStatusCode(status)

    updated = storage.change_processor_status(
        processor_id=processor_id,
        status=statusCode
    )

    result = ProcessorStatusUpdated(
        processor_id=processor_id,
        status=statusCode,
        success=False,
    )

    # if the update was successful then set success = true
    if updated > 0: result.success = True
    return result

#
# @app.put("/processor/terminate", tags=["Processor"])
# async def terminate_processor(processor_state: ProcessorState) \
#         -> Optional[ProcessorState]:
#
#     # set the process to queued
#     processor_state.status = StatusCode.TERMINATED
#     state_storage.update_processor_state(processor_state)
#     message = processor_state.model_dump_json()
#
#     # identify the route
#     route = get_route_by_processor(processor_id=processor_state.processor_id)
#
#     if route.manage:
#         route.manage.send(message)
#
#     return processor_state