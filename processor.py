from typing import Optional, List

from core.base_model import ProcessorStateDirection
from core.processor_state_storage import Processor, ProcessorState
from fastapi import APIRouter

from environment import storage
from http_exceptions import check_null_response

processor_router = APIRouter()


@processor_router.get("/{processor_id}")
@check_null_response
async def fetch_processor(processor_id: str) \
        -> Optional[Processor]:

    return storage.fetch_processor(processor_id=processor_id)


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

    return storage.fetch_processor_state(
        processor_id=processor_id,
        direction=direction
    )

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