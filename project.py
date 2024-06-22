from typing import Optional, List
from core.base_model import UserProject, WorkflowNode, WorkflowEdge, ProcessorState
from core.processor_state import InstructionTemplate, State
from core.processor_state_storage import Processor, ProcessorProvider
from fastapi import APIRouter
from environment import storage
from http_exceptions import check_null_response

project_router = APIRouter()


@project_router.post("/create")
@check_null_response
async def create_project(user_project: UserProject) \
        -> Optional[UserProject]:
    return storage.insert_user_project(user_project=user_project)


@project_router.get("/{project_id}/processors")
@check_null_response
async def fetch_processors(project_id: str) \
        -> Optional[List[Processor]]:
    return storage.fetch_processors(project_id=project_id)


@project_router.get("/{project_id}/workflow/nodes")
@check_null_response
async def fetch_project_workflow_nodes(project_id: str) \
        -> Optional[List[WorkflowNode]]:
    return storage.fetch_workflow_nodes(project_id=project_id)


@project_router.get("/{project_id}/workflow/edges")
@check_null_response
async def fetch_project_workflow_edges(project_id: str) \
        -> Optional[List[WorkflowEdge]]:
    return storage.fetch_workflow_edges(project_id=project_id)


@project_router.get("/{project_id}/templates")
@check_null_response
async def fetch_project_instruction_templates(project_id: str) -> Optional[List[InstructionTemplate]]:
    return storage.fetch_templates(project_id=project_id)


@project_router.get("/{project_id}/states")
@check_null_response
async def fetch_project_states(project_id: str) \
        -> Optional[List[State]]:
    return storage.fetch_state(project_id=project_id)


@project_router.get("/{project_id}/processor/states")
@check_null_response
async def fetch_project_processor_states(project_id: str) \
        -> Optional[List[ProcessorState]]:

    # TODO needs caching likely, or we need to stream this to each user connected,
    #  instead of a POLL mechanism (this was the easiest fastest for now, ...)
    processor_states = storage.fetch_processor_state_routes_by_project_id(project_id=project_id)
    return processor_states


@project_router.get("/{project_id}/provider/processors")
@check_null_response
async def fetch_provider_processors(project_id: str) \
        -> Optional[List[ProcessorProvider]]:
    return storage.fetch_processor_providers(project_id=project_id)
