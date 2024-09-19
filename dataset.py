import os
from typing import Optional
from core.processor_state import State
from fastapi import APIRouter, Depends
from huggingface_hub import login

from environment import storage, HUGGING_FACE_TOKEN
from http_exceptions import check_null_response
from datasets import Dataset

dataset_router = APIRouter()


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
