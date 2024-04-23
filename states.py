import io
from typing import Optional
from core.processor_state import State
from fastapi import UploadFile, File, APIRouter
from environment import state_storage
from process_file import process_csv_stream

state_router = APIRouter()

@state_router.get('/{state_id}')
async def fetch_state(state_id: str, load_data: bool = False) -> Optional[State]:
    return state_storage.load_state(state_id=state_id, load_data=load_data)


@state_router.post("/create")
async def merge_state(state: State) -> State:
    return state_storage.save_state(state=state)


@state_router.post("/{state_id}/data/upload")
async def upload_file(state_id: str, file: UploadFile = File(...)):
    try:
        state = state_storage.load_state(state_id=state_id)

        if not state:
            raise KeyError(f"unable to locate state id {state_id}")

        data = await file.read()
        text_data = io.StringIO(data.decode('utf-8'))
        state = await process_csv_stream(state=state, io=text_data)
        state = state_storage.save_state(state=state)

        return {
            "status": "success",
            "message": "file uploaded successfully",
            "state_id": state.id,
            "count": state.count
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "count": 0}

