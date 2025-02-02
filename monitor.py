from typing import Optional, List
from core.base_model import MonitorLogEvent
from fastapi import APIRouter, Depends

import token_service
from environment import storage
from http_exceptions import check_null_response

monitor_router = APIRouter()


@monitor_router.post("/project/{project_id}")
@check_null_response
async def fetch_monitor_log_events_by_project_id(project_id: str, user_id=Depends(token_service.verify_jwt)) -> \
        Optional[List[MonitorLogEvent]]:
    return storage.fetch_monitor_log_events(
        user_id=user_id,
        project_id=project_id
    )


@monitor_router.post("/state/{state_id}")
@check_null_response
async def fetch_monitor_log_events_by_id(state_id: str, user_id=Depends(token_service.verify_jwt)) -> Optional[
    List[MonitorLogEvent]]:
    processor_states = storage.fetch_processor_state(state_id=state_id)

    if not processor_states:
        return None

    monitor_log_events = [
        storage.fetch_monitor_log_events(
            user_id=user_id,
            reference_id=state.internal_reference_id)
        for state in processor_states]

    return monitor_log_events


@monitor_router.post("/route/{route_id}")
@check_null_response
async def fetch_monitor_log_events_by_route_id(route_id: str, user_id=Depends(token_service.verify_jwt)) \
        -> Optional[List[MonitorLogEvent]]:
    # there should only be one when searching by route_id
    route_details = storage.fetch_processor_state_route(route_id=route_id)
    if not route_details:
        return None

    route_details = route_details[0]
    monitor_log_events = storage.fetch_monitor_log_events(user_id=user_id, reference_id=route_details.internal_id)

    return monitor_log_events


@monitor_router.delete('/project/{project_id}')
async def delete_monitor_log_events_by_project_id(project_id: str) -> int:
    return storage.delete_monitor_log_event(project=project_id)
