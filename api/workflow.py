import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from ismcore.model.base_model import WorkflowNode, WorkflowEdge

from api import token_service
from environment import storage
from models.models import WorkflowEdgeDelete

workflow_router = APIRouter()


@workflow_router.post("/node/create")
async def create_workflow_node(node: WorkflowNode, user_id: str = Depends(token_service.verify_jwt)) \
        -> Optional[WorkflowNode]:

    if not node.node_id:
        node.node_id = str(uuid.uuid4())

    return storage.insert_workflow_node(node=node)


@workflow_router.delete("/node/{node_id}/delete")
async def delete_workflow_node(node_id: str, user_id: str = Depends(token_service.verify_jwt)) -> None:
    storage.delete_workflow_node(node_id=node_id)


@workflow_router.post("/edge/create")
async def create_workflow_edge(edge: WorkflowEdge, user_id: str = Depends(token_service.verify_jwt)) \
        -> Optional[WorkflowEdge]:

    return storage.insert_workflow_edge(edge=edge)


@workflow_router.delete("/edge")
async def delete_workflow_edge(edge: WorkflowEdgeDelete, user_id: str = Depends(token_service.verify_jwt)) -> None:
    storage.delete_workflow_edge(
        source_node_id=edge.source_node_id,
        target_node_id=edge.target_node_id)
