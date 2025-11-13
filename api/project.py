import uuid
import datetime as dt
from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ismcore.model.base_model import (
    UserProject,
    Processor, WorkflowNode, WorkflowEdge, InstructionTemplate, \
    ProcessorState, ProcessorProvider, ProcessorStatusCode, ProcessorStateDirection)
from ismcore.model.processor_state import State, StateConfig
from ismcore.model.base_model_usage_and_limits import UserProjectCurrentUsageReport

from api import token_service
from environment import storage
from utils.http_exceptions import check_null_response

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
async def fetch_project_workflow_nodes(project_id: str, user_id: str = Depends(token_service.verify_jwt)) \
        -> Optional[List[WorkflowNode]]:
    return storage.fetch_workflow_nodes(project_id=project_id)


@project_router.get("/{project_id}/workflow/edges")
@check_null_response
async def fetch_project_workflow_edges(project_id: str, user_id: str = Depends(token_service.verify_jwt)) \
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
    states = storage.fetch_states(project_id=project_id)
    if not states:
        return None

    for index, state in enumerate(states):
        states[index] = storage.load_state(state_id=state.id, load_data=False)

    return states



@project_router.get("/{project_id}/processor/states")
@check_null_response
async def fetch_project_processor_states(project_id: str) \
        -> Optional[List[ProcessorState]]:
    # TODO needs caching likely, or we need to stream this to each user connected,
    #  instead of a POLL mechanism (this was the easiest fastest for now, ...)
    processor_states = storage.fetch_processor_state_routes_by_project_id(project_id=project_id)
    return processor_states

@project_router.get("/{project_id}")
@check_null_response
async def fetch_project(project_id: str, user_id: str = Depends(token_service.verify_jwt)) -> Optional[UserProject]:
    """
    Fetch a project by its ID.
    :param project_id: The ID of the project to fetch.
    :param user_id: The ID of the user making the request.
    :return: The UserProject object if found, otherwise None.
    """
    return storage.fetch_user_project(project_id=project_id)


async def delete_project(project_id: str, user_id: str = Depends(token_service.verify_jwt)) -> bool:
    """
    Delete a project by its ID.
    :param project_id: The ID of the project to delete.
    :param user_id: The ID of the user making the request.
    :return: True if the project was deleted successfully, otherwise False.
    """
    return storage.delete_user_project(project_id=project_id)

@project_router.get("/{project_id}/provider/processors")
@check_null_response
async def fetch_provider_processors(project_id: str) \
        -> Optional[List[ProcessorProvider]]:
    return storage.fetch_processor_providers(project_id=project_id)


@project_router.post("/{project_id}/share/link")
async def share_project(project_id: str, user_id: str = Depends(token_service.verify_jwt)):
    pass


class CloneProjectRequest(BaseModel):
    to_user_id: str
    project_name: Optional[str] = None
    copy_columns: bool = True
    copy_data: bool = False


@project_router.post("/{project_id}/clone")
@check_null_response
async def clone_project(project_id: str, request: CloneProjectRequest) -> bool:
    project = storage.fetch_user_project(project_id=project_id)
    project.user_id = request.to_user_id
    project.project_id = None
    project.created_date = None
    if request.project_name:
        project.project_name = request.project_name
    else:
        project.project_name = f"12 testing cloning of {project.project_name}"

    project = storage.insert_user_project(user_project=project)

    # copy the nodes and edges for the studio
    nodes = storage.fetch_workflow_nodes(project_id=project_id)
    if nodes:
        nodes = {node.node_id: node for node in nodes}
    else:
        nodes = {}

    edges = storage.fetch_workflow_edges(project_id=project_id)
    if edges:
        edges = {f"{edge.source_node_id}:{edge.target_node_id}": edge for edge in edges}
    else:
        edges = {}

    state_mapping = {}
    states = storage.fetch_states(project_id=project_id)
    for fetched_state in states:
        state = storage.load_state(state_id=fetched_state.id, load_data=request.copy_data)
        old_state_id = state.id
        state.project_id = project.project_id
        state.id = str(uuid.uuid4())

        state.create_date = dt.datetime.utcnow()
        state.update_date = state.create_date

        # reset the persistence position
        state.persisted_position = -1

        if not request.copy_data:
            state.data = {}
            state.mapping = {}

        # remap all columns
        if state.columns:
            for column_name, column_definition in state.columns.items():
                column_definition.id = None

        if isinstance(state.config, StateConfig) and state.config.state_join_key:
            for tc in state.config.state_join_key:
                tc.id = None

        if isinstance(state.config, StateConfig) and state.config.template_columns:
            for tc in state.config.template_columns:
                tc.id = None

        if isinstance(state.config, StateConfig) and state.config.primary_key:
            for pk in state.config.primary_key:
                pk.id = None

        if isinstance(state.config, StateConfig) and state.config.query_state_inheritance:
            for qsi in state.config.query_state_inheritance:
                qsi.id = None

        if isinstance(state.config, StateConfig) and state.config.remap_query_state_columns:
            for rqsc in state.config.remap_query_state_columns:
                rqsc.id = None

        # save the entire state
        state = storage.save_state(state)

        # update state data position if any
        if request.copy_data:
            # we explicitly update the state count TODO need to figure this out with cache
            state = storage.update_state_count(state=state)

        state_mapping[old_state_id] = state.id

        # TODO I know redundant
        # create new state node in workflow nodes ( I know redundant but this is how it works for now )
        new_node = nodes[old_state_id]
        new_node.node_id = state.id
        new_node.project_id = project.project_id
        storage.insert_workflow_node(new_node)  # save the new state workflow node

    processor_mapping = {}
    processors = storage.fetch_processors(project_id=project_id)
    if processors:
        for processor in processors:
            old_processor_id = processor.id
            new_processor_id = str(uuid.uuid4())
            processor.id = new_processor_id
            processor.project_id = project.project_id
            processor.status = ProcessorStatusCode.CREATED
            processor = storage.insert_processor(processor=processor)

            processor_mapping[old_processor_id] = new_processor_id
            new_node = nodes[old_processor_id]
            new_node.node_id = new_processor_id
            new_node.project_id = project.project_id
            new_node = storage.insert_workflow_node(new_node)  # save the new processor workflow node

        #
        process_states = storage.fetch_processor_state_routes_by_project_id(project_id=project_id)
        for ps in process_states:
            new_state_id = state_mapping[ps.state_id]
            new_processor_id = processor_mapping[ps.processor_id]

            if ps.direction == ProcessorStateDirection.INPUT:
                edge = edges[f"{ps.state_id}:{ps.processor_id}"]
                edge.source_node_id = new_state_id
                edge.target_node_id = new_processor_id
                storage.insert_workflow_edge(edge)  # save the new edge

                ps.id = f"{new_state_id}:{new_processor_id}"
            else:
                edge = edges[f"{ps.processor_id}:{ps.state_id}"]
                edge.target_node_id = new_state_id
                edge.source_node_id = new_processor_id
                storage.insert_workflow_edge(edge)  # save the new edge

                ps.id = f"{new_processor_id}:{new_state_id}"

            ps.internal_id = 0
            ps.state_id = new_state_id
            ps.processor_id = new_processor_id
            ps.status = ProcessorStatusCode.CREATED
            storage.insert_processor_state_route(ps)

    templates = storage.fetch_templates(project_id=project_id)
    if templates:
        for template in templates:
            template.template_id = None
            template.project_id = project.project_id
            storage.insert_template(template)

    return True

