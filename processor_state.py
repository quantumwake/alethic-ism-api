from typing import Optional
from core.processor_state_storage import ProcessorState
from fastapi import APIRouter
from environment import storage
from http_exceptions import check_null_response

processor_state_router = APIRouter()


@processor_state_router.post("/create")
@check_null_response
async def insert_processor_state(processor_state: ProcessorState) \
        -> Optional[ProcessorState]:

    return storage.insert_processor_state(
        processor_state=processor_state
    )

# async def delete_processor_state(processor_id: str, state_id: str):
    # state_storage.delete_processor_state