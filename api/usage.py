from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends
from ismcore.model.base_model_usage_and_limits import UserProjectCurrentUsageReport, UsageReport
from ismcore.storage.processor_state_storage import FieldConfig

from api import token_service
from environment import storage
from utils.http_exceptions import check_null_response

usage_router = APIRouter()

#
# @usage_router.get("/user")
# @check_null_response
# async def fetch_usage_group_by_user(user_id: str = Depends(token_service.verify_jwt)) -> Optional[List[UsageReport]]:
#     usage = storage.fetch_usage_report(
#         user_id=FieldConfig("user_id", value=user_id, use_in_group_by=True, use_in_where=True),
#         input_count=FieldConfig("input_count", value=None, aggregate="SUM"),
#         input_cost=FieldConfig("input_cost", value=None, aggregate="SUM"),
#         input_tokens=FieldConfig("input_tokens", value=None, aggregate="SUM"),
#         input_price=FieldConfig("input_price", value=None, aggregate="MAX"),
#
#         output_count=FieldConfig("output_count", value=None, aggregate="SUM"),
#         output_cost=FieldConfig("output_cost", value=None, aggregate="SUM"),
#         output_tokens=FieldConfig("output_tokens", value=None, aggregate="SUM"),
#         output_price=FieldConfig("output_price", value=None, aggregate="MAX"),
#
#         total_tokens=FieldConfig("total_tokens", value=None, aggregate="SUM"),
#         total_cost=FieldConfig("total_cost", value=None, aggregate="SUM"),
#     )
#     return usage


@usage_router.get("/project/{project_id}/percentages")
async def fetch_project_usage_percentages(project_id: str, user_id: str = Depends(token_service.verify_jwt)) -> Optional[UserProjectCurrentUsageReport]:
    """
    Fetch current usage percentages for the authenticated user.

    Returns usage percentages across different time periods (minute, hour, day, month, year)
    for both tokens and costs. Percentages are calculated against the user's tier limits.

    Returns None if the user has no usage yet.
    """

    if project_id is None:
        return None

    user_current_usage = storage.fetch_user_project_current_usage_report(user_id=user_id, project_id=project_id)
    return user_current_usage

@usage_router.get("/user/percentages")
async def fetch_user_usage_percentages(user_id: str = Depends(token_service.verify_jwt)) -> Optional[UserProjectCurrentUsageReport]:
    """
    Fetch current usage percentages for the authenticated user.

    Returns usage percentages across different time periods (minute, hour, day, month, year)
    for both tokens and costs. Percentages are calculated against the user's tier limits.

    Returns None if the user has no usage yet.
    """
    user_current_usage = storage.fetch_user_project_current_usage_report(user_id=user_id)
    return user_current_usage


@usage_router.get("/user/percentages/status")
@check_null_response
async def fetch_user_usage_status(
    user_id: str = Depends(token_service.verify_jwt),
    warn_pct: float = 90.0,
    block_pct: float = 100.0
) -> Optional[Dict[str, Any]]:
    """
    Fetch current usage percentages and decision status for the authenticated user.

    Args:
        user_id: Authenticated user ID from JWT token
        warn_pct: Warning threshold percentage (default: 90.0)
        block_pct: Block threshold percentage (default: 100.0)

    Returns a dictionary containing:
    - usage: The UserProjectCurrentUsageReport with all percentage fields
    - decision: "ok", "warn", or "block"
    - message: Human-readable explanation of the decision

    Returns None if the user has no usage yet.
    """
    user_current_usage = storage.fetch_user_project_current_usage_report(user_id=user_id)

    if not user_current_usage:
        return None

    decision, message = user_current_usage.is_allowed(warn_pct=warn_pct, block_pct=block_pct)

    return {
        "usage": user_current_usage,
        "decision": decision,
        "message": message
    }


#
# @usage_router.get("/user/{user_id}/project/{project_id}")
# @check_null_response
# async def fetch_usage_group_by_user_and_project(user_id: str, project_id: str) -> Optional[List[UsageReport]]:
#     # return storage.fetch_usage_report_user(user_id=user_id)
#     usage = storage.fetch_usage_report(
#         user_id=FieldConfig("user_id", value=user_id, use_in_group_by=True, use_in_where=True),
#         project_id=FieldConfig("project_id", value=project_id, use_in_group_by=True, use_in_where=True),
#     )
#     return usage
#
#
# @usage_router.get("/user/{user_id}/charts")
# @check_null_response
# async def fetch_usage_group_for_charts(user_id: str) -> Optional[List[UsageReport]]:
#     # return storage.fetch_usage_report_user(user_id=user_id)
#     usage = storage.fetch_usage_report(
#         user_id=FieldConfig("user_id", value=user_id, use_in_group_by=True, use_in_where=True),
#         year=FieldConfig("year", value=None, use_in_group_by=True, use_in_where=False),
#         month=FieldConfig("month", value=None, use_in_group_by=True, use_in_where=False),
#         day=FieldConfig("day", value=None, use_in_group_by=True, use_in_where=False),
#         resource_type=FieldConfig("resource_type", value=None, use_in_group_by=True, use_in_where=False),
#     )
#     return usage
