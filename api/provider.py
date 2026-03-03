from typing import Optional, List

from fastapi import APIRouter
from ismcore.model.base_model import ProcessorProvider

from environment import storage
from utils.http_exceptions import check_null_response

provider_router = APIRouter()


@provider_router.get("/list")
@check_null_response
async def fetch_provider_processors(user_id: str = None, project_id: str = None, name: str = None, version: str = None, class_name: str = None) \
        -> Optional[List[ProcessorProvider]]:

    return storage.fetch_processor_providers(
        user_id=user_id,
        project_id=project_id,
        name=name,
        version=version,
        class_name=class_name
    )


@provider_router.get("/search")
async def search_providers(
    name: str = None,
    version: str = None,
    class_name: str = None,
    limit: int = 20,
):
    """Search providers with case-insensitive partial matching (ILIKE) on name, version, and class_name."""
    return storage.search_processor_providers(
        name=name,
        version=version,
        class_name=class_name,
        limit=limit,
    )
