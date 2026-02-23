import json
import logging
import os
import tempfile

import pyarrow as pa
import pyarrow.parquet as pq
from fastapi import APIRouter, Body
from huggingface_hub import HfApi

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


def _write_state_to_parquet(state_id: str, chunk_size: int = 1000) -> tuple[str, str | None] | None:
    """
    Load state data in chunks and write to a temp parquet file.
    Returns (tmp_file_path, state_name) or None if state not found.
    """
    state_meta = storage.load_state_metadata(state_id=state_id)
    if not state_meta:
        logger.warning("state metadata not found for state_id=%s", state_id)
        return None

    columns = list(state_meta.columns.keys())
    state_name = state_meta.config.name if state_meta.config else None
    logger.info("writing parquet for state_id=%s, count=%d, columns=%d, chunk_size=%d",
                state_id, state_meta.count, len(columns), chunk_size)

    tmp_path = tempfile.mktemp(suffix='.parquet')
    writer = None
    offset = 0

    try:
        while offset < state_meta.count:
            chunk = storage.load_state(state_id=state_id, load_data=True, offset=offset, limit=chunk_size)
            if not chunk or not chunk.data:
                logger.warning("empty chunk at offset=%d for state_id=%s, stopping", offset, state_id)
                break

            chunk_dict = {col: chunk.data[col].values for col in columns if col in chunk.data}
            table = pa.table(chunk_dict)

            if writer is None:
                writer = pq.ParquetWriter(tmp_path, table.schema)

            writer.write_table(table)
            offset += chunk_size
            logger.debug("wrote chunk offset=%d for state_id=%s", offset, state_id)
    except Exception:
        logger.exception("failed writing parquet at offset=%d for state_id=%s", offset, state_id)
        raise
    finally:
        if writer:
            writer.close()

    logger.info("parquet written to %s for state_id=%s (%d rows)", tmp_path, state_id, offset)
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
            logger.info("uploading parquet to %s", path)
            api.upload_file(
                path_or_fileobj=tmp_path,
                path_in_repo="data/train-00000-of-00001.parquet",
                repo_id=path,
                repo_type="dataset",
                token=token,
                commit_message=payload.commit_message,
                revision=payload.revision,
            )
            logger.info("upload complete for %s", path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        return BasicResponse(success=True, message=path)
    except Exception:
        logger.exception("failed to push hg dataset for state_id=%s", state_id)
        raise
