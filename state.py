import io
import json
from typing import Optional
from core.processor_state import State, StateDataKeyDefinition
from fastapi import UploadFile, File, APIRouter
from environment import storage
from http_exceptions import check_null_response
from message_router import message_router
from process_file import process_csv_stream, process_csv_state_sync_store

state_router = APIRouter()


@state_router.get('/{state_id}')
@check_null_response
async def fetch_state(state_id: str, load_data: bool = False) -> Optional[State]:
    return storage.load_state(state_id=state_id, load_data=load_data)


@state_router.post("/create")
@check_null_response
async def merge_state(state: State) -> State:
    return storage.save_state(state=state, options={
        "force_update_column": True
    })


@state_router.delete('/{state_id}/data')
@check_null_response
async def delete_state_data(state_id: str) -> int:
    result = storage.delete_state_data(state_id=state_id)
    return 1


@state_router.delete("/{state_id}/config/{definition_type}/{id}")
@check_null_response
async def delete_config_definition(state_id: str, definition_type: str, id: str) -> int:
    return storage.delete_state_config_key_definition(
        state_id=state_id,
        definition_type=definition_type,
        definition_id=id
    )


@state_router.delete("/{state_id}/column/{column_id}")
@check_null_response
async def delete_state_column(state_id, column_id) -> int:
    storage.delete_state_column()


    # return storage.save_state(state=state, options={
    #     "force_update_column": True
    # })


@state_router.post("/{state_id}/data/upload")
async def upload_file(state_id: str, file: UploadFile = File(...)):
    try:
        state = storage.load_state(state_id=state_id)

        if not state:
            raise KeyError(f"unable to locate state id {state_id}")

        data = await file.read()
        text_data = io.StringIO(data.decode('utf-8'))
        query_state = await process_csv_state_sync_store(state=state, io=text_data)

        # derive the new message with complete csv file data
        message = {
            "type": "query_state_direct",
            "state_id": state.id,
            "query_state": query_state
        }

        message_string = json.dumps(message)
        sync_route = message_router.find_route("processor/state/sync")
        await sync_route.publish(msg=message_string)
        # sync_route.flush()

        # state = storage.save_state(state=state)

        return {
            "status": "success",
            "message": "file uploaded successfully",
            "state_id": state.id,
            "count": state.count
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "count": 0}


@state_router.get('/{state_id}/processors')
@check_null_response
async def fetch(state_id: str):
    return storage.fetch_processor_state(state_id=state_id)

