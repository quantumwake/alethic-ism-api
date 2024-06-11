from typing import Optional, List

from core.processor_state_storage import ProcessorProvider
from fastapi import APIRouter
from environment import storage
from http_exceptions import check_null_response

provider_router = APIRouter()


@provider_router.get("/processors")
@check_null_response
async def fetch_provider_processors(name: str = None, version: str = None, class_name: str = None) \
        -> Optional[List[ProcessorProvider]]:
    return storage.fetch_processor_providers(name=name, version=version, class_name=class_name)
