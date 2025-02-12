from typing import Optional, List

from core.base_model import UsageReport
from core.processor_state_storage import FieldConfig
from fastapi import APIRouter, Depends

from api import token_service
from environment import storage
from utils.http_exceptions import check_null_response

usage_router = APIRouter()


@usage_router.get("/user/{user_id}")
@check_null_response
async def fetch_usage_group_by_user(user_id: str = Depends(token_service.verify_jwt)) -> Optional[List[UsageReport]]:
    usage = storage.fetch_usage_report(
        user_id=FieldConfig(
            field_name="user_id",
            value=user_id,
            use_in_group_by=True,
            use_in_where=True
        ),
        # year=FieldConfig(
        #     field_name="year",
        #     value="2024",
        #     use_in_group_by=True,
        #     use_in_where=True
        # ),
    )
    return usage


@usage_router.get("/user/{user_id}/project/{project_id}")
@check_null_response
async def fetch_usage_group_by_user_and_project(user_id: str, project_id: str) -> Optional[List[UsageReport]]:
    # return storage.fetch_usage_report_user(user_id=user_id)
    usage = storage.fetch_usage_report(
        user_id=FieldConfig("user_id", value=user_id, use_in_group_by=True, use_in_where=True),
        project_id=FieldConfig("project_id", value=project_id, use_in_group_by=True, use_in_where=True),
    )
    return usage


@usage_router.get("/user/{user_id}/charts")
@check_null_response
async def fetch_usage_group_for_charts(user_id: str) -> Optional[List[UsageReport]]:
    # return storage.fetch_usage_report_user(user_id=user_id)
    usage = storage.fetch_usage_report(
        user_id=FieldConfig("user_id", value=user_id, use_in_group_by=True, use_in_where=True),
        year=FieldConfig("year", value=None, use_in_group_by=True, use_in_where=False),
        month=FieldConfig("month", value=None, use_in_group_by=True, use_in_where=False),
        day=FieldConfig("day", value=None, use_in_group_by=True, use_in_where=False),
        resource_type=FieldConfig("resource_type", value=None, use_in_group_by=True, use_in_where=False),
    )
    return usage
