import uuid
import datetime as dt
from typing import Optional, List
from core.base_model import UserProject, WorkflowNode, WorkflowEdge, ProcessorState, ProcessorStatusCode, \
    ProcessorStateDirection
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


@project_router.get("/{project_id}/clone/{to_user_id}")
@check_null_response
async def clone_project(project_id: str, to_user_id: str, project_name: str = None):
    project = storage.fetch_user_project(project_id=project_id)
    project.user_id = to_user_id
    project.project_id = None
    project.created_date = None
    if project_name:
        project.project_name = project_name
    else:
        project.project_name = f"12 testing cloning of {project.project_name}"

    project = storage.insert_user_project(user_project=project)

    # copy the nodes and edges for the studio
    nodes = storage.fetch_workflow_nodes(project_id=project_id)
    nodes = {node.node_id: node for node in nodes}

    edges = storage.fetch_workflow_edges(project_id=project_id)
    edges = {f"{edge.source_node_id}:{edge.target_node_id}": edge for edge in edges}

    state_mapping = {}
    states = storage.fetch_states(project_id=project_id)
    for fetched_state in states:
        state = storage.load_state(state_id=fetched_state.id, load_data=False)
        old_state_id = state.id
        state.project_id = project.project_id
        state.id = str(uuid.uuid4())
        state.count = 0
        state.persisted_position = -1
        state.create_date = dt.datetime.utcnow()
        state.update_date = state.create_date
        state = storage.save_state(state)

        state_mapping[old_state_id] = state.id

        # TODO I know redundant
        # create new state node in workflow nodes ( I know redundant but this is how it works for now )
        new_node = nodes[old_state_id]
        new_node.node_id = state.id
        new_node.project_id = project.project_id
        storage.insert_workflow_node(new_node)                  # save the new state workflow node

    processor_mapping = {}
    processors = storage.fetch_processors(project_id=project_id)
    for processor in processors:
        old_processor_id = processor.id
        processor.project_id = project_id
        processor.id = str(uuid.uuid4())
        processor.status = ProcessorStatusCode.CREATED
        processor = storage.insert_processor(processor=processor)

        processor_mapping[old_processor_id] = processor.id
        new_node = nodes[old_processor_id]
        new_node.node_id = processor.id
        new_node.project_id = project.project_id
        new_node = storage.insert_workflow_node(new_node)       # save the new processor workflow node

    #
    process_states = storage.fetch_processor_state_routes_by_project_id(project_id=project_id)
    for ps in process_states:
        new_state_id = state_mapping[ps.state_id]
        new_processor_id = processor_mapping[ps.processor_id]

        if ps.direction == ProcessorStateDirection.INPUT:
            edge = edges[f"{ps.state_id}:{ps.processor_id}"]
            edge.source_node_id = new_state_id
            edge.target_node_id = new_processor_id
            storage.insert_workflow_edge(edge)      # save the new edge

            ps.id = f"{new_state_id}:{new_processor_id}"
        else:
            edge = edges[f"{ps.processor_id}:{ps.state_id}"]
            edge.target_node_id = new_state_id
            edge.source_node_id = new_processor_id
            storage.insert_workflow_edge(edge)      # save the new edge

            ps.id = f"{new_processor_id}:{new_state_id}"

        ps.internal_id = 0
        ps.state_id = new_state_id
        ps.processor_id = new_processor_id
        ps.status = ProcessorStatusCode.CREATED
        storage.insert_processor_state_route(ps)

    return True

