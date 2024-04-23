import uuid
from typing import Optional, List
from db.models import WorkflowNode, WorkflowEdge
from fastapi import APIRouter
from environment import state_storage
from models import WorkflowEdgeDelete

workflow_router = APIRouter()


@workflow_router.post("/node/create")
async def create_workflow_node(node: WorkflowNode) \
        -> Optional[WorkflowNode]:

    if not node.node_id:
        node.node_id = str(uuid.uuid4())

    return state_storage.insert_workflow_node(node=node)


@workflow_router.delete("/node/{node_id}/delete")
async def delete_workflow_node(node_id: str) -> None:
    state_storage.delete_workflow_node(node_id=node_id)


@workflow_router.post("/edge/create")
async def create_workflow_edge(edge: WorkflowEdge) \
        -> Optional[WorkflowEdge]:

    return state_storage.insert_workflow_edge(edge=edge)


@workflow_router.delete("/edge/delete")
async def delete_workflow_edge(edge: WorkflowEdgeDelete) -> None:
    state_storage.delete_workflow_edge(
        source_node_id=edge.source_node_id,
        target_node_id=edge.target_node_id)
