from typing import Optional, Dict, List
from fastapi import APIRouter, Depends
from ismcore.model.filter import Filter, FilterItem, FilterOperator
from utils.http_exceptions import check_null_response
from environment import storage
from api import token_service

filter_router = APIRouter()


@filter_router.get('/{filter_id}')
@check_null_response
async def fetch_filter(filter_id: str, user_id: str = Depends(token_service.verify_jwt)) -> Optional[Filter]:
    return storage.fetch_filter(filter_id=filter_id)


@filter_router.post("")
@check_null_response
async def merge_filter(filter: Filter, user_id: str = Depends(token_service.verify_jwt)) -> Filter:
    filter.user_id = user_id
    return storage.insert_filter(filter)


@check_null_response
@filter_router.put("/apply")
async def apply_filter_on_data(filter_id: str, data: Dict[str, str], user_id: str = Depends(token_service.verify_jwt)) -> bool:
    return storage.apply_filter_on_data(filter_id=filter_id, data=data)


@check_null_response
@filter_router.get("/user")
async def fetch_filters_by_user(user_id: str = Depends(token_service.verify_jwt)) -> Optional[List[Filter]]:
    return storage.fetch_filters_by_user(user_id=user_id)
