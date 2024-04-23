from typing import List, Optional
from core.processor_state_storage import ProcessorState
from environment import state_storage
from main import app


@app.post("/processor/state", tags=["Processor State"])
async def insert_processor_state(processor_state: ProcessorState) \
        -> Optional[ProcessorState]:

    return state_storage.insert_processor_state(
        processor_state=processor_state
    )
