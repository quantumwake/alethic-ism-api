import json

from fastapi import APIRouter, Body

from environment import storage, HUGGING_FACE_TOKEN
from message_router import message_router
from models.hg_models import ImportHgDatasetRequest
from models.models import BasicResponse
from utils.http_exceptions import check_null_response
from datasets import Dataset
from datasets import load_dataset

dataset_router = APIRouter()

@check_null_response
@dataset_router.post("/state/{state_id}/load/hg", response_model=BasicResponse)
async def load_hg_dataset(
        state_id: str,
        payload: ImportHgDatasetRequest = Body(...),
) -> BasicResponse | None:
    # TODO need to pull the config/vault key -- more thought is required
    # if request.vaultKeyId is None:
    token = HUGGING_FACE_TOKEN

    # Load the dataset from the Hugging Face Hub from URL
    dataset = load_dataset(payload.path, subset=payload.subset, split=payload.split, revision=payload.revision, token=token)
    dataset = dataset.to_list()

    offset = 0
    block_index = 0
    block_size = 10
    sync_route = message_router.find_route("processor/state/sync")
    while offset < len(dataset):
        message_block = {
            "type": "query_state_direct",
            "state_id": state_id,
            "query_state": dataset[offset:offset + block_size]
        }
        offset += block_size
        block_index += 1

        message_string = json.dumps(message_block)
        await sync_route.publish(msg=message_string)

    return BasicResponse(success=True)



@dataset_router.get('/{state_id}/create/hg')
@check_null_response
# async def create_hg_dataset(state_id: str, namespace: str, user_id: str = Depends(token_service.verify_jwt)) -> Optional[State]:
async def create_hg_dataset(state_id: str, namespace: str) -> str:
    # TODO make sure state has name otherwise create a random name
    state = storage.load_state(state_id=state_id, load_data=True)

    state_name = state.config.name
    if state_name is None:
        state_name = state_id[:8]

    # login("")

    # Prepare the data for Hugging Face's Dataset
    # Flatten the 'data' key into a format that Hugging Face expects
    data_for_dataset = {
        column: values.values
        for column, values in state.data.items()
    }

    # Create a Dataset object
    dataset = Dataset.from_dict(data_for_dataset)

    path = f"{namespace}/{state_name}"

    # Push the dataset to the Hugging Face Hub
    dataset.push_to_hub(f"{path}", token=HUGGING_FACE_TOKEN, private=True)

    return path
