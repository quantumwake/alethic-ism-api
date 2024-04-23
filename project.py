import uuid

from typing import Optional, List

from core.processor_state import InstructionTemplate, State
from core.processor_state_storage import Processor
from db.models import UserProject, WorkflowNode, WorkflowEdge
from fastapi import APIRouter
from environment import state_storage

project_router = APIRouter()


@project_router.post("/create")
async def create_project(user_project: UserProject) \
        -> Optional[UserProject]:
    return state_storage.insert_user_project(user_project=user_project)


@project_router.get("/{project_id}/processors")
async def fetch_processors(project_id: str) \
        -> Optional[List[Processor]]:
    return state_storage.fetch_processors(project_id=project_id)


@project_router.get("/{project_id}/workflow/nodes")
async def fetch_project_workflow_nodes(project_id: str) \
        -> Optional[List[WorkflowNode]]:
    return state_storage.fetch_workflow_nodes(project_id=project_id)


@project_router.get("/{project_id}/workflow/edges")
async def fetch_project_workflow_edges(project_id: str) \
        -> Optional[List[WorkflowEdge]]:
    return state_storage.fetch_workflow_edges(project_id=project_id)


@project_router.get("/{project_id}/templates")
def fetch_project_instruction_templates(project_id: str) -> Optional[List[InstructionTemplate]]:
    return state_storage.fetch_templates(project_id=project_id)


@project_router.get("/{project_id}/states")
async def fetch_project_states(project_id: str) \
        -> Optional[List[State]]:
    return state_storage.fetch_state(project_id=project_id)

