from typing import Optional, List

from core.processor_state import ProcessorStateDirection
from core.processor_state_storage import Processor, ProcessorState
from fastapi import APIRouter

from environment import state_storage

processor_router = APIRouter()

@processor_router.get("/{processor_id}")
def fetch_processor(processor_id: str) \
        -> Optional[Processor]:

    return state_storage.fetch_processor(processor_id=processor_id)


@processor_router.post("/create")
async def merge_processor(processor: Processor) \
        -> Optional[Processor]:

    return state_storage.insert_processor(processor=processor)


@processor_router.get("/{processor_id}/state")
def fetch_processor_states(processor_id: str,
                           direction: ProcessorStateDirection = ProcessorStateDirection.INPUT) \
        -> Optional[List[ProcessorState]]:

    return state_storage.fetch_processor_state(
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