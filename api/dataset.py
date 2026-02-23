import json
import logging
import os
import tempfile
import traceback

import pyarrow as pa
import pyarrow.parquet as pq
from fastapi import APIRouter, Body
from huggingface_hub import HfApi, CommitOperationAdd, CommitOperationDelete

from environment import storage, HUGGING_FACE_TOKEN
from message_router import message_router
from models.hg_models import ImportHgDatasetRequest, ExportHgDatasetRequest
from models.models import BasicResponse
from utils.http_exceptions import check_null_response
from datasets import load_dataset

logger = logging.getLogger(__name__)

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


def _serialize_values(values: list) -> list:
    """Ensure all values are strings or None for a consistent parquet schema."""
    return [
        json.dumps(v) if v is not None and not isinstance(v, str) else v
        for v in values
    ]


def _write_state_to_parquet(state_id: str, chunk_size: int = 1000) -> tuple[str, str | None] | None:
    """
    Load state data in chunks and write to a temp parquet file.
    Returns (tmp_file_path, state_name) or None if state not found.
    """
    state_meta = storage.load_state_metadata(state_id=state_id)
    if not state_meta:
        print(f"[push_hg] state metadata not found for state_id={state_id}")
        return None

    columns = list(state_meta.columns.keys())
    state_name = state_meta.config.name if state_meta.config else None
    print(f"[push_hg] writing parquet for state_id={state_id}, count={state_meta.count}, columns={len(columns)}, chunk_size={chunk_size}")

    # Build an explicit all-string schema so every chunk matches,
    # even when sparse columns are all-None in some chunks.
    schema = pa.schema([(col, pa.string()) for col in columns])

    tmp_path = tempfile.mktemp(suffix='.parquet')
    writer = None
    offset = 0

    try:
        while offset < state_meta.count:
            chunk = storage.load_state(state_id=state_id, load_data=True, offset=offset, limit=chunk_size)
            if not chunk or not chunk.data:
                print(f"[push_hg] empty chunk at offset={offset} for state_id={state_id}, stopping early")
                break

            chunk_dict = {
                col: _serialize_values(chunk.data[col].values)
                for col in columns if col in chunk.data
            }
            table = pa.table(chunk_dict, schema=schema)

            if writer is None:
                writer = pq.ParquetWriter(tmp_path, schema)

            writer.write_table(table)
            offset += chunk_size
            print(f"[push_hg] wrote chunk offset={offset}/{state_meta.count} for state_id={state_id}")
    except Exception:
        print(f"[push_hg] EXCEPTION writing parquet at offset={offset} for state_id={state_id}")
        traceback.print_exc()
        raise
    finally:
        if writer:
            writer.close()

    print(f"[push_hg] parquet complete: {tmp_path} for state_id={state_id} ({offset} rows)")
    return tmp_path, state_name


@check_null_response
@dataset_router.post("/state/{state_id}/push/hg", response_model=BasicResponse)
async def push_hg_dataset(
        state_id: str,
        payload: ExportHgDatasetRequest = Body(...),
) -> BasicResponse | None:
    token = HUGGING_FACE_TOKEN

    try:
        result = _write_state_to_parquet(state_id=state_id, chunk_size=payload.chunk_size)
        if result is None:
            return None

        tmp_path, state_name = result
        try:
            dataset_name = payload.dataset_name or state_name or state_id[:8]
            path = f"{payload.namespace}/{dataset_name}"

            api = HfApi()
            api.create_repo(repo_id=path, repo_type="dataset", exist_ok=True, private=payload.private, token=token)

            parquet_path_in_repo = "data/train-00000-of-00001.parquet"
            operations = [
                CommitOperationDelete(path_in_repo=parquet_path_in_repo, is_folder=False),
                CommitOperationAdd(path_in_repo=parquet_path_in_repo, path_or_fileobj=tmp_path),
            ]
            print(f"[push_hg] uploading parquet to {path}")
            api.create_commit(
                repo_id=path,
                repo_type="dataset",
                operations=operations,
                commit_message=payload.commit_message or "Update dataset",
                revision=payload.revision,
                token=token,
            )
            print(f"[push_hg] upload complete for {path}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        return BasicResponse(success=True, message=path)
    except Exception:
        print(f"[push_hg] EXCEPTION pushing hg dataset for state_id={state_id}")
        traceback.print_exc()
        raise
